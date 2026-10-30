# -*- coding: utf-8 -*-
"""S5 非地形段（type28 击杀マナ確率）推断模块。

范围（``docs/tasks/20261026-s5-nonterrain-batch.md`` §1；
预检 ``output/character_skills/inference_inventory/chain_precheck_20261026/precheck_report.md`` §8；
前审计 ``output/character_skills/inference_inventory/mana_b_audit_20261026/`` §3.3）
----------------------------------------------------------------------------
S5 = ``gain_chance`` 且 ``verdict=ready_with_limits`` 且句面不含地形/战场条件：
**172 行 / 189 项**（P1 9 项；Y.G. 6 行 / 9 项；审计数与预检数逐数一致）。
值源 = ``skilllist`` ability 28 的 ``param0/param1/param2``：

* ``damageType 0/2/1`` 分别读取 ``param0/param1/param2`` 的基础阈值
  （规则键 ``skilllist|28|/param0,/param1,/param2``，rules.json 现状 6 键中的三键）；
* 判定式 ``Random.Range(0,1) ≤ 基础阈值（＋地形附加）`` 时进入玛那生成分支；
* 地形附加：damageType2 取 ``param4``、type0/1 取 ``param5``，掩码 ``1<<param6``；
* ``param3``／``param9`` 语义未登记 → 只登记原值并写未知注记，不解释。

证据档（主持三裁决）
---------------------
1. 原文只写「一定確率」时允许出示字段概率阈值（param0/1/2）；
   **单来源（occurrences=1）、类型级外推、不升确认**，答案 ``numeric_evidence=推断``、
   ``answer_status=INFERRED_SINGLE_SOURCE``、``evidence_scope=BY_TYPE_EXTRAPOLATED``；
   规则证据层为 **CACHE**（记录 43023602 的受控原生检查），逐行同时披露本行载体层。
2. ``param6≠4`` 只写掩码位 ``1<<param6``，**不写地形名**；本段 26 行带地形附加
   （其中 param6=4 仅 30236，已按零触碰拒答）。
3. ``param3``／``param9`` 语义未知 → 就地未知注记，不填零、不按参数对称性补解释。

逐行门控（拒绝即不出该行；原因码落盘可数）
--------------------------------------------
G1  句式：必须有「マナを獲得」概率主张（一定確率／必ず／獲得しやすくなる）；
    无概率主张 → NOT_S5_CLAIM。
G2  时机：概率主张必须绑定击杀触发（倒す／倒した／止めを刺す…）。本行无触发时，
    只允许「さらに／また」接续片段从父记录前文最后一句继承触发；仍无 →
    TIMING_MISMATCH。非击杀触发（地形/戦闘時/使用時…）→ TIMING_MISMATCH。
G3  载体串：own → sub（1082 转发）→ 容器 skill_ids / abi0/abi1；断裂 →
    CARRIER_CHAIN_BROKEN；无 ability28 → NO_TYPE28_CARRIER。
G4  multi-carrier：同一行链上 ≥2 条不同的 ability28 记录且无逐伤害类型唯一归属 →
    MULTI_CARRIER_AMBIGUOUS（不求和、不取最大，审计「多来源叠加未模拟」）。
G5  零触碰：30236/30239 → ZERO_TOUCH_CID（30236 本段已有基线答案，不覆盖）。
G6  表边界：charainfo/denju 等展示复制行需记录级等价门 → 本批 fail-closed
    （CHARAINFO_EQUIVALENCE_FAIL_CLOSED）；仅 skilllist / extra_ability_info。
G7  职业/条件位图：击杀子句点名的职业集合 ↔ ``iParam0`` 位图必须逐一相等；
    不点名职业时 ``iParam0`` 只登记原值（0/31/null，不赋义）。
G8  同值时机不符：句面点名伤害类型 ↔ 槽位必须一致且该槽 >0（一定確率/相对句），
    「必ず」句点名槽必须精确 ==1.0；不符 → VALUE_TRIGGER_MISMATCH。
    句面点名的伤害类型槽缺失（null）→ SLOT_MISSING（不填零）。
G9  数值域：阈值必须 0..1；越界 → PROBABILITY_OUT_OF_RANGE。
G10 无既有答案：同 rule_key＋record_id＋field_path 已存在 → ALREADY_ANSWERED（不改旧值）。
G11 单来源不外推：只在 ADMITTED_ROWS（审计 172 行重筛集）内写入；
    非本段行不消费（apply_to_groups 直接跳过）。

答案粒度：一句「一定確率」＝一条概率主张。每个通过行输出 **1 条答案**，答案内
``binding.fields`` 列出 param0/param1/param2 三档原值；``field_path`` 取
param0→param1→param2 的首个存在槽（缺失槽不填零，只写未知注记）。

2026-10-29 批1 增量（``docs/tasks/20261029-kill-mana-batch.md``）
---------------------------------------------------------------
1. **8297 f3**「敵を倒した時、一定確率でマナを獲得する。」→ 绝对出数 1 行（1 答案 3 槽），
   载体 APK ``/skilllist/7179`` skillid 30829702 ability28（p0=p1=0.10000000149011612、
   p2=0.15000000596046448）。该记录**在 rules 声明样本域外**（conditions 明写仅普通
   43023602），故答案标 ``evidence_scope=BY_TYPE_EXTRAPOLATED``、``association=推断``，
   并在 conditions/note/unknowns/binding.rule_domain 逐处披露域外；**只对该记录追加文案**，
   既有 170 条 S5 答案文本逐字节不变。
2. **相对句 90 行**（预检 89 行＋8297 f4）「…で倒すと獲得しやすくなる。」→ **行级归位**：
   不新增唯一数值；写入值必须与同技能基础行答案文本中**同名伤害类型百分比逐位相等**
   （同一 ``_pct`` 格式），构建期逐行核验，不符即拒答（BASE_ROW_ANSWER_MISSING）。
   句面点名槽必须有限且 >0；同层 sub 链 ability28 必须恰 1 条（多载体拒答）；范围外
   （NO_CARRIER 17 行、20234 跨层、50 行未证触发路径、1038/12004 另列）一律不消费。
   相对句**不写增幅**：记录无相对幅度槽，f4 亦只对应必殺技槽（param2）阈值。
3. 相对段在绝对段之后执行（8297 f4 的基准行 f3 在同批出数）。
"""
from __future__ import annotations

import copy
import json
import math
import re

import card_page_inference_mana_b as MB

MODULE_VERSION = "s5_kill_mana_20261029"
SCOPE = "S5_NONTERRAIN_20261026"
ADMITTED_TABLES = ("skilllist", "extra_ability_info")
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

