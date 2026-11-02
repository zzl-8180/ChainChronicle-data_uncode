# C11-P1 t114 直接四行：候选独立审查要求

- 前置：候选实施 workflow 已完成且 `run_checks.py` 通过；**独立审查在途，workflow `dwfrun-8e9cb00a-2148-460d-9e2d-17cc7c21efd5`**。
- 审查：独立新上下文，dynamic workflow，`new-provider/deepseek-v4-pro-ga-260813` high；不得参与实施或替实施改码。
- 输入任务：`docs/tasks/20261031-c11-p1-t114-direct.md`；候选模块与 `output/character_skills/c11_p1_t114_20261031/candidate/` 以完成时哈希为准。

## 独立核验范围

1. 不采信主持预检、实施回执或检查器的 PASS 作为语义证据；直接从现有完整解码 CACHE/APK JSON 读取四条父链、原始记录、slot/type/field、raw_value 和 float32。
2. 逐行核对日文、row_id、record_id、来源层、对象、阶段、公式适用、载体唯一、机制唯一及既有 t114 同卡零答案背景；关联只评推断，不升级为执行或实机确认。
3. 复核既有 `bossskill|114|/skillparam1` 局部公式与单位；不得推出总伤害、最终 HP、p4 次数或未覆盖子句。原文「25回」保留。
4. 检查 type52/type13 不竞争、错误槽/记录/类型/卡反例、非 Y.G. 零连带、镜像零新增；候选模块不得含 row_id/原值白名单。
5. 独立复算四条数值并检查 no-op/旧答案保护证据的充分性；实际运行必要的候选检查，失败不得包装成通过。
6. 两条 skilltext 镜像只允许核对是否被排除，不得提前审查为可放行。

## 写入与结论

- 只写 `output/character_skills/review/c11_p1_t114_direct_20261031_deepseek/` 与自身 `work/c11_p1_t114_direct_review_20261031/`；不改生产代码、候选实现、正式产物或共享文件。
- 报告须含 verdict、覆盖范围、逐行重算、检查命令、阻断项和非阻断限制。缺陷交回实施修复，不代为修改。
- 候选通过只表示可进入镜像阶段，不表示正式全库交付通过。
