# 角色技能阅读器导航

## 正式阅读器与试点

正式全库阅读器仍在 `output/character_skills/`，与正式卡页、共享图片和翻译输入一起使用。外部数据从[解包](../unpack/README.md)、[研究](../skill-research/README.md)和[媒体](../assets/README.md)的现行入口定位。页面服务说明与数据、前端版本见下表。

历史版本索引：[B00 总览](../../docs/project-layout/20261107-b00-v1/README.md) · [本项目全部23条映射](../../docs/project-layout/20261107-b00-v1/reader.md) · [全1140条机器索引](../../docs/project-layout/20261107-b00-v1/index.json)。基线为[20261106 path-map](../../docs/project-layout/20261106/path-map.json)，更具体子行优先；本轮新增任务卡不因此改写旧映射。

## 当前阅读入口

| 用途 | 入口与消费者 |
|---|---|
| 全库阅读页 | [reader_full_20261106/index.html](../../output/character_skills/reader_full_20261106/index.html)，首页含全部角色索引与分页；本地服务地址及使用说明见[脚本README](../../scripts/skill_reader_preview/README.md) |
| B02 试点 | [候选前端](site/b02-20261108-v1/index.html)、[验收与使用边界](../../docs/project-layout/20261108-b02-candidate-v1/README.md)。试点按绑定版本读取源数据，正式全库阅读入口独立保留。 |
| 生产代码 | [scripts/skill_reader_preview](../../scripts/skill_reader_preview/)；从正式 pages/card.json、campaign、rules 和账本读取，输出独立阅读页；没有后台自动同步 |
| 数据版本 | [build_receipt.json](../../output/character_skills/reader_full_20261106/build_receipt.json)，记录源快照、哈希和数量 |
| 前端版本 | [frontend_receipt.json](../../output/character_skills/reader_full_20261106/frontend_receipt.json)，与数据构建回执分别记录 |
| 语义审查 | [语义任务卡](../../docs/tasks/20261107-reader-semantic-review.md)、[审查报告](../../output/character_skills/reader_full_20261106/audit/semantic_review.html)、[冻结审查目录](../../output/character_skills/reader_semantic_20261107/) |
| 阅读层级调整 | [reading-layout任务卡](../../docs/tasks/20261107-reader-reading-layout.md)，正文与数值常显，待对应数据和重复说明折叠 |
| 原型历史与复发案例 | [prototype任务卡](../../docs/tasks/20261106-character-skills-reader-prototype.md)、[full任务卡](../../docs/tasks/20261106-character-skills-reader-full.md)；CID350的25/27.5与卡面比例须保留版本上下文 |

## 历史版本记录

2026-11-07 本地读取时，语义审查卡与阅读层级卡均标记完成。数据回执锚定 C18 后 snapshot `01c05f78-cf9451c6ff47fcfb`，该次任务卡记录2236卡、41665条描述、35404项答案；前端回执标明仅更新前端并沿用该数据快照。这些是对应版本的交付记录，本导航没有重跑其验收，也不宣称与后续主线自动同步。

中文审查完成不等于所有游戏效果已解释。已有答案包含推断，未解项仍保留；CID350分支条件的推断、12010／13014攻击间隔方向歧义不能因展示更新被抹掉。末尾强化句须保留完整作用范围，不能把分支序号当游戏档位，也不能将一个增幅套给所有效果。

## 共享依赖与保护边界

- 正式数值生产链为 [card_page_data.py](../../scripts/character_skills/card_page_data.py) → [rules.py](../../scripts/character_skills/rules.py) 的 `answer_for`；当前规则和答案见[研究导航](../skill-research/README.md)。旧 `query_effect_dictionary.py`只读30236旧视图及 records，不读取当前 rules／cards。
- [audit/reference_pairs.json](../../output/character_skills/reader_full_20261106/audit/reference_pairs.json) 是实际翻译输入，不能因位于 audit 就视为可丢报告；[reviewed_sentences.json](../../scripts/skill_reader_preview/reviewed_sentences.json)与[semantic_sentences.json](../../scripts/skill_reader_preview/semantic_sentences.json)分别保留已审句库与全库语义结论。全库图片实际引用相邻 [pages/art](../../output/character_skills/pages/art/)，不能单独移动阅读输出目录。
- 正式 pages 中的 card.json、index.html、receipt、blocker、backup、`_batch` 及作为输入的旧 card 属同一事务；[正式渲染器](../../scripts/character_skills/card_page_render_v2.py)仍有 ledger／policy 和复制写入依赖。逻辑归入 reader 不等于可直接剪切模板或拆分生产输出。
- 冻结审查目录的 manifest、rows、units、[packets](../../output/character_skills/reader_semantic_20261107/packets/)和[results](../../output/character_skills/reader_semantic_20261107/results/)保留输入与结论对应；不重新准备、不覆盖或去重删除，不把分片数量当审查完成证据。历史样稿及 before 材料保持原位，详见[23条索引](../../docs/project-layout/20261107-b00-v1/reader.md)。

任务当前状态以[项目交接](../../HANDOFF.md)和对应任务卡为准。
