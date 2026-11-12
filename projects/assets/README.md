# 媒体资源导航

## 现行媒体入口

[媒体导出](data/full_unpack/)保存 bdl 展开对象、账本与清单，[角色图片](data/card_images/)保存图片和绑定证据，[APK Unity 索引](history/unity/)单独保存。[页面共享图片](../../output/character_skills/pages/art/)仍随正式页面维护，并由阅读器引用。历史 ledger 中的路径保留原来源。

历史版本索引：[B00 总览](../../docs/project-layout/20261107-b00-v1/README.md) · [本项目全部 16 条映射](../../docs/project-layout/20261107-b00-v1/assets.md) · [全量机器索引](../../docs/project-layout/20261107-b00-v1/index.json)。基线为 [20261106/path-map.json](../../docs/project-layout/20261106/path-map.json)，其中 `target_proposal` 是未来候选布局，并非已落地路径。

## 当前入口

| 入口 | 用途与边界 |
|---|---|
| [full_unpack/README.md](data/full_unpack/README.md)、[原任务卡](../../docs/tasks/20261016-full-unpack.md) | 2026-10-16 本地资源解包成果及其历史验证口径 |
| [ledger.jsonl](data/full_unpack/ledger.jsonl)、[coverage.json](data/full_unpack/coverage.json)、[manifest.json](data/full_unpack/manifest.json) | 输入资源状态、文件／对象覆盖和来源版本；读取记录的 producer 路径约定 |
| [objects](data/full_unpack/objects/)、[cid_index.json](data/full_unpack/cid_index.json) | 纹理、音频、网格、文本及结构化对象；CID 索引仅按包名规律关联，不能代替客户端绑定证明 |
| [APK Unity 对象索引](history/unity/objects.jsonl)、[summary.json](history/unity/summary.json) | APK 内置资源索引，与缓存 bdl 导出分源保存；不等于 APK 媒体已全量导出 |
| [角色图片目录](data/card_images/)、[cid30236 来源说明](data/card_images/cid30236/SOURCES.txt)、[绑定证据](data/card_images/cid30236/binding_evidence.json) | 查看具体来源、客户端关联以及完整／局部图像标记；cid30236 的 `standing_partial.png` 是上半身图，完整无卡框全身立绘尚未定位 |
| [页面共享 art](../../output/character_skills/pages/art/) | 正式渲染器仍维护、阅读器直接引用的共享接口，保持原位；不作为冻结媒体副本 |
| [解包项目](../unpack/README.md)、[当前交接](../../HANDOFF.md) | APK／缓存快照及共享原生解码依赖，当前在途边界 |

## 输入、生产者与消费者

历史 full_unpack 范围以 [组合清单](../unpack/data/cache/cache_refresh_20261015/composite_inventory.jsonl)的 68,993 个本地缓存文件为分母：其 README 记录 68,655 个 bdl 成功展开、834,741 个对象，77 个 data5 复用 v3 解码。该范围不是全游戏覆盖，也不代表字段语义全部已解释；这些数字是历史成果说明，本次没有重跑验证。

| 链路 | 原位生产者／输入 | 消费者与约束 |
|---|---|---|
| bdl 批量导出 | [full_unpack_run.py](../../scripts/full_unpack_run.py)、[merge](../../scripts/full_unpack_merge.py)、[finalize](../../scripts/full_unpack_finalize.py)；组合清单、缓存工作副本及共享 NativeDecoder | [媒体导出](data/full_unpack/)的对象、账本和清单供图片绑定、名册、角色页及发行使用；[work/full_unpack](../../work/full_unpack/) 含续跑分片，不因目录名视为可删 |
| APK Unity 索引 | [unity_scan.py](../../scripts/unity_scan.py)及 APK 输入 | 结果见 [APK Unity 索引](history/unity/)；APK 内置媒体未批量导出的缺口沿用原成果说明 |
| 定向角色图片 | [extract_cid30236_images.py](../../scripts/extract_cid30236_images.py)、[trace_cid30236_art.py](../../scripts/trace_cid30236_art.py)；v3 角色记录、组合清单与所选包 | 产出图片与绑定／来源证据；重跑默认在 `data/card_image_runs/` 新建版本。卡面、头像、局部透明图分别标记，不能互称完整立绘 |
| 页面媒体 | [正式渲染器](../../scripts/character_skills/card_page_render_v2.py)维护 `pages/art` | 角色页、阅读器及发行共同依赖；阅读器的 `../pages/art` 相对 URL 与当前服务布局耦合 |

## 历史、共享依赖与保护范围

- 媒体 ledger 的输出路径基准按各 producer 解释。data5 的 decoded 路径、bdl 成功／partial 对象目录及错误／null 状态不能统一按“相对媒体根”重写；现有账本、分片和冻结来源保留原值。
- 依赖 [解包项目](../unpack/README.md)管理的 APK、缓存清单、工作副本、原生恢复材料与现有环境。历史 `work/`／`output/` 可能是续跑输入、恢复材料或冻结基线，不能当作普通临时文件。
- `pages/art` 是在途生产者／消费者共同保护范围。名册与渲染代码、图片完整性标记和来源映射须随消费者核对；复制到兼容布局不算重新解包收益，内容相同也不证明路径可换。

- 原位导航阶段的 16 条映射、分类边界和历史任务见 [B00 任务卡](../../docs/tasks/20261107-project-layout-b00-navigation.md)及[批次方案](../../docs/project-layout/20261106/batch-plan.json)。现行物理位置以[实际迁移回执](../../docs/project-layout/20261109-unified-physical-v1/REPORT.md)为准。
