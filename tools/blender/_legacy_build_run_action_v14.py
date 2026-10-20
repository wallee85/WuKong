"""Build the run cycle analytically: two-bone leg solve -> local bone rotations.

Why analytic: reading PoseBone.matrix / .tail in a background build returns stale
values (the depsgraph does not refresh the pose for reads), and the shin IK
constraint made every pose depend on that stale evaluation. Solving the leg in
closed form and writing local rotations needs no evaluation at all, bakes to
plain FK, and exports unchanged.

Numbers (see docs/量参考_跑步.md):
  speed v = 4.20 m/s, cycle 17 frames @ 24 fps = 0.7083 s (170 steps/min,
  step length 1.48 m -- 222 spm at 13 frames read as "sewing machine legs")
  stance = 26.5% of the cycle -> stance sweep 0.788 m (+-0.394), no foot slide
  contact knee ~152 deg: the leg never locks straight
  ankle height derived from foot pitch so the sole stays on the ground

  Every channel is driven off the same phase u, but NOT on the same frame: each link
  of the chain (pelvis -> spine -> chest -> shoulder -> elbow -> hand) trails the one
  above it by 1-1.5 frames, and the head trails the chest by 3. That is the
  "desynchronised parts" pass from the animation skill (Step 4/6). Without it every
  joint reaches its extreme on the same frame and the body reads as one rigid block.

  blender -b --python tools/blender/build_run_action.py
"""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"

FPS = 24
CYCLE = 17
# Stance fraction trades stride against airtime at a fixed speed (stride = v*T*s/2).
# 0.343 at 13 frames = 222 spm: the legs outran the body and read as flailing.
# At 17 frames the same 0.79 m sweep gives 170 spm / 1.48 m steps -- a long-stride
# run instead of a scurry.
STANCE = 0.265
SPEED = 4.20
STRIDE = SPEED * STANCE * (CYCLE / FPS) / 2.0

SOLE_Z = 0.079
BALL_DIST = 0.1317
BALL_ANG = math.radians(9.2)

# The whole foot path sits 7.5 cm behind the pelvis. With the 39 deg lean the COM is
# already well forward, and this is what buys the contact knee its bend: landing
# 0.316 m ahead of the hip instead of 0.394 keeps the leg at ~0.96 of its length
# (knee 152 deg) at the same 0.788 m stance sweep -- so the sole can sit on the floor.
FOOT_Y_BIAS = 0.035
# The boot mesh itself is modelled 23.5 deg toe-out ("外八字") even though the foot
# BONE points dead ahead (measured: foot bone yaw 0.0, boot yaw +23.5 L / -23.7 R).
# The boot is weighted 43% foot / 43% shin / 13% toe, so yawing the foot bone alone
# only takes out half of it: distribute the internal rotation over hip, calf and foot.
FOOT_YAW = {"l": -23.5, "r": 23.5}
THIGH_TWIST = 8.0      # internal rotation at the hip, degrees (mirrored for R)
SHIN_TWIST = 11.0      # internal rotation of the calf, degrees

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
scene.render.fps = FPS
scene.render.fps_base = 1.0
rig = bpy.data.objects["Wukong_Rig"]
bpy.context.view_layer.objects.active = rig

# --- mute the leg IK: the action is baked FK, the constraint would override it
for side in ("l", "r"):
    for c in rig.pose.bones["shin_%s" % side].constraints:
        if c.type == "IK":
            c.mute = True
    for c in list(rig.pose.bones["foot_%s" % side].constraints):
        rig.pose.bones["foot_%s" % side].constraints.remove(c)

for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.location = (0.0, 0.0, 0.0)
    pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    pb.scale = (1.0, 1.0, 1.0)

REST_M = {b.name: b.matrix_local.copy() for b in rig.data.bones}
REST_R = {n: m.to_3x3() for n, m in REST_M.items()}
HEAD = {n: m.translation.copy() for n, m in REST_M.items()}

THIGH_L = rig.data.bones["thigh_l"].length
SHIN_L = rig.data.bones["shin_l"].length
REACH = THIGH_L + SHIN_L
HIP_OFF = Vector((0.10, 0.0, HEAD["thigh_l"].z - HEAD["pelvis"].z))   # rest offset
ANKLE_X = 0.095

