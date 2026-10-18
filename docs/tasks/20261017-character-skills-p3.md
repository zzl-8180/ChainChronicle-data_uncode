# 任务记录：角色技能完整解读 P2 第 3 批（暴击率／暴击伤害双路径锚定）

- 任务标识：`20261017-character-skills-p3`
- 负责人／对话：实施对话（DeepSeek 4.1 Flash，2026-10-17）
- 状态：**第 0 项五项修正 ＋ 五项范围全流程落盘 ＋ p2b3 审查整改 2 项 ＋ 验证通过（verify 89/89、crosscheck A–I
  `overall_ok`、DOM P2 19/19、真实浏览器核对、默认 GBK 九入口回归）＋ 收尾两项已完成**；等针对性审查。
- 写入范围：`scripts/character_skills/`（`skilllist_types.py`、`rules.py`、`verify_p1.py`、
  `crosscheck_raw.py`）、`output/character_skills/`（新增 `P3_HANDOFF.md`、`skilllist_types/` 的
  `crit_anchoring.json`／`unindexed_paths.json`／更新其余产物，更新 `README.md`、`P2B2_HANDOFF.md`
  的待办登记与 `review/p2b2_20261017_thirdparty/RECTIFICATION.md` 的计数文字）、
  `work/character_skills_p2/`（夹具）、`work/character_skills_p3/`、本文件、
  `HANDOFF.md`／`STATUS.md`（仅角色技能线段落／一行）。
