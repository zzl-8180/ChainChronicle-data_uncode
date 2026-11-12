# R01 临前 survivor 内容门（待父聊天／Astra 验收）

仅新增只读检查器 `scripts/project_layout/check_retirement_survivors.py` 和本目录材料。未迁移、删除、切换 junction、执行旧工具或主线生成，未改冻结清单、原审查、原 verification 或共享根。

本轮真实 **current 模式 1,406／1,406 匹配，失败 0**；1,270 外部 survivor 中 **87** 项实测为多硬链接，源／survivor 同文件 ID 为 0。物理身份绑定缓存后新读取 **1,880,958,800 B**（含四份冻结证据），见 [current-full1406.json](current-full1406.json)。它是当前位置观察回执，不是未来删除授权、句柄锁或真实迁址验收。

## 检查合同

- 固定解析 1,270 份原双端 proof、136 份 readback proof 和 1,406 条终态链；完整表及三份 proof／mapping 文件 SHA 在检查器中锁定。长度、SHA 与原记录比较，不能用“有新版”继续删。
- 1,270 项外部 survivor 必须在完整处置表之外且终态不变；136 项的 survivor 必须逐条映射到 `REHOME_BUSINESS` 保留 payload 和明确最终 target。当前／终态 survivor 任何一个进入 DELETE 都拒绝。
- 每源均核冻结 `current_identity` 的 bytes／mtime_ns／dev／ino／nlink。这 1,406 项没有 execution-overlay 授权更新，故仍严格用原身份，不套用其他行的 README 更新。
- 每文件有界流式哈希；读取前后核路径 stat、handle fstat、父路径 ID、reparse、普通文件和内容长度。ctime 在 stat→stat、fstat→fstat 内比较，避免 Windows 两 API ctime 语义差异。整对完成后再次核两端 stat（含 ctime）与祖先 ID；source 不能在另一端读取期间悄然漂移。
- 同一进程只复用已新算哈希且 dev／ino／size／mtime／ctime／nlink／mode／attributes 全部仍一致的物理文件；缓存命中也打开指定路径并核 handle、祖先和整对末端身份。多硬链接 survivor 正常记录并允许稳定者；源与 survivor 同文件 ID 拒绝。
- 默认 `current`，136 项读原 payload 当前位置；未来临删必须用 `archive`，136 项**只读终态归档 target，不回退 current**。1,270 外部位置在两模式相同。
- 按来源根分八组；任意 pair 失败，该组所有 pair 都标 `group_stopped=true`／`source_should_keep=true`。无漂移的独立组可另行复核，但最终必须有完整 1,406 项的新回执。`--group` 的局部 PASS 永远不满足 `full1406_content_gate_pass`，退出码为 2；局部结果不可拼接冒充一次总门。
- `source_should_keep=false` 只表示该组此次 R01 内容检查未阻断；`deletion_authorized` 始终 false，仍须其余实际执行门和用户精确授权。新回执不保证完成到实际删除之间无人写入；执行者须按组临前运行，期间发生写入／身份漂移则保留该组并重审，不要求主线全局停工。
- 检查器无迁移、删除或联接能力，唯一写入为显式 `--report`。父目录须预先存在且无 reparse；报告须是本目录下的新文件，`open('x')` 拒绝覆盖。明确其他独立位置时须同时给 `--independent-report`。不得把原 verification 或旧回执作为目标。

## 命令

本轮已运行（不可重用同一报告名）：

```powershell
& .\.venv\Scripts\python.exe -I -B scripts/project_layout/check_retirement_survivors.py --report docs/project-layout/20261108-packaging-execution-v1/r01/current-full1406.json
```

未来真实迁址等前置完成后，用另一个不存在的报告名全量检查（本轮未运行此命令）：

```powershell
& .\.venv\Scripts\python.exe -I -B scripts/project_layout/check_retirement_survivors.py --mode archive --report docs/project-layout/20261108-packaging-execution-v1/r01/archive-full1406-NEW.json
```

单组诊断示例：`--group work/review_20261017`。八组 source 根及本轮数量：

| 组 | pair 数 | 失败 |
|---|---:|---:|
| output/share_bundle/20261025-character-tools | 920 | 0 |
| work/delivery_20261016 | 163 | 0 |
| work/mechanism_first_handoff_20261104 | 136 | 0 |
| work/repro_20261016 | 96 | 0 |
| work/review2_20261016 | 8 | 0 |
| work/review_20261016 | 4 | 0 |
| work/review_20261017 | 1 | 0 |
| work/review_20261017_r1 | 78 | 0 |

## 针对验证与保留诊断

```powershell
& .\.venv\Scripts\python.exe -I -B docs/project-layout/20261108-packaging-execution-v1/r01/test_survivors.py
```

最终 **20／20 PASS，失败 0、错误 0**，回执 [targeted-tests-20261108T034116136068Z.json](targeted-tests-20261108T034116136068Z.json)。覆盖 source／survivor 漂移、整对窗口 source 漂移、真实 3 B NTFS 多硬链接 survivor 变更、源同 inode 拒绝、源缺失、archive 缺失绝不回退、DELETE survivor、未声明终态 target、reparse 模拟、越界、大小上界、handle 变化、冻结源身份变化、Windows stat／fstat ctime 语义差、分组全保留及局部不通过最终门、新报告拒绝覆盖／越界写入。

第一次运行是 19 PASS＋1 ERROR（沙箱内 `os.link` 返回 `PermissionError: [WinError 5]`），[原计数回执](targeted-tests.json)保留未覆盖。测试本身未失败在内容断言；唯一错误位于 `os.link(self.survivor, linked)`。随后仅为新 r01 小夹具 NTFS 硬链接创建进行窄范围提升运行，通过自动审查并 20／20 PASS；没有自动审批拒绝，没有修改业务文件。失败夹具和成功夹具都保留，测试新运行使用新时间戳目录与新回执，禁止清理旧诊断。

reparse／并发身份变化以真实检查函数配合小夹具／受控 API 注入验证；未实际创建 reparse 或做真实业务并发、迁址、删除。读取后的内容门依然是有限观察，不冒称 OS 原子删除事务。

父聊天实施前捕获的 57 份保护 hash 入口为 `../protected-before.json`；本目录 `protected-after.json`记录对照结果。新增完整代码差异见 [checker.diff](checker.diff)。仍待父聊天／Astra 独立审查，不自行关闭原 R01。
