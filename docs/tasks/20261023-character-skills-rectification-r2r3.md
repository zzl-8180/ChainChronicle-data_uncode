# 复审整改 R2：数字/注记/子句覆盖根因＋R3 读卡与语境约束＋S1 同步（保留 R1 成果）

- 任务 ID：20261023-character-skills-rectification-r2r3
- 负责：主持 Kimi K3（唯一写入整合者）；实施 GLM 5.3 Flash 260828（high，CreateWorkflow 钉模型）；独立复验 DeepSeek V4.1 Flash 1017（high，完成后同会话或新会话按批惯例）
- 授权来源：用户 2026-10-23 指令「依据最新独立复审开展本轮整改，重点修复 R2、R3 的根因并同步 S1，保留已经通过的 R1 成果；完成后停在整改交付点，不自行展开新批次」（复审 `output/character_skills/review/independent_20261023_rectification_recheck/REPORT.md`）
- 状态：**进行中（R2/R3 实施＋DeepSeek 复验 REQUEST_CHANGES 的修复第三轮完成，实施及自检完成待独立复验；S1 归主持）**
- R3 交付（GLM 5.3 Flash 2026-10-23）：assign_candidates.py 两处根因修复（enrich_records.py 本轮
  无需改动——效果项语境由其 span→子句/全句定位提供且 join 零缺失）——
  ①R3a `_row_of` 始终返回所请求 row_id（旧实现首查返回该卡末行；修复后首查＝`_row_idx[row_id]`，
  不存在行显式 None）；②R3b 两级通道：效果项局部机制只在该效果自己的子句/全句匹配（弃用行日文
  full 级——复审实测置空后零变化）；技能级专项标签（context_text【…】头，如【共鳴必殺/連撃】）
  单列 skill_tags/also_basis 只记入不覆盖局部归属，局部无命中时才作主分类（basis=skill_tag）。
  正式产物重建：yg_backlog_view（P0∪Y.G. 11,168 项=P1 集合）、yg_candidates.json、
  yg_candidates_items.json；闭包 sum(items)=11,168、unassigned=0、fallback_reason 2,236 项、
  skill_tag 主分类 413 项。回归 19/19（r3_fix_regression.py）：复审 1,929 项错配冷缓存首查逐项
  归零、CID2/CID3 首查正确、全量 68,858 非视图项语境与页面独立重读一致、冷缓存/热缓存/逆序一致、
  349 共鳴必殺→YG1/共鳴アビリティ→YG2/350 反響→YG3/普通自身增益→G9 保持、真实多机制行三效果
  项 YG1/G2/G7 互异且置空局部语境后塌缩为技能级标签（语境实际参与）、多分类无重复、视图⊆backlog
  双向对账、锚点一致（snapshot 2306af95-57a14d29a773f3b7）。证据：work/character_skills_rectification_r2r3/
  （r3_fix_regression_results.json、r3_distribution_diff.json、chain1-3 stdout）。
- R2 交付（GLM 5.3 Flash 2026-10-23）：effect_ledger.py 三处根因修复——
  ①R2a 数字角色绑定（`_digit_role_class`/`_role_qk_compat`/`_digit_num_eq`/`_digit_text_role`＋
  答案消费后解析：角色↔quantity_kind/单位/数值三重绑定，效果量角色须被同子句主张消费；
  叙述性数字永不映射）②R2b 结构化覆盖（`_mechanism_structural_coverage`：只认 quantity_kind
  指认或注记结构化载体披露，「未知/未解析/待核查/未分配」否定注记不构成覆盖）③R2c 逐子句
  残余监视扩表（＋バリア/盾/シールド/ガード/軽減/弱点）＋谓词模板〈宾语〉を付与/無効化/吸収/
  軽減（`_MECHANISM_PRED_RE`，宾语≤12 字符排除に格）。终态：完整 4,000（零变）、部分 48、
  未解析 9,107、拆分 28,510、backlog 80,026；641 行未解析/部分→拆分（S3b 217/S2 424）；
  735 完整行数字重绑定全部核心段相等验证通过；账本 9 项自检＋verify_full 17/17 PASS
  （campaign 新签 2306af95…，页面 2,236 卡全量重渲染 0 失败，30236 card.json 字节不变）。
  证据：work/character_skills_rectification_r2r3/（r2_fix_regression 17/17、A7 25/25、
  r2_affected_rows_review.json、status_transitions.json、verify_full_final.json）；
  上轮 r2_regression 9/10（6257 例预期 basis 更名，语义保持）。R1 保护核验通过
  （HP 32 行/104 答案 pages 零写入、S7 1,336 行零状态变化、6306 HP ?–50% 保留）。

