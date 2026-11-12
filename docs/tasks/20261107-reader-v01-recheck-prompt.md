# V01 验证链独立复审提示词

请独立复审本轮V01验证器修复。原R01生产内容已获PASS_WITH_EXPLICIT_SCOPE_LIMITS，B01—B03、N01—N06均FIXED。不要重新修改已通过的生产答案、标签、条件或页面，不启动C20。不能把实施方内部PASS当作V01复审通过。

项目根：`E:/代码项目/锁链战记数据解包`。

先读AGENTS.md、HANDOFF.md、`docs/tasks/20261107-reader-v01-verifier-closeout.md`；读取原R01独审 `output/character_skills/review/reader_c19_r01_thirdparty_20261107/REPORT.md`、verdict/evidence及work/run01/forged_label_verifier.json。新材料入口为 `output/character_skills/review/reader_v01_prepared_20261107/README.md`、manifest.json及source/。先核对哈希及代码差异。

独审输出新目录 `output/character_skills/review/reader_v01_thirdparty_20261107/`，已存在则另选目录。全部主线、正式reader、C19/C18备份、latest、历史审查及冻结材料只读。会写回执的工具仅对真实copy2副本运行；禁止复用硬链接，先检查目标nlink=1。保留每次失败输出和退出码。

重点检查：

1. verify_c19在允许标签变化前，是否直接读取before/after及ledger重算局部证明，而非信任pass=true、回执自身字段或另一个PASS文件。
2. effectID/rowId/description_ref、effect_type、span、snippet及原始日文是否真正对应；old/new、old/new pendingText及answerCount是否精确；解除异常状态带答案必须失败。
3. 全部55个相关卡的before/after SHA、固定同目录fixes文件的SHA及changes内容是否一一对应；缺卡、重复、遗漏、未消费修复是否失败。
4. R01批次118/106/55是否由独立策略约束，而非回执自报期望；实际输出恢复一项旧标签、只剩117修复并同步伪造receipt/hashes也必须拒绝。未来批次不能被无条件强制成118。
5. 全库实际effect容器中的21,806条答案，source.effectId必须等于容器effect.id；将30310 denju #e01答案移至#e02但保留source.effectId=#e01必须以容器错误拒绝。另把source.effectId改成异常目标后，仍应以“解除异常不得带答案”拒绝。14,005条unbound视图没有effect容器，不伪造绑定；35,811总视图保持。
6. 独立构造原V01：30310 denju #e01带答案“回复”改“伤害”，伪造对应new并同步after与fixes哈希，保留118项；必须因局部语义失败，不能只是旧schema/缺参数失败。
7. 其余负例：错误span/snippet/effect_type、old/new/pendingText/original/answerCount、缺/重复/未消费项、漏before/after卡哈希、错误fixes/ledger/after哈希、仅pass=true无证明、少于118声称R01完整。检查真实CLI退出码及具体拒绝原因，不把环境错误当成功拒绝。
8. 所有原C19保护保持：133/407/45、35404旧答案、9卡16指纹、760→474/286、2222评估、394父、883条件、2240主线SHA；353/30257金、30236绿、30310紫。核对生产数据和页面哈希未变化。

隔离命令接口（变量由你指向自己的真实副本）：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_effect_labels.py --reader $reviewReader --baseline output/character_skills/reader_c19_before_r01_20261107 --output "$reviewReader/audit/v01_review" --batch reader_c19_r01_20261107
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_c19.py --output $reviewReader --baseline output/character_skills/reader_c18_before_c19_20261107 --audit-dir audit/v01_review --label-review "$reviewReader/audit/v01_review/effect_label_validation.json" --label-baseline output/character_skills/reader_c19_before_r01_20261107 --label-batch reader_c19_r01_20261107
```

不要混用两个baseline：C19守恒对C18；标签修复对整改前C19。旧v1标签回执缺少新证明字段，会拒绝；新回执仅在隔离目录生成，不更新正式封存。源文件冻结副本不是独立发行包，执行前核对当前项目源码与新manifest；其余既有依赖仍从项目只读使用。

另在隔离副本重跑verify_full、verify_confidence、verify_condition_closeout及verify_branch_wiring，参数参见材料regressions/results.json。条件验证所需原inventory与condition_closeout_receipt可copy2到自己的新audit，不重建或变更生产。写回执会使复制的旧seal失效，这是副本行为，不能重写正式seal来通过。

本轮没有生产输出变更，不要求为了形式重复浏览器；若发现或实施生产变化，另报告并补30310桌面/390px验证。没有任何实机或新主线语义研究授权。

交付REPORT.md、verdict.json、evidence.json及独立反例。对V01给出FIXED / STILL_OPEN / UNTESTED，列代码位置、适用域、正负退出码、拒绝原因及剩余限制。共享proof函数和独立CLI是同一算法的两个入口，不能当成两份独立证明。原R01报告及裁决保持不变；内部子代理测试也不等于第三方复审。
