# 第二批完整目录整理：执行前交付

当前状态：**两目录迁移、五入口切换及导航整合已实际完成；最终回执见下列物理执行入口。** 下方准备材料仍保留当时状态，不把准备预检当实际执行证据。

- [实际执行报告](physical-20261108-v1/REPORT.md)、[逐项迁移](physical-20261108-v1/migration-files.jsonl)、[实际路径映射](physical-20261108-v1/actual-path-map.json)
- [实际执行结果](physical-20261108-v1/execution-result.json)、[导航与43项链接检查](physical-20261108-v1/navigation.json)
- [实际执行Astra独审](physical-astra-review.json)、[最终验收](physical-20261108-v1/acceptance.json)

本批已将 `output/single` 和 `output/cache_full_20261015_v2` 同卷整体迁出，共98文件、122,302,114 B。当前v3和主线继续使用现址；未删除文件、未复制大载荷，五个v2 previous停用保留。

- [范围、引用、空间、验证和恢复说明](REPORT.md)
- [唯一一轮主持交接提示词](host-handoff-prompt.md)：整段转发一次，主持只确认范围与交接，不另行执行
- [准备阶段Astra独立复核](astra-review.json)：当时技术阻断0、`ready_for_execution=false`；实际结果使用上方新物理独审
- [98文件及五历史入口冻结前像](source-inventory.json)、[历史路径外部映射](path-map.json)
- [只读准备预检](tooling/preflight.json)、[候选源码身份](consumer-code-binding.json)
- [候选解码器补丁](decoder-reuse.patch)、[候选校验器补丁](verifier-path.patch)
- [执行手册](tooling/README.md)、[具体命令](tooling/runbook.md)、[连续PowerShell模板](tooling/runbook.ps1.txt)、[失败与恢复](tooling/recovery.md)
- [仅成功后应用的导航补丁](navigation-after-success.patch)、[导航与局部忽略规则说明](navigation-preparation.json)
- [22项执行材料身份绑定](tooling/bindings.json)、[工具验证](tooling/verification.json)、[本轮收尾验收](acceptance.json)

不重复第一批v1迁移或已完成的打包支线退役。准备预检不能代替未来窗口内的新预检，技术PASS不能代替主持实际交接和用户授权。本文及 REPORT、交接提示词、acceptance 是整合说明，不修改已绑定的执行材料。
