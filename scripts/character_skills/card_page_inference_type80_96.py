# -*- coding: utf-8 -*-
"""type80（HoldMana，一次性玛那条件增益）与 type96（ManaCountUp，逐珠线性增益）成对批。

任务书：``docs/tasks/20261028-type80-96-batch.md``。规则引用
``docs/角色技能完整解读实施方案.md``（2026-10-24 修订，含 §1.3）。原生证据：
``output/character_skills/skilllist_types/composite_chains.json``（P2 第 5 批，20 条分支体）、
``dispatch_map.json``、``crit_anchoring.json``（本批**不做新反汇编**）。协作者对照
``output/reference_analysis/cc_20261027/``（conflicts.md#C2、merge_recommendations A8/A9）。

两族语义严格分开（C2 防线）
---------------------------
* **type80 一次性**：条件成立时把系数**乘/加一次**；没有按珠数循环的乘子。
  条件＝``PanelManaGage.isCurrentManaJob_or/and(job_flag=iParam0, num=int(param0))``：
  ``param6`` 为有限值且 ``int(param6)==0`` → **or**（任一命中职业的当前玛那 ≥ num），
  否则 → **and**（位图内全部职业都要 ≥ num）；``iParam0==0`` 时比较**当前玛那总数**；
  比较含等于。槽位：攻 param1／移 param2／受伤量 param3（**都是 fmul 乘算**）＋
  暴击率 param7（pp，**fadd 加算**）／暴伤 param8（系数，**fadd 加算**）。
  **80 的暴击槽是 param7/param8，不是 type67 的 param6/param7**——本模块按
  ``composite_chains.json#crit_rate/80``（get_param7 @0x11195ac → fadd s9,s9,s0 @0x11195b0）
  与 ``crit_dmg/80``（get_param8 @0x1119dbc → fadd @0x1119dc0）逐条核对。
* **type96 逐珠线性**：``×(1 + 系数×计数)``（攻击/移速/受伤量）或 ``+= 系数×计数``
  （暴击率 pp／暴伤系数）。计数对象由 ``int(param0)`` 选择：``==0`` → 斯库拉普玛那
  （``GetCurrentScrapManaNum`` 0x1242df0），否则 → ``iParam0`` 经
  ``Constants.ConvJobFlagToElementFlag`` 的当前职业元素玛那；计数 ≥1 才生效；按
  ``min(计数, int(param1))`` 计入；**``int(param1)<1`` 时不设上限（不是按 0 计）**。
  槽位：受伤量 param5／移速 param4／暴击率 param6（pp）／暴伤 param7（系数）。
  **攻击 param2/param3 本批全库 0 答案**：同一分支体读两槽，由调用级标志 ``[sp+0x18]``
  选择，含义未定位（任务书 §1）——即使 ``rules.json`` 条件文本另记 damageType 择槽，
  本批不据此出数，只写 limits/hint（差异见 build_report §5）。

范围（逐行门控，任一不满足即拒答并记原因码；不出数）
----------------------------------------------------
G1  零触碰：cid∈{30236,30239} 不进入。
G2  载体：行属 ``table=skilllist``、``layer∈{APK,CACHE}``；记录 + sub 递归**同层**解析
    （``_mdSkill.json`` / ``skilllist.data5.json.raw``），缺件即拒（不跨层取值）；
    答案只按载体所在层取值，另一层同 skillid 原值仅披露（``other_layer_raw``）。
G3  句族：先排除时机/获得句（マナを獲得すると／マナスロット／使用／変換／持った状態で
    開始／ピリカ），再分族：
    * 计数度句（多いほど・多い程・多ければ多いほど・多く持っている程・少ないほど・少ない程）
      ＋玛那/斯库拉普 → **96 族**；
    * 持有谓句（〜マナを所持している／〜マナを保持している／〜マナの場合／マナを所持）→
      **80 族**。
    两族都不中 → SENTENCE_NOT_IN_FAMILY（不立注记）。
G4  目标：句面出现「味方」→ 不是自身 apply 路径（80/96 都只作用于装载者自身）→
    ALLY_TARGET_NOT_SELF。
G5  无既有答案：行 ``answers`` 必须为空（零答案行）；否则 ALREADY_ANSWERED（不改旧值）。
G6  载体唯一（同层、同句族）：
    * 80：句面职业集合 → 位图（戦士1/弓使い2/魔法使い4/僧侶8/騎士16）；「〜以外」取
      31 去掉该位。句面点名职业 → 候选＝同层链内 iParam0 **恰等于**该位图的 80 记录；
      句面未点名职业 → 候选＝链内全部 80 记录（且必须恰 1 条、iParam0∈{0,31}）。
      去重后 ≠1 → NO_CARRIER / CARRIER_NOT_UNIQUE / JOB_SET_MISMATCH。
    * 96：计数对象由句面判定——只提「スクラップ」→ param0==0 记录；只提「マナ」且点名
      职业 → param0≠0 且 iParam0 恰等于该位图的记录；「マナかスクラップ」两对象同时出现
      → COUNT_OBJECT_AMBIGUOUS（不猜）；「スクラップの場合」→ param0==0 记录。
      `int(param0)==0` 含 param0 缺失/0（get_param0 返回 0）。
      去重后 ≠1 → NO_CARRIER / CARRIER_NOT_UNIQUE。
    * 80 载体但句面为逐珠度句（如「マナが多いほど」）→ C2_ONE_SHOT_VS_PER_ORB：
      **不得**把一次性增益写成每颗 n%。
G7  规则可用：``rules.answer_for`` 返回 ``CONFIRMED_NUMERIC`` 且 ``rule_for`` 状态含
    「已确认」。``skilllist|80|/param1,/param2,/param3,/param7,/param8`` 与
    ``skilllist|96|/param1,/param4,/param5,/param6,/param7`` 均**已存在**（P2 第 5 批
    复合分支体登记，rules 290 键）；本模块不改 rules.json / rules.py。
G8  槽位点名：只答句面**点名**的属性（攻撃力/防御力/移動速度/クリティカル発生率/
    クリティカル威力）。「効果が上がり」不点名 → 不展开（本批按任务书「句面点名槽位」，
    与 mana_b 的父句展开口径不同，见 build_report §5）。无可答槽 → NO_NAMED_SLOT。
G9  非中性：所点槽系数须非中性（倍率≠1／加算≠0）；96 的 param2/param3 **一律不答**。
G10 方向：上がる/下がる × 槽位语义（受伤量乘数反向）；不符 → SIGN_MISMATCH。

答案文本口径：
* 80 写「一次性」：条件成立时乘/加一次，不随玛那数量累加；条件文本含 or/and 选择码与
  ``iParam0==0`` 总玛那口径。
* 96 写「每颗（斯库拉普/职业）玛那 × 计数」：捕 min(计数, param1) 上限，``int(param1)<1``
  写「不设上限」；计数 ≥1 才生效。
* 暴击两族都写 pp／系数加算，不写成倍率。96 攻击不写。

证据档：``mana_coeff_*``＝CONFIRMED_FORMULA_ONLY（另乘运行时因子）；阈值/选择码/上限＝
CONFIRMED_NUMERIC；「本句↔这组记录」归属＝推断。不承诺最终伤害/扣血；不含 Chain 与等级成长.
"""
from __future__ import annotations

