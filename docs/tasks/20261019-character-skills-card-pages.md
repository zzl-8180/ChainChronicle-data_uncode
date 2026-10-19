# 角色技能页11张样本

- 负责人：`/root/type1082_implement`，主持 `/root`；状态：R1唯一P2来源定位整改完成，重新冻结待定向复验，2026-10-19。
- 用户授权：按已确认整改方案推进样本及R1准备，样本确认前不全量。固定cid：30236、7229、29、2020、5023、4009、8151、30004、10001、13001、30338。
- 写入：本卡、`scripts/character_skills/card_page*.py`、`output/character_skills/pages/`、`work/character_skills_card_pages/`及独立新增源码快照。
- 只读：任务0、旧P3/profiles/rules/links生成器和产物、原始输入、旧审查、根交接、主持方案/进度。无依赖安装、git提交推送、全量生成或新原生研究。
- 输入：现有profiles/records/rules、links、同源decoded/APK、cid30236的101基线。Extra/PASSIVE按links逐引用原始record，不经复用rec_key恢复等级。
- 结构：卡头/基础信息/固定13组/日文原文/行内数值及未知原因/独立数值与关联证据/折叠来源；denju_lb并入传授。
- 政策：A为实际数值或公式，原文有效数字优先建立A清单；B须新增有据机制，翻译不计；C未知。FORWARD仅关联目标已有规则，句内归属未证不提升。保留N_all/E/N_num和old→new映射。
- 已生成11×HTML/card.json、pilot_report.md/.json、72个不同实际行抽样HTML/JSONL、old→new映射与validation.json。主入口 `output/character_skills/pages/pilot_report.md`。
- 实测：N_all/E/N_num=387/0/387，A185（47.8%）/B0/C202，原文A165，A部分填充181。链目标关联96（有已有规则53），链新增A/行内数值0；未把4496当新增A。
- 每卡 N/A/B/C：30236=58/46/0/12；7229=108/59/0/49；29=2/2/0/0；2020=1/1/0/0；5023=1/1/0/0；4009=4/0/0/4；8151=14/7/0/7；30004=81/35/0/46；10001=52/8/0/44；13001=4/0/0/4；30338=62/26/0/36。
- 分母变化：旧384＋3行Leader.sympathy_text＋2次真实重复出现−2条SA内部标签＝387；内部标签留来源占位，不计E。Extra/PASSIVE逐引用分档原文、传授突破5档完整保留。
- 30236基线101项全部保留定位：92项入实际描述行，9项入条件档位/配置头部，不冒充101条新描述。沙漠pattern43023600无sinfo，依据原condition＋实际子记录链展示7项条件数值；保留基线原description ID，未造沙漠正文。Class自身/全体依据原target和65000001/65000002真实引用分开。
- 实施检查25/25：11页13组、HTML/JSON/日文逐行一致、分档原文、六基础位置、缺失/null/零、HP阈值/1st/6发、101归属、固定防御/Chain公式、内部标签、72抽样与分母对账。没有189/A–P/旧native重跑。
- 运行：`& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page.py --input-root . --output output/character_skills/pages --pilot`；检查入口 `card_page_check.py --input-root . --output output/character_skills/pages`。
- 新源码与本卡：`work/character_skills_card_pages/snapshots/20261019-pilot-r1-frozen/`，含5项源文件hash与正式输出冻结hash；依赖旧公共模块/规则证据目录，未声称新环境安装或完整发行包。原`20261019-pilot-r1/`为收据脚本属性调用笔误造成的未完成快照，保留不覆盖，不能当正式冻结清单。
- 视觉：实施者未声称浏览器视觉验收。主持已实际浏览7229首稿并反馈C文案与SA标签，已定向修正。网站9张对照及外部差异由主持另存；8151本地缺卡、13001无网站匹配不强配。
- 剩余限制：大量句内数值归属未知；原文A并不确认参数对应。候选不升确认，无新增通用模板；B0，不靠翻译凑数。部分链门控及账号装载未知，旧P3/任务0全部只读。
- 下一步：停写，等待主持转交具体R1问题；不自行全量或继续扩值。

## R1 来源定位定向整改

- 问题来源：`output/character_skills/review/r1_20261019_card_pages/source_gaps.json`。首轮其余实质审读无数值/方向/分母/B虚增问题；本轮只修唯一P2，不重跑旧研究。
- 原因：新页沿用了旧common的fallback来源；CACHE bosspattern/bossskill被写成不存在的分表文件，Class没有json_pointer。旧common保持只读。
- 修复：仅`card_page_data.py`的`Inputs.precise_source`补真实CACHE表映射，record_evidence子引用同样经过此函数。Boss定位到`bossinfo.data5.json.raw#/bossinfo/bosspattern|bossskill/<index>`；Class定位到`jobabilityinfo.data5.json.raw#/job_ability/<index>`。original_file为输入根下真实decoded文件路径。
- 唯一性：Boss按真实ID及完整原始record匹配；Class必须同时匹配cids和完整原始record，不取首个包含cid的行。缺文件、完全重复或record不符均保留未知，不伪造pointer。三个边界用内存夹具定向验证，不改原件。
- 已核：36个真实引用（8父pattern/25子skill/3Class），146处定位与42个唯一来源对象全部可解析；真实record与原JSON逐对象相同。row、record_evidence、old→new及HTML/JSON同步重建。
- 差量：只改变30236/30004/30338三张卡的来源对象；其余8张card.json不变。387行原文、A185/B0/C202、原文A165、全部字段值/条件/等级/101项原基线的非来源内容严格一致，没有升等级、改数值或删除未知。
- 证据：`output/character_skills/pages/source_fix_validation.json`。修前11份card.json按首稿冻结hash核对后留`work/character_skills_card_pages/r1_source_fix/before/`；新定向验证入口`card_page_source_fix.py --input-root . --output output/character_skills/pages --before work/character_skills_card_pages/r1_source_fix/before`。
- 新增增量源码/正式输出快照：`work/character_skills_card_pages/snapshots/20261019-pilot-r1-source-fix/`，只复制相对首稿冻结清单新增/变化的源文件和输出，另存当前全清单hash；原冻结目录与R1审查文件不覆盖。
- 完成后再次停写，等待主持交原R1定向复验；本实施自检不代替独立闭合结论。
