# 任务：可复现性审计与 GitHub 交付规范（2026-10-16）

- 状态：第一、二阶段完成；审查整改完成（P1-1 待提交清单已列，等用户授权提交；其余 P1-2／P2-1—P2-4 均改完并复验 PASS，见文末「审查整改记录」）
- 负责人：本轮 OpenCode 对话（用户直接指派，兼本轮整合者）
- 写入（本任务所有）：`docs/tasks/20261016-reproducibility-audit.md`（本文件）、`AGENTS.md`（§2/§3 小补、§7 GitHub 存储策略、§8 重构）、`scripts/apk_baseline.py`、`scripts/decode_cache_snapshot.py`、`scripts/signal_region_probe.py`、`scripts/jni_prefix_probe.py`、`scripts/metadata_decode_probe.py`、`output/apk/baseline.json`（生成器变更后重建）、`work/repro_20261016/`（隔离测试区）
- 共享文件：HANDOFF.md／STATUS.md 由本任务在结束时追加一节，不覆盖既有内容
- 未改：原始采集件、v3／E／refresh 正式成果、独立审查报告、full_unpack 产物、其他任务输出；未提交 git、未推送、未打包上传

---

## 1. 审计范围与方法

目标：判断第三方仅凭 GitHub 仓库（git HEAD 109 个跟踪文件）＋自行提供的兼容 APK＋自行提供的游戏缓存，能否独立解包，并定位具体失败步骤。

方法：
1. 通读核心链路脚本，梳理每个脚本的输入、隐含读取和硬编码。
2. 用 `git archive HEAD` 在 `work/repro_20261016/isolated/` 构建**仅含仓库文件**的隔离目录，复制 APK 与 2 个样本 data5（charainfo、skilllist），用项目 `.venv` 解释器（模拟依赖已安装）逐步执行链路。
3. 先记录 HEAD 原始状态的实际失败点，再应用最小修复，重跑至全部通过，并用 SHA256 与既有可靠结果做字节级对照。
4. output/、work/、raw/ 用 robocopy 只读统计，不逐文件分析。

结论分级：**【实测】**本轮隔离环境实际运行；**【推断】**根据代码阅读判断，未实际复跑；**【未验证】**本轮无法或尚未检查。

## 2. 版本与输入边界（有意设计的安全边界，不是缺陷）

- 仅支持 **com.sega.chainchronicle 5.6.2 / versionCode 56021（Unity 2021.3.58f1）**。
- 硬编码 SHA256 钉住：`libcompatible.so`（79b6ae19…）、`libChronicleNUtils.so`（adc5f1d9…，native_debug.py）、恢复镜像 `nutils_loader_seed1.bin`（3fd354b5…，decode_data5.py）。
- data5 密钥由 **APK 签名证书＋原生代码**派生；换 APK 版本整条原生恢复链失效，需重新逆向。版本不匹配会明确报错（哈希校验），不会静默产出错误数据。
- 其他 APK 版本、其他游戏：不适用。

## 3. 第三方输入清单

| 输入 | 来源 | 说明 |
|---|---|---|
| 兼容 APK（如 `チェンクロ.apk`，96MB） | 用户自行提供 | 用于提取库／资产及签名证书；只读 |
| 游戏缓存 data5（77 个）／bdl（按需） | 用户自行采集或既有归档 | 采集链见 §4 阶段 C；也可只提供 data5 做结构化解包 |
| Python 3.12＋requirements-lock.txt（20 包） | 公开渠道 | 本项目实测 3.12.14；Windows 实测，其他平台【未验证】 |
| ADB platform-tools | 仅采集需要 | 离线解包不需要 |

## 4. 解包链路与逐步状态

### 阶段 A：APK 准备（纯离线）

