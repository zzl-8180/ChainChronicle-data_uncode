# 任务卡：批 11 ability1095（Always3 自身增益）——前置审计（纯分析）

- 任务 ID：20261022-character-skills-inference-b11-sa1095
- 负责人：批11-1095审计员（GLM 5.3 Flash 260828，workflow 子代理，单 ask）
- 状态：**前置审计已完成（未晋级；规则登记与实施批待进行）**
- 日期：2026-10-22

## 目标

普通自身增益链（普通 skilllist 父记录→`sub[]`→ability1095 Always3 记录）的前置审计：规则库存、记录库存（CACHE/APK）、候选行集逐行分类（形状/归属/方向）、代表样本核对、范围设计。**三套 1095 相关命名空间分清**：本批 1110 系父→sub 1095；批 5 job_ability→skill_ids→skilllist|65000001（跨表链）；批 8 bossskill.s_ability→skilllist 2012（暴击链）。

## 允许写入范围（本轮实际写入）

- `work/character_skills_b11_sa1095/`（3 脚本＋3 中间数据：`1095_inventory.json`、`b11_rows.json`、`b11_rows_classified.json`、`b11_samples.json`，全可复跑）
- `output/character_skills/inference_inventory/b11_sa1095_scope.md`
- 本任务卡

## 关键结论（详见 scope §1–§6）

1. **规则库存**：rules.json `skilllist|1095` 恰 5 键（p1/p2/p3/p5/p6），status 全「已确认」；p1/p3 occurrences=407 与 407 条根记录实测一致，**p2/p5/p6 occurrences=1/1/2 是「已核 ID 数」口径（65000001；p6 加 43023601）**——与 p1/p3 的「存在数」口径不同，登记时须注明。证据目录 `output/ordinary_effects/ability1095/`（README/trace/native_checks 32 项/5 片段）清点在；rules evidence 相对 origin `output/card_comparison_cid30236/` 全实存。records.jsonl 中 86 条记录带 1095 answers（相邻集记录级候选，页面行未消费）。
2. **记录库存**：CACHE 1095 根 407；被父 sub 引用 230（每父恰 1、无共享、全部同时是根）；父 ability=1110 UniverseMana×145＋26 ManaGet×69＋1089 PirikaExtend×15＋1017×1；APK 52 sub/35 父（域外同构）。sub 参数：**p1 全部活性**（1.05–18.5 全 >1）、p2 80 非中性、p3 79（0.4–0.7 全 <1）、p5 148、p6 128；p0/param9 全缺、flag 全 0；p4（×2）/p7/p8（×5）语义未推广。基础句形态＝「⟨ATTR⟩(と…)*が上がる。」（**句面无「自身の」**，对象=规则 target 装有者自身）。
3. **候选行集**：全库普通 skilllist C/hint 行 12,285（Y.G. 775）；有 1095 sub **1,070（Y.G. 388）**，全部干净 C 行（0 既有 hint/晋级键）。任务书背景 2,508/229/326＝批 8 crit 池口径（子集），本批按全宇宙审计。逐行：**PROMOTABLE（tier A）34/23**（主张恰={p1}，34 cid 各 1）；**tier B 94/38**（形状完美，p2/p5/p6 规则已核 ID 外；现可部分晋级 131 值行，扩域后 295）；shape-mismatch 58、conditional 92、mixed 69、enemy-debuff 56、non-base 10、OOD 27；**multi-1095-sub 与 direction-mismatch 结构性为 0**；候选 186 行 G1′ 句唯一 186/186、跨 cid 竞争 0。
4. **批 5 去重**：65000001 不被任何 skilllist.sub 引用；候选池父/sub 无 6500xxxx；批 5 晋级 211 行与他表，两链零重叠、各自登记。
5. **代表样本 8 行**（Y.G. 4、父类型 1110/1089/26/1095）逐行核对全过，含排除集（adjacent-root-1095 cid1217 多重不符）示证。

## 下一步（实施批建议）

1. 规则键：现 5 键不改；tier B 处理二选一（整行 hint 保守／p1+p3 部分晋级 131 值行，scope §5.3）；p2/p5/p6 规则域扩展（407 条全域）须先做 critical/movement 原生检查扩展，另立批。
2. 实施批按 scope §5.2 门（P0–P6＋G1′）晋级 tier A 34 行/34 值行；行级键 `inference_b11`、evidence_scope=`TEMPLATE_BATCH11_SA1095`。
3. 相邻集 370 行（行源=1095 自身，含 b5 §7 严格句 5 行）与批 5 fam3 194 行延伸不入本批，另行批次。
4. APK 52/35 域外留 hint（`carrier-out-of-domain`）；扩域另立小步。

## 共享依赖（只读）

- `output/character_skills/profiles/{records.jsonl,rules.json,characters.csv}`、`output/character_skills/pages/*/card.json`
- `output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw`、`output/base_master/_mdSkill.json`
- `work/protection/metadata_aei_decoded.bin`、`scripts/{metadata_targets,il2cpp_sample_code}.py`
- 既有证据：`output/ordinary_effects/ability1095/`、`output/card_comparison_cid30236/`（origin/evidence 相对基）
- 前批口径：`work/character_skills_b8_crit2012/b8_rows_classified.json`（2,508/326 对账）、`b5_xtable_scope.md`（65000001 链与去重）

## 最近更新

- 2026-10-22：前置审计完成，产出 scope/work 数据/任务卡；未 git 暂存、未改 rules.json/pages。

---

## 实施节（20261022 批 11 实施员，GLM 5.3 Flash 260828，workflow 子代理，单 ask）

