# 任务卡：40to59 cohort 正式生成实施（角色技能页主线）

- 日期：2026-10-20
- 负责人：GLM 5.3 Flash（40to59实施统计员，动态工作流子代理）
- 状态：机器生成完成并复核通过（290/290）；人工核读未开始
- 上游口径：`output/character_skills/r2_preparation/README.md`（报告/队列/续跑口径；队列政策已更新：每个有实际行的 configured skill 至少 1 行入队＋每卡≥10 行下限）

## 目标

对冻结名册 40to59 cohort（40–59旧描述，290张卡，含30236基线卡）执行一次正式生成（`--execute --resume`），核对完成度与 receipt，统计四联指标，记录失败与体积，确认 NOT_REVIEWED 审查队列状态。

## 允许写入路径

- `output/character_skills/pages/`（含 `_batch/`）
- 本任务卡 `docs/tasks/20261020-character-skills-40to59-implement.md`

只读：旧P3、profiles、r2_preparation、原始输入、旧审查报告、根HANDOFF/STATUS、character-skills-progress.md、pages_versions。

## 执行情况

- 主持侧已运行一次正式生成：exitCode=0，reused=0，failed=0。
- run 目录：`output/character_skills/pages/_batch/40to59/runs/20261019T164735760239Z-145ceb4b/`
- 因 exitCode=0 且 failed=0，按任务要求**未触发续跑**（0次 resume，上限2次）。
- 本轮全部核查为只读统计，未重复生成、未改游戏原值、未 git 暂存/提交。

## 结果

- completed/expected = 290/290，cohort_complete=true，requested/requested_completed=290/290，subset=false。290/290 全部成功，可称 cohort 完成（**机器生成口径，非人工验收**）。
- receipt：290张 `output/character_skills/pages/<cid>/receipt.json` 均 status=SUCCESS 且 signature=`9501343f1e77bff993753b0928566fcede9ec6fdee355251373a0f16dd709b2b`、run_id 与本 run 一致（290/290，本轮实际执行核对脚本）。
- 产物哈希：290卡×2文件（card.json、index.html）按 receipt 记录逐一 SHA-256 核对，580/580 一致（本轮实际执行）。
- 依赖哈希：29/29 数据依赖（signatures.json `data_dependencies`）逐项重算 SHA-256 与 run 快照一致，dependency_signature=`4029ad13d86c85cdc94bf100ed484f129074af8dc178af465e6fa50537986bac` 重算未变（本轮实际执行，复用 `card_page_batch.data_paths`）。
- unresolved_latest_failures=0；pending_cids=0；stale_or_invalid_cids=0（cohort_report）。campaign 快照：ge60 MATCHING_SIGNATURE_SNAPSHOT 34/34（同签名 `9501343f…`），40to59 MATCHING_SIGNATURE_SNAPSHOT 290/290，20to39/remaining NOT_GENERATED；无 STALE_SIGNATURE 条目。
- manifest_sha256=`032e6eea5431c6a49246a77be6d4fc7e21606f1f9b16d9c99b45f2bf31f44bda`；source_signature=`5d06b4dbf49b98645e1cd2be25ed9ff30bb02acd6d706dcf8f9fe0538aa4b1a8`。

### 四联指标（N_all=14221行，290卡合计；290卡 card.json 行数独立求和与 cohort 报告一致：A 6127＋C 8094=14221）

| 指标 | 数量/分母 | 率 |
|---|---|---|
| A率（数值/公式行率，**不是已解释率**） | 6127/14221 | 43.1% |
| 整行确认率 | 43/14221 | 0.3% |
| 原文A | 6109/14221 | 43.0% |
| C仅未知 | 8094/14221 | 56.9% |

