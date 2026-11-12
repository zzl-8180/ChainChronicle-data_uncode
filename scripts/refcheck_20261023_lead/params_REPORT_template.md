# param_table 与参数推断脚本 —— 2026-10-23 两个新目录核查（只读）

核查对象
- 新版1：`其他人的参考/claude_cc_site_pages 20261023/`（本机生成 2026-10-23 01:25–02:46）
- 新版2（给 GPT 的包）：`其他人的参考/claude_cc_site_pages_给GPT_20261023/claude_cc_site_pages/`（04:34–10:41，**比新版1晚**）
- 旧版基线：`其他人的参考/claude_cc_site_pages/`（2026-10-17 副本）
- 我方 10-17 结论：`output/reference_analysis/claude_cc_site_pages/README.md` + `param_table_crosscheck.csv`（1610 行）+ `crosscheck_summary.json`

本轮只做**参数含义表与参数推断脚本**这一块；不含页面、卡片、翻译、Leader 条件等其它块。只读，未修改 `其他人的参考` 下任何文件。

文中标记：**【对方声明】**＝仅出自对方文档/注释；**【核实】**＝本轮实际跑数或比对得出；**【推断】**＝由观察推出、未独立验证。

---

## 0. 结论摘要

1. **结构**：`param_table.json` 仍是 `{paired_cards, rows}`，`paired_cards` 两次都是 **2037**；行数 1673（旧 1610）。表分布 skilllist 934（+63）/ bossskill 382（±0）/ charainfo 357（±0）——**行数增长 100% 来自 skilllist**，而且 62 条集中在 skilllist 的 **2000–2020 号「SA（附加效果技能）」类型**，1 条是 `skilllist type58 param0`。
2. **增长机制【核实】**：`infer_params.py` 新版比旧版多做了三件事——把必杀槽位的 `slot["sa"]`（`L232-233`）和角色 `charainfo.s_ability`（`L250-251`）也计入统计、把「队伍能力」单独成段（`is_party` `L159-161`，用在 `L258-260`）、卡片路径改 `*/data/card.json`（`L286`）。所以**不是新解包数据、也不是新卡**，而是同一批记录里原本被漏掉的 SA 槽位被纳入统计。
3. **63 条新增里只有 2 条高于「统计推断」**：`skilllist 58 param0`（用户确认，无敌时间 1 秒）和 `skilllist 2012 param4`（参考推断，暴击率）。**0 条解包确认**；其余 61 条是统计推断 19 / 弱证据 21 / 未知 19 / 待定 2。
4. **33 条既有行改判**：26 条改了 status（其中 3 条升到用户确认、4 条升到参考推断、19 条升到统计推断、1 条被降为待定），7 条只改换算/单位/标签。**旧版唯一冲突 `skilllist 99 param8` 已改为「移动速度」，与我方证据一致 —— 已修正。**
5. **来源追溯【核实，硬证据】**：对方三个脚本的注释、`REFERENCE` 表注释、`HANDOFF.md` 的 10-22/10-23 章节**都明写引用了 `cc_skill_values_20261021` / `cc_skill_values_20261022`**（即我方交付包及其派生）；`build_cards.py` 等 4 个脚本读的是 `CC_full_unpack_results_data_20261016/...`（我方 20261016 交付的解包表）。更进一步：**给 GPT 的那个包里直接塞了一份与我方 `output/cache_full_20261015_v3/decoded/leaderabilityinfo.data5.json.raw` 字节完全相同的文件**（83980 字节，SHA-256 `06dae31c74d91d95a5390c25a495910072e7abe2093ada98aab2d606bc2aa996`）。
   → 结论：**它不是新证据，是「回收我方数据 + 他们自己抓的网站数字」的比对结果**。唯一真正属于外部的新增信息是：(a) 网站（koncoo）数字本身；(b) 4 条用户口述确认；(c) 自称的「GPT 反汇编」（在本目录内**无法复核**，且它引用的是 `cc_skill_values_20261022`，本身是我方包的派生物）。
6. **对我方最有价值的用法不是「新规则」，而是「网站对照命中率」**：新版补齐了我方已用代码确认的 45 个槽位的网站拟合数（§6 表）。例如 `skilllist 2012 param0` 662/696、`param5` 464/500；`skilllist 2003 param9` 511/537；`bossskill 13 param1` 1526/1522；`skilllist 1017 param3` 590/624。这些可以直接作为我方已确认结论的**独立旁证（网站侧一致性）**引用。
7. **真正对我方新增的可用信息很少**：`skilllist 1095 param2＝移动速度`（参考推断，但与我方 `output/ordinary_effects/ability1095/README.md` 批 12 的**代码证据独立吻合**）、`skilllist 1017 param2＝移动速度`（我方仍记为「未知 param2」，站点 160/485 命中、dec 155）、`type58 param0＝无敌 1 秒`（我方未覆盖 guts）、`type116 param1＝随机攻击间隔`（我方未覆盖随机攻击）。统计推断级的一切都只能当验证候选，**不得混入「可确认」**。
8. **新引入的矛盾**：新版给 `skilllist 2012 param7/param8` 打了「伤害 raw 倍」（弱证据，62/527、3/696），而我方代码证据是 **param7＝支持目标数量上限、param8＝TARGET_TYPE（31=pGROUP_ALL、64=MYSELF）**；`skilllist 2003 param5/param6` 打了「攻击力」，我方是 **param5＝自身 _move、param6＝自身 _defense**。这几行不要采用。

---

## 1. 结构与分布（问题 1）

### 1.1 顶层结构与行数

| 项 | 新版 20261023 | 旧版 20261017 |
|---|---|---|
| 文件 | `param_table.json`（796,090 B） | `param_table.json`（766,009 B） |
| 顶层键 | `paired_cards`、`rows` | 同 |
| `paired_cards` | 2037 | 2037 |
| `rows` | **1673** | **1610** |
| 行键 | `table,type,slot,status,site_statistics,label,conversion,unit,hits,cards_with_value,hit_rate,decisive_hits,decisive_cases,examples,alternatives`（15 个，全部齐全） | 同 |
| 键唯一性 | 1673 个 (table,type,slot) 唯一 | 1610 唯一 |

