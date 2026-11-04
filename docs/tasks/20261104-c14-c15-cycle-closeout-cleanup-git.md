# C14＋C15 周期收尾：A/B清理与Git闭包

- 日期：2026-11-04；主持：`new-provider/kimi-k3-1-pro-261024`。
- 用户本轮明确要求“先完成清理、Git和发布”。本任务据此执行A/B清理及Git提交／推送；公开发布目的地与内容须另行核实，不从Git推送推断公开上传授权。
- 状态：**A/B清理已完成，postcheck与删除后verify_full 17/17通过；Git收尾执行中，公开发布目标待核实**。

## 范围

1. C14四个run与C15四个run，共8个RETAINED run、reserved_bytes 5,281,820,700 B；12 run／8 GiB限额不变。
2. 仅处理transaction payload：A类同哈希存活副本；不同内容先进入新归档并通过全量校验及8件恢复抽样。无额外派生账本删除。
3. 新目录：`output/storage_retention/cycle_closeout_c14_c15_20261104/`；独立工作：`work/cycle_closeout_c14_c15_20261104/`；新脚本：`scripts/storage_retention/cycle_closeout_c14_c15_20261104.py`。
4. 保护当前正式pages、rules、正式账本、原始输入、全部审查证据、当前C14／C15／C15-R01成果与清单、机制交接包、run顶层元数据、pre_rebuild前像、G1归档和其他未列C类文件。
5. 顺序：plan→archive build/verify/restore→precheck→10件微批→全量执行→postcheck→删除后verify_full。失败保源，不静默跳过。

## Git边界

- 仅按实际diff与依赖显式添加C14、C15、机制优先方法／交接及本周期收尾的适宜源码、任务／进度／交接文档。
- 不批量暂存，不接管UI、参考分析、根目录`nul`／预览HTML或其他任务文件，不强制加入raw／work／output，不强制推送。
- 提交前核依赖、语法与必要回归；提交到main的已配置上游origin/main，记录实际commit与推送结果。

## 验收

- journal精确覆盖白名单，失败0；归档恢复、postcheck和删除后verify_full 17/17通过。
- 正式页／rules／账本／审查／G1与元数据前后不变；RETAINED 8/12→0/12，reserved_bytes归零，限额不变。
- 逻辑删除、归档体积和实测可用空间分别记录，不把归档动作当净释放。
- Git提交只含明确清单；公开发布未完成目标核实前不宣称已发布。
