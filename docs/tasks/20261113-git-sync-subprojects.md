# Git 同步与八支线取舍

- 日期：2026-11-13；负责人：当前 Codex 主聊天。
- 用户授权：目录调整收尾后补查变化，完成 Git 整理和推送至既有 GitHub origin，列八个子项目的用途、依赖与放弃影响；明确不删除文件。
- 状态：已完成源码提交与推送，远端核对通过；未新增删除。主聊天唯一 Git 整合；Sol low 核目录收尾及闭包，Terra low 整理八支线决策文档，Luna low 执行语法及敏感模式预检。
- 写域：本任务卡、根 `HANDOFF.md` 收尾入口、`.gitignore`／`.gitattributes`、`docs/project-layout/.gitignore` 与导航、`projects/reader/site/.gitignore`／`projects/reader/reports/.gitignore`、`operations/records/git-sync/20261113/`、`work/20261113-git-sync/`。已有源码和任务成果仅筛选提交，不接管生成或删除。
- 起点：main `56a9d1793a93ead3d01afcb4cff2f6d1ff5e6db0`。已核远端同 SHA。全局旧代理 `127.0.0.1:7897` 不适用本轮 Clash TUN；仅本仓库 GitHub URL 覆盖为空代理，fetch 成功，0 ahead／0 behind；全局及 Clash 设置未改。
- 收尾变化：`20261113-legacy-rerun-safety.md` 已完成防覆盖与只读回执保护，无新物理迁移；无需重新盘点。相关39项、14项和既有21项回归沿用原回执，限制照原记录披露。
- Git范围：代码、必要规则／模板、运行配置、小型导航和任务文档，以及旧归档只读查询的必要映射。保留原始字节绑定的配置和冻结源码；大载荷、原件、环境与大量历史副本保持本地。9个旧发行脚本删除只记录之前已履行的退役，不执行本地删除。
- 验证：显式路径清单、语法／敏感项检查、固定字节哈希、暂存内容检查、隔离检出和必要现行只读回归；不重新解包或正式全库生成。
- 决策入口：[八条支线](../project-layout/20261113-subproject-decisions-v1/README.md)。用户选择前不清理。

## 完成回执

- 源码同步提交 `3ba9106b0d7343cc38b4789a7e0d5d5d69fe2855`，`git push origin HEAD:main` 成功；随后 `ls-remote` 与本地 HEAD 一致。
- 623 个提交路径：620 项选择（含9项既有删除）与3份同步记录；约19 MB 工作树源码／配置／文档，未夹带大成果。必要原字节资产以逐路径属性保护，7份 index／隔离检出逐字节一致。
- 303 项语法／格式解析通过，限定凭据模式未命中；当前主线17/17、阅读器21/21、隔离映射3项通过。6条既有末尾空行提示保留，未改冻结材料。验证范围和限制见[validation.json](../../operations/records/git-sync/20261113/validation.json)。
- GitHub URL 级仓库代理覆盖生效；全局与 Clash 未改。Git 对象约119 MiB，维持轻量源码仓库。
- 收尾仅补充本任务、根 HANDOFF、同步说明和精确 ignore 祖先；未触碰业务数据。收尾文档与同步说明随下一笔文档提交推送。
