"""Dump toe-tip / ankle / hand world positions for every frame (interpolation drift check)."""
import json

import bpy

rig = bpy.data.objects["Wukong_Rig"]
sc = bpy.context.scene
out = {}
for f in range(0, 19):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    row = {}
    for b in ("toe_l", "foot_l", "toe_r", "foot_r", "hand_l", "hand_r", "pelvis"):
        pb = rig.pose.bones[b]
        row[b] = [round(v, 6) for v in (rig.matrix_world @ pb.tail)]
    out[str(f)] = row
print("@@JSON@@" + json.dumps(out))
