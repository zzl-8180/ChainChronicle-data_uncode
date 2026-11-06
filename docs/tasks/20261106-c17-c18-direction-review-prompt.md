# 交第三方：C17＋C18 联合周期方向审查提示词

请对《锁链战记》角色技能主线 **C17与C18** 做独立、只读的联合方向审查。重点检查两周期交付方向、成果页忠实度、默认中文、来源展示、版本与计数口径、保护边界、审查限制和停止点，不必重新开发解算器。**两周期必须分别核账，不得把C18后的当前状态当作C17历史状态。**

## 读取入口

1. `AGENTS.md`、`HANDOFF.md`、`docs/角色技能完整解读实施方案.md`、`docs/tasks/character-skills-progress.md`当前块。
2. C17：`docs/tasks/20261106-c17-cycle.md`、`20261106-c17-p1-1095-attack-partial.md`、`20261106-c17-delivery-package.md`、`20261106-c17-cycle-closeout.md`。
3. C18：`docs/tasks/20261106-c18-cycle.md`、`20261106-c18-p1-1095-attack-partial.md`、`20261106-c18-delivery-package.md`、`20261106-c18-cycle-closeout.md`。
4. C17交付：`output/character_skills/c17_delivery_20261106/README.md`、`run_record.json`、`run_records/formal_build_summary.json`、`precheck/check_report.json`、`checks/final_diff.json`、`checks/validate_formal.json`。
5. C18交付：`output/character_skills/c18_delivery_20261106/README.md`、`run_record.json`、`run_records/formal_build_summary.json`、`precheck/check_report.json`、`precheck/expected_ledger_delta.json`、`precheck/absolute_diff_scope.json`、`checks/final_diff.json`、`checks/validate_formal.json`。
6. 独立审查：
   - C17候选 `output/character_skills/review/c17_p1_1095_attack_partial_20261106_deepseek/`
   - C17正式终审 `output/character_skills/review/c17_delivery_final_20261106_deepseek/`
   - C18候选 `output/character_skills/review/c18_p1_1095_attack_partial_20261106_deepseek/`
   - C18正式终审 `output/character_skills/review/c18_delivery_final_20261106_deepseek/`
7. 成果：`output/character_skills/cycle_reports/C17/`与`output/character_skills/cycle_reports/C18/`各自的`index.html`、`remaining.html`、`report_data.json`、`verification.json`、`verification_detailed.json`、`browser_verification.json`、`final_manifest.json`、`handoff_verification.json`。

## A. 分开核对版本与生成历史

### C17历史快照

- campaign `dc38910014d6f4629ec13e2afc6d46e8ea2dbdc6568c48c8169fad15518417b2`；snapshot `dc389100-cf9451c6ff47fcfb`；rules 294键。
- 正式全库生成恰1次、jobs 4、96.03秒；`formal_build_summary`的`executed=true/count=1`与resume后`run_record`的`executed=false/reused_after_build=true/count=1`一致，不是第二次生成。
- C17 manifest SHA-256 `2296ebb165207b14eba42776f108c899310a128e0cec79a6c1bffc22e08c8a6d`，文件与哈希不得因C18改变。

### C18新快照

- C18前像必须正是上述C17后状态；C18 campaign `01c05f78bd54263efd40991b96e3aed2a421cce3e0845e5e49bb4fcd03d114c3`，snapshot `01c05f78-cf9451c6ff47fcfb`，rules 294键。
- 正式全库生成恰1次、jobs 4、97.55秒；build_summary与run_record均`executed=true/reused_after_build=false/count=1`，**未使用resume、无aborted**。
- C18 manifest SHA-256 `e3afcaf8e46de230d52904f3d565c4f7808bc276de49030197569fd38b107d94`。
- 不要运行C17或C18原包正式脚本/resume；C18后共享`card_page_data.py`已合法前进，不能要求其仍等于C17历史接线哈希。

## B. 分开核对数值、来源与账本

### C17：3卡3行3答案，全部Y.G.

- 30110／30237／30333分别提高42.5%／37.5%／35%，raw 1.425／1.375／1.35，载体43011001／43023701／43033301，指针/skilllist/5943、6419、7455。
- C17账本has_answer 21,096（Y.G. 5,324）、unresolved 48,569（Y.G. 5,230）、backlog 74,762（Y.G. 8,511）；完整6,514、未解析8,694；相对C16 +3/-3、完整+3、未解析−3，其余0。
- C17绝对变化3目标∪9漂移＝12卡，其余2,224卡不变；终审132/132＝113项独立重算＋19项只读引用，N01–N08保留。

