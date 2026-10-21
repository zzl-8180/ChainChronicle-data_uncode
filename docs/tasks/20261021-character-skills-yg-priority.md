# 20261021 角色技能·Y.G. 优先高价值缺口研究清单（H3 整改，纯分析）

- 状态：完成（2026-10-21；2026-10-21 复审修订：候选数与分类计数、命名及 cid349 归属按复审 REPORT §5 纠正，见清单 §0 修订注记）。
- 负责人／对话：YG清单研究员（GLM 5.3 Flash 260828，workflow 子代理，单 ask）。
- 目标：按独立第三方审查 `review/independent_20261020_codex_audit/REPORT.md` §三（H3）整改方向，把「Y.G. 优先」从口号落到选题结果：以审查 `coverage_refined.json` 的 Y.G. 剩余 2,066 行（分母 2,344＝已推断 278＋剩余 2,066）为分母，产出带证据状态与工作量分级的候选任务清单。
- 清单（权威结论入口）：`output/character_skills/inference_inventory/yg_priority_list.md`。
- 数据与脚本：`work/character_skills_yg_priority/`（build_inventory.py / enrich_records.py / assign_candidates.py ＋ 6 个数据 JSON）。

## 允许写入范围

- 本任务卡、`work/character_skills_yg_priority/`、`output/character_skills/inference_inventory/yg_priority_list.md`。
- 不改：生成器（scripts/character_skills/*）、pages/ 产物、profiles/ 与原始输入、旧审查报告、其他任务卡。未 git 暂存/提交。

## 核心结论（详见清单）

1. 分母核验通过：109 Y.G. 卡（characters.csv 实测 109）；2,066 剩余行逐个回查当前 pages 均 in-place 为 C；Y.G. 页行 5,805＝A 2,839＋C 2,966 与审查表一致；278 已点亮＝试点/批 5（170）＋批 6（83）＋批 7（25）。
2. 五类缺口（重叠口径）：攻撃 1,331／时间 1,004／减伤·防御 819／暴击 629／回复 269 行。
3. 2,066 行不相交归属 **16 个候选**（YG1–YG6 Y.G. 优先主题 384 行＋G0–G9 通用 1,682 行），closure 2,066/2,066（2026-10-21 复审修订：候选数、分类计数与命名纠正；cid349 归属见清单 §2 注记）。
4. 关键跨切发现：b6 残留 221 行中 116 行卡在暴击属性；规则本体已确认（`skilllist|2012|/param4` occ 308、`/param5` occ 311），但归属须走真实链（cid 349：bosspattern40034900→bossskill40034901（type13）→s_ability40034914→skilllist40034914（ability2012）；skilllist40034901（ability1095）为普通自身增益、属另一候选，**不得**混为本句来源）。规则有证据 ≠ 全部候选的对象/条件/动作阶段/句级归属已证明——是否需补证按具体缺口判断，**不笼统承诺全部无需新证据**。
5. 建议下一批：①暴击属性增益解锁批（多子记录归属扩展，中）；②敵デバフ批（G2，198 行/16 文，低–中）。伤害几何类（共鳴必殺本体、必殺骨格）留原生专项排期。

## 最近更新

- 2026-10-21：清单、数据与任务卡落盘；未 git 暂存/提交。
