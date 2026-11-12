# 阅读页正式整合、等级合并与候选数值检查

- 状态：完成。本聊天为整合者；原版指reader_full_20261106展示页，不重建主线解析。
- 授权：并入已接受的测试版，合并只差数值的额外能力等级展示，排查紫色候选是否逐项进入对应描述，清理本任务临时文件。
- 写入：scripts/skill_reader_preview/web/及其生成器、验证脚本、README；output/character_skills/reader_full_20261106的前端及audit/presentation_release_20261107；本任务记录和原试验任务收尾。
- 临时清理限：本任务创建的scripts/skill_reader_preview/inline_trial、output/character_skills/reader_inline_trial_20261107。先迁移必要源码/验收记录，确认原版通过，再删除重复数据及试验源码；旧预览URL保留轻量跳转。不清理其他任务、原始输入或已交付包。
- 子代理purple_audit只读审查候选答案，不写入；额外能力模块若并行由独立worker负责。其他主线任务不受影响。
- 接手输入：原版已审C18冻结数据2236卡/41665原始描述/35404答案。当前C19主线不在本次前端刷新范围内。


## 实际交付

- 已合入正式展示源web/和原入口reader_full_20261106，前端刷新未重跑主线数据；2237份数据文件与build_receipt逐哈希保持。主线快照仍为已审C18，不混入在途C19。
- 额外能力495组仅数值变化的等级合并，2486技能段→524；5127原行均可追溯。350、30315从5个等级段合为1段，按1/2/3/4/最高顺序显示32/34/36/38/40%。不同条件或对象文字不合并。全部等级绑定与未绑定答案保留，不能只保留首级。
- 紫色全库检查：原句外452项，加原先已句内4项；其中448项现均句内，句外紫色0。另8项为实际用途待确认或沙漠/森林矛盾，灰色保留常显，未强行绑定；详情在purple_audit.json。回复候选定位到小幅回复/小回复，不贴到解除异常状态旁。
- 人数递增候选保留“人数递增效果仍待确认”，不写成每人增加；所有新增句内紫色保留实际条件或简短待确认提示。×C与固定防御系数原义不变。
- 全库verify_inline、verify_merge、verify_levels、verify_purple，以及分页/筛选/返回位置回归通过。浏览器原入口、旧URL跳转、等级数列、候选位置、390px窄屏和控制台检查通过。输入原始数据不变，此为展示与映射验证，非新增实机验证。
- 临时目录已清理：测试源码inline_trial/删除；测试输出重复数据及前端删除，释放131651780字节（约132MB）。原测试URL只留index.html跳转与README。必要历史回执/截图在正式页audit/presentation_release_20261107/trial_history/；previous_frontend.zip是小型前端回退副本。清理范围未涉及其他任务或原始游戏资源。
- 正式验证脚本：verify_inline.js、verify_merge.js、verify_levels.js、verify_purple.js；前端模块inline.js、levels.js。后续只在正式源维护，不能重建已退役试验副本。生成器已修正skilltext命名，并兼容旧冻结数据。
- 验收入口：output/character_skills/reader_full_20261106/audit/presentation_release_20261107/；关键文件purple_audit.json、levels_validation.json、merge_validation.json、inline_validation.json、browser_validation.json、cleanup_receipt.json、extra-desktop.jpg。
