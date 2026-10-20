# 角色技能页终版 polish 修复（2026-10-20）

- 负责人：终版polish修复员（GLM 5.3 Flash 260828，动态工作流子任务）
- 状态：已完成（2026-10-20）
- 上游：`output/character_skills/review/host_final_20261020/RESULTS.md` 终版债务清单；`remaining_20261020_deepseek/RECHECK.md`（RM-05）；`20to39_20261020_deepseek/RECHECK.md`（N-01..N-07）

## 目标

清理四轮独立审查遗留的 Low/Note 债务：RM-05、H-01 字段 pill、M-01 措辞、L-13 范围 literal、L-05 中日混排图例、L-08「さらにNつ減る」、L-04 多值重复标签（保守口径）。不改 profiles/原始输入/旧审查报告/共享进度文件；不启用候选晋级/推断层；不做 native。

## 允许写入

- 脚本：`scripts/character_skills/card_page_data.py`、`card_page_render.py`
- 产物：`output/character_skills/pages/`（仅经生成器重建，含 `_batch/`）＋ `pages/README.md`
- 对账/干跑：`work/polish_20261020/`
- 本任务卡

## 改动摘要

| 项 | 处理 | 实测 |
|---|---|---|
| RM-05 | 段首「N%」+叙述文本 → `叙述数字`（与8022同法） | 1 行（5037） |
| H-01/N-05 | 「字段／描述关联」pill 同步 scope（确认（类型外推）） | 17/17 行；30236 18 行不变 |
| M-01/N-01 | 注记改「「回」是「回復」的首字（不是次数单位）」 | 24 行，值/标签不变 |
| L-13/N-02 | 范围 literal/raw_span 取完整 token（「1回～6回」） | 10 行；raw_value 仍为「1～6」 |
| L-05 | 页面统一图例＋常见短语对照（不翻译，逐字引用） | 2236/2236 页 |
| L-08 | (a) 同分句「(必要な)マナ(の数|数)が/を」→`所需玛那减少`（G-05 窗口扩展）9 行；(b) 片段内无对象 → 注记「减少对象见同技能前文（片段内无逐字依据）」18 行 | 27 项/26 行 |
| L-04 | 仅同分句紧邻「名詞＋を/が＋数值」或「敵/味方/自身/マナ＋数值」形态时逐值括注（l04_object）；无据行保留 | 标注 121 项/73 行；保留 140 行（l04_retained.jsonl） |

## 重建与复核（本轮实际运行）

- 命令：`./.venv/Scripts/python.exe -B scripts/character_skills/card_page_batch.py --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json --cohort {ge60|40to59|20to39|remaining} --output output/character_skills/pages --execute --resume`
- 新 run：ge60 `20261020T025207124738Z-4288fdd0`、40to59 `20261020T025218701134Z-16d40ded`、20to39 `20261020T025300741802Z-5cd02dc6`、remaining `20261020T025340009283Z-777b2929`
- 新 signature `66054242a0649c2d9442fcab6a5ace735b2e6aad2bb8aec3e04f5dbcaee92303`（source_signature `7e122c80…` 随代码更新；dependency_signature `4029ad13…` 不变）
- 复核（`work/polish_20261020/verify.py`，只读）：2236/2236 receipt SUCCESS；4472 产物哈希一致；29/29 数据依赖未变；0 stale；campaign 2236/2236、四 cohort MATCHING_SIGNATURE_SNAPSHOT；行集合增删 0；raw_value 多重集变化 0；答案数变化 0；变化 134 行（L-04 73＋L-08 注记 18＋G-05 改标 8＋M-01 24＋L-13 10＋RM-05 1）
- 四联 old→new 全部不变：ge60 1005/0/1005/1206（2211）、40to59 6165/18/6147/8056（14221）、20to39 3867/17/3850/8165（12032）、remaining 3088/231/2857/10113（13201）、campaign 14125/266/13859/27540（41665）

## 保留未修

- L-04 保留 140 行：对象在数值之后／跨数值残留尾巴／时间副词／承接词／已带 qualifier 或既有括注，以及 % 属性重复行（属性名词已在标签）与条件阈值重复行——无逐字就近依据，不按位置猜测。
- L-07（8 行 SA 标签计入分母）：维持 denominator_notes 登记口径（R-12/RM-04），本轮未列。
- L-09（11 行同值规则注记）：上轮已闭合，本轮未动。
- 10030 f1/denju 自伤「N%のダメージ」未写基数 2 行：原文未写最大HP，不猜基数。
- 6 个既有空 record_evidence 占位、7932 个无 records 索引 CACHE 记录未重做字节切片哈希：既有范围限制不变。

## 最近更新

- 2026-10-20：四项修复＋三项保守处理完成，四 cohort 重建并全量复核通过；README §12 已记录。

## L-04 微修（2026-10-20 终版复验唯一未闭合项）

- 依据：`output/character_skills/review/remaining_20261020_deepseek/FINAL_RECHECK.md` L-04 节——`9240-ability-ability-skillid_2_-lvorder1-f3` 的 1人 括注过宽且张冠李戴（「接触した敵に小ダメージを与える宝石を自身から最も遠い味方」，把前一分句宝石对象带入被计数的「味方」）。
- 规则修复（`scripts/character_skills/card_page_data.py` `l04_object`）：对象名词收尾的尾巴（不以を/が或助词结尾）若含「を」，截到最后一个「を」之后，只保留紧邻数值的最小名词短语（本行 →「自身から最も遠い味方」）；「名詞＋を/が＋数值」直接受助词支配的形态不变。
- 干跑门（`work/polish_20261020/dry_run_l04fix.py`，73 行 47 cid 全量重建不落盘）：121 项标注全部保留、行数 73 不变；对旧规则产物逐项核验「名词收尾尾巴跨を链」真过宽仅 9240 一项；20207「盾を破壊する雷球」/20915「味方全体のHPが上限を超えて回復する式神」属 tail 以「を」结尾的被数名词直接受支配形态（を 在被数名词自身定语内），非同类过宽。修复后差异行恰为 9240 f3 一行（曾出现一次中间版把「騎士マナも」等 3 项误丢，已修复规则分支，干跑 0 丢失）。
- 重建：同命令四 cohort `--execute --resume`；新 run：ge60 `20261020T031548019063Z-24bcc896`、40to59 `20261020T031559839274Z-6670a306`、20to39 `20261020T031641831998Z-fe4628d3`、remaining `20261020T031720252959Z-ba6df5c1`；新 signature `a09f0239edbd785e2ab3377e05f284a34fa9512445244ac5a7b964921cca228c`（source_signature `3049d473…` 随代码更新；dependency_signature `4029ad13…` 不变）。
- 复核（`work/polish_20261020/verify_l04fix.py`，基线=微修前快照 `work/polish_20261020/old_pages_l04fix/` 2236 卡）：2236/2236 receipt SUCCESS；4472 产物哈希一致（0 mismatch）；29/29 数据依赖未变；0 stale；campaign 2236/2236、四 cohort MATCHING_SIGNATURE_SNAPSHOT；行集合增删 0；raw_value 多重集变化 0；答案数变化 0；行不变式破坏 0；old→new 变化仅 1 行——`9240-ability-ability-skillid_2_-lvorder1-f3`（kinds: answer_text+L04）；L-04 口径不变：标注 121 项/73 行、保留 140 行；9240 同行 4つ 仍未标注（部分标注保守边界，审查已认可，维持）。
