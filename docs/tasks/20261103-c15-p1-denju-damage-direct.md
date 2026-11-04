# C15-P1 denju 非首段伤害直接链

- 日期：2026-11-03；周期：C15-P1（实质语义批次1，候选阶段）。
- 状态：**候选独立审查PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0；6行／5个cid／6答案及32项排除全量通过，待合并正式交付，正式生成0次**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high；例行独审：`new-provider/deepseek-v4-pro-ga-260813` high。
- 方案：`docs/角色技能完整解读实施方案.md`（现行），C15总卡`docs/tasks/20261103-c15-cycle.md`。

## 目标与选择理由

补齐C14-P2明确排除的denju非首段6行伤害答案。现在这些行已有同卡charainfo直接链同记录同原值作交叉证据，且denju自身`patternid0`也能独立定源，因此可以按**denju原始直接链**交付，不再只是同文镜像候选。

全部6行／5个cid均为Y.G.，非Y.G.连带0。复用既有`bossskill|105|/skillparam1`、`bossskill|110|/skillparam1`、`bossskill|22|/skillparam1`与`binding.g1_b1_binding`窄映射，不新增公式、规则键、账本映射或原生研究。

## 冻结预检行

| cid | denju行 | patternid0 | 选中bossskill | type | 句面 | 原值 |
|---|---|---:|---:|---:|---|---:|
| 7250 | f1 | 40725003 | 40725002 | 105 | 10回ダメージ | skillparam1=1 |
| 7250 | f2 | 40725003 | 40725003 | 22 | 大ダメージ | skillparam1=15 |
| 30105 | f2 | 43010502 | 43010501 | 110 | 5回ダメージ | skillparam1=8 |
| 30301 | f1 | 43030103 | 43030102 | 110 | 5回ダメージ | skillparam1=8 |
| 30329 | f1 | 43032903 | 43032901 | 110 | 8回ダメージ | skillparam1=5 |
| 30334 | f2 | 43033403 | 43033402 | 110 | 10回ダメージ | skillparam1=4 |

主持已直接从CACHE `denju.data5.json.raw`与`bossinfo.data5.json.raw`核对：每行`denju.stext==bosspattern.sinfo`、类型与原值相符、N回与`skillparam6`相符、选中记录属于该pattern。实施必须重新证明，不得把表格当免检答案。

## 实施要求

1. 新模块限`scripts/character_skills/card_page_inference_c15_p1_denju_damage_direct.py`；候选输出限`output/character_skills/c15_p1_denju_damage_direct_20261103/`，自身work限`work/c15_20261103/p1/`。
2. 每行重新验证row_id、cid、`group=denju`、`reference_field=denju.denju_id == cid`、denju记录唯一、原文与`pattern.sinfo`一致、行片段在denju.stext中恰一次、patternid0唯一命中、子记录连续且唯一可解析。
3. N回只取type105／110且`skillparam6==N`恰一条；大／中／一定间隔只取既有单发型3／22／55／74恰一条。多候选、类型不符、指针漂移、文本不符、缺失／null／非有限／零／负值均拒绝。
4. 答案source必须直接指向选中bossskill的原始JSON记录及`skillparam1`，不是denju、pattern或同卡其他答案。保留float32、原始JSON pointer、table／record_id／layer／field_path、rule_key、对象、条件与证据档。
5. 数值规则体已确认；句面→子记录归属保持推断。不得写最终扣血、保证命中、运行时选档、玩家解锁或实机结论。
6. 同卡charainfo的C14-P2同记录同原值只作交叉核，不替代denju链。检查其他档位值只登记排除，不并入；不能用charainfo.pattern0覆盖denju.patternid0的实际记录。
7. 幂等且不覆盖旧答案；为现有`binding.g1_b1_binding`提供完整一致的scope／rule_key／field_path／table／record_id／layer/source身份。候选阶段不得修改共享`card_page_data.py`、`effect_ledger.py`、正式pages／ledger／rules，不运行正式全库生成。
8. 自检覆盖6个正例、其他非首段反例、跨层同号、多载体、N回参数不符、文本不符、已答、缺失／null／零／负值、异档值及保护卡；输出README、候选／排除JSON、`check_candidate.py`和机器结果。

## 独立审查

本轮初审运行：`dwfrun-b23aa879-b7d8-4204-b7b0-f30a5c4e79b1`（DeepSeek V4 Pro GA high）。最终[REPORT](../../output/character_skills/review/c15_p1_denju_damage_direct_20261103_deepseek/REPORT.md)／[verdict](../../output/character_skills/review/c15_p1_denju_damage_direct_20261103_deepseek/verdict.json)：`PASS_WITH_EXPLICIT_SCOPE_LIMITS`、阻塞0；`run_review.py` 10项检查通过、退出0。送审模块SHA-256 `e2f67d026e26d89dc4142be0694d170059164a821666827c0cc32f00410e8cec`；`candidates.json` `a186065351009e9b59442f93fe29a7a2efe70a385afbb865c8a29eb392f9aee8`。

审查者不得只import实施模块作为依据，须从CACHE denju／bossinfo与当前正式行独立重导6行及排除项，核对原文、链、类型、N回、伤害槽、来源身份、证据档和中文说明；写`output/character_skills/review/c15_p1_denju_damage_direct_20261103_deepseek/REPORT.md`。默认初审一次，集中修复后定向复核最多一次。

## 允许／禁止

只写上述模块、候选输出、自身work和指定审查目录。不得修改共享生产入口、正式pages／ledger／rules、其他任务文件；不得正式全库生成、清理、Git、发布、新原生、实机、新缓存或启动C16。
