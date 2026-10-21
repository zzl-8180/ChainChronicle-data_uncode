# 20261021 角色技能页独立审查整改（H1/M2/M5/L1）——card_page 主线

- 负责人：H1M2修复员（主持工作流子代理，GLM 5.3 Flash）
- 状态：**整改完成（2026-10-21 终态）**：代码＋契约＋明细→四 cohort 统一重建完成（campaign 20261020T172510847737Z-a6c71db2、签名 c4bce1bb）→固定机器检查 10/10 PASS→DeepSeek 定向审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS。上部「未重建」为阶段一时点状态。
- 审查输入：`output/character_skills/review/independent_20261020_codex_audit/REPORT.md`
  §4/§5/§9（H1/M2/M5/L1 条目）及 samples.json 批 4 样本
- 允许写入：`scripts/character_skills/card_page*` 主线代码、`output/character_skills/pages/README.md`
  （schema 契约节）、`work/character_skills_audit_rectify_20261021/`、本任务卡。
  不改 pages 单卡产物、profiles/原始输入、旧审查报告；不 git 暂存提交；不开 native。

## 本轮目标与结果

针对 REPORT §9 四项整改（H1 High／M2·M5 Medium／L1 Low），只改生成器与渲染层代码并补契约文本，
**先不重建**；四 cohort 全量重建按整改计划在入口页/机器检查/分享清单阶段完成后统一执行。

## 改动清单（全部落在生成器/渲染层，产物零手改）

### H1 批 4 条件标签（High）

1. `scripts/character_skills/card_page_inference_cond.py`
   - `_promote` 条件增幅值行新增结构化 **`condition_label`**＝条件原文逐字
     （`condition_verbatim`，与 note「条件文本（逐字）」同源同值，不换算）；
   - 模块 docstring 补双字段说明。
2. `scripts/character_skills/card_page_render_v2.py`／`card_page_dbstyle_sample.py`
   - 新增 `chip_groups_html`：带 condition_label 的行首屏 chips 分组——「基础」组
     （无 condition_label 的答案）与「条件：⟨逐字条件⟩」组（按条件值分组、组内按原顺序），
     组标签首屏可见、不需展开详情；同行多条件分别分组（实测批 4 单条件链，37 行均 1 个条件组）；
     不合乘、不改证据等级；无 condition_label 的行维持原样；
   - CSS 新增 `.chip-group`/`.chip-group-label`（render_v2 常规、dbstyle `{{}}` 转义）；
   - render_v2 `run_checks` 与 dbstyle `run_checks` 各加组标签存在性检查；
   - render_v2 页脚版式声明补分组与「原文已写｜关联未知」语义说明。

### M2 逐答案 source（Medium）

3. `scripts/character_skills/card_page_inference_cond.py`
   - 新增 `_child_answer_source`：批 4 条件增幅值行（175 条）source **直接指向子记录**：
     `table/record_id/layer/source_key/json_pointer/field_path`（与 rules.json rule_key
     一致到字段）＋`record_key`（`skilllist|<子id>|<layer>|ability=<type>`）＋
     `link_kind:"sub_effect"`＋`parent_record_id`＋`link_effect_type`＋
     `raw_record_sha256`/字节范围（若可得；印章取自 link_skills `_resolve` 登记的
     `C.location`）；source_key 缺失显式失败，不静默继承父记录；
   - 基础句值行（110 条）不在此设 source，由数据层按继承契约补。
4. `scripts/character_skills/card_page_data.py` build_card 片段循环（promoted 分支后）：
   - 试点 type1017（941）＋批 3 type8（89）＋批 4 基础句（110）共 **1,140 条**（DeepSeek 复验 LOW-01 更正；175＋1,140＝1,315 与全库 diff 一致）按
     **同记录继承契约**补 source：行级 source 所指记录（推断模块 evaluate 的 record 与
     `entry['record']` 为同一对象）＋本答案 `field_path`（与 rule_key 第三段一致）＋
     `inheritance:"same_record_as_row_source"`；结构六字段同上＋record_key/
     original_file/raw_record_sha256（若可得）；批 5/6/7 自带 source 不改写。
5. `output/character_skills/pages/README.md`：新增 **§20「逐答案 source 契约与规则/归属证据分层」**
   （20.1 字段定义/继承规则/批 4 父子记录区分示例；20.2 rule_body_status 分层；
   20.3 渲染层分组与原文小字；20.4 覆盖核对），§7 消费方速查表补 3 行
   （逐答案 source／rule_body_status／condition_label）。

