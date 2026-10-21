# 任务卡：角色技能页版式迁移（20261020）——玩家视角版式推广为正式主渲染层＋B4-R01 顺带修复

- 任务 ID：`20261020-character-skills-layout-migration`
- 状态：**已完成（四 cohort 全量重建＋复核＋抽样自检通过）**
- 负责人／对话标识：版式迁移实施员（GLM 5.3 Flash 260828，动态工作流子代理）
- 日期：2026-10-20

## 目标

把已定稿的玩家视角版式（`output/character_skills/dbstyle_samples/DESIGN.md` 与三张示例
`{30236,7616,10001}.html`，渲染器 `card_page_dbstyle_sample.py`；用户已确认定稿
「暂时按这个来搞」）推广为正式 2236 页的主渲染层；顺带修复批 4 审查 B4-R01。
**card.json 不变**（唯一例外：B4-R01 的 33 行注记），迁移只换 HTML 呈现。

## 允许写入（本轮实际遵守）

- 脚本：`card_page_render_v2.py`（新建）、`card_page_batch.py`（渲染层切换＋permission_boundary）、
  `card_page_inference_cond.py`（B4-R01 修复）
- 输出：`output/character_skills/pages/`（含 `_batch/`、`art/`、README.md §16）
- `work/character_skills_layout_migration/`（旧 card.json 快照/对账/复核/抽样自检脚本）
- 本任务卡
- 未改：profiles/原始输入、旧审查报告、共享进度文件、旧 `card_page_render.py`（保留给
  11 卡试点入口）、type1017/批 3 模块；未 git 暂存/提交

## 实施内容

### 1. 新渲染层 `card_page_render_v2.py`（受控接入）

- 版式要素与定稿示例一致：
  - 首屏阅读层级：卡名行 → 四联指标一行小字 → 立绘区 → 基础信息表 → 13 组技能区；
  - 每描述行＝日文原文（17px 主体）＋数值 chips（确认=绿实、确认（类型外推）=绿虚框＋
    「外推」、推断=橙、未知=灰；「关联未知」小字；混合 scope 绿实「确认（部分类型外推）」）；
  - 右上角吸顶图例（四档讲人话定义＋提示语；`<!-- legend:start/end -->` 包围、位于
    第一个折叠层之前；≤760px 媒体查询回退文档流）；
  - 全部审计内容入折叠层（默认收起、信息一条不删）：每行「▶ 详情」通用渲染行/答案全部键
    （规则键/原值/证据目录/适用范围/来源指针/条件/unknown_reasons 全文/绑定条件/多段披露）；
    技能级「▶ 技能记录审计」；基础信息证据细节（逐字段全键 JSON）；立绘绑定标注/立绘区审计；
    intro 说明（推断层口径/日文短语对照/指标方法）折叠不删；
  - 13 组导航保留（无配置组「本输入快照未关联；不代表游戏没有此组」）。
- 兼容钩子（`card_page.validate` 依赖，全部保留）：data-row-id/data-row-class/data-evidence
  属性序、独立 `<p class="jp">`、13 组 data-group、内嵌 card-data JSON payload。
- 接入：`card_page_batch.py` 改 `from card_page_render_v2 import page`；旧渲染器仅供
  `card_page.py`（11 卡试点）与历史对照。

### 2. 立绘接入（pages/art/，相对路径不 base64）

- `card_page_render_v2.py --copy-art`：从 `output/full_unpack/objects/{Card_OrgSize,
  Trimmed_Whole,Card_Icon}/cha_2d_*_<cid>/` 复制到 `pages/art/<cid>/{card,whole,icon}.png`；
  页面 `../art/<cid>/<kind>.png` 相对路径引用。
- 规模（分母 2236 cid）：card 2205（缺 31）、whole 2235（缺 1）、icon 2232（缺 4）；
  三类齐全 2205，至少一类 2235，**仅 59103 三类皆缺**；art 目录 6672 PNG／1,475,926,606
  字节（≈1.476 GB）。
- 绑定依据标注：「命名规则绑定：CharacterFactory.GetCharaTextureName* 方法证据（cid 计算
  纹理名），见 output/card_images/cid30236/binding_evidence.json；解包台账
  output/full_unpack/ledger.jsonl」——逐图折叠＋全部页立绘区审计页级说明；30236 另按
  `output/card_images/cid30236/manifest.json` 如实标注（头像 CONFIRMED、全身未定位、
  局部已导出）。缺图 cid 显示「本输入快照未取得」＋尝试路径，不借图。

### 3. B4-R01 修复（同一轮生成器变化内）

- `card_page_inference_cond.py` `_promote`：「父记录句外参数未分配」排除集合改为仅基础句
  值行字段（追加条件增幅值行前先记 `base_field_paths`）。
- 修复 33/37 晋级行的注记漏列（type36 /param4/5、type80 /param7/8、type67 /param6/7 与
  父记录同名槽相撞）及 4227（CACHE）整条注记缺失；7613 同法核对。详见 pages/README.md §16.3。

## 重建与复核结果（本轮实际执行）

- 命令（仓库根，四条依次）：
  `& .\.venv\Scripts\python.exe -B scripts/character_skills/card_page_batch.py --input-root .
  --manifest output/character_skills/r2_preparation/cohorts/manifest.json --cohort <ge60|40to59|20to39|remaining>
  --output output/character_skills/pages --execute --resume`
