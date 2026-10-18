# 任务记录：角色技能完整解读 P2 第 1 批（charainfo 必杀技参数）

- 任务标识：`20261017-character-skills-p2`
- 负责人／对话：实施对话（DeepSeek 4.1 Flash，2026-10-17）
- 状态：**五项范围全部落盘 ＋ 验证通过（verify 56/56、crosscheck A–G `overall_ok`、DOM 12/12、真实浏览器核对）
  ＋ 收尾两项（HANDOFF／STATUS 入口、针对性审查交接）已完成**；等独立审查结论。
- 写入范围：`scripts/character_skills/`（新增 3 个脚本／模块、改 `rules.py`／`profiles.py`／`query.py`／
  `link_skills.py`／`verify_p1.py`／`crosscheck_raw.py`）、`output/character_skills/`（新增
  `charainfo_types/`、`charainfo_params/`、`P2R_HANDOFF.md`，更新 `README.md` 与本批重建的产物）、
  `work/character_skills_p2/`、本文件、`HANDOFF.md`／`STATUS.md`（仅角色技能线段落／一行）、
  `output/character_skills/review/r2_20261017_thirdparty/RECTIFICATION.md`（未动）。
- 未触碰：`AGENTS.md`、`docs/角色技能完整解读实施方案.md`、`docs/tasks/character-skills-progress.md`（主持）、
  其他任务记录、`scripts/query_effect_dictionary.py`、公共解包生成器、`review/r1_*`／`r2_*` 与
  `review/r2_*/REPORT.md` 等历史报告、原始输入与版本快照。未提交、未推送、未发布、未启动其他对话。

## 启动前核对（不重复已完成研究）

P1 四项落盘、R1 修正闭环、R2 第三方审查「带明确限制通过」＋复验「通过」均已核实落盘；
`verify_p1.py` 起点 40/40；R2 钉死的口径（`skillparam1..6` 严格比较、1110/1286、剔除 cid 1285）已在
`review/r2_20261017_thirdparty/REPORT.md` 与 `RE_VERIFICATION.md` 中确认。本批未重跑 P1 研究。

## 五项范围与结果

| 项 | 内容 | 状态 | 产物 | 关键数字 |
|---|---|---|---|---|
| 1 | bossskill／charainfo 类型域的原生常量索引 ＋ 20 个 NOT_AMONG 定性 | 完成 | `output/character_skills/charainfo_types/` | type 0..121 走跳转表（`cmp w20,#0x79`），其余落 default；122 条 type→handler；原生检查 **37/37**（含 Unicorn 实执行跳转表）；20 个 NOT_AMONG 全部给出 handler 与定性 |
| 2 | charainfo ↔ bossskill 记录级等价正式规则 ＋ 例外清单 | 完成 | `charainfo_params/equivalence.json`、`exceptions.jsonl` | universe **1287**；E0 **1110**（＝R2 口径 1110/1286）／E1 15／E2 52；X0 5／X1 104／X2 1；NOT_AMONG 949（含无 pattern 929） |
| 3 | 无 pattern 角色（929）的原生读取路径取证 | 完成 | `charainfo_types/native_checks.json` 第 6 项 | `BtlCharaUtil.CharaParamToBossSkill` 把 `skillid[0]`／`skillparam0..9` **下标对齐**写入 `BattleBossSkill`；调用方 `CharaInfoCharaModel.PlaySpMotion`、`BtlCharaUtil.GetDenjuSkill` |
| 4 | 应用已确认 boss 类型规则到 charainfo 参数 | 完成 | `charainfo_params/answers.jsonl`、`profiles/` | 新增答案 **522**（页求和＝唯一 522）；按类型 105→214／13→184／112→56／27→40／66→26／16→2；证据范围仅 `BY_TYPE_EXTRAPOLATED` |
| 5 | 头部类型 3／22／110 原生证据与规则 | 完成（结论为"缺证"） | `charainfo_types/head_types.json` | 255／207／179 角色；handler 与读取槽位已定位，伤害基数所在全局技能表未定位 → **不给数值答案**，缺证写明 |
| — | 验证扩展 | 完成 | `verify_p1.py`、`crosscheck_raw.py`、`work/character_skills_p2/html_dom_test.js` | verify **56/56**（原 40 项全保留）、crosscheck **A–G `overall_ok=True`**、DOM 夹具 **12/12**、真实浏览器核对通过 |

## 覆盖增量（相对 P1 基线，基线取自改动前的 `profiles/`）

- 答案：29953 → **30475**（页求和）；唯一记录 29729 → **30251**；新增 **522**（双口径相同，
  因 `charainfo` 记录每 cid 唯一）。