### M5 规则/归属证据分层（Medium）

6. 六个推断模块（`card_page_inference_1017.py`、`card_page_inference_type8.py`、
   `card_page_inference_cond.py`、`card_page_inference_b5_xtable.py`、
   `card_page_inference_b6_bossbuff.py`、`card_page_inference_b7_sympathy.py`）
   全部设 `rule_status` 的答案处新增 **`rule_body_status`**（=rules.json `rule["status"]`
   原值）；`rule_status` 保留为兼容别名（同值）。README §20.2 写明：两者只描述规则本体，
   本值归属看 `numeric_evidence`/`association_evidence`。

### L1 原文数字小字（Low）

7. 两个渲染层 `answer_chip`：`numeric_source='原文'` 且 `numeric_evidence='确认'`、
   `association_evidence='未知'` 的绿 chip 在「关联未知」旁并列小字**「原文已写」**；
   基线答案不标；确认/类型外推/推断/未知四档语义不变。
8. 两个渲染层 `ANSWER_AUDIT_LABELS` 补键：`rule_body_status`（规则本体状态）、
   `condition_label`（条件标签（原文逐字，首屏分组键））；`rule_status` 标注
   「规则状态（兼容别名，=rule_body_status）」。

## 验证（本轮实际执行；沙盒 build_card，不写 pages 产物）

- `work/character_skills_audit_rectify_20261021/sandbox_verify.py`：9 卡抽样
  （10205/1284/20624/4227/4296/8348 批 4 全形状＋10001 试点＋11212 批 3＋30236 基线/原文）
  build_card → `card_page.validate` ＋ render_v2 `run_checks` 全部 0 失败；
  批 4 卡 answers_missing_source=0、条件增幅 source 六字段齐全（APK 含 json_pointer+
  raw_record_sha256；CACHE 4227 另含字节范围）、rule_body_status==rule_status 零不一致、
  10205 chips 分组 HTML 含「基础」与「条件：HPが50％以上の時」两组、30236 页面含
  「原文已写」（REPORT L1 样例行 30236-…-pattern1-lvorder1-f0 chip 实为
  `次数：5回＋关联未知＋原文已写`）；
- `card_page_dbstyle_sample.py` 全页自检：当前 pages 三示例（30236/7616/10001）0 失败；
  沙盒 card（10205/10001，含新字段）0 失败（输出均落 work 沙盒目录）；
- 30236 有 4 条 `既有逐描述证据` 答案 `source=None`（REVIEWED_RECORD 口径，
  非推断答案，不在 M2 的 1,315 范围内；本轮不改，已有逐条 field_refs/record_id 可追溯）。

## 明细产物（`work/character_skills_audit_rectify_20261021/`）

- `missing_source_inventory.jsonl`：1,315 条逐条（试点 941＋批 3 89＋批 4 285＝基础句 110＋
  条件增幅 175）＋批 4 条件增幅补齐后 source 静态计算 175 条；
- `b4_condition_labels.json`：37 行分组/condition_label 覆盖（37/37 有逐字条件标签；
  11 种逐字条件：HPが50％/50%/25％/25%以上の時、マナを所持していると、騎士マナを所持していると、
  戦場に自身以外の味方がいると/いる場合、…魔法使い…、…<副都>所属…、状態異常の敵がいると；
  全角/半角％逐字保留，0 行多条件）；
- `cond_source_examples.json`：批 4 子记录 source 示例 30 条（含 10205 的 5 条）＋
  与沙盒实建 12 对逐字段一致核对（0 失配）；
- `sandbox_verify_result.json`、`inherited_source_samples.jsonl`（试点/批 3 继承 source 样例：
  json_pointer/raw_record_sha256 与行级 source 同记录）；
- `sandbox_pages/`、`dbstyle_out/`（沙盒渲染输出）。

## 边界与保留

- 保留全部正确原值与推断等级：raw_value/numeric_evidence/association_evidence/evidence_scope/
  note 一律不动；不合乘基础值与条件增幅、不升格「确认」；
- rule_status 原值保留（兼容别名），不删除、不改枚举；
- 未重建四 cohort（按整改计划留最后阶段统一执行）；重建后指标应零变化
  （新增字段不进任何指标分母；condition_label/source/rule_body_status 均为新增键）；