## 基线锚点（2026-10-23 实测）

campaign `0b66de961401c7c1…`；source `5b9973b9775a289c…`；rules SHA 前 16 `57a14d29a773f3b7`；行 41,665／A 17,476／C 24,189／整行推断 3,351／确认 266／原文A 13,859；推断答案 12,871；backlog 79,385（P0 0／P1 11,024／P2 68,361）；完整 4,000／部分 385／未解析 9,411／拆分 27,869；verify_full 17/17。

## 已核实的根因（主持独立复核）

1. **R2a 数字误映射**：`effect_ledger.py:360-376` `_digit_mapping` 首环——数字等于整行任一答案 raw 或其百分比即返回映射，无数量角色/语义位置核对。复审反例成立：349 前置「HPが30%以上のとき」→30 映射到暴击答案 raw 0.3×100 判完整（错）；HP40%→待核查（证明判定靠数字碰巧）。
2. **R2b 注记词面覆盖**：`:652-656`——任一答案注记/类型/条件含机制词即 covered，「暗闇机制尚未解析，待核查。」式否定注记也被当完成证据。
3. **R2c 子句整句覆盖**：`:333-335`——子句识别到任一主张即 covered_clause_idx 整句结清，24 词监视表外的同句机制（如 バリア）漏出待办。
4. **R3a 首次读卡错行**：`assign_candidates.py:166-169` `_row_of`——首次加载卡片时循环 `out` 停在末行并返回 `out`（非 `_row_idx[row_id]`）；实测 1,929 项语境错配、1,328 项分类改变，正式 nonyg 统计与错误重放吻合（CID2 的 ability 行被读成该卡传授伤害句落 G1）。
5. **R3b 语境不约束分类**：`assign_item:67-85` 对每个候选用 clause/sentence/full 命中后按全局优先序取首个，context_text 不参与匹配、page_group/effect_type 只进兜底理由——7,157 效果项清空 clause/sentence 后主分类与 also 变化均为 0（语境是摆设）。

## R1 保留范围（不得回退）

8 行 104 个 HP 条件答案（原值/来源/条件关系）；1,336 行 same_cond 披露与 S7 待办；6306 缺失 HP 下界保持缺失不补 0；HP 运行时边界与同条件组选取维度保留待核查说明；30236 零触碰。R2 公共判定修复致相关行状态变化时逐行说明原因，保留已解析单项和来源。

## 整改方案

- **R2**（effect_ledger.py）：数字映射绑定具体主张/条件——语义角色（条件/阈值/效果量/序数）＋数量类型＋单位/换算口径＋文本位置＋答案/证据引用，数值相等仅为必要线索；机制覆盖只认有解析状态的结构化引用或明确审过且完整匹配的语义模板；「未知/未解析/待核查/未分配」注记保留为缺口不作完成证据；同句剩余内容无法证明覆盖时产生具体待办或拆分待核查（有限可审计模板，不加 CID/测试文本特判）；受影响「完整」行定向复评（保留正确答案、逐条记录状态变化依据、不一律降级）；真实行复评与合成测试分开统计。
- **R3**（assign_candidates.py/enrich_records.py）：`_row_of` 始终返回所请求行（含不存在行处理）；逐项验证日文/类别/表名/效果位置属所请 row_id；分类区分技能整体专项标签（如【共鳴必殺】，技能级）与目标效果局部机制（伤害/增益/屏障/反響，效果级）——技能级标签可参与分类但不得无依据让同句其他机制覆盖目标效果归属；多分类每项有可定位依据＋明确主/附加分类与计数规则；重建正式 Y.G. 候选与非 Y.G. 收益统计（非旁路）。
- **S1（主持）**：整改后按最终正式产物重算并同步进度文件唯一当前块（campaign/完整度/待办/状态一致性；历史段保留历史值标轮次）；复验前写「实施及自检完成，待独立复验」。

