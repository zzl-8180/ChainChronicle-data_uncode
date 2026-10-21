# 角色技能页 · 数据库样式示例渲染器（展示层实验）

- 日期：2026-10-20
- 状态：第二轮完成（三张示例接入 full_unpack 立绘并重新渲染，内置自检＋独立自检通过）
- 负责人：数据库样式示例员（动态工作流子代理）
- 参考版式：`其他人的参考/数据库-《Y.G.1515》光耀の騎士 カイン.png`（只作版式参照，不借其数值与图片）

## 目标

按参考数据库页版式（深色底）做**展示层实验**：输入 cid 列表，从
`output/character_skills/pages/<cid>/card.json` 读数据，输出单文件 HTML 到
`output/character_skills/dbstyle_samples/<cid>.html`。不是正式 card_page 生成器，
不改 `card_page*.py` 主链与 `pages/` 正式产物。

## 允许写入范围

- 脚本：`scripts/character_skills/card_page_dbstyle_sample.py`（本任务唯一脚本）
- 输出：`output/character_skills/dbstyle_samples/`（含本 README 说明的任务卡即本文件）
- 不修改：card_page 主生成器、pages/ 正式产物、profiles/、旧审查报告、共享进度文件

## 运行命令

```powershell
& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_dbstyle_sample.py
# 可选参数：--cids 30236,7616,10001  --pages-dir ...  --out-dir ...
```

## 产物

| 文件 | 说明 |
|---|---|
| `output/character_skills/dbstyle_samples/30236.html` | 基线卡 チーカ（确认行最多：58 行，46A/12C，整行确认 18，原文A 28，答案行 134，推断 0） |
| `output/character_skills/dbstyle_samples/7616.html` | 随机 remaining 卡 ブカフィ（8 行，4A/4C，整行确认 1 且为「确认（类型外推）」BY_TYPE_EXTRAPOLATED） |
| `output/character_skills/dbstyle_samples/10001.html` | エル（52 行，9A/43C，整行确认 0，含 type1017 模板推断行：16 答案中 3 条「推断」TEMPLATE_PILOT_1017） |

## 版式对应参考图

| 参考图区域 | 示例实现 | 数据来源 |
|---|---|---|
| 顶部卡名/称号/星级/COST | 标题行＋★行＋COST | `basic.raw_record`（name/title/rarity/cost） |
| 左上卡图 | 深色虚线占位块，写明 `NO_VERIFIED_BINDING` | `basic.card_art`；不借参考图 |
| 左侧基础信息表 | 职业/所属/攻击类型/成长/暴击几率/攻击速度/获得来源/画师/声优/登场日期＋附加武器ID/主表初始ATK/主表初始HP/介绍 | `basic.fields` 的 `display_value`/`evidence`、`basic.external`（画师/声优/日期）；card.json 无来源的字段（攻击类型/获得来源/登场日期缺外部值时）显示「外部/网站维护」 |
| 右侧等级 ATK/HP 表＋成长曲线 | 整块显示「外部/网站维护」，不按截图编数 | `basic.external.等级成长表` 即外部资料 |
| 技能区（深色组标签＋右侧条目） | 13 组按 card.json `groups` 渲染；仅「已配置且有技能」的组出节，空组在底部以「本输入快照未关联」条列出 | `groups[].label/skills` |
| 逐技能 | 名称、费用（cost_state）、档位/等级、引用字段 | `skills[]` |
| 逐描述行 | 日文原文＋行内数值（A 行值行）＋证据标注：确认=绿、确认（类型外推）=绿虚线框、推断=橙、未知=灰；条件以「条件：」标签内联在值行后；未知行 unknown_reasons 用 `<details>` 折叠 | `rows[]`：`row_class`/`evidence`/`evidence_scope`（REVIEWED_RECORD→确认；BY_TYPE_EXTRAPOLATED→确认（类型外推）；TEMPLATE_PILOT_1017→推断）/`answers[]`/`unknown_reasons` |
| 页脚 | 四联指标（A、整行确认、原文A、C 各 count/denominator）＋数据快照/来源＋「示例渲染，数据来自 card.json」声明 | `summary.A/whole_row_confirmed/original_A/C`、`sources.snapshot/input_root` |

