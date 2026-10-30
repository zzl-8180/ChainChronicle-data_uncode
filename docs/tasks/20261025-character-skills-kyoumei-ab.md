# 共鳴必殺本体 A/B 档模板批 任务书

- 日期：2026-10-25。状态：**本批收口（独立初审 PASS、零阻断，无需修复轮）；方向复核在途**。独审 `output/character_skills/review/kyoumei_ab_20261025_deepseek/REPORT.md`（dwfrun-5503f2e3，V4 Pro GA high；8/8 链独立重建、5键语义、零变化、对账、§1.3、容量回执全过，复跑 check_rules_diff 与 verify_full 17/17）。阶段一 dwfrun-ff9cde41（75,473,819 token）；阶段二 dwfrun-67802074 完成：生成链接入、容量处置后验全 PASS、正式重建 2236/2236、verify_full 17/17（含主持 world.run 独立复跑）、账本 9/9、A7 29/29、隔离复跑 14/14。**版本**：campaign `03172aef111a00661eaae6e89f3772ce4920b8b703934ef6771098e9be6a8cb2`，snapshot `03172aef-de6030e7dceb858d`，rules SHA-16 `de6030e7dceb858d`；新增答案 8、旧答案 0 改、backlog 78,313、YG1 视图 776、RETAINED 8/12。主持为本会话 kimi-k3-260716。主持预置 `output/character_skills/kyoumei_ab_20261025/baseline_rules_fingerprint.json` 与 `check_rules_diff.py` 机械门。
- 规则引用：`docs/角色技能完整解读实施方案.md`（2026-10-24 修订、生效日 2026-10-24，含 2026-10-25 §1.3 补充）全部现行条款；本任务书按 §5 第 0 步要求注明路径与版本。
- 依据研究：YG1 研究 workflow `dwfrun-52578137-623d-47a4-8820-f22685038eec`（2026-10-23，GLM 10,608,331 token，纯勘察未改生产文件）；范围文档 `output/character_skills/inference_inventory/yg1_sympathy_damage_research.md`；证据索引 `output/ordinary_effects/sympathy_damage/README.md`＋`evidence_index.json`；分析 JSON 与可复现脚本 `work/character_skills_yg1_research/`。

## 1. 本轮目标与判定（§4 四件事）

**做什么**：把当前 backlog 中 YG1（共鳴必殺本体，page_group=special_move）未解效果里属 A/B 档的项，接入既有规则键与公式级答案；383 个拆分项随行逐行处置。伤害链已查明：bosspattern（flag 8192 共鳴 332／32768 超共鳴 186）→skillid0→bossskill 类型分派（skillparam1=单次倍率，公式 floor/clamp(float32(B×pN))，B=bhSkillUtil.getBasicSkillAttack 已含 Chain）＋skillid1→t13 buff（批 6 槽位已确认）＋s_ability→SA 子效果（2012/2003 批 8/10 已消费）。

**影响路径**：推断层新增本批模块；rules.json 仅限 B 档 7 个空壳键的规则化升级（bossskill|55|/skillparam1、|74|/skillparam5、|51|/skillparam0、|114|/skillparam1、|64|/skillparam1、|76|/skillparam1、|103|/skillparam3），旧键逐字节不变；页面/账本/选题链随正式重建随动。

**怎么算对（同类判定）**：
- 逐行门控：竞争句判定、charainfo 行记录级等价门（批 1 先例——charainfo 是伤害侧未执行副本，门控不严不得消费其内联值）、multi-carrier 判定；词面 tier 是机械分类，**实施必须逐行审核**，误桶按实际降 A/B/C 或留 hint，不按研究期 479/70 机械立项。
- 倍率答案带公式、基准（B 已含 Chain）与适用档位披露；B 档空壳键升级须逐键 pin 复验全过，按 CONFIRMED_FORMULA_ONLY／BY_TYPE_EXTRAPOLATED 先例（cid 89/93/283 既有消费）出公式级答案；无证据项保留未知，不填零不猜。
- type55 的「一定間隔」间隔数值、范围槽属 C 档（W2），本批只出倍率，间隔/范围保持未知；type74 的 p2 位图与反射比例（type108 p1 候选）未证，保持未知。

**必须保留**：旧答案零丢失零改值；C 批 176 答案与批 18 的 171 答案；HOLD18 及 C 固定池遗留 113 项原处置（18 后段 HOLD／9 type27／13 阻塞／73 暂缓）；30236 基线零触碰；范围外行与账本对象零变化。

## 2. 范围与口径