# 审计 172 行（非地形段）重筛集；只限定写入范围，evaluate 保持通用供重筛/探针使用。
ADMITTED_ROWS = frozenset({
    '10027-ability-ability-skillid_1_-lvorder0-f2', '10037-ability-ability-skillid_2_-lvorder1-f1', '10200-ability-ability-skillid_1_-lvorder0-f2', '10201-ability-ability-skillid_1_-lvorder0-f0',
    '10210-ability-ability-skillid_1_-lvorder0-f2', '1034-ability-ability-skillid_2_-lvorder1-f1', '105-ability-ability-skillid_2_-lvorder1-f2', '108-ability-ability-skillid_1_-lvorder0-f2',
    '11002-ability-ability-skillid_1_-lvorder0-f1', '11219-ability-ability-skillid_1_-lvorder0-f2', '11222-ability-ability-skillid_2_-lvorder1-f4', '1201-ability-ability-skillid_2_-lvorder1-f2',
    '1219-ability-ability-skillid_1_-lvorder0-f1', '12231-ability-ability-skillid_2_-lvorder1-f2', '12236-ability-ability-skillid_1_-lvorder0-f5', '12237-ability-ability-skillid_1_-lvorder0-f2',
    '1242-ability-ability-skillid_2_-lvorder1-f5', '1247-ability-ability-skillid_1_-lvorder0-f1', '1251-ability-ability-skillid_1_-lvorder0-f1', '1283-ability-ability-skillid_2_-lvorder1-f3',
    '1290-ability-ability-skillid_2_-lvorder1-f3', '1298-ability-ability-skillid_1_-lvorder0-f2', '13006-ability-ability-skillid_2_-lvorder1-f0', '13008-ability-ability-skillid_1_-lvorder0-f0',
    '13021-ability-ability-skillid_1_-lvorder0-f2', '13204-ability-ability-skillid_1_-lvorder0-f2', '13213-ability-ability-skillid_1_-lvorder0-f4', '13219-ability-ability-skillid_2_-lvorder1-f3',
    '13220-ability-ability-skillid_2_-lvorder1-f2', '20104-ability-ability-skillid_1_-lvorder0-f3', '20108-ability-ability-skillid_2_-lvorder1-f0', '20121-ability-ability-skillid_1_-lvorder0-f3',
    '20124-ability-ability-skillid_1_-lvorder0-f3', '2021-ability-ability-skillid_1_-lvorder0-f1', '20210-ability-ability-skillid_2_-lvorder1-f0', '20216-ability-ability-skillid_1_-lvorder0-f4',
    '20234-ability-ability-skillid_2_-lvorder1-f3', '20236-ability-ability-skillid_1_-lvorder0-f2', '203-ability-ability-skillid_2_-lvorder1-f4', '20302-extra-extra-extra_abilities_0_-lv1-f0',
    '20302-extra-extra-extra_abilities_1_-lv2-f0', '20302-extra-extra-extra_abilities_2_-lv3-f0', '20302-extra-extra-extra_abilities_3_-lv4-f0', '20302-extra-extra-extra_abilities_4_-lvMAX-f0',
    '20324-ability-ability-skillid_1_-lvorder0-f4', '20325-ability-ability-skillid_2_-lvorder1-f3', '20328-ability-ability-skillid_1_-lvorder0-f4', '20414-ability-ability-skillid_1_-lvorder0-f6',
    '20437-crossworld-crossworld-crossworld_ability_info__id_20437__ability0-lvorder0-f0', '20503-ability-ability-skillid_2_-lvorder1-f7', '20508-ability-ability-skillid_2_-lvorder1-f6', '20523-ability-ability-skillid_2_-lvorder1-f3',
    '20602-ability-ability-skillid_2_-lvorder1-f4', '20604-ability-ability-skillid_2_-lvorder1-f4', '20612-ability-ability-skillid_1_-lvorder0-f3', '20620-ability-ability-skillid_1_-lvorder0-f3',
    '20636-ability-ability-skillid_1_-lvorder0-f5', '20638-ability-ability-skillid_1_-lvorder0-f4', '20644-ability-ability-skillid_1_-lvorder0-f1', '2068-ability-ability-skillid_1_-lvorder0-f1',
    '20701-ability-ability-skillid_1_-lvorder0-f4', '20702-ability-ability-skillid_1_-lvorder0-f3', '20706-ability-ability-skillid_1_-lvorder0-f3', '20801-ability-ability-skillid_1_-lvorder0-f5',
    '20806-ability-ability-skillid_1_-lvorder0-f4', '20828-ability-ability-skillid_1_-lvorder0-f3', '20903-ability-ability-skillid_2_-lvorder1-f4', '2229-ability-ability-skillid_2_-lvorder1-f2',
    '224-ability-ability-skillid_1_-lvorder0-f2', '227-ability-ability-skillid_1_-lvorder0-f1', '2305-ability-ability-skillid_2_-lvorder1-f2', '2307-ability-ability-skillid_2_-lvorder1-f0',
    '2308-ability-ability-skillid_1_-lvorder0-f1', '2312-ability-ability-skillid_1_-lvorder0-f3', '2320-ability-ability-skillid_1_-lvorder0-f4', '245-ability-ability-skillid_2_-lvorder1-f2',
    '253-ability-ability-skillid_2_-lvorder1-f3', '263-ability-ability-skillid_1_-lvorder0-f4', '300-ability-ability-skillid_1_-lvorder0-f3', '3013-ability-ability-skillid_2_-lvorder1-f2',
    '30236-ability-ability-skillid_1_-lvorder0-f3', '30242-ability-ability-skillid_1_-lvorder0-f1', '30249-ability-ability-skillid_2_-lvorder1-f3', '30249-ability-ability-skillid_2_-lvorder1-f4',
    '30306-ability-ability-skillid_1_-lvorder0-f1', '3031-ability-ability-skillid_1_-lvorder0-f1', '3031-ability-ability-skillid_1_-lvorder0-f2', '30312-ability-ability-skillid_1_-lvorder0-f3',
    '320-ability-ability-skillid_2_-lvorder1-f2', '3225-ability-ability-skillid_2_-lvorder1-f3', '3228-ability-ability-skillid_2_-lvorder1-f3', '3236-ability-ability-skillid_2_-lvorder1-f3',
    '326-ability-ability-skillid_1_-lvorder0-f4', '344-ability-ability-skillid_1_-lvorder0-f1', '4006-ability-ability-skillid_1_-lvorder0-f0', '4208-ability-ability-skillid_2_-lvorder1-f2',
    '4210-ability-ability-skillid_1_-lvorder0-f2', '4224-ability-ability-skillid_2_-lvorder1-f2', '4311-ability-ability-skillid_2_-lvorder1-f5', '4313-ability-ability-skillid_1_-lvorder0-f2',
    '44-ability-ability-skillid_2_-lvorder1-f1', '44-ability-ability-skillid_2_-lvorder1-f2', '5048-ability-ability-skillid_2_-lvorder1-f1', '5067-ability-ability-skillid_1_-lvorder0-f2',
    '5067-ability-ability-skillid_1_-lvorder0-f3', '5234-ability-ability-skillid_1_-lvorder0-f0', '5286-ability-ability-skillid_2_-lvorder1-f2', '5300-ability-ability-skillid_1_-lvorder0-f2',
    '5303-ability-ability-skillid_1_-lvorder0-f6', '5305-ability-ability-skillid_1_-lvorder0-f3', '6003-ability-ability-skillid_1_-lvorder0-f2', '6007-ability-ability-skillid_1_-lvorder0-f2',
    '6030-ability-ability-skillid_2_-lvorder1-f1', '6228-ability-ability-skillid_2_-lvorder1-f1', '6246-ability-ability-skillid_2_-lvorder1-f1', '6280-ability-ability-skillid_1_-lvorder0-f1',
    '6294-ability-ability-skillid_1_-lvorder0-f2', '6302-ability-ability-skillid_2_-lvorder1-f1', '6303-ability-ability-skillid_1_-lvorder0-f2', '6308-ability-ability-skillid_1_-lvorder0-f1',
    '6310-ability-ability-skillid_2_-lvorder1-f2', '6318-ability-ability-skillid_1_-lvorder0-f3', '6319-ability-ability-skillid_2_-lvorder1-f1', '6323-ability-ability-skillid_2_-lvorder1-f2',
    '6325-ability-ability-skillid_2_-lvorder1-f2', '6334-ability-ability-skillid_1_-lvorder0-f3', '7023-ability-ability-skillid_2_-lvorder1-f1', '7023-ability-ability-skillid_2_-lvorder1-f2',
    '7075-ability-ability-skillid_2_-lvorder1-f1', '7218-ability-ability-skillid_2_-lvorder1-f1', '7228-ability-ability-skillid_2_-lvorder1-f1', '7240-ability-ability-skillid_1_-lvorder0-f1',
    '7243-ability-ability-skillid_2_-lvorder1-f3', '7248-ability-ability-skillid_2_-lvorder1-f4', '7521-ability-ability-skillid_1_-lvorder0-f1', '7527-ability-ability-skillid_2_-lvorder1-f2',
    '7580-ability-ability-skillid_1_-lvorder0-f2', '7613-ability-ability-skillid_2_-lvorder1-f4', '7630-ability-ability-skillid_2_-lvorder1-f2', '7661-ability-ability-skillid_2_-lvorder1-f0',
    '7682-ability-ability-skillid_2_-lvorder1-f3', '8039-ability-ability-skillid_2_-lvorder1-f1', '8056-ability-ability-skillid_1_-lvorder0-f2', '8056-ability-ability-skillid_1_-lvorder0-f3',
    '8073-ability-ability-skillid_2_-lvorder1-f1', '8085-ability-ability-skillid_1_-lvorder0-f1', '8099-ability-ability-skillid_2_-lvorder1-f0', '8129-ability-ability-skillid_2_-lvorder1-f2',
    '8161-ability-ability-skillid_2_-lvorder1-f1', '8207-ability-ability-skillid_1_-lvorder0-f1', '8215-ability-ability-skillid_1_-lvorder0-f1', '8236-ability-ability-skillid_2_-lvorder1-f0',
    '8250-ability-ability-skillid_1_-lvorder0-f3', '8258-ability-ability-skillid_2_-lvorder1-f1', '8297-ability-ability-skillid_1_-lvorder0-f3', '8316-ability-ability-skillid_1_-lvorder0-f1', '8327-ability-ability-skillid_2_-lvorder1-f0',
    '8335-ability-ability-skillid_2_-lvorder1-f2', '8344-ability-ability-skillid_2_-lvorder1-f0', '8348-ability-ability-skillid_2_-lvorder1-f2', '8352-ability-ability-skillid_2_-lvorder1-f3',
    '8356-ability-ability-skillid_2_-lvorder1-f0', '8369-ability-ability-skillid_2_-lvorder1-f2', '8375-ability-ability-skillid_2_-lvorder1-f2', '8381-ability-ability-skillid_2_-lvorder1-f2',
    '8385-ability-ability-skillid_2_-lvorder1-f3', '8393-ability-ability-skillid_2_-lvorder1-f2', '8400-ability-ability-skillid_1_-lvorder0-f4', '8406-ability-ability-skillid_2_-lvorder1-f2',
    '8412-ability-ability-skillid_1_-lvorder0-f4', '8422-ability-ability-skillid_1_-lvorder0-f2', '9036-ability-ability-skillid_2_-lvorder1-f0', '9229-ability-ability-skillid_2_-lvorder1-f2',
})

