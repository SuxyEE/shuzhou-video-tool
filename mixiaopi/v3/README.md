# 蜜小π首发片 v3

按 `source/SCRIPT_SHOT_MAP.md` 声画同步剪的一版。旁白点到地点，画面切到那个地点的实拍，不再用校门外立面顶替室内。

成片 **183.5 秒**。片头 3 秒只有校门和片名，没有人声。最后一句之后大约还有 2 秒落版。旁白是 edge-tts `zh-CN-XiaoxiaoNeural`，原文在 `source/narration_full.txt`。全片插画/生成画面大约 22 秒，其余是实拍或实拍静帧。

## 成片

| 文件 | 规格 |
| --- | --- |
| `artifacts/蜜小π_首发_v3.mp4` | 1920×1080，183.5 秒，74.3 MiB（77,905,271 字节） |
| `artifacts/蜜小π_分享版_v3.mp4` | 1280×720，183.5 秒，32.5 MiB（34,052,150 字节） |

## 每段用了什么

时间是成片时间轴。

| 段 | 时间 | 素材 | 说明 |
| --- | --- | --- | --- |
| 片头 | 0:00–0:03 | `clips/overview_01.mp4` | 校门石牌实拍，叠片名 |
| 开场 | 0:03–0:20 | 插画地图约 2.6 秒；`old_campus/playground1.mp4`；`old_campus/enter.mp4`；`old_campus/gate1.mp4`；`clips/overview_04.mp4` | 「西海岸」是线描地图，不是假海景。念到校名切校门石牌，念到蜜小π切主楼 |
| 理念 | 0:20–0:43 | `stills/garden_1.jpg`；`old_campus/clip_extra.mp4`（自然教育墙）；插画「两颗大树」；`clips/overview_09.mp4`、`overview_08.mp4`（大树阅读阶梯）；`stills/library_2.jpg`；`stills/sunny_1.jpg` | 图解之后立刻回到实拍大树阶梯 |
| 自然π | 0:43–1:07 | `course_08` 植物图鉴、`course_01` 自然π、`course_02` 课程图、`course_06` 孩子、`moss.mp4` 野外调查、`course_07` 看植物、`plant.mp4` 叶子、`soil.mp4` 测土、`course_15` 昆虫家园、插画「沙·叶·凤蝶」、`course_03` 学生作品 | 合集片底部无关字幕已裁掉 |
| 银河π | 1:07–1:30 | `stills/cls_exhibit_1.jpg`（大屏 1972/2026）；`clips/exhibit_1.mp4` 首展课堂；`stills/workshop_1.jpg`、`cls5_1.jpg`；`stills/cls_soil_1.jpg`；插画星空约 4 秒 | 科技馆没有合作现场，只在字幕写「厦门科技馆展教中心」，不画假场馆 |
| 落地 | 1:30–1:47 | `clips/overview_04.mp4`、`stills/rainbow_1.jpg`、`clips/pi_01.mp4` 玻璃顶展廊、`old_campus/enter.mp4` | 「跟我看看」推进主楼 |
| 马年形象墙 | 1:47–1:53 | `clips/horse_1.mp4`（稚笔千骏）、`clips/horse_4.mp4`（整墙） | 1100 个孩子对整墙作品 |
| π空间 / 图书馆 / 工坊 / 信箱 | 1:53–2:13 | `clips/pi_04.mp4`、`pi_08.mp4` 展墙；`stills/library_1.jpg` 探微书馆字、`clips/overview_09.mp4` 孩子读书；`stills/workshop_2.jpg`、`workshop_1.jpg`；**插画「问题卡投递」** | 青色柜没有当信箱用 |
| 三园 | 2:13–2:27 | `stills/cls_garden_1.jpg` 孩子种植、`garden_1.jpg`（叠 1㎡ 框）；`banye_1.jpg`、`banye_2.jpg`；`habitat_1.jpg`、`habitat_2.jpg`（乔木/灌木/地被线） | 三处都是专属实拍 |
| 操场 / 绿语花园 | 2:27–2:33 | `old_campus/playground1.mp4`；`stills/sunny_2.jpg`、`sunny_3.jpg` | 绿语花园按定案用阳光书房走廊的绿植角。旁白里「操场」和「绿语花园」挨得很近，操场镜头较短 |
| 教室 | 2:33–2:42 | `stills/art_1.jpg`、`art_2.jpg`；`clips/course_03.mp4` 自然笔记作品；`stills/science_2.jpg`；`stills/cls6_1.jpg` | 美术教室、科学教室都是室内 |
| 结尾 | 2:42–3:03.5 | `course_01`、`cls_exhibit_1.jpg`、`cls5_1.jpg`、`overview_01`、`overview_09`；插画 π 小数光带；`old_campus/school_gate.jpg` | 落版：「从自然π到银河π · 读世界 · 长思维」「让生命自然生长 · 让爱传递」「厦门市东渡第二小学 & 自然π·校园生态探秘博物馆」 |

角色锁在 `char/explorer_humanoid.jpg`（头盔、放大镜、π 翅膀）。另外生成了 8 个姿势，抠成透明图放在 `char/poses/`：挥手、左指、右指、走路、飞行、举放大镜、探头、欢呼。它不再钉在一个角上，每镜都会换位置：从画面外飞入、斜着穿过、沿着边走，或者在左右之间来回。指的方向朝向正在讲的景物。校门石牌特写时它缩小，只在石牌上方的天空里横飞，不压「厦门市东渡第二小学」。CC 馆长信箱仍是问题卡投递插画，角色在信箱右侧飞上飞下，用手指着投递口。落版时它贴在右边上下移动，不挡住字。平面插画（地图、两棵树、沙叶凤蝶、星空、信箱、π 光带）都是扁平画法，不冒充实拍。全片插画时长仍约 22 秒，飞行和换位都是叠在实拍上的透明角色，不另占生成画面预算。

## 重做

```bash
python3 mixiaopi/v3/build/build_v3.py --step film
python3 mixiaopi/v3/build/reoverlay_poses.py
```

第一条做出实拍底板和旁白。第二条只重贴会飞的蜜小π。需要 ffmpeg、Pillow、numpy、scipy，以及能联网的 edge-tts。旁白若已生成在 `work/voice/`，脚本会直接用。

剪映草稿给同事二创时，在电脑上用剪映专业版：

```bash
python3 mixiaopi/v3/build/export_jianying.py
```

得到的 `蜜小π_剪映草稿.zip` 里有导入说明。解压后双击 `导入剪映.bat`（苹果电脑用 `导入剪映.command`），退出剪映再打开，草稿名叫「蜜小π首发」。画面、蜜小π、字幕、旁白、音乐是分开的轨道。
