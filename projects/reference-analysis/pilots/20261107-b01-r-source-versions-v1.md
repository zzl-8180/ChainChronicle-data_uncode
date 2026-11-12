# B01-R 固定历史来源报告试点

本试点只比较两个历史外部 `param_table.json` 的固定SHA-256、字节数、JSON结构以及 `(table,type,slot)` 键集合；不校验游戏数值、换算公式、译文或规则语义，不收取当前C19或Web输入。共同键不代表对应行内容相同。

入口：[source_version_report.py](../scripts/source_version_report.py)。只使用Python标准库，不导入业务脚本或外部参考代码。

首次生成时从项目根目录执行；下述版本目录现已生成，再运行会按设计拒绝。后续重建须指定新的版本目录：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -B projects/reference-analysis/scripts/source_version_report.py --root . --out projects/reference-analysis/reports/20261107-b01-r-source-versions-v1
```

输出：[README](../reports/20261107-b01-r-source-versions-v1/README.md)、[report.json](../reports/20261107-b01-r-source-versions-v1/report.json)、[validation.json](../reports/20261107-b01-r-source-versions-v1/validation.json)。报告树由本项目局部 `.gitignore` 忽略。

入口只接受 `--root` 和 `--out`；输出必须为该root下 `projects/reference-analysis/reports/` 的一个不存在的直接子目录。输入路径及哈希写在入口中，输出、输入和root祖先遇目录联接／符号链接即失败。已有输出一律拒绝，重跑需明确指定新版本目录；不会覆盖历史结果或更新latest指针。

原件保持在 `其他人的参考/claude_cc_site_pages/param_table.json` 和 `其他人的参考/claude_cc_site_pages 20261023/param_table.json`，不复制全表到报告。生成前重新读取哈希以拒绝来源漂移。负例验证仅在本次报告的独立 `negative/` 内使用小JSON假输入，不修改原件。

失败时停用新入口并保留诊断；不覆盖旧树、不清理失败目录。B01-R与B01-D单独回执；发行子轨只有主聊天验收后才可收取固定 `report.json`，不收取此生成器或外部参数表。本次没有新机器安装验证，也不代表完整解包／角色重建／完整发行验收。

本次验证：正常生成1次；已有输出及小错误来源哈希负例均退出2；两原件与两旧报告README哈希不变；7条本地链接存在；4个代表产物被局部忽略。键集合共同1610、增加63、删除0。首次验证driver捕获负例stderr发生编码异常，保留诊断并以 `-X utf8` 重做负例；未重跑成功生成，详见 `validation.json`。冻结 `report.json` 为6207字节，SHA-256 `1bebea9545c02bc56b89d414f3eb7af4011539889548d6a15e154eff862e3643`。