- `charainfo` 未解释字段：444790 → **444268**（−522）。
- 证据范围：已逐条评审 9400 不变；按类型套用 20553 → **21075**（未新增第三类）。
- 缺口队列：字段级 5797 → **5790**；类型级 377、有线索 323、断链 0 不变。
- 角色状态：**部分 1323／仅未知 913／完整 0 不变**；获得 charainfo 答案的 **199** 个角色此前已因
  bossskill 等表有答案，故无状态迁移（如实报告为 0，并说明原因）。
- 描述片段 41594／有归属 7383→**7862**（基线 7383 ＋ 增量 **479**；口径＝基线条目 31 ＋ 关键词提示片段，
  新增 522 条答案带来 479 个新归属片段）。

## 关键原生发现（本批新增证据）

1. `bhSkill.ExecSkill`（`0x1297ccc`）是真正的 `switch`：`cmp w20,#0x79; b.hi 0x1298ca0`，
   跳转表 `0x206ee04`（uint16×4＋基准 `0x1297d4c`）。**type 0..121 有处理器，>121 与负数走 default**；
   导出数据最大 type 119，APK `charainfo.skillid[0]` 的 −1（137 行）同样落 default。
2. 每个 case 是一个 stub，指向 `Exec_*`；13/14/15/16 共用 `bhSkill.Exec_HEAL` 靠 w2/w3/w4 区分模式
   （w4 即 type 号），27→`Exec_REGENERATION`，105→`Exec_ATTACK_FRONT_REPEAT`，112→`Exec_SET_AREA2`，
   66→`Exec_FIELD_CHANGE`，3→`Exec_ATTACK_AREA`，22→`Exec_ATTACK_FRONT`，110→`Exec_ATTACK_AREA_REPEAT`。
3. handler 实际读取的 util 偏移（`skillparamN` → util+0x2c+4N）与 `rules.json` 已确认规则的槽位**相交**
   （type27 1/2/3、type105 1/6、type13 1/2/3/6、type112 0/1/4/5/8/9…），是独立得到的交叉验证；
   type112 `skillparam7` 不在设置路径的读取集合内，规则来自陷阱更新路径，已作为例外登记而非删除。
4. `BtlCharaUtil.CharaParamToBossSkill` **有两个同名重载**（`0x13aa390`、`0x13aa764`）；带
   `get_skillparamN→set_skillparamN` 全序列的是 `0x13aa764`。本批的"下标对齐"结论只建立在该重载上。

## 中途发现并修掉的自有问题

1. **等价门控最初只覆盖 `skillparam*`** → type27 的 `/skillflag0_1` 绕开门控，多出 17 条无等价前提的答案
   （曾使状态计数从 913 变 899）。改为"凡能取到规则的 charainfo 字段都要过门控"，
   表外字段另加逐字段相等检查（float32 归一、缺省读 0.0）→ 522 条（含 10 条 flag 答案）。
2. **页面漏了中文理由**：`profiles.REASON_TEXT` 未加新理由码，页面直接显示
   `CHARAINFO_EQUIVALENCE_UNPROVEN`。由 DOM 夹具发现并修掉（新增 `REASON_TEXT` ＋ `query.py` 的 `REASON_ZH`）。
3. **交叉核对脚本自身解析顺序错**：先合并 cache 与 APK 再按键覆盖，让 APK 覆盖缓存，E0 算成 1088。
   改为与 `Table.get` 相同的逐 ID 缓存优先后，独立重推与产物**逐类一致**（E0 1110、universe 1287）。
4. `equivalence.classify` 的类别判定顺序会让 14 个 type 槽为 0 的角色落入 X1 而非 E0，
   使 E0 变成 1096 而非 R2 钉死的 1110。改为"先判值类、后判 type0"并给这些角色 `type_zero_member` 标记，
   严格口径与 R2 完全对齐（它们本就不产出答案，因为 rules.json 对 type 0 没有规则）。
5. `charainfo_params` 的增量统计曾把"charainfo 答案数"与"角色答案总数"直接相比，报成 0 与 0；
   改为"本批至少新增一条 charainfo 答案的角色数"（199）与"状态迁移数"（0）分别报告并注明原因。

## 运行命令（项目根目录）

