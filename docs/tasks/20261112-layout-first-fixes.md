# 目录整理收尾：A7 与缓存校验

- 状态：独立修复与复验完成。源码版 A7 接入迁址读路径，补采和 v3 校验的报告分流到新目录。
- 写入范围：`scripts/character_skills_pipeline/a7_regression.py`、`scripts/verify_cache_refresh.py`、`scripts/verify_cache_snapshot.py`、本任务卡及 `work/20261112-layout-first-fixes/` 的独立复验。
- 正式数据、历史回执、C21 归档和五个旧联接保留。主线依赖签名后续方案及实施回执见下方。

## 验收

- A7 独立输出 29/29，v3 独立输出 13/13、39,047 条记录。两份新回执分别与历史回执逐字节一致。
- 补采独立输出 7 文件、4 项检查通过，含 77 个数据文件、68,993 条来源记录及 165 个新增资源。4 文件逐字节一致，另外 3 文件的差异仅为工作路径分隔符。
- 两个缓存校验均拒绝已存在的输出目录。未传 `--output` 时，在 `projects/unpack/reports/validation/` 创建独立时间戳目录。
- 复验前后核对两个缓存快照、缓存指针、A7 验收目录及指定 C21 冻结证据，共 352 个文件，SHA-256 无变化。
- [首轮命令与退出码](../../work/20261112-layout-first-fixes/commands.json)、[v3 补齐参数后的复验](../../work/20261112-layout-first-fixes/snapshot-r2-commands.json)。

## 依赖签名后续收口方案

状态为 R1—R6 已实施，独立复验通过。以[两轮最终合并审查](../../work/20261112-dependency-plan-independent-review/final/FINAL_REPORT.md)的 R1—R6 为索引。保留[原专项回执](../../output/character_skills/review/dependency_signature_relocation_20261112/REPORT.md)和两轮探针。修订前重核第三方保护清单的 41 项文件，均匹配审查结束时的 SHA。原正式根 17/17、专项 18/18 继续作为原运行证据。候选三卡验证与主线单次正式构建边界见[迁址候选复核](../project-layout/20261108-unified-path-validation-v2/REPORT.md)和[主线实施方案](../角色技能完整解读实施方案.md)。

| 审查项 | 复核结论与当前依据 |
|---|---|
| R1 | 原方案已有外部数据方向，补齐实际入口和根冲突。`data_path` 仅覆盖部分 JSON，`pages.iterdir()` 和部分账本／哈希读取仍使用直接路径；构建端以 `--input-root` 同时读取名册并签源码。第三方配置-only 退出 2，显式 pages/ledger 退出 1，空显式数据根在启用配置时对两种历史格式结果不一致。[验收入口](../../scripts/character_skills/card_page_verify_full.py:556) · [构建入口](../../scripts/character_skills/card_page_batch.py:123) · [配置-only 命令](../../work/20261112-dependency-plan-independent-review/config-only-command.json) |
| R2 | 采纳。历史物理键当前从已解析落点推导。同字节的单项改落点使 C21 回执失败。四份 C21 回执的 33 个物理键及顺序已逐项一致。[物理键推导](../../scripts/character_skills/card_page_dependencies.py:119) · [单项改落点反例](../../work/20261112-dependency-plan-independent-review/round2/mapped-result.json) |
| R3 | 采纳。实际 main 读四组 latest，却未把它们与 campaign snapshots 逐一绑定；逐卡检查漏掉 `source_signature`。两种内存反例均错误退出 0。当前 manifest 原始哈希与回执匹配；验收未核实际 manifest 字节是源码确认，尚无全量 CLI 篡改复现。[当前验收源码](../../scripts/character_skills/card_page_verify_full.py:573) · [快照反例](../../work/20261112-dependency-plan-independent-review/campaign-snapshot-mutation.json) · [逐卡反例](../../work/20261112-dependency-plan-independent-review/receipt-source-mutation.json) · [manifest 证据](../../work/20261112-dependency-plan-independent-review/round2/manifest-binding.json) |
| R4 | 原方案已有坏字段和混用诊断，补首次聚合、SHA 语法及原数组签名。坏 cohort 字段在 `set` 处异常退出，额外依赖键被重建数组时丢弃后错误通过。[聚合入口](../../scripts/character_skills/card_page_verify_full.py:585) · [依赖数组复算](../../scripts/character_skills/card_page_dependencies.py:220) · [坏字段反例](../../work/20261112-dependency-plan-independent-review/cohort-bad-field-mutation.json) · [额外键反例](../../work/20261112-dependency-plan-independent-review/round2/extra-entry-field.json) |
| R5 | 采纳。坏配置 SHA 的进程确实退出 2，旧 PASS 文件仍在；缺口是上层未把报告与本次退出码绑定。[反例命令](../../work/20261112-dependency-plan-independent-review/stale-out-command.json) |
| R6 | 原方案已区分两组联接，补保护分类和指针。原 25 项实为 22 项材料和 3 份源码。原联接回执记录正式 `share_bundle`；v2 `previous` 另用原身份清单核对。[25 项前后哈希](../../output/character_skills/review/dependency_signature_relocation_20261112/frozen_hashes.json) · [五个 v2 previous](../project-layout/20261109-batch2-previous-assessment-v1/conditional-candidates.jsonl) |

