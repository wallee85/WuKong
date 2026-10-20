"""Highlight the candidate "blue skirt" faces so the selection can be eyeballed.

  blender -b --python tools/blender/highlight_skirt.py -- <z0> <z1> <rmin> <rmax> <ymax>
Writes docs/renders/skirt_pick_side.png / skirt_pick_game.png (nothing is saved).
"""
import math
import sys

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

argv = sys.argv[sys.argv.index("--") + 1:]
z0, z1, rmin, rmax, ymax = (float(a) for a in argv[:5])

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
ob = bpy.data.objects["Wukong_LOD0"]
me = ob.data

mat = bpy.data.materials.new("SKIRT_TEST")
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = (1.0, 0.05, 0.05, 1.0)
em.inputs[1].default_value = 1.0
nt.links.new(em.outputs[0], out.inputs[0])
mat.diffuse_color = (1.0, 0.05, 0.05, 1.0)
me.materials.append(mat)
idx = len(me.materials) - 1

count = 0
for poly in me.polygons:
    pts = [me.vertices[v].co for v in poly.vertices]
    ok = 0
    for p in pts:
        r = math.hypot(p.x, p.y)
        if z0 <= p.z <= z1 and rmin <= r <= rmax and p.y <= ymax:
            ok += 1
    if ok >= len(pts) * 0.6:
        poly.material_index = idx
        count += 1
print("HIGHLIGHT faces", count, "of", len(me.polygons))

cam_data = bpy.data.cameras.new("SKCAM")
cam = bpy.data.objects.new("SKCAM", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_object_outline = False
scene.render.film_transparent = True
scene.render.resolution_x = 700
scene.render.resolution_y = 780

rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions.get("Run")
if act:
    if not rig.animation_data:
        rig.animation_data_create()
    rig.animation_data.action = act
    for s in act.slots:
        rig.animation_data.action_slot = s
        break

for view, loc, target in (("side", (-2.4, 0.0, 1.00), (0.0, 0.0, 0.80)),
                          ("game", (0.0, 2.6, 1.40), (0.0, 0.0, 0.95))):
    cam_data.type = "PERSP"
    cam_data.angle = math.radians(55.0)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    for f in (0, 3):
        scene.frame_set(f)
        scene.render.filepath = "%s\\skirt_pick_%s_%d.png" % (OUT, view, f)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath)
print("SKIRT_HIGHLIGHT_DONE")
