import bpy
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
ob=bpy.data.objects["Wukong_LOD0"]
me=ob.data
print("materials:", [(i,m.name if m else None) for i,m in enumerate(me.materials)])
# per-material z range and face count
import collections
stats=collections.defaultdict(lambda:[1e9,-1e9,0])
for p in me.polygons:
    zs=[me.vertices[v].co.z for v in p.vertices]
    s=stats[p.material_index]
    s[0]=min(s[0],min(zs)); s[1]=max(s[1],max(zs)); s[2]+=1
for mi,(lo,hi,n) in sorted(stats.items()):
    name=me.materials[mi].name if mi < len(me.materials) and me.materials[mi] else "?"
    print("mat %2d %-40s z %.3f..%.3f  faces %d" % (mi, name, lo, hi, n))
print("total verts", len(me.vertices), "polys", len(me.polygons))
