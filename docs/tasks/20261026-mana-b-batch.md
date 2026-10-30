# 第3批：マナ B 档公式核实（start_boost/start_job/hold_mana/mana_count_up）任务书

- 日期：2026-10-26。状态：**本批收口（独立初审 PASS、零阻断，无需修复轮；周期 3/3 完成，已停下待用户安排第三方审查）**。独审 `output/character_skills/review/mana_b_batch_20261026_deepseek/REPORT.md`（dwfrun-80bdb9b0，V4 Pro GA high）：877 答案逐条独立验证 0 错误、窄集成仅三处、对账全一致、首轮范围外处置核实、保护与容量回执、verify_full 17/17 与 A7 29/29 复跑全过。实施 dwfrun-30faed74 完成。**版本**：campaign `d6b4e90385c4bb49da0c22116b67886f2355945c9125e5b36c6c80aef87d283c`、snapshot `d6b4e903-d8773bc3460da4c1`；rules 290 键（仅新增 26|param5）。

## 8. 正式收口（2026-10-26，独审 PASS）

- 877 答案逐条独立验证 0 错误：master 槽位原值＝raw_value、S1 全 param4/iParam1=31/param5=1、S2 职业位图↔句面与卡页 jobtype 逐一相等、S3 子句↔系数槽＋方向＋换算（含 kaburu 展开）、S4 96 槽非中性；isBoost 的 26|param5 仅 INFERRED_NOT_CONFIRMED 标志、数值仍绑 param0/param4。
- 窄集成仅三处（effect_ledger.py:340-369、1076-1088、1089-1130），均经 mana_b_binding 校验；范围外 41,119 行零失配、S4_unconsumed 415→415（新增/消失均 0）、開局マナ 1,209→1,607 逐条保留（注意：1,607 为映射后新口径，含本批新增消费族）。
- metrics 对账全一致：has_answer 18,628→19,355、backlog 77,123→76,397、完整 5,614→6,138、unresolved 50,224→49,895、effects 69,151→69,549、A 17,743→17,884、C 23,922→23,781、整行推断 4,904→5,450。
- 首轮 a7e823ed 误入 7 行 17 答案已修根因（ADMITTED_ROWS=546＋Nつ以上阈值门）并整轮重跑；首轮按既定模式释放、预重建页面另存。
- 独审唯一新观察（非阻塞）：build_report/README 的 before 数字误引 index 硬编码旧常量——**主持已按 ledger 真值修正**（17,743/23,922/4,904），纯文档措辞，无产物语义变化；index 基线常量统一配置化仍登记维护。
- 其余已登记非阻塞项维持。周期 3/3 完成，**已停下，待用户安排第三方审查；未获接续指令不开第 4 批**。

## 7. 生成结果（2026-10-26，metrics 实测）

- campaign `d6b4e90385c4bb49da0c22116b67886f2355945c9125e5b36c6c80aef87d283c`、snapshot `d6b4e903-d8773bc3460da4c1`；rules 290 键（SHA-16 d8773bc3460da4c1，仅新增 26|param5，旧 289 键不变、重生成幂等）。
- has_answer 18,628→**19,355**；backlog 77,123→**76,397**；完整 5,614→**6,138**；unresolved 50,224→49,895；effects 69,151→69,549；A 17,743→17,884、C 23,922→23,781；整行推断 4,904→5,450；未解析 9,067→8,939。
- 877 答案全被主张消费（S4_unconsumed 全局 415 行与批前相同，本批新增/消失均 0）；范围外 41,119 行零失配；既有開局マナ 1,209 条逐条保留；拒答 6 行/17 项状态不变（30303、6214/7671、7658/7662、2315 f1 等，原因落盘）。
- 首轮 campaign a7e823ed 误入 7 行 17 答案，已加 546 行准入＋Nつ以上阈值门并整轮重跑；首轮按既定模式释放、预重建页面另存 previous_pages_compact.json.gz。
- 保护：旧答案零丢失零改值、30236/30239 逐字节不变、HOLD18/C113/cost_statement 原样；容量两次既定模式处置（最终 12/12、used 7.68GB）。
- 未做：S5/Chain/第三套槽位/原生/cost_statement；§1.3 中文草稿随批待独审；未 Git/发布。
- 规则引用：`docs/角色技能完整解读实施方案.md`（2026-10-24 修订生效，含§1.3）；自动推进规划与用户满3批停审指示。
- 依据：`docs/tasks/20261026-mana-b-audit.md`（含四项主持裁决）与 `output/character_skills/inference_inventory/mana_b_audit_20261026/`（范围文档、batch_candidates.csv、b_readiness_rows.jsonl、verify_claims.py 62/62）。
- 当前版本：campaign `781731f3317cb9471dd167991599d192da49f7616de747c308d7b3d7b10847a2`、snapshot `781731f3-de6030e7dceb858d`；rules 289 键（本批仅允许裁决②的 26|param5 条件键新增，其他键不变）。