规范化后的全量行见 `param_rows_new1673.json`（15 原字段 + `evidence_grade` / `status_group` / `prev_1017` 快照）。

从 `infer_params.py` 可复核字段含义（新版行号）：`site_statistics` 是**统计候选**的摘要（`L360`），`hits` 是**最终采用标签**下的命中数（`L365-388`）——两者在「解包确认/用户确认/参考推断」被外部规则改写时会不一致，**读表时必须看 `hits` 与 `alternatives`，不能只看 `site_statistics` 的前缀**。这是本次最容易读错的地方（例：`skilllist 1017 param2` 的 `site_statistics` 写「防御力% … 430/485」，但 label 是移动速度、`hits`＝160，`alternatives` 里才是 `移动速度% ×160`）。

### 1.2 status 分级分布

| status | 新版 1673 | 旧版 1610 | 差 |
|---|---|---|---|
| 解包确认 | 37 | 37 | 0 |
| 用户确认 | **4** | 0 | +4 |
| 参考推断 | **5** | 0 | +5 |
| 统计推断 | 536 | 502 | +34 |
| 弱证据 | 460 | 452 | +8 |
| 未知 | 534 | 518 | +16 |
| 待定（合并计数） | 97 | 101 | −4 |
| **合计** | **1673** | **1610** | **+63** |

待定的细分（`status` 原值）——新版：`待定（与param3同标签）`27、`param1`20、`param4`16、`param2`12、`param7`11、`param5`6、`param0`4、`param8`1。

> 说明：「待定」不是对方的初始分级，而是**后处理降级**——新版 `infer_params.py L398-411`：同一 (table,type,label,unit) 组里若已有更强的一行，其余 `统计推断` 行改成 `待定（与paramN同标签）`。该后处理只对 `解包确认/统计推断` 生效（`L400 rank`），`用户确认/参考推断` 既不参与降级、也不作为组内基准 —— 这是一处**实现上的不对称**，会让用户确认规则压不住统计行。

可用于填数的等级只有 `numbers.py L12`：`USABLE = (解包确认, 用户确认, 统计推断, 参考推断)`。**合计 582 行（34.8%）**；其余 1091 行（65.2%）不使用。

### 1.3 table × type 分布（只看有变化的）

| table | 新版 | 旧版 | 差 |
|---|---|---|---|
| skilllist | 934 | 871 | **+63** |
| bossskill | 382 | 382 | 0 |
| charainfo | 357 | 357 | 0 |

有增量的 19 个 type（全部在 skilllist，除 `58` 外都是 SA 类型，**【推断】**2000 段是 SA 记录的编号段）：

| type | 旧→新 | type | 旧→新 |
|---|---|---|---|
| 2012 | 0→9 | 2013 | 0→4 |
| 2007 | 0→9 | 2018 | 0→4 |
| 2003 | 0→8 | 2004 | 0→3 |
| 2015 | 0→7 | 2014 | 0→3 |
| 58 | 7→8 | 2000/2001/2002/2006/2016 | 各 0→2 |
| 2005/2008/2009/2019/2020 | 各 0→1 | | |

新增行涉及 19 个 type；新增行里 **12 条连 label 都是空**（`status=未知`），49 条带 `examples`。

### 1.4 全表质量量级（可用于判断「值不值得花时间」）

| 指标 | 行数 |
|---|---|
| 解包确认+用户确认+参考推断 | 46 |
| 统计推断 且 decisive≥50 | 110 |
| 统计推断 且 decisive≥20 | 232 |
| 统计推断 但 decisive<3（旧分析点过的高风险同类） | 54 |
| 弱证据+未知 | 994 |

旧分析批评的「`opp_u<3` 逃生口」仍在：`infer_params.py L349` `enough_u = n_u >= 3 or opp_u[key] < 3`。`v==1` 的记录仍被全局跳过（`L301-302`），所以源值恒为 1 的字段（`1017 param0`、`99 param1/2/3` 触发阈值）系统性缺失 —— **本条与旧版一致，未改**。

### 1.5 两个 2026-10-23 目录并不是同一快照【核实】

| 文件 | 新版1 | 新版2（给GPT） | 差异 |
|---|---|---|---|
| `param_table.json` | 2026-10-23 01:40 / 796,090 B | 10:0x / 795,432 B | **7 行不同**，键集合完全相同 |
| `scripts/infer_params.py` | 02:14 / 46 行 REVIEWED | 04:37 / **53 行 REVIEWED** | 新版2 多 7 条 REVIEWED：`skilllist 1014 param1`（间隔）+ `skilllist 1104 param0–param5`（人数上限/攻击力/移动速度/防御力/暴击率/暴击威力，单位 `n%`） |
| `scripts/numbers.py` | 01:25 | 04:34 | 新版2 多 `type1091` 与 `1009` 同级（三档法力）；**多补超上限位 `bit 3 → 30%`** |
| `scripts/unpack_text.py` | 01:34 / 350 行 | 09:27 / **515 行** | 新版2 多 `per_member/fill_variants/fill_atk/fix_tiers/norm_n` 等文本函数 |

→ **要引用「最新状态」应引用新版2**。本轮 REPORT 的逐行统计以新版1（1673 行的 `param_table.json`）为准，特此说明；7 行差异单独列在 §2.3。

---

## 2. 63 条新增逐条 + 33 条改判（问题 2）

### 2.1 63 条新增（新版有、旧版无），按证据等级→决定性排序

> 全部 63 行都在 `skilllist`；`status` 为 用户确认 1、参考推断 1、统计推断 19、弱证据 21、未知 19、待定 2；**解包确认 0**。数据同 `new_rows_since_1017.json` 的 `added`。

{{ADDED_TABLE}}

**63 条里 status≥参考推断（即可能有用）的只有 2 条：**

