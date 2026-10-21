# 任务卡：角色技能页索引入口两页（选择器首页＋全卡列表页，20261020）

- 任务 ID：`20261020-character-skills-index-pages`
- 状态：**已完成（两页生成＋双通道自检＋浏览器烟雾测试通过）**
- 负责人／对话标识：索引页构建员（GLM 5.3 Flash 260828，动态工作流子代理）
- 日期：2026-10-20

## 目标

为正式角色技能页（`output/character_skills/pages/<cid>/index.html`，v2 玩家版式）
做两个纯静态、离线可用的入口页（与 per-card 页面同目录）：

1. `pages/index.html` 选择器首页：顶部搜索框输入 CID（数字前缀）或名称／称号
   （日文原文，部分匹配），下方即时列出 匹配卡（头像小图＋CID＋名称/称号），
   点击跳 `<cid>/index.html`，回车跳第一个匹配；附全卡列表页与 README 链接。
2. `pages/all_cards.html` 全卡列表页：2236 行（头像＋CID＋名称/称号），按 cid
   升序，点击跳 `<cid>/index.html`；顶部页内搜索过滤（cid/名称）＋数量统计。

## 允许写入（本轮实际遵守）

- 脚本：`scripts/character_skills/card_page_index.py`（新建，本轮唯一新脚本）
- 输出：`output/character_skills/pages/index.html`、`pages/all_cards.html`（新建）
- `work/character_skills_index_pages/check_index.py`（独立自检脚本）
- 本任务卡
- 未改：per-card 页面、`card_page_render_v2.py`／`card_page_batch.py` 等既有生成器
  （未触发任何签名变化）、profiles/原始输入、旧审查报告、共享进度文件、
  `pages/README.md`；未 git 暂存/提交

## 数据口径（要点）

- **cid/name/title**：逐卡取 `pages/<cid>/card.json` 的 `basic.fields` 中
  key=`name`/`title` 的 `display_value`（与 per-card 页 R-07 修复口径一致：
  字段缺失显示 `display_value` 如「外部/网站维护」，不造值）。
- **头像**：一律指向本 cid 自己的 `pages/art/<cid>/icon.png`（相对路径、
  不内嵌 base64、**不跨 cid 借图**）；缺 icon 的 4 个 cid（7107、8234、13001、
  59103）生成时即改为「未取得」虚线占位块（生成期决定，无 onerror 依赖）。
- **库快照信息**：取 card.json `sources.snapshot`（=「cache_full_20261015_v3 +
  APK5.6.2」；生成器逐卡收集并断言唯一值）。
- **四联总指标**：**生成时实时读** `pages/_batch/campaign_latest.json` 所指
  campaign_report.json（`_batch/remaining/runs/20261020T091931839631Z-8fe9d50a/
  campaign_report.json`，四 cohort 汇总）的 `summary`，并与迁移任务卡
  `docs/tasks/20261020-character-skills-layout-migration.md` 记录值交叉核对
  （A 14,539；整行确认 266=记录级 18＋类型外推 248；原文A 13,859；C 27,126；
  整行推断 414；N_all 41,665）——**任何一项不一致即显式失败，不静默写出过期
  数值**（指标变化时需先更新脚本内 `EXPECTED_CAMPAIGN` 与页面文案）。选择
  实时读取而非写死，是因为写死会随下次批量重建悄悄过期；交叉核对则保证
  现值与已交付记录一致才算数。
- **数据提取分母**：cohort manifest `output/character_skills/r2_preparation/
  cohorts/manifest.json` 的 2236 members（与迁移任务同分母）。

## 实现要点

- 内嵌紧凑索引：index.html 内嵌 `<script type="application/json" id="cards-data">`
  （[cid, name, title, icon] × 2236，`</` 转义防提前闭合），纯前端 JS 即时过滤
  （数字→CID 前缀＋包含、日文→名称/称号部分匹配、大小写不敏感），结果上限
  100 条并提示走全卡列表页；不依赖网络/后端。
