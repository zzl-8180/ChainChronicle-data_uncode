# 任务卡：批 12 ability1095 扩域（tier B 94 行 p2/p5/p6）——前置审计（纯分析）

- 任务 ID：20261022-character-skills-inference-b12-1095ext
- 负责人：批12-1095扩域审计员（GLM 5.3 Flash 260828，workflow 子代理，单 ask）
- 状态：**前置审计已完成（未晋级；案 A/B 取舍与实施批待主持裁决）**
- 日期：2026-10-22
- 上游：批 11（`20261022-character-skills-inference-b11-sa1095.md`）遗留项第 1 条

## 目标

评估把 `skilllist|1095` 的 p2（移动乘数）/p5（暴击概率直接加算）/p6（暴伤 delta=p6−1.5）三键从「已核 ID 数」口径（occurrences 1/1/2）扩展到 CACHE ability1095 全域的可行性；给出 occurrences 口径依据、tier B 94 行候选复核、代表样本与实施批范围设计。

## 允许写入范围（本轮实际写入）

- `work/character_skills_b12_1095ext/`（`b12_ext_audit.py`＋`b12_ext_data.json`，可复跑）
- `output/character_skills/inference_inventory/b12_1095ext_scope.md`
- 本任务卡

## 关键结论（详见 scope §1–§6）

1. **证据可行性＝能闭合**：三槽读点与语义均在既有片段（p2=movement/walk_self_dispatch+walk_small_types 的 `cmp #0x447`→IsEnableAbility→get_param2→**fmul**；p5=critical/chance_dispatch_and_add 的 get_param5→**fadd 直接加算**；p6=critical/damage_baseline_and_dispatch＋attack_critical_base 的 get_param6→**fmov -1.5→fadd** delta、0x153b6e4 加回基础 1.5），全部按 ability **类型**分派、无按 skill_id 分叉——与 p1/p3 occurrences=407 同一结构论证。差距仅两点：受控检查 1095 槽覆盖窄（p2/p5 仅 65000001、p6=43023601+65000001）＋无全域公式核对。最小新增＝每槽 2–3 条域内记录边界检查（约 6–9 项）＋公式核对扩到 p2 407/p5 211/p6 407，**无需新反汇编**（scope §1.3 案 A；案 B 零新增直接扩域可行但须窄覆盖注记）。
2. **occurrences 口径**：扩域后按**407 根记录字段存在数**登记（p2=407、p5=211、p6=407），与 p1/p3 同域同义；**不按 sub 230 另列**。依据：rules.json 现行语义=声明域存在数；230 sub 全部同时是根（230⊂407，每父恰 1、无共享）；63 条有 p5 的根记录不被任何 sub 引用，按 230 口径会错误排除。sub230 数（存在 p2 230/p5 148/p6 230；非中性 80/148/128）作**载体分母**放批级行集元数据，不入 rules.json。
3. **候选行集**：tier B 94（Y.G. 38）独立复核全过——形状 94/94、方向 0 违例、G1′ 94/94、主张槽无缺席、active_unknown 全空；主张构成 p1×94＋p2×38＋p3×37＋p5×88＋p6×38=**295 值行**（Y.G. 92；Y.G. 无 p2/p3 主张）。扩域后 94 行**整行晋级**（不再部分晋级）；现域部分晋级=131 复现批 11。与 tier A 34 行 **cid/row/父三零交集**。shape-mismatch 58 等其他桶与扩域无关、零变化。
4. **代表样本 5 行**（Y.G. 2：30105、30102；非 Y.G. 10213/3237/1302）decoded 独立重导逐行全过：含 p2 乘算（1.5→+50%、1.05→+5%）、p5 直接加算（0.35→+35pp、0.1→+10pp）、**p6 delta 形态（2.25→+75pp、2→+50pp）**、p6 中性不写（1.5）、p5 缺席=中性、p3 受伤量口径（0.6→减伤 40%）。
5. **指标投影**（分母 41,665）：A 16,859→16,953（40.69%）；整行确认 266 不变（0.64%）；原文 A 13,859 不变；C 24,806→24,712；值行 +295。

## 下一步（实施批建议）

1. 案 A/B 裁决后改 rules.json 三键（p1/p3 零改动；p4/p7/p8 不新增）；conditions 改 p1/p3 同款域声明，「仅已核 ID」历史口径移 limits 注记。
2. tier B 94 行整行晋级：行级键建议 `inference_b12`（区别 b11），须显式处理批 11 `slot-rule-not-in-domain` hint 的替换/历史保留，勿双登记。
3. 其他桶（shape-mismatch 58、conditional 92、mixed 69、enemy 56、non-base 10、APK 27）与 adjacent 370、批 5 fam3 194 维持既有口径不入本批。
4. 归属披露（sub[] 装载无原生核实）与「推断非实机」口径原样沿用。

