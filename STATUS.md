# 项目状态

更新：2026-10-21（角色技能页主线·独立第三方审查与复审整改，本轮）。**当前阶段**：2236/2236 角色页交付完成（玩家视角版式、立绘、图例、入口两页齐全）；独立第三方初审整改（H1 条件分组／M2 逐答案 source／M5/L1 分层／M1 入口页）与复审五项整改（核心看板落地／交接收敛／分享清单绑定当前版本／Y.G. 选题纠正／检查器豁免收紧并定向用例验证）均已落地。**核心看板与全部指标以 `docs/tasks/character-skills-progress.md` 唯一当前块为准**（本文件不再维护数字副本；当前 campaign run `20261020T172510847737Z-a6c71db2` 可在看板与 `output/character_skills/share_manifest_20261021/` 核对）。**必要限制**：本轮新增技能数值答案 0；30236 基线 3 处历史缺失登记保留原样；未打包、未上传、未发布；批 8–9 不按原排期自动恢复、选题待用户裁决。旧 P3 批次线冻结；下列 2026-10-19（含）之前各条为历史记录（其“当前/待D/进行中”表述以各时点为准）。

更新：2026-10-19（角色技能P3B10 C冻结待新D，**该时点历史记录**）。28条type67武器/职业逗号纯句，新增28唯一/28页描述、54唯一/54页效果槽、28cid；25主组47槽＋3缺主武器type组7槽，页面明示缺口与N>=2，只有运行时自身合格且实际计入才换述其他>=1。Constants武器跳表逐值核，不套22+枚举；实际装载/装备/资格仍为前提。字段+0，当前398真实/11409提示/29788未知，2233部分/0仅未知/3完整无迁移。C专项12/12、边界94/94、原行61/61、GBK8/DOM39、verify189/A—P、12产物一次稳定；旧82013完整字段/重复、311绑定/强度、101/31、非目标/分母与三完整profile整体保留。本批新native执行0，复用B9已审证据及夹具边界。见[交接](output/character_skills/P3B10_HANDOFF.md)/[命令与限制](output/character_skills/description_bindings/p3b10_batch/README.md)。本批待独立D；未提交推送发布。

P3B9已由独立D R1[带明确范围限制通过，问题/阻塞/整改0](output/character_skills/review/p3b9_20261019_type67_bindings/REPORT.md)。以下旧C待审/PENDING为冻结历史，不代表当前状态。

更新：2026-10-19（角色技能P3B9 C冻结待独立新D）。仅普通type67条件纯句，新增162唯一/162页描述、336唯一/336页效果槽、162角色；字段增量0，当前82875/82013/81996、scope10095/72780、用规则277/源287不变。41595=真实370＋提示11437＋未知29788，角色仍2233部分/0仅未知/3完整；三旧完整profile整体、149旧绑定/强度、82013完整答案/重复、101/31、非目标及未知/分母保留。156主组、6条文本未写计数2的差异、30620310持有者职业缺失排除分别留证；实际装载、同阵营alive列表后active、职业聚合位图门槛与自身条件计入明示。C native9/9、专项10/10、边界2117/2117、GBK14/DOM338、verify189/189、原表A—P与相关12产物一次重建稳定，见[交接](output/character_skills/P3B9_HANDOFF.md)/[命令与限制](output/character_skills/description_bindings/p3b9_batch/README.md)。不是独立审查或实机结论。P3B8已由独立D R1[带范围限制通过/无整改](output/character_skills/review/p3b8_20261019_boss_bindings/REPORT.md)，下段旧C待审为历史冻结。未提交推送发布。

更新：2026-10-19（角色技能P3B8 C冻结待新D）。自身F0/Boss type5纯直线22＋type11全体HP回复15，新增37唯一/37页描述、37唯一/37页效果槽、37角色各一句，字段+0。当前41595=真实208+提示11599+未知29788；字段82875/82013/81996、页scope10095/72780、未知字段427176/字段缺口5560/断链3不变。2236人按原标准自然重算，仅2020/5023部分→完整，现2233部分/0仅未知/3完整（29/2020/5023）；新完整仍13/14未知字段，旧29完整对象及24未知槽原样。原生9/9、专项10/10、边界565/565、raw37根+13另域、GBK12次、DOM80/80，verify/A—P和一次相关稳定性结果见[证据/命令](output/character_skills/description_bindings/p3b8_boss/README.md)与[交接](output/character_skills/P3B8_HANDOFF.md)。伤害/回复保留运行时B公式/BY_TYPE；13条denju不借自身答案，普通同号不跨域；旧82013完整答案/重复数、277用规则/源287、112旧绑定及强度、101/31和全部非目标/分母/未知对象保留。仅C自检，未实机/真实浏览器验收、未提交推送发布。

P3B7已由原D R2闭合F1，带明确范围限制通过，剩余P0/P1/P2/阻塞/需整改均0，见[最终报告](output/character_skills/review/p3b7_20261019_type26_batch/REPORT_R2.md)。82原始引用=80当前玩家+2范围外，新增/移除/槽位/源/身份变更拒绝经D独立复验；12正式产物与R1字节相同。以下B7待复验及旧批待审是历史阶段记录，不改变最终指针。

更新：2026-10-19（角色技能P3B7 R1 F1整改完成，待原D R2）。原D未发现数值错误或旧成果破坏，指出全原表引用范围未覆盖名册外2条敌用引用。独立重扫9169选源charainfo，82原始引用＝当前2236玩家范围内80＋范围外2（75370/75528分别slot2/3→3233）；槽位只作原表事实，后两明确排除，不扩敌方执行/玩家覆盖。现scope及bind增加全表skillid[1+]原始引用和名册/links/profiles身份守卫，root/local/children/links不变的9类原表或范围变更均拒绝，80正例完整绑定不变。C定向6/6、8054实际GBK2次、DOM5项、12正式产物一次重建字节不变；112完整绑定、82013答案/重复、277规则/源287、101/31、全部状态/分母/未知对象保留。原生/189/A—P未变未重跑，初次C及D R1证据、阶段A及旧交接不覆盖。见[更正/交接](output/character_skills/description_bindings/p3b7_batch/RECTIFICATION.md)与新rectification_manifest；以下旧待初审字样是历史冻结状态。

更新：2026-10-19（角色技能P3B7，C冻结待新D）。80条普通type26完整开局基础玛那句已绑定，新增80唯一/80页/80角色、80/80效果槽，字段答案+0。当前描述41595＝真实171＋提示11599＋未知29825；目标中78未知和2提示升级，旁句及原分母保持。字段82875/82013/81996、scope10095/72780、未知参数427176、字段缺口5560、断链3不变；状态迁移0，部分2235/仅未知0/完整1，原完整cid29保留。旧82013完整答案及重复数、277用规则/源287、32旧绑定/强度、101基线答案/31片段精确保留。新原生8/8与204过滤样本，三入口1073/1077/26的真实缓存索引182/186/26及双向映射和精确比较闭合；GetValues枚举/对象/泛型接口初始化夹具、ParamS_int解码stub明示，其他系统授予路径和旁句保留，不称队伍总量或实机。C专项10/10、边界1140/1140、raw80根+199子引用、GBK12次、DOM165/165、verify189/189、A—P overall_ok、12产物一次重建无漂移。见[交接](output/character_skills/P3B7_HANDOFF.md)、[证据](output/character_skills/description_bindings/p3b7_batch/README.md)。B6最终独立D已[带限制通过、无阻塞整改](output/character_skills/review/p3b6_20261019_batch_bindings/REPORT.md)，以下B6旧待审文字是冻结历史。未实机/真实浏览器验收、未提交推送发布。

更新：2026-10-19（角色技能P3B6，C冻结待独立D）。已有字段到完整句子的受控结构规则，固定普通type26三条及自身F0/Boss type5六条；新增描述9唯一/9页、效果槽9唯一/9页，字段答案+0。当前字段82875/82013/81996、scope10095/72780、未知参数427176、字段缺口5560、断链3均不变；描述41595＝真实91＋提示11601＋未知29903。按原“所有片段真实对应且无断链”标准独立重算2236人，只有cid29由部分→完整，当前部分2235/仅未知0/完整1；该角色24未知字段保留，未称全引擎/账号/最终伤害解释完毕。type5仍CONFIRMED_FORMULA_ONLY，六条小伤害句的2.8/3.5/4/4.5从各自raw读取，小不定义固定倍率；原生固有基础子弹效果允许运行时能力/武器flag另修改，不保证实战全敌命中。旧82013完整答案及重复数、277旧已用规则（源287）、101/31与全部旧type8/type26绑定和旁句对象保留。C自检原生10/10、专项9/9、91边界/91、原JSON9/9、GBK8次、DOM14/14、verify189/189、A—P overall_ok；相关稳定性见[证据](output/character_skills/description_bindings/p3b6_batch/README.md)，[交接](output/character_skills/P3B6_HANDOFF.md)。未改verify标准/预期，历史P10规则范围保留。P3B5原D R2已[通过闭合F1](output/character_skills/review/p3b5_20261019_remaining_five/REPORT_R2.md)，以下旧“待复验”是历史快照。未实机/真实浏览器验收、未提交推送发布。

更新：2026-10-19（角色技能P3B5初审需整改，F1已修待原D复验）。新增6条Boss必杀type24/56/68/73的局部计时/请求系数/发射门槛规则，+97页/+97归一行/+97父holder键，52来源（APK44/CACHE8）、40角色；原五人均仅未知→部分，当前部分2236/仅未知0/完整0。字段82875/82013/81996，scope10095/72780，未知参数427176、字段缺口5560、断链3；描述新增0，真实对应82页保留。旧81916完整答案对象及重复数、旧规则/绑定零破坏。原生8/8、专项12/12、独立原表97/97、GBK六JSON查询和DOM8/8、verify189/189；其余最终验证见[交接](output/character_skills/P3B5_HANDOFF.md)与[证据](output/character_skills/remaining_five/README.md)。F1修订type73候选遍历入口门槛，非正冷却同轮可越次数门槛，正冷却停止本轮继续遍历；27行文案/数量名称及3规则对象变更，全部原值/单位/来源/scope/计数不变。新原生3/3、整改9/9、GBK2/2、DOM9/9，见[整改](output/character_skills/remaining_five/RECTIFICATION.md)，待原D复验，不能据初审其他项通过称整批通过。P10历史5人用真实P3B1开工快照固定规则范围重构，不把预期改0；P7/P8只刷新动态报告。P3B4 N1已由原D[复验闭合](output/character_skills/review/p3b4_20261019_type9/RE_VERIFICATION.md)，以下旧更新为历史记录。未实机/真实浏览器验收，未提交推送发布。

更新：2026-10-19（角色技能P3第4批，D已审带限制通过/阻塞0，N1整改待差异复验）。普通type9 param0的“暴击率(x−1)×100”候选被原生反证，真实是Bullet贯通后伤害保留系数：当前命中先交Attack，随后以已启用type9最大param0逐次乘法/向零整数化/int32夹紧，写回供后续命中；门槛含bCheckAbility、非Skill(1)、MULTIHIT或击杀SHOT_THROUGH继续路径。仅新增1规则，789页/788归一行/788父holder键、441来源（APK345/CACHE96）、450角色，全BY_TYPE；描述对应+0、角色状态与断链不变。当前82778/81916/81899，scope10095/72683，未知字段427273、字段缺口5569。原生13/13、专项13/13、逐位置raw788/788、verify189/189、A—P overall_ok、GBK CLI4次与DOM6/6通过；首次P8动态报告滞后仅刷新报告，P8自身15653页不变，未改检查/派发算法。见[交接](output/character_skills/P3B4_HANDOFF.md)、[证据/命令](output/character_skills/type9_crit/README.md)。旧81128条完整答案对象及重复数、101/31基线与type8/type26绑定保留。P3B3 N1已由原D差异复验闭合。本次仅修N1的系数1精度文案，277归一行/278页；公式/raw/单位/scope/条件与旧对象不变，未重跑原生或A—P。见[正式报告](output/character_skills/review/p3b4_20261019_type9/REPORT.md)、[整改](output/character_skills/type9_crit/RECTIFICATION.md)；机器PENDING保留审查前状态，以正式报告为准。未实机或浏览器视觉验收，未提交/推送/发布。

更新：2026-10-19（角色技能P3第3批，D已审、N1已修待文档差异复验）。type26 param0原生身份/转换/持有者职业/授予及开局门槛已定向取证，新增1条类型规则；字段+489页/+469归一记录行/+469父holder键（416来源记录），全部BY_TYPE，影响481角色；3101/3102固定APK纯句+2唯一/+22页。当前81989页字段答案、未知字段428062；描述41595＝31基线＋29旧type8对应＋22本批已审＋11601提示＋29912未知。角色状态2231部分/5仅未知/0完整、断链3不变。见[交接](output/character_skills/P3B3_HANDOFF.md)、[证据](output/character_skills/type26_mana/README.md)；不借用旧审查结论、不宣称实机或真实浏览器验收。D[正式报告](output/character_skills/review/p3b3_20261019_type26/REPORT.md)结论带明确限制通过、阻塞0；仅非阻塞N1参数名误称已按wrapper寄存器/metadata事实修正，见[整改记录](output/character_skills/type26_mana/RECTIFICATION.md)，待原D仅核文档差异。机器JSON保留审查前PENDING，以正式报告为准；本次未改代码/数值/机器产物，未重跑检查。

