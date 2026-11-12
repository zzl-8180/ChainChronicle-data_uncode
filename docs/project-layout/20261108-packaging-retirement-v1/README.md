# 打包支线退役 V1：执行前清单

状态：**Sol 编制完成，主聊天独立验收通过；未执行删除。** 本页不是删除脚本或清理授权。2026-11-08 只读盘点九棵明确候选树，逐文件记录在 [`delete-candidates.jsonl`](delete-candidates.jsonl) 与 [`retain-and-hold.jsonl`](retain-and-hold.jsonl)；元数据、覆盖和来源回执见 [`inventory-receipt.json`](inventory-receipt.json)，独立验收见 [`acceptance.json`](acceptance.json)。任务卡为 [`20261108-packaging-retirement-plan.md`](../../tasks/20261108-packaging-retirement-plan.md)。

## 精确范围与容量

| 决策 | 文件 | 逻辑字节 | 含义 |
|---|---:|---:|---|
| `DELETE_AFTER_GATE` | 28 | 2,061,279,175 | 已界定逐文件候选；执行前仍须满足该行 `gate` 和下文共同门槛。当前不计为可立即释放。 |
| `HOLD` | 1,997 | 2,894,924,641 | 独立隔离／复现现场的来源与唯一性未逐文件闭合。不得按目录名推定可删。 |
| `RETAIN` | 4,763 | 81,107,363 | 历史报告、manifest、provenance、回执、小型基线及 payload 等证据。 |
| **九棵树合计** | **6,788** | **5,037,311,179** | 两份 JSONL 路径互斥，覆盖九棵树的全部普通文件。 |

九棵树为 `scripts/release`、`output/share_bundle`、`projects/distribution`，以及 `work/delivery_20261016`、`work/repro_20261016`、`work/review2_20261016`、`work/review_20261016`、`work/review_20261017`、`work/review_20261017_r1`。枚举逐层检查 reparse，不跟随链接；9,407 个目录中未遇到 reparse。任务不扩展到其他 `work/`、`output/` 或 `projects/`。路径均为仓库相对路径；每行有文件字节数、`mtime_ns`、`dev`、`ino`、`nlink`、分组及门槛。所有 6,788 个文件观察到 `nlink=1`，各决策集合内无重复 inode；**2,061,279,175 B 是待删文件的逻辑总量，不是 NTFS 实际释放空间的保证或严格上限**，仍受压缩、稀疏、簇分配与其他引用影响。没有全量哈希大 ZIP 或 APK。

### 删除候选分组与顺序

| 顺序 | 组 | 文件 | 逻辑字节 | 当前门槛 |
|---|---|---:|---:|---|
| 1 | `release_code_cache` | 2 | 82,872 | `G_CODE`；旧 `.pyc`，随代码退役。 |
| 2 | `release_code` + `legacy_builder` | 17 | 157,899 | `G_CODE`；`scripts/release` 九个 `.py`，旧 `output/share_bundle` 八个 `.py`。 |
| 3 | `delivery_zip` + `character_zip` + 旧 full `analysis_zip` | 7 | 2,027,261,655 | `G_ARCHIVE`；包括 2026-10-25 成功 A/B/C 三 ZIP、失败 A ZIP、2026-10-16 两交付 ZIP 与旧 full ZIP。 |
| 4 | 旧 data `analysis_zip` | 1 | 28,435,262 | `G_REF`，**BLOCKED_REFERENCE_CONSUMER**。先适配参考分析，再审删除。 |
| 5 | `handoff_zip` | 1 | 5,341,487 | `G_HANDOFF`；仅 ZIP，payload 和旧清理所保护的 manifest 保留。 |

上表顺序是实施依赖与复核顺序，并非立即删除许可。`character_zip` 四个压缩文件总计 1,852,628,443 B；成功 A/B/C ZIP 本体合计 1,852,628,325 B，另 118 B 为失败 A ZIP。容量以当前逐文件 ZIP 清单为准。本清单保留 `packages_retry/manifest.json`。当前**立刻可释放：0 B**；完成归档与代码门槛后的已界定候选为 2,027,502,426 B，参考 ZIP 和 handoff ZIP 仍单独受阻。HOLD 的 2,894,924,641 B 仅是进一步查证的容量上限，不能加入可释放数。

### 共同及专项门槛

