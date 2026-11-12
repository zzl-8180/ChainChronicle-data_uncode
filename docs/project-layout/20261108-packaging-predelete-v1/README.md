# 打包支线删除前准备 V1

状态：**删除前准备完成，Sol high 整合、Astra high 独立审查 PASS**；[验收回执](acceptance.json)。`SHARED_INTEGRATION_PENDING`；**未获得删除授权，未删除或移动文件**。共享补丁尚未合入，实际删除继续等待用户最终确认并临前复核。历史清单和独立验收不覆盖或重写。

本次统一退役提案严格限于 [28 项逐文件清单](execution-candidates.md)（[机器清单](execution-candidates.jsonl)），合计 **2,061,279,175 B 逻辑字节**，约 2.061 GB／1.920 GiB。它不是 NTFS 物理空间释放保证，也不是严格上限。当前未执行，已释放空间为 0。六个成功旧包作为一次整支退役决策提交最终确认，无须逐包建立新的审批流程。

| 组成 | 文件 | 逻辑字节 | 删除影响与准备 |
|---|---:|---:|---|
| 旧打包源码与缓存 | 19 | 240,771 | 17 个 `.py` 已保存 157,899 B 非执行前像；2 个 `.pyc` 仅记新算哈希，不复制 |
| 六个成功历史 ZIP | 6 | 2,027,261,537 | 未确认独立完整替代副本；提案明确放弃下列旧版整包重放／回退，不新造大型备份 |
| data ZIP、handoff ZIP、失败 A ZIP | 3 | 33,776,867 | 参考消费者已解除；handoff 的139份展开载荷／证据保留；失败A仅含空README，118 B |

HOLD **1,997 文件／2,894,924,641 B** 与 RETAIN **4,763 文件／81,107,363 B** 完全排除。原 APK、raw、缓存、当前技能成果、媒体、事故保护、其他参考分析，以及 B00／B01 冻结材料不在本次删除范围。未来仅删除清单中的普通文件，不递归删除根目录，不顺便删空目录或“清理”历史证据。

## 统一放弃的六个成功旧包

| 仓库相对路径 | 逻辑字节 |
|---|---:|
| `output/share_bundle/20261016-delivery/CC_delivery_research_20261016.zip` | 22,177,812 |
| `output/share_bundle/20261016-delivery/CC_delivery_tools_20261016.zip` | 1,441,178 |
| `output/share_bundle/20261025-character-tools/packages_retry/A_tools.zip` | 1,521,555 |
| `output/share_bundle/20261025-character-tools/packages_retry/B_data_research.zip` | 69,517,757 |
| `output/share_bundle/20261025-character-tools/packages_retry/C_character_pages_images.zip` | 1,781,589,013 |
| `output/share_bundle/CC_analysis_full_20261016.zip` | 151,014,222 |

这些 ZIP 删除后，不能按原发行说明原样取用整包、重放或回退；当前 pages、主表、新成果和本轮源码前像均不能代替这些完整版本。保留的历史 README、manifest、provenance、审查与回执能解释当时结果，不能据此声称恢复了整包。旧 data ZIP 的594份载荷也不能从596成员冻结清单恢复；解除消费者只保留抽样证据与字段可复现性。

随删除退役的历史重放还包括：`scripts/storage_retention/recycle_v1/prepare_manifest.py` 中对 retry A/B/C 的 stat／read／hash（20261027旧治理清单固定重放），以及 `projects/distribution/releases/20261107-b01d-pilot-v1/run_pilot.py` 依赖旧打包源码的试点重放。它们不是当前角色正式生成主线，但删除后不能原样重跑；这些历史脚本和冻结回执保留，不为本次删除改写旧保护清单。本轮不能据此声称“全仓无非打包消费者”。

## 已完成的可审查准备

