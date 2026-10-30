# 第三方全面审查提示词（本周期三批：S5非地形／S5地形／クリティカル吸収）

- 日期：2026-10-27。用途：用户安排第三方独立审查（非实施、非主持、非例行独审），新上下文、从原始来源核查。
- 本文件为可直接复制的提示词正文（见下分隔线内）。审查目录建议 `output/character_skills/review/direction_cycle3_20261027_thirdparty/`，如第三方在自身工作区，请其保留等价路径并回传报告。

---

你是《锁链战记》角色技能解析项目的**独立第三方全面审查者**。你不参与实施、主持或此前的例行审查；本次请用全新上下文，从原始来源独立核查，不采信任何自检、主持说明或既有审查结论（它们只是待验证对象）。项目根：`E:\代码项目\锁链战记数据解包`（Windows 中文路径；命令统一用 `./.venv/Scripts/python.exe -X utf8 -B`，避免 GBK 输出问题）。

## 一、先读（限定入口，不通读全部历史）

1. `AGENTS.md`（证据、口径与交付约定）与 `docs/角色技能完整解读实施方案.md` 的 §1、§1.1、§1.3、§4、§5、§6、§6.1。
2. `docs/tasks/character-skills-progress.md` 顶部接手摘要与核心看板。
3. 本周期三批的任务书与交付：
   - S5非地形：`docs/tasks/20261026-s5-nonterrain-batch.md`、`output/character_skills/s5_nonterrain_20261026/README.md`；例行独审 `output/character_skills/review/s5_nonterrain_20261026_deepseek/REPORT.md`。
   - S5地形：`docs/tasks/20261026-s5-terrain-batch.md`、`output/character_skills/s5_terrain_20261026/README.md` 与 `fix_record.md`；例行独审 `output/character_skills/review/s5_terrain_20261026_deepseek/REPORT.md`。
   - クリティカル吸収：`docs/tasks/20261026-crit-absorb-batch.md`、`output/character_skills/crit_absorb_20261026/README.md`；例行独审 `output/character_skills/review/crit_absorb_20261026_deepseek/REPORT.md`。
4. 选题预检（按需）：`output/character_skills/inference_inventory/chain_precheck_20261026/`、`yg_alternative_precheck_20261026/`、`g0_g1_g7_precheck_20261026/`。

## 二、送审版本（各批独立，不跨批相加）

- S5非地形：campaign `954fd03aea4b0f87e95090a55ae7cd4b39d6aaea198849a1fad3d9aff0812409`，snapshot `954fd03a-d3790431153a5dcd`。
- S5地形（含残留修正）：campaign `93eb61e10aaa…`（以最新 campaign_report 为准），snapshot `93eb61e1-d3790431153a5dcd`。
- クリティカル吸収（当前正式版）：campaign `9325cf4d00a6d24db06ce822b6d9eade8cde81e9244227fb970e14691a2fd2e9`，snapshot `9325cf4d-d3790431153a5dcd`；rules.json 290 键（SHA-16 `d3790431153a5dcd`，本周期未改）。
- 当前正式产物：`output/character_skills/pages/`（2236 卡）、`output/character_skills/effect_ledger/`（metrics：has_answer 19,592、完整 6,299、backlog 76,171、Y.G. 队列 9,520、effects 69,733、A 18,116/C 23,549、整行推断 5,634——请重算，不要照抄）。
- 原始来源：`output/cache_full_20261015_v3/decoded/`（CACHE）与 `output/base_master/`（APK），两命名空间分开，不跨层取值。

## 三、审查问题（逐项给证据，不接受"报告说通过"）

