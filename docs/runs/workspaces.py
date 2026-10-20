"""Which workspaces / screens does the file have (for the how-to doc)?"""
import bpy

print("@@JSON@@" + str({
    "workspaces": [w.name for w in bpy.data.workspaces],
    "screens": [s.name for s in bpy.data.screens],
    "prefs_undo_steps": bpy.context.preferences.edit.undo_steps,
    "save_version": bpy.context.preferences.filepaths.save_version,
    "keyframe_new_interp": bpy.context.preferences.edit.keyframe_new_interpolation_type,
}))