## 自检（本轮实际运行）

命令：`& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_dbstyle_sample.py`

结果（全部 PASS，脚本内置 `run_checks`）：
- 三张 HTML 均生成且非空（70151 / 12628 / 35412 字节）；
- 逐行比对：每个 row_id 恰好出现一次、每行日文原文、每个答案值字符串均在页面中（30236 检 227 项、7616 检 36 项、10001 检 111 项）；
- A/C 行数与 `summary.A.count` / `summary.C.count` 一致（46/12、4/4、9/43）；
- 无来源区域全部显示「外部/网站维护」（30236 页 6 处基础表/成长区、10001 页 9 处），未出现编造数值；
- 页脚四联指标与 `summary` 逐项相等。

## 已知边界

- 本示例只做展示层，不改变证据等级；「确认（类型外推）」「推断」沿用 card.json 原有标注，不在渲染层升级任何证据。
- ~~卡图无验证绑定，全部占位~~（第二轮已接入 full_unpack 解包立绘，见下方追加记录；此处保留首轮历史）。
- 未做浏览器渲染视觉回归（本轮仅静态 HTML 与文本级自检）。

---

## 2026-10-20 第二轮追加记录：接入立绘并重新渲染

### 立绘来源与绑定证据（本轮实际核实）

- 全部三张卡（30236 / 07616 / 10001，目录名按 5 位零填充）在
  `output/full_unpack/objects/` 有解包 PNG，逐文件用 `ls`/`stat` 核实存在与字节数：
  `Card_OrgSize/cha_2d_card_<cid>/cha_2d_card_<cid>.png`（整卡）、
  `Trimmed_Whole/cha_2d_whole_<cid>/…`（全身/局部）、`Card_Icon/cha_2d_icon_<cid>/…`（头像）、
  `Card_LongVer3/cha_2d_tanz_<cid>/…`（长版，本轮未上页面）。
- 绑定方法证据：`output/card_images/cid30236/binding_evidence.json`（本轮读取）——
  `CharacterFactory.GetCharaTextureNameFaceBustUp`(metadata 6583)、
  `GetCharaTextureNameWhole`(6584)、`GetCharaTextureNameIcon`(6586)，参数 `cid`，
  含 native_rva 与 code_sha256；字面量表含 `cha_2d_whole_`、`cha_2d_icon_` 前缀。
  该方法证据为 cid 参数化通用方法，证据文件现存于 cid30236 目录，三卡共用同一绑定依据文案。
- 解包台账：`output/full_unpack/ledger.jsonl` 本轮 grep 核实
  `cha_2d_card_30236/07616/10001.bdl` 三条，`processing_status: ok`、
  `source_snapshot: phone_20261015_full_02`、`detected_format: bdl_xor_unityfs`、
  含 source_sha256/decoded_sha256；各对象目录 `objects_index.json` 记录 bundle 与导出对象。
- cid30236 专属：`output/card_images/cid30236/manifest.json` 状态
  `PORTRAIT_CONFIRMED_FULL_BODY_NOT_LOCATED_PARTIAL_ART_EXPORTED`；逐图 role/status 本轮读取为
  portrait=CONFIRMED_CLIENT_ID_BINDING、standing_partial=CONFIRMED_CLIENT_ID_BINDING
  （原文注明「画面边缘截断身体及装饰，不是完整全身立绘」）、
  bustup=CONFIRMED_CLIENT_ID_BINDING、card=CARD_VARIANT_CONTAINER_AND_VISUAL_MATCH。
  **页面如实转述：30236 的整卡不标注为全身体已确认。**

### 渲染器改动（仅 `scripts/character_skills/card_page_dbstyle_sample.py`）

