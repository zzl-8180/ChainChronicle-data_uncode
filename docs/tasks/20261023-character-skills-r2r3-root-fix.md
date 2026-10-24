# 复审整改：R2 机制覆盖有效状态＋R3 同句抢占根因＋S1 同步（保留 R1）

- 任务 ID：20261023-character-skills-r2r3-root-fix
- 负责：主持 Kimi K3（唯一写入整合者）；实施 GLM 5.3 Flash 260828（high，CreateWorkflow 钉模型，**双 workflow 并行**）；独立复验 DeepSeek V4.1 Flash 1017（high，完成后独立新上下文）
- 授权来源：用户 2026-10-23 指令「根据最新独立复审继续整改，只修复 R2、R3 剩余根因并同步 S1，保留 R1；尽可能并行开展，加快速度；不启动新批次」（复审 `output/character_skills/review/independent_20261023_r2r3_root_recheck/REPORT.md`＋root_probes/root_r2_probes/r3_local_overridden 证据）
- 状态：**进行中（根因已核实，A/B 双线并行实施）**

## 基线锚点（2026-10-23 实测）

campaign `a470c05442a6294c…`；receipt source_signature `241caa4be40a4f7c…`（当前源码闭包 `26cdc644…` 已叠加并行重建改动——后续并行重建任务已授权，旧回执不代表当前源码全库验证）；rules SHA 前 16 `57a14d29a773f3b7`；行 41,665／A 17,476／C 24,189；backlog 79,121（P1 10,939／P2 68,182）；完整 4,378／部分 76／未解析 9,125／拆分 28,086；verify_full 17/17。

## 已核实的根因（主持独立复核）

1. **R2（高）**：`effect_ledger.py:942-947` `_mechanism_structural_coverage`——quantity_kind 命中机制词即返回覆盖，未检查答案本身的 value/raw_value/evidence/status（`quantity_kind=暗闇`＋value=未知＋raw_value=null＋证据未知＋status=unresolved 的答案仍判覆盖）；注记分支只要求机制词与概率载体/阈值特征同在一个 note（`.../_CARRIER_PROB_RE/_CARRIER_KEY_RE+_THRESH_LIST_RE`），不验证该载体实际解释的是哪个效果（86 行注记「暗闇仅作为对照词，不属于上述概率载体解释的效果。」仍判覆盖）。
2. **R3（中）**：`assign_candidates.py:111-117` `assign_item`——先遍历 CANDS 再逐候选找子句/全句命中并取 matched[0]；高优先级候选的**全句**命中（G5 状態異常回復）压过当前效果**子句**命中（G7）。真实反例 `349-ability-ability-skillid_2_-lvorder1-f2`：攻击/防御/时长三效果（子句「味方全体の攻撃力と防御力が一定時間上がり」）主分类被同句后面的「全状態異常を回復する」抢为 G5，G7 仅列附加。诊断候选 605 个「全句主分类覆盖不同子句分类」待复查（非全部错误，须区分合法共享条件）。
3. **S1（低）**：当前看板写 campaign `2306af95`（正式产物实为 `a470c054`）；标题称收官、正文称复验进行中；当前源码叠加并行重建改动，旧回执≠当前源码全库验证。

## 并行组织（用户指示尽可能并行）

- **线 A（R2）**：修 `_mechanism_structural_coverage`——覆盖必须指向有效解析：quantity_kind 命中须答案有真实值（非未知/null）、证据非未知、status 非 unresolved（未知答案保留为缺口）；注记载体分支须验证载体实际解释的是当前机制（载体键/槽与机制的效果对应，对照性提及不作证）；不加否定词黑名单、不硬编码反例、不一律降级。验收：两负例（未知暗闇答案／无关概率载体注记提暗闇）保持不完整＋剩余待办；HP 阈值、有效バリア回数正例与上轮全部反例保持。账本＋页面重建＋verify_full 17/17＋R1 保护复验（104 答案/1,336 S7/6306/30236/2,236 卡 JSON）＋变化清单。**让出选题链**（由线 B 重建）。
- **线 B（R3）**：修 `assign_item` 排序——子句命中优先（按 CANDS 序取首个子句命中），全句命中仅在无子句命中时作主分类，全句上下文保留为附加分类与依据（不机械删除）；effect_type 参与候选适用性约束；技能级标签与共享条件保留可定位依据。349 反例：攻击/防御/时长→G7、全状態異常回復→G5。复查 605 诊断候选（区分错误覆盖纠正/合法共享条件保留，逐项记录）。回归：冷/热/逆序一致、缺行 None、队列集合对账、同句多机制代表用例（改无关子句不改当前效果主分类）。**只在 scratch 产物上验证（work/），正式产物待线 A 完成后由主持整合重建**。
- **整合（主持）**：两线完成后跑选题链（build_inventory→enrich_records→assign_candidates，线 B 修复后的代码×线 A 的最终 backlog）→对账→S1 同步看板→派 DeepSeek 复验。