- all_cards.html 为静态 DOM（2236 个 `<a>`，data-k 属性承载小写 cid+名称+称号
  供过滤），头像 `loading="lazy"`；两页体积分别 118,507 B / 644,256 B（无 base64）。
- 版式沿用 v2 页面同一套暗色 CSS 变量/字体（paper/panel/gold 等），两页页头
  标注数据口径；index.html 页面显示快照行＋四联指标行＋来源指针小字。

## 重建与检查（本轮实际执行）

- 生成命令（仓库根）：
  `& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_index.py --execute`
  → 提取 2236 条（有头像 2232、缺 icon [7107,8234,13001,59103]）；指标交叉核对
  一致；写盘后生成器内置 `run_checks` 通过（跳转目标逐一存在、头像文件逐一
  存在、占位数=4、内嵌 JSON 与 entries 全量一致、盘上缺 {card,whole,icon} 集合
  与任务卡清单逐一核对、59103 无任何图引用）。
- **独立自检**（`work/character_skills_index_pages/check_index.py`，独立于生成器
  重新逐卡重读 2236 份 card.json）：index.html 内嵌 JSON 2236/2236 条逐卡比对
  （cid/名称/称号/icon 位）；all_cards.html 2236 行逐行比对（cid/名称/称号/data-k/
  头像/跳转目标文件存在）；缺图集合 card 31／whole 1／icon 4 与迁移任务卡清单
  一致；无跨 cid 借图；快照唯一值正确；两页来源标注与统计数字在页。
  **结果 PASS，0 问题。**
- **浏览器烟雾测试**（本地静态服务 http://127.0.0.1:8734，测毕已停；IAB 后端
  不支持 file: 故走 localhost，页面本身纯静态无任何服务依赖）：
  - index.html 正常渲染（JS 无错，2236 条中显示前 100）；搜「チーカ」→1 张
    （30236）；搜「30236」→1 张；回车跳转 `30236/index.html` 成功（键事件经
    页面内合成 keydown 验证，落地页 title「チーカ · 30236 技能解读」）。
  - all_cards.html 2236 行、2232 个 img、4 个「未取得」占位恰在
    7107/8234/13001/59103；过滤「チーカ」→当前显示 1 张→30236；统计行
    「共 2,236 张 · 有头像 2,232 张 · 头像缺失 4 张」正确。
  - 头像相对路径实际加载（前 12 个 img naturalWidth>0 全 true）。
- 备注：自动化 `press("Enter")` 在 IAB 后端未触发 input 的 keydown（键事件派发
  层面问题，非页面缺陷）——用页面内合成 KeyboardEvent 验证，处理器正常导航。

## 边界与保留

- 索引数据为**初版快照**：指标与缺图清单对齐 20261020 迁移版（终版签名
  46de0c7c…）；后续批量重建后需重跑本生成器刷新（生成器会对不上旧值时显式
  报错提醒）。
- 搜索为前缀/包含匹配，无拼音/罗马字/模糊音；称号含特殊字符（如
  `"神々の義眼"保持者`、`<豚の帽子>亭`）按 HTML 转义存储、浏览器解码后
  过滤正常（独立自检已覆盖 8283/8066 等）。
- 浏览器烟雾测试为 localhost HTTP 渲染验证，未做窄屏/多浏览器视觉回归
  （与迁移任务同口径）。
- `pages/README.md` 未改（入口页说明由本任务卡承载；如需并入 README §17
  交由整合者）。

## 下一步（供主持/审查方）

1. 用户实际打开 `output/character_skills/pages/index.html` 验收搜索体验；
   如需调整结果上限（现 100 条）或匹配规则改本生成器重跑即可。
2. 下次 2236 页批量重建后：重跑 `card_page_index.py --execute` 刷新两页
   （指标/快照自动取现值＋交叉核对）。
