# 任务卡：四 cohort 重建并行化（card-page parallel cohort）

- 日期：2026-10-23；负责人：并行重建改进员（自动工作流子代理，GLM 5.3 Flash 260828）
- 状态：已完成（沙箱等价证明 + 速度实测 + 正式 pages 零触碰）
- 授权边界：`scripts/character_skills/`（card_page_batch.py 最小可选参数 + 新增并行驱动）、`work/character_skills_parallel_cohort/`、本任务卡。effect_ledger.py / rules.json / 正式 pages/ / 旧报告 零改动；无 git 提交。

## 1. 目标

把每批最频繁的单段耗时——四 cohort（ge60 34 / 40to59 290 / 20to39 436 / remaining 1,476 张）串行重建——并行化，墙钟显著下降，且输出与串行**逐字节一致**（card.json / index.html / campaign 签名 / 29 项依赖哈希；运行标识字段差异显式列出并证明下游免疫）。

## 2. 顺序假设审查（跨 cohort 共享态清单）

| 共享态 | 结论 |
|---|---|
| `pages/<cid>/{card.json,index.html,receipt.json,reuse_blocked.json}` | cohort 私有：manifest 四 cohort 严格划分 2236 唯一 cid（`card_page_cohorts.py:21-23` 断言），并行进程绝不写同一卡目录。事务/回滚（`card_page_write.py:37-72`）全部在卡目录内 |
| `_batch/<cohort>/runs/<stamp>/`、`card_latest/`、`latest.json`、`plan_latest.json` | cohort 私有目录；run stamp 含 uuid4 后缀（`card_page_batch.py:129`），无碰撞 |
| `Inputs.__init__` 的 `os.chdir(root)` 与模块级全局 `C.ROOT/R.DECODED/CARD_COMPARISON`（`card_page_data.py:455-457`） | 进程全局态 → **必须子进程并行，禁止线程**。驱动按此实现 |
| 失败路径 `failures/<cid>.json`、`--resume`（`reusable()` 读卡目录 receipt，`card_page_write.py:27-34`） | cohort 私有，语义不变 |
| **`_batch/campaign_latest.json`（唯一跨 cohort 共享写）** | `campaign()`（`card_page_batch.py:83-117`）在每次 run 末尾读其他三 cohort `latest.json` 指针并聚合写回——并发会读到半写指针且终态取决于完成顺序。改造：`--defer-campaign` 剥离子进程，由驱动在全部 cohort 成功后单写者调用**同一 campaign() 函数**聚合；聚合遍历 `m['cohorts'].items()`（manifest 顺序，`card_page_batch.py:86`），与完成顺序无关 |
| campaign 报告宿主 run 目录 | 串行终态 = 最后执行的 cohort（remaining）的 run 目录。驱动默认 `--campaign-host-cohort remaining`（=manifest 顺序最后一个选中 cohort），复现同一终态 |
| `source_signature` | 各子进程开始时独立从 `source_paths()` 一次性读取（`card_page_batch.py:131`），只读，与并行无关（与主持调研一致） |
| entry_pages 一致性检查（campaign 内，`card_page_index.py:198`） | 只读 pages/index.html、all_cards.html |

## 3. 实现（改动清单）

1. `scripts/character_skills/card_page_batch.py`（最小可选参数，串行默认行为逐字节不变）：
   - `--defer-campaign` 旗标（argparse，main()）+ run() 末尾 `if not getattr(args,'defer_campaign',False): campaign(...)`（含注释）。`getattr` 缺省 False 保证程序化调用（如 `card_page_r2_fixes_check.py` 的 SimpleNamespace）兼容。
   - git diff 中其余差异为接手前既有 R1 整改工作区状态（card_page_batch.py 接手时已是 M），非本任务改动。