| 行 | status | 语义 | 依据 | 我方是否已有 |
|---|---|---|---|---|
| `skilllist 58 param0` | 用户确认 | 无敌时间 raw 秒（guts 免疫死亡后无敌，p0 恒为 1 → 1 秒） | 用户口述（`infer_params.py L91-93`；`HANDOFF L126`） | 我方**未覆盖** type58 |
| `skilllist 2012 param4` | 参考推断 | 暴击率 x100（百分点加算） | **回收**：`cc_skill_values_20261021 模板推断（批 8 暴击 2012 链）`（`L49-52`） | 我方 `output/ordinary_effects/ability2012/README.md L8` 已确认同一语义 |

其余 61 条（统计推断 19 / 弱证据 21 / 未知 19 / 待定 2）的证据强度：decisive≥10 的仅 8 条，decisive≥20 的 5 条，hits≥50 的 9 条。**没有一条达到我方「可确认」的门槛。**

### 2.2 33 条既有行改判（status / label / 换算 / 单位变了）

其中 26 条动了 `status`（3 条升到用户确认、4 条升到参考推断、19 条升到统计推断、1 条降为待定、其余为弱→统计），7 条只改换算/单位/标签（附表最后几行）。另有 **107 行只是命中数/决定性数变了、结论没变**（列在 `new_rows_since_1017.json` 的 `recount_only`）。

{{CHANGED_TABLE}}

改判要点：
- **升级值得看**：`bossskill/charainfo 116 param1`（弱证据→用户确认，攻击力→间隔）、`skilllist 1095 param5`（弱证据→用户确认，防御力→暴击率）、`skilllist 67 param2`（→参考推断，移动速度 170/344 dec 137）、`skilllist 1017 param2`（→参考推断，防御力→移动速度）、`skilllist 1095 param2`（→参考推断，暴击威力→移动速度）、`skilllist 1106 param0`（→参考推断，颗）。
- **降级**：`bossskill 116 param7`（统计推断→待定，dec 0）。
- **换算更正**：`skilllist 1051 param1/2/3` 由 `x100 / -x*100` 统一改为 `|x|x100`（按目标取绝对值）；`skilllist 1095 param8` 由「HP raw 秒」改为「其他 (x-1)x100 %」——后者仍是弱证据级，无意义。
- **标签更名不改语义**：`skilllist 23 param4`、`48 param5` 由「持续时间」改名「CD」（`REVIEWED`，见 §3）。

### 2.3 新版1 → 新版2 的 7 行差异（要引用「最新」时用这份）

| 行 | 新版1 | 新版2 | 依据 |
|---|---|---|---|
| `skilllist 1014 param1` | 弱证据 回复 x100 %（16/53） | **统计推断 间隔 raw 秒**（hits 0） | 新增 REVIEWED：副队回复 p1＝间隔，「30+ 张卡写 5 秒，写 4/6 秒的也对上」 |
| `skilllist 1104 param0` | 待定 攻击力 raw % | **统计推断 人数上限 raw 人** | 新增 REVIEWED：`<所属>的队员越多…` 每人加算布局 |
| `skilllist 1104 param1` | 弱证据 攻击力 x100 % | **统计推断 攻击力 x100 n%** | 同上（1303 0.03 → 3n%） |
| `skilllist 1104 param2` | 待定 攻击力 x100 % | **统计推断 移动速度 x100 n%** | 同上 |
| `skilllist 1104 param3` | 弱证据 攻击力 -x*100 % | **统计推断 防御力 -x*100 n%** | 同上 |
| `skilllist 1104 param4` | 弱证据 暴击威力 x100 % | **统计推断 暴击率 x100 n%** | 同上 |
| `skilllist 1104 param5` | 弱证据 暴击威力 x100 % | **统计推断 暴击威力 x100 n%** | 同上 |

`type1104` 这 6 行是「按人数叠加」的整套布局，**我方完全没有这个类型的证据**，是本次新增里唯一结构完整、可独立验证的一组候选（证据仍只是「逐卡人工核对 + 网站措辞」，非代码级）。

---

## 3. 三个推断脚本的知识表（问题 3）

三个脚本的分工：`infer_params.py` 出 `param_table`（含义规则 + 统计）；`numbers.py` 用 `param_table` 把原始参数变成带标签的数值（换算函数表 + 门控）；`unpack_text.py` 把数值填回中文文本（措辞级规则表）。

### 3.1 `scripts/infer_params.py`（新版1，463 行）

| 表 | 条目 | 源文件行 | 作用 |
|---|---|---|---|
| `REFERENCE` | **5** | `L44-53` | 回收外部（我方）规则的覆盖层，status＝参考推断 |
| `CONFIRMED` | 源码写 **25**，运行期 **37** | `L55-85`（镜像循环 `L143-145`） | 解包确认 |
| `USER_CONFIRMED` | **4** | `L90-101` | 用户确认 |
| `REVIEWED` | **18** | `L103-141` | 人工逐类型核对，status 仍记 **统计推断** |
| `LABELS` | 22 | `L23-24` | 网站文本里可识别的标签词表 |
| `SYNONYMS` | 3 | `L25` | 概率/一定几率→几率；必杀威力→必杀技威力 |
| `TRANSFORMS` | **8** | `L26-35` | 换算候选：`x100`、`(x-1)x100`、`(1-x)x100`、`-x*100`、`(x-1.5)x100`、`x*10 (ATK*%)`、`x*100 (ATK*%)`、`raw` |

> `CONFIRMED` 25→37 的镜像：`L143-145` 把每条 `bossskill` 规则复制到 `charainfo` 同型同槽。**这 12 行 charainfo 是推断出来的、未独立验证**（旧分析已指出，本轮未变）。

**`REFERENCE`（5 条）完整清单 —— 全部注明了回收来源：**

