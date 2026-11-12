# 数据解包原位路径索引

生成：2026-11-07T02:08:05+08:00。导航批次：B00；物理操作：none；recursive=false；selection_mode=exact_mapping_entry；specific_child_precedence=true。

本索引完整覆盖批准基线 `path-map.json`（schema_version=3，SHA-256 `a2a89d48104cd4707515b98d4ccd48462a455c7b63b5a3431ed4978c9ea2061d`）中本归属的所有行，**不是此刻全项目文件枚举，不是实时任务看板或移动许可**。目录父子行有重叠，更具体子行优先，不能把目录行递归解释为移动全部后代。业务文件均在原位；不据归属判定可清理、可改写或所有者已交接。

每行“路径”是原 `source` 的当前物理路径。仅存在且非Windows保留名生成相对链接；缺件只标 missing，不补造文件。存在性仅为生成时精确路径元数据观察，不表示内容验证、所有后代齐备或动态依赖验证。`nul` 使用扩展路径判断且不链接普通设备。原依赖／契约／任务编号与保护属性保持基线含义；任务阶段可能已过时，请读实际任务卡。未来目标建议只在机读索引中保留为方案，不做目标死链接。

完整原行属性、历史目标建议与存在性元数据见 [index.json](index.json)；版本入口见 [README.md](README.md)。

本归属：80行。

