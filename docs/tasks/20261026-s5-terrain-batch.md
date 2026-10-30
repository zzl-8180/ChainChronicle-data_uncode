# 新周期批2：S5 地形段＋168 族冻结登记 任务书

- 日期：2026-10-26。状态：**本批收口（独审 PASS 零阻断＋两项非阻塞残留修正复验通过；计周期 2/3）**。独审 `output/character_skills/review/s5_terrain_20261026_deepseek/REPORT.md`（dwfrun-d3323ff6，PASS）；残留修正 dwfrun-5ffd7021 完成：ADDON_TARGETS 与 conversion 对齐（param4→param1、param5→param0+param2）＋param4≠param5 合成反例（手算预期）＋14 卡逐字节不变证明（4472 文件 0 变化）、build_report §4 param8 笔误修正；修正后正式重建 campaign `93eb61e10aaa…`（以 campaign_report 为准）、verify_full 17/17（含主持 world.run 复跑）、账本 9/9、A7 29/29、final_diff PASS、隔离复跑 10/10、probe 27/27、scratch 30/30＋13/13。实施 dwfrun-92ab3393 完成。**版本**：campaign `93eb61e10aaa…`（以最新 campaign_report 为准）、snapshot `93eb61e1-d3790431153a5dcd`；rules 290 键未改（SHA-16 d3790431153a5dcd）。新周期第 2/3 批。

## 7. 正式收口（2026-10-26，独审 PASS＋残留修正复验）

- 独审六项重点全过：14 条答案原值/掩码/未知注记、双 scope 互不相交、对账（+14 答案、+12 完整、YG/P1 +1/+1）、168 族登记、并行度 jobs 2 与容量处置、§1.3 样本；verify_full 17/17 与 A7 29/29 独立复跑。
- 残留①（ADDON_TARGETS 与 conversion 互换）：修正为 param4→param1、param5→param0+param2，totals 统一走 totals_by_type；新增 param4≠param5 合成反例（手算 type0=0.35/type2=0.30/type1=0.45）与 P26/P27；首轮仅 totals 键序差异已固定 BASE_SLOTS，最终 14/14 卡与修正前逐字节相同、4472 文件 0 变化。
- 残留②（build_report §4 param8 笔误）：改为「param8 本批未登记（14 条载体无非零值），param7 已登记」；独审原报告 SHA 未改。
- 最终 metrics：backlog 76,224、has_answer 19,539、完整 6,299（与修正前一致）；A 18,063／C 23,602／整行推断 5,634；rules 290 键未改；095905 与独审送审版 145601 基线均保留。
- 批3＝クリティカル吸収（dwfrun-a108d071 在途）；满3批后停下通知用户第三方独立审查。

## 6. 生成结果（2026-10-26，metrics 实测）

