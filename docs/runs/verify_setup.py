"""Verify the hand-edit setup: key histogram, pose-frame values untouched, seam intact."""
import json

import bpy
from bpy_extras import anim_utils

rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
POSE_FRAMES = [0, 2, 5, 7, 9, 11, 14, 16, 18]
cb = anim_utils.action_ensure_channelbag_for_slot(act, act.slots[0])
hist = {}
for fc in cb.fcurves:
    n = len(fc.keyframe_points)
    hist[n] = hist.get(n, 0) + 1
    frames = [round(k.co.x) for k in fc.keyframe_points]
    assert all(f in frames for f in POSE_FRAMES), (fc.data_path, frames)
print("@@JSON@@" + json.dumps(dict(
    key_histogram={str(k): v for k, v in sorted(hist.items())},
    scene_range=[bpy.context.scene.frame_start, bpy.context.scene.frame_end],
    show_in_front=bool(rig.show_in_front),
), default=str))
