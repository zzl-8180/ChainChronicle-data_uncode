# 任务卡：角色技能页 · 批 6 味方全体必殺バフ（Top20 #1 / bossskill 子记录解析前置批）

- 任务 ID：20261020-character-skills-inference-b6-bossbuff
- 状态：**实施完成（2026-10-20；四 cohort 全量重建＋对账复核通过，见文末实施节）**
- 负责人／对话标识：批6解析审计员（GLM 5.3 Flash 260828，workflow 子代理）
- 上游依据：`yg_coverage.md` §4/§5（批 6 行）、批 1 `TOP20.md` 家族 #1 注记、
  批 5 任务卡与 B5 审查（B5-R01～R04）

## 目标

把家族 #1「味方全体の⟨ATTR⟩が一定時間上がる。」（全库 2,137 行／667 cid；Y.G. 304 行）
从 hint 状态按 bossskill 子记录（type13）解析晋级为「推断」值行；同时给出 B5-R01
（值行 rule_status「已确认」字样）的处理建议。

## 前置审计结论（详见 scope）

- 范围文档：`output/character_skills/inference_inventory/b6_bossbuff_scope.md`
- bossskill 子记录已在 profiles 层解析（records.jsonl children 带 effect_type＋answers；
  8,842 实例／5,462 distinct id、类型零冲突）；「子记录类型无法解析」只是批 1 盘点索引
  缺口（enrich_v2.py 只索引顶层）→ **接入=实施批运行时建 child_type_index，不需要新解析器**
- rules.json bossskill 规则 140 条/55 型；fam1 唯一可消费载体＝type13 四槽
  （p1 攻/p2 防/guard/p3 时长/p6 移；occurrences=None 需样本域披露）
- 终版分类：**晋级候选 1,379**（直接 1,003＋charainfo 经同页同文 pattern 376；Y.G. 83）、
  **留 hint 758**（crit 386、charainfo 继承 175、同记录 fam11/fam13 冲突 36、链缺口 20、
  不可达 8、同文多 pattern ~130、多 t13 3）
  〔B6-RV-03 更正：以上为实施前审计估算；实施后最终分类与修复后口径见文末「修复轮次」节〕
- ⚠️ 待主持裁决：任务卡字面「非首段留 hint」会把晋级收缩到 ~10 行；scope §4.1 推荐
  以「唯一 t13 载体＋形状匹配」替代（b5 第 2◆段先例），并按 B5-R03 同性质披露。
- B5-R01 建议：影响面 1,931 值行/493 页（pilot 941/b3 89/b4 285/b5 616，全部 skilllist 键）；
  **推荐纯渲染层限定**（card_page_render_v2.py 特判，card.json 不变）；若口径约束 card.json
  数据层则需 4 模块改写＋493 页重跑（scope §7）。

## 允许写入（实施批）

- 脚本：`scripts/character_skills/card_page_inference_b6_bossbuff.py`（新）；
  `card_page_data.py`/`card_page_policy.py`/`card_page_render_v2.py` 最小接线（行键
  `inference_b6`＋label＋rule_status 渲染口径）
- work：`work/character_skills_b6_bossbuff/`
- 输出：pages 产物（batch 入口重建受影响页）＋`output/character_skills/inference_inventory/`
  本批文档；不碰 profiles/rules/links 共享层、不重跑 profiles.py、不 git 暂存提交

## 共享依赖（只读）

- `output/character_skills/profiles/{records.jsonl,rules.json,characters.csv}`、
  `output/character_skills/links/character_skills.jsonl`（slot 在 boss_skill_refs）
- 证据：`output/boss_heal/field_dictionary.json`、`output/boss_chain/type13_basis/`（7 件）
- 页面 gate 接线位：`card_page_data.py:828` 起的批 2–5 gate 链

## 最近更新

- 2026-10-20：前置审计完成（scan_fam1/audit_part2/3/4 四脚本＋三份行级 JSON＋scope 文档）；
  关键实测：2,137/2,137 方向=上がる；既有 inference 键 0；形状不符 0/1,425；
  skilllist 候选确认为伤害句噪声（排除）；charainfo 自身 answers 是伤害侧副本（不消费）。

## 下一步（实施批入口）

1. 主持裁决 scope §4.1（非首段口径）与 §7（B5-R01 方案 A/B）；
2. 按 scope §5 门控 G1–G7 实施模块，先 10 行代表样本（10001 pattern0/skilltext、
   crit 行、multi-pattern 行、30236）回归，再全量；