- 入口页（index/all_cards 旧 run 与计数，M1）、机器检查脚本（M1/M6）、分享清单（M4/M6）
  属后续阶段任务，本轮未动。

## 最近更新

- 2026-10-21：H1/M2/M5/L1 代码与契约落地＋沙盒验证＋明细产出；待后续阶段统一重建。

---

# 第二阶段：M1（入口页）＋M6（固定机器检查）＋交付边界（20261021）

- 负责人：入口与交付修复员（主持工作流子代理，GLM 5.3 Flash 260828）
- 状态：完成（未重建四 cohort；未 git 暂存/提交）
- 审查输入：REPORT §9 M1/M4/M6 条目、§10 整改顺序 P1「固定全量机器检查」/P2「本地交付闭环」

## M1 入口页（REPORT M1：入口旧 run 与计数）

1. `scripts/character_skills/card_page_index.py`
   - `EXPECTED_CAMPAIGN` 基线从旧迁移任务卡值（A 14,539/C 27,126/整行推断 414，对应旧 run
     20261020T091931）更新为**当前 campaign 实测值**（run 20261020T144318282523Z-bc726985，
     签名 e2aa02bb…）：A 16,205／C 25,460／整行推断 2,080／原文A 13,859／整行确认 266
     （记录级 18＋类型外推 248）／N_all 41,665——即批 5/6/7 晋级后的现值；基线存档于本节；
     不一致仍显式失败；
   - 新增可复用函数（与 batch/verify 共用）：`metric_values_from_summary`、
     `parse_entry_pointer`、`parse_entry_metrics`、`entry_pages_consistency`
     （返回 CURRENT/STALE/NOT_FOUND＋逐页明细）。
2. `pages/index.html`／`pages/all_cards.html` 已重生成（118,571 B／644,256 B）：
   指标行变为 A 16,205/41,665 · 整行确认 266 · 原文A 13,859 · C仅未知 25,460 · 整行推断 2,080；
   两页 run 指针均指向 `pages/_batch/remaining/runs/20261020T144318282523Z-bc726985/campaign_report.json`。
   生成器内置 run_checks（内嵌 JSON/跳转/头像/占位/缺图集合）写盘后通过。
3. `scripts/character_skills/card_page_batch.py` `campaign()` 最小接入：
   结果 dict 新增 `entry_pages` 字段（复用 `entry_pages_consistency`），入口页指针/指标
   过期或缺失时在 campaign_report **明确标注 STALE/NOT_FOUND** 并向 stderr 发
   `[WARN]`（含刷新指引），不静默、不中断 cohort 收尾。单测四状态：CURRENT／
   指针 STALE／指标 STALE（A 14,539 等旧值）／NOT_FOUND 全部按预期。

## M6 固定全量机器检查

4. 新建 `scripts/character_skills/card_page_verify_full.py`（只读；此后每次变更的固定回归）。
   十项检查（全 2236 卡＋入口两页，一次性跑完）：receipt 状态与签名一致（SUCCESS/无
   blocker/四签名字段==当前 campaign、run_id==所在 cohort run）、产物哈希（receipt.files
   vs 盘上 sha256）、29 项声明依赖存在＋哈希未变＋dependency_signature 复算＋campaign
   签名组成复算、行集合/row_id 唯一（card.json↔HTML data-row-id↔coverage↔campaign
   N_all）、行级/逐答案 source 解引用（指针落真实记录＋字段存在；批 5/6/7 的
   table/record_id/layer 形状经 registry 按 id 唯一定位；显式 UNKNOWN 定位单列）、
   推断答案 source 覆盖、推断答案原值与来源记录精确相等、首屏 chip 颜色档位与
   evidence 一致（逐行 chip 类多重集==按证据推导；单列「推断→绿」「确认→橙」事件）、
   四联计数与 campaign 对账（逐卡 coverage 重聚合==campaign coverage/summary，逐卡
   summary==policy.metrics）、入口页指标与 run 指针一致。输出机器可读 JSON＋逐项
   PASS/FAIL＋总判定。
   - 解引用实现细节：original_file 仅在为 JSON 文档时采用（work/ 原始 .data5 二进制
     改走 source_key/record_key 前缀映射 CACHE/→decoded、APK/→base_master）；部分来源
     json_pointer 已含字段段（落在标量），与 field 一致时视为定位到值。

