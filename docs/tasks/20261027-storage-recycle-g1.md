# 回收方案G1材料交付（已收口，G2阻塞）

用户本轮明确授权G1：开发工具、创建A归档、验证恢复，仅用合成夹具测试回收站。真实候选G2未获批准；G3永远由用户本人操作，代理不实现最终释放。
负责人：本盘点对话；两个Sol子代理负责互不重叠模块，父代理整合。不得修改其他任务或撤销其工作。
写入范围：scripts/storage_retention/recycle_v1/；output/storage_retention/recycle_g1_20261027/；output/storage_retention/vault_g1_20261027/；work/storage_recycle_g1_20261027/；本任务卡。
主代理：protection_manifest、plan_manifest、A/P候选、方案修订、归档执行和验证整合。
archive子代理：archive_store.py、test_archive_store.py及其README_ARCHIVE.md。
recycle子代理：recycle_fixture.py、其可选C#辅助与README_RECYCLE.md；只读配额检测和独立合成夹具测试。
共享依赖：只复用.venv，不安装/升级；不改HANDOFF/STATUS/进度、retention/state.json、正式源码或输出；不Git、不联系既有对话。
保护：W排除；M暂缓；P仅三个成功ZIP且保留历史小闭包/隔离树/44输入。当前/旧93eb61e1/095905/本周期前像/独审及其证据永久保护。追加当前campaign保护。
当前终态：归档和恢复通过；回收能力未验收，保护面7处变化/2项临时产物退役需主持确认。入口 output/storage_retention/recycle_g1_20261027/REPORT.md 与 HOST_REVIEW_PROMPT.txt。所有本任务进程已结束；不执行G2，不重跑已完成归档。

用户要求暂停并切换6.1 Sol High：归档和后验等待进程均已停止。以output/storage_retention/recycle_g1_20261027/PAUSED_HANDOFF.json为当前停点。归档未验收，不运行complete_g1/finalize_g1，不自动重启、不覆盖、不删除。G2仍未授权。

用户已明确恢复G1（6.1 Sol High），要求复用进度。采用archive_store_resume.py原位只新增续建，复用6个已闭卷与67359映射；原index/log/未封口7卷原样保留。真实文件仍不回收。以RESUMED_HANDOFF.json和随后终态为准。

G1交付：A归档/恢复/最小消费者完成；真实回收能力BLOCKED，G2未申请/未授权。以output/storage_retention/recycle_g1_20261027/REPORT.md和FINAL_SUMMARY.json为准；G3禁止代理实现。旧RUNNING_HANDOFF是历史记录，不表示仍有活跃构建。

## 主持复核后的补齐（2026-10-27，进行中）
用户要求按缺口1→8顺序补齐。当前仅开发/验证真实Shell合成夹具后端，不回收任何真实候选；第三方方向审查已启动，可并行，只读保护所有主线/独审/周期前像。保护基线与回收前源hash待第三方审查及修复收口后再冻结。用户已自行清空旧回收站，后续重新只读计量，不使用旧4.32GiB作为现有占用。
新增独立输出：output/storage_retention/recycle_g1_20261027/shell_validation/，本任务scripts/work根；既有报告/归档不覆盖不重跑。

## 当前状态：用户要求暂停，等待第三方审查收口
2026-10-27：用户选择主线第三方审查及修复全部完成后一次性核对，本任务暂停。主持复核后仅只读查阅Shell官方文档及记录协作范围，未启动真实Shell测试/后台流程，未回收真实或合成文件。停点 PAUSED_PENDING_THIRDPARTY_20261027.json。既有归档与恢复PASS保留；不重跑归档。待用户明确审查/修复已收口再按缺口1→8继续，G2仍BLOCKED且未授权。

## 接任补齐（2026-10-27，本对话接任，按缺口1→8）
用户交接授权恢复G1；第三方审查已收口（direction_cycle3_20261027_thirdparty，verdict=PASS_WITH_EXPLICIT_SCOPE_LIMITS，阻塞0）。本对话负责持续跟进，写入 followup_after_review/（只新增不覆盖）。当前进展：

