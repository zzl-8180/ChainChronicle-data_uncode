# 分支选择、使用计数与扣珠时序核查

> 后续更正见[剩余五条核查](20261107-reader-final5-evidence.md)：12236目标记录实际有hpend=100，上轮“缺上界”归因不成立；新证据已接3条、仅278两条卡面对应保留。下方40/45与缺口表是本轮历史结果，当前以final5回执为准。

- 状态：完成，选择旁注已接原版并验收；2026-11-07；阅读页父代理整合。
- 用户目标：查主线已有优先级、计数生命周期和法珠扣费时点证据；能闭合直接接，确需新研究列准确缺口，不重复改待确认文案。
- 写入：scripts/skill_reader_preview/和reader_full_20261106展示旁注（仅证据闭合时）、audit/selection_order_20261107/、本任务卡；主线和旧审查只读。
- 分工：condition_evidence只读priority/_useNum；branch_inventory_review只读法珠计数与扣费调用时序；父代理核对交叉证据、整合和必要验收。中间件work/reader_selection_audit/。
- 边界：先读既有研究和片段；不扩大为完整战斗引擎恢复。部分必要门不当完整选择，不按数值大小和pattern顺序猜档次。

## 实际结果

- 重点45条：40条选择条件闭合（29使用阶段、6地形、5法珠/废料），5条继续保留。按精确父记录同步其它效果，共104条由紫改金；另7条条件已明但效果对应仍未闭合，继续紫。全库2236卡/2222受审答案当前1454金/768紫，未改正式主线、原值或原confidence。
- 复用既有镜像、metadata和主线研究，补读相关函数的有界静态片段；没有恢复完整战斗引擎、重新采集或冒称实机验证。元数据/恢复镜像哈希、相关21份法珠方法片段、选择与计数片段、全部父引用与顺序已保留本轮audit。
- **priority是抽选权重，不是最大值优先**。think_attack常规预测bFirst=false/allRandom=false按整数区间抽选；若没有命中（含权重全0）取第一个有效候选。bFirst=true另有直接首项路径。100/0的地形双分支因此可确定，而100/50不能误判成只取100。整数Random.Range等端点返回端点的API契约用Unity官方2021.3文档旁证，已核本机调用确为Int32重载。
- makeExAttackPatternList按pattern0..8建立控制器并清零各自useNum；预览不递增；手动显式ID执行FindPatternCtrl后只递增选中控制器一次；setListPattern复制引用并不重置计数。完整线性limit=[1,...,1,0]、权重=[正数,0,...,0]的阶段可推导。只有原文最大变化次数与阶段数一致才写“强化N次”；缺此句也可按原生证据写初次/再次，不反复因旧文字缺失保留未知。
- **普通手动UI执行缓存分支ID**：UpdateCharaInfo→GetExecSkillInfo（subMana/nextChain=true）→写_patternId；点击先ExecSpSkill扣珠，再取缓存ID→显式CreateExecSkillList重载，不重选。自动无ID重载会另行选择。中途“实际施放一律按扣珠后重选”的判断已纠正，不能复用。
- 法珠/废料：12032为选档时废料0–3/4–12；12226为0–2/3–12；20619为0–1/2–12。废料计数不模拟减费；7654为预测扣费后职业法珠0–2/3–12，不擅改“发动前至少4颗”。全部保留上界12，不声称计数没有更大值；范围外不推广。
- 同flag不同名称的潜在竞争父记录必须排除；完整charainfo引用与主线父集合必须一致；新标签依据真实父记录、顺序及完整raw匹配，不能按网页数组位置或数值高低猜。父级选择回执不复用别的数值来源身份，触发来源单列triggerSource。
- 页面2046已显示初始/使用后强化1次/强化2次；20716已显示夜间/非夜间；12226已显示废料范围。7654强化6倍虽条件已明，但原效果绑定仍缺依据，继续紫色；原文“至少4颗”作为原文保留，不覆盖当前字段推演。

## 需要另行研究的准确缺口

| 范围 | 已有证据 | 尚需证明与入口 |
|---|---|---|
| 278两条 | 完整原表含flag8、多个权重100卡面分支 | getPatternAttackList@0x100a0f0和CheckEntry入口的flag8/卡面状态与全部候选映射；不能只给两个已解释数值各50% |
| 12236两条 | 特殊模式flag32768父记录、完整原表引用在回执 | 稀疏父记录缺hpend等字段，不能补100；核BattleBossPattern.FromJSONDictionary@0x1a6d95c、.ctor@0x1a6e0b4和daBattleBossParameter.getBossPattern@0x1a701ac实际源层/初始化，随后才能准入选择模型 |
| 5300一条 | 森林bgf4、limit3、高权重与基础分支 | 同样先核稀疏字段初始化；再对地形改变与同分支3次限制作联合状态模型；不能只用“初次/再次”二档模板 |
| 7654固定发动前阈值 | 预测先扣effectivePredictionCost再比较，普通点击执行缓存 | BattleParam.get_skillCost@0x1105f6c与selector@0x100a3e4..434/0x100ad60..80的实际费用、减费、特殊资源；名义scost1不足以证明所有场景发动前4颗 |
| 缓存即时性 | UpdateCharaInfo写缓存、GetPatternId读缓存、点击显式执行 | PanelCharaInfo.Update@0x146be3c、UpdateCharaInfo@0x146cc40、OnClickSpSkill@0x13a1dc8的刷新调度和插入事件；本次只认选档快照条件 |
| 跨波/复活/其它触发 | 新控制器清零、复制列表不清零、两执行重载不同 | 逐个查makeExAttackPatternList@0x10ffc98及setListPattern@0x112aaa0在对应生命周期的调用者；自动重载@0x1295878与显式ID重载@0x1296718分别追，不承诺整场永不重置 |

## 验收与复现

- 验证：review_selection_order.py实际父分母、权重全部抽样区间、99个地形背景、使用计数序列和0..12计数逐点枚举通过；verify_selection_order.js 40/45及回执身份/句内顺序通过；verify_confidence.js全库、verify_player_conditions.js、verify_partial_conditions.js兼容后续证据通过。页面2046/20716/12226/7654/278抽查，错误日志0。
- 本轮审查独立保留：output/character_skills/reader_full_20261106/audit/selection_order_20261107/，含selection_receipt.json、inventory/changes/validation、selection_validation、browser_validation、native/和截图。
- 生成顺序：Python build_mana_timing_receipt.py（仅原生事实/源版本更新时需要）→Python review_selection_order.py→Node review_confidence.js→Python build.py --frontend-only，均在scripts/skill_reader_preview/。当前生成器从正式保存的证据片段读取，不依赖本轮临时work目录；原生重读脚本与必需输入见audit README。
- 经验：源码字段名不是算法。priority权重、bFirst直接返回、全零fallback必须分别识别；同名重载不是同一流程，手动缓存显式执行与自动重新选档不可混用。本次对话的中间判断以此证据和最终回执为准。
