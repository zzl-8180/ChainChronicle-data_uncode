# 任务记录：P2 第 10 批（Exec_HEAL 家族与其余类型；里程碑 A 收官）

- 任务标识：`20261018-character-skills-p10`
- 负责人／对话：本线实施对话（角色技能完整解读 P2 系列，2026-10-18 第 10 批）
- 状态：**已实施 → p2b10 审查「需修正」（F1–F4）→ 整改完成、待复验**（`verify_p1.py` 189/189、
  `crosscheck_raw.py` A–P overall_ok、两轮全链重跑 82 份产物字节无漂移、默认 GBK 19 个入口 exit 0）
- 允许写入范围：`scripts/character_skills/`、`output/character_skills/`（本批产物与 README／交接）、
  `work/p10_*`、`work/p10_paths/`、`docs/tasks/20261018-character-skills-p10.md`（本文件）；
  `HANDOFF.md`／`STATUS.md` 本线数字段落
- 共享依赖（只读）：`work/protection/il2cpp_loader_seed1.bin`、`work/protection/metadata_aei_decoded.bin`、
  `output/cache_full_20261015_v3/decoded/{charainfo,bossinfo}.data5.json.raw`、
  `output/base_master/{_mdBossInfo,_mdCharacter}.json`、`output/boss_heal/field_dictionary.json`＋`constants.json`、
  `output/character_skills/charainfo_types/type_dispatch_index.json`、
  `work/p10_records_before.jsonl`／`work/p10_summary_before.json`（P9 终态快照，增量与零破坏基准）
