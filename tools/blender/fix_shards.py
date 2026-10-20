"""Remove tiny loose shards and re-test the skinning with a symmetric pose."""

import math
import os

import bpy
import bmesh

BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_game.blend"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\renders"

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
body = next(o for o in scene.objects if o.type == "MESH" and o.name.startswith("Wukong_LOD0"))

bm = bmesh.new()
bm.from_mesh(body.data)

# group vertices into islands
parent = list(range(len(bm.verts)))
bm.verts.ensure_lookup_table()


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for edge in bm.edges:
    ra, rb = find(edge.verts[0].index), find(edge.verts[1].index)
    if ra != rb:
        parent[rb] = ra

from collections import defaultdict

islands = defaultdict(list)
for vert in bm.verts:
    islands[find(vert.index)].append(vert)

small = [verts for verts in islands.values() if len(verts) < 300]
print("ISLANDS", len(islands), "SMALL", len(small), "SMALL_VERTS", sum(len(v) for v in small))
to_remove = [vert for verts in small for vert in verts]
if to_remove:
    bmesh.ops.delete(bm, geom=to_remove, context="VERTS")
bm.to_mesh(body.data)
bm.free()

rig = bpy.data.objects["Wukong_Rig"]
for bone_name, angle in (("upperarm_l", -55), ("upperarm_r", 55)):
    pb = rig.pose.bones.get(bone_name)
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (0, 0, math.radians(angle))

cam = bpy.data.objects.get("CAM")
if cam is None:
    cam_data = bpy.data.cameras.new("CAM")
    cam = bpy.data.objects.new("CAM", cam_data)
    scene.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.2
cam.location = (0, -6, 0.95)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True
scene.render.filepath = os.path.join(OUT, "rig_pose_test2.png")
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("DONE")