old = bpy.data.actions.get("Run")
if old:
    bpy.data.actions.remove(old)
action = bpy.data.actions.new("Run")
action.use_fake_user = True
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = action


# ------------------------------------------------------------------ curve tools
def catmull(vals, u):
    n = len(vals)
    x = (u % 1.0) * n
    i = int(math.floor(x))
    t = x - i
    p0, p1, p2, p3 = vals[(i - 1) % n], vals[i % n], vals[(i + 1) % n], vals[(i + 2) % n]
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def table(u, keys):
    if u <= keys[0][0]:
        return keys[0][1]
    if u >= keys[-1][0]:
        return keys[-1][1]
    for (u0, v0), (u1, v1) in zip(keys, keys[1:]):
        if u0 <= u <= u1:
            return lerp(v0, v1, smooth((u - u0) / (u1 - u0)))
    return keys[-1][1]


def arc_to(a, b):
    """Minimal rotation taking unit vector a to unit vector b."""
    a = a.normalized()
    b = b.normalized()
    d = max(-1.0, min(1.0, a.dot(b)))
    if d > 0.999999:
        return Matrix.Identity(3)
    if d < -0.999999:
        axis = a.orthogonal().normalized()
        return Matrix.Rotation(math.pi, 3, axis)
    axis = a.cross(b).normalized()
    return Matrix.Rotation(math.acos(d), 3, axis)


# ------------------------------------------------------------------ chain timing
# Frames of delay per link. The pelvis drives; everything else trails it. Measured in
# this rig: with all lags at 0 every channel peaks on frame 0 and the arc of the hand
# is a straight line -- the "all joints arrive together" tell.
LAG_PELVIS_YAW = 0.5
LAG_SPINE_01 = 1.0
LAG_SPINE_02 = 1.5
LAG_CHEST = 2.0
LAG_CLAVICLE = 2.0
LAG_ARM = 0.5          # shoulder swing (curve already sits on the leg cycle)
LAG_ELBOW = 3.5        # forearm trails the upper arm by one more link
LAG_HEAD = 3.0         # head lag 2-3 frames in a cycle (Joey, skill reference)
ARM_ELASTIC = 10.0     # degrees the elbow opens at the back / closes at the front

# Arm swing is keyed to the LEG CYCLE, not to a free-running cosine. Spec (client):
# at LEFT TOE-OFF the left hand is at the chest and the right hand is behind the hip;
# at LEFT CONTACT it is the other way round. Toe-off is at u = STANCE (0.265), so the
# left arm peaks +1 there and -1 at u = 0, with a slower return through the flight.
# One curve drives both arms; the right arm uses -curve.
ARM_CURVE = [
    (0.00, -1.00),   # left contact      -> left hand behind
    (0.09, -0.96),
    (0.20, -0.15),
    (0.30, +0.90),
    (0.36, +1.00),   # just after left toe-off -> left hand at the chest
    (0.48, +0.72),
    (0.62, +0.05),
    (0.78, -0.72),
    (0.90, -0.95),
    (1.00, -1.00),
]


def arm_curve(u):
    return table(u % 1.0, ARM_CURVE)


def ph(u, lag_frames):
    """Phase u shifted back by lag_frames, wrapped to the cycle."""
    return (u - lag_frames / CYCLE) % 1.0


def lean_osc_at(u):
    """Torso lean breathes with the stride: hardest after toe-off, upright mid-flight."""
    return 1.0 + 0.10 * math.cos(2.0 * math.pi * (u - 0.35))


def bone_world_rot(name, cache):
    """Armature-space rotation of a pose bone, composed from the basis quats set this
    frame. Reading pb.matrix in a background build is stale, so the chain is composed
    by hand: pose = parent_pose @ (parent_rest^-1 @ rest) @ basis."""
    if name in cache:
        return cache[name]
    pb = rig.pose.bones[name]
    basis = pb.rotation_quaternion.to_matrix()
    if pb.parent is None:
        R = REST_R[name] @ basis
    else:
        R = (bone_world_rot(pb.parent.name, cache)
             @ (REST_R[pb.parent.name].inverted() @ REST_R[name])
             @ basis)
    cache[name] = R
    return R