更新：2026-10-19（角色技能P3第2批，已独立审查闭合）。D结论「带明确限制通过」，阻塞0、需整改0，见[报告](output/character_skills/review/p3b2_20261019_type8/REPORT.md)。15条指定type8候选纳入11/排除4，新增11唯一片段/12页引用、12唯一效果槽/13页引用、12角色且与首批无重合；字段答案新增0、角色状态迁移0。当前描述41595＝31基线＋17首批已审＋12本批已审＋11601提示＋29934未知；type8累计21唯一片段/29页、25唯一效果槽/33页、29角色。旧答案对象/重复次数、首批十条与基线101答案/31绑定全保留。实施检查见[P3B2交接](output/character_skills/P3B2_HANDOFF.md)，D另行独立核验；未实机/真实浏览器验收。四条条件/对象歧义记录保留提示，不新增条件值中性逻辑。两批结论各限固定记录，不向白名单外自动推广。机器产物PENDING为审查前冻结快照，README已明确当前以D报告为准。本次仅文档收口，未改代码/数值、未重跑检查；停止写入。不提交/推送/发布。

更新：2026-10-19（角色技能 P3 第 1 批，已审查闭合）。D 独立审查「带明确限制通过」，阻塞0、需整改0，见[审查报告](output/character_skills/review/p3b1_20261019_type8/REPORT.md)。基线校准与十条固定APK type8记录的人工语义对应白名单试点，新增描述对应 **10 唯一片段／17 页引用**（13 唯一效果槽／20 页效果引用），涉及 17 角色；字段数值答案新增 **0**。规则答案仍为 81500 页／80659 归一记录答案行；80642 是父记录＋所属表/ID＋规则/字段键去重（重复子引用造成差 17）。描述页引用 41595＝31 基线＋17 审定对应＋11613 仅提示＋29934 未解释。角色仍部分2231／仅未知5／完整0，未知参数槽428551，断链3。不是通用逐句解析器；白名单外、CACHE源和复合条件句保留原状态，不向其他记录自动推广。交接见 [P3B1_HANDOFF.md](output/character_skills/P3B1_HANDOFF.md)。本轮不提交、不推送、不发布。

更新：2026-10-18（角色技能线 P2 第 10 批：`Exec_HEAL` 家族与其余类型；里程碑 A 收官，本轮）。第 9 批把 147 个「仅未知」归因到**缺类型规则**，本批清掉 142 人。**① `Exec_HEAL` 家族＝一个 handler ＋ 两个模式实参**：`bhSkill.Exec_HEAL(0x1299C74)` 的 `w2`＝对象选择、`w3`＝动作选择、`w4`＝类型 → `bhSkillUtil.Exec_HEAL(0x1187C80)`（第一跳转表 0x206DE44，4 项）→ `Exec_HEAL_common(0x1188194)`（第二跳转表 0x206DE48，9 项）；动作→类型：0 回复(10/11/28)、1 支援(12/13/14)、2 支援(26)、3 护盾(15/16)、4 回复+支援(31)、5 回复+支援(32)、6 回复+支援+载荷(46)；对象→类型：0 自身(10/12/15)、1 同 `_type` 且职业位命中 `iParam0` 的存活成员(11/13/16/26/31/32/46)、2 再随机取 1 人(14)、3 再取 HP 比例最低者(28)。**② 回复量**＝`floor/clamp(float32(B × skillparam1))`，`B=getBasicSkillAttack(true)`（0x1182ED8，与第 8 批攻击族同一函数），整数化 `0x14374BC`，交 `CharaBehavior.Heal`（0x1541158）的 healValue；**超上限（HP 上限）比率**＝`max(HealSkill_HealFlag(0x1182B4C) 的位表档位, 附加槽)`，位序 `[40,35,41,42,43,44]`→档位 `[1.2,1.3,1.4,1.6,1.8,2.0]`（复用 `output/boss_heal/constants.json`），附加槽 10/11→sp2、28→sp5、31/32→sp4、46 无；仅动作 ∈{0,4,5,6} 才合入标志位。**③ 支援块实参序取自 `SetSupport_noCheckTime`(0x17765F0) 自身的存储点**——该方法（与 `BtEffect_LineExec_ContSupport..ctor` 一样）的**元数据 `parameters` 顺序与原生实参序不一致**，照元数据读会把防御系数答成标志位、攻速答成移动；12/13/14/26 乘 `_skillChainRate`、28/31/32/46 不乘（用不同 answer_kind 区分并逐条钉死）。**④ FALL_AREA（33/103）**：sp3＝落点 X 偏移（`_type==0` 取负＋夹到地面范围）、sp6（仅 33）＝选择码；**伤害在 `AirAreaStrike`(0x118380C) 建立的工作对象里结算**（对象 +0x40 持有 util），未追进其 update → 伤害槽不给数值。**⑤ 其余类型**：6／7／19／23／29／34／36／43／44／49／50／51／55／64／67／69／72／74／75／76／80／82／86／87／114 共 **80 条规则**（36 个类型，全部由「pin 逐字节重读」把关；34/50/64/72/76/86 的消费点未定位 → 答案写「消费点未定」）。**增量：新增答案 5452 条（页求和）／4050 唯一键**，未解释 434003 → **428551**，**142 个角色由「仅未知」变「部分」**（147 → **5**；脱贫路径：等价门控 123／＋传授链 7／＋自身 pattern 6／仅自身 pattern 2／门控＋pattern 2／传授链＋pattern 2）；规则答案 76048 → **81500**、唯一记录 75207 → **80659**、缺口字段级 5679 → **5571**。仍未脱贫 5 人：cid 4009(24)／4049·8116(56)／10018(68)（F0）与 8151(73)（E0）——这 4 个类型未解出可交付槽位语义，**不是缺等价前提**。**零破坏**：0 键丢失、0 raw／kind／unit／status／scope 变化、0 value 文本变化（独立复算 `work/p10_paths/zerobreak.py`：75191→80642 实例）。`boss_heal_types.py` **219/219**、`verify_p1.py` **189/189**（+15 项 `p10.*`；P8 的增量恒等式改为结构式并注释原因）、`crosscheck_raw.py` **A–P overall_ok**（新增 P 区直读原始表核对新答案）、`charainfo_types.py` 37/37（`handler_slots_agree_with_confirmed_rules` 增加「由逐字节钉死的读取点覆盖」一路并说明扫描是下界）、`boss_attack_types.py` 86/86、`denju_skills.py` 17/17、`cp_paths.py` 18/18、默认 GBK **19 个入口调用 exit 0 且 stderr 0**、两轮全链重跑 **82 份产物字节无漂移**、HTML 夹具 p1 **8/8**＋p2 **25/25**。产物 [output/character_skills/README.md](output/character_skills/README.md) §3.10、[P10_HANDOFF.md](output/character_skills/P10_HANDOFF.md)、[docs/tasks/20261018-character-skills-p10.md](docs/tasks/20261018-character-skills-p10.md)。**p2b10 审查整改（F1–F4，只有文本与一条漏规则）已完成、待复验**：**F1（会漏答案）** 初版把 type46 的 sp5 写成「无消费点」，字节复核确认它与 type28 共用 `0x11882AC` 的超上限附加档位装载（`0x118827C cmp w19,#0x2e` → `0x1188280 b 0x11882A4` → `0x11882A4 fmov s0,wzr` 不改 NZCV → `0x11882A8 b.ne` 不跳转 → `0x11882AC ldr s0,[x22,#0x40]`＝sp5），补 `bossskill|46|/skillparam5`（**147** 条实例：holder 97 条，APK 120＋5／charainfo 21＋1；raw∈{0,15,20,25,30}；本批页答案 5305→**5452**、唯一 3953→**4050**、未解释→**428551**），并加 2 项自检与 crosscheck P 区逐条钉死；**F2** 类型数 39→**36**；**F3** DOM 夹具计数改 p1 **8/8**、p2 **25/25**（原先把 `ALL DOM CHECKS PASSED` 汇总行也计了）；**F4** 去掉答案里与模板重复的注记句并新增常驻检查 `p10.answers_have_no_repeated_clause`（覆盖 80 条规则、重复 0）。整改后：`boss_heal_types.py` **219/219**、`verify_p1.py` **189/189**、`crosscheck_raw.py` **A–P overall_ok**（P 区 `type46_sp5`＝147、mismatch 0）、零破坏逐实例 lost 0／文本 0 变化、默认 GBK 19 入口 exit 0、两轮 82 份产物无漂移。整改记录见 `output/character_skills/P10_HANDOFF.md` §10。未提交、未推送、未发布。

更新：2026-10-18（角色技能线 P2 第 9 批：必杀技执行侧裁决 X1／NOT_AMONG／F0，本轮）。**里程碑 A 收官**：不再问「两份副本是否相等」，而是从执行侧回答「游戏跑哪一份」。**路径 A（自身 pattern 可解析）**：`OnClickSpSkill`／`CheckEntry` → `bhSkill.CreateExecSkillList` → `FindPatternCtrl` 命中 → `_CreateExecSkillList` 的 pattern 分支 → `pattern.getListBattleBossSkill()`（`BattleBossPattern.makeListBattleBossSkill` → `daBattleBossParameter.getBosSkill` = boss 主表）→ `Mission_execSkillPattern`。**路径 B（自身 pattern 无可达技能 ＝ F0，929 角色）**：`CharaParamToBossSkill(0x13aa390)` 读 `BattleParam`（`_atvSkillID` ← `charainfo.skillid[0]`、`_skillparam0..9` ← `CreateByID` 复制的 `charaParameter.skillparamN`）构造 `BattleBossSkill` → `pattern==0` 分支 → `Mission_execSkill` → `CheckEntry` 取列表第 0 项 → `SetExecSkill` → `bhSkillUtil.initialize_ExAttack`（把该 skill 的 `skillparamN`／`skillflag` 复制进 util）→ `Execute` → `ExecSkill(w2=skillid0)`。**关键更正**：`BattleParam` 侧**不是** boss 主表侧（`CreateByID` 从角色记录复制），故 **X1 裁决＝执行取 pattern 侧、charainfo 副本不是执行值**（区分性样本 cid 2315／6058／8139 的正文回数只与 boss 侧一致；P2-1 拒绝迁移的方向正确）；**F0 的记录原值就是执行值**，故新增 `F0_NO_PATTERN_FALLBACK` 门控类（929），`NOT_AMONG` 收窄为「pattern 存在但类型集合不含 `skillid[0]`」的 **20** 人（逐个定性）。**新增答案 1727 条**（页求和＝唯一键，落在 535 角色上），未解释 435730 → **434003**，**187 个角色由「仅未知」变「部分」**（334 → **147**）；剩余 147 人的原因变为**缺类型规则**（F0 134／E0 9／X1 3／NOT_AMONG 1；F0 桶 heal 族 `Exec_HEAL` 53、`Exec_FALL_AREA`＋`FALL_AREA2` 11、type23 14、type6 11、type7 11…）。数据侧印证：F0 正文回数 51/51 与 `trunc(sp6)`（105/110）／`trunc(sp3)+1`（type1）一致，据此修正 type1 `sp3` 文案（追加回数；总次数＝该值+1，数值/kind 不变）。第 0 项完成 p2b8 审查 3 处文字修正（type5/47 推力链路、P2R_HANDOFF 指向注记、type110 sp6 范围措辞）。**零破坏**：0 键丢失、0 raw／kind／unit／status／scope 变化；value 文本按 p2b9 整改项有意变更（901 条既有实例只改 value）。`verify_p1.py` **174/174**、`crosscheck_raw.py` A–O overall_ok（F 区新增 F0 分类重推、G2 新增 F0 前提核对、N 区 1521 条 F0 答案不再要求 boss 同值）、`boss_attack_types.py` **86/86**、`cp_paths.py` **18/18**、默认 GBK **17 个入口调用 exit 0 且 stderr 0**、两轮全链重跑 **76 份产物字节无漂移**。**p2b9 审查整改（需修正，阻塞项 F1）已完成、待复验**：F1 把 type1 `sp3` 的**答案渲染层**改为「追加回数；总攻击次数 = trunc(sp3) + 1」（`rules.py` 新增按 `(type, kind)` 的模板分派；99 条实例，kind／unit／status 未变）、F2 type110 `sp6` 答案去掉「范围外也消耗预算」（820 条）、F3 type47 `sp4` 补 `SpreadBullet` 中转注记（45 条）、F4 16 条 F0 `/skillflag0_1` 补人读「证据路径」注记（1727/1727 全覆盖）、F5 订正交接散文的 147 归因数字（F0 134／E0 9／X1 3／NOT_AMONG 1；heal 族 53、FALL_AREA＋2 11）。复查：`verify_p1.py` **174/174**、`crosscheck_raw.py` **A–O overall_ok**（新增 O 区逐条钉死）；实例级对账（`p9_increment.json.rectification_accounting`）lost 0／new 0、文本变更 964、只补注记 16、raw／kind／unit／status 0 变化。口径注记：`charainfo_params/`（522 → 3131 → **4858**）、`p8_increment.json` 分离「P8 新规则答案 15653」与「落在更早规则上的 206」。

