# 任务卡：角色技能页 · 批 8 暴击增益（bossskill.s_ability→skilllist 2012 链）

- 任务 ID：20261021-character-skills-inference-b8-crit2012
- 状态：**实施完成（2026-10-21；四 cohort 全量重建 0 失败，verify_full 10/10 PASS）**
- 负责人／对话标识：批8链审计员（GLM 5.3 Flash 260828，workflow 子代理）
- 上游依据：批 6 crit hint（H1 386＋charainfo 继承 55，`b6_bossbuff_scope.md` §6）；
  cid349 先例链；`rules.json skilllist|2012` 3 条已确认规则；
  `output/ordinary_effects/ability2012/`＋`output/card_comparison_cid30236/critical/` 证据

## 目标

把必殺/传授系行的暴击段从 hint 晋级为「推断」值行——唯一消费路径是
bossskill(type13)→s_ability→skilllist(ability=2012) 载体上的 `skilllist|2012|/param4`
（暴击率加算，pp）与 `/param5`（暴伤系数加算）。普通 1110→1095 自身增益暴击段单列
不进本批；归属未化解的候选留 hint。

## 前置审计结论（详见 scope）

- 范围文档：`output/character_skills/inference_inventory/b8_crit2012_scope.md`
- rules.json 实测：`skilllist|2012|/param0`（occ406）/`/param4`（occ308）/`/param5`
  （occ311）三条已确认；与 v3 CACHE 406 条 2012 记录实测逐项一致（p4 存在 308 全>0、
  p5 311 全>0、p0 406={22.5,24.15,30,60,100,300}、p7 {20×305,1×99,缺2}、p8
  {31×307,64×99}）——README/native_checks 口径吻合
- 链库存：v3 CACHE bossskill 3,745 中 982 含 s_ability，→2012 共 397（type13 中继 345）；
  537 个 pattern 链上带 2012 载体；页面行可达 148 cid（pattern 路径）＋86 cid（denju
  路径，denju_id==cid 实测）；distinct 载体 325/406。profiles 层已以
  `link_kind='boss_skill.s_ability'` 解析该链且子记录带全 answers——实施批无需新解析器
- 行集：C∪b6/b7-hint 含クリティカル＝全库 3,837 行／Y.G. 629 行
- **晋级候选：全库 343 行（~686 值行，p4+p5 各一条）/ Y.G. 159 行（~318 值行）**——
  629 行候选池不可整体晋级；留 hint 3,494 行（APK 载体域外 196、charainfo 同文多
  pattern 104、b7 家族 252、job_ability/supporterskill 303、no-2012-chain 68、
  multi-carrier 12、relay-non13 23 等）
- 交叉检查全过：G1′ 句唯一子串 343/343；跨 cid 载体競争 0；批 6 crit hint 545 行去向
  promote 271／域外 166／多 pattern 103／no-chain 3／shape 2
- 代表样本 9 行独立重建链核对通过（Y.G. 3／非 Y.G. 6；bosspattern/denju/charainfo/
  dlb/ability 5 路径；含 multi-carrier、shape-mismatch、域外、1110→1095 排除各类）

## 允许写入（实施批）

- 脚本：`scripts/character_skills/card_page_inference_b8_crit2012.py`（新）；
  `card_page_data.py`/`card_page_policy.py`/`card_page_batch.py`/`card_page_render_v2.py`
  最小接线（行键 `inference_b8`＋label；批 6 gate 链后同位接入）
- work：`work/character_skills_b8_crit2012/`
- 输出：pages 产物（batch 入口重建受影响页）＋`inference_inventory/` 本批文档；
  不碰 profiles/rules/links 共享层、不动批 1–7 行与键、不 git 暂存提交

## 共享依赖（只读）

- `output/character_skills/profiles/{records.jsonl,rules.json,characters.csv}`
- 证据：`output/ordinary_effects/ability2012/`（README/trace/native_checks）、
  `output/card_comparison_cid30236/critical/`、
  `output/card_comparison_cid30236/field_dictionary.json`
- 解码侧：`output/cache_full_20261015_v3/records.jsonl`（v3 全量；行源 pointer 对位）、
  `output/base_master/_mdSkill.json`/`_mdBossInfo.json`（仅 APK 载体层判定与域外拦截，
  不消费其参数）

## 最近更新

- 2026-10-21：前置审计完成（scan_b8_chain.py＋scan_b8_rows.py＋audit_samples.py；
  b8_chain_inventory.json／b8_rows.json／b8_rows_classified.json／b8_samples.json＋scope
  文档）。关键实测：occurrences 交叉验证一致；cid349 链逐记录核实；PROMOTE-CAND
  343/159；句唯一性 343/343；跨 cid 競争 0。