def aim(name, target_dir, cache):
    """Point a bone's +Y at a world direction with the minimum twist, then store the
    result as a local basis rotation. Used for arms: aiming in world space is the only
    way to get a sagittal swing out of an A-pose rest arm."""
    pb = rig.pose.bones[name]
    rest_dir = (REST_R[name] @ Vector((0.0, 1.0, 0.0))).normalized()
    R_pose = arc_to(rest_dir, target_dir) @ REST_R[name]
    if pb.parent is None:
        R_parent, rest_off = Matrix.Identity(3), REST_R[name]
    else:
        R_parent = bone_world_rot(pb.parent.name, cache)
        rest_off = REST_R[pb.parent.name].inverted() @ REST_R[name]
    pb.rotation_quaternion = ((R_parent @ rest_off).inverted() @ R_pose).to_quaternion()
    cache[name] = R_pose


# ------------------------------------------------------------------ leg targets
# Forefoot strike. A runner lands on the ball of the foot, heel up -- a flat-footed
# contact (pitch 0, the previous pass) is a walk cue. Pitch 14 at touchdown, 34 at
# toe-off (was 40: the higher the pitch the higher the ankle, and the shorter the leg
# reads at push-off).
STANCE_PITCH = [(0.00, 14.0), (0.22, 6.0), (0.45, 0.0), (0.62, 2.0),
                (0.80, 12.0), (0.92, 26.0), (1.00, 34.0)]
# swing keys: (u, ankle y as a fraction of STRIDE, ankle z, foot pitch)
# The heel used to kick to 0.62 m with the ankle 0.60 back -- the knee folded to 29
# deg and the leg read as "curled up". Now the knee drives forward and the heel only
# comes up to 0.50: minimum knee 60 deg, the leg stays long on the way through.
SWING = [
    (STANCE, +1.00, 0.189, 34.0),
    (0.36, +1.10, 0.315, 48.0),
    (0.44, +0.95, 0.430, 50.0),
    (0.52, +0.62, 0.500, 44.0),
    (0.60, +0.22, 0.505, 32.0),
    (0.68, -0.18, 0.470, 18.0),
    (0.76, -0.50, 0.420, 6.0),
    (0.84, -0.70, 0.360, 0.0),
    (0.91, -0.86, 0.280, 6.0),
    (0.96, -0.95, 0.200, 16.0),
    (1.00, -1.00, 0.150, 14.0),
]


def ankle_z_from_pitch(pitch_deg):
    # +0.020: the boot sole is skinned partly to the shin, so a flat planted foot
    # sinks ~2 cm into the ground without this bias (measured in check_run_action)
    return SOLE_Z + BALL_DIST * math.sin(BALL_ANG + math.radians(pitch_deg)) + 0.020


def leg_state(u):
    y, z, pitch, planted = _leg_state_raw(u)
    return y + FOOT_Y_BIAS, z, pitch, planted


def _leg_state_raw(u):
    u = u % 1.0
    if u <= STANCE:
        p = u / STANCE
        pitch = table(p, STANCE_PITCH)
        # Forefoot contact: the boot is skinned 43% to the shin, so pressing the ankle
        # down a few mm at touchdown is what puts the ball of the foot on the floor
        # instead of hovering 14 mm above it (measured). Late stance needs the opposite:
        # the toe roll was sinking the boot 5.5 mm, so lift it there.
        press = 0.032 * max(0.0, 1.0 - p / 0.30)
        lift = 0.008 * min(max((p - 0.50) / 0.40, 0.0), 1.0)
        return (-STRIDE + 2.0 * STRIDE * p,
                ankle_z_from_pitch(pitch) - press + lift, pitch, True)
    us = [k[0] for k in SWING]
    if u <= us[0]:
        return SWING[0][1] * STRIDE, SWING[0][2], SWING[0][3], False
    if u >= us[-1]:
        return SWING[-1][1] * STRIDE, SWING[-1][2], SWING[-1][3], False
    i = max(i for i in range(len(SWING) - 1) if us[i] <= u)
    t = smooth((u - us[i]) / (us[i + 1] - us[i]))
    return (lerp(SWING[i][1], SWING[i + 1][1], t) * STRIDE,
            lerp(SWING[i][2], SWING[i + 1][2], t),
            lerp(SWING[i][3], SWING[i + 1][3], t), False)


