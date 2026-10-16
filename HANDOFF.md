# 交接：数据提取与截图对照

更新：2026-10-16（审查整改，本轮）。独立审查结论「带明确限制通过、无 P0」的整改已全部完成：P2-1（--prior-report 复用分支改从报告所在目录解析，三模式复验 PASS、77 重放 0 差异）、P2-2（77 重放口径澄清＋bossinfo/helper 两变体原生解码与 v3 字节一致）、P1-2（jni_prefix_probe／metadata_decode_probe 隔离实测，产物与项目逐字节一致）、P2-3（protection_sample／callback_sample／callback_key_candidates 补 mkdir，隔离冒烟 PASS）、P2-4（--cert-hex 端到端 2 bdl，APK 隐藏运行，产物与 full_unpack 逐字节一致）。P1-1 待提交清单已列在 [审计文档](docs/tasks/20261016-reproducibility-audit.md) 整改记录，等用户授权后显式提交（不推送）。本轮修改：decode_cache_snapshot、protection_sample、callback_sample、callback_key_candidates 四脚本及审计文档；未提交 git、未推送、未覆盖正式输出。前轮各线结论继续有效。

更新：2026-10-16（可复现性审计与规范，本轮）。完成第三方独立解包审计：git HEAD 原始状态在 APK 原生库提取、旧解码报告依赖、`work/protection` 建目录三处必败，均已最小修复并在仅含仓库文件的隔离目录实测通过；恢复镜像 SHA256 与钉住值一致，data5 解码与既有参考字节一致，项目侧 77 文件重放与 v3 规范化后 0 差异。AGENTS.md 新增 §7 GitHub 存储策略、§8 重构（8.1 独立可复现性／8.2 分层发布 A—C／8.4 发布前验证）。审计全文、文件盘点与下一阶段清单见 [可复现性审计](docs/tasks/20261016-reproducibility-audit.md)。本轮未提交 git、未推送、未打包上传；`full_unpack_*.py`、`build_char_roster.py`、`docs/` 仍未跟踪，git 补缺是下一阶段最高优先。前一轮完整解包及以下各线结论继续有效。

更新：2026-10-16（完整解包）。本轮完成已取得本地资源完整解包：全部68655个bdl解码展开成功（0失败），导出834741个对象（73490 PNG/17389 WAV/50051 OBJ/2845 TXT/759621 JSON），输入账本覆盖全部68993个缓存文件；77个data5沿用v3已验证解码；261个其他文件逐项分类排除。前轮ability1008（TargetStageAll）37记录/111字段及前六类型、cid30236五组政策继续有效；不重做A—E，不改原始资源、v3/E或独立报告，真实安装/后备转写和完整战斗另论。

## 1. 当前有效入口

- **完整解包**：[阅读说明](output/full_unpack/README.md)、[输入账本](output/full_unpack/ledger.jsonl)（68993行，来源/格式/状态/输出/理由）、[对象产物](output/full_unpack/objects/)（56类目录，每包objects_index.json）、[覆盖统计](output/full_unpack/coverage.json)、[4项验证PASS](output/full_unpack/validation.json)、[cid附加索引](output/full_unpack/cid_index.json)（6233个，仅命名规律）。重跑：full_unpack_run.py（分片续跑）→merge→verify→finalize。

