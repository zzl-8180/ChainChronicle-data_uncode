"""模板作用域推断层——批 12：ability1095 扩域（tier B 94 行 p2/p5/p6 整行晋级）。

前置与依据：批 12 第一步（案 A，20261022）已把 rules.json ``skilllist|1095`` 的
param2/param5/param6 三键 occurrences 由「已核 ID 数」（1/1/2）扩为「当前 v3 CACHE
ability=1095 全部根记录字段存在数」（407/211/407，与 p1/p3 同域同义）——受控检查
9 项边界＋p2 407/p5 211/p6 407 全域公式核对落盘
``output/ordinary_effects/ability1095/native_checks.json`` 顶层 ``b12_extension``
（无新反汇编、未实机；规则域审计
``output/character_skills/inference_inventory/b12_1095ext_scope.md``）。

本批行集＝批 11 tier B **94 行**（全库；Y.G. 38；分类文件
``work/character_skills_b11_sa1095/b11_rows_classified.json`` category=
``hint:slot-rule-not-in-domain``）：形状完美（主张属性集↔sub 非中性活性槽双向相等
94/94）、方向 0 违例、G1′ 句唯一 94/94、n_sub1095 全 1、与批 11 tier A 34 行
cid/row/父三零交集。批 12 第一步规则域扩展后，这 94 行**整行晋级**（不再保守案
留 hint ``slot-rule-not-in-domain``）。

门控（逐行重验，与批 11 完全同门——复用 B11 的门实现，保证不漂移）：

* P0 链：行源＝普通 skilllist 父记录，sub[] 恰 1 个 ability=1095 记录；
* P1 片段：japanese 恰为基础句正则（B11.BASE_RE）；
* P2 域：sub 落在 v3 CACHE 407 条样本域；
* P4 形状（双向）＋未推广槽（p4/p7/p8 活性即不符）；
* P5 方向（p1>1／p3<1／p2>1／p5>0／p6>1.5）；
* P6 对象（rules target＝装有者自身；句面省略主语）；
* G1′ 句唯一＋P3 跨 cid 载体竞争守卫。
任何一门不过 → 返回 None（批 11 evaluate 照常接管、留原有 hint——本批不产生
任何新 hint、不静默丢弃）；**主张⊆{p1,p3} 的行也返回 None（批 11 tier A 34 行
零触碰，仍由 B11 晋级、键 inference_b11）**。仅当全部门通过且主张含 p2/p5/p6
（扩域解锁槽）时，本批整行晋级。

值行（rule_key 允许 ``skilllist|1095|/param1|/param2|/param3|/param5|/param6``；
全部经 rules.py 既有 1095 换算器出值——p1 ``_mult_kind``、p3 ``_take_kind``、
p2 ``_move``、p5 ``_pp``（直接加算，不套减 1.5）、p6 ``_crit_dmg(value−1.5)``）：

* p1 攻击倍率：攻击因子乘原值，本项提高 (原值−1)×100%；
* p3 受伤量倍率：受伤量乘原值，本项减伤 (1−原值)×100%（**不是固定防御量**）；
* p2 移动乘数：移动因子乘原值（×原值）；
* p5 暴击概率直接加算：+pp（**不套 Always3 减 1.5 规则**）；
* p6 暴伤 delta＝原值−1.5（pp，系数增量）；
* p5/p6 中性（p5 缺席＝中性；p6=1.5）**如实不写值**——P4 形状门保证中性槽不在
  主张内，中性不补写、缺字段不补零（rule limits 口径）。

值行披露两层区分：**「规则本体已确认（样本域扩至 407 根记录，新增 6–9 项受控
检查）」与「本条归属推断（模板批 12 1095 扩域）」**；p2/p5/p6 值行披露扩域口径
（原已核 ID 数→407 根记录存在数）；p1/p3 值行口径未变（407 存在数）。

行级：标注「推断（模板批 12 1095 扩域）」、evidence_scope=TEMPLATE_BATCH12_1095EXT、
metadata 键 ``inference_b12``（含 replaces_hint='inference_b11_hint' 溯源）——
批 11 的 tier B hint 键在这 94 行按**行级替换**为 inference_b12（接线保证 B11
evaluate 不再对该行执行，无 ``inference_b11_hint`` 键，**不双登记**）。

硬边界（沿用批 11 口径）：

* 只升「推断」；不进整行确认；sub[] 装载路径无原生核实（归属＝数据侧结构对应），
  永不据此升「确认」。
* 证据按字段（INFR-01）：复用 B11 证据解析——p1/p3 → output/ordinary_effects/
  ability1095/＋ordinary_rules/；p2/p5/p6 → output/card_comparison_cid30236/
  {movement,critical}/（规则 origin 相对基）；存在性检查，缺失显式失败。
* 条件文本逐字入 note；对象=自身（rules target 逐字）；同父其他 sub 登记不消费、
  不跨记录合并；批 11 tier A 34 行、批 5 65000001 跨表链、批 9/10 链零触碰；
  APK 52 sub/35 父域外已由批 14 扩域分配（B12.evaluate 对 APK 载体返回 None、由批 14
  按载体层域接管）。
* rules.json 本批零改动（三键已在批 12 第一步经管线更新，dependency_signature
  由批 12 第一步变化、本批重建 pages 自然对齐）。
"""
from __future__ import annotations

