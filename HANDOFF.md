# 当前交接入口

更新：2026-11-08。本文件只维护当前入口和边界；数字及批次状态以[唯一进度看板](docs/tasks/character-skills-progress.md)顶部为准，不在此复制另一套看板。

## 接手顺序与主线

1. [AGENTS.md](AGENTS.md)：目录、证据、协作及交付约定。
2. [角色技能完整解读实施方案](docs/角色技能完整解读实施方案.md)：当前规则、职责与验收流程；历史阶段安排保留在其附录，不重新启动。
3. [进度页](docs/tasks/character-skills-progress.md)：先读接手摘要与唯一当前看板，再按需读其指向的任务和审查。
4. [2026-10-25主持交接](docs/tasks/20261025-host-transition.md)：已收口过程、版本锚点、发行使用方法和新缓存恢复条件；历史授权不自动激活。

主线保持Y.G.优先的逐描述、逐效果数值解读，已证适用域可连带其他卡；有证单项先交付，其余机制保留未知。资源解包、字段解释和展示按用户当次目标推进，不默认同时启动。

## 已交付与当前边界

- **当前状态（2026-11-07）**：**C19在明确范围限制下收口；R01 CLOSED、阻断0，RETAINED 0/12。** 主提交`e2e864624b407682a6c2ab6798bea37ff6ea12bb`与文档提交`10abe23bd3c50ee1dd22e21c5e850b024c1bb882`均已推送，等待用户下一步安排，不启动C20或发布。数字与历史以[唯一看板](docs/tasks/character-skills-progress.md)和[C19收口记录](docs/tasks/20261107-c19-cycle-closeout.md)为准；通用经验已并入[实施方案](docs/角色技能完整解读实施方案.md)§1.3／§1.4／§1.6及收口记录§8。
- **C19当前入口**：[收口记录](docs/tasks/20261107-c19-cycle-closeout.md)／[新版成果页](output/character_skills/cycle_reports/C19_r01_20261107/index.html)／[剩余量](output/character_skills/cycle_reports/C19_r01_20261107/remaining.html)／[R01复核REPORT](output/character_skills/review/direction_c19_20261107_thirdparty_r01_recheck/REPORT.md)／[verdict](output/character_skills/review/direction_c19_20261107_thirdparty_r01_recheck/verdict.json)／[清理与Git任务卡](docs/tasks/20261107-c19-closeout-cleanup-git.md)／[清理回执](output/storage_retention/cycle_closeout_c19_20261107/README.md)／[Git回执](output/storage_retention/cycle_closeout_c19_20261107/git_commit_manifest.json)。
- **C19 Web接收登记（2026-11-08）**：[接收登记](docs/tasks/20261108-c19-web-evidence-receipt.md)／[V01独审REPORT](output/character_skills/review/reader_v01_thirdparty_20261107/REPORT.md)。V01 FIXED、总体PASS_WITH_EXPLICIT_SCOPE_LIMITS，原R01的B01—B03、N01—N06保持FIXED。**已登记接收／证据保留／正式吸收待另行安排**；不改主线规则、答案、账本或数据基线，不启动C20。
- **C19历史前像**：[正式交付包](output/character_skills/c19_delivery_20261107/README.md)／[正式独立终审](output/character_skills/review/c19_delivery_final_20261107_deepseek/REPORT.md)／[原C19成果](output/character_skills/cycle_reports/C19/index.html)／[原方向审查REQUEST_CHANGES](output/character_skills/review/direction_c19_20261107_thirdparty/REPORT.md)。历史报告、送审材料和manifest不改；关联推断、45个未解效果、4行既有split_flags、未实机及第三方浏览器UNTESTED继续保留。其他周期入口见进度页。
- **较早历史入口（C16—C15）**：[C16收口记录](docs/tasks/20261104-c16-cycle-closeout.md)／[C15-R01复验收口](docs/tasks/20261104-c15-r01-recheck-closeout.md)。历史数字、检查范围及推送状态以原记录为准，不在当前入口重复。
- **较早历史入口（C14—C11）**：[C14收口记录](docs/tasks/20261103-c14-cycle-closeout.md)／[C13收口记录](docs/tasks/20261031-c13-cycle-closeout.md)／[C11／C12收口](docs/tasks/20261031-c11-c12-direction-review-closeout.md)。历史冻结成果、原裁决和UNTESTED范围不改。
- **机制优先交接**：[执行细则](docs/tasks/20261104-mechanism-first-execution.md)／[接收对账](docs/tasks/20261104-mechanism-first-reconciliation.md)／[下一批方案依据](docs/tasks/20261104-mechanism-first-next-batch-plan.md)。历史候选仅作回归种子，须按当前版本重新核验，不自动晋级。
- **批18已收口**：[任务卡](docs/tasks/20261025-character-skills-b18.md)、[产物与证据](output/character_skills/b18_20261025/README.md)、[最终独审](output/character_skills/b18_20261025/review/REVIEW_FINAL.md)。既有结果不因本次文档适配重新审查。
- **②本地独立发行/干净目录代表复现已完成**：[发行说明](output/share_bundle/20261025-character-tools/README.md)、[任务记录](docs/tasks/20261025-clean-release-reproduction.md)。使用该发行目录的`packages_retry/`；`packages/`为失败诊断。范围及未验证环境按发行说明，不将本地交付写成已公开发布。
- **第二周期第三方审查整改已完成（2026-10-26）**：审查 verdict＝REQUEST_CHANGES（R01/R02 阻塞、N01 非阻塞）→ 修复并正式重建。交付[整改索引](output/character_skills/cycle2_rectification_20261026/README.md)（修复说明、代码差异、190条受影响清单、探针、容量回执、run_record）；campaign `f44c4089…`、snapshot `f44c4089-d3790431153a5dcd`、rules 290键（仅26|param5 unit文案）；verify_full 17/17、账本9/9、A7 29/29；代码定稿两次正式生成同签名、4,472 个卡片产物逐字节相同，隔离目录 16 张代表卡 32/32 相同；旧答案零丢失零改值、范围外零变化、30236/30239逐字节不变、S4 415→415。**后续定向复核与原第三方复审均已通过并收口（2026-10-26，详见进度页历史）**。
- **③新缓存更新暂缓**：`DEFERRED_NO_NEW_CACHE`；有新缓存且用户明确恢复后，按主持交接§4先核版本/差异，再定有界任务。不得自动采集、覆盖latest或恢复HOLD18。
- **其他后续**：HOLD18保持；C8—C13 Git闭包已完成，统一查询CLI及其他语义专项按用户下一安排。当前已有未提交/未跟踪成果，不删除、不批量暂存、不擅自推送。
- **UI样稿**：[独立任务卡](docs/tasks/20261025-ui-reading-preview.md)记录B版主入口已完成、待用户查看，尚未正式整合；其实际在途写入需按任务核实，不在解析批次中接管。

