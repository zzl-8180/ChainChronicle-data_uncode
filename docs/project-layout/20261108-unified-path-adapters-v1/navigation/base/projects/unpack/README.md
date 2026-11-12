# 解包与共享输入导航

第二批已于2026-11-08 18:35北京时间实际完成：single及v2共98文件整体迁移，C14—C18五个v2正式入口均指向新根；五个previous仅停用留证，next均不存在。见[实际执行回执](../../docs/project-layout/20261108-directory-batch2-ready-v1/physical-20261108-v1/REPORT.md)；当前v3与主线保持原位。

## 2026-11-08 历史打包材料退役与只读维护

旧打包支线的1,607项文件、5个停用previous及9,467个旧空目录已按各次授权清理；5,317项保留材料位于 `operations/history/retired-packaging/20261108/` 下的 `share_bundle/`、`distribution/`、`history-work/`，11项跨任务材料仍在原位。见[最终文件删除回执](../../docs/project-layout/20261108-packaging-final-ready-v1/deletion-20261108-v1/REPORT.md)、[空目录清理回执](../../docs/project-layout/20261108-packaging-empty-cleanup-v1/REPORT.md)。只读维护入口为 [retirement_runtime.py](../../scripts/project_layout/retirement_runtime.py)，不复跑旧打包、恢复或冻结清理脚本。

两版旧技能值manifest及P第222项12,340字节旧源码现已在上述新历史根验真；P/v7和四份旧plan保持原字节，物理位置由外部映射承接。manifest仅提供历史身份线索，不意味着缺失角色JSON／HTML／图片或旧ZIP可恢复。全部归档材料继续留存，不按retired名称直接丢弃。

本页负责 APK 基线、原生恢复、缓存采集与 data5／APK 内置主表解码的入口导航。历史v1缓存、单文件解码样本single及旧缓存v2已按各批回执整体迁至本项目；现用v3、补采和正式技能数据保持原位。本页只更新已完成迁址的历史入口，不启动采集、解码或主线生成。历史JSON／CSV中的原路径值不改写，按[第二批外部路径映射](../../docs/project-layout/20261108-directory-batch2-ready-v1/path-map.json)和对应批次回执定位。

版本索引：[B00 总览](../../docs/project-layout/20261107-b00-v1/README.md) · [本项目全部 80 条映射](../../docs/project-layout/20261107-b00-v1/unpack.md) · [全量机器索引](../../docs/project-layout/20261107-b00-v1/index.json)。基线为 [20261106/path-map.json](../../docs/project-layout/20261106/path-map.json)，其中 `target_proposal` 是未来候选布局，并非已落地路径。

## 当前入口

| 入口 | 用途与版本 |
|---|---|
| [根使用说明](../../README.md)、[当前交接](../../HANDOFF.md) | 工具版本边界、现用入口及当前工作范围；接手前核对最新交接 |
| [cache_full_latest.json](../../output/cache_full_latest.json) | 当前指向 `output/cache_full_20261015_v3`，原始快照为 `raw/phone_20261015_full_02` |
| [v3 manifest](../../output/cache_full_20261015_v3/manifest.json)、[decoded](../../output/cache_full_20261015_v3/decoded/) | 缓存主表的版本与完整 JSON；`.json.raw` 是 JSON 字节 |
| [records.jsonl](../../output/cache_full_20261015_v3/records.jsonl)、[tables.csv](../../output/cache_full_20261015_v3/tables.csv) | 记录视图与表索引，不能替代完整 JSON |
| [v1 历史目录](data/cache/cache_full_20261015/)、[迁址记录与路径映射](../../docs/project-layout/20261108-move-cache-v1/README.md) | 原 `output/cache_full_20261015/` 已整体移至本项目；历史 JSON 内的 `json_file` 仍是旧来源路径，不代表现用缓存，读取时按外部映射定位 |
| [single历史样本](history/single/) | 原 `output/single/`，保留JSON、raw及原报告三个文件；整目录迁移，不去重、不改来源字段 |
| [v2历史缓存](data/cache/cache_full_20261015_v2/)／[解码报告](data/cache/cache_full_20261015_v2/decode_report.json) | 原 `output/cache_full_20261015_v2/`，95文件原字节保留；复用与历史验证读取端按显式新根解析decoded成员；[第二批回执](../../docs/project-layout/20261108-directory-batch2-ready-v1/README.md) |
| [cache_refresh_latest.json](../../output/cache_refresh_latest.json)、[组合清单](../../output/cache_refresh_20261015/composite_inventory.jsonl) | 补采与原快照组合的输入来源；当前补采目录 `output/cache_refresh_20261015`，记录新增 165 个 bdl、核心 data5 未变 |
| [APK 内置主表](../../output/base_master/) | APK 来源的解码结果，与缓存分源保存 |
| [可复现性审计](../../docs/tasks/20261016-reproducibility-audit.md) | 第三方解包依赖链及隔离检查的历史证据；按其版本和结论等级阅读 |
| [媒体项目](../assets/README.md) | bdl、Unity 对象及图片成果，避免把主表解码与媒体导出混为同一覆盖口径 |

