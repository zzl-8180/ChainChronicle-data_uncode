# -*- coding: utf-8 -*-
"""C14-P1：**被 `not answers` 守卫跳过的 B10/B13 直接 2003 载体行** → 敵デバフ四键补隙（候选，未接线）。

任务卡 ``docs/tasks/20261102-c14-p1-2003-enemy-debuff.md``；周期卡
``docs/tasks/20261102-c14-cycle.md``；候选预筛 ``work/c14_20261102/p1/full_screen.json``
（逐行实跑既有 ``B10.evaluate``），逐行独立核对 ``work/c14_20261102/p1/verify_rows.json``。

范围形态（已实测纠正，不沿用旧预估）
------------------------------------
**不是**「行记录自身 ability==2003」（全库 0 行）。本批补的是这样一组行：行属于
``bosspattern`` / ``denju`` / ``denju_limit_break_info`` / ``charainfo`` 表，行记录
``own children`` 里有 ``boss_skill.s_ability → skilllist ability==2003``
直接载体（charainfo 行 own children 为空，经同页同文 bosspattern 中继，B10 G5 同法），
**且该行已有一条原文数字答案**（如「4羽」的数量「4」）——因此共享生成器
``card_page_data.py`` 的 ``table in B10.TABLES and not answers`` 守卫使既有
``B10.evaluate`` 从未运行。这与 C9 t99 补隙同形：规则与载体都已存在，缺的是被守卫挡住的
那一次评估。本模块**不改该守卫、不全局放宽**，只对冻结的 16 行逐行重新调用既有
``B10.evaluate``（APK 载体由其内部委托 ``B13.handle_2003_apk``），并要求
``kind == 'promote'`` 且 carrier／subject／attrs／每条值行逐项相等。

冻结范围（2026-11-02 由当前正式页、backlog、原始 CACHE/APK skilllist 与既有
B10/B13 实跑重导一致后固化；任何漂移即拒绝，不静默重绑）
--------------------------------------------------------
* 16 行 / 6 cid / 63 条值行：Y.G. 30303 3 行 12 条；同域非 Y.G. 106、347、5302、
  20608、20704 共 13 行 51 条。
* 值行规则键只允许既有 ``skilllist|2003|/param7|/param8|/param9|/param0``
  （rules.json 五键中原有的四个出值键；``/param3`` 是触发阈值，只披露不出值）。
* 句面 1:1 映射：攻撃力→``/param7``、移動速度→``/param8``、防御力→``/param9``；
  只有句面含「一定時間」且载体 ``param0`` 有限正值才出 ``/param0`` 游戏秒。
* 方向：p7／p8 **负值加算＝下降贡献**；p9 **正值为受伤量倍率加算**（正文写作「防御力
  下がる」的表现层），**不写成固定防御减少**。
* 触发：仅 Skill 型着弹（damageType==1）经 ``param3×Random.Range`` 门；Normal／Critical
  永不触发。``param3`` 只披露阈值，不冒充攻击／防御／移动或时长答案。
* CACHE／APK 分源：每行只在其载体所在层取值，绝不回退到另一层；同行号另层存在时只登记
  不取值（当前 16 行载体均无同号另层记录）。
* B10/B13 已答不重复：冻结行当前均无 ``skilllist|2003|*`` 答案；若出现同键同记录同值
  答案按幂等跳过，异值／异来源拒绝而非覆盖。

硬门（任一不符即拒，不猜、不补 0、不跨层）
------------------------------------------
G0  保护／禁推卡 20234、30102、30236、30239 零触碰。
G1  行 ``row_id`` 在冻结表内，cid／group 与冻结值一致。
G2  行句面与冻结句面 NFKC＋去空白后逐字相同。
G3  ``reference_field`` 与冻结值一致。
G4  技能节点表／层／容器 ``record_id`` 与冻结值一致；行 ``source`` 的 source_key、
    json_pointer、field 与冻结父记录身份一致（行记录自身，非载体记录）。
G5  父记录（charainfo 为中继 pattern）存在，正文字段含该句。
G6  行内必须仍有至少一条原文数字答案（守卫来源），且其 raw 值与冻结值一致；
    消失 → ``ORIGINAL_NUMERIC_MISSING``，变化 → ``ORIGINAL_NUMERIC_DRIFT``。
G7  既有 ``skilllist|2003|*`` 答案：全同 → ``ALREADY_PRESENT_SAME``（零写入）；
    一致子集 → 只补缺键；异值／异记录／异层 → ``ALREADY_ANSWERED``（只披露不改写）。
G8  载体链：父记录（或中继 pattern）``boss_skill.s_ability`` 子记录中 ability==2003
    恰恰 1 条且 id／层等于冻结载体；链上出现 ability99 → 拒绝（99 家族归批 9）；
    仅 ``sub_effect`` 伪影不算链。
G9  载体记录在冻结层存在、ability==2003；param0/3/7/8/9 状态与数值与冻结值逐位相等
    （缺失／null／非有限分别拒绝，不补 0；p7/p8 负值、p9 正值是规则方向语义）。
    同号跨层（另一层也有同一 skillid）→ CROSS_LAYER_SAME_ID_PRESENT 整行拒绝：既有
    B9._ability_by_id 是 CACHE-first，若两域同号会让 B10 取错层；冻结 16 行载体均无
    同号另层，故一律 fail-closed、不按存在层静默选择，也不回退取另一层值。
G10 形状双向：句面属性集合 ⇔ 载体 p7/p8/p9 活性（零＝不活性，不补 0）。
G11 方向：p7<0、p8<0、p9>0；违反即拒。
G12 触发：``param3`` 有限且 0<param3≤1；句面写「通常攻撃」触发即拒（仅 Skill 路）。
G13 时长哨兵：句面「一定時間」时``param0`` 必须有限且 >0；-1/0/缺失/null/非有限
    → ``DURATION_PARAM0_NOT_POSITIVE``，**不补时长**、不把 -1 当 0 秒。
G14 ``B10.evaluate`` 必须返回 ``kind=='promote'``，且 carrier_record_id／carrier_layer／
    subject／attrs／值行（rule_key＋raw_value＋field_path＋source 记录层＋evidence_scope）
    与冻结值逐项相等；值行 note 必须仍含「仅 Skill 型着弹」「不升确认」，p9 必须仍写
    「不是固定防御减少」，p0 必须仍写「游戏秒」。

P6 处理（明确披露）
-------------------
B10/B13 的 ``_CLAIMS`` 是进程内「跨 cid 载体竞争」登记。正式全库运行时该登记会累积其它
行的主张，使本模块的后置调用受扫描顺序影响。本模块在调用前**只临时移除本行冻结载体的
登记键**，调用后原样恢复，不改变其它载体状态；替代门是更强的全库冻结核对：16 行载体互不
跨 cid 共享（candidate JSON 中 ``cross_cid_shared_carriers = {}``），且每行载体恒等匹配。
这不是放宽守卫，只是把「本行载体是否被别的 cid 抢走」从运行时顺序问题提升为冻结时全库核对。

证据档
------
* 规则本体：rules.json ``skilllist|2003|/param0|/param3|/param7|/param8|/param9``
  status 已确认（静态及受控原生局部规则）——指规则本身。
* 本条数值归属：句面→载体字段仍是**推断**（数据侧结构对应；引擎侧行→载体装载路径无
  原生核实），沿用 B10／B13 答案对象原档，**不升确认**。
* 不证明：引擎实际装载、玩家解锁、最终面板、最终扣血、实机叠加/覆盖、命中次数。
* 只补「被守卫跳过的成熟行」；其余同形行不因本模块自动进入。

接口
----
``evaluate(data, cid, row, skill, b10=None, frozen_override=None)``
    单行判定（不写入）。``data`` 与共享生成器同形（``old``/``cache_skill``/``apk_skill``/
    ``links``）；``b10`` 可注入替代评估器（只读测试）；``frozen_override`` 仅供检查脚本
    构造反例，正式路径不传。
``apply_to_groups(data, cid, groups)``
    正式页消费：只为冻结行补值行并写行级 marker；非目标卡一行不处理。
"""
from __future__ import annotations

