# 给原审查对话的复审确认提示词：R3 sentence 残余整改（2026-10-24）

> 用法：把以下内容整段交给产出 `independent_20261023_r2r3_root_recheck` 的原审查对话。你是该审查线的原审查者：请独立核实整改是否真正闭合了你上轮指出的根因，不要采信我方的实施/审查结论，也不要把 DeepSeek 复验的 PASS 当作无需验证的输入。

## 一、整改对象（你上轮的发现）

你在 `output/character_skills/review/independent_20261023_r2r3_root_recheck/REPORT.md` 判定：R2 机制覆盖仍可误报完整（高）、R3 同句其他机制抢占主分类（中，420/1,097 个 sentence 回退项命中词在兄弟效果子句、99 项类型启发式明确错配、7 个原文反例）、605 诊断候选中约 90 项误标共享、EFFECT_TYPE_LIMITS 空钩子。本提示词对应的整改只针对这些（R2 覆盖修复与 R3 首次读卡/两级通道已在此前轮闭合，不在本次范围；420 以外不得把"99"当成当前未修复数量）。

## 二、整改后当前终态（请以实读核实，勿照抄）

- pages campaign `c019af0b…`（source `87c905a1…`、dependency `a23f7133…`）；账本/选题锚点快照 `a2dc963c-57a14d29a773f3b7`（本轮未改 effect_ledger.py）；rules.json SHA-256 前 16 `57a14d29a773f3b7`（声明零改动）；verify_full 17/17。
- 选题产物：`work/character_skills_yg_priority/yg_candidates.json`＋`yg_candidates_items.json`（meta.generator_scripts 含三脚本运行时 SHA-256）。
- 主分类变化合计 732 项＝复审点名 420＋同判据扩展 296＋MANA 族 16（视图；nonYG 另有 62）——全部限 sentence 回退路径，clause 路径零改类，旧候选 0 丢失（保留于 also_candidates/skill_tags）。

## 三、整改内容（实施声明，待你独立核查）

1. **兄弟子句归属判定**（`work/character_skills_yg_priority/assign_candidates.py` 的 `_sentence_hit_info`＋`_unowned_sibling_check`）：无子句命中时的全句回退逐候选判定命中词所在子句归属——属本效果自身（span 重合）→作主分类；属兄弟效果子句（账本 effect 记录 span→子句 join）→降 also 并注明兄弟效应 ID＋子句原文；属未登记兄弟机制（共享形态豁免后机制词族不匹配）→同降；技能级头/触发包装/无冲突共享→合法保留。
2. **420 项全部重分类**（after：G9 410／YG1 2／G7 8）；你的 7 个原文反例全部改归 G9＋逐候选拒绝明细；349 f2 的 e00/e01/e02 保持 G7 clause、e04 保持 G5 clause、e03 由 G5 sentence→G9 fallback。处置明细：`work/character_skills_r3_sentence_fix/sentence_fallback_dispositions.json`。
3. **~90 误标共享复查**：102 项改判"未登记兄弟机制"（G5 47/YG4 18/YG5 12/G6 3 与你的例子一致；YG3 10/YG6 12 经机制族/声明类型判据）；387 维持合法共享。明细：`work/character_skills_r3_sentence_fix/review_605_shared_recheck.json`。
4. **EFFECT_TYPE_LIMITS 填实**（候选族声明兼容效果类型，sentence 回退路径生效；clause 路径不变）＋MANA 族（`必要なマナ`/`必要マナ`，types=∅＝该机制子句从不承载归属）。
5. **复验修复**（DeepSeek 复验抓出的 Medium）：`_sentence_hit_info` 跨顿号回退曾取句中首子句而非命中起点所在子句——已修（循环保留最后 start≤命中起点的子句）；由此纠正 P1 的 41 项证据文本＋P2 的 4 项分类（11024 f3 e00、11039 f2 e00/e01、11233 f4 e01）。
6. **外观债务**：20332 的 8 条 /skillparam3 注记精确化（HP 句对象仅ダメージ量、保守归因披露）；20510 的 4 条 numeric_source 父链去重。

## 四、独立审查链（已闭合，供你判断是否采信）

DeepSeek 独立复验两轮（崩溃重派一次）：初审 REQUEST_CHANGES（跨顿号 Medium＋2 Low＋4 Info）→ 修复 → 复验 **PASS_WITH_EXPLICIT_SCOPE_LIMITS**，并给出**R3 在归属/选题层全局闭合**的判定。其关键证据（你可独立重放）：AST 抽取真实 `assign_item` 与其独立规格实现在 79,121 项（视图 10,939＋nonYG 68,182）逐项 0 差异；verify_r3fix 9/9；dispositions R0-R7；605 复查 D0-D4；A7 29/29；verify_full 17/17；页面差异恰 20332/20510 两卡（值/原值/类型/单位/条件标签 0 变化）；30236 与 rules 不变。残留登记：1 Low（MANA 空集在 meta 序列化为 null 的披露口径，无分类/答案/页面影响，建议下次正常生成时修）＋4 Info。审查产物：`output/character_skills/review/r3_sentence_fix_20261024_deepseek/`（主轮＋`recheck_20261024/`）。

## 五、请你独立核查的重点

1. 你上轮的 7 个原文反例与 420 集合：处置是否正确、有无误伤合法共享、有无借"兄弟机制"名义把本该归属的项推给 G9。
2. 判据本身的语义合理性：span→子句 join 的完备性（账本 effect 记录覆盖）、共享形态豁免（技能级头/触发包装）是否会漏放真兄弟；MANA 族 types=∅ 是否成立（有无"マナ句承载效果归属"的反例）。
3. 296 项同判据扩展与 16/62 项 MANA 扩展：是否守住同一根因判据、有无超范围改类。
4. 跨顿号 KWCL 修复：循环实现的边界正确性（首子句命中、无命中、顿号在词内等）。
5. 版本对应与披露诚实：c019af0b/a2dc963c 的分工是否如声明；MANA meta null 残留的影响评估是否准确（纯披露口径）。
6. 结论请求：R3 根因是否可宣**全局闭合**；若否，剩余项与最小修复范围。

## 六、边界与产物

- 只读复核，不修改仓库文件、不启动新任务、不重跑全库统计；你的报告请另存新目录（不覆盖你此前与本线的冻结证据）。
- 进度与交付口径以 `docs/tasks/character-skills-progress.md` 顶部接手摘要为准；任务卡 `docs/tasks/20261024-character-skills-r3-sentence-fix.md`。
- 注意：本整改只覆盖 R3 归属/选题层；效果数值层（HP 分支、R2 完成判定等）已在此前各轮闭合，如有疑问见其各自审查目录。
