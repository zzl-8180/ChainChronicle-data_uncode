# C19 Web 收口结论及补充证据接收登记

- 接收日期：2026-11-08；状态：**已登记接收／证据保留／正式吸收待另行安排**。
- 本文件只做接收登记与交接，不表示正式吸收，不改变主线数据基线，不启动C20或新研究周期。

## 1. 来源与独审结论

读取来源：

- `docs/tasks/20261107-reader-v01-verifier-closeout.md`
- `docs/tasks/20261107-reader-mainline-evidence-handoff.md`
- [原C19 Web R01复审](../../output/character_skills/review/reader_c19_r01_thirdparty_20261107/REPORT.md)及[verdict](../../output/character_skills/review/reader_c19_r01_thirdparty_20261107/verdict.json)
- [V01独立复审REPORT](../../output/character_skills/review/reader_v01_thirdparty_20261107/REPORT.md)／[verdict](../../output/character_skills/review/reader_v01_thirdparty_20261107/verdict.json)／[evidence](../../output/character_skills/review/reader_v01_thirdparty_20261107/evidence.json)

登记结论：

- C19 Web接入与独立复审已收口；V01 **FIXED**，总体 **PASS_WITH_EXPLICIT_SCOPE_LIMITS**。
- 原R01的B01—B03、N01—N06保持FIXED；早期REQUEST_CHANGES作为历史前像保留，不改写。
- V01复审实际日期为2026-11-08，目录名沿用`20261107`。其29个独立反例均真实退出1并按预期拒绝，六项隔离回归通过；生产输出和主线未变。
- Web工作未修改主线`rules.json`、角色答案或`effect_ledger`，也未修改正式pages、profiles或latest。

## 2. 证据原路径、版本及已有哈希入口

- 原R01证据目录：`output/character_skills/review/reader_c19_r01_thirdparty_20261107/`；snapshot `99bee2a1-cf9451c6ff47fcfb`。
- V01证据目录：`output/character_skills/review/reader_v01_thirdparty_20261107/`；含逐案输入、真实退出码、失败日志、回归结果和保护证据，不复制目录。
- prepared材料：[README](../../output/character_skills/review/reader_v01_prepared_20261107/README.md)、[manifest.json](../../output/character_skills/review/reader_v01_prepared_20261107/manifest.json)及[manifest.sha256](../../output/character_skills/review/reader_v01_prepared_20261107/manifest.sha256)。送审时`PREPARED_NOT_REVIEWED`状态保留，由上述V01新裁决承接。
- 冻结与保护：[prepared_freeze.json](../../output/character_skills/review/reader_v01_thirdparty_20261107/prepared_freeze.json)、[r01_production_freeze.final.json](../../output/character_skills/review/reader_v01_thirdparty_20261107/r01_production_freeze.final.json)、[regression_exit_codes.json](../../output/character_skills/review/reader_v01_thirdparty_20261107/regression_exit_codes.json)、[all_copies_nlink_check.json](../../output/character_skills/review/reader_v01_thirdparty_20261107/all_copies_nlink_check.json)、[all_negative_results.json](../../output/character_skills/review/reader_v01_thirdparty_20261107/all_negative_results.json)。
- 补证根目录：`output/character_skills/reader_full_20261106/audit/`；各子目录和输入哈希按`reader-mainline-evidence-handoff.md`原索引读取，不另建副本。

独审登记的当前源码SHA-256：

| 文件 | SHA-256 |
|---|---|
| `verify_c19.py` | `7582c1add45c2ce7406e07509e25eb7dce6708c12296b067e6b6c6baec5f7f99` |
| `verify_effect_labels.py` | `f0b86c534e0a3b9e42ad7c29c8207f09e97e2431bded61e50f753df8ea0faf64` |
| `verify_v01_fixtures.py` | `763638230071a8c36d443376fff5af714dee661dd619e46966d1c9b2a2c5f877` |

`evidence.json`另记录正式reader manifest `bcdd886deb94a7273377e544414cb7909b3542b8eefccf046ee2b085e4bdc365`、前次独立verdict `0faacd4dec4e31a64d9ca2c55cf57048c7257e8a8c5420071f9b5cb342fb3193`及2,240个主线保护文件不变的证据。此处只引用，不重算或重写。

## 3. 尚未正式吸收的范围与限制

接收材料涉及：HP／Chain条件、完整竞争父集合与分支选择、使用次数与地形、法珠选档及扣费时点、稀疏字段初始化，以及部分结构关联推断。它们是**待主线独立核验的证据**，不已经成为主线正式结论；Web显示颜色和通过审查不自动授予答案升级、可信度提升或统计变化。

目录适配与正式吸收分开。若用户另行安排吸收，须先明确输入快照、证据适用域、正式消费者和验收基准，再决定接入方式；主线不得长期依赖Web JS或展示层audit路径作为生产消费者。本轮不展开吸收方案，不修改目录或生产实现。

## 4. 本轮实际边界

- 不修改规则、答案、账本、profiles、正式pages、验证器、正式Web、C18/C19备份、冻结送审材料或历史独立审查。
- 不重建正式数据，不修改latest、统计口径、可信度或数据基线；不删除、迁移或复制整套证据。
- 保留隔离副本、失败日志、真实退出码、逐案反例和原始哈希入口；不提交Git、不推送、不发布。
- 本登记仅新增本文件并在`HANDOFF.md`添加简短入口，不作为语义修改或新证据吸收授权。
