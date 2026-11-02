# C13 交付包（P1 supporterskill type8／P2 t27镜像／P3 2012时长镜像）

- 日期：2026-10-31；主持：`new-provider/kimi-k3-1-pro-261024`。
- 状态：**C13正式独立审查PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0；成果展示与浏览器验收完成，等待用户安排第三方方向审查**。campaign `f0b36c7f0c40284bf8c25a74e3014d34884c2deabaa436815f4de5e62abcb357`；snapshot `f0b36c7f-cf9451c6ff47fcfb`。收口记录 `docs/tasks/20261031-c13-cycle-closeout.md`。
- 前置门：P1 `PASS_WITH_EXPLICIT_SCOPE_LIMITS`、P2 `PASS`、P3 `PASS_WITH_EXPLICIT_SCOPE_LIMITS`，均阻断0。
- 方案：`docs/角色技能完整解读实施方案.md`（2026-10-31现行）；总卡 `docs/tasks/20261031-c13-cycle.md`。

## 冻结候选与审查

| 批次 | 候选 | 独立审查 | 模块SHA-256 |
|---|---:|---|---|
| P1 supporterskill→abiN type8 | 61卡61行89答案（攻61／防24／移4） | `output/character_skills/review/c13_p1_supporterskill_type8_20261031_deepseek/REPORT.md` | `f5a1caaf395dc0588606a2bdbd2f90258241efc089f278ba2385762ccc201e5d` |
| P2 t27同卡同文回复镜像 | 3卡3行3答案 | `output/character_skills/review/c13_p2_t27_mirror_20261031_deepseek/REPORT.md` | `6a939d5392e220d048cdc2ecab3cb9c1df4b55c78d2ec15e3600cf9fe91dc030` |
| P3 2012同卡同记录攻速时长 | 2卡3行3答案 | `output/character_skills/review/c13_p3_2012_duration_20261031_deepseek/REPORT.md` | `550042a32a1dd075f048dd9f1f13fbe784f9adc6476057d099138208ff4a1154` |

候选合计67行95答案，全部Y.G.、非Y.G. 0；不是正式收益。候选答案SHA-256：P1 `bd5ce13c843ed575a8b7329907dc31e7176fefee04858b77ed30cc8edcd73581`；P2 `d283ce2dec0db0dbd6e4807a0d82b6af40c8d272025f8dee81607b628626b175`；P3 `52ac259c4a9c0faeefc039e6b87b74b4d4adf9952e59ea3f61008364e2f1206c`。

## 合并写入与约束

1. 主持最小修改 `scripts/character_skills/card_page_data.py`：新增三模块显式scope接线；P1复用`apply_to_skill`并按新增答案来源补嵌缺失的`record_evidence`，不得重复嵌入或改写既有项。
2. 主持最小修改 `scripts/character_skills/effect_ledger.py`：仅新增P2 `binding.c13_p2_t27_mirror_binding`／scope `C13_P2_T27_MIRROR_20261031`的来源限定t27 p1映射。P1 type8与P3时长使用既有通用消费路径，预检逐行实测，不为形式统一多加映射。
3. 不改三份已审候选模块、rules.json、rules.py或其他语义模块；不覆盖旧批次、旧审查、C11／C12冻结成果。
4. 新增交付目录 `output/character_skills/c13_delivery_20261031/` 和自身work `work/c13_delivery_20261031/`；正式pages／账本／入口只在预检全过后由唯一正式入口写入。
5. 合并预检必须重新推导95条来源、核对变化卡／行、旧答案前缀、证据嵌入、跨批交互、no-op、幂等、保护卡、账本效果与完整增量；数量不符即停止，不静默降级。
6. 容量基线8/12；正式四cohort前重新核对，不在本包自动清理。正式全库生成最多一次、jobs 4；失败后只可按实际回执从构建后续跑，不重复全库生成。

## 合并预检冻结预期

63张候选卡小范围重建实测：63卡67行95答案，旧答案前缀0失配、P1证据缺失0、未解效果129→34（净−95）、S4 0；P3三行由部分变完整，故完整+3、部分−3。卡片summary实测A+3／C−3、整行推断+3，identified／unparsed／split_check预期不变。全库no-op与其他卡零变化仍须由 `run_prechecks.py` 证明，不能以小范围结果替代。

接线冻结：`card_page_data.py`=`68a01c16e0663c18e2bd502434e4366239414332d7a967b09b34939a5d271949`；`effect_ledger.py`=`0e52a01be31b8e95002a14bcaf1658da413167c2c58e2143eebddb198166d29a`。接线前基线分别为`34976af8…388bfc`与`1a8ebf5f…b8de1`；rules及三份已审候选模块不变。首建后仅为确定性复现修复backlog冻结与证据schema，未进行第二次全库生成；E2 150文件与首建逐字节一致。

## 正式步骤

冻结源码／输入／审查／范围 → 合并预检 → 重建前基线 → 唯一一次四cohort生成 → 正式账本 → 入口页／选题链 → verify_full／A7／final_diff／隔离复跑 → 独立终审 → C13成果页与剩余量 → 停止等待用户安排第三方方向审查。

正式预期影响卡数、答案净增、效果净增、完整／部分／未解析、S4及整行推断变化以合并预检和正式账本实测为准，不用候选数提前填报。

## 禁止

不新原生、实机、新缓存、C14、清理、Git、发布或其他专项；不扩大30239豁免、不处置20234、不处理30102／30236／30239；denju非首段、状态异常回复、t16、1095、30102、t11/t84不写成已解决。
