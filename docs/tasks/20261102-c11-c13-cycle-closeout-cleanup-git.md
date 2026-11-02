# C11—C13 周期收尾：A/B 清理与 Git 闭包

- 日期：2026-11-02；主持：本会话 `new-provider/kimi-k3-1-pro-261024`。
- 状态：**清理与Git收尾执行中，C14未启动**。
- 授权：沿用用户已确认的每周期第三方审查闭环后推送Git、每周期自动清理到B类；本轮用户明确要求按C14规划执行，先完成C13收尾。

## 范围与保护

1. 复用既有 `scripts/storage_retention/cycle_closeout_20261031.py` 实现，新增本周期专用 `cycle_closeout_c11_c13_20261102.py` 和 `output/storage_retention/cycle_closeout_c11_c13_20261102/`，不覆盖旧目录。
2. 仅处理当前12个retained run的transaction payload：与当前正式页同哈希的A类，以及先建立可恢复归档的不同内容。无额外派生账本删除。
3. 默认保护当前正式pages、rules、正式账本、原始输入、全部审查证据、G1有效归档、run顶层元数据及C类文件。C11/C12 R3、C13终审和空ID最终复验文件均纳入保护。
4. 先 `archive_store build/verify/restore`，再 precheck、10件微批、全量执行与postcheck；失败不静默，未验证存活副本不得删除。
5. Git只按实际diff/依赖形成显式清单，提交并推送main的已配置上游；不批量暂存，不接管UI、参考分析、根目录杂项或其他改动，不强制推送。

## 验收

- 白名单、归档、恢复、journal与实际删除完全一致；当前正式页面／rules／账本／审查证据前后不变。
- 容量只通过既有 `run_retention.release_reservation` 释放，限额不放宽。
- 记录逻辑删除量、归档新增量及实测空间，不把归档动作写成净释放。
- 清理与Git完成后才进入C14候选预筛；C14正式生成不重用C13的首次生成次数。

## 当前基线

- C13 campaign：`f0b36c7f0c40284bf8c25a74e3014d34884c2deabaa436815f4de5e62abcb357`；snapshot `f0b36c7f-cf9451c6ff47fcfb`；rules 294键未改。
- RETAINED 12/12，reserved_bytes 7,854,192,286 B。C13数值交付与空record_id R01均已闭环。
