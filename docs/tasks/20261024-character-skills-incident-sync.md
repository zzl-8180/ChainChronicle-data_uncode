# 事故指挥·有界正式同步（代码保全＋账本快照同步＋当前交接更新）

- 任务 ID：20261024-character-skills-incident-sync
- 负责：主持 Kimi K3（唯一写入整合者）；任务书来源：总指挥（Codex `01a16a26-…`）经用户转交（`output/20261024-project-review/incident_command_20261024/ZCODE_HOST_TASK.md` 与用户指令）
- 状态：**本轮代码保全、账本快照同步和当前交接更新完成，待总指挥验收；历史恢复缺口仍未全部解决**
- 范围：仅步骤 A（代码保全）＋B（四份已核验账本文件提升）＋C（下游核对＋当前入口更新）。不恢复连续批次授权、不重建页面、不重新解包、不重跑账本生成器、不推进新数值研究、不清理、不改配对语义、不提交推送 Git、不发布。

## 步骤 A：代码现场保全

- 目录：`output/character_skills/incident_sync_20261024/code_scene/`（本轮独立目录，未写入独立核验目录）。
- 内容：git/（HEAD.txt＝`b297118…`、status_porcelain.txt、diff_tracked.bin 390,462 字节——subprocess 原始字节写入无文本编码转换）＋sources/（90 个文件完整内容：scripts/character_skills 全部 .py＋选题三脚本＋regen_readme28＋rules.json＋characters.csv＋campaign 指针与所指报告/审计队列）。
- 清单：`manifest.json`（相对路径＋SHA-256＋大小＋是否已跟踪＋保存位置＋范围说明）。
- 复用核对：与独立核验 `ledger_audit/sources/` 重叠的 8 份源码哈希 8/8 一致；旧正式账本四文件与 `ledger_audit/before/` 4/4 一致。

## 步骤 B：四份已核验账本文件提升

- 前置核对全过：无其他任务在读写正式账本（无在途 workflow）；`input_freeze_after.json` 复核——2,236 卡 card.json 哈希 0 失配、manifest 一致、14 个其他输入（rules/源码/指针）0 失配；旧正式文件与 before/ 4/4 一致；candidate 四文件 SHA-256 与 `delivery_checks.json` 4/4 一致。
- 执行：逐文件二进制复制（candidate→正式）；记录 `output/character_skills/incident_sync_20261024/step_b_sync_log.json`。
- 后置：四文件与 candidate 逐一相同；正式 metrics 的 snapshot_id＝`c019af0b-57a14d29a773f3b7`、campaign＝`c019af0b…`（对应已核验版本）；业务指标不变（完整 4,378／部分 76／未解析 9,125／拆分 28,086；backlog 79,121）；未重跑页面/账本生成器/A7/历史审查。
- 原生成命令的 exit 1（末尾 GBK 无法编码「↔」的 print 错误）如实保留，未为修饰退出码重复生成；后续确需运行时用 `python -X utf8`。

## 步骤 C：下游关系核对

- 选题链实际消费账本的字段：enrich_records.py（`record_type`/`effect_id`/`span`）、assign_candidates.py（`record_type`/`description_ref`/`span`/`effect_id`）——全部为非锚点内容字段；backlog.json 字节一致。独立核验已证明旧↔新非锚点字段零差异（`ledger_audit/REPORT.md`＋`comparison.json`）。
- 结论：**消费字段完全等价→保留现有候选产物**。其原生成快照＝metrics 锚点 `a2dc963c-57a14d29`（backlog 79,121、rules `57a14d29`）；与当前账本的关系：内容一致、仅快照身份与时间推进到 `c019af0b`（依据 `ledger_audit/` 的等价性核验）。未手改候选 meta 冒称重新生成；未仅为更换锚点重跑选题链。
- 例外如实注明：metrics.json 的锚点字段（campaign_signature/snapshot_id）被 assign_candidates 读入 meta.backlog_anchor——现候选 meta 中的锚点引用的是同步前的历史快照记录（其内容口径：backlog 79,121＋rules 哈希不变，仍真实）；F03 的下一代生成记录规则不受影响。

## 当前入口更新

- `docs/tasks/character-skills-progress.md`：当前状态行＋接手摘要更新（见下节）。
- HANDOFF.md 顶部入口此前已含总方案/进度/任务卡链接，本轮无需再改。
- 历史报告不改、历史数字不机械替换。

## 恢复缺口与限制（如实保留）

- 恢复：7,980 文件已恢复（首批 7,938＋后续 42，均原 SHA-256 验证）；仍缺 4,072＝755 批 8 基线 JSON（阻塞批 8"非本批零变化"完整历史复验）＋302 早期轮次 JSON＋3,015 HTML（旧页面字节/回滚现场）。文件缺失影响今天的复验能力，不直接反证旧报告的数值结论；不写成"全部恢复"或"历史审查全部重新通过"。
- 六脚本缺件防护已由原清理对话完成（17 项防护测试通过、58 份旧审查/比较结果哈希未变），本轮未重复修改。
- R3 sentence 已有 DSH 复验结论（PASS_WITH_EXPLICIT_SCOPE_LIMITS、归属/选题层全局闭合）；**原 Codex 审查者的最终确认尚未执行，不冒称已获得**。
- MANA 空集序列化 null 的 Low 债务按原审查限制继续登记，本轮未搭车修改。
- F03 生成记录与 A7 保存步骤：执行安排已明确，**实际运行验证待下次正常运行**。

## 最近更新

- 2026-10-24：任务卡建立＋三步执行完成（证据见各节与 `output/character_skills/incident_sync_20261024/`）；待总指挥验收。
