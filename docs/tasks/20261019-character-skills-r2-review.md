# 角色技能页 R2 独立方法审查

- 负责人：`/root/card_pages_r2_review`；GPT-6 Astra / high，独立新上下文；主持 `/root`。
- 状态：F1–F5原审查者定向复验全部闭合，PASS_WITH_EXPLICIT_SCOPE_LIMITS；按用户要求完成后暂停，不启动全量；2026-10-19。
- 写入范围：本任务卡、`output/character_skills/review/r2_20261019_methods/`、`work/character_skills_r2_review/`。
- 只读范围：全部实施源码／页面、profiles/common/rules、原始输入、旧 R1／任务0及其他审查。不开全量、不新 native、不重跑旧全链。
- 审查四组：四联指标与推断边界；同源基础字段；原位置去重及分母映射；冻结旧名册的 cohort／续跑失败保留／全量后实际行审查方法。
- 沿用：用户确认的旧 11 卡与 R1 174 行、任务0限定 FORWARD。4496 只是关联范围。当前不对改动中的页面给 PASS。
- 下一步：直接核 5 个披露案例原候选／规则、30004 的两个双位置文本和 7229／30236 主表原值；向主持报告方法风险。冻结后做最小有界执行核查并交 REPORT.md / checks.json。
- 冻结前补查：主持预览发现home错连worldinfo；独立直接原表＋既有IsTargetHome证据确认home应查homelist（7229義勇軍、30236湖都）。此前worldinfo同记录所属join计划撤回，见审查目录 `home_namespace_review.md`；不修旧roster，不新native，等待更正后的冻结版。
- 最终方法初审：69冻结项一致；11卡387语义及原span一致，四联185/47/165/202，原文A∩确认27；计划34/290/436/1476、790审查集合一致。独立7229/30236有界运行及29内存别名夹具发现F1跨cohort覆盖队列、F2漏声明3个嵌套数据源、F3替换失败假保留、F4ordinal虚分同引用别名、F5攻速单位/夹具证据标签未分层。入口 `REPORT.md` / `checks.json`，不改实施代码。
- 定向复验完成：新 `20261019-r2-f1-f5-frozen` 的160项一致；独立实际执行34个有界检查全部通过，F1–F5闭合。387行及四联未变；R1最终manifest覆盖旧正式pages29项，29/29独立匹配且本次前后未变。新入口 `REPORT_RECHECK.md` / `checks_recheck.json`；初审和原探针不覆盖。下一步是用户要求暂停，不默认生成760/其余cohort或全量后核读。
