"""Measure, for each bone, what a +15 deg rotation about its LOCAL X/Y/Z does.

Gives an axis cheat-sheet that matches exactly what "R then X twice" does in the UI.
Read-only: nothing is saved.
"""
import json
import math

import bpy
from mathutils import Quaternion, Vector

rig = bpy.data.objects["Wukong_Rig"]
sc = bpy.context.scene
sc.frame_set(1)
if rig.animation_data:
    rig.animation_data.action = None

BONES = ["pelvis", "spine_01", "spine_02", "chest", "neck", "head",
         "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
         "thigh_l", "shin_l", "foot_l", "toe_l", "tail_01", "tail_02"]


def reset():
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def describe(d):
    m = d.magnitude
    words = []
    if abs(d.y) > 0.20 * m:
        words.append("前" if d.y < 0 else "后")
    if abs(d.z) > 0.20 * m:
        words.append("上" if d.z > 0 else "下")
    if abs(d.x) > 0.20 * m:
        words.append("左(+X)" if d.x > 0 else "右(-X)")
    return "/".join(words) if words else "-"


out = {}
for name in BONES:
    pb = rig.pose.bones[name]
    reset()
    tip = rig.matrix_world @ pb.tail
    head = rig.matrix_world @ pb.head
    entry = dict(rest_head=[round(v, 3) for v in head],
                 rest_tail=[round(v, 3) for v in tip])
    for axis, vec in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
        reset()
        pb.rotation_quaternion = Quaternion(Vector(vec), math.radians(15))
        bpy.context.view_layer.update()
        d = (rig.matrix_world @ pb.tail) - tip
        entry[axis] = dict(disp=[round(v, 3) for v in d], mag=round(d.length, 3),
                           dir=describe(d))
    out[name] = entry
reset()

pelvis = rig.pose.bones["pelvis"]
pv = {}
for idx, axis in enumerate("XYZ"):
    reset()
    base = rig.matrix_world @ pelvis.head
    v = [0.0, 0.0, 0.0]
    v[idx] = 0.1
    pelvis.location = v
    bpy.context.view_layer.update()
    d = (rig.matrix_world @ pelvis.head) - base
    pv[axis] = dict(disp=[round(c, 3) for c in d], dir=describe(d))
out["_pelvis_location"] = pv
print("@@JSON@@" + json.dumps(out))