3. 逐行清单复用 `work/character_skills_b6_bossbuff/fam1_classification.json`
   （行级 cls/reasons/t13 原值），实施时以现场数据重建再校验。

---

## 实施节（20261020 批 6 实施员，GLM 5.3 Flash 260828）

- 状态：**已完成（四 cohort 全量重建＋对账复核通过）**
- 主持裁决（实施前经 workflow 主持确认）：
  - **非首段口径＝scope §4.1 替代口径**：「非首段留 hint」按其本意（INFR-05：归属无法逐句
    化解时不猜）限定理解；非首段行在 G2 唯一 t13 载体＋G3 形状匹配化解归属时晋级，逐行披露
    数据侧结构对应（B5-R03 同性质措辞），不写「段位↔槽位位置序对应」；同文多次/方向冲突
    仍一律 hint。执行结果与审计分类 0 错配（若 G2/G3 不能稳定化解归属须停下上报——实测
    形状不符 0/1,425，未触发）。
  - **B5-R01＝方案 A（纯渲染层）**：card.json 不动。
- 生成器改动（全部在 scripts/character_skills/ 本线）：
  - 新模块 `card_page_inference_b6_bossbuff.py`：G1–G7 门控逐行实现（与审计 part4 classify
    同序同因）；家族模板 norm_text/family_of 与批 1 盘点逐字节同法；运行时子记录索引从
    `Inputs.old`（records.jsonl 页记录子集）构建，不重读解码 JSON；slot 从 links
    `boss_skill_refs[].slot` 取；值行经 `R.answer_for('bossskill',13,…)` 同源换算；证据按
    字段（p1/p3/p6→boss_heal 字典＋README；p2→boss_chain/type13_basis 6 件，缺失显式失败）；
    样本域按规则 occurrences 分支披露（None→外推披露；p2 occ=718 按登记口径）。
  - `card_page_data.py`：b6 gate 接入（`table in B6.TABLES and not answers`，批 2–5 表集不相交）、
    promoted/active/evidence_label/hint 注记/coverage 计数器（inference_b6_promoted/hinted）。
    `card_page_policy.py`：INFERENCE_STATUS 增 b6 scope 与 message（五批）。
    `card_page_render_v2.py`：ROW_AUDIT_LABELS 增 `inference_b6`/`inference_b6_hint`；
    `render_audit` 对 rule_status 特判（B5-R01）。`card_page_dbstyle_sample.py` 同步。
    `card_page_batch.py`：aggregate 透传 b6 计数；plan.json inference_layer/permission_boundary
    更新。
- B5 遗留：
  - **B5-R01（方案 A，渲染层）**：`render_audit` 特判显示「规则级状态（规则本体〈原值〉；
    不代表本值归属确认）」（render_v2＋dbstyle_sample 同步）；**card.json 零变化**
    （1,931 既有值行＋本批 5,142 值行均经渲染限定；对账单确认 0 个 R01 引起的数据变化）。
  - **B5-R02（数据层）**：b5 模块 belonging「子记录自文一致性」→「语义一致（非逐字）」＋
    值行 note「链记录正文旁证——语义一致（非逐字）（B5-R02）」；supporterskill 17 行
    card.json 变化，已在对账单列。
  - **B5-R04（数据层）**：sup 17 行×2 值行 conditions 追加「规则级适用范围（本行域外）：…」；
    job 行不变。
- 逐行审核结果：晋级 1,379（bosspattern 615／denju 358／dlb 30／charainfo 经同页同文 pattern
  376；值行 5,142＝每行非 crit 属性数＋时长）＋hint 登记 758（首拍口径：crit 386、charainfo
  继承 175、同记录 fam11/fam13 冲突 36、链缺口 20、不可达 8、同文多 pattern ~130、多 t13 3；
  〔B6-RV-03 更正：最终分类为 crit direct 386、charainfo 多 pattern 240、无 pattern 7、
  冲突 45（36 direct＋9 继承）、链缺口 22（20 direct＋2 继承）、多 t13 3、继承 crit 55；
  30236 charainfo 行属 G5 多 pattern 非「无同文 pattern」；空链 12 行实为 7 denju＋5
  heroicskilllist〕，与审计
  §6 一致）；与审计 fam1_classification.json 逐行决策对账 **0 错配**（含 Y.G. 晋级 83＝83）。
