# 任务卡：批 4 前置结构审计——句后条件扩展 172 行的兄弟记录承载结构核实（纯分析）

- 任务 ID：`20261020-character-skills-inference-b4-cond`
- 状态：**已完成（结构核实与范围设计；未晋级、未改生成器、未改 pages 产物）**
- 负责人／对话标识：批4结构审计员（GLM 5.3 Flash 260828，动态工作流子代理）
- 日期：2026-10-20
- 产出：`output/character_skills/inference_inventory/b4_cond_scope.md`（结构核实、模式分类、
  晋级规则与边界）；逐行明细 `work/character_skills_b4_cond/`（audit_set.json、b4_rows.jsonl、
  b4_promotable.json、b4_hints.jsonl、build_b4.py、match_b4.py）

## 目标

对批 3 遗留「句后条件扩展」172 行做全子集结构核实：逐行解析所属 type8 记录的
兄弟/sub 记录链，判定「基础 type8 记录承载基础值＋兄弟记录（type36 等）承载条件增幅」
分工模式是否稳定成立，给出可晋级行与留 hint 行清单及理由。只分析，不晋级。

## 允许写入（本轮实际遵守）

- `work/character_skills_b4_cond/`（审计脚本与中间数据）
- `output/character_skills/inference_inventory/b4_cond_scope.md`
- 本任务卡
- 未改：生成器、pages 产物、profiles/原始输入、旧审查报告、共享进度文件；未 git 暂存/提交。

## 关键结果（详见 b4_cond_scope.md）

- **行集**：批 3 hint 178 行中，结构上句后有文本者恰 172 行（显式标签 163＋同文多次行
  结构带句后文本 9），与批 3 任务卡勘误计数 172 一致；6 行无句后文本（暴击-only 4、
  8229、8404-f4）不在本批。
- **链路**：skilllist 记录自带数据侧 `sub` 数组（APK/CACHE 均有）；link_skills.py:612-630
  单层展开、profiles.py:402 落 sub_ids/children。**172 行父记录 100% 有 sub_ids，
  children 与 sub_ids 零偏差；1 行 1 记录无共享。**
- **模式定案（P-A，37 行晋级候选）**：基础句→父 type8 param1/2/3（方向全过、未主张槽
  全中性）；tail 主张→恰好一个兄弟记录、逐主张槽已确认规则＋方向一致＋无未主张活性槽；
  条件族与兄弟类型零交叉混杂——
  - 36×19（HPがN%以上；param0 阈值 19/19 一致；type36 语料 27/27 条实质正文均 HP 条件增幅，B 级）
  - 80×10（マナ所持；iParam0=31/16 位图逐例一致；composite_80 原生核实，A 级）
  - 67×7（味方在场/魔法使い/〈副都〉；param0=2 计数阈值；composite_67 原生核实，A 级）
  - 1005×1（状態異常の敵；仅值规则、门控无证据，C 级，实施可单独保守降级）
  - 含 CACHE 1 行（4227，原始层复核 child 40422701 param0=0.25）。
- **留 hint 135 行**：兄弟无规则/覆盖不齐 86（69/9/1079/51 等承载增幅）、tail 其他效果主张 26、
  兄弟活性槽超出文本 15、双条件链 7（均同文多次行）、结构通过但同文/非首段遗留 1（7626）。
- 顶层锚例复核：31020500（type8，sub=[31020501,31020502]）→31020501（type36，
  p1=1.75/p2=1.15/p3=0.9/p4=0.4/p5=0.2，与批 3 B3-R01 口径一致）。

## 晋级纪律（批 4 实施时逐行强制；scope §4 全文）

只升推断、evidence_scope=TEMPLATE_BATCH4_COND_EXT；**双记录映射**——基础句值行与条件
增幅值行分列、各自注明来源记录（父 rec_key／child rec_key＋link_kind=sub_effect）；
条件文本逐字、条件槽（param0/iParam0 等）不造数；门控证据 A/B/C 分级逐行披露；
方向审核父/子两侧；INFR-01/02、多段披露、句外参数注记沿用批 3 §5。

## 边界（scope §6 全文）

不得跨记录合并数值答案（禁写 3.0×1.75 之类乘积）；不得把条件增幅写进基础值（双向禁止）；
子记录单层展开为界；非首段/同文多次行不晋级；P-B/C/D/E 类不得借本批口径产出。

