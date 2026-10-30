# 第二周期第三方审查整改：R01/R02（＋N01）修复与定向验收

- 日期：2026-10-26。状态：**整改与原第三方复审均收口（复审 PASS，R01/R02/N01 全部关闭、阻塞 0）**。原第三方复审 `output/character_skills/review/direction_cycle2_20261026_thirdparty_recheck/REPORT.md`＋verdict.json＋closure_checks.json＋evidence_manifest.json（复审版本 campaign `f44c4089d996c8b4ce2afb46746be0dbc3d623ae67fd6ea04f76319e8d4ac4ab`、snapshot `f44c4089-d3790431153a5dcd`）；我方定向独立复核 `output/character_skills/review/cycle2_rectification_20261026_deepseek/REPORT.md`（PASS，dwfrun-e6a76f17）。实施 run `dwfrun-6be0745d-21c7-42c2-bede-24256d517bd4`（DeepSeek V4.1 Flash high）。交付 `output/character_skills/cycle2_rectification_20261026/`；rules 290键 SHA-16 `d3790431153a5dcd`；verify_full 17/17、账本 9/9、A7 29/29、final_diff PASS；R01 190条/100行/90卡、R02 绑定门＋前缀拒绝、N01 float==1.0；范围外零变化；两次正式生成同签名 4,472 逐字节，隔离 16 卡 32/32；容量两次既定模式处置后 12/12（used 7,755,532,747 B，上限未变）。未开下一批、未扩原生提取、未 Git/UI/发布。原 REQUEST_CHANGES 报告与整改过程全部保留，不改写独立审查报告。

## 7. 原第三方复审收口与 D01 修正（2026-10-26，纯文档）

- 复审独立结论：R01 190 条修正集合双向差为空、数值/来源/证据档未变、type96 合法说明保留；R02 对全部 398 条 start_boost/start_job 答案逐一执行真实 analyze_row，移除绑定标记后全部被拒，原映射批 1,209 条全保留；N01 浮点反例通过、rules 仅 param5 unit 变、旧 289 键不变；全量指标不变、保护卡字节不变；17/17、A7 29/29 复跑通过；七卡重生成 14/14 逐字节一致。复审期间原报告与正式产物未修改。
- **D01（非阻塞文档项）已修正**：整改 README §0 容量行原值 7,730,831,459 B 已标明为「第一次生成后时点」，并补复审时当前值 7,755,532,747 B／RETAINED 12/12（主持只读核对 retention/state.json：12 RETAINED、reserved_bytes=7,755,532,747、max_bytes 未变）；README 头部已补复审链接/版本/关闭结论。未重新生成页面/账本/rules、未重跑全量测试、未启动容量处置。
- 本周期到此完成；下一周期「逐效果候选清单＋消费者准入预检＋YG 净收益选题」仅保留为建议，不自动启动。

## 6. 收口与剩余不确定项（2026-10-26，定向复核 PASS）

- R01：190 条集合与 affected_answers.json 双向差为空；77 note、113 conditions 与修正文本 mismatches=0；value/raw_value/source/证据档六项对前像零变化；10209/8166/30337 真实样本独立读值核对；type96 param3(37)/param5(13) 注记逐字保留。
- R02：复核自写探针 25/25——11222 原行保持 has_answer，移除标记后不登记（S1/S3/S4 保留）、错误 family/scope/slot/record_id 不登记、Chain/スロット/コスト 前缀不登记、映射批 1,209 全保留、7211 复合句合法部分保留；effect_ledger.py:384-402（_mana_b_marker_ok）、794-808（gate 分支）审阅正确。
- N01：float==1.0 与原生 fcmp/cset eq 一致；0.0/1.5/1.999/2.0 拒、1.0 接受；rules 仅 param5 unit 变、旧 289 键指纹不变、内存重生成两遍逐字节相同；本快照 599 个已提供值全 0/1、19 缺失。
- 对账与保护：1,664 卡逐字节不变、572＝90 R01＋482 仅 unit 回显（0 违规）；30236/30239 不变；账本 41,665 行 0 状态失配、backlog 0 集合差、metrics 逐项不变；HOLD18/C113/cost_statement/拒答 6 行保持；容量两次处置逐份 sha==surviving_copy、源全在 backup/ 内。
- **剩余不确定项（非阻塞，如实保留）**：①R01 说明是对既有规则键＋原生片段的中文说明，非新原生发现；②R02 门以 B 批 binding.mana_b_binding 为准，record_id 取「存在则一致」；③N01 float 比较按 JSON float32 值 ==1.0，未验证引擎装载期其他 param5 语义；④482 卡仅 param5 unit 回显；⑤隔离复跑 16 代表卡非全量、未实机验证、入口页嵌入 campaign run id 每次重建不同；⑥容量已删除内容无法再读，只能证明登记处置符合模式、无清单外动作。
- 后续（待用户安排，不自动启动）：选题方式改为冻结逐效果候选清单＋真实消费者准入预检计算 YG 净收益；YG1 偏噪 376/393；168 项分 120 Chain/26 使用次数/22 其他（只读预检起点）；28 专项、第三套槽位原生窄目标（需用户明确原生授权）、新成果打包。
- 规则引用：`docs/角色技能完整解读实施方案.md`（2026-10-24 修订生效，含§1.3）；AGENTS.md。
- 审查交付（只读，不覆盖）：`output/character_skills/review/direction_cycle2_20261026_thirdparty/`（REPORT.md、verdict.json、evidence_manifest.json 及反例证据）。verdict＝REQUEST_CHANGES，两项阻塞 R01/R02，非阻塞 N01 同轮最小修正。
- 当前版本（整改前）：campaign `d6b4e90385c4bb49da0c22116b67886f2355945c9125e5b36c6c80aef87d283c`、snapshot `d6b4e903-d8773bc3460da4c1`；rules 290 键（SHA-16 d8773bc3460da4c1）。容量 RETAINED 12/12。

