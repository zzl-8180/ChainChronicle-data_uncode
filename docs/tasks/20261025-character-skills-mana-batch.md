# マナ族批（A 档：开局/获得法力数值）任务书

- 日期：2026-10-25。状态：**本批收口（独立初审 PASS、零阻断，无需修复轮）**。独审 `output/character_skills/review/mana_batch_20261025_deepseek/REPORT.md`（dwfrun-b8cc8091，V4 Pro GA high）。实施 dwfrun-868f1e2c 完成：重筛与审计零差异、正式重建 2236/2236、verify_full 17/17（含主持 world.run 复跑＋独审独立复跑）、账本 9/9、A7 29/29、隔离复跑 22/22。**版本**：campaign `9484664b2af92fac9008ed3fa375d082ea31165254f0474a0a5cdffdb25d030c`、snapshot `9484664b-de6030e7dceb858d`；rules 289 键未改（SHA-16 de6030e7dceb858d）。本批计新周期 1/3。

## 8. 正式收口（2026-10-25，独审 PASS）

- 独审独立复算全 2,236 卡：added=1,104／removed=0／semantic_changed=0；分族计数 param7=935（全 1.0）／param4=115（66×1+49×2）／param0=54（46×1+8×2）；载体链从解码原始记录独立重建（万象 extra_abilities→1082 str0→type26 param7=1；bond abi0→115010；变体 56000091/92、115011；param7 仅 CACHE：APK 505 条全 0、CACHE 113 条中 7 条>0）；万象 158 卡×5 档+157 羁绊=947 行无重复计数无档位错配。
- 防线逐项实测（classify_claim 直接探针）：boost／時の楔／Chain／コスト／スロット／所持／職業限定均正确拒答；复合句只绑主句；15 行残余、3 非 mana effect 项、cost_statement 302 行、Chain 36 行无新增答案。
- 105 行：answer_unchanged 105/105、flag_closed_after 0、split_flags=[S1,S3]；账本 has_answer 17,419／backlog 78,313 不变且披露一致，无冒充账本完成。
- 零变化与保护：全卡 removed=0／语义改 0／范围外逐字节 0；30236/30239 逐字节相同（description_effects.json SHA 未变）；HOLD18／C113 原样。§1.3 抽样通过。
- **非阻塞残留**：①模块 UNKNOWNS 全族共享，全職業/素マナ答案携带无关的「万象玛那属性标志8」未知项（纯文案冗余，下一批顺带修，验证无语义变化）；②其余已登记项维持（依赖签名缺口、profiles 两缺陷、index 基线、B/C 与原生未授权、param1+iParam0/isBoost 未消费）。
- **后续窄门任务（独审建议，主持采纳为下一批）**：mana 效果类型接入 effect_ledger——仅按 rule_key 精确映射 skilllist|26|/param0|param4|param7 三键，**不得整族映射 type26**（防 boost/job/wedge 误关）；15 行复合句与 3 非 mana 项保持 S3 开放；105 行关闭动作属账本词表变更须独立审查；新增类型对 metrics.by_type 与 has_answer/backlog 的影响单列对账。
- 本批未做：B/C 档、原生、cost_statement、Git、发布、UI。

## 7. 生成结果与主持注记（2026-10-25）

- **新增 1,104 条公式级答案**（范围 1,209 行＝1,221 扣 30236/30239 的 12 行零触碰排除；万象 158 卡×主张分组、全职业、素マナ新绑定 39 行等）；行证据档 原文数字（未知）→推断 1,104 行（未知 37,599→36,495、推断 3,800→4,904），A/C 与完整度不变。
- **账本口径重要说明**：effect_ledger 无 skilllist|26 效果映射，页面答案未进入账本 has_answer（17,419 不变）、backlog 78,313 不变；105 行已有 26|param0 答案值不变、拆分标志未关闭（S1+S3 保留），逐行依据在 `plain_105_flag_basis.jsonl`。映射新增属§6 独立审查范围，本批未做——独审重点评估此状态的披露与后续映射必要性。
- 30236/30239 各 6 行按零触碰整卡排除（主持认可该保守处置），其万象行保留拆分；旧答案零丢失零改值、范围外零字节变化、HOLD18/C113/cost_statement 302 行原样。
- 容量现 12/12（7.60GB/8GiB）；检查工具两处自身缺陷已修根因并重跑整套（生成物未见缺陷，未重跑生成）。
- 未消费：Chain 36（B）、第三套槽位/isBoost、28、時の楔、cost_statement；未做原生、Git、发布。
- 规则引用：`docs/角色技能完整解读实施方案.md`（2026-10-24 修订生效，含 2026-10-25 §1.3 补充）；自动推进规划 `docs/tasks/20261025-mainline-autopilot-plan.md`。
- 依据：`docs/tasks/20261025-mana-readonly-audit.md`（含三项主持初裁）与 `output/character_skills/inference_inventory/mana_audit_20261025/`（范围文档、candidates.jsonl 5,752 条、可复跑脚本；dwfrun-6162eb76）。

