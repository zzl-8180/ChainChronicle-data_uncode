# C21-R01原第三方定向复验提示词

请将以下提示词交回**原C21第三方方向审查者**，沿用原审查上下文。不要用其他模型或主持自检替代原第三方关闭F01／F02。

---

请对C21-R01做F01／F02定向复验。项目根为`E:\代码项目\锁链战记数据解包`。

先读原最终审查`output/character_skills/review/direction_c21_20261112_thirdparty/`的`REPORT.md`、`verdict.json`、`findings.json`、`evidence.json`、`answer_ledger.json`、`run_log.json`和`execution_receipts.json`，再读：
- `docs/tasks/20261112-c21-direction-receipt-r01-plan.md`
- `docs/tasks/20261112-c21-r01-condition-display.md`
- 新版`output/character_skills/cycle_reports/C21_r01_20261112/`。

原裁决REQUEST_CHANGES、40/42、阻断2必须保留；`development_attempt_01/02`只属审查脚本开发诊断，不列为正式交付缺陷。本轮只整改默认条件表达与展开证据，900项raw、来源、父集合、机器答案、账本、正式pages及原C21成果不改。

## 只允许写入

`output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/`。

至少交付`REPORT.md`、`verdict.json`、`findings.json`、`evidence.json`、`answer_ledger.json`和可重跑`run_review.py`。入口支持`--root . --out <审查目录>`，实际执行并记录命令、退出码、独立重算数与只读引用数。不要依赖固定parents层数定位项目根。

不得修改正式pages、rules、effect_ledger、生成器、原C21成果、C21-R01成果、原审查或新旧manifest；不得运行正式生成、resume、隔离卡页生成、清理、Git、发布、新缓存、新原生或实机。若未实际启动浏览器，视觉与交互继续UNTESTED，静态HTML解析不得冒充浏览器验收。

## 定向复验范围

### F01：70条／51卡，不只46条

对照原`evidence.json/details/nonchain_condition_inventory`全部70条：

1. 40条`limit=1`：默认中文必须为“本分支已使用次数小于1次”，不能改称整个技能第几次；重置时机、优先级／切换边界和完整选档未验证保留。强制检查CID354。
2. 6条地形：5条沙滩／船上／海中，CID6326为荒地；不得把另一分支自动译为地形补集，不得套给其它效果。强制检查CID6310与6326。
3. 24条法珠相关：逐项核对原文明确写出的法珠／废料种类、阈值或生成／破坏描述，与原始计数区间对象、扣费前后阈值、重置和完整选档未知分开。不得把mns/mne直接译成发动前数量，不得把生成效果误当条件。24条都要有已知与未知，不得只写“当前基础档”。
4. `chs=che=0`只能说未设置Chain区间门，其他必要条件另列；不能再以“当前基础档”掩盖使用次数／地形／法珠条件。

### F02：19条／15卡

对照原`evidence.json/details/chain_condition_inventory`全部19条：

- `[0,3]` 11条→通常（0th）至2ndChain；
- `[0,4]` 7条→通常（0th）至3rdChain；
- `[4,5]` 1条→3rdChain至MaxChain。

强制检查CID8320与CID8297。默认层不得出现“Chain计数4–5”等内部计数；原始chs/che、0值特殊无Chain路径及完整选档未验证必须在展开层保留。不得把内部4／5写成玩家4th／5th。

### 全量回归与证据

1. 合计89条／66卡与原第三方row集合精确一致，无row重叠；每条条件从本答案`binding.selected.parent_conditions_raw`重导，不借兄弟分支。其它811条不得被借入使用次数、地形或法珠条件。
2. 逐行同时检查summary、必要条件栏和展开层，不只看`condition_ledger`自洽。900条默认层不出现chs/che、mns/mne、bgf、limit、skillparam、record_id、json_pointer或内部Chain计数；900条展开层都有selected原始条件。
3. 新版`condition_ledger.json`应为89条，CSV同为89条；法珠24条的`mana_known/mana_unknown`与实际默认中文一致。
4. 900条机器答案身份、raw、value、来源、规则键、证据等级、完整父集合、current_parent、selected、children、fragment、账本和正式pages不变。4项同句未解与843行拆分标志保留，CID30304首句条件镜像回归通过。
5. 新版详细验证为60/60；全部相对链接可解析。独立work重跑的report_data、900答案台账和89条件台账逐字节一致。
6. 原C21机器数据与答案台账重跑逐字节一致；HTML／README仅在外部链接解析目标及`--output`路径归一化后比较，不把不同输出目录的相对href误判为语义变化。原C21 manifest的10文件哈希与handoff保持，原第三方REQUEST_CHANGES不改。
7. 新版`final_manifest.json`登记12文件（原10＋condition_ledger JSON/CSV），SHA-256与字节数匹配；`handoff_verification.json`为单向manifest哈希，`F01_CLOSED=False`、`F02_CLOSED=False`、原第三方复验PENDING。只有你的最终裁决才能改变主持状态。
8. retention 12/12、reserved_bytes 8,032,729,057 B、12 run／8 GiB限额不变；本轮没有正式生成或新reservation。浏览器、新原生、实机、最终扣血／命中／运行时装载继续UNTESTED。

## 裁决格式

`verdict`使用`PASS_WITH_EXPLICIT_SCOPE_LIMITS`或`REQUEST_CHANGES`，明确：
- `F01=CLOSED／OPEN`、`F02=CLOSED／OPEN`；
- `blocking`数组与`blocking_count`；
- `checks_total/checks_passed`；
- 独立重算与只读引用数量；
- 89条逐项台账、未测项与精确证据。

任何漏项、错档、跨分支借值、法珠时点猜测、默认内部字段泄漏、机器答案变化或旧成果漂移，都给出具体row／record／字段／文件位置和最小修复范围。若REQUEST_CHANGES，停在findings；主持不会自动继续重建。若两项CLOSED且无阻断，也请保留关联推断、固定cohort、浏览器／实机UNTESTED及局部伤害输入边界。
