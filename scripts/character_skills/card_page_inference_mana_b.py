# -*- coding: utf-8 -*-
"""マナ B 档（第 3 批）推断模块：start_boost / start_job / hold_mana / mana_count_up。

范围（``docs/tasks/20261026-mana-b-batch.md`` §1；审计
``output/character_skills/inference_inventory/mana_b_audit_20261026/``）
------------------------------------------------------------------------
S1 ``start_boost``（全ての必殺技が使えるマナ N つ開始）＝ ``skilllist|26|/param4``
   （iParam1=31 全职业位图；param5=1 isBoost 标志）。
S2 ``start_job``（職業限定マナ開始）＝ ``26|/param4``＋``/iParam1``（句面职业集合↔位图）
   或 ``26|/param0``＋``/param5``（持有者职业 _jobType 与卡页 jobtype 核对）。
S3 ``hold_mana``（マナ所持/保持バフ）＝ ``skilllist|80`` 的系数槽
   param1 攻击／param2 移动／param3 受伤量／param7 暴击率／param8 暴伤；
   条件＝param0（含等于）＋iParam0 位图＋param6 and/or。
S4 ``mana_count_up``（マナ数スケール）＝ ``skilllist|96`` 的系数槽
   param2/3 攻击（非 Skill／Skill）+ param4 移动 + param5 受伤量 + param6 暴击率 +
   param7 暴伤；条件＝param0 计数对象＋iParam0 位图。

规则来源：``output/character_skills/profiles/rules.json`` 既有键
``skilllist|26|/param0,/param4,/iParam1,/param6``、``skilllist|80|/*``、``skilllist|96|/*``；
原生核对 ``output/character_skills/skilllist_types/native_checks.json`` 53/53。
本批**唯一**新增规则键 ``skilllist|26|/param5``（主持裁决②，条件/标志语义，
证据 ``output/character_skills/type26_mana/native_evidence.json`` slices[5]；
类型级推断，不升确认；不得写「使える必殺技が増える」）。

门控（逐行，拒绝即不出该行/该项；原因码落盘可数）
--------------------------------------------------
G1  句式精确匹配四族；前缀出现 Chain/WAVE/発動時/地形/撃破/スロット/消費/必要マナ
    等时机词 → TIMING_MISMATCH。
G2  载体串：own → sub（1082 str0 转发）→ 容器 skill_ids / abi0/abi1；转发断裂 →
    FORWARD_BROKEN。
G3  mana_plus_bundle：同串非本机制类型的玛那记录（26/28/80/96/1106/1110/1111）
    只登记不取值；本机制类型必须存在，否则 NO_<TYPE>_CARRIER。
G4  level_dup/container_dup：同一载体 record_id 重复（extra 5 档）按 record_id 去重；
    同串 ≥2 个不同 record 且无法按条件/槽位一一区分 → MULTI_CARRIER_AMBIGUOUS。
G5  无既有答案：同 rule_key＋record_id＋field_path 已存在 → ALREADY_ANSWERED（不改旧值）。
G6  同文组：charainfo/denju 记录级等价未证 → CHARAINFO_EQUIVALENCE_FAIL_CLOSED。
G7  职业位图核对：句面职业集合 ↔ iParam1（26）／iParam0（80/96）必须逐一相等；
    不等 → JOB_SET_MISMATCH（不按单一位猜）。
G8  子句↔系数槽断言（80/96）：每个被命名子句必须落到一个非中性系数槽；
    载体的每个非中性系数槽必须被本行子句认领；「効果」只在父记录基础句点名了
    对应属性时才展开；否则 SLOT_UNCLAIMED / CLAUSE_NO_COEFFICIENT / EFFECT_UNRESOLVED。
G9  方向/符号断言：上がる/下がる × 槽位语义（受伤量乘数反向）→ SIGN_MISMATCH。
G10 原值数字核对：句面 N% ↔ 系数（攻/移/暴击率 1+N/100；受伤量 1−N/100；
    暴伤 N/100）→ NUMBER_MISMATCH。
G11 26 生效码 param6：0/1/2 分支；其他码 → PARAM6_INACTIVE。
G12 同值时机不符拒答：S3/S4 的「多い/少ない」方向、S1/S2 的 boost 标志与句式
    必须一致（boost 句↔param5==1.0；使用できる句↔param5!=1.0）→ FLAG_SENTENCE_MISMATCH。
    第二周期整改 N01：param5 与原生 float==1.0 比较（0x158cbb4 fcmp／0x158cbb8 cset eq），
    不做整数化（1.5／1.999 不是 boost）。
G13 S3 带 HP 回复子句（任务书排除项 47 行）→ HP_HEAL_SUBCLAUSE_EXCLUDED。
G14 30236/30239 零触碰 → ZERO_TOUCH_CID。

说明生成（第二周期整改 R01）：type80 /param1,/param2,/param3 为 fmul 乘算（条件写
「乘入」）；/param7 概率 pp 与 /param8 暴伤系数为 fadd 加算（条件写「加算」）；/param3 的
Skill 必杀择槽注记仅属 type96，type80 /param3 是受伤量倍率、/param2 是移动速度乘数；
防御注记方向按受伤量乘数实际增减生成（<1 上がる／>1 下がる）。

证据档：数值换算「确认」（既有规则）；句面→槽位归属「推断」；
``answer_status=CONFIRMED_NUMERIC``、``evidence_scope=BY_TYPE_EXTRAPOLATED``。
不冒充实机、不写业务含义、未知保留不填零。
"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

MODULE_VERSION = "mana_b_batch_20261026"

SCOPE = "MANA_B_BATCH_20261026"
ADMITTED_TABLES = ("skilllist", "extra_ability_info", "supporterskill")
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

# 本批准入行集（审计 batch_candidates S1–S4 重筛 ACCEPT 的 546 行；与数值表无关，
# 只限定 apply_to_groups 的写入范围，保证范围外零变化。evaluate 保持通用供重筛/探针使用）。
ADMITTED_ROWS = frozenset({
    '10001-ability-ability-skillid_1_-lvorder0-f0',
    '10013-ability-ability-skillid_1_-lvorder0-f0',
    '10014-ability-ability-skillid_2_-lvorder1-f1',
    '10030-ability-ability-skillid_1_-lvorder0-f2',
    '10032-ability-ability-skillid_2_-lvorder1-f1',
    '10032-ability-ability-skillid_2_-lvorder1-f2',
    '10042-ability-ability-skillid_2_-lvorder1-f1',
    '10207-ability-ability-skillid_1_-lvorder0-f0',
    '10209-ability-ability-skillid_1_-lvorder0-f0',
    '10209-ability-ability-skillid_1_-lvorder0-f2',
    '10212-extra-extra-extra_abilities_0_-lv1-f0',
    '10212-extra-extra-extra_abilities_1_-lv2-f0',
    '10212-extra-extra-extra_abilities_2_-lv3-f0',
    '10212-extra-extra-extra_abilities_3_-lv4-f0',
    '10212-extra-extra-extra_abilities_4_-lvMAX-f0',
    '10213-extra-extra-extra_abilities_0_-lv1-f0',
    '10213-extra-extra-extra_abilities_1_-lv2-f0',
    '10213-extra-extra-extra_abilities_2_-lv3-f0',
    '10213-extra-extra-extra_abilities_3_-lv4-f0',
    '10213-extra-extra-extra_abilities_4_-lvMAX-f0',
    '10215-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '10215-bond-bond-supporterskill_ability_id____cid-lvorder0-f2',
    '11004-ability-ability-skillid_1_-lvorder0-f0',
    '11216-ability-ability-skillid_1_-lvorder0-f0',
    '11222-ability-ability-skillid_1_-lvorder0-f0',
    '11226-ability-ability-skillid_1_-lvorder0-f0',
    '11231-extra-extra-extra_abilities_0_-lv1-f0',
    '11231-extra-extra-extra_abilities_1_-lv2-f0',
    '11231-extra-extra-extra_abilities_2_-lv3-f0',
    '11231-extra-extra-extra_abilities_3_-lv4-f0',
    '11231-extra-extra-extra_abilities_4_-lvMAX-f0',
    '11232-extra-extra-extra_abilities_0_-lv1-f0',
    '11232-extra-extra-extra_abilities_1_-lv2-f0',
    '11232-extra-extra-extra_abilities_2_-lv3-f0',
    '11232-extra-extra-extra_abilities_3_-lv4-f0',
    '11232-extra-extra-extra_abilities_4_-lvMAX-f0',
    '1201-ability-ability-skillid_1_-lvorder0-f0',
    '1213-ability-ability-skillid_1_-lvorder0-f0',
    '1216-ability-ability-skillid_1_-lvorder0-f0',
    '12213-ability-ability-skillid_1_-lvorder0-f0',
    '12223-ability-ability-skillid_1_-lvorder0-f0',
    '12225-ability-ability-skillid_1_-lvorder0-f0',
    '12225-ability-ability-skillid_2_-lvorder1-f0',
    '12226-ability-ability-skillid_1_-lvorder0-f1',
    '12227-ability-ability-skillid_1_-lvorder0-f0',
    '12229-ability-ability-skillid_1_-lvorder0-f0',
    '12234-ability-ability-skillid_1_-lvorder0-f1',
    '12235-ability-ability-skillid_1_-lvorder0-f0',
    '12236-extra-extra-extra_abilities_0_-lv1-f0',
    '12236-extra-extra-extra_abilities_1_-lv2-f0',
    '12236-extra-extra-extra_abilities_2_-lv3-f0',
    '12236-extra-extra-extra_abilities_3_-lv4-f0',
    '12236-extra-extra-extra_abilities_4_-lvMAX-f0',
    '1242-ability-ability-skillid_1_-lvorder0-f0',
    '1242-ability-ability-skillid_1_-lvorder0-f2',
    '1248-ability-ability-skillid_1_-lvorder0-f1',
    '1249-ability-ability-skillid_1_-lvorder0-f0',
    '1250-ability-ability-skillid_1_-lvorder0-f0',
    '1266-ability-ability-skillid_1_-lvorder0-f1',
    '1268-ability-ability-skillid_1_-lvorder0-f0',
    '1270-ability-ability-skillid_2_-lvorder1-f0',
    '1284-ability-ability-skillid_1_-lvorder0-f1',
    '1284-ability-ability-skillid_2_-lvorder1-f0',
    '1288-ability-ability-skillid_1_-lvorder0-f0',
    '1292-extra-extra-extra_abilities_0_-lv1-f0',
    '1292-extra-extra-extra_abilities_1_-lv2-f0',
    '1292-extra-extra-extra_abilities_2_-lv3-f0',
    '1292-extra-extra-extra_abilities_3_-lv4-f0',
    '1292-extra-extra-extra_abilities_4_-lvMAX-f0',
    '1293-extra-extra-extra_abilities_0_-lv1-f0',
    '1293-extra-extra-extra_abilities_1_-lv2-f0',
    '1293-extra-extra-extra_abilities_2_-lv3-f0',
    '1293-extra-extra-extra_abilities_3_-lv4-f0',
    '1293-extra-extra-extra_abilities_4_-lvMAX-f0',
    '1296-ability-ability-skillid_1_-lvorder0-f0',
    '1296-ability-ability-skillid_1_-lvorder0-f3',
    '13032-ability-ability-skillid_2_-lvorder1-f2',
    '13201-ability-ability-skillid_1_-lvorder0-f0',
    '13201-ability-ability-skillid_2_-lvorder1-f3',
    '13202-ability-ability-skillid_1_-lvorder0-f0',
    '13205-ability-ability-skillid_1_-lvorder0-f0',
    '13207-ability-ability-skillid_1_-lvorder0-f0',
    '13208-ability-ability-skillid_1_-lvorder0-f0',
    '13210-ability-ability-skillid_2_-lvorder1-f2',
    '13211-ability-ability-skillid_1_-lvorder0-f1',
    '13213-ability-ability-skillid_1_-lvorder0-f0',
    '13214-ability-ability-skillid_1_-lvorder0-f1',
    '13214-ability-ability-skillid_1_-lvorder0-f2',
    '13214-ability-ability-skillid_1_-lvorder0-f3',
    '20002-ability-ability-skillid_1_-lvorder0-f0',
    '20105-ability-ability-skillid_1_-lvorder0-f0',
    '20106-ability-ability-skillid_1_-lvorder0-f0',
    '20107-ability-ability-skillid_1_-lvorder0-f0',
    '20108-ability-ability-skillid_1_-lvorder0-f0',
    '20113-ability-ability-skillid_1_-lvorder0-f0',
    '20114-ability-ability-skillid_1_-lvorder0-f0',
    '20115-ability-ability-skillid_1_-lvorder0-f1',
    '20119-ability-ability-skillid_1_-lvorder0-f0',
    '20121-ability-ability-skillid_1_-lvorder0-f0',
    '20123-ability-ability-skillid_1_-lvorder0-f0',
    '20124-ability-ability-skillid_1_-lvorder0-f0',
    '20126-ability-ability-skillid_1_-lvorder0-f0',
    '20127-ability-ability-skillid_1_-lvorder0-f0',
    '20128-ability-ability-skillid_1_-lvorder0-f0',
    '20129-ability-ability-skillid_1_-lvorder0-f0',
    '20130-ability-ability-skillid_1_-lvorder0-f0',
    '20131-ability-ability-skillid_1_-lvorder0-f0',
    '20132-ability-ability-skillid_1_-lvorder0-f0',
    '20132-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20201-ability-ability-skillid_1_-lvorder0-f0',
    '20202-ability-ability-skillid_1_-lvorder0-f0',
    '20203-ability-ability-skillid_1_-lvorder0-f0',
    '20205-ability-ability-skillid_1_-lvorder0-f0',
    '20211-ability-ability-skillid_1_-lvorder0-f0',
    '20211-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20212-ability-ability-skillid_1_-lvorder0-f0',
    '20214-ability-ability-skillid_1_-lvorder0-f0',
    '20215-ability-ability-skillid_1_-lvorder0-f0',
    '20217-ability-ability-skillid_1_-lvorder0-f0',
    '20219-ability-ability-skillid_2_-lvorder1-f2',
    '20221-ability-ability-skillid_1_-lvorder0-f0',
    '20221-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20228-ability-ability-skillid_1_-lvorder0-f0',
    '20229-ability-ability-skillid_1_-lvorder0-f0',
    '20230-ability-ability-skillid_1_-lvorder0-f0',
    '20232-ability-ability-skillid_1_-lvorder0-f0',
    '20233-ability-ability-skillid_1_-lvorder0-f0',
    '20234-ability-ability-skillid_1_-lvorder0-f0',
    '20301-ability-ability-skillid_1_-lvorder0-f0',
    '20302-ability-ability-skillid_1_-lvorder0-f0',
    '20303-ability-ability-skillid_1_-lvorder0-f0',
    '20304-ability-ability-skillid_1_-lvorder0-f0',
    '20305-ability-ability-skillid_1_-lvorder0-f0',
    '20306-ability-ability-skillid_1_-lvorder0-f0',
    '20309-ability-ability-skillid_1_-lvorder0-f0',
    '20311-ability-ability-skillid_1_-lvorder0-f0',
    '20313-ability-ability-skillid_1_-lvorder0-f0',
    '20315-ability-ability-skillid_1_-lvorder0-f0',
    '20318-ability-ability-skillid_1_-lvorder0-f1',
    '20320-ability-ability-skillid_1_-lvorder0-f0',
    '20320-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20325-ability-ability-skillid_1_-lvorder0-f0',
    '20326-ability-ability-skillid_1_-lvorder0-f0',
    '20327-ability-ability-skillid_1_-lvorder0-f0',
    '20330-ability-ability-skillid_1_-lvorder0-f0',
    '20331-ability-ability-skillid_1_-lvorder0-f0',
    '20332-ability-ability-skillid_1_-lvorder0-f0',
    '204-ability-ability-skillid_1_-lvorder0-f2',
    '20401-ability-ability-skillid_1_-lvorder0-f0',
    '20403-ability-ability-skillid_1_-lvorder0-f0',
    '20404-ability-ability-skillid_1_-lvorder0-f0',
    '20405-ability-ability-skillid_1_-lvorder0-f0',
    '20406-ability-ability-skillid_1_-lvorder0-f0',
    '20407-ability-ability-skillid_1_-lvorder0-f0',
    '20409-ability-ability-skillid_1_-lvorder0-f0',
    '20411-ability-ability-skillid_1_-lvorder0-f0',
    '20413-ability-ability-skillid_1_-lvorder0-f0',
    '20414-ability-ability-skillid_1_-lvorder0-f0',
    '20415-ability-ability-skillid_1_-lvorder0-f0',
    '20420-ability-ability-skillid_1_-lvorder0-f0',
    '20422-ability-ability-skillid_1_-lvorder0-f0',
    '20422-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20433-ability-ability-skillid_1_-lvorder0-f0',
    '20434-ability-ability-skillid_1_-lvorder0-f0',
    '20435-ability-ability-skillid_1_-lvorder0-f0',
    '20436-ability-ability-skillid_1_-lvorder0-f0',
    '20438-ability-ability-skillid_1_-lvorder0-f0',
    '20438-ability-ability-skillid_1_-lvorder0-f2',
    '20439-ability-ability-skillid_1_-lvorder0-f0',
    '2046-ability-ability-skillid_1_-lvorder0-f0',
    '205-ability-ability-skillid_1_-lvorder0-f1',
    '20501-ability-ability-skillid_1_-lvorder0-f0',
    '20503-ability-ability-skillid_1_-lvorder0-f0',
    '20504-ability-ability-skillid_1_-lvorder0-f0',
    '20506-ability-ability-skillid_1_-lvorder0-f0',
    '20509-ability-ability-skillid_1_-lvorder0-f0',
    '20510-ability-ability-skillid_1_-lvorder0-f0',
    '20511-ability-ability-skillid_1_-lvorder0-f0',
    '20512-ability-ability-skillid_1_-lvorder0-f0',
    '20513-ability-ability-skillid_1_-lvorder0-f0',
    '20514-ability-ability-skillid_1_-lvorder0-f0',
    '20515-ability-ability-skillid_1_-lvorder0-f0',
    '20516-ability-ability-skillid_1_-lvorder0-f0',
    '20518-ability-ability-skillid_1_-lvorder0-f0',
    '20520-ability-ability-skillid_1_-lvorder0-f0',
    '20525-ability-ability-skillid_1_-lvorder0-f0',
    '20525-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20602-ability-ability-skillid_1_-lvorder0-f0',
    '20603-ability-ability-skillid_1_-lvorder0-f0',
    '20604-ability-ability-skillid_1_-lvorder0-f0',
    '20606-ability-ability-skillid_1_-lvorder0-f0',
    '20607-ability-ability-skillid_1_-lvorder0-f0',
    '20609-ability-ability-skillid_1_-lvorder0-f0',
    '20610-ability-ability-skillid_1_-lvorder0-f0',
    '20612-ability-ability-skillid_1_-lvorder0-f0',
    '20613-ability-ability-skillid_1_-lvorder0-f0',
    '20614-ability-ability-skillid_1_-lvorder0-f0',
    '20615-ability-ability-skillid_1_-lvorder0-f0',
    '20615-ability-ability-skillid_1_-lvorder0-f3',
    '20618-ability-ability-skillid_1_-lvorder0-f0',
    '20619-ability-ability-skillid_1_-lvorder0-f0',
    '20619-ability-ability-skillid_1_-lvorder0-f2',
    '20620-ability-ability-skillid_1_-lvorder0-f0',
    '20622-ability-ability-skillid_1_-lvorder0-f0',
    '20623-ability-ability-skillid_1_-lvorder0-f0',
    '20627-ability-ability-skillid_1_-lvorder0-f0',
    '20629-ability-ability-skillid_1_-lvorder0-f0',
    '20629-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '20630-ability-ability-skillid_1_-lvorder0-f0',
    '20633-ability-ability-skillid_1_-lvorder0-f0',
    '20634-ability-ability-skillid_1_-lvorder0-f0',
    '20635-ability-ability-skillid_1_-lvorder0-f0',
    '20636-ability-ability-skillid_1_-lvorder0-f0',
    '20637-ability-ability-skillid_1_-lvorder0-f0',
    '20638-ability-ability-skillid_1_-lvorder0-f0',
    '20640-ability-ability-skillid_1_-lvorder0-f0',
    '20641-ability-ability-skillid_1_-lvorder0-f2',
    '20642-ability-ability-skillid_1_-lvorder0-f0',
    '207-ability-ability-skillid_1_-lvorder0-f1',
    '20701-ability-ability-skillid_1_-lvorder0-f0',
    '20704-ability-ability-skillid_1_-lvorder0-f0',
    '20705-ability-ability-skillid_1_-lvorder0-f0',
    '20706-ability-ability-skillid_1_-lvorder0-f0',
    '20710-ability-ability-skillid_1_-lvorder0-f0',
    '20711-ability-ability-skillid_1_-lvorder0-f0',
    '20712-ability-ability-skillid_1_-lvorder0-f0',
    '20713-ability-ability-skillid_1_-lvorder0-f0',
    '20714-ability-ability-skillid_1_-lvorder0-f0',
    '20715-ability-ability-skillid_1_-lvorder0-f0',
    '20717-ability-ability-skillid_1_-lvorder0-f0',
    '20719-ability-ability-skillid_1_-lvorder0-f0',
    '20721-ability-ability-skillid_1_-lvorder0-f0',
    '20722-ability-ability-skillid_1_-lvorder0-f0',
    '20724-ability-ability-skillid_1_-lvorder0-f0',
    '20724-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20725-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '20726-ability-ability-skillid_1_-lvorder0-f0',
    '20802-ability-ability-skillid_1_-lvorder0-f0',
    '20803-ability-ability-skillid_1_-lvorder0-f0',
    '20803-ability-ability-skillid_1_-lvorder0-f2',
    '20804-ability-ability-skillid_1_-lvorder0-f0',
    '20805-ability-ability-skillid_1_-lvorder0-f0',
    '20806-ability-ability-skillid_1_-lvorder0-f0',
    '20808-ability-ability-skillid_1_-lvorder0-f0',
    '20811-ability-ability-skillid_1_-lvorder0-f0',
    '20812-ability-ability-skillid_1_-lvorder0-f0',
    '20816-ability-ability-skillid_1_-lvorder0-f0',
    '20817-ability-ability-skillid_1_-lvorder0-f0',
    '20818-ability-ability-skillid_1_-lvorder0-f0',
    '20819-ability-ability-skillid_1_-lvorder0-f0',
    '20820-ability-ability-skillid_1_-lvorder0-f0',
    '20822-ability-ability-skillid_1_-lvorder0-f0',
    '20823-ability-ability-skillid_1_-lvorder0-f0',
    '20824-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20827-ability-ability-skillid_1_-lvorder0-f0',
    '20827-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20902-ability-ability-skillid_1_-lvorder0-f0',
    '20902-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20903-ability-ability-skillid_1_-lvorder0-f0',
    '20903-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20904-ability-ability-skillid_1_-lvorder0-f0',
    '20904-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20905-ability-ability-skillid_1_-lvorder0-f0',
    '20905-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20906-ability-ability-skillid_1_-lvorder0-f0',
    '20906-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20907-ability-ability-skillid_1_-lvorder0-f0',
    '20907-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20908-ability-ability-skillid_1_-lvorder0-f0',
    '20908-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20909-ability-ability-skillid_1_-lvorder0-f0',
    '20909-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20910-ability-ability-skillid_1_-lvorder0-f0',
    '20910-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20912-ability-ability-skillid_1_-lvorder0-f0',
    '20912-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20913-ability-ability-skillid_1_-lvorder0-f0',
    '20913-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20914-ability-ability-skillid_1_-lvorder0-f0',
    '20914-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20915-ability-ability-skillid_1_-lvorder0-f0',
    '20915-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20916-ability-ability-skillid_1_-lvorder0-f0',
    '20916-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20916-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '20917-ability-ability-skillid_1_-lvorder0-f0',
    '20917-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '20918-ability-ability-skillid_1_-lvorder0-f0',
    '20918-bond-bond-supporterskill_ability_id____cid-lvorder0-f0',
    '2204-ability-ability-skillid_1_-lvorder0-f0',
    '2205-ability-ability-skillid_1_-lvorder0-f0',
    '2206-ability-ability-skillid_1_-lvorder0-f0',
    '2207-ability-ability-skillid_1_-lvorder0-f1',
    '2219-ability-ability-skillid_2_-lvorder1-f0',
    '2229-ability-ability-skillid_1_-lvorder0-f1',
    '2236-ability-ability-skillid_1_-lvorder0-f1',
    '224-ability-ability-skillid_1_-lvorder0-f0',
    '2248-ability-ability-skillid_2_-lvorder1-f1',
    '2261-ability-ability-skillid_1_-lvorder0-f1',
    '2262-ability-ability-skillid_2_-lvorder1-f0',
    '2269-ability-ability-skillid_1_-lvorder0-f0',
    '2269-ability-ability-skillid_1_-lvorder0-f2',
    '2274-ability-ability-skillid_1_-lvorder0-f0',
    '2274-ability-ability-skillid_1_-lvorder0-f2',
    '2275-ability-ability-skillid_1_-lvorder0-f0',
    '2276-ability-ability-skillid_1_-lvorder0-f0',
    '2276-ability-ability-skillid_2_-lvorder1-f1',
    '2277-ability-ability-skillid_1_-lvorder0-f0',
    '2277-ability-ability-skillid_2_-lvorder1-f1',
    '2280-ability-ability-skillid_1_-lvorder0-f2',
    '2282-ability-ability-skillid_1_-lvorder0-f0',
    '2282-ability-ability-skillid_1_-lvorder0-f2',
    '2282-ability-ability-skillid_1_-lvorder0-f3',
    '2285-ability-ability-skillid_2_-lvorder1-f0',
    '2286-ability-ability-skillid_1_-lvorder0-f1',
    '2289-ability-ability-skillid_1_-lvorder0-f0',
    '2293-ability-ability-skillid_2_-lvorder1-f1',
    '2300-ability-ability-skillid_1_-lvorder0-f0',
    '2300-ability-ability-skillid_1_-lvorder0-f1',
    '2301-ability-ability-skillid_1_-lvorder0-f0',
    '2305-ability-ability-skillid_2_-lvorder1-f0',
    '2310-ability-ability-skillid_1_-lvorder0-f0',
    '2315-ability-ability-skillid_2_-lvorder1-f3',
    '2320-ability-ability-skillid_1_-lvorder0-f1',
    '2321-ability-ability-skillid_1_-lvorder0-f0',
    '2322-extra-extra-extra_abilities_0_-lv1-f0',
    '2322-extra-extra-extra_abilities_1_-lv2-f0',
    '2322-extra-extra-extra_abilities_2_-lv3-f0',
    '2322-extra-extra-extra_abilities_3_-lv4-f0',
    '2322-extra-extra-extra_abilities_4_-lvMAX-f0',
    '2323-extra-extra-extra_abilities_0_-lv1-f0',
    '2323-extra-extra-extra_abilities_1_-lv2-f0',
    '2323-extra-extra-extra_abilities_2_-lv3-f0',
    '2323-extra-extra-extra_abilities_3_-lv4-f0',
    '2323-extra-extra-extra_abilities_4_-lvMAX-f0',
    '2324-ability-ability-skillid_1_-lvorder0-f1',
    '2326-ability-ability-skillid_1_-lvorder0-f0',
    '2329-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '2329-bond-bond-supporterskill_ability_id____cid-lvorder0-f3',
    '2330-ability-ability-skillid_1_-lvorder0-f2',
    '2330-ability-ability-skillid_1_-lvorder0-f3',
    '268-ability-ability-skillid_1_-lvorder0-f0',
    '278-ability-ability-skillid_1_-lvorder0-f0',
    '279-ability-ability-skillid_1_-lvorder0-f0',
    '282-ability-ability-skillid_1_-lvorder0-f0',
    '282-ability-ability-skillid_1_-lvorder0-f2',
    '285-ability-ability-skillid_1_-lvorder0-f0',
    '292-ability-ability-skillid_1_-lvorder0-f0',
    '292-extra-extra-extra_abilities_0_-lv1-f0',
    '292-extra-extra-extra_abilities_1_-lv2-f0',
    '292-extra-extra-extra_abilities_2_-lv3-f0',
    '292-extra-extra-extra_abilities_3_-lv4-f0',
    '292-extra-extra-extra_abilities_4_-lvMAX-f0',
    '295-ability-ability-skillid_1_-lvorder0-f1',
    '302-ability-ability-skillid_1_-lvorder0-f1',
    '30207-ability-ability-skillid_1_-lvorder0-f0',
    '30207-ability-ability-skillid_1_-lvorder0-f1',
    '30223-ability-ability-skillid_1_-lvorder0-f1',
    '30264-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '30301-ability-ability-skillid_1_-lvorder0-f1',
    '30301-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '30337-ability-ability-skillid_1_-lvorder0-f3',
    '305-ability-ability-skillid_1_-lvorder0-f0',
    '308-ability-ability-skillid_1_-lvorder0-f0',
    '309-ability-ability-skillid_1_-lvorder0-f0',
    '318-ability-ability-skillid_2_-lvorder1-f1',
    '322-ability-ability-skillid_1_-lvorder0-f0',
    '322-ability-ability-skillid_2_-lvorder1-f3',
    '3222-ability-ability-skillid_1_-lvorder0-f0',
    '3235-ability-ability-skillid_1_-lvorder0-f2',
    '327-ability-ability-skillid_1_-lvorder0-f0',
    '337-extra-extra-extra_abilities_0_-lv1-f0',
    '337-extra-extra-extra_abilities_1_-lv2-f0',
    '337-extra-extra-extra_abilities_2_-lv3-f0',
    '337-extra-extra-extra_abilities_3_-lv4-f0',
    '337-extra-extra-extra_abilities_4_-lvMAX-f0',
    '339-ability-ability-skillid_1_-lvorder0-f0',
    '340-extra-extra-extra_abilities_0_-lv1-f0',
    '340-extra-extra-extra_abilities_1_-lv2-f0',
    '340-extra-extra-extra_abilities_2_-lv3-f0',
    '340-extra-extra-extra_abilities_3_-lv4-f0',
    '340-extra-extra-extra_abilities_4_-lvMAX-f0',
    '345-ability-ability-skillid_1_-lvorder0-f1',
    '4209-ability-ability-skillid_1_-lvorder0-f0',
    '4215-ability-ability-skillid_2_-lvorder1-f3',
    '4224-ability-ability-skillid_1_-lvorder0-f0',
    '4224-ability-ability-skillid_2_-lvorder1-f1',
    '4257-ability-ability-skillid_1_-lvorder0-f1',
    '4272-ability-ability-skillid_1_-lvorder0-f0',
    '4276-ability-ability-skillid_1_-lvorder0-f2',
    '4286-ability-ability-skillid_1_-lvorder0-f1',
    '4291-ability-ability-skillid_1_-lvorder0-f1',
    '4296-ability-ability-skillid_1_-lvorder0-f0',
    '4300-ability-ability-skillid_1_-lvorder0-f0',
    '4307-ability-ability-skillid_2_-lvorder1-f1',
    '4309-ability-ability-skillid_1_-lvorder0-f0',
    '4310-ability-ability-skillid_1_-lvorder0-f0',
    '4311-extra-extra-extra_abilities_0_-lv1-f0',
    '4311-extra-extra-extra_abilities_1_-lv2-f0',
    '4311-extra-extra-extra_abilities_2_-lv3-f0',
    '4311-extra-extra-extra_abilities_3_-lv4-f0',
    '4311-extra-extra-extra_abilities_4_-lvMAX-f0',
    '4312-extra-extra-extra_abilities_0_-lv1-f0',
    '4312-extra-extra-extra_abilities_1_-lv2-f0',
    '4312-extra-extra-extra_abilities_2_-lv3-f0',
    '4312-extra-extra-extra_abilities_3_-lv4-f0',
    '4312-extra-extra-extra_abilities_4_-lvMAX-f0',
    '5207-ability-ability-skillid_1_-lvorder0-f0',
    '5211-ability-ability-skillid_1_-lvorder0-f0',
    '5224-ability-ability-skillid_1_-lvorder0-f0',
    '5259-ability-ability-skillid_1_-lvorder0-f1',
    '5275-ability-ability-skillid_1_-lvorder0-f0',
    '5275-ability-ability-skillid_1_-lvorder0-f2',
    '5287-ability-ability-skillid_1_-lvorder0-f0',
    '5291-ability-ability-skillid_2_-lvorder1-f3',
    '5294-ability-ability-skillid_1_-lvorder0-f0',
    '5295-ability-ability-skillid_1_-lvorder0-f0',
    '5296-ability-ability-skillid_2_-lvorder1-f0',
    '5296-ability-ability-skillid_2_-lvorder1-f1',
    '5302-extra-extra-extra_abilities_0_-lv1-f0',
    '5302-extra-extra-extra_abilities_1_-lv2-f0',
    '5302-extra-extra-extra_abilities_2_-lv3-f0',
    '5302-extra-extra-extra_abilities_3_-lv4-f0',
    '5302-extra-extra-extra_abilities_4_-lvMAX-f0',
    '5303-extra-extra-extra_abilities_0_-lv1-f0',
    '5303-extra-extra-extra_abilities_1_-lv2-f0',
    '5303-extra-extra-extra_abilities_2_-lv3-f0',
    '5303-extra-extra-extra_abilities_3_-lv4-f0',
    '5303-extra-extra-extra_abilities_4_-lvMAX-f0',
    '6206-ability-ability-skillid_1_-lvorder0-f0',
    '6214-ability-ability-skillid_2_-lvorder1-f1',
    '6222-ability-ability-skillid_1_-lvorder0-f0',
    '6229-ability-ability-skillid_1_-lvorder0-f2',
    '6280-ability-ability-skillid_1_-lvorder0-f2',
    '6294-ability-ability-skillid_2_-lvorder1-f0',
    '6298-ability-ability-skillid_1_-lvorder0-f0',
    '6307-ability-ability-skillid_1_-lvorder0-f1',
    '6314-ability-ability-skillid_1_-lvorder0-f0',
    '6318-ability-ability-skillid_2_-lvorder1-f0',
    '6322-ability-ability-skillid_1_-lvorder0-f1',
    '6330-ability-ability-skillid_1_-lvorder0-f0',
    '6333-extra-extra-extra_abilities_0_-lv1-f0',
    '6333-extra-extra-extra_abilities_1_-lv2-f0',
    '6333-extra-extra-extra_abilities_2_-lv3-f0',
    '6333-extra-extra-extra_abilities_3_-lv4-f0',
    '6333-extra-extra-extra_abilities_4_-lvMAX-f0',
    '6335-extra-extra-extra_abilities_0_-lv1-f0',
    '6335-extra-extra-extra_abilities_1_-lv2-f0',
    '6335-extra-extra-extra_abilities_2_-lv3-f0',
    '6335-extra-extra-extra_abilities_3_-lv4-f0',
    '6335-extra-extra-extra_abilities_4_-lvMAX-f0',
    '6336-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '6339-ability-ability-skillid_1_-lvorder0-f0',
    '6339-ability-ability-skillid_1_-lvorder0-f1',
    '7201-ability-ability-skillid_1_-lvorder0-f1',
    '7220-ability-ability-skillid_1_-lvorder0-f0',
    '7223-ability-ability-skillid_1_-lvorder0-f2',
    '7229-ability-ability-skillid_1_-lvorder0-f0',
    '7235-ability-ability-skillid_1_-lvorder0-f0',
    '7236-ability-ability-skillid_1_-lvorder0-f0',
    '7238-ability-ability-skillid_1_-lvorder0-f0',
    '7240-ability-ability-skillid_2_-lvorder1-f1',
    '7245-ability-ability-skillid_1_-lvorder0-f2',
    '7248-extra-extra-extra_abilities_0_-lv1-f0',
    '7248-extra-extra-extra_abilities_1_-lv2-f0',
    '7248-extra-extra-extra_abilities_2_-lv3-f0',
    '7248-extra-extra-extra_abilities_3_-lv4-f0',
    '7248-extra-extra-extra_abilities_4_-lvMAX-f0',
    '7507-ability-ability-skillid_2_-lvorder1-f1',
    '7518-ability-ability-skillid_1_-lvorder0-f1',
    '7526-ability-ability-skillid_1_-lvorder0-f2',
    '7576-ability-ability-skillid_1_-lvorder0-f0',
    '7613-ability-ability-skillid_1_-lvorder0-f1',
    '7637-ability-ability-skillid_1_-lvorder0-f1',
    '7638-ability-ability-skillid_2_-lvorder1-f0',
    '7644-ability-ability-skillid_1_-lvorder0-f1',
    '7648-ability-ability-skillid_1_-lvorder0-f0',
    '7658-ability-ability-skillid_2_-lvorder1-f2',
    '7660-ability-ability-skillid_1_-lvorder0-f0',
    '7661-ability-ability-skillid_1_-lvorder0-f2',
    '7662-ability-ability-skillid_2_-lvorder1-f2',
    '7671-ability-ability-skillid_2_-lvorder1-f3',
    '7673-ability-ability-skillid_2_-lvorder1-f0',
    '7673-ability-ability-skillid_2_-lvorder1-f1',
    '7674-ability-ability-skillid_1_-lvorder0-f0',
    '7679-ability-ability-skillid_1_-lvorder0-f0',
    '8160-ability-ability-skillid_1_-lvorder0-f1',
    '8166-ability-ability-skillid_2_-lvorder1-f1',
    '8244-ability-ability-skillid_1_-lvorder0-f0',
    '8256-ability-ability-skillid_1_-lvorder0-f0',
    '8261-ability-ability-skillid_2_-lvorder1-f0',
    '8271-ability-ability-skillid_2_-lvorder1-f0',
    '8294-ability-ability-skillid_1_-lvorder0-f0',
    '8295-ability-ability-skillid_1_-lvorder0-f0',
    '8295-ability-ability-skillid_1_-lvorder0-f1',
    '8311-ability-ability-skillid_1_-lvorder0-f1',
    '8315-ability-ability-skillid_2_-lvorder1-f0',
    '8321-ability-ability-skillid_2_-lvorder1-f3',
    '8323-ability-ability-skillid_1_-lvorder0-f2',
    '8323-ability-ability-skillid_1_-lvorder0-f3',
    '8328-ability-ability-skillid_1_-lvorder0-f3',
    '8328-ability-ability-skillid_1_-lvorder0-f4',
    '8344-ability-ability-skillid_2_-lvorder1-f2',
    '8345-ability-ability-skillid_1_-lvorder0-f0',
    '8351-ability-ability-skillid_1_-lvorder0-f3',
    '8361-ability-ability-skillid_1_-lvorder0-f0',
    '8367-ability-ability-skillid_1_-lvorder0-f0',
    '8368-ability-ability-skillid_1_-lvorder0-f0',
    '8371-ability-ability-skillid_1_-lvorder0-f0',
    '8372-ability-ability-skillid_1_-lvorder0-f0',
    '8375-ability-ability-skillid_1_-lvorder0-f0',
    '8377-ability-ability-skillid_1_-lvorder0-f0',
    '8378-ability-ability-skillid_1_-lvorder0-f0',
    '8380-ability-ability-skillid_1_-lvorder0-f0',
    '8381-ability-ability-skillid_1_-lvorder0-f0',
    '8383-ability-ability-skillid_1_-lvorder0-f0',
    '8385-ability-ability-skillid_1_-lvorder0-f0',
    '8387-ability-ability-skillid_1_-lvorder0-f0',
    '8389-ability-ability-skillid_1_-lvorder0-f0',
    '8391-ability-ability-skillid_1_-lvorder0-f0',
    '8392-ability-ability-skillid_1_-lvorder0-f0',
    '8393-ability-ability-skillid_1_-lvorder0-f0',
    '8394-ability-ability-skillid_1_-lvorder0-f0',
    '8396-ability-ability-skillid_1_-lvorder0-f0',
    '8398-ability-ability-skillid_1_-lvorder0-f0',
    '8401-ability-ability-skillid_1_-lvorder0-f0',
    '8403-ability-ability-skillid_1_-lvorder0-f0',
    '8405-ability-ability-skillid_1_-lvorder0-f0',
    '8407-ability-ability-skillid_1_-lvorder0-f0',
    '8409-ability-ability-skillid_1_-lvorder0-f0',
    '8412-ability-ability-skillid_1_-lvorder0-f0',
    '8414-ability-ability-skillid_1_-lvorder0-f0',
    '8416-ability-ability-skillid_1_-lvorder0-f0',
    '9217-ability-ability-skillid_1_-lvorder0-f0',
    '9223-ability-ability-skillid_1_-lvorder0-f0',
    '9229-ability-ability-skillid_1_-lvorder0-f0',
    '9236-ability-ability-skillid_1_-lvorder0-f0',
    '9238-extra-extra-extra_abilities_0_-lv1-f0',
    '9238-extra-extra-extra_abilities_1_-lv2-f0',
    '9238-extra-extra-extra_abilities_2_-lv3-f0',
    '9238-extra-extra-extra_abilities_3_-lv4-f0',
    '9238-extra-extra-extra_abilities_4_-lvMAX-f0',
    '9240-ability-ability-skillid_1_-lvorder0-f0',
    '9240-ability-ability-skillid_1_-lvorder0-f2',
    '9242-bond-bond-supporterskill_ability_id____cid-lvorder0-f1',
    '9242-bond-bond-supporterskill_ability_id____cid-lvorder0-f2',
})

JOB_BITS = {"戦士": 1, "弓使い": 2, "魔法使い": 4, "僧侶": 8, "騎士": 16, "天魔": 32}
JOBTYPE_BITS = {0: 1, 1: 2, 2: 4, 3: 8, 4: 16}
JOB_NAMES = {v: k for k, v in JOB_BITS.items()}

EFFECT_WORDS = {
    "攻撃力": "attack",
    "防御力": "defence",
    "移動速度": "move",
    "クリティカル発生率": "crit_rate",
    "クリティカル威力": "crit_dmg",
}
E80_SLOT = {"attack": "param1", "move": "param2", "defence": "param3",
            "crit_rate": "param7", "crit_dmg": "param8"}
E96_SLOTS = {"attack": ("param2", "param3"), "move": ("param4",),
             "defence": ("param5",), "crit_rate": ("param6",), "crit_dmg": ("param7",)}
EFFECT_ZH = {"attack": "攻击力", "move": "移动速度", "defence": "防御力",
             "crit_rate": "暴击发生率", "crit_dmg": "暴击威力"}
SLOT_EFFECT = {"param1": "attack", "param2": "move", "param3": "defence",
               "param7": "crit_rate", "param8": "crit_dmg"}

FLAT = str.maketrans("０１２３４５６７８９", "0123456789")
JOBWORD = r"(?:戦士|弓使い|魔法使い|僧侶|騎士)"
JOBSEQ = JOBWORD + r"(?:(?:と|か|、|または)" + JOBWORD + r")*"

S1_RX = re.compile(r"^全ての必殺技が使えるマナを([0-9]+)つ持った状態で戦闘を開始する。?$")
S2_BOOST_RX = re.compile(
    r"^(" + JOBSEQ + r")の全ての必殺技が使えるマナを([0-9]+)つ持った状態で戦闘を開始"
    r"(?:する。?|し、(.+))$")
S2_USABLE_RX = re.compile(
    r"^(" + JOBSEQ + r")(?:で使用できる|の性質を持った)マナを([0-9]+)つ持った状態で戦闘を開始"
    r"(?:する。?|し、(.+))$")
HOLD_TRIGGER = re.compile(r"(?:所持|保持)している(?:と|場合)")
COUNT_RX = re.compile(
    r"(?:(?P<jobs>" + JOBWORD + r"(?:マナ)?(?:(?:と|か|、|または)" + JOBWORD + r"(?:マナ)?)*)"
    r"マナ|(?P<plain>マナ))が?(?P<dir>多い|少ない)ほど")
FLAVOR_RX = re.compile(r"^[^！？♪]*[！？♪]")
CONNECTIVES = ("また、", "また", "さらに")
PREFIX_TRIGGERS = ("Chain", "チェイン", "WAVE", "発動時", "使用すると", "倒した時", "倒すたび",
                   "止めを刺す", "地形", "マナスロット", "マナを獲得", "マナを消費",
                   "必要なマナ", "限界突破", "ピリカ")
RESIDUAL_WORDS = ("ダウン", "弾き飛ばし", "炎属性", "盾", "毒", "スロウ", "暗闇",
                  "状態異常", "追加する", "になる", "貫通", "追撃")
HP_HEAL_RX = re.compile(r"HP[^。、]{0,6}?(?:回復|徐々に)")

PARAM6_TEXT = {
    0: "param6=0：仅当装载期 CharaBehavior._isActive 非 0 时生效（装载流程未在逐卡证据中确认）",
    1: "param6=1：恒生效分支",
    2: "param6=2：仅当装载期 _isActive 为 0 时生效",
}
UNKNOWNS_START = [
    "实机装载/开局流程是否逐卡满足 param6 条件（本批不验证实机）",
    "最终战斗数值（本答案只给开局授予数量）",
]
UNKNOWNS_BOOST = [
    "param5/isBoost 的业务含义未证（只登记标志=1，不写「使える必殺技が増える」）",
    "实机装载/开局流程是否逐卡满足 param6 条件（本批不验证实机）",
    "最终战斗数值（本答案只给开局授予数量）",
]
UNKNOWNS_HOLD = [
    "触发条件的战斗内判定时机（当前玛那计数）未做实机验证",
    "同串其它子句（机制/属性/追加效果）未在本答案覆盖",
    "最终战斗数值（本答案只给系数原值）",
]
UNKNOWNS_COUNT = [
    "玛那计数的实时取值与 WAVE 内覆盖时机未做实机验证",
    "同串其它子句（耐久/间隔/机制）未在本答案覆盖",
    "最终战斗数值（本答案只给系数原值）",
]

EVIDENCE_BASE = [
    "output/character_skills/profiles/rules.json",
    "output/character_skills/skilllist_types/native_checks.json",
    "output/character_skills/type26_mana/native_evidence.json",
]

# ---------------------------------------------------------------------------
# 唯一新增规则键（主持裁决②）：skilllist|26|/param5 条件/标志语义
# 与 rules.py::_mana_b_param5_dictionary 同源（单一事实来源）。
# ---------------------------------------------------------------------------
PARAM5_KEY = "skilllist|26|/param5"
PARAM5_CONDITIONS = (
    "type26 记录进入 PlayerManager.PartyAbilityInit 的 ManaGet 分支；"
    "param0 产线把 (param5==1) 作为 isBoost 传给 ProduceManaForce；"
    "param4 产线的「属性标志」=(param5==1)（既有 /param4 conversion 同述）；"
    "本键只作条件/标志，不单独产生数量。"
)
RULE_ADDITIONS = {
    PARAM5_KEY: {
        "table": "skilllist",
        "effect_type": 26,
        "field_path": "/param5",
        "meaning_zh": "属性／必杀 boost 标志（param5==1）",
        "unit": "标志（float32(param5) == 1.0，精确相等）",
        "conversion": ("float32(param5)==1 时：param0 产线把 isBoost=true 传给 "
                       "ProduceManaForce；param4 产线把属性标志置 1。其余值不作 boost。"),
        "base_definition": None,
        "target": None,
        "conditions": PARAM5_CONDITIONS,
        "applicability": PARAM5_CONDITIONS,
        "evidence": [
            {"report": "output/character_skills/type26_mana/native_evidence.json",
             "scope": "slices[5]：0x158ca94 fmov s9,#1.0；0x158cab0 bl get_param5；"
                      "0x158cbb4 fcmp s8,s9；0x158cbb8 cset w2,eq；0x158cbc8 bl ProduceManaForce"},
            {"report": "output/character_skills/type26_mana/README.md",
             "scope": "isBoost=(param5==1)（README 原文；不从名称外推业务含义）"},
            {"report": "output/character_skills/profiles/rules.json",
             "scope": "skilllist|26|/param4 conversion「属性标志=(param5==1)」"},
        ],
        "status": "类型级推断（既有原生片段已证 param0 产线传 isBoost；不升确认；业务含义未证）",
        "limits": ("不写「使える必殺技が増える」等业务含义；不证明逐卡装载；"
                   "不单独作为数值答案；occurrences 未登记（条件键）。"),
        "occurrences": None,
        "origin": "scripts/character_skills/card_page_inference_mana_b.py::RULE_ADDITIONS",
    },
}
RULE_JSON_FIELDS = ("table", "effect_type", "field_path", "meaning_zh", "unit", "conversion",
                    "base_definition", "target", "conditions", "evidence", "status", "limits",
                    "occurrences", "origin")


def apply_rule_additions(rules: dict) -> tuple[dict, dict]:
    """把 RULE_ADDITIONS 并入一份 rules 映射副本（只新增缺失键；已存在必须逐字段相等）。"""
    out = json.loads(json.dumps(rules, ensure_ascii=False))
    log = {"added": [], "identical": [], "conflict": []}
    for key, patch in RULE_ADDITIONS.items():
        shaped = {k: v for k, v in patch.items() if k in RULE_JSON_FIELDS}
        if key not in out:
            out[key] = shaped
            log["added"].append(key)
            continue
        if all(out[key].get(k) == v for k, v in shaped.items()):
            log["identical"].append(key)
        else:
            log["conflict"].append(key)
    if log["conflict"]:
        raise RuntimeError("param5 规则键已存在且内容不同，拒绝静默覆盖：%s" % log["conflict"])
    return out, log


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def _norm(text):
    s = (text or "").replace("◆", "").replace("\\n", "").replace("\n", "")
    return re.sub(r"\s+", "", s.translate(FLAT))


def _strip_flavor(text):
    pref, t = "", text
    while True:
        m = FLAVOR_RX.match(t)
        if not m:
            break
        seg, rest = t[:m.end()], t[m.end():]
        if any(w in rest for w in ("マナ", "必殺技")):
            return pref + seg, rest
        pref, t = pref + seg, rest
    return pref, t


def _finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _int_slot(rec, slot):
    v = (rec or {}).get(slot)
    if not _finite(v):
        return None
    return int(v)


def _is_boost(rec):
    """N01（第二周期整改）：与原生一致的 float==1.0 判定。

    原生 0x158cab0 bl get_param5 → 0x158cbb4 fcmp s8,s9（s9=1.0）→ 0x158cbb8 cset w2,eq；
    不做整数化，因此 1.5／1.999 等不等于 1.0 的值**不是** boost（旧 ``int(param5)==1`` 会误收）。
    """
    v = (rec or {}).get("param5")
    return _finite(v) and float(v) == 1.0


def _skill_entry(data, sid, layer=None):
    try:
        sid = int(sid)
    except (TypeError, ValueError):
        return None
    for want, table, path in (("CACHE", getattr(data, "cache_skill", None),
                               "skilllist.data5.json.raw"),
                              ("APK", getattr(data, "apk_skill", None), "_mdSkill.json")):
        if table is None or (layer and layer != want):
            continue
        hit = table.get(sid)
        if hit is None:
            continue
        idx, row = hit
        return dict(resolved=True, table="skilllist", reference_id=sid, record=row,
                    layer=want, source=dict(
                        source_key="%s/%s" % (want, path), json_pointer="/skilllist/%d" % idx,
                        layer=want, record_key="%s/%s#/skilllist/%d" % (want, path, idx)))
    try:
        return data.skill(sid)
    except (AttributeError, TypeError, ValueError):
        return None


def _expand(data, sid, maxhop=3):
    entry = _skill_entry(data, sid)
    chain = []
    for _ in range(maxhop):
        if entry is None:
            return None, chain, "TARGET_MISSING"
        rec = entry.get("record") or {}
        if rec.get("ability") != 1082:
            return entry, chain, None
        s0 = str(rec.get("str0") or "").strip()
        chain.append({"wrapper": rec.get("skillid"), "str0": s0})
        if not s0.lstrip("-").isdigit() or int(s0) < 1:
            return None, chain, "STR0_INVALID"
        entry = _skill_entry(data, int(s0))
    return None, chain, "WRAPPER_DEPTH"


def resolve_carriers(data, table, record, layer=None):
    out, issues = [], []
    rec = record or {}
    if table == "skilllist":
        entry = _skill_entry(data, rec.get("skillid"), layer)
        if entry is None or entry.get("record") != rec:
            issues.append("OWN_RECORD_MISMATCH")
            return out, issues
        out.append({"record_id": entry.get("reference_id"), "record": rec, "layer": entry.get("layer"),
                    "role": "own", "wrapper_chain": []})
        for sid in rec.get("sub") or []:
            sub, chain, broken = _expand(data, sid)
            if sub is None:
                issues.append("SUB_FORWARD_BROKEN:%s:%s" % (sid, broken))
                continue
            out.append({"record_id": sub.get("reference_id"), "record": sub["record"],
                        "layer": sub.get("layer"), "role": "sub", "wrapper_chain": chain})
    elif table == "extra_ability_info":
        for sid in rec.get("skill_ids") or []:
            target, chain, broken = _expand(data, sid)
            if target is None:
                issues.append("CONTAINER_FORWARD_BROKEN:%s:%s" % (sid, broken))
                continue
            out.append({"record_id": target.get("reference_id"), "record": target["record"],
                        "layer": target.get("layer"), "role": "container",
                        "wrapper_chain": chain})
    elif table == "supporterskill":
        for sid in (rec.get("abi0"), rec.get("abi1")):
            if sid in (None, 0, "0"):
                continue
            target, chain, broken = _expand(data, sid)
            if target is None:
                issues.append("SUPPORT_FORWARD_BROKEN:%s:%s" % (sid, broken))
                continue
            out.append({"record_id": target.get("reference_id"), "record": target["record"],
                        "layer": target.get("layer"), "role": "container",
                        "wrapper_chain": chain})
    return out, issues


def _dedupe(carriers):
    seen, out = set(), []
    for c in carriers:
        key = (c["record_id"], c.get("layer"))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _record_job(data, cid):
    """卡页职业取数与 card_page_data.basic 同口径：CACHE 整条记录优先，缺失不回退 APK。"""
    rec = data.cache_chara.get(cid, data.apk_chara.get(cid)) if data is not None else None
    return (rec or {}).get("jobtype")


def _job_bitmap(jobs):
    bits = 0
    for j in jobs:
        bits |= JOB_BITS[j]
    return bits


def _jobs_in(text):
    out = []
    for j in sorted(JOB_BITS, key=lambda x: text.find(x) if x in text else 999):
        if j in text and j not in out:
            out.append(j)
    # 按出现顺序更稳
    out = sorted(out, key=lambda x: text.find(x))
    return out


def _base_text(record, text):
    """父记录文本中本行之前的「基础句」；找不到本行文本返回 (None, -1)。"""
    rt, st = _norm(record.get("text") or record.get("sinfo") or ""), _norm(text)
    if not st:
        return None, -1
    pos = rt.find(st)
    if pos < 0:
        return None, -1
    return rt[:pos], pos


def _effects_in_text(text):
    return {eff for w, eff in EFFECT_WORDS.items() if w in text}


def _last_sentence(text):
    """「効果」展开只用紧邻本行的基础句（最后一句），不把更早的无关片段算入。"""
    return (text or "").rstrip("。").rsplit("。", 1)[-1]


def _jobs_before_mana(text):
    out = []
    for m in re.finditer(r"(" + JOBSEQ + r")(?:マナ)?", text or ""):
        for j in _jobs_in(m.group(1)):
            if j not in out:
                out.append(j)
    return out


def _has_kaburu(text):
    # 「効果が上がる/上昇」才是一般效果；「ダウンの効果を追加」等机制句不算。
    return bool(re.search(r"効果(?:が|も)?(?:上が|上昇|増)", text or ""))


# ---------------------------------------------------------------------------
# S1 / S2 句式分类
# ---------------------------------------------------------------------------
def classify_start(text):
    raw = str(text or "").strip()
    if not raw:
        return {"rejection": "EMPTY_TEXT"}
    t = raw.translate(FLAT)
    pref, t = _strip_flavor(t)
    conn = ""
    for c in CONNECTIVES:
        if t.startswith(c):
            conn, t = c, t[len(c):]
            break
    m = S1_RX.match(t)
    if m:
        return {"family": "start_boost", "number": int(m.group(1)), "jobs": [],
                "subform": "boost_all", "prefix": pref + conn, "residual": None}
    m = S2_BOOST_RX.match(t)
    if m:
        return {"family": "start_job", "number": int(m.group(2)), "jobs": _jobs_in(m.group(1)),
                "subform": "boost_job", "prefix": pref + conn,
                "residual": (m.group(3) or "").strip() or None}
    m = S2_USABLE_RX.match(t)
    if m:
        return {"family": "start_job", "number": int(m.group(2)), "jobs": _jobs_in(m.group(1)),
                "subform": "usable", "prefix": pref + conn,
                "residual": (m.group(3) or "").strip() or None}
    if "マナ" in raw and "戦闘を開始" in raw:
        return {"rejection": "START_SENTENCE_UNVERIFIED", "detail": raw[:60]}
    return {"rejection": "NOT_START_CLAIM"}


# ---------------------------------------------------------------------------
# S3 / S4 子句解析
# ---------------------------------------------------------------------------
def parse_hold_segments(text):
    """返回 (segments, issues)。segment=dict(cond, effects, direction, numbers, snippet)。"""
    t = _norm(text)
    marks = list(HOLD_TRIGGER.finditer(t))
    if not marks:
        return [], ["NO_HOLD_TRIGGER"]
    segs, issues = [], []
    for i, m in enumerate(marks):
        start = marks[i - 1].end() if i else 0
        prefix = t[start:m.start()]
        # 条件前缀：去掉连接词/尾部「マナを」
        p = prefix
        for c in CONNECTIVES:
            p = p.replace(c, "")
        p = p.strip("、")
        body = p
        if body.endswith("を"):
            body = body[:-1]
        if body.endswith("マナ"):
            body = body[:-2]
        cond, cond_issue = _parse_condition(body)
        if cond_issue:
            issues.append(cond_issue)
            cond = None
        end = marks[i + 1].start() if i + 1 < len(marks) else len(t)
        seg = t[m.end():end]
        eff = _parse_effect_segment(seg)
        segs.append(dict(cond=cond, snippet=t[start:end], **eff))
    if not segs:
        return [], ["NO_SEGMENT"]
    return segs, issues


def _parse_condition(body):
    jobs = _jobs_in(body)
    if re.search(r"[0-9０-９]", body) and not re.search(r"[0-9０-９]+つ以上", body):
        return None, "THRESHOLD_TEXT_UNSUPPORTED"
    threshold = 1
    m = re.search(r"([0-9０-９]+)つ以上", body)
    if m:
        threshold = int(m.group(1).translate(FLAT))
        if threshold < 1:
            return None, "THRESHOLD_TEXT_UNSUPPORTED"
    alljob = "全ての職業" in body
    both = "両方" in body
    excl = "以外" in body
    dten = "天魔" in body
    if alljob and dten:
        return None, "CONDITION_COMPOSITE_UNSUPPORTED"
    if both:
        return {"mode": "both", "jobs": [], "andor": "and", "bitmap": None,
                "threshold": threshold}, None
    if alljob:
        return {"mode": "all", "jobs": [JOB_NAMES[b] for b in (1, 2, 4, 8, 16)],
                "andor": "and", "bitmap": 31, "threshold": threshold}, None
    if not jobs:
        return {"mode": "any", "jobs": [], "andor": "or", "bitmap": 31,
                "threshold": threshold}, None
    if excl:
        if len(jobs) != 1:
            return None, "EXCL_MULTI_JOB_UNSUPPORTED"
        return {"mode": "excl", "jobs": jobs, "andor": "or",
                "bitmap": 31 & ~JOB_BITS[jobs[0]], "threshold": threshold}, None
    andor = "or"
    return {"mode": "jobs", "jobs": jobs, "andor": andor,
            "bitmap": _job_bitmap(jobs), "threshold": threshold}, None


def _parse_effect_segment(seg):
    direction = None
    if any(w in seg for w in ("下がる", "下がり", "下げる", "減少")):
        direction = "down"
    elif any(w in seg for w in ("上がる", "上がり", "上昇", "上げる", "増える")):
        direction = "up"
    effects, numbers = [], {}
    for w, eff in EFFECT_WORDS.items():
        if w in seg and eff not in effects:
            effects.append(eff)
    for part in re.split(r"[、。]", seg):
        for w, eff in EFFECT_WORDS.items():
            if w in part:
                m = re.search(r"([0-9]+)%", part)
                if m:
                    if eff in numbers:
                        return {"effects": effects, "numbers": numbers, "direction": direction,
                                "issue": "NUMBER_DUPLICATE"}
                    numbers[eff] = int(m.group(1))
    return {"effects": effects, "numbers": numbers, "direction": direction, "kaburu": _has_kaburu(seg)}


def parse_count_clause(text):
    """S4：返回 (cond, effects, direction, numbers, snippet) 或 rejection。"""
    t = _norm(text)
    if "マナスロット" in t:
        return {"rejection": "COUNT_OBJECT_SLOT_UNVERIFIED"}
    m = COUNT_RX.search(t)
    if not m:
        return {"rejection": "NOT_COUNT_CLAIM"}
    jobs = _jobs_in(m.group("jobs") or "")
    cond = {"mode": "jobs" if jobs else "any", "jobs": jobs,
            "bitmap": _job_bitmap(jobs) if jobs else 31,
            "andor": "or"}
    seg = t[m.end():]
    eff = _parse_effect_segment(seg)
    return dict(cond=cond, count_dir=("more" if m.group("dir") == "多い" else "less"),
                snippet=t[m.start():], prefix=t[:m.start()], **eff)


# ---------------------------------------------------------------------------
# 槽位工具
# ---------------------------------------------------------------------------
def _nonneutral80(rec):
    out = {}
    for slot, eff in SLOT_EFFECT.items():
        v = rec.get(slot)
        if not _finite(v):
            if v is not None:
                return None, "VALUE_NOT_FINITE:%s" % slot
            continue
        neutral = 1.0 if slot in ("param1", "param2", "param3") else 0.0
        if float(v) != neutral:
            out[slot] = float(v)
    return out, None


def _nonneutral96(rec):
    out = {}
    for slot in ("param2", "param3", "param4", "param5", "param6", "param7"):
        v = rec.get(slot)
        if not _finite(v):
            if v is not None:
                return None, "VALUE_NOT_FINITE:%s" % slot
            continue
        if float(v) != 0.0:
            out[slot] = float(v)
    return out, None


def _sign_ok80(slot, value, direction):
    if direction is None:
        return False
    if slot in ("param1", "param2"):
        return value > 1.0 if direction == "up" else 0.0 < value < 1.0
    if slot == "param3":
        return 0.0 < value < 1.0 if direction == "up" else value > 1.0
    if slot in ("param7", "param8"):
        return value > 0.0 if direction == "up" else value < 0.0
    return False


def _sign_ok96(slot, value, direction, count_dir):
    if direction is None:
        return False
    # 「多いほど攻撃力が上がる」→ 系数为正；「少ないほど上がる」→ 系数为负。
    sign = 1 if direction == "up" else -1
    if count_dir == "less":
        sign = -sign
    if slot in ("param2", "param3", "param4", "param6", "param7"):
        return value * sign > 0.0
    if slot == "param5":  # 受伤量乘数：防御力「上がる」→ 系数为负（受伤减少）
        return value * sign < 0.0
    return False


def _number_ok80(slot, value, direction, number):
    if number is None:
        return True
    want = number / 100.0
    if slot in ("param1", "param2"):
        target = 1.0 + (want if direction == "up" else -want)
    elif slot == "param3":
        target = 1.0 - (want if direction == "up" else -want)
    elif slot in ("param7", "param8"):
        target = want if direction == "up" else -want
    else:
        return False
    return abs(value - target) <= 1e-6


# ---------------------------------------------------------------------------
# 答案构造
# ---------------------------------------------------------------------------
def _claim_record_id(record, table, cid=None):
    if table in ("supporterskill", "extra_ability_info"):
        return cid
    return (record or {}).get("skillid")


def _carrier_source(data, carrier):
    entry = _skill_entry(data, carrier["record_id"], carrier.get("layer")) or {}
    src = copy.deepcopy(entry.get("source") or {})
    src.update({"table": "skilllist", "record_id": carrier["record_id"],
                "field_path": "/" + carrier["slot"] if carrier.get("slot") else None})
    return src


def build_start_answer(data, table, reference_field, record, text, carrier, cls, card_job,
                       cid=None):
    rec = carrier["record"]
    fam = cls["family"]
    number = cls["number"]
    slot = "param4" if (fam == "start_boost" or int(rec.get("param4") or 0) > 0) else "param0"
    rule_key = "skilllist|26|/" + slot
    src = _carrier_source(data, dict(carrier, slot=slot))
    mask = rec.get("iParam1") if slot == "param4" else None
    boost = _is_boost(rec)
    p6 = _int_slot(rec, "param6")
    jobs = cls.get("jobs") or []
    jobtxt = "・".join(jobs) if jobs else "（句面未限职业）"
    if fam == "start_boost":
        value = "战斗开始时获得 %d 个「全ての必殺技が使える」玛那（param4 产线；iParam1=31 全职业；param5=1 isBoost）" % number
        target = "持有者；开戦时授予有效 PanelManaGage"
        cond = ("战斗开始时；type26 param4 分支；职业旗标 iParam1=31（全职业）；"
                "param5=1（isBoost 标志，类型级推断）；" + PARAM6_TEXT.get(p6, "param6=未知"))
        unknowns = UNKNOWNS_BOOST
        qk = "开局玛那数量"
    elif slot == "param4":
        value = ("战斗开始时获得 %d 个仅限 %s 使用的玛那（param4 产线；iParam1=%d%s）"
                 % (number, jobtxt, mask or 0, "；param5=1 isBoost" if boost else ""))
        target = "持有者；按 iParam1 位图展开为职业旗标"
        cond = ("战斗开始时；type26 param4 分支；职业位图 iParam1=%d＝句面「%s」；%s；%s"
                % (mask or 0, jobtxt,
                   "param5=1（isBoost 标志，类型级推断）" if boost else "param5=0/缺（非 boost）",
                   PARAM6_TEXT.get(p6, "param6=未知")))
        unknowns = UNKNOWNS_BOOST if boost else UNKNOWNS_START
        qk = "开局玛那数量"
    else:
        value = ("战斗开始时按持有者职业（%s）获得 %d 个「全ての必殺技が使える」玛那"
                 "（param0 产线；param5=1 isBoost）" % (card_job, number))
        target = "持有者职业（_jobType=%s）；开戦时授予有效 PanelManaGage" % card_job
        cond = ("战斗开始时；type26 param0 分支；职业取持有者 _jobType=%s（卡页 jobtype 核对）；"
                "param5=1（isBoost 标志，类型级推断）；%s"
                % (card_job, PARAM6_TEXT.get(p6, "param6=未知")))
        unknowns = UNKNOWNS_BOOST
        qk = "开局玛那数量"
    note_parts = []
    if fam == "start_job" and slot == "param4" and boost:
        note_parts.append("同句带「全ての必殺技が使える」且 param5=1；boost 标志与句面一致")
    if slot == "param0" and rec.get("iParam0") not in (None, 0):
        note_parts.append("同记录另带 iParam0=%s（第三套槽位 getter；param1=0 时产线 0 次，"
                          "本批不消费其语义）" % rec.get("iParam0"))
    if cls.get("residual"):
        note_parts.append("同句另有未被本批覆盖的子句「%s」，行拆分标志保留" % cls["residual"])
    if cls.get("prefix"):
        note_parts.append("前置为角色台词/接续词，不构成效果子句")
    fields = [{"f": "/" + slot, "raw": float(rec.get(slot)), "value": value, "kind": qk,
               "unit": "个", "status": "CONFIRMED_NUMERIC",
               "evidence_scope": "BY_TYPE_EXTRAPOLATED", "rule_key": rule_key,
               "table": "skilllist", "record_id": carrier["record_id"]}]
    flag_fields = []
    if boost:
        flag_fields.append({"f": "/param5", "raw": float(rec.get("param5")), "value": "isBoost=1",
                            "kind": "属性/boost 标志", "unit": "标志",
                            "status": "INFERRED_NOT_CONFIRMED",
                            "evidence_scope": "BY_TYPE_EXTRAPOLATED",
                            "rule_key": PARAM5_KEY, "table": "skilllist",
                            "record_id": carrier["record_id"]})
    binding = {
        "template_id": "type26_%s_%s" % (slot, cls["subform"]),
        "strength": ("既有规则槽位已确认数值换算；句面→记录归属逐行结构门控＋原文数字一致，"
                     "证据档推断；不是机器码解析日文"),
        "status": "推断（句面→载体槽位；数值换算已确认）",
        "target": target,
        "condition": cond,
        "duration": "开局一次授予；不是持续时间或每WAVE",
        "rationale": ("原文只有开局玛那主张；载体 %s 的 %s 原值整数化＝原文数字；"
                      "其它产线/类型载体不参与本值" % (carrier["record_id"], slot)),
        "source": src,
        "claim": {"table": table,
                  "record_id": _claim_record_id(record, table, cid),
                  "reference_field": reference_field, "text": text},
        "fields": fields + flag_fields,
        "unknowns": list(unknowns),
        "mana_b_binding": {"scope": SCOPE, "family": fam, "slot": slot,
                           "subform": cls["subform"], "is_boost": boost},
    }
    return {
        "value": value,
        "quantity_kind": qk,
        "unit": "个",
        "raw_value": float(rec.get(slot)),
        "field_path": "/" + slot,
        "rule_key": rule_key,
        "table": "skilllist",
        "record_id": carrier["record_id"],
        "layer": carrier["layer"],
        "source": src,
        "context": text,
        "numeric_source": "规则",
        "numeric_evidence": "确认",
        "association_evidence": "推断",
        "answer_status": "CONFIRMED_NUMERIC",
        "evidence_scope": "BY_TYPE_EXTRAPOLATED",
        "quantitative": True,
        "condition_label": "战斗开始时 / %s" % slot,
        "conditions": cond,
        "target": target,
        "note": "；".join(note_parts) if note_parts else None,
        "conversion": value,
        "binding": binding,
        "evidence": list(EVIDENCE_BASE),
    }


def _value80(eff, slot, v, cond_txt, direction="up"):
    if eff == "attack":
        return "攻击力 ×%g（%s）" % (v, cond_txt), "倍率"
    if eff == "move":
        return "移动速度 ×%g（%s）" % (v, cond_txt), "速度倍率"
    if eff == "defence":
        return ("受伤量 ×%g（防御力%s；%s）" % (v, "上升" if direction == "up" else "下降", cond_txt),
                "受伤量倍率")
    if eff == "crit_rate":
        return "暴击率 +%g 百分点（%s）" % (v * 100.0, cond_txt), "百分点"
    return "暴击伤害系数 +%g（%s）" % (v, cond_txt), "系数增量"


def _value96(eff, slot, v, cond_txt, cap, direction="up"):
    if eff == "attack":
        kind = "必杀技伤害" if slot == "param3" else "非必杀技伤害"
        return ("攻击力 ×(1 + %g × min(玛那数, %d))（%s；%s）"
                % (v, cap, cond_txt, kind), "倍率")
    if eff == "move":
        return "移动速度 ×(1 + %g × min(玛那数, %d))（%s）" % (v, cap, cond_txt), "速度倍率"
    if eff == "defence":
        return ("受伤量 ×(1 + (%g) × min(玛那数, %d))（防御力%s；%s）"
                % (v, cap, "上升" if direction == "up" else "下降", cond_txt), "受伤量倍率")
    if eff == "crit_rate":
        return ("暴击率 +(%g) × min(玛那数, %d) × 100 百分点（%s）"
                % (v, cap, cond_txt), "百分点")
    return "暴击伤害系数 +(%g) × min(玛那数, %d)（%s）" % (v, cap, cond_txt), "系数增量"


def build_slot_answer(data, table, reference_field, record, text, carrier, slot, eff,
                      direction, cls, cond_txt, target, cap=None, cid=None, extra_note=None):
    """构造 80/96 系数槽答案。

    R01 整改（2026-10-26，第二周期第三方审查）：说明按 **type／slot／实际运算／增减方向**
    分别生成——
      * type80 /param1,/param2,/param3 为 fmul 乘算（攻/移/受伤量倍率），条件写「乘入」；
      * type80 /param7（概率 pp）与 /param8（暴伤系数）原生为 fadd 加算，条件写「加算」；
      * /param3 的 Skill 必杀/非必杀择槽注记**仅属 type96**；type80 /param3 是受伤量倍率，
        /param2 是移动速度乘数，不得借用该注记；
      * 防御注记的方向按实际增减生成（受伤量乘数 <1＝防御上がる；>1＝防御下がる）。
    """
    rec = carrier["record"]
    v = float(rec.get(slot))
    semantic = carrier["semantic"]
    if semantic == "80":
        rule_key = "skilllist|80|/%s" % slot
        value, unit = _value80(eff, slot, v, cond_txt, direction)
        conversion = value
        if eff in ("crit_rate", "crit_dmg"):
            how = "加算（%s）" % ("百分点" if eff == "crit_rate" else "系数增量")
        else:
            how = "乘入"
        cond = ("玛那条件成立（当前玛那 ≥ %d；职业位图 iParam0=%d；%s）；"
                "条件成立时该项按原值%s" % (int(rec.get("param0") or 0),
                                       int(rec.get("iParam0") or 0),
                                       "and（全部命中）" if int(rec.get("param6") or 0) != 0 else "or（任一命中）",
                                       how))
        unknowns = UNKNOWNS_HOLD
        qk = EFFECT_ZH[eff]
        template = "80_%s" % eff
        native_path = "ManaHold.%s" % slot
    else:
        rule_key = "skilllist|96|/%s" % slot
        value, unit = _value96(eff, slot, v, cond_txt, cap, direction)
        conversion = value
        cond = ("计数对象：iParam0=%d 经 ConvJobFlagToElementFlag 的当前玛那（int(param0)==0 时为"
                "斯库拉普玛那）；计数 ≥1 生效，按 min(计数, int(param1)=%d) 计入；%s"
                % (int(rec.get("iParam0") or 0), cap, cond_txt))
        unknowns = UNKNOWNS_COUNT
        qk = EFFECT_ZH[eff]
        template = "96_%s" % eff
        native_path = "ManaCountUp.%s" % slot
    src = _carrier_source(data, dict(carrier, slot=slot))
    note_parts = []
    if eff == "defence":
        # 实际增减方向：type80 /param3 为受伤量直接乘数（<1 受伤减少）；type96 /param5 为
        # 受伤量系数（1+v×min），v<0 才是受伤减少。均按受伤量乘数表述，不写固定防御量。
        up = (v < 1.0) if semantic == "80" else (v < 0.0)
        note_parts.append("防御力「%s」按受伤量乘数 %s 表述（规则 %s 语义），不是固定防御量"
                          % ("上がる" if up else "下がる", "<1" if up else ">1",
                             "param3" if semantic == "80" else "param3/param5"))
    if slot == "param3":
        if semantic == "96":
            note_parts.append("param3 是 Skill(必杀技) 伤害档；非必杀档见同行 /param2")
        else:
            note_parts.append("type80 /param3 是受伤量倍率（不是必杀技伤害档；"
                              "type80 /param2 是移动速度乘数）")
    if extra_note:
        note_parts.append(extra_note)
    fields = [{"f": "/" + slot, "raw": v, "value": value, "kind": qk, "unit": unit,
               "status": "CONFIRMED_NUMERIC", "evidence_scope": "BY_TYPE_EXTRAPOLATED",
               "rule_key": rule_key, "table": "skilllist",
               "record_id": carrier["record_id"], "semantic_effect": EFFECT_ZH[eff],
               "native_path": native_path}]
    binding = {
        "template_id": "%s_%s" % (template, cls["family"]),
        "strength": ("既有规则槽位已确认数值换算；子句→槽位由逐行结构门控（职业位图/and-or/"
                     "方向/原值数字）绑定，证据档推断"),
        "status": "推断（子句→载体槽位；数值换算已确认）",
        "target": target,
        "condition": cond,
        "duration": "常时（玛那条件成立期间）" if cls["family"] == "hold_mana" else "随玛那计数持续（WAVE 内覆盖未验证）",
        "rationale": ("原文子句「%s」对应槽 %s；载体 %s 原值 %g；同串其它类型/记录不参与本值"
                      % (cls.get("snippet", "")[:40], slot, carrier["record_id"], v)),
        "source": src,
        "claim": {"table": table, "record_id": _claim_record_id(record, table, cid),
                  "reference_field": reference_field, "text": text},
        "fields": fields,
        "unknowns": list(unknowns),
        "mana_b_binding": {"scope": SCOPE, "family": cls["family"], "slot": slot,
                           "record_id": carrier["record_id"]},
    }
    return {
        "value": value,
        "quantity_kind": qk,
        "unit": unit,
        "raw_value": v,
        "field_path": "/" + slot,
        "rule_key": rule_key,
        "table": "skilllist",
        "record_id": carrier["record_id"],
        "layer": carrier["layer"],
        "source": src,
        "context": text,
        "numeric_source": "规则",
        "numeric_evidence": "确认",
        "association_evidence": "推断",
        "answer_status": "CONFIRMED_NUMERIC",
        "evidence_scope": "BY_TYPE_EXTRAPOLATED",
        "quantitative": True,
        "condition_label": "%s / %s" % (cls["family"], slot),
        "conditions": cond,
        "target": target,
        "note": "；".join(note_parts) if note_parts else None,
        "conversion": conversion,
        "binding": binding,
        "evidence": list(EVIDENCE_BASE),
    }


# ---------------------------------------------------------------------------
# 逐行评估
# ---------------------------------------------------------------------------
def _result(table, reference_field, text):
    return {"scope": SCOPE, "table": table, "reference_field": reference_field,
            "text": text, "gates": {}, "accepted": False, "rejection": None,
            "detail": None, "family": None, "answers": []}


def _reject(res, code, detail=None):
    res["rejection"] = code
    if detail is not None:
        res["detail"] = detail
    return res


def _param6_code(rec):
    v = (rec or {}).get("param6")
    if v in (None, ""):
        return 0, None
    if not _finite(v):
        return None, "PARAM6_UNREADABLE"
    code = int(float(v))
    if code not in PARAM6_TEXT:
        return code, "PARAM6_INACTIVE"
    return code, None


def _already(row_answers, rule_key, record_id, field_path):
    for a in row_answers or []:
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
    t = str(text or "").strip().translate(FLAT)
    if not t:
        return _reject(res, "EMPTY_TEXT")
    if "マナ" not in t:
        return _reject(res, "NOT_MANA_CLAIM")
    # 时机词（句式主张之前）
    prefix = t.split("マナ")[0] if "マナ" in t else ""
    hit = [w for w in PREFIX_TRIGGERS if w in prefix]
    if hit:
        return _reject(res, "TIMING_MISMATCH", hit)
    cls = classify_start(t)
    if cls.get("family"):
        res["family"] = cls["family"]
        return _evaluate_start(data, table, reference_field, record, text, cls,
                               existing_answers, cid, res)
    if cls.get("rejection") not in ("NOT_START_CLAIM",):
        res["gates"]["start_rejection"] = cls
    if HOLD_TRIGGER.search(_norm(t)):
        res["family"] = "hold_mana"
        return _evaluate_hold(data, table, reference_field, record, text,
                              existing_answers, cid, res)
    if COUNT_RX.search(_norm(t)) or "ほど" in _norm(t):
        res["family"] = "mana_count_up"
        return _evaluate_count(data, table, reference_field, record, text,
                               existing_answers, cid, res)
    return _reject(res, "NOT_IN_SCOPE_FAMILY")


def _verify_text(record, text):
    base, pos = _base_text(record, text)
    return base, pos


def _evaluate_start(data, table, reference_field, record, text, cls, existing_answers, cid, res):
    fam = cls["family"]
    num = cls["number"]
    carriers, issues = resolve_carriers(data, table, record, layer=None)
    res["gates"]["carrier_issues"] = issues
    c26 = _dedupe([c for c in carriers if c.get("record") == c.get("record")
                   and (c.get("record") or {}).get("ability") == 26])
    res["gates"]["sibling_mana_types"] = sorted({(c.get("record") or {}).get("ability")
                                                 for c in carriers
                                                 if (c.get("record") or {}).get("ability")
                                                 in (26, 28, 80, 96, 1106, 1110, 1111)})
    if not c26:
        return _reject(res, "NO_TYPE26_CARRIER")
    # 选载体：S1 -> param4；S2 -> param0 或 param4
    p4 = [c for c in c26 if (_int_slot(c["record"], "param4") or 0) > 0]
    p0 = [c for c in c26 if (_int_slot(c["record"], "param0") or 0) > 0]
    if fam == "start_boost":
        cand = p4
        slot = "param4"
    else:
        if p0 and p4:
            ids = sorted({c["record_id"] for c in p0 + p4})
            if len(ids) > 1:
                return _reject(res, "MULTI_CARRIER_AMBIGUOUS", ids)
        if p0:
            cand, slot = p0, "param0"
        elif p4:
            cand, slot = p4, "param4"
        else:
            return _reject(res, "VALUE_MISMATCH",
                           [(_id, {k: (c["record"] or {}).get(k) for k in ("param0", "param4")})
                            for c in c26 for _id in [c["record_id"]]])
    if len({c["record_id"] for c in cand}) != 1:
        return _reject(res, "MULTI_CARRIER_AMBIGUOUS",
                       [c["record_id"] for c in cand])
    carrier = cand[0]
    rec = carrier["record"]
    res["gates"]["slot"] = slot
    res["gates"]["carrier"] = {"record_id": carrier["record_id"], "layer": carrier["layer"],
                               "role": carrier["role"]}
    got = _int_slot(rec, slot)
    if got != num or got is None or got < 1:
        return _reject(res, "VALUE_MISMATCH", {"slot": slot, "raw": rec.get(slot), "text": num})
    # 产线互斥
    other = _int_slot(rec, "param4" if slot == "param0" else "param0")
    if (other or 0) > 0:
        return _reject(res, "COMPETING_START_LINE", {"other_slot_value": other})
    if _int_slot(rec, "param7") not in (None, 0):
        return _reject(res, "COMPETING_START_LINE", {"param7": rec.get("param7")})
    if _int_slot(rec, "param1") not in (None, 0):
        return _reject(res, "THIRD_SLOT_ACTIVE", {"param1": rec.get("param1")})
    mask = _int_slot(rec, "iParam1")
    boost = _is_boost(rec)
    p5 = rec.get("param5")
    res["gates"].update({"iParam1": mask, "param5": p5, "is_boost": boost})
    if slot == "param4":
        if fam == "start_boost":
            if mask != 31:
                return _reject(res, "JOB_MASK_NOT_ALL", mask)
            if not boost:
                return _reject(res, "FLAG_SENTENCE_MISMATCH",
                               {"sentence": "boost_all", "param5": p5})
        else:
            if not cls["jobs"]:
                return _reject(res, "JOB_SET_UNPARSED")
            want = _job_bitmap(cls["jobs"])
            if mask != want:
                return _reject(res, "JOB_SET_MISMATCH", {"sentence": want, "iParam1": mask})
            want_boost = cls["subform"] == "boost_job"
            if want_boost != boost:
                return _reject(res, "FLAG_SENTENCE_MISMATCH",
                               {"sentence": cls["subform"], "param5": p5})
    else:  # param0
        if len(cls["jobs"]) != 1:
            return _reject(res, "JOB_SET_UNPARSED", cls["jobs"])
        job = cls["jobs"][0]
        jobtype = _record_job(data, cid)
        if jobtype is None:
            return _reject(res, "CARD_JOBTYPE_MISSING", cid)
        if JOBTYPE_BITS.get(int(jobtype)) != JOB_BITS.get(job):
            return _reject(res, "CARD_JOB_MISMATCH",
                           {"jobtype": jobtype, "sentence": job})
        if cls["subform"] != "boost_job":
            return _reject(res, "FLAG_SENTENCE_MISMATCH",
                           {"sentence": cls["subform"], "param5": p5})
        if not boost:
            return _reject(res, "FLAG_SENTENCE_MISMATCH", {"sentence": "boost_job", "param5": p5})
        if (mask or 0) != 0:
            return _reject(res, "JOB_MASK_UNEXPECTED", mask)
        res["gates"]["card_job"] = job
        res["gates"]["card_jobtype"] = int(jobtype)
    code, p6err = _param6_code(rec)
    res["gates"]["param6"] = code
    if p6err:
        return _reject(res, p6err, rec.get("param6"))
    base, pos = _verify_text(record, text)
    res["gates"]["text_verified"] = pos >= 0
    if pos < 0:
        return _reject(res, "TEXT_UNVERIFIED")
    rule_key = "skilllist|26|/" + slot
    if _already(existing_answers, rule_key, carrier["record_id"], "/" + slot):
        return _reject(res, "ALREADY_ANSWERED", {"rule_key": rule_key,
                                                 "record_id": carrier["record_id"]})
    res["accepted"] = True
    res["answer"] = build_start_answer(data, table, reference_field, record, text, carrier,
                                       cls, res["gates"].get("card_job"), cid)
    res["answers"] = [res["answer"]]
    return res


def _evaluate_hold(data, table, reference_field, record, text, existing_answers, cid, res):
    raw = str(text or "")
    if HP_HEAL_RX.search(raw):
        return _reject(res, "HP_HEAL_SUBCLAUSE_EXCLUDED")
    segs, issues = parse_hold_segments(raw)
    if issues:
        return _reject(res, "HOLD_SEGMENT_" + issues[0], issues)
    carriers, cissues = resolve_carriers(data, table, record, layer=None)
    res["gates"]["carrier_issues"] = cissues
    c80 = _dedupe([c for c in carriers if (c.get("record") or {}).get("ability") == 80])
    res["gates"]["sibling_mana_types"] = sorted({(c.get("record") or {}).get("ability")
                                                 for c in carriers
                                                 if (c.get("record") or {}).get("ability")
                                                 in (26, 28, 80, 96, 1106, 1110, 1111)})
    if not c80:
        return _reject(res, "NO_TYPE80_CARRIER")
    base, pos = _verify_text(record, text)
    if pos < 0:
        return _reject(res, "TEXT_UNVERIFIED")
    base_effects = _effects_in_text(_last_sentence(base))
    prev_jobs = set(_jobs_before_mana(_last_sentence(base)))
    used = set()
    assignments = []
    for seg in segs:
        cond = seg["cond"]
        if cond["mode"] == "both":
            if not prev_jobs:
                return _reject(res, "BOTH_WITHOUT_ANTECEDENT")
            resolved = sorted(prev_jobs, key=lambda j: JOB_BITS[j])
            bitmap, andor = _job_bitmap(resolved), "and"
            seg["resolved_jobs"] = resolved
        else:
            bitmap, andor = cond["bitmap"], cond["andor"]
            prev_jobs |= set(cond.get("jobs") or [])
        effects = list(seg["effects"])
        if seg.get("kaburu"):
            if not base_effects:
                return _reject(res, "EFFECT_UNRESOLVED", seg["snippet"])
            for e in base_effects:
                if e not in effects:
                    effects.append(e)
        if not effects:
            res["gates"].setdefault("residual_segments", []).append(seg["snippet"])
            continue
        if seg["direction"] is None:
            return _reject(res, "DIRECTION_UNRESOLVED", seg["snippet"])
        claimed = set()
        for e in effects:
            claimed |= {E80_SLOT[e]} if e in E80_SLOT else set()
        want_p6 = 1 if andor == "and" else 0
        threshold = int(cond.get("threshold") or 1)
        pool = [c for c in c80
                if _int_slot(c["record"], "iParam0") == bitmap
                and int(_int_slot(c["record"], "param6") or 0) == want_p6
                and _int_slot(c["record"], "param0") == threshold]
        if not pool:
            near = [c for c in c80
                    if _int_slot(c["record"], "iParam0") == bitmap
                    and int(_int_slot(c["record"], "param6") or 0) == want_p6]
            if near:
                return _reject(res, "THRESHOLD_MISMATCH",
                               {"bitmap": bitmap, "andor": andor,
                                "param0": [c["record"].get("param0") for c in near],
                                "snippet": seg["snippet"]})
            return _reject(res, "NO_MATCHING_80",
                           {"bitmap": bitmap, "andor": andor, "snippet": seg["snippet"]})
        exact, reasons = [], []
        for c in pool:
            rec = c["record"]
            if int(_int_slot(rec, "param4") or 0) or int(_int_slot(rec, "param5") or 0):
                reasons.append((c["record_id"], "HP_HEAL_SLOTS"))
                continue
            nn, err = _nonneutral80(rec)
            if err:
                reasons.append((c["record_id"], err))
                continue
            if set(nn) != claimed:
                reasons.append((c["record_id"], "SLOT_SET", sorted(nn), sorted(claimed)))
                continue
            bad = [s for s, v in nn.items() if not _sign_ok80(s, v, seg["direction"])]
            if bad:
                reasons.append((c["record_id"], "SIGN", bad))
                continue
            if not all(_number_ok80(s, nn[s], seg["direction"], seg["numbers"].get(SLOT_EFFECT[s]))
                       for s in nn):
                reasons.append((c["record_id"], "NUMBER",
                                {s: nn[s] for s in nn}, seg["numbers"]))
                continue
            exact.append(c)
        if len({c["record_id"] for c in exact}) != 1:
            if not exact:
                return _reject(res, "SLOT_CLAUSE_MISMATCH",
                               {"snippet": seg["snippet"], "reasons": reasons})
            return _reject(res, "MULTI_CARRIER_AMBIGUOUS",
                           [c["record_id"] for c in exact])
        carrier = exact[0]
        if carrier["record_id"] in used:
            return _reject(res, "MULTI_CLAUSE_SAME_RECORD", carrier["record_id"])
        used.add(carrier["record_id"])
        nn, _ = _nonneutral80(carrier["record"])
        assignments.append((seg, carrier, nn, effects))
    if not assignments:
        return _reject(res, "NO_NUMERIC_CLAUSE")
    target = "味方全体（句面）" if "味方全体" in raw else "自身（句面）"
    answers, skipped = [], []
    for seg, carrier, nn, effects in assignments:
        for slot, v in sorted(nn.items()):
            eff = SLOT_EFFECT[slot]
            rule_key = "skilllist|80|/%s" % slot
            if _already(existing_answers, rule_key, carrier["record_id"], "/" + slot):
                skipped.append({"rule_key": rule_key, "record_id": carrier["record_id"]})
                continue
            answers.append(build_slot_answer(
                data, table, reference_field, record, text, dict(carrier, semantic="80"),
                slot, eff, seg["direction"], res, _seg_cond_text(seg), target,
                cid=cid, extra_note=_residual_note(raw)))
    if not answers:
        return _reject(res, "ALREADY_ANSWERED", skipped)
    res["gates"]["skipped_existing"] = skipped
    res["answers"] = answers
    res["accepted"] = True
    return res


def _seg_cond_text(seg):
    cond = seg["cond"]
    if cond["mode"] == "both":
        return "持有 %s 两种玛那（全部）" % "・".join(seg.get("resolved_jobs") or [])
    if cond["mode"] == "any":
        return "持有≥1 个玛那（任一职业）"
    if cond["mode"] == "all":
        return "持有全部 5 种职业玛那"
    if cond["mode"] == "excl":
        return "持有 %s 以外的玛那" % "・".join(cond["jobs"])
    return "持有 %s 玛那" % "・".join(cond["jobs"])


def _residual_note(raw):
    words = [w for w in RESIDUAL_WORDS if w in raw]
    return ("同句另有机制子句（%s），无本批系数槽，未覆盖" % "・".join(words)) if words else None


def _evaluate_count(data, table, reference_field, record, text, existing_answers, cid, res):
    raw = str(text or "")
    parsed = parse_count_clause(raw)
    if parsed.get("rejection"):
        return _reject(res, parsed["rejection"])
    seg = parsed
    if not seg["effects"] and not seg.get("kaburu"):
        return _reject(res, "NO_NUMERIC_CLAUSE", seg["snippet"])
    carriers, cissues = resolve_carriers(data, table, record, layer=None)
    res["gates"]["carrier_issues"] = cissues
    c96 = _dedupe([c for c in carriers if (c.get("record") or {}).get("ability") == 96])
    res["gates"]["sibling_mana_types"] = sorted({(c.get("record") or {}).get("ability")
                                                 for c in carriers
                                                 if (c.get("record") or {}).get("ability")
                                                 in (26, 28, 80, 96, 1106, 1110, 1111)})
    if not c96:
        return _reject(res, "NO_TYPE96_CARRIER")
    base, pos = _verify_text(record, text)
    if pos < 0:
        return _reject(res, "TEXT_UNVERIFIED")
    base_effects = _effects_in_text(_last_sentence(base))
    effects = list(seg["effects"])
    if seg.get("kaburu"):
        if not base_effects:
            return _reject(res, "EFFECT_UNRESOLVED", seg["snippet"])
        for e in base_effects:
            if e not in effects:
                effects.append(e)
    if not effects:
        return _reject(res, "NO_NUMERIC_CLAUSE", seg["snippet"])
    if seg["direction"] is None:
        return _reject(res, "DIRECTION_UNRESOLVED", seg["snippet"])
    claimed = set()
    for e in effects:
        claimed |= set(E96_SLOTS[e])
    bitmap = seg["cond"]["bitmap"]
    pool = [c for c in c96
            if _int_slot(c["record"], "iParam0") == bitmap
            and _int_slot(c["record"], "param0") == 1]
    if not pool:
        near = [c for c in c96 if _int_slot(c["record"], "iParam0") == bitmap]
        if near:
            return _reject(res, "THRESHOLD_MISMATCH",
                           {"bitmap": bitmap, "param0": [c["record"].get("param0") for c in near]})
        return _reject(res, "NO_MATCHING_96", {"bitmap": bitmap})
    exact, reasons = [], []
    for c in pool:
        rec = c["record"]
        cap = _int_slot(rec, "param1")
        if cap is None or cap < 1:
            reasons.append((c["record_id"], "CAP_UNSUPPORTED", rec.get("param1")))
            continue
        nn, err = _nonneutral96(rec)
        if err:
            reasons.append((c["record_id"], err))
            continue
        if set(nn) != claimed:
            reasons.append((c["record_id"], "SLOT_SET", sorted(nn), sorted(claimed)))
            continue
        bad = [s for s, v in nn.items()
               if not _sign_ok96(s, v, seg["direction"], seg["count_dir"])]
        if bad:
            reasons.append((c["record_id"], "SIGN", bad))
            continue
        exact.append(c)
    if len({c["record_id"] for c in exact}) != 1:
        if not exact:
            return _reject(res, "SLOT_CLAUSE_MISMATCH",
                           {"snippet": seg["snippet"], "reasons": reasons})
        return _reject(res, "MULTI_CARRIER_AMBIGUOUS", [c["record_id"] for c in exact])
    carrier = exact[0]
    nn, _ = _nonneutral96(carrier["record"])
    cap = _int_slot(carrier["record"], "param1")
    target = "味方全体（句面）" if "味方全体" in raw else "自身（句面）"
    cond_txt = "玛那数%s；%s" % ("较多" if seg["count_dir"] == "more" else "较少",
                               _seg_cond_text({"cond": seg["cond"]}))
    residual = _count_residual(raw, seg)
    answers, skipped = [], []
    for slot, v in sorted(nn.items()):
        eff = {"param2": "attack", "param3": "attack", "param4": "move",
               "param5": "defence", "param6": "crit_rate", "param7": "crit_dmg"}.get(slot)
        if eff is None:
            return _reject(res, "SLOT_UNMAPPED_96", slot)
        rule_key = "skilllist|96|/%s" % slot
        if _already(existing_answers, rule_key, carrier["record_id"], "/" + slot):
            skipped.append({"rule_key": rule_key, "record_id": carrier["record_id"]})
            continue
        answers.append(build_slot_answer(
            data, table, reference_field, record, text, dict(carrier, semantic="96"),
            slot, eff, seg["direction"], res, cond_txt, target, cap=cap, cid=cid,
            extra_note=residual))
    if not answers:
        return _reject(res, "ALREADY_ANSWERED", skipped)
    res["gates"]["skipped_existing"] = skipped
    res["answers"] = answers
    res["accepted"] = True
    return res


def _count_residual(raw, seg):
    """96 句中不属于本批系数槽的残余（回復/通常攻撃/攻撃速度/必殺技発動等）。"""
    tail = _norm(raw)
    body = seg["snippet"]
    i = tail.find(body)
    rest = (tail[i + len(body):] if i >= 0 else "").strip("。、")
    words = [w for w in ("通常回復量", "回復", "通常攻撃", "攻撃速度", "攻撃間隔",
                         "スロット", "状態異常", "ダウン", "必殺技") if w in tail]
    words += [w for w in RESIDUAL_WORDS if w in rest and w not in words]
    if not words and not rest:
        return None
    parts = []
    if words:
        parts.append("同句另有非本批槽位内容（%s）" % "・".join(dict.fromkeys(words)))
    if rest:
        parts.append("残余子句「%s」" % rest[:40])
    return "；".join(parts) + "，未覆盖"


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
    row["evidence_label"] = "推断（マナB档：句式→已确认系数槽/条件）"
    row["partial"] = True
    row["evidence_scope"] = list(dict.fromkeys(list(row.get("evidence_scope") or [])
                                              + ["BY_TYPE_EXTRAPOLATED"]))
    marker = row.setdefault("inference_mana_b", {"scope": SCOPE, "claims": []})
    marker["claims"].append({"family": answer["binding"]["mana_b_binding"]["family"],
                             "slot": answer["field_path"],
                             "record_id": answer["record_id"],
                             "rule_key": answer["rule_key"],
                             "value": answer["raw_value"]})
    report["answers_added"] += 1
    report["additions"].append({"row_id": row["row_id"],
                                "family": answer["binding"]["mana_b_binding"]["family"],
                                "slot": answer["field_path"],
                                "record_id": answer["record_id"],
                                "rule_key": answer["rule_key"],
                                "value": answer["raw_value"]})
    return True


def apply_to_groups(data, cid, groups):
    """正式页消费：为マナ B 档四族行绑定系数槽答案（不覆盖/不删除既有答案）。"""
    report = {"scope": SCOPE, "cid": cid, "answers_added": 0, "additions": [],
              "rejections": [], "skipped_existing": 0, "evaluated": 0}
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
                    elif res["rejection"] not in ("NOT_START_CLAIM", "NOT_IN_SCOPE_FAMILY",
                                                  "NOT_MANA_CLAIM"):
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
                row.setdefault("mana_b_gate", dict(res["gates"]))
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="マナB档：句式分类/门控只读探针")
    ap.add_argument("--text", help="单句测试")
    args = ap.parse_args(argv)
    if args.text:
        print(json.dumps({"start": classify_start(args.text),
                          "hold": parse_hold_segments(args.text),
                          "count": parse_count_clause(args.text)},
                         ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
