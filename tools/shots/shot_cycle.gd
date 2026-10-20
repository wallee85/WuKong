extends Node3D

# Captures one full run cycle FROM THE GAME (chase camera, real scene, ink shader),
# one image per animation frame, so the baked clip can be judged as motion rather
# than as an ortho still.
#
# The frames are picked by animation position, not by wall-clock timing: every
# rendered frame records the AnimationPlayer position and fills the first empty
# 1/24 s slot. Wall-clock sampling drifts and aliases against 24 fps.
#
#   godot --path . --resolution 720x760 res://tools/shots/shot_cycle.tscn

const OUT := "res://docs/renders/"
const FPS := 24.0
const SLOTS := 16

var _scene: Node3D
var _player: AnimationPlayer
var _got: Dictionary = {}
var _warm := 0
var _anim_len := 0.0


func _ready() -> void:
	process_priority = 200          # run AFTER main.gd has moved the camera
	OS.set_environment("WUKONG_AUTORUN", "1")
	_scene = load("res://scenes/main.tscn").instantiate()
	add_child(_scene)
	var players := _scene.find_children("*", "AnimationPlayer", true, false)
	if players.is_empty():
		print("CYCLE_FAIL no AnimationPlayer")
		get_tree().quit(1)
		return
	_player = players[0]
	print("CYCLE start")


func _process(_delta: float) -> void:
	if _player == null:
		return
	# camera first, every frame: the captured image is the PREVIOUS frame's texture,
	# so a camera moved on the same frame as the capture shows up one frame late (the
	# first two cycle images came out from the default far camera because of this)
	var model: Node3D = _scene.get_node("Wukong")
	var cam: Camera3D = _scene.get_node("Camera3D")
	cam.position = model.position + Vector3(-2.85, 1.15, 0.0)
	cam.look_at(model.position + Vector3(0.0, 0.98, 0.0))
	if _player.current_animation != "Run":
		return
	_warm += 1
	if _warm < 8:
		return                      # the first rendered frames are not composited yet
	var pos: float = _player.current_animation_position
	if _anim_len <= 0.0:
		_anim_len = _player.get_animation(_player.current_animation).length
	# slot from the clip's own length, not a hard-coded 16 frames: the cycle changed
	# from 16 to 18 frames and a fixed window silently aliased the frames
	var slot := int(floor(fmod(pos, _anim_len) / _anim_len * float(SLOTS))) % SLOTS
	if not _got.has(slot):
		_got[slot] = true
		var image := get_viewport().get_texture().get_image()
		image.save_png("%scycle_%02d.png" % [OUT, slot])
		print("saved cycle_%02d  t=%.3f" % [slot, pos])
	if _got.size() >= SLOTS:
		print("CYCLE done")
		get_tree().quit()