更新：2026-10-18（角色技能线 P2 第 8 批：攻击系 boss 技能类型族，本轮）。**伤害基值定位（里程碑 A 攻坚项）**：`bhSkill.Exec_ATTACK_*` 家族的伤害输入一律是 `floor/clamp(float32(B × skillparamN))`，`B = bhSkillUtil.getBasicSkillAttack(true)`（`0x1182ed8`，入参 `w1=1`），整数化 `0x14374bc`（`frintm`/`fcvtms` 向下取整后夹到 int32；`+inf` → int32 最小值）——与 type105／type112 既有证据同源；**P2-1 的「全局技能表」候选被否**（`[[0x29e9000+0x6e8]]+0xb8` 是被 `skillparam4` 缩放的攻击起点偏移，不是伤害表）。**新增 35 条规则**（type 0/1/2/3/4/5/22/47/105/110 的伤害倍率/推力/间隔/次数/范围/爆炸等槽，与既有字典零重叠），伤害倍率与推力由**分支可达体重算**（只允许从该 type 的 handler 可达的调用点，避免共享体串槽）、其余槽由钉死 RVA 复核；受控执行 85/85。**新增答案 14132 页／10000 唯一键**，未解释 449862 → **435730**，**39 个角色由「仅未知」变「部分」**（373 → 334；21 人经 charainfo 等价门控，其余经自身 pattern 的 boss 技能／传授链）；零破坏（既有答案键 0 丢失、0 变化）。第 0 项完成 p2b7 审查 4 处文档修正（只改文字）。`verify_p1.py` **163/163**、`crosscheck_raw.py` A–N overall_ok（新 N 区 14124 条从原始表重算，0 失配）、默认 GBK 14 入口 exit 0 且 stderr 0、全链 66 份产物 SHA-256 逐字节相同。口径注记：`charainfo_params/`（522 → 3131）与 `denju_skills/p7_increment.json`（3236 → 6177）按当前规则集重算，各批交接记录的是该批闭合口径。

更新：2026-10-18（角色技能线 P2 第 7 批：denju 传授必杀技 ＋ p2b6 审查 5 条注记整改，本轮）。**第 0 项（p2b6 审查文字注记 5 条，只改文字）**：① 交接 §2③ 门控四个地址多写一位「1」→ 改为 `0x111293c..48`／`0x111295c..60`／`0x1112994`／`0x111288c..98`（产物 JSON 原本即正确）；② §6 注释改 `--cid 2205` 看 96 双槽（cid30236 无 96 记录，仅验证基线渲染）；③ 1059 门控特例按原生语义改「iParam0 与 int(param8) 均不为正（≤0；现有记录均非负，等价于 ==0）」（`rules._union_count_threshold` 与 `UNION_COUNT_CONDITION` 同步）；④ 玩家侧 `GetAbilityOnFlagIndex_ParamN` 聚合＝**极值选择**（按调用方实参取 min／max，非叠乘叠加）补注进 `union_count_chains.json` 的 `player_side_paramn_aggregation` 与 1059 规则 `limits`；⑤ `Constants.WeaponKind2AttackFlag` 跳转表**表项是字节**（`ldrb` ＋ `add x10,x10,x11,lsl #2`）补进 `filter_dictionary.json` 的 `native_evidence`。**主体：denju（1504 行／1500 角色）**。**① 结构结论**：denju 行**没有参数槽**（键集＝`denju_id`／`develop_only`／`scost`／`sname`／`stext`／`timestamp`／`patternid0..5`），效果类型与数值在 `denju.patternidN → bosspattern → bossskill` 链上（946 行有 patternid，995 个引用字段：缓存 231／APK 758／**两源都缺 6**）。交叉证据：`denju.sname`＝所指 pattern 的 `sname`（950 个引用字段）且 `denju.stext`＝该 pattern 的 `sinfo`（820 个，含 29 个两者都非空却不同；按 995 个 `patternidN` 引用字段计）。**② 原生链路 17/17 复读**：`BattleParam.CreatePlayer` → `BtlCharaUtil.GetBattleDenju`（门控 `EnableDenjuSkill`：接收方 `isDenjuFrom`＋传授方 `isDenjuTo`＋同 `jobtype`＋`daLimitBreakDenju.GetDenju≠null`）→ `BattleParam.InitlizeDenjuSkill`（`_denju`@0xa20＝`denju_lblist` 的 BattleDenju ／ `_denjuSkill`@0xa10＝`GetDenjuSkill` 经 `CharaParamToBossSkill`（传授者自身角色参数，记录号置 −1）／ `_denjuListPattern`@0xa18＝denju pattern 逐个包 `BossPatternCtrl`）→ 战斗执行 `BtlCharaUtil.GetExecSkillInfo` 用 `_denju` 取名字与费用、以 `_denjuListPattern` 调 `bhExAttack.think_attack` ⇒ **攻防数值来自 denju 链的 pattern→bossskill**；`daDenjuParameter.GetInfo`（即 denju 行本身）的调用方全在 UI／卡面侧，无战斗消费者。**③ 应用**：`denju.patternidN` 与 `charainfo.patternN` 共用同一个 `resolve_pattern` 助手，把 pattern 的 bossskill 挂成 denju 记录的 `boss_skill_refs`（＋`boss_skill.s_ability` 交叉引用），类型／数值按已确认 boss 规则出答案；关联一律 `denju.denju_id == cid`（实测 1500/1504），224 行 `sname` 与角色 `skillname` 不同者**只按 ID 关联**并在 `link_status` 注明。**增量：新增规则答案 3236 页／3236 记录级／210 新增唯一键**（按类型页和 13→2296、2012(SA)→456、105→184、112→147、27→100、66→29、16→24），可达角色 **579**；未解释参数槽 417790→**449862**（＋32072 全在新挂子记录上，既有记录未解释键 0 减少）；断链 0→**3**（6 个 patternid 两源均缺，名册内命中 3 人，逐条列在 `denju_skills/structure.json`，非关联错误）；**1 个角色（cid 12021）由「仅未知」变为「部分」**（部分 1862→1863）。**零破坏**：既有答案键 **0 丢失**、raw／kind／unit／status／scope **0 变化**；457 条文本变化全部来自第 0 项注记 3 且首个数值 0 变化。**区分性样本**：148 行传授版本与被传授者自身必杀技 `skillparam1..6` 不同（如 cid 253 链上 0.3 对角色自身 6.5，页面显示链上值）、102 行类型不在自身链上——不拿角色自身 skillparam 替换。**④ 顺带修正传授突破** `denju_lblist` 五个条目此前共用记录键 `cid` 致 2—5 号内容不可见：改逐条键 `cid#i`（＋44 记录、0 答案丢失），并把各条目 pattern 的技能一并挂出。**验证**：`verify_p1.py` **149/149**（+18）、`crosscheck_raw.py` **A–M overall_ok**（M 区 2600 条 denju 页答案 ＋ 519 条 SA 交叉引用全部从原始表重算）、`denju_skills.py` 原生自检 **17/17**、`skilllist_types.py` **53/53**；默认 GBK（`PYTHONUTF8=0`）**11 个入口 exit 0 且 stderr 0 字节**；重跑全链 **25 份关键产物 SHA-256 逐字节相同**。产物 [output/character_skills/README.md](output/character_skills/README.md) §3.7、[P7_HANDOFF.md](output/character_skills/P7_HANDOFF.md)、[docs/tasks/20261018-character-skills-p7.md](docs/tasks/20261018-character-skills-p7.md)。等针对性审查；未提交、未推送、未发布。

更新：2026-10-18（角色技能线 P2 第 6 批：条件语义三件套，本轮）。**① type 96 攻击路径的 `[sp+0x18]` 标志语义已定位**：`BattleParam.GetAbilityAttack` 的第 4 个实参是 `damageType`（元数据枚举 `eDamageType`），序言 `cmp w23,#1` —— **Skill(=1)** 走扩展缩放路径并把 `[sp+0x18]` 置 1（0x1107618），其余伤害类型置 0（0x110759c `str wzr`）；96 的攻击分支体在 0x1107c48 读该标志择槽：`!=Skill → get_param2`、`==Skill → get_param3`。两个调用方全图扫描确认仅两个：`CharaBehavior.Attack`（把当次伤害类型透传）与 `BattleParam.UpdateParam`（`mov w4, wzr`，即缓存态固定走 param2）。两条槽各按其条件出行（攻击 ×(1+系数×min(玛那计数,param1))），P5 留下的该处缺证**关闭**。**② 筛选位字典建成**（`skilllist_types/filter_dictionary.json`）：职业＝元数据枚举 `JOB_TYPE`（`1<<jobId`，`_jobType`@0xf8，`BattleParam.CalcCharaNum` 0x1113e08..0x1113e1c 位测试）；武器＝游戏自身 `Constants.WeaponKind2AttackFlag` 跳转表（0x2074180 → kind 0..5 与 8/9/10 = bit22..27 与 28..30，6/7=OTHER/ALL 无位；角色侧 `_weaponTypeAttackFlag`@0x1b0）；出身＝游戏主表 `homelist.home_id`（`BattleParam.IsTargetHome` 0x10fdd50：`%100`／`/100%100`／`/10000%100` 三组比较 `home`／`battle_home`，0＝不筛选）。记录侧字段映射：`_flag`@0x90 → `flag0_0`（低 32 位，武器位全在此）、`_flag1`@0x98 → `flag1_0`。字典附**正文区分性对照**（只取正文恰含一个该维度词、位图恰一位的样本：职业 273／273、武器 54／54、出身 73／73 全一致）。**③ type 1059 UnionCount（432 角色）闭环**：门控＝`BattleParam.IsEnableAbility` case 0x423（0x11127c8，`BattleManager.GetAllCharaList` 逐角色，`1<<jobId`／`_weaponTypeAttackFlag`／`IsTargetHome` **任一**命中即计数，`iParam0==0 且 param8==0` 时另要求武器位与全体武器掩码有交集，计数 ≥ `int(param0)` 含等于）；装载＝`setupAbility` 跳转表（x28 基址 0x206dbb2）0x423→0x10f5830 创建 `cAbilityUnionCountWork`（`_timer=get_param7`）入 `_abilityUnionCountWorkList`@0x728；施加＝`update_ability` 0x110bc28..0x110be64（每帧计时器、≤0 重置并对满足 `iParam1`／`flag1`／`param9` 的成员 `CharaBehavior.Heal(int(param6×成员最大HP))`）；数值＝五个 `PlayerManager.GetAbility{Attack,WalkSpeed,Defence,Critical,CriticalDmg}` 按静态 rank 表（`AbilityTypeCachedFlagIndex..cctor`，rank(1059)=121、offset `0xf2`）取本类型 flag index 后用 `GetAbilityOnFlagIndex_ParamN` 读 `param1..param5`（队伍范围、固定倍率不随人数缩放）——这正是 P2-2「三条乘算路径落中性、属队伍范围效果」的解释，两条结论不冲突。**新增规则 21 条**（96×3、67×3、80×1、1059×14）；67／80 的阈值答案升级为逐值可读（只改文本）。**增量：新增规则答案 9112 条（页求和）／9112 条（记录级）／7959 条（（表,记录,层,字段）去重）**，按类型页求和 67→2797／80→298／96→207／1059→5810；未解释参数槽 426902→**417790**；规则答案 47841→**56953**（唯一 47008→**56120**）；缺口字段级 5736→**5715**；可达角色 67→**513**／80→**166**／96→**52**／1059→**432**（去重 919）；**1 个角色由「仅未知」变为「部分」**（部分 1861→1862、仅未知 375→374）；相对 P5 终态快照（`work/p6_records_before.jsonl`）**0 键丢失、0 raw／kind／unit／status／scope 变化**，1414 条只改条件文本且文本首个数值 0 变化。**如实保留未验证**：`AbilityTypeCachedFlagIndex` 的 rank↔type 完整表与 `flagIndex` 值未录入；出身筛选「0 组是否命中缺省 home」未验证；1059 的计数来源在门控（`GetAllCharaList`）与玩家侧施加（成员列表）两处不同，答案统一按前者表述。回归：verify **131/131**（+15）、crosscheck **A–L `overall_ok`**（K 8754／L 4602 条 0 失配）、`skilllist_types.py` 自检 **53/53**（+12）、双路核对 5×3001 type 0 差异保持、默认 GBK（`PYTHONUTF8=0`）六个入口 exit 0 且 stderr 0 字节；重跑全链后 **16 份关键产物 SHA-256 逐字节相同**。**待针对性审查**（样本与错答风险见 `output/character_skills/P6_HANDOFF.md`）。未提交、未推送、未发布。

