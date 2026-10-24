# 流程调整落地记录（依据 20261023-rectification-workflow-adjustment-request.md）

- 任务 ID：20261024-character-skills-workflow-adjustment
- 负责：主持 Kimi K3（整合者）；依据文件：`docs/tasks/20261023-rectification-workflow-adjustment-request.md`（流程评估对话 2026-10-23/24 合并版）
- 状态：**落地完成（文档与流程整合部分）＋五项补正完成**；F03 已落（meta 三脚本哈希）＋上游生成记录规则已明确待下次生成实施验证；F05/F08 自下一次回归/任务起生效
- 说明：本卡只记流程与文档整合，不代替数值工作审查结论；「文档已整合／代码产物已修改／独立验证完成」分列见末节。

## 当前真实流程与整改所处位置（§七.1 核实，2026-10-24）

- 当前真实流程：任务书→实施自检→四 cohort 并行重建＋账本＋选题链＋verify_full 17 项→DeepSeek 独立审查→修复→同会话复验→同步收官；**易反复整改自下一轮适用的复杂整改起按两段式（总方案 §5）**——本轮 R3 sentence 在 2026-10-24 版方案定稿前已按上一流程完成实施与正式生成，**从最终产物独立复验步骤接入**（见其任务卡，不冒称先前步骤已按两段式执行）。
- 当前整改做到哪：**R3 sentence 回退兄弟子句归属整改实施已完成**（workflow dwfrun-e77bb3f4 已收官：716 项主分类变化全部限 sentence 回退路径、~90→102 改判、外观债务落地；页面已重建至 campaign `c019af0b`，账本/选题锚点 `a2dc963c`——对应关系与旧证据适用范围见 progress.md 接手摘要）；**DeepSeek 独立复验进行中**（重派会话；首次会话因宿主崩溃中断），完成后由用户交原第三方复审。
- 仍待复验：R3 sentence 本轮全部结论（**DeepSeek 复验进行中——重派会话**；首次会话因宿主崩溃中断）；旧结论 R2/R3 root fix 已闭合（PASS_WITH_EXPLICIT_SCOPE_LIMITS）继续有效于其版本 `a2dc963c` 的送审范围（本轮改过的选题结果按本轮复验结论判定）。
- 版本对应：正式 pages campaign `c019af0b`（source `87c905a1…`，含并行重建驱动与该轮 b17/b6 注记修正）；ledger/backlog 快照 `a2dc963c-57a14d29`（R3 sentence 轮不改 effect_ledger.py）；verify_full_latest 归属版本以复验时实读为准。

## F01–F08 处置表