- 最新入口：[原对照页](output/card_comparison_cid30236/index.html)，顶部含1095、1017、2012、3000、99、7、1008七个独立检索区，分别按普通技能名称/ID/原文检索407/321/406/382/133/64/37条；原チーカ101项及截图对照保留。无需联网。
- [1008对象/当前地形/接受者攻防依据](output/ordinary_effects/ability1008/README.md)、[389项本轮局部原生检查](output/ordinary_effects/ability1008/native_checks.json)。查询`query_effect_dictionary.py --id 43023606`看沙漠本项攻击/减伤各12.5%；`--id 102070`看攻击5%、防御原值1；`--id 42011507`看607=7或6。target_conditions列地形，trigger_context列提供者/接受者及后备边界。
- [7地形编码/当前背景/自身攻防依据](output/ordinary_effects/ability7/README.md)、[1390项本轮局部原生检查](output/ordinary_effects/ability7/native_checks.json)。查询`query_effect_dictionary.py --id 43023607`看沙漠与5%本项攻防；`--id 102071`看代码/正文矛盾；`--id 47000707`看原值250；`--id 47000830`看1320或条件。
- [99门槛/目标/攻防/正时间及-1依据](output/ordinary_effects/ability99/README.md)、[192项既有原生检查](output/ordinary_effects/ability99/native_checks.json)。查询`query_effect_dictionary.py --id 43023616`看攻防/30游戏秒；`--id 42080504`看仅暴击触发与-1标记；`--id 127008`看缺攻防字段，不填0。
- [3000共鸣资格/Support3/四字段依据](output/ordinary_effects/ability3000/README.md)、[86项既有原生检查](output/ordinary_effects/ability3000/native_checks.json)。查询`query_effect_dictionary.py --id 43023611`得普攻/技能各+.1、45游戏秒、暴伤系数+.1；`--id 40121710`得四项缺失及资格上下文，未补默认值。
- [2012时间/暴击/动作门槛依据](output/ordinary_effects/ability2012/README.md)、[49项既有原生检查](output/ordinary_effects/ability2012/native_checks.json)。查询`query_effect_dictionary.py --id 40431614`或`--id 40126713`，在`trigger_context`看动作/目标输入和字段缺失状态。
- [1017对象/职业/攻防依据](output/ordinary_effects/ability1017/README.md)、[236项既有原生检查](output/ordinary_effects/ability1017/native_checks.json)。查询`query_effect_dictionary.py --id 40768606`会在`target_conditions`集中显示param0/iParam0，未知其他参数保留。
- [1095范围与依据](output/ordinary_effects/ability1095/README.md)、[32项既有原生片段检查](output/ordinary_effects/ability1095/native_checks.json)。快速查询：`.venv\Scripts\python.exe -B scripts/query_effect_dictionary.py --id 40129301`，也可`--name 祈りの聖女`；Boss需显式`--table bossskill`。返回原记录、中文解释/依据、未知原值，不混命名空间或同名版本。
- 当前主进度：[逐描述效果CSV](output/card_comparison_cid30236/description_effects.csv)、[JSON](output/card_comparison_cid30236/description_effects.json)，HTML攻防表同源生成。逐效果清单已扩展101项，101项已有原文明示数字或限定单项配置数值/公式、0项数值空缺；首批攻防单列40/40。五组采用值为屏障动态固定量公式（默认系数1时玩家路径名义原始ATK20%）、Class暴击+40个百分点、暴击回复25%、Chain每次有效事件阈值10%、敌方弱化30游戏秒；截图5%/20%/20%/20%/45秒保留。详见[裁决政策](output/card_comparison_cid30236/difference_sources/adoption_policy.json)。
- 同目录 [CSV](output/card_comparison_cid30236/comparison.csv)、[JSON](output/card_comparison_cid30236/comparison.json)、[54条完整来源记录](output/card_comparison_cid30236/evidence.json)、[manifest](output/card_comparison_cid30236/manifest.json)。
- 旧概览33项（含等级/素材等目标外项目）：13项文本/局部规则已对应、3项截图数值已裁决、11项分组原值尚有解释边界、2项其他差异、2项未建立对应、2项网站添加排除。这不是完成率；屏障/Chain所在分组仍保留raw，不影响其中数值取值已裁决。
- [type105证据](output/boss_chain/type105/README.md)、[type112证据](output/boss_chain/type112/README.md)、[type13基数证据](output/boss_chain/type13_basis/README.md)、[合并77条限定规则](output/card_comparison_cid30236/field_dictionary.json)、[2684来源记录/6613存在字段CSV](output/card_comparison_cid30236/verified_parameter_views.csv)（同目录有JSON）；105为142/284、112为96/657、13为718/718（玩家基数换算有条件）。v3历史字典不改。
- 当前核心原值：[records.jsonl](output/cache_full_20261015_v3/records.jsonl)，39047个记录/文档视图，134个表；完整JSON见同目录 decoded。
- 当前核心包含1488条角色、8634条普通技能、2149条Boss pattern、3745条Boss skill。角色条数不等于可用卡牌数。
- [全量缓存说明](output/cache_full_20261015_v3/README.md)、[最新核心指针](output/cache_full_latest.json)。
- [字段字典](output/cache_full_20261015_v3/analysis/field_dictionary.json)：4671项字段观察，绝大多数不能当作已解释语义。
- [核心覆盖审计](output/cache_full_20261015_v3/analysis/coverage_audit.json)、[引用](output/cache_full_20261015_v3/analysis/references.jsonl)、[未关联项](output/cache_full_20261015_v3/analysis/unresolved_references.jsonl)。均有对应CSV视图可筛选。
- [后续下载核对入口](output/cache_refresh_latest.json)、[刷新说明](output/cache_refresh_20261015/README.md)、[当前组合清单](output/cache_refresh_20261015/composite_inventory.jsonl)。
- 最新刷新取得165个新增bdl，77个data5与v3密文及解码JSON一致；因此主表查询仍可使用v3。
- 最新可访问外部缓存清单68993文件：77 data5、68655 bdl、261其他。未变化媒体仅大小/mtime核对，非全文件双端哈希或原子快照。
- 原始全量包：raw/phone_20261015_full_02/external_cache.tar；补充包：raw/phone_20261015_refresh_02/external_cache.tar。不要改写。
- 已审查E构建：[build_261ac189c316abba](output/export/snapshot_223183400c1c62013338/build_261ac189c316abba/manifest.json)。它是较早输入的稳定交付，不能冒充最新全量缓存。
- [正式E说明](output/export/README.md)、[复审报告](output/审查报告/阶段E独立交付复审报告_2026-10-15.md)、[历史进度](STATUS.md)。

