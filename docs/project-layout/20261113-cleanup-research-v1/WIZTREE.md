# WizTree 目录导出摘要

2026-11-13。WizTree 4.33 普通权限目录扫描（`/admin=0`），不是管理员 MFT 快速扫描。首份根目录为 2,103,201 文件、逻辑 183.579 GiB、分配 185.495 GiB；记录 82,563 个目录，项目外路径 0 条。分配大小不是删除后可回收量，也未证明硬链接已去重。

原扫描根为 2,098,061 文件、183.386 GiB；WizTree 多 5,140 文件、0.193 GiB。原扫描不跟随 29,637 个 reparse、错误 0，且排除了本次 work/report 目录；WizTree 包含本次目录。两者遍历口径也可能不同，目前证据不足以解释全部差异。以下按同路径显示差值，不能将一级目录差值直接当成归因结论。

## 一级目录

| 路径 | 逻辑 GiB | 分配 GiB | 文件数 | 对原扫描逻辑差 GiB | 文件数差 |
|---|---:|---:|---:|---:|---:|
| `output` | 101.474 | 101.991 | 929,224 | 0.000 | +0 |
| `work` | 50.072 | 50.329 | 195,635 | 0.193 | +5,140 |
| `projects` | 24.159 | 25.204 | 917,063 | 0.000 | +0 |
| `raw` | 3.804 | 3.804 | 36 | 0.000 | +0 |
| `其他人的参考` | 3.303 | 3.387 | 45,061 | 0.000 | +0 |
| `docs` | 0.280 | 0.289 | 4,682 | 0.000 | +1 |
| `.git` | 0.128 | 0.130 | 3,644 | -0.000 | -1 |
| `.venv` | 0.116 | 0.118 | 1,482 | 0.000 | +0 |
| `operations` | 0.101 | 0.099 | 5,335 | 0.000 | +0 |
| `tools` | 0.024 | 0.024 | 15 | 0.000 | +0 |
| `scripts` | 0.022 | 0.023 | 604 | 0.000 | +0 |
| `.zcode` | 0.006 | 0.006 | 406 | 0.000 | +0 |
| `skill参考` | 0.000 | 0.000 | 2 | 0.000 | +0 |

## 重点目录（深度不超过 4）

以下父子目录存在重叠，不能把各行相加。导出目录行最大深度为 6；根及父目录的汇总包含更深层内容，不等于只统计六层文件。

| 路径 | 逻辑 GiB | 分配 GiB | 文件数 | 对原扫描逻辑差 GiB | 文件数差 |
|---|---:|---:|---:|---:|---:|
| `work` | 50.072 | 50.329 | 195,635 | 0.193 | +5,140 |
| `output/character_skills/pages/_batch` | 41.817 | 42.007 | 615,652 | 0.000 | +0 |
| `output/character_skills/review` | 37.582 | 37.841 | 278,261 | 0.000 | +0 |
| `projects/assets` | 20.317 | 21.336 | 903,504 | 0.000 | +0 |
| `projects/assets/data` | 20.238 | 21.258 | 903,452 | 0.000 | +0 |
| `projects/assets/data/full_unpack` | 20.236 | 21.255 | 903,402 | 0.000 | +0 |
| `output/character_skills/review/reader_c19_r01_thirdparty_20261107` | 17.350 | 17.492 | 75,478 | 0.000 | +0 |
| `output/character_skills/review/reader_c19_thirdparty_20261107` | 14.245 | 14.329 | 184,647 | 0.000 | +0 |
| `work/phone_20261015_full_02` | 3.628 | 3.766 | 68,828 | 0.000 | +0 |
| `work/phone_20261015_full_02/files` | 3.627 | 3.765 | 68,621 | 0.000 | +0 |
| `work/phone_20261015_full_02/files/Bundle` | 3.613 | 3.750 | 68,490 | 0.000 | +0 |
| `work/character_skills_recheck_rectification` | 3.463 | 3.474 | 13,483 | 0.000 | +0 |
| `work/rule_registration_20261028` | 2.783 | 2.792 | 4,618 | 0.000 | +0 |
| `work/character_skills_recheck_rectification/replay_final` | 2.658 | 2.664 | 11,218 | 0.000 | +0 |
| `output/character_skills/review/reader_v01_thirdparty_20261107` | 2.443 | 2.470 | 15,254 | 0.000 | +0 |
| `work/character_skills_recheck_rectification/replay_final/pages` | 2.413 | 2.420 | 11,213 | 0.000 | +0 |
| `work/rule_registration_20261028/pages_pre` | 2.411 | 2.420 | 4,472 | 0.000 | +0 |
| `work/storage_recycle_g1_20261027` | 1.798 | 1.804 | 4,891 | 0.000 | +0 |
| `work/storage_recycle_g1_20261027/g2_bulk_verify` | 1.427 | 1.433 | 2,867 | 0.000 | +0 |
| `work/type67_20261028` | 1.369 | 1.374 | 2,376 | 0.000 | +0 |

## 两次导出和方法

第二份是观察进程时重复启动，两次均 exit 0；取消请求到达时均已自然结束，实际停止 0。第二份记录 82,563 个目录，项目外路径 0 条。只比较已导出记录中的关键父根；关键父根的逻辑大小、分配大小、文件数和文件夹数一致。 未重新扫描文件内容。

命令模板（参数含项目绝对路径；把 `<工作CSV>` 替换为新的 CSV 绝对路径，不覆盖本次回执）：

```powershell
Start-Process -FilePath 'C:\Program Files\WizTree\WizTree64.exe' -ArgumentList @('E:\代码项目\锁链战记数据解包', '/export=<工作CSV>', '/admin=0', '/exportfiles=0', '/exportfolders=1', '/exportmaxdepth=6', '/exportallsizes=1', '/sortby=2', '/exportUTCTime=1') -WindowStyle Hidden -Wait
```

[官方命令行导出说明](https://diskanalyzer.com/guide#command-line-csv-export)描述目录 CSV 导出；MFT 扫描需要管理员权限。比较使用既有 [原扫描目录摘要](directory-sizes.csv)，完整结果见 [机器摘要](wiztree-summary.json)、[首份原始 CSV](../../../work/20261113-cleanup-research/wiztree-folders.csv) 和 [第二份原始 CSV](../../../work/20261113-cleanup-research/wiztree-folders-native.csv)。