| 编号 | 处置 | 证据/位置 |
|---|---|---|
| F01 当前任务入口与状态不明 | **已解决**：进度文件顶部新增「接手摘要」（当前任务卡/审查/版本/下一步/停止边界一目可答）；本卡登记 R3 sentence 在途状态；`20261023-character-skills-r2r3-root-fix.md` 状态已在此前收官时更新；新建 `docs/tasks/20261024-character-skills-r3-sentence-fix.md` 为本轮任务卡 | progress.md 接手摘要节；本卡 |
| F02 验收文件分属不同版本 | **已解决（标注）**：A14 首部加所属版本标注（campaign a470c054 的历史终态，当前版本以最新复验为准）；总方案 §7 明确回归入口与「下一次回归带被测版本」规则；生成中只写「生成中/待验收」（见进度当前状态行） | acceptance/A14_final_state.md 首部标注；总方案 §7 |
| F03 选题代码版本不可证 | **已解决（当前代码哈希已核对）＋部分待下一次生成**：meta.generator_scripts 三脚本运行时 SHA-256 已落并实测一致；上游中间产物（view/enriched）生成版本本次无法追溯已如实标注；下一次正常生成按**三脚本旁置 run_record**（`<step>_run_record.json`，不改现有产物结构；每步记录脚本路径＋运行时哈希、直接输入及哈希/版本标识、输出位置＋哈希、上游记录指针、命令与时间）——最新安排见 R3 任务卡 F03 节与总方案 §7.1 末段 | yg_candidates.json meta；`docs/tasks/20261024-character-skills-r3-sentence-fix.md`；总方案 §7.1 |
| F04 正式依赖在临时/输出目录 | **已解决（清单补齐，补正后）**：总方案 §7.1 必要依赖表（8 个入口的路径/用途/必要输入/可重建性/保存规则）；「§F04」失效引用已修正为 §7.1；不得以哈希替代唯一源码/输入的保存；Git 提交另行授权，禁止强制 add work/output 全目录 | 总方案 §7.1 |
| F05 A7 结果版本对应不足 | **已解决（规则落地，下次回归起生效）**：总方案 §7 写明下一次回归运行须记录被测源码哈希、输入/页面版本、脚本哈希、命令与输出位置；A7 文档已注明；不重做旧修复（旧缺陷 25 例/路径问题已随文档债务包修复闭合） | 总方案 §7；acceptance/A7_rule_regressions.md 注记 |
| F06 旧分享清单自称"当前" | **已解决（标签）**：`output/character_skills/share_manifest_20261021/README.md` 标题与首段已加历史版本标注（绑定 b670cd42/推断 2,461 快照，非当前交付；保留旧 ZIP 不覆盖；无新分享授权不重打包） | 该 README 首部标注 |
| F07 容量保留机制纳入 | **已解决（纳入）**：机制规则七条已写入总方案 §8（限额、非全项目上限、生成前查询、失败处置、释放条件、保留集、清理候选≠授权、锁与签名关系）；已完成首轮清理（51.9865 GiB）作历史记录引用，不重复实施；149 历史引用 run 不处理 | 总方案 §8；scripts/storage_retention/README.md；docs/tasks/20261023-retention-cleanup.md |
| F08 耗时/消耗口径 | **已解决（自下一次授权任务起）**：总方案 §9 写明分阶段墙钟、返修次数、token 分口径或注明未知、禁止混合累计再求和、实测与估算区分（258s/97.5s 仅为页面段）；进度文件按此记账 | 总方案 §9 |

## 成本分析建议 A—E 的采纳（§六裁决）

A 选择式预检（采纳）；B 先稳定回归入口（采纳，A7 29 例已可运行）；C 分级验证按实际影响（采纳，总方案 §6）；**D 增量账本暂不实施**（先分段计时证明瓶颈与收益，规则变化时输入不变也可能需重算）；E 保留已验证并行（采纳）。依据：总方案 §10。

## 文档与流程整合清单（已落地文件）

1. `docs/角色技能完整解读实施方案.md`——2026-10-24 版全文修订（唯一当前规则入口；生效日、三方职责与模型配置/待定建议、验收目标、当前流程、两段式、分级验证、回归入口、容量保留、记账口径、A—E 状态、接入点；旧阶段安排/启动提示词/旧模型表降附录 B 历史）。
2. `docs/tasks/character-skills-progress.md`——顶部新增「接手摘要」（F01）；当前状态行与最新在途一致。
3. `output/character_skills/share_manifest_20261021/README.md`——历史版本标注（F06）。
4. `output/character_skills/effect_ledger/acceptance/A14_final_state.md`——所属版本首部标注（F02）。
5. `output/character_skills/effect_ledger/acceptance/A7_rule_regressions.md`——F05 版本记录要求注记（与文档债务包的 29 例修复衔接）。
6. `docs/tasks/20261019-character-skills-pivot-handoff.md`——顶部历史标记与当前入口指针（§零.3）。
7. `docs/tasks/20261023-rectification-cost-analysis-prompt.md`——首部「分析材料」标注（§零.4）。
8. `HANDOFF.md`——顶部加总方案与进度接手摘要入口（§零.5）。
9. `docs/tasks/20261024-character-skills-r3-sentence-fix.md`——本轮任务卡（F01）。
10. 本卡。