| 步骤 | 命令（项目根目录） | 产出 | 状态 |
|---|---|---|---|
| A1 | `scripts/apk_baseline.py <APK>` | `work/apk/*`（44 文件）、`output/apk/baseline.json` | 【实测】本轮修复后通过 |
| A2 | `scripts/elf_relocations.py work/apk/lib/arm64-v8a/libcompatible.so` | `output/protection/relocations.json`（2855 项） | 【实测】通过 |
| A3 | `scripts/signal_region_probe.py --loader-probe` | `work/protection/nutils_loader_seed1.bin` | 【实测】本轮修复后通过；镜像 SHA256＝钉住值＝本项目既有文件 |
| A3′ | `scripts/signal_region_probe.py --loader-probe --library-name libil2cpp.so` | `work/protection/il2cpp_loader_seed1.bin` | 【推断】字段解释线需要，data5 解码不需要；本轮未复跑 |
| A4 | `scripts/native_debug.py work/apk/lib/arm64-v8a/libChronicleNUtils.so` | `output/native/recovered_symbols.json` 等 | 【推断】输入齐全，链路完整；chronicle 解码需要 |

### 阶段 B：data5 解码（核心目标，已实测复现）

| 步骤 | 命令 | 产出 | 状态 |
|---|---|---|---|
| B1 | `scripts/decode_data5.py --input <data5目录> --output output/decoded` | 每文件 `.json`＋`.json.raw`＋report.json | 【实测】2 样本与既有参考字节一致 |
| B2 | `scripts/decode_cache_snapshot.py --work <缓存工作副本> --output <新目录> [--reuse-dir <旧>] [--prior-report <旧报告>]` | `decoded/`、`records.jsonl`、`tables.csv`、`decode_report.json` | 【实测】修复后两种模式通过；项目侧 77 文件重放与 v3 规范化后 0 差异 |
| B3 | `scripts/analyze_cache_snapshot.py --input <目录>` | 字段字典、覆盖审计、引用分析 | 【未解决·研究线依赖】硬编码读 `output/sample/active_skill_trace.json` 与 `output/export/latest.json` 正式 E 构建；第三方缺失会失败。不影响 B1—B2 核心交付 |
| B4 | `scripts/verify_cache_snapshot.py --input <目录>` | 13 项检查 | 【设计如此·不适用第三方】本项目快照专用回归：硬编码 68828 文件／77 data5／39047 记录及 `output/phone_full_20261015` |

### 阶段 C：缓存采集（需手机＋ADB，已有缓存则跳过）

| 步骤 | 命令 | 状态 |
|---|---|---|
| C1 | `scripts/phone_collect.py probe` → probe.json＋inventory.jsonl | 【推断】本轮无手机未验证 |
| C2 | `scripts/collect_cache_archive.py --probe … --snapshot raw/<新>` | 【推断】 |
| C3 | `scripts/extract_cache_archive.py --snapshot … --work work/<新> --output <报告目录>` | 【推断】纯本地 tar 处理，输入齐全即可运行 |
| C4 | `scripts/verify_cache_refresh.py` → composite_inventory.jsonl | 【设计如此·不适用第三方】全硬编码本项目两次快照；第三方单次采集无此清单（见 §6.5 替代方案） |

### 阶段 D：APK 内置主表

| 步骤 | 命令 | 状态 |
|---|---|---|
| D1 | `scripts/decode_chronicle.py` | 【推断】依赖 A3/A4 产物与 `work/apk/assets/chronicle.dat`，链路完整；本轮未隔离复跑 |

### 阶段 E：bdl 完整解包

| 步骤 | 命令 | 状态 |
|---|---|---|
| E1 | `scripts/full_unpack_run.py --inventory <清单> [--output …] [--workers N]` → merge → verify → finalize | 【阻塞·仓库缺源码】4 个 `full_unpack_*.py` 与 `build_char_roster.py`、`docs/` 尚未 git 跟踪，第三方克隆缺失。脚本本身已参数化（--inventory/--output/--shards/--native-image/--apk/--cert-hex） |
| E2 | inventory 格式 | JSONL 每行至少 `path`（files/Bundle/… 相对路径）、`bytes`、`work_file`（本地工作副本路径）；本项目清单另有 archive 来源字段。第三方按格式自备即可 |

### 阶段 F：主表导出与字段解释（研究线，非第三方目标）

- `export_master.py`：依赖 phase-D 多个研究证据文件（output/sample、output/il2cpp、output/phase_d、output/validation 等），第三方不可独立重跑——STATUS 已声明“完整重跑依赖现有工作区，不能宣称独立运行包”。
- 各 `chica_*`、`boss_*`、`ordinary_*_probe.py`：依赖 il2cpp 恢复镜像、metadata 解码及既有证据目录，属字段解释任务线。

