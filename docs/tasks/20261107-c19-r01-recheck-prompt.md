# 交原第三方：C19-R01 定向复核提示词

请原第三方只对 C19 方向审查的唯一阻断 **R01** 及直接影响做定向复核。不要重做整个C19，不把本次复核扩成新机制、数值或全游戏完成度审查。

## 原裁决与整改入口

1. 原裁决保持只读：`output/character_skills/review/direction_c19_20261107_thirdparty/REPORT.md`、`verdict.json`、`affected_unresolved.json`。原结论为REQUEST_CHANGES，R01涉及35行45项；第三方浏览器当时UNTESTED。
2. 整改任务卡：`docs/tasks/20261107-c19-r01-row-unresolved-rectification.md`。
3. 新成果：`output/character_skills/cycle_reports/C19_r01_20261107/`下的`index.html`、`remaining.html`、`report_data.json`、`rectification_mapping.json`、`verification_detailed.json`、`browser_verification.json`、`browser/dom_evidence.json`、`final_manifest.json`、`handoff_verification.json`。
4. 整改证据：`output/character_skills/rectification_c19_r01_row_unresolved_20261107/README.md`及`shared_generator_regression.json`。
5. 原C19成果目录`output/character_skills/cycle_reports/C19/`是历史前像，不得覆盖或要求它与新版具有相同未知披露。

## 逐项复核

1. **35行45项精确覆盖**：以原`affected_unresolved.json`为名单，逐行核对新版对应成果行。默认阅读层必须直接显示具体中文未知提示，不接受只有批次顶部`449→45`或统一免责声明。45项应有45个`details.unresolved-effect`，分属35个row_id。
2. **代表项**：20131／20512／20603均默认显示“同句暴击率增幅仍未确定”，展开保留完整effect_id及`param5=None`缺口证据，不得补零；5264默认显示“同句攻击间隔仍未确定”，并保留词表外、无已确认映射的账本证据。
3. **证据来源**：每个未知详情应有effect_id、原句片段、span、unresolved状态、gap、blocker、candidate_sources、next_step及`backlog.json`的backlog_id；row_id与effect_id须和正式账本一致。
4. **既有答案不变**：133行407条答案的JSON对象、默认／展开HTML、来源、条件、raw、单位、推断等级及统计与原C19一致；新增语义答案0。4行既有split_flags为223／353／12238／30109，保持原样。
5. **账本与剩余量不变**：has_answer 21,505、unresolved 48,160、backlog 74,353及Y.G.分项均不变；remaining计数不变。
6. **历史与正式输入不变**：原C19 manifest仍为`afc2c436cfe289a335d3590a076f5f518d6ec7880eba64ef3025c6f2c6c16f42`；原第三方REQUEST_CHANGES仍在。第三方记录的323个输入＋4,472个页面文件，共4,795个哈希在本整改后变化0。
7. **机器与链接**：新版`verification_detailed.json`为26/26 PASS，坏链接0，本地链接143；整改映射为35行45项。新manifest登记14个文件，单向manifest SHA-256为`4197992299c03a27c391e37c3e8fd99cb92d1682ab8d5b32e895b2152b191f68`，请实际重算，不只引用。
8. **R02／R03措辞**：617.3秒仅是`run_formal.py`总运行时间，正式生成133.24秒，不称整个周期；旧独立终审原文不覆盖。12个同号记录原始表示差异＝11个实质值差＋1个仅float32表示差，后者为CID20713／skillid42071301；CACHE答案不改。

## 浏览器证据边界

- 主持实际完成：首张1280×900桌面总览截图并查看；20131／20512／5264桌面坐标点击展开及证据读取；20603只读DOM证据；320×720下20512展开状态、表格横向滚动最大值附近及页面无横向溢出；剩余量与返回链接实际坐标点击。
- 多次自动定位点击、滚轮及后续截图发生运行时超时。代表行、窄屏和剩余量视觉截图未完成；完整控制台、键盘完整导航、角色／审查链接点击未执行。主持DOM／坐标操作不是独立视觉验收。
- 若你未实际执行浏览器，必须继续写第三方浏览器UNTESTED；不要把主持回执当成你的视觉通过，也不要把未测截图写成产品缺陷。

## 写入与停止

- 只写你的新目录：`output/character_skills/review/direction_c19_20261107_thirdparty_r01_recheck/`，至少包含`REPORT.md`、`verdict.json`和实际证据／命令。
- 不修改新版或原C19成果、正式pages／ledger／rules、共享生成器、交付包、原审查及历史独立终审。
- 不运行正式全库生成、`run_formal.py`、resume、隔离卡页生成；不要原地运行会覆盖新版验证回执的脚本。需要重算时在自己的审查目录独立读取、独立输出。
- 不启动C20、其他机制族、新原生、实机、新缓存、清理、Git提交／推送或发布。
- 请明确R01是否CLOSED、阻断数、实际核查行数／effect数、407答案是否保持、manifest实算结果及未测项。只有你可以关闭原R01；主持当前状态仅为“R01整改完成，待原第三方定向复核”。
