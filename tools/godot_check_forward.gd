extends SceneTree
func _init() -> void:
	var packed: PackedScene = load("res://assets/characters/wukong/wukong.glb")
	var root: Node = packed.instantiate()
	get_root().add_child(root)
	var sk: Skeleton3D = root.find_children("*", "Skeleton3D", true, false)[0]
	for n in ["toe_l","foot_l","head","pelvis","tail_01"]:
		var i := sk.find_bone(n)
		if i < 0: continue
		var rest := sk.get_bone_rest(i)
		print("%-8s rest.origin=%s  basis.z=%s" % [n, rest.origin, rest.basis.z])
	print("model rotation = ", root.get("rotation"))
	print("FORWARD_CHECK_DONE")
	quit(0)
