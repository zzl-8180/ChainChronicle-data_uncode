# 20261020 角色技能·Y.G. 覆盖度测量（批 5 前置，纯分析）

- 状态：完成（2026-10-20）。
- 负责人／对话：YG覆盖测量员（GLM 5.3 Flash 260828，workflow 子代理，单 ask）。
- 目标：用户定调「新卡（称号含 Y.G.）优先攻关」后，测量批 1 两级模板分组在 Y.G. 109 卡 C 行的命中量、三批已实施模板（type1017 试点／批 3 type8／批 4 条件扩展）在 Y.G. 的已点亮/剩余、Y.G. 特有机制簇，并给出后续批次建议。
- 报告（权威结论入口）：`output/character_skills/inference_inventory/yg_coverage.md`。
- 数据与脚本：`work/character_skills_yg_coverage/`（extract_yg_rows.py / analyze_families.py / cluster_mechanics.py / deep_analysis.py / fulllibrary_scan.py＋yg_rows.json、yg_c_rows.json、yg_top20_hits.json、yg_families.json、yg_clusters.json、yg_unclustered.json、batch_status.json、deep_analysis.json、fulllibrary_remaining.json）。

## 允许写入范围

- 本任务卡、`work/character_skills_yg_coverage/`、`output/character_skills/inference_inventory/yg_coverage.md`。
- 不改：生成器（scripts/character_skills/*）、pages/ 产物、profiles/ 与原始输入、旧审查报告、其他任务卡。

## 核心结论（详见报告）

1. 分母实测与任务给定一致：109 卡 5,805 行＝A 2,623＋C 3,182；整行确认 18（全在 30236）；整行推断 62（全为批 1 试点 `inference_pilot`）。
2. Y.G. C 行 3,182 行归 425 个 L2 家族，**新归一形状 0 个**（全部在批 1 家族库中）；批 1 Top20 合计命中 1,865（58.6%）。
3. 三批状态：试点已点亮 62、剩余试点形状 110（**全部是 job_ability 108＋supporterskill 2，被试点表 gate 挡住**）＋crit 变体 12；批 3 type8 在 Y.G. 剩余 0（Y.G. 192 行同形句为 ability 1110/1095/job_ability，无 type8）；批 4 剩余 0。
4. 最大增量簇：味方全体必殺バフ（Y.G. 304/全库 2,137，需 bossskill 子记录解析——rules.json 实有 bossskill 规则 140 条/55 型）；共鳴 3000/3005（Y.G. 124，3000 有规则、3005 无）。
5. 关键结构发现：job_ability 行无参数槽，值在 `skill_ids`→skilllist(skillid=6500xxxx，ability 1095/1017) 记录，rules/occurrences 现成（1095 param1/param3 occurrences=407）——试点跨表扩展证据路径已核实。
6. 批次建议：批 5＝type1017 跨表扩展（Y.G. ~110–140）；批 6＝味方全体必殺バフ/bossskill 子记录解析（Y.G. ~240–300/全库 ~1,500–2,100）；批 7＝共鳴 3000/3005；批 8＝敵デバフ＋自身バフ（复用批 6）；批 9＝Chain 威力族。另立机制专项：設置/戦闘不能、反響、時の楔等；定性限定句 748 行不进数值推断层。

## 最近更新

- 2026-10-20：测量完成，报告与数据落盘；未 git 暂存/提交。
