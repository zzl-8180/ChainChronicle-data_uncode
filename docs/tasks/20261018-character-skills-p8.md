# 任务记录：P2 第 8 批（攻击系 boss 技能类型族 ＋ p2b7 审查 4 条文档修正）

- 任务标识：`20261018-character-skills-p8`
- 负责人／对话：本线实施对话（角色技能完整解读 P2 系列，2026-10-18 第 8 批）
- 状态：**待针对性审查**（已实施、验证全绿、全链字节可复现）
- 允许写入范围：`scripts/character_skills/`、`output/character_skills/`（本批产物与 README／交接）、
  `work/p8_*` 与 `work/p8_attacks/`（本批快照、一次性探针）、`docs/tasks/20261018-character-skills-p8.md`（本文件）
- 共享依赖（只读）：`work/protection/il2cpp_loader_seed1.bin`、`work/protection/metadata_aei_decoded.bin`、
  `output/cache_full_20261015_v3/decoded/{bossinfo,charainfo,denju,denju_lblist}.data5.json.raw`、
  `output/base_master/{_mdBossInfo,_mdCharacter}.json`、`work/p8_records_before.jsonl`（P7 终态快照）
- 未触碰：`review/` 历史报告、`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、
  `docs/tasks/character-skills-progress.md`（主持）、其他任务未提交文件；未提交、未推送、未发布

## 目标（逐项）

1. **第 0 项（先修）**：p2b7 审查 4 条文档修正——P7_HANDOFF §5.2 缺证声明过度保守且有内部矛盾、
   §4 样本 `40025301` 的 type 笔误（112→13）、§1① 键集枚举漏 `weaponChange`、
   §5.6「148 行两者不同值」补口径注记。只改文字。
2. **伤害基数定位**：沿 `Exec_ATTACK_AREA`（type3）／`Exec_ATTACK_FRONT`（type22）／
   `Exec_ATTACK_AREA_REPEAT`（type110）等 handler 的实际读取，找到伤害基值来源并给逐段 RVA。
3. **按角色覆盖优先级给规则**：type 5/0/2/3/11/22/23/33/47/110 中能闭环的几个给几个，
   至少覆盖最高的 3 个类型；不能闭环的如实写明断点。
4. **应用**：规则经等价门控应用到 `charainfo` 必杀技参数（E 类）与 `bossskill` 记录（含 denju 链），
   重建 profiles／gaps，报告覆盖增量与脱贫对账。
5. **验证**：`verify_p1.py` 全绿并加本批新检查；`crosscheck_raw.py` 扩展；全链 SHA-256 可复现；
   默认 GBK 全部入口 exit 0；既有答案零破坏。

## 关键做法与结论

- **伤害基值就是共享的技能基值函数**：`伤害输入 = floor/clamp(float32(B × skillparamN))`，
  `B = bhSkillUtil.getBasicSkillAttack(true)`（0x1182ed8，入参 w1=1），整数化 0x14374bc
  （`frintm`/`fcvtms` **向下取整**后夹到 int32；+inf → int32 最小值）。与 type105／type112 既有证据同源。
- **P2-1 的「全局技能表」候选被否**：`[[0x29e9000+0x6e8]]+0xb8` 的三浮点被 `skillparam4` 缩放后加到
  施法者位置上，作为 `BattleManager.FindNearPosition` 的搜索中心——是攻击起点偏移表，不是伤害表。
- **推力的两种落点**：多数类型作为 `CharaBehavior.Attack` 的 `pushPower` 形参；子弹类型（5／47）
  经 `Bullet._pushPower`／`SpreadBullet._pushPower`（字段偏移 0x60，元数据字段名为锚）。type1 的
  pushPower 实参是硬编码 `fmov s2, wzr`（0），**没有推力槽**。
- **共享体串槽的防护**：type0 与 type1 共用 `AttackNear_Common → AttackList_Common`，回溯时只允许
  从该 type 的 handler 可达的调用点（`NativeView.reachable_from`），避免把 type0 的 `sp3` 当成 type1 的推力。
- **type47 的伤害倍率是 `skillparam0`**（不是同族的 `sp1`；`sp1` 是 `m_BombType`）。
- **受控执行**：Unicorn 跑真实字节执行整数化函数（含 `-0.5→-1`、`+inf→int32 最小值`），并对每个 type
  的 `fmul` 指令复算一次；85/85 检查全过。
- **应用与增量**：新增 35 条规则；答案 +14132（页求和）／+10000（唯一键）；未解释 449862 → 435730；
  39 个角色由「仅未知」变「部分」（其中 21 人经 charainfo 等价门控，其余经自身 pattern 的
  boss 技能／传授链）；零破坏（0 丢失、0 变化）。
- **脱贫上限的诚实说明**：其余 334 个未知角色的主因是 `NOT_AMONG_OWN_PATTERN_TYPES`
  （无可对齐 boss 记录）与 X1，门控不通过；本批不放宽门控，另记录一条待验证候选路径
  （`bhSkill.CreateExecSkillList` 直接消费 `charaParameter.skillparamN`）。

## 产物

| 产物 | 位置 |
|---|---|
| 逐 type 证据（伤害函数链、逐槽 RVA、未定论槽、取值分布、参考候选冲突） | `output/character_skills/boss_attack_types/type_rules.json` |
| 受控检查 85/85（含 Unicorn 执行整数化、逐 type `fmul` 复算、metadata 锚点、0.001 哨兵） | `output/character_skills/boss_attack_types/native_checks.json` |
| 新增 35 条规则（第四规则来源，只补缺键） | `output/character_skills/boss_attack_types/field_dictionary.json` |
| 三口径增量＋零破坏＋脱贫三路线 | `output/character_skills/boss_attack_types/p8_increment.json` |
| 直读原始表的 N 区交叉核对 | `output/character_skills/validation/crosscheck_raw.json` |
| P7 终态快照（增量与零破坏基准） | `work/p8_records_before.jsonl`、`work/p8_summary_before.json` |
| 一次性探针与 GBK／可复现核对 | `work/p8_attacks/{gbk_run.py,hashes_*.json,explore.py,sigs.py,slotdist.py,unknown_dist.py,migrated.py}` |
| 针对性审查交接 | `output/character_skills/P8_HANDOFF.md` |

## 关键数字（本批增量）

- 新增答案 **14132**（页求和）／**10000**（唯一键；`records.jsonl` 行实例 **14124**）；
  按类型页和 110→4821、3→4297、22→2853、105→936、2→312、5→249、47→177、4→174、1→171、0→142；
  分组口径 special_move 11191＋denju 2811＋denju_lb 130。
- 规则答案 60189 → **74321**；唯一记录级 59356 → **73480**；未解释参数槽 449862 → **435730**。
- 可达角色 **846**；状态迁移：**39 个角色**由「仅未知」变「部分」（部分 1863→1902、仅未知 373→334）。
- 经等价门控的 charainfo 答案 522 → **3131**（页求和＝唯一记录）。
- 缺口队列字段级 5715 → **5680**、类型级 377（不变）、有线索 296 → 287；断链 3（不变）。
- **零破坏**：既有答案键 **0 丢失**、raw／kind／unit／status／scope **0 变化**、value 文本 **0 变化**。

## 验证

`boss_attack_types.py` 自检 **85/85**；`verify_p1.py` **163/163**（P7 为 149，本批 +14）；
`crosscheck_raw.py` **A–N overall_ok**（N 区 14124 条新规则答案从原始表重算，0 失配、0 遗漏）；
`denju_skills.py` 17/17、`charainfo_types.py` 37/37、`skilllist_types.py` 53/53；
默认 GBK（`PYTHONUTF8=0`）下 **14 个入口 exit 0 且 stderr 0 字节**；全链重跑 **67 份产物 SHA-256 逐字节相同**；
HTML 夹具（p1／p2）全过；相对 P7 终态快照既有答案 0 丢失 0 变化。

## 下一步（留给后续批次）

1. 334 个仍未知角色的候选路径：`bhSkill.CreateExecSkillList`／`CreateSkillList_SkillID` 直接消费
   `charaParameter._skillid[0]`／`_skillparamN`（需先确认该路径是战斗路径而非卡面/预览路径）。
2. type33（`Exec_FALL_AREA` → `AirAreaStrike` work 对象）与 type23（`Exec_LOCKED_SUPPORT`）的伤害/参数；
   type110／105 的 `sp7`、type1 的 `sp4`、type47 的 `sp6` 语义。
3. 攻击起点偏移表（`[[0x29e9000+0x6e8]]+0xb8`）与 `_type==0` 两个偏移分支的业务名。
4. `AbilityTypeCachedFlagIndex` 的 rank↔type 对照表、`charaParameter.get_home` 缺省返回（P6／P7 遗留）；
   bosspattern（1307）、extra_ability_info（494）。
