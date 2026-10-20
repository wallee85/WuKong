"""Delete the leftover tail stub by sampling the albedo texture (fur is grey)."""

import math
import os

import bpy
import bmesh
import numpy as np
from mathutils import Vector

GLB = r"D:\Workspace\games\WuKong\source\glb\wukong_hunyuan_v1.glb"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
scene = bpy.context.scene
body = next(o for o in scene.objects if o.type == "MESH")
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0003)
bm.to_mesh(body.data)
bm.free()

corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
scale = 1.895 / (mx.z - mn.z)
body.scale = (scale, scale, scale)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
body.location.x -= (mn.x + mx.x) / 2
body.location.y -= (mn.y + mx.y) / 2
body.location.z -= mn.z
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

img = bpy.data.images["texture_pbr_20250901"]
w, h = img.size
buf = np.empty(w * h * 4, dtype=np.float32)
img.pixels.foreach_get(buf)
pixels = buf.reshape(h, w, 4)

bm = bmesh.new()
bm.from_mesh(body.data)


def big_tail(co):
    return -0.45 <= co.x <= -0.08 and 0.50 <= co.z <= 0.90 and co.y >= 0.14


bm_uv = bm.loops.layers.uv.active
removed = 0
for face in list(bm.faces):
    if not all(big_tail(v.co) for v in face.verts):
        continue
    u = sum(l[bm_uv].uv.x for l in face.loops) / len(face.loops)
    v = sum(l[bm_uv].uv.y for l in face.loops) / len(face.loops)
    px = int(u % 1.0 * w)
    py = int(v % 1.0 * h)
    r, g, b = pixels[py, px, 0], pixels[py, px, 1], pixels[py, px, 2]
    mx_c = max(r, g, b)
    mn_c = min(r, g, b)
    sat = 0.0 if mx_c <= 0 else (mx_c - mn_c) / mx_c
    if mx_c < 0.45 and sat < 0.20:
        bmesh.ops.delete(bm, geom=[face], context="FACES")
        removed += 1
print("TEXTURE_REMOVED", removed)
print("REMAINING_FACES", len(bm.faces))

uv_layer = bm.loops.layers.uv.active
vert_uv = {}
for face in bm.faces:
    for loop in face.loops:
        vert_uv[loop.vert] = loop[uv_layer].uv.copy()

boundary = [e for e in bm.edges if len(e.link_faces) == 1]
adj = {}
for edge in boundary:
    for vert in edge.verts:
        adj.setdefault(vert, []).append(edge)

seen = set()
loops = []
for edge in boundary:
    if edge in seen:
        continue
    stack = [edge]
    loop = []
    seen.add(edge)
    while stack:
        current = stack.pop()
        loop.append(current)
        for vert in current.verts:
            for other in adj.get(vert, []):
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
    loops.append(loop)

old_faces = set(bm.faces)
filled = 0
for loop in loops:
    if len(loop) < 300:
        bmesh.ops.holes_fill(bm, edges=loop, sides=0)
        filled += 1
print("LOOPS", len(loops), "FILLED", filled)

for face in bm.faces:
    if face in old_faces:
        continue
    for loop in face.loops:
        if loop.vert in vert_uv:
            loop[uv_layer].uv = vert_uv[loop.vert]

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(body.data)
bm.free()

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.2
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True

for name, loc, rot in (
    ("v6_back", (0, 6, 0.95), (90, 0, 180)),
    ("v6_front", (0, -6, 0.95), (90, 0, 0)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("DONE")
