# 旧隔离／复现现场逐文件处置

2026-11-08，仅完成删除前准备；**未删除、移动、复制载荷，未运行任何业务生成器或旧清理入口**。仅写本目录。本页承接原退役 V1 的 1,997 项 HOLD，不修改原清单、旧独审、存储保护清单或当前业务成果。

机器入口：[repro-disposition.jsonl](repro-disposition.jsonl)，每行有 `path`、`bytes`、`disposition`（兼容保留 `decision`）、原因、证据编号、拟目标，删除项 `target=null`。1,997 个唯一路径精确覆盖原 HOLD，合计 2,894,924,641 B；无新增候选。元数据回执见 [receipt.json](receipt.json)。

|处置|文件|逻辑字节|含义|
|---|---:|---:|---|
|DELETE|1,443|2,868,028,876|1,270 项有独立存活来源新算 SHA-256 相同；另173项明确退休旧实验生成载荷／负例夹具及其精确重放|
|RETAIN_HISTORICAL|547|14,715,193|旧版本源码／文档／tar、报告、审查查询、原生恢复元数据、小型对账与来源证据，拟移交历史区|
|REHOME|7|12,180,572|P保管例外脚本、五份2MiB恢复输入以及一份原生库备份；不以“打包副本”理由放弃|
|BLOCKED|0|0|未确认唯一性的恢复输入已转为保留移交，没有以整组HOLD掩盖未知|

上述数字是逻辑文件长度，未释放空间为0，不是NTFS实际释放保证。保存554项合计26,895,765 B的历史／恢复内容不等于保存整包；旧现场生成载荷的精确回放将永久退役。当前版本不同的根文件没有被称作旧版本同字节替代品。

## 范围与拟移交位置

|根|DELETE文件／字节|历史保留文件／字节|REHOME文件／字节|
|---|---:|---:|---:|
|20261025 isolated 中文 space|1,011 / 1,355,553,049|21 / 1,468,377|2 / 2,109,492|
|work/delivery_20261016|187 / 674,886,172|258 / 6,213,790|3 / 5,876,776|
|work/repro_20261016|112 / 340,115,975|114 / 2,785,732|1 / 2,097,152|
|work/review2_20261016|21 / 65,111,048|14 / 346,662|0|
|work/review_20261016|10 / 24,406,474|16 / 634,278|0|
|work/review_20261017|3 / 4,341,861|3 / 88,653|0|
|work/review_20261017_r1|99 / 403,614,297|121 / 3,177,701|1 / 2,097,152|

拟目标统一为 `operations/history/retired-packaging/20261108/`：share_bundle内保留材料进入 `share_bundle/<原output/share_bundle后缀>`；六work根进入 `history-work/<原work后缀>`。保留原相对后缀，避免破坏外部映射所需位置；本轮目标均未存在，不复制数据或建立联接。只有完成移交、目标逐项长度／哈希与路径映射验收后，才有条件退役这些源路径。五份signal输入虽内容可能重复，仍逐路径保留移交计划，不猜测物理硬链接或独立唯一性。

## 逐项证据编号