### 本轮全量实测（命令：`& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_verify_full.py`）

| 检查 | 结果 | 计数 |
|---|---|---|
| receipt_signature | PASS | 2236/2236（0 blocker、0 缺 receipt） |
| artifact_hashes | PASS | 4,472/4,472 |
| dependencies_29 | PASS | 29 项全部存在、哈希未变、签名复算一致 |
| rows_rowids | PASS | 41,665 行；row_class 合计 A 16,205/C 25,460 与 campaign 一致 |
| source_dereference | **FAIL** | 65,229 解引用成功，**3 处失败**（见发现①） |
| inference_source_coverage | **FAIL** | 1,315 条推断答案无 source（发现②，与阶段一明细一致） |
| inference_value_equality | PASS | 6,017 条有 source 的推断答案原值与来源记录**全部精确相等** |
| chip_evidence_colors | PASS | 41,665 行 chip 类多重集全一致；推断→绿 0、确认→橙 0 |
| campaign_reconciliation | PASS | 2236 卡 summary 零失配；聚合==campaign；推断计数器全对上 |
| entry_pages | PASS | 入口页 CURRENT、all_cards 跳转集合==2236 manifest |

**总判定：FAIL**（由发现①②构成，均为真实交付缺口，如实暴露；修复后本脚本应 PASS）。

- 发现①（基线输入缺陷，非页面生成错误）：`pages/30236` 有 3 处「既有逐描述证据」答案的
  基线 field_refs 指向记录中不存在的字段——`/bossinfo/bosspattern/1170/scost`（bosspattern
  43023602 无 scost 键）、`/skilllist/6405/iParam0`×2（skilllist 43023608 只有 param0）。
  已对照原始记录逐一核实为真；源自 `output/card_comparison_cid30236/description_effects.json`
  基线自身的引用缺陷，页面忠实保留。基线属原始输入，本轮不改；待基线侧修正。
- 发现②：1,315 条推断答案（试点 941＋批 3 89＋批 4 285）source 缺失＝阶段一代码已就绪、
  统一重建未执行的已知缺口（与阶段一 missing_source_inventory.jsonl 完全一致）。
- 附带发现（清单侧）：页面 source 解引用实际读取、但 `card_page_dependencies.data_paths`
  未声明的 4 个解码 JSON——`denju`/`leaderabilityinfo`/`heroicskilllist`/`supporterskill`
  `.data5.json.raw`；已在分享清单列为「referenced_but_undeclared」，重建/交付需随 29 项一并提供。
- 明细报告：`work/character_skills_phase2_20261021/verify_full_latest.json`。
- 本脚本不检查（显式声明）：source 内原始字节范围/raw_record_sha256 的字节级复核、
  details 折叠层文本逐字比对、浏览器渲染交互。

## 交付边界（REPORT M4/M6：独立发行目录绑定当前源码/结果清单）

5. 新建 `output/character_skills/share_manifest_20261021/`（**本地分享清单，非发布包，
   不打包不上传**）：
   - `manifest.json`（机器可读，22,005 B）：①源码版本——24 个 `card_page*.py`（含
     inference*/render_v2/index/verify_full）＋13 个 import 闭包辅助脚本（common/rules/
     build_char_roster 等，`source_paths` 实测）的 SHA-256/字节数/git 状态；②数据依赖——
     core 4 件（profiles/records/rules/links）＋29 项声明依赖（全部含哈希，无缺失）＋
     4 项未声明但被引用的解码 JSON；③结果范围——pages/<cid>/×2236（6,708 文件
     1,920.9MB）＋index/all_cards/README＋art/×2235（6,672 文件 1,407.6MB），_batch
     明确列为默认排除（历史运行备份，REPORT 实测 171,971 文件/37.84GB/91.55%，不删除）；
     ④图片来源——art/<cid>/{card,whole,icon} ↔ full_unpack/objects/{Card_OrgSize,
     Trimmed_Whole,Card_Icon}/cha_2d_*_<cid>/ 逐字节复制（README §16.2；缺图集合按 2236
     分母：card 31 缺/whole 59103/icon 7107,8234,13001,59103）；⑤排除清单与理由；
     ⑥当前 campaign run/签名/四 cohort 状态/四联指标；⑦复现命令（batch 四 cohort→
     index→verify_full→清单重生）。
   - `README.md`：用途声明（本地分享清单、非发布）＋白名单/排除/当前指标/已知缺口
     （上述①②③）/复现命令。
   - 生成脚本：`work/character_skills_phase2_20261021/build_share_manifest.py`（暂放
     work/；如需转正建议移 `scripts/release/` 并由整合者维护）。

