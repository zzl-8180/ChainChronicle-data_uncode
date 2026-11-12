# 六个历史独审入口精确处置提案

状态：**待用户最终批准，未执行、未安装映射**。维护与证据接管归本执行对话，Sol实施、Astra独审；不再找主持第二轮，也不把本提案当已获批。

| 保留原位的alias对象 | 当前材料根 | 拟迁后实体 |
|---|---|---|
| `work/review_p2b5_thirdparty/iso/output/base_master` | `output/base_master` | `projects/unpack/data/apk/base_master` |
| `work/review_p2b5_thirdparty/iso/output/boss_heal` | `output/boss_heal` | `projects/skill-research/evidence/boss_heal` |
| `work/review_p2b5_thirdparty/iso/output/cache_full_20261015_v3` | `output/cache_full_20261015_v3` | `projects/unpack/data/cache/cache_full_20261015_v3` |
| `work/review_p2b5_thirdparty/iso/output/card_comparison_cid30236` | `output/card_comparison_cid30236` | `projects/skill-research/evidence/card_comparison_cid30236` |
| `work/review_p2b5_thirdparty/iso/output/char_roster` | `output/char_roster` | `projects/skill-research/data/char_roster` |
| `work/review_p2b5_thirdparty/iso/output/reference_analysis` | `output/reference_analysis` | `projects/reference-analysis/history/reference_analysis` |

每项原ID、tag、raw readlink精确绑定见[机器提案](six-review-contract-proposal.json)，临窗必须再核。

1. 六个alias原路径、对象ID、tag、target字符串均不动，不创建next/previous，不改名、不改target。
2. 只有用户明确批准材料根迁址及下面能力变化，才可移动对应六棵实体；搬迁后旧物理target不再存在，原alias保留为不可直读的历史证据。
3. 在冻结原目录之外创建版本化只读维护映射，按表解析旧逻辑alias和suffix至新实体。该读取入口不得跟随旧dangling alias、不得暴露写操作、缺新件不得回旧根，须验证新根祖先与内部路径不借二次reparse越界。当前只有提案，真实新址验读尚未发生。
4. 明确退役：旧alias直接读取、未经适配旧verifier和原现场精确重放能力。保留：原证据字节、原对象结构身份、历史结论、日志及通过新只读映射读取证据的能力。不把manifest/源码前像说成完整原现场备份。
5. 用户不接受能力退役则整组保持NOT_READY，执行者设计另案并交用户审定，不偷偷先搬其它根。
6. 新发现64条C19/C20历史隔离入口另列待保护契约，不混入这六条，也不自动变普通运行入口；执行者核其pins/冻结身份兼容后一次并入最终精确授权清单。

本提案不要求现在回复授权，当前只是接管回执的一部分；最终代码、保护和精确范围闭合后再一次提交用户。
