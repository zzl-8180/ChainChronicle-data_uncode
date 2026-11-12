# 第三批完整目录整理：执行前方案

2026-11-08。Sol执行准备，Astra独立复核；仅新准备材料，业务原件、正式脚本及所有联接保持现状。沿用1140条映射与既有静态引用／别名索引，按本批范围定向核当前差异，不重做全仓研究。

## 能搬的完整目录

项目根 `E:\代码项目\锁链战记数据解包`，下表均为项目相对路径。

| 现在 | 目标 | 文件／字节 | 在途边界 |
|---|---|---:|---|
| `output/git_sync_20261024` | `operations/records/git-sync/20261024` | 6／29,828 | 历史已完成Git同步回执，无当前生产脚本读写；5个历史隔离入口需接管 |
| `output/project_overview` | `operations/records/project-overview/20261020` | 5／69,618 | 一次性人工概览，无当前生产读写；5个历史隔离入口需接管 |

合计 **11文件、99,446 B，约100KB**，两树均无子目录和内部reparse；目标当前不存在。它们归跨项目运维记录，不强塞进六个业务子项目。此批是清理目录位置，并非释放空间；其余旧目录仍有具体耦合，不能仅凭历史名称搬走。

## 引用适配：不需要业务源码补丁

1. **原字节保留。** project_overview的HTML没有实际href／src或上级相对资源链接，README中的旧根路径是历史文字；git_sync没有随目录深度变化的相对链接。目录内部无须修改。`paths.nul`等原文件按二进制读取保留，不当文本重写。
2. **10个真实junction。** C14—C18各有两种入口，均在 `impl/isolation_input/output/` 下，basename为 `git_sync_20261024` 和 `project_overview`；当前均指向两旧根。必须由一次主持交接确认实际使用者和共同局部窗口，然后随根迁址逐一切换，不能只搬目录让入口永久悬空。
3. **历史文档不回写。** `docs/tasks/20261024-git-mainline-sync.md`里的旧回执路径、旧概览README／提示词、原映射及冻结证据保留原状，由新外部path-map和运维导航说明新位置。历史“可删除”、清理提示词和Git命令不构成当前授权。
4. **新导航只准备。** 候选新增 `operations/README.md`、`operations/records/README.md`，指向两个完整目录。实际根移动、10入口及独审通过后才落地，不提前发布成功状态；若目标说明文件届时已存在，先读并增量整合，不整文件覆盖。
5. **局部忽略先于移动。** 候选 `operations/records/.gitignore`只忽略这两个准确载荷目录；不修改根.gitignore，不强制暂存批量产物。若已有规则则保留并合并，不能覆盖。

精确source、target、11文件身份／SHA、10联接ID／tag／readlink与next／previous缺失记录见[source-inventory.json](source-inventory.json)，结论及当前脚本证据见[candidate-screen.md](candidate-screen.md)。当前只读预检和未来具体命令见[tooling](tooling/README.md)。

## 本轮准备验证

[最终只读预检](tooling/preflight-final.json)已通过：11/11源文件SHA、两根目录身份与集合、十个旧junction及next／previous空名均正确。三类授权／范围负例分别拒绝；6项纯内存状态检查通过，没有真实创建或改名联接。PowerShell命令单语法解析通过但未执行；其动作集合恰为2次Directory.Move、10次next创建和20次junction改名，另有受检父目录创建。

[tool-bindings.json](tooling/tool-bindings.json)绑定18份工具、原件清单、只读helper及导航／ignore候选，SHA为 `ebe8b3381d38e11c51a3cf2de55b71cdda7c4d900dd3c576dd20f01d92e243eb`。旧准备回执及初次库存空列表类型判断失败保留，最终预检用新名字写入；未覆盖旧证据。这里的测试和PASS只针对准备材料，不冒充真实NTFS第三批迁移或全系统无使用者证明。

## 执行前条件与未来顺序

当前没有本批物理授权，也没有第三批主持交接。只准备到执行前，不复用第二批授权或19:30窗口。

