# F1/F2 最小补修：合法 Chain 触发误判＋nonYG 逐效果影响证据

- 任务 ID：20261024-character-skills-chain-trigger-fix
- 负责：主持 Kimi K3（唯一写入整合者；本轮按总指挥任务书由主持直接实施，不启动其他代理或审查对话）；验收：总指挥安排（原 Codex 独立复验尚未执行）
- 授权来源：用户 2026-10-24 转交总指挥验收报告（`output/20261024-project-review/incident_command_20261024/f1f2_acceptance_r1/REPORT.md` REQUEST_CHANGES_BEFORE_FINAL_REVIEW：阻塞 A 合法 Chain 触发误判＋阻塞 B nonYG 逐效果证据缺口）
- 状态：**最小补修及自验完成，待总指挥安排原 Codex 独立复验**（不冒称 R3 全局闭合）

## 基线（实读核实）

- 当前分类器 assign_candidates.py SHA-256＝`22bc1478e889badf…`（F1/F2 修复版）；F1/F2 修改前保全版在 `work/character_skills_f1f2_fix/pre_fix/`（SHA `bfdbe188…`）。
- pages campaign `c019af0b`；正式账本快照 `c019af0b-57a14d29`；当前候选绑定 `c019af0b-57a14d29`（上轮已重生成，不再写 a2dc963c）。
- 阻塞 A 证据：14 项（30243/30256/352/4316），触发片段「【共鳴アビリティ】1stChain以上で自身を含む<味方>が≪共鳴必殺≫を発動した時」——Chain 门槛触发条件被机制词表判为 G4 兄弟机制（类型不兼容拒绝）。

## 修法（最小）

- `_mech_words_of` 增加阈值语境排除：序数阈值/达成形态（`\d+(st|nd|rd|th)Chain（以上|を達成|が\d|の数が）`）中的 Chain 不登记为 G4 机制词（与「属性防御力」负向断言同法）；机制型 Chain（「同じChain内で」「Chain数に応じて」「Chainによる威力」）不受影响。全库词形已实测：阈值形态 1,334 处（496+376+144+84+130+120+100…）、机制形态 1,810+396+100+140…。
- 效果：触发片段剥离标记后无机制词＋触发收尾→合法共享；G4 命中保留但按类型兼容如实写「合法共享触发条件（类型不兼容不作主分类）」，不再写「未登记兄弟机制」；各项原有主分类（如有依据的 G2 等）不动。
- 禁止项：不按 4 CID/14 ID 硬编码；不恢复"有标记即整段共享"；不把全部 Chain 命中认作共享或全降 G9；不删类型检查/上下文/附加候选/待办。

## 允许写入

`work/character_skills_yg_priority/assign_candidates.py`（本修复）＋ `work/character_skills_chain_trigger_fix/`（本轮保全/验证/影响证据）＋ `work/character_skills_yg_priority/yg_candidates*.json`（验证通过后提升）＋ 本卡 ＋ `docs/tasks/character-skills-progress.md` 与 `HANDOFF.md`（一次性同步）。不动：pages/正式账本/rules/旧审查/旧保全副本。

## 最近更新

- 2026-10-24：任务卡建立；验收报告与 14 项证据已读；全库 Chain 词形分布实测完成；修法已定。
- 2026-10-24（实施与自验完成）：①实现——`assign_candidates.py` 的 `_mech_words_of` 增阈值语境排除（`_CHAIN_THRESHOLD_RE`：序数/达成形态 `\d+(st|nd|rd|th)Chain（以上|を達成|が\d|の数が）` 中的 Chain 不登记为 G4 机制词，仅当全部出现处均为阈值语境才排除；机制型 Chain（同じChain内で/Chain数に応じて/Chainによる威力）不受影响；新分类器 SHA `9528f763c383…`）。②验证（`verify_chain_trigger.py` 23/23 PASS，全部实跑）：**14 项触发误判全部消除**（30243/30256/352/4316——触发片段现为合法共享，G4 命中的 also_basis 准确写「合法共享子句…；类型不兼容不作主分类」而非「未登记兄弟机制」；14 项主分类为 YG2/sentence＝其技能真实家族（共鳴アビリティ），依据为触发片段含【共鳴アビリティ】标记且 sympathy 语境在 YG2 声明 page_groups 内）；配对负例（MANA plain/header、cleanse plain/header）保持 G9；G8 合法共享正例保持；F1/F2 套件重跑 18/18。③**影响证据**（`impact_evidence.json`，三版本隔离重放）：本轮增量（22bc1478→本轮）view 343 项＋nonYG 72 项全部限触发/共享判定路径；其中 **160 项为 A→B→A 回返**（F1/F2 误伤的触发项被恢复至 bfdbe188 状态，逐项核验一致）＋183 项仍不同（F1/F2 保留的变化）；累计净影响（bfdbe188→本轮）view 330＋nonYG 663；主分类翻转仅 G2→YG2 8 项（sympathy 项归其真实技能族）。④提升：assign_candidates 正常路径重跑，正式产物与 scratch 逐项一致（meta 时间戳除外）；meta 三脚本哈希实测一致；锚点 c019af0b-57a14d29；verify_r3fix 提升后 9/9 PASS。⑤页面/账本/rules 零触碰（无依赖变化不重跑）；未 Git；未动旧审查/旧保全。⑥重放副本 `replay_f1f2.py`/`replay_orig.py`（仅 ROOT 与链目录定位两行适配）与三版本产物在本目录留档。
