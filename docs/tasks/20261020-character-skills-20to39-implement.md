# 任务卡：20to39 cohort 正式生成实施（角色技能页主线）

- 日期：2026-10-20
- 负责人：GLM 5.3 Flash（20to39实施统计员，动态工作流子代理）
- 状态：机器生成完成并复核通过（436/436）；人工核读未开始
- 上游口径：`output/character_skills/r2_preparation/README.md` 与 `output/character_skills/pages/README.md`（数据模型、整行确认口径＝全部答案关联均为确认、G-15 队列政策每技能≥1行＋每卡≥10行）

## 目标

对冻结名册 20to39 cohort（20–39旧描述，436张卡，不含30236）执行一次正式生成（`--execute --resume`），核对完成度与 receipt，统计四联指标，复核17行整行确认来源，记录失败与体积，确认 NOT_REVIEWED 审查队列状态。

## 允许写入路径

- `output/character_skills/pages/`（含 `_batch/`）
- 本任务卡 `docs/tasks/20261020-character-skills-20to39-implement.md`

只读：旧P3、profiles、r2_preparation、原始输入、旧审查报告、根HANDOFF/STATUS、character-skills-progress.md、pages_versions。

## 执行情况

- 主持侧已运行一次正式生成：exitCode=0，reused=0，failed=0。
- run 目录：`output/character_skills/pages/_batch/20to39/runs/20261019T233249882056Z-9857e9b9/`
- 因 exitCode=0 且 failed=0，按任务要求**未触发续跑**（0次 resume，上限2次）。
- 本轮全部核查为只读统计，未重复生成、未改游戏原值、未 git 暂存/提交。
- 统计会话墙钟：2026-10-20T07:33:32+0800 起、2026-10-20T07:35:58+0800 止；cohort 生成自身用时 31.96 秒（cohort_report `seconds`）。

## 结果

- completed/expected = 436/436，cohort_complete=true，requested/requested_completed=436/436，subset=false。436/436 全部成功，可称 cohort 完成（**机器生成口径，非人工验收**）。
- receipt：436张 `output/character_skills/pages/<cid>/receipt.json` 均 status=SUCCESS 且 signature=`9b8f43b3913a2290407232582a7bad29d7ee8493947fc9b8f8b147376748b15b`、run_id=`20261019T233249882056Z-9857e9b9`（436/436，本轮实际执行核对）。
- 产物哈希：436卡×2文件（card.json、index.html）按 receipt `files` 记录逐一 SHA-256 核对，872/872 一致（本轮实际执行）。
- 依赖哈希：29/29 数据依赖（`signatures.json` `data_dependencies`）逐项重算 SHA-256 与 run 快照一致，dependency_signature=`4029ad13d86c85cdc94bf100ed484f129074af8dc178af465e6fa50537986bac` 重算未变（本轮实际执行，复用 `scripts/character_skills/card_page_dependencies.py` `data_paths`）。
- unresolved_latest_failures=0；pending_cids=0；stale_or_invalid_cids=0（cohort_report）。campaign 快照：ge60 MATCHING_SIGNATURE_SNAPSHOT 34/34、40to59 MATCHING_SIGNATURE_SNAPSHOT 290/290、20to39 MATCHING_SIGNATURE_SNAPSHOT 436/436；remaining NOT_GENERATED 0/1476；无 STALE 条目。
- manifest_sha256=`032e6eea5431c6a49246a77be6d4fc7e21606f1f9b16d9c99b45f2bf31f44bda`；source_signature=`3e358747e8044d5259b56c1e8ae28e10a8b6b0cfc6f4c9899608ee9a800e7183`。

### 四联指标（N_all=12032行，436卡合计）

| 指标 | 数量/分母 | 率 |
|---|---|---|
| A率（数值/公式行率，**不是已解释率**） | 3867/12032 | 32.1% |
| 整行确认率 | 17/12032 | 0.14% |
| 原文A | 3850/12032 | 32.0% |
| C仅未知 | 8165/12032 | 67.9% |

- N_all/E/N_num = 12032/0/12032；B = 0（技能描述推断层暂不启用：候选晋级未实现，有意保守边界；0不代表全库无hint，B0表示无经实现入页的新增机制）。
- A中整行未知 3850/3867（99.6%）；整行推断 0/12032；部分A（partial_A）3839。
- 未知原因分类：C 8165行为"仅未知"，主因是技能描述推断层（候选晋级/一般机制择句）未实现入页，并非原数据无机制；基础职业名称沿用名册推断映射，与技能候选层分开标注（cohort_report `summary.implementation_status`）。

### 17行整行确认来源复核（任务预期为0，实际17，已逐行复核）

