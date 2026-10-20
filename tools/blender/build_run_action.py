"""Build the Run cycle from KEY POSES -- redesign v15.

Why this is not another parameter pass on v14
--------------------------------------------
v14 drove every joint from one phase function and sampled it. Every channel was
smooth, and the result read as a crouched guard-hop: the legs never scissored (the
contact foot landed under the pelvis), the trailing leg never extended, and both
hands stayed at the chin. Nothing in it was *staged*: a run is not a waveform, it
is four poses per step hit on specific frames.

The tutorial (Chiara Porri / 动画手册, sohu 731528008) says exactly that:
  1. a step is contact / down / passing / up -- four key poses, blocked first,
     with the loop's start and end identical;
  2. spacing is not uniform: accelerate contact -> passing, decelerate up -> contact;
  3. the foot curve is Z-shaped -- linear while it is on the ground, eased in the
     air; toe up before contact, ball first, heel rolls up, toes point down on lift;
  4. legs may repeat, arms must vary: left and right arm bend and travel differ;
  5. check the arcs with a simplified body (silhouette), not by staring at textures.

So this builder blocks an 8-pose cycle (contact/down/pass/up x2) on a 16 frame
loop, two frames per pose, and derives the motion between poses from those poses.

What changed in the maths
-------------------------
* STANCE DRIVES THE BALL OF THE FOOT, NOT THE ANKLE. v14 moved the ankle at exactly
  4.2 m/s, so while the heel lifted the ball of the foot (the only point actually
  touching) ran ahead of the ground and the toe skated. Here the contact point moves
  back at exactly the run speed and the ankle is derived from it and the foot pitch:
      ankle_y = ball_y + BALL_DIST * cos(BALL_ANG + pitch)
      ankle_z = SOLE_Z  + BALL_DIST * sin(BALL_ANG + pitch)
  At pitch 0 that reproduces the rest ankle (z = 0.100) exactly.
* The hips run TALL (0.870 .. 0.940 against a 0.950 standing pelvis). v14 sat at
  0.856, which forces every knee to stay bent and photographs as a crouch. Tall
  hips + a longer stance give the straight contact leg and the long scissor.
* Legs are solved with the same closed-form two-bone solver (no evaluation reads,
  plain FK written out, bakes and exports unchanged).

Numbers (docs/量参考_跑步.md):  v = 4.20 m/s, 16 frames @ 24 fps = 0.6667 s,
180 steps/min, 1.40 m steps, stance 25% -> 0.700 m ball travel, no foot slide.

  blender -b --python tools/blender/build_run_action.py
  WK_NORENDER=1 blender -b --python tools/blender/build_run_action.py   # numbers only
"""
import math
import os

import bpy
from mathutils import Matrix, Quaternion, Vector

BLEND = r"D:\Workspace\games\WuKong\source\blend\wukong_rigged.blend"
OUT = r"D:\Workspace\games\WuKong\docs\renders"
RENDER = os.environ.get("WK_NORENDER") != "1"

# ---------------------------------------------------------------- timing
FPS = 24
CYCLE = 18                 # frames 0..18; frame 18 repeats frame 0
# v17: the stride was the complaint. The reach limit is what sets it: with a 0.82 m
# leg and the hip at ~0.86 the foot can only be ~0.32 m ahead / ~0.44 m behind, i.e.
# a 0.76 m ground sweep. The only way to a long, calm stride is to make the character
# cover fewer metres per second: at 4.20 m/s the sweep/speed ratio forces ~190 spm,
# which reads as a scurry no matter how the joints are posed. 3.40 m/s at 18 frames
# (160 spm, 1.275 m steps) is a jog a human that size actually runs.
STANCE = 0.30              # ball on the ground 30% of the cycle (was 25%)
SPEED = 3.40               # must equal RUN_SPEED in scripts/main.gd
SWEEP = SPEED * STANCE * CYCLE / FPS       # 0.765 m of ball travel = no slide

