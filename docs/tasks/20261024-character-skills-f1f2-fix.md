# F1/F2 有界修复：共享关系肯定依据＋头标记不豁免动作正文

- 任务 ID：20261024-character-skills-f1f2-fix
- 负责：主持 Kimi K3（唯一写入整合者；本轮按总指挥任务书**由主持直接实施**，不启动其他代理或审查对话）；验收：总指挥安排（原 Codex 审查者独立验收尚未执行）
- 授权来源：用户 2026-10-24 转交总指挥任务书（原 Codex 最终复审 `output/character_skills/review/r3_sentence_codex_final_20261024/` REQUEST_CHANGES：F1/F2 阻塞 R3 归属/选题层全局闭合；总指挥 `codex_final_acceptance_r1/` 独立复现接受）
- 状态：**F1/F2 修复及自验完成，待总指挥安排独立验收**（不冒称已获原审查者最终通过）

## 基线与保留（先核后改）

- 当前 assign_candidates.py SHA-256＝`bfdbe1885a0112865a6aafc12331048e190fef13230f38844f84c3601992646a`（与审查验讫版本一致，已实测）。
- pages campaign `c019af0b`；正式账本快照 `c019af0b-57a14d29`；rules `57a14d29`；候选产物当前锚点 a2dc963c（旧生成快照，内容口径不变）。
- **保留已通过修复**（回归保护，不得倒退）：原 7 个 sentence 反例处置、349 子句优先（e00/e01/e02→G7 clause、e04→G5 clause）、跨顿号命中起点定位（11024/11039/11233）、clause 路径约定与旧候选/also/skill_tags 保留、MANA 正常动作识别（空类型集合与无限制的区别）、合法共享正例（「自身がサブパーティにいると、攻撃力が上がる」→G8 sentence）、自身状态异常持续时间与真实共享条件配对正例。
- **证据强度更正（写入交接）**：此前"79,121 项真实函数与独立规格逐项零差异"表述过强（nonYG 为聚合对照＋共享判据共用假设）——旧报告保留，当前交接注明该限制，不再用它证明语义全局闭合。

## F1/F2 根因与修法（最小实现）

- **F1**：`_unowned_sibling_check` 在"无类型/机制冲突"时让 `_sentence_hit_info` 返回 shared→可主分类。修：无冲突不再等于共享——动作/陈述子句须**肯定依据**（纯条件形态（触发/条件收尾且无机制词）或机制词族与本效果类型兼容且条件形态）才可 shared；否则新增 klass=**undetermined**（不作主分类、候选保留 also＋待定位理由）。
- **F2**：`_shared_shape` 只因子句含【/≪即豁免。修：先剥离标记片段再判——纯标记/包装（剥离后为空）仍豁免；含动作/机制内容的子句不豁免（标记存在不使整段独立动作免检）。
- 禁止项遵守：不对三个 CID 硬编码；不只从 G5 兼容表删时长/回复类型掩盖；不把所有 shared 一律降 G9；不删上下文/附加候选/待办。

## 允许写入

`work/character_skills_yg_priority/assign_candidates.py`（F1/F2 最小实现）＋ `work/character_skills_f1f2_fix/`（本轮保全/验证/差异报告）＋ `work/character_skills_yg_priority/yg_candidates*.json`（验证通过后提升）＋ 本卡 ＋ `docs/tasks/character-skills-progress.md`（当前入口，本轮一次同步）。不改：效果数值、HP 分支、R2 完整性规则、证据等级、正式账本语义、原始数据、旧审查报告、既有事故保全副本。

## 最近更新

- 2026-10-24：任务卡建立；材料已读（REPORT/findings/remaining_real_counterexamples/boundary_probes/targeted_checks/preservation＋codex_final_acceptance_r1/REPORT+checks）；当前分类器哈希与审查验讫一致已实测；F1/F2 修法已定。
- 2026-10-24（实施与自验完成）：①实现——F2：_shared_shape 先剥离【…】/≪…≫标记片段再判（纯标记/包装仍豁免；含动作/机制内容不豁免）；F1：_unowned_sibling_check 返回契约改三态（shared/sibling_unreg/undetermined），无冲突≠共享——新增 _positive_shared_evidence（纯条件形态无机制词，或族兼容＋条件形态才算肯定依据），undetermined 不作主分类、候选保留 also＋待定位理由；_sentence_hit_info 与下游 also_basis/demote_why 增 undetermined 分支。②验证——probe 套件（work/character_skills_f1f2_fix/f1f2_probes.py）18/18 PASS：三反例（30109/30249/30330）全部归 G9＋原抢占候选保留 also＋待定位理由；配对探针（cleanse_vs_hp plain/header、mana_action plain/header）全 G9；合法共享 G8 正例保持；349 f2（G7/G7/G7/G5 clause）、30225（G7 clause）、KWCL 四具名项（11024→G2/sentence、11039 e00→G9、e01→G2、11233→G9）全部保持。③全量差异（scratch vs 提升前正式产物，scratch_diff.json）：主分类变化 209 项全部来自旧 sentence 主分类路径（越界 0）、klass 变化 209（201 shared→无＋8 shared→own）、also 集合变化 130（均为被降候选入 also）、候选丢失 0、新增项 0、skill_tags 变化 0；before→after 主要过渡：YG4→G9 30、YG4→YG1 30、YG5→G9 17、YG3→YG1 12、G7→G9 12、G7→YG1 9、YG2→G2 8、YG6→G9 5、G5→G9 5、YG2→YG2 63（同族 basis 变化）。④提升：assign_candidates.py 正常路径重跑（输入未变、仅本分类器变化），正式 yg_candidates.json＋yg_candidates_items.json 与 scratch 逐项内容一致（meta 时间戳除外）；meta.generator_scripts 与当前三脚本哈希实测一致（assign_candidates 新 SHA 22bc1478…）；backlog 锚点 c019af0b-57a14d29。提升后 verify_r3fix 9/9 PASS（V3c 与正式逐项 0 差异、V5 nonYG 差异 0、V7 作用域保持）。⑤页面与正式账本无依赖变化，未重跑；未碰 pages/effect_ledger/rules；未 Git。⑥证据强度注记：此前「79,121 项逐项零差异」表述过强（nonYG 为聚合对照）——已写入交接，不再用作语义全局闭合依据；F1/F2 修复后该说法的任何用法均待原审查者独立验收。
