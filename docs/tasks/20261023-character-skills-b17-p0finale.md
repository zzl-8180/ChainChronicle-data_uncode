# 任务卡：批 17 P0 断点收尾（20261023-character-skills-b17-p0finale）

- 状态：**完成**（2026-10-23，批17实施员 GLM 5.3 Flash 260828，workflow 子代理）
- 上游：批 16 审计（`output/character_skills/inference_inventory/b16_backlog_audit_scope.md`）
  ＋主持 D1 级裁决（H2 时长槽共享方案①）
- 范围文档（终态明细）：`output/character_skills/inference_inventory/b17_p0finale_scope.md`

## 目标

P0 断点 182 项清零：三族规则改动一次落地（H1 槽位分区 31 行／H2 时长槽共享 27 行／
多 t13 denju patternid 映射 20510）＋P2 溢出（45+30 行）逐行复验＋登记债务
DS-GR-R1b（30230 对象标签）与 B14-L02（rules.json 19 条同号清单措辞）随批处置。

## 允许写入与实际写入

| 位置 | 内容 |
|---|---|
| `scripts/character_skills/card_page_inference_b17_p0finale.py` | 新建（四路径 evaluate；行级键 inference_b17/_hint，replaces_hint 不双登记） |
| `scripts/character_skills/card_page_data.py` | b17 调用点＋promoted_b17 分支（answers/keys/reasons）＋coverage 计数 |
| `scripts/character_skills/card_page_batch.py` | aggregate b17 键＋plan.inference_layer/permission_boundary 文案 |
| `scripts/character_skills/card_page_verify_full.py` | aggregate b17 键＋`_r1_clause_object` R1b 复刻同步 |
| `scripts/character_skills/card_page_render_v2.py` | b17 键审计标签＋未解决区候选段分支 |
| `scripts/character_skills/card_page_policy.py` | INFERENCE_STATUS 批 17 条目＋message 十七批 |
| `scripts/character_skills/rules.py` | 仅 B14-L02：`_b14_apkext_domain_update` domain2012/domain1095 逐组元组措辞 |
| `scripts/character_skills/effect_ledger.py` | DS-GR-R1b `_clause_object`＋b17 hint blocker/next_step |
| `output/character_skills/profiles/rules.json` | 经 regen 脚本：8 键恰 conditions；其余 274 键逐字节不变（SHA 8bb01b77→57a14d29） |
| `output/character_skills/pages/`、`effect_ledger/` | 四 cohort 重建＋账本重建＋入口页＋§28 |
| `work/character_skills_b17_impl/` | 干跑/快照/对账/regen/A7 结果/replay |
| `work/character_skills_yg_priority/` | 选题链随动重跑（三个脚本输出刷新） |
| `output/character_skills/inference_inventory/b17_p0finale_scope.md` | 本批范围/终态文档 |

未触碰：30236 基线（对账 0 差异）、批 8/14/15 既有答案（丢失 0）、
`docs/tasks/character-skills-progress.md`（主持维护）、旧审查报告、git（未操作）。

## 终态（实测）

- P0 182→**0**（backlog 78,237→77,950；未解决效果 51,803→51,516；有答案 15,885→16,172；
  完整 4,224→4,289；断点行 59→0）；新增答案 287/丢失 0/行集合变化 0。
- 晋级 92 行＝H1 31＋H2 27＋20510 1＋P2 溢出 33（44 行 P2 留守 hint 不变；
  33＋44＝77＝75 行 fam/compet＋2 行多 t13——B17-R03 更正，原稿 75 分母把
  2320/10210 两行多 t13 重复计入致「42 留守」误记）。
- H2 27 行未解决清零、仍拆分待核查（S3 条件子句，诚实保留）；H1 31＋20510＋P2 33 → 完整。
- campaign 签名 `c46066745b97…`（A 17,476/C 24,189/整行推断 3,351；EXPECTED_CAMPAIGN
  首轮预测 3410 误、重建实测后更正并整轮重跑统一签名）；verify_full **15/15 PASS**；
  A7 回归 **16/16 PASS**（新增 5 用例）；签名按当前代码重算一致（47 个 card_page*.py
  源文件入 source_signature）。
- 独立目录复跑：4,472 个卡产物逐字节一致＋campaign 签名/coverage/summary 相等＋
  入口页 run_id 归一后一致（replay 沙箱无 art/ 目录导致 icon 计数差异，junction 后消除）。

## 下一步（移交主持/后续批次）

- 批 18（裸 crit 成对＋时长混句，上限 2,218）／批 19（マナ族）按批 16 批序建议；
- H2 27 行 S3 条件子句留待后续；20510/2320/10210 的 charainfo 行**无多 t13 待办**
  （f1 已由批 8/15／批 6 以同一 t13 出 6/4/4 答案，与本批 denju 选中 t13 同值；
  全库无「个 type13 子记录」b6 hint 存量——B17-R05 更正，原稿「仍 b6 hint 留守」
  与现状不符）。
- P2 溢出 44 行留守（30 行同属性竞争句＋14 行 fam 句——竞争句映射槽与本行相交）
  与 b6 其余 hint 315 行不动（B17-R03 更正：原记 42；33 晋级＋44 留守＝77）。

## 修复轮（2026-10-23，DeepSeek 审查 B17-R01…R09 处置；实施员 GLM 5.3 Flash 260828）

- **R01（medium）**：`_value_row` 新增 object_desc 参数——H2 27 行值行注记改为
  「条件「弓使いの味方の場合」等句面条件逐字短语／对象「弓使いの味方」为句面依据」
  （与行级 subject「味方（条件句）」一致），不再写「味方全体」；27/27 逐行核对
  （`work/character_skills_b17_impl/check_b17fix_rows.py`：R01 bad 0）。
