extends Node3D

@onready var ink_layer: CanvasLayer = $InkLayer
@onready var camera: Camera3D = $Camera3D
@onready var model: Node3D = $Wukong

const STAFF_SCENE := preload("res://assets/props/staff/staff.tscn")
# RUN_SPEED / RUN_CYCLE must match the baked run cycle or the feet slide:
#   v = ball sweep / stance time = 0.765 m / 0.225 s = 3.40 m/s
#   RUN_CYCLE = 18 frames @ 24 fps = 0.7500 s -> 160 steps/min, 1.275 m steps
# (v17: 3.40 m/s not 4.20. At 4.20 this 0.82 m leg cannot reach a long stride -- the
#  sweep is capped at ~0.77 m, so the cadence is forced to ~190 spm and reads as a
#  scurry. Slower speed is the only lever that buys a longer, calmer stride.)
const RUN_SPEED := 3.40
const TURN_RATE := 9.0
const RUN_CYCLE := 0.7500
const ATTACK_RADIUS := 2.0
const ATTACK_HALF_ANGLE := deg_to_rad(60.0)

const POSES := [
	{
		"thigh_l": 0.50, "shin_l": 0.10,
		"thigh_r": -0.55, "shin_r": 1.05,
		"upperarm_l": -0.65, "upperarm_r": 0.45,
		"twist": 0.12, "bob": -0.06,
	},
	{
		"thigh_l": 0.05, "shin_l": 0.15,
		"thigh_r": -0.05, "shin_r": 1.65,
		"upperarm_l": -0.15, "upperarm_r": 0.10,
		"twist": 0.0, "bob": 0.03,
	},
	{
		"thigh_l": -0.55, "shin_l": 1.05,
		"thigh_r": 0.50, "shin_r": 0.10,
		"upperarm_l": 0.65, "upperarm_r": -0.45,
		"twist": -0.12, "bob": -0.06,
	},
	{
		"thigh_l": -0.05, "shin_l": 1.65,
		"thigh_r": 0.05, "shin_r": 0.15,
		"upperarm_l": 0.15, "upperarm_r": -0.10,
		"twist": 0.0, "bob": 0.03,
	},
]

const ATTACKS := [
	{
		"duration": 0.50,
		"hit": [0.38, 0.58],
		"poses": [
			{"t": 0.0, "x": {}, "y": {}, "z": {}},
			{"t": 0.22, "x": {"upperarm_r": -0.95, "lowerarm_r": 0.70},
				"y": {"spine_01": 0.70, "chest": 0.55, "head": -0.25}, "z": {}},
			{"t": 0.40, "x": {"upperarm_r": 1.35, "lowerarm_r": 0.05},
				"y": {"spine_01": -0.95, "chest": -0.70, "head": 0.30}, "z": {}},
			{"t": 0.58, "x": {"upperarm_r": 1.45, "lowerarm_r": 0.05},
				"y": {"spine_01": -1.05, "chest": -0.75, "head": 0.30}, "z": {}},
			{"t": 1.0, "x": {}, "y": {}, "z": {}},
		],
	},
	{
		"duration": 0.50,
		"hit": [0.36, 0.56],
		"poses": [
			{"t": 0.0, "x": {}, "y": {}, "z": {}},
			{"t": 0.20, "x": {"upperarm_r": 1.15, "lowerarm_r": 0.55},
				"y": {"spine_01": -0.70, "chest": -0.55, "head": 0.25}, "z": {}},
			{"t": 0.38, "x": {"upperarm_r": -1.30, "lowerarm_r": 0.10},
				"y": {"spine_01": 0.95, "chest": 0.70, "head": -0.30}, "z": {}},
			{"t": 0.56, "x": {"upperarm_r": -1.40, "lowerarm_r": 0.10},
				"y": {"spine_01": 1.05, "chest": 0.75, "head": -0.30}, "z": {}},
			{"t": 1.0, "x": {}, "y": {}, "z": {}},
		],
	},
	{
		"duration": 0.74,
		"hit": [0.46, 0.64],
		"poses": [
			{"t": 0.0, "x": {}, "y": {}, "z": {}},
			{"t": 0.30, "x": {"upperarm_r": -0.45, "upperarm_l": -0.45},
				"y": {}, "z": {"upperarm_r": 1.25, "upperarm_l": 1.25},
				"spine_x": -0.35},
			{"t": 0.50, "x": {"upperarm_r": 1.10, "upperarm_l": 1.10},
				"y": {}, "z": {"upperarm_r": 0.15, "upperarm_l": 0.15},
				"spine_x": 0.50},
			{"t": 0.64, "x": {"upperarm_r": 1.20, "upperarm_l": 1.20},
				"y": {}, "z": {}, "spine_x": 0.55},
			{"t": 1.0, "x": {}, "y": {}, "z": {}, "spine_x": 0.0},
		],
	},
]