任务书预期"本cohort不含30236，整行确认预期为0"，实际整行确认 17/12032。逐行复核结论（本轮实际扫描 436 张 card.json 并逐行核对答案来源）：17行全部为**能力（ability）行**（row_id 形如 `<cid>-ability-ability-skillid_3_-lvorder2-f0`，row_class=A），句式统一为「戦場に自身以外の<職業/所属>の味方がいると自身の攻撃力と…が上がる」，涉及 cid：328、2219、2302、2303、4225、6317、6323、6326、7641、7653、8228、9230、9234、11223、12222、12224、13205。48个答案全部为 `numeric_source='规则'`、`numeric_evidence='确认'`、`association_evidence='确认'`、`evidence_scope='BY_TYPE_EXTRAPOLATED'`、rule_key 均为 `skilllist|67|/paramN`，来源指向 `APK/_mdSkill.json#/skilllist/<id>`；绑定模板 45 答案为 `p3b9_type67_conditional_self_stats`（`scripts/character_skills/p3b9_bindings.py:97`）、3 答案为 `p3b10_type67_weapon_or_job_self_stats`（`scripts/character_skills/p3b10_bindings.py`），均为**已冻结 P3B9/P3B10 队列的既有结构规则证据**（binding status「已确认（冻结队列的结构规则对应）」，native_evidence 文件 `output/character_skills/description_bindings/p3b9_batch/native_evidence.json` 存在），不属于本轮暂未启用的技能描述候选晋级层。即：预期0的判断依据（40to59 的整行确认全部来自30236基线）未覆盖 type67 能力规则冻结队列在本 cohort 的命中，属预期口径遗漏而非数据异常；未发现来源可疑行。

### 审查队列（G-15）

- `runs/20261019T233249882056Z-9857e9b9/audit_queue.json`：**5626行**、436卡全覆盖，每卡 11–20 行（最小11：cid 203；最大20：cid 9236；中位12）。row_class 分布 A 2402 / C 3224。
- 技能覆盖：436卡中有实际行的 configured skill 共 **3797 个，全部≥1行入队（0个未覆盖）**（本轮实际逐卡核对）。
- 队列行全部 `review_status='NOT_REVIEWED'`。**NOT_REVIEWED 仅表示未进入审查流程，不等于已验收或已通过**；审查结论由独立版本化审查目录记录，仅生成队列/统计不算核读完成。campaign 层 review_required_cards=790、queue_cards=760、audited=0。

## Campaign 层口径

- 复杂760卡至此全部生成：ge60 34/34＋40to59 290/290＋20to39 436/436 = **760/2236**（campaign_report `completed/expected`，campaign_complete=false）；remaining cohort（其余1476张）NOT_GENERATED。
- campaign coverage：N_all=28464、E=0、N_num=28464、A=11037、B=0、C=17427、原文A=11002、整行确认35（30236基线18＋本cohort type67规则17）；A率 11037/28464=38.8%（数值/公式行率，不是已解释率）。

## 输出体积

- 436个 `pages/<cid>/` 目录合计 515.14 MB；`_batch/20to39/` 合计 21.76 MB；本轮新增合计约 536.90 MB。

## 失败

- 无。failed=0，unresolved_latest_failures=[]，续跑未触发（0/2次）。

## 下一步

- remaining cohort（1476张）由主持按已确认顺序调度；本任务不自动推进。
- 20to39 的 5626 行 NOT_REVIEWED 队列与既有 40to59 4954 行、ge60 671 行一并等待独立版本化审查；整行确认17行的复核结论可作审查输入，但不替代逐行人工核读。

---

# 修复轮次 2（2026-10-20）：DeepSeek 20to39 审查 REQUEST_CHANGES 后修复

- 审查输入：`output/character_skills/review/20to39_20261020_deepseek/`（REPORT.md、issues.jsonl；1 High、6 Medium、13 Low、3 Note）。
- 本轮只改生成器（`card_page_data.py`、`card_page_render.py`、`card_page_policy.py`、`card_page_basic.py`、`card_page_batch.py`），未手改任何 HTML/card.json；未 git 暂存/提交。
- 执行命令（三 cohort 依序，均在仓库根）：`./.venv/Scripts/python.exe -B scripts/character_skills/card_page_batch.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --cohort <ge60|40to59|20to39> --output output/character_skills/pages --execute --resume`。三次全部 failed=0、reused=0、cohort_complete=true。
- 新 run 目录：ge60 `20261020T001431675807Z-aa629f69`、40to59 `20261020T001444000598Z-20d940d0`、20to39 `20261020T001525281381Z-40959198`；三 cohort 新签名一致 `a466037d0c0d553a…`（旧 receipt 按签名 STALE 属预期）；dependency_signature 不变。

## 逐项状态

