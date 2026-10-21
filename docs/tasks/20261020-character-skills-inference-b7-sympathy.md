# 任务卡：角色技能页 · 批 7 共鳴アビリティ家族（sympathy 3000/3005/3006）

- 任务 ID：20261020-character-skills-inference-b7-sympathy
- 状态：**已闭合（2026-10-21 复核更新）**：前置审计（纯分析）→ 实施晋级 106 行（Y.G. 25）＋hint 687 → DeepSeek 审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS。过程记录见下文各节；本卡上部按阶段区分前置分析/实施/复验终态。
- 负责人／对话标识：批7共鳴审计员（GLM 5.3 Flash 260828，workflow 子代理）
- 上游依据：`yg_coverage.md` §4 簇②（Y.G. 124 行：3000×47/3005×75/3006×2，hint 121）、
  §5 批 7 行；批 1 Top20 家族 #7/#14；批 6 任务卡与 scope（门控/非首段裁决/競争句/
  B5-R01 方案 A）

## 目标

把共鳴アビリティ家族的 buff 句行从 hint 晋级为「推断」值行——唯一消费路径是
`skilllist|3000` 4 条已确认规则（param1/2/6/8）；3005/3006 自身参数无规则、不可补证，
一律留 hint。

## 前置审计结论（详见 scope）

- 范围文档：`output/character_skills/inference_inventory/b7_sympathy_scope.md`
- rules.json（277 键实测）：`skilllist|3000` 4 条（p1/p2 攻击加算贡献、p6 时长、p8 暴伤
  系数；occurrences 303/303/348/144，与 CACHE 382 条记录非零计数交叉验证一致）；
  **3005/3006 为 0 规则**——派发证据 `ability3000/dispatch.txt:10` 在 0xbb8(3000) 即返回，
  既有原生证据不覆盖 3005/3006 处理器 → occurrence 补证不可行，留 hint
- 关键结构（本轮新核实）：主记录 text 承载全部正文，buff 数值在「sub1」记录
  （skillid=M+1，ability=3000）与/或主记录自身；30236 确认先例（43023610→43023611）；
  载体競争 0 例、同属性重复段 0 例
- 行集：sympathy 组 2,232 行/719 cid（A 257/C 1,975）；主 ability 3000×1,511/3005×639/
  3006×51/旧型 31；主层 APK 1,082 行；buff 语义行 794（Y.G. 108）
- **晋级候选：全库 96 行（~324 值行）/ Y.G. 25 行（~100 值行）**——远低于 yg_coverage §5
  预期（Y.G. ~90–120/全库 ~600–900），收缩原因四项（scope §4）：3005 自身无规则、
  buff 段 2/3 含无规则属性（防御力等）、APK 载体域外 156 行、A 行不动
- 留 hint：非 buff 句 1,182／无规则属性 ~500／APK 载体 156／无载体 48（35 行有未定槽
  p7 相关性待原生核实）／旧型主记录 16
- ④ charainfo 句序（批 6 复验 Low 49/367 行）：批 7 无 charainfo 行（家族行全在
  sympathy 组/skilllist）；批 7 新行采用自识正文口径（「sympathy 主记录正文句序…；
  sub1 载体与同页其他记录句序另计」）；批 6 遗留 49 行建议纯渲染层限定（方案 A，
  同 B5-R01 先例），由下次触碰 renderer 的批次实施，批 7 不改 b6 逻辑

## 允许写入（实施批）

- 脚本：`scripts/character_skills/card_page_inference_b7_sympathy.py`（新）；
  `card_page_data.py`/`card_page_policy.py`/`card_page_render_v2.py` 最小接线（行键
  `inference_b7`＋label；按 b6 同位 gate 链接入）
- work：`work/character_skills_b7_sympathy/`
- 输出：pages 产物（batch 入口重建受影响页）＋`inference_inventory/` 本批文档；
  不碰 profiles/rules/links 共享层、不重跑 profiles.py、不动批 1–6 行与键、不 git 暂存提交

## 共享依赖（只读）

- `output/character_skills/profiles/{records.jsonl,rules.json,characters.csv}`
- 证据：`output/ordinary_effects/ability3000/`（README/trace/native_checks）、
  `output/card_comparison_cid30236/{timed_support,critical}/`、
  `output/card_comparison_cid30236/field_dictionary.json`
- 解码侧：`output/cache_full_20261015_v3/decoded/{skilllist,sympathy_skilllist}.data5.json.raw`、
  `output/base_master/_mdSkill.json`（APK skilllist；仅用于载体层判定，不消费其参数）

