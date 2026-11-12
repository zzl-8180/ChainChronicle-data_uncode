# 最终物理授权清单（候选已准备，当前未执行）

项目根：`E:\代码项目\锁链战记数据解包`。以下相对路径均以此根解释。主持交接已1/1，不再找主持；最终用户授权尚未收到，60分钟窗口未开启。

本清单只请求一次明确范围授权，不包含任何删除、Git提交／推送或正式网站发布。机器权威表为 `authorization-scope.json`，代码只使用本包 `effective-code.patch`，不得再用旧v4／旧v2单独补丁或叠加完整版本。

最终动作清单：`authorization-scope.json`，SHA-256 **`b1f5d94b7ba1d4496be3ac8527d6b8538d20504020cae4342bf077e6aaf40df7`**。执行ID：`unified-output-20261109-v1`。本包不是已授予的物理许可，也未开启窗口。代码完整补丁SHA：`f305364b096d1ee21e9cbd16f68878e6a84d611f299f54249eb6f7935ccb0e0a`。

空间：31目录逻辑量25,057,294,461 B（约23.34 GiB）；同E卷rename，不复制这批载荷，不释放其占用。192文件候选总3,491,435 B，单个原子临时文件最大232,574 B；必要前像已通过绑定复用，另有小型WAL和回执。当前准备包约6.34 MB逻辑量，保留旧版本证据，不自动清理腾空间。

## 1. 整体移动31个目录、2个顶层控制文件

同E卷rename，保留每棵内部结构和文件对象，不复制完整payload、不合并覆盖目标。31根当前只读属性观察共907,829普通文件、25,057,294,461逻辑字节（约23.34GiB），另2个顶层小JSON；不是全游戏覆盖或实际磁盘分配量。搬家不释放这批载荷，也不另占同等大小副本。新父目录只限scope的16项。

| 动作 | 现在 | 目标 | 本次观测普通文件数 | 逻辑字节 |
|---|---|---|---:|---:|
| D01 | `output/apk` | `projects/unpack/data/apk/apk-baseline` | 6 | 258,559 |
| D02 | `output/base_master` | `projects/unpack/data/apk/base_master` | 8 | 116,830,646 |
| D03 | `output/boss_chain` | `projects/skill-research/evidence/boss_chain` | 83 | 5,126,991 |
| D04 | `output/boss_heal` | `projects/skill-research/evidence/boss_heal` | 21 | 5,171,236 |
| D05 | `output/cache_full_20261015_v3` | `projects/unpack/data/cache/cache_full_20261015_v3` | 111 | 129,284,652 |
| D06 | `output/cache_refresh_20261015` | `projects/unpack/data/cache/cache_refresh_20261015` | 90 | 129,779,325 |
| D07 | `output/card_comparison_cid30236` | `projects/skill-research/evidence/card_comparison_cid30236` | 209 | 80,324,348 |
| D08 | `output/card_images` | `projects/assets/data/card_images` | 49 | 2,420,881 |
| D09 | `output/char_roster` | `projects/skill-research/data/char_roster` | 2,665 | 157,532,573 |
| D10 | `output/decoded` | `projects/unpack/history/decoded` | 23 | 17,027,377 |
| D11 | `output/export` | `projects/unpack/data/export` | 234 | 1,500,467,070 |
| D12 | `output/field_guide` | `projects/skill-research/reports/field_guide` | 133 | 807,663,591 |
| D13 | `output/full_unpack` | `projects/assets/data/full_unpack` | 903,402 | 21,727,783,139 |
| D14 | `output/git_sync_20261024` | `operations/records/git-sync/20261024` | 6 | 29,828 |
| D15 | `output/il2cpp` | `projects/unpack/research/il2cpp` | 53 | 481,829 |
| D16 | `output/native` | `projects/unpack/research/native` | 45 | 22,543,420 |
| D17 | `output/ordinary_effects` | `projects/skill-research/evidence/ordinary_effects` | 119 | 3,878,723 |
| D18 | `output/phase_d` | `projects/skill-research/evidence/phase_d` | 86 | 1,411,477 |
| D19 | `output/phone` | `projects/unpack/reports/acquisition/phone` | 13 | 16,009,387 |
| D20 | `output/phone_full_20261015` | `projects/unpack/reports/acquisition/phone_full_20261015` | 5 | 44,162,287 |
| D21 | `output/phone_refresh_20261015` | `projects/unpack/reports/acquisition/phone_refresh_20261015` | 9 | 34,939,444 |
| D22 | `output/project_overview` | `operations/records/project-overview/20261020` | 5 | 69,618 |
| D23 | `output/protection` | `projects/unpack/research/protection` | 60 | 15,112,060 |
| D24 | `output/reference_analysis` | `projects/reference-analysis/history/reference_analysis` | 82 | 13,267,363 |
| D25 | `output/sample` | `projects/skill-research/evidence/sample` | 4 | 227,053 |
| D26 | `output/skill_mechanism_scale` | `projects/skill-research/experiments/skill_mechanism_scale` | 121 | 49,665,530 |
| D27 | `output/skill_mechanism_trial` | `projects/skill-research/experiments/skill_mechanism_trial` | 79 | 18,172,371 |
| D28 | `output/skill_route_experiments` | `projects/skill-research/experiments/skill_route_experiments` | 43 | 73,031,660 |
| D29 | `output/structured` | `projects/skill-research/data/structured` | 7 | 42,661 |
| D30 | `output/unity` | `projects/assets/history/unity` | 50 | 84,552,259 |
| D31 | `output/validation` | `projects/unpack/reports/validation` | 8 | 27,103 |
| F01 | `output/cache_full_latest.json` | `projects/unpack/data/cache/cache_full_latest.json` | 1 | 小JSON，原SHA见机器清单 |
| F02 | `output/cache_refresh_latest.json` | `projects/unpack/data/cache/cache_refresh_latest.json` | 1 | 小JSON，原SHA见机器清单 |