## 5. 本轮发现并修复的阻塞（全部隔离实测）

| # | 问题 | HEAD 实际失败表现 | 修复 | 验证 |
|---|---|---|---|---|
| F1 | `apk_baseline.py` 不提取 `libcompatible.so` 等原生库 | `elf_relocations.py` → FileNotFoundError: work/apk/lib/arm64-v8a/libcompatible.so | 提取全部 `lib/arm64-v8a/*.so`（44 文件） | 隔离通过＋项目侧重建 baseline.json，`verify_phase_a.py` PASS（44 文件哈希核验） |
| F2 | `decode_cache_snapshot.py` 硬编码读 `output/decoded/report.json` | 干净环境 FileNotFoundError: output/decoded/report.json | 新增 `--prior-report`，缺省容忍不存在并在报告中注明 | 隔离两种模式（复用／无旧报告全原生解码）均 PASS，字节一致 |
| F3 | `signal_region_probe.py` 等 3 脚本写入前不创建 `work/protection`、`output/protection` | 干净环境 FileNotFoundError: work/protection/callback_region_seed1.bin（signal_region_probe 实测；另两脚本同模式） | 三脚本（signal_region_probe、jni_prefix_probe、metadata_decode_probe）入口补 mkdir | 三脚本均隔离实测通过：镜像 SHA256＝3fd354b5…＝钉住值＝项目既有文件；compatible_jni_prefix/conversion.bin、metadata_aei_decoded.bin 与项目既有文件逐字节一致 |

以上修复均为最小改动，未触碰解码算法、哈希边界或既有正式成果。

## 6. 尚未解决的依赖／兼容性（下一阶段）

1. **仓库缺完整解包管线源码**（最高优先）：`scripts/full_unpack_{probe,run,merge,verify,finalize}.py`、`scripts/build_char_roster.py`、`docs/` 全部未跟踪。需用户授权的 git 提交任务解决。
2. `full_unpack_run.py --cert-hex` 兼容性：原 `NativeDecoder` 无 `cert_hex` 参数。本轮会话期间，并行任务已为 `decode_data5.NativeDecoder` 补上 `cert_hex`／`protection` 可选参数（2026-10-16 20:36 落盘，向后兼容，与本轮修改无冲突），并新建 `scripts/release/` 打包脚本（属该任务写入范围，本任务不接管）。**--cert-hex 路径已实测通过（整改记录 P2-4）**。
3. B3/B4/F 研究线依赖（§4）：以文档标注适用范围即可，不为第三方强行打通。
4. `verify_cache_refresh.py` 全硬编码（本项目专用），维持现状并文档注明。
5. 第三方 inventory 生成：在 README 给出 JSONL 格式与示例（path/bytes/work_file），或下一阶段补一个从单一工作副本生成清单的小工具。
6. 仅 Windows＋Python 3.12.14 实测；Linux/macOS、其他 Python 版本【未验证】（unicorn/capstone/UnityPy 均跨平台，预期可移植，需实测后声明）。
7. `.venv` 创建与依赖安装本身未在全新机器验证（本轮用既有 .venv 模拟“依赖已装好”）。

## 7. 文件分布盘点（2026-10-16 只读统计）

### output/ 23.54 GB，约 97.7 万文件

| 类别 | 目录（大小，文件数） | 建议存放 |
|---|---|---|
| 最终结构化成果 | cache_full_20261015_v3（0.12GB/111）、base_master（0.11GB/8）、export（1.40GB/234，含来源副本） | B 包（Release）；v3 为当前核心 |
| 研究／字段解释成果 | field_guide（0.75GB/133）、card_comparison_cid30236（0.07GB/209）、boss_chain+boss_heal（0.01GB/104）、ordinary_effects、phase_d、sample | B 包（Release） |
| 展示成果 | char_roster（0.15GB/2665）、card_images、对照页 HTML | B 包可选；HTML 可直接阅读 |
| 可重建媒体产物 | full_unpack（20.24GB/903,402） | C 包按类型拆分或本地保留＋清单注明重建命令；不入 git |
| 可重建中间数据 | unity、decoded、protection、native、il2cpp、apk、structured、validation（合计约 0.15GB） | 本地；发布清单注明生成命令 |
| 采集对账证据 | phone_full_20261015、phone_refresh_20261015、cache_refresh_20261015（约 0.19GB） | 本地；B 包可选摘录 |
| 历史版本／重复 | cache_full_20261015（0.07GB）、cache_full_20261015_v2（0.11GB）、single、share_bundle 既有 ZIP（0.17GB） | 本地保留；新发行按 AGENTS §8 重新组织，不回改旧包 |
| 独立审查报告 | 审查报告（52KB） | B 包 |

