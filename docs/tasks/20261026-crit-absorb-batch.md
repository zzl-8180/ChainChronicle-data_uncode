# 新周期批3：クリティカル吸収（StealHP/65000003）任务书

- 日期：2026-10-26。状态：**本批收口（独立初审 PASS、零阻断，无需修复轮；周期 3/3 完成，已停下待用户安排第三方独立审查）**。独审 `output/character_skills/review/crit_absorb_20261026_deepseek/REPORT.md`（dwfrun-a9126849，V4 Pro GA high）：载体唯一性与两键 conditions/answer_for、53 行范围排除、窄 variant 消费（双 refs 无 S4）、对账全一致、首建缺陷修复核实、容量处置、§1.3 与复跑全过。实施 dwfrun-a108d071 完成。**版本**：campaign `9325cf4d00a6d24db06ce822b6d9eade8cde81e9244227fb970e14691a2fd2e9`、snapshot `9325cf4d-d3790431153a5dcd`；rules 290 键未改（SHA-16 d3790431153a5dcd）。新周期第 3/3 批，**收口后停下通知用户进行第三方独立审查，未获接续指令不开新批**。

## 8. 正式收口（2026-10-26，独审 PASS）

- 独审独立核实：skillid=65000003 唯一记录（ability21、param1=0.25、flag0_1=512）；jobabilityinfo 16 条中仅 rec0（58 cids，第3◆段逐字=本句）与 rec14（8424/8425 方言）引用该载体；links cid351 的 skill_refs[2]→skilllist|65000003|CACHE，entry 无 children/sub_effect；两键 conditions/applicability 明写「仅普通65000003」、answer_for=CONFIRMED_NUMERIC；正式页 source 为 B5 registry 形状、无 work 指针。
- 范围排除：53=31 YG+22 非 YG（独立按 title 核对）；rescreen 65 行=53 ACCEPT+12 REJECT（8 无上限变体、2 方言、1 supporterskill 20907、1 零触碰 30236）；6327/8163 为 APK 同号 ability21 param1=0.15/0.12≠CACHE 0.25，证明同号不跨层；rec0 的 4 个 cid（30114/30265/30339/30340）在 2236 卡 cohort 之外（无页面），非漏处理。
- 窄 variant 消费：effect_ledger.py:313/1335-1383 两键映射+三重来源限定；positive 双 refs 无 S4，no_marker/wrong_scope/wrong_record 仅 param1 且 S4 可见；cid351 回復（词表外）has_answer 2 refs、クリティカル攻撃机制+ダメージ unresolved（0 行关闭）；S4 415→415 新增 0。
- 对账（metrics 独立读）：has_answer 19,539→19,592、unresolved 49,895→49,842、backlog 76,224→76,171、partial 100→153、unparsed 8,937→8,884；A 18,063→18,116、C 23,602→23,549；全 2236 卡 crit 答案 106（param1 53+flag0_1 53）；开局答案 1,607 保留；30236/30239 逐字节一致；HOLD18/C113/cost 原样。
- 过程：首建 432c071f source 缺陷根因修复于 card_page_inference_crit_absorb.py:203-214（B5 registry 形状）；并行度 jobs=2；容量 release1 删 4,444/留 28/元数据 4,494、release2 删 4,366/留 106/元数据 4,494，095905/145601 两代基线保留，RETAINED 12/12；§1.3 与 verify_full 17/17、A7 29/29 复跑全过。
- **非阻塞残留**：首建 106 项失败原始 verify 日志未单独落盘（文档完整性）；并行度读数为运行时快照不可重现；其余已登记项维持。
- **本周期三批（S5非地形/S5地形/クリティカル吸収）全部完成，已停下，待用户安排第三方独立审查；未获接续指令不开新批。**

## 7. 生成结果（2026-10-26，metrics 实测）

