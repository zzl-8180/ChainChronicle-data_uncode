# C20：直接伤害来源绑定与条件选档收口记录

- 日期：2026-11-09；F01收口更新：2026-11-11；状态：**全部交付与审查完成（明确范围限制）；F01=CLOSED／不启动C21、清理、Git或发布**。当前成果入口为 `output/character_skills/cycle_reports/C20_r02_20261109/`。
- 最终工作流：`dwfrun-0be5a878-aa3f-4d52-bb9b-ee5fcf20d115`，结论C20完成，10个阶段全部通过。
- 最终方向复核：`dwfrun-f66358e8-66f3-42b0-92b5-82a5fc054298` 的 F1 已关闭，后续最终定向复核为 **7/7 PASS、阻断0**。

## 1. 版本与真实增量

- campaign `754f04b6f552fc2a993c7c7b1de233fc7d138cbac35497c28ce12478a30f4373`
- snapshot `754f04b6-cf9451c6ff47fcfb`
- rules 294键，SHA-16 `cf9451c6ff47fcfb`，未改。
- 合计 **16卡18行18效果25答案**：P1 9卡10行10效果10答案；P2 7卡8行8效果15答案。CACHE 16条／APK 9条；五个既有bossskill伤害规则键，0新键。
- Y.G.效果+10／非Y.G.效果+8；答案Y.G.10／非Y.G.15。18效果与25答案分列，不混为同数。
- 15行21项行级拆分机制默认披露；目标effect级未解为0。关联推断、runtime_verified=False，未做新原生执行或实机，最终扣血／命中／运行时装载未验证。

## 2. 当前账本

| 指标 | all | Y.G. |
|---|---:|---:|
| has_answer | 21,523 | 5,386 |
| unresolved | 48,142 | 5,168 |
| justified_na | 299 | 40 |
| identified | 69,964 | 10,594 |
| backlog | 74,335 | 8,449 |
| complete | 6,614 | 1,464 |
| partial | 298 | 72 |
| unparsed | 8,560 | 988 |
| split_check | 26,193 | 3,281 |
| A | 18,532 | — |
| C | 23,133 | — |
| 整行推断 | 6,370 | 2,099 |

相对C19：has_answer +18、unresolved −18、backlog −18；完整+3、部分+0、未解析−3、拆分+0；A +9／C −9／整行推断+0／S4 +0。

## 3. 审查与验证闭环

- 两批候选各22/22；静态F 11/11。
- Pro正式候选独审16/16、阻断0；恢复定向复核通过。
- A–F合并预检全部通过。
- 第一次全库生成16目标卡因marker tuple→JSON list失败，修复后16/16 validate通过；经用户明确授权后，一次纠正性全库构建完成2,236卡、失败0。
- 入口页曾误用首次失败的不完整campaign摘要，改为C19完整指标＋实际增量，实测planned mismatch={}；后续仅resume-post-build，没有再次全库生成。
- `verify_full` 17/17、`final_diff` 36/36、A7 29/29、24卡48文件隔离一致、`validate_formal` 26/26。
- Pro正式独立终审27/27、阻断0。
- 成果页详细对账34/34：25答案与正式pages逐项一致、18效果has_answer、26链接0断、2,279个正式输入文件SHA不变、重跑逐字节一致。
- F1定向复核19/19；最终复核7/7：8个登记文件SHA及字节数全部匹配，manifest/handoff不含自身、无循环哈希，浏览器UNTESTED。
- **F01展示整改承接**：收口后原Sol独立复审v05（349项中348通过）指出展开层缺完整父集合和具体合并／排除分支；F01展示R01主持29/29后，原Sol `f01_recheck_v01`（380项中373通过）确认补齐，但发现7条父标记语义错误。F01展示R02统一区分`current_parent`与`selected`，主持41/41后，原Sol最终R02复验 **565/565、F01=CLOSED、PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0**。
- 最终R02独立解析25答案、只读引用0；7条异父、18条同父、原三个反例、25份父集合、6项合并、2项排除、不变量及11文件清单全部通过。主审查、隔离展示生成和入口自检均退出0；父代理验收及125份父跟踪文件无变化。

