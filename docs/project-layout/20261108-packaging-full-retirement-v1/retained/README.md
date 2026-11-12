# RETAIN 4,763 项：完整支线去向与消费适配

2026-11-08；只读调查与本目录审查材料写入。**ADAPTATION_REQUIRED；未删除、未移动、未改业务入口、未运行打包／生成／清理。** [逐文件去向](retained-disposition.jsonl)恰好覆盖原 RETAIN 4,763 路径／81,107,363 B，`bytes`沿用原冻结清单，不能据此当作现存容量或释放容量。原件与独立历史审查不改。

## 去向与完整目录规则

统一非活跃历史根拟为 `operations/history/retired-packaging/20261108/`。此目录是历史保管区，不能注册为新的打包项目或恢复现行打包能力。逐行 `path → target` 就是外部迁址映射；归档不另建载荷副本、不改manifest内历史source／target／哈希。完整父目录变换如下，具体删除空缺由主清单声明，不隐瞒原整包已退役。

| 原父目录 | 新父目录（拟） | 说明 |
|---|---|---|
| `output/share_bundle/` | `operations/history/retired-packaging/20261108/share_bundle/` | 所有存续证据的内部相对关系保持；139项研究交接也在此完整树内，由skill-research导航登记业务归属 |
| `projects/distribution/` | `operations/history/retired-packaging/20261108/distribution/` | 包含B01-D release、spec和原导航26项；撤去活跃项目，不留下仅“停用”的实体支线 |

| 分组 | 项／基线字节 | disposition | 保留依据 |
|---|---:|---|---|
| mechanism_handoff | 139／50,124,806 | REHOME_BUSINESS | 136个payload成员与3个外侧README／release_manifest／isolation_receipt成组保管；含74冻结输入、27路线提交、49／4／61去向，研究证据不因打包退役删除 |
| skill_value_history | 4,478／7,129,344 | ARCHIVE_HISTORY | 两历史campaign各2,236逐卡receipt、pages契约README、包说明和逐成员manifest；记录旧答案／HTML身份，不能重建缺失字节，仍用于事故及旧版对账 |
| character_tools_history | 114／23,175,621 | ARCHIVE_HISTORY | 最终发行spec与失败spec、selection前后像、135证据补齐来源、构建／隔离日志、fixture及故障/修复小样本、独审与完整读回回执，解释20261025接受闭包；整个冻结证据目录保持，非按后缀决定保留 |
| b01d_history | 26／65,810 | ARCHIVE_HISTORY | spec、2个小ZIP、包内同源工具和报告、负例现场、接收前像与回执成组；保留B01-D接受事实，旧run不再推荐执行 |
| early_release_history | 6／611,782 | ARCHIVE_HISTORY | 根说明／package_summary、20261016 README／RELEASE_NOTES／media_manifest／package_manifest；保留包身份、范围和未含媒体来源，不把它们称作现有完整包 |

因此该4,763项没有新增DELETE建议，不为减少文件数丢弃研究、事故或验收证据。4624历史归档＋139业务证据移交均离开原支线根，**保留证据不等于原地保留打包支线**。目标历史树包含历史脚本、绝对旧路径或缺失ZIP引用，仅供阅读，不能原样重新运行。

## 当前身份差异

[summary.json](summary.json)保留完整差异：`projects/distribution/README.md`原4,024 B，当前4,789 B，mtime也已变；本轮读取的是带前次停用修订的现文，不把旧盘点覆盖回去。该行`current_bytes`与`DRIFT_REVIEW_REQUIRED`提示整合者重读并接受新前像后重定执行基线。其余4,762项size／mtime_ns／dev／ino／nlink与原清单匹配；这不是全机无写入者或打开句柄证明。迁址前仍须祖先路径、reparse、身份与活动复核；目标已存在不得覆盖。

## 真实消费者与具体适配门槛

所有下列方案都未应用到业务共享文件；不能把映射文件存在写成运行依赖已解除。