2. `scripts/character_skills/card_page_batch_parallel.py`（新增驱动，~120 行）：
   - 每 cohort 以 `subprocess` 调用**未改动的串行入口** `card_page_batch.py --defer-campaign`（`sys.executable -B`）；
   - 调度：按 cohort 规模降序（remaining→20to39→40to59→ge60），`--jobs` 个并发槽（ThreadPoolExecutor 仅管理子进程等待，无共享 Python 态）；
   - 全部成功后：校验四 cohort 签名一致 → 读取宿主 cohort（默认 remaining）run 目录的 cohort_report.json → 调用 `card_page_batch.campaign(out,m,signature,host,report,host_dir)` 单写者聚合（复用串行实现本身，零逻辑复制）；
   - 任一 cohort 失败：**不聚合**（避免把 STALE/部分签名集写进 campaign 指针），打印 `COHORT_FAILED` JSON 退出 1；`--resume` 重跑同一命令即可按 cohort 复用成功卡重试失败卡。
3. 串行入口完全保留为回退：原命令一个字不变仍可用（不带新旗标时行为与历史逐字节一致）。

## 4. 沙箱等价验证（实测）

命令与产物均在 `work/character_skills_parallel_cohort/`：
- 串行基线：现行串行入口四连跑 → `sandbox_pages_serial/`（`serial_*.stdout.json`）
- 并行：`card_page_batch_parallel.py --execute --jobs 4` → `sandbox_pages_par4/`；`--jobs 2` → `sandbox_pages_par2/`
- 比对器：`compare_outputs.py` → `equivalence_serial_vs_par4.json`、`equivalence_serial_vs_par2.json`，两者 **equivalent=true**：

| 项 | serial vs par4 | serial vs par2 |
|---|---|---|
| card.json+index.html 逐字节 | **4,472/4,472 identical**（含 30236），0 差异 0 缺失 | 同 4,472/4,472 |
| receipt 语义 | 2,236/2,236 除 run_id 外全字段相等、files 哈希相等、status=SUCCESS | 同 |
| signatures.json（29 项依赖声明+签名组成） | 四 cohort 全部逐字节相同（sha 46565538dd16df1e…） | 同 |
| campaign 签名 | 相等：`c19b4d6efb832c6a…` | 同 |
| campaign_report.json 归一化（剥运行标识） | 完全一致；campaign_audit_queue.json **逐字节**一致 | 同 |
| cohort_report.json 归一化 / latest.json 指针 | 归一化一致；指针差异仅 run stamp | 同 |
| card_latest/<cid>.json 归一化 | 0 失配 | 同 |

**运行标识类差异清单（预期、且证明下游免疫）：**
- `receipt.run_id`（每卡）＝所在 cohort run stamp；verify_full 第 1 项核对 receipt.run_id == 该 cohort latest 指针所指 run（`card_page_verify_full.py:616-617`）——并行下同 cohort 的 receipt 与指针由同一子进程写出，自洽；
- `_batch/<c>/latest.json`、`_batch/campaign_latest.json` 指针路径中的 stamp：所有消费者（card_page_index.load_campaign_metrics、verify_full、effect_ledger 的 campaign 签名读取、`scripts/release/build_skill_values_bundle.py:129-142`）均为**指针跟随**，不比较 stamp 文本；
- `campaign_report.cohort_snapshots[].report` 路径、`cohort_report.seconds`、plan.run_id/run_directory：同为 stamp/计时类，聚合内容（coverage/summary/queue/failures）与完成顺序无关（campaign 遍历顺序固定）；
- 沙箱 campaign 签名 `c19b4d6e…` ≠ 正式 pages 当前签名 `a470c054…`：因本任务在 `card_page*.py` glob 内新增/修改代码（`card_page_dependencies.py:7` 的 source_paths 把 card_page_batch_parallel.py 计入 source_signature）——签名反映「当前代码+当前输入」，属预期；等价命题是「同代码同输入下 串行==并行」，已证。
- 入口两页：生成时内嵌当前 campaign 指针路径（stamp 类）。沙箱入口页 vs 正式入口页 stamp 归一化后逐字节一致（index.html 与 all_cards.html 均 normalized identical）。

