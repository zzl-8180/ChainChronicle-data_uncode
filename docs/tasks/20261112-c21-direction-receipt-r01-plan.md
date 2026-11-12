# C21第三方REQUEST_CHANGES接收与R01限定整改方案

- 日期：2026-11-12。
- 当前状态：**R01原第三方定向复验通过，F01／F02均CLOSED，阻断0；C21在明确范围限制下收口。** 最终承接见`docs/tasks/20261112-c21-r01-recheck-closeout.md`。
- 原审查：`output/character_skills/review/direction_c21_20261112_thirdparty/`。
- 最终裁决：40/42通过、阻断2；900项数值与来源独立重算全部通过，历史只读引用11项。最终`run_review.py`实际退出1，表示F01／F02实质findings。
- 授权边界：本轮不修改正式pages、规则、账本、生成器或旧成果，不运行生成／resume／清理／Git／发布／新缓存／新原生／实机。浏览器继续UNTESTED。

## 1. 接收的最终证据

- `REPORT.md`：最终裁决与检查范围。
- `verdict.json`、`findings.json`：F01／F02及受影响数量。
- `evidence.json`：`details.nonchain_condition_inventory` 70项、`details.chain_condition_inventory` 19项的逐行原文、raw、指针、当前显示和最低可读条件。
- `answer_ledger.json`：独立900答案台账。
- `run_review.py`、`run_log.json`、`execution_receipts.json`：可重跑入口、最终命令与退出码。

`development_attempt_01/02`仅为审查脚本开发期诊断，已保留，不列为正式交付缺陷。900项raw、来源、父集合、片段绑定、正式页／候选一致性、精确消费、账本、保护卡、固定cohort现存文件比较及manifest哈希均通过；两项阻断不是900项原值错误。

## 2. 精确影响范围

| 项目 | 答案 | 卡 | 内容 |
|---|---:|---:|---|
| F01直接漏项 | 46 | 34 | 40条`limit=1`使用次数条件＋6条地形条件 |
| F01法珠相关 | 24 | 17 | 原文有法珠／废料条件；mns/mne对象和扣费前后时点不得猜测 |
| F01合计 | 70 | 51 | `nonchain_condition_inventory`全部纳入 |
| F02 | 19 | 15 | `[0,3]` 11条、`[0,4]` 7条、`[4,5]` 1条 |
| 合计去重 | **89** | **66** | 两组无row重叠，不得只修示例或只修46条 |

代表反例：

- CID354：本分支已使用次数小于1次；不能改称整个技能第几次，重置时机与完整选档仍未验证。
- CID6310：地形为沙滩／船上／海中；另一分支不得自动译为地形补集。
- CID6326：地形为荒地，不能套用CID6310的地形标签。
- CID8320：`[4,5]`→3rdChain至MaxChain。
- CID8297：`[0,3]`→通常（0th）至2ndChain；原始0的特殊无Chain路径留展开说明。

## 3. 最小整改范围（待另行明确授权）

### 写入范围

- 仅展示生成器`scripts/character_skills/cycle_report.py`的C21_R01配置与显示投影。
- 新版目录`output/character_skills/cycle_reports/C21_r01_20261112/`；原`C21/`冻结不动。
- 独立工作与验证目录`work/c21_direction_r01_20261112/`。
- 本任务及后续验收／送审文档。

不修改`card_page_inference_c20_direct_damage_common.py`、正式pages、rules、effect_ledger、正式账本、900条机器答案、原C21 manifest/handoff或原第三方报告。`direct_condition`是根因定位，但本轮用展示层等价投影闭合默认阅读，不为展示整改启动正式重建或改变旧周期答案。若未来要改生产答案文案，须另立任务、另行授权并先核容量，不属于本R01。

### F01：统一条件投影，不硬编码CID

