# 技能数值研究导航

## 正式成果与研究证据

[正式规则](../../output/character_skills/profiles/rules.json)、[逐卡答案](../../output/character_skills/pages/)、[效果账本](../../output/character_skills/effect_ledger/)和 campaign 继续在 `output/character_skills/` 使用同一套版本。研究材料位于本项目的 [Boss 证据](evidence/boss_chain/)、[治疗证据](evidence/boss_heal/)、[普通效果](evidence/ordinary_effects/)、[30236 对照](evidence/card_comparison_cid30236/)、[名册](data/char_roster/)、[结构化数据](data/structured/)、[字段指南](reports/field_guide/)及[退役实验独有证据](evidence/retired-experiments/20261113/)。S6停止独立维护；84项独有证据及169项替代关系见[精确来源映射](../../operations/records/cleanup-retirement/20261114-execution-r1/source-locations.json)。

## 退役打包支线的研究归档

139份机制交接材料现位于[机制交接证据](evidence/mechanism-first-handoff/20261104/)。C14—C18的五个旧share_bundle联接已退役，旧retirement_runtime及六个历史工具不作现行入口。冻结manifest、计划和历史报告不改；新旧路径、真实TARGET/POST及阶段审查见[本次清理回执](../../operations/records/cleanup-retirement/20261114-execution-r1/REPORT.md)。

历史版本索引：[B00 总览](../../docs/project-layout/20261107-b00-v1/README.md) · [本项目全部900条映射](../../docs/project-layout/20261107-b00-v1/skill-research.md) · [全1140条机器索引](../../docs/project-layout/20261107-b00-v1/index.json)。基线为[20261106 path-map](../../docs/project-layout/20261106/path-map.json)，更具体子行优先于父目录；归属不授予迁移或写入权限。

## 从这里读取

| 用途 | 入口与版本含义 |
|---|---|
| 当前方法和状态 | [实施方案](../../docs/角色技能完整解读实施方案.md)、[唯一进度看板](../../docs/tasks/character-skills-progress.md)、[根交接](../../HANDOFF.md) |
| 当前规则与逐卡答案 | [profiles/rules.json](../../output/character_skills/profiles/rules.json)、[pages](../../output/character_skills/pages/)，如[30236 card.json](../../output/character_skills/pages/30236/card.json) |
| 当前生产消费链 | [card_page_data.py](../../scripts/character_skills/card_page_data.py) 调用 [rules.py](../../scripts/character_skills/rules.py) 的 `answer_for`；同级模块及固定根目录深度仍有耦合 |
| 签名与账本 | [campaign_latest.json](../../output/character_skills/pages/_batch/campaign_latest.json)、[effect_ledger](../../output/character_skills/effect_ledger/)；latest 内 report 按 pages 根下相对路径解析 |
| 解码主表输入 | [cache_full_latest.json](../unpack/data/cache/cache_full_latest.json)、[缓存20261015_v3](../unpack/data/cache/cache_full_20261015_v3/)、[APK内置主表](../unpack/data/apk/base_master/)；不同来源保持分开 |
| 历史单卡查询 | [query_effect_dictionary.py](../../scripts/query_effect_dictionary.py) 只读既有30236参数视图与 records，不读取当前 profiles/rules.json 或各卡新答案；统一只读 CLI 尚未交付 |
| 展示消费者 | [阅读器导航](../reader/README.md)；中文审查和界面验收不升级解析结论 |

## 版本与任务保护

周期进度以[唯一进度看板](../../docs/tasks/character-skills-progress.md)为准。[C19 周期卡](../../docs/tasks/20261107-c19-cycle.md)与[交付卡](../../docs/tasks/20261107-c19-delivery-package.md)记录各阶段的历史状态。

正式 `pages/<cid>/card.json`、`index.html`、receipt、blocker、backup 和 `_batch` 属现行同一事务；旧 card 还参与输入和指纹。不得按 JSON／HTML 或“研究／展示”归属拆开。campaign、rules 哈希、页面和账本须同版；在途消费者仍读取原路径时不切指针。

研究还依赖 APK 工作根、恢复镜像／重定位／symbols、字段字典和 trace 等共享证据；依赖范围见[版本索引](../../docs/project-layout/20261107-b00-v1/skill-research.md)及[耦合审计](../../docs/project-layout/20261106/audit/coupling-report.md)。同内容或静态字符串命中不能证明可去重、可独立运行；历史隔离目录中的 Windows 联接可能直接指向当前 scripts／output。

历史周期、独立审查、冻结输入和 before/backup 的意义按各自版本保留，不用当前数字改写旧报告。B00 仅检查文档与链接，不运行业务脚本、构建、验证或准备流程，不启动后续批次。
