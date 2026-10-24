# 任务卡：批 13 APK 域外扩域（ability99 ×199、ability2003 ×148）——前置审计（纯分析）

- 任务 ID：20261022-character-skills-inference-b13-apkext
- 负责人：批13APK审计员（GLM 5.3 Flash 260828，workflow 子代理，单 ask）
- 状态：**前置审计已完成；实施批已完成（同日，见文末实施节：rules.json 九键扩域＋晋级 276/hint 10＋四 cohort 重建＋verify_full 10/10 PASS）**
- 日期：2026-10-22
- 上游：批 9 遗留第 2 项（APK 99×199 域外）、批 10 遗留第 3 项（APK 148 条 2003 域＋192 行 hint 扩域另立小步）

## 目标

评估把 `skilllist|99`（4 键）与 `skilllist|2003`（5 键）的样本域从「当前 v3 CACHE」扩为「CACHE＋APK 主表双域」的可行性；APK 记录同构复核（199＋148 全量）、occurrences 双域登记形态、94＋192 行候选分类、代表样本核对、实施批范围设计。

## 允许写入范围（本轮实际写入）

- `work/character_skills_b13_apkext/`（3 脚本＋4 中间数据：`scan_apkext_inventory.py`/`inventory_apkext.json`/`ood_hint_rows_current.json`/`classify_ext_rows.py`/`ext_rows_classified.json`/`audit_samples_b13.py`/`b13_samples.json`，全可复跑）
- `output/character_skills/inference_inventory/b13_apkext_scope.md`
- 本任务卡

## 关键结论（详见 scope §1–§5）

1. **可闭合（2003 即时／99 差一步）**：APK 99×199／2003×148 全量分布复核 **0 方向反例**（p7≤0/p8≤0/p9≥0）；2003 处理器证据已含 APK 记录受控实测（31222712、50009，批 10 native_checks），扩域只差全域公式核对；**99 处理器证据未含 APK 记录→需最小新增**（≥2 条 APK 记录受控检查＋两型全域公式核对，复用批 12 方法，无新反汇编）。
2. **两域同号 5＋5 条记录参数值不同**（99：42030603 p7 -0.2/-0.15 等；2003：42013112 等）——命名空间真实分歧，**不得合并/跨层取值**；5＋5 号均非候选行载体（候选载体与 CACHE skilllist 全表 **0 交集**）。
3. APK 特有形态：2003 p3=0.15×1（50009，恰为候选载体，句面「一定確率で」形状一致）；99 分数阈值 23 条（p1/p2/p3 无规则键、登记不分配）＋**p0=0×3**（17547/25510/28053，语义未核，非候选载体）；p0 新正值 4.5–120（正值=秒语义同）。
4. **触发限定词↔阈值组合逐行一致**（通常攻撃時/クリティカル攻撃時/必殺技攻撃時/一定確率で，数据侧强对应）：PROMOTABLE 278 行 0 违例；14 处违例全在 8 行 multi-carrier。
5. **候选行集**：99 侧 94 行＝PROMOTABLE **86**＋multi-carrier **8**（双 99 载体值不同→留守）；2003 侧 **192 全 PROMOTABLE**（**跨层 63 行：CACHE 层行＋APK 载体，按载体层域归类**）。值行 ≈**826**（99：178 槽＋57 时长；2003：416 槽＋175 时长）。**Y.G. ＋0**（候选集 Y.G. 0 行，实测）。
6. **登记形态**：单键保留、新增 `occurrences_apk`（APK 存在数）；不拆双键（convert 按 effect_type 分派、行侧 rule_for 无层参数）。99 p8 CACHE 侧保持已核 ID 数口径 1，APK 侧 82 存在数口径不同须 limits 注明。

## 下一步（实施批建议）

