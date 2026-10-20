import bpy, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
scene=bpy.context.scene; rig=bpy.data.objects["Wukong_Rig"]
act=bpy.data.actions["Run"]; rig.animation_data.action=act
for s in act.slots: rig.animation_data.action_slot=s; break
def yaw(m3):
    x=m3.col[0]
    return math.degrees(math.atan2(x.y, x.x))
rows=[]
for f in range(0,14):
    scene.frame_set(f)
    dg=bpy.context.evaluated_depsgraph_get(); ev=rig.evaluated_get(dg)
    rows.append((f, yaw(ev.pose.bones["pelvis"].matrix.to_3x3()),
                    yaw(ev.pose.bones["chest"].matrix.to_3x3()),
                    yaw(ev.pose.bones["head"].matrix.to_3x3())))
print("%5s %9s %9s %9s" % ("f","pelvis","chest","head"))
for r in rows: print("%5d %9.2f %9.2f %9.2f" % r)
print("HEAD yaw range = %.2f deg   CHEST range = %.2f   PELVIS range = %.2f" % (
    max(r[3] for r in rows)-min(r[3] for r in rows),
    max(r[2] for r in rows)-min(r[2] for r in rows),
    max(r[1] for r in rows)-min(r[1] for r in rows)))
