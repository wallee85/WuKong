"""Highlight a tight box around the leftover stub to verify the cut region."""

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
bpy.ops.object.modifier_add(type="DECIMATE")
body.modifiers[-1].ratio = 30000 / sum(len(p.vertices) - 2 for p in body.data.polygons)
bpy.ops.object.modifier_apply(modifier=body.modifiers[-1].name)

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

red = bpy.data.materials.new("RED")
red.diffuse_color = (0.9, 0.05, 0.05, 1.0)
body.data.materials.append(red)

count = 0
for poly in body.data.polygons:
    c = poly.center
    if -0.20 <= c.x <= -0.04 and 0.48 <= c.z <= 0.68 and -0.10 <= c.y <= 0.25:
        poly.material_index = 1
        count += 1
print("HIGHLIGHT", count)

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 1.2
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("W")
scene.world.color = (0.1, 0.1, 0.1)

cam.location = (0, 6, 0.58)
cam.rotation_euler = (math.radians(90), 0, math.radians(180))
scene.render.filepath = os.path.join(OUT, "stub_highlight_back.png")
bpy.ops.render.render(write_still=True)

cam.location = (-6, 0, 0.58)
cam.rotation_euler = (math.radians(90), 0, math.radians(-90))
scene.render.filepath = os.path.join(OUT, "stub_highlight_side.png")
bpy.ops.render.render(write_still=True)
print("DONE")