## 下一步（需主持/审查方放行后实施）

1. 批 4 实施：按 scope §2.4 判定模型＋§4 晋级规则新建 `card_page_inference_cond.py`
   （建议命名），全量重建＋old→new 对账＋抽样现场构建（至少 10205/1284/20624/8348/4227）。
2. P-B 86 行：type69/51/9/1079 等兄弟类型槽位语义的原生核实（另行审计，不预设结论）。
3. 家族 #3 type26 子集（272 行）独立前置审计（批 3 遗留，未动）。

---

## 实施节（2026-10-20，批 4 实施完成）

- 负责人／对话标识：批4实施员（GLM 5.3 Flash 260828，动态工作流子代理）
- 状态：**实施完成，四 cohort 全量重建＋复核通过（待审查方独立审查）**

### 实现内容

- 新模块 `scripts/character_skills/card_page_inference_cond.py`（独立于批 1/批 3 模块，独立标记；
  句位/句后文本/同文次数/方向判定 import 复用 `card_page_inference_type8` 同口径实现，不复制逻辑）：
  - 范围判定：type8 记录＋基础句匹配批 3 严格句正则（无连接词）＋同段句后有实质文本；
    无句后文本/正文不可用/定位失败的行返回 None（交批 3 口径，零影响）。
  - 结构分工（scope §2.4）：tail 主张解析（効果が上がり→基础属性、クリティカル発生率/威力→
    暴击两槽、HPが徐々に回復する→regen；条件前缀逐字保留）＋兄弟记录覆盖匹配（逐主张槽
    已确认规则＋方向一致＋无未主张活性槽＋消费后无残余＋至多 1 条件句）；兄弟记录来自
    links 的 sub_effect_refs（父记录 sub 字段，link_kind=sub_effect，单层展开为界）。
  - 分类（scope §3）：P-B 覆盖不齐（逐主张槽计数）/P-C 消费后残余/P-D 活性槽超出文本/
    P-E 多条件链/THRESHOLD/AMBIGUOUS/NO_CLAIM/PARENT（父方向冲突、父未主张活性槽）；
    基础句含暴击名词不产生候选（§4.6）；行级遗留（同文多次/非首段）强制 hint 且
    7626 类「结构通过但行级遗留」在 hint 首句显式注明；结构原因不被父侧/暴击问题抢占
    （与审计 match_b4 同序，原因叠加登记）。
  - 双记录映射（scope §4.2）：基础句值行（父 type8 /param1/2/3，numeric_source=
    「模板推断（批 4 条件扩展·基础句）」）＋条件增幅值行（兄弟记录对应参数，numeric_source=
    「模板推断（批 4 条件扩展·条件增幅）」）；两组各自注明来源记录（父 rec_key／child rec_key
    ＋link_kind=sub_effect）＋条件文本逐字＋门控 A/B/C 分级；条件槽不造数、只注记原值（§6.3）；
    两值行不合并、不写跨记录乘积（§6.1/§6.2）；INFR-01 字段级证据（child 类型含
    dispatch_map.json 证据源；带括注路径件截取路径核对，缺失显式失败）；INFR-02 按记录分支的
    适用范围披露（type36/80/67/1005 同为 occurrences 未登记的同类型外推口径，§6.4）；
    多段披露、父/子句外参数注记、其余兄弟记录登记（§2.4 判定 5）。
- 接入：`card_page_data.py`（片段循环批 4 先于批 3——批 4 晋级的行不再调批 3，其句后文本
  hint 由批 4 裁决；批 4 hint 行批 3 照常审核叠加登记；promote 行 metadata `inference_b4`、
  hint 行 `inference_b4_hint`、coverage 新增 `inference_b4_promoted/hinted`）、
  `card_page_policy.py`（INFERENCE_STATUS 批 4 字段）、`card_page_batch.py`（聚合透传＋plan
  文本＋permission_boundary 指向本任务卡）、`card_page_render.py`（intro 批 4 说明，两批→三批）。
- 实施前预检（`work/character_skills_b4_cond/verify_eval_set.py`）：用生成器同款装配对审计行集
  172 行全量重判——promote 37/hint 135/none 0，与 `b4_promotable.json`/`b4_hints.jsonl`
  逐行 0 偏差后才重建。实施中发现并修正两处实现偏差（兄弟覆盖判断子集条件写反；
  P-B/P-D 原因曾被暴击/父侧检查抢占——修正后与审计 verdict 文案逐行一致）。

