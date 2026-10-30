# G1 纯归档与恢复工具

入口 `archive_store.py`，仅 Python 标准库。仅提供 `build`、`verify`、`restore`；没有删除、移动、回收、清空或释放空间功能。源文件以只读方式打开。此实现不自行生成/批准候选或保护清单，父端须提供过滤后的 manifest；当前使用 `plan_manifest_v2.csv.gz`，旧 v1 只留诊断。

## 接口

以下命令是交接示例，开发测试没有执行真实候选归档。执行位置为项目根目录。所有目录的父目录必须已经存在；vault 和 dest 必须是全新目录。失败目录保留，重试使用新的目录名。

```powershell
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/archive_store.py build --root . --manifest output/storage_retention/recycle_g1_20261027/plan_manifest_v2.csv.gz --vault output/storage_retention/vault_g1_NEW --reserve-free-gib 15 --max-added-gib 10
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/archive_store.py verify --vault output/storage_retention/vault_g1_NEW
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/archive_store.py restore --vault output/storage_retention/vault_g1_NEW --request work/storage_recycle_g1_20261027/request.json --dest work/storage_recycle_g1_20261027/restore_NEW
./.venv/Scripts/python.exe -X utf8 -B scripts/storage_retention/recycle_v1/test_archive_store.py
```

成功退出 0，错误非零；CLI 输出 JSON 状态。缺件、坏卷、预算不足、路径异常、空候选不会冒 PASS。恢复可在新进程中仅凭完整 vault 和请求 JSON 执行，不读取原项目输入或原 manifest。

manifest 是 gzip CSV，UTF-8（兼容 BOM），至少具有 `path,bytes,sha256,classification`。仅处理 classification 精确等于 `ELIGIBLE_A` 的行，其他分类计数后跳过。bytes 为非负十进制整数，sha256 为小写 64 位十六进制。

每个合格 path 必须严格匹配：

```text
output/character_skills/pages/_batch/{ge60,40to59,20to39,remaining}/runs/YYYYMMDDTHHMMSSffffffZ-xxxxxxxx/transactions/<数字cid>/backup/{card.json,index.html}
```

run 后缀为 8 位小写十六进制。路径为项目根相对 POSIX，拒绝绝对路径、反斜杠、空段、`.`/`..`、ADS、Windows 设备名、尾随点/空格、大小写冲突。即使误标 ELIGIBLE_A，`retained_payloads` 或其他形状也会失败。没有测试绕过开关；合成项目根同样模拟真实 A 路径。动态保护集合仍由父端过滤，形状白名单不替代保护清单。

request 为非空 JSON 精确路径数组，例如：

```json
["output/character_skills/pages/_batch/ge60/runs/20261027T123456000000Z-12345678/transactions/30236/backup/card.json"]
```

请求不可含通配符、重复或大小写冲突。dest 必须不存在且与 vault 独立；已有目录也拒绝，因此已有相同或不同文件都不会被覆盖。恢复先全量验证 vault，再对每个待恢复成员在锁定的卷中复核 SHA/长度，随后独占创建新文件并再次核对写入流。Windows 恢复 mtime（100ns 精度），ctime、属性、硬链接数等仅作快照，不恢复 ACL、所有权或硬链接。

## 保管格式和验收

|文件|内容|
|---|---|
|`plan_manifest.csv.gz`|原输入的逐字节快照，记录输入 SHA-256|
|`index.jsonl`|每个合格原 path 一行；sha256、bytes、volume、member、mtime_ns；metadata 内含 ctime_ns/mtime_ns/attrs/linkcount/mode/device/inode|
|`volume-NNNNNN.zip`|ZIP64、DEFLATE level 6；成员名 `sha256/<sha>-<bytes>`|
|`catalog.json`|格式版本、输入与 index SHA、各卷完整 SHA/长度、统计|
|`build_events.jsonl`|开始、源开始/完成、卷关闭、全读回与完成事件；逐事件 flush+fsync|
|`build_report.json`|本次 build 最终 PASS/FAIL、输入 SHA、成功统计/失败进度、预算、catalog SHA|
|`verify_report-<uuid>.json`|独立验证的最终状态、统计、各卷 SHA、index/catalog/input SHA|
|`restore_report-<uuid>.json`|恢复最终状态、请求 SHA、输入 SHA、已恢复路径、失败诊断|

