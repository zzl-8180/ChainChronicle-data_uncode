# 统一 output 整目录迁移：unpack / assets 剩余根

**准备结论：16 棵现存完整树全部须先完成读写适配，才能并入同一次物理窗口；当前 0 棵可直接执行。** 这里仅整理已知接口与候选目标。未运行解码、采集、媒体导出或全树哈希，未搬目录、改联接、更新 latest 或触碰业务脚本。

既有 `output/single`、`output/cache_full_20261015_v2` 已迁；旧 `output/cache_full_20261015` 当前不存在，不再作为载荷根。本表按 2026-11-06 的 1140 行 [path-map](../20261106/path-map.json) 中 `unpack/assets` 的顶层完整目录筛选；每个目标是**独立且当前不存在**的新容器，不合并已有项目根。其他项目分类的 output 树由统一总包其他分工处理。

| 完整现址 → 候选目标 | 既有测量（文件／字节） | 静态别名 | 当前关键门槛 |
|---|---:|---:|---|
| `output/apk` → `projects/unpack/data/apk/apk-baseline` | 未见适用既有全树计数 | 5 | APK基线/版本及原生恢复链 |
| `output/base_master` → `projects/unpack/data/apk/base_master` | 未见适用既有全树计数 | 6 | 主线APK读者和Chronicle写者 |
| `output/cache_full_20261015_v3` → `projects/unpack/data/cache/cache_full_20261015_v3` | 未见适用既有全树计数 | 11 | 主线77 raw、latest及冻结路径值 |
| `output/cache_refresh_20261015` → `projects/unpack/data/cache/cache_refresh_20261015` | 90／129,779,325 B（2026-11-08） | 5 | refresh latest、组合清单与raw/work溯源 |
| `output/card_images` → `projects/assets/data/card_images` | 未见适用既有全树计数 | 5 | 绑定证据、媒体复制与相对URL |
| `output/decoded` → `projects/unpack/history/decoded` | 23／17,027,377 B（2026-11-08） | 0 | 旧报告复用及固定读写者 |
| `output/export` → `projects/unpack/data/export` | 234／1,500,467,070 B（2026-11-08） | 5 | 内部latest与正式根守卫 |
| `output/full_unpack` → `projects/assets/data/full_unpack` | 未见适用既有全树计数 | 5 | bdl ledger、shards与媒体消费者 |
| `output/il2cpp` → `projects/unpack/research/il2cpp` | 未见适用既有全树计数 | 5 | 字段指南/样本研究证据 |
| `output/native` → `projects/unpack/research/native` | 未见适用既有全树计数 | 5 | 原生恢复hash与phase A子进程 |
| `output/phone` → `projects/unpack/reports/acquisition/phone` | 13／16,009,387 B（2026-11-08） | 5 | 采集/字段指南/阶段B固定读写 |
| `output/phone_full_20261015` → `projects/unpack/reports/acquisition/phone_full_20261015` | 5／44,162,287 B（2026-11-08） | 0 | v3 manifest提取报告绑定 |
| `output/phone_refresh_20261015` → `projects/unpack/reports/acquisition/phone_refresh_20261015` | 9／34,939,444 B（2026-11-08） | 0 | refresh manifest输入绑定 |
| `output/protection` → `projects/unpack/research/protection` | 未见适用既有全树计数 | 5 | relocation/镜像/seed完整契约 |
| `output/unity` → `projects/assets/history/unity` | 50／84,552,259 B（2026-11-08） | 5 | text_path旧值及五隔离入口 |
| `output/validation` → `projects/unpack/reports/validation` | 8／27,103 B（2026-11-08） | 0 | 阶段A子进程+多个验收写者 |

静态别名共 67 条，其中 `base_master` 另有第三方隔离入口，v3 的 11 条包括 C14—C18 下 `analysis`／`provenance` 两条子目录 junction 及第三方隔离入口。静态值只作清单种子，**物理前必须逐条重新 lstat、核 tag/ID/readlink，并查是否新增别名**。既有测量是第二／第三批各自时间点；其余八棵在现有证据中未找到可信全树数量，明确留空，不临时全盘枚举或冒充 100%。

