# 混元 3D 输入包（悟空）

用途：用腾讯混元 3D 的**多视角图生 3D**跑出带服装的完整形体，再由 Blender 端重拓扑成游戏资产。

## 1. 上传哪几张

混元 3D 网页版（3D生成 V3.1）的「添加多视图」弹窗，按下面填，其余留空：

| 弹窗里的槽位 | 上传文件 |
|---|---|
| **正图**（必填，带 `*`） | `front.png` |
| **左图** | `side.png`（角色左侧轮廓，画面朝左） |
| **背图** | `back.png` |

顶图 / 底图 / 左45° / 右45° / 右图 全部**留空**（最少 2 张即可，只填正图 + 背图也能跑）。

三张都是 2048×2048、纯白底、人物高 1800 px、脚底对齐，**同一个姿势**。

> 如果生成结果里尾巴/腰带方向反了，把 `side.png` 换到「右图」再跑一次即可。
>
> 只能单图生成时，改用 `tpose_front.png`（T-pose 正面），并换成下面的「单图版 prompt」。

## 2. Prompt（中文，推荐）

```
孙悟空，暗黑东方幻想风格，半写实游戏角色。A-pose 站立，双臂自然下垂，双手握拳。
白色交领道袍，青色斜襟与腰带，虎皮短裙，白色灯笼裤，黑色长靴带金色纹样，
金色紧箍，棕色猴毛，长尾。全身完整，白色背景，均匀平光，无投影，无武器，无场景。
写实 PBR 材质，干净的反照率贴图，无手绘笔触。
```

单图（T-pose）版：

```
孙悟空，暗黑东方幻想风格，半写实游戏角色。T-pose 站立，双臂水平伸展，双手张开。
白色交领道袍，青色斜襟与腰带，虎皮短裙，白色灯笼裤，黑色长靴带金色纹样，
金色紧箍，棕色猴毛，长尾。全身完整，白色背景，均匀平光，无投影，无武器，无场景。
写实 PBR 材质，干净的反照率贴图，无手绘笔触。
```

英文备用：

```
Sun Wukong, dark oriental fantasy, semi-realistic game character, A-pose with arms
relaxed at the sides and fists closed. White cross-collar robe with teal sash and belt,
tiger-skin skirt, white baggy pants, black boots with gold trim, golden headband,
brown fur, long tail. Full body, plain white background, flat even lighting, no shadows,
no weapon, no scene. Realistic PBR materials, clean albedo, no painterly brush strokes.
```

## 3. 参数建议（对应网页版选项）

| 网页选项 | 选什么 | 原因 |
|---|---|---|
| 单张 / 多张图片 | **多张图片** | 三视图一起喂，形体更准 |
| 模型 | 3D生成-V3.1 | 新版本几何更好 |
| 模型面数 | **500k** | 够重拓扑；1.5m/1m 太重，50k 细节不够 |
| 提示词（如果有输入框） | 用上面那段 | 网页版可能没有，没就不用填 |

API 里还有 `EnablePBR=true`、`KeepUV=true`、`Seed=20261020` 这几个参数，网页版如果没暴露就不用管。

## 4. 跑完把这些发我

1. **原始 `.glb`**（不要减面、不要压贴图，30 万面没关系）；
2. 贴图文件（BaseColor / Normal / Roughness / Metallic / AO，有什么给什么）；
3. 参数截图或 JSON（面数、Seed、PBR、KeepUV 是否开启）；
4. 正 / 侧 / 背 / 3-4 四张截图（或一段 turntable 视频）；
5. 你觉得明显不对的地方（例如尾巴方向、手指融合），标一句，我重拓扑时会重点修。

## 5. 我拿到之后做什么

1. 导入 → 统一到 1.895 m、+Z 上、-Y 朝前；
2. 正交三视图渲染，和你给的三视图叠图核对比例；
3. 重拓扑到 15–18k 面（游戏 LOD0），展 UV、烘法线；
4. 绑 Godot `SkeletonProfileHumanoid` 骨架 + `weapon_r` 挂点；
5. 水墨后处理在 Godot 里做，贴图保持写实。
