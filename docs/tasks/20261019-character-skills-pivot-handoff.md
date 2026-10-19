# 锁链战记角色技能页整改主持交接提示词

2026年10月19日。将下文直接发给下一位主持即可。本阶段已完成到R2方法审查，旧主持及实施、审查均已停写；交接本身不解除用户要求的暂停。Git整理提交另见同目录 `20261019-character-skills-git-handoff.md`，不与页面扩量混成一个任务。

---

你接手《锁链战记》角色技能页整改主线，担任新的唯一主持和写入整合者。仓库为 `E:\代码项目\锁链战记数据解包`，使用PowerShell及既有 `.venv\Scripts\python.exe`。旧P3逐句绑定线已冻结并由整改主线取代，不再开P3B11；你要交付的是2236张可读角色技能页。

## 当前暂停和首轮动作

用户上一条执行授权是“允许追加，完成后先暂停”。五项整改和原Astra复验已经完成，现在暂停；本交接只授权接手和必要的只读核对，不自动授权完整cohort或全量运行。如果用户随本提示词明确要求继续，即视为恢复，无须再问一次；否则先报告接手结果和下一步，保持暂停。

先 `git status --short`，定向读以下资料，不通读全部历史，不重跑解包、旧native或全库统计：

1. `AGENTS.md`；`HANDOFF.md`只读当前入口。根交接有过时的“P3B10待新D”等记录，不能据此恢复旧线。
2. `docs/tasks/20261019-character-skills-pivot.md`，以及 `docs/tasks/character-skills-progress.md` 顶部“当前状态”。这是当前方案和状态入口。
3. `output/character_skills/review/host_r2_20261019/RESULTS.md`、`output/character_skills/r2_preparation/README.md`。
4. `output/character_skills/review/r2_20261019_methods/REPORT_RECHECK.md`。需要复核时再看同目录 `checks_recheck.json` 和原初审 `REPORT.md`；不要把初审REQUEST_CHANGES当最终未闭合。
5. `output/character_skills/r2_preparation/boundary_disclosure.md`、`cohorts/manifest.json`。具体候选和原值按需读同名JSON。
6. `output/character_skills/review/r1_20261019_card_pages/REPORT_R1_SOURCE_FIX.md` 和 `TASK0_REVIEW.md`。任务0实现入口在 `output/character_skills/type1082/README.md`、`native_checks.json`；该实现README仍有“未独立审查”的历史措辞，以后续TASK0_REVIEW为准，不为改措辞覆盖旧证据。

按需再读 `docs/角色技能完整解读实施方案.md`、`output/character_skills/README.md`、`output/reference_analysis/claude_cc_site_pages/README.md`、cid30236的101项描述效果及参考页。参考目录 `其他人的参考/claude_cc_site_pages/` 只读，只借版式和带来源候选，不复制其卡页数据。

首轮简报应交代：已完成边界、当前四项指标、待完成范围、Git是否已整理及源码是否漂移、恢复后的首个cohort和预算。方法/R1均已通过且用户已确认样本，不再让用户重复确认11张。

## 交付标准和汇报口径

目标是 `output/character_skills/pages/<cid>/index.html` 加 `card.json`：基础信息、固定13技能组、全部日文原文及行内参数/公式/机制或明确未知。13组为必杀技、能力、SA、共鸣、Leader、Class、Extra、PASSIVE、羁绊、英雄技、传授、CrossWorld、必杀效果类型；无配置也保留组入口，限定为“本输入快照未关联”。传授突破留在传授内；`skillid[0]`是效果类型，不作技能引用或描述分母。

每行互斥归类：A为可读数值/公式；B为有可追溯依据、相对原文新增的机制说明；C为原文、原值状态和具体未知原因。翻译或复述不计B，候选/ID/裸参数不计A。A可为部分填充，其余未知仍须显示。缺失、null、真实零分别处理，不填零、不猜。

证据确认/推断/未知与A/B/C独立。原文数字可确认“原文”，字段关联未证就同时标未知；规则本身确认不等于描述绑定确认。每次报告必须并列 **A率、整行确认率、原文A、C**，带数量和分母，不能单说“A率就是已解释率”。原文A与整行确认有交集，四项不是互斥分区。

本轮技能描述候选晋级和一般机制接入尚未实现，明确写 **“技能描述推断层暂不启用”**。B0和推断0不代表全库没有机制或11,409条hint没有覆盖。基础职业名称的推断、英雄技ID模式关联等其他层的标签要分别保留，不能混作整行推断数。以后若启用候选，最多按200–300个模板规划、只升推断，多候选留hint，不能以“唯一候选+数字对得上”升确认。

