# 整条打包支线退役独立审查

**结论：REQUEST_CHANGES**

| 审查问题 | 本审查判断 |
|---|---|
| 删除清单正确性 | **PASS_WITH_EXPLICIT_SCOPE_LIMITS（仅限当前快照）**：未发现把已核保护项、唯一恢复输入或版本前像误列 DELETE；不等于现在可以删除 |
| 最终确认包是否完备 | **REQUEST_CHANGES**：R01、R02 两项执行合同需要补齐；R03、R04 为低严重度文档修正 |
| 实际执行条件是否已经满足 | **NOT_MET**：新归档根不存在、四共享根补丁未合入、五入口负责人未接管、真实迁址和切换未验收、最终删移授权未获得，且 R01／R02 尚未关闭 |

本结论**不是**报告已经发生误删或损坏，也**不是**删除、迁移或联接切换授权。现有材料对“物理操作均为 0”的披露与本轮观察一致。

## 1. 审查范围与独立取证

已读取提示指定的方案、映射、验证、切换／回退、导航补丁和真实维护代码；对六份大型处置／survivor JSON／JSONL 清单做了全量解析，而不是只审早先 28 项。另按需核对了原保护记录、真实消费者、源码前像和历史复现材料。

本轮只进行只读检查：

- 无跟随枚举九棵旧树的 9,407 个目录，当前 6,788 个普通文件与核心集合完全一致；另有 147 项补充范围，总计 6,935 项。
- 对 6,935 个源逐项 `lstat` 并比对记录身份；检查源、现存目标祖先和 survivor 祖先的 reparse，检查硬链接、大小写冲突及目标碰撞。
- 独立流式重算 1,270 对来源／survivor、136 对 readback／payload、554 份带哈希保留项、17 份源码前像、221 份 P 小闭包保管载荷、两版技能 manifest 及其 4,476 个现存清单成员等。按路径缓存后共读取 7,556 个不同文件、1,915,041,141 逻辑字节，未复制大型 ZIP／APK。
- 实测五个 C14—C18 联接的 tag、target、父路径和关键文件读取；实测 archive 缺件返回退出码 2，且错误路径位于新归档根。
- 核对四共享根补丁基底及 `git apply --check`；未应用补丁。

未运行旧打包、清理、恢复、主线生成，未运行会覆盖原 `verification.json` 的测试，未迁移、删除、切换联接或修改业务文件。

## 2. 需要修正的问题

### R01 — P2／执行前阻断：1,270 条外部 survivor 的临前内容复核门不明确

**位置**

- `docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/junction-switch-plan.md:26`
- `docs/project-layout/20261108-packaging-runtime-ready-v1/acceptance.json:37-41`
- `docs/project-layout/20261108-packaging-full-retirement-v1/repro/verified-source-pairs.json` 条目 1—1270
- 对照：`docs/project-layout/20261108-packaging-full-retirement-v1/retained/README.md:53` 已明确 136 份 readback“临前重核两个精确文件”

**证据**

当前 1,270 对双端 SHA 全部匹配，1,406 条终态链也全部正确；但 1,270 个 survivor 全部位于完整处置集合之外，方案只写了临前复核“源与目标”或“身份”，没有明确列出删除前对**这 1,270 对双端内容身份**重新核算并生成执行回执的步骤。

这些 survivor 不是全部静态历史保管件。本轮发现 87 个 survivor 有多个硬链接，其中 81 个位于当前缓存树、6 个位于当前角色成果树。硬链接本身不使现有证明失效，本轮也未发现源与 survivor 是同一文件 ID；它说明外部存活内容可能随其他合法工作变化，不能把本次审查时的哈希当作未来执行时永远有效的证明。

**影响**

若外部 survivor 在准备后、删除前漂移，旧的双端 SHA 证据不再证明待删项仍有同字节替代者。按旧回执继续删除，可能删除已经不再有同字节 survivor 的历史副本。主线无需全局停工，但必须有逐组复核和漂移中止规则。当前尚未发生这种损失。

**最小修正**