### work/ 4.30 GB

phone_20261015_full_02 工作副本 3.63GB（可由 raw tar 重建）、恢复镜像与 protection 0.11GB（可由 APK 重建）、phase_e 测试 0.40GB（临时）、full_unpack 分片 0.07GB。全部本地，不入库不入包。

### raw/ 3.80 GB

原始采集件（两个 external_cache.tar 及早期采集），只读保留本地；含游戏原始资源，原则上不公开分发（版权／隐私），重跑输入由用户自备。

### 仓库现状

.git 仅 1MB／71 对象；跟踪 109 文件（脚本＋文档＋参考 ZIP）。距 1GB 目标余量充足；v3 records.jsonl 54.6MB、decoded 单文件最大 18MB，适合 Release／结果包而非 git 入库。

## 8. 本轮实测记录

隔离目录：`work/repro_20261016/isolated/`（`git archive HEAD` 摘要＋修复脚本逐次覆盖为工作目录版＋APK＋2 样本 data5；解释器用项目 .venv 模拟依赖已安装。HEAD 原始失败证据先行记录，随后覆盖修复脚本重跑）。

| 命令 | 结果 |
|---|---|
| HEAD 原始 `apk_baseline.py` → `elf_relocations.py` | **按预期失败**（F1 证据）：libcompatible.so 缺失 |
| HEAD 原始 `decode_cache_snapshot.py --work work/mini_cache` | **按预期失败**（F2 证据）：output/decoded/report.json 缺失 |
| HEAD 原始 `signal_region_probe.py --loader-probe` | **按预期失败**（F3 证据）：work/protection 目录缺失 |
| 修复后 `apk_baseline.py チェンクロ.apk` | PASS，44 文件提取 |
| 修复后 `elf_relocations.py …libcompatible.so` | PASS，2855 重定位 |
| 修复后 `signal_region_probe.py --loader-probe` | PASS；镜像 SHA256＝3fd354b5…＝钉住值＝项目既有文件（字节级一致） |
| `decode_data5.py --input work/phone_candidates` | PASS；charainfo 40b4fa98…、skilllist 6515177e… 与项目 `output/decoded/` 参考字节一致 |
| 修复后 `decode_cache_snapshot.py`（有旧报告复用） | PASS，10824 记录；两文件与直接解码字节一致 |
| 修复后 `decode_cache_snapshot.py --prior-report <不存在>` | PASS，`EXISTING_NATIVE_DECODER` 全原生解码，报告注明旧报告缺失，字节一致 |
| 项目侧 `decode_cache_snapshot.py --work work/phone_20261015_full_02 --reuse-dir v3` | PASS，77/77，39047 记录与 v3 规范化后 **0 差异**（口径见下注） |
| 项目侧 `verify_phase_a.py`（baseline 重建后） | PASS，44 提取文件哈希核验、TextAsset 字节核对、重跑确定性 |
| 修复后 `jni_prefix_probe.py`（隔离） | PASS；compatible_jni_prefix.bin、compatible_jni_conversion.bin 与项目既有文件逐字节一致 |
| 修复后 `metadata_decode_probe.py`（隔离） | PASS；metadata_aei_decoded.bin（9,827,272B）与项目既有文件逐字节一致 |
| P2-3 三脚本冒烟（隔离，protection_emulate→protection_sample→callback_sample→callback_key_candidates） | PASS：PASS_PROTECTION_SAMPLE／PASS_OFFLINE_BLOCK_MODEL／distinct_keys=1, occurrences=43 |
| `full_unpack_run.py --cert-hex`（隔离，2 bdl 迷你清单，APK 临时隐藏） | PASS：2/2 status=ok；decoded_sha256 与项目 ledger 一致；objects_index.json 与项目 full_unpack 同名包逐字节一致 |

