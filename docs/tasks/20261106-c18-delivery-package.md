# C18 交付包任务卡（P1两项1095攻击外推）

- 创建：2026-11-06；主持：`new-provider/kimi-k3-1-pro-261024`。
- 状态：**C18正式交付、正式独立终审、成果页及C17＋C18联合第三方方向审查已完成并限定通过；R01已仅文档修正，R02按回执登记UNKNOWN；不启动C19、清理、Git或发布**。campaign `01c05f78bd54263efd40991b96e3aed2a421cce3e0845e5e49bb4fcd03d114c3`，snapshot `01c05f78-cf9451c6ff47fcfb`；联合第三方136项中135通过、1项文档一致性失败（非阻断），C18实际核查2卡2行2答案，浏览器UNTESTED；RETAINED 8/12。联合[REPORT](../../output/character_skills/review/direction_c17_c18_20261106_thirdparty/REPORT.md)／[verdict](../../output/character_skills/review/direction_c17_c18_20261106_thirdparty/verdict.json)；接收`docs/tasks/20261106-c17-c18-thirdparty-closeout.md`。
- 周期卡：`docs/tasks/20261106-c18-cycle.md`；批次卡：`docs/tasks/20261106-c18-p1-1095-attack-partial.md`。

## 候选对账上限

- 仅2个非Y.G. effect：6341 f0、20333 f0，全部`skilllist|1095|/param1`。
- 预筛raw为1.225／1.375，实施必须重新解引用，不直接导入。
- 预计0新公式／规则键／账本映射／新原生；额外param6和句外条件强化不并入，不扩其他词条或机制族。

## 合并前置条件

1. 真实Inputs＋`effect_ledger.analyze_row`通过两项目标effect由unresolved→has_answer、第二次0新增、缺省／错误scope硬拒绝。
2. 候选、排除、来源链、player_text、模块／输入哈希和可复跑检查完成，独立审查无阻断。
3. 主持合并预检验证旧答案前缀、二次幂等、范围外零变化和保护卡；反向移除C18接线回到C17后`card_page_data.py`哈希`815ce15603620c775bc6b8af21bb6382d13a3d0a0a5135adefb9d426a6c8bce9`。
4. 真实账本预检冻结预期增量，Y.G.／非Y.G.、效果净增、四档、A/C、S4和split分列；不得按2答案预写效果净增。
5. 重核容量与保留状态：起点RETAINED 4/12、reserved_bytes 2,645,032,471，正式后按实测；12 run／8 GiB限额未放宽。预登记本轮所有既有`page_sha256`信息性漂移卡，逐字段证明且不计收益；不能直接复用C17的9卡名单。
6. 预先避免C17检查器问题：正确读取`snapshot.snapshot_id`、显式定义DECODED／FULL_CARDS、Y.G.增量读取冻结字典，每次失败独立留档不覆盖。

## 正式步骤

- 合并预检→冻结→**唯一一次正式全库生成（jobs 4）**→正式账本→入口页→F03→verify_full→账本9/9→A7→final_diff→隔离复跑→只读验证→正式独立终审→成果／剩余量页。
- 正式脚本必须支持`--resume-post-build`，仅供构建后失败续跑，不得借此进行第二次全库生成。
- 独立审查通过前不得创建`pre_rebuild/state.json`，不得运行`card_page_batch_parallel.py --execute`或`run_formal.py`（含resume）；不得运行C17原包正式脚本或resume。

## 验收与停止

1. 正式归属变化只能来自审查冻结的2个非Y.G. effect；Y.G.／非Y.G.、答案、效果净增和完整度以正式账本实测为准。
2. 旧答案零丢失零改值，30236／30239／30102／20234保护边界不破；C17三卡不得误归C18收益；信息性指纹差异单列，不计收益。
3. 默认中文与正式JSON语义一致，关联不升格；精确公式、来源和未知边界保留。
4. 正式独立终审无阻断后生成C18成果页与机器验证，再与C17一并交第三方方向审查；不自动启动C19、清理、Git推送或发布。第三方若REQUEST_CHANGES，停在findings，不自动整改或重建。
