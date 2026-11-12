# 精确221个previous清理：实际完成回执

状态：**COMPLETED_EXACT221_PREVIOUS_REMOVAL_ASTRA_PASS**。用户已明确授权并接受原联接实体/ID不能原样恢复；弱推理Sol实际执行，Astra独立后验通过。全部批准动作完成，无删除失败、无重试；未停止或联系主持，主线/F01可继续。

## 实际范围和时间

- 只移除旧计划[精确221条](../20261109-unified-postcleanup-plan-v1/cleanup-candidates.jsonl)中的junction对象：C14为29，C15—C20各32。
- 候选SHA：`3b1f9c172e341bf7288a9390069519fb0b2f8d4cb2d35e014f6390a60d27499f`；[逐项实际删除记录](deleted-objects.jsonl)保留每项原路径、对象ID、mount tag、raw target、reparse字节摘要及真实完成时间。
- 实际程序北京时间 **2026-11-09T19:53:51.831363+08:00—2026-11-09T19:53:53.315225+08:00**；进程退出码0。工具审批请求/返回另在process-exit中记载，不把等待审批时间当原生操作耗时。
- 本次执行ID为`unified-previous-cleanup-20261109-v1`，单独记录清理起止，没有复用或延长此前已结束的搬迁窗口，也未另加全主线停工窗口。

## 执行方法与日志

临前校验221个旧联接句柄的原文件身份、mount-point tag和完整target，以及221 formal、next缺失、81个保留对象、221目标样本和43项既有证据SHA。所有控制JSON/JSONL从同一份已核SHA原字节解析；准入绑定源码、用户授权、候选和保留清单。

实际执行以OPEN_REPARSE_POINT打开联接自身，持有具DELETE权限的句柄，核原ID/tag/rawtarget后，只用FileDispositionInfo标记这个对象并关闭。没有递归命令、通配删除、目标解析删除或父目录删除。每项INTENT先FlushFileBuffers落盘，删除及缺失/formal检查后才写COMPLETED。

[完整WAL](execution/deletion.wal.jsonl)：START1、INTENT221、COMPLETED221、FAILED0、FINISHED1。WAL SHA：`49f6e7f91b23d2a4cdc7985d0021b3538f22e0ac38b5e77da595accfc9014665`。旧对象原ID无法恢复这一后果没有被隐瞒；已有身份/路径/回执仍保留追溯。

第一次只读准备预检和修订后v2均保留；真正删除只使用已审最终工具SHA `77b957ef84dbc763b0425e6d4038d6c90b7f9851d185ef668ec6f35466fcccfb`。旧只读计划中deletion=false是当时状态，本次实际许可来自[当前用户授权](execution/user-authorization.json)及[聊天原消息证据](execution/latest-explicit-cleanup-user-message.json)，没有从评估PASS自行推断删除权。

## 保留和后验

| 检查项目 | 实际结果 |
|---|---:|
| 批准221 previous名称缺失 | 221 |
| 221现行formal原身份/target保留 | 221 |
| next残留 | 0 |
| 另外5个更早批次previous保留 | 5 |
| 六个P2B5独审原对象保留 | 6 |
| 普通父目录原对象保留 | 39 |
| 已迁目标根原对象保留 | 31 |
| 目标样本ID/大小/限定前缀通过 | 221 |
| 既有两manifest及core证据SHA通过 | 43 |
| 普通目录/目标/证据删除 | 0 |

39父目录保留身份和类型，子项数量/mtime随移除子入口自然变化，不要求其数值不变。旧迁移/评估包、冻结数据、WAL和失败审查等证据未修改；按既有两manifest核43项必要字节一致，没有全游戏载荷重哈希。正常主线源码变化不被当作迁移漂移。

[Astra准入](review/astra-pre-execution-review.json)通过后执行，[Astra实际独立后验](review/astra-post-execution-review.json)直接核精确221缺失、formal/保留项/目标样本/证据及WAL顺序和身份，`actual_cleanup_accepted=true`。最终独审SHA：`ce8af73ba4a94f6b4470a7ed1de4297716299c3246cae42864e43ba94514183e`。这不是准备或模拟结果。

## 空间及禁止扩围

游戏数据载荷删除量 **0 B**。只清理旧入口的文件系统元数据，真实可回收/复用量及磁盘可用空间增量未隔离测量，不以目标约25GB大小或卷空闲变化冒充释放量。

没有删除另5个previous、六独审入口、39父目录或任何普通空目录；没有改现行入口、目标数据、根导航、主线源码/规则/答案/正式页；没有Git提交、推送或公开发布。本次无剩余批准动作，不据此扩展其他批次清理。

若将来需要物理回退，仍须先按迁移回执恢复材料并验真，再新建/适配入口，新联接有新ID；不可盲指已空旧根。删除后同名新对象也不自动继承本次清理许可。

技术参考：[Microsoft reparse操作](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points-and-file-operations)、[句柄删除接口](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfileinformationbyhandle)。