## 允许写入（本轮实际遵守）

`card_page_index.py`、`card_page_batch.py`、`card_page_verify_full.py`（新建）、
`pages/index.html`/`all_cards.html`（重生成）、`share_manifest_20261021/`（新建）、
`work/character_skills_phase2_20261021/`、本任务卡。未改：pages 单卡产物、profiles/
原始输入、旧审查报告、pages/README.md、其他任务卡；未 git 暂存/提交；未删除任何
历史备份（含 nul 文件——非本任务范围，留待主持处理）。

## 遗留与下一步

- 统一重建四 cohort（阶段一/二代码全部就绪后执行）→ 重跑 verify_full（预期仅剩
  发现①的 3 处基线缺陷，基线侧修正后 PASS）→ 刷新入口页与分享清单。
- 基线 `description_effects.json` 的 3 处坏 field_refs 需基线侧任务修正（不在本轮范围）。

## 最近更新（第二阶段）

- 2026-10-21：M1 入口页重生成＋batch 一致性检查接入；M6 全量机器检查脚本落地并全量
  实测（8 PASS/2 FAIL 均归因）；交付边界清单建成。

---

# 第三阶段：四 cohort 统一重建汇总与「问题—修改位置—验证结果—剩余限制」对照表（20261021）

- 负责人：整改汇总员（主持工作流子代理，GLM 5.3 Flash 260828）
- 输入：最新 campaign_report（`pages/_batch/remaining/runs/20261020T172510847737Z-a6c71db2/campaign_report.json`）
  ＋ `work/character_skills_phase2_20261021/verify_full_latest.json`（01:26:37 全量实测）
  ＋ 本阶段自跑全量对账（明细：`work/character_skills_rectify_summary_20261021/diff_rebuild_result.json`）。

## 重建事实（①—⑦ 核验）

- **① run/签名**：campaign run `20261020T172510847737Z-a6c71db2`，签名
  `c4bce1bb9c298ec9d0d353b7a7f639d61176abc6d0c1dc45fad6b46e86bd9a9f`；四 cohort 快照
  ge60=dee23041(34/34)、40to59=c45283ad(290/290)、20to39=cf540bd4(436/436)、
  remaining=a6c71db2(1476/1476)，全部 `MATCHING_SIGNATURE_SNAPSHOT`（0 STALE/0 未生成）。
- **② card.json 变化范围对账**（2236 卡全量，重建前快照取自 a6c71db2 四 cohort
  `transactions/<cid>/backup/card.json`，即整改前 bc726985 状态）：755 卡有差异，**全部
  差异仅为三种新增键**——`condition_label` 175 处（落 37 行，0 空标签）、答案级 `source`
  **恰 1,315 处**（== M2 缺口数）、`rule_body_status` 7,332 处（== 推断有 source 答案数，
  且全库 `rule_body_status==rule_status` 零不一致）；**删除/值变化/数组长度变化/越键变更
  零处**，raw_value/numeric_evidence/association_evidence/note/coverage/summary 逐字节未动。
- **③ 指标零变化**：四联指标与整改前逐项一致——全库 A 16,205/41,665、整行确认 266
  （记录级 18＋类型外推 248）、原文A 13,859、C仅未知 25,460、整行推断 2,080（campaign
  summary 与 verify campaign_reconciliation PASS 双证）。Y.G.（characters.csv title 含
  Y.G.，109 卡）整改前后逐项相等：行 5,805＝A 2,839＋C 2,966、**推断 278（行级口径，
  与审查 coverage_refined 一致）**；答案级推断 942（一行可含基础＋条件多答案），同为前后
  一致，本阶段实测（`diff_rebuild_result.json` 同法）。
- **④ receipt/哈希/依赖**：receipt_signature 2236/2236（0 blocker、0 缺 receipt、盘上
  cid 集合==manifest）、artifact_hashes 4,472/4,472、dependencies_29 PASS（29 项存在、
  哈希未变、dependency_signature 复算==记录值 `4029ad13…`、campaign 签名三段组成复算
  一致）；cohort 0 stale（见①）。