| 消费者 | 已核事实 | 具体维护／替代入口与剩余门槛 |
|---|---|---|
| `scripts/character_skills/reconcile_mechanism_first_handoff_20261104.py:18` | `DEFAULT_BUNDLE`固定旧payload；已有`--bundle`参数。20261104对账已经完成，当前C16—C19生产链不以再次运行该历史对账为前置 | 新调用明确传`--bundle operations/history/retired-packaging/20261108/share_bundle/20261104-mechanism-first-handoff-r1/payload`，另传新`--output`，不得覆盖旧对账；下一次合法使用需核当前snapshot。现脚本不改亦可参数适配；主导航/用法待整合。原命令无参数重放退役，不称无损保持 |
| payload内`verify_bundle.py` | 以自身`__file__`为根，135成员、74输入、27路线相对定位；不读旧发行根 | 迁址后从新payload运行`python -I -B verify_bundle.py`；不改payload任何字节。此入口只读，不能把研究脚本/历史生成器作为兼容入口运行 |
| 四个`cycle_closeout_c14_c15_20261104.py`／`c16_20261106.py`／`c17_c18_20261106.py`／`c19_20261107.py` | 创建plan和postcheck真实stat/hash旧manifest，既有冻结`plan.json.protected_files`均钉45882 B和SHA `ae3a591d1dd35be221294a6418ca7455c9ec1184f247192cfee6c0f80bdef051` | **旧脚本、旧plan、旧postcheck不改、不重跑**。新只读[check_relocated_payload.py](check_relocated_payload.py)接受显式新`--payload-root`，读四旧plan的同一历史键并核新位置manifest字节/哈希，再核135成员；替代的是该保护项后续维护核验，不是整份历史postcheck。其余保护文件仍由原保留体系负责 |
| 五个C14—C18隔离输入junction | 已逐项lstat确认仍指向旧`output/share_bundle`，[精确交接](known-alias-handoff.json)记录原target | 拟全部改target到同一个完整新`.../share_bundle`根；由该隔离契约负责人单独实施并核相对payload路径可读、不得跟随junction遍历/删除、不得留下`output/share_bundle`兼容根。**本轮不改junction**。该切换仅保留存续证据读取，ZIP/旧构建器缺口保持明确；旧整包重放不恢复 |
| `scripts/storage_retention/continue_recovery_20261024.py:37–42` | `packages()`同时打开两旧ZIP和外部manifest，比较内外清单并按原sha搜索缺件；20261024已完成，20261025主持交接明确旧ZIP与展开载荷已退役。该函数在本轮前已不能按原命令完整重放 | 保留原恢复脚本/恢复结果/事故材料原位；两manifest迁至history后供显式新路径读取。需要新缺件研究时，以`remaining_targets.json`的原sha为请求，把新历史manifest路径显式作为只读输入，可返回旧成员身份线索，**不能声称manifest/receipt能还原card.json或HTML**。若要保留整段packages()历史重放，必须另提供原ZIP并新增`--archive-root/--manifest-root/--output`入口，拒绝缺包且不写旧回执；本轮未实现、未授权重建ZIP |
| `projects/distribution/.../run_pilot.py:18,119` | 通过subprocess执行旧BUILDER（不是import），依赖旧spec/root深度；移动后默认ROOT也会错误 | 整组存档供阅读，不运行旧run，不为本次改其源码。实际包内工具源码和两个小ZIP都在26项归档；如需新试验另指定root/spec/out，读取存档中的`isolation/中文 空格/extracted/tools/build_explicit_bundle.py`，不得借旧run改写存档；B01-R来源报告和生成器原位不动 |

新保护项维护命令（**迁址后**；不是旧清理命令）：

```powershell
& .\.venv\Scripts\python.exe -I -B docs/project-layout/20261108-packaging-full-retirement-v1/retained/check_relocated_payload.py --repo . --payload-root operations/history/retired-packaging/20261108/share_bundle/20261104-mechanism-first-handoff-r1/payload --run-frozen-verifier
```

