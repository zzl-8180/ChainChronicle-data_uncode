# マナ B 档只读范围审计（第 3 批备料）

- 日期：2026-10-26。状态：**审计已完成**（dwfrun-748ae69c，DeepSeek V4.1 Flash high）；交付 `output/character_skills/inference_inventory/mana_b_audit_20261026/`（范围文档、batch_candidates.csv 724 行、b_readiness_rows.jsonl 2,509 行逐行裁定、verify_claims.py 62/62 通过）。第 3 批任务书 `docs/tasks/20261026-mana-b-batch.md` 已据此派发。

## 实测结论（锚点 781731f3-de6030e7dceb858d）

- B 行集合稳定 2,509（left/entered 0），映射批不影响 B；命中行 backlog 项 7,151（前审计 8,341 系口径与 A 档关闭变化）。
- 就绪子族：start_boost 314 可核实（全槽覆盖）；start_job 84（42 P4＋42 P0boost，14 行 param1+iParam0 排除）；hold_mana 116 全槽（47 行带未覆盖 HP 回复子句排除）；mana_count_up 38（96 八键全槽）；gain_chance 172 带限制（28 专项）。
- 不足排除：Chain 36（1106 显示计数换算未验证＋数据侧 2 处同句两槽自相矛盾）；param1+iParam0 14 行（无受控检查）；gain_number 1,005（831 无载体＋173 类型不符）；cost_statement 302 冻结；qualifier 78；gain_kill/gain_job_no_number 68。
- 互斥分区：2,509＝724＋63＋25＋1＋252＋1,249＋117＋78。

## 主持裁决（2026-10-26，第 3 批范围依据）

1. **Chain 36 行**：维持排除。证据矛盾与换算未验证成立，不改判「只出数量、档位沿用句面」。
2. **isBoost（param0×param5）42 行**：批准新增 `skilllist|26|/param5` 作为**条件/标志键**（slices[5] 已证 param5==1 传 ProduceManaForce；类型级推断，不升确认）；数值答案仍绑 param0，boost 条件如实披露；受控检查不过则这些行退出本批。不改写 26|param0 旧注记。
3. **S5（type28，172 行/189 项）**：**不并入第 3 批**，另立 28 专项再裁决（概率阈值出示口径、param6≠4 只写掩码不写地形名、param9 未知注记）。
4. **param1+iParam0 原生窄目标**（补 3–5 项受控检查、无需新反汇编）：登记为后续候选，**不纳入第 3 批**；原生类动作仍按边界需用户明确后开展。
- 第 3 批范围＝S1 start_boost 314＋S2 start_job 84＋S3 hold_mana 116＋S4 mana_count_up 38＝**552 行/761 项（P1 14、Y.G. 9）**，不含 S5。
- 依据：マナ批/映射批已收口（周期 2/3）；自动推进「每批先小审计定范围」。前审计 `output/character_skills/inference_inventory/mana_audit_20261025/`（B 档 2,509 行/3,686 项）。
- 当前版本：snapshot `781731f3-de6030e7dceb858d`（映射批后，backlog 77,123）。必须在新账本重导，不搬旧数。
- 写入范围（唯一）：`output/character_skills/inference_inventory/mana_b_audit_20261026/`；只读其他一切，不改正式产物/脚本/rules、不原生提取、不 Git。

## 目标

把 B 档（公式核实）拆成子族并逐族判定证据就绪度，给出第 3 批建议范围（精确计数、门控、排除项）：

1. Chain マナ獲得 36 行：1106 param1-4 与 1st/2nd/3rd Chain 文本的档位映射能否用既有证据核实（chain_mana 等）；不足则排除。
2. 第三套槽位 param1＋iParam0（APK 21＋CACHE 3）与 param0×param5(isBoost)（30+11）：槽位语义有无既有原生证据；不足则排除。
3. 28 六键仅单来源（43023602）：是否仅限单记录或可扩，param6 取值映射/param3 与 param4/5 同值的证据情况。
4. 其余 B 子族（gain_job_no_number、mana_count_up、slot_rate 等按实际清单）：哪些可用既有证据公式核实、哪些需新原生（排除）。
5. 映射批后这些行的最新状态是否有变化（新账本重导并说明差异）。

交付：范围文档＋候选清单＋建议批次范围与验收要点（中文），注明证据位置与未知。
