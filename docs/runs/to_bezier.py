"""Switch the thinned Run curves to BEZIER + auto-clamped and save (drift experiment)."""
import bpy
from bpy_extras import anim_utils

rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
cb = anim_utils.action_ensure_channelbag_for_slot(act, act.slots[0])
n = 0
for fc in cb.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "BEZIER"
        k.handle_left_type = "AUTO_CLAMPED"
        k.handle_right_type = "AUTO_CLAMPED"
        n += 1
    fc.update()
bpy.ops.wm.save_mainfile()
print("BEZIER_SET", n)
