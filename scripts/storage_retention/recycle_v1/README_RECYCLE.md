# G1 回收夹具能力核查

范围：`docs/tasks/20261027-storage-recycle-g1.md` 中 recycle 模块。本工具只探测环境、创建并验证**本任务自己生成的合成夹具**、验证失败闸门模型。当前交付结论是 **BLOCKED_G1_NOT_PASSED**，没有可用的真实回收/恢复后端。它不是 G2 生产执行器，也没有 G3 最终释放功能。

## 本机环境判断（2026-10-27，Asia/Shanghai）

- Windows 64 位、Python 3.12.14，E 盘为固定盘。实际卷 GUID 的 HKCU `Explorer\BitBucket\Volume\{GUID}` 项可读，`MaxCapacity=27647`、`NukeOnDelete=0`，均为 DWORD 原值。这与主持早期“按盘项不存在”的记录不同；工具从卷挂载点解析 GUID，不猜盘符对应项。
- **有效容量未知**。不把原始注册表值转换为已验证配额，不推定单位、默认值或策略优先级。注册表读取不等于回收语义验证。
- `SHQueryRecycleBinW(E:\)` 返回 `0x80070005`（访问被拒绝），现有总字节数及条目数必须记为 `null`，不能记零。没有枚举无关条目或记录私人物件名。此 API 即使成功也只作为调用安全上下文的 Shell 汇总，不冒称磁盘所有用户的物理占用。
- `OpenInputDesktop` 返回错误 5，无法证明能安全监控并拒绝永久删除提示。STA 初始化、`IFileOperation` COM 激活成功只证明接口可创建；未调用 `SetOperationFlags`、`DeleteItem` 或 `PerformOperations`。
- 令牌只读上下文：`app_container=true`、`elevated=false`、`restricted=false`、会话 1；不记录账号/SID。该结果只描述当前调用上下文，没有申请提权或切换到更高权限进程。
- 因总占用、有效配额及 UI 控制未证实，**真实入站、可恢复条目定位、恢复到新目录及同 hash 闭环均未执行**。没有通过扩大权限、安装依赖、改变配置、修改 ACL 或挤满磁盘来制造正例。

## 命令

从项目根目录执行，所有命令使用现有 `.venv`。只用 Python 标准库和 ctypes Windows 只读 API；不安装任何共享依赖。不使用 win32com/comtypes/send2trash。无额外 C#/PowerShell 辅助程序。

```powershell
# 默认 dryrun：只读探针 + 新建诊断记录目录，不创建夹具或调用动作。
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/recycle_fixture.py

# 显式只读探针，同上。
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/recycle_fixture.py probe

# 新建一组有界合成夹具、本地 guard 检查、新进程重读、失败分支模型。
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/recycle_fixture.py exercise

# 将命令输出的 run_id 代入；inspect 只读取，不写新记录。
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/recycle_fixture.py inspect --run-id RUN_ID

# 重新探测环境并核验既有夹具；生成新报告，不重试任何回收。
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/recycle_fixture.py resume --run-id RUN_ID

# 能力闸门入口：当前实现永远 BLOCKED，绝不会调用真实动作。
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/recycle_fixture.py attempt-fixture --run-id RUN_ID
```

`RUN_ID` 必须是工具返回的 32 位小写十六进制 ID，不是任意文件路径。`exercise` 每次创建新目录，拒绝给定旧 ID；只有它创建合成负例目录。`resume` / `attempt-fixture` 只核对既有源并生成新报告，不重跑模拟或继续真实动作。`inspect` 不创建副本或回收条目。

Python 进程退出码：`0` 仅用于成功的只读 `inspect` / `--help`；`1` 为本地测试失败；`2` 为能力 BLOCKED、guard 拒绝或参数错误。PowerShell/调用器可能包装非零码，机器集成应读取 Python 子进程的 `returncode` 和 JSON 的 `overall`；不能把“0 个本地测试失败”解读为 G1 通过。

## 文件与 guard

- 源码仅 `recycle_fixture.py` 与本说明；不改共享配置、任务卡、交接或其他模块。
- 记录固定追加到 `output/storage_retention/recycle_g1_20261027/recycle_tests/<UTC时间_随机ID>/`，含 `report.json`、同源生成的 `REPORT.md`；拒绝覆盖。错误另存 `diagnostic_<ID>/diagnostic.json`。
- 夹具固定在 `work/storage_recycle_g1_20261027/recycle_fixtures/<新UUID>/`。主组七个文件（六个拟入站源和一个禁止连带的资源），约 8.02 MiB；另有一个未列入清单的微小负例。伪造 manifest / 错误内容的负例各自创建独立新 UUID 目录并保留。不会读取或接收真实项目候选作为源。
- 清单必须逐字结构等于内置合成配方（ID、固定相对路径、长度、SHA-256、是否拟入站）；每个字节都可从 run ID 和配方重建。调用者不能在清单中改填真实文件/hash来通过 guard。
- 拒绝绝对路径、遍历、ADS、未列名文件、连带资源排队；检查全部已存在祖先及文件的 reparse 属性、常规文件类型、单硬链接、长度与 SHA-256。`inspect` 可以验证未排队的资源，但不能把它视作可回收源。
- 这些路径检查不是抵御恶意并发替换的原子删除授权。当前没有动作后端消费 guard，不能据此批准任何真实操作。尚未实际测试 junction/hardlink 攻击或 OS 重启。
- 夹具生成总量上限 16 MiB，写前要求额外至少 256 MiB 可用；使用扩展路径访问长路径，不改 `LongPathsEnabled`。8 MiB 仅代表相对较大夹具，不代表最大文件或容量上限测试。
- 所有夹具、负例和报告均保留。没有恢复副本或新增回收条目。未进行清理、清空回收站、全局配置更改或任何最终释放。