内容按 SHA+长度去重，首个源边压缩边 hash，其余每份源仍完整 hash；每个旧路径都单独保留映射和源元数据。数据流块上限 1MiB，不暂存未压缩全量副本；内存主要随路径映射和 ZIP 成员数量增长。

build 完成前，100% 卷先核容器 SHA/长度，再对 100% 成员解压重算 SHA/长度；对输入合格集合、index 映射、内容位置、实际卷和全部 ZIP 成员集合完整对账。拒绝缺失、多余、重复、zip slip、加密、符号链接成员及非 DEFLATE 成员。完成后才写成功 build 报告；没有有效 PASS build 报告的 vault 不能恢复或验收。catalog/index 的哈希链用于完整性检查，不是外部签名或防恶意改写的认证。

Windows 检查全部祖先及源对象，不跟随 reparse。读取句柄拒绝并发写入和替换；祖先目录句柄拒绝重命名/替换，逐源还核对打开前后身份、长度和时间。`nlink != 1` 一律 HOLD 并使本次 build 失败；NTFS 额外命名数据流同样 HOLD。元数据 `ctime_ns` 保留路径 stat 原值；当前 Windows Python 的路径 stat/句柄 fstat 对 deprecated ctime 语义不同，身份比对使用一致的 birthtime、inode、mtime 等字段。

## 容量、失败和实际边界

- 分卷按实际压缩写入位置达到 512MiB 后切下一卷；成员不跨卷，单卷硬上限 640MiB（包含 ZIP 头与目录）。大成员或接近满卷时可能触碰硬上限并失败；保留该卷，不自动拆分、重试或清理，应先检查单大对象后改用新的有界批次。这个目标不是保证所有卷都 ≤512MiB。
- 每次实际写入检查累计新增高水位字节及当时磁盘空闲，ZIP 回填头不重复计量；manifest 快照、index、ZIP、日志、catalog、build 报告都在 build 预算内。预留 64KiB 诊断空间。预算是逻辑新增字节及磁盘 free 护栏，不是 NTFS 精确簇配额；并行任务仍会改变空闲。
- 失败时不清理任何输出，源不动；未完成/空文件和部分卷均保留诊断。报告本身如果因真实磁盘耗尽/权限或 reserve 无法写入，命令仍失败并向 stderr 报错，不能保证磁盘完全不可写时落盘报告。没有 build PASS 即不合格。
- verify/restore 的独立报告会在 vault 新建 UUID 文件，需要 vault 可写；其新增量不属于先前 build 的预算。恢复展开量也不纳入 build 的 10GiB 上限，调用方应先核请求体积和目标容量。坏档/缺件在建 dest 前失败；写出期间遇到 I/O 或外部干扰可能留部分恢复结果，报告逐项记录，不会覆盖已有对象，也不清理。
- 未宣称全程文件系统快照；某个源核完后仍可能被其他任务修改，后续任何处置必须再次核源 SHA。记录的 logical bytes 不是物理可释放量；所有阶段的 `physical_released_bytes` 都为 0。
- 父端计划先跑 ≤10 文件、≤64MiB 真实微批并恢复核对，再评估扩大。此工具测试不代替该实证，不验证所有磁盘/文件系统或完整 20 万项规模。未在其他操作系统或新装环境中测试。

## 测试留存

每次运行在 `work/storage_recycle_g1_20261027/archive_tests/<uuid>/` 新增，不使用 TemporaryDirectory，不删除或清理旧夹具；最后写 `test_result.json`（含结果、跳过原因、三个交付文件的 SHA）。覆盖去重多映射、不同旧内容、中文/空格项目根、空文件、首源/重复源 SHA 错误、坏卷、请求穿越与冲突、恶意 ZIP 成员、缺件/漏映射、多卷全读回、两个预算、单卷硬上限、卷名被其他文件抢先占用、强制 A 形状、硬链接/reparse/ADS。新进程恢复只提供 vault/request/dest。

Windows 实际硬链接和 junction 创建可能被受限沙箱阻止；这时保留创建诊断并明确 skip，另有 nlink/reparse 属性拒绝单元测试。最终交付回执以所链接的具体 test_result.json 为准，不能把带 skip 的测试称为全部 Windows 实测通过。