import re

import rules as R
import card_page_inference_b11_sa1095 as B11
import card_page_inference_b6_bossbuff as B6

B12_TAG = '推断（模板批 12 1095 扩域）'
B12_SCOPE = 'TEMPLATE_BATCH12_1095EXT'
B12_FAMILY = ('普通自身增益家族・ability1095 Always3 载体（「⟨ATTR⟩(と⟨ATTR⟩)*が上がる。」'
              '基础句；skilllist 父记录 sub[]→skilllist ability1095 载体；批 12 规则域'
              '扩域后 p2/p5/p6 三键解锁，tier B 94 行整行晋级——批 11 tier B hint '
              'slot-rule-not-in-domain 的行级替换）')

TABLES = B11.TABLES  # skilllist（接线门同批 11：group ∉ {sympathy, crossworld}）

# 扩域后全域五槽（批 12 第一步 rules.json 三键 occurrences 407/211/407）。
DOMAIN_SLOTS = {'param1', 'param2', 'param3', 'param5', 'param6'}
# 扩域解锁槽→（原 occurrences 已核 ID 数, 新 occurrences 存在数）（rules.json 登记值）。
EXT_OCC = {'param2': (1, 407), 'param5': (1, 211), 'param6': (2, 407)}

_RULED_ID_SLOTS = B11.RULED_ID_SLOTS  # {'param2':['65000001'],'param5':['65000001'],'param6':['43023601','65000001']}


def _ext_domain_note(rule, param):
    """p2/p5/p6 扩域口径披露（原已核 ID 数→407 根记录存在数；rules.json 登记值原样引用）。"""
    old, new = EXT_OCC[param]
    return (f'批 12 扩域口径：该规则登记 occurrences={rule.get("occurrences")}（origin '
            f'{B11._rule_origin(rule)}），由批 11 时「已核 ID 数」{old}'
            f'（{_RULED_ID_SLOTS[param]}）改为当前 v3 CACHE ability=1095 全部 {new} 条'
            '根记录字段存在数（与 p1/p3 同域同义）；样本域扩至 407 根记录，新增 6–9 项'
            '受控检查（output/ordinary_effects/ability1095/native_checks.json 顶层 '
            'b12_extension：9 项边界记录×资格真假＋p2 407/p5 211/p6 407 全域公式核对），'
            '无新反汇编、未实机')


def _unit_desc(param, raw):
    if param == 'param1':
        return '单位：本项攻击倍率（攻击因子乘原值；提高 (原值−1)×100%；无量纲倍率，非百分点加算）'
    if param == 'param3':
        return ('单位：受伤量倍率（受伤量乘原值；本项减伤 (1−原值)×100%；'
                '不是固定防御量）')
    if param == 'param2':
        return '单位：移动速度乘数（移动因子乘原值＝×原值；非加算百分点）'
    if param == 'param5':
        return ('单位：暴击概率直接加算（＋pp，对 0 的加算增量；'
                '不套 Always3 的减 1.5 规则）')
    return ('单位：暴伤 delta＝原值−1.5（系数增量，攻击时在基础 1.5 暴击系数上加 delta；'
            '基础 1.5 在攻击侧另行加回，0x153b6e4）')