### 实施契约与顺序

1. **确定写域和基线。** 由单一执行者整合，临前重读生产源码和在途任务写域。预计只改 `card_page_dependencies.py`、`card_page_verify_full.py`、`card_page_batch.py`。并行驱动已原样传参，沿用布局模块的现有解析能力。需要超出这三份时，在计划／回执单列真实调用理由。以 22 项材料、五个正式指针和配置联接清单建立基线，三份授权源码各留修改前哈希。验证入口、候选配置和报告放新建 `work/20261112-layout-dependency-signature-followup/`，原审查工具与回执保留。
2. **统一实际入口的根和路径。** 验收以 `--root` 指定代码根。构建的 `--input-root` 保留输入命名空间用法，源码签名使用实际运行脚本所在的代码根。独立运行时核对模块加载位置。有效数据根取启用配置声明的根；布局未启用时使用显式 `data_root` 或代码根。配置已启用且同时给定 `data_root` 时，两者必须指向同一实际目录，否则在读依赖前明确报冲突。空显式根、错误配置或缺件均不能隐式改用正式／旧副本。独立代码根通过工作目录内的新配置绑定预期数据的**绝对根**和该配置 SHA，避免直接沿用正式配置的相对 `repository_root`。
   - 验收默认 pages、ledger、manifest 从有效数据位置解析一次，枚举、存在性、JSON、HTML、账本和哈希均使用同一解析结果。显式 `--pages`／`--ledger` 保留既有传参，记录最终读取位置并校验其版本归属。当前 manifest 用正式声明位置，历史验证用与历史快照绑定的冻结 manifest。
   - 构建前置读取使用实际 `--manifest`、同目录冻结名册及按统一布局解析的名册源；签源码仍使用独立代码根。独立源码清单含 import 所需的 `scripts/character_skills/c21_direct_damage_targets.json` 等源码侧资产及其 SHA。
   - 本次验证的 `--out` 和构建计划的 `--output` 明确传入独立 work 下的绝对位置，先确认无跳转或历史文件覆盖。验证器报告写入不依赖布局 `strict_write_roots` 来兜底。