| 行 | 依据注释（原文） |
|---|---|
| `skilllist 1017 param2` = 移动速度 (x-1)x100 % | `cc_skill_values_20261021 模板推断＋原项目 30236 逐条审定` |
| `skilllist 1095 param2` = 移动速度 (x-1)x100 % | `原项目 30236 逐条审定（65000001）` |
| `skilllist 67 param2` = 移动速度 (x-1)x100 % | `cc_skill_values_20261021 模板推断` |
| `skilllist 1106 param0` = 颗 raw 颗 | `原项目 30236 逐条审定（Chain 获珠数）` |
| `skilllist 2012 param4` = 暴击率 x100 % | `cc_skill_values_20261021 模板推断（批 8 暴击 2012 链）` |

表头注释（`L40-43`）原文：
> `# Rules taken from the other AI's bundle (cc_skill_values_20261021, template inference batches + the unpack project's per-record review of cid30236) where our own site statistics are weak, tied, or fooled by equal values.`
> `_REF_GPT = "cc_skill_values_20261021 模板推断"`

`REFERENCE` 的生效逻辑（**重要**，`L380-388`）：只有当本表统计「不够强」或与参考结论不一致时才套用参考规则；套用后把 `hits` 换成**参考标签**的命中数。所以**参考推断行的 `hits` 天然偏低**（例：`2012 param4` 106/491＝21.6%，`1095 param2` 5/165＝3.0%），这不是「实测支持弱」的独立证据，而是「统计被打败后被覆盖」的结果；反过来，`67 param2`（170/344，dec 137/282）是统计本身也强、只是被抬到参考级的。

**`CONFIRMED`（37 条，`L55-85` + 镜像）** —— 关键依据注释（原文摘录）：
- `L38`：`# Rules the unpack project confirmed from game code / native checks (see ChainChronicle-data_uncode HANDOFF.md).`
- `L78-81`（`skilllist 99 param7/8/9` 的依据，**正是回收我方结论的那一条**）：
  > `# param7/8/9 feed TimePowerUpData _attack/_move/_defense (cc_skill_values_20261022 §22/§26, disassembly):`
  > `# p8 is the MOVE drop — 11222 -0.2 / 221 -0.3 / 20107 -0.15 = the site's 移动速度; p9 (damage taken) is 防御力.`
  > `# The earlier "p8 = 防御力" was wrong (2026-10-22).`

完整 37 条（表/type/slot → 标签/换算/单位）已机器提取在 `knowledge_tables.json`；与旧版逐条是同一套（`99 param8` 的标签由防御力改成移动速度）。

**`USER_CONFIRMED`（4 条，全部带依据注释）：**

| 行 | 语义 | 依据注释（原文） | param_table 现状 |
|---|---|---|---|
| `skilllist 58 param0` | 无敌时间 raw 秒 | `免疫死亡后无敌1秒（p0 恒为 1）`（`L91-92`：用户 2026-10-22 确认，网站 2/3 秒错） | 用户确认，hits 0/0 |
| `skilllist 1095 param5` | 暴击率 x100 % | `能力的暴击率不含基础暴击率（网站多写 10%）`（`L94-95`：用户 2026-10-23 确认） | 用户确认，hits 10/221，dec 10/219 |
| `bossskill 116 param1` | 间隔 raw 秒 | `随机攻击间隔＝p1；网站 p1<1 时写的「1秒」是未实测的惯用写法`（`L97-98`：用户 2026-10-23） | 用户确认，hits 0/84 |
| `charainfo 116 param1` | 间隔 raw 秒 | `同上（必杀本体行）` | 用户确认，hits 0/15 |

**`REVIEWED`（18 条，`L103-141`）** —— 声明依据是「逐类型人工比对每张卡网站文本（2026-10-22）」，但**注释里给的是卡号级举例，不是代码证据**，最终 status 仍是「统计推断」，并在 `site_statistics` 里加「；逐类型人工核对」。清单（18 条）：

`skilllist 48 param5`＝CD秒、`23 param4`＝CD秒、`58 param4`＝复活回复 HP、`2012 param6`＝攻击间隔倍率(1+x)、`3000 param4`＝防御力(敌ATK%)、`2003 param8`＝移动速度、`1051 param0/1/2/3/4/5`＝持续时间/攻击力/移动速度/防御力/暴击率/暴击威力、`1074 param2/3/6/7`＝移动速度/防御力/暴击率/暴击威力、`bossskill 116 param4` 与 `charainfo 116 param4`＝伤害倍。

代表性原注释：
- `L104-105`：`# reflect (…ReflectionBullet): p0 reflect 倍, p4 damage-cut ratio, p5 cooldown — 13201/13207/…: 5 -> CD5秒`
- `L119-120`：`# SA_PowerDrain (type2003 …) uses 99's data path: p7 attack, p8 move, p9 damage taken (cc_skill_values_20261022 §23, ExecSA_PowerDrain)`
- `L122-128`（1051 与 116 的整段布局推断，含「p6 1.5 多半是半径＝1格、p8 0.5 含义不明，均未使用」的自我限制说明）

### 3.2 `scripts/numbers.py`（新版1，190 行；新版2 194 行）

| 内容 | 条目 | 行 | 说明 |
|---|---|---|---|
| `USABLE` | **4** | `L12` | `("解包确认","用户确认","统计推断","参考推断")` |
| `CONV` 换算函数表 | **10** | `L14-25` | `x100`、`(x-1)x100`、`(1-x)x100`、`-x*100`、`(x-1.5)x100`、`x*10 (ATK*%)`、`x*100 (ATK*%)`、`raw`、`1+x`、`\|x\|x100` |
| `ENEMY_TYPES` | 2 | `L70` | `(99, 2003)` 作用对象是敌人；`L75` 另把 `1051` 的 `param6==1` 记录也当敌方 |
| 超上限位表 | 5+1 | `L100-113` | 新版1：`bit 12/11/10/9/8 → 100/80/60/40/20%`；新版2 追加 `bit 3 → 30%`（`L111-113`） |
| 法力槽分档 | 1 | `L88-99` | `type1009`（新版2 扩到 `1009/1091`）p1–p5 × m1/m2/m3 逐档 |

