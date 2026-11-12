# 统一目录迁移：路径适配与验证候选

状态：**PARTIAL_WITH_RECORDED_SCOPE_DEVIATION / NOT_READY_FOR_PHYSICAL_EXECUTION**。本包继续完成不依赖主持的代码、清点、导航和验证准备；不是搬迁回执，也不是已经获准迁移。

- [实际结果和限制](REPORT.md)
- [验收总账](acceptance.json)、[Astra独立复核](astra-review.json)：只验本轮候选准备，不代表物理准入。
- [路径总账：31目录、2顶层指针、7原位项](../20261108-unified-output-migration-v1/unified-path-map.md)
- [33项执行前总表：现址、目标、引用、清点、空间与回退](execution-scope-matrix.md)
- [可直接转发的一份完整主持提示词](HOST_PROMPT.md)：已合并原总包与实现补充，不用分别发送，主持交互仍为 **0/1**。
- [部署与恢复顺序](activation-and-recovery.md)：不含可直接运行的迁移／删除命令。
- [最终统一代码补丁](candidate-code-final-v4.patch)、[检查回执](candidate-code-patch-check-final-v4.json)、[逐文件绑定](candidate-bindings-final-v4.json)：仅候选，未应用；v1/v2/v3是保留的中间证据，不用于执行。
- [局部ignore候选](ignores/manifest.json)：16份局部规则覆盖33个新叶目标，保留既有规则，根.gitignore不改。
- [四selector候选](pointers/README.md)：7个定位字段按原映射拟改，身份字段保留，live未写。
- [解包与媒体候选](unpack/REPORT.md)、[研究与阅读器候选](research/STATUS.md)、[导航候选](navigation/REPORT.md)
- [Node四入口候选](unpack/node-adapters/REPORT.md)、[已修点与真正剩余事项](research/remaining-work.md)
- [清点及大型目录限制](inventory/REPORT.md)、[85个硬链接源的所有伙伴](inventory/hardlink-partners.md)
- [最新24+9项根测试](tests/root-check-results/root-suite-final-v2.json)、[真实查询及三卡对比](tests/real-readonly/final-comparison.json)
- [阅读器范围失误纠偏](tests/media-scope-correction/REPORT.json)：仅清除本轮重复测试图片，不涉及业务文件。

候选均在本包内，未应用到正式 scripts、四共享根、指针或生产联接。代码快照和小型测试输出不是完整业务备份。原统一方案、独立审查、冻结证据、历史失败与退出码继续保留。

目前不能直接搬：六个历史独审入口的保护／旧访问能力退役方案尚待确认；主线代码仍会更新，最终合入需最小重定基底；生产写入、事务和发布全链尚未全部验收；还需一次主持交接及用户针对最终范围的物理授权。相关方让出选定输入的关键窗口不等于主线全局停工。

真实数据测试已经结束，36个自建输入测试junction已逐项核ID／tag／target后卸载，目标ID未变；见 [卸载回执](tests/projection-uninstall.json)。历史测试结果保留，复现须显式重建测试映射，不能把现有候选目录当作已经部署的新布局。