import json
import math

import rules as R

MODULE_VERSION = 'type80_96_20261028'
SCOPE = 'TYPE80_96_BATCH_20261028'
TAG = '推断（模板批 type80 一次性玛那条件／type96 逐珠线性）'

TABLE = 'skilllist'
LAYERS = ('APK', 'CACHE')
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

MAX_SUB_DEPTH = 3

# ---- 句族记号 ---------------------------------------------------------------
# 时机/获得句：不是「持有玛那条件」也不是「按珠计数」，整类不出数（仍立 meta，不立 hint）。
TIMING_MARKS = ('マナを獲得', 'マナスロット', '使用', '変換', 'ピリカ',
                '持った状態で戦闘を開始', '必殺技が使えるマナが追加',
                '必殺技が使えるマナが', 'マナが追加', 'マナを全て破壊')
COUNT_MARKS = ('多いほど', '多い程', '多ければ多いほど', '多く持っている程',
               '少ないほど', '少ない程')
HOLD_MARKS = ('マナを所持', 'マナを保持', 'マナの場合', 'マナを保持している場合')
SCRAP_COND_MARKS = ('スクラップの場合',)
MANA_WORD = 'マナ'
SCRAP_WORD = 'スクラップ'
ALLY_MARKS = ('味方',)
DOWN_MARKS = ('下がる', '減少', '低下')
UP_MARKS = ('上がる', '上昇', '増加', '上がり', '増え')

# 职业位图（skilllist_types/filter_dictionary.json#job.enum：WARRIOR 0 → 1<<0 …）
JOB_BITS = (('戦士', 1), ('弓使い', 2), ('魔法使い', 4), ('僧侶', 8), ('騎士', 16))
JOB_ALL = 31

# 槽位 → 句面属性词；G8 只答被点名的属性。
SLOT_STAT = {
    80: {'param1': '攻撃力', 'param2': '移動速度', 'param3': '防御力',
         'param7': 'クリティカル発生率', 'param8': 'クリティカル威力'},
    96: {'param4': '移動速度', 'param5': '防御力',
         'param6': 'クリティカル発生率', 'param7': 'クリティカル威力'},
}
# 槽位 → 账本主张类型（与 type67 同一词表）。**按能力分表**（批 1 独审残留①，2026-10-28）：
# type80 的 param7 是暴击発生率、param8 是暴击威力；type96 是 param6 発生率／param7 威力。
# 合表会把 type80 param7 误标为「クリティカル威力」。该字段只是页面元数据（账本已改用
# effect_ledger._T8096_SLOT_EFFECT[ability][slot]、不消费本字段），纠正后数值零变化；
# 本表内容与 SLOT_STAT 逐槽相同，分表只为消除合表误配。
SLOT_EFFECT = {
    80: {'param1': '攻撃力', 'param2': '移動速度', 'param3': '防御力',
         'param7': 'クリティカル発生率', 'param8': 'クリティカル威力'},
    96: {'param4': '移動速度', 'param5': '防御力',
         'param6': 'クリティカル発生率', 'param7': 'クリティカル威力'},
}
MULT_SLOTS = {'param1', 'param2', 'param3', 'param4', 'param5'}
# 96 攻击槽：本批全库 0 答案（调用级 [sp+0x18] 择槽未证）。
T96_ATTACK_SLOTS = ('param2', 'param3')

RULE_KEYS_80 = tuple(f'skilllist|80|/{s}' for s in SLOT_STAT[80])
RULE_KEYS_96 = tuple(f'skilllist|96|/{s}' for s in SLOT_STAT[96])
# 载体链/条件/上限读取而 answers 不直接产出的规则键（口径记录用）。
READ_ONLY_KEYS = ('skilllist|80|/param0', 'skilllist|80|/param6', 'skilllist|80|/iParam0',
                  'skilllist|96|/param0', 'skilllist|96|/param1', 'skilllist|96|/iParam0')

FAMILY_80 = 'hold_mana_oneshot'
FAMILY_96 = 'mana_count_up_linear'
FAMILY_96_SCRAP_COND = 'mana_count_up_scrap_condition'

REJECT_ORDER = ('ZERO_TOUCH_CID', 'NOT_SKILLLIST_LAYER', 'TIMING_OR_GAIN_SENTENCE',
                'SENTENCE_NOT_IN_FAMILY', 'ALLY_TARGET_NOT_SELF', 'SUB_UNRESOLVED',
                'ALREADY_ANSWERED', 'C2_ONE_SHOT_VS_PER_ORB', 'NO_CARRIER',
                'CARRIER_NOT_UNIQUE', 'JOB_SET_MISMATCH', 'COUNT_OBJECT_AMBIGUOUS',
                'NO_NAMED_SLOT', 'SLOT_NEUTRAL', 'ATTACK_SLOT_UNPROVEN',
                'SIGN_MISMATCH', 'RULE_UNAVAILABLE')


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def skill_lookup(data, layer):
    """原始主表的 skillid → (index, record)。CACHE/APK 分源，不跨层。"""
    table = getattr(data, 'cache_skill' if layer == 'CACHE' else 'apk_skill', None)
    return table or {}


