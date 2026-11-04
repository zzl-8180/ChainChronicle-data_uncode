# 交原第三方：C15 周期方向审查提示词

请对《锁链战记》角色技能主线 **C15** 做独立、只读的方向审查。你不是此前的例行数值终审者；请重点检查周期交付方向、成果页忠实度、来源展示、计数口径、边界与停止点，不必重新开发解算器。

## 读取入口

先读：

1. `AGENTS.md`、`HANDOFF.md`、`docs/角色技能完整解读实施方案.md`。
2. `docs/tasks/character-skills-progress.md` 当前块。
3. `docs/tasks/20261103-c15-cycle.md`、`docs/tasks/20261103-c15-delivery-package.md`、`docs/tasks/20261103-c15-p1-denju-damage-direct.md`。
4. `output/character_skills/c15_delivery_20261103/README.md`、`run_record.json`、`run_records/formal_build_summary.json`、`checks/final_diff.json`、`checks/validate_formal.json`。
5. P1候选审查 `output/character_skills/review/c15_p1_denju_damage_direct_20261103_deepseek/REPORT.md` 与 `verdict.json`。
6. 正式独立终审 `output/character_skills/review/c15_delivery_final_20261103_deepseek/REPORT.md`、`verdict.json`、`evidence.json`。
7. 本周期成果：
   - `output/character_skills/cycle_reports/C15/index.html`
   - `remaining.html`
   - `report_data.json`
   - `verification.json`
   - `verification_detailed.json`
   - `browser_verification.json`
   - `final_manifest.json`
   - `handoff_verification.json`
8. `docs/tasks/20261104-c15-cycle-closeout.md`。

## 必须逐项核对

1. **版本与一次生成**：campaign应为`65839ad742869b73949926049f85cdb1fab08d7e9bed8c721adc5ac32fa66e8b`，snapshot为`65839ad7-cf9451c6ff47fcfb`，rules 294键未改。正式全库生成历史恰1次、jobs 4；`formal_build_summary`的`executed=true/count=1`与resume后`run_record`的`executed=false/reused_after_build=true/count=1`并不矛盾，后者是复用首次构建的记录。不得把它误报为第二次生成或未生成。
2. **真实增量**：恰5个cid、6行、6答案／6效果，全部Y.G.，非Y.G. 0。7250两行，30105／30301／30329／30334各一行。六条raw依次为1、15、8、8、5、4；P2/P3未启动，不能为了凑“6卡”或三批扩域。
3. **来源与答案展示**：逐条从成果页展开答案，核对table=`bossskill`、正整数record_id、layer=CACHE、field_path=`/skillparam1`、record_key、source与逐答案json_pointer；确认页面没有把数值规则体确认写成句→记录关联确认。六条均应为numeric=确认、association=推断，只写局部伤害输入公式，不写最终扣血、保证命中或运行时选档。
4. **账本与剩余量**：has_answer 21,044（Y.G. 5,298）、unresolved 48,621（Y.G. 5,256）、backlog 74,814（Y.G. 8,537）、identified 69,964；完整6,488、部分264、未解析8,720、拆分26,193，A 18,523／C 23,142。完整／部分／未解析／拆分增量均0，A+1／C−1，S4 0；6行仍拆分待核查。
5. **4张指纹工件卡**：30107／30220／30223／30225只允许既有C14-P2 `binding.g1_b1_binding.page_sha256`重算，不计C15语义收益；不得写成“范围外2,231卡逐字节不变”。正确口径是5张C15目标卡＋4张信息性指纹工件卡，其他2,227卡逐字节不变。30236／30239／30102／20234保护边界不破。
6. **成果页机器对账**：6个`tr[data-cid]`、6个答案`details`；remaining未解效果合计48,621、Y.G. 5,256，拆分26,193；本地链接目标存在。`verification_detailed.json`应18/18 PASS、坏链接0；最终清单12个文件及单向manifest哈希应一致。
7. **正式终审的非阻塞文档项**：审查时交付包README曾写“正式生成0次”，主持已更正状态行与§4。不要改写原审查报告或要求消除这条历史发现；请核当前README是否已与`formal_build_summary/run_record`一致。
8. **浏览器回执分主体**：主持已实际覆盖桌面成果页、首条答案展开、剩余量链接、窄屏指标与横向滚动，并保存两张成功截图。答案展开／桌面剩余量／原窄屏标签截图有运行时超时，窄屏表格截图未测；角色／正式终审链接点击未完成，完整控制台未采集。上述只能称主持侧有限回执。若你未实际执行浏览器，必须明确写第三方浏览器UNTESTED，不得把主持截图或DOM结果冒充你的独立视觉验收。
9. **审查范围**：正式独立终审PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0、33项独立检查通过，不代替你的方向复核；你的PASS也不应扩大成完整原生、实机、任意分组复现或全游戏完成度结论。

## 写入与停止边界

- 只写你自己的新目录：`output/character_skills/review/direction_c15_20261104_thirdparty/`，至少包含`REPORT.md`、`verdict.json`，另附实际检查证据与执行命令。
- 不修改正式pages／ledger／rules／入口页、候选包、交付包、C15成果目录、既有独立审查或历史整改包。
- 不运行正式全库生成、`run_formal.py`（含resume）、隔离卡页生成；不要原地重跑会覆盖交付回执或历史审查证据的脚本。需要重算时在自己的审查目录实现只读读取、独立输出。
- 不执行清理、Git、发布，不启动C16，不实施机制优先交接包中的候选。
- 若发现问题，按R01／R02…给出严重度、是否阻断、精确文件／行／答案、实际证据和最小整改范围；不要把未测项伪装成产品缺陷，也不要以旧PASS替代当前核查。

请在`verdict.json`明确给出`verdict`、`blocking_findings`、实际核查行数／答案数、未测项。结论可用`PASS_WITH_EXPLICIT_SCOPE_LIMITS`或`REQUEST_CHANGES`；最终报告请区分“独立重算／实际浏览器／仅阅读证据／判断性结论”。