1. **主线是否推进**：三批收益是否落在 109 张 Y.G. 卡逐描述逐效果目标上；有没有为凑数放宽门控、把未知写成已知、把推断写成确认、把通用补齐当 Y.G. 收益（本周期 Y.G. 净收益很小：批1仅3行/3项、批2仅+1/+1、批3为+31项/+31行，是否如实）。
2. **数字是否真实**：分层抽样从原始记录独立重建——type28 击杀マナ確率（param0/1/2 基础阈值、param4/5 地形附加、param6 掩码 1<<n、INFERRED_SINGLE_SOURCE＋occurrences=1＋CACHE 披露）、职业位图、20612 双 type28 互补拒答（不求和不取最大）、クリティカル吸収（skilllist|65000003 ability21、param1=0.25、flag0_1=512、◆3→skill_ids[2]、conditions「仅普通65000003」与 answer_for=CONFIRMED_NUMERIC、同号不跨层）。
3. **账本集成是否窄而正确**：確率マナ獲得只覆盖 param0/1/2 与 param4/5 双 scope 且互不相交；地形主张不覆盖条件前基础概率子句（5092/7546 保持 S3）；クリティカル吸収的窄 variant 消费（binding.crit_absorb_binding 三重来源限定）使 param1 与 flag0_1 同被「回復（词表外）」消费、S4 新增为 0；其他族与既有开局/B档答案零影响。
4. **关闭是否合法**：批1 149 行关闭与 21 行未完整原因、批2 12 行关闭与 5092/7546 保持 S3、批3 0 行关闭（每行仍有クリティカル攻撃/ダメージ未解）；是否有整行/整卡冒充完成；30236/30239 零触碰（含既有命名与确认档未动）；HOLD18/C113/cost_statement 原样。
5. **防线与误桶**：boost/職業限定/時の楔/Chain/コスト/スロット/所持 是否仍被拒；8424/8425 方言、8 行无上限变体、20907 CACHE 缺失、Chain 36、type28 第三套槽位、gain_number、168 族是否原样未动；168 族冻结登记（80行/40卡/168项、准入0、可交付0、_skillChainRate 需新原生未授权）与反響变体另册是否准确。
6. **过程纪律（自动推进下重点）**：容量处置是否始终为"重复件哈希核实删除＋不同件无损搬移＋元数据全留＋回执"，有无越界删除；批1 3张 MemoryError 卡串行重试与整轮重跑是否留档；批2 ADDON_TARGETS 与 conversion 互换的残留修正（param4→param1、param5→param0+param2、param4≠param5 合成反例、14 卡逐字节不变）与 param8 文档笔误修正是否成立；批3 首建 source 形状缺陷（work/*.data5 指针）修根因并整轮重跑、首建 run 按既定模式处置；并行度是否先检后定（提交>75% 不进 jobs 4）。
7. **方向与效率**：选题方式是否健康（冻结逐效果候选清单＋消费者准入预检＋YG 净收益 vs 技能标签总数）；G0 真正载体被纠正为 skilllist|29|/param0（ExtraChainRate）是否成立；G1/G7 多为镜像/原文级绑定的判断是否准确；后续 G0-B1＋G7-B0 合并小批、G1/G7 绑定批、G7-B3 定性轨道的顺序是否合理，下一周期最该改的一件事是什么。

## 四、建议抽查样本（可按证据自行替换）

type28 阈值卡（30242/30306/30312）、地形掩码（20236/20523/6334/7248/7546）、20612 双 type28 互补、30236/30239 零触碰、5092/7546 基础概率未覆盖、クリティカル吸収 cid351 与其他代表卡、105 行关闭代表（映射批历史）、20 行开放代表（15 复合句＋5 台词）、拒答 6 行（30303/6214/7671/7658/7662/2315）、8424/8425 方言。非 Y.G. 对照与正反例按风险自取，不机械凑数。

## 五、允许与禁止

- 只读正式产物与原始记录；可重算 metrics、哈希、差异对账；可复跑 `card_page_verify_full.py`（用 `--out` 指向你自己的目录）与 A7（先按方案 §7 保存旧结果到 `acceptance/results_history/<UTC>/` 再跑并写 run_record）。
- 禁止：修改任何正式产物/脚本/rules、四 cohort 重建、删除或搬移文件、Git 操作、发布、新原生提取、联系其他对话。
- 输出：verdict（PASS / PASS_WITH_EXPLICIT_SCOPE_LIMITS / REQUEST_CHANGES）＋报告（版本、覆盖范围、逐项证据、阻塞项=根因、非阻塞项、对下一周期方向的建议）。写到你自己的审查目录 `output/character_skills/review/direction_cycle3_20261027_thirdparty/`（不存在则新建），其余一律只读。报告与证据请回传。

## 六、已登记的非阻塞项（不要重复当新阻断）

依赖签名缺口（页面生成实读 1,686 证据文件＋42 立绘未入 33 项声明依赖，已列清单）、profiles 生成器两缺陷（cid 3 崩溃、register_rule 缺 occurrences_apk）、index 基线常量统一配置化维护、原生未授权族（_skillChainRate、type52/108/117、type55 间隔、type74 反射、type103 伤害槽、1110/1111、設置/弾速）、30236 命名专项另立、首建失败原始日志未单独落盘（文档完整性）、并行度读数为运行时快照、rec0 的 4 个 cid 在 2236 cohort 之外（无页面）、容量已删除内容无法再读（只能证明登记处置符合模式）。旧 R3 与事故链已关闭不重开、HOLD18 保留。

请给出：三批是否推进主线、数字是否真实、边界是否干净、过程是否越轨、下一周期最该改的一件事。没有证据不许下结论；发现反例必须附原始来源定位。
