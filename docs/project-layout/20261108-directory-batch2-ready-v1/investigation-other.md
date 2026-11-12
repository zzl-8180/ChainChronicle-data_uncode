# 第二批：四处采集／补采目录的有界独立调查

结论：本次四个目录均不作为未经适配即可整树迁移的新增项。第二批可继续按 Sol 对 single／v2／decoded／export 的独立结论准备；不要为了多搬目录扩大主线依赖面。本调查不要求主持再次交接或停工，也不对 Sol 范围提前给准入。

| 目录 | 实际文件／字节 | 本批结论 |
|---|---:|---|
| output/phone | 13／16,009,387 | 排除：现存采集、有限解码、field guide、export、trace、阶段验收仍硬编码读写旧路径 |
| output/phone_full_20261015 | 5／44,162,287 | 排除：分析／快照验收硬编码读取，v3 manifest 绑定 extraction 报告 |
| output/phone_refresh_20261015 | 9／34,939,444 | 排除：采集／补采核对入口及 cache_refresh manifest、相对说明共同引用 |
| output/cache_refresh_20261015 | 90／129,779,325 | 明确排除：含77份decoded、组合清单和记录视图，是 latest 及 full_unpack／图片追踪输入，不是独立报告树 |

四树结构检查均未发现 reparse；这里只统计目录、文件和大小，没有全量内容重哈希。前三树将来可考虑完整搬迁，但必须先有明确的外部路径解析或旧路径兼容契约，覆盖实际读写者及冻结引用；本轮未提出或创建新联接、未改消费者。旧 v1 的准入依据是未发现明确运行消费者，这一事实不能套用到三处 phone 树。

## 直接证据

- 当前代码：`scripts/analyze_cache_snapshot.py:158-159`、`verify_cache_snapshot.py:19`、`build_field_guide.py:156-161`、`export_master.py:243`、`sample_trace.py:195`、`verify_phase_b.py:21-26`；均保留具体旧路径读者。
- 当前写者／历史重跑入口：`cache_probe.py`、`phone_collect.py`、`bounded_decode.py`、`collect_cache_refresh.py`、`verify_cache_refresh.py`。未运行这些入口，尤其不自动连接手机或重放旧采集计划。
- v3 `manifest.json/input_versions` 绑定 `output/phone_full_20261015/extraction/extraction.json`；cache_refresh manifest 的 inputs 绑定 phone_refresh 四个文件，旧记录字节不应为目录整理重写。
- `cache_refresh_latest.json` 仍指向补采数据树；`full_unpack_run/probe/merge/verify/finalize` 与两处图片定位代码消费其 `composite_inventory.jsonl`。
- 复用既有1140映射、耦合报告及两个压缩引用索引；索引中的退役 share_bundle 路径只当历史线索，不冒充当前运行消费者。当前关键代码和小manifest已直接读取。

## 第二批执行前准入框架

1. 固定选定根、目标及必要消费者差异；其余候选明确排除。主线 v3/latest、rules/pages/ledger、原件、既有归档和冻结证据只读。
2. 准备精确清单、最小导航／消费者补丁和只读预检；检查词法祖先、reparse、同卷、身份、目标缺失与冲突，绑定清单及工具SHA。必要内容验真限实际批次，不重验无关大归档。
3. 执行器仅按清单同卷整目录 rename，无copy/delete；逐项持久化INTENT/DONE，紧邻操作再核身份和目标。漂移停在可审状态，不自动盲回滚、不要求主线全局停工。
4. 后验新树精确集合和内容／身份、源缺失及小保护锚点；核导航实际可读。静态依赖检查不宣称全机无句柄。
5. 主持问题仅由root合并到最多一次交互；本调查四树排除已足够，无新增必问问题。

机器可读范围、证据和当前小锚点见 [investigation-other.json](investigation-other.json)。本轮只写本说明和JSON，不迁移业务、不改共享根、不提交／推送。
