# 第二批完整目录整理：执行前报告

2026-11-08。Sol执行准备，Astra独立复核。沿用既有目录映射和引用调查，只补充本批仍在运行的读口、五联接与执行安全边界。技术准备PASS；主持交互已使用0/1。尚未取得本批物理迁移授权。

## 精确范围

项目根 `E:\代码项目\锁链战记数据解包`，下表均为项目相对路径。

| 现在 | 目标 | 文件 | 字节 |
|---|---|---:|---:|
| `output/single` | `projects/unpack/history/single` | 3 | 4,131,868 |
| `output/cache_full_20261015_v2` | `projects/unpack/data/cache/cache_full_20261015_v2` | 95 | 118,170,246 |
| 合计 | 两棵完整目录 | 98 | 122,302,114 |

同E卷目录rename，保留内容、目录／文件ID、mtime与历史字符串。目标当前均不存在；源仍在原处。无需再复制122MB；只增加准备文档、小夹具、日志和回执，实际准备占用见 acceptance.json，不另留载荷副本。搬迁本身不会释放这122MB，目的是整理位置。

只准备同步切换五个 `cache_full_20261015_v2` junction：

1. `work/c14_delivery_20261103/impl/isolation_input/output/cache_full_20261015_v2`
2. `work/c15_delivery_20261103/impl/isolation_input/output/cache_full_20261015_v2`
3. `work/c16_delivery_20261104/impl/isolation_input/output/cache_full_20261015_v2`
4. `work/c17_delivery_20261106/impl/isolation_input/output/cache_full_20261015_v2`
5. `work/c18_delivery_20261106/impl/isolation_input/output/cache_full_20261015_v2`

它们均仍指旧v2根，原ID、mount-point tag与精确target已入前像。不是上一批已处理的五个share_bundle入口。next及previous十个名字当前不存在；未来五previous保留停用，不自动清理。

## 引用和必要适配

| 消费者／材料 | 处理及影响 |
|---|---|
| `scripts/decode_cache_snapshot.py` 的 `--reuse-dir` | 候选补丁改用显式reuse-dir下的 `decoded/<filename>.json.raw`，不再沿用报告里旧绝对路径；文件名限制、cipher／JSON SHA保留。不改无reuse或其他分支。当前正式文件未修改。 |
| `scripts/verify_cache_snapshot.py` 的两处 `json_file` 读取 | 候选补丁改用显式input下同一固定布局，原有校验断言及native流程保留。当前正式文件未修改，也未运行其main或native。 |
| v2报告、progress、tables.csv、analysis | 保持原字节。77个DECODED成员布局已核实；134行tables的旧路径作为历史来源值，由外部path-map说明。14个analysis为JSON／CSV／JSONL，没有HTML静态资源链。未发现需要额外适配的当前路径读取者。 |
| `analyze_cache_snapshot.py` | 使用显式input及records／report；迁后如确需运行必须显式给新input。会写analysis，因此执行窗口必须排除其并发运行，不为搬迁重跑分析。 |
| 五个v2历史入口 | 整根迁出后逐个next验读、formal→previous、next→formal，保留原入口证据。两rename非原子，局部窗口内正式名短暂缺失。 |
| `projects/unpack/README.md` | 已备成功后导航补丁，同时纠正打包退役已经完成但本页仍写准备态的旧文字；实际成功前不合入。保留并发内容。 |
| 局部Git忽略 | cache局部规则新增v2，history局部规则新增single；读取现有规则后增量合并，不改根.gitignore，不覆盖其他规则。 |

两个候选代码须在唯一主持交接中获准，由执行对话最小合入后才能物理操作。若live源码已变，不能拿旧补丁直接覆盖；停止受影响步骤并保留新内容。冻结报告及旧字符串不批量替换。

## 不动的内容

当前 `output/cache_full_20261015_v3`、latest／cache_refresh链、pages／profiles／rules／effect_ledger、媒体、原始输入、vault和主线源码不在本批。已归档5317项、11项原位材料、P/v7、四份plan及binding、失败日志、独立审查原件均保留。既有v1迁移、打包退役和share_bundle五入口不重复执行。

`decoded`、`export`、phone系列和cache_refresh仍有多个默认读写、当前来源或历史联接，不为凑批次迁移；细节沿用[解包侧差异调查](investigation-unpack.md)和[其他候选排除记录](investigation-other.md)。

## 已完成的验证

- 98源文件只读SHA及大小／ID／mtime／nlink，目录身份、无内部reparse、同卷、目标无冲突：PASS。
- 五个旧v2入口身份及target，十个临时名字缺失：PASS；保护观察22项匹配。主线现用文件只观察，不要求其所有者停止合法更新。
- decoder候选7项、verifier路径候选5项：PASS。仅小夹具，不冒充生产native／完整重解码。
- 只读checker的11项小夹具原语／边界检查：PASS；真实目录／junction原语只作用于新9字节夹具，未操作业务原件。
- 缺少授权、false授权模板的实际CLI：拒绝执行；PowerShell模板语法解析0错，未执行模板。
- Astra核对22绑定文件、两份精确补丁／测试、98准备预检、五入口和保护身份：技术阻断0，见[完整独审](astra-review.json)。

执行材料bindings SHA：`e903da8ab43d0a56c62c51c94d649b49b469b07bc1caaf7ba5d3112f059ffd42`。准备预检SHA：`e1ee9fb16319d218fb84bde8cf42addff25c80cf5ec0b5895ffa35de75a9b07d`。清单SHA：`e2aec985a2c7a8683bd786e9e37c1b573f3d8eabbde831dd1ada1511e45930c6`。

## 获得交接和物理授权后的具体顺序

1. 一次性主持回执明确两根无相关使用者、五入口接管、两源码和本批导航写域及局部窗口；主线继续。
2. 用户最终授权两根rename与五入口切换；记录真实来源，不把主持同意冒充用户授权。
3. 窗口内合入两份批准路径补丁及局部ignore；重读当前文件。新做98项source-preflight，绑定新回执路径、SHA、窗口和授权。今天准备回执不复用为临前检查。
4. 整体移动single并核3项，再整体移动v2并核95项；逐入口建立next、验读、两次rename及逐步身份／内容回执，才处理下一个。原子交换和全机无句柄均不作承诺。
5. 两根与五入口全部通过后才合入本批导航，保存WAL和真实退出码，Astra独立验收实际结果。不提交、不推送。

每个物理动作之前均有持久INTENT、最新身份gate与授权时间复核。任何漂移、窗口过期、未知使用者或目标冲突立即停止对应批次，不扩大为主线全局停工。

## 暂停与恢复

[完整恢复表](tooling/recovery.md)已列每根／每入口中间状态和精确检查命令。默认保留已验真的新位置，按回执只继续未完成步骤；不盲目重跑，不把正式入口指回已经迁空的旧根。真正退回旧物理位置须先另定可审恢复范围，按前像恢复保留树并验真，然后处理入口；本批不自动逆搬或删除previous。移动后不能单独撤掉必要路径补丁。

## 剩余事项

仅剩一次主持交接、用户最终物理授权及该局部窗口内的临前复核／真实执行。唯一主持提示词见[host-handoff-prompt.md](host-handoff-prompt.md)。本报告不是迁移授权；目前不写READY_FOR_EXECUTION，不把准备或小夹具PASS写成物理整理完成。