## 共享依赖（只读）

- `output/character_skills/profiles/rules.json`、`output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw`
- `output/ordinary_effects/ability1095/`（32 项检查仅 p1/p3）、`output/card_comparison_cid30236/{movement,critical}/`（三槽片段＋检查）
- `work/character_skills_b11_sa1095/b11_rows_classified.json`（行集入口；本批已独立复核）

## 最近更新

- 2026-10-22：前置审计完成，产出 scope/work 数据/任务卡；未 git 暂存、未改 rules.json/pages。

---

## 实施节（20261022 批 12 第一步实施员，GLM 5.3 Flash 260828，workflow 子代理，单 ask）

- 状态：**已完成（案 A 受控检查与规则管线三键扩域落地；tier B 94 行晋级待下一 ask）**
- 本轮写入：`work/character_skills_b12_1095ext/`（`b12_ext_checks.py` 新增、
  `regen_rules_b12.py` 新增、`rules_1095_keys_current.json`/`rules_diff_b12.txt`
  diff 证明中间件）、`output/ordinary_effects/ability1095/`（native_checks.json 追加
  b12_extension、trace.json 更新、README 三槽段落）、`scripts/character_skills/rules.py`
  （`_b12_1095_domain_update()`＋rules() 合并后调用）、
  `output/character_skills/profiles/rules.json`（经管线重生成）、本任务卡。

### 1. 受控检查（案 A，无新反汇编；未实机）

- 边界记录独立重导确定（decoded skilllist，与审计一致）：p2 低 75004101=1.02／高
  40633600=2.25；p5 低 75005101=0.02／高 42070800=0.8；p6 低 42081525=1.51／高
  40129301=4.5（4.5 全域仅此一条；其 p1/p3 已在既有 32 项内核对、p6 此前未核）。
- **9 项边界检查全过**（复用 LocalGuest/TimedGuest 夹具；资格/装载显式供给）：
  p2×3（1.02 真、2.25 真、2.25 假=IsEnableAbility 假不读保留 1.2）、p5×2（0.02
  seed0、0.8 seed0.25 直接加算）、p6×4（1.51 seed0、4.5 seed0.25 delta、4.5 空列表
  槽假不读不写增量不变、4.5 基础 1.5 加回 0x153b6e4）。reads 逐项断言 SOURCE 单读。
- **全域公式核对 3 项聚合**：p2 407／p5 211／p6 407 条逐记录执行既有片段窗口，
  result==float32 模型期望（max_abs_deviation=0，0 失败），逐条断言 reads 来源。
- 落盘：`native_checks.json` 既有 32 项 checks/limits **逐字节保留**，新增顶层
  `b12_extension`（关系说明＋9 项边界＋3 项聚合＋occurrences 口径＋limits 追加行）；
  `trace.json` record_count=407（不变）、present_field_count 814→**1839**
  （407×4+211）、field_summary 增 p2/p5/p6、新增 b12_extension 节（读点 RVA、
  边界检查名、全域核对、口径）。

### 2. 规则管线三键更新（rules.py 1095 键处）

- `scripts/character_skills/rules.py`：新增 `_b12_1095_domain_update(merged)` 在
  `rules()` 合并后生效（card_comparison 字典属前线生成产物，其 extend_1095 只覆盖
  p1/p3）；convert 分支零改动（语义不变）。
- 三键：`/param2` occurrences 1→407、`/param5` 1→211、`/param6` 2→407；conditions
  改 p1/p3 同款域声明（p2 门=IsEnableAbility；p5/p6 门=列表装载+类型分派命中）；
  旧「已核 ID 数 1/1/2」口径移 limits「批12扩域」注记历史保留；status/换算语义/
  evidence/origin 不变；p1/p3 及其余 279 键（含批 10 的 2003 五键）零改动。
- **diff 证明**（`work/character_skills_b12_1095ext/regen_rules_b12.py` 逐键序列化
  断言＋`rules_diff_b12.txt` unified diff）：键数 282 不变、键序不变；三键内仅
  occurrences/conditions/limits 三子键变化；rules.json SHA
  458a25681d716b2425253fe75cdf1e0411ef2bb191fb82d5f730141c2a6087a4 →
  9f1009f469e246ec26c8fbc18d7cb032c07ba40b1e5988078cff9cd2e947cb6c。
- 重建顺序：先 `scripts/ordinary_1095_probe.py`（基线），再
  `work/character_skills_b12_1095ext/b12_ext_checks.py`（追加）、
  `work/character_skills_b12_1095ext/regen_rules_b12.py`（三键）。

