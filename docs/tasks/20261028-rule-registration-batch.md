# 新周期批2：专门规则登记批（100/102/19/1033 走 register_rule 序列化）任务书

- 日期：2026-10-28。状态：**已收口，独立初审 PASS、零阻断、无残留**（独审 `dwfrun-3fe46ad5-e7cf-457f-98f9-8c6ec623fe84`，V4 Pro GA high；报告 `output/character_skills/review/rule_registration_20261028_deepseek/REPORT.md`：指纹门/等价性门/白名单/分表/单一事实源/保护项/过程容量/L1 闭合八项全部独立重算通过；165 条答案从原始主表独立重算零 mismatch；批1 残留①闭合）。独审注明：verify_full/账本/A7/F03/隔离复跑/scratch/INC 回执为读取实施回执而非独审重跑，其数值结论已由独立重算覆盖；HOLD18 status 未重跑 analyze_row 但 row_hash 字节级相同可纯函数推论。**L1 结构边界正式关闭：rules.json 294 键已是四键族完整规则清单**。新周期第 2/3 批收口。实施 `dwfrun-0afb131a-32a1-4a37-a81a-5644c1137001` 完成：rules.json **290→294 键**、SHA-16 `d3790431153a5dcd`→`cf9451c6ff47fcfb`；旧 290 键逐键 canonical SHA 290/290 不变、新增恰四键（指纹门 PASS）；等价性门重建前后各 165/165 PASS（含来源限定门：仅显式 source_layer 可取，防止对另 157 记录/141 卡新增 BY_TYPE_EXTRAPOLATED 答案，guard_violations=0）；单一事实源＝rules.py::_registration_20261028_specs、两模块改 rule_for/answer_for 读取；SLOT_EFFECT 按能力分表、16 条 type80 param7 effect_type 已纠正。campaign `81362bb917711647e4a05dd44549a1a7a298802d827de32d81a724abd8e2cab9`、snapshot `81362bb9-cf9451c6ff47fcfb`；**指标零漂移**（has_answer 19,920／backlog 75,900／identified 69,873／A 18,330／C 23,335）；final_diff PASS（676 变化叶＝660 登记状态＋16 effect_type，无第三类）；隔离复跑 18/18 逐字节；scratch 前后各 21/21；verify_full 17/17、账本 9/9、A7 29/29；容量 postcheck PASS 上限未放宽（建后 12/12、7.242 GiB）；jobs 4。实施期 INC-1..3 已修并留证据，登记失败那次按安全阀恢复原字节。新周期第 2/3 批。
- 来源：第四周期第三方向审查范围限制①（100/102/19/1033 规则仅在模块 RULE_SPECS、未入 rules.json，跨批消费者不得只凭 rules.json/answer_for 判定这些槽位无规则；建议专门登记批走 register_rule 序列化）及复审 L1（结构性边界，直至本批落地）。登记 `docs/tasks/20261028-cycle4-review-closeout.md` §二/§四。
- 规则引用：`docs/角色技能完整解读实施方案.md`（含§1.3）；自动推进规划与满3批停审指示。
- 当前版本以开工实测为准（上一批 campaign `6d8c793c6e54aa4815575e1791a0c7ff9601d580d3387a550fa8b7f45c28edc8`、snapshot `6d8c793c-d3790431153a5dcd`；rules 290 键 SHA-16 `d3790431153a5dcd`——**本批将按登记流程变更 rules.json，是全项目首次在例行批次中变更 rules，须走基线指纹门**）。容量按既定模式处置，并行度先检后定。

## 1. 目标与范围

**把四个已出数键族从模块 RULE_SPECS 正式登记进 rules.json（register_rule 序列化），关闭 L1 结构边界；数值零变化**：

