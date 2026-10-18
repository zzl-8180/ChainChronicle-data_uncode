# 任务记录：角色技能完整解读 P2 第 2 批（skilllist 能力类型 8/26/67/1059）

- 任务标识：`20261017-character-skills-p2b2`
- 负责人／对话：实施对话（DeepSeek 4.1 Flash，2026-10-17）
- 状态：**第 0 项文字修正 ＋ 四项类型全流程落盘 ＋ 验证通过（verify 71/71、crosscheck A–H `overall_ok`、
  DOM 12/12、真实浏览器核对、默认 GBK 九个入口回归）＋ 收尾两项已完成**；等针对性独立审查结论。
- 写入范围：`scripts/character_skills/`（新增 `skilllist_types.py`，改 `rules.py`／`verify_p1.py`／
  `crosscheck_raw.py`）、`output/character_skills/`（新增 `skilllist_types/`、`P2B2_HANDOFF.md`，
  更新 `README.md` 与本批重建的 `profiles/`／`gaps/`、`charainfo_types/README.md` 的一处文字）、
  `work/character_skills_p2b2/`、`work/character_skills_p2/`（夹具）、本文件、
  `HANDOFF.md`／`STATUS.md`（仅角色技能线段落／一行）。
- 未触碰：`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、`docs/tasks/character-skills-progress.md`（主持）、
  其他任务记录与未提交文件、`scripts/query_effect_dictionary.py`、公共解包生成器、
  `review/r1_*`／`r2_*`／`p2b1_*` 历史报告（字节未动）。未提交、未推送、未发布、未启动其他对话。

## 启动前核对

P1（R1／R2＋复验）与 P2 第 1 批（`review/p2b1_20261017_thirdparty/REPORT.md` 结论**通过**，
六项核心声称独立复核成立、零条答案级错误）均已核实落盘；第 2 批提示词第 0 项的两处文字小问题
（P2-1 增量数字、NOT_AMONG「分两类」）已按审查建议修正，未动数据与脚本。

## 第 0 项文字修正

- `docs/tasks/20261017-character-skills-p2.md`：覆盖增量改为与产物一致
  「有归属 7383 → **7862**（基线 7383 ＋ 增量 **479**；口径＝基线条目 31 ＋ 关键词提示片段）」。
- `output/character_skills/charainfo_types/README.md`：补「**本批 20 个角色全部落在第一类
  （`IN_RANGE_HANDLER_FOUND`），第二类为空**」，并注明该文件由脚本生成、生成脚本内同段文字尚未同步。

## 四项类型全流程与结果

| 类型 | 枚举名 | 受影响角色 | 结论 | 槽位（原生） |
|---|---|---|---|---|
| 8 | `Always` | 868 | **本批确认** | 攻击 ← `param1`、移动速度 ← `param2`、受伤量 ← `param3`；资格门控无条件通过 |
| 26 | `ManaGet` | 707 | **本批确认** | `param4` 开局追加玛那个数、`iParam1` 职业位图、`param6` 生效范围 0/1/2、`param7` 不限职业的追加个数 |
| 67 | `HeroOne` | 598 | **缺证，不给数值** | 分支先 `CalcCharaNum` 计数＋mana 职业判定再读 param0/iParam0/param8/flag/param1/param6/param3/param2，最终换算未跟踪 |
| 1059 | `UnionCount` | 432 | **缺证，不给数值** | 三条累加路径均落中性分支 → 队伍范围效果，施加路径未定位 |

原生方法：`BattleParam.GetAbilityAttack`（0x1107390）、`GetAbilityDefence`（0x1107df0）、
`GetAbilityWalkSpeed`（0x1118900）、`IsEnableAbility`（0x1112574）、
`PlayerManager.PartyAbilityInit` → `subPartyAbilityInit_ManaGet`（0x158c958）。
复用 P2 第 1 批的「handler 槽位筛选」方法：先解析 type→分支（Unicorn 执行游戏自身 switch 前导字节），
再静态读出该分支的 `skillParameter.get_paramN` 调用。

## 覆盖增量（相对 P2 第 1 批基线，基线已快照）

- 规则答案：30475 → **36684**（页求和）；唯一记录 30251 → **35981**；新增 **6209** 页／**2869** 唯一。
- 按类型：type8 3846 页／1185 唯一；type26 2363 页／1684 唯一。
- 未解释参数槽：444268 → **438059**（−6209）。
- 角色状态：仅未知 913 → **645**，部分 1323 → **1591**；**268 个角色由「仅未知」变为「部分」**。
- 缺口队列：字段级 5790 → **5783**；类型级 377、有参考线索 323 → 319、断链 0。
- 证据范围：已逐条评审 9400 不变；按类型套用 20553 → **27284**（未新增第三类）。

## 关键原生发现

1. 三条 apply 路径的分支形状一致：`IsEnableAbility` 门控 → 读一个槽 → `fmul` 乘进累加因子。
   type 8 的三条路径分别读 `param1`／`param2`／`param3`，且掩码寄存器在进入循环前被置 1
   （attack `mov w23,#1`；defence `stp w23,w21,[sp,#0x18]` 后 `mov w21,#1`），
   故分支只由 type 决定、与调用方参数无关。
