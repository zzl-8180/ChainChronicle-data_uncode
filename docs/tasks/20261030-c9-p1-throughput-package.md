# C9-P1 主线提速交付包任务卡

- 创建：2026-10-30。当前状态：**已验收并收口**。最终独立审查PASS、零阻断；s1重建披露已同步进交付清单。
- 预检 `dwfrun-c6b541ff-4dd4-41bf-a9b1-43c1b0572cbe` 完成，15/15自校验通过。主持裁决：①C9-B1纳入t99敌减益4行/16答案（30101/30302/30305/30333，各p7=-0.3、p9=+0.3、p8=-0.3、p0=30），只用既有b9.evaluate与冻结4行准入，绝不全局放宽`not answers`守卫；p9按「受伤量倍率+0.3→受伤因子1.3」表述，不写固定防御−30%，p8已核样本域仅1条的限制保留。②C9-B2纳入t64受击回复7行/7答案（30110×3、30203×2、30223×2），采用t27同级「规则确认＋链内载体唯一＋句面机制唯一」标准，同卡0披露不作为阻断，跨卡30310先例不直接放行；关联推断，对象/触发只由句面给出，target_selection为空，不写最终HP/超上限/触发次数/实机间隔。两族均不改rules或effect_ledger映射，非Y.G.连带0，预期has_answer+23、unresolved/backlog−23、identified不变、完整描述+0。
- 授权：用户2026-10-30要求连续完成C8→C9→C10后再独立复审；C8已验收，本卡只推进C9，不启动C11。
- 主持／唯一整合者：本会话 new-provider/kimi-k3-260716。实施候选：DeepSeek V4.1 Flash `new-provider/deepseek-v4-1-flash-261017$high`。独立审查：DeepSeek V4 Pro GA `new-provider/deepseek-v4-pro-ga-260813$high`。

## 1. 基线与检查点

- 最近安全检查点：C8-P1已验收（`output/character_skills/c8_p1_20261030/`），最终初审18条语义全过，B1证据哈希整改后定向复审PASS、零阻断。
- campaign `f4e1bfb0c0c87f171c68db12a1c5791df7faf15e478db131205e230f7a708b84`、snapshot `f4e1bfb0-cf9451c6ff47fcfb`；rules 294键SHA-16 `cf9451c6ff47fcfb`。
- 2236卡/41665行/69964效果；has_answer 20,133（Y.G.4,438）、unresolved 49,532（Y.G.6,116）、backlog 75,725（Y.G.9,397）、完整6,471（Y.G.1,424）、拆分26,193（Y.G.3,281）。
- 容量12/12、7,782,478,303 B，上限12 run/8 GiB未放宽；正式重建前按既定模式处置。性能沿用jobs 4，不重复三档基准。

## 2. 预检范围与Y.G.优先顺序

1. **t64受击回复7行**：30110×3、30203×2、30223×2。C7-P2已证明type64 reactive-heal基值规则与既有账本映射；本批逐行重新判定是否能满足「规则已确认＋本行链内载体唯一＋句面机制唯一＋对象/触发可判定」。同卡0披露必须显式登记，不因30310跨卡先例直接放行；若主持裁决采用与t27相同的归属推断标准，最多7行/7答案，仍不写最终HP、超上限保留比例、触发次数或实机间隔。
2. **敌方减益直接链**：从当前Y.G.未解攻/防/移/时长主张中，只评估已有确认规则且本行原始链唯一、对象=敵、方向与阶段一致的记录；type13正值增益不得填敌减益，t51等负值槽须逐槽核对，不借后续段或同文猜值。
3. 其余候选只在证据已足够时列入；不重新泛化t16、1095对象不清、30102额外标签、召唤物载体或702条粗筛域，不启动新原生、30239豁免扩大、20234处置、Git、UI、发布或真正增量生成。

## 3. 预检交付

- 只写 `output/character_skills/c9_p1_20261030/precheck/` 与 `work/c9_p1_20261030/`；不改正式页面、账本、rules或生产脚本。
- 输出目标Y.G.卡/未解效果、选择理由、预期收益类别、非Y.G.连带范围与主要障碍；原始正例/反例、不同原值、空值/null/真零、跨层同号、对象/阶段不符、同值异记录、幂等及排除清单。
- 每候选按可出值并绑定／仅字段值／需补证／范围外分流；无安全新增如实登记，不承诺数量。

## 4. 后续步骤与停止条件

- 预检后按「候选实现→候选独审→合并冻结→一次正式重建→固定检查→最终独审→收官」执行；同一问题一次初审、集中修复、最多一次定向复审。
- 正式命令仅在候选独审通过后执行：`./.venv/Scripts/python.exe -X utf8 -B scripts/character_skills/card_page_batch_parallel.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --output output/character_skills/pages --execute --jobs 4`。
- C9完成后生成数据库式成果页和剩余量页，再继续C10；C8/C9/C10全部完成后停下由用户安排独立复审。
- 本卡随预检、候选、审查、冻结、生成、终验、失败或范围变化立即更新。

## 5. 最终验收与周期成果（2026-10-30）

- 候选独审 `output/character_skills/review/c9_p1_candidate_20261030_deepseek/`：PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0。
- 正式全库生成1次（jobs4、122.4s、返修0），campaign `7d0d53196d5a0fad38031a02bbeb6eb5b53e3ec280384c188c7c8f23cc2d1184`、snapshot `7d0d5319-cf9451c6ff47fcfb`；has_answer 20,133→20,156(+23)、unresolved/backlog −23、identified/完整描述不变，Y.G.+23，非Y.G.0。
- verify_full 17/17、账本9/9、A7 29/29、final_diff 29/29、隔离19卡38文件逐字节；范围外2,229卡不变。最终独审 `output/character_skills/review/c9_p1_final_20261030_deepseek/REPORT.md` verdict=PASS、blockers=0。
- 审查§8.2披露s1_fullscan.json由审查者从run_record重建并加注记；主持已用 `work/c9_p1_20261030/tools/refresh_delivery_manifest.py` 同步清单，65/65、0失配（`checks/manifest_closeout.json`）。
- 成果页 `output/character_skills/cycle_reports/C9/index.html`、剩余量页 `remaining.html`、机器数据 `report_data.json`；10个row_id/答案示例与最终审查链接经 `verification.json` 全部PASS，真实浏览器DOM和t99答案展开通过（`browser_verification.json`）。
- 工程时间：正式生成122.4s、账本25.3s、入口页7.2s；生成后容量12/12、7,783,134,602 B，上限未放宽。C9计2个实质语义批次。

## 6. 独立方向复审接收（2026-10-30）

- C8/C9/C10联合独立方向复审 `output/character_skills/review/direction_c8_c10_20261030_independent/REPORT.md` verdict=PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0、无正式产物修复要求；C9的23条答案全部独立成立。
- C9七个t64行使“部分”259→266（Y.G.53→60）、“未解析”8,742→8,735（Y.G.1,047→1,040）；完整6,471与拆分26,193不变。
- 数值口径：C9首次出现的`(rule_key,raw_value)`组合为t64/p1=2一组（30203 pattern2，记录43020305），复用既有公式，不是新公式发现；不得写为0新增唯一组合。跨效果标量新增为0，0新公式/规则键/完整描述不变。
- 接收记录 `docs/tasks/20261030-c8-c10-independent-review-closeout.md`。保持停止，不启动C11，不重新实施。
