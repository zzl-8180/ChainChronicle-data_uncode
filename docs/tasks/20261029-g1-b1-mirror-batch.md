# C6 批2：G1-B1 必殺ダメージ镜像绑定 25 项 任务书

- 日期：2026-10-29。状态：**已收口，独立初审 PASS、零阻断**（独审 `dwfrun-45792498-9965-47aa-bb10-434aad5e8041`，V4 Pro GA high；报告 `output/character_skills/review/g1_b1_20261029_deepseek/REPORT.md`：独审不 import 实施模块，从原始 CACHE denju/charainfo/bossinfo 独立重导 25/25 原始链、O02 排除值、片段判别、账本指标、source 解引用与 rules/保护项）。残留登记：①verify_full/A7/账本为实施自检，独审未逐脚本重跑但已独立重算核心断言；②7251 记录不唯一值唯一为设计内已知情况、非缺陷；③S7（same_cond_alt_t13）6 行、S3 25 行、S3b 15 行残留，未声称已解，与 split 不承诺关闭一致。首轮 source 缺陷已补 source 并整轮重跑，最终 25 条 source 独立解引用 25/25 OK。C6 第 2/3 批收口。实施 `dwfrun-3e28d490-850f-4459-a847-2ee64db17e54` 完成：25 行/21 卡全 Y.G. 镜像绑定，0 新增唯一数值；25/25 选中记录∈本行原始链（19 denju＋6 charainfo.pattern0），24 行与同卡基础档位行答案 record_id 一致，7251 同值异记录 0.83 已写明；23 行/25 个链外档位值与预检逐项一致。账本 has_answer 20,043→20,068(+25)、unresolved 49,622→49,597(−25)、backlog 75,815→75,790(−25)、A+22/C−22、identified/split/complete/partial/unparsed 零漂移；25 行仍拆分待核查（S3 25、S3b 15、S7 6 未关闭）。campaign `5f6581da0f0f946779af380407a92fd0067eccd68dd78af10228c9455c0eb752`、snapshot `5f6581da-cf9451c6ff47fcfb`；rules 294 键未改。verify_full 17/17、账本 9/9、A7 29/29、final_diff/baseline_diff PASS（2,215 卡逐字节不变）、隔离复跑 22/22、scratch pre 24/24＋post 25/25、账本预检字节全等；容量两轮处置 PASS（收尾 7,780,510,022 B、上限未放宽）；jobs 4。披露：首轮 25 条 source 缺 source_key/original_file 致 source_dereference 失败，补 source 后按既定模式释放中间轮并二次重建（差异仅 source）；预检「S7 可解」实测未关闭，按 split 不承诺关闭登记；片段判别为类型语义＋25 项一致性推断（非原生证据，标推断）。C6 第 2/3 批。
- 依据：`output/character_skills/inference_inventory/next_cycle_precheck_20261029/`（precheck_report.md、`g1_b1_admission_final.jsonl`、`g1_b1_o02_admission.jsonl`）与高强度独审 O02。所有计数从原始记录与当前正式页重导，不搬旧数。
- 当前版本以开工实测为准（批1 campaign `3ca79d753a7a1bb1327df2436f63db3f024f50c5099b9f7fea7473ba5ad528ac`、snapshot `3ca79d75-cf9451c6ff47fcfb`；rules 294 键 SHA-16 `cf9451c6ff47fcfb`，本批不改 rules.json/rules.py）。容量按既定模式处置，并行度先检后定。

## 1. 目标与范围

**G1-B1 必殺ダメージ镜像行绑定修正 25 行/21 卡（全部 Y.G.）**，不新增唯一数值：

- 词条示例：「その後、前方範囲内の全ての敵に大ダメージを与え、弾き飛ばし、ダウンにする。」（351）、「その後、前方範囲内の全ての敵に10回ダメージを与え、弾き飛ばし、ダウンにする。」（2331）、「その後、前方範囲内の全ての敵に15回ダメージを与え、弾き飛ばす。」（7251）。
- 只补 6 个既有确认规则键的账本映射：`bossskill|3|/skillparam1`、`|22|/skillparam1`、`|105|/skillparam1`、`|110|/skillparam1`、`|55|/skillparam1`、`|74|/skillparam5`（均已是已确认规则，**不动 rules.json**；另 4 个 76/112/51/47 不预登记）。
- 定源路径：19 行 denju→patternid0→bosspattern→bossskill；6 行 charainfo.pattern0→bosspattern→bossskill（charainfo 自带 pattern0，禁止同文复制）。
- 片段判别：写 N回→多段型（105/110）param6==N（2331/7251/30327 三行）；写大/中/一定间隔→单发型（3/22/74/55）恰 1 条。该对应为类型语义与 25 项一致性推断，**不是原生证据**，答案关联档标推断。
- 账本预期：25 条既有 unresolved→has_answer；行仍拆分待核查（S3/S3b 残留，弾き飛ばし/ダウン/状態異常未解），**完整行 +0、split 不承诺关闭**。

