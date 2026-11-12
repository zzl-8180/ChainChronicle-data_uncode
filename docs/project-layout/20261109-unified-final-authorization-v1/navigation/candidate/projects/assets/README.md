# 媒体资源导航

## 统一迁移后媒体入口（统一迁移验收后）

统一迁移仅在 31 棵完整目录、2 个 latest 控制文件、读取与写入适配、别名及保护契约通过最终验收，并按单独授权安装 `scripts/project_layout_active.json` 后作为当前物理布局。合入后，原 CLI 的已适配逻辑路径默认解析到新根，无须每次手设环境变量；未适配命令仍须按各自验收回执核对。冻结清单中的旧来源字符串保留原值；不能把迁址当作重新生成或重新签名。 [full_unpack](data/full_unpack/) 保存 bdl 展开对象、账本与清单，[card_images](data/card_images/) 保存角色媒体及绑定证据，[unity](history/unity/) 保存 APK Unity 索引。正式页面共享媒体 `output/character_skills/pages/art/` 仍原位；历史 ledger 中旧路径值保留来源身份，不将 CID 规律等同客户端绑定。下文 B00 原位描述仅按其历史时点阅读。


本页负责 bdl／Unity 对象导出、角色图片、绑定证据及页面共享媒体的入口导航。B00 仅新增导航，脚本、数据和运行材料仍在原位；不重建媒体、不复制数据、不切换消费者。

版本索引：[B00 总览](../../docs/project-layout/20261107-b00-v1/README.md) · [本项目全部 16 条映射](../../docs/project-layout/20261107-b00-v1/assets.md) · [全量机器索引](../../docs/project-layout/20261107-b00-v1/index.json)。基线为 [20261106/path-map.json](../../docs/project-layout/20261106/path-map.json)，其中 `target_proposal` 是未来候选布局，并非已落地路径。

## 当前入口

| 原位入口 | 用途与边界 |
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
| bdl 批量导出 | [full_unpack_run.py](../../scripts/full_unpack_run.py)、[merge](../../scripts/full_unpack_merge.py)、[finalize](../../scripts/full_unpack_finalize.py)；组合清单、缓存工作副本及共享 NativeDecoder | `output/full_unpack` 的对象、账本和清单供图片绑定、名册、角色页及发行使用；[work/full_unpack](../../work/full_unpack/) 含续跑分片，不因目录名视为可删 |
| APK Unity 索引 | [unity_scan.py](../../scripts/unity_scan.py)及 APK 输入 | 形成 `output/unity`；APK 内置媒体未批量导出的缺口沿用原成果说明 |
| 定向角色图片 | [extract_cid30236_images.py](../../scripts/extract_cid30236_images.py)、[trace_cid30236_art.py](../../scripts/trace_cid30236_art.py)；v3 角色记录、组合清单与所选包 | 产出图片与绑定／来源证据；卡面、头像、局部透明图分别标记，不能互称完整立绘 |
| 页面媒体 | [正式渲染器](../../scripts/character_skills/card_page_render_v2.py)维护 `pages/art` | 角色页、阅读器及发行共同依赖；阅读器的 `../pages/art` 相对 URL 与当前服务布局耦合 |

## 历史、共享依赖与保护范围

- 媒体 ledger 的输出路径基准按各 producer 解释。data5 的 decoded 路径、bdl 成功／partial 对象目录及错误／null 状态不能统一按“相对媒体根”重写；现有账本、分片和冻结来源保留原值。
- 依赖 [解包项目](../unpack/README.md)管理的 APK、缓存清单、工作副本、原生恢复材料与现有环境。历史 `work/`／`output/` 可能是续跑输入、恢复材料或冻结基线，不能当作普通临时文件。
- `pages/art` 是在途生产者／消费者共同保护范围。名册与渲染代码、图片完整性标记和来源映射须随消费者核对；复制到兼容布局不算重新解包收益，内容相同也不证明路径可换。
- 16 条映射是导航归属，不是可移动／可删除清单；更具体子行优先于父目录。后续媒体根、分片、名册及消费者适配属于独立批次，B00 不启动。
- 本页按 2026-11-07 可见文档核对。[B00 任务卡](../../docs/tasks/20261107-project-layout-b00-navigation.md)及[批次方案](../../docs/project-layout/20261106/batch-plan.json)限定保护范围；历史 full_unpack 完成状态不授权接管当前角色页或阅读器工作。
