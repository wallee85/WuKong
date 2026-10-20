"""Bone-axis calibration sheet: which local axis swings which way."""

import math
import os

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]

cam_data = bpy.data.cameras.new("CAL_CAM")
cam = bpy.data.objects.new("CAL_CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.2
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 640
scene.render.resolution_y = 800
scene.render.film_transparent = True

VIEWS = {
    "front": ((0, -6, 0.95), (90, 0, 0)),
    "side": ((6, 0, 0.95), (90, 0, 90)),
}

TESTS = [
    ("thigh_l", Vector((1, 0, 0)), 30, "side"),
    ("thigh_l", Vector((0, 0, 1)), 30, "side"),
    ("upperarm_r", Vector((0, 0, 1)), 30, "front"),
    ("upperarm_r", Vector((1, 0, 0)), 30, "front"),
    ("spine_01", Vector((0, 1, 0)), 25, "front"),
]

for index, (bone_name, axis, angle, view) in enumerate(TESTS):
    for pbone in rig.pose.bones:
        pbone.rotation_mode = "QUATERNION"
        pbone.rotation_quaternion = (1, 0, 0, 0)
    pbone = rig.pose.bones.get(bone_name)
    if pbone is None:
        print("MISSING", bone_name)
        continue
    pbone.rotation_quaternion = __import__("mathutils").Quaternion(axis, math.radians(angle))
    location, rotation = VIEWS[view]
    cam.location = location
    cam.rotation_euler = tuple(math.radians(a) for a in rotation)
    scene.render.filepath = os.path.join(OUT, "cal_%d.png" % index)
    bpy.ops.render.render(write_still=True)
    print("CAL", index, bone_name, tuple(axis), angle, view)
print("DONE")