- `skilllist|100|/param0`、`skilllist|102|/param0`：金币/经验倍率 `(p0−1)×100%`（来源模块 `card_page_inference_gold_exp.py` RULE_SPECS）。
- `skilllist|19|/param2`、`skilllist|1033|/param3`：两段回复间隔乘数（来源模块 `card_page_inference_heal_interval.py` RULE_SPECS；只登记乘数结构，**仍不写秒数、1033.p1 范围仍仅推断、96 攻击未证边界与本批无关不得触碰**）。
- 键清单以模块 RULE_SPECS 实际声明为准逐键核对，预期恰为上述四键；如模块另有声明须如实列出并限于已出数槽，不扩到未出数槽。
- **附带（批1 独审残留①）**：`card_page_inference_type80_96.py` 的 SLOT_EFFECT 死元数据按能力分表（80/96 分列），16 条 type80 param7 的 binding.effect_type 由「クリティカル威力」纠正为「クリティカル発生率」；账本已不消费该字段，属页面元数据修正，数值零变化；build_report §4 键清单正确口径（17 键＝16 skilllist＋1 bossskill，无 96/param0）在新文档中沿用，不改旧交付件。

## 2. 判定与保护

- **基线指纹门**（共鳴 A/B 先例 `output/character_skills/kyoumei_ab_20261025/baseline_rules_fingerprint.json`＋`check_rules_diff.py` 模式）：旧 290 键逐键 canonical JSON SHA 不变，仅允许新增本批四键（含其 conditions/conversion 等完整定义）；指纹对账报告入批次目录。
- **等价性门**：登记后 `rules.answer_for` 对全部既有 165 条相关答案（gold_exp 140＋heal_interval 25）重算结果与现页逐键相等；模块侧单一事实源——登记后模块从 rules 读取或保留等价断言，禁止双写漂移（实施选择并说明）。
- **页面变化白名单**：数值/单位/证据档零变化；允许的变化仅两类并逐键列清——①四键族答案的 rule_registry/rule_status 等登记状态字段由「未登记」转为已登记；②type80 param7 的 binding.effect_type 元数据纠正（16 条）。其余字段、其余卡、其余族零变化；30236/30239 零触碰；開局/B档/type67/mana_b 96 攻击 74 条等既有答案零改值。
- **不新增任何数值答案**：has_answer/backlog/identified 预期零变化（19,920／75,900／69,873）；若出现指标漂移即停车报主持。
- rules.py 可改（登记序列化逻辑），rules.json 新 SHA 与 snapshot 后缀如实记录；index 基线常量仅在实测指标变化时按先例改常量。
- 验收：指纹门＋等价性门全过；verify_full 17/17、账本 9/9、A7 29/29（先存旧结果）、final_diff（白名单内变化逐键清单相等、白名单外零变化）、隔离复跑代表卡（30246/11234/1213/11217＋type80 param7 代表卡）逐字节比对（白名单字段除外逐项说明）、scratch 原错误/相邻变体/正确保留三类用例。

## 3. 写入范围

实施：`scripts/character_skills/rules.py`、`output/character_skills/profiles/rules.json`（仅本批四键登记）、`card_page_inference_gold_exp.py`／`card_page_inference_heal_interval.py`（单一事实源改造，不改动数逻辑）、`card_page_inference_type80_96.py`（SLOT_EFFECT 分表）、`card_page_data.py` 如需、`output/character_skills/rule_registration_20261028/`、自身 work；effect_ledger 预期无需新映射（既有绑定不变），如确需仅本批窄映射；独审：`output/character_skills/review/rule_registration_20261028_deepseek/`。主持：任务卡、进度、容量与共享整合。

## 4. 验收与流程

预检（模块 RULE_SPECS 键清单与既有 165 条答案清单）→基线指纹建立→登记与等价性验证→scratch 三用例→四 cohort 统一签名重建（并行度先检后定）→账本/入口/选题（F03）→固定检查→final_diff（白名单口径）→隔离复跑→独审（V4 Pro GA high，初审一次＋集中修复后定向复核一次）。容量按既定模式处置留回执。模型：实施 DeepSeek V4.1 Flash high、独审 V4 Pro GA high，显式 `$high`。

## 5. 停止边界

不新增数值答案、不扩其他键族（type52/116、96 攻击、1033.p1、秒数均不触碰）、不做 Chain/新原生/cost_statement；不 Git/UI/发布；指标漂移或等价性不成立停车报主持。本批收口计 2/3，满3批后停下通知用户第三方独立审查。