_B12_NATIVE_NOTE = ('记录侧＝1095 数据路径（既有 5 反汇编片段：p1 GetAbilityAttack/attack_multiply/'
                    'attack_dispatch、p3 GetAbilityDefence/defence_getter_multiply/defence_dispatch；'
                    'p2 walk_self_dispatch+walk_small_types 的 cmp #0x447→IsEnableAbility→'
                    'get_param2→fmul；p5 critical/chance_dispatch_and_add get_param5→fadd 直接加算；'
                    'p6 critical/damage_baseline_and_dispatch＋attack_critical_base get_param6→'
                    'fmov -1.5→fadd，基础 1.5 加回 0x153b6e4）；'
                    '批 12 受控检查＝既有 32 项＋b12_extension 9 项边界记录×资格真假＋p2 407/'
                    'p5 211/p6 407 全域公式核对（max_abs_deviation=0）（'
                    'output/ordinary_effects/ability1095/，无新反汇编、未实机）；'
                    '父技能 sub[] 如何安装 1095 到角色（装载路径）无原生核实——'
                    '行保持推断（批 11 scope §6 边界原样沿用）')

_B12_ASSIGN_NOTE = ('跨记录归属依据（批 11 scope §5.2/§5.4 原样沿用，批 12 未改变归属口径）：'
                    '句→1095 sub 为数据侧结构对应：行记录自身 sub[] 恰 1 个 ability=1095 记录'
                    '（每父恰 1）＋基础句主张属性集↔sub 非中性活性槽集双向相等（P4）＋方向一致'
                    '（P5）；基础句↔Always(1095)、条件句↔其他 sub 的分工为数据侧形状对照＋条件'
                    '结构对应，无引擎侧装载原生核实——本条归属不因晋级升「确认」')

_B12_REPLACE_NOTE = ('批 11→批 12 溯源：本行批 11 时因主张含 p2/p5/p6（当时规则已核 ID 数口径 '
                     '1/1/2 域外）整行留 hint「slot-rule-not-in-domain」（保守案 scope §5.3）；'
                     '批 12 第一步三键扩域（407/211/407 存在数口径）后按本批整行晋级——'
                     '行级键由 inference_b11_hint 按行级替换为 inference_b12（不双登记）；'
                     '批 11 tier A 34 行（主张⊆{p1,p3}）零触碰、仍为 inference_b11 键')

_B12_PROMO_NOTE = ('整行晋级构成（批 12）：行值行覆盖主张全部槽（p1/p2/p3/p5/p6 一并出值）；'
                   '中性槽不补写、缺字段不补零（p5 缺席＝中性、p6=1.5 中性均如实不写值）；'
                   '1095 无 param0 时限槽；p4/p7/p8 语义未推广（活性即形状不符留批 11 hint）')


