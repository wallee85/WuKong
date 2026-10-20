extends SceneTree

func _init() -> void:
	var root := Node3D.new()
	root.name = "Main"
	root.set_script(load("res://scripts/main.gd"))

	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.045, 0.05, 0.065)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.5, 0.55, 0.65)
	env.ambient_light_energy = 0.45
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.fog_enabled = true
	env.fog_light_color = Color(0.05, 0.055, 0.07)
	env.fog_density = 0.03

	var world := WorldEnvironment.new()
	world.name = "WorldEnvironment"
	world.environment = env
	root.add_child(world)
	world.owner = root

	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-38.0, -32.0, 0.0)
	sun.light_energy = 1.4
	sun.shadow_enabled = true
	root.add_child(sun)
	sun.owner = root

	var rim := DirectionalLight3D.new()
	rim.name = "Rim"
	rim.rotation_degrees = Vector3(-15.0, 150.0, 0.0)
	rim.light_energy = 0.6
	rim.light_color = Color(0.65, 0.78, 1.0)
	root.add_child(rim)
	rim.owner = root

	var ground := MeshInstance3D.new()
	ground.name = "Ground"
	var plane := PlaneMesh.new()
	plane.size = Vector2(24.0, 24.0)
	ground.mesh = plane
	var ground_material := StandardMaterial3D.new()
	ground_material.albedo_color = Color(0.10, 0.10, 0.11)
	ground_material.roughness = 0.95
	ground.material_override = ground_material
	root.add_child(ground)
	ground.owner = root

	var camera := Camera3D.new()
	camera.name = "Camera3D"
	camera.fov = 42.0
	root.add_child(camera)
	camera.owner = root
	var eye := Vector3(1.65, 1.45, 2.65)
	camera.look_at_from_position(eye, Vector3(0.0, 1.0, 0.0))

	var packed: PackedScene = load("res://assets/characters/wukong/wukong.glb")
	var character := packed.instantiate()
	character.name = "Wukong"
	root.add_child(character)
	character.owner = root

	var ink_layer := CanvasLayer.new()
	ink_layer.name = "InkLayer"
	ink_layer.layer = 10
	root.add_child(ink_layer)
	ink_layer.owner = root

	var ink_rect := ColorRect.new()
	ink_rect.name = "InkPost"
	ink_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	ink_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var shader := load("res://assets/shaders/ink_post.gdshader") as Shader
	var material := ShaderMaterial.new()
	material.shader = shader
	material.set_shader_parameter("paper_tex", load("res://assets/textures/paper.png"))
	ink_rect.material = material
	ink_layer.add_child(ink_rect)
	ink_rect.owner = root

	var scene := PackedScene.new()
	scene.pack(root)
	var err := ResourceSaver.save(scene, "res://scenes/main.tscn")
	print("SCENE_SAVE_ERR=", err)
	quit()