不动六目录：`output/character_skills`、`output/storage_retention`、`output/20261016-reproducibility-audit`、`output/20261024-project-review`、`output/审查报告`、`output/project-layout`；`output/_p.tmp`也不动。不重做v1/single/v2或旧打包退役，不移动原始APK/raw/work或已迁历史归档。

## 2. 源码、控制文件和导航

- 有效候选325份：155个既有文件的必要路径修改、3个新增helper；其余167份不覆盖live。新增第三个helper是只读历史定位工具，不是打包／恢复／清理入口。完整代码补丁、before/candidate SHA在effective绑定中。
- C20索引只保留当前版本，撤掉旧补丁整文件换行段；C20 cycle_report新增原样保留。common的list修复已是主线前像，不是迁址新增语义。检查器只适配数据读口／输出与源码指纹边界，历史C19硬门不放宽，不用其main冒充当前C20全套通过。
- 192项明确文件动作＝158个代码文件（155改＋3新）、16局部ignore、11导航、4selector、主配置／locator／历史ACTIVE路由3个控制文件。逐项路径、候选／前像SHA和临时文件名见file-writes.csv；只允许scope中列出的原子文件替换／新文件，不整目录覆盖。
- 四selector只更新原已审7个定位字段；snapshot/build/manifest/raw_snapshot等其他身份值不改。`operations/config/project-layout/20261109.json`、`scripts/project_layout_active.json`仅全组实际验收后发布。
- 六历史只读工具拟安装`scripts/project_layout/history_readonly.py`；实际ACTIVE路由只能在已批准的31根真实搬后验ID、按实际回执派生至`operations/config/project-layout/history-review-20261109.json`，不能拿候选预览假装已激活。预期确定字节SHA见config/readonly-route-install.json。
- 四共享根只改迁址定位／状态，保留C20及后续所有新增和AGENTS第8节；根.gitignore不改。冻结HTML／README／manifest原字节不改；不承诺其中旧物理路径和跨树相对链接继续原样可点，使用新总导航／明确只读定位。当前KEEP的三个正式卡页及reader的25条字面href/src投影无迁址影响，但未冒充浏览器／JS全站验收，不切换正式站点。

## 3. 195个已知alias逐项处置

