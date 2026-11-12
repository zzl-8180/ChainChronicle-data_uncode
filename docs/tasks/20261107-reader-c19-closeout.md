# 阅读页 C19 接入与条件收尾

- 状态：实施与验收完成，第三方材料待审；2026-11-07；本 Web 聊天为整合者。
- 用户授权：按收尾调研方案接入 C19、全面筛查剩余条件、保持主线独立，验收后准备第三方材料。
- 允许写入：scripts/skill_reader_preview/、output/character_skills/reader_full_20261106/（可重建展示）、独立 work/reader_c19_closeout/、本任务文档及送审/证据交接文档。主线 pages/profiles/effect_ledger 和旧审查报告只读。
- 分工：c19_adapter 独占 C19 迁移脚本与 build.py 必需接线（不运行正式输出生成）；condition_closeout 独占全剩余条件筛查脚本与独立 work/reader_condition_closeout/（不写正式旁注）；父代理整合、正式生成、前端、README 与验收/材料。各代理不得覆盖其他人的改动。
- 验收：C19 133行407答案接入、45同句未知保留、原值/来源/条件正确；全部剩余条件项有逐项结论，只有充分证据才升色；旧未解范围可追溯；前端和数据同版本；主线哈希不变。
- 第三方：本轮准备冻结材料与提示词，不把内部自检当独立审查，不自动发送或开启其他聊天。

## 已完成的数据验收

- C19基础快照：99bee2a1-cf9451c6ff47fcfb。2,236卡、41,665描述、35,811源答案。新增133行407答案全部句内，同句45未解效果保留。
- 原35,404答案的文字/数值/条件/可信度不改；9卡16个来源指纹按已审主线变化接入。139张变化卡逆向重建原整卡SHA通过，5项负向迁移守卫拒绝。
- 原760紫色全部逐项筛查；474项通过数值、效果绑定、选择条件三轴复核升为金色推断。全部2,222项补充评估中1,936金色、286紫色；不是主线新加474答案，不代表实机验证。
- 286保留：记录与效果对应200、条件及对应5、逐人增长70、位置/形态7、具体卡面2、回复与解除异常对应2。7项仅条件缺口为20811×3、30204×2、8371×2。
- 40项计数随机分支明确写随机选档，不转换成固定档或实际施放概率；使用次数仅当前控制器生命周期；法珠采用对应预测计数和缓存执行路径。
- 全库验证通过1,544,616检查，4,437图片引用；C19专项、2,222评估、760条件清单验证通过。程序校验与浏览器抽验分别留回执。

## 本轮反复遗漏的原因与防复发

1. 不能仅看旧绑定字段或旧颜色。必须从当前主线原表、真实父子引用、完整charainfo竞争集合和消费者证据重新判定；选择、效果绑定、数值分别判断。
2. 条件补证不能只传给追加候选。浏览器抽验10213发现旧值仍用A：完整集合已经核验，但回执只导出目标候选父。补充完整已证父映射，前端核父记录全等后统一标注原值/候选条件；不借此改变数值可信度。
3. 历史审查是当时快照。新评估写独立audit，不覆盖final5/独审；本轮送审冻结源码和输入哈希，版本漂移应指出具体范围。
4. 基础快照和Web补证分母分开。页面“已解”仍按主线，补充推断另列；不得把网页升色直接写进主线账本。

## 后续更新与主线独立性

Web可随着主线更新。当前提供只读sync_status.py --check预检：0已对应、2有变化待审、3输入未完成或不一致。没有后台轮询，也不自动批准未来周期。

实际更新顺序为：主线完成快照→预检及差异审定→独立目录重建→旁注和页面验收→保留旧版并切换。新周期若无法核验语义变化，保持旧网页。C19精确迁移不是任意未来版本的通行证。

主线无需依赖Web；可接收的结构绑定、HP/Chain、完整选择、次数/地形/法珠时点及稀疏字段证据已整理为20261107-reader-mainline-evidence-handoff.md，由主持决定如何独立验证和正式接收。本轮不修改主线、不发送消息、不自动启动新周期。

第三方提示词：20261107-reader-thirdparty-review-prompt.md。准备材料状态必须为PREPARED_NOT_REVIEWED，不能将内部验收说成第三方通过。

## 最终交付

- 正式入口：output/character_skills/reader_full_20261106/，本机 http://127.0.0.1:8768/reader_full_20261106/ 。旧8767服务若仍运行并指向原目录，也读取同一份新页面；本轮实际浏览器验证8768入口。
- 原版备份：output/character_skills/reader_c18_before_c19_20261107/。候选目录已切换，不再单独保留stage副本。
- 新验收：reader_full_20261106/audit/c19_closeout_20261107/。正式主线2,240文件前后SHA完全不变；所有检查及页面最终版本可追溯。
- 实际浏览器：220新增答案、10213原值/强化次数、20332 HP顺序、20627随机选档、20811未知位置、20622等级数列对称间距；2,236角色索引与搜索；390px无页面横溢；卡面近2:3；无控制台错误。是代表性浏览器验收，不冒称逐卡视觉审查。
- 完整父条件映射补齐394父，其中98普通原值父，覆盖185个已准入cohort；全库复核父记录全等，条件不会只到追加候选。原760分母、474升色与286保留不变。
- 第三方材料：output/character_skills/review/reader_c19_closeout_prepared_20261107/。manifest记录全部页面/证据、主线保护与源码哈希，source/、documents/保存小型快照；大数据和媒体依赖原项目目录明确定位。不是可独立安装的完整解包发行包。
- 第三方未开始、证据未发给主持。只准备提示词和交接，不改变主线生产职责。

复核命令（独立审查请对隔离副本运行，不覆写正式或历史回执）：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/sync_status.py --check
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_c19.py --output <隔离网页> --baseline output/character_skills/reader_c18_before_c19_20261107
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_full.py --output <隔离网页>
node scripts/skill_reader_preview/verify_confidence.js <隔离网页> audit/c19_closeout_20261107/confidence_validation.json
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/verify_condition_closeout.py --output <隔离网页>
```