## 1. R01：说明串用类型与运算语义（实际产物错误，190 条答案/100 行/90 卡）

位置：`scripts/character_skills/card_page_inference_mana_b.py`（build_slot_answer 条件/note，审查定位 1318、1338–1341）。

- 77 条 type80 /param3 防御答案误附 type96「Skill 必杀伤害档，非必杀见 param2」注记——type80 /param3 是受伤量倍率、/param2 是移速，不是两种伤害档；type96 param3 的正确注记必须保留。
- 113 条 type80 暴击加算答案（/param7 概率 pp、/param8 暴伤系数）条件写「按原值乘入」，与主文加法矛盾——按 type/slot 写加算。
- 8166 反向（防御力と移動速度が下がる）：固定注记误写「防御力上がる／受伤量乘数<1」，须按实际增减方向生成（受伤量乘数>1 为受伤增加）。
- 原生依据：`native_excerpt_evidence.json`（type80 defence 0x1108140 读 param3、0x1108144 fmul；crit_rate 0x11195b0/crit_dmg 0x1119dc0 为 fadd）。
- 要求：按 type、slot、实际运算、增减方向生成说明；修改生成器并重生成受影响产物（不只手改 JSON/HTML）；数值、来源、推断等级、既有答案不发生无关变化。

## 2. R02：B 档开局账本分支未落实绑定门

位置：`scripts/character_skills/effect_ledger.py`（_mana_start_answer_slots、_mana_start_claim_text 及开局主张注册分支；审查定位 340、372、757 行）。

- 真实反例：11222 f0 仅移除 `binding.mana_b_binding`（其余不变）仍得 開局マナ/has_answer 且 flags=[]——必须在新增 B 档开局分支校验本批 scope/family/绑定标记。
- 合成反例：Chain/スロット/コスト 前缀＋普通开局后缀也被接纳为开局效果（仍留 S2，未整行误关）——触发词防线须覆盖"前缀＋开局后缀"形态。
- 要求：仅对新增 B 档开局分支加门；映射批原有 1,209 条合法三键答案正常消费，不得被新门误杀；不用整行黑名单误杀 7211 等复合句合法部分。
- 正反例：有标记正例、无标记、错误 family/scope、Chain/slot/cost 前缀反例、合法复合句、无 typed 答案负例（S1/S3 保留）。
- 同时验证「当前冻结数据范围外零变化」与「代码准入约束正确」两件事。

## 3. N01（同轮最小修正）：param5 浮点比较与规则文案

- `_int_slot(param5)==1` 会接纳 1.5/1.999；原生证据为 float 与 1.0 比较（0x158cbb4 fcmp s8,s9；0x158cbb8 cset w2,eq）。
- 改为与原生一致的 float==1.0 判定；新键 `skilllist|26|/param5` 的 unit 文案与 conversion 对齐（不写"整数化后与 1 比较"）。
- **仅允许修正本次新增的 param5 键，旧 289 键逐字节不变**；保留 1.5/1.999 反例；本快照 599 个已提供值全为 0/1（19 缺失），356 个 boost 答案数值不受影响，不升级成事故；不为保旧签名漏报合法修订。

## 4. 实施与验收

- 先复现反例、定位直接原因再改；三类用例（原错误/相邻变体/正确保留），预期依据语义或原始证据独立给出；保留修复前失败与修复后通过证据。
- 签名闭包纪律：代码定稿后一次正式生成，生成后不再改影响结果的代码；若必须再改，按影响范围补生成与复验。
- 重生成范围以保持页面↔账本同步为准（四 cohort --jobs 4 及账本/入口/选题/§28），不重跑历史研究；容量按既定模式处置（重复件哈希核实删除＋不同件无损保留＋元数据全留＋回执）。
- 固定检查：verify_full 17/17（第 15/17 项 0 失配）、账本 9/9、A7 29/29（先按§7保存旧结果并写 run_record）；S4 新增为 0。
- final_diff：R01 受影响 190 条答案/100 行/90 卡清单及说明修正前后对照；R02 正反例修复前后结果；旧答案无丢失无数值变化、范围外无关变化为 0；30236/30239 字节保护、HOLD18、C113、拒答 6 行保持。
- 重算 metrics 并说明预期变化与零变化；记录新 campaign/snapshot/rules 哈希，不沿用失效版本号。
- 交付：`output/character_skills/cycle2_rectification_20261026/`（修复说明、代码差异、受影响清单、探针、回执、run_record）。
- 定向独立复核（V4 Pro GA high）以第三方反例为验收基准；原报告不改写，修复回执供复核。
- 模型：实施 DeepSeek V4.1 Flash high；定向复核 V4 Pro GA high；显式 `$high`。

## 5. 边界与交接

不开下一批、不扩原生、不 Git/UI/发布；审查目录只读；不覆盖旧快照、首轮失败留档或已交付文件。出现真实写入冲突或必须扩范围时停下说明。完成后更新进度与交接，列明剩余不确定项；第三方§8 的选题方式建议（冻结逐效果候选清单＋真实消费者准入预检计算 YG 净收益；YG1 376/393；168 项分 120 Chain/26 使用次数/22 其他）仅登记为后续只读预检起点，不在本轮执行。