## 2. O02 定源与排除值（硬门）

25/25 必须选中本行原始链记录，且选中记录＝同卡对应基础档位行答案 record_id（7251 同值异记录 40725100/40725101 均 0.83，写明记录不唯一但值唯一）；23 行链外档位值逐行登记为排除值：

- 351→40035101(t3)=30，排除 34.5；352→40035201(t22)=15，排除 19.5；2331→40233101(t110)=3，排除 3.5（N回 param6=10，链内 p6=5 排除）；4315→40431501(t3)=17.5，排除 20.5；7251→40725100(t105)=0.83，排除 lvl2 1.083。
- 30108→43010801(t3)=30，排除 32.5；30109→43010901(t22)=30，排除 32.5；30110→43011001(t3)=30，排除 32.5；30232→43023202(t74)/skillparam5=40，排除 42.5/47.5；30247 charainfo.pattern0→43024701(t3)=13.75，排除 17.5。
- 30258→43025801(t3)=17.5，排除 20.5；30303→43030301(t22)=10，排除 12.5；30309→43030901(t22)=31.25，排除 34.5；30310→43031002(t74)=15，排除 20；30317→43031701(t22)=17.5，排除 21。
- 30323→43032302(t55)=1.6，排除 1.8；30324→43032401(t3)=20，排除 22.5；30325→43032501(t55)=1（唯一档，无排除）；30326→43032601(t3)=25，排除 28.5；30327→43032701(t110)=5，排除 5.5；30330→43033001(t3)=16，排除 19。
- 30232 pattern0 镜像行同一 rule_key 出现 2 次须先去重；6 个 charainfo 行是账本 S7（same_cond_alt_t13）行，绑定后 S7 可解，S3/S3b 仍在。

## 3. 判定与保护

- 门控：原始链唯一命中/同值唯一、句面片段判别、选中记录与同卡基础档位行答案一致、排除值逐行在案；链外档位/多值不唯一/引用不全留 hint 不出数；CACHE/APK 按载体所在层取值不跨层。
- 保留：旧答案零丢失零改值、范围外零变化、30236/30239 零触碰（30239 G0 豁免不扩大）、HOLD18/C113/cost_statement 原样、開局/B档/type67/gold_exp/heal_interval/type80_96/g0_g7b0/kill_mana 既有答案不改写；R01 边界文案不回退；不新增最终伤害或实机验证结论。
- effect_ledger 仅本批来源限定窄映射（g1_b1_binding 标记＋上述 6 键，其他行映射行为零变化）；「新码×旧页」账本预检字节全等为硬门。
- 验收：25/25 选中记录∈本行原始链且与同卡基础档位行答案 record_id 一致；23 行排除值逐行核对；0 新增唯一数值；25 条 unresolved→has_answer；verify_full 17/17、账本 9/9、A7 29/29（先存旧结果）、final_diff（新增/绑定与重筛逐键相等、白名单外零变化）、隔离复跑代表卡（351/2331/7251/30232/30309/30325）逐字节；scratch 原错误/相邻变体/正确保留三类用例（含 351 30 vs 34.5、2331 N回 param6、7251 同值异记录、30232 去重）。
- §1.3 中文：写「镜像行按原始链定源到 bossskill 记录与档位，倍率见同卡基础档位行；链外档位值排除」；标推断，不写成同文复制或最终伤害。

## 4. 写入范围

实施：`scripts/character_skills/card_page_inference_g1_b1.py`（新绑定生产者）、`scripts/character_skills/effect_ledger.py`（仅本批窄映射＋6 键）、`output/character_skills/g1_b1_20261029/`、自身 work；card_page_data.py 接入由实施按任务书执行；独审：`output/character_skills/review/g1_b1_20261029_deepseek/`。主持：任务卡、进度、容量与共享整合。

## 5. 验收与流程

预检口径核对→实施自检三用例→四 cohort 统一签名重建（并行度先检后定）→账本/入口/选题（F03）→verify_full 17/17、账本 9/9、A7 29/29（先存旧结果）→final_diff→隔离复跑→独审（V4 Pro GA high，初审一次＋集中修复后定向复核一次）。容量按既定模式处置留回执。模型：实施 DeepSeek V4.1 Flash high、独审 V4 Pro GA high，显式 `$high`。

## 6. 停止边界

不做 G7 各段、G1 其他档、30239 子项、20234 跨层处置、Chain/新原生/cost_statement/其他词族；不 Git/UI/发布；证据冲突停车报主持。本批收口计 2/3，随后批3＝G7-B1 type13 首段 3 行，满3批后停下通知用户第三方独立方向审查。
