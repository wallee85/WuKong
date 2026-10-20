"""Render the baked Run action from arbitrary cameras (no rebuild, no export).

  blender -b --python tools/blender/render_run_views.py -- <view> <frames> <prefix>

view: side | front | back | foot | q34
frames: comma separated, e.g. 0,2,4,7
"""
import math
import sys

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

VIEWS = {
    #        location                look-at            ortho scale
    "side": ((-6.0, 0.0, 0.95), (0.0, 0.0, 0.95), 2.35),
    "front": ((0.0, -6.0, 0.95), (0.0, 0.0, 0.95), 2.35),
    "back": ((0.0, 6.0, 0.95), (0.0, 0.0, 0.95), 2.35),
    "foot": ((-2.6, -3.4, 0.75), (0.05, -0.05, 0.18), 1.30),
    "q34": ((-4.2, -4.2, 1.35), (0.0, 0.0, 0.85), 2.60),
    # what the player actually sees: follow cam 4.2 m behind, 2.3 m up, looking down
    "game": ((0.0, 4.6, 1.70), (0.0, 0.0, 1.15), 0.0),
    # offset follow cam: 3/4 rear like the reference, character wider in frame
    "game2": ((0.95, 4.35, 1.75), (0.0, 0.0, 1.10), 0.0),
}
PERSPECTIVE = {"game": (70.0, 760, 720), "game2": (62.0, 760, 760)}

argv = sys.argv[sys.argv.index("--") + 1:]
view, frames_arg, prefix = argv[0], argv[1], argv[2]
frames = [int(f) for f in frames_arg.split(",")]

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = act
for s in act.slots:
    rig.animation_data.action_slot = s
    break

loc, target, scale = VIEWS[view]
cam_data = bpy.data.cameras.new("CHECK_CAM")
cam = bpy.data.objects.new("CHECK_CAM", cam_data)
scene.collection.objects.link(cam)
if view in PERSPECTIVE:
    fov, rx, ry = PERSPECTIVE[view]
    cam_data.type = "PERSP"
    cam_data.angle = math.radians(fov)
else:
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = scale
scene.camera = cam
cam.location = loc
cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
if view in PERSPECTIVE:
    scene.render.resolution_x, scene.render.resolution_y = PERSPECTIVE[view][1], PERSPECTIVE[view][2]
else:
    scene.render.resolution_x = 700 if view != "foot" else 820
    scene.render.resolution_y = 900 if view != "foot" else 620
scene.render.film_transparent = True

for f in frames:
    scene.frame_set(f)
    scene.render.filepath = "%s\\%s_%s_%02d.png" % (OUT, prefix, view, f)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)
print("VIEW_RENDER_DONE")
