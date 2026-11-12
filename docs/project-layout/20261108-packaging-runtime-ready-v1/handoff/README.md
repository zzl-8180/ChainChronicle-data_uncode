# 导航与五历史junction交接准备

状态：`PREDELETE_CONFIRMATION_PACKET_READY_WITH_OWNER_HANDOFF_PENDING`。本轮仅准备材料与三项目当前导航增补，未对旧树/真实junction做物理改动，四共享根补丁未应用。

- [交给主持的短交接](handoff-to-host.md)：只交五历史入口和四共享根整合权；不要求主线停工。
- [精确五入口/target/负责人线索/短提示词](junction-owner-handoff.json)与[逐步切换/回退方案](junction-switch-plan.md)。
- [当前真实旧入口只读核验](current-junction-check.json)：5/5真实mount-point junction、target等预期，135 payload成员、完整139存续研究文件、两个恢复manifest、P指定旧源码及P/v7身份通过。仅证明可读，不证明无人使用。
- [只读核验入口](check_handoff.py)与[外围/恢复身份基线](retained-identity-baseline.json)：不运行历史脚本，不写文件；new模式显式接收批准绝对路径，拒绝新根/祖先及研究树/关键文件祖先reparse、回指旧根或解析出界。真实新根尚未落地，不声称new模式通过。
- [RAM映射合同模拟](mapping-contract-simulation.json)：五旧/新映射10正例及拒绝非junction/错target/二次alias回旧根等反例；只mock，不创建真实联接，不证明Windows双rename原子交换。
- [完整范围四共享根补丁](shared-navigation.patch)、[当前基底SHA](shared-navigation-base.json)：只供主持审阅合入，不覆盖当前主持工作，AGENTS第8节保持原字节。
- [三项目导航改动回执](project-navigation-receipt.json)与 `navigation-before/` 小前像；原B00/B01和其他任务卡不动。
- [未来历史父目录局部ignore拟稿](archive-local.gitignore.proposed)：未建立新历史目录/目标，不改根ignore。

完整范围仍以 [6935项逐文件去向](../../20261108-packaging-full-retirement-v1/full-disposition.jsonl) 为准：拟删1607项，保留迁址5317项，原位留11项。139研究树当前另有1个拟删ZIP，不能把现存140个文件全称作139保留项。保留材料先精确迁到新位置并核验，再切5入口，最后删旧source候选；禁止先整旧根改名搬走却仍拿旧source清单删除。

可复跑RAM检查（不创建junction，不模拟真实迁址）：

```powershell
& .\.venv\Scripts\python.exe -I -B docs/project-layout/20261108-packaging-runtime-ready-v1/handoff/test_handoff_contract.py
```
