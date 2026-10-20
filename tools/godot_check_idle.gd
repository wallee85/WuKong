extends SceneTree

# Headless check for the idle regression: after playing Run, stopping it and doing the
# same reset the idle path uses, the pelvis must be back at its rest height and the
# lowest skinned vertex back on the ground.
func _init() -> void:
	var packed: PackedScene = load("res://assets/characters/wukong/wukong.glb")
	var root: Node = packed.instantiate()
	get_root().add_child(root)
	var ap: AnimationPlayer = root.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = root.find_children("*", "Skeleton3D", true, false)[0]
	var mesh: MeshInstance3D = root.find_children("*", "MeshInstance3D", true, false)[0]

	var pelvis := sk.find_bone("pelvis")
	print("rest pelvis height = %.4f" % sk.get_bone_global_pose(pelvis).origin.y)
	print("rest lowest vertex = %.4f" % _lowest(mesh, sk))

	ap.play("Run")
	ap.seek(0.3, true)
	await process_frame
	await process_frame
	print("during Run: pelvis = %.4f  lowest = %.4f"
		% [sk.get_bone_global_pose(pelvis).origin.y, _lowest(mesh, sk)])

	ap.stop()
	# old behaviour: rotation-only reset
	for i in range(sk.get_bone_count()):
		sk.set_bone_pose_rotation(i, sk.get_bone_rest(i).basis.get_rotation_quaternion())
	await process_frame
	await process_frame
	print("after rotation-only reset: pelvis = %.4f  lowest = %.4f"
		% [sk.get_bone_global_pose(pelvis).origin.y, _lowest(mesh, sk)])

	# new behaviour: also reset position/scale
	for i in range(sk.get_bone_count()):
		sk.set_bone_pose_rotation(i, sk.get_bone_rest(i).basis.get_rotation_quaternion())
		sk.set_bone_pose_position(i, sk.get_bone_rest(i).origin)
		sk.set_bone_pose_scale(i, Vector3.ONE)
	await process_frame
	await process_frame
	print("after full reset:           pelvis = %.4f  lowest = %.4f"
		% [sk.get_bone_global_pose(pelvis).origin.y, _lowest(mesh, sk)])
	print("IDLE_CHECK_DONE")
	quit(0)


func _lowest(mesh: MeshInstance3D, sk: Skeleton3D) -> float:
	var arr := mesh.get_mesh().surface_get_arrays(0)
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var low := INF
	for v in verts:
		low = min(low, mesh.global_transform.origin.y + v.y)
	return low
