# C20-F01-R02：描述来源父与本答案分支父标记

- 日期：2026-11-09；收口：2026-11-11；状态：**F01=CLOSED；原Sol R02定向复验PASS_WITH_EXPLICIT_SCOPE_LIMITS，565/565，阻断0**。
- 前次复验：原生 `gpt-6.1-sol/high` 沿用原审查上下文；F01=OPEN、REQUEST_CHANGES，380项中373通过、7项父标记失败，聚合1个阻断。该历史裁决保留。
- 最终复验：`output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_r02_v01/REPORT.md`／`verdict.json`；父代理验收：`work/c20_post_closeout_independent_recheck_20261109/f01_recheck_r02_v01/parent_acceptance.json`。
- 本轮只修展开层父标记语义，不重开数值研究，不纳入N01。

## 写域与并行边界

- `scripts/character_skills/cycle_report.py`：只按 `binding.current_parent` 和 `binding.selected` 统一标记全部25答案，并新增C20_R02展示配置。
- `docs/tasks/20261109-c20-f01-parent-marker-r02.md`：本卡。
- `work/c20_f01_parent_marker_r02_20261109/`：试点、隔离重跑和验证中间件。
- `output/character_skills/rectification_c20_f01_parent_marker_r02_20261109/`：验证器、finalize、整改说明、25答案台账和送审提示词。
- `output/character_skills/cycle_reports/C20_r02_20261109/`：新版展示与清单。

当前生成器SHA-256 `6516f3b3f9fbafa09435f025091265f6d9faafb28477842d542fcdb4d8fe3bd9`，与R01 manifest封印一致。统一output物理迁移已完成并允许主线在新进程继续；本任务不接管其路径、清理或导航写域。

## 硬边界

1. `current_parent`只标为“当前描述来源父”；`selected`对应父只标为“本答案分支父”。两者相同则同一父同时保留两种标记，不同则分别落在对应父项。
2. 不按CID硬编码，不用答案record_id推定父pattern。pattern_id与子record_id分别识别；20619必须是父42061901→子record42061902。
3. 保留完整父集合顺序、原始条件、children、6项合并、2项排除及全部来源字段和理由，不修改机器答案或binding。
4. 原C20、C20_r01、原v05、f01_recheck_v01及其manifest／裁决全部保留，不覆盖。
5. 不修改正式pages、rules、effect_ledger或25答案；不运行正式生成、corrective-rebuild、resume、清理、Git、发布、C21、新缓存、新原生或实机。
6. 默认玩家层不增加研究字段；15行21项拆分继续默认披露，12226精确raw不变。浏览器、新原生和实机继续UNTESTED。
7. 新版保持 `IMPLEMENTED_PENDING_ORIGINAL_SOL_RECHECK`、`original_sol_recheck=PENDING`。原Sol明确F01=CLOSED及PASS_WITH_EXPLICIT_SCOPE_LIMITS后才更新主持收口。

## 定向验收

1. 同一row、同一record定位25答案展开块；分别核对两种父标记的身份、数量及所在父项。
2. 七条反例逐项闭合，其余18条两种标记同父且无回归。
3. 25份父集合、6项合并、2项排除和原三个反例继续通过。
4. 机器batch_results、正式pages答案、旧答案前缀、默认层和精确raw不变。
5. 新版11个登记文件（含25答案JSON／CSV台账）逐项核字节和SHA-256；manifest／handoff不登记自身、无循环哈希。
6. 隔离生成与验证只写本任务work；主持自测不替代原Sol独立复验。

## 当前整改回执

- 新版：`output/character_skills/cycle_reports/C20_r02_20261109/`；原C20、R01、v05和f01_recheck_v01未改。
- 全部25答案均有“当前描述来源父”和“本答案分支父”各1个标记；7条异父分别落位，其余18条同父双标记，旧“当前选中父”不出现于R02。
- 25答案record均属于selected父children；20619为pattern1／42061901→首个伤害子record 42061902，完整children未删减。
- 定向验证41/41 PASS，独立空目录“生成＋41/41验证”通过；25份父集合、6项合并、2项排除和原三个反例继续通过，2,356个保护文件零写入。
- 首轮40/41是验证器误把20619 children限定为单record，已保留attempt1；只修专项断言，不改HTML或机器数据。
- 25答案JSON／CSV台账、展开审计和41项详细验证均随新版提供；manifest登记11文件。
- manifest SHA-256 `2def5740d286d193cccea0b4d88aefe4c2a1fae830e7593a809dc6710434d553`；handoff SHA-256 `fec08de8f036dec526e541d505d74b1ed0bcf6cb80018a70b173e01264f5fdf0`。
- 整改说明及原Sol复验提示词：`output/character_skills/rectification_c20_f01_parent_marker_r02_20261109/README.md`、`SOL_R02_RECHECK_PROMPT.md`。

## 最终独立复验收口（2026-11-11）

- 原Sol沿用原审查上下文，最终 **F01=CLOSED、PASS_WITH_EXPLICIT_SCOPE_LIMITS、565/565、阻断0**；25条答案全部独立解析，只读引用答案0，主持41/41未替代独立结论。主审查、隔离展示生成及入口自检均退出0。
- 7条异父、18条同父、原三个反例、25份完整父集合、6项合并、2项排除、不变量及11文件清单全部通过；R02 manifest/handoff送审哈希与独立重算一致。
- 当前成果入口：`output/character_skills/cycle_reports/C20_r02_20261109/`。原v05与`f01_recheck_v01`的REQUEST_CHANGES／F01 OPEN保留，由本轮最终复验承接；R01/R02清单和handoff中的PENDING仅表示送审时点，不回写消除。
- N01仍为非阻断且未纳入。浏览器视觉／交互、新原生及实机继续UNTESTED；静态解析与隔离展示复现不构成视觉或运行时验证。本轮仅登记收口，不重建成效，不启动C21、清理、Git、发布、新缓存、新原生或实机。
