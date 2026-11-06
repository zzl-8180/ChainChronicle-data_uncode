# C16-P1 1095逐效果部分绑定任务卡

- 创建：2026-11-04；主持：`new-provider/kimi-k3-1-pro-261024`。
- 状态：**C16正式交付、独立终审及第三方方向审查已完成；第三方结论PASS_WITH_EXPLICIT_SCOPE_LIMITS，阻塞0；在明确范围限制下收口，等待用户下一步安排，不启动C17**。
- 第三方：[REPORT](../../output/character_skills/review/direction_c16_20261104_thirdparty/REPORT.md)／[verdict](../../output/character_skills/review/direction_c16_20261104_thirdparty/verdict.json)／[evidence](../../output/character_skills/review/direction_c16_20261104_thirdparty/evidence.json)：23卡23行49答案，102/102通过（含独立重算、实际HTML静态核查及历史证据一致性检查，不全是独立重跑）。本轮文档接收新增数值收益为0。
- 周期收尾：[A/B清理与Git推送](20261106-c16-closeout-cleanup-git.md)已完成；RETAINED 0/12，origin/main=`45a368d8ea85c0d1dfc7d0af2f8cb5acfce2c4c5`。
- 方法：现行方案§1.6及`docs/tasks/20261104-mechanism-first-next-batch-plan.md`；基线见C16周期卡。

## 试点门（先于全批）

- 正例11项：20822四项（param1／3／2／5）、20906四项（同四槽且1095在`sub[1]`）、30246三项（param1／5／6）。
- 负例：20822额外param6不得并入基础句；20607四项缺原始上游且暴击率继续未知；type108七项不得出数；30236／30239／30102／20234保护卡零新增。
- 必须用真实`card_page_data.Inputs`和`effect_ledger.analyze_row`证明11项目标effect由unresolved→has_answer，第二次0新增，缺省／错误scope硬拒绝。只读helper或旧实验PASS不算通过。
- 每条答案必须带可读`player_text`、raw／单位／对象／条件／来源／证据档，关联保持推断；精确公式与来源可在展开层复核。

## 全批边界（试点通过后才允许）

- Y.G.23项／15卡，字段param1×15、param5×7、param6×1。
- 同域非Y.G.26项／8卡，字段param1×8、param2×6、param3×6、param5×6；出现新证据负担即剔除，不拖Y.G.。
- 上限49项／23卡／23描述／23载体，不承诺正式净增；0新公式／规则键／新原生，预计不改rules.json与effect_ledger.py，若现有消费失败必须停止而不是默认改账本。
- 不全局删除旧P4，不放宽B11／B12／B14；49个effect_id只作作用域与回归种子，数值由真实角色→父→唯一1095→字段重算，不按cid或同文复制。

## 允许写入

- 实施者：`scripts/character_skills/card_page_inference_c16_p1_1095_partial.py`、`output/character_skills/c16_p1_1095_partial_20261104/`、`work/c16_p1_1095_partial_20261104/`及本任务卡。
- 独立审查者：`output/character_skills/review/c16_p1_1095_partial_20261104_deepseek/`。
- 共享`card_page_data.py`、正式pages／ledger／rules／入口只能由主持在候选独立审查无阻断后处理；实施者不得提前接线或运行正式生成。

## 最小交付与停止

- 试点README、candidate/exclusions、检查脚本与结果、真实Inputs／账本证据、模块和输入哈希。
- 全批候选独立审查无阻断后才允许主持合并；非Y.G.未达低成本标准时只交Y.G.。
- 不做APK补证、新原生、实机、其他机制族、正式生成／resume（候选阶段）、清理、Git推送或发布。