def resolve_chain(data, layer, record):
    """记录 + sub 递归展开（同层）；返回 (chain, unresolved)。"""
    lookup = skill_lookup(data, layer)
    chain, missing, seen = [record], [], {record.get('skillid')}
    frontier = [(record, 0)]
    while frontier:
        head, depth = frontier.pop(0)
        subs = head.get('sub') or []
        if depth >= MAX_SUB_DEPTH:
            if subs:
                missing.append(dict(parent=head.get('skillid'), reason='DEPTH_LIMIT',
                                    sub=list(subs)))
            continue
        for child in subs:
            if child in seen:
                continue
            hit = lookup.get(child)
            if hit is None:
                missing.append(dict(parent=head.get('skillid'), reason='MISSING_IN_LAYER',
                                    sub=child))
                continue
            seen.add(child)
            chain.append(hit[1])
            frontier.append((hit[1], depth + 1))
    return chain, missing


def ability_records(chain, ability):
    return [c for c in chain if c.get('ability') == ability]


def _resolve_record(data, layer, skillid):
    hit = (skill_lookup(data, layer) or {}).get(skillid)
    return hit[1] if hit else None


def _is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _int(value, default=0):
    """int 向零截断；缺失/非数值按 default（原生 get_paramN 缺字段返回 0）。"""
    if not _is_num(value):
        return default
    return int(float(value))


def named_jobs(frag, identifier):
    return [bit for word, bit in JOB_BITS if word in frag]


def jobs_text(bits):
    names = [word for word, bit in JOB_BITS if bits & bit]
    return '/'.join(names) if names else f'位图 {bits}'


def classify(frag):
    """返回 (family, reason, detail)。family∈{'80','96','96cond',None}。"""
    has_mana = MANA_WORD in frag
    has_scrap = SCRAP_WORD in frag
    if any(m in frag for m in TIMING_MARKS):
        return None, 'TIMING_OR_GAIN_SENTENCE', [m for m in TIMING_MARKS if m in frag]
    if any(m in frag for m in COUNT_MARKS):
        if has_mana or has_scrap:
            return '96', None, [m for m in COUNT_MARKS if m in frag]
        return None, 'SENTENCE_NOT_IN_FAMILY', 'COUNT_WITHOUT_MANA'
    if any(m in frag for m in SCRAP_COND_MARKS) and has_scrap:
        return '96cond', None, [m for m in SCRAP_COND_MARKS if m in frag]
    if any(m in frag for m in HOLD_MARKS) and has_mana:
        return '80', None, [m for m in HOLD_MARKS if m in frag]
    return None, 'SENTENCE_NOT_IN_FAMILY', 'NO_FAMILY_MARK'


# ---------------------------------------------------------------------------
# 载体选择
# ---------------------------------------------------------------------------
def carriers_80(data, layer, record, frag):
    """80 族载体：按句面职业位图精确匹配；返回 (candidates, info)。"""
    chain, missing = resolve_chain(data, layer, record)
    recs = ability_records(chain, 80)
    bit_list = named_jobs(frag, 80)
    bits = 0
    for bit in bit_list:
        bits |= bit
    info = dict(carriers=[r.get('skillid') for r in recs], named_bits=bits,
                negated_job=bool(bits) and '以外' in frag, missing=missing)
    if bits:
        expect = (JOB_ALL & ~bits) if '以外' in frag else bits
        info['expected_bits'] = expect
        picked = [r for r in recs if _int(r.get('iParam0'), -1) == expect]
    else:
        # 句面未点名职业 → 全职业位图（31）或 0（原生按总数比较）才与「マナ」通名相称。
        picked = [r for r in recs if _int(r.get('iParam0'), -1) in (0, JOB_ALL)]
        info['expected_bits'] = JOB_ALL
        info['generic'] = True
        if not picked and recs:
            info['job_set_mismatch'] = True
    return picked, info


def carriers_96(data, layer, record, frag, family):
    """96 族载体：按计数对象（斯库拉普 / 职业元素玛那）唯一化。"""
    chain, missing = resolve_chain(data, layer, record)
    recs = ability_records(chain, 96)
    bits = 0
    for bit in named_jobs(frag, 96):
        bits |= bit
    has_mana = MANA_WORD in frag
    has_scrap = SCRAP_WORD in frag
    info = dict(carriers=[r.get('skillid') for r in recs], named_bits=bits, missing=missing)
    if has_mana and has_scrap:
        info['ambiguous_object'] = True
        return [], info
    if has_scrap:
        picked = [r for r in recs if _int(r.get('param0'), 0) == 0]
        info['count_object'] = 'scrap'
        if bits:
            info['job_words_with_scrap'] = bits
    else:
        info['count_object'] = 'job'
        cands = [r for r in recs if _int(r.get('param0'), 0) != 0]
        if bits:
            picked = [r for r in cands if _int(r.get('iParam0'), -1) == bits]
            info['expected_bits'] = bits
        else:
            picked = [r for r in cands if _int(r.get('iParam0'), -1) in (0, JOB_ALL)]
            info['expected_bits'] = JOB_ALL
    return picked, info


def other_layer_raw(data, ability, skillid, layer, fields=('param1', 'param2', 'param3',
                                                          'param4', 'param5', 'param6',
                                                          'param7', 'param8')):
    """同 skillid 在另一层的原值（只披露，不参与换算）。"""
    other = 'APK' if layer == 'CACHE' else 'CACHE'
    rec = _resolve_record(data, other, skillid)
    if not isinstance(rec, dict) or rec.get('ability') != ability:
        return None
    return {k: rec.get(k) for k in fields if k in rec}


# ---------------------------------------------------------------------------
# 文本
# ---------------------------------------------------------------------------
def _fmt(value, digits=6):
    text = f'{float(value):.{digits}g}'
    return text


def _pp(value):
    return f'{float(value) * 100:.2f}'


def _signed_pct(value):
    pct = float(value) * 100
    if abs(pct) < 5e-5:
        return '±0%'
    return f'{"+" if pct > 0 else "-"}{abs(pct):.4g}'


