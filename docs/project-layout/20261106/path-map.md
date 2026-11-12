# 六个子项目路径映射修订版

修订：2026-11-07T00:28:06+08:00。1140条路径；21项人工核对耦合契约。未移动文件。

先读[审计结论](audit/coupling-report.md)。目标位置仅表示未来布局；物理处置和契约门槛优先。冻结历史只建索引入口，在途资料原位保护。静态引用次数不是运行依赖数；目录契约不等于每个后代都具同种读取方式。

## 数据解包

| 现有路径 | 拟定目标或保留位置 | 物理处置 | 契约 | 在途任务 | 说明 |
|---|---|---|---|---|---|
| output/apk | projects/unpack/data/apk/apk-baseline | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/base_master | projects/unpack/data/apk/base_master | 保持原位，后续仅在具体迁移任务中实施 | C03 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/cache_full_20261015 | projects/unpack/data/cache/cache_full_20261015 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/cache_full_20261015_v2 | projects/unpack/data/cache/cache_full_20261015_v2 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/cache_full_20261015_v3 | projects/unpack/data/cache/cache_full_20261015_v3 | 保持原位，后续仅在具体迁移任务中实施 | C03,C07 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/cache_full_latest.json | projects/unpack/data/cache/cache_full_latest.json | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 仅对应产物检查完成后更新当前指针 |
| output/cache_refresh_20261015 | projects/unpack/data/cache/cache_refresh_20261015 | 保持原位，后续仅在具体迁移任务中实施 | C02 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/cache_refresh_latest.json | projects/unpack/data/cache/cache_refresh_latest.json | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 仅对应产物检查完成后更新当前指针 |
| output/decoded | projects/unpack/history/decoded | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/export | projects/unpack/data/export | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/il2cpp | projects/unpack/research/il2cpp | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 格式与元数据恢复归解包；同目录也含技能语义反汇编，研究是消费者；不因归属解包而切断研究引用 |
| output/native | projects/unpack/research/native | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/phone | projects/unpack/reports/acquisition/phone | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/phone_full_20261015 | projects/unpack/reports/acquisition/phone_full_20261015 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/phone_refresh_20261015 | projects/unpack/reports/acquisition/phone_refresh_20261015 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/protection | projects/unpack/research/protection | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/single | projects/unpack/history/single | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/validation | projects/unpack/reports/validation | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| scripts/analyze_cache_snapshot.py | projects/unpack/src/analyze_cache_snapshot.py | 保持原位，后续仅在具体迁移任务中实施 | C20 | T02,T06 | 还导入字段指南并读取样板/export/phone；跨研究消费者未适配前原位 |
| scripts/apk_baseline.py | projects/unpack/src/apk_baseline.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/apk_certificate.py | projects/unpack/src/apk_certificate.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/bounded_decode.py | projects/unpack/src/bounded_decode.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/cache_probe.py | projects/unpack/src/cache_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/callback_key_candidates.py | projects/unpack/src/callback_key_candidates.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/callback_sample.py | projects/unpack/src/callback_sample.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/collect_cache_archive.py | projects/unpack/src/collect_cache_archive.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/collect_cache_refresh.py | projects/unpack/src/collect_cache_refresh.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/decode_cache_snapshot.py | projects/unpack/src/decode_cache_snapshot.py | 保持原位，后续仅在具体迁移任务中实施 | C20 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/decode_cache_variants.py | projects/unpack/src/decode_cache_variants.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/decode_chronicle.py | projects/unpack/src/decode_chronicle.py | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/decode_data5.py | projects/unpack/src/decode_data5.py | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/elf_branch_refs.py | projects/unpack/src/elf_branch_refs.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/elf_global_refs.py | projects/unpack/src/elf_global_refs.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/elf_relocations.py | projects/unpack/src/elf_relocations.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/emulator_probe.py | projects/unpack/src/emulator_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/export_master.py | projects/unpack/src/export_master.py | 保持原位，后续仅在具体迁移任务中实施 | C20 | T02,T06 | 纯解析被解包复用，main还消费phase-D证据；混合接口先不拆 |
| scripts/extract_cache_archive.py | projects/unpack/src/extract_cache_archive.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/guest_lz4.py | projects/unpack/src/guest_lz4.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/il2cpp_metadata_entry.py | projects/unpack/src/il2cpp_metadata_entry.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/il2cpp_sample_code.py | projects/unpack/src/il2cpp_sample_code.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/jni_prefix_probe.py | projects/unpack/src/jni_prefix_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/metadata_decode_probe.py | projects/unpack/src/metadata_decode_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/metadata_targets.py | projects/unpack/src/metadata_targets.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/native_debug.py | projects/unpack/src/native_debug.py | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/native_plugin_paths.py | projects/unpack/src/native_plugin_paths.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/native_probe.py | projects/unpack/src/native_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/native_readpaths.py | projects/unpack/src/native_readpaths.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/nutils_data_probe.py | projects/unpack/src/nutils_data_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/phone_collect.py | projects/unpack/src/phone_collect.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/protection_emulate.py | projects/unpack/src/protection_emulate.py | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/protection_report.py | projects/unpack/src/protection_report.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/protection_sample.py | projects/unpack/src/protection_sample.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/recovered_readpaths.py | projects/unpack/src/recovered_readpaths.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/signal_region_probe.py | projects/unpack/src/signal_region_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_cache_refresh.py | projects/unpack/src/verify_cache_refresh.py | 保持原位，后续仅在具体迁移任务中实施 | C02 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_cache_snapshot.py | projects/unpack/src/verify_cache_snapshot.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_data5.py | projects/unpack/src/verify_data5.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_export.py | projects/unpack/src/verify_export.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_export_pointer.py | projects/unpack/src/verify_export_pointer.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_metadata.py | projects/unpack/src/verify_metadata.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_phase_a.py | projects/unpack/src/verify_phase_a.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_phase_b.py | projects/unpack/src/verify_phase_b.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_phase_c.py | projects/unpack/src/verify_phase_c.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T06 | 迁移前核对 import、默认路径和外部调用 |
| raw/_p.tmp | raw/_p.tmp | 原件原位保护 | 待核 | T02,T06 | 不复制或搬迁；由各子项目配置引用 |
| raw/phone_20261014_binary_retry | raw/phone_20261014_binary_retry | 原件原位保护 | 待核 | T02,T06 | 不复制或搬迁；由各子项目配置引用 |
| raw/phone_20261014_connected | raw/phone_20261014_connected | 原件原位保护 | 待核 | T02,T06 | 不复制或搬迁；由各子项目配置引用 |
| raw/phone_20261015_full_01 | raw/phone_20261015_full_01 | 原件原位保护 | 待核 | T02,T06 | 不复制或搬迁；由各子项目配置引用 |
| raw/phone_20261015_full_02 | raw/phone_20261015_full_02 | 原件原位保护 | C02 | T02,T06 | 不复制或搬迁；由各子项目配置引用 |
| raw/phone_20261015_refresh_01 | raw/phone_20261015_refresh_01 | 原件原位保护 | 待核 | T02,T06 | 不复制或搬迁；由各子项目配置引用 |
| raw/phone_20261015_refresh_02 | raw/phone_20261015_refresh_02 | 原件原位保护 | C02 | T02,T06 | 不复制或搬迁；由各子项目配置引用 |
| work/apk | work/apk | 工作／恢复材料原位保护 | C01 | T02,T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/decoded_candidates | work/decoded_candidates | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 原生data5探针解码中间材料；由nutils_data_probe直接生产，另写output/native/data_probe；未证明这些历史中间产物是当前正式解码器必需输入；限制：未逐项对账历史report或穷尽动态消费者；子项目索引归属：projects/unpack/history/work/decoded_candidates |
| work/phase_c_checks | work/phase_c_checks | 工作／恢复材料原位保护 | 待核 | T02,T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/phase_e_delivery_fix_20261015_4a244651af | work/phase_e_delivery_fix_20261015_4a244651af | 工作／恢复材料原位保护 | 待核 | T02,T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/phone_20261015_full_02 | work/phone_20261015_full_02 | 工作／恢复材料原位保护 | C02 | T02,T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/phone_20261015_refresh_02 | work/phone_20261015_refresh_02 | 工作／恢复材料原位保护 | C02 | T02,T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/phone_candidates | work/phone_candidates | 工作／恢复材料原位保护 | 待核 | T02,T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/protection | work/protection | 工作／恢复材料原位保护 | C01 | T02,T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| output/protection/relocations.json | projects/unpack/runtime/relocations.json | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02 | 每次Experiment初始化的实际输入 |
| output/native/recovered_symbols.json | projects/unpack/runtime/recovered_symbols.json | 保持原位，后续仅在具体迁移任务中实施 | C01 | T02 | chronicle解码运行输入 |

## 媒体资源

| 现有路径 | 拟定目标或保留位置 | 物理处置 | 契约 | 在途任务 | 说明 |
|---|---|---|---|---|---|
| output/card_images | projects/assets/data/card_images | 保持原位，后续仅在具体迁移任务中实施 | C16 | T01,T02 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/full_unpack | projects/assets/data/full_unpack | 保持原位，后续仅在具体迁移任务中实施 | C16 | T01,T02 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/unity | projects/assets/history/unity | 保持原位，后续仅在具体迁移任务中实施 | C16 | T01,T02 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| scripts/audit_unity_headers.py | projects/assets/src/audit_unity_headers.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/extract_cid30236_images.py | projects/assets/src/extract_cid30236_images.py | 保持原位，后续仅在具体迁移任务中实施 | C16 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/full_unpack_finalize.py | projects/assets/src/full_unpack_finalize.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/full_unpack_merge.py | projects/assets/src/full_unpack_merge.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/full_unpack_probe.py | projects/assets/src/full_unpack_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/full_unpack_run.py | projects/assets/src/full_unpack_run.py | 保持原位，后续仅在具体迁移任务中实施 | C02 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/full_unpack_verify.py | projects/assets/src/full_unpack_verify.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/mono_headers.py | projects/assets/src/mono_headers.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/trace_cid30236_art.py | projects/assets/src/trace_cid30236_art.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| scripts/unity_scan.py | projects/assets/src/unity_scan.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 迁移前核对 import、默认路径和外部调用 |
| work/full_unpack | work/full_unpack | 工作／恢复材料原位保护 | 待核 | T01,T02 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| docs/tasks/20261016-full-unpack.md | projects/assets/docs/tasks/20261016-full-unpack.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T02 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| output/character_skills/pages/art | projects/assets/data/page-art | 在途生产者／消费者共同保护 | C07,C08,C09,C15,C16 | T01,T02 | 媒体共享接口：生产渲染器写入，reader直接相对引用；未来站点副本另建 |

## 技能研究