> **77 重放口径**：77 条全部走 `REUSE_THIS_SNAPSHOT_VERIFIED_DECODE`（密文＋JSON 哈希复核后的复用分支），比较对象是 records.jsonl，归一化仅 `snapshot_id`；**不是 77 次原生解码**。原生解码抽样：charainfo／skilllist（隔离，旧密文）、bossinfo（gzip 偏移 6）＋helper（偏移 0 变体，走 decode_variant，work/review_20261016/rectify_native/），均与对应参考逐字节一致；两种包装变体均有原生解码覆盖。审查方另独立复验 v3 charainfo／skilllist 原生解码一致。

未验证事项：A3′ il2cpp 镜像、A4 native_debug、D1 chronicle、C1—C3 采集链（无手机）、E1 bdl 全量（仓库缺源码，未在隔离环境跑）、全新机器 .venv 安装、非 Windows 平台。

并行变更记录：本轮会话期间（20:36—20:38），另一并行任务修改 `scripts/decode_data5.py`（NativeDecoder 增加 `cert_hex`／`protection` 可选参数，向后兼容）并新建 `scripts/release/build_full_unpack_bundle.py`、`check_full_unpack_bundle.py`（full_unpack 分享包构建与检查，按其 docstring 属用户已指派的打包任务，音频按用户要求排除）。全部在本审计测试完成后落盘，不影响上表任何测试结论；该范围由并行任务负责，本任务未接管、未改动。

## 9. 下一阶段最小任务清单（按优先级）

1. **git 提交补缺**（需用户授权）：提交 `scripts/full_unpack_*.py`、`scripts/build_char_roster.py`、`docs/` 及本轮 5 个脚本修复与 AGENTS.md；不推送。
2. **根目录 README.md**：项目简介、已实现／未实现、输入要求（APK 版本硬边界）、安装、data5 解包命令、bdl 解包命令与 inventory 格式、验证命令、研究线脚本适用范围声明。
3. **小修复与补测**：`--cert-hex` 路径已实测通过（见整改记录 P2-4）；视 README 需要补 inventory 生成小工具。
4. **隔离复跑补测**：A4＋D1（chronicle 主表）与 2 个 bdl 样本的 full_unpack 小清单端到端。
5. **发布准备**：按 AGENTS §8.2 起草 A/B/C 包清单（机器可读 manifest 草案），评估 Release 附件划分；不实际上传。
6. 可选：全新机器／干净 venv 安装验证；非 Windows 平台验证。

---

## 审查整改记录（对照 output/20261016-reproducibility-audit/review/review_20261016_independent/README.md）

整改依据：审查结论「带明确限制通过」，无 P0。以下记录每项实际改动与证据；复验均写独立目录（work/review_20261016/、work/repro_20261016/isolated/），未覆盖正式输出。

### 已完成（2026-10-16 暂停前）

**P2-1（C-3）--prior-report 复用分支硬编码——已修复并三模式复验 PASS**
- 改动：`scripts/decode_cache_snapshot.py` 复用分支（原第 87 行）`Path('output/decoded',source.name+'.json.raw')` → `previous.get('json_file') or args.prior_report.parent/(source.name+'.json.raw')`。默认 `--prior-report output/decoded/report.json` 时解析路径与原来逐字节相同，项目内行为不变。
- 复验：
  1. 项目侧 77 文件 `--reuse-dir output/cache_full_20261015_v3` 重放（写 `work/review_20261016/rectify_replay_v3`）：PASS，77/77，39047 记录；与 v3 records.jsonl 逐行比对，仅归一化 snapshot_id 后 **0 差异**；77 条全部 `REUSE_THIS_SNAPSHOT_VERIFIED_DECODE`。
  2. 隔离目录 `--prior-report output/nonexistent/report.json`（不存在）：PASS，全部 `EXISTING_NATIVE_DECODER`，charainfo `40b4fa98…`／skilllist `6515177e…` 不变。
  3. 隔离目录自定义旧报告目录 `output/my_prior/`（复制 report.json＋.json.raw，**临时改名隐藏 `output/decoded`**）：PASS，`REUSE_EXACT_CIPHERTEXT_AND_VERIFIED_JSON`，两文件 sha 不变；证明复用分支确实从 --prior-report 所在目录解析而非硬编码路径。已恢复目录名。