def condition_80(record):
    """80 条件文本：or/and 选择码 + iParam0==0 总玛那口径（逐字写进答案）。"""
    ip0 = _int(record.get('iParam0'), 0)
    p0 = _int(record.get('param0'), 0)
    p6 = record.get('param6')
    p6_finite = _is_num(p6)
    mode = 'or' if (not p6_finite or _int(p6) == 0) else 'and'
    jobs = jobs_text(ip0) if ip0 else '无职业位（iParam0==0）'
    if ip0 == 0:
        scope = 'iParam0==0 → 比较**当前玛那总数**'
    elif mode == 'or':
        scope = f'任一命中职业（{jobs}）的当前玛那 ≥ {p0} 即成立'
    else:
        scope = f'位图内**全部**命中职业（{jobs}）的当前玛那都要 ≥ {p0}'
    if not p6_finite:
        p6_text = 'param6 缺失/非有限（原生 get_param6 返回 0）'
    elif _int(p6) == 0:
        p6_text = f'param6={_fmt(p6)}（有限且 int(param6)==0）'
    else:
        p6_text = f'param6={_fmt(p6)}（有限、int(param6)={_int(p6)}≠0）'
    return (f'条件：PanelManaGage.isCurrentManaJob_{mode}(job_flag=iParam0={ip0}'
            f'（{jobs}）, num=int(param0)={p0})；{p6_text} → {mode}：{scope}；'
            f'比较含等于（当前玛那 ≥ {p0}）；iParam0==0 时比较当前玛那总数')


def condition_96(record, info):
    obj = info.get('count_object')
    ip0 = _int(record.get('iParam0'), 0)
    p1 = record.get('param1')
    cap = _int(p1, 0) if _is_num(p1) else None
    if obj == 'scrap':
        obj_text = ('计数对象＝**斯库拉普玛那**（int(param0)==0 → PanelManaGage.'
                    'GetCurrentScrapManaNum 0x1242df0）')
    else:
        obj_text = (f'计数对象＝**{jobs_text(ip0)} 的当前职业元素玛那**'
                    f'（int(param0)={_int(record.get("param0"), 0)}≠0 → iParam0={ip0} 经 '
                    f'Constants.ConvJobFlagToElementFlag）')
    if cap is None or cap < 1:
        cap_text = f'**不设上限**（int(param1)={_fmt(p1)} < 1 时引擎不设上限，不是按 0 计）'
    else:
        cap_text = f'按 min(计数, int(param1)={cap}) 计入（上限 {cap}）'
    return f'条件：{obj_text}；计数 ≥1 才生效（GetCurrentManaNum 返回 0 时跳过）；{cap_text}'


def value_text_80(slot, raw):
    v = float(raw)
    if slot == 'param1':
        return f'攻击力 ×{_fmt(v)}（一次性：条件成立时乘一次，不随玛那数量累加）'
    if slot == 'param2':
        return f'移动速度 ×{_fmt(v)}（一次性：条件成立时乘一次）'
    if slot == 'param3':
        trend = '受伤量减少＝防御力提升' if v < 1 else ('受伤量增加＝防御力下降' if v > 1 else '中性')
        return f'受伤量 ×{_fmt(v)}（{trend}；一次性，不是固定防御量）'
    if slot == 'param7':
        return f'暴击率 +{_pp(v)}pp（一次性加算，不随玛那数量累加）'
    if slot == 'param8':
        return f'暴击伤害系数 +{_fmt(v)}（一次性加算，不是倍率、不随玛那数量累加）'
    raise KeyError(slot)


def _cap_of(record):
    p1 = record.get('param1')
    return _int(p1, 0) if _is_num(p1) else None


def value_text_96(slot, raw, record, info, down=False):
    """96 答案文本：逐颗线性 × 计数 / 加算×计数；写明计数对象、上限或不设上限、方向。

    ``down``＝句面「少ないほど」（计数越少越高）。倍率类按 ×(1+v×min(计数,cap)) 写，
    给出计数 0 与计数满两端的因子，避免读者把「每颗 −2.5%」误读成惩罚。
    """
    v = float(raw)
    cap = _cap_of(record)
    capped = cap is not None and cap >= 1
    unit_obj = ('斯库拉普玛那' if info.get('count_object') == 'scrap'
                else f'{jobs_text(_int(record.get("iParam0"), 0))}玛那')
    trend = '计数越少、加成越高' if down else '计数越多、加成越高'
    eff = -v if down else v
    if capped:
        span = f'min(计数,{cap})'
        cap_text = f'计数满 {cap} 时'
    else:
        span = '计数（int(param1)<1 → 不设上限）'
        cap_text = '不设上限，按实际计数'
    if slot == 'param4':
        if capped:
            tail = f'计数 0 时 ×1.0，计数满 {cap} 时 ×{_fmt(1 + v * cap)}'
        else:
            tail = '计数 0 时 ×1.0，此后不封顶'
        return (f'移动速度 ×(1 + {_fmt(v)}×{span})；每颗{unit_obj} {_signed_pct(v)}%；'
                f'{tail}（{trend}）')
    if slot == 'param5':
        dmg_trend = '受伤量随计数减少＝防御力提升' if eff < 0 else '受伤量随计数增加＝防御力下降'
        if capped:
            tail = f'计数 0 时 ×1.0，计数满 {cap} 时 ×{_fmt(1 + v * cap)}'
        else:
            tail = '计数 0 时 ×1.0，此后不封顶'
        return (f'受伤量 ×(1 + ({_fmt(v)})×{span})；每颗{unit_obj} {_signed_pct(v)}%；'
                f'{tail}（{dmg_trend}；{trend}）')
    if slot == 'param6':
        if capped:
            tail = f'{cap_text} +{_pp(v * cap)}pp'
        else:
            tail = '按实际计数累加（不封顶）'
        return (f'暴击率 +({_fmt(v)}×{span})×100pp＝每颗{unit_obj} +{_pp(v)}pp；{tail}'
                f'（pp 加算，不是倍率；{trend}）')
    if slot == 'param7':
        if capped:
            tail = f'{cap_text} +{_fmt(v * cap)}'
        else:
            tail = '按实际计数累加（不封顶）'
        return (f'暴击伤害系数 +({_fmt(v)}×{span})＝每颗{unit_obj} +{_fmt(v)}；{tail}'
                f'（系数加算，不是倍率；{trend}）')
    raise KeyError(slot)


