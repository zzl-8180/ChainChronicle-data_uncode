# 主线布局与退役空目录清理回执

结论：**主线位置正确，可按最新主持流程继续；本轮已清理5个previous联接对象、9,467个旧空目录，文件删除0。Sol及Astra独立后验通过。** 不需要主线停工、再次交接或等待目录整理。

## 主线位置

正常生成源码仍在 `scripts/character_skills/`，包括 `card_page_batch.py`、`card_page_batch_parallel.py`、`card_page_data.py`、`rules.py`、`effect_ledger.py`。正式规则、pages及账本仍在 `output/character_skills/`，v3输入仍在 `output/cache_full_20261015_v3/decoded/`。本轮没有迁移主线，也不要将新主线输出写入退役历史根。

规则294键、当前指针、C19当前入口及正式文件保持；AGENTS第8节、C19／Web结论不因整理改变。C19历史包装脚本实际位置是 `output/character_skills/c19_delivery_20261107/run_formal.py`，不是根scripts下的同名文件；该历史周期不需要重跑。

已知旧历史对账脚本 `reconcile_mechanism_first_handoff_20261104.py` 的默认bundle是旧路径，历史对账需显式 `--bundle operations/history/retired-packaging/20261108/share_bundle/20261104-mechanism-first-handoff-r1/payload`。旧打包、旧恢复及冻结清理脚本均不作为主线接续入口；普通生成链未发现对退役打包执行路径的依赖。

## 本轮实际清理

用户已授权确认安全后直接清理。沿用前次绑定的9,476目录原ID快照、11原位文件及五previous原身份，明确排除保留文件所需祖先和新历史根。

- 五previous逐项核原ID、mount-point tag、旧target后，仅删除联接对象。
- 9,467目录来自原快照减9个必要祖先的精确集合，按深度逆序逐项核ID、no-reparse和为空，再非递归移除；未知项或非空会停止，不会清空内容。
- 9个必要祖先目录、11项原位文件、三个新历史根、五个正式联接保持；next仍无。
- 使用 `RemoveDirectoryW`，没有递归或文件删除API。自有小夹具实测删除junction后target及文件SHA不变、非空目录被WinError145拒绝。见 [native-fixture-result.json](native-fixture-result.json)及[微软API说明](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-removedirectoryw)。

真实结果：[result.json](result.json)，退出码：[apply-exit.json](apply-exit.json)。日志 [cleanup-journal.jsonl](cleanup-journal.jsonl) 有9,472对INTENT／DONE，共18,945行，无PAUSED。没有修改联接target或移动材料，没有停止其他进程，没有提交／推送。

## 保留材料的处置

**5,317项／108,004,454字节归档材料及11项原位材料继续保留，不能整批删除。** 其中包含研究payload与manifest、历史恢复manifest、P/v7保护的指定旧源码、历史审查／反例及来源证据。目录名含“retired”不表示内容可丢弃；前次完整分类和冻结保护边界继续有效。本轮不扩大成新的材料退役或批次迁移。

## 验收

Sol [sol-postcheck.json](sol-postcheck.json)通过。Astra [astra-post-review.json](astra-post-review.json)独立核实全部清理对象明确不存在、9个必要目录／11文件原身份、三个新根／五正式联接、17保护及七份关键归档身份，日志集合／原ID／顺序／数量一致；SHA `d1700748c0acbc236f77d71467804d0368d16f40a1b2ff3d0894f03ae91e3b98`。未重复全量验收5,317材料或五入口各142文件。

前置边界独审：[astra-review.json](astra-review.json)。本轮授权范围已履行，不重放旧清单；当前导航更新仅限四根退役状态，其他主线内容保持。

最终导航独审 [navigation-review.json](navigation-review.json)通过，SHA `2ebf913ee9990080e2bf1a3112592cd79a03935bf971ad051d2b95ad07dfe486`。四根仅5个退役状态段落改变，AGENTS第8节及C19／Web完整保持；399个本地链接均实际有效。没有剩余阻断或待主持操作事项。
