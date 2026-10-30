# 第三方全面审查提示词（本周期三批：マナ批／映射批／B档批）

- 日期：2026-10-26。用途：用户安排第三方独立审查（非实施、非主持、非例行独审），新上下文、从原始来源核查。
- 本文件为可直接复制的提示词正文（见下分隔线内）。审查目录建议 `output/character_skills/review/direction_cycle2_20261026_thirdparty/`，如第三方在自身工作区，请其保留等价路径并回传报告。

---

你是《锁链战记》角色技能解析项目的**独立第三方全面审查者**。你不参与实施、主持或此前的例行审查；本次请用全新上下文，从原始来源独立核查，不采信任何自检、主持说明或既有审查结论（它们只是待验证对象）。项目根：`E:\代码项目\锁链战记数据解包`（Windows 中文路径；命令统一用 `./.venv/Scripts/python.exe -X utf8 -B`，避免 GBK 输出问题）。

## 一、先读（限定入口，不通读全部历史）

1. `AGENTS.md`（证据、口径与交付约定）与 `docs/角色技能完整解读实施方案.md` 的 §1、§1.1、§1.3、§4、§5、§6、§6.1。
2. `docs/tasks/character-skills-progress.md` 顶部接手摘要与核心看板。
3. 本周期三批的任务书与交付：
   - マナ批：`docs/tasks/20261025-character-skills-mana-batch.md`、`output/character_skills/mana_batch_20261025/README.md`；例行独审 `output/character_skills/review/mana_batch_20261025_deepseek/REPORT.md`。
   - 账本映射批：`docs/tasks/20261026-mana-ledger-mapping.md`、`output/character_skills/mana_ledger_mapping_20261026/README.md`；例行独审 `output/character_skills/review/mana_ledger_mapping_20261026_deepseek/REPORT.md`。
   - 第3批 B 档：`docs/tasks/20261026-mana-b-batch.md`、`output/character_skills/mana_b_batch_20261026/README.md`；例行独审 `output/character_skills/review/mana_b_batch_20261026_deepseek/REPORT.md`。
4. 相关依据（按需）：`output/character_skills/inference_inventory/mana_audit_20261025/`、`output/character_skills/inference_inventory/mana_b_audit_20261026/`（两次只读审计）。

## 二、送审版本（各批独立，不跨批相加）

- マナ批：campaign `9484664b2af92fac9008ed3fa375d082ea31165254f0474a0a5cdffdb25d030c`，snapshot `9484664b-de6030e7dceb858d`。
- 映射批：campaign `781731f3317cb9471dd167991599d192da49f7616de747c308d7b3d7b10847a2`，snapshot `781731f3-de6030e7dceb858d`。
- B 档批（当前正式版）：campaign `d6b4e90385c4bb49da0c22116b67886f2355945c9125e5b36c6c80aef87d283c`，snapshot `d6b4e903-d8773bc3460da4c1`；rules.json 290 键（仅新增 `skilllist|26|/param5`）。
- 当前正式产物：`output/character_skills/pages/`（2236 卡）、`output/character_skills/effect_ledger/`（metrics：has_answer 19,355、完整 6,138、backlog 76,397、Y.G. 队列 9,556、effects 69,549、A 17,884/C 23,781、整行推断 5,450——请重算，不要照抄）。
- 原始来源：`output/cache_full_20261015_v3/decoded/`（CACHE）与 `output/base_master/`（APK），两命名空间分开，不跨层取值。

## 三、审查问题（逐项给证据，不接受"报告说通过"）