## 最近更新

- 2026-10-20：前置审计完成（scan_b7_rows.py＋两份行级 JSON＋参数快照＋scope 文档）。
  关键实测：rules.json 277 键、3000 occurrences 交叉验证一致；3005/3006 原生证据 0 命中；
  主/sub1 载体架构与 30236 确认先例；G1 唯一子串 96/96；競争 0 例；晋级候选 96/25。

## 下一步（实施批入口）

1. 主持确认 scope §4 与 §5 的收缩后范围（96/25），特别是：①非首段口径沿用批 6 裁决；
   ②APK 载体域外留 hint（不扩域）；③p3/p4/p5/p7 与 3005/3006 参数不消费；
   ④批 6 遗留句序措辞走渲染层、归属下次 renderer 批次；
2. 按 scope §5 门控 G1–G8 实施模块，先代表样本（30236 基线不动、10215（Y.G. 3005 主）、
   40033910/40033911 拆分架构、40024510 主不活性、203 APK 载体 hint、40034110 双 buff 段）
   回归，再全量；
3. 逐行清单复用 `work/character_skills_b7_sympathy/b7_rows_classified.json`，
   实施时以现场数据重建再校验（b5/b6 同法）。

## 实施节（2026-10-20，批 7 实施员 GLM 5.3 Flash 260828）

- 状态：**实施完成**；四 cohort 全量重建 0 失败，2236/2236 receipt SUCCESS，终签名
  `e2aa02bb153074d5dded779ba170e1b892aefe8fa30e1701a173188cedad30f8`
- 模块：`scripts/character_skills/card_page_inference_b7_sympathy.py`（新）；接线
  `card_page_data.py`（批 6 gate 链后，gate＝sympathy 组＋skilllist＋not answers＋批 3/4 未晋级）、
  `card_page_policy.py`（b7 scope 登记＋message 六批）、`card_page_batch.py`（b7 计数透传＋
  plan 描述）、`card_page_render_v2.py`/`card_page_dbstyle_sample.py`（b7 标签＋**批 6 遗留
  49 行句序口径澄清**：charainfo b6 行渲染「charainfo.skilltext 句序；同页 pattern 正文句序
  另计」——纯渲染层方案 A，card.json 零变化，367 行/354 页全覆盖）
- 结果：晋级 **106**（Y.G. 25；值行 357＝p1 87/p2 87/p8 77/p6 106；Y.G. 100＝各 25）、
  hint 登记 **687**（Y.G. 82：unruled 477／APK 载体 146／无载体 48／旧型 16；競争 0）；
  变化行恰 793＝106＋687，0 增删、0 个批外变化行（对账
  `work/character_skills_b7_impl/compare_full_rows.py`）
- 指标 old→new（分母 N_all）：全库（41,665）A 16,099→16,205（+106）、C 25,566→25,460、
  原文A 13,859 不变、整行推断 1,974→2,080、整行确认 266 不变；Y.G. 109 卡（5,805）A
  2,814→2,839（+25）、C 2,991→2,966、原文A 2,543 不变、整行推断 253→278、整行确认 18 不变
- **与预分类差异 10 行（8399/8400×2/8401/8402/8403/20131/20301/20607/20609）**：审计
  scan_b7_rows.py 注释「CACHE 优先」但 `sl = sl + apk_sl` 实际 APK 覆盖 CACHE（双层并存
  568 id），10 行被误标 APK 载体；实施按 CACHE 优先（=links common.py Table.get 口径、
  =行登记层、=规则 382 条样本域）解析出 CACHE 载体晋级，槽值均在 {0.05,0.1,45} 已核值域
  （8400 为拆分架构双行 f0→main/f2→sub1）。审计 work 中间件不改写，以 pages/README.md
  §19.3 为准
- 回归：`work/character_skills_b7_impl/sample_regression.py`（11 cid 40 行）0 失败；30236
  基线 A 行（43023610→43023611 确认链）b7 零接触；复核
  `work/character_skills_b7_impl/check_receipts.py`：2236 receipt SUCCESS/4,472 哈希 0 不一致/
  29 依赖未变（dependency_signature `4029ad13…`）/0 stale/4 cohort MATCHING
- run_id：ge60 `20261020T144044225775Z-1995fc5c`、40to59 `20261020T144108683781Z-8244870e`、
  20to39 `20261020T144215578609Z-3a60e788`、remaining `20261020T144318282523Z-bc726985`