## 验收（关键用例）

R2：349 六项保持；20905 真实完整保持；删 20905 HP 阈值→未完成/待核查；349+「HPが30%以上のとき」→未完成/待核查（0.3 暴击不得覆盖）；与已有答案碰巧同值的条件数字→语义判定不放行；349+「と同時にバリアを付与する。」→待办/拆分；349+暗闇＋注记「暗闇机制尚未解析，待核查。」→仍未完成；真正有效结构化答案/证据能解除对应待办（不一律判未知）；CID86 概率映射保留。R3：同一 row_id 冷/热缓存与不同访问顺序返回相同语境与分类；CID2/CID3 真实错配实例首查正确；原 1,929 错配清单逐项归零（不硬编码 1,328 为通过条件）；非 Y.G. 统计与修复后逐项聚合一致并给前后差异；349 共鳴必殺/共鳴能力/350 反響/普通自身增益保持正确；同一描述多机制不同目标效果的测试证明局部语境约束分类；多分类每项有依据且无无意重复；视图⊆backlog 双向对账、锚点一致；unassigned=0 非唯一验收。回归不得只调用同一错误实现自我对账。

## 允许写入

`scripts/character_skills/`（effect_ledger/render/verify 最小改动）、`work/character_skills_yg_priority/`（assign/enrich 与产物）、`output/character_skills/pages/`（重建）、`output/character_skills/effect_ledger/`（重建）、`work/character_skills_rectification_r2r3/`、`docs/tasks/20261023-character-skills-rectification-r2r3.md`（本卡）、`output/character_skills/inference_inventory/`（补记）、`docs/tasks/character-skills-progress.md`（仅主持 S1）。rules.json 预期零改动。禁止 git；禁止改旧审查报告与冻结证据；30236 零触碰。

## 交付与停止

根因与处置表（R2/R3/S1）；逐行变化清单（答案变化/条件映射变化/状态纠正/待办补录/纯展示变化分列）；R1 保护核验（8 行 104 答案与 1,336 披露无非预期变化）；回归证据（正反例＋冷热缓存＋访问顺序＋多效果分类＋正式检查）；一致终态（代码/页面/账本/候选/进度同版本＋运行命令＋证据路径）；旧结果保护（未受影响旧答案与 30236）。**完成后停在整改交付点待独立复验，不自行开始下一批。**

## 最近更新

