extends SceneTree


func _init() -> void:
	var staff := Node3D.new()
	staff.name = "Staff"

	var shaft_mesh := CylinderMesh.new()
	shaft_mesh.height = 1.4
	shaft_mesh.top_radius = 0.02
	shaft_mesh.bottom_radius = 0.02
	shaft_mesh.radial_segments = 12

	var shaft_material := StandardMaterial3D.new()
	shaft_material.albedo_color = Color(0.32, 0.07, 0.05)
	shaft_material.metallic = 0.15
	shaft_material.roughness = 0.55

	var shaft := MeshInstance3D.new()
	shaft.name = "Shaft"
	shaft.mesh = shaft_mesh
	shaft.material_override = shaft_material
	staff.add_child(shaft)
	shaft.owner = staff

	var gold_material := StandardMaterial3D.new()
	gold_material.albedo_color = Color(0.86, 0.68, 0.28)
	gold_material.metallic = 0.95
	gold_material.roughness = 0.22

	for index in range(2):
		var band_mesh := CylinderMesh.new()
		band_mesh.height = 0.16
		band_mesh.top_radius = 0.028
		band_mesh.bottom_radius = 0.028
		band_mesh.radial_segments = 12

		var band := MeshInstance3D.new()
		band.name = "Band%d" % index
		band.mesh = band_mesh
		band.material_override = gold_material
		band.position = Vector3(0.0, 0.58 if index == 0 else -0.58, 0.0)
		staff.add_child(band)
		band.owner = staff

	var scene := PackedScene.new()
	scene.pack(staff)
	var err := ResourceSaver.save(scene, "res://assets/props/staff/staff.tscn")
	print("STAFF_SAVE_ERR=", err)
	quit()

