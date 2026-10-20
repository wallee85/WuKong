"""Shrink the duplicated right tail into the hip with a tight region."""

import math
import os

import bpy
import bmesh
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"
BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_rigged.blend"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
scene = bpy.context.scene
body = next(o for o in scene.objects if o.type == "MESH")
body.name = "Wukong_LOD0"
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
s = 1.895 / (mx.z - mn.z)
body.scale = (s, s, s)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
body.location.x -= (mn.x + mx.x) / 2
body.location.y -= (mn.y + mx.y) / 2
body.location.z -= mn.z
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

# tight tail region on the right hip, away from hand and skirt front
bm = bmesh.new()
bm.from_mesh(body.data)
anchor = Vector((-0.20, 0.14, 0.83))
selected = []
for vert in bm.verts:
    co = vert.co
    if -0.46 <= co.x <= -0.21 and 0.52 <= co.z <= 0.88 and co.y >= 0.08:
        selected.append(vert)
print("REGION_VERTS", len(selected))
if selected:
    mn_s = Vector((min(v.co.x for v in selected), min(v.co.y for v in selected), min(v.co.z for v in selected)))
    mx_s = Vector((max(v.co.x for v in selected), max(v.co.y for v in selected), max(v.co.z for v in selected)))
    print("REGION_BBOX", [round(v, 3) for v in mn_s], [round(v, 3) for v in mx_s])

bm.to_mesh(body.data)
bm.free()

# if the region looks sane, shrink it; otherwise leave the mesh untouched
if 200 < len(selected) < 9000:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    for vert in bm.verts:
        co = vert.co
        if -0.46 <= co.x <= -0.21 and 0.52 <= co.z <= 0.88 and co.y >= 0.08:
            vert.co = anchor + (co - anchor) * 0.12
    bm.to_mesh(body.data)
    bm.free()
    print("SHRUNK")

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
    ("shrink_front", (0, -6, 0.95), (90, 0, 0)),
    ("shrink_back", (0, 6, 0.95), (90, 0, 180)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("DONE")
