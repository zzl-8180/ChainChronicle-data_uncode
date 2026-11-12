# C21-P2：denju直接与限定镜像伤害

- 状态：**正式交付与独立终审完成（2026-11-12）；C21-R01原第三方定向复验通过，F01／F02均CLOSED，阻断0；C21在明确范围限制下收口**。候选机器检查28/28；正式净增134项／107卡，全部CACHE，133项直接denju＋CID30304一项首句条件镜像；正式独立终审23/23、阻断0，成果见`output/character_skills/cycle_reports/C21/`。
- 写域：`card_page_inference_c21_p2_denju_direct.py`、共享冻结配置、`output/character_skills/c21_p2_denju_direct_20261111/`、本卡。
- scope：`C21_P2_DENJU_DIRECT_20261111`；缺省、错误或空scope硬拒绝。

## 直接denju门

1. 当前row为denju，source指向真实denju下标及`/stext`；denju_id与cid一致，patternid0唯一指向bosspattern。
2. denju.stext与pattern.sinfo逐字一致，目标句在全文恰出现一次；pattern子槽连续且record唯一。
3. 多段次数与`skillparam6`一致，大／中伤害只取单发型；原值有限正数，既有规则及G1-B1消费口唯一。
4. 同句其它效果、屏障、回复、增益和异常不借值；已有同规则答案不新增。

## CID30304条件镜像门

- denju首段大伤害与pattern首句一致，patternid0=43030403→bossskill43030400，type22／skillparam1=15；同角色普通共鸣行已有同record同值答案。
- denju全文与pattern全文不一致，必须在答案和展开层明确披露；镜像关联仍为推断，不得把该项写成直接全文一致项。
- 独审若不认可句界和首句身份，仅移除该项，严格直接899项继续，不拖住其它候选。

候选目录须包含candidates、exclusions、check_result、run_record、README和真实Inputs/analyze_row检查脚本。独审有阻断时不接线。

## 当前实施回执（2026-11-11）

- 冻结：同一 `scripts/character_skills/c21_direct_damage_targets.json`（sha256
  `425450f99d6792d9873b5a73cb08b34e633c6f58366fccb0b2e481b90e008459`）；P2 取
  `DENJU_DIRECT` 133 + `DENJU_CONDITION_MIRROR` 1。
- 实测数量：134 项／107 卡，全部 CACHE；direct 133、mirror 1；multihit 68、bigmid 66；
  134 效果 134 答案。30102 的 denju 行（4回ダメージ type110）在冻结门重放中本可通过，
  按保护卡零触碰不纳入。
- 唯一镜像：`exclusions.json.mirror_universe` 覆盖全库 denju 全文不一致的 3 条——
  1292（首句一致但无单发型伤害载体，拒绝）、20811（首句不一致，拒绝）、
  30304（接受：`patternid0=43030403 → bossskill 43030400 type22 /skillparam1=15`，
  同卡同记录同值旧答案存在）。答案与展开层均明示全文不一致、条件镜像、关联推断；
  `not_included.mirror_disclosure` 已写。
- 模块：`scripts/character_skills/card_page_inference_c21_p2_denju_direct.py`
  （sha256 `06ed26f32f9264d38c0cd625c806b7fab9ab9be54ec9349d450f540b87d2bea0`）；自建
  `DenjuView`（C20 RawView + CACHE denju + decode_report 哈希核对）与 denju resolver，
  答案构建复用 C20 `build_answer`；导出 evaluate／apply_to_groups／build_candidates／
  write_outputs，scope 缺省、错误、空值硬拒绝。`apply_to_groups` 同时写
  `inference_c21_p2_denju_direct` 与账本显式变体所需的 `inference_yg1.pattern_ids`
  （与 C20 同一消费机制）；marker identities 为 JSON 原生列表。
- 产物：`output/character_skills/c21_p2_denju_direct_20261111/`（candidates 5,730,491 B
  sha256 `857828bc…`；exclusions 234 项 + mirror_universe 3 sha256 `370b5cdb…`；
  run_record；README；check_candidate.py；check_result）。
- 命令与退出码：
  - `./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/c21_freeze_direct_damage.py --root . --write --json` → 0
  - `./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/card_page_inference_c21_p2_denju_direct.py --root . --write --json` → 0
  - `./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/check_c21_candidate.py --root . --write` → 0（28/28，约 63 s）
- 检查：900 条独立 raw 重导、denju 完整父集合与 current／selected 分列、规则重算、
  首次新增 766+134、目标效果全部 has_answer、新增未消费 0、split 不变、二次新增 0／
  跳过 900、scope 拒绝、保护卡与反例零新增、来源篡改／零 raw／冲突原子、共享文件与
  525 张 page 前后哈希不变。
- 阻断（不属于 C21 写入域）：与 P1 同一既有共享代码布局缺陷（逻辑快照路径 +
  `card_page_inference_type8.py:98`／`card_page_inference_cond.py:204` 的 `parents[1]`
  证据根）；检查器只在内存适配并登记 33 处改动，共享文件未改。正式全库生成前须由主持修复
  或显式适配。
- 仍需独审注意：CID30304 条件镜像可单独否决，严格直接 899 项不依赖；30102 保护卡零触碰；
  2 条 `DENJU_DAMAGE_ROW_CARRIER_GATE_FAILED`（20106 f1／20237 f1，type103 非单发型）
  逐行登记；关联全为推断，未实机。
