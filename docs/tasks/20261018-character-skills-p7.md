# 任务记录：P2 第 7 批（denju 传授必杀技 ＋ p2b6 审查 5 条文字注记）

- 任务标识：`20261018-character-skills-p7`
- 负责人／对话：本线实施对话（角色技能完整解读 P2 系列，2026-10-18 第 7 批）
- 状态：**待针对性审查**（已实施、验证全绿、全链字节可复现）
- 允许写入范围：`scripts/character_skills/`、`output/character_skills/`（本批产物与 README／交接）、
  `work/p7_*` 与 `work/p7_denju/`（本批快照、一次性探针）、`docs/tasks/20261018-character-skills-p7.md`（本文件）
- 共享依赖（只读）：`work/protection/il2cpp_loader_seed1.bin`、`work/protection/metadata_aei_decoded.bin`、
  `output/cache_full_20261015_v3/decoded/{denju,denju_lblist,bossinfo,charainfo}.data5.json.raw`、
  `output/base_master/{_mdBossInfo,_mdCharacter}.json`、`work/p7_records_before.jsonl`（P6 终态快照）
- 未触碰：`review/` 历史报告、`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、
  `docs/tasks/character-skills-progress.md`（主持）、其他任务未提交文件；未提交、未推送、未发布

## 目标（逐项）

1. **第 0 项（先修）**：p2b6 审查 5 条文字注记——交接 §2③ 门控地址多一位「1」、§6 注释 `cid30236→2205`、
   1059 门控特例实为 ≤0、玩家侧 `GetAbilityOnFlagIndex_ParamN` 极值选择补注、武器跳转表项为字节补注。只改文字。
2. **denju 记录结构解析**：效果类型在哪个字段、参数槽布局、与 charainfo／bossskill 的同异；
   逐 ID 缓存优先、缺才回退 APK。
3. **处理器路径取证**：`GetDenjuSkill` 的完整链路（denju 记录如何装载、类型与参数如何进 BattleBossSkill），
   受控原生证据；确认后复用等价门控与 boss 类型规则。
4. **应用规则生成 denju 答案**，每条记录挂回其角色页（`denju_id==cid`；名称不匹配行只按 ID 关联并注明）。
5. **应用＋重建 profiles／gaps**；报告覆盖增量（双／三口径、受影响角色数、状态迁移）与缺证。

## 关键做法与结论

- **结构（先查数据再查代码）**：denju 1504 行的键集里**没有 skillparam**（唯一的 param 形状键是 `scost`）；
  946 行带 `patternid0..5`（995 个引用字段）。效果类型与数值只能来自 `denju.patternidN → bosspattern → bossskill`。
  独立交叉证据：`denju.sname` ＝ 所指 pattern 的 `sname`（950 个引用字段）、`denju.stext` ＝ pattern 的 `sinfo`（820 个，
  29 行两者都非空但不同）⇒ denju 行是「该 pattern 的文本同伴」。
- **原生（元数据＋逐指令复读，17/17）**：`BattleParam.CreatePlayer` → `GetBattleDenju`（门控 `EnableDenjuSkill`：
  接收方 `isDenjuFrom`／传授方 `isDenjuTo`／同 `jobtype`／`daLimitBreakDenju.GetDenju≠null`）→
  `BattleParam.InitlizeDenjuSkill`（`_denju@0xa20`／`_denjuSkill@0xa10`／`_denjuListPattern@0xa18`）→
  `GetDenjuSkill`＝`CharaParamToBossSkill`（类型＝`charaParameter._skillid[0]`，槽位下标对齐）＋
  `GetDenjuPattern`（`daLimitBreakDenju`，即 `denju_lblist`）。**战斗执行** `GetExecSkillInfo` 用 `_denju`
  取名字/费用并以 `_denjuListPattern` 调 `bhExAttack.think_attack` ⇒ 数值走 denju chain 的 bossskill。
  `daDenjuParameter.GetInfo`（denju 行本身）的调用方全在 UI／卡面侧，无战斗消费者；
  `DenjuMasterData_J`（cid/initiation/forget）是另一张关系表，不混用。
- **应用**：`link_skills.py` 抽出 `resolve_pattern()`，让 `denju.patternidN` 与 `charainfo.patternN` 走**同一个**助手，
  把 pattern 的 bossskill 挂成 denju 记录的 `boss_skill_refs`（＋`boss_skill.s_ability` 的 skilllist 交叉引用），
  由既有 `bossskill` 规则出答案；不新增规则、不改任何既有规则数值。
- **关联**：一律 `denju.denju_id == cid`（1500/1504 落在角色表）；224 行 `sname` 与角色 `skillname` 不同者
  在 `link_status` 注明「只按 ID 关联，不按名称推断」。
- **顺手修正**：`denju_lblist`（传授突破）5 个条目此前共用记录键 `cid`，导致 2—5 号条目显示 1 号的内容；
  改逐条键 `cid#i` 并把各条目 pattern 的技能挂出（+44 记录、0 答案丢失）。
