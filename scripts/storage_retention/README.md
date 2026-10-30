# run 保留机制与只读盘点

2026-10-23 引入。初始授权范围：阻止后续大备份无限增长，盘点现有 run/work；不删除已有文件。后续用户单独授权的清理见本文末节，不改变默认只读策略。

## 自动生效的机制

`card_page_batch.py` 的 EXECUTE 路径在加载构建输入、写入任何正式页面之前调用
`scripts/character_skills/run_retention.py`。现有串行入口和并行驱动均生效，无须更换命令。

- 每个 output 独立管理 `_batch/retention/state.json`；首次真正重建时初始化。
- 默认最多 **12 个未释放 cohort run**、**8 GiB 备份预留量**，任一触顶即拒绝新重建。
  四 cohort 一轮时相当于最多三轮；子集 run 也占一个名额。全复用的 `--resume` 不占名额。
- 预约量为本次需要替换的已有 card.json/index.html/receipt.json/reuse_blocked.json 字节和，
  再加每卡 4 KiB 元数据余量。它约束新增旧版本备份，不包括当前 pages、旧历史、审查输出、
  work 独立脚本、失败的新 stage 文件或操作系统分配空间。run 数上限同时约束失败 stage 的积累轮数。
- 预约先落盘再构建，四 cohort 通过独占锁和原子替换共享账本，不超卖名额。
- 构建成功不自动等于审查通过；失败、中断、初始化错误均保留预约，防止失败重试绕过限额。
- 本机制不实现自动删除。已有历史 run 不搬迁、不删除，也不计入新增预算；清理候选另行列明。
- 达限会明确报错并返回非零；不取消签名或安全检查，不自动扩大预算、不覆盖旧报告。
  已启动的其他 cohort 可能继续完成，因此达限不是整轮事务回滚；并行驱动不会将失败整轮聚合为成功。
- PLAN_ONLY 仍可创建小型计划记录；报告/签名长期保留，本机制针对大副本，不声称整个目录零增长。

现有命令无需改变，例如：

```powershell
& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_batch_parallel.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --output output/character_skills/pages --execute --jobs 4
```

## 达限后的处置

1. 运行只读清单，检查当前 campaign/cohort 指针、未恢复失败、活动任务和审查引用。
2. 保留最近已验收完整 campaign 及正在复审基线；仅生成成功不能当作验收通过。
3. 对已闭合历史保存报告、签名、回执、来源/差异、审查结论；需长期重查的基线保留实际归档或
   可复建的准确代码/输入/依赖版本，不能只有哈希。归档应有内容校验与原路径映射。
4. 另获清理授权后处理指定 run 的 transaction payload。本文和清单不是删除授权。
5. 处理该 run 的 transactions 大文件后，以人工处置说明释放它的预算。此命令只改账本，不删除任何文件：

```powershell
& .\.venv\Scripts\python.exe -B scripts/character_skills/run_retention.py --pages output/character_skills/pages
# 以下仅说明将来的用法：需要真实 run 路径及已保存的审查/归档/清理处置说明。
& .\.venv\Scripts\python.exe -B scripts/character_skills/run_retention.py --pages output/character_skills/pages --release-run '_batch/ge60/runs/<run_id>' --evidence 'output/<task>/disposition.md'
```

release 检查 transactions 中只剩小型 backup/before.json、receipt.json（每文件不超过 64 KiB）
或空目录，以及处置说明存在；登记说明哈希和剩余元数据量，不会自动判断说明中的审批或审查结论真实性。
备份仍在时拒绝释放。保留 released 登记，禁止重用 run ID。只有未来登记的 run 能释放预算。
旧历史的整理仍按单独清单进行。若进程被强杀留下 reservation.lock，应先查其 PID 和活动写入，
确认没有写入者后由维护者处理；程序不按文件年龄擅自抢锁。勿删除/重置 state.json 绕过上限。

## 只读清理清单

```powershell
& .\.venv\Scripts\python.exe -B scripts/storage_retention/inventory.py --root . --out output/storage_retention/<new-report-id>
```

输出目录必须不存在，避免覆盖已有报告。清单包含每个 run、work 复跑子树及其余保留文件，
CSV/JSON 给出大小、条件回收上限、理由、具体文本引用及活动任务。work 分组互斥，不重复计算父子目录。
`pins.json` 显式保护历史验收基线：本次已核对 0b66de96… 的完整 pages/ledger 复跑成果及独立复验报告。
pin 是保留要求，不把历史通过解释为永远无缺陷；盘点时校验所钉 campaign 签名。具体清理必须遵守该保留清单。
使用 scandir 目录元数据，不逐字节读取 100+ GB 大文件；逻辑字节不等于真实磁盘回收量。
引用扫描只覆盖已声明的本地文档/脚本，不声称掌握所有聊天或动态引用。KEEP 不可按名单删除；
CANDIDATE/ARCHIVE_REVIEW/REVIEW_REPLAY 都有前置条件，不是直接可删承诺。

同一任务只更新 work 分类时，可显式传 `--reuse-runs-from <此前报告目录>` 复用历史 run 测量；
程序检查项目根、run 目录集合和当前指针不变，保留原测量时间及分类，不重新声称旧大文件已复测。
正式删除前应不带此参数完整重扫。目录连接点不跟随，避免重复计数或递归触及原件；跳过项均记入 scan_issues.json。

## 验证与边界

```powershell
& .\.venv\Scripts\python.exe -B scripts/storage_retention/test_retention.py
& .\.venv\Scripts\python.exe -B scripts/storage_retention/test_inventory.py
```

测试在新建 work/storage_retention_20261023/test-* 中运行，不触碰正式 pages。
包含字节/数量边界、四进程争用两个名额、失败预约保留、锁不被抢、释放前置条件、路径逃逸、
真实 batch 命令在加载构建输入前拒绝超预算请求。fixture 清理仅针对测试自己新建的临时目录。

修改编排代码会影响已有 source_signature。现有正式 pages 的回执仍对应历史代码版本；
本任务不为修改保留机制全量重建页面，也不更改/豁免回执。下一次有实际需求的正式重建自然产生新签名。
同一 cohort 仍须单写者；本机制协调容量预约，不替代正式页面的并发写入隔离。

## 2026-10-23 单次授权清理

用户后续授权核查原 v3 清单中的 119 个普通旧 run 和 18 个 work 复跑目录，
仅对审查闭合且无活动依赖的部分执行清理。149 个有历史引用的 run 排除在外。
`cleanup_20261023.py` 是这次固定范围的处置工具，不是通用自动清理入口。

- `--prepare` 只生成逐文件计划、闭合证据和保留理由；不删除文件，也不覆盖已有计划。
- 执行需要该计划的准确 SHA-256；逐文件检查绝对路径、连接点、大小、时间与内容哈希。
- 仅删除白名单中的重复产物；保留目录、报告、签名、回执、来源记录和独立审查证据。
- 正式指针、所有 run 顶层元数据及当前/历史验收基线回执在前后进行哈希核对。
- 记录成功删除日志和卷可用空间变化；存在执行日志时拒绝直接重跑，部分失败必须先核对日志。
- 近期整改仍活动，核查决定保留其中 24 个 run 和 1 个复跑目录；其余 95 个 run、17 个 work
  只处理列明的重复产物。没有 payload 的 run 不会产生删除记录。

本次计划与最终结果入口：`output/storage_retention/cleanup_20261023/`。
原盘点报告仍是清理前的历史测量，后续盘点应使用新的输出目录。
