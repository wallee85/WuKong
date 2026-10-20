"""Shorten the blue skirt so the knees show during the run.

Selection (verified by tools/blender/highlight_skirt.py):
  z in [z0, z1], radius in [rmin, rmax], y <= ymax  -> exactly the skirt shell,
  leaving the baggy pants and the tail untouched.

The hem is lifted by `amount` with a monotonic taper, so the skirt compresses
instead of folding. Writes the blend only when --save is passed.

  blender -b --python tools/blender/shorten_skirt.py -- amount z_top z_min [--save]
"""
import math
import os
import shutil
import sys

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
BACKUP = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged_before_skirt.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

argv = sys.argv[sys.argv.index("--") + 1:]
amount = float(argv[0])          # how much the hem rises (m)
z_top = float(argv[1])           # taper ends here (no change above)
z_min = float(argv[2])           # lowest hem vertex
save = "--save" in argv

Z0, Z1, RMIN, RMAX, YMAX = 0.48, 0.82, 0.14, 0.40, 0.10

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene

for lod in ("Wukong_LOD0", "Wukong_LOD1", "Wukong_LOD2"):
    ob = bpy.data.objects.get(lod)
    if ob is None:
        continue
    me = ob.data
    sel = [v.index for v in me.vertices
           if Z0 <= v.co.z <= Z1 and RMIN <= math.hypot(v.co.x, v.co.y) <= RMAX
           and v.co.y <= YMAX]
    moved = 0
    hem_before = min((me.vertices[i].co.z for i in sel), default=z_min)
    for i in sel:
        v = me.vertices[i]
        z = v.co.z
        if z >= z_top:
            continue
        w = max(0.0, min(1.0, (z_top - z) / max(z_top - z_min, 1e-6)))
        v.co.z = z + amount * w
        moved += 1
    hem_after = min((me.vertices[i].co.z for i in sel), default=z_min)
    print("SKIRT %s verts=%d moved=%d hem %.3f -> %.3f" % (lod, len(sel), moved, hem_before, hem_after))

ob = bpy.data.objects["Wukong_LOD0"]
me = ob.data

# ---- preview renders (side + game, run frame 3 and idle)
rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions.get("Run")
cam_data = bpy.data.cameras.new("SKCAM")
cam = bpy.data.objects.new("SKCAM", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.type = "PERSP"
cam_data.angle = math.radians(60.0)
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.film_transparent = True
scene.render.resolution_x = 700
scene.render.resolution_y = 780

for view, loc, target in (("side", (-3.0, 0.0, 1.05), (0.0, 0.0, 0.85)),
                          ("game", (0.0, 3.4, 1.55), (0.0, 0.0, 0.95))):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scen = [(0, act), (3, act), (-1, None)]
    for f, a in scen:
        if a:
            if not rig.animation_data:
                rig.animation_data_create()
            rig.animation_data.action = a
            for s in a.slots:
                rig.animation_data.action_slot = s
                break
            scene.frame_set(max(f, 0))
        else:
            rig.animation_data.action = None
            scene.frame_set(0)
        bpy.context.view_layer.update()
        tag = "run%d" % f if f >= 0 else "idle"
        scene.render.filepath = "%s\\skirt_%s_%s.png" % (OUT, view, tag)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath)

if save:
    if not os.path.exists(BACKUP):
        shutil.copy(BLEND, BACKUP)
        print("BACKUP", BACKUP)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("SAVED")
print("SKIRT_DONE")
