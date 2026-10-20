"""Measure how far the planted boot actually sits from the floor, per frame.

The builder drives the ankle from the ball-of-foot geometry, but the boot is skinned
43% to the shin, so bending the knee drags the sole down through the calf weights.
This prints the residual (mesh minZ) plus the exact vertex that owns it, so the
LIFT_V table in build_run_action.py can be calibrated instead of guessed.

  blender -b --python tools/blender/calibrate_run_lift.py
"""
import bpy

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
rig = bpy.data.objects["Wukong_Rig"]
act = bpy.data.actions["Run"]
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = act
for s in act.slots:
    rig.animation_data.action_slot = s
    break

meshes = [o for o in bpy.data.objects
          if o.type == "MESH" and o.parent == rig and not o.name.startswith("RUN_FLOOR")]
F0, F1 = int(act.frame_range[0]), int(act.frame_range[1])
print("%5s %8s | %8s %8s | %8s %8s %8s | %s"
      % ("frame", "minZ", "ankL", "ankR", "low_x", "low_y", "low_z", "lift_needed"))
for f in range(F0, F1 + 1):
    scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = rig.evaluated_get(dg)
    lo = None
    for o in meshes:
        eo = o.evaluated_get(dg)
        me = eo.to_mesh()
        mw = eo.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            if lo is None or w.z < lo.z:
                lo = w.copy()
        eo.to_mesh_clear()
    ank = {}
    for side in ("l", "r"):
        ank[side] = (rig.matrix_world @ ev.pose.bones["foot_%s" % side].head).z
    print("%5d %8.4f | %8.3f %8.3f | %8.3f %8.3f %8.3f | %+8.4f"
          % (f, lo.z, ank["l"], ank["r"], lo.x, lo.y, lo.z, -lo.z))
print("LOW_VERTEX_DONE")
