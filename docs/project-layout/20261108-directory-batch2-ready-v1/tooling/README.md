# 第二批整目录迁移工具：准备态

**仅准备、未物理授权、未执行迁移／联接／业务代码合入。** 工具是只读校验器；可审的未来命令单独保存在[机器执行手册](runbook.json)和[逐步命令](runbook.md)。只读PASS不是执行许可。

精确范围为 `output/single` → `projects/unpack/history/single`（3文件／4,131,868 B）与 `output/cache_full_20261015_v2` → `projects/unpack/data/cache/cache_full_20261015_v2`（95文件／118,170,246 B），共98文件／122,302,114 B。同E卷整目录rename，不复制载荷；只产生少量目录元数据、日志和回执。两旧根不补兼容联接、不重建为空目录。排除当前v3、5317归档、其他根、五个share_bundle联接和全部旧打包清理。

当前冻结[唯一源码前像清单](../source-inventory.json)SHA-256为 `e2aec985a2c7a8683bd786e9e37c1b573f3d8eabbde831dd1ada1511e45930c6`。清单包括98文件的内容／size／ID／mtime／nlink及全部目录ID；五个C14—C18 **v2** junction保留原ID、tag、精确原target。

## 读取与执行边界

- 校验器：[batch2_directory_move.py](../../../../scripts/project_layout/batch2_directory_move.py)。没有move、rename、junction创建、删除、业务import或shell执行；只允许独占创建指定的tooling JSON回执。失败不覆盖证据，flush／fsync后结束。
- [bindings.json](bindings.json)绑定校验器、手册、两候选脚本／patch、冻结库存／路径映射／保护观察基线、准备文档和夹具测试的SHA；改动后原预检／授权不再适用，不能静默绕过绑定。
- 准备预检允许每份live脚本处于精确基底或精确候选SHA，分别记录状态；物理前每道gate强制两份live均等于已批准candidate。业务补丁合入由共享写域所有者执行，校验器不合入。
- `protected-before.json`的P／v7／四份plan及binding是冻结证据，不得漂移；rules／latest／root文档等现用文件只观察哈希和身份，不全局锁定，允许其所有者合法更新，不把并行主线合法变化误判成全仓违规。
- 每个源／目标祖先先逐级lstat真实目录，无reparse；缺失只接受FileNotFoundError，权限或IO错误直接停。目标必须不存在，包括悬空junction也算冲突；同E卷；不跟随内部reparse。
- 全98来源SHA只在一次预检中计算；未来授权窗口内另产一份全98新预检并绑定路径／SHA／时间，不覆盖今天的准备回执。每根移动后分别全3／95 SHA核验一次；每次alias阶段只核95文件ID／metadata、target根目录ID与三个小锚点（decode_report、tables、helper.raw），不反复读57MB records。

## 一次主持交接与单独物理授权

未来同一份主持交接须覆盖两根无写入、五个v2入口共同局部窗口、共享代码／导航写域释放，以及两份路径适配补丁的批准。用户还须明确授权物理移动与五入口顺序切换；当前均未取得。模板[authorization-template.json](authorization-template.json)的false／空值不能通过gate。

授权回执还绑定：审定bindings SHA、窗口内新source-preflight回执路径与SHA、用户授权来源、主持交接来源及有效窗口。checker只验证这些必要字段和身份，不能代替真实用户／主持授权，也不能证明全机无句柄或无未知写入。每次mutation前仍须保持局部所有者窗口；不暂停或干扰当前主线。

未来顺序：所有者最小合入两份批准候选，增量合并两处局部ignore（不改root .gitignore，不覆盖已有history规则）→ 窗口内新只读预检 → 核验用户物理授权回执 → 整目录rename single并核3文件 → rename v2并核95文件 → C14到C18逐个创建同父next、核验、旧formal改previous且立刻核原ID／tag／oldtarget、next改formal并经alias核验 → 最终只读复核 → 指定所有者最小合入导航候选，保留并发内容。导航不得提前声称移动成功。两次rename存在正式入口空档，**不承诺原子交换**。

五个 `cache_full_20261015_v2.batch2-20261108-previous` 保留原junction作为回退证据，指向已不再存在的旧根，最终不自动删除。任何previous清理均不在本批默认范围。错误立即停止，按[精确失败／恢复清单](recovery.md)检查；不得盲重跑或恢复旧根来掩盖失败。

## 本轮命令与证据

仅执行只读预检：

```powershell
& .\.venv\Scripts\python.exe -B scripts/project_layout/batch2_directory_move.py preflight --receipt docs/project-layout/20261108-directory-batch2-ready-v1/tooling/preflight.json
```

回执[preflight.json](preflight.json)记录两根98SHA、完整ID／metadata、五原junction与名称冲突、代码状态及保护观察。本轮不运行手册中的未来setup／mutation。测试[源码](test_batch2_tool.py)只在本目录新小夹具内做同卷rename／junction，保留夹具；不触碰98原件，不复制大payload，结果见[test-result.json](test-result.json)。小夹具junction创建在沙箱内被拒绝后，仅该9字节夹具测试获准以提升权限运行并通过；不外推真实业务mutation已获授权。

测试范围为小夹具与只读预检；真实98文件的整目录rename和真实五入口交换均 **NOT_EXECUTED**，未知全机句柄与原子竞态保护 **NOT_PROVEN**。下一步交独立审查，不能因准备完成自动进入执行。
