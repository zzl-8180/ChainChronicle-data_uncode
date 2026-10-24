# 批 14：crit-2012 与 1095 的 APK 域外扩域（2012×211＋1095×52 与 223 行晋级）

- 任务 ID：20261022-character-skills-inference-b14-apkext
- 负责：主持 Kimi K3（唯一写入整合者）；实施 GLM 5.3 Flash 260828（high，经 CreateWorkflow 钉模型）；独立审查 DeepSeek V4.1 Flash 1017（high，独立新上下文）
- 状态：**实施完成（2026-10-22，GLM workflow dwfrun-70837560；待 DeepSeek 定向审查）**——晋级 212／留 hint 11／值行 418＝审计投影逐项一致；verify_full 10/10 PASS
- 允许写入：审计期＝`work/character_skills_b14_audit/`、`output/character_skills/inference_inventory/b14_apkext_scope.md`；实施期（另行授权后）＝`scripts/character_skills/`（rules.py 注册函数、b8/b11 推断模块最小改动）、`output/character_skills/profiles/rules.json`（仅经注册函数重建）、`output/character_skills/pages/`（cohort 重建）、`output/character_skills/review/inference_b14_*`（审查目录）、`output/ordinary_effects/ability2012|1095/`（证据增补，若审计升级项成立）
- 共享依赖：`output/character_skills/profiles/rules.json`（2012 param0/4/5 三键、1095 param1/2/3/5/6 五键，现 CACHE 单域）、card_page_inference_b8_crit2012.py、b11_sa1095.py、card_page_verify_full.py、四 cohort 重建入口
- 范围来源：批 13 范围文档（b13_apkext_scope.md）明示「b8 crit-2012 APK 域外＋b11/12 1095 APK 域外各自另行立项」；本卡合并为一批两族（同批 13 双族先例）

## 主持实测定标（2026-10-22，GLM 审计独立复核中）

- 候选 223 行（当前 card.json unknown_reasons 含 carrier-out-of-domain、非批 9/10 族）：196 行 b8 族（inference_b8_hint）＋27 行 b11 族（inference_b11_hint）；行层 145 APK＋78 CACHE（跨层：CACHE 行＋APK 载体）；166 行兼带 inference_b6_hint。
- 载体 113 条全在 APK 主表（`output/base_master/_mdSkill.json`，记录 id 字段＝`skillid`）：86 条 ability2012＋27 条 ability1095；与 CACHE skilllist（`output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw` 的 `skilllist` 键，8,634 条）同号 0 重叠——无批 13 式同号异值风险（全域排查仍属审计项）。
- Y.G. 重叠 0（109 卡清单逐 cid 核对）；本批预期不点亮 Y.G. 行，属 APK 侧存量解锁。
- CACHE 基线：ability2012×406＋ability1095×407，iParam0 全部缺失（与 rules.json limits 注记一致）；APK 域：2012×211（param0/4/5 全存在，param4 79×0.0、param5 80×0.0、param0 10–300）、1095×52（param1 1.02–11.5、param2 1.0–2.25、param3 0.5–1.0、param5 0–0.75 含 15×0.0、param6 1.5–4.0）。
- **iParam0 职业过滤（本批关键新机制）**：86 个 2012 载体中 8 个 iParam0≠0（1×4、2×2、5×2）；1095 载体全 0。示例载体 41100413：param0=20.0、param4=0.15000000596046448、param5=0.0、iParam0=2，行文本「弓使いの味方の場合、クリティカル発生率も一定時間上げる」。审计须给出 iParam0 原生读取语义与职业枚举映射、8 载体逐行文本-职业核对、晋级时条件 chip 接线方案（条件分组披露，不并入基础值）。
- 中性 0.0 槽：param4/param5 存储零＝无效果贡献（getter 加 0），与 CACHE「缺失保持缺失不导出默认0」一致性政策由审计定义；p4/p5 全 0 载体对暴击主张无贡献的行按形状匹配重判，预期部分留 hint。

## 审计期任务（GLM，只读）

载体逐条表→APK 全域键存在数（建议 occurrences_apk）→公式级方向/值域核对（2012 p4 pp 加算 clamp [0,0.5]、p5 系数增量、p0 支持时间；1095 p1 攻击因子、p2 移动因子、p3 受伤量、p5 暴击 pp（APK max 0.75 属 1095 分支非 2012 clamp）、p6 delta=原值−1.5）→受控检查（复用既有反汇编，不开新原生；覆盖性论证不出则记升级项）→iParam0 专项→中性槽政策→门控复检（223 行除 G5 外其他门控是否已过）→同号异值全域排查→晋级预估与零变化对账方案→范围文档。

## 实施期（批 13 审查闭环后，按审计结论派单）

rules.py 注册（预期两域分源 occurrences_apk，照批 13 模板；2012 三键＋1095 五键）→晋级与 hint 替换（inference_b14，0 双登记）→四 cohort 重建→verify_full→DeepSeek 定向审查→进度文件登记。

## 最近更新

