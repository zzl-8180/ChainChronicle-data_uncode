# C20 候选正式独立审查提示词（DeepSeek V4 Pro GA high）

请以 `new-provider/deepseek-v4-pro-ga-260813`、high，在独立上下文中对《锁链战记》C20 两批候选做正式独立审查。不要沿用实施者或主持的结论，不要把当前 Flash 预审查当成本正式门。

## 写域与停止点

项目根：`E:\代码项目\锁链战记数据解包`。

只写 `output/character_skills/review/c20_attack_candidates_20261108_deepseek/` 与自己的 `work/c20_attack_candidates_review/`。至少交付 `REPORT.md`、`verdict.json`、`evidence.json`、可重跑 `run_review.py` 和逐项台账。其他文件只读；不得修改实施代码、共享 `card_page_data.py`、rules、effect_ledger、正式pages、候选文件或历史报告。

不运行正式全库生成、resume、清理、Git、发布、新原生、实机或新缓存。共享 `card_page_data.py` 必须仍为 C19 终点 `c1334ca6b621fe282d69a3c6793e356ee06f768fec08db7133e97e0fbc50d252`；若已含C20接线，停止并报告。独审无阻断前主持不会接线。

## 读取入口

1. `AGENTS.md`、`docs/角色技能完整解读实施方案.md`、C20四张任务卡及方向评估。
2. `output/character_skills/c20_p1_yg_direct_damage_20261108/` 与 `c20_p2_nonyg_direct_damage_20261108/` 的 README、candidates、exclusions、check_result、run_record、check_candidate.py。
3. `scripts/character_skills/card_page_inference_c20_direct_damage_common.py`、两个P1/P2模块、`check_c20_candidate.py`。
4. 当前正式 `pages/<cid>/card.json`、`profiles/rules.json`、`effect_ledger/ledger.jsonl` 与 `effect_ledger.py` 的G1-B1和精确变体消费段。
5. R01整改与定向复核：`output/character_skills/rectification_c20_r01_20261108/README.md`、`output/character_skills/review/c20_candidates_pre_review_r01_recheck_20261108_deepseek_flash/REPORT.md`。原REQUEST_CHANGES保留，不能把预审查当正式门。
6. 原始CACHE `decoded/{charainfo,bossinfo}.data5.json.raw`、APK `_mdCharacter.json`、`_mdBossInfo.json`；Web材料只作补证，不得代替原表重导。

冻结身份：共用实现 `83210ca766c194d5ba8a5255e75fa9fd06ee4be6cb27767b0573e2a2d187eedb`；P1 `b4ff0997c1857331ce2a5ae76244e80155a6a00a765d640c509885416533fd76`；P2 `5788d6698f315bef0d16adb661e2f724b261b0fd7ef4daa70d4a58ca463b86f8`；检查器 `9b6cd8d188225a29eecd065d4f8203c382ab0910af48fa18aa5c3b72f245c10e`。候选与检查哈希见两批README，任何变化须重新冻结和审查，不得静默沿用。

## 必须独立核查

### A. 全量18效果25答案

- 当前基线campaign `99bee2a166e5ec5f9c03ac97b555d4ada2f6f30d1535258add16bc64c7227c66`、snapshot `99bee2a1-cf9451c6ff47fcfb`、rules294。18个目标effect必须在基线为unresolved，类型为 `ダメージ（词表外）`。
- 逐字核row_id、effect_id、日文、fragment span、source层与source pointer。独立建立charainfo／bosspattern／bossskill索引；记录ID与数组下标不得混用。
- 完整枚举charainfo真实pattern引用及顺序，核当前父在集合内；逐答案重走pattern.skillidN→bossskill，核实际下标、record_id、raw、字段指针和raw_record_sha256。
- 用既有 `rules.answer_for` 重算value、float32、单位、方向、对象与状态。`numeric_evidence=确认`仅限原值＋规则体；关联必须推断，binding=inferred，runtime_verified=False。
- 真实 `card_page_data.Inputs`＋`effect_ledger.analyze_row` 验证首次P1=10／P2=15、目标effect全部has_answer、新增未消费0、split_flags不新增；第二次新增0且序列化不变。旧原文数字未消费与新增未消费必须分开。
- 精确变体消费必须满足row_id、effect_type、span、pattern_id、variant_group、source字段与 `inference_yg1.pattern_ids` 的C20 scope。篡改任一身份应拒绝或保持未消费，不能靠condition_label颜色／HP前缀掩盖。
- 旧答案前缀、非目标行、保护卡、30207／278／220、其它pattern和denju零新增；缺省／错误／空scope硬拒绝。

### B. P1 9卡10答案

确认这些是当前pattern行，不是复制C14-P2的skilltext镜像行。逐值核对：7250＝1／15；30105＝8；30107＝4；30220＝12.5；30223＝15；30225＝5；30301＝8；30329＝5；30334＝4。多段次数与倍率分开，句尾Chain强化、其它pattern、denju、回复、异常和状态不借值。

### C. P2 7卡8效果15答案

- 20332：8个真实父按同记录合成4项20／19／18／17，HP整数百分比76–100／51–75／26–50／0–25含边界，Chain 0–1与2–5共用同记录；只答前方敌人，自身受伤与type116另论。
- 12236 pattern1：初始1.25（41223600／858）与使用一次后1.5（41223601→41223602／860），次数限当前控制器生命周期。
- 12236 pattern3：只答当前父41223605＝2（bossskill下标863）；旧41223602＝1.5不重复。缺priority构造0与当前priority=100必须分开，不能套J/AB默认。
- 5300：森林含夜间、bgf=4、limit=3且当前控制器不足3次；通常父与森林父共用bossskill40530000＝1.75，合记一项；非森林／耗尽回退基础，跨波／复活／重建不保证。
- 7654：预测扣费后职业法珠0–2＝4.5、3–12＝6；执行沿用缓存档位，不写所有场景的发动前门槛。
- 12032：0–3基础父31203200／2353＝4.5；4–12父31203201／2354同为4.5但异记录，只披露合记一项，不任选父或重复计答案。
- 12226：废料0–2＝0.75、3–12的raw必须为 `1.100000023841858`；12回是次数，玩家文案1.1不得覆盖raw。
- 20619：废料0–1＝35、2–12＝37.5；超共鸣父不并入。

### D. 展示与证据边界

默认player_text必须可读、条件完整，不含skillparam／bossskill／公式／JSON指针。展开value／source／binding须保留精确公式、raw、表名、字段、指针、完整父集合、合记／排除和限制。证据路径按模型相关，不得把静态补证写成新原生执行或实机。

## 输出要求

`verdict.json` 明确 verdict、blocking、实际独立重算数、只读引用数、18效果／25答案台账、未测项。结论使用 `PASS_WITH_EXPLICIT_SCOPE_LIMITS` 或 `REQUEST_CHANGES`。任何阻断给出精确row／record／字段／证据和最小修复范围；个别项不合格可单独否决，不为凑25放行。未实际浏览器、原生执行或实机时明确UNTESTED。

若只有非阻断限制，可带明确范围限制通过；若任一来源、条件、单位、归属、消费或保护边界错误，必须REQUEST_CHANGES，主持不会接线或启动正式生成。
