# 交第三方：C16 周期方向审查提示词

请对《锁链战记》角色技能主线 **C16** 做独立、只读的方向审查。重点检查周期交付方向、成果页忠实度、默认中文、来源展示、计数口径、保护边界与停止点，不必重新开发解算器。

## 读取入口

1. `AGENTS.md`、`HANDOFF.md`、`docs/角色技能完整解读实施方案.md`、`docs/tasks/character-skills-progress.md` 当前块。
2. `docs/tasks/20261104-c16-cycle.md`、`docs/tasks/20261104-c16-p1-1095-partial-binding.md`、`docs/tasks/20261104-c16-delivery-package.md`。
3. `output/character_skills/c16_delivery_20261104/README.md`、`run_record.json`、`run_records/formal_build_summary.json`、`checks/final_diff.json`、`checks/validate_formal.json`。
4. 候选审查 `output/character_skills/review/c16_p1_1095_partial_20261104_deepseek/REPORT.md` 与 `verdict.json`。
5. 正式独立终审 `output/character_skills/review/c16_delivery_final_20261104_deepseek/REPORT.md`、`verdict.json`、`evidence.json`。
6. 本周期成果：
   - `output/character_skills/cycle_reports/C16/index.html`
   - `remaining.html`
   - `report_data.json`
   - `verification.json`
   - `verification_detailed.json`
   - `browser_verification.json`
   - `final_manifest.json`
   - `handoff_verification.json`
7. `docs/tasks/20261104-c16-cycle-closeout.md`。

## 必须逐项核对

1. **版本与一次生成**：campaign应为`09258f11cc04beda8662133cf8bf3be5ee77d36543d7290315b857e663406858`，snapshot为`09258f11-cf9451c6ff47fcfb`，rules 294键未改。正式全库生成历史恰1次、jobs 4；`formal_build_summary`的`executed=true/count=1`与resume后`run_record`的`executed=false/reused_after_build=true/count=1`一致，不是第二次生成。
2. **真实增量**：恰23卡、23行、49答案／49效果，Y.G. 23／非Y.G. 26；完整+23、未解析−23，A/C/整行推断/S4均0。字段分布：Y.G. param1×15、param5×7、param6×1；非Y.G. param1×8、param2×6、param3×6、param5×6。
3. **来源与答案展示**：逐条从成果页展开答案，核对table=skilllist、正整数record_id、layer=CACHE、field_path=/param1..6、record_key、source与逐答案json_pointer；默认中文可读，关联为推断，不把数值规则体确认写成句→1095字段归属确认。
4. **账本与剩余量**：has_answer 21,093（Y.G. 5,321）、unresolved 48,572（Y.G. 5,233）、backlog 74,765（Y.G. 8,514）、identified 69,964；完整6,511、部分264、未解析8,697、拆分26,193，A 18,523／C 23,142。
5. **9张漂移卡**：7250／30105／30107／30220／30223／30225／30301／30329／30334只允许既有`binding.g1_b1_binding.page_sha256`重算，不计C16收益；其他2,205卡逐字节不变。30225同时是合法目标卡与漂移卡，不能误报为冲突。保护卡30236／30239／30102／20234不破；30102的两条1095答案属历史B12而非C16。
6. **正反例**：20905／20906载体在sub[1]；额外活性槽与条件增强不并入；同文异值不复制；20607四项与暴击率、type108七项继续未知；2个跨命名空间同号非Y.G.记录APK ability=8且值不同，只能取CACHE。
7. **成果页机器对账**：23个`tr[data-cid]`、49个答案`details`；remaining未解效果合计48,572、Y.G. 5,233，拆分26,193；本地链接目标存在。`verification_detailed.json`应18/18 PASS、坏链接0；最终清单11个文件及单向manifest哈希一致。
8. **浏览器主体**：主持只做了默认摘要、首条展开、剩余量内容和窄屏横向滚动。桌面与窄屏截图均UNTESTED_RUNTIME_TIMEOUT；剩余量两种链接点击均未得到可验证导航，角色／审查链接与完整控制台未测。若你未实际执行浏览器，必须写第三方浏览器UNTESTED，不得把主持DOM回执冒充你的独立视觉验收。
9. **范围**：正式独立终审PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0、16/16通过，不代替你的方向复核；你的PASS也不应扩大成实机、完整原生、任意分组复现或全游戏完成度结论。候选REPORT.md:10的16/16与verdict/evidence 15/15差异保留，以verdict/evidence为准。

## 写入与停止边界

- 只写你自己的新目录：`output/character_skills/review/direction_c16_20261104_thirdparty/`，至少包含`REPORT.md`、`verdict.json`及实际检查证据与命令。
- 不修改正式pages／ledger／rules／入口页、候选包、交付包、C16成果目录、既有独立审查或历史整改包。
- 不运行正式全库生成、`run_formal.py`（含resume）、隔离卡页生成；不要原地重跑会覆盖交付回执或历史审查证据的脚本。需要重算时在自己的审查目录实现只读读取、独立输出。
- 不执行清理、Git推送、发布，不启动C17或其他机制族。
- 若发现问题，按R01／R02…给出严重度、是否阻断、精确文件／行／答案、实际证据和最小整改范围；不要把未测项伪装成产品缺陷，也不要以旧PASS替代当前核查。

请在`verdict.json`明确给出`verdict`、`blocking_findings`、实际核查行数／答案数、未测项。结论可用`PASS_WITH_EXPLICIT_SCOPE_LIMITS`或`REQUEST_CHANGES`；最终报告请区分“独立重算／实际浏览器／仅阅读证据／判断性结论”。
