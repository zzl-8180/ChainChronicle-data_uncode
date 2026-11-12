# 本轮实测盘点


日期：2026-11-13。用途是支持实施方案，**不是可删除白名单**。

本页为独立元数据扫描结果。按用户补充使用的 [WizTree 统计](WIZTREE.md)另列逻辑大小、分配空间及两种口径的差异；后续目录容量展示优先查该页。两者都已完成，无后台扫描待办。

普通文件路径 **2,098,061**，逻辑大小 **183.386 GiB**（196,908,965,415 B）；普通目录 1,265,681，另登记 29,637 个重解析点，扫描错误 0。

## 口径与边界


- 扫描整个工作区，包括 Git 忽略项、.git、本地环境和工具；排除本次扫描器及报告目录，避免自计。扫描跨时间进行，不是冻结快照；执行清理前需复核候选。

- 不跟随 junction／符号链接；链接目标未在本树普通目录中出现时，其载荷不计入。本树内同文件的硬链接路径仍可能重复计数。

- 本次只读元数据，未测分配空间、压缩和硬链接去重，未读取全部文件内容或全量哈希。Windows DirEntry 返回的 0 文件 ID／链接数表示未知，不证明唯一文件或共享关系。

- 目录总量是逻辑字节，不是物理占用或删除收益；父子表分别展示，不跨表相加。已读关键入口、事故、迁移、清理回执及相关配置，没有声称逐文件语义审查完成。

- UTC 扫描区间：`2026-11-12T16:34:45.571418+00:00` 至 `2026-11-12T16:50:37.789559+00:00`。用户日期按 Asia/Shanghai。

## 全树一级目录


| 目录 | 普通文件数 | 逻辑 GiB |
|---|---:|---:|
| `output` | 929,224 | 101.474 |
| `work` | 190,495 | 49.879 |
| `projects` | 917,063 | 24.159 |
| `raw` | 36 | 3.804 |
| `其他人的参考` | 45,061 | 3.303 |
| `docs` | 4,681 | 0.280 |
| `.git` | 3,645 | 0.128 |
| `.venv` | 1,482 | 0.116 |
| `operations` | 5,335 | 0.101 |
| `[root files]` | 12 | 0.090 |
| `tools` | 15 | 0.024 |
| `scripts` | 604 | 0.022 |
| `.zcode` | 406 | 0.006 |
| `skill参考` | 2 | 0.000 |

## 容量最大的二级目录（最多 25 项）


| 目录 | 普通文件数 | 逻辑 GiB |
|---|---:|---:|
| `output/character_skills` | 928,138 | 93.195 |
| `projects/assets` | 903,504 | 20.317 |
| `output/storage_retention` | 954 | 7.744 |
| `raw/phone_20261015_full_02` | 5 | 3.692 |
| `work/phone_20261015_full_02` | 68,828 | 3.628 |
| `work/character_skills_recheck_rectification` | 13,483 | 3.463 |
| `work/rule_registration_20261028` | 4,618 | 2.783 |
| `projects/unpack` | 861 | 2.070 |
| `work/storage_recycle_g1_20261027` | 4,891 | 1.798 |
| `其他人的参考/claude_cc_site_pages 20261023` | 15,644 | 1.703 |
| `work/type67_20261028` | 2,376 | 1.369 |
| `work/c21_delivery_20261111` | 3,300 | 1.349 |
| `work/reader_incremental_sync_20261111` | 4,870 | 1.211 |
| `projects/skill-research` | 3,575 | 1.120 |
| `work/character_skills_inference_inventory` | 11 | 1.097 |
| `work/character_skills_rectification_r2r3` | 92 | 1.084 |
| `work/c7_p1_ledger_opt` | 105 | 1.065 |
| `work/polish_20261020` | 4,482 | 1.063 |
| `其他人的参考/claude_cc_site_pages` | 8,933 | 0.888 |
| `work/reader_v01_fixtures_20261107` | 5,248 | 0.882 |
| `work/kill_mana_20261029` | 501 | 0.724 |
| `work/mana_isolated_repro_20261026` | 1,904 | 0.703 |
| `work/kyoumei_isolated_repro_20261026` | 1,871 | 0.694 |
| `projects/reader` | 9,029 | 0.640 |
| `work/s5_terrain_20261026` | 117 | 0.605 |