- **⑤ 机器检查明细**：10 项中 9 PASS/1 FAIL，总判定 FAIL——唯一 FAIL 为
  source_dereference 65,544 中 **3 处**（30236 基线 field_refs 指向不存在字段：`/bossinfo/
  bosspattern/1170/scost`、`/skilllist/6405/iParam0`×2，属基线输入缺陷，见下表）；其余
  9 项含 inference_source_coverage（重建后 **0 条推断答案无 source**，第二阶段的
  1,315 缺口闭合）、inference_value_equality（7,332 条有 source 推断答案原值与来源记录
  全部精确相等＝重建前 6,017＋本次补齐 1,315）、chip_evidence_colors（41,665 行全一致，
  推断→绿 0、确认→橙 0）、campaign_reconciliation（2238 项 0 失配）、entry_pages。
- **⑥ 37 行分组与 10205 父子抽验**（本阶段实跑）：37/37 行有非空逐字 condition_label
  （11 种，与阶段一 `b4_condition_labels.json` 的 11 种一致，全角/半角％逐字保留）；
  37/37 行 HTML 含「基础」与「条件：⟨逐字条件⟩」chip-group（cid 321 `<副都>` 为
  `&lt;副都&gt;` HTML 转义，实存非缺失）。10205 同行父子双记录：基础句答案 source
  `skilllist|8|/param1`→`APK/_mdSkill.json#/skilllist/7939`（record 31020500，
  `inheritance:"same_record_as_row_source"`）；条件增幅答案 source→子记录 31020501
  （`link_kind:"sub_effect"`、`parent_record_id:31020500`、`link_effect_type:36`、
  `field_path:/param1`），六字段齐全；两答案 `rule_body_status==rule_status`。
- **⑦ 入口页当前性**：index.html/all_cards.html（01:26 重生成，118,571/644,256 B）页内
  run 指针均指向 a6c71db2 campaign_report、指标行 A 16,205 等现值；verify check10
  entry_pages PASS（CURRENT）＋all_cards 跳转集合==2236 manifest。

## 对照表（问题—修改位置—验证结果—剩余限制）

| 问题（REPORT §9） | 修改位置 | 验证结果（本阶段实测） | 剩余限制 |
|---|---|---|---|
| H1 批 4 条件标签缺失（High） | `card_page_inference_cond.py`（condition_label 逐字）、`card_page_render_v2.py`/`card_page_dbstyle_sample.py`（chip_groups_html 分组＋CSS＋run_checks） | 37/37 行有逐字标签（11 种）、HTML 基础/条件分组齐全（含转义核验）；重建 diff 中 condition_label 新增 175 处/37 行、0 空标签 | 标签首屏分组不参与任何指标分母；全角/半角％并存系原文逐字保留，不做归一 |
| M2 推断答案无 source（1,315 条，Medium） | `card_page_inference_cond.py`（`_child_answer_source` 子记录直指）、`card_page_data.py` build_card（试点/批 3/批 4 基础句同记录继承契约）、README §20 | verify inference_source_coverage **0 缺失**；重建 diff 新增答案 source 恰 1,315 处；inference_value_equality 7,332 条原值全部精确相等 | 30236 另有 4 条「既有逐描述证据」答案 source=None（REVIEWED_RECORD 口径，非推断、不在 1,315 内，有 field_refs 可追溯）——维持不改 |
| M5 规则/归属证据分层（Medium） | 六个推断模块新增 `rule_body_status`（=rules.json 原值），`rule_status` 保留为兼容别名；README §20.2 | 重建新增 rule_body_status 7,332 处；全库 rule_body_status==rule_status 零不一致 | 两字段仅描述规则本体；行归属看 numeric_evidence/association_evidence（README 已写明） |
| L1 原文数字小字（Low） | 两渲染层 `answer_chip`「原文已写」并列小字＋`ANSWER_AUDIT_LABELS` 补键 | 重建后页面含「原文已写」（30236 样例行）；chip 颜色档位 41,665 行零错位 | — |
| M1 入口页旧 run/旧计数 | `card_page_index.py`（基线更新＋一致性函数）、`card_page_batch.py` campaign()（entry_pages 字段＋[WARN]） | ①—⑦ 之⑦：两页指针/指标均为当前 run，verify entry_pages PASS/CURRENT | **campaign_report 内嵌 `entry_pages` 字段为 STALE 快照**：campaign() 在 batch 收尾时先写报告（card_page_batch.py:104-105），入口页刷新是其后的独立步骤（脚本自身从不重建入口页），故该字段落后于实际页面；下次 campaign 运行会覆盖为 CURRENT。以 verify check10 实时解析为准 |
| M6 固定全量机器检查 | `card_page_verify_full.py`（新建，10 项只读检查） | 全量 2236 卡＋入口两页实测：9 PASS/1 FAIL（明细见①—⑦/⑤） | **唯一 FAIL＝3 处基线 field_refs**（`description_effects.json` 引用 `/bossinfo/bosspattern/1170/scost`、`/skilllist/6405/iParam0`×2，记录中无此键）；基线属原始输入本轮不改，需基线侧任务修正后重跑 verify 应 PASS。另：脚本第 575 行硬编码 note 仍写「1,315 已知缺口」，重建后检查已 0 失败，note 文案未随状态更新（纯文案，不影响判定） |
| M4/M6 交付边界 | `output/character_skills/share_manifest_20261021/`（manifest+README）+ `work/.../build_share_manifest.py` | 清单生成时绑定的是重建前 run bc726985/签名 e2aa02bb | **清单已过期**：建于 01:22（重建 01:25-26 之前），其 §⑥ campaign run/签名与 pages 哈希均为重建前值；需按清单 ⑦ 复现命令末步重生成清单绑定 a6c71db2 |