import math
import unicodedata

import card_page_inference_b10_sa2003 as B10
import card_page_inference_b13_apkext as B13

MODULE_VERSION = 'c14_p1_2003_enemy_debuff_gap_20261102'
#: 候选标记：本模块未接入共享 ``card_page_data.py``；正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
SCOPE = 'C14_P1_2003_ENEMY_DEBUFF_GAP_20261102'
MARKER_KEY = 'inference_c14_p1_2003'
ADMISSION = 'FROZEN_16_ROW_TABLE_REUSING_EXISTING_B10_GATE'

ATTRS3 = ('攻撃力', '防御力', '移動速度')
SLOT_OF = {'攻撃力': 'param7', '移動速度': 'param8', '防御力': 'param9'}
RULE_KEYS = ('skilllist|2003|/param7', 'skilllist|2003|/param8',
             'skilllist|2003|/param9', 'skilllist|2003|/param0')
PARAM_ORDER = ('param7', 'param8', 'param9', 'param0')
#: 保护／禁推卡（任务卡共同门槛；本模块对其中任何 cid 一行不处理）。
ZERO_TOUCH_CIDS = frozenset({20234, 30102, 30236, 30239})
B10_SCOPE = 'TEMPLATE_BATCH10_SA2003'
B13_SCOPE = 'TEMPLATE_BATCH13_APKEXT'

#: 冻结行表的表清单（与 B10.TABLES 一致；不是 skilllist 行）。
TABLES = B10.TABLES

