"""Pull the leftover tail stubs inside the body and add a clean tail."""

import math
import os

import bpy
import bmesh
from mathutils import Vector

BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_game.blend"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
body = bpy.data.objects["Wukong_LOD0"]

# ---- tuck the remaining stubs inside the skirt ------------------------------
bm = bmesh.new()
bm.from_mesh(body.data)
target = Vector((0.0, 0.02, 0.84))
moved = 0
for vert in bm.verts:
    co = vert.co
    if 0.66 <= co.z <= 0.92 and 0.16 <= abs(co.x) <= 0.36 and co.y >= 0.06:
        vert.co = co.lerp(target, 0.85)
        moved += 1
print("TUCKED", moved)
bm.to_mesh(body.data)
bm.free()

# ---- tail mesh ---------------------------------------------------------------
points = [
    Vector((0.10, 0.12, 0.95)),
    Vector((0.16, 0.22, 0.98)),
    Vector((0.20, 0.33, 1.08)),
    Vector((0.18, 0.40, 1.22)),
    Vector((0.14, 0.42, 1.34)),
]
radii = [1.0, 0.9, 0.72, 0.5, 0.28]

curve_data = bpy.data.curves.new("TailCurve", "CURVE")
curve_data.dimensions = "3D"
curve_data.bevel_depth = 0.05
curve_data.bevel_resolution = 4
curve_data.use_fill_caps = True
spline = curve_data.splines.new("BEZIER")
spline.bezier_points.add(len(points) - 1)
for i, point in enumerate(points):
    bp = spline.bezier_points[i]
    bp.co = point
    bp.handle_left_type = "AUTO"
    bp.handle_right_type = "AUTO"
    bp.radius = radii[i]

tail = bpy.data.objects.new("Wukong_tail", curve_data)
scene.collection.objects.link(tail)
bpy.context.view_layer.objects.active = tail
tail.select_set(True)
bpy.ops.object.convert(target="MESH")
tail = bpy.context.object

# weights from distance to the tail bone segments
rig = bpy.data.objects["Wukong_Rig"]
bones = ["tail_01", "tail_02", "tail_03", "tail_04"]


def segment_distance(point, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (point - a).dot(ab) / ab.length_squared))
    return (point - (a + ab * t)).length


for name in bones:
    if name not in tail.vertex_groups:
        tail.vertex_groups.new(name=name)

bone_segments = {
    name: (Vector(rig.data.bones[name].head_local), Vector(rig.data.bones[name].tail_local))
    for name in bones
}

for vert in tail.data.vertices:
    distances = {
        name: segment_distance(vert.co, seg[0], seg[1]) for name, seg in bone_segments.items()
    }
    total = 0.0
    weights = {}
    for name, dist in distances.items():
        weight = 1.0 / (dist + 0.01) ** 3
        weights[name] = weight
        total += weight
    for name, weight in weights.items():
        tail.vertex_groups[name].add([vert.index], weight / total, "REPLACE")

modifier = tail.modifiers.new("Armature", "ARMATURE")
modifier.object = rig
tail.parent = rig

# ---- renders -----------------------------------------------------------------
cam = bpy.data.objects.get("CAM")
if cam is None:
    cam_data = bpy.data.cameras.new("CAM")
    cam = bpy.data.objects.new("CAM", cam_data)
    scene.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.2
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True

for name, loc, rot in (
    ("tail_front", (0, -6, 0.95), (90, 0, 0)),
    ("tail_back", (0, 6, 0.95), (90, 0, 180)),
    ("tail_side", (6, 0, 0.95), (90, 0, 90)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("DONE")
