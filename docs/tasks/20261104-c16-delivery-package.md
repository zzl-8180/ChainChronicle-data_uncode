# C16 交付包任务卡（P1 1095逐效果部分绑定）

- 创建：2026-11-04；主持：`new-provider/kimi-k3-1-pro-261024`。
- 状态：**C16正式交付、独立终审及第三方方向审查已完成；第三方结论PASS_WITH_EXPLICIT_SCOPE_LIMITS，阻塞0；在明确范围限制下收口，等待用户下一步安排，不启动C17**。
- 第三方：[REPORT](../../output/character_skills/review/direction_c16_20261104_thirdparty/REPORT.md)／[verdict](../../output/character_skills/review/direction_c16_20261104_thirdparty/verdict.json)／[evidence](../../output/character_skills/review/direction_c16_20261104_thirdparty/evidence.json)：23卡23行49答案，102/102通过（含独立重算、实际HTML静态核查及历史证据一致性检查，不全是独立重跑）。本轮文档接收新增数值收益为0。
- 周期卡：`docs/tasks/20261104-c16-cycle.md`；批次卡：`docs/tasks/20261104-c16-p1-1095-partial-binding.md`。

## 候选对账上限

- Y.G.23项／15卡优先；同域非Y.G.26项／8卡仅在共用判据、真实消费和同一轮独审均覆盖时连带。
- 总上限49项／23卡／23描述／23载体；试点11项只是机制验证，不是正式净增。
- 预计0新公式／规则键／新原生，rules.json与effect_ledger.py不改；若真实消费失败必须停下，不得默认修改账本。

## 合并前置条件

1. 试点真实Inputs＋`effect_ledger.analyze_row`通过，负例和保护卡不被吸收。
2. 全批候选、排除、来源链、player_text、模块／输入哈希和可复跑检查完成，独立审查无阻断。
3. 主持合并预检验证旧答案前缀、缺省／错误scope拒绝、二次幂等、范围外零变化和真实Inputs首次新增／第二次0。
4. 用真实账本预检冻结预期增量，Y.G.／非Y.G.、效果净增、四档、A/C、S4和split分列；不得按49答案预写效果净增。
5. 重核容量与保留状态，预登记本次所有既有`page_sha256`信息性漂移卡，逐字段证明且不计收益；不能直接复用C15的4卡名单。

## 正式步骤

- 合并预检→冻结→**唯一一次正式全库生成（jobs 4）**→正式账本→入口页→F03→verify_full→账本9/9→A7→final_diff→隔离复跑→只读验证→正式独立终审→成果／剩余量页。
- 正式脚本必须支持`--resume-post-build`，仅供构建后失败续跑，不得借此进行第二次全库生成。
- 独立审查通过前不得创建`pre_rebuild/state.json`，不得运行`card_page_batch_parallel.py --execute`或`run_formal.py`（含resume）。

## 验收与停止

1. 正式归属变化只能来自审查冻结的成熟子集；Y.G.／非Y.G.、答案、效果净增和完整度以正式账本实测为准。
2. 旧答案零丢失零改值，30236／30239／30102／20234保护边界不破；信息性指纹差异单列，不计收益。
3. 默认中文与正式JSON语义一致，关联不升格；精确公式、来源和未知边界保留。
4. 正式独立终审无阻断后生成C16成果页与机器验证，等待第三方方向审查；不自动启动C17、清理、Git推送或发布。
