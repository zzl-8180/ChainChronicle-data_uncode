# R3 sentence 回退兄弟子句归属整改（R3-RESIDUAL-SENTENCE-SIBLING）

- 任务 ID：20261024-character-skills-r3-sentence-fix
- 负责：主持 Kimi K3（唯一写入整合者）；实施 GLM 5.3 Flash 260828（high，workflow dwfrun-e77bb3f4）；独立审查 DeepSeek V4.1 Flash 1017（high，独立新上下文，已派出）
- 授权来源：用户 2026-10-23 指令「先完成整改，我交给原审查对话复审确认」；根因登记于 DeepSeek 复验 `output/character_skills/review/r2r3_root_fix_20261023_deepseek/`（High：420/1,097 sentence 回退命中词在兄弟效果子句、99 明确错配；Medium：~90 误标共享、EFFECT_TYPE_LIMITS 空钩子）
- 状态：**正式收官（2026-10-24，DeepSeek 复验 PASS_WITH_EXPLICIT_SCOPE_LIMITS——R3 在归属/选题层全局闭合：真实 assign_item 与审查方独立规格实现在 79,121 项逐项 0 差异）**；残留 1 Low＋4 Info 登记（MANA meta 空集序列化 null 的披露口径——建议下次正常生成时修；MANA 扩展实际影响视图+16/nonYG+62 已明示；其余 Info 存档）；待用户交原审查对话复审确认
- **方案引用与接入说明（2026-10-24 补正）**：本轮遵循 `docs/角色技能完整解读实施方案.md`（2026-10-24 版）。**接入点如实说明**：本轮在新版方案定稿前已按上一流程完成实施与正式生成（pages campaign `c019af0b`），现从**最终产物独立复验步骤**接入——不能称本轮完整执行了新版§5 的两段式（先审修法、后正式生成）；先前步骤不代表已按新规则执行。不为补流程形式倒退重做已完成工作；若独立审查发现实质问题，仍按实际影响修复、补生成与复验。后续适用的复杂整改按新版两段式执行。

## 基线与范围

基线：pages campaign `a2dc963c`（整改前）；backlog 79,121（P1 10,939/P2 68,182）；rules `57a14d29`。范围：sentence 回退路径的归属判定（assign_candidates.py）、420 项重分类＋~90 误标共享复查、effect_type 参与分类；搭车外观债务（20332 p3 注记×8、R08-R1 去重）。clause 路径与 split 项零改动。

## 实施结果（GLM，2026-10-24 完成）

