# 项目文件夹清理：只读盘点与安全处置提示词

```text
你负责《锁链战记数据解包》项目文件夹的只读盘点与清理候选整理。项目根：E:\代码项目\锁链战记数据解包。命令统一用 ./.venv/Scripts/python.exe -X utf8 -B（Windows 中文路径，避免 GBK 输出问题）。

【最高原则：先盘点、后批准、再删除】
本项目 2026-10-24 已发生过清理事故（误删固定读取备份，7,980 恢复、4,072 不可恢复）。你本轮默认只做只读盘点和候选清单，不做任何删除、搬移、归档、清空回收站、Git 操作、发布或联系其他对话。任何具体删除必须等用户逐项批准精确清单后才可进行，且只能按下面"安全处置模式"执行。禁删闸门＝永久防误删机制验收 PASS 或用户明示解禁；该机制目前未实施，所以你无权自行放行任何删除。

一、先读（限定入口，不通读全部历史）
1. AGENTS.md 的 §4、§5、§6、§7.1、§8、§8.1（证据、文件分类、必要依赖、容量与防误删）。
2. output/20261024-project-review/incident_command_20261024/README.md 与 incident_closeout_20261024.md（事故边界、不可恢复清单、禁删闸门）。
3. scripts/storage_retention/README.md（容量保留机制；state.json 只能由保留工具修改，你不许改）。
4. output/storage_retention/export_cleanup_review_20261025/REPORT.md 与同目录 postcheck_result_20261025.json（旧 10/21、10/22 角色分享 ZIP 及展开件已由第三方删除并后验 PASS，**不得重复执行旧删除清单或扩大清理**）。
5. docs/tasks/character-skills-progress.md 顶部当前状态与各任务卡（判断在途写入，不得凭目录名或时间猜已停止）。

二、禁碰清单（写入、删除、搬移都不许）
- 原件与输入：APK、raw/、output/base_master/、output/cache_full_20261015_v3/、output/cache_refresh_20261015*。
- 44 份隔离输入、当前发行包 output/share_bundle/20261025-character-tools/（含 packages_retry 三包与清单；packages/ 为失败诊断包，仅可列为可选候选，不自动删）。
- 恢复材料 work/protection/、原生证据目录（output/character_skills/boss_heal_types、boss_attack_types、ordinary_effects、output/boss_chain）。
- 当前正式产物：output/character_skills/pages/、profiles/、effect_ledger/、各批次输出与回执、全部独立审查目录 output/character_skills/review/**（只读）。
- 在途输出：output/character_skills/s5_nonterrain_20261026/、output/character_skills/inference_inventory/g0_g1_g7_precheck_20261026/ 及后续批2/批3目录。
- .venv/、tools/、.git/ 与工作区未提交文件（禁止 reset/clean）。
- §7.1 必要依赖：选题链脚本与产物、A7 套件、冻结审查证据（如 coverage_refined.json）、R3 重放保全、各 run_record/签名/receipt。

三、盘点要求（只读）
0. **先按"实际还有没有消费者"分类，而不是按名字和感觉**：①现在的生产脚本还读它吗？②验证"当前版本"还用得上它吗（独立审查/隔离复现/发行包复现）？③它是原件或不可再生证据吗？三个都答"否"的，即使目录名看着重要，也属"其实已经没用了"的复盘材料（如历代重复 run 备份、各批隔离复跑树、一次性 scratch/探针、失败诊断包、旧分析 ZIP、nul）。**但注意**：原生证据（boss_heal_types/type_rules/native_checks/ordinary_effects/boss_chain）是当前规则和答案的证据母体不是复盘材料，冻结审查证据与恢复材料不可再生，都必须留；当前发行包与 44 份隔离输入在用户有分享意图时保留。
0.1 **时点警告**：本周期满 3 批后还有第三方独立审查，其"旧答案零变化"验证要读本周期各批的前像备份（previous_pages_compact.json.gz、各 run backup/card.json）——这些在审查完成前一律进 C 禁删，不得因"复盘材料"名义提前清理。
1. 先量体积：按目录给出占用（work/、output/、_batch、发行目录、根目录杂项），列大文件/大目录，不凭感觉。
2. 候选分三类并逐项给证据：
   A. 可删重复件：路径、SHA-256、字节数、存活同哈希副本位置（当前正式页/较新 run/保留区之一）——没有存活同哈希副本的一律不得进 A。
   B. 可再生的中间产物（如隔离复跑树、scratch）：体积、生成命令与声明输入、为什么能按声明输入重建、当前是否仍被任务引用；不能被当前任务引用的才候选。
   C. 禁止项/待决项：凡在禁碰清单、证据不足、或无法证明可恢复/可重建的，一律进 C 并写原因。
3. 特别标注易错点：与当前正式页"相同"的备份只说明它无额外回滚信息（可进 A），"不同"的备份常是真正历史版本（进 C，不得删）；最近重建会改哈希，判断必须基于文件内容而非目录名/时间。
4. 已知可关注位置（仅为线索，须逐项验证）：_batch 各 run 的重复 backup、work/ 下隔离复跑树（每棵约 450MB）、packages/ 失败诊断包（约 1.85GB，交付只用 packages_retry）、根目录 nul 杂散文件、旧 work/review_* 目录（含冻结证据者进 C）。

四、交付（本轮唯一输出）
- 一份盘点报告（新目录 output/storage_retention/cleanup_inventory_20261026/，只新增不覆盖）：体积表、A/B/C 候选清单（逐文件路径/哈希/字节/消费者/可恢复性/建议）、禁碰与在途核对记录、拟释放空间的上下界估计。
- 不执行任何删除。报告交给用户逐项批准；获批后的执行也必须走"安全处置模式"：逐件执行时重算 SHA-256 与清单一致才动、删除件必须有存活同哈希副本、不同件一律无损保留并记录映射、元数据全留、写回执与后验（删除路径均有存活同哈希副本证明、保护面哈希前后一致），retention/state.json 只能由保留工具修改。
- 报告须明确：本轮未删除任何文件、未做 Git 操作、未联系其他对话、未启动新研究或原生提取。
```

- 使用方式：新对话先跑只读盘点，清单回来你逐项勾选后再谈执行；不要让它一口气"直接清理"。