## 4. 关键答案边界

- 20332：8父按同记录合成4档20／19／18／17，HP整数百分比与0th／1st以上Chain标签正确；只答前方敌人，自身受伤与type116另论。
- 12236：pattern1初始1.25、使用一次后强化1.5；pattern3只取当前父41223605＝2，旧41223602不计新增。
- 5300：常规与森林（含夜间）limit<3共用同记录1.75，非森林或耗尽回退基础分支。
- 7654：预测扣费后职业法珠0–2＝4.5、3–12＝6。
- 12032：0–3与4–12废料同值异记录4.5合记一项，不任选父或重复计答案。
- 12226：0–2＝0.75、3–12的raw为`1.100000023841858`，玩家文案1.1不覆盖raw；12回是次数。
- 20619：0–1＝35、2–12＝37.5；超共鸣父不并入，但在答案内登记排除。
- P1 pattern行不是复制C14 skilltext镜像答案；其它pattern、denju、回复、增益、异常、周期攻击及句外强化不并入。

## 5. 交付入口

- **当前R02成果**：[成果页](../../output/character_skills/cycle_reports/C20_r02_20261109/index.html)／[剩余量](../../output/character_skills/cycle_reports/C20_r02_20261109/remaining.html)／[25答案台账](../../output/character_skills/cycle_reports/C20_r02_20261109/answer_ledger.json)／[展开审计](../../output/character_skills/cycle_reports/C20_r02_20261109/expanded_display_audit.json)。
- **当前R02清单**：[final_manifest](../../output/character_skills/cycle_reports/C20_r02_20261109/final_manifest.json)，SHA-256 `2def5740d286d193cccea0b4d88aefe4c2a1fae830e7593a809dc6710434d553`；[handoff_verification](../../output/character_skills/cycle_reports/C20_r02_20261109/handoff_verification.json)，SHA-256 `fec08de8f036dec526e541d505d74b1ed0bcf6cb80018a70b173e01264f5fdf0`。
- **F01最终复验**：[原Sol R02 REPORT](../../output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_r02_v01/REPORT.md)／[verdict](../../output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_r02_v01/verdict.json)／[25答案独立台账](../../output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_r02_v01/answer_ledger.json)／[commands](../../output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_r02_v01/commands.json)；[父代理验收](../../work/c20_post_closeout_independent_recheck_20261109/f01_recheck_r02_v01/parent_acceptance.json)。
- **F01历史承接**：[原v05 REQUEST_CHANGES](../../output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/v05/REPORT.md) → [R01任务卡](20261109-c20-f01-expanded-parents.md) → [R01复验REQUEST_CHANGES／7条父标记问题](../../output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_v01/REPORT.md) → [R02任务卡](20261109-c20-f01-parent-marker-r02.md) → 上述最终通过。旧裁决及送审清单均不改写。
- **原C20历史成果**：[成果页](../../output/character_skills/cycle_reports/C20/index.html)／[剩余量](../../output/character_skills/cycle_reports/C20/remaining.html)
- 原C20 [final_manifest](../../output/character_skills/cycle_reports/C20/final_manifest.json)，SHA-256 `8bdfd2c88646ab64c82cd2f926c58b865ae9ad17b1149d8fc8629d0fe881fddf`
- 原C20 [handoff_verification](../../output/character_skills/cycle_reports/C20/handoff_verification.json)，SHA-256 `cdf54d38821a37dd9e7befde5ee88cc3ae350f714cbe7140de2cd58021b9eb39`
- [正式run_record](../../output/character_skills/c20_delivery_20261108/run_record.json)，SHA-256 `e277dd1f58c02ffdd7619d767143337a593cb4eaaaf921b6ffb67bca529cc4cc`
- [候选独审](../../output/character_skills/review/c20_attack_candidates_20261108_deepseek/REPORT.md)
- [恢复定向复核](../../output/character_skills/review/c20_recovery_r01_20261108_deepseek/REPORT.md)
- [正式独立终审](../../output/character_skills/review/c20_delivery_final_20261108_deepseek/REPORT.md)
- [原方向复核](../../output/character_skills/review/direction_c20_20261108_thirdparty/REPORT.md)
- [F1定向复核](../../output/character_skills/review/direction_c20_20261108_thirdparty_recheck/REPORT.md)
- [最终定向复核](../../output/character_skills/review/direction_c20_20261108_thirdparty_final_recheck/REPORT.md)／[verdict](../../output/character_skills/review/direction_c20_20261108_thirdparty_final_recheck/verdict.json)
- [合并预检](../../output/character_skills/c20_delivery_20261108/precheck/check_report.json)／[只读验证](../../output/character_skills/c20_delivery_20261108/checks/validate_formal.json)
- [R01整改与预审查保留件](../../output/character_skills/rectification_c20_r01_20261108/README.md)