# ---------------------------------------------------------------------------
# 相对概率句（2026-10-29 批1，``docs/tasks/20261029-kill-mana-batch.md``）
# ---------------------------------------------------------------------------
# 「必殺技で倒すと獲得しやすくなる。」式**相对表述行**：本行不给新数值，只把同技能基础行
# 已经披露的同一伤害类型阈值做行级归位。范围＝预检 89 行（79 卡）＋ 8297 f4（其基础行
# 8297 f3 在同批由绝对段出数）。范围外任何相对句不消费（NO_RELATIVE_SCOPE）。
RELATIVE_ADMITTED_ROWS = frozenset({
    '203-ability-ability-skillid_2_-lvorder1-f5', '224-ability-ability-skillid_1_-lvorder0-f3',
    '245-ability-ability-skillid_2_-lvorder1-f3', '263-ability-ability-skillid_1_-lvorder0-f5',
    '300-ability-ability-skillid_1_-lvorder0-f4', '320-ability-ability-skillid_2_-lvorder1-f3',
    '1201-ability-ability-skillid_2_-lvorder1-f3', '1242-ability-ability-skillid_2_-lvorder1-f6',
    '1283-ability-ability-skillid_2_-lvorder1-f4', '1298-ability-ability-skillid_1_-lvorder0-f3',
    '2229-ability-ability-skillid_2_-lvorder1-f3', '2305-ability-ability-skillid_2_-lvorder1-f3',
    '2307-ability-ability-skillid_2_-lvorder1-f1', '2308-ability-ability-skillid_1_-lvorder0-f2',
    '2312-ability-ability-skillid_1_-lvorder0-f4', '2320-ability-ability-skillid_1_-lvorder0-f5',
    '3236-ability-ability-skillid_2_-lvorder1-f4', '4210-ability-ability-skillid_1_-lvorder0-f3',
    '4224-ability-ability-skillid_2_-lvorder1-f3', '4311-ability-ability-skillid_2_-lvorder1-f6',
    '4313-ability-ability-skillid_1_-lvorder0-f3', '5234-ability-ability-skillid_1_-lvorder0-f1',
    '5286-ability-ability-skillid_2_-lvorder1-f3', '5303-ability-ability-skillid_1_-lvorder0-f7',
    '5305-ability-ability-skillid_1_-lvorder0-f4', '6303-ability-ability-skillid_1_-lvorder0-f3',
    '6308-ability-ability-skillid_1_-lvorder0-f2', '6318-ability-ability-skillid_1_-lvorder0-f4',
    '6319-ability-ability-skillid_2_-lvorder1-f2', '6323-ability-ability-skillid_2_-lvorder1-f3',
    '6325-ability-ability-skillid_2_-lvorder1-f3', '6325-ability-ability-skillid_2_-lvorder1-f4',
    '7218-ability-ability-skillid_2_-lvorder1-f2', '7218-ability-ability-skillid_2_-lvorder1-f3',
    '7613-ability-ability-skillid_2_-lvorder1-f5', '7661-ability-ability-skillid_2_-lvorder1-f1',
    '7682-ability-ability-skillid_2_-lvorder1-f4', '8161-ability-ability-skillid_2_-lvorder1-f2',
    '8297-ability-ability-skillid_1_-lvorder0-f4', '8316-ability-ability-skillid_1_-lvorder0-f2',
    '8327-ability-ability-skillid_2_-lvorder1-f1', '8335-ability-ability-skillid_2_-lvorder1-f3',
    '8348-ability-ability-skillid_2_-lvorder1-f3', '8352-ability-ability-skillid_2_-lvorder1-f4',
    '8356-ability-ability-skillid_2_-lvorder1-f1', '8369-ability-ability-skillid_2_-lvorder1-f3',
    '8385-ability-ability-skillid_2_-lvorder1-f4', '8393-ability-ability-skillid_2_-lvorder1-f3',
    '8393-ability-ability-skillid_2_-lvorder1-f4', '8400-ability-ability-skillid_1_-lvorder0-f5',
    '8400-ability-ability-skillid_1_-lvorder0-f6', '8406-ability-ability-skillid_2_-lvorder1-f3',
    '8412-ability-ability-skillid_1_-lvorder0-f5', '8422-ability-ability-skillid_1_-lvorder0-f3',
    '10201-ability-ability-skillid_1_-lvorder0-f1', '10210-ability-ability-skillid_1_-lvorder0-f3',
    '11219-ability-ability-skillid_1_-lvorder0-f3', '11222-ability-ability-skillid_2_-lvorder1-f5',
    '13006-ability-ability-skillid_2_-lvorder1-f1', '13204-ability-ability-skillid_1_-lvorder0-f3',
    '13220-ability-ability-skillid_2_-lvorder1-f3', '20104-ability-ability-skillid_1_-lvorder0-f4',
    '20108-ability-ability-skillid_2_-lvorder1-f1', '20121-ability-ability-skillid_1_-lvorder0-f4',
    '20124-ability-ability-skillid_1_-lvorder0-f4', '20210-ability-ability-skillid_2_-lvorder1-f1',
    '20216-ability-ability-skillid_1_-lvorder0-f5', '20216-ability-ability-skillid_1_-lvorder0-f6',
    '20325-ability-ability-skillid_2_-lvorder1-f4', '20328-ability-ability-skillid_1_-lvorder0-f5',
    '20414-ability-ability-skillid_1_-lvorder0-f7',
    '20437-crossworld-crossworld-crossworld_ability_info__id_20437__ability0-lvorder0-f1',
    '20437-crossworld-crossworld-crossworld_ability_info__id_20437__ability0-lvorder0-f2',
    '20503-ability-ability-skillid_2_-lvorder1-f8', '20508-ability-ability-skillid_2_-lvorder1-f7',
    '20602-ability-ability-skillid_2_-lvorder1-f5', '20602-ability-ability-skillid_2_-lvorder1-f6',
    '20620-ability-ability-skillid_1_-lvorder0-f4', '20636-ability-ability-skillid_1_-lvorder0-f6',
    '20636-ability-ability-skillid_1_-lvorder0-f7', '20638-ability-ability-skillid_1_-lvorder0-f5',
    '20701-ability-ability-skillid_1_-lvorder0-f5', '20701-ability-ability-skillid_1_-lvorder0-f6',
    '20702-ability-ability-skillid_1_-lvorder0-f4', '20806-ability-ability-skillid_1_-lvorder0-f5',
    '20828-ability-ability-skillid_1_-lvorder0-f4', '20903-ability-ability-skillid_2_-lvorder1-f5',
    '20903-ability-ability-skillid_2_-lvorder1-f6', '30306-ability-ability-skillid_1_-lvorder0-f2',
    '30312-ability-ability-skillid_1_-lvorder0-f4',
})

# 相对句的触发词（严格形态：本批只收「獲得しやすくなる」相对表述；句面含「マナ」的既有
# 绝对/地形路径不进入本路径，避免与既有 S5 行为重叠）。
RELATIVE_RX_STRICT = re.compile(r"獲得しやすくな|獲得しやすく|なりやすく")
BASEROW_RULE_KEY = "skilllist|28|/param0"

# 规则样本域外：rules.json 三个 type28 基础键的 conditions 明写「仅普通43023602 /ability28
# 的 subManaHunter」；82829702 之外的记录一律按类型级外推登记。本批只有 30829702（8297 f3）
# 需要显式域外披露，且**只对该记录**追加文案，不改已交付的 170 条既有 S5 答案文本。
OUT_OF_DOMAIN_RECORDS = frozenset({30829702})
DOMAIN_OUTSIDE_TEXT = (
    "规则域外披露：rules.json「skilllist|28|/param0,1,2」的 conditions 明写样本域为"
    "「仅普通43023602 /ability28 的 subManaHunter」；本记录 %s 在声明域外——本答案为"
    "**类型级外推**（BY_TYPE_EXTRAPOLATED），不升记录级确认，不作实机概率")

SLOTS = ("param0", "param1", "param2")
# slot → death damageType（rules.json conversion：damageType0/2/1 读取 param0/1/2）
SLOT_DAMAGE_TYPE = {"param0": "0", "param1": "2", "param2": "1"}
# slot → 句面对照（推断，不是枚举名确认）
SLOT_SENTENCE_HINT = {
    "param0": "句面「通常攻撃」行只在该槽非零（推断对照）",
    "param1": "句面「クリティカル」行只在该槽非零（推断对照）",
    "param2": "eDamageType.Skill=1（既有规则证据：必殺技）",
}
TYPE_NAMED_SLOT = {"normal": "param0", "crit": "param1", "skill": "param2"}
TYPE_ZH = {"normal": "通常攻撃", "crit": "クリティカル", "skill": "必殺技"}

PHRASE_ZH = {"certain": "一定確率", "always": "必ず", "relative": "獲得しやすくなる"}

FLAT = str.maketrans("０１２３４５６７８９", "0123456789")
JOBWORD = r"(?:戦士|弓使い|魔法使い|僧侶|騎士)"
JOB_BITS = {"騎士": 1, "戦士": 2, "魔法使い": 4, "僧侶": 8, "弓使い": 16}

