# 任务记录：P2 第 6 批（条件语义三件套：96 攻击择槽／筛选位字典／1059 UnionCount）

- 任务标识：`20261018-character-skills-p6`
- 负责人／对话：本线实施对话（角色技能完整解读 P2 系列，2026-10-18 第 6 批）
- 状态：**待针对性审查**（已实施、验证全绿、全链字节可复现）
- 允许写入范围：`scripts/character_skills/`、`output/character_skills/`（本批产物与 README／交接）、
  `work/p6_*`（本批快照、一次性探针与核对脚本）、本文件
- 共享依赖（只读）：`work/protection/il2cpp_loader_seed1.bin`、`work/protection/metadata_aei_decoded.bin`、
  `output/cache_full_20261015_v3/decoded/{skilllist,homelist}.data5.json.raw`、`output/base_master/_mdSkill.json`、
  `work/p5_records_before.jsonl`（P4 终态快照，只读）、`work/p6_records_before.jsonl`（本批新建的 P5 终态快照）
- 未触碰：`review/` 历史报告、`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、
  `docs/tasks/character-skills-progress.md`（主持）、其他任务未提交文件；未提交、未推送、未发布

## 目标（逐项）

1. **type 96 攻击路径 `[sp+0x18]` 标志语义**：定位标志的业务含义（谁置 1、何时走扩展缩放路径），
   定位后 `param2`／`param3` 择一给规则；无法定位则保持缺证并写明缺哪段。
2. **筛选位字典**：为 `iParam0`（职业位图）、`flag`（武器位图）、`param8`（出身筛选值）建位/取值字典；
   建成后把 67／80 的条件升级为逐值可读，并给 67 的 `param8`（出身）可读条件。
3. **type 1059 UnionCount**（432 角色）：沿 `PartyAbilityInit`／`subPartyAbilityInit` 或 `GetAllCharaList`
   系追踪真实施加路径；能闭环则给规则，不能则如实缺证写明断点。

## 关键做法

- **96 择槽**：读 `BattleParam.GetAbilityAttack` 序言 —— `w23 = w4 = damageType`（元数据签名第 4 参数，
  `eDamageType`），`cmp w23,#1`（Skill=1）走扩展缩放路径并 `str w8(=1),[sp,#0x18]`，否则
  `str wzr,[sp,#0x18]`；分支体 `0x1107c48` `ldr w8,[sp,#0x18]; cbz → get_param2 / 否则 get_param3`。
  两个调用方（`callers_of` 全图扫描）核实为 `CharaBehavior.Attack`（透传当次伤害类型）与
  `BattleParam.UpdateParam`（`mov w4, wzr`）。
- **筛选位字典**：职业名取元数据枚举 `JOB_TYPE`（type 714），武器位取游戏自身
  `Constants.WeaponKind2AttackFlag` 的跳转表（0x2074180，WeaponKind→bit22..30），出身名取游戏主表
  `homelist`；位形状由原生读取点（`CalcCharaNum`／`IsEnableAbility` case 1059／`IsTargetHome`）确认；
  再用「正文只出现一个该维度词、位图只有一位」的区分性样本做对照（职业 273／武器 54／出身 73，全一致）。
- **1059**：穷举全图对 `0x423` 的比较点（只有 4 处）→ 发现 `IsEnableAbility` 的 case 1059 与
  `Constants.AbilityTypeCachedFlagIndex..cctor` 的 rank 表；据 rank 反查消费点 → 五个
  `PlayerManager.GetAbility*` 按 `ldrh w1,[静态表+2*rank]` 取 flag index 后用
  `GetAbilityOnFlagIndex_ParamN` 读参数；`setupAbility` 跳转表 case 1059（0x10f5830）创建
  `cAbilityUnionCountWork` 入 `_abilityUnionCountWorkList@0x728`，`update_ability` 遍历该表做
  `CharaBehavior.Heal(int(param6×成员最大HP))`。
- **规则由重算产出**：`union_count_rule_rows()` 只在 `union_count_evidence()` 的四个段（门控／装载／
  施加／玩家侧消费）全部重算通过后才出行；96 的攻击槽沿用 P5 的「分支重算才出行」约束。

## 产物

| 产物 | 位置 |
|---|---|
| 筛选位字典（职业／武器／出身＋正文对照＋原生依据） | `output/character_skills/skilllist_types/filter_dictionary.json` |
| 1059 换算链逐段证据（门控／装载／施加／玩家侧消费／rank） | `output/character_skills/skilllist_types/union_count_chains.json` |
| 规则字典（沿用本批新增 **21** 条：96×3、67×3、80×1、1059×14） | `output/character_skills/skilllist_types/field_dictionary.json` |
| 原生自检 53/53（本批新增 12 项） | `output/character_skills/skilllist_types/native_checks.json` |
| 覆盖增量（三口径＋可达角色＋零破坏） | `output/character_skills/skilllist_types/p6_increment.json` |
| 交叉核对新增 L 区（直读原始表重解码筛选位） | `output/character_skills/validation/crosscheck_raw.json` |
| P5 终态快照（供增量与零破坏对账） | `work/p6_records_before.jsonl`、`work/p6_summary_before.json` |
| 一次性探针与核对脚本 | `work/p6_native/`（explore／enums／filters／evidence_single／diff_before_after／hashes 等） |
| 交接 | `output/character_skills/P6_HANDOFF.md` |

## 关键数字（本批增量，三口径）

- 新增答案 **9112**（页求和）／**7959**（（表,记录,层,字段）去重）／**9112**（记录级）。
  按 type 页求和：67→**2797**、80→**298**、96→**207**、1059→**5810**。
- 未解释字段 426902 → **417790**；规则答案 47841 → **56953**（唯一记录 47008 → **56120**）。
- 可达角色（本批规则命中）：67→**513**、80→**166**、96→**52**、1059→**432**（去重 **919**）。
- 状态迁移：**1 个角色**由「仅未知」变为「部分」（部分 1861→1862、仅未知 375→374）。
- 缺口队列字段级 5736 → **5715**、类型级 377（不变）、有线索 301 → **296**、断链 0。
- **零破坏**：相对 P5 终态快照，既有答案键 **0 丢失**、raw／kind／unit／status／scope **0 变化**；
  1414 条（67 `/param0` 1116 ＋ 80 `/param0` 298）只改文本（条件升级为逐值可读），
  文本首个数值 **0 变化**。

## 验证

`verify_p1.py` **131/131**、`skilllist_types.py` 自检 **53/53**、`crosscheck_raw.py` **A–L overall_ok**
（K 8754 条／L 4602 条，0 失配）、双路核对 5×3001 type 0 差异；默认 GBK（`PYTHONUTF8=0`）下六个入口
exit 0 且 stderr 0 字节；重跑全链（skilllist_types→profiles→gaps→report→verify→crosscheck）后
16 份关键产物 SHA-256 逐字节相同（`work/p6_native/hashes_after.json` 与 compare 结果）。

## 下一步（留给后续批次）

1. `AbilityTypeCachedFlagIndex` 静态 rank 与 flag index 的完整对照表（本批只用 rank=121 反查消费点）；
2. `charaParameter.get_home` 在记录缺 home 时的返回值（决定「0 组是否命中缺省角色」）；
3. `cAbility*Work..ctor` 的字段归属（type8 param4 可达性）；charainfo 3/22/110 的全局技能表；
4. denju（1500 角色）、bosspattern（1307）整类无规则。