## 下一步（实施批入口）

1. 主持确认 scope §4，特别是：①D1 裁决——时长值行仍归 t13 p3（b8 建议不出 p0 值行，
   只在 note 登记载体 p0）；②非 t13 中继 23 行留 hint 不猜；③APK 载体 196 行域外不扩域；
   ④与批 6 的接续（b6 仅因 G4 而 hint 的行重评补非 crit 值行，不重写既有键）；
2. 按 scope §4.1 门控 G1–G8 实施模块；先代表样本回归（349/10215/20105/10212/12236 晋级、
   30105 multi-carrier、20301 shape、12238 普通链排除、11004 域外），再全量；
3. 逐行清单复用 `work/character_skills_b8_crit2012/b8_rows_classified.json`，
   实施时以现场数据重建再校验（b5/b6/b7 同法）；行源 pointer 对位失败即 hint
   （本轮 dlb 25 行教训，按 field_json_pointer 修复后归位域外类）。

## 实施节（2026-10-21，批8实施员 GLM 5.3 Flash 260828）

### 实现

- 新模块 `scripts/character_skills/card_page_inference_b8_crit2012.py`：evaluate 五表行
  （bosspattern/charainfo/denju/dlb/heroicskilllist，含 クリティカル、`not answers`），
  G1–G8 门控逐行重审（scope §4.1），值行只消费 `skilllist|2012|/param4|/param5`。
  链解析复用 links 既有产物（boss_skill_refs/sa_ability_refs 带完整 raw record，实测
  9,102 条全 resolved；bsr/sar 未挂载时回退 `data.skill` 解码索引——dlb 链走此回退）；
  bosspattern 行按 raw skillidN 槽位逐一对位 bsr（防漏中继），denju/dlb 行按
  reference_field 的 `bosspattern[pid]` 分组。G5 样本域按**载体记录自身所属层**判定
  （decoded skilllist ability2012 集合实测 406，与 rules conditions 一致）。
- 接线（最小改动）：`card_page_data.py`（b8 调用点在批 6/7 gate 链后＋promoted_b8 分支
  ＋inference_b8/inference_b8_hint 键＋b6 hint 保留＋coverage 计数）、
  `card_page_policy.py`（b8 开关/scope/message 七批）、`card_page_batch.py`
  （aggregate 两键＋plan 文案＋permission_boundary 指向本任务卡）、
  `card_page_render_v2.py`（inference_b8/b8_hint 审计标签）、`card_page_index.py`
  （EXPECTED_CAMPAIGN 基线更新为批 8 后值）、`card_page_verify_full.py`（aggregate
  两键透传对齐，检查语义未动）。
- 行级：`evidence_label="推断（模板批 8 暴击 2012 链）"`、`inference_b8` 元数据、
  evidence_scope=`TEMPLATE_BATCH8_CRIT2012`；值行 numeric_source=「模板推断（批 8 暴击
  2012 链：…→bossskill|<id>|<layer>(type13,slot N)→s_ability→skilllist|<carrier>|<layer>
  (ability2012)）」；note 固定含「规则本体：已确认（…指规则本身）；本条数值归属＝推断，
  不升确认」两层区分＋对象/条件双源逐字＋载体 /param0 登记（D1：不出 p0 值行）＋
  Support2 上限与 README 口径＋样本域 occ 406/308/311。批 8 晋级的 274 条原批 6 hint 行
  **保留 inference_b6_hint 键**（不重写批 6 键）。

### 结果（实测）

- 晋级 **346**（Y.G. 159）/值行 **692**（p4 346＋p5 346；Y.G. 318）；留 hint **428**
  （Y.G. 60）；行集 774（promote＋hint 恰等于批 8 表集行池，0 静默丢弃）。
- campaign（N_all 41,665 不变）：A 16,205→**16,551**（+346）；C 25,460→**25,114**；
  original_A 13,859 不变；整行推断 2,080→**2,426**；整行确认 **266 不变**；既有批 1–7
  推断行 2,080 零变化；B 0 不变。
- **Y.G. 专项**：净新增晋级 159 行／受益 Y.G. 卡 60／唯一 NFKC 正文新增 19 文
  （基线 0/0/0）；yg_priority 剩余 2,066→**1,907**（159 行全在该集合内，实测交集 159）。
- 分 cohort（晋级/hint）：ge60 37＋10、40to59 261＋188、20to39 48＋147、remaining 0＋83。

### 与审计预分类的差异（已逐行核实，详见 pages/README.md §21.3）