- 2026-10-23：任务卡建立；R2a/R2b/R2c/R3a/R3b 根因经主持逐行源码核实（effect_ledger.py:333-335/:360-376/:652-656、assign_candidates.py:166-169）；基线锚点记录；GLM 实施已派。
- 2026-10-23（R2 实施完成）：R2 三根因修复＋终态重建＋回归全绿，待独立复验；页面/账本同版本（campaign 2306af9559431a72…，rules 57a14d29a773f3b7 零改动，rules.json 未触碰）；R3（assign_candidates）本实施轮未动；S1 看板同步归主持。
- 2026-10-23（R3 实施完成）：assign_candidates._row_of 首查与两级语境通道修复＋正式产物链重建（build_inventory→enrich_records→assign_candidates）＋回归 19/19，待独立复验；非 Y.G. 收益统计随同版本 backlog（80,026 项）重算并给分类器级同池前后分布差异（r3_distribution_diff.json）；S1 看板同步归主持。
- 2026-10-23（终态统一重建与验收完成）：四 cohort 非 resume 单轮重建 2,236/2,236（失败 0、复用 0，campaign 签名与代码重算一致 2306af9559431a72…）→effect_ledger 重建（9/9 自检；ledger d731ac3ac0b29ac6/backlog 1d3fee7c82e9c449 与重建前逐字节一致）→card_page_index --execute（EXPECTED_CAMPAIGN 交叉核对通过）→regen_readme28→选题链全链重跑（视图 11,168＝P1 集合、闭包 11,168、unassigned 0、skill_tag 主分类 413）→verify_full **17/17 PASS**（新增 A14 终态证据对，既有检查零删除）→独立目录复跑 ledger.jsonl/backlog.json 逐字节一致（metrics 仅时间戳字段异）。R1 保护核验全过：8 行 104 个 HP 条件答案 vs 冻结复审证据逐字段 0 差异、8 行账本状态 0 差异、S7 1,336 行页面披露＝账本＝backlog 三方集合相等、6306 保留 HP ?–50%、30236 card.json 字节不变。逐行变化清单与根因处置表：work/character_skills_rectification_r2r3/final_change_list_and_disposition.json（答案变化 0／条件映射变化 735（全部核心段相等复评通过）／状态纠正 641（完整→其他 0、拆分→完整 0）／待办补录 +641＋S2/S3b gap/have/next_step／纯展示=页面重渲染）。验收对账：A14_final_state.{md,json}。**R2/R3 实施及自检完成，停在整改交付点待独立复验；S1 看板同步归主持。**
- 2026-10-23（复验修复第三轮完成）：DeepSeek 复验 REQUEST_CHANGES（R2-S2-CONSUMPTION-319 High／R2-ROLE-ALIAS-105 Medium／Low×5）全部处置——①效果类型补齐（必杀技威力→威力（词表外）、暴击威力→クリティカル威力、暴击发生率→クリティカル発生率、回复量→HP回復；全库 223 种 qk 扫描审计、批 8 暴击零冲突）＋效果量消费位置同句跨子句回退＋泛化标签精确同标签结构化回退（effect_ledger.py）→**424 行 S2 误挂全部解除（0 残留）**、状态回正确轨迹（部分→完整 313/部分→部分 24/未解析→完整 65/未解析→部分 4/未解析→未解析 18；逐行 r2fix2_424rows_review.json）；S2 gap/have/next_step 文案区分四类「无答案/同标签答案存在但绑定链未闭合/叙述性数字角色说明/文本角色未识别（role-none 321 行，第四类）」（口径更正：原写三分漏 role-none 类——复验 R2-S2-GAP-FOURTH-BRANCH，20261023 文档债务修正包）；变更清单 424 行措辞更正（319 行为同标签正确旧映射被误挂、105 行为子类型错配、真收紧 0 行）。②effect_amount 类别别名收紧为 _AMOUNT_SUBTYPE_TABLE 同子类型＋绑定优先序全标签>核心段；A7-21 重写为真实行 2046 受控变体＋_role_qk_compat 单元断言（真不同子类型拒绝）。③Low：S3b 叙事过报低置信注记（不排除命中）；narrative S2 文案精确化；非 Y.G. 同池差异固定（nonyg_same_pool_diff.json：G9 −1,069/YG1 +2,050，corrected 基线 −2,208；跨池 −2,039 停用作归因）；sentence-only 计数入 yg_candidates meta（效果项 1,702；skill_tag-only 效果 248/拆分 165）；a7_regression.py 入库 acceptance/。终态重建：页面四 cohort 非 resume（campaign a470c054）→账本（ledger b4c62b175abe2ebf/backlog 67c6a39d5fbaec5c）→index/readme28/选题链（视图 10,939 闭包 10,939 unassigned 0）→verify_full 17/17→独立复跑逐字节一致→R1 保护重跑全过（104 HP/S7 1,336/6306/30236 零变化）→r2_fix 17/17、r3_fix 19/19、A7 25/25。**实施及自检完成，待独立复验；S1 归主持。**