enum State { IDLE, RUN, ATTACK }

var _skeleton: Skeleton3D
var _rest: Dictionary = {}
var _state := State.IDLE
var _cycle_t := 0.0
var _time := 0.0
var _model_base_y := 0.0
var _camera_offset := Vector3(2.2, 1.9, 3.6)
var _autorun := false
var _autoattack := false

var _attack_index := 0
var _attack_t := 0.0
var _attack_hit_done := false
var _queued := false
var _buffered := 0.0
var _hitstop := 0.0
var _shake := 0.0
var _dummies: Array[Node3D] = []
var _staff: Node3D
var _trail := ImmediateMesh.new()
var _trail_instance: MeshInstance3D
var _trail_points: Array[Vector3] = []
var _dummy_hit: Dictionary = {}
var _player: AnimationPlayer
# debug orbit camera: hold right mouse to orbit, wheel to zoom, R to reset
var _cam_yaw_off := 0.0
var _cam_pitch_off := 0.0
var _cam_dist_off := 0.0
var _turn_target := Vector3.ZERO
var _has_turn_target := false


func _ready() -> void:
	_autorun = OS.get_environment("WUKONG_AUTORUN") == "1"
	_autoattack = OS.get_environment("WUKONG_AUTOATTACK") == "1"
	if _autorun:
		_camera_offset = Vector3(4.2, 1.4, 0.0)
	var player := get_node_or_null("Wukong/AnimationPlayer") as AnimationPlayer
	if player:
		player.stop()
		_player = player
	_skeleton = find_child("Skeleton3D", true, false) as Skeleton3D
	_cache_rest()
	_model_base_y = model.position.y
	_attach_staff()
	_setup_trail()
	_spawn_dummies()
	var forward := Vector3(sin(model.rotation.y), 0.0, cos(model.rotation.y))
	camera.position = model.position - forward * 4.2 + Vector3(0.0, 2.3, 0.0)
	camera.look_at(model.position + Vector3(0.0, 1.1, 0.0))
	print("WASD move | J attack | LMB drag camera | RMB click to turn | I ink")


func _cache_rest() -> void:
	_rest.clear()
	for index in range(_skeleton.get_bone_count()):
		_rest[_skeleton.get_bone_name(index)] = _skeleton.get_bone_rest(index).basis.get_rotation_quaternion()


func _pose(bone_name: String, axis: Vector3, angle: float) -> void:
	var index := _skeleton.find_bone(bone_name)
	if index < 0:
		return
	var rest: Quaternion = _rest.get(bone_name, Quaternion.IDENTITY)
	_skeleton.set_bone_pose_rotation(index, rest * Quaternion(axis, angle))


func _reset_pose() -> void:
	# Reset rotation AND position: the Run animation animates the pelvis / foot IK
	# bone positions, so a rotation-only reset left the body parked in the last run
	# frame (pelvis up to 13 cm low) and the feet sank into the ground when idling.
	for index in range(_skeleton.get_bone_count()):
		var bone_name := _skeleton.get_bone_name(index)
		_skeleton.set_bone_pose_rotation(index, _rest.get(bone_name, Quaternion.IDENTITY))
		_skeleton.set_bone_pose_position(index, _skeleton.get_bone_rest(index).origin)
		_skeleton.set_bone_pose_scale(index, Vector3.ONE)


