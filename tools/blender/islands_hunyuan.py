"""List connected components of the Hunyuan mesh with their bounds."""

import bpy
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
mesh = obj.data

# union-find over vertices
parent = list(range(len(mesh.vertices)))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra


for edge in mesh.edges:
    union(edge.vertices[0], edge.vertices[1])

from collections import defaultdict

islands = defaultdict(list)
for index, vert in enumerate(mesh.vertices):
    islands[find(index)].append(index)

stats = []
for root, verts in islands.items():
    coords = [mesh.vertices[i].co for i in verts]
    mn = Vector((min(c.x for c in coords), min(c.y for c in coords), min(c.z for c in coords)))
    mx = Vector((max(c.x for c in coords), max(c.y for c in coords), max(c.z for c in coords)))
    stats.append((len(verts), mn, mx, mx - mn))

stats.sort(key=lambda s: -s[0])
print("ISLANDS", len(stats))
for count, mn, mx, size in stats[:15]:
    print(
        "ISLAND",
        count,
        "min", [round(v, 3) for v in mn],
        "max", [round(v, 3) for v in mx],
        "size", [round(v, 3) for v in size],
    )