- **归属判定**（`_sentence_hit_info`＋`_unowned_sibling_check`）：命中词子句属本效果（span 重合）→作主分类；属兄弟效果子句（账本 67,987 条 effect 记录 span→子句 join，backlog 项↔effect_id 51,035/51,035 实测）→降 also（also_basis 注明兄弟效应 ID＋子句原文），主分类走 skill_tag/G9＋含拒绝明细的 fallback_reason；未登记兄弟机制（共享形态豁免＋机制词族对比）同降；技能级头/触发包装/无冲突共享→合法保留。无 CID 特判、旧候选 0 丢失。
- **420 项处置**：与复审 residual 集合完全相等（差 0）；after 分布 G9 410/YG1 2/G7 8；7 个原文反例全部改归 G9＋逐候选拒绝明细；349 f2 保持（e00/e01/e02→G7 clause、e04→G5 clause）、e03→G9 fallback。同判据扩展 +296（G4 146/YG4 81/其他 69）——**主分类变化合计 716，全部限 sentence 回退路径、clause 路径零改类**；未变化项 also/skill_tags 集合零变化（also_basis 文本精化 593）。
- **~90 复查**：102 项改判未登记兄弟机制（G5 47/YG4 18/YG5 12/G6 3 与审查例一致；YG3 10 经自身子句机制族对比、YG6 12 经声明类型判据）；387 维持合法共享；旧候选在 also 保留。
- **外观债务**：20332 的 8 条 /skillparam3 注记改精确化口径（b6 补传 gains_uniform）；R08-R1 去重（b17 numeric_source 父链 child 不重复追加；实测仅 1 行 4 条重复，另两行属 B17-R08 槽位分区文案、不在本项范围未动）；其余债务项核实现状已由前轮文档债务包闭合。
- **验证**：四 cohort 并行重建 0 失败（页面差异恰 2 卡：20332×8 note＋20510×4 numeric_source；值/原值/类型/单位/字段/条件标签 0 差异；30236 不变；rules 零改动）；pages campaign `c019af0b`（source `87c905a1`）；verify_full 17/17；R1 保护 4 案全过（104 HP/S7 1,336/6306/30236）；选题链重跑闭包 10,939、unassigned=0、视图⊆backlog 差 0、scratch 与正式逐项 0 差异；verify_r3fix.py 9/9（AST 抽取真实函数、预期独立书写）。
- **F03（主持）**：yg_candidates.json meta 新增 generator_scripts（三脚本运行时 SHA-256）＋note，实测与文件哈希一致。
- **F03 上游生成关联（2026-10-24 补正；2026-10-24 二次补正按复核意见写全）**：
  - **纠正事实**：此前写「backlog.json 自带快照锚点」不准确——`backlog.json` 实测为**纯列表**（79,121 项，无 meta/快照字段）；snapshot_id 与 campaign 信息来自配套记录 `output/character_skills/effect_ledger/metrics.json`（`snapshot.snapshot_id=a2dc963c-57a14d29a773f3b7`、`snapshot.campaign_signature=a2dc963c…`）。「backlog 内容」与「配套快照记录」不得混称。
  - **区分两个事实**：①「当前代码哈希已核对」= 已完成（`yg_candidates.json` meta.generator_scripts 与磁盘三脚本运行时哈希一致，只证明当前代码内容）；②「实际生成链已可追溯」= **部分不可追溯（如实标注）**：`yg_backlog_view.json`（纯 list 无 meta）与 `yg_backlog_view_enriched.json`（meta 为空）未记录其生成代码/输入版本——本次无法追溯，**不以事后计算的文件哈希补写成历史生成事实**；`yg_candidates.json` 的 backlog_anchor 来自 metrics.json（账本快照记录）＋generator_scripts（当前代码哈希）。已有生成记录/冻结材料引用：R3 轮实施产物 `work/character_skills_r3_sentence_fix/`（无链式 stdout 留档，如实注明）；前轮链式 stdout 存 `work/character_skills_rectification_r2r3/`（属旧版本产物）。
  - **下一次正常生成的记录办法（执行安排已明确，待下次正常生成实施验证）**：采用**旁置生成记录**（每步在 `work/character_skills_yg_priority/` 写 `<step>_run_record.json`，不改动现有 JSON 列表/对象结构，避免破坏消费者）。每步记录：实际执行脚本路径＋运行时内容 SHA-256；实际消费的直接输入及各自内容 SHA-256（或适用的既有版本标识：campaign 签名/账本 snapshot_id 等）；生成输出位置＋内容 SHA-256；上游生成记录指针（上一步 run_record 路径）；完整运行命令与生成时间。逐步形成可查链：输入/快照（backlog.json 哈希＋metrics.json 快照）→ build_inventory 输出（view 哈希）→ enrich_records 实际输入（view 哈希）与输出（enriched 哈希）→ assign_candidates 实际输入（enriched/backlog/ledger/metrics/inventory_summary/页面）与最终候选（yg_candidates 哈希）。
  - **实施登记**：最小修改范围＝选题链三脚本各自新增 run_record 写出（纯新增文件、不改现有产物结构与消费者）；负责人＝下一次选题链执行的实施者（GLM）；验证办法＝记录中的代码与输入哈希对应实际运行、输出哈希一致、上下游指针链完整（可写一个小校验脚本逐环核对）；未实现部分状态＝「记录要求和执行安排已明确，待下次正常生成实施验证」，**不宣称为"生成链已经完整可追溯"**。本轮不实际修改生成器、不重跑链。
- **实施者自注待裁点**：①716＝420＋296 扩展项（同判据作用于回退全路径的必然结果，主持认可；如需收窄可回退 _unowned_sibling_check 的机制词族判据）；②102 vs 复验「约 90」（判据逐项留痕）；③EFFECT_TYPE_LIMITS 的 G5 含継続時間（clause 级实测 2 例，当前 0 翻转，保守保留）。

## 允许写入

`work/character_skills_yg_priority/`（assign/产物）、`work/character_skills_r3_sentence_fix/`、`scripts/character_skills/card_page_inference_b17_p0finale.py` 与 `b6_bossbuff.py`（仅注记生成器最小改动）、`output/character_skills/pages/`（重建）、`output/character_skills/inference_inventory/`（补记）、`docs/tasks/20261023-character-skills-r2r3-root-fix.md`（追加记录）。rules.json 零改动。禁止 git；禁止改旧审查报告与冻结证据；30236 零触碰。

## R3 复验缺陷修复（GLM 5.3 Flash 260828，2026-10-24）

依据：DeepSeek 复验 `output/character_skills/review/r3_sentence_fix_20261024_deepseek/issues.jsonl`（7 条：Medium R3F-CROSS-CLAUSE-KWCL、Low R3F-VERIFY-V6-VACUOUS、Low R3F-30225-SHARED-MISLABEL、Info×4 存档不处理）。

