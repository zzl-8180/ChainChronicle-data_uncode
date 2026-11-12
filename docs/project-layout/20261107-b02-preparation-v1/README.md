# B02 独立准备：范围、准入与 Web 交接

结论：**独立准备已完成；B02 尚未进入实现或候选运行，状态为 NOT_HANDED_OFF。** 三个 Sol medium 子代理只读调查，主聊天整合；本轮只新增本目录文档与自身任务卡。[机读准入](readiness.json)将设计完成与运行门槛明确分开。

## 已推进的独立准备

- [命令读写矩阵](command-io-matrix.md)／[机读矩阵](command-io-matrix.json)：覆盖16个入口或模式，含失败分支、顶层import副作用、默认路径及新增inline链。
- [最小接口与候选验证设计](interfaces-and-validation.md)：区分full、sample、frontend刷新和inline；明确代码／数据／翻译／媒体／输出／验收路径，以及回退方式。所有接口均为拟议，未改CLI。
- [交接边界与待发送草稿](handoff-request.md)／[未填写模板](handoff-template.json)：说明Web、研究、媒体各自需要交付什么，按所选模式缩小读集与稳定窗口；未发送给其他聊天。
- [本地观察与代码身份](observations.json)：保留时间边界和已知版本差异；不是冻结快照或owner签认。[文档整合回执](validation.json)仅验新文档与静态范围。

## 这次新增的关键发现

1. **Web又有独立inline试读版。** 调查窗口02:35—02:36内任务卡由V2更新到V3，随后记录完成、等待用户比较。其build/verify/web与原版分开，旧矩阵未覆盖；阶段完成不能视作B02已移交。见[inline任务卡](../../tasks/20261107-reader-inline-trial.md)。
2. **主线与阅读快照已不同。** reader/inline回执仍为C18 `01c05f78-cf9451c6ff47fcfb`；本次读到的metrics为`99bee2a1-cf9451c6ff47fcfb`。未据单份metrics验证当前主线事务收口，也不沿用旧C19卡“正式生成0次”作为当前事实。full/sample需要选定同版输入；frontend/inline如果只消费Web交付的固定载荷，则无需读取或暂停C19。
3. **现有参数不能保证独立运行。** sample不传output仍写默认full目录；sample与frontend-only可同时传且后者优先；Translator仍固定读旧reference_pairs和源码旁字典；full的媒体URL固定`../pages/art`，原前端还会拒绝http(s)图片。接口必须分别处理磁盘路径、浏览器基址与服务根。
4. **“验证／审查”可能先写再失败。** merge collect先写review_progress，review_report又隐式调用它；prepare_numeric、audit_answer_inventory和verify_regressions各有固定写域，后者import即执行。verify_full即使fatal也写validation；inline verify读的是源码planner，并非自动核验候选站输出planner。未适配的入口全部不调用。

两份旧reader任务卡确有已完成阶段：[语义复核](../../tasks/20261107-reader-semantic-review.md)、[阅读层级](../../tasks/20261107-reader-reading-layout.md)。本地部分字典／参考／前端哈希与旧receipt匹配，也有新增frontend-only源码与旧数据receipt不同的合理分层记录；这些都需要明确版本交付，不能由本轮代签。未核实时聊天身份、未逐卡或逐分片重验，未连接服务。

## 需要先交接的部分

先选原版还是inline，以及数据重建还是固定载荷旁路。Web需交付相应固定源码/frontend、译文与语义结果、reference材料及数据／前端／试读回执。若选full/sample，研究owner再确认所用同版cards/campaign/rules/ledger；媒体约定按实际引用集合确认。

**当前无需暂停任何任务。** 候选复制、路径适配实现和业务运行等待交接；能提供不可变版本则无需停主线，否则只协调选定文件的稳定收取窗口。未启动服务、构建、验证或任何其他批次，未改共享根入口、旧方案、B00/B01成果或移动冻结原件。

原批次范围仍以[修订方案](../20261106/batch-plan.md)的B02为准，前置[B00回执](../20261107-b00-v1/validation.json)已存在；B01限定通过不替代Web版本交接。当前入口／服务根切换属于B03，不随本次准备启动。详细协作记录见[本任务卡](../../tasks/20261107-project-layout-b02-preparation.md)。