- 四 cohort 0 失败：ge60 34/34、40to59 290/290、20to39 436/436、remaining 1476/1476。
  最终 run_id：ge60 `20261020T091743775283Z-f0389862`、40to59 `20261020T091753495799Z-4c126885`、
  20to39 `20261020T091844603395Z-c6664b20`、remaining `20261020T091931839631Z-8fe9d50a`。
  终版签名 `46de0c7cd11446ff24024c93f0ac49bb3e1c43041a99ba263bdd40aca75229b6`
  （dependency_signature `4029ad13…` 不变，29/29 数据依赖逐一重算未变）。
- 复核（`work/character_skills_layout_migration/recheck.py`）：
  2236/2236 receipt SUCCESS；4472 个 receipt 声明产物哈希逐一核对 0 不一致；0 stale；
  campaign 四 cohort MATCHING_SIGNATURE_SNAPSHOT；审计队列 11469 行/790 卡不变
  （全部 NOT_REVIEWED）。
- **四联指标 old→new 逐项一致**（分母 N_all 41,665）：A 14,539；整行确认 266
  （记录级 18＋类型外推 248）；原文A 13,859；C 27,126；整行推断 414；B 0；
  partial_A 14,172；推断层 pilot 337/4、批3 40/141、批4 37/135——全部不变。
- **card.json 等价性**：old→new 逐字节 SHA-256（快照 `old_card_json/` 2236 份）：
  **2203/2236 逐字节一致**；33 个变化文件恰为 B4-R01 affected 33 行，逐行核对变化全部
  落在该行 unknown_reasons 的「父记录句外参数未分配」注记（其余行逐键零变化、非行结构
  零变化、缺失参数原值按 issues.jsonl missing_parent_params 全部出现在注记：10205
  /param4=1.0、/param5=0.0；4227 注记由缺失变为 /param4=1）。无范围外差异。
- HTML 体积：index.html 合计 1.319 GB（迁移前 1.276 GB）；card.json 合计 580,790,057 字节。
- 抽样自检（`sample_selfcheck.py`，17 卡＝定稿示例 3＋批4 晋级 6＋缺图卡 4＋普通/边界 4，
  ≥10 卡要求）全部通过：图例存在且首屏、四档定义/提示语各恰一次、每行原文与 chips 在
  折叠层之前、折叠层含规则键/原值/证据目录/unknown_reasons 全文、art 引用与盘上文件一致
  （复制件与源 PNG 哈希一致）、缺图回退正确、13 组导航与空组限定完整、`card_page.validate`
  结构一致。

## 边界与保留

- 未做浏览器渲染视觉回归（静态 HTML＋DOM/文本级自检；折叠依赖标准 `<details>`，无 JS）；
  窄屏回退仅媒体查询静态核查，未做实机截图验证。
- `dbstyle_samples/` 三张示例保留 base64 版本；`card_page_render.py` 与 11 卡试点入口不动。
- `schema_version` 仍为 `card-page-pilot-1`；数据语义一行不动。
- 审计队列 NOT_REVIEWED 状态未变：本版式迁移不改变任何行的审查语义。

## 下一步（供主持/审查方）

1. 按需对最终 2236 页做一次独立版式验收（浏览器视觉回归本轮未做）。
2. B4-R01 修复后可请审查方在 issues.jsonl 将 B4-R01 置为 fixed（本实施不改旧审查报告）。
3. 遗留：README §15 下一步的 P-B 86 行原生核实、type26 子集 272 行前置审计（未动）。

---

## 追加轮（2026-10-20）：主图显示比例修正（2:3 竖版）

- 需求来源：已核实证据 `output/card_images/cid30236/followup/REPORT.txt`（只读引用）——
  卡面纹理存储 512×512 方形，游戏 UI 控件 640×960＝2:3 竖版（APK prefab 最小序列化前缀
  解析，非实机测量）；whole/icon 维持 1:1；半身 face 变体保留 1:1。
- 改动：`card_page_render_v2.py` 主图 CSS 改 `width:min(340px,100%);aspect-ratio:2/3;
  height:auto;object-fit:fill`（非均匀缩放＝游戏 UI 行为；源 PNG 不改）；逐图绑定标注与
  立绘区审计追加显示比例依据文本；`run_checks` 内置显示比例自检。`card_page_dbstyle_sample.py`
  同步并重渲染三张示例卡。
- 重建：四 cohort 0 失败（ge60 `20261020T105237995373Z-792dbc80`、40to59
  `20261020T105300269503Z-1d7adde0`、20to39 `20261020T105407774703Z-423c2551`、remaining
  `20261020T105510177428Z-ef67b344`）；新签名 `66de3593e75dae03…4858ff`
  （dependency_signature `4029ad13…` 不变，29/29 依赖重算未变）。
- 复核（`work/character_skills_display_ratio_20261020/recheck.py`）：2236/2236 receipt
  SUCCESS、4472 哈希 0 不一致、29/29 依赖、0 stale；**card.json 逐字节不变 2236/2236**
  （重建前全量 SHA-256 快照对比，纯显示层修正）；四联指标、coverage 全键、campaign 与
  各 cohort 审计队列（11469 行）逐字节不变；全量 2236 页落盘核查 2:3 CSS/页级依据段
  2236/2236、主图逐图标注 2205/2205、whole/icon 1:1 标注 2235/2232（与有图页数恰等）。
- 抽样自检：`work/character_skills_display_ratio_20261020/sample_selfcheck.py` 17 卡全部通过。
- 详见 `output/character_skills/pages/README.md` §16.6。未做浏览器截图级视觉回归。
