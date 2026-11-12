# 研究／恢复线只读维护入口

本目录只准备迁址后的读取方式。**尚未真实迁址，没有删除、搬迁、恢复、重跑研究对账、运行主线或打包。** 旧脚本、历史manifest、P_preservation及四份closeout plan保持原字节。

入口是 `scripts/project_layout/retirement_runtime.py`，仅用标准库。它明确读取本目录的 `locations.json`，并核对原完整处置表的6935行来源身份，SHA-256为 `274c6cd5602b591047ce2b2c907b4e5d9bb33ff55b190b0bb8678ec586e82ef1`。新表只收录四项必要保留身份，不复制完整处置表。每项的来源、目标、处置和大小必须匹配冻结表；只读内容还须匹配新表记录的字节数与SHA-256。

`--location current` 仅用于本轮现址核验；`archive` 只解析 `operations/history/retired-packaging/20261108/` 的声明目标，不向旧 `output/share_bundle` 回退。未声明项（包括DELETE）、错误来源、目标不符、路径越界和身份不符均拒绝。`resolve` 只打印声明位置，不检查存在性；实际内容命令读取新位置，缺件立即报错。

## 当前可用命令

以下命令从仓库根目录运行，均不写业务输出；JSON打印到标准输出。

```powershell
& .\.venv\Scripts\python.exe -B scripts/project_layout/retirement_runtime.py --repo . --mapping docs/project-layout/20261108-packaging-runtime-ready-v1/runtime/locations.json --location current preservation

& .\.venv\Scripts\python.exe -B scripts/project_layout/retirement_runtime.py --repo . --mapping docs/project-layout/20261108-packaging-runtime-ready-v1/runtime/locations.json --location current skill-manifest 20261021 --member pages/1/card.json

& .\.venv\Scripts\python.exe -B scripts/project_layout/retirement_runtime.py --repo . --mapping docs/project-layout/20261108-packaging-runtime-ready-v1/runtime/locations.json --location current skill-manifest 20261022 --member pages/1/card.json
```

`skill-manifest` 也可用 `--sha256 <摘要>` 查历史身份；省略筛选时只列manifest身份、campaign与声明数量。它不读取manifest内所指的card／HTML／媒体，不执行旧 `continue_recovery_20261024.py`。两旧ZIP在本轮检查前已经缺失，结果明确标记 `ZIP_ALREADY_MISSING_NOT_RECOVERED`，没有恢复内容。

`preservation` 读取冻结 `P_preservation.json` 的第222项，以旧逻辑路径定位新物理位置，再核实际字节。必须是 **12340字节 / b74e4681d492fbf0f7258e138669abf91bba23c27e091f865deae428ec4e9ee2** 的旧构建器；当前12508字节版本不能替代。

## 迁址后才可使用的命令

将上述内容命令的 `current` 改成 `archive` 即读取目标位置。现在目标尚未迁入，不能声称它们已经可从真实归档目录读取。

以下命令只**打印**两条带显式路径的命令，不运行它们，不创建 `--output` 目录：

```powershell
& .\.venv\Scripts\python.exe -B scripts/project_layout/retirement_runtime.py --repo . --mapping docs/project-layout/20261108-packaging-runtime-ready-v1/runtime/locations.json --location archive commands --output work/packaging_runtime_reconcile_after_move
```

打印结果包含可直接复核的argv数组和PowerShell命令：

- 研究对账：现有 `scripts/character_skills/reconcile_mechanism_first_handoff_20261104.py`，显式 `--bundle <归档payload>` 和 `--output <用户指定位置>`。该业务会读取当前主线并写输出；本任务仅输出命令，未运行。旧默认bundle不再作为迁址后的现行用法。
- payload核验：复用新只读 `docs/project-layout/20261108-packaging-full-retirement-v1/retained/check_relocated_payload.py --repo <仓库> --payload-root <归档payload> --run-frozen-verifier`。此入口禁止旧share_bundle访问；当前原位置不能作为其payload-root。

## 针对性验证与实际结果

可重跑测试，输出JSON到标准输出（本次保存为 [verification.json](verification.json)）：

```powershell
& .\.venv\Scripts\python.exe -B docs/project-layout/20261108-packaging-runtime-ready-v1/runtime/verify_runtime.py --repo .
```

测试导入并调用真正的新代码，还通过CLI核P；不导入旧恢复／清理模块。archive测试先将现存四文件读入RAM，然后把源字节映射到声明目标路径，拦截实际新代码的文件读取；整个archive阶段禁止旧share_bundle的文件读取、列目录或打开。未在磁盘复制这两份约2MB的manifest；没有假称完成实际迁址。

本轮结果 `PASS_TARGETED_READONLY_RUNTIME`：

| 检查 | 结果 |
|---|---|
| P旧构建器 | 12340字节，冻结第222项字节数和SHA-256相符 |
| 两旧技能manifest | 1957351 / 1960840字节，分别核SHA-256；各13384条声明；成员与SHA查询相符 |
| 研究manifest | 45882字节，SHA-256 `ae3a591d1dd35be221294a6418ca7455c9ec1184f247192cfee6c0f80bdef051` |
| archive RAM读取 | 四项新目标读取成功，`old_root_access_attempts=[]` |
| 负例 | 缺新物件不回退；12508字节P替代品、DELETE身份、越界、错误来源全部拒绝 |
| 命令输出 | 新bundle、显式output与新checker参数存在；`executed=false` |
| 独立readback复用checker | 135成员、4份历史plan的manifest身份、冻结verifier均通过；旧根访问0 |

独立checker使用原已存在的 `work/mechanism_first_handoff_20261104/isolated_readback/`，没有复制或修改它；本次只再核一次，不跑全对账。冻结verifier也只检查历史研究闭包，不晋级任何主线结果。测试和入口使用 `-B`，语法检查用 `ast.parse`，不写pyc。新代码与mapping的最终SHA-256见verification.json；本次没有删除或移动任何文件。
