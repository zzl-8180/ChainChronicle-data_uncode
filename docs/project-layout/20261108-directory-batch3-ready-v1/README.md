# 第三批完整目录整理：准备交付

最新安排：用户已要求合并全部剩余整理事项，本目录两棵运维树及十入口**不再单独交接或启动**，改并入[一次总交接方案](../20261108-unified-output-migration-v1/README.md)。本目录准备前像、独审和18项绑定原样保留；原技术PASS不扩大为其它根的验收。

**仅准备，未搬迁、未改正式入口、未合入候选导航和ignore。** Sol执行准备，Astra独立复核；当前没有第三批主持交接或物理授权，不沿用第二批窗口。

最终技术准备结论：**PASS_WITH_EXPLICIT_SCOPE_LIMITS，阻断0，ready_for_execution=false**。只剩一次主持交接／新窗口、用户最终物理授权，以及该窗口内实际使用者与新11项source-preflight复核。

本批范围仅为两个历史运维目录，共11文件、99,446 B：

| 原目录 | 拟目标 |
|---|---|
| `output/git_sync_20261024` | `operations/records/git-sync/20261024` |
| `output/project_overview` | `operations/records/project-overview/20261020` |

无业务源码适配；保持原文件字节，10个C14—C18历史联接须随迁址逐一切换。候选目录内旧清理／审查提示词和“可删除”文字是历史证据，不作为当前行动指令。

- [完整方案：范围、引用、空间与回退](REPORT.md)
- [精确原件／10入口库存](source-inventory.json)、[外部路径映射](path-map.json)
- [候选筛选](candidate-screen.md)、[不搬的解包侧目录](unpack-screen.md)
- [只读预检与具体未来命令](tooling/README.md)
- [本轮最终11项预检](tooling/preflight-final.json)、[18项执行材料绑定](tooling/tool-bindings.json)：旧准备回执及初次失败均留存，不覆盖、不当作未来窗口内的新预检
- [候选导航及局部ignore身份](navigation-preparation.json)
- [仅成功后应用的导航补丁](navigation-after-success.patch)、[首动作前的局部ignore补丁](local-ignore.patch)
- [唯一一次主持交接提示词](host-handoff-prompt.md)
- [Astra独立复核](astra-review.json)、[准备验收及空间观察](acceptance.json)

本批不删除、复制大载荷、生成正式数据或改四共享根；不提交、推送或发布。当前v3与主线继续。前两批已完成路径、五v2 previous和packaging保留材料均不再处置。
