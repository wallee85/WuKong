"""Measure foot yaw (toe-out) and leg twist, in the rest pose and through the Run cycle.

  blender -b --python tools/blender/check_foot_yaw.py
"""
import math

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]


def yaw_of(a, b):
    """Yaw of the a->b vector: 0 = straight forward (-Y), positive = toe-out (+X)."""
    d = b - a
    return math.degrees(math.atan2(d.x, -d.y))


def twist_of(m3):
    """Roll of a bone frame about its own axis: angle of its X column away from world X."""
    x = m3.col[0]
    return math.degrees(math.atan2(x.z, x.x))


print("%-8s %-10s %-10s %-10s %-10s" % ("state", "footL_yaw", "footR_yaw", "toeL_yaw", "toeR_yaw"))
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
if rig.animation_data:
    rig.animation_data.action = None
scene.frame_set(0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
pose = rig.evaluated_get(dg).pose
vals = []
for side in ("l", "r"):
    f = pose.bones["foot_%s" % side]
    t = pose.bones["toe_%s" % side]
    vals += [yaw_of(f.head, f.tail), yaw_of(t.head, t.tail)]
print("%-8s %-10.1f %-10.1f %-10.1f %-10.1f" % ("rest", *vals))

act = bpy.data.actions["Run"]
rig.animation_data.action = act
for s in act.slots:
    rig.animation_data.action_slot = s
    break
print("%-8s %-10s %-10s %-10s %-10s  shinL_twist shinR_twist" % ("frame", "footL", "footR", "toeL", "toeR"))
for f in range(0, 15):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    pose = rig.evaluated_get(dg).pose
    vals = []
    for side in ("l", "r"):
        fb = pose.bones["foot_%s" % side]
        tb = pose.bones["toe_%s" % side]
        vals += [yaw_of(fb.head, fb.tail), yaw_of(tb.head, tb.tail)]
    tw = [twist_of(pose.bones["shin_%s" % s].matrix.to_3x3()) for s in ("l", "r")]
    print("%-8d %-10.1f %-10.1f %-10.1f %-10.1f  %-11.1f %-11.1f" % (f, *vals, *tw))
