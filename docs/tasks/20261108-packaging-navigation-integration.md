# 打包材料迁移后共享导航整合回执

- 日期：2026-11-08；状态：**真实导航已整合／链接检查通过／未提交、未推送、未发布**。
- 本轮只修改 `AGENTS.md`、`HANDOFF.md`、`STATUS.md`、根 `README.md` 的相关条目及新增本回执；未重复迁移或切换，未删除候选、previous或空目录。
- 依据：[物理回执](../project-layout/20261108-packaging-physical-v1/REPORT.md)、[Astra独立复核](../project-layout/20261108-packaging-physical-v1/physical-independent-review.json)。Sol验收及Astra独立复核已通过，不使用旧准备态补丁。

## 1. 重定基底与实际差异

| 文件 | 整合前SHA-256 | 整合后SHA-256 | 实际变化 |
|---|---|---|---|
| `AGENTS.md` | `6d678f33f09bbd13c3182fd75dc52c742e718622c709433640c651cd08a86a5c` | `0a39612be2094f5d48782e035c372f142627db435c488ab94d3ff0f48f769875` | 分享包定位改为已迁移的 `operations/history/retired-packaging/20261108/` 下三个真实根；补5,317项、五正式入口、previous及删除门槛。第8节未改 |
| `HANDOFF.md` | `e4bc574357975cc632af3129c29cf526fd478ecefb5786eee50a52f51a394451` | `cce2f9bab2346da6771ce837a98332fd7515a0bac275ed9f07e4112740ac3a90` | ②历史发行说明改指新位置；新增物理迁移与五入口验收入口及删除边界，保留C19／Web和其他主线内容 |
| `STATUS.md` | `ffd817f7c538bec2ca66e470e183383d038617c1438ca51983f519f79b1ab7a3` | `8525de9843c97d9927f80c0a014546c35a0eed1a3f2e86bf2f9d5b5c5429d48d` | 顶部加入真实完成状态；旧 `20261016-delivery`、`20261025-character-tools`、`cc_skill_values_20261021` 路径改指新历史根，历史结论不改 |
| `README.md` | `9ac947801949c279064a2c294082d8092442e921e5ed0e8c8c930639c726438c` | `6cc87ec52a00cd914a1d18ff7a39bc9d07e59bfce815e6c2673a25a1d4bd3fa1` | 增加真实迁移与只读维护入口；仓库结构中的 `scripts/` 改为解包／验证源码及 `retirement_runtime.py`，保留未来完整分享原则 |

`git diff --stat`：4文件，24行新增、14行删除（长行按行计数）。未使用 `shared-navigation-r04.patch` 的准备态文字，未整文件覆盖。

## 2. 引用与身份检查

- 四份根文件共检查 **390个本地Markdown链接，缺失0**。
- `share_bundle/`、`distribution/`、`history-work/` 三个新根均实际存在。
- 五个C14—C18正式 `share_bundle` 仍指向 `operations/history/retired-packaging/20261108/share_bundle`；五个previous仍存在且只作停用回滚证据，next均不存在。
- AGENTS第8节、C19主线、C19 Web登记及其他并发新增内容保留；无“尚未迁移／目标尚不存在”的准备态表述。
- `git diff --check` 通过。历史 `output/share_bundle/build_bundle.py` 属未删除的DELETE候选，未误改为不存在的新位置。

## 3. 剩余边界

- 本轮未改主线源码、规则、答案、账本、profiles、正式pages、latest、其他junction、原始输入、vault、P/v7或四份历史plan。
- 未重复迁移、切换或删除，未运行旧打包、清理、恢复或冻结verifier。
- 1,607项删除候选、previous及旧空目录未处理；最终删除须另获用户确认，并重新通过archive模式完整1,406对临前检查及漂移检查。
- 当前无未解决的导航冲突；真实新位置、共享引用及并发内容已一致。
