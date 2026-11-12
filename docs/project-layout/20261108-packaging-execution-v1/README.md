# R01—R04整改与只读验证

2026-11-08。Sol high实施与整合，Astra high独立复核 **PASS_WITH_EXPLICIT_SCOPE_LIMITS**，R01—R04整改关闭，见[补充验收](acceptance.json)。物理执行条件仍为 **NOT_MET**。本轮仅代码／文档整改和只读验证；未迁移业务文件、切换联接、删除候选或合入共享导航。本目录是新增修订，不覆盖原独立审查及冻结清单、原验证回执。

## 整改对应

| 项 | 实施与证据 | 限定 |
|---|---|---|
| R01 | 新只读 `scripts/project_layout/check_retirement_survivors.py`；[当前1406对](r01/current-full1406.json)、[测试与用法](r01/README.md) | 1270外部survivor＋136 payload临前双端内容门；current通过不是实际迁址后archive通过；失败组source保留，不要求主线全停 |
| R02 | 新只读 `scripts/project_layout/check_retirement_alias.py`；[逐入口用法及回执](r02/README.md) | 单cycle、临时next、previous结构身份和正式内容验收分别处理；每alias真实拼写读完整142文件；模拟不等于NTFS切换 |
| R03 | [执行合同](EXECUTION.md)中迁址前与删除前均直接承接原execution-overlay | distribution README为5350 B和既定SHA；冻结表4789 B行不改 |
| R04 | [新导航补丁](shared-navigation-r04.patch)、[基底与修正回执](r04-patch-receipt.json) | 完整项目相对交接路径已修；只为准备态审阅，当前check通过未合入，迁后必须按真实回执更新状态再重定基底 |

原外部审查的REQUEST_CHANGES保留原字节；新验收只说明其四项整改的关闭情况，不冒充原第三方已重新出具PASS，也不将准备／模拟结果写成物理完成。

## 两处口径统一

保护的是保留项和清单外证据；不能笼统禁止一切“隔离副本”从而与精确1607项DELETE矛盾。5317项保留材料仍只能在明确迁移授权后精确移交验真，11项原位材料不动。

第一次rename后，previous只核原联接对象tag／target／fileID并出结构回执，不能要求迁空旧target完整可读；第二次rename后，正式new入口必须经alias自身全量验读，之后才处理下一入口，最后五入口聚合。结构PASS不是内容PASS。

## 剩余授权与交接

主持接收回执已确认五入口由 `new-provider/kimi-k3-1-pro-261024` 统一接管，材料Sol high验收、Astra high独立复核；不再把“找负责人”当未完成问题。仍需：

1. 用户明确保留材料迁移／五联接切换授权；本轮不含任何物理授权。
2. 已接管主持落实五入口共同30—60分钟建议窗口，临窗再核活动和对象身份；主线无需全局停工。
3. 5317保留材料真实新位置逐项验真，研究139项、P指定旧源码、两恢复manifest、四plan绑定及P/v7保护继承实际验收。
4. 新临时／previous／正式入口按阶段真实验证，最后五入口聚合；这些尚未实际切换。
5. 共享根在真实阶段整合；本轮R04是准备态审阅稿，不能迁后原样写入“尚未迁移”的旧状态。保留并发新增，按真实回执重生成。
6. 汇总真实迁移／切换／保护验收后，由用户最终确认1607条删除候选；最后删除前再运行archive完整1406对及源／overlay／reparse／并发检查。旧根空目录和五个改名旧junction另列后置动作，不默认包含。

旧ZIP和173份旧生成载荷的精确重放损失已披露；manifest、源码前像和当前数据不是旧ZIP完整备份。新文档不扩大任何删除范围。
