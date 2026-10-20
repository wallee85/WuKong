extends Node3D

# Prints what the RUNNING GAME is actually playing (not what is on disk): animation
# name, skeleton bone count, and the spine's forward lean measured from bone world
# positions. Used to tell "the animation did not change" apart from "the editor is
# showing a stale import of it".
#
#   godot --path . --resolution 640x480 res://tools/shots/probe_run.tscn

var _scene: Node3D
var _frames := 0
var _leans: Array = []
var _hand_z: Array = []


func _ready() -> void:
	OS.set_environment("WUKONG_AUTORUN", "1")
	_scene = load("res://scenes/main.tscn").instantiate()
	add_child(_scene)


func _process(_delta: float) -> void:
	_frames += 1
	if _frames < 20:
		return
	var sk := _scene.find_child("Skeleton3D", true, false) as Skeleton3D
	var ap := _scene.find_child("AnimationPlayer", true, false) as AnimationPlayer
	if sk == null or ap == null:
		print("PROBE_FAIL skeleton=%s player=%s" % [sk, ap])
		get_tree().quit(1)
		return
	var p := sk.get_bone_global_pose(sk.find_bone("pelvis")).origin
	var c := sk.get_bone_global_pose(sk.find_bone("chest")).origin
	var spine := c - p
	_leans.append(rad_to_deg(atan2(spine.z, spine.y)))      # model forward = +Z
	var hand := sk.get_bone_global_pose(sk.find_bone("hand_l")).origin
	_hand_z.append(hand.z - c.z)
	if _frames >= 140:
		var lo: float = _leans.min()
		var hi: float = _leans.max()
		print("PROBE anim=%s  pos=%.3f  bones=%d" % [ap.current_animation,
			ap.current_animation_position, sk.get_bone_count()])
		print("PROBE lean_fwd min=%.1f max=%.1f  (v16 bakes 14.7..16.9; v15 baked 26.9..31.0)"
			% [lo, hi])
		print("PROBE left hand fwd of chest: min=%.3f max=%.3f" % [_hand_z.min(), _hand_z.max()])
		get_tree().quit()