func _process(delta: float) -> void:
	_time += delta
	if _autoattack and _time > 0.12 and _state != State.ATTACK:
		_try_attack()
	if _hitstop > 0.0:
		_hitstop -= delta
	elif _state == State.ATTACK:
		_advance_attack(delta)
	_update_camera(delta)
	_update_trail(_state == State.ATTACK)
	if _state == State.RUN and _player != null:
		if _player.current_animation != "Run":
			_player.play("Run")
			_player.get_animation("Run").loop_mode = Animation.LOOP_LINEAR
	elif _state != State.RUN and _player != null and _player.is_playing():
		_player.stop()
	if _state == State.RUN and _player != null:
		if _staff:
			_set_staff_carry()
	elif _state == State.RUN:
		_apply_run(delta)
	elif _state == State.IDLE:
		_apply_idle()
		# keep the same carried orientation as the run, otherwise the staff snaps to
		# world-axis-aligned and reads as floating next to the fist
		_set_staff_carry()
	if _state == State.ATTACK and _staff:
		_staff.global_rotation = Vector3.ZERO
		_staff.position = Vector3.ZERO      # undo the run carry's axis slide
	_update_dummies(delta)


func _set_staff_carry() -> void:
	if _staff == null:
		return
	# LOCAL rotation relative to the grip socket. The old version wrote a world-space
	# basis every frame, which cancelled the hand's rotation: the staff stood bolt
	# upright while the arm pumped, the one part of the body that never followed.
	#
	# v15: the run leans ~30 deg and the arm now pumps through 30 deg, so the old
	# -64 deg carry pointed the tip out at face height like a couched lance. The
	# staff now trails up behind the right shoulder, and it is slid 0.45 m along its
	# own axis (grip 0.25 m from one end) so the front end stays by the hip instead
	# of running out past the knee. Swept with tools/shots/shot_staff.gd.
	var carry := Basis.from_euler(Vector3(deg_to_rad(200.0), 0.0, deg_to_rad(-14.0)))
	_staff.rotation = carry.get_euler()
	_staff.position = carry * Vector3(0.0, 0.45, 0.0)


func _physics_process(delta: float) -> void:
	if _state == State.ATTACK:
		model.position.y = _model_base_y
		return
	# Input basis comes from the character's own yaw, NOT from camera.global_basis.
	# The follow cam is offset to the side, so its forward is skewed ~13 deg from the
	# body; steering off that made W curve in a circle (turn -> cam follows -> turn).
	var body_forward := Vector3(sin(model.rotation.y), 0.0, cos(model.rotation.y))
	# character's LEFT is +X at yaw 0 (thigh_l sits at +X), so A must ADD this
	var body_left := Vector3(body_forward.z, 0.0, -body_forward.x)
	var direction := Vector3.ZERO
	if Input.is_physical_key_pressed(KEY_W):
		direction += body_forward
	if Input.is_physical_key_pressed(KEY_S):
		direction -= body_forward
	if Input.is_physical_key_pressed(KEY_A):
		direction += body_left
	if Input.is_physical_key_pressed(KEY_D):
		direction -= body_left
	direction.y = 0.0

	if _autorun:
		direction = Vector3(0.0, 0.0, -1.0)

	if direction.length() > 0.01:
		direction = direction.normalized()
		_state = State.RUN
		_has_turn_target = false
		model.position += direction * RUN_SPEED * delta
		var target_yaw := atan2(direction.x, direction.z)
		model.rotation.y = lerp_angle(model.rotation.y, target_yaw, delta * TURN_RATE)
	else:
		_state = State.IDLE
		# right-click puts a point on the ground; the character turns in place to face it
		if _has_turn_target:
			var to := _turn_target - model.position
			to.y = 0.0
			if to.length() < 0.08:
				_has_turn_target = false
			else:
				var want := atan2(to.x, to.z)
				model.rotation.y = lerp_angle(model.rotation.y, want, clamp(delta * TURN_RATE, 0.0, 1.0))
				if absf(wrapf(want - model.rotation.y, -PI, PI)) < 0.02:
					_has_turn_target = false


func _apply_idle() -> void:
	_reset_pose()
	var breathe := sin(_time * 1.6) * 0.02
	_pose("spine_02", Vector3.RIGHT, breathe)
	_pose("chest", Vector3.RIGHT, breathe * 0.7)
	_pose("head", Vector3.RIGHT, -breathe * 0.6)
	for i in range(1, 5):
		_pose("tail_0%d" % i, Vector3.UP, sin(_time * 1.2 + i * 0.6) * 0.07)
	model.position.y = _model_base_y


