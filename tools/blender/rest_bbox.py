import bpy
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
rig=bpy.data.objects["Wukong_Rig"]
if rig.animation_data: rig.animation_data.action=None
for pb in rig.pose.bones:
    pb.location=(0,0,0); pb.rotation_quaternion=(1,0,0,0); pb.scale=(1,1,1); pb.rotation_mode="QUATERNION"
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
body=bpy.data.objects["Wukong_LOD0"]
evb=body.evaluated_get(dg); me=evb.to_mesh(); mw=body.matrix_world
zs=[(mw@v.co).z for v in me.vertices]; xs=[(mw@v.co).x for v in me.vertices]; ys=[(mw@v.co).y for v in me.vertices]
print("REST bbox z %.4f..%.4f  x %.4f..%.4f  y %.4f..%.4f" % (min(zs),max(zs),min(xs),max(xs),min(ys),max(ys)))
evb.to_mesh_clear()