**P2-2（C-4）「77 文件 0 差异」口径＋原生解码抽样**
- 77 重放全部为密文校验复用分支，比较对象是 records.jsonl（归一化仅 snapshot_id），不是 77 次原生解码——本文档 §8 措辞已相应修正（见 §8 实测表注）。
- 原生解码加强证据：`work/review_20261016/rectify_native/` 对 **bossinfo.data5（gzip 偏移 6）与 helper.data5（偏移 0 变体，走 decode_variant）** 无复用原生解码，结果与 v3 `decoded/` 逐字节一致（bossinfo `00df710f…`、helper `d8d23ced…`）。加上既有 charainfo／skilllist（隔离旧密文）与审查方 v3 两文件复验，两种包装变体均有原生解码覆盖。

**P1-2（C-2）F3 隔离证据补齐——两个脚本均已隔离实测**
- 工作目录修复版 `jni_prefix_probe.py`、`metadata_decode_probe.py` 复制进 `work/repro_20261016/isolated/scripts/` 各运行一次：
  - `jni_prefix_probe.py`：生成 `work/protection/compatible_jni_prefix.bin`、`compatible_jni_conversion.bin`，与项目既有文件 **SHA256 逐字节一致**。
  - `metadata_decode_probe.py`：生成 `work/protection/metadata_aei_decoded.bin`（9,827,272 字节），与项目既有文件 **SHA256 逐字节一致**。
- 三脚本（signal_region_probe／jni_prefix_probe／metadata_decode_probe）至此全部有隔离实测。§8 隔离环境描述已修正为「git archive HEAD 摘要＋修复脚本覆盖为工作目录版」。

**P2-3（C-5）同类缺 mkdir——已修复并冒烟 PASS**
- 改动（各入口补 `Path("output/protection").mkdir(parents=True, exist_ok=True)` 或等效）：
  - `scripts/protection_sample.py`（output 写入前补 output.parent.mkdir）
  - `scripts/callback_sample.py`（同上）
  - `scripts/callback_key_candidates.py`（同上）
- 冒烟（全部在隔离目录，避免覆盖项目 output/protection 既有 JSON；先跑 `protection_emulate.py` 生成 stage3 快照满足 callback_key_candidates 输入）：
  - `protection_sample.py` → `PASS_PROTECTION_SAMPLE`
  - `callback_sample.py` → `PASS_OFFLINE_BLOCK_MODEL`
  - `callback_key_candidates.py` → `distinct_keys=1, occurrences=43`（与原始记录一致）

**P2-4（C-6）--cert-hex 端到端——完成**
- 证书提取：`apk_certificate.certificates(チェンクロ.apk)` → 单一签名者，DER hex 存 `work/review_20261016/cert_hex.txt`（879 字节，公开签名证书）。
- 端到端：隔离目录（复制 `full_unpack_run.py` 与工作目录版 `decode_data5.py`），迷你清单 2 个 bdl（el_home_idle01.bdl 1207B、el_talvy_neutral01.bdl 1210B，work_file 绝对路径只读引用项目工作副本），**运行期间将隔离目录内 APK 临时改名隐藏**，命令：
  `full_unpack_run.py --inventory work/mini_inventory.jsonl --output output/full_unpack_mini --shards work/full_unpack_mini_shards --workers 1 --native-image work/protection/nutils_loader_seed1.bin --cert-hex <hex>`
  结果：2/2 `status=ok`（首次失败因隔离目录 decode_data5.py 为 HEAD 无 cert_hex 版，复制工作目录版后成功；APK 已恢复原名）。
- 收尾比对（PASS）：两包 `objects_index.json` 与项目 `output/full_unpack/` 同名包**逐字节一致**；shard 记录 `decoded_sha256` 与项目 ledger 逐项一致（f77e5824…／00c487f6…）。cert_hex 路径端到端可用，且证明该分支不读 APK 文件。

