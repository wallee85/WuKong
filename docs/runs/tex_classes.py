import bpy, colorsys, collections
bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
ob=bpy.data.objects["Wukong_LOD0"]; me=ob.data
img=bpy.data.images['texture_pbr_20250901']
W,H=img.size
px=list(img.pixels)   # RGBA, row 0 = bottom
def sample(u,v):
    x=int((u%1.0)*(W-1)); y=int((v%1.0)*(H-1))
    i=(y*W+x)*4
    return px[i],px[i+1],px[i+2]
uvl=me.uv_layers.active.data
classes=collections.defaultdict(lambda:[1e9,-1e9,0])
for p in me.polygons:
    us=[];vs=[]
    for li in p.loop_indices:
        uv=uvl[li].uv; us.append(uv.x); vs.append(uv.y)
    r,g,b=sample(sum(us)/len(us), sum(vs)/len(vs))
    h,s,v = colorsys.rgb_to_hsv(r,g,b)
    if v < 0.10: c="black"
    elif s < 0.18: c="white/grey"
    elif 0.42 <= h <= 0.62: c="blue/teal"
    elif h < 0.09 or h > 0.93: c="red/brown"
    elif 0.09 <= h < 0.20: c="orange/gold"
    else: c="other(h=%.2f)"%h
    zs=[me.vertices[i].co.z for i in p.vertices]
    st=classes[c]; st[0]=min(st[0],min(zs)); st[1]=max(st[1],max(zs)); st[2]+=1
for c,(lo,hi,n) in sorted(classes.items(), key=lambda kv:-kv[1][2]):
    print("%-12s z %.3f..%.3f  faces %5d" % (c, lo, hi, n))