更新：2026-10-18（角色技能线 P2 第 5 批 · p2b5 审查整改，本轮）。审查结论「带明确限制通过」＋4 项待修正，**4 项已全部整改并交回复验**（每项先自写反汇编复现审查者的事实再落盘）：**A（会给错答案，限域）**——type 96 的计数对象由 `int(param0)` 分流：`==0` 时是**斯库拉普玛那**（`PanelManaGage.GetCurrentScrapManaNum` 0x1242df0 ＝ `mov w1,#0x20; b GetCurrentManaNum`；五条路径的标志站点 attack 0x1107938／defence 0x1108210／move 0x1118d68／crit_rate 0x1119590／crit_dmg 0x11199dc），否则才是 `iParam0` 经 `ConvJobFlagToElementFlag` 的当前玛那；原先统一写「当前玛那」，影响 18 个原始行／23 个记录级节点／**115 条答案／18 个角色**（如行 8291「幸せのぬくもり」、2680／8221 与 8527／8531／8535 等「开局玛那转斯库拉普」类角色，按旧文本会被读成无效）。整改：条件文本写明两条计数对象；`rules._mana_object(record)` **按记录自身 param0** 选答案名词（param0 缺失时用中性名词＋note，不擅自二选一）；`composite_chains.json` 增该 helper 语义与分流说明；新增原生检查 `composite_96_param0_selects_the_counting_object`（5 路径必须同时出现 0x20 标志与 job-flag 转换）；crosscheck K 区**按记录钉死**（90 个（记录,字段）键必须写斯库拉普、146 个必须不写）；verify 增两项检查（115 条实例必须写斯库拉普、条件必须写明两种对象）。**B（文字，潜在错误）**——96 上限槽语义实为 `int(param1)<1` **不设上限**（`cmp w26,w8; ccmp w8,#1,#8,ge; csel w19,w26,w8,lt` 三级情形复核），产物原写「按 0 计」方向相反（本快照 param1∈{1,2,4,8,10} 无记录触发）；已改为「不设上限」并注明无记录触发，verify 增检查拒绝旧措辞。**C（文字，证据描述错误）**——`BattleParam..ctor` 内**无** `+0x328` 存储（`0x10f8740 adrp` 静态基址的类初始化指针读取），原「ctor 在同一偏移写入」不成立；`hyperGauge` 身份改述为「元数据字段表 `_hyperGauge`@0x328 ＋ 具名 getter 0x10f3c10」双路钉死，`composite_chains.json`／P5_HANDOFF／README 同步，verify 增检查。**D（文字）**——交接规则计数更正为**数值 19＋阈值/选择/上限 4**（合计 23 未变）。**只动文本**：96 的 320 条答案 raw／kind／unit／status 与渲染系数**逐条 0 变化**（文本变化仅三类：计数对象改斯库拉普 92 条、补注计数对象 159 条、上限槽语义修正 69 条）；数字口径全部不变（规则答案 47841／唯一 47008／未解释 426902／部分 1861／仅未知 375／缺口 5736；相对 P4 快照 27440 键 0 丢失 0 变化）。回归：verify **116/116**、crosscheck **A–K `overall_ok`**、`skilllist_types.py` 自检 **41/41**、默认 GBK 可运行。整改记录 `output/character_skills/review/p2b5_20261018_thirdparty/RECTIFICATION.md`（审查方 REPORT／evidence 字节未动）。等复验结论；未提交、未推送、未发布。

更新：2026-10-18（角色技能线 P2 第 5 批：复合分支 67／80／96／1036 原生研究，本轮）。**做法升级**：67／80／96 在**同一条路径上被编译合并进同一个 worker**（三个 leaf 从不同标签进入同一段代码），「扫一个 leaf 的固定窗口」看不到它们的链；改用**函数内可达性遍历**（条件分支两支都跟、遇该路径循环尾／共享累加尾停止、`bl` 只记调用点、边界取所属方法真实范围），逐段定位并把 20 条分支体与逐段关键地址写进 `composite_chains.json`；**规则由该遍历重算后才产出**（`composite_rule_rows` 要求「该字段是该分支真正读的槽」且「分支抵达累加器」），规则表写错也不会产出规则。**结论**：① **67 HeroOne**（598 角色）「命中角色数 ≥ int(param0)」时把 paramN 乘进攻击/移动/受伤量因子或加进暴击累加器，计数＝`BattleParam.CalcCharaNum(cType, 职业位图=iParam0, 武器位图=flag, 出身筛选=int(param8), 成员列表)`（只计存活且三项筛选都命中者，比较含等于）；② **80 HoldMana**（166 角色）当前玛那满足 `PanelManaGage.isCurrentManaJob_or/and(职业位图=iParam0, 数量=int(param0))` 时乘 paramN，`param6`==0 选 or、否则 and（iParam0==0 比较玛那总数）；③ **96 ManaCountUp**（52 角色）按 `min(当前玛那数, int(param1))` 计入，系数在 防御 param5／移动 param4／暴击率 param6／暴伤 param7；④ **1036 HyperModeUp** ＝ `paramN × hyperGauge ÷ 1000`（攻/移/伤乘 (1+·)、暴击加算），`hyperGauge` 由 `BattleParam.get_hyperGauge`（0x10f3c10）与 `..ctor`（0x10f8744）两路确认即 `[this+0x328]` 经 `ParamS_int.get_Value()` 的整数（本快照该类型无记录）。**如实缺证**：96 的**攻击路径**系数在 param2／param3 之间由调用级标志 `[sp+0x18]`选择、含义未定位 ⇒ 两槽都不给答案，缺段写进规则行 `limits`；`iParam0`／`flag`／`param8` 是筛选参数（位字典未建立）仍为未解释字段但已作为条件写进 67 的答案文本。**新增规则 23 条**（18 条数值＋5 条阈值/选择码/上限）；`mana_coeff_*`／`hyper_*` 为**公式型**答案（CONFIRMED_FORMULA_ONLY，另乘运行时因子），阈值类仍为数值型（`rules.answer_for` 改为尊重转换器声明的状态）。**增量：新增规则答案 8979 条（页求和）／8979 条（summary 记录级）／6305 条（（表,记录,层,字段）去重）**，按类型页求和 67→6643／80→2016／96→320；未解释参数槽 435881→**426902**；规则答案 38862→**47841**（唯一 38029→47008）；缺口字段级 5754→**5736**；可达角色 67→**598**／80→**166**／96→**52**（去重 742）；**97 个角色由「仅未知」变为「部分」**（部分 1764→1861、仅未知 472→375）；既有 **27440 个答案键 0 丢失 0 变化**。**第 0 项**（p2b4 审查观察）：crosscheck 的直读区从「只核顶层」扩展到**含内嵌子记录的全量**——H 2862→**4147**、I 370→**1067**、J 159→**672**（＝去重口径），并新增 **K 区** 核对 6305 条复合答案的原值与措辞（含「96 的 param2／param3 必须无答案」的反向检查；正文与数据冲突只记观察，数据优先）。回归：verify **111/111**（+12）、crosscheck **A–K `overall_ok`**、`skilllist_types.py` 自检 **40/40**（含 6 项复合分支检查）、双路核对 0 差异保持、默认 GBK 各入口 exit 0；重跑全链 6 份关键产物 SHA-256 **逐字节相同**；真实浏览器核对 cid 3（67）与 cid 203（80）渲染。产物 [output/character_skills/README.md](output/character_skills/README.md) §3.5、[P5_HANDOFF.md](output/character_skills/P5_HANDOFF.md)、[docs/tasks/20261018-character-skills-p5.md](docs/tasks/20261018-character-skills-p5.md)。等针对性审查；未提交、未推送、未发布。

更新：2026-10-17（角色技能线 P2 第 4 批：现成增量＋索引加固，本轮）。**索引加固（先行）**：新增纯静态派发求值器（自维护寄存器与标志位、不执行）与既有 Unicorn 仿真**双路核对**，逐 type 比较落到的分支 `leaf`（5 条路径 × 3001 个 type，**0 差异**），接入 `skilllist_types.py` 常驻检查 `switch_resolution_sim_matches_static`（自检 32/32→**33/33**）——P2 第 3 批「仿真未预置位测试常量导致 type 误判中性」这类静默错误今后会立刻暴露。**现成增量**：确认 type 36／1003／1005／1026 在攻击／移动／受伤量三条 apply 路径上落到的分支与 type 8 **完全是同一条**（`leaf`／`gate_rva`／`slot_calls` 三者相同：攻击 0x1107958→`param1`@0x1107974、受伤量 0x1108124→`param3`@0x1108140、移动速度 0x1118c28→`param2`@0x1118c44），据此复用 type 8 换算产出 12 条 (type,字段) 规则（`attack_mult`／`move_mult`／`take_mult`，换算实现只有一份，由 `field_dictionary.json` 的规则行按 `answer_kind` 通用分发）。**新增规则答案 999 条（页求和）／963 条（summary 记录级）／672 条（（表,记录,层,字段）去重）**；未解释参数槽 −999 （436880→435881）；规则答案 37863→**38862**（唯一 37066→38029）；缺口字段级 5766→**5754**；可达角色 36→**156**、1005→**38**、1026→**17**、1003→**8**（去重 **213** 人），**状态迁移 0**——这 213 人此前都已有别的类型答案，故「仅未知→部分」不增加（部分 1764／仅未知 472 不变，`verify_p1.py` 有专门检查断言成因，非漏算）。方向不互换：`param2` 恒为移动速度乘数、`param3` 恒为受伤量倍率（0.9→「本项减伤 10%，不是固定防御量」），39 条 `param2≠param3` 区分性样本全部保持各自种类；正文「与えるダメージが増加」不驱动 `param3`（`skilllist#113` 的 `param3=1.0` 保持中性）；`skilllist#111`（テレサ）正文的「攻撃力が増加する」子句仍是关键词候选，`param1=1.0` 未被写成 +40% 攻击。本批不做（留缺口队列）：36／1003／1005／1026 的 `param0`／`param6..9`／`flag*`／`iParam*`、type 80／96／67 复合分支、1036 缩放基数。回归：verify **99/99**（本批 +10 项）、crosscheck **A–J** `overall_ok`（新增 J 区直读原始 skilllist 核对 159 条新答案的原值与方向）、`skilllist_types.py` 33/33、默认 GBK 各入口 exit 0；重跑 `skilllist_types.py`→`profiles.py`→`gaps.py` 后 `field_dictionary.json`／`records.jsonl`／`summary.json` 的 SHA-256 **逐字节相同**。产物 [output/character_skills/README.md](output/character_skills/README.md) §3.4、[P4_HANDOFF.md](output/character_skills/P4_HANDOFF.md)、[docs/tasks/20261017-character-skills-p4.md](docs/tasks/20261017-character-skills-p4.md)。等针对性审查；未提交、未推送、未发布。

更新：2026-10-17（角色技能线 P2 第 3 批：暴击率／暴击伤害双路径锚定 ＋ 审查整改，本轮）。两条**加算**暴击累加器（`GetAbilityCritical` 0x1119018／`GetAbilityCriticalDmgRate` 0x1119794）并入派发索引（路径数 3→**5**，受控原生检查 **32/32**）：按 type 读槽——暴击率 `param4`（1／2／36／1003／1005／1026）、`param5`（6／7）、`param6`（3／34）；暴击伤害 `param5`（1／2／36／1003／1005／1026）、`param6`（6／7）、`param7`（3）；夹紧 rate [0,0.5]／dmg [-1,2]。**新增规则答案 1179 条（页求和）／1085 条（summary 记录级）／881 条（（表,记录,层,字段）去重）**，未解释参数槽 −1179，缺口字段级 5783→5766，**173 个角色由「仅未知」变为「部分」**（部分 1591→1764、仅未知 645→472）。既有暴击口径归属已登记：2012／3000／1008／1095 不在两条路径上（support2／Support3 等），type 7 的 `/param5`／`/param6` 与新定位一致（锚定、数值未改）；1036（带缩放）与复合分支 67／80／96 缺证。**本批已经 p2b3 针对性审查（结论「需修正」，2 项）并按 2 项整改完成**：① 两条暴击路径的低号 type 分支被误登中性（根因：派发仿真未预置函数序言放在 X26／X29 的位测试常量；且 `UC_ARM64_REG_X29` 非递增常量，按 X0+n 写会写错寄存器）→ 修正后新增 11 个条目、三条乘算路径 0 变化，并据此新增 9 条规则；② `crit_increment.json` 去重键塌陷（97→881，审查报的真值 355 已复现）。对账：相对 P2B2 快照 0 条答案缺失／0 条 kind/value 变化，修正前 8 条规则仍 355 行／494 页。回归：verify **89/89**、crosscheck A–I `overall_ok`（I 项 370 条暴击答案）、DOM P2 20/20＋P1 8/8、默认 GBK 九入口 exit 0。整改记录 `output/character_skills/review/p2b3_20261017_thirdparty/RECTIFICATION.md`；产物 [output/character_skills/README.md](output/character_skills/README.md) §3.3、[P3_HANDOFF.md](output/character_skills/P3_HANDOFF.md)、[docs/tasks/20261017-character-skills-p3.md](docs/tasks/20261017-character-skills-p3.md)。等复验结论，通过前不开下一批；未提交、未推送。