### 3. 回归与新证据状态

- **既有 32 项重跑无回归**：`.venv\Scripts\python.exe -B scripts/ordinary_1095_probe.py`
  输出 `{"records": 407, "fields": 814, "native_checks": 32}`，native_checks.json 与
  trace.json 重跑前后 SHA 逐字节一致（7d2f80f3…/6cf33107…，追加前基线）。
- verify_chica_comparison.py 对 1095 证据的既有断言口径（checks==32、sample_ids==8、
  p1/p3 occurrences==407）未受追加影响（b12_extension 为独立键）；**该验证脚本本轮
  未整体重跑**（需重建对照页产物，超出本步写入边界）。
- rules.json 变更会使 pages 的 dependency_signature 漂移——tier B 94 行晋级 ask
  重建 pages 时自然对齐；本步未重建 pages（禁改）。
- 剩余缺口：tier B 94 行整行晋级＋b11 hint `slot-rule-not-in-domain` 替换（下一 ask）；
  sub230 载体分母（80/148/128）入行集元数据；APK 52/35 域外维持批 11 口径。

---

## 实施节（20261022 批 12 第二步实施员，GLM 5.3 Flash 260828，workflow 子代理，单 ask）

- 状态：**已完成（tier B 94 行整行晋级；四 cohort 全量重建 0 失败；verify_full 10/10 PASS）**
- 本轮写入：`scripts/character_skills/card_page_inference_b12_1095ext.py`（新模块）、
  `card_page_inference_b11_sa1095.py`（仅 `_sample_domain_note`/`_sample_domain_summary`
  两披露句文案刷新——三键扩域后旧文案与显示值自相矛盾，见 README §25.2）、
  `card_page_data.py`（接入：批 10 gate 链之后、批 11 之前；b12 promote 分支/
  inference_b12 元数据/coverage 键；b12 非 None 时 b11 不评估）、`card_page_batch.py`
  （aggregate 两键＋plan inference_layer「十一批」＋permission_boundary 指本任务卡）、
  `card_page_policy.py`（b12 enabled/scope＋message 文案十一批）、`card_page_index.py`
  （EXPECTED_CAMPAIGN A 16,953/C 24,712/推断 2,828）、`card_page_verify_full.py`
  （aggregate 两键）、`output/character_skills/pages/`（2,236 卡重建＋README §25）、
  `work/character_skills_b12_1095ext/`（`b12_tierB_gate_check.py`/`smoke_test_b12.py`/
  `reconcile_b12.py`/`snapshot_b12.py`＋pages_before.json 快照）、本任务卡。

### 1. 重建前逐行门审核（独立复核，不信任分类文件结论）

- `b12_tierB_gate_check.py`（decoded skilllist 现值重验）：tier B **94 行（Y.G. 38）**
  形状双向 **94/94**、方向 **0 违例**、G1′ 句唯一 **94/94**、n_sub1095 **全 1**、
  与批 11 tier A 34 行 **cid/row_id/父 skillid 三零交集**；主张构成 p1×94＋p2×38＋
  p3×37＋p5×88＋p6×38＝**295 值行**（与审计一致）→ PASS。

### 2. 实施口径

- **整行晋级**：门与批 11 完全同门（复用 B11 门实现：P0 链/P1 基础句正则/P2 CACHE
  407 域/P4 形状双向＋未推广槽/P5 方向/P6 对象/G1′ 句唯一/跨 cid 守卫）；任何一门
  失败返回 None→批 11 照常接管（原 hint 口径零变化）；主张⊆{p1,p3}（tier A）返回
  None→仍由 B11 晋级（键 inference_b11，**34 行零触碰**）；仅主张含 p2/p5/p6 且全门
  通过时晋级。值行五键经 rules.py 既有换算器：p1 攻击倍率 ((原值−1)×100%)、p3 受伤量
  倍率 ((1−原值)×100%，不是固定防御量)、p2 移动乘数（×原值）、p5 暴击概率直接加算
  （pp，不套减 1.5）、p6 暴伤 delta=p6−1.5（pp）；p5/p6 中性（p5 缺席、p6=1.5）如实
  不写值。
- **行级替换不双登记**：94 行 `inference_b11_hint`（slot-rule-not-in-domain）→
  `inference_b12`（b12 非 None 时 b11 evaluate 不执行）；行级标注「推断（模板批 12
  1095 扩域）」、evidence_scope=TEMPLATE_BATCH12_1095EXT、metadata 含
  replaces_hint='inference_b11_hint' 溯源。
