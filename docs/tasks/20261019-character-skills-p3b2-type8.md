# P3 第 2 批：type8 同句候选逐记录核查

- 负责人：C·实施 `/root/p3b2_implement`；2026-10-19。
- 状态：已独立审查闭合；D「带明确限制通过」，阻塞0、需整改0，见[报告](../../output/character_skills/review/p3b2_20261019_type8/REPORT.md)。
- 目标：只核查 APK type8 的 15 个指定候选，确认完整原文、实际 sub、角色引用和同路径条件后，才增加逐记录人工语义对应。
- 写入：`scripts/character_skills/` 必要绑定模块；`output/character_skills/` 当前可重建 profiles/gaps/type8；新增 `description_bindings/p3b2_type8/` 和 `P3B2_HANDOFF.md`；`work/character_skills_p3b2/`；本任务卡。必要时维护 HANDOFF/STATUS 本线入口。
- 禁止：主持进度、P3B1 任务卡/交接/审查、原始输入、AGENTS、参考分析文件、共享依赖；不提交/推送/发布，不再派代理。
- 基线：81500 页字段答案；80659 归一记录内答案行；80642 父 holder 实例键。描述 41595=31 既有+17 P3B1+11613 提示+29934 未知；角色部分2231/仅未知5/完整0。
- 共享依赖：现有 `.venv`、主表和原生镜像/元数据只读；不重跑解包或既有全链原生索引。
- 结果：15候选纳入11/排除4；新增11唯一片段/12页、12唯一效果槽/13页、12角色且与首批无重合。字段答案+0；描述累计31基线+29type8对应+11601提示+29934未知；角色状态0迁移。
- 检查：独立before已保存；专项55/55、verify189/189、8GBK入口、19机器产物重建0漂移、DOM夹具8/8；没有实机或真实浏览器视觉验收。
- 交接：`output/character_skills/P3B2_HANDOFF.md`；逐项裁决`description_bindings/p3b2_type8/candidate_decisions.jsonl`，完整源值/hash/sub/角色来源随附。
- 收口：只更新本批及本线当前文档；机器产物保留审查前冻结快照，PENDING字段以D报告为准，README已明确说明。未改代码/数值、未重跑检查。
- 下一步：停止写入；下一批由主持另派新C。两批各自结论仅覆盖固定记录，不能向其他记录自动推广。
