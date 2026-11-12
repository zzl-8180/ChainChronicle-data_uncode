# C20-F01：完整父集合与合并／排除分支展开披露

- 日期：2026-11-09；状态：**R01父集合整改已完成；后续7条父标记问题由R02修正，F01于2026-11-11经原Sol最终复验关闭**。
- 原审查：原生 `gpt-6.1-sol/high` 全新独立上下文；目录名中的deepseek仅为既有写域。最终结论REQUEST_CHANGES，349项中348通过、唯一阻断F01。
- 原报告：`output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/v05/REPORT.md`；父代理验收：`work/c20_post_closeout_independent_recheck_20261109/parent_acceptance.json`。
- 本轮只修成果HTML展开层；25答案、18效果、数值、条件、证据等级、正式campaign／snapshot均不变。N01非阻断且不纳入。

## 写域

- `scripts/character_skills/cycle_report.py`：仅在现有 `show_scope` 展开层消费机器答案已有的 `complete_parent_set`、`merged_disclosures`、`excluded_branch_values`，并新增C20_R01展示配置。
- `docs/tasks/20261109-c20-f01-expanded-parents.md`：本卡。
- `work/c20_f01_20261109/`：定向验证、确定性重跑与finalize脚本。
- `output/character_skills/rectification_c20_f01_20261109/`：整改说明和验证回执。
- `output/character_skills/cycle_reports/C20_r01_20261109/`：新版本成果、清单和交接验证。

共享 `cycle_report.py` 当前已有C20修改，SHA-256 `a71ec711e34de8db1a3b885b9c1d7048b9a0575b8a60acee2a688aa478f15f5d`。统一output任务只读／候选重基明确要求保留这些新增；本任务只增量修改展示逻辑，不接管其路径写域。

## 硬边界

1. 不修改正式答案、rules、effect_ledger或正式pages；不运行正式全库生成、corrective-rebuild或resume。
2. 不覆盖 `output/character_skills/cycle_reports/C20/`、原Sol审查或任何历史报告／manifest。
3. 默认玩家文案继续不泄漏raw、公式、表名和指针；完整研究信息只放展开层。
4. 每条答案按机器数据顺序展开完整父集合、原始条件和子记录；合并／排除分支展开pattern、record、raw、来源指针和理由。
5. 定向验证覆盖25答案、12032／12236／20619三个明确反例、正式pages一致性、15行21项行级拆分、默认层边界、确定性重跑和新清单哈希。
6. 静态HTML解析不写成浏览器视觉验收；浏览器、新原生和实机继续UNTESTED。F01经原Sol关闭前，不更新主持为最终收口，不启动C21、清理、Git、发布、新缓存或其他研究。

## 当前整改回执

- 新版：`output/character_skills/cycle_reports/C20_r01_20261109/`；原C20和原Sol v05未改。
- 25份完整父集合、6个合并披露、2个排除分支均逐答案进入展开层；12032／12236／20619三个反例闭合于各自答案块。
- 定向验证29/29 PASS；独立空目录“生成＋29/29验证”通过；2,334个保护文件零写入，C19_R01 407个非目标答案块回归一致。
- 首轮27/29和第二轮28/29是验证器路径比较／C19重跑口径问题，失败回执保留；最终没有放宽F01检查。
- manifest：`output/character_skills/cycle_reports/C20_r01_20261109/final_manifest.json`，SHA-256 `150705f31744a006bbf7638ae095e6da953ba759d1bd9612b291387558256389`。
- handoff：SHA-256 `b1b9cf4d7f585bd54345069aedacb380e84ec5bc8b5f3daa7c6a7bd4d98348ae`；`original_sol_recheck=PENDING`。
- 整改说明与复验入口：`output/character_skills/rectification_c20_f01_20261109/README.md`、`SOL_RECHECK_PROMPT.md`。

## 后续承接与最终状态（2026-11-11）

- 原Sol在`f01_recheck_v01`确认R01已补齐25份父集合、6项合并、2项排除和原三个反例，但发现7条答案把描述来源父误标为选中父；该REQUEST_CHANGES／F01 OPEN历史保留。
- R02按`current_parent`与`selected`统一区分“当前描述来源父”和“本答案分支父”，见[R02任务卡](20261109-c20-f01-parent-marker-r02.md)。原Sol最终R02复验 **565/565、F01=CLOSED、PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0**。
- 当前成果入口为 `output/character_skills/cycle_reports/C20_r02_20261109/`；R01仅作历史版本，不再作为当前展示入口。R01/R02清单、handoff及旧报告中的PENDING／OPEN均保留送审时点，由最终复验与C20收口记录承接。
