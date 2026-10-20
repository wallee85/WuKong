"""check_run_action.py, but on the file already open (no reopen from BLEND)."""
import math

import bpy

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

print("%5s %7s | %6s %6s %6s | %6s %6s %6s | %7s"
      % ("frame", "minZ", "ankL", "toeL", "pitL", "ankR", "toeR", "pitR", "hipZ"))
for f in range(0, 19):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    evb = body.evaluated_get(dg)
    me = evb.to_mesh()
    mw = body.matrix_world
    minz = min((mw @ v.co).z for v in me.vertices)
    evb.to_mesh_clear()
    ev = rig.evaluated_get(dg)
    pose = ev.pose
    out = [f, minz]
    for side in ("l", "r"):
        foot = pose.bones["foot_%s" % side]
        toe = pose.bones["toe_%s" % side]
        d = (rig.matrix_world.to_3x3() @ (foot.tail - foot.head)).normalized()
        rest = REST_DIR[side]
        ang = math.degrees(math.atan2(d.y, -d.z) - math.atan2(rest.y, -rest.z))
        ang = (ang + 180) % 360 - 180
        out += [(rig.matrix_world @ foot.head).z, (rig.matrix_world @ toe.tail).z, ang]
    out.append((rig.matrix_world @ pose.bones["pelvis"].head).z)
    print("%5d %7.3f | %6.3f %6.3f %6.1f | %6.3f %6.3f %6.1f | %7.3f" % tuple(out))