本轮已用**现有**`work/mechanism_first_handoff_20261104/isolated_readback`作为新位置模拟，不复制载荷；逐136文件与原payload现存字节SHA/大小相同。模拟审计拒绝旧`output/share_bundle`的open／scandir／listdir及全部写open；四份冻结plan同一保护manifest、135成员哈希和原只读核验器49／4／61来源算术均PASS，旧根访问尝试0。见[模拟回执](payload-relocation-simulation.json)。这证明该只读核验闭包可离开旧根；**不是实际迁址、5junction适配、reconcile当前对账、完整历史重放或原生OS所有访问审计**，整体仍ADAPTATION_REQUIRED。

## 九根以外的定向范围复查

[extra-disposition.jsonl](extra-disposition.jsonl)独立列147项，不混入4,763计数：

- **136项DELETE候选／50,121,835 B**：`work/mechanism_first_handoff_20261104/isolated_readback/`，本轮逐文件sha/大小与payload完全相同；保留139研究交接及其独立isolation_receipt后可删除冗余验证副本。执行门槛`G_DUPLICATE_PAYLOAD`要求先完成存续payload迁址/保护核验，临前重核两个精确文件；不在本轮执行。
- **11项RETAIN_IN_PLACE／160,921 B**：`output/20261016-reproducibility-audit/`6份独立报告、`output/character_skills/share_manifest_20261021/`2份历史清单，以及`docs/tasks/20261016-reproducibility-audit.md`、`20261025-clean-release-reproduction.md`、`20261104-mechanism-first-handoff.md`3份历史卡。它们位于九根之外，属于跨任务解包复现／事故／共享治理依据；旧path-map归distribution不构成物理清理授权。原位排除，不为整支退役制造新断链。extra允许`RETAIN_IN_PLACE`，主4763表仍仅使用约定去向枚举。

这次定向搜索沿既有1140条path-map中20条distribution归属、release源码实际写域与引用、scripts内具体旧根引用、B01接收映射进行。未见九根以外遗漏的独立打包执行脚本；发现上述readback与8份跨任务证据及5junction。**静态未命中不证明全局无消费者**。生产`character_skills_pipeline`、C周期delivery主线、普通研究实验、解包器、恢复脚本和存储治理实现均不因名称含delivery/bundle/release就归删除；历史任务中提过某路径也不自动构成本轮执行目标。

## 引用与导航补丁建议（未应用）

1. 共享AGENTS保留一般未来分享／可移植性／版权与发布规则；只将“当前分享包”定位表切为本次退役历史说明。HANDOFF、STATUS、根README撤掉当前可用打包入口，明确不再从旧包命令启动工作；保留历史收口链接，当前事实以主整合回执为准。
2. 整合者更新`projects/unpack/README.md`等当前发行导航指向独立history索引；skill-research导航登记139研究交接的新实际位置和上述显式参数命令。`projects/distribution`整体归档后不再作为当前子项目，六项目历史B00及B01冻结证据不重写。
3. `docs/project-layout/20261107-b01-v1/README.md`及`validation.json`为B01-R/D混合冻结验收，全部保持原位原字节；新外部历史索引链接到原`b01-d-acceptance.json`、新归档D目录和原B01-R报告，说明原文旧链接按映射查阅。不能删除整个B01文档根或B01-R。
4. 四旧清理保护清单、storage_retention全套事故／pins／vault、历史manifest/source spec不替换旧路径；新映射与只读保护项核验承接新位置。禁止“全局替换share_bundle”改写冻结证据。旧6成功大ZIP、当前这136重复副本及HOLD结论由主整合清单统一覆盖，不能据本页单独删除整个目录。

代码与文档状态：本目录`prepare_retained_plan.py`只生成本目录清单，不运行旧业务脚本；`check_relocated_payload.py`是新只读维护验证入口，已做上述模拟，未注册当前业务消费者。`G_PAYLOAD_ADAPT`需导航/显式参数及5junction交接验收；`G_RECOVERY_HISTORY`需明确旧packages()冻结重放边界；`G_HISTORY_LINKS`需当前导航更新与临前身份；`G_B01D_REPLAY`需原接收回执外部链接与run退役提示。所有实际归档／移交／删除继续等待主聊天整合、用户最终执行授权及临前复核。
