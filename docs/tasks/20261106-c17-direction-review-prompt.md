# 交第三方：C17 周期方向审查提示词

请对《锁链战记》角色技能主线 **C17** 做独立、只读的方向审查。重点检查周期交付方向、成果页忠实度、默认中文、来源展示、计数口径、保护边界、终审限制与停止点，不必重新开发解算器。

## 读取入口

1. `AGENTS.md`、`HANDOFF.md`、`docs/角色技能完整解读实施方案.md`、`docs/tasks/character-skills-progress.md`当前块。
2. `docs/tasks/20261106-c17-cycle.md`、`20261106-c17-p1-1095-attack-partial.md`、`20261106-c17-delivery-package.md`、`20261106-c17-cycle-closeout.md`。
3. `output/character_skills/c17_delivery_20261106/README.md`、`run_record.json`、`run_records/formal_build_summary.json`、`precheck/check_report.json`、`precheck/expected_ledger_delta.json`、`precheck/absolute_diff_scope.json`、`checks/final_diff.json`、`checks/validate_formal.json`。
4. 候选审查 `output/character_skills/review/c17_p1_1095_attack_partial_20261106_deepseek/REPORT.md`与`verdict.json`。
5. 正式独立终审 `output/character_skills/review/c17_delivery_final_20261106_deepseek/REPORT.md`、`verdict.json`、`evidence.json`。
6. 本周期成果：`output/character_skills/cycle_reports/C17/`下的`index.html`、`remaining.html`、`report_data.json`、`verification.json`、`verification_detailed.json`、`browser_verification.json`、`final_manifest.json`、`handoff_verification.json`。

## 必须逐项核对

1. **版本与一次生成**：campaign应为`dc38910014d6f4629ec13e2afc6d46e8ea2dbdc6568c48c8169fad15518417b2`，snapshot为`dc389100-cf9451c6ff47fcfb`，rules 294键未改。正式全库生成历史恰1次、jobs 4、96.03秒；`formal_build_summary`的`executed=true/count=1`与resume后`run_record`的`executed=false/reused_after_build=true/count=1`一致，不是第二次生成。隔离16卡32文件不是第二次全库或任意分组复现。
2. **真实增量**：恰3卡30110／30237／30333、3行、3答案／3效果，全部Y.G.；raw 1.425／1.375／1.35，分别提高42.5%／37.5%／35%。完整+3、未解析−3，A/C/整行推断/S4均0，非Y.G.新增0；只用既有`skilllist|1095|/param1`，0新公式／规则键／账本映射。
3. **来源与答案展示**：逐条从成果页展开答案，核对table=skilllist、正整数record_id（43011001／43023701／43033301）、layer=CACHE、field_path=/param1、record_key及逐答案json_pointer（/skilllist/5943、6419、7455）；三载体均sub[0]，APK同号0条。默认中文可读，关联为推断，不把数值规则体确认写成句→1095字段归属确认。额外param6（2.5／2.375／2.375）与句外条件强化不并入。
4. **账本与剩余量**：has_answer 21,096（Y.G. 5,324）、unresolved 48,569（Y.G. 5,230）、backlog 74,762（Y.G. 8,511）、identified 69,964；完整6,514（Y.G. 1,459）、部分264、未解析8,694、拆分26,193，A 18,523／C 23,142、整行推断6,370。剩余页效果合计与这些口径一致。
5. **9张漂移卡与保护边界**：7250／30105／30107／30220／30223／30225／30301／30329／30334只允许既有`binding.g1_b1_binding.page_sha256`重算，不计C17收益；其值指**构建时输入页（重建前）哈希**，不是构建后正式页。其他2,224卡`card.json/index.html`逐字节不变。保护卡30236／30239／30102／20234不破；30102历史B12答案不能误算为C17。
6. **正反例与消费**：三个目标effect应各由unresolved→has_answer，答案全部被消费、split_flags不变；第二次0新增、缺省／错误scope硬拒绝。C16同族30246／20822、20607与保护卡零新增；同句面不跨卡复制，额外暴伤与句外强化不取数。
7. **成果页机器对账**：3个`tr[data-cid]`、3个答案`details`；remaining未解效果48,569、Y.G. 5,230，拆分26,193；本地链接目标存在。`verification_detailed.json`应20/20 PASS、坏链接0；最终清单11个文件及单向manifest哈希一致，当前manifest SHA-256为`2296ebb165207b14eba42776f108c899310a128e0cec79a6c1bffc22e08c8a6d`。
8. **浏览器主体**：主持只做了1280px默认摘要、首条答案DOM展开与来源、剩余量内容、320px表格横向滚动0→160，以及成果页↔剩余量往返导航。普通定位点击两次超时、DOM-CUA点击未展开，最终DOM evaluate点击`open=true`；这不是第三方视觉验收。桌面截图未尝试、窄屏截图3秒准备超时、完整控制台未采集、角色／审查链接未点击。若你未实际执行浏览器，必须写第三方浏览器UNTESTED，不得把主持DOM回执冒充你的独立视觉验收。
9. **过程与终审限制**：正式独立终审PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0、132/132＝113项独立重算＋19项只读引用，不代替你的方向复核。两次预检65/66仅A16 snapshot路径检查器问题，最终66/66，失败回执保留；首次构建后`EXPECT_DELTA['yg']`中断无独立机器回执，第二次`FULL_CARDS`中断有回执，两次均只修检查器并resume，无第二次全库。
10. **N01–N08**：N01共享交接旧状态由收口更新；N02冻结模块候选时“未接线”文档头不改；N03首次中断回执缺口保留；N04指纹为构建时输入页；N05展开层conditions含能力编号但默认player_text无内部术语；N06隔离目录48文件中32个card/index参与比较；N07旧`unknown_reasons`未刷新属既有展示遗留，未修复；N08生成器曾预写徽章，现已在终审后以正式verdict无阻断为闸门重建。不要把这些未测／展示遗留伪装成已解决，也不要仅因非阻塞说明否定已独立核实的数值。

## 写入与停止边界

- 只写你自己的新目录：`output/character_skills/review/direction_c17_20261106_thirdparty/`，至少包含`REPORT.md`、`verdict.json`及实际检查证据与命令。
- 不修改正式pages／ledger／rules／入口页、候选包、交付包、C17成果目录、既有独立审查或历史整改包。
- 不运行正式全库生成、`run_formal.py`（含resume）、隔离卡页生成；不要原地重跑会覆盖交付回执或历史审查证据的脚本。需要重算时在自己的审查目录实现只读读取、独立输出。
- 不执行清理、Git提交／推送、发布，不启动C18或其他机制族，不做新原生、实机或新缓存。
- 若发现问题，按R01／R02…给出严重度、是否阻断、精确文件／行／答案、实际证据和最小整改范围；不要把未测项伪装成产品缺陷，也不要以旧PASS替代当前核查。

请在`verdict.json`明确给出`verdict`、`blocking_findings`、实际核查行数／答案数、未测项。结论可用`PASS_WITH_EXPLICIT_SCOPE_LIMITS`或`REQUEST_CHANGES`；最终报告请区分“独立重算／实际浏览器／仅阅读证据／判断性结论”。你的PASS也不应扩大成实机、完整原生、任意分组复现或全游戏完成度结论。
