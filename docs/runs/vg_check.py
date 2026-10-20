import bpy
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
for name in ("Wukong_LOD0","Wukong_LOD1","Wukong_LOD2"):
    ob=bpy.data.objects.get(name)
    if not ob: continue
    vg=[g.name for g in ob.vertex_groups]
    print(name, "groups", len(vg), "stale:", [g for g in vg if g not in {b.name for b in bpy.data.objects["Wukong_Rig"].data.bones}])
print("armature bones", len(bpy.data.objects["Wukong_Rig"].data.bones))
