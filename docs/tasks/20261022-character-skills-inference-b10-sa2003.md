# 任务卡：批 10 ability2003（SA_PowerDrain）——前置审计与最小受控检查

- 任务 ID：20261022-character-skills-inference-b10-sa2003
- 负责人：批10-2003审计员（GLM 5.3 Flash 260828，workflow 子代理，单 ask）
- 状态：**已完成（可闭合；规则登记与实施批待进行）**
- 日期：2026-10-22

## 目标

批 9 遗留 431 行 C1 hint（载体 ability2003=SA_PowerDrain，形状与 ability99 同构但无规则）的闭合可行性审计：记录库存、执行侧证据（最小范围新增静态＋受控原生检查）、规则草案、候选行集分类、代表样本核对。

## 允许写入范围（本轮实际写入）

- `work/character_skills_b10_sa2003/`（4 脚本＋4 中间数据，可复跑）
- `output/ordinary_effects/ability2003/`（README.md／trace.json／native_checks.json／7 个反汇编片段——**规则判定可闭合，故按任务要求产出证据三件**）
- `output/character_skills/inference_inventory/b10_sa2003_scope.md`
- 本任务卡

## 关键结论（详见 scope §1–§5）

1. **可闭合**。2003 是**独立处理器** `AttackEffectCtrl.ExecSA_PowerDrain`@0x1037a08（方法 3373），与 99 的 `OnAttackAbilityPowerDrain`@0x1121be0 不同函数；但目标侧数据路径**同一**：param7/8/9→TimePowerUpData(_attack/_move/_defense)→setSupport2（multiCheck=true、时间 param0），Support2 聚合/倒计时链与 99 共用（复用既有证据，未重跑）。
2. **触发差异（须逐行披露）**：2003 仅 damageType==1（Skill）经 param3×Random.Range 门；Normal/Critical 恒不触发（99 是 param1/3/2 三路）。派发点在 CharaBehavior.Attack→OnDamagedTo（伤害≥1 后），不经 haveAbilityFlags。
3. 记录库存：CACHE 2003×265（p0 30×251/-1×10/60×2/90×1/300×1；p3 全 1；p7 全负、**例外 47000844 p7=+1**；p8 258 全负；p9 263 全正；p1/p2 全缺）；APK 2003×148（同构，p3 例外 50009=0.15）。
4. 431 行 C1 复核：载体 238 唯一；敵半句↔p7/p8/p9 活性 **0 反例**（7 行批 9 表面例外系「自身の攻撃力が上がる」半句↔p4=+0.2，恰为双向提交的正面证据）；符号 p7≤0/p8≤0/p9≥0 全成立。
5. 候选分类：**PROMOTABLE 239 行**（Y.G. 100/40 cid 全数；载体全在 CACHE 265 域；估值 ≈956 值行）；**hint 192 行**（载体 APK 域外）。
6. 受控原生检查 8 项全过（`native_checks.json`）；haveAbility 成员集合/List 分配/Random 抽样为显式模型，边界全文披露；未实机。

## 下一步（实施批建议）

1. 规则键 `skilllist|2003|/param0|/param3|/param7|/param8|/param9` 登记归整合者（本轮未改 rules.json）；occurrences 265/265/265/258/263，样本域=CACHE 265。
2. 实施批按 scope §4 门（P2 域/P3 唯一/P4 形状/P5 方向/P6 跨 cid）晋级 239 行；行级键 `inference_b10`、evidence_scope=`TEMPLATE_BATCH10_SA2003`；param9 用受伤量口径披露；p3=1 披露为「Skill 着弹即触发」。
3. 192 行 APK 载体留 hint（`carrier-out-of-domain`）；扩域（APK 148）另立小步。
4. 复合句自身半句（p4/5/6）只登记不分配，归属 fam11/自身バフ侧。

## 共享依赖（只读）

- `output/character_skills/profiles/{records.jsonl,rules.json,characters.csv}`、`output/character_skills/pages/*/card.json`、`work/character_skills_b9_debuff/debuff_rows_classified.json`
- `output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw`、`output/base_master/_mdSkill.json`
- `work/protection/{il2cpp_loader_seed1.bin,metadata_aei_decoded.bin}`、`scripts/{metadata_targets,il2cpp_sample_code,phase_d_chain_probe,chica_ordinary_rules,chica_timed_support,ordinary_99_probe}.py`
- 既有证据：`output/ordinary_effects/ability99/`、`output/card_comparison_cid30236/timed_support/`

