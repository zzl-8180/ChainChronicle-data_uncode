# 锁链战记角色技能源码整理提交提示词

2026年10月19日。建议先单开Git整理对话完成本地提交，再让新主持恢复页面写入。本提示词不启动页面扩量或研究；当前对话只编写交接，没有执行暂存、提交、推送。

---

你接手 `E:\代码项目\锁链战记数据解包` 的角色技能源码整理和本地Git提交任务。请读取 `AGENTS.md` 并实际检查后，完成本线源码、必要配置和任务文档的筛选提交，交付commit SHA及可复用的文件清单。用户已要求单开本任务整理提交；在明确本线边界内连续完成，不为每次add/commit重复询问。**不推送，不发布Release，不生成角色全量，不恢复P3研究。**

## 当前事实

最后核对HEAD为 `c50433f`。工作树有已跟踪修改和许多untracked文件，属于本线及其他任务；不要clean/reset/stash他人文件，也不把“untracked”当无用文件。`.gitignore`已忽略output/work/raw、工具、环境、APK及他人参考。

当前角色技能页主线已经完成任务−1源码快照、任务0限定FORWARD、11张样本、R1和R2方法审查，按用户要求暂停。R2最终 `output/character_skills/review/r2_20261019_methods/REPORT_RECHECK.md` 为PASS_WITH_EXPLICIT_SCOPE_LIMITS，五项闭合；源码整理不能改算法或借提交任务重做审查。权威状态在 `docs/tasks/20261019-character-skills-pivot.md`、`character-skills-progress.md`、`20261019-character-skills-pivot-handoff.md`；根HANDOFF仍有过时P3B10待D记录，不据此开旧线。

源码快照已保全，但Git尚未补齐。尤其已修改的 `profiles.py` 导入六个未跟踪模块：`description_bindings.py`、`batch_bindings.py`、`p3b7_bindings.py`、`p3b8_bindings.py`、`p3b9_bindings.py`、`p3b10_bindings.py`；HEAD不能代表当前398/11409/29788描述产物的生成器。需要收进的不只这六个文件，还要核对它们的本地导入和JSON/JS配置闭包。

## 先盘点再建立白名单

先 `git status --short`、`git diff --name-status`、查看staged内容，确认没有其他对话仍在写拟提交文件。若已有他人暂存项，保留其状态，不能顺带提交；本任务只处理自己的明确白名单。新主持若已恢复写源码，应协调为本线冻结点；能独立处理的文件先做，不自动清空或接管工作树。

定向核对这些本线候选，不把整目录或快照67项自动当成全需提交：

1. **旧P3生成器和必需依赖/配置。** 六模块；`scripts/character_skills/` 内相关p3b脚本、binding_scope JSON、DOM JS、remaining_five/type26_mana/type9_bullet等实际被调用模块；10张P3任务卡。已跟踪的profiles/rules/skilllist_types/query/gaps/crosscheck_raw/verify_p1改动须逐份diff确认与本线关系，再纳入必要部分。
2. **本次type1082和页面工具。** `scripts/character_skills/type1082_native.py`、`type1082_probe.py`、`type1082_snapshot.py`；`card_page.py` 及当前 `card_page*.py` 配套模块，包括basic/data/render/policy/positions/dependencies/cohorts/batch/write/check、source_fix、r2_prep和r2_fixes_check。以实际清单核准，不假定此列举穷尽。已有 `scripts/il2cpp_sample_code.py`、`scripts/metadata_targets.py` 已受Git跟踪，确认是否有真实diff，不为快照包含它们而复制或制造提交。
3. **本线文档。** `docs/tasks/character-skills-progress.md`、`20261019-character-skills-pivot.md`、type1082/card-pages/r1/r2-prep/r2-review任务卡，以及本次两份主持/Git交接提示词；相关旧P3任务卡可保留历史内容，不能为整理改写旧结论。

快照仅用于核对范围和漂移：

