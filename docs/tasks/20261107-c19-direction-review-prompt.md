# 交第三方：C19 周期方向审查提示词

请对《锁链战记》角色技能主线 **C19** 做独立、只读的方向审查。重点检查交付方向、成果页忠实度、默认中文、来源展示、计数口径、保护边界与停止点，不必重新开发解算器。

## 读取入口

1. `AGENTS.md`、`HANDOFF.md`、`docs/角色技能完整解读实施方案.md`、`docs/tasks/character-skills-progress.md`当前块。
2. `docs/tasks/20261107-c19-cycle.md`、`20261107-c19-p1-1095-attack-families.md`、`20261107-c19-p2-type8-basic-attack.md`、`20261107-c19-delivery-package.md`、`20261107-c19-cycle-closeout.md`。
3. `output/character_skills/c19_delivery_20261107/README.md`、`run_record.json`、`run_records/formal_build_summary.json`、`precheck/check_report.json`、`precheck/expected_ledger_delta.json`、`precheck/absolute_diff_scope.json`、`checks/final_diff.json`、`checks/validate_formal.json`。
4. 候选审查 `output/character_skills/review/c19_attack_candidates_20261107_deepseek/REPORT.md`与`verdict.json`。
5. 正式独立终审 `output/character_skills/review/c19_delivery_final_20261107_deepseek/REPORT.md`、`verdict.json`、`evidence.json`。
6. 本周期成果：`output/character_skills/cycle_reports/C19/`下的`index.html`、`remaining.html`、`report_data.json`、`verification.json`、`verification_detailed.json`、`browser_verification.json`、`final_manifest.json`、`handoff_verification.json`。

## 必须逐项核对

1. **版本与一次生成**：campaign应为`99bee2a166e5ec5f9c03ac97b555d4ada2f6f30d1535258add16bc64c7227c66`，snapshot为`99bee2a1-cf9451c6ff47fcfb`，rules 294键未改。正式全库生成恰1次、jobs 4、133.24秒、未使用resume；`run_formal.py`总617.3秒不是整个C19周期。不得运行第二次全库生成或resume。
2. **真实增量**：恰133卡、133行、407答案／407效果，Y.G. 52／非Y.G. 355。P1 CACHE 130卡404答案（param1 130／param2 74／param3 71／param5 90／param6 39）；P2 APK 1063提高35%、1238提高75%、12220提高10%。完整+95、部分+34、未解析−129，A/C/整行推断/S4均0。
3. **来源与答案展示**：逐条从成果页展开答案，核对table=skilllist、正整数record_id、layer=CACHE或APK、field_path=/param1..6、record_key与逐答案json_pointer。P1直接父71／唯一sub 59（sub[1] 7），P2父自身type8／唯一type8子记录。默认中文可读，关联为推断，不把数值规则体确认写成句→字段归属确认。
4. **字段语义**：param3为受伤量减伤而非固定防御，param5为百分点，param6为1.5基准系数增量；param4/7/8不解释，20131／20512／20603缺param5不补零，47个非中性未主张槽不并入。130个1095目标行仍有45个其他effect未解，4行既有split_flags未新增。
5. **账本与剩余量**：has_answer 21,505（Y.G. 5,376）、unresolved 48,160（Y.G. 5,178）、backlog 74,353（Y.G. 8,459＝拆分3,281＋未解5,178）、identified 69,964；完整6,611（Y.G. 1,464）、部分298、未解析8,563、拆分26,193，A 18,523／C 23,142、整行推断6,370。剩余页合计须一致。
6. **139卡并集与保护边界**：133目标∪9既有漂移＝139，因为7250／30107／30220同时属于目标与漂移集合；不要写成142。其他2,097卡`card.json/index.html`逐字节不变。9张漂移只允许既有`binding.g1_b1_binding.page_sha256`，不计C19收益，指纹指构建时输入页。保护卡30236／30239／30102／20234不破；C16／C17／C18旧答案不误归C19。
7. **正反例**：7687跨能力槽不可用；20607／20638／20708缺CACHE上游或跨源冲突不拼接；已有答案行、条件增强、友方、近战、WAVE／击杀／地形／静止／命中／反击／自动必杀不借值。12个APK同名不同值只取CACHE；type8既有quantity_kind回退不新增映射。
8. **成果页机器对账**：133个`tr[data-cid]`、407个答案`details`；remaining未解效果48,160、Y.G. 5,178，拆分26,193；本地链接目标存在。`verification_detailed.json`应21/21 PASS、坏链接0；最终清单11个文件及单向manifest哈希一致，当前manifest SHA-256为`afc2c436cfe289a335d3590a076f5f518d6ec7880eba64ef3025c6f2c6c16f42`。
9. **浏览器主体**：主持只做了133行407详情计数、220答案DOM展开与来源、剩余量、320px横向滚动0→160及往返导航；截图、完整控制台、角色／审查链接未测。若你未实际执行浏览器，必须写第三方浏览器UNTESTED，不得把主持DOM回执冒充独立视觉验收。
10. **非阻断说明**：F1文档哈希已同步为当前`run_prechecks.py`；F2并集139（交集3）不写成142。候选N01–N05保留：关联推断、45个其他effect未解、4行既有split_flags未新增、12个APK同名不同值只取CACHE、type8既有quantity_kind回退。正式独立终审47/47＝28项独立重算＋19项只读引用，不代替你的方向复核。

## 写入与停止边界

- 只写你自己的新目录：`output/character_skills/review/direction_c19_20261107_thirdparty/`，至少包含`REPORT.md`、`verdict.json`及实际检查证据与命令。
- 不修改正式pages／ledger／rules／入口页、候选包、交付包、C19成果目录、既有独立审查或历史整改包。
- 不运行正式全库生成、`run_formal.py`（含resume）、隔离卡页生成；不要原地重跑会覆盖交付回执或历史审查证据的脚本。需要重算时在自己的审查目录实现只读读取、独立输出。
- 不执行清理、Git提交／推送、发布，不启动C20或其他机制族，不做新原生、实机或新缓存。
- 若发现问题，按R01／R02…给出严重度、是否阻断、精确文件／行／答案、实际证据和最小整改范围；不要把未测项伪装成产品缺陷，也不要以旧PASS替代当前核查。

请在`verdict.json`明确给出`verdict`、`blocking_findings`、实际核查行数／答案数、未测项。结论可用`PASS_WITH_EXPLICIT_SCOPE_LIMITS`或`REQUEST_CHANGES`；最终报告请区分“独立重算／实际浏览器／仅阅读证据／判断性结论”。你的PASS也不应扩大成实机、完整原生、任意分组复现或全游戏完成度结论。