# One step = 7 frames. Hip height against a standing hip of 0.95. Landing lower
# (0.836, not 0.850) is what keeps the contact knee bent; the rise into flight is
# slightly higher and flatter than before so the run does not pump up and down.
HIP_HALF = [0.856, 0.830, 0.824, 0.830, 0.846, 0.862, 0.874, 0.884, 0.892, 0.898, 0.900, 0.894, 0.878, 0.864]
YAW_HALF = [10.0, 7.5, 1.5, -7.5, -10.0, -7.5, -1.5]
HIP_Z = HIP_HALF + HIP_HALF
PELVIS_YAW = YAW_HALF + [-v for v in YAW_HALF]

# Torso lean: 39 deg total. 48 deg photographed as a beast-crouch: the shoulders
# were below the hips at the drive frame and the head was buried (head pitch 44).
LEAN_PELVIS = 25.0
LEAN_01 = 3.0
LEAN_02 = 2.0
LEAN_CHEST = 0.0
TORSO_LEAN = LEAN_PELVIS + LEAN_01 + LEAN_02 + LEAN_CHEST

# Arms (degrees). swing = amplitude around the vertical, bias pushes the whole arc
# forward so the hand travels chest-front -> hip-back. lat is the sideways offset of
# the aim direction: 0.22 keeps the arm clear of the robe without splaying it.
ARM_AMP_L, ARM_ELBOW_L, ARM_LAT_L, ARM_BIAS_L = 52.0, 66.0, 0.20, 5.0
ARM_AMP_R, ARM_ELBOW_R, ARM_LAT_R, ARM_BIAS_R = 40.0, 58.0, 0.15, 3.0


def solve_leg(H, A, side):
    """Two-bone solve. Returns (thigh_dir, shin_dir, knee_pos, clamped_target)."""
    d = A - H
    L = d.length
    if L < 1e-6:
        d = Vector((0.0, 0.0, -1.0))
        L = 0.01
    L = min(L, 0.995 * REACH)
    w = d.normalized()
    a = (THIGH_L ** 2 - SHIN_L ** 2 + L * L) / (2.0 * L)
    h = math.sqrt(max(THIGH_L ** 2 - a * a, 0.0))
    # pure sagittal knee plane: any lateral component twists the shin, and the
    # boot is skinned ~20% to the shin, which shows up as a toe-out ("外八字")
    knee_plane_dir = Vector((0.0, -1.0, 0.0))
    m = knee_plane_dir - w * knee_plane_dir.dot(w)
    if m.length < 1e-5:
        m = (Vector((0.0, -1.0, 0.0)) - w * Vector((0.0, -1.0, 0.0)).dot(w))
    m.normalize()
    K = H + w * a + m * h
    return (K - H).normalized(), (H + w * L - K).normalized(), K, H + w * L


frames = list(range(0, CYCLE + 1))   # 0..14 so the glTF sampler starts at t = 0
rows = []

