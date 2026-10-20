"""Create an empty, game-oriented Wukong project scaffold.

Run headless:
    blender -b --python scripts/create_project.py
"""

import math
import os

import bpy

OUT_DIR = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong"
OUT_BLEND = os.path.join(OUT_DIR, "wukong_base.blend")

bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene
scene.name = "Wukong"

# Units: 1 Blender unit = 1 m, character assumed 1.90 m tall.
units = scene.unit_settings
units.system = "METRIC"
units.scale_length = 1.0
units.length_unit = "METERS"

COLLECTIONS = [
    "00_REF",
    "10_BODY",
    "20_CLOTH",
    "30_HAIR",
    "40_PROPS",
    "50_RIG",
    "60_LIGHTS",
    "70_CAMERAS",
]
for name in COLLECTIONS:
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)

# Reference images never render.
bpy.data.collections["00_REF"].hide_render = True


def add_ortho_camera(name: str, location, rotation_deg) -> bpy.types.Object:
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.2  # frames a 1.9 m character with margin
    cam = bpy.data.objects.new(name, cam_data)
    cam.location = location
    cam.rotation_euler = tuple(math.radians(angle) for angle in rotation_deg)
    bpy.data.collections["70_CAMERAS"].objects.link(cam)
    return cam


front = add_ortho_camera("CAM_ortho_front", (0.0, -6.0, 0.95), (90.0, 0.0, 0.0))
add_ortho_camera("CAM_ortho_side", (6.0, 0.0, 0.95), (90.0, 0.0, 90.0))
add_ortho_camera("CAM_ortho_back", (0.0, 6.0, 0.95), (90.0, 0.0, 180.0))
scene.camera = front

render = scene.render
render.resolution_x = 2048
render.resolution_y = 2048
render.resolution_percentage = 100
render.fps = 30
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        render.engine = engine
        break
    except TypeError:
        continue

try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass

world = bpy.data.worlds.new("WLD_neutral")
world.use_nodes = True
background = next(
    node for node in world.node_tree.nodes if node.bl_idname == "ShaderNodeBackground"
)
background.inputs[0].default_value = (0.05, 0.05, 0.05, 1.0)
background.inputs[1].default_value = 1.0
scene.world = world

os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

print("SAVED", OUT_BLEND)
print("COLLECTIONS", [c.name for c in scene.collection.children])
print(
    "CAMERAS",
    [(o.name, o.data.ortho_scale) for o in bpy.data.objects if o.type == "CAMERA"],
)
print("ENGINE", render.engine)