- 晋级 +3：20607 系三行跨层链（中继段仅 APK 层可见、s_ability 目标由 links 解析到
  v3 CACHE 载体 42060713∈406 条样本域）——按 G5 门载体层语义晋级，跨层事实逐行披露；
  审计把 pattern 层传播给载体判定，实施不沿用。晋级 343→346（Y.G. 159 不变）。
- hint 原因改判 3：20701 系三行 no-2012-chain→APK 载体域外（links 解析出 APK 载体
  42070115/42070116，审计 pointer 解析未达；仍留 hint）。
- charainfo-sa-route 2 行（2280/5242）：实施以原始 charainfo 记录（Inputs cache_chara/
  apk_chara）判定 s_ability→2012 路由（links 条目 record 为执行副本无该字段）——与审计
  分类一致，hint 文案含层与载体值。

### 验证（全部本轮实际执行）

- 代表样本回归 9/9（`work/character_skills_b8_crit2012/regress_samples.py`）：349/10215/
  20105/10212/12236 晋级值逐条核对；30105 multi-carrier、20301 形状不符、11004 域外
  留 hint；12238 普通 skilllist 行零触碰。
- 全库试算对账（`dryrun_full.py`→`dryrun_vs_audit.json`）：2236 卡 vs 审计
  b8_rows_classified.json——row_id 集合 0 缺 0 增，promote/hint 逐行一致（仅上述 3+3 行）；
  跨 cid 载体竞争 0（G8 守卫实测未触发）。
- old→new 多重集比对（`old_new_diff.py`→`old_new_diff.json`，批 8 前备份→终版）：
  行集合零增删；变化行恰 774＝346 晋级＋428 hint，0 个非本批变化行；既有批 1–7 键零改写。
- 重建：四 cohort 全量 0 失败（ge60 34/34、40to59 290/290、20to39 436/436、
  remaining 1476/1476）；签名 `8cfbbd91c62486b13313948d915e486936ba104c461d8e25ae60b5783b2982f2`；
  run_id：ge60 `20261021T112226186343Z-ca057ac3`、40to59 `20261021T112237214946Z-f028c17a`、
  20to39 `20261021T112335498652Z-5dbc7ac6`、remaining `20261021T112432592211Z-f7825add`
  （campaign 同 run）；dependency_signature `4029ad13…` 不变（29/29 依赖重算未变）。
- 全量机器检查 `card_page_verify_full.py`：**10/10 PASS**（2236 receipt/4,472 哈希/29 依赖/
  41,665 行/67,239 source 解引用/8,024 推断值原值相等/41,665 chip/campaign 对账/入口页
  CURRENT）；入口页 `card_page_index.py --execute` 已按新基线刷新。
- 过程注记：终轮重建前曾出现两类阶段性 FAIL，均已修复并复验——①REUSED 卡 receipt.run_id
  与新 run 指针不一致（改用无 --resume 重建归位）；②40to59/20to39 构建期间修改
  card_page_index.py（属 source_paths 签名范围）导致四 cohort 签名不一致、campaign 只聚合
  2 个 cohort（脚本稳定后四 cohort 同签名重建解决）。

### 边界遵守

- 普通技能 1110→1095 链行零触碰（skilllist 不在批 8 表集；skilllist-sub-2012 未审路由
  不消费）；非 t13 中继 23 行、APK 载体 196 行、多 pattern/多载体/形状/对象/方向不符各行
  全部留 hint 并逐行登记原因；不跨记录合并；值行/行级无确认字样（rule_body_status 保留
  rules.json 原值、渲染层按 B5-R01 限定口径显示）；未 git 暂存提交；未改 profiles/rules/
  links 共享层、批 1–7 行与键、旧审查报告。

## 微修节（20261021，批8微修员 GLM 5.3 Flash 260828——定向审查 B8-R01/R02/I02/R03 闭合）

审查：`output/character_skills/review/inference_b8_crit2012_20261021_deepseek/`（DeepSeek
定向审查，PASS_WITH_EXPLICIT_SCOPE_LIMITS；3 Low＋2 Info）。本轮**只修披露文本**：不动
任何数值、行类、证据等级与晋级/hint 判定（行集/键/coverage 计数零变化）。

### 修改内容（全部在 `scripts/character_skills/card_page_inference_b8_crit2012.py`）

