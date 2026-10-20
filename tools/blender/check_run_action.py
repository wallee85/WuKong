"""Verify the baked run cycle in a fresh process: ground contact and foot pitch.

  blender -b --python tools/blender/check_run_action.py
"""
import math

import bpy

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
body = bpy.data.objects["Wukong_LOD0"]
act = bpy.data.actions["Run"]
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = act
for s in act.slots:
    rig.animation_data.action_slot = s
    break

REST_DIR = {}
for side in ("l", "r"):
    b = rig.data.bones["foot_%s" % side]
    REST_DIR[side] = (b.tail_local - b.head_local).normalized()

print("%5s %7s | %6s %6s %6s | %6s %6s %6s | %7s" % (
    "frame", "minZ", "ankL", "toeL", "pitL", "ankR", "toeR", "pitR", "hipZ"))
prev = {}
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = rig.evaluated_get(dg)
    pose = ev.pose
    evb = body.evaluated_get(dg)
    me = evb.to_mesh()
    mw = body.matrix_world
    minz = min((mw @ v.co).z for v in me.vertices)
    evb.to_mesh_clear()

    out = [f, minz]
    pitch = {}
    for side in ("l", "r"):
        foot = pose.bones["foot_%s" % side]
        toe = pose.bones["toe_%s" % side]
        ank = rig.matrix_world @ foot.head
        toe_tip = rig.matrix_world @ toe.tail
        d = (rig.matrix_world.to_3x3() @ (foot.tail - foot.head)).normalized()
        # pitch relative to the rest foot direction, positive = toe down
        rest = REST_DIR[side]
        ang = math.degrees(math.atan2(d.y, -d.z) - math.atan2(rest.y, -rest.z))
        ang = (ang + 180) % 360 - 180
        pitch[side] = ang
        out += [ank.z, toe_tip.z, ang]
    out.append((rig.matrix_world @ pose.bones["pelvis"].head).z)
    print("%5d %7.3f | %6.3f %6.3f %6.1f | %6.3f %6.3f %6.1f | %7.3f"
          % (out[0], out[1], out[2], out[3], out[4], out[5], out[6], out[7], out[8]))
print("rest sole z = 0.0794; a planted foot should put minZ on that value")