**超上限位表与我方证据的关系【核实】**：我方 `output/boss_heal/constants.json` 的 `bits.values = [40,35,41,42,43,44]`、`values.values = [1.2,1.3,1.4,1.6,1.8,2.0]`。新版1 的 5 个位（8–12 → 64 位第 40–44 位）对应 1.2/1.4/1.6/1.8/2.0，**与我方常量一致**；新版2 新加的 `bit 3`（64 位第 35 位 → 1.3 → 超上限 30%）**也与我方 [35]→1.3 一致**。这是本轮发现的**唯一一处对方独立推进到与我方代码常量完全吻合**的地方（但他们的注释自述依据是网站实测：type30 的 12/16 张网站写 30%，不是反汇编）。

`numbers.py` 的 `_emit` 还有两处**手写门控**，读表时要注意：`v == 0` 直接跳过（`L79-80`）；`(x-1)x100 / (1-x)x100` 结果≈0 跳过（`L85`）。

### 3.3 `scripts/unpack_text.py`（新版1，350 行；新版2 515 行）

知识表只有一张 `NAMED`（**8 条**，`L67-77`）——「措辞里出现了这个说法，就用该标签的值去填这个数字」：

| 标签 | 正则要点 | 限定 | 行 |
|---|---|---|---|
| CD | `CD\s*(\d+(?:\.\d+)?)\s*秒` | 无 | `L68` |
| 间隔 | `一定(时间)?间隔（N秒）(?=内?随机)` | **仅 type116** | `L70` |
| 间隔 | `一定(时间)?间隔（N秒）` | 无 | `L71` |
| 复活回复 | `(HP回复\|回复HP\|HP)（HP?N点?）` | 无 | `L72` |
| 复活回复 | `(回复\|回復)\s*HP\s*N(?![\d.%])` | 无 | `L73` |
| 无敌时间 | `无敌一段时间（N秒）` | 无 | `L74` |
| 无敌时间 | `(一定时间内\|一段时间内)（N秒）…(无敌\|不受伤害)` | 无 | `L75` |
| 无敌时间 | `N秒内无敌` | 无 | `L76` |

其余是**文本侧规则**（不是参数含义）：`backed()`（`L32-37`，一个数字必须能被解包值/日文原文/原始参数解释，否则变「？」）、`collapse()`（`L40-62`，传授 a/b 二选一）、`scrub()`（`L80-157`）、`attack_interval()`（`L103-119`，基础间隔 ×(1+p6) 并截到 0.1 秒）、`fix_overheal()`（`L159-189`）。新版2 再加 `per_member / fill_variants / fill_atk / fix_tiers / norm_n` 五个函数（同样属措辞层）。

> 判断：`unpack_text.py` 的「知识」主要是**网站措辞模板**（CD／间隔／超上限／攻击间隔的写法），可复用性限于「把数字填回中文句子」，**不提供新的字段语义**。`NAMED` 8 条里真正与我方相关的只有 CD（type48 p5 / type23 p4）与随机攻击间隔（type116 p1）。

---

## 4. 来源追溯：是「新证据」还是「回收我方数据」（问题 4）

### 4.1 结论

**是回收**。三层证据，从弱到强：

**(a) 脚本注释与参数表字段自述【核实，原文可查】**

| 位置 | 原文 |
|---|---|
| `scripts/infer_params.py L40-41` | `# Rules taken from the other AI's bundle (cc_skill_values_20261021, template inference batches + the unpack project's per-record review of cid30236) where our own site statistics are weak, tied, or fooled by equal values.` |
| `scripts/infer_params.py L43` | `_REF_GPT = "cc_skill_values_20261021 模板推断"` |
| `scripts/infer_params.py L45/52` | 注释里直接拼进参数表：`参考：cc_skill_values_20261021 模板推断＋原项目 30236 逐条审定` |
| `scripts/infer_params.py L79` | `# param7/8/9 feed TimePowerUpData _attack/_move/_defense (cc_skill_values_20261022 §22/§26, disassembly)` |
| `scripts/infer_params.py L120` | `# (cc_skill_values_20261022 §23, ExecSA_PowerDrain)` |
| `param_table.json` 第 14289/18998/19797/21293/25356 行 | 5 条参考推断行的 `site_statistics` 里带 `cc_skill_values_20261021` / `原项目 30236` |
| `param_table.csv` 第 842/1119/1166/1254/1493 行 | 同上（CSV 行号） |

**(b) 代码里读的是我方交付的解包表【核实】** `CC_full_unpack_results_data_20261016` 出现 4 处：
- `scripts/build_cards.py L17`：`DECODED = DESK / "CC_full_unpack_results_data_20261016" / "master_data" / "decoded"`
- `scripts/build_cards.py L19`：`IMAGES = DESK / "CC_full_unpack_results_images_20261016" / "full_unpack" / "objects"`
- `scripts/leader_conditions.py L17`、`scripts/render_pages.py L281/L290`：同上 `decoded` 路径

**(c) 给 GPT 的包里物理包含了我方解包文件【核实，哈希级】**：
`其他人的参考/claude_cc_site_pages_给GPT_20261023/CC_full_unpack_results_data_20261016/master_data/decoded/leaderabilityinfo.data5.json.raw`
- 大小 83,980 B；SHA-256 `06dae31c74d91d95a5390c25a495910072e7abe2093ada98aab2d606bc2aa996`
- 与我方 `output/cache_full_20261015_v3/decoded/leaderabilityinfo.data5.json.raw` **字节完全相同**
- 该包根部的 `给GPT_请先读我.md L25` 也明写：`压缩包的结构和用户电脑上一致：claude_cc_site_pages/ 旁边有 site_diff/out/（网站措辞）和 CC_full_unpack_results_data_20261016/master_data/decoded/ 里的两个表（Leader 发动条件用）`

### 4.2 对方 HANDOFF 的 10-22 / 10-23 章节自述（原文摘录）

`HANDOFF.md L69`（10-22 章节开头）：
> **2026-10-22 Claude 接管后的合并**（参考 ChatGPT 成果包 `Desktop/cc/cc_skill_values_20261021/`；那份是逐行带证据等级的日文审计页面，不翻译、不对照网站，我们只吸收数据和规则）：

