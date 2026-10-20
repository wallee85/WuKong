"""Import the Hunyuan3D GLB, report stats and render orthographic views."""

import math
import os

import bpy
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

scene = bpy.context.scene
meshes = [o for o in scene.objects if o.type == "MESH"]
print("MESH_OBJECTS", [(o.name, len(o.data.vertices), len(o.data.polygons)) for o in meshes])

# world bbox
corners = []
for obj in meshes:
    for corner in obj.bound_box:
        corners.append(obj.matrix_world @ Vector(corner))
min_v = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
max_v = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
size = max_v - min_v
center = (min_v + max_v) / 2
print("BBOX_MIN", [round(v, 4) for v in min_v])
print("BBOX_MAX", [round(v, 4) for v in max_v])
print("SIZE", [round(v, 4) for v in size])

tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
print("TRIS", tris)

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    images = []
    for node in mat.node_tree.nodes:
        if node.bl_idname == "ShaderNodeTexImage" and node.image:
            images.append((node.image.name, tuple(node.image.size), node.image.colorspace_settings.name))
    print("MATERIAL", mat.name, "IMAGES", images)

height = size.z
ortho = height * 1.15

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = ortho
scene.camera = cam

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1000
scene.render.resolution_y = 1400
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"

world = bpy.data.worlds.new("W")
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
bg.inputs[0].default_value = (0.05, 0.05, 0.06, 1.0)
scene.world = world


def add_light(name, loc, energy, size_l):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size_l
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    obj.rotation_euler = (center - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(obj)


add_light("key", (center.x + 1.6, center.y - 2.2, max_v.z + 1.2), 900, 2.0)
add_light("rim", (center.x - 1.8, center.y + 2.0, max_v.z + 0.8), 600, 1.8)
add_light("fill", (center.x - 2.2, center.y - 1.8, center.z), 250, 2.5)

views = {
    "front": ((center.x, min_v.y - 4 * height, center.z), (90, 0, 0)),
    "side": ((max_v.x + 4 * height, center.y, center.z), (90, 0, 90)),
    "back": ((center.x, max_v.y + 4 * height, center.z), (90, 0, 270)),
}
for name, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    cam_data.ortho_scale = ortho
    scene.render.filepath = os.path.join(OUT, f"hy_{name}.png")
    bpy.ops.render.render(write_still=True)

# three-quarter beauty
cam_data.type = "PERSP"
cam_data.lens = 70
cam.location = (center.x + 0.55 * height, center.y - 0.85 * height, center.z + 0.2 * height)
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.render.resolution_x = 1000
scene.render.resolution_y = 1400
scene.render.film_transparent = False
scene.render.filepath = os.path.join(OUT, "hy_beauty.png")
bpy.ops.render.render(write_still=True)

print("RENDERS", sorted(os.listdir(OUT)))