```powershell
& .\.venv\Scripts\python.exe -B scripts/character_skills/scope_diff.py
& .\.venv\Scripts\python.exe -B scripts/character_skills/link_skills.py
& .\.venv\Scripts\python.exe -B scripts/character_skills/charainfo_types.py
& .\.venv\Scripts\python.exe -B scripts/character_skills/profiles.py
& .\.venv\Scripts\python.exe -B scripts/character_skills/gaps.py
& .\.venv\Scripts\python.exe -B scripts/character_skills/charainfo_params.py     # 首次先加 --snapshot-baseline
& .\.venv\Scripts\python.exe -B scripts/character_skills/verify_p1.py            # 56/56
& .\.venv\Scripts\python.exe -B scripts/character_skills/crosscheck_raw.py       # overall_ok
& .\.venv\Scripts\python.exe -B scripts/character_skills/query.py --cid 30236
node work/character_skills_p1/html_dom_test.js
node work/character_skills_p2/html_dom_test.js
```

## 验证

- `verify_p1.py` **56/56**（P1 原 40 项保留；新增 16 项：类型索引边界／handler 映射／原生检查全过／
  数据类型在界内／NOT_AMONG＝20 且有判定、等价口径 1110＋1177、X1 两侧原值齐备、类别划分 2236＝1287＋949、
  答案双口径 522＝522＝唯一、门控确有拒绝、无第三类证据范围、type13 防御/速度不互换（40 样本）、
  type105 倍率/次数不互换（107 样本，含 7 个取值相等的样本仍不互换）、X1 角色无迁移答案）。
- `crosscheck_raw.py` **A–G `overall_ok=True`**：F 项不导入本管道模块，直读原始 charainfo／bossinfo
  重推类别；G 项对 38 条 charainfo 答案逐条重读原始值与匹配 boss 同槽值并判等。
- DOM 夹具 `work/character_skills_p2/html_dom_test.js` **12/12**（P1 的 8 项 ＋ 4 项 P2 用例）。
- **真实浏览器**（`http.server` 本地服务，IAB）：页头 `共 2236 个角色；完整 0／部分 1323／仅未知 913`；
  cid30236 的 charainfo 块含 `/skillparam1`／`/skillparam6` 答案与"按类型套用"；cid2053 的 charainfo 块
  无迁移答案、无原始理由码、显示中文门控说明。
- **默认 GBK 环境**（`env -u PYTHONIOENCODING PYTHONUTF8=0`，探针确认 stdout=gbk）：8 个入口全部
  exit 0、stderr 0 字节；`query.py --cid 30236` 日文正常输出。

## 剩余缺口与阻塞

- 无 pattern 的 929 个角色：`charainfo` 参数没有可对齐的 boss 记录，等价未证实 → 保持未解释
  （理由码 `CHARAINFO_EQUIVALENCE_UNPROVEN`）。**缺证**：这些角色必杀技在战斗中的参数来源
  （已排除 `getDefaultBossPattern` 路径，它按 `patternN` 取 pattern，无 pattern 即返回空）。
- 头部类型 3（255 角色）／22（207）／110（179）：handler 与槽位已定位，**缺证**是
  `bhSkillUtil.AttackList_Common` 的伤害基数与 `[0x29e9000+0x6e8]+0xb8` 全局技能表的内容；补到后可按
  "槽位 → 倍率/次数"给数值规则。
- X1 的 104 个角色两侧数值确有不同（同快照内 charainfo 与自身 pattern 的 bossskill 不一致；
  已验证**不是**跨层版本偏斜——同层 boss 记录与缓存 boss 记录一致）。**缺证**：游戏在何种上下文用哪一侧。
- 其余类型（122 个 type 中的大多数）没有已确认规则；每个 type 只有部分槽位有规则时，其余槽位仍显示未解释。
- `profiles/index.html` 浏览器标题仍为「角色技能档案（P1 首批）」（纯文案）。

## 下一批建议（交主持决定）

按主持进度文件的队列：`skilllist type=8/26/67/1059` 族；本批的类型索引（`charainfo_types/`）与
"handler 槽位"方法可直接复用到那些类型的槽位筛选上。

## 最近更新

2026-10-17：读交接确认 P1／R1／R2 已落盘 → 原生勘察（类型派发、`CharaParamToBossSkill`、等价口径复现、
异常分层、头部类型 handler）→ 三项落盘（`charainfo_types/`、`equivalence.py`、`charainfo_params/`）→
改 `rules.py`／`profiles.py`／`query.py`／`link_skills.py` → 重建（含基线快照）并核对增量 →
扩展 `verify_p1.py`（56/56）与 `crosscheck_raw.py`（A–G）→ DOM 夹具 12/12 ＋ 真实浏览器核对 →
GBK 八入口回归 → 收尾（`HANDOFF.md` 角色技能线入口、`STATUS.md` 一行、`P2R_HANDOFF.md`）。
下一步：等针对性独立审查结论，按其结论修正后再进 P2 第 2 批。
