# 参考分析 data ZIP 消费者适配回执

状态：Sol 实施完成，主聊天独立验收通过。18 个保护文件哈希不变；未删除或移动文件。见 [独立验收](acceptance.json) 和 [28 项删除条件复核](deletion-readiness.md)。原退役 V1 清单保持原样，由本记录说明 data ZIP 的消费者阻断已解除。

本次仅替换 `scripts/ref_analysis_claude_cc.py` 中 `version_sample_check()` 的包成员名来源。旧 `CC_analysis_data_20261016.zip` 保持原位；冻结清单、历史 `version_sample_check.json` 和主线成果均未重建。脚本与参考页 README 的修改前文件分别保存在本目录的 `.before` 文件。

运行针对性验证：

```powershell
& .\.venv\Scripts\python.exe -B docs\project-layout\20261108-reference-zip-decouple-v1\test_reference_zip_decouple.py
```

测试从源码 AST 抽取**实际新增读取函数**执行，不导入含顶层 `OUT.mkdir` 的整份参考分析脚本。它核对消费者已调用该函数、冻结 `entries` 与旧 ZIP `namelist()` 原序 596/596 相等，以及「总条目」「含decoded路径」「含charainfo」与旧 ZIP 和历史 JSON 逐项相等。内存隔离根没有 ZIP，读取仅获冻结清单字节；另覆盖缺清单、坏 JSON、序号异常、内容改动的明确报错。机器回执为 `verification.json`。

冻结清单 SHA-256 为 `57c77bdba0266f084d12e1e5c9555ff73b27c2269ef2108ae5b168778bd06724`。它记录的旧 ZIP SHA-256 是**历史记录**，本轮没有重算 ZIP 全文件哈希。首次验证尝试使用系统临时目录，因当前沙箱目录权限失败；改为无落盘的内存隔离根后通过，未修改或移动旧 ZIP。未运行完整参考分析生成器。
