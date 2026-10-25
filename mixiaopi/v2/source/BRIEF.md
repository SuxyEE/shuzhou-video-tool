# 蜜小π首发视频 v2（Cursor 任务）

## 目标
做一条约 **3 分钟**、16:9 的学校 IP 首发片：
**厦门市东渡第二小学 & 自然π·生态探秘博物馆 — IP 形象蜜小π**。

**硬性要求**
1. **必须结合真实校园素材**（`uploads/` 下 campus 目录）。画面主体以实拍校园为主，不要再用纯 AI 虚构校园顶替实拍。
2. **角色以「人形探险家定案」为主**（`explorer_humanoid.jpg`：头盔、放大镜、π翅膀、探险背心）。可辅以毛绒圆蜂（`plush_3view.jpg` / `flat_simple.jpg`）作点缀或转场，但主视角是人形蜜小π。
3. **不要「小野」水印**，不要任何第三方水印。
4. 旁白第一人称（蜜小π），中文；可用 edge-tts（推荐 `zh-CN-XiaoxiaoNeural`）。
5. 成片约 180 秒；输出 `artifacts/蜜小π_首发_v2.mp4`（1080p 优先）和 `artifacts/蜜小π_分享版_v2.mp4`（720p 小体积）。
6. 在 README 写清：每段用了哪些 campus 文件、角色如何合成、已知缺口（没有室内图书馆/教室实拍时如何处理）。

## 素材清单（已挂载到 uploads）
### 角色
- `char/explorer_humanoid.jpg` — **人形蜜小π定案（主）**
- `char/plush_3view.jpg` — 3D 毛绒三视图（辅）
- `char/flat_simple.jpg` — 平面简版圆蜂（辅）

### 校园实拍（已压缩 720p）
| 文件 | 原名 | 用途建议 |
|------|------|----------|
| campus/enter.mp4 | 入校.mp4 | 开场/入校 |
| campus/gate1.mp4, gate2.mp4 | 校门1/2 | 校门巡游 |
| campus/school_gate.jpg | 学校大门.jpg | 校门静帧/落版 |
| campus/front_field.mp4 | 前操场.mp4 | 理念/自然场景 |
| campus/playground1/2/3.mp4 | 操场1/2/3 | 运动·生长 |
| campus/thousand_horses.mp4 | 千马图.mp4 | **马年形象墙重点** |
| campus/clip_extra.mp4 | VID_… | 补充空镜 |

### 文档
- `docs/timeline_v2.json` — 分镜、旁白、建议素材映射
- `docs/narration.txt` — 旁白全文

## 制作方法（请你自主选型，但必须吃实拍）
推荐流水线（可调整）：
1. 抠出人形蜜小π透明 PNG（背景白）。
2. 用 edge-tts 按 `narration.txt` / timeline 分段生成旁白，对齐总时长 ~180s（片头留白约3s、片尾余韵约2s）。
3. **每段画面 = 真实校园素材裁切/变速/Ken Burns + 蜜小π叠加动画**（飞入、悬停、挥手、掠过）。角色合成可用 PIL/ffmpeg overlay、或你们环境里可用的图生视频/参考生视频——但底层背景必须来自 campus 实拍（银河π星空段除外，可用生成星空+从实拍地面起飞）。
4. ASS 中文字幕 + 关键词大字；片尾落版文案：
   - 「从自然π到银河π · 读世界 · 长思维」
   - 「厦门市东渡第二小学 & 自然π·校园生态探秘博物馆」
5. 轻 BGM，音量压在旁白下。

## 成功标准
- [ ] 成片时长 170–190s
- [ ] 肉眼可辨：大量镜头背景是东渡二小实拍（校门/操场/千马图等），不是假校园
- [ ] 人形蜜小π定案形象贯穿（与参考图一致：头盔、放大镜、π翼）
- [ ] 无「小野」水印
- [ ] artifacts 下两版 mp4 + README 说明素材用法
- [ ] 在最终报告写出 artifacts 相对路径与文件大小

请直接开工，完成后把成品放到 artifacts/。