- 新增 `load_art(cid)`：按 5 位零填充 cid 从 `output/full_unpack/objects/` 读
  Card_OrgSize（主图）/Trimmed_Whole/Card_Icon 三类 PNG，base64 内嵌（单文件 HTML）；
  缺失时该区域显示「本输入快照未取得」并在 `<details>` 列出尝试路径（PNG 路径与
  objects_index.json），不借其他 cid 的图。
- 新增逐图绑定标注文案：`命名规则绑定：CharacterFactory.GetCharaTextureName* 方法证据
  （cid 计算纹理名），见 output/card_images/cid30236/binding_evidence.json；
  解包台账 output/full_unpack/ledger.jsonl`；30236 三图各追加 manifest 原文标注。
- 30236 页额外渲染 manifest 状态条（状态串＋头像已确认／全身未定位、局部已导出＋
  「不视为全身体已确认」声明），并保留 card.json `basic.card_art` 的
  NO_VERIFIED_BINDING 原状态作对照说明（立绘区独立于 card_page 主管线）。
- `run_checks` 新增立绘自检：data URI 必须在页面且 base64 非空、绑定标注文本必须在页面、
  缺失图必须显示「本输入快照未取得」与尝试路径、30236 页必须含 manifest 状态标注。
- 脚本 docstring 同步更新（不再写 NO_VERIFIED_BINDING 占位）。

### 每图来源与绑定依据（三页共 9 图）

| cid | 图 | 来源（解包产物，本轮 stat 核实） | 绑定标注 |
|---|---|---|---|
| 30236 | 主图整卡 | `output/full_unpack/objects/Card_OrgSize/cha_2d_card_30236/cha_2d_card_30236.png`（359769B） | 命名规则绑定（GetCharaTextureName* 方法证据＋台账）；另注 manifest CARD_VARIANT_CONTAINER_AND_VISUAL_MATCH |
| 30236 | Trimmed_Whole | `…/Trimmed_Whole/cha_2d_whole_30236/cha_2d_whole_30236.png`（300421B） | 同上；另注 CONFIRMED_CLIENT_ID_BINDING 且为边缘截断局部立绘、非完整全身 |
| 30236 | Card_Icon | `…/Card_Icon/cha_2d_icon_30236/cha_2d_icon_30236.png`（19672B） | 同上；另注 CONFIRMED_CLIENT_ID_BINDING |
| 07616 | 主图整卡 | `…/Card_OrgSize/cha_2d_card_07616/cha_2d_card_07616.png`（373592B） | 命名规则绑定（同上）＋台账 |
| 07616 | Trimmed_Whole | `…/Trimmed_Whole/cha_2d_whole_07616/cha_2d_whole_07616.png`（314410B） | 同上 |
| 07616 | Card_Icon | `…/Card_Icon/cha_2d_icon_07616/cha_2d_icon_07616.png`（22840B） | 同上 |
| 10001 | 主图整卡 | `…/Card_OrgSize/cha_2d_card_10001/cha_2d_card_10001.png`（415415B） | 命名规则绑定（同上）＋台账 |
| 10001 | Trimmed_Whole | `…/Trimmed_Whole/cha_2d_whole_10001/cha_2d_whole_10001.png`（250362B） | 同上 |
| 10001 | Card_Icon | `…/Card_Icon/cha_2d_icon_10001/cha_2d_icon_10001.png`（24084B） | 同上 |

（07616/10001 无各自 manifest；仅按通用方法证据＋台账标注，不写成已实机验证绑定。）

### 本轮自检（实际运行）

1. 渲染命令：`& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_dbstyle_sample.py`
   → 三页 [OK]：30236（979502B，自检 227 项）、7616（962693B，36 项）、10001（957500B，111 项），
   A/C 行数与 summary 仍逐页一致。