1. 前置：99 处理器 ≥2 条 APK 记录受控检查＋99/2003 APK 全域公式核对（batch 12 方法）。
2. rules.json：九键加 `occurrences_apk`＋conditions/limits 双域措辞（scope §2.2 原文可用）；regen diff 证明（批 10/12 先例）。
3. 278 行晋级：行级键 `inference_b13`、evidence_scope=`TEMPLATE_BATCH13_APKEXT`、replaces_hint 溯源防双登记；8 行 multi-carrier 维持 hint。
4. 2290 属性门行、b8 crit-2012 域外 184 行、b11/12 1095 域外 39 行不属本批。

## 共享依赖（只读）

- `output/character_skills/profiles/{rules.json,characters.csv}`、`output/character_skills/pages/*/card.json`
- `output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw`、`output/base_master/_mdSkill.json`（分源，不混用）
- `work/character_skills_b9_debuff/debuff_rows_classified.json`、`work/character_skills_b10_sa2003/{c1_promotion.json,inventory_2003.json}`
- 既有证据：`output/ordinary_effects/ability2003/`（含 APK 记录受控检查）、`output/ordinary_effects/ability99/`、`output/card_comparison_cid30236/timed_support/`

## 最近更新

- 2026-10-22：前置审计完成，产出 scope/work 数据/任务卡；未 git 暂存、未改 rules.json/pages/生成器。

---

## 实施节（2026-10-22，批13实施员 GLM 5.3 Flash 260828，workflow 子代理）

- 状态：**实施已完成**（rules.json 九键扩域＋286 行按载体层域晋级/留守＋四 cohort 全量重建＋verify_full 10/10 PASS）
- 前置：audit 结论为可闭合（99 需最小新增）→ 按方案执行。

### 实施内容

1. **最小新增证据**（`work/character_skills_b13_impl_apkext/b13_apk_checks.py`，复用批 9/10 夹具 DrainGuest/SAGuest，无新反汇编、未实机）：
   - 99 处理器（OnAttackAbilityPowerDrain@0x1121be0）2 条 APK 记录受控检查 6 项：31020502 全路 (1,1,1) 三路接受；31221605 分数阈值 p1=0.2——draw 0.5 拒绝（0 提交、恰 1 次 draw）、draw 0.1 接受、Skill 路 (p3=1) 接受；提交字段映射（目标侧 attack=param7/incoming=param9、自身侧 param4/param6、param0 计时）逐项断言。
   - 全域公式核对：99 APK 199 条×3 路＝597 项、2003 APK 148 条×Skill 路＝148 项（147 触发＋50009 draw0.5 拒绝；另 50009 draw0.1 接受例）——**0 失败、0 方向违例**。
   - **落地披露（写入边界）**：结果落 `work/character_skills_b13_impl_apkext/b13_apk_checks_{99,2003}.json`＋`b13_apk_extension.json`；`output/ordinary_effects/ability99|2003/` 不在本批写入范围、**未合并**既有 native_checks.json（整合者可按需合并）；rules.json limits 内按 work/ 路径如实引用。
2. **rules.json 九键扩域**（`scripts/character_skills/rules.py` `_b13_apkext_domain_update()`，99/2003 键处；regen：`work/character_skills_b13_impl_apkext/regen_rules_b13.py`）：
   - 新增 `occurrences_apk`（APK 存在数）：99＝196/157/82/162、2003＝148/148/114/75/140（实测断言）；`occurrences`（CACHE 存在数）不变；不拆双键。
   - conditions 改两域分源措辞（scope §2.2 全文；同号 5＋5 清单、不得跨层读取）；limits 追加批 13 注记（旧 CACHE 单域口径移注记保留）；status/evidence/conversion/origin/occurrences 不变。
   - diff 证明：282 键其余 273 键逐字节断言不变（含批 12 的 1095 三键、批 10 的 2003 注册前键）；九键内恰 {conditions,limits,occurrences_apk} 变化；SHA `9f1009f4…`→`cddd0a22…`；`rules_diff_b13.py` 逆向重建旧文件 SHA 一致＋`rules_diff_b13.txt` 逐键 diff。
