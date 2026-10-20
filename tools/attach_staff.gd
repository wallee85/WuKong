extends SceneTree


func _init() -> void:
	var packed: PackedScene = load("res://scenes/main.tscn")
	var root := packed.instantiate()
	var skeleton := root.find_child("Skeleton3D", true, false) as Skeleton3D
	if skeleton == null:
		print("NO_SKELETON")
		quit(1)
		return

	var old := skeleton.get_node_or_null("WeaponR")
	if old != null:
		old.free()

	var attachment := BoneAttachment3D.new()
	attachment.name = "WeaponR"
	attachment.bone_name = "weapon_r"
	skeleton.add_child(attachment)
	attachment.owner = root

	var staff: PackedScene = load("res://assets/props/staff/staff.tscn")
	var staff_instance := staff.instantiate()
	staff_instance.name = "Staff"
	attachment.add_child(staff_instance)
	staff_instance.owner = root

	var scene := PackedScene.new()
	scene.pack(root)
	var err := ResourceSaver.save(scene, "res://scenes/main.tscn")
	print("SCENE_SAVE_ERR=", err)
	quit()
