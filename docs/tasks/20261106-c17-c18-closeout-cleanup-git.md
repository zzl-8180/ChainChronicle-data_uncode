# C17＋C18 清理与Git收尾任务卡

- 日期：2026-11-06；用户明确“同步完成清理和Git推送”。
- 状态：**归档恢复验证、A/B清理、postcheck及删除后verify_full已完成；Git提交／推送待执行**。
- 清理回执：`output/storage_retention/cycle_closeout_c17_c18_20261106/README.md`。

## 已完成边界

- 8个retained run（C17／C18各4）仅处理transaction payload `card.json/index.html`。
- 8,944件payload全部有live或归档survivor；50个不同路径、46个唯一内容已归档并恢复8件样本。
- B类派生清理0；run元数据、pre_rebuild、正式pages/rules/ledger、原始输入、成果、审查、联合第三方和G1保留。
- RETAINED 8/12→0/12，reserved_bytes 5,290,260,425→0，限额未放宽。
- postcheck全部通过，verify_full 17/17通过；C18 campaign未改。

## Git范围

- 仅显式暂存C17／C18生产模块与共享生成器、任务文档、联合第三方接收文档、C19方向评估、清理脚本与当前交接。
- 不暂存参考分析、UI样稿、`.zcode/plans/`、`nul`、根目录预览HTML或其他未跟踪杂项；不对`output/`、`work/`、`raw/`强制加文件。
- output中的大型正式产物、缓存、归档、清单和审查证据不因此入Git；其取得／重建方式仍由任务文档说明。
- 先检查cached清单和差异，再提交推送；不force-push，不提交他人改动。

## 后续C19边界

C19仅完成方向评估，不随收尾自动实施。推荐五项父层1095非Y.G.攻击绑定为候选方向；7687跨槽、缺上游或其他机制不并入。正式实施需用户确认具体范围，并重新执行候选独立审查、合并预检及唯一一次正式生成。
