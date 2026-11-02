# C12-P3 charainfo.skilltext 同卡同文档位同文镜像

- 规则入口：现行实施方案、三周期计划及 `output/character_skills/c12_p3_selection_20261031/selection_report.md`。
- 状态：**独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0；123行/459答案与效果、0新值、S4 0、完整+0，可进入C12交付包。C12后停止等待第三方审查**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high；例行独审：独立新上下文 `new-provider/deepseek-v4-pro-ga-260813` high，均用dynamic workflow。

## 主持裁决与范围

主持确认：本批是新描述行的答案归位，不是同记录重复答题；raw值已存在不构成值级重复。允许多槽镜像，但每槽独立满足同卡、同标签、唯一同文行和原记录链。保留S7与hint，完整+0，不宣称Boss模式档位选取已解析。

仅预检冻结88卡123行，目标上限 **459答案／459效果净增**：buff 84行（45行5槽=225、39行3槽=117）＋debuff 39行（117）。0新增唯一数值、0新公式/规则键/账本映射/原生。

## 硬门与未知

1. group=special_move、table=charainfo、CACHE、reference_field=skilltext；原文与charainfo.skilltext NFKC全等，本行为逐字子串。
2. 同卡同【共鳴必殺】标签的patternN行逐字同文且恰1条；该档位行已有对应rule_key/field/raw答案。同文super兄弟必须存在且至少一个原值不同，证明不能只按文本选值。
3. 原记录链逐位相等：bosspattern→bossskill(13)→s_ability(2012/2003)；只出句面槽：13 p1/p2/p6、2012 p4/p5、2003 p7/p8/p9。13 p3与2003 p0时长已有答案不重复，30108不得补时长。
4. 一行一槽一答案，避免同主张双值行S4；答案与效果净增均为459，新增唯一值0。数值与关联证据均为推断。
5. S7_same_cond_alt_t13与b6/b8/b10 hint保留，完整+0，不写实际pattern选取或镜像行参与战斗；CACHE/APK同号不合并且只用CACHE值。
6. 22个文本块的其他「状態異常」子句不得顺带回答；敌方debuff对象与buff味方不混，2003触发口径照规则披露。
7. 30102/30239/20234/30236零触碰；不含t114/1059/1017/1095/11/84/16、denju非首段、状态异常回复。

## 允许写入与验收

- 新模块 `scripts/character_skills/card_page_inference_c12_p3_skilltext_mirror.py`；候选 `output/character_skills/c12_p3_skilltext_mirror_20261031/candidate/`；临时 `work/c12_p3_skilltext_mirror_20261031/`。
- `run_checks.py` 覆盖123行/459答案与效果、同标签唯一同文行、super异值、原记录链、时长保护、未知子句、C11/C12-P1/P2回归、幂等、非Y.G.零连带和范围外零变化。
- 不改共享接线、rules、effect_ledger、正式pages或交接；不运行正式生成、清理、Git或新原生。
- 候选独审通过后才可进入C12交付包整合。
