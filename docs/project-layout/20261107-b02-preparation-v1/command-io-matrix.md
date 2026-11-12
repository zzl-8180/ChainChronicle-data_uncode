# B02 当前命令读写矩阵

静态调查版；16个入口或模式，**本轮均未运行或import**。这是所选闭包下限，新入口及其子调用须先补齐同等声明。行号绑定[观察代码身份](observations.json)，不声称活动代码永不变化。完整字段见[机读矩阵](command-io-matrix.json)。

`DATA=output/character_skills`，`FULL=DATA/reader_full_20261106`，`SEM=DATA/reader_semantic_20261107`，`HERE=scripts/skill_reader_preview`。`out`是源码当前输出参数或固定目标，不表示已获准候选根。各命令的`--root`语义不相同。

| ID／入口 | 当前读取 | 当前写入及失败副作用 | CLI与候选前置 |
|---|---|---|---|
| build-full：[build.py](../../../scripts/skill_reader_preview/build.py)；default full；源码76-107,130-136,223-265,287-294行 | DATA/pages/_batch/campaign_latest.json及相对pages的report；DATA/profiles/rules.json；DATA/effect_ledger/metrics.json及ledger.jsonl；账本涵盖的全部pages/<cid>/card.json；Translator：源码旁四字典及固定FULL/audit/reference_pairs.json；参考index_unpack.html；pages/art存在性 | out顶层前端文件及README；out/data/catalog.js及data/cards/*.js；out/audit翻译统计；out/build_receipt.json。非原子写；写中失败可留部分结果；末尾重读reference_pairs失败也已写。 | --root与--output；output默认FULL，无候选边界。 固定完整输入/代码并显式新输出；不得仅改--output。 |
| build-sample：[build.py](../../../scripts/skill_reader_preview/build.py)；--sample；源码21,36-65,103-153,237-265,289-294行 | 完整ledger与全库cards/名字，详情六卡；旧ui_reading_preview/_research/copy_*与_data/facts_*；reading_copy_extra.json；pages/art | out/data/catalog.js及合并data/cards.js；out/assets/icons与assets/cards；web/README/build_receipt。out缺省仍为FULL；头像同大小可跳过复制；只复核六卡并非全目录读取一致性。 | 有--sample，help虽写explicit output却未强制；不与frontend-only互斥。 独立sample数据协议；显式新输出、禁止与其他mode混用。 |
| build-frontend：[build.py](../../../scripts/skill_reader_preview/build.py)；--frontend-only；源码268-294行 | 已有out/build_receipt.json与catalog存在性；源码web/及README | 已有out顶层web文件；out/frontend_receipt.json及README。拷贝后才读receipt字段；失败可留下部分前端；不读取实时主线。 | --root/--output；与sample同时给时frontend优先。 仅刷新本批拥有且已接收的候选；预验数据receipt并绑定其完整哈希。 |
| reference-copy：[reference_copy.py](../../../scripts/skill_reader_preview/reference_copy.py)；standalone；源码126-139,231-240行 | --root下参考cards/*/unpack.html | --audit文件，默认FULL/audit/reference_pairs.json。解析完成后覆盖目标；缺单卡HTML跳过；不自动把audit参数传Translator。 | --root含义为参考站根，区别build；--audit可指定。 优先接收固定reference_pairs；需重新提取则另明确参考版本与新输出。 |
| inline-build：[inline_trial/build.py](../../../scripts/skill_reader_preview/inline_trial/build.py)；standalone；源码8-35行 | 固定FULL/data整树；FULL三份web及build/frontend receipt；inline_trial/web/*及README | 固定reader_inline_trial/data及web/README；trial_receipt.json。复制后才校验源稳定和目标JS；失败已有写出。copytree范围大于预hash的*.js；不复制源receipt本体。 | 无CLI；ROOT/SOURCE/OUT固定，source与out同父断言维持媒体相对布局。 先确认产品范围；显式source_reader/output/web；复制与哈希范围一致；保留源receipt身份。 |
| prepare-semantic：[prepare_semantic_review.py](../../../scripts/skill_reader_preview/prepare_semantic_review.py)；standalone；源码6-10,20-28,62-72行 | 全局DATA/pages；Translator固定字典/reference_pairs | SEM/packets、units.json、rows.jsonl、manifest.json。已有manifest会拒绝；否则可能先建目录/写部分文件，manifest最后写。 | 无路径CLI。 默认不选用；额外授权时输入与全输出候选化，不能覆盖冻结SEM。 |
| prepare-numeric：[prepare_numeric_review.py](../../../scripts/skill_reader_preview/prepare_numeric_review.py)；standalone；源码6-20,32-37行 | 全局DATA/pages；presentation/literal_presentation/branch_reading | SEM/numeric_families.json；SEM/numeric_rows.jsonl；SEM/numeric_compact.json。没有已有manifest保护，顺序写可部分成功。 | 无路径CLI。 默认不选用；若需生成独立版本，明确所有数值审查输出。 |
| merge-collect：[merge_semantic_review.py](../../../scripts/skill_reader_preview/merge_semantic_review.py)；collect / without --complete；源码13-47,57-58行 | AUDIT/manifest、packets、results | AUDIT/review_progress.json。先写进度再对errors抛错；不是只读收集。 | 函数仅audit可变；CLI没有完整路径接口。 默认禁用；接收已整合冻结字典，无需本批collect。 |
| merge-complete：[merge_semantic_review.py](../../../scripts/skill_reader_preview/merge_semantic_review.py)；--complete；源码44-58行 | collect的输入；全局DATA/pages的sourceHashes校验 | AUDIT/review_progress.json；源码HERE/semantic_sentences.json。覆盖/完整性/源哈希失败时进度可能已写；成功才写字典。 | --complete；audit不能约束pages和字典根。 若另选用须显式audit_input/progress_output/source_pages/dictionary_output四根；完整性拒绝不降低。 |
| review-report：[review_report.py](../../../scripts/skill_reader_preview/review_report.py)；standalone；源码15-29,49,83-87行 | collect()及SEM/units、rows；FULL validation、build_receipt；源码semantic_sentences | 先经collect写SEM/review_progress；成功写FULL/audit/semantic_review.json和html。后续验收失败前可能已写进度；通过后写报告。 | 无路径CLI。 默认禁用；移除隐式collect写入或显式候选进度，所有报告根单独声明。 |
| verify-sample：[verify.py](../../../scripts/skill_reader_preview/verify.py)；standalone；源码6-25,69行 | 固定reader_preview/catalog.js及cards.js；六CID正式DATA/pages及presentation | reader_preview/validation.json。check失败直接抛错，不更新报告；不能把旧PASS当新结果。 | 无路径CLI。 仅sample协议；候选站输入/正式基线/验收输出均显式。 |
| verify-full：[verify_full.py](../../../scripts/skill_reader_preview/verify_full.py)；standalone；源码68,88-128,267-291行 | --root的pages/rules/ledger/metrics；--output的receipt/catalog/card/frontend；源码字典及root下固定FULL/reference_pairs；由out+媒体URL解析的路径 | out/validation.json，含fatal失败分支和mkdir。成功和fatal均写validation；媒体解析可越出out；Node读取候选app但Translator仍有固定输入。 | --root/--output不足以隔离翻译/参考输入。 验证输入与报告输出分开；Node指定候选app；实际媒体路径在声明白名单；保留源/null/条件/哈希检查。 |
| verify-regressions：[verify_regressions.py](../../../scripts/skill_reader_preview/verify_regressions.py)；import or script；源码4-12,34,47,55,62,82行 | 固定FULL的350；正式DATA/pages/350及20329；SEM/numeric_families；顶层Translator | 成功写FULL/audit/regression_checks.json。顶层执行，无main保护；import即读/测/潜在写；失败可能留下旧报告。 | 无CLI。 禁止import；候选路径闭合前不调用；后续验证输出绑定run身份。 |
| verify-pagination：[verify_pagination.js](../../../scripts/skill_reader_preview/verify_pagination.js)；node positional app path；源码67-68,140-141行 | argv[2]或默认源码web/app.js；内存2236条fixture及模拟DOM | 无文件写入。无文件/网络/服务/子进程写入，stdout/stderr；模拟DOM不等于浏览器。 | 位置参数可指定app.js。 可候选只读验证，但本轮仍未执行；必须绑定选定候选app哈希。 |
| inline-verify：[inline_trial/verify.js](../../../scripts/skill_reader_preview/inline_trial/verify.js)；standalone；源码2-11,70行 | 固定reader_inline_trial/data/cards；require源码旁web/inline.js，非站点输出planner | 成功覆盖reader_inline_trial/validation.json。断言失败可能保留旧validation；当前验证器不证明站点planner字节一致。 | 无CLI；没有网络/服务/子进程。 显式候选站、输出报告及实际候选planner；源码与产物身份核对。 |
| answer-inventory：[audit_answer_inventory.py](../../../scripts/skill_reader_preview/audit_answer_inventory.py)；standalone；源码11-15,43-54,67-72,99-111行 | 全局DATA/pages；presentation.readable_value | 固定FULL/audit/answer_inventory.json。解析/呈现错误收集后仍写报告；标题Read-only不表示无写入或失败退出。 | 无CLI。 报告新路径；显式source_pages；定义错误状态与该次run的有效性。 |

## 子调用和服务边界

- verify_full调用Node的`--check`和`-e PENDING_JS`，读取指定输出app.js并做模拟DOM检查，失败由Python入口写validation。它不会自动运行verify_pagination，也不启动HTTP服务。
- review_report调用collect，因此可能在后续验收报错前已写现用语义进度；不能只隔离最终HTML输出。
- Translator在源码旁查semantic字典和三份已审句库；semantic不存在会改变翻译模式，有semantic时仍读reference_pairs。候选必须按所选模式明确必需文件，禁止静默缺件退回旧根或旧模式。
- common_grammar的translate属于内存调用；独立coverage入口另有固定审计输入，不在本轮所选执行集合。其他未列入口不由本表默认放行。
- 现服务只按README观察为127.0.0.1:8768、根output/character_skills；未查进程、未连接、未启动。现入口和服务切换不在B02本轮范围。

所有候选接口均未实现；更具体设计及拒绝保留规则见[接口与验收设计](interfaces-and-validation.md)，交接状态见[readiness.json](readiness.json)。