### C18：2卡2行2答案，全部非Y.G.

- 6341 raw 1.225→**提高22.5%**，载体40634101、`/skilllist/1619`；20333 raw 1.375→**提高37.5%**，载体42033301、`/skilllist/3214`。均sub[0]，APK同号0条；20333与C17 30237同raw但载体/父不同，不复制。
- C18账本has_answer 21,098（Y.G. 5,324）、unresolved 48,567（Y.G. 5,230）、backlog 74,760（**Y.G.仍为8,511**）；完整6,516、未解析8,692；相对C17 +2/-2、完整+2、未解析−2，Y.G.效果／A/C/整行推断/S4增量0，非Y.G.+2。
- C18绝对变化2目标∪9漂移＝11卡，其余2,225卡不变；终审41/41＝29项独立重算＋12项只读引用。
- 默认中文应可读，关联为推断；`numeric=确认`仅指既有规则体与原值，不能升格为归属确认或实机验证。额外param6（C17 2.5/2.375；C18 2.5/2.25）与句外条件强化不并入。

## C. 必须核查的边界与展示

1. **账本与剩余页**：C17 remaining为48,569／Y.G. 5,230、backlog 74,762；C18 remaining为48,567／Y.G. 5,230、backlog 74,760／Y.G. 8,511，拆分均26,193。不要拿C18后的当前账本要求等于C17绝对值。
2. **成果页**：C17应3个`tr[data-cid]`／3个答案details、20/20；C18应2个／2个、20/20；本地链接目标存在，最终清单均11文件及单向哈希通过。
3. **漂移与保护**：两周期均各自由扫描重推9张既有指纹漂移卡，不计收益；指纹指各自构建时输入页哈希，不要求两周期具体哈希值相同。保护卡30236／30239／30102／20234不破，C17三卡不得误归C18。
4. **C18候选N01–N05**：answers_total为序列化长度、run_record基线空值、父层／跨槽1095负例、候选K12同解析器、未使用常量。预检与终审以独立重导和当前metrics为准，父层／跨槽机制不在本批扩展。
5. **完整度与旧展示**：C18两行完整不等于语义确认（仍row_class=C／row_evidence=未知）；C17 N07旧unknown_reasons遗留不写成已修复，展开层conditions能力编号不放到默认player_text。
6. **Y.G. backlog笔误**：C18 HOST-NOTE所指8,509已在交接收口修正为8,511；metrics与独立重算应支持Y.G.拆分3,281＋未解5,230＝8,511。
7. **浏览器主体**：C17主持覆盖默认三摘要、首条DOM展开、剩余量、320px滚动与往返导航，窄屏截图超时、桌面未尝试；C18主持覆盖默认两摘要、6341 DOM展开、剩余量、320px滚动与往返导航，两种截图均未尝试。完整控制台与角色／审查链接未测。若你未实际执行浏览器，必须写第三方浏览器UNTESTED，不得把主持DOM回执冒充你的视觉验收。
8. **隔离与收益**：C17为16卡32文件，C18为18卡36文件；均不是第二次全库或任意分组复现。receipt与根入口重签不计数值收益。

## 写入与停止边界

- 只写你自己的新目录：`output/character_skills/review/direction_c17_c18_20261106_thirdparty/`，至少包含`REPORT.md`、`verdict.json`及实际检查证据与命令。
- 不修改正式pages／ledger／rules／入口页、两周期候选包、交付包、成果目录、既有独立审查或历史整改包。
- 不运行正式全库生成、`run_formal.py`（含resume）、隔离卡页生成；不要原地重跑会覆盖交付回执或历史审查证据的脚本。需要重算时在自己的审查目录实现只读读取、独立输出。
- 不执行清理、Git提交／推送、发布，不启动C19或其他机制族，不做新原生、实机或新缓存。
- 若发现问题，按R01／R02…给出严重度、是否阻断、所属周期、精确文件／行／答案、实际证据和最小整改范围；不要把未测项伪装成产品缺陷，也不要以旧PASS替代当前核查。

请在`verdict.json`明确给出`verdict`、`blocking_findings`、C17／C18各自实际核查行数与答案数、未测项。结论可用`PASS_WITH_EXPLICIT_SCOPE_LIMITS`或`REQUEST_CHANGES`；最终报告请区分“独立重算／实际浏览器／仅阅读证据／判断性结论”。你的PASS也不应扩大成实机、完整原生、任意分组复现或全游戏完成度结论。