**verify_full 17/17 PASS（并行沙箱 par4）**：
`./.venv/Scripts/python.exe -B scripts/character_skills/card_page_verify_full.py --root . --pages work/character_skills_parallel_cohort/sandbox_pages_par4 --out work/character_skills_parallel_cohort/verify_full_par4_sandbox.json` → 判定 PASS，17 项全 PASS（receipt_signature 2236、artifact_hashes 4472、dependencies_29、rows_rowids 41,665 行、source_dereference 72,086、inference_source_coverage 30,287（无遗漏推断答案）、inference_value_equality 12,871、chip_evidence_colors 41,665、campaign_reconciliation、entry_pages CURRENT、r1_hp_branch_binding 8、r2_completion_recompute、ledger 五项、page_ledger_unresolved_sync）。
- **账本对账项直接以并行沙箱过检**：沙箱 card.json/index.html 与正式逐字节一致 → `output/character_skills/effect_ledger`（按正式 pages 重建）与沙箱 pages 行集合/答案引用/未解决区完全可解析，无需降级论证。入口页检查通过方式：沙箱内以 art 目录联接（mklink /J，只读指向正式 art）+ README 副本生成沙箱入口页（card_page_index.py 自检通过后写入）。
- 官方锚点：同日 `verify_full` 默认路径对正式 pages 亦 PASS（报告 `work/character_skills_parallel_cohort/verify_full_official_anchor.json`）。

## 5. 速度实测（同机同代码：16 逻辑核 / 32GB RAM / Windows；冷启动各沙箱，无复用）

| 执行方式 | ge60 | 40to59 | 20to39 | remaining | 总墙钟 | 加速比 |
|---|---|---|---|---|---|---|
| 串行（4 连跑） | 15.6s | 82.3s | 72.9s | 87.1s | **258.0s** | 1.00× |
| 并行 --jobs 2 | 13.7s | 69.6s | 69.0s | 94.5s | **139.4s** | **1.85×** |
| 并行 --jobs 4 | 15.6s | 81.9s | 72.9s | 96.6s | **97.5s** | **2.65×** |

- 并行行各 cohort 时间为并发下子进程墙钟（有 CPU/IO 争用，单 cohort 变慢属预期）；总墙钟为驱动实测（含 campaign 聚合 0.46s）。
- 注意：本次实测机器处于热缓存、无其他负载，绝对值低于主持调研估计的 15–25 分钟（该估计大概率含更冷 IO / 不同负载）；加速比比绝对值更可迁移。jobs=4 时 remaining（最大 cohort）成为下限（~97s），继续加并发无收益；jobs=2 波次调度下限同样由 remaining 决定。
- 负载注意：并行度为 N 时约 N 份 Python 进程同时持有解码表与 records.jsonl 过滤视图（单进程数百 MB 级）；重建窗口内避免同时跑 verify_full / 账本重建等重 IO 任务。

## 6. 使用说明与回退

- **何时用并行**：常规全量重建（无 card_page*.py 代码改动风险时）——`--jobs 4`；机器有其他负载时 `--jobs 2`。
- **何时必须串行或先定稿代码**：代码热修窗口（「重建窗口内零 card_page*.py 改动」纪律继续适用——先定稿全部代码，再一次性并行重建）；单 cohort 调试/子集验证仍直接用串行入口 `--cohort <c> --cid ...`（驱动不支持 --cid 子集）。
- **回退路径**：串行入口不变；并行驱动失败或对结果存疑时，用原串行命令重跑即可（`--resume` 复用同签名产物）。
- 正式 pages/ 本次零触碰证明：`official_pages_before_hashes.json` vs `official_pages_after_hashes.json`——7 个指针锚点 + 2,236×3（card.json/index.html/receipt.json）哈希前后全等，且期间官方锚点 verify_full PASS。

## 7. 风险与限制

- 驱动失败路径与串行的差异：串行下单 cohort 失败仍会执行 campaign()（带 STALE 快照）；并行驱动**跳过聚合**以防错误指针。全成功路径输出等价已证；失败路径属运维语义，选择更保守方向。
- 驱动不支持 `--cid` 子集（保持简单；子集走串行入口）。
- 并行进程同时 `mkdir` 中间目录（parents=True）在 Windows 下安全；run stamp 含 uuid 防碰撞。
- 沙箱入口页生成需要 art/README 副本，仅用于 verify_full 第 10 项；正式流程中入口页刷新仍按原纪律由 card_page_index.py 单独执行（重建后）。