- 2026-10-22：审计期完成（结论见下条；`work/character_skills_b14_audit/`、范围文档 `output/character_skills/inference_inventory/b14_apkext_scope.md`）。（`work/character_skills_b14_audit/`、范围文档 `output/character_skills/inference_inventory/b14_apkext_scope.md`）。结论：①晋级投影 **212 行**（2012 族 195/196＋1095 族 17/27）；留 hint 11 行＝b11 族 P4 形状不符 10（sub p6/p5+p6 活性未被句主张，CACHE 域同判、与域无关；11232/12235/20630/20633/20634/20636/20639/20712/20718/6335）＋G6 句无对象词 1（cid2310）。②建议 occurrences_apk（中性口径，存储零不计，与 CACHE 缺失不计同语义）：2012 p0=211/p4=132/p5=131；1095 p1=p2=p3=p6=52、p5=37。③iParam0 专项：读取语义确认（get_iParam0→BtlCharaUtil.CheckJobFlag 成员过滤，既有片段）、职业枚举经 1017/3000 元数据 JobType＋rules.py 既有 decode_job_mask 复用，8 载体×27 行句面职业位集合==解码位集合 27/27；**升级项＝CheckJobFlag 非零分支体（0x13ab388–0x13ab458）不在既有片段窗口，实施期最小新增该片段或 41100413 受控检查**。④中性 0.0 槽＝无贡献（getter 读 0 加 0），不出值行；双 0 载体实测 0、形状失配 0 行。⑤同号异值全域 19 条（15×2012＋4×1095）**均不在 113 载体中**，层局部性成立。⑥门控复检 223 行：212 行全门通过（用 B8/B11 模块自身实现 import 复检防漂移）；G4/G7/G8 0 违例。⑦分桶差异注记：批 13 快照记 184/39、现状实测 196/27（合计 223 不变），系批 13 重建后链解析/hint 分派变化，实施期以逐行门控为准。⑧实施期另须：全域公式核对（2012×211×3＋1095×52×5，批 13 夹具 replay 法）、rules.json 2012 limits「iParam0 均缺失」句限定 CACHE 侧、b8/b11/b12 存量披露刷新（数值零变化）。

## 实施轮完成（2026-10-22，GLM 5.3 Flash 260828 high）

全部以实测为准；与审计投影一致（0 收缩、0 扩张）：

1. **升级项已执行（经主持授权）**：CheckJobFlag 非零分支体（0x13ab388–0x13ab458）自既有
   恢复的原生镜像提取→`output/ordinary_effects/ability2012/checkjobflag_body.txt`＋
   native_checks.json/trace.json 顶层 `b14_extension`＋README b14 节（既有内容未改动；
   无新反汇编来源镜像、未开真机）。语义：iParam0≠0 时逐成员读职业
   （成员+0x28→+0xf8 的 ParamS_int.get_Value）→`lsl w8,1,w0`→`tst w8,w19` 位命中保留、
   未命中 bl 0xa85b64 移出成员列表；职业过滤受控检查 6 项（41100413 mask=2／30322211
   mask=1 的命中/未命中/混合成员）全过；0xa85b64/0x1eb8358 无元数据方法名（按控制流
   判读＋行为验证，如实披露）。41100413 端到端受控检查以扩展夹具（成员 ParamS_int
   职业值＋List.Remove 集合模型）实现，并入全域 replay（ iParam0≠0×16 条记录全覆盖）。
2. **全域公式核对 0 违例**：2012×211×3 键（SupportGuest/action_case 逐条 replay，提交值
   float32 回舍断言）＋1095×52×5 键（批 12 同法五窗口：p1/p3 LocalGuest、p2 walk、p5
   chance、p6 damage）；边界记录 4＋3 条（40033812/41100413/40322511/40429211；
   40034001/41123201/40033901）。落盘：2012 侧 ability2012/b14_extension；1095 侧
   `work/character_skills_b14_impl/b14_apk_checks_1095.json`（ability1095 目录不在本批
   写入边界，未合并，整合者可按需合并）。
3. **rules.py 注册＋rules.json 重建**：`_b14_apkext_domain_update()`（照批 13 模板）——
   2012 三键＋1095 五键获 `occurrences_apk`（211/132/131；52/52/52/37/52，中性口径与建议
   一致）、conditions 两域分源措辞（同号 15＋4 清单披露、中性口径说明、iParam0 双侧注记
   ——旧「iParam0 均缺失」句限定 CACHE 侧、不删史）、limits 批 14 注记（含 CheckJobFlag
   升级项路径）；occurrences/status/evidence/conversion 不变。**B13-R02b 随同重建**：
   42030603 多写「-0.15」删除、2003 四组改逐组元组（恰九键 conditions 变化）。diff 恰
   17 键、其余 265 键逐字节不变（`regen_rules_b14.py` 断言）；SHA `cc7da2d2…`→
   `8bb01b77…`（字节 341,281→359,932）。
