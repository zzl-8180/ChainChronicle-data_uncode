# C19 周期收口记录（1095与type8同族扩大）

- 日期：2026-11-07；主持：`new-provider/kimi-k3-1-pro-261024`。
- 状态：**原第三方R01定向复核通过，R01 CLOSED，阻断0；C19清理与主提交`e2e864624b407682a6c2ab6798bea37ff6ea12bb`已推送，最终文档回执随本提交同步，不启动C20或发布。**
- 周期／批次／交付任务卡：`20261107-c19-cycle.md`／`20261107-c19-p1-1095-attack-families.md`／`20261107-c19-p2-type8-basic-attack.md`／`20261107-c19-delivery-package.md`。

## 1. 正式范围与数值

共133卡、133行、407答案／407效果净增：

- P1 CACHE 1095：130卡130行404答案；攻击130、移速74、受伤量减伤71、暴击率90、暴伤39。直接父1095 71、唯一sub 59（sub[1] 7）。
- P2 APK type8：1063提高35%、1238提高75%、12220提高10%，复用`skilllist|8|/param1`与既有quantity_kind回退，不新增映射。

param3是受伤量倍率不是固定防御，param5是百分点，param6是1.5基准系数增量；param4/7/8只登记不解释，20131／20512／20603缺param5不补零，47个非中性未主张槽不并入。130个1095目标行仍有45个其他effect未解，4行既有split_flags未新增。关联保持推断，numeric确认仅指既有规则体与原值，runtime_verified=False，未实机。

## 2. 版本、生成与正式账本

- campaign：`99bee2a166e5ec5f9c03ac97b555d4ada2f6f30d1535258add16bc64c7227c66`
- snapshot：`99bee2a1-cf9451c6ff47fcfb`；rules 294键未改。
- 正式全库生成**仅1次**、jobs 4、133.24秒，2,236卡／四cohort完成、失败0，未使用resume。`run_formal.py`总运行617.3秒不是整个C19周期耗时。
- has_answer 21,098→**21,505**（Y.G. 5,324→**5,376**）；unresolved 48,567→**48,160**（Y.G. 5,230→**5,178**）；backlog 74,760→**74,353**（Y.G. 8,511→**8,459**）。
- 完整6,516→**6,611**（+95）、部分264→**298**（+34）、未解析8,692→**8,563**（−129）、拆分26,193不变；A/C/整行推断/S4均0。identified 69,964与justified_na 299不变。
- 绝对变化并集为**139卡**：133目标∪9既有漂移，交集3＝7250／30107／30220，**不是142**；其余**2,097卡**逐字节不变。9张漂移卡仅重算既有`binding.g1_b1_binding.page_sha256`，不计收益，指构建时输入页哈希。
- 保护卡30236／30239／30102／20234不变；C16／C17／C18旧答案不误归C19。
- 正式生成后曾RETAINED **4/12**、reserved_bytes **2,645,358,782**；后续清理与预约释放见§7，限额未放宽。

## 3. 验证与独立审查

| 环节 | 实际结果 |
|---|---|
| 候选实施自检 | P1 22/22、P2 21/21；404＋3答案均由真实Inputs与`analyze_row`消费 |
| 候选独立审查 | DeepSeek Pro GA high，PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0、13/13（9独立重算＋4只读引用） |
| 合并预检 | 74/74；四cohort启用／停用扫描，实测冻结407效果、完整+95／部分+34／未解析−129及9张漂移卡 |
| 正式固定检查 | final_diff 36/36、verify_full 17/17、账本9/9、A7 29/29 |
| 只读正式验证 | 32/32；隔离24卡48文件逐字节一致，不是第二次全库或任意分组复现 |
| 正式独立终审 | DeepSeek Pro GA high，PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0、47/47（28独立重算＋19只读引用） |
| 成果页详细验证 | 21/21、133个`tr[data-cid]`、407个答案details、坏链接0；最终清单11文件及单向哈希通过 |