## 2. 已确认规则与证据

- 数据记录保留原始字段、缺失、数组顺序与重复、字节定位及SHA；不得静默补默认值。
- 逐ID条件回退：指定JSON表查不到ID时才走APK/AB；不逐字段合并。主表存在不证明玩家已解锁或当前实例已安装。
- 普通技能子效果只按已证实的单层执行语义展开；不能把递归图遍历当作游戏执行。
- 阶段D安装/资格/来源证据脚本：scripts/phase_d_trace.py、phase_d_chain_probe.py、phase_d_source_rule.py；详见STATUS与阶段D审查报告。
- Boss pattern按有序技能槽引用Boss skill，普通skilllist同号ID属于另一个命名空间。
- [Boss链规则字典](output/boss_chain/field_dictionary.json)、[追踪](output/boss_chain/trace.json)、[受控片段结果](output/boss_chain/native_checks.json)。
- type13：攻击输入乘skillChainRate，形成1+输入；防御参数乘chain和接受者_normalAtk再整数化，是固定防御量；移动形成1+输入。
- type27：回复输入乘getBasicSkillAttack(true)再整数化；间隔与次数来自对应参数。初始化计时0，更新可能立即回复，一次更新最多一次；不是完整战斗仿真。
- [时间/回复规则字典](output/boss_heal/field_dictionary.json)、[追踪](output/boss_heal/trace.json)、[常量](output/boss_heal/constants.json)、[13项受控检查](output/boss_heal/checks.json)。
- type13.param3和type27.param2单位为游戏秒，沿fixedDeltaTime链确认；非墙钟秒。
- type27技能高32位的42/43位对应1.6/1.8上限档位；其他能力旗标仍可能合入。不要套到ability21。
- [可用局部参数视图](output/boss_heal/verified_parameter_views.json)：772记录、3084字段；不是全效果解释。
- [Elemia样例](output/boss_heal/cid2327_description_fields.json)：54行；其语义不能不加条件转用到チーカ。
- type105：param1是单次前方攻击的技能基值系数；Attack整数输入=floor/clamp(float32(getBasicSkillAttack(true)×param1))。Chain在基值内乘一次；基值含BattleParam._skillAtk、状态与技能等因子，面板ATK换算及最终扣血未验证。
- type105.param6是每目标尝试上限，有限正数向零截断；在范围判定前计数，持续在范围内的样例为5次Attack调用，离开范围也消耗预算。仅推广type105的142条/284字段，不推广到type112。普通/沙漠/超共鸣明确映射43023601→00、00→05、02→09，系数3.5/3.75/4.25。
- type112.param1：设置时算floor/clamp(float32(getBasicSkillAttack(true)×param1))，Chain已在基值内；整数经CoveringFirePoint→BulletDelay保存后原样传到Attack/AttackOther入口。六条Boss技能普通02/03=.75、沙漠06/07=.875、超共鸣10/11=1.125。只解释单次伤害输入，不套用type105次数规则或承诺最终扣血。
- type112.param5：每陷阱对象共用爆发上限，有限正值向零截断；本卡5次。param0=1有敌才消耗次数，2为定时模式；param4=.25为游戏秒间隔，无敌仍累积计时，一次update至多一次。16项原生片段检查（含既有8项伤害）通过；缺失param4/5不补0。
- type112.param8=88725为6×3位图，bit i为(i%6,i//6)，置位0/2/4、7/9/11、12/14/16共9格；初始战场6×3，边界按运行时尺寸夹原点。param9=1不清理旧对象，两段都执行时9格各2层。param7=.001推力经Attack进入允许条件下的DamageL(10)请求，原文転倒的视觉动作对应为推断。23项受控检查通过。
- type13.param2名义基数：已核CreatePlayer缩放片段使用.1×CardInfo.ATK及初始化因子后截断，故.3/.325/.375可对应名义原始ATK3/3.25/3.75%；接受者当前normalAtk仍含后续修正，不能用该名义系数直接算最终guard。7项片段检查通过，含双重截断反例。只对已核玩家构造路径作此换算。
- HighHPAll ability1105既有局部规则保留；给定列表的实验结果不等于实际装载或最终倍率。

## 3. 尚未解决：缺数据/关联与缺解释分开

缺数据或覆盖依据：
- 没有可信全游戏目标资源索引；私有目录、服务端范围未知，不能宣称全游戏100%。
- bdl已整体解码展开（见上完整解包入口）；对象语义未解释属字段解释线，不再是"已取得但未识别"。APK内置媒体未批量导出（索引已有），需要时按同一UnityPy管线补。
- cid30236卡面资产绑定未建立；不能据此断言文件不存在。获得来源和登场日期按用户补充属于网站添加，不再算提取缺口。
- 全缓存引用审计还有66处未关联引用（Extra 60、传授pattern 6）；保留未关联项，不删除记录。

前阶段单项数值清单已无空项，本阶段五组截图取值已裁决；以下边界保留，不再作为本阶段阻塞：
- 屏障实际战斗规则/当前normalAtk修正未知；采用公式，不能把默认名义20%当无条件20%减伤。五组截图注数成因未知，未宣称版本更新或截图与解包数字相同。
- 羁绊102071名称/父文案写砂漠，自身text写森林，源内矛盾保留；本轮已核7.param0=4是沙漠编号，经1<<4匹配背景flag16。其他类型地形输入不自动套用。
- 玩家当前装载/解锁、全部叠加/最终HP，完整候选队伍范围、陷阱动作视觉/抵抗/最终扣血及pattern选择均未纳入本数值Goal验收。
- 等级/突破到ATK/HP成长公式、职业/武器显示链和卡面绑定属后续范围。原始资源/历史证据不变。

## 4. 已解决，不应重复调查

- 羁绊106001缓存缺ID，已在APK同名空间找到并按既有逐ID回退；该数据缺口已解决，完整来源见[必杀威力证据](output/card_comparison_cid30236/skill_power/README.md)。

- A—C提取/解码路线已成立；不用重新从APK字符串搜索开始，不需要完整IL2CPP恢复。
- bossinfo.data5缺件已补齐并解码；全77个data5已导出，不能继续沿用“只取得11个”的旧判断。
- 后续下载确实已补采：新增165个bdl，主表77个未变；不再因旧ADB离线记录要求用户重下缓存。
- E指针复用修复完成：5种指针场景、12检查+4原生结构场景通过，新旧10载荷一致。
- 本轮没有重新执行这些历史测试；结论引用已有证据，不冒充新测。
- 不重做无新证据的穷举、不Root、不清缓存、不安装模拟器；不新增全量双端哈希门槛。
- 中文名、标签、外部资料、获得来源和登场日期按用户说明属于网站添加；后两项为2026-10-16补充，不据此断言游戏文件中绝无相关信息。

## 5. 当前可复用字典进展与下一最小动作

本轮只处理普通`skilllist.ability=1008`（TargetStageAll）。37条param0/param1/param3全存在，共111字段（净新增108）；旧攻防两规则扩大，新增地形规则。字典现77规则，视图2684来源记录/6613字段；普通子集1723来源记录/4947字段、60规则。背景99条仍为辅助证据，不计新角色数。

- 对象已核：PlayerManager当前param是接受者；提供者候选来自BattleManager.GetAllCharaList(0)→_aChara_Player@70，非空且存活活动。实际类型筛选、IsEnableAbility、1008地形判断执行；本类型段无自身排除、接受者职业或距离测试。可含自身或其他队友，不能套7自身范围或1017职业掩码。安装数组/位缓存、候选列表内容仍是夹具输入。
- param0沿相同IsTargetStage→当前背景→源flag路径，复用7地形证据及相同镜像SHA；9种源编码为2/3/4/13/15/20/325/607/1320。新编码3、607分别对99源背景验证，607是7或6。其他7编码复用既有匹配表，并在1008全部37条攻防样本实际经过地形路径。背景名仍按实际匹配行列ID/flag/原名/来源，不编造唯一正式枚举。
- param1乘接受者本项攻击，增加=(raw−1)×100%；param3乘接受者本项受伤量，减伤=(1−raw)×100%，原值1为中性。43023606在沙漠下本项攻击/减伤各12.5%；102070为攻击5%、防御原值1。两段不乘Chain；本轮不推广同记录param2/4/5或敌方管理器。
- 非活动提供者转独立后备路径，该generic BackUp段筛选另一类型并查IsTargetHome；未证明1008的后备安装/转写。40526403原文提及后备仍原样保留，不把文本升级为1008直接生效结论。敌用47000910保留同表数据，不推定玩家管理器实际装入。真实安装/解锁、完整叠加/最终HP仍另论。
- [新trace](output/ordinary_effects/ability1008/trace.json)含37完整源记录、99背景、9编码匹配表、方法/对象字段/片段与SHA；[389检查](output/ordinary_effects/ability1008/native_checks.json)：新编码背景198、37条攻防命中/不命中148、同人/不同人和职业0..5共24、当前背景覆盖4、混入其他类型/缺1008共4、存活活动路由8、候选列表getter3。缺ReadOnlySpan元数据槽的初次局部失败已补夹具槽后通过，未改原值/机器码；未重跑7既有1390项。
- 同一字段模块/主生成器/逐效果/查询/验证器更新，新增ordinary_1008_probe.py及限定证据；HTML第七区37记录/111字段，查询target_conditions列地形，trigger_context列范围。1008相关原逐效果行补param0/对象条件/依据，保留101项、旧状态及截图。未手改HTML。

实际运行：新1008探针389项、主生成器、验证器71项数据/结构检查通过；命令行43023606/102070/42011507与Boss同号隔离通过。37技能/99复用背景字节定位、原值/类型/换算、CSV/JSON/manifest/本地链接、前六类型和101项/五组政策均核。七段生成页实际搜索脚本在V8 DOM夹具14项筛选/隔离/恢复通过；file协议既有限制保留，未做视觉验收。旧原生证据只读，不重跑A—E/核心全量校验/手机。

已解决不重查：1008玩家侧活动提供者→当前接受者范围、param0资格/编码及两攻防字段；7及102071代码地形、前五类型和五组取值政策均有效。[旧数值审验](output/card_comparison_cid30236/completion_audit.json)仍只绑定冻结载荷；本轮看[validation](output/card_comparison_cid30236/validation.json)的reusable_1008/native_checks_reusable_1008及71项检查，非独立审查。

下一最小动作：只定向核40526403“后备亦生效”原文与1008活动提供者路径的关系，先沿该卡后备安装/转写及独立Backup记录查现有证据，不泛化其余角色/效果。该边界不影响本轮37条原值及活动路径规则可查。15%剩余额度暂停线保留，最近可见剩16%。

## 6. 重建对照页

从项目根目录运行 `.venv\Scripts\python.exe -B scripts/build_chica_comparison.py`。
生成器仅标准库，读取当前records.jsonl、Boss旧证据及本目录ordinary_rules/skill_power/timed_support/barrier/critical/movement/lifesteal/field_time/mana_chance/chain_mana/leader_condition/super_counter/wedge_time及barrier_request/difference_sources/chain_dispatch、ordinary_effects/ability1095、ability1017、ability2012、ability3000、ability99、ability7、ability1008已有证据和用户取值政策；图片优先取原临时附件，否则复用输出目录reference.png。请保留该图片。
主生成器写output/card_comparison_cid30236/，新增1095/1017/2012/3000/99/7/1008证据脚本分别只写output/ordinary_effects/下对应类型目录；不会修改原输入、正式E构建或审查报告。
页面含101条逐效果表（首批攻防40、其余61）、33项旧概览与54条完整记录；77条限定规则/2684来源记录6613字段均同流程输出，另含407条普通1095、321条普通1017、406条普通2012、382条普通3000、133条普通99、64条普通7与37条普通1008的独立检索区块；CSV/JSON和manifest同步生成。type112视觉对应为推断、type13玩家基数换算有条件，未冒充实机结果。重建后运行 `.venv\Scripts\python.exe -B scripts/verify_chica_comparison.py`。
既有浏览器file协议安全限制保留，未完成视觉验收；本轮HTML结构、本地链接及搜索脚本DOM夹具已核对。已提供本地HTML文件，可双击打开。
