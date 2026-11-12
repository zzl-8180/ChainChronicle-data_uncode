# Web R01 V01 验证链收口

- 状态：**CLOSED_WITH_EXPLICIT_SCOPE_LIMITS**。2026-11-08接收第三方独立复审：V01 FIXED、总体PASS_WITH_EXPLICIT_SCOPE_LIMITS；原R01的B01—B03/N01—N06继续FIXED。父聊天仅更新本收口交接，不改代码或生产内容。
- 本轮授权：只修验证链与必要夹具，不改已独审通过的生产答案、标签、条件、颜色或网页；不启动C20。
- 写入范围：scripts/skill_reader_preview/verify_c19.py、verify_effect_labels.py、新V01验证夹具；output/character_skills/reader_v01_validation_20261107独立副本；work/reader_v01_20261107；本任务文档及新的V01复审材料。
- 只读：正式reader、C19/C18旧版、主线、latest、全部历史独审及冻结材料。
- 修复前基准：R01独审PASS_WITH_EXPLICIT_SCOPE_LIMITS，B01—B03/N01—N06 FIXED；当时V01 OPEN_NON_BLOCKING。当前结论以本文末尾独立复审接收记录为准，内部复验与第三方结论分开保存。
- 验收：局部语义直接重算、答案容器一致性、118/106/55和全部要求的伪造负例；六项隔离回归、主线及正式Web哈希不变。复制只用真实copy，不用硬链接。

## 验证责任划分与接口

`verify_c19.py --label-review` 不再相信旧v1回执自报PASS。新增必填配套参数 `--label-baseline <整改前C19>`；原 `--baseline <C18>` 继续用于C19守恒，两者不能混用。`--label-batch reader_c19_r01_20261107` 选择R01的118效果/106行/55卡契约，期望值不来自回执，也不是所有未来批次的通用常量。

`verify_effect_labels.py` 提取无写入的 `audit_labels` / `validate_review`：直接读取独立before/after卡和主线ledger，核对effectID、description_ref、原文、局部span/snippet和effect_type；只允许有局部证据的回复↔解除异常变更；精确核对old/new与pendingText、answerCount，其他effect/row字段不变。新的v2回执新增effect_type、batch及容器统计。

`verify_c19` 直接执行上述函数，重算后才接受118项，逐项比较回执changes与同目录固定文件effect_label_fixes.json、fixesSHA256、ledgerSHA及全部55卡before/after哈希；重复、缺少、未消费项均拒绝。无需先运行独立CLI并信任其输出；CLI可生成可核对的新回执，但其自报PASS不是语义证明。

答案容器检查在共享证明及verify_c19主循环均执行：对全部原始阅读页实际effect容器中的21,806条答案要求 `answer.source.effectId == effect.id`；14,005条明确处于unboundAnswers的视图没有effect容器，不虚构绑定。合计35,811视图保持。全部69,964个effect中205个“解除异常状态”容器必须无答案。

其他责任仍由专项验证承担：verify_full检查全库阅读页结构/中文/来源/媒体；verify_confidence和verify_condition_closeout检查2222评估及760→474/286；verify_branch_wiring反向检查394父和883条件。文件保护另作前后SHA核对。V01不重新裁决原35,404答案的全部游戏语义，也不把原独审的范围限制升级为无条件通过。

## 复现与隔离

独立副本：`output/character_skills/reader_v01_validation_20261107/`，copytree(copy2)，2498个初始文件全部nlink=1；无硬链接或软链接。新回执写入 `audit/v01_validation_20261107/`，verify_full仅在该副本改写validation.json。

六项回归命令及完整stdout/stderr/exitCode：`work/reader_v01_20261107/regression_run01/results.json`。标签正向为118/106/55；六工具均exit0。生产数据未重建、未发布、未改页面，因此按用户要求不重复浏览器验收。

负向夹具由另一子代理独立编写，调用真实verify_c19 CLI。语义攻击同步fixes/after哈希，避免被哈希层提前拒绝；详细日志、输入快照和拒绝码保留在 `work/reader_v01_fixtures_20261107/`。共享核心函数与独立CLI复用同一实现，不能把这两次运行当成两套独立语义算法；新的第三方复审仍需自行检查代码及反例。

新独立复审只针对V01验证链；原R01总体裁决PASS_WITH_EXPLICIT_SCOPE_LIMITS及B01—B03/N01—N06 FIXED保持，不改原报告或冻结文件。

## 收口结果及复审入口

