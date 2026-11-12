# B02 交接边界与待发送清单

**未向 Web、ZCode 或其他聊天发送。** 本文是用户及后续接收者可用的交接草稿；不是已取得交接。机读填写入口见 [handoff-template.json](handoff-template.json)，当前所有 owner 确认和运行开关均为空／关闭。

| 需要确认的事项 | 提供者 | 当前缺口 |
|---|---|---|
| 原阅读版或 inline 修订；full/sample/frontend/inline 模式；基线快照 | 用户确定产品范围，Web 说明各版身份与可交付状态 | 未选择；inline V3仍是独立试读产品，未自动取代原版 |
| 固定代码、README、原版 web、verify_pagination；选 inline 时加 inline build/verify/web | Web 主整合者 | 本地可读不等于固定交付；缺 B02 接收对象、交付版本与 owner 确认 |
| 四份语义／已审字典、reference_pairs及名字参考页；语义manifest/results/progress与最终验收身份 | Web 主整合者 | 当前部分哈希匹配可作证据，未逐包复验；需要整合后的交付集合，不能直接用未合并分片 |
| 数据构建 receipt、frontend receipt；选 inline 时 trial receipt与该修订验收 | Web 主整合者 | 旧数据代码哈希与当前 build 不同有后续前端改动记录，须分层声明；不能称所有文件同一代码版本 |
| 同版 cards、campaign指针及report、rules、ledger/metrics | 研究整合者，**仅当模式实际消费这些输入** | 当前 metrics 已是99bee2a1快照，reader仍是01c05f78；若重建全库必须交付选定同版输入 |
| 已有reader固定载荷及其完整性/版本回执 | Web 主整合者，frontend/inline旁路模式 | 可继承既有C18阅读快照，不必因此暂停C19或读取当前主线补洞 |
| 已用媒体的来源／缺失或局部标记、候选磁盘根与浏览器基址 | 媒体／服务实际负责者，或其已有明确版本交付回执 | 当前 `../pages/art`依赖服务布局；不能仅改site_output后声称可用 |

## 给 Web 的交接草稿

> B02目前只完成路径适配设计，没有复制、修改或运行你的代码，也没有改现服务。请说明原阅读版和 inline 当前修订各自的代码、frontend、数据及验收版本，列出适合交付的固定集合及仍在修改的内容。选定产品后，请提供该集合的清单/版本/必要哈希、数据build与frontend（及inline trial）回执、已整合语义字典/reference_pairs和相关语义结果身份，并确认收取窗口内这些选定文件不变。已有不可变版本可直接交接，不要求你停止整项任务；无需为了交接重跑prepare、merge、全库生成或全部语义审查。若存在未整合结果、主线版本不匹配或仍待用户选择，请明确保留为缺口。交接只是允许按选定版本准备独立候选，不授权改现站、切入口/服务或搬迁原件。

研究／媒体确认也只针对候选实际读集：full/sample的主线输入需同版；纯frontend/inline固定载荷旁路继承已有数据身份，不向C19索取未使用输入。收到交付后由B02整合者核清单、源码／数据／前端对应关系和候选真实写域；不以单条“完成”或哈希相等代替接收。

## 最小停止范围

现在无需停工。若所有者能提供不可变快照，后续交接也可不停主线；否则只协调选定交付集合的短暂稳定收取窗口，不暂停全 Web 或全 C19。收取中变化即停止受影响候选步骤、重新确认该集合，不覆盖原件，不抓取不同时间的 latest 拼成同版。

原路径继续保护：`scripts/skill_reader_preview/`（含inline）、`reader_full_20261106/`、`reader_semantic_20261107/`、`reader_inline_trial_20261107/`、正式pages/profiles/effect_ledger、参考原件和pages/art。候选源码副本、参数实现、站点构建与业务验证均等待上述交接；共享根入口和现用服务切换不在B02本轮范围。
