# 第三批整目录候选：解包、验收与 Unity 有界准入

**结论：本批不选这三棵作为低耦合整目录搬迁。** `validation` 最小，但仍是阶段验收和探针的当前写入根；`decoded` 与 `unity` 均有更宽的现用读写闭包。第三批优先取已经单独筛出的低耦合完整树。此处只读调查，未搬迁、改脚本、改联接、运行生成器或提交。

| 现址 → 既有映射目标 | 文件／子目录／逻辑字节 | 准入判断 |
|---|---:|---|
| `output/decoded` → `projects/unpack/history/decoded` | 23／0／17,027,377 | 排除：默认解码输出与旧报告输入，加上多条固定研究／验证读口 |
| `output/validation` → `projects/unpack/reports/validation` | 8／2／27,103 | 暂不选：小而非纯报告，固定写者和读者需一起适配 |
| `output/unity` → `projects/assets/history/unity` | 50／2／84,552,259 | 排除：五个当前隔离 junction、内嵌 `text_path` 和字段／图片消费者 |

三棵根及内部均未见 reparse。三个目标都不存在；`decoded` 目标父目录存在，另两个目标父目录尚不存在。计数为当前不跟随外部联接的物理集合，不是先前静态索引的时间点保证。未做全量内容哈希。

## 最小接口闭包

- `decoded`：第二批 [调查](../20261108-directory-batch2-ready-v1/investigation-unpack.md)已明确 `decode_data5.py` 默认写、`decode_cache_snapshot.py` 默认读 report；当前另核 `export_master.py` 的 report/raw、`verify_data5.py` 的字节对照、`sample_trace.py`、Chica 和阶段 D 探针。若未来搬迁，须针对实际选用命令一起配置默认／读根，更新根 [README](../../../README.md) B1 命令和 unpack 导航，并保留旧卡页 `original_file` 作为冻结溯源，不手改旧报告。此批不再扩大主线读口调查。
- `validation`：`verify_phase_a.py` 固定写 checks、截断样本及 invalid_unity；它还启动 Unity、native、structured 子命令，所以单独改其 `out` 不能隔离整条执行链。`verify_data5.py`、`verify_metadata.py`、`verify_phase_b.py`、`verify_phase_c.py`、`high_hp_sample_probe.py` 固定写相应检查文件；`sample_trace.py`、`export_master.py` 固定读 high-HP 样本。`build_field_guide.py` 写出的说明保留旧路径。未来最小方案是让选用验收链与读者共享一个声明的候选根，逐个关闭子命令写域，在生成器更新说明导航，不改冻结检查文件。当前不值得为本批低耦合搬迁启动这套适配。
- `unity`：`unity_scan.py`、`mono_headers.py` 虽有 `--output`，默认仍写旧根；前者把输出路径写入 `textassets.jsonl` 的 `text_path`，`verify_phase_a.py` 和 `structured_candidates.py` 会按该值取文件。`build_field_guide.py`、`audit_unity_headers.py`、`extract_cid30236_images.py` 固定读旧索引。五个 C14—C18 `impl/isolation_input/output/unity` 目前均是真实 junction，精确目标为旧 `output/unity`，不能当作已退役的 share_bundle previous。未来须先决定旧 `text_path` 的外部解析或新版本索引，再闭合读取者、默认写入、五入口共同切换及 [assets README](../../../projects/assets/README.md) 导航；不可直接改旧 JSONL 字节掩盖路径问题。

静态映射给 `decoded` 485、`validation` 87、`unity` 118 个候选命中，仅作定位线索，不等于当前运行次数。定向查 `scripts/character_skills` 与 `scripts/skill_reader_preview` 的 Python/JS 未发现三个根的字面引用；但现有 `pages/30236/card.json` 中仍有 `output/decoded/skilllist.data5.json.raw` 溯源值。不能据此宣称 P/v7 冻结材料全域无引用。当前 rules/pages、旧报告与原始资源保持原字节，下一次具体搬迁另作所选消费者的临前核验。

机器可读范围和行号见 [unpack-screen.json](unpack-screen.json)。依据沿用 [path-map](../20261106/path-map.json)、静态索引、[命令读写矩阵](../20261106/audit/thirdparty-recheck-20261107/command-io-matrix.json) 与第二批调查；本轮只核当前目录、联接、脚本和少量小元数据。
