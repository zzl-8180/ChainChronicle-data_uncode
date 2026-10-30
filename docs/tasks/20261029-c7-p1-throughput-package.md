# C7-P1 主线提速试行交付包任务卡

- 创建：2026-10-29。当前状态：**已验收收口，最终独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断；文件交接整改 R1/R2/R3 及外部最终定向复核均已完成**；run_record state＝ACCEPTED。**当前真实在途任务：无（不重复派发已完成实施或审查；不启动 C7-P2）。**独立效率复核 `docs/tasks/20261029-c7-p1-throughput-independent-report.md` verdict＝REQUEST_CHANGES（交接状态、冗余哈希、恢复说明）→ 已完成定向整改，外部最终定向复核 verdict＝PASS（仅针对文件交接整改），交接阻断已关闭。产品本身仍保留原 PASS_WITH_EXPLICIT_SCOPE_LIMITS，不扩大语义结论；原独立审查报告与历史 REQUEST_CHANGES 不追改。
- 最终独审 `dwfrun-77c21f27-d0bd-4ec7-b7d4-9f9ea5a79e96`（V4 Pro GA high），报告 `output/character_skills/review/c7_p1_final_20261029_deepseek/REPORT.md`：2 条新答案回源、7251 去重、账本指标、保护项、容量与正式生成一次均通过；仅凭文件接手核对通过。**外部最终定向复核 verdict＝PASS（仅针对文件交接整改）**，确认交接阻断已关闭，不是新增语义或生产验证。非阻塞残留：①任务卡部分状态行更新滞后（本次已回填）；②formal_build_run_record.json 的 run_at_local 晚于 campaign/账本/A7 时间戳，按记录落盘时间理解，不影响产物；③final_diff B5 detail 仅写「answer_refs已核」未展开，但两新增数值已由独审回源确认；④「越权362条」为实施修复前中间态自述，最终根因消除，不构成产品反例。
- 合并实施 `dwfrun-7b95d44d-9aa3-4751-883c-6381b3a80324` 完成：新 campaign `bf1dc4ee525c0fd837b188db41561cfbf2e9f008592fe16bfe0c85b9102099d3`、snapshot `bf1dc4ee-cf9451c6ff47fcfb`；正式全库生成 1 次（jobs 4，124.1s）、生成后返修 0。最终新增恰 2 条（30247=0.75、30258=1.25）；7251 仅 SAME_VALUE_DIFF_RECORD_EXISTING marker、无重复同值答案。账本 has_answer 20,080→20,082、unresolved 49,585→49,583、backlog 75,778→75,776（Y.G. +2/+2/−2）、identified 69,964 不变。verify_full 17/17、账本 9/9、A7 29/29、final_diff 38/38、隔离复跑 9 卡逐字节、scratch 全过；容量既定模式处置，max_runs/max_bytes 未放宽。
- 候选审查结果：G1 `dwfrun-d75acc84`＝PASS_WITH_EXPLICIT_SCOPE_LIMITS（`output/character_skills/review/c7_p1_g1_structure_20261029_deepseek/REPORT.md`，含仅凭文件接手核对通过）；账本优化 `dwfrun-c03d4554`＝PASS（`output/character_skills/review/c7_p1_ledger_opt_20261029_deepseek/REPORT.md`）。
- 账本优化候选完成（`dwfrun-7bb1ca62`）：仅改 `effect_ledger.py:3174-3201`，A3 每卡独立重读一次并建临时行索引、cid 切换即释放；旧版存 `work/c7_p1_ledger_opt/original_effect_ledger.py`。同输入 ledger.jsonl（111,629 条）与 backlog.json（75,778 项）逐字节一致，官方 9/9；读卡 43,901→4,472 次（−89.8%）、读取字节 −94.1%、总时 389.1/414.3→47.1s（8.26×/8.79×）、峰值内存 732.4/732.6→732.1 MiB 无增长。产物 `output/character_skills/c7_p1_20261029/ledger_opt/`；等价性独审 `dwfrun-c03d4554-8a7e-45dc-907a-b7dad89946db`（V4 Pro GA high）。
- G1 候选扫描完成（`dwfrun-e8b472da`）：全量 9,135 行分流；真正新增 3 行（7251/30247/30258，0 新增唯一数值）。主持裁决：`_same_slots` 仅约束旧 YG1 charainfo 镜像路径，本 3 行 bosspattern/skilltext 直接链与 C6 已验收直接链同口径，全部可纳入；7251 同值异记录单列不升格。候选独审 `dwfrun-d75acc84-5175-4136-8707-a513e55e81bb`（V4 Pro GA high，含文件可接手核对）。产物 `output/character_skills/c7_p1_20261029/g1_structure/`，候选代码在 `code/`、`code_snapshot/`（未进入正式签名集合）。
- **历史已完成任务（仅追溯，不重新派发）**：G1 结构推广 `dwfrun-e8b472da-5d9f-4967-b430-233483234720`；账本读卡优化 `dwfrun-7bb1ca62-e3b9-4045-8f67-4b9c98ce9eb4`（均 V4.1 Flash high）。前者曾只写新候选模块与 `output/character_skills/c7_p1_20261029/g1_structure/`，后者曾只写 `scripts/character_skills/effect_ledger.py` 与 `output/character_skills/c7_p1_20261029/ledger_opt/`、各自 work；当时正式 pages/effect_ledger 只读，公共消费者由主持整合。当前真实在途任务：无。
- 用户授权：`docs/tasks/20261029-mainline-throughput-plan.md` v1，用户 2026-10-29 明确要求落实。依次实施同类字段批量推广、成熟语义批次合并后一次全库重建、账本按卡读取复用；真正增量生成不在本包，未经计时证明不得启动。
- 主持／唯一整合者：本会话 new-provider/kimi-k3-260716。实施候选：DeepSeek V4.1 Flash `new-provider/deepseek-v4-1-flash-261017$high`。独立审查：DeepSeek V4 Pro GA `new-provider/deepseek-v4-pro-ga-260813$high`。历史任务 ID 仅用于追溯；新任务须另行登记，当前无在途任务。各代理只写声明的模块、候选输出与自身 work，公共消费者、账本和共享文件由主持整合。

