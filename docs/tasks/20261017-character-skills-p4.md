# 任务记录：P2 第 4 批（现成增量＋索引加固）

- 任务标识：`20261017-character-skills-p4`
- 负责人／对话：本线实施对话（角色技能完整解读 P2 系列）
- 状态：**待针对性审查**（本批已实施、验证全绿，等待审查对话复验）
- 允许写入范围：`scripts/character_skills/`、`output/character_skills/`（本任务产物与 README／交接）、
  `work/character_skills_p4*`（本批快照）、本文件
- 共享依赖：`work/protection/il2cpp_loader_seed1.bin`（原生镜像，只读）、
  `work/protection/metadata_aei_decoded.bin`（元数据，只读）、`output/character_skills/links/character_skills.jsonl`
- 未触碰：`review/` 历史报告、`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、
  `docs/tasks/character-skills-progress.md`（主持）、公共生成器的非本线部分

## 目标（逐项）

0. 复验遗留文字修正：P2B3 整改记录的「entries 15/14」→ 实际「rate 14／dmg 13」＋1112 的 anchoring 口径说明。
1. 索引加固：按审查者建议建「按 type 仿真 vs 静态解码」双路核对（最小形式），并作为常驻检查纳入 `skilllist_types.py`。
2. 现成增量：确认 type 36/1003/1005/1026 在攻/移/伤三路径落与 type 8 相同的单槽分支，复用其换算产出答案。
3. 应用重建＋覆盖增量报告（双/三口径、受影响角色核账、状态迁移数）。
4. 不扩大范围：其余槽位、type 80/96/67 复合分支、1036 缩放基数留缺口队列。

## 证据链

- 分支归属：`dispatch_map.json` 的 `leaf`／`gate_rva`／`slot_calls`（同一条分支，逐地址可比）。
- 派发解析：双路——Unicorn 仿真（`mask_registers` 按序言 `mov wN,#1` 自动预置位测试常量寄存器）与
  纯静态指令解码求值器（自维护寄存器与标志位、不执行）。5 路径 × 3001 type 一致。
- 换算复用：`rules.py` 顶部 `answer_kind` 通用分发；type 8 与四类型共用一份实现。
- 方向：`param2`＝移动速度乘数、`param3`＝受伤量倍率（减伤显式标注「不是固定防御量」）；
  正文「与えるダメージ」不驱动 `param3`。

## 产物

| 产物 | 位置 |
|---|---|
| 派发索引（含双路核对结果） | `output/character_skills/skilllist_types/dispatch_map.json`、`native_checks.json` |
| 规则字典（12 条新规则＋type8 三槽 answer_kind） | `output/character_skills/skilllist_types/field_dictionary.json` |
| 增量报告 | `output/character_skills/skilllist_types/same_leaf_increment.json` |
| 角色档案／记录／摘要（重建） | `output/character_skills/profiles/` |
| 缺口队列（重建） | `output/character_skills/gaps/` |
| 直读交叉核对 | `output/character_skills/validation/crosscheck_raw.json`（新增 J 区） |
| 本批快照 | `work/character_skills_p4_records_before.jsonl`、`work/character_skills_p4_summary_before.json` |
| 交接 | `output/character_skills/P4_HANDOFF.md` |

## 关键数字

- 新增答案 **999**（页求和）／**963**（记录级）／**672**（（表,记录,层,字段）去重）。
- 未解释字段 436880 → **435881**；规则答案 37863 → **38862**（唯一 37066 → 38029）。
- 可达角色 36→156／1005→38／1026→17／1003→8（去重 213）；**状态迁移 0**（此前都已有答案）。
- 缺口字段级 5766 → **5754**；断链 0。

## 验证

`verify_p1.py` 99/99（本批 +10 项）、`crosscheck_raw.py` `overall_ok=true`（J 区核对 159 条）、
`skilllist_types.py` 33/33；默认 GBK 控制台可运行；重建后三份关键产物 SHA-256 逐字节相同。

## 下一步

交针对性审查（重点样本见 `P4_HANDOFF.md` §5）。审查通过后，再下一批候选：type 80/96/67
复合分支的原生研究（较重，已由本批双路核对打下防回归基础）。