2. 与既有已确认规则交叉核对：type 7／1095 的已确认攻击/移动/受伤量字段**正好**被本批三条路径覆盖；
   其余已确认字段（暴击率/暴击伤害系数、param0 地形、param7 间隔）走别的读取路径，
   暴击的两条独立累加路径为 `GetAbilityCritical`（0x1119018）／`GetAbilityCriticalDmgRate`（0x1119794）。
3. type 26 的 `iParam1` 是职业位图（逐位 → `Constants.GetJobMana` → `ManaIcon.transELEMENT_TYPE_FLAG`），
   `param4` 决定 `ProduceManaForce` 的调用次数（`int(param4)` 次），`param6` 的 0/1/2 三分支决定生效范围。
4. 方向防错：skilllist 304 正文写「攻撃力は増加するが、受けるダメージも増加する」而 `param3=1.1`，
   与「param3 = 受伤量倍率」一致；记录 351 正文「**与える**ダメージが増加」（造成的伤害）而 `param3=1`，
   说明「造成的伤害」不在本槽（属子效果记录），两类正文明文可区分。

## 中途发现并修掉的自有问题

1. `is_pure` 未把条件分支（`b.le`/`b.hi`…）算作纯指令 → 全部解析停在 switch 首条条件分支、
   槽位全空。改为「`b`／`b.*` 为纯，`bl` 不是」。
2. 防御/移动分支的终止地址集合写成硬编码，漏了 `0x1108108` 这类节点 → 改为**自动推导**：
   显式纯起始叶 ＋ 区域内所有「首条指令不是纯指令」的分支目标。
3. 叶扫描的退出条件只认循环尾、不认共享乘法尾（`fmul` 处）→ 槽位列表串到相邻分支，
   type8 attack 一度读出 param0/iParam0/param8/flag。改为同时以 `TAIL_MUL` 退出。
4. 交叉核对检查写成「既有规则字段必须全部被三条路径覆盖」，对暴击/地形类字段不成立 →
   改为「type 7／1095 的已确认攻/移/伤字段必须正好覆盖 ＋ type8 三条路径恰好是三个单槽」，
   其余字段登记为 `read_elsewhere` 并注明暴击另走两条路径。
5. 增量统计未递归子效果记录 → 页求和少算（2966 vs 6209）。改为递归 `children` 后与 summary 增量完全一致。
6. `crosscheck_raw.py` 的方向判据用「正文出现 受けるダメージ」→ 把「受けるダメージを軽減する」也算成增加；
   收紧为「受けるダメージ…増加／ダメージも増加」后，351 的「与えるダメージ」不再误命中。

## 运行命令（项目根目录）

