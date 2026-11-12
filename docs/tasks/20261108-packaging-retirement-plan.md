# 打包支线退役：逐文件清单与门槛

状态：**Sol 清单完成，主聊天独立验收通过；未执行删除**；2026-11-08。负责人：Sol 独立清单子任务，主聊天验收与整合。

目标：只读盘点旧打包执行代码、包、隔离现场与六个旧复现目录，列出逐文件删除候选、保留及 HOLD，核对空间上限与外部引用门槛。本轮不删除、移动、运行打包或修改业务代码。

允许写入：本任务卡与 `docs/project-layout/20261108-packaging-retirement-v1/` 下的新规划文件。其他路径（含共享根、B00/B01-R 基线、正式角色成果与存储保护证据）只读。与其他任务并行，不撤销或覆盖其改动。

已读入口：`AGENTS.md`、`HANDOFF.md`、`docs/project-layout/20261106/` 的路径审计、`docs/project-layout/20261107-b01-v1/` 及对应任务卡。当前主线的生成／续跑／校验／账本不依赖打包支线；历史对账、发行复现和旧清理重放另列边界。

共享依赖：参考分析脚本仍读取旧 data ZIP 的成员表；旧 handoff payload 关联历史接收／清理重放。删除门槛须分组注明。

结果入口：[`README.md`](../project-layout/20261108-packaging-retirement-v1/README.md)、[`delete-candidates.jsonl`](../project-layout/20261108-packaging-retirement-v1/delete-candidates.jsonl)、[`retain-and-hold.jsonl`](../project-layout/20261108-packaging-retirement-v1/retain-and-hold.jsonl)、[`inventory-receipt.json`](../project-layout/20261108-packaging-retirement-v1/inventory-receipt.json)、[`analysis-data-central-directory.json`](../project-layout/20261108-packaging-retirement-v1/analysis-data-central-directory.json)。九树 6,788 文件／5,037,311,179 B；候选 28／2,061,279,175 B；RETAIN 4,763／81,107,363 B；HOLD 1,997／2,894,924,641 B。全部候选仍有门槛，其中旧 data ZIP 被参考分析消费者阻断。没有读大文件全量哈希、改旧脚本、打包或物理删除。

验收：主聊天独立遍历九树，确认 6,788 路径精确覆盖、无重复、现存元数据一致；旧 ZIP 的 596 个中央目录成员及三项参考字段完全一致；15 个选定保护文件哈希未变。详见 [acceptance.json](../project-layout/20261108-packaging-retirement-v1/acceptance.json)。验收修订明确 handoff 候选只有 ZIP，保留 payload 不需改主线／旧保护清单。后续各门槛按本清单处理，物理删除另行执行；HOLD 不在删除范围。参考分析实际消费者仍未修改。
