"""Render the run from N azimuths (turntable) with game-like framing.

  blender -b --python tools/blender/turntable.py -- <prefix> <frames csv> [step_deg]
"""
import math
import sys

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

argv = sys.argv[sys.argv.index("--") + 1:]
prefix = argv[0]
frames = [int(f) for f in argv[1].split(",")]
step = int(argv[2]) if len(argv) > 2 else 45
AZS = [int(a) for a in argv[3].split(',')] if len(argv) > 3 else list(range(0, 360, step))

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = act
for s in act.slots:
    rig.animation_data.action_slot = s
    break

cam_data = bpy.data.cameras.new("TURNCAM")
cam = bpy.data.objects.new("TURNCAM", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.type = "PERSP"
cam_data.angle = math.radians(62.0)
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.film_transparent = True
scene.render.resolution_x = 560
scene.render.resolution_y = 640

PIVOT = Vector((0.0, 0.0, 1.05))
DIST = 3.6
PITCH = 0.18

for f in frames:
    scene.frame_set(f)
    for az in AZS:
        a = math.radians(az)
        # az=0 is directly behind (+Y), az=180 is front
        loc = PIVOT + Vector((math.sin(a) * DIST * math.cos(PITCH), math.cos(a) * DIST * math.cos(PITCH),
                              DIST * math.sin(PITCH)))
        cam.location = loc
        cam.rotation_euler = (PIVOT - loc).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = "%s\\%s_az%03d_f%02d.png" % (OUT, prefix, az, f)
        bpy.ops.render.render(write_still=True)
    print("TURN frame", f, "done")
print("TURNTABLE_DONE")
