# 任务卡：批 9 敵デバフ（G2）——前置审计（纯分析）

- 任务 ID：20261021-character-skills-inference-b9-debuff
- 负责人：批9debuff审计员（GLM 5.3 Flash 260828，workflow 子代理，单 ask）
- 状态：**已完成（前置审计）**；实施批未开始
- 日期：2026-10-21

## 目标

清单 `yg_priority_list.md` G2「敵デバフ（攻撃した敵…下がる）」批的前置审计：规则库存（减益/负向语义）、候选行集（C∪hint）、代表样本逐行核对、晋级范围设计。**纯分析**：不晋级、不改生成器、不改 pages 产物。

## 允许写入范围（本轮实际写入）

- `work/character_skills_b9_debuff/`（脚本＋中间数据，全部可复跑）
- `output/character_skills/inference_inventory/b9_debuff_scope.md`
- 本任务卡

## 关键结论（详见 scope §1–§5）

1. **敌方减益的已确认规则只有 `skilllist|99`（PowerDrain）一族 4 条**（p0 时长/p7 攻/p8 移/p9 防=受伤量口径；occ 133/126/1/123；样本域=当前 v3 CACHE 普通 ability99 的 133 条；APK 99×199 域外）。bossskill 140 条中**无**敌方减益规则；et13 换算器硬编码「+」方向（rules.py:1349-1365）。
2. 广筛（敵+攻/防/移+下がる/下げる）：**973 行/451 cid，Y.G. 208/77**；核心家族 #6=453/135 与 Top20 逐字一致；G2 对账 208−10=198 ✓、cid 77 ✓。
3. 分类：C1 载体 2003（SA_PowerDrain，**无规则**）431 行→hint；C-skilllist-row 310 中 **PASS 35 行（Y.G. 11，估值 ≈138 值行）**经 ability99 规则域内＋形状/方向门；C2 方向冲突 77 行（B1 30338 防线）；其余 charainfo 歧义 95/无 pattern 19/无载体 15/heroic 12/链缺口 8/真多载体 6。
4. **新发现（须实施批强制）**：profiles 装配层存在 sub_effect **ID 碰撞伪影**（profiles.py:426-428 按 record_id 跨表挂子）——pattern 行 children 里的 sub_effect 99/1095 记录可能是能力记录的子效果，pattern 行不得经该伪影消费。
5. 2003 与 99 形状同构（431 行 6 种属性组合全自洽，p7≤0/p8≤0/p9≥0/p0∈{10..30,-1}）但**域外无规则**——扩域需 ability2003 原生专项（可解锁 431 行）。

## 下一步（实施批建议）

1. 按 scope §5.1 门 P1–P6＋B1 防线实施 PASS 35 行（值行 ≈138，规则键限 `skilllist|99|/param0|/param7|/param8|/param9`）；行级键 `inference_b9`、evidence_scope=`TEMPLATE_BATCH9_DEBUFF`。
2. 防御力值行用受伤量口径披露（§5.2-4）；p8 已核样本域仅 1 条（43023616）逐行披露。
3. 其余 938 行留 hint 并按 §3 类登记原因；2003 扩域另立原生专项。

## 共享依赖

- 只读：`output/character_skills/profiles/{records.jsonl,rules.json,characters.csv}`、`output/character_skills/pages/*/card.json`、解码 `skilllist.data5.json.raw`、`output/base_master/_mdSkill.json`、`output/card_comparison_cid30236/`、`output/ordinary_effects/ability99/`。
- 复用先例：批 6（bossskill 子记录/门控）、批 8（s_ability 载体链/样本域/披露）。

## 最近更新

- 2026-10-21：审计完成，产出 scope/任务卡/work 数据；未 git 暂存。

---

## 实施节（20261021 批 9 实施员，workflow 子代理，单 ask）

- 状态：**已完成（实施＋四 cohort 全量重建＋verify_full 10/10 PASS）**
- 允许写入：`scripts/character_skills/card_page_inference_b9_debuff.py`（新）、
  `card_page_data.py`（接入）、`card_page_policy.py`、`card_page_batch.py`、
  `card_page_index.py`（EXPECTED_CAMPAIGN 基线）、`card_page_verify_full.py`（聚合键）、
  `card_page_render_v2.py`（审计标签）、`output/character_skills/pages/`（含 README §22）、
  `work/character_skills_b9_debuff/`（快照/烟雾/对账脚本与数据）、本任务卡。未 git 暂存。

### 实现要点

1. 门控：scope §5.1 P1–P6 全部实现＋B1 防线（99 载体主张只对 skilllist/supporterskill
   容器行自身 sub_effect 链有效；pattern 行只读 boss_skill/boss_skill.s_ability 子记录、
   从不读 sub_effect 伪影；et13 正値候选逐行拒绝；新增 P1 逐字对象门——敌方减益半句＝
   首个下降谓词句段，须同含「敵」与属性名）＋P4b 竞争句检测（批 6 G6 扩展；35 行 0 例）。
   链解析复用 `data.old`（profiles/records.jsonl）＝审计同源同法；99 样本域由解码
   skilllist 实测（ability==99 的 CACHE 133 条）。
