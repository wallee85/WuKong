"""Second pass: cut the right tail behind the skirt and fill every small loop."""

import math
import os

import bpy
import bmesh
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

bm = bmesh.new()
bm.from_mesh(body.data)

boundary = [e for e in bm.edges if len(e.link_faces) == 1]
print("BOUNDARY_EDGES_BEFORE", len(boundary))


def loops_of(edges):
    adj = {}
    for edge in edges:
        for vert in edge.verts:
            adj.setdefault(vert, []).append(edge)
    seen = set()
    result = []
    for edge in edges:
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
        result.append(loop)
    return result


for loop in loops_of(boundary):
    verts = {v for e in loop for v in e.verts}
    center = Vector((0, 0, 0))
    for v in verts:
        center += v.co
    center /= len(verts)
    print("LOOP_BEFORE", len(loop), [round(v, 2) for v in center])


def in_region(co):
    return (
        -0.45 <= co.x <= -0.08
        and 0.50 <= co.z <= 0.90
        and co.y >= 0.14
    )


faces = [f for f in bm.faces if all(in_region(v.co) for v in f.verts)]
print("TAIL_FACES", len(faces))
bmesh.ops.delete(bm, geom=faces, context="FACES")

boundary = [e for e in bm.edges if len(e.link_faces) == 1]
loops = loops_of(boundary)
filled = 0
for loop in loops:
    if len(loop) < 400:
        bmesh.ops.holes_fill(bm, edges=loop, sides=0)
        filled += 1
print("LOOPS_AFTER", len(loops), "FILLED", filled)

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
    ("v3_front", (0, -6, 0.95), (90, 0, 0)),
    ("v3_back", (0, 6, 0.95), (90, 0, 180)),
    ("v3_left", (-6, 0, 0.95), (90, 0, -90)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("DONE")
