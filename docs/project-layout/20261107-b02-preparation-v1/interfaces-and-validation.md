# B02 最小接口与候选验收设计

**仅设计，未实现，未复制源码或运行候选。** 当前准入为 `NOT_HANDED_OFF`。原方案允许先设计；现有 `--root/--output` 不足以改变翻译、验证、媒体和失败分支的固定路径。以下字段是拟议接口，不是当前 CLI 可用参数。

## 先选产品与实际执行模式

| 模式 | 应接收的实际输入 | 边界 |
|---|---|---|
| full | Web 固定代码、原版前端、整合字典与参考材料；研究线同版 cards/campaign/rules/ledger/metrics；媒体约定 | 全库构建；当前源码会检查源卡与语义审查哈希，保留拒绝，不能给旧字典拼新主线 |
| sample | 同版研究输入及名字页、旧 copy/facts、reading_copy_extra、sample 前端／媒体 | 当前实现仍读全库目录与全部卡，只有详情六卡；不是仅收六卡即可运行。不得使用 full 默认输出 |
| frontend_refresh | 已由 Web 交付且属于本候选的阅读载荷／data receipt，以及选定原版 frontend | 不读当前研究线；不得刷新原站或他人候选。绑定完整数据 receipt 哈希，禁止只凭 builtAt 判断匹配 |
| inline_trial | Web 交付的固定阅读载荷、源 build/frontend receipts 和独立 inline 代码／frontend／验收版本 | 不读当前 C19；V3 等具体修订由 owner 确认，不把原版 frontend 和试读 frontend 混为一版 |

四种模式互斥；未选择或同时选择多个则预检拒绝。首个候选只选一种产品与一种模式。原阅读版或 inline V3 的选择尚未交接，不由本轮代用户定案。若只做 frontend/inline 的固定载荷旁路，不要求 C19 停工或重新拼出整套旧主线；若选择 full/sample，才需要所消费的研究输入交付。

## 最小路径契约

| 字段组（拟议） | 含义与验收 |
|---|---|
| `code_root`、`frontend_source` | Web 明确交付的代码与所选产品 frontend；现源码根推导、同级 import 要在候选进程中闭合，不只换 CWD。源码清单覆盖实际子调用；数据 receipt 与前端 receipt 可分层，须声明对应关系 |
| `pages_dir`、`campaign_pointer`、`campaign_report`、`rules_file`、`ledger_file`、`metrics_file` | full/sample 同版正式输入；campaign report 当前相对 pages 解析，须保留原含义。不要默认读取最新指针，也不改正式指针 |
| `reference_pairs`、`reference_index` | 已交付的翻译对照和 `index_unpack.html` 名字来源。Translator 不能自行拼旧 FULL/audit；即使有 semantic 字典，当前仍读 reference_pairs |
| `semantic_dictionary`、`reviewed_dictionaries` | 精确列明 `semantic_sentences.json`、`reviewed_sentences.json`、`extra_reviewed_sentences.json`、`audited_sentence_fixes.json`；按所选模式声明必须／不用。缺失必需字典硬失败，不以存在性静默切换到语法翻译模式 |
| `legacy_copy_dir`、`legacy_facts_dir`、`reading_copy_extra` | 仅 sample 显式选用；旧样稿是数据来源，不执行其历史生成器 |
| `source_reader`、`source_build_receipt`、`source_frontend_receipt` | frontend/inline 从交付载荷读取，不借当前正式 pages 补洞；inline 复制清单与哈希覆盖范围一致，不只 hash JS 却 copy 整树 |
| `media_dir`、`media_url_base`、`candidate_service_root` | 分开磁盘读取根与浏览器 URL 基址。当前 full 使用 `../pages/art`，原 app 会拒绝 http(s) 图片；不能只填一个磁盘根或绝对 URL 就声称可移植。由 owner 选定候选布局并验证 URL 在候选服务中可达，不改现服务路由或媒体位置 |
| `site_output`、`audit_output`、`validation_output` | 全部限制本批新候选树。验证报告与站点输入分开，含失败报告；frontend_refresh 仅操作本候选已接收的目录，其余新建必须不存在 |
| `candidate_app_js`、`candidate_inline_js` | Node 和 inline 验证显式读取实际候选输出字节；不能 `require` 当前源码 planner 后推断候选站点同版。模拟 DOM 与浏览器另记 |

候选站布局仅建议 `projects/reader/site/<candidate-id>/`，审计／验证在该候选下独立子目录；受控代码位置在交接时指定。本轮没有创建它们。后续实际生成前先设置该新目录的局部忽略规则（数据、媒体、站点与工作输出不入 Git），源码／配置／说明可跟踪；根 `.gitignore` 不动。空间按所选载荷和媒体估算，不默认复制三份站点或完整媒体库，不清理旧文件腾空间。

## 默认不运行的语义链

优先直接接收已整合冻结字典。prepare、merge、review_report、answer_inventory 均不因名称带审查而成为只读步骤。本次不需要为路径整理重新准备178包、重新合并或重新审语义。

未来若选定任务确需 merge，至少显式区分 `audit_input`、`progress_output`、`source_pages`、`dictionary_output`；collect 的进度写入也须落候选。review_report 不能暗中调用写现用进度的 collect。保留 ID、覆盖／重复、占位符、裸数字、空句、标题、语义禁混、verdict、完整性、源卡哈希和结果哈希拒绝；未整合的分片不是已交付字典。

## 分阶段验证（均未执行）

1. **接收前预检**：明确产品、mode、输入版本、所有者回执和未完成项；解析实际文件／别名，确认读集没有未声明兜底、写集不含正式根。复用已有清单和哈希核选定集合，不新设全项目／全媒体双端哈希门槛。
2. **候选准入**：代码、前端、参考／字典、所选数据版本对应；旧数据 receipt 与后续 frontend-only 修改分层登记。主线和 reader 快照不同不自动判损坏，但不准混用。缺必要文件或身份歧义在首次写出前拒绝；仅末尾 adapterHashes 不够。
3. **独立构建**：选定候选源码、CWD、进程及全部路径；实际写入和失败诊断只进本候选。构建前后核必要输入／代码身份；源变时停止本候选并保留诊断，不改旧站。
4. **数据对照**：按所选模式比较卡／描述／答案数量和逐项原值、null、类型、绑定、置信度、来源及条件引用；sample/full 协议分开。布局变化不得升格游戏语义，不以抽样替代 Web 已交付的全量语义证据。
5. **静态与 Node**：明确候选目标及报告路径；语法、模拟 DOM／分页、inline 数值守恒各有回执。失败必须标明本次 run，不能拿遗留 validation 当本次通过。Node 用既有版本，不安装升级。
6. **真实浏览器**：在独立候选服务下核完整卡图／头像、待译边界、CID350的25/27.5与条件跳转、分页／搜索／返回、390px；inline 如被选用则核对应修订的句序、×C和来源标签。不得沿用旧截图冒充新验收；不抢占8768、不重启现服务。当前入口／服务根切换属于 B03，本轮不推进。

## 失败与回退

来源漂移、写入旧 audit／字典、媒体断链、未整合分片、语义差异或验证目标不明确即停止受影响候选步骤，保留候选和诊断，继续原服务。若未来由 Web 合入最小参数改动，只能处理本批且未被新工作修改的差异；有新的语义／frontend 写入交由 Web 合并，不整树覆盖或恢复旧快照。本轮尚无代码改动或候选数据需要回退。