# ---------------------------------------------------------------------------
# 方向与中性
# ---------------------------------------------------------------------------
def slot_neutral(slot, raw):
    v = float(raw)
    return abs(v - (1.0 if slot in MULT_SLOTS else 0.0)) < 1e-12


def direction_ok(slot, raw, frag, down_count, ability):
    """句面方向 × 槽位语义。返回 (ok, expected_direction_text)。

    净变化 Δ 的口径（原生形状）：
    * type80 的攻/移/受伤量是**乘数**（factor＝param），Δ＝param−1；暴击两槽是加算，Δ＝param。
    * type96 全是「×(1+param×计数)」/「+= param×计数」，Δ＝param（计数增方向）；
      「少ないほど」时计数向减方向，Δ＝−param。
    受伤量（param3／param5）以「受伤量减少」为防御力提升，其余以 Δ>0 为提升。
    """
    v = float(raw)
    if ability == 80 and slot in ('param1', 'param2', 'param3'):
        delta = v - 1.0
    else:
        delta = v
    if down_count:
        delta = -delta
    improves = -delta if slot in ('param3', 'param5') else delta
    wants_up = any(m in frag for m in UP_MARKS) and not any(m in frag for m in DOWN_MARKS)
    wants_down = any(m in frag for m in DOWN_MARKS) and not any(m in frag for m in UP_MARKS)
    if wants_up:
        return improves > 0, 'UP'
    if wants_down:
        return improves < 0, 'DOWN'
    return True, 'UNSPECIFIED'


# ---------------------------------------------------------------------------
# 来源与答案
# ---------------------------------------------------------------------------
def _record_key(layer, index):
    return (f'{layer}/_mdSkill.json#/skilllist/{index}' if layer == 'APK'
            else f'{layer}/skilllist.data5.json.raw#/skilllist/{index}')


def _source(data, layer, record, ability, field):
    lookup = skill_lookup(data, layer)
    hit = lookup.get(record.get('skillid'))
    index = hit[0] if hit else None
    source_key = f'{layer}/_mdSkill.json' if layer == 'APK' else 'skilllist.data5.json.raw'
    original = ('output/base_master/_mdSkill.json' if layer == 'APK'
                else 'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')
    return dict(table=TABLE, record_id=record.get('skillid'), layer=layer,
                source_key=source_key,
                record_key=_record_key(layer, index) if index is not None else None,
                json_pointer=(f'/skilllist/{index}' if index is not None else None),
                original_file=original, field=field, field_path=field,
                raw_value=record.get(field[1:]), namespace=TABLE, ability_type=ability)


ACCEPTED_STATUSES = ('CONFIRMED_NUMERIC', 'CONFIRMED_FORMULA_ONLY')


def _rule_probe(table, ability, slot, raw, record, layer):
    """G7：规则可用。type80 系数槽＝CONFIRMED_NUMERIC；type96 系数槽＝
    CONFIRMED_FORMULA_ONLY（另乘运行时计数因子，见任务书 §1 口径）；两者都要求
    rule_for 状态含「已确认」。"""
    probe = R.answer_for(table, ability, '/' + slot, raw, record, source_layer=layer)
    rule = R.rule_for(table, ability, '/' + slot) or {}
    ok = bool(probe and probe.get('answer_status') in ACCEPTED_STATUSES
              and '已确认' in str(rule.get('status') or ''))
    return ok, probe or {}, rule


def build_answer_80(cid, row, layer, carrier, slot, data, info, extra_note=''):
    raw = carrier.get(slot)
    ok, probe, rule = _rule_probe(TABLE, 80, slot, raw, carrier, layer)
    other = other_layer_raw(data, 80, carrier.get('skillid'), layer)
    cond = condition_80(carrier)
    layer_note = ''
    if other and 'param' in ''.join(other.keys()):
        diff = {k: v for k, v in other.items() if _is_num(v) and _is_num(raw)
                and k == slot and abs(float(v) - float(raw)) > 1e-9}
        if diff:
            layer_note = (f'；同 skillid {carrier.get("skillid")} 在另一层 '
                          f'{slot}={_fmt(diff[slot])}，按载体层 {layer} 取值（不跨层混用）')
    return dict(
        value=value_text_80(slot, raw),
        quantity_kind=probe.get('quantity_kind'),
        unit=probe.get('unit'),
        raw_value=raw,
        field_path='/' + slot,
        numeric_source='规则',
        numeric_evidence='确认',
        association_evidence='推断',
        evidence_scope=SCOPE,
        rule_key=f'skilllist|80|/{slot}',
        rule_body_status=rule.get('status'),
        rule_status=rule.get('status'),
        answer_status=probe.get('answer_status'),
        conversion=rule.get('conversion'),
        base_definition=probe.get('base_definition'),
        conditions=probe.get('conditions'),
        rule_limits=probe.get('rule_limits') or rule.get('limits'),
        target=rule.get('target'),
        evidence=['output/character_skills/profiles/rules.json#skilllist|80|/' + slot,
                  'output/character_skills/skilllist_types/composite_chains.json#' +
                  {'param1': 'attack/80', 'param2': 'move/80', 'param3': 'defence/80',
                   'param7': 'crit_rate/80', 'param8': 'crit_dmg/80'}[slot],
                  'output/reference_analysis/cc_20261027/merge_recommendations.md#A8'],
        source=_source(data, layer, carrier, 80, '/' + slot),
        table=TABLE, record_id=carrier.get('skillid'), layer=layer,
        binding={'type80_96_binding': dict(
            scope=SCOPE, family=FAMILY_80, form='ONE_SHOT', ability=80,
            row_id=row.get('row_id'), slot=slot, effect_type=SLOT_EFFECT[80][slot],
            rule_key=f'skilllist|80|/{slot}', carrier_record_id=carrier.get('skillid'),
            carrier_layer=layer, carrier_ability=80, raw=raw,
            param0=_int(carrier.get('param0'), 0), param6=carrier.get('param6'),
            mode=('or' if (not _is_num(carrier.get('param6'))
                           or _int(carrier.get('param6')) == 0) else 'and'),
            iParam0=_int(carrier.get('iParam0'), 0),
            iParam0_total=(_int(carrier.get('iParam0'), 0) == 0),
            job_bits=info.get('expected_bits'),
            other_layer_raw=other)},
        note=('一次性的玛那条件增益（原生 fmul/fadd 各一点；条件成立时只乘/加一次，'
              '不随玛那数量累加）；' + cond +
              '；目标对象＝本记录实际装载者自身；以能力被装载并进入玩家侧 apply 路径为前提'
              + layer_note + extra_note),
        quantitative=True)


