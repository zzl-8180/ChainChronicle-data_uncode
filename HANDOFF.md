> **YG1第二批已收口（2026-10-24）**：55/74同类公式复用及55调度配置已整合，Sol high独立最终验收PASS_WITH_EXPLICIT_SCOPE_LIMITS，阻塞0、必需修复0。交付 `output/character_skills/yg1_batch2_20261024/README.md`；当前数字与下一步只看 `docs/tasks/character-skills-progress.md`。本批已停止，其他专项未启动；下文旧批次数字为历史。

> **入口（2026-10-24）**：当前执行规则＝`docs/角色技能完整解读实施方案.md`（2026-10-24 版，含 §8.1 存储治理要求）；当前状态与接手摘要＝`docs/tasks/character-skills-progress.md` 顶部。**已知 R3 归属/选题整改链已关闭**：原 Codex 最终复验 `output/character_skills/review/r3_selfobj_codex_final_20261024/`（PASS_WITH_EXPLICIT_SCOPE_LIMITS）＋总指挥最终确认 `output/20261024-project-review/incident_command_20261024/selfobj_final_confirmation_r1/`；事故本轮处置已按残留缺口收口（已恢复7,980／缺4,072），永久防误删设计定稿、未实施；唯一事故边界见 `output/20261024-project-review/incident_command_20261024/README.md` 顶部，交付见同目录 `incident_closeout_20261024.md`。事故不作为批18/YG1等主线前置，主线由主持推进。**存储治理（防误删＋防堆积）已入方案 §8.1，代码待用户安排启动**（分工与启动条件见任务卡 `docs/tasks/20261024-storage-governance-plan.md`）。下列各条含历史记录（其「当前/进行中」表述以各时点为准）。

---

# 交接：数据提取与截图对照

更新：2026-10-22（角色技能页主线·批 8–9 收官与交付闭环）。**当前阶段**：2236/2236 角色页已交付（玩家视角版式、立绘、图例、入口两页齐全）；推断层批 1–9 全部实施并经独立审查闭合（整行推断 2,461＝试点 337＋批3 40＋批4 37＋批5 211＋批6 1,349＋批7 106＋批8 346＋批9 35；整行确认 266、原文A 13,859 不变）；初审整改（H1/M2/M5/L1/M1/M6）与复审五项整改（核心看板落地／交接收敛／分享清单绑定当前版本／Y.G. 选题纠正／检查器豁免收紧并定向用例验证）经 R3 验收 PASS 闭合；固定机器检查 card_page_verify_full.py 10/10 PASS（30236 三条基线显式登记缺失按 NOTED 单列）。**核心看板与全部指标以 `docs/tasks/character-skills-progress.md` 唯一当前块为准**（本文件不维护数字副本；当前 campaign run `20261021T144023488884Z-91417d7e`、签名 `b670cd42…`，可在看板、`output/character_skills/share_manifest_20261021/` 与页面回执核对）。**交付状态**：组合X 全量页面成果包已本地生成（`output/share_bundle/cc_skill_values_20261021/` 及同名 zip：13,385 文件/3.30 GiB，zip 1.59 GiB，manifest 逐文件 SHA-256 对账 PASS），**未发送、未上传、未公开**，发送由用户本人执行；分层完整发行（A 工具/B 数据/C 媒体）另列后续。**必要限制**：推断值未逐记录人工审定、不得当确认；30236 三条历史缺失登记保留原样；C 行 25,079 无数字量化（页面标灰、不填 0）。**下一步**：批 10 选题待用户裁决（`output/character_skills/inference_inventory/yg_priority_list.md` 剩余 1,896 行/16 候选；批 8/9 不按原排期自动恢复）；低优先级登记待查：战斗所属与等级 ATK/HP 的游戏内来源。历史 P3 批次线与下列 2026-10-20 各条为历史记录（其“当前/进行中”表述以该时点为准）。

更新：2026-10-20（角色技能页主线·玩家视角版式与数值解读深化，**该时点历史记录**）。**① 主交付现状**：2236/2236 角色页已交付并全部切换为玩家视角版式——`output/character_skills/pages/<cid>/index.html`＋选择器 `pages/index.html`＋全卡列表 `pages/all_cards.html`（原文主体＋颜色即证据等级数值 chips：确认绿实／确认·类型外推绿虚／推断橙／未知灰；审计内容全部 ▶详情 折叠；右上角图例；立绘 `pages/art/<cid>/`，主图按游戏 UI 的 2:3 竖版显示，证据 `output/card_images/cid30236/followup/REPORT.txt`）。四联（分母 41,665 行）：A 14,539、整行确认 266（记录级 18＋类型外推 248）、原文A 13,859、C 27,126；整行推断 414（type1017 试点 337＋type8 批 40＋条件扩展批 37）。全部批次经 DeepSeek 独立审查闭合；790 卡 11,138 行实际核读完成。主持总结 `output/character_skills/review/host_final_20261020/RESULTS.md`。**② 核心诉求（用户定调，权威版）**：玩家视角页面——每段技能原文对应数值、颜色即证据等级、可信依据/条件/来源折叠展开；游戏文本没写数字的效果逐一点亮（推断不冒充确认，多候选留 hint）；**新卡（称号含“Y.G.”共 109 张）优先攻关**，老卡重要度低；分享方向为角色数据核心（A 工具包＋B 数据包候选，图片可发、其他媒体不发，目的地后定）。**③ 当前进行中**：推断层批次按 Y.G. 覆盖度排序（批 5 起为 Y.G. 覆盖度测量）；模型调度 Kimi K3 主持／GLM 5.3 Flash 实施／DeepSeek V4.1 独立审查（均 high，经 workflow 钉模型）；进度明细 `docs/tasks/character-skills-progress.md`。旧 P3 批次线冻结不再开新批；下列 2026-10-19 之前各条为历史入口，P3B10 等“待新D”表述已闭合，不再有效。

更新：2026-10-17（Release 暂缓，等项目告一段落）。发布说明草稿已备：[RELEASE_NOTES_draft.md](output/share_bundle/20261016-delivery/RELEASE_NOTES_draft.md)（拟标签 `v2026.10.17`、附件 A/B/C 清单/总清单 4 个）；A/B/C 包与 `e8c5ae4` 代码绑定、核验通过，随时可发。**用户决定暂不发布，待项目告一段落后裁决**；不创建 Release、不上传。`origin/main` 已在 `6240a04`（含全部解包工具与文档）。前轮各线结论继续有效。

更新：2026-10-17（已推送 GitHub）。复审通过后经用户授权，`origin/main` 已从 c027959 快进到 `e8c5ae4`（9 个提交：源码仓库补齐、可复现性修复、R1 闭合、根 README、docs、打包脚本）。GitHub 现含完整解包工具源码与文档；分层交付包（A/B/C）在本地 `output/share_bundle/20261016-delivery/`，**Release 上传仍待授权**。`其他人的参考/` 已忽略不入库；并行分析任务有其未提交文件（AGENTS.md 增改、ref_analysis 脚本与任务卡），本任务未提交、未接管。前轮各线结论继续有效。

更新：2026-10-17（复审 R1 闭合，本轮）。按 review_20261017_rectification_independent 完成闭合：**R1**——`decode_cache_snapshot.py` 增加 `--apk`（默认 `チェンクロ.apk` 不变）并传入 `NativeDecoder(apk=args.apk)`；偏移 0 变体路径 `decode_cache_variants.decode_variant` 同步接受 apk（否则改名 APK 下 helper/search 会失败）；README §2/§4 同步。隔离目录（git archive 新 HEAD＋自建前置）三用例全过：a) 改名 APK＋`--apk`：6 文件（偏移 6／0 两种包装）全部原生 DECODED、报告 PASS、decoded 与 v3 逐字节一致、17,669 记录 raw／字节定位 0 差异（仅 snapshot_id／original_file 环境字段不同）；b) 默认命名不传 --apk：结果与 a 完全一致；c) 破坏 helper.data5：该文件 FAILED_RETAINED（SHA1 mismatch）、其余 5 正常、PARTIAL_FAILURES_RETAINED。**I4**——`.gitignore` 增加 `/其他人的参考/`（他人基于本项目的分析成果，0.9GB，防 `git add .` 误带入；目录内容未动）。**I3**——HANDOFF §6 reference.png 文案与 P2-4 对齐。**I1**——本次重建的 B 包（698 项）已含最新两份审查报告。A/B/C 包按最终 HEAD 重建并核验，交付 README 同步。origin/main..HEAD 有待推送提交（计数随交接文档提交递增，以 `git log origin/main..HEAD` 为准），**未推送、未发布**。前轮各线结论继续有效。

