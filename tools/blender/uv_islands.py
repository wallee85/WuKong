"""Decompose the mesh into UV islands and describe each one.

  blender -b --python tools/blender/uv_islands.py
"""
import collections

import bpy

bpy.ops.wm.open_mainfile(filepath=r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend")
ob = bpy.data.objects["Wukong_LOD0"]
me = ob.data
uvl = me.uv_layers.active.data
img = bpy.data.images["texture_pbr_20250901"]
W, H = img.size
px = list(img.pixels)


def sample(u, v):
    x = int((u % 1.0) * (W - 1))
    y = int((v % 1.0) * (H - 1))
    i = (y * W + x) * 4
    return px[i], px[i + 1], px[i + 2]


# union-find over loops
parent = list(range(len(uvl)))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra


EPS = 1e-4
vert_loops = collections.defaultdict(list)
for loop in me.loops:
    vert_loops[loop.vertex_index].append(loop.index)
for loops in vert_loops.values():
    for i in range(len(loops)):
        for j in range(i + 1, len(loops)):
            a, b = loops[i], loops[j]
            ua, va = uvl[a].uv
            ub, vb = uvl[b].uv
            if abs(ua - ub) < EPS and abs(va - vb) < EPS:
                union(a, b)

for poly in me.polygons:
    loops = list(poly.loop_indices)
    for i in range(len(loops)):
        a, b = loops[i], loops[(i + 1) % len(loops)]
        for other in loops[i + 1:]:
            pass
# stitch across shared edges: faces sharing an edge with matching UVs belong together
edge_faces = collections.defaultdict(list)
for poly in me.polygons:
    ls = list(poly.loop_indices)
    for i in range(len(ls)):
        a = ls[i]
        b = ls[(i + 1) % len(ls)]
        va, vb = me.loops[a].vertex_index, me.loops[b].vertex_index
        edge_faces[tuple(sorted((va, vb)))].append((a, b))

for key, pairs in edge_faces.items():
    if len(pairs) != 2:
        continue
    (a1, b1), (a2, b2) = pairs
    d1 = (uvl[a1].uv - uvl[a2].uv).length + (uvl[b1].uv - uvl[b2].uv).length
    d2 = (uvl[a1].uv - uvl[b2].uv).length + (uvl[b1].uv - uvl[a2].uv).length
    if min(d1, d2) < EPS * 8:
        union(a1, a2)

groups = collections.defaultdict(list)
for poly in me.polygons:
    groups[find(poly.loop_indices[0])].append(poly)

print("uv islands:", len(groups))
rows = []
for root, polys in groups.items():
    vids = set()
    cols = []
    for poly in polys:
        vids.update(poly.vertices)
        us = [uvl[li].uv for li in poly.loop_indices]
        c = sample(sum(u.x for u in us) / len(us), sum(u.y for u in us) / len(us))
        cols.append(c)
    zs = [me.vertices[v].co.z for v in vids]
    xs = [me.vertices[v].co.x for v in vids]
    r = sum(c[0] for c in cols) / len(cols)
    g = sum(c[1] for c in cols) / len(cols)
    b = sum(c[2] for c in cols) / len(cols)
    rows.append((len(vids), min(zs), max(zs), min(xs), max(xs), r, g, b, len(polys)))

rows.sort(key=lambda t: -t[0])
print("%6s %6s %6s %8s %6s %6s %6s %6s %6s" % (
    "verts", "zmin", "zmax", "zspan", "red", "green", "blue", "faces", "xmin"))
for nv, z0, z1, x0, x1, r, g, b, nf in rows:
    if nv < 25:
        continue
    print("%6d %6.3f %6.3f %8.3f %6.2f %6.2f %6.2f %6d %6.3f" % (
        nv, z0, z1, z1 - z0, r, g, b, nf, x0))