func _apply_run(delta: float) -> void:
	_reset_pose()
	_cycle_t = fmod(_cycle_t + delta / RUN_CYCLE, 1.0)
	var scaled := _cycle_t * 4.0
	var index := int(floor(scaled)) % 4
	var next := (index + 1) % 4
	var t := smoothstep(0.0, 1.0, scaled - floor(scaled))
	var a: Dictionary = POSES[index]
	var b: Dictionary = POSES[next]

	_pose("thigh_l", Vector3.RIGHT, lerp(a["thigh_l"], b["thigh_l"], t))
	_pose("shin_l", Vector3.RIGHT, lerp(a["shin_l"], b["shin_l"], t))
	_pose("thigh_r", Vector3.RIGHT, lerp(a["thigh_r"], b["thigh_r"], t))
	_pose("shin_r", Vector3.RIGHT, lerp(a["shin_r"], b["shin_r"], t))
	_pose("upperarm_l", Vector3.RIGHT, lerp(a["upperarm_l"], b["upperarm_l"], t))
	_pose("upperarm_r", Vector3.RIGHT, lerp(a["upperarm_r"], b["upperarm_r"], t))
	_pose("lowerarm_l", Vector3.RIGHT, 0.25)
	_pose("lowerarm_r", Vector3.RIGHT, 0.25)
	_pose("spine_01", Vector3.RIGHT, 0.28)
	var twist: float = lerp(a["twist"], b["twist"], t)
	_pose("pelvis", Vector3.UP, -twist * 0.7)
	_pose("spine_02", Vector3.UP, twist)
	_pose("chest", Vector3.UP, -twist * 1.6)
	_pose("head", Vector3.UP, twist * 0.4)
	_pose("foot_l", Vector3.RIGHT, 0.15 + max(0.0, sin(_cycle_t * TAU)) * 0.35)
	_pose("foot_r", Vector3.RIGHT, 0.15 + max(0.0, -sin(_cycle_t * TAU)) * 0.35)
	_pose("tail_01", Vector3.UP, twist)
	_pose("tail_02", Vector3.UP, twist * 0.8)
	model.position.y = _model_base_y + lerp(a["bob"], b["bob"], t)
	if _staff:
		_staff.rotation = Vector3(deg_to_rad(-72.0), 0.0, deg_to_rad(-10.0))


func _update_camera(delta: float) -> void:
	if _autorun:
		camera.position = model.position + Vector3(4.2, 1.2, 0.0)
		camera.look_at(model.position + Vector3(0.0, 1.0, 0.0))
		return
	# Orbitable follow cam. Base pose is a ~13 deg off-axis 3/4 rear view (a dead-centre
	# rear view of a symmetric character reads as narrow); hold RIGHT mouse to orbit
	# around the character, wheel to zoom, R to snap back to the base view.
	var pivot := model.position + Vector3(0.0, 1.05, 0.0)
	var yaw: float = model.rotation.y + _cam_yaw_off
	var forward := Vector3(sin(yaw), 0.0, cos(yaw))
	var screen_right := Vector3(-forward.z, 0.0, forward.x)
	var pitch: float = clamp(0.18 + _cam_pitch_off, -0.35, 1.0)
	var dist: float = clamp(3.60 + _cam_dist_off, 1.60, 8.0)
	# over-the-shoulder: the camera is shifted sideways but still looks nearly parallel
	# to the body, so W stays "up the screen" instead of drifting off at an angle
	var target := (pivot - forward * (dist * cos(pitch)) + screen_right * 0.85
		+ Vector3(0.0, dist * sin(pitch), 0.0))
	camera.position = camera.position.lerp(target, clamp(delta * 3.0, 0.0, 1.0))
	var shake := Vector3.ZERO
	if _shake > 0.0:
		_shake = max(0.0, _shake - delta * 6.0)
		shake = Vector3(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0), 0.0) * _shake * 0.05
	camera.look_at(pivot + screen_right * 0.30 + shake)


func _try_attack() -> void:
	if _state != State.ATTACK:
		_start_attack(0)
		return
	var attack: Dictionary = ATTACKS[_attack_index]
	var t: float = _attack_t / float(attack["duration"])
	if t > 0.55 and t < 0.98:
		_queued = true
	else:
		_buffered = 0.18


