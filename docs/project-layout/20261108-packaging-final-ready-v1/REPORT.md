# 打包支线退役：统一整合及最终删除前回执

结论：**已完成本轮导航整合、删除前准备和Astra复核，阻断0；1,607项真实候选删除0，等待用户单独最终删除授权。** 主持交接与导航事项已闭合，无需再逐步请求主持操作。此前物理报告中的“待主持整合”是当时状态，原件保留，以本轮交接和当前回执承接后续。

## 1. 实际整合差异

以主持当前未提交的四根文件为基底，全部保留其真实迁移导航，不套用准备态补丁、不回滚。基底和前后SHA见 [navigation-base.json](navigation-base.json)、[root-integration.json](root-integration.json)；本轮实际增量见 [root-integration.patch](root-integration.patch)。

| 文件 | 本轮相对主持交接的增量 |
|---|---|
| AGENTS.md | 未再修改；第8节与HEAD逐字一致 |
| 根README.md | 未再修改，保留真实迁移和只读维护入口 |
| HANDOFF.md | 仅增加1条退役事项统一整合任务入口 |
| STATUS.md | 仅在8个历史段落后补归档范围限定；原数字、路径和历史结论保留 |

STATUS补注明确：13,385文件／3.30 GiB、ZIP容量及A／B／C完整包是当时历史记录；新历史目录仅保留批准的材料，旧ZIP未迁入，不是当前完整包领取位置。八段原行号为24、74、76、106、346、350、352、360。

相对主持基底仅增加17行；去除本轮新增行后，HANDOFF／STATUS与交接基底逐字节相同。AGENTS／README与主持基底SHA相同。现有四根相对Git HEAD的41行新增／14行删除包括主持原有修改，不能误算为本轮全部修改，也没有暂存或提交。

## 2. 引用、入口与主线边界

- 四根共391个本地Markdown链接，缺失0，链接指向DELETE候选0；模拟删除批准集合后无新增断链。比主持的390个多出的1个为统一整合任务入口。见 [root-links.json](root-links.json)；`git diff --check`通过。
- 三个新历史根均为真实目录，祖先无未声明reparse。五正式入口仍为新历史根及原已验收fileID；五previous保留原ID、mount-point tag及旧target，仅作停用证据；五next均不存在。
- 沿用已绑定的5,317项／108,004,454 B物理独审及五入口各142文件验读，不重复迁移、切换、全量hash／stat／扫描5,317项，也不重复五入口内容检查。本轮只核入口结构、关键归档身份和删除前必需的archive内容门。
- AGENTS第8节和C19／Web边界保留。规则仍294键，SHA `cf9451c6ff47fcfb2707a845a799839b352acc10180c1ebc559f852a93affe67`；C19 campaign `99bee2a166e5ec5f9c03ac97b555d4ada2f6f30d1535258add16bc64c7227c66`、snapshot `99bee2a1-cf9451c6ff47fcfb`，133卡／133行／407答案、35行45项未知及4行split_flags的既有记录未改。历史C19 manifest保留原状态，不用其早期pending文字覆盖后续R01 CLOSED结论。见 [mainline-preservation.json](mainline-preservation.json)。
- P/v7、四plan及binding、根ignore等保持原冻结身份；17份小型保护文件通过，四共享根采用本轮真实新基底。另对旧保护清单中47份冻结方案／审查／证据文档重核SHA，全部一致，见 [frozen-documents.json](frozen-documents.json)。失败日志和原审查未覆盖；保留材料完整内容继承既有独审。
- 不接管参考分析／UI／reader，未改主线源码、规则、答案、账本、profiles、正式pages、latest、其他junction、输入或vault。未运行旧打包／清理／恢复／冻结verifier、生产对账或主线生成；主线不需停工。

## 3. 本轮真实删除前准备

2026-11-08北京时间13:43执行一次完整archive模式内容门：**1,406／1,406匹配，失败0**，包括1,270对外部替代者和136对迁址payload；87项外部替代者为合法多链接，未混同待删源的单链接要求。真实读取1,880,958,800字节（含证据），不是旧current报告、RAM模拟或旧根fallback。报告：[archive-full1406-preconfirm.json](archive-full1406-preconfirm.json)，SHA `7071a5ad5a73c2be68ee026d35b53ffe94848d5a0ea94423a9285fd10e9f91cb`；[真实退出码0](gate-invocation.json)。

