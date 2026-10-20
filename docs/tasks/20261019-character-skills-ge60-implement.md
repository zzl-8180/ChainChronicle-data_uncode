# 任务卡：ge60 cohort 正式生成实施（角色技能页主线）

- 日期：2026-10-19
- 负责人：GLM 5.3 Flash（ge60实施统计员，动态工作流子代理）
- 状态：polish 轮完成（2026-10-20：R-01 条件/所属/目标标签 + G-15 队列政策已实施并重建34/34，见文末 polish 轮记录；人工全行核读仍未开始）
- 上游口径：`output/character_skills/r2_preparation/README.md`（报告/队列/续跑口径、resume方法、NOT_REVIEWED含义）

## 目标

对冻结名册 ge60 cohort（≥60旧描述，34张卡）执行一次正式生成（`--execute --resume`），核对完成度与receipt，统计四联指标，记录失败与体积，确认NOT_REVIEWED审查队列状态。

## 允许写入路径

- `output/character_skills/pages/`（含 `_batch/`）
- 本任务卡 `docs/tasks/20261019-character-skills-ge60-implement.md`

只读：旧P3、profiles、r2_preparation、pages_versions、旧审查报告、根HANDOFF/STATUS。

## 执行情况

- 主持侧已运行一次正式生成：exitCode=0，reused=0，failed=0。
- run目录：`output/character_skills/pages/_batch/ge60/runs/20261019T153621609643Z-8de0300c/`
- 因 exitCode=0 且 failed=0，按任务要求**未触发续跑**（0次resume，上限2次）。
- 本轮全部核查为只读统计，未重复生成、未改游戏原值、未git暂存/提交。

## 结果

- completed/expected = 34/34，cohort_complete=true，requested/requested_completed=34/34，subset=false。34/34全部成功，可称cohort完成（机器生成口径，非人工验收）。
- receipt：34张 `output/character_skills/pages/<cid>/receipt.json` 均 status=SUCCESS 且 signature=`1839f97f611757eb43d5eb3a0234221023404106f43c4c043ddb9bfa324eeb74` 与 run 一致（34/34）。
- 产物哈希：34卡×2文件（card.json、index.html）按receipt记录逐一SHA-256核对，68/68一致（cid 204 抽查脚本 + 全量核对脚本均在本轮实际执行）。
- transactions：34条，各含 backup/new（旧三文件备份与回滚材料在位）。
- unresolved_latest_failures=0；pending_cids=0；stale_or_invalid_cids=0。

### 四联指标（N_all=2211行，34卡合计；每卡coverage求和与cohort报告一致）

| 指标 | 数量/分母 | 率 |
|---|---|---|
| A率（数值/公式行率，**不是已解释率**） | 1004/2211 | 45.4% |
| 整行确认率 | 0/2211 | 0% |
| 原文A | 1004/2211 | 45.4% |
| C仅未知 | 1207/2211 | 54.6% |

- N_all/E/N_num = 2211/0/2211；B=0；部分A=1004（partial_A）。
- A中整行未知 1004/1004；整行推断 0/2211。
- 整行证据（evidence_cross，按row_class）：A 确认0/推断0/未知1004；B 全0；C 确认0/推断0/未知1207。
- 链新增：chain新A行0、新增行内数值0（全部34卡statistics求和）。
- 未知原因分类（C/无答案行共1207行，按unknown_reasons组合去重计数）：
  - 497行：原文未提供数值＋无适用已确认证据
  - 431行：上述＋旧关键词候选未作为答案（不排除对象/效果错配）
  - 150行：上述＋英雄技引用沿用既有ID模式关联，未证明运行时装载和等级条件
  - 129行：str0目标规则已在来源层复用＋原文未提供数值＋无适用已确认证据
- 实施状态：技能候选晋级层与一般机制层均未启用（有意保守边界）；B=0表示无经实现入页的新增机制，不代表原数据不存在机制。

### 输出体积与墙钟

- 34卡目录（card.json+index.html+receipt.json）：82.87 MB / 102文件。
- `_batch/ge60/`（报告+队列+transactions）：8.69 MB，其中本次run目录 8.69 MB / 47文件。
- 生成耗时（报告记录）：4.66秒（单进程统计，不含人工阅读）。
- 统计任务墙钟：开始 2026-10-19T15:36:38Z，结束 2026-10-19T15:38:43Z（约2分钟，只读统计+任务卡）。

## 失败

无（failed=0，unresolved_latest_failures=0，无INVALID receipt）。

## 审查队列（NOT_REVIEWED，不等于已验收）

