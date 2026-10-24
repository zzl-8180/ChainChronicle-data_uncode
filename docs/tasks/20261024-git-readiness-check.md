# Git提交准备检查（2026-10-24）

仅检查和建议，不暂存/提交/推送、不迁移源码、不清理文件。依据用户本轮要求及AGENTS.md §4/§7/§8；不解除历史Git写入冻结。以下基础数量来自本轮文档新增前的工作树，新增本报告及YG1第三批提案后任务文档另增2份。

## 结论

轻量源码仓库的取舍符合项目实际；**现有HEAD不能完整代表当前本地成果，也不能只提交已跟踪文件后称当前版本完整入库**。最后提交`b297118`（2026-10-22），其前状态入口仍在批9阶段；工作树实际已到批17整改闭合及YG1第二批。当前无暂存变更。已跟踪266文件，工作树实际文件合计6,689,349 bytes，最大文件1,374,485 bytes；体积不是目前的主要障碍。

## 提交候选及边界

| 类别 | 实查范围 | 建议 |
|---|---|---|
| 核心生产源码 | 10个已跟踪修改＋12个未跟踪新模块 | 适合优先准备成依赖闭合的一组，保留各自批次/整改说明；不能只挑YG1文件或只提交已跟踪diff |
| 方案及状态/任务文档 | 已跟踪4份文档修改；未跟踪42份任务文档，另加本轮2份 | 当前方案/进度/必要交接与已完成任务记录适合纳入；历史提示词、事故/分析记录按各自身份筛选，不能把“计划待实施”写成已实现 |
| 参考分析脚本 | 38个未跟踪文件，约295KB，含scripts/refcheck_20261023_lead/ | 可作为研究源码单独筛选；部分硬编码本机路径并依赖外部参考包，不是生产解析器或独立工具完成证明。原件不入库，注明输入与许可边界 |
| 容量/事故相关源码 | scripts/storage_retention/下16文件，约166KB | 只读盘点、replay_guard及必要测试可评估单列；历史cleanup/restore/recovery及本机pins不是通用默认动作，不与主线顺手整目录提交，不自动运行 |
| 本机异常/生成内容 | 未跟踪nul；raw/work/output/工具/环境/原始APK等 | nul不提交、不在本次删除。大资源、运行输出与环境继续按.gitignore排除，成果通过声明的发行包/来源映射保留 |

核心修改：`card_page_batch.py`、`card_page_data.py`、`card_page_index.py`、`card_page_inference_b6_bossbuff.py`、`card_page_inference_b8_crit2012.py`、`card_page_inference_b9_debuff.py`、`card_page_policy.py`、`card_page_render_v2.py`、`card_page_verify_full.py`、`rules.py`（均在scripts/character_skills/）。

核心新增：`card_page_batch_parallel.py`、`card_page_inference_b10_sa2003.py`、`card_page_inference_b11_sa1095.py`、`card_page_inference_b12_1095ext.py`、`card_page_inference_b13_apkext.py`、`card_page_inference_b14_apkext.py`、`card_page_inference_b15_union.py`、`card_page_inference_b17_p0finale.py`、`card_page_inference_yg1.py`、`card_page_inference_yg1_timing.py`、`effect_ledger.py`、`run_retention.py`（同目录）。AST只读核对确认当前data/render/verify/batch直接或间接导入其中多个未跟踪模块。

4份已跟踪文档修改为HANDOFF.md、docs/角色技能完整解读实施方案.md、docs/tasks/character-skills-progress.md及20261019-character-skills-pivot-handoff.md。当前模型/阶段应以顶部现行入口为准，旧配置及旧数字按历史保留，不批量改写。

## 仓库与实际工程的缺口

1. 以下5个必要源码实存但被忽略且未跟踪：`work/character_skills_yg_priority/{build_inventory,enrich_records,assign_candidates}.py`、`work/character_skills_goal_rectification/regen_readme28.py`、`output/character_skills/effect_ledger/acceptance/a7_regression.py`。方案§7.1已列依赖；提交生产主线源码时必须同步声明这些缺口，不能声称选题/验收链都已随仓库提供。后续专门整合可给它们建立scripts/下受控入口或纳入发布工具包，更新引用；本次不迁移，不全目录强制添加work/output。
2. 正式profiles/rules.json、页面/账本/候选、原生证据及原始数据位于被忽略目录。它们不必全进Git，但最终交付清单须说明随B包提供、生成方式或用户输入要求，避免“仓库可运行”依赖作者本机历史成果。
3. 生产源码和近期任务有既有语义/机器验收证据，本次没有重新全量验证、建立干净Git检出复现或逐行审定全部历史改动；“提交候选”不等于已完成发行验收。仅对本轮待提交文本作私钥头/明显凭据赋值/设备标识的有限模式筛查，0命中，不当作全仓历史安全审计。

建议顺序：先准备核心源码及对应任务/状态文档的工作区研究快照，再单列参考分析/容量历史源码；若要求成为可独立复现发行版本，先补必要源码与声明依赖的交付入口及隔离检查。未来提交按显式文件清单分组，不用git add .、不接管别人的未提交改动，不自动推送。本检查不是清理/打包/发布专项的启动。

2026-10-24后续：用户已明确授权“按照你的建议提交Git并推送，然后进入下一批”。本检查是授权前快照，上述冻结/缺口结论按当时记录保留；5个必要脚本的受控源码入口已补至scripts/character_skills_pipeline/，旧源码及正式产物不改。实际提交范围、检查及推送结果见20261024-git-mainline-sync.md，不再将先前冻结作为本次已授权操作的阻碍。
