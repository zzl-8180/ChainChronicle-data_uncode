# 第三方复审提示词：C19 Web R01

请独立复审角色技能阅读页针对初审REQUEST_CHANGES的R01修复。不要把实施方内部PASS或下面的摘要视作裁决；不要只读说明文档。请核对真实生成器、全库生产输出及浏览器，最终自行给出PASS / REQUEST_CHANGES及具体反例。

项目根：`E:/代码项目/锁链战记数据解包`。先读AGENTS.md、HANDOFF.md、`docs/tasks/20261107-reader-c19-r01-fix.md`。

## 输入和边界

- 原独审只读：`output/character_skills/review/reader_c19_thirdparty_20261107/REPORT.md`、verdict.json、evidence.json、work/run01/blocker_reproduction.json、browser_acceptance.json。
- 新送审清单：`output/character_skills/review/reader_c19_r01_prepared_20261107/manifest.json`及manifest.sha256；source/和documents/是冻结副本。先验证清单，不只依赖当前脚本路径。
- 被审页面：`output/character_skills/reader_full_20261106/`；浏览器 `http://127.0.0.1:8768/reader_full_20261106/`。
- R01内部证据：上述reader的`audit/c19_r01_fix_20261107/`，先读README.md、change_manifest.json。
- 整改前C19完整备份：`output/character_skills/reader_c19_before_r01_20261107/`；更早C18：`reader_c18_before_c19_20261107/`，都只读。
- 主线pages/profiles/effect_ledger、2240个mainlineGuard文件、latest、原独审和所有冻结材料只读。不启动C20或新主线研究，不修复生产内容。
- 输出新目录：`output/character_skills/review/reader_c19_r01_thirdparty_20261107/`；若已存在，另用不冲突目录，禁止覆盖历史结论。重跑放自身work或独立reader副本。

## 必须独立判断

1. B01：CID30207 pattern0 f0/f1，CACHE:43020701/02/03是否实际进入生产分支表，分别覆盖预测扣费后0–2/0–4/0–6颗；完整skillid执行槽与43020700相同才允许复用绑定值。检查伤害15倍及六项增益/持续时间，count=1为三个15倍父合计300/500；不得只修文本。全库反向覆盖394个resolvedCohortParents，各父有值或可信排除理由。
2. B02：全部883个selectionResolved反向检查，不只474项。六原反例：353pattern0f3=1.25初始；30257pattern1f3=1.25非高地；30236pattern1f2攻击60%×C/固定减伤0.3×C非沙漠（含夜间）；30310pattern0/1f0=1.5/1.75当前选档。条件直接接到数值/分支，不能只在折叠来源。保留实际原显示颜色：353/30257金、30236两项绿、30310两项紫。只有353属于先前474升金。
3. B03：30310-denju-denju-denju_denju_id____cid-lvorder0-f0，type64 skillparam1=1.5必须归“回复”，不可归解除异常。检查生成器局部span/snippet、inline与denju比较路径、未解提示；解除异常仍未知。全面复核118处标签变动（106行55卡）是否全部有局部证据，未借标签修复改变答案。
4. N01：旧C18旁注戳保留但有1774追加/563承载行/396卡的当前适配证明；sync能发现缺件、运行或输入哈希变化，不能把base same当语义一致。
5. N02：封存后篡改任意stage内容或验证回执/缺件/新增文件应拒绝；成功回执只在切换成功后写；rename或回执失败能回滚。独立隔离负向复现，不触碰正式live。实施方16案例只作线索。
6. N03：新验证receiptSHA256必须绑定最终96dc4309…完整字节，不覆盖旧错误回执；核对seal及发布路径迁移证明。
7. N04：10210传授值按HP高→低，保留不同HP条件的相同数值；只去重值/颜色/条件全同项。N05：596张仅角色资料必杀与传授同文的卡有跨组提示且不丢记录类型。N06：15个旧基础显示升金（14行）单列且属于先前474，R01零新升色。
8. 保持133/407/45、35404旧答案、9卡16指纹、760→474/286、2222评估与2240主线保护哈希。对比原值、字段、对象、单位、条件和颜色，别只比总数。

不要重提已被原独审驳回的过度指控：同值跨多段条件本身合理；无card.png用头像/字母；未绑定raw不等于已交付答案；1059不在当前快照；20211全角空格不是漏译。若有新证据，请明确与旧裁决的区别。

## 重跑入口（所有有输出的命令只对隔离副本运行）

在项目根用PowerShell；`$reviewReader`指你复制的reader目录，保留相邻pages/art关系或另开HTTP服务；`$reviewAudit='audit/c19_r01_fix_20261107'`。不要直接在冻结live重跑写回执的验证器。

```powershell
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_c19.py --output $reviewReader --baseline output/character_skills/reader_c18_before_c19_20261107 --audit-dir $reviewAudit --label-review "$reviewReader/$reviewAudit/effect_label_validation.json"
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_full.py --output $reviewReader
node scripts/skill_reader_preview/verify_confidence.js $reviewReader "$reviewAudit/confidence_validation.json"
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_condition_closeout.py --output $reviewReader --audit-dir $reviewAudit
node scripts/skill_reader_preview/verify_branch_wiring.js --output $reviewReader --receipt "$reviewReader/$reviewAudit/condition_closeout_receipt.json" --report "$reviewReader/$reviewAudit/branch_wiring_validation.json"
node scripts/skill_reader_preview/verify_r01_production.js $reviewReader --output "$reviewReader/$reviewAudit/production"
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_effect_labels.py --reader $reviewReader --baseline output/character_skills/reader_c19_before_r01_20261107 --output "$reviewReader/$reviewAudit"
```

注意重跑会更新验证回执，从而使复制的旧stage seal失效，这是预期。对正式版本执行只读`sync_status.py --check --audit-dir audit/c19_r01_fix_20261107`即可检查原封存；对重跑副本应使用自己的新audit/封存并说明差别，不为通过而删改已交付封存。

需要从生产器重新生成时：复制整改前C19到新隔离输出，`build.py --data-only --semantic-migration <副本>/audit/c19_closeout_20261107/semantic_migration.json --output <副本>`，复制最终condition_closeout_receipt到新audit，`node review_confidence.js --output <副本> --audit-dir <新audit>`，再`build.py --frontend-only --output <副本>`。先核实脚本参数及所有写入落在自己的副本，勿重跑A—E或主线解析。label验证以整改前C19为baseline，C19守恒验证以C18为baseline，二者不能混用。

发布适配与封存源文件：revalidate_sidecars.py、seal_reader.py、publish_reader.py；参数和16项隔离夹具在reader新audit/integrity/。复制夹具到自己目录并设新run目录，原夹具失败诊断不得覆盖。实机游戏逻辑、干净机器完整解包不在这轮Web复审内。

## 浏览器与交付

真实桌面和390px查看30207/353/30257/30236/30310，回归10213/350/20332/20622；额外10210传授顺序及跨组提示样本。测试中文搜索、分页、全部2236角色索引、原文/来源展开、卡面2:3及无横向溢出。截图和DOM证据与纯脚本结果分开，不声称全库逐卡视觉已验。

输出REPORT.md、verdict.json、evidence.json及可复现反例/浏览器证据。逐项说明B01—B03和N01—N06是FIXED / STILL_OPEN / UNTESTED，严重性、CID/row/effect/父ID、实际与预期、源码位置、证据路径。缺少环境或无法复验应写UNTESTED，不能照抄实施方PASS。不要自动改生产、启动研究或发布网页。