在切换方案的“最后删旧 source 候选”之前增加独立、机器可验收的门：

1. 对 `verified-source-pairs.json` 的 1,270 行重新读取待删 source 与当前 survivor，核对长度和 SHA-256 均仍等于记录值；同时确认 survivor 未进入最终 DELETE 集合。
2. 任一对漂移时保留受影响 source 并重新审查，不得直接改用“当前有新版”作为删除理由；无漂移组才可按已批准精确清单继续。
3. 保留已有 136 对 readback／最终 payload 的双端临前复核，并把两类结果写入新的执行报告目录，不覆盖本次准备回执。
4. 将并发写入时的中止粒度写清；不要求主持主线全局停工。

### R02 — P2／执行前阻断：现有 checker 不能完成方案要求的临时入口及逐入口顺序验读

**位置**

- `docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/junction-switch-plan.md:24-25`
- `docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/check_handoff.py:106-151`
- `docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/check_handoff.py:154-183`
- `docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/README.md:38-41`

**证据**

切换方案要求：临时 junction 先验读；每次 rename 后“逐项验新正式入口后才处理下一个”。但现有 CLI：

1. 只接受 old／new target，固定遍历五个**正式**入口，没有选择单个 cycle 或临时 alias 路径的参数；只切换一个入口时，其余四个旧入口会使整体 new 检查失败。
2. `validate_payload(expected)` 确实在新 target 上检查 135 个 payload 成员、外围文件、两份恢复 manifest 和 P 源码，但逐 alias 循环在 `check_handoff.py:177-180` 只读取研究 manifest 与 P 源码，没有经每个 alias 验读 135 成员及两份恢复 manifest。
3. 文档给出的 new 模式命令说明是五个全部切换后运行，不能替代步骤 4 的临时入口检查和步骤 5 的逐次检查。

**影响**

操作者无法在两次 rename 的非原子窗口内，直接用交付的 checker 完成方案所承诺的逐入口验收，只能临时手写检查或把整体验证推迟到五个入口全部切完后。后者会扩大半切换状态的窗口。当前五个真实旧入口的 target 均正确；本项是未来执行工具的缺口，不是现有联接已损坏。

**最小修正**

增加只读的单入口验证方式，例如 `--cycle C14` 与显式 `--alias-path`／临时入口参数，并做到：

- 核单入口 reparse、mount-point tag、精确 target 和父路径；
- 经该临时或正式 alias 本身读取并核 135 个 payload 成员及 manifest、3 个外围研究文件、两份恢复 manifest、P 的 12,340 字节指定版本；
- 保持新根、祖先及嵌套路径的二次 reparse 拒绝；
- 每次 rename 后立即产生该入口回执，五入口全部完成后再运行总体验收。

若不扩 CLI，则必须提供等价、明确、可逐入口执行的只读检查命令和回执格式；不能用五入口全切换后的聚合 PASS 代替过程验收。

### R03 — P3／文档：顺序执行文档未显式承接 execution overlay

**位置**

- `docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/junction-switch-plan.md:22,28`
- `docs/project-layout/20261108-packaging-full-retirement-v1/full-disposition.jsonl:6763`
- `docs/project-layout/20261108-packaging-runtime-ready-v1/execution-overlay.json:4-23`

**证据**

冻结表第 6763 行的 `projects/distribution/README.md` 为 4,789 字节；当前实际为 5,350 字节，SHA-256 为 `be223b27dff5dded6704d36740593e40409c9657e251df6a67a142ed62551db7`。根 README 和 overlay 已正确解释这一授权导航修订，冻结表也确实未改；但切换方案只链接完整清单，没有在该执行步骤明确引用 overlay。

**影响**

只拿切换方案和冻结表执行的人会得到身份漂移中止，或误用 4,789 字节旧基线。当前是安全失败风险，不是已发生的误删。

**最小修正**

在迁址和临前身份步骤直接引用 `execution-overlay.json`，明确该行使用 5,350 字节及上述 SHA 的执行身份；保持冻结 `full-disposition.jsonl` 原字节不变。