- N_all/E/N_num = 14221/0/14221；B=0；部分A=6127（partial_A）。
- A中整行未知 6084/6127（99.3%）；整行推断 0/14221。
- 整行证据（evidence_cross，按row_class）：A 确认43/推断0/未知6084；B 全0；C 确认0/推断0/未知8094。
- 链新增：chain新A行0、新增行内数值0（290卡statistics求和）。
- 30236基线卡复核：整行确认43/58全部来自30236（old_confirmed=31；A 46/58，C 12/58），与 cohort 汇总43一致，非零，口径通过。
- 未知原因分类（行可携带多条原因；按 unknown_reasons 组合去重，共14220行携带≥1条，仅1行无）：
  - 3817行：原文未提供数值＋无适用已确认证据
  - 3361行：上述＋旧关键词候选未作为答案（不排除对象/效果错配）
  - 2685行：str0目标规则已在来源层复用＋原文数字仅确认原文不猜参数对应
  - 2372行：原文数字仅确认原文（A行）
  - 870行：原文数字仅确认原文＋旧候选未作答案
  - 802行：str0规则已复用＋原文未提供数值＋无适用已确认证据
  - 157行：原文数字仅确认原文＋英雄技引用未证运行时装载
  - 114行：原文未提供数值＋无适用已确认证据＋英雄技引用未证运行时装载
  - 32行：仅旧候选未作答案；10行：仅str0规则已复用（上述零散行主要为整行确认行携带的残留备注）
- 实施状态：技能候选晋级层与一般机制层均未启用（有意保守边界）；B=0表示无经实现入页的新增机制，不代表原数据不存在机制；基础职业名称沿用名册推断映射，与技能候选层分开标注。

### 输出体积与墙钟

- 290卡目录（card.json+index.html+receipt.json）：591.87 MiB / 870文件（平均约2.09 MiB/卡）。
- `_batch/40to59/`：20.70 MiB / 592文件，其中本次run目录 20.64 MiB / 301文件（audit_queue.json 5.73MB、campaign_audit_queue.json 6.49MB、transactions暂存 7.57MiB、cohort_report.json 0.83MB）；card_latest 指针 0.06 MiB。
- 生成耗时（报告记录）：41.34秒（不含人工阅读）。
- run 目录时间戳：20261019T164735760239Z（UTC）≈ 本地 2026-10-20 00:47:35。
- 统计任务墙钟：开始 2026-10-20 00:48:27，结束 2026-10-20 00:52:35 前后（只读统计+任务卡）。

## 失败

无（failed=0，unresolved_latest_failures=0，无 INVALID receipt，无 STALE 签名）。

## 审查队列（NOT_REVIEWED，不等于已验收）

- `audit_queue.json` 与 `campaign_audit_queue.json`：4954行（290卡，每卡14–21行，中位17行，全部≥10行下限），review_status 全部 NOT_REVIEWED，decision/reviewer 均空。
- 行类分布：A 2842行、C 2112行。
- 技能覆盖率：290/290卡全覆盖——每卡所有有实际行的 configured skill 至少1行入队（本轮按 290卡 card.json row_id 技能前缀与队列逐一比对，1905个技能组，缺失0）。
- campaign_report：audited=0，review_required_cards=790，queue_cards=324（ge60 340行/34卡＋本cohort 4954行/290卡），campaign_complete=false（2236张中完成324张机器生成）。
- 明确：仅生成队列/统计不算核读完成；NOT_REVIEWED 绝不表示已验收。逐行人工核读由独立版本化审查目录承担。

## 下一步

1. 主持调度独立审查，对5294行（ge60 340＋40to59 4954）审计队列逐行核读（记录真实阅读时长，更新剩余验收估计）。
2. 按既定顺序继续 cohort：20to39（436）→remaining（1476），命令同 README 全量入口加 `--execute --resume`。
3. 760复杂卡＋固定30卡核读集合欠账持续对账；不在本任务内启动。

## 追加：R-02 数据模型说明与 30236 confirmed 行回归自检（2026-10-20）

### R-02：pages 数据模型说明已写入

