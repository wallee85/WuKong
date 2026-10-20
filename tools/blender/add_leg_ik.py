"""Add leg IK controls, prove the foot can be posed, render a check."""

import shutil

import bpy
from mathutils import Matrix, Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
BACKUP = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged_backup.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

shutil.copyfile(BLEND, BACKUP)
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
bpy.context.view_layer.objects.active = rig

bpy.ops.object.mode_set(mode="EDIT")
eb = rig.data.edit_bones
for name in ("foot_ik_l", "foot_ik_r", "knee_pole_l", "knee_pole_r"):
    if eb.get(name):
        eb.remove(eb[name])
foot_l = eb.new("foot_ik_l")
foot_l.head = (0.12, 0.0, 0.10)
foot_l.tail = (0.12, -0.18, 0.05)
foot_l.use_deform = False
foot_r = eb.new("foot_ik_r")
foot_r.head = (-0.12, 0.0, 0.10)
foot_r.tail = (-0.12, -0.18, 0.05)
foot_r.use_deform = False
pole_l = eb.new("knee_pole_l")
pole_l.head = (0.12, -0.55, 0.55)
pole_l.tail = (0.12, -0.65, 0.55)
pole_l.use_deform = False
pole_r = eb.new("knee_pole_r")
pole_r.head = (-0.12, -0.55, 0.55)
pole_r.tail = (-0.12, -0.65, 0.55)
pole_r.use_deform = False
bpy.ops.object.mode_set(mode="OBJECT")

for side in ("l", "r"):
    shin = rig.pose.bones["shin_%s" % side]
    constraint = shin.constraints.new("IK")
    constraint.target = rig
    constraint.subtarget = "foot_ik_%s" % side
    constraint.chain_count = 2
    constraint.pole_target = rig
    constraint.pole_subtarget = "knee_pole_%s" % side
    constraint.pole_angle = 0.0

scene.frame_set(1)
pb = rig.pose.bones["foot_ik_l"]
pb.matrix = Matrix.Translation(Vector((0.0, -0.30, 0.18))) @ pb.matrix
bpy.context.view_layer.update()

cam_data = bpy.data.cameras.new("IK_CAM")
cam = bpy.data.objects.new("IK_CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.2
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 800
scene.render.resolution_y = 1000
scene.render.film_transparent = True

for name, loc, rot in (
    ("ik_side", (6, 0, 0.95), (90, 0, 90)),
    ("ik_front", (0, -6, 0.95), (90, 0, 0)),
):
    cam.location = loc
    cam.rotation_euler = tuple(__import__("math").radians(a) for a in rot)
    scene.render.filepath = OUT + "\\" + name + ".png"
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("IK_DONE")