- `audit_queue.json` 与 `campaign_audit_queue.json`：340行（34卡，每卡10行），review_status 全部 NOT_REVIEWED，decision/reviewer 均空。
- campaign_report：audited=0，review_required_cards=790，campaign_complete=false（2236张中完成34张）。
- 明确：仅生成队列/统计不算核读完成；NOT_REVIEWED 绝不表示已审。逐行人工核读由独立版本化审查目录承担。

## 下一步

1. 主持调度独立R2审查，对340行 ge60 审计队列逐行核读（记录真实阅读时长，更新剩余验收估计）。
2. 按既定顺序继续 cohort：40to59（290）→20to39（436）→remaining（1476），命令同 README 全量入口加 `--execute --resume`。
3. 760复杂卡＋固定30卡核读集合欠账持续对账；不在本任务内启动。

---

## 修复轮（2026-10-20）：DeepSeek 独立审查 REQUEST_CHANGES 的 G-01…G-14

- 审查输入：`output/character_skills/review/ge60_20261019_deepseek/`（REPORT.md、issues.jsonl、ledger.jsonl、checks/）；结论 REQUEST_CHANGES：2 Medium（G-01、G-02）+ 12 Low + 1 Scope（G-15，流程问题，主持处理，本线不改队列逻辑）。
- 实施者：GLM 5.3 Flash（ge60缺陷修复员）；只改生成器 `scripts/character_skills/card_page_data.py`、`card_page_render.py`，未手改任何产物 HTML/card.json。
- 修复方式：全部通过生成器重建（`--execute --resume`），34 张 receipt 因生成器源码变化按新签名重建（预期行为）。

### 修复项状态（G-01…G-14）

| 项 | 状态 | 实现 |
|---|---|---|
| G-01 | 已修 | `NUM_UNITS` 单位表补「匹」；30110 f2 行 C→A，答案「数量：4匹」；「原文未提供该效果数值」假陈述消失（`original_numbers`，card_page_data.py:57-84 区域） |
| G-02 | 已修 | 新增「所持できるマナの数がNに増え」提取；354/6343/7689 三行补「数量：11（可持有玛那上限）」 |
| G-03 | 已修 | 「N回ダメージを受けるまで」→ role=受击次数上限（12行，含11231两处及同文其他档位） |
| G-04 | 已修 | 「Nマナで発動」→发动费用（27行）；「Nつ獲得」→获得数量（84行） |
| G-05 | 已修 | 「必要なマナがNつ減る」→所需玛那减少（42行，覆盖审查4行及同文档位） |
| G-06 | 已修 | 原文数字按 span 排序（HP→防御→移動→暴击与原文一致）；context 改按句读边界截取 |
| G-07 | 已修 | 一行内≥2个百分数时逐分句前文补属性/对象（73行）：如「自身/攻击力效果量百分比：350%」「必杀技威力效果量百分比：30%」「对人间伤害效果量百分比：15%」「1st角色/攻击力效果量百分比：2%」 |
| G-08 | 已修 | 时长单位显示统一为「秒」；item 保留 `unit_raw=秒間` 与 `display_note`，literal 保留原文「20秒間」（80行） |
| G-09 | 已修 | 逐字 NFKC 映射表：`literal`=逐字原文（「1％」「２人」），新增 `normalized_literal`，显示值用归一化（4206/7206 等含全角数字的行） |
| G-10 | 已修 | `SOURCE_ANOMALIES` 登记表：204 两处同文行登记源数据疑似笔误，页面忠实保留；写入 card.json `sources.source_anomalies`（页脚来源 details 可见） |
| G-11 | 已修 | 页面文案改为指向 `pages/_batch/<cohort>/latest.json` 所指运行目录的 cohort_report.md/audit_queue.json，并说明本目录仅含三文件（34/34 页） |
| G-12 | 已修 | 技能级 `association_evidence` 改为「确认·记录引用（不代表句内归属）」；`partial` 判定同步改用 startswith('确认')，行级证据不变 |
| G-13 | 已修 | context 改为按句读（。、，\n◆）对齐的边界窗口，不再出现「0上がり」「5%上がり」伪子串（全部 A 行的 numeric item context 重写；原16行问题行均消除） |
| G-14 | 已修 | 页面 intro 补「整行确认」「原文A」定义并链接 `../../r2_preparation/README.md`（34/34 页） |

### 新 run 与复核结果