- 新增 `output/character_skills/pages/README.md`（此前该目录无 README），内容基于 30236 新旧 card.json 逐层实测与 pages/ 全量扫描，非凭记忆书写。要点：
  - `schema_version` 恒为字符串常量 `"card-page-pilot-1"`（`card_page_data.py:635`），polish 轮未升号，不能据此做封闭校验；
  - `answers[].quantity_kind` 为显示用复合标签：pages/ 已生成 330 张 card.json 全量扫描去重 141 种取值（含 `/` 复合标签 57 种、非复合 84 种；30236 单卡 53 种）；下游必须按文本处理，不得当封闭枚举或分组键（同一量语义可带不同对象前缀）；
  - 标签成分全部来自同句原文逐字短语：`original_numbers()`/`attribute_role()`/`dimension_labels()`（`card_page_data.py:91/150/187`，R-01/G-07 边界）；
  - 数值语义以 `raw_value`/`unit` 为准，`value`/`quantity_kind`/`note` 仅显示层；
  - `original_numeric_items[]`（审查口径的 "numeric_items"）中 `literal`=逐字原文、`normalized_literal`=NFKC 归一（`_raw_map()` 逐字符映射可回切，G-09）；旧样本版多数条目 `normalized_literal` 为 null，正式版填充；
  - `sources.source_anomalies` 为 polish 新增键（旧样本版 30236 卡无此键），当前仅 cid 204 一条登记（`SOURCE_ANOMALIES`，`card_page_data.py:409`）；
  - G-15 队列政策：每卡≥10行（不足全列）＋每个有实际行的 configured skill 至少 1 个不同 row_id（`card_page_batch.py:25-38`），NOT_REVIEWED≠已验收。

### 30236 confirmed 行回归自检（实施侧）

- 命令：`.venv\Scripts\python.exe -B work/character_skills_pages_r02_regression/r30236_confirmed_regression.py`（本轮实际执行；脚本与完整结果 `regression_result.json` 在同目录）。
- 对比对象：旧 `output/character_skills/r2_preparation/pages/30236/card.json`（11张样本版旧生成器）↔ 新 `output/character_skills/pages/30236/card.json`。
- **结论：整行确认行（evidence=确认）43/43 全部匹配，零变化通过**：
  - `japanese`：43行全部逐字一致（0差异）；
  - 行级 `evidence`：43行全部仍为"确认"（0变化）；
  - `raw_value`：按 (raw_value, unit) 多重集口径逐行比对，0差异；
  - source 指针：行级与答案级全部 `record_key`/`json_pointer` 集合，0差异。
- **行集合差异：0**。新旧两版均为 58 行、row_id 集合完全一致；确认行集合 43↔43 完全一致。审查口径"旧387行"是 11 张样本版整包分母（`r2_preparation/README.md` A 185/387、整行确认 47/387），其中 30236 占 58 行；40to59 正式版 30236 行数与样本版一致，差异不在行数，而在 11 张样本版与 290 卡正式版的**队列/标签政策**（样本版未启用复合标签与 normalized_literal 填充、无 source_anomalies 键）。
- **允许的显示层差异（逐项列出，共 25 行，数值/原文/证据/指针零影响）**：
  - 全部 25 行：`original_numeric_items[].normalized_literal` 由旧版 null 改为正式版填充（如 `1つ`/`32%`），`value`/`unit`/`literal` 三者逐行一致；
  - 其中 5 行另发生 `quantity_kind`/`value` 文案细化，均为 G-04/G-07 政策内：`数量：1つ`→`获得数量：1つ`（skillid_2_-lvorder1-f5）、`数量：1つ`→`所需玛那减少：1つ`（pattern1-lvorder1-f3）、`效果量百分比：60%/10%`→`味方全体/攻击力效果量百分比：60%`＋`攻击力效果量百分比：10%`（leader-f0）、同上 3%/2%（leader-sympathy-f0）、`数量：0マナ/1つ`→`发动费用：0マナ`＋`获得数量：1つ`（pattern2-lvorder2-f3）。
- 边界：本轮为只读对比，未改动任何产物；回归按需求口径覆盖 30236 单卡整行确认行，不代表 290 卡全量已复核（其余 289 卡未经本轮确认行比对）。

## 追加：R2 独立审查（REQUEST_CHANGES）修复轮次（2026-10-20）

- 审查输入：`output/character_skills/review/40to59_20261020_deepseek/`（REPORT.md、issues.jsonl R-01…R-12、ledger.jsonl 4954 行）。本轮按修复指令只改生成器并重建两 cohort，未手改任何 HTML/card.json，未开 native，未启用候选晋级/推断层。

### 修复内容（生成器：scripts/character_skills/card_page_data.py、card_page_render.py）