## R1 保留范围

8 行 104 个 HP 条件答案（原始来源绑定）；6306 缺失 HP 下界保持「HP ?–50%」不补 0；1,336 行 S7 分支待办及 flag_detail；30236 基线；2,236 卡 JSON 逐文件无变化承诺（合理改动须解释差异并核对语义/来源/条件）。不得删答案、隐藏待办、提高证据等级。

## 允许写入

线 A：`scripts/character_skills/`（effect_ledger/render/verify 最小改动）、`output/character_skills/pages/`（重建）、`output/character_skills/effect_ledger/`（重建）、`work/character_skills_r2_root_fix/`。线 B：`work/character_skills_yg_priority/`（assign/enrich 与 scratch 产物）、`work/character_skills_r3_root_fix/`。主持：选题链正式产物、`docs/tasks/character-skills-progress.md`（S1）、本卡。rules.json 预期零改动。禁止 git；禁止改旧审查报告与冻结证据；30236 零触碰。

## 交付与停止

R2/R3 根因与修改位置；独立反例及配对正例的预期/实际；真实受影响效果清单与状态/分类变化依据；最终版本、产物入口、重建与检查命令；R1 保护项与 S1 同步结果、剩余限制。**17/17 不代替语义反例通过。完成后停在整改交付点待独立复验，不自行开始新批次。**

## 最近更新

- 2026-10-23：任务卡建立；R2/R3 根因经主持逐行源码核实（effect_ledger.py:942-947、assign_candidates.py:111-117）；基线锚点记录；A/B 双 workflow 并行已派。

## R3 sentence 回退残余整改实施记录（R3-RESIDUAL-SENTENCE-SIBLING，20261023 第四轮）

实施：R3残余整改实施员（GLM 5.3 Flash 260828，high，workflow 子代理）。依据＝DeepSeek 复验
`output/character_skills/review/r2r3_root_fix_20261023_deepseek/REPORT.md` §2.4/§6 问题 1–3。
写入边界内：`work/character_skills_yg_priority/assign_candidates.py`（第四轮整改版）、
`work/character_skills_r3_sentence_fix/`（处置与验收）、`scripts/character_skills/
card_page_inference_b6_bossbuff.py`＋`card_page_inference_b17_p0finale.py`（外观债务搭车）、
`output/character_skills/pages/`（重建）、`output/character_skills/inference_inventory/
r3_sentence_sibling_fix_scope.md`（补记）、本卡。rules.json 零改动；账本/backlog 未动；
30236 零触碰（card.json 哈希 e5eadc72… 复验不变）。

1. **sentence 回退归属判定**（问题 1）：`assign_item` 无子句命中时的全句回退逐候选判定
   命中词所在子句归属（`_sentence_hit_info`；归属数据源＝账本全部 effect 记录
   span→子句映射 `_ROW_CLAUSE_OWNERS` 懒建＋当前 enrich 项，review_605.py join 机制）：
   (a) 命中词子句＝本效果自身子句（span 重合）→正常作主分类；(b) 兄弟效果子句→不得作
   主分类：降 also_candidates，also_basis 注明「兄弟效果 ⟨效应 ID⟩ 的机制，不作本效果
   归属依据」；(c) 不属任何 effect 子句→形态判据（【…】头/≪…≫包装/触发助词结尾＝
   真共享）＋机制词族分析（`_MECH_FAMILY_WORDS` 只读复用 effect_ledger 机制词族口径；
   声明类型/自身子句机制族冲突＝未登记兄弟机制，同 (b)）；合法共享可作主分类
   （sentence_fallback 逐项字段＋also_basis 注明依据）。主分类按无命中路径顺延
   （skill_tag/G9 兜底＋具体理由）；被拒命中保留于 also（不丢失）。clause 路径零改动；
   split 项（行日文即自身范围）零改动。
