# C12 交付包：正式独立审查要求

- 状态：**PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0，C12正式验收完成并停止；范围限制与文件可接手核对已登记**。
- 前置：C12正式生成、账本和固定检查完成。
- 审查：独立新上下文 `new-provider/deepseek-v4-pro-ga-260813` high；只写 `output/character_skills/review/c12_delivery_final_20261031_deepseek/` 与自身work，不改生产或正式产物。

## 必查

1. 冻结正式campaign/snapshot/rules/源码与输入；正式生成仅一次、jobs4、RETAINED 8/12、限额不变。
2. 分别核对P1 108/66、P2 102/68、P3 459/459，合计669答案/593效果净增、S4 76、完整+0、0新增唯一值；199行/102卡及范围外2,134卡不变。
3. 账本has_answer/unresolved/backlog、Y.G.分项、identified/complete/partial/unparsed/split/A/C与整行推断按实测对账，不把669当效果净增。
4. P1 p6保护、P2 M字段不消费和跨记录推断、P3同标签唯一同文行/super异值/2003非13中继/S7保留；CACHE/APK不合并。
5. 正式verify_full 17/17、账本9/9、A7 29/29、final_diff、validate和隔离复跑可复现；独立运行必要检查，不以机器全绿替代语义。
6. 报告最终verdict、阻断、限制和文件可接手核对。通过后C12正式闭环并停止等待第三方方向审查，不启动C13。
