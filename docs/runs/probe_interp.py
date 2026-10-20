"""Probe: interpolation types in the saved file + evaluated value at f1/f3/f4."""
import bpy
from bpy_extras import anim_utils

rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
cb = anim_utils.action_ensure_channelbag_for_slot(act, act.slots[0])
fc = [f for f in cb.fcurves if f.data_path.endswith('["thigh_l"].rotation_quaternion')
      or f.data_path == 'pose.bones["thigh_l"].rotation_quaternion'][0]
print("INTERP", [k.interpolation for k in fc.keyframe_points][:4],
      [k.handle_left_type for k in fc.keyframe_points][:4])
print("KEYS", [(round(k.co.x), round(k.co.y, 6)) for k in fc.keyframe_points])
sc = bpy.context.scene
vals = {}
for f in (0, 1, 2, 3, 4, 5):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    vals[f] = round(rig.pose.bones["thigh_l"].rotation_quaternion.w, 6)
print("EVAL", vals)
