extends Node3D

# Sweeps the staff's carry (local rotation + slide along its own axis) and prints
# world-space tip / butt, so the carry is chosen from numbers instead of eyeballed
# from a 200 px character. main.gd rewrites _set_staff_carry() every frame, so this
# node overrides it with a higher process priority.
#
# The grip socket sits at the staff's CENTRE, and the run leans ~30 deg, so any tilt
# leaves one end projecting. Sliding the staff back along its own axis is what turns
# "lance couched at the face" into "staff trailing behind the hip".
#
#   godot --path . --resolution 720x760 res://tools/shots/shot_staff.tscn

const OUT := "res://docs/renders/"
# (rot_x, rot_z, slide along the staff's own axis in metres)
const CANDIDATES := [
	Vector3(195, -14, 0.30),
	Vector3(200, -14, 0.10),
	Vector3(205, -20, -0.10),
	Vector3(190, -30, 0.30),
	Vector3(210, -14, 0.45),
	Vector3(200, -14, 0.45),
]
const FREEZE := 0.0             # animation time the sweep is measured at
const SETTLE := 12

var _scene: Node3D
var _staff: Node3D
var _player: AnimationPlayer
var _idx := 0
var _wait := 0
var _frozen := false


func _ready() -> void:
	process_priority = 300
	OS.set_environment("WUKONG_AUTORUN", "1")
	_scene = load("res://scenes/main.tscn").instantiate()
	add_child(_scene)
	var players := _scene.find_children("*", "AnimationPlayer", true, false)
	if not players.is_empty():
		_player = players[0]
	print("STAFF start")


func _process(_delta: float) -> void:
	if _idx >= CANDIDATES.size() or _player == null:
		return
	if not _frozen:
		if _player.current_animation != "Run":
			return
		_player.seek(FREEZE, true)
		_player.pause()
		_frozen = true
		return
	if _staff == null:
		for n in _scene.find_children("*", "Node3D", true, false):
			if n.name.begins_with("Staff"):
				_staff = n
				break
		if _staff == null:
			return
	var c: Vector3 = CANDIDATES[_idx]
	var b := Basis.from_euler(Vector3(deg_to_rad(c.x), 0.0, deg_to_rad(c.y)))
	_staff.rotation = b.get_euler()
	_staff.position = b * Vector3(0.0, c.z, 0.0)
	_wait += 1
	if _wait < SETTLE:
		return
	var tip: Vector3 = _staff.global_transform * Vector3(0.0, 0.7, 0.0)
	var butt: Vector3 = _staff.global_transform * Vector3(0.0, -0.7, 0.0)
	var root: Node3D = _scene.get_node("Wukong")
	var rt: Vector3 = _scene.to_local(tip)
	var rb: Vector3 = _scene.to_local(butt)
	var rm: Vector3 = _scene.to_local(root.global_position)
	print("CAND %d  x=%.0f z=%.0f dive=%.2f | tip y=%+.2f fwd=%+.2f | butt y=%+.2f fwd=%+.2f"
		% [_idx, c.x, c.y, c.z, rt.y - rm.y, -(rt.z - rm.z), rb.y - rm.y, -(rb.z - rm.z)])
	var image := get_viewport().get_texture().get_image()
	image.save_png("%sstaff_%02d.png" % [OUT, _idx])
	_idx += 1
	_wait = 0
	if _idx >= CANDIDATES.size():
		print("STAFF done")
		get_tree().quit()