## 当前必须先闭合的成组接口

### 缓存主表、补采与三个正式指针

- `cache_full_latest.json` 当前将 `directory/manifest` 指向旧 v3；`cache_refresh_latest.json` 将 `directory/base_directory` 分别指向旧 refresh/v3。两份顶层文件在既有映射中拟移至 `projects/unpack/data/cache/`。新目录、清单与现用读者验证后，须在同一整合窗口原子安装新值，并把所有读者和未来写者改到新指针；不能保留旧 output 静默回退。`output/export/latest.json` 随 export 树移动，但其 `directory` 值仍指旧 build，选中构建核验后同样需原子换值。
- v3 `decode_report.json` 的 77 个 `json_file` 值为旧 `output\cache_full_20261015_v3\decoded\…`；记录视图的 `original_file`、卡页和报告也可能保存旧逻辑来源。保持这些冻结字节，维护读取端以显式 moved root + 安全 basename 和原 SHA gate 解析；`decode_cache_snapshot.py --reuse-dir` 的既有 v2 候选实现可作为模式，不能把报告旧路径当迁后物理真值。
- `cache_refresh_20261015/composite_inventory.jsonl` 的 `archive/work_file` 指向 `raw/`、`work/` 原输入，`full_unpack` 记录又有 `local_path/output_path` 等不同语义；不可统一字符串替换。`verify_cache_refresh.py`、`full_unpack_run/merge/verify/finalize/probe` 和图片提取须显式接同一候选清单根。

### APK / native / protection 与验收闭包

- 根 `チェンクロ.apk`、`raw/`、`work/apk`、`work/protection` 均保持原位。`output/apk/baseline.json` 钉 APK 5.6.2／56021 和 SHA；迁移 `output/apk`、`base_master`、`native`、`protection`、`il2cpp` 时仍需显式绑定 baseline、恢复镜像、relocations、seed、symbols 的来源与 hash，不可放宽版本拒绝或让本机历史 work 文件变成未声明前提。
- `decode_chronicle.py` 写 base_master 且有 work/protection 副作用；`verify_phase_a.py` 既写 validation，又启动 unity_scan/native_debug/structured_candidates，不能只改父进程一个输出参数。候选环境、CWD、import、子进程读写根都必须版本一致；仅隔离候选执行，旧冻结结果不重建。

### 媒体与主线字段消费者

- `unity_scan.py` 在 `textassets.jsonl` 写 `output/unity/textassets/...`；`structured_candidates.py` 和 phase A 直接解引用该值。必须决定外部旧路径解析或生成新版本索引，并覆盖 field guide、CID30236 图片和五个正式隔离入口。
- `full_unpack` 的 ledger/coverage/objects 与 `card_images` 的绑定证据被名册、卡页渲染、阅读器和发行复制使用；需保持部分／缺失标记、来源映射及相对 URL。`card_page_data.py` 直接读 v3/raw 和 base_master，`card_page_dependencies.py` 把其纳入签名；新路径适配后做代表卡的源 SHA/答案回归，P/v7、rules/pages 与历史报告不为整理重写。

## 每棵目录的具体修补清单

### `output/apk`

目标：`projects/unpack/data/apk/apk-baseline`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：assets, skill-research, unpack。

**已知接口**：

- scripts/apk_baseline.py:20 --output defaults output/apk; scripts/apk_certificate.py:78 writes certificates
- scripts/native_debug.py:35; scripts/verify_phase_a.py:19; scripts/cache_probe.py:56; scripts/structured_candidates.py:16 read baseline.json
- baseline.json pins root APK SHA/version 5.6.2/56021 and work/apk extracted paths; NativeDecoder consumes compatible APK and recovery materials

**物理前补丁**：

- Make baseline/certificate output root explicit and pass same baseline to native_debug, verify_phase_a and structured_candidates; preserve APK SHA/version hard refusal
- Keep baseline.json original APK/work source values as provenance; add external old-logical-path resolver where physical output/apk paths are consumed, never silently rewrite signed/version evidence

**定向验收**：

- Compare pinned APK SHA/version and representative extracted entry hashes; reject incompatible APK/missing baseline
- Prove independent candidate native/structured/phase-A input closure without writing old output roots