- **189项获准后普通切换**：原125＋新C19 32／C20 32。每项next验读→formal改previous并核旧ID→next改formal并验新ID／内容；新formal的ID和target变化是明确授权项。189个previous只停用留证、不供业务、不删除。
- **六P2B5独审原对象完全不动**：路径、ID、tag、raw target保持；其实体迁后旧alias将不可直读，退役旧直读和原现场精确重放能力，改由新独立只读route定位/stat/digest证据。原报告、源码前像、冻结字节与失败日志保留。需要用户明确接受此能力变化，不能把“不改junction对象”说成旧入口仍可用。
- 新64是历史隔离输入。源码证据表明其构建器本就重建联接树、未将junction ID/target列为冻结文件身份，因此给出普通切换方案；仍需最终用户逐项批准，不把此前pending当默认权限。
- C19/C20未迁的scripts链接随live源码更新而读到新版本；不能承诺完整旧隔离现场所有源码SHA／旧checker原样重放。另16个非本批reparse、KEEP页面链接、旧v1/v2/single/share_bundle问题不顺手改动。
- `alias-actions.csv`和protection逐项契约给全部195路径／ID／target／suffix／next／previous。口述62与实际64差异不丢两条凑数，也不为此再找主持。195是已知实际核对清单，临窗增量发现新对象即暂停，不宣称全机穷尽。

## 4. 保护与不删除边界

85共享inode当前698名称；只有85个MOVE源名随其父根改位置，613个非MOVE伙伴名（含新增83个C20 work链接）原位且同ID／nlink／大小／mtime。目录rename不授权任何原位重生成，未来产物用另行批准的新版本输出。

11项原位、P/v7、四份指定历史plan/binding及其它既有plan、C20原始失败/独审/最终清单、8份RETAINED和5,353,728,612B预留、原5317份归档均不清理；现有previous、旧空目录和测试缓存也不删除。protection/CONTRACT与scope保护快照是精确边界。

## 5. 何时搬、主线何时让出

现在不搬，C20不需现在全停。本包和Astra候选复核完成、用户最终授权后，等相关生成／校验／隔离输入构建／选中文件写入自然到安全断点并让出；长期缓存进程受控退出／重启，普通研究继续。然后刷新源码／alias／树属性／硬链／目标和实际参与者检查，通过即自主开启一次不超过60分钟窗口，真实UTC计时，不等固定钟点、不再找主持。

默认精确SHA。若C20或其它身份漂移，先停，不用旧候选覆盖新语义；如用户明确允许同文件集、同物理范围内仅路径hunk／导航定位的非语义重基，执行者可保留新前像、做必要回归和Astra独审、记录新SHA及原授权派生依据后再执行。不得扩大根／alias／保护能力／控制字段／文件集或重签冻结数据；未给该条件则提交新绑定再确认。

临窗检查不是本轮准备PASS。full_unpack已完成90.3万文件的属性扫描，但它仍是时点观察、非全部载荷哈希或无人使用证明；真正窗口重查31根，遇未知reparse、新参与者、冲突、硬链／保护身份改变、读取失败或超时，停受影响依赖组留现场，不偷缩小批、不自动续窗。

## 6. 顺序、验收与恢复

先必要代码／局部ignore，再31根＋2控制文件，再189alias和六只读route，Sol/Astra接受实际新位置及保护后，才发布主配置→4selector→locator→真实导航。两次junction rename和多根移动都非原子，不承诺零竞态或全程零停顿。完整seal/publish成功及全库/native/手机/全站未做，不伪造PASS；只有实际影响接口做必要验证。

每步WAL INTENT落盘→即时身份／权限／期限核对→原生精确操作→COMPLETED与真实ID/SHA/退出码。失败优先保留已验新址和新写入、前向修复；旧根迁空不得盲指，逆搬前先证无新增/无冲突并验真恢复材料，不覆盖新成果。到期停新增步骤，不自动回退或跨窗继续。

## 7. 可复制的授权回复（当前尚未收到）

> 授权按这份最终scope清单整合必要代码／控制文件，并同E卷整体迁移31目录和2顶层控制文件；按逐项方案切换189个普通alias、保留previous，六独审原对象不动并接受旧直读／原现场精确重放能力退役，使用经真实新址验ID派生的只读路由。只改4selector约定定位字段，实际验收后发布locator和迁址导航。相关写入／生成／校验／缓存任务已让出，或等约定的可观察终态后再检查；临前全通过即自主开一次最长60分钟窗口。漂移或失败暂停，previous／旧空目录／任何历史证据不删，不提交推送或公开发布。

如希望本次授权同时涵盖上文有界非语义重基，可另明确附一句允许；否则按精确SHA门执行。实际执行时采用最终公布scope SHA及用户原消息引用文件化授权，绝不把此模板或候选审查PASS当授权。