- 未触碰：`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、`docs/tasks/character-skills-progress.md`（主持）、
  其他任务记录与未提交文件、`scripts/query_effect_dictionary.py`、公共解包生成器、
  `review/*/REPORT.md` 与 `RE_VERIFICATION.md`（字节未动）。未提交、未推送、未发布、未启动其他对话。

## 启动前核对

P2 第 2 批已闭合：`review/p2b2_20261017_thirdparty/RE_VERIFICATION.md` 结论**通过**（五项修复点独立核实、
中性桶缺陷已修、镜像 sha256 `562a6975…47c1` 一致），另附 5 条文字级观察项（O1–O5）＝本批第 0 项。

## 第 0 项（复验 O1–O5，只改文字与死代码）

1. **O1** `RECTIFICATION.md` 的 DOM 计数 19/19 → **18/18**（原写把 `run(` 函数定义行计入），
   两处（摘要与回归表）都已更正并注明原因。
2. **O2** `P2B2_HANDOFF.md` §3 补口径对应句：新增答案 **6209（页求和）／2869（全局唯一）／
   5730（summary 记录级＝standalone 2862 ＋ children 2868）**。
3. **O3** 生成的 `skilllist_types/README.md` 补「**复合分支的槽位清单是下界估计**」整段（说明扫描窗口、
   `slot_list_scope`、`leaf`／`gate_rva`／`slot_calls` 的对齐方式），由生成脚本产出并重建。
4. **O4** APK `type8` `param4` 待办**字面登记**：`output/character_skills/README.md` §5 第 11 条与
   `P2B2_HANDOFF.md` §6 各补一条（本批第 2 项处理，处理结果见下）。
5. **O5** `report_increment()` payload 的重复键（`new_answers_summary_caliber` 两组）去掉前一组死代码，
   产物不变。

## 五项范围与结果

| 项 | 内容 | 结果 |
|---|---|---|
| 1 | 用修正后的中性判据索引两条暴击累加路径 | **完成**：`GetAbilityCritical`（0x1119018）／`GetAbilityCriticalDmgRate`（0x1119794）并入派发索引，索引路径由 3 条增到 **5 条**；两路径的累加是 **fadd（加算）**，`ACCUM_OP` 按路径声明 |
| 2 | APK `type8 param4` 是否存在未索引读取路径 | **完成（结论已细化）**：按类型分派**无**（185 个 `get_ability` 调用点上 type 8 的分支都不读 param4/param0）；**但不按类型分派的读取者存在**（178 个 param4 读取点中 136 个的所属函数不按类型分派，实际案例 `CharaBehavior.Attacked` 0x153eb1c→0x153eca4 的 support2 组装块）→ **仍不给规则**，见下 |
| 3 | 锚定 2012／3000／1008／1095 的暴击口径 | **完成**：四者在两条累加路径上**都落中性**，登记 `read_elsewhere`；机制分别指向 support2（2012）、Support3（3000）、未定位（1008／1095）；**不改其既有答案** |
| 4 | 扩新类型 ＋ 核查 type67 | **完成**：新增 8 条规则（36 `/param4`；1003／1005／1026 各 `/param4`＋`/param5`；3 `/param7`）；80／96／67 落复合分支→缺证不给规则；1036 索引到但无记录；1112 分支不读槽；type9／51 候选经核实**不在**两路径上（未采纳） |
| 5 | 应用并重建，区分性样本 | **完成**：审查整改后新增答案 **1179** 条（页求和）／**1085** 条（记录级）／**881** 条（（表,记录,层,字段）去重）；173 个角色迁移；区分性样本含「同记录 rate ≠ dmg」与「取值相同仍不互换」（见下） |

## 关键原生发现

1. **两条暴击累加器的形状**（与三条乘算路径同构但为加算）：
   `IsEnableAbility` 门控 → `skillParameter.get_paramN` → **`fadd s9,s9,s0`**；分支体自己界定、中性＝解析到该路径循环尾。
   分支与门控地址（产物 `dispatch_map.json` 的 `gate_rva`／`slot_calls` 逐项可核）：
   - 暴击率：`0x111933c`（type 36/1003/1005/1026，gate `0x1119348`，读 `param4`）、`0x1119388`（1036）。
   - 暴击伤害：`0x1119a48`（1003/1005/1026，gate `0x1119a54`，读 `param5`）、`0x1119a70`（1036）、
     `0x1119ce8`（type 3，读 `param7`）。
2. **循环后的夹紧**：暴击率 `fmov s8,#0.5 / fcmp / b.gt → 0.5`，`fcmp #0.0 / b.pl → 原值 else 0.0` ⇒ **[0, 0.5]**；
   暴击伤害 `#2.0`／`#-1.0` ⇒ **[-1, 2]**，之后 `fadd` 上 `PlayerManager.GetAbilityCriticalDmg`。
3. **口径结论**：两条路径都是**加算** ⇒ 「暴击率＝百分点加算、暴击伤害＝系数加算」站得住；但**夹紧范围按机制不同**
   （本路径 rate [0,0.5]／dmg [-1,2]，2012 的 support2 路径为 [0,.5]／[-1.5,1]），不得跨机制套用。
4. **正文明示交叉验证**：type 36 的 `100507/100508/100509` 正文「クリティカル発生率 10%/7%/5%」对应
   `param4 = 0.1/0.07/0.05`（百分点直接可读）；type 3 的 `107015`「ボスWAVE時、攻撃力とクリティカル威力が上がる」
   对应 `param7 = 0.1`；type 1005 的 `27008`「クリティカル威力が上がる」对应 `param5 = 0.75`。
5. **item 2 的实测**：`CharaBehavior.Attacked` 的 support2 组装块（`0x153eb1c`→`0x153eca4`）按
   `int(param0)∈{0,1,2}`（mode 1 另需 `param_flag & 攻击旗标`）+ 槽位表查表进入，把
   `param1/2/3/5/6/8` 与 **`param4`** 写入 `TimePowerUpData` 后 `setSupport2` —— **不按能力类型分派**。

## 覆盖增量（相对 P2 第 3 批基线，基线已快照）

- 规则答案：36684 → **37863**（页求和）；唯一记录 35981 → **37066**；新增 **1179** 页／**1085** 记录级／**881** 去重行。
- 按类型（页求和）：type 36 → 229、1005 → 112、3 → 89、1026 → 46、1003 → 18；
  按（记录,字段）去重：36 → 46、3 → 29、1005 → 18、1026 → 2、1003 → 2（合计 97，见
  `skilllist_types/crit_increment.json`，由 `skilllist_types.py --report-crit-increment` 生成）。
- 未解释参数槽：438059 → **436880**（−1179）；缺口字段级 5783 → **5766**；有线索 319 → 316。
- 角色状态：仅未知 645 → **560**，部分 1591 → **1676**；**85 个角色由「仅未知」变为「部分」**。
- 受影响角色（可达暴击路径记录）：共 **288** 个（type 36 → 156、3 → 84、1005 → 38、1026 → 17、1003 → 8）。
- 证据范围：已逐条评审 9400 不变、按类型套用 27284 → **27778**（未新增第三类）。

## 区分性样本（防 pp 与系数混淆）

| 样本 | 期望 | 说明 |
|---|---|---|
| `skilllist 27001`（type1005） | `param4=0.12` → **暴击率 +12 个百分点**；`param5=0.1` → **暴击伤害系数 +0.1** | 同一记录两个槽取值不同、种类与单位不同 |
| `skilllist 30830500`（type1005） | `param4=0.3` → +30 个百分点；`param5=0` → 系数 +0 | 一增一零，方向与种类都可区分 |
| 取值相同的 4 条记录 | 即使两槽原值相同，仍输出「百分点」与「系数增量」两个不同种类 | 防「值相同就互换/合并」 |
| `skilllist 100507/8/9`（type36） | 正文 10%/7%/5% 与 `param4` 一一对应 | 百分点口径的正文对照 |
| 任何暴击答案 | 种类中不含「倍率」 | 防把加算写成相对乘 |

## 中途发现并修掉的自有问题

1. 把两条暴击路径加进 `FUNCS` 后，`derive_terminals` 一度把**已声明的决策节点**也当停止点，
   导致三条既有路径（defence 7/8/26 等）解析回退 → 改为只把**纯指令起始的已声明叶**当显式停止点
   （`PURE_LEAVES`），其余叶由「首条非纯指令」自动发现。
2. `reaches_multiply_tail` 字段名对加算路径已不准确 → 更名 `reaches_accumulate_op`，
   并补「分支把值交给出口处的共享 `fadd`」的识别（type 3／1036 即此形态）。
3. `crit_rule_rows()` 首版漏 `return rows` 与一个右括号 → 语法/类型错误，已修。
4. 槽位名提取 `nm[22:]` 前缀长度写错（应为 19），一度把 `param4` 显示成 `am4` → 已修并复核。
5. verify 的暴击检查首版未按 type 限定，误把 type 28（概率阈值）等记录计入 → 限定到
   `CRIT_TYPES` 限定后通过（整改后 89/89）。

## 运行命令（项目根目录）

```powershell
& .\.venv\Scripts\python.exe -B scripts/character_skills/skilllist_types.py        # 5 条路径索引＋新规则
& .\.venv\Scripts\python.exe -B scripts/character_skills/profiles.py              # 应用新规则
& .\.venv\Scripts\python.exe -B scripts/character_skills/gaps.py
& .\.venv\Scripts\python.exe -B scripts/character_skills/skilllist_types.py --report-crit-increment
& .\.venv\Scripts\python.exe -B scripts/character_skills/verify_p1.py             # 89/89
& .\.venv\Scripts\python.exe -B scripts/character_skills/crosscheck_raw.py        # A–I overall_ok
node work/character_skills_p2/html_dom_test.js                                     # 19/19
```

## 验证

- `verify_p1.py` **89/89**（p2b3 整改后；整改前 85/85。P1 40 ＋ P2-1 16 ＋ P2-2 18 全保留；本批新增 11 项：暴击路径槽位／加算性／
  **rate 与 dmg 槽不同**、既有暴击规则不在两累加器上、`unindexed_paths` 结论、
  暴击答案单位是百分点 vs 系数增量、`no_relative_multiplier_wording`、
  同记录两槽不同/相同两类样本、取值相同仍不互换）。
- `crosscheck_raw.py` **A–I `overall_ok=True`**：新增 I 项逐条重读原始 skilllist，核对 **89** 条暴击答案的
  原值与口径（rate 必须百分点、dmg 必须系数增量）并检查各自落在路径夹紧范围内（rate [0,0.5]／dmg [-1,2]）。
- `skilllist_types.py` 受控原生检查 **32/32**（新增 6 项：暴击率/暴伤槽位、加算性、rate≠dmg 槽、
  既有暴击规则不在两累加器上、`unindexed_paths` 结论、累加算子按路径声明）。
- DOM 夹具 **19/19**（新增 1 项守暴击种类的百分点/系数区分）；**真实浏览器**核对页头
  「部分 1676／仅未知 560」与 cid8193 的 `skilllist #27017` 块。
- **默认 GBK 环境**：九个生成器 ＋ `query.py` ＋ `verify_p1.py` ＋ `crosscheck_raw.py` 全部 exit 0、
  stderr 0 字节。

## 剩余缺口与阻塞

- **type 80（HoldMana）／96（ManaCountUp）／67（HeroOne）**：两条暴击路径上落**复合分支**，
  分支体内先调 `CalcCharaNum`／`PanelManaGage.isCurrentManaJob_or·_and`／`Constants.ConvJobFlagToElementFlag`
  再读多槽，**哪一槽最终喂进累加器未跟踪** → 不给规则。补到后可按「mana 条件 + 按人数缩放」给暴击规则。
  （type 67 因此仍是缺证：本批新增的是「它确实出现在两条暴击路径的分派表里、落 `0x11193d4`／`0x1119b90`」
  这一段证据，不足以定槽。）
- **type8 `param4`**：只知道「无按类型分派的读取路径」；support2 路径对 type-8 记录的**可达性**
  （槽位表内容、type-8 记录是否入表）与语义未确认 → 仍未解释。这是本批对上一批辅助依据的**修正**：
  从「无读取路径」降级为「无按类型分派的读取路径」。
- 1036（HyperModeUp）无任何记录；1112 分支不读槽；type 9／51 不在两路径上。
- `attack 67/68` 的运行期指针解引用建模、`type 1059` 队伍施加路径、`charainfo 3/22/110` 的全局技能表、
  `X1` 的 104 角色（均沿用既有登记）。

## 下一批建议（交主持决定）

1. **type 80／96 的暴击喂入槽**：继续跟踪复合分支内 `fadd` 的来源（最可能是「mana 数量 × 系数」中
   `param0`/`iParam0` 的组合），一旦定槽即可为 229／63 条记录给规则。
2. **type 36／1003／1005／1026 的 `param1`／`param2`／`param3`**：这些 type 的这三槽落在与 type 8 相同的
   已确认单槽分支（攻击／移动／受伤量），规则可复用，本批按范围未加——是现成增量。
3. `cAbility*Work..ctor` 一组（不按类型分派的 param4 读取者）的字段归属，可回答 type8 `param4` 的
   可达性问题。

## 最近更新

2026-10-17：第 0 项（复验 O1–O5）→ 原生勘察（两条暴击累加器分支/夹紧/fadd、type8 param4 读取者排查、
2012/3000/1008/1095 路径归属）→ 落盘（`skilllist_types.py` 5 路径＋8 条新规则、`rules.py` 转换器、
`crit_anchoring.json`、`unindexed_paths.json`）→ 重建 profiles/gaps 并核对增量 → 扩展 verify（现 89/89）
与 crosscheck（A–I）→ DOM 19/19 ＋ 真实浏览器 → GBK 九入口回归 → 收尾（README §3.3、任务记录、
`P3_HANDOFF.md`、HANDOFF/STATUS、修正 P2B2 的 param4 待办登记）。
下一步：等针对性审查结论，通过前不开下一批。


## p2b3 审查整改（2026-10-17，审查后）

审查报告：`output/character_skills/review/p2b3_20261017_thirdparty/REPORT.md` ＋ `findings.json`
（结论「需修正」，2 项）。整改记录：同目录 `RECTIFICATION.md`。**2 项全部处理，无未采纳。**

1. **【会漏答案，核心】暴击两路径的低号 type 分支被误登中性**——先自行复现根因：两条路径的位测试常量 1
   由函数序言放在 **X26**（rate `0x111918c mov w26,#1`）／**X29**（dmg `0x1119918 mov w29,#1`），
   而原 `Resolver.resolve()` 只初始化 X0／X21／X23。**附带发现**：unicorn 的 `UC_ARM64_REG_X29` 值为 `0x1`，
   按 `UC_ARM64_REG_X0 + 29` 写寄存器会写错（X0+21／X0+23 恰好正确，故此前未暴露）——
   已改为显式名字映射 + 自动扫描序言 `mov wN,#1` 预置。
   重跑后新增 11 个条目（rate 1／2→`0x111933c` param4、6／7→`0x1119364` param5、3／34→`0x1119318` param6；
   dmg 1／2／36→`0x1119a48` param5、6／7→`0x1119a24` param6），与审查逐项一致；
   **全索引 0..3000×5 diff：三条乘算路径 0 新增／0 删除／0 变化**。
   据此新增 **9 条规则**（1/param4、2/param4、6/param5、3/param6、34/param6、1/param5、2/param5、6/param6、36/param5），
   规则表改为**由 dispatch_map 派生**（不再硬编码清单）；type 7 既有 `/param5`／`/param6` 与新定位一致 →
   登记锚定、**数值未改**；**1036** 分支带 `×int([BattleParam+0x328])÷1000` 缩放、**67／80／96** 复合分支
   → 不套用单槽规则（缺证）。
2. **【文字】`crit_increment.json` 去重键塌陷**：子记录无 `rec_key` → 键塌陷成 (type, 字段) → 报 97；
   改为 `(table, record_id, layer, field)` 并与快照做差集 → **881**；审查报的修正前真值 **355** 我独立复现
   （3:76、36:153、1003:16、1005:76、1026:34，正是修正前 8 条规则在该键下的行数，页求和仍 494）。

**整改后增量**：1179 页／1085 记录级／881 去重行；按类型（页／行）1→156/114、2→76/64、3→177/151、6→114/98、
34→33/28、36→447/300、1003→18/16、1005→112/76、1026→46/34；**173 个角色迁移**；缺口字段级 5766。
**对账**：相对 P2B2 快照 0 条答案缺失、0 条 kind/value 变化；修正前 8 条规则答案仍为 355 行／494 页。
回归：`skilllist_types.py` 32/32、`verify_p1.py` **89/89**（新增 4 项：低号 type 不落中性桶、掩码寄存器声明、
type7 锚定一致、缩放/复合类型不套用规则）、`crosscheck_raw.py` A–I `overall_ok`（I 项改由
`field_dictionary.json` 的 `answer_kind` 驱动，核对 370 条）、DOM P2 **20/20**、默认 GBK 九入口 exit 0。
