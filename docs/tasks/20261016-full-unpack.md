# 任务：完整解包已取得本地资源（full_unpack）

- 状态：已完成（2026-10-16）
- 负责人：本轮 OpenCode 对话（用户直接指派）
- 结果：68655/68655 bdl 解码展开成功，834741 对象导出；账本 68993 行；4 项验证 PASS + 全量逐包索引↔磁盘核对 0 失配。产物 output/full_unpack/（20.24 GiB）。已同步 HANDOFF.md / STATUS.md。
- 写入（本任务所有）：scripts/full_unpack_{probe,run,merge,verify,finalize}.py、work/full_unpack/、output/full_unpack/、docs/tasks/20261016-full-unpack.md；HANDOFF.md/STATUS.md 顶部各加一节并修正 bdl 旧表述。
- 共享依赖（只读）：composite_inventory.jsonl、两个 raw 归档工作副本、decode_data5.NativeDecoder、work/protection/、.venv。未改原始归档、v3、refresh、E、card_*、ordinary_effects、boss_*。
- 已闭合：15 包大小写命名覆盖（重跑修正）+75 旧命名遗留清理；纹理 format_name 元数据 UNKNOWN 修正（全量重跑）。
- 后续（如需要）：字段语义解释按需做；APK 内置媒体批量导出可复用本管线；cid 绑定证明按 cid30236 方法定向取证。
