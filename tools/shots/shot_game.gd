extends Node3D

# Captures the run the way the player sees it: main.tscn in autorun, chase camera,
# ink post-process on. Used to judge the animation in-engine, not in an ortho side view.
#   godot --path <project> --resolution 900x600 res://tools/shots/shot_game.tscn

const OUT := "res://docs/renders/"
const SHOTS := 8
const INTERVAL := 0.09

var _t := 0.0
var _i := 0


func _ready() -> void:
	OS.set_environment("WUKONG_AUTORUN", "1")
	var packed: PackedScene = load("res://scenes/main.tscn")
	add_child(packed.instantiate())
	print("GAME_SHOT start")


func _process(delta: float) -> void:
	_t += delta
	if _t < 0.6:
		return
	if _i >= SHOTS:
		return
	_t = 0.0
	var image := get_viewport().get_texture().get_image()
	image.save_png("%sgame_run_%02d.png" % [OUT, _i])
	print("saved game_run_%02d.png" % _i)
	_i += 1
	if _i >= SHOTS:
		print("GAME_SHOT done")
		get_tree().quit()