2. **EFFECT_TYPE_LIMITS 填表**（问题 3）：按各候选 clause 级命中 effect_type 实测分布＋
   任务卡指定语义填表（G0/G1→ダメージ・威力・効果；G2→攻撃/防御/移動/継続時間；G5→
   回復/HP回復/効果/継続時間；YG1→page_group=special_move；YG2→sympathy；G3/G4/G6/
   YG3–YG6 按 clause 实测），在 sentence 回退主分类与技能级标签主分类处经 `_et_ok`
   生效——空钩子闭合；声明依据写入代码注释＋meta.effect_type_limits_basis。
3. **处置结果**（产物：work/character_skills_r3_sentence_fix/）：
   - 420 项（222 动作句含 99 明确错配）全部重分类（`dispositions_420.py` 8 检查全过）；
     7 个原文反例全部不再归 G0/G2/G7，按无命中路径 G9 兜底＋具体理由（兄弟效果 ID＋
     命中词子句原文）；349 f2 e00/e01/e02 保持 G7 clause、e04 G5 clause、e03→G9。
   - 同判据扩展：另 296 项 sentence 回退效果项降级（未登记兄弟机制/适用性不兼容——
     G4 Chain/マナ句 146、YG4 戦闘不能耐性句 81 等）；主分类变化合计 716 项，全部为
     sentence 回退路径（clause 路径零改类）；未变化项 also_candidates/skill_tags 零变化。
   - 605 处置表 489「合法共享」复查（`recheck_605_shared.py`）：102 项改判「未登记兄弟
     机制（降附加）」（G5 47/YG4 18/YG5 12/YG6 12/G6 3/YG3 10——前四组含复验审查例
     G5 47/YG4 18/YG5 12/G6 3；YG3 10 经自身子句机制族对比、YG6 12 经声明类型判据改判）；
     387 项维持合法共享（技能级头/触发包装/无冲突族）。主分类输出不受影响（旧主分类在
     also 保留）。
   - 分布 before→after（主分类）：G9 1,823→2,320；G7 1,643→1,581；G4 1,497→1,351；
     YG1 975→1,180；G3 484→286；G2 642→574；G5 251→188；YG4 281→198；G0 153→110；
     G1 626→616；YG5 157→139；G6 115→112；YG6 856→848；YG2/YG3/G8/非数值/G9 外不变。
     闭包 sum(items)=10,939＝视图；unassigned=0；未变化项 also_basis 文本精化 593 项
     （兄弟机制拒绝依据，候选集合不变）。
4. **外观债务搭车**：a) b6 时长行 /skillparam3 传入 gains_uniform——20332 f4 的 8 条
   旧「本行增益答案受…约束」注记改用ダメージ量精确化归因口径（与 p1/p2/p6 对齐）；
   c) b17 `_value_row` numeric_source 父链 child 去重——实测当前页面仅 20510-denju f1
   一行 4 条含重复追加（任务卡「三行 12 条」与当前页面状态不符，已如实按现状修复并记录）；
   重建后全库复核：重复追加 0、旧措辞 0。b/e/f/g/h/i（744→738、1,336 构成、S2 四分与
   总移除 1,504、confidence 契约、CHANGELIST-STALE、R3-DIST-FIELD、39 行审计无漂移、
   A7 入库副本 29 例）已由 `work/character_skills_doc_debt_fix/` 修正包处置（本轮逐项
   核实现状落地）；CHANGELIST 第二轮：presentation_only/disposition.S1 推进至本轮重建
   campaign c019af0b（regen_final_change_list.py 第 7 节，幂等化后重跑）。
5. **重建与验证**：四 cohort 并行重建（card_page_batch_parallel.py，jobs 4，failed 0/
   reused 0）→card.json 变化恰 2 卡 12 字符串（20332 8 注记＋20510 4 numeric_source；
   值/数量字段 0 差异、行集合不变，旧 run transactions backup 逐字段对账）→
   card_page_index.py 入口页刷新→verify_full 17/17 PASS（work/character_skills_r3_
   sentence_fix/verify_full_r3fix.json）→R1 保护 4 案全过（104 HP 答案 0 diff、
   账本状态 0 diff、S7 1,336 集合相等、6306 HP ?–50% 保留）→选题链全链重跑（正式产物，
   scratch 与正式逐项 0 差异）→`verify_r3fix.py` 9/9 PASS（349 f2 逐项、7 反例、
   冷/热/逆序一致、闭包/视图⊆backlog、nonYG 68,182 独立重放一致、缺行 None、作用域）。
   页面 campaign 推进为 c019af0b（注记文本级重建；账本未动，页面↔账本未解决同步
   verify_full 0 mismatch）。