1. 以每条答案`binding.selected.parent_conditions_raw`为本答案分支条件来源；当前描述父、完整父集合和原文继续用于展开核对，不跨分支借条件。
2. 40条`limit=1`统一显示“本分支已使用次数小于1次”；同时保留“重置时机、优先级／切换边界及完整选档未验证”。
3. 6条地形按所选分支raw和原文显示：5条沙滩／船上／海中，1条荒地；不得把另一分支写成地形补集，也不得把地形条件套给其它效果。
4. 24条法珠相关项逐行建立条件台账：原文明确写出的法珠／废料种类与条件作为已知；mns/mne原值和指针放展开层；计数对象、扣费前后阈值、重置与选档时点未闭合处逐项标未知。不得统一译成“发动前法珠数量”，不得只写“当前基础档”。
5. `chs=che=0`只表示未设置Chain区间门，改称“未设置Chain区间条件（其他必要条件另列）”，不再笼统写“当前基础档”。其它非Chain条件仍逐项展示。

### F02：内部计数转换为玩家档位

1. 对全部900条统一从raw区间重算显示，不只替换19条字符串：
   - `[0,3]`→通常（0th）至2ndChain；
   - `[0,4]`→通常（0th）至3rdChain；
   - `[4,5]`→3rdChain至MaxChain。
2. 既有其它区间继续按既有证据映射，不把内部4／5写成玩家4th／5th；无法确认的0值特殊路径不补造档位。
3. 原始`chs/che`、内部区间、原表指针、优先级与完整选档未知保留在展开层。默认层不得出现“Chain计数4–5”等内部计数。

## 4. 验收标准（实施后必须全部满足）

### 范围与语义

1. F01的46条／34卡及法珠相关24条／17卡逐项有证据台账；70条默认中文均显示该分支已知必要条件与未知边界，无一项仍仅写“当前基础档”。
2. F02的19条／15卡全部使用正确玩家Chain档位；CID8320、CID8297及`[0,4]`代表项分别通过，19条无内部Chain计数泄漏。
3. 合计89条／66卡全覆盖；每条从本答案selected分支重导，父集合、current_parent、selected、children和fragment不变。其它811条不得被借入使用次数、地形、法珠或Chain条件。
4. 900条答案的raw、value、来源、规则键、答案状态、证据等级及正式页身份逐项不变；0新增／删除机器答案，0规则键变化，0账本变化。

### 展示与回归

5. 默认层不出现`chs/che`、mns/mne、bgf、limit、skillparam、record_id、json_pointer或内部Chain计数；展开层完整保留这些原始证据及0值特殊路径、完整选档未验证限制。
6. CID354、6310、6326、8320、8297为强制反例；另覆盖24条法珠全部条目、非地形补集反例、无额外条件反例和CID30304条件镜像回归。
7. 900行HTML身份、全部相对链接、4项同句未解与843行拆分标志保持；默认／展开分层和900答案台账通过静态检查。静态解析不得写成浏览器视觉验收，浏览器继续UNTESTED。
8. 独立work重跑的机器数据和答案台账确定性一致；正式pages／rules／ledger／原C21成果／原审查的输入哈希在整改前后不变。新版生成自己的verification、browser UNTESTED、answer ledger、final_manifest和单向handoff，不改旧清单。

### 独立复验与停止点

9. 完成后交**原第三方审查者**只定向复验F01／F02及上述回归。主持不得自行把F01／F02写成CLOSED；新版状态先保持`IMPLEMENTED_PENDING_ORIGINAL_THIRD_PARTY_RECHECK`。
10. 只有原第三方明确给出两项CLOSED、无阻断后，才更新主持收口状态。若仍REQUEST_CHANGES，停在findings，不继续重建。
11. 实施前重新读取retention实际状态；12 run／8 GiB限额不放宽。当前历史值为12/12、8,032,729,057 B，只作起点，不预写实施时结论，不自动清理。

## 5. 限定收口

展示限定R01已实施并完成60/60验收，原第三方最终复验39/39、F01／F02均CLOSED、阻断0，C21在明确范围限制下收口。最终复验目录为`output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck/`；原REQUEST_CHANGES与R01送审时PENDING／false保留，由最终裁决承接。不启动C22、清理、Git或发布。
