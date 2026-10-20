"""Dump rig / run-action facts for writing the user-facing how-to (read-only)."""
import json
import bpy

sc = bpy.context.scene
rig = bpy.data.objects.get("Wukong_Rig")
out = {}
out["blender"] = bpy.app.version_string
out["fps"] = [sc.render.fps, sc.render.fps_base]
out["frame_range"] = [sc.frame_start, sc.frame_end, sc.frame_current]
out["objects"] = []
for o in bpy.data.objects:
    out["objects"].append(dict(
        n=o.name, t=o.type,
        parent=(o.parent.name if o.parent else None),
        mods=[m.type for m in o.modifiers],
        hide_viewport=o.hide_viewport,
        hide_render=o.hide_render,
    ))
out["actions"] = []
for a in bpy.data.actions:
    out["actions"].append(dict(
        n=a.name, users=a.users, fake=a.use_fake_user,
        range=[round(v, 2) for v in a.frame_range],
        slots=[(s.name_display or s.name) for s in a.slots],
    ))
out["rig_anim"] = None
if rig is not None and rig.animation_data:
    ad = rig.animation_data
    out["rig_anim"] = dict(
        action=(ad.action.name if ad.action else None),
        slot=(ad.action_slot.name_display if ad.action_slot else None),
        nla=[dict(name=t.name, mute=t.mute,
                  strips=[(s.name, s.action.name if s.action else None,
                           round(s.frame_start, 1), round(s.frame_end, 1))
                          for s in t.strips])
             for t in ad.nla_tracks],
    )
out["bones"] = []
out["bone_collections"] = []
if rig is not None:
    out["bone_collections"] = [c.name for c in rig.data.collections]
    for b in rig.data.bones:
        pb = rig.pose.bones[b.name]
        out["bones"].append(dict(
            n=b.name,
            parent=(b.parent.name if b.parent else None),
            con=[(c.type, c.name, getattr(c, "mute", None)) for c in pb.constraints],
            conn=b.use_connect, deform=b.use_deform,
            rot_mode=pb.rotation_mode,
            coll=[c.name for c in b.collections],
            len=round(b.length, 4),
        ))
out["meshes"] = [o.name for o in bpy.data.objects if o.type == "MESH"]
out["libraries"] = [l.filepath for l in bpy.data.libraries]
print("@@JSON@@" + json.dumps(out))