### `output/base_master`

目标：`projects/unpack/data/apk/base_master`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：distribution, reader, reference-analysis, skill-research。

**已知接口**：

- scripts/decode_chronicle.py:29,63 reads native symbols and writes output/base_master; work/protection side output also exists
- scripts/export_master.py:242,273; scripts/character_skills/card_page_data.py:494; scripts/character_skills/effect_ledger.py:2920; scripts/build_char_roster.py:38 read fixed master files
- C03 connects skill-research, reader, reference-analysis, distribution; frozen card/report original_file paths name old base_master

**物理前补丁**：

- Parameterize decode_chronicle input symbols and base_master output with NativeDecoder/Experiment inputs as one closure; never run against live old root
- Rebind export, card_page_data/Dependencies, ledger, roster and selected readers to explicit APK source root before window; preserve APK/CACHE namespace and frozen provenance strings

**定向验收**：

- Hash key _mdSkill/_mdCharacter/_mdBossInfo and report against prior identity; source version stays APK 5.6.2
- Selected card answers/ledger source SHA and no mixed old/new source roots

### `output/cache_full_20261015_v3`

目标：`projects/unpack/data/cache/cache_full_20261015_v3`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：distribution, reader, reference-analysis, skill-research。

**已知接口**：

- output/cache_full_latest.json currently has directory/manifest at old v3; scripts/character_skills/card_page_data.py:493 and card_page_dependencies.py:26 read v3 raw JSON
- scripts/full_unpack_merge.py:17 uses V3_DECODED; scripts/build_char_roster.py:39 reads v3; many reader/Chica consumers use records.jsonl
- decode_report.json contains 77 json_file values under old output\cache_full_20261015_v3\decoded; records/original_file and frozen source keys preserve old logical paths
- scripts/decode_cache_snapshot.py --output explicit/--reuse-dir; scripts/analyze_cache_snapshot.py --input writes analysis; scripts/verify_cache_snapshot.py reads phone_full extraction and v3 report
- C07 uses decode_report fingerprint in card pages; current rules/pages and P/v7 remain protected

**物理前补丁**：

- Introduce explicit snapshot root/pointer resolver for all current card/reader/roster/full_unpack consumers, including source fingerprinting; do not change frozen card, report, records or JSON raw bytes
- For reuse, bind --reuse-dir to moved root and use verified decoded/<safe filename>.json.raw plus existing source/plaintext hashes; never trust frozen json_file as a postmove physical path or fall back to old output
- Move cache_full_latest.json with root and atomically write new directory/manifest values only after content and current-consumer checks; update writer defaults and navigation together

**定向验收**：

- Current pointer resolves moved v3 manifest and 77 decoded raw files with original SHA checks; mismatch rejects, no old-root fallback
- Representative card page/ledger/source signature equal under relocated source; historical C07/frozen provenance unchanged

### `output/cache_refresh_20261015`

目标：`projects/unpack/data/cache/cache_refresh_20261015`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：assets, unpack。

**已知接口**：

- output/cache_refresh_latest.json points old refresh root and base v3 root; manifest.json inputs pin phone_refresh files and v3 manifest SHA
- scripts/verify_cache_refresh.py:5 fixed phone_refresh, refresh and v3 roots; scripts/full_unpack_run.py:26, merge.py:14, verify.py:25, finalize.py:26, probe.py:16 consume composite_inventory.jsonl
- scripts/extract_cid30236_images.py:23 reads composite_inventory; inventory rows carry archive/work_file provenance into raw/work input snapshots

**物理前补丁**：

- Parameterize all full_unpack and image-input readers plus verify_cache_refresh as one declared inventory root; preserve raw/work archive path semantics and hashes
- Move cache_refresh_latest.json together with refresh and v3; atomically set new directory/base_directory only after both roots verify; retain manifest input bytes and old logical references via resolver

**定向验收**：

- Compare composite inventory row count, per-status and selected source hashes; distinguish archive/work_file/local provenance from movable output paths
- Full_unpack representative bdl input resolves through declared raw/work roots, not old output alias

### `output/card_images`

目标：`projects/assets/data/card_images`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：assets, distribution, reader, skill-research。