- **新增 14 条答案**（param4 主槽＋param5 附加槽，raw_value=param4 原值；掩码只写 1<<param6，param3/param9 未知注记，param7/param8 登记不解释）；**12 行转完整**；**YG/P1 各 +1 行/+1 项（30242）**，不写成 +2/+2（30236 零触碰）。
- backlog 76,236→**76,224**（−12）；has_answer 19,525→**19,539**（+14）；完整 6,287→**6,299**（+12）；A 18,049→18,063（+14）、C 23,616→23,602（−14）、整行推断 5,620→5,634（+14）；效果行 +14 確率マナ獲得、其余 69,719 行不变；页面仅 14 卡 28 文件变化、其余 2,222 卡逐字节不变。
- 双 scope：S5_NONTERRAIN(param0/1/2) 与 S5_TERRAIN_20261026(param4/param5) 槽位互不相交；主张只覆盖地形条件子句＋其后玛那子句，不覆盖条件前基础概率子句（5092/7546 保持仅 S3 不越界补答）；S4 415→415（本批 0）。
- 168 族冻结登记：80 行/40 卡/168 项、准入 0 项、可交付 0/关闭 0、_skillChainRate 需新原生未授权；反響变体另册 6 行/3 卡/20 项不并入；F03 候选 110/110、78/78 不变（未改选题分类逻辑）。
- 容量：释放 4 个被取代 run（删重复 2,866 份 873MB、不同件 160 份 56MB 无损搬入、元数据 3,050 份全留、逐件哈希＋存活副本证明、回执），12/12→8/12→12/12、used 7.77GB、095905 基线未动；并行度实测写 concurrency_check.json。
- 未做：独立审查（已派发在途）、实机验证、Git/UI/发布、param7/param8 与多地形↔多位语义（需新原生未授权）。
- 规则引用：`docs/角色技能完整解读实施方案.md`（2026-10-24 修订生效，含§1.3）；自动推进规划与满3批停审指示。
- 依据：`docs/tasks/20261026-chain-precheck.md`（含主持三裁决）与 `output/character_skills/inference_inventory/chain_precheck_20261026/precheck_report.md`。
- 当前版本以批1收口后实测为准（批1前为 campaign `f44c4089d996c8b4ce2afb46746be0dbc3d623ae67fd6ea04f76319e8d4ac4ab`、snapshot `f44c4089-d3790431153a5dcd`）。容量按既定模式处置。

## 1. 范围

**S5 地形段 15 行/15 项（P1 2；预计 Y.G. +2/+2）**，以预检清单重筛实测为准。口径同批1：28 六键 occurrences=1 单来源、类型级外推不升确认、layer=CACHE 披露；概率阈值推断档＋来源；**param6≠4 只写掩码位、不写地形名**；param3/param9 语义未知写未知注记。

**168 族冻结登记（文档级，不占独立批次）**：将 `output/character_skills/inference_inventory/chain_precheck_20261026/` 的 168 项冻结清单及「消费者准入 0 项、_skillChainRate 需新原生未授权」结论写入本批 README 与进度，防止后续把 168 当可兑现预算；另册列「必殺技の威力と反響の威力と…」6行/3卡/20项变体（不并入 168）。不为其生成答案、不改选题链分类逻辑。

排除：Chain 36、第三套槽位、共鳴 C 档等原生未授权项、cost_statement、其他词族。

## 2. 判定与保护

同批1：逐行门控、单来源不外推、旧答案零丢失零改值、范围外零变化、30236/30239 零触碰、HOLD18/C113/cost_statement 原样、開局マナ与 B 档答案不改写、未知保留。rules.json 预期不改，确需变更先报主持。

## 3. 写入范围

实施：`scripts/character_skills/card_page_inference_s5_terrain.py`（新模块）、`output/character_skills/s5_terrain_20261026/`、自身 work；独审：`output/character_skills/review/s5_terrain_20261026_deepseek/`。主持：任务卡、进度、容量与共享整合。

## 4. 验收与流程

同批1：三用例→四 cohort（**并行度先检后定**：按自动推进规划§6操作规则，重建前只读检查内存空闲率/提交占比/CPU/磁盘，空闲≥40%且提交<75%且CPU<50%→jobs 4；中等→jobs 2；偏高→jobs 1 串行；检查输出写入 run_record；MemoryError 时按既有回退串行重建失败卡。当前基准 jobs 2，届时复核）→账本/入口/选题（F03）→verify_full 17/17、账本 9/9、A7 29/29（先存旧结果）→final_diff→隔离复跑→独审（V4 Pro GA high，初审一次＋集中修复后定向复核一次）。§1.3 中文随批验收（掩码位与未知注记就地）。容量按既定模式处置留回执。模型：实施 DeepSeek V4.1 Flash high、独审 V4 Pro GA high，显式 `$high`。

## 5. 停止边界

不做 Chain/第三套槽位/新原生/cost_statement/其他词族；不 Git/UI/发布；证据冲突停车报主持。本批收口计 2/3，满3批后停下通知用户第三方独立审查。
