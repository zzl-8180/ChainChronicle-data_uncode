# 统一迁移：候选完成后的补充验证

- 目标：回应用户对“能做是否都做了”的复核；前阶段完成的是候选和限定测试，不能据此说全部可独立验证都完成。补齐最终v4真实模型、命令失败写域、reader真实事务边界；不无限增加无关测试，不全库重跑。
- 写域：`docs/project-layout/20261108-unified-path-validation-v2/` 及本卡。原v1的47封印、代码、审查、baseline不改；正式代码、数据、四共享根、指针、业务junction、previous均不动，不提交推送。主持交互仍0/1。
- 分工：root模型回归／临时源码与五测试入口的精确卸载／合并交接；Sol research只管reader；Sol unpack只管command-edges；Astra只读复核及新v2/astra-review。彼此不回滚或占用他方写域。
- 实际：最终v4 query和350/30236/30239模型四进程exit0、payload与同轮输入锚点一致；真实源读取逐SHA绑定。临时646份源码31,586,695 B按SHA/独立inode精确清掉、五自建testjunction按ID/tag/target移除，v1原件及targets未变。
- 新发现：prepare_review遗漏新物理路径与数据入口，Sol在v2独立fork修复；最终有效候选需v1-v4加新单文件修复，不能继续只给v4补丁。reader真正成功seal/publish要求完整真实审查回执，不允许手填PASS或绕门；只做真实小数据来源与失败/身份保护边界测试。
- 状态：补充验证、prepare候选修复和Astra增量独审完成；PASS_TARGETED_VALIDATION_AND_FOLLOWUP_CANDIDATE_WITH_EXPLICIT_LIMITS。新HOST_PROMPT已合并为唯一当前入口，最终37核心封印通过；已知独立必要工作可收口，完整发布能力未验、真实交接/授权/临窗仍开。主持交互0/1，未搬文件。
