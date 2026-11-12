# v1 旧缓存目录迁址记录

状态：Sol 执行完成，主聊天独立验收通过，见 [验收回执](acceptance.json)。其他批次未启动。

本任务仅移动 `output/cache_full_20261015/` 整个真实目录至 `projects/unpack/data/cache/cache_full_20261015/`，不改变目录内字节。`output/cache_full_latest.json` 仍指向 v3。历史 JSON 的 `json_file` 保留旧来源字符串；读取这些历史字段时，按 [path-map.json](path-map.json) 在外部映射物理路径，不回写历史报告。

迁移前持久化 [before.json](before.json)：88 个文件各自相对路径、大小、mtime、SHA-256，目录项及 12 个保护锚点哈希；[readme-before.md](readme-before.md) 是项目导航页的前像。[check_move.py](check_move.py) 是本次一次性前后核验脚本，不执行移动。`preflight.json` 记录第二次稳定检查，`verify.json` 记录搬迁后检查。

实际执行：从仓库根运行 `& .\.venv\Scripts\python.exe -B docs/project-layout/20261108-move-cache-v1/check_move.py capture`，间隔数秒后运行 `preflight`；确认源和所有已存在祖先均为同盘仓库内真实目录、目标不存在后，PowerShell 以 `[IO.Directory]::Move($source,$target)` 对两个已核实的精确绝对路径整目录移动。迁移发生于 2026-11-08 02:33:52—02:34:00（Asia/Shanghai）之间；之后运行 `verify`。全部 88 文件、73,835,561 字节、mtime、目录项和 12 个保护锚点一致，源不存在；88/88 文件被局部 `.gitignore` 忽略，88/88 外部路径映射可定位，导航页新链接存在。

## 回退条件与方法

仅在目标清单与 `before.json` 的每个文件 SHA-256、大小、mtime 和目录项再次完全一致，且旧源路径仍不存在时，才允许把这个**单一目录**同盘移回。旧源路径若已被重建（包括文件、目录或联接），必须拒绝覆盖并停止，先查明新内容归属。回退前也要检查目标及各级祖先仍为真实目录、同盘且没有明确写入者；不能停其他任务来制造条件。用 PowerShell `Move-Item -LiteralPath <精确目标绝对路径> -Destination <精确旧源绝对路径>`，不使用复制后删除。回退后重新核 88 文件及保护锚点。

项目导航页可能在迁移后由他人继续修改；回退时**不得**直接用 `readme-before.md` 覆盖。应重读当前 `projects/unpack/README.md`，仅定向修正本任务的迁址行，并保留后来改动。局部 `.gitignore` 与本记录页可先保留作为诊断，不要求删除。此次只写回退方案，不实际往返搬迁。

边界：定向静态引用核对与进程列表未发现明确 v1 运行消费者，不等于证明所有动态依赖均不存在；CIM 进程查询不可用，也不声称全机无人使用。若未来有旧路径动态读取，使用外部路径映射或在对应新任务中修消费者。