| 现有路径 | 拟定目标或保留位置 | 物理处置 | 契约 | 在途任务 | 说明 |
|---|---|---|---|---|---|
| output/boss_chain | projects/skill-research/evidence/boss_chain | 保持原位，后续仅在具体迁移任务中实施 | C04 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/boss_heal | projects/skill-research/evidence/boss_heal | 保持原位，后续仅在具体迁移任务中实施 | C03,C04 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/card_comparison_cid30236 | projects/skill-research/evidence/card_comparison_cid30236 | 保持原位，后续仅在具体迁移任务中实施 | C03,C04 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/char_roster | projects/skill-research/data/char_roster | 保持原位，后续仅在具体迁移任务中实施 | C06,C16 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/character_skills | projects/skill-research/ | 保持原位，后续仅在具体迁移任务中实施 | C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C21 | T02,T04 | 仅逻辑归属；以下子行覆盖此行；禁止整目录移动 |
| output/field_guide | projects/skill-research/reports/field_guide | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/ordinary_effects | projects/skill-research/evidence/ordinary_effects | 保持原位，后续仅在具体迁移任务中实施 | C03,C04 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/phase_d | projects/skill-research/evidence/phase_d | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/sample | projects/skill-research/evidence/sample | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/skill_mechanism_scale | projects/skill-research/experiments/skill_mechanism_scale | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/skill_mechanism_trial | projects/skill-research/experiments/skill_mechanism_trial | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/skill_route_experiments | projects/skill-research/experiments/skill_route_experiments | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/structured | projects/skill-research/data/structured | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/character_skills/attack_interval_batch1_20261024 | projects/skill-research/history/attack_interval_batch1_20261024 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/attack_interval_batch2_20261025 | projects/skill-research/history/attack_interval_batch2_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/attack_interval_batch2_preparation_20261025 | projects/skill-research/history/attack_interval_batch2_preparation_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/attack_interval_batch3_20261025 | projects/skill-research/history/attack_interval_batch3_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/attack_interval_batch3_preparation_20261025 | projects/skill-research/history/attack_interval_batch3_preparation_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/attack_interval_preparation_20261024 | projects/skill-research/history/attack_interval_preparation_20261024 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/b18_20261025 | projects/skill-research/history/b18_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/boss_attack_types | projects/skill-research/evidence/boss_attack_types | 保持原位，后续仅在具体迁移任务中实施 | C03 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/boss_heal_types | projects/skill-research/evidence/boss_heal_types | 保持原位，后续仅在具体迁移任务中实施 | C03 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/c10_p1_20261030 | projects/skill-research/history/c10_p1_20261030 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c11_delivery_20261031 | projects/skill-research/history/c11_delivery_20261031 | 保持原位，后续仅在具体迁移任务中实施 | C12 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c11_p1_t114_20261031 | projects/skill-research/history/c11_p1_t114_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c11_p2_selection_20261031 | projects/skill-research/history/c11_p2_selection_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c11_p2_t114_yg_20261031 | projects/skill-research/history/c11_p2_t114_yg_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c11_p2_union_count_20261031 | projects/skill-research/history/c11_p2_union_count_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c11_p3_selection_20261031 | projects/skill-research/history/c11_p3_selection_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c11_p3_strength_job2_20261031 | projects/skill-research/history/c11_p3_strength_job2_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c12_delivery_20261031 | projects/skill-research/history/c12_delivery_20261031 | 保持原位，后续仅在具体迁移任务中实施 | C12 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c12_p1_selection_20261031 | projects/skill-research/history/c12_p1_selection_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c12_p1_sympathy_attack_20261031 | projects/skill-research/history/c12_p1_sympathy_attack_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c12_p2_selection_20261031 | projects/skill-research/history/c12_p2_selection_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c12_p2_sympathy_3005_sub1_20261031 | projects/skill-research/history/c12_p2_sympathy_3005_sub1_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c12_p3_selection_20261031 | projects/skill-research/history/c12_p3_selection_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c12_p3_skilltext_mirror_20261031 | projects/skill-research/history/c12_p3_skilltext_mirror_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c13_delivery_20261031 | projects/skill-research/history/c13_delivery_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c13_p1_supporterskill_type8_20261031 | projects/skill-research/history/c13_p1_supporterskill_type8_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c13_p2_t27_mirror_20261031 | projects/skill-research/history/c13_p2_t27_mirror_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c13_p3_2012_duration_20261031 | projects/skill-research/history/c13_p3_2012_duration_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c14_delivery_20261103 | projects/skill-research/history/c14_delivery_20261103 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c14_p1_2003_enemy_debuff_20261102 | projects/skill-research/history/c14_p1_2003_enemy_debuff_20261102 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c14_p2_boss_damage_direct_20261102 | projects/skill-research/history/c14_p2_boss_damage_direct_20261102 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c15_delivery_20261103 | projects/skill-research/history/c15_delivery_20261103 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c15_p1_denju_damage_direct_20261103 | projects/skill-research/history/c15_p1_denju_damage_direct_20261103 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c16_delivery_20261104 | projects/skill-research/history/c16_delivery_20261104 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c16_p1_1095_partial_20261104 | projects/skill-research/history/c16_p1_1095_partial_20261104 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c17_delivery_20261106 | projects/skill-research/history/c17_delivery_20261106 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c17_p1_1095_attack_partial_20261106 | projects/skill-research/history/c17_p1_1095_attack_partial_20261106 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c18_delivery_20261106 | projects/skill-research/history/c18_delivery_20261106 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c18_p1_1095_attack_partial_20261106 | projects/skill-research/history/c18_p1_1095_attack_partial_20261106 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c7_p1_20261029 | projects/skill-research/history/c7_p1_20261029 | 保持原位，后续仅在具体迁移任务中实施 | C21 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c7_p2_20261030 | projects/skill-research/history/c7_p2_20261030 | 保持原位，后续仅在具体迁移任务中实施 | C21 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c7_p3_20261030 | projects/skill-research/history/c7_p3_20261030 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c8_p1_20261030 | projects/skill-research/history/c8_p1_20261030 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/c9_p1_20261030 | projects/skill-research/history/c9_p1_20261030 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/charainfo_params | projects/skill-research/evidence/charainfo_params | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/charainfo_types | projects/skill-research/evidence/charainfo_types | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/closeout_c11_c12_20261031 | projects/skill-research/history/closeout_c11_c12_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/closeout_c13_r01_empty_id_20261102 | projects/skill-research/history/closeout_c13_r01_empty_id_20261102 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/cp_paths | projects/skill-research/evidence/cp_paths | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/crit_absorb_20261026 | projects/skill-research/history/crit_absorb_20261026 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/cycle2_rectification_20261026 | projects/skill-research/history/cycle2_rectification_20261026 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/cycle_reports | output/character_skills/cycle_reports | 冻结原件原位；子项目建立索引入口 | C12 | T02,T04 | 原内容保留；路径兼容及来源映射由迁移层处理；子项目索引归属：projects/skill-research/reports/cycle_reports |
| output/character_skills/cycles3to5_rectification_20261029 | projects/skill-research/history/cycles3to5_rectification_20261029 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/denju_skills | projects/skill-research/evidence/denju_skills | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/description_bindings | projects/skill-research/data/description_bindings | 保持原位，后续仅在具体迁移任务中实施 | C04,C05 | T02,T04 | 当前生产输入或派生数据；迁移前确认实际生产者 |
| output/character_skills/effect_ledger | projects/skill-research/data/effect_ledger | 在途生产者／消费者共同保护 | C10,C15 | T02,T04 | 当前生产输入或派生数据；迁移前确认实际生产者 |
| output/character_skills/g0_g7b0_20261028 | projects/skill-research/history/g0_g7b0_20261028 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/g1_b1_20261029 | projects/skill-research/history/g1_b1_20261029 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/g7_b1_20261029 | projects/skill-research/history/g7_b1_20261029 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/gaps | projects/skill-research/data/gaps | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 当前生产输入或派生数据；迁移前确认实际生产者 |
| output/character_skills/gold_exp_20261028 | projects/skill-research/history/gold_exp_20261028 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/heal_interval_20261028 | projects/skill-research/history/heal_interval_20261028 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/host_review_closeout_20261025 | projects/skill-research/history/host_review_closeout_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/host_takeover_20261024 | projects/skill-research/history/host_takeover_20261024 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/incident_sync_20261024 | projects/skill-research/history/incident_sync_20261024 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/inference_inventory | projects/skill-research/data/inference_inventory | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 当前生产输入或派生数据；迁移前确认实际生产者 |
| output/character_skills/kill_mana_20261029 | projects/skill-research/history/kill_mana_20261029 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/kyoumei_ab_20261025 | projects/skill-research/history/kyoumei_ab_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/links | projects/skill-research/data/links | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 当前生产输入或派生数据；迁移前确认实际生产者 |
| output/character_skills/mana_b_batch_20261026 | projects/skill-research/history/mana_b_batch_20261026 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/mana_batch_20261025 | projects/skill-research/history/mana_batch_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/mana_ledger_mapping_20261026 | projects/skill-research/history/mana_ledger_mapping_20261026 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/mechanism_first_reconciliation_20261104 | projects/skill-research/history/mechanism_first_reconciliation_20261104 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/P10_HANDOFF.md | projects/skill-research/docs/legacy/P10_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P2B2_HANDOFF.md | projects/skill-research/docs/legacy/P2B2_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P2R_HANDOFF.md | projects/skill-research/docs/legacy/P2R_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3_HANDOFF.md | projects/skill-research/docs/legacy/P3_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B10_HANDOFF.md | projects/skill-research/docs/legacy/P3B10_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B1_HANDOFF.md | projects/skill-research/docs/legacy/P3B1_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B2_HANDOFF.md | projects/skill-research/docs/legacy/P3B2_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B3_HANDOFF.md | projects/skill-research/docs/legacy/P3B3_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B4_HANDOFF.md | projects/skill-research/docs/legacy/P3B4_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B5_HANDOFF.md | projects/skill-research/docs/legacy/P3B5_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B6_HANDOFF.md | projects/skill-research/docs/legacy/P3B6_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B7_HANDOFF.md | projects/skill-research/docs/legacy/P3B7_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B8_HANDOFF.md | projects/skill-research/docs/legacy/P3B8_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P3B9_HANDOFF.md | projects/skill-research/docs/legacy/P3B9_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P4_HANDOFF.md | projects/skill-research/docs/legacy/P4_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P5_HANDOFF.md | projects/skill-research/docs/legacy/P5_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P6_HANDOFF.md | projects/skill-research/docs/legacy/P6_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P7_HANDOFF.md | projects/skill-research/docs/legacy/P7_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P8_HANDOFF.md | projects/skill-research/docs/legacy/P8_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/P9_HANDOFF.md | projects/skill-research/docs/legacy/P9_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/pages | output/character_skills/pages | 在途生产者／消费者共同保护 | C07,C08,C09,C10,C12,C13,C15,C16 | T01,T02,T04 | 撤回可直接按扩展名拆分的假设：数据、HTML、receipt、blocker及_batch目前同事务；旧card还作输入指纹 |
| output/character_skills/pages_versions | projects/skill-research/history/pages_versions | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 版本材料不改写；同时核验保留 pin |
| output/character_skills/profiles | projects/skill-research/data/profiles | 在途生产者／消费者共同保护 | C06,C10,C15 | T02,T04 | 当前生产输入或派生数据；迁移前确认实际生产者 |
| output/character_skills/R1_HANDOFF.md | projects/skill-research/docs/legacy/R1_HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/r2_preparation | projects/skill-research/contracts/r2_preparation | 保持原位，后续仅在具体迁移任务中实施 | C06,C09 | T02,T04 | 当前cohort manifest及CSV，不是可直接退役的普通history |
| output/character_skills/README.md | projects/skill-research/docs/legacy/README.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 历史 README 不当作当前看板 |
| output/character_skills/rectification_c11_c12_20261031 | projects/skill-research/history/rectification_c11_c12_20261031 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/rectification_c11_c12_20261031_r2 | projects/skill-research/history/rectification_c11_c12_20261031_r2 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/rectification_c13_r01_20261101 | projects/skill-research/history/rectification_c13_r01_20261101 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/rectification_c13_r01_empty_id_20261101 | projects/skill-research/history/rectification_c13_r01_empty_id_20261101 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/rectification_c14_r01_source_presentation_20261103 | projects/skill-research/history/rectification_c14_r01_source_presentation_20261103 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/rectification_c15_r01_default_reading_20261104 | projects/skill-research/history/rectification_c15_r01_default_reading_20261104 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/remaining_five | projects/skill-research/evidence/remaining_five | 保持原位，后续仅在具体迁移任务中实施 | C03 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/review | output/character_skills/review | 冻结原件原位；子项目建立索引入口 | C04,C11,C12 | T02,T04 | 原内容保留；路径兼容及来源映射由迁移层处理；子项目索引归属：projects/skill-research/reports/review |
| output/character_skills/rule_registration_20261028 | projects/skill-research/history/rule_registration_20261028 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/s5_nonterrain_20261026 | projects/skill-research/history/s5_nonterrain_20261026 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/s5_terrain_20261026 | projects/skill-research/history/s5_terrain_20261026 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/scope_diff | projects/skill-research/data/scope_diff | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 当前生产输入或派生数据；迁移前确认实际生产者 |
| output/character_skills/skilllist_types | projects/skill-research/evidence/skilllist_types | 保持原位，后续仅在具体迁移任务中实施 | C03 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/type1082 | projects/skill-research/evidence/type1082 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/type26_mana | projects/skill-research/evidence/type26_mana | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/type67_20261028 | projects/skill-research/history/type67_20261028 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/type80_96_20261028 | projects/skill-research/history/type80_96_20261028 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/type9_crit | projects/skill-research/evidence/type9_crit | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 被规则或交付引用的原生与字段证据，不视作可丢弃历史 |
| output/character_skills/validation | projects/skill-research/reports/validation | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 原内容保留；路径兼容及来源映射由迁移层处理 |
| output/character_skills/yg1_batch1_20261024 | projects/skill-research/history/yg1_batch1_20261024 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/yg1_batch2_20261024 | projects/skill-research/history/yg1_batch2_20261024 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/yg1_batch3_20261024 | projects/skill-research/history/yg1_batch3_20261024 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/yg1_remaining_ab_batch1_20261025 | projects/skill-research/history/yg1_remaining_ab_batch1_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/yg1_remaining_ab_plan_20261025 | projects/skill-research/history/yg1_remaining_ab_plan_20261025 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| output/character_skills/yg_unresolved_20261026 | projects/skill-research/history/yg_unresolved_20261026 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 保留原目录名；history 只表达记录组织，不宣告可删或已停用 |
| scripts/active_skill_trace.py | projects/skill-research/src/active_skill_trace.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/boss_chain_probe.py | projects/skill-research/src/boss_chain_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/boss_chain_trace.py | projects/skill-research/src/boss_chain_trace.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/boss_guard_basis.py | projects/skill-research/src/boss_guard_basis.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/boss_heal_probe.py | projects/skill-research/src/boss_heal_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/boss_heal_trace.py | projects/skill-research/src/boss_heal_trace.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/boss_type105_probe.py | projects/skill-research/src/boss_type105_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/boss_type105_trace.py | projects/skill-research/src/boss_type105_trace.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/boss_type112_probe.py | projects/skill-research/src/boss_type112_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/build_boss_chain_guide.py | projects/skill-research/src/build_boss_chain_guide.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/build_boss_heal_guide.py | projects/skill-research/src/build_boss_heal_guide.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/build_char_roster.py | projects/skill-research/src/build_char_roster.py | 保持原位，后续仅在具体迁移任务中实施 | C16,C20 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/build_chica_comparison.py | projects/skill-research/src/build_chica_comparison.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/build_field_guide.py | projects/skill-research/src/build_field_guide.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/character_skills | projects/skill-research/src/character_skills | ZCode主线所有者保护；路径签名未适配不得拆 | C01,C03,C04,C05,C06,C07,C08,C09,C10,C12,C16,C17 | T02,T04 | 同级 import 与固定根目录深度需要核对；具体子行优先 |
| scripts/character_skills_pipeline | projects/skill-research/src/character_skills_pipeline | 保持原位，后续仅在具体迁移任务中实施 | C11 | T02,T04 | 同级 import 与固定根目录深度需要核对；具体子行优先 |
| scripts/chica_barrier_request.py | projects/skill-research/src/chica_barrier_request.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_barrier_rule.py | projects/skill-research/src/chica_barrier_rule.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_chain_dispatch.py | projects/skill-research/src/chica_chain_dispatch.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_chain_mana.py | projects/skill-research/src/chica_chain_mana.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_critical_rules.py | projects/skill-research/src/chica_critical_rules.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_description_effects.py | projects/skill-research/src/chica_description_effects.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_difference_sources.py | projects/skill-research/src/chica_difference_sources.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_field_time.py | projects/skill-research/src/chica_field_time.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_leader_condition.py | projects/skill-research/src/chica_leader_condition.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_lifesteal.py | projects/skill-research/src/chica_lifesteal.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_mana_chance.py | projects/skill-research/src/chica_mana_chance.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_move_rules.py | projects/skill-research/src/chica_move_rules.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_ordinary_rules.py | projects/skill-research/src/chica_ordinary_rules.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_remaining_effects.py | projects/skill-research/src/chica_remaining_effects.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_skill_power.py | projects/skill-research/src/chica_skill_power.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_source_priority.py | projects/skill-research/src/chica_source_priority.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_super_counter.py | projects/skill-research/src/chica_super_counter.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_timed_support.py | projects/skill-research/src/chica_timed_support.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/chica_wedge_time.py | projects/skill-research/src/chica_wedge_time.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/high_hp_sample_probe.py | projects/skill-research/src/high_hp_sample_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/master_source_compare.py | projects/skill-research/src/master_source_compare.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ordinary_1008_probe.py | projects/skill-research/src/ordinary_1008_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ordinary_1017_probe.py | projects/skill-research/src/ordinary_1017_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ordinary_1095_probe.py | projects/skill-research/src/ordinary_1095_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ordinary_2012_probe.py | projects/skill-research/src/ordinary_2012_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ordinary_3000_probe.py | projects/skill-research/src/ordinary_3000_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ordinary_7_probe.py | projects/skill-research/src/ordinary_7_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ordinary_99_probe.py | projects/skill-research/src/ordinary_99_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ordinary_effect_dictionary.py | projects/skill-research/src/ordinary_effect_dictionary.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/phase_d_chain_probe.py | projects/skill-research/src/phase_d_chain_probe.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/phase_d_source_rule.py | projects/skill-research/src/phase_d_source_rule.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/phase_d_trace.py | projects/skill-research/src/phase_d_trace.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/query_effect_dictionary.py | projects/skill-research/src/query_effect_dictionary.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 按已有入口职责与名称归类；未逐函数分析。旧查询字典不等于当前答案 CLI |
| scripts/sample_trace.py | projects/skill-research/src/sample_trace.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/skill_mechanism_scale | projects/skill-research/src/skill_mechanism_scale | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 同级 import 与固定根目录深度需要核对；具体子行优先 |
| scripts/skill_mechanism_trial | projects/skill-research/src/skill_mechanism_trial | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 同级 import 与固定根目录深度需要核对；具体子行优先 |
| scripts/skill_route_experiments | projects/skill-research/src/skill_route_experiments | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 同级 import 与固定根目录深度需要核对；具体子行优先 |
| scripts/structured_candidates.py | projects/skill-research/src/structured_candidates.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/verify_chica_comparison.py | projects/skill-research/src/verify_chica_comparison.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 迁移前核对 import、默认路径和外部调用 |
| scripts/character_skills/batch_bindings.py | projects/skill-research/src/character_skills/batch_bindings.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/boss_attack_types.py | projects/skill-research/src/character_skills/boss_attack_types.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/boss_heal_types.py | projects/skill-research/src/character_skills/boss_heal_types.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page.py | projects/skill-research/src/character_skills/card_page.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_attack_interval_grants.py | projects/skill-research/src/character_skills/card_page_attack_interval_grants.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_basic.py | projects/skill-research/src/character_skills/card_page_basic.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_batch.py | projects/skill-research/src/character_skills/card_page_batch.py | ZCode主线所有者保护；路径签名未适配不得拆 | C06,C08,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_batch_parallel.py | projects/skill-research/src/character_skills/card_page_batch_parallel.py | ZCode主线所有者保护；路径签名未适配不得拆 | C08,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_check.py | projects/skill-research/src/character_skills/card_page_check.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_cohorts.py | projects/skill-research/src/character_skills/card_page_cohorts.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_data.py | projects/skill-research/src/character_skills/card_page_data.py | ZCode主线所有者保护；路径签名未适配不得拆 | C03,C07,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_dependencies.py | projects/skill-research/src/character_skills/card_page_dependencies.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_1017.py | projects/skill-research/src/character_skills/card_page_inference_1017.py | ZCode主线所有者保护；路径签名未适配不得拆 | C04,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_attack_interval.py | projects/skill-research/src/character_skills/card_page_inference_attack_interval.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_attack_interval2.py | projects/skill-research/src/character_skills/card_page_inference_attack_interval2.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_attack_interval3.py | projects/skill-research/src/character_skills/card_page_inference_attack_interval3.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b10_sa2003.py | projects/skill-research/src/character_skills/card_page_inference_b10_sa2003.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b11_sa1095.py | projects/skill-research/src/character_skills/card_page_inference_b11_sa1095.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b12_1095ext.py | projects/skill-research/src/character_skills/card_page_inference_b12_1095ext.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b13_apkext.py | projects/skill-research/src/character_skills/card_page_inference_b13_apkext.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b14_apkext.py | projects/skill-research/src/character_skills/card_page_inference_b14_apkext.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b15_union.py | projects/skill-research/src/character_skills/card_page_inference_b15_union.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b17_p0finale.py | projects/skill-research/src/character_skills/card_page_inference_b17_p0finale.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b18_duration.py | projects/skill-research/src/character_skills/card_page_inference_b18_duration.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b5_xtable.py | projects/skill-research/src/character_skills/card_page_inference_b5_xtable.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b6_bossbuff.py | projects/skill-research/src/character_skills/card_page_inference_b6_bossbuff.py | ZCode主线所有者保护；路径签名未适配不得拆 | C04,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b7_sympathy.py | projects/skill-research/src/character_skills/card_page_inference_b7_sympathy.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b8_crit2012.py | projects/skill-research/src/character_skills/card_page_inference_b8_crit2012.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_b9_debuff.py | projects/skill-research/src/character_skills/card_page_inference_b9_debuff.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c10_p1_mirror.py | projects/skill-research/src/character_skills/card_page_inference_c10_p1_mirror.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c11_p1_t114.py | projects/skill-research/src/character_skills/card_page_inference_c11_p1_t114.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c11_p2_union_count.py | projects/skill-research/src/character_skills/card_page_inference_c11_p2_union_count.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c11_p3_strength_job2.py | projects/skill-research/src/character_skills/card_page_inference_c11_p3_strength_job2.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c12_p1_sympathy_attack.py | projects/skill-research/src/character_skills/card_page_inference_c12_p1_sympathy_attack.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c12_p2_sympathy_3005_sub1.py | projects/skill-research/src/character_skills/card_page_inference_c12_p2_sympathy_3005_sub1.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c12_p3_skilltext_mirror.py | projects/skill-research/src/character_skills/card_page_inference_c12_p3_skilltext_mirror.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c13_p1_supporterskill_type8.py | projects/skill-research/src/character_skills/card_page_inference_c13_p1_supporterskill_type8.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c13_p2_t27_mirror.py | projects/skill-research/src/character_skills/card_page_inference_c13_p2_t27_mirror.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c13_p3_2012_duration.py | projects/skill-research/src/character_skills/card_page_inference_c13_p3_2012_duration.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c14_p1_2003_enemy_debuff.py | projects/skill-research/src/character_skills/card_page_inference_c14_p1_2003_enemy_debuff.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c14_p2_boss_damage_direct.py | projects/skill-research/src/character_skills/card_page_inference_c14_p2_boss_damage_direct.py | ZCode主线所有者保护；路径签名未适配不得拆 | C07,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c15_p1_denju_damage_direct.py | projects/skill-research/src/character_skills/card_page_inference_c15_p1_denju_damage_direct.py | ZCode主线所有者保护；路径签名未适配不得拆 | C07,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c16_p1_1095_partial.py | projects/skill-research/src/character_skills/card_page_inference_c16_p1_1095_partial.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c17_p1_1095_attack_partial.py | projects/skill-research/src/character_skills/card_page_inference_c17_p1_1095_attack_partial.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c18_p1_1095_attack_partial.py | projects/skill-research/src/character_skills/card_page_inference_c18_p1_1095_attack_partial.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c7_p2_denju.py | projects/skill-research/src/character_skills/card_page_inference_c7_p2_denju.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c7_p3_denju.py | projects/skill-research/src/character_skills/card_page_inference_c7_p3_denju.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c8_p1_denju.py | projects/skill-research/src/character_skills/card_page_inference_c8_p1_denju.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c8_p1_t27.py | projects/skill-research/src/character_skills/card_page_inference_c8_p1_t27.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c9_p1_t64.py | projects/skill-research/src/character_skills/card_page_inference_c9_p1_t64.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_c9_p1_t99.py | projects/skill-research/src/character_skills/card_page_inference_c9_p1_t99.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_cond.py | projects/skill-research/src/character_skills/card_page_inference_cond.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_crit_absorb.py | projects/skill-research/src/character_skills/card_page_inference_crit_absorb.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_g0_g7b0.py | projects/skill-research/src/character_skills/card_page_inference_g0_g7b0.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_g1_b1.py | projects/skill-research/src/character_skills/card_page_inference_g1_b1.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_g1_structure.py | projects/skill-research/src/character_skills/card_page_inference_g1_structure.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_g7_b1.py | projects/skill-research/src/character_skills/card_page_inference_g7_b1.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_gold_exp.py | projects/skill-research/src/character_skills/card_page_inference_gold_exp.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_heal_interval.py | projects/skill-research/src/character_skills/card_page_inference_heal_interval.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_kyoumei_ab.py | projects/skill-research/src/character_skills/card_page_inference_kyoumei_ab.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_mana.py | projects/skill-research/src/character_skills/card_page_inference_mana.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_mana_b.py | projects/skill-research/src/character_skills/card_page_inference_mana_b.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_s5.py | projects/skill-research/src/character_skills/card_page_inference_s5.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_s5_terrain.py | projects/skill-research/src/character_skills/card_page_inference_s5_terrain.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_type67.py | projects/skill-research/src/character_skills/card_page_inference_type67.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_type8.py | projects/skill-research/src/character_skills/card_page_inference_type8.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_type80_96.py | projects/skill-research/src/character_skills/card_page_inference_type80_96.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_yg1.py | projects/skill-research/src/character_skills/card_page_inference_yg1.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_yg1_multihit.py | projects/skill-research/src/character_skills/card_page_inference_yg1_multihit.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_yg1_multihit_timing.py | projects/skill-research/src/character_skills/card_page_inference_yg1_multihit_timing.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_yg1_multistage.py | projects/skill-research/src/character_skills/card_page_inference_yg1_multistage.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_yg1_remaining_ab.py | projects/skill-research/src/character_skills/card_page_inference_yg1_remaining_ab.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_inference_yg1_timing.py | projects/skill-research/src/character_skills/card_page_inference_yg1_timing.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_policy.py | projects/skill-research/src/character_skills/card_page_policy.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_positions.py | projects/skill-research/src/character_skills/card_page_positions.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_r2_fixes_check.py | projects/skill-research/src/character_skills/card_page_r2_fixes_check.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_r2_prep.py | projects/skill-research/src/character_skills/card_page_r2_prep.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_source_fix.py | projects/skill-research/src/character_skills/card_page_source_fix.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_verify_full.py | projects/skill-research/src/character_skills/card_page_verify_full.py | ZCode主线所有者保护；路径签名未适配不得拆 | C06,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/card_page_write.py | projects/skill-research/src/character_skills/card_page_write.py | ZCode主线所有者保护；路径签名未适配不得拆 | C08,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/charainfo_params.py | projects/skill-research/src/character_skills/charainfo_params.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/charainfo_types.py | projects/skill-research/src/character_skills/charainfo_types.py | ZCode主线所有者保护；路径签名未适配不得拆 | C01,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/common.py | projects/skill-research/src/character_skills/common.py | ZCode主线所有者保护；路径签名未适配不得拆 | C03,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/composite_branches.py | projects/skill-research/src/character_skills/composite_branches.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/cp_paths.py | projects/skill-research/src/character_skills/cp_paths.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/crosscheck_raw.py | projects/skill-research/src/character_skills/crosscheck_raw.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/cycle_report.py | projects/skill-research/src/character_skills/cycle_report.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09,C12 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/denju_skills.py | projects/skill-research/src/character_skills/denju_skills.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/description_bindings.py | projects/skill-research/src/character_skills/description_bindings.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/effect_ledger.py | projects/skill-research/src/character_skills/effect_ledger.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09,C10 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/equivalence.py | projects/skill-research/src/character_skills/equivalence.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/gaps.py | projects/skill-research/src/character_skills/gaps.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/link_skills.py | projects/skill-research/src/character_skills/link_skills.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b10_batch.py | projects/skill-research/src/character_skills/p3b10_batch.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b10_binding_scope.json | projects/skill-research/src/character_skills/p3b10_binding_scope.json | ZCode主线所有者保护；路径签名未适配不得拆 | C05,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b10_bindings.py | projects/skill-research/src/character_skills/p3b10_bindings.py | ZCode主线所有者保护；路径签名未适配不得拆 | C05,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b10_dom.js | projects/skill-research/src/character_skills/p3b10_dom.js | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b2_type8.py | projects/skill-research/src/character_skills/p3b2_type8.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b3_dom.js | projects/skill-research/src/character_skills/p3b3_dom.js | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b3_type26.py | projects/skill-research/src/character_skills/p3b3_type26.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b4_dom.js | projects/skill-research/src/character_skills/p3b4_dom.js | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b4_type9.py | projects/skill-research/src/character_skills/p3b4_type9.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b5_dom.js | projects/skill-research/src/character_skills/p3b5_dom.js | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b5_f1.py | projects/skill-research/src/character_skills/p3b5_f1.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b5_remaining_five.py | projects/skill-research/src/character_skills/p3b5_remaining_five.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b6_batch.py | projects/skill-research/src/character_skills/p3b6_batch.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b6_binding_scope.json | projects/skill-research/src/character_skills/p3b6_binding_scope.json | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b6_dom.js | projects/skill-research/src/character_skills/p3b6_dom.js | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b6_native.py | projects/skill-research/src/character_skills/p3b6_native.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b7_batch.py | projects/skill-research/src/character_skills/p3b7_batch.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b7_binding_scope.json | projects/skill-research/src/character_skills/p3b7_binding_scope.json | ZCode主线所有者保护；路径签名未适配不得拆 | C05,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b7_bindings.py | projects/skill-research/src/character_skills/p3b7_bindings.py | ZCode主线所有者保护；路径签名未适配不得拆 | C05,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b7_dom.js | projects/skill-research/src/character_skills/p3b7_dom.js | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b7_native.py | projects/skill-research/src/character_skills/p3b7_native.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b7_rectification.py | projects/skill-research/src/character_skills/p3b7_rectification.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b8_batch.py | projects/skill-research/src/character_skills/p3b8_batch.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b8_binding_scope.json | projects/skill-research/src/character_skills/p3b8_binding_scope.json | ZCode主线所有者保护；路径签名未适配不得拆 | C05,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b8_bindings.py | projects/skill-research/src/character_skills/p3b8_bindings.py | ZCode主线所有者保护；路径签名未适配不得拆 | C05,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b8_dom.js | projects/skill-research/src/character_skills/p3b8_dom.js | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b8_native.py | projects/skill-research/src/character_skills/p3b8_native.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b9_batch.py | projects/skill-research/src/character_skills/p3b9_batch.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b9_binding_scope.json | projects/skill-research/src/character_skills/p3b9_binding_scope.json | ZCode主线所有者保护；路径签名未适配不得拆 | C05,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b9_bindings.py | projects/skill-research/src/character_skills/p3b9_bindings.py | ZCode主线所有者保护；路径签名未适配不得拆 | C05,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b9_dom.js | projects/skill-research/src/character_skills/p3b9_dom.js | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/p3b9_native.py | projects/skill-research/src/character_skills/p3b9_native.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/profiles.py | projects/skill-research/src/character_skills/profiles.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/query.py | projects/skill-research/src/character_skills/query.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/reconcile_mechanism_first_handoff_20261104.py | projects/skill-research/src/character_skills/reconcile_mechanism_first_handoff_20261104.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/remaining_five.py | projects/skill-research/src/character_skills/remaining_five.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/rules.py | projects/skill-research/src/character_skills/rules.py | ZCode主线所有者保护；路径签名未适配不得拆 | C03,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/run_retention.py | projects/skill-research/src/character_skills/run_retention.py | ZCode主线所有者保护；路径签名未适配不得拆 | C08,C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/scope_diff.py | projects/skill-research/src/character_skills/scope_diff.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/skilllist_types.py | projects/skill-research/src/character_skills/skilllist_types.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/type1082_native.py | projects/skill-research/src/character_skills/type1082_native.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/type1082_probe.py | projects/skill-research/src/character_skills/type1082_probe.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/type1082_snapshot.py | projects/skill-research/src/character_skills/type1082_snapshot.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/type26_mana.py | projects/skill-research/src/character_skills/type26_mana.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/type9_bullet.py | projects/skill-research/src/character_skills/type9_bullet.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| scripts/character_skills/verify_p1.py | projects/skill-research/src/character_skills/verify_p1.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T02,T04 | 不按 card_page 前缀整体划给阅读器；数据计算、事务、审核仍归研究 |
| work/20261020-pilot1017 | work/20261020-pilot1017 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | type1017推断试点、修复对账及旧行快照；历史append_readme会读写正式pages/README.md；旧行快照服务历史比较，不可用当前页替代；限制：未重验历史快照完整性；子项目索引归属：projects/skill-research/history/work/20261020-pilot1017 |
| work/20261021_recheck_rectify | work/20261021_recheck_rectify | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 20261021复审整改、checker反例重放及清单修正；checker读card_page_verify_full源码及定向审查checker_cases；另含Y.G.与分享manifest修正，distribution为跨项目消费者；限制：patch_yg_list与refresh_share_manifest当前可重放性未验；子项目索引归属：projects/skill-research/history/work/20261021_recheck_rectify |
| work/20261022_skill_values_bundle | work/20261022_skill_values_bundle | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/20to39_deepseek_review | work/20to39_deepseek_review | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 20to39 cohort独审及逐行检查现场；读pages、冻结manifest、指定run队列，写独审issues/sample；旧新run不能自动替换为最新campaign；限制：指定历史run载荷完整性未核；子项目索引归属：projects/skill-research/history/work/20to39_deepseek_review |
| work/20to39_fix_20261020 | work/20to39_fix_20261020 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 20to39整改旧行快照与数值零变化证据；读本目录changes_<cohort>.jsonl；old_rows为三cohort冻结前像；限制：历史快照完整性未重验；子项目索引归属：projects/skill-research/history/work/20to39_fix_20261020 |
| work/40to59_deepseek_review | work/40to59_deepseek_review | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 40to59独审及修复复验账本；读指定run、checks和pages，生成独审ledger；旧版复验绑定历史receipt/backup签名；限制：324份历史前像当前可用性未重验；子项目索引归属：projects/skill-research/history/work/40to59_deepseek_review |
| work/40to59_fix_20261020 | work/40to59_fix_20261020 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 40to59/ge60整改的旧状态、差异与队列对账；读cohort latest及独审issues；old_rows/old_state/old_basic为历史比较输入；限制：latest动态变化，今日运行不等于旧版本重放；子项目索引归属：projects/skill-research/history/work/40to59_fix_20261020 |
| work/archive_r1_pages.py | work/archive_r1_pages.py | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 正式R1角色页版本归档脚本；读正式pages并写pages_versions/r1_20261019；manifest里的独审等是历史引用并非脚本实读；不得重跑覆盖冻结归档；子项目索引归属：projects/skill-research/history/work/archive_r1_pages.py |
| work/b14_carriers_probe.json | work/b14_carriers_probe.json | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批14 APK扩域载体名单对照输入；b14_carrier_table实际读取以断言载体集合相等，涉及批8/11/12 hint及2012/1095；限制：probe原始生成命令未定位；子项目索引归属：projects/skill-research/history/work/b14_carriers_probe.json |
| work/b5_review_deepseek | work/b5_review_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批5 type1017跨表扩展独审；链检查读rows、jobabilityinfo、CACHE/APK skill、links/rules；历史复验依赖批前快照；限制：未重跑历史审查；子项目索引归属：projects/skill-research/history/work/b5_review_deepseek |
| work/b8_recheck2_deepseek | work/b8_recheck2_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批8微修最终确认行快照与机器回执；保存签名05b45a0c…批8终态证据，非当前全库输入；与前轮复验分版本保留；限制：未见顶层生产脚本，生成方式依RECHECK2；子项目索引归属：projects/skill-research/history/work/b8_recheck2_deepseek |
| work/b8_recheck_deepseek | work/b8_recheck_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批8微修定向复验行导出与回执；当时页面、原始表和独审的复验版本，不替代RECHECK2；限制：未见顶层生产脚本；未与最终行快照逐字比较；子项目索引归属：projects/skill-research/history/work/b8_recheck_deepseek |
| work/b8_review_deepseek | work/b8_review_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批8暴击2012链独审及零变化重放；读v3 records和APK；历史比较受replay_guard约束，须有旧backup及冻结新版本，缺输入应阻断；限制：未重验guard所需全部历史载荷；子项目索引归属：projects/skill-research/history/work/b8_review_deepseek |
| work/build_yg_unresolved.py | work/build_yg_unresolved.py | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | Y.G.未解项分类与选题生成器；读work/character_skills_yg_priority及ledger/profiles；写output/character_skills/yg_unresolved_20261026；其只读措辞不表示不写文件；子项目索引归属：projects/skill-research/history/work/build_yg_unresolved.py |
| work/c10_p1_20261030 | work/c10_p1_20261030 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C10-P1预检、正式差异辅助与F03前像；读当时正式页及CACHE/APK；f03_previous、formal_diff用于历史比较，不是权威答案入口；子项目索引归属：projects/skill-research/history/work/c10_p1_20261030 |
| work/c10_p1_candidate_20261030_deepseek | work/c10_p1_candidate_20261030_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C10候选独审原始链重导与模拟页账本；模拟页实际引用当前正式pages，非完整冻结副本；保留ledger_oldpages/ledger_sim；新增联接统计不并入上一轮661口径；子项目索引归属：projects/skill-research/history/work/c10_p1_candidate_20261030_deepseek |
| work/c10_p1_final_20261030_deepseek | work/c10_p1_final_20261030_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C10正式独审重算、逆补丁及6卡恢复材料；回退脚本会直接改正式6卡，不执行；pages_backup和patch_reverse为历史前像和恢复材料；子项目索引归属：projects/skill-research/history/work/c10_p1_final_20261030_deepseek |
| work/c11_delivery_20261031 | work/c11_delivery_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c11_delivery_final_review_20261031_deepseek | work/c11_delivery_final_review_20261031_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c11_p1_t114_20261031 | work/c11_p1_t114_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c11_p1_t114_direct_review_20261031 | work/c11_p1_t114_direct_review_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c11_p1_t114_final_review_20261031 | work/c11_p1_t114_final_review_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c11_p1_t114_mirror_20261031 | work/c11_p1_t114_mirror_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c11_p2_t114_yg_20261031 | work/c11_p2_t114_yg_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c11_p2_union_count_20261031 | work/c11_p2_union_count_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c11_p3_strength_job2_20261031 | work/c11_p3_strength_job2_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c12_delivery_20261031 | work/c12_delivery_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c12_p1_sympathy_attack_20261031 | work/c12_p1_sympathy_attack_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c12_p2_sympathy_3005_sub1_20261031 | work/c12_p2_sympathy_3005_sub1_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c12_p3_skilltext_mirror_20261031 | work/c12_p3_skilltext_mirror_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c13_20261031 | work/c13_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c13_delivery_20261031 | work/c13_delivery_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c13_delivery_precheck_review_20261031_deepseek | work/c13_delivery_precheck_review_20261031_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c13_r01_empty_id_20261101 | work/c13_r01_empty_id_20261101 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c13_r01_empty_id_20261101_deepseek | work/c13_r01_empty_id_20261101_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c13_r01_empty_id_closeout | work/c13_r01_empty_id_closeout | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c13_r01_rectification | work/c13_r01_rectification | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c13_r01_rectification_review | work/c13_r01_rectification_review | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c14_20261102 | work/c14_20261102 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c14_delivery_20261103 | work/c14_delivery_20261103 | 工作／恢复材料原位保护 | C21 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c15_20261103 | work/c15_20261103 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c15_delivery_20261103 | work/c15_delivery_20261103 | 工作／恢复材料原位保护 | C21 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c16_delivery_20261104 | work/c16_delivery_20261104 | 工作／恢复材料原位保护 | C21 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c16_p1_1095_partial_20261104 | work/c16_p1_1095_partial_20261104 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c17_delivery_20261106 | work/c17_delivery_20261106 | 工作／恢复材料原位保护 | C21 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c17_p1_1095_attack_partial_20261106 | work/c17_p1_1095_attack_partial_20261106 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c18_delivery_20261106 | work/c18_delivery_20261106 | 工作／恢复材料原位保护 | C21 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c18_delivery_final_20261106 | work/c18_delivery_final_20261106 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c18_p1_1095_attack_partial_20261106 | work/c18_p1_1095_attack_partial_20261106 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/c6_direction_review_20261029 | work/c6_direction_review_20261029 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C6独立方向审查执行源码；读主表、正式pages/ledger及C6前像，写配对review；属历史审查消费者而非生产入口；子项目索引归属：projects/skill-research/history/work/c6_direction_review_20261029 |
| work/c7_p1_formal | work/c7_p1_formal | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7-P1旧码no-op基线与冻结源码隔离输出；比较旧码与冻结源码；_batch属于隔离运行，不能按formal名称判当前生产事务；子项目索引归属：projects/skill-research/history/work/c7_p1_formal |
| work/c7_p1_g1_structure | work/c7_p1_g1_structure | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7-P1 G1结构化准入探索；读正式页/原表、候选及冻结实现，写探索JSON；非权威生产规则；子项目索引归属：projects/skill-research/history/work/c7_p1_g1_structure |
| work/c7_p1_g1_structure_20261029_deepseek | work/c7_p1_g1_structure_20261029_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7-P1候选独审运行前哈希锚点；记录candidates_all、scan_summary、dryrun、cases四项哈希；本目录不是完整审查环境；限制：仅剩哈希记录，不据此宣称全部独审中间件齐备；子项目索引归属：projects/skill-research/history/work/c7_p1_g1_structure_20261029_deepseek |
| work/c7_p1_ledger_opt | work/c7_p1_ledger_opt | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 账本按卡读取复用优化基准与回退链；冻结页输入和旧新性能/等价结果；original_effect_ledger.py及ledger_opt.patch组成恢复链，不用当前页重跑旧基准；子项目索引归属：projects/skill-research/history/work/c7_p1_ledger_opt |
| work/c7_p1_ledger_opt_review | work/c7_p1_ledger_opt_review | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7账本优化独立性能与边界复测；独审旧新实现、输出和异常路径等价；旧实现副本保留，与实施目录分源；子项目索引归属：projects/skill-research/history/work/c7_p1_ledger_opt_review |
| work/c7_p2_20261030 | work/c7_p2_20261030 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7-P2 G7链、denju镜像与G9门控预检；读当时正式页、denju/boss/chara、rules及ledger，写行索引和precheck；非当前答案入口；子项目索引归属：projects/skill-research/history/work/c7_p2_20261030 |
| work/c7_p2_formal | work/c7_p2_formal | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7-P2旧码基线与冻结源码隔离页；oldcode_pages供新增证明消费；独立构建状态不是当前正式事务；子项目索引归属：projects/skill-research/history/work/c7_p2_formal |
| work/c7_p3_20261030 | work/c7_p3_20261030 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7-P3 denju/G1候选门控及原始链重导；原表、正式页及规则门控结果驱动rederive/候选/行索引；本批实施辅助不替代正式模块；子项目索引归属：projects/skill-research/history/work/c7_p3_20261030 |
| work/c7_p3_formal | work/c7_p3_formal | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7-P3旧码基线与冻结源码隔离验收页；oldcode供新增证明/正式差异消费；_batch属隔离构建，保持相对路径；子项目索引归属：projects/skill-research/history/work/c7_p3_formal |
| work/c8_p1_20261030 | work/c8_p1_20261030 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C8-P1预检、差异、旧账本实现及F03前像；subset_pages被独审消费；旧实现/F03为恢复材料；历史清理有6件派生账本因复建不足保留为C类；子项目索引归属：projects/skill-research/history/work/c8_p1_20261030 |
| work/c8_p1_candidate_20261030_deepseek | work/c8_p1_candidate_20261030_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C8候选独审模块与模拟页账本验证；模拟树引用当前正式页而非完整冻结副本；保留ledger_oldpages/ledger_sim；新增联接不并入前轮661口径；子项目索引归属：projects/skill-research/history/work/c8_p1_candidate_20261030_deepseek |
| work/c8_p1_final_20261030_deepseek | work/c8_p1_final_20261030_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C8终审隔离重建、no-op账本及回退复查；依赖C8 pre_rebuild旧页；保留重构/逆补丁账本与B1哈希整改前后证据，不合并覆盖；子项目索引归属：projects/skill-research/history/work/c8_p1_final_20261030_deepseek |
| work/c9_p1_20261030 | work/c9_p1_20261030 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C9-P1候选扫描及正式前像差异；读扫描/账本/rules，保存旧页哈希、A7及retention状态；F03与patchcheck是历史恢复链；子项目索引归属：projects/skill-research/history/work/c9_p1_20261030 |
| work/c9_p1_candidate_20261030_deepseek | work/c9_p1_candidate_20261030_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C9候选独审全扫、原始链及账本预检；读原表/pages/profiles及subset_pages；代码可创建联接，但本轮深度≤5未见实际联接，不能混为一谈；子项目索引归属：projects/skill-research/history/work/c9_p1_candidate_20261030_deepseek |
| work/c9_p1_final_20261030_deepseek | work/c9_p1_final_20261030_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C9终审差异、边界与历史检查记录修复；读旧页/账本与正式态；rebuild_s1会从权威run_record写冻结包scratch，禁止重跑覆盖；子项目索引归属：projects/skill-research/history/work/c9_p1_final_20261030_deepseek |
| work/cc_skill_values_20261022_build | work/cc_skill_values_20261022_build | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_audit_rectify_20261021 | work/character_skills_audit_rectify_20261021 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b10_fix2 | work/character_skills_b10_fix2 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b10_rv_fix | work/character_skills_b10_rv_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b10_sa2003 | work/character_skills_b10_sa2003 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b11_impl_sa1095 | work/character_skills_b11_impl_sa1095 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b11_sa1095 | work/character_skills_b11_sa1095 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b12_1095ext | work/character_skills_b12_1095ext | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b12_review_deepseek | work/character_skills_b12_review_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b13_apkext | work/character_skills_b13_apkext | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b13_fix | work/character_skills_b13_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b13_impl_apkext | work/character_skills_b13_impl_apkext | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b14_audit | work/character_skills_b14_audit | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b14_impl | work/character_skills_b14_impl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b16_audit | work/character_skills_b16_audit | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b17_impl | work/character_skills_b17_impl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b18_audit | work/character_skills_b18_audit | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b3_type8 | work/character_skills_b3_type8 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b4_cond | work/character_skills_b4_cond | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b5_impl | work/character_skills_b5_impl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b5_xtable | work/character_skills_b5_xtable | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b6_bossbuff | work/character_skills_b6_bossbuff | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b6_fix | work/character_skills_b6_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b6_impl | work/character_skills_b6_impl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b7_impl | work/character_skills_b7_impl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b7_sympathy | work/character_skills_b7_sympathy | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b8_crit2012 | work/character_skills_b8_crit2012 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b9_debuff | work/character_skills_b9_debuff | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_b9_fix | work/character_skills_b9_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_card_pages | work/character_skills_card_pages | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_chain_trigger_fix | work/character_skills_chain_trigger_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_display_ratio_20261020 | work/character_skills_display_ratio_20261020 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_doc_debt_fix | work/character_skills_doc_debt_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_f1f2_evidence_20261024 | work/character_skills_f1f2_evidence_20261024 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_f1f2_fix | work/character_skills_f1f2_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_goal_rectification | work/character_skills_goal_rectification | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_index_pages | work/character_skills_index_pages | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_inference_inventory | work/character_skills_inference_inventory | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_layout_migration | work/character_skills_layout_migration | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_n1n2_fix_20261024 | work/character_skills_n1n2_fix_20261024 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_n1n2_selfobj_fix_20261024 | work/character_skills_n1n2_selfobj_fix_20261024 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p1 | work/character_skills_p1 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p2 | work/character_skills_p2 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p2b2 | work/character_skills_p2b2 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p2b2_explore.py | work/character_skills_p2b2_explore.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3 | work/character_skills_p3 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b1 | work/character_skills_p3b1 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b10 | work/character_skills_p3b10 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b2 | work/character_skills_p3b2 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b3 | work/character_skills_p3b3 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b4 | work/character_skills_p3b4 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b5 | work/character_skills_p3b5 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b6 | work/character_skills_p3b6 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b7 | work/character_skills_p3b7 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b8 | work/character_skills_p3b8 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p3b9 | work/character_skills_p3b9 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p4_account.py | work/character_skills_p4_account.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p4_records_before.jsonl | work/character_skills_p4_records_before.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_p4_summary_before.json | work/character_skills_p4_summary_before.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_pages_r02_regression | work/character_skills_pages_r02_regression | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_parallel_cohort | work/character_skills_parallel_cohort | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_phase2_20261021 | work/character_skills_phase2_20261021 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_pivot | work/character_skills_pivot | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_r1 | work/character_skills_r1 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_r2 | work/character_skills_r2 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_r2_prep | work/character_skills_r2_prep | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_r2_review | work/character_skills_r2_review | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_r2_root_fix | work/character_skills_r2_root_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_r3_root_fix | work/character_skills_r3_root_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_r3_sentence_fix | work/character_skills_r3_sentence_fix | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_recheck_rectification | work/character_skills_recheck_rectification | 工作／恢复材料原位保护 | C13 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_rectification_r2r3 | work/character_skills_rectification_r2r3 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_rectify_summary_20261021 | work/character_skills_rectify_summary_20261021 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_review_b9_deepseek | work/character_skills_review_b9_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_type1082 | work/character_skills_type1082 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_yg1_research | work/character_skills_yg1_research | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_yg_coverage | work/character_skills_yg_coverage | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/character_skills_yg_priority | work/character_skills_yg_priority | 工作／恢复材料原位保护 | C11 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/closeout_c11_c12_20261031 | work/closeout_c11_c12_20261031 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/crit_absorb_20261026 | work/crit_absorb_20261026 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 暴击吸收批F03选题流水线前像；保存YG backlog/enriched/candidates、pages/README哈希及分步记录；为恢复与历史比较材料；子项目索引归属：projects/skill-research/history/work/crit_absorb_20261026 |
| work/crit_absorb_isolated_repro_20261026 | work/crit_absorb_isolated_repro_20261026 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 暴击吸收批11卡冻结源码隔离复跑树；以本树声明输入生成JSON/HTML比较；非发行包，也不证明其中所有解包工具可独立运行；子项目索引归属：projects/skill-research/history/work/crit_absorb_isolated_repro_20261026 |
| work/cycle2_deepseek_review | work/cycle2_deepseek_review | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 第二周期整改独立源码规则账本重核；读整改包before_rules、previous_ledger、正式页与原表；审查输出不作为生产规则输入；子项目索引归属：projects/skill-research/history/work/cycle2_deepseek_review |
| work/cycle2_isolated_repro_20261026 | work/cycle2_isolated_repro_20261026 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 第二周期整改16卡隔离复跑树；冻结源码、声明研究输入与代表输出构成历史验收，非当前根或完整发行闭包证明；子项目索引归属：projects/skill-research/history/work/cycle2_isolated_repro_20261026 |
| work/cycle2_rectification_20261026 | work/cycle2_rectification_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/cycle_closeout_c11_c13_20261102 | work/cycle_closeout_c11_c13_20261102 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/cycle_closeout_c14_c15_20261104 | work/cycle_closeout_c14_c15_20261104 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/cycle_closeout_c16_20261106 | work/cycle_closeout_c16_20261106 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/cycle_closeout_c17_c18_20261106 | work/cycle_closeout_c17_c18_20261106 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/cycles3to5_rectification_20261029 | work/cycles3to5_rectification_20261029 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/cycles3to5_rectification_20261029_deepseek | work/cycles3to5_rectification_20261029_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/deepseek_review_20261021 | work/deepseek_review_20261021 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 20261021整改独立定向审查证据；读整改前backup及当前card，写boundary_diff；bc726985旧态是比较前提；限制：历史backup完整性未核；子项目索引归属：projects/skill-research/history/work/deepseek_review_20261021 |
| work/direction_c11_c12_20261031_thirdparty | work/direction_c11_c12_20261031_thirdparty | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/direction_c11_c12_20261031_thirdparty_recheck | work/direction_c11_c12_20261031_thirdparty_recheck | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/direction_c11_c12_20261031_thirdparty_recheck_r2 | work/direction_c11_c12_20261031_thirdparty_recheck_r2 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/direction_c11_c12_20261031_thirdparty_recheck_r3 | work/direction_c11_c12_20261031_thirdparty_recheck_r3 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/direction_c13_20261101_thirdparty | work/direction_c13_20261101_thirdparty | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/direction_c13_20261101_thirdparty_recheck | work/direction_c13_20261101_thirdparty_recheck | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/direction_c13_20261102_thirdparty_empty_id_recheck | work/direction_c13_20261102_thirdparty_empty_id_recheck | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/direction_c7_20261030_codex | work/direction_c7_20261030_codex | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C7三批方向独审增量、原始链及展示核验；读各批前像、正式页/账本及原表，写独审；展示核验服务技能成果，不因此归reader；原裁决与整改复审分开；子项目索引归属：projects/skill-research/history/work/direction_c7_20261030_codex |
| work/direction_c8_c10_20261030_independent | work/direction_c8_c10_20261030_independent | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | C8-C10联合独审与三时点重构；读三批pre_rebuild、代码快照、清单及reconstructed树；保留retention/正式哈希，非当前生产恢复器；子项目索引归属：projects/skill-research/history/work/direction_c8_c10_20261030_independent |
| work/direction_cycles3to5_20261028_independent | work/direction_cycles3to5_20261028_independent | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 周期3-5独立方向审查先行源码和日志；限定配对work/output及正式页输入，记录固定检查和隔离账本；与后续R01/R02整改分源，不覆盖旧裁决；子项目索引归属：projects/skill-research/history/work/direction_cycles3to5_20261028_independent |
| work/final_confirm | work/final_confirm | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | remaining收尾L-04微修四cohort最终确认；读pages、manifest/latest和指定campaign，写metrics；历史对账依赖polish_20261020/old_pages_l04fix；限制：旧页完整性和动态latest匹配未验；子项目索引归属：projects/skill-research/history/work/final_confirm |
| work/final_polish_recheck | work/final_polish_recheck | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/g0_g7b0_20261028 | work/g0_g7b0_20261028 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | G0/G7-B0合批F03前像、旧账本及隔离页；旧账本锚定81362bb9及2236卡；F03为恢复前像，隔离页18个直接子项、深度≤5无联接；子项目索引归属：projects/skill-research/history/work/g0_g7b0_20261028 |
| work/g1_b1_20261029 | work/g1_b1_20261029 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | G1-B1镜像绑定对照、候选草稿和前像；O02及admitted_draft不替代正式admission；保留F03、旧账本和隔离验收关系；子项目索引归属：projects/skill-research/history/work/g1_b1_20261029 |
| work/g1_b1_20261029_deepseek | work/g1_b1_20261029_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | G1-B1独审原始链、来源及保护项核查；读最终admission、原表、pages/rules及配对独审输出；硬编码项目绝对路径，不是通用可移植入口；子项目索引归属：projects/skill-research/history/work/g1_b1_20261029_deepseek |
| work/g7_b1_20261029 | work/g7_b1_20261029 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | G7-B1前像、隔离页与一次性验收补丁；保留F03/旧账本/隔离页；一次性补丁写本批final_diff，不是生产模块，不重跑；隔离页深度≤5无联接；子项目索引归属：projects/skill-research/history/work/g7_b1_20261029 |
| work/ge60_deepseek_recheck | work/ge60_deepseek_recheck | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | ge60首轮修复34卡定向独审复验；读pages、ge60_fix旧卡、原始表与指定队列，写checks_recheck；旧卡须与审查card_sha锚点匹配；限制：34份旧卡哈希未重算；子项目索引归属：projects/skill-research/history/work/ge60_deepseek_recheck |
| work/ge60_deepseek_recheck2 | work/ge60_deepseek_recheck2 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | ge60 polish轮复验及细化证据；读pages、ge60_polish旧卡/变化清单及指定队列；旧receipt和transaction backup是比较约束；限制：旧backup可用性未重验；子项目索引归属：projects/skill-research/history/work/ge60_deepseek_recheck2 |
| work/ge60_deepseek_review | work/ge60_deepseek_review | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | ge60初版独审队列、issues及检查证据；指定run audit_queue、pages及checks驱动独审输出；保留初版REQUEST_CHANGES历史；限制：初版结论不代表当前版本；子项目索引归属：projects/skill-research/history/work/ge60_deepseek_review |
| work/ge60_fix | work/ge60_fix | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | ge60修复旧卡前像及逐行差异；读冻结cohort、old_cards与pages生成row_changes；old_cards被独立RECHECK消费；限制：旧卡完整性未重验；子项目索引归属：projects/skill-research/history/work/ge60_fix |
| work/ge60_polish | work/ge60_polish | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/gold_exp_20261028 | work/gold_exp_20261028 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 金币经验批勘察及批前账本预检；survey读CACHE/APK/pages并写survey.json；final_diff读ledger_precheck作type100/102批前比较；限制：ledger_precheck载荷范围未重核；子项目索引归属：projects/skill-research/history/work/gold_exp_20261028 |
| work/heal_interval_20261028 | work/heal_interval_20261028 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 回复间隔批构建重跑日志与账本前像；final_diff实际读本目录ledger_precheck和指定run旧backup；保存A7/F03/ledger等历史日志；限制：ledger_precheck完整性未核；子项目索引归属：projects/skill-research/history/work/heal_interval_20261028 |
| work/kill_mana_20261029 | work/kill_mana_20261029 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/kill_mana_20261029_deepseek | work/kill_mana_20261029_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/kyoumei_ab_review_20261026 | work/kyoumei_ab_review_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/kyoumei_isolated_repro_20261026 | work/kyoumei_isolated_repro_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/layout_migration_20261020_deepseek | work/layout_migration_20261020_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/mana_b_batch_20261026 | work/mana_b_batch_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/mana_b_isolated_repro_20261026 | work/mana_b_isolated_repro_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/mana_isolated_repro_20261026 | work/mana_isolated_repro_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/mana_ledger_isolated_repro_20261026 | work/mana_ledger_isolated_repro_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/mana_ledger_mapping_20261026 | work/mana_ledger_mapping_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/mechanism_first_handoff_20261104 | work/mechanism_first_handoff_20261104 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p10 | work/p10 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p10_paths | work/p10_paths | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p10_records_before.jsonl | work/p10_records_before.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p10_summary_before.json | work/p10_summary_before.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p4_crit_inc_check.log | work/p4_crit_inc_check.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p4_crosscheck.log | work/p4_crosscheck.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p4_crosscheck2.log | work/p4_crosscheck2.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p4_gaps_rerun.log | work/p4_gaps_rerun.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p4_hash_after.txt | work/p4_hash_after.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p4_hash_before.txt | work/p4_hash_before.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p4_profiles_rerun.log | work/p4_profiles_rerun.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_cc.log | work/p5_cc.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_cc2.log | work/p5_cc2.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_cc3.log | work/p5_cc3.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_final_after.txt | work/p5_final_after.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_final_before.txt | work/p5_final_before.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_gaps.log | work/p5_gaps.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_hash_after.txt | work/p5_hash_after.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_hash_before.txt | work/p5_hash_before.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_insert_composite.py | work/p5_insert_composite.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_patch2.py | work/p5_patch2.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_patch3.py | work/p5_patch3.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_patch_crosscheck.py | work/p5_patch_crosscheck.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_patch_report.py | work/p5_patch_report.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_patch_rules.py | work/p5_patch_rules.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_patch_text.py | work/p5_patch_text.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_patch_verify.py | work/p5_patch_verify.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_profiles.log | work/p5_profiles.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_profiles2.log | work/p5_profiles2.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_records_before.jsonl | work/p5_records_before.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5_summary_before.json | work/p5_summary_before.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_96_before.json | work/p5r_96_before.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_cc.log | work/p5r_cc.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_cc2.log | work/p5r_cc2.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_hash_after.txt | work/p5r_hash_after.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_hash_b2.txt | work/p5r_hash_b2.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_hash_b3.txt | work/p5r_hash_b3.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_hash_before.txt | work/p5r_hash_before.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_patch_checks.py | work/p5r_patch_checks.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_patch_rules.py | work/p5r_patch_rules.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_patch_skilllist.py | work/p5r_patch_skilllist.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p5r_profiles.log | work/p5r_profiles.log | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p6_native | work/p6_native | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p6_records_before.jsonl | work/p6_records_before.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p6_summary_before.json | work/p6_summary_before.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p7_denju | work/p7_denju | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p7_records_before.jsonl | work/p7_records_before.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p7_summary_before.json | work/p7_summary_before.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p8_attacks | work/p8_attacks | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p8_records_before.jsonl | work/p8_records_before.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p8_summary_before.json | work/p8_summary_before.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_a390.txt | work/p9_a390.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_a764.txt | work/p9_a764.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_atv.txt | work/p9_atv.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_atvset.txt | work/p9_atvset.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_before | work/p9_before | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_callers_cp2bs.txt | work/p9_callers_cp2bs.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_callers_skilllist.txt | work/p9_callers_skilllist.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_callers_up.txt | work/p9_callers_up.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_cc.txt | work/p9_cc.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_cc2.txt | work/p9_cc2.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_checkentry.txt | work/p9_checkentry.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_cp_patternlist.txt | work/p9_cp_patternlist.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_createbyid.txt | work/p9_createbyid.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_execskill_callers.txt | work/p9_execskill_callers.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_onclicksp.txt | work/p9_onclicksp.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_paths | work/p9_paths | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_patlist_callers.txt | work/p9_patlist_callers.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_probe1.py | work/p9_probe1.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_probe2.py | work/p9_probe2.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_probe3.py | work/p9_probe3.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_probe4.py | work/p9_probe4.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_probe5.py | work/p9_probe5.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_probe6.py | work/p9_probe6.py | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_q2315.txt | work/p9_q2315.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_records_before.jsonl | work/p9_records_before.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_before_ca_answers.jsonl | work/p9_rect_before_ca_answers.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_before_increment.json | work/p9_rect_before_increment.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_before_records.jsonl | work/p9_rect_before_records.jsonl | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_before_rules.json | work/p9_rect_before_rules.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_cc.txt | work/p9_rect_cc.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_cpinc2.txt | work/p9_rect_cpinc2.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_run_boss_attack_types.txt | work/p9_rect_run_boss_attack_types.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_run_charainfo_params.txt | work/p9_rect_run_charainfo_params.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_run_cp_paths.txt | work/p9_rect_run_cp_paths.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_run_cpinc.txt | work/p9_rect_run_cpinc.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_run_gaps.txt | work/p9_rect_run_gaps.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_run_inc.txt | work/p9_rect_run_inc.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_run_profiles.txt | work/p9_rect_run_profiles.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_v.txt | work/p9_rect_v.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rect_v2.txt | work/p9_rect_v2.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rerun_charainfo_params.txt | work/p9_rerun_charainfo_params.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rerun_gaps.txt | work/p9_rerun_gaps.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rerun_link_skills.txt | work/p9_rerun_link_skills.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rerun_profiles.txt | work/p9_rerun_profiles.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_rerun_scope_diff.txt | work/p9_rerun_scope_diff.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_cap.txt | work/p9_run_cap.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_cc.txt | work/p9_run_cc.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_gaps.txt | work/p9_run_gaps.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_inc.txt | work/p9_run_inc.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_profiles.txt | work/p9_run_profiles.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_verify.txt | work/p9_run_verify.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_verify2.txt | work/p9_run_verify2.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_verify3.txt | work/p9_run_verify3.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_verify4.txt | work/p9_run_verify4.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_verify5.txt | work/p9_run_verify5.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_run_verify6.txt | work/p9_run_verify6.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_setsp_callers.txt | work/p9_setsp_callers.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_shape.txt | work/p9_shape.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_skillsp.txt | work/p9_skillsp.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_summary_before.json | work/p9_summary_before.json | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_tmp_ce1.txt | work/p9_tmp_ce1.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_tmp_ce2.txt | work/p9_tmp_ce2.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_tmp_ce3.txt | work/p9_tmp_ce3.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_tmp_ce4.txt | work/p9_tmp_ce4.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_v7.txt | work/p9_v7.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_x1_diffs.txt | work/p9_x1_diffs.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/p9_x1_text.txt | work/p9_x1_text.txt | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/polish_20261020 | work/polish_20261020 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/rectification_c11_c12_20261031_r2 | work/rectification_c11_c12_20261031_r2 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/remaining_deepseek_review | work/remaining_deepseek_review | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/remaining_fix_r3 | work/remaining_fix_r3 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/remaining_recheck_r4 | work/remaining_recheck_r4 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_b10_sa2003_deepseek | work/review_b10_sa2003_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批10 SA2003独审及两轮复验；读pages及promos/hints/chain_issue生成独审artifacts；历史零变化需对应旧页；限制：未复跑或重裁旧问题；子项目索引归属：projects/skill-research/history/work/review_b10_sa2003_deepseek |
| work/review_b11_deepseek | work/review_b11_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批11 SA1095独审池扫描与问题生成；write_issues写inference_b11_sa1095独审issues；其余为分类池、行差异与入口一致性证据；限制：未完整审读本轮正式REPORT；子项目索引归属：projects/skill-research/history/work/review_b11_deepseek |
| work/review_b13_deepseek | work/review_b13_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批13 APK扩域独审及only-shrink复验；复验实际读CACHE/APK skill；保留278行晋级、规则披露及zero_change历史证据；限制：历史全库比较输入未重验；子项目索引归属：projects/skill-research/history/work/review_b13_deepseek |
| work/review_b14_deepseek | work/review_b14_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批14 crit2012/1095 APK扩域独审；分析读rows_scan/APK；其他检查涉及CACHE/rules/pages和原生窗口，共享镜像是外部前提；限制：全部原生与数据检查未重验；子项目索引归属：projects/skill-research/history/work/review_b14_deepseek |
| work/review_b17_deepseek | work/review_b17_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批17 P0收尾独审和修复复验；读CACHE/APK/rules/pages写审查JSON；zero-change依赖对应旧版前像；限制：全部历史前像未重验；子项目索引归属：projects/skill-research/history/work/review_b17_deepseek |
| work/review_b3_type8_deepseek | work/review_b3_type8_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_b4_cond_deepseek | work/review_b4_cond_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批4句后条件扩展独审与反例；读b4_promotable、pages与原始表，写issues；37行验证绑定当时冻结候选和旧新页；限制：未重跑历史审查；子项目索引归属：projects/skill-research/history/work/review_b4_cond_deepseek |
| work/review_b6_deepseek | work/review_b6_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批6 bossbuff独审与竞争句修复复验；本目录行、promoted/hint/reconcile/metrics驱动独审summary/issues/sample；旧态按批次保留；限制：历史reconcile输入清单未完整核对；子项目索引归属：projects/skill-research/history/work/review_b6_deepseek |
| work/review_b7_deepseek | work/review_b7_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 批7共鸣载体链独审及全库零变化对账；读行导出及CACHE/APK；character_skills_b7_impl/old_rows.jsonl是41665行比较输入；限制：旧行快照完整性未重验；子项目索引归属：projects/skill-research/history/work/review_b7_deepseek |
| work/review_character_skills_p3b1 | work/review_character_skills_p3b1 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b10 | work/review_character_skills_p3b10 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b2 | work/review_character_skills_p3b2 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b3 | work/review_character_skills_p3b3 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b4 | work/review_character_skills_p3b4 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b5 | work/review_character_skills_p3b5 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b6 | work/review_character_skills_p3b6 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b7 | work/review_character_skills_p3b7 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b8 | work/review_character_skills_p3b8 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_character_skills_p3b9 | work/review_character_skills_p3b9 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_direction_20261026_third | work/review_direction_20261026_third | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 技能方向第三方审查预留空工作目录；历史消费者审计可确认管理归属；当前无载荷，不因空而删除；限制：未定位实际执行过的方向审查；空目录不能证明审查完成；子项目索引归属：projects/skill-research/history/work/review_direction_20261026_third |
| work/review_goal_rectification_deepseek | work/review_goal_rectification_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_inference1017_deepseek | work/review_inference1017_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_p2b1 | work/review_p2b1 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第1批charainfo参数及等价性独立复算；自写复算读decoded/APK/roster/charainfo_params；原生overload需共享镜像和metadata；限制：未重新执行等价性或原生复算；子项目索引归属：projects/skill-research/history/work/review_p2b1 |
| work/review_p2b10_thirdparty | work/review_p2b10_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第10批HEAL与尾类型独审及整改复验；读profiles/records与类型产物，部分旧复跑器会写产物；保存p10/crosscheck前像、原生及DOM证据；限制：全部历史前像未重验；子项目索引归属：projects/skill-research/history/work/review_p2b10_thirdparty |
| work/review_p2b2_thirdparty | work/review_p2b2_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第2批类型8/26派发表及数据独立复验；读profiles/records及共享访问层；隔离复跑有独立输出；依赖恢复镜像和metadata；限制：隔离子树全部输入完整性未验；子项目索引归属：projects/skill-research/history/work/review_p2b2_thirdparty |
| work/review_p2b3_thirdparty | work/review_p2b3_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第3批skilllist扩展独审及整改复验；读skilllist_types、rules和原表；t04/t05/t06结果为冻结比较基准，原生复算需共享镜像；限制：冻结审查文件哈希未重算；子项目索引归属：projects/skill-research/history/work/review_p2b3_thirdparty |
| work/review_p2b4_thirdparty | work/review_p2b4_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第4批增量和索引加固独审及隔离复跑；比较自写my_leaves与正式dispatch_map；保留iso_repro、DOM及硬链接事故披露，不能假定隔离副本独立；限制：全部隔离文件物理链接关系未重检；子项目索引归属：projects/skill-research/history/work/review_p2b4_thirdparty |
| work/review_p2b5_thirdparty | work/review_p2b5_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第5批复合分支独审及带联接的隔离复跑；读profiles/原表；iso输入由junction指向正式数据；原生依赖work/protection，别名不算独立副本；限制：本轮未逐一重检9个目标；静态import命中iso不等于实际源文件在那里；子项目索引归属：projects/skill-research/history/work/review_p2b5_thirdparty |
| work/review_p2b6_thirdparty | work/review_p2b6_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第6批条件语义原生数据复算与DOM证据；自写脚本读CACHE/APK/homelist/profiles及原生访问层；保存p6前像、type96及UnionCount证据；限制：p6旧快照未重验；子项目索引归属：projects/skill-research/history/work/review_p2b6_thirdparty |
| work/review_p2b7_thirdparty | work/review_p2b7_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第7批denju传授链及消费者独审；读denju/denju_lblist/bossinfo/charainfo及APK；p7前像、调用方、DOM及全镜像证据依赖共享恢复材料；限制：旧快照和镜像重放条件未重验；子项目索引归属：projects/skill-research/history/work/review_p2b7_thirdparty |
| work/review_p2b8_thirdparty | work/review_p2b8_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第8批攻击boss类型原生数据与DOM独审；读boss/chara/denju、APK、profiles及charainfo_params；DOM读本地page_2052.html；保留p8前像及原生哈希锚点；限制：旧快照和受控执行环境未重验；子项目索引归属：projects/skill-research/history/work/review_p2b8_thirdparty |
| work/review_p2b9_thirdparty | work/review_p2b9_thirdparty | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | P2第9批必杀执行侧及文字修正独审复验；读boss_attack、原生和数据产物；部分入口会写产物，report/gen/crosscheck前像用于副作用核查；限制：未执行有写入副作用的旧入口；子项目索引归属：projects/skill-research/history/work/review_p2b9_thirdparty |
| work/review_r2r3_deepseek | work/review_r2r3_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | R2数值绑定与R3候选归属独审索引及反例；读rectification旧ledger及正式ledger，写idx_old/new；冻结复验证据及ledger_before不可用最新账本替代；限制：旧ledger和冻结证据完整性未全部核验；子项目索引归属：projects/skill-research/history/work/review_r2r3_deepseek |
| work/review_r2r3_root_fix_deepseek | work/review_r2r3_root_fix_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | R2/R3根因修复独审重放与样本；读pages/ledger/backlog/yg_candidates及独立JSON，写审查样本；pre_ledger_snapshot及replay是历史证据；限制：replay载荷与旧账本完整性未重验；子项目索引归属：projects/skill-research/history/work/review_r2r3_root_fix_deepseek |
| work/review_r3_sentence_deepseek | work/review_r3_sentence_deepseek | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | R3句级归属修复独立归因、重放及A7副本；比较before候选与正式候选/enriched；A7调用ledger并读pages；旧候选及独立重放不能由最新队列替代；限制：对应审查根REPORT.md当前不存在；以实际checks、recheck和脚本确认归属，缺失原因未判；子项目索引归属：projects/skill-research/history/work/review_r3_sentence_deepseek |
| work/review_recheck_rectification_deepseek | work/review_recheck_rectification_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/rule_registration_20261028 | work/rule_registration_20261028 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/rule_registration_20261028_deepseek | work/rule_registration_20261028_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/s5_nonterrain_20261026 | work/s5_nonterrain_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/s5_nonterrain_review_20261026 | work/s5_nonterrain_review_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/s5_terrain_20261026 | work/s5_terrain_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/s5_terrain_review_20261026 | work/s5_terrain_review_20261026 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/type67_20261028 | work/type67_20261028 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/type67_20261028_review_deepseek | work/type67_20261028_review_deepseek | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/type80_96_20261028 | work/type80_96_20261028 | 工作／恢复材料原位保护 | 待核 | T02,T04 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| docs/tasks/20261016-char-roster.md | projects/skill-research/docs/tasks/20261016-char-roster.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261016-character-interpretation-plan.md | projects/skill-research/docs/tasks/20261016-character-interpretation-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261017-character-plan-update.md | projects/skill-research/docs/tasks/20261017-character-plan-update.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261017-character-skills-p1.md | projects/skill-research/docs/tasks/20261017-character-skills-p1.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261017-character-skills-p2.md | projects/skill-research/docs/tasks/20261017-character-skills-p2.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261017-character-skills-p2b2.md | projects/skill-research/docs/tasks/20261017-character-skills-p2b2.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261017-character-skills-p3.md | projects/skill-research/docs/tasks/20261017-character-skills-p3.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261017-character-skills-p4.md | projects/skill-research/docs/tasks/20261017-character-skills-p4.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261018-character-skills-p10.md | projects/skill-research/docs/tasks/20261018-character-skills-p10.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261018-character-skills-p5.md | projects/skill-research/docs/tasks/20261018-character-skills-p5.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261018-character-skills-p6.md | projects/skill-research/docs/tasks/20261018-character-skills-p6.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261018-character-skills-p7.md | projects/skill-research/docs/tasks/20261018-character-skills-p7.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261018-character-skills-p8.md | projects/skill-research/docs/tasks/20261018-character-skills-p8.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261018-character-skills-p9.md | projects/skill-research/docs/tasks/20261018-character-skills-p9.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-card-pages.md | projects/skill-research/docs/tasks/20261019-character-skills-card-pages.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-ge60-implement.md | projects/skill-research/docs/tasks/20261019-character-skills-ge60-implement.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b1-type8.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b1-type8.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b10-batch-bindings.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b10-batch-bindings.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b2-type8.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b2-type8.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b3-type26-mana.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b3-type26-mana.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b4-type9.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b4-type9.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b5-remaining-five.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b5-remaining-five.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b6-batch-bindings.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b6-batch-bindings.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b7-batch-bindings.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b7-batch-bindings.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b8-boss-bindings.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b8-boss-bindings.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-p3b9-batch-bindings.md | projects/skill-research/docs/tasks/20261019-character-skills-p3b9-batch-bindings.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-pivot-handoff.md | projects/skill-research/docs/tasks/20261019-character-skills-pivot-handoff.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-pivot.md | projects/skill-research/docs/tasks/20261019-character-skills-pivot.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-r1.md | projects/skill-research/docs/tasks/20261019-character-skills-r1.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-r2-prep.md | projects/skill-research/docs/tasks/20261019-character-skills-r2-prep.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-r2-review.md | projects/skill-research/docs/tasks/20261019-character-skills-r2-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-source-commit.md | projects/skill-research/docs/tasks/20261019-character-skills-source-commit.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261019-character-skills-type1082.md | projects/skill-research/docs/tasks/20261019-character-skills-type1082.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-20to39-implement.md | projects/skill-research/docs/tasks/20261020-character-skills-20to39-implement.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-40to59-implement.md | projects/skill-research/docs/tasks/20261020-character-skills-40to59-implement.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-inference-b3-type8.md | projects/skill-research/docs/tasks/20261020-character-skills-inference-b3-type8.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-inference-b4-cond.md | projects/skill-research/docs/tasks/20261020-character-skills-inference-b4-cond.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-inference-b5-xtable.md | projects/skill-research/docs/tasks/20261020-character-skills-inference-b5-xtable.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-inference-b6-bossbuff.md | projects/skill-research/docs/tasks/20261020-character-skills-inference-b6-bossbuff.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-inference-b7-sympathy.md | projects/skill-research/docs/tasks/20261020-character-skills-inference-b7-sympathy.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-inference-inventory.md | projects/skill-research/docs/tasks/20261020-character-skills-inference-inventory.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-inference-pilot1017.md | projects/skill-research/docs/tasks/20261020-character-skills-inference-pilot1017.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-polish-implement.md | projects/skill-research/docs/tasks/20261020-character-skills-polish-implement.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-remaining-implement.md | projects/skill-research/docs/tasks/20261020-character-skills-remaining-implement.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-yg-coverage.md | projects/skill-research/docs/tasks/20261020-character-skills-yg-coverage.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261021-character-skills-audit-rectify.md | projects/skill-research/docs/tasks/20261021-character-skills-audit-rectify.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261021-character-skills-inference-b8-crit2012.md | projects/skill-research/docs/tasks/20261021-character-skills-inference-b8-crit2012.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261021-character-skills-inference-b9-debuff.md | projects/skill-research/docs/tasks/20261021-character-skills-inference-b9-debuff.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261021-character-skills-yg-priority.md | projects/skill-research/docs/tasks/20261021-character-skills-yg-priority.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261021-review-prompt.md | projects/skill-research/docs/tasks/20261021-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261022-character-skills-goal-rectification-prompt.md | projects/skill-research/docs/tasks/20261022-character-skills-goal-rectification-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261022-character-skills-goal-rectification.md | projects/skill-research/docs/tasks/20261022-character-skills-goal-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261022-character-skills-inference-b10-sa2003.md | projects/skill-research/docs/tasks/20261022-character-skills-inference-b10-sa2003.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261022-character-skills-inference-b11-sa1095.md | projects/skill-research/docs/tasks/20261022-character-skills-inference-b11-sa1095.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261022-character-skills-inference-b12-1095ext.md | projects/skill-research/docs/tasks/20261022-character-skills-inference-b12-1095ext.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261022-character-skills-inference-b13-apkext.md | projects/skill-research/docs/tasks/20261022-character-skills-inference-b13-apkext.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261022-character-skills-inference-b14-apkext.md | projects/skill-research/docs/tasks/20261022-character-skills-inference-b14-apkext.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261022-third-party-review-prompt.md | projects/skill-research/docs/tasks/20261022-third-party-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-character-skills-b17-p0finale.md | projects/skill-research/docs/tasks/20261023-character-skills-b17-p0finale.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-character-skills-parallel-cohort.md | projects/skill-research/docs/tasks/20261023-character-skills-parallel-cohort.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-character-skills-r2r3-root-fix.md | projects/skill-research/docs/tasks/20261023-character-skills-r2r3-root-fix.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-character-skills-recheck-rectification.md | projects/skill-research/docs/tasks/20261023-character-skills-recheck-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-character-skills-rectification-r2r3.md | projects/skill-research/docs/tasks/20261023-character-skills-rectification-r2r3.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-rectification-cost-analysis-prompt.md | projects/skill-research/docs/tasks/20261023-rectification-cost-analysis-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-attack-interval-batch1.md | projects/skill-research/docs/tasks/20261024-attack-interval-batch1.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-attack-interval-preparation.md | projects/skill-research/docs/tasks/20261024-attack-interval-preparation.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-astra-takeover.md | projects/skill-research/docs/tasks/20261024-character-skills-astra-takeover.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-chain-trigger-fix.md | projects/skill-research/docs/tasks/20261024-character-skills-chain-trigger-fix.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-evidence-completion.md | projects/skill-research/docs/tasks/20261024-character-skills-evidence-completion.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-f1f2-fix.md | projects/skill-research/docs/tasks/20261024-character-skills-f1f2-fix.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-n1n2-fix.md | projects/skill-research/docs/tasks/20261024-character-skills-n1n2-fix.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-n1n2-selfobj-fix.md | projects/skill-research/docs/tasks/20261024-character-skills-n1n2-selfobj-fix.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-r3-sentence-fix.md | projects/skill-research/docs/tasks/20261024-character-skills-r3-sentence-fix.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-yg1-batch1.md | projects/skill-research/docs/tasks/20261024-character-skills-yg1-batch1.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-yg1-batch2.md | projects/skill-research/docs/tasks/20261024-character-skills-yg1-batch2.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-yg1-batch3-plan.md | projects/skill-research/docs/tasks/20261024-character-skills-yg1-batch3-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-yg1-batch3.md | projects/skill-research/docs/tasks/20261024-character-skills-yg1-batch3.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-r3-sentence-review-confirmation-prompt.md | projects/skill-research/docs/tasks/20261024-r3-sentence-review-confirmation-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-attack-interval-batch2-plan.md | projects/skill-research/docs/tasks/20261025-attack-interval-batch2-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-attack-interval-batch2.md | projects/skill-research/docs/tasks/20261025-attack-interval-batch2.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-attack-interval-batch3-plan.md | projects/skill-research/docs/tasks/20261025-attack-interval-batch3-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-attack-interval-batch3.md | projects/skill-research/docs/tasks/20261025-attack-interval-batch3.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-character-skills-b18.md | projects/skill-research/docs/tasks/20261025-character-skills-b18.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-character-skills-kyoumei-ab.md | projects/skill-research/docs/tasks/20261025-character-skills-kyoumei-ab.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-character-skills-mana-batch.md | projects/skill-research/docs/tasks/20261025-character-skills-mana-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-condition-coverage-probe.md | projects/skill-research/docs/tasks/20261025-condition-coverage-probe.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-external-review-reply-prompt.md | projects/skill-research/docs/tasks/20261025-external-review-reply-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-host-review-closeout.md | projects/skill-research/docs/tasks/20261025-host-review-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-host-transition.md | projects/skill-research/docs/tasks/20261025-host-transition.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-mainline-autopilot-plan.md | projects/skill-research/docs/tasks/20261025-mainline-autopilot-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-mana-readonly-audit.md | projects/skill-research/docs/tasks/20261025-mana-readonly-audit.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-yg1-remaining-ab-batch1.md | projects/skill-research/docs/tasks/20261025-yg1-remaining-ab-batch1.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-yg1-remaining-ab-plan.md | projects/skill-research/docs/tasks/20261025-yg1-remaining-ab-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-chain-precheck.md | projects/skill-research/docs/tasks/20261026-chain-precheck.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-crit-absorb-batch.md | projects/skill-research/docs/tasks/20261026-crit-absorb-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-cycle2-rectification.md | projects/skill-research/docs/tasks/20261026-cycle2-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-g0-g1-g7-precheck.md | projects/skill-research/docs/tasks/20261026-g0-g1-g7-precheck.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-mana-b-audit.md | projects/skill-research/docs/tasks/20261026-mana-b-audit.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-mana-b-batch.md | projects/skill-research/docs/tasks/20261026-mana-b-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-mana-ledger-mapping.md | projects/skill-research/docs/tasks/20261026-mana-ledger-mapping.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-s5-nonterrain-batch.md | projects/skill-research/docs/tasks/20261026-s5-nonterrain-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-s5-terrain-batch.md | projects/skill-research/docs/tasks/20261026-s5-terrain-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-third-party-direction-review-prompt.md | projects/skill-research/docs/tasks/20261026-third-party-direction-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-yg-alternative-precheck.md | projects/skill-research/docs/tasks/20261026-yg-alternative-precheck.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261027-third-party-direction-review-prompt.md | projects/skill-research/docs/tasks/20261027-third-party-direction-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261028-cycle4-review-closeout.md | projects/skill-research/docs/tasks/20261028-cycle4-review-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261028-cycle5-review-closeout.md | projects/skill-research/docs/tasks/20261028-cycle5-review-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261028-g0-g7b0-batch.md | projects/skill-research/docs/tasks/20261028-g0-g7b0-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261028-rule-registration-batch.md | projects/skill-research/docs/tasks/20261028-rule-registration-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261028-type100-102-batch.md | projects/skill-research/docs/tasks/20261028-type100-102-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261028-type19-1033-batch.md | projects/skill-research/docs/tasks/20261028-type19-1033-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261028-type67-batch.md | projects/skill-research/docs/tasks/20261028-type67-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261028-type80-96-batch.md | projects/skill-research/docs/tasks/20261028-type80-96-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-c6-review-closeout.md | projects/skill-research/docs/tasks/20261029-c6-review-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-c7-p1-host-rectification-prompt.md | projects/skill-research/docs/tasks/20261029-c7-p1-host-rectification-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-c7-p1-throughput-independent-report.md | projects/skill-research/docs/tasks/20261029-c7-p1-throughput-independent-report.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-c7-p1-throughput-package.md | projects/skill-research/docs/tasks/20261029-c7-p1-throughput-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-cycles3to5-r01-r02-rectification.md | projects/skill-research/docs/tasks/20261029-cycles3to5-r01-r02-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-g1-b1-mirror-batch.md | projects/skill-research/docs/tasks/20261029-g1-b1-mirror-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-g7-b1-first-segment-batch.md | projects/skill-research/docs/tasks/20261029-g7-b1-first-segment-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-kill-mana-batch.md | projects/skill-research/docs/tasks/20261029-kill-mana-batch.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-mainline-throughput-plan.md | projects/skill-research/docs/tasks/20261029-mainline-throughput-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-next-cycle-yield-precheck.md | projects/skill-research/docs/tasks/20261029-next-cycle-yield-precheck.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261029-progress-audit.md | projects/skill-research/docs/tasks/20261029-progress-audit.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261030-c10-p1-throughput-package.md | projects/skill-research/docs/tasks/20261030-c10-p1-throughput-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261030-c7-p2-throughput-package.md | projects/skill-research/docs/tasks/20261030-c7-p2-throughput-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261030-c7-p3-throughput-package.md | projects/skill-research/docs/tasks/20261030-c7-p3-throughput-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261030-c7-r1-r2-display-rectification.md | projects/skill-research/docs/tasks/20261030-c7-r1-r2-display-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261030-c8-c10-independent-review-closeout.md | projects/skill-research/docs/tasks/20261030-c8-c10-independent-review-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261030-c8-p1-b1-hash-rectification.md | projects/skill-research/docs/tasks/20261030-c8-p1-b1-hash-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261030-c8-p1-throughput-package.md | projects/skill-research/docs/tasks/20261030-c8-p1-throughput-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261030-c9-p1-throughput-package.md | projects/skill-research/docs/tasks/20261030-c9-p1-throughput-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-c12-direction-review-closeout.md | projects/skill-research/docs/tasks/20261031-c11-c12-direction-review-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-c12-direction-review-rectification-r2.md | projects/skill-research/docs/tasks/20261031-c11-c12-direction-review-rectification-r2.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-c12-direction-review-rectification.md | projects/skill-research/docs/tasks/20261031-c11-c12-direction-review-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-c13-three-cycle-plan.md | projects/skill-research/docs/tasks/20261031-c11-c13-three-cycle-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-delivery-package.md | projects/skill-research/docs/tasks/20261031-c11-delivery-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-delivery-review.md | projects/skill-research/docs/tasks/20261031-c11-delivery-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p1-t114-direct-review.md | projects/skill-research/docs/tasks/20261031-c11-p1-t114-direct-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p1-t114-direct.md | projects/skill-research/docs/tasks/20261031-c11-p1-t114-direct.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p1-t114-final-review.md | projects/skill-research/docs/tasks/20261031-c11-p1-t114-final-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p1-t114-mirror.md | projects/skill-research/docs/tasks/20261031-c11-p1-t114-mirror.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p2-t114-yg-expansion.md | projects/skill-research/docs/tasks/20261031-c11-p2-t114-yg-expansion.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p2-t114-yg-review.md | projects/skill-research/docs/tasks/20261031-c11-p2-t114-yg-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p2-union-count-review.md | projects/skill-research/docs/tasks/20261031-c11-p2-union-count-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p2-union-count.md | projects/skill-research/docs/tasks/20261031-c11-p2-union-count.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p3-strength-job2-review.md | projects/skill-research/docs/tasks/20261031-c11-p3-strength-job2-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c11-p3-strength-job2.md | projects/skill-research/docs/tasks/20261031-c11-p3-strength-job2.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c12-delivery-package.md | projects/skill-research/docs/tasks/20261031-c12-delivery-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c12-delivery-review.md | projects/skill-research/docs/tasks/20261031-c12-delivery-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c12-p1-sympathy-attack-review.md | projects/skill-research/docs/tasks/20261031-c12-p1-sympathy-attack-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c12-p1-sympathy-attack.md | projects/skill-research/docs/tasks/20261031-c12-p1-sympathy-attack.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c12-p2-sympathy-3005-sub1-review.md | projects/skill-research/docs/tasks/20261031-c12-p2-sympathy-3005-sub1-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c12-p2-sympathy-3005-sub1.md | projects/skill-research/docs/tasks/20261031-c12-p2-sympathy-3005-sub1.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c12-p3-skilltext-mirror-review.md | projects/skill-research/docs/tasks/20261031-c12-p3-skilltext-mirror-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c12-p3-skilltext-mirror.md | projects/skill-research/docs/tasks/20261031-c12-p3-skilltext-mirror.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c13-cycle-closeout.md | projects/skill-research/docs/tasks/20261031-c13-cycle-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c13-cycle.md | projects/skill-research/docs/tasks/20261031-c13-cycle.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c13-delivery-package.md | projects/skill-research/docs/tasks/20261031-c13-delivery-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c13-delivery-review.md | projects/skill-research/docs/tasks/20261031-c13-delivery-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c13-p1-supporterskill-type8.md | projects/skill-research/docs/tasks/20261031-c13-p1-supporterskill-type8.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c13-p2-t27-skilltext-mirror.md | projects/skill-research/docs/tasks/20261031-c13-p2-t27-skilltext-mirror.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c13-p3-2012-duration-mirror.md | projects/skill-research/docs/tasks/20261031-c13-p3-2012-duration-mirror.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261101-c13-r01-empty-id-rectification.md | projects/skill-research/docs/tasks/20261101-c13-r01-empty-id-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261101-c13-r01-rectification.md | projects/skill-research/docs/tasks/20261101-c13-r01-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261102-c13-r01-empty-id-closeout.md | projects/skill-research/docs/tasks/20261102-c13-r01-empty-id-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261102-c14-cycle.md | projects/skill-research/docs/tasks/20261102-c14-cycle.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261102-c14-p1-2003-enemy-debuff.md | projects/skill-research/docs/tasks/20261102-c14-p1-2003-enemy-debuff.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261102-c14-p2-boss-damage-direct.md | projects/skill-research/docs/tasks/20261102-c14-p2-boss-damage-direct.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261103-c14-cycle-closeout.md | projects/skill-research/docs/tasks/20261103-c14-cycle-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261103-c14-delivery-package.md | projects/skill-research/docs/tasks/20261103-c14-delivery-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261103-c15-cycle.md | projects/skill-research/docs/tasks/20261103-c15-cycle.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261103-c15-delivery-package.md | projects/skill-research/docs/tasks/20261103-c15-delivery-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261103-c15-p1-denju-damage-direct.md | projects/skill-research/docs/tasks/20261103-c15-p1-denju-damage-direct.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261103-skill-route-experiments.md | projects/skill-research/docs/tasks/20261103-skill-route-experiments.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c15-cycle-closeout.md | projects/skill-research/docs/tasks/20261104-c15-cycle-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c15-direction-review-prompt.md | projects/skill-research/docs/tasks/20261104-c15-direction-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c15-r01-default-reading-rectification.md | projects/skill-research/docs/tasks/20261104-c15-r01-default-reading-rectification.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c15-r01-recheck-closeout.md | projects/skill-research/docs/tasks/20261104-c15-r01-recheck-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c15-r01-recheck-prompt.md | projects/skill-research/docs/tasks/20261104-c15-r01-recheck-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c16-cycle-closeout.md | projects/skill-research/docs/tasks/20261104-c16-cycle-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c16-cycle.md | projects/skill-research/docs/tasks/20261104-c16-cycle.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c16-delivery-package.md | projects/skill-research/docs/tasks/20261104-c16-delivery-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c16-direction-review-prompt.md | projects/skill-research/docs/tasks/20261104-c16-direction-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c16-p1-1095-partial-binding.md | projects/skill-research/docs/tasks/20261104-c16-p1-1095-partial-binding.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-mechanism-first-execution.md | projects/skill-research/docs/tasks/20261104-mechanism-first-execution.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-mechanism-first-handoff.md | projects/skill-research/docs/tasks/20261104-mechanism-first-handoff.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-mechanism-first-host-prompt.md | projects/skill-research/docs/tasks/20261104-mechanism-first-host-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-mechanism-first-next-batch-plan.md | projects/skill-research/docs/tasks/20261104-mechanism-first-next-batch-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-mechanism-first-reconciliation.md | projects/skill-research/docs/tasks/20261104-mechanism-first-reconciliation.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-mechanism-parallel-controlled.md | projects/skill-research/docs/tasks/20261104-mechanism-parallel-controlled.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-mechanism-scale-trial.md | projects/skill-research/docs/tasks/20261104-mechanism-scale-trial.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c17-c18-direction-review-prompt.md | projects/skill-research/docs/tasks/20261106-c17-c18-direction-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c17-c18-thirdparty-closeout.md | projects/skill-research/docs/tasks/20261106-c17-c18-thirdparty-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c17-cycle-closeout.md | projects/skill-research/docs/tasks/20261106-c17-cycle-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c17-cycle.md | projects/skill-research/docs/tasks/20261106-c17-cycle.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c17-delivery-package.md | projects/skill-research/docs/tasks/20261106-c17-delivery-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c17-direction-review-prompt.md | projects/skill-research/docs/tasks/20261106-c17-direction-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c17-p1-1095-attack-partial.md | projects/skill-research/docs/tasks/20261106-c17-p1-1095-attack-partial.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c18-cycle-closeout.md | projects/skill-research/docs/tasks/20261106-c18-cycle-closeout.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c18-cycle.md | projects/skill-research/docs/tasks/20261106-c18-cycle.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c18-delivery-package.md | projects/skill-research/docs/tasks/20261106-c18-delivery-package.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c18-p1-1095-attack-partial.md | projects/skill-research/docs/tasks/20261106-c18-p1-1095-attack-partial.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c19-direction-assessment.md | projects/skill-research/docs/tasks/20261106-c19-direction-assessment.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/character-skills-progress.md | docs/tasks/character-skills-progress.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T04 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| output/character_skills/review/independent_20261020_codex_audit/coverage_refined.json | output/character_skills/review/independent_20261020_codex_audit/coverage_refined.json | 冻结原件原位；子项目建立索引入口 | C04,C11,C12 | T02 | 冻结研究输入，被选题流水线真实读取；子项目索引归属：projects/skill-research/contracts/coverage_refined.json |
| work/c14_delivery_20261103/impl/isolation_input/scripts | work/c14_delivery_20261103/impl/isolation_input/scripts | 工作／恢复材料原位保护 | C21 | T01,T02 | Windows目录联接到根scripts，非独立冻结代码副本 |
| work/c15_delivery_20261103/impl/isolation_input/scripts | work/c15_delivery_20261103/impl/isolation_input/scripts | 工作／恢复材料原位保护 | C21 | T01,T02 | Windows目录联接到根scripts，非独立冻结代码副本 |
| work/c16_delivery_20261104/impl/isolation_input/scripts | work/c16_delivery_20261104/impl/isolation_input/scripts | 工作／恢复材料原位保护 | C21 | T01,T02 | Windows目录联接到根scripts，非独立冻结代码副本 |
| work/c17_delivery_20261106/impl/isolation_input/scripts | work/c17_delivery_20261106/impl/isolation_input/scripts | 工作／恢复材料原位保护 | C21 | T01,T02 | Windows目录联接到根scripts，非独立冻结代码副本 |
| work/c18_delivery_20261106/impl/isolation_input/scripts | work/c18_delivery_20261106/impl/isolation_input/scripts | 工作／恢复材料原位保护 | C21 | T01,T02 | Windows目录联接到根scripts，非独立冻结代码副本 |

