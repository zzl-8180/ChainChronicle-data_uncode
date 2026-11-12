# 阅读页45条触发条件再核

- 状态：完成，原版更新和页面验收通过；2026-11-07；阅读页父代理。
- 目标：优先上轮45条仍紫项目，核主线已有使用次数、地形、法珠条件及选择证据；充分则接入，部分必要条件和完整选择分开。
- 写入：scripts/skill_reader_preview/、reader_full_20261106前端/评估旁注及audit/trigger45_evidence_20261107/、本任务卡。主线pages/rules/ledger只读；旧审查不覆盖。
- 分工：condition_evidence只读使用次数与地形，branch_inventory_review只读法珠/附加能力及其他已有证据；父代理整合与验收。独立中间件work/reader_condition_followup2/。
- 标准：核真实引用和完整同段分支，不能只靠旧绑定字段；数值、效果对应和触发选择分别处理；不凭必要条件强行升金，不为减少紫色启动完整选择引擎恢复。

## 结果及边界

- 45条全查：18条limit门＋2条地形门有可接必要条件；20条无数值门仍有随机/同阈值选择、不同伤害值、附加能力或额外执行器缺口；5条法珠门有计数输入证据，但种类分派与扣费前后仍未闭合。45条均保留紫色，全库1350金/872紫。
- 接入20条必要条件，并按精确层/父ID和完整parentRaw匹配，传播到同一真实父分支44条其他候选，合计64条。不凭卡名、相邻行或数值大小传播；不会把bgf0基础值译成地形补集，也不会把limit0译成第二次以后。
- limit：BossPatternCtrl._pattern@0x10、_useNum@0x18；selector上游将controller保存在x25，positive limit比较其_useNum，_useNum>=limit排除。5174既有片段FindPatternCtrl后计数递增。故写“本分支已使用次数＜1次”，不能写整个技能第1/2/3次或保证后续档次。计数重置及priority选择仍未知。
- 地形：0x100a2cc GetStageNo→0x100a2fc GetBgFlag→sp+0x24；与selector的bgf按位AND衔接。ability7已核背景表原名及flag对应夜间8192、水边1114112。20716增强值标夜间；7224增强值标沙滩／船上／海中（含夜间）。只证明必要门，分支优先级仍未知。
- 法珠：0x100a3c8 GetCurrentJobManaNum→sp+0x34，0x100a3d8 GetCurrentScrapManaNum→sp+0x20；mns/mne两组含边界比较已有静态路径。但职业法珠/斯库拉普的分派、函数内部计数口径及扣费前后未闭合，不把raw2擅改为发动前2颗，也不按scost加减阈值。
- 25条其他（20无门＋5法珠）当前主线正式answers按同卡rule/raw匹配新增0。2000/2001/2002/2005/2015尚无对应已登记消费者规则；2259、283、6332、8323的主伤害同值但附加链未解，1300额外执行器未归属，278随机且伤害本身不同；这些不能靠同值或内部名强升。
- 页面：必要条件紧贴对应紫色数值；行下统一“分支选取待确认”，并保留A/B来源跳转。相同数值合并时如只有部分源已核条件，明确加“部分分支”，不把其中一个必要门套给全部来源。
- 验证：verify_partial_conditions.js 45/20和保持紫色、非全技能使用序号、非地形补集检查通过；verify_confidence.js全2236卡2222条通过；页面20716/2046/7224实看，控制台错误0，截图留在本轮audit。旧审查不覆盖。
- 复现：Python运行review_partial_conditions.py→Node运行review_confidence.js→Python运行build.py --frontend-only（同在scripts/skill_reader_preview/）。输入为上轮45条冻结分母，当前主线card/解码父记录仍每次实读并hash对账；来源摘录/controller元数据已保存本轮audit，不依赖work临时件。
- 经验：确认必要条件后应接到具体数值与真实同父效果，即使未解除紫色也有新增可读结论；不要把“紫色数量没减少”误写成没有证据进展。完整选档证据缺失时，不能以原文增强、数值大小或必要门取代优先级/计数生命周期证明。