## 最近更新

- 2026-10-22：审计与受控检查完成，产出 scope/证据三件/work 数据/任务卡；未 git 暂存。

---

## 实施节（20261022 批 10 实施员，GLM 5.3 Flash 260828，workflow 子代理，单 ask）

- 状态：**已完成（四 cohort 全量重建 0 失败；verify_full 10/10 PASS）**
- 本轮写入：`scripts/character_skills/rules.py`（2003 注册处：`_sa2003_rules()` 五键＋
  convert 分支 a==2003）、`card_page_inference_b10_sa2003.py`（新模块）、
  `card_page_data.py`（接入：批 8 gate 链后、批 9 前；b10 非 None 的行批 9 接管关闭）、
  `card_page_batch.py`（aggregate/plan 文案九批）、`card_page_policy.py`（b10 scope/九批）、
  `card_page_verify_full.py`（b10 计数透传）、`card_page_index.py`（EXPECTED_CAMPAIGN
  A 16,825/C 24,840/推断 2,700）、`work/character_skills_b10_sa2003/`（regen_rules_b10.py/
  snapshot_b10.py/reconcile_b10.py/smoke_test_b10.py＋新旧快照/smoke_result）、
  `output/character_skills/profiles/rules.json`（277→282 键）、
  `output/character_skills/pages/`（2236 卡重建＋README §23）、本任务卡。

### 规则注册（题给草案→rules.json）

- 新键恰 5：`skilllist|2003|/param0`（occ 265）／`/param3`（265）／`/param7`（265）／
  `/param8`（258）／`/param9`（263）；occurrences 经解码 skilllist 实测断言；
  status「已确认（静态及受控原生局部规则）」；origin=b10_sa2003_scope.md；evidence 9 件/键
  （ability2003 三件＋复用 timed_support/ability99 各三件）。
- **diff 证明**：regen_rules_b10.py 断言旧 277 键经 json.dumps(indent=1) round-trip 与原文件
  字节相等、合并后既有键序列化逐键字节相等；277→282 仅尾部追加 5 键
  （309,863→321,206 B）。未运行 profiles.main（records.jsonl/profiles.jsonl 禁改）。

### 晋级实施

- 晋级 **239 行/87 卡**（Y.G. **100 行/40 卡**；bosspattern 153＋denju 65＋charainfo 21），
  与审计 PROMOTABLE 集合双向差集为空（reconcile_b10.py）；值行 **941**（p7 239＋p9 239＋
  p8 233＋p0 230；9 行 p0=-1 无时长值行；6 行自身半句 p4/5/6 登记不分配）。
- hint **282**：审计 192（APK 域外 carrier-out-of-domain）＋4313 C3 multi-carrier 6＋
  charainfo 同文多 pattern 涉 2003 归属歧义 84（后两类为批 9 hint 接管改写，判定档位不变；
  其余 11 行 ambig 无 2003 由批 9 照常处理——30219 回归实测通过）。
- 行级「推断（模板批 10 SA2003）」、evidence_scope=TEMPLATE_BATCH10_SA2003、值行两层区分
  （规则本体已确认／本条归属推断）；触发条件（仅 Skill 型着弹）与 99 三路差异逐行披露；
  30338 防线（S2 经 2003 规则晋级、et13 正値候选仍在味方バフ A 行）与 99 混淆防线
  （样本域 265/133 分清；sub_effect 伪影不消费）逐行落位。

### 指标（old→new；分母 N_all 41,665 不变）

- A 16,586→**16,825**（+239）；C 25,079→**24,840**（−239）；original_A 13,859 不变；
  整行推断 2,461→**2,700**；整行确认 **266 不变**；partial_A 16,219→16,458。
- coverage 计数：b10 239/282；批 1–8 计数不变；批 9 35 晋级不变、hint 938→417（521 行
  接管＝239＋282，对账闭合）。
