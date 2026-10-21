# 20261020 角色技能页 remaining cohort 实施任务卡

- 负责人：GLM 5.3 Flash 260828（remaining实施统计员，工作流调度）
- 状态：已完成（生成与机器核查）；DeepSeek 审查 RM-01…RM-04 修复轮次已完成（见文末）【2026-10-21 复核注：seed30 队列 218 行逐行核读已完成（历史台账，见 review/remaining_20261020_deepseek/）；其余 1,446 卡为全量机器核查＋风险抽样，非全量人工审读】
- 最近更新：2026-10-20 09:25（本地 UTC+8，R3 修复轮次后）

## 目标

按已审方法对 remaining cohort（1476 张，冻结名册 `output/character_skills/r2_preparation/cohorts/manifest.json` 的 `cohorts.remaining`）执行正式生成 `--execute --resume`，完成 receipt/产物哈希/依赖哈希机器核查，并收集四联指标与审查队列。工作流已先行跑出 run `20261020T003504325268Z-b6c77e70`（exitCode=0），本任务做独立复核，未再续跑（无失败卡，0 次重试触发）。

## 允许写入

- `output/character_skills/pages/`（含 `_batch/remaining/`，由 batch 生成器写入）
- `work/` 下本任务目录（本轮未产生）
- 本任务卡

## 运行命令

```
./.venv/Scripts/python.exe -B scripts/character_skills/card_page_batch.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --cohort remaining --output output/character_skills/pages --execute --resume
```

run：`output/character_skills/pages/_batch/remaining/runs/20261020T003504325268Z-b6c77e70/`，耗时 47.3s，attempts 1476 全 GENERATED，reused=0，failed=0。

## 结果（四联指标，remaining cohort，分母 N_all=13201）

| 指标 | 数量/分母 | 率 |
|---|---|---|
| A（数值/公式行率，**不是已解释率**） | 3088/13201 | 23.39% |
| 整行确认（全部 BY_TYPE_EXTRAPOLATED 类型外推，记录级 0） | 231/13201 | 1.75% |
| 原文A | 2857/13201 | 21.64% |
| C 仅未知 | 10113/13201 | 76.61% |

- N_all/E/N_num = 13201/0/13201；B=0（技能候选晋级层未启用，0 不代表全库无 hint）；部分A=2749；整行推断 0。
- A 中整行未知 2857/3088（92.52%）；A 整行证据：确认 231、推断 0、未知 2857。
- 未知原因分类（逐行扫描 1476 card.json 实测）：C 10113 行全部带「此描述尚无可适用的已确认数值或新增机制证据」，其中 10086 行另有「原文未提供该效果数值…」、27 行为 N直線 范围几何数字注记（L-10）、2539 行另有「旧关键词候选未作为答案；不能排除对象或效果错配」、5 行 str0 目标规则来源层复用注记；A 中整行未知 2857 行原因均为「原文数字仅确认原文，不猜参数对应」。
- 29/2020/5023 复核（R1 样本口径 29→2、2020→1、5023→1，合计 4；本 cohort 整行确认合计 2，差异全部来自 R-01 整行口径）：29→1（special_move f0「直線範囲上にいる全ての敵に小ダメージ」确认；ability 行「マナを１つ持った…」两答案一确认一未知，整行按 R-01 维持未知）；2020→0（special_move f0 两答案一确认一未知，整行未知）；5023→1（「味方全体のＨＰを中回復」确认）。来源指针逐行核读：APK `_mdCharacter.json#/charainfo/27`、`/charainfo/293`、`/charainfo/583`，均带 raw_record_sha256。
- campaign 层（同 run campaign_report.json）：2236/2236（760+1476）completed=expected，campaign_complete=true；status 注明是生成快照、非人审完成。campaign N_all=41665，A 14125（33.90%）、整行确认 266（记录级 18＋类型外推 248）、原文A 13859、C 27540。

## 机器核查（本轮实际执行）

- 1476/1476 receipt SUCCESS，signature=a466037d…，1476×2 产物（card.json/index.html）SHA-256 与 receipt 逐一一致，0 不匹配。
- 29/29 数据依赖 SHA-256 重算未变，dependency_signature=4029ad13… 与 run/receipt 一致。
- stale_or_invalid_cids=[]；ge60 34/34、40to59 290/290、20to39 436/436 receipts 均当前签名 SUCCESS（campaign 快照 4 cohort 均 MATCHING_SIGNATURE_SNAPSHOT）。
- 行集合重扫一致：13201 行 = A 3088 + C 10113；partial_A 2749；整行确认 231 与报告一致。

## 审查队列（NOT_REVIEWED，≠已验收）

- cohort 队列：`_batch/remaining/runs/20261020T003504325268Z-b6c77e70/audit_queue.json`，218 行/30 卡（仅 seed30），每卡 1–12 行，全部 NOT_REVIEWED。
- campaign 队列：同 run `campaign_audit_queue.json`，11469 行/790 卡（760 复杂＋seed30），每卡 1–31 行（中位 15），全部 NOT_REVIEWED。
- seed30（manifest.random_remaining_30，seed=20261019）每卡队列行数（≥10 或不足全列，实测 0 违例，且每有实际行的技能 ≥1 行入队）：9004:10、6246:11、2016:1、4203:10、8098:11、8258:11、6011:5、5203:5、59016:8、58:4、7027:9、2068:11、12:2、8270:5、6014:2、8035:9、11037:4、5227:12、8294:10、6215:9、1021:4、1024:2、7515:7、5052:8、4304:11、8058:8、1027:2、3033:6、7581:10、6328:11。
- 按验收规格：remaining 仅 seed30 的 30 卡需逐行人工核读（218 行欠账）；其余 1446 卡为全量结构/来源机器核查（本轮已做，receipt＋双产物哈希＋签名＋依赖哈希＋行集合重扫）。队列 NOT_REVIEWED 不等于已验收；独立审查须在版本化审查目录逐行记录。