func _start_attack(index: int) -> void:
	_state = State.ATTACK
	_attack_index = clampi(index, 0, ATTACKS.size() - 1)
	_attack_t = 0.0
	_attack_hit_done = false
	_queued = false
	_buffered = 0.0
	model.position.y = _model_base_y


func _advance_attack(delta: float) -> void:
	var attack: Dictionary = ATTACKS[_attack_index]
	var duration: float = attack["duration"]
	_attack_t += delta
	var t: float = clamp(_attack_t / duration, 0.0, 1.0)
	_apply_attack_pose(attack, t)

	if _buffered > 0.0:
		_buffered = max(0.0, _buffered - delta)
		if t >= 0.55 and not _queued:
			_queued = true
			_buffered = 0.0

	var window: Array = attack["hit"]
	if not _attack_hit_done and t >= window[0] and t <= window[1]:
		_attack_hit_done = true
		_perform_hit()

	if t >= 1.0:
		if _queued and _attack_index < ATTACKS.size() - 1:
			_start_attack(_attack_index + 1)
		else:
			_state = State.IDLE
			_queued = false


func _apply_attack_pose(attack: Dictionary, t: float) -> void:
	_reset_pose()
	var poses: Array = attack["poses"]
	var i := 0
	while i < poses.size() - 2 and t > poses[i + 1]["t"]:
		i += 1
	var a: Dictionary = poses[i]
	var b: Dictionary = poses[i + 1]
	var span: float = max(0.0001, b["t"] - a["t"])
	var local: float = clamp((t - a["t"]) / span, 0.0, 1.0)
	local = smoothstep(0.0, 1.0, local)

	_apply_axis(a, b, "x", Vector3.RIGHT, local)
	_apply_axis(a, b, "y", Vector3.UP, local)
	_apply_axis(a, b, "z", Vector3.FORWARD, local)

	var spine_x: float = lerp(float(a.get("spine_x", 0.0)), float(b.get("spine_x", 0.0)), local)
	_pose("spine_01", Vector3.RIGHT, spine_x - 0.05)


func _apply_axis(a: Dictionary, b: Dictionary, key: String, axis: Vector3, local: float) -> void:
	var bones := {}
	for bone_name in a[key]:
		bones[bone_name] = true
	for bone_name in b[key]:
		bones[bone_name] = true
	for bone_name in bones:
		var av: float = a[key].get(bone_name, 0.0)
		var bv: float = b[key].get(bone_name, 0.0)
		_pose(bone_name, axis, lerp(av, bv, local))


func _perform_hit() -> void:
	var yaw: float = model.rotation.y
	var forward := Vector3(sin(yaw), 0.0, cos(yaw))
	var hit_any := false
	for dummy in _dummies:
		if _dummy_hit.get(dummy, -1) == _attack_index:
			continue
		var offset: Vector3 = dummy.position - model.position
		offset.y = 0.0
		if offset.length() > ATTACK_RADIUS:
			continue
		var angle := forward.angle_to(offset.normalized())
		if angle > ATTACK_HALF_ANGLE:
			continue
		_dummy_hit[dummy] = _attack_index
		_dummy_flash(dummy)
		hit_any = true
	if hit_any:
		_hitstop = 0.06
		_shake = 0.6


func _dummy_flash(dummy: Node3D) -> void:
	var mesh := dummy.get_node_or_null("Mesh") as MeshInstance3D
	if mesh == null:
		return
	var material := mesh.material_override as StandardMaterial3D
	if material:
		material.albedo_color = Color(0.9, 0.2, 0.15)
	dummy.set_meta("flash", 0.25)


func _update_dummies(delta: float) -> void:
	for dummy in _dummies:
		var flash: float = dummy.get_meta("flash", 0.0)
		if flash > 0.0:
			flash = max(0.0, flash - delta)
			dummy.set_meta("flash", flash)
			if flash == 0.0:
				var mesh := dummy.get_node_or_null("Mesh") as MeshInstance3D
				if mesh and mesh.material_override:
					(mesh.material_override as StandardMaterial3D).albedo_color = Color(0.45, 0.42, 0.38)


