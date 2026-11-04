# C14-P2 Boss 伤害 charainfo.pattern0 直接链

- 日期：2026-11-02；周期：C14-P2（实质语义批次2，候选预筛完成，待实施）。
- 状态：**候选独立审查PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0；10行／9卡／10答案及82项排除全量通过，待合并正式交付，正式生成0次**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high；例行独审：`new-provider/deepseek-v4-pro-ga-260813` high。
- 方案：`docs/角色技能完整解读实施方案.md`（2026-11-02现行），C14总卡`docs/tasks/20261102-c14-cycle.md`。

## 目标与选择理由

从Y.G.当前`ダメージ（词表外）`未解效果出发，只处理`charainfo.skilltext`行自身经`charainfo.pattern0→bosspattern→bossskill`可直接定源的伤害段。预筛保留10行／9卡：7250两段，以及30105、30107、30220、30223、30225、30301、30329、30334各一段。

这些行此前因缺少“同卡基档同值答案”而未晋级；本批不靠同文复制或基档答案作证，而是按C7-P3已验收的原始直接链口径，重新验证父记录、pattern文本、句面类型、子记录唯一性与伤害槽原值。复用既有bossskill规则与来源限定账本映射，0新公式／规则键／新原生，非Y.G.连带0。

## 预筛候选（必须逐行重导）

| cid | 行尾 | 句面 | 预选bossskill／type／伤害原值 |
|---|---|---|---|
| 7250 | skilltext f1 | 10回ダメージ | 40725002／105／skillparam1=1 |
| 7250 | skilltext f2 | 大ダメージ | 40725003／22／skillparam1=15 |
| 30105 | skilltext f2 | 5回ダメージ | 43010501／110／skillparam1=8 |
| 30107 | skilltext f3 | 6回ダメージ | 43010702／110／skillparam1=4 |
| 30220 | skilltext f1 | 2回ダメージ | 43022001／110／skillparam1=12.5 |
| 30223 | skilltext f3 | 大ダメージ | 43022302／3／skillparam1=15 |
| 30225 | skilltext f1 | 5回ダメージ | 43022502／110／skillparam1=5 |
| 30301 | skilltext f1 | 5回ダメージ | 43030102／110／skillparam1=8 |
| 30329 | skilltext f1 | 8回ダメージ | 43032901／110／skillparam1=5 |
| 30334 | skilltext f2 | 10回ダメージ | 43033402／110／skillparam1=4 |

完整row_id、原文、pattern和JSON pointer由实施从当前正式页与CACHE重导；表格只是预筛索引，不得直接当预期答案绕过门控。

## 明确排除

- **denju非首段6行继续保持未知**：7250 denju f1／f2、30105 denju f2、30301 denju f1、30329 denju f1、30334 denju f2；不得因对应charainfo行出数而顺带复制。
- 30102、20234、30236、30239不处理；APK同号记录不与CACHE合并。
- 无pattern0、pattern／sinfo文本不一致、多伤害载体无法由句面唯一选取、N回与param6不一致、伤害槽缺失／null／非有限／负值／真零、已答或异值冲突均拒绝。
- 大／中／一定间隔句只许既有单发型3／22／55／74；N回只许105／110且param6==N。其他类型、最终扣血、保证命中、运行时选档、弹射／ダウン／状态异常等同句机制不在本批。

## 实施要求

1. 新模块限`scripts/character_skills/card_page_inference_c14_p2_boss_damage_direct.py`；候选输出限`output/character_skills/c14_p2_boss_damage_direct_20261102/`，自身work限`work/c14_20261102/p2/`。
2. 先阅读并复用`card_page_inference_g1_structure.py`、`card_page_inference_c7_p3_denju.py`及C6／C7审查边界，但不得简单调用旧`NO_SAME_CARD_BASE_CONFIRMATION`结论充当本批证据。
3. 每行必须重新满足：当前row_id／cid／reference_field=skilltext；CACHE charainfo记录身份与原文；pattern0来源及pattern.sinfo与父文本一致；句面为对敌伤害实例；类型与N回／单发形态精确匹配；选中bossskill及伤害槽唯一。
4. 答案source必须直接指向选中bossskill的原始JSON记录与字段，不是charainfo、pattern或同卡其他答案。保留rule_key、raw_value、float32、table／record_id／layer／field_path／pointer、对象、条件和证据档。
5. 规则体沿用已确认局部公式，句→子记录归属保持“推断”；不把“直接链”写成引擎运行时已实机验证。若有同卡其他档位值，逐行登记为排除值，不并入、不拿来反推。
6. 幂等且不覆盖旧答案；为现有`binding.g1_b1_binding`窄映射提供完整一致的身份信息，候选阶段不得修改共享`effect_ledger.py`。若现有映射不能安全消费，先报告，不擅自全局放宽。
7. 自检覆盖10个正例、6条denju非首段反例、30102／保护卡、跨层同号、多载体、N回参数不符、文本不符、已答、缺失／null／零／负值及异档值；输出README、候选／排除JSON、check_candidate.py和机器结果，不运行正式全库生成。

## 独立审查

本轮初审运行：`dwfrun-33e72aeb-e472-4b6e-afe6-b16334e80189`（DeepSeek V4 Pro GA high）。最终[REPORT](../../output/character_skills/review/c14_p2_boss_damage_direct_20261102_deepseek/REPORT.md)／[verdict](../../output/character_skills/review/c14_p2_boss_damage_direct_20261102_deepseek/verdict.json)：`PASS_WITH_EXPLICIT_SCOPE_LIMITS`、阻塞0；`run_review.py`退出0。限制为局部伤害输入公式、denju非首段6行未知、同句残余机制待办、其他档位仅排除，浏览器／实机与正式生成未测。

审查者不import实施候选模块作为唯一依据，须从CACHE charainfo／bossinfo与当前正式行独立重导10行及排除项，核查原文、链、类型、N回、伤害槽、来源身份、证据档、单位与中文说明；写`output/character_skills/review/c14_p2_boss_damage_direct_20261102_deepseek/REPORT.md`。默认初审一次，集中修复后定向复核最多一次。

## 允许／禁止

只写上述模块、候选输出、自身work和指定审查目录。不得修改共享生产入口、正式pages／ledger／rules、其他任务文件；不得正式全库生成、清理、Git、发布、新原生、实机、新缓存、处理denju非首段或启动C15。
