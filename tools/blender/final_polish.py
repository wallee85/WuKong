"""Final beauty render and clean GLB export (LOD0 only)."""

import math
import os

import bpy
from mathutils import Vector

BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_rigged.blend"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"
EXPORT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\export\wukong_LOD0.glb"

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene

world = bpy.data.worlds.new("W")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
bg.inputs[0].default_value = (0.03, 0.03, 0.04, 1.0)
scene.world = world

rig = bpy.data.objects["Wukong_Rig"]
body = bpy.data.objects["Wukong_LOD0"]


def add_light(name, loc, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    obj.rotation_euler = (Vector((0, 0, 1.1)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(obj)


add_light("key", (2.4, -3.0, 3.0), 600, 2.5)
add_light("rim", (-2.2, 2.6, 2.4), 500, 2.0)
add_light("fill", (-3.0, -2.0, 1.4), 150, 3.0)

scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 64
scene.view_settings.view_transform = "AgX"
scene.render.film_transparent = False
scene.render.resolution_x = 1100
scene.render.resolution_y = 1400

cam = bpy.data.objects["CAM"]
cam.data.type = "PERSP"
cam.data.lens = 75
cam.location = (2.3, -3.4, 2.0)
cam.rotation_euler = (Vector((0.0, 0.0, 1.05)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.frame_set(31)
scene.render.filepath = os.path.join(OUT, "final_beauty.png")
bpy.ops.render.render(write_still=True)

# export only LOD0 + rig
for lod_name in ("Wukong_LOD1", "Wukong_LOD2"):
    obj = bpy.data.objects[lod_name]
    obj.hide_set(True)
    obj.hide_render = True

bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

bpy.ops.export_scene.gltf(
    filepath=EXPORT,
    export_format="GLB",
    use_selection=True,
    export_animations=True,
    export_skins=True,
    export_apply=False,
)
print("EXPORTED", EXPORT, os.path.getsize(EXPORT))
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("DONE")
