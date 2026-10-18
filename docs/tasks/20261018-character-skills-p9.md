# 任务记录：P2 第 9 批（必杀技执行侧裁决：X1／NOT_AMONG／F0 ＋ p2b8 审查 3 处文字修正）

- 任务标识：`20261018-character-skills-p9`
- 负责人／对话：本线实施对话（角色技能完整解读 P2 系列，2026-10-18 第 9 批）
- 状态：**已过针对性审查（p2b9 结论「需修正」，阻塞项 F1）→ 整改已完成、待复验**（验证全绿、两轮全链重跑字节无漂移；整改记录见本文件末节）
- 允许写入范围：`scripts/character_skills/`、`output/character_skills/`（本批产物与 README／交接）、
  `work/p9_*`、`work/p9_paths/`（本批快照与一次性探针）、`docs/tasks/20261018-character-skills-p9.md`（本文件）；
  `HANDOFF.md`／`STATUS.md` 本线数字段落
- 共享依赖（只读）：`work/protection/il2cpp_loader_seed1.bin`、`work/protection/metadata_aei_decoded.bin`、
  `output/cache_full_20261015_v3/decoded/{charainfo,bossinfo}.data5.json.raw`、`output/base_master/{_mdBossInfo,_mdCharacter}.json`、
  `work/p9_records_before.jsonl`／`work/p9_summary_before.json`（P8 终态快照，本批增量与零破坏基准）