### R04 — P3／导航：共享补丁中的交接短路径不可从项目根解析

**位置**

- `docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/shared-navigation.patch:12`

**证据**

新增 AGENTS 文本末尾写 `handoff/handoff-to-host.md`，项目根下该路径不存在；实际文件是 `docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/handoff-to-host.md`，同一补丁前文已使用完整路径。

**影响**

仅影响维护者定位交接文件，不改变删除集合或联接 target。

**最小修正**

改为完整的项目相对路径；合入共享根时仍需重读当前文件，不整文件覆盖。

## 3. 删除分类核查结果

完整 DELETE 集合可精确拆为以下四类，数量和逻辑字节相互对账：

| 类别 | 文件 | 逻辑字节 | 独立判断 |
|---|---:|---:|---|
| 早先旧包／旧代码退役 | 28 | 2,061,279,175 | 属明确能力退役；六个成功旧包不可整包重放的损失已披露，17 份源码前像真实可读 |
| 双端 SHA 证明的副本 | 1,270 | 1,421,174,242 | 本轮重新计算双端长度／SHA，0 不匹配；源与 survivor 文件 ID 不同，survivor 均在 DELETE 集合之外 |
| 放弃精确重放的旧实验生成物 | 173 | 1,446,854,634 | 均有 `retirement_loss`，没有冒充逐字节重复或可由当前版原样重建；属明确放弃旧生成载荷及精确重放 |
| 交接 readback 重复项 | 136 | 50,121,835 | 本轮重新计算双端长度／SHA，0 不匹配；最终 payload target 均为 REHOME，不在 DELETE 中 |
| **合计** | **1,607** | **4,979,429,886** | 与完整清单一致 |

### 3.1 173 份生成物没有按目录名或“有新版”简单判删

逐行理由分为：76 份解码／缓存重放载荷、60 份隔离角色 JSON／HTML、12 份媒体／对象测试载荷、10 份 APK 主表输出、8 份语义投影／账本、2 份参数视图、2 份 DWARF 展开、3 份负例夹具。

真实生产证据支持其“测试生成物”属性，例如：

- `output/share_bundle/20261025-character-tools/test_isolation.py:32-80` 显式生成解码、APK 主表、媒体及角色样本，并与声明根结果比较；不是当前主线原地输出。
- `scripts/decode_chronicle.py:68` 将 `ChronicleArchiveData.bin` 写为解码输出。
- `full-disposition.jsonl:31`、`:505`、`:1802-1803` 等代表项均明确写出永久放弃旧沙盒载荷及精确重放，不声称当前内容同字节。

各输出目录的 `decode_report.json`、`decode_progress.json`、对比报告、审查回执和负例诊断进入历史保留；本轮未见必要失败诊断被统一列入 DELETE。五份未证与根来源同字节的 2,097,152 字节 `compatible_signal_seed1.bin`，以及一份独立保留的 1,682,472 字节 `libcompatible.bak` 原生库备份，均列入移交而非 DELETE，见完整清单条目 1059、1284、1295、1500、1725、2007。

本审查**没有**声称这 173 份生成物与当前版本同字节或能够精确重建；其永久损失属于方案明确披露的退役范围。

### 3.2 源码前像与 P 保管载荷真实存在

- 旧 28 项含 19 个代码／缓存文件，其中 17 个 `.py` 有前像、2 个 `.pyc` 仅哈希记录。17 份前像逐字节匹配其来源，总计 157,899 字节；前像位于删除范围之外。
- `P_preservation.json` 前 221 项均有 `preserved_path`，本轮 221／221 重算长度／SHA 匹配。两个拟删 ZIP 是历史 `source_zip`，不能据此推断仍需保留 ZIP，也不能把 ZIP 删除说成前 221 项保管载荷丢失。
- 第 222 项位于 `P_preservation.json:1553-1555`，实际字段为 `source_existing_protected`。目标是 **12,340 字节**，SHA-256 为 `b74e4681d492fbf0f7258e138669abf91bba23c27e091f865deae428ec4e9ee2`，当前实读及最终 target 映射均正确。
- 另一个同名版本确为 **12,508 字节**、SHA-256 `5b77a83d0b4dc574379d2f918bc99776cd1f5019a2f8809953006b42a4b84cd4`，不能替代第 222 项。
- P 与 v7 当前 SHA 分别匹配 `10e5b3d7…98f` 和 `2db5e6fd…1de17`；本轮未改写它们。

