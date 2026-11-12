# 打包支线退役：执行对话统一整合权责交接

- 日期：2026-11-08；状态：**退役条目已移交执行对话／主线研究继续／不删除、不迁移、不切换、不提交推送**。
- 本交接依据 [物理回执](../project-layout/20261108-packaging-physical-v1/REPORT.md) 和 [Astra独立复核](../project-layout/20261108-packaging-physical-v1/physical-independent-review.json)：5,317项／108,004,454 B迁移与五入口各142文件验读均已完成，无需重复执行或全量重验。

## 1. 写入权移交与现有成果

自本交接起，执行对话统一负责退役事项的导航整合、删除前准备和Astra复核，不再逐步往返要求主持操作。主持不再并发修改下列文件中的**退役条目**：

- `AGENTS.md`
- `HANDOFF.md`
- `STATUS.md`
- 根 `README.md`

移交的是退役事项写域，不是四份文件的全部内容。AGENTS第8节未来完整分享原则、C19／Web主线、其他历史结论及非退役说明仍由主持和相关任务所有者维护；执行对话不得借退役整合覆盖这些条目。

已完成的导航修改**全部保留，不回滚、不重复处理**：

1. `AGENTS.md`：历史打包材料定位改到 `operations/history/retired-packaging/20261108/` 下的 `share_bundle/`、`distribution/`、`history-work/`，补真实迁移、五入口和删除边界。
2. `HANDOFF.md`：②历史发行说明改指新位置，新增5,317项迁移与五入口验收入口。
3. `STATUS.md`：顶部加入真实完成状态；旧 `20261016-delivery`、`20261025-character-tools`、`cc_skill_values_20261021` 路径改指新历史根。
4. 根 `README.md`：加入真实迁移与只读维护入口，更新 `scripts/` 说明。
5. 新增 `docs/tasks/20261108-packaging-navigation-integration.md`，记录前后SHA、实际差异及390个本地链接无缺失的检查结果。

这些修改尚未提交；本交接不代替执行对话后续审阅，不要求其沿用准备态文字或放弃按真实状态重定基底。

## 2. 必须保留的主线内容

- C19 campaign `99bee2a166e5ec5f9c03ac97b555d4ada2f6f30d1535258add16bc64c7227c66`、snapshot `99bee2a1-cf9451c6ff47fcfb`、rules 294键及正式数据基线。
- 133卡133行407答案／效果、35行45项同句未知披露、4行既有split_flags；关联推断、未实机和第三方浏览器UNTESTED边界不变。
- C19 R01 CLOSED、原方向REQUEST_CHANGES历史前像、旧独立终审、R01整改与复核材料、C19 Web接收登记；Web补证仍是“已登记接收／正式吸收待另行安排”。
- 原始输入、正式pages／profiles／effect_ledger、原始审查、P/v7、四份历史plan及binding、冻结manifest和失败证据。
- AGENTS第8节未来完整分享原则及其他任务的新增内容，不因退役条目移交而撤销。

## 3. 当前在途写域与新使用者

| 范围 | 当前负责者／使用边界 |
|---|---|
| 四根文件中的退役条目、退役导航整合、删除前准备 | **执行对话统一接管**；主持不再并发修改 |
| `scripts/project_layout/`、`docs/project-layout/`、`operations/history/retired-packaging/` | 执行对话及其指定维护者；只读维护入口为 `scripts/project_layout/retirement_runtime.py` |
| 五个正式历史 `share_bundle` 入口 | 已指向新历史根；后续读取应使用新正式入口，previous仅作停用回滚证据，不供业务读取 |
| 材料验收与独立复核 | Sol high负责材料验收，Astra high独立复核；已有迁移／切换结论保留 |
| 主线研究、规则修订、正常生成与校验 | 主持继续；无需停工，不与退役写域混用 |
| C19及以后主线、角色技能脚本与当前进度看板 | 主持及既有任务所有者；新周期仍须用户单独授权 |
| 参考分析、UI／reader及其他未跟踪任务文件 | 各原任务所有者；本交接不接管、不覆盖 |

执行对话是退役条目和相关维护入口的新整合者；未发现需要把previous重新投入使用的业务消费者。不能把“新正式入口可用”解释为旧target或previous仍可继续读取已迁出的材料。

## 4. 尚未解决的阻断

1. **最终删除授权未到**：1,607项DELETE候选不得删除；previous和旧空目录不包含在该数量内，须另列后续范围。
2. **删除前门槛未完成**：届时仍须重新通过完整archive模式1,406对内容门、源身份／overlay／reparse／硬链接／漂移检查，再取得用户单独最终确认。
3. **回退不能只看junction**：旧target已迁空时不得盲指；须保持已验真的新位置，或先恢复5,317项保留树并验真再回退。
4. **旧包恢复边界**：历史ZIP、六个成功旧包及173份旧生成载荷的精确重放不因manifest或源码前像而保证恢复，不声称拥有完整旧版打包现场。
5. **写入纪律**：本交接及现有导航差异未提交或推送；执行对话后续Git、删除或发布动作仍需各自明确授权。

除上述事项外，没有需要主持继续阻塞主线研究的问题。执行对话可在其写域内独立完成导航整合、删除前准备及Astra复核。
