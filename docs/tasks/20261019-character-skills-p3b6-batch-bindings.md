# P3B6：已有字段答案到完整描述的受控复用

- 负责人：C `/root/p3b6_implement`；状态：C已冻结，待独立D审查；2026-10-19。
- 目标：先核普通 type8/26 的严格完整片段、原值、真实 sub 与全部角色引用场景；必要时仅看 type51 简单句。主持定范围前不修改正式绑定实现或 profiles。
- 写入：本卡；`work/character_skills_p3b6/`；`output/character_skills/description_bindings/p3b6_batch/`。后续经主持定范围才写必要绑定模块/生成集成、当前 profiles/gaps 及本线 HANDOFF/STATUS。
- 共享依赖：现有 `.venv`、缓存 v3、APK 主表、已审普通字段规则与 native 证据；全部只读，不改依赖环境。
- 边界：21 条 type8 与 2 条 type26 历史绑定原样保留；不把字段 BY_TYPE 答案提升为逐条评审；不扩大未知槽语义，不改历史分母、不做 type68/73。
- 最近更新：阶段A完成；开工完整records/profiles/rules/summary已快照；证据见`output/character_skills/description_bindings/p3b6_batch/PHASE_A.md`及inventory。type26整句89/109页，83/83页仅结构候选上界；建议先冻结无sub两条＋仅type9叶子一条，共3/3页。type8无sub新攻移句仅330一条；type51没有local数值答案，不开语义研究。三个近完整角色诊断及直接受影响角色剩余句均列出。
- 阶段B主持授权：type26固定30123300/3112/3255；type5追加cid29完整纯直线句，并允许同执行侧/控制向量小队列。实际冻结type5为29/2045/2058/5052/10039/58001六条；2022sp2不同、8062/58006flags不同、5047pattern与附加句、denju另域均排除。type8局部方案不实施。
- 最近实施：新增batch_bindings及冻结scope、p3b6_native，最小接入profiles；旧字段规则和旧绑定实现未改。type5有界原生10/10通过，未追外部能力全集；尚待正式重建、专项/零破坏、相关CLI/DOM、必要verify/raw与稳定性。
- 已完成：6条type5＋3条type26，共9唯一/9页描述及9唯一/9页效果槽，字段+0；真实91/提示11601/未知29903，分母41595不变。独立重算所有角色仅cid29部分→完整，当前部分2235/仅未知0/完整1；24未知字段仍留。旧82013完整对象/重复数、277旧已用规则、101/31、全部旧绑定及旁句保留。
- 必要自检：有界原生10/10、专项9/9、91边界/91、原JSON9/9、GBK8接口、DOM14/14、verify189/189、A—P overall_ok；profiles/gaps相关重建稳定性见rebuild_check。未改verify期望或分母。
- 下一步：冻结交独立D，C停止写入；交接`output/character_skills/P3B6_HANDOFF.md`。阶段A与历史审查/交接快照保留，不提交推送发布。
