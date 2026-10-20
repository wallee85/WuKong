"""Second attempt: cut both tails including their stubs, then close the loops."""

import math
import os

import bpy
import bmesh
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"
BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_game.blend"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
obj.name = "Wukong_body"
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

bm = bmesh.new()
bm.from_mesh(obj.data)


def in_region(co):
    return 0.50 <= co.z <= 0.88 and 0.21 <= abs(co.x) <= 0.47 and co.y > -0.03


faces = [f for f in bm.faces if in_region(f.calc_center_median())]
print("TAIL_FACES", len(faces))
bmesh.ops.delete(bm, geom=faces, context="FACES")

# group boundary edges into loops
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

print("LOOPS", len(loops), "sizes", sorted((len(l) for l in loops), reverse=True)[:8])

filled = 0
for loop in loops:
    verts = {v for e in loop for v in e.verts}
    if all(in_region(v.co) for v in verts) and len(loop) < 400:
        try:
            bmesh.ops.holes_fill(bm, edges=loop, sides=0)
            filled += 1
        except Exception as exc:  # noqa: BLE001
            print("FILL_FAIL", len(loop), exc)
print("FILLED_LOOPS", filled)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(obj.data)
bm.free()

print("CLEAN_DIMS", [round(v, 3) for v in obj.dimensions],
      "TRIS", sum(len(p.vertices) - 2 for p in obj.data.polygons))

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
    ("clean3_front", (0, -6, 0.95), (90, 0, 0)),
    ("clean3_back", (0, 6, 0.95), (90, 0, 180)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)

world = bpy.data.worlds.new("W")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
bg.inputs[0].default_value = (0.05, 0.05, 0.06, 1.0)
scene.world = world
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
