# 剩余 output 统一整理：最终授权包（尚未实施）

当前状态：READY_TO_REQUEST_FINAL_AUTHORIZATION_WITH_WINDOW_GATES。候选与保护方案准备完成，Sol执行，Astra独立复核；用户最终物理授权未取得，真实窗口未开始，新位置实际验收未进行。

先看 [完整授权清单](AUTHORIZATION.md)，再按需要看 [精确动作JSON](authorization-scope.json)、[目录映射CSV](directory-moves.csv)、[195入口CSV](alias-actions.csv)、[192文件动作CSV](file-writes.csv) 和 [执行与恢复顺序](execution/RUNBOOK.md)。这些文件是本轮唯一授权范围，不叠加旧完整补丁，不把历史提示词视为许可。

31目录加2个顶层控制文件，189普通入口（含新增64）拟切换并保留previous，六独审入口保留原对象但退役旧直读／原现场精确重放，改用经真实新根身份派生的只读路由。六KEEP目录、旧批次、冻结数据和所有删除均不在范围。

C20现在无需全停。用户授权后，相关生成／校验／隔离输入构建和缓存进程在自然断点让出，刷新临窗条件，通过后自主开一次最长60分钟窗口。主线无关研究继续，不再找主持。漂移不覆盖、到期不顺延。

[REPORT](REPORT.md) 列候选验证与局限；[acceptance](acceptance.json) 绑定本轮证据；[Astra结论](astra-review.json) 是候选独审，不能代替搬后实际独审。只读门1871项通过不证明没有句柄或现在可搬。

未修改正式代码、根导航、selector、locator或业务联接，未迁移／删除／提交／推送。保护测试留下的两份pyc因自动审批拒绝清理而保留，不在部署或迁移清单；详见protection/PREPARATION-DIAGNOSTIC.md。