- 未触碰：`review/` 历史报告、`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、
  `docs/tasks/character-skills-progress.md`（主持）、其他任务未提交文件；未提交、未推送、未发布

## 目标（逐项）

1. **heal 族（最优先，53 人）**：`bhSkill.Exec_HEAL` 的 type 10/11/12/14/26/28/31/32（＋46）——
   回复量基数、间隔／次数、对象、条件、超上限位是否适用。
2. **FALL_AREA 族（11 人）**：type 33/103 的落点／范围攻击 handler。
3. **type 23／6／7（36 人）**：沿类型索引与 handler 槽位解参数语义；type7 与 skilllist ability7 不混。
4. **E0 9／X1 3／NOT_AMONG 1 所缺类型（49/82/84/86/87/88 等）**：按证据顺度给规则或缺证。
5. **应用＋重建 profiles/gaps**：报告覆盖增量（双/三口径、脱贫数与逐人路径、仍未脱贫者的具体缺证）。

## 关键做法与结论

- **Exec_HEAL 家族＝一个 handler ＋ 两个模式实参**：`bhSkill.Exec_HEAL(0x1299C74)` 把 `w2`→对象选择、
  `w3`→动作选择、`w4`→类型 传进 `bhSkillUtil.Exec_HEAL(0x1187C80)` → `Exec_HEAL_common(0x1188194)`；
  两个跳转表（`0x206DE44` 4 项、`0x206DE48` 9 项）由游戏自身字节重算，得到动作表与对象表。
- **回复量**＝`floor/clamp(float32(B × skillparam1))`，`B = getBasicSkillAttack(true)`，整数化 `0x14374BC`，
  交 `CharaBehavior.Heal` 的 healValue；超上限（HP 上限）比率＝`max(HealSkill_HealFlag(标志), 附加槽)`，
  附加槽按类型为 sp2（10/11）、**sp5（28 与 46，同一装载点 0x11882AC）**、sp4（31/32）。
- **支援块**：`SupportData` 字段存储点定实参序（**不采用元数据 `parameters` 的顺序**——`SetSupport` 上
  两者不一致，这是本批最容易抄错的一处）；12/13/14/26 的攻击/防御/移动乘 `_skillChainRate`，
  28/31/32/46 不乘（本批用不同 answer_kind 区分并逐条钉死）。
- **FALL_AREA**：sp3＝落点 X 偏移（`_type==0` 取负＋夹到地面范围）、sp6（仅 33）＝选择码；
  **伤害在 `AirAreaStrike(0x118380C)` 建立的工作对象里结算**（对象 +0x40 持有 util），未追进其 update
  → 伤害槽明确不给数值。
- **type 23／36／43／87 手读**：23 给 sp1/sp2（支援 ×chain）＋sp7（暴伤载荷）；36 给 sp3（钢铁守护时间
  ×chain）＋sp2（自身那次的门控码）；43 给 sp3（总回数＝trunc+1）／sp2（击间隔）／sp1（首段倍率）／
  sp4（末段倍率）／sp5（末段推力）／sp6（末段后计时）；87 给 sp1..sp4（区域支援载荷实参 #1..#4）。
- **其余类型**：6/7/19/29/34/44/49/50/51/55/64/67/69/72/74/75/76/80/82/86/114 的「技能基值×槽→整数化」
  点由调用图可达性重算（受限可达集＋与手工核对表逐条比对）；其中 34/50/64/72/76/86 的消费点（伤害或
  回复）未定位 → 答案写「消费点未定」，不猜。
- **结果**：新增 **80** 条规则（36 个类型）；新增答案 **5452**（页求和）／**4050**（唯一键）；
  **仅未知 147 → 5**（脱贫 142）；未解释 434003 → **428551**；零破坏（0 丢失、0 变化、0 文本变化）。

## 产物

| 产物 | 位置 |
|---|---|
| 逐类型证据（模式表、槽位 RVA、缺证、原值分布） | `output/character_skills/boss_heal_types/type_rules.json` |
| 受控检查 219/219 | `output/character_skills/boss_heal_types/native_checks.json` |
| 新规则行（由 `rules.py` 作为第五来源合并） | `output/character_skills/boss_heal_types/field_dictionary.json` |
| 覆盖增量＋零破坏（页/记录/唯一三口径、脱贫路径、孤儿名单） | `output/character_skills/boss_heal_types/p10_increment.json` |
| 生成器 | `scripts/character_skills/boss_heal_types.py` |
| 答案渲染（新 kind 模板＋回复量/超上限文案） | `scripts/character_skills/rules.py` |
| 门控与答案（重建） | `output/character_skills/profiles/`、`gaps/`、`charainfo_params/`、`cp_paths/` |
| P9 终态快照（增量/零破坏基准） | `work/p10_records_before.jsonl`、`work/p10_summary_before.json` |
| 探索脚本（22 个探针） | `work/p10/probe_*.py`、`work/p10/disasm_table.py`（审查用逐类型读取表） |
| 复跑探针（GBK／可复现／零破坏） | `work/p10_paths/{gbk_run.py,zerobreak.py}` |
| 针对性审查交接 | `output/character_skills/P10_HANDOFF.md` |

## 关键数字（本批增量）

- 新增规则 **79**（36 类；46→7、43→6、12/14/28→5、26/31/32/87→4、7/23→3、10/11/33/36→2，其余 1）。
- 新增答案 **5452**（页求和）／**4050**（唯一键）；`new_answers_from_earlier_rule_sets_page_sum`＝0。
- 脱贫 **142**（部分 2089→**2231**、仅未知 147→**5**）；规则答案 76048 → **81500**；唯一记录 75207 → **80659**；
  未解释 434003 → **428551**；缺口字段级 5679 → **5571**；`rules.json` 199 → **279**（`unique_rules_used` 268）。
- 按类型页和：46→1052、12→910、43→473、55→326、23→267、114→253、103→250、51→190、11→177、26→162、
  74→159、7→144、33→136、76→118、31→100。
- 仍未脱贫 **5 人**：cid 4009（type24）、4049／8116（type56）、10018（type68）为 F0；cid 8151（type73）为 E0
  ——这 4 个类型本批没有解出可交付的槽位语义，**不是缺等价前提**。

## 验证

`boss_heal_types.py` 自检 **219/219**；`verify_p1.py` **189/189**（本批 +15 项 `p10.*`，并把 P8 的增量
恒等式改为结构式＋注释原因）；`crosscheck_raw.py` **A–P overall_ok**（新增 **P 区**：直读原始表核对新答案
raw、回复量/超上限文本、chainRate 分型渲染、type43 +1 口径、落点夹紧、新键不冲突、孤儿角色独立重算＝5）；
`charainfo_types.py` **37/37**（`handler_slots_agree_with_confirmed_rules` 增加「由逐字节钉死的读取点覆盖」
一路并说明扫描是下界）；老入口回归 `denju_skills.py` 17/17、`boss_attack_types.py` 86/86、
`skilllist_types.py` 53/53；默认 GBK 下 **19 个入口调用 exit 0、stderr 0 字节**；**两轮全链重跑
82 份产物字节无漂移**；零破坏独立复算 `work/p10_paths/zerobreak.py`（75191→80642 实例、lost 0、
`value_text_changed` 0、raw/kind/unit/status/scope 变化 0）；HTML 夹具 p1 **8/8**、p2 **25/25**。

## 下一步（留给后续批次）

1. 剩余 5 个孤儿类型：24（`Exec_LOCKED_CURSE`）、56（`Exec_TARGET_CURSE`）、68（`Exec_MANA_CYCLE`
   ＋`common_Exec_MANA_CYCLE`）、73（`Exec_MODE_LAUNCHER`）——都是"非伤害/支援"型，需要追 curses/mana
   gauge/mode launcher 各自的 work 对象。
2. `AirAreaStrike` 工作对象的 update（type 33/103 的伤害）与 `AirStrike` 协程（34/50/64/72/76/86 的消费点）。
3. 23 的 `0x118B0C8` helper 内三个浮点、87 的 sp5..sp9、43 的 sp7、84 的基值槽。
4. 片段↔字段代码级绑定（"完整"长期为 0 的主因）；bosspattern（1307）、extra_ability_info（494）。
5. `BattleParam` 的运行时改写（变身场景）对 `_skillparamN` 的影响。

## p2b10 审查整改记录（F1–F4；每项先自行复算再落盘）

审查报告 `output/character_skills/review/p2b10_20261018_thirdparty/REPORT.md`（结论「需修正」）。
写入范围仅 `scripts/character_skills/`、`output/character_skills/`、`work/p10/`、`work/p10_paths/`、
`docs/tasks/20261018-character-skills-p10.md`、`HANDOFF.md`／`STATUS.md` 本线段落；未提交、未推送、未发布。

| 项 | 落点 | 复算 | 对账 |
|---|---|---|---|
| **F1（会漏答案）** type46 的 sp5＝超上限附加档位（与 type28 同一装载点） | `boss_heal_types.py`：`HEAL_FAMILY[46]` 增 `over_heal_ratio`(sp5, pin `0x11882AC`)；`read_slots[46]` 补 5；新增 `OVER_HEAL_BRANCH`＋`over_heal_floor_slot()` 与 2 项自检 | `work/p10/probe_f1_type46.py` 自写字节译码：`0x118827C cmp w19,#0x2e` → `0x1188280 b 0x11882A4` → `0x11882A4 fmov s0,wzr`（不改 NZCV）→ `0x11882A8 b.ne` 不跳转 → `0x11882AC ldr s0,[x22,#0x40]`＝sp5；分支求值 10/11→sp2、28/46→sp5、31/32→sp4、其余→无 | 新增规则 `bossskill|46|/skillparam5`；**147 条实例**（97 条 holder：APK 120＋5、charainfo 21＋1；raw ∈ {0,15,20,25,30}），审查者「26 记录／36 页」是单层直接记录的下界；本批页答案 5305→**5452**、唯一 3953→**4050** |
| **F2** 「39 个类型」→ 36 | 交接／任务记录／README／HANDOFF／STATUS | `field_dictionary.json` 的 `effect_type` 去重 = 36 | 全文改「80 条规则（36 个类型）」 |
| **F3** DOM 夹具计数 | 同上 | 逐个数 `run()` 用例：p1 = 8、p2 = 25（原先把 `ALL DOM CHECKS PASSED` 汇总行也计了） | 文档改 p1 **8/8**、p2 **25/25** 并注明口径 |
| **F4** 答案句内重复 | `boss_heal_types.py` 去掉与模板重复的 `role_note`；`rules.py` 的 `BOSS_HEAL_LIMITS` 去掉重复句 | `work/p10/probe_f4.py` 按「；」切句：修前 3 条规则有重复子句；再按模板逐条排查，删/改 33/sp3、33/sp6、36/sp2、36/sp3、7/sp3、23/sp1/2/7、43/sp1/2/4/5/6、19/sp1、46/sp6/7/8、87/sp1..4 的注记 | 新增常驻检查 `p10.answers_have_no_repeated_clause`（覆盖 80 条规则，重复 0） |

**整改后复跑**：`boss_heal_types.py` **219/219**、`verify_p1.py` **189/189**（+3 项 p2b10 整改检查）、
`crosscheck_raw.py` A–P `overall_ok`（P 区 `type46_sp5`＝147、mismatch 0）、`charainfo_types.py` 37/37、
`denju_skills.py` 17/17、`boss_attack_types.py` 86/86；默认 GBK 19 个入口 exit 0 且 stderr 0；
两轮全链重跑 82 份产物字节无漂移；零破坏逐实例 lost 0／`value_text_changed` 0／
`raw_kind_unit_status_scope_changed` 0（75191→80642）；HTML 夹具 p1 8/8＋p2 25/25。