## 存储与事故边界

- **旧包退役V2已完成**：[第三方执行报告](output/storage_retention/export_cleanup_review_20261025/REPORT.md)、[删除后验收](output/storage_retention/export_cleanup_review_20261025/postcheck_result_20261025.json)、[任务卡](docs/tasks/20261025-export-cleanup-inventory.md)。用户已确认执行，第三方删除与后验均完成；清单授权已履行，不再运行旧提示词。44份隔离输入、当前发行包、旧报告与元数据保持；两旧完整快照已退役。未释放构建预约，不扩大其他清理。
- **容量**：沿用方案§8及进度页当前记录；后续正式重建先核容量，处置依新的具体清单，不能复用已履行的删除授权。
- **事故与旧整改**：[事故唯一边界](output/20261024-project-review/incident_command_20261024/README.md)、[处置收口与残留缺口](output/20261024-project-review/incident_command_20261024/incident_closeout_20261024.md)。恢复线按残留缺口收口，R3归属/选题链已关闭；永久防误删设计定稿、代码未实施，不写成事故全部解决。
- **存储治理**：沿用方案§8.1与[任务卡](docs/tasks/20261024-storage-governance-plan.md)，待用户安排启动；不作为主线前置，不因规范适配启动代码、删除或新的审查流程。

## 按需查阅

- 解包使用方法：[README.md](README.md)；缓存、APK、媒体及既有证据入口见AGENTS定位表，原件保持不变。
- 当前规则：`output/character_skills/profiles/rules.json`；逐卡答案：`output/character_skills/pages/<cid>/card.json`。旧`query_effect_dictionary.py`不读取这套新答案，统一只读CLI尚未交付。
- 历史阶段概况：[STATUS.md](STATUS.md)；[旧HANDOFF正文](STATUS.md#handoff-history-20261025)原样转存，独有历史证据及原链接保留。仅按相关版本查阅，不通读全部历史或重跑A—E。

本次轻量适配只修文档入口与执行规则，完成记录见进度页；后续实施仍以用户当次任务为准。