**已知接口**：

- scripts/extract_cid30236_images.py:149 has --output default output/card_images/cid30236 and reads unity/v3/refresh
- scripts/character_skills/card_page_dbstyle_sample.py:50,56,81 uses binding/manifest/followup; card_page_render_v2.py and release/materialize_character_art_sources.py consume/copy images
- C16 crosses reader/distribution and relative URL/asset copy boundaries; old screenshots/partial markers cannot become full art

**物理前补丁**：

- Set explicit media root in extraction, card renderer, dbstyle, release materialization and selected reader; update generated links through generator, not hand-edit HTML
- Keep binding evidence and complete/partial labels; do not turn screenshot or AI image into extracted source

**定向验收**：

- Representative CID binding evidence/image hash and all chosen relative URLs; no additional missing art versus baseline

### `output/decoded`

目标：`projects/unpack/history/decoded`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：映射未列；以下脚本读口仍须处理。

**已知接口**：

- scripts/decode_data5.py:145 --output defaults output/decoded; scripts/decode_cache_snapshot.py:52 --prior-report defaults report.json
- scripts/export_master.py:241,266; verify_data5.py:53,83; sample_trace.py:166; master_source_compare.py:18; Chica and phase-D probes read old path
- README.md:55-56 documents B1 output/decoded; frozen card original_file may name skilllist.data5.json.raw

**物理前补丁**：

- Make selected decoder/prior/export/verify/research reader roots explicit and update README command; preserve old report and card provenance as logical path
- Run candidate-only old-vs-new source SHA/negative path tests; do not broaden to rebuilding current v3

**定向验收**：

- 23-file prior screen exact set, report/raw and output bytes; missing new source never falls back to old output

### `output/export`

目标：`projects/unpack/data/export`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：映射未列；以下脚本读口仍须处理。

**已知接口**：

- scripts/export_master.py:238 --output-root defaults output/export; scripts/analyze_cache_snapshot.py:51 and build_field_guide.py:154 read latest.json directory
- scripts/verify_export.py:27 reads latest pointer; scripts/verify_export_pointer.py:37 treats output/export as official guard; Chica comparison reads fixed old build manifest
- latest.json directory points output/export/snapshot_.../build_... and manifest/sources may record old logical origins

**物理前补丁**：

- Set explicit export root for writer and all latest consumers; update official guard so relocated root is protected, not old output
- After moving full tree, validate selected build/manifest then atomically update internal latest directory to new build path; preserve existing build bytes and source provenance

**定向验收**：

- 234-file/1,500,467,070-B prior bounded set; selected build manifest and copied source hashes; pointer mismatch/corrupt build hard reject
- No mutation of frozen historical export builds or forced rebuild

### `output/full_unpack`

目标：`projects/assets/data/full_unpack`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：assets, distribution, reader, skill-research。

**已知接口**：

- scripts/full_unpack_run.py:26-28 fixed inventory/output/shards; merge.py:14-17; verify.py:25; finalize.py:10,26; probe.py:16
- scripts/build_char_roster.py:41 consumes objects/Card_Icon; card_page_dbstyle_sample.py:51,120 uses ledger and object paths; reader/art release copies them
- ledger local_path/archive/work_file/output_path and manifest record types have distinct path meanings (B07 command-IO matrix)

**物理前补丁**：

- Parameterize run/merge/verify/finalize/probe roots and shard location as one closure; preserve per-record root_id/path_kind and distinction between raw/work source and moved object path
- Rebind roster, card rendering, release materialization and reader URLs; do not recopy objects into new root or rewrite frozen ledger

**定向验收**：

- Ledger/coverage/manifest and representative object hashes, source mapping, missing/partial status unchanged; test resume failure path in isolated candidate only
- Existing declared missing artwork remains missing; no new missing due to move

### `output/il2cpp`

目标：`projects/unpack/research/il2cpp`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：映射未列；以下脚本读口仍须处理。

**已知接口**：

- scripts/active_skill_trace.py:30 reads active_code; scripts/build_field_guide.py:113,131 and export_master.py:244,257 read sample_code evidence
- C01 native/metadata consumers link to work/protection and recovered image; five isolation aliases

