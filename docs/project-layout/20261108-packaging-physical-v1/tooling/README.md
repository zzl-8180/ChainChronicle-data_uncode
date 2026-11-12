# 保留材料迁移工具

当前执行时间修订：用户在全量清点完成后明确要求“不再等到13:00，清点完成后开始”。起点保守固定为收到该指示后UTC 2026-11-08 04:47:51，结束仍为UTC06:00（北京时间14:00）。以 `../authorization-immediate-amendment.json` 及 `../run-immediate-bound/` 为执行绑定；下文原13:00起点仅为最初约定，已被此修订替代。

`scripts/project_layout/run_retirement_preservation.py` 只处理冻结表中 5317 个保留文件的逐文件同卷 rename；1607 个删除候选和 11 个原位文件仅核身份，不移动或删除。工具不建立、改名或删除 junction，不改共享根文件，不运行旧模块或生成器。

父聊天负责临窗核使用者、授权、五入口状态和后续 junction 操作。此工具的 `MOVE_VERIFIED` 仅表示保留材料移交通过，不表示支线退役、入口切换或允许删除。

```powershell
$run = 'docs/project-layout/20261108-packaging-physical-v1/run-20261108-unique'
& .\.venv\Scripts\python.exe -I -B scripts/project_layout/run_retirement_preservation.py preflight --repo . --run-dir $run
# 保存上一步打印的 source-hashes.json SHA，审阅后原样传入：
$binding = '<preflight打印的64位SHA256>'
& .\.venv\Scripts\python.exe -I -B scripts/project_layout/run_retirement_preservation.py move --repo . --run-dir $run --preflight-sha256 $binding
& .\.venv\Scripts\python.exe -I -B scripts/project_layout/run_retirement_preservation.py verify --repo . --run-dir $run --preflight-sha256 $binding
```

preflight 可以窗口前执行，只读业务文件并在全新 `physical-v1/run*` 目录创建独占回执。它绑定完整清单、批准 overlay、工具本身的 SHA；九根 6788 项和额外 147 项重新无跟随枚举，保留文件全量实读 SHA，源路径与打开句柄前后稳定；原位项仅记录小 metadata。P/v7 和四 plan binding 原字节核验，同时捕获四共享根、根 `.gitignore`、规则和 current pointer。

move 再核全集合、所有身份/保留内容与目标，UTC `2026-11-08 05:00:00 <= now < 06:00:00` 才允许开始；没有等待开窗或 CLI 时钟覆盖。move 开始时历史根须仍不存在。逐文件最终 scope、reparse、目标不存在、同卷和源身份检查后，INTENT flush/fsync、Windows 非覆盖 `os.rename`、目标 SHA/metadata/fileID 核验、DONE flush/fsync。每次 mkdir 和 rename 紧前再核时间；到期或失败写 PAUSED，保留已完成状态，无自动回滚、覆盖或续跑。任何已有 move journal 都拒绝再次 move，父聊天须依据 INTENT/DONE 和实际路径人工接管；不要新建回执伪装从头执行。

verify 可在窗口后只读执行：5317 旧 source 必须消失，目标逐文件 SHA、大小、mtime、fileID、nlink、mode、attributes 必须一致（rename 可改变 ctime，原 ctime 仍记录）。新历史树无跟随枚举须精确等于5317批准target，不得有额外文件。1607+11 项完整 metadata 和保护文件必须不变；旧根不得新增或漏项。不会读取旧 source 内容作为 fallback。所有 JSON/JSONL 均独占创建，不覆盖已有证据；重复 verify 会拒绝覆盖 `verify.json`。

合成测试仅在此 `tooling/fixtures/<unique>/` 下生成少量新文件；通过 Python 参数注入时钟和 rename 故障，不动业务5317，也不复制库：

```powershell
& .\.venv\Scripts\python.exe -I -B docs/project-layout/20261108-packaging-physical-v1/tooling/test_preservation.py
```

测试保留夹具及唯一结果 JSON，不删除旧文件。当前沙箱拒绝在新夹具中创建真实 Windows junction；祖先拒绝测试注入 Windows reparse lstat 属性，执行真实祖先检查代码，不冒称已实测 NTFS junction。失败尝试及夹具保留；这些夹具不在批准业务根中。
