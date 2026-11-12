# 28 项删除候选：适配后条件复核

本轮不删除文件。此表更新原退役清单的条件状态，不改原冻结清单。技术条件满足不等于已执行删除；实际删除时仍须重核身份、确认无新增写入，并同步退役指引。

| 状态 | 项数 | 逻辑字节 | 说明 |
|---|---:|---:|---|
| 专属技术条件满足 | 3 | 33,776,867 | 旧 data ZIP、handoff ZIP、118 字节失败 A ZIP |
| 待代码入口退役 | 19 | 240,771 | 17 个脚本和 2 个缓存，文档／导航及实际删除时活动核对未完成 |
| 待旧版本处置边界明确 | 6 | 2,027,261,537 | 成功历史包无已核完整替代副本，不能承诺可回退 |

六个成功历史包是 20261016 两交付 ZIP、20261025 retry A/B/C 和旧 full 分析 ZIP。确认整支退役时应列明这些旧版本的整包重放／恢复随之放弃；不需要为此新造一套大型备份。

参考分析已解除运行依赖，不再需要为历史抽样保留旧 data ZIP；这也不表示该 ZIP 的完整594份载荷能够由成员清单恢复。成员清单只保留包内身份和抽样证据。

HOLD 的1,997项及RETAIN的4,763项不在此次28项条件评估的删除范围内。

## 逐文件状态

| 文件（仓库相对路径） | 字节 | 当前状态 |
|---|---:|---|
| `output/share_bundle/20261016-delivery/CC_delivery_research_20261016.zip` | 22,177,812 | 待旧版本处置边界明确 |
| `output/share_bundle/20261016-delivery/CC_delivery_tools_20261016.zip` | 1,441,178 | 待旧版本处置边界明确 |
| `output/share_bundle/20261025-character-tools/build_with_record.py` | 1,162 | 待入口退役 |
| `output/share_bundle/20261025-character-tools/finalize_release.py` | 11,527 | 待入口退役 |
| `output/share_bundle/20261025-character-tools/freeze_package_spec.py` | 2,405 | 待入口退役 |
| `output/share_bundle/20261025-character-tools/isolation_launcher.py` | 952 | 待入口退役 |
| `output/share_bundle/20261025-character-tools/packages/A_tools.zip` | 118 | 专属技术条件满足 |
| `output/share_bundle/20261025-character-tools/packages_retry/A_tools.zip` | 1,521,555 | 待旧版本处置边界明确 |
| `output/share_bundle/20261025-character-tools/packages_retry/B_data_research.zip` | 69,517,757 | 待旧版本处置边界明确 |
| `output/share_bundle/20261025-character-tools/packages_retry/C_character_pages_images.zip` | 1,781,589,013 | 待旧版本处置边界明确 |
| `output/share_bundle/20261025-character-tools/prepare_release.py` | 5,173 | 待入口退役 |
| `output/share_bundle/20261025-character-tools/supplement_inputs.py` | 1,786 | 待入口退役 |
| `output/share_bundle/20261025-character-tools/test_isolation.py` | 5,763 | 待入口退役 |
| `output/share_bundle/20261104-mechanism-first-handoff-r1/mechanism_first_handoff_r1.zip` | 5,341,487 | 专属技术条件满足 |
| `output/share_bundle/CC_analysis_data_20261016.zip` | 28,435,262 | 专属技术条件满足 |
| `output/share_bundle/CC_analysis_full_20261016.zip` | 151,014,222 | 待旧版本处置边界明确 |
| `output/share_bundle/build_bundle.py` | 8,657 | 待入口退役 |
| `scripts/release/__pycache__/build_delivery_bundle.cpython-312.pyc` | 18,767 | 待入口退役 |
| `scripts/release/__pycache__/build_skill_values_bundle.cpython-312.pyc` | 64,105 | 待入口退役 |
| `scripts/release/build_delivery_bundle.py` | 16,139 | 待入口退役 |
| `scripts/release/build_explicit_bundle.py` | 12,508 | 待入口退役 |
| `scripts/release/build_full_unpack_bundle.py` | 15,507 | 待入口退役 |
| `scripts/release/build_mechanism_handoff.py` | 15,660 | 待入口退役 |
| `scripts/release/build_skill_values_bundle.py` | 44,315 | 待入口退役 |
| `scripts/release/check_full_unpack_bundle.py` | 5,844 | 待入口退役 |
| `scripts/release/materialize_character_art_sources.py` | 1,915 | 待入口退役 |
| `scripts/release/reproduce_character_samples.py` | 2,423 | 待入口退役 |
| `scripts/release/verify_mechanism_handoff.py` | 6,163 | 待入口退役 |

[机器清单与逐项理由](deletion-readiness.json) · [适配验收](README.md)
