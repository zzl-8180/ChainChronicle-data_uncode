# 转交主持的提示词

请接管“打包支线保留材料真实迁移／五入口切换”后的共享导航整合。主线无需停工，不要另起迁移或切换。

项目根：`E:\代码项目\锁链战记数据解包`。

先读当前 `AGENTS.md`、`HANDOFF.md`，再完整读取：

1. `docs/project-layout/20261108-packaging-physical-v1/REPORT.md`
2. 同目录 `physical-independent-review.json`、`archive-independent-review.json`
3. `run-immediate-bound/junction-summary.json`、`all-five-new.json`、`previous-final-structure.json`
4. `run-immediate-bound/verify.json`、`move-exit.json`、`final-untouched-protection.json`
5. `authorization-immediate-amendment.json`、`rollback-manifest.json`

真实结果已完成：用户后来明确“不再等到13:00，清点完成后开始”；5317项保留材料同卷迁至 `operations/history/retired-packaging/20261108/`，108,004,454 B；北京时间12:58:01迁移结束，13:06:48五入口切换结束，13:09:15 Astra最终独复核通过。所有物理动作均早于14:00。不是RAM模拟或准备态PASS。

五入口分别为：

- `work/c14_delivery_20261103/impl/isolation_input/output/share_bundle`
- `work/c15_delivery_20261103/impl/isolation_input/output/share_bundle`
- `work/c16_delivery_20261104/impl/isolation_input/output/share_bundle`
- `work/c17_delivery_20261106/impl/isolation_input/output/share_bundle`
- `work/c18_delivery_20261106/impl/isolation_input/output/share_bundle`

正式入口均已指向 `E:\代码项目\锁链战记数据解包\operations\history\retired-packaging\20261108\share_bundle`，各142文件验读及聚合通过。五previous仍保留原ID/tag/旧target，作为停用证据，不供业务访问；next均无。历史入口冻结期间的验收已完成，请按新正式入口接管后续使用，不用previous读取已迁空的保留材料。

本次请只整合 `AGENTS.md`、`HANDOFF.md`、`STATUS.md`、根 `README.md`：重读当前文件，以实际新路径和本轮回执更新状态／当前入口，重定基底，保留并发新增内容和AGENTS第8节。不要原样合入 `shared-navigation-r04.patch` 的“尚未迁移／目标不存在”准备态文字；不要整文件覆盖。P/v7和四plan仍保留原字节，历史source通过已验真的外部runtime archive映射承接，不能改写冻结保护键来冒充历史原件变化。

请回传四根的实际差异、重定基底／引用检查回执及仍有冲突的条目。原独审报告、冻结表和历史前像继续保留。不自动提交、推送或发布。

1,607项DELETE候选、11项原位材料、五previous及旧空目录均未删除。本提示词不授权删除、迁移或切换；不要再次执行已完成的物理动作。未来删除仍须用户单独确认，且临前重新通过archive模式完整1,406对内容门及漂移检查；previous和旧空目录不纳入该1,607文件授权。主线研究、规则、正常生成与校验继续，勿运行旧打包／清理／恢复／冻结verifier。