更新：2026-10-17（角色技能线 P2 第 2 批＋审查整改，本轮）。把 skilllist 能力类型 8＝Always／26＝ManaGet 接入（三条 apply 路径派发索引）；type 67＝HeroOne／1059＝UnionCount 缺证不给数值（参考候选的暴击标签未获原生支持，不采纳）。**新增规则答案 6209 条（页求和）／2869 条（全局唯一记录）／5730 条（summary 记录级口径）**，未解释参数槽 −6209，缺口字段级 5790→5783，**268 个角色由「仅未知」变为「部分」**（部分 1323→1591、仅未知 913→645）。本批经针对性第三方审查（`review/p2b2_20261017_thirdparty/`，结论「带明确限制通过」，会给错答案 0 项）并按 **5 项**建议整改完成：① 索引中性桶误判修正（5 个位于循环尾之后的分支不再被当中性，新增「有分支无槽位」单列类＋四项原生检查）；② type26「不产出」加路径限定与范围注记（164 条风险记录）；③ type8 param4/param0 口径改为缓存＋APK 两源；④ increment.json 补 2869↔5730 口径对应；⑤ 页面 `<title>` 改当前口径（改脚本重建，未手改 HTML）。对账：type8/26 答案逐行零变化（哈希 204780159d8fa873，仅 1293 行文本按②变化）。回归：verify **74/74**、crosscheck A–H `overall_ok`、DOM P2 19/19＋P1 8/8、真实浏览器核对通过、默认 GBK 九入口 exit 0。整改记录 `output/character_skills/review/p2b2_20261017_thirdparty/RECTIFICATION.md`；产物 [output/character_skills/README.md](output/character_skills/README.md) §3.2、[P2B2_HANDOFF.md](output/character_skills/P2B2_HANDOFF.md)、[docs/tasks/20261017-character-skills-p2b2.md](docs/tasks/20261017-character-skills-p2b2.md)。等复验结论，通过前不开第 3 批；未提交、未推送。

更新：2026-10-17（角色技能线 P2 第 1 批，本轮）。把 `charainfo` 必杀技参数（`skillparam0..9`）接入：类型派发原生索引（type 0..121＋default，37/37 受控原生检查）＋记录级等价规则（E0 1110/1286 ＝R2 钉死口径、可迁移 1177、例外 110 逐类留证、无 pattern 的 929 保持未解释）→ **新增规则答案 522 条**、charainfo 未解释字段 −522、缺口字段级 5797→5790、角色状态不变（部分 1323／仅未知 913／完整 0）；verify 56/56、crosscheck A–G `overall_ok`、DOM 12/12、真实浏览器核对通过、默认 GBK 八入口 exit 0。产物 [output/character_skills/README.md](output/character_skills/README.md) §3.1；针对性审查交接 [P2R_HANDOFF.md](output/character_skills/P2R_HANDOFF.md)；实施记录 [docs/tasks/20261017-character-skills-p2.md](docs/tasks/20261017-character-skills-p2.md)。未提交、未推送。

更新：2026-10-17（Release 暂缓）。发布说明草稿与 A/B/C 包已就绪（`output/share_bundle/20261016-delivery/`，含 RELEASE_NOTES_draft.md），**用户决定待项目告一段落后决定是否发布**；当前不创建 Release、不上传。`origin/main = 6240a04`。接手入口：[HANDOFF.md](HANDOFF.md)。

更新：2026-10-17（已推送 GitHub）。复审通过后经用户授权，`origin/main` 已快进到 `e8c5ae4`（9 个提交含完整解包工具、修复、README、docs、打包脚本）；A/B/C 交付包在本地 `output/share_bundle/20261016-delivery/`，Release 上传待授权。接手入口：[HANDOFF.md](HANDOFF.md)。

更新：2026-10-17（复审 R1 闭合）。接手入口：[HANDOFF.md](HANDOFF.md)；整改记录③：[docs/tasks/20261016-reproducibility-audit.md](docs/tasks/20261016-reproducibility-audit.md)。

## 当前交付：复审 R1/I3/I4/I1 闭合（2026-10-17）

- **R1**：`decode_cache_snapshot.py --apk`（默认不变）＋变体路径 `decode_cache_variants` 同步传 apk（偏移 0 必需）；README 同步。隔离三用例全过：改名 APK＋--apk 6/6 原生解码（raw／字节定位与 v3 0 差异）、默认命名结果一致、破坏文件 FAILED_RETAINED。
- **I4**：`.gitignore` 增 `/其他人的参考/`（用户确认他人分析成果，不提交；内容未动）。**I3**：HANDOFF reference.png 文案对齐。**I1**：B 包（698 项）已含两份最新审查报告。
- **基准**：审查基准＝当前最新提交；origin/main..HEAD 有待推送提交（计数随交接文档提交递增，以 `git log origin/main..HEAD` 为准），未推送；对外发布待授权。

更新：2026-10-17（最终确认与审查基准）。接手入口：[HANDOFF.md](HANDOFF.md)；交付包：[output/share_bundle/20261016-delivery/README.md](output/share_bundle/20261016-delivery/README.md)。

## 当前交付：最终确认与审查基准（2026-10-17）

- **仓库确认**：124 个跟踪文件（107 脚本＋README/docs/规范/依赖锁/参考 ZIP）；全部解包管线与修复入库；第三方导入（unicorn/capstone/pyelftools/UnityPy/pillow/lz4/pyaxmlparser/asn1crypto）全部被 requirements-lock.txt 覆盖；无游戏资源、大产物、凭据入库（模式扫描为空）；winreg 仅见于 emulator_probe.py（研究探针，非解包链）；工作树干净。
- **版本绑定**：被测目录 `work/delivery_20261016/final/`（git archive ff664a7）与最终 HEAD 的全部脚本、README.md、requirements-lock.txt、.gitignore 经 `git diff` 确认完全相同（差异仅 HANDOFF/STATUS/审计文档与打包脚本新增），交付测试结论适用于最终版本。
- **错误输入处理（本轮补测，全在隔离目录）**：破坏 data5（位翻转）→ 该文件 FAILED_RETAINED（"Native envelope digest-size constant or payload boundary invalid"），其余文件正常，报告 PARTIAL_FAILURES_RETAINED；空输入目录 → ValueError("No data5 input")；libcompatible.so 改动 1 字节 → 版本断言拒绝（"Pinned build only"，已恢复原件 79b6ae19…）；缺恢复镜像 → FileNotFoundError 并给出缺失路径。
- **A/B/C 包核验**：A 1.4MB/129 项（git archive 最终 HEAD）；B 149.7MB/3366 项；C media_manifest.json（56 类统计＋重建命令＋分包方案＋版权边界，不复制 20GB）；zip 条目对账＋CRC 自检全过；B 包内 base_master 全量组件 JSON 与四个分表 JSON 存在同数据两种访问形式（项目既有产物结构，压缩后增量小，已在清单注明，不重构）。
- **媒体数量口径**（按审查 P2-7 注明）：903,402 文件／20.24GiB＝`output/full_unpack` 目录总量；903,396＝其中 `objects/` 下导出文件数；56 类 exported_bytes 合计 20.18GiB 仅导出媒体本体。三者均为真实数值，用途不同。
- **审查基准**：以当前最新提交为冻结版本（哈希见本轮交付报告与 git log）；若审查期间修改交付版本，须重记提交哈希与受影响文件。
- **待推送差异**：origin/main..HEAD 共 5 个提交（8b91293、ff664a7、e2cc987、ac76029、a8e1f02；原文误写 4，按审查 P2-6 修正），未推送；外部发布动作（push、Release 上传）待用户授权。
- **未验证（如实保留）**：全新机器从零安装 .venv、非 Windows 平台、bdl 全量 68655 在独立目录重跑（项目内既有 100% 验证，不重复）；verify_cache_snapshot/refresh 本快照专用；analyze/export_master 研究线。

更新：2026-10-16（第三阶段交付准备）。接手入口：[HANDOFF.md](HANDOFF.md)；交付包：[output/share_bundle/20261016-delivery/README.md](output/share_bundle/20261016-delivery/README.md)。

## 当前交付：源码仓库补齐＋交付版本验证＋分层成果包（2026-10-16）

- **Git 提交（未推送）**：`8b91293` 26 文件（根 README.md、docs/ 全部、full_unpack 五脚本、build_char_roster、scripts/release 两脚本、9 个修复脚本、AGENTS/HANDOFF/STATUS）；`ff664a7` full_unpack merge/finalize 容忍第三方最小清单（archive 等来源字段可选、finalize 加 --inventory）；`e2cc987` 分层交付打包脚本。提交前确认并行打包任务无新改动，未覆盖他人文件；工作树干净，无 output/work/raw 入库。
- **交付版本验证（任务二）**：`work/delivery_20261016/final/`＝`git archive ff664a7`＋APK＋4 样本 data5，全链实测：A1 apk_baseline 44 文件→A2 重定位 2855→A3 镜像 SHA256＝3fd354b5…钉住值；B1 decode_data5 2 文件、B2 四文件（charainfo/skilllist 偏移 6、bossinfo/helper 偏移 0 变体）16719 记录全部原生解码；**全部与既有参考逐字节一致**。bdl：2 样本 run→merge→verify→finalize，objects_index.json 与项目 full_unpack 逐字节一致。**chronicle**：A4 native_debug＋D1 decode_chronicle，ChronicleArchiveData.json/.bin 及四表与 output/base_master 逐字节一致（7800 角色/21008 技能唯一 ID）。
- **真实验证状态**：data5【已验证·独立目录·两包装格式】；BDL【已验证·独立目录小样本；全量 68655 为项目内既有验证】；chronicle【已验证·独立目录】。未验证：全新机器从零安装、非 Windows 平台。
- **分层交付包（任务三）**：`output/share_bundle/20261016-delivery/`——A 工具包 1.4MB/129 项（与最终 HEAD `a8e1f02` 逐文件内容一致，CRLF 行尾；原文误记为 e2cc987 的 git archive，按审查 P2-6 修正）；B 研究成果包 149.7MB/3366 项（v3 全部、base_master、card_comparison、ordinary_effects、boss_chain/boss_heal、sample、phase_d、validation、双审查报告、card_images、char_roster、structured、两个 latest 指针）；C `media_manifest.json`（20.24GiB/903402 文件逐类统计＋重建命令＋分包方案，**不复制媒体**）；统一 README＋package_manifest.json（git HEAD、SHA-256、排除项、用法、版权边界）；zip 条目对账＋CRC 自检全过。有意排除：export 旧构建（被 v3+base_master 覆盖）、field_guide 旧快照字典、可重建中间产物、历史版本。
- **README**：根 README.md 完成（版本硬边界、环境、安装、data5/bdl/chronicle 命令、采集、结果查看、已知限制、仓库结构）。
- **待授权**：git push origin main；GitHub Release 上传 A/B 包（及如需 C 媒体分包，先确认音频与版权范围）；均属外部发布动作，未执行。
- **不影响交付的限制**：verify_cache_snapshot/refresh 为本快照专用；analyze/export_master 研究线依赖历史证据；bdl 全量独立重跑未做（无必要重复）；pwsh 已切 7.6.6。

更新：2026-10-16（审查整改）。接手入口：[HANDOFF.md](HANDOFF.md)；审计与整改全文：[docs/tasks/20261016-reproducibility-audit.md](docs/tasks/20261016-reproducibility-audit.md)；独立审查报告：[output/20261016-reproducibility-audit/review/review_20261016_independent/README.md](output/20261016-reproducibility-audit/review/review_20261016_independent/README.md)。

## 当前交付：可复现性审查整改（2026-10-16）