## 最近更新

- 2026-10-24：全部 F01–F08 处置落地（F03 当时标注为后续安排——已于同日五项补正中落地，见下条）；总方案 2026-10-24 版生效；HANDOFF/旧交接/分析材料/分享清单/A14/A7 标注完成。代码/产物修改：仅 F06/F02/F05 的标注类文本与本流程文档；无数值产物变化。独立验证：本轮无新数值审查（R3 sentence 复验待派）。
- 2026-10-24（**五项补正落地，依据方案调整审查对话复核结论「部分通过」**）：①状态与版本统一——progress.md 接手摘要与当前状态行按最新证据同步（R3 sentence 实施完成/复验在途；pages c019af0b、ledger/backlog a2dc963c、选题锚点同快照；「未改 effect_ledger.py 不证明无需复核」写明；不作永久最新硬写）；②F04 依赖清单补齐——总方案新增 §7.1 必要依赖表（选题三脚本/regen_readme28/a7_regression/并行驱动/run_retention/effect_ledger 的路径/用途/输入/可重建性/保存规则），「§F04」失效引用修正为 §7.1；③F03 上游关联——任务卡补记「当前代码哈希已核对」与「中间产物生成版本本次无法追溯」的区分（view 纯 list、enriched 空 meta 实测），下一次正常生成时 build_inventory/enrich_records meta 增直接输入 SHA-256＋来源快照（修改范围、负责人、验证方式已写明）；④F05 运行办法——A7_rule_regressions.md 注记升级为可执行步骤（固定写入路径说明＋运行前保存到 acceptance/results_history/<UTC>/＋新结果旁补 run_record.json 六要素；旧结果缺版本记录如实注明；状态＝运行办法已明确、下一次验证待执行，未重跑 A7）；⑤接入点与任务书版本——总方案 §5.0 新增任务书必须引用方案路径＋版本/日期并注明中途接入步骤；R3 任务卡补方案引用与「从最终产物复验接入、未完整执行两段式、不倒退重做」的如实说明。本卡 F03/F04 行按此更新。
- 2026-10-24（**三项最后补正落地，依据方案调整审查对话的复核回复**）：①当前区域统一——progress.md 接手摘要（旧证据适用范围收窄为原送审版本与已审范围、本轮选题结果按本轮复验判定）＋页面完成行（campaign a2dc963c→c019af0b＋对应关系）；本卡顶部状态行（F03 已落）＋§七.1 现状（R3 实施完成、复验重派进行中）＋「自本轮起按两段式」更正为「自下一轮适用的复杂整改起」（本轮从最终产物复验接入，不冒称）；首条更新记录的 F03 括号与「未送审」两处打架点修正。②F04 依赖表输入列按源码实读补齐（build_inventory：backlog＋characters.csv＋rules.json＋pages＋coverage_refined（诊断/冻结证据）；enrich_records：view＋records.jsonl＋pages＋ledger.jsonl；assign_candidates：enriched＋inventory_summary＋backlog＋ledger.jsonl＋metrics.json＋pages；其余条目同法核对），总方案 §7.1。③F03 写全——纠正「backlog.json 自带快照锚点」（实测纯列表，快照来自 metrics.json）；下一次生成的旁置 run_record 完整规范（每步：脚本路径＋运行时哈希、直接输入及哈希/版本标识、输出位置＋哈希、上游记录指针、命令与时间；链＝输入/快照→build_inventory→enrich_records→assign_candidates→最终候选）；最小修改范围＝三脚本各新增 run_record 写出、负责人＝下次选题链实施者、验证＝逐环核对；状态＝「记录要求和执行安排已明确，待下次正常生成实施验证」，不宣称为已可追溯。本轮未运行生成器、未执行清理、未新增数值审查结论、未重建页面。