1. 将[唯一交接提示词](host-handoff-prompt.md)一次交主持，确认两根、10历史入口无当前使用者；本执行对话接管这两根、10入口及新运维导航的范围，主持不另行操作。主线继续。
2. 用户单独最终授权两根整体rename与10入口切换。窗口起止由这次新交接约定，不能沿用前批窗口或默认顺延。授权、库存、工具和窗口内新11项source-preflight均按SHA绑定。
3. 首个物理动作前增量落地局部ignore，核同E卷、源真实目录／普通单链文件、祖先无二次reparse、目标无冲突，以及两根与10入口的当前使用者。未知使用者、漂移或冲突立即停止受影响批次。
4. 同卷整体移动git_sync，核6文件及源缺失；再移动project_overview，核5文件及源缺失。不复制后删除、不递归合并、不改原文件、不建立旧output兼容junction。
5. 每个入口先建同父 `<basename>.batch3-20261108-next`，经next完整验读该树；formal改名 `<basename>.batch3-20261108-previous`并立即核原ID／tag／精确旧target，再将next改formal并完整验读。每入口通过才处理下一入口。两次rename非原子，正式名有短暂空档；previous只核结构，不要求迁空旧target可读。
6. 两根和10正式入口聚合验收、Astra实际独审，再发布新导航并检查本地链接。保留10个previous和全部WAL／成功／失败回执，不自动提交、推送或发布。

未来共2个整目录移动和10组联接切换（各创建next、两次rename），精确步骤、门禁、独占新回执和暂停条件均在工具手册；当前没有执行这些命令。

## 空间

同E卷rename保留原对象，不额外复制99,446 B，也不释放它。只增加少量联接和目录元数据、导航与执行回执；没有大payload临时副本、压缩包或备份盘预约。本轮实际准备材料大小在acceptance.json记录，不冒称磁盘净变化。原目录作为唯一原件留在现址直至另获授权。

## 暂停与回退

- 某根移动前失败：保留源，目标不得覆盖；不为排障创建旧output兼容入口。
- 仅git_sync已移动：保持已验真的新git_sync和未动的project_overview，按真实回执暂停；不盲目重跑第一步。默认前向完成，不自动逆搬。
- 两根已移动但入口部分切换：保持已验真的两个新target，记录每入口formal／next／previous的实际ID和target。处于两次rename之间时，只在原授权有效且身份完全匹配时完成next→formal；窗口过期或身份未知立即停，不指回空旧根。
- 若真正决定恢复旧物理路径，先另列具体恢复范围，核新树内容身份及旧source精确缺失、无新使用者，再恢复材料并验真，然后恢复相应入口。仅把junction指回旧target不算回退；不能覆盖新任务重建的旧路径。
- 导航和ignore基于实际现态定向调整，保留并发新增，不用旧前像整文件覆盖。10个previous的后置删除不属于本批默认范围。

## 明确不搬

`decoded`、`validation`、`unity`、`field_guide`、`char_roster`、`sample`尚有固定读写、索引路径、当前主线或多消费者，具体最小适配范围见[筛查](candidate-screen.md)和[解包侧筛查](unpack-screen.md)。当前v3／latest／cache_refresh、pages／profiles／rules／ledger、原始输入、vault不动；已完成v1、single／v2、packaging退役不重复。五v2 previous、5317归档、11原位保留、P/v7、四plan／binding、原审查与失败材料保留。

最终结论及未闭合门见[独审](astra-review.json)和[验收](acceptance.json)。准备PASS不等于物理完成或当前可直接执行。

Astra最终独审为 **PASS_WITH_EXPLICIT_SCOPE_LIMITS，技术阻断0**。remaining E1—E3分别是一次主持交接和新局部窗口、用户明确物理授权、有效新窗口内使用者／漂移检查与fresh11及授权SHA绑定。以上是执行余门，不是遗漏的技术准备工作；本轮到此结束，不自动启动实际迁移。