4. **晋级 212 行**：B8 G5 域门/B11 P2 域门委托新模块
   `card_page_inference_b14_apkext.py`（`handle_2012_apk`/`handle_1095_apk`，同门同序、
   值行政策与批 8/12 parity——2012 侧 p4 pp/p5 系数增量、不出 p0 时长值行；1095 侧
   p1/p2/p3/p5/p6 按句主张活性槽、p5 直接加算/p6 delta=原值−1.5）；行级键
   `inference_b14`、evidence_scope=TEMPLATE_BATCH14_APKEXT、replaces_hint 溯源
   （inference_b8_hint 195＋inference_b11_hint 17），0 双登记；166 行批 6 让渡注记随晋级
   行级替换（b6_hinted 788→622 恰 −166，原注记记入 b6_yield_note_replaced）；78 跨层行
   按载体层归类逐行披露；值行按 rule_key 分布与审计投影逐键一致（p4×184/p5×164/p1×17/
   p2×17/p3×17/p5×17/p6×2＝418）。
5. **iParam0 条件接线（27 行）**：值行带结构化 `condition_label`＝句面条件短语逐字
   （戦士 13／弓使い 10／戦士と魔法使い 4——实测），首屏条件分组（批 4 chip_groups 先例，
   不并入基础值）；note 双源披露（rules.py 既有 decode_job_mask＋CheckJobFlag 片段语义）；
   27/27 句面职业位==解码位断言入 B14 门（不符留 hint 不硬猜）。
6. **b13 遗留并入**：R02b（见 3）；R01b-residual——`card_page_inference_b9_debuff.py`
   `_debuff_clause` frag 侧应用同一 `(?<!属性)` 负向断言，only-shrink 全语料回归
   （41,665 行：缩小 15/相等 41,650/增大 0）＋已晋级行 0 翻转实测（b9/b10/b13 共 552 行
   metadata.attrs 与新口径重算逐一相等；`work/character_skills_b14_impl/
   b9_frag_regression.json`）；RC-INFO-02——交集非空门超集保守残留注记
   →pages/README.md §27.4。
7. **存量披露刷新（数值零变化）**：b8 已晋级 346 行 conditions/limits 快照＋
   `_sample_domain_note` 两域分源句；b11 34＋b12 94 行「APK 52 条同构已核但域外未分配」
   过时短语刷新为已分配口径；b13 278＋b9 35＋b10 239 行 conditions 字段随 R02b 九键
   conditions 刷新（对账口径沿用：行级披露变化单列、forward_links 非 row 级 groups 文本
   变化单列）。
8. **重建与验证**：四 cohort 全量 `--execute`（无 resume）0 失败 0 复用（终轮 runs：
   ge60 `20261022T041305800261Z-b69812d5`、40to59 `…7ac9937d`、20to39 `…2a835734`、
   remaining/campaign `20261022T041519353046Z-76f27187`；签名 `546a170b…`、source
   `aeef7542…`、dependency `4817aa51…`——rules.json 17 键变化随动）。接线中间轮一次
   （b11 侧 b14 元数据缺 carrier_record_id 键，17 卡 FAILED）修复后终轮全量再生成取代，
   无混合 run。`card_page_index.py --execute`（EXPECTED_CAMPAIGN→A 17,443/C 24,222/
   推断 3,318；entry CURRENT）；`card_page_verify_full.py` **10/10 PASS**（receipt
   2,236/2,236、哈希 4,472/4,472、29 依赖、行 41,665、source 解引用 69,891、值相等
   10,676＝+418、chip 41,665、campaign 对账 inference_b14_promoted=212、入口页）。
9. **指标（实测，与投影一致）**：A 17,231→**17,443**（+212，41.9%）、C 24,434→**24,222**
   （−212）、整行推断 3,106→**3,318**、整行确认 **266**、原文A **13,859** 不变；
   **Y.G. 609/108/30 与阶段 331/100/25 不变**（本批 Y.G. 0；yg A/B 行 3,170→3,170）；推断
   答案（quantitative 值行）+418。对账（`reconcile_b14.py`）：变化行恰 **1,249＝212 晋级
   （C→A）＋11 hint 改写（C→C）＋1,026 存量披露刷新（b8 346＋b11 34＋b12 94＋b13 278＋
   b9 35＋b10 239）**；OUTSIDE 0；非晋级行值字段 0 变化；30236 行/值 0 变化（页面文本随
   forward_links conditions 刷新非逐字节零变化，如实披露；基线目录零触碰）。
10. 留 hint 11 行（理由改写为实际门）：P4 形状不符×10（11232/12235/20630/20633/20634/
    20636/20639/20712/20718/6335——sub p6 或 p5+p6 活性未被句主张）＋G6 句无对象词×1
    （2310-…-pattern1-lvorder1-f0）；hint 键不变（inference_b11_hint/inference_b8_hint）。
    未实机；APK 装载路径仍无原生核实——行保持推断。产物：`work/character_skills_b14_impl/`
    （b14_apk_checks.py＋_1095.json＋b14_apk_extension.json、regen_rules_b14.py、
    b9_frag_regression.py/.json、snapshot_pages.py＋pages_before_b14.json、reconcile_b14.py/
    .json、smoke_b14.py）；pages/README.md §27。
