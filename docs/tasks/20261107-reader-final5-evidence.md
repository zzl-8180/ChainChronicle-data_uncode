# 剩余五条分支证据核查

- 状态：完成，原版已接入并验收；2026-11-07；阅读页父代理整合。
- 目标：278两条随机卡面、12236两条稀疏初始化、5300一条地形限次。先主线已有材料，闭合直接接入，缺证据保留并记录。
- 写入：scripts/skill_reader_preview/和reader_full_20261106展示旁注/前端（限证据闭合项）、audit/final5_evidence_20261107/、本任务卡。主线和历史审查只读。
- 分工：condition_evidence只读随机卡面，独占work/reader_final5_random/；branch_inventory_review只读稀疏初始化及地形限次，独占work/reader_final5_sparse/；父代理整合验收。
- 标准：同层完整父分母、真实加载路径和字段缺失/0/null分开；不因通用constructor或当前展示字段缺失直接判结论。随机概率、候选图案对应、实际施放、局部数值用途分别证明。不恢复完整引擎。

## 实际交付

- 本轮5条：3条选择条件闭合，278两条卡面对应继续紫色。与同父其他参数一起更新后8项由紫改金，另1项条件已明但数值效果绑定仍不足；受审2222项当前1462金/760紫。最初45条中的43条选择条件已接入。原始数值、原confidence、主线pages/rules/ledger及原始统计不改。
- 12236：CACHE父41223602/05均显式hpend=100，上轮“缺hpend导致HP未知”归因错误。本轮真正补齐的是主加载路径、缺失priority初始化0以及无其它门的0/100权重模型。常规UI bFirst=false预测必选05；02显示“旧分支（常规选档不选用）”，不是可切换的另一实战档位。资格检测bFirst=true和其它显式ID调用仍有不同路径，不能把“不选用”扩成任何代码永不执行。
- 5300：森林背景（含夜间）且森林控制器_useNum<3选40530000；非森林，或该控制器已用≥3次，选40530001。对全部背景×计数0..5×有效随机抽值枚举，并验证离开森林、回来继续计数、耗尽回基础的顺序。限当前同模式控制器生命周期，不承诺跨波/复活/重建不重置，不把计数当保证命中或成功获取法珠次数。
- **实际CACHE JSON加载证据**：getMasterBossInfo回调@0x19e7844→daBattleBossParameter.FromJSONDictionary@0x1a7086c→每记录new BattleBossPattern/.ctor@0x1a6e0b4→FromJSONDictionary@0x1a6d95c。不是BattleBossPattern_J装载。hpstart/hpend/priority构造为0；字典缺键跳过setter，不能补100。getBossPattern@0x1a701ac只在整条primary记录查不到时回退AB，不逐字段合并。这3条目标的HP上界原本都存在，不能继续以旧缺字段说法挡住。
- 278：完整charainfo pattern0..3四父。普通池30027800/01/02为flag8，满槽超必杀30027803为flag4/type78；selector@0x100a7b4..7d8按SSkillGaugeFull互斥，普通池只有前三项。权重均100，整数区间[0,100)/[100,200)/[200,300)，已经300点全枚举。这里是每次选择调用的池，不能声称实际点击/施放各1/3，因为UI缓存和刷新时点未穷尽。

## 仍保留的两条：缺什么证据

- 5.1、5.6倍各属于普通随机池的哪个原记录已清楚，但`sp_komodia03/02/01`到具体卡牌画面的映射仍未建立。不能把动画名数字后缀当作扑克牌花色或直接命名Joker。缺的是映射证据，**不是已经证明资源文件缺失或需要重新采集**。
- 下一步入口：BattleBossSkill.get_spmotname@0x1a6ea74 → BattleParam.get/set_SPMotionName@0x10f298c/0x10f29e8 → CharaInfoCharaModel.PlaySpMotion@0xda3ea4 / CharaInfoModelCtrl.PlaySpMotion@0xdad4b8。需沿已有Animator/AnimationClip/特效/材质/纹理的真实bundle与对象引用找到呈现卡面，再做视觉确认；本轮没有展开完整素材系统。
- 30027802另有skillflag0_0=16，metadata中ATTACK_FLAG.DOWN枚举默认值为4；16与1<<4的对应仍须装载/消费链证明，即使DOWN成立也不替代Joker画面绑定，更不能给另外两动画命名。
- 保留完整4父、3普通子记录和满槽排除证据；不把只显示的两个倍率当完整随机分母，也不因为已知随机池就虚称具体卡面条件已确认。

## 验证与入口

- review_final5_sparse.py / review_final5_random.py：当前原表、主线父分母、loader/metadata与镜像哈希核对；源读前后不变；真正缺hpend的反例保持0，不补100。
- verify_final5.js、verify_confidence.js全库2236卡、verify_player_conditions.js通过；页面12236/5300/278实看、控制台错误0。5300的森林候选另有原效果绑定缺口，虽条件已核仍紫；没有被本轮选择证据掩盖。
- 产物：output/character_skills/reader_full_20261106/audit/final5_evidence_20261107/，含sparse_receipt、random_pool_receipt、inventory/changes、final5_validation、validation、browser_validation、native/sparse与native/random及截图。
- 生成顺序：Python scripts/skill_reader_preview/review_final5_sparse.py → review_final5_random.py → Node同目录review_confidence.js → Python同目录build.py --frontend-only。只读原生重读入口read_final5_sparse_native.py和既有read_selection_native.py；证据已从临时work分离保存，原恢复镜像/metadata依赖仍显式为work/protection/下两文件。
- 经验：旧“未知原因”也是待核结论，必须回看实际字段。应区分“字段缺失且默认未证”与“字段存在但选择模型未覆盖”；原表明确hpend=100不能被导出摘要未打印该字段误写成缺失。J/AB转换默认也不能移植到primary JSON装载路径。
