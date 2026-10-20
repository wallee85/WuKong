"""Dump rig proportions, rest-pose landmarks and current Run pose angles.

  blender -b --python tools/blender/dump_rig_metrics.py
"""
import json
import math

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)

rig = bpy.data.objects["Wukong_Rig"]
scene = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

out = {"objects": [], "bones": {}, "heights": {}, "action": {}}

for ob in bpy.data.objects:
    out["objects"].append({"name": ob.name, "type": ob.type,
                           "parent": ob.parent.name if ob.parent else None,
                           "mods": [m.type for m in ob.modifiers],
                           "hide": ob.hide_get()})

# bone rest data
for b in rig.data.bones:
    out["bones"][b.name] = {
        "parent": b.parent.name if b.parent else None,
        "head_world": [round(v, 4) for v in (rig.matrix_world @ b.head_local)],
        "tail_world": [round(v, 4) for v in (rig.matrix_world @ b.tail_local)],
        "length": round(b.length, 4),
        "deform": b.use_deform,
    }

# mesh world-space bounds in the rest pose (no action)
rig.animation_data.action = None if rig.animation_data else None
if rig.animation_data:
    rig.animation_data.action = None
scene.frame_set(1)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    if not me.vertices:
        ev.to_mesh_clear()
        continue
    mw = ob.matrix_world
    zs, ys, xs = [], [], []
    for v in me.vertices:
        w = mw @ v.co
        xs.append(w.x)
        ys.append(w.y)
        zs.append(w.z)
    out["heights"][ob.name] = {
        "z": [round(min(zs), 4), round(max(zs), 4)],
        "y": [round(min(ys), 4), round(max(ys), 4)],
        "x": [round(min(xs), 4), round(max(xs), 4)],
        "verts": len(me.vertices),
    }
    ev.to_mesh_clear()

# current Run action, sampled joint angles
act = bpy.data.actions.get("Run")
if act:
    if not rig.animation_data:
        rig.animation_data_create()
    rig.animation_data.action = act
    for slot in act.slots:
        rig.animation_data.action_slot = slot
        break
    out["action"]["name"] = act.name
    out["action"]["frame_range"] = [round(v, 2) for v in act.frame_range]
    out["action"]["slots"] = [s.identifier for s in act.slots]
    frames = {}
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        rec = {}
        for name in ("pelvis", "thigh_l", "shin_l", "foot_l", "thigh_r", "shin_r", "foot_r",
                     "foot_ik_l", "foot_ik_r", "spine_01", "upperarm_l", "upperarm_r"):
            pb = rig.pose.bones.get(name)
            if not pb:
                continue
            m = rig.matrix_world @ pb.matrix
            rec[name] = {
                "head": [round(v, 3) for v in m.translation],
                "tail": [round(v, 3) for v in (rig.matrix_world @ pb.tail)],
            }
        frames[f] = rec
    out["action"]["frames"] = frames

def sagittal(a, b):
    """Angle of the a->b segment from vertical in the YZ plane (deg, + = +y forward)."""
    d = Vector(b) - Vector(a)
    return round(math.degrees(math.atan2(d.y, -d.z)), 1)

if act:
    print("FRAME  hipZ   thighL  shinL   footL  thighR  shinR   footR")
    for f, rec in out["action"]["frames"].items():
        def ang(n):
            if n not in rec:
                return 999
            return sagittal(rec[n]["head"], rec[n]["tail"])
        print("%5d %6.3f %7.1f %6.1f %6.1f %6.1f %6.1f %6.1f" % (
            f, rec["pelvis"]["head"][2], ang("thigh_l"), ang("shin_l"), ang("foot_l"),
            ang("thigh_r"), ang("shin_r"), ang("foot_r")))

json.dump(out, open(r"D:\Workspace\games\WuKong\docs\runs\rig_metrics.json", "w"), indent=1)
print("RIG_DUMP_DONE")
