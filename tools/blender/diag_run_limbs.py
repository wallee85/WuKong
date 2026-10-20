"""Measure the three things the side/front sheets hide: arm swing plane, foot yaw, leg fold.

  blender -b --factory-startup --python tools/blender/diag_run_limbs.py
"""
import json
import math
import os

import bpy
from mathutils import Vector

BLEND = os.environ.get("WK_BLEND", r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = act
if rig.animation_data.action_slot is None and act.slots:
    rig.animation_data.action_slot = act.slots[0]

F0, F1 = int(act.frame_range[0]), int(act.frame_range[1])
LEN = {b.name: b.length for b in rig.data.bones}


def wp(pb, point="head"):
    m = rig.matrix_world @ pb.matrix
    return m.translation.copy() if point == "head" else (m @ Vector((0.0, LEN[pb.name], 0.0)))


rows = []
for f in range(F0, F1):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = rig.evaluated_get(dg)
    P = {n: wp(ev.pose.bones[n]) for n in
         ("chest", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r",
          "lowerarm_l", "lowerarm_r", "hand_l", "hand_r",
          "thigh_l", "shin_l", "foot_l", "toe_l", "thigh_r", "shin_r", "foot_r", "toe_r")}

    def dirv(a, b):
        return (P[b] - P[a]).normalized()

    def yaw(v):
        # forward is -Y. yaw > 0 means the segment points to +X (character's left)
        return math.degrees(math.atan2(v.x, -v.y))

    def knee_ang(s):
        return math.degrees((P["thigh_%s" % s] - P["shin_%s" % s])
                            .angle(P["foot_%s" % s] - P["shin_%s" % s]))

    rec = {"f": f}
    for s in ("l", "r"):
        foot_dir = dirv("foot_%s" % s, "toe_%s" % s)
        rec[s] = {
            "foot_yaw": round(yaw(foot_dir), 1),
            "knee": round(knee_ang(s), 1),
            "ankle_z": round(P["foot_%s" % s].z, 3),
            "toe_z": round(P["toe_%s" % s].z, 3),
            "hand_rel": [round(P["hand_%s" % s][i] - P["chest"][i], 3) for i in range(3)],
            "upper_dir": [round(dirv("upperarm_%s" % s, "lowerarm_%s" % s)[i], 3) for i in range(3)],
        }
    rows.append(rec)

print("JSON_BEGIN")
print(json.dumps({"rows": rows,
                  "rest_foot_yaw": {s: round(math.degrees(math.atan2(
                      (rig.data.bones["foot_%s" % s].tail_local - rig.data.bones["foot_%s" % s].head_local).x,
                      -(rig.data.bones["foot_%s" % s].tail_local - rig.data.bones["foot_%s" % s].head_local).y)), 1)
                      for s in ("l", "r")}}, ensure_ascii=False))
print("JSON_END")

print("f   | footYawL footYawR | kneeL kneeR | ankL_z ankR_z | handL(dx,dy,dz)      handR(dx,dy,dz)")
for r in rows:
    l, rr = r["l"], r["r"]
    print("%2d  | %7.1f %8.1f | %5.1f %5.1f | %5.3f %6.3f | %-20s %-20s"
          % (r["f"], l["foot_yaw"], rr["foot_yaw"], l["knee"], rr["knee"], l["ankle_z"], rr["ankle_z"],
             "%+.3f %+.3f %+.3f" % tuple(l["hand_rel"]), "%+.3f %+.3f %+.3f" % tuple(rr["hand_rel"])))

for s in ("l", "r"):
    xs = [r[s]["hand_rel"][0] for r in rows]
    ys = [r[s]["hand_rel"][1] for r in rows]
    zs = [r[s]["hand_rel"][2] for r in rows]
    print("%s hand excursion: lateral(x) %.3f  sagittal(y) %.3f  vertical(z) %.3f  -> plane ratio x/y = %.2f"
          % (s, max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs),
             (max(xs) - min(xs)) / max(1e-6, max(ys) - min(ys))))
    print("%s foot yaw range: %.1f .. %.1f deg   knee min %.1f max %.1f"
          % (s, min(r[s]["foot_yaw"] for r in rows), max(r[s]["foot_yaw"] for r in rows),
             min(r[s]["knee"] for r in rows), max(r[s]["knee"] for r in rows)))