- Y.G.：净新增 **100**/受益卡 **40**（去重）/唯一 NFKC 正文新增 **2** 文；绝对累计
  448→**548 行**/108 卡（不变，40 卡均已有推断行）/25→**27 文**；阶段口径（批 8＋9＋10）
  170→**270 行**/去重受益 62→**92 卡**（批 10 与批 8∪9 卡重叠 10）/20→**22 文**。
- old→new：行级变化恰 **521**（239 C→A＋282 hint 接管/登记）、other **0**、非 C→A 翻转 **0**；
  卡级 2,236 卡 implementation_status 文案＋b10 两键；87 张晋级卡派生键 ±1；其余 2,149 卡
  仅键级/文案变化。
- 分 cohort（晋级/hint）：ge60 42＋14、40to59 172＋93、20to39 25＋141、remaining 0＋34。
- 签名：四 cohort 同签名 `4436d984…65fc2b`（source_signature `e146440d…` 更新；
  dependency_signature `bc9b353f…` 因 rules.json 变化更新——29 项清单不变，新证据目录不在
  清单内、由模块 INFR-01 存在性检查覆盖，与批 5–9 同口径）；run_id：ge60
  `20261021T173102384103Z-7e17aa44`、40to59 `20261021T173122883069Z-d0ed9a6e`、20to39
  `20261021T173238918975Z-4979876c`、remaining `20261021T173351341580Z-d2f031a7`。
- 验证：card_page_batch 四 cohort 0 失败 0 stale；card_page_index.py --execute 入口页刷新
  （entry_pages CURRENT，自检通过）；card_page_verify_full.py **10/10 PASS**
  （receipt 2,236/2,236、产物哈希 4,472/4,472、29 依赖、行 41,665、source 解引用 68,318、
  值相等 9,103、chip 41,665、campaign 对账、入口页）。

### 遗留/未做

- APK 148 条 2003 域与 192 行 hint 未扩域（题给样本域=CACHE 265）；扩域另立小步
  （届时 occurrences 双列、行级 layer 披露）。
- param4/5/6 自身侧未登记换算（scope §3）；clamp 边界/重复施加沿用 99 侧「另论」口径。
- 未 git 暂存/提交（按任务约定）。

---

## 修复节（20261022 批 10 缺陷修复员，GLM 5.3 Flash 260828，workflow 子代理，单 ask）

- 状态：**已完成（B10-RV-01..05 全部已修；四 cohort 重建 0 失败；verify_full 10/10 PASS）**
- 审查对象：`output/character_skills/review/inference_b10_sa2003_20261022_deepseek/`
  （REPORT.md／issues.jsonl，结论 REQUEST_CHANGES：1×M1＋4×L）
- 修复边界：**不动 raw 值、行类、证据等级、晋级/hint 判定；rules.json 不改**
  （dependency_signature `bc9b353f…` 不变；source_signature `e146440d…`→`e64f250a…`
  因生成器代码变化更新；四 cohort 新组合签名 `3cb73f2f…`）。

### 逐条修复

- **B10-RV-01（M1）已修**：`card_page_inference_b10_sa2003.py` `_promote` 新增
  `via_pattern` 参数（charainfo 分支传入已算出的同页同文 pattern id）；21 条 charainfo
  晋级行 chain_desc/numeric_source/answer note/行摘要的链前缀由
  「charainfo|…|CACHE own children→boss_skill.s_ability→…」改为
  「charainfo|⟨cid⟩|CACHE 经同页同文 bosspattern|⟨patternid⟩|CACHE→s_ability→
  skilllist|⟨载体⟩|CACHE(…)」；`inference_b10` 元数据新增 `via_pattern`
  （`card_page_data.py` 透传；**存 list 不存 tuple**——首版 tuple 被页面 validate
  `json.loads(payload)==card` 断言拦截，40to59 12 卡 FAILED 后即改，重跑通过）。
  21 行 pattern id 与审查 affected_rows 逐行一致（含 337→40033702、20727→42072701、
  20728→42072801）。