## 已完成和冻结成果

| 阶段 | 完成情况 |
|---|---|
| 任务−1源码保全 | 用户核过67文件、六模块6/6 hash及10张P3任务卡；实施补54项调用/配置闭包及遗漏辅助源码快照。前置阻断已解除，不重复补保全流程。 |
| 任务0 | type1082在extra专用链上的str0转发，结论限定FORWARD，已由R1独立审查支持。 |
| 11张样本 | 30236、7229、29、2020、5023、4009、8151、30004、10001、13001、30338；用户已复算确认。 |
| R1 | 最终PASS_WITH_EXPLICIT_SCOPE_LIMITS；36个真实父子引用/146处来源修复闭合，174个不同实际row_id审读。 |
| R2 | 初审1P1+4P2，原实施者修复、原Astra独立复验34项通过，F1–F5全部闭合，剩余整改0。只通过全量前方法。 |
| 全量与后验收 | 完整cohort、2236全量、790卡实际抽样验收均未执行；已有计划和NOT_REVIEWED队列不算已验。 |

11张当前统计为N_all/E/N_num＝387/0/387：

| 必须并列的指标 | 数量和比例 |
|---|---:|
| A数值/公式行率 | 185/387＝47.8% |
| 整行确认率 | 47/387＝12.1% |
| 原文A | 165/387＝42.6% |
| C仅未知 | 202/387＝52.2% |

B0；整行证据确认47/推断0/未知340；A中138行整行仍未知，部分A181。7229为A59/108、整行确认0/108、原文A59/108、C49/108。旧确认+提示核心10张19.6%、11张20.6%是另一口径，不作提升比较。旧384→新387＝补3条Leader＋保留2条不同原位置重复−2条SA内部标签，有逐行映射。

旧 `output/character_skills/pages/` 是用户确认的R1版，29文件与R1冻结独立29/29匹配；**当前通过R2的新版11张在 `output/character_skills/r2_preparation/pages/`**。不要误把旧版当最新版，也不要为了交接覆盖旧版。恢复后正式全量仍写既定pages目录，先在独立版本目录保存原11张及映射。

当前源码/准备输出冻结：`work/character_skills_r2_prep/snapshots/20261019-r2-f1-f5-frozen/manifest.json`，160项清单、128项增量实存、29项数据依赖。home-fix-frozen及更早快照保留为历史，不作为最新版。R1最终冻结是 `work/character_skills_card_pages/snapshots/20261019-pilot-r1-source-fix/manifest.json`。

R2已修五项：版本化cohort/run及campaign报告/待审队列并保留累计失败债务；实际extraabilitylist/passivelist/denju_lblist进入签名；card/HTML/receipt失败回滚及回滚失败禁复用；用真实引用槽/父条件/等级/源位置去别名且前插不串后续row_id；攻速原值确认与单位推断分层。不重开同一轮R2来“再证明一遍”；公共规则/来源大改或实际漂移才复核受影响范围。

## 来源和容易误判的地方

正式输入复用 `output/character_skills/profiles/{profiles,records}.jsonl`、`rules.json`、`links/character_skills.jsonl`、既有字段字典、缓存decoded及APK主表。整条CACHE记录优先，缺角色ID才回退APK，不能逐字段拼源。换算复用rules的conversion，区分倍率、增加量、百分点、固定防御量；×Chain和自身ATK基数按已有适用证据，不重复乘Chain。

沿用已给事实，不重新统计：2236人；字段页答案82,875、字段缺口5,560；描述页实例41,595＝398确认＋11,409提示＋29,788未知，12,505种句子。第三方1610行参数表已有36/37一致、1冲突及343条强候选核对，只作候选，不直接导入确认。

任务0证明extra专用预处理将包装str0解析为目标ID，再由资格选择及BattleParam查表装载目标能力。父档位、active集合、对象selector、缺param0默认值及逐句归属仍有边界，未实机/未恢复完整引擎。**4496是extra关联范围，不是4496个A行；11张链新增A和新增行内数值均0。** 其他六表2828页是别的链，不混算。若未来结论变化，NOT_FORWARD也只能行级判定：有原文数字留N_all/N_num计A·原文；只有既无原文数字也无其他数值来源才进E，附逐行清单、old→new row_id和排除前后分母，不整表排除5106。

基础信息保持以下处理：