- **H-01（已修，只改呈现不降级）**：BY_TYPE_EXTRAPOLATED 在行级「整行证据」pill、A 行「数值」pill、值行证据头标注「确认（类型外推）」（`card_page_render.py` `scope_label()`）；四联拆分新增 `coverage.confirmed_rows_by_scope` / `summary.whole_row_confirmed_scopes`；页面 intro 与 `pages/README.md` §7/§10 同步「整行确认分两类」口径（记录级 REVIEWED_RECORD=30236 基线 18 行 vs 类型外推=本 cohort 17 行）。实测 17/17 行显示「确认（类型外推）」、ge60+40to59 的 18 行确认仍显示「确认」无限定（本轮实际执行核对）。
- **M-01（已修）**：「N回復」→`回复量`（unit=HP，unit_raw=回）；20 行 value「次数：300回」→「回复量：300HP」，逐行回原文核对为 HP 固定回复量；另覆盖 40to59 的 2046 四档（同型）。
- **M-02（已修）**：「状態異常の敵がいると」登记条件并遮蔽；13203 5 行改「攻击力效果量百分比（条件：…）」；同型 20411 5 行一并修正（审查未列，逐字同模式）。
- **M-03（已修）**：20219 5 行 10 答案——1st 不再作效果对象前缀，改条件注记「1stキャラクターに付与」；效果标签「敌方/攻击力」「敌方/防御力」（授予侧/效果对象已按原文「攻撃した敵の」逐字理清）。**M-03B（已修）**：20219 heroic f2「敵陣の奥に行く程」按 R-03 遮蔽＋条件登记。
- **M-04（已修）**：326/20435 各 3 行改「对敌伤害（基数：自身最大HP）效果量百分比」。
- **M-05（已修）**：31 行全部补「回复量效果量百分比」标签并带逐字对象（味方全体/自身/戦場にいる味方等）；「与えたダメージのN%、自身のHPが回復」对象在数字后，按逐字就近补。
- **Low 逐条**：L-01 已修（敌方继承；20to39 7 行=20329/20434+20219、40to59 4 行）；L-02 已修（20 行；40to59 85 行组同步）；L-03 已修（付与注记，6 行含 5264 f3、20417×5、20115）；L-04 **保留**（113 行需新建次数/数量类逐值对象推断机制，跨 cohort 数百行，按审查报告建议留下一 polish 轮）；L-05 部分修（固定减少量 10 行改纯中文值行；条件短语 181 行保留逐字原文，翻译失据，RR-02 债务维持）；L-06 已修（统一「1st角色」，重建后全库 quantity_kind 0 处「1stキャラクター」）；L-07 **保留**（6 行 SA 内部标签无逐字排除依据，不扩 cid89 规则改分母，待冻结审查依据）；L-08 部分修（耐久次数 205 行、受击触发次数 15 行；「さらにNつ減る」10 行片段内无マナ逐字依据，保留 `数量`）；L-09 已修注记（11 行，判定/数值不变）；L-10 已修措辞（N直線 范围几何注记）；L-11 已修（省略号后数字可提取；8424 2 行补「3つ（随机效果数，非效果量）」，30326 同模式加注）；L-12 已修（28 行绑定条件提为行级可见块）；L-13 已修（范围合并，20to39 8 行+40to59 20437 2 行）。
- **S-01（已修）**：20001 称号原值为空字符串（raw_state=present），R-07 只覆盖 missing/null 故未命中；现按 R-07 同法显示「外部/网站维护」（字段与页头一致）。**S-02/S-03**：注记项，不改代码（按审查报告口径维持）。

## 复核（本轮实际执行）

- receipt：760/760（34+290+436）status=SUCCESS 且签名=新签名；产物哈希 760×2=1520 个逐一核对一致；数据依赖 29/29 SHA-256 未变、`data_paths()` 集合一致；三 cohort stale_or_invalid=0、pending=0、failed=0；campaign 快照 ge60/40to59/20to39 均 MATCHING_SIGNATURE_SNAPSHOT、remaining NOT_GENERATED 0/1476。
- 审计队列：三 cohort 行数与成员逐行不变（671/4954/5626，added=0 removed=0）。
- old→new 逐行对账（`work/20to39_fix_20261020/changes_<cohort>.jsonl` + `audit_changes.py`）：行集合增删 0、row_class 变化 0；答案变化行 ge60 19、40to59 273、20to39 218，全部归入上列修复类目（0 条 OTHER）；除 L-11 两行新增答案、L-13 十行两并一外，487 行 raw_value 多重集逐一相等（数值不变）；L-09 11 行仅注记。
- 四联指标三 cohort 全部不变：ge60 A 1005/2211、整行确认 0、原文A 1005、C 1206；40to59 6165/14221、18、6147、8056；20to39 3867/12032、17、3850、8165（口径拆分：40to59 record=18/by_type=0；20to39 record=0/by_type=17）。campaign N_all=28464、整行确认 35 不变，拆分 record 18 / by_type 17。
- 状态：本轮修复完成，机器复核通过；**仍非人工验收**，5626 行队列 NOT_REVIEWED 待独立版本化审查复审。
