# B02 当前依赖增量与运行边界

2026-11-08。相对 [旧命令矩阵](../20261107-b02-preparation-v1/command-io-matrix.json) 的只读增量；依据当前源码静态读取，未 import 或执行业务入口。下面的代码路径相对项目根，仅作定位，不是可直接运行命令。

## 新增执行链

| 入口/组 | 已核实的输入与写域 | 候选准入处置 |
|---|---|---|
| build.py full（287–302） | 自动调用 branch_candidates、branch_conditions、mana_costs、review_branch_invariance，按旧正式目录证据有无调用 partial/selection；仅旧正式 out 时调用 final5 sparse/random；最后 review_confidence。部分子进程不透传 root，也不带 -B。 | 不能只改顶层 output；逐个限定调用子集与 ROOT、输入、输出、子进程字节码写域。初始适配路线不重生成这条历史链。 |
| build.py data-only（246–286） | 写 web、README、data、翻译 audit、build receipt 后才 return；仅跳过旁注和 version_assets。 | 不视为纯数据/只读模式。 |
| build.py frontend-only（325–349） | 检查四旁注及 assessment.inputHashes 后，写 web、版本化 index、frontend receipt、README。默认 out 仍正式目录。 | 若选此模式，只能明确候选根；固定四旁注与 frontend 版本，禁止无 output 默认调用。 |
| sync_status.py | root/output 可选，默认正式 reader；读 campaign/cohort/latest、卡/回执、rules/ledger/metrics、旁注、前端、adaptation/seal。默认 stdout；--report 独占创建文件。 | 可作为未来只读预检；report 必须新独立路径。same snapshot 不等于全部语义通过，也不是发布锁。 |
| migrate_c19.py | FROZEN 固定正式 reader，首次迁移要求其仍 C18；当前已 C19。生成必填的新 receipt；build 消费 validate_receipt 后复制到固定 audit/c19_closeout_20261107。 | 不按默认值重跑首次迁移；既有迁移回执只读复用，保留精确变化约束，不用取消哈希检查代替兼容。 |
| branch_candidates / branch_conditions / mana_costs | root/output 可选，读取候选卡及正式卡、固定 APK/CACHE boss 表；写候选四旁注中的三份与各自 inventory/parent_sources。 | 旁注生成会换 snapshot；不是原样复用。初始路线固定旧旁注和证据，显式声明外部依赖。 |
| review_branch_invariance / review_partial_conditions / review_selection_order | 仅 output；固定正式 reader/native/controller/terrain/mana 证据，部分顶层执行；先写 receipt 再检查输入未变。 | 不 import；不因有 output 就视为输入隔离。初始路线不重跑。 |
| review_confidence.js | output/audit-dir；读四旁注、多份历史 receipt，扫描正式卡。 | audit-dir 不是全部写域：还写 out/data/branch_assessments.js。复用与重生成分开。 |
| revalidate_sidecars.py | root/output/baseline/audit-dir/label-fixes；核 branch_candidates 与 baseline 字节相同，固定 APK/CACHE 来源和 carrier 差异。 | 只写候选 sidecar_adaptation.json；保留旁注真实 C18 原戳，不能改戳冒充 C19 原生证据。 |
| seal_reader.py | 核主线、必需 PASS、adaptation；覆盖 candidate/audit-dir/stage_seal.json。 | seal 覆盖整树，仅排除该 seal 和对应 publish receipt。必须先完成所有会写文件的检查再封存，正式封存树不重跑。 |
| publish_reader.py | ROOT/BASE 固定，stage/live/backup 只能旧 BASE 直属 reader_*；rename 后才写 publish receipt，异常会反向 rename 并写失败日志。 | **B02 禁用**。这是 B03 切换动作，且当前接口不支持 projects/reader/site 直接发布。 |
| prepare_review.py | 遍历 reader 和源码，固定根文档/guard；复制后才核 guard，失败可能留部分 target。 | 不是候选构建；如需送审只用新 target，先核全部输入/复制写域，不接管旧冻结包。 |
| review_condition_closeout.py | 固定旧证据根、760 紫色 baseline/native/metadata；默认旧 work 目录。 | 先写 baseline inventory，后写条件回执/summary。初始路线不重跑。 |

当前未发现 build_c19.py 或 migrate_semantic.py；真实入口为 migrate_c19.py 与 build 的迁移参数，不按假定名字编制命令。