- 新 run：`output/character_skills/pages/_batch/ge60/runs/20261019T161733110645Z-770f54b4/`；completed=34/34，failed=0，reused=0，生成 5.72 秒。
- 新签名 `signature=0f9b2fb0a512f7f9bf0f5a4cb7148e29b5e66ffbe89c6825a456cd79d35e14c1`（source_signature=5be31400…，因 `card_page_data.py`/`card_page_render.py` 源码变化而变，34 张旧 receipt 按预期 STALE 后全部重建）。
- 复核（脚本 `work/ge60_fix/verify_rebuild.py`，本轮实际执行）：34/34 receipt status=SUCCESS 且签名/run_id 与 run 一致、0 stale；68/68 产物 SHA-256 与 receipt 一致；29/29 依赖哈希与 signatures.json 一致（dependency_signature=4029ad1… 未变，数据输入未动）。
- G-11/G-14 文案：34/34 页含新说明、旧「同目录报告」句为 0；4 条 Medium 行在最终产物逐条复读通过（30110 行 A「数量：4匹」；354/6343/7689 各含「数量：11（可持有玛那上限）」，且无「原文未提供该效果数值」残留）。
- campaign 快照：ge60 MATCHING_SIGNATURE_SNAPSHOT 34/34；40to59/20to39/remaining NOT_GENERATED（未生成，非 STALE）。

### 指标变化（分母 N_all=2211 不变；E=0、N_num=2211、B=0 不变）

| 指标 | 修复前 | 修复后 |
|---|---|---|
| A | 1004/2211（45.4%） | **1005/2211（45.5%）** |
| 整行确认 | 0/2211 | 0/2211 |
| 原文A | 1004/2211 | **1005/2211** |
| C仅未知 | 1207/2211 | **1206/2211（54.5%）** |
| 部分A | 1004 | 1005 |

与审查预测（采纳 G-01 后 A=1005/C=1206，30110 卡内 A=29/C=36）完全一致。

### old→new 逐行变化清单（`work/ge60_fix/row_changes.jsonl`，脚本 diff_rows.py）

- 总行数 2211（34卡行集合逐一 assert 不变，无增删行）。
- row_class 变化：**仅 1 行**，30110 `*-skillid_2_-lvorder1-f2` C→A（G-01）。
- 答案新增（多出答案项）：**4 行**——上表 G-01 一行 + 354/6343/7689 各一行（G-02）。
- 答案标签/方向修改（数值不变）：291 行，按修复项计数（部分行跨类）：获得数量 84、秒统一 80、所需玛那减少 42、属性标签 73、发动费用 27、受击次数上限 12、G-06 顺序调整 9（20002 passives_0..8，值多重集不变）。
- numeric_items（literal/context/normalized_literal/raw_span 表示）重写：1005 行（全部 A 行；数值均未变，raw_value 多重集逐行比对仅上述 4 行新增项，无一行既有数值改变）。
- 审查期望的覆盖外改进同源行（如 350/30232/30337 另一档位、354 的 0マナ 行）一并修复，未扭曲任何原值。

### 遗留与边界

- G-15（队列抽样覆盖）按分工由主持处理，本线未改队列逻辑；新 run 队列仍为 340 行 NOT_REVIEWED，34 卡未完成全行人工验收。
- 其余 cohort（40to59/20to39/remaining）及 30236 等 11 卡试点页仍为旧生成器产物；下轮 cohort 生成时将自然带上本轮规则。
- `card_page_check.py` 的 pilot 自检断言（HP条件阈值、6発、1stChain 排除等）已用新 `original_numbers` 逐条手工验证通过（本轮实测），但该脚本针对旧11卡页，未重跑全套。

---

## polish 轮（2026-10-20）：DeepSeek 复验 PASS_WITH_EXPLICIT_SCOPE_LIMITS 的残留 R-01 与政策项 G-15

- 审查输入：`output/character_skills/review/ge60_20261019_deepseek/RECHECK.md`、`checks_recheck/residual_g07_full.json`（R-01 全表58条记录，RECHECK 第六节按行组汇总为24行）。
- 实施者：GLM 5.3 Flash（ge60标签与队列polish员）；只改 `scripts/character_skills/card_page_data.py`（标签规则）、`card_page_batch.py`（队列构造），未手改任何产物。
- 实施前快照：34卡旧 card.json、340行队列、旧报告存 `work/ge60_polish/old_cards/`、`old_audit_queue.json`、`old_cohort_report.json`。

### R-01：条件/所属/目标标签（58条记录：57条补标签，1条无据保留）

