"""Print bone world matrices at pose frames, to diff original vs thinned."""
import json

import bpy

rig = bpy.data.objects["Wukong_Rig"]
sc = bpy.context.scene
BONES = ["pelvis", "thigh_l", "shin_l", "foot_l", "upperarm_l", "lowerarm_l", "chest"]
frames = [0, 2, 5, 7, 9, 11, 14, 16, 18]
out = {}
for f in frames:
    sc.frame_set(f)
    bpy.context.view_layer.update()
    vals = []
    for b in BONES:
        m = rig.matrix_world @ rig.pose.bones[b].matrix
        vals.extend(round(v, 5) for row in m for v in row)
    out[str(f)] = vals
print("@@JSON@@" + json.dumps(out))