## 角色阅读器

| 现有路径 | 拟定目标或保留位置 | 物理处置 | 契约 | 在途任务 | 说明 |
|---|---|---|---|---|---|
| 角色数据库预览.html | projects/reader/previews/ui_reading_preview_20261025/角色数据库预览.html | 保持原位，后续仅在具体迁移任务中实施 | C17 | T01,T03 | 根快捷入口需保留兼容或更新指向 |
| output/character_skills/dbstyle_samples | projects/reader/previews/dbstyle_samples | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T03 | 当前原型可能读取旧样稿代码和文案，不能单独搬旧样稿 |
| output/character_skills/reader_preview_20261106 | projects/reader/previews/reader_preview_20261106 | 保持原位，后续仅在具体迁移任务中实施 | C15 | T01,T03 | 当前原型可能读取旧样稿代码和文案，不能单独搬旧样稿 |
| output/character_skills/ui_reading_preview_20261025 | projects/reader/previews/ui_reading_preview_20261025 | 保持原位，后续仅在具体迁移任务中实施 | C14 | T01,T03 | 当前原型可能读取旧样稿代码和文案，不能单独搬旧样稿 |
| scripts/skill_reader_preview | projects/reader/src/skill_reader_preview | 在途生产者／消费者共同保护 | C10,C14,C15,C17 | T01,T03 | 同级 import 与固定根目录深度需要核对；具体子行优先 |
| scripts/character_skills/card_page_dbstyle_sample.py | projects/reader/src/character_skills/card_page_dbstyle_sample.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T01,T02 | 纯渲染候选仍有同级依赖；批量生成、card_page_data、验证、写入与 retention 先随研究维护 |
| scripts/character_skills/card_page_index.py | projects/reader/src/character_skills/card_page_index.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09,C17 | T01,T02 | 纯渲染候选仍有同级依赖；批量生成、card_page_data、验证、写入与 retention 先随研究维护 |
| scripts/character_skills/card_page_render.py | projects/reader/src/character_skills/card_page_render.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09 | T01,T02 | 纯渲染候选仍有同级依赖；批量生成、card_page_data、验证、写入与 retention 先随研究维护 |
| scripts/character_skills/card_page_render_v2.py | projects/reader/src/character_skills/card_page_render_v2.py | ZCode主线所有者保护；路径签名未适配不得拆 | C09,C16,C17 | T01,T02 | 纯渲染候选仍有同级依赖；批量生成、card_page_data、验证、写入与 retention 先随研究维护 |
| work/dbstyle_v3_check | work/dbstyle_v3_check | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 第三轮角色展示样稿校验；读pages、dbstyle_samples、full_unpack/objects，输出stdout；目录仅检查脚本、无联接；历史通过不代替当前验收；子项目索引归属：projects/reader/history/work/dbstyle_v3_check |
| work/dbstyle_v4_legend | work/dbstyle_v4_legend | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 第四轮图例校验与三卡前像；读dbstyle_samples和本目录before，无写页面；before为冻结显示基准而非缓存；子项目索引归属：projects/reader/history/work/dbstyle_v4_legend |
| docs/tasks/20261020-character-skills-dbstyle-samples.md | projects/reader/docs/tasks/20261020-character-skills-dbstyle-samples.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T03 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-index-pages.md | projects/reader/docs/tasks/20261020-character-skills-index-pages.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T03 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261020-character-skills-layout-migration.md | projects/reader/docs/tasks/20261020-character-skills-layout-migration.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T03 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-ui-reading-preview.md | projects/reader/docs/tasks/20261025-ui-reading-preview.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T03 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-character-skills-reader-prototype.md | projects/reader/docs/tasks/20261106-character-skills-reader-prototype.md | 原任务所有者保护 | 待核 | T01,T03 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-character-skills-ui-research.md | projects/reader/docs/tasks/20261106-character-skills-ui-research.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T03 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| output/character_skills/ui_reading_preview_20261025/build_preview.py | output/character_skills/ui_reading_preview_20261025/build_preview.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T01,T03 | 旧样稿生成器；默认全库不执行，sample直接读取其既有copy/facts数据 |
| docs/tasks/20261106-character-skills-reader-full.md | projects/reader/docs/tasks/20261106-character-skills-reader-full.md | 原任务所有者保护 | C15 | T01 | 全库在途任务卡，当前写入范围以此为准 |
| output/character_skills/reader_full_20261106 | projects/reader/site | 在途生产者／消费者共同保护 | C14,C15 | T01 | 全库在途输出，含作为构建输入的audit/reference_pairs；当前../pages/art布局不可独立移动 |
| output/character_skills/reader_full_20261106/audit/reference_pairs.json | projects/reader/data/reference_pairs.json | 在途生产者／消费者共同保护 | C14,C15 | T01 | 翻译桥接必需前置输入，不能按audit目录名当临时报告 |
| output/character_skills/reader_semantic_20261107 | output/character_skills/reader_semantic_20261107 | 阅读器在途所有者保护；不接管写入 | 逐项证据 | T01 | 在途全库逐句语义审查输入快照、分片及结果；包含manifest、rows、units、packets和results；输入存句式ID、原文、当前中文、card.json来源和上下文，结果存同ID译文及verdict；不是可丢缓存；限制：已有结果分片不代表审查完成；未独立确认聊天ID；子项目索引归属：projects/reader/review/reader_semantic_20261107 |
| docs/tasks/20261107-reader-semantic-review.md | docs/tasks/20261107-reader-semantic-review.md | 阅读器在途所有者保护；不接管写入 | 逐项证据 | T01 | 全库逐句语义复核与目录分页在途任务卡；卡片声明写阅读器脚本、reader_full、reader_semantic及自身任务卡；正式pages/rules/ledger和参考只读；frontend与语义分片分工；旧全库卡更新为程序验收完成、语义精校未完成；限制：负责人仅写本聊天；T01关联属本地证据推断；子项目索引归属：projects/reader/docs/tasks/20261107-reader-semantic-review.md |