- **B8-R01（8 条 heroic hint 原因改写）**：heroicskilllist 分支新增披露专用路径
  `_heroic_chain_hint`——记录实有 `boss_patternN` 字段（原「记录无 pattern 字段」不实），
  按实际链解析登记：有 boss_pattern、链上无 type13→s_ability→2012 载体（no-2012-chain），
  逐行附中继类型与 s_ability 目标 ability（20632 type3 无指向／3228 type110+100 无指向／
  4292 type110+3 s_ability=0／6319×5 type22 s_ability=40631912→skilllist|40631912|APK
  ability=2003）。恒返回 hint；链索引读**已声明依赖**（decoded bossinfo／_mdBossInfo.json，
  未新增依赖、未读 records.jsonl）。
- **B8-R02（20510 denju 晋级行）**：`_multi_relay_disclosure` 披露专用注记——行记录 2 条
  patternidN（42051003/42051004，后者 sinfo 空）链上 3 条 type13→2012 中继
  （42051003.skillid3／42051004.skillid3／42051004.skillid6）同指唯一载体
  skilllist|42051013|CACHE；该行「唯一 type13 中继」措辞改为「载体唯一（多 pattern/多条
  type13 中继同指）」（extra_reason＋summary），值行 note 增披露段并登记本值行所取链
  （42051004→42051005 skillid6）。数值 0.275 不变。条件按现场数据计算，实测全库仅此
  1 行满足（denju ≥2 pattern 且 ≥2 条 t13→2012 中继）。
- **B8-I02（20301 两条 hint）**：G4 形状不符 hint 追加披露「载体 /param8=64（MYSELF）与
  句面对象『味方全体』不符」（判定不变；实测 G4 mismatch hint 全库恰此 2 行）。
- **B8-R03（计数）**：模块 docstring 加注审计预分类 224/83/36、122 cid 与实施后
  225/84/37、123 cid 的差异来源；pages/README.md §21.2 补路径分解、§21.3 加计数口径注记、
  hint 分类更新（no-2012-chain 65→73 含 heroic 8；「无 pattern 字段」桶剩 denju/dlb 4）、
  新增 §21.6 微修轮记录。

### 验证（全部本轮实际执行）

- 目标卡试算 `work/character_skills_b8_crit2012/microfix_probe.py`：6 卡 11 行判定全部
  与预期一致（8+2 hint、1 promote 值行 2 条），新披露文本逐行核对。
- old→new 多重集比对 `work/character_skills_b8_crit2012/microfix_old_new_diff.py`（基线＝
  批 8 终版 run `20261021T1122…` 四 cohort transactions backup→本轮 pages）：**变化行恰 11**、
  与计划逐一相等；row_id 集合零增删；row_class/japanese/evidence/association_evidence 与
  answers 数值/证据多重集逐行零变化；既有批 1–7 键零改写；计划外变化行 0。首轮曾以
  批 8 第一轮 run 备份为基线误报 2280/5242 两行——经逐字段核对为基线错位（该两行差异属
  批 8 内部两轮之间的 charainfo-sa-route 文案修正，本轮零变化），改用本轮 run 备份后通过。
- 重建：四 cohort 0 失败（ge60 34/34、40to59 290/290、20to39 436/436、remaining 1476/1476）；
  新签名 `0d646a89c69286e8e081a0066096a6b4724f1587c4a5f8030c9d1d5fdfacb2ad`
  （source_signature `1a714ac9…` 更新；dependency_signature `4029ad13…` 不变、29/29）；run_id：
  ge60 `20261021T121242109673Z-957fcb1e`、40to59 `20261021T121302310002Z-b907d946`、
  20to39 `20261021T121406892629Z-da8181bd`、remaining `20261021T121509083854Z-0a67dc16`
  （campaign 同 run）；receipt 2236/2236 SUCCESS、0 stale、哈希 4,472/4,472。
- `card_page_verify_full.py` **10/10 PASS**；指标与微修前逐项一致：campaign A 16,551/
  41,665、整行推断 2,426、确认 266、原文A 13,859、C 25,114；批 8 346/428；分 cohort
  37＋10／261＋188／48＋147／0＋83；Y.G. 159 行/60 卡/NFKC 正文 19/hint 60、
  yg_priority 剩余 1,907。入口页 `card_page_index.py --execute` 刷新（CURRENT）。

### 移交注记（不在本微修写入范围）

- `docs/tasks/character-skills-progress.md` 第 29 行「晋级 346 行（Y.G. 159 行、122 cid；
  bosspattern 224＋denju 83＋charainfo 36）」为 20607 三行晋级前口径——共享进度文件不归
  本微修任务改写，请整合者同步为 225＋84＋37＝346、123 cid（或在行内加注「分解为
  20607 调整前口径，实际 225/84/37、123 cid，见 pages/README.md §21.3」）。
