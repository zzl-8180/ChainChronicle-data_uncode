# 第二批剩余5个previous：条件性清理资格评估

结论：五项当前身份/正式入口/数据样本检查无异常，可作为**有条件的清理候选**；存在真实旧现场检查依赖，不能称完全无依赖。用户本轮只要求评估，不授权删除；此前221项删除许可已履行，不覆盖这5项。弱推理Sol检查、Astra独立复核，本轮不影响或停止主线。

## 精确路径

以下为完整绝对路径；对象ID、tag、raw target和正式入口对照见[条件候选JSONL](conditional-candidates.jsonl)与[原始清点CSV](inventory/assessment.csv)。

- `E:\代码项目\锁链战记数据解包\work\c14_delivery_20261103\impl\isolation_input\output\cache_full_20261015_v2.batch2-20261108-previous`
- `E:\代码项目\锁链战记数据解包\work\c15_delivery_20261103\impl\isolation_input\output\cache_full_20261015_v2.batch2-20261108-previous`
- `E:\代码项目\锁链战记数据解包\work\c16_delivery_20261104\impl\isolation_input\output\cache_full_20261015_v2.batch2-20261108-previous`
- `E:\代码项目\锁链战记数据解包\work\c17_delivery_20261106\impl\isolation_input\output\cache_full_20261015_v2.batch2-20261108-previous`
- `E:\代码项目\锁链战记数据解包\work\c18_delivery_20261106\impl\isolation_input\output\cache_full_20261015_v2.batch2-20261108-previous`

五个旧入口均指向原`E:\代码项目\锁链战记数据解包\output\cache_full_20261015_v2`；该旧目标现已不存在。五个正式入口（去掉`.batch2-20261108-previous`后缀）指向仍须保留的新数据根`E:\代码项目\锁链战记数据解包\projects\unpack\data\cache\cache_full_20261015_v2`。

## 依赖分开看

| 依赖类别 | 已确认情况 | 清理时的要求 |
|---|---|---|
| 主线/数据读取 | 未发现主线生产读取这五个previous；v2数据及正式入口仍是独立可用资料入口 | 正式入口与整个新v2数据根保留，不因旧入口可清理而删除数据 |
| 旧第二批现场验收/恢复 | `scripts/project_layout/batch2_directory_move.py`对previous做lstat及原ID/raw target核验，progression和verify覆盖五项；原runbook/recovery.md亦要求previous存在 | 删除会破坏这项原现场必要前提，相关旧检查不能再按这项前提原样复跑 |
| 审查与冻结证据 | 原第二批成功回执、migration-files/WAL/binding、P/v7及旧历史plan均保留；限定检索未发现精确五对象pin | 不改旧脚本/报告/签名来把现场变化隐藏成原检查仍通过 |

具体源码行与分类见[dependencies.json](inventory/dependencies.json)。本轮没有运行旧gate/verifier，也不保证它们在当前新布局的其它条件本来全部满足；仅确认“原previous对象存在且身份不变”确是静态必要条件。历史成功回执仍是当时状态的有效证据，不因未来清理而改写。

## 必须继续保留的条件

1. 若仍需要保留上述原现场前提、检查原previous身份，或保留原联接物理对象作回退证据，则五项继续保留。
2. 若接受退役这些原对象及依赖它们的旧现场检查前提，才可另行明确授权精确清理五个联接对象；原文件ID不可原样恢复。现时五项技术异常HOLD数0不等于无条件批准删除。
3. 真正物理回退仍须先根据回执恢复/逆搬材料并验真，再创建或适配入口；新建联接是新ID，不能盲指已经迁空的旧根。
4. 将来若发现ID/tag/raw target或正式入口漂移、旧目标被新任务重建、实际消费者正使用这些历史入口，暂停相关项并保留现场；不能只凭“previous”后缀删除。

## 不得动的范围

- 五个现行formal入口及新v2整棵数据树。
- 21个相关普通父目录/祖先、六个P2B5原独审对象及其只读承接路径。
- 原第二批迁移/恢复/验收回执、原plan/binding、P/v7、已完成221清理的全部证据、当前主线代码/配置/规则/答案/正式页及所有未列对象。

精确保留路径和身份见[preserve.json](inventory/preserve.json)。不把更早只读计划或旧迁移许可转成删除权，不复用已结束迁移窗口；只读评估不需要主持停工或再次交接。

## 实际验证与限制

复核五个previous原ID/tag/raw、五个formal迁后身份、新v2根原ID、next缺失，均一致。读取原第二批三份代表样本共180,040字节并核ID/SHA，未重哈95文件或整个118MB数据。本轮是有限范围、时点观察，字面引用/保护检索不是全机动态消费者或无句柄证明。

移除这五个入口可释放游戏数据载荷0B，只有少量文件系统元数据可能回收/复用，实际可用空间增量未知；不得按目标数据大小估算。

当前删除数0、联接/目标/正式入口/根导航/主线修改0，未提交或推送。
