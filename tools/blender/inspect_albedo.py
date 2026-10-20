"""Inspect the Hunyuan base-colour texture and render a flat albedo pass."""

import math
import os

import bpy
import numpy as np
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

scene = bpy.context.scene
obj = next(o for o in scene.objects if o.type == "MESH")

# save base colour texture
image = bpy.data.images.get("texture_pbr_20250901")
if image is None:
    image = next(i for i in bpy.data.images if tuple(i.size) == (4096, 4096))
image.filepath_raw = os.path.join(OUT, "hy_basecolor.png")
image.file_format = "PNG"
image.save()
arr = np.array(image.pixels[:]).reshape(image.size[1], image.size[0], 4)[..., :3]
print("ALBEDO_MEAN", [round(float(v), 3) for v in arr.reshape(-1, 3).mean(axis=0)])
print("ALBEDO_MAX", [round(float(v), 3) for v in arr.reshape(-1, 3).max(axis=0)])
print("ALBEDO_MIN", [round(float(v), 3) for v in arr.reshape(-1, 3).min(axis=0)])

# material values
mat = obj.data.materials[0]
print("MAT", mat.name)
for node in mat.node_tree.nodes:
    if node.bl_idname == "ShaderNodeBsdfPrincipled":
        for key in ("Metallic", "Roughness", "Base Color"):
            sock = node.inputs.get(key)
            if sock is not None and not sock.is_linked:
                print("PRINCIPLED", key, sock.default_value)

# flat albedo render (workbench, texture colour)
corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
min_v = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
max_v = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
center = (min_v + max_v) / 2
height = max_v.z - min_v.z

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = height * 1.15
cam.location = (center.x, min_v.y - 4 * height, center.z)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "FLAT"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1260
scene.render.film_transparent = True
scene.render.filepath = os.path.join(OUT, "hy_albedo_front.png")
bpy.ops.render.render(write_still=True)

print("DONE")
