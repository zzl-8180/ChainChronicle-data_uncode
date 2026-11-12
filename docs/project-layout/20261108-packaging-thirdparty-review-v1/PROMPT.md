# 独立第三方审查提示词

用途：由用户自行交给外部第三方 AI。本聊天不代建审查对话。若第三方无法访问本地路径，应先列缺少的文件，由用户提供；不得声称已读本地材料。

请对“整条打包支线退役、拟删除材料是否删错”做独立第三方审查。

项目：E:\代码项目\锁链战记数据解包
本轮审查业务文件只读，暂不迁移、删除、切换联接、修改共享根或修复代码。不运行旧打包、清理、恢复、主线生成脚本，不联系或停止其他对话。你可以仅在 E:\代码项目\锁链战记数据解包\docs\project-layout\20261108-packaging-thirdparty-review-v1\ 新增 REPORT.md、verdict.json 和必要小型证据；自己的任务卡可用 docs/tasks/20261108-packaging-thirdparty-review.md。不得覆盖提示词或其他已有报告。请独立取证，不把已有 Sol/Astra PASS 当成你的结论。

先读 AGENTS.md、HANDOFF.md 当前入口，然后完整阅读以下材料（以下路径均位于项目根）：
1. docs/project-layout/20261108-packaging-runtime-ready-v1/README.md、acceptance.json、execution-overlay.json。
2. docs/project-layout/20261108-packaging-full-retirement-v1/README.md、full-disposition.jsonl、integration.json、terminal-survivors.json、review.json。
3. docs/project-layout/20261108-packaging-full-retirement-v1/repro/README.md、repro-disposition.jsonl、verified-source-pairs.json、storage-resolution-proposal.json。
4. docs/project-layout/20261108-packaging-full-retirement-v1/retained/README.md、retained-disposition.jsonl、extra-disposition.jsonl。
5. docs/project-layout/20261108-packaging-runtime-ready-v1/runtime/ 和 handoff/ 下的位置映射、验证回执、联接交接、切换回退方案、共享导航补丁及基底。
6. scripts/project_layout/retirement_runtime.py；按需查真实消费者和原保护记录。

当前提案：6,935项，拟删除1,607文件、4,979,429,886逻辑字节；保留迁址/归档5,317项，冻结清单108,003,893字节，本轮导航增加561字节后为108,004,454字节；11份跨任务历史文档原位保留。数字只是审查对象，不是正确性证明。早先28项仅为子集，不要只审28项。

重点检查：
A. 逐项删除是否误伤。将1,607项区分为已证明重复副本、明确退役的旧包/代码、以及放弃旧实验精确重放的生成物。尤其核1270份双端SHA来源证据、173份非逐字节重复生成载荷的退休理由、136份交接readback重复项。不能仅据名称、日期或“有新版”判可删。明确任何唯一研究结果、恢复输入、版本前像、必要失败诊断是否误列DELETE。
B. 终态存活来源。独立核1406条survivor链最终不被删除；源如果也要迁址，应解析最终target。独立检查路径集合覆盖、重复/大小写冲突、拟迁目标冲突、reparse、硬链接和当前身份漂移；当前身份以execution-overlay承接导航修改，不改冻结full-disposition。
C. 其他分支真实依赖。区分正常生成/resume/verify/ledger、历史研究/事故恢复、冻结打包重放。核五个C14—C18隔离入口、139项研究交接、两版技能manifest、P_preservation第222项source_existing_protected。该项必须保留12,340B、SHA b74e4681d492fbf0f7258e138669abf91bba23c27e091f865deae428ec4e9ee2 的旧源码，不能用12,508B现版替换。旧P/v7/四保护plan及历史source身份保持原样。
D. 新维护入口archive模式是否真正读取新位置、缺件是否拒绝而非fallback旧根；研究命令是否显式--bundle和独立--output。两旧技能ZIP本来已缺失，metadata查询不能冒充恢复角色/HTML。只读保护项核验不能冒充完整历史postcheck。
E. 联接交接是否安全。五个精确入口均只允许受控交接；新根、祖先和嵌套payload/P不能通过二次联接回旧根。检查迁移保留材料验真→五入口逐个切换及验读→最后处置旧source的顺序；两rename不是原子交换。旧target迁空后不能盲目回退，不得使用常驻output兼容junction冒称整支清完。
F. 范围/能力损失。六成功旧包的整包重放与恢复放弃是否充分披露；源码17份157,899B前像是否真可回退。共享原始APK/raw/当前缓存/主线/媒体/vault以及11跨任务历史文档不得随支线删除。原位保留历史文档并非保留活跃打包分支。
G. 导航及授权。四共享根补丁尚未合入、五入口owner尚未接管、新归档根尚不存在；准备PASS不代表实际迁址完成或现在可直接删。当前主持主线不应全停，窗口仅限五历史入口。审查不得替用户批准删除。

优先复用既有取证，针对疑点补查，不重复解包/全库生成。不要为审查复制大型ZIP/APK，不跟随junction递归枚举。可以只读执行已审过的检查器；会覆盖原verification.json的测试不得直接重跑，可在本报告目录隔离取证，保持原交付记录不变。不得执行任何迁移、清理或删除命令，包括为了模拟缺件而移动真实文件。

交付：
- REPORT.md：先给 PASS / PASS_WITH_EXPLICIT_SCOPE_LIMITS / REQUEST_CHANGES / BLOCKED，再列每项问题的严重度、具体路径/行号或清单条目、证据、影响、最小修正。
- verdict.json：结论、阻断项、已核/推断/未核范围，分别判断“删除清单正确性”“确认包是否完备”“是否已具备实际执行条件”。
- 不要因为owner交接尚待落实就误报为已发生损坏；也不要把准备状态当作执行授权。发现误删风险时先报告，不自行修复。
