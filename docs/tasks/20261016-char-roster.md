# 任务：全角色名册（cid／名称／头像，分类放置）

- 状态：已完成（2026-10-16）
- 负责人：本轮 OpenCode 对话（用户直接指派）
- 结果：合并 9169 唯一 cid（APK 7800 + 缓存 1488，逐 ID 缓存优先，同号覆盖 119）→ 可玩 2236 / NPC·敌人 6933；复制头像 2656 个（可玩缺 4：7107/8234/13001/59103，未下载）；单文件自包含 index.html（~82MB，头像 base64 内嵌）+ 分类 icons/ + CSV/JSON + README/manifest/verification（全 PASS）。浏览器实测：DOM 卡片/行/图数量正确、data URI 解码 128×128 字节一致、搜索过滤/恢复正确。职业名=推断；127 条新版记录无 jobtype 归“未知”。
- 新旧判断（二、三轮）：charainfo 全 117 键无逐角色日期字段。用户质疑“cid≠出卡顺序”成立：5xxxx 换装段在 APK、30xxx 不在，块间/段内顺序均无证据，已在 README/HTML 明确修正（不再按 cid 排序解释新旧）。段级“30xxx=最新一批”保留，证据链：全段仅存于缓存增量 + booklist 416 本带日期剧情匹配 509 唯一名/117 命中，30xxx 命中 4 个全部 2026 年（30002 ミレニア 2026-08-20=APK 打包后 2 天、30255 マルカ 2026-05-28、30210/30215 2026-10-15）；APK 内置主表数据截止不晚于 2026-05-28 附近（マルカ锚点）。增量含 308 条低编号老角色更新，“在增量中”≠新出。
- 目标：合并缓存／APK charainfo 主表（逐 ID 缓存优先），输出全部角色的 cid、名称、头像图；头像按 可玩/NPC·敌人 → 职业 → 稀有度 分类复制；附 CSV/JSON/HTML 画廊。
- 写入（本任务所有）：scripts/build_char_roster.py、output/char_roster/、docs/tasks/20261016-char-roster.md。
- 共享依赖（只读）：output/base_master/_mdCharacter.json、output/cache_full_20261015_v3/decoded/{charainfo,worldinfo}.data5.json.raw、output/full_unpack/objects/Card_Icon/。
- 不改：原始采集件、v3/E、full_unpack 产物、HANDOFF.md／STATUS.md（本任务非指定整合者，交接留在本文件与输出 README）。
