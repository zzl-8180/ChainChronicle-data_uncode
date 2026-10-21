# 任务卡：批 5 前置审计——type1017 同形句跨表扩展（job_ability／supporterskill）

- 日期：2026-10-20
- 负责人／对话标识：批5跨表审计员（GLM 5.3 Flash 260828，动态工作流子代理）
- 状态：**前置审计已完成（2026-10-20 时点：未晋级、未改生成器）【2026-10-21 复核注：其后实施晋级 211 行＋hint 46，DeepSeek 审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS；过程见下文实施节】**
- 依据：`output/character_skills/inference_inventory/yg_coverage.md`（Y.G. 覆盖测量）
  §3 剩余、§4.3-1 关键结构发现、§5 批 5 建议；试点纪律
  `docs/tasks/20261020-character-skills-inference-pilot1017.md`（INFR-01/02/05/06/07）；
  批 3/批 4 前置审计同格式（`b3_type8_scope.md`、`b4_cond_scope.md`）

## 目标

对被试点表 gate（`card_page_data.py:828` `table=='skilllist'`）挡住的 job_ability／
supporterskill 两表，核实 type1017 试点严格句式的行集（全库与 Y.G. 分别计数）、
6500xxxx 链（skill_ids→skilllist 记录的 ability/参数/规则映射）、crit 变体与 fam17
的候选/规则可用性，产出批 5 晋级范围与映射设计。

## 产出（本轮实际写入）

- 范围设计：`output/character_skills/inference_inventory/b5_xtable_scope.md`
- 审计中间数据与脚本（可复跑）：`work/character_skills_b5_xtable/`
  （`scan_xtable.py`＋`xtable_rows.json`/`chain_6500.json`/`supporterskill_rows.json`、
  `audit_part3.py`＋`crit_rows.json`/`fam17_rows.json`/`fam17_yg_detail.json`/
  `crit_fam17_rows.json`/`skilllist_non1017_strict.json`、
  `classify_rows.py`＋`row_classification.json`）

## 关键结论（详见 scope §1–§4）

1. **跨表行集**：试点完整严格正则实测全库 **257** 行（job_ability 194＋supporterskill 63）、
   Y.G. **111**（108＋3）。对 yg_coverage 报告的勘误：其复扫正则缺 所属/前缀 变体，
   「剩 110／全库 271」应以 111／257（本批口径）为准；skilllist 表另有 ability≠1017 的
   严格句相邻集 210 行（Y.G. 0），不在本批。
2. **6500xxxx 链**：16 条 CACHE jobabilityinfo 记录的 skill_ids 全部指向 CACHE skilllist
   14 个 distinct 6500xxxx 记录；每条恰含 65000001（1095，第 1 段）＋65000002
   （1017，第 2 段＝严格句）；段位↔skill_ids[1] 位置对应 15/15 一致；65000002 在
   skilllist|1017 全部 5 条规则的已核样本域内（321 条含它；param2 已核 ID 显式列出）；
   records.jsonl 无 6500xxxx 表项（Y.G. 报告注记属实），但候选值已随 job_ability 片段
   cands 到达行级。
3. **crit 变体 12 行（Y.G.）**：全部同段句后有条件扩展（時の楔/ボスWAVE/地形）＋crit 属性
   在 skilllist|1017 无规则 → **全部留 hint**，不进本批。
4. **fam17 18 行（Y.G.）**：条件句（sub-party 谓词无原生证据，native_checks grep 0）＋
   18/18 句后条件扩展＋多为非首段 → **全部留 hint**；后续条件批（批 4 式）另议。
5. **批 5 晋级范围**：**211 行候选**（job_ability 194＝Y.G. 108＋86；supporterskill 17＝
   Y.G. 0，值来自共享 APK 记录 121009），46 行留 hint（所属 27＋句后文本 19）；
   值行全部「推断」、逐行注明来源记录链、不得跨记录合并（scope §5/§6）。

## 允许写入（本审计）

`work/character_skills_b5_xtable/`、`output/character_skills/inference_inventory/b5_xtable_scope.md`、
本任务卡。不改生成器/pages/profiles/共享进度文件。

## 后续（实施批另行授权）

- 批 5 实施：按 scope §5 逐行审核 211 行候选（生成器接入 job_ability/supporterskill 两表
  gate＋链解析；运行命令与验证沿用试点四 cohort 全量重建＋old→new 对账＋边界回归）。
- 延伸候选（scope §7）：jobabilityinfo 第 1 段 fam3 形状 194 行（1095 五槽规则已确认且
  已核 ID 含 65000001）——独立审计后另行批次。