## 4. 集合、终态 survivor 与文件系统检查

### 4.1 集合及目标

- 完整表 SHA-256 为 `274c6cd5602b591047ce2b2c907b4e5d9bb33ff55b190b0bb8678ec586e82ef1`，与维护代码锁定值一致。
- 28＋1,997＋4,763＋147＝6,935；四个组成部分与完整表的路径、去向、target 对齐。唯一内容差异是已由 overlay 承接的 distribution README。
- 源路径无重复、无大小写折叠冲突；迁址 target 无重复、无大小写折叠冲突、无文件／祖先类型冲突。5,317 个迁址 target 当前均不存在。
- 当前源全部存在，均为普通文件、`nlink=1`；九根内部无 reparse，检查 11,939 个源／现存目标祖先路径未见 reparse。
- `operations/history/retired-packaging/20261108` 当前不存在，`operations` 也不存在；没有真实新归档根可冒充已落地。

### 4.2 1,406 条 survivor 链

- `deleted_copy` 为 1,406 个唯一值，恰等于 1,270＋136；无额外或缺失链。
- 共有 1,079 个不同的当前／最终 survivor 路径。所有当前 survivor 仍存在，未见自身或祖先 reparse；最终路径与 DELETE 集合无大小写折叠交集。
- 1,270 条链的 survivor 均在完整处置表之外，最终仍在原外部位置；136 条 readback 链均解析到 `REHOME_BUSINESS` payload 的最终归档 target，而不是只检查其当前旧位置。
- 136 个 payload 文件（135 个成员＋manifest）及 3 个外围研究文件的当前身份均匹配；研究交接合计 139 项，未把同目录拟删 ZIP 误算为第 140 个保留项。

因此，**当前快照没有“源和最终替代者同时被删”的链错误**。R01 要求的是执行时重新证明这一状态，而不是否定本轮结果。

## 5. 其他分支与保护记录

### 5.1 当前正常生产、resume、verify、ledger

对 `scripts/character_skills`、`scripts/character_skills_pipeline` 及当前 campaign／ledger 元数据的定向静态核查，未见导入或读取待删 `scripts/release` 的现行生产依赖。唯一旧根默认输入是历史研究对账 `reconcile_mechanism_first_handoff_20261104.py:18`，已有 `--bundle` 与 `--output` 参数，维护入口打印的命令显式使用新 bundle 和独立 output，`executed=false`。

这支持“当前正常主线不因删除打包代码而直接断链”，但静态搜索不等于全仓动态无消费者证明；不能扩写为所有历史脚本、外部任务或未来调用均已动态验证。

### 5.2 历史研究与事故恢复

- 新 archive 实测缺件返回退出码 2，报错指向 `operations/history/...`，没有回退旧 `output/share_bundle`。
- 研究 payload 的冻结 verifier 以自身 `__file__` 相对定位；现有独立 readback 闭包与真实消费者代码支持迁址后运行。新 checker 的保护项验证明确不是整份历史 postcheck。
- 两版技能 manifest 分别为 1,957,351／1,960,840 字节，SHA 分别为 `9492d8c5…4045`、`424aaf23…67b2`；4,476 个现存非 manifest 成员全部能在原 manifest 中找到并重算匹配。
- 两旧技能 ZIP 在本轮前已缺失。manifest 查询只提供身份线索，不恢复 ZIP、角色 JSON、HTML 或图片；方案对此没有夸大。
- `continue_recovery_20261024.py:33-59` 的 `packages()` 确实同时需要旧 ZIP 与 manifest；旧恢复整段重放并未被伪装成仍可用。
- 参考分析当前从冻结中央目录读取 596 个名字，未见 `zipfile` 读取；不依赖拟删 `CC_analysis_data_20261016.zip` 重新打开。

