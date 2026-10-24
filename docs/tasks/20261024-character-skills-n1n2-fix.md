# N1/N2 有界补修（原 Codex 最终复验两个残留根因）

- 日期：2026-10-24；负责人：Kimi K3（主持，本轮亲自动手，不派发实施/审查代理）
- 状态：**已交付，待总指挥独立验收及原 Codex 复验**（2026-10-24）
- 依据：用户本轮任务书（"本轮仅执行 N1/N2 有界补修，交付后停止，等待总指挥独立验收及原 Codex 审查者复验"）＋原 Codex 最终复验 `output/character_skills/review/r3_f1f2_chain_codex_recheck_20261024/REPORT.md`（REQUEST_CHANGES，唯二阻塞 N1/N2）＋总指挥复验验收 `output/20261024-project-review/incident_command_20261024/final_recheck_acceptance_r1/REPORT.md`。

## 目标（仅限两项）

- **N1**：「攻撃した際」反响触发被误判无共享依据。`89-special_move-special_move-pattern0-lvorder0-f1#e00`（nonYG）与 `350-denju-denju-denju_denju_id____cid-lvorder0-f1#e00`（view）应得 YG3/sentence 归属及 shared 依据。根因：`_COND_TAIL_RE`/`_TRIGGER_TAIL_RE` 含「時」不含「際」。
- **N2**：`223-denju-denju-denju_denju_id____cid-lvorder0-f2#e00`（nonYG）「その後、味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。」的对象/时长修饰语（「味方全体のHPを一定時間」）与回复谓语承接被误判 undetermined→G9。应归 G7/sentence 并给出正确共享依据（仅保留 G7 为附加候选不算修复）。根因：肯定依据仅接受条件词尾，遗漏无谓语修饰短语对后接谓语的承接。

## 禁止事项（任务书原文边界）

不按 CID/effect ID/完整原句硬编码；不恢复"没有冲突就等于共享"；不将所有"際/時"、相邻子句或跨顿号片段一律判为共享；不将包含完整独立动作的前段当作未完成对象短语；不整体回滚 F1/F2、不放松头标记正文检查、不重构为通用日语解析器。保留：F1 原反例、F2 头标记正文检查、MANA 负例、四卡14项 Chain 修复、原7反例、349子句优先、跨顿号既有具名修复及11024/11039/11233、合法后备条件（G8 サブパーティ例）、自身状态异常时长/恢复正例。不启动其他代理或审查对话；无依赖变化时不重建页面/账本；不删除/恢复历史文件、不清理、不装依赖、不提交/推送 Git、不上传发布。

## 写入范围

- 改：`work/character_skills_yg_priority/assign_candidates.py`（仅此一生产文件）
- 建：`work/character_skills_n1n2_fix_20261024/`（保全、探针、验证、影响证据）
- 晋级（核验通过后）：`work/character_skills_yg_priority/yg_candidates.json`、`yg_candidates_items.json`
- 一次性入口同步：`docs/tasks/character-skills-progress.md` 当前块、`HANDOFF.md` 指针、本任务卡
- 其他一律不写（页面/账本/规则/其他脚本不动）

## 设计（已核对代码与声明表）

- N1：`_COND_TAIL_RE` 与 `_TRIGGER_TAIL_RE` 增补「際」形态（際/際に/際は）。机制不变：词尾命中后仍须过机制词族兼容检查（`_positive_shared_evidence` 第②类）——YG3.types 含 ダメージ（词表外）/回復（词表外），89/350 兼容；含不兼容族机制词的「際」子句仍拒绝。与「時」同等待遇（配对探针已证 際→時 即恢复 shared）。
- N2：新增肯定依据③「修饰语承接」：kwcl 无谓语（含 を/が 对象标记或时长/频次名词、无动作谓语）＋句内紧邻下一子句＝本效果自身子句＋自身子句无与 kwcl 对象冲突的显式目标 → shared（依据文本注明承接结构）。谓语词表按全语料子句尾形态实测落地（探针先行）。F1 反例形态（含完整独立动作的前段：…した／…する）被谓语检查排除，不适用本规则。

