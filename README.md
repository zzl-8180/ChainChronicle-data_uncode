# 锁链战记（チェインクロニクル）数据解包工具

把《锁链战记》日服客户端的游戏数据解包为可读的结构化数据与媒体文件：

- **data5 主表**（77 个加密文件）→ 完整 JSON＋记录视图（records.jsonl，39,047 条）
- **bdl 资源包**（68,655 个）→ UnityFS 对象导出（PNG／WAV／OBJ／TXT／typetree JSON）
- **APK 内置主表**（chronicle.dat）→ ChronicleArchiveData JSON
- 已有字段解释、查询脚本与对照页属研究成果，见 §7 获取方式

## 1. 硬性版本边界

**仅支持 `com.sega.chainchronicle` 5.6.2（versionCode 56021，Unity 2021.3.58f1）。**

解密链钉住以下 SHA-256：APK 签名证书参与密钥派生、`libcompatible.so`（79b6ae19…）、`libChronicleNUtils.so`（adc5f1d9…）、恢复镜像（3fd354b5…）。**其他版本会明确报哈希错误，不会静默产出错误数据**；适配新版本需要重新做原生恢复，不在本工具范围。

## 2. 环境要求

| 项 | 要求 |
|---|---|
| 系统 | Windows 10/11＋Python 3.12（本项目实测 3.12.14）。Linux/macOS 与其他版本未实测（依赖均跨平台，预期可移植，需自行验证） |
| 依赖 | `pip install -r requirements-lock.txt`（unicorn、capstone、pyelftools、UnityPy、Pillow、lz4 等 20 个包） |
| 输入 1 | 兼容版本的 APK 文件（自行准备，如命名为 `チェンクロ.apk` 放仓库根目录） |
| 输入 2 | 游戏外部缓存（`Android/data/com.sega.chainchronicle/files` 下的 data5／bdl；自行采集，见 §6） |
| 可选 | ADB platform-tools：仅采集缓存需要；离线解包不需要 |

路径含中文／空格可以工作；以下命令一律在**仓库根目录**执行（脚本使用相对路径）。

## 3. 安装

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

下文均以 `& .\.venv\Scripts\python.exe -B scripts/<脚本>` 形式调用。

## 4. data5 解包（核心链路，已在干净目录实测）

首次运行需从 APK 生成三个前置文件（确定性的，内容与输入绑定）：

```powershell
# A1 提取 APK 程序/配置 → work/apk/、output/apk/baseline.json
& .\.venv\Scripts\python.exe -B scripts/apk_baseline.py チェンクロ.apk
# A2 解析保护库重定位 → output/protection/relocations.json
& .\.venv\Scripts\python.exe -B scripts/elf_relocations.py work/apk/lib/arm64-v8a/libcompatible.so
# A3 恢复 NUtils 原生镜像 → work/protection/nutils_loader_seed1.bin
& .\.venv\Scripts\python.exe -B scripts/signal_region_probe.py --loader-probe
```

然后解码 data5：

```powershell
# B1 解码目录内全部 data5 → output/decoded/（.json + .json.raw + report.json）
& .\.venv\Scripts\python.exe -B scripts/decode_data5.py --input <data5目录> --output output/decoded
# B2 导出记录视图 → <新输出目录>/decoded、records.jsonl、tables.csv、decode_report.json
& .\.venv\Scripts\python.exe -B scripts/decode_cache_snapshot.py --work <含data5的目录> --output <新输出目录>
```

- 中断或换机重跑：`--reuse-dir <旧输出目录>` 在密文＋JSON 哈希一致时安全复用；`--prior-report <旧report.json>` 指定 decode_data5 旧报告（不存在时自动改为全原生解码并注明）。
- 输出目录必须不存在（`exist_ok=False`），防止覆盖历史成果。
- 两种包装变体（gzip 偏移 6／偏移 0）自动识别；超大文件自动使用有界提升的指令上限，算法不变。

## 5. bdl 资源解包（已在干净目录小样本实测）

bdl 前 256 字节经原生 `DecodeXorData` 转换后即标准 UnityFS，由 UnityPy 展开。输入清单为 JSONL，每行：

```json
{"path":"files/Bundle/<类别>/.../<名>.bdl","bytes":<大小>,"work_file":"<本地文件路径>"}
```

从工作副本生成清单的最小示例：

