# R02：逐历史入口只读验收

状态：`IMPLEMENTED_AND_CURRENT_OLD_READBACK_PASS_WITH_SCOPE_LIMITS`。本修正只增加 [独立 checker](../../../../scripts/project_layout/check_retirement_alias.py) 和本目录；原 `check_handoff.py`、原审查、原验证回执、冻结完整处置表和 P/v7 未改。当前真实迁址、删除、junction 创建／切换均为 0。

## 入口和通过口径

checker 的标准输出是 JSON，成功退出 0，拒绝／缺件退出 1；参数语法错误由 argparse 退出 2。checker 不写回执，不创建目录、不改名、不跟随未知联接、不启动旧业务／旧 verifier。单独的 [回执采集器](collect_readonly_receipts.py) 只在本 `r02` 下的**新子目录**写新回执，拒绝覆盖已有目录。

- `--cycle C14`（到 C18）：仅验该周期正式 `share_bundle`；其他周期可以仍在旧状态。
- `--alias-path <绝对路径>`：只接受 C14—C18 批准 `output` 父目录下的 `share_bundle`、`share_bundle.retirement-next-20261108`、`share_bundle.retirement-previous-20261108`。同时传 `--cycle` 时必须一致；拒绝任意目录、未知 basename、其他 junction。入口位置不靠调用者任意指定。
- `--all`：五个正式入口聚合。未提供选择参数时也聚合五个正式入口；`--all` 不可与单入口参数混用。
- `--expected-target old`：精确旧根 `output/share_bundle`；旧入口 file ID 还必须等于原 `current-junction-check.json` 已记录值。
- `--expected-target new --new-target <绝对批准根>`：唯一批准新根为 `operations/history/retired-packaging/20261108/share_bundle`，不接受任意替代目录。
- `--identity-only`：**仅用于第一次改名后、正式名缺失窗口中的单个 previous，且必须 old 模式**。只核 previous 对象的 mount-point tag、精确旧 target、原 file ID 与父祖先身份；不访问旧根内容、不核 P/v7，输出 `IDENTITY_PASS`、`content_checked=false`、0 内容读取。正式名还存在时拒绝此阶段命令；previous 不允许完整内容模式，formal／next 不允许 identity-only。它不表示可回滚或内容完整。

每个 `CONTENT_PASS` 都通过**该 alias 自己的拼写**读取并核验 142 个不同文件：135 payload、payload manifest、3 个外围研究文件、两份历史恢复 manifest、P 指定 12,340 B 源码。研究保留树为 139 文件；旧树另有一个已知 ZIP 候选，仅允许它作为未读取的额外文件，新树不允许它混入。每个入口还核 P/v7 冻结 SHA。不会先 `resolve()` 后改用全局 target 打开文件。

路径检查从祖先向下进行：除唯一批准 consumer mount-point alias 本身之外，alias 父链、目标根与祖先、payload 内部、恢复 manifest 与 P 路径都必须是普通真实目录／文件。拒绝 tag 非 `0xA0000003`、普通目录冒充 junction、未知 target、新根／深层别名回旧根或解析出界。读取结束再次核入口 tag、target、file ID 与父链身份。此检查不提供原子快照，也不能排除检查与打开之间的全部竞态；仍需已批准的负责人短窗口。

## 分阶段只读命令

从仓库根运行。以下仅为 checker 命令；不创建／改名任何真实对象。每次用新的回执文件名；`Out-File` 使用 `-FilePath`、`-NoClobber`，并保留 native checker 的 `$LASTEXITCODE`。目录由未来执行记录的整合者提前准备，不用旧回执路径。

```powershell
$ErrorActionPreference = 'Stop'
$checker = 'scripts/project_layout/check_retirement_alias.py'
$history = 'E:\代码项目\锁链战记数据解包\operations\history\retired-packaging\20261108\share_bundle'
$aliasParent = 'E:\代码项目\锁链战记数据解包\work\c14_delivery_20261103\impl\isolation_input\output'

# 迁出前：原正式入口完整读（目前可运行）。
& .\.venv\Scripts\python.exe -I -B $checker --repo . --cycle C14 --expected-target old |
    Out-File -FilePath '<新的独立目录>\C14-before-old.json' -Encoding utf8 -NoClobber
$checkExit = $LASTEXITCODE
if ($checkExit -ne 0) { throw "C14 old checker exit=$checkExit" }

# 保留材料已迁址且临时 next 已由获授权接管者建立后：临时入口完整读。
& .\.venv\Scripts\python.exe -I -B $checker --repo . --cycle C14 --expected-target new --new-target $history --alias-path (Join-Path $aliasParent 'share_bundle.retirement-next-20261108') |
    Out-File -FilePath '<新的独立目录>\C14-next-content.json' -Encoding utf8 -NoClobber
$checkExit = $LASTEXITCODE
if ($checkExit -ne 0) { throw "C14 next checker exit=$checkExit" }

# 第一次 old -> previous 改名后：正式名短暂缺失；只读 previous 对象身份。
# 不要求已迁空的旧根仍有旧内容，也不把 IDENTITY_PASS 当 CONTENT_PASS。
& .\.venv\Scripts\python.exe -I -B $checker --repo . --cycle C14 --expected-target old --alias-path (Join-Path $aliasParent 'share_bundle.retirement-previous-20261108') --identity-only |
    Out-File -FilePath '<新的独立目录>\C14-gap-previous-identity.json' -Encoding utf8 -NoClobber
$checkExit = $LASTEXITCODE
if ($checkExit -ne 0) { throw "C14 previous identity checker exit=$checkExit" }

# 第二次 next -> formal 改名后：立即完整读新正式入口。通过后才处理下一周期。
& .\.venv\Scripts\python.exe -I -B $checker --repo . --cycle C14 --expected-target new --new-target $history |
    Out-File -FilePath '<新的独立目录>\C14-new-formal-content.json' -Encoding utf8 -NoClobber
$checkExit = $LASTEXITCODE
if ($checkExit -ne 0) { throw "C14 new formal checker exit=$checkExit" }

# 五周期各自完成上面的完整新正式验收后，才作最终聚合。
& .\.venv\Scripts\python.exe -I -B $checker --repo . --all --expected-target new --new-target $history |
    Out-File -FilePath '<新的独立目录>\all-five-new-content.json' -Encoding utf8 -NoClobber
$checkExit = $LASTEXITCODE
if ($checkExit -ne 0) { throw "Aggregate new checker exit=$checkExit" }
```