3. **固定历史键，分开实际读口。** 本轮支持**整根迁移及受绑定配置声明的单项重映射**，包括已声明且经解析器许可的根外读取。新签名只用固定 33 项有序逻辑键。对 C21 历史物理格式，在依赖模块登记一份版本化有序键表或等价的冻结根映射，按 C21 四份冻结回执及 20261109 迁址映射交叉确认。历史键表在实现时一次固定，不能从当前落点或待验回执反推。只接受完整匹配的已知有序逻辑表或 C21 历史物理表。两种格式的字节均由 33 项受控声明经 `read_path` 读取，回执键仅用于格式匹配和签名复算。未登记的物理格式、逐项混用和未声明落点明确拒绝。维持原顺序、JSON 序列化和签名算法。
4. **按模式绑定验收对象。** 先读取并校验 campaign、四组快照、指针和 report 的结构，再使用字段。四组必须为 `ge60`、`40to59`、`20to39`、`remaining`，各一份，快照状态须符合该次完整验收。路径按原记录核对且解析后仍在指定 pages 内。当前模式要求 campaign snapshot 逐组等于本轮实际读取的 latest 所指路径；同签名而不同 run 也不能代用。历史复算按冻结 campaign snapshot 选择，不要求与当前 latest 相同，也不要求四组 run ID 相同。每组 cohort_report 和 signatures 必须来自同一绑定 run，核对四个签名组成字段和 campaign。逐卡 `source_signature` 及既有签名、run ID 和 manifest 绑定均与其所属组核对。当前及历史各自对**实际解析的同一份 manifest 原始字节**求哈希；历史源码签名按其冻结记录核对组成，不要求等于已修改的当前源码。
5. **结构检查前移，绑定本次验收输出。** 在首次取字段、聚合去重及拼接前检查 pointer、campaign、cohort_report、signatures 和签名相关 receipt 结构；损坏组退出后不进入二次聚合。签名及依赖 SHA 使用 64 位 ASCII 小写十六进制，现有样本均为此格式，历史值不隐式改大小写。依赖项键集严格为 `{path, sha256}`。按原序列化直接复算原记录数组签名，再独立对比实际依赖字节。混用诊断列出组、冲突索引、实际键与该位置两种预期键。每次命令使用全新不存在的 `--out`，仅在本次退出 0、该命令新生成有效报告且 verdict 为 PASS 时计为通过；早期失败保留本次命令和 stderr。

### 验证矩阵与证据落点

新目录内用 `commands/` 保存命令、实际源码路径和 SHA、配置 SHA、有效数据根、输入／输出落点、退出码与 stdout／stderr；独立记录以下验收。已有未改变的探针作为前像，修复后复验对应场景。

| 项目 | 触发条件与预期 | 证据位置（相对新 work 根） |
|---|---|---|
| R1 实际入口 | 新进程从独立代码根分别运行配置-only、显式正式 pages/ledger 两条 `card_page_verify_full.py` 命令，均读取同一 C21 并产出新 PASS。独立根无本机数据副本；同根显式 data_root 通过，冲突／空显式根及错误配置 SHA 结构化失败，逻辑和物理格式结果一致。 | `commands/`、`cli/`、`root-cases.json` |
| R1 构建前置与新签名 | 独立源码及源码侧 JSON 逐项绑定。实际 batch 用新 work 输出执行 PLAN_ONLY，名册和源码身份正确；该分支在依赖计算前返回。另用真实共享声明生成新逻辑签名，进入实际验收检查块，且可核对该签名计算用的源码身份。 | `builder/plan.json`、`builder/logical-verifier-block.json` |
| R2 历史及重映射 | C20／C21 各四组在正式根、独立根显式数据根、独立根配置-only 下按冻结指针通过。整根换址、同字节单项改落点和获准的根外映射均保持历史签名可验；目标缺失、改字节、越出声明读域或未知历史键明确失败。根外映射为新增夹具，旧审查仅作源码推断。 | `historical-receipts.json`、`mapping-cases.json` |
| R3 绑定 | 少／重复／错组、交换路径、同签名不同 run、单改 snapshot 或状态、路径越界、分离同组 report 与 signatures、逐卡来源签名缺失／置零、只改 manifest 非 cohorts 字段均失败。snapshot 与逐卡两例复用已证实错误 PASS 的探针；manifest 反例在独立夹具或实际验收入口验证，并如实标注运行层次。 | `binding-cases.json` |
| R4 结构与签名 | 空／缺失签名文件、坏 JSON、顶层非对象、首次聚合前的坏 cohort 字段、null／数组／对象／布尔或短值、依赖额外键、缺项、错序、重复、混用、改哈希及组间不一致受控失败。混用报告有具体位置。 | `negative-cases.json` |
| R5 新回执 | 原 PASS 仅保留作前像；复现旧 PASS 加坏 SHA，退出非零，不能计入本轮验收。正式根做一次修复后的只读完整验收，退出 0、新报告 PASS。 | `commands/stale-out.json`、`cli/formal.json` |
| R6 前后保护 | 原 25 项拆分。22 项材料前后 SHA 一致，三份授权源码单独记录前后 SHA 和实际差异。另核 `campaign_latest.json`、四组 `latest.json`、正式配置及 locator。按原清单无跟随核五个 v2 `previous` 的 lstat ID、tag、raw target，以及五个 v2 正式入口的 ID 和目标。确认五个 next 不存在，另列五个正式 `share_bundle` 的身份和目标。 | `protected-hashes.json`、`junctions.json` |