## 1. 目标与范围

把マナ族（マナ·時の楔及相邻词族）中证据就绪的 A 档效果接入规则与答案。审计口径 A 档上限 1,257 行/1,260 项（P1 642），本批实际范围为其中扣除初裁降 B 的 Chain マナ獲得 36 行后的约 **1,221 行**（以新账本复跑重筛实测为准）：

- 万象マナ開始 947 行＝158 卡同句（按初裁③：卡×主张登记一次、5 档分行引用各自载体，双口径计数）；
- 全職業マナ開始 115 行；
- 素マナ開始残余 159 行（其中 105 行已有 26|param0 答案，仅差关闭拆分标志——完成判定变化属§6独立审查范围，逐行给依据）。

**开工硬前置**：共鳴批已改 rules 与账本，必须先在新 snapshot（当前 `03172aef-de6030e7dceb858d`）复跑审计目录脚本重筛，逐项对账（审计锚点 ff178894 → 当前），不得直接搬旧数字。

**不在本批**：B 档公式核实 2,509 行（含 Chain 36、第三套槽位 param1＋iParam0 与 param0×param5(isBoost) 变体——26 五键未覆盖，先核证据再定）、C 档 1,714 行（含時の楔 80 行，原生单独授权）、cost_statement 302 行（初裁①保持不动）、B/C 档以外的词族扩展。

## 2. 判定与保护（§4）

- 已确认消费链：skilllist|26（param0 9/9 原生、param4＋iParam1 成对）及二级链 extra_ability_info.extra_abilities[N].skill_ids[]／supporterskill.abi0/abi1 经 1082 包装 str0 转发（审计解析 1,474/1,490、262/266）；28 六键仅单来源（43023602），不得外推。
- 误桶防线（审计实测）：同值命中不等于本族——cost_reduce 146 行分散 20+ 类型且 74|skillparam6 恒 1；41 行 Chain/WAVE 获得句同值命中开戦型 26 但时机不符（已降 B）；竞争句/charainfo 记录级等价/multi-carrier 逐行门控。
- 保留：旧答案零丢失零改值、范围外零变化、30236/30239 零触碰、HOLD18 与 C 批 113 遗留原样；未知保留，不填零不猜；同值时机不符不得出答案。

## 3. 写入范围

- 实施：`scripts/character_skills/card_page_inference_mana.py`（新模块）、`output/character_skills/mana_batch_20261025/`、自身 work；rules.json 仅限已确认语义的新键/升级（diff 证明旧键不变；需超出现有 26/28 键先报主持）；新数据输入由主持整合进依赖签名。
- 独审：`output/character_skills/review/mana_batch_20261025_deepseek/` 与自身 work。
- 主持：任务卡、进度、容量与共享整合。

## 4. 模型与流程

实施 new-provider/deepseek-v4-1-flash-261017 high；独审 new-provider/deepseek-v4-pro-ga-260813 high（独立新上下文）；显式 `$high`。流程按方案§5：实施自检三用例→四 cohort 重建（--jobs 4）→账本/入口/选题→17/17、9/9、A7 29/29（先存旧结果）→独审（初审一次＋集中修复后定向复核一次）→收官。新增答案中文说明按§1.3随批验收（多档位成组、对象/数值/条件/未知就地）。

## 5. 容量与周期

现 RETAINED 8/12；正式重建前若需预约，按既定模式另列精确清单处置（重复件删除＋不同件保留＋元数据全留＋回执）。本批为实质解析批，计入新方向复核周期（当前新周期 0/3，方向复核收口后计 1/3）。

## 6. 停止边界

不做 B/C 档、新原生、cost_statement；不动 HOLD18、③、Git、UI、发布；证据冲突（档位映射、槽位变体、转发链断裂）停车报主持，不硬猜。