2. 独立自检脚本（本轮运行，PASS）：三页各含 3 个 data URI 且逐一与源 PNG 字节重编码后的
   base64 完全匹配；绑定标注文案每页恰好出现 3 次；30236 页含 manifest 状态串、
   「头像 CONFIRMED_CLIENT_ID_BINDING；全身未定位、局部立绘已导出」、
   CARD_VARIANT_CONTAINER_AND_VISUAL_MATCH、边缘截断说明；页面未出现其他 cid 的图引用。
3. 缺失回退单测：`load_art(88888888)` 三条目均无 data_uri、尝试路径正确
   （注：`load_art(99999)` 返回真实存在图——full_unpack 中确有 cha_2d_card_99999 资产，非 bug）。

### 第二轮边界

- 立绘绑定状态为「命名规则绑定（客户端方法证据）＋解包台账」，非截图比对级实机验证；
  页面文案如实如此标注。30236 整卡不宣称全身体已确认。
- 未做浏览器渲染视觉回归（静态 HTML＋文本级自检）。
- Card_LongVer3 长版图本轮未上页面（参考版式无对应区域）。

---

## 2026-10-20 第三轮改版：按玩家反馈重排首屏阅读层级（数值颜色=证据等级，审计全部入折叠）

### 反馈与改版方向（用户原话要点）

「太乱了不是给人看的；玩家首先关心①角色能力的文字描述（原文段落）、②每一段对应的
数值是多少；③确定和不确定直接用数值上的颜色表示；④为什么可信、条件、类型等另外
展开显示。」

### 首屏新阅读层级（`scripts/character_skills/card_page_dbstyle_sample.py` 本轮重写渲染层）

- 每条描述行＝**日文原文（17px，视觉主体）**＋紧随的**数值 chips**（按原文顺序排列）；
  chip 文案沿用既有换算结果（如「自身攻击×1.4（本项提高 40%）」「次数：5回」）。
- chip 颜色即证据等级：确认=绿实线；确认（类型外推）=绿**虚线框**＋「外推」小字；
  推断=橙；未知=灰（chip 只显示「未知」）；关联未证另加灰色「关联未知」小字。
  判定仍完全沿用 card.json 原标注（REVIEWED_RECORD／BY_TYPE_EXTRAPOLATED／
  TEMPLATE_PILOT_1017），渲染层不升级不降级。
- 删除首屏全部审计副行：行头徽章/stage/字段/片段行、逐答案证据徽章串、
  「类型｜单位｜card.json 原值｜换算」副行、行内「条件：」长文。
- 每行唯一「▶ 详情」`<details>`（默认收起）：逐答案（规则键/card.json 原值/单位类型/
  证据目录/适用范围/条件/来源指针等**全部键通用渲染**）＋行级审计（unknown_reasons
  全文/绑定条件/上下文多段披露/合并键/别名引用等），不删任何键。
- 技能头保持名称/费用/档位/等级；新增技能级「▶ 技能记录审计」折叠
  （original_text/record_evidence/forward_links 等）。
- 四联指标压缩为页面顶部一行小字；基础信息表徽章保留、证据长文入「▶ 基础信息证据
  细节」折叠；立绘主图＋条带保留、绑定标注与 manifest/card_art 状态入折叠。

### 产物

| 文件 | 本轮结果 |
|---|---|
| `output/character_skills/dbstyle_samples/30236.html` | 2179569B；58 行（46A/12C）、134 答案；折叠 58 |
| `output/character_skills/dbstyle_samples/7616.html` | 1048245B；8 行（4A/4C）、4 答案；含 BY_TYPE_EXTRAPOLATED 绿虚线 chip |
| `output/character_skills/dbstyle_samples/10001.html` | 1474413B；52 行（9A/43C）、16 答案（推断 3）；含 TEMPLATE_PILOT_1017 橙 chip |
| `output/character_skills/dbstyle_samples/DESIGN.md` | 新增：显示层设计说明（阅读层级/颜色语义/折叠清单/与审计用途关系） |

### 本轮自检（实际运行，双通道）