方案修订阶段仅写本任务卡。实施前确认唯一整合者和当前写域；任一绑定未闭合不得声明整体通过，发生并发变更时保留现场并只复验受影响检查。保护原历史签名、原报告、正式 pages／规则／账本、C20／C21 归档及联接。不新增全量双端哈希门槛，不启动正式生成、resume、账本重建、清理、提交、发布或 C22。依赖覆盖范围和其他目录待办另行处理。

### 实施回执

- 临前核对三份脚本与第三方保护快照一致，C21 整改已收口，未发现重叠写域。本对话统一整合，只改上述三份生产脚本、本任务卡和独立 work 验证材料。
- R1、R2 通过。正式根与独立代码根两种 CLI 读法均为 17/17；C20／C21 八份真实签名在三种根调用方式复算通过。七种映射夹具覆盖同字节重映射、根外读口、缺件、未声明落点和变字节。独立进程对真实 C21 第 29 项重映射后仍通过。构建器保留旧 `--input-root` 的输入命名空间用法，源码签名固定取实际运行脚本所在的源码根。独立 PLAN_ONLY 按原算法复算 106 份 Python 源码签名，另核 1 份源码侧 JSON 的哈希。新逻辑签名在实际验收检查块通过。
- R3、R4、R5 通过。快照篡改、2236 张逐卡来源签名置零、仅改 manifest 非 cohorts 字段的实际入口均退出 1。44 项签名反例及 11 项绑定反例均按预期拒绝。旧 PASS 加坏配置的命令退出 1，旧文件原字节保留，本轮判定拒绝。
- R6 通过。40 项监看对象仅三份授权源码 SHA 改变。22 项冻结材料、五个正式指针、配置及 locator 均一致。五个 v2 previous、五个正式 v2 和五个正式 share_bundle 的对象身份及目标一致，五个 next 仍不存在。
- [汇总](../../work/20261112-layout-dependency-signature-followup/verification.json) · [命令和退出码](../../work/20261112-layout-dependency-signature-followup/cli-results.json) · [独立配置验收](../../work/20261112-layout-dependency-signature-followup/cli/config-only.json) · [历史签名复算](../../work/20261112-layout-dependency-signature-followup/matrix/historical-receipts.json) · [保护哈希](../../work/20261112-layout-dependency-signature-followup/protected-hashes.json) · [联接身份](../../work/20261112-layout-dependency-signature-followup/junctions.json)。
- 本轮运行只读验收、构建计划和独立夹具。正式生成、resume、账本重建、清理、提交、发布及 C22 均未执行。

### N01／N02 定向修补

- N01 已关闭。验收在读取每组报告后检查内部 `plan` 对象，将 `cohort`、`run_id` 和 `run_directory` 绑定到实际选中的组与 run。八项函数级反例受控失败，C20／C21 八份真实历史报告绑定通过。原先会错误通过的内存篡改再次调用实际 `main`，退出 1，诊断指向 `ge60` 的 `plan.cohort`，未生成验收报告。正常当前 CLI 退出 0，17/17 PASS。
- N02 已关闭。步骤 2 的 `--input-root` 契约与构建端源码及实施回执一致，构建端无代码修改。
- 临前 107 项源码／资产匹配独立复核基线，未发现并行写域冲突。临后 40 项监看对象中仅验收器的授权 SHA 改变。22 项冻结材料、正式指针、配置和联接身份均一致，独立复核的八份原证据保留。
- [函数级反例](../../work/20261113-dependency-plan-identity-fix/function-negatives.json) · [历史绑定](../../work/20261113-dependency-plan-identity-fix/historical-binding.json) · [实际 main 反例](../../work/20261113-dependency-plan-identity-fix/internal-plan-main-command.json) · [正常 CLI 回执](../../work/20261113-dependency-plan-identity-fix/current-cli-command.json) · [保护核对](../../work/20261113-dependency-plan-identity-fix/verification.json)。
- 2026-11-13，[独立定向复审](../../work/20261113-dependency-n01-n02-independent-review/REPORT.md)结论为 **PASS**。**N01／N02 均 CLOSED，定向修补已收口，本轮无剩余阻断。**
