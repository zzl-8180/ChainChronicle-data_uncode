# 独立第三方审查提示词：角色技能页主线（整改后状态复核）

审查日期：2026-10-21。将下文直接发给审查对话即可。本提示词只授权只读核查，不授权修改正式产物、提交 Git、上传或发布。

---

你是独立第三方审查者，在新的独立上下文中工作。不要采信主持（Kimi）、实施（GLM）或此前任何审查者（含 codex_audit、各批 DeepSeek）的结论；一切从原始来源独立核查。有异议必须给出具体原值、row_id 或计算证据，不接受"因为此前审查 PASS 所以没问题"式的反驳。

## 仓库与当前终态

- 仓库根：`E:\代码项目\锁链战记数据解包`；Python 用 `./.venv/Scripts/python.exe -B`；注意 Windows GBK，建议 `PYTHONIOENCODING=utf-8` 或 `-X utf8`。
- 当前 campaign run：`output/character_skills/pages/_batch/remaining/runs/20261020T172510847737Z-a6c71db2/campaign_report.json`；签名 `c4bce1bb9c298ec9d0d353b7a7f639d61176abc6d0c1dc45fad6b46e86bd9a9f`。
- 当前指标（待你独立重算，勿采信）：2236 卡、41,665 行；A 16,205（38.9%）、整行确认 266（记录级 18＋类型外推 248）、原文A 13,859、C 25,460、整行推断 2,080（六批：337＋40＋37＋211＋1,349＋106）；Y.G. 109 卡 A 2,839/5,805、推断 278、确认 18。
- 原始来源：`output/character_skills/profiles/{profiles,records}.jsonl`、`rules.json`、`links/character_skills.jsonl`、缓存 `output/cache_full_20261015_v3/decoded/*.json.raw`、APK 主表 `output/base_master/`。

## 背景：本轮已完成的整改（这些是"待证声明"）

第三方审查（`output/character_skills/review/independent_20261020_codex_audit/REPORT.md`）提出 H1–H3/M1–M6/L1–L2 后，实施了如下整改，另有 DeepSeek 定向审查（`output/character_skills/review/rectify_20261021_deepseek/REPORT.md`）结论 PASS_WITH_EXPLICIT_SCOPE_LIMITS——**两者均只作待证声明**：

1. H1：批 4 共 37 行条件增幅值行新增 `condition_label`（条件原文逐字，11 种），首屏 chips 分「基础／条件：⟨逐字⟩」两组；声称不合乘、不升格。
2. M2：1,315 条推断答案补齐逐答案 source（六字段契约 table/record_id/layer/source_key/json_pointer/field_path）；批 4 的 175 条条件答案 source 指向子记录（如 10205 /param1→`skilllist|31020501|APK`），声称 0 条继承父记录；同记录继承 1,140 条标 `inheritance=same_record_as_row_source`。
3. M5/L1：答案新增 `rule_body_status`（=rules.json rule["status"] 原值，`rule_status` 为兼容别名）；原文绿色 chip 加「原文已写」小字。
4. M1：入口页（pages/index.html、all_cards.html）重建为当前 campaign；`card_page_batch.py` 的 campaign 完成检查新增 `entry_pages` 一致性字段。
5. 固定全量机器检查 `scripts/character_skills/card_page_verify_full.py`，当前 10/10 PASS，3 条 NOTED。
6. 本地分享清单 `output/character_skills/share_manifest_20261021/`（_batch 排除）。
7. Y.G. 研究清单 `output/character_skills/inference_inventory/yg_priority_list.md`。

## 审查任务

### A. 整改是否真实成立（重点）

1. **H1 独立核（≥10 行含 10205/20624/8348/4227）**：condition_label 是否为父记录原文与行文本的精确子串；chips 分组是否正确（基础组只含父 type8 已映射槽——注意 4296 行只有 2 槽属正确）；是否有任何合乘（父×子）、升格（推断→确认）或条件错配。
2. **M2 独立核（重点）**：批 4 条件答案 source 抽 ≥15 条独立解引用——record_id/json_pointer 是否确为子记录（父记录 `sub` 含该子记录、links 的 sub_effect 关系一致）、field_path 原值与答案 raw_value 精确相等；同记录继承抽 ≥10 条核对同 record_key 与 field_path 原值；全量扫描 7,332 条推断答案是否 0 条缺 source；批 5/6/7 原有 source（6,017 条）是否 0 改写。
3. **M5/L1**：rule_body_status 与 rules.json 原值全量一致？「原文已写」小字与「数值确认＋关联未知」是否 1:1、四档（确认/类型外推/推断/未知）语义未变？
4. **M1**：入口页指标与当前 campaign_report 实读一致；entry_pages 一致性检查的 STALE 判定逻辑是否合理（读代码即可）。