`HANDOFF.md L73`（同章节，量化声明）：
> 参考规则：`infer_params.py` 新增 `REFERENCE` 表（状态"参考推断"，`numbers.py` 的 `USABLE` 已包含它）。对方 30 条单字段规则中 28 条与我们的统计一致；新增 1017/1095/67 的 p2（移动速度）、1106 p0（Chain 获珠数）、2012 p4（暴击率）。

`HANDOFF.md L141-144`（10-22 晚，GPT 第二包）：
> **GPT 资料包 cc_skill_values_20261022 对照结果（2026-10-22）**：新增批 10–14（ability2003、1095、APK 扩域的 99/2003/2012/1095）。
> - 采纳：**ability99 p8 = 移动速度**（−x×100）。我们原来的解包确认规则把 p8 写成防御力，是错的：GPT 按反汇编确认 p7/p8/p9 → TimePowerUpData 的 _attack/_move/_defense，数据也吻合（11222 p8 −0.2 → 移动速度20%、221 −0.3 → 30%）。
> - 采纳：ability2003（SA_PowerDrain）p8 = 移动速度（与 99 同一数据路径；p7 攻击、p9 受伤量=防御力，我们已有）。
> - 1095 p5 = 暴击率（x100），**用户确认**（2026-10-23）…

`HANDOFF.md L147`（10-23 行为声明）：
> 纯解包页允许用统计推断/参考推断的规则改正网站数字，但只限"一个网站数字对一个解包值"的情况；凑剩余数字配对的改写仍只用解包确认规则；超上限只由标志位决定，不参与配对。对比页行为不变。

`给GPT_请先读我.md`（新版2，7488 B）`L41`（对 GPT 的指示，间接说明规则来源）：
> 4. 写进 `infer_params.py`（`REVIEWED` / `USER_CONFIRMED`）或 `numbers.py`，**注释里写明依据的卡号**；重跑 `infer_params.py` 和 `render_unpack.py`。

### 4.3 拆解：哪些是新信息，哪些是回收

| 成分 | 归属 | 说明 |
|---|---|---|
| 所有 param 原值 | **我方** | `build_cards.py` 只读 `CC_full_unpack_results_data_20261016/.../decoded`；`cards/*/data/card.json` 的 `raw` 就是我们的解包值 |
| 1637×… 的 hits / decisive 计数 | **对方新算，但被比对的是我方数值** | 网站数字是他们自己抓的（`site_diff/out/site_parsed.json`），比对对象是我们的参数值。计数量本身可复核（本轮核对 1673 行的 `hits/cards_with_value` 格式一致） |
| 5 条 `参考推断` 规则 | **我方** | `REFERENCE` 表注释自述来自 `cc_skill_values_20261021` / 原项目 30236 |
| 37 条 `解包确认` | **我方**（旧版即已有） | 旧分析已核 36/37 与我方一致、1 冲突；本轮冲突已修 |
| 4 条 `用户确认` | **用户口述**（第三来源） | 2026-10-22/23 用户直接告知，非代码、非网站 |
| 18 条 `REVIEWED` | 对方人工判读 | 依据是「逐卡看网站文本 + 卡号举例」，无代码证据 |
| 自称「GPT 反汇编」 | **不可复核** | 引用对象是 `cc_skill_values_20261022`，它本身是 `cc_skill_values_20261021`（我方包）的派生；这两个包**都不在本目录**，`§22/§23/§26` 的具体证据无从核对。本轮只能核到「其结论与我方 `ability99`/`ability2003` README 的 `_attack/_move/_defense` 映射一致」 |

**因此**：把它当「新证据」用会重复计算——它给的数值就是我们自己的数值；它能给我们的**只有网站对照这一层的量化结果**（见 §6）。

---

## 5. 与我方 10-17 旧结论逐项对照（问题 5）

旧结论出处：`output/reference_analysis/claude_cc_site_pages/README.md`（§4.2 冲突、§4.4 八条误配、§4.5 未覆盖）、`crosscheck_summary.json`（`冲突清单` 1 条）、`param_table_crosscheck.csv`（1610 行逐条结论）。