## 1. 包组成与计数

- **C7-B1（实质语义批次，已完成）**：G1 必殺镜像中来源唯一、结构一致的子族结构推广。语义准入已从 row_id／原值名单改为可验证的来源、类型、引用链、对象、条件和阶段规则；最终新增 2 条既有值描述绑定，0 新增唯一数值、0 新公式、0 完整描述，未扩大语义域。
- **工程项（不计实质批次）**：`effect_ledger.py` 在一次冻结运行内按卡读取复用／临时索引，已验证同输入输出语义等价并记录耗时和内存；未阻塞 C7-B1 交付。
- **交付包 C7-P1**：纳入上述已成熟项；只正式全库重建一次，未为凑满三批等待其他子项。C7 已完成 1 个实质语义批次，剩余 2 个名额；工程优化与本次文档整改均不计批次。后续批次不得加入本包已冻结源码签名。
- 每三个实质语义批次一次第三方方向复核及停审约定不变；工程优化不冒充实质解析批次。

**Y.G. 优先选题（本包实际执行与后续共同规则）**：先从 Y.G. 未解效果选题，再判断既有公式、来源、对象与阶段是否可证，不以全库易扫族为起点。本包目标 Y.G. 卡＝30247/30258（各 1 个未解伤害效果，已有值但缺描述绑定）及 7251（仅同值异记录披露，不计新增）；选择理由＝直接 boss 链来源唯一、句型/档位可判定、同卡基础值可交叉核、公式既有，符合 Y.G. 实际未知项可安全解决。预期收益类别＝既有值新增描述绑定 2 行、Y.G. 未解效果 −2，0 新公式、0 新唯一参数槽、0 完整描述；非 Y.G. 全库 9,135 行只用于结构验证，不因数量扩张语义域，也没有非 Y.G. 新增交付。主要障碍＝同文不同档、同值异记录、旧 `_same_slots` 适用范围及重复认领，均按反例单列，未强行放行。后续包任务卡须同样简写目标 Y.G. 卡/未解效果、选择理由、预期收益类别、非 Y.G. 连带范围与主要障碍；候选数量不是承诺收益，已交付项不得重复计算。

## 2. 允许写入范围与保护/停止条件

- 允许：`docs/角色技能完整解读实施方案.md`（流程、检查、周期与计时条款）、`docs/tasks/character-skills-progress.md`、`HANDOFF.md`、本任务卡；候选推断/扫描模块、`scripts/character_skills/effect_ledger.py`（仅读卡复用）、`output/character_skills/c7_p1_20261029/`、相关 `work/c7_p1_20261029*/`。共享消费者由主持或其明确指定整合者修改。
- 保护：APK/CACHE 分源不跨层；原值、单位、对象、条件、阶段与证据档不升格；30236/30239（30239 G0 豁免不扩大）、20234、HOLD18、C113、cost_statement、旧正确答案与既有批次产物；rules 294 键当前不变，除任务书明确允许外不改 rules.json/rules.py。
- 停止：无新增安全收益、来源歧义、跨层风险、新原生需求、输入/版本不一致、保护项冲突、检查无法证明等价时，相应候选移出并保留待办；不为凑成果扩大范围，不改写 receipt/签名、不取消检查、不混用版本。禁止新原生、手机采集、Git 提交/推送、公开发布、未经授权删除或真正增量生成。

## 3. 已验收基线与恢复入口