- 未触碰：`review/` 历史报告、`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、
  `docs/tasks/character-skills-progress.md`（主持）、其他任务未提交文件；未提交、未推送、未发布

## 目标（逐项）

1. **第 0 项（先修）**：p2b8 审查 3 处文字问题——type5 推力字典「原样传入」与自身 chainRate 注记矛盾且未提
   `Bullet` 中转；`P2R_HANDOFF.md` 两处「伤害基数取全局技能表」旧写法加指向注记；type110 sp6「范围外也消耗预算」
   在 type110 无对应指令结构。只改文字，不动数据与规则。
2. **执行侧路径研究**：`CharaParamToBossSkill` 另一重载（0x13aa390，`BattleParam` 源）的调用方
   （`CreateExecSkillList`×2／`CreateSkillList_SkillID`／`SkillAbility_EnchantUnionSkill`）与
   `BattleParam.skillparam` 的装入来源；判定这条路径是不是战斗执行路径、对它的是哪一侧数值。
3. **X1 裁决**（104 角色）：执行用 `BattleParam` 侧还是 `charaParameter` 侧，或按场景区分。
4. **NOT_AMONG 裁决**：无可对齐 boss 记录的角色能否按 `skillid[0]` 直接构建出答案；20 个例外角色逐个定性。
5. **应用与对账**：经裁决的路径出答案时**仍过门控**（逐角色标注依据路径），重建 profiles／gaps／增量；
   报告覆盖增量（双/三口径、脱贫数及逐人路径、未脱贫原因）。
6. **验证**：`verify_p1.py` 全绿并加本批新检查；`crosscheck_raw.py` 扩展；全链关键产物 SHA-256 可复现；
   默认 GBK 全部入口 exit 0；既有答案零破坏（快照对账）。

## 关键做法与结论

- **两个 `CharaParamToBossSkill` 重载的语义（本批定死）**：`0x13aa764` 读 `charaParameter`（角色记录，
  调用方 `CharaInfoCharaModel.PlaySpMotion`／`BtlCharaUtil.GetDenjuSkill`）；**`0x13aa390` 读 `BattleParam`**
  （`[chara+0x28]` = `CharaBehavior._param`），`skillid0 ← _atvSkillID`、`skillparam0..9 ← _skillparamN`、
  `skillflag/skillflag1/iparam/str/s_ability ← BattleParam`。
- **`BattleParam` 的来源＝角色记录，不是 boss 主表**：`BattleParam.CreateByID(0x10fcee4)` 把
  `charaParameter.skillid[0] → _atvSkillID(0x930)`、`charaParameter.skillparamN → _skillparamN(0x940..)`、
  `charaParameter.patternN → _patternN(0x9b8..)`（十个槽与九个 pattern 槽逐条核对）。**用户提示中
  「BattleParam 侧＝boss 主表同值侧」不成立**。
- **两条执行路径**（`cp_paths/path_evidence.json`，12 步逐指令；`native_checks.json` 18/18）：
  ① 自身 pattern 可解析：`OnClickSpSkill(0x13a1dc8)`／`CheckEntry(0x1295360)` →
  `CreateExecSkillList(0x1295878/0x1296718)` → `FindPatternCtrl(0x12969b8)` 命中 →
  `_CreateExecSkillList(0x1296364)` 的 pattern 分支 → `pattern.getListBattleBossSkill()`
  （`makeListBattleBossSkill(0x1a6d4f4)` → `daBattleBossParameter.getBosSkill`）→ `Mission_execSkillPattern(0x10c0d40)`；
  ② 自身 pattern 无可达技能（F0）：`_CreateExecSkillList` 的 `pattern==0` 分支 → 构造的 `BattleBossSkill`
  进执行列表 + `Mission_execSkill(0x10c0abc)` → `CheckEntry` 取列表第 0 项 → `SetExecSkill(0x1295e70)` →
  `bhSkillUtil.initialize_ExAttack(0x11819d0)`（**读 `BattleBossSkill.get_skillparamN` 写入 util**）→
  `Execute(0x1297a98)` → `ExecSkill(0x1297ccc)`，派发键 `w2 = BattleBossSkill.get_skillid0()`。
- **第 5 个调用方不是第二条执行路径**：`SkillAbility_EnchantUnionSkill(0x11a5e64)` 调 `0x13aa390` 后把结果
  只写进 `[sp,#0x10]`，函数体内此后无读取（`chain_step_12_dropped_result` 检查）。
- **裁决**：X0／X1／NOT_AMONG ⇒ **执行取 pattern（boss 主表）侧**，charainfo 副本不是执行值
  （不给 charainfo 侧数值答案，两侧原值都保留，差异槽逐人列出）；**F0（929）⇒ 记录原值就是执行值，给答案**
  （这 929 人九个 `pattern` 槽全为 0，`makeExAttackPatternList` 对 0 直接跳过 → 执行用 pattern 列表为空）。
- **数据侧印证**（客观、可复算）：F0 角色的必杀技正文回数 51/51 与 `trunc(sp6)`（type105/110）或
  `trunc(sp3)+1`（type1）一致；X1 中可判别的样本 cid 2315／6058／8139 的正文回数只与 boss 侧一致
  （`x1_text_samples.json`；无「只与 charainfo 侧一致」的样本）。
- **顺带修正（只改文案）**：type1 `sp3` = 「追加回数；总攻击次数＝该值+1」（首次攻击在 `_numCounter==0`
  发出，循环在 `_numCounter > trunc(sp3)` 结束）——数值与 kind 不变，仅文案与 limits。
- **门控变化**：`equivalence.classify` 新增 `F0_NO_PATTERN_FALLBACK`（applicable，槽位 0..9＋四个 flag 由构造携带）；
  `NOT_AMONG_OWN_PATTERN_TYPES` 由 949 收窄为 20（只保留「pattern 存在但类型集合不含 `skillid[0]`」）。
- **结果**：新增 **1727** 条答案（页求和＝唯一键＝`records.jsonl` 行实例，全部 charainfo），落在 **535** 角色上；
  **187 角色脱贫**（部分 1902→2089、仅未知 334→**147**）；未解释 435730→**434003**；零破坏（0 丢失、0 变化、0 文本变化）。

## 产物

| 产物 | 位置 |
|---|---|
| 执行侧逐指令证据（12 步＋其它调用方） | `output/character_skills/cp_paths/path_evidence.json` |
| 受控检查 18/18（每步指令重读、字段锚点、X1 样本、F0 pattern 槽全 0） | `output/character_skills/cp_paths/native_checks.json` |
| F0 角色逐人（929 行：类型、pattern 槽、是否有规则、答案数） | `output/character_skills/cp_paths/fallback_characters.jsonl` |
| NOT_AMONG 20 人逐个定性 | `output/character_skills/cp_paths/notamong_exceptions.jsonl` |
| X1 区分性样本与口径 | `output/character_skills/cp_paths/x1_text_samples.json` |
| 逐类裁决 | `output/character_skills/cp_paths/verdicts.json` |
| 覆盖增量（双口径、脱贫 187 人、未脱贫 147 人原因、零破坏） | `output/character_skills/cp_paths/p9_increment.json` |
| 门控与答案（重建） | `output/character_skills/charainfo_params/`、`profiles/`、`gaps/` |
| P8 快速通道（本批文案修正／计数印证 86/86） | `output/character_skills/boss_attack_types/` |
| P8 终态快照（增量/零破坏基准） | `work/p9_records_before.jsonl`、`work/p9_summary_before.json` |
| 一次性探针（GBK／可复现／分类形状／文本印证） | `work/p9_paths/{gbk_run.py,zerobreak.py,classify_shape.py,text_corroboration.py,x1_text.py,x1_diffs.py,probe.py}` |
| 针对性审查交接 | `output/character_skills/P9_HANDOFF.md` |

## 关键数字（本批增量）

- 新增答案 **1727**（页求和 ＝ 唯一键 ＝ `records.jsonl` 行实例），新增字符 **535**（全部 charainfo 参数）。
- 脱贫 **187**（部分 1902→**2089**、仅未知 334→**147**）；规则答案 74321 → **76048**；唯一记录 73480 → **75207**；
  未解释参数槽 435730 → **434003**；缺口字段级 5680 → **5679**；charainfo 答案 3131 → **4858**。
- 按类型页和：3→311、5→270、22→268、2→198、0→168、1→126、13→120、47→96、27→64、4→46、110→30、105→16、16→14。
- 按字段：`/skillparam1` 535、`/skillparam3` 517、`/skillparam2` 320、`/skillparam4` 259、`/skillparam6` 39、
  `/skillparam5` 25、`/skillflag0_1` 16、`/skillparam0` 16。
- 剩余 147 人按（类,类型）无歧义拆分（`p9_increment.json` 的 `remaining_unknown_by_class_and_type`）：
  **F0 134／E0 9／X1 3／NOT_AMONG 1**。F0 桶按 handler 分（E0／X1 不并入类型桶）：
  `bhSkill.Exec_HEAL`（type 10／11／12／14／26／28／31／32）**53**、
  `Exec_FALL_AREA`(33) 10＋`Exec_FALL_AREA2`(103) 1＝**11**、type23（`Exec_LOCKED_SUPPORT`）14、
  type6（`Exec_SHOOT_BACK`）11、type7（`Exec_SHOOT_RANDOM`）11、其余零散 handler；
  E0 9（type 31×2／103×2／64／44／73／46／33）、X1 3（type 80／33／43）、NOT_AMONG 1（`skillid[0]`=76，pattern 类型 82／88 无规则）。
- **零破坏**：既有答案键 **0 丢失**、raw／kind／unit／status／scope **0 变化**；value 文本按 p2b9 整改项**有意变更**
  （901 条既有实例全部只改 value；整改对账见本文件末节）。

## 验证

`cp_paths.py` 自检 **18/18**；`boss_attack_types.py` 自检 **86/86**（+1 计数文案数据侧印证）；
`verify_p1.py` **174/174**（+6 本批检查、+5 p2b9 整改检查）；`crosscheck_raw.py` **A–O overall_ok**
（F 区新增 F0 分类重推、G2 新增 F0 前提核对、N 区 1521 条 F0 答案不再要求 boss 同值改为核对本记录原值、
**O 区新增答案措辞与 F0 注记的逐条钉死**）；
`charainfo_types.py` 37/37、`denju_skills.py` 17/17、`skilllist_types.py` 53/53；
默认 GBK（`PYTHONUTF8=0`）**17 个入口调用 exit 0 且 stderr 0 字节**；**两轮全链重跑 76 份产物字节无漂移**；
相对 P8 终态快照既有答案 0 丢失 0 变化（`work/p9_paths/zerobreak.py`）。

## 下一步（留给后续批次）

1. **heal 族类型规则**（`Exec_HEAL` 的 type 10／11／12／14／26／28／31／32／46 与 `Exec_HEAL_UNION` 75；15／16 已有规则）：剩余 147 人里最大一块
   （单 type 11 就挡 23 人）。
2. type23（`Exec_LOCKED_SUPPORT`）／type6（`Exec_SHOOT_BACK`）／type7（`Exec_SHOOT_RANDOM`）／
   type33（`Exec_FALL_AREA` 的 work 结算，第 8 批遗留）。
3. 运行时判定「该次必杀由传授链（denju）／英雄技 pattern 承担」的优先级（本批只在答案注记里声明条件）。
4. `AbilityTypeCachedFlagIndex` 的 rank↔type 表；`charaParameter.get_home` 缺省。
5. `BattleParam` 的运行时改写（`updateMutate_sub_backupBattleParam`／`_copyBattleParam`，变身场景）对
   `_skillparamN` 的影响；bosspattern（1307）与 extra_ability_info（494）。

## p2b9 审查整改记录（2026-10-18，只改文本／渲染，不动数值）

审查报告 `output/character_skills/review/p2b9_20261018_thirdparty/REPORT.md`（结论「需修正」，阻塞项 F1）。
每项先复算确认再落盘，写入范围仅 `scripts/character_skills/`、`output/character_skills/`、`work/p9_paths/`
与本文件；未提交、未推送、未发布。

| 项 | 落点 | 证据（复算） | 对账 |
|---|---|---|---|
| **F1** type1 `sp3` 答案仍渲染「每目标尝试上限 N 次」，与本批自证的总次数＝N+1 矛盾 | `rules.py`：新增 `BOSS_ATTACK_TEMPLATE_BY_TYPE`，`_boss_attack` 按 `(effect_type, kind)` 取模板，`convert` 传入 `effect_type`；`(1,count_cap)` 模板＝「追加回数 trunc(v) = n：… → 总攻击次数 = n + 1」 | 复算指令级循环 `Exec_ATTACK_REPEAT(0x11848b0)`：`cmp w8,w21; b.gt`（`_numCounter > trunc(sp3)` 退出）、自增 `str w10,[x19,#0xc8]` 在攻击之后；数据侧 51/51 F0 正文回数＝`trunc(sp3)+1`（`boss_attack_types` 自检第 86 项） | 99 条实例（85 记录）文本更新，`kind`／`unit`／`status` **未变**；cid 25 → 「总攻击次数 = 4 + 1」＝正文 5 回；cid 6058 的 boss 子记录（60580／60582，sp3=6.0）→「6 + 1」＝正文 7 回 |
| **F2** type110 `sp6` 820 条仍含「范围外也消耗预算」 | 同表 `(110,count_cap)` 模板＝「每目标上限 trunc(v) = n 次（…计时到期即消耗一次预算并攻击，目标在清单建立后不再做范围重判…）」 | 复算确认 type110 攻击前无 `get_bodyRadius/get_statusBodyRadius` 调用（type105 有）；与 p2b8 定论、字典 `conversion`／`limits` 同一措辞 | 820 条文本更新；`kind`／`unit`／`status` 未变 |
| **F3** type47 `sp4` 45 条缺 `SpreadBullet` 中转注记 | `boss_attack_types.py` `SPEC[47]["push"]["note"]` → `slots.push_pow.note` → 规则行 `role_note` → 答案文本追加 | 字段锚点 `SpreadBullet._pushPower`=0x60（`push_power_field_is_0x60_on_Bullet_and_SpreadBullet`）；与 type5 同型 | 45/45 条点名 `SpreadBullet`（整改前 0/45） |
| **F4** 16 条 F0 `/skillflag0_1` 缺人读注记 | `profiles.py` 注记条件 `== EQ.NO_PATTERN_FALLBACK` → `startswith(...)`（flag 字段 gate 返回 `…+FIELD_CARRIED_BY_CONSTRUCTION`） | 机读 gate 本就标注该字段，缺的只是人读注记 | F0 答案注记覆盖 **1727/1727**（整改前 1711/1727）；16 条只增 `note` |
| **F5** 交接散文 147 归因数字（heal 56／FALL_AREA 15 与机读不符） | `P9_HANDOFF.md` §5／§6、`README.md` §3.9、`HANDOFF.md`、`STATUS.md`、本文件；`cp_paths.py` 新增机器字段 `remaining_unknown_by_class_and_type`＋`remaining_unknown_grouping_note` | `p9_increment.json`（权威）：F0 134／E0 9／X1 3／NOT_AMONG 1；F0 桶 heal 族 **53**、`FALL_AREA`＋`FALL_AREA2` **11**（33→10、103→1） | 散文数字与机读逐格一致；cid 25 样本行改为引用整改后的**实际渲染文本** |
| 钉死检查 | `crosscheck_raw.py` 新增 **O 区**（逐条读 value：type1 sp3 必写总次数且无「尝试上限」、type110 sp6 无「范围外也消耗预算」、type47 sp4 点名 SpreadBullet、1727 条 F0 答案带人读注记）；`verify_p1.py` 新增 5 项 `p9r.*`（含 kind/unit/status 不变断言） | O 区自读计数：type1_sp3 99／type110_sp6 820／type47_sp4 45／f0_answers 1727、缺注记 0 | `crosscheck_raw.py overall_ok=true`；`verify_p1.py` **174/174** |

**逐条实例级对账**：`cp_paths/p9_increment.json` 的 `rectification_accounting`（基准＝`work/p9_rect_before_records.jsonl`）：
实例 75191 → 75191、**lost 0／new 0**、`value_text_changed` **964**（＝820＋99＋45；其中 **P8 既有 901／P9 新增 63**）、
`note_added_only` **16**、**`raw_kind_unit_status_or_other_changed` 0**；独立复算脚本
`work/p9_paths/rect_accounting.py`、逐槽措辞统计 `work/p9_paths/rect_samples.py`、新老拆分 `work/p9_paths/rect_split.py`。
**口径**：964 按角色页实例计；`existing_answer_keys_value_text_changed`＝640 按（表,记录,层,字段）去重计（差额来自共享
bossskill 记录被多页引用）。type105 `sp6` 的渲染保持不变（其语义确有范围重判，O 区不覆盖它）。

**整改后复跑**：`boss_attack_types.py` 86/86、`cp_paths.py` 18/18、`verify_p1.py` **174/174**、
`crosscheck_raw.py` **overall_ok**（A–O）、DOM p1 9/9＋p2 24/24、默认 GBK 入口 exit 0 且 stderr 0、
两轮全链重跑产物字节无漂移（探针见 `work/p9_paths/gbk_run.py`）。