| # | 旧分析指出的问题 | 新版状态 | 判定 |
|---|---|---|---|
| 1 | **冲突**：`skilllist 99 param8` 对方＝防御力，我方＝移动（我方 param9 才是防御/受伤量） | 新版 `99 param8`＝**移动速度**（解包确认，hits 33/158，dec 14/19），`param9`＝防御力（统计推断，206/223，dec 200/218） | **已修正**（语义与我方完全一致） |
| 2 | 可升级：`skilllist 1095 param1` 统计推断 → 建议升解包确认 | 仍 **统计推断**（307/333，dec 304/330） | **未修正**（标签正确、等级未提） |
| 3 | 可升级：`skilllist 1095 param3` 同上 | 仍 **统计推断**（109/161，dec 107/159） | **未修正** |
| 4 | 可升级：`skilllist 99 param9` 同上 | 仍 **统计推断** | **未修正** |
| 5 | 误配：`skilllist 7 param0`＝地形编码被配成「攻击力 raw %」 | 仍 **弱证据 攻击力 raw %**（hits 27，dec 27/298） | **未修正**（等级低，不进填数） |
| 6 | 误配：`skilllist 1008 param0` 同上 | 仍 **弱证据 攻击力 raw %**（hits 11，dec 11/109） | **未修正** |
| 7 | 误配：`skilllist 99 param1/param2/param3`＝三种攻击类型触发阈值被配成「几率 ×100」 | `param1` 统计推断 几率（12/13，dec 2）、`param2` 待定 几率（10/11，dec 0）、`param3` **无行** | **未修正**（且 param3 仍缺行；`v==1` 跳过规则未改） |
| 8 | 误配：`bossskill 112 param7`（推力）被配成「伤害倍」 | 仍 **弱证据 伤害 raw 倍**（5/102，dec 0） | **未修正** |
| 9 | 误配：`bossskill 112 param8`（九位置掩码）为「未知」 | 仍 **未知**（0/102） | **未修正** |
| 10 | 未覆盖：`skilllist 2012 param0/param4/param5` 完全无行 | 新增 9 行：`param0` 持续时间 662/696（dec 338）、`param4` 暴击率 参考推断 106/491、`param5` 暴击威力 464/500（dec 5） | **已补行**，且 `param0`/`param5` 与我方代码结论方向一致；但 **`param7`/`param8` 新打上「伤害倍」与我方冲突**（见 #14） |
| 11 | 未覆盖：`bossskill 112 param0`(fireType)、`param9`(清理跳过) | 仍无行 | **未覆盖** |
| 12 | 未覆盖：`skilllist 1017 param0`(自身可否接受) 与 `iParam0`(职业位图) | 仍无行（只出 paramN，`iParam` 字段不进表） | **未覆盖** |
| 13 | 未覆盖：`skilllist 2003`（我方已确认） | 新增 8 行：`param0` 501/546、`param7` 483/509、`param9` 511/537、`param8` 28/442 | **已补行**，`p0/p7/p8/p9` 与我方一致 ✔ |
| 14 | —（新增） | `skilllist 2012 param7`＝「伤害 raw 倍」弱证据（62/527，dec 34）；`param8`＝「伤害 raw 倍」（3/696） | **新引入矛盾**：我方 `ability2012/README.md L13` 明确 param7＝应用数量上限、param8＝TARGET_TYPE（31=pGROUP_ALL、64=MYSELF） |
| 15 | —（新增） | `skilllist 2003 param5`＝攻击力（待定）、`param6`＝攻击力（待定） | **新引入矛盾**：我方 `ability2003/README.md L15/L20` 明确 p4/p5/p6＝攻者自身 `_attack/_move/_defense` |
| 16 | 旧分析 §6.3 指出文档内部矛盾：HANDOFF 写「p9 移动速度」vs 表里「p9 防御力」 | `HANDOFF.md L92` **仍写**：`type99（攻击时减益）：p0 秒，p7/p8 攻击/防御 −x×100%，p9 移动速度。` —— 与同文件 `L142`、与 param_table 都相反 | **仍未修正**（文档自相矛盾） |

**汇总**：旧分析点名的 9 项（1 冲突 + 8 误配）中 **已修正 1 项（94/99 冲突），未修正 8 项**；4 项「未覆盖」中 **2 项已补行（2012、2003）、2 项仍未覆盖（112 param0/param9、1017 param0/iParam0）**；**新引入 2 处矛盾**（2012 p7/p8、2003 p5/p6）。

---

## 6. 可直接用于我方字段解释的候选清单（问题 6）

### 6.0 先说「不能怎么用」

- **统计推断 / 弱证据 / 待定 / 未知 一律不能标成「可确认」**。本清单里标「候选，需我方验证」的行，最多只能进我方「待验证候选池」。
- **参考推断 5 条全部回收自我方**（§4），除 `1095 param2` 外不构成新增信息。
- `2012 param7/param8`、`2003 param5/param6` 与我方代码证据冲突，**明确不要采用**。

### 6.1 直接可用（确认级，共 4 条，其中 2 条我方已有）

| 行 | 语义 | 换算 | 依据 | 对我方价值 |
|---|---|---|---|---|
| `skilllist 99 param8` | 目标 _move | −x×100 % | 解包确认；本轮改判（旧为防御力） | **我方已有**（`ability99/README.md L28` 单样本、`ability2003` 受控检查确认同槽）→ 作对方已对齐的旁证 |
| `skilllist 1095 param5` | 暴击率加算 | x100 % | 用户确认（2026-10-23）；站点 10/221 命中 | 语义我方已有（`ability1095/README.md L25`）；**新增信息是「网站多数多写 10%」这一句**，可解释我方与网站的差异 |
| `skilllist 58 param0` | 无敌时间 1 秒 | raw 秒 | 用户确认（2026-10-22）；p0 恒为 1，无站点统计 | **我方未覆盖 guts(type58)**。可用，但来源是用户口述，建议先向用户复核一次 |
| `bossskill/charainfo 116 param1` | 随机攻击间隔 | raw 秒 | 用户确认（2026-10-23）；p1<1 时网站写「1秒」是惯用写法 | **我方未覆盖随机攻击(type116)**。同上，属用户口述级 |

### 6.2 候选清单（≤40 条，按 证据等级 × 我方是否未覆盖 × 决定性样本数 排序）

候选池＝63 条新增 + 33 条改判中 `status` 属四档可用级或 `decisive≥20` 的行，共 **{{POOL_N}}** 条；下表为前 40。`我方是否已覆盖该类型` 按我方 `output/ordinary_effects`、`output/boss_chain`、`output/boss_heal` 的类型清单判定（skilllist 7/99/1008/1017/1095/2003/2012/3000；bossskill 13/27/105/112）。

{{CANDIDATE_TABLE}}

> 读表注意：本排序里「我方已覆盖该类型」是**降权项**，所以 `skilllist 2012 param0`（662/696，dec 338/355）、`skilllist 2003 param0`（501/546，dec 179/197）这类决定性很高、但我方早已确认的行会被排到 39–40 位。**它们不是没用，而是用途不同**——不是「候选新语义」，是「我方结论的网站侧旁证」，见 §6.3 第 4、5 条与 §6.4 全表。

### 6.3 最值得优先验证的 6 条（人工排序，理由）

