# 临前暂停及32历史入口补充方案（尚未批准）

当前已收到原范围搬运授权，原scope、候选和独审冻结不动；未开物理窗口，未改业务代码／数据／联接／正式入口。

本次是临前真实枚举发现的旧清单漏项；没有证据证明它们是刚刚新建，不能称为近期新增文件。它们均属于C14—C18隔离输入，同样指向本批31源目录。若只搬实体而不处理它们，会留下失效入口。

Sol核查及根直接lstat/readlink确认：原195项身份未变；另外32项不在195项、也不属于C19/C20的other-16排除集合。按原RUNBOOK第0节“新参与者／新alias…停止受影响组，不偷缩成另一小批”暂停。

## 最小补充范围

- 原31目录＋2指针及192文件动作不扩；只补32个历史输入junction的next→previous→formal受控切换，沿用原普通入口验读、身份、WAL和回退规则。
- 原189普通入口变为221；加六个原对象不动的独审入口，总已知227。新32个previous只停用留证，不删。
- C14补4项；C15、C16、C17、C18各补7项。四类各5个：decoded、phone_full_20261015、phone_refresh_20261015、validation；三类各4个：skill_mechanism_scale、skill_mechanism_trial、skill_route_experiments。
- 不搬任何新增载荷，不扩大到KEEP／raw／APK／旧批次／冻结／删除／Git。

全部路径如下（均为项目相对路径）：

| 原入口 | 获准后指向 |
|---|---|
| `work/c14_delivery_20261103/impl/isolation_input/output/decoded` | `projects/unpack/history/decoded` |
| `work/c14_delivery_20261103/impl/isolation_input/output/phone_full_20261015` | `projects/unpack/reports/acquisition/phone_full_20261015` |
| `work/c14_delivery_20261103/impl/isolation_input/output/phone_refresh_20261015` | `projects/unpack/reports/acquisition/phone_refresh_20261015` |
| `work/c14_delivery_20261103/impl/isolation_input/output/validation` | `projects/unpack/reports/validation` |
| `work/c17_delivery_20261106/impl/isolation_input/output/decoded` | `projects/unpack/history/decoded` |
| `work/c17_delivery_20261106/impl/isolation_input/output/phone_full_20261015` | `projects/unpack/reports/acquisition/phone_full_20261015` |
| `work/c17_delivery_20261106/impl/isolation_input/output/phone_refresh_20261015` | `projects/unpack/reports/acquisition/phone_refresh_20261015` |
| `work/c17_delivery_20261106/impl/isolation_input/output/skill_mechanism_scale` | `projects/skill-research/experiments/skill_mechanism_scale` |
| `work/c17_delivery_20261106/impl/isolation_input/output/skill_mechanism_trial` | `projects/skill-research/experiments/skill_mechanism_trial` |
| `work/c17_delivery_20261106/impl/isolation_input/output/skill_route_experiments` | `projects/skill-research/experiments/skill_route_experiments` |
| `work/c17_delivery_20261106/impl/isolation_input/output/validation` | `projects/unpack/reports/validation` |
| `work/c15_delivery_20261103/impl/isolation_input/output/decoded` | `projects/unpack/history/decoded` |
| `work/c15_delivery_20261103/impl/isolation_input/output/phone_full_20261015` | `projects/unpack/reports/acquisition/phone_full_20261015` |
| `work/c15_delivery_20261103/impl/isolation_input/output/phone_refresh_20261015` | `projects/unpack/reports/acquisition/phone_refresh_20261015` |
| `work/c15_delivery_20261103/impl/isolation_input/output/skill_mechanism_scale` | `projects/skill-research/experiments/skill_mechanism_scale` |
| `work/c15_delivery_20261103/impl/isolation_input/output/skill_mechanism_trial` | `projects/skill-research/experiments/skill_mechanism_trial` |
| `work/c15_delivery_20261103/impl/isolation_input/output/skill_route_experiments` | `projects/skill-research/experiments/skill_route_experiments` |
| `work/c15_delivery_20261103/impl/isolation_input/output/validation` | `projects/unpack/reports/validation` |
| `work/c18_delivery_20261106/impl/isolation_input/output/decoded` | `projects/unpack/history/decoded` |
| `work/c18_delivery_20261106/impl/isolation_input/output/phone_full_20261015` | `projects/unpack/reports/acquisition/phone_full_20261015` |
| `work/c18_delivery_20261106/impl/isolation_input/output/phone_refresh_20261015` | `projects/unpack/reports/acquisition/phone_refresh_20261015` |
| `work/c18_delivery_20261106/impl/isolation_input/output/skill_mechanism_scale` | `projects/skill-research/experiments/skill_mechanism_scale` |
| `work/c18_delivery_20261106/impl/isolation_input/output/skill_mechanism_trial` | `projects/skill-research/experiments/skill_mechanism_trial` |
| `work/c18_delivery_20261106/impl/isolation_input/output/skill_route_experiments` | `projects/skill-research/experiments/skill_route_experiments` |
| `work/c18_delivery_20261106/impl/isolation_input/output/validation` | `projects/unpack/reports/validation` |
| `work/c16_delivery_20261104/impl/isolation_input/output/decoded` | `projects/unpack/history/decoded` |
| `work/c16_delivery_20261104/impl/isolation_input/output/phone_full_20261015` | `projects/unpack/reports/acquisition/phone_full_20261015` |
| `work/c16_delivery_20261104/impl/isolation_input/output/phone_refresh_20261015` | `projects/unpack/reports/acquisition/phone_refresh_20261015` |
| `work/c16_delivery_20261104/impl/isolation_input/output/skill_mechanism_scale` | `projects/skill-research/experiments/skill_mechanism_scale` |
| `work/c16_delivery_20261104/impl/isolation_input/output/skill_mechanism_trial` | `projects/skill-research/experiments/skill_mechanism_trial` |
| `work/c16_delivery_20261104/impl/isolation_input/output/skill_route_experiments` | `projects/skill-research/experiments/skill_route_experiments` |
| `work/c16_delivery_20261104/impl/isolation_input/output/validation` | `projects/unpack/reports/validation` |

32项原ID、tag、raw target、样本、next／previous精确名在 [机读增量](execution/alias-amendment-proposal.json)；[完整拟修订scope](execution/scope-proposed-v2.json) SHA-256：`d7bf0694306d8331cab687d513ffc2d2a7b71722779aad0aef5284c0b83e7c3d`。这两份仍是提案，不自赋新权限。

## 另一个独立门

临前发现聊天“独立复审C20正式成果”当时正在做F01复验，因此未开窗。随后只读wait_threads已观察其自然完成并idle；复验REQUEST_CHANGES、F01仍OPEN（7个展示标签问题），属于主持后续语义整改，不由本迁址任务修复。没有打断或联系它。临窗仍须再次核参与者、相关读写、当前源码及保护身份；若主持随后启动整改或新基底变化，重新暂停，不拿现时idle当永久让出。

## 可直接回复的补充授权

> 在原搬运授权基础上，同意将这32个C14—C18历史输入入口纳入同一批切换，按拟修订scope执行；不扩大31目录、2指针和192文件动作，不删除previous或其他文件。在相关读写让出、当前C20复验已自然结束并经临前复核通过后再开启一次最长60分钟窗口，漂移继续暂停。

原先的搬运许可已保留，不需要重新批准原范围；这里只需对超出原精确清单的32个对象补充授权。
