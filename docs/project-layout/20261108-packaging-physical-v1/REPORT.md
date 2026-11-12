# 保留材料迁移与五历史入口切换回执

结论：**授权的5,317项保留迁移、真实验真、五入口切换及独立复核完成；共享导航待主持整合，未执行删除。** Sol high执行并验收，Astra high独立复核。

## 授权与实际时间

用户最初授权2026-11-08北京时间13:00—14:00，随后明确“不再等到13:00，清点完成后开始”。修订后工具起点保守设为收到指示后的12:47:51，截止仍为14:00，不顺延。原授权和修订分别见 [authorization.json](authorization.json)、[authorization-immediate-amendment.json](authorization-immediate-amendment.json)。

以下均为2026-11-08北京时间：

| 阶段 | 实际起止 | 结果／真实退出码 |
|---|---|---|
| 迁移命令，含最终写前复核 | 12:52:48—12:58:01 | 5,317项逐项完成，0 |
| 第一条文件移动INTENT至最后一条DONE | 12:55:01—12:57:54 | 同卷rename，SHA及文件ID一致 |
| Sol全目录验真 | 12:58:25—13:00:54 | MOVE_VERIFIED，0 |
| Astra独立读取全部新位置 | 13:03:01—13:04:51 | 5,317项／108,004,454 B通过 |
| 五入口实际切换 | 13:05:58—13:06:48 | 15个联接动作及所有分阶段检查通过 |
| Sol五入口聚合验读 | 13:07完成 | 5×142文件通过，0 |
| Astra最终物理独审 | 13:09:05—13:09:15 | 五入口内容、previous结构、顺序及保护门通过 |

物理动作全部在修订后的授权时间内完成。失败0、暂停0、回退0；失败暂停机制本次未实际触发，不把合成故障测试写成真实回退经历。

## 实际文件与存放位置

冻结6,935项完整表保持原字节，SHA-256 `274c6cd5602b591047ce2b2c907b4e5d9bb33ff55b190b0bb8678ec586e82ef1`。使用批准的execution-overlay承接 `projects/distribution/README.md` 当前5,350字节身份；未修改冻结表。

- ARCHIVE_HISTORY 5,171项、REHOME_BUSINESS 146项已逐文件迁至 `operations/history/retired-packaging/20261108/` 下批准的 `share_bundle/`、`distribution/`、`history-work/` 目标。共5,317项、108,004,454字节，所有旧source消失，目标文件集合精确一致。
- DELETE 1,607项仍原位，逻辑4,979,429,886字节；RETAIN_IN_PLACE 11项仍原位。迁后旧树文件集合精确为这1,618项，后验metadata一致。
- 没有整体搬走混合旧根，没有复制大型载荷，没有在output创建常驻兼容联接。
- 真实新历史根及祖先、嵌套路径均通过无未声明reparse检查；5,317项SHA、长度、mtime、文件ID、nlink、mode、attributes均与前像一致。rename可改变ctime，前后值保存在逐项日志中。
- 单独新增治理辅助文件 `operations/history/retired-packaging/.gitignore`，仅11字节 `/20261108/`，位于5,317项树外；根 `.gitignore` 未改。

唯一执行前像：[source-hashes.json](run-immediate-bound/source-hashes.json)，SHA-256 `b37141ce19ba36958e555d30da4f3e744ae6fcf9dd51a316c8bb5b09c28e33f0`。早先三份run前像保留为预审过程证据，未用于物理执行。

实际逐项迁移／回退映射：[move-journal.jsonl](run-immediate-bound/move-journal.jsonl)、[verify.json](run-immediate-bound/verify.json)、[rollback-manifest.json](rollback-manifest.json)。日志含5,317对INTENT／DONE，共10,636行，无PAUSED。

## 五入口实际切换

入口均位于各周期 `impl/isolation_input/output/`，只处理 `share_bundle`、同父 `share_bundle.retirement-next-20261108` 和 `share_bundle.retirement-previous-20261108`。

