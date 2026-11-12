# 第三批目录候选筛查

状态：仅准备，未搬迁、未修改业务脚本、未切换联接、未提交。依据是既有 `20261106/path-map.json` 的五行映射与静态索引，另定向检查当前脚本和目录内说明。精确身份库存见 [source-inventory.json](source-inventory.json)。

## 建议最终范围

| 源目录 → 映射目标 | 现存内容 | 当前耦合与处理 |
|---|---:|---|
| `output/project_overview` → `operations/records/project-overview/20261020` | 5文件、69,618 B；0子目录、0内部联接 | 一次性人工报告；当前脚本无读写。目录内 README、提示词保留旧根路径文字；HTML 无 `href`、`src` 或 `../` 相对链接。可整树搬迁，导航文字由整合者随后适配。 |
| `output/git_sync_20261024` → `operations/records/git-sync/20261024` | 6文件、29,828 B；0子目录、0内部联接 | 2026-10-24 Git 同步回执；当前脚本无读写，任务卡引用旧回执路径。无随目录深度变化的相对链接。可整树搬迁。 |

合计 **11文件、99,446 B**。两目标均不存在；`operations/` 是同 E: 卷真实目录，尚无 `operations/records/`。无需修改 live 业务脚本或冻结文件才能先形成这两棵整树搬迁范围。

两树各有 C14—C18 五个隔离输入 junction，当前都指向源目录；它们仍真实存在，不能把仅移动源目录等同于入口闭合。库存记录十个联接的路径、ID、`0xA0000003` tag、实际目标及 `.batch3-20261108-next/previous` 同父旁路缺失。后续执行须按审批后的切换方案维持隔离入口可读，并在执行前重核身份。

## 其余三棵

| 源目录 → 映射目标 | 现存内容 | 本批暂缓的具体边 |
|---|---:|---|
| `output/field_guide` → `projects/skill-research/reports/field_guide` | 133文件、6子目录、807,663,591 B | `scripts/build_field_guide.py` 默认写旧目录、固定读取其中审计 JSON 并写 `latest.json`；`scripts/audit_unity_headers.py` 固定写审计 JSON。现有 latest 指向旧路径，README 的 `../cache_full_20261015_v3/README.md` 搬后断链。需要生成器与指针适配，不能零业务改动闭合。 |
| `output/char_roster` → `projects/skill-research/data/char_roster` | 2,665文件、37子目录、157,532,573 B | `build_char_roster.py` 固定输出，`character_skills/common.py`、`crosscheck_raw.py`、`scope_diff.py` 读名册；既有映射显示 reader、媒体、发行消费及2,831条静态候选。本次只核现用脚本，不展开旧索引逐条分析。 |
| `output/sample` → `projects/skill-research/evidence/sample` | 4文件、227,053 B | `sample_trace.py`、`active_skill_trace.py` 固定写入；解包、字段指南、核验等多脚本固定读取 `sample.json` 或 `active_skill_trace.json`，且缓存快照 provenance/manifest 有旧路径。 |

## 冻结和边界

`full-disposition.jsonl` 的 11 项 `RETAIN_IN_PLACE` 已逐条对照，均不落入五棵候选，尤其不落入建议搬迁的两树。P/v7 两份保护 JSON 无这五棵路径的精确字面命中；这不代替对历史冻结引用的保护。项目概览内关于旧角色页、规则及清理的提示词是历史文本，不能据此执行清理或改写冻结 P/v7、当前 rules/pages/主线。两树内容、目标与联接的后续物理实施由主持确定范围后另行安排。
