"""Set every key in Run to LINEAR and save (test file)."""
import bpy
from bpy_extras import anim_utils

act = bpy.data.actions["Run"]
cb = anim_utils.action_ensure_channelbag_for_slot(act, act.slots[0])
n = 0
for fc in cb.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
        n += 1
    fc.update()
bpy.ops.wm.save_mainfile()
print("LINEAR_SET", n)