## 6. 非阻断说明、历史时点与容量

- 原v05与`f01_recheck_v01`的REQUEST_CHANGES／F01 OPEN保留为历史裁决，分别由原Sol确认R01字段补齐和指出R01父标记问题；最终由R02复验565/565关闭F01。R01/R02清单、handoff及旧报告中的PENDING／OPEN仅表示送审时点，不回写或重签，当前状态由[最终R02复验](../../output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_r02_v01/REPORT.md)与本记录承接。
- N01（CID30225分组相关`record_evidence`元数据差异）仍为非阻断，未纳入F01整改，也未借本轮修改正式数据。

- `verification_detailed.json` 的 `readme_and_remaining_present.detail.readme_bytes=2945` 是finalize前点内快照；当前README为3,225 B。最终方向复核已明确记录此非阻断观察，manifest与当前README哈希、字节数一致，未据此伪造统一快照。
- `final_manifest.json` 的 `status=FINALIZED_PENDING_ORIGINAL_THIRD_PARTY_RECHECK`、`handoff_verification.json` 的 `original_third_party_recheck=PENDING`，以及正式／周期run_record中的“待正式独立审查／待原第三方定向复核”文字，均是相应文件生成时的冻结时点。当前状态由后续[最终定向复核](../../output/character_skills/review/direction_c20_20261108_thirdparty_final_recheck/REPORT.md)7/7 PASS承接；为保持已审文件及哈希，不追溯改写这些历史字段。
- 当前 **RETAINED 8/12、reserved_bytes 5,353,728,612 B**。清理、Git提交／推送、发布和C21均未执行，不能将C20完成写成清理或实机完成。
- 默认中文无raw／公式／表名／指针泄漏；展开层保留完整来源、条件和排除。静态HTML检查不冒充浏览器视觉验收，第三方浏览器继续UNTESTED。

## 7. 可复用经验

1. 正式答案必须保持JSON原生类型，避免tuple进入marker导致HTML payload不一致。
2. 同规则多分支答案必须走精确row／effect_type／span／pattern变体消费，不能只追加后任由S4暴露。
3. P2同时有CACHE与APK时，binding批次按答案自身判断，不按来源层判断。
4. 恢复时不能拿失败campaign的部分摘要当完整基线；只能用C19完整指标加本批真实增量。
5. verdict／verification的`blocking`、`blocking_count`、`status=PASS`与`checks_total=checks_passed`结构必须显式兼容；流程误判不能改写实际审查结论。
6. final_manifest与handoff必须单向记录，README、当前文件和清单分别保留真实时点，不能用新manifest掩盖旧快照差异。
7. 展示父标记必须分别表达`current_parent`（描述来源父）与`selected`（本答案分支父）；相同则同父双标，不同则分别落位。`pattern_id`与子`record_id`不可互推，验收须定位同row、同record及具体父`li`，不能以整页出现ID代替。
