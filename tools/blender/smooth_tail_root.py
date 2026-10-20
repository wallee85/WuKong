"""Smooth the tail root vertices to soften the kink."""

import bpy
import bmesh
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
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    verts = [
        v for v in bm.verts
        if chain_distance(v.co) < 0.085 and v.co.z < 0.68
    ]
    print(obj_name, "SMOOTH_VERTS", len(verts))
    for _ in range(4):
        bmesh.ops.smooth_vert(
            bm,
            verts=verts,
            factor=0.5,
            use_axis_x=True,
            use_axis_y=True,
            use_axis_z=True,
        )
    bm.to_mesh(obj.data)
    bm.free()

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED")
