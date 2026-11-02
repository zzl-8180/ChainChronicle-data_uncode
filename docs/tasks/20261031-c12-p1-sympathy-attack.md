# C12-P1 共鳴アビリティ skilllist|3000 攻撃力・クリティカル威力段

- 规则入口：现行实施方案、三周期计划及 `output/character_skills/c12_p1_selection_20261031/selection_report.md`。
- 状态：**独立审查PASS、阻断0；42行/108答案、效果净增66、S4 42、完整+0，可进入C12交付包。unresolved文案已修正为126→60并复跑17/17通过**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high；例行独审：独立新上下文 `new-provider/deepseek-v4-pro-ga-260813` high，均用dynamic workflow。

## 主持裁决与范围

主持允许「不晋级、仅补答已确认属性段」：符合有证单项先交付原则，但 b7 hint 和 S3 必须保留，完整+0，不得把整行写成完成或解除「不拆半晋级」语义边界。

仅预检冻结42张Y.G.卡、42条 sympathy 首段行，潜在上限 **108条答案**：p1普通攻击加算+p2技能攻击加算+p8暴击伤害系数加算。每行按句面是否有クリティカル威力为2或3条。30102禁推卡、30107/30214全状態異常回復排除；共享记录涉及的非Y.G.行零触碰。

复用既有3000三键换算与四条账本映射；0新公式、0新规则键、0新账本映射、0新原生。

## 硬门与未知

1. group=sympathy、CACHE skilllist、`sympathy_skill_info[_id=<cid>].ability0`，记录text含本行原文、skillid唯一、ability=3000；本行自身记录供值，不用sub或跨记录。
2. 攻撃力仅p1+p2：普通/技能攻击倍率各+10个百分点（加算增量，不是面板×1.1）；クリティカル威力仅p8：暴击伤害系数+0.1（非乘数）。按记录读取，不硬编码。
3. p6=45游戏秒已有答案零改值零丢失，不重复；p3/p4/p5/p7不得出值，防御/移速/クリ発生/回復继续未知，p4负值不得猜消费。
4. b7 hint与S3保留，完整+0；证据档按预检保守口径，numeric/association不升格为记录级执行确认，使用本批独立scope。
5. 触发和对象只按句面与规则conditions披露；不写最终面板、伤害、HP、Chain、叠加上限或账号解锁。
6. 共享记录15条的全库无p1/p2/p8答案前提须复核；同槽已有答案幂等跳过，不覆盖异值。

## 允许写入与验收

- 新模块 `scripts/character_skills/card_page_inference_c12_p1_sympathy_attack.py`；候选 `output/character_skills/c12_p1_sympathy_attack_20261031/candidate/`；临时 `work/c12_p1_sympathy_attack_20261031/`。
- `run_checks.py` 覆盖42行来源与句面、按行2/3答案、普通/技能/暴伤口径、p6保护、未知属性不消费、S3/b7保留、C11回归、共享记录、幂等、非Y.G.零连带和范围外零变化。
- 不改共享接线、rules、effect_ledger、正式pages或交接；不运行正式生成、清理、Git或新原生。
- 候选独审通过后才可进入C12交付包整合。