只读prepare于13:54:02—13:55:09执行，退出0，见 [prepare-exit.json](prepare-exit.json)。结果为 `PREPARED_PENDING_FINAL_USER_AUTHORIZATION`：

- 精确1,607个冻结DELETE source，逻辑4,979,429,886字节（约4.98 GB／4.64 GiB）。全部当前普通单链接，源身份、祖先和长度上界通过；逐项新读SHA，与已有冻结SHA者一致。
- 1,406项有冻结SHA和内容替代链；其余201项为28项旧代码／ZIP及173项放弃精确重放载荷，记录本轮源SHA，不声称其有survivor。
- 旧范围无跟随枚举精确剩1,618文件＝1,607候选＋11原位材料，无未知文件；11项原位身份保持。
- 保留材料、previous、所有目录和未知项均不在删除清单内。未来只允许这1,607个source，不能按目录／通配符扩大范围。

正式清单：[delete-manifest.json](prepare-20261108/delete-manifest.json)，SHA-256 **`204ea4ada31f9e8076f3fabb168434814ea4865322fecff805c27b947f73f6e5`**。

准备报告：[preparation.json](prepare-20261108/preparation.json)，SHA-256 `c788efe3b556b6e3c94102e290300e29a6ac228733d83d9a4350c0917ababaa6`。按旧根分类见 [delete-scope-summary.json](delete-scope-summary.json)，汇总见 [prepared-summary.json](prepared-summary.json)。

## 4. 执行工具、测试与Astra复核

新增 `scripts/project_layout/retirement_delete.py`，SHA `b626ca21b832fb3a7b5b77aab7c01d8f61ec3392c51bc968ca3f5a8d1eba5add`。默认只读prepare，未来apply独立要求用户授权文件、明确SHA绑定、唯一运行ID和新有效期；没有递归删除、目录／联接清理或自动续跑。禁用模板保持 `authorized:false`，本轮没有创建真实可执行删除授权。

工具10项检查通过，包含只针对新建小夹具的真实Windows单文件句柄删除／拒写／错误SHA保留、紧贴API调用的到期拒绝、删除后PermissionError不记DONE、源／替代者漂移、错误授权、暂停和拒绝重放。实际业务apply没有调用，不能把夹具删除写成1,607候选已删。见 [测试回执](tooling/test-result-20261108T055306663810Z.json)及 [工具说明](tooling/README.md)。

Astra独立审查于13:59完成：**PASS_PREPARATION_WITH_EXPLICIT_SCOPE_LIMITS，阻断0**。实核清单集合／字节、1,607项当前metadata、1,406冻结SHA／terminal映射、201项分类、保护、根导航、391链接、入口结构、工具及10项测试；不重复大内容读取。审查中两项代码问题（最后API前时限、删除后不确定状态）和历史整包措辞均已修正。

独审：[astra-review.json](astra-review.json)，SHA `b8676e7c83d89bdf152be266f297a86bf815e02982e155fa69c506a348a856b4`。

## 5. 剩余授权和执行边界

**当前仅剩用户单独最终删除授权，以及真正执行时必须重新通过的即时检查；没有待主持继续操作的事项。** 本轮业务删除0、迁移0、联接变更0，没有提交／推送／发布。

用户如批准上面清单，后续由执行对话自行记录授权并运行已审工具：当次重新执行完整archive 1,406对门、源／overlay／reparse／单链接／漂移检查；逐组及逐项紧邻删除重新核实。仅短持当前单个退役源句柄，外部替代者不加排他锁，不阻止主线合法写入。发现漂移、共享冲突、过期或不确定状态即暂停，不盲重试，不宣称零竞态或永久有效PASS。

六个成功旧包及173份旧实验载荷删除后不保证精确重放；manifest、当前数据与源码前像不是完整ZIP备份。删除是永久处置，不能以改回previous恢复旧整包能力。

五previous、旧根／空目录、11原位项和5,317保留项仍排除；这些后置事项不随1,607文件自动获准。此前迁移窗口不构成删除授权，未来删除使用独立新授权。实际流程与失败处置见 [deletion-execution.md](deletion-execution.md)。