- **R-01（High，已修）**：`build_card` 整行关联判定由 `any(答案 association==确认)` 改为 `answers 非空且 all(确认)`；页面 intro 四联定义文案同步（card_page_render.py）。整行确认＝该行全部答案的字段关联均为「确认」；任一答案关联未知（含全部原文数字答案）即整行未知，同行不再出现「字段关联：确认」与「字段关联未证」并存的矛盾 pill。
  - **口径更正（全局记录）**：30236 整行确认 43→**18**（25 行含关联未知答案改判未知，逐行清单见 changes_40to59.jsonl row_evidence_changed，与审查 R-01 row_ids 完全一致）；ge60 整行确认保持 0。旧 R2 样本版「47/387」为历史「任一确认」口径，旧目录不改；29/2020/5023 等样本卡待 remaining cohort 生成时按新口径重建。
- **R-02（Medium，已修）**：`NUM_UNITS` 增加计数单位 `羽/台/本`；新增「ダメージをN減少」固定减少量提取（role=固定减少量，unit=ダメージ固定量，display=「ダメージをN減少」）；`まで` 上限单位扩到 体/羽/台/本（→数量上限）；「この効果で0マナにはならない」→费用下限（R-04）；「マナを1つも所持していない」→条件阈值（未持有玛那）（R-05）。
  - 40to59：38 行 C→A（与审查 R-02 row_ids 完全一致），A 6127→**6165**、C 8094→**8056**、原文A 6109→**6147**，N_all 14221 不变；38 行假原因「原文未提供该效果数值」消失（复核 0 残留）。ge60：无同模式行（实测 0 行 answer 集变化），A/C/original_A 均不变。
- **R-03（Medium，已修）**：`敵陣にいると`／`同じ敵を攻撃すると` 中的「敵」在对象搜索前遮蔽并登记为同句条件标签；12 行「敌方/攻击力效果量百分比」→「攻击力效果量百分比（条件：敵陣にいると / 2人以上で同じ敵を攻撃すると）」。全库残留扫描：条件型「敌方」误标 0；真实敌方减益（20436/30241/30304/6340「攻撃した敵の…下がる」4 行组）的 `敌方/` 前缀保留。
- **R-06（Low，部分修复，只补同句逐字有据）**：新增逐字短语——`メインパーティの<…>所属`（主队所属 85 行组）、1st角色（10001/20521/20115 等 16 行组，含「1stキャラクターに」付与对象不因条件切点丢失）、`天魔に与えるダメージ`（7611，2 行）、多值行逐数值窗口＋`味方の必殺技の威力` 遮蔽泛化（10212 等）、`経験値/ゴールド`（220）、`状態異常の敵に与えるダメージ`（20113 等）、`遠距離通常攻撃のダメージ`（20436 等）。其余无逐字短语支撑的泛化行保留原样（无据不补），未修数量待后续审查逐条核对。
- **R-07（Low，已修）**：页头称号 missing/null 时用 `display_value`（30001 显示「外部/网站维护」），不再渲染空 `<p class="title">`。
- **R-08（Low，已修）**：card.json `sources.baseline_evidence_roots` 声明 30236 基线 evidence 相对路径解析根为 `output/card_comparison_cid30236/`（本轮实测：45 种 evidence 字符串中路径型 token 306 个全部可由该根解析，含 `../boss_chain/…` 同层引用；`skill43023600.text` 等 12 个为说明性引用非文件指针）。
- **R-12（Low，保留＋登记）**：20438 SA 标题行「神仙セリーヌ_神仙の力」保留计入 N_all/C——内部标签排除规则是整技能文本单行且匹配内部前缀/含 SA_（cid89 据此整技能排除）；20438 该技能含句读正文行「《玲瓏璧》のサブアビリティ。」不满足整技能排除，标题行无独立逐字排除依据，排除属推断，故不修而登记：card.json `sources.denominator_notes`（N_all 14221 不变）。
- R-09/R-10/R-11：注记/范围项，不改代码（R-09 partial_A 口径、R-10「2直線範囲」、R-11 队列抽样范围见审查报告）。

### 重建与复核（本轮实际执行）

- 命令（仓库根）：
  - `.venv/Scripts/python.exe -B scripts/character_skills/card_page_batch.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --cohort ge60 --output output/character_skills/pages --execute --resume`
  - 同命令 `--cohort 40to59`