更新：2026-10-17（最终审查整改，本轮）。按 review_20261017_final_delivery（带限制通过，1 P1＋7 P2）完成最小整改：**P1-1 经用户裁决为细分排除**——B 包排除 char_roster/icons 与两个内嵌媒体 HTML、card_images 内 .unityfs/.png、reference.png，保留名册 data/ 与全部研究证据（被排除项逐条登记 package_manifest.json 的 media_excluded）；base_master 保留两种形式。P2-1 README 注明 B1 仅偏移 6（整目录用 B2）；P2-2 decode_data5/apk_certificate 加 --apk（实测改名 APK 解码 PASS）；P2-3 apk_certificate 加 --hex 并补 README 命令；P2-4 删除 build_chica_comparison 作者机器路径常量；P2-5 full_unpack_run 按 Bundle 分量定位导出树（三种前缀实测，缺分量记 error）＋finalize 缺清单不再崩溃；P2-6/2-7 文档口径修正（待推送计数、A 包版本、媒体数量口径）。改后 A/B/C 包按最终 HEAD 重建并核验。提交后 origin/main..HEAD 共 6 个提交，**未推送、未发布**。审查基准＝当前最新提交；证据见 [审计文档](docs/tasks/20261016-reproducibility-audit.md) 整改记录②。前轮各线结论继续有效。

更新：2026-10-17（最终确认与审查交接准备，本轮）。逐项复核实际文件与运行结果：① 仓库 124 个跟踪文件含全部管线源码与文档，无游戏资源／凭据／大产物入库，工作树干净，5 个提交待推送（origin/main..HEAD，原文误写 4，按审查 P2-6 修正）。② 交付验证绑定最终版本：被测目录（git archive ff664a7）与最终 HEAD 的全部脚本、README、依赖锁、.gitignore 逐一相同（git diff 为空，仅交接文档与打包脚本差量），测试结论完整适用于最终版本。③ 错误输入处理补测：破坏 data5 单文件 FAILED_RETAINED（其余文件不受影响，报告 PARTIAL_FAILURES_RETAINED）、空目录 ValueError("No data5 input")、改动 libcompatible.so 触发版本断言、缺镜像报 FileNotFoundError 含路径。④ A/B/C 包按最终 HEAD 重建并核验（见 STATUS）。审查基准：当前最新提交即冻结版本；证据与建议抽查项见 [审计文档](docs/tasks/20261016-reproducibility-audit.md) 第三阶段记录与 `work/delivery_20261016/final/`。此后暂停修改正式成果，等待独立审查。前轮各线结论继续有效。

更新：2026-10-16（第三阶段交付准备，本轮）。① 源码仓库已补齐：提交 `8b91293`（26 文件：README.md、docs/、full_unpack 管线、build_char_roster、scripts/release、9 个修复脚本、AGENTS/HANDOFF/STATUS）、`ff664a7`（full_unpack merge/finalize 容忍第三方最小清单）、`e2cc987`（分层交付打包脚本）；未推送。② 交付版本验证：从 `git archive e2cc987`（等效 ff664a7 代码＋打包脚本）独立目录实测全链——A1—A3 前置生成（镜像＝钉住值）、data5 两包装格式 4 文件、bdl 2 样本四步管线、chronicle 主表 6 文件，全部与既有成果逐字节一致。③ 分层交付：`output/share_bundle/20261016-delivery/`（A 工具包 1.4MB/129 项、B 研究成果包 149.7MB/3366 项含 v3+base_master+技能解释+审查报告+名册、C 媒体清单 media_manifest.json 不复制 20GB、统一 README 与 package_manifest.json，CRC/对账全过）。④ 待授权动作：git push、GitHub Release 上传；媒体分包可另行运行 scripts/release/build_full_unpack_bundle.py。版权边界：APK/缓存/媒体为 SEGA 所有，不分发。前轮各线结论继续有效。

更新：2026-10-16（审查整改，本轮）。独立审查结论「带明确限制通过、无 P0」的整改已全部完成：P2-1（--prior-report 复用分支改从报告所在目录解析，三模式复验 PASS、77 重放 0 差异）、P2-2（77 重放口径澄清＋bossinfo/helper 两变体原生解码与 v3 字节一致）、P1-2（jni_prefix_probe／metadata_decode_probe 隔离实测，产物与项目逐字节一致）、P2-3（protection_sample／callback_sample／callback_key_candidates 补 mkdir，隔离冒烟 PASS）、P2-4（--cert-hex 端到端 2 bdl，APK 隐藏运行，产物与 full_unpack 逐字节一致）。P1-1 待提交清单已列在 [审计文档](docs/tasks/20261016-reproducibility-audit.md) 整改记录，等用户授权后显式提交（不推送）。本轮修改：decode_cache_snapshot、protection_sample、callback_sample、callback_key_candidates 四脚本及审计文档；未提交 git、未推送、未覆盖正式输出。前轮各线结论继续有效。

更新：2026-10-16（可复现性审计与规范，本轮）。完成第三方独立解包审计：git HEAD 原始状态在 APK 原生库提取、旧解码报告依赖、`work/protection` 建目录三处必败，均已最小修复并在仅含仓库文件的隔离目录实测通过；恢复镜像 SHA256 与钉住值一致，data5 解码与既有参考字节一致，项目侧 77 文件重放与 v3 规范化后 0 差异。AGENTS.md 新增 §7 GitHub 存储策略、§8 重构（8.1 独立可复现性／8.2 分层发布 A—C／8.4 发布前验证）。审计全文、文件盘点与下一阶段清单见 [可复现性审计](docs/tasks/20261016-reproducibility-audit.md)。本轮未提交 git、未推送、未打包上传；`full_unpack_*.py`、`build_char_roster.py`、`docs/` 仍未跟踪，git 补缺是下一阶段最高优先。前一轮完整解包及以下各线结论继续有效。

更新：2026-10-16（完整解包）。本轮完成已取得本地资源完整解包：全部68655个bdl解码展开成功（0失败），导出834741个对象（73490 PNG/17389 WAV/50051 OBJ/2845 TXT/759621 JSON），输入账本覆盖全部68993个缓存文件；77个data5沿用v3已验证解码；261个其他文件逐项分类排除。前轮ability1008（TargetStageAll）37记录/111字段及前六类型、cid30236五组政策继续有效；不重做A—E，不改原始资源、v3/E或独立报告，真实安装/后备转写和完整战斗另论。

## 1. 当前有效入口（2026-10-19 时点历史节，现已被 2026-10-21 顶部当前块取代，仅留档）