**物理前补丁**：

- Add explicit IL2CPP research root to active trace/field guide/export inputs and generated evidence links
- Do not conflate research excerpt with original APK/native image; keep source hash/provenance

**定向验收**：

- Sample code evidence hash and field-guide source locations; no replacement of native version checks

### `output/native`

目标：`projects/unpack/research/native`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：assets, skill-research, unpack。

**已知接口**：

- scripts/native_debug.py:30 --output defaults output/native and :35 reads output/apk/baseline.json
- scripts/decode_chronicle.py:29 requires recovered_symbols.json; verify_phase_a.py:39-40 reads/re-runs native_debug
- NativeDecoder in decode_data5.py:60 and protection_emulate.py:53 rely on compatible APK/image/relocations across output and work

**物理前补丁**：

- Parameterize native_debug output and baseline, decode_chronicle symbols and phase-A subcommand closure; keep pinned APK/recovered-image hash refusal
- Declare which outputs are reproducible from APK and which work/protection files remain inputs; no silent fallback to historical local work

**定向验收**：

- Representative symbols/recovery reports and pinned image/APK SHA; incompatible version rejects before writing
- Phase A candidate subprocess writes only candidate roots

### `output/phone`

目标：`projects/unpack/reports/acquisition/phone`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：映射未列；以下脚本读口仍须处理。

**已知接口**：

- scripts/phone_collect.py:24 --output defaults output/phone; scripts/cache_probe.py:11 and bounded_decode.py:41-42 write/read phone reports
- scripts/build_field_guide.py:156-161 and export_master.py:243, sample_trace.py:195, verify_phase_b.py:21,26 fixed read collected/inventory/trials

**物理前补丁**：

- Parameterize collection/probe/trial output and field-guide/export/sample/phase-B reader roots together; leave raw phone acquisition originals unchanged
- Future acquisition uses a new snapshot directory and no overwrite of historic phone reports

**定向验收**：

- 13-file/16,009,387-B prior bounded set; collected list and inventory source hashes; no phone connection for migration validation

### `output/phone_full_20261015`

目标：`projects/unpack/reports/acquisition/phone_full_20261015`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：映射未列；以下脚本读口仍须处理。

**已知接口**：

- scripts/analyze_cache_snapshot.py:158-159 and verify_cache_snapshot.py:25 fixed extraction/inventory read
- v3 manifest input_versions and cache refresh linkage bind phone_full extraction report hash

**物理前补丁**：

- Parameterize snapshot analyzer/verifier extraction root; preserve v3 manifest recorded old logical path and hash via resolver, no rewrite of frozen snapshot

**定向验收**：

- 5-file/44,162,287-B prior bounded set; extraction report SHA and v3 manifest input binding match

### `output/phone_refresh_20261015`

目标：`projects/unpack/reports/acquisition/phone_refresh_20261015`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：映射未列；以下脚本读口仍须处理。

**已知接口**：

- scripts/collect_cache_refresh.py:5 plan_dir fixed output/phone_refresh_20261015; scripts/verify_cache_refresh.py:5 fixed P/D/OLD roots
- cache_refresh manifest inputs pin probe/stat/inventory/extraction hashes under old phone_refresh paths

**物理前补丁**：

- Parameterize refresh collection/verification plan and output root; preserve raw/phone_20261015_refresh_02 and work source path separation
- Resolve manifest input keys as historical logical identifiers to moved physical files; do not edit frozen manifest to simulate a new capture

**定向验收**：

- 9-file/34,939,444-B prior bounded set; four pinned report hashes and extraction provenance match

### `output/protection`

目标：`projects/unpack/research/protection`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：assets, skill-research, unpack。

**已知接口**：

- scripts/elf_relocations.py:14 and elf_global_refs.py:17 --output default under output/protection
- scripts/protection_emulate.py:53 reads relocations and :317 writes emulation; callback_sample.py:96,118; protection_report.py:10,12,30,45; jni_prefix_probe.py and signal_region_probe.py have fixed output/protection writes
- NativeDecoder/Experiment construct path defaults and work/protection recovered image/seed remain separate and pinned

**物理前补丁**：

