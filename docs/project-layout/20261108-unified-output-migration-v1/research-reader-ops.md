# 技能研究、阅读器、参考分析与跨任务运维迁移交接

状态：仅整理统一窗口的物理范围和接口门槛；**未搬迁、未改 live 脚本、未切联接、未提交**。机器可读逐根表为 [research-reader-ops.json](research-reader-ops.json)。基于 `20261106/path-map.json` 的 1140 行及 `audit/contracts.json`、第三方复查 `command-io-matrix.json`，现存顶层身份以同目录 `current-top-level.json` 的 **2026-11-08 11:20:20 UTC** 浅层 lstat 为准。旧映射的静态命中数、目录联接数仅作 2026-11-06 索引元数据；本交接没有遍历大 payload 或重做全量哈希。

## 当前物理边界

本分工覆盖 21 个 `output/` 顶层完整目录：**15 个适配后可纳入一次统一迁移，6 个本次原位保留**。后者有明确冻结或实时使用边界，不能用“全量交接”四字覆盖。全部可迁目标是独立且当前不存在的新容器；旧 `path-map` 中 `output/character_skills` → 已存在的 `projects/skill-research/`、`output/reference_analysis` → 已存在的 `projects/reference-analysis/reports` 两个宽泛提案均不能直接作为整树 `Move` 目标。后者是 B01 既有 reports，改用尚不存在的 `projects/reference-analysis/history/reference_analysis`，不合并覆盖 B01。

| 现址完整根 | 独立新容器或原位 | 当前裁决与主要接口 |
|---|---|---|
| `output/boss_chain` | `projects/skill-research/evidence/boss_chain` | 适配后可移；`boss_chain_trace/probe`、`build_boss_chain_guide` 与卡页推断的证据存在门槛。 |
| `output/boss_heal` | `projects/skill-research/evidence/boss_heal` | 适配后可移；`boss_heal_trace/probe`、`build_boss_heal_guide`、规则与卡页推断。 |
| `output/ordinary_effects` | `projects/skill-research/evidence/ordinary_effects` | 适配后可移；`ordinary_*` 探针/字典、`query_effect_dictionary`、卡页规则读口。 |
| `output/card_comparison_cid30236` | `projects/skill-research/evidence/card_comparison_cid30236` | 适配后可移；`build_chica_comparison`、`verify_chica_comparison`、旧查询字典与卡页证据。 |
| `output/char_roster` | `projects/skill-research/data/char_roster` | 适配后可移；`build_char_roster.py` 固定 `OUT_DIR`，`character_skills/common.py`、`crosscheck_raw.py`、`scope_diff.py` 固定读 JSON；图片及发行消费同步适配。 |
| `output/field_guide` | `projects/skill-research/reports/field_guide` | 适配后可移；`build_field_guide.py` 默认写旧根并固定读审计 JSON，`audit_unity_headers.py` 固定写该 JSON；`latest.json` 及 README 的 `../cache_full_20261015_v3` 链接须闭合。 |
| `output/structured` | `projects/skill-research/data/structured` | 适配后可移；`structured_candidates.py` 固定写入；`verify_phase_a.py` 读取两样例并可能调用子命令重写。 |
| `output/phase_d` | `projects/skill-research/evidence/phase_d` | 适配后可移；`phase_d_*` 写入，`sample_trace.py`、`export_master.py`、`build_field_guide.py` 读入。 |
| `output/sample` | `projects/skill-research/evidence/sample` | 适配后可移；`sample_trace.py`、`active_skill_trace.py` 写入，解包、字段指南、主表导出及核验脚本固定读取。 |
| `output/skill_mechanism_scale` | `projects/skill-research/experiments/skill_mechanism_scale` | 适配后可移；`scripts/skill_mechanism_scale/{prepare,collect,census,summarize,report}.py` 固定 `BASE/OUT`，prepare 读取 trial 冻结 review。 |
| `output/skill_mechanism_trial` | `projects/skill-research/experiments/skill_mechanism_trial` | 适配后可移；`scripts/skill_mechanism_trial/{prepare,compare,report}.py` 固定输出，scale 对其 review 有输入哈希。 |
| `output/skill_route_experiments` | `projects/skill-research/experiments/skill_route_experiments` | 适配后可移；`scripts/skill_route_experiments/run.py` 固定 `OUT`。 |
| `output/reference_analysis` | `projects/reference-analysis/history/reference_analysis` | 适配后可移；旧映射宽目标 `projects/reference-analysis/reports` 为已存在的 B01，改用不存在的独立 history 子容器，整根不拆。`ref_analysis_claude_cc*`、`ref_ui_audit*`、`ref_analysis_lead_reconcile*` 写入；卡页 `gaps/rules`、历史清理复放及报告读取或引用。对方原始目录仍只读。 |
| `output/git_sync_20261024` | `operations/records/git-sync/20261024` | 适配后可移；旧 Git 回执，无当前脚本读写。和 `project_overview` 合计 11 文件／99,446 B，身份及十联接见第三批 `source-inventory.json`；并入统一窗口，不单独交接。 |
| `output/project_overview` | `operations/records/project-overview/20261020` | 适配后可移；人工历史报告，HTML 无深度敏感链接；README/旧提示词仅根路径文字与过期清理提案，不能执行。 |
| `output/character_skills` | **本次原位保留**；未来候选 `projects/skill-research/data/character_skills` | `share_manifest_20261021/README.md` 和 `manifest.json` 正是 11 项 `RETAIN_IN_PLACE` 中的两项。当前整根 Move 会改变两项原位身份，旧根 junction 或搬后复制回不能代替原位保持。另有 live 事务与冻结签名门槛；新容器只是未来备选，不在本次可迁 15 根内。 |
| `output/20261016-reproducibility-audit` | **本次原位保留** | 其 `review/` 中六份 README 属 11 项原位保留；历史独审入口及祖先目录保持。 |
| `output/20261024-project-review` | **本次原位保留** | 事故与独审冻结证据、C13 pins/恢复路径，不能按一般记录根迁。 |
| `output/审查报告` | **本次原位保留** | 旧独审报告及旧路径引用保持原位，不用统一迁移推断可改冻结审查。 |
| `output/storage_retention` | **本次原位保留** | P/v7、各周期 plan/binding、pins、归档/预约及 live 保留状态混合；不能勉强整根搬迁。 |
| `output/project-layout` | **本次原位保留** | 新增的布局审计与当前迁移回执根，不在旧 1140 行顶层映射，仍可能有并行写入。 |