- **P3B10 C冻结待新D**：[交接](output/character_skills/P3B10_HANDOFF.md)、[证据/命令](output/character_skills/description_bindings/p3b10_batch/README.md)。仅28条type67（26武器＋2职业逗号），新增28唯一/28页描述、54唯一/54页效果槽、28cid；25主组47槽＋3缺weapon.type组7槽。3条页面明示主weaponlist缺type/自身计入未知，保留N>=2及条件化自外关系；武器按Constants跳表逐值，不套22+枚举。字段+0，398真实/11409提示/29788未知、2233部分/0仅未知/3完整，无迁移。复用B9已审native，新执行0；C专项12/12、边界94/94、原行61/61、GBK8/DOM39、verify189/A—P与12产物一次稳定通过。旧82013完整答案/重复、311绑定及强度、101/31、非目标/分母/三完整profile整体保留；仅C自检，待独立D。
- **P3B9已由独立D R1带明确范围限制通过**：[交接](output/character_skills/P3B9_HANDOFF.md)、[证据/命令](output/character_skills/description_bindings/p3b9_batch/README.md)。仅type67条件纯句，新增162唯一/162页描述、336唯一/336页效果槽、162角色，字段+0；当前41595=真实370＋提示11437＋未知29788，角色仍2233部分/0仅未知/3完整。156主组与6条原文未写计数2的差异分别保留；30620310持有者CACHE缺jobtype保留未知。实际alive列表后再判active、聚合职业位图门槛及AND筛选，阈值2仅在持有者合格且实际计入时可换述其余>=1；所有162均ordinary skillid[3]，实际装载为明确前提。C原生9/9、专项10/10、边界2117/2117、GBK14/DOM338、verify189/189与原表A—P通过，12相关产物一次重建字节一致；旧82013完整答案/重复、149绑定/强度、277用规则/源287、101/31、三旧完整profile及非目标/未知/分母保留。D最终结论为问题/阻塞/整改0，见[正式报告](output/character_skills/review/p3b9_20261019_type67_bindings/REPORT.md)；上列C检查为实施历史。
- **P3B8 已由独立D R1带明确范围限制通过，问题/阻塞/需整改0**：[最终报告](output/character_skills/review/p3b8_20261019_boss_bindings/REPORT.md)。下面旧C待审/PENDING均是冻结历史，不为文案另开整改轮次。
- **角色技能解读（P1＋P2十批＋P3第1—8批独立审查闭合；第9批C冻结待新D）**：[产物说明](output/character_skills/README.md)、
  [逐角色查询页](output/character_skills/profiles/index.html)（约 100 MB 自包含，按 cid／名称查询；也可用
  `query.py --cid 30236`）、[缺口队列](output/character_skills/gaps/gap_queue.json)、
  审查交接 [P2-1](output/character_skills/P2R_HANDOFF.md)／[P2-2](output/character_skills/P2B2_HANDOFF.md)／
  [P2-3](output/character_skills/P3_HANDOFF.md)／[P2-4](output/character_skills/P4_HANDOFF.md)／
  [P2-5](output/character_skills/P5_HANDOFF.md)／[P2-6](output/character_skills/P6_HANDOFF.md)／
  [P2-7](output/character_skills/P7_HANDOFF.md)／[P2-8](output/character_skills/P8_HANDOFF.md)／
  [P2-9](output/character_skills/P9_HANDOFF.md)／[P2-10](output/character_skills/P10_HANDOFF.md)、实施记录
  [docs/tasks/20261018-character-skills-p7.md](docs/tasks/20261018-character-skills-p7.md)／
  [docs/tasks/20261018-character-skills-p8.md](docs/tasks/20261018-character-skills-p8.md)／
  [docs/tasks/20261018-character-skills-p9.md](docs/tasks/20261018-character-skills-p9.md)／
  [docs/tasks/20261018-character-skills-p10.md](docs/tasks/20261018-character-skills-p10.md)
  （P1／P2-1／P2-2／P2-3／P2-4／P2-5／P2-6 见同目录同前缀的 `-p1.md`／`-p2.md`／`-p2b2.md`／`-p3.md`／`-p4.md`／`-p5.md`／`-p6.md`）。
  P1（R1＋R2 复验）与 P2 第 1—8 批均已过审查（各 `review/p2b*_2026101*_thirdparty/`，通过或带限制通过）；
  P2 第 8 批审查 3 处文字问题已在本批第 0 项整改；P2 第 9 批已过审查并完成整改；
  **P2 十批与P3 第 1 批已审查闭合**：P3B1 独立审查「带明确限制通过」，阻塞0、需整改0，
  [审查报告](output/character_skills/review/p3b1_20261019_type8/REPORT.md)；仅基线校准与十条固定APK type8记录的人工描述对应试点，
  [P3B1 交接](output/character_skills/P3B1_HANDOFF.md)。10 唯一片段／17 页引用、17 角色，字段数值答案新增 0；
  **P3B2 已独立审查闭合**（带明确限制通过，阻塞0、需整改0）：[报告](output/character_skills/review/p3b2_20261019_type8/REPORT.md)、[交接](output/character_skills/P3B2_HANDOFF.md)、[15候选裁决](output/character_skills/description_bindings/p3b2_type8/candidate_decisions.jsonl)。
  纳入11/排除4，新增11唯一片段/12页引用、12唯一效果槽/13页引用、12角色（与首批无重合）；字段答案+0、角色状态不变。
  P3B2闭合时41595描述页引用＝31基线＋17首批已审＋12本批已审＋11601仅提示＋29934未解释；type8累积21条/29页，两批结论各限固定记录，不向其他记录自动推广。机器产物PENDING为审查前快照，当前以D报告为准。
  **P3B3 D已审，带明确限制通过，阻塞0；N1已修待文档差异复验**（[报告](output/character_skills/review/p3b3_20261019_type26/REPORT.md)、[整改](output/character_skills/type26_mana/RECTIFICATION.md)）：[交接](output/character_skills/P3B3_HANDOFF.md)、[原生/增量证据](output/character_skills/type26_mana/README.md)。type26 param0基础玛那+489页/+469归一行/+469父holder键（416来源记录），影响481角色；3101/3102固定APK纯句+2唯一/+22页，仍限装载/非继续战斗/存活/isHero与param6门槛。当前描述41595＝31基线＋29旧type8对应＋22本批已审＋11601提示＋29912未知；旧答案和绑定零破坏。机器JSON保留审查前PENDING，以正式报告为准；本次仅文档整改，未改代码/数值/机器产物、未重跑检查。
  **P3B4 D已审，带限制通过/阻塞0；N1已由原D差异复验闭合**（[报告](output/character_skills/review/p3b4_20261019_type9/REPORT.md)、[整改](output/character_skills/type9_crit/RECTIFICATION.md)；机器PENDING保留审查前状态，以正式报告为准）：[交接](output/character_skills/P3B4_HANDOFF.md)、[证据/命令](output/character_skills/type9_crit/README.md)。type9 param0原“暴击率”候选被反证，真实是Bullet贯通后伤害保留系数；首次先Attack、后按最大已启用param0逐次乘法/整数化/夹紧，须符合MULTIHIT或击杀SHOT_THROUGH继续条件，非具体最终伤害。新增1规则、789页/788归一行/788父holder键、441来源、450角色；全BY_TYPE，描述+0、状态不变。P3B3 N1已由原D差异复验闭合，旧交接快照不改。
  **P3B5 初审需整改，F1已修待原D复验**：[交接](output/character_skills/P3B5_HANDOFF.md)、[证据/命令](output/character_skills/remaining_five/README.md)。6条Boss必杀规则（24/sp3、56/sp2、68/sp4、73/sp5/sp6/sp7），+97页/+97归一行/+97父holder键，52来源（APK44/CACHE8）、40角色；4009/4049/8116/10018/8151均仅未知→部分，描述+0。仅局部计时/请求系数/发射门槛，未承诺整条技能时长或最终发射数。P10检查以P3B1开工真实快照固定历史规则视角，仍核原5人；当前实际零未知另由实际答案核算。F1把type73改为候选遍历入口门槛，非正冷却同轮可越过次数门槛，正冷却停止继续遍历；27行文案/数量名称和3规则修订，原值/单位/来源/scope/状态/计数不变，见[整改](output/character_skills/remaining_five/RECTIFICATION.md)。P3B4 N1已[复验闭合](output/character_skills/review/p3b4_20261019_type9/RE_VERIFICATION.md)，旧交接/审查快照不改。
  **P3B5 F1已由原D R2复验通过，闭合无剩余阻塞**：[最终报告](output/character_skills/review/p3b5_20261019_remaining_five/REPORT_R2.md)，上段初审/整改为历史快照。
  **P3B6 已独立D带范围限制通过（阻塞0、整改0）**：[交接](output/character_skills/P3B6_HANDOFF.md)、[证据与命令](output/character_skills/description_bindings/p3b6_batch/README.md)。3条type26与6条自身F0/Boss type5纯直线句采用冻结集合的受控结构规则＋raw/native对应，新增9唯一/9页片段及9唯一/9页效果槽，字段+0。type5伤害保持公式，运行时能力/武器flag可另调整，不保证实战全敌命中或最终伤害。cid29的2/2原有片段真实对应且无断链，按原标准自然从部分→完整；24未知字段照留。其他8受影响角色状态不变；旧82013完整字段对象/重复数、277旧已用规则、101/31/type8/type26旧绑定原样。当前描述41595＝真实91＋提示11601＋未知29903；未改完整标准/分母或verify期望。C自检原生10/10、专项9/9、边界91/91、原JSON9/9、GBK8次、DOM14/14、verify189/189与A—P通过，[独立D报告](output/character_skills/review/p3b6_20261019_batch_bindings/REPORT.md)已确认限定队列和完整cid29；旧C交接PENDING保持历史状态。
  **P3B7 R1 F1整改完成，待原D R2**：[交接](output/character_skills/P3B7_HANDOFF.md)、[证据/命令](output/character_skills/description_bindings/p3b7_batch/README.md)。仅80条type26完整开局基础玛那句，实际新增80唯一/80页/80角色及80/80效果槽，字段+0；当前描述41595＝真实171＋提示11599＋未知29825（目标78未知、2提示升级）。角色状态迁移0，仍2235部分/0仅未知/1完整，cid29保留。新原生8/8含204过滤样本；metadata→ctor→实际双向缓存映射→消费者→精确类型比较，26/1073/1077子消费者拒绝；初始化枚举/对象/泛型接口夹具及保护值解码stub明示，不是全引擎/实机。199子源/65类型不扩研究，其他系统授予/旁句保留。旧82013完整答案/重复数、277用规则/源287、32旧绑定、101/31及非目标对象精确保留；专项10/10、边界1140/1140、raw80根+199子引用、GBK12次、DOM165/165、verify189/189、A—P及12产物稳定性通过。
  F1更正与定向交接：[RECTIFICATION](output/character_skills/description_bindings/p3b7_batch/RECTIFICATION.md)。80玩家页面引用以外，全选源9169条charainfo有82原始引用＝80范围内＋2范围外敌用引用（75370/75528→3233），后两明确排除于玩家语义和输出。现冻结全表skillid[1+]引用及名册/links/profiles范围身份，原表增删/槽位/源/分类变化可在root与links不变时拒绝；C定向6/6、80正例＋9变更反例通过，8054 GBK2次/DOM5项和12产物一次重建不变，112完整绑定及旧全部答案/状态/分母保留。原C/A与D R1证据保持冻结，旧“全引用”仅为玩家links范围的说法以本更正为准；不重跑原生/189/A—P。
  **P3B7 F1已由原D R2闭合，带范围限制通过，剩余问题/阻塞/需整改均0**：[最终报告](output/character_skills/review/p3b7_20261019_type26_batch/REPORT_R2.md)。上面R1待复验文字及旧C交接是历史冻结；80绑定与全部正式产物不因整改改变。
  **P3B8 C冻结待新D**：[交接](output/character_skills/P3B8_HANDOFF.md)、[证据/命令](output/character_skills/description_bindings/p3b8_boss/README.md)。自身F0/Boss type5纯直线22条＋type11全体HP回复15条，新增37唯一/37页描述、37/37效果槽、37角色各一句，字段+0；真实208/提示11599/未知29788，分母41595。按原标准仅2020/5023自然部分→完整，仍13/14未知字段，旧29完整对象不变。四flag单/多目标及type11实际列表/活动出场hero字节/存活/职业/逐目标Heal输入与一次执行有界原生9/9；伤害/回复均保留运行时B的公式和BY_TYPE。37原始CID身份/自身上下文及13另域denju分别冻结，12普通同号数字不当charainfo引用。C专项10/10、边界565/565、raw37+13、GBK12次、DOM80/80，verify/A—P与一次相关稳定性机器结果见本批；全部旧82013完整答案/重复数、277用规则/源287、112旧绑定/101答案/31片段及非目标对象保留，不称独立审查。
  当前数字：角色 2236、部分 **2233**／仅未知 **0**／完整 **3**（cid29/2020/5023，本批规则范围；第9批待D）；引用 48555＝已解析 48552＋断链 3；记录 15973；
  规则答案 **82875**（归一记录行求和 **82013**，另按父/所属记录/规则/字段键去重 **81996**；已逐条评审10095／按类型套用72780）；未解释参数槽 **427176**；缺口字段级 **5560**；
  十批累计新增：P2-1 `charainfo` 参数 **522**、P2-2 skilllist 8／26 **6209 页／2869 唯一**、
  P2-3 暴击双路径 **1179／1085／881**、P2-4 同叶四类 **999／963／672**、
  P2-5 复合分支 67／80／96 **8979／8979／6305**、P2-6 条件语义三件套 **9112／9112／7959**、
  P2-7 denju 传授必杀技 **3236 页／3236 记录级／210 新增唯一键**、
  P2-8 攻击系类型族 **14132 页／10000 新增唯一键**、
  **P2-9 执行侧裁决后的 F0 答案 1727 页／1727 唯一（全部 charainfo）**、
  **P2-10 heal 族与其余类型 5452 页／4050 唯一（80 条新规则，36 个类型）**（页／记录级／去重行）；
  P2状态累计迁移 **908**（268／173／97／1／1／39／**187**／**142**）；P3B5另迁移5人已由D闭合；P3B6 cid29部分→完整已由D确认，P3B7新增80描述但无状态迁移。
  暴击双路径已并入派发索引（路径 3 → **5**，夹紧 rate [0,0.5]／dmg [-1,2]；2012／3000／1008／1095
  经核实不在其上，登记 `read_elsewhere`）；`type8 param4` 的依据是「**无按类型分派的**读取路径」。索引侧现有
  两项常驻防回归检查：**双路核对**（Unicorn 仿真 vs 纯静态解码，5 路径 × 3001 type 0 差异）与
  **复合分支的路径重算**（规则槽必须是该分支真读的槽且抵达累加器）。
  **P2 第 5 批（复合分支 67／80／96／1036）已实施并过审查**：67／80／96 在同一条路径上被编译合并进同一 worker，
  改用**函数内可达性遍历**逐段定位换算链（20 条分支体与逐段地址写在 `composite_chains.json`），规则由该遍历重算后才产出。
  67 = 命中角色数 ≥ `param0` 时乘 `paramN`（计数＝`CalcCharaNum(cType, 职业位图=iParam0, 武器位图=_flag 低 32 位,
  出身=int(param8), 成员列表)`，含等于）；80 = 当前玛那满足 `isCurrentManaJob_or/and`（`param6` 选 or/and）时乘
  `paramN`；96 = 按 `min(玛那计数, param1)` 计入、系数在 `param4/5/6/7`；1036 = `paramN × hyperGauge ÷ 1000`
  （`hyperGauge` ＝ `BattleParam.get_hyperGauge` ＝ `[this+0x328]`，本快照无该类型记录）。
  **P2 第 6 批（条件语义三件套）已实施，第 6 批闭合了第 5 批留下的两处缺证**：
  ① **96 攻击路径的 `[sp+0x18]` 标志＝调用方实参 `damageType == eDamageType.Skill(1)`**——Skill 时读
  `param3`（攻击 ×(1+`param3`×计数)），其余伤害类型读 `param2`；两个调用方（`CharaBehavior.Attack` 透传当次
  伤害类型；`BattleParam.UpdateParam` 固定传 0）已核实。
  ② **筛选位字典**：`iParam0` 职业位图（位 i ＝ JOB_TYPE i）、`flag` 武器位图（`_flag` 低 32 位，bit ＝ 22 +
  `WeaponKind`，掩码 `0x7fc00000`）、`param8`／`param9` 出身筛选值（两位十进制分组查游戏主表 `homelist`）；
  67／80／96 的这三类槽各自出可读答案，67／80 的阈值答案升级为逐值可读（只改文本）。**67 的三项筛选是「同时」
  满足，1059 是「任一」满足**——最易抄错处。
  ③ **type 1059 UnionCount 闭环**：门控＝`IsEnableAbility` case 1059（`GetAllCharaList` 逐角色、任一命中、
  计数 ≥ `int(param0)`）；数值＝五个 `PlayerManager.GetAbility*` 按静态 rank 表（rank=121／offset `0xf2`）
  取本类型 flag index 后应用 `param1..param5`（队伍范围，固定倍率不随人数缩放）；另有周期回复
  `int(param6×目标最大HP)`（间隔 `param7` 秒，目标按 `iParam1`／`flag1`／`param9` 筛选）。
  新增 **9112 页／9112 记录级／7959 去重行**，可达角色 67→513／80→166／96→52／1059→432（去重 919），
  **1 个角色由「仅未知」变为「部分」**；相对 P5 终态快照 **0 键丢失、0 raw／kind／unit／status 变化**
  （1414 条只改条件文本且首个数值 0 变化）；重跑全链 16 份关键产物 SHA-256 逐字节相同。
  **P2 第 6 批已过第三方审查**（`review/p2b6_20261018_thirdparty/`，结论「通过」＋5 条文字注记）；
  5 条注记已在本批第 0 项整改（交接地址笔误、`--cid 2205`、门控特例实为 ≤0、玩家侧 ParamN 极值选择补注、
  武器跳转表表项为字节），只改文字、不动数据与规则。
  **P2 第 7 批（denju 传授必杀技，1500 角色）已实施，待针对性审查**：
  ① **结构结论：denju 行没有参数槽**——1504 行的键集是 `denju_id`／`develop_only`／`scost`／`sname`／`stext`／
  `timestamp`／`patternid0..5`，**没有 `skillparamN`**；效果类型与数值在 `denju.patternidN → bosspattern → bossskill`
  链上（946 行有 patternid／995 个引用字段：缓存 231＋APK 758 可解析；6 个字段两源都缺，逐条列出）。交叉证据：`denju.sname` ＝
  所指 pattern 的 `sname` 950 个引用字段一致、`denju.stext` ＝ 该 pattern `sinfo` 820 个一致
  （按 995 个 `patternidN` 引用字段计，不是按行）。
  ② **原生链路**（`denju_skills/native_checks.json` 17/17 复读）：`BattleParam.CreatePlayer` →
  `BtlCharaUtil.GetBattleDenju`（门控 `EnableDenjuSkill`：接收方 `isDenjuFrom`＋传授方 `isDenjuTo`＋同 `jobtype`＋
  `daLimitBreakDenju.GetDenju≠null`）→ `BattleParam.InitlizeDenjuSkill`（`_denju@0xa20`／`_denjuSkill@0xa10`／
  `_denjuListPattern@0xa18`）→ `BtlCharaUtil.GetDenjuSkill`（＝`CharaParamToBossSkill` 出参 `_denjuSkill` ＋
  `GetDenjuPattern`（`daLimitBreakDenju`，即 `denju_lblist`）出参 pattern 列表）；战斗执行时
  `BtlCharaUtil.GetExecSkillInfo` 用 `_denju` 取名字/费用、以 `_denjuListPattern` 调 `bhExAttack.think_attack`
  ⇒ **攻防数值来自 denju 链的 pattern→bossskill**，与 `CharaParamToBossSkill`（传授者自身角色参数）是两个不同来源。
  ③ **应用与增量**：`denju.patternidN` 走与 `charainfo.patternN` **同一个** `resolve_pattern` 助手，把该 pattern 的
  bossskill 挂成 denju 记录的 `boss_skill_refs`（＋`boss_skill.s_ability` 交叉引用），类型/数值按已确认 boss 规则出答案。
  新增 **3236 页／3236 记录级／210 新增唯一键**（按类型页和：13→2296、2012(SA)→456、105→184、112→147、27→100、
  66→29、16→24）；可达角色 **579**；**1 个角色（cid 12021）由「仅未知」变为「部分」**；未解释参数槽
  417790 → 449862（＋32072 全落在新挂上的子记录，既有记录未解释键 0 减少）；断链 0 → **3**（denju patternid 两源缺口，
  非关联错误）。**零破坏**：既有答案键 0 丢失、raw／kind／unit／status／scope 0 变化；457 条文本变化全部来自第 0 项
  注记 3（1059 `/param0` 特例句改 ≤0），首个数值 0 变化。
  区分性样本：**148 行传授版本与被传授者自身必杀技数值不同**（如 cid 253：链上 `skillparam1`＝0.3 而角色自身＝6.5，
  页面显示链上值）＋102 行类型不在自身链上——这类行**只按 ID 关联、不拿角色自身 skillparam 替换**；
  `denju_id ≠` 角色 `skillname` 的 224 行在 `link_status` 注明「只按 ID 关联，不按名称推断」。
  ④ 顺带修正**传授突破**（`denju_lblist`）子记录此前 5 个条目共用键 `cid` 导致 2—5 号条目内容不可见：
  改为逐条键 `cid#i`（＋44 条记录，0 答案丢失），并把每个条目的 pattern 技能一并挂出。
  验证：`verify_p1.py` **149/149**、`crosscheck_raw.py` **A–M overall_ok**（M 区 2600 条 denju 页答案＋519 条 SA
  从原始表重算）、`denju_skills.py` 原生自检 **17/17**、`skilllist_types.py` **53/53**；
  默认 GBK（`PYTHONUTF8=0`）**11 个入口 exit 0 且 stderr 0 字节**；重跑全链 **25 份关键产物 SHA-256 逐字节相同**。
  **P2 第 8 批（攻击系 boss 技能类型族：伤害基数定位与逐槽规则）已实施，待针对性审查**。
  · **伤害基值定位**：`bhSkill.Exec_ATTACK_*` 家族的伤害输入一律是 `floor/clamp(float32(B × skillparamN))`，
  `B = bhSkillUtil.getBasicSkillAttack(true)`（`0x1182ed8`，入参 `w1=1`），整数化 `0x14374bc`
  （`frintm`/`fcvtms` **向下取整**后夹到 int32；`+inf` → int32 最小值）——与 type105／type112 是同一条函数、同一个助手。
  · **P2-1 的「全局技能表」候选被否**：`[[0x29e9000+0x6e8]]+0xb8` 的三浮点被 `skillparam4` 缩放后**加到施法者位置上**，
  作为 `BattleManager.FindNearPosition` 的搜索中心（攻击起点偏移表），不是伤害表。
  · **逐槽规则 35 条**（与既有字典零重叠）：type0 `sp1`/`sp3`；type1 `sp1`/`sp2` 间隔秒/`sp3` 次数（推力**硬编码 0**）；
  type2 `sp1`/`sp2` 突进位移/`sp3`；type3 `sp1`/`sp2` 范围长度/`sp3`/`sp4` 起点偏移缩放；type4 `sp1`/`sp3`；
  type5 `sp1`/`sp3`（×Chain 后进 `Bullet._pushPower`）/`sp4` 子弹半径；type22 `sp1`/`sp2`/`sp3`/`sp4`；
  type47 **`sp0`** 才是伤害倍率（`sp1` 是爆炸类型、`sp2`·`sp3` 是爆炸半径、`sp4` 推力、`sp5` 第二段伤害）；
  type105 `sp4`/`sp5`（`sp1`·`sp6` 既有）；type110 `sp1`/`sp2`/`sp3`/`sp4`/`sp5`/`sp6`。
  · **证据强度分两层**：`伤害倍率`与`推力`由**分支可达体重算**（沿调用图回溯 `fmul` 操作数到 `_skillparamN` 装载点，
  且只允许从该 type 的 handler 可达的调用点，避免 type0／type1 共用 `AttackList_Common` 时串槽）；其余槽由
  **钉死 RVA＋重读指令字节**核对；数据侧另有 `0.001` 哨兵交叉印证（只在推力槽密集出现）。
  · **受控执行**：Unicorn 跑真实字节执行 `0x14374bc`（`12.7→12`、`-0.5→-1`、`inf→-2147483648`）并对每个 type 的
  `fmul` 复算一次；`boss_attack_types.py` 自检 **85/85**。
  · **应用与增量**：新增答案 **14132 页／10000 新增唯一键**（`records.jsonl` 行实例 14124）；规则答案 60189 → **74321**；
  未解释 449862 → **435730**；可达角色 **846**；**39 个角色由「仅未知」变「部分」**（部分 1863→1902、仅未知 373→334），
  其中 21 人经 `charainfo` 等价门控，其余经自身 pattern 可达的 boss 技能与／或传授链（逐人归属见
  `boss_attack_types/p8_increment.json` 的 `unknown_reachability`）。
  · **脱贫上限的诚实说明**：其余 334 个未知角色多数是 `NOT_AMONG_OWN_PATTERN_TYPES`（`skillid[0]` 不在自身 pattern
  的类型集合内，没有可对齐的 boss 记录）与 X1，**等价门控不通过**——不是缺规则而是缺等价前提。
  · **零破坏**：既有答案键 0 丢失、raw／kind／unit／status／scope 与文本 0 变化；`bossskill|105|/skillparam1` 仍由既有字典定义。
  · **验证**：`verify_p1.py` **163/163**、`crosscheck_raw.py` **A–N overall_ok**（N 区 14124 条新规则答案从原始表重算，0 失配）、
  `denju_skills.py` 17/17、`charainfo_types.py` 37/37、`skilllist_types.py` 53/53；默认 GBK **14 个入口 exit 0 且 stderr 0 字节**；
  全链重跑 **67 份产物 SHA-256 逐字节相同**。
  · **第 0 项**：p2b7 审查 4 处文档修正已整改（§5.2 缺证框架、§4 样本 type 13、§1① 补 `weaponChange`、§5.6 补 148 行口径），
  只改文字；同批把 `denju_skills.py` 的两处 note／检查名与 `charainfo_types.py` 的头部类型说明改为与本批结论一致。
  · **口径注记**：`charainfo_params/`（522 → 3131 → 4858）与 `denju_skills/p7_increment.json`（3236 → 6177）由生成脚本按
  **当前规则集**重算，各批交接记录的是该批闭合口径，`verify_p1.py` 已把相关数值断言改为从产物重算的结构式断言。
  **P2 第 8 批已过第三方审查**（`review/p2b8_20261018_thirdparty/`，「带明确限制通过」，3 处文字级问题＋2 条口径备注），
  3 处文字问题已在第 9 批第 0 项整改（见 §3.9）。

  **P2 第 9 批（必杀技执行侧裁决：X1／NOT_AMONG／F0）已实施，待针对性审查**。
  · **问题**：第 8 批把 334 个「仅未知」的主因归为「等价前提缺失」（NOT_AMONG 无可对齐 boss 记录／X1 两侧数值不同）。
  本批改为从**执行侧**回答「游戏到底跑哪一份」：`output/character_skills/cp_paths/path_evidence.json`（自检 18/18）。
  · **路径 A（自身 pattern 可解析）**：`OnClickSpSkill`／`CheckEntry` → `bhSkill.CreateExecSkillList` →
  `FindPatternCtrl` 命中 → `_CreateExecSkillList` 的 pattern 分支 → `pattern.getListBattleBossSkill()`
  （`BattleBossPattern.makeListBattleBossSkill` → `daBattleBossParameter.getBosSkill` = **boss 主表**）→ `Mission_execSkillPattern`。
  · **路径 B（自身 pattern 无可达技能 = F0，929 角色）**：`CharaParamToBossSkill(0x13aa390)` 读 `BattleParam`
  （`_atvSkillID`←`charainfo.skillid[0]`、`_skillparam0..9`←`CreateByID` 复制的 `charaParameter.skillparamN`）构造
  `BattleBossSkill` → `_CreateExecSkillList` 的 `pattern==0` 分支 → `Mission_execSkill`；`CheckEntry` 取列表第 0 项 →
  `SetExecSkill` → `bhSkillUtil.initialize_ExAttack`（把该 skill 的 `skillparamN`／`skillflag` 复制进 util）→
  `Execute` → `ExecSkill(w2=skillid0)` ⇒ **本记录原值就是执行值**。
  · **关键更正**：`BattleParam` 侧**不是** boss 主表侧（`CreateByID` 从角色记录复制），因此 **X1 的裁决是「执行取 pattern 侧」**、
  charainfo 副本不是执行值；区分性样本 cid 2315／6058／8139 的正文回数只与 boss 侧一致（无反向样本）。
  · **门控变化**：`equivalence.classify` 新增 `F0_NO_PATTERN_FALLBACK`（929）；`NOT_AMONG_OWN_PATTERN_TYPES` 收窄为
  「自身 pattern 存在但类型集合不含 skillid[0]」的 **20** 人（逐个定性见 `cp_paths/notamong_exceptions.jsonl`）。
  · **增量**：新增 **1727** 条答案（页求和＝唯一键，落在 **535** 个角色上）；**187 个角色脱贫**（部分 1902→2089、
  仅未知 334→**147**）；未解释 435730→**434003**。**剩余 147 人的原因变了**：不再是缺等价前提，而是**缺类型规则**
  （F0 134／E0 9／X1 3／NOT_AMONG 1；F0 桶 heal 族 `Exec_HEAL` 53、`Exec_FALL_AREA`＋`FALL_AREA2` 11、type23 14、type6 11、type7 11…）。
  · **数据侧印证**：F0 角色正文回数 51/51 与 `trunc(sp6)`（105／110）／`trunc(sp3)+1`（type1）一致；据此把 type1
  `sp3` 文案改为「追加回数；总攻击次数＝该值+1」（数值/kind 不变）。
  · **零破坏**：0 键丢失、0 raw／kind／unit／status／scope 变化；value 文本按整改项有意变更（见下）。
  **p2b9 审查整改（结论「需修正」，阻塞项 F1）已完成、待复验**：F1 把 type1 `sp3` 的**答案渲染层**改为
  「追加回数；总攻击次数 = trunc(sp3) + 1」（`rules.py` 新增按 `(type, kind)` 的模板分派；99 条实例，
  kind／unit／status 未变）、F2 type110 `sp6` 答案去掉「范围外也消耗预算」（820 条）、
  F3 type47 `sp4` 补 `SpreadBullet` 中转注记（45 条）、F4 16 条 F0 `/skillflag0_1` 补人读「证据路径」注记
  （1727/1727 全覆盖）、F5 订正交接散文的 147 归因数字（F0 134／E0 9／X1 3／NOT_AMONG 1；F0 桶 heal 族 53、
  `Exec_FALL_AREA`＋`FALL_AREA2` 11）。复查：`verify_p1.py` **174/174**、`crosscheck_raw.py` **A–O overall_ok**
  （新增 O 区逐条钉死答案措辞与 F0 注记）；实例级对账（`p9_increment.json` 的 `rectification_accounting`）
  lost 0／new 0、文本变更 964、只补注记 16、raw／kind／unit／status 0 变化。
  默认 GBK **17 个入口调用 exit 0 且 stderr 0 字节**；两轮全链重跑 **76 份产物字节无漂移**。

  **下一批建议**：① **剩余 5 个孤儿类型**：24（`Exec_LOCKED_CURSE`）、56（`Exec_TARGET_CURSE`）、
  68（`Exec_MANA_CYCLE`＋`common_Exec_MANA_CYCLE`）、73（`Exec_MODE_LAUNCHER`）——都是「非伤害／支援」型，
  需追各自的 work 对象；② `AirAreaStrike`（0x118380C）工作对象的 update（type 33/103 的伤害）与
  `AirStrike` 协程（34/50/64/72/76/86 的消费点）；③ 23 的 `0x118B0C8` helper 内三个浮点、87 的 sp0/sp5..sp9、
  43 的 sp7、84 的基值槽、19 的运行时整数语义；④ 运行时判定「该次必杀由传授链／英雄技承担」的优先级；
  ⑤ `AbilityTypeCachedFlagIndex` 的 rank↔type 表与 `charaParameter.get_home` 缺省；
  ⑥ 片段↔字段代码级绑定（「完整」长期为 0 的主因）、bosspattern（1307）与 extra_ability_info（494）。

  **P2 第 10 批（`Exec_HEAL` 家族与其余类型；里程碑 A 收官）已实施，待针对性审查**。
  · **问题**：第 9 批把 147 个「仅未知」归因到**缺类型规则**（不是缺等价前提）。
  · **`Exec_HEAL` 家族＝一个 handler ＋ 两个模式实参**：`bhSkill.Exec_HEAL(0x1299C74)` 的 `w2`＝对象选择、
  `w3`＝动作选择、`w4`＝类型 → `bhSkillUtil.Exec_HEAL(0x1187C80)`（第一跳转表 0x206DE44，4 项）→
  `Exec_HEAL_common(0x1188194)`（第二跳转表 0x206DE48，9 项）。动作→类型：0 回复(10/11/28)、1 支援(12/13/14)、
  2 支援(26)、3 护盾(15/16)、4 回复+支援(31)、5 回复+支援(32)、6 回复+支援+载荷(46)；
  对象→类型：0 自身(10/12/15)、1 同 `_type` 且职业位命中 `iParam0` 的存活成员(11/13/16/26/31/32/46)、
  2 再随机取 1 人(14)、3 再取 HP 比例最低者(28)。
  · **回复量**＝`floor/clamp(float32(B × skillparam1))`，`B=getBasicSkillAttack(true)`（0x1182ED8；与第 8 批
  攻击族同一函数），整数化 `0x14374BC`，交 `CharaBehavior.Heal`（0x1541158）的 healValue；
  **超上限（HP 上限）比率**＝`max(HealSkill_HealFlag(0x1182B4C) 的位表档位, 附加槽)`，
  附加槽 10/11→sp2、28→sp5、31/32→sp4、46 无（位表复用 `output/boss_heal/constants.json`）。
  · **支援块实参序取自 `SetSupport_noCheckTime`(0x17765F0) 自身的存储点**——该方法（与
  `BtEffect_LineExec_ContSupport..ctor` 一样）的**元数据 `parameters` 顺序与原生实参序不一致**，
  照元数据读会把防御系数答成标志位、攻速答成移动；12/13/14/26 乘 `_skillChainRate`，
  28/31/32/46 不乘（本批用不同 answer_kind 区分并逐条钉死）。
  · **FALL_AREA（33/103）**：sp3＝落点 X 偏移（`_type==0` 取负＋夹到地面范围）、sp6（仅 33）＝选择码；
  **伤害在 `AirAreaStrike`(0x118380C) 建立的工作对象里结算**（对象 +0x40 持有 util），未追进其 update → 伤害槽不给数值。
  · **其余类型**：6／7／19／23／29／34／36／43／44／49／50／51／55／64／67／69／72／74／75／76／80／82／86／87／114
  共 80 条规则（36 个类型）；34/50/64/72/76/86 的「技能基值×槽→整数化」已确认但**消费点未定位** → 答案写「消费点未定」。
  · **增量**：新增 **5452** 条答案（页求和）／**4050** 唯一键；**仅未知 147 → 5**（脱贫 **142**；
  部分 2089→**2231**）；规则答案 76048→**81500**；唯一记录 75207→**80659**；未解释 434003→**428551**；
  缺口字段级 5679→**5571**。仍未脱贫 5 人：cid 4009(24)／4049·8116(56)／10018(68)（F0）与 8151(73)（E0），
  原因是这 4 个类型未解出可交付槽位语义，**不是缺等价前提**。
  · **零破坏**：0 键丢失、0 raw／kind／unit／status／scope 变化、0 value 文本变化（独立复算
  `work/p10_paths/zerobreak.py`：75191→80642 实例）。
  · **验证**：`boss_heal_types.py` 219/219、`verify_p1.py` **189/189**、`crosscheck_raw.py` **A–P overall_ok**  （新增 P 区）、`charainfo_types.py` 37/37（`handler_slots_agree_with_confirmed_rules` 增加「由逐字节钉死的
  读取点覆盖」一路并说明扫描是下界）、P8 的增量恒等式改为结构式并注释原因；默认 GBK **19 个入口调用
  exit 0、stderr 0 字节**；两轮全链重跑 **82 份产物字节无漂移**；HTML 夹具 p1 **8/8**、p2 **25/25**。

  · **F1–F4 整改**（p2b10 审查，只有文本与一条漏规则）：F1 type46 的 sp5 实为超上限附加档位（与 type28
  共用 0x11882AC，按 ARM64 标志位语义读分支）→ 补 `bossskill|46|/skillparam5`（**147** 条实例，
  页答案 5305→**5452**、唯一 3953→**4050**）；F2 类型数 39→**36**；F3 DOM 夹具计数改 p1 **8/8**、
  p2 **25/25**（原先把 `ALL DOM CHECKS PASSED` 汇总行也计了）；F4 去掉答案里与模板重复的注记句并新增
  `p10.answers_have_no_repeated_clause`（覆盖 80 条规则、重复 0）。整改后：`boss_heal_types.py`
  **219/219**、`verify_p1.py` **189/189**、`crosscheck_raw.py` **A–P overall_ok**（P 区 `type46_sp5`＝147）、
  零破坏 lost 0／文本 0 变化、默认 GBK 19 入口 exit 0、两轮 82 份产物无漂移、DOM 8/8＋25/25。

