# 唯一一轮主持交接提示词

请一次性确认第二批目录整理的局部交接，由执行对话统一实施后续补丁、迁移、验收与导航，主持不另行操作；主线研究、正常生成与校验继续。本轮只回复一次完整回执，不逐步来回协助。

项目根：`E:\代码项目\锁链战记数据解包`

先读 `docs/project-layout/20261108-directory-batch2-ready-v1/` 中的 README.md、REPORT.md、astra-review.json、consumer-code-binding.json，以及 tooling/runbook.md、tooling/recovery.md。技术准备及Astra复核已通过，无需重做全量调查或已通过测试。执行材料由 tooling/bindings.json 绑定。

本批仅：

1. `output/single` → `projects/unpack/history/single`，3文件、4,131,868 B。
2. `output/cache_full_20261015_v2` → `projects/unpack/data/cache/cache_full_20261015_v2`，95文件、118,170,246 B。

请在同一回执中闭合以下事项：

- 核实两源根当前没有相关读写者；特别检查显式 `--output output/single`、`--reuse-dir` 指向v2、analyze／verify的 `--input` 指向v2，以及尚未登记的新任务。无法确认时指出具体使用者，不能仅凭旧周期收口认定闲置。
- 确认下面五个v2入口的实际接管者及无使用状态，将本批局部窗口的调度交给执行对话：用户最终物理授权后，由执行对话确定并记录一次不超过30分钟的窗口和实际UTC起止，开始前再核当前使用者；不需第二轮主持确认。若不能这样安排，请本次直接给出有效固定窗口及限制，过期不顺延。
  1. `work/c14_delivery_20261103/impl/isolation_input/output/cache_full_20261015_v2`
  2. `work/c15_delivery_20261103/impl/isolation_input/output/cache_full_20261015_v2`
  3. `work/c16_delivery_20261104/impl/isolation_input/output/cache_full_20261015_v2`
  4. `work/c17_delivery_20261106/impl/isolation_input/output/cache_full_20261015_v2`
  5. `work/c18_delivery_20261106/impl/isolation_input/output/cache_full_20261015_v2`
- 审阅并批准 decoder-reuse.patch、verifier-path.patch，将 `scripts/decode_cache_snapshot.py` 的reuse路径部分及 `scripts/verify_cache_snapshot.py` 的对应路径部分交执行对话最小整合，不再并发修改这些部分。仅改显式新根解析，保留SHA／native校验，不运行旧冻结验证或重建数据；两候选和精确前像身份在consumer-code-binding.json。
- 将 `projects/unpack/README.md` 本批导航，以及 `projects/unpack/data/cache/.gitignore`、`projects/unpack/history/.gitignore` 的本批增量规则交执行对话整合。导航仅实际成功后更新，保留并发内容；不改根.gitignore，不整文件覆盖。四共享根本批无需更新，主线其他写域保持原分工。
- 确认两rename存在正式名短暂空档、五previous只停用留证；迁出后不指回空旧根。范围不含删除、v3／latest／当前pages／profiles／ledger、原始输入、归档5317／原位11项、P/v7、四plan及binding或share_bundle入口。

请一次回复：实际接管者、检查时间与使用者证据、可交接写域、两补丁批准与否、窗口安排和全部已知冲突。无需执行迁移、联接切换、补丁合入、生成、提交或推送。

本交接不是用户最终物理授权。执行对话取得用户授权后，还必须在有效窗口内产出新98项预检、核代码／来源漂移再开始；任何未闭合项均先停止受影响步骤，不干扰主线。