def _promote12(frag, table, layer, record_id, cid, claimed, subject_phrase, sub_id, subrec,
               parent_ability, other_sub_abilities, sent_no, sent_total):
    """批 12 晋级行：值行覆盖主张全部槽（含扩域解锁的 p2/p5/p6）。"""
    sub_key = f'skilllist|{sub_id}|CACHE'
    parent_key = f'skilllist|{record_id}|{layer}'
    chain_desc = (f'{parent_key} sub[]→{sub_key}'
                  f'(ability1095,Always3"{(subrec.get("name") or "")[:20]}")')
    numeric_source = f'模板推断（批 12 1095 扩域：{chain_desc}）'
    claimed_slots = [B11.ATTR_SLOT[a] for a in claimed]
    beyond = sorted(s for s in claimed_slots if s in ('param2', 'param5', 'param6'))
    answers = []
    for attr in claimed:
        param = B11.ATTR_SLOT[attr]
        raw = subrec.get(param)
        rule = R.rule_for('skilllist', 1095, '/' + param)
        converted = R.answer_for('skilllist', 1095, '/' + param, raw, subrec)
        evidence_files = B11._field_evidence(param)
        ext_note = (f'{_ext_domain_note(rule, param)}；' if param in beyond else
                    '该规则键批 12 未改动（p1/p3 occurrences=407 存在数口径，批 11 时已全域）；')
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B12_SCOPE,
            rule_key=f'skilllist|1095|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=sub_id, layer='CACHE',
                        record_key=sub_key),
            note=(f'模板批 12 1095 扩域值行（来源 sub＝{sub_key}，ability=1095；链：'
                  f'{chain_desc}）；基础句「{frag}」的「{attr}」→/{param} 映射'
                  '（批 11 scope §5.1 字段映射原样沿用）；'
                  f'规则键 skilllist|1095|/{param}；原值 {raw}；{_unit_desc(param, raw)}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身；'
                  '样本域扩至 407 根记录，新增 6–9 项受控检查——9 项边界记录×资格真假＋'
                  'p2/p5/p6 全域公式核对，无新反汇编）；'
                  f'{ext_note}'
                  '本条数值归属＝推断（模板批 12 1095 扩域：唯一 sub[]→1095 载体＋句面形状'
                  '匹配为数据侧结构对应，引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'方向审核：{B11._direction_note(attr, raw)}；'
                  '证据按字段（INFR-01）：rules.json skilllist|1095|/'
                  f'{param} evidence→'
                  + ('output/ordinary_effects/ability1095/＋output/card_comparison_cid30236/'
                     'ordinary_rules/' if param in ('param1', 'param3') else
                     'output/card_comparison_cid30236/movement|critical/（origin 相对基）')
                  + '；'
                  f'{B11._TARGET_NOTE}；'
                  f'条件逐字：句面「{frag}」；'
                  f'样本域：批 12 扩域后 p2/p5/p6 与 p1/p3 同域（occurrences '
                  f'{R.rule_for("skilllist", 1095, "/param2").get("occurrences")}/'
                  f'{R.rule_for("skilllist", 1095, "/param5").get("occurrences")}/'
                  f'{R.rule_for("skilllist", 1095, "/param6").get("occurrences")}，'
                  f'p1/p3=407；本行 sub 记录未逐条核对，按规则适用条件披露，'
                  '不属逐记录确认）'),
            quantitative=True))

    extra = [
        _B12_NATIVE_NOTE,
        _B12_ASSIGN_NOTE,
        _B12_REPLACE_NOTE,
        _B12_PROMO_NOTE,
        ('B1 防线披露：本批载体主张只认行记录（父 skilllist）自身 sub[] 数组内 ability=1095 '
         '记录；批 9 sub_effect 链、批 10 s_ability 链、批 5 job_ability 跨表链均不消费'
         '（三套 1095 相关命名空间分清，批 11 scope §0；65000001 不入本批任何值行）'),
        B11._TARGET_NOTE,
    ]
    if other_sub_abilities:
        extra.append('同父其他 sub 登记（不消费、不跨记录合并）：ability=' +
                     '、'.join(str(a) for a in other_sub_abilities) +
                     '；条件增强半句/敵侧半句（如有）归属这些 sub 为形状对照推断'
                     '（批 11 scope §2.2），本值行不吸收其数值')
    else:
        extra.append('同父其他 sub：无（父 sub[] 仅此 1 个 1095 记录）')
    summary = (B12_TAG + '：自身增益值行来源＝' + chain_desc + '；值行全部「推断」，不升'
               '「确认」，不进入整行确认。本行批 11 时为 tier B 保守案 hint '
               'slot-rule-not-in-domain；批 12 规则域扩域（p2/p5/p6 occurrences '
               '1/1/2 已核 ID 数→407/211/407 存在数）后整行晋级，行级键按行级替换为 '
               'inference_b12（不双登记）；批 11 tier A 34 行零触碰。句→sub 归属为'
               '数据侧结构对应：唯一 sub[]→1095 载体＋基础句主张↔非中性活性槽形状匹配'
               '（双向）＋方向一致；装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露：批 12 扩域后五键 occurrences＝p1=407、p2=407、p3=407、'
                 'p5=211、p6=407（存在数口径，origin rules.json 登记值）；样本域＝当前 '
                 'v3 CACHE 普通 skilllist ability1095（Always3）的 407 条根记录；APK 52 条'
                 '已由批 14 扩域分配（occurrences_apk 登记，两域分源、不得跨层取值——批 14 '
                 '存量披露刷新）；本行来源 sub 记录未逐条核对，不属逐记录确认。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject_phrase, attrs=list(claimed),
                claims={a: B11.ATTR_SLOT[a] for a in claimed},
                beyond_slots=beyond,
                table=table, parent_ability=parent_ability,
                sub_record_id=sub_id, sub_layer='CACHE', sub_name=subrec.get('name'),
                via='own_sub_array',
                replaces_hint='inference_b11_hint',
                sent_no=sent_no, sent_total=sent_total)


# ---- P3 跨 cid 载体竞争守卫（批 12 自身注册；审计候选池实测 0 例）----
_CLAIMS = {}