def build_answer_96(cid, row, layer, carrier, slot, data, info, family, extra_note='',
                    down=False):
    raw = carrier.get(slot)
    ok, probe, rule = _rule_probe(TABLE, 96, slot, raw, carrier, layer)
    other = other_layer_raw(data, 96, carrier.get('skillid'), layer)
    cond = condition_96(carrier, info)
    layer_note = ''
    if other:
        diff = {k: v for k, v in other.items() if k == slot and _is_num(v) and _is_num(raw)
                and abs(float(v) - float(raw)) > 1e-9}
        if diff:
            layer_note = (f'；同 skillid {carrier.get("skillid")} 在另一层 '
                          f'{slot}={_fmt(diff[slot])}，按载体层 {layer} 取值（不跨层混用）')
    cap = _cap_of(carrier)
    return dict(
        value=value_text_96(slot, raw, carrier, info, down=down),
        quantity_kind=probe.get('quantity_kind'),
        unit=probe.get('unit'),
        raw_value=raw,
        field_path='/' + slot,
        numeric_source='规则',
        numeric_evidence='确认',
        association_evidence='推断',
        evidence_scope=SCOPE,
        rule_key=f'skilllist|96|/{slot}',
        rule_body_status=rule.get('status'),
        rule_status=rule.get('status'),
        answer_status=probe.get('answer_status'),
        coefficient_class='CONFIRMED_FORMULA_ONLY（另乘运行时计数因子；计数对象与上限为运行时值）',
        conversion=rule.get('conversion'),
        base_definition=probe.get('base_definition'),
        conditions=probe.get('conditions'),
        rule_limits=probe.get('rule_limits') or rule.get('limits'),
        target=rule.get('target'),
        evidence=['output/character_skills/profiles/rules.json#skilllist|96|/' + slot,
                  'output/character_skills/skilllist_types/composite_chains.json#' +
                  {'param4': 'move/96', 'param5': 'defence/96', 'param6': 'crit_rate/96',
                   'param7': 'crit_dmg/96'}[slot],
                  'output/reference_analysis/cc_20261027/merge_recommendations.md#A9'],
        source=_source(data, layer, carrier, 96, '/' + slot),
        table=TABLE, record_id=carrier.get('skillid'), layer=layer,
        binding={'type80_96_binding': dict(
            scope=SCOPE, family=family, form='PER_UNIT_LINEAR', ability=96,
            row_id=row.get('row_id'), slot=slot, effect_type=SLOT_EFFECT[96][slot],
            rule_key=f'skilllist|96|/{slot}', carrier_record_id=carrier.get('skillid'),
            carrier_layer=layer, carrier_ability=96, raw=raw,
            param0=_int(carrier.get('param0'), 0),
            count_object=info.get('count_object'),
            iParam0=_int(carrier.get('iParam0'), 0),
            cap=cap, capped=bool(cap is not None and cap >= 1),
            other_layer_raw=other)},
        note=('逐珠线性：×(1 + 系数×计数) / 暴击类 pp·系数加算（不是一次性固定值）；' + cond +
              '；攻击槽 param2/param3 本批不出数（调用级择槽未证）；'
              '目标对象＝本记录实际装载者自身；以能力被装载并进入玩家侧 apply 路径为前提'
              + layer_note + extra_note),
        quantitative=True)


