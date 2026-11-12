# 第三批双目录只读门禁：准备态

本目录仅准备执行材料；**没有物理授权，未执行目录移动、junction 创建／改名或业务导航合入**。选定两棵：`output/git_sync_20261024` → `operations/records/git-sync/20261024`（6 文件／29,828 B），`output/project_overview` → `operations/records/project-overview/20261020`（5 文件／69,618 B）。合计 11 文件／99,446 B，无子目录；C14—C18 各 2 个正式 junction 共 10 个需按同一窗口切换。

只读 [batch3_gate.py](batch3_gate.py) 使用 SHA 绑定的第二批 `batch2_directory_move.py` 的祖先和精确树核验函数，不复制 NTFS 检查实现。它读取 [source-inventory.json](../source-inventory.json) 的 11 个 SHA、文件／目录 ID、mtime、nlink、10 junction ID/tag/readlink，并验证目标无冲突、同 E 卷、祖先和树内无 reparse、next/previous 名称空缺。每个门禁步重读全部 11 SHA（总不足 100 KB）。`protected-before.json` 的 P/v7 与四组 plan/binding 精确 SHA 必须保持，其余并行主线文件只观察，不锁定。回执只能用新名字在本目录独占创建并 fsync。

[tool-bindings.json](tool-bindings.json) 固定本工具、只读 helper、冻结清单／保护基线、命令单和整合者冻结的八项 path-map／navigation／ignore 候选 SHA。变更任一文件须经重新审查与重新绑定；今天的 preflight 不能代替未来窗口内 fresh preflight。只读 PASS 不是执行授权。未来 gate 必须取得另一份真实用户物理授权、10 junction 的一次 owner 窗口和两根无写者交接，并绑定窗口内新 full-11 preflight 的路径／SHA／时间。`authorization-template.json` 明确为 false，直接使用必被拒绝。

未来步骤见 [runbook.ps1.txt](runbook.ps1.txt)、[说明](runbook.md) 与 [失败恢复](recovery.md)。顺序为建立必要空父目录、两个同卷原子整目录 rename，再逐个创建 next／验读、正式名改 previous 并核旧 ID/tag/readlink、next 改正式名并核新 ID；保留所有 previous。每步 durable INTENT → 当前状态只读 gate → 紧邻动作授权窗口检查 → 单次原语 → 新状态只读 gate → durable DONE。step 0..32 的状态对应两次根移动及 10×3 次 junction 操作。任何错误停住，按 WAL 和当前状态核验，不盲重跑。

本轮只允许运行：

```powershell
& .\.venv\Scripts\python.exe -B docs/project-layout/20261108-directory-batch3-ready-v1/tooling/batch3_gate.py preflight --receipt docs/project-layout/20261108-directory-batch3-ready-v1/tooling/preflight-final.json
```

实际执行命令仍须独立审查和明确授权。校验器不能证明全机无句柄，也不能使两次 junction 改名成为原子交换。
