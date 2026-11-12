# 第二批完整成果目录整理：执行前准备

- 用户要求：沿用既有调查，一口气推进至实际执行前，最多一次与主持交互，不实际搬迁。Sol执行准备、Astra独立复核。
- 本轮第二批指旧cache v1整体迁移之后的完整目录批次，不是阅读器B02批次。准确候选：`output/single` → `projects/unpack/history/single`（3文件／4,131,868 B）；`output/cache_full_20261015_v2` → `projects/unpack/data/cache/cache_full_20261015_v2`（95文件／118,170,246 B），同卷整体rename，内容／历史字段保留。
- 配套：v2复用读取器须按实际reuse-dir解析decoded成员，候选补丁和小夹具先验证；五个C14—C18 v2历史联接只准备切换／验读／回退，不当前操作。五入口接管和公共decoder写域集中在唯一主持交接中确认。
- 写域：本卡、`docs/project-layout/20261108-directory-batch2-ready-v1/`、新 `scripts/project_layout/batch2_directory_move.py`；公共decoder和导航只准备补丁，不合入、不移动、不切换、不删除，不提交／推送。
- 当前主线继续，v3／cache_refresh／phone链、pages／profiles／ledger、原件、vault、冻结P/v7与历史报告原位保护。其他候选不硬凑本批；packaging归档5317／11不再处置。
- 状态：技术准备与Astra独立复核完成，technical_blockers=0、ready_for_execution=false。两候选7+5项、工具11项夹具、98文件只读预检通过；正式脚本／源目录／五业务联接未修改。主持交互已用0/1，唯一提示词已备于交付目录host-handoff-prompt.md。
- 下一步：仅一次主持交接，闭合两根／五入口局部窗口、两源码及本批导航写域；再待用户最终物理授权。窗口内重新临前检查，不复用今天的准备PASS，不提交或推送。交付入口：docs/project-layout/20261108-directory-batch2-ready-v1/README.md。

## 物理执行接管（2026-11-08）

- 主持一次交接已闭合，见20261108-directory-batch2-host-handoff.md；主持不再并发合入或物理操作，本批两代码对应路径部分、局部ignore、项目导航和两根五入口由本执行对话负责。主线其他写域不变。
- 用户已明确最终授权，并将开始时间提前为清点后立即开始；仍以北京时间19:30截止，过期不顺延。授权原文见交付目录physical-20261108-v1/user-authorization.json。
- 状态：开始重新核对使用者和身份，准备最小合入代码／ignore及窗口内新98项预检；未据此声称迁移成功。Astra独立复核已派出。previous不删除，不提交／推送。

## 实际执行结果

- 2026-11-08 18:35:22.9908040—18:35:32.4754588北京时间，物理会话退出0；两目录98项／122,302,114 B同卷整体迁移完成，移动后3+95全SHA通过，五个v2正式入口均切至新根，五previous原身份停用保留、next不存在。
- 两正式代码与批准candidate精确一致；局部ignore完成，项目导航实际成功后更新，43本地链接无缺失，四共享根及主线基线未修改。Astra物理中间复核PASS，最终独审及完整回执见交付目录physical-20261108-v1/REPORT.md及physical-astra-review.json。
- 记录首次Git自动CRLF导致的SHA断言退出1：当时尚未物理移动，保留失败与中间前像，Astra核实仅换行后归一为精确candidate并通过新98预检。后续物理步骤无失败、无逆搬。附加文档补丁曾因上下文不匹配被拒绝，未改文件，正确上下文后合入。
- 主持交互已使用1/1，不再请求主持操作。没有本批文件删除、previous删除、旧空目录清理、Git提交／推送或其它批次操作。
- 收口：Astra最终独审PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0；物理与导航均已完成，最终验收在physical-20261108-v1/acceptance.json。剩余仅previous／旧空目录的另行处置及其他批次，不属于本次迁移待办。