## 参考资料分析

| 现有路径 | 拟定目标或保留位置 | 物理处置 | 契约 | 在途任务 | 说明 |
|---|---|---|---|---|---|
| 其他人的参考 | 其他人的参考 | 保持原位，后续仅在具体迁移任务中实施 | C14 | T01,T05 | 只登记逻辑归属，不搬参考原件 |
| output/reference_analysis | projects/reference-analysis/reports | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| scripts/ref_analysis_claude_cc.py | projects/reference-analysis/src/ref_analysis_claude_cc.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ref_analysis_claude_cc_20261023.py | projects/reference-analysis/src/ref_analysis_claude_cc_20261023.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ref_analysis_lead_reconcile_20261023.py | projects/reference-analysis/src/ref_analysis_lead_reconcile_20261023.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 迁移前核对 import、默认路径和外部调用 |
| scripts/ref_ui_audit_20261023.py | projects/reference-analysis/src/ref_ui_audit_20261023.py | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 迁移前核对 import、默认路径和外部调用 |
| scripts/refcheck_20261023_lead | projects/reference-analysis/src/refcheck_20261023_lead | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 同级 import 与固定根目录深度需要核对；具体子行优先 |
| raw/external_reference | raw/external_reference | 原件原位保护 | 待核 | T01,T05 | 不复制或搬迁；由各子项目配置引用 |
| 其他人的参考/CC解包数据_给GPT_20261024 | 其他人的参考/CC解包数据_给GPT_20261024 | 原件原位保护 | 待核 | T01,T05 | 不复制或搬迁；由各子项目配置引用 |
| 其他人的参考/CC解包数据_给GPT_20261027 | 其他人的参考/CC解包数据_给GPT_20261027 | 原件原位保护 | C14 | T01,T05 | 不复制或搬迁；由各子项目配置引用 |
| 其他人的参考/claude_cc_site_pages | 其他人的参考/claude_cc_site_pages | 原件原位保护 | 待核 | T01,T05 | 不复制或搬迁；由各子项目配置引用 |
| 其他人的参考/claude_cc_site_pages 20261023 | 其他人的参考/claude_cc_site_pages 20261023 | 原件原位保护 | 待核 | T01,T05 | 不复制或搬迁；由各子项目配置引用 |
| 其他人的参考/claude_cc_site_pages_给GPT_20261023 | 其他人的参考/claude_cc_site_pages_给GPT_20261023 | 原件原位保护 | 待核 | T01,T05 | 不复制或搬迁；由各子项目配置引用 |
| 其他人的参考/数据库-《Y.G.1515》光耀の騎士 カイン.png | 其他人的参考/数据库-《Y.G.1515》光耀の騎士 カイン.png | 原件原位保护 | 待核 | T01,T05 | 不复制或搬迁；由各子项目配置引用 |
| 其他人的参考/给GPT_请先读我 20261024 v2.md | 其他人的参考/给GPT_请先读我 20261024 v2.md | 原件原位保护 | 待核 | T01,T05 | 不复制或搬迁；由各子项目配置引用 |
| work/refcheck_20261023_lead | work/refcheck_20261023_lead | 工作／恢复材料原位保护 | 待核 | T05 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/reference_analysis_20261023 | work/reference_analysis_20261023 | 工作／恢复材料原位保护 | 待核 | T05 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review_external | work/review_external | 工作／恢复材料原位保护 | 待核 | T05 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| docs/tasks/20261017-reference-analysis.md | projects/reference-analysis/docs/tasks/20261017-reference-analysis.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-reference-analysis.md | projects/reference-analysis/docs/tasks/20261023-reference-analysis.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-reference-check-lead.md | projects/reference-analysis/docs/tasks/20261023-reference-check-lead.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-reference-ui-review.md | projects/reference-analysis/docs/tasks/20261023-reference-ui-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-new-reference-package-review.md | projects/reference-analysis/docs/tasks/20261024-new-reference-package-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-reference-host-handoff.md | projects/reference-analysis/docs/tasks/20261024-reference-host-handoff.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-reference-v2-host-analysis.md | projects/reference-analysis/docs/tasks/20261024-reference-v2-host-analysis.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-referenced-runs-audit.md | projects/reference-analysis/docs/tasks/20261024-referenced-runs-audit.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |

## 工具与成果发行

| 现有路径 | 拟定目标或保留位置 | 物理处置 | 契约 | 在途任务 | 说明 |
|---|---|---|---|---|---|
| output/20261016-reproducibility-audit | projects/distribution/reports/20261016-reproducibility-audit | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T05 | 保持内部结构；检查活跃消费者与历史引用后才可迁移 |
| output/share_bundle | output/share_bundle | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 保持内部结构；检查活跃消费者与历史引用后才可迁移；子项目索引归属：projects/distribution/releases |
| output/character_skills/share_manifest_20261021 | projects/distribution/manifests/share_manifest_20261021 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T05 | 保持历史白名单原意，下一版另建清单 |
| scripts/release | projects/distribution/src/release | 保持原位，后续仅在具体迁移任务中实施 | C10,C16,C18 | T02,T05 | 同级 import 与固定根目录深度需要核对；具体子行优先 |
| work/delivery_20261016 | work/delivery_20261016 | 工作／恢复材料原位保护 | 待核 | T06 | 已识别为发行隔离复现历史，保留原位及来源身份 |
| work/repro_20261016 | work/repro_20261016 | 工作／恢复材料原位保护 | 待核 | T02,T05 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/review2_20261016 | work/review2_20261016 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 独立可复现性交付复审工作材料；解包为被审功能，主职责为发行独立复现；cleanup_20261023.py按该路径识别治理范围；不补造已清理载荷；限制：未穷尽所有剩余产物内容及动态消费者；子项目索引归属：projects/distribution/history/work/review2_20261016 |
| work/review_20261016 | work/review_20261016 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 可复现性整改及解包媒体链验收材料；服务发行复现审计；cleanup_20261023.py按路径治理；证书文本为公开APK签名证书；限制：rectify_native旧报告当前缺失，不把历史文档引用当实物存在；子项目索引归属：projects/distribution/history/work/review_20261016 |
| work/review_20261017 | work/review_20261017 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | 工具交付前APK参数与前缀冒烟证据；解包为被测功能，属于历史交付验收；未证明是主线日常必读输入；限制：q1_ref、q2_ref生成命令未定位；子项目索引归属：projects/distribution/history/work/review_20261017 |
| work/review_20261017_r1 | work/review_20261017_r1 | 所属子项目建立历史索引；物理原位保护，不重跑 | 逐项证据 | T06 | R1工具发行整改隔离副本及包检查；真实文件副本；同名extract_native/probe_native当前明确导入根scripts，不能把静态同名import候选误作本iso运行消费者；限制：未穷尽外部执行器；不能证明整个iso无人使用；子项目索引归属：projects/distribution/history/work/review_20261017_r1 |
| docs/tasks/20261016-reproducibility-audit.md | projects/distribution/docs/tasks/20261016-reproducibility-audit.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-clean-release-reproduction.md | projects/distribution/docs/tasks/20261025-clean-release-reproduction.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02,T05 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| output/share_bundle/build_bundle.py | output/share_bundle/build_bundle.py | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 更具体例外；保留父级成果和旧入口兼容；子项目索引归属：projects/distribution/src/legacy/build_bundle.py |
| output/share_bundle/20261025-character-tools/prepare_release.py | output/share_bundle/20261025-character-tools/prepare_release.py | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 冻结历史执行脚本；不重跑，不import；需要新维护入口时另取受控版本；子项目索引归属：output/share_bundle/20261025-character-tools/prepare_release.py |
| output/share_bundle/20261025-character-tools/freeze_package_spec.py | output/share_bundle/20261025-character-tools/freeze_package_spec.py | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 冻结历史执行脚本；不重跑，不import；需要新维护入口时另取受控版本；子项目索引归属：output/share_bundle/20261025-character-tools/freeze_package_spec.py |
| output/share_bundle/20261025-character-tools/build_with_record.py | output/share_bundle/20261025-character-tools/build_with_record.py | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 冻结历史执行脚本；不重跑，不import；需要新维护入口时另取受控版本；子项目索引归属：output/share_bundle/20261025-character-tools/build_with_record.py |
| output/share_bundle/20261025-character-tools/finalize_release.py | output/share_bundle/20261025-character-tools/finalize_release.py | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 冻结历史执行脚本；不重跑，不import；需要新维护入口时另取受控版本；子项目索引归属：output/share_bundle/20261025-character-tools/finalize_release.py |
| output/share_bundle/20261025-character-tools/supplement_inputs.py | output/share_bundle/20261025-character-tools/supplement_inputs.py | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 冻结历史执行脚本；不重跑，不import；需要新维护入口时另取受控版本；子项目索引归属：output/share_bundle/20261025-character-tools/supplement_inputs.py |
| output/share_bundle/20261025-character-tools/isolation_launcher.py | output/share_bundle/20261025-character-tools/isolation_launcher.py | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 冻结历史执行脚本；不重跑，不import；需要新维护入口时另取受控版本；子项目索引归属：output/share_bundle/20261025-character-tools/isolation_launcher.py |
| output/share_bundle/20261025-character-tools/test_isolation.py | output/share_bundle/20261025-character-tools/test_isolation.py | 冻结原件原位；子项目建立索引入口 | C18,C19 | T02,T05 | 冻结历史执行脚本；不重跑，不import；需要新维护入口时另取受控版本；子项目索引归属：output/share_bundle/20261025-character-tools/test_isolation.py |