# 击杀触发（长式优先，避免「敵を倒す」被短式抢先）
KILL_RX = re.compile(
    r"敵に止めを刺した|敵に止めを刺す|止めを刺した時|止めを刺す|"
    r"敵を倒した時|敵を倒した場合|敵を倒すたび|敵を倒すと|敵を倒した|敵を倒す|"
    r"倒した時|倒した場合|倒すたび|倒すと|倒した|倒す"
)
CERTAIN_RX = re.compile(r"一定確率で")
ALWAYS_RX = re.compile(r"必ず")
RELATIVE_RX = re.compile(r"獲得しやすくな|獲得しやすく|なりやすく")
CLAUSE_SEP = "、。！？!?"
CONNECTIVES = ("また", "さらに", "また、", "さらに、")

PARAM6_UNKNOWN = "param6≠4：只写掩码位 1<<param6，地形名未核（不写地形名）"
# 原生比较口径（独审 2026-10-28 实际字节执行：0x154510c fcmp → 0x1545110 b.hi 0x15451b4）：
# 随机值**大于**阈值才跳到跳过分支；随机值**等于**阈值（与小于阈值一样）继续到通过分支。
# 该口径只描述受控比较分支本身，不给实机掉珠概率、自然发生频率或「最终已获/不获珠」结论。
CMP_BOUNDARY = "（比较边界：随机值>阈值跳过，=或<通过；相等计入通过侧）"
ZERO_SLOT_NOTE = "，原值0（阈值0：随机值>阈值跳过，=阈值（相等）通过）"
UNKNOWN_TAIL = [
    "多来源叠加/取最大值未模拟；本答案只给单记录阈值",
    "实际击杀资格、装载与玛那生成未模拟（未做实机验证）",
    "同串其它子句（攻撃力/HP/状態異常/回転速度 等）不在本答案范围",
]
EVIDENCE_BASE = [
    "output/character_skills/profiles/rules.json",
    "output/card_comparison_cid30236/mana_chance/README.md",
    "output/card_comparison_cid30236/mana_chance/native_checks.json",
    "output/card_comparison_cid30236/mana_chance/trace.json",
]

# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def _norm(text):
    s = str(text or "").replace("◆", "").replace("\\n", "").replace("\n", "")
    s = re.sub(r"\[/?[^\]]{0,24}\]", "", s)
    return re.sub(r"\s+", "", s).translate(FLAT)


def _finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _pct(v):
    if not _finite(v):
        return "缺"
    s = ("%.3f" % (float(v) * 100.0)).rstrip("0").rstrip(".")
    return s + "%"


def _raw_txt(v):
    if v is None:
        return "null"
    if not _finite(v):
        return repr(v)
    return repr(float(v))


def _mask_text(p6):
    """param6 → 地形掩码（只写位，不写地形名）；0/缺 → 无附加掩码。"""
    if p6 is None:
        return None
    try:
        code = int(float(p6))
    except (TypeError, ValueError):
        return None
    if code <= 0:
        return None
    return "%d（1<<%d）" % (1 << code, code)


def _base_text(record, text):
    rt, st = _norm((record or {}).get("text") or (record or {}).get("sinfo") or ""), _norm(text)
    if not st:
        return None, -1
    pos = rt.find(st)
    if pos < 0:
        return None, -1
    return rt[:pos], pos


def _last_sentence(prefix):
    parts = [p for p in re.split(r"[。！？!?]", prefix or "") if p]
    return parts[-1] if parts else ""


def _kill_clause(text, pos, end):
    """返回 pos..end 处击杀触发所在的原文子句（只到触发词，不含后接概率短语）。"""
    start = 0
    for i in range(pos - 1, -1, -1):
        if text[i] in CLAUSE_SEP:
            start = i + 1
            break
    seg = text[start:end]
    # 「止めを刺す」等短式后接的と／時／たび／場合属于条件的一部分
    for _suf in ("たび", "場合", "と", "時"):
        if text.startswith(_suf, end):
            seg += _suf
            end += len(_suf)
            break
    for pre in ("また、", "また", "さらに、", "さらに"):
        if seg.startswith(pre):
            seg = seg[len(pre):]
            break
    return seg.strip()


# ---------------------------------------------------------------------------
# 句式解析
# ---------------------------------------------------------------------------
def _named_in(clause):
    named = []
    if "通常攻撃" in clause:
        named.append("normal")
    if "クリティカル" in clause:
        named.append("crit")
    if "必殺技" in clause and not re.search(r"全ての必殺技が使える|必殺技の威力", clause):
        named.append("skill")
    return named


def _prob_hits(t):
    """所有「マナを獲得」概率短语（一定確率／必ず／獲得しやすくなる）。"""
    hits = []
    for code, rx in (("certain", CERTAIN_RX), ("always", ALWAYS_RX), ("relative", RELATIVE_RX)):
        for m in rx.finditer(t):
            pos = m.start()
            if code == "relative":
                # 「マナを獲得しやすくなる」：マナ在短语前
                ok = "マナ" in t[max(0, pos - 20):pos + 12]
            else:
                tail = t[pos:pos + 40]
                ok = ("マナ" in tail
                      and bool(re.search(r"マナ[^。]{0,12}?獲得|獲得[^。]{0,12}?マナ", tail)))
            if ok:
                hits.append((pos, code))
    hits.sort()
    dedup = []
    for pos, code in hits:
        if dedup and pos - dedup[-1][0] < 4:
            continue
        dedup.append((pos, code))
    return dedup


def classify(text, record=None):
    """解析「击杀マナ確率」句；返回 claims（每句概率短语一条）或 rejection。"""
    t = _norm(text)
    out = {"phrase": None, "trigger": None, "named": [], "mana_kind": None,
           "inherited": False, "claims": [], "jobs": [], "rejection": None, "detail": None}
    if not t:
        out["rejection"] = "EMPTY_TEXT"
        return out
    if "マナ" not in t:
        out["rejection"] = "NOT_MANA_CLAIM"
        return out
    hits = _prob_hits(t)
    if not hits:
        out["rejection"] = "NOT_S5_CLAIM"
        return out
    # 玛那种类（原文级）
    if "全ての必殺技が使えるマナ" in t:
        out["mana_kind"] = "allskill"
    elif "全ての職業で使用できるマナ" in t:
        out["mana_kind"] = "alljob"
    else:
        out["mana_kind"] = "plain"
    base = None
    for pos, phrase in hits:
        kills = [m for m in KILL_RX.finditer(t) if m.start() < pos]
        inherited = False
        if kills:
            km = kills[-1]
            clause = _kill_clause(t, km.start(), km.end())
        else:
            # 片段继承：只允许接续词开头的片段，从父记录前文最后一句取触发
            if base is None:
                base, _ = _base_text(record, text)
            if not base or not t.startswith(CONNECTIVES):
                out["rejection"] = "TIMING_MISMATCH"
                out["detail"] = "no kill trigger in row text and no inheritable prefix"
                return out
            last = _norm(_last_sentence(base))
            kills = [m for m in KILL_RX.finditer(last)]
            if not kills:
                out["rejection"] = "TIMING_MISMATCH"
                out["detail"] = {"prefix": last[:80]}
                return out
            km = kills[-1]
            clause = _kill_clause(last, km.start(), km.end())
            inherited = True
        out["claims"].append({"phrase": phrase, "trigger": clause,
                              "named": _named_in(clause), "inherited": inherited})
    first = out["claims"][0]
    out.update({"phrase": first["phrase"], "trigger": first["trigger"],
                "named": list(first["named"]), "inherited": first["inherited"]})
    for c in out["claims"]:
        for n in c["named"]:
            if n not in out["named"]:
                out["named"].append(n)
        for j in [j for j in JOB_BITS if j in c["trigger"]]:
            if j not in out["jobs"]:
                out["jobs"].append(j)
    return out


# ---------------------------------------------------------------------------
# 载体
# ---------------------------------------------------------------------------
def _carriers(data, table, record, layer=None):
    return MB.resolve_carriers(data, table, record, layer=layer)


def _select28(carriers):
    return MB._dedupe([c for c in carriers
                       if (c.get("record") or {}).get("ability") == 28])


def _source_for(data, carrier, slot):
    return MB._carrier_source(data, dict(carrier, slot=slot))


# ---------------------------------------------------------------------------
# 答案
# ---------------------------------------------------------------------------
def _result(table, reference_field, text):
    return {"scope": SCOPE, "table": table, "reference_field": reference_field,
            "text": text, "gates": {}, "accepted": False, "rejection": None,
            "detail": None, "phrase": None, "answers": []}


def _reject(res, code, detail=None):
    res["rejection"] = code
    if detail is not None:
        res["detail"] = detail
    return res