- [源码前像映射](source-manifest.json)：按原相对路径保存在 `source-before/<原路径>.before`，17份逐字节相同，157,899 B（小于1 MiB）。9个 `scripts/release/*.py` 实际被 Git 跟踪，8个 `output/share_bundle/*.py` 未跟踪，不能假定 Git 可恢复后者。前像只作保存，未导入或执行；`.pyc` 只记哈希。
- [元数据回执](metadata-receipt.json)：28项与冻结清单的 size／mtime_ns／dev／ino／nlink 相符；两轮间隔约2秒，观察值相同。逐项检查仓库范围及所有祖先，无 reparse，普通文件、nlink=1；139项 handoff 保留材料也与原清单身份一致。
- [权限观察](permissions.json)：每项记录 owner、SDDL、属性，逐项机器清单同时记录 mode、只读属性及 `os.access` 指示。它们是权限证据，**不是**当前令牌有效 DELETE／父目录 DELETE_CHILD 权限的完整判定，未实际试删。
- 19个小文件 SHA-256 本轮实读；大 ZIP 仅核元数据，8个有历史 SHA-256及来源，明确标为未重算；118 B失败A未定位历史哈希，本轮未读ZIP内容。其“仅空README”来自[已通过独立验收](../20261108-reference-zip-decouple-v1/acceptance.json)。
- 参考分析已改读冻结成员原序清单，禁ZIP／缺包验证通过，依据[适配验收](../20261108-reference-zip-decouple-v1/acceptance.json)；本轮未重跑完整报告。handoff 只退役ZIP，payload、受保护manifest与139份材料继续保留，不要求修改主线保护清单。
- `projects/distribution/README.md` 已增加当前停用声明，并定向把旧“现行源码”与成功包使用措辞改为历史。B00／B01冻结材料未改。

这两轮观察不排除未来写入，也不证明全机无打开句柄或无在途任务。本轮没有可靠的全机句柄／进程排他证明，也没有基于句柄的原子防竞态保证；不得把短时稳定写成“无人写入”。若执行时发现写入者或无法澄清的活动，停止受影响项并由整合者处理，不停止或抢占其他任务。

## 共享入口等待整合

[最小文档补丁](shared-navigation.patch)基于当前工作树原文生成，原文件 SHA-256见[补丁基线](shared-patch-bases.json)，`git apply --check`已通过但**尚未应用**。补丁只为 AGENTS／HANDOFF／STATUS／根README增加停用与确认入口，并把当前分享使用指引限定为历史；AGENTS第8节的一般分享能力保留，未来须另授权，本次退役优先且不默认重建。

状态必须继续写为 **`SHARED_INTEGRATION_PENDING`**，不能宣称全部实施条件通过。主聊天独立审查后由指定整合者重读当前文件、保留并发新增内容，再最小合入；若基线漂移，重新生成或手工对照，不能用旧全文覆盖。实际删除前必须同步这一共享入口。其他导航（例如 `projects/unpack/README.md` 的 release 链接）本轮不修改，整合者可将其解释为历史取证入口，不能从链接存在推导旧脚本仍为现行工具。

## 最终执行约束

1. 主聊天完成独立验收，解决共享入口待整合状态，并展示本页及精确28项清单。
2. 用户最终确认这28项逐文件删除，包括统一放弃六个成功旧版本整包重放／回退；当前授权只到准备，不能把“推进到删除前”当成删除许可。
3. 执行前对每项重新验证根／祖先无reparse、普通文件身份、size、mtime_ns、dev、ino、nlink、小源码哈希与权限／活动状态。任一项漂移仅停止该项／对应组，另行核对；不能重新扩展或递归删目录。
4. 使用原生 PowerShell 的单文件 `-LiteralPath` 语义，保留空目录；先预览，再在明确授权与一致性复核下执行。不得用根目录递归删除、路径通配符、跨shell删除或后台自动删除。
5. 最终回执逐项记删除／保留／漂移失败状态和实际观察的空间变化，核对HOLD、RETAIN及保留证据；不以逻辑总量冒充物理实收空间。

以下只是**不会删除文件的预览模板**，本轮未执行，不提供自动删除脚本；`<逐项已批准的absolute_path>`必须取自机器清单，并经上述临前核验，不能替换为目录：

```powershell
Remove-Item -LiteralPath '<逐项已批准的absolute_path>' -WhatIf
```

## 材料入口与复核方法

- 冻结范围：[原退役README](../20261108-packaging-retirement-v1/README.md)／[原28项清单](../20261108-packaging-retirement-v1/delete-candidates.jsonl)／[原验收](../20261108-packaging-retirement-v1/acceptance.json)。旧文中G_REF阻断等是历史状态，由本轮及适配验收承接，不改旧文。
- [适配后条件复核](../20261108-reference-zip-decouple-v1/deletion-readiness.md)与[机器复核](../20261108-reference-zip-decouple-v1/deletion-readiness.json)；[任务卡](../../tasks/20261108-packaging-predelete.md)。
- 本目录 `prepare_evidence.py` 只读取清单精确候选、生成本目录证据与非执行前像，`prepare_shared_patch.py` 只生成待合入补丁；均不删除／移动、不运行旧模块、不重建业务成果。已完成必要复核后不为增加检查次数反复运行。
- 下一步仅主聊天独立最终审查与共享入口整合；物理删除继续等待用户明确最终确认。