## 验证与证据（对应任务书 §四/§五）

1. 真实重建输入：89/350/223 从页面＋账本 span 重建，修后分别 YG3/sentence/shared、YG3/sentence/shared、G7/sentence/shared（承接依据）。
2. 正例配对：際/時 同义配对（89 改造配对）；223 型承接合成正例。
3. 负例：已完成前段动作不共享（F1 三反例 30109/30249/30330 保持 G9）；对象切换不继承；含完整谓语前段不判承接；MANA/状态配对不变；标记不免检正文（F2）；Chain 阈值/机制词边界保持；G8 サブパーティ合法后备、自身状态异常时长/恢复正例保持。
4. 全量影响证据 C(9528f763)→新：view 10,939＋nonYG 68,182 逐项全字段（cand/context_basis/also_candidates/skill_tags/also_basis/fallback_reason/sentence_fallback）比较、变化原因分类、候选池保留核对、ID 集合对账、失败登记不跳过；变化项附原文/子句/语境。
5. 三版本身份：沿用 A/B/C 清单，新增 C→新 的执行副本身份与输入哈希（replay_manifest 同法）。

## 验收后可报告「本轮实施完成、待独立复验」的条件（任务书 §七）

五项同时满足才可如此报告：① N1/N2 真实项修复成立（真实重建输入）；② §四全部正负边界通过；③ 保留清单回归通过（F1/F2/Chain/MANA/349/跨顿号/后备）；④ 全量影响证据落盘且候选池零丢失、失败零跳过；⑤ 产物晋级与入口同步完成、meta 锚点诚实。

## 停止边界

交付后立即停止，不自行派发复审，不继续下一轮。交付结语按任务书 §八："本轮仅完成N1/N2有界补修及自验，已停止，等待总指挥安排独立验收与原 Codex 复验"。

## 最近更新

- 2026-10-24：任务卡建立。已实读当前分类器（9528f763）相关函数、EFFECT_TYPE_LIMITS（YG3.types 兼容 89/350 效果类型）；实测当前候选 view 10,939 项中 sentence_fallback.klass=undetermined 为 0（undetermined 落入 fallback 路径、体现在 fallback_reason/also_basis）；89/223 不在 view 集（nonYG）。evidence-completion 轮的 capture_full_impact.py/replay_manifest.py 工具链可复用。
- 2026-10-24：**交付**。实施完成（C `9528f763`→D `f9ce04a9`，diff 80 行含注释：N1 词尾表增补「際」形态、N2 新增 `_modifier_continuation` 承接规则，无 CID/ID/整句硬编码）。自验：`verify_n1n2.py`＋`finalize_pool_check.py` 合计 **58/58 PASS**——三目标真实重建输入修复成立（89/350→YG3/sentence/shared、223→G7/sentence/shared）、際/時 同义配对成立、全部负例与保留清单（F1 三反例、MANA×2、状态/HP×2、G8 后备、Chain 阈值/机制词边界、14 项 Chain 触发、349×4、30225、350-ability、11024/11039/11233、自身状态异常正例）保持。全量影响证据 `impact_evidence.json`：266 项（view 39/nonYG 227），归因 N1 137＋N2 129、待语义核查 0；候选池精化口径零丢失（54 项 G9 兜底被真实归属替代逐项断言）；失败 0/0；ID 对账 79,121=10,939+68,182；取证与真实生成路径交叉一致（39=39）。正式候选产物已晋级（正常路径重建，与验证 scratch 去 generated_at 逐字节一致；meta 诚实记录 D 哈希；锚点 c019af0b-57a14d29 不变）。证据索引与限制见 `work/character_skills_n1n2_fix_20261024/README.md`。入口已一次性同步（progress 当前块＋HANDOFF 指针）。**已停止，不自行派发复审。**

## 下一步

（冻结）等总指挥独立验收＋原 Codex 复验；其后动作由用户/总指挥决定。