def build_answer(data, table, reference_field, record, text, carrier, cls, cid=None):
    rec = carrier["record"]
    slots = [s for s in SLOTS if _finite(rec.get(s))]
    # 主槽：句面第一条概率子句点名的伤害类型优先（让 raw_value/field_path 落在被主张的
    # 分支上），否则 param0（DamageType0）优先；缺失槽不填零。
    first_named = [TYPE_NAMED_SLOT[n] for n in (cls["claims"][0]["named"] if cls.get("claims")
                                               else [])
                   if TYPE_NAMED_SLOT[n] in slots]
    primary = first_named[0] if first_named else ("param0" if "param0" in slots else slots[0])
    rule_key = "skilllist|28|/" + primary
    named = cls.get("named") or []
    named_slots = [TYPE_NAMED_SLOT[n] for n in named if TYPE_NAMED_SLOT[n] in slots]
    p6 = rec.get("param6")
    mask = _mask_text(p6)
    addon = ((_finite(rec.get("param4")) and float(rec["param4"]) != 0.0)
             or (_finite(rec.get("param5")) and float(rec["param5"]) != 0.0))
    kind_zh = {"allskill": "全ての必殺技が使えるマナ", "alljob": "全ての職業で使用できるマナ",
               "plain": "マナ"}[cls["mana_kind"]]
    named_zh = "・".join(TYPE_ZH[n] for n in named) if named else "不限（不限伤害类型）"

    parts = []
    for s in slots:
        v = rec.get(s)
        tag = "伤害类型%s" % SLOT_DAMAGE_TYPE[s]
        extra = ""
        if s in named_slots:
            extra = "，句面点名"
        elif named and _finite(v) and float(v) > 0.0:
            extra = "，句面未点名（字段原值披露）"
        if _finite(v) and float(v) == 0.0:
            extra += ZERO_SLOT_NOTE
        elif _finite(v) and float(v) == 1.0 and cls["phrase"] != "always":
            extra += "，阈值1.0（100%；句面未单独给出该分支）"
        parts.append("%s→%s%s" % (tag, _pct(v), extra))
    missing = [s for s in SLOTS if s not in slots]
    if missing:
        parts.append("缺失槽：" + "、".join("param%s" % s[-1] for s in missing) + "（null，不填零）")
    # 零阈值答案显式写比较边界（>跳过、=/<通过），与逐槽零值说明及 cond 同一口径；
    # 非零答案不加后缀，保持既有文本逐字节不变。
    has_zero = any(_finite(rec.get(s)) and float(rec.get(s)) == 0.0 for s in slots)
    cmp_boundary = CMP_BOUNDARY if has_zero else ""
    value = ("击杀时获得玛那的概率阈值：%s；判定 Random.Range(0,1) ≤ 基础阈值%s"
             % ("；".join(parts), cmp_boundary))
    if addon:
        value += "（记录另带地形附加 param4/param5，掩码 %s，地形名未核）" % (mask or "未知")

    cond = ("击杀条件（原文，按子句）：%s；句面点名伤害类型：%s；玛那种类（原文）：「%s」；"
            "判定：Random.Range(0,1) ≤ param0/param1/param2（按 DamageType0/2/1）%s"
            % ("；".join("「%s」→%s" % (c["trigger"], PHRASE_ZH[c["phrase"]])
                        for c in cls["claims"]), named_zh, kind_zh, cmp_boundary))
    if any(c.get("inherited") for c in cls["claims"]):
        cond += "；本行为片段，条件取自父记录前文"
    domain_outside = int(rec.get("skillid") or 0) in OUT_OF_DOMAIN_RECORDS
    if domain_outside:
        cond += "；" + DOMAIN_OUTSIDE_TEXT % rec.get("skillid")
    if addon:
        cond += ("；另带地形附加阈值 param4/param5=%.6g/%.6g，掩码 %s（地形名未核，"
                 "本句未写地形条件）" % (float(rec.get("param4") or 0.0),
                                        float(rec.get("param5") or 0.0), mask or "未知"))

    unknowns = [
        "单来源证据（occurrences=1，规则证据记录 43023602/CACHE）；类型级外推，"
        "未逐卡原生核实，不升确认",
        "param3=%s 语义未知（规则未登记；原值保留，不解释）" % _raw_txt(rec.get("param3")),
        "param9=%s 语义未知（规则未登记；原值保留，不解释）" % _raw_txt(rec.get("param9")),
    ]
    if addon:
        unknowns.append(PARAM6_UNKNOWN + "；param4/param5 仅在掩码匹配时叠加，"
                                        "本句未写地形条件")
    if any(c["phrase"] == "relative" for c in cls["claims"]):
        unknowns.append("句面「獲得しやすくなる」为相对表述；记录给绝对阈值，"
                        "相对基准/增幅未登记，不按差值解释")
    if any((_finite(rec.get(s)) and float(rec[s]) == 1.0) for s in slots) and             not any(c["phrase"] == "always" for c in cls["claims"]):
        unknowns.append("记录存在阈值 1.0（100%）的伤害类型；本句概率表述不单独解释该"
                        " 100% 分支（按字段原值披露）")
    if any(c.get("inherited") for c in cls["claims"]):
        unknowns.append("本行文本为片段，触发条件取自父记录前文最后一句")
    if domain_outside:
        unknowns.append(DOMAIN_OUTSIDE_TEXT % rec.get("skillid"))
    if missing:
        unknowns.append("缺失槽 %s：不填零，实际语义未知" % "、".join(missing))
    if cls.get("jobs"):
        unknowns.append("句面点名职业 %s；iParam0=%s 按原值登记（不按单一位猜）"
                        % ("・".join(cls["jobs"]), _raw_txt(rec.get("iParam0"))))
    unknowns.extend(UNKNOWN_TAIL)

    fields = []
    for s in slots:
        v = float(rec.get(s))
        fields.append({
            "f": "/" + s,
            "raw": v,
            "value": "伤害类型%s 击杀マナ阈值 %s（原值 %s；%s）"
                     % (SLOT_DAMAGE_TYPE[s], _pct(v), _raw_txt(v), SLOT_SENTENCE_HINT[s]),
            "kind": "概率阈值",
            "unit": "概率阈值；派生百分比",
            "status": "INFERRED_SINGLE_SOURCE",
            "evidence_scope": "BY_TYPE_EXTRAPOLATED",
            "rule_key": "skilllist|28|/" + s,
            "table": "skilllist",
            "record_id": carrier["record_id"],
            "damage_type": SLOT_DAMAGE_TYPE[s],
            "sentence_hint": SLOT_SENTENCE_HINT[s],
        })

    src = _source_for(data, carrier, primary)
    note_parts = ["单来源类型级外推（occurrences=1，证据层 CACHE；本行载体层 %s）；不升确认" % carrier["layer"]]
    if any(c["phrase"] == "relative" for c in cls["claims"]):
        note_parts.append("句面为相对表述「獲得しやすくなる」")
    if any(c.get("inherited") for c in cls["claims"]):
        note_parts.append("条件取自父记录前文")
    if addon:
        note_parts.append("另带地形附加 param4/param5（掩码 %s，地形名未核）" % (mask or "未知"))
    note_parts.append("句面表述：" + "・".join(PHRASE_ZH[c["phrase"]] for c in cls["claims"]))
    if named:
        note_parts.append("句面点名：" + named_zh)
    if domain_outside:
        note_parts.append(DOMAIN_OUTSIDE_TEXT % rec.get("skillid"))

    binding = {
        "template_id": "type28_%s" % "_".join(c["phrase"] for c in cls["claims"]),
        "strength": ("规则键数值换算已确认（静态＋受控原生局部规则）；句面→载体类型级外推，"
                     "occurrences=1，不升确认"),
        "status": "推断（单来源类型级外推；不升确认）",
        "target": "持有者；击杀事件对应的玛那获得判定（ability28 subManaHunter）",
        "condition": cond,
        "duration": "击杀时逐次判定；常时被动（不是持续时间/每WAVE）",
        "rationale": ("原文只有「%s」概率主张，无逐字数值；载体 type28 记录 %s 的 "
                      "param0/param1/param2 为 DamageType0/2/1 的基础阈值；"
                      "其它类型/记录只登记不取值"
                      % ("・".join(PHRASE_ZH[c["phrase"]] for c in cls["claims"]),
                         carrier["record_id"])),
        "source": src,
        "rule_status": "已确认（静态及受控原生局部规则）",
        "claim": {"table": table,
                  "record_id": MB._claim_record_id(record, table, cid),
                  "reference_field": reference_field, "text": text},
        "fields": fields,
        "registered_not_answered": {
            "param4": rec.get("param4"), "param5": rec.get("param5"),
            "param6": rec.get("param6"),
            "note": ("param4/param5 为地形附加阈值、param6 为位索引（掩码 1<<param6）；"
                     "本批非地形句只登记原值，不写地形名、不作基础阈值答案"),
        },
        "unknowns": unknowns,
        "s5_binding": {"scope": SCOPE, "phrase": cls["phrase"],
                       "phrases": [c["phrase"] for c in cls["claims"]], "slots": slots,
                       "record_id": carrier["record_id"], "carrier_layer": carrier["layer"],
                       "evidence_layer": "CACHE", "rule_occurrences": 1,
                       "damage_types": {s: SLOT_DAMAGE_TYPE[s] for s in slots},
                       "mask": mask, "terrain_addon": bool(addon)},
    }
    # 规则样本域：type28 三键 conditions 只覆盖普通43023602；域外记录（本批仅 30829702 =
    # 8297 f3）逐行披露，数值换算仍按已确认规则，适用性为类型级外推（不升确认）。
    # 域内记录不新增该键——既有 170 条 answer 结构逐字节不变（final_diff 可直接核对）。
    if domain_outside:
        binding["rule_domain"] = dict(
            sample_record=43023602, outside=True,
            rule_keys=["skilllist|28|/param0", "skilllist|28|/param1", "skilllist|28|/param2"],
            evidence_scope="BY_TYPE_EXTRAPOLATED",
            note=DOMAIN_OUTSIDE_TEXT % rec.get("skillid"))

    return {
        "value": value,
        "quantity_kind": "击杀玛那概率阈值",
        "unit": "概率阈值",
        "raw_value": float(rec.get(primary)),
        "field_path": "/" + primary,
        "rule_key": rule_key,
        "table": "skilllist",
        "record_id": carrier["record_id"],
        "layer": carrier["layer"],
        "source": src,
        "context": text,
        "numeric_source": "规则",
        "numeric_evidence": "推断",
        "association_evidence": "推断",
        "answer_status": "INFERRED_SINGLE_SOURCE",
        "evidence_scope": "BY_TYPE_EXTRAPOLATED",
        "quantitative": True,
        "condition_label": "击杀时 / 伤害类型%s（主槽 %s）"
                            % ("·".join(SLOT_DAMAGE_TYPE[x] for x in slots), primary),
        "conditions": cond,
        "target": binding["target"],
        "note": "；".join(note_parts),
        "conversion": value,
        "binding": binding,
        "evidence": list(EVIDENCE_BASE),
    }