## 剩余缺口（按序）

1. 基线侧修正 `output/card_comparison_cid30236/description_effects.json` 3 处坏
   field_refs → 重跑 verify_full 预期 10/10 PASS。
2. 重生成分享清单（绑定 a6c71db2；`build_share_manifest.py` 建议转正移 `scripts/release/`）。
3. （文案）`card_page_verify_full.py:575` note 更新为随检查状态生成。

## 最近更新（第三阶段）

- 2026-10-21：四 cohort 统一重建（a6c71db2/c4bce1bb）＋本汇总；2236 卡 card.json 重建
  对账零违规（仅三种新增键）；Y.G. 前后逐项一致；verify 9 PASS/1 FAIL（FAIL=3 处基线
  输入缺陷）；明细 `work/character_skills_rectify_summary_20261021/diff_rebuild_result.json`。

---

# 第四阶段：source_dereference「显式登记缺失」误报修正（20261021）

- 负责人：verify修正员（主持工作流子代理，GLM 5.3 Flash 260828）
- 状态：完成（全量重跑 10/10 PASS；未改 pages/profiles/基线/其他任务产物；未 git 暂存提交）
- 背景与误报定性：第三阶段重跑唯一 FAIL 为 source_dereference ok=66544 failed=3
  （30236 基线 field_refs：`/skilllist/6405/iParam0`×2、`/bossinfo/bosspattern/1170/scost`）。
  本阶段独立核实（实读，非沿用前述结论）：
  - 三个指针的记录级部分均存在：decoded `skilllist[6405].skillid==43023608`、
    `bosspattern[1170].patternid==43023602`；`iParam0`/`scost` 键确不在记录中（`param0` 存在）；
  - 基线 `output/card_comparison_cid30236/description_effects.json` 自身对此三条显式登记
    `present:false、raw_value:null`（条目 23.field_refs.2、24.field_refs.2、57.field_refs.0），
    pages/30236/card.json 的对应 source 条目逐字携带同一登记——即项目「缺失/null/真实零
    分别处理」约定下的**有意登记缺失**，非坏指针；
  - 全 2236 卡扫描：`present:false` 的 source 条目**恰好 3 条**，全在 30236，无其他卡受影响。
  误报根源：旧检查把「字段路径在记录中不存在」一律判 FAIL，未区分「记录不存在/字段缺失
  未登记」（真 FAIL）与「字段缺失但已显式登记 present:false」（应 PASS-with-note）。

## 修改（仅 `scripts/character_skills/card_page_verify_full.py`）

1. `Check` 新增 `noted` 列表与 `note()` 方法：PASS-with-note 计入 ok、同时在报告
   `checks[].noted` 单列明细（含 field_path 与登记原文 present:false/raw_value）。
