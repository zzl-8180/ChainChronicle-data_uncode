# 28 项逐文件执行前清单

状态：准备完成待最终审查；`SHARED_INTEGRATION_PENDING`；删除权限 `NOT_GRANTED`。详尽的两轮身份、ACL、祖先检查及哈希来源见 [JSONL](execution-candidates.jsonl)。下表只列文件，不能按目录扩大。

| 仓库相对路径 | 字节 | 门槛 | 当前身份／短时稳定 | 哈希依据 |
|---|---:|---|---|---|
| `output/share_bundle/20261016-delivery/CC_delivery_research_20261016.zip` | 22,177,812 | `G_ARCHIVE` | 一致／两轮稳定 | 历史 SHA-256（未重算） |
| `output/share_bundle/20261016-delivery/CC_delivery_tools_20261016.zip` | 1,441,178 | `G_ARCHIVE` | 一致／两轮稳定 | 历史 SHA-256（未重算） |
| `output/share_bundle/20261025-character-tools/build_with_record.py` | 1,162 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `output/share_bundle/20261025-character-tools/finalize_release.py` | 11,527 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `output/share_bundle/20261025-character-tools/freeze_package_spec.py` | 2,405 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `output/share_bundle/20261025-character-tools/isolation_launcher.py` | 952 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `output/share_bundle/20261025-character-tools/packages/A_tools.zip` | 118 | `G_ARCHIVE` | 一致／两轮稳定 | 仅元数据；无已定位历史哈希（未重算） |
| `output/share_bundle/20261025-character-tools/packages_retry/A_tools.zip` | 1,521,555 | `G_ARCHIVE` | 一致／两轮稳定 | 历史 SHA-256（未重算） |
| `output/share_bundle/20261025-character-tools/packages_retry/B_data_research.zip` | 69,517,757 | `G_ARCHIVE` | 一致／两轮稳定 | 历史 SHA-256（未重算） |
| `output/share_bundle/20261025-character-tools/packages_retry/C_character_pages_images.zip` | 1,781,589,013 | `G_ARCHIVE` | 一致／两轮稳定 | 历史 SHA-256（未重算） |
| `output/share_bundle/20261025-character-tools/prepare_release.py` | 5,173 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `output/share_bundle/20261025-character-tools/supplement_inputs.py` | 1,786 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `output/share_bundle/20261025-character-tools/test_isolation.py` | 5,763 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `output/share_bundle/20261104-mechanism-first-handoff-r1/mechanism_first_handoff_r1.zip` | 5,341,487 | `G_HANDOFF` | 一致／两轮稳定 | 历史 SHA-256（未重算） |
| `output/share_bundle/CC_analysis_data_20261016.zip` | 28,435,262 | `G_REF` | 一致／两轮稳定 | 历史 SHA-256（未重算） |
| `output/share_bundle/CC_analysis_full_20261016.zip` | 151,014,222 | `G_ARCHIVE` | 一致／两轮稳定 | 历史 SHA-256（未重算） |
| `output/share_bundle/build_bundle.py` | 8,657 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/__pycache__/build_delivery_bundle.cpython-312.pyc` | 18,767 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/__pycache__/build_skill_values_bundle.cpython-312.pyc` | 64,105 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/build_delivery_bundle.py` | 16,139 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/build_explicit_bundle.py` | 12,508 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/build_full_unpack_bundle.py` | 15,507 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/build_mechanism_handoff.py` | 15,660 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/build_skill_values_bundle.py` | 44,315 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/check_full_unpack_bundle.py` | 5,844 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/materialize_character_art_sources.py` | 1,915 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/reproduce_character_samples.py` | 2,423 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |
| `scripts/release/verify_mechanism_handoff.py` | 6,163 | `G_CODE` | 一致／两轮稳定 | 本轮实读小文件 SHA-256 |

合计 28 文件／2,061,279,175 B；所有项目前仍存在，普通单硬链接文件，逐祖先无 reparse。未证明全机无写入、未来不变化或有效删除权限；必须在实际执行前逐项重新核对。