- 对象＝**当前 snapshot 重筛的 YG1 主分类项**，不直接搬研究期数字。研究期口径 993 项（610 effect＋383 split，407 唯一行／239 唯一 (cid，句）／308 技能；100% 在 109 张 Y.G. 卡）；须与 C 批固定 289 池（216 准入／176 答案）及批 18 逐集合对账，每个差异给出处。636 旧口径不重放（研究期已如实注明不可逐项映射）。
- A 档＝既有键直接消费（bossskill|1/2/3/22/105/110/112、bossskill|13、bossskill|27、skilllist|3000|param1/2/6/8、2012/2003 链）；B 档＝上述 7 空壳键规则化；研究期估计 A 479＋B 70，以重筛实测为准。
- **不在本批**：C 档（type52/108/117 handler 定位与 W1–W6 提取，真实约 30–40 项）——另需用户授权；触发链内部（共鳴成立条件、超共鳴升级、sympathy 系数）无证据——一律披露为适用条件限制，不阻塞倍率、不补乘项；マナ族、回复适配、type27 等其他专项不扩。
- 同规则自然延伸的 nonYG 行允许连带晋级（参照批 8/13 先例），Y.G. 与 nonYG 分列计数；同句式 nonYG 待办 4,819 项不批量处理。

## 3. 写入范围

- 实施：`scripts/character_skills/card_page_inference_kyoumei_ab.py`（新模块，命名可微调）、`output/character_skills/kyoumei_ab_20261025/`、自身 work 目录；rules.json 仅 B 档注册（diff 证明旧 289 键逐字节不变）；新增数据输入须提出并由主持整合进 `card_page_dependencies.py` 签名。
- 主持：本任务卡、进度页、方案/HANDOFF 同步、容量清单、共享生成器与依赖签名整合。
- 独审：`output/character_skills/review/<review_id>/` 与自身 work 目录，只读正式产物。
- 不改：原件、旧审查报告、其他任务目录、UI 样稿、Git。

## 4. 送审版本锚点

- snapshot `ff178894-2f1da88647215e87`；campaign `ff178894179b25ba7b84fadf4e3b499b6642368e13e63e0860035e13ddc5cbfb`；rules.json 289 键 SHA-256 `2f1da88647215e87…befd5`；分类器 `ab6fcb03…`。实施时 backlog/视图锚点重算并记录实际值。

## 5. 模型与派发（2026-10-25 用户确认）

- 主持：本会话 kimi-k3-260716（用户试用 K3.1 Pro 后明确切回 K3）。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high，CreateWorkflow 显式 `subagent_model` `$high`。
- 独审：`new-provider/deepseek-v4-pro-ga-260813` high，独立新上下文。
- 内置角色代理定义携带历史模型，不作派发依据；上游 high 不可独立回显限制保留。

## 6. 流程与验收

1. 实施与自检：先重筛候选并出对账表；每类实质修复/新逻辑保留原错误、相邻变体、正确保留三用例；预期独立给出。
2. 机器生成与固定检查：四 cohort 并行驱动 `--jobs 4` 重建→账本→入口→选题链→`card_page_verify_full.py` 17/17（33 输入版）、账本 9/9、A7 29/29（按 §7 先保存旧结果）。
3. 独立审查：初审一次；集中修复后同一上下文定向复核一次；仍有阻断说明原因与必要额外范围，不因轮次用尽写 PASS。
4. §1.3：本批新增答案的玩家中文说明随批交付，纳入独审抽样（对象/数值/条件/时长/未知可复述）。
5. 差异对账：新增/丢失/范围外变化逐项；候选池三向对账（研究期 vs C 批 vs 当前重筛）。
6. 同步收官：进度页登记终态（数字以正式产物实测为准）。

## 7. 容量门（硬前置）

现预约 RETAINED 12/12。**正式重建（写 pages）前**，主持另列精确容量清单报用户批准；获批前只进行筛选、规则草案、scratch 验证等不写正式页的阶段。不通过放宽限制生成，不扩大处置授权。

## 8. 方向复核

本批为实质解析批，收口后周期满 3/3，按 §6.1 安排独立新上下文第三方方向复核（建议 `new-provider/glm-5-3-flash-260828` high，独立于实施与例行独审；届时由用户确认）。

## 9. 停止边界

不做 C 档原生提取（W1–W6 待单独授权）；不触碰 HOLD18、③新缓存、Git、UI、发布；遇到触发链独立系数、type74 反射比例等新证据问题停车报主持 D1 裁决，不硬猜。

## 10. 主持附记：阶段一对账后的证据修正（2026-10-25，主持核收）

依据 `output/character_skills/kyoumei_ab_20261025/reconciliation.md` 与主持对生产 rules.json 的独立抽核（SHA `de6030e7dceb858d`、289 键、仅 5 键值变化、差异门 PASS）：

1. **收益口径修正**：研究期 A479/B70 估计在当前 backlog 上不可复现（多数已被批 1–3、C、批 18 交付）。当前残余 401 效果项＝A0／B8／C117／HINT163／P113（C 批遗留维持原处置）。本批实际可交付＝**8 条公式级答案**（30310 反应回复×3＝64 p1；30252/30255/30306 冲刺重复攻击×5＝114 p1）＋5 键真实语义注册＋误桶纠正（36 项受击触发词不再当伤害主张）。按「有证单项先交付」继续，不为凑数放宽门控。
2. **103 p3 指令-证据冲突裁决**：接受证据——`bossskill|103|/skillparam3` 真实语义为落点偏移（fall offset），非伤害倍率；本批按真实语义注册，30205「大ダメージ」留 C 档。原任务书把 103 p3 列入倍率 B 档系研究期误判，予以纠正。
3. **55/74 两键已在批 1/批 2 升级**，本批不重复；实际空壳仅 51 p0、114 p1、64 p1、76 p1、103 p3 五键，生产已按此变更（55/74 字节不变）。
4. **168 项「必殺技の威力…」**属 Chain/超共鳴强化触发层而非本体伤害链，后续改派 Chain/超共鳴专项的候选（登记，不在本批处理）；YG1 分母偏噪问题留待选题链后续评估。
5. C 批遗留 113 项中 13 项按本批口径会判 A，仍维持 C 批原处置；如要收取须单独裁决 type27 别名与 t13 条件门。
6. 阶段一后续流程不变：容量处置（既定模式）→正式重建→固定检查→独审→方向复核。

## 11. 阶段一验收与升级处置（主持，2026-10-25）

- 主持独立抽核：生产 rules.json SHA-16 `de6030e7dceb858d`、289 键、恰 5 键值变化、其余 284 键指纹不变；差异门 PASS。5 键语义与原生证据一致（103 p3＝落点偏移、114 p1＝冲刺重复攻击倍率、51 p0＝范围伤害倍率、64 p1＝反应回复系数、76 p1＝浮游炮系数）。
- 实施四项升级的处置：①**生成链接入**——阶段二先把 5 键升级接入 rules.py::rules() 并重生成核对 SHA 不变，再正式重建；②**103 p3** 按 §10.2 接受证据，不另开窗口（如未来要出 type103 伤害槽须单独授权）；③**容量**按 `capacity_proposal.json` 精确清单在阶段二执行，属自动推进规划 §4 既定模式（释放最旧 8 run、保留最新 4 run 回滚基线；identical 逐件执行时复核哈希且须有存活同哈希副本，different 无损搬移，metadata 全留）；④**168 项改派 G4/Chain 专项**登记为后续选题建议，本批不动选题链分类逻辑。
- マナ审计（并行）已完成，其 3 项升级初裁见 `docs/tasks/20261025-mana-readonly-audit.md`；不影响本批范围。

## 12. 阶段二结果与主持确认（2026-10-25）

- **实际收益**：新增 8 条公式级答案（30252 p0/p2、30255 p0、30306 p0/p1＝114 p1；30310 p0/p1/skilltext＝64 p1），恰 8 条 unresolved→has_answer，其余 67,934 效果零变化；3 行 C→A（A 17743／C 23922）；backlog 78,321→78,313；Y.G. 有答案 3,642→3,650；YG1 视图 784→776（恰减 8）。
- **主持确认①（规则元数据传播）**：5 键升级的文本（conversion/limits/conditions/meaning/status/evidence）传播到 6 条既有行答案与 254 卡 744 条 record_evidence，数值与证据档不变——这是空壳文本升级为已确认公式的必然结果，接受，不回退；final_diff 的 PASS_WITH_RULE_METADATA_PROPAGATION 即指此。
- **主持确认②（容量偏差与事故记录）**：different 清单 3,117 件中 880 件属保留的最新 4 run，实施按「保留回滚基线」优先只搬移被释放 8 run 的 2,237 件，880 件原位保留——处置正确（原指令②与④有冲突，按④是对的），偏差已留档。apply 首次在物理完成后记账阶段中断，已修复并以后验全 PASS 收口；disk_free_before=null 如实保留。
- **登记为非阻塞后续（不挡本批收口）**：①profiles.build_character 对 cid 3 无 None 保护崩溃、register_rule 不携带 occurrences_apk（17 键）——既有生成器缺陷，影响从零重生成完整性，另立修补；②隔离复跑发现页面生成实读 1,686 证据文件＋42 立绘不在 33 项声明依赖内——既有签名缺口，复跑已逐项列出（undeclared_inputs_copied），主持后续整合 card_page_dependencies；③card_page_index.py 的 EXPECTED_CAMPAIGN 仍为 b18 常量，本次沿用显式配置模式（原源码未改、校验未降），统一配置化另列维护。
- **本批边界**：未做 C 档原生、HOLD18、③、Git、UI、发布；独审与方向复核随后按规划执行。

## 13. 正式收口（2026-10-25，独审 PASS）

- 独立初审 **PASS、零阻断、无需修复轮**（审查退出条件满足，不重复送审）：`output/character_skills/review/kyoumei_ab_20261025_deepseek/REPORT.md`。8/8 答案链从解码原值独立重建精确匹配；103 p3 落点偏移经三层证据确认；rules 289→289 恰 5 键变、其余不变；removed_answers=0／semantic_changes=0；HOLD18／C113／36 误桶全保持 unresolved；401=577−176 桥接成立；§1.3 中文 8/8；容量回执只读核验通过；审查方独立复跑 check_rules_diff 与 verify_full 17/17 PASS。
- 审查残留（Low/Info）均为已登记非阻塞项；其中容量 proof_sample 2/5 survivor 当前哈希与清单不符系正式重建覆盖正式页所致，处置时点不变式成立、非数据丢失，如实保留。
- 终态数字（metrics 实测）：完整 4,425（+0）／部分 84／未解析 9,067／拆分 28,089；A 17,743／C 23,922；整行推断 3,800／确认 266；有答案 17,419（Y.G. 3,650）／未解 50,224／NA 299；backlog 78,313（P1=Y.G. 10,178、P2 68,135、P0=0）；YG1 视图 776。预约 RETAINED 8/12。
- 方向复核（本周期 C＋批18＋本批，3/3）**已完成**：`third_party_direction/REVIEW_DIRECTION.md`（dwfrun-460ad92d，GLM high）**PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞 0**——主线推进属实无凑数放宽、可复用能力形成、13 项原始记录抽查全过、证据与未知边界准确、549→8 发现过程诚实合理。新增 2 项非阻塞过程建议：研究期/中间池持久化逐项清单；YG1 主分类偏噪收紧与 168 项改派 Chain/超共鳴专项落实为选题链改动（登记后续，不在本批）。方向复核未自行重跑 verify_full/A7（只读，以读回执＋独立抽核替代；例行独审已复跑 17/17）。新周期 0/3，マナ批接续。

## 附录：独审与方向复核准备（主持预写，2026-10-25）

**A. 独审任务框架（正式产物验收时派发，独审 new-provider/deepseek-v4-pro-ga-260813 high，独立新上下文）**
- 全量机械对账：候选三向对账、rules 差异门独立重跑、旧答案零丢失零改值、范围外零变化、30236 零触碰、HOLD18 原样。
- 分层语义抽样：A 档按类型取代表行（bosspattern flag/skillid0→bossskill 原值、公式 floor/clamp(float32(B×pN))、B 已含 Chain 披露）；B 档 7 键逐键独立复验 pin 与证据档；charainfo 镜像、nonYG 连带、split 随行各取样。
- 反例方向：同句多主张被错并；跨层/跨命名空间取值；charainfo 内联值误当独立来源；倍率被写成最终扣血；type55 间隔/范围被填数；type74 反射比例被填数；Chain 被重复乘入；触发链系数被补猜。
- §1.3 样本：仅看默认中文能否复述对象/量与基准/条件/时长/未知，再对照 JSON 与来源核不漂移；缺已知要素或把未知读成确定＝不通过。

**B. 第三方方向复核框架（本批收口后周期满 3/3，§6.1）**
- 范围：本周期 C＋批 18＋共鳴A/B 三批；独立新上下文，从原始来源分层抽查新增机制族、代表 Y.G. 卡、必要 nonYG 对照与正反例。
- 核查：是否推进主线、字典/工具是否形成可复用能力、数字收益是否真实、证据与未知边界是否准确；不重复全量历史审查，不重开已关闭 R3。
- 模型届时由用户确认（建议 new-provider/glm-5-3-flash-260828 high，独立于实施与例行独审）。

**C. 并行在途**：マナ族只读审计（`docs/tasks/20261025-mana-readonly-audit.md`，dwfrun-6162eb76-ab15-4004-9e3b-27d7113591fa）与本批无写入重叠，其产物不进入本批证据链。
