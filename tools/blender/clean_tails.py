"""Remove the duplicated tails (after normalising scale) and save the model."""

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

# normalise BEFORE cutting, so the region is in metres
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
    return 0.55 <= co.z <= 0.80 and 0.20 <= abs(co.x) <= 0.46 and co.y > -0.02


faces = [f for f in bm.faces if in_region(f.calc_center_median())]
print("TAIL_FACES", len(faces))
bmesh.ops.delete(bm, geom=faces, context="FACES")

boundary = [e for e in bm.edges if len(e.link_faces) == 1]
near = [e for e in boundary if in_region(e.verts[0].co) or in_region(e.verts[1].co)]
print("BOUNDARY_NEAR", len(near))
if near:
    bmesh.ops.triangle_fill(bm, use_beauty=True, edges=near)
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
    ("clean2_front", (0, -6, 0.95), (90, 0, 0)),
    ("clean2_back", (0, 6, 0.95), (90, 0, 180)),
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