正式终审：`output/character_skills/review/c19_delivery_final_20261107_deepseek/REPORT.md`。其独立重算覆盖407条来源、真实账本消费、全库字节差异、receipt、隔离样本和接线可逆；预检／final_diff／validate／verify_full等19项为只读引用，未冒充全部重跑。

## 4. 非阻断问题与限制

- **F1**：交付README曾未同步`run_prechecks.py`哈希，已更新为当前文件`10b5d137472c5685c60ae1b1c2f0e1d6fb99e6a3d0f6eaa0fec6119b7c23463c`；正式脚本和检查器一致，仅文档问题。
- **F2**：133目标与9漂移有3卡交集（7250／30107／30220），并集为139；已在README和成果清单明确，不写成142。
- **N01–N05**：关联推断；45个其他effect未解；4行既有split_flags未新增；12个APK同号记录存在原始表示差异（11个实质值差＋1个仅float32表示差，后者为CID20713／42071301）只取CACHE；type8走既有quantity_kind回退。
- 预检C8曾把30225既有指纹漂移误判为负例，已按行、答案索引、`structure_scope`和停用C19对照修正，未改变正式答案。
- 工作流一次静态检查命令格式错误和一次终审模板字符串错误均在执行前修正并复跑，不是正式产品失败；交付脚本静态F组最终11/11通过。

## 5. 成果与主持浏览器边界

- 成果页：`output/character_skills/cycle_reports/C19/index.html`
- 剩余量：`remaining.html`；机器数据：`report_data.json`
- 详细验证：`verification_detailed.json`；浏览器回执：`browser_verification.json`
- 最终清单：`final_manifest.json`，SHA-256 `afc2c436cfe289a335d3590a076f5f518d6ec7880eba64ef3025c6f2c6c16f42`
- 单向交接：`handoff_verification.json`
- 最终交接只读复核：HANDOFF、STATUS、进度看板、交付README、本记录与送审提示词共620个本地Markdown链接目标存在；重算`final_manifest.json`的11个登记文件，大小与SHA-256全部一致，`handoff_verification.json`单向记录的manifest哈希`afc2c436cfe289a335d3590a076f5f518d6ec7880eba64ef3025c6f2c6c16f42`一致；C17历史manifest仍为`2296ebb165207b14eba42776f108c899310a128e0cec79a6c1bffc22e08c8a6d`，C18仍为`e3afcaf8e46de230d52904f3d565c4f7808bc276de49030197569fd38b107d94`，未被C19改写。

主持浏览器实际完成：133行407答案详情计数、220答案DOM展开及来源身份、剩余量数据、320px表格247／720px与横向滚动0→160、成果页↔剩余量往返导航。8768预览曾404，更换8769后正常，未当作产品缺陷。截图、完整控制台和角色／审查链接点击未测；第三方浏览器与实机均UNTESTED。

## 6. 第三方审查、R01整改与停止点

原送审提示词：`docs/tasks/20261107-c19-direction-review-prompt.md`。第三方方向审查已完成，实际核查133卡133行407答案，数值、来源、账本增量、139卡并集及保护边界通过；裁决为REQUEST_CHANGES，唯一阻断R01是35行45个同句未解效果未在成果行就地披露，R02／R03为非阻断措辞问题。第三方浏览器UNTESTED，原报告及裁决保留在`output/character_skills/review/direction_c19_20261107_thirdparty/`。

已按用户授权完成最小展示整改：新版`output/character_skills/cycle_reports/C19_r01_20261107/`在35行默认层逐项显示45个未知效果并保留正式账本证据；407条答案、来源、统计和4行既有split_flags不变。详细验证26/26、坏链接0、第三方记录的4,795个文件变化0；新manifest为`4197992299c03a27c391e37c3e8fd99cb92d1682ab8d5b32e895b2152b191f68`。整改证据见`output/character_skills/rectification_c19_r01_row_unresolved_20261107/README.md`，原第三方定向复核提示词为`docs/tasks/20261107-c19-r01-recheck-prompt.md`。

