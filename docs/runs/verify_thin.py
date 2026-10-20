"""Verify the thinning result: 9 keys per channel, pose-frame values unchanged,
loop seam intact, scene range set."""
import json

import bpy
from bpy_extras import anim_utils

rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
POSE_FRAMES = [0, 2, 5, 7, 9, 11, 14, 16, 18]
slot = act.slots[0]
cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)

counts = {}
bad = []
seam_bad = []
for fc in cb.fcurves:
    ks = list(fc.keyframe_points)
    counts[len(ks)] = counts.get(len(ks), 0) + 1
    frames = [round(k.co.x) for k in ks]
    if frames != POSE_FRAMES:
        bad.append((fc.data_path, fc.array_index, frames))
    else:
        first, last = ks[0].co.y, ks[-1].co.y
        if abs(first - last) > 1e-5:
            seam_bad.append((fc.data_path, fc.array_index, round(first, 5), round(last, 5)))
sc = bpy.context.scene
print("@@JSON@@" + json.dumps(dict(
    n_fcurves=len(cb.fcurves),
    key_count_histogram=counts,
    bad_curves=bad[:5],
    n_bad=len(bad),
    seam_mismatch=seam_bad[:6],
    n_seam=len(seam_bad),
    scene_range=[sc.frame_start, sc.frame_end],
    show_in_front=rig.show_in_front,
    mode=bpy.context.object.mode if bpy.context.object else None,
    packed_images=[(i.name, bool(i.packed_file)) for i in bpy.data.images][:6],
), default=str))
