# 阅读器通用增量同步

- 状态：通用入口已实现，C20 正向与反例回归完成。2026-11-12 核实 C21 正式终审与交付已通过，隔离同步及展示验收完成。
- 写入：`scripts/skill_reader_preview/incremental_sync.py`、同任务展示适配与验证脚本、本任务卡、`work/reader_incremental_sync_20261111/`、`projects/reader/site/` 与 `projects/reader/reports/` 下本任务独立版本。
- 输入：独审认可的主线差异、前后卡片及账本、已验证的阅读器快照。主线、正式阅读器、历史试点和 latest 只读。
- 验收：通用入口无 C20/C21 数量或角色硬编码；安全增量自动接入，等价候选去重，非等价与同句未知保留；歧义输出到核查队列。C20 对照 25/15/6/1 与原展示证据，C21 按其正式差异实测。

## 交付与接续

- [通用同步入口](../../scripts/skill_reader_preview/incremental_sync.py) · [C20 回归报告](../../projects/reader/reports/c20-incremental-20261111/REPORT.md) · [本机回归页](http://127.0.0.1:8772/projects/reader/site/c20-incremental-20261111/)。
- work/reader_incremental_sync_20261111 下保留 C20 正式输入副本、逐案命令与真实退出码。c20_source 以 C21 重建前的 C20 全卡 SHA 验证；生成过程中 C21 在并行写入主线，故未混读现场快照。30220 使用 C20 已有隔离复跑副本，SHA 与 C21 重建前的 C20 清单一致。
- 可用 --plan 预检。结果 0 表示已对齐，2 表示存在待核对卡并保留旧数据，3 表示正式输入、版本或验收门拒绝。没有被自动合并的候选同时在 reviewQueue 报告。
- 参数 --manifest 指正式 final_manifest.json，--verdict 指独立正式裁决。裁决可直接绑定 manifest SHA。先审后打包的流程通过交付回执、清单哈希、独审执行记录、campaign 和完整独立台账建立对应。报告使用 manifest 同目录的 report_data.json，按哈希读取逐行 before/after。--before-cards 指旧卡完整前像，以 Web 基线保存的卡片 SHA 逐张核对。
- C21 实跑使用 --base-reader projects/reader/site/c20-incremental-20261111、--before-cards work/reader_incremental_sync_20261112/before_cards、C21 正式 manifest／verdict 及 --name c21-incremental-20261112。新增 900 条，103 条候选去重，116 条不同父分支保留，四项同句未解与 1,415 条拆分记录继续披露。详见 [C21 验收](../../projects/reader/reports/c21-incremental-20261112/REPORT.md)与[隔离试点](http://127.0.0.1:8773/projects/reader/site/c21-incremental-20261112/)。