2. 值行 138 条（p7 35＋p9 35＋p8 33＋p0 35；rule_key 只允许 skilllist|99|/param0|/param7|
   /param8|/param9，经 rules.py 既有换算器出值）：numeric_source=「模板推断（批 9 敵デバフ：
   <链>）」；note 两层区分（规则本体已确认／本条数值归属推断）；方向按符号逐行审核；
   对象=敌方逐字＋setSupport2 受击目标路径；条件全句逐字；防御力行固定受伤量口径披露；
   p8 行逐行披露已核样本域仅 43023616 单条；60 秒档句外槽 p4/p5/p6（13 行）与复合句
   「自身の…上がる」半句登记不分配；证据按字段（timed_support/＋ordinary_effects/ability99/
   ＋difference_sources/movement；param8→movement/），存在性检查实测全在。
3. 行级：`inference_b9` 元数据、`evidence_label=推断（模板批 9 敵デバフ）`、
   evidence_scope=`TEMPLATE_BATCH9_DEBUFF`、row_class=C→A、行 evidence=推断；
   hint 键 `inference_b9_hint`（938 行逐行登记 scope §3 类原因）。

### 实测结果（对账脚本 work/character_skills_b9_debuff/reconcile_b9.py）

- 晋级 **35 行/35 cid（Y.G. 11）**＝审计 PASS 集完全相等（双向差集空）；值行 138＝审计估值。
- 留 hint **938**＝审计 973−35 完全相等，逐类对账：C1 431（355＋charainfo 76）／C2 77
  （60＋charainfo 17）／C3 6／C4 15（10＋charainfo 5）／charainfo 歧义 95／无 pattern 19／
  no-99-carrier 165／APK 99 域外 94／heroic 12／denju 无 children 8；
  **实施新增 P1/B1 逐字对象门改判 16 行**（审计 P2 桶内：首个下降谓词句段无「敵」，
  如引号内元描述「…属性防御力を下げる」）——hint→hint，档位不变，总数不变。
- campaign（N_all 41,665 不变）：A 16,551→**16,586**（+35）／C 25,114→**25,079**／
  原文A 13,859 不变／整行推断 2,426→**2,461**／整行确认 **266 不变**（18+248）／partial_A +35。
- **Y.G. 专项（对照批 8 后基线 159/60/19/1,907）**：净新增晋级 **11** 行／受益 Y.G. 卡
  **11**／唯一 NFKC 正文新增 **1** 文（11 行同文「さらに攻撃時、攻撃した敵の攻撃力と防御力と
  移動速度が一定時間下がる。」）／yg_priority 剩余 **1,896**（11 行全在 G2 集合内）。
- 分 cohort（晋级/hint）：ge60 1＋78／40to59 19＋396／20to39 15＋294／remaining 0＋170。
- 代表晋级行（数值/单位/对象/条件/来源）：30002-ability-…-f3「さらに攻撃時、攻撃した敵の
  攻撃力と防御力と移動速度が一定時間下がる。」——/param7=-0.3（攻撃倍率加算增量，敌「攻撃
  した敵」，攻撃時触发，载体 skilllist|43000203|CACHE own sub_effect）/param9=+0.3（受伤量
  倍率加算＝防御下降表现层，因子 1.3）/param8=-0.3（移速因子加算 ×0.7；p8 披露外推）/
  param0=30（游戏秒）。非 Y.G. 复合句例：11235-…-f5 载体 41123503，p7/p8=-0.15、p9=+0.15、
  p0=60（自身增益半句登记不分配）。
- old→new 变化清单（重建前后全量行签名对比）：行级变化恰 **973**（35 晋级 C→A＋938
  hint 登记），计划外行级变化 **0**；卡级仅 coverage 新增 b9 两计数键＋policy 文案更新。
- 验证：四 cohort 0 失败（首轮回 remaining 1 例 WinError 5 文件锁瞬时失败 cid 7591，
  整 cohort 强制重建后统一 run_id）；签名 `873a7208…`（source_signature 因批 9 代码更新、
  dependency_signature `4029ad13…` 不变）；run_id ge60 `…c06f6b26`/40to59 `…011b388f`/
  20to39 `…89af2622`/remaining `…62d9a3dc`；index 入口页刷新（EXPECTED_CAMPAIGN 同步
  A 16,586/C 25,079/推断 2,461）；`card_page_verify_full.py` **10/10 PASS**。

### 遗留

- 2003 载体扩域（可解锁 431 行 C1 hint）需 ability2003 原生专项（无规则/无换算器/无证据目录）。
- 其余 hint 类（charainfo 歧义 95、方向冲突 77、域外 94 等）保持 hint，归属未化解不晋级。
- profiles 装配层 sub_effect ID 碰撞伪影（profiles.py:426-428）为既存行为，本批仅在
  推断层设防（B1 防线），未改 profiles（生成器共享层，留整合者）。

---

## 修复节（20261021 批 9 修复员，workflow 子代理，单 ask）