# ---------------------------------------------------------------------------
# 逐行门控
# ---------------------------------------------------------------------------
def evaluate(cid, layer, table, record, row, *, data=None):
    """单行门控。返回 dict(status=ACCEPT|REJECT, reject, gates, answers, family, carrier)。"""
    row = row or {}
    frag = str(row.get('japanese') or '')
    gates = {}
    if cid in ZERO_TOUCH_CIDS:
        return dict(status='REJECT', reject='ZERO_TOUCH_CID',
                    gates={'G1_not_zero_touch': False}, answers=[], family=None, carrier=None)
    gates['G1_not_zero_touch'] = True
    family, reason, detail = classify(frag)
    if family is None and reason == 'SENTENCE_NOT_IN_FAMILY':
        # 不属本批句族：不立注记（由调用方按 status='OUT_OF_FAMILY' 直接跳过）。
        return dict(status='OUT_OF_FAMILY', reject=None, gates=gates, answers=[],
                    family=None, carrier=None)
    if not (table == TABLE and layer in LAYERS and isinstance(record, dict)):
        return dict(status='REJECT', reject='NOT_SKILLLIST_LAYER',
                    gates={**gates, 'G2_carrier': False}, answers=[], family=family,
                    carrier=None)
    gates['G2_carrier'] = True
    if family is None:
        return dict(status='REJECT', reject=reason,
                    gates={**gates, 'G3_sentence': False}, answers=[], family=None,
                    carrier=None, detail=detail)
    gates['G3_sentence'] = True
    if any(m in frag for m in ALLY_MARKS):
        return dict(status='REJECT', reject='ALLY_TARGET_NOT_SELF',
                    gates={**gates, 'G4_self_target': False}, answers=[], family=family,
                    carrier=None)
    gates['G4_self_target'] = True
    if row.get('answers'):
        return dict(status='REJECT', reject='ALREADY_ANSWERED',
                    gates={**gates, 'G5_zero_answers': False}, answers=[], family=family,
                    carrier=None)

    if family == '80':
        picked, info = carriers_80(data, layer, record, frag)
        if info.get('missing'):
            return dict(status='REJECT', reject='SUB_UNRESOLVED',
                        gates={**gates, 'G2_sub_resolved': False, 'G5_zero_answers': True},
                        answers=[], family=family, carrier=None, missing=info['missing'])
        if not picked:
            code = 'JOB_SET_MISMATCH' if info.get('job_set_mismatch') else 'NO_CARRIER'
            return dict(status='REJECT', reject=code,
                        gates={**gates, 'G6_carrier_unique': False,
                               'G5_zero_answers': True},
                        answers=[], family=family, carrier=None, info=info)
        if len({r.get('skillid') for r in picked}) != 1:
            return dict(status='REJECT', reject='CARRIER_NOT_UNIQUE',
                        gates={**gates, 'G6_carrier_unique': False,
                               'G5_zero_answers': True},
                        answers=[], family=family, carrier=None, info=info)
        gates['G6_carrier_unique'] = True
        carrier = picked[0]
        named = [s for s, stat in SLOT_STAT[80].items() if stat in frag]
        active = [s for s in named if _is_num(carrier.get(s)) and not slot_neutral(s, carrier.get(s))]
        if not named:
            return dict(status='REJECT', reject='NO_NAMED_SLOT',
                        gates={**gates, 'G8_named_slot': False, 'G5_zero_answers': True},
                        answers=[], family=family, carrier=carrier.get('skillid'))
        if not active:
            return dict(status='REJECT', reject='SLOT_NEUTRAL',
                        gates={**gates, 'G9_non_neutral': False, 'G5_zero_answers': True},
                        answers=[], family=family, carrier=carrier.get('skillid'),
                        named=named)
        for slot in active:
            ok, want = direction_ok(slot, carrier.get(slot), frag, down_count=False, ability=80)
            gates[f'G10_direction_{slot}'] = ok
            if not ok:
                return dict(status='REJECT', reject='SIGN_MISMATCH',
                            gates={**gates, 'G5_zero_answers': True}, answers=[],
                            family=family, carrier=carrier.get('skillid'), slot=slot)
        rules_ok = {}
        for slot in active:
            ok, _probe, _rule = _rule_probe(TABLE, 80, slot, carrier.get(slot), carrier, layer)
            rules_ok[slot] = ok
        gates.update({f'G7_rule_{s}': v for s, v in rules_ok.items()})
        if not all(rules_ok.values()):
            return dict(status='REJECT', reject='RULE_UNAVAILABLE', gates=gates,
                        answers=[], family=family, carrier=carrier.get('skillid'))
        answers = [build_answer_80(cid, row, layer, carrier, slot, data, info)
                   for slot in active]
        return dict(status='ACCEPT', reject=None, gates={**gates, 'G5_zero_answers': True},
                    answers=answers, family=family, carrier=carrier.get('skillid'),
                    info=info, slots=active)

    # ---- 96 族 ---------------------------------------------------------
    picked, info = carriers_96(data, layer, record, frag, family)
    if info.get('ambiguous_object'):
        return dict(status='REJECT', reject='COUNT_OBJECT_AMBIGUOUS',
                    gates={**gates, 'G6_count_object': False, 'G5_zero_answers': True},
                    answers=[], family=family, carrier=None, info=info)
    if info.get('missing'):
        return dict(status='REJECT', reject='SUB_UNRESOLVED',
                    gates={**gates, 'G2_sub_resolved': False, 'G5_zero_answers': True},
                    answers=[], family=family, carrier=None, missing=info['missing'])
    if not picked:
        # 80 载体存在但句面是逐珠度句 → C2 明确拒（不得写成每颗 n%）
        has_80 = bool(ability_records(resolve_chain(data, layer, record)[0], 80))
        code = 'C2_ONE_SHOT_VS_PER_ORB' if has_80 else 'NO_CARRIER'
        return dict(status='REJECT', reject=code,
                    gates={**gates, 'G6_carrier_unique': False, 'G5_zero_answers': True},
                    answers=[], family=family, carrier=None, info=info)
    if len({r.get('skillid') for r in picked}) != 1:
        return dict(status='REJECT', reject='CARRIER_NOT_UNIQUE',
                    gates={**gates, 'G6_carrier_unique': False, 'G5_zero_answers': True},
                    answers=[], family=family, carrier=None, info=info)
    gates['G6_carrier_unique'] = True
    carrier = picked[0]
    named = [s for s, stat in SLOT_STAT[96].items() if stat in frag]
    active = [s for s in named if _is_num(carrier.get(s)) and not slot_neutral(s, carrier.get(s))]
    if not named:
        # 句面只点名攻击力/必殺技威力 → 落在 96 未证的攻击槽（param2/param3）上，单独记原因码。
        if '攻撃力' in frag or '威力' in frag:
            return dict(status='REJECT', reject='ATTACK_SLOT_UNPROVEN',
                        gates={**gates, 'G8_named_slot': False, 'G5_zero_answers': True},
                        answers=[], family=family, carrier=carrier.get('skillid'), info=info)
        return dict(status='REJECT', reject='NO_NAMED_SLOT',
                    gates={**gates, 'G8_named_slot': False, 'G5_zero_answers': True},
                    answers=[], family=family, carrier=carrier.get('skillid'), info=info)
    if not active:
        # 句面只点名攻击力（96 攻击槽本批不出数）或系数中性。
        if '攻撃力' in frag:
            return dict(status='REJECT', reject='ATTACK_SLOT_UNPROVEN',
                        gates={**gates, 'G9_non_neutral': False, 'G5_zero_answers': True},
                        answers=[], family=family, carrier=carrier.get('skillid'), info=info)
        return dict(status='REJECT', reject='SLOT_NEUTRAL',
                    gates={**gates, 'G9_non_neutral': False, 'G5_zero_answers': True},
                    answers=[], family=family, carrier=carrier.get('skillid'), named=named)
    down_count = any(m in frag for m in ('少ないほど', '少ない程'))
    for slot in active:
        ok, want = direction_ok(slot, carrier.get(slot), frag, down_count=down_count, ability=96)
        gates[f'G10_direction_{slot}'] = ok
        if not ok:
            return dict(status='REJECT', reject='SIGN_MISMATCH',
                        gates={**gates, 'G5_zero_answers': True}, answers=[],
                        family=family, carrier=carrier.get('skillid'), slot=slot, info=info)
    rules_ok = {}
    for slot in active:
        ok, _probe, _rule = _rule_probe(TABLE, 96, slot, carrier.get(slot), carrier, layer)
        rules_ok[slot] = ok
    gates.update({f'G7_rule_{s}': v for s, v in rules_ok.items()})
    if not all(rules_ok.values()):
        return dict(status='REJECT', reject='RULE_UNAVAILABLE', gates=gates,
                    answers=[], family=family, carrier=carrier.get('skillid'), info=info)
    fam_const = FAMILY_96 if family == '96' else FAMILY_96_SCRAP_COND
    answers = [build_answer_96(cid, row, layer, carrier, slot, data, info, fam_const,
                               down=down_count)
               for slot in active]
    return dict(status='ACCEPT', reject=None, gates={**gates, 'G5_zero_answers': True},
                answers=answers, family=fam_const, carrier=carrier.get('skillid'),
                info=info, slots=active)


