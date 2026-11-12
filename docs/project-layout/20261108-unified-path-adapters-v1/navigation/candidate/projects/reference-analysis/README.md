# 参考资料分析

## 统一迁移后参考分析入口（统一迁移验收后）

统一迁移仅在 31 棵完整目录、2 个 latest 控制文件、读取与写入适配、别名及保护契约通过最终验收，并按单独授权安装 `scripts/project_layout_active.json` 后作为当前物理布局。合入后，原 CLI 的已适配逻辑路径默认解析到新根，无须每次手设环境变量；未适配命令仍须按各自验收回执核对。冻结清单中的旧来源字符串保留原值；不能把迁址当作重新生成或重新签名。 旧 `output/reference_analysis/` 作为完整树进入 [history/reference_analysis](history/reference_analysis/)；没有合并进现存 [reports](reports/)（B01独立报告继续独立）。第三方原件 `其他人的参考/`、`raw/external_reference/` 仍只读且原位。六个历史第三方审查别名中的 `reference_analysis` 属未决访问退役契约；不把旧别名自动改指向或冒称历史现场仍可直读。下文旧 B00 路径字符串仅作其当期索引。


职责：对照他人资料、网站快照与本项目分源原值，保留差异、冲突、可验证候选和证据边界。这里是B00新增导航入口；业务材料仍在原位，不启动参考接入、重建或迁移。

| 当前原位入口 | 输入版本／用途 |
|---|---|
| [output/reference_analysis/claude_cc_site_pages/README.md](history/reference_analysis/claude_cc_site_pages/README.md) | 20261016交付数据的下游旧包；20261017分析含1610行参数表核对 |
| [output/reference_analysis/claude_cc_site_pages_20261023/README.md](history/reference_analysis/claude_cc_site_pages_20261023/README.md) | 20261023第一包与晚间包分版比较；候选与正式结论分开 |
| [output/reference_analysis/claude_cc_site_pages_20261023/host_refresh_20261024/README.md](history/reference_analysis/claude_cc_site_pages_20261023/host_refresh_20261024/README.md) | 20261024主持交接更新；计划并非实施授权 |
| [output/reference_analysis/cc_unpack_gpt_20261024/README.md](history/reference_analysis/cc_unpack_gpt_20261024/README.md) | 20261024新包检查；77表一致不证明语义全正确 |
| [output/reference_analysis/cc_20261027/README.md](history/reference_analysis/cc_20261027/README.md) | 20261027包只读分析；规则、中文与来源清单分层核对 |
| [其他人的参考](../../%E5%85%B6%E4%BB%96%E4%BA%BA%E7%9A%84%E5%8F%82%E8%80%83) | 第三方原件只读，多版本分别保留 |
| [raw/external_reference](../../raw/external_reference) | 外部采集来源，按原快照使用 |

生产／消费关系：原件与我方CACHE／APK分源主表作为对照输入，原位 `scripts/ref_analysis_*`、`scripts/refcheck_20261023_lead/` 等产生 `output/reference_analysis/` 的分析、差异和候选。技能研究可据独立验证引入有界候选，阅读器可消费明确来源的译文与对照；对方页面、旧站数字、统计推断及包内交接指令不自动升级为正式规则或本轮授权。各README中的规则键数、快照与结论只适用于该分析版本，不代表当前正式进度。

冻结保护：第三方原件、旧分析和独立审查不改写；不因目录归属移动、去重或覆盖历史材料。包内脚本与联网/翻译管线只作资料，不执行或导入。后续新分析使用独立版本输出并保留输入对应关系，不能把最新文件时间当作证据优先级。

完整批准基线归属为26行，见 [参考分析全路径索引](../../docs/project-layout/20261107-b00-v1/reference-analysis.md)；[B00版本总入口](../../docs/project-layout/20261107-b00-v1/README.md) 说明计数、当前任务观察与边界。契约和后续门槛见 [原21项契约](../../docs/project-layout/20261106/audit/contracts.json) 及 [当前分批方案](../../docs/project-layout/20261106/batch-plan.md)（B01-R尚未由本任务启动）。