# ---------------------------------------------------------------- foot geometry
# BALL_ANG: the boot's sole is not flat under the foot bone -- at rest the lowest
# contact point sits 9.2 deg below the bone's forward axis (measured against the
# mesh: rest ankle z = 0.100, sole = 0.000).
SOLE_Z = 0.079
BALL_DIST = 0.1317
BALL_ANG = 9.2

# The contact point is biased forward: the run leans, so the COM sits ahead of the
# pelvis and the foot has to land in front of it.
BALL_FRONT = -0.425
BALL_BACK = BALL_FRONT + SWEEP

# Boot mesh is modelled 23.5 deg toe-out even though the foot bone points dead
# ahead; it is weighted 43% foot / 43% shin / 13% toe, so the correction has to be
# split over hip + calf + foot or the boot still reads pigeon-toed.
FOOT_YAW = {"l": -23.5, "r": 23.5}
# The split matters: the boot is 43% foot / 43% shin, so the shin's world twist moves
# the boot as much as the foot does. When the leg poses changed (v16) the landing
# boot went from 8.8 to 16.8 deg toe-out. Re-balancing to 10/17 only recovered ~1 deg
# (now 15.9): the leftover comes from the shin bone's own world yaw in this pose, not
# from this split. Known issue -- see docs/交接说明_跑步.md.
THIGH_TWIST = 10.0
SHIN_TWIST = 17.0

# Skinning compensation for the planted foot, sampled by stance progress. The boot is
# weighted 43% to the shin, so bending the knee drags the sole DOWN through the calf
# weights: measured with press = 0, the mesh sat -0.0 / -0.9 / -1.9 / -2.0 cm at
# q = 0 / .3 / .6 / .9. This table lifts the ankle by that much so the sole lands on
# the floor instead of 2 cm inside it. Re-measured with calibrate_run_lift.py.
LIFT_Q = [0.0, 0.30, 0.60, 0.90, 1.0]
LIFT_V = [0.000, 0.010, 0.019, 0.021, 0.021]

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
# purge helpers left behind by earlier builds: each run creates a camera + floor to
# render the check frames, and saving without removing them grew this file by one
# camera per build (60 of them were in here).
for _o in [o for o in bpy.data.objects
           if o.name.startswith("RUN_CAM") or o.name.startswith("RUN_FLOOR")]:
    bpy.data.objects.remove(_o, do_unlink=True)
scene.render.fps = FPS
scene.render.fps_base = 1.0
rig = bpy.data.objects["Wukong_Rig"]
bpy.context.view_layer.objects.active = rig

# The action is baked FK: mute the leg IK or it overrides every keyed pose.
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
THIGH_L = rig.data.bones["thigh_l"].length
SHIN_L = rig.data.bones["shin_l"].length
REACH = THIGH_L + SHIN_L
HIP_OFF = Vector((0.10, 0.0, -0.030))      # pelvis origin -> hip joint, rest
ANKLE_X = 0.095

old = bpy.data.actions.get("Run")
if old:
    bpy.data.actions.remove(old)
action = bpy.data.actions.new("Run")
action.use_fake_user = True
if not rig.animation_data:
    rig.animation_data_create()
rig.animation_data.action = action


# =================================================================== curves
def cr_periodic(vals, u):
    """Periodic Catmull-Rom through uniformly spaced samples (u in [0,1))."""
    n = len(vals)
    x = (u % 1.0) * n
    i = int(math.floor(x)) % n
    t = x - math.floor(x)
    p0, p1 = vals[(i - 1) % n], vals[i]
    p2, p3 = vals[(i + 1) % n], vals[(i + 2) % n]
    return 0.5 * ((2.0 * p1) + (-p0 + p2) * t
                  + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t
                  + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t * t * t)