- 对账与复核（`work/character_skills_b6_impl/`，snapshot_old/compare_full_rows/check_receipts
  ＋sample_regression 四脚本实际执行）：
  - 行集合零增删（41,665 两侧一致）；变化行恰 **2,154＝批 6 行集 2,137＋B5 遗留 17**，
    0 增 0 漏、0 个非本批/B5 遗留变化行；既有四批晋级行、30236 基线 A 行、边界行零变化。
  - 指标 old→new：全库 A 14,750→16,129（+1,379）、C 26,915→25,536（−1,379）、原文A 13,859
    不变、整行推断 625→2,004、整行确认 266 不变（N_all 41,665）；Y.G. 109 卡 A 2,731→2,814
    （+83）、C 3,074→2,991（−83）、整行推断 170→253、整行确认 18 不变（N_all 5,805）；
    Y.G. b6 值行 332 条、hint 221 行（行集 304 全覆盖）。
  - 2236/2236 receipt SUCCESS（单一签名）、4472 产物哈希 0 不一致、29/29 数据依赖未变
    （dependency_signature 4029ad13…）、0 stale、4 cohort MATCHING、campaign_complete=true。
  - 新签名 `4c3d51b3637f41d348f0928b92f9b60e4de8bb87700880618850597998a6e92a`；run_id：ge60
    `20261020T125432730434Z-55b00796`、40to59 `20261020T125449025721Z-7a639b4d`、20to39
    `20261020T125549769172Z-b40a7ade`、remaining `20261020T125647982337Z-07ffb70b`。
- 代表样本回归（10 cid＝10001/11004/10210/1264/1266/2289/20510/2320/1285/30236，46 行）：
  0 失败；覆盖 promote/promote_charainfo/crit/多 pattern/多 t13/链缺口/不可达/基线 A 行不动。
- pages/README.md 新增 §18（批 6 节）。未 git 暂存/提交；未改 profiles/原始输入/旧审查报告/
  共享进度文件/HANDOFF。
- 实施过程如实记录：compare_full_rows.py 首轮运行出现「2,137 决策错配」——为对账脚本自身
  cid 类型 bug（审计 JSON cid 为 str、card.json 为 int），非生成器问题；修正后 0 错配。
  生成器本身无返工（首轮全量重建即通过全部对账）。
- 下一步（供排期）：批 8 候选（敵デバフ fam6＋自身バフ fam11，复用本批子记录解析）；
  H3 的 36 行待 fam11/fam13 批一并裁决后复评；crit 承载记录（type52/119 等）原生核实
  独立专项。

---

## 修复轮次（20261020 DeepSeek 批 6 审查 REQUEST_CHANGES → B6-RV-01～04 修复，批 6 修复员）

- 状态：**已完成（四 cohort 全量重建＋对账/复核/全量复扫通过）**
- 审查依据：`output/character_skills/review/inference_b6_bossbuff_20261020_deepseek/`
  （REPORT.md §2；checks/competing_rows.json 30 行）。修复前快照
  `work/character_skills_b6_fix/old_rows.jsonl`（首轮产物 41,665 行，签名 `4c3d51b3…`）。
- **B6-RV-01（High）已修**：按主持先前裁决「归属未化解仍留 hint」，30 行全部降级——
  `card_page_inference_b6_bossbuff.py` G6 扩展 `_competing_ally_buffs()`：父记录正文按「。」
  逐句归一化后匹配「（範囲内の）味方／自身の⟨ATTR-run⟩が一定時間上がる/上がり」竞争短语
  （覆盖「範囲内の味方」独立句与复合句内嵌「自身の…」短语；味方全体 主语视为本句自身排除），
  属性集合与本句相同→hint，原因写明竞争句原文与「唯一 t13 形状同时匹配两句、无已确认规则
  指定接受者、归属不能唯一化解」。降级 30 行（11 cid）＝审查 competing_rows.json 全集
  （0 缺 0 增）。晋级 1,379→**1,349**（bosspattern 602/denju 350/dlb 30/charainfo 367）、
  hint 758→**788**、值行 5,142→**5,044**（p1 1,349/p2 1,279/p3 1,349/p6 1,067）。
- **G6 加固后全量复扫**（`work/character_skills_b6_fix/full_rescan.py`，独立实现——自建
  records.jsonl/links 索引与独立正则，复刻审查 competing_rows 方法，不调用实施模块）：
  1,349 晋级行竞争句命中 **0**；即除已降级 30 行外，剩余晋级行无同属性竞争 ally-buff 句。
- **B6-RV-02（Medium）已修**：`_sample_domain_note()` 的 origin 改按
  `profiles/rules.json` 登记值输出（`bossskill|13|/skillparam2` 登记
  `origin=output/card_comparison_cid30236/field_dictionary.json`；rules.py 合并源条目确无
  origin 键——实测 `R.rule_for('bossskill',13,'/skillparam2')['origin'] is None`）。
  修复后 p2 值行 1,279 条「origin None」残留 **0**（对账实测）。
