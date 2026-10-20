"""Remove the remaining tail stubs and close the holes."""

import math
import os

import bpy
import bmesh

BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_game.blend"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"

bpy.ops.wm.open_mainfile(filepath=BLEND)
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
bpy.context.view_layer.objects.active = obj

bm = bmesh.new()
bm.from_mesh(obj.data)


def in_region(co):
    return 0.66 <= co.z <= 0.92 and 0.15 <= abs(co.x) <= 0.34 and co.y >= 0.05


faces = [f for f in bm.faces if in_region(f.calc_center_median())]
print("STUB_FACES", len(faces))
bmesh.ops.delete(bm, geom=faces, context="FACES")

boundary = [e for e in bm.edges if len(e.link_faces) == 1]
adj = {}
for edge in boundary:
    for vert in edge.verts:
        adj.setdefault(vert, []).append(edge)

seen = set()
loops = []
for edge in boundary:
    if edge in seen:
        continue
    stack = [edge]
    loop = []
    seen.add(edge)
    while stack:
        current = stack.pop()
        loop.append(current)
        for vert in current.verts:
            for other in adj.get(vert, []):
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
    loops.append(loop)

from mathutils import Vector

filled = 0
for loop in loops:
    verts = {v for e in loop for v in e.verts}
    if not verts:
        continue
    center = Vector((0.0, 0.0, 0.0))
    for vert in verts:
        center += vert.co
    center /= len(verts)
    if in_region(center) and len(loop) < 300:
        try:
            bmesh.ops.holes_fill(bm, edges=loop, sides=0)
            filled += 1
        except Exception as exc:  # noqa: BLE001
            print("FILL_FAIL", len(loop), exc)
print("LOOPS", len(loops), "FILLED", filled)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(obj.data)
bm.free()

scene = bpy.context.scene
cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.2
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True

for name, loc, rot in (
    ("stub_front", (0, -6, 0.95), (90, 0, 0)),
    ("stub_back", (0, 6, 0.95), (90, 0, 180)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
