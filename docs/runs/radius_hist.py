import bpy, collections, math
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
me=bpy.data.objects["Wukong_LOD0"].data
bins=collections.defaultdict(int)
for v in me.vertices:
    p=v.co
    if not (0.35 <= p.z <= 1.00): continue
    r=math.hypot(p.x,p.y)
    zb=round(p.z*20)/20.0
    rb=round(r*10)/10.0
    bins[(zb,rb)]+=1
rs=sorted({k[1] for k in bins})
print("z\\r   " + " ".join("%5.1f"%r for r in rs))
for z in sorted({k[0] for k in bins}):
    print("%.2f  " % z + " ".join("%5d"%bins.get((z,r),0) for r in rs))
