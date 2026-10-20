"""Add a grip_r bone at the measured fist centre and export."""

import bpy

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"

bpy.ops.wm.open_mainfile(filepath=BLEND)
rig = bpy.data.objects["Wukong_Rig"]
bpy.context.view_layer.objects.active = rig
rig.select_set(True)

bpy.ops.object.mode_set(mode="EDIT")
existing = rig.data.edit_bones.get("grip_r")
if existing:
    rig.data.edit_bones.remove(existing)
bone = rig.data.edit_bones.new("grip_r")
bone.head = (-0.513, -0.109, 0.877)
bone.tail = (-0.513, -0.109, 0.797)
bone.parent = rig.data.edit_bones["hand_r"]
bone.use_deform = True
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("GRIP_BONE_ADDED")
