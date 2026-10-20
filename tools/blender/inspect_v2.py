"""Inspect the new single-tail generation."""

import math
import os

import bpy
from mathutils import Vector

GLB = r"D:\Workspace\games\WuKong\source\glb\wukong_v2.glb"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
scene = bpy.context.scene
body = next(o for o in scene.objects if o.type == "MESH")
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
print("VERTS", len(body.data.vertices), "TRIS", tris)
print("IMAGES", [(i.name, tuple(i.size)) for i in bpy.data.images if i.size[0] > 0])

corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
print("RAW_SIZE", [round(v, 3) for v in (mx - mn)])

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
print("SCALED_SIZE", [round(v, 3) for v in body.dimensions])

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True

for name, loc, rot, ortho in (
    ("v2_front", (0, -6, 0.95), (90, 0, 0), 2.2),
    ("v2_back", (0, 6, 0.95), (90, 0, 180), 2.2),
    ("v2_left", (-6, 0, 0.95), (90, 0, -90), 2.2),
    ("v2_tail", (-0.9, 3.2, 0.85), (84, 0, -160), 0.9),
):
    cam_data.ortho_scale = ortho
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("DONE")