- 正向118项exit0；28负向全部exit1。原始30310伪改伤害被 `label_proof_local_semantics` 拒绝；#e01移至#e02保留旧source被 `label_proof_answer_container` 拒绝；source改为异常目标后仍被 `label_proof_status_removal_has_answer` 拒绝；实际恢复一项旧标签、只有117项且伪造自洽回执，被 `label_proof_batch_counts` 拒绝。
- `verify_c19` 正向514571项C19检查通过，额外局部证明包含118项及全库容器；verify_full仍1544616项；394/394父、883/883条件及原分母保持。没有生产输出变化，不重复浏览器。
- 共两次夹具驱动运行（主28案及追加真实117案1案）均exit0；每案真实CLI退出码单独保存。追加前源码按启动SHA精确还原并核对保留，两个已执行版本与最终源码都有哈希，未把未验证的源码冒充执行版本。
- 冻结送审材料：`output/character_skills/review/reader_v01_prepared_20261107/README.md`，含代码diff、三份源码、正向证明、全部反例输入与日志、六项回归、保护SHA及manifest。保留送审时的PREPARED_NOT_REVIEWED历史状态，不回写冻结材料；后续独立复审见下节。
- 隔离输出：`output/character_skills/reader_v01_validation_20261107/`；工作记录：`work/reader_v01_20261107/` 与 `work/reader_v01_fixtures_20261107/`。不改正式reader、旧版、主线、latest或旧报告；未提交Git、未发布页面。

## 2026-11-08 独立复审接收与最终收口

权威入口：[独立REPORT](../../output/character_skills/review/reader_v01_thirdparty_20261107/REPORT.md)、[verdict](../../output/character_skills/review/reader_v01_thirdparty_20261107/verdict.json)、[evidence](../../output/character_skills/review/reader_v01_thirdparty_20261107/evidence.json)。目录名沿用20261107，报告实际复审日期为2026-11-08。结论为V01 **FIXED**、总体 **PASS_WITH_EXPLICIT_SCOPE_LIMITS**；原R01的B01—B03、N01—N06保持FIXED。

本次收口已读取上述材料，以及同目录的 `all_negative_results.json`、`v01_negative_probes.py`、`all_copies_nlink_check.json`，只核对版本并更新本任务交接，没有重新运行或修改验证器。当前实际SHA-256与独审版本一致：

| 验证器 | SHA-256 |
|---|---|
| verify_c19.py | `7582c1add45c2ce7406e07509e25eb7dce6708c12296b067e6b6c6baec5f7f99` |
| verify_effect_labels.py | `f0b86c534e0a3b9e42ad7c29c8207f09e97e2431bded61e50f753df8ea0faf64` |

独立证据（区别于前文实施方的1正向＋28负向）：第三方独立构造的29个反例全部实际退出1并按预期拒绝；原V01同步伪造new/fixes/after哈希后仍被 `label_proof_local_semantics` 拒绝。六项隔离回归均通过，verify_c19为514,571项、verify_full为1,544,616项；21,806条绑定答案容器一致，14,005条unbound视图保持，205个解除异常效果带答案数为0。独审核实2,240主线保护文件及正式reader未变，所有测试副本nlink=1；完整依据保留在独审目录，不把本次文档接收称为再次独立测试。

验证责任及范围限制继续有效：

- verify_c19自身重算before/after和ledger局部证明，不再信任pass=true；R01的118/106/55是具名批次契约，不是未来所有批次的常量。
- 共享audit_labels与独立CLI是同一算法的两个入口，不能相互冒充独立证明；其他结构、中文、媒体、置信度、条件及分支检查仍由专项验证器负责。
- 失败列表最多100条，部分无review错误可能被截断；这是已披露的诊断限制，本轮不修改。不重裁全部旧答案游戏语义，不包含实机验证、新主线研究或新的生产浏览器验收。
- 实施方和第三方的隔离副本、失败日志、真实退出码、逐案输入与反例脚本全部保留，不清理、不只保留PASS摘要。冻结送审包、历史裁决、独审报告、正式reader、C18/C19备份、主线和latest均不修改。

后续复审从上述独立REPORT/verdict/evidence及逐案结果进入。原 `docs/tasks/20261107-reader-v01-recheck-prompt.md` 仅保留为本轮历史复现说明，不表示仍待复审或自动授权新任务。只有用户另行授权新批次或证明函数变更时才另建有界任务和审查目录：新标签批次另建独立契约及反例；共享证明函数变化须重验原V01、错容器、异常带答案及真实117项反例。诊断改进也是可选后续，不在本轮启动。

本轮收口仅修改本任务文档；未提交Git、未推送、未对外发布，未启动C20或新研究。
