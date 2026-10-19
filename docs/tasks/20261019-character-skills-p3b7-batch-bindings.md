# P3B7：下一批描述绑定规则族盘点

- 负责人：C `/root/p3b7_implement`；状态：F1整改C已冻结，待原D R2定向复验；2026-10-19。
- 目标：优先找可复用既有原生字段规则、显著多于 B6 九人的完整纯句规则族；统计来源唯一、页引用、角色去重及执行侧唯一性。
- 允许写入：本卡、自有work与p3b7_batch；B获批后仅必要scripts/character_skills、当前profiles/gaps、本线README/HANDOFF/STATUS。主持进度不写；旧审查/交接不改。
- 共享依赖：v3 缓存、APK 主表、当前 profiles/links、B6 已审证据，只读；不改依赖、不提交、不推送、不发布。
- 边界：旧绑定与数值答案保持；普通/Boss 分域；X1 角色本体不补答案，跨记录绑定须指向真实 pattern→boss 源。其他任务和历史审查不写。
- 阶段 A：复用 B6 type26 有限队列，排除旧 5 对应及原 4 排除，余 80 来源／80 页／80 角色；199 sub、65 类型、69 组合，没有 26/1073/1077，全部普通直接引用及当前源一致。已保存 PartyAbilityInit caller／两个 helper、三个 flag 字段及 ctor、精确类型筛选的当前字节轮廓；不是新原生验证。
- 其他候选：type5 受控 F0 新 22 人，type22 受控 F0 18 人；type5 纯 pattern 实际 3 源／3 角色，含唯一 Boss 子的传授共 6 文本源／6 页／4 角色，Boss 源仅 4 个。本批先不扩。
- 产物：`output/character_skills/description_bindings/p3b7_batch/PHASE_A.md`、两份 inventory JSONL、summary、start_consumer_outline、baseline manifest；最小源码及 records/profiles/rules/summary 开工快照在自身 before。
- A已交接并获批；原PHASE_A.md保持历史提案冻结。
- B 授权：主持已明确仅 80 条 type26 有限队列，Boss 不扩；三入口新原生 8/8，204 过滤样本，forward BinarySearch/真实Compare/双向映射不stub；枚举与泛型接口对象初始化夹具、ParamS_int保护值解码stub如实记录。已新增独立绑定模块和配置入口，准备正式生成及零破坏核查。
- B实际：新增80唯一/80页描述、80/80效果槽、80角色；字段+0，迁移0。当前真实171/提示11599/未知29825；目标中原hint2条。旧82013完整答案/重复数、277用规则/源287、32旧绑定、101/31、非目标片段/分母/scope和完整cid29精确保留。专项10/10、边界1140/1140、原表80根+199唯一子源/199引用、GBK12次、DOM165/165、verify189/189、raw A—P通过；12产物一次重建字节一致。当前本线HANDOFF/STATUS已补B6最终D通过指针及B7待审状态，未改主持进度或历史审查/交接。
- 下一步：P3B7_HANDOFF与冻结清单交主持／新D，C停止写入。整改只续本C；本批自检不称独立审查，未提交推送发布。
- R1 F1：D发现全原始charainfo引用82＝玩家范围80＋范围外敌用2（75370/75528→3233），原links守卫未覆盖后两项。只补原表全引用与范围身份冻结/变更拒绝及更正说明，保留80绑定完整对象和旧全部产物；初审C/D证据及阶段A不覆盖，不研究敌方执行。
- F1完成：全9169选源charainfo/skillid[1+]审计82＝80＋2，源/槽/分类/排除记录加入独立审计与scope；bind保留links/反向sub守卫并新增全原表与范围身份比较。80正例完整绑定对象不变，9个真实原表/范围变更（root/local/children/links不变）拒绝，C定向6/6、8054 GBK2次、定向DOM5项、12产物一次稳定性字节一致。112完整绑定、82013答案/重复、全部旧规则/基线/状态/分母/未知对象严格保留，原生/189/A—P不重跑。
- 更正当前README与本线HANDOFF/STATUS指针；PHASE_A、P3B7_HANDOFF和C/D R1原件不覆盖。整改前快照rectification_f1_before、新RECTIFICATION/定向证据/rectification_manifest交原D R2；C停止写入，无提交推送发布。
