# 第三批唯一一次主持交接

请一次性核对并交接第三批目录整理，后续由本执行对话统一整合、迁移、入口切换、验收和导航；主持不并发搬迁、切换或合入本批候选。主线研究、规则修订、正常生成和校验继续。本次只需一份完整回执，不逐步往返协助，不执行物理操作。

项目根：`E:\代码项目\锁链战记数据解包`

请先读 `docs/project-layout/20261108-directory-batch3-ready-v1/` 的README、REPORT、astra-review.json、source-inventory.json及tooling/README.md、runbook.md、recovery.md。不必重做全仓调查、重复准备测试或重验已完成前两批。

## 一、两棵完整树与对应十入口

- `output/git_sync_20261024` → `operations/records/git-sync/20261024`，6文件、29,828 B。
- `output/project_overview` → `operations/records/project-overview/20261020`，5文件、69,618 B。

以下每个父目录各有 `git_sync_20261024` 和 `project_overview` 两个正式junction，共10个：

1. `work/c14_delivery_20261103/impl/isolation_input/output/`
2. `work/c15_delivery_20261103/impl/isolation_input/output/`
3. `work/c16_delivery_20261104/impl/isolation_input/output/`
4. `work/c17_delivery_20261106/impl/isolation_input/output/`
5. `work/c18_delivery_20261106/impl/isolation_input/output/`

请核实两源根和十入口当前实际使用者、任务写域及未登记调用；检查旧概览清理／审查提示词有没有被其他任务重新激活、Git历史回执是否正被读取。原周期结束、无静态命中或旧进程扫描不能单独证明此刻无人使用。发现使用者或不能确认时，在同一次回执中给出具体冲突，不自行停止其他任务。

## 二、一次交接闭合的范围

1. 明确两根与十入口实际接管者，将本批操作权交执行对话；只释放这十入口的局部使用窗口，不暂停主线。
2. 请允许执行对话在用户最终物理授权后开启一次不超过30分钟的局部窗口，记录实际UTC起止，临前重新核使用者，不需要第二次主持确认；若必须固定时间，请本次直接给出有效窗口和限制，过期不顺延。不能沿用第二批窗口。
3. 确认本批不需要业务源码补丁；旧报告、README、提示词、Git回执、`paths.nul`保持原字节，旧路径由外部path-map承接。历史可删除判断不构成这次删除授权。
4. 交接新建 `operations/README.md`、`operations/records/README.md`及 `operations/records/.gitignore`的本批写域。当前三文件不存在；如届时出现则先读并增量整合，不覆盖并发内容。局部ignore先于物理动作，导航仅在真实迁移、十入口验收和独审通过后发布；根.gitignore和四共享根不改。
5. 同卷整体移动两树、各根验真后，十入口逐个创建同父next并验读、formal→previous核结构、next→formal验读；两rename非原子，存在短暂正式名空档。十个previous保留停用，迁空后不盲指回旧根，不创建常驻旧output兼容联接。

## 三、保留与授权

当前v3／latest／cache_refresh、rules／pages／profiles／ledger、原始输入、vault、P/v7、四plan与binding、5317归档／11原位材料均不动；不重复v1／single／v2／packaging退役，不处置五v2 previous。其他候选目录暂不启动。

本交接不是用户最终物理授权。执行对话仍须取得对本批两根和十入口的明确授权，在新窗口内做新11项source-preflight、绑定SHA并检查漂移，才能开始。不得迁移、删除、联接切换、合入导航、生成、提交、推送或发布。

请一次回复：检查时间与实际使用者证据、两根／十入口接管人及可释放范围、窗口安排、新导航／ignore写域，以及全部已知冲突。回复后由执行对话接管，无需主持逐步协助。
