# WuKong

Godot 4.7 项目：用 AI 图生 3D 打底、Blender 清理绑定的悟空角色。

## 运行

- 编辑器：用 Godot 4.7 打开本目录，按 **F5**
- 命令行：
  ```powershell
  & "C:\Users\jianxin\Downloads\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe" --path "D:\Workspace\games\WuKong"
  ```
- **WASD** 移动（跑步，第三人称跟随镜头）；**鼠标左键拖动** 转镜头、滚轮缩放；**鼠标右键** 点地面让角色转向该方向；**J** 三连击（范围伤害）；**I** 开/关水墨后处理

## 目录

| 路径 | 内容 |
|---|---|
| `scenes/main.tscn` | 主场景：环境、灯光、地面、相机、角色、水墨后处理层 |
| `scripts/main.gd` | 状态机（idle 程序化 / run 播烘焙动画 / 三连击）、追尾相机、水墨开关、持棍朝向 |
| `assets/characters/wukong/` | 角色 GLB 与拆出的 4K PBR 贴图 |
| `assets/shaders/ink_post.gdshader` | 水墨后处理着色器 |
| `assets/textures/paper.png` | 宣纸纹理 |
| `assets/props/staff/staff.tscn` | 程序化金箍棒（独立场景，挂在 `weapon_r` 骨骼上） |
| `docs/` | 制作说明、参考图、混元输入、各阶段渲染（`.gdignore`，Godot 不导入） |
| `source/` | Blender 工程、原始 GLB、混元原始模型（`.gdignore`） |
| `tools/blender/` | 生成/清理/绑定/导出的 Blender Python 脚本（跑动动画：`build_run_action.py`） |
| `tools/shots/` | Godot 内取样：`shot_game`（追尾机位）、`shot_cycle`（逐帧循环）、`shot_staff`（持棍角度扫描） |
| `tools/build_scene.gd` | 程序化生成 `main.tscn` |
| `tools/capture.gd` | 截图小工具 |

## 角色规格

- 身高 1.895 m，A-pose 绑定，27 根骨骼（含 4 节尾骨、`weapon_r` 武器挂点）
- LOD0 18k / LOD1 8k / LOD2 3.5k 三角面
- 3 张 4096² PBR 贴图（BaseColor / Metallic-Roughness / Normal）
- **Run 动画：18 帧 @24fps 循环（0.75 s，160 步/分，步长 1.275 m，3.40 m/s）**，
  每步 4 个关键姿势（contact/down/pass/up），站姿驱动脚球、零滑步；做法见 `docs/交接说明_跑步.md`
- idle 仍是 `scripts/main.gd` 程序化（呼吸 + 尾巴），未烘焙

## 已知问题

- 尾巴根部略歪（生成器从正+左两视图推断背面时的产物），加尾骨时可顺带微调
- UV 由生成器提供，局部拉伸；终版应重展 UV 并烘 2K 图集
- 毛发为几何尖刺，终版换 hair cards
- 手部无手指骨骼

详细流程见 `docs/制作说明.md`。







