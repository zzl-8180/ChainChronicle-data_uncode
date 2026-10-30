# C8-P1 主线提速交付包任务卡

- 创建：2026-10-30。当前状态：**已验收并收口**。最终初审18条语义与固定检查全过；唯一证据哈希B1已集中修复，定向复审PASS、零阻断。
- 预检 `dwfrun-a8aae63c-b7b2-4290-b49f-7982b064a7b6` 完成：denju 首句伤害镜像余量 3 行可安全新增（全 Y.G.）——30104 t51 p0=0.5、30336 t110 p1=5、7251 t105 p1=0.83；均为首句、对象=敵、档位 1、同卡基档同记录同原值披露 slot0，0 新公式/新规则键/账本改动，预期 has_answer +3、unresolved −3、完整描述 +0（仍拆分待核查）。主持裁决：30104 以「基档 t51 p0↔小ダメージ句」先例而非 G7 形态分类作准入依据；30336 只绑 slot0（其基档 slot1 的 t13 记录不同、序列不匹配保留披露）；7251 f0 只写 f0 并披露 f2 同值异记录，不把记录不唯一升级为唯一来源。另：t27 周期回复 15 行/15 答案（353/10215/30104/30228/30257/30314 及 3 个 denju 行）作为 C8-B2 纳入，仅限 `bossskill|27|/skillparam1→回復（词表外）` 窄映射，规则 p1/p2/p3 已确认、载体链内唯一、全库 pages 0 条使用 27 键、同卡 0 披露；关联仍标推断，不写最终 HP/实机间隔。30102 因基档额外「無敵」标签不纳入；t16 泛化、adjacent-root-1095 对象不可判定、702 条粗筛域、t64 跨卡推广（同卡 0 披露）均排除。
- 授权：用户 2026-10-30「现在继续，这一次开三个周期再进行复审」。按 C8→C9→C10 顺序连续推进，三个周期完成并通过各自例行独审后，停下由用户安排独立复审，不提前开始第四个周期。
- 当前真实在途任务：无。B1 定向复审 `dwfrun-2970c985-6d0d-4e04-988f-938533e50002` 已PASS；原最终初审 REQUEST_CHANGES 与整改记录均保留。
- 主持／唯一整合者：本会话 new-provider/kimi-k3-260716。实施候选：DeepSeek V4.1 Flash `new-provider/deepseek-v4-1-flash-261017$high`。独立审查：DeepSeek V4 Pro GA `new-provider/deepseek-v4-pro-ga-260813$high`。各代理只写声明的候选输出与自身 work；共享消费者、账本和共享文件由主持整合。

## 1. 基线与检查点

- 当前产品安全检查点：C7 已完成方向审查及整改收口（`output/character_skills/c7_p3_20261030/`），最终独审 PASS、展示层复审 PASS；C7-P1 已验收＋文件交接整改完成保留为上一验收点。
- campaign `80ca83d9ecbb5e0c8a4ff3e96c60b44ec28b03cc6a1f8b8d9b2a9fff820b4e13`、snapshot `80ca83d9-cf9451c6ff47fcfb`；rules 294 键 SHA-16 `cf9451c6ff47fcfb`；has_answer 20,115（Y.G. 4,420）、unresolved 49,550（Y.G. 6,134）、backlog 75,743（Y.G. 9,415）。
- 容量上限 12 run/8 GiB 未放宽；生成后 12/12、7,781,187,902 B，下一轮正式重建前必须再按既定模式处置。性能沿用已验证 jobs 4，环境无实质变化时不重复三档全库基准。C6 仅作更早期恢复基线。

## 2. 选题规则与允许范围

- 先从 Y.G. 未解效果选题：优先证据充分可直接补答案者，其次只差少量来源/阶段核对者；非 Y.G. 仅同域低成本顺带且不延误 Y.G. 交付。
- 候选须已有公式、同层来源唯一、对象与阶段可判定；不从全库易扫族开始，不为增加数量扩大语义域。G7 与「已有公式且引用唯一」不单独决定优先级，允许替换更成熟的 Y.G. 规则族，难做不无限深挖。
- 不重复 C6/C7 已交付项；不启动新原生、30239 豁免扩大、20234 处置、Git 提交/推送、公开发布、真正增量生成或未经授权删除。保护卡、HOLD18、C113、cost_statement、旧答案与历史产物保持。
- 每个候选按可出值并绑定／仅字段值／需补证／范围外分流，记录具体原因；证据障碍只登记有限缺口，不转为非 Y.G. 主导。

## 3. 预检任务

- 输出：目标 Y.G. 卡/未解效果、选择理由、预期收益类别、非 Y.G. 连带范围与主要障碍；可执行的结构规则、原始正例/反例、不同原值、空值/null/真零、跨层同号、阶段与对象不符处理。
- 优先评估与 C7-P2/C7-P3 同门的 denju 同记录绑定或 G7 其他首段可证子族；若存在对象/阶段/竞争记录歧义，移出，不强行放行。若 G7 无安全新增，登记替换族及理由，不停在无限研究。
- 预检输出只写 `output/character_skills/c8_p1_20261030/precheck/` 与 `work/c8_p1_20261030/`；不改正式页面、账本、rules 或生产脚本。

## 4. 后续步骤与停止条件

- 预检通过后才建立 C8-B1 任务书与候选模块，按「候选实现→独立候选审查→合并冻结→一次正式重建→固定检查→最终独审→收官」执行；不为凑满三批等待未成熟子项。
- 若预检无安全新增，报告零新增并给有限替代候选；若证据冲突，保留未知，不扩大豁免或原生研究。
- 后续正式命令仅在候选审查通过后执行：`./.venv/Scripts/python.exe -X utf8 -B scripts/character_skills/card_page_batch_parallel.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --output output/character_skills/pages --execute --jobs 4`。
- **完成 C8、C9、C10 三个周期及各自独审后，停下由用户安排独立复审，不启动 C11**。
- 本卡随候选完成、独审返回、版本冻结、正式生成、终验、失败或范围变化立即更新，附实际哈希、检查证据与恢复方式。