3. **晋级实施**（`scripts/character_skills/card_page_inference_b13_apkext.py` 新模块；批 9/10 载体域门扩展委托 B13——B9.evaluate 的 `apk99 and not c99` 出口→`handle_99_apk`、B10.evaluate 的 P2 域门→`handle_2003_apk`）：
   - 门控与批 9/10 同门同序（P4 形状双向/P5 方向按符号/P4b 竞争句/P6 跨 cid 守卫，仅样本域换扩后两域）；多载体→hint 双侧值。
   - **实测晋级 276 行**（audit PROMOTABLE 278−2）：99 侧 84＋2003 侧 192（跨层 63 行按载体层域归类，逐行披露「载体来自 APK 主表、行在 CACHE 层」；APK/APK 213 行）；2 行收缩（13029-…-f0、2290-…-f1 落批 9 P4b 竞争句门——audit 分类器未建模该门，留 hint 写明阻塞，audit §5.5 预告情形）。
   - **hint 10 行**＝8 multi-carrier（双侧值披露）＋2 P4b；行级键 `inference_b13_hint` 行级替换旧 b9/b10 hint（不双登记，对账 0）。
   - 行级键 `inference_b13`（replaces_hint 溯源：99 侧→inference_b9_hint、2003 侧→inference_b10_hint）、evidence_scope=TEMPLATE_BATCH13_APKEXT、行级标注「推断（模板批 13 APK 扩域）」；披露区分「规则本体已确认（样本域扩至 CACHE+APK）」与「本条归属推断」；值行 820（99：p7 71/p9 75/p8 28/时长 55；2003：p7 143/p9 186/p8 87/时长 175）。
4. **接线**：card_page_data.py（B13 evaluate 接入＋promoted_b13 分支＋hint 路由＋coverage 计数）、card_page_batch.py（aggregate＋plan 文案）、card_page_policy.py（b13 scope＋message 十二批）、card_page_verify_full.py（aggregate）、card_page_index.py（EXPECTED_CAMPAIGN 基线 A 17,229/C 24,436/推断 3,104）。

### 指标（old→new；分母 N_all 41,665 不变）

- A 16,953→**17,229**（＋276，41.35%）；C 24,712→**24,436**（−276）；原文A 13,859 不变；整行推断 2,828→**3,104**；整行确认 **266 不变**（记录级 18＋类型外推 248）；partial_A 16,586→16,862；值行＋820（verify 值相等 9,432→10,252）。
- **Y.G. ＋0**（净新增 0 行/受益卡 0/唯一 NFKC 正文新增 0；累计 609 行/108 卡/30 文不变；阶段批 8–13 331 行/100 卡/25 文不变）。
- 批 1–12 计数零变化（b9 35/323〔−94 恰 APK 域外行〕、b10 239/90〔−192〕、b11 34/312、b12 94）；30236 基线零触碰；old→new 行级变化恰 286（276 晋级＋10 hint 键替换）＋274 行 rules.json 相连披露文本（批 9/10 CACHE 载体行样本域句刷新）＋全卡 implementation_status 文案。

### 重建与验证（本轮实际执行）

- 终轮四 cohort `--execute` 全量再生成（receipt run_id 与终轮一致）：ge60 `20261022T021054804445Z-0c37c36c`、40to59 `20261022T021106999360Z-d353bdbf`、20to39 `20261022T021209519668Z-78a93a25`、remaining/campaign `20261022T021307330971Z-bb6baff2`；签名 `62aeebfa…`（source_signature `70ab68d4…`、dependency_signature `dc21cbcd…` 均因本批变化而更新）。均 0 失败。
- `card_page_index.py --execute`：入口页刷新（entry_pages CURRENT）。
- `card_page_verify_full.py`：**10/10 PASS**（receipt 2,236/2,236、哈希 4,472/4,472、29 依赖、行 41,665、source 解引用 69,467、值相等 10,252、chip 41,665、campaign 对账、入口页）。
- 中间轮如实记录：接线初建轮（b13_ext 行级标记缺失→86/10205 等先行行误写 inference_b10 键）已修复并终轮全量再生成覆盖；曾出现 receipt run_id 不一致（6 张烟雾卡＋index.py 基线编辑改 source_signature 导致 ge60/40to59 签名过期）→ 终轮 no-resume 全量再生成消除。