- **53 行（31 YG＋22 非 YG）/106 答案值/53 效果项翻转/0 行关闭/唯一主张 1**（按§6裁决，不为凑 55 放行方言）；每行 2 条答案（floor(伤害×0.25)；上限 1.4×最大HP），与原始记录逐值一致。
- has_answer 19,539→**19,592**（+53）；unresolved 49,895→**49,842**（−53）；backlog 76,224→**76,171**（−53）；A 18,063→18,116（+53）、C 23,602→23,549（−53）；完整 6,299 不变（0 行关闭）。
- 窄 variant 消费（binding.crit_absorb_binding：scope/row_id/record 65000003/ability21/CACHE 三重一致）：param1 与 flag0_1 被同一「回復（词表外）」主张消费，S4_unconsumed 新增=0；无标记/错 scope/错 record 不消费；其他族与既有开局/B档答案零影响。
- 排除：8424/8425 方言、8 行无上限变体、20907 CACHE 缺失、30236 整卡、P1/P3、Chain/第三套槽位/原生/cost_statement。
- 过程：首建 campaign 432c071f 因答案 source 携带 work/*.data5 指针致 source_dereference 106 项失败，修根因（改 B5 同法 registry 形状）后整轮重建统一签名；并行度实测 jobs 2（提交 75–85% 中等档）；容量两次既定模式处置（release1/release2，095905 与 145601 送审版基线保留），结束 12/12、used 7.77GB。
- 保护：旧答案零丢失零改值、范围外零变化、30236/30239 逐字节不变、HOLD18/C113/cost_statement 原样、1,607 开局答案保留。
- 未做：独立审查（已派发在途）、实机与最终 HP 验证、Git/UI/发布。
- 规则引用：`docs/角色技能完整解读实施方案.md`（2026-10-24 修订生效，含§1.3）；自动推进规划与满3批停审指示。
- 依据：`docs/tasks/20261026-yg-alternative-precheck.md`（含主持裁决）与 `output/character_skills/inference_inventory/yg_alternative_precheck_20261026/precheck_report.md`。
- 当前版本以批2收口后实测为准。容量按既定模式处置。

## 1. 范围

クリティカル吸収：**Y.G. 31 行（30236 基线整卡零触碰除外）＋同载体非 Y.G. 24 行按同规则连带（分开计数）＝55 行/110 答案值（55×2）/55 效果项翻转、0 行关闭、唯一主张 1**。

- 载体唯一：`skilllist|65000003|CACHE`（ability21 StealHP；param1=0.25＝回复 floor(伤害×0.25)，flag0_1=512＝上限 1.4×最大HP）；第 3◆段↔skill_ids[2]。
- 两规则键 `skilllist|21|/param1`、`skilllist|21|/flag0_1` 均「已确认」且 conditions 明写「仅普通65000003」，载体恰在声明样本域内；rules.answer_for 返回 CONFIRMED_NUMERIC；不需要新原生。
- 门控：table=job_ability∧CACHE、逐字句、◆3→skill_ids[2]、载体=65000003∧ability21、param1==0.25∧flag0_1==512、cid≠30236、无既有答案。
- 每行仍有クリティカル攻撃机制、ダメージ 两项无答案型，**0 行关闭**，不得把整行写成完整。
- 排除：8 行无上限变体、8424/8425 方言、20907 支持技能载体 CACHE 缺失、30236 整卡、P1/P3 各池、Chain/第三套槽位/原生未授权项、cost_statement。

## 2. 判定与保护

- 逐行门控：上述载体/句式/段序/原值四重一致才出答案；同号记录不跨层取值（CACHE 载体 only）；无既有答案才新增；profiles children 链注意 sub_effect 同号碰撞伪影（b9 §5.1 B1 同法）。
- 保留：旧答案零丢失零改值、范围外零变化、30236/30239 零触碰、HOLD18/C113/cost_statement 原样、開局マナ与 B 档答案不改写；未知保留。
- rules.json 与 rules.py 本批不改（两键已存在）；effect_ledger._RULE_KEY_EFFECT 增两键映射（skilllist|21|/param1、/flag0_1）属本批范围，须来源限定、不影响其他族与既有 1,209+ 开局答案。

## 3. 写入范围

实施：`scripts/character_skills/card_page_inference_crit_absorb.py`（新模块）、`output/character_skills/crit_absorb_20261026/`、自身 work；effect_ledger.py 仅上述两键映射；独审：`output/character_skills/review/crit_absorb_20261026_deepseek/`。主持：任务卡、进度、容量与共享整合。

## 4. 验收

- 55/55 行各 2 条答案（floor(伤害×0.25)；上限 1.4×最大HP），与原记录逐值一致；账本两键映射后 55 项转 has_answer、其余零翻转；两项机制效果保持 unresolved。
- 固定检查：verify_full 17/17、账本 9/9、A7 29/29（先存旧结果）；final_diff（新增与重筛逐键相等、旧答案零改、范围外零变化、30236/30239 零触碰、HOLD18/C113/cost_statement 原样）；隔离复跑代表卡；容量按既定模式处置留回执。**并行度先检后定**（同自动推进规划§6操作规则：按重建前内存/CPU/磁盘实测选 jobs 4/2/1，检查输出写入 run_record，当前基准 jobs 2；MemoryError 时串行重建失败卡）。
- §1.3 中文：回复量与上限分别就近标注，推断/确认按两键证据档如实（CONFIRMED_NUMERIC 与类型级关联分层），不宣称整行/整卡完成。
- 独审（V4 Pro GA high，初审一次＋集中修复后定向复核一次）：重点＝载体唯一性与样本域、◆3→skill_ids[2] 段序、非 YG 连带同规则同门控、30236 零触碰、0 行关闭。
- 模型：实施 DeepSeek V4.1 Flash high、独审 V4 Pro GA high，显式 `$high`。

## 5. 停止边界

不做 8 行无上限变体/方言/CACHE 缺失行、Chain/第三套槽位/新原生/cost_statement/其他词族；不 Git/UI/发布；证据冲突停车报主持。**本批收口＝周期 3/3，停下通知用户进行第三方独立审查。**

## 6. 主持裁决（dwfq-a108d071-1，2026-10-26）

- **范围按证据修正为 53 行**（31 YG＋22 非 YG）：8424/8425 方言按任务书排除，55 是未剔除方言前的口径，不得为凑数放宽逐字句；验收同步为 53/53 行各 2 条答案（106 值/53 项翻转）。
- **账本加来源限定双槽 variant 消费**（按 mana_b 先例，仅作用于带本批 scope 标记的答案）：param1 与 flag0_1 被同一「回復（词表外）」主张消费，**S4_unconsumed 新增必须为 0**；不使用 HP 档位 label（语义不符）。其他族与既有开局/B档答案零影响；无合格答案行不得新增未解决主张或拆分；两项机制效果保持 unresolved、0 行关闭；30236/30239 零触碰。
- 探针：param1/flag0_1 双消费正例、无标记/错 scope/错 record 反例、其他族不受影响证明；final_diff 以 53 行/106 值逐键对账。20907 CACHE 缺失与 8 行无上限变体继续排除。
