# C19 清理与Git收尾任务卡

- 创建：2026-11-07；用户明确“复审通过，现在完成清理和Git推送”。
- 主持：`new-provider/kimi-k3-1-pro-261024`。
- 状态：**A/B清理、postcheck与删除后verify_full 17/17已完成；Git提交／推送进行中，不启动C20或发布**。
- 清理实现：`scripts/storage_retention/cycle_closeout_c19_20261107.py`；输出`output/storage_retention/cycle_closeout_c19_20261107/`；恢复工作目录`work/cycle_closeout_c19_20261107/`。

## 清理边界

1. 仅处理当前4个C19 retained run的transaction payload `card.json/index.html`，保留run顶层与transaction元数据、pre_rebuild前像和未列出的全部内容。
2. 起点须为RETAINED 4/12、reserved_bytes 2,645,358,782；12 run／8 GiB限额不变。
3. 同哈希live survivor可直接作为存活副本；不同内容先归档、全量读回校验并恢复8件样本。10件微批删除→precheck→全量白名单删除→postcheck→删除后verify_full。
4. B类派生清理0，C类全部保留；正式pages／ledger／rules、原始输入、候选、成果、独立审查、原方向审查、R01复核及G1不改。
5. 任一项来源、存活副本、恢复样本或保护文件不符即停止，不扩大清单，不释放未完成清理的预约。

## Git边界

- 仅显式暂存C19生产模块、共享接线与成果生成器、本周期任务文档、清理脚本和当前交接。
- 不暂存`AGENTS.md`的其他改动，不接管参考分析、UI、project-layout、`.zcode/plans/`、`projects/`、`nul`、根目录预览HTML或其他未跟踪文件。
- 不使用`git add .`，不对`output/`、`work/`、`raw/`强制加文件；大型产物和归档保留在本地成果目录，不因Git体积限制无记录删除。
- 提交前核对cached清单和差异；只推送`main`，不force-push，不发布Release。

## 完成条件

RETAINED 4/12→0/12、reserved_bytes归零、journal失败0、postcheck与verify_full通过；随后更新回执和当前交接，显式提交并核对`origin/main`。最后总结C19实际收益及限制，不自动启动下一周期。
