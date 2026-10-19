# 角色技能源码整理与本地 Git 提交

- 负责人：Git 整理对话（2026-10-19，单开后接 `20261019-character-skills-git-handoff.md`）。
- 状态：已完成本地提交（2026-10-19），未推送、未发布 Release、未重跑页面/native、未改算法与审查结论。
- 写入范围：`scripts/character_skills/` 白名单文件、本任务卡；提交后仅追加 SHA/结果。
- 只读范围：全部快照、`output/`、`work/`、其他任务改动（`AGENTS.md`、根 `HANDOFF.md`/`STATUS.md`、reference-analysis 两项）。

## 白名单（两组，按依赖完整性拆分）

### 第 1 组：P3 生成器、必要公共改动与配置

新增生成器／绑定／证据模块：

- 六个绑定模块：`description_bindings.py`、`batch_bindings.py`、`p3b7_bindings.py`、`p3b8_bindings.py`、`p3b9_bindings.py`、`p3b10_bindings.py`（`profiles.py` 直接导入）。
- 规则转换模块：`type26_mana.py`、`type9_bullet.py`、`remaining_five.py`（`rules.py`／`skilllist_types.py` 按字段导入）。
- 分批实施：`p3b2_type8.py`、`p3b3_type26.py`、`p3b4_type9.py`、`p3b5_remaining_five.py`、`p3b5_f1.py`、`p3b6_native.py`、`p3b6_batch.py`、`p3b7_native.py`、`p3b7_batch.py`、`p3b7_rectification.py`、`p3b8_native.py`、`p3b8_batch.py`、`p3b9_native.py`、`p3b9_batch.py`、`p3b10_batch.py`。
- 冻结队列配置：`p3b6_binding_scope.json`、`p3b7_binding_scope.json`、`p3b8_binding_scope.json`、`p3b9_binding_scope.json`、`p3b10_binding_scope.json`（由各 `*_bindings.py` 用 `Path(__file__).with_name` 读取，缺失会直接失败）。
- DOM 夹具：`p3b3_dom.js`、`p3b4_dom.js`、`p3b5_dom.js`、`p3b6_dom.js`、`p3b7_dom.js`、`p3b8_dom.js`、`p3b9_dom.js`、`p3b10_dom.js`（手动/批脚本调用的生成页脚本夹具，非浏览器验收）。

已跟踪公共文件的本线改动（逐份 diff 确认，无其他任务 hunk）：

- `profiles.py`（六模块导入、绑定状态与 CSV/HTML 字段）、`rules.py`（remaining_five/type9/type26 按字段分派）、`skilllist_types.py`（新增规则行与 P6 报告索引复用）、`query.py`（审定绑定展示）、`gaps.py`（绑定/提示分列）、`crosscheck_raw.py`（type26 param0 独立重算、P10 冻结视角）、`verify_p1.py`（P6/P10 历史口径按冻结规则集重算）。

历史任务卡：`docs/tasks/20261019-character-skills-p3b1-type8.md` 至 `20261019-character-skills-p3b10-batch-bindings.md` 共 10 份（内容保持原结论，不因整理改写）。

### 第 2 组：type1082、card_page 工具与当前文档

- type1082：`type1082_native.py`、`type1082_probe.py`、`type1082_snapshot.py`。
- 页面工具：`card_page.py`、`card_page_basic.py`、`card_page_batch.py`、`card_page_check.py`、`card_page_cohorts.py`、`card_page_data.py`、`card_page_dependencies.py`、`card_page_policy.py`、`card_page_positions.py`、`card_page_r2_fixes_check.py`、`card_page_r2_prep.py`、`card_page_render.py`、`card_page_source_fix.py`、`card_page_write.py`（`card_page_dependencies.py` 以 `card_page*.py` 通配收集，故整组入库）。
- 文档：`docs/tasks/character-skills-progress.md`（已跟踪修改）、`20261019-character-skills-pivot.md`、`20261019-character-skills-pivot-handoff.md`、`20261019-character-skills-type1082.md`、`20261019-character-skills-card-pages.md`、`20261019-character-skills-r1.md`、`20261019-character-skills-r2-prep.md`、`20261019-character-skills-r2-review.md`、`20261019-character-skills-git-handoff.md`、本任务卡。

## 明确排除