- **B6-RV-04（Low）已修**：`_promote()` summary/extra 补「正文句序：buff 句位于第 N 句／
  共 M 句（以「。」切分）」＋显式声明「◆段口径不传达句序」；1,349 晋级行披露缺失 0。
  `inference_b6` 元数据增 `sent_no`/`sent_total`（`card_page_data.py` 接线 2 行）。
- **B6-RV-03（Low）已修（文档）**：分母脚注（全库 2,139＝b6 评估 2,137＋30236 两条基线
  A 行；Y.G. 306/304）；hint 分类对齐最终口径（386 crit direct、240 charainfo 多 pattern、
  7 无 pattern、45 冲突＝36 direct＋9 继承、22 链缺口＝20 direct＋2 继承、3 多 t13、
  55 继承 crit；修复后另加竞争句 30）；30236 更正为 G5 多 pattern（43023601/43023602，
  非「无同文 pattern」）；「12 行 denju 无 children」更正为 7 denju＋5 heroicskilllist。
  修改位置：本卡（实施节就地注记＋本节）、`pages/README.md` §18.1/18.2/18.4＋新增 §18.6、
  `inference_inventory/b6_bossbuff_scope.md`（§3.3/§5.5/§6 H4/H5＋终版分类注记）、
  生成器内静态口径文本（`card_page_policy.py` scope、`card_page_batch.py` plan 文案、
  b6 模块 docstring）。
- 修复 old→new 对账（`work/character_skills_b6_fix/compare_fix.py`，逐行多重集 vs 修复前
  快照）：变化行恰 **1,379**＝1,349 仍晋级行（句序＋p2 origin 披露）＋30 降级行
  （A→C、promote→竞争句 hint、值行 −98）；**批外变化行 0**（30236 基线 A 行、既有四批
  晋级行、B5 遗留 17 行、旧 758 hint 行全部零变化）；0 行新增/删除（41,665 两侧一致）；
  newly promoted 0、hint 集合仅 +30（恰为降级行）。
- 指标（修复 old→new）：全库 A 16,129→**16,099**、C 25,536→**25,566**、原文A 13,859 不变、
  整行推断 2,004→**1,974**、整行确认 266 不变（N_all 41,665）；Y.G. **全部不变**（A 2,814、
  C 2,991、原文A 2,543、整行推断 253、整行确认 18，N_all 5,805；降级 30 行经
  characters.csv 核对 0 命中 Y.G.；Y.G. b6 晋级 83、hint 221、值行 332 不变）。
- 重建（`card_page_batch.py --execute --resume`，四 cohort 0 失败 34/290/436/1476）：
  2236/2236 receipt SUCCESS（单一签名）、4,472 产物哈希 0 不一致、29/29 数据依赖未变
  （dependency_signature `4029ad13…` 不变）、0 stale、4 cohort MATCHING_SIGNATURE_SNAPSHOT、
  campaign_complete=true。新签名
  `e096f2cae855d11056fc91a3ae077d1f4f519e6934443378d04d025e7ccc6845`；run_id：ge60
  `20261020T134319764010Z-6a4aa7c1`、40to59 `20261020T134331134797Z-254735b9`、20to39
  `20261020T134431661215Z-63fd0be0`、remaining `20261020T134529352453Z-ef1aef06`。
  分 cohort b6 晋级/hint：ge60 49＋40、40to59 441＋503、20to39 674＋205、remaining 185＋40。
- 代表样本回归复跑（`work/character_skills_b6_impl/sample_regression.py`，10 cid 46 行，
  含 30236/10001）：0 失败；B5-R01/R02/R04 效果保持；30236 基线 A 行不动。
- 修复过程如实记录：首轮重建启动后补改了 `card_page_batch.py`/`card_page_policy.py` 的静态
  口径文案（原写「晋级候选 1,379」）——为保持单一生成签名，中止首轮（仅 ge60 完成）、
  改后重跑全部四 cohort；上述 run_id/签名均为重跑后终值。修复员自查脚本两次因「競争/竞争」
  用字不一致漏计，已修正（不影响产物，仅验证脚本）。
- 未做/遗留：type51/76/84/108 旁证排除竞争句（可能恢复部分降级行）需主持裁决或独立原生
  专项；本修复按「不猜」保守降级。未 git 暂存/提交；未改 profiles/原始输入/旧审查报告/
  共享进度文件/HANDOFF。