1. 渲染命令：`& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_dbstyle_sample.py`
   → 三页 [OK]，内置 `run_checks`（227/36/111 项）＋行数/折叠/审计核对通过：
   - 旧审计副行类名（ans-sub/row-meta/row-head）及「card.json 原值：」「｜换算：」
     内联格式已从页面消失；
   - 每行恰一个 row-detail 折叠；行ID 可见文本在折叠层；
   - 折叠层含全部规则键/raw_value/证据目录/evidence_scope/条件/换算；
     unknown_reasons 全文在页面；
   - A/C 行数与 summary 一致（46/12、4/4、9/43）；未知灰 chip 数 ≥ C 行数；
   - 立绘 data URI、绑定标注、30236 manifest 标注仍在页面。
2. 独立自检 `work/dbstyle_v3_check/check_v3.py`（本轮运行，**ALL PASS**）：
   - 分层剥离全部 `<details>` 后的首屏正文不含规则键/原值/换算/证据目录/来源指针/
     绑定条件/上下文全文；REVIEWED_RECORD、BY_TYPE_EXTRAPOLATED、TEMPLATE_PILOT_1017
     及「条件：」在整个首屏（含页脚）不出现；
   - 每行原文与数值 chip 位于该行折叠层之前（首屏在上）；
   - 所有 details 无默认 open；
   - 9 张立绘 data URI 与源 PNG 重编码 base64 逐一相等；指标行位于技能区之前。

### 第三轮边界

- 未做浏览器渲染视觉回归（静态 HTML＋DOM/文本级自检；折叠依赖标准 `<details>`，无 JS）。
- 30236 页因全行通用审计渲染增至约 2.1MB（立绘 base64 为主），单文件无外部依赖。
- 证据等级与数值均沿用 card.json 原值，展示层不改判。

---

## 2026-10-20 第四轮追加：右上角证据等级图例（玩家定稿版式＋图例）

### 需求（用户定稿）

玩家视角版式定稿后，要求在角落加**颜色含义图例（讲人话的定义）**：
固定/吸顶小卡（滚动跟随）或技能区开头显眼小块，不挡正文、窄屏不溢出；
四档定义按 card.json 实际口径写（可微调措辞不改口径）；图例自带一句
「颜色只表示证据等级，数值都可在 ▶详情 里查到出处」。

### 实现（仅 `scripts/character_skills/card_page_dbstyle_sample.py`）

- 采用**右上角固定吸顶小卡**方案：`position:fixed; top:8px; right:8px; width:296px;
  max-width:calc(100vw-16px)`，半透明深底＋投影，滚动跟随；DOM 位于四联指标行之后、
  顶部两栏之前，`<!-- legend:start/end -->` 标记包围，不在任何 `<details>` 内（首屏可见）。
- 窄屏（≤760px）媒体查询回退为文档流静态全宽块，不溢出视口。
- 四档图例 chip（复用页面 chip 样式：绿实/绿虚框/橙/灰）＋讲人话定义：
  - 确认：这个数值有逐条核过的证据链（代码规则或原文审核记录），不是猜的。
  - 确认·类型外推：证据来自同类型技能的规则，适用到这条上没有逐条再审，但规则本身已核。
  - 推断：按句式模板和数据字段推出来的值，方向大概率对，但没逐条审定，可能错配。
  - 未知：原文没写数值，目前也没有能用的证据；点开详情能看到缺什么。
  - 提示语：颜色只表示证据等级，数值都可在 ▶详情 里查到出处。
- `run_checks` 新增图例自检：图例块存在、位于第一个折叠层之前、四档定义与提示语
  各恰好一次、图例内四档 chip 类名齐全。

### 本轮自检（实际运行，双通道）

1. 渲染命令：`& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_dbstyle_sample.py`
   → 三页 [OK]：30236（2181097B，自检 228 项）、7616（1049773B，37 项）、
   10001（1475941B，112 项）；行数/答案/指标与上一版一致
   （46A/12C/58、4A/4C/8、9A/43C/52；答案 134/4/16，推断 0/0/3）。
