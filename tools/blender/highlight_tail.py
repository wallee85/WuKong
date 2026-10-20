"""Highlight the suspected tail region to verify a safe cut."""

import math

import bpy
import bmesh
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders\tail_select_test.png"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0003)
bm.to_mesh(obj.data)
bm.free()

corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
s = 1.895 / (mx.z - mn.z)
obj.scale = (s, s, s)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
obj.location.x -= (mn.x + mx.x) / 2
obj.location.y -= (mn.y + mx.y) / 2
obj.location.z -= mn.z
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

# decimate for speed
tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
mod = obj.modifiers.new("Dec", "DECIMATE")
mod.ratio = 30000 / tris
bpy.ops.object.modifier_apply(modifier="Dec")

mat_red = bpy.data.materials.new("RED")
mat_red.diffuse_color = (0.9, 0.05, 0.05, 1.0)
obj.data.materials.append(mat_red)

selected = 0
for poly in obj.data.polygons:
    c = poly.center
    if 0.55 <= c.z <= 0.80 and 0.20 <= abs(c.x) <= 0.46 and c.y > -0.02:
        poly.material_index = 1
        selected += 1
print("HIGHLIGHTED", selected, "of", len(obj.data.polygons))

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.0
cam.location = (0, -6, 0.85)
cam.rotation_euler = (math.radians(90), 0, 0)
bpy.context.scene.camera = cam

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1000
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("DONE")
