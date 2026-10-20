import bpy, collections
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
ob=bpy.data.objects["Wukong_LOD0"]; me=ob.data
gname={g.index:g.name for g in ob.vertex_groups}
adj=collections.defaultdict(set)
for e in me.edges:
    a,b=e.vertices; adj[a].add(b); adj[b].add(a)
seen=[False]*len(me.vertices)
islands=[]
for v in range(len(me.vertices)):
    if seen[v]: continue
    stack=[v]; seen[v]=True; comp=[]
    while stack:
        n=stack.pop(); comp.append(n)
        for m in adj[n]:
            if not seen[m]: seen[m]=True; stack.append(m)
    islands.append(comp)
print("islands:", len(islands))
print("%4s %6s %7s %7s %8s %8s  %s" % ("#","verts","zmin","zmax","ymin","ymax","top group"))
for i,comp in enumerate(islands):
    zs=[me.vertices[v].co.z for v in comp]
    ys=[me.vertices[v].co.y for v in comp]
    w=collections.Counter()
    for v in comp:
        for g in me.vertices[v].groups:
            w[gname.get(g.group,"?")] += g.weight
    top=", ".join("%s:%.0f"%(k,val) for k,val in w.most_common(2))
    if len(comp) >= 40:
        print("%4d %6d %7.3f %7.3f %8.3f %8.3f  %s" % (i,len(comp),min(zs),max(zs),min(ys),max(ys),top))