## 输入、生产者与消费者

工具明确支持 `com.sega.chainchronicle` 5.6.2／versionCode 56021（Unity 2021.3.58f1）；APK 签名、保护库和恢复镜像受版本及哈希约束。输入是兼容 APK 与自行提供的缓存，不从本页推断其他版本可用。

| 链路 | 原位生产者／材料 | 下游用途 |
|---|---|---|
| APK 基线与原生恢复 | [apk_baseline.py](../../scripts/apk_baseline.py)、[elf_relocations.py](../../scripts/elf_relocations.py)、[signal_region_probe.py](../../scripts/signal_region_probe.py)；[work/apk](../../work/apk/)、[work/protection](../../work/protection/) | 为解码和研究提供固定版本库、恢复镜像及重定位材料 |
| data5 | [decode_data5.py](../../scripts/decode_data5.py)、[decode_cache_snapshot.py](../../scripts/decode_cache_snapshot.py) | 产出完整 JSON 与记录视图，供字段研究、名册、角色页及媒体绑定使用 |
| APK 主表 | [decode_chronicle.py](../../scripts/decode_chronicle.py)、[recovered_symbols.json](../../output/native/recovered_symbols.json) | 产出 `base_master`；不与同号缓存对象自动合并 |
| 缓存来源 | [raw 全量快照](../../raw/phone_20261015_full_02/)、[raw 补采快照](../../raw/phone_20261015_refresh_02/)及对应 [全量工作副本](../../work/phone_20261015_full_02/)、[补采工作副本](../../work/phone_20261015_refresh_02/) | 组合清单中的 `archive`／`work_file` 保留实际原路径，供媒体导出与来源追溯 |

## 历史、共享依赖与保护范围

- 80 条映射含旧缓存版本、阶段性 `output/export`、采集与恢复工作目录。历史与现用关系逐条见版本索引；目录名、旧日期或“候选”分类不证明可以移动或删除。
- [relocations.json](../../output/protection/relocations.json)、恢复镜像、符号、APK 工作根由解包、媒体和技能研究共享。历史 `work/`／`output/` 中的恢复材料及冻结基线不能按临时文件处理；共享环境与原件保持原位。
- 当前研究、阅读器和语义审查仍可能消费这些输入。本页是 2026-11-07 的导航核对，不接管在途任务，不将历史完成状态作为未来修改许可。新缓存更新在当前交接中为暂缓状态，不因导航恢复采集或改写 latest。
- [B00 任务卡](../../docs/tasks/20261107-project-layout-b00-navigation.md)与[批次方案](../../docs/project-layout/20261106/batch-plan.json)限定本次为原位导航。映射按更具体子条目优先，父目录行不构成递归操作清单；后续参数化、迁址、清理与发行须分别交接和验收。