- **值行两层披露**：规则本体已确认（样本域扩至 407 根记录，新增 6–9 项受控检查——
  9 项边界＋p2 407/p5 211/p6 407 全域公式核对，无新反汇编）/本条归属＝推断（模板批
  12），不升确认；p2/p5/p6 值行披露扩域口径（原已核 ID 数 1/1/2→存在数 407/211/407）；
  对象=自身（rules target 逐字）；条件逐字入 note；同父其他 sub 登记不消费；
  APK 52/35 域外维持 carrier-out-of-domain hint。
- **b11 披露句刷新（对「tier A 零触碰」的如实偏离说明）**：tier A 行的样本域披露句
  动态引用 rules.json 登记值，三键扩域后旧文案「p2/p5/p6＝已核 ID 数口径」与显示值
  （407/211/407）自相矛盾；已把该句文案刷新为批 12 后语义。tier A 行级键/值行/档位/
  claims 零变化（old→new 逐行核实：34 行仅 answers 内披露句与 unknown_reasons 摘要句
  文字变化）。

### 3. 重建与对账

- 重建顺序：snapshot（pages_before.json＝批 11 终态 2,236 卡）→ 门审核 → 烟测
  （`smoke_test_b12.py` build_card 实跑不落盘：10213 五值行/30105 三值行/30102 两值行
  晋级、30002 tier A 保持、30110/1296 失败桶 hint 零变化→ PASS）→ 四 cohort
  `--execute --resume`（ge60 34/34、40to59 290/290、20to39 436/436、remaining
  1,476/1,476，0 失败）→ `card_page_index.py --execute` → `card_page_verify_full.py`
  **10/10 PASS**。
- 共三轮全量重建（接线初建→b11 披露句刷新后→family 文案修正后），本节记**终轮**；
  终轮 run_id：ge60 `20261022T005413283885Z-e8893860`、40to59
  `20261022T005428108022Z-5778b80b`、20to39 `20261022T005541927909Z-1e1bcf0b`、
  remaining/campaign `20261022T005649357100Z-0e7cf688`；签名统一
  `d65ef732ca82ffa5…`（source_signature `6b038408…`→`0653ae92…` 生成器代码变化；
  dependency_signature `bc9b353f…`→`db644d15…`＝批 12 第一步 rules.json 三键变化）；
  前两轮 run（0037–0040、0045–0048 时段）已被终轮取代。
- reconcile（`reconcile_b12.py`）：b12 晋级集↔审计 tier B **94/94 双向差集空**；
  b11 晋级 **34/34**、hint **406→312**（−94 恰 tier B 行）、其余类别关键词 0 错位、
  hint 行 answers 变化 0、双登记 0；行级变化恰 94 晋级（全部 C→A、0 坏翻转）＋34
  tier A 披露句刷新；卡级 2,236 卡 implementation_status/coverage/summary 文案（十一批）
  ＋291 卡 record_evidence 规则元数据（p2/p5/p6 conditions/limits 随 rules.json）。
- 指标（old→new；分母 N_all 41,665 不变）：A 16,859→**16,953**（40.69%）；C
  24,806→**24,712**；original_A 13,859 不变；整行推断 2,734→**2,828**；整行确认
  **266 不变**；partial_A 16,492→16,586；值行 **＋295**（verify 值相等
  9,137→9,432；1095 家族值行 34→329；p1 n=94 原值 1.2–12、p2 n=38 1.05–1.6、
  p3 n=37 0.6–0.7、p5 n=88 0.1–0.75、p6 n=38 1.9–3.5）。分 cohort b12 晋级：ge60 10、
  40to59 74、20to39 10、remaining 0。
- Y.G.：净新增 **38 行/38 cid**、净新增受益卡 **0**（38 cid 均已有批 1–11 推断行）/
  唯一 NFKC 正文新增 **2 文**；累计 **609 行/108 卡（不变）/30 文**；阶段（批 8–12）
  **331 行/100 卡/25 文**。
- rules.json：本步零改动（SHA `9f1009f4…`＝第一步终态；三键 occurrences 407/211/407）。

### 4. 遗留/未做

- 未实机、无新反汇编；父技能 sub[] 装载路径无原生核实（归属＝数据侧结构对应，
  永不据此升确认）。
- APK 52 sub/35 父域外（27 行 carrier-out-of-domain hint）本批未扩，另立小步。
- 相邻集 370 行、批 5 fam3 194 行、其他失败桶（58/92/69/56/10）与 p4/p7/p8 未推广
  槽维持既有口径。
- `verify_chica_comparison.py` 对 1095 证据的既有断言口径本批未整体重跑（同第一步
  边界）；未 git 暂存/提交。
