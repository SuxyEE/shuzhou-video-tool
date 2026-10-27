# 蜜小π首发片 v3（Cursor 任务）

## 目标
按 `SCRIPT_SHOT_MAP.md` 做约 **180 秒**、16:9 IP 首发片。用户已批准开剪。

## 硬性要求
1. **严格声画同步**：旁白点名地点/课程时，必须切到对照表中的对应实拍（±0.5s）。
2. **禁止**用校门外立面+字幕顶替已有室内/专属场景（图书馆、π空间、奇点工坊、教室、三园等）。
3. **无「小野」水印**，无第三方水印。
4. 旁白：edge-tts `zh-CN-XiaoxiaoNeural`，文本见 `narration_full.txt`；片头约 3s 无人声，片尾约 2s 余韵。
5. 角色：人形探险家定案 `explorer_humanoid.jpg` 抠图叠加；全片生成动画 ≤30s。
6. 用户定案：
   - CC馆长信箱：**不是**青色柜 → 用**插画风格**「问题卡投递」短动画补位
   - 绿语花园：用阳光书房走廊绿植角（stills/sunny_*.jpg）
7. 输出：`artifacts/蜜小π_首发_v3.mp4`（1080p）与 `artifacts/蜜小π_分享版_v3.mp4`（720p）+ README（每段用了哪些素材）。

## 素材位置（uploads/）
解压后预期存在：
- `docs/SCRIPT_SHOT_MAP.md`（权威分镜）
- `docs/narration_full.txt`
- `docs/BRIEF_v3.md`
- `char/explorer_humanoid.jpg`
- `clips/*.mp4`（马年、π空间、overview 切片、course 切片、仙岳山、首展等）
- `stills/*.jpg`（书馆/工坊/教室/花园/课堂等）
- `old_campus/*`（旧版校门/入校/操场/千马图）

## 成功标准
- [ ] 时长 170–190s
- [ ] 段 6 点名 π空间/图书馆/奇点工坊时有专属实拍；段 9 两间教室有室内实拍；段 7 三园有专属实拍；段 3 有银河π首展实拍
- [ ] 信箱为插画补位，非青色柜冒充
- [ ] 绿语花园用 sunny 绿植角
- [ ] 无小野水印；README 写清素材映射