这组命令补齐 R02 的过程验收能力，不授权任何物理步骤。旧 target 已迁空时，第一次改名后的 previous 仅是停用证据；不盲目改回正式名，不要求通过旧内容检查。新正式内容检查失败后停止该周期、保留证据，按整合者的回退合同处理，不继续下一周期。

## 本轮已运行与证据

[汇总及原件前后 SHA](verification-v1/collection.json)记录了实际命令、退出码、时间、checker 哈希，以及 14 份原件前后身份相同：原 checker／基线／旧回执／旧 README／旧方案／旧测试／旧模拟，原第三方 REPORT 与 verdict，冻结完整处置表，旧 runtime verification，P/v7，研究 manifest。

| 实际对象 | 回执 | 结果 |
|---|---|---|
| C14 原正式入口 | [C14-old.json](verification-v1/C14-old.json) | CONTENT_PASS；142 文件；54,055,337 B |
| C15 原正式入口 | [C15-old.json](verification-v1/C15-old.json) | CONTENT_PASS；142 文件；54,055,337 B |
| C16 原正式入口 | [C16-old.json](verification-v1/C16-old.json) | CONTENT_PASS；142 文件；54,055,337 B |
| C17 原正式入口 | [C17-old.json](verification-v1/C17-old.json) | CONTENT_PASS；142 文件；54,055,337 B |
| C18 原正式入口 | [C18-old.json](verification-v1/C18-old.json) | CONTENT_PASS；142 文件；54,055,337 B |
| 五原正式入口聚合（另一次逐入口读取） | [all-five-old.json](verification-v1/all-five-old.json) | CONTENT_PASS；5 × 142 文件 |
| 真实新根尚未落地 | [real-new-root-unavailable.json](verification-v1/real-new-root-unavailable.json) | 预期 FAIL_ALIAS_CHECK，退出 1，不能宣称 new 通过 |
| RAM 核心合同 | [ram-contract.json](verification-v1/ram-contract.json) | 6 类正例、46 类拒绝例、1 个变异回归捕获 |

RAM 测试使用真实 checker 核心，只替代文件系统接口和测试内容身份；未创建真实 junction，不复制大型 payload。覆盖临时 next 完整读、第一次改名 formal 缺失且旧根内容清空时 previous 0 内容读、第二次改名后新正式完整读、单 C14 已新而其余四旧时单入口通过／聚合 new 拒绝、五新入口各 142 次独立 alias 拼写读取，以及普通目录、未知 target、cycle 不符、根／祖先／深层 payload／P／恢复路径 reparse、出界、5 基线漂移、P 错用 12,508 B、读取期间 alias 身份变化和只读 audit 拒绝。

测试的独立 read-log oracle 断言每个 alias 的 142 个文件集合，另故意注入“全局 target 全量哈希、每 alias 只读两件”的退化实现，确认被抓为 `2/142`。不能仅靠 checker 自报计数证明逐 alias 读取。测试还断言生产中复制的 5 个基线及旧 file ID 与原冻结记录完全相同。

复跑 RAM 测试只打印 JSON：

```powershell
& .\.venv\Scripts\python.exe -I -B docs/project-layout/20261108-packaging-execution-v1/r02/test_alias_contract.py
```

需要新一轮当前旧入口检查时，用**新的、尚不存在**的本目录子目录采集；该采集器限当前旧入口状态，真实切换后应使用前述分阶段 checker 命令，不把此旧状态采集器当切换流程。

```powershell
& .\.venv\Scripts\python.exe -I -B docs/project-layout/20261108-packaging-execution-v1/r02/collect_readonly_receipts.py --output docs/project-layout/20261108-packaging-execution-v1/r02/<新的回执目录>
```

补充收集器边界修正：`validate_output()` 在mkdir／subprocess之前拒绝 `..`、r02外路径、已有目标和不安全父路径，检查真实父目录及canonical包含性。[新增边界回执](collector-boundary-test-v1.json)记录8个拒绝例与1个合法新子路径（仅验证、未创建）；原verification-v1回执不覆盖，也未为此重复真实五入口全量读。

未核：真实新归档根／临时／previous／新正式验读，NTFS 两次 rename 或竞态消除，临窗负责人当前活动、真实迁址、完整历史 postcheck、旧 ZIP 重放和主线运行；不得将 RAM 或当前 old 通过替代这些未来门槛。负责人接管已由主持intake确认，尚待的是窗口落实与临窗再次核对，不再重复要求寻找负责人。
