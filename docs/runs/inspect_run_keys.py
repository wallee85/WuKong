"""Second pass: action key density, interpolation, armature display, view state."""
import json

import bpy
from bpy_extras import anim_utils

rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
out = {}
out["action"] = act.name
out["curve_stats"] = {}
slot = act.slots[0]
cb = anim_utils.action_ensure_channelbag_for_slot(act, slot) if hasattr(
    anim_utils, "action_ensure_channelbag_for_slot") else None
if cb is None:
    cb = act.layers[0].strips[0].channelbags[0]
out["n_fcurves"] = len(cb.fcurves)
counts = {}
interps = set()
bones_touched = set()
for fc in cb.fcurves:
    counts.setdefault(fc.data_path, []).append(len(fc.keyframe_points))
    for k in fc.keyframe_points:
        interps.add(k.interpolation)
    # data_path like pose.bones["thigh_l"].rotation_quaternion
    if fc.data_path.startswith('pose.bones["'):
        bones_touched.add(fc.data_path.split('"')[1])
out["keys_per_channel"] = {k: sorted(set(v)) for k, v in list(counts.items())[:6]}
out["n_distinct_paths"] = len(counts)
out["interpolations"] = sorted(interps)
out["n_bones_keyed"] = len(bones_touched)
out["bones_keyed"] = sorted(bones_touched)
out["rig_show_in_front"] = rig.show_in_front
out["armature_display"] = rig.data.display_type
out["custom_shapes"] = {b.name: (b.custom_shape.name if b.custom_shape else None)
                        for b in rig.pose.bones if b.custom_shape}
out["rest_display"] = rig.data.show_names if hasattr(rig.data, "show_names") else None
out["mask"] = {
    "action_frame_range": list(act.frame_range),
    "use_frame_range": act.use_frame_range if hasattr(act, "use_frame_range") else None,
    "use_cyclic": act.use_cyclic if hasattr(act, "use_cyclic") else None,
}
sc = bpy.context.scene
out["frame_current"] = sc.frame_current
out["camera"] = sc.camera.name if sc.camera else None
out["world"] = sc.world.name if sc.world else None
out["view_layers"] = [vl.name for vl in sc.view_layers]
out["collections"] = [c.name for c in bpy.data.collections]
out["hide_state"] = {}
for o in bpy.data.objects:
    hl = bpy.context.view_layer.layer_collection.children
    out["hide_state"][o.name] = dict(
        hide_get=o.hide_get() if o.name in bpy.context.view_layer.objects else "not_in_vl")
out["rig_scale"] = list(rig.scale)
out["rig_layers_colls"] = getattr(rig.data, "collections_all", None) and [
    c.name for c in rig.data.collections_all]
print("@@JSON@@" + json.dumps(out, default=str))
