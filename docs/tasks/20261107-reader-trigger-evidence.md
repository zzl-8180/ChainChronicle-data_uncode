# 阅读页触发条件证据续查

- 状态：完成，原版更新及浏览器验收通过；2026-11-07；阅读页父代理整合。
- 用户目标：继续检查896条紫色，优先59条新核实效果但条件未知项；查实际主线和既有原生证据，能核实直接接入。
- 写入范围：scripts/skill_reader_preview/、reader_full_20261106的前端/条件评估旁注和audit/trigger_evidence_20261107/、本任务卡。主线pages/rules/ledger只读；旧审查目录保留。
- 分工：condition_evidence只读59条；branch_inventory_review只读其余837条；父代理实施及验收。不重做已完逆向或正式生成。
- 标准：源记录身份、条件消费者、玩家可读含义、同技能分支区分分别核对；不凭旧字段缺失判未知，也不凭有正文消除同阈值竞争。条件明确但数值/效果未明时仍留紫并说明具体缺口。

## 结果

- 本轮24条由紫转金：20612的10条条件重复误判；重点59条中的14条全实际分支局部系数相同。当前全库2222条受审项为1350金/872紫。
- 59条逐项按当前主线charainfo的完整pattern引用集合与页面父引用对账，同层同名同flag收集全部父记录，核目标唯一载体、实际槽、字段和完整记录；附加能力变化/未知、额外执行器及差异参数均阻挡。7卡14条恒值：11228、20644、2208、2272、301、8302、8383。其余45条保留紫色；1300有额外执行器，主持比子代理建议再收紧1条。
- 恒值项保留conditionKnown=false，另记branchInvariant=true；页面写“各分支相同”，展开明确触发选择尚未完全解释。不是证明了使用次数、地形或随机条件，也不是解除全技能其他效果疑问。
- 20612两条父记录行为签名相同，仅ID/语音/台词等展示信息不同；保留全部来源后允许解释1stChain以上。签名仍包括全部执行槽、priority/scost/flag和未知字段及缺失状态；不同执行链/未知门不放行。
- 其余条件560条核查：543增益都有同家族不同值反证，不能用恒值捷径；16伤害/1回复按现有来源缺口保留。10条20612外，其他类含使用/地形/法珠/位置/tid门及相同阈值选择歧义。现有局部摘录有部分必要条件，但完整分支优先级/切换没有足够既有证据，不冒称触发完全闭合。
- 地形必要条件已有旁证：ordinary_effects/ability7/trace.json和既有native_conditions.txt的bgf按位AND；20716夜间、7224水边等可读背景可以对照，但不能由bgf=0推断“白天/非水边”或排他基础分支，故本轮不凭必要条件强升金。
- 回归：verify_confidence.js全2236卡2222条通过；verify_player_conditions.js含20612等价正例、未知字段/不同执行槽及20437负例通过；verify_trigger_evidence.js核59/14/45和实际句内标记通过。浏览器抽查20612、11228，控制台错误0，截图11228-invariant.png。
- 重建顺序：review_branch_invariance.py → review_confidence.js → build.py --frontend-only；前两者分别由Python/Node运行，脚本均在scripts/skill_reader_preview/。依赖上轮冻结59条清单remaining_evidence_20261107/changes.json，当前主线和原表仍每次重新读取并校验哈希。旧审查保留。
- 输出：reader_full_20261106/audit/trigger_evidence_20261107/含inventory/changes/branch_invariance_receipt/validation、其他条件清单与增益不同值反证。读取旧字段之外的完整引用分母，逐条留有可追溯依据；未修改主线或进行新逆向。