### B. 指标与覆盖率的独立重算

5. 从 2236 个 card.json 独立重算四联与 Y.G. 指标（勿用 campaign 数字当输入）；按你自己的词法口径重算"无数字量化句的补值覆盖"（参考口径见 codex_audit REPORT.md §4 与 `coverage_refined.json`；声明你的分母规则与假阳/假阴边界，不冒充人工标注）。
6. 六批分布的 Y.G. 占比独立复算（批 5–7 是否 216/1,666=12.97%；批 6 是否 83/1,349）；评估"Y.G. 优先落实为选题清单"这一纠正在数据上是否得到支撑。

### C. 研究清单与交付边界的事实基础

7. `yg_priority_list.md` 的关键事实独立抽查：Y.G. 2,066 剩余目标中含クリティカル 是否 629 行；批 6 残留 221 行中 116 行是否仅因暴击槽留 hint；skilllist|2012/param4（occ 308）、/param5（occ 311）规则是否真实存在且有证据目录；清单候选的"受益 Y.G. 卡数/唯一效果数"抽 ≥3 个候选复算。
8. `share_manifest_20261021/`：清单的源码/依赖/结果/图片版本是否与实际文件哈希一致；_batch 排除是否明确；是否存在该列未列的运行必需文件。
9. `card_page_verify_full.py`：其 10 项检查口径是否有放宽（重点核 NOTED 判定：仅当基线显式登记 present:false 且记录可解且记录 id 匹配时才 PASS-with-note；构造或找出 1–2 个反例验证"记录缺失/字段不符仍 FAIL"）。

### D. 边界与陷阱（逐项确认未犯）

- 3 条基线 field_refs（/skilllist/6405/iParam0×2、/bossinfo/bosspattern/1170/scost）是**有意登记缺失**（基线自身 present:false、raw_value:null），不是坏指针；但也请独立核实这两条记录确实存在、这些字段确实不存在。
- `rule_status`/`rule_body_status` 只描述规则本体；任何把该字段当"本值已确认"的读法都是错的——检查页面/JSON 是否有引导这种误读的地方。
- 推断行不得出现"确认"样式；确认行（记录级 18＋类型外推 248）不得出现"推断"样式。
- campaign_report 内嵌 `entry_pages` 字段是写时快照（可能标 STALE）；实时一致性检查才是当前状态——确认这个语义在文档里说清了。
- `_batch/`（约 37.8GB 历史备份）不得混入分享范围；旧审查报告与历史任务卡不得被覆盖改写。

## 方法约束

- 机器检查覆盖：receipt/哈希/依赖、行集合与 row_id 唯一、来源解引用、推断答案原值与来源记录精确相等、颜色档位与 evidence 一致、计数对账、入口页一致性。
- 人工深查仅限：上述 A/C 两节的契约项与抽查。
- 不开 native、不实机、不重跑全库统计、不做浏览器视觉验收（如做，单独标注为浏览器核验而非数据结论）。
- 只读：不改 pages/scripts/profiles/交接/旧审查报告；不 git 暂存提交；不上传发布。发现缺陷写成清单交回。

## 报告要求

- 分级结论：PASS / PASS_WITH_EXPLICIT_SCOPE_LIMITS / REQUEST_CHANGES，逐项给证据（cid/row_id/原值/指针）。
- 必须分别回答：① 整改七项是否真实成立；② 当前指标与你独立重算是否一致（列对账表）；③ Y.G. 优先的选题纠正是否有数据支撑；④ 交付边界与机器检查口径是否可靠。
- 列出你的未覆盖项与结论边界；把你的脚本与中间数据保存在 `output/character_skills/review/<你的审查id>/`（只写这个目录和你自己的 work 目录）。
- 如实区分"已独立核实"与"沿用他人证据"；后者逐条标明。
