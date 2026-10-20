"""Remove build helpers (RUN_CAM* / RUN_FLOOR*) that the run builder used to leave
in the source blend. Every build created a fresh camera + floor slab and saved the
file, so 60 builds left 60 cameras and 5 floors in source/blend/wukong_rigged.blend.

  blender -b --python tools/blender/clean_helpers.py
"""
import bpy

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)

junk = [o for o in bpy.data.objects
        if o.name.startswith("RUN_CAM") or o.name.startswith("RUN_FLOOR")]
for o in junk:
    bpy.data.objects.remove(o, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras):
    for b in list(block):
        if b.users == 0 and (b.name.startswith("RUN_") or b.name.startswith("RUN_CAM")):
            block.remove(b)

print("REMOVED %d helper objects" % len(junk))
print("OBJECTS: %s" % sorted(o.name for o in bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("CLEAN_DONE")
