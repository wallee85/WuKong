import bpy, collections, math
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
ob=bpy.data.objects["Wukong_LOD0"]; me=ob.data
gname={g.index:g.name for g in ob.vertex_groups}
dom=collections.Counter()
for v in me.vertices:
    if not v.groups: dom["<none>"]+=1; continue
    g=max(v.groups, key=lambda g:g.weight)
    dom[gname.get(g.group,"?")]+=1
print("dominant group counts:")
for k,n in dom.most_common(): print("  %-12s %5d" % (k,n))
# z histogram for pelvis-dominant verts
pv=[]
for v in me.vertices:
    if not v.groups: continue
    g=max(v.groups, key=lambda g:g.weight)
    if gname.get(g.group)=="pelvis":
        pv.append(v.co.copy())
print("pelvis verts", len(pv), "z %.3f..%.3f" % (min(p.z for p in pv), max(p.z for p in pv)))
hist=collections.Counter(round(p.z,1) for p in pv)
for z in sorted(hist): print("  z %.1f : %d" % (z, hist[z]))
rad=[math.hypot(p.x,p.y) for p in pv]
print("radius max %.3f  mean %.3f" % (max(rad), sum(rad)/len(rad)))
