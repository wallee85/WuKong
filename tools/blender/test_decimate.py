"""Test welding + decimation on the Hunyuan mesh."""

import math
import os

import bmesh
import bpy
from mathutils import Vector

GLB = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\incoming\wukong_hunyuan_v1.glb"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"


def island_count(mesh):
    parent = list(range(len(mesh.vertices)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for edge in mesh.edges:
        ra, rb = find(edge.vertices[0]), find(edge.vertices[1])
        if ra != rb:
            parent[rb] = ra
    return len({find(i) for i in range(len(mesh.vertices))})


bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
scene = bpy.context.scene
obj = next(o for o in scene.objects if o.type == "MESH")

# bake the import rotation so local == world
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

print("BEFORE verts", len(obj.data.vertices), "tris",
      sum(len(p.vertices) - 2 for p in obj.data.polygons), "islands", island_count(obj.data))

bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0003)
bm.to_mesh(obj.data)
bm.free()
obj.data.update()
print("AFTER_WELD verts", len(obj.data.vertices), "islands", island_count(obj.data))

# scale to 1.895 m, feet on z=0, centred on x/y
corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
s = 1.895 / (mx.z - mn.z)
obj.scale = (s, s, s)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
mx = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
obj.location.x -= (mn.x + mx.x) / 2
obj.location.y -= (mn.y + mx.y) / 2
obj.location.z -= mn.z
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
print("SCALED", [round(v, 3) for v in obj.dimensions])

# decimated copy
dec = obj.copy()
dec.data = obj.data.copy()
scene.collection.objects.link(dec)
dec.name = "HY_test_30k"
tris = sum(len(p.vertices) - 2 for p in dec.data.polygons)
mod = dec.modifiers.new("Dec", "DECIMATE")
mod.ratio = 30000 / tris
bpy.context.view_layer.objects.active = dec
bpy.ops.object.modifier_apply(modifier="Dec")
print("DECIM", len(dec.data.polygons), "faces")

# hide the source, keep the decimated for the render
obj.hide_set(True)

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.2
cam.location = (0, -6, 0.95)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = False
scene.render.filepath = os.path.join(OUT, "hy_decim_front.png")
bpy.ops.render.render(write_still=True)
print("DONE")
