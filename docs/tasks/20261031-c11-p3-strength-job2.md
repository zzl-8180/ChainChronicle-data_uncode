# C11-P3 skilllist|1017| サブパーティ条件攻防速

- 规则入口：现行实施方案、三周期计划及 `output/character_skills/c11_p3_selection_20261031/selection_report.md`。
- 状态：**独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0；13行/39答案、完整+0，可进入C11交付包。两项low预检分母/探针限制已由审查全量补验**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high；例行独审：独立新上下文 `new-provider/deepseek-v4-pro-ga-260813` high，均用dynamic workflow。

## 范围与上限

仅预检冻结13张Y.G.卡、13条第二段条件句：350、4316、30229、30232、30237、30238、30241、30252、30262、30327、30328、30333、30337。目标为 **13行／39答案**，每行攻击、移动速度、防御三效果。30239同族但保护排除；19张非Y.G.同族行不纳入。

复用 `skilllist|1017|/param1..3` 已确认换算和既有三条账本映射；0新公式、0新规则键、0新账本映射、0新原生。

## 硬门与未知

1. group=ability、CACHE skilllist、skillid[2]、记录和页面指针一致；skillid全表唯一且全charainfo引用计数1，ability=1017，param0..3/iParam0/flag符合原记录。
2. 句面须位于记录第二段，两种形态逐字匹配；不得把首段、同段暴击子句或其他段归入本批。首段既有39条答案零改值零丢失。
3. p1攻击×1.15、p2移动速度×1.15、p3受伤量×0.85（减伤15%，不是固定防御或防御−15%）；param2已核ID仅2个，逐行保留同类型外推注记。
4. iParam0=31只含JobType0..4，不写全职业；对象与关联仍为推断。
5. 「サブパーティ／メインパーティ」放置条件未被规则编码：本批**保留S3拆分标记，不用binding_conditions清旗，完整描述+0**；不得写成已确认仅对主队生效。
6. 同段「クリティカル発生率／威力」继续未知，1017无p4/p5规则；不写最终伤害、HP、面板、叠加上限或Chain影响。
7. APK与CACHE同号记录不合并不跨层；数值是既有记录的第二句归属，不写成新发现。

## 允许写入与验收

- 新模块 `scripts/character_skills/card_page_inference_c11_p3_strength_job2.py`；候选 `output/character_skills/c11_p3_strength_job2_20261031/candidate/`；临时 `work/c11_p3_strength_job2_20261031/`。
- `run_checks.py` 覆盖13行/39答案、第二段、首段与同段保护、S3保留、三条既有映射、参数与单位、CACHE/APK隔离、C11-P1/P2回归、幂等、非Y.G.零连带和范围外零变化。
- 不改共享接线、rules、effect_ledger、正式pages或交接；不运行正式生成、清理、Git或新原生。
- 候选独审通过后才可进入C11交付包整合。
