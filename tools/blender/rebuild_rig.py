"""Rebuild the game mesh from the GLB, hiding the duplicate tail, and rig it."""

import math
import os

import bpy
import bmesh
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"
BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_rigged.blend"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
scene = bpy.context.scene
body = next(o for o in scene.objects if o.type == "MESH")
body.name = "Wukong_LOD0"
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bm = bmesh.new()
bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0003)

# normalise to metres before spatial edits
bm.to_mesh(body.data)
bm.free()
corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
s = 1.895 / (mx.z - mn.z)
body.scale = (s, s, s)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
body.location.x -= (mn.x + mx.x) / 2
body.location.y -= (mn.y + mx.y) / 2
body.location.z -= mn.z
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

# collapse the duplicated right-hand tail into the hip (invisible, no hole)
bm = bmesh.new()
bm.from_mesh(body.data)
anchor = Vector((-0.16, 0.10, 0.86))
collapsed = 0
for vert in bm.verts:
    co = vert.co
    if co.x < -0.16 and 0.50 <= co.z <= 0.98 and co.y > -0.06 and co.x > -0.55:
        vert.co = anchor + (co - anchor) * 0.04
        collapsed += 1
print("COLLAPSED", collapsed)
bm.to_mesh(body.data)
bm.free()

tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
print("SOURCE_TRIS", tris)
dec = body.modifiers.new("LOD0", "DECIMATE")
dec.ratio = 18000 / tris
bpy.ops.object.modifier_apply(modifier="LOD0")
print("LOD0_TRIS", sum(len(p.vertices) - 2 for p in body.data.polygons))

BONES = [
    ("root", (0, 0, 0), (0, 0, 0.12), None, False),
    ("pelvis", (0, 0, 0.95), (0, 0, 1.05), "root", True),
    ("spine_01", (0, 0, 1.05), (0, 0, 1.18), "pelvis", True),
    ("spine_02", (0, 0, 1.18), (0, 0, 1.32), "spine_01", True),
    ("chest", (0, 0, 1.32), (0, 0, 1.46), "spine_02", True),
    ("neck", (0, 0, 1.46), (0, 0, 1.58), "chest", True),
    ("head", (0, 0, 1.58), (0, 0, 1.84), "neck", True),
    ("clavicle_l", (0.03, 0, 1.42), (0.18, 0, 1.42), "chest", True),
    ("upperarm_l", (0.18, 0, 1.42), (0.33, 0, 1.17), "clavicle_l", True),
    ("lowerarm_l", (0.33, 0, 1.17), (0.44, 0, 0.97), "upperarm_l", True),
    ("hand_l", (0.44, 0, 0.97), (0.53, 0, 0.88), "lowerarm_l", True),
    ("clavicle_r", (-0.03, 0, 1.42), (-0.18, 0, 1.42), "chest", True),
    ("upperarm_r", (-0.18, 0, 1.42), (-0.33, 0, 1.17), "clavicle_r", True),
    ("lowerarm_r", (-0.33, 0, 1.17), (-0.44, 0, 0.97), "upperarm_r", True),
    ("hand_r", (-0.44, 0, 0.97), (-0.53, 0, 0.88), "lowerarm_r", True),
    ("thigh_l", (0.10, 0, 0.92), (0.11, 0, 0.50), "pelvis", True),
    ("shin_l", (0.11, 0, 0.50), (0.12, 0, 0.10), "thigh_l", True),
    ("foot_l", (0.12, 0, 0.10), (0.12, -0.12, 0.03), "shin_l", True),
    ("toe_l", (0.12, -0.12, 0.03), (0.12, -0.19, 0.02), "foot_l", True),
    ("thigh_r", (-0.10, 0, 0.92), (-0.11, 0, 0.50), "pelvis", True),
    ("shin_r", (-0.11, 0, 0.50), (-0.12, 0, 0.10), "thigh_r", True),
    ("foot_r", (-0.12, 0, 0.10), (-0.12, -0.12, 0.03), "shin_r", True),
    ("toe_r", (-0.12, -0.12, 0.03), (-0.12, -0.19, 0.02), "foot_r", True),
    ("weapon_r", (-0.53, 0, 0.88), (-0.53, -0.06, 0.88), "hand_r", False),
]

arm_data = bpy.data.armatures.new("Wukong_Rig")
rig = bpy.data.objects.new("Wukong_Rig", arm_data)
scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
for name, head, tail, parent, deform in BONES:
    eb = arm_data.edit_bones.new(name)
    eb.head = head
    eb.tail = tail
    eb.use_deform = deform
    if parent:
        eb.parent = arm_data.edit_bones[parent]
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
print("GROUPS", len(body.vertex_groups))

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
    ("build_front", (0, -6, 0.95), (90, 0, 0)),
    ("build_back", (0, 6, 0.95), (90, 0, 180)),
    ("build_side", (6, 0, 0.95), (90, 0, 90)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