| 当前原位source | 种类／归属 | 本行原位保护说明 | 依赖／契约／任务编号 |
|---|---|---|---|
| [output/apk](../../../output/apk) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C01；任务 T02, T06 |
| [output/base_master](../../../output/base_master) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；字典/trace/主表是活跃输入，不按历史目录整体归档；两个在途任务都需保持读取根；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C03；任务 T02, T06 |
| [output/cache_full_20261015](../../../output/cache_full_20261015) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/cache_full_20261015_v2](../../../output/cache_full_20261015_v2) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/cache_full_20261015_v3](../../../output/cache_full_20261015_v3) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；字典/trace/主表是活跃输入，不按历史目录整体归档；两个在途任务都需保持读取根；保留旧页输入版本；页面不仅输出，不能按JSON与HTML直接拆路径；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C03, C07；任务 T02, T06 |
| [output/cache_full_latest.json](../../../output/cache_full_latest.json) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移时同步指针；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/cache_refresh_20261015](../../../output/cache_refresh_20261015) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；清单archive/work_file必须可解析；另建新清单映射，不手改冻结来源；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C02；任务 T02, T06 |
| [output/cache_refresh_latest.json](../../../output/cache_refresh_latest.json) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移时同步指针；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/decoded](../../../output/decoded) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/export](../../../output/export) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/il2cpp](../../../output/il2cpp) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11, D04, D08；契约 —；任务 T02, T06 |
| [output/native](../../../output/native) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C01；任务 T02, T06 |
| [output/phone](../../../output/phone) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/phone_full_20261015](../../../output/phone_full_20261015) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/phone_refresh_20261015](../../../output/phone_refresh_20261015) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/protection](../../../output/protection) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C01；任务 T02, T06 |
| [output/single](../../../output/single) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [output/validation](../../../output/validation) | directory／unpack | 保持原位，后续仅在具体迁移任务中实施；迁移候选；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/analyze_cache_snapshot.py](../../../scripts/analyze_cache_snapshot.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；代码不只在scripts；纯函数被跨项目复用，主入口可能读取研究证据；先维持接口与旧CLI；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C20；任务 T02, T06 |
| [scripts/apk_baseline.py](../../../scripts/apk_baseline.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/apk_certificate.py](../../../scripts/apk_certificate.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/bounded_decode.py](../../../scripts/bounded_decode.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/cache_probe.py](../../../scripts/cache_probe.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/callback_key_candidates.py](../../../scripts/callback_key_candidates.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/callback_sample.py](../../../scripts/callback_sample.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/collect_cache_archive.py](../../../scripts/collect_cache_archive.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/collect_cache_refresh.py](../../../scripts/collect_cache_refresh.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/decode_cache_snapshot.py](../../../scripts/decode_cache_snapshot.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；代码不只在scripts；纯函数被跨项目复用，主入口可能读取研究证据；先维持接口与旧CLI；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C20；任务 T02, T06 |
| [scripts/decode_cache_variants.py](../../../scripts/decode_cache_variants.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/decode_chronicle.py](../../../scripts/decode_chronicle.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C01；任务 T02, T06 |
| [scripts/decode_data5.py](../../../scripts/decode_data5.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C01；任务 T02, T06 |
| [scripts/elf_branch_refs.py](../../../scripts/elf_branch_refs.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/elf_global_refs.py](../../../scripts/elf_global_refs.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/elf_relocations.py](../../../scripts/elf_relocations.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/emulator_probe.py](../../../scripts/emulator_probe.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/export_master.py](../../../scripts/export_master.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；代码不只在scripts；纯函数被跨项目复用，主入口可能读取研究证据；先维持接口与旧CLI；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C20；任务 T02, T06 |
| [scripts/extract_cache_archive.py](../../../scripts/extract_cache_archive.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/guest_lz4.py](../../../scripts/guest_lz4.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/il2cpp_metadata_entry.py](../../../scripts/il2cpp_metadata_entry.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/il2cpp_sample_code.py](../../../scripts/il2cpp_sample_code.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/jni_prefix_probe.py](../../../scripts/jni_prefix_probe.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/metadata_decode_probe.py](../../../scripts/metadata_decode_probe.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/metadata_targets.py](../../../scripts/metadata_targets.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/native_debug.py](../../../scripts/native_debug.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C01；任务 T02, T06 |
| [scripts/native_plugin_paths.py](../../../scripts/native_plugin_paths.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/native_probe.py](../../../scripts/native_probe.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/native_readpaths.py](../../../scripts/native_readpaths.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/nutils_data_probe.py](../../../scripts/nutils_data_probe.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/phone_collect.py](../../../scripts/phone_collect.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/protection_emulate.py](../../../scripts/protection_emulate.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C01；任务 T02, T06 |
| [scripts/protection_report.py](../../../scripts/protection_report.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/protection_sample.py](../../../scripts/protection_sample.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/recovered_readpaths.py](../../../scripts/recovered_readpaths.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/signal_region_probe.py](../../../scripts/signal_region_probe.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/verify_cache_refresh.py](../../../scripts/verify_cache_refresh.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；清单archive/work_file必须可解析；另建新清单映射，不手改冻结来源；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 C02；任务 T02, T06 |
| [scripts/verify_cache_snapshot.py](../../../scripts/verify_cache_snapshot.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/verify_data5.py](../../../scripts/verify_data5.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/verify_export.py](../../../scripts/verify_export.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/verify_export_pointer.py](../../../scripts/verify_export_pointer.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/verify_metadata.py](../../../scripts/verify_metadata.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/verify_phase_a.py](../../../scripts/verify_phase_a.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/verify_phase_b.py](../../../scripts/verify_phase_b.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [scripts/verify_phase_c.py](../../../scripts/verify_phase_c.py) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；代码候选待适配；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11；契约 —；任务 T02, T06 |
| [raw/_p.tmp](../../../raw/_p.tmp) | file／unpack | 原件原位保护；原件原位；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D09, D12；契约 —；任务 T02, T06 |
| [raw/phone_20261014_binary_retry](../../../raw/phone_20261014_binary_retry) | directory／unpack | 原件原位保护；原件原位；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D09, D12；契约 —；任务 T02, T06 |
| [raw/phone_20261014_connected](../../../raw/phone_20261014_connected) | directory／unpack | 原件原位保护；原件原位；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D09, D12；契约 —；任务 T02, T06 |
| [raw/phone_20261015_full_01](../../../raw/phone_20261015_full_01) | directory／unpack | 原件原位保护；原件原位；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D09, D12；契约 —；任务 T02, T06 |
| [raw/phone_20261015_full_02](../../../raw/phone_20261015_full_02) | directory／unpack | 原件原位保护；原件原位；清单archive/work_file必须可解析；另建新清单映射，不手改冻结来源；本轮仅新增导航，原位未动 | 依赖 D01, D09, D12；契约 C02；任务 T02, T06 |
| [raw/phone_20261015_refresh_01](../../../raw/phone_20261015_refresh_01) | directory／unpack | 原件原位保护；原件原位；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D09, D12；契约 —；任务 T02, T06 |
| [raw/phone_20261015_refresh_02](../../../raw/phone_20261015_refresh_02) | directory／unpack | 原件原位保护；原件原位；清单archive/work_file必须可解析；另建新清单映射，不手改冻结来源；本轮仅新增导航，原位未动 | 依赖 D01, D09, D12；契约 C02；任务 T02, T06 |
| [work/apk](../../../work/apk) | directory／unpack | 工作／恢复材料原位保护；运行或历史材料，原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11, D07；契约 C01；任务 T02, T06 |
| [work/decoded_candidates](../../../work/decoded_candidates) | directory／unpack | 所属子项目建立历史索引；物理原位保护，不重跑；归属已核；仅建立分类索引，原位保护；归属确定不构成迁移或清理授权；保持原路径、冻结内容和现有消费者。尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D08, D11, D12, D07；契约 —；任务 T06 |
| [work/phase_c_checks](../../../work/phase_c_checks) | directory／unpack | 工作／恢复材料原位保护；原位待核；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11, D07；契约 —；任务 T02, T06 |
| [work/phase_e_delivery_fix_20261015_4a244651af](../../../work/phase_e_delivery_fix_20261015_4a244651af) | directory／unpack | 工作／恢复材料原位保护；原位待核；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11, D07；契约 —；任务 T02, T06 |
| [work/phone_20261015_full_02](../../../work/phone_20261015_full_02) | directory／unpack | 工作／恢复材料原位保护；运行或历史材料，原位保护；清单archive/work_file必须可解析；另建新清单映射，不手改冻结来源；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11, D07；契约 C02；任务 T02, T06 |
| [work/phone_20261015_refresh_02](../../../work/phone_20261015_refresh_02) | directory／unpack | 工作／恢复材料原位保护；运行或历史材料，原位保护；清单archive/work_file必须可解析；另建新清单映射，不手改冻结来源；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11, D07；契约 C02；任务 T02, T06 |
| [work/phone_candidates](../../../work/phone_candidates) | directory／unpack | 工作／恢复材料原位保护；原位待核；尚未完成具体运行接口闭包；不依据无静态命中判定无人使用；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11, D07；契约 —；任务 T02, T06 |
| [work/protection](../../../work/protection) | directory／unpack | 工作／恢复材料原位保护；运行或历史材料，原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D01, D02, D03, D11, D07；契约 C01；任务 T02, T06 |
| [output/protection/relocations.json](../../../output/protection/relocations.json) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D11, D12；契约 C01；任务 T02 |
| [output/native/recovered_symbols.json](../../../output/native/recovered_symbols.json) | file／unpack | 保持原位，后续仅在具体迁移任务中实施；契约适配前原位保护；先显式配置APK工作根、重定位、镜像、symbols；保持版本哈希与原路径兼容；本轮仅新增导航，原位未动 | 依赖 D11, D12；契约 C01；任务 T02 |