- **B10-RV-02（L）已修**：`b10_sa2003_scope.md` §2.1 与 `ability2003/README.md` 的
  `drain_enemy_mapping.txt` 指针改为完整路径
  `output/card_comparison_cid30236/timed_support/drain_enemy_mapping.txt`
  （99 目标侧路径既有片段，本批复用；ability99 目录无此文件）。
- **B10-RV-03/-04（L）已修**：行级「适用范围披露」改键级汇总一次
  （p0/p3/p7 各 265、p8 258、p9 263，origin=rules.json 登记值；实测 239/239 行含
  `/param3=265` 且无按 param 重复段）——RV-03（p3 occurrence 行级出现）与 RV-04
  （去重）一次解决；值行 note 内单键口径保留。
- **B10-RV-05（L）已修**：`probe_sa2003.py` 删恒真式 `or True` 改显式断言；首次重跑
  即暴露真实语义——**threshold_reject_apk 拒绝时 submission=0 但 draws=1**（Random.Range
  在门到达时必调用），断言改为「门到达（kind==1 且 haveAbility 模型含 2003）⇔ draws==1」；
  重跑 8/8 passed；`trace.json` script_sha256 `07f148b3…`→`03458d0e…`（cache b2e00aa0/
  APK 21966993/native 562a6975/metadata 07d582df 与审查记录逐一相等）；
  `native_checks.json` 随探针重建；ability2003 证据目录不在 29 项依赖清单内（INFR-01
  存在性检查覆盖，口径不变）。

### 重建与 old→new 对账

- 重建：ge60 34/34、40to59 290/290、20to39 436/436、remaining 1,476/1,476，全 0 失败；
  run_id：ge60 `20261021T181607083713Z-6f2f2103`、40to59 `20261021T181620347727Z-374d2ad1`、
  20to39 `20261021T181734683142Z-231e09a7`、remaining/campaign
  `20261021T181848852748Z-b1ebc45d`；`card_page_index.py --execute` 入口页 CURRENT；
  `card_page_verify_full.py` **10/10 PASS**（receipt 2,236/2,236、产物哈希 4,472/4,472、
  29 依赖、行 41,665、source 解引用 68,318、值相等 9,103、chip 41,665、campaign 对账、
  入口页；b10 计数 239/282、b9 35/417 等全部不变）。
- old→new（`work/character_skills_b10_rv_fix/compare_fix.py`，全量 2,236 卡逐卡 JSON
  比对，old＝本轮各 run transactions/backup 修复前 card.json）：变化卡恰 **87**、
  变化行恰 **239**（b10 晋级行全体；其中 21 行链前缀变化、全部 239 行 unknown_reasons[0]
  披露汇总）；raw_value/value/rule_key/field_path/conversion/source/evidence 多重集
  941/941 零变化；行类/证据/晋级/hint 判定零变化；**b10 集合外行与卡零变化**。
  四联指标 A 16,825/C 24,840/推断 2,700/确认 266/原文A 13,859 不变（N_all 41,665 不变）。
- 本轮写入：`scripts/character_skills/card_page_inference_b10_sa2003.py`、
  `card_page_data.py`（inference_b10 透传 via_pattern）、
  `work/character_skills_b10_sa2003/probe_sa2003.py`、
  `output/ordinary_effects/ability2003/{trace.json,native_checks.json,README.md}`、
  `output/character_skills/inference_inventory/b10_sa2003_scope.md`、
  `output/character_skills/pages/`（87 卡重建＋README §23.2/§23.5）、
  `work/character_skills_b10_rv_fix/`（比对脚本与快照）、本任务卡。未 git 暂存/提交。

---

## 修正节二（20261022 批 10 残留修正员，GLM 5.3 Flash 260828，workflow 子代理，单 ask）

- 状态：**已完成（B10-RV-06 全部 63 处残留已修；四 cohort 重建 0 失败；verify_full 10/10 PASS）**
- 审查对象：同审查 ID 复验轮 `RECHECK.md`／`checks/recheck_residual.json`
  （结论 REQUEST_CHANGES：RV-01 部分闭合——21 条 charainfo 晋级行仍各含 3 处
  「own children」残留，共 63 处，与 records.jsonl/links 的 charainfo children=0、
  boss_skill_refs=0、sa_ability_refs=0 事实矛盾）。
