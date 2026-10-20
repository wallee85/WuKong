"""Give the tail vertices proper weights on the tail bone chain."""

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"

bpy.ops.wm.open_mainfile(filepath=BLEND)
rig = bpy.data.objects["Wukong_Rig"]
bones = ["tail_01", "tail_02", "tail_03", "tail_04"]
segments = [
    (Vector(rig.data.bones[name].head_local), Vector(rig.data.bones[name].tail_local))
    for name in bones
]


def segment_distance(point, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (point - a).dot(ab) / ab.length_squared))
    return (point - (a + ab * t)).length


def chain_distance(point):
    return min(segment_distance(point, a, b) for a, b in segments)


for obj_name in ("Wukong_LOD0", "Wukong_LOD1", "Wukong_LOD2"):
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        continue
    groups = {vg.name: vg for vg in obj.vertex_groups}
    missing = [name for name in bones if name not in groups]
    for name in missing:
        groups[name] = obj.vertex_groups.new(name=name)

    touched = 0
    for vert in obj.data.vertices:
        distance = chain_distance(vert.co)
        if distance > 0.075:
            continue
        touched += 1
        weights = {}
        total = 0.0
        for name, (a, b) in zip(bones, segments):
            d = segment_distance(vert.co, a, b)
            w = 1.0 / (d + 0.01) ** 4
            weights[name] = w
            total += w
        for vg in obj.vertex_groups:
            vg.remove([vert.index])
        for name, w in weights.items():
            groups[name].add([vert.index], w / total, "REPLACE")
    print(obj_name, "TAIL_VERTS", touched)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED")