- **E_META**：原来源是 `../..` 下 `20261108-packaging-retirement-v1/retain-and-hold.jsonl` 的HOLD记录。重新按七根逐层无跟随枚举，共357目录，普通文件集合与1,997原路径完全一致；逐文件size、mtime_ns、dev、ino、nlink均与冻结观察相符，七根内部无reparse。**不包含外部指向这些根的junction**，不能从本结果推出全项目无联接。
- **E_EXACT**：[verified-source-pairs.json](verified-source-pairs.json) 为1,270项逐件源→存活来源映射，新算双端SHA-256、长度一致，未用单纯相同大小判断。存活来源限定本次七根之外，也未以拟删除的 `scripts/release` 充当依赖。保留 `survivor` 的原路径，整合者仍须解析完整迁址方案的最终目标，避免同时删掉源和替代者。活跃四根文档不作历史回退来源；isolated README的存活副本改为冻结 `P_small_closure/A_tools/README.md`，新核8459 B／9ac94780…。
- **E_APK**：[apk-originals.json](apk-originals.json) 新算根原APK身份。六份隔离APK均在E_EXACT中与根 `チェンクロ.apk` 新算SHA-256相同，各95,931,650 B；包括R1现场另名 `MyApk-5.6.2.apk`。原APK只读保留，不归打包。原始raw、缓存、主线、存储vault不在处置集合。
- **E_HISTORY**：优先保留未证同字节的小型历史版本和事实，不假定Git可恢复未跟踪代码。包括四个head/final tar、旧源码和任务文档、q1/q2查询结果、decode_report/progress/tables、audit_reads、baseline、relocations、metrics、stage元数据、分片／对象索引／验证回执。普通效果、必杀／治疗、角色原生检查与规则中未证同字节的语义证据也保留。对应原实测与审查入口见 `docs/tasks/20261016-reproducibility-audit.md` §8、整改记录及 `output/20261016-reproducibility-audit/review/`；这些正式报告原位不改。
- **E_REPRO**：六work根是上述10月16—17日隔离复现、独立复验和整改现场；20261025现场的生产／消费由 `output/share_bundle/20261025-character-tools/test_isolation.py` 的 `run()`、解码与对比段和 `isolation_launcher.py` 的audit记录明确。173项无存活同字节证明的DELETE，逐行写明永久放弃旧生成数据和精确重放：旧解码展开／records、APK主表输出、DWARF展开、隔离参数查询视图、profiles/links/ledger投影、试验角色JSON/HTML与少量负例／媒体载荷。原生恢复输入和独特参数证据不走这条默认理由。**未称这些旧数据可由当前版本原样重建。**
- **E_INPUT**：五份 `work/protection/compatible_signal_seed1.bin` 各2,097,152 B，根同名来源未证一致，均保留移交；`work/delivery_20261016/final/work/neg_tests/libcompatible.bak` 1,682,472 B也保留。没有以bin后缀、测试目录名或库备份名判定可删，逐项记录新算哈希。
- **E_CONSUMERS**：定向检查当前 `scripts/**/*.py` 的真实引用与IO。`scripts/release/build_delivery_bundle.py:249` 只把旧final路径写入manifest文字；`cleanup_20261023.py:117` 对review两根是旧清理扫描分类，正式审查消费者读的是独立正式review报告。未发现当前正式角色生成、查询、verify或ledger直接读取这七个根。`recycle_v1/prepare_manifest.py:11` 硬编码isolated保护前缀，并实际读取retry A/B/C ZIP形成旧清单；`finalize_g1.py` 对P路径仅写报告文字。**这是一份有边界的静态IO复核，不是全仓动态无消费者证明**；外部junction和其他work历史脚本由整合者的消费者调查承接。
- **E_PRESERVATION**：见下节及 [storage-resolution-proposal.json](storage-resolution-proposal.json)。

为控制读取范围，新算流式哈希约1.80GB，未全量哈希所有生成大JSON、旧ZIP或APK展开包。实际流读取字节不代表磁盘物理IO；APK／必要native来源与小文件按需核对。元数据稳定不证明未来无人写入，执行前仍需重核。

## P第222项与存储保护的承接

`output/storage_retention/recycle_g1_20261027/P_preservation.json` 共222项。**第222项实际字段是 `source_existing_protected`，没有 `preserved_path`、`source_zip` 或 `member`**，指向isolated中的 `scripts/release/build_explicit_bundle.py`，12,340 B，SHA-256 `b74e4681d492fbf0f7258e138669abf91bba23c27e091f865deae428ec4e9ee2`，本轮实读匹配。它是被保管的小payload，必须移交，不能随isolated生成数据删除。

`P_small_closure/A_tools/scripts/release/build_explicit_bundle.py` 是另一版：12,508 B，SHA-256 `5b77a83d0b4dc574379d2f918bc99776cd1f5019a2f8809953006b42a4b84cd4`，不能替代第222项。前221项的 `source_zip` 是历史来源身份；是否还有代码实际打开ZIP要按IO判断，不能把字段文字本身当动态读取。当前所查 `scripts` 中未找到解析P的 `preserved_path`／`source_existing_protected` 的程序；旧prepare_manifest实际读ZIP是另一条已经识别的旧治理重放依赖。

P第222项目标保持为 `operations/history/retired-packaging/20261108/share_bundle/20261025-character-tools/isolated 中文 space/scripts/release/build_explicit_bundle.py`。整合时须新增**有版本的外部来源路径＋预期内容→新路径解析映射**及当前保护继承／退役覆盖说明，保存原P清单和protection_manifest_v7内容不变。v7整根isolated保护是冻结旧基线，不能静默改写、删除或把旧保护原样生效说成已解除。当前任务只提出映射，未实施移交、联接retarget或保护策略更新。

## 删除前仍要完成的整合门槛

逐项唯一性已闭合到“新核同字节来源／明确弃置旧生成载荷／保留移交”，没有未查明内容被塞入DELETE。**这不等于可以立即删除**：整合者须验证所有survivor在完整方案中的最终存活目标，完成554项移交与外部映射、P保护承接，以及外部junction消费者的保留／明确退役方案；更新现行导航而保留冻结历史；用户最终确认后临前复核身份和祖先无reparse，只按明确普通文件清单处置。当前审批范围仍是准备，不执行任何移交或删除。

[investigate.py](investigate.py) 是此范围的只读调查实现；只输出本目录证据，不导入业务模块，不执行解码／打包／清理。已有回执足够，不因收尾重复读取大文件。