- `work/character_skills_pivot/snapshots/20261019-pre-pivot-a7bf4d21/manifest.json`（67来源文件；同名ZIP也在，含10张任务卡）。
- `work/character_skills_pivot/snapshots/20261019-type1082-dependencies-20261019T105412Z/` 和 `20261019-type1082-final/`。
- `work/character_skills_card_pages/snapshots/20261019-pilot-r1-source-fix/manifest.json`。
- **最新页面源码** `work/character_skills_r2_prep/snapshots/20261019-r2-f1-f5-frozen/manifest.json`（160项清单、128增量副本、29数据依赖），前home-fix及初稿已是历史版本。

快照含已跟踪未变源码、展示输出和依赖，不能整份照单加入Git。以当前源码对最终冻结版本核对；发现漂移先列文件及差异，查明是否属于主持收口文档/其他工作，不以旧副本覆盖现有文件。不要为更新冻结manifest而覆盖旧审查证据。

## 排除范围和可复现性说明

AGENTS.md、根HANDOFF.md/STATUS.md、`docs/tasks/20261017-reference-analysis.md`、`scripts/ref_analysis_claude_cc.py`等有其他任务改动，本次默认不纳入。只有确认属于本线且必要的具体hunk才提出/处理，不能为看起来干净而全收。公共文件存在混合修改时，用精确补丁/分段暂存保留他人改动；无法安全拆分才报告具体阻塞，不自动改写内容。

不加入APK、游戏缓存、raw/work/output、参考卡页、环境/工具、媒体、ZIP和凭据；不 `git add .`，不对目录 `add -f`，不修改忽略规则来收入大产物。本轮只整理源码和文档，不迁移研究数据进新目录、不打包发行成果。

这些工具仍依赖已解码主表、profiles/rules/links及既有研究证据，部分检查还依赖本地镜像/metadata。源码入Git不等于仅git clone就能生成页面。请记录：哪些源码/配置已入库，哪些游戏输入/生成依赖仍在忽略目录，取得/重建入口是什么，尚未验证的隔离运行边界。不要删除这些依赖检查、伪造空结果或把依赖省掉来声称干净环境通过。无需在本任务恢复完整引擎或运行旧189/A—P/GBK全链。

## 建议提交顺序和最小核验

先把白名单、分组、数量/大小、混合修改与未纳入项写入你自己的简短任务卡 `docs/tasks/20261019-character-skills-source-commit.md`。必要时在提交前补最小依赖说明，除此不改算法/来源/页面。

建议按真实diff拆成：① 补齐P3生成器及必要公共改动/配置/历史任务卡；② type1082与card_page实现/本轮文档。共享依赖使前一组不能自洽时可以合并或调整，以依赖完整和可审查为准，不机械追求提交数。旧已受审代码保持内容，不能用Git整理开启另一轮重构。

验证限本次风险：

- 对拟提交Python做不写仓库pyc的语法检查，并核本地import/配置文件闭包；动态引用、固定输出读取也要列出。避免只提交profiles而遗漏六模块、scope JSON或DOM脚本。
- 每次暂存显式列文件；检查 `git diff --cached --name-status`、`--stat`、`--check` 和关键diff，确认无混入输出/输入/凭据/其他任务、不发生全文件行尾改写。不要改全局Git配置或归一化整仓库换行。
- 如做小样本运行，先确认输出参数和输入依赖，写独立临时目录；不得覆盖用户确认pages、R2准备版或旧审查。已有结果与代码冻结无漂移时，不为增加测试数量重跑页面/native。
- 从提交后的仓库树核所有必要源码/配置可取得；未实际完成干净目录运行时只报告源码闭包/语法已核，不冒称端到端可复现。

然后本地提交明确白名单。不要使用包含他人staged内容的无范围提交；不要amend他人提交、重写历史、push或发布。若权限/签名等使commit不能完成，保留工作树并报告实际状态，快照不能冒充成功commit。

## 交付

给出每个commit的SHA、主题、文件数、实际纳入范围；给出源码/配置闭包检查和最小核验结果、未纳入修改/依赖、`git status`剩余项及原因。工作树仍有其他任务改动属正常，不追求全仓库clean。

在自己的任务卡记录新HEAD及源码与R2最终冻结的关系，供新主持只读接手。根HANDOFF/STATUS和旧独立审查不覆盖。完成后暂停，不自动让页面线开跑；新主持恢复前先读你的交付，不再以c50433f作为最新状态。
