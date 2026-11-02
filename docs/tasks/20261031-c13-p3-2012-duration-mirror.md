# C13-P3 2012 同卡同记录攻速时长镜像

- 日期：2026-10-31；周期：C13-P3（实质语义批次3/3，候选阶段）。
- 状态：**正式交付完成；候选及正式独立审查PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0；3行3答案、完整+3**。
- 实施：`new-provider/deepseek-v4-1-flash-261017` high；例行独审：`new-provider/deepseek-v4-pro-ga-260813` high。
- 方案：`docs/角色技能完整解读实施方案.md`（2026-10-31现行），C13总卡 `docs/tasks/20261031-c13-cycle.md`。

## 目标与范围

候选3行3答案：
- 30255 `pattern0-lvorder0-f3`「さらに自身の攻撃速度が一定時間上がる。」；
- 30306 `pattern0-lvorder0-f5`与`pattern1-lvorder1-f5`「また自身の攻撃速度が一定時間上がる。」。

三行已有同记录`skilllist|2012|/param6=-0.325`攻速答案，唯一未解目标为时长；同卡skilltext同文行已有同一2012记录的`param0=30`时长答案。只补`skilllist|2012|/param0=30`游戏秒，不重复添加param6。

镜像扫描：`work/c13_20261031/mirror_scan.json`。非Y.G.连带0。

## 实施要求

1. 新模块限 `scripts/character_skills/card_page_inference_c13_p3_2012_duration.py`；候选输出限 `output/character_skills/c13_p3_2012_duration_20261031/`，自身work限 `work/c13_20261031/p3/`。
2. 逐行证明目标pattern行与skilltext行同卡同文、目标已有param6与peer param0来自同一skilllist record_id、同一原始JSON pointer和raw；核对pattern→bossskill→s_ability→2012链与slot，不能仅按文本或数值镜像。
3. 只补param0正时长30游戏秒；不重答param6，不把间隔因子当动作周期，不写最终攻速、永久、实际装载或实机。30255与30306两个pattern分别保留自己的pattern／slot条件，即使共享2012子记录也不合并来源。
4. 数值与关联证据按既有来源级别保持，镜像归属为推断；旧答案、S3／S7和未覆盖子句保持，不宣称整行完整。
5. 不处理其他卡、其他效果或p2／p3等新字段；保护卡20234、30102、30236、30239硬拒绝。
6. 自检覆盖3正例、同文异record／异slot／异raw反例、已有param6保护、非正时长拒绝与保护卡；输出README、候选JSON、检查脚本和结果，不运行正式全库生成。

## 独立审查

审查者独立核对3行完整来源链、param0单位与换算、param6零重复、对象／条件／证据档和账本效果归属；报告写 `output/character_skills/review/c13_p3_2012_duration_20261031_deepseek/REPORT.md`。默认初审一次，集中修复后定向复核最多一次。

## 允许／禁止

只写上述模块、候选输出、自身work和指定审查目录；不得改共享生成器／账本／rules／正式pages，不得新原生、实机、新缓存、正式全库生成、清理、Git、发布或C14。
