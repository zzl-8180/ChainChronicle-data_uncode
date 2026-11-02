# C11-P2 skilllist|1059| UnionCount 队伍增益

- 规则入口：现行实施方案、`docs/tasks/20261031-c11-c13-three-cycle-plan.md` 与预检 `output/character_skills/c11_p2_selection_20261031/selection_report.md`。
- 状态：**独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0；14行/70答案/完整14行，可进入C11交付包。两项low限制登记：披露示例参数化留待未来扩展、非Y.G.探针缺口已由审查补验**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high，dynamic workflow。
- 例行独审：独立新上下文，`new-provider/deepseek-v4-pro-ga-260813` high。

## 范围与预期上限

仅预检冻结的14张Y.G.卡、14条 `…-ability-ability-skillid_2_-lvorder1-f0`：1303、30002、30112、30113、30218、30240、30243、30248、30249、30250、30336、352、353、7250。每行五属性效果，潜在上限 **14行／70答案，14行由未解析→完整**；不是承诺收益，任何一行证据失败即保留未解。

复用既有 `skilllist|1059|/param1..param5` 换算与 `union_count_chains.json` 已验证受控原生证据；0新公式、0新规则键、0新原生。主持已裁决候选可准备**恰好5条键精确账本映射**：p1→攻撃力、p2→移動速度、p3→防御力、p4→クリティカル発生率、p5→クリティカル威力；p0、筛位、p6/p7不接。

## 逐行硬门

1. group=ability、CACHE skilllist、`reference_field=skillid[2]`、页面指针与charainfo.skillid[2]一致；skillid全表唯一，ability=1059。
2. param0..5存在且为有限数值，iParam1=31，param9/flag1_0=0；恰一个筛选维度非零，解码集合与句面〈…〉逐项相等。模块不得含row_id/记录/原值白名单，scope须显式声明。
3. 句面在本卡skillid记录中唯一命中；只消费首段1059，不把sub[4]第二◆段机制归入本句。
4. p1攻击×1.15、p2移动速度×1.15、p3受伤量×0.85（减伤15%，不是固定防御或防御−15%）、p4暴击率+15个百分点、p5暴击伤害系数+0.15；实际值从记录读取，不硬编码。
5. p0只是人数阈值；聚合为极值选择而非按人叠乘。「多いほど」人数比例与「5人まで」上限未知，不根据原文5人反推比例。另行的原文「5人」答案零改值零丢失。
6. 对象由句面与iParam1/筛位双向支持，关联仍为推断，不升级记录级执行或实机确认；不写最终伤害、HP或叠加上限。

## 允许写入与验收

- 新模块 `scripts/character_skills/card_page_inference_c11_p2_union_count.py`；候选 `output/character_skills/c11_p2_union_count_20261031/candidate/`；临时 `work/c11_p2_union_count_20261031/`。
- 候选提供五条映射的独立patch/JSON和内存账本干跑，不改共享effect_ledger、card_page_data、rules、正式pages或交接文件。
- `candidate/run_checks.py` 必须覆盖14行来源与筛位、70答案、五映射、完整度、第二段不归属、原文5人保护、C11-P1回归、幂等、非Y.G.零连带、30236/30239零触碰和范围外零变化。
- 排除30102/20234、denju非首段、状态异常回复、t11/t84/t16/1095/t114及非Y.G.卡；不启动新原生、实机、正式生成、清理或Git。
- 候选独审通过前只写候选完成，不得放行C11-P3或正式交付。