- 新 run：ge60 `_batch/ge60/runs/20261019T175325949256Z-5ac350e9/`（34/34，reused=0，failed=0）；40to59 `_batch/40to59/runs/20261019T175337285159Z-4085a36d/`（290/290，reused=0，failed=0）。
- 新签名：`9b8f43b3913a2290407232582a7bad29d7ee8493947fc9b8f8b147376748b15b`（source_signature `3e358747e8044d5259b56c1e8ae28e10a8b6b0cfc6f4c9899608ee9a800e7183` 因生成器代码变化更新；dependency_signature `4029ad13…` 不变）；两 cohort 签名一致；旧 receipt 按签名 STALE 属预期，rebuild 后 stale_or_invalid=0、pending=0、unresolved_latest_failures=0。
- receipt：324/324 SUCCESS 且签名一致；产物哈希 324×2=648 文件逐一 SHA-256 与 receipt 一致；29/29 数据依赖哈希未变。
- campaign：ge60/40to59 MATCHING_SIGNATURE_SNAPSHOT（34/34、290/290），20to39/remaining NOT_GENERATED；completed 324/2236；audited=0（队列全部 NOT_REVIEWED）。

### 四联指标（old→new；数量+分母）

| 指标 | 40to59 old | 40to59 new | ge60 old | ge60 new |
|---|---|---|---|---|
| A率 | 6127/14221（43.1%） | **6165/14221（43.4%）** | 1005/2211（45.5%） | 1005/2211（45.5%，不变） |
| 整行确认率 | 43/14221（0.3%，旧口径） | **18/14221（0.13%，新口径）** | 0/2211 | 0/2211（不变） |
| 原文A | 6109/14221（43.0%） | **6147/14221（43.2%）** | 1005/2211 | 1005/2211（不变） |
| C仅未知 | 8094/14221（56.9%） | **8056/14221（56.6%）** | 1206/2211 | 1206/2211（不变） |

- N_all/E/N_num=14221/0/14221（40to59）、2211/0/2211（ge60）均不变；B=0；整行推断=0。
- 40to59 evidence_cross A：确认 43→18、未知 6084→6147（+25 改判＋38 新 A 行）；C 未知 8094→8056。
- 30236 单卡回归：58 行集合、row_id 集合与旧版完全一致；A 46/58、C 12/58、original_A 28 不变；整行确认 43→18。

### old→new 逐行变化清单（work/40to59_fix_20261020/）

- `old_rows.jsonl`（重建前 16432 行快照＝两 cohort 全部行）、`old_state.json`/`old_basic.jsonl`（签名/称号快照）。
- `changes_40to59.jsonl`：行增删 0；row_class C→A 38（=R-02 row_ids 完全一致）；答案集新增 38 行（全部为新增答案、无删除）；numeric_items 38 行全部只增不丢（literal/value/unit 多重集）；answer 标签修改 413 行（raw_value 多重集逐行比对全部不变——数值零变化）；row_evidence 确认→未知 25 行（=R-01 row_ids 完全一致，全部在 30236）。
- `changes_ge60.jsonl`：行增删 0、class/evidence/答案集变化 0；仅 45 行标签修改（raw_value 多重集全部不变；示例：自身/味方全体前缀补全）。
- 结论：**无任何行新增/删除、无任何 raw_value/unit 变化、无数值项丢失**；43→18 的 25 行、C→A 的 38 行与审查清单逐行核对一致。

### 审计队列

- 行数不变：40to59 4954（A 2855/C 2099，+13 C→A 翻转）、ge60 671；全部 NOT_REVIEWED。
- 40to59 队列内 3 行替换（30103/10213/20704 各 1 行）：choose_samples 的 A/B/C 覆盖槽取「该类第一行」，原首 C 行改判 A 后顺延到下一 C 行，属确定性策略行为；每技能≥1行＋每卡≥10行 政策不变（G-15）。
- R-02 15 行、R-03 12 行、R-01 12 行在新队列中的入队数与审查期一致。

### 保留与下一步

- 保留未修：R-06 其余泛化标签（无同句逐字短语支撑，无据不补）；R-12（保留＋登记）；R-09/R-10/R-11（注记项）。
- 下一步：主持将新产物/新队列送独立复审（重点是 R-01/R-02/R-03 修复项与 25+38 行变化清单）；20to39/remaining 按 README 全量入口排程，29/2020/5023 等样本卡届时按新口径重建。
