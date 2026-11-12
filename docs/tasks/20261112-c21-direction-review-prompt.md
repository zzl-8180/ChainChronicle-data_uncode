# C21第三方方向审查提示词

请将以下提示词交给独立第三方审查者。审查结论返回前，主持只登记PENDING，不写成C21全部收口。

---

请对《锁链战记》角色技能页C21做独立第三方方向审查。项目根为`E:\代码项目\锁链战记数据解包`。

先读`AGENTS.md`、`HANDOFF.md`、`docs/tasks/character-skills-progress.md`、`docs/tasks/20261112-c21-cycle-closeout.md`、`docs/tasks/20261112-c21-delivery-wording-errata.md`，再按需读C21任务卡、正式交付包、正式独立终审和当前成果。不要通读全部历史或重跑旧周期。

## 审查对象

- 当前成果：`output/character_skills/cycle_reports/C21/`。
- 900答案机器台账：同目录`answer_ledger.json`／`answer_ledger.csv`；完整前后行与答案在`report_data.json`。
- 正式交付：`output/character_skills/c21_delivery_20261111/run_record.json`及`precheck/`、`checks/`。
- 正式独立终审：`output/character_skills/review/c21_delivery_final_20261111_deepseek/`，23/23、阻断0、900项独立重导；其`REPAIR.md`记录审查入口路径修复。
- 最终清单：`final_manifest.json`与`handoff_verification.json`；10个登记文件不含manifest自身和handoff，handoff只单向登记manifest哈希。

## 只允许写入

`output/character_skills/review/direction_c21_20261112_thirdparty/`。

至少交付`REPORT.md`、`verdict.json`、`evidence.json`、`answer_ledger.json`和可重跑`run_review.py`。入口支持`--root . --out <审查目录>`，实际执行并记录命令和退出码；避免依赖固定parents层数定位项目根。保留实际命令、独立重算与只读引用的分别计数。

不得修改正式pages、rules、effect_ledger、C21生成器、候选、正式交付包、当前成果、manifest或旧审查；不得运行正式全库生成、resume、隔离卡页生成、清理、Git、发布、新缓存、新原生或实机。若未实际启动浏览器，浏览器视觉／交互必须写UNTESTED，静态HTML解析不得冒充视觉验收。

## 必查范围与风险

1. **真实规模**：518卡900行900效果900答案；P1 special 766（CACHE 259／APK 507），P2 denju 134（全部CACHE，直接133＋CID30304条件镜像1）。Y.G.答案／效果11，非Y.G.889；严格直接899＋条件镜像1。900答案不等于900行或518卡全部解释完成。
2. **分源与来源身份**：CACHE与APK不混源，普通skilllist与Boss/bossskill命名空间不混用，记录ID不当下标。独立重建原始表ID→数组位置索引，核对bossskill raw、字段、JSON指针、raw_record_sha256、类型、规则状态、单位、方向和float32。历史`original_file`逻辑字符串与统一`read_path`实际读取分开。
3. **归属与条件**：逐行核完整父集合、`current_parent`（当前描述来源父）、`selected`（本答案分支父）、children、原始条件、fragment span和effect_binding。P2父集合必须从denju记录重导，展示不得再标成charainfo顺序。
4. **伤害形态**：多段次数与`skillparam6`一致；大／中伤害使用单发型；type74只解释首次直接范围伤害的`skillparam5`，不把后续反響借到`skillparam1`。数值是处理器收到的局部伤害输入，不是最终扣血、保证命中或运行时装载。
5. **CID30304**：denju `patternid0=43030403`→bossskill 43030400，type22 `/skillparam1=15`；denju全文与pattern全文不一致但首句一致，只能称首句条件镜像。默认层不得泄漏`denju.patternid`、`skillparam`、表名或指针；展开层必须保留全文差异、首句一致性、同记录既有答案、来源和推断边界。
6. **正式页面与消费**：900条展示答案与正式pages及候选逐项一致；旧答案前缀不变，仅允许已登记的`page_sha256`信息性漂移；非目标行与四张保护卡30102／20234／30236／30239不变。900个新answer_ref精确消费，旧答案的既有unmatched项不得误算为C21新未消费；第二次新增0，split_flags不新增。
7. **账本与完整度**：has_answer 21,523→22,423（+900）、unresolved 48,142→47,242（−900）、backlog 74,335→73,435（−900）；完整6,614→6,670（+56）、部分298→299（+1）、未解析8,560→8,503（−57）；A+502／C−502／整行推断+0／S4+0；Y.G.+11／非Y.G.+889。其它同句未解效果4项必须就地显示，行级拆分标志不得被900答案掩盖。
8. **正式生成与固定检查**：唯一一次jobs4全库生成，2,236卡完成，campaign_complete=true；campaign `5492e173e3fa7c918eb3a2a701d6471e4a84246927e9450cf1cd99d3bc74e010`，snapshot `5492e173-cf9451c6ff47fcfb`，rules 294键未改。核对预检48/48、verify_full 17/17、账本9/9、A7 29/29、final_diff 36/36、validate_formal 26/26，以及固定cohort 525卡1050文件逐字节一致。固定cohort不得称任意分组复现，也不得称第二次全库。
9. **展示与清单**：默认中文只给可读局部贡献和必要条件；完整日文、公式、raw、表名、字段、指针、父集合和镜像证据放展开层。核对900条答案台账、所有相对链接、详细验证42/42、10文件SHA与字节数、manifest／handoff单向哈希。浏览器UNTESTED不得改成PASS。
10. **说明勘误**：C21交付包若干历史检查名／说明残留C20“16卡／18行”，实际集合断言和独立终审均为518卡900行。读`docs/tasks/20261112-c21-delivery-wording-errata.md`，判断其是否影响可接受性；不得通过改写原始回执消除问题。
11. **审查入口修复**：正式终审首次由主持从深层review目录以`-I`运行时因固定parents层级找不到`project_layout_paths`；原审查者已改为向上查找项目根并实际退出0。区分该审查工具故障与正式数值／生成结果，核修复后23/23及原失败证据保留。
12. **容量与边界**：retention 12/12，reserved_bytes 8,032,729,057 B，未放宽12 run／8 GiB限额，没有第二次全库生成空间。关联推断、`binding=inferred`、`runtime_verified=False`；未做新原生、实机或第三方浏览器验收。

## 裁决格式

`verdict`使用`PASS_WITH_EXPLICIT_SCOPE_LIMITS`或`REQUEST_CHANGES`，给出`blocking`数组、`blocking_count`、`checks_total/checks_passed`、独立重算数、只读引用数、未测项及精确证据。发现来源、条件、单位、对象、归属、消费、展示、清单或计数错误时，给出具体row／record／字段／文件位置和最小修复范围，不为凑900放行。

若`REQUEST_CHANGES`，停在findings；主持不会自动整改、重建或启动C22。若通过，也必须保留上述明确范围限制，不把静态审查写成运行时、视觉或实机验证。