## 验证器也可能写文件

| 验证组 | 已核实边界 | 处置 |
|---|---|---|
| verify_c19.py | 必填 output；缺省 baseline 指向现已 C19 的正式 reader；写 c19_validation.json，失败也写。 | 必须显式 C18 baseline 与独立报告根；不能正式 reader 自比。已有 hardlink 回执保护不是全树保护。 |
| verify_effect_labels.py | reader/baseline/output 必填；ledger 仍由源码 ROOT 固定读取；写 fixes 与 validation。 | 显式区分 R01 标签 baseline 与 C18 守恒 baseline，补 ledger/报告接口且不降低证明。 |
| verify_condition_closeout.py / verify_confidence.js / verify_branch_ui.js / verify_player_conditions.js | 各自写 reader 内 audit 报告；部分证据仍固定 ROOT。 | 候选根和证据根必须同时闭合，正式封存树不运行。 |
| verify_branch_wiring.js | output 有默认正式路径，只有 --report 时写报告。 | 显式候选与独立报告；不把静态验证等同浏览器。 |
| verify_r01_production.js | 默认正式 reader；可选 source/output，输出多份生产核对 JSON 与 validation，失败亦保留。 | source、reader、报告根都必须显式；先确认真实副本，避免曾发生的硬链接污染。 |
| verify_branch_candidates.py、verify_inline.js、verify_levels.js、verify_levels_full.js、verify_merge.js、verify_multi_branch.js、verify_purple.js、verify_selection_order.js、verify_final5.js | 固定旧正式 reader，且写报告。 | 未适配前禁用，不能拿正式树成功证明 candidate。 |
| verify_damage_structure.js、verify_partial_conditions.js、verify_trigger_evidence.js | 本次静态扫描未发现文件写入，但输入仍固定旧 reader。 | 不能当作候选验证成功。 |
| read_selection_native.py、read_final5_sparse_native.py、build_mana_timing_receipt.py、review_final5_sparse.py、review_final5_random.py | 固定写正式 reader/native/历史 audit。 | 属历史证据生产，本次默认排除，不因过去被 full 调用就授权重跑。 |

旧矩阵中的 Translator/reference_pairs、semantic 字典、reference_copy、sample、prepare_*、verify_regressions、merge 失败写域等风险仍需对所选调用子集保留审查。媒体磁盘根与 URL 根分开；现有 ../pages/art 不能迁到新目录后照抄。

## 三类 baseline 与证明版本

1. C19 守恒：output/character_skills/reader_c18_before_c19_20261107/。
2. R01 标签：output/character_skills/reader_c19_before_r01_20261107/，经显式 label-baseline；不能用 C18 替代。
3. 旁注复用：按所选 branch_candidates 字节身份与 carrier 适配关系指定，不能只因目录名叫 baseline 就与前两者互换。

当前 V01 核对的源码 SHA-256：
- verify_c19.py：7582c1add45c2ce7406e07509e25eb7dce6708c12296b067e6b6c6baec5f7f99
- verify_effect_labels.py：f0b86c534e0a3b9e42ad7c29c8207f09e97e2431bded61e50f753df8ea0faf64
- verify_v01_fixtures.py：763638230071a8c36d443376fff5af714dee661dd619e46966d1c9b2a2c5f877

R01 正式封存与 V01 验证源码是分层交付，不覆盖原冻结 manifest。独立证明须保留 receipt schema/batch、fixes 内容与 hash、before/after/ledger 重算、容器检查；118 effects/106 rows/55 cards 是具名 R01 batch 契约，不是未来通用常量。

保留原 V01、错误 effect 容器、解除异常带答案、真实 117 项且同步伪造 hash 四类反例，以及第三方 29 案的退出码/失败日志。共享证明函数若改变，按原收口约定补必要回归，不能只跑正例。seal 的 symlink 检查不等于 hardlink 检查：所有未来待写副本逐项核实 nlink=1 与解析后的路径位于白名单。

## 候选回退

运行前先核真实路径、固定输入与允许写域；未闭合就不运行。运行时若失败或输入漂移，停止该候选，保留新失败目录/日志；既有站点继续使用。只撤回本任务的独立源码改动，不 reset 共享树，不覆盖他人的新改动，不删除 frozen evidence。正式服务切换与反向 rename 不属于本批。

