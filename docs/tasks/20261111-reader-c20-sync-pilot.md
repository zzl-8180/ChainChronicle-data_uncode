# C20 阅读器增量接入试点

- 状态：隔离试点已验收。范围为已审 C20 的 16 卡、18 行、25 个正式答案。
- 写入范围：`projects/reader/site/c20-sync-pilot-20261111/`、`projects/reader/reports/c20-sync-pilot-20261111/`、`scripts/skill_reader_preview/c20_pilot.py`、本任务卡和独立测试工作目录。
- 输入：C19 R01 正式阅读器、C20 R02 交付及最终独审、C20 正式卡与账本、共享卡面。所有输入只读。
- 验收：精确匹配的 15 个旧候选让位于正式答案，其余父分支按合记／排除依据披露，保持同句未知、原有答案和可信度。交付隔离入口与逐项对账。
- 结果：[试点](http://127.0.0.1:8771/projects/reader/site/c20-sync-pilot-20261111/) · [验收报告](../../projects/reader/reports/c20-sync-pilot-20261111/REPORT.md)。15 条同父去重，6 条其他父按正式证据合记，1 条旧父明确保留为未选用。21 条同句拆分待核查继续可见。16 张变化卡桌面和 390px 验收通过，其余分支覆盖及条件无回归。