- 状态：**已完成（四 cohort 全量重建 0 失败；verify_full 10/10 PASS）**
- 本轮写入：`scripts/character_skills/card_page_inference_b11_sa1095.py`（新模块）、
  `card_page_data.py`（接入：批 10 gate 链之后；b11 evaluate/promote 分支/hint 分支/
  coverage 两键透传）、`card_page_batch.py`（aggregate 两键＋plan inference_layer/
  permission_boundary 文案「十批」）、`card_page_policy.py`（b11 scope＋message 文案）、
  `card_page_verify_full.py`（b11 两键透传）、`card_page_index.py`（EXPECTED_CAMPAIGN
  A 16,859/C 24,806/推断 2,734）、`output/character_skills/pages/`（2,236 卡重建＋
  README §24）、`work/character_skills_b11_impl_sa1095/`（snapshot_b11.py/
  smoke_test_b11.py/reconcile_b11.py＋pages_before.json 快照）、本任务卡。

### 实施口径

- **tier B 取保守案（scope §5.3 默认推荐）**：94 行整行留 hint
  `slot-rule-not-in-domain`（p2/p5/p6 现规则已核 ID 仅 65000001/43023601，
  occurrences 1/1/2 已核 ID 数口径），不出部分值行；「一描述一行值」纪律统一，
  p2/p5/p6 规则域扩展（407 条全域，须先 critical/movement 原生检查扩展）另立批。
- **rules.json 零变化**（五键既有；dependency_signature `bc9b353f…` 不变）——
  scope §1.1「occurrences 口径不统一」按登记原样引用并在行级披露一次注明。
- 行级「推断（模板批 11 自身增益 1095）」、evidence_scope=TEMPLATE_BATCH11_SA1095、
  `inference_b11` 元数据（via='own_sub_array'）；值行两层披露（规则本体已确认／
  本条归属推断）；对象=自身（rules.json target 逐字「装有此能力的接受者自身；
  安装来源/资格另论」＋句面省略主语披露）；条件文本逐字入 note；同父其他 sub
  登记不消费（条件半句归属为形状对照推断）；中性槽不补写。
- 门控逐行重验（P0 链/P1 基础句正则/P2 CACHE 407 域/P3 唯一＋跨 cid 守卫/P4 形状
  双向＋未推广槽/P5 方向/P6 对象/G1′ 句唯一）；父 ability==1095 相邻集 370 行与
  批 5 65000001 链不入本批。

### 重建与对账

- 重建：`card_page_batch.py --execute --resume` 四 cohort 0 失败（ge60 34/34、40to59
  290/290、20to39 436/436、remaining 1,476/1,476）；run_id：ge60
  `20261021T235722051533Z-e0a8e216`、40to59 `20261021T235739728003Z-ed43bab2`、
  20to39 `20261021T235900571015Z-17d38e5d`、remaining/campaign
  `20261022T000022805072Z-16279a82`；组合签名 `32fd61c4…1fcb`（source_signature
  `6b038408…` 因生成器代码变化更新；dependency_signature `bc9b353f…` 不变）。
- reconcile（`work/character_skills_b11_impl_sa1095/reconcile_b11.py`）：晋级集与审计
  PROMOTABLE **34/34 双向差集均为空**；hint 集 **406/406 相等**、类别关键词逐行核对
  **0 错位**；Y.G. 23/23；审计 8 代表样本烟测全过（smoke_test_b11.py，cid30002/30104/
  30001/2327 晋级、30102 tier B、30110 shape-mismatch、1296 APK 域外、1217 相邻集排除）。
- 指标（old→new；分母 N_all 41,665 不变）：A 16,825→**16,859**（+34）；C 24,840→
  **24,806**（−34）；original_A 13,859 不变；整行推断 2,700→**2,734**；整行确认
  **266 不变**（记录级 18＋类型外推 248）；partial_A 16,458→16,492；值行 34（全部
  `skilllist|1095|/param1`，原值 1.05–1.425）。
- Y.G.：净新增 **23** 行/净新增受益卡 **0**（23 cid 均已有批 1–10 推断行）/唯一 NFKC
  正文新增 **1** 文（「攻撃力が上がる。」）；累计 **571 行**/108 卡（不变）/**28 文**；
  阶段（批 8＋9＋10＋11）**293 行**/96 卡（92＋4）/**23 文**（22＋1）。
- old→new（pages_before.json 全量逐卡比对）：行级变化恰 **440**（34 晋级 C→A＋406
  hint 登记）、b11 集合外行 **0**、hint 行 answers 零变化（406/406）、非 C→A 翻转
  **0**；卡级全 2,236 卡 implementation_status 文案＋b11 两键，34 张晋级卡派生键 ±1。
- 分 cohort（晋级/hint）：ge60 8＋32（Y.G. 5＋20）、40to59 26＋288（Y.G. 18＋102）、
  20to39 0＋86（Y.G. 0＋1）、remaining 0＋0。
- 验证：`card_page_index.py --execute` 入口页刷新（entry_pages CURRENT，自检通过）；
  `card_page_verify_full.py` **10/10 PASS**（receipt 2,236/2,236、产物哈希 4,472/4,472、
  29 依赖、行 41,665、source 解引用 68,352（+34）、值相等 9,137（+34）、chip 41,665、
  campaign 对账、入口页）。

### 遗留/未做

- tier B 94 行保守案 hint；p2/p5/p6 规则域扩展另立批（扩后 295 值行）。
- APK 52 sub/35 父域外（27 行 carrier-out-of-domain hint）扩域另立小步。
- 相邻集 370 行（含批 5 §7 严格句 5 行）与批 5 fam3 194 行延伸另行批次。
- p4/p7/p8 语义未推广（活性即形状不符留 hint）；未实机；sub[] 装载路径无原生核实
  （归属=数据侧结构对应，披露口径见模块 docstring）。
- 未 git 暂存/提交（按任务约定）。