1. **主线是否推进**：三批收益是否落在 109 张 Y.G. 卡逐描述逐效果目标上；有没有为凑数放宽门控、把未知写成已知、把推断写成确认。
2. **数字是否真实**：分层抽样从原始记录独立重建——万象（extra_abilities→1082 str0→type26 param7、158 卡×5 档＋羁绊分组是否有重复计数或档位错配）、全职业（param4＋iParam1=31）、素マナ（param0）、start_boost（param4/param5）、start_job（职业位图↔句面）、hold_mana、mana_count_up（96 双槽）；isBoost 的 `26|param5` 是否仅作条件标志且数值仍绑 param0/param4、未升确认。
3. **账本集成是否窄而正确**：映射批仅 `skilllist|26|/param0|param4|param7` 三键；B 档批仅三处（开局句式来源限定主张、効果展开 variant、96 双攻击槽 variant）；无整族/词面扩域；无合格答案的行不得新增未解决主张；`S4_unconsumed_typed_answers` 本批新增为 0；page↔ledger 同步（第 15/17 项检查）是否真为 0 失配。
4. **关闭是否合法**：1,189 行关闭（映射批）与 B 档批关闭行是否全部子句覆盖；20 行保持开放（15 复合句＋5 台词行）是否成立；105/105 bare 行；6058/7014/7211 的 S3 消失但行仍开放是否正确；13 行无三键答案行（30236×6/30239×6/323）保留 S1/S3 是否确为保守必需；拒答 6 行/17 项是否未获答案。
5. **防线与误桶**：boost/職業限定/時の楔/Chain/コスト/スロット/所持 是否仍被拒；Chain 36、type28、第三套槽位 param1+iParam0、isBoost 变体、gain_number、cost_statement 302 行是否原样未动。
6. **保护项**：旧答案零丢失零改值、范围外零变化、30236/30239 逐字节不变、HOLD18 与 C 批 113 遗留原样、rules 旧 289 键不变（B 档批仅 +1 键且重生成幂等）。
7. **过程纪律（自动推进下重点）**：容量处置是否始终为"重复件哈希核实删除＋不同件无损搬移＋元数据全留＋回执"，有无越界删除；B 档批首轮误入 7 行范围外（17 答案）是否修根因并整轮重跑、首轮留档；A7-4 夹具改为确定性选取后断言语义是否不变、无候选是否 FAIL；批次文档 before 数字曾误引 index 旧常量，是否已按 ledger 真值修正。
8. **方向与效率**：选题与审计方法是否健康（参考共鳴批"估计 549→实际 8"的教训）；机械分档估计是否只作线索；研究/中间池是否应持久化逐项清单；YG1 主分类偏噪（376/401 仅凭 skill_tag）与 168 项「必殺技の威力…」改派 Chain/超共鳴专项的建议是否成立、应如何排期。

## 四、建议抽查样本（可按证据自行替换）

万象 20628/10026/2243、S2 职业位图代表、S4 96 双槽代表、isBoost 11222、105 行关闭代表、20 行开放代表（2068/8190/8193/8204/13005 任一）、6058/7014/7211、拒答 6 行（30303/6214/7671/7658/7662/2315）、30236/30239/323 零触碰。非 Y.G. 对照与正反例按风险自取，不机械凑数。

## 五、允许与禁止

- 只读正式产物与原始记录；可重算 metrics、哈希、差异对账；可复跑 `card_page_verify_full.py`（用 `--out` 指向你自己的目录）与 A7（先按方案 §7 保存旧结果到 `acceptance/results_history/<UTC>/` 再跑并写 run_record）。
- 禁止：修改任何正式产物/脚本/rules、四 cohort 重建、删除或搬移文件、Git 操作、发布、新原生提取、联系其他对话。
- 输出： verdict（PASS / PASS_WITH_EXPLICIT_SCOPE_LIMITS / REQUEST_CHANGES）＋报告（版本、覆盖范围、逐项证据、阻塞项=根因、非阻塞项、对下一周期方向的建议）。写到你自己的审查目录 `output/character_skills/review/direction_cycle2_20261026_thirdparty/`（不存在则新建），其余一律只读。报告与证据请回传。

## 六、已登记的非阻塞项（不要重复当新阻断）

依赖签名缺口（页面生成实读 1,686 证据文件＋42 立绘未入 33 项声明依赖，已列清单）、profiles 生成器两缺陷（cid 3 崩溃、register_rule 缺 occurrences_apk）、index 基线常量统一配置化维护、S5(type28)/Chain/第三套槽位/共鳴 C 档等原生未授权、旧 R3 与事故链已关闭不重开、HOLD18 保留。

请给出：三批是否推进主线、数字是否真实、边界是否干净、过程是否越轨、下一周期最该改的一件事。没有证据不许下结论；发现反例必须附原始来源定位。
