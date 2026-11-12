# 六个第三方历史审查入口：未授权的处置提案

状态：**PROPOSED_ACCESS_RETIREMENT_NOT_AUTHORIZED**。这里只列梳理结果和待确认契约；不修改、删除、改名这些入口或其隔离副本，不运行旧审查。

旧reparse索引中有六个不同于C14—C18常规入口的对象，父目录均为 `work/review_p2b5_thirdparty/iso/output/`：

| basename | 指向的候选迁移根 |
|---|---|
| base_master | output/base_master |
| boss_heal | output/boss_heal |
| cache_full_20261015_v3 | output/cache_full_20261015_v3 |
| card_comparison_cid30236 | output/card_comparison_cid30236 |
| char_roster | output/char_roster |
| reference_analysis | output/reference_analysis |

它们属于第三方历史独审的隔离输入，不能按一般运行入口默认重定target或改名为previous。即使目标文件内容不变，改写这些冻结入口也需要先证明符合保护契约；主持普通生产写域的移交不自动包含该权限。

供一次总交接审定的低写入方案是：

1. 原六个alias对象的路径、ID、tag和target原样保留，原独审、隔离副本、日志和回执不改；不复制大型payload。
2. 在新的外部维护映射中登记其旧逻辑target到迁址后新实体的解析，使用新只读入口验真并读取材料。
3. 原物理target迁走后，六个旧alias会成为不可直接读取的停用证据；不再承诺旧alias直读或原审查现场精确重放。**这是访问能力退役，必须明确披露并批准，不能声称全部历史入口仍可用。**

一次主持总交接须确认历史材料保护接管者及可接受处置，最终用户物理授权须明确包含这一项能力变化，才能把六个相关根放入最终整组迁移清单。若不获准，就继续完善不破坏保护契约的其他方案，整个统一范围保持NOT_READY，不偷偷先移其余根再称“一次完成”。

若希望原alias本身继续可读，必须另行审定相应入口适配／兼容契约；本包不自动创建旧output兼容junction、不改冻结alias、不松开原独审保护。旧索引的六条不是当前身份验收，最终仍须逐条lstat/readlink、确认实际使用者与保护范围。