## 输出体积与墙钟

- remaining 1476 卡目录（card.json＋index.html＋receipt.json×1476）：4428 文件，564.89 MiB；run 报告/事务目录 19.4 MiB（1495 文件）；card_latest 0.29 MiB。
- 墙钟：run 生成于 2026-10-20T00:35:04Z（≈本地 08:35）；本任务复核 08:36–08:40 本地（UTC+8）。

## 失败

- 无（failed=0，unresolved_latest_failures=[]，未触发续跑）。

## 下一步

- 主持调度独立审查：先 seed30 30 卡 218 行逐行核读（版本化审查目录），再做全 campaign 790 卡 11469 行对账；NOT_REVIEWED 状态在审查推进前保持。
- 整行确认 231 行全部为类型外推（BY_TYPE_EXTRAPOLATED），无逐记录人工审定；人审时应按页面「确认（类型外推）」标注复核。

## R3 修复轮次（2026-10-20，DeepSeek remaining 审查 REQUEST_CHANGES 后）

- 审查输入：`output/character_skills/review/remaining_20261020_deepseek/`（REPORT.md、issues.jsonl）。只改生成器 `scripts/character_skills/card_page_data.py`，未手改任何 HTML/card.json；未启用候选晋级/推断层；依赖签名 4029ad13… 不变（29/29 数据依赖 SHA-256 重算未变）。
- 修复内容（均带原文依据，规则见 pages/README.md §2.3/§11）：
  - RM-01（Medium，已修）：HP 条件百分比改标 `HP条件阈值`——「(残り)HPが N% の時/の場合/ならば/だと」＋同句承前「N%の場合」。实测 35 行全部在 remaining（审查点名 21＋同批扫描同型 14：49/54/69/5019/5041/5042/5062×3/7513/10009/11021/11033/58005）；前三 cohort 同型 0 行（全量语料扫描）。
  - RM-02（Low，已修）：M-04 扩展——省略领属「最大HP N%のダメージ」→`对敌伤害（基数：最大HP）`、「(自身/自分)も最大HP N%（の）ダメージを受ける」自伤→`自身受到伤害（基数：自身最大HP）`、炎属性变体同法。实测 53 行（remaining 40＋20to39 13：326×3、20435×3、6252×2、8228×5）；既有 M-04 行标签逐字不变。
  - RM-03（Low，已修）：「N秒先/秒後」改 `叙述数字`（display 带「（叙述性时间，非效果时长）」），实测 1 行（8022，全库唯一）。
  - RM-04（Low，保留口径＋登记＋补提取）：6215/6327 SA 内部标签行按 L-07 保留口径计入 N_all 并登记 `sources.denominator_notes`；6215「1000ダメージ」补提 `固定伤害量：1000`（special_move 正文佐证），全库「Nダメージ」仅此 1 行。
- 重建：四 cohort 依次 `--execute --resume`（ge60 34、40to59 290、20to39 436、remaining 1476），全部 completed=expected、failed=0、reused=0。新签名 `c1c3f739eb836805…`（四 cohort 一致；source_signature 因生成器代码变化更新）。
- 复核（本轮实际执行，脚本 `work/remaining_fix_r3/verify.py`）：2236/2236 receipt SUCCESS 且签名一致；4472 产物哈希逐一一致；29/29 依赖存在且 SHA-256 一致、data_paths 集合与声明一致；0 stale；campaign 快照 4 cohort MATCHING_SIGNATURE_SNAPSHOT（2236/2236）。页面抽验：7581 值行已为「HP条件阈值：100%」（无「效果量百分比：100%」）；8022 为「叙述数字：30秒（叙述性时间，非效果时长）」。
- old→new 对账（`work/remaining_fix_r3/row_changes.jsonl`，旧产物快照 old_pages/）：行集合增删 0；标签修改 90 行（RM01 35、RM02 53、RM03 1、RM04 提取 1），0 行意外变化；raw_value 多重集比对无一变化；japanese/row_class/evidence 逐行不变。唯一附注：5041 一行随角色变化移除「自身/」前缀（条件阈值不参与效果对象标注，语义更准确）。
- 四联指标 old→new 全部不变：ge60 A 1005/确认 0/原文A 1005/C 1206（N_all 2211）；40to59 6165/18/6147/8056（14221）；20to39 3867/17/3850/8165（12032）；remaining 3088/231/2857/10113（13201）；campaign N_all 41665、A 14125、C 27540、确认 266（记录级 18＋类型外推 248）。
- 保留未修项：L-04 多值重复标签（60 行，跨 cohort 债务）、L-05 中日混排条件短语（7 行，逐字依据）、L-08「さらにNつ減る」（9 行，片段内无マナ逐字依据）、L-07 同类 SA 内部标签（本轮 2 行已登记分母说明）——均按审查报告口径保留，待后续 polish 轮集中处理。
