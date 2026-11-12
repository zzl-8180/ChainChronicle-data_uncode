# 精确删除准备与独立授权执行工具

`scripts/project_layout/retirement_delete.py` 默认 `prepare`，本轮只运行此模式。1607文件/4,979,429,886逻辑字节以冻结完整表SHA `274c6cd5602b591047ce2b2c907b4e5d9bb33ff55b190b0bb8678ec586e82ef1` 为唯一范围。previous、空目录、未知项、5317保留材料、11原位材料均排除；没有递归删除、通配符、自动续跑或清理联接功能。

prepare 接收本轮真实 archive/full1406 PASS 报告及其明确 SHA，核报告完整映射、最近60分钟时间和当前双端metadata/祖先。随后逐1607源读取有长度上界的 SHA、要求普通单链接、源身份与b371物理前像完全一致（有冻结SHA者亦须一致）。重新无跟随枚举旧树精确1618；5317内容继承绑定的既有物理/Astra验收，不再全量hash、stat或扫描，只核三个真实新根、五入口及previous结构和7份关键归档文件。17个小保护文件按当前导航基底捕获，P/v7及四plan/binding保持历史原值。rules/current pointer属于主线即时观察，不以其旧值阻止研究推进；其变化不会被当作工具修改。

```powershell
$gate = 'docs/project-layout/20261108-packaging-final-ready-v1/archive-full1406-preconfirm.json'
$gateSha = '<该报告真实SHA256>'
& .\.venv\Scripts\python.exe -I -B scripts/project_layout/retirement_delete.py prepare --repo . --run-dir docs/project-layout/20261108-packaging-final-ready-v1/prepare-<unique> --gate-report $gate --gate-report-sha256 $gateSha
```

输出仅创建新 `prepare-<unique>/delete-manifest.json`、`preparation.json`（失败为`prepare-failure.json`），均独占写入；`PREPARED_PENDING_FINAL_USER_AUTHORIZATION` 是准备快照，不能授权删除或承诺未来未漂移。

## future apply合同

本轮不运行apply、不生成真实授权。`authorization-template.json`始终 `authorized:false`，不得把它改成true当作用户已批准。实施者必须先向用户呈交确切1607清单及准备报告，得到独立最终确认，再据用户确认建立授权文件。授权须同时绑定：repo、1607数量、`DELETE_EXACT_1607`动作、完整排除项、清单SHA、准备报告SHA、本轮内容门报告SHA、四个工具代码SHA、明确用户确认依据、唯一`apply-<run_id>`、最多2小时的UTC有效起止。CLI另传授权文件SHA，缺项/时间窗外/既有运行目录一律拒绝。授权没有从prepare或旧迁移授权继承。

future命令形式（本轮**禁止实际运行**）：

```text
python -I -B scripts/project_layout/retirement_delete.py apply --repo <repo> --run-dir <repo>/docs/project-layout/20261108-packaging-final-ready-v1/apply-<unique> --manifest <delete-manifest.json> --manifest-sha256 <SHA> --preparation <preparation.json> --preparation-sha256 <SHA> --authorization <separate-user-authorization.json> --authorization-sha256 <SHA>
```

执行时重新读取全部绑定证据，重新跑一次完整archive1406内容门并保留新报告，再核全部1607源SHA/metadata、新根/入口结构和小型保护。每组使用新Reader重新读对应source/survivor，组开始/结束补充核survivor元数据/祖先；逐项只即时核本对，避免无益的全组重复扫描。每个待删source只持一个Windows `GENERIC_READ|DELETE`、`FILE_SHARE_READ`句柄，阻止该候选被写/改名/删除；源SHA直接从此句柄读取。外部survivor继续用普通只读Reader，允许主线写入，不加deny-write/delete锁；本对读完后再次核双端身份和祖先。写前记录INTENT并flush/fsync，紧前再核有效期和本对身份；进入`unlink`后在最终path/handle检查之后、紧贴`SetFileInformationByHandle(FileDispositionInfo=4, DeleteFile=BOOLEAN(1))`再验授权时间，标记这个精确源句柄，关闭句柄完成单文件unlink；仅明确`lstat`抛FileNotFoundError才记DONE，PermissionError等为PAUSED。没有放开源锁后再按路径删的fallback。

这是观察内容门加单个退役源句柄保护。survivor合法并发修改可能使本组或剩余批次PAUSED，主线无需停工；最后观察到单文件unlink之间仍有微小竞态，不声称全系统排他或所有survivor全程锁定。若已有写者持源句柄，锁获取立即失败并PAUSED，不抢占进程、不盲重试。保护/root发生新的合法并发修改时重新定基准备，不要求无关研究停止。

失败写PAUSED，记录已确认删除数量、当前源和实际存在状态；不回滚、续跑或覆写既有回执。若unlink已发生而DONE未落盘，应以INTENT、实际路径和句柄错误调查，不凭计数断言未删除。完整成功后只核旧树剩11原位材料及新根/入口/小型保护，5317仍继承既有独审，不全量复查；previous/空目录均保留，删除完成也不代替其他退役验收。

## 合成与native测试

```powershell
& .\.venv\Scripts\python.exe -I -B docs/project-layout/20261108-packaging-final-ready-v1/tooling/test_delete.py
```

测试只在本目录全新`fixtures/<unique>/`下创建少量自有文件，不读取或删除真实1607，不复制大payload。测试native句柄删除也仅针对本测试新建文件；授权与apply流程用新夹具和注入依赖缩小集合，CLI生产数量不可配置。唯一结果JSON保留测试及原生API失败诊断，不把模拟PASS冒充Windows API实测。
