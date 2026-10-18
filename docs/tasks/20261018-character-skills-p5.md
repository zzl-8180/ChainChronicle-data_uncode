# 任务记录：P2 第 5 批（复合分支 67／80／96／1036 原生研究）

- 任务标识：`20261018-character-skills-p5`
- 负责人／对话：本线实施对话（角色技能完整解读 P2 系列）
- 状态：**待针对性审查**（已实施、验证全绿，等待审查对话复验）
- 允许写入范围：`scripts/character_skills/`、`output/character_skills/`（本任务产物与 README／交接）、
  `work/p5_*`（本批快照与一次性插入脚本）、本文件
- 共享依赖：`work/protection/il2cpp_loader_seed1.bin`（原生镜像，只读）、
  `work/protection/metadata_aei_decoded.bin`（元数据，只读）、`output/character_skills/links/character_skills.jsonl`
- 未触碰：`review/` 历史报告、`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、
  `docs/tasks/character-skills-progress.md`（主持）、其他任务未提交文件

## 目标（逐项）

0. 审查观察：`crosscheck_raw.py` 的 J 区只核顶层 159 条新答案，children 513 条未覆盖 → 扩展到全量。
1. type 80／96／67 复合分支原生研究：追踪完整换算链（基数槽、计数如何参与、喂入哪个累加器、量纲与夹紧）。
2. 规则与缺证分界：换算链不闭环的类型保持缺证并写明缺段；67 不许只给槽位定位。
3. 弹性项：type 1036 的 `BattleParam+0x328` 计数身份。
4. 应用＋重建 profiles／gaps，报告覆盖增量与区分性样本。

## 关键做法

- **函数内可达性遍历**替代「扫一个 leaf 的窗口」：67／80／96 被编译合并进同一 worker，线性扫描看不到链。
  `reachable_body()` 跟两支、在路径循环尾/共享累加尾停止、`bl` 只记调用点；边界用 `func_bounds()` 取
  所属方法真实范围（防走进邻接函数）。
- **规则由分支重算后才产出**：`composite_rule_rows()` 要求「该字段是该分支真正读的槽」且「分支抵达累加器」，
  否则不出行；因此规则表本身写错也不会产出规则。
- **缺证如实保留**：96 攻击路径的系数在 param2／param3 之间由调用级标志 `[sp+0x18]` 选择（含义未定位）
  ⇒ 两槽都不给答案，缺段写进同类型规则行的 `limits` 与交接文档。
- **口径分列**：`mana_coeff_*`／`hyper_*` 是公式型答案（另乘运行时因子），阈值/选择码/上限是数值型答案；
  `rules.answer_for` 改为尊重转换器声明的 `answer_status`。

## 产物

| 产物 | 位置 |
|---|---|
| 换算链证据（20 条分支体＋helper 语义＋`hyperGauge` 身份） | `output/character_skills/skilllist_types/composite_chains.json` |
| 规则字典（+23 条复合规则） | `output/character_skills/skilllist_types/field_dictionary.json` |
| 增量报告（三口径＋可达角色＋迁移） | `output/character_skills/skilllist_types/composite_increment.json` |
| 逐类型证据（现含 80／96／1036） | `output/character_skills/skilllist_types/type_evidence.json` |
| 原生自检（40/40，含 6 项复合检查） | `output/character_skills/skilllist_types/native_checks.json` |
| 分支浏览器工具 | `scripts/character_skills/composite_branches.py`（`--brief` / `--write`） |
| 交叉核对（新增 K 区） | `output/character_skills/validation/crosscheck_raw.json` |
| 本批快照 | `work/p5_records_before.jsonl`、`work/p5_summary_before.json` |
| 交接 | `output/character_skills/P5_HANDOFF.md` |

## 关键数字

- 新增答案 **8979**（页求和）／**8979**（记录级）／**6305**（（表,记录,层,字段）去重）；
  按类型页求和 67→6643、80→2016、96→320、1036→0。
- 未解释字段 435881 → **426902**；规则答案 38862 → **47841**（唯一 38029 → 47008）。
- 可达角色 67→598、80→166、96→52（去重 742）；**97 个角色**由「仅未知」变为「部分」。
- 缺口字段级 5754 → 5736；断链 0。既有答案键 27440 个 0 丢失 0 变化。

## 验证

`verify_p1.py` 111/111、`crosscheck_raw.py` A–K `overall_ok`（H 4147／I 1067／J 672／K 6305 条）、
`skilllist_types.py` 40/40；默认 GBK 可运行；重跑全链 6 份关键产物 SHA-256 逐字节相同；真实浏览器核对
cid 3（67）与 cid 203（80）渲染。

## p2b5 审查整改（2026-10-18）

审查「带明确限制通过」＋4 项修正，已改完并交回复验：① 96 的 `int(param0)==0` 分支计数对象是
斯库拉普玛那（`GetCurrentScrapManaNum`，标志 0x20），条件与答案文本改为按记录自身 param0 选名词，
并新增原生检查与 crosscheck 钉死；② 96 上限槽语义更正为 `int(param1)<1` 不设上限；③ `hyperGauge`
身份证据改述为元数据字段表 `_hyperGauge`@0x328 ＋ 具名 getter（撤回 ctor 写入的旧说法）；
④ 交接规则计数更正为 19＋4。只动文本：96 的 320 条答案 raw／kind／unit／status 与渲染系数 0 变化，
全体数字口径不变。整改记录：`output/character_skills/P5_HANDOFF.md` §9 与审查目录 `RECTIFICATION.md`。

## 下一步

交针对性审查（重点样本见 `P5_HANDOFF.md` §6）。审查通过后候选：① 96 攻击路径系数槽的标志语义；
② 筛选位字典（iParam0／flag／param8）；③ 1059 UnionCount 的施加路径；④ `cAbility*Work..ctor` 字段归属。