1. **`skilllist 1095 param2` ＝ 移动速度 (x-1)x100**（参考推断。要注意该行 `hits` 只有 5/165，原因是参考规则**覆盖**了统计最优标签后把 hits 换成了参考标签的命中数，不代表「实测支持弱」；我方 `ability1095/README.md L24` 已用反汇编确认「移动因子×param2，乘算，407 条」）。**唯一一条双方独立到达同一结论的行**，可直接把我方结论升级为「代码 + 交叉来源」双证。
2. **`skilllist 1017 param2` ＝ 移动速度 (x-1)x100**（参考推断，160/485＝33%，但 dec 155/357＝43%，dec 数很硬）。我方 `ability1017/README.md L20` 至今把 `param2` 记为「未知」——**这是本轮最实的一条新增候选**，值得用我方反汇编复核（1017 与 1095 同族布局，1095 的 p2 已是移动，可作先验）。
3. **`skilllist 1104 param0–param5`（新版2 才有）**：「按人数叠加」整套布局（人数上限/攻击/移动/防御/暴击率/暴击威力，单位 `n%`）。我方完全无此类型证据，但布局自洽、有卡号级例证（1303 `0.03/0.03/0.02 → 15%、3n%`）。
4. **`skilllist 2012 param0 / param5` 的网站命中率**（662/696、464/500）：不是新语义（我方已确认），但**是我方结论的第一份网站侧量化旁证**，可直接写进我方 README 的证据行。
5. **`skilllist 2003 param0/p7/p9` 的网站命中率**（501/546、483/509、511/537）：同上，为我方 `ability2003` 补网站侧一致性。
6. **`skilllist 67 param2` ＝ 移动速度**（参考推断，170/344，dec 137/282 —— **统计本身也强**）。我方 type67 未覆盖；这条同时有「我方模板推断」与「对方统计」两路支持，是参考推断里证据最干净的一条。

### 6.4 我方已确认语义 ↔ 对方表（含网站命中率，可直接引用的旁证库）

{{OURS_TABLE}}

读法说明：`网站命中/出现` 是「该标签的换算值出现在网站数字里的次数 / 该槽位有值的卡数」。命中率低不一定说明我方错，可能是网站措辞不写这个数（例：`bossskill 13 param6` 移动速度 157/1327＝12%，因为 type13 的移动速度网站大多不写；`1095 param5` 10/221＝4.5%，因为网站多写了 +10% 基础暴击，正是用户确认要纠正的那一点）。

---

## 7. 不确定与局限（不要把这些当结论）

1. **未重跑对方管线**：`site_diff/out/site_parsed.json`（4.9 MB）虽在给 GPT 的包内、新版1 目录里没有；本轮所有 `hits/decisive` 都是**直接读对方 `param_table.json` 的字段**，没有独立重算。若对方统计口径有 bug（旧分析已指出 `v==1` 跳过、`opp_u<3` 逃生口），本轮无法发现。
2. **`更新：2026-10-17` 的标题是过期的**：`HANDOFF.md L3` 写「更新：2026-10-17」，但正文有 10-22/10-23 章节（`L69`、`L141`）。引用其日期时要按章节而不是文件头。
3. **自称的「GPT 反汇编」不可复核**：`cc_skill_values_20261021/20261022` 都不在本目录，`§22/§23/§26` 无从对照。本轮只能验到「结论与我方 `ability99`/`ability2003` 的 `_attack/_move/_defense` 映射一致」。
4. **`charainfo` 12 行是镜像推断**（`L143-145`），对方未独立验证；主表 `bossskill` 侧的数值抽样一致（旧分析已核）。
5. **「SA 类型段 2000–2020」是推断**：本轮只核实到 `2003`＝SA_PowerDrain、`2012`＝SA_SupportTarget（对方注释 + 我方 README 双向确认），其余 2000/2001/2002/2004…2020 的语义**未核实**。
6. **新版2 与新版1 的取舍**：本 REPORT 的逐行数字基于新版1 的 `param_table.json`（1673 行）。新版2 有 7 行更新（§2.3）。若下游要引用「最新」，需按 §2.3 覆盖那 7 行。
7. **`1095 param5` 用户确认的普适性未知**：只覆核到「网站 114 张多写 10%」这一半；「能力的暴击率不含基础暴击率」是用户口述，我方 `ability1095` 代码证据支持「直接加算、不套 1.5 基准」，但**未核到基础暴击是否另计**。

---

## 8. 复现与产物

产物目录 `work/refcheck_20261023_lead/params/`：

| 文件 | 内容 |
|---|---|
| `REPORT.md` | 本报告 |
| `param_rows_new1673.json` | 新版全部 1673 行规范化（15 原字段 + `evidence_grade` / `status_group` / `prev_1017`），按证据等级→决定性排序 |
| `new_rows_since_1017.json` | `added`（63）、`changed`（33，带 `changed_fields`）、`recount_only`（107）、`removed`（0） |
| `candidate_list_40.json` | 候选池 {{POOL_N}} 条，前 40 条 + `rest` |
| `knowledge_tables.json` | 四个知识表（CONFIRMED/USER_CONFIRMED/REVIEWED/REFERENCE）+ `unpack_text.NAMED` + `numbers.CONV/USABLE`，含源文件行号 |
| `vs_1017.json` | 旧 1610 行逐条核对结论 ↔ 新版行 |
| `_stats.json` | 分布统计 |

脚本 `scripts/refcheck_20261023_lead/`（全部只读，不写 `其他人的参考`）：

```
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_diff.py          # 1673 vs 1610 逐行比对
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_knowledge.py     # 知识表提取（import 对方模块）
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_knowledge_new2.py
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_new1_vs_new2.py  # 两个 2026-10-23 目录差异
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_vs_1017.py       # 与 10-17 核对结论对照
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_candidates.py    # 候选清单
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_ours_sitecheck.py
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_summary.py       # 分布统计
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_aggregates.py    # 汇总数
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_rows.py skilllist 7 99 1095   # 按类型打印行
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_show.py skilllist:1017:param2 # 打印单行全字段
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_dump.py          # 新增/改判行紧凑打印
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_report.py        # 由模板生成本报告
.venv\Scripts\python.exe -B scripts\refcheck_20261023_lead\params_check_md.py      # 校验本报告表格列数
```

（本轮跑完 `params_check_md.py` 结果：22 张表、列数不符 0 行。）

核对基线（我方，只读引用）：`output/reference_analysis/claude_cc_site_pages/{README.md,param_table_crosscheck.csv,crosscheck_summary.json}`、`output/ordinary_effects/ability{7,99,1008,1017,1095,2003,2012,3000}/README.md`、`output/boss_heal/constants.json`。