## 最近更新

- 2026-10-20：审计完成。三项实测脚本全部实际执行（scan_xtable / audit_part3 /
  classify_rows，命令见 scope 头注）；257 行逐行分类落盘。

---

## 实施节（2026-10-20 批 5 实施员，GLM 5.3 Flash 260828）

- 状态：**已完成（四 cohort 全量重建＋对账复核通过）**
- 生成器改动（全部在 scripts/character_skills/ 本线）：
  - 新模块 `card_page_inference_b5_xtable.py`：严格句正则逐字节复用试点
    `card_page_inference_1017.STRICT_PATTERN`；段位公式沿用试点实现（与 TYPE8 段中句口径
    不同，为不漂移于审计行集）；句位/句后文本/同文次数/方向复用 `card_page_inference_type8`
    helpers；证据复用 `card_page_inference_1017._field_evidence`（param1/param3→
    ordinary_effects/ability1017 三件、param2→card_comparison_cid30236/movement 三件，
    缺失显式失败）。TAG=`推断（模板批 5 跨表 type1017）`、SCOPE=`TEMPLATE_BATCH5_XTABLE`。
    任务卡摘要所写「批 5 跨表 1017/1095」：值规则仅 type1017（1095 值行在 scope §7 延伸候选
    不在本批），1095 仅作为「链上其余位置记录未消费」披露出现在注记中，故行级标签不写 1095。
  - `card_page_data.py`：build_card 片段循环接入 b5（gate＝`table in B5.TABLES`，既有
    skilllist 三批 gate 与「批 4 晋级不调批 3」优先级原样）；promoted/active/evidence_label/
    hint 注记/coverage 计数器（`inference_b5_promoted/hinted`）。
  - `card_page_batch.py`：aggregate 透传 b5 计数；plan.json inference_layer/permission_boundary
    更新。`card_page_policy.py`：INFERENCE_STATUS 增 b5 scope 与 message（四批）。
    `card_page_render_v2.py`：ROW_AUDIT_LABELS 增 `inference_b5`/`inference_b5_hint`。
- 逐行审核结果：211 晋级（job 194×3 值行＝65000002/CACHE；sup 17×2 值行＝121009/APK，
  param2=1.0 未主张中性登记）＋46 hint（所属 27＋句后文本 19），与审计
  row_classification.json 逐行 decision 0 错配；crit 12 行/fam17 18 行/skilllist 相邻 210 行/
  第 1 段 fam3 194 行/5 条边界全部未动。
- 对账与复核（`work/character_skills_b5_impl/`，snapshot_old / compare_full_rows /
  check_receipts 三脚本实际执行）：
  - 行集合零增删（41,665 两侧一致）；变化行恰 257＝审计行集（0 增 0 漏、0 非批 5 变化行）；
    试点 337/批 3 40/批 4 37 晋级行零变化。
  - 指标 old→new：全库 A 14,539→14,750（+211）、C 27,126→26,915（−211）、原文A 13,859 不变、
    整行推断 414→625、整行确认 266 不变（N_all 41,665）；Y.G. 109 卡 A 2,623→2,731（+108）、
    C 3,182→3,074、整行推断 62→170、整行确认 18 不变（N_all 5,805）。
  - 2236/2236 receipt SUCCESS（单一签名）、4472 产物哈希 0 不一致、29/29 数据依赖未变
    （dependency_signature 4029ad13…）、0 stale、4 cohort MATCHING、campaign_complete=true。
  - 新签名 `a0babcc4e973ae0b54f3ecec5da3df8264593e9901e016cd790fed90421cce4e`；run_id：ge60
    `20261020T115021093461Z-dffc0e5e`、40to59 `20261020T115031890816Z-5c28a529`、20to39
    `20261020T115125602105Z-daf657b8`、remaining `20261020T115211791404Z-22d832da`。
- 实施过程记录（如实）：首轮全量重建后对账发现 37 个非批 5 变化行——实施时误删 b3 调用行
  的「批 4 晋级不调批 3」gate 条件；定位后恢复并重新全量重建，终态 0 个非批 5 变化行。
- pages/README.md 新增 §17（批 5 节）。未 git 暂存/提交；未改 profiles/原始输入/旧审查报告/
  共享进度文件/HANDOFF。
- 下一步（供排期）：scope §7 延伸候选——jobabilityinfo 第 1 段 fam3 形状 194 行（1095 五槽
  规则已确认且已核 ID 含 65000001）独立审计后另行批次；skilllist 相邻集 type1095 5 行可随
  评估。