## 5. 实施方回执（2026-10-30，V4.1 Flash；候选 → 正式生成完成）

- 状态：**候选实现＋唯一一次正式全库生成已完成（0 返修），固定检查全过，待最终独立审查**。
  交付目录 `output/character_skills/c8_p1_20261030/`（`build_report.md`、`run_record.json`、
  `dedup_proof.json`、`t27_narrow_mapping.json`、`code_snapshot/`、`pre_rebuild/`、`checks/`、
  `run_records/`、`scratch/`、`SHA256SUMS.txt`）。
- 代码：新增 `card_page_inference_c8_p1_denju.py`（`d36086d0…8d4dab`）、
  `card_page_inference_c8_p1_t27.py`（`1164012d…5c9b0c`）；`card_page_data.py`
  （`4c41ddf6…`，相对 C7-P3 快照仅 2 import＋2 apply）与 `effect_ledger.py`
  （`833c4d12…`，仅 +23 行的 1 条来源限定窄映射；反向应用本批 patch 后＝`b09bb928…`，
  与 C7-P1/P2/P3 回执一致）；
  `card_page_index.py` 仅显式更新 `EXPECTED_CAMPAIGN`（A 18,504／C 23,161／推断 6,102）。
- 正式生成（唯一一次）：`card_page_batch_parallel.py … --execute --jobs 4`，**105.2s**、
  campaign `f4e1bfb0…`、2236/2236、`campaign_complete=true`、失败列表空、四 cohort 同一签名、
  `source_signature ea484851…→150149e8…`（新增模块进 glob，预期）、`dependency_signature` 不变。
- 固定检查：账本 **9/9**（has_answer 20,115→20,133、unresolved 49,550→49,532、backlog 75,743→75,725、
  identified 69,964 不变、split 26,193 不变）；verify_full **17/17**（entry_pages=CURRENT）；
  A7 **29/29**（旧结果存 `acceptance/results_history/20261030T051018Z/`，结果哈希仍 `a84e211f…`）；
  final_diff **28/28**（范围外 2,228 卡逐字节不变、30236/30239 零触碰、HOLD18/C113/cost_statement
  由全库效应差覆盖、R01 文案逐卡不回退、隔离复跑 40 文件逐字节相同、18/18 原值逐位相等）。
- 入口页/§28/选题链：入口页显式配置生成并写盘后自检；§28 由 `regen_readme28.py` 重写；
  选题链三脚本重跑并写旁置 F03 回执（上一轮保存 `work/c8_p1_20261030/f03_previous/`）。
- 容量：生成前既定模式处置（删 4,416 重复件／保留 56 不同件／4,472 元数据全留，保留 095905/145601 基线）；
  生成后 12/12 run、7,782,478,303 B、余量 807,456,289 B，限额未放宽。
- 需主持裁决/知悉：① t51 **未**加入 `G1B1_RULE_EFFECT`（沿用同卡基档行的 quantity_kind
  词面消费路径），故账本改动只有 t27 一条窄映射；② `effect_ledger.py` 本批前基线为 `b09bb928…`，
  与 C7-P1/P2/P3 回执一致；`a40a1694…` 是 C7-P1 早态，不是本批前基线；
  ③ `denju.data5.json.raw` 仍未列入 `card_page_dependencies.data_paths`（既有残留）；
  ④ `campaign_report.entry_pages` 为 STALE 时点字段，最终态以 verify_full `entry_pages=CURRENT` 为准。

## 6. 最终验收与周期成果（2026-10-30）

- 最终初审 `output/character_skills/review/c8_p1_final_20261030_deepseek/REPORT.md`：18条答案、账本、no-op、verify_full 17/17、账本9/9、A7 29/29、隔离40文件全过；仅B1回退哈希证据REQUEST_CHANGES。
- B1整改记录 `docs/tasks/20261030-c8-p1-b1-hash-rectification.md`；定向复审 `output/character_skills/review/c8_p1_final_20261030_deepseek/RECHECK.md` verdict=PASS、blockers=0，无新阻断。原初审报告保留。
- 周期成果页 `output/character_skills/cycle_reports/C8/index.html`、剩余量页 `remaining.html`、机器数据 `report_data.json`；9个row_id/答案示例与RECHECK链接由 `verification.json` 全量复核PASS。真实浏览器DOM与答案展开通过；截图超时，未声称截图视觉验收（`browser_verification.json`）。
- 工程时间：正式全库生成105.2s、账本23.7s、入口页7.0s；生成后容量12/12、7,782,478,303 B，上限未放宽。C8-P1计2个实质语义批次，无C8-B3强制凑批。

## 7. 独立方向复审接收（2026-10-30）

- C8/C9/C10联合独立方向复审 `output/character_skills/review/direction_c8_c10_20261030_independent/REPORT.md` verdict=PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0、无正式产物修复要求；C8的18条答案全部独立成立，已关闭哈希问题无新反例，不重开。
- 数值口径：C8首次出现的`(rule_key,raw_value)`组合为t27/p1四组（1.25、1.5、1.75、2），复用既有公式，不是新公式发现；不得写为0新增唯一组合。跨效果标量新增为0，0新公式/规则键/完整描述不变。
- 接收记录 `docs/tasks/20261030-c8-c10-independent-review-closeout.md`。保持停止，不启动C11，不重新实施。
