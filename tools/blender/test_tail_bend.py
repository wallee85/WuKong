"""Bend the tail bones to verify skinning (does not save)."""

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

for name, angle in (("tail_02", 0.5), ("tail_03", 0.6), ("tail_04", 0.6)):
    pb = rig.pose.bones.get(name)
    if pb:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0.0, 0.0, angle)

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1.4
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.film_transparent = True

for name, loc, rot in (
    ("tail_bend_back", (2.6, 3.6, 0.85), (82, 0, 145)),
    ("tail_bend_back2", (0, 6, 0.85), (90, 0, 180)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = OUT + "\\" + name + ".png"
    bpy.ops.render.render(write_still=True)
print("DONE")
