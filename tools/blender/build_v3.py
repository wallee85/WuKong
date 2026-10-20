"""Final asset build: single tail, LODs, armature, skin, idle, GLB export."""

import math
import os

import bpy
import bmesh
from mathutils import Vector

GLB = r"D:\Workspace\games\WuKong\source\glb\wukong_v2.glb"
OUT = r"D:\Workspace\games\WuKong\docs\renders"
BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
EXPORT = r"D:\Workspace\games\WuKong\source\glb\wukong.glb"

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
bm.to_mesh(body.data)
bm.free()

corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
scale = 1.895 / (mx.z - mn.z)
body.scale = (scale, scale, scale)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
corners = [body.matrix_world @ Vector(c) for c in body.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
body.location.x -= (mn.x + mx.x) / 2
body.location.y -= (mn.y + mx.y) / 2
body.location.z -= mn.z
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

# single tail in this generation - no geometry surgery needed

tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
dec = body.modifiers.new("LOD0", "DECIMATE")
dec.ratio = 18000 / tris
bpy.ops.object.modifier_apply(modifier="LOD0")

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

# LOD1 / LOD2 inherit the skin weights
def make_lod(source, target_tris, name):
    lod = source.copy()
    lod.data = source.data.copy()
    lod.name = name
    scene.collection.objects.link(lod)
    for modifier in list(lod.modifiers):
        if modifier.type == "ARMATURE":
            lod.modifiers.remove(modifier)
    current = sum(len(p.vertices) - 2 for p in lod.data.polygons)
    decimator = lod.modifiers.new("LOD", "DECIMATE")
    decimator.ratio = target_tris / current
    bpy.context.view_layer.objects.active = lod
    bpy.ops.object.modifier_apply(modifier="LOD")
    arm = lod.modifiers.new("Armature", "ARMATURE")
    arm.object = rig
    return lod


lod1 = make_lod(body, 8000, "Wukong_LOD1")
lod2 = make_lod(body, 3500, "Wukong_LOD2")

# idle animation (2 s loop)
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 61
rig.animation_data_create()
for pose_bone in rig.pose.bones:
    pose_bone.rotation_mode = "XYZ"

KEYS = {
    "pelvis": [(1, (0.0, 0.0, 0.0)), (31, (0.015, 0.0, 0.0)), (61, (0.0, 0.0, 0.0))],
    "chest": [(1, (0.0, 0.0, 0.0)), (31, (-0.02, 0.0, 0.0)), (61, (0.0, 0.0, 0.0))],
    "head": [(1, (0.0, 0.0, 0.0)), (31, (0.01, 0.0, 0.02)), (61, (0.0, 0.0, 0.0))],
    "upperarm_l": [(1, (0.0, 0.0, 0.0)), (31, (0.0, 0.02, 0.0)), (61, (0.0, 0.0, 0.0))],
    "upperarm_r": [(1, (0.0, 0.0, 0.0)), (31, (0.0, -0.02, 0.0)), (61, (0.0, 0.0, 0.0))],
}
for bone_name, keys in KEYS.items():
    pose_bone = rig.pose.bones.get(bone_name)
    if pose_bone is None:
        continue
    for frame, euler in keys:
        pose_bone.rotation_euler = euler
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)

# renders
cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True

cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.2
cam.location = (0, -6, 0.95)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.frame_set(1)
scene.render.filepath = os.path.join(OUT, "final_rest.png")
bpy.ops.render.render(write_still=True)

cam.data.type = "PERSP"
cam.data.lens = 70
cam.location = (2.2, -3.2, 1.9)
cam.rotation_euler = (Vector((0, 0, 1.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.frame_set(31)
scene.render.resolution_x = 1000
scene.render.resolution_y = 1300
scene.render.film_transparent = False
scene.render.filepath = os.path.join(OUT, "final_idle.png")
bpy.ops.render.render(write_still=True)

os.makedirs(os.path.dirname(EXPORT), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=EXPORT,
    export_format="GLB",
    export_animations=True,
    export_skins=True,
    export_apply=False,
    use_selection=False,
)
print("EXPORTED", EXPORT, os.path.getsize(EXPORT))
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)

