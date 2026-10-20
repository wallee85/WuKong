"""一键把 Run 动作变成"可以手动摆姿势"的状态（只改数据结构，不改姿势）。

**只跑一次。** 之后再跑，会把你手动加在中间帧上的关键帧删掉。

用法（详细步骤见 docs/教程_自己改跑步.md）：
  1. 用 Blender 打开 source/blend/wukong_rigged.blend
  2. 顶部工作区 -> 脚本(Scripting) -> 文本编辑器「打开」本文件 -> ▶ 运行脚本

它做的事：
  1. 备份整个 .blend 到 source/blend/backups/
  2. 把 Run 里"每帧都有"的关键帧抽稀成 9 个姿势帧
     (0 2 5 7 9 11 14 16 18)，姿势帧上的数值一个都不改
  3. 补回"承重腿"在少数中间帧上的键 —— 少了这些键，鞋底会陷进地面 3 cm
  4. 时间轴范围设成 0..17，空格播放就是无缝循环
  5. 打开"骨架穿透显示"（In Front），让你隔着衣服也能点到骨头
  6. 保存，选中骨架、切进 Pose Mode、停在 f0
"""

import datetime
import os

import bpy
from bpy_extras import anim_utils

POSE_FRAMES = [0, 2, 5, 7, 9, 11, 14, 16, 18]
FRAMES = list(range(0, 19))
RIG_NAME = "Wukong_Rig"
BODY_NAME = "Wukong_LOD0"
ACTION_NAME = "Run"
SOLE_TOL = -0.008          # 鞋底低于地面这么多就算"陷进去了"
LEG_ROOTS = ('pose.bones["thigh_', 'pose.bones["shin_',
             'pose.bones["foot_', 'pose.bones["toe_')


def log(msg):
    print("[setup] %s" % msg)


def side_of(path):
    for s in ("l", "r"):
        if ('bone_%s"' % s) in path or ('_%s"].' % s) in path:
            return s
    return None


if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")

rig = bpy.data.objects.get(RIG_NAME)
body = bpy.data.objects.get(BODY_NAME)
act = bpy.data.actions.get(ACTION_NAME)
src = bpy.data.filepath
assert src, "先把 wukong_rigged.blend 打开再跑这个脚本"
assert rig is not None, "这个文件里没有 %s（你打开的是对的 .blend 吗）" % RIG_NAME
assert body is not None, "这个文件里没有 %s" % BODY_NAME
assert act is not None, "这个文件里没有叫 %s 的动作" % ACTION_NAME

sc = bpy.context.scene
slot = act.slots[0] if len(act.slots) else act.slots.new(id_type="OBJECT", name=rig.name)
cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)
curves = {(fc.data_path, fc.array_index): fc for fc in cb.fcurves}


def is_thin(fc):
    keys = list(fc.keyframe_points)
    return len(keys) == len(POSE_FRAMES) and all(
        round(k.co.x) in POSE_FRAMES for k in keys)


def evaluate_sole(minz):
    """Lowest mesh point + which foot is the planted one, at the current frame."""
    dg = bpy.context.evaluated_depsgraph_get()
    evb = body.evaluated_get(dg)
    me = evb.to_mesh()
    mw = body.matrix_world
    z = min((mw @ v.co).z for v in me.vertices)
    evb.to_mesh_clear()
    ev = rig.evaluated_get(dg)
    feet = {s: (rig.matrix_world @ ev.pose.bones["foot_%s" % s].head).z for s in "lr"}
    return z, min(feet, key=feet.get)


# ------------------------------------------------------------------ snapshot
# values of every channel on every frame, before anything is thrown away
snapshot = {}
sole_before = {}
for fc in cb.fcurves:
    snapshot[(fc.data_path, fc.array_index)] = {
        f: fc.evaluate(float(f)) for f in FRAMES}
for f in FRAMES:
    sc.frame_set(f)
    sole_before[f] = evaluate_sole(0)[0]