## 1. 范围（仅此四族）

S1 start_boost 314 行＋S2 start_job 84 行＋S3 hold_mana 116 行＋S4 mana_count_up 38 行＝**552 行/761 项（P1 14、Y.G. 9）**，以审计 `batch_candidates.csv` 与重筛实测为准。

- S2 含 42 行 isBoost（param0×param5）：按裁决②新增 `skilllist|26|/param5` 条件/标志键（类型级推断、不升确认），数值仍绑 param0，boost 条件披露；受控检查不过则这 42 行退出，不得硬出。
- 排除：Chain 36、param1+iParam0 14、S5（28 专项另立）、hold 带 param4/5 HP 回复子句 47、gain_number 1,005、cost_statement 302、qualifier 78、gain_kill/gain_job_no_number 68、地形句 15、9228 及审计排除全集。互斥分区 2,509＝724＋63＋25＋1＋252＋1,249＋117＋78，本批只取 S1–S4。

## 2. 判定与保护

- 门控按审计实测：mana_plus_bundle、level_dup/container_dup、multi_mana_carrier、无既有答案、同文组、职业位图核对、子句↔系数槽断言；charainfo/denju 记录级等价 fail-closed；同值时机不符拒答。
- 保留：旧答案零丢失零改值、范围外零变化、30236/30239 零触碰、HOLD18/C113/cost_statement 原样；開局マナ 既有 1,209 条不得被本批改写；未知保留，不填零不猜。
- rules.json 仅允许新增 26|param5 一键（条件/标志语义，证据切片 slices[5]），其余 289 键逐字节不变；需同步接入 rules.py 生成链并验证幂等（参照共鳴批 rules_integration.md）。

## 3. 写入范围

实施：`scripts/character_skills/card_page_inference_mana_b.py`（新模块）、`output/character_skills/mana_b_batch_20261026/`、自身 work；rules/rules.py 仅限裁决②；新数据输入报主持整合。独审：`output/character_skills/review/mana_b_batch_20261026_deepseek/`。

## 4. 验收与流程

实施自检三用例→四 cohort --jobs 4（campaign_complete＋2236/2236 验收）→账本/入口/选题（F03）→verify_full 17/17、账本 9/9、A7 29/29（先存旧结果）→final_diff（新增与重筛逐键相等、旧答案零改、范围外零变化、保护项原样）→隔离复跑→独审（V4 Pro GA high，初审一次＋集中修复后定向复核一次）。§1.3 中文随批验收。容量现 12/12，重建前按既定模式处置留回执。模型：实施 DeepSeek V4.1 Flash high、独审 V4 Pro GA high，显式 `$high`。

## 5. 停止边界

不做 S5/Chain/第三套槽位/新原生/cost_statement/其他词族；不 Git/UI/发布；证据冲突停车报主持。本批收口后**停下通知用户第三方审查**，不自动开第 4 批。

## 6. 主持裁决记录（2026-10-26）

- **effect_ledger 窄口径集成授权（dwfq-30faed74-1）**：S1/S2/S4 新句式与 S3「効果」展开、96 双槽答案若无账本集成会新增 595 条未消费答案、436 行新拆分（比现状更差），故批准三处窄集成（S1/S2 开局句式分支、「効果（词表外）」variant 绑定、96 攻撃力双 variant）。硬约束：仅以 mana_b_binding 标记为前提（来源限定），无合格答案行不得新增未解决主张/拆分；既有 1,209 条開局マナ与其他族零影响；探针含原错误/相邻变体/正确保留；verify_full 17/17（sync 0 失配）、final_diff 逐 id 对账且 S4_unconsumed=0；属§6完成判定变化，独审重点复核；不满足则停下，不允许降级口径凑收口。
- 实施实测（裁决时）：重筛 546/552 行（S1 314、S2 84、S3 111、S4 37）、877 条答案；rules.json 289→290（仅新增 26|param5，旧 289 键零变、重生成幂等 PASS）；scratch 32/32＋不变量 4/4；容量已按既定模式释放最老一代 4 run（12/12→8/12，回执 capacity/）。