for f in frames:
    u = f / CYCLE
    scene.frame_set(f)
    hip_z = catmull(HIP_Z, u)
    yaw = math.radians(catmull(PELVIS_YAW, u))
    # lean breathes with the stride: hardest during the drive just after toe-off,
    # most upright in mid-flight. A constant lean reads as a pose, not as running.
    lean_osc = 1.0 + 0.10 * math.cos(2.0 * math.pi * (u - 0.35))
    lean_p = math.radians(LEAN_PELVIS * lean_osc)

    R_pelvis = (Matrix.Rotation(lean_p, 3, "X") @ Matrix.Rotation(yaw, 3, "Z"))
    pelvis_desired = (Matrix.Translation(Vector((0.0, 0.0, hip_z)))
                      @ (R_pelvis @ REST_R["pelvis"]).to_4x4())
    pelvis = rig.pose.bones["pelvis"]
    basis = REST_M["pelvis"].inverted() @ pelvis_desired
    loc, rot, _ = basis.decompose()
    pelvis.location = loc
    pelvis.rotation_quaternion = rot
    pelvis.keyframe_insert("location", frame=f)
    pelvis.keyframe_insert("rotation_quaternion", frame=f)

    # ---- torso: the shoulder girdle COUNTER-rotates against the pelvis (it used to
    # co-rotate with it: -0.30 -0.85 +1.70 summed to +0.55, so the shoulders turned
    # WITH the hips). Targets are world yaw as a fraction of the pelvis yaw, each one
    # trailing the link below by 1-1.5 frames, so the twist travels up the spine.
    prev_yaw = yaw
    for name, lean, frac, lag in (("spine_01", LEAN_01, 0.78, LAG_SPINE_01),
                                  ("spine_02", LEAN_02, 0.50, LAG_SPINE_02),
                                  ("chest", LEAN_CHEST, -0.40, LAG_CHEST)):
        ul = ph(u, lag)
        target = frac * math.radians(catmull(PELVIS_YAW, ul))
        local_yaw = target - prev_yaw
        prev_yaw = target
        pb = rig.pose.bones[name]
        pb.rotation_quaternion = (Quaternion((1, 0, 0), math.radians(lean * lean_osc_at(ul)))
                                  @ Quaternion((0, 1, 0), local_yaw))
        pb.keyframe_insert("rotation_quaternion", frame=f)

    # Head: 0.55 of the torso lean cancelled, and it runs 3 frames behind the chest.
    # The instant compensation it had before pinned the head to the pelvis yaw, so the
    # skull was the only part of the body that never lagged.
    uh = ph(u, LAG_HEAD)
    head_target = 0.0
    local_yaw = head_target - prev_yaw
    for name, k in (("neck", 0.6), ("head", 0.4)):
        pb = rig.pose.bones[name]
        pb.rotation_quaternion = (Quaternion((1, 0, 0), math.radians(TORSO_LEAN * lean_osc_at(uh)) * -0.32)
                                  @ Quaternion((0, 1, 0), local_yaw * k))
        pb.keyframe_insert("rotation_quaternion", frame=f)

    # pull the shoulder tips back ~9 deg: rounded/clutched shoulders are the single
    # biggest remaining "thief" cue from the follow cam
    for side, sgn in (("l", 1.0), ("r", -1.0)):
        cb = rig.pose.bones["clavicle_%s" % side]
        cb.rotation_mode = "QUATERNION"
        cax = (REST_R["clavicle_%s" % side].inverted() @ Vector((0.0, 0.0, 1.0))).normalized()
        cb.rotation_quaternion = Quaternion(cax, math.radians(9.0) * sgn)
        cb.keyframe_insert("rotation_quaternion", frame=f)

    # ---- arms: AIMED IN WORLD SPACE. The old version spun the upper arm about the
    # world X axis in the bone's local frame; because the A-pose arm points 40 deg
    # out, that swept a cone and 43% of the hand's travel went sideways (measured:
    # lateral 0.275 m vs sagittal 0.647 m). Aiming the bone at a direction that lives
    # in the sagittal plane fixes the plane itself, and the elbow is aimed the same
    # way so it cannot bend out to the side.
    cache = {}
    for side, amp, elbow, lat, bias in (("l", ARM_AMP_L, ARM_ELBOW_L, ARM_LAT_L, ARM_BIAS_L),
                                        ("r", ARM_AMP_R, ARM_ELBOW_R, ARM_LAT_R, ARM_BIAS_R)):
        sgn = 1.0 if side == "l" else -1.0
        # One curve drives both arms; the right one runs on -curve. c = +1 means THIS
        # arm is at the chest, -1 means it is behind the hip.
        c = arm_curve(ph(u, LAG_ARM)) * sgn
        sw_ang = bias + amp * c
        # slight elbow spring: closes a little at the chest, opens a little at the back,
        # so the hand whips through instead of the forearm staying rigid
        elbow_now = elbow + ARM_ELASTIC * c
        up_dir = Vector((lat * sgn,
                         -math.sin(math.radians(sw_ang)),
                         -math.cos(math.radians(sw_ang)))).normalized()
        aim("upperarm_%s" % side, up_dir, cache)
        rig.pose.bones["upperarm_%s" % side].keyframe_insert("rotation_quaternion", frame=f)

        fore_ang = sw_ang + elbow_now
        fore_dir = Vector((lat * sgn * 0.85,
                           -math.sin(math.radians(fore_ang)),
                           -math.cos(math.radians(fore_ang)))).normalized()
        aim("lowerarm_%s" % side, fore_dir, cache)
        rig.pose.bones["lowerarm_%s" % side].keyframe_insert("rotation_quaternion", frame=f)

    # ---- legs, solved analytically in world space then expressed as local rotations
    meas = {}
    for side in ("l", "r"):
        phase = u if side == "l" else u + 0.5
        y, z, pitch, planted = leg_state(phase)
        sx = 1.0 if side == "l" else -1.0
        H = Vector((0.0, 0.0, hip_z)) + R_pelvis @ Vector(
            (HIP_OFF.x * sx, HIP_OFF.y, HIP_OFF.z))
        A = Vector((ANKLE_X * sx, y, z))
        thigh_dir, shin_dir, K, A_eff = solve_leg(H, A, side)

        rest_thigh_dir = (REST_M["thigh_%s" % side].to_3x3()
                          @ Vector((0.0, 1.0, 0.0))).normalized()
        rest_shin_dir = (REST_M["shin_%s" % side].to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()

        R_arc_thigh = arc_to(rest_thigh_dir, thigh_dir)
        R_pose_thigh = R_arc_thigh @ REST_R["thigh_%s" % side]
        # internal rotation about the bone's own axis: the leg is modelled toe-out,
        # a hip + calf twist is what takes the splay out without breaking the ankle
        R_pose_thigh = Matrix.Rotation(math.radians(THIGH_TWIST) * sx, 3, thigh_dir) @ R_pose_thigh
        rb_thigh = (R_pelvis @ REST_R["thigh_%s" % side]).inverted() @ R_pose_thigh
        tb = rig.pose.bones["thigh_%s" % side]
        tb.rotation_quaternion = rb_thigh.to_quaternion()
        tb.keyframe_insert("rotation_quaternion", frame=f)

        R_arc_shin = arc_to(rest_shin_dir, shin_dir)
        R_pose_shin = R_arc_shin @ REST_R["shin_%s" % side]
        R_pose_shin = Matrix.Rotation(math.radians(SHIN_TWIST) * sx, 3, shin_dir) @ R_pose_shin
        rb_shin = (R_pose_thigh @ REST_R["thigh_%s" % side].inverted()
                   @ REST_R["shin_%s" % side]).inverted() @ R_pose_shin
        sb = rig.pose.bones["shin_%s" % side]
        sb.rotation_quaternion = rb_shin.to_quaternion()
        sb.keyframe_insert("rotation_quaternion", frame=f)

        R_pose_foot = (Matrix.Rotation(math.radians(FOOT_YAW[side]), 3, "Z")
                       @ Matrix.Rotation(math.radians(pitch), 3, "X")
                       @ REST_R["foot_%s" % side])
        rb_foot = (R_pose_shin @ REST_R["shin_%s" % side].inverted()
                   @ REST_R["foot_%s" % side]).inverted() @ R_pose_foot
        fb = rig.pose.bones["foot_%s" % side]
        fb.rotation_quaternion = rb_foot.to_quaternion()
        fb.keyframe_insert("rotation_quaternion", frame=f)

        bend = -pitch if (planted and pitch > 1.0) else 0.0
        tob = rig.pose.bones["toe_%s" % side]
        tob.rotation_quaternion = Quaternion((1, 0, 0), math.radians(bend))
        tob.keyframe_insert("rotation_quaternion", frame=f)

        meas[side] = {"H": H, "A": A, "A_eff": A_eff, "K": K,
                      "d": (A - H).length, "err": (A_eff - A).length}

    # ---- tail: lift it out behind and let it bounce with the stride. A tail that
    # hangs down between the legs is the single strongest "sneaking animal" cue.
    # Each segment trails the previous one by ~1 frame (lag 1/16 cycle), so the
    # wave travels down the chain instead of the whole tail swinging as one stick.
    for idx, (lift, wave) in enumerate(((32.0, -9.0), (20.0, -11.0), (9.0, -10.0), (-2.0, -8.0)),
                                       start=1):
        tb = rig.pose.bones["tail_%02d" % idx]
        tb.rotation_mode = "QUATERNION"
        lag = (idx - 1) / CYCLE
        tail_wave = math.cos(2.0 * math.pi * (u - lag))
        tb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(lift + wave * tail_wave))
        tb.keyframe_insert("rotation_quaternion", frame=f)

    rows.append({"f": f, "u": u, "hip": hip_z, "l": leg_state(u), "r": leg_state(u + 0.5),
                 "ld": meas["l"]["d"], "rd": meas["r"]["d"],
                 "lerr": meas["l"]["err"], "rerr": meas["r"]["err"],
                 "kz_l": meas["l"]["K"].z, "kz_r": meas["r"]["K"].z,
                 "ky_l": meas["l"]["K"].y, "ky_r": meas["r"]["K"].y})