2. 新增 `field_registered_missing(src, docs)`：仅在同时满足
   ①src 显式登记 `present:false`；②json_pointer 失败发生在末段且末段==登记 field_path
   末段；③记录级指针（`location.json_pointer` 优先，缺省取父指针）可解引用；
   ④记录身份核对——解析到的记录携带表 id 键（skilllist→skillid、bosspattern→
   patternid、bossskill→skillid）且值==record_id——时判为「显式登记缺失」，否则维持 FAIL。
   条件③④防止记录缺失/指针错位被登记标记掩盖。
3. `deref_one` 新增 `NOTED` 状态：json_pointer 解引用失败但满足上述条件 → NOTED；
   记录内字段检查失败且 `present:false` → NOTED。其余解引用逻辑（registry 唯一性、
   UNRESOLVED_EXPLICIT、field_json_pointer、标量指针一致性）不变。
4. 主循环 c5 三个调用点（行 source／基线 ref 列表项／答案 source dict）接入 NOTED→
   `c5.note(...)`；模块 docstring 检查 5 说明同步更新。

## 验证（本轮实际执行）

- 负向对照矩阵（`deref_one` 直测）：登记缺失→NOTED；同指针未登记→FAIL；
  record_id 不符→FAIL；field_path 与失败末段不符→FAIL；无 location 但记录真实→NOTED。
- 全量重跑（命令：`& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_verify_full.py`）：

| 检查 | 结果 | 计数 |
|---|---|---|
| receipt_signature | PASS | 2236/2236 |
| artifact_hashes | PASS | 4,472/4,472 |
| dependencies_29 | PASS | 29 项存在、哈希未变、签名复算一致 |
| rows_rowids | PASS | 41,665 行；A 16,205/C 25,460 |
| source_dereference | **PASS** | ok=66,547（含 NOTED 3）failed=0 |
| inference_source_coverage | PASS | 0 失败（重建后无无 source 推断答案） |
| inference_value_equality | PASS | 7,332 条精确相等 |
| chip_evidence_colors | PASS | 41,665 行；推断→绿 0、确认→橙 0 |
| campaign_reconciliation | PASS | 2,238 项 0 失配 |
| entry_pages | PASS | CURRENT |

**总判定：PASS**（`work/character_skills_phase2_20261021/verify_full_latest.json`）。
无新增 FAIL；ok 66,544→66,547 恰为 3 条 NOTED 计入 ok，与改前 failed=3 对账一致。

## NOTED 3 条明细（报告 checks[source_dereference].noted 逐字）

1. `30236/30236-special_move-special_move-pattern2-lvorder2-f3` 基线ref：字段 `/scost`
   在记录 `CACHE/bossinfo.data5.json.raw#/bossinfo/bosspattern/1170` 内缺失，
   基线 field_refs 显式登记 present:false、raw_value=None（记录级指针可解）。
2. `30236/30236-ability-ability-skillid_2_-lvorder1-f3` 基线ref：字段 `/iParam0`
   在记录 `CACHE/skilllist.data5.json.raw#/skilllist/6405` 内缺失，
   基线 field_refs 显式登记 present:false、raw_value=None。
3. 同上行另一答案的同一 `/skilllist/6405/iParam0` 登记（两条答案各引用一次）。

## 边界与剩余

- NOTED 属检查口径修正（登记缺失按约定为 PASS-with-note），**不修改任何 pages 产物、
  基线文件或指标分母**；第三阶段对照表「唯一 FAIL=3 处基线 field_refs」自本节起闭合，
  基线侧无需再改。
- 负向对照保证口径未放宽：未登记缺失、记录不存在/record_id 不符仍 FAIL。

## 最近更新（第四阶段）

- 2026-10-21：source_dereference 显式登记缺失误报修正＋全量重跑 10/10 PASS。


## 审查遗留 LOW 处置（2026-10-21 主持）

- LOW-01：上文 1,130 已更正为 1,140。
- LOW-02：「基础组只含父 type8 三槽」精确化为「基础组只含父 type8 已映射 param 槽（36 行 3 槽；4296 行原文只写攻撃力と防御力，为 2 槽）」。
- LOW-03：campaign_report 内嵌 entry_pages 字段是写报告时的快照（彼时入口页指 bc726985，标 STALE）；入口页随后已重建指向 a6c71db2，实时一致性检查（card_page_verify_full.py / entry_pages_consistency）返回 CURRENT——以实时检查为准，嵌入快照仅作历史。后续运行的设计注记：入口一致性评估应在入口页重建后再写入 campaign 报告。
