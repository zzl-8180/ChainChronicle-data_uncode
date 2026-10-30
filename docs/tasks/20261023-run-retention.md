# 历史 run 保留上限与只读清理清单

- 负责人：本 Codex 对话；状态：已完成（2026-10-23，本地交付；未删除已有文件）。
- 授权：修改历史 run 保留机制，列出现有 run/work 清理清单；不删除已有文件。
- 写入：`scripts/storage_retention/`、`scripts/character_skills/run_retention.py`、`scripts/character_skills/card_page_batch.py` 的运行准入接点、`output/storage_retention/20261023/`、`work/storage_retention_20261023/`、本任务卡。
- 并行边界：不修改 effect_ledger/render/verify、正式 pages、根交接、其他任务记录。batch 已有并行驱动和字段改动原样保留；仅增加运行前容量准入。
- 设计：新 run 共享容量账本，默认最多 12 个未释放 run、8 GiB 预留备份；超限在正式页面写入前报错，无自动删除。历史 run 不迁移、不删除、不计入新增预算；报告另列实际历史占用。失败/中断保守保留预约，不自动释放。报告/签名长期保留；后续归档并处理 payload 后可显式释放预算。
- 验证：隔离目录容量边界、并发预约、失败保留、旧文件不变、入口接入；清单计数与分类对账。不会为工具签名变化重建 2236 页。
- 交付入口：`output/storage_retention/20261023/README.md`；最终逐项清单 `inventory_v3/{runs,work}.{csv,json}`，`validation.json` 记录测试及源码哈希。v1/v2 为本轮中间报告，未覆盖。
- 实际机制：串行入口最小接入，现有并行驱动自动受控；默认 12 个未释放 cohort run / 8 GiB 新增旧备份预留量，共享原子预约。无自动删除，达到上限拒绝对应重建；失败/中断保持预约。后续处理 payload 并留处置说明后可仅释放预算，小型 before/receipt 元数据仍保留。
- 实测：287 run 136.327 GiB，work 37.477 GiB。普通旧 run 候选 119 个/52.238 GiB；有历史引用、须先归档处置 149 个/70.207 GiB；work 复跑/沙箱候选 18 个/14.051 GiB。合计条件回收毛上限 136.495 GiB，不是即刻可删或净回收承诺。19 个 run 当前/近期/恢复材料保留；历史曾通过的 0b66de96… 实存 pages/ledger 基线另 pin 保留约 2.66 GiB。
- 验证：8 项容量/并发/失败/真实入口测试 + 3 项清单/基线 pin 测试通过；互斥计数、汇总、当前指针对账通过。14 个目录连接点跳过，其他扫描错误 0。v3 复用 v1 run 测量（复核 run 集合/指针），重新扫描 work。正式 pages、已有 run/work 文件零删除，正式 retention state 尚未创建（下次实际重建初始化）。
- 注意：修改编排源码改变未来 source_signature；现有页面仍是原签名版本，不伪造回执、不为工具改动全量重建。容量限制按输出目录生效，不约束其他独立 work 脚本。预算是旧备份预留，失败新 stage 由 run 数限额间接约束；跨 cohort 不承诺整轮回滚。既有 Git 未提交改动保留，本任务未提交。
- 下一步：用户审阅清单。实际清理须另获授权，并完整重扫、确认活动写入与基线归档；本任务不执行删除。