def evaluate(record: dict, frag: str, table: str, group: str | None = None,
             layer: str | None = None, record_id=None, text: str | None = None,
             data=None, cid=None):
    """对一行做批 12 1095 扩域审核。

    返回 None（批 11 照常接管）或 promote dict。仅当批 11 全部门通过且主张含
    扩域解锁槽 p2/p5/p6 时晋级；主张⊆{p1,p3}（批 11 tier A）与任何门失败均返回
    None——本批不产生 hint（批 11 原有 hint 口径零变化），不静默丢弃（失败行仍由
    批 11 留原 hint）。
    """
    if data is None or cid is None or table not in TABLES or not isinstance(record, dict):
        return None
    j = frag
    if record.get('ability') == 1095:
        return None  # 相邻集（批 11 同门）
    sub_ids = [s for s in (record.get('sub') or []) if isinstance(s, int)]
    subs1095 = []
    for sid in sub_ids:
        w = data.skill(sid)
        if w is not None and (w.get('record') or {}).get('ability') == 1095:
            subs1095.append((sid, w['layer'], w['record']))
    if len(subs1095) != 1:
        return None  # 0 个＝非本批；≥2 个＝multi-1095-sub，批 11 hint 接管
    sid, sub_layer, subrec = subs1095[0]
    claimed = list(dict.fromkeys(B11.ATTR_RE.findall(j)))
    if not claimed:
        return None  # no-claim-fragment：批 11 口径返回 None 不占 hint
    if B11.ENEMY_RE.search(j):
        return None  # enemy-debuff-fragment：批 11 hint 接管
    if not B11.BASE_RE.match(j):
        return None  # conditional/mixed/non-base：批 11 hint 接管
    if '味方' in j and '自身' not in j:
        return None  # object-ally：批 11 hint 接管
    if sub_layer != 'CACHE' or sid not in B11._domain1095(data):
        return None  # carrier-out-of-domain（APK 52/35）：批 11 口径不变
    ok, _mism = B11._shape_check(claimed, subrec)
    if not ok:
        return None  # shape-mismatch：批 11 hint 接管
    dir_bad = []
    for attr in claimed:
        raw = subrec.get(B11.ATTR_SLOT[attr])
        good = {'攻撃力': lambda v: v > 1, '防御力': lambda v: v < 1,
                '移動速度': lambda v: v > 1, 'クリティカル発生率': lambda v: v > 0,
                'クリティカル威力': lambda v: v > 1.5}[attr](raw)
        if not good:
            dir_bad.append(B11._direction_note(attr, raw))
    if dir_bad:
        return None  # direction-mismatch：批 11 hint 接管
    # G1′ 句唯一（批 11 同法：NFKC 归一后恰 1 次）
    jk = lambda t: B6.unicodedata.normalize('NFKC', t).strip()
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    if jk(wb).count(jk(frag)) != 1:
        return None  # 归属歧义：批 11 hint 接管
    claimed_slots = {B11.ATTR_SLOT[a] for a in claimed}
    # 批 11 tier A（主张⊆{p1,p3}）零触碰：返回 None，仍由 B11 晋级（键 inference_b11）。
    if claimed_slots <= B11.DOMAIN_SLOTS:
        return None
    # P3 跨 cid 载体竞争守卫（批 11 晋级注册表＋批 12 本批注册表，防御性保留）
    others = (B11._CLAIMS.get(sid, set()) | _CLAIMS.get(sid, set())) - {cid}
    if others:
        return None  # 竞争（审计实测 0 例）：批 11 无 hint、此处防御性放行为 None
                   # （该情形审计结构性为 0；若出现，批 11 evaluate 不覆盖此分支，
                   # 重建前门脚本会显式失败，不静默）
    _CLAIMS.setdefault(sid, set()).add(cid)
    other_sub_abilities = [((data.skill(s) or {}).get('record') or {}).get('ability')
                           for s in sub_ids if s != sid]
    return _promote12(frag, table, layer, record_id, cid, claimed, '（省略主语）',
                      sid, subrec, record.get('ability'), other_sub_abilities,
                      _sent_no(text, frag), _sent_total(text))


def _sent_no(text, frag):
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    _sents = [s for s in re.findall(r'[^。]*。', wb)]
    return next((i + 1 for i, s in enumerate(_sents) if frag.strip() in s), None)


def _sent_total(text):
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    return len(re.findall(r'[^。]*。', wb))