- **整改依据**：独立审查结论「带明确限制通过、无 P0」；2 项 P1（修复未提交、F3 隔离证据只覆盖 1/3 脚本）与 4 项 P2（--prior-report 不彻底、77 重放口径、同类缺 mkdir、--cert-hex 未实测）。
- **P2-1**：`decode_cache_snapshot.py` 复用分支改从 `json_file`／--prior-report 所在目录解析（原第 87 行硬编码 `output/decoded`）；默认路径行为不变。三模式复验 PASS：项目侧 77 文件重放 39047 记录归一化后 0 差异、隔离旧报告缺失、隔离自定义报告目录（隐藏 output/decoded 仍正确解析）。
- **P2-2**：77 重放口径写入审计文档（全部 REUSE_THIS_SNAPSHOT_VERIFIED_DECODE，比较对象 records.jsonl，归一化仅 snapshot_id，非 77 次原生解码）；原生解码抽样补 bossinfo（偏移 6）＋helper（偏移 0 变体），与 v3 逐字节一致。
- **P1-2**：jni_prefix_probe／metadata_decode_probe 修复版隔离各跑一次，产物（compatible_jni_prefix/conversion.bin、metadata_aei_decoded.bin）与项目既有文件 SHA256 逐字节一致；F3 三脚本至此全部有隔离实测。
- **P2-3**：protection_sample.py、callback_sample.py、callback_key_candidates.py 入口补 output/protection mkdir；隔离冒烟 PASS（PASS_PROTECTION_SAMPLE／PASS_OFFLINE_BLOCK_MODEL／distinct_keys=1, occurrences=43）。
- **P2-4**：`full_unpack_run.py --cert-hex` 端到端实测通过——2 个 bdl 迷你清单、运行期隐藏 APK，2/2 ok；objects_index.json 与项目 full_unpack 同名包逐字节一致，decoded_sha256 与 ledger 一致。
- **P1-1**：待提交清单已列（full_unpack_*.py、build_char_roster、scripts/release/ 两脚本、docs/、AGENTS.md、9 个修复脚本），**等用户授权后显式提交，一律不推送**。
- **本轮修改**：scripts/decode_cache_snapshot.py、protection_sample.py、callback_sample.py、callback_key_candidates.py 及审计文档、HANDOFF/STATUS；复验全写独立临时目录，未覆盖正式输出；未提交 git、未推送。
- **下一步**：用户授权后按清单提交（git 补缺）；根 README.md；chronicle（A4+D1）隔离补测；发布清单草案。

更新：2026-10-16（可复现性审计与规范）。接手入口：[HANDOFF.md](HANDOFF.md)；审计全文：[docs/tasks/20261016-reproducibility-audit.md](docs/tasks/20261016-reproducibility-audit.md)。

## 当前交付：可复现性审计与 GitHub 交付规范（2026-10-16）

- **可复现性结论**：data5 解包链第三方可独立复现——git HEAD 原始状态在 APK 原生库提取（apk_baseline 未提取 libcompatible.so）、旧解码报告硬依赖（decode_cache_snapshot 必读 output/decoded/report.json）、`work/protection` 建目录（signal_region_probe 等三脚本）三处必败；本轮均最小修复并在仅含仓库文件＋APK＋2 样本 data5 的隔离目录实测通过。恢复镜像 SHA256＝钉住值＝既有文件；charainfo/skilllist 解码字节一致；77 文件重放与 v3 规范化后 0 差异；bdl 管线脚本已参数化但未入 git（下一阶段最高优先）；export_master／analyze／verify_cache_snapshot 属研究线或本快照专用，第三方不适用已标注。
- **版本边界**：仅支持 com.sega.chainchronicle 5.6.2/56021；库、镜像、密钥派生均以哈希钉住，不匹配明确报错。
- **规范调整**：AGENTS.md §7 新增 GitHub 存储策略（≤1GB、遵守单文件限制、继续忽略 raw/work/output/.venv/tools、严禁全目录强制提交、Git LFS 非默认）；§8 重构为 8.1 独立可复现性、8.2 分层发布 A—C、8.3 工具可移植性、8.4 发布清单与发布前隔离验证。
- **实际修改**：scripts/apk_baseline.py、decode_cache_snapshot.py、signal_region_probe.py、jni_prefix_probe.py、metadata_decode_probe.py 五处最小修复；output/apk/baseline.json 重建（verify_phase_a PASS，44 文件）；AGENTS.md；新增 docs/tasks/20261016-reproducibility-audit.md。
- **实测**：隔离环境 11 项（3 项失败复现＋8 项通过）；项目侧 verify_phase_a PASS、v3 重放 PASS（0 差异，测试目录已删）。未验证：il2cpp 镜像、native_debug、chronicle、采集链、bdl 全量隔离、全新机器安装、非 Windows 平台。
- **文件盘点**：output 23.54GB/97.7 万文件（full_unpack 20.24GB 可重建媒体、export 1.40GB、field_guide 0.75GB 等，分类与存放建议见审计文档 §7）；work 4.30GB；raw 3.80GB；.git 仅 1MB。
- **边界**：未提交 git、未推送、未打包上传、未删除或覆盖既有成果；会话期间并行任务已为 NativeDecoder 补 cert_hex/protection 并新建 scripts/release/ 打包脚本（其范围，未接管）。下一阶段：git 补缺→根 README→cert_hex 实测→chronicle/bdl 隔离补测→发布清单草案。

更新：2026-10-16（完整解包）。本轮完成已取得本地资源完整解包：68655个bdl全部解码展开、834741个对象导出；前轮ability1008及前六类型有效，不重跑A—E/核心全量校验/手机，原始资源、v3/E和独立报告不改。

## 当前交付：本地资源完整解包（full_unpack）

- 入口：[阅读说明](output/full_unpack/README.md)、[输入账本68993行](output/full_unpack/ledger.jsonl)、[覆盖统计](output/full_unpack/coverage.json)、[4项验证PASS](output/full_unpack/validation.json)、[manifest](output/full_unpack/manifest.json)、[cid附加索引6233](output/full_unpack/cid_index.json)。
- 范围：composite_inventory全部68993文件。68655 bdl经DecodeXorData（每文件前256字节）转UnityFS后UnityPy展开，100%成功、0部分、0失败；77个data5沿用v3已验证解码（补采密文一致）；261个其他文件分类为il2cpp引擎文件4（复用）、UnityShaderCache 206、广告SDK 34、macOS垃圾17，理由逐条在账本。
- 产物20.24 GiB/903396导出文件：73490 PNG（原尺寸mip0含透明）、17389 WAV（Vorbis→PCM）、50051 OBJ、2845 TXT（BGMTable/Motion/Tips等UTF-8）、759621 JSON（622311个45类typetree+68655包清单+68655包索引）。每包objects_index.json记录对象类型/path_id/导出文件/纹理格式（ETC2_RGBA8 34335、ETC_RGB4 33784等）/音频参数；命名冲突（含大小写）加path_id后缀，全量逐包索引↔磁盘核对0失配。
- 字节/特殊值约定：typetree字节转__bytes_hex__（>256KB截断记SHA）、非有限浮点转__non_finite_float__；无静默补零。本轮0例typetree失败退存.bin。
- 已闭合问题：15包大小写命名覆盖+75个旧命名遗留文件清理；纹理格式名UNKNOWN元数据修正（全量重跑14.2分钟）。
- 实际命令：`full_unpack_run.py --workers 14`（分片续跑，中断自动跳过已完成）→ `full_unpack_merge.py` → `full_unpack_verify.py` → `full_unpack_finalize.py`；现有.venv（UnityPy 1.25.4/Pillow 12.3.0/unicorn），无新依赖，未连手机。
- 剩余：字段语义解释（另一任务线）、APK内置媒体批量导出（索引已有，可复用本管线）、cid_index仅命名规律非绑定证明、257个非游戏文件未展开（有理由）、全游戏索引不可信不声明100%。详见README剩余问题列表。

## 前轮交付：TargetStageAll地形条件全体攻防可查

- [原对照页](output/card_comparison_cid30236/index.html)含七个独立检索区，1095/1017/2012/3000/99/7/1008分别407/321/406/382/133/64/37条。1008相关逐效果行补param0和对象条件/依据；原101项、截图、33概览状态保留。
- [77条规则](output/card_comparison_cid30236/field_dictionary.json)：1008两旧攻防规则扩大、新增param0。来源/原值/类型/字节及JSON定位、中文解释、换算、单位/条件、三类确认状态另列；总2684来源记录/6613存在字段，普通子集1723/4947、60规则。未改v3历史字典。
- 玩家侧当前param是接受者，提供者候选来自_aChara_Player，非空且存活活动；实际类型/资格筛选执行。1008段无自身排除、接受者职业或距离筛选，可含自身/其他队友。非活动提供者转独立后备路径，未证明1008后备安装/转写，40526403后备原文保留；敌用同表记录不推定玩家侧实际装入。
- param0复用7相同IsTargetStage/当前背景flag证据，9种源编码；新3/607分别对99背景核实，607=7或6。param1乘接受者本项攻击，param3乘本项受伤量，均不在该段乘Chain。43023606沙漠下本项攻击/减伤各12.5%；102070攻击5%、防御原值1为中性。完整叠加/HP及其余字段不扩张。
- [1008限定依据](output/ordinary_effects/ability1008/README.md)、[trace](output/ordinary_effects/ability1008/trace.json)、[389项本轮原生检查](output/ordinary_effects/ability1008/native_checks.json)。只新增ordinary_1008_probe.py及相应证据，更新原字段模块/生成器/逐效果/查询/验证器；CSV/JSON/HTML和manifest同流程生成，未手改展示。
- 实际执行新1008探针389项、主生成器及验证器71项，全部通过；四个命令行样本含普通/Boss同号隔离通过。源字节/换算/背景匹配/CSVJSON/链接及前六类型、101项/五组政策回归通过；七段实际生成搜索脚本的V8 DOM夹具14项通过。浏览器file限制保留，未做视觉验收；旧原生证据只读，未重跑7的1390项。
- [查询脚本](scripts/query_effect_dictionary.py)示例：`.venv\Scripts\python.exe -B scripts/query_effect_dictionary.py --id 43023606`；102070看中性防御，42011507看607。target_conditions列param0，trigger_context列范围和来源边界。前轮[7规则](output/ordinary_effects/ability7/README.md)及102071森林/沙漠源内矛盾、2/250原值有效；[五组政策](output/card_comparison_cid30236/difference_sources/adoption_policy.json)不变，[旧审验](output/card_comparison_cid30236/completion_audit.json)仅绑定冻结旧载荷。

下一最小动作：定向追40526403后备生效原文与1008活动提供者路径的关系，先查该卡后备安装/转写及独立Backup记录；不重新调查已核地形和攻防。15%剩余额度暂停线保留，最近可见剩16%。

## 前轮字段对照进展：type105（2026-10-16，后续以当前节为准）

- [チーカ cid30236 HTML](output/card_comparison_cid30236/index.html) 沿用原33项结构，新增一项局部规则对应：现在10项文本/局部规则已对应、14项原值待解释、5项差异、2项未对应、2项网站添加排除；不是完成率。[详细证据与重建命令](output/boss_chain/type105/README.md)。
- 普通pattern43023601→Boss43023600、沙漠43023600→43023605、超共鸣43023602→43023609；param1=3.5/3.75/4.25是**单次攻击技能基值系数**。整数伤害输入=floor/clamp(float32(getBasicSkillAttack(true)×param1))，Chain已在基值内参与，不重复乘。基值使用BattleParam._skillAtk及状态/技能等因子，不能直接当面板ATK倍率或最终扣血。
- param6=5为每目标尝试上限，有限正数向零截断；范围判定前计数。目标持续在范围内可产生5次Attack调用，范围外会消耗预算。对应页同时分列原值已找到、对应关系已确认、局部计算已确认/最终伤害未知。
- 同一生成器新增[2条type105字段规则](output/card_comparison_cid30236/field_dictionary.json)、[142记录/284存在字段CSV](output/card_comparison_cid30236/verified_parameter_views.csv)及JSON，保留原字段、值/类型、Boss命名空间、来源SHA、记录ID、字节和JSON定位、单位/条件/证据。未修改v3历史字典或其他类型解释。
- 实际执行现有.venv的 `scripts/boss_type105_trace.py`、`boss_type105_probe.py`、`build_chica_comparison.py`、`verify_chica_comparison.py`。11项受控片段检查及11项局部数据/结构检查通过；[验证结果](output/card_comparison_cid30236/validation.json)。54条证据一致、三档关联/6样本字段源字节一致、同类型284字段及三组CSV/JSON、HTML33项/链接/manifest核对通过。未重跑A—E、未连接手机、无新依赖。
- 受控夹具建模引擎/ParamS访问及能力提供值，Attack入口拦截；不证明实际HP变化、当前装载或玩家解锁。初版静态脚本的施法者类型名定位失败已按类型索引修正重跑，详情留在局部说明。浏览器安全策略拒绝file协议，视觉验收未完成；结构检查通过。
- 剩余具体缺口：type112单次陷阱伤害基值、九个位置及触发次数；下一步只从Boss43023602 param1=.75追到处理器/伤害输入，再核同卡档位。type105局部规则已从待办移除，完整战斗伤害和pattern选择仍未知。

