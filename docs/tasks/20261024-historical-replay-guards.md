# 历史复验缺件防护与影响核查

- 负责人：本 Codex 对话；状态：已完成用户授权的两项，停在交付点（2026-10-24）；误清理恢复事件尚未整体闭合，删除继续暂停。
- 用户授权：修复缺件仍可能通过的旧脚本，逐项核查剩余缺口；禁止删除、覆盖旧审查结果。
- 写入：六个已定位的 work 历史比较／指标脚本；scripts/storage_retention/replay_guard.py、对应定向测试与本轮核查脚本；output/storage_retention/replay_safety_20261024/。
- 不占用：当前页面生成器、正式 pages、根 HANDOFF/STATUS、主持进度文件、原审查报告／checks。
- 结果：六脚本缺件均硬失败（实际检查退出码 2，缺件分别 4/284/755/755/755/14）；17 项定向防护测试通过。实际复跑要求完整旧输入、显式历史新版本／完整签名和新目录；指标不再复用未绑定的旧对账或硬编码旧 PASS。
- 修改前六脚本已按逆向补丁重建并与先前记录的原 SHA-256 全部一致，另存 source_before/，差异 source_diffs/；未用不匹配副本冒充原脚本。
- 逐文件核查 4,072 项：755 JSON 优先恢复独立批 8 初审完整基线；302 JSON 是早期轮次完整复跑必要输入；3,015 HTML 影响旧页面／字节回滚，六 JSON 比较器不直接读取，未判定可删。原 before／receipt／删除记录哈希 4,072 项一致；按 run 的影响矩阵 10 行。
- 本轮恢复 0；累计恢复口径核清为原 11 run 的 3,508＋额外批 10 四基线的 4,472＝7,980，仍缺 4,072。后来三组完整基线各 2,236 JSON＋2,236 HTML 均存在，六份投影快照哈希不变；仅说明可用证据，未运行历史全量复验。
- 58 个旧审查／比较结果前后哈希一致；删除 0、旧报告覆盖 0。当前正式 pages、账本、latest、共享生成器、根交接和主持进度未被本对话写入。所有本对话运行命令已结束。
- 交付入口：output/storage_retention/replay_safety_20261024/README.md；final_validation.json、all_missing_file_impacts.csv、run_replay_impact_matrix.csv、recovery_count_reconciliation.json、source_traceability.json、HOST_HANDOFF.md。
- 后续由主持选定历史版本配对并整合验收限制；有新来源后按 P1/P2 清单和原 SHA 定向恢复。已查两份分享 ZIP、E 盘 VSS、Windows Backup 不重复扫描。没有向其他对话发送消息。
- 历史结论不覆盖；不运行当前版本的全量生成，不发消息给其他对话。