- **环境前提**：当前进程已回正常本机上下文（app_container=false），SHQueryRecycleBinW 返回 0（用户已清空旧回收站），IFileOperation 激活成功，回收站目录可枚举。此前 AppContainer 拒绝访问的记录不再适用。
- **缺口1（已验收）**：真实 Shell 合成夹具后端 recycle_shell_backend.py（1307 行）开发完成。阶段A 安全闸门逐条通过；阶段B 最小样本闭环；阶段C 完整矩阵 8 PASS/0 FAIL/1 BLOCKED/1 UNVERIFIED。真实入站→自身条目定位→同 hash 恢复在中文/空格、同名异目录、8MiB、HTML 关联不连带、失败、取消、部分成功、新进程续跑闭环。**长路径（>260）是平台限制**（Shell 走永久删除，fail-safe 保源）；OS 重启未实测。关键修正：TSF_DELETE_RECYCLE_IF_POSSIBLE=0x80（非 0x40）、SHCreateItemFromParsingName 拒绝 \\?\ 前缀、真实 $I name_len 含结尾 NUL。记录：followup_after_review/20261027-gap1-{shell-backend-scope,stageA-review,stageB-review,stageC-review}.md、gap1_stage{A,B,C}_*。
- **缺口2（诚实停报）**：配额充足性无法证明（磁盘空闲 73.3 GiB < 约117GiB门槛；MaxCapacity=27647 不推单位）。记录：followup_after_review/20261027-gap2-quota-assessment.md。
- **缺口3（已闭合）**：动态 UNKNOWN 闭合。唯一真实交叉是 replay_guard 经 validate_restored_consumer 读的 38 文件/33,523,249 字节，须移出候选保护。记录：followup_after_review/20261027-gap3-dynamic-consumers-closure.{md,json}。
- **缺口4（已建立）**：完整保护基线 96318 文件/43.16GB 逐文件 hash，错误0/不稳定0；计数对账 10528/43/38/33/26 全对上；7 处变化 6 稳定 + 1（character-skills-progress.md 活文档）postcheck 后又变化已按最新值冻结；2 缺失件退役接受、三份 compact SHA+计数全对上。记录：followup_after_review/gap4_protection_baseline_*。
- **缺口5（用户已决策）**：用户选方案A，接受小闭包替代同 hash 副本，P 保管形式闭合。用户同时明确"先不要执行删除"。记录：followup_after_review/20261027-gap5-p-contract-decision.md。
- **缺口6（已完成）**：同轮源 hash 重算 + 归档/保护/恢复健康全部 PASS。候选 196905 文件源 hash 重算 same=196905/different=0/error=0，长路径候选量=0（不影响真实候选）；保护集合同轮 96317 same + 1 变化（缺口5 决策文档，本任务自身 followup，良性）；归档 verify PASS（207433 路径/90778 内容/10 卷 readback 全过）；恢复 restore PASS（39 路径）。记录：followup_after_review/gap6_*。
- **缺口7（批准稿已写）**：journal 批参数批准稿已写（精确 SHA 待缺口6 回填）。记录：followup_after_review/20261027-gap7-journal-batch-approval-draft.md。
- **缺口8（已验收 PASS）**：永久防误删机制按流程验证到 PASS（防护链 7 层核实 + 长路径真实永久删除风险实测保源）。用户要求不执行删除。但缺口8 的另一半"精确 G2 清单 SHA 逐项批准"仍未满足（待缺口6/7），故 G2 仍 BLOCKED。记录：followup_after_review/20261027-gap8-permanent-delete-safeguard-review.md。

G2 仍 BLOCKED 且未授权；真实候选绝不入站。回收站现有 16 个本任务产生的合成夹具条目（约16MiB，非真实候选），G3 由用户决定。所有新命令统一 ./.venv/Scripts/python.exe -X utf8 -B。