```powershell
& .\.venv\Scripts\python.exe -B scripts/character_skills/skilllist_types.py            # 索引＋新规则字典
& .\.venv\Scripts\python.exe -B scripts/character_skills/profiles.py                  # 应用新规则
& .\.venv\Scripts\python.exe -B scripts/character_skills/gaps.py
& .\.venv\Scripts\python.exe -B scripts/character_skills/skilllist_types.py --report-increment
& .\.venv\Scripts\python.exe -B scripts/character_skills/verify_p1.py                 # 71/71
& .\.venv\Scripts\python.exe -B scripts/character_skills/crosscheck_raw.py            # A–H overall_ok
node work/character_skills_p2/html_dom_test.js                                         # 15/15
```

## 验证

- `verify_p1.py` **71/71**（P1 40 项 ＋ P2-1 16 项全保留；本批新增 15 项：原生检查全过、type8 三路径槽位、
  type26/1059 不在三路径、受影响角色 868/707/598/432、67/1059 无确认规则、type8/26 有答案、
  type8 param4 与 param0 不被答、新类型不产暴击类答案、**受けダメージ方向**、param3<1 全减伤、
  **移动 vs 受伤量不互换**（56 样本）、param4/param7 不混同（212 样本）、iParam1 职业位图、param4 整数截断）。
- `crosscheck_raw.py` **A–H `overall_ok=True`**：H 项逐条重读原始 skilllist 记录，核对 **2862** 条答案原值、
  type26 param4 的截断文案、type8 的受伤量方向（2 条明文「受けるダメージ…増加」记录）与
  「type8 param4 不得有答案」。
- DOM 夹具 `work/character_skills_p2/html_dom_test.js` **15/15**；**真实浏览器**（本地 http.server）核对
  页头「部分 1591／仅未知 645」、cid5 的 type8 块（`自身攻击×1.2`、`受伤量×1.1（本项增伤 10%）`、
  无固定防御量混淆、`param4` 未解释）、cid2 的 type26 块（玛那数量／职业位图／范围选择码）。
- **默认 GBK 环境**：九个生成器 ＋ `query.py` ＋ `verify_p1.py` ＋ `crosscheck_raw.py` 全部 exit 0、stderr 0 字节。

## 剩余缺口与阻塞

- type 67（598 角色）：`HeroOne` 的 apply 分支先调用 `BattleParam.CalcCharaNum`、
  `PanelManaGage.isCurrentManaJob_or/_and`、`Constants.ConvJobFlagToElementFlag`，
  再读 `param0..param3／param6／param8／iParam0`。**缺证**＝`CalcCharaNum` 的计数口径与这些槽的最终换算；
  补到后可按「按人数缩放的攻/防/移动」给规则。
- type 1059（432 角色）：三条累加路径中性 → 队伍范围效果。**缺证**＝按队友人数施加的支援路径
  （`GetAbilityListOnFlagIndex`／`AbilityTypeCachedFlagIndex` 指向的 flag 桶是下一步入口）。
- 参考分析给 67/1059 的槽位标签（含暴击率/暴击威力）未获原生支持，**不采纳**；暴击两条累加路径本批未索引。
- type 8 的 `param0`（记录中不存在）／`param4`（恒 1，无读取路径）、type 26 的 `param0/1/2/3/5` 未解释。

## 下一批建议（交主持决定）

暴击族两条累加路径（`GetAbilityCritical` 0x1119018、`GetAbilityCriticalDmgRate` 0x1119794）
是现成入口，可把 type 2012／3000／1008／1095 的暴击率与暴击伤害系数槽位一并锚定，
并可与「暴击率＝百分点加算／暴击伤害＝系数加算」的既有口径对照；其次是 type 67 的 `CalcCharaNum`。

## p2b2 审查整改（2026-10-17，本轮）

审查报告：`output/character_skills/review/p2b2_20261017_thirdparty/REPORT.md`
（结论「带明确限制通过」；会给错答案 0 项）。整改记录：同目录 `RECTIFICATION.md`。**5 项全部处理，无未采纳。**

