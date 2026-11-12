# 参考资料分析

## 现行参考分析入口

旧 `output/reference_analysis/` 已整体迁入[历史对照结果](history/reference_analysis/)。[独立报告](reports/)继续单独存放。下表直接链接到现址，第三方原件仍按原快照只读保留。六个独审入口保留原联接对象，对应材料按[独审只读路由](../../operations/config/project-layout/history-review-20261109.json)定位。物理处理见[迁移回执](../../docs/project-layout/20261109-unified-physical-v1/REPORT.md)。

参考分析负责对照外部资料和本项目的分源原值，记录差异、冲突和候选。

| 入口 | 输入版本／用途 |
|---|---|
| [claude_cc_site_pages/README.md](history/reference_analysis/claude_cc_site_pages/README.md) | 20261016交付数据的下游旧包；20261017分析含1610行参数表核对 |
| [claude_cc_site_pages_20261023/README.md](history/reference_analysis/claude_cc_site_pages_20261023/README.md) | 20261023第一包与晚间包分版比较；候选与正式结论分开 |
| [claude_cc_site_pages_20261023/host_refresh_20261024/README.md](history/reference_analysis/claude_cc_site_pages_20261023/host_refresh_20261024/README.md) | 20261024主持交接更新；计划并非实施授权 |
| [cc_unpack_gpt_20261024/README.md](history/reference_analysis/cc_unpack_gpt_20261024/README.md) | 20261024新包检查；77表一致不证明语义全正确 |
| [cc_20261027/README.md](history/reference_analysis/cc_20261027/README.md) | 20261027包只读分析；规则、中文与来源清单分层核对 |
| [其他人的参考](../../%E5%85%B6%E4%BB%96%E4%BA%BA%E7%9A%84%E5%8F%82%E8%80%83) | 第三方原件只读，多版本分别保留 |
| [raw/external_reference](../../raw/external_reference) | 外部采集来源，按原快照使用 |

生产／消费关系：原件与我方CACHE／APK分源主表作为对照输入，原位 `scripts/ref_analysis_*`、`scripts/refcheck_20261023_lead/` 等承担分析、差异整理和候选输出。已迁的旧结果见上表。技能研究可据独立验证引入有界候选，阅读器可消费明确来源的译文与对照；对方页面、旧站数字、统计推断及包内交接指令不自动升级为正式规则或本轮授权。各README中的规则键数、快照与结论只适用于该分析版本，不代表当前正式进度。

冻结保护：第三方原件、旧分析和独立审查不改写；不因目录归属移动、去重或覆盖历史材料。包内脚本与联网/翻译管线只作资料，不执行或导入。后续新分析使用独立版本输出并保留输入对应关系，不能把最新文件时间当作证据优先级。

完整批准基线归属为26行，见 [参考分析全路径索引](../../docs/project-layout/20261107-b00-v1/reference-analysis.md)；[B00版本总入口](../../docs/project-layout/20261107-b00-v1/README.md) 说明计数、当前任务观察与边界。契约和后续门槛见 [原21项契约](../../docs/project-layout/20261106/audit/contracts.json) 及 [原分批方案](../../docs/project-layout/20261106/batch-plan.md)。