### 边界与保留

- 未实机、无新反汇编；引擎侧行→载体装载路径无原生核实，行保持推断。
- 留守：8 multi-carrier＋2 P4b（13029/2290）；2290 属性门口径由 P4b 竞争句门兜底维持不晋级（批 9 修正节 P1/B1 语义同向）。
- 不属本批：b8 crit-2012 域外 184 行、b11/12 1095 域外 39 行（另行立项）；批 13 受控检查合并进 output/ordinary_effects/* 由整合者定。
- 未 git 暂存/提交；pages/README.md 已增 §26。

## 最近更新

- 2026-10-22：前置审计完成；同日实施批完成（本节）。

---

## 修复轮节（2026-10-22，批13修复员 GLM 5.3 Flash 260828，workflow 子代理）

- 状态：**修复轮已完成**（DeepSeek 定向审查 `inference_b13_apkext_20261022_deepseek`
  REQUEST_CHANGES：R01 High＋R02/R03/R04 Low＋R05/R06 Info 全部处置；四 cohort 最终
  全量重建＋verify_full 10/10 PASS＋零变化对账 RECONCILE OK）
- R01（High）：P4b 检测器修复（NFKC 双侧规范化 R01a＋属性词边界感知 R01b，
  `card_page_inference_b9_debuff.py` `_competing_debuff_sentences`/`_norm_text`/
  `_sentence_attrs`）；13029/2290 重评晋级（+2 行/+6 值行），行级 `p4b_fix_round`
  provenance 记修复轮；已晋级行 0 翻转（重建 diff 实测）。
- R02：rules.json 九键 conditions 同号措辞精确化（7 组真实分歧＋3 组仅表示差，逐组
  实测分列；`work/character_skills_b13_fix/regen_rules_b13fix.py`；273 键逐字节不变；
  SHA `cddd0a22…`→`cc7da2d2…`）。
- R03：multi-carrier hint 文案逐载体阈值组合列示＋214 句面/路由不符披露（判定不变）。
- R04：对账口径扩展——237 卡非行级 forward_links 披露文本（本轮 8,484 leaf 全
  conditions）与 30236（行级/值 0 变化、页面文本刷新）显式列账。
- R05/R06：简报矛盾与 evidence 基准混用在 scope.md §7 补注（不改产物）。
- 指标（实测）：A 17,231/C 24,434/整行推断 3,106/确认 266/原文A 13,859；晋级 278 行/
  826 值行；Y.G. 609/108/30 不变；b9 35/323、b10 239/90、b11 34/312、b12 94 不变。
- 最终 run：ge60 `…Z-c0d5e609`、40to59 `…Z-86b56282`、20to39 `…Z-f96d8463`、
  remaining/campaign `20261022T031646571545Z-9b83c7bb`；source_signature `45a61418…`、
  dependency_signature `4341b5fe…`、campaign 签名 `8f6732fa…`。明细见
  `output/character_skills/pages/README.md` §26.5 与
  `output/character_skills/inference_inventory/b13_apkext_scope.md` §7。
- 边界：未实机、无新反汇编；未 git 操作；未触碰批 14 审计文件
  （work/character_skills_b14_audit/、inference_inventory/b14_apkext_scope.md）与
  b8/b11 族 hint 行（计数实测零变化）。

## 最近更新

- 2026-10-22：前置审计完成；同日实施批完成；同日修复轮完成（本节）。
