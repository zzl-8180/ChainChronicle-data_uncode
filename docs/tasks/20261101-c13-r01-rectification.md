# C13-P2 R01 来源身份门控有界整改

- 日期：2026-11-01；主持：本会话 `new-provider/kimi-k3-1-pro-261024`。
- 状态：**整改完成，独立定向复核PASS_WITH_EXPLICIT_SCOPE_LIMITS；待原第三方再次定向复核，原REQUEST_CHANGES不改写**。
- 原审查：`output/character_skills/review/direction_c13_20261101_thirdparty/REPORT.md`、`verdict.json`、`p2_mutations.json`、`evidence_schema_variation.json`、`cohort_replay.json`。
- 范围：仅R01门控修复与N01复现边界记录；不启动C14、新缓存、原生专项、清理、Git提交或发布。

## 缺陷与最小修复范围

当前C13-P2分支只核binding.scope/rule_key/record_id/layer及答案顶层常量，未逐项比对binding.field_path/table、carrier_slot及source身份，导致三类binding篡改和source.layer／record_id篡改仍消费。目标只修改 `scripts/character_skills/effect_ledger.py` 的C13-P2专用分支：

1. 合法10215／30228／30314三条继续消费。
2. scope、rule_key、field_path、table、record_id、layer、carrier_slot或source身份矛盾，或必要字段缺失时，回复效果必须回到unresolved。
3. carrier_slot只接受skillid0；binding、答案顶层和source的table／field_path／record_id／layer必须同源一致。
4. 不新增整族t27映射，不扩大卡、行、档位；p2/p3仍仅披露。
5. 不改变P1 type8消费、P3 `quantity_kind=持续时间`回退、C8/C10 t27分支及保护卡行为。

## 写入范围

- `scripts/character_skills/effect_ledger.py`（仅C13-P2分支）。
- `work/c13_r01_rectification/`：基线、探针、差异和验证辅助材料。
- `output/character_skills/rectification_c13_r01_20261101/`：整改报告、前后反例、回归、源码版本和复核入口。
- 独立复核：`output/character_skills/review/c13_r01_rectification_20261101_deepseek/`及自身work。
- 当前交接文件仅由主持最小更新；不覆盖旧审查或冻结交付。

## 验证要求

- 三卡逐项覆盖binding／answer／source的scope、rule_key、field_path、table、record_id、layer、carrier_slot、缺失和source整体缺失。
- 必须读取实际 `effect_ledger.analyze_row` 的效果状态，不只断言辅助函数返回值。
- 保存修复前后结果、合法三条、P1/P3、保护卡和正式页面／账本字节不变证据。
- 分别记录原构建版本与整改后代码版本，禁止把修复后源码哈希冒称首建时哈希。
- N01只保留固定cohort复现条件，不重构全库证据schema、不删除旧证据。
- 第三方真实浏览器视觉／交互本轮未测；主持侧历史浏览器回执单列。
- 正式全库生成仅1次，本整改不执行第二次正式全库重建；RETAINED 12/12不清理。

完成后状态只写：**整改完成，待原第三方定向复核**，不得自行宣布方向审查通过。独立复核材料：`output/character_skills/review/c13_r01_rectification_20261101_deepseek/REPORT.md`、`verdict.json`；整改包：`output/character_skills/rectification_c13_r01_20261101/README.md`、`final_manifest.json`。
