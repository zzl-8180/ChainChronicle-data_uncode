# 额外能力等级全库展示普查

- 状态：子模块完成、已交主任务整合；2026-11-07；负责人：当前阅读页主任务的 extra_level_fix 子代理。
- 目标：全2236卡普查仅数值变化的额外能力，消除原文数值与逐等级答案重复，保留实际结构变化、来源和可信度颜色。
- 写入：`scripts/skill_reader_preview/web/levels.js`、`verify_levels.js`、`verify_levels_full.js`；`output/character_skills/reader_full_20261106/audit/extra_levels_20261107/`；本任务卡。
- 协作：主代理维护 app.js/inline.js 等前端；本任务不运行 build，不写冻结 data，不改主线。其他任务改动不撤销。
- 输入：冻结阅读页2236份 `data/cards/*.js`。
- 当前发现：494卡2486等级技能；468卡为仅数字变化，26卡有日文结构/术语变化。严格同日文数字骨架的中文骨架差异为0。现有合并分段本身成立，重复来自渲染再次列出逐级答案。
- 交付：`CC_LEVELS.presentation(row,inline)`输出数字部件/颜色与补充计划，原文已有数字不在下方逐级重复；3452个bound答案由原文呈现、11个来源答案合为3个补充项；879个金色数字位置、4980个原文蓝色位置，颜色不升级。单独结构变化段加extraLevelStage也适用。
- 检查：`verify_levels.js`与`verify_levels_full.js`均PASS，2236卡、5127源描述全部保留，输入内容不变。回执及逐卡清单见`audit/extra_levels_20261107/README.md`。
- 下一步（主任务）：app.js接入presentation.textParts与visible；前端build和浏览器验收。本子任务未运行build。
