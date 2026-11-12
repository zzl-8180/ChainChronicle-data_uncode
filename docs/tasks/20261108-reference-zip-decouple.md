# 参考分析旧 data ZIP 消费者适配

- 负责人／对话：`/root/reference_zip_decouple`；2026-11-08。
- 状态：Sol 实现完成，主聊天独立验收通过；未执行任何删除或移动。
- 范围：`scripts/ref_analysis_claude_cc.py` 的包成员读取；`output/reference_analysis/claude_cc_site_pages/README.md` 的再生成说明；本任务 `docs/project-layout/20261108-reference-zip-decouple-v1/`。
- 共享依赖：冻结 `docs/project-layout/20261108-packaging-retirement-v1/analysis-data-central-directory.json`；历史 `output/reference_analysis/claude_cc_site_pages/version_sample_check.json`。两者仅只读，未修改。
- 变更：抽样消费者按冻结中央目录的 `entries` 原序读取成员名，校验来源、条目结构、连续序号及冻结文件 SHA-256。移除唯一 ZIP 读取和 `zipfile` 导入。清单缺失或损坏时明确失败，无 ZIP 回退。
- 验证：`& .\.venv\Scripts\python.exe -B docs\project-layout\20261108-reference-zip-decouple-v1\test_reference_zip_decouple.py`；实际 helper 的成员名与旧 ZIP 原序 596/596 相同，三个字段与 ZIP 计算及历史 JSON 相同；无 ZIP 内存隔离、缺失、坏 JSON、序号错误、哈希变化均通过。详见同目录 `verification.json`。
- 边界：未导入或运行完整参考分析，未重建历史输出、打包或修改 ZIP；28 项退役候选的最终门槛由主聊天评估。
- 独立验收：主聊天复跑9项针对测试，并从修改前后源码分别提取实际消费者读取段执行，三个字段与历史结果完全一致，新读取段禁止 ZIP 访问仍通过；18个保护文件哈希不变。
- 最近更新／下一步：2026-11-08；28项中3项专属技术条件满足、19项待代码入口退役、6项待旧版本处置边界明确；实际删除前仍须临前身份与活动核对。见 [逐项状态](../project-layout/20261108-reference-zip-decouple-v1/deletion-readiness.md)。本轮到此收口，不自动删除。
