# C19 交付包任务卡（1095与type8同族扩大）

- 创建：2026-11-07；主持：`new-provider/kimi-k3-1-pro-261024`。
- 状态：**原第三方R01定向复核通过，R01 CLOSED，阻断0；C19清理与主提交`e2e864624b407682a6c2ab6798bea37ff6ea12bb`已推送，最终文档回执随本提交同步，不启动C20或发布**。campaign `99bee2a166e5ec5f9c03ac97b555d4ada2f6f30d1535258add16bc64c7227c66`，snapshot `99bee2a1-cf9451c6ff47fcfb`；正式独立终审PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0、47/47（28项独立重算＋19项只读引用）；成果页详细验证21/21、坏链接0；RETAINED 4/12。
- 周期卡：`docs/tasks/20261107-c19-cycle.md`；批次卡：`20261107-c19-p1-1095-attack-families.md`、`20261107-c19-p2-type8-basic-attack.md`。

## 合并前置条件

1. 两组候选、排除、完整来源、player_text、模块／输入哈希和可复跑检查完成；DeepSeek Pro GA候选独审无阻断。
2. 真实Inputs＋`effect_ledger.analyze_row`首次新增、第二次0、scope硬拒绝、未消费0；非目标行和保护卡不变。
3. 主持合并预检验证旧答案前缀、二次幂等、范围外零变化；反向移除C19接线回到C18后`card_page_data.py`哈希`adf1ffee83c853575852a6cd95094929168270ba2ba27eb38bd2580662b88b16`。
4. 真实账本预检冻结答案／效果净增，按效果类型、Y.G.／非Y.G.、四档、A/C、S4和split分列；不得按133攻击效果预写答案总数或完整度。
5. 重新推导全部既有`page_sha256`信息性漂移卡，逐字段证明且不计收益；不直接复用历史9卡名单。
6. RETAINED起点0/12，12 run／8 GiB限额不变；正式后按实测，不预写。
7. 保留检查器经验：正确读取`snapshot.snapshot_id`，显式DECODED／FULL_CARDS，Y.G.读冻结字典，每次失败独立留档不覆盖。

## 正式步骤与停止

- 合并预检→冻结→**唯一一次正式全库生成（jobs 4）**→正式账本→入口页→F03→verify_full→账本9/9→A7→final_diff→隔离复跑→只读验证→DeepSeek Pro GA正式独审→成果／剩余量页→第三方方向审查交接。
- 正式脚本支持`--resume-post-build`仅供构建后失败续跑，不进行第二次全库生成。
- 独审通过前不得创建`pre_rebuild/state.json`或运行`card_page_batch_parallel.py --execute`、`run_formal.py`（含resume）。
- 旧答案零丢失零改值，30236／30239／30102／20234保护边界不破；C16／C17／C18旧答案不误归C19收益。
- 默认中文与正式JSON一致，关联不升格；精确公式、来源和未知边界保留。
- 不启动C20、其他机制族、新原生、实机、新缓存、清理、Git或发布；第三方若REQUEST_CHANGES，停在findings，不自动整改或重建。