R02继续明确617.3秒仅为`run_formal.py`总运行时间、正式生成133.24秒，不代表整个C19周期；R03按11个实质值差＋1个float32表示差澄清。原C19目录、旧独立终审和原REQUEST_CHANGES不改。

原第三方R01定向复核已完成：[REPORT](../../output/character_skills/review/direction_c19_20261107_thirdparty_r01_recheck/REPORT.md)／[verdict](../../output/character_skills/review/direction_c19_20261107_thirdparty_r01_recheck/verdict.json)／[evidence](../../output/character_skills/review/direction_c19_20261107_thirdparty_r01_recheck/evidence.json)。裁决PASS_WITH_EXPLICIT_SCOPE_LIMITS，R01=CLOSED、阻断0，25/25通过；实际复核35行45项，133行407条既有答案JSON对象和HTML块不变，4,795个记录文件变化0，新版14个清单文件实算通过。第三方浏览器仍UNTESTED，本次不是独立视觉、实机或整个C19重新验收；407条数值成果沿用原第三方已完成的核查。

新版`C19_r01_20261107`成果、送审时“待复核”记录及已核验manifest保持不变，由本收口记录链接新裁决承接。关联推断、45个效果仍未解、4行既有split_flags、未实机及第三方浏览器UNTESTED继续保留。**原第三方R01定向复核通过，R01 CLOSED，阻断0；C19在明确范围限制下收口，等待用户下一步安排。**

## 7. 清理与Git收尾

用户随后明确授权清理和Git推送。C19的4个retained run仅清理transaction payload：白名单4,472件／2,634,793,682 B，其中4,194件有同哈希live survivor；278个不同内容、278个唯一内容已归档并恢复8件样本。B类派生清理0，4,494个run／transaction元数据和30个指定保护文件不变，未列内容全部保留。

清理journal 4,472项、失败0；RETAINED 4/12→0/12，reserved_bytes 2,645,358,782→0，实测可用空间+2,585,399,296 B。postcheck与删除后verify_full 17/17通过，campaign及正式pages／ledger／rules未改。回执：`output/storage_retention/cycle_closeout_c19_20261107/README.md`；任务卡：`docs/tasks/20261107-c19-closeout-cleanup-git.md`。

Git仅显式暂存本周期生产模块、共享接线与成果生成器、任务文档、清理脚本和当前交接，不纳入其他对话改动或output大型产物。主提交`e2e864624b407682a6c2ab6798bea37ff6ea12bb`已推送，`origin/main`已核对一致；最终文档回执随本提交同步，Git证据见`output/storage_retention/cycle_closeout_c19_20261107/git_commit_manifest.json`。不启动C20或发布。

## 8. 可复用经验

1. **公式复用不等于归属放行**：同一句式仍须证明真实引用、句界和逐效果对应；跨槽、跨层、句外强化及已有答案行不得借值。407个局部答案不等于整卡解释完成。
2. **同族扩大用共享实现**：直接父与唯一sub按真实下标解引用，通用解析器取代逐卡模板；确定性脚本负责扫描和计数，模型负责实现与独立语义审查，审查从原记录重导。
3. **已解与未解必须同句可见**：汇总`449→45`不能替代35行45项的默认中文提示；effect_id和正式backlog证据随提示保留，展示整改不改答案，也不重建正式卡页。
4. **计数与口径分开**：绝对变化133∪9应去重为139；`page_sha256`漂移不计收益。R02区分脚本总耗时与正式生成耗时，均不冒充全周期；R03区分11个实质值差与1个float32表示差。
5. **收口保留完整证据链**：候选与正式独审、第三方原裁决、整改复核、成果manifest和清理journal分别承担不同结论。清理只处理有live或归档survivor的白名单payload，元数据与未列内容保留；Git只显式纳入本任务文件。
