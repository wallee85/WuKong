"""End-to-end check: export the thinned file the same way export_lod0.py does,
then read back the GLB's animations."""
import json
import os
import struct

import bpy

GLB = os.path.join(os.path.dirname(bpy.data.filepath), "check_export.glb")
rig = bpy.data.objects["Wukong_Rig"]
body = bpy.data.objects["Wukong_LOD0"]
for lod in ("Wukong_LOD1", "Wukong_LOD2"):
    o = bpy.data.objects[lod]
    o.hide_set(True)
    o.hide_render = True
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_animations=True, export_skins=True,
                          export_apply=False)
data = open(GLB, "rb").read()
jlen = struct.unpack("<I", data[12:16])[0]
doc = json.loads(data[20:20 + jlen].decode("utf-8"))
anims = []
for a in doc.get("animations", []):
    mx = 0.0
    for s in a["samplers"]:
        acc = doc["accessors"][s["input"]]
        if "max" in acc:
            mx = max(mx, acc["max"][0])
    anims.append(dict(name=a.get("name"), channels=len(a["channels"]),
                      duration=round(mx, 4)))
print("@@JSON@@" + json.dumps(dict(
    size_mb=round(len(data) / 1e6, 1),
    nodes=len(doc["nodes"]),
    joints=[len(s["joints"]) for s in doc.get("skins", [])],
    animations=anims,
)))
