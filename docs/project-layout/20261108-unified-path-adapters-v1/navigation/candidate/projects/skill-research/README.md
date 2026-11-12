# 技能数值研究导航

## 统一迁移后研究入口（统一迁移验收后）

统一迁移仅在 31 棵完整目录、2 个 latest 控制文件、读取与写入适配、别名及保护契约通过最终验收，并按单独授权安装 `scripts/project_layout_active.json` 后作为当前物理布局。合入后，原 CLI 的已适配逻辑路径默认解析到新根，无须每次手设环境变量；未适配命令仍须按各自验收回执核对。冻结清单中的旧来源字符串保留原值；不能把迁址当作重新生成或重新签名。 [Boss证据](evidence/boss_chain/)、[治疗证据](evidence/boss_heal/)、[普通效果](evidence/ordinary_effects/)、[30236对照](evidence/card_comparison_cid30236/)、[名册](data/char_roster/)、[结构化数据](data/structured/)、[field_guide](reports/field_guide/) 和 [规模实验](experiments/skill_mechanism_scale/)、[机制试验](experiments/skill_mechanism_trial/)和[路线实验](experiments/skill_route_experiments/)按完整旧根各自迁入新容器；`phase_d` 与 `sample` 亦在 `evidence/`。正式 `output/character_skills/` 整根保留原位：其中两份 share_manifest 属11项原位锚点，rules/pages/ledger/campaign 仍按原事务和签名。历史 C19/C20、P/v7 与旧审查结论保持原字节和原版本；下面 B00 历史观察不当作当前搬迁许可。


## 2026-11-08 打包退役的研究维护入口

整条旧打包支线已停用，尚未物理删移；完整6,935项去向见[整支清单](../../docs/project-layout/20261108-packaging-full-retirement-v1/README.md)，本轮准备入口为[运行适配与交接](../../docs/project-layout/20261108-packaging-runtime-ready-v1/README.md)。根README／AGENTS／HANDOFF／STATUS的新全范围补丁[待主持合入](../../docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/shared-navigation.patch)。这不改变主线规则、答案、账本或下一周期安排。

当前研究交接仍原位保留在 `output/share_bundle/20261104-mechanism-first-handoff-r1/`，139个存续研究文件（payload内135成员及manifest、外侧3件）必须完整保留；同目录ZIP属拟退役项，不计入139。新只读维护入口为 `scripts/project_layout/retirement_runtime.py`（使用方法见本轮准备记录），不得依赖旧默认路径无参数重放。未来归档参数拟为 `operations/history/retired-packaging/20261108/share_bundle/20261104-mechanism-first-handoff-r1/payload`；该目标尚未落地，不能作为当前可读链接或已迁址结论。未来需历史对账时显式传新 `--bundle` 与独立 `--output`，按当时snapshot重新核验，不改旧回执。

C14—C18的5个历史隔离share_bundle入口仍真实联接旧根，需[逐入口交接](../../docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/junction-owner-handoff.json)确认无人使用并由隔离契约整合者接管短窗口。只冻结这5个历史入口的使用，主线研究可继续。B00/B01和原周期报告保持冻结。

职责：解释角色每条描述对应的数值、单位、条件和可信度，保留来源与未知项。本页是 B00 六项目导航之一；六目录仅提供原位导航，没有迁移文件，也不是六个独立可运行包。

本轮版本：[B00 总览](../../docs/project-layout/20261107-b00-v1/README.md) · [本项目全部900条映射](../../docs/project-layout/20261107-b00-v1/skill-research.md) · [全1140条机器索引](../../docs/project-layout/20261107-b00-v1/index.json)。基线为[20261106 path-map](../../docs/project-layout/20261106/path-map.json)，更具体子行优先于父目录；归属不授予迁移或写入权限。

## 从这里读取

| 用途 | 原位入口与版本含义 |
|---|---|
| 当前方法和状态 | [实施方案](../../docs/角色技能完整解读实施方案.md)、[唯一进度看板](../../docs/tasks/character-skills-progress.md)、[根交接](../../HANDOFF.md) |
| 当前规则与逐卡答案 | [profiles/rules.json](../../output/character_skills/profiles/rules.json)、[pages](../../output/character_skills/pages/)，如[30236 card.json](../../output/character_skills/pages/30236/card.json) |
| 当前生产消费链 | [card_page_data.py](../../scripts/character_skills/card_page_data.py) 调用 [rules.py](../../scripts/character_skills/rules.py) 的 `answer_for`；同级模块及固定根目录深度仍有耦合 |
| 签名与账本 | [campaign_latest.json](../../output/character_skills/pages/_batch/campaign_latest.json)、[effect_ledger](../../output/character_skills/effect_ledger/)；latest 内 report 按 pages 根下相对路径解析 |
| 解码主表输入 | [cache_full_latest.json](../unpack/data/cache/cache_full_latest.json)、[缓存20261015_v3](../unpack/data/cache/cache_full_20261015_v3/)、[APK内置主表](../unpack/data/apk/base_master/)；不同来源保持分开 |
| 历史单卡查询 | [query_effect_dictionary.py](../../scripts/query_effect_dictionary.py) 只读既有30236参数视图与 records，不读取当前 profiles/rules.json 或各卡新答案；统一只读 CLI 尚未交付 |
| 展示消费者 | [阅读器导航](../reader/README.md)；中文审查和界面验收不升级解析结论 |

## 版本与任务保护

2026-11-07 本地读取时，[C19周期卡](../../docs/tasks/20261107-c19-cycle.md)及[交付卡](../../docs/tasks/20261107-c19-delivery-package.md)记录：候选独审通过，主持最小接线与内存消费复核完成，交付脚本准备中，正式全库生成0次。133卡407答案／407效果是该阶段复核记录，不是已正式交付收益。C18 后基线为 snapshot `01c05f78-cf9451c6ff47fcfb`、rules 294键；实际后续状态以任务卡和版本回执为准，不能用旧映射 T02 的规划状态代替当前记录。

保护用户指定的 ZCode `session_484fe26880b140801f3734c1a724c9f8`／C19 与 CodeX Web 阅读器任务。这里仅观察本地任务卡和产物，没有独立核实任务卡作者与聊天身份，也不能据此判断聊天是否停工或移交。

正式 `pages/<cid>/card.json`、`index.html`、receipt、blocker、backup 和 `_batch` 属现行同一事务；旧 card 还参与输入和指纹。不得按 JSON／HTML 或“研究／展示”归属拆开。campaign、rules 哈希、页面和账本须同版；在途消费者仍读取原路径时不切指针。

研究还依赖 APK 工作根、恢复镜像／重定位／symbols、字段字典和 trace 等共享证据；依赖范围见[版本索引](../../docs/project-layout/20261107-b00-v1/skill-research.md)及[耦合审计](../../docs/project-layout/20261106/audit/coupling-report.md)。同内容或静态字符串命中不能证明可去重、可独立运行；历史隔离目录中的 Windows 联接可能直接指向当前 scripts／output。

历史周期、独立审查、冻结输入和 before/backup 的意义按各自版本保留，不用当前数字改写旧报告。B00 仅检查文档与链接，不运行业务脚本、构建、验证或准备流程，不启动后续批次。
