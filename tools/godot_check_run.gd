extends SceneTree

# Headless verification of the imported wukong GLB: animation names, lengths, loops,
# and the skeleton joints used by scripts/main.gd.
func _init() -> void:
	var packed: PackedScene = load("res://assets/characters/wukong/wukong.glb")
	if packed == null:
		print("CHECK_FAIL could not load glb")
		quit(1)
		return
	var root: Node = packed.instantiate()
	var players := root.find_children("*", "AnimationPlayer", true, false)
	if players.is_empty():
		print("CHECK_FAIL no AnimationPlayer")
		quit(1)
		return
	var ap: AnimationPlayer = players[0]
	for name in ap.get_animation_list():
		var anim := ap.get_animation(name)
		print("ANIM %s length=%.4f loop=%d tracks=%d" % [name, anim.length, anim.loop_mode, anim.get_track_count()])
	var skels := root.find_children("*", "Skeleton3D", true, false)
	if not skels.is_empty():
		var sk: Skeleton3D = skels[0]
		print("SKELETON bones=%d" % sk.get_bone_count())
		for bone in ["pelvis", "thigh_l", "shin_l", "foot_l", "toe_l", "spine_01",
				"upperarm_l", "lowerarm_l", "upperarm_r", "lowerarm_r", "grip_r"]:
			print("  bone %-10s idx=%d" % [bone, sk.find_bone(bone)])
	root.queue_free()
	print("CHECK_OK")
	quit(0)
