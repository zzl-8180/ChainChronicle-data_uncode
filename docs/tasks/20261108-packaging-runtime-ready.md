# 打包整支最终确认前运行适配准备

- 日期：2026-11-08；负责人：Sol主聊天整合，原生子代理分写runtime与handoff，Astra独审；本卡由handoff子任务维护，其他子任务不覆盖。
- 状态：`FINAL_CONFIRMATION_PACKAGE_READY_WITH_EXPLICIT_HANDOFFS`；Sol high已验收、Astra high独立审查PASS。真实删除0、迁址0、junction变更0；五入口owner行动未实施，四共享根补丁未应用。
- 本子任务独占：`docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/`、本卡；仅增补 `projects/skill-research/README.md`、`projects/unpack/README.md`、`projects/distribution/README.md` 当前导航，保存小前像，不覆盖历史或他人新增。
- 并行写域：另一Sol维护 `scripts/project_layout/retirement_runtime.py` 及父级runtime材料；我不改其文件。四共享根只产新全范围hash补丁不应用；B00/B01、其他任务卡、主线源码/数据、旧树和真实junction只读。不发其他聊天消息。
- 目标：把完整6935项去向的研究/恢复消费者、5个历史隔离入口交接、当前导航准备成可执行前审阅材料；无大数据副本，新文档小于1MB。不将旧28项子集补丁冒充全范围。
- 已核：5/5 junction均真实mount-point并精确指旧root；135 payload成员与manifest、外围3件（139存续研究文件）、两恢复manifest、P特定12340B源码和P/v7冻结身份。该树另1个ZIP待删，现存140不等139保留。历史周期主持仅为负责人线索，不能推断当前使用者。
- 准备：逐入口绝对路径/target/周期/负责人线索/转交短提示词；先保留迁址5317、再切5junction、最后旧source删1607的明确顺序；同父临时junction验读、两次rename窗口与失败回退；新根不能回指旧根的只读检查及RAM mock反例；四共享根完整补丁、基底SHA、三项目导航回执和局部ignore拟稿。
- 入口：[handoff README](../project-layout/20261108-packaging-runtime-ready-v1/handoff/README.md)、[主持短交接](../project-layout/20261108-packaging-runtime-ready-v1/handoff/handoff-to-host.md)、[检查](../project-layout/20261108-packaging-runtime-ready-v1/handoff/check_handoff.py)。
- 验证：当前只读checker复跑PASS；RAM可复跑脚本 `test_handoff_contract.py` 的10个映射正例、13个反例通过（含newroot/祖先/nested payload/P alias与5小件身份变更），未创建真实junction；`git apply --check shared-navigation.patch`通过但未应用。
- 下一步：主聊天独立验收并汇入Astra终审；用户转交5历史入口/四共享入口整合权，原整合者确认无人使用及短窗口；存储治理owner确认外部恢复映射（不改P/v7）；最终具体删移授权前不实施物理动作。主线无需停工。
