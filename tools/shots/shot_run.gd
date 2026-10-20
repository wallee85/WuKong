extends Node3D

# Renders the imported run cycle straight out of Godot (the real delivered asset),
# so the export can be verified visually without opening the editor.
#   godot --path <project> tools/shots/shot_run.tscn

const OUT := "res://docs/renders/"

var _ap: AnimationPlayer
var _times: Array[float] = []
var _i := 0
var _wait := 0


func _ready() -> void:
	var packed: PackedScene = load("res://assets/characters/wukong/wukong.glb")
	var model: Node3D = packed.instantiate()
	add_child(model)

	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 2.3
	cam.position = Vector3(6.0, 0.95, 0.0)
	add_child(cam)
	cam.look_at(Vector3(0.0, 0.95, 0.0), Vector3.UP)

	var world_env := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.10, 0.10, 0.12)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.9, 0.9, 0.95)
	env.ambient_light_energy = 1.0
	world_env.environment = env
	add_child(world_env)

	var light := DirectionalLight3D.new()
	light.rotation = Vector3(deg_to_rad(-50.0), deg_to_rad(30.0), 0.0)
	light.light_energy = 1.2
	add_child(light)

	var players := model.find_children("*", "AnimationPlayer", true, false)
	_ap = players[0]
	var anim := _ap.get_animation("Run")
	anim.loop_mode = Animation.LOOP_NONE
	_ap.play("Run")
	print("SHOT anim length=%.4f tracks=%d" % [anim.length, anim.get_track_count()])
	var n := int(round(anim.length * 24.0))
	for k in range(0, n, 2):
		_times.append(anim.length * float(k) / float(n))
	_ap.seek(_times[0], true)


func _process(_delta: float) -> void:
	if _i >= _times.size():
		print("SHOT_DONE")
		get_tree().quit()
		return
	_wait += 1
	if _wait < 3:
		return
	_wait = 0
	_ap.seek(_times[_i], true)
	_ap.pause()
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png("%sgodot_run_%02d.png" % [OUT, _i])
	print("saved godot_run_%02d.png  t=%.4f" % [_i, _times[_i]])
	_i += 1