- 职业复用名册JOB_NAMES并标推断；所属用homelist/已有IsTargetHome证据，7229 home1＝義勇軍，30236 home8＝湖都。旧roster接worldinfo.chara_place是地理命名空间误配，缺home不能用place代替；旧工具不接管。
- 7229 CACHE /charainfo/141缺critical，APK /909为0.0，页面缺失不跨源补40%或0%；30236同源0.4才格式化40%。
- atkspeed2→2.0秒/下是名义间隔展示；原值确认、单位推断分列。既有检查手工s0输入，完整charainfo→BattleParam赋值链未全证，非实机节奏，不倒数、不为此新native。
- 成长/战斗所属无可靠映射时显示外部/网站维护，原值保留详情；介绍、标签/外部资料、日期、等级表、画师/声优均保留明确来源或维护状态。
- 30004的能力重复源 `/skilllist/5772/text` 两段[26,77)、[116,167)，羁绊 `/supporterskill/212/text` 两段[21,49)、[86,114)。是不同原位置，应保留；同位置同实际引用别名才合并，不跨真实槽/父条件/等级合并同文。

## 恢复后的顺序和命令

冻结旧characters.csv决定cohort，不因新分母变化换组。依次ge60＝34、40to59＝290、20to39＝436，共760复杂角色（旧descriptions≥20，占68%描述量），再remaining＝1476。逐cohort按行加权报四联指标、N_all/E/N_num、B、证据交叉、部分A、失败、未知原因、体积和实际审阅时间，不先做简单卡。

入口 `scripts/character_skills/card_page_batch.py` 默认plan-only，显式manifest/cohort。以下命令是恢复后的第一批计划示例；当前暂停时不运行：

```powershell
& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_batch.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --cohort ge60 --output output/character_skills/pages
```

只有用户恢复且确认当前源码/依赖对应已审方法、原11张已保存后，才在该命令加 `--execute --resume`。后续改cohort，不重建冻结名册。输出追踪在 `_batch/<cohort>/runs/<run_id>/` 和campaign报告，latest只是指针。复用受源码/数据/产物hash及blocker约束；不能绕过签名或把子集成功称整个cohort完成。

全量之后必须完成 **全部760复杂卡＋从其余1476固定seed20261019抽30** 的实际行审查，790唯一cid已冻结。每卡至少10个不同实际行，不足全列；约7600–7900行，保存cid/row_id、原文、值/机制、等级、来源、未知原因、问题和复验结论。NOT_REVIEWED队列、自动检查和抽查包生成都不代替核读。

## 调度 写入和预算

用户已授权一个实施子智能体和独立审查子智能体。原实施Sol/high，R1原审Sol/high；R2和全量后抽样采用Astra/high独立上下文，目的为增加判断路径差异，结论仍靠证据。旧子智能体均停写，新会话未必能复用其工具身份，按职责新建即可；不每cohort另派D、不另开P3批次、不升max。当前暂停时不派实施。

主持接管 `docs/tasks/character-skills-progress.md` 和整改方案；新增实施只写card_page模块及本线输出、自己的任务卡；独立审查只写新版本审查目录，修复回实施。旧P3/profiles/原始输入/旧报告只读；不接管根HANDOFF/STATUS其他改动。若Git整理对话正在暂存/提交，页面线保持只读，待其交付commit/白名单再恢复写入，避免提交中源码漂移。

截至2026-10-19 21:50:18（Asia/Shanghai）最后执行阶段额度观测，同7天窗口used37、reset1792903149；全程起点28、页面起点29。全程观测+9、页面+8；追加修复35→37为+2，授权本次最多到38已随暂停结束。额度共享且取整，不能称独占费用；新会话不能重新从零计预算。

原页面累计14点/16有效小时预警、20点/24小时停止；全程累计20点/32小时预警、26点/41小时停止。按历史整数差，页面距总20点还约12、全程距26点还约17，实际须新读共享窗口并说明其他对话/重置影响。旧R2后10–18点估计包含现已完成的R2，不能整段再相加；生成和790卡实读仍未测吞吐，恢复前重新估算，尤其实际核读时间，原总停止线不自动放宽。

Git状态最后核对HEAD＝c50433f，许多源码和任务卡仍untracked，有本线及其他任务已修改文件；源码快照不等于已入Git或干净环境可复现。先读Git整理对话的新交付（若已有）再判断。不要删除、重置、批量暂存，不 `git add .` 或强制加入output/work/raw。没有授权推送、上传、发布。P3B10已D PASS_WITH_EXPLICIT_SCOPE_LIMITS闭合（10/10、44/44、17/17、6/6、121项hash），不再待新D，不派P3B11。

接手后请先给简短、可核对的状态与恢复计划；已有结果不再证明一遍，未完成部分不写成完成。除非用户明确恢复，保持暂停。
