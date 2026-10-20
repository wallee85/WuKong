"""Export LOD0 to the Godot project and render verification views."""

import math
import os

import bpy
from mathutils import Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"
GODOT_GLB = r"D:\Workspace\games\WuKong\assets\characters\wukong\wukong.glb"
SOURCE_GLB = r"D:\Workspace\games\WuKong\source\glb\wukong_LOD0.glb"

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
body = bpy.data.objects["Wukong_LOD0"]

cam_data = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.2
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.film_transparent = True
scene.frame_set(1)

for name, loc, rot in (
    ("v4_front", (0, -6, 0.95), (90, 0, 0)),
    ("v4_back", (0, 6, 0.95), (90, 0, 180)),
    ("v4_left", (-6, 0, 0.95), (90, 0, -90)),
):
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.data.objects.remove(cam, do_unlink=True)

for lod_name in ("Wukong_LOD1", "Wukong_LOD2"):
    obj = bpy.data.objects[lod_name]
    obj.hide_set(True)
    obj.hide_render = True

bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

bpy.ops.export_scene.gltf(
    filepath=GODOT_GLB,
    export_format="GLB",
    use_selection=True,
    export_animations=True,
    export_skins=True,
    export_apply=False,
)
bpy.ops.export_scene.gltf(
    filepath=SOURCE_GLB,
    export_format="GLB",
    use_selection=True,
    export_animations=True,
    export_skins=True,
    export_apply=False,
)
print("EXPORTED", os.path.getsize(GODOT_GLB), os.path.getsize(SOURCE_GLB))


def check_glb(path):
    """Post-export guard: the GLB must be self-consistent with the rig.

    A skin bind naming a bone that the Skeleton3D does not have makes Godot log
    "Skin bind #N contains named bind 'x' but Skeleton3D has no bone by that name".
    This happens if a helper bone (e.g. foot_level_l/r) is deleted from the armature
    but its name survives somewhere in the export, so assert it here instead of
    discovering it in the editor.
    """
    import json
    import struct

    data = open(path, "rb").read()
    if data[:4] != b"glTF":
        raise RuntimeError("not a GLB: %s" % path)
    jlen = struct.unpack("<I", data[12:16])[0]
    doc = json.loads(data[20:20 + jlen].decode("utf-8"))
    blob = json.dumps(doc)
    bones = {b.name for b in rig.data.bones}
    extra = [n for n in ("foot_level_l", "foot_level_r") if n in blob]
    joints = [len(s["joints"]) for s in doc.get("skins", [])]
    anims = [(a.get("name"), len(a["channels"])) for a in doc.get("animations", [])]
    print("GLB_CHECK %s nodes=%d joints=%s anims=%s"
          % (os.path.basename(path), len(doc["nodes"]), joints, anims))
    if extra:
        raise RuntimeError("stale helper bones in export: %s (delete their vertex groups "
                           "and re-export)" % extra)
    if joints and joints[0] != len(bones):
        print("GLB_CHECK_WARN joints %s vs armature bones %d" % (joints, len(bones)))
    for a in doc.get("animations", []):
        mx = 0.0
        for s in a["samplers"]:
            acc = doc["accessors"][s["input"]]
            if "max" in acc:
                mx = max(mx, acc["max"][0])
        print("GLB_CHECK anim %s duration=%.4f s" % (a.get("name"), mx))
    return doc


check_glb(GODOT_GLB)
check_glb(SOURCE_GLB)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("DONE")