上述原位目录以外，11 项 `RETAIN_IN_PLACE` 还有三份 `docs/tasks/` 历史任务卡；全部逐条列在 JSON 的 `protect.retained_in_place_paths`。`operations/history/retired-packaging/20261108/` 的 5,317 项归档独立保护；名称含历史、旧包或 retired 不等于可移动或可删除。P/v7 及四组周期计划/绑定的身份约束继续有效。

## `character_skills` 将来整根备选的必要闭包

旧映射把 `pages`、`pages/art`、`profiles`、`effect_ledger`、`reader_full`、`reader_semantic`、`cycle_reports`、`review`、`share_manifest` 等分别提案到不同项目目录，同时已有 494 条目录联接候选。**物理上不能按逻辑子项目拆开**：这些目录互相以相对 URL、源路径、规则哈希、campaign 指针及事务恢复引用。将来若两项原位保留保护被单独合法解决，才可评估整个 `character_skills` 根作为一体迁入新的 `projects/skill-research/data/character_skills`；阅读器和发行仅做导航标签与显式读口，不另移其子树。

至少在同一候选版本中闭合：`scripts/character_skills/common.py` 的 ROOT 与正式数据根、`rules.py`、`card_page_data.py`、`card_page_batch.py`、`card_page_write.py`、`effect_ledger.py`、`cycle_report.py`、`run_retention.py` 的输入/输出；`scripts/skill_reader_preview/build.py`、`verify.py`、`reference_copy.py`、`verify_full.py`、`verify_regressions.py`、`prepare_*` 与 `merge_semantic_review.py` 的默认输出、失败前写入和 `reference_pairs` 固定位；页面 `../pages/art/<cid>` URL、卡面渲染和 `char_roster`/媒体读口。`build.py` 的 `--output` 不约束其他命令、Node 子进程或固定数据读口。`merge_semantic_review.py` 会先写进度再报错，其 ROOT/HERE 与字典输出必须单独绑定。

保持同一版本的 `pages/_batch/campaign_latest.json`、`profiles/rules.json`、card.json/receipt/index.html、ledger/report、reader 源哈希；核 `card_page_dependencies.py` 和批量签名的路径敏感输入，不改写历史签名伪装相同。`card_page_write` 的 blocker/backup 与 `run_retention` state/lock、resume 共一事务；旧脚本不能只换 `pages-root` 就执行。`cycle_report` 的历史 backup、before_cards、metrics/verdict 解析要完整预检，无匹配/重复 CID 不得默默降级。`storage_retention/recycle_v1/archive_store.py`、`inventory.py` 的 pin、catalog、vault 和旧逻辑路径需另有内容身份映射；归档 ledger 的 `root_id`、`path_kind`、相对/绝对路径语义要逐类型区分，不能统一字符串替换。

## 统一窗口的实施和验收门槛

1. 先固定本次 15 个完整根及其他分工的正式范围，重核 `current-top-level.json` 身份、每个独立目标不存在、同盘真实祖先、内部 reparse 与 C14—C18 隔离联接的实际 tag/target。旧索引数量不是当前活链清单，不能把联接当普通子目录递归复制。`git_sync/project_overview` 的 10 联接并入这一窗口处理。
2. 每条实际执行命令及子命令按 `command-io-matrix.json` 声明 CWD、`__file__` 根、import 期缓存、读源、正常与失败写入、输出参数及版本拒绝。统一适配查询/生成入口、`latest.json`、manifest 结构路径、HTML/README 相对链接及 evidence `is_file` 门槛；只更新允许维护的新版本索引，不覆盖冻结成果或归档记录。未闭合前不能运行旧生成器。
3. 先以独立候选目录进行代表只读查询、单样本生成和错误路径测试；对账文件内容、来源快照、路径类型、链接及历史引用。正式切换按依赖组留下精确回执。任一断链或源漂移时，保留实际已迁位置及新写入，停止受影响依赖组，优先在现位置前向修复；不承诺自动整批逆搬。确需逆搬时，先核目标现身份、旧源仍缺失且没有并发新增，再按回执先恢复材料、后切回入口，另定受控恢复范围，禁止覆盖新内容。主线 `character_skills`、`storage_retention` 与原位独审根的内容和身份保持不变。冻结 manifest 只作身份核对，不在本窗口重签或改写。

本报告是必要接口与保护门槛的交接，不是运行许可或已经通过的迁移验收。历史第三批两树的精细 SHA/ID 回执仅适用于那两树，其他大根还须在实施前按风险做有界身份检查。