- **R02（medium）**：`_sent_attrs` 增加注记补全词 `_ATTR_NOTE_EXTRA`（通常攻撃威力/
  攻撃間隔/攻撃速度，B6._ATTRS 内、_ATTR_DETECT 外；「効果」泛称不入）——H1 62 行
  时长论证注记竞争句属性逐字写出「属性主张（攻撃速度）」，并明示「词表外属性逐字披露、
  不进映射——∅ 映射语义不变」；mapped 只按 ATTR_PARAM，门判定零变化（干跑实测：
  值/键/门 0 变化）；62/62 逐行核对（R02 bad 0；「属性主张（（无））」叠词同时消除）。
- **R03（medium）**：P2 留守 42→44（30＋14）；账目改为 33 晋级＋44 留守＝77
  （75 行 fam/compet＋2 行多 t13；原稿 75 分母把 2320/10210 重复计入）——本卡、
  b17 范围文档、b16 范围文档同步更正。
- **R04（low）**：H1 P0 Y.G. 更正为 24 行/12 卡（30002/30101/30202/30221/30229/30238/
  30239/30243/30318/30324/30325/30336），H2 为 0；b16 范围文档「占 21（另 3 行 H2）」
  更正；P2 晋级 Y.G. 17 行不变。
- **R05（low）**：charainfo 多 t13 范围陈述更正——全库无「个 type13 子记录」b6 hint
  存量；20510 charainfo f1 已 6 答案（批 8/15）、2320/10210 f1 已 4 答案（批 6），
  与本批 denju 选中 t13 同值；「同法可解性未测」仅指无此形态存量可测（本卡与两份
  范围文档同步）。
- **R06（low）**：H2 charainfo 行注记补「兄弟 FAM1 行晋级为 pattern 级（同页同文
  bosspattern 记录链）；同 skilltext 的 charainfo 兄弟行实测 0 答案仍 hint（批 6 门：
  同文对应 2 个 pattern 记录…）」——运行时对兄弟 charainfo 行真实重放 B6.evaluate
  动态生成（7 行 charainfo H2 全部带披露；7623/7624 实测兄弟行已晋级、5 行实测仍 hint，
  逐行如实，不硬编码）。
- **R07（low）**：`_run_multi` crit_promotion 为 None 时调用 `_sent_pos(wb, frag)` 补
  句序/段位——2320/10210 注记改为「正文句序：本句位于第 2 句／共 3 句」（3/3 multi 行
  逐行核对）。
- **R08（low）**：汇总标签去叠词/嵌套——「（H1 槽位分区：槽位分区）」→「（H1 槽位分区）」、
  P2 标签「P2 溢出：fam 竞争句槽位分区」（不再嵌套括号）、multi 汇总不再追加重复 child
  （父链末位即链 t13）；全库「属性主张（（无））」/「槽位分区：槽位分区」零残留。
- **R09（low）**：B14-L02 前 rules.json 留档重建——等价法：从批 15 时代页面副本
  （`work/character_skills_goal_rectification/union_build/*/card.json`，嵌 B14-L02 前
  conditions）提取 7 键 pre-L02 conditions＋2012 param0＝param4 同文补第 8 键，逐键断言
  同号清单段外逐字节相等后落盘 `work/character_skills_b17_impl/rules_before_b14l02.json`
  ——**SHA-256 `8bb01b772e7bcef9…` 与批 17 前文件字节级命中**（恰 8 键、每键恰
  conditions 字段差异；逐键 diff 证明 `rules_before_b14l02_proof.json`；当前 rules.json
  全程零触碰，复验 SHA `57a14d29a773f3b7` 不变）。重建脚本
  `recover_rules_before_b14l02.py`——274 键逐字节不变从此可从留档文件独立重放。
- **重建与验证（全部实测）**：干跑（全库 2,236 卡内存 build vs 修复前 pages）＝值字段
  新增/删除 0、行级键变化 0、row_class/evidence_label 变化 0、conditions 变化 0、注记
  变化恰 92 行（全为 inference_b17 行）、30236 零变化；代码定稿后四 cohort 单轮
  --execute 不 resume（34/290/436/1476，0 failed/0 reused）→ campaign 签名
  `598ec4f8…`（coverage 计数零变化：b17 92/0、b6_hinted 315、b15_hinted 0、b8 0、
  b14 17、A 17,476/C 24,189/整行推断 3,351）→ ledger 重建（9 checks 全过；rows/
  descriptions/effects/backlog 四对象与修复前逐值相等：完整 4,289/部分 400/未解析
  10,542/拆分 26,434、有答案 16,172/未解决 51,516/NA 299、backlog 77,950；仅快照
  锚点 campaign 签名随动 `598ec4f8`＋rules `57a14d29` 不变）→ 入口页 --execute
  （自检过、entry_pages CURRENT）→ regen_readme28（§28 与 metrics 逐项相等）→
  verify_full **15/15 PASS**（值相等 12,799、页面↔账本 mismatches 0、
  r1_object_violations 0；报告 `work/character_skills_b17_impl/verify_full_b17fix.json`）
  → A7 回归 **16/16 PASS** → 独立目录复跑（replay2：四 cohort 0 failed/0 reused，
  4,472 个 card.json/index.html 与正式 pages 逐字节一致、campaign 签名相等；30236
  card.json 逐字节一致）→ ledger 独立复跑（backlog.json 逐字节一致；ledger.jsonl 仅
  input_snapshot 快照锚点字段差——replay 目录无入口页致 campaign 签名 None，内容行
  109,652 行零差异）→ 修复前后磁盘快照对账（`post_b17fix_diff.json`）：值字段 0、
  行级键 0、行元数据 0、b17 注记恰 92 行、非 b17 注记 0、30236 零变化。