# ---------------------------------------------------------------------------
# 逐行评估
# ---------------------------------------------------------------------------
def _already(existing, rule_key, record_id, field_path):
    for a in existing or []:
        if (a.get("rule_key") == rule_key and a.get("record_id") == record_id
                and a.get("field_path") == field_path):
            return True
    return False


def evaluate(data, table, reference_field, record, text, existing_answers=None,
             layer=None, cid=None):
    existing_answers = existing_answers or []
    res = _result(table, reference_field, text)
    if cid in ZERO_TOUCH_CIDS:
        return _reject(res, "ZERO_TOUCH_CID", cid)
    if table not in ADMITTED_TABLES:
        return _reject(res, "CHARAINFO_EQUIVALENCE_FAIL_CLOSED",
                       "展示复制行（%s）需记录级等价门；本批 fail-closed" % table)
    t = _norm(text)
    if not t:
        return _reject(res, "EMPTY_TEXT")
    cls = classify(text, record)
    res["gates"]["classify"] = {k: v for k, v in cls.items() if k != "rejection"}
    res["phrase"] = cls.get("phrase")
    if cls.get("rejection"):
        return _reject(res, cls["rejection"], cls.get("detail"))
    carriers, issues = _carriers(data, table, record, layer)
    res["gates"]["carrier_issues"] = issues
    if issues:
        return _reject(res, "CARRIER_CHAIN_BROKEN", issues)
    c28 = _select28(carriers)
    ids = sorted({c["record_id"] for c in c28})
    res["gates"]["carriers"] = [{"record_id": c["record_id"], "layer": c["layer"],
                                 "role": c["role"]} for c in c28]
    res["gates"]["sibling_mana_types"] = sorted(
        {(c.get("record") or {}).get("ability") for c in carriers
         if (c.get("record") or {}).get("ability") in (26, 28, 80, 96, 1106, 1110, 1111)})
    if not c28:
        return _reject(res, "NO_TYPE28_CARRIER")
    if len(ids) != 1:
        return _reject(res, "MULTI_CARRIER_AMBIGUOUS", ids)
    carrier = c28[0]
    rec = carrier["record"]
    res["gates"]["record_id"] = carrier["record_id"]
    res["gates"]["layer"] = carrier["layer"]
    res["gates"]["params"] = {k: rec.get(k) for k in
                              ("param0", "param1", "param2", "param3", "param4", "param5",
                               "param6", "param8", "param9", "iParam0")}
    res["gates"]["mask"] = _mask_text(rec.get("param6"))
    slots = [s for s in SLOTS if _finite(rec.get(s))]
    res["gates"]["slots"] = slots
    if not slots:
        return _reject(res, "NO_THRESHOLD")

    # G8 同值时机不符：句面点名伤害类型 ↔ 槽位（按每条概率子句各自的表述）
    for claim in cls["claims"]:
        for n in claim["named"]:
            s = TYPE_NAMED_SLOT[n]
            if s not in slots:
                return _reject(res, "SLOT_MISSING", {"named": n, "slot": s,
                                                     "raw": rec.get(s)})
            v = float(rec[s])
            if claim["phrase"] == "always":
                if v != 1.0:
                    return _reject(res, "VALUE_TRIGGER_MISMATCH",
                                   {"named": n, "slot": s, "raw": v, "expected": "必ず=1.0"})
            elif v <= 0.0:
                return _reject(res, "VALUE_TRIGGER_MISMATCH",
                               {"named": n, "slot": s, "raw": v, "expected": ">0"})
    # G9 数值域
    for s in slots:
        v = float(rec[s])
        if not (0.0 <= v <= 1.0):
            return _reject(res, "PROBABILITY_OUT_OF_RANGE", {"slot": s, "raw": v})
    # G7 职业位图
    i0 = rec.get("iParam0")
    jobs = cls.get("jobs") or []
    if jobs:
        want = 0
        for j in jobs:
            want |= JOB_BITS[j]
        if not _finite(i0) or int(i0) != want:
            return _reject(res, "JOB_BITMAP_MISMATCH",
                           {"jobs": jobs, "expected": want, "iParam0": i0})
    else:
        if i0 not in (None, 0, 31, 0.0, 31.0):
            res["gates"]["iParam0_uninterpreted"] = i0
    # G10 无既有答案
    ans = build_answer(data, table, reference_field, record, text, carrier, cls, cid)
    for _s in ans["binding"]["s5_binding"]["slots"]:
        _rk = "skilllist|28|" + _s
        if _already(existing_answers, _rk, ans["record_id"], "/" + _s):
            return _reject(res, "ALREADY_ANSWERED",
                           {"rule_key": _rk, "record_id": ans["record_id"],
                            "field_path": "/" + _s})
    res["accepted"] = True
    res["answers"] = [ans]
    return res


# ---------------------------------------------------------------------------
# 相对概率句：同技能基础行行级归位（2026-10-29 批1；不新增唯一数值）
# ---------------------------------------------------------------------------
def classify_relative(text):
    """解析「（クリティカル攻撃／必殺技…）で倒すと獲得しやすくなる。」式相对句。

    只收**无「マナ」字样**的相对片段（含「マナ」的句子仍走既有绝对/地形路径，行为不变）。
    返回 ``named``（句面点名的伤害类型）；无点名 → NO_NAMED_DAMAGE_TYPE（不猜槽）。
    """
    t = _norm(text)
    out = {"phrase": None, "trigger": None, "named": [], "jobs": [], "rejection": None,
           "detail": None}
    if not t:
        out["rejection"] = "EMPTY_TEXT"
        return out
    if "マナ" in t:
        out["rejection"] = "NOT_RELATIVE_ONLY"
        out["detail"] = "句面含「マナ」：属既有绝对/地形路径，不进入相对归位"
        return out
    m = RELATIVE_RX_STRICT.search(t)
    if not m:
        out["rejection"] = "NOT_RELATIVE_CLAIM"
        return out
    kills = [k for k in KILL_RX.finditer(t) if k.start() < m.start()]
    if not kills:
        out["rejection"] = "TIMING_MISMATCH"
        out["detail"] = "相对句无击杀触发（倒す/倒した/止めを刺す）"
        return out
    km = kills[-1]
    clause = _kill_clause(t, km.start(), km.end())
    named = _named_in(clause)
    out.update(phrase="relative", trigger=clause, named=named)
    if not named:
        out["rejection"] = "NO_NAMED_DAMAGE_TYPE"
        out["detail"] = clause
        return out
    out["jobs"] = [j for j in JOB_BITS if j in clause]
    return out


def _pct_tag(slot, value):
    """「伤害类型X→P%」片段：与 build_answer 的逐槽文案同一格式（逐位相等的前提）。"""
    return "伤害类型%s→%s" % (SLOT_DAMAGE_TYPE[slot], _pct(value))