needs_thin = [fc for fc in cb.fcurves if not is_thin(fc)]
log("原始：每条通道 %d 个键；需要抽稀的通道 %d 条"
    % (len(list(cb.fcurves[0].keyframe_points)), len(needs_thin)))

if needs_thin:
    # ------------------------------------------------------------- 1. backup
    backup_dir = os.path.join(os.path.dirname(src), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(backup_dir, "wukong_rigged_%s.blend" % stamp)
    bpy.ops.wm.save_as_mainfile(filepath=backup, copy=True)
    log("备份 -> %s (%.1f MB)" % (backup, os.path.getsize(backup) / 1e6))

    # ------------------------------------------------------------- 2. thin
    before = sum(len(fc.keyframe_points) for fc in cb.fcurves)
    for fc in needs_thin:
        keep = [(k.co.x, k.co.y) for k in fc.keyframe_points
                if round(k.co.x) in POSE_FRAMES]
        fc.keyframe_points.clear()
        for x, y in keep:
            fc.keyframe_points.insert(x, y, options={"FAST"})
        fc.keyframe_points.sort()
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"
            k.handle_left_type = "AUTO_CLAMPED"
            k.handle_right_type = "AUTO_CLAMPED"
        fc.update()
    after = sum(len(fc.keyframe_points) for fc in cb.fcurves)
    log("抽稀：关键帧 %d -> %d" % (before, after))

    # --------------------------------------- 3. put the planted foot back on
    # the floor. Nine poses are not enough to describe the stance path: the
    # rolling boot cuts through the ground by up to 3.5 cm. Re-key the
    # supporting leg (only) on the frames where that happens.
    fixed = set()
    for attempt in ("planted", "both"):
        bad = {}
        for f in FRAMES:
            if f in POSE_FRAMES:
                continue
            sc.frame_set(f)
            z, planted = evaluate_sole(0)
            if z < SOLE_TOL:
                bad[f] = planted
        if not bad:
            break
        log("补键（第 %d 轮，%s）：%s" % (attempt == "planted" and 1 or 2,
                                        attempt, sorted(bad)))
        for f, planted in bad.items():
            sides = (planted,) if attempt == "planted" else ("l", "r")
            for fc in cb.fcurves:
                if not fc.data_path.startswith(LEG_ROOTS):
                    continue
                if attempt == "planted" and side_of(fc.data_path) not in sides:
                    continue
                fc.keyframe_points.insert(
                    float(f), snapshot[(fc.data_path, fc.array_index)][f])
                fc.keyframe_points.sort()
                for k in fc.keyframe_points:
                    k.interpolation = "BEZIER"
                    k.handle_left_type = "AUTO_CLAMPED"
                    k.handle_right_type = "AUTO_CLAMPED"
                fc.update()
            fixed.add(f)

    worst = 0.0
    for f in FRAMES:
        sc.frame_set(f)
        worst = min(worst, evaluate_sole(0)[0])
    log("补了 %d 个中间帧；现在最低鞋底 %.4f m（原来 %.4f m）"
        % (len(fixed), worst, min(sole_before.values())))

# ------------------------------------------------------------------ 4. range
sc.frame_start = 0
sc.frame_end = 17          # f18 是 f0 的复制，预览时跳过它
sc.frame_set(0)

# ------------------------------------------------------------------ 5. display
rig.show_in_front = True
rig.data.display_type = "OCTAHEDRAL"
rig.data.show_names = False

# ------------------------------------------------------------------ 6. save
bpy.ops.wm.save_mainfile()
log("已保存到 %s" % src)

# ------------------------------------------------------------------ 7. select & pose mode
for ob in bpy.context.view_layer.objects:
    ob.select_set(False)
rig.hide_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")

log("完成：现在停在 f0，可以开始摆姿势了（改完记得 Ctrl+S 再导出）")
print("SETUP_OK")
