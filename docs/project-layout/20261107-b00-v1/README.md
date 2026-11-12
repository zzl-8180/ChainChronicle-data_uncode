# B00 六项目导航与原位版本索引

版本：20261107-b00-v1；生成：2026-11-07T02:08:05+08:00。B00已新增六个项目README和本版本导航索引；B01—B08未由本任务启动。未移动、复制或重建业务文件，未切换现有生产／消费路径。`physical_action_this_turn=none`、`recursive=false`、`selection_mode=exact_mapping_entry`、`specific_child_precedence=true`。

本轮由三个 Sol medium 子代理编写、主聊天整合验收；[验收回执](validation.json)确认1,140条原映射字段逐条一致、六个入口齐备、既有1,315条本地链接通过及旧方案／报告哈希未变。检查仅针对导航文档，不代表业务兼容测试或后续迁移门槛通过。

这份索引完整覆盖批准基线的1,140行，不是此刻全项目枚举。目录行与子行可重叠，更具体子行优先；行数不等于唯一文件数、媒体数或可移动条数。业务代码与数据仍从原路径运行，新README是导航入口。原任务目录、冻结证据、ZIP、spec、manifest、pins、归档与目录联接均保留；逻辑归属不授予修改、删除、发布或迁移权限。

| 项目入口 | 职责 | 完整原位路径索引 | 基线行数 |
|---|---|---|---:|
| [数据解包](../../../projects/unpack/README.md) | APK／缓存采集与解码 | [unpack.md](unpack.md) | 80 |
| [媒体资源](../../../projects/assets/README.md) | 媒体导出、来源绑定与完整性 | [assets.md](assets.md) | 16 |
| [技能研究](../../../projects/skill-research/README.md) | 规则、逐句答案与证据账本 | [skill-research.md](skill-research.md) | 900 |
| [角色阅读器](../../../projects/reader/README.md) | 中文阅读、查询与展示 | [reader.md](reader.md) | 23 |
| [参考资料分析](../../../projects/reference-analysis/README.md) | 外部资料对照与候选分析 | [reference-analysis.md](reference-analysis.md) | 26 |
| [工具与成果发行](../../../projects/distribution/README.md) | 工具、成果的声明版本交付 | [distribution.md](distribution.md) | 20 |

共享治理单列：[shared.md](shared.md)（75行），包括根约定、输入与环境、治理工具和历史恢复关系；它不是第七个业务项目，也不建立新的共享生产根。合计1,140行。机读全量入口：[index.json](index.json)。

批准来源：[docs/project-layout/20261106/path-map.json](../20261106/path-map.json)（schema_version=3，修订时间 `2026-11-07T00:28:06+08:00`，SHA-256 `a2a89d48104cd4707515b98d4ccd48462a455c7b63b5a3431ed4978c9ea2061d`）。配套 [21项耦合契约](../20261106/audit/contracts.json)、[当前分批方案](../20261106/batch-plan.md)／[批次机读方案](../20261106/batch-plan.json)、[第三方逐项复查入口](../20261106/audit/thirdparty-recheck-20261107/RECHECK.md)。原方案及其“未实施”等历史观察保留原文；本版本单独记录B00新增，不回写旧方案。来源文件哈希、版本与生成时间完整登记在index.json；未给业务文件新增全量哈希。

本地任务入口（观察限定为本次读取，不代表实时会话/全局停工状态）：[C19周期卡](../../tasks/20261107-c19-cycle.md)、[C19交付卡](../../tasks/20261107-c19-delivery-package.md)；读取时两组候选独审及最小接线内存消费复核完成、交付脚本准备中。阅读器 [语义复核卡](../../tasks/20261107-reader-semantic-review.md) 与 [阅读层级卡](../../tasks/20261107-reader-reading-layout.md) 本地状态均为完成；阶段完成不表示整个聊天停工或负责人已交接。继续保护脚本、正式输入、旧输出和分片，不接管他人写入。旧映射的task_catalog原样转存为baseline_task_catalog并明确标为历史观察，不能当当前看板。

已知历史缺口继续保留：`output/character_skills/review/r3_sentence_fix_20261024_deepseek/REPORT.md` 当前缺失；`work/review_20261016` 中rectify_native旧报告为前次审计确认缺件、未恢复，未确认具体文件名。均不造链接或补造内容，见 [原归属与缺件报告](../20261106/audit/unassigned-resolution-report.md)。目录存在不证明其历史报告齐备。

索引只对精确source取存在性、种类和reparse元数据，不递归跟随junction，不运行/导入build、verify、prepare或其他业务脚本。存在且非保留名才生成source链接；Windows根`nul`以扩展路径检测并保留非链接文字。各项目索引中的未来目标只属方案元数据，不能据此将当前工作写入尚未建立的目标目录。后续批次须按具体授权和对应契约实施。
