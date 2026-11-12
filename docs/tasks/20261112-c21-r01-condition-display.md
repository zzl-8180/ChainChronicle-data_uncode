# C21-R01：F01／F02默认条件展示整改

- 日期：2026-11-12；状态：**原第三方定向复验通过，F01／F02均CLOSED，阻断0；C21在明确范围限制下收口**。
- 授权：用户明确“现在进行整改”，范围限于`20261112-c21-direction-receipt-r01-plan.md`。
- 原裁决：REQUEST_CHANGES，40/42，F01／F02阻断；原报告与C21冻结成果不改。

## 写域

- `scripts/character_skills/cycle_report.py`：仅新增C21_R01配置和 gated 展示投影；原C21路径不改语义。
- `output/character_skills/cycle_reports/C21_r01_20261112/`：新版展示、条件台账、验证、UNTESTED回执与新清单。
- `work/c21_direction_r01_20261112/`：独立重跑和验收。
- 本任务、复验提示词及必要短交接。

不修改正式pages、rules、effect_ledger、正式账本、900条机器答案、C20共用生产模块、原C21 manifest/handoff或原第三方审查；不运行正式生成、resume、清理、Git、发布、新缓存、新原生或实机。

## 容量临前实测

- RETAINED 12/12；reserved_bytes 8,032,729,057 B；max_runs 12、max_bytes 8,589,934,592 B，未放宽。
- 原C21成果174,025,359 B；当前磁盘可用123,368,497,152 B。新版与独立重跑均为展示文件，不申请正式run reservation，不自动清理。

## 验收门

- F01 70条／51卡（46条直接漏项＋24条法珠相关）与F02 19条／15卡全部覆盖，合计89条／66卡。
- 40条使用次数、6条地形、24条法珠和19条Chain逐项台账；其它811条不得借入条件。
- CID354、6310、6326、8320、8297强制反例；CID30304与无额外条件反例回归。
- 900条机器答案身份、raw、来源、规则、账本不变；默认无内部字段／Chain计数，展开保留raw和未知边界。
- 新版与独立重跑确定性一致；原C21成果和原审查哈希不变；浏览器继续UNTESTED。
- 完成后状态仅为`IMPLEMENTED_PENDING_ORIGINAL_THIRD_PARTY_RECHECK`，交原第三方复验，不自行关闭F01／F02。

## 实施与验收回执

- 新版：`output/character_skills/cycle_reports/C21_r01_20261112/`；原C21目录与原第三方审查未改。
- `condition_ledger.json`／CSV：89条／66卡；40条使用次数、6条地形、24条法珠、19条Chain全部登记，其它811条无借入非Chain条件。
- `verification_detailed.json`：**60/60 PASS**。覆盖第三方精确row/raw、summary与必要条件栏、900条展开raw、24条法珠已知／未知、19条Chain、CID30304、4项同句未解与843行拆分、全部链接和独立重跑。
- 原C21 report_data／verification／900答案台账重跑逐字节一致；HTML／README在外部链接目标与`--output`路径归一化后一致。原manifest的10文件和handoff未改。
- 新manifest登记12文件，SHA-256 `f56b9f5ee3a64bdf6a9820467e383aaeefdb80205fd43ac05009fd62279996fd`；handoff为`IMPLEMENTED_PENDING_ORIGINAL_THIRD_PARTY_RECHECK`，`F01_CLOSED=False`、`F02_CLOSED=False`。
- 浏览器继续UNTESTED；未运行正式生成、resume、清理、Git、发布、新原生或实机。
- 原第三方复验提示词：`docs/tasks/20261112-c21-r01-original-thirdparty-recheck-prompt.md`。

## 原第三方最终复验

- 裁决：PASS_WITH_EXPLICIT_SCOPE_LIMITS；F01=CLOSED、F02=CLOSED、39/39、阻断0。
- 独立核对89条／66卡，900条机器答案回归通过；全库2,236卡、4,472个正式文件与生成回执通过；只读历史引用3项，最终入口实际退出0。
- 复验目录：`output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/`。
- 限定收口记录：`docs/tasks/20261112-c21-r01-recheck-closeout.md`。原REQUEST_CHANGES、R01送审时PENDING／false及新旧manifest/handoff均不回写，由最终裁决承接。