- 修复边界：**只改三处披露文本；raw 值/值文案/行类/证据等级/晋级与 hint 判定零变化；
  rules.json 不改**（dependency_signature `bc9b353f…` 不变；source_signature
  `e64f250a…`→`3e05dae3…` 因生成器文本变化更新；新组合签名
  `ab364b87f9aa73d03fe2a6e833258b0dd51bdf6b0bbd7c22cccf34d0991e258f`）。

### 表感知修正（B10-RV-06）

- `scripts/character_skills/card_page_inference_b10_sa2003.py`：
  1. 家族文案：新增 `B10_FAMILY_CHARAINFO`＋`family_for(table)`（`card_page_data.py`
     透传）。charainfo 行＝「charainfo 记录无 own children；载体主张经同页同文
     bosspattern（G5 唯一）→s_ability→skilllist ability2003 SA_PowerDrain 载体）」；
     bosspattern/denju/dlb 行**逐字节保留**原 `B10_FAMILY` 文案（含表清单，218 行零
     变化——首版误将通用文案表清单去掉 charainfo，全量比对暴露 218 行 family 变化后
     即改回，重跑通过）。
  2. `unknown_reasons[3]`（跨记录归属依据）：`_promote` 内 P2/P3 段表感知——charainfo
     行＝「P2/P3：同页同文 bosspattern 的 s_ability 链恰 1 个 CACHE 层 ability2003
     记录∈265 条样本域」；其余表保留原 own children 段。
  3. `unknown_reasons[4]`：`_B1_DISCLOSURE` 常量改 `_b1_disclosure(table)` 函数——
     charainfo 行＝「本批载体主张只认同页同文 bosspattern 的 s_ability 链」；其余表
     保留原句（含「批 9 §3.1 审计同法」注）。
- `output/character_skills/pages/README.md`：§23.1 链条目补行级披露表感知口径交叉
  引用；新增 §23.6（复验残留修正）。
- 口径注记：charainfo 行 family 按审查修复建议保留「无 own children」**否定式**提及；
  复验若以裸子串计数，family 仍各计 1 处——肯定式断言实测 **0** 处（镜像
  `recheck_scan2.py` 口径复扫：21 行否定式提及、肯定式 0；218 条
  bosspattern/denju/dlb 晋级行保留原文案）。

### 重建与对账

- 重建：`card_page_batch.py --execute --resume` 四 cohort 0 失败（ge60 34/34、40to59
  290/290、20to39 436/436、remaining 1,476/1,476）；run_id：ge60
  `20261021T184523028496Z-4a8cb6e3`、40to59 `20261021T184534571410Z-b49a49ea`、20to39
  `20261021T184635882287Z-afc8d278`、remaining/campaign
  `20261021T184732951573Z-a3d7eb2a`；`card_page_index.py --execute` 入口页 CURRENT
  （A 16,825/C 24,840/确认 266/原文A 13,859）；`card_page_verify_full.py` **10/10 PASS**
  （receipt 2,236/2,236、产物哈希 4,472/4,472、29 依赖、行 41,665、source 解引用
  68,318、值相等 9,103、chip 41,665、campaign 对账、入口页；coverage b10 239/282、
  b9 35/417 等计数全部不变）。
- old→new（`work/character_skills_b10_fix2/compare_fix2.py`，全量 2,236 卡逐卡 JSON
  比对，old＝重建前快照 `work/character_skills_b10_fix2/pages_before.json`）：
  变化卡恰 **21**、变化行恰 **21**（charainfo 晋级行全体）、每行恰 3 处字段文本
  （`inference_b10.family`／`unknown_reasons[3]`／`unknown_reasons[4]` 各 21）；
  答案数组（raw_value/value/rule_key/source/evidence 等）零变化；卡级非行键零变化；
  其余 2,215 卡逐卡全等；21 行 note 内除三段新旧文本外逐字节相等。
- 本轮写入：`scripts/character_skills/card_page_inference_b10_sa2003.py`、
  `card_page_data.py`（family 一行透传）、`output/character_skills/pages/`（21 卡重建
  ＋README §23.1/§23.6）、`work/character_skills_b10_fix2/`（快照与比对脚本）、
  本任务卡。未 git 暂存/提交。
