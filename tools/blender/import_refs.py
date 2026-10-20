"""Place the three-view reference images in the Wukong project.

Crops in refs/ are tight to each figure, so every view is scaled to the same
1.90 m height. Blender draws image empties with their *longest* side equal to
`empty_display_size`, which for these portrait crops is the height.
"""

import math

import bpy

BLEND = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\wukong_base.blend"
REFS = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\refs"

HEIGHT = 1.9
CENTER_Z = HEIGHT / 2

bpy.ops.wm.open_mainfile(filepath=BLEND)

collection = bpy.data.collections["00_REF"]


def add_reference(name: str, filename: str, location, rotation_deg,
                  hidden: bool = False) -> bpy.types.Object:
    image = bpy.data.images.load(f"{REFS}\\{filename}", check_existing=True)
    bpy.ops.object.empty_add(type="IMAGE", location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data = image
    obj.empty_display_size = HEIGHT
    obj.rotation_euler = tuple(math.radians(angle) for angle in rotation_deg)
    obj.empty_image_depth = "DEFAULT"
    obj.empty_image_side = "FRONT"
    obj.show_in_front = False
    obj.hide_select = True
    for other in list(obj.users_collection):
        other.objects.unlink(obj)
    collection.objects.link(obj)
    if hidden:
        obj.hide_set(True)
    return obj


add_reference("REF_front", "ref_front.png", (0.0, -2.5, CENTER_Z), (90, 0, 0))
add_reference("REF_side", "ref_side.png", (2.5, 0.0, CENTER_Z), (90, 0, 90))
add_reference("REF_back", "ref_back.png", (0.0, 2.5, CENTER_Z), (90, 0, 180))
add_reference(
    "REF_tpose", "ref_tpose_front.png", (0.0, -2.5, CENTER_Z), (90, 0, 0), hidden=True
)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)

print("REFS", [o.name for o in collection.objects])
print(
    "SIZES",
    [(o.name, round(o.empty_display_size, 3), o.empty_image_depth, o.empty_image_side)
     for o in collection.objects],
)