## 矩阵解释

| 范围 | 实际完成 | 能力结论 |
|---|---|---|
| Windows 只读环境 | 卷定位、原始配置、空间读取、STA/COM 激活 | 这些读取/激活成功；回收总量和桌面访问被拒绝 |
| 中文/空格、同名异目录、长路径、8 MiB | 生成、完整 hash、单文件身份、本地 guard | ACTUAL_LOCAL；真实入站和恢复仍 BLOCKED |
| HTML 连接资源 | 独立生成并 hash，拒绝资源加入队列，末尾仍核同 hash | 不能证明 Shell 无连带；真实验证 BLOCKED |
| 真候选/路径越界/ADS/未列名/清单伪造/内容不符 | guard 实际拒绝 | ACTUAL_LOCAL；不是回收实测 |
| 新进程重读 | 独立 Python 子进程加载 manifest 并核验全部 hash | ACTUAL_LOCAL；不是 OS/Shell 重启恢复 |
| 不可用/未知容量/超配额/永久删除风险/UI不可控/磁盘余量不足 | 向同一纯 preflight 函数注入模拟环境 | SIMULATED；没有改变真实环境 |
| 拒绝访问/取消/部分成功/条目身份错配/恢复 hash 不符/重启回执 | 内存状态及 JSON 往返模型 | SIMULATED；没有真实 Shell 调用 |
| synthetic 入站→真实条目识别→新目录恢复同 hash | 未执行 | BLOCKED，G1 未通过 |

模拟回执显式标识 `MODEL_ONLY`。仅“原路径消失”产生 `UNCERTAIN_STOP_NO_RETRY`，不能计成功；部分成功按项记录，不能对整批伪报通过或自动重试。

## Windows Shell 后续实现边界

本交付只保存需求常量，**没有未测试的删除分支**。`attempt-fixture` 不能通过 CLI、环境变量或一份 JSON 解锁动作。有效容量和占用得到可信证据、UI 能安全拒绝永久删除提示后，仍需另行完成并验收 G1 后端；即使换到可交互终端，本版本也不会自动回收。

若后续实现受控夹具入站，应使用 STA `IFileOperation`，同时设置 `FOFX_RECYCLEONDELETE`、`FOF_ALLOWUNDO`、`FOF_NO_CONNECTED_ELEMENTS`，并保留永久删除告警及失败停机语义；不使用 `FOF_NOCONFIRMATION`，不自动同意对话框。仅标志值不构成“可恢复”证明，仍需逐条识别自身夹具条目与真实同 hash 恢复验收。不能用通用文件删除函数替代回收，不能提供 G3 功能。

官方 API 依据（读取于 2026-10-27）：[SHQueryRecycleBinW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shqueryrecyclebinw)、[SHQUERYRBINFO](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-shqueryrbinfo)、[IFileOperation](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nn-shobjidl_core-ifileoperation)、[SetOperationFlags](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperation-setoperationflags)、[PreDeleteItem](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperationprogresssink-predeleteitem)。

## 本轮验收入口

- 最终同代码版本矩阵：[REPORT.md](../../../output/storage_retention/recycle_g1_20261027/recycle_tests/20261026T165510Z_f293680c2e35/REPORT.md)、[report.json](../../../output/storage_retention/recycle_g1_20261027/recycle_tests/20261026T165510Z_f293680c2e35/report.json)。15 项 ACTUAL_LOCAL 通过、18 项 SIMULATED 模型通过、12 项 ACTUAL_SHELL 阻塞，G1 总结论不通过。
- CLI 验证：[cli_validation.json](../../../output/storage_retention/recycle_g1_20261027/recycle_tests/20261026T165510Z_f293680c2e35/cli_validation.json)。默认 dryrun、resume、attempt-fixture 均返回 Python 退出码 2；非法 ID 和任意源参数被拒绝。报告含工具 SHA-256。
- 最终正例夹具 ID：`80c00a47fb534fe793e373c48731b90a`；最长文件路径 433 字符。新进程只读重新核验成功，不代表回收后恢复。
- 早期探针/代码迭代记录及所有夹具、合成负例保留；不覆盖、不清理。日期目录用 UTC，因此北京时间 2026-10-27 的记录显示 `20261026T16…Z`。