- **包前基线（C6 已验收历史）**：C6 三批及方向审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、无需复审；`output/character_skills/review/direction_c6_20261029_independent/REPORT.md`。C6 是包前基线，不是当前安全检查点。
- campaign `4ddfca38451eafdb30df010fc6c6eee96b9e84ad799361961fd0ab4523274df1`；snapshot `4ddfca38-cf9451c6ff47fcfb`；rules 294 键 SHA-16 `cf9451c6ff47fcfb`；has_answer 20,080（Y.G. 4,385）、backlog 75,778（Y.G. 9,450）。容量 12/12、7,780,539,717 B，上限 12 run/8 GiB 未放宽。
- 当前工作区含大量未提交/未跟踪成果，均保留；不得仅写 Git HEAD 充当恢复点。候选代码定稿后，在本目录记录修改文件、实际 SHA-256、必要小补丁和基线；候选输入只读引用，不复制游戏大表。
- **当前产品安全检查点：C7-P1 已生成且产品验收通过**（`output/character_skills/c7_p1_20261029/`、`output/character_skills/review/c7_p1_final_20261029_deepseek/REPORT.md`）；C6 成果及独立审查目录、C6 成果页 `output/character_skills/cycle_reports/C6/` 仅作包前恢复基线。**本次文件交接整改状态单独记录**：独立效率复核 REQUEST_CHANGES 的 R1/R2/R3 文件整改已完成、定向自检通过，外部复核状态不以主持自检代替。任何候选失败先保留输入，不发布半成品；恢复以上述已验收版本为准。

## 4. 候选版本与已完成证据

- 候选代码/规则/输入版本：G1 `output/character_skills/c7_p1_20261029/g1_structure/code/g1_structure_rules.py`，SHA-256 `c66e19544eb8ace6ca471a582e39f924eed5ada7fa50db61bb16ccdef8cbdb86`（与 `code_snapshot/` 一致；候选全集 `candidates_all.jsonl` SHA-256 `6ee2958770076868eb1c9ccf7fc1c8e1c20a5b616678b2c19021eb97f06f494f`）。账本优化 `scripts/character_skills/effect_ledger.py` 基线 `work/c7_p1_ledger_opt/original_effect_ledger.py` SHA-256 `8eebc4dc…690c`；候选版 SHA-256 `b09bb928…7190`（独审核实）。输入只读引用 C6 正式 pages 与原始表，rules 294 键 `cf9451c6ff47fcfb` 未改。
- 已完成证据：G1 全量扫描/28用例/候选独审通过；账本旧新逐字节对账、9/9自检、10/10边界、性能实测与独审通过；正式全库生成 1 次及 verify_full 17/17、账本 9/9、A7 29/29、final_diff 38/38、隔离复跑 9 卡逐字节、最终独审 PASS_WITH_EXPLICIT_SCOPE_LIMITS，均已落盘于 `output/character_skills/c7_p1_20261029/` 与 `output/character_skills/review/c7_p1_final_20261029_deepseek/`。
- 阶段耗时：研究/实现、候选检查、独审、正式生成、账本、固定检查、返修、等待分别记录；未知写未知，不用文件时间估算工时，不将并行时长相加。

## 5. 待办

**以下三项均已完成；剩余仅为非阻断登记项，不阻断本包收口。**
- C7-B1：全量候选扫描及四类分流（可出值并绑定／仅字段值／需补证／范围外）；结构规则、不同原值、原名单外正例、同文不同档、跨层同号、空值/真零、阶段/对象反例；7251 同值异记录单列，不升格。
- 工程项：旧/新账本同冻结输入比较，所有描述、效果、答案引用、状态、待办和计数一致；只允许时间戳等非语义字段差异；记录读卡次数、耗时和峰值内存。
- 主持：候选合并与共同路径交互检查、冻结、容量处置、一次正式重建→账本→入口/选题→固定检查、final_diff/隔离复跑、独审、收官与收益分列。
- 首个试行包冻结时由现有独审者做「仅凭文件即可接手」轻量核对，不另建审查体系。

## 6. 下一步与成功标准

- 下一步（当前）：**无在途任务，不重复派发已完成实施或审查，不启动 C7-P2**。后续仅登记选题原则：先列 Y.G. 未解效果，优先已有公式且来源/对象/阶段可证者；证据障碍只记录有限缺口，不无限深挖；非 Y.G. 仅在同一已证域内低成本顺带，不得延误成熟 Y.G. 交付。
- 成功标准：候选全集均有状态与原因；合法/非法例可区分；同族新记录不再靠手加 row_id；无新增安全收益如实报告。账本优化语义等价且计时/内存实测。成熟项冻结后只正式全库生成一次，17/17、账本 9/9、A7 29/29、final_diff/保护项/隔离复跑通过，各批独审结论与收益分别保留。
- 候选通过后的正式命令（已于本包执行一次，jobs 4）：`./.venv/Scripts/python.exe -X utf8 -B scripts/character_skills/card_page_batch_parallel.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --output output/character_skills/pages --execute --jobs 4`。运行目录＝项目根；输入＝冻结源码/规则/原始表，输出＝正式 pages 及下游账本/入口/选题。后续如需重建须另起交付包任务卡，不重开本包。
- 更新要求：候选完成、独审返回、版本冻结、正式生成完成、终验完成、失败或范围变化时立即更新本卡及 run_record，不等收官补交接。
