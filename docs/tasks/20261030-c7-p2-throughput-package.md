# C7-P2 主线提速交付包任务卡

- 创建：2026-10-30。当前状态：**已验收收口，最终独立审查 PASS、零阻断**（`dwfrun-7c564948-ec1b-47a7-b0c7-795f414a028b`；报告 `output/character_skills/review/c7_p2_final_20261030_deepseek/REPORT.md`）；run_record state＝ACCEPTED。**当前真实在途任务：无（不重复派发已完成实施或审查）。**残留登记：①scratch s1/s2/s3 为候选阶段检查，重建后页已含答案，重跑分别得 6/8、43/46（P1/P2/V2 幂等返回），属预期，README/run_record 已注明阶段；②final_diff part_c/part_d 与 s3 part B 未由独审重跑（避免新增 run 占容量），仅核脚本逻辑与独立复现 part_a/E5；③任务卡状态行更新滞后（本次已回填）。
- 合并实施 `dwfrun-186db13d-5ba9-4f25-aa1f-1dafb7be3619` 完成：新 campaign `3c408370e6673da7b43ede845eaced7176fcd3f6f1cade3d444ecad70e886e0b`、snapshot `3c408370-cf9451c6ff47fcfb`；正式全库生成 1 次（jobs 4、91.93s）、生成后返修 0。最终新增恰 5 条/2 行（7250 四槽 .6/.3/30/.3、30310 一槽 1.5），0 新增唯一数值、0 新公式、0 新规则键、0 完整描述增量；账本 has_answer 20,082→20,087、unresolved 49,583→49,578、backlog 75,776→75,771（Y.G. +5/+5/−5）、identified 69,964 不变。verify_full 17/17、账本 9/9、A7 29/29、final_diff 37/37、final_additions 18/18、隔离复跑 32 文件逐字节、scratch s1 8/8、s2 46/46、s3 12/12；容量既定模式处置，max_runs/max_bytes 未放宽（生成后 12/12、7,780,929,917 B）。
- 预检 `dwfrun-bde556dc-bb35-44d1-b36a-3d0c8515f790` 完成：G7 多段零安全新增，不再深挖。推荐 C7-B2＝denju 同记录绑定 2 行/5 条答案/5 效果（全 Y.G.）：7250 denju f0 绑定 bossskill|13|/skillparam1/2/3/6＝.6/.3/30/.3（记录 40725000，4 效果，行未解析→部分，敌方减益 2 条未知）；30310 denju f0 绑定 bossskill|64|/skillparam1＝1.5（记录 43031000，1 效果，映射沿用既有页答案）。均与 C6 G7-B1 同门法（链定档＋同记录＋同卡基行逐位相等），0 新增唯一数值、0 新公式、0 新规则键、0 完整描述增量、非 Y.G. 连带 0 行。R8b 敏感匹配 5 行、30104 竞争载体、30304 文本不匹配均排除，不计收益；85 行无规则新公式、853/89 行未做链解析仅登记为有界范围外。
- 授权：用户 2026-10-30「现在继续下一周期」，按 C7-P2 继续（C7 尚余 2 个实质语义批次名额）。遵循 `docs/tasks/20261029-mainline-throughput-plan.md` v1、方案§1.5、C7-P1 已验收交接。
- 当前真实在途任务：无（不重复派发已完成实施或审查）；C7-P3 的 Y.G. 优先预检另行登记，不重复 C7-P1/C7-P2 已交付项。
- 主持／唯一整合者：本会话 new-provider/kimi-k3-260716。实施候选：DeepSeek V4.1 Flash `new-provider/deepseek-v4-1-flash-261017$high`。独立审查：DeepSeek V4 Pro GA `new-provider/deepseek-v4-pro-ga-260813$high`。各代理只写声明的候选输出与自身 work；共享消费者、账本和共享文件由主持整合。

## 1. 基线与检查点

- 当前产品安全检查点：C7-P1 已生成且验收通过（`output/character_skills/c7_p1_20261029/`），外部最终文件交接复核 PASS、交接阻断关闭；产品仍 PASS_WITH_EXPLICIT_SCOPE_LIMITS。
- campaign `bf1dc4ee525c0fd837b188db41561cfbf2e9f008592fe16bfe0c85b9102099d3`、snapshot `bf1dc4ee-cf9451c6ff47fcfb`；rules 294 键 SHA-16 `cf9451c6ff47fcfb`；has_answer 20,082（Y.G. 4,387）、unresolved 49,583（Y.G. 6,167）、backlog 75,776（Y.G. 9,448）。
- 容量上限 12 run/8 GiB 未放宽；性能沿用已验证 jobs 4，环境无实质变化时不重复 jobs 1/2/4 三档全库基准。C6 仅作更早期恢复基线。

## 2. 选题规则与允许范围

- 先从 Y.G. 未解效果选题：优先证据充分可直接补答案者，其次只差少量来源/阶段核对者；非 Y.G. 仅同域低成本顺带且不延误 Y.G. 交付。
- 候选须已有公式、同层来源唯一、对象与阶段可判定；不从全库易扫族开始，不为增加数量扩大语义域。G7 与「已有公式且引用唯一」不单独决定优先级，允许替换更成熟的 Y.G. 规则族，难做不无限深挖。
- 不重复 C7-P1 已交付两行、C6 已交付项及 G7 首段 12 项；已交付项不得重复计收益。
- 不启动新原生、30239 豁免扩大、20234 处置、Git 提交/推送、公开发布、真正增量生成或未经授权删除。保护卡、HOLD18、C113、cost_statement、旧答案与历史产物保持。
- 每个候选按可出值并绑定／仅字段值／需补证／范围外分流，记录具体原因；证据障碍只登记有限缺口，不转为非 Y.G. 主导。

## 3. 预检任务

- 输出：目标 Y.G. 卡/未解效果、选择理由、预期收益类别、非 Y.G. 连带范围与主要障碍；可执行的结构规则、原始正例/反例、不同原值、空值/null/真零、跨层同号、阶段与对象不符处理。
- 优先评估 G7 多段增益中首/次段可证子族；若存在对象/阶段/竞争记录歧义，移出，不强行放行。若 G7 无安全新增，登记替换族及理由，不停在无限研究。
- 预检输出只写 `output/character_skills/c7_p2_20261030/precheck/` 与 `work/c7_p2_20261030/`；不改正式页面、账本、rules 或生产脚本。

## 4. 后续步骤与停止条件

- 预检通过后才建立 C7-B2 任务书与候选模块，按「候选实现→独立候选审查→合并冻结→一次正式重建→固定检查→最终独审→收官」执行；不为凑满三批等待未成熟子项。
- 若预检无安全新增，报告零新增并给有限替代候选；若证据冲突，保留未知，不扩大豁免或原生研究。
- 后续正式命令仅在候选审查通过后执行：`./.venv/Scripts/python.exe -X utf8 -B scripts/character_skills/card_page_batch_parallel.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --output output/character_skills/pages --execute --jobs 4`。
- **周期节奏（用户 2026-10-30 补充）**：先完成 C7-P2，再推进 C7-P3；两个交付包完成并通过各自独审后，停下由用户安排独立审查，不提前开始第三个包。C7 共 3 个实质语义批次（C7-B1 G1 结构推广、C7-B2 denju 同记录绑定、C7-B3 后续选定），满三批后按约定停审。
- 本卡随候选完成、独审返回、版本冻结、正式生成、终验、失败或范围变化立即更新，附实际哈希、检查证据与恢复方式。
