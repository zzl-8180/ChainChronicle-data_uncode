# B02 小体积候选适配与验收

2026-11-08。**本次受控前端候选已生成并通过限定范围验收。** 采用 Sol 执行与只读复核、主聊天整合。B02 完整生成链移植及正式站点切换没有实施；其他批次未启动。

## 当前结果

- 新候选：[index.html](../../../projects/reader/site/b02-20261108-v1/index.html)，7 个文件，127,531 字节（约125KiB）。
- 实现及重现命令：[适配器说明](../../../scripts/project_layout/b02_candidate/README.md)；原生成器与前端源码不修改。
- 数据、2236卡片、旁注、媒体、历史audit都在原路径只读加载，没有复制或移动。候选不是可脱离本项目的独立发行包。
- 用户追加空间约束后，原436MB整树复制方案未执行。项目内本轮新增总量低于10MiB；最终逐目录数量见 [空间与文档检查](validation.json)。
- 主持实际会话已核：只接收登记和保留 Web 补证，没有吸收语义或改变主线基线。[消息依据](host-receipt.json)。

## 实际改变与版本边界

候选只改 index 的五个数据脚本地址，以及 app 的固定路径配置、图片路径、详情懒加载路径和历史审查链接。新增 paths.js。历史链接明确标“查看源版本审查（历史）”，在新标签打开。其余展示算法、数值、条件与置信度不变。

receive01 固定源 runtime 身份和候选前端哈希；validate 与 serve 必须指明该 receive run，源或前端漂移即拒绝。源版本仍是 C19 snapshot `99bee2a1-cf9451c6ff47fcfb`。原 C18 守恒 baseline、整改前 C19 标签 baseline、R01生产封存与V01验证器身份保持原位，不相互替代。

当前 source adaptation 仅验证原位数据的身份与 primary 源哈希；本次 composition 另绑定候选前端和源载荷。Full/C19/R01/V01 的语义证明按原范围继承，没有重跑，也没有把旧 seal 当成候选 seal。完整接口与写域见 [scope.md](scope.md)，运行准入见 [runtime-gate.json](runtime-gate.json)。

## 已执行检查

| 检查 | 实际结果 |
|---|---|
| receive01 | exit0；候选7文件，nlink=1；源runtime读取前后相同 |
| validate01 | exit0；原位source adaptation身份通过，5个JS语法通过；接收与验证之间身份一致 |
| 实际候选模块接线 | 原验证逻辑读取原数据、执行候选inline/branches/levels；14,475项，2236卡、883选择条件、394父记录；exit0 |
| HTTP白名单 | 24项通过；所选资源200并no-store，根AGENTS/raw/未声明回执/audit目录/路径越界404 |
| 浏览器 | 实际IAB HTTP：分页、搜索350/30236、两卡详情、返回保留筛选、原位图片、历史审查新标签通过；1280及390px无横向溢出，完整卡图保持2:3，成功标签无console警告/错误 |
| 保护锚点 | 23个选定共享入口/正式回执/源码锚点前后相同；不宣称全项目全树重哈希 |
| 空间 | 最终内容字节及上限验收见validation.json；不为腾空间删除旧成果 |

原始本次回执：
- [receive01](../../../output/project-layout/b02-20261108-v1/receive01/receipt.json)、[接收输入身份](../../../output/project-layout/b02-20261108-v1/receive01/input-manifest.json)。
- [validate01](../../../output/project-layout/b02-20261108-v1/validate01/result.json)、[候选组合](../../../output/project-layout/b02-20261108-v1/validate01/composition.json)、[真实Node命令/退出码](../../../output/project-layout/b02-20261108-v1/validate01/branch-wiring-process.json)。
- [HTTP检查](../../../output/project-layout/b02-20261108-v1/serve02/http-validation.json)、[实际浏览器记录](browser-validation.json)、[保护检查](protected-after.json)。

最初 sandbox 服务无法被主机浏览器连接；诊断保留在serve01。自动权限审查通过后，使用同一已审服务代码在主机127.0.0.1:8779启动独立临时服务，不改代理/防火墙、不绑定外网、不占正式端口。receive/validate源码版本与随后仅加no-store的serve版本分层记录在serve01/launch.json及serve02，未覆盖旧执行身份。验收后停止本次临时服务，停止回执见运行目录。

## 使用与未完成范围

HTTP模式已验收。启动入口为：

```powershell
& ./.venv/Scripts/python.exe -B scripts/project_layout/b02_candidate/adapter.py serve --port 8779 --receive-run receive01
```

这只启动候选预览，不切换正式站点；若端口已有进程，换空闲端口，不能停止他人的服务。浏览器进入对应端口的 `/projects/reader/site/b02-20261108-v1/index.html`。本地执行环境若限制套接字，需在允许本机loopback的环境启动，不改变网络安全设置。

`file://` 直接打开被浏览器工具的协议策略拒绝，**未验证**，没有改用其他工具绕过；不能把相对路径设计当成双击浏览器已通过。代表性浏览器验收也不等于逐卡视觉或实机游戏验证。截图只在工具内观察，未另存大图。

本轮只交付低占用的既有载荷前端路径适配。完整build/sample/merge/历史证据生产链接口迁移没有启动；正式服务、共享根入口、latest、冻结原件、历史独审、主线答案及账本保持不变。候选仍依赖原位数据：后续若吸收Web补证或更新源载荷，应创建新候选身份并做受影响检查，不能绕过漂移拒绝沿用旧回执。

回退只需停止候选服务并继续用原站；本轮没有对正式产物的回退操作。保留候选、运行记录和失败诊断，不自动删除。