#: 冻结准入表（每项：cid/group/row_id/table/layer/record_id/reference_field、
#: 句面、父记录层-指针-字段、载体(id,层,ability,name,五参数)、charainfo 中继、
#: subject/attrs/句序、既有原文数字 raw、期望值行(rule_key,raw,field_path,source,层,scope)。
_ADMITTED_LIST = [
    dict(cid=106, group='denju', row_id='106-denju-denju-denju_denju_id____cid-lvorder0-f0',
         table='denju', layer='CACHE', record_id=106, reference_field='denju.denju_id == cid',
         japanese='直線範囲上にいる敵1体に小ダメージを与え、攻撃した敵の防御力と移動速度を一定時間下げる。',
         parent=('CACHE/denju.data5.json.raw', '/denju/45', '/stext'),
         carrier=(50010, 'APK', 2003, '伝授必殺技用ヴィドック',
                  dict(param0=15.0, param3=1.0, param7=0.0,
                       param8=-0.30000001192092896, param9=0.10000000149011612)),
         via_pattern=None, subject='攻撃した敵', attrs=('防御力', '移動速度'),
         sent_no=1, sent_total=1, original_numeric=('1'),
         answers=(
             ('skilllist|2003|/param9', 0.10000000149011612, '/param9', 50010, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param8', -0.30000001192092896, '/param8', 50010, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param0', 15.0, '/param0', 50010, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
         )),
    dict(cid=20608, group='special_move', row_id='20608-special_move-special_move-pattern2-lvorder2-f1',
         table='bosspattern', layer='APK', record_id=42060802, reference_field='pattern2',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する料理を3つ生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がり、自身の攻撃力と防御力と移動速度が一定時間上がる。',
         parent=('APK/_mdBossInfo.json', '/bosspattern/4201', '/sinfo'),
         carrier=(42060816, 'APK', 2003, 'ｉｆモアネット用SA_PowerDrain3',
                  dict(param0=30.0, param3=1.0, param7=-0.30000001192092896,
                       param8=-0.30000001192092896, param9=0.30000001192092896)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=5, original_numeric=('3'),
         answers=(
             ('skilllist|2003|/param7', -0.30000001192092896, '/param7', 42060816, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param9', 0.30000001192092896, '/param9', 42060816, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param8', -0.30000001192092896, '/param8', 42060816, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param0', 30.0, '/param0', 42060816, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
         )),
    dict(cid=20608, group='special_move', row_id='20608-special_move-special_move-skilltext-lvorder3-f1',
         table='charainfo', layer='APK', record_id=20608, reference_field='skilltext',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する料理を3つ生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がり、自身の攻撃力と防御力と移動速度が一定時間上がる。',
         parent=('APK/_mdCharacter.json', '/charainfo/1826', '/skilltext'),
         carrier=(42060816, 'APK', 2003, 'ｉｆモアネット用SA_PowerDrain3',
                  dict(param0=30.0, param3=1.0, param7=-0.30000001192092896,
                       param8=-0.30000001192092896, param9=0.30000001192092896)),
         via_pattern=['42060802', 'APK'], subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=5, original_numeric=('3'),
         answers=(
             ('skilllist|2003|/param7', -0.30000001192092896, '/param7', 42060816, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param9', 0.30000001192092896, '/param9', 42060816, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param8', -0.30000001192092896, '/param8', 42060816, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param0', 30.0, '/param0', 42060816, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
         )),
    dict(cid=20608, group='denju', row_id='20608-denju-denju-denju_denju_id____cid-lvorder0-f1',
         table='denju', layer='CACHE', record_id=20608, reference_field='denju.denju_id == cid',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する料理を3つ生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がり、自身の攻撃力と防御力と移動速度が一定時間上がる。',
         parent=('CACHE/denju.data5.json.raw', '/denju/1344', '/stext'),
         carrier=(42060814, 'APK', 2003, 'ｉｆモアネット用SA_PowerDrain1',
                  dict(param0=30.0, param3=1.0, param7=-0.25,
                       param8=-0.25, param9=0.25)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=4, original_numeric=('3'),
         answers=(
             ('skilllist|2003|/param7', -0.25, '/param7', 42060814, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param9', 0.25, '/param9', 42060814, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param8', -0.25, '/param8', 42060814, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param0', 30.0, '/param0', 42060814, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
         )),
    dict(cid=20704, group='special_move', row_id='20704-special_move-special_move-pattern1-lvorder1-f2',
         table='bosspattern', layer='APK', record_id=42070400, reference_field='pattern1',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する折り鶴を4羽生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('APK/_mdBossInfo.json', '/bosspattern/4318', '/sinfo'),
         carrier=(42070412, 'APK', 2003, '幽夜ファルベ用SA_PowerDrain1',
                  dict(param0=30.0, param3=1.0, param7=-0.20000000298023224,
                       param8=-0.20000000298023224, param9=0.20000000298023224)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=3, sent_total=6, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.20000000298023224, '/param7', 42070412, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param9', 0.20000000298023224, '/param9', 42070412, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param8', -0.20000000298023224, '/param8', 42070412, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param0', 30.0, '/param0', 42070412, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
         )),
    dict(cid=20704, group='special_move', row_id='20704-special_move-special_move-pattern2-lvorder2-f2',
         table='bosspattern', layer='APK', record_id=42070402, reference_field='pattern2',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する折り鶴を4羽生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('APK/_mdBossInfo.json', '/bosspattern/4320', '/sinfo'),
         carrier=(42070413, 'APK', 2003, '幽夜ファルベ用SA_PowerDrain2',
                  dict(param0=30.0, param3=1.0, param7=-0.25,
                       param8=-0.25, param9=0.25)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=3, sent_total=6, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.25, '/param7', 42070413, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param9', 0.25, '/param9', 42070413, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param8', -0.25, '/param8', 42070413, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param0', 30.0, '/param0', 42070413, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
         )),
    dict(cid=20704, group='denju', row_id='20704-denju-denju-denju_denju_id____cid-lvorder0-f2',
         table='denju', layer='CACHE', record_id=20704, reference_field='denju.denju_id == cid',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する折り鶴を4羽生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/denju.data5.json.raw', '/denju/1378', '/stext'),
         carrier=(42070412, 'APK', 2003, '幽夜ファルベ用SA_PowerDrain1',
                  dict(param0=30.0, param3=1.0, param7=-0.20000000298023224,
                       param8=-0.20000000298023224, param9=0.20000000298023224)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=3, sent_total=5, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.20000000298023224, '/param7', 42070412, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param9', 0.20000000298023224, '/param9', 42070412, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param8', -0.20000000298023224, '/param8', 42070412, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
             ('skilllist|2003|/param0', 30.0, '/param0', 42070412, 'APK', 'TEMPLATE_BATCH13_APKEXT'),
         )),
    dict(cid=30303, group='special_move', row_id='30303-special_move-special_move-pattern0-lvorder0-f2',
         table='bosspattern', layer='CACHE', record_id=43030300, reference_field='pattern0',
         japanese='さらに軌道上の敵を一定時間自動で攻撃する蝶を4羽召喚し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/bossinfo.data5.json.raw', '/bossinfo/bosspattern/1287', '/sinfo'),
         carrier=(43030311, 'CACHE', 2003, '時空軍オルオレータ用SA_PowerDrain1',
                  dict(param0=30, param3=1, param7=-0.3,
                       param8=-0.3, param9=0.3)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=3, sent_total=4, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.3, '/param7', 43030311, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.3, '/param9', 43030311, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.3, '/param8', 43030311, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 43030311, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
    dict(cid=30303, group='special_move', row_id='30303-special_move-special_move-pattern1-lvorder1-f2',
         table='bosspattern', layer='CACHE', record_id=43030301, reference_field='pattern1',
         japanese='さらに軌道上の敵を一定時間自動で攻撃する蝶を4羽召喚し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/bossinfo.data5.json.raw', '/bossinfo/bosspattern/1288', '/sinfo'),
         carrier=(43030312, 'CACHE', 2003, '時空軍オルオレータ用SA_PowerDrain2',
                  dict(param0=30, param3=1, param7=-0.35,
                       param8=-0.35, param9=0.35)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=3, sent_total=5, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.35, '/param7', 43030312, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.35, '/param9', 43030312, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.35, '/param8', 43030312, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 43030312, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
    dict(cid=30303, group='denju', row_id='30303-denju-denju-denju_denju_id____cid-lvorder0-f2',
         table='denju', layer='CACHE', record_id=30303, reference_field='denju.denju_id == cid',
         japanese='さらに軌道上の敵を一定時間自動で攻撃する蝶を4羽召喚し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/denju.data5.json.raw', '/denju/1463', '/stext'),
         carrier=(43030311, 'CACHE', 2003, '時空軍オルオレータ用SA_PowerDrain1',
                  dict(param0=30, param3=1, param7=-0.3,
                       param8=-0.3, param9=0.3)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=3, sent_total=4, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.3, '/param7', 43030311, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.3, '/param9', 43030311, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.3, '/param8', 43030311, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 43030311, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
    dict(cid=347, group='special_move', row_id='347-special_move-special_move-pattern1-lvorder1-f1',
         table='bosspattern', layer='CACHE', record_id=40034701, reference_field='pattern1',
         japanese='その後、軌道上の敵を一定時間自動で攻撃するプレゼントボックスを6個生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/bossinfo.data5.json.raw', '/bossinfo/bosspattern/38', '/sinfo'),
         carrier=(40034712, 'CACHE', 2003, '聖夜ファルベ用SA_PowerDrain1',
                  dict(param0=30, param3=1, param7=-0.3,
                       param8=-0.3, param9=0.3)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=5, original_numeric=('6'),
         answers=(
             ('skilllist|2003|/param7', -0.3, '/param7', 40034712, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.3, '/param9', 40034712, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.3, '/param8', 40034712, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 40034712, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
    dict(cid=347, group='special_move', row_id='347-special_move-special_move-pattern2-lvorder2-f1',
         table='bosspattern', layer='CACHE', record_id=40034702, reference_field='pattern2',
         japanese='その後、軌道上の敵を一定時間自動で攻撃するプレゼントボックスを6個生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/bossinfo.data5.json.raw', '/bossinfo/bosspattern/39', '/sinfo'),
         carrier=(40034714, 'CACHE', 2003, '聖夜ファルベ用SA_PowerDrain2',
                  dict(param0=30, param3=1, param7=-0.35,
                       param8=-0.35, param9=0.35)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=5, original_numeric=('6'),
         answers=(
             ('skilllist|2003|/param7', -0.35, '/param7', 40034714, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.35, '/param9', 40034714, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.35, '/param8', 40034714, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 40034714, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
    dict(cid=347, group='denju', row_id='347-denju-denju-denju_denju_id____cid-lvorder0-f1',
         table='denju', layer='CACHE', record_id=347, reference_field='denju.denju_id == cid',
         japanese='その後、軌道上の敵を一定時間自動で攻撃するプレゼントボックスを6個生成し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/denju.data5.json.raw', '/denju/110', '/stext'),
         carrier=(40034712, 'CACHE', 2003, '聖夜ファルベ用SA_PowerDrain1',
                  dict(param0=30, param3=1, param7=-0.3,
                       param8=-0.3, param9=0.3)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=4, original_numeric=('6'),
         answers=(
             ('skilllist|2003|/param7', -0.3, '/param7', 40034712, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.3, '/param9', 40034712, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.3, '/param8', 40034712, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 40034712, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
    dict(cid=5302, group='special_move', row_id='5302-special_move-special_move-pattern2-lvorder2-f1',
         table='bosspattern', layer='CACHE', record_id=40530202, reference_field='pattern2',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する蝶を4羽召喚し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/bossinfo.data5.json.raw', '/bossinfo/bosspattern/250', '/sinfo'),
         carrier=(40530215, 'CACHE', 2003, '覚醒オルオレータ用SA_PowerDrain3',
                  dict(param0=30, param3=1, param7=-0.3,
                       param8=-0.3, param9=0.3)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=4, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.3, '/param7', 40530215, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.3, '/param9', 40530215, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.3, '/param8', 40530215, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 40530215, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
    dict(cid=5302, group='special_move', row_id='5302-special_move-special_move-skilltext-lvorder3-f1',
         table='charainfo', layer='CACHE', record_id=5302, reference_field='skilltext',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する蝶を4羽召喚し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/charainfo.data5.json.raw', '/charainfo/105', '/skilltext'),
         carrier=(40530215, 'CACHE', 2003, '覚醒オルオレータ用SA_PowerDrain3',
                  dict(param0=30, param3=1, param7=-0.3,
                       param8=-0.3, param9=0.3)),
         via_pattern=['40530202', 'CACHE'], subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=4, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.3, '/param7', 40530215, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.3, '/param9', 40530215, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.3, '/param8', 40530215, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 40530215, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
    dict(cid=5302, group='denju', row_id='5302-denju-denju-denju_denju_id____cid-lvorder0-f1',
         table='denju', layer='CACHE', record_id=5302, reference_field='denju.denju_id == cid',
         japanese='その後、軌道上の敵を一定時間自動で攻撃する蝶を4羽召喚し、同時に攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。',
         parent=('CACHE/denju.data5.json.raw', '/denju/472', '/stext'),
         carrier=(40530211, 'CACHE', 2003, '覚醒オルオレータ用SA_PowerDrain1',
                  dict(param0=30, param3=1, param7=-0.25,
                       param8=-0.25, param9=0.25)),
         via_pattern=None, subject='同時に攻撃した敵', attrs=('攻撃力', '防御力', '移動速度'),
         sent_no=2, sent_total=3, original_numeric=('4'),
         answers=(
             ('skilllist|2003|/param7', -0.25, '/param7', 40530211, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param9', 0.25, '/param9', 40530211, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param8', -0.25, '/param8', 40530211, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
             ('skilllist|2003|/param0', 30, '/param0', 40530211, 'CACHE', 'TEMPLATE_BATCH10_SA2003'),
         )),
]


def _normalize_freeze(item):
    """把紧凑字面量展开为判定用结构（载体/父记录/值行均为 dict；不改冻结原值）。"""
    out = dict(item)
    cid, layer, ability, name, params = item['carrier']
    out['carrier'] = dict(record_id=cid, layer=layer, ability=ability, name=name,
                          params=dict(params))
    out['parent'] = tuple(item['parent'])
    out['attrs'] = tuple(item['attrs'])
    out['original_numeric'] = tuple(str(v) for v in item['original_numeric'])
    out['answers'] = [dict(rule_key=rk, raw_value=rv, field_path=fp, source_record=sr,
                           source_layer=sl, evidence_scope=sc)
                      for (rk, rv, fp, sr, sl, sc) in item['answers']]
    return out


_ADMITTED_LIST = [_normalize_freeze(item) for item in _ADMITTED_LIST]
ADMITTED = {item['row_id']: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item['cid'] for item in _ADMITTED_LIST)

#: 冻结时的全库核对结论（由 candidate_rows.json 机器结果背书）。
FREEZE_COUNTS = dict(rows=16, cids=6, answers=63, yg_rows=3, yg_answers=12,
                     non_yg_rows=13, non_yg_answers=51,
                     cross_cid_shared_carriers={})

_IDX = {}


# ---------------------------------------------------------------- 基础工具
def canon(text):
    """NFKC＋去全部空白（句面/正文比较口径）。"""
    return ''.join(unicodedata.normalize('NFKC', str(text or '')).split())


def raw_state(value, present=True):
    """MISSING／NULL／NON_FINITE／FINITE_ZERO／FINITE。"""
    if not present:
        return 'MISSING'
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'NON_FINITE'
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 'NON_FINITE'
    if not math.isfinite(f):
        return 'NON_FINITE'
    return 'FINITE_ZERO' if f == 0 else 'FINITE'


def _finite(value):
    """有限数值或 None（布尔不算数值）。"""
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _record_index(data):
    """(table, str(record_id), layer) → 记录；与 B9._chain_index 同键，持强引用防 id 复用。"""
    key = id(data)
    hit = _IDX.get(key)
    if hit is not None and hit[0] is data:
        return hit[1]
    idx = {}
    for rec in data.old.values():
        idx[(rec.get('table'), str(rec.get('record_id')), rec.get('layer'))] = rec
    _IDX[key] = (data, idx)
    return idx


def _carrier_store(data, layer):
    return data.cache_skill if layer == 'CACHE' else data.apk_skill


def _original_numeric(row):
    return [a for a in row.get('answers') or []
            if a.get('rule_key') is None and a.get('quantitative')]


def _existing_2003(row):
    return [a for a in row.get('answers') or []
            if str(a.get('rule_key') or '').startswith('skilllist|2003|')]


def _answer_source(answer):
    src = answer.get('source') or {}
    return src.get('record_id'), src.get('layer')


def _reject(code, gates, detail=None, **extra):
    out = dict(accepted=False, rejection=code, detail=detail, gates=gates, b10=None,
               missing_keys=[], partial_existing=False)
    out.update(extra)
    return out


# ---------------------------------------------------------------- 链／载体硬门
def _chain_2003(data, adm):
    """G8：s_ability 链上 ability==2003 载体恰 1 条且等于冻结载体。

    返回 (state, detail)。state∈{OK, PARENT_RECORD_MISSING, RELAY_PATTERN_MISSING,
    RELAY_TEXT_MISMATCH, NO_CHILDREN, NO_2003_S_ABILITY, ABILITY_99_ON_CHAIN,
    MULTI_2003_CARRIER, CARRIER_DRIFT}。
    """
    idx = _record_index(data)
    if adm['table'] == 'charainfo':
        if not adm['via_pattern']:
            return 'RELAY_PATTERN_MISSING', 'charainfo 行缺冻结中继 pattern'
        pid, player = adm['via_pattern']
        relay = idx.get(('bosspattern', str(pid), player))
        if relay is None:
            return 'RELAY_PATTERN_MISSING', f'中继 bosspattern|{pid}|{player} 不存在'
        if canon(adm['japanese']) not in canon(relay.get('text') or ''):
            return 'RELAY_TEXT_MISMATCH', f'中继 bosspattern|{pid}|{player} 正文不含本句'
        kids = relay.get('children') or []
    else:
        parent = idx.get((adm['table'], str(adm['record_id']), adm['layer']))
        if parent is None:
            return 'PARENT_RECORD_MISSING', f'{adm["table"]}|{adm["record_id"]}|{adm["layer"]}'
        kids = parent.get('children') or []
    if not kids:
        return 'NO_CHILDREN', '行记录无 own children（charainfo 应走中继）'
    found = []
    for child in kids:
        if child.get('table') != 'skilllist' or child.get('link_kind') != 'boss_skill.s_ability':
            continue
        lay = child.get('layer')
        hit = _carrier_store(data, lay).get(child.get('record_id'))
        ability = (hit or (None, {}))[1].get('ability') if hit else None
        found.append((str(child.get('record_id')), lay, ability, hit is not None))
    if any(a == 99 for _i, _l, a, _p in found):
        return 'ABILITY_99_ON_CHAIN', '链上另有 ability99（99 家族归批 9，不混用样本域）'
    two = [f for f in found if f[2] == 2003]
    if len(two) > 1:
        return 'MULTI_2003_CARRIER', '；'.join(f'{i}|{l}' for i, l, _a, _p in two)
    if not two:
        cid0, lay0 = adm['carrier']['record_id'], adm['carrier']['layer']
        if len(found) == 1 and found[0][0] == str(cid0) and found[0][1] == lay0:
            if not found[0][3]:
                return ('CARRIER_RECORD_MISSING',
                        f'唯一 s_ability 载体 {cid0}|{lay0} 在该层原始 skilllist 不可解析'
                        '（只在该层查找，绝不回退到另一层）')
            return 'CARRIER_NOT_2003', f'唯一 s_ability 载体 {cid0}|{lay0} ability={found[0][2]}'
        return 'NO_2003_S_ABILITY', 's_ability 链上无 ability2003 载体'
    carrier_id, carrier_layer = adm['carrier']['record_id'], adm['carrier']['layer']
    if two[0][0] != str(carrier_id) or two[0][1] != carrier_layer:
        return 'CARRIER_DRIFT', f'链上 {two[0][0]}|{two[0][1]} ≠ 冻结 {carrier_id}|{carrier_layer}'
    return 'OK', dict(s_ability=[f'{i}|{l}|a={a}' for i, l, a, _p in found])


def _shape_and_direction(adm, crec, states):
    """G10/G11：属性 ↔ 活性双向，方向按符号。返回 (ok, code, detail)。"""
    attrs = set(adm['attrs'])
    mism, bad = [], []
    for attr, slot in SLOT_OF.items():
        active = states[slot] == 'FINITE'
        if attr in attrs and not active:
            mism.append(f'句面含{attr}但 /{slot} 状态={states[slot]}（不活性）')
        if attr not in attrs and active:
            mism.append(f'/{slot}={crec.get(slot)!r} 活性但句面无{attr}')
    if mism:
        return False, 'ATTR_SLOT_MISMATCH', '；'.join(mism)
    for attr in ('攻撃力', '移動速度'):
        if attr not in attrs:
            continue
        slot = SLOT_OF[attr]
        if not (_finite(crec.get(slot)) < 0):
            bad.append(f'/{slot}={crec.get(slot)!r} 与{attr}下降冲突（须负值加算）')
    if '防御力' in attrs and not (_finite(crec.get('param9')) > 0):
        bad.append(f'/param9={crec.get("param9")!r} 与受伤量倍率加算口径冲突（须正值）')
    if bad:
        return False, 'DIRECTION_MISMATCH', '；'.join(bad)
    return True, None, None


def _call_b10(data, adm, row, skill, b10):
    """G14：调用既有 B10.evaluate；只临时摘除本行冻结载体的 P6 登记键，调用后原样恢复。"""
    carrier_id, carrier_layer = adm['carrier']['record_id'], adm['carrier']['layer']
    key10 = carrier_id
    key13 = (carrier_layer, carrier_id)
    saved10 = B10._CLAIMS.get(key10)
    saved13 = B13._CLAIMS.get(key13)
    B10._CLAIMS.pop(key10, None)
    B13._CLAIMS.pop(key13, None)
    try:
        return b10({}, row.get('japanese') or '', table=adm['table'], layer=adm['layer'],
                   record_id=adm['record_id'], text=skill.get('original_text'),
                   data=data, cid=adm['cid'])
    finally:
        if saved10 is None:
            B10._CLAIMS.pop(key10, None)
        else:
            B10._CLAIMS[key10] = saved10
        if saved13 is None:
            B13._CLAIMS.pop(key13, None)
        else:
            B13._CLAIMS[key13] = saved13


def _check_expected_answers(got, adm):
    """G14：值行逐项核对。返回 (ok, code, detail)。"""
    expected = adm['answers']
    brief = [dict(rule_key=a['rule_key'], raw_value=a['raw_value'],
                  field_path=a['field_path'], source_record=a['source_record'],
                  source_layer=a['source_layer'], evidence_scope=a['evidence_scope'])
             for a in expected]
    actual = [dict(rule_key=a.get('rule_key'), raw_value=a.get('raw_value'),
                   field_path=a.get('field_path'),
                   source_record=(a.get('source') or {}).get('record_id'),
                   source_layer=(a.get('source') or {}).get('layer'),
                   evidence_scope=a.get('evidence_scope'),
                   note=a.get('note') or '') for a in got]
    if len(actual) != len(brief):
        return False, 'VALUE_ROWS_COUNT_DRIFT', dict(expected=brief, actual=actual)
    for a, b in zip(actual, brief):
        if (a['rule_key'] != b['rule_key'] or a['field_path'] != b['field_path']
                or float(a['raw_value']) != float(b['raw_value'])
                or a['source_record'] != b['source_record']
                or a['source_layer'] != b['source_layer']
                or a['evidence_scope'] != b['evidence_scope']):
            return False, 'VALUE_ROWS_DRIFT', dict(expected=brief, actual=actual)
        note = a['note']
        if '仅 Skill 型着弹' not in note or '不升确认' not in note:
            return False, 'VALUE_NOTE_TRIGGER_OR_STATUS_DRIFT', dict(rule_key=a['rule_key'])
        param = a['field_path'].lstrip('/')
        if param == 'param9' and '不是固定防御减少' not in note:
            return False, 'VALUE_NOTE_P9_UNIT_DRIFT', dict(rule_key=a['rule_key'])
        if param == 'param0' and '游戏秒' not in note:
            return False, 'VALUE_NOTE_DURATION_UNIT_DRIFT', dict(rule_key=a['rule_key'])
        if param in ('param7', 'param8') and '下降' not in note:
            return False, 'VALUE_NOTE_DIRECTION_DRIFT', dict(rule_key=a['rule_key'])
    return True, None, None


# ---------------------------------------------------------------- 单行判定
def evaluate(data, cid, row, skill, b10=None, frozen_override=None):
    """冻结行硬门判定（不写入）。返回 dict（accepted／rejection／gates／b10…）。"""
    gates = {}
    rid = (row or {}).get('row_id')
    adm = frozen_override if frozen_override is not None else ADMITTED.get(rid)
    if frozen_override is not None:
        gates['frozen_override'] = True
    if adm is None:
        return _reject('NOT_IN_BATCH_SCOPE', gates, f'row_id {rid!r} 不在冻结 16 行表内')

    # G0 保护卡
    if cid in ZERO_TOUCH_CIDS:
        return _reject('PROTECTED_CID', gates, f'cid {cid} 属保护/禁推卡 {sorted(ZERO_TOUCH_CIDS)}')
    # G1 行身份
    if adm['cid'] != cid:
        return _reject('CID_MISMATCH', gates, dict(expected=adm['cid'], actual=cid))
    if row.get('group') != adm['group']:
        return _reject('GROUP_MISMATCH', gates, dict(expected=adm['group'],
                                                     actual=row.get('group')))
    gates['row_id'] = rid
    # G2 句面
    if canon(row.get('japanese')) != canon(adm['japanese']):
        return _reject('ROW_TEXT_NOT_ADMITTED', gates, dict(expected=adm['japanese'],
                                                            actual=row.get('japanese')))
    # G3 引用字段
    if str(row.get('reference_field') or '') != adm['reference_field']:
        return _reject('REFERENCE_FIELD_DRIFT', gates,
                       dict(expected=adm['reference_field'], actual=row.get('reference_field')))
    # G4 技能节点 + 行来源身份（父记录，不是载体记录）
    if skill is None or skill.get('table') != adm['table']:
        return _reject('ROW_TABLE_DRIFT', gates, dict(expected=adm['table'],
                                                      actual=None if skill is None
                                                      else skill.get('table')))
    gates['skill'] = {k: skill.get(k) for k in ('table', 'record_id', 'layer')}
    if (skill.get('layer') != adm['layer'] or skill.get('record_id') != adm['record_id']):
        return _reject('ROW_LAYER_OR_RECORD_MISMATCH', gates,
                       dict(expected=[adm['record_id'], adm['layer']],
                            actual=[skill.get('record_id'), skill.get('layer')]))
    src = row.get('source') or skill.get('source') or {}
    parent_key, parent_pointer, parent_field = adm['parent']
    gates['row_source'] = {k: src.get(k) for k in ('source_key', 'json_pointer', 'field')}
    if (src.get('source_key') != parent_key or src.get('json_pointer') != parent_pointer
            or src.get('field') != parent_field):
        return _reject('ROW_SOURCE_IDENTITY_DRIFT', gates,
                       dict(expected=dict(source_key=parent_key, json_pointer=parent_pointer,
                                          field=parent_field),
                            actual=gates['row_source']))
    # G5 父记录正文含本句
    idx = _record_index(data)
    if adm['table'] == 'charainfo':
        relay = idx.get(('bosspattern', str(adm['via_pattern'][0]), adm['via_pattern'][1]))
        body = (relay or {}).get('text') or ''
        if relay is None:
            return _reject('RELAY_PATTERN_MISSING', gates, '中继 pattern 不存在')
    else:
        parent = idx.get((adm['table'], str(adm['record_id']), adm['layer']))
        body = (parent or {}).get('text') or ''
        if parent is None:
            return _reject('PARENT_RECORD_MISSING', gates, '父记录不存在')
    if canon(adm['japanese']) not in canon(body):
        return _reject('FRAGMENT_NOT_IN_PARENT_TEXT', gates, '句面不是父记录正文子串')
    # G6 守卫前提：至少一条原文数字答案，且与冻结值一致
    originals = _original_numeric(row)
    got_orig = [str(a.get('raw_value')) for a in originals]
    gates['preexisting_original_numeric'] = [dict(value=a.get('value'),
                                                  raw_value=a.get('raw_value')) for a in originals]
    if not originals:
        return _reject('ORIGINAL_NUMERIC_MISSING', gates,
                       '本行已无原文数字答案：守卫补隙前提消失，拒绝（不得当作通用放宽）')
    if sorted(got_orig) != sorted(adm['original_numeric']):
        return _reject('ORIGINAL_NUMERIC_DRIFT', gates,
                       dict(expected=list(adm['original_numeric']), actual=got_orig))
    # G7 既有 2003 答案（幂等／冲突）
    expected_by_key = {a['rule_key']: a for a in adm['answers']}
    existing = _existing_2003(row)
    gates['existing_2003'] = [dict(rule_key=a.get('rule_key'), raw_value=a.get('raw_value'),
                                   source=_answer_source(a)) for a in existing]
    consistent = {}
    for a in existing:
        exp = expected_by_key.get(a.get('rule_key'))
        if exp is None:
            return _reject('ALREADY_ANSWERED', gates,
                           '既有 2003 答案含冻结表外规则键，拒绝覆盖',
                           existing=gates['existing_2003'])
        if (float(a.get('raw_value')) != float(exp['raw_value'])
                or _answer_source(a) != (exp['source_record'], exp['source_layer'])):
            return _reject('ALREADY_ANSWERED', gates,
                           '既有同键答案异值／异记录／异层，拒绝覆盖',
                           existing=gates['existing_2003'])
        consistent[a['rule_key']] = True
    missing = [k for k in expected_by_key if k not in consistent]
    gates['missing_rule_keys'] = missing
    if not missing:
        return _reject('ALREADY_PRESENT_SAME', gates,
                       '同键同记录同值答案已存在：幂等跳过，零写入')
    partial_existing = bool(consistent)

    # --- 句面对象／属性（与 B10 P1 同法：B9._debuff_clause） ---
    frag = row.get('japanese') or ''
    if '敵から受ける' in frag:
        return _reject('OBJECT_OUR_SIDE_TAKEN', gates, '「敵から受ける…」为我方被击句，不是敌方减益')
    clause, attrs, subject = B10.B9._debuff_clause(frag)
    if clause is None or not attrs or not subject:
        return _reject('OBJECT_NOT_ENEMY', gates, f'首个下降谓词句段未同时含「敵」与属性：{clause!r}')
    gates['clause'] = clause
    gates['sentence_attrs'] = list(attrs)
    gates['subject'] = subject
    if set(attrs) != set(adm['attrs']):
        return _reject('SENTENCE_ATTRS_DRIFT', gates,
                       dict(expected=list(adm['attrs']), actual=list(attrs)))
    if subject != adm['subject']:
        return _reject('SUBJECT_DRIFT', gates, dict(expected=adm['subject'], actual=subject))

    # --- G8 链 ---
    state, detail = _chain_2003(data, adm)
    gates['chain_s_ability'] = detail
    if state != 'OK':
        return _reject(state, gates, detail)
    # --- G9 载体层记录与参数 ---
    carrier_id, carrier_layer = adm['carrier']['record_id'], adm['carrier']['layer']
    ability, carrier_name, params = (adm['carrier']['ability'], adm['carrier']['name'],
                                     adm['carrier']['params'])
    hit = _carrier_store(data, carrier_layer).get(carrier_id)
    if hit is None:
        other = _carrier_store(data, 'CACHE' if carrier_layer == 'APK' else 'APK').get(carrier_id)
        return _reject('CARRIER_RECORD_MISSING', gates,
                       dict(carrier=carrier_id, layer=carrier_layer,
                            same_id_other_layer=bool(other),
                            note='只在该层查找，绝不回退到另一层'),
                       same_id_other_layer=bool(other))
    crec = hit[1] or {}
    gates['carrier'] = dict(record_id=carrier_id, layer=carrier_layer,
                            ability=crec.get('ability'), name=crec.get('name'))
    # 跨层同号：另一层存在同一 skillid 时整行拒绝（B9._ability_by_id 的 CACHE-first 优先级
    # 会让既有 B10/B13 取错层；冻结 16 行载体均无同号另层，故拒绝即 fail-closed，不跨层取值）
    other_layer = 'APK' if carrier_layer == 'CACHE' else 'CACHE'
    other_hit = _carrier_store(data, other_layer).get(carrier_id)
    gates['same_id_other_layer'] = bool(other_hit)
    if other_hit is not None:
        return _reject('CROSS_LAYER_SAME_ID_PRESENT', gates,
                       dict(carrier=carrier_id, frozen_layer=carrier_layer,
                            other_layer=other_layer,
                            other_ability=(other_hit[1] or {}).get('ability'),
                            note='同号跨层不合并、不取值：整行拒绝而不是按存在层静默选择'))
    if crec.get('ability') != 2003:
        return _reject('CARRIER_NOT_2003', gates,
                       dict(expected=2003, actual=crec.get('ability')))
    states = {p: raw_state(crec.get(p), p in crec) for p in
              ('param0', 'param3', 'param7', 'param8', 'param9')}
    gates['carrier_params'] = {p: crec.get(p) for p in states}
    gates['carrier_param_states'] = states
    for p in ('param7', 'param8', 'param9'):
        if states[p] in ('MISSING', 'NULL', 'NON_FINITE'):
            return _reject('CARRIER_PARAM_STATE', gates, dict(param=p, state=states[p]))
    drift = {}
    for p in params:
        actual_v, want_v = crec.get(p), params[p]
        fa, fw = _finite(actual_v), _finite(want_v)
        if fa is None or fw is None or fa != fw:
            drift[p] = dict(expected=want_v, actual=actual_v)
    if drift:
        return _reject('CARRIER_PARAM_DRIFT', gates, drift)
    # G10/G11 形状与方向
    ok, code, detail = _shape_and_direction(adm, crec, states)
    if not ok:
        return _reject(code, gates, detail)
    # G12 触发：仅 Skill 型着弹
    p3_state = states['param3']
    p3 = _finite(crec.get('param3'))
    gates['trigger_param3'] = dict(state=p3_state, raw=crec.get('param3'))
    if p3_state in ('MISSING', 'NULL', 'NON_FINITE'):
        return _reject('TRIGGER_PARAM3_STATE', gates, p3_state)
    if p3 == 0:
        return _reject('TRIGGER_PARAM3_ZERO', gates, 'param3=0 → Skill 路永不触发')
    if not (0 < p3 <= 1):
        return _reject('TRIGGER_PARAM3_OUT_OF_RANGE', gates, f'param3={p3!r} 不在 (0,1]')
    if '通常攻撃' in frag:
        return _reject('TRIGGER_NOT_SKILL_ONLY', gates,
                       '句面写「通常攻撃」触发，与 2003 仅 Skill 型着弹冲突')
    # G13 时长哨兵
    if '一定時間' in frag:
        p0_state = states['param0']
        p0 = _finite(crec.get('param0'))
        gates['duration'] = dict(sentence=True, param0_state=p0_state,
                                 param0_raw=crec.get('param0'))
        if p0_state in ('MISSING', 'NULL', 'NON_FINITE'):
            return _reject('DURATION_PARAM0_NOT_POSITIVE', gates,
                           dict(state=p0_state, note='不补时长'))
        if p0 == -1:
            return _reject('DURATION_PARAM0_NOT_POSITIVE', gates,
                           dict(state=p0_state, raw=-1,
                                note='param0=-1 是无正计时标记（登记口径），不是 -1 秒/永久；不补时长'))
        if not (p0 > 0):
            return _reject('DURATION_PARAM0_NOT_POSITIVE', gates,
                           dict(state=p0_state, raw=crec.get('param0'), note='不补时长'))
    else:
        gates['duration'] = dict(sentence=False, param0_state=states['param0'],
                                 param0_raw=crec.get('param0'))
    # 期望值行集合必须与句面派生一致（防御力/攻撃力/移動速度 + 一定時間）
    derived = [SLOT_OF[a] for a in ATTRS3 if a in adm['attrs']]
    if '一定時間' in frag:
        derived.append('param0')
    want_keys = [f'skilllist|2003|/{p}' for p in derived]
    if sorted(want_keys) != sorted(expected_by_key):
        return _reject('ANSWER_SET_DRIFT', gates,
                       dict(expected=sorted(expected_by_key), derived=sorted(want_keys)))
    # G14 既有 B10.evaluate（APK 载体内部委托 B13）
    if b10 is None:
        b10 = B10.evaluate
    res = _call_b10(data, adm, row, skill, b10)
    if not isinstance(res, dict):
        return _reject('B10_RETURNED_NONE', gates, None)
    gates['b10_kind'] = res.get('kind')
    if res.get('kind') != 'promote':
        return _reject('B10_NOT_PROMOTED', gates, res.get('reasons'))
    gates['b10_carrier'] = [res.get('carrier_record_id'), res.get('carrier_layer')]
    if (res.get('carrier_record_id') != carrier_id
            or res.get('carrier_layer') != carrier_layer):
        return _reject('B10_CARRIER_DRIFT', gates, gates['b10_carrier'])
    if res.get('subject') != adm['subject'] or list(res.get('attrs') or []) != list(adm['attrs']):
        return _reject('B10_SUBJECT_OR_ATTRS_DRIFT', gates,
                       dict(subject=res.get('subject'), attrs=res.get('attrs')))
    ok, code, detail = _check_expected_answers(res.get('answers') or [], adm)
    if not ok:
        return _reject(code, gates, detail)
    gates['b10_value_rows'] = [dict(rule_key=a.get('rule_key'), raw_value=a.get('raw_value'),
                                    field_path=a.get('field_path'))
                               for a in res.get('answers') or []]
    return dict(accepted=True, rejection=None, gates=gates, b10=res,
                missing_keys=missing, partial_existing=partial_existing, detail=None)


# ---------------------------------------------------------------- 正式页消费
def _merge_reasons(row, res, adm, originals):
    reasons = [res['summary_reason']]
    reasons += list(res.get('extra_reasons') or [])
    reasons.append('C14-P1 补隙披露：本行原先因「已有原文数字答案」被共享生成器的 '
                   '`not answers` 守卫跳过，既有 B10/B13 门从未运行；本模块逐行重跑同一门并'
                   '要求 promote，只补' + '、'.join(sorted({a['rule_key'] for a in adm['answers']}))
                   + ' 值行。共享守卫未改动、未全局放宽；非目标行一行不处理。')
    if originals:
        reasons.append('本行既有原文数字答案（%s）保持不变，其字段关联仍未知；本批只补 '
                       'skilllist|2003| 值行，不改写原文数字答案。'
                       % '、'.join(str(a.get('value')) for a in originals))
    row['unknown_reasons'] = list(dict.fromkeys(reasons))


def _append(row, answers):
    key = lambda a: (a.get('rule_key'), (a.get('source') or {}).get('record_id'),
                     (a.get('source') or {}).get('layer'), a.get('field_path'))
    existing = {key(a) for a in row.get('answers') or []}
    added = []
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault('answers', []).append(answer)
        existing.add(key(answer))
        added.append(answer)
    return added


def _row_provenance(row, adm, res, partial_preexisting=False):
    is_b13 = any(a['evidence_scope'] == B13_SCOPE for a in adm['answers'])
    tag = B13.B13_TAG if is_b13 else B10.B10_TAG
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = tag
    row['numeric_evidence'] = '推断'
    row['association_evidence'] = '推断'
    row['partial'] = True
    scopes = row.get('evidence_scope') or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row['evidence_scope'] = sorted(set(scopes) | {a['evidence_scope'] for a in adm['answers']})
    carrier_id, carrier_layer = adm['carrier']['record_id'], adm['carrier']['layer']
    carrier_name = adm['carrier']['name']
    if is_b13:
        row['inference_b13'] = dict(
            batch='20261022 批13', family=B13.B13_FAMILY, table=adm['table'],
            record_id=adm['record_id'], layer=adm['layer'],
            carrier_record_id=carrier_id, carrier_layer=carrier_layer,
            carrier_name=res.get('carrier_name') or carrier_name,
            via=res.get('via'), via_pattern=res.get('via_pattern'),
            cross_layer=res.get('cross_layer'), replaces_hint=res.get('replaces_hint'),
            subject=res.get('subject'), attrs=res.get('attrs'), claims=res.get('claims'),
            sent_no=res.get('sent_no'), sent_total=res.get('sent_total'))
        row.pop('inference_b10', None)
    else:
        row['inference_b10'] = dict(
            batch='20261022 批10', family=B10.family_for(adm['table']), table=adm['table'],
            record_id=adm['record_id'], layer=adm['layer'],
            carrier_record_id=carrier_id, carrier_layer=carrier_layer,
            carrier_name=res.get('carrier_name') or carrier_name,
            via=res.get('via'), via_pattern=res.get('via_pattern'),
            subject=res.get('subject'), attrs=res.get('attrs'), claims=res.get('claims'),
            sent_no=res.get('sent_no'), sent_total=res.get('sent_total'))
        row.pop('inference_b13', None)
    row[MARKER_KEY] = dict(
        scope=SCOPE, module=MODULE_VERSION, batch='C14-P1',
        row_id=adm['row_id'], cid=adm['cid'],
        admission=ADMISSION,
        global_guard=('card_page_data.py 的 `table in B10.TABLES and not answers` 调用守卫'
                      '未改动、未全局放宽'),
        parent=dict(table=adm['table'], record_id=adm['record_id'], layer=adm['layer'],
                    reference_field=adm['reference_field'],
                    source_key=adm['parent'][0], json_pointer=adm['parent'][1],
                    field=adm['parent'][2]),
        carrier=dict(record_id=carrier_id, layer=carrier_layer, ability=2003,
                     name=res.get('carrier_name') or carrier_name,
                     params=dict(adm['carrier']['params'])),
        subject=res.get('subject'), attrs=res.get('attrs'), claims=res.get('claims'),
        sent_no=res.get('sent_no'), sent_total=res.get('sent_total'),
        p6_isolation=('仅临时摘除本行冻结载体的进程内 P6 登记键并在调用后恢复；替代核对＝'
                      '冻结时全库共享载体检查（16 行载体跨 cid 共享=0）'),
        preexisting_original_numeric=[dict(value=a.get('value'), raw_value=a.get('raw_value'))
                                      for a in _original_numeric(row)],
        partial_preexisting=bool(partial_preexisting),
        non_yg_collateral=('Y.G. 30303 3 行 12 条；同域非 Y.G. 106/347/5302/20608/20704 '
                           '13 行 51 条（冻结准入；未放宽全局守卫）'),
        limits=('规则本体已确认（rules.json skilllist|2003| 五键）；本条数值归属＝推断；'
                'p9 为受伤量倍率加算表现层（正值增伤），不是固定防御减少；'
                '触发仅 Skill 型着弹（Normal/Critical 不触发）；不写最终扣血、不写实机'
                '时长/叠加/覆盖/玩家解锁。'))


def apply_to_groups(data, cid, groups):
    """正式页消费：只为冻结行补 B10/B13 值行（幂等；不改写既有原文数字答案）。"""
    report = dict(scope=SCOPE, cid=cid, evaluated=0, answers_added=0, additions=[],
                  markers=[], rejections=[], skipped_existing=0, marker_only=0,
                  partial_existing=0, out_of_scope=True)
    if cid not in ADMITTED_CIDS:
        return report
    report['out_of_scope'] = False
    if cid in ZERO_TOUCH_CIDS:
        report['rejections'].append(dict(reason='PROTECTED_CID', cid=cid))
        return report
    index = {}
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                index[row.get('row_id')] = (skill, row)
    for rid, adm in sorted(ADMITTED.items(), key=lambda kv: kv[0]):
        if adm['cid'] != cid:
            continue
        pair = index.get(rid)
        if pair is None:
            report['rejections'].append(dict(row_id=rid, reason='ROW_NOT_FOUND'))
            continue
        skill, row = pair
        report['evaluated'] += 1
        res = evaluate(data, cid, row, skill)
        if not res['accepted']:
            if res['rejection'] == 'ALREADY_PRESENT_SAME':
                report['skipped_existing'] += 1
                report['markers'].append(dict(row_id=rid, dedup='ALREADY_PRESENT_SAME'))
            elif res['rejection'] == 'ALREADY_ANSWERED':
                disclosure = dict(
                    scope=SCOPE, module=MODULE_VERSION, batch='C14-P1', row_id=rid, cid=cid,
                    admission=ADMISSION, dedup='ALREADY_ANSWERED',
                    existing=res['gates'].get('existing_2003'),
                    disclosure='本行已有同 rule_key 答案且值/记录/层不一致；不新增、不改写，只披露。')
                if row.get(MARKER_KEY) != disclosure:
                    row[MARKER_KEY] = disclosure
                    report['marker_only'] += 1
                    report['markers'].append(dict(row_id=rid, dedup='ALREADY_ANSWERED'))
            else:
                report['rejections'].append(dict(row_id=rid, reason=res['rejection'],
                                                 detail=res.get('detail')))
            continue
        b10 = res['b10']
        added = _append(row, b10['answers'])
        if not added:
            report['skipped_existing'] += 1
            continue
        if res.get('partial_existing'):
            report['partial_existing'] += 1
        _merge_reasons(row, b10, adm, _original_numeric(row))
        _row_provenance(row, adm, b10, res.get('partial_existing'))
        report['answers_added'] += len(added)
        for answer in added:
            report['additions'].append(dict(
                row_id=rid, rule_key=answer.get('rule_key'),
                field_path=answer.get('field_path'), raw_value=answer.get('raw_value'),
                source_record=(answer.get('source') or {}).get('record_id'),
                source_layer=(answer.get('source') or {}).get('layer'),
                evidence_scope=answer.get('evidence_scope')))
    return report


def freeze_summary():
    """冻结表机器摘要（候选 README／检查脚本共用）。"""
    per_cid = {}
    for item in _ADMITTED_LIST:
        d = per_cid.setdefault(str(item['cid']), dict(yg=item['cid'] == 30303, rows=0,
                                                      answers=0))
        d['rows'] += 1
        d['answers'] += len(item['answers'])
    return dict(rows=len(_ADMITTED_LIST), cids=len(ADMITTED_CIDS),
                answers=sum(len(i['answers']) for i in _ADMITTED_LIST),
                carriers=len({(i['carrier']['record_id'], i['carrier']['layer'])
                        for i in _ADMITTED_LIST}),
                per_cid=per_cid, scope=SCOPE, module=MODULE_VERSION,
                admission=ADMISSION, zero_touch_cids=sorted(ZERO_TOUCH_CIDS))


if __name__ == '__main__':
    raise SystemExit('C14-P1 候选模块不提供写入口；检查请运行 check_candidate.py')
