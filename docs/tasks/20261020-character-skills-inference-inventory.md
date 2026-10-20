# 任务卡：角色技能页 C 行句式模板盘点与试点设计（推断层晋级准备）

- 任务 ID：`20261020-character-skills-inference-inventory`
- 状态：**已完成（纯分析，未晋级、未改生成器、未改 pages 产物）**
- 负责人／对话标识：推断层盘点员（GLM 5.3 Flash 260828，经动态 workflow 子代理派发）
- 日期：2026-10-20

## 目标

把全库 27,540 行 C 行（row_class=C，分母 N_all=41,665）按规范化句式模板分组，定位并评估既有 11,409 条候选提示数据，给出 Top 20 模板清单、首批试点设计与有意拒绝晋级的边界。**只盘点与试点设计，不做任何晋级。**

## 允许写入范围（本轮实际遵守）

- `work/character_skills_inference_inventory/`（中间数据与脚本：c_rows_raw/c_rows_enriched/c_rows_v2.json、templates_level1.json、families*.json、build_templates.py、enrich_v2.py、build_families*.py、emit_inventory.py）
- `output/character_skills/inference_inventory/`（template_inventory.json、TOP20.md、pilot_design.md、boundaries.md）
- 本任务卡 `docs/tasks/20261020-character-skills-inference-inventory.md`
- 未改：生成器、pages、profiles/原始输入、旧审查报告、共享进度文件（character-skills-progress.md 未动）；未 git 暂存/提交。

## 输入（全部只读）

- `output/character_skills/pages/<cid>/card.json` ×2236：C 行提取（japanese、row_id、unknown_reasons、skill 级 record 上下文）
- `output/character_skills/profiles/records.jsonl`（13,613 记录）：**候选提示底层**——`fragments[].status='INFERRED_KEYWORD_HINT'`，`fragments[].cands=[{f,value,table,record_id}]`
- `output/character_skills/profiles/descriptions.csv`：页引用视图（41,595 实例 = 398 确认＋11,409 hint＋29,788 未知）
- `output/character_skills/profiles/rules.json`（277 条已确认规则键）
- 生成器参考：`scripts/character_skills/profiles.py`（KEYWORD_HINT :58-75；候选匹配循环 :302-317；collect_answers :189-249）
- `output/character_skills/r2_preparation/boundary_disclosure.md`、`output/character_skills/pages/README.md`、`docs/tasks/character-skills-progress.md`

## 关键结果

- **分组**：L1 严格模板 7,647 个；L2 家族（属性列表→⟨ATTR⟩、剥句首连接词）6,341 个。Top20 家族覆盖 8,976 行（32.6%）；≥100 行的家族 19 个（6,748 行）。
- **候选提示定位与评估**：底层在 profiles/records.jsonl 片段级；候选全部来自已确认规则答案（CONFIRMED_NUMERIC），由 12 组关键词触发（profiles.py:58-75），**只有关键词级归属、无句法审核**→对象/方向错配风险实测存在（30338 敌方减益句挂我方增益候选）。行级（本记录片段）连接率 27,517/27,540，C 行 9,143/27,540（33.2%）有候选；页级 11,409 与行级 9,143 分母不同（页引用实例含 A 行与别名重复）。
- **试点推荐**：type1017「戦場バフ」家族——341 行/341 cid、7 个严格模板、候选 rule-hit 341/341；规则 5 条已确认（rules.json `skilllist|1017`），原生证据 `output/ordinary_effects/ability1017/`，方法先例 P3B9 type67 冻结队列。详见 pilot_design.md。
- **拒绝晋级边界**：5 条（boundaries.md），前 4 条沿用 boundary_disclosure 实例并逐条在 card.json 核实，第 5 条为元语句新增实例（10212 代表 2,014 行）。
- **长尾**：家族 <3 行的 5,030 个（6,397 行，23.2%）；单行家族 3,663 个；元语句/定性句约 3,849 行；27,054/27,540 行原文无数字。

## 已知限制（如实声明）

- special_move 行候选多来自 bossskill **子记录**，子记录不是 records.jsonl 独立行，其 effect_type 本轮无法解析→这些家族的 rule-hit 计数被低估（TOP20 中以 * 注记）；候选本身均有已确认规则背书（collect_answers 只在规则存在时产生候选）。
- 23 行 C 行未能连接到 profiles 片段（空白行/别名分行等），hint 状态按无候选处理。
- 长尾分类（元语/状态/玛那/伤害）为正则近似，边界重叠，只作规模参考。

## 下一步（需用户/主持授权后实施）

1. type1017 试点实施（生成器推断层接入＋341 行晋级＋独立审查）；
2. 试点通过后按同方法评估 #3（type8/type26 子集）与共鳴家族候选完整性审核；
3. 元语句类是否转机制/定性层，单独立项。
