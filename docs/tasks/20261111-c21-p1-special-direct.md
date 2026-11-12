# C21-P1：special直接多段／大伤害

- 状态：**正式交付与独立终审完成（2026-11-12）；C21-R01原第三方定向复验通过，F01／F02均CLOSED，阻断0；C21在明确范围限制下收口**。候选机器检查28/28；正式净增766项／517卡，CACHE 259／APK 507，含Y.G. 10项；正式独立终审23/23、阻断0，成果见`output/character_skills/cycle_reports/C21/`。
- 写域：`card_page_inference_c21_p1_special_direct.py`、共享冻结配置、`output/character_skills/c21_p1_special_direct_20261111/`、本卡。
- scope：`C21_P1_SPECIAL_DIRECT_20261111`；缺省、错误或空scope硬拒绝。

## 逐行门

1. 当前row为special_move、patternN直接来源；同层charainfo唯一，实际patternN等于skill.record_id，row.source指向真实bosspattern下标及`/sinfo`。
2. `skill.original_text`、`row.context_text`与pattern.sinfo一致，当前片段在父文恰出现一次；目标effect由真实`analyze_row`确认恰一个未解伤害效果。
3. `N回ダメージ`只选type105／110且`skillparam6==N`恰一条；大／中ダメージ只选type3／22／55／74恰一条。类型和槽位存在既有确认规则及G1-B1消费口。
4. 原值从选中bossskill字段重读，有限正数，保留raw与float32。已有同规则答案不新增；旧答案前缀与非目标行不变。
5. 完整父集合与当前／选中父逐项保留，合并或排除分支不能因同型而任选。保护卡和同型多记录无法消歧行零新增。

候选目录须包含candidates、exclusions、check_result、run_record、README和真实Inputs/analyze_row检查脚本。独审有阻断时不接线。

## 当前实施回执（2026-11-11）

- 冻结：`scripts/character_skills/c21_freeze_direct_damage.py` 从当前正式来源重导，写出
  `scripts/character_skills/c21_direct_damage_targets.json`（sha256
  `425450f99d6792d9873b5a73cb08b34e633c6f58366fccb0b2e481b90e008459`；只含
  cid／row_id／effect_id／layer／reference_field／model，不存 raw）。重跑逐字节一致。
- 实测数量：766 行／517 卡／CACHE 259／APK 507／Y.G. 10；multihit 327、bigmid 439；
  766 效果 766 答案。保护卡 30102／20234／30236／30239 零触碰；20234 的
  `pattern1-lvorder1-f0` 在冻结门重放中本可通过（`bossskill|22|/skillparam1`），按保护卡不纳入。
- 模块：`scripts/character_skills/card_page_inference_c21_p1_special_direct.py`
  （sha256 `c40d759852895180c0744b590a3e509c88f88221fd699f9f0d63caae9c075685`）；
  复用 C20 RawView／resolve_row／select_carrier／build_answer／apply_to_groups；导出
  evaluate／apply_to_groups／build_candidates／write_outputs，scope 缺省、错误、空值硬拒绝。
- 产物：`output/character_skills/c21_p1_special_direct_20261111/`（candidates 32,333,790 B
  sha256 `653f6bb6…`；exclusions 2,310 项 sha256 `d21ccb4d…`；run_record；README；
  check_candidate.py；check_result）。
- 命令与退出码：
  - `./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/c21_freeze_direct_damage.py --root . --write --json` → 0
  - `./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/card_page_inference_c21_p1_special_direct.py --root . --write --json` → 0
  - `./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/check_c21_candidate.py --root . --write` → 0（28/28，约 63 s）
- 检查：778+ 附带证据全部通过——900 条 raw／指针／记录哈希／float32 独立重导、完整父集合、
  规则重算、首次新增 766+134、新增未消费 0、split 不变、二次新增 0／跳过 900、
  scope 12/12 拒绝、保护卡与反例零新增、来源篡改／零 raw／冲突原子、共享文件与 525 张 page
  前后哈希不变。
- 阻断（不属于 C21 写入域，正式全库生成前必须由主持处理）：既有共享代码在当前布局下
  `build_card` 对部分目标卡直接抛错——12+ 个既有推断模块保存逻辑路径
  `output/cache_full_20261015_v3`；`card_page_inference_type8.py:98` 与
  `card_page_inference_cond.py:204` 以 `Path(__file__).resolve().parents[1]` 解析
  `scripts/` 证据路径（差一级）。检查器只在内存把过期常量指向同一物理快照（三文件哈希与
  decode_report 一致），登记 33 处改动；共享文件未改。正式入口需修复这些共享模块或采用同样
  的显式适配。
- 仍需独审注意：11 条 `TEXT_MISMATCH`（页面把 `\n` cleaning 成换行）、24 条载体门失败、
  18 条未解伤害效果非单条、19 条已答／非未解行均逐行登记，不得按值任取；关联全为推断，
  `numeric=确认` 只指原值＋既有规则体，未实机。
