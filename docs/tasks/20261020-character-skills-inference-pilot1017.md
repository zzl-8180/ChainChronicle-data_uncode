# 任务卡：type1017「戦場バフ」推断层首批试点实施（批 1）

- 日期：2026-10-20
- 负责人／对话标识：type1017试点实施员（GLM 5.3 Flash 260828，动态工作流子代理）
- 状态：**已闭合（2026-10-21 复核更新）**：修复轮次与全量重建完成，DeepSeek 定向复验 PASS_WITH_EXPLICIT_SCOPE_LIMITS（晋级 337、hint 4）。过程记录见下文；上部「待复验」为该时点状态。
- 设计依据：`output/character_skills/inference_inventory/pilot_design.md`（pilot_design / TOP20 / boundaries / template_inventory，批 1 盘点产物）

## 目标

把批 1 盘点认定的 type1017「戦場バフ」纯句式家族 341 行 C 行，经模板作用域推断层晋级为
「推断」档（row_class=A、行级 evidence=推断），只升推断、绝不升确认；审核不通过的行留 hint。

## 范围

- 生效条件：`skilllist` 记录 `ability==1017`＋严格模板
  `^(その後、|さらに)?戦場にいる(味方|⟨X⟩|⟨X⟩所属(の味方)?)の(攻撃力|防御力|移動速度)(と…)*が上がる。$`＋该行晋级前无答案。
- 实测：严格命中 342 行/342 cid——口径仅指 **skilllist ability1017** 严格句（INFR-07：30236 另有 1 行同文 jobabilityinfo 严格句在试点范围外；strict 文本全表 810 行）；其中含 30236 已确认 A 行 1 行，不进入本层；试点对象 C 行 341；晋级 339，留 hint 2（20902 iParam0=22、20917 iParam0=21，「味方」句位图未覆盖全集）。
- 排除：下がる句、条件句、共鳴、元语句、type1017 更大的 2,203 行池、裸职业名/味方全員变体（不匹配严格模板）。

## 允许写入

- 脚本：`scripts/character_skills/card_page_inference_1017.py`（新建）、`card_page_data.py`、`card_page_render.py`、`card_page_policy.py`、`card_page_batch.py`
- 输出：`output/character_skills/pages/`（含 `_batch/`、`README.md`）；`work/20261020-pilot1017/`
- 本任务卡；不改共享进度文件、不动其他任务产物

## 实现

- 新模块 `card_page_inference_1017.py`：严格模板正则、句式→字段 1:1（攻撃力→/param1、移動速度→/param2、防御力→/param3，rules.json skilllist|1017 五条已确认规则）、逐行对象审核（味方→位图 31 全集；`<职业>`→恰为单位；所属→一律 hint）、属性级 hint、中性值如实登记、句外参数注记、param0 只注记。
- `card_page_data.py`：build_card 片段循环接入（仅 `table=='skilllist'` 且行无既有答案时）；promote 行 `evidence=推断`、`evidence_label=推断（模板试点 type1017）`、`numeric_evidence=推断`、`evidence_scope=[TEMPLATE_PILOT_1017]`；hint 行登记 `inference_pilot_hint`；coverage 新增 `inference_pilot_promoted/hinted`。
- `card_page_render.py`：整行证据 pill 显示 `evidence_label`；intro 补试点说明（指向 README §13）。
- `card_page_policy.py`：INFERENCE_STATUS 增加试点状态字段与说明。
- `card_page_batch.py`：aggregate 透传试点计数；plan 的 inference_layer / permission_boundary 文本更新。

## 运行命令（四 cohort 全量重建）

```
& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_batch.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --cohort <ge60|40to59|20to39|remaining> --output output/character_skills/pages --execute --resume
```

## 验证

- old→new 逐行对账与四联指标：`work/20261020-pilot1017/`（old_rows.jsonl 快照、changes JSONL、compare 脚本）。
- receipt/哈希/依赖复核脚本与结果：同目录。
- boundaries.md 5 条边界逐条复核仍拒绝。

## 最近更新

- 2026-10-20：实施完成。四 cohort 全量重建 0 失败（ge60 34/34、40to59 290/290、20to39 436/436、remaining 1476/1476）。晋级 339 行、留 hint 2 行（20902/20917）。新签名 `3374b280622d76ae89cbbb1e13bdf2d108baadd8cb9ae0cfda578fc2caf4d957`（source_signature `a8c79c17…` 因生成器变化更新；dependency_signature `4029ad13…` 不变，29/29 数据依赖逐一重算未变）。2236/2236 receipt SUCCESS、4472 产物哈希逐一核对一致、0 stale、campaign 四 cohort MATCHING_SIGNATURE_SNAPSHOT。
- old→new 对账：行集合零增删；整行多重集比对 339 晋级行全字段变化＋2 hint 行仅 unknown_reasons/新增 hint 字段变化；非试点行 41324 行逐字节零变化（含 5 条边界行；41265 为笔误，已按独立对账 41665−341=41324 更正，INFR-04）。947 条值行全部按 rules.json 换算器从原始记录再推导一致。
- 对账文件：`work/20261020-pilot1017/`（old_rows.jsonl、changes_old_new.jsonl、full_row_changes.jsonl、compare_rows.py、compare_full_rows.py、check_receipts.py、check_boundaries_and_values.py）。