def pchip(xs, ys):
    """Monotone cubic Hermite. Smooth arcs, no overshoot -- the foot path must not
    dip below the floor between keys the way a Catmull-Rom would."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0.0:
            m[i] = 0.0
        else:
            w1 = 2.0 * h[i] + h[i - 1]
            w2 = h[i] + 2.0 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = max(j for j in range(n - 1) if xs[j] <= x)
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1])
    return f


def lerp(a, b, t):
    return a + (b - a) * t


def ph(u, lag_frames):
    """Phase shifted back by lag_frames (chain overlap: each link trails its parent)."""
    return (u - lag_frames / CYCLE) % 1.0


def arc_to(a, b):
    a, b = a.normalized(), b.normalized()
    d = max(-1.0, min(1.0, a.dot(b)))
    if d > 0.999999:
        return Matrix.Identity(3)
    if d < -0.999999:
        return Matrix.Rotation(math.pi, 3, a.orthogonal().normalized())
    return Matrix.Rotation(math.acos(d), 3, a.cross(b).normalized())


def bone_world_rot(name, cache):
    """Armature-space rotation composed by hand: reading pose matrices in a
    background build returns stale values, so the chain is rebuilt from the basis
    quaternions written this frame."""
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
    """Point a bone's +Y at a world direction (minimum twist), store as local basis.
    The A-pose arm points 40 deg out, so swinging it about a 'local' world axis
    sweeps a cone -- 43% of the hand travel went sideways in v13. Aiming the bone
    at a direction that lives in the sagittal plane fixes the plane itself."""
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


def solve_leg(H, A):
    """Closed-form two-bone solve, knee in the sagittal plane. Returns dirs + knee."""
    d = A - H
    L = min(d.length, 0.995 * REACH)
    w = (d.normalized() if d.length > 1e-6 else Vector((0.0, 0.0, -1.0)))
    a = (THIGH_L ** 2 - SHIN_L ** 2 + L * L) / (2.0 * L)
    h = math.sqrt(max(THIGH_L ** 2 - a * a, 0.0))
    fwd = Vector((0.0, -1.0, 0.0))
    m = fwd - w * fwd.dot(w)
    if m.length < 1e-5:
        m = Vector((0.0, 0.0, 1.0)) - w * Vector((0.0, 0.0, 1.0)).dot(w)
    m.normalize()
    K = H + w * a + m * h
    return (K - H).normalized(), (H + w * L - K).normalized(), K, H + w * L


# =================================================================== leg path
# Foot pitch over stance, as a fraction of stance. Positive = toe down (ball first).
# 12 at contact (ball touches, heel 12 deg up) -> 0 (flat, weight over the foot) ->
# 34 at toe-off (full plantar flexion). The tutorial's "heel rolls up, ball leaves
# last" is this ramp; press/lift are skinning compensation, not animation.
STANCE_PITCH = pchip([0.0, 0.18, 0.42, 0.62, 0.80, 1.0],
                     [12.0, 7.0, 1.0, 6.0, 18.0, 34.0])

SKIN_LIFT = pchip(LIFT_Q, LIFT_V)


def ball_to_ankle(ball_y, pitch_deg, extra_z=0.0):
    ang = math.radians(BALL_ANG + pitch_deg)
    return (ball_y + BALL_DIST * math.cos(ang),
            SOLE_Z + BALL_DIST * math.sin(ang) + extra_z)


# The swing path must START and END exactly on the stance path or the foot jumps at
# the seam, so both ends are computed from the same ball geometry instead of typed in.
A_OFF = ball_to_ankle(BALL_BACK, STANCE_PITCH(1.0), SKIN_LIFT(1.0))    # just left floor
A_ON = ball_to_ankle(BALL_FRONT, STANCE_PITCH(0.0), SKIN_LIFT(0.0))    # just landed

# SWING keys: (swing phase 0..1, ankle y, ankle z, foot pitch)
# Rebuilt against the reference sketch. Two rules from it:
#   * the trailing leg must still be BEHIND and LOW when the other foot lands -- the
#     v15 path had it folded up under the hips by then, which is what made every
#     contact frame read as bunched instead of as a wide stride;
#   * the swing foot hangs BELOW the knee (peak ~0.38 m); it must not be tucked up
#     against the seat, which reads as skipping rather than running.
SWING_KEYS = [
    (0.00, A_OFF[0], A_OFF[1], 34.0),   # toe-off
    (0.10, 0.440, 0.235, 40.0),         # leg keeps travelling back after lift-off
    (0.22, 0.460, 0.285, 48.0),         # farthest behind, still LOW -- the wide "A"
    (0.29, 0.420, 0.300, 46.0),         # other foot lands here: rear leg still open
    (0.40, 0.300, 0.380, 40.0),         # knee starts to drive through
    (0.52, 0.100, 0.430, 18.0),         # knee up, foot hanging below it
    (0.62, -0.120, 0.390, 0.0),         # peak knee lift: shin hangs, foot under knee
    (0.72, -0.280, 0.370, -8.0),        # shin opens forward
    (0.82, -0.360, 0.290, -12.0),       # furthest reach, toes up
    (0.91, -0.330, 0.200, -6.0),        # paw back into contact
    (1.00, A_ON[0], A_ON[1], 12.0),     # contact
]
SW_Y = pchip([k[0] for k in SWING_KEYS], [k[1] for k in SWING_KEYS])
SW_Z = pchip([k[0] for k in SWING_KEYS], [k[2] for k in SWING_KEYS])
SW_P = pchip([k[0] for k in SWING_KEYS], [k[3] for k in SWING_KEYS])


def leg_state(u):
    """(ankle y, ankle z, foot pitch, planted) for one leg at cycle phase u."""
    u %= 1.0
    if u <= STANCE:
        q = u / STANCE
        pitch = STANCE_PITCH(q)
        ball_y = lerp(BALL_FRONT, BALL_BACK, q)
        ay, az = ball_to_ankle(ball_y, pitch, SKIN_LIFT(q))
        return ay, az, pitch, True
    s = (u - STANCE) / (1.0 - STANCE)
    return SW_Y(s), SW_Z(s), SW_P(s), False


# =================================================================== body poses
# Eight poses, one every two frames: contact / down / pass / up, then mirrored.
# All angles in degrees.
# LEAN: the reference sketch is an upright run (torso maybe 15 deg), not a sprint
# crouch. At 31 deg the chest sits ahead of the hips, the skirt swallows the thighs
# and the whole figure reads as hunched no matter what the limbs do.
LEAN_PELVIS, LEAN_01, LEAN_02, LEAN_CHEST = 14.0, 2.0, 1.0, 0.0
TORSO_LEAN = LEAN_PELVIS + LEAN_01 + LEAN_02 + LEAN_CHEST

# Pelvis yaw: leading leg forward at contact. RotZ(-) sends the left hip forward,
# which is why the left contact pose is -9 and the right contact pose is +9.
PELVIS_YAW = [-9.0, -6.0, -1.0, 5.0, 9.0, 6.0, 1.0, -5.0]
# Hip drop: weight on the left lifts the left hip (roll about the forward axis).
PELVIS_ROLL = [-1.6, -3.4, -2.2, 0.6, 1.6, 3.4, 2.2, -0.6]
# Chest opens at contact and compresses into the down pose (tutorial steps 9-10).
CHEST_PITCH = [-2.5, 1.5, -1.8, -1.0, -2.5, 1.5, -1.8, -1.0]

# Pelvis height, one value PER FRAME (this is the spacing channel). The apex dwells
# for two frames -- the tutorial's "decelerate between the top and the next contact".
# 18 frames: f0 contact .. f9 the other contact, f10..f17 mirror f1..f8.
PELVIS_Z = [0.885, 0.868, 0.858, 0.860, 0.872, 0.890, 0.908, 0.920, 0.915,
            0.885, 0.868, 0.858, 0.860, 0.872, 0.890, 0.908, 0.920, 0.915]

# Arms. Left hand pumps, right hand carries the staff and travels less -- the
# tutorial's "legs can repeat, arms must vary". c = +1 is this arm's front extreme.
#
# PHASE: the front extreme sits on the CONTACT of the opposite foot (tutorial's
# 对侧原则). Left arm forward at u=0.5 (right foot strikes), back at u=0.0 (left foot
# strikes). The first pass used 0.35/0.85, which left both fists parked in front of
# the chest on every contact frame -- the pose read as a boxing guard, not a run.
# elbow_amp is POSITIVE: the elbow folds at the front and opens at the back.
ARM_L = {"bias": -2.0, "amp": 50.0, "elbow": 60.0, "elbow_amp": 38.0, "lat": 0.24}
# The staff hand CARRIES: it swings less than the free arm, otherwise a 1.4 m staff
# sweeps across the face every half cycle -- but it still swings, because a dead arm
# on one side is the thing that read as broken.
# lat: sideways component of the aim direction. 0.16 hung the arms against the robe
# -- the front view showed the fists parked on the belt and the swing "eaten by the
# clothes", which is the exact run cue docs/动作设计.md §9.4 says to avoid.
ARM_R = {"bias": 0.0, "amp": 15.0, "elbow": 52.0, "elbow_amp": 14.0, "lat": 0.28}
ARM_PEAK_L, ARM_PEAK_R = 0.50, 0.00       # phase of the front extreme
# Chain overlap: frames of delay behind the link that drives it.
LAG_SPINE_01, LAG_SPINE_02, LAG_CHEST = 0.5, 1.0, 1.5
LAG_CLAV, LAG_ARM, LAG_HEAD = 1.5, 0.5, 2.5
LAG_TAIL = 1.0

TAIL = [(26.0, 9.0), (18.0, 10.0), (10.0, 9.0), (2.0, 7.0)]   # (lift, wave deg)


def pelvis_z(u):
    x = (u % 1.0) * CYCLE
    i = int(math.floor(x)) % CYCLE
    t = x - math.floor(x)
    p0, p1 = PELVIS_Z[(i - 1) % CYCLE], PELVIS_Z[i]
    p2, p3 = PELVIS_Z[(i + 1) % CYCLE], PELVIS_Z[(i + 2) % CYCLE]
    return 0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t
                  + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t * t * t)


def lean_breath(u):
    """Torso works hardest just after toe-off and stands up through the flight."""
    return 1.0 + 0.07 * math.cos(2.0 * math.pi * (u - 0.30))


# =================================================================== bake
frames = list(range(0, CYCLE + 1))
rows = []

for f in frames:
    u = f / CYCLE
    scene.frame_set(f)

    hip_z = pelvis_z(u)
    yaw = math.radians(cr_periodic(PELVIS_YAW, u))
    roll = math.radians(cr_periodic(PELVIS_ROLL, u))
    breathe = lean_breath(u)
    lean_p = math.radians(LEAN_PELVIS * breathe)

    R_pelvis = (Matrix.Rotation(lean_p, 3, "X")
                @ Matrix.Rotation(roll, 3, "Y")
                @ Matrix.Rotation(yaw, 3, "Z"))
    pelvis_desired = (Matrix.Translation(Vector((0.0, 0.0, hip_z)))
                      @ (R_pelvis @ REST_R["pelvis"]).to_4x4())
    basis = REST_M["pelvis"].inverted() @ pelvis_desired
    loc, rot, _ = basis.decompose()
    pb = rig.pose.bones["pelvis"]
    pb.location = loc
    pb.rotation_quaternion = rot
    pb.keyframe_insert("location", frame=f)
    pb.keyframe_insert("rotation_quaternion", frame=f)

    # ---- spine: each link trails the one below by half a frame to a frame and a
    # half, and the shoulder girdle COUNTER-rotates the pelvis (it co-rotated in v6,
    # which is why the whole torso read as one rigid block).
    prev_yaw = yaw
    for name, lean, frac, lag in (("spine_01", LEAN_01, 0.55, LAG_SPINE_01),
                                   ("spine_02", LEAN_02, 0.30, LAG_SPINE_02),
                                   ("chest", LEAN_CHEST, -0.45, LAG_CHEST)):
        ul = ph(u, lag)
        target = frac * math.radians(cr_periodic(PELVIS_YAW, ul))
        local_yaw = target - prev_yaw
        prev_yaw = target
        pitch = lean * breathe + (cr_periodic(CHEST_PITCH, ul) if name == "chest" else 0.0)
        pb = rig.pose.bones[name]
        pb.rotation_quaternion = (Quaternion((1, 0, 0), math.radians(pitch))
                                  @ Quaternion((0, 1, 0), local_yaw))
        pb.keyframe_insert("rotation_quaternion", frame=f)

    # ---- neck + head: cancel part of the lean so he looks where he runs, and run
    # 2.5 frames behind the chest. Less cancellation now that the torso is upright --
    # the old -0.45/-0.30 was sized for a 31 deg lean and tips the chin up here.
    ul = ph(u, LAG_HEAD)
    head_yaw = -0.10 * math.radians(cr_periodic(PELVIS_YAW, ul))
    for name, k, pitch_k in (("neck", 0.6, -0.30), ("head", 0.4, -0.20)):
        pb = rig.pose.bones[name]
        pb.rotation_quaternion = (Quaternion((1, 0, 0), math.radians(TORSO_LEAN * breathe) * pitch_k)
                                  @ Quaternion((0, 1, 0), head_yaw * k))
        pb.keyframe_insert("rotation_quaternion", frame=f)

    # ---- arms
    cache = {}
    hands = {}
    for side, spec, peak in (("l", ARM_L, ARM_PEAK_L), ("r", ARM_R, ARM_PEAK_R)):
        s = 1.0 if side == "l" else -1.0
        c = math.cos(2.0 * math.pi * (ph(u, LAG_ARM) - peak))
        swing = spec["bias"] + spec["amp"] * c
        elbow = spec["elbow"] + spec["elbow_amp"] * c

        # clavicle: protract with the swing (the old +9 deg retraction was what made
        # the shoulders read hunched from the follow camera)
        cb = rig.pose.bones["clavicle_%s" % side]
        cax = (REST_R["clavicle_%s" % side].inverted() @ Vector((0.0, 0.0, 1.0))).normalized()
        cb.rotation_quaternion = Quaternion(cax, math.radians(-5.0 * c))
        cb.keyframe_insert("rotation_quaternion", frame=f)

        up_dir = Vector((spec["lat"] * s,
                         -math.sin(math.radians(swing)),
                         -math.cos(math.radians(swing)))).normalized()
        aim("upperarm_%s" % side, up_dir, cache)
        rig.pose.bones["upperarm_%s" % side].keyframe_insert("rotation_quaternion", frame=f)

        fore_ang = swing + elbow
        fore_dir = Vector((spec["lat"] * s * 0.80,
                           -math.sin(math.radians(fore_ang)),
                           -math.cos(math.radians(fore_ang)))).normalized()
        aim("lowerarm_%s" % side, fore_dir, cache)
        rig.pose.bones["lowerarm_%s" % side].keyframe_insert("rotation_quaternion", frame=f)
        hands[side] = (c, swing, elbow)

    # ---- legs
    meas = {}
    for side in ("l", "r"):
        phase = u if side == "l" else u + 0.5
        ay, az, pitch, planted = leg_state(phase)
        sx = 1.0 if side == "l" else -1.0
        H = Vector((0.0, 0.0, hip_z)) + R_pelvis @ Vector((HIP_OFF.x * sx, HIP_OFF.y, HIP_OFF.z))
        A = Vector((ANKLE_X * sx, ay, az))
        thigh_dir, shin_dir, K, A_eff = solve_leg(H, A)

        rest_thigh = (REST_R["thigh_%s" % side] @ Vector((0.0, 1.0, 0.0))).normalized()
        rest_shin = (REST_R["shin_%s" % side] @ Vector((0.0, 1.0, 0.0))).normalized()

        R_thigh = arc_to(rest_thigh, thigh_dir) @ REST_R["thigh_%s" % side]
        R_thigh = Matrix.Rotation(math.radians(THIGH_TWIST) * sx, 3, thigh_dir) @ R_thigh
        tb = rig.pose.bones["thigh_%s" % side]
        tb.rotation_quaternion = ((R_pelvis @ REST_R["thigh_%s" % side]).inverted()
                                  @ R_thigh).to_quaternion()
        tb.keyframe_insert("rotation_quaternion", frame=f)

        R_shin = arc_to(rest_shin, shin_dir) @ REST_R["shin_%s" % side]
        R_shin = Matrix.Rotation(math.radians(SHIN_TWIST) * sx, 3, shin_dir) @ R_shin
        sb = rig.pose.bones["shin_%s" % side]
        sb.rotation_quaternion = ((R_thigh @ REST_R["thigh_%s" % side].inverted()
                                   @ REST_R["shin_%s" % side]).inverted()
                                  @ R_shin).to_quaternion()
        sb.keyframe_insert("rotation_quaternion", frame=f)

        R_foot = (Matrix.Rotation(math.radians(FOOT_YAW[side]), 3, "Z")
                  @ Matrix.Rotation(math.radians(pitch), 3, "X")
                  @ REST_R["foot_%s" % side])
        fb = rig.pose.bones["foot_%s" % side]
        fb.rotation_quaternion = ((R_shin @ REST_R["shin_%s" % side].inverted()
                                   @ REST_R["foot_%s" % side]).inverted()
                                  @ R_foot).to_quaternion()
        fb.keyframe_insert("rotation_quaternion", frame=f)

        # toes: only the metatarsal bends, and only while the ball is planted
        bend = -0.85 * pitch if (planted and pitch > 1.0) else 0.0
        tob = rig.pose.bones["toe_%s" % side]
        tob.rotation_quaternion = Quaternion((1, 0, 0), math.radians(bend))
        tob.keyframe_insert("rotation_quaternion", frame=f)

        # knee angle from the solved triangle (interior angle, 180 = straight)
        knee = math.degrees(math.acos(max(-1.0, min(1.0,
            (THIGH_L ** 2 + SHIN_L ** 2 - (A_eff - H).length ** 2)
            / (2.0 * THIGH_L * SHIN_L)))))
        meas[side] = dict(knee=knee, ext=(A_eff - H).length / REACH, pitch=pitch,
                          planted=planted, ankle_z=az)

    # ---- tail: each segment trails the previous one by a frame so the wave
    # travels down the chain instead of the whole tail swinging as one stick.
    for idx, (lift, wave) in enumerate(TAIL, start=1):
        ul = ph(u, (idx - 1) * LAG_TAIL)
        tb = rig.pose.bones["tail_%02d" % idx]
        sw = math.cos(2.0 * math.pi * (ul - 0.25))
        tb.rotation_quaternion = (Quaternion((1, 0, 0), math.radians(lift + wave * sw))
                                  @ Quaternion((0, 0, 1), math.radians(4.0 * sw)))
        tb.keyframe_insert("rotation_quaternion", frame=f)

    rows.append(dict(f=f, u=u, hip=hip_z, l=leg_state(u), r=leg_state(u + 0.5),
                     kl=meas["l"]["knee"], kr=meas["r"]["knee"],
                     el=meas["l"]["ext"], er=meas["r"]["ext"],
                     armL=hands["l"][1], armR=hands["r"][1]))

# ------------------------------------------------------------------ bake sanity
from bpy_extras import anim_utils

slot = action.slots[0] if len(action.slots) else action.slots.new(id_type="OBJECT", name=rig.name)
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
for fc in channelbag.fcurves:
    for key in fc.keyframe_points:
        key.interpolation = "LINEAR"

print("\nRUN v=%.2f m/s  T=%.4f s  cycle=%d  stance=%.0f%%  ball sweep=%.3f m  lean=%.0f deg"
      % (SPEED, CYCLE / FPS, CYCLE, STANCE * 100, SWEEP, TORSO_LEAN))
print("poses: contact f0 / down f2 / pass f4 / up f6 (step = 8 frames)")
print("%3s %7s | %7s | %7s %7s %6s %6s | %7s %6s | %5s %5s"
      % ("f", "pose", "hipZ", "ankL_y", "ankL_z", "kneeL", "extL",
         "ankR_z", "kneeR", "armL", "armR"))
POSENAME = {0: "CONTACT", 2: "down", 5: "pass", 7: "UP", 9: "contact", 11: "down",
            14: "pass", 16: "up"}
for r in rows:
    fy, fz = r["l"][0], r["l"][1]
    rz = r["r"][1]
    print("%3d %7s | %7.3f | %7.3f %7.3f %6.1f %6.3f | %7.3f %6.1f | %5.1f %5.1f"
          % (r["f"], POSENAME.get(r["f"], ""), r["hip"], fy, fz,
             r["kl"], r["el"], rz, r["kr"], r["armL"], r["armR"]))

max_ext = max(max(r["el"], r["er"]) for r in rows)
print("MAX extension %.3f (limit 0.995)   contact knee %.1f   min knee %.1f"
      % (max_ext, rows[0]["kl"], min(min(r["kl"], r["kr"]) for r in rows)))

# =================================================================== renders
if RENDER:
    # ground: a thin slab, not a plane -- edge-on planes vanish in an ortho side view
    floor = bpy.data.meshes.new("RUN_FLOOR")
    floor.from_pydata(
        [(-4, -4, -0.03), (4, -4, -0.03), (4, 4, -0.03), (-4, 4, -0.03),
         (-4, -4, 0.0), (4, -4, 0.0), (4, 4, 0.0), (-4, 4, 0.0)], [],
        [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7)])
    floor.update()
    fobj = bpy.data.objects.new("RUN_FLOOR", floor)
    fmat = bpy.data.materials.new("RUN_FLOOR_MAT")
    fmat.diffuse_color = (0.30, 0.30, 0.33, 1.0)
    floor.materials.append(fmat)
    scene.collection.objects.link(fobj)

    cam_data = bpy.data.cameras.new("RUN_CAM")
    cam = bpy.data.objects.new("RUN_CAM", cam_data)
    scene.collection.objects.link(cam)
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.30
    scene.camera = cam
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.show_object_outline = False
    scene.render.resolution_x = 560
    scene.render.resolution_y = 760
    scene.render.film_transparent = True

    VIEWS = {"side": ((-6.0, 0.0, 0.95), (90.0, 0.0, -90.0)),
             "front": ((0.0, -6.0, 0.95), (90.0, 0.0, 0.0))}
    for view, (loc, rot) in VIEWS.items():
        cam.location = loc
        cam.rotation_euler = tuple(math.radians(a) for a in rot)
        for f in (0, 2, 4, 6, 8, 10, 12, 14, 16, 18):
            scene.frame_set(f)
            scene.render.filepath = "%s\\run15_%s_%02d.png" % (OUT, view, f)
            bpy.ops.render.render(write_still=True)

    # tutorial step: judge the arcs on a simplified body -- flat black silhouette on
    # white. A dark silhouette on a dark sheet (the first attempt) shows nothing.
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "SINGLE"
    scene.display.shading.single_color = (0.02, 0.02, 0.02)
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (1.0, 1.0, 1.0)
    scene.render.film_transparent = False
    scene.render.resolution_x = 460
    scene.render.resolution_y = 640
    fobj.hide_render = True
    cam.location = (-6.0, 0.0, 0.95)
    cam.rotation_euler = (math.radians(90), 0.0, math.radians(-90))
    for f in (0, 2, 4, 6, 8, 10, 12, 14, 16):
        scene.frame_set(f)
        scene.render.filepath = "%s\\run15_sil_%02d.png" % (OUT, f)
        bpy.ops.render.render(write_still=True)

    # do not save the check camera / floor into the source blend
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.objects.remove(fobj, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("RUN_ACTION_DONE")