## 共享与运维

| 现有路径 | 拟定目标或保留位置 | 物理处置 | 契约 | 在途任务 | 说明 |
|---|---|---|---|---|---|
| .git | .git | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| .gitignore | .gitignore | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| .venv | .venv | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| .zcode | .zcode | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| AGENTS.md | AGENTS.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| HANDOFF.md | HANDOFF.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| README.md | README.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| STATUS.md | STATUS.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| docs | docs | 保持原位，后续仅在具体迁移任务中实施 | C15 | T01,T02,T06,T07 | 按下层明确行迁移；容器不整体移动 |
| nul | nul | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | 命令失败诊断残留普通文件；真实普通文件而非NUL设备；未发现实际消费者，不据此判定无人使用；限制：具体创建命令、时间及执行者未确认；子项目索引归属：docs/operations/project-layout |
| output | output | 保持原位，后续仅在具体迁移任务中实施 | C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C18,C19,C21 | T01,T02,T06,T07 | 按下层明确行迁移；容器不整体移动 |
| raw | raw | 保持原位，后续仅在具体迁移任务中实施 | C02 | T01,T02,T06,T07 | 按下层明确行迁移；容器不整体移动 |
| requirements-lock.txt | requirements-lock.txt | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| scripts | scripts | 保持原位，后续仅在具体迁移任务中实施 | C01,C02,C03,C04,C05,C06,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18,C20 | T01,T02,T06,T07 | 按下层明确行迁移；容器不整体移动 |
| skill参考 | skill参考 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| tools | tools | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| work | work | 保持原位，后续仅在具体迁移任务中实施 | C01,C02,C11,C13,C21 | T01,T02,T06,T07 | 按下层明确行迁移；容器不整体移动 |
| チェンクロ.apk | チェンクロ.apk | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| 锁链战记_Codex缓存数据提取方案.md | 锁链战记_Codex缓存数据提取方案.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| 锁链战记_可行性评估与实施方案_v2.md | 锁链战记_可行性评估与实施方案_v2.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| 锁链战记_阶段AB成果与阶段C路线独立审查_20261015_0006.md | 锁链战记_阶段AB成果与阶段C路线独立审查_20261015_0006.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 根约定、输入、工具、环境或未归属参考；本次不调整 |
| output/20261024-project-review | operations/records/project-review/20261024 | 保持原位，后续仅在具体迁移任务中实施 | C13 | T06 | 包含运行记录或历史成果；目标需忽略 Git；不得改历史内容 |
| output/_p.tmp | output/_p.tmp | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | 单字节临时占位文件；内容无业务记录、路径或代码；不能指定业务项目；限制：创建用途和执行者未确认；子项目索引归属：docs/operations/project-layout |
| output/git_sync_20261024 | operations/records/git-sync/20261024 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 包含运行记录或历史成果；目标需忽略 Git；不得改历史内容 |
| output/project_overview | operations/records/project-overview/20261020 | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 包含运行记录或历史成果；目标需忽略 Git；不得改历史内容 |
| output/storage_retention | output/storage_retention | 冻结原件原位；子项目建立索引入口 | C13 | T06 | 包含运行记录或历史成果；目标需忽略 Git；不得改历史内容；子项目索引归属：operations/records/storage-retention |
| output/审查报告 | operations/records/legacy-reviews | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 包含运行记录或历史成果；目标需忽略 Git；不得改历史内容 |
| scripts/__pycache__ | scripts/__pycache__ | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | 公共工具CPython运行缓存；跨解包、字段研究与采集模块的缓存，不是权威源码或业务成果；限制：未反序列化每份pyc核对历史源码路径；子项目索引归属：docs/operations/project-layout |
| scripts/storage_retention | scripts/operations/storage_retention | 保持原位，后续仅在具体迁移任务中实施 | C13 | T06 | 保护规则及 pin 先保持，不借整理变更保留策略 |
| scripts/work | scripts/work | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | 空的嵌套工作容器；当前无业务输入或产物；不能凭refcheck名称归参考资料分析；限制：创建者和原用途未知；治理归属已定；子项目索引归属：docs/operations/project-layout |
| scripts/character_skills/__pycache__ | scripts/character_skills/__pycache__ | 共享运行／治理材料原位保留，不清理 | C09 | T06 | 角色研究与展示模块CPython缓存；跨研究与展示运行缓存；父目录C09保护不等于缓存本身参加源码签名；不解除主线保护；限制：未穷尽其他运行器对缓存的访问；子项目索引归属：docs/operations/project-layout |
| scripts/character_skills/_p.tmp | scripts/character_skills/_p.tmp | 共享运行／治理材料原位保留，不清理 | C09 | T06 | 单字节临时占位文件；未由内容确定业务用途；保留父目录在途保护；限制：创建用途、执行者及其他动态访问未确认；子项目索引归属：docs/operations/project-layout |
| work/_p.tmp | work/_p.tmp | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | 单字节临时占位文件；不含业务依赖；不是空文件；限制：创建用途和执行者未确认；子项目索引归属：docs/operations/project-layout |
| work/_tmp_check.py | work/_tmp_check.py | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | Git HEAD模块依赖完整性诊断；读取git ls-tree、HEAD和当前.py，输出stdout，无业务生成调用；限制：原始执行记录和调用者未确认；子项目索引归属：docs/operations/project-layout |
| work/_tmp_import_scan.py | work/_tmp_import_scan.py | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | Git未跟踪模块依赖诊断；读Git索引与工作树，输出stdout，不写业务成果；限制：原始执行记录和调用者未确认；子项目索引归属：docs/operations/project-layout |
| work/chain_precheck_scratch | work/chain_precheck_scratch | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | 当前空的未定来源工作占位目录；未发现当前运行/历史/恢复依赖；不能凭chain/precheck名称认定业务，保守归共享治理；限制：创建者、原用途及是否曾有内容未知；子项目索引归属：docs/operations/project-layout |
| work/character_skills_incident_sync | work/character_skills_incident_sync | 工作／恢复材料原位保护 | 待核 | T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/cycle_closeout_c8_c10_20261031 | work/cycle_closeout_c8_c10_20261031 | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | C8-C10存储收尾归档恢复抽样树；依赖vault/清单/restore_request，关联journal、容量和Git闭包；治理恢复样本，非普通技能数据；旧清理授权不复用；子项目索引归属：docs/operations/project-layout |
| work/memcheck.ps1 | work/memcheck.ps1 | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | 系统内存和进程占用诊断；读系统状态、输出stdout，无项目文件读写；子项目索引归属：docs/operations/project-layout |
| work/memcheck2.ps1 | work/memcheck2.ps1 | 共享运行／治理材料原位保留，不清理 | 逐项证据 | T06 | Python及全部进程工作集诊断；读进程状态、输出stdout，无项目文件读写；子项目索引归属：docs/operations/project-layout |
| work/project_review | work/project_review | 工作／恢复材料原位保护 | 待核 | T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/recycle_bytes.ps1 | work/recycle_bytes.ps1 | 工作／恢复材料原位保护 | 待核 | T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/recycle_occupancy.ps1 | work/recycle_occupancy.ps1 | 工作／恢复材料原位保护 | 待核 | T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/recycle_occupancy2.ps1 | work/recycle_occupancy2.ps1 | 工作／恢复材料原位保护 | 待核 | T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/recyclecheck.ps1 | work/recyclecheck.ps1 | 工作／恢复材料原位保护 | 待核 | T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/storage_recycle_g1_20261027 | work/storage_recycle_g1_20261027 | 工作／恢复材料原位保护 | 待核 | T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| work/storage_retention_20261023 | work/storage_retention_20261023 | 工作／恢复材料原位保护 | 待核 | T06 | 工作副本可能是输入、冻结基线或恢复材料；仅提出候选归属，先查任务与引用 |
| docs/tasks/20261019-character-skills-git-handoff.md | docs/operations/tasks/20261019-character-skills-git-handoff.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-rectification-workflow-adjustment-request.md | docs/operations/tasks/20261023-rectification-workflow-adjustment-request.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-retention-cleanup.md | docs/operations/tasks/20261023-retention-cleanup.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261023-run-retention.md | docs/operations/tasks/20261023-run-retention.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-incident-sync.md | docs/operations/tasks/20261024-character-skills-incident-sync.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-character-skills-workflow-adjustment.md | docs/operations/tasks/20261024-character-skills-workflow-adjustment.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-git-mainline-sync.md | docs/operations/tasks/20261024-git-mainline-sync.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-git-readiness-check.md | docs/operations/tasks/20261024-git-readiness-check.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-historical-replay-guards.md | docs/operations/tasks/20261024-historical-replay-guards.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-incident-command.md | docs/operations/tasks/20261024-incident-command.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-incident-thirdparty-review.md | docs/operations/tasks/20261024-incident-thirdparty-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-run-recovery-audit.md | docs/operations/tasks/20261024-run-recovery-audit.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-run-restore.md | docs/operations/tasks/20261024-run-restore.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-storage-governance-plan.md | docs/operations/tasks/20261024-storage-governance-plan.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261024-workflow-adjustment-review-prompt.md | docs/operations/tasks/20261024-workflow-adjustment-review-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261025-export-cleanup-inventory.md | docs/operations/tasks/20261025-export-cleanup-inventory.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261026-cleanup-inventory-prompt.md | docs/operations/tasks/20261026-cleanup-inventory-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261027-recycle-g1-review-reply.md | docs/operations/tasks/20261027-recycle-g1-review-reply.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261027-recycle-g2-micro-batch-prompt.md | docs/operations/tasks/20261027-recycle-g2-micro-batch-prompt.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261027-recycle-plan-host-review.md | docs/operations/tasks/20261027-recycle-plan-host-review.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261027-storage-recycle-g1.md | docs/operations/tasks/20261027-storage-recycle-g1.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261031-c8-c10-cycle-closeout-cleanup-git.md | docs/operations/tasks/20261031-c8-c10-cycle-closeout-cleanup-git.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261102-c11-c13-cycle-closeout-cleanup-git.md | docs/operations/tasks/20261102-c11-c13-cycle-closeout-cleanup-git.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261104-c14-c15-cycle-closeout-cleanup-git.md | docs/operations/tasks/20261104-c14-c15-cycle-closeout-cleanup-git.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c16-closeout-cleanup-git.md | docs/operations/tasks/20261106-c16-closeout-cleanup-git.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-c17-c18-closeout-cleanup-git.md | docs/operations/tasks/20261106-c17-c18-closeout-cleanup-git.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T06 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| docs/tasks/20261106-project-layout-mapping.md | docs/tasks/20261106-project-layout-mapping.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T07 | 旧文档相对链接需映射；不改原任务状态，不以老日期推定任务结束 |
| .zcode/plans/plan-session_484fe26880b140801f3734c1a724c9f8.md | .zcode/plans/plan-session_484fe26880b140801f3734c1a724c9f8.md | 保持原位，后续仅在具体迁移任务中实施 | 待核 | T02 | C18旧计划，不能当当前C19实时状态 |

## 待核归属

| 现有路径 | 拟定目标或保留位置 | 物理处置 | 契约 | 在途任务 | 说明 |
|---|---|---|---|---|---|

## 覆盖及使用边界

逐路径静态候选来源、消费者、迁移门槛、首版目标与物理别名保存在[path-map.json](path-map.json)。当前清单不是移动脚本；没有引用命中不代表无人使用。
