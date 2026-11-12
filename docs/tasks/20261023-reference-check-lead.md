# 20261023 参考包独立检查（Lead 线）

状态：已完成（2026-10-23）
负责人：本对话（Lead）
写入范围（实际使用）：
- `work/refcheck_20261023_lead/`（中间产物：params/、corpus/、verify/、本线补查 JSON）
- `scripts/refcheck_20261023_lead/`（本次检查脚本 `lead_crosscheck.py`、`lead_bond_check.py`、`lead_bond_join_check.py`、`lead_spotcheck.py` 及三名队友的 `params_*`/`corpus_*`/`verify_*`）
- `output/reference_analysis/claude_cc_site_pages_20261023_review/README.md`（最终报告）
- `docs/tasks/20261023-reference-check-lead.md`（本文件）

只读对象：`其他人的参考/claude_cc_site_pages 20261023/`、`其他人的参考/claude_cc_site_pages_给GPT_20261023/`、`其他人的参考/claude_cc_site_pages/`（均未修改）

明确未读（另一并行对话在飞产物，按用户要求不参考不复用）：`output/reference_analysis/claude_cc_site_pages_20261023/`、`scripts/ref_analysis_claude_cc_20261023.py`、`docs/tasks/20261023-reference-analysis.md`

结论摘要：
1. 两个目录是「我方解包数据 + 我方 cc_skill_values_20261021/22 分享包」经他人重组的角色页，外加 koncoo 网站抓取语料；1.58 GB 图片与我方 `pages/art/` 抽样逐字节相同，数据请以「给GPT」包为准（更新 2–8 小时）。
2. 对我方有用三件：羁绊 APK 层（311→2,207 卡，1,897 可解析）、45 个已确认槽位的网站命中率旁证、候选语义清单（1017 p2 / 1104 / 3000 p3–p7 / 1074 / 1051 / 58 / 116）。
3. 不可整表吸收：37 条「解包确认」含 12 条 charainfo 镜像、540 条统计推断、8 条旧误配未修 + 2 条新矛盾、存在循环引用（参考推断源自我方包）。
4. 我方原表复核另纠正对方 3 处：type99 p8/p9、type58 p4「职业通用 100000」、type28 p3 地形追加。

交接/下一步：A 组（羁绊回退层、网站旁证入库、候选登记批 10）待用户裁决是否开工；B 组（site 语料隔离收录、图片清理）需用户确认。
本任务未改 `output/character_skills/`、未改 `其他人的参考/`、未更新根 `HANDOFF.md`/`STATUS.md`。
