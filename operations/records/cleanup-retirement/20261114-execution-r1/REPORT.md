# 清理执行完成

用户批准的精确清理已执行，四个阶段均经新开的子代理审核通过，阻断0。运行ID：`cleanup-20261114-0ae961a99b48`。授权绑定最终准备包 `364646aba25894e65e7cd1cc23a65d4e69cd614463e799f878928fb69f516881`；原准备包的 false/null 保持历史原样，实际授权、日志、states及TARGET/POST另建并串联。

| 阶段 | 实际结果 | 审核 |
|---|---|---|
| Copy-first | 2,466项复制、关后重开SHA/长度读回；审核时原件完整 | [PASS](audits/stage1-copy/REPORT.md) |
| 消费者及TARGET | S7 148/139/135；S6 84独有、168依赖、51答案；S4 2234来源/2231引用页/2233名/5164句对、2236卡及89/811答案一致；真实TARGET通过 | [PASS](audits/stage2-consumers-target/REPORT.md) |
| 旧源及联接 | 2,466旧源逐项移除，五个junction叶退役，六个别名保留；真实POST及TARGET谱系复验通过 | [PASS](audits/stage3-old-sources-post/REPORT.md) |
| 精确删除 | 65,639项逐件重新核对祖先、普通文件、dev/ino/nlink/mtime、长度与SHA后删除；112项KEEP保留 | [PASS](audits/stage4-final/REPORT.md) |

## 分支结果

| 分支 | 删除候选实际删除 | 迁入保留 | 原位KEEP |
|---|---:|---:|---:|
| S2 音频派生件 | 17,389 | 0 | 清单外图文/原tar/bdl不动 |
| S5 独立分析退出 | 42,912 | 2,234，供S4使用 | 100（包含B01的11项） |
| S6 临时研究退出 | 169 | 84独有证据，168依赖已由S7新址承接 | 另1替代源继续原位 |
| S7 旧支线退出 | 5,169 | 148 | 12，含根ignore与11原位件 |

删除候选和REHOME旧源不重叠，共移除68,105个旧普通文件路径；迁入新址的2,466件保留。未递归删除目录，没有顺带清理未登记文件或父目录。

## 容量实测

删除候选逻辑大小 **12,218,673,553 B**。执行前条件完整簇量 **12,339,138,560 B（约11.49 GiB）**。

本次精确DELETE窗口：2026-11-14T02:25:05.930558+00:00 至 2026-11-14T02:35:37.266403+00:00，卷可用空间从 **187,854,737,408 B** 到 **205,909,942,272 B**，实测净变化 **18,055,204,864 B（16.82 GiB）**。这是实测卷空间差值，包含日志分配及其他磁盘活动，不能等同逐文件净释放计数。执行期间在该窗口前还出现约70GB其他卷空间变动，因此不把整段对话的空间增量归因本清理。Copy-first临时占用已通过旧源处置归并；本轮回执、日志和独立Reader验读输出继续保留。

## 当前入口与证据

- [新旧来源定位映射](source-locations.json)：2,466项迁址与169项S6替代关系，含84项独有证据；冻结历史字符串不改写。
- [Reader导航](../../../../projects/reader/README.md)：实际读取已安装映射的 `reference_source_route.py`，支持新址重建及Unicode/#片段定位。独立验读页保留旧组装器“模拟”标签，未冒充正式阅读器发布。
- [实际授权](user-authorization.json)、[源处置批准](source-disposition-authorization.json)、[DELETE精确批准](delete-authorization.json)、[最终状态](final-status.json)。
- [正式TARGET/POST目录](../../retired-packaging-rehome/20261113/cleanup-20261114-0ae961a99b48/)：TARGET绑定真实COPIED_VERIFIED日志；POST另绑MOVED日志、states和原TARGET回执，没有预造或复用日志。
- [当前导航差异及回退前像](navigation-changes.json)；[Git只读最终观察](git-final-observation.json)。未暂存、提交或推送Git。

## 执行中发现及处理

1. S5/S6原检查器被函数方式调用时，旧报告函数要求CLI argv[1]，第一次退出1。仅调整本轮报告适配，保留消费者逻辑和末端身份核验；复用已成功的真实Reader构建，恢复退出0并经阶段2独立审核。
2. 新安装S4映射继承了提案的 current_installed=false 元数据。保留修改前完整字节和原消费者回执，仅改此字段为true，记录旧新SHA并重新实读Unicode片段。内容来源和行为不变，独立审核通过。
3. 删除函数的扩展Windows disposition模式在独立夹具上不受支持；切换为经过普通/只读样本、错身份/错SHA/越界负例验证的标准handle disposition。业务文件首次删除前已通过夹具验证。
4. 旧127项特殊保护中3项本就属于批准REHOME（两技能manifest及一份隔离源码）；处置后按精确新址保持原SHA。112项原位KEEP没有减少。七项Git KEEP分类历史提示保留解释，未当作漂移修复文件。

所有阶段审核由真实原生OpenAI gpt-6.1-sol子代理完成，阶段1/2 high、阶段3/4以实际委派参数为准；不是第三方R4复审的替代或伪造。既有R4结论、prep184项绑定、三个ignore、六个历史工具、冻结reference_pairs和证据README保持边界。后续额外清理或Git处理需要新的具体任务，不重放本次已履行授权。
