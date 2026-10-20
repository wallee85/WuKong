import bpy, collections
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
ob=bpy.data.objects["Wukong_LOD0"]; me=ob.data
rig=bpy.data.objects["Wukong_Rig"]
segs=[]
for n in ("thigh_l","thigh_r","shin_l","shin_r"):
    b=rig.data.bones[n]
    segs.append((b.head_local.copy(), b.tail_local.copy()))
def dist_seg(p,a,b):
    ab=b-a; t=max(0.0,min(1.0,(p-a).dot(ab)/ab.length_squared))
    return (p-(a+ab*t)).length
bands=collections.defaultdict(lambda:[0,0])
for v in me.vertices:
    p=v.co
    d=min(dist_seg(p,a,b) for a,b in segs)
    zb=round(p.z*20)/20.0
    bands[zb][1 if d>0.10 else 0]+=1
print("z-band   near(<0.10)  loose(>0.10)")
for z in sorted(bands):
    if z < 1.15:
        n,l=bands[z]; print("  %.2f %10d %12d" % (z,n,l))
