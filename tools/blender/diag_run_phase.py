"""Report the timing of each chain link: when does it reach its extreme?

The point: with every channel driven by cos(2*pi*u) they all peak on the same frame and
the body reads as one rigid block. This prints the frame of each link's maximum and the
lag against the pelvis, plus the boot yaw (the mesh is modelled toe-out; the foot bone
has to be yawed back to compensate).

  blender -b --factory-startup --python tools/blender/diag_run_phase.py
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
mesh = bpy.data.objects["Wukong_LOD0"]
act = bpy.data.actions["Run"]
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = act
if rig.animation_data.action_slot is None and act.slots:
    rig.animation_data.action_slot = act.slots[0]

F0, F1 = int(act.frame_range[0]), int(act.frame_range[1])
N = F1 - F0


def yaw_of(m):
    """Yaw of a rotation matrix about +Z, in degrees (forward is -Y)."""
    fwd = m.to_3x3() @ Vector((0.0, 0.0, -1.0))
    return math.degrees(math.atan2(-fwd.x, -fwd.y) * -1.0)


def bone_yaw(name, ev):
    """Extrinsic yaw of the bone's world matrix (rotation of its local X in the XY plane)."""
    m = ev.pose.bones[name].matrix.to_3x3()
    return math.degrees(math.atan2(m[1][0], m[0][0]))


def sagittal_angle(v):
    """Angle of a direction in the YZ plane: + = forward (-Y), 0 = straight down."""
    return math.degrees(math.atan2(-v.y, -v.z))


series = {"pelvis": [], "chest": [], "head": [], "upperarm_l": [], "hand_l": [], "hip_z": []}
boot = []
for f in range(F0, F1):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = rig.evaluated_get(dg)
    pb = ev.pose.bones
    series["pelvis"].append(bone_yaw("pelvis", ev))
    series["chest"].append(bone_yaw("chest", ev))
    series["head"].append(bone_yaw("head", ev))
    up = (pb["lowerarm_l"].matrix.translation - pb["upperarm_l"].matrix.translation)
    series["upperarm_l"].append(sagittal_angle(up))
    series["hand_l"].append(-(pb["hand_l"].matrix.translation.y))     # forward = +
    series["hip_z"].append(pb["pelvis"].matrix.translation.z)

    eo = mesh.evaluated_get(dg)
    me = eo.to_mesh()
    mw = eo.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    pts = [p for p in pts if p.z < 0.16 and p.x > 0.02]
    if pts:
        ys = [p.y for p in pts]
        lo, hi = min(ys), max(ys)
        span = max(hi - lo, 1e-6)
        toe = [p for p in pts if p.y < lo + span * 0.25]
        heel = [p for p in pts if p.y > hi - span * 0.25]
        tx = sum(p.x for p in toe) / len(toe); ty = sum(p.y for p in toe) / len(toe)
        hx = sum(p.x for p in heel) / len(heel); hy = sum(p.y for p in heel) / len(heel)
        boot.append(math.degrees(math.atan2(tx - hx, -(ty - hy))))
    eo.to_mesh_clear()

ref = series["pelvis"]
peak = {k: (max(range(len(v)), key=lambda i: v[i]), max(v), min(v)) for k, v in series.items()}


def lag_frames(a, b):
    d = (a - b) % N
    return d if d <= N / 2 else d - N


print("JSON_BEGIN")
print(json.dumps({"cycle_frames": N, "peaks": {k: v[0] for k, v in peak.items()},
                  "ranges": {k: [round(v[2], 3), round(v[1], 3)] for k, v in peak.items()},
                  "boot_yaw_deg": round(sum(boot) / len(boot), 1) if boot else None}))
print("JSON_END")

print("cycle = %d frames @ 24 fps = %.4f s" % (N, N / 24.0))
print("%-12s %6s %9s %9s %8s" % ("channel", "peak@f", "max", "min", "lag vs pelvis"))
for k in ("pelvis", "chest", "head", "upperarm_l", "hand_l", "hip_z"):
    f, hi, lo = peak[k]
    print("%-12s %6d %9.2f %9.2f %8.1f" % (k, f, hi, lo, lag_frames(f, peak["pelvis"][0])))
print("boot mesh yaw (left, deg): %.1f" % (sum(boot) / len(boot) if boot else float("nan")))