## 修复轮次（2026-10-20，DeepSeek inference1017 审查 REQUEST_CHANGES 后）

审查输入：`output/character_skills/review/inference1017_20261020_deepseek/`。逐项处置（详见 `output/character_skills/pages/README.md` §13.5）：

- **INFR-01（High，已修）**：`card_page_inference_1017.py` 值行 evidence/note 按字段取 rules.json `rule["evidence"]`——param2→`output/card_comparison_cid30236/movement/` 三件、param1/param3→`output/ordinary_effects/ability1017/` 三件；证据文件缺失显式失败；`card_page_render.py` intro 与 pages/README §13.2 同步。
- **INFR-02（Medium，已修）**：值行 note 与行级 summary 逐行披露适用范围（param2 仅 2 个已核 ID、param1/param3 已核样本为 v3 CACHE 321 条，APK 173 类行属同类型外推；CACHE 行不加外推注记）；`evaluate()` 新增 layer/text 参数，`card_page_data.py` 调用点传入。不升级档位。
- **INFR-03（Medium，已修）**：`card_page_render.py` row_html A 行「数值」pill 按 numeric_evidence 取样式（确认→e-confirm/推断→e-infer/未知→e-unknown）。
- **INFR-05（Medium，已修·保守降级）**：严格句位于记录非首段◆的行降级留 hint（8157/8355；hint 写明段号与多段歧义）；晋级行登记「另含其他◆段」多段披露。晋级 339→337、留 hint 2→4。
- **INFR-04（Low，已修·文档）**：本任务卡「41,265」→「41,324」（独立对账口径 41665−341）。
- **INFR-06（Low，已修·守卫）**：全角尖括号占位（＜味方＞）归一为半角后判定；句中重复属性按字段 1:1 去重并注记。当前数据未触发（0 行变化）。
- **INFR-07（Low，已修·文档）**：本任务卡与 pages/README §13.1 「342 行/342 cid」限定为 skilllist ability1017 严格句（30236 另有 1 行同文 jobabilityinfo 严格句在范围外）。
- 单测：`work/20261020-pilot1017/test_infr_fixes.py`（10 组断言：APK/CACHE 证据与披露、8157/8355 真实记录降级、多段披露、全角归一、去重守卫、20902 型非首段＋位图双原因）全部通过。实施中发现 20902/20917 的严格句同样位于记录第 2 个◆段——降级逻辑改为追加原因而非覆盖，两行 hint 同时保留位图原因与降级原因（rows 仍维持 C，行集合与档位不受影响）。

### 修复轮次重建与复核结果（最终，2026-10-20）

- 四 cohort 全量重建 0 失败（ge60 34/34、40to59 290/290、20to39 436/436、remaining 1476/1476）。新签名 `950c3495621354febc3b1df3053fbebc205eb384431c6d7e4186ba1fbb9ad92e`（source_signature `77b9538817e7da2c…` 因生成器变化更新；dependency_signature `4029ad13…` 不变，29/29 数据依赖逐一重算未变）。2236/2236 receipt SUCCESS、4472 产物哈希逐一核对 0 不一致、0 stale、campaign 四 cohort MATCHING_SIGNATURE_SNAPSHOT。
- 指标 old→new（campaign，分母 N_all 41665）：A 14,464→14,462；C 27,201→27,203；整行推断 339→337；pilot hint 2→4（新增 8157/8355，属 20to39/remaining 各 1）；整行确认 266、原文A 13,859、N_all 不变。分 cohort 整行推断：ge60 21、40to59 132、20to39 129→128、remaining 57→56。值行 947→941（param1 338→336、param3 322→320、param2 287→285；8157/8355 各 3 行随降级移除）。
- old→new 逐行对账（事务备份全行全字段比对，`work/20261020-pilot1017/compare_fix_full.py`/`compare_final_round.py`，清单 fix_changes_full.jsonl）：行集合零增删（41,665 行两侧一致）；变化行合计 341 = 337 晋级行（answers/note 证据与适用范围披露、unknown_reasons）＋2 降级行（8157/8355，row_class A→C 等行级字段）＋2 hint 行（20902/20917，仅 unknown_reasons/inference_pilot_hint 原因文本更新）；**其余 41,324 行全行全字段逐字节零变化**（非试点行 raw_value 多重集比对零变化）。5 条边界行 12 项共享字段与试点前逐字段一致、仍拒绝。
- 最终产物抽查（全 2236 页扫描）：A 行「数值」pill e-confirm 14,125 / e-infer 337（推断行 0 个绿色 e-confirm）；941 条值行证据目录全部按字段正确（param2→movement 三件、param1/param3→ability1017 三件）；285 条 param2 值行全部带「已核 ID 仅 2 个」适用范围注记；hint 行恰为 8157/8355/20902/20917。
- 对账快照与脚本：`work/20261020-pilot1017/`（fix_old_rows.jsonl 修复前 17 键快照、snapshot_fix_old.py、compare_fix_round.py、compare_fix_full.py、compare_final_round.py、fix_changes_full.jsonl、test_infr_fixes.py）。
- 备注：`docs/tasks/character-skills-progress.md`（共享进度文件，本轮无写入权限）中「41,265」笔误与「342 行」口径由有权限的整合任务更正；pages/README.md §13 已按 INFR-04/07 同步。