- `AGENTS.md`（reference-analysis 入口行）、根 `HANDOFF.md`／`STATUS.md`（混合且含过时 P3B10 待 D 记录，由整合者维护）、`docs/tasks/20261017-reference-analysis.md`、`scripts/ref_analysis_claude_cc.py`（另一任务）。
- APK、`raw/`、`work/`、`output/`、参考卡页、媒体、ZIP、环境/工具、凭据；不 `git add .`、不 `add -f`、不改 `.gitignore`。

## 冻结与漂移核对

- 快照覆盖：全部本线未跟踪/已修改源码均出现在下列清单之一，无清单外新增：pre-pivot 67、type1082-dependencies 54、type1082-final 57、pilot-r1-source-fix 35、r2-f1-f5-frozen 189。
- 漂移：pre-pivot 67/67 与 `20261019-type1082-final` 及 `r2-f1-f5-frozen` 均 0 漂移；`pilot-r1-source-fix` 中 `card_page.py`／`card_page_data.py`／`card_page_render.py` 3 项与当前不同，属 R2 后续修订，最终以 `r2-f1-f5-frozen`（160 项 0 漂移）为准，不覆盖旧审查证据。

## 可复现性边界

- 入库的是源码、冻结队列配置与任务文档；运行仍依赖忽略目录中的解码主表、`profiles/rules/links` 及既有研究证据，部分检查另需本地原生镜像/metadata。
- 重新生成页面的入口为 `scripts/character_skills/card_page.py`（及 `card_page_batch.py`），逐角色查询为 `query.py`；输入取得方式见各产物目录 README，不在本次迁移数据。
- 未在干净 clone 中端到端运行；本次仅核语法/导入/配置闭包与提交后仓库树可取得性。

## 核验记录

- 59 个 `scripts/character_skills/*.py` AST 解析通过，无语法错误。
- 本地导入闭包：除包式 `from character_skills import ...`（经 `scripts` 路径解析）外无缺失；`capstone`／`unicorn` 为已声明第三方依赖。
- 静态字符串引用的同目录配置/夹具均存在：`p3b5_dom.js`、`p3b6/7/8/9/10_binding_scope.json` 及对应 `_dom.js`；`p3b3/p3b4_dom.js` 为独立手动夹具，一并入库。

## 提交结果

| commit | 主题 | 文件数 | 范围 |
|---|---|---|---|
| `e64bc0d` | 角色技能解读线：补齐 P3 生成器、冻结队列配置与公共改动源码 | 54 | 第 1 组全部文件（+63887/−30） |
| `1ed7318` | 角色技能页：补齐 type1082 与 card_page 工具源码及 R1/R2 文档 | 27 | 第 2 组全部文件（+2673/−1） |

本任务卡更新的记录提交紧随两条源码提交；新 HEAD 即 `git log -1` 所示提交。工作树保留其他任务改动，见下节。

### 提交后仓库树核验

- 用 `git archive HEAD` 解出隔离目录后重跑：`scripts/character_skills/*.py` 59 个全部 AST 解析通过；本地模块导入无缺失；5 份 `p3b*_binding_scope.json` 可解析且与 `*_bindings.py` 的 `Path(__file__).with_name` 引用一一对应；`p3b5_dom.js` 及 P3B6—P3B10 的 DOM 夹具均在该树中取得。
- 与 `20261019-r2-f1-f5-frozen` 核对：160 项 0 漂移；`card_page.py`／`card_page_data.py`／`card_page_render.py` 相对 R1 source-fix 的差异即 R2 已审修订。
- 未做干净 clone 端到端运行；数据输入（解码主表、profiles／links、原生镜像／metadata）仍在忽略目录，按“可复现性边界”如实记录。

### 提交后仍存在的其他任务改动（未纳入）

- `AGENTS.md`、`HANDOFF.md`、`STATUS.md`（混合／过时 P3B10 记录，由整合者处理）。
- `docs/tasks/20261017-reference-analysis.md`、`scripts/ref_analysis_claude_cc.py`（reference-analysis 任务）。
- 其余 `raw/`、`work/`、`output/` 产物按 `.gitignore` 保持忽略。

## 下一步

页面线按 R2 `PASS_WITH_EXPLICIT_SCOPE_LIMITS` 暂停；新主持恢复前先读本卡与 `20261019-character-skills-pivot-handoff.md`，以本卡两条源码提交为源码基线，不回到 `c50433f`。