```powershell
& .\.venv\Scripts\python.exe -B -c "import json;from pathlib import Path;root=Path('work/my_cache');f=open('my_inventory.jsonl','w',encoding='utf-8');[f.write(json.dumps({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'work_file':str(p)},ensure_ascii=False)+'\n') for p in sorted(root.rglob('*.bdl'))];f.close()"
```

运行（分片续跑，中断自动跳过已完成）：

```powershell
& .\.venv\Scripts\python.exe -B scripts/full_unpack_run.py --inventory my_inventory.jsonl --output output/my_unpack --workers 8
& .\.venv\Scripts\python.exe -B scripts/full_unpack_merge.py --inventory my_inventory.jsonl --output output/my_unpack
& .\.venv\Scripts\python.exe -B scripts/full_unpack_verify.py --inventory my_inventory.jsonl --output output/my_unpack
& .\.venv\Scripts\python.exe -B scripts/full_unpack_finalize.py --output output/my_unpack
```

- 前置文件默认读 §4 的相对路径；也可用 `--native-image <镜像>`、`--apk <APK>` 或 `--cert-hex <签名证书hex>`（免 APK，证书可用 `scripts/apk_certificate.py` 从 APK 提取）覆盖。
- 产物：`objects/<类别>/<包名>/`（PNG 原尺寸含透明、WAV 无损 PCM、OBJ 网格、TXT、typetree JSON）＋每包 `objects_index.json`＋`ledger.jsonl`／`coverage.json`／`validation.json`。

## 6. （可选）采集游戏缓存

需要一台已授权 Android 设备、ADB 与本机 `tools/platform-tools/adb.exe`；全程只读，不改手机：

```powershell
& .\.venv\Scripts\python.exe -B scripts/phone_collect.py probe --output output/my_probe
& .\.venv\Scripts\python.exe -B scripts/collect_cache_archive.py --probe output/my_probe --snapshot raw/<新快照名>
& .\.venv\Scripts\python.exe -B scripts/extract_cache_archive.py --snapshot raw/<新快照名> --work work/<新工作目录> --output output/<提取报告>
```

## 7. 查看结果与研究成果

- `records.jsonl`：每行一条记录视图（原值、来源、JSON pointer、字节区间）；`tables.csv` 为表索引。
- APK 内置主表（chronicle.dat）：`scripts/native_debug.py work/apk/lib/arm64-v8a/libChronicleNUtils.so` 后运行 `scripts/decode_chronicle.py` → `output/base_master/`。
- 字段字典、技能数值解释、对照页与查询脚本属**研究成果包**（另行发布，见发布清单）；查询示例：`scripts/query_effect_dictionary.py --id 43023606`（需研究成果数据文件）。
- `scripts/build_char_roster.py` 需要 v3 主表与 bdl 头像产物，属展示线。

## 8. 已知限制

- `verify_cache_snapshot.py`、`verify_cache_refresh.py` 是本项目特定快照的回归工具（硬编码本次文件数／哈希），不适用于你的快照。
- `analyze_cache_snapshot.py`、`export_master.py` 及 `chica_*`／`boss_*`／`ordinary_*_probe.py` 属字段解释研究线，依赖本项目历史证据文件，不能独立运行。
- 全新机器从零安装、非 Windows 平台未实测；chronicle 链路依赖已随 §4 生成的镜像，但其独立复跑未在干净目录完整验证（状态见发布清单）。
- 不声明全游戏覆盖；私有目录与服务端内容不在范围。
- **版权边界**：APK、游戏缓存与解包出的媒体为 SEGA 所有，本仓库只含自有工具源码；请勿公开分发游戏资源。

## 9. 仓库结构

| 路径 | 内容 |
|---|---|
| `scripts/` | 全部解包／验证源码（含 `full_unpack_*.py` bdl 管线、`release/` 打包脚本） |
| `docs/` | 任务交接与实施方案（含可复现性审计 `docs/tasks/20261016-reproducibility-audit.md`） |
| `AGENTS.md` | 项目工作约定（协作、证据、Git 与分层发布规范） |
| `HANDOFF.md`／`STATUS.md` | 当前进度入口与历史状态 |
| `requirements-lock.txt` | 锁定依赖版本 |
| `raw/`、`work/`、`output/`、`.venv/`、`tools/` | 本地输入与产物，**不入库**（见 `.gitignore`） |