1. **（核心）索引中性桶误判**：`leaf_slots()` 删掉「地址越过循环尾即退出」的前提，改为按分支体自身界定
   （首条无条件 `b` 退出／`fmul s8,s8,s0` 命中／窗口 0x400）；`_compact()` 的中性判据改为「解析到该路径
   循环尾」，并把「有真实分支但窗口内无槽位」单列为 `branch_no_slots_in_window`（本批仅 1112）。
   defence 67/96/1036、move 96/1036 五个分支现落 `entries` 且不入 `neutral_ranges`，`leaf` 与审查者地址逐项
   一致（move:1036 的 `leaf=0x1118d74` 为该分支目标，审查者引用的 0x1118d80 是同体内
   `bl IsEnableAbility`，产物新增 `gate_rva` 记录之）；每个条目新增 `gate_rva`／`slot_calls`／`exit`／
   `reaches_multiply_tail`。`type_evidence.json` 与 `native_checks.json` 的自相矛盾消除（type 67 的
   defence 现为 slots=[param0,iParam0,param8,flag,param3]）。attack 96 的串扰修正为
   `slots=[param0], gated=false`；attack 67/68 按审查口径保持原静态结果并注明下界估计。
   原生检查 18 → **22/22**；`verify_p1.py` 新增 3 项中性判据检查（→ **74/74**）。
2. **type26「不产出」限定路径**：`/param4`、`/param7`、`/iParam1` 的文案改为「**这条产线**不产出／
   不另行追加」，三字段统一附注「本类型另有 param0..3 四条产线（0x158cb8c／0x158cbf8／0x158ccb4／
   0x158cddc），本批未解释，不能据此断言该能力整体不产玛那」。我按「已答记录」口径复算这类记录
   **164 条**（审查报告 166，差 2 条为口径细节）。交接的「3101 全 0」更正为 `param0=1.0` 未解释。
3. **type8 param4/param0 分源口径**：检查改为 `type8_param4_param0_scope_two_sources`——缓存 328 条
   param4 恒 1／无 param0；**APK 主表 2209 条** param4 有 36 个取值（0.0..2.5）、param0 恒 0.0；
   不给规则的实质依据是「三条 apply 路径与资格门控都不读取」，不是取值本身。README／verify／交接同步。
4. **增量口径对应**：`increment.json` 增 `new_answers_summary_caliber`＝5730，并拆出
   standalone 2862 ＋ children 2868，说明 summary 按「存储记录」计数（子效果记录按父记录各计一次），
   与全局唯一 2869 并列不矛盾（与审查数字逐项一致）。
5. **页面标题**：改 `profiles.py` 的 `<title>`／`<h1>` 为当前口径并重建 HTML（未手改），
   交付物内已无「P1 首批」；真实浏览器确认 title／h1 与页头统计。

**对账**：修正前先备份 `records.jsonl`／`summary.json`（`work/character_skills_p2b2/fix_reconcile/`）。
索引修正后 type8/26 答案**逐行相同**（2862 行，键＝记录／字段／原值／数量类型／状态／证据范围，
哈希 `204780159d8fa873` 前后一致），summary 三项数字不变；第 2 项为**文本变更 1293 行**，
原值／类型／状态／范围零变化。

**回归（默认 GBK）**：`skilllist_types.py` 22/22、`verify_p1.py` **74/74**、
`crosscheck_raw.py` A–H `overall_ok=True`、DOM P2 **19/19** / P1 8/8、真实浏览器核对通过、
九个生成器 ＋ query 全部 exit 0、stderr 0 字节。

## 最近更新

2026-10-17：第 0 项文字修正 → 原生勘察（三条 apply 路径 switch、type8/26 分支、type67/1059 分支、
受影响角色复算 868/707/598/432）→ 落盘 `skilllist_types.py` ＋ `rules.py` 新规则来源 →
重建 profiles/gaps 并核对增量 → 扩展 verify（71/71）与 crosscheck（A–H）→ DOM 15/15 ＋ 真实浏览器 →
GBK 九入口回归 → 收尾（README §3.2、任务记录、`P2B2_HANDOFF.md`、HANDOFF/STATUS 本线数字）
→ **p2b2 第三方审查（带明确限制通过）→ 5 项整改：索引中性桶修正＋四处文字口径 → 对账（type8/26 答案
逐行零变化）→ 回归 74/74／A–H／19-8／真实浏览器 → 整改记录 `RECTIFICATION.md` 交回复验**。
下一步：等复验结论；通过前不开第 3 批。
