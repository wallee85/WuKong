"""Measure where the two tail protrusions are, in metres."""

import bpy
import bmesh
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")

bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0003)
bm.to_mesh(obj.data)
bm.free()

corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
s = 1.895 / (mx.z - mn.z)
obj.scale = (s, s, s)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
obj.location.x -= (mn.x + mx.x) / 2
obj.location.y -= (mn.y + mx.y) / 2
obj.location.z -= mn.z
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

mesh = obj.data
print("DIMS", [round(v, 3) for v in obj.dimensions])
for z0 in (0.70, 0.80, 0.90, 1.00, 1.10):
    xs = [v.co.x for v in mesh.vertices if z0 <= v.co.z < z0 + 0.1]
    if not xs:
        continue
    xs.sort()
    print(
        "BAND", f"{z0:.2f}-{z0+0.1:.2f}",
        "xmin", round(xs[0], 3), "xmax", round(xs[-1], 3),
        "p01", round(xs[int(len(xs) * 0.01)], 3), "p99", round(xs[int(len(xs) * 0.99)], 3),
        "n", len(xs),
        "beyond0.26", sum(1 for x in xs if abs(x) > 0.26),
    )