最终验收依据：[阶段E独立交付复审报告](output/审查报告/阶段E独立交付复审报告_2026-10-15.md)。复审独立重跑五种指针、12项检查和4项受控原生结构场景均通过；新旧10个数据与样本载荷一致。未确认范围继续保留，不宣称全游戏覆盖、当前玩家生效配置、全部字段解释或最终战斗倍率。初审修正工作已结束，不重复执行。

## 已成立基线

- APK：com.sega.chainchronicle 5.6.2/56021，Unity2021.3.58f1。必要程序/配置已提取，未批量导出媒体。
- 原APK、14个采集件不改写。11个data5已解码并通过C阶段完整性/结构验证；chronicle.dat内置主表已解出。元数据和必要原生代码已恢复，不要求完整Android初始化或全部源码。
- D：cid2327「すこやかなるメイド エレミア」→40232705→40232706的原记录、安装/展开/资格/HighHPAll条件链已建立。25%/50%门槛看接受者，局部运算有代码与受控模型依据，不等于当前实机生效或最终倍率。
- D：daSkill逐ID先查JSON层，缺ID才回退APK，不逐字段合并。36000358分别保留APK300.0/缓存400；当前加载版本未知。外部数据库截图仅EXTERNAL_REFERENCE。

依据：[阶段D独立审查（只读）](output/审查报告/阶段D独立审查报告_2026-10-15.md)、[标准样本](output/sample/sample_trace.md)、[完整样本JSON](output/sample/sample.json)。

## 全量采集与新缓存交付（2026-10-15）

当前入口：[阅读说明](output/cache_full_20261015_v3/README.md)、[选定指针](output/cache_full_latest.json)、[来源/版本清单](output/cache_full_20261015_v3/manifest.json)。手机端工作已完成，可拔下手机。

- 原件`raw/phone_20261015_full_02/external_cache.tar`3948107776字节；工作副本`work/phone_20261015_full_02/`。68828个文件、内容3895475185字节，全部路径/大小与本次清单一致，无缺项或差异；OBB为空。首次中文路径ADB pull失败保留在full_01，随后只读tar流成功，无手机文件改动。
- 77个data5、68490个bdl、261个其他文件全部取得。77个data5全部通过原生解密、外层SHA1、gzip CRC/长度及严格JSON核对；bdl和其他混合文件的目标语义仍未穷尽。全量名称/大小校验不冒充原子采集或全量双端哈希。
- 新缓存角色1488、普通技能8634；Boss pattern2149、Boss技能3745。完整77份JSON在[decoded](output/cache_full_20261015_v3/decoded)，[records.jsonl](output/cache_full_20261015_v3/records.jsonl)共39047个记录/文档视图，[tables.csv](output/cache_full_20261015_v3/tables.csv)列134个数组/文档视图数量。原嵌套、缺失、空值、重复和包装字段保留；非数组包装字段仍在完整JSON，不把视图总数当角色实体数。
- 更新[字段字典CSV](output/cache_full_20261015_v3/analysis/field_dictionary.csv)/[JSON](output/cache_full_20261015_v3/analysis/field_dictionary.json)：4671项，仅本缓存，已确认1007/推断47/未知3617。与旧双来源11261项范围不同，不计算解释率；CSV长示例有显式预览标志与完整JSON定位。
- 新[覆盖审计CSV](output/cache_full_20261015_v3/analysis/coverage_audit.csv)/[JSON](output/cache_full_20261015_v3/analysis/coverage_audit.json)：资源取得缺口已补齐至本次可访问目录；结构、关联、语义范围继续分开。所有原始文件可离线再分析，尚无全游戏可信索引。
- cid2327已找到3个pattern及其6条Boss技能：[原记录与候选链](output/cache_full_20261015_v3/analysis/cid2327_patterns.json)、[原文/参数48行CSV](output/cache_full_20261015_v3/analysis/cid2327_pattern_fields.csv)。type116/27/13及原参数存在；Boss读取/安装、后续段执行条件、type27/13单位未知。Boss40232705与普通能力40232705严格分域。已有HighHPAll规则仍仅34条、143个存在字段，不推定实际开放或最终倍率。
- 旧9个缺候选技能ID均在本批找到。当前已列范围23491条引用：普通技能按既有逐ID条件回退，Boss只分别列缓存/APK候选，不套用优先级。仍有60次Extra技能候选引用（12个ID）和6次传授pattern缺候选，[未关联CSV](output/cache_full_20261015_v3/analysis/unresolved_references.csv)逐位置保留；不等于66个资源缺件。36000358仍为缓存400/APK300，未合并当前生效值。
- 适配两个已观察包装：helper/search的gzip从载荷偏移0开始，原主表偏移6。questdigest提高受控实例指令上限至120000000/60秒后成功，算法未变。只新增适配器，未改原E解码脚本。初次74成功/3失败记录及修正前中间输出保留供追溯。
- [13项检查PASS](output/cache_full_20261015_v3/analysis/checks.json)：文件对账、77文件哈希与校验、39047条字节/pointer、409个四槽/1079个八槽完整保留、偏移0/6重复解码、破坏/截断/错误文件名拒绝、样本和旧缺ID、冲突、CSV追溯及引用数量。未重跑无关A—D/E实验；不是实机或独立审查。

实际命令（先采集到新原件，再在工作副本分析）：

```powershell
& .\.venv\Scripts\python.exe -B scripts/collect_cache_archive.py --probe output/phone_full_20261015 --snapshot raw/phone_20261015_full_02
& .\.venv\Scripts\python.exe -B scripts/extract_cache_archive.py --snapshot raw/phone_20261015_full_02 --work work/phone_20261015_full_02 --output output/phone_full_20261015/extraction
& .\.venv\Scripts\python.exe -B scripts/decode_cache_snapshot.py --work work/phone_20261015_full_02 --output output/cache_full_20261015_v3 --reuse-dir output/cache_full_20261015_v2
& .\.venv\Scripts\python.exe -B scripts/analyze_cache_snapshot.py --input output/cache_full_20261015_v3
& .\.venv\Scripts\python.exe -B scripts/verify_cache_snapshot.py --input output/cache_full_20261015_v3
```

采集/提取/导出命令要求新目录；不要把以上已执行路径再用于覆盖历史。离线重跑范例、现有依赖和写入范围见新README；不需要连接手机或安装新包。下一步优先核对Boss pattern读取链及type27/13处理器，再解释必杀后续段；剩余候选缺引用先查命名空间和加载规则。当前没有追加手机操作的具体阻塞。

## 治疗上限与时间单位补充（2026-10-15）

- [最新阅读说明](output/boss_heal/README.md)、[合并字段字典CSV](output/boss_heal/field_dictionary.csv)、[54行样本对照CSV](output/boss_heal/cid2327_description_fields.csv)、[批量字段视图](output/boss_heal/verified_parameter_views.csv)（均有JSON）。8条局部规则覆盖772记录3084个存在字段；本轮新增53个type27标志字段解释。
- 追通skillflag0_1高32位装配、常量元数据数组、GetOverHealRate和Heal上限分支。40232701原值1024→bit42→HP上限1.6倍；40232704原值2048→bit43→1.8倍。仅原记录标志，能力可合入其他位，不能冒充最终实机结果。
- UpdateParameter→BattleManager.GetDeltaTime→Unity Time.fixedDeltaTime成立，结合2021.3官方API文档，type27间隔2、type13支持时间30确认为游戏秒，不是现实墙钟秒。15次回复首次update可触发，不把15×2直接当精确持续时间。
- 13项受控原生检查通过（7个标志档位/组合、6个HP上限边界），执行真实选择函数及Heal上限片段，ParamS访问/小正整数加法建模；未运行完整Heal或实机。初始夹具入口x0缺值已修正后重验，详情见README。
- 修正Boss样本CSV漏列skillflag前缀的6行；原JSON未丢失。build_boss_chain_guide.py已最小修正，样本48→54行，逐槽/逐字段及CSV复杂值核对通过。旧E/v3载荷及全部独立报告未改。
- 本轮命令：现有.venv Python -B运行scripts/boss_heal_trace.py、scripts/boss_heal_probe.py、scripts/build_boss_heal_guide.py。只写output/boss_heal；视图修正另写output/boss_chain。manifest保存输入与代码哈希，非独立审查结果。
- 仍需闭合pattern选择/超共鸣切换及逐段触发；技能基值、整数转换、完整Heal及支持聚合仍未知。下一步优先样本选择链，非必要不采手机。补下载165个bdl的覆盖与语义未知维持前节结论。

## 补下载缓存已核对并补采（2026-10-15 20:30）

- 手机连接恢复。新清单68993文件，较前一份增加165个bdl，无删除；已有文件大小/mtime无变化。补采全部165新增包及77个data5，共242文件到raw/phone_20261015_refresh_02，旧原件不改。
- [本次交付说明](output/cache_refresh_20261015/README.md)、[新增文件CSV](output/cache_refresh_20261015/added_resources.csv)、[覆盖表](output/cache_refresh_20261015/coverage_audit.csv)、[4项核对PASS](output/cache_refresh_20261015/checks.json)、[新旧原件映射](output/cache_refresh_20261015/composite_inventory.jsonl)。242文件提取/归档内容核对通过。
- 77个data5重取密文与v3完全一致；核验完整JSON哈希后复用解码，重新导出39047记录视图，原值、类型、顺序、定位一致。角色1488、普通技能8634、Boss pattern2149、Boss技能3745；本次未新增主表记录。沿用v3字段/关联视图，不冒充新原生解码测试。
- 新清单范围77 data5 / 68655 bdl / 261其他，可由旧归档加补采映射定位。新增bdl尚未解码，未知目标语义保留；未重取媒体按路径/大小/mtime核对，不声称全量内容哈希或原子快照。
- 成功归档11169280字节；首次stdin清单尝试零输出已终止，保留refresh_01诊断。现无手机操作阻塞。旧E、v3及其指针不变，另设output/cache_refresh_latest.json。
- 下面Boss补充段的ADB阻塞为本次恢复前历史状态，已解决。下一步继续本地Boss flag/上限与时间链，以及有证据索引支持的bdl目标识别，不因新增包无目的重跑A—E。

## Boss后续段静态补充与新下载核对（2026-10-15）

- 新[补充说明](output/boss_chain/README.md)、[字段字典](output/boss_chain/field_dictionary.csv)、[cid2327描述/字段对照](output/boss_chain/cid2327_description_fields.csv)。7条type13/27局部规则，48行样本；推广至772条记录3031个存在字段，不覆盖旧E/v3输出。
- 静态追通Boss JSON/AB逐ID条件回退、按槽有序组装、SetExecSkill→initialize_ExAttack→type27/type13处理器。完整pattern选择/切换及当前运行版本仍未知。
- type27参数1为技能基值乘数、参数2为间隔输入、参数3为次数。type13参数1/2/6分别进入攻击/固定防御/移动增益，乘skillChainRate；参数3为支持时间。防御读取接受者_normalAtk，不能称为减伤百分比。时间到秒及整数转换规则仍待核实。
- 8项受控原生片段实验通过：首次update回复、间隔边界、15次停止、零次数、大delta仅一次、新设置覆盖、两组支持参数。Heal和SetSupport入口被拦截；不证明实际HP/最终倍率。3项样本结构检查通过。
- 强化治疗缓存param1=1.75，与截图2倍分别保留，不以截图改值。原始flag与缺失项保留。
- 用户告知又补下载缓存。本轮ADB两次无设备；Windows正常识别手机/MTP及ADB Interface，重启本机ADB后曾出现offline，已尝试reconnect offline。待恢复后核对新增范围，尚未宣称本次新下载已采集。旧全量采集发生北京时间19:19:14—19:23:33。
- 重跑：`.\.venv\Scripts\python.exe -B scripts/boss_chain_trace.py`、`scripts/boss_chain_probe.py`、`scripts/build_boss_chain_guide.py`（后两者同Python命令前缀）。只写output/boss_chain，依赖现有native/metadata/v3 records；无手机、无新依赖。下一步优先完成新下载对账及必要补采，再继续flag/上限与时间链。

## 前一离线字段与覆盖交付（保留旧快照，2026-10-15）

前一离线交付：`output/field_guide/guide_8753bb116c6e66b2/`。入口：[阅读说明](output/field_guide/guide_8753bb116c6e66b2/README.md)、[该系列指针](output/field_guide/latest.json)、[版本/输入/载荷清单](output/field_guide/guide_8753bb116c6e66b2/manifest.json)。以下数量及待采结论均绑定采集前旧快照；新进展以上节为准。

