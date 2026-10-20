"""Build LOD0 (18k), a humanoid armature and skin weights for the Wukong mesh."""

import math
import os

import bpy
from mathutils import Vector

BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_game.blend"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
body = next(o for o in scene.objects if o.type == "MESH")
body.name = "Wukong_LOD0"

# ---- decimate to game resolution -------------------------------------------
tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
print("SOURCE_TRIS", tris)
bpy.context.view_layer.objects.active = body
body.select_set(True)
dec = body.modifiers.new("LOD0", "DECIMATE")
dec.ratio = 18000 / tris
bpy.ops.object.modifier_apply(modifier="LOD0")
print("LOD0_TRIS", sum(len(p.vertices) - 2 for p in body.data.polygons))

# ---- armature ---------------------------------------------------------------
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
    ("tail_01", (0.10, 0.10, 0.95), (0.16, 0.22, 0.98), "pelvis", True),
    ("tail_02", (0.16, 0.22, 0.98), (0.20, 0.33, 1.08), "tail_01", True),
    ("tail_03", (0.20, 0.33, 1.08), (0.18, 0.40, 1.22), "tail_02", True),
    ("tail_04", (0.18, 0.40, 1.22), (0.14, 0.42, 1.34), "tail_03", True),
    ("weapon_r", (-0.53, 0, 0.88), (-0.53, -0.06, 0.88), "hand_r", False),
]

arm_data = bpy.data.armatures.new("Wukong_Rig")
rig = bpy.data.objects.new("Wukong_Rig", arm_data)
scene.collection.objects.link(rig)

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
for name, head, tail, parent, deform in BONES:
    edit_bone = arm_data.edit_bones.new(name)
    edit_bone.head = head
    edit_bone.tail = tail
    edit_bone.use_deform = deform
    if parent:
        edit_bone.parent = arm_data.edit_bones[parent]
        edit_bone.use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")

# ---- skin -------------------------------------------------------------------
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
print("PARENTED", body.parent.name if body.parent else None,
      "GROUPS", len(body.vertex_groups))

# ---- pose test ---------------------------------------------------------------
import math

for bone_name, angle in (("upperarm_l", -50), ("upperarm_r", -50)):
    pb = rig.pose.bones.get(bone_name)
    if pb:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, math.radians(angle))

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.2
cam.location = (0, -6, 0.95)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True
scene.render.filepath = os.path.join(OUT, "rig_pose_test.png")
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("DONE")