**P1-1（C-1）待提交清单——已列出，等待用户授权后提交（不推送）**

待提交项（显式逐个 `git add`，禁止 `git add .`／`git add -f output|work|raw`）：
1. `scripts/full_unpack_probe.py`、`scripts/full_unpack_run.py`、`scripts/full_unpack_merge.py`、`scripts/full_unpack_verify.py`、`scripts/full_unpack_finalize.py`
2. `scripts/build_char_roster.py`
3. `scripts/release/build_full_unpack_bundle.py`、`scripts/release/check_full_unpack_bundle.py`（并行打包任务成果；提交前与并行任务确认其状态）
4. `docs/`（整个目录：3 个既有任务卡＋`角色技能完整解读实施方案.md`＋本审计文档）
5. `AGENTS.md`
6. 修复脚本：`scripts/apk_baseline.py`、`scripts/decode_cache_snapshot.py`、`scripts/jni_prefix_probe.py`、`scripts/metadata_decode_probe.py`、`scripts/signal_region_probe.py`、`scripts/decode_data5.py`（cert_hex/protection，并行任务改动）、`scripts/protection_sample.py`、`scripts/callback_sample.py`、`scripts/callback_key_candidates.py`

不提交：`HANDOFF.md`／`STATUS.md` 随提交时整合者的最新版本一并处理；`output/`、`work/`、`raw/`、`.venv/`、`tools/` 维持忽略。

### 待办

1. P1-1：等用户授权后按上表提交（不推送）。
2. 最终交付报告：逐文件逐行改动、命令、PASS/数值、未验证项；审计可否结束与 S1/S2 启动建议（提醒根交接在整合者交回前不要抢改）。

### 环境备注

- 复验命令主要在 Windows PowerShell 5.1 下执行，遇到并已绕过：`-AsByteStream` 缺失、GBK 控制台乱码、`Out-File -Encoding ascii` 破坏中文路径、`WriteAllLines` 数组合并单行、robocopy 本地化输出；收尾阶段已切换 pwsh 7.6.6。项目 .venv 的 Python 环境不受 shell 版本影响。
- 隔离目录 `work/repro_20261016/isolated/scripts/` 当前为「git archive HEAD 摘要＋工作目录修复版覆盖」：apk_baseline、decode_cache_snapshot、signal_region_probe、jni_prefix_probe、metadata_decode_probe、decode_data5（并行任务 cert_hex 版）、full_unpack_run 及 P2-3 三脚本。

---

## 第三阶段交付记录（2026-10-16 晚）

- **Git**：`8b91293`（26 文件补缺＋README）、`ff664a7`（full_unpack merge/finalize 容忍第三方最小清单）、`e2cc987`（scripts/release/build_delivery_bundle.py）；本地提交，未推送。
- **交付版本验证**：`work/delivery_20261016/final/`（`git archive ff664a7`＋APK＋4 样本）全链通过：A1—A3（镜像＝钉住值）、B1、B2（两包装格式 4 文件 16719 记录全原生解码）、bdl 2 样本四步管线、chronicle（A4＋D1，6 产物文件），全部与既有成果逐字节一致。此前各轮已通过的测试未重跑。
- **分层交付**：`output/share_bundle/20261016-delivery/`（A 1.4MB/129 项、B 149.7MB/3366 项、C 仅清单、统一 README＋package_manifest.json，CRC/对账全过）；排除项与版权边界见清单。
- **待授权**：git push；GitHub Release 上传。其余限制见 STATUS 末节。

## 最终确认记录（2026-10-17）