- **第 0 项**：5 条注记逐条整改（纯文字／文档字段），验证「1059 `/param0` 文本首个数值不变、raw/kind/unit/status/scope 0 变化」。

## 产物

| 产物 | 位置 |
|---|---|
| denju 结构与交叉证据（键集／解析统计／分歧统计／缺件清单） | `output/character_skills/denju_skills/structure.json` |
| 原生链路受控检查 17/17 | `output/character_skills/denju_skills/native_checks.json` |
| 逐行链证据（1504 行：patternid→pattern→skills＋与自身必杀技对比） | `output/character_skills/denju_skills/denju_chains.jsonl` |
| 三口径增量＋零破坏对账 | `output/character_skills/denju_skills/p7_increment.json` |
| 直读原始表的 M 区交叉核对 | `output/character_skills/validation/crosscheck_raw.json` |
| P6 终态快照（增量与零破坏基准） | `work/p7_records_before.jsonl`、`work/p7_summary_before.json` |
| 一次性探针与 GBK／可复现核对 | `work/p7_denju/gbk_run.py`、`hashes_{before,after}.json`、`createplayer.txt` |
| 交接 | `output/character_skills/P7_HANDOFF.md` |

## 关键数字（本批增量）

- 新增答案 **3236**（页求和）／**3236**（记录级，`summary.rule_answers_unique_records`）／
  **210**（（表,记录,层,字段）新增唯一键）；按类型页和 13→2296、2012(SA)→456、105→184、112→147、
  27→100、66→29、16→24；分组口径 denju 3056＋denju_lb 180。
- 规则答案 56953 → **60189**；唯一记录级 56120 → **59356**；顶层记录 13569 → **13613**（传授突破逐条键 +44）。
- 未解释参数槽 417790 → **449862**（+32072，全在新挂子记录；既有记录未解释键 0 减少；11 个旧键随逐条键替换消失）。
- 可达角色（本批规则命中）**579**；状态迁移：**1 个角色**由「仅未知」变为「部分」（部分 1862→1863、仅未知 374→373）。
- 断链 0 → **3**（6 个 patternid 两源均缺，名册内命中 3 人）。
- 缺口队列字段级 5715（不变）、类型级 377（不变）、有线索 296（不变）、断链分组 1。
- **零破坏**：既有答案键 **0 丢失**、raw／kind／unit／status／scope **0 变化**；457 条只改文本
  （第 0 项注记 3 的 1059 `/param0` 特例句），首个数值 0 变化。

## 验证

`verify_p1.py` **149/149**（+18）、`denju_skills.py` 自检 **17/17**、`skilllist_types.py` **53/53**、
`crosscheck_raw.py` **A–M overall_ok**（M 区 2600 条 denju 页答案＋519 条 SA 引用从原始表重算，0 失配）；
默认 GBK（`PYTHONUTF8=0`）下 **11 个入口 exit 0 且 stderr 0 字节**；重跑全链 **25 份关键产物 SHA-256 逐字节相同**；
相对 P6 终态快照既有答案 0 丢失 0 变化。

## 下一步（留给后续批次）

1. `AbilityTypeCachedFlagIndex` 静态 rank 与 flag index 的完整对照表；
2. `charaParameter.get_home` 在记录缺 home 时的返回值（「0 组是否命中缺省角色」）；
3. 头部类型 3／22／110 的伤害基数全局技能表（本批 denju 链上最大的未解释块就是这些类型）；
4. bosspattern（1307）、extra_ability_info（494）；charainfo 3/22/110 的全局技能表；
5. `_denjuSkill@0xa10` 的消费点（`haveAbility`／`setupAbilityFlag` 的同偏移读取）与 `denju.weaponChange` 语义。