- **F1 跨顿号子句定位修复**（`assign_candidates.py` `_sentence_hit_info`，原 296-302）：全包含判定失败时的回退由 `next(... if cm.start() <= m.start())`（实际取句中**首**子句，与注释「命中起点所在子句」不符）改为循环保留**最后一个** start≤命中起点 的子句；owners／机制词族判定随正确子句生效。clause 路径与子句切分零改动。
- **F2 机制词族表补 MANA 族**（`_MECH_FAMILY_WORDS`＋`EFFECT_TYPE_LIMITS['MANA'].types=∅`）：必要マナ減り（「1stChain以上で必殺技を発動する時に必要なマナが1つ減り」等 37 种句形，词面 `必要なマナ`/`必要マナ` 全覆盖）登记为独立技能级机制——无 effect 记录动作子句含该词 → 未登记兄弟机制（降附加、候选保留），不再标「合法共享」。`_et_ok` 不受影响（无候选 ID 以 MANA 开头）。
- **重生成**：先行 scratch（R3B_OUT_DIR）后正式 `yg_candidates.json`＋`yg_candidates_items.json`；**不重跑 build_inventory/enrich_records**（backlog 未变，锚点 `a2dc963c-57a14d29a773f3b7` 79,121 不变）、**不重建页面**（2236 页 card.json 与 before 快照哈希对账仅 20332/20510 两卡差异＝上一轮已声明变化；30236 零触碰；rules/ledger/backlog mtime 未动）。meta.generator_scripts 运行时哈希与磁盘 3/3 一致。
- **缺陷归因（三组重放分离）**：fix1 单独生效 → 视图主分类/also 集合 **0 变化**（与复验独立规格一致），nonYG 仅 G9 unique_texts 6,663→6,662（即 4 项规格差，items 30,468 不变）；MANA 族 → 视图主分类 **+16**（G4 sentence→YG1 skill_tag，均为「必要マナ減り」触发句曾作 G4 主分类的共鳴必殺技能效果，旧候选 G4 全部保留 also/also_basis 0 丢失）、nonYG G4→YG1 62 项。**主分类变化集合（vs before）=732＝716＋16**，全部 sentence 回退效果项（越界 0），复验 420 全部在内。
- **复核集合（recheck_r3fix_items.py，6/6 PASS）**：①18 项 sentence_fallback klass/子句（30241 denju+special_move pattern0/2/skilltext、30250 ability f2、30337 同三组 e00/e01）全部 klass=own＋keyword_clause=正确子句，主分类/also 与修复前重放相等；②23 项 also_basis（352 f2 e00-e04、4316/30243/30256 f2 e00-e02、30241/30250/30337 各 1）全部引用正确子句、G2 候选保留 also；③4 项 nonYG（11024 f3 e00→G2/sentence、11039 f2 e00→G9/fallback、11039 f2 e01→G2/sentence、11233 f4 e01→G9/fallback）与复验规格逐项相等（兄弟 G2 不作主分类、自身子句 G2 恢复主分类）；④G9 unique_texts=6,662（规格口径）。
- **605 复查更新（recheck_605_shared.py 重跑，D0-D4 全过）**：30225-special_move pattern0/skilltext f2 e00 两项改判「未登记兄弟机制（降附加）」，flagged＝「机制词「必要なマナ」属 MANA 族（声明类型（なし），本效果类型「効果（词表外）」不在内）」；主分类保持 G7 clause 不受影响；改判 102→**104**、维持合法共享 387→**385**（其余分布不变：G5 47/YG4 18/YG5 12/YG3 10/YG6 12/G6 3/G4 2）。
- **验证**：verify_r3fix.py **9/9**（V6 改真实断言：实际数据缺行=0＋合成缺行探针 `_row_of` 显式 None、assign_item 两次一致归 G9 fallback、语境字段保持 None 无他行回退；V3c/V5 detail 注明「同源确定性重放，非独立语义验证」并引用独立规格对照）；dispositions_420.py R0-R7 全过（420 集合不变、scratch==正式、变化集合 732 越界 0）；A7 规则层回归 29/29（`a7_regression.py` 重跑）。
- **修复期临时证据**（保留可溯）：`work/character_skills_yg_priority/_prefix_replay_assign.py`（修复前三脚本副本）与 `_fix1only_replay_assign.py`（仅 fix1 副本）及 `work/character_skills_r3_sentence_fix/scratch/{prefix_replay,fix1only_replay}/` 重放产物、`*_stdout.txt`；逐项复核输出 `recheck_r3fix_items.json`。A7 结果文件由其脚本自身更新（`work/character_skills_goal_rectification/a7_regression_results.json`，29/29）。

## 最近更新

- 2026-10-24：R3 复验 7 issues 处置——Medium 跨顿号子句定位修复＋Low マナ族补登记（重生成正式选题产物、41 项 P1 文本/4 项 P2 分类/605 处置逐项复核）＋Low V6 真实断言（verify_r3fix 9/9）；Info×4（批 7 去重债务、420 口径注记、2323 重复子句键、F03 溯源边界）按复验建议存档不处理。待原第三方审查对话复审确认。
