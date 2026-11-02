# C13-P1 supporterskill→abiN 的 type8 基础增益

- 日期：2026-10-31；周期：C13-P1（实质语义批次1/3，候选阶段）。
- 状态：**正式交付完成；候选及正式独立审查PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0；61行89答案**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high；例行独审：`new-provider/deepseek-v4-pro-ga-260813` high。
- 方案：`docs/角色技能完整解读实施方案.md`（2026-10-31现行），C13总卡 `docs/tasks/20261031-c13-cycle.md`。

## 目标与选择理由

从Y.G. supporterskill未解效果出发，利用记录自身的`abiN`精确引用和既有`skilllist|8`规则，补齐句面攻击、受伤量（正文防御）及移动速度数值。上游严格候选上限为61卡66行94答案（攻击65、受伤量25、移动4）；实施复核进一步剔除5行条件／对象句后，冻结候选为61卡61行89答案（攻击61、受伤量24、移动4），以最终独立审查和正式实测为准。

选择理由：每个候选均有「supporterskill句面属性→abiN→唯一skilllist记录→现有type8字段」链，无需新公式、新原生或跨类型猜测。非Y.G.连带范围为0，不为了扩量扫描普通卡。

## 输入与候选范围

- 候选筛选：`work/c13_20261031/supporterskill_type8_strict.json`。
- 原始supporterskill：CACHE `output/cache_full_20261015_v3/decoded/supporterskill.data5.json.raw`。
- abi记录：逐ID CACHE优先，CACHE缺ID才回退APK `output/base_master/_mdSkill.json`；不得把CACHE/APK同号记录合并。
- 既有规则：`output/character_skills/profiles/rules.json`的`skilllist|8|/param1..3`，rules 294键不改。
- 排除：20234、30102、30236、30239；其他属性中性1.0；ABI原文不支持该属性；同一效果重复主张；多非中性来源；缺失、null、非有限值。30302重复攻击主张已排除，不得重新纳入。

## 实施要求

1. 新模块限 `scripts/character_skills/card_page_inference_c13_p1_supporterskill_type8.py`；候选输出限 `output/character_skills/c13_p1_supporterskill_type8_20261031/`，自身work限 `work/c13_20261031/p1/`。
2. 逐行重新验证候选，不信任筛选脚本结论。supporterskill记录必须满足`ability_id==cid`、页面source pointer身份一致；abiN只能按原记录引用解引用。
3. 只允许ability8：param1攻击、param2移动、param3受伤量。ABI原文必须明确支持对应属性；不得把同记录其他中性字段或非对应属性一并出答。
4. 每个目标效果恰一个未解backlog项、恰一个非中性ABI来源；一效果一答案。已有答案保留，不重复回答既有skilllist|29等特殊威力，不处理type18、type9或其他类型。
5. 使用既有规则换算，不新注册规则、不改rules.py/rules.json。数值证据与关联证据分开：type8规则体可保持已确认，supporterskill→abi装载／生效关联保持推断；不写玩家解锁、最终面板或最终伤害。
6. 答案记录rule_key、raw_value、record_id、layer、原始JSON pointer、abi字段、对象、条件、证据档和限制。保留float32原值；缺失／null／零／一中性分别处理。
7. 自检覆盖正例、相邻变体、反例和保护卡；对账候选行数、答案数、效果归属、旧答案零改及非Y.G.零连带。输出README、候选JSON、检查脚本和结果，不运行正式全库生成。

## 独立审查

审查者从原始supporterskill、abi记录和rules独立重算，不采信实施自检。重点抽查全量来源身份、属性错配、中性误答、重复效果、CACHE/APK分源、对象／条件／证据档与中文可读性；写 `output/character_skills/review/c13_p1_supporterskill_type8_20261031_deepseek/REPORT.md`。默认初审一次，集中修复后定向复核最多一次。

## 允许／禁止

只写上述模块、候选输出、自身work和指定审查目录。不得修改共享`card_page_data.py`、`effect_ledger.py`、正式pages／ledger／rules、其他任务文件；不得正式全库生成、清理、Git、发布、新原生、实机、新缓存或C14。