## 正式技能树内部（与上表重叠，不能相加）


| 目录 | 普通文件数 | 逻辑 GiB |
|---|---:|---:|
| `output/character_skills/pages` | 629,042 | 45.742 |
| `output/character_skills/review` | 278,261 | 37.582 |
| `output/character_skills/c7_p3_20261030` | 2,368 | 1.610 |
| `output/character_skills/c7_p1_20261029` | 108 | 0.820 |
| `output/character_skills/c7_p2_20261030` | 96 | 0.805 |
| `output/character_skills/c8_p1_20261030` | 71 | 0.793 |
| `output/character_skills/cycle_reports` | 234 | 0.624 |
| `output/character_skills/reader_v01_validation_20261107` | 2,506 | 0.436 |
| `output/character_skills/reader_full_20261106` | 2,498 | 0.406 |
| `output/character_skills/inference_inventory` | 112 | 0.382 |
| `output/character_skills/reader_c19_before_r01_20261107` | 2,452 | 0.362 |
| `output/character_skills/reader_c18_before_c19_20261107` | 2,432 | 0.320 |
| `output/character_skills/c21_delivery_20261111` | 577 | 0.311 |
| `output/character_skills/c19_delivery_20261107` | 198 | 0.274 |
| `output/character_skills/c10_p1_20261030` | 74 | 0.269 |
| `output/character_skills/c9_p1_20261030` | 68 | 0.268 |
| `output/character_skills/effect_ledger` | 139 | 0.264 |
| `output/character_skills/profiles` | 8 | 0.263 |

## 子项目物理目录


| 目录 | 普通文件数 | 逻辑 GiB |
|---|---:|---:|
| `projects/assets` | 903,504 | 20.317 |
| `projects/unpack` | 861 | 2.070 |
| `projects/skill-research` | 3,575 | 1.120 |
| `projects/reader` | 9,029 | 0.640 |
| `projects/reference-analysis` | 94 | 0.012 |

## Git 实测


- 分支 `main`，HEAD `56a9d1793a93ead3d01afcb4cff2f6d1ff5e6db0`，已跟踪 588 个路径；状态计数 `{" M": 169, " D": 9, "??": 13626}`（两字符为 Git porcelain 状态）。

- 未跟踪普通路径按 lstat 汇总 994,883,292 B，约 948.8 MiB。这不是建议入库量；统计时点含本轮任务卡，不含本轮工作／报告目录。

- `git ls-remote --heads origin main` 返回失败：127.0.0.1 代理连接不可用。仅核实本地 main 与 origin/main 同指，未确认远端实时 SHA；未 fetch、提交或推送。

- `projects/reader/site/.gitignore` 当前仅列 B02 试点，其余多套生成站点成为未跟踪文件；布局目录也含大型扫描、夹具和历史副本。后续 Git 整理须逐类选择，不能全目录暂存。

## 产物与重跑


- [机器摘要](inventory-summary.json)：时间、总量、大文件、跳过的重解析点和错误。

- [目录体积 CSV](directory-sizes.csv)：最多四级汇总，支持筛选；不同层级重叠。

- [Git 摘要](git-summary.json)：状态和未跟踪分布。

- [文件元数据清单](../../../work/20261113-cleanup-research/files.jsonl.gz)：逐行数组，字段顺序见机器摘要 files_schema；未计算内容哈希，不是删除清单。

- [只读扫描脚本](../../../work/20261113-cleanup-research/inventory.py)及[汇总脚本](../../../work/20261113-cleanup-research/summarize.py)。从项目根执行 `.\.venv\Scripts\python.exe -B work/20261113-cleanup-research/inventory.py`，随后执行同目录 `summarize.py`。将来重扫先改为新的任务输出路径，保留本版测量。

- 本轮仅新增这份方案、盘点结果、任务卡和工作材料；未修改业务数据或脚本、根导航、Git 索引，未删除或迁移文件。


核验：一级目录文件数和字节数汇总与扫描总计一致；本轮无业务代码变更，不额外运行业务测试。