- 实现（`card_page_data.py`）：新增 `dimension_labels()`——条件短语表（地形が砂浜/船上/海中の時、ボスWAVE時、年代記の力を発動した時）、所属范围正则（戦場にいる<…>所属）、目标短语（戦場にいる味方，负向 lookahead 排除「味方以外」）。仅当短语**逐字出现在同句、且位于该数字之前**时附加；目标取数字之前最近主体，味方全体/自身/敵/1stキャラ就近覆盖、不跨句继承；只作用于效果量角色（效果量百分比/效果固定量/倍数），条件另作用于所需玛那减少/发动费用/获得数量/数量。条件以「（条件：…）」后缀并入答案 value，并写入 numeric item 与 answer 的 `condition` 字段；目标/所属并入 role 前缀（与 G-07 的「味方全体/攻击力效果量百分比」同格式）。
- 属性标签（G-07）触发从「行内≥2个百分数」改为「角色为效果量百分比」：单值泛标签行同样补分句属性（30104 leader 30%→「味方全体/攻击力效果量百分比：30%」）；阈值/上限角色（HP条件阈值等）一律不覆盖，修复了旧触发可能覆盖阈值角色的潜在缺陷（本轮 diff 中未发现实际受害行）。
- 处理结果：57条补上同句逐字标签（30110 地形条件×4、13229 ボスWAVE条件×2、20643 `<ｉｆの世界/魔神>所属`×5、30002 `<時空軍/未来>所属`×5、20002 戦場にいる味方目标×9、30004 passive 目标+条件×9、30104 味方全体/攻击力×1、4206 heroic 目标×6、7229 heroic 目标×16）；**30004 extra f0 保留原样**——原句「攻撃力が5%上がり」无「自身」字样（日文默认省略），按"同句没写的维度不得编造"不补，并经校验确认未被误改。
- 全部逐字验证：171个标签变化行逐一检查（脚本 `work/ge60_polish/verify_polish.py`），属性 token 全部位于该数字前分句内、目标/所属/条件全部位于同句数字之前（0 违例；target 59行、scope 20行、condition 15行）；同源同模板行一并修复，未扭曲任何原值。

### G-15：审查队列政策（`card_page_batch.py` audit_rows）

- 新规则：在既有每卡≥10行抽样（不足10行全列）之上，保证每个有实际行的 configured skill 至少1个不同实际 row_id 入队；技能多的卡队列可超过10行。合并别名行（alias）的技能由共享的规范行代表（同实际位置，无法拆出不同 row_id）。
- 队列行数 old→new：**340 → 671**；每卡17–31行；全部 review_status=NOT_REVIEWED、reviewer/decision 空；row_id 全部存在于 card.json 且互异。
- 技能覆盖率 old→new：**252/630 → 583/630**（有实际行的583个技能全部覆盖，逐技能 min-1 校验0违例）；其余47个技能为别名合并或无正文技能，无独立实际行可入队。

### 新 run 与复核

- 新 run：`output/character_skills/pages/_batch/ge60/runs/20261019T163658853746Z-313e0c28/`；34/34 GENERATED，reused=0，failed=0，6.7秒。
- 新签名 `signature=9501343f1e77bff993753b0928566fcede9ec6fdee355251373a0f16dd709b2b`；source_signature 5be31400…→5d06b4db…（生成器源码变化，预期）；**dependency_signature 4029ad13… 未变**（29/29 路径及哈希与 signatures.json 一致，数据输入未动）。
- 复核（`work/ge60_polish/verify_polish.py`，本轮实际执行）：34/34 receipt SUCCESS 且签名/run_id 与 run 一致；68/68 产物 SHA-256 与 receipt 一致；旧 run 目录未改写；campaign 快照 ge60 MATCHING_SIGNATURE_SNAPSHOT 34/34，40to59/20to39/remaining NOT_GENERATED。

### 指标对账（old→new，N_all=2211 不变）

| 指标 | 旧 | 新 |
|---|---|---|
| A | 1005/2211（45.5%） | 1005/2211（45.5%） |
| 整行确认 | 0/2211 | 0/2211 |
| 原文A | 1005/2211 | 1005/2211 |
| C仅未知 | 1206/2211（54.5%） | 1206/2211（54.5%） |
| B / E / N_num / partial_A | 0/0/2211/1005 | 0/0/2211/1005 |

- 逐行 diff：行集合增删0、japanese 逐字不变0变化、row_class 变化0、answer raw_value 多重集变化0；**仅171行答案标签（role 前缀/条件后缀）变化**，全部为逐字有据的标签补全，无任何数值或归类变化。

### 遗留与边界

- 本轮仅标签与队列变化；340→671 行队列仍是抽样，34卡全行人工核读仍未开始。
- 其余 cohort（40to59/20to39/remaining）尚未生成；下轮生成将自然带上本轮标签规则与队列政策。
- `card_page.py` 的 pilot `choose_samples`/`report` 未改（11卡试点产物口径不变）；队列政策只改批次线。
- 验证为离线文本/结构级；未做浏览器视觉验收、未实机。
