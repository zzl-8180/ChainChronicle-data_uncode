# C7 展示层 R1/R2 定向整改回执

- 日期：2026-10-30。范围：仅 `scripts/character_skills/cycle_report.py`、`output/character_skills/cycle_reports/C7/` 与本回执、看板/交接。未改角色答案、rules、正式页面、账本语义或证据等级；未重跑正式全库生成，未启动 C7-P4、20234 或扩大 30239 范围，未提交/推送 Git。原独立审查报告与证据保持只读。
- 依据：`output/character_skills/review/direction_c7_20261030_codex/REPORT.md`、`verdict.json`、`cycle_page_counterexamples.json`。

## R1：按 row_id／新增身份选例

生成器现支持以 `row_id` 精确选例，替代仅按日文子串匹配；示例性质单列展示。7251 保留为「对照（未新增：同值异记录披露）」，不混作新增。

| 批次 | row_id | 原始记录 | 展示值 | 校验 |
|---|---|---|---|---|
| C7-B1 | `30247-special_move-special_move-skilltext-lvorder3-f0` | bossskill 43024700 / skillparam1 | 0.75 | 通过（不再用旧后段 13.75／17.5 代替） |
| C7-B1 | `30258-special_move-special_move-skilltext-lvorder3-f0` | bossskill 43025800 / skillparam1 | 1.25 | 通过（不再用旧后段 17.5／20.5 代替） |
| C7-B3 | `351-denju-denju-denju_denju_id____cid-lvorder0-f0` | bossskill 40035100 / skillparam1 | 2.5 | 通过 |
| C7-B3 | `2331-denju-denju-denju_denju_id____cid-lvorder0-f0` | bossskill 40233100 / skillparam1 | 2 | 通过（不再用旧后段 3／3.5 代替） |
| C7-B3 | `30327-denju-denju-denju_denju_id____cid-lvorder0-f0` | bossskill 43032700 / skillparam1 | 15 | 通过 |

## R2：六个证据链接

`relative_href(output_dir, target)` 按实际输出目录计算项目根相对路径，六条均经文件存在验证：

- `../../../../docs/tasks/20261029-c7-p1-throughput-package.md`
- `../../review/c7_p1_final_20261029_deepseek/REPORT.md`
- `../../../../docs/tasks/20261030-c7-p2-throughput-package.md`
- `../../review/c7_p2_final_20261030_deepseek/REPORT.md`
- `../../../../docs/tasks/20261030-c7-p3-throughput-package.md`
- `../../review/c7_p3_final_20261030_deepseek/REPORT.md`

## 相关口径同步

- G1 改为「名单外新准入结构化，旧 25 行名单及兼容路径仍保留」，不再写成完全退出旧名单；不删除旧 G1 名单或旧答案。
- 剩余量页「近期候选」改为「历史待办（不构成下一包准入或授权）」，不得据此启动 20234 或扩大 30239 豁免。
- 看板过期摘要由「C7 剩余两批」统一为 C7 已完成 3 批、当前无在途任务、C7-P4 未启动。
- 文档残留核实：隔离复跑实际为 41 卡/82 文件（早期 README 写 40 卡/80 文件，覆盖只多不少）；code_snapshot/README 的 index「未改」为文字滞后，实际 `card_page_index.patch` 正确记录 EXPECTED_CAMPAIGN 变更；`checks/a7_run_record.json` 有 C7-P1 路径复制遗留，实际结果文件 29/29 正确。以上仅登记，不改历史独立审查报告或生产结果。

## 定向验证

- 五个示例 row_id／原始记录／展示值逐项核对通过；7251 示例性质已单列。
- 六条链接全部存在；无 `../../docs/`、`../../output/` 形式的错误链接。
- 生成后无「未找到示例行」。
- 浏览器展开答案后再次核对五个示例数值通过；剩余页文本与计数复核通过。
- 未修改生产脚本或重建页面，仅重生成 C7 展示产物。

**结论：展示层 R1/R2 已修复，申请原审查对话定向复审。**

## 定向复审结论（2026-10-30）

**PASS，两项整改均已关闭，无剩余必改项，可以收口 C7。** 复审独立确认：

- 五个示例的 row_id、原始记录与 HTML 展示一致：30247=0.75、30258=1.25、351=2.5、2331=2、30327=15，不再用旧后续段代替新增首段；
- 7251 明确标为「对照／未新增」；
- 六个任务书／独审链接 6/6 目标存在，生成器按实际输出目录计算相对路径；
- G1 已明确「名单外新准入结构化、旧名单兼容路径保留」；
- 剩余页候选已明确为历史待办，不构成下一包准入或授权。

原 REQUEST_CHANGES 报告和证据保留，不覆盖历史结论。此前通过的 35 条新增答案、type64 消费、排除规则、30110 交叉核、账本及签名结论保持有效，不重复审查或正式生成。原有范围限制继续保留：归属仍为推断、未实机验证最终效果、旧 G1 名单兼容路径保留、7251 同值异记录不升格、split 行不算完整；后续仍须 Y.G. 优先、有界选题。**本次仅完成收口记录，不自动启动 C7-P4 或下一周期，不启动 20234、不扩大 30239 豁免，不提交或推送 Git。**