func _spawn_dummies() -> void:
	var positions := [Vector3(0.9, 0, 1.4), Vector3(-0.8, 0, 1.5), Vector3(1.6, 0, 0.6), Vector3(-1.6, 0, 0.7)]
	for i in range(positions.size()):
		var dummy := Node3D.new()
		dummy.name = "Dummy%d" % i
		dummy.position = positions[i]
		var mesh := MeshInstance3D.new()
		mesh.name = "Mesh"
		var capsule := CapsuleMesh.new()
		capsule.height = 1.6
		capsule.radius = 0.25
		mesh.mesh = capsule
		var material := StandardMaterial3D.new()
		material.albedo_color = Color(0.45, 0.42, 0.38)
		material.roughness = 0.9
		mesh.material_override = material
		mesh.position.y = 0.8
		dummy.add_child(mesh)
		add_child(dummy)
		_dummies.append(dummy)


func _attach_staff() -> void:
	if _skeleton == null:
		return
	var attachment := BoneAttachment3D.new()
	attachment.name = "WeaponSocket"
	attachment.bone_name = "grip_r"
	_skeleton.add_child(attachment)
	var staff := STAFF_SCENE.instantiate()
	staff.name = "Staff"
	attachment.add_child(staff)
	_staff = staff
	await get_tree().process_frame
	staff.global_rotation = Vector3.ZERO
	if OS.get_environment("WUKONG_GRIPCAM") == "1":
		camera.position = staff.global_position + Vector3(0.55, 0.18, 0.65)
		camera.look_at(staff.global_position + Vector3(0.0, 0.1, 0.0))


func _setup_trail() -> void:
	_trail_instance = MeshInstance3D.new()
	_trail_instance.name = "StaffTrail"
	_trail_instance.mesh = _trail
	_trail_instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.vertex_color_use_as_albedo = true
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	_trail_instance.material_override = material
	add_child(_trail_instance)


func _update_trail(visible_now: bool) -> void:
	if _staff == null or _trail_instance == null:
		return
	if not visible_now:
		_trail_points.clear()
		_trail.clear_surfaces()
		return
	var tip: Vector3 = _staff.global_transform * Vector3(0.0, 0.68, 0.0)
	_trail_points.push_front(tip)
	if _trail_points.size() > 24:
		_trail_points.pop_back()
	if _trail_points.size() < 2:
		return
	var right: Vector3 = camera.global_transform.basis.x
	_trail.clear_surfaces()
	_trail.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	for index in range(_trail_points.size()):
		var fade := 1.0 - float(index) / float(_trail_points.size())
		fade = fade * fade
		var colour := Color(0.86, 0.95, 1.0, 0.5 * fade)
		var point: Vector3 = _trail_points[index]
		_trail.surface_set_color(colour)
		_trail.surface_add_vertex(point + right * 0.035)
		_trail.surface_set_color(colour)
		_trail.surface_add_vertex(point - right * 0.035)
	_trail.surface_end()


func _unhandled_input(event: InputEvent) -> void:
	# LEFT drag orbits the camera, wheel zooms, R resets.
	# RIGHT click sends the character to that spot on the ground (turn in place).
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_cam_yaw_off -= event.relative.x * 0.006
		# drag DOWN (relative.y > 0) raises the camera and looks down, which is the
		# usual third-person convention (it was inverted)
		_cam_pitch_off = clamp(_cam_pitch_off + event.relative.y * 0.004, -0.5, 0.8)
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_I:
			ink_layer.visible = not ink_layer.visible
			print("Ink post-process: ", "on" if ink_layer.visible else "off")
		elif event.keycode == KEY_J:
			_try_attack()
		elif event.keycode == KEY_R or event.keycode == KEY_HOME:
			_cam_yaw_off = 0.0
			_cam_pitch_off = 0.0
			_cam_dist_off = 0.0
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			var mpos: Vector2 = event.position
			var origin := camera.project_ray_origin(mpos)
			var dir := camera.project_ray_normal(mpos)
			if absf(dir.y) > 0.0001:
				var t: float = (model.position.y - origin.y) / dir.y
				if t > 0.0:
					_turn_target = origin + dir * t
					_has_turn_target = true
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_cam_dist_off = clamp(_cam_dist_off - 0.30, -1.8, 4.0)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_cam_dist_off = clamp(_cam_dist_off + 0.30, -1.8, 4.0)