2. 独立自检 `work/dbstyle_v4_legend/check_v4.py`（本轮运行，**ALL PASS**）：
   - 每页 legend 标记/`id="evidence-legend"` 恰好一次；四档定义与提示语整页各恰好一次；
   - 图例内四个 chip（>确认<、>确认·类型外推<、>推断<、>未知<）各恰好一次；
   - 图例块位于页面第一个 `<details>` 之前（首屏可见、不在折叠层内）；
   - **其余内容不变**：剔除图例块＋图例 CSS 行后，三页与上一版 HTML 逐字节一致
     （既有 CSS 行零改动、新增行全部为图例规则）；渲染前已备份上一版三页到
     `work/dbstyle_v4_legend/before/` 作比对基准。

### 第四轮边界

- 未做浏览器渲染视觉回归（静态 HTML＋文本级自检）；吸顶卡滚动遮挡行为仅静态核查，
  未做实机窄屏截图验证。
- DESIGN.md 已补「五、证据等级图例」节（原边界节顺延为六）。

---

## 2026-10-20 第五轮追加：主图显示比例修正（2:3 竖版，与正式渲染层同步）

### 需求与证据边界（本轮只读引用，未新采）

已核实证据 `output/card_images/cid30236/followup/REPORT.txt`：卡面纹理存储 512×512 方形，
但游戏 UI 显示为 2:3 竖版（CharaInfoCard._cardTexture → UITexture 109376/CardOrg，控件
640×960、aspectRatio≈0.6667、UV 覆盖整张纹理；APK prefab 最小序列化前缀解析，非实机
测量）；头像 42×42 与上半身 512×512 的使用场景是 1:1；半身 face 变体无其他界面比例依据、
保留 1:1。本轮另实测：full_unpack 全部 4313 张 Card_OrgSize PNG 逐一读 IHDR 均为 512×512。

### 渲染器改动（仅 `scripts/character_skills/card_page_dbstyle_sample.py`）

- 主图 CSS：`max-width:100%;max-height:420px;width:auto` →
  `width:min(340px,100%);aspect-ratio:2/3;height:auto;object-fit:fill`——512×512 源图
  非均匀拉伸进 2:3 盒子，等价于游戏 UI 把整张方形纹理铺进 640×960 控件的行为；
  `.art-thumb`（whole/icon）CSS 不动，维持 1:1。
- 逐图「▶ 绑定标注」追加显示比例标注（主图 2:3；whole/icon 各带 1:1 使用场景依据）；
  立绘区审计折叠新增页级「显示比例依据」段。
- `run_checks` 新增：2:3 缩放 CSS 恰 1 次、逐图/页级标注文本齐全（缺图页不要求逐图标注）。

### 本轮自检（实际运行）

1. 渲染命令：`& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_dbstyle_sample.py`
   → 三页 [OK]：30236（2182042B，自检 228 项）、7616（1050718B，37 项）、
   10001（1476886B，112 项）；A/C 行数与 summary 不变（46A/12C/58、4A/4C/8、9A/43C/52）。
2. 三页逐一 grep 核实：`aspect-ratio:2/3`、主图「显示 2:3 竖版（游戏 UI 控件 640×960」
   标注、页级「显示比例依据（output/card_images/cid30236/followup/REPORT.txt」段、
   whole/icon 1:1 标注各恰 1 次。
3. 正式 2236 页由 `card_page_render_v2.py` 同口径修正并四 cohort 全量重建（复核
   2236/2236 receipt SUCCESS、card.json 逐字节不变 2236/2236）；详见
   `output/character_skills/pages/README.md` §16.6 与
   `docs/tasks/20261020-character-skills-layout-migration.md` 追加轮。

### 第五轮边界

- 与第四轮相同：未做浏览器渲染视觉回归；显示比例为静态 CSS（aspect-ratio＋object-fit:fill）。
- 源 PNG、base64 数据 URI、证据等级与数值均不变——本轮只改显示盒比例与标注文本。