- **完整解包**：[阅读说明](output/full_unpack/README.md)、[输入账本](output/full_unpack/ledger.jsonl)（68993行，来源/格式/状态/输出/理由）、[对象产物](output/full_unpack/objects/)（56类目录，每包objects_index.json）、[覆盖统计](output/full_unpack/coverage.json)、[4项验证PASS](output/full_unpack/validation.json)、[cid附加索引](output/full_unpack/cid_index.json)（6233个，仅命名规律）。重跑：full_unpack_run.py（分片续跑）→merge→verify→finalize。

- 最新入口：[原对照页](output/card_comparison_cid30236/index.html)，顶部含1095、1017、2012、3000、99、7、1008七个独立检索区，分别按普通技能名称/ID/原文检索407/321/406/382/133/64/37条；原チーカ101项及截图对照保留。无需联网。
- [1008对象/当前地形/接受者攻防依据](output/ordinary_effects/ability1008/README.md)、[389项本轮局部原生检查](output/ordinary_effects/ability1008/native_checks.json)。查询`query_effect_dictionary.py --id 43023606`看沙漠本项攻击/减伤各12.5%；`--id 102070`看攻击5%、防御原值1；`--id 42011507`看607=7或6。target_conditions列地形，trigger_context列提供者/接受者及后备边界。
- [7地形编码/当前背景/自身攻防依据](output/ordinary_effects/ability7/README.md)、[1390项本轮局部原生检查](output/ordinary_effects/ability7/native_checks.json)。查询`query_effect_dictionary.py --id 43023607`看沙漠与5%本项攻防；`--id 102071`看代码/正文矛盾；`--id 47000707`看原值250；`--id 47000830`看1320或条件。
- [99门槛/目标/攻防/正时间及-1依据](output/ordinary_effects/ability99/README.md)、[192项既有原生检查](output/ordinary_effects/ability99/native_checks.json)。查询`query_effect_dictionary.py --id 43023616`看攻防/30游戏秒；`--id 42080504`看仅暴击触发与-1标记；`--id 127008`看缺攻防字段，不填0。
- [3000共鸣资格/Support3/四字段依据](output/ordinary_effects/ability3000/README.md)、[86项既有原生检查](output/ordinary_effects/ability3000/native_checks.json)。查询`query_effect_dictionary.py --id 43023611`得普攻/技能各+.1、45游戏秒、暴伤系数+.1；`--id 40121710`得四项缺失及资格上下文，未补默认值。
- [2012时间/暴击/动作门槛依据](output/ordinary_effects/ability2012/README.md)、[49项既有原生检查](output/ordinary_effects/ability2012/native_checks.json)。查询`query_effect_dictionary.py --id 40431614`或`--id 40126713`，在`trigger_context`看动作/目标输入和字段缺失状态。
- [1017对象/职业/攻防依据](output/ordinary_effects/ability1017/README.md)、[236项既有原生检查](output/ordinary_effects/ability1017/native_checks.json)。查询`query_effect_dictionary.py --id 40768606`会在`target_conditions`集中显示param0/iParam0，未知其他参数保留。
- [1095范围与依据](output/ordinary_effects/ability1095/README.md)、[32项既有原生片段检查](output/ordinary_effects/ability1095/native_checks.json)。快速查询：`.venv\Scripts\python.exe -B scripts/query_effect_dictionary.py --id 40129301`，也可`--name 祈りの聖女`；Boss需显式`--table bossskill`。返回原记录、中文解释/依据、未知原值，不混命名空间或同名版本。
- 当前主进度：[逐描述效果CSV](output/card_comparison_cid30236/description_effects.csv)、[JSON](output/card_comparison_cid30236/description_effects.json)，HTML攻防表同源生成。逐效果清单已扩展101项，101项已有原文明示数字或限定单项配置数值/公式、0项数值空缺；首批攻防单列40/40。五组采用值为屏障动态固定量公式（默认系数1时玩家路径名义原始ATK20%）、Class暴击+40个百分点、暴击回复25%、Chain每次有效事件阈值10%、敌方弱化30游戏秒；截图5%/20%/20%/20%/45秒保留。详见[裁决政策](output/card_comparison_cid30236/difference_sources/adoption_policy.json)。
- 同目录 [CSV](output/card_comparison_cid30236/comparison.csv)、[JSON](output/card_comparison_cid30236/comparison.json)、[54条完整来源记录](output/card_comparison_cid30236/evidence.json)、[manifest](output/card_comparison_cid30236/manifest.json)。
- 旧概览33项（含等级/素材等目标外项目）：13项文本/局部规则已对应、3项截图数值已裁决、11项分组原值尚有解释边界、2项其他差异、2项未建立对应、2项网站添加排除。这不是完成率；屏障/Chain所在分组仍保留raw，不影响其中数值取值已裁决。
- [type105证据](output/boss_chain/type105/README.md)、[type112证据](output/boss_chain/type112/README.md)、[type13基数证据](output/boss_chain/type13_basis/README.md)、[合并77条限定规则](output/card_comparison_cid30236/field_dictionary.json)、[2684来源记录/6613存在字段CSV](output/card_comparison_cid30236/verified_parameter_views.csv)（同目录有JSON）；105为142/284、112为96/657、13为718/718（玩家基数换算有条件）。v3历史字典不改。
- 当前核心原值：[records.jsonl](output/cache_full_20261015_v3/records.jsonl)，39047个记录/文档视图，134个表；完整JSON见同目录 decoded。
- 当前核心包含1488条角色、8634条普通技能、2149条Boss pattern、3745条Boss skill。角色条数不等于可用卡牌数。
- [全量缓存说明](output/cache_full_20261015_v3/README.md)、[最新核心指针](output/cache_full_latest.json)。
- [字段字典](output/cache_full_20261015_v3/analysis/field_dictionary.json)：4671项字段观察，绝大多数不能当作已解释语义。
- [核心覆盖审计](output/cache_full_20261015_v3/analysis/coverage_audit.json)、[引用](output/cache_full_20261015_v3/analysis/references.jsonl)、[未关联项](output/cache_full_20261015_v3/analysis/unresolved_references.jsonl)。均有对应CSV视图可筛选。
- [后续下载核对入口](output/cache_refresh_latest.json)、[刷新说明](output/cache_refresh_20261015/README.md)、[当前组合清单](output/cache_refresh_20261015/composite_inventory.jsonl)。
- 最新刷新取得165个新增bdl，77个data5与v3密文及解码JSON一致；因此主表查询仍可使用v3。
- 最新可访问外部缓存清单68993文件：77 data5、68655 bdl、261其他。未变化媒体仅大小/mtime核对，非全文件双端哈希或原子快照。
- 原始全量包：raw/phone_20261015_full_02/external_cache.tar；补充包：raw/phone_20261015_refresh_02/external_cache.tar。不要改写。
- 已审查E构建：[build_261ac189c316abba](output/export/snapshot_223183400c1c62013338/build_261ac189c316abba/manifest.json)。它是较早输入的稳定交付，不能冒充最新全量缓存。
- [正式E说明](output/export/README.md)、[复审报告](output/审查报告/阶段E独立交付复审报告_2026-10-15.md)、[历史进度](STATUS.md)。

