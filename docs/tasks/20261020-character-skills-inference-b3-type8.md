# 任务卡：批 3 前置审计——家族 #3「⟨ATTR⟩が上がる。」type8 子集（纯分析）

- 任务 ID：`20261020-character-skills-inference-b3-type8`
- 状态：**前置审计已完成（2026-10-20 时点：未晋级、未改生成器）【2026-10-21 复核注：其后实施晋级 40 行＋hint 178，DeepSeek 审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS；过程见下文实施节】**
- 负责人／对话标识：type8范围审计员（GLM 5.3 Flash 260828，动态工作流子代理）
- 日期：2026-10-20
- 产出：`output/character_skills/inference_inventory/b3_type8_scope.md`（范围设计与晋级规则）

## 目标

按 DeepSeek 试点审查前置条件，核对 type8 规则（rules.json occurrences/conditions/换算
语义/已核样本域），重建家族 #3 的 type8 子集，给出严格模板范围定义、排除项与晋级规则。
只分析，不晋级。

## 允许写入（本轮实际遵守）

- `work/character_skills_b3_type8/`（build_scope.py、positions.py、type8_subset.json、type8_tier1.json）
- `output/character_skills/inference_inventory/b3_type8_scope.md`
- 本任务卡
- 未改：生成器、pages、profiles/原始输入、旧审查报告、共享进度文件；未 git 暂存/提交。

## 关键结果（详见 b3_type8_scope.md）

- **规则核对**：rules.json `skilllist|8` 仅 /param1（攻撃，GetAbilityAttack 0x1107958）、
  /param2（移動速度，0x1118c28）、/param3（受伤量乘数、正文写「防御」，0x1108124）三条
  已确认规则；conditions=IsEnableAbility 无条件通过（Always 常时）；**occurrences 三条均
  null**（72/277 规则有 occurrences，均源于 cid30236 字典；type8 不在其列）→ 已核样本域
  按 native 口径披露：双路分支解析 53/53 通过、正文数值直写对照 1 条、param3 中性核对
  1 条、param4/param0 分源范围核对（CACHE 328 / APK 2209 条）。
- **子集实测**：218 行/214 cid（APK 214 + CACHE 4），100% 对接 records.jsonl type8 记录；
  属性分解 FULL 178 / PART（含暴击）36 / NONE（暴击-only）4；方向冲突 0 行；
  rule-hit 行 214（param1/2/3 候选全部 rule_hit；param4..9 候选无 rule、指向同 cid 兄弟记录）。
- **严格范围 Tier1：40 行/40 cid（全 APK）**＝第 1 段首句＋段内句后无后续文本＋同文仅
  出现 1 次＋方向一致（34 FULL + 6 PART）；PART 行暴击属性留 attr-hint、其余照常映射。
- **排除 178 行留 hint**：句后条件扩展 164（条件增幅疑由兄弟记录承载，仅 1 例核实，宁可
  排除）、同文多次出现 10、非首段/段中 10、暴击-only 无字段映射 4（重叠计数，见 scope §4）。
- CACHE 4 行全部不在 Tier1；type8 无 1017 的「CACHE 已核 321 条」豁免口径，全部值行
  逐行披露「同类型原生规则外推」。
- cid 221 有 2 行同子集（1 Tier1 + 1 排除）——「每卡恰一行」不成立，实施须逐行。

## 晋级纪律（批 3 实施时逐行强制；scope §5 全文）

只升推断；属性→字段 1:1；方向审核（param3<1 才算防御上升）；对象=自身（type8 原生语义，
无位图审核）；字段级证据取 rules.json rule["evidence"]（INFR-01 同法）；适用范围披露
（INFR-02 同法、type8 口径）；多段披露（Tier1 全部 40 条记录为 2–3 段，全行生效）；
非首段/条件扩展/同文多次/暴击-only 各按 scope §4 文案留 hint。

## 下一步（需主持/审查方放行后实施）

1. 批 3 实施：按 scope §3.1 六条件＋§5 晋级规则新建 `card_page_inference_type8.py`
   （建议命名），四 cohort 全量重建＋old→new 对账（同试点方法）。
2. 待补证二批：句后条件扩展 164 行的兄弟记录结构原生核实。
3. 家族 #3 的 type26 子集（272 行）独立前置审计。

---

## 实施节（2026-10-20，批 3 实施完成）

- 负责人／对话标识：type8子集实施员（GLM 5.3 Flash 260828，动态工作流子代理）
- 状态：**实施完成，四 cohort 全量重建＋复核通过（待审查方独立审查）**

### 实现内容

- 新模块 `scripts/character_skills/card_page_inference_type8.py`（独立于 type1017 模块）：严格句正则
  （属性名词「と」连接＋「が上がる。」；句首连接词只 hint 不晋级）、属性→字段 1:1
  （攻撃力→/param1、移動速度→/param2、防御力→/param3，rules.json skilllist|8 三条已确认规则）、
  方向审核（param1/2>1、param3<1＝受伤量乘数方向按代码；中性如实登记；冲突整行 hint）、
  暴击名词不映射（PART 行 attr-hint、暴击-only 整行 hint）、句位/段内句后文本/同文次数逐行审核、
  句外参数注记（param0/param4 无读取路径）、字段级证据（INFR-01：rules.json rule["evidence"]，
  路径件缺失显式失败）、适用范围披露（INFR-02 type8 口径，按记录 id 分支——R-02 教训内建）。
