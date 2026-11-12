# C21：正式交付包任务卡

- 状态：**正式交付、正式独立终审与原冻结成果完成；C21-R01原第三方定向复验通过，F01／F02均CLOSED，阻断0；C21在明确范围限制下收口**。
- 写域：`output/character_skills/c21_delivery_20261111/`、`work/c21_delivery_20261111/`、本卡；正式共享pages/_batch已由唯一正式入口写入，后续不再生成。
- 当前版本：campaign `5492e173e3fa7c918eb3a2a701d6471e4a84246927e9450cf1cd99d3bc74e010`、snapshot `5492e173-cf9451c6ff47fcfb`；唯一一次jobs4全库生成，固定检查与525卡1050文件隔离复跑通过，正式独立终审23/23、阻断0。
- 成果：`output/character_skills/cycle_reports/C21/`，900答案台账及10文件manifest已完成，详细验证42/42；阶段收口`docs/tasks/20261112-c21-cycle-closeout.md`，第三方提示词`docs/tasks/20261112-c21-direction-review-prompt.md`。
- 共享接线由主持在候选独审无阻断后完成；C20后原基线SHA-256为`bfeaba72c19fd5753b87d4440936610e09e3adefac7ff30f2f66c3fe4c178b32`，接线后冻结SHA-256为`29d29f320083fa88cb6dce06041e55442e752aa8354de6cab072589a59c0b07f`。

## 正式接线前的迁址兼容修复

两批独立审查均通过，但真实build_card暴露既有共享代码的迁址遗留：C11—C20部分推断模块仍保存`output/cache_full_20261015_v3`逻辑常量，type8／cond用`parents[1]`解析`scripts/`证据导致差一级。主持将这些既有常量最小改为经`read_path`解析，脚本证据根改为`parents[2]`；不改规则、答案语义或历史来源字符串，不在内存中伪装正式通过。候选阶段登记的33处适配必须回落为可审计源码后，才允许接线和正式构建。

## 合并预检

A 冻结哈希、来源分源、候选与独审判决；B 独立重导900效果900答案及排除；C 真实Inputs/build_card边际、旧答案前缀、二次幂等、scope拒绝、保护卡和非目标行；D 真实analyze_row答案／效果／四档／A/C／split实测；E 当前RETAINED与8GiB／12run；F 正式脚本静态单次生成门。按C20单次构建的4个run估算，一次C21正式生成后为12/12、预约约8,030,405,403 B（低于8GiB），没有第二次全库构建余量；只认临前实测，不自动清理。

三轨只用于身份、来源和审查分工，不分别运行全库生成。合并预检全部通过后，保存C20后前像，执行**唯一一次**jobs4全库生成，再做正式账本、入口、F03、verify_full、A7、final_diff和隔离代表复跑。失败只许resume-post-build复用首次构建，不第二次全库生成。

DeepSeek Pro正式独审无阻断后才新增C21成果页配置并生成版本化成果、剩余量、机器数据与final_manifest。默认中文显示对象、倍率与必要条件，原文／raw／公式／指针／排除放展开层；同句未解效果继续就地披露。

不自动清理、Git提交／推送、公开发布或启动C22。第三方方向审查若REQUEST_CHANGES，停在findings，不自动整改或重建。
