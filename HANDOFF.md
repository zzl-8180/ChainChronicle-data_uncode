# 当前交接入口

## 现行目录入口

统一迁移已验收，已适配的 CLI 默认解析到新址。按[根 README 的现行入口表](README.md#现行入口)查找正式成果、试点、共享目录和退役归档。逐根新旧位置以[实际迁移回执](docs/project-layout/20261109-unified-physical-v1/REPORT.md)为准。正式规则、逐卡页面、账本与全库阅读器继续位于 `output/character_skills/`，存储保留及冻结审查也保留原位。下方各周期的旧 `output/...` 字符串按其历史版本理解。

更新：2026-11-12。本文件只维护当前入口和边界；数字及批次状态以[唯一进度看板](docs/tasks/character-skills-progress.md)顶部为准，不在此复制另一套看板。

## 接手顺序与主线

1. [AGENTS.md](AGENTS.md)：目录、证据、协作及交付约定。
2. [角色技能完整解读实施方案](docs/角色技能完整解读实施方案.md)：当前规则、职责与验收流程；历史阶段安排保留在其附录，不重新启动。
3. [进度页](docs/tasks/character-skills-progress.md)：先读接手摘要与唯一当前看板，再按需读其指向的任务和审查。
4. [2026-10-25主持交接](docs/tasks/20261025-host-transition.md)：已收口过程、版本锚点、发行使用方法和新缓存恢复条件；历史授权不自动激活。

主线保持Y.G.优先的逐描述、逐效果数值解读，已证适用域可连带其他卡；有证单项先交付，其余机制保留未知。资源解包、字段解释和展示按用户当次目标推进，不默认同时启动。

## 已交付与当前边界

- **当前状态（2026-11-12）**：**C21-R01原第三方定向复验通过，F01／F02均CLOSED，阻断0；C21在明确范围限制下收口，不启动C22、清理、Git或发布。** 518卡900行900效果900答案（P1 766／P2 134；严格直接899＋首句条件镜像1；Y.G.11／非Y.G.889），campaign `5492e173e3fa7c918eb3a2a701d6471e4a84246927e9450cf1cd99d3bc74e010`、snapshot `5492e173-cf9451c6ff47fcfb`、rules 294键未改。唯一一次jobs4全库生成；正式终审23/23、阻断0、900项独立重导，成果详细验证42/42；第三方40/42、阻断2，900项数值与来源独立重算通过；R01 60/60、89条条件台账及12文件manifest通过；原第三方复验39/39、F01／F02均CLOSED、阻断0。当前RETAINED 12/12、reserved_bytes 8,032,729,057 B，未清理；关联推断、runtime_verified=False、未实机及浏览器UNTESTED保留。数字、范围、验证、勘误和限制见[C21阶段收口](docs/tasks/20261112-c21-cycle-closeout.md)。
- **C21当前入口**：[阶段收口](docs/tasks/20261112-c21-cycle-closeout.md)／[成果页](output/character_skills/cycle_reports/C21/index.html)／[剩余量](output/character_skills/cycle_reports/C21/remaining.html)／[900答案台账](output/character_skills/cycle_reports/C21/answer_ledger.json)／[final_manifest](output/character_skills/cycle_reports/C21/final_manifest.json)／[handoff_verification](output/character_skills/cycle_reports/C21/handoff_verification.json)／[正式独立终审](output/character_skills/review/c21_delivery_final_20261111_deepseek/REPORT.md)／[审查入口修复](output/character_skills/review/c21_delivery_final_20261111_deepseek/REPAIR.md)／[第三方送审提示词](docs/tasks/20261112-c21-direction-review-prompt.md)／[第三方REPORT](output/character_skills/review/direction_c21_20261112_thirdparty/REPORT.md)／[verdict](output/character_skills/review/direction_c21_20261112_thirdparty/verdict.json)／[findings](output/character_skills/review/direction_c21_20261112_thirdparty/findings.json)／[接收与R01方案](docs/tasks/20261112-c21-direction-receipt-r01-plan.md)／[R01实施回执](docs/tasks/20261112-c21-r01-condition-display.md)／[R01成果](output/character_skills/cycle_reports/C21_r01_20261112/index.html)／[89条条件台账](output/character_skills/cycle_reports/C21_r01_20261112/condition_ledger.json)／[60项验证](output/character_skills/cycle_reports/C21_r01_20261112/verification_detailed.json)／[R01 manifest](output/character_skills/cycle_reports/C21_r01_20261112/final_manifest.json)／[原第三方复验提示词](docs/tasks/20261112-c21-r01-original-thirdparty-recheck-prompt.md)／[最终限定收口](docs/tasks/20261112-c21-r01-recheck-closeout.md)／[复验REPORT](output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/REPORT.md)／[verdict](output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/verdict.json)／[findings](output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/findings.json)／[evidence](output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/evidence.json)／[89条复验台账](output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/answer_ledger.json)／[run_log](output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/run_log.json)／[execution_receipts](output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/execution_receipts.json)。
- **C20历史入口（R02已闭环）**：[收口记录](docs/tasks/20261109-c20-cycle-closeout.md)／[成果页](output/character_skills/cycle_reports/C20_r02_20261109/index.html)／[25答案台账](output/character_skills/cycle_reports/C20_r02_20261109/answer_ledger.json)／[F01最终复验](output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_r02_v01/REPORT.md)。
- **C20原始审查与历史**：[正式独立终审](output/character_skills/review/c20_delivery_final_20261108_deepseek/REPORT.md)／[最终方向复核](output/character_skills/review/direction_c20_20261108_thirdparty_final_recheck/REPORT.md)／[只读验证](output/character_skills/c20_delivery_20261108/checks/validate_formal.json)。原v05与`f01_recheck_v01`的REQUEST_CHANGES／F01 OPEN保留，由R02最终复验承接；R01/R02清单和handoff的PENDING仅表示送审时点，不回写。N01仍为非阻断且未纳入；静态解析与隔离展示复现不构成视觉或运行时验证。
- **C19当前入口（历史）**：[收口记录](docs/tasks/20261107-c19-cycle-closeout.md)／[新版成果页](output/character_skills/cycle_reports/C19_r01_20261107/index.html)／[剩余量](output/character_skills/cycle_reports/C19_r01_20261107/remaining.html)／[R01复核REPORT](output/character_skills/review/direction_c19_20261107_thirdparty_r01_recheck/REPORT.md)／[verdict](output/character_skills/review/direction_c19_20261107_thirdparty_r01_recheck/verdict.json)／[清理与Git任务卡](docs/tasks/20261107-c19-closeout-cleanup-git.md)／[清理回执](output/storage_retention/cycle_closeout_c19_20261107/README.md)／[Git回执](output/storage_retention/cycle_closeout_c19_20261107/git_commit_manifest.json)。
- **C19 Web接收登记（2026-11-08，历史）**：[接收登记](docs/tasks/20261108-c19-web-evidence-receipt.md)／[V01独审REPORT](output/character_skills/review/reader_v01_thirdparty_20261107/REPORT.md)。V01 FIXED、总体PASS_WITH_EXPLICIT_SCOPE_LIMITS，原R01的B01—B03、N01—N06保持FIXED。当时仅登记接收／证据保留，未改主线规则、答案、账本或数据基线；C20随后已由用户另行授权并完成。
- **C19历史前像**：[正式交付包](output/character_skills/c19_delivery_20261107/README.md)／[正式独立终审](output/character_skills/review/c19_delivery_final_20261107_deepseek/REPORT.md)／[原C19成果](output/character_skills/cycle_reports/C19/index.html)／[原方向审查REQUEST_CHANGES](output/character_skills/review/direction_c19_20261107_thirdparty/REPORT.md)。历史报告、送审材料和manifest不改；关联推断、45个未解效果、4行既有split_flags、未实机及第三方浏览器UNTESTED继续保留。其他周期入口见进度页。
- **较早历史入口（C16—C15）**：[C16收口记录](docs/tasks/20261104-c16-cycle-closeout.md)／[C15-R01复验收口](docs/tasks/20261104-c15-r01-recheck-closeout.md)。历史数字、检查范围及推送状态以原记录为准，不在当前入口重复。
- **较早历史入口（C14—C11）**：[C14收口记录](docs/tasks/20261103-c14-cycle-closeout.md)／[C13收口记录](docs/tasks/20261031-c13-cycle-closeout.md)／[C11／C12收口](docs/tasks/20261031-c11-c12-direction-review-closeout.md)。历史冻结成果、原裁决和UNTESTED范围不改。
- **机制优先交接**：[执行细则](docs/tasks/20261104-mechanism-first-execution.md)／[接收对账](docs/tasks/20261104-mechanism-first-reconciliation.md)／[下一批方案依据](docs/tasks/20261104-mechanism-first-next-batch-plan.md)。历史候选仅作回归种子，须按当前版本重新核验，不自动晋级。
- **批18已收口**：[任务卡](docs/tasks/20261025-character-skills-b18.md)、[产物与证据](output/character_skills/b18_20261025/README.md)、[最终独审](output/character_skills/b18_20261025/review/REVIEW_FINAL.md)。既有结果不因本次文档适配重新审查。
- **②历史本地独立发行/干净目录代表复现已完成；保留材料已迁移**：[历史发行说明](operations/history/retired-packaging/20261108/share_bundle/20261025-character-tools/README.md)、[任务记录](docs/tasks/20261025-clean-release-reproduction.md)。`packages_retry/`是当时成功包的历史位置，不是当前使用指引；`packages/`为历史失败诊断。范围及未验证环境按发行说明，不将本地交付写成已公开发布。
- **第二周期第三方审查整改已完成（2026-10-26）**：审查 verdict＝REQUEST_CHANGES（R01/R02 阻塞、N01 非阻塞）→ 修复并正式重建。交付[整改索引](output/character_skills/cycle2_rectification_20261026/README.md)（修复说明、代码差异、190条受影响清单、探针、容量回执、run_record）；campaign `f44c4089…`、snapshot `f44c4089-d3790431153a5dcd`、rules 290键（仅26|param5 unit文案）；verify_full 17/17、账本9/9、A7 29/29；代码定稿两次正式生成同签名、4,472 个卡片产物逐字节相同，隔离目录 16 张代表卡 32/32 相同；旧答案零丢失零改值、范围外零变化、30236/30239逐字节不变、S4 415→415。**后续定向复核与原第三方复审均已通过并收口（2026-10-26，详见进度页历史）**。
- **③新缓存更新暂缓**：`DEFERRED_NO_NEW_CACHE`；有新缓存且用户明确恢复后，按主持交接§4先核版本/差异，再定有界任务。不得自动采集、覆盖latest或恢复HOLD18。
- **其他后续**：HOLD18保持；C8—C13 Git闭包已完成，统一查询CLI及其他语义专项按用户下一安排。当前已有未提交/未跟踪成果，不删除、不批量暂存、不擅自推送。
- **UI样稿**：[独立任务卡](docs/tasks/20261025-ui-reading-preview.md)记录B版主入口已完成、待用户查看，尚未正式整合；其实际在途写入需按任务核实，不在解析批次中接管。

## 存储与事故边界

- **打包保留材料迁移与五入口切换已完成（2026-11-08）**：5,317项／108,004,454 B已迁至 `operations/history/retired-packaging/20261108/` 下的 `share_bundle/`、`distribution/`、`history-work/`；五个C14—C18正式隔离入口均指向新 `share_bundle`，各142文件验读及Sol验收、Astra独立复核通过。见[物理回执](docs/project-layout/20261108-packaging-physical-v1/REPORT.md)、[Astra独立复核](docs/project-layout/20261108-packaging-physical-v1/physical-independent-review.json)。previous旧联接已清理，不作当前读取入口；只读维护入口为 `scripts/project_layout/retirement_runtime.py`。1,607项旧文件已按最终授权逐项删除，临前archive模式1,406对检查及后验通过；5个停用previous联接及9,467个旧空目录已按后续授权清理；9个必要祖先目录、11项原位文件及归档材料保留。见[空目录清理回执](docs/project-layout/20261108-packaging-empty-cleanup-v1/REPORT.md)和[此前文件删除回执](docs/project-layout/20261108-packaging-final-ready-v1/deletion-20261108-v1/REPORT.md)。
- **打包支线退役后续统一整合（2026-11-08）**：退役条目已交执行对话，主线继续；现有导航保留，最终执行及独立复核见[清理收口任务](docs/tasks/20261108-packaging-empty-cleanup.md)。1,607项授权旧文件及后续5个previous、9,467个空目录已清理；必要证据／恢复归档继续保留，主线可继续。


- **旧包退役V2已完成**：[第三方执行报告](output/storage_retention/export_cleanup_review_20261025/REPORT.md)、[删除后验收](output/storage_retention/export_cleanup_review_20261025/postcheck_result_20261025.json)、[任务卡](docs/tasks/20261025-export-cleanup-inventory.md)。用户已确认执行，第三方删除与后验均完成；清单授权已履行，不再运行旧提示词。44份隔离输入、当前发行包、旧报告与元数据保持；两旧完整快照已退役。未释放构建预约，不扩大其他清理。
- **容量**：沿用方案§8及进度页当前记录；后续正式重建先核容量，处置依新的具体清单，不能复用已履行的删除授权。
- **事故与旧整改**：[事故唯一边界](output/20261024-project-review/incident_command_20261024/README.md)、[处置收口与残留缺口](output/20261024-project-review/incident_command_20261024/incident_closeout_20261024.md)。恢复线按残留缺口收口，R3归属/选题链已关闭；永久防误删设计定稿、代码未实施，不写成事故全部解决。
- **存储治理**：沿用方案§8.1与[任务卡](docs/tasks/20261024-storage-governance-plan.md)，待用户安排启动；不作为主线前置，不因规范适配启动代码、删除或新的审查流程。

## 按需查阅

- 解包使用方法：[README.md](README.md)；缓存、APK、媒体及既有证据入口见AGENTS定位表，原件保持不变。
- 当前规则：`output/character_skills/profiles/rules.json`；逐卡答案：`output/character_skills/pages/<cid>/card.json`。旧`query_effect_dictionary.py`不读取这套新答案，统一只读CLI尚未交付。
- 历史阶段概况：[STATUS.md](STATUS.md)；[旧HANDOFF正文](STATUS.md#handoff-history-20261025)原样转存，独有历史证据及原链接保留。仅按相关版本查阅，不通读全部历史或重跑A—E。

本次轻量适配只修文档入口与执行规则，完成记录见进度页；后续实施仍以用户当次任务为准。