# ---------------------------------------------------------------------------
# 写页
# ---------------------------------------------------------------------------
def _append(row, answer):
    def key(a):
        return (a.get('rule_key'), a.get('record_id'), a.get('field_path'))
    if any(key(a) == key(answer) for a in row.get('answers') or []):
        return False
    row.setdefault('answers', []).append(answer)
    row['row_class'] = 'A'
    row['evidence'] = '推断'
    row['evidence_label'] = TAG
    row['partial'] = True
    row['evidence_scope'] = list(dict.fromkeys(list(row.get('evidence_scope') or []) + [SCOPE]))
    marker = row.setdefault('inference_type80_96', dict(scope=SCOPE, claims=[]))
    binding = answer['binding']['type80_96_binding']
    marker['claims'].append(dict(family=binding['family'], form=binding['form'],
                                 ability=binding['ability'], slot=binding['slot'],
                                 record_id=answer['record_id'],
                                 rule_key=answer['rule_key'], value=answer['raw_value']))
    return True


def _hint(row, reason, detail=None):
    text = f'{TAG}：{reason}'
    if detail:
        text += f'（{detail}）'
    row['inference_type80_96_hint'] = text
    row.setdefault('inference_type80_96_meta', dict(scope=SCOPE, reason=reason,
                                                    detail=detail))
    return text


def apply_to_groups(data, cid, groups):
    """正式页消费：为 80 持有条件句 / 96 逐珠句绑定本批答案（不覆盖/不删除既有答案）。"""
    report = dict(scope=SCOPE, cid=cid, answers_added=0, additions=[], rejections=[],
                  hints=0, skipped_existing=0, evaluated=0, out_of_family=0,
                  timing_skipped=0, families={}, attack_refused_rows=0)
    if cid in ZERO_TOUCH_CIDS:
        report['zero_touch'] = True
        return report
    for group in groups or []:
        for skill in group.get('skills') or []:
            if skill.get('table') != TABLE:
                continue
            rows = skill.get('rows') or []
            if not rows:
                continue
            layer = skill.get('layer')
            record = _resolve_record(data, layer, skill.get('record_id'))
            for row in rows:
                frag = str(row.get('japanese') or '')
                if MANA_WORD not in frag and SCRAP_WORD not in frag:
                    continue
                report['evaluated'] += 1
                res = evaluate(cid, layer, skill.get('table'), record, row, data=data)
                if res['status'] == 'OUT_OF_FAMILY':
                    report['out_of_family'] += 1
                    continue
                if res['reject'] == 'TIMING_OR_GAIN_SENTENCE':
                    # マナ獲得/マナスロット/使用/変換/開始 等时机句：不是本批句族，
                    # 不立 hint（避免动到其他机制的句行）。
                    report['timing_skipped'] = report.get('timing_skipped', 0) + 1
                    continue
                if res['status'] != 'ACCEPT':
                    if res['reject'] == 'ALREADY_ANSWERED':
                        report['skipped_existing'] += 1
                        continue
                    if res['reject'] == 'ATTACK_SLOT_UNPROVEN':
                        report['attack_refused_rows'] += 1
                    if res['reject'] == 'SIGN_MISMATCH' and res.get('slot') in T96_ATTACK_SLOTS:
                        report['attack_refused_rows'] += 1
                    detail = res.get('detail')
                    if not detail:
                        parts = [f'{k}={v}' for k, v in sorted(res['gates'].items()) if not v]
                        detail = '；'.join(parts) or None
                    _hint(row, res['reject'], detail)
                    report['hints'] += 1
                    report['rejections'].append(dict(row_id=row.get('row_id'),
                                                     reason=res['reject'],
                                                     family=res.get('family'),
                                                     carrier=res.get('carrier')))
                    continue
                added = 0
                for ans in res['answers']:
                    if _append(row, ans):
                        added += 1
                        b = ans['binding']['type80_96_binding']
                        report['additions'].append(dict(
                            row_id=row.get('row_id'), family=b['family'], slot=b['slot'],
                            rule_key=ans['rule_key'], value=ans['value'],
                            raw_value=ans['raw_value'], carrier=ans['record_id'],
                            carrier_layer=ans['layer'], ability=b['ability'],
                            count_object=b.get('count_object'), cap=b.get('cap')))
                report['answers_added'] += added
                report['families'][res['family']] = report['families'].get(res['family'], 0) + added
                row.setdefault('type80_96_gate', dict(res['gates']))
                if res['family'].startswith('mana_count_up') and '攻撃力' in frag:
                    # 攻击槽本批不出数：在已出数行留可审标记（不改行答案）。
                    row['type80_96_attack_slot'] = dict(
                        scope=SCOPE, reason='ATTACK_SLOT_UNPROVEN',
                        detail='type96 攻击 param2/param3 由调用级 [sp+0x18] 择槽，含义未证；'
                               '本批全库 0 答案')
    return report


def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='type80/96 成对批：句族/载体只读探针')
    ap.add_argument('--text', help='单句测试（句族与点名槽位）')
    args = ap.parse_args(argv)
    if args.text:
        frag = args.text
        family, reason, detail = classify(frag)
        print(json.dumps(dict(
            family=family, reason=reason, detail=detail,
            named_jobs=[w for w, _b in JOB_BITS if w in frag],
            named_slots_80=[s for s, st in SLOT_STAT[80].items() if st in frag],
            named_slots_96=[s for s, st in SLOT_STAT[96].items() if st in frag],
            ally=any(m in frag for m in ALLY_MARKS),
            down_count=any(m in frag for m in ('少ないほど', '少ない程'))),
            ensure_ascii=False, indent=1))
        return 0
    ap.print_help()
    return 2


if __name__ == '__main__':
    raise SystemExit(_main())