### 5.3 冻结清理计划与五入口

四份 C14—C19 closeout plan 与本次 6,935 项范围的唯一逐路径交集，均为拟 `REHOME_BUSINESS` 的研究 manifest；没有其他 plan 保护文件落入 DELETE。只读新位置核验只承接该 manifest 保护项，其余保护文件仍属原体系，披露准确。

本轮独立实测五个 C14—C18 入口：

- 都是 tag `0xA0000003` 的 mount-point reparse；
- `readlink` 均为 `\\?\E:\代码项目\锁链战记数据解包\output\share_bundle`；
- 父路径未见其他 reparse，两个临时名称均尚不存在；
- 经五个入口分别读取研究 manifest、两份恢复 manifest、P 指定源码，长度／SHA 均匹配。

方案没有扩展到其他联接，也没有提出常驻 `output` 兼容联接。先保留材料移交验真、再切五入口、最后处置旧 source 的顺序正确；两次 rename 非原子、旧 target 迁空后不得盲目回指、退役 ZIP 不可作为回退恢复等限制均已明确。R02 是将这些原则落实到逐入口工具前需要补的缺口。

## 6. 数据损失、排除范围与当前准备状态

### 6.1 明确披露的能力损失

六个成功旧 ZIP 的删除意味着不能按原发行说明原样取用、整包重放或恢复；当前 pages、主表、新成果、成员清单和源码前像均不是这些 ZIP 的完整备份。旧 data ZIP、handoff ZIP、失败 A ZIP，以及 `prepare_manifest.py`、B01-D `run_pilot.py` 等固定历史重放能力的退役也有单独披露。

这些是有意的范围／能力损失，不应被后续执行报告写成“无损去重”或“仍可完整恢复旧版”。

### 6.2 排除范围

- 六份隔离 APK 副本均重新与根 `チェンクロ.apk` 双端哈希匹配；根 APK 不在 DELETE。
- 所有 DELETE 都位于声明的旧九根或独立 readback 树；没有 DELETE 落入共享 `raw/`、当前缓存、当前角色成果、当前媒体、存储 vault 或其他主线目录。
- 11 份跨任务材料均为 `RETAIN_IN_PLACE`：3 份 `docs/tasks` 历史文档、6 份独立解包复现审查 README、2 份 `output/character_skills/share_manifest_20261021` 历史清单。它们不在迁址 5,317 项内，也未被列 DELETE。

### 6.3 准备状态

- 四共享根当前字节和 SHA 与补丁基底完全一致，`git apply --check` 通过，但补丁确实未应用。
- 三个项目 README 的当前 SHA 与导航回执一致；distribution 的 5,350 字节身份与 execution overlay 一致。
- 五入口 owner 接管仍是待办，本轮未联系其他任务，也未把周期收口当作无人使用证明。
- 真实新归档根不存在，真实迁址、联接切换、删除均为 0。模拟／RAM 验证不能替代真实 NTFS 操作验收。
- 主线无需全局停工；短窗口仅限五个历史入口。用户最终精确删移确认仍是独立门槛，本审查不予代替。

## 7. 明确未核及推断边界

**已核**：当前文件集合、清单结构、哈希与终态链、当前身份漂移、指定保护记录、五入口当前身份、archive 缺件拒绝、命令构造、静态消费者和文档准备状态。

**推断**：基于真实生产代码、输出位置和保留报告，173 项属于可明确退役的旧隔离生成载荷，而非当前研究权威源。此判断不依赖其能与当前版本逐字节重建，也不证明每个旧生成值都具有同等语义。

**未核**：真实迁址后全量内容、真实临时／逐次 junction 切换、Windows rename 实际竞态、五入口 owner 当前活动、全仓所有动态消费者、旧六包整包内容重放、173 项旧载荷的逐字节再生成、完整历史 postcheck。上述未核项均不得被写成已经通过；其中 R01／R02 和实际物理门未闭合前，不应执行删除。
