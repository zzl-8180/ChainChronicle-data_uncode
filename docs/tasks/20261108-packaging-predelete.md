# 打包支线删除前准备

- 日期：2026-11-08；负责人：Sol 子任务 `retirement_prepare`；主聊天 Sol high 整合、Astra high 子代理独立审查。
- 状态：**准备完成，Astra high 独立审查 PASS，Sol high 已验收**；`SHARED_INTEGRATION_PENDING`。未获得删除授权，未删除、移动或运行旧打包／清理／生成器。
- 目标：把既有 28 项清单推进到可最终审查状态，保留 17 个小型源码前像，核验候选身份和短时稳定性，明确旧版整包退役影响。
- 独占写入：`docs/project-layout/20261108-packaging-predelete-v1/`、本任务卡；`projects/distribution/README.md` 新增顶部停用声明与本轮记录入口，并定向将旧打包源码／成功包使用措辞改为历史停用。
- 其他文件只读；根 AGENTS／HANDOFF／STATUS／README 仅提出基于当前文本的待合入补丁，交主持整合。不修改 B00／B01 冻结记录、主线及旧保护清单。
- 输入：`20261108-packaging-retirement-v1` 冻结清单及验收；`20261108-reference-zip-decouple-v1` 条件复核及验收。
- 范围：28 候选，2,061,279,175 B；HOLD 1,997 与 RETAIN 4,763 项全部排除。不创建大 ZIP 备份。
- 完成：17个`.py.before`前像逐字节／SHA-256一致，共157,899 B；2个pyc只记录哈希；9个源码已跟踪、8个未跟踪。28项和原清单身份相符、两轮约2秒短时稳定，139项handoff保留材料身份一致；逐项无reparse、普通单硬链接。权限仅观察ACL／属性，未证明全机无写入／有效DELETE权限，不作该声明。
- 交付：[准备README](../project-layout/20261108-packaging-predelete-v1/README.md)、[逐文件清单](../project-layout/20261108-packaging-predelete-v1/execution-candidates.md)、[源码映射](../project-layout/20261108-packaging-predelete-v1/source-manifest.json)、[共享待合入补丁](../project-layout/20261108-packaging-predelete-v1/shared-navigation.patch)。补丁基于当前原文，`git apply --check`通过，未应用。
- 下一步：主聊天独立最终审查与共享入口整合，再由用户确认精确28项删除（包括统一放弃六个成功旧版整包重放）。不自动开始物理删除；未来漂移停止对应项，保留空目录／历史证据。

独立最终验收：Astra high 已将三项修正复核为 PASS；Sol high 独立核对17份前像及28项当前身份。见 `docs/project-layout/20261108-packaging-predelete-v1/acceptance.json`。共享补丁尚未合入，当前停在最终删除确认前，删除0、移动0。