from bpy_extras import anim_utils

slot = action.slots[0] if len(action.slots) else action.slots.new(id_type="OBJECT", name=rig.name)
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
for fc in channelbag.fcurves:
    for key in fc.keyframe_points:
        key.interpolation = "LINEAR"

print("\nRUN v=%.2f m/s  T=%.4f s  stride=+-%.3f m  stance sweep=%.3f m  torso lean=%.0f deg"
      % (SPEED, CYCLE / FPS, STRIDE, 2 * STRIDE, TORSO_LEAN))
print("%5s %5s %6s | %6s %5s %5s %5s | %6s %5s %5s %5s | %6s %6s"
      % ("frame", "u", "hipZ", "Ly", "Lz", "Lpitch", "Lreach", "Ry", "Rz", "Rpitch",
         "Rreach", "kneeL_z", "kneeR_z"))
for i, r in enumerate(rows):
    ly, lz, lp, pl = r["l"]
    ry, rz, rp, pr = r["r"]
    slide = ""
    if i:
        p = rows[i - 1]
        if p["l"][3] and pl:
            slide = "L%+.2f" % ((ly - p["l"][0]) * FPS)
        if p["r"][3] and pr:
            slide += " R%+.2f" % ((ry - p["r"][0]) * FPS)
    print("%5d %5.3f %6.3f | %6.3f %5.3f %5.1f %5.3f | %6.3f %5.3f %5.1f %5.3f | %6.3f %6.3f  %s"
          % (r["f"], r["u"], r["hip"], ly, lz, lp, r["ld"], ry, rz, rp, r["rd"],
             r["kz_l"], r["kz_r"], slide))
print("MAX reach %.3f of %.3f  MAX solve error %.5f"
      % (max(max(r["ld"], r["rd"]) for r in rows) / REACH,
         REACH, max(max(r["lerr"], r["rerr"]) for r in rows)))

# ------------------------------------------------------------------ check renders
cam_data = bpy.data.cameras.new("RUN_CAM")
cam = bpy.data.objects.new("RUN_CAM", cam_data)
scene.collection.objects.link(cam)
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.35
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_object_outline = False
scene.render.resolution_x = 620
scene.render.resolution_y = 820
scene.render.film_transparent = True

views = {
    "side": ((6.0, 0.0, 0.95), (90.0, 0.0, 90.0)),
    "front": ((0.0, -6.0, 0.95), (90.0, 0.0, 0.0)),
    "foot": ((-3.4, -4.6, 0.35), (78.0, 0.0, -36.0)),
}
for view, (loc, rot) in views.items():
    cam.location = loc
    cam.rotation_euler = tuple(math.radians(a) for a in rot)
    for f in (0, 2, 4, 6, 8, 10, 12, 14, 16):
        scene.frame_set(f)
        scene.render.filepath = "%s\\run6_%s_%02d.png" % (OUT, view, f)
        bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("RUN_ACTION_DONE")






