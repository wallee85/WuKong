"""Verify what the cleaned file actually contains around the hips."""

import math

import bpy

BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_game.blend"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders\verify_front.png"

bpy.ops.wm.open_mainfile(filepath=BLEND)
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
print("OBJ", obj.name, "verts", len(obj.data.vertices), "faces", len(obj.data.polygons))

region = [
    p for p in obj.data.polygons
    if 0.55 <= p.center.z <= 0.80 and 0.20 <= abs(p.center.x) <= 0.46 and p.center.y > -0.02
]
print("REGION_FACES", len(region))

scene = bpy.context.scene
cam = bpy.data.objects.get("CAM")
if cam is None:
    cam_data = bpy.data.cameras.new("CAM")
    cam = bpy.data.objects.new("CAM", cam_data)
    scene.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.2
cam.location = (0, -6, 0.95)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("DONE")