- [字段字典CSV](output/field_guide/guide_8753bb116c6e66b2/field_dictionary.csv) / [JSON](output/field_guide/guide_8753bb116c6e66b2/field_dictionary.json)：11261个来源/表/类型/路径条目；已确认2188、推断58、未知9015。此分组计数不是字段解释率；同名参数按效果分域，原值示例、缺字段计数、单位确认状态和定位分列。
- [实际样例CSV](output/field_guide/guide_8753bb116c6e66b2/record_comparisons_examples.csv) / [JSON](output/field_guide/guide_8753bb116c6e66b2/record_comparisons_examples.json)：30行，先做cid2327根/子HighHP、143001、必杀116入参、Extra五档、36000358两来源冲突；原文、片段、中文和数值解释分列。Extra仅关联同一嵌套对象的等级/描述/ID列表，不用文案百分比代替参数证据。
- [已验证规则扩展CSV](output/field_guide/guide_8753bb116c6e66b2/record_comparisons_highhp.csv) / [JSON](output/field_guide/guide_8753bb116c6e66b2/record_comparisons_highhp.json)：34条HighHPAll、143行存在字段；不解释param4、不补缺失，不推定玩家解锁或最终倍率。其他效果参数继续未知。
- 实际补充数据：原先完整JSON内的18296个辅助顶层记录/文档视图新增[JSONL](output/field_guide/guide_8753bb116c6e66b2/supplemental_records.jsonl)和[CSV索引](output/field_guide/guide_8753bb116c6e66b2/supplemental_record_index.csv)。覆盖APK Boss pattern/skill、传授、Class/Extra/Leader、羁绊/共鸣等；与E核心38849条合计57145个顶层视图。另2658个Extra/被动嵌套视图与父项重叠，不相加作为实体数。const根文档是分析视图，不是角色/技能实体。
- [覆盖审计CSV](output/field_guide/guide_8753bb116c6e66b2/coverage_audit.csv) / [JSON](output/field_guide/guide_8753bb116c6e66b2/coverage_audit.json)：按取得、解码、解析、导出、关联、解释分层。原E确认图不变，新增144967条辅助候选引用明确标推断。45次缺技能候选引用涉及Extra第491—493项的9个不同ID；1644次其他命名空间缺候选。全部保留，不证明记录失效，不默认删除或强行跨表按同号替代。
- 无E已验证入边的技能为缓存4828/APK9416；再计辅助候选仍无已知入边为缓存2859/APK6430。这是指定图内情况，不是废弃/无效数量。重复、历史、占位或未生效性质未确认时均原位置保存；str0数字串未自动当技能ID。
- 定向补查既有Unity头部19项错误：[原字节和分类](output/field_guide/guide_8753bb116c6e66b2/unity_header_gap_audit.json)。19项均32字节、脚本指针为空，共608字节已保存，不计成已解析游戏记录。已有9个按类名候选中6个完整可读、3个字段读取失败（2个ChroSkillParameterView、1个CharaDetailSkill），原二进制已保留；目标性质未证实，不把181783个对象元信息导出当所有目标字段已解析。
- [本轮核对](output/field_guide/guide_8753bb116c6e66b2/checks.json)：8项PASS，覆盖全部57145视图与原JSON字节/位置、APK四组件完整一致、原文片段、类型限定、CSV数量、辅助引用及19项错误原值保留；未重跑A—D或既有全部E原生实验，不冒充实机/独立审查。

重跑只写`output/field_guide`，复用Python3.12.14及现有依赖，不改正式E输入/历史构建：

```powershell
Set-Location 'E:\代码项目\锁链战记数据解包'
$env:PYTHONIOENCODING='utf-8'
& .\.venv\Scripts\python.exe -B scripts/build_field_guide.py
# 仅重建19项头部证据时先执行（现有UnityPy1.25.4）：
& .\.venv\Scripts\python.exe -B scripts/audit_unity_headers.py
```

字段交付器使用标准库与现有export_master辅助函数，需正式E构建、既有手机清单/采集清单、组件JSON、必杀追踪和Unity扫描/定向证据。头部脚本另需原Unity容器。完整工作区前提及CSV显示限制见新README，不是独立可运行包或未来快照通用验收器。

## 采集前具体缺口（历史依据，现已补采）

- 2026-10-14外部清单共68789个文件：77个data5，电脑取得/解码11个，66个尚无采集件；68451个bdl未取得/识别；其余261个其他后缀/无后缀文件仅取2个技术文件。三组总数已核对，未凭名称全部排除其他文件；候选文件数不等于目标表/记录数。没有可信全游戏目标索引，不报全游戏百分比。
- cid2327 pattern0=40232700、pattern1=40232701及传授候选patternid0=40232702未在当前APK pattern表找到。旧手机清单确有`bossinfo.data5`134000字节但电脑未取得，是高价值缺件候选，不能用普通skilllist同号或旧APK数据替代。
- 用户随后连接并授权全量采集；本次已完成外部files/cache采集及77文件解码，见上节。旧14件/旧清单保持，私有目录未采，不自动Root、不清缓存、不更新/卸载。
- 电脑已取得范围的原值和辅助视图可查询；全部资源取得、全部效果解释、当前加载版本/玩家开放状态、完整治疗/增益、成长及最终战斗倍率仍不成立。只对实际缺资源/运行态问题安排最小操作。

## 阶段E实际交付

当前快照：`snapshot_223183400c1c62013338`；正式构建：`build_261ac189c316abba`。旧构建`build_d21ab77ae4cbcdf3`及其载荷保留不变。

[使用说明/输出索引](output/export/README.md) · [当前构建指针](output/export/latest.json) · [manifest](output/export/snapshot_223183400c1c62013338/build_261ac189c316abba/manifest.json) · [验证结果](output/export/snapshot_223183400c1c62013338/build_261ac189c316abba/validation.json)。

|来源|角色记录|技能记录|四槽/八槽角色|原始槽位/sub引用|
|---|---:|---:|---|---|
|缓存|1482|8559|406 / 1076|10232 / 3203|
|APK|7800|21008|1927 / 5873|54692 / 7863|

- 合计38849条主记录，分四份来源JSONL；15份完整JSON保留所有辅助表及包装字段。角色含NPC等，不等于可用卡数；未声明全游戏覆盖。
- 合计75990条原始引用，含11066条sub边。全部父记录、引用序号、顺序与重复保留；根/子图不递归执行。一层展开59134项场景结果，均非玩家实际安装声明。
- 缓存104条sub须回退APK。假定JSON快照与APK都装入时，11066条sub均可关联；APK单层有3条APK sub缺目标，保留MISSING_ID。八槽55592个槽位保留SLOT_ROLE_UNKNOWN，未套四槽角色。
- 119个角色、568个技能跨来源同ID差异逐字段保存；不合成当前唯一值。当前输入来源内重复ID、坏记录、解析异常为0；未来异常会保留可取得原字节及具体错误，受影响查询标异常。
- 仅ability1105的存在param0/1/2/3/5附已有局部语义。缓存34条HighHPAll按27/4/3三种参数存在组合核对；不补默认值、不解释param4、不统一求值。其余29533条技能的参数语义UNKNOWN，原值照样导出。
- CSV仅38849行可追溯筛选视图，不是完整交付或生效表。JSONL保留缺失/null/0、字段类型、嵌套、数组；来源JSON副本保留精确原字节。
- manifest记录APK版本、快照、解析器/解释规则版本及SHA、验证器/模型脚本SHA和依赖锁；构建内保存必要脚本及证据副本。更新生成新snapshot/build，不覆盖旧输出。

## 阶段E交付修正（2026-10-15）

- 修复scripts/export_master.py已有构建分支：全部载荷校验成功后更新所选输出根的latest.json，缺失则创建；失败时不改指针或旧载荷。
- 新增scripts/verify_export_pointer.py。5种独立目录测试全部PASS：首次导出、同构建复用、缺指针恢复、指向其他真实构建后切回、损坏测试副本校验失败时指针不变。
- 原有12项当前快照验证及4项受控原生结构场景在独立目录重验PASS。主记录JSONL、引用、冲突、一层展开、异常、CSV和D样本等10个语义载荷与修正前字节一致；原输入、独立审查报告、旧正式载荷不变。
- 测试及日志只写work/phase_e_delivery_fix_20261015_4a244651af/；原验证器另在work/phase_e_fault_*创建/清理临时故障目录。测试完成前正式指针未变。
- 验证后生成正式新构建，manifest与独立已验构建字节一致、37个载荷SHA全部一致，再复制已绑定该manifest的validation.json；正式latest.json已明确选定新构建。
- 修正记录：[5种指针结果](work/phase_e_delivery_fix_20261015_4a244651af/pointer_tests/pointer_checks.json)、[语义与保护核对](work/phase_e_delivery_fix_20261015_4a244651af/delivery_fix_checks.json)、[正式选定依据](work/phase_e_delivery_fix_20261015_4a244651af/formal_selection.json)。损坏副本仅保留在独立测试目录供诊断。

## 验证与重跑

12项检查PASS：全量JSONL/完整JSON回读、类型与字节定位；记录/引用数量；四/八槽；cid2327；36000358冲突；循环/自环/共享子项；34条参数缺失组合；重复ID/坏JSON/null/0/缺引用；CSV追溯；输入与证据版本。

4项结构场景同时对照既有受控原生安装模型：42011300跨来源、602循环、36000376自环、40034712+40034714共享子项。新增故障注入导出也通过：坏缓存原字节及缺APK技能表错误保留，其余7800条APK角色、8559条缓存技能仍导出。临时测试件在work内运行后清理，未改真实输入。此前D的32项HP、11+1关联及4项来源实验复用锁定证据，不冒充本轮新测或实机观测。

```powershell
Set-Location 'E:\代码项目\锁链战记数据解包'
$env:PYTHONIOENCODING='utf-8'
& .\.venv\Scripts\python.exe -B scripts/export_master.py
& .\.venv\Scripts\python.exe -B scripts/verify_export.py
```

必须从项目根目录运行，复用Python3.12.14的现有.venv；导出器用标准库，验证器需要Unicorn2.1.4、work/protection/il2cpp_loader_seed1.bin、模型脚本及manifest所列原输入路径。构建目录可供数据消费，完整重跑依赖现有工作区，不能宣称独立运行包。完整逐项前提、独立输出命令及写入范围集中在README。

verify_export.py是当前快照回归工具，固定数量/样本不适用于任意新快照。当前更新是新输入重新全量导出并保留旧构建，未实现增量解析。新快照先核实变化与适用回归，再调整有依据的基准，不能只改断言获得PASS。依赖锁哈希目前不参与build ID，本轮未处理该可选改进；不承诺环境变化自动刷新构建。未新增依赖或验证干净环境安装。

## 仍未知与后续范围

- 补充只读核对：[cid2327截图字段覆盖](output/sample/cid2327_截图字段覆盖.md)。本轮已将相关辅助JSON补成逐记录/嵌套阅读视图并标注候选关联；截图LV60—80属性及全部细化倍率尚未还原。E完成及新字段对照都不代表整页数据库内容一一复刻；截图仍仅为外部参考。

- 玩家实际CardInfo.skillid、等级/突破/解锁条件、当前激活和接受的JSON版本；不能把主表定义当实例。
- 八槽角色、其他效果参数、完整必杀后续段与单位、全局叠加及最终战斗倍率。元数据枚举匹配不代表参数含义已确认。
- 外部数据库截图没有解锁条件或测试原始数据，不覆盖解包原值。
- 当前已完成本次可访问外部files/cache的全量采集和77个data5原值导出；bdl结构化目标、未列命名空间、私有/服务端范围仍未知。后续先利用本地原件静态核对，无需Root或模拟器，不把全部未知实机验证作为前置条件。

## 2026-10-16 截图对照与交接（本轮结束）

- 完成 [cid30236 チーカ HTML 对照页](output/card_comparison_cid30236/index.html)，附同目录 comparison.csv/json、evidence.json、reference.png 和 manifest.json；生成脚本 scripts/build_chica_comparison.py。
- 33项：9项文本或局部规则已对应、15项原值待解释、5项差异待核、2项未建立对应、2项网站添加排除；不是完成百分比。未把候选数字匹配写成最终倍率。
- 54条完整证据与v3源记录逐对象核对一致，全部引用和本地下载链接有效，HTML含33项；结果见 [validation.json](output/card_comparison_cid30236/validation.json)。内置浏览器本地服务连接超时，未完成视觉/交互验收；可直接在本地浏览器打开HTML。
- 完成 [HANDOFF.md](HANDOFF.md)，81行，文档链接已核对，包含当前有效数据入口、已确认规则、缺数据/缺解释、已解决事项及单一后续任务。
- 遵照用户限定，本轮未扩展新逆向、不连接手机、不重做历史验证；原始采集件、正式E构建和独立审查报告未修改。后续交由新对话。

- 2026-10-16用户补充：获得来源、登场日期为网站添加。已同步对照生成器、HTML/CSV/JSON及HANDOFF，不再计入游戏数据提取缺口；未扩展调查。