| 周期目录 | next内容验收 | previous结构验收 | 正式新入口内容验收 |
|---|---|---|---|
| `work/c14_delivery_20261103/` | 142／142 | 原tag、target、fileID通过 | 13:06:08，142／142 |
| `work/c15_delivery_20261103/` | 142／142 | 同上 | 13:06:29，142／142 |
| `work/c16_delivery_20261104/` | 142／142 | 同上 | 13:06:35，142／142 |
| `work/c17_delivery_20261106/` | 142／142 | 同上 | 13:06:41，142／142 |
| `work/c18_delivery_20261106/` | 142／142 | 同上 | 13:06:48，142／142 |

五正式入口的精确新target均为 `E:\代码项目\锁链战记数据解包\operations\history\retired-packaging\20261108\share_bundle`；五previous仍保留原 `\\?\E:\代码项目\锁链战记数据解包\output\share_bundle` target及原fileID，均标记为停用回滚证据，不供业务读取。tag均为mount-point `0xA0000003`。next均不存在，next→formal文件ID与读取集合一致。

每个入口严格执行：建立next → 通过next读取142文件 → 原formal改名previous → 在formal暂缺时核previous原结构，不读已迁空旧target内容 → next改名formal → 通过formal读取142文件。两次rename不是原子交换，间隙存在；逐项完成后才处理下一入口。

详细真实target、ID、时间与回执：[junction-summary.json](run-immediate-bound/junction-summary.json)、[all-five-new.json](run-immediate-bound/all-five-new.json)、[previous-final-structure.json](run-immediate-bound/previous-final-structure.json)。每周期另有各动作intent／done／native、next-content、previous-gap、formal-content及退出码回执。

## 保护材料与在途边界

Sol及Astra均确认：139份研究材料＝135 payload成员＋manifest＋3外围文件；两版技能manifest；P第222项指定12,340字节源码；四plan及binding；P/v7身份一致。每入口142文件即139＋2＋1，来自真实新位置，不是RAM模拟或旧根fallback。

- 研究manifest为45,882字节，SHA-256 `ae3a591d1dd35be221294a6418ca7455c9ec1184f247192cfee6c0f80bdef051`。
- P指定源码SHA-256 `b74e4681d492fbf0f7258e138669abf91bba23c27e091f865deae428ec4e9ee2`，没有拿12,508字节同名版本替代。
- 新只读维护入口archive模式及独立payload检查均退出0，未运行旧冻结verifier、打包、清理、恢复、生产对账或主线生成。
- 17份保护文件后验通过，包括四共享根、根ignore、规则、current指针、P/v7和四plan及binding。冻结清单、原审查、失败证据及历史独立材料未覆盖。
- 临场及切换前均查任务、进程命令行及入口身份；未发现新使用者或其他任务写域变化。进程命令行不证明全系统无句柄，协作冻结依据用户／主持明确安排。没有停止或抢占其他任务；主线无需全局停工。

独审：[archive-independent-review.json](archive-independent-review.json)、[physical-independent-review.json](physical-independent-review.json)。最终物理独审SHA-256 `4324a59e52229a5682af6b4be55e018118135a30a8d65129a96475ba48c2bf80`。

## 空间、回退与剩余事项

同卷迁移108,004,454字节材料，没有新增一份payload副本。本轮验收记录约28 MB；逻辑量与实际分配簇不同，全盘可用空间还受并行任务影响。未删除候选，因此本轮不声称释放约5 GB。空间测量见 [space-after.json](run-immediate-bound/space-after.json)。

保持已验真的新target为首选状态。若以后确需恢复旧target，须先依据逐项回执恢复5,317项保留树、验真，再处理联接；单独把previous改回正式名不能构成数据回退。不自动回滚或续跑，不授权在14:00后继续本轮物理操作。

仍需主持按真实回执整合四共享根，见 [handoff-to-host.md](handoff-to-host.md)。不得原样合入旧准备态补丁。

删除仍未授权：须先闭合主持导航回执，再在拟删除前重新执行archive模式完整1,406对内容门（1,270＋136）、源身份／overlay／reparse／硬链接／漂移检查，并取得用户单独最终删除确认。五previous和旧根／空目录另属后续范围，不能夹带处理。六成功旧包和173份旧实验载荷的精确重放在将来删除后不承诺恢复；manifest与源码前像不是完整ZIP备份。

没有暂存、提交、推送或发布；整支删除退役尚未完成。
