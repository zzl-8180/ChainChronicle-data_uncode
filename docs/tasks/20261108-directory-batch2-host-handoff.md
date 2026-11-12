# 第二批目录整理：一次性主持交接回执

- 交接时间：2026-11-08 18:17:37（北京时间）。
- 状态：**交接确认完成／等待用户最终物理授权；未搬迁、未切换、未合入补丁、未提交推送**。
- 依据：`host-handoff-prompt.md`、REPORT、Astra review、consumer-code-binding、runbook及recovery。技术准备和Astra复核已通过，未重复全量调查或测试。

## 1. 两源目录与五入口的接管和使用状态

两源目录实际接管者统一移交执行对话：

- `output/single`：3文件／4,131,868 B，目标 `projects/unpack/history/single`。
- `output/cache_full_20261015_v2`：95文件／118,170,246 B，目标 `projects/unpack/data/cache/cache_full_20261015_v2`。

两源当前均存在、目标均不存在。五个C14—C18 `cache_full_20261015_v2` 历史入口均为真实mount-point，tag `0xA0000003`，readlink仍精确指向 `\\?\E:\代码项目\锁链战记数据解包\output\cache_full_20261015_v2`；五个next和五个previous名称均不存在。

**当前使用证据**：检查任务写域未发现其他新增任务接管这些入口；非shell进程命令行未命中两源路径、`--reuse-dir`或`--input`。代码检索只发现通用reuse接口及本批执行器，未发现另一当前消费者。以上仅是本次可核范围，**不证明全系统无打开句柄或未来使用者**，执行对话临窗必须复核。

历史整合者 `new-provider/kimi-k3-1-pro-261024` 与当前主持一致；本批后续实际接管者为**执行对话**，由其独立安排物理操作、回执和复核，主持不再并发执行。

## 2. 可交接写域

| 写域 | 交接安排 |
|---|---|
| `scripts/decode_cache_snapshot.py` | 仅reuse-dir下decoded成员解析和文件名安全校验；无reuse、recovered_variants、原生解码及SHA校验分支保持 |
| `scripts/verify_cache_snapshot.py` | 仅新增decoded_file helper及两处旧`json_file`读取；其余native流程、断言和校验保持 |
| 两源目录与五个v2入口 | 执行对话统一整体rename、next验读、previous结构回执、正式入口内容验读及聚合验收 |
| `projects/unpack/README.md` | 只在两源和五入口实际成功后整合本批导航；保留并发内容，不写准备态成功声明 |
| `projects/unpack/data/cache/.gitignore` | 在现有v1规则后增量加入`/cache_full_20261015_v2/`，不覆盖其它规则 |
| `projects/unpack/history/.gitignore` | 当前不存在，成功后可新建仅含`/single/`的局部规则；若已出现则先读再合并，不覆盖 |
| 执行预检、授权、WAL、恢复及独立复核 | 由执行对话维护；本批四共享根无需更新，主线其他写域不变 |

## 3. 两份路径补丁与导航审阅

| 项目 | 当前结果 | 主持决定 |
|---|---|---|
| `decoder-reuse.patch` | live `decode_cache_snapshot.py` SHA与绑定值完全一致；`git apply --check`通过；7项既有测试回执符合审查 | **批准由执行对话最小合入，不在本轮回合入** |
| `verifier-path.patch` | live `verify_cache_snapshot.py` SHA与绑定值完全一致；`git apply --check`通过；5项既有测试回执符合审查 | **批准由执行对话最小合入，不在本轮回合入** |
| `navigation-after-success.patch` | 当前 `projects/unpack/README.md` SHA与准备记录一致，检查通过；含single/v2实际成功入口 | **仅实际成功后合入，当前不合入** |

补丁批准只限所列路径部分。若live源码或基底再变，停止受影响步骤，保存新内容并重定基底，不整文件覆盖。局部ignore规则采用增量合并，根 `.gitignore` 不改。

## 4. 局部窗口

**建议固定窗口：2026-11-08 19:00—19:30（北京时间）。**

生效条件：

1. 用户另行明确两目录迁移及五入口切换的最终物理授权；
2. 窗口内完成新的98项source-preflight并绑定其路径与SHA，不复用准备阶段PASS；
3. 临窗再次确认使用者、代码candidate SHA、源／目标、reparse及并发写域均通过；
4. 任何漂移、未知使用者、授权缺失或目标冲突立即暂停，不扩大到主线全局停工。

窗口仅覆盖本批两源迁移和五入口验收，主线研究、规则修订、正常生成与校验继续。**19:30后未使用即失效，不自动顺延，须重新预约。** 执行对话记录真实UTC起止，不把本建议当作已开始的物理窗口。

## 5. 全部已知冲突与未闭合事项

1. 用户最终物理授权尚未取得，当前不能开始rename或junction切换。
2. 全系统句柄不可得；本轮回执未发现使用者不等于永久无人使用，临窗出现新使用者即停止。
3. 两候选代码及导航虽已检查通过，但尚未合入；任何后续漂移必须重审，不能拿旧补丁覆盖。
4. 新的98项窗口预检、执行授权SHA、WAL和实际退出码尚未产生。
5. `navigation-after-success.patch` 和局部ignore只能成功后处理；当前准备态导航不能发布为成功状态。
6. 两次rename不是原子交换，formal短暂缺失；previous仅停用留证，不供业务读取，不删除或清理previous／旧空目录。
7. 迁出后不得回指空旧根；需要回退时先恢复保留树并验真，或保持已验真的新位置。必要路径适配不能在迁移后单独撤销。
8. v3／latest／当前pages／profiles／ledger、原始输入、已归档5317项／原位11项、P/v7、四份plan及binding、share_bundle入口均不在本批范围，不重复处理。

除上述条件外，当前未发现新的使用者冲突。后续由执行对话统一操作，主持不另行搬迁、切换或合入补丁。