- Parameterize selected relocations/global refs/emulation/report/probe inputs and outputs as an explicit native version bundle; do not run old exploratory probes against live root
- Keep recovered image/seed/relocation hashes and APK version gates; do not copy work/protection into research output or erase recovery contract

**定向验收**：

- Relocation and image hashes, code address samples and version rejection; no historical work fallback

### `output/unity`

目标：`projects/assets/history/unity`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：assets, distribution, reader, skill-research。

**已知接口**：

- scripts/unity_scan.py:16 --output defaults output/unity and textassets.jsonl writes text_path=output/unity/textassets/...
- scripts/mono_headers.py:14 --output defaults output/unity; structured_candidates.py:15 and verify_phase_a.py:25,38 dereference text_path
- scripts/build_field_guide.py:164-165,477-522,635-637; audit_unity_headers.py:11; extract_cid30236_images.py:173,178 fixed read indexes

**物理前补丁**：

- Choose external old-text_path resolver or new versioned index; do not hand-edit frozen textassets.jsonl; parameterize all selected readers and writer defaults
- Close verify_phase_a subprocess closure and field-guide/image consumers plus five formal aliases in same window

**定向验收**：

- 50-file/84,552,259-B prior bounded set; textasset bytes and selected ResourceManager/object rows compare
- No old text_path physical fallback; bad-input rejection remains

### `output/validation`

目标：`projects/unpack/reports/validation`；分类：**先适配后并入同一次窗口**。既有映射目标相同。跨项目读者：映射未列；以下脚本读口仍须处理。

**已知接口**：

- scripts/verify_phase_a.py:17-66 writes checks.json, truncated.unity3d and invalid_unity; subprocesses can write unity/native/structured
- scripts/verify_data5.py:99; verify_metadata.py:40; verify_phase_b.py:32; verify_phase_c.py:58; high_hp_sample_probe.py:116 fixed writes
- scripts/sample_trace.py:11 and export_master.py:246,263 read high_hp_sample.json; build_field_guide.py:114 publishes path

**物理前补丁**：

- Declare validation root across selected writers/readers; phase-A child output roots must be isolated as one closure
- Update field-guide generated evidence path through generator, not hand-edit report; preserve frozen checks and 32-sample evidence

**定向验收**：

- 8-file/27,103-B prior bounded set; selected report hash/status and negative bad-input path; no child writes to old roots

## 执行、回退和保留边界

统一窗口的前置是：最终选定的每棵源树建立精确文件／目录身份清单与适度内容 hash、估算容量；源／目标／祖先同 E 卷无冲突和内部 reparse；所有实际别名与新的 next/previous 名称逐项核实；所选 producer、reader、失败写入和子进程补丁均在独立候选通过。静态 2026-11-06 引用数字不代表当前调用次数或临前身份。未修好任何一棵时不能把它默默标成 ready。

物理执行须有精确清单、单一 owner 窗口与用户对具体根／指针／别名的授权；每步持久 INTENT、紧邻 gate、同卷整目录 rename、验身份与代表内容，别名以 next→previous→formal 阶段切换并保留 previous。两次改名不原子。窗口中断先按实际物理状态、WAL 和回执判定；原授权／窗口失效后另定恢复契约，不能盲重跑或直接逆搬。所有 current latest 在根及消费者验证后原子切换，旧报告的逻辑来源值继续保留，外部 resolver 负责定位。

原位保留：根 APK、`raw/phone_20261015_full_02` 和 refresh 原件、`work/apk`／`work/protection`／`work/full_unpack/shards`（除非另行列入）、当前 `output/character_skills/profiles/rules.json` 与 `pages/<cid>/card.json`、P/v7 与冻结 plans、历史 ZIP 和独审报告。此处 16 棵均归“须先适配后并入”，没有可直接一次窗口移的根，也没有把某棵剩余根藏在“原位保留”。

机器清单及逐项 static alias 路径见 [unpack-assets.json](unpack-assets.json)。依据为 1140 行 path-map、21 contract、静态引用／reparse 索引、命令 I/O 矩阵及第二／三批现核调查；本任务只读取这些已有证据和少量 pointer/manifest/脚本片段。