## 2. 已确认规则与证据

- 数据记录保留原始字段、缺失、数组顺序与重复、字节定位及SHA；不得静默补默认值。
- 逐ID条件回退：指定JSON表查不到ID时才走APK/AB；不逐字段合并。主表存在不证明玩家已解锁或当前实例已安装。
- 普通技能子效果只按已证实的单层执行语义展开；不能把递归图遍历当作游戏执行。
- 阶段D安装/资格/来源证据脚本：scripts/phase_d_trace.py、phase_d_chain_probe.py、phase_d_source_rule.py；详见STATUS与阶段D审查报告。
- Boss pattern按有序技能槽引用Boss skill，普通skilllist同号ID属于另一个命名空间。
- [Boss链规则字典](output/boss_chain/field_dictionary.json)、[追踪](output/boss_chain/trace.json)、[受控片段结果](output/boss_chain/native_checks.json)。
- type13：攻击输入乘skillChainRate，形成1+输入；防御参数乘chain和接受者_normalAtk再整数化，是固定防御量；移动形成1+输入。
- type27：回复输入乘getBasicSkillAttack(true)再整数化；间隔与次数来自对应参数。初始化计时0，更新可能立即回复，一次更新最多一次；不是完整战斗仿真。
- [时间/回复规则字典](output/boss_heal/field_dictionary.json)、[追踪](output/boss_heal/trace.json)、[常量](output/boss_heal/constants.json)、[13项受控检查](output/boss_heal/checks.json)。
- type13.param3和type27.param2单位为游戏秒，沿fixedDeltaTime链确认；非墙钟秒。
- type27技能高32位的42/43位对应1.6/1.8上限档位；其他能力旗标仍可能合入。不要套到ability21。
- [可用局部参数视图](output/boss_heal/verified_parameter_views.json)：772记录、3084字段；不是全效果解释。
- [Elemia样例](output/boss_heal/cid2327_description_fields.json)：54行；其语义不能不加条件转用到チーカ。
- type105：param1是单次前方攻击的技能基值系数；Attack整数输入=floor/clamp(float32(getBasicSkillAttack(true)×param1))。Chain在基值内乘一次；基值含BattleParam._skillAtk、状态与技能等因子，面板ATK换算及最终扣血未验证。
- type105.param6是每目标尝试上限，有限正数向零截断；在范围判定前计数，持续在范围内的样例为5次Attack调用，离开范围也消耗预算。仅推广type105的142条/284字段，不推广到type112。普通/沙漠/超共鸣明确映射43023601→00、00→05、02→09，系数3.5/3.75/4.25。
- type112.param1：设置时算floor/clamp(float32(getBasicSkillAttack(true)×param1))，Chain已在基值内；整数经CoveringFirePoint→BulletDelay保存后原样传到Attack/AttackOther入口。六条Boss技能普通02/03=.75、沙漠06/07=.875、超共鸣10/11=1.125。只解释单次伤害输入，不套用type105次数规则或承诺最终扣血。
- type112.param5：每陷阱对象共用爆发上限，有限正值向零截断；本卡5次。param0=1有敌才消耗次数，2为定时模式；param4=.25为游戏秒间隔，无敌仍累积计时，一次update至多一次。16项原生片段检查（含既有8项伤害）通过；缺失param4/5不补0。
- type112.param8=88725为6×3位图，bit i为(i%6,i//6)，置位0/2/4、7/9/11、12/14/16共9格；初始战场6×3，边界按运行时尺寸夹原点。param9=1不清理旧对象，两段都执行时9格各2层。param7=.001推力经Attack进入允许条件下的DamageL(10)请求，原文転倒的视觉动作对应为推断。23项受控检查通过。
- type13.param2名义基数：已核CreatePlayer缩放片段使用.1×CardInfo.ATK及初始化因子后截断，故.3/.325/.375可对应名义原始ATK3/3.25/3.75%；接受者当前normalAtk仍含后续修正，不能用该名义系数直接算最终guard。7项片段检查通过，含双重截断反例。只对已核玩家构造路径作此换算。
- HighHPAll ability1105既有局部规则保留；给定列表的实验结果不等于实际装载或最终倍率。

## 3. 尚未解决：缺数据/关联与缺解释分开

缺数据或覆盖依据：
- 没有可信全游戏目标资源索引；私有目录、服务端范围未知，不能宣称全游戏100%。
- bdl已整体解码展开（见上完整解包入口）；对象语义未解释属字段解释线，不再是"已取得但未识别"。APK内置媒体未批量导出（索引已有），需要时按同一UnityPy管线补。
- cid30236卡面资产绑定未建立；不能据此断言文件不存在。获得来源和登场日期按用户补充属于网站添加，不再算提取缺口。
- 全缓存引用审计还有66处未关联引用（Extra 60、传授pattern 6）；保留未关联项，不删除记录。

前阶段单项数值清单已无空项，本阶段五组截图取值已裁决；以下边界保留，不再作为本阶段阻塞：
- 屏障实际战斗规则/当前normalAtk修正未知；采用公式，不能把默认名义20%当无条件20%减伤。五组截图注数成因未知，未宣称版本更新或截图与解包数字相同。
- 羁绊102071名称/父文案写砂漠，自身text写森林，源内矛盾保留；本轮已核7.param0=4是沙漠编号，经1<<4匹配背景flag16。其他类型地形输入不自动套用。
- 玩家当前装载/解锁、全部叠加/最终HP，完整候选队伍范围、陷阱动作视觉/抵抗/最终扣血及pattern选择均未纳入本数值Goal验收。
- 等级/突破到ATK/HP成长公式、职业/武器显示链和卡面绑定属后续范围。原始资源/历史证据不变。

## 4. 已解决，不应重复调查

- 羁绊106001缓存缺ID，已在APK同名空间找到并按既有逐ID回退；该数据缺口已解决，完整来源见[必杀威力证据](output/card_comparison_cid30236/skill_power/README.md)。

- A—C提取/解码路线已成立；不用重新从APK字符串搜索开始，不需要完整IL2CPP恢复。
- bossinfo.data5缺件已补齐并解码；全77个data5已导出，不能继续沿用“只取得11个”的旧判断。
- 后续下载确实已补采：新增165个bdl，主表77个未变；不再因旧ADB离线记录要求用户重下缓存。
- E指针复用修复完成：5种指针场景、12检查+4原生结构场景通过，新旧10载荷一致。
- 本轮没有重新执行这些历史测试；结论引用已有证据，不冒充新测。
- 不重做无新证据的穷举、不Root、不清缓存、不安装模拟器；不新增全量双端哈希门槛。
- 中文名、标签、外部资料、获得来源和登场日期按用户说明属于网站添加；后两项为2026-10-16补充，不据此断言游戏文件中绝无相关信息。

## 5. 当前可复用字典进展与下一最小动作

本轮只处理普通`skilllist.ability=1008`（TargetStageAll）。37条param0/param1/param3全存在，共111字段（净新增108）；旧攻防两规则扩大，新增地形规则。字典现77规则，视图2684来源记录/6613字段；普通子集1723来源记录/4947字段、60规则。背景99条仍为辅助证据，不计新角色数。

- 对象已核：PlayerManager当前param是接受者；提供者候选来自BattleManager.GetAllCharaList(0)→_aChara_Player@70，非空且存活活动。实际类型筛选、IsEnableAbility、1008地形判断执行；本类型段无自身排除、接受者职业或距离测试。可含自身或其他队友，不能套7自身范围或1017职业掩码。安装数组/位缓存、候选列表内容仍是夹具输入。
- param0沿相同IsTargetStage→当前背景→源flag路径，复用7地形证据及相同镜像SHA；9种源编码为2/3/4/13/15/20/325/607/1320。新编码3、607分别对99源背景验证，607是7或6。其他7编码复用既有匹配表，并在1008全部37条攻防样本实际经过地形路径。背景名仍按实际匹配行列ID/flag/原名/来源，不编造唯一正式枚举。
- param1乘接受者本项攻击，增加=(raw−1)×100%；param3乘接受者本项受伤量，减伤=(1−raw)×100%，原值1为中性。43023606在沙漠下本项攻击/减伤各12.5%；102070为攻击5%、防御原值1。两段不乘Chain；本轮不推广同记录param2/4/5或敌方管理器。
- 非活动提供者转独立后备路径，该generic BackUp段筛选另一类型并查IsTargetHome；未证明1008的后备安装/转写。40526403原文提及后备仍原样保留，不把文本升级为1008直接生效结论。敌用47000910保留同表数据，不推定玩家管理器实际装入。真实安装/解锁、完整叠加/最终HP仍另论。
- [新trace](output/ordinary_effects/ability1008/trace.json)含37完整源记录、99背景、9编码匹配表、方法/对象字段/片段与SHA；[389检查](output/ordinary_effects/ability1008/native_checks.json)：新编码背景198、37条攻防命中/不命中148、同人/不同人和职业0..5共24、当前背景覆盖4、混入其他类型/缺1008共4、存活活动路由8、候选列表getter3。缺ReadOnlySpan元数据槽的初次局部失败已补夹具槽后通过，未改原值/机器码；未重跑7既有1390项。
- 同一字段模块/主生成器/逐效果/查询/验证器更新，新增ordinary_1008_probe.py及限定证据；HTML第七区37记录/111字段，查询target_conditions列地形，trigger_context列范围。1008相关原逐效果行补param0/对象条件/依据，保留101项、旧状态及截图。未手改HTML。

实际运行：新1008探针389项、主生成器、验证器71项数据/结构检查通过；命令行43023606/102070/42011507与Boss同号隔离通过。37技能/99复用背景字节定位、原值/类型/换算、CSV/JSON/manifest/本地链接、前六类型和101项/五组政策均核。七段生成页实际搜索脚本在V8 DOM夹具14项筛选/隔离/恢复通过；file协议既有限制保留，未做视觉验收。旧原生证据只读，不重跑A—E/核心全量校验/手机。

已解决不重查：1008玩家侧活动提供者→当前接受者范围、param0资格/编码及两攻防字段；7及102071代码地形、前五类型和五组取值政策均有效。[旧数值审验](output/card_comparison_cid30236/completion_audit.json)仍只绑定冻结载荷；本轮看[validation](output/card_comparison_cid30236/validation.json)的reusable_1008/native_checks_reusable_1008及71项检查，非独立审查。

下一最小动作：只定向核40526403“后备亦生效”原文与1008活动提供者路径的关系，先沿该卡后备安装/转写及独立Backup记录查现有证据，不泛化其余角色/效果。该边界不影响本轮37条原值及活动路径规则可查。15%剩余额度暂停线保留，最近可见剩16%。

## 6. 重建对照页

从项目根目录运行 `.venv\Scripts\python.exe -B scripts/build_chica_comparison.py`。
生成器仅标准库，读取当前records.jsonl、Boss旧证据及本目录ordinary_rules/skill_power/timed_support/barrier/critical/movement/lifesteal/field_time/mana_chance/chain_mana/leader_condition/super_counter/wedge_time及barrier_request/difference_sources/chain_dispatch、ordinary_effects/ability1095、ability1017、ability2012、ability3000、ability99、ability7、ability1008已有证据和用户取值政策；需自行提供output/card_comparison_cid30236/reference.png（B包不含该截图）。
主生成器写output/card_comparison_cid30236/，新增1095/1017/2012/3000/99/7/1008证据脚本分别只写output/ordinary_effects/下对应类型目录；不会修改原输入、正式E构建或审查报告。
页面含101条逐效果表（首批攻防40、其余61）、33项旧概览与54条完整记录；77条限定规则/2684来源记录6613字段均同流程输出，另含407条普通1095、321条普通1017、406条普通2012、382条普通3000、133条普通99、64条普通7与37条普通1008的独立检索区块；CSV/JSON和manifest同步生成。type112视觉对应为推断、type13玩家基数换算有条件，未冒充实机结果。重建后运行 `.venv\Scripts\python.exe -B scripts/verify_chica_comparison.py`。
既有浏览器file协议安全限制保留，未完成视觉验收；本轮HTML结构、本地链接及搜索脚本DOM夹具已核对。已提供本地HTML文件，可双击打开。