- **仓库复核**：124 跟踪文件；管线与修复全部入库；第三方导入均被 requirements-lock.txt 覆盖；无资源／凭据／大产物（模式扫描为空）；工作树干净。
- **版本绑定**：`git diff ff664a7 <最终HEAD> -- scripts/ requirements-lock.txt README.md .gitignore` 为空（仅交接文档与打包脚本差量），交付测试完整适用于最终 HEAD。
- **错误输入补测**（`work/delivery_20261016/final/`）：破坏 data5→FAILED_RETAINED（envelope 校验拒绝，其余文件正常，PARTIAL_FAILURES_RETAINED）；空目录→ValueError("No data5 input")；libcompatible.so 位翻转→版本断言拒绝（原件已恢复 79b6ae19…）；缺镜像→FileNotFoundError 含缺失路径。
- **A/B/C 复核**：条目数、体积、SHA-256 与 package_manifest.json 对账一致；CRC 自检过；B 包 base_master 全量组件与四分表为同数据两种访问形式（既有产物结构，已在清单注明，不重构）。
- **审查基准**：最终 HEAD 即冻结版本（完整哈希见本轮交付报告与 git log）；测试证据在 `work/delivery_20261016/final/`（含 neg_t1/neg_t2/neg_t4 负向测试产物），媒体与发布清单在 `output/share_bundle/20261016-delivery/`。

## 审查整改记录②（对照 review_20261017_final_delivery，2026-10-17）

依据：`output/20261016-reproducibility-audit/review/review_20261017_final_delivery/README.md`，结论「带明确限制通过，无 P0；1 项 P1＋7 项 P2」。

- **P1-1（用户裁决：细分排除）**：B 包排除 `output/char_roster/icons/**`（2,656 PNG）、`output/char_roster/index.html`、`output/card_images/**` 内 5 个 .unityfs 与 7 个 .png、`output/card_comparison_cid30236/reference.png` 与 `index.html`；保留名册 data/（9,169 cid 合并成品）、全部研究证据 JSON/TXT/bin、README。实现：`scripts/release/build_delivery_bundle.py` 增加 `B_EXCLUDE_PATHS`/`B_EXCLUDE_MEDIA_IN` 与泄漏断言；被排除项逐条登记 package_manifest.json 的 `media_excluded`（含"展示页与媒体本地可用、按 C 清单重建"说明）。base_master 按用户确认**保留两种形式**。
- **P2-1**：README §4 注明「B1 仅处理 gzip 偏移 6 包装；整目录请直接用 B2（自动识别两种包装并逐文件容错）」。
- **P2-2**：`decode_data5.py`、`apk_certificate.py` 增加 `--apk`（默认值不变）。实测：`--apk <改名副本>` 解码 charainfo PASS（40b4fa98… 不变）。
- **P2-3**：`apk_certificate.py` 增加 `--hex`（report.json 与 stdout 输出 1,758 字符 hex）；README §5 补取 hex 命令。
- **P2-4**：删除 `build_chica_comparison.py:16` 作者机器临时路径常量及刷新行，仅保留 `output/.../reference.png` 兜底断言。
- **P2-5**：`full_unpack_run.py` 改为定位路径中的 `Bundle` 分量；缺分量时该行记录 `status=error` 与明确原因。实测三种前缀：`Bundle/…` 与 `cache/files/Bundle/…` 均导出到 `objects/Motion/…`，`files/Motion/…`（无 Bundle）记录错误；README §5 注明期望前缀。另修 `full_unpack_finalize.py`：默认清单不存在时 sha 记 null 而非崩溃（README 同步改为显式 `--inventory`）。
- **P2-6**：HANDOFF「4 个提交待推送」更正为 5；交付 README/A 包清单措辞收紧为「与 HEAD 逐文件内容一致（zip 内 CRLF 行尾）」「与最终 HEAD 除新增打包脚本与交接文档外零差异」；STATUS 历史节 A 包版本更正为 a8e1f02。
- **P2-7**：media_manifest.json 与 STATUS 各加口径句（903,402/20.24GiB＝目录总量；903,396＝objects/ 文件数；56 类合计 20.18GiB 仅导出媒体）。
- **复验**：5 个修改脚本 py_compile 通过；decode_data5 --apk、apk_certificate --hex、full_unpack 三种前缀实测通过（证据见上文与 work/review_20261017/、work/delivery_20261016/final/work/prefix_test_shards/）。改后按最终 HEAD 重建 A/B/C 包并核验条目数/体积/SHA-256/CRC（见交付报告）。
- **未做**（按约束）：不重跑 A—E、不重做全量解包、不覆盖既有成果与审查报告；git push 与对外发布仍等用户授权。