- `G_META`（每组执行时必做）：重读逐文件路径与身份；核对仓库根和祖先仍在预期范围、无 reparse；逐文件 `size`、`mtime_ns`、`dev`、`ino`、`nlink` 未漂移。若有漂移，仅停止受影响文件／组并重审，禁止递归删除整个候选树。不得跟随外部联接。
- `G_CODE`：整合者确认正式生成、resume、verify、ledger 与当前 rules/links/ledger/campaign 仍无这些旧入口；确认无其他在途打包任务或历史重放需要；把现有文档入口改成退役说明。源码可能未被 Git 跟踪，不能假定 Git 可恢复。这里**没有**执行这些模块。
- `G_ARCHIVE`：对每个历史发行版本，须明确**永久放弃该旧版本的整包重放与回退**，或确认另一份独立、已核验的完整副本；现用 `pages`、主表和其他新成果不能自动当作旧 A/B/C 包的回退。用户仍可通过保留的 manifest、README、审查和来源记录理解旧结果；整合者更新指向被删 ZIP 的共享文档与导航。旧 2026-10-25 发行原本仅本地验收，删除将使其不可按旧说明整包使用。逐个 ZIP 复核记录后才执行，不能以目录整体删除代替。
- `G_REF`：旧 `CC_analysis_data_20261016.zip` 是 `scripts/ref_analysis_claude_cc.py:224` 的实际消费者。先将本轮只读取得的 [`analysis-data-central-directory.json`](analysis-data-central-directory.json) 作为冻结成员证据，适配该函数读取经来源标识的**原序**成员名；用纯函数逐项核对旧三个输出字段：总条目、前两级路径集合排序前十、含 `charainfo` 的前五项。`[:5]` 依赖 ZIP 顺序，不得预排序成员。确认新脚本在旧 ZIP 不存在时仍生成相同字段，再解除本 ZIP 的阻断。本轮**未改脚本**。旧 `package_summary.json` 给出的 SHA-256 是历史记录，本轮未重算；中央目录共 596 条，即摘要中的 594 个载荷文件加 `README_先读.md` 和 `PACKAGE_MANIFEST.json` 两个包装成员；与现有 `version_sample_check.json` 的 596 个总条目一致。
- `G_HANDOFF`：候选仅为 `mechanism_first_handoff_r1.zip`；`payload/`、release manifest、回执与 C19 旧清理脚本保护的 `payload/manifest.json` 均在 RETAIN。执行前核对这些保留项现存且身份未变，并登记该 ZIP 的退役位置。**仅删除此 ZIP 不需要移交 payload、修改主线或改写旧保护清单，也不能称其使原 payload 对账／保护检查失效。** 直接使用该 ZIP 的历史分发／解压命令会退役；若未来另提删除 payload，才另行处理历史对账与保护边界。
- `G_SOURCE_PROOF`：HOLD 不参与本次删除。2026-10-25 `isolated` 现场 1,034 文件／1,359,130,918 B；六个 `work` 目录 963 文件／1,535,793,723 B。二者含 APK、原生库、输出与脚本副本。仅观察到路径和元数据，未验证每个对象可由现存原件／清单重建；若后续要释放，须独立来源映射、保留必要冻结审查／manifest／receipt，并另版逐文件晋级清单。不可因扩展名 `.md` 或目录名 `review` 整组保留或整组删除。

## 保留边界与影响

`RETAIN` 中包括 B01-D 试点 26 文件／65,810 B、角色工具历史发行证据 114 文件／23,175,621 B、机制交接 payload 与证据 139 文件／50,124,806 B、两版技能值逐卡回执 4,478 文件／7,129,344 B，以及其他根／2026-10-16 小型证据 6 文件／611,782 B。保留 manifest、review、receipt、provenance 和失败诊断，并非仅凭 `.md` 后缀。B01-R 不在这九棵树内；B00/B01-R 和独立审查／冻结任务记录均保持原位。

明确排除：`output/single` 三个解码样本，原 APK、`raw/`、现用缓存与正式技能成果、媒体、`output/storage_retention/` 全部保护材料（含 P_small_closure、pins、vault、事故证据）、第一批已迁至 `projects/unpack/data/cache/cache_full_20261015` 的缓存，以及其他参考分析和项目共享根文件。本任务未修改 `AGENTS.md`、`HANDOFF.md`、`STATUS.md`、根 `README.md`、`.gitignore` 或项目导航。共享入口由整合者在门槛满足后更新；历史冻结材料不改。

当前正式角色生成、续跑、验证、账本无需 `scripts/release` 或 `output/share_bundle`；这使主线可继续，但**不证明**旧包重建、隔离复现和旧清理回放仍可用。物理删除后旧包不可整包回退；本计划不自动复制全部 5 GB 以制造新备份。当前尚未解决：HOLD 的逐文件来源证明、data ZIP 消费者适配、仅 ZIP 退役后的指引更新、共享文档链接更新、执行时身份复核及真实可回收空间。

## 参考分析的最小适配范围（尚未实施）

后续仅修改 `scripts/ref_analysis_claude_cc.py` 的 `version_sample_check()` 中原 224–229 行读取段，读取本目录的冻结 `analysis-data-central-directory.json`，按 `entries` 原序取 `name`；移除仅该段使用的 `zipfile` import。源 ZIP 身份来自快照的 source、size、mtime 和明确标为历史记录的 SHA-256，不把它说成本轮重算值。可直接复用本份快照，不另造包或复制载荷。

对应更新 `output/reference_analysis/claude_cc_site_pages/README.md` 的再生成说明：原命令保持，包成员抽查改为冻结清单来源；旧分析结果不覆盖。验证需证明三个原输出字段一致、清单缺失／结构异常明确报错，以及不访问旧 ZIP 时该读取段仍正常。可在隔离的最小测试中验证，不能为模拟缺包而搬动或删除真实 ZIP，也不必重跑整份参考分析。当前只完成中央目录和三个字段的纯数据对照，业务消费者依赖尚未解除。
