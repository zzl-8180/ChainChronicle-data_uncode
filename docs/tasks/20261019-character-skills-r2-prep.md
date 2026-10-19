# 角色技能页R2方法准备

- 负责人：`/root/type1082_implement`；主持 `/root`。状态：已冻结，待独立R2，2026-10-19。用户已确认11张样本，授权先收口四点并进入R2，R2通过前不执行全量，过审后等主持按已确认顺序调度。
- 写入：本卡、`scripts/character_skills/card_page*.py`、`output/character_skills/r2_preparation/`、`work/character_skills_r2_prep/`及本线增量快照。用户确认的旧pages、R1快照和审查、P3/common/rules/原件均只读。
- 四点：A率/整行确认率/原文A/C四联指标；披露技能候选推断晋级与一般机制层未启用；基础字段同源格式化及名册映射；原始字段字符span和同源别名合并。
- 先披露：实际候选边界3–5例、7229两源critical差异、30004重复源位置及384→387影响，再实现11张新版和有界检查。
- 冻结旧characters.csv名册与cohort，准备默认plan-only的全量入口、续跑/失败留存、固定种子抽样和审查记录方法。不得生成其他角色或重跑native。

## 冻结交接

- 新版入口：`output/character_skills/r2_preparation/README.md`；11张在其`pages/`，旧确认版及R1产物不改。
- 四联指标：A185/387=47.8%；整行确认47/387=12.1%；原文A165/387=42.6%；C202/387=52.2%。B0；A整行未知138/185；整行推断0/387；E0。技能候选晋级/一般机制择句明确未实现，保守不升。
- 5个真实边界、7229双源critical核查、30004四个源位置见boundary_disclosure。4009数值若适用是A，机制B必须无数字新增依据；30338共鸣+10%攻击贡献/45秒只列未审核候选。
- 原387行逐字及原有答案/证据/条件比较不变；387个raw span回切；13组/JSON-HTML/72抽样一致；必要25项通过。两处不同位置重复保留+2，384→387不变；11卡同位置别名合并0。合并键含执行档、父记录完整hash、组/等级/真实字段位置，未按同文跨档合并。
- 名册冻结2236唯一cid：ge60=34、40to59=290、20to39=436、remaining=1476；复杂760及seed20261019从其余1476中30卡合并成790张核读集合。四个cohort仅PLAN_ONLY。批处理仅实际执行授权7229与同签名resume复用1次；没有全量/其他角色输出。失败留存实现，未注入故障或模拟OS崩溃。
- 批入口`card_page_batch.py`默认plan-only，显式manifest/cohort；逐卡构建/写出，成功receipt后复用，失败另存并保留旧成功文件，cohort并列四联指标，audit_queue明确未审；后续按主持调度。非完整解包发行包，无干净机器复现声明。
- 运行：`.venv\Scripts\python.exe -B scripts/character_skills/card_page_r2_prep.py --input-root . --output output/character_skills/r2_preparation`；定向25项用`card_page_check.py --input-root . --output output/character_skills/r2_preparation/pages`。四cohort plan见`r2_preparation/plans/`；7229续跑见work/batch_smoke与batch_validation.json。
- 旧确认版29文件哈希未变。源码/依赖及本版输出独立快照：`work/character_skills_r2_prep/snapshots/20261019-r2-preparation-home-fix-frozen/manifest.json`。不复制大游戏输入、无全项目哈希、无native重跑、无本实施者浏览器验收声明。
- 剩余限制：候选及一般B层未启用；职业映射是推断；成长/战斗所属名称未知；实机节奏/完整引擎/玩家资格未验证；全量生成与约7600–7900行实际核读未执行。机器约4.6秒/11卡不等于人工吞吐，预算估算见space_time_budget.json，按既定停止线由主持观测。
- 停写等待主持转独立R2意见，不自派审、不自行开始cohort。

### 主持预览后的home命名空间纠正

直接读取homelist与已审filter_dictionary.home及skilllist_types.py既有IsTargetHome/get_home证据；只改新basic映射，职业继续roster推断。7229 home1→義勇軍；30236 home8→湖都。缺home所属未知，不以place地理值替代。旧roster worldinfo地理join及用户截图差异留详情，旧工具不改。此前20261019-r2-preparation-frozen独立保留为修正前快照，不作为最终R2输入；当前修订见home_mapping_correction.json及home-fix-frozen增量快照。技能387行及四联指标不变，无新native。

最终定向检查在重建完成后25/25通过。一次过早启动的检查读到了重建中的部分HTML而失败，等待生成结束后重试通过；没有据此扩语义研究或修改已审数据。当前home边界检查包含4→副都、5→聖都、真实0保留未知、缺失/null时不以place替代，均通过。

## R2 F1–F5追加整改（当前冻结）

用户已批准追加最多3共享点（基准35，硬止38），只做F1–F5及同Astra定向复验，完成后先暂停。主持21:44观测36；非精确本任务耗费。本实施者现在冻结停写，不执行完整cohort/760。

- F1：cohort/run独立不可覆盖报告、queue、signatures、失败收据；cohort latest仅指针。当前同签名receipt累计及未解决最新失败持续汇总，排除过期卡。requested/subset与completed/expected/cohort_complete分开。跨cohort campaign带每批签名/时点快照与未审队列；没有人审核完成声明。
- F2：extraabilitylist/passivelist/denju_lblist三实际nested源加入29项依赖/receipt签名。实际11样本读取路径闭包检查、各路径独立签名变化导致重建且旧量排除通过；未改原输入、未全项目hash。
- F3：显式备份card/HTML/receipt，设blocker后替换；二次replace失败恢复旧三文件；注入回滚失败时受影响路径/错误真实保存，INVALID/blocker禁止SUCCESS复用，下一次成功重建恢复。无OS断电/并发读事务保证，不递归清理。
- F4：真实reference slot/level/父记录哈希进入执行身份，不用遍历ordinal；旧profile绑定按reference_field和必要记录身份匹配。等价alias不推动后续展示序号/row_id。真实build29复制同skillid[1]仍N2合并1；不同槽/父limit_break/level均N3不合并；30236前插alias后其他原行ID/值/证据不变。原11卡387与30004不同源位置重复保留。
- F5：raw_value_evidence确认；unit_evidence/formatting_evidence_level推断，正文可见手工s0及charainfo→BattleParam赋值链未全证限制。2.0秒/下保留；无新native。
- 自检：`card_page_r2_fixes_check.py --input-root . --output work/character_skills_r2_prep/f1_f5_fix_checks_final_20261019` 19/19通过；重建11页后card_page_check.py 25/25通过，387原语义/四联185/47/165/202不变，旧pages29文件hash不变。仅授权样本小输出与故障注入，无完整cohort。
- 当前小收据：`output/character_skills/r2_preparation/f1_f5_fixes/`；完整故障现场/备份留独立work，不覆盖旧R2/R1。最终增量快照：`work/character_skills_r2_prep/snapshots/20261019-r2-f1-f5-frozen/manifest.json`。前home-fix与更早快照只作历史，不改动。
- 下一步仅主持唤醒原Astra定向复验F1–F5；无论复验是否通过，本实施者先暂停等待用户后续指令，不自动全量。