- 状态：**已完成（B9-R01…R05 修复＋四 cohort 全量重建＋verify_full 10/10 PASS）**
- 允许写入：`scripts/character_skills/card_page_inference_b9_debuff.py`（披露层 3 处）、
  `output/character_skills/pages/`（含 README §22.4 更正＋§22.5 新增）、
  `work/character_skills_b9_fix/`（快照与比对脚本）、本任务卡。未 git 暂存。
- 审查对象：`output/character_skills/review/inference_b9_debuff_20261021_deepseek/`
  （1 Medium＋4 Low）。

### 修复内容

1. **B9-R01（Medium）**：`_promote` p9 值行 note 括注百分比 `int(round(raw*100))`（银行家
   舍入，0.175→18%）改 `f'{raw*100:g}'`（17.5%）。2 行（20836/30255 p9 值行）note 与主值
   「增伤 17.5%」一致；全库「固定防御减少 18%」残留 0；value/raw/单位零变化。
2. **B9-R02（Low）**：P1/B1 门分支对句段含「属性防御力」的 15 行改如实理由：「＝敌方属性
   防御减益；属性防御力超出本批攻/防/移属性范围（属性门），归属未化解——不晋级（30338
   防线镜像门）」（实测 15/15 对象承接前句「攻撃した敵に」；全库 P1/B1 共 16 行，另 1 行
   8148 自身防御保留原「我方半句」文案）。判定仍 hint、0 值行。
3. **B9-R03（Low）**：C2（direction-conflict-t13）分支检测 parent children 中 link_kind=
   sub_effect 且 ability=99（CACHE/APK 均）的记录并补披露：「披露：parent sub_effect 存在
   ability99 伪影（skilllist|<id>|<层>），按 B1 防线不消费、profiles 装配层 ID 碰撞伪影见
   任务卡遗留」。**实测披露 9 行**＝审查 6 行 pattern 行＋同 pattern0 父记录的 3 行
   charainfo/skilltext 行（20125/20325/30254 各 1，经同页同文匹配同一父记录、旧文案同为
   「无 2003/99 载体」，同一缺陷一并披露）；cid 集合与审查一致。判定仍 hint、0 answers。
4. **B9-R04（Low·文档）**：README §22.4「卡级差异仅两类、数值与既有键零变化」更正为：
   35 张晋级卡 coverage A/C/A_rate/C_rate/evidence_cross/partial_A 与 summary A/整行推断/C
   按 +1/−1 变化（审查 zero_change.json 逐一重算）；仅 2,201 卡只有 b9 两键变化；行级
   other=0 与 30236 行级零差异仍成立。
5. **B9-R05（Low·指标）**：README §22.4 Y.G. 口径两口径并列——绝对累计 278+159+11=448 行/
   有推断行卡 108/唯一 NFKC 文本 24→25；阶段净新增（2026-10-21 清零起算）170 行/去重受益 62 卡/20 文（批级卡次 60+11=71、重叠 9 卡、B9-RC01 更正）
   （审查 metrics.json：yg_old 437/108/24 → yg_new 448/108/25）；不混用。

### 实测结果（快照多重集比对 work/character_skills_b9_fix/snapshot_full.py）

- 行级变化恰 **26**＝2 note（R01）＋15 hint 理由（R02）＋9 hint 披露（R03）；计划外行级
  变化 0；行集合增删 0。
- **零变化核（多重集比对）**：行类/evidence/label 多重集（41,665 行）修复前后相等；答案
  多重集（除 note，25,578 条）相等；coverage/summary 卡级零变化；30236 行级零差异；raw 值/
  行类/证据等级/晋级与 hint 判定零变化。
- 指标与修复前一致：campaign A 16,586/C 25,079/推断 2,461/确认 266/N 41,665；b9 晋级
  35/hint 938；Y.G. 11 行/11 卡/1 文/hint 197；yg_priority 剩余 1,896。
- 四 cohort 0 失败（ge60 34/34、40to59 290/290、20to39 436/436、remaining 1,476/1,476）；
  40to59 因烟雾子集（6 卡）先行生成留下混合 run_id，整 cohort 强制重建统一 run_id（批 9
  实施批 cid 7591 同先例）；index 入口页刷新（CURRENT）；`card_page_verify_full.py`
  **10/10 PASS**（receipt 2,236、哈希 4,472、依赖 29、行集合 41,665、值相等 8,162）。
- 签名 `b670cd42790861d405eafdfa94554208f3d040ed2adb4340c33c9e67a35cdaec`（source_signature
  `a84947b6…` 因披露层代码变化更新、dependency_signature `4029ad13…` 不变）；run_id ge60
  `20261021T143631712701Z-b6924788`、40to59 `20261021T144023488884Z-91417d7e`（campaign 同
  run）、20to39 `20261021T143649814948Z-26762c9c`、remaining `20261021T143812907209Z-8ade1c9d`。

### 遗留（与实施节相同，新增无）

- B9-I01/I02/I03（Info）未在本轮范围（复合句文案扩展、clean_span 注释、P1 门变体健壮性）。
- profiles 装配层 sub_effect ID 碰撞伪影为既存行为，仍留整合者；本批仅在推断层设防＋逐行披露。
- 2003 扩域、其余 hint 类保持 hint。