def build_relative_answer(data, table, reference_field, record, text, carrier, cls,
                          base_row_id, base_answer, cid=None):
    rec = carrier["record"]
    named = cls["named"]
    slots = [TYPE_NAMED_SLOT[n] for n in named]
    primary = slots[0]
    tags = [_pct_tag(s, rec[s]) for s in slots]
    named_zh = "・".join(TYPE_ZH[n] for n in named)
    base_key = (base_answer or {}).get("rule_key")
    base_rec = (base_answer or {}).get("record_id")
    base_note = "同技能基础行 %s（规则键 %s，记录 %s）" % (base_row_id, base_key, base_rec)
    value = ("同技能基础行已披露、本行只作行级归位（不新增唯一数值）：击杀时获得玛那的"
             "概率阈值：%s；基准＝%s 答案文本中同名伤害类型百分比（逐位相同）；"
             "本句为相对表述「獲得しやすくなる」，记录没有相对幅度槽——不写增幅、"
             "不把阈值写成 +N%%" % ("；".join(tags), base_note))
    cond = ("击杀条件（原文，按子句）：「%s」→相对表述「獲得しやすくなる」；句面点名伤害类型："
            "%s；本行为同技能基础行的行级归位：%s；判定口径与基础行相同"
            "（Random.Range(0,1) ≤ param0/param1/param2 按 DamageType0/2/1），"
            "本行不重复给出基础行以外的槽值"
            % (cls["trigger"], named_zh, "；".join(tags)))
    fields = []
    for s in slots:
        v = float(rec.get(s))
        fields.append({
            "f": "/" + s,
            "raw": v,
            "value": "伤害类型%s 击杀マナ阈值 %s（原值 %s；同技能基础行归位，不是本行新增数值）"
                     % (SLOT_DAMAGE_TYPE[s], _pct(v), _raw_txt(v)),
            "kind": "概率阈值（同技能基础行归位）",
            "unit": "概率阈值；派生百分比",
            "status": "INFERRED_RELATIVE_BINDING",
            "evidence_scope": "BY_TYPE_EXTRAPOLATED",
            "rule_key": "skilllist|28|/" + s,
            "table": "skilllist",
            "record_id": carrier["record_id"],
            "damage_type": SLOT_DAMAGE_TYPE[s],
            "sentence_hint": SLOT_SENTENCE_HINT[s],
            "base_row_id": base_row_id,
        })
    src = _source_for(data, carrier, primary)
    unknowns = [
        "本句为相对表述「獲得しやすくなる」：记录只有三个伤害类型的基础阈值，没有「提高多少」"
        "的相对幅度槽——不换算成 +N%、不按差值解释",
        "数值已在同技能基础行答案中披露；本行写入值与该行同名伤害类型百分比逐位相同，"
        "属行级归位（不新增唯一数值），不升确认",
        "单来源证据（occurrences=1，规则证据记录 43023602/CACHE）；类型级外推，"
        "未逐卡原生核实，不升确认",
        "实际击杀资格、装载与玛那生成未模拟（未做实机验证）",
        "同串其它子句（攻撃力/HP/状態異常 等）不在本答案范围",
    ]
    binding = {
        "template_id": "type28_relative_binding",
        "strength": ("数值已在同技能基础行披露；本行只做行级归位（不新增唯一数值）；"
                     "句面→载体归属为推断"),
        "status": "推断（同技能基础行归位；不新增数值、不升确认）",
        "target": "持有者；击杀事件对应的玛那获得判定（ability28 subManaHunter）",
        "condition": cond,
        "duration": "击杀时逐次判定；常时被动（不是持续时间/每WAVE）",
        "rationale": ("原文「%s」为相对表述，没有逐字数值；同一技能的基础行已给出 type28 记录 "
                      "%s 的三个伤害类型基础阈值，本行按句面点名伤害类型取同名百分比做行级"
                      "归位；不改变基础行、不新增幅度" % (cls["trigger"], carrier["record_id"])),
        "source": src,
        "rule_status": "已确认（静态及受控原生局部规则）",
        "claim": {"table": table,
                  "record_id": MB._claim_record_id(record, table, cid),
                  "reference_field": reference_field, "text": text},
        "fields": fields,
        "base_binding": {"base_row_id": base_row_id,
                         "base_rule_key": base_key,
                         "base_record_id": base_rec,
                         "base_field_path": (base_answer or {}).get("field_path"),
                         "base_answer_index": (base_answer or {}).get("answer_index"),
                         "expected_tags": tags,
                         "equality": "逐位相等（同一 _pct 格式；构建期已在基础行答案文本中核验）"},
        "unknowns": unknowns,
        "s5_binding": {"scope": SCOPE, "phrase": "relative", "phrases": ["relative"],
                       "slots": slots, "record_id": carrier["record_id"],
                       "carrier_layer": carrier["layer"], "evidence_layer": "CACHE",
                       "rule_occurrences": 1,
                       "damage_types": {s: SLOT_DAMAGE_TYPE[s] for s in slots},
                       "mask": _mask_text(rec.get("param6")),
                       "terrain_addon": False,
                       "binding_only": True},
        "s5_relative_binding": {"scope": SCOPE, "phrase": "relative",
                                "base_row_id": base_row_id,
                                "base_rule_key": base_key,
                                "base_record_id": base_rec,
                                "slots": slots,
                                "tags": tags,
                                "not_a_new_value": True},
    }
    return {
        "value": value,
        "quantity_kind": "击杀玛那概率阈值（同技能基础行归位）",
        "unit": "概率阈值",
        "raw_value": float(rec.get(primary)),
        "field_path": "/" + primary,
        "rule_key": "skilllist|28|/" + primary,
        "table": "skilllist",
        "record_id": carrier["record_id"],
        "layer": carrier["layer"],
        "source": src,
        "context": text,
        "numeric_source": "规则",
        "numeric_evidence": "推断",
        "association_evidence": "推断",
        "answer_status": "INFERRED_RELATIVE_BINDING",
        "evidence_scope": "BY_TYPE_EXTRAPOLATED",
        "quantitative": True,
        "condition_label": "击杀时·相对句 / 伤害类型%s（同技能基础行归位）"
                            % "·".join(SLOT_DAMAGE_TYPE[s] for s in slots),
        "conditions": cond,
        "target": binding["target"],
        "note": ("同技能基础行归位（不新增唯一数值）：%s；句面为相对表述「獲得しやすくなる」，"
                 "无相对幅度槽，不写增幅；" % "；".join(tags))
                + "单来源类型级外推（occurrences=1；本行载体层 %s）；不升确认" % carrier["layer"],
        "conversion": value,
        "binding": binding,
        "evidence": list(EVIDENCE_BASE),
    }


def evaluate_relative(data, table, reference_field, record, text, sibling_rows,
                      existing_answers=None, layer=None, cid=None, row_id=None):
    """相对句逐行门控：同层 sub 链 ability28 恰 1 条；句面类型↔槽；槽有限且>0；
    同技能基础行已有 ``skilllist|28|/param0`` 答案且同名百分比逐位相同。"""
    existing_answers = existing_answers or []
    sibling_rows = sibling_rows or []
    res = _result(table, reference_field, text)
    if cid in ZERO_TOUCH_CIDS:
        return _reject(res, "ZERO_TOUCH_CID", cid)
    if table not in ADMITTED_TABLES:
        return _reject(res, "CHARAINFO_EQUIVALENCE_FAIL_CLOSED",
                       "展示复制行（%s）需记录级等价门；本批 fail-closed" % table)
    cls = classify_relative(text)
    res["gates"]["classify"] = dict(cls)
    res["phrase"] = cls.get("phrase")
    if cls.get("rejection"):
        return _reject(res, cls["rejection"], cls.get("detail"))
    carriers, issues = _carriers(data, table, record, layer)
    res["gates"]["carrier_issues"] = issues
    if issues:
        return _reject(res, "CARRIER_CHAIN_BROKEN", issues)
    c28 = _select28(carriers)
    ids = sorted({c["record_id"] for c in c28})
    res["gates"]["carriers"] = [{"record_id": c["record_id"], "layer": c["layer"],
                                 "role": c["role"]} for c in c28]
    if not c28:
        return _reject(res, "NO_TYPE28_CARRIER")
    if len(ids) != 1:
        return _reject(res, "MULTI_CARRIER_AMBIGUOUS", ids)
    carrier = c28[0]
    # 同层门：CACHE/APK 同 skillid 不跨层取值（20234 反例：CACHE 技能层 sub 在 CACHE 缺失、
    # 却能从 APK 解析出 42023407）。本批相对句只认同层载体；跨层一律拒答并登记。
    if layer is not None and carrier["layer"] != layer:
        return _reject(res, "CARRIER_LAYER_MISMATCH",
                       {"row_layer": layer, "carrier_layer": carrier["layer"],
                        "record_id": carrier["record_id"]})
    rec = carrier["record"]
    res["gates"]["record_id"] = carrier["record_id"]
    res["gates"]["layer"] = carrier["layer"]
    res["gates"]["params"] = {k: rec.get(k) for k in
                              ("param0", "param1", "param2", "param3", "param4", "param5",
                               "param6", "param8", "param9", "iParam0")}
    slots = [TYPE_NAMED_SLOT[n] for n in cls["named"]]
    res["gates"]["named_slots"] = slots
    for s in slots:
        v = rec.get(s)
        if not _finite(v):
            return _reject(res, "SLOT_MISSING", {"slot": s, "raw": v})
        if float(v) <= 0.0:
            return _reject(res, "VALUE_TRIGGER_MISMATCH",
                           {"slot": s, "raw": float(v), "expected": ">0"})
        if not (0.0 <= float(v) <= 1.0):
            return _reject(res, "PROBABILITY_OUT_OF_RANGE", {"slot": s, "raw": float(v)})
    expected = {s: _pct_tag(s, rec[s]) for s in slots}
    base_hit, seen = None, []
    for srow in sibling_rows:
        if not srow or srow.get("row_id") == row_id:
            continue
        for ai, a in enumerate(srow.get("answers") or []):
            if a.get("rule_key") != BASEROW_RULE_KEY:
                continue
            seen.append({"row_id": srow.get("row_id"), "rule_key": a.get("rule_key"),
                         "record_id": a.get("record_id")})
            if a.get("record_id") != carrier["record_id"]:
                continue
            if a.get("field_path") != "/param0":
                continue
            if a.get("raw_value") != rec.get("param0"):
                continue
            txt = str(a.get("value") or "")
            if not all(t in txt for t in expected.values()):
                continue
            base_hit = (srow.get("row_id"), ai, a)
            break
        if base_hit:
            break
    if base_hit is None:
        return _reject(res, "BASE_ROW_ANSWER_MISSING",
                       {"expected_tags": expected, "candidates": seen[:8]})
    res["gates"]["base_row"] = {"row_id": base_hit[0], "answer_index": base_hit[1],
                                "rule_key": base_hit[2].get("rule_key"),
                                "record_id": base_hit[2].get("record_id"),
                                "expected_tags": expected}
    for s in slots:
        rk = "skilllist|28|/" + s
        if _already(existing_answers, rk, carrier["record_id"], "/" + s):
            return _reject(res, "ALREADY_ANSWERED",
                           {"rule_key": rk, "record_id": carrier["record_id"],
                            "field_path": "/" + s})
    ans = build_relative_answer(data, table, reference_field, record, text, carrier, cls,
                                base_hit[0], dict(base_hit[2], answer_index=base_hit[1]), cid)
    res["accepted"] = True
    res["answers"] = [ans]
    return res


