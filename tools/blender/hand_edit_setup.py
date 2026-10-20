"""一键把 Run 动作变成"可以手动摆姿势"的状态（只改数据结构，不改姿势）。

用之前请先关掉 Godot 编辑器里正在看的东西，然后在 Blender 里
  Scripting 工作区 -> Open -> 选这个文件 -> Run Script

它做的事（每一步都可回退，会先在 source/blend/backups/ 里存一份完整副本）：
  1. 备份整个 .blend
  2. 把 Run 动作里"每帧都有"的关键帧抽稀成 9 个姿势帧
     (0 2 5 7 9 11 14 16 18)，姿势帧上的数值一个都不改
  3. 时间轴范围设成 0..17，空格播放就是无缝循环
  4. 打开"骨架穿透显示"（In Front），让你隔着衣服也能点到骨头
  5. 选中骨架、切进 Pose Mode、停在 f0
"""

import datetime
import os

import bpy
from bpy_extras import anim_utils

POSE_FRAMES = [0, 2, 5, 7, 9, 11, 14, 16, 18]
RIG_NAME = "Wukong_Rig"
ACTION_NAME = "Run"


def log(msg):
    print("[setup] %s" % msg)


bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None

rig = bpy.data.objects[RIG_NAME]
act = bpy.data.actions[ACTION_NAME]
src = bpy.data.filepath
assert src, "先把 wukong_rigged.blend 打开再跑这个脚本"

# ------------------------------------------------------------------ 1. backup
backup_dir = os.path.join(os.path.dirname(src), "backups")
os.makedirs(backup_dir, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = os.path.join(backup_dir, "wukong_rigged_%s.blend" % stamp)
bpy.ops.wm.save_as_mainfile(filepath=backup, copy=True)
log("备份 -> %s (%.1f MB)" % (backup, os.path.getsize(backup) / 1e6))

# ------------------------------------------------------------------ 2. thin
slot = act.slots[0] if len(act.slots) else act.slots.new(id_type="OBJECT", name=rig.name)
cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)

before = after = 0
changed = 0
for fc in cb.fcurves:
    keys = list(fc.keyframe_points)
    before += len(keys)
    if len(keys) == len(POSE_FRAMES) and all(
            round(k.co.x) in POSE_FRAMES for k in keys):
        after += len(keys)
        continue
    # keep the value of every pose frame, drop the rest
    keep = [(k.co.x, k.co.y) for k in keys if round(k.co.x) in POSE_FRAMES]
    fc.keyframe_points.clear()
    for x, y in keep:
        fc.keyframe_points.insert(x, y, options={"FAST"})
    fc.keyframe_points.sort()
    fc.update()
    after += len(keep)
    changed += 1

log("关键帧 %d -> %d（改动 %d 条曲线，共 %d 条）" % (before, after, changed, len(cb.fcurves)))

# ------------------------------------------------------------------ 3. range
sc = bpy.context.scene
sc.frame_start = 0
sc.frame_end = 17          # f18 是 f0 的复制，预览时跳过它
sc.frame_set(0)

# ------------------------------------------------------------------ 4. display
rig.show_in_front = True
rig.data.display_type = "OCTAHEDRAL"
rig.data.show_names = False

# ------------------------------------------------------------------ 5. save
bpy.ops.wm.save_mainfile()
log("已保存到 %s" % src)

# ------------------------------------------------------------------ 6. select & pose mode
for ob in bpy.context.view_layer.objects:
    ob.select_set(False)
rig.hide_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")

log("完成：现在停在 f0，可以开始摆姿势了（改完记得 Ctrl+S 再导出）")
print("SETUP_OK")
