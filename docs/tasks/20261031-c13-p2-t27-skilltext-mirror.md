# C13-P2 t27 同卡同文回复镜像

- 日期：2026-10-31；周期：C13-P2（实质语义批次2/3，候选阶段）。
- 状态：**正式交付完成；候选独立审查PASS、正式终审PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0；3行3答案**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high；例行独审：`new-provider/deepseek-v4-pro-ga-260813` high。
- 方案：`docs/角色技能完整解读实施方案.md`（2026-10-31现行），C13总卡 `docs/tasks/20261031-c13-cycle.md`。

## 目标与范围

候选仅3卡3行3答案：10215、30228、30314的`special_move.skilltext`行，句面均为「【共鳴必殺/連撃】味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。」；同卡`pattern0`同文行已有`bossskill|27|/skillparam1`答案。目标只补单次回复系数p1，候选原值依次为1.25／1.25／1.75。

镜像扫描：`work/c13_20261031/mirror_scan.json`。既有证据：C8 t27周期回复、C10同卡同记录镜像及当前正式页面答案。非Y.G.连带0。

## 实施要求

1. 新模块限 `scripts/character_skills/card_page_inference_c13_p2_t27_mirror.py`；候选输出限 `output/character_skills/c13_p2_t27_mirror_20261031/`，自身work限 `work/c13_20261031/p2/`。
2. 逐行核对同卡同文身份、skilltext／pattern0来源、charainfo.pattern0→bosspattern→skillid0→bossskill链，确保链内唯一type27且record_id／field／raw与既有答案一致。不得只按日文或数字跨表选值。
3. 只新增`bossskill|27|/skillparam1`单次回复系数答案；p2间隔和p3次数只可按既有证据披露，不写成新增答案；不处理「全状態異常」、超上限保留比例、最终HP、实际间隔／次数或Boss pattern选择。
4. 数值规则体保持既有级别，skilltext↔pattern关联保持推断；对象仅按句面「味方全体」，条件写明对应pattern／skilltext结构，不宣称实际装载或实机。
5. 不修改既有pattern答案，不处理其他pattern／super／denju，不把C8／C10已交付项重复计收益。保护卡20234、30102、30236、30239硬拒绝。
6. 自检覆盖3正例、同文异档反例、错误pattern／非唯一type27／raw不一致拒绝和保护卡；输出README、候选JSON、检查脚本与结果，不运行正式全库生成。

## 独立审查

审查者独立读取原始CACHE链和既有规则，逐行核来源、原值、单位、对象、条件、证据档、p2／p3边界和旧答案保护；报告写 `output/character_skills/review/c13_p2_t27_mirror_20261031_deepseek/REPORT.md`。默认初审一次，集中修复后定向复核最多一次。

## 允许／禁止

只写上述模块、候选输出、自身work和指定审查目录；不得改共享生成器／账本／rules／正式pages，不得新原生、实机、新缓存、正式全库生成、清理、Git、发布或C14。