### 重建与复核结果（本轮实际执行）

- 四 cohort 全量重建 0 失败（ge60 34/34、40to59 290/290、20to39 436/436、remaining 1476/1476）。
  终版签名 `877e9337bc14194d1ab456404dc2744b3d3352365383379df0f2b8d8b6b3aca9`
  （dependency_signature `4029ad13…` 不变，29/29 数据依赖逐一重算未变）。
- 复核（`work/character_skills_b4_cond/check_receipts.py`）：2236/2236 receipt SUCCESS、
  4472 产物哈希逐一核对 0 不一致、0 stale、campaign 四 cohort MATCHING_SIGNATURE_SNAPSHOT。
- 晋级/留 hint：**晋级 37 行/37 cid（APK 36＋CACHE 1；20to39 16＋remaining 21）、留 hint 135 行**
  （ge60 1／40to59 8／20to39 73／remaining 53）——恰为审计 37＋135；晋级∪hint＝审计行集 172，
  逐行 0 偏差。
- 指标 old→new（分母 N_all 41,665）：A 14,502→**14,539**（+37）；C 27,163→**27,126**（−37）；
  原文A 13,859 不变；整行推断 377→**414**；整行确认 266 不变。
- 值行 285 条（基础句 110：/param1 37、/param2 36、/param3 37；条件增幅 175），全部按 rules.json
  换算器从原值再推导一致（基础句 raw↔审计 parent_raw_params、条件增幅 raw↔审计 child_answers）。
- 零变化对账（`compare_full_rows.py` → changes_old_new.jsonl）：行集合零增删（41,665 两侧一致）；
  变化行恰 172＝37 晋级＋135 hint，与审计行集逐行一致（0 增 0 漏），全部带批 4 标注字段标记
  （0 个非批 4 变化行）；变化字段：unknown_reasons 172、inference_b4_hint 135、批 4 晋级字段各 37、
  inference_b3_hint 37（晋级行的批 3 句后文本 hint 移除，其余 141 行批 3 hint 原样保留）。
  5 条边界行（30338×2/7229/4009/10212）零变化；批 3 晋级 40 行、pilot 晋级 337 行零变化；
  既有整行推断 377 行（pilot 337＋批 3 40）不变。
- 双记录映射边界逐行核对（`check_boundaries_and_values.py`）：基础句值行仅父 type8 三槽＋
  来源记录注记；条件增幅值行 rule_key∈审计 child_answers、来源记录/逐字条件/link_kind/
  不合并注记齐全；行级 A·推断·TEMPLATE_BATCH4_COND_EXT。hint 分类实测与审计一致：
  P-B 86、P-C 26、P-D 15、P-E 7、同文多次（多标签）9、非首段/段中（多标签）8、
  结构通过但行级遗留 1。
- 抽样现场构建（`test_build_samples.py`）：10205（type36 B 级）、1284（type80 A 级）、
  20624（type67 A 级）、8348（type1005 C 级，按 scope §4.4 晋级＋C 级显式披露）、
  4227（CACHE）、4296（基础句 2 属性、父 param2 中性）全部晋级且值行/注记符合边界；
  7626/10211/1044 hint 原因正确；5 条边界 cid 零晋级零批 4 hint。

### 允许写入（本轮实际遵守）

- 脚本：`card_page_inference_cond.py`（新建）、`card_page_data.py`、`card_page_policy.py`、
  `card_page_batch.py`、`card_page_render.py`
- 输出：`output/character_skills/pages/`（含 `_batch/`、README.md §15）；`work/character_skills_b4_cond/`
  （快照/对账/复核脚本与 JSONL）；本任务卡实施节
- 未改：profiles/原始输入、旧审查报告、共享进度文件、type1017/批 3 模块；未 git 暂存/提交

### 下一步

1. 派独立审查按 b4_cond_scope.md 验收：37 晋级行逐行、285 值行换算与双记录来源注记、
   135 hint 行原因、门控 A/B/C 分级披露、条件槽不造数、零变化对账、指标对账。
2. P-B 86 行：type69/51/9/1079 等兄弟类型槽位语义的原生核实（另行审计，不预设结论）。
3. 家族 #3 type26 子集（272 行）独立前置审计（批 3 遗留，未动）。