# ---------------------------------------------------------------------------
# 正式页消费
# ---------------------------------------------------------------------------
def _record_index(data, cid):
    index = {}
    for g in ((data.links.get(cid) or {}).get("groups") or []):
        for rec in g.get("records") or []:
            index[(rec.get("table"), rec.get("reference_field"))] = rec
    return index


def _append(row, answer, report):
    def key(a):
        return (a.get("rule_key"), a.get("record_id"), a.get("field_path"))
    if any(key(a) == key(answer) for a in row.get("answers") or []):
        return False
    row.setdefault("answers", []).append(answer)
    row["row_class"] = "A"
    row["evidence"] = "推断"
    row["evidence_label"] = "推断（S5：type28 概率阈值单来源外推）"
    row["partial"] = True
    row["evidence_scope"] = list(dict.fromkeys(list(row.get("evidence_scope") or [])
                                              + ["BY_TYPE_EXTRAPOLATED"]))
    marker = row.setdefault("inference_s5", {"scope": SCOPE, "claims": []})
    marker["claims"].append({"phrase": answer["binding"]["s5_binding"]["phrase"],
                             "record_id": answer["record_id"],
                             "rule_key": answer["rule_key"],
                             "slots": answer["binding"]["s5_binding"]["slots"]})
    report["answers_added"] += 1
    report["additions"].append({"row_id": row["row_id"],
                                "record_id": answer["record_id"],
                                "rule_key": answer["rule_key"],
                                "field_path": answer["field_path"],
                                "raw_value": answer["raw_value"]})
    return True


def _append_relative(row, answer, report):
    def key(a):
        return (a.get("rule_key"), a.get("record_id"), a.get("field_path"))
    if any(key(a) == key(answer) for a in row.get("answers") or []):
        return False
    row.setdefault("answers", []).append(answer)
    row["row_class"] = "A"
    row["evidence"] = "推断"
    row["evidence_label"] = "推断（S5 相对句：同技能基础行行级归位，不新增数值）"
    row["partial"] = True
    row["evidence_scope"] = list(dict.fromkeys(list(row.get("evidence_scope") or [])
                                              + ["BY_TYPE_EXTRAPOLATED"]))
    marker = row.setdefault("inference_s5_relative", {"scope": SCOPE, "claims": []})
    marker["claims"].append({"phrase": "relative",
                             "record_id": answer["record_id"],
                             "rule_key": answer["rule_key"],
                             "slots": answer["binding"]["s5_binding"]["slots"],
                             "base_row_id": answer["binding"]["s5_relative_binding"]["base_row_id"]})
    report["relative_answers_added"] += 1
    report["relative_additions"].append({"row_id": row["row_id"],
                                         "record_id": answer["record_id"],
                                         "rule_key": answer["rule_key"],
                                         "field_path": answer["field_path"],
                                         "raw_value": answer["raw_value"],
                                         "base_row_id": answer["binding"]["s5_relative_binding"]["base_row_id"]})
    return True


def apply_to_groups(data, cid, groups):
    """正式页消费：为 S5 非地形段行绑定 type28 概率阈值答案（不覆盖/不删除既有答案）。

    两段执行：先绝对段（既有 172 行＋8297 f3），再相对段（90 行行级归位）——相对段必须在
    绝对段之后，才能对同技能基础行答案做逐位相等核验（8297 f4 的基准行 f3 就在同批）。
    """
    report = {"scope": SCOPE, "cid": cid, "answers_added": 0, "additions": [],
              "rejections": [], "skipped_existing": 0, "evaluated": 0,
              "relative_evaluated": 0, "relative_answers_added": 0,
              "relative_additions": [], "relative_rejections": [],
              "relative_skipped_existing": 0}
    if cid in ZERO_TOUCH_CIDS:
        report["zero_touch"] = True
        report["rejections"].append({"reason": "ZERO_TOUCH_CID", "cid": cid})
        return report
    index = _record_index(data, cid)
    seen_rows = set()
    for group in groups:
        for skill in group.get("skills", []):
            table = skill.get("table")
            ref = skill.get("reference_field")
            lo = index.get((table, ref))
            if lo is None:
                continue
            record = lo.get("record") or {}
            for row in skill.get("rows", []):
                rid = row.get("row_id")
                if rid in seen_rows:
                    report["rejections"].append({"row_id": rid, "reason": "DUPLICATE_ROW_ID"})
                    continue
                seen_rows.add(rid)
                if rid not in ADMITTED_ROWS:
                    continue
                text = str(row.get("japanese") or "")
                if "マナ" not in text:
                    continue
                report["evaluated"] += 1
                res = evaluate(data, table, ref, record, text, row.get("answers") or [],
                               layer=lo.get("layer"), cid=cid)
                if not res["accepted"]:
                    if res["rejection"] == "ALREADY_ANSWERED":
                        report["skipped_existing"] += 1
                    elif res["rejection"] not in ("NOT_S5_CLAIM", "NOT_MANA_CLAIM"):
                        report["rejections"].append({"row_id": rid,
                                                     "reason": res["rejection"],
                                                     "detail": res.get("detail")})
                    continue
                added = 0
                for ans in res["answers"]:
                    if _append(row, ans, report):
                        added += 1
                if not added:
                    report["skipped_existing"] += 1
                row.setdefault("s5_gate", dict(res["gates"]))

    # ---- 相对句行级归位（2026-10-29 批1）----------------------------------------
    # 只在 RELATIVE_ADMITTED_ROWS 名单内；同层 sub 链 ability28 恰 1 条、句面类型↔槽、
    # 槽有限且>0、同技能基础行已有 skilllist|28|/param0 答案且同名百分比逐位相等。
    # 范围外相对句（NO_CARRIER 17 行、20234 跨层、50 行未证触发路径）不消费。
    rel_seen = set()
    for group in groups:
        for skill in group.get("skills", []):
            table = skill.get("table")
            ref = skill.get("reference_field")
            lo = index.get((table, ref))
            if lo is None:
                continue
            record = lo.get("record") or {}
            rows = skill.get("rows", [])
            for row in rows:
                rid = row.get("row_id")
                if rid not in RELATIVE_ADMITTED_ROWS:
                    continue
                if rid in rel_seen:
                    report["relative_rejections"].append({"row_id": rid,
                                                          "reason": "DUPLICATE_ROW_ID"})
                    continue
                rel_seen.add(rid)
                text = str(row.get("japanese") or "")
                report["relative_evaluated"] += 1
                res = evaluate_relative(data, table, ref, record, text, rows,
                                        row.get("answers") or [], layer=lo.get("layer"),
                                        cid=cid, row_id=rid)
                if not res["accepted"]:
                    if res["rejection"] == "ALREADY_ANSWERED":
                        report["relative_skipped_existing"] += 1
                    else:
                        report["relative_rejections"].append({"row_id": rid,
                                                              "reason": res["rejection"],
                                                              "detail": res.get("detail")})
                    continue
                added = 0
                for ans in res["answers"]:
                    if _append_relative(row, ans, report):
                        added += 1
                if not added:
                    report["relative_skipped_existing"] += 1
                else:
                    row.setdefault("s5_relative_gate", dict(res["gates"]))
    missing = sorted(RELATIVE_ADMITTED_ROWS - rel_seen)
    if missing:
        report["relative_missing_rows"] = missing
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="S5 type28 击杀マナ確率：句式分类只读探针")
    ap.add_argument("--text", help="单句测试")
    args = ap.parse_args(argv)
    if args.text:
        print(json.dumps(classify(args.text, None), ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
