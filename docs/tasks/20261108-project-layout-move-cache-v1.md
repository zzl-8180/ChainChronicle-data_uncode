# v1 旧缓存目录整体迁址

状态：执行完成，主聊天独立验收通过；2026-11-08。负责人：Sol 子任务 `migrate_cache_v1`，主聊天整合验收。

目标：将 `output/cache_full_20261015/` 原目录同盘移动至 `projects/unpack/data/cache/cache_full_20261015/`，保留目录内全部字节与历史字段原值。当前 `output/cache_full_latest.json` 指向 v3，不参与迁址。

本任务写入范围：仅上述 v1 目录的精确移动、`projects/unpack/README.md` 的迁址入口、`projects/unpack/data/cache/.gitignore`、`docs/project-layout/20261108-move-cache-v1/`、本任务卡。共享根入口、v3、single、旧审查／报告和其他任务卡均只读。

共享依赖：历史报告内的 v1 `json_file` 保留原来源字符串，另以本任务的外部映射说明当前物理路径。静态定向搜索仅发现旧清理盘点与发行脚本的历史文字，不构成动态依赖的全局证明；运行中的任务是否占用源目录以迁移前稳定观测和只读检查为准。

结果：迁移前后 88 个文件、73,835,561 字节，各文件相对路径、大小、mtime、SHA-256 与 4 个目录项一致；12 个保护锚点未变，旧源路径不存在。88/88 个文件由新增局部 `.gitignore` 忽略，88/88 个外部路径映射落到现存文件。新文档、清单、脚本、任务卡与局部 ignore 合计约 35 KiB（导航页增量另计），未产生数据副本。详见 [迁址记录](../project-layout/20261108-move-cache-v1/README.md)。

独立验收：主聊天使用自行记录的迁移前基线复核，88 个文件路径、大小、SHA-256、mtime 与目录项一致；single、两份 latest 及共享根保护文件未变。Git 忽略、外部映射和新增导航链接均通过，回退说明已核对但未执行。见 [验收回执](../project-layout/20261108-move-cache-v1/acceptance.json)。本批结束，其他批次未启动；动态依赖仍按新任务具体证据处理，本次静态检查不证明全局无动态消费者。
