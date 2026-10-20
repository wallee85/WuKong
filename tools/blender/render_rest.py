"""Render the rest pose (no action) from the follow-cam angle, for A/B against the run.

  blender -b --python tools/blender/render_rest.py
"""
import math

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.scale = (1, 1, 1)
scene.frame_set(0)
bpy.context.view_layer.update()

cam_data = bpy.data.cameras.new("RESTCAM")
cam = bpy.data.objects.new("RESTCAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "PERSP"
cam_data.angle = math.radians(70.0)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.film_transparent = True
scene.render.resolution_x = 760
scene.render.resolution_y = 720

for name, loc in (("game", (0.0, 4.6, 1.70)), ("side", (-4.6, 0.0, 1.20))):
    cam.location = loc
    cam.rotation_euler = (Vector((0.0, 0.0, 1.15 if name == "game" else 0.95))
                          - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = "%s\\rest_%s.png" % (OUT, name)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)
print("REST_RENDER_DONE")
