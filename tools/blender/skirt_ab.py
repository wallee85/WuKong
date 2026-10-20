"""A/B render of the skirt shortening: before vs after, hips close-up.

  blender -b --python tools/blender/skirt_ab.py -- <amount> <z_top> <z_min>
"""
import math
import sys

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

argv = sys.argv[sys.argv.index("--") + 1:]
amount, z_top, z_min = (float(a) for a in argv[:3])
Z0, Z1, RMIN, RMAX, YMAX = 0.48, 0.82, 0.14, 0.40, 0.10

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
ob = bpy.data.objects["Wukong_LOD0"]
me = ob.data
rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]

cam_data = bpy.data.cameras.new("ABCAM")
cam = bpy.data.objects.new("ABCAM", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.type = "ORTHO"
cam_data.ortho_scale = 1.45
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.film_transparent = True
scene.render.resolution_x = 620
scene.render.resolution_y = 620

orig = [v.co.copy() for v in me.vertices]


def set_rest():
    if rig.animation_data:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    scene.frame_set(0)
    bpy.context.view_layer.update()


def set_run(f):
    if not rig.animation_data:
        rig.animation_data_create()
    rig.animation_data.action = act
    for s in act.slots:
        rig.animation_data.action_slot = s
        break
    scene.frame_set(f)
    bpy.context.view_layer.update()


def shoot(tag):
    for view, loc, target in (("side", (-3.0, 0.0, 0.80), (0.0, 0.0, 0.80)),
                              ("back", (0.0, 3.0, 1.30), (0.0, 0.0, 0.95))):
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = "%s\\skab_%s_%s.png" % (OUT, view, tag)
        bpy.ops.render.render(write_still=True)


set_run(3)
shoot("before_run")
set_rest()
shoot("before_idle")

for v in me.vertices:
    v.co = orig[v.index]
moved = 0
for v in me.vertices:
    p = v.co
    r = math.hypot(p.x, p.y)
    if not (Z0 <= p.z <= Z1 and RMIN <= r <= RMAX and p.y <= YMAX):
        continue
    if p.z >= z_top:
        continue
    w = max(0.0, min(1.0, (z_top - p.z) / max(z_top - z_min, 1e-6)))
    p.z += amount * w
    moved += 1
print("MOVED", moved)

set_run(3)
shoot("after_run")
set_rest()
shoot("after_idle")
print("SKIRT_AB_DONE")
