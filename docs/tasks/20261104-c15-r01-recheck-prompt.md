# 交原第三方：C15-R01 定向复验提示词

请对《锁链战记》C15第三方方向审查中的**唯一阻塞项R01（成果页默认阅读层）**做定向复验。你是原第三方审查的接续上下文；本次只核R01整改及其直接影响，不重做全库数值、原生或完整历史审查。

## 原裁决与整改入口

先读：

1. 原审查 `output/character_skills/review/direction_c15_20261104_thirdparty/REPORT.md`、`verdict.json`、`evidence.json`。原裁决为REQUEST_CHANGES，阻塞1项R01；第三方实际浏览器UNTESTED。
2. `docs/角色技能完整解读实施方案.md` §1.3。
3. `docs/tasks/20261104-c15-r01-default-reading-rectification.md`。
4. 整改证据 `output/character_skills/rectification_c15_r01_default_reading_20261104/README.md`、`code_diff.patch`、`generator_regression.json`、`source_verification.json`、`formal_integrity.json`、`hash_comparison.json`、`disposition.json`。
5. 新版成果 `output/character_skills/cycle_reports/C15_r01_20261104/`：
   - `index.html`、`remaining.html`、`report_data.json`
   - `verification.json`、`verification_detailed.json`
   - `browser_verification.json`
   - `run_record.json`、`final_manifest.json`、`handoff_verification.json`

原`output/character_skills/cycle_reports/C15/`及原第三方目录是保留前像，不要修改。

## 必核R01

1. **默认中文**：逐条读取六个`<summary>`，应分别与正式JSON六条`player_text`一致，并附“句面到来源的关联为推断”。默认层可直接理解敌方对象、技能基础攻击的倍率与相对B、必要回数、其他档位排除，以及实际扣血和命中尚未验证。
2. **内部术语移除**：六个默认summary均不得再出现floor/clamp、float32、param、denju.patternid0、bossskill、skillparam、S4或delta。注意这些研究信息可以且必须继续出现在展开层，不要误判为全部删除。
3. **展开层完整**：六条均应含原精确`value`、raw、单位、table=bossskill、正整数record_id、layer=CACHE、field_path=/skillparam1、record_key、source及逐答案json_pointer；numeric=确认／association=推断，关联未升格。
4. **范围不变**：仍5卡6行6答案，raw依次1、15、8、8、5、4；没有新增解析收益。`remaining.html`、`report_data.json`与基础`verification.json`应与原C15逐字节一致，剩余量不变，本地链接目标存在。
5. **生成器影响**：`code_diff.patch`应是默认说明的显式选择路径，只有C15启用；`generator_regression.json`记录C13／C14共168条直接函数样本整改前后逐字节一致。该检查不冒充历史周期全量重建，历史目录未被重建或覆盖。
6. **完整性**：原C15和原第三方18个保护文件不变；4,479个正式输入文件聚合哈希不变。正式pages／ledger／rules／数值实现未改，正式全库生成和resume均未运行。
7. **新版清单**：详细验证应24/24 PASS、坏链接0；最终清单12个文件的大小／SHA-256及handoff对manifest的单向哈希应独立重算一致。`run_record`与`disposition`必须保留原REQUEST_CHANGES、复验PENDING，不能由主持预先写成R01 CLOSED或第三方PASS。
8. **浏览器主体**：主持只做了桌面／窄屏默认中文、首条展开和横向滚动，保存两张截图。窄屏答案区域滚动截图UNTESTED_SCROLL_TIMEOUT；展开截图、剩余量链接点击、角色／审查链接点击与完整控制台未测。若你未实际执行浏览器，继续写第三方浏览器UNTESTED；不要把主持回执当成你的独立视觉验收。

## 写入与停止

- 只写新目录 `output/character_skills/review/direction_c15_20261104_thirdparty_r01_recheck/`，至少包含`REPORT.md`、`verdict.json`及实际检查证据／命令。
- 不修改原审查、原C15、修订版、正式pages／ledger／rules或其他历史报告；不运行正式全库生成、`run_formal.py`（含resume）、隔离卡页生成、机制候选、C16、清理、Git收尾或发布。
- 需要重算时在自有审查目录独立输出，不原地覆盖主持验证或清单。
- 若仍有问题，给出精确summary／展开字段、文件位置、证据和最小整改范围；不要把未测项伪装成产品缺陷。
- `verdict.json`请明确`verdict`、`blocking_findings`、`r01_status`、实际核查答案数、浏览器与未测项。只有你可依据定向复验将R01标为CLOSED；主持不代填。

可给出`PASS_WITH_EXPLICIT_SCOPE_LIMITS`或`REQUEST_CHANGES`。即使通过，也仅表示R01默认阅读层整改闭环，不扩大为实机、完整原生、任意分组复现或全游戏完成度结论。
