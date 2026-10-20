"""Diagnose the baked Run action: cadence, lean, knee extension, arm/leg phase, foot travel.

Reads the EVALUATED rig in a fresh process (background pose reads are stale otherwise).
Prints a per-frame table and a JSON block so numbers can be quoted in docs.

  blender -b --factory-startup --python tools/blender/diag_run_gait.py
"""
import json
import math
import os

import bpy
from mathutils import Vector

BLEND = os.environ.get("WK_BLEND", r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
ACTION = os.environ.get("WK_ACTION", "Run")
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions[ACTION]
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = act
if rig.animation_data.action_slot is None and act.slots:
    rig.animation_data.action_slot = act.slots[0]

FPS = scene.render.fps
F0, F1 = int(act.frame_range[0]), int(act.frame_range[1])
CYCLE = F1 - F0                      # frame F1 duplicates F0
DUR = CYCLE / FPS

bones = rig.data.bones
LEN = {b.name: b.length for b in bones}
REST = {b.name: (rig.matrix_world @ b.head_local) for b in bones}


def wpos(pb, point="head"):
    m = rig.matrix_world @ pb.matrix
    return m.translation.copy() if point == "head" else (m @ Vector((0.0, LEN[pb.name], 0.0)))


def ang_between(a, b):
    if a.length == 0 or b.length == 0:
        return 0.0
    return math.degrees(a.angle(b))


rows = []
for f in range(F0, F1 + 1):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = rig.evaluated_get(dg)
    P = {n: wpos(ev.pose.bones[n]) for n in ("pelvis", "spine_01", "chest", "neck", "head",
                                              "thigh_l", "shin_l", "foot_l", "toe_l",
                                              "thigh_r", "shin_r", "foot_r", "toe_r",
                                              "upperarm_l", "lowerarm_l", "hand_l",
                                              "upperarm_r", "lowerarm_r", "hand_r")}
    spine = P["chest"] - P["pelvis"]
    lean = math.degrees(math.atan2(-spine.y, spine.z))     # forward = -Y
    head_fwd = P["head"] - P["neck"]

    def knee(side):
        v1 = P["thigh_%s" % side] - P["shin_%s" % side]     # knee -> hip
        v2 = P["foot_%s" % side] - P["shin_%s" % side]      # knee -> ankle
        return ang_between(v1, v2)

    def ext(side):
        reach = (P["foot_%s" % side] - P["thigh_%s" % side]).length
        return reach / (LEN["thigh_%s" % side] + LEN["shin_%s" % side])

    def arm_swing(side):
        v = P["hand_%s" % side] - P["upperarm_%s" % side]
        return math.degrees(math.atan2(-v.y, -v.z))          # + = forward

    def kneebend(side):
        v1 = P["upperarm_%s" % side] - P["lowerarm_%s" % side]
        v2 = P["hand_%s" % side] - P["lowerarm_%s" % side]
        return ang_between(v1, v2)

    rows.append(dict(
        f=f, hip=round(P["pelvis"].z, 3),
        lean=round(lean, 1), head_pitch=round(math.degrees(math.atan2(-head_fwd.y, head_fwd.z)), 1),
        ankL=(round(P["foot_l"].y, 3), round(P["foot_l"].z, 3)),
        ankR=(round(P["foot_r"].y, 3), round(P["foot_r"].z, 3)),
        toeL_z=round(P["toe_l"].z, 3), toeR_z=round(P["toe_r"].z, 3),
        kneeL=round(knee("l"), 1), kneeR=round(knee("r"), 1),
        extL=round(ext("l"), 3), extR=round(ext("r"), 3),
        armL=round(arm_swing("l"), 1), armR=round(arm_swing("r"), 1),
        elbL=round(kneebend("l"), 1), elbR=round(kneebend("r"), 1),
    ))

# ground: evaluated mesh lowest point per frame
meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == rig and o.data.users >= 1]
low = []
for f in range(F0, F1 + 1):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    zmin, ylow = 1e9, 0.0
    for o in meshes:
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        mw = eo.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            if w.z < zmin:
                zmin, ylow = w.z, w.y
        eo.to_mesh_clear()
    low.append((round(zmin, 4), round(ylow, 3)))

v = 3.40  # RUN_SPEED in scripts/main.gd (v17: was 4.20)
step = v / FPS
print("JSON_BEGIN")
print(json.dumps(dict(cycle=CYCLE, dur=round(DUR, 4), fps=FPS, speed=v,
                      step_per_frame=round(step, 4),
                      stance_minz=[z for z, _ in low], rows=rows), ensure_ascii=False))
print("JSON_END")

hdr = "f  hip   lean  head  ankL(y,z)      ankR(y,z)      kneeL kneeR extL  extR  armL  armR  elbL  elbR  groundZ"
print(hdr)
for r, (gz, gy) in zip(rows, low):
    print("%2d %5.3f %5.1f %5.1f  %7.3f,%5.3f  %7.3f,%5.3f  %5.1f %5.1f %5.3f %5.3f %5.1f %5.1f %5.1f %5.1f  %6.4f"
          % (r["f"], r["hip"], r["lean"], r["head_pitch"], r["ankL"][0], r["ankL"][1],
             r["ankR"][0], r["ankR"][1], r["kneeL"], r["kneeR"], r["extL"], r["extR"],
             r["armL"], r["armR"], r["elbL"], r["elbR"], gz))

ankL = [r["ankL"][0] for r in rows]
ankR = [r["ankR"][0] for r in rows]
print("\nstride L = %.3f m, R = %.3f m   (span of ankle y)" % (max(ankL) - min(ankL), max(ankR) - min(ankR)))
print("hip range %.3f .. %.3f  bob %.3f m" % (min(r["hip"] for r in rows), max(r["hip"] for r in rows),
                                              max(r["hip"] for r in rows) - min(r["hip"] for r in rows)))
print("max leg extension L %.3f R %.3f" % (max(r["extL"] for r in rows), max(r["extR"] for r in rows)))
print("cadence = %.0f steps/min, step length = %.3f m" % (2 * 60.0 / DUR, v * DUR / 2.0))