- **R-03 教训内建**：段号按片段精确出现位置；段中句按所在段开启 ◆ 计数（试点公式对段中句段号
  虚增 1，本模块不沿用；试点模块未改动，其晋级行全部首段首句不受影响）。同文多次出现不取首次，
  登记全部出现位置（8404「第 1、3 段」实测正确）。
- 接入：`card_page_data.py`（片段循环并列调用、promote 行 metadata `inference_b3`、hint 行
  `inference_b3_hint`、coverage 新增 `inference_b3_promoted/hinted`）、`card_page_policy.py`
  （INFERENCE_STATUS 批 3 字段）、`card_page_batch.py`（聚合透传＋plan 文本）、
  `card_page_render.py`（intro 批 3 说明）。

### 重建与复核结果（本轮实际执行）

- 四 cohort 全量重建 0 失败：ge60 34/34、40to59 290/290、20to39 436/436、remaining 1476/1476。
  新签名 `28bb8fc3554f49362ed70fba47443719b8626efa45ed0e55382f9994dbcd0182`
  （dependency_signature `4029ad13…` 不变，29/29 数据依赖逐一重算未变）。
- 复核（`work/character_skills_b3_type8/check_receipts.py`）：2236/2236 receipt SUCCESS、
  4472 产物哈希逐一核对 0 不一致、0 stale、campaign 四 cohort MATCHING_SIGNATURE_SNAPSHOT。
- 晋级/留 hint：**晋级 40 行/40 cid（全部 APK；20to39 2＋remaining 38）、留 hint 178 行**
  （ge60 1／40to59 8／20to39 90／remaining 79）——恰为审计 tier1 40＋排除 178；
  晋级集合与 `type8_tier1.json` tier1 清单 40 行完全对齐（逐行 row_id 比对 0 偏差）。
- 指标 old→new（分母 N_all 41,665）：A 14,462→**14,502**（+40）；C 27,203→**27,163**（−40）；
  原文A 13,859 不变；整行推断 337→**377**；整行确认 266 不变。分 cohort：ge60/40to59 指标零变化；
  20to39 A 3,995→3,997、整行推断 128→130；remaining A 3,144→3,182、整行推断 56→94。
  值行 89 条（param1 33／param2 33／param3 23），全部按 rules.json 换算器从原始记录再推导一致。
- 零变化对账（`compare_full_rows.py`，changes_old_new.jsonl）：行集合零增删（41,665 两侧一致）；
  变化行恰 218＝40 晋级＋178 hint，全部带批 3 标注字段标记（0 个非批 3 变化行）；
  **其余 41,447 行全行全字段逐字节零变化**；5 条边界行（30338×2/7229/4009/10212）零变化仍拒绝。
- 单样本验证（`test_build_samples.py`）：cid 11212/1279/221/5223/8404 及边界 cid 现场构建——
  晋级行均在 tier1、PART 行暴击 attr-hint＋其余照常、221 两行逐行处理（1 晋级 1 hint）、
  8404 连接词句与同文多次行 hint 原因正确、段号精确（第 3 段非第 4 段）。

### 文档勘误（对审计产物的两处更正，实施实测为准）

1. scope §3.2 变体表合计 41 行（多列 1 行「防御力が上がる。」）；tier1 权威清单为
   `type8_tier1.json`（40 行，无该变体）。子集中「防御力が上がる。」2 行（8111 段中＋句后扩展、
   8229 同文两次）均正确留 hint。
2. scope §4 排除类计数 164/10/10/4 为近似重叠归类；实测多标签口径：句后后续文本 172、同文多次 10、
   非首段/段中 13、暴击-only 4（唯一行数 178 与审计一致）。

### 允许写入（本轮实际遵守）

- 脚本：`card_page_inference_type8.py`（新建）、`card_page_data.py`、`card_page_policy.py`、
  `card_page_batch.py`、`card_page_render.py`
- 输出：`output/character_skills/pages/`（含 `_batch/`、README.md §14）；`work/character_skills_b3_type8/`
  （快照/对账/复核脚本与 JSONL）；本任务卡实施节
- 未改：profiles/原始输入、旧审查报告、共享进度文件、type1017 试点模块；未 git 暂存/提交

### 下一步

1. 派独立审查（DeepSeek 会话）按 b3_type8_scope.md 验收：40 晋级行逐行、89 值行换算、
   178 hint 行原因、适用范围披露、零变化对账、指标对账。
2. 待补证二批：句后条件扩展 172 行的兄弟记录承载结构原生核实（31020500 链 1 例 → 结构性核实）。
3. 家族 #3 type26 子集（272 行）独立前置审计。
