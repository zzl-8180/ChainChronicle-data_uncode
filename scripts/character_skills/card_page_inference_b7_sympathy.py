"""模板作用域推断层——批 7：共鳴アビリティ家族（sympathy 3000/3005/3006）→ skilllist 3000 载体。

设计与范围依据：``output/character_skills/inference_inventory/b7_sympathy_scope.md``
（批 7 前置审计；逐行明细 work/character_skills_b7_sympathy/b7_rows_classified.json：
sympathy 组 2,232 行/719 cid＝分母，A 257/C 1,975；buff 语义行 794 为唯一候选池；
预分类晋级候选 96 行〔Y.G. 25〕／~324 值行〔Y.G. ~100〕——实施批逐行审核还可能再收缩）。

关键结构（scope §3，本轮审计新核实）：``sympathy_skill_info[_id=cid].ability0`` → 主记录 M
（ability 3000/3005/3006/旧型），M.text 承载该 cid 共鳴能力全部正文（多段拼接）；**数值不在
M 上**（部分形态除外），分散在相邻「sub1」记录（skillid=M+1，ability=3000）与/或 M 自身；
链接＝skillid+1 相邻＋形状匹配为实质判据（30236 确认先例：其 A 行确认回答的 source 即
43023611——本映射机制已有逐描述确认级先例，非本批新发明）。载体競争/同属性重复段实测 0 例
（守卫保留）。

精确范围（scope §5.1，门控 G1–G8 全部通过才晋级；任一不过→留 hint 并登记原因）：

* 行集＝sympathy 组 skilllist 行（调用点 ``group=='sympathy' and table=='skilllist' and
  not answers`` 守卫；家族行实测全部在 sympathy 组，其余组含「共鳴アビリティ」的行 0——
  含 leader sympathy_text 亦无）；
* **G2 buff 形状**：句含 ``≪共鳴必殺≫を発動するたび`` 且 ``が一定時間上がる/上がり``
  （方向实测全「上がる」系；下がる/上げる不属本族）；不匹配→不属本批（返回 None，维持原样）；
* **G1 句归属**：行 japanese 是主记录 text 的唯一子串（同文多次→hint）；
* **G3 主记录类型**：主记录 ability ∈ {3000,3005,3006}；3001/3002/3004 旧型→hint；
* **G4 属性全有规则**：句中属性 ⊆ {攻撃力, クリティカル威力, 一定時間}；出现防御力/
  移動速度/HPが上限を超えて回復/回復系/クリティカル発生率/クリティカル攻撃/状態異常/
  呪い/封印/暗闇/スロウ/毒/遅効 任一 → 整行 hint（「句中属性无规则→整行留 hint」纪律；
  3000 的 p3/p4/p5/p7 槽语义未定——p4 实测为负值与「上がる」句向矛盾——不得按相关性
  猜想消费）；
* **G5 唯一载体**：候选载体＝{M（若 ability=3000），M+1（若相邻记录 ability=3000）}；
  载体活性 ruled 槽 == 行主张属性（攻撃力⇔p1∧p2 双活性；クリ威力⇔p8 活性；不得有行未
  主张的 ruled 活性槽——防跨段误配；p1/p2 活性不一致为形状未定义→hint）；恰 1 个匹配→
  通过；0 个→hint(no-matching-carrier)；≥2 个→hint(carrier-competition)；
* **G6 競争句检测**（B6-RV-01 同法）：主记录正文本句之外的「。」句中，与本句同属性集合的
  ally-buff 短语（⟨ATTR-run⟩が一定時間上がる/上がり）→归属不能唯一化解→hint（实测 0 例）；
* **G7 样本域**：载体层 == CACHE（规则 conditions 登记域＝当前 v3 CACHE ability3000 的
  382 条记录）；APK 载体→hint（域外；APK 层 3000 记录 446 条值形同构但含 CACHE 域外值，
  扩域需独立原生核实，不静默扩域）；
* **G8 槽值健全/方向**：攻撃力/クリ威力槽原值 >0（负值→方向冲突 hint）；时长值行仅在载体
  p6>0 时出（规则 limits：「缺时间不推定永久」；缺字段不补 0）。

句式→类型→param 映射（唯一映射表，scope §5.2；值行 rule_key 只允许 ``skilllist|3000|*``）：

==============  =============================  ==============================================
句中成分         规则键                          值行数量类型（rules.py 换算器）
==============  =============================  ==============================================
攻撃力           /param1＋/param2（两条值行）    普通攻击/技能攻击的加算贡献（+5/+10 个百分点；
                                                1+Σ(_attack+_attackNormal/_attackSkill) 夹紧，
                                                不乘 Chain）
クリティカル威力 /param8                         暴伤系数增量（直接写 _criticalDmgRate，不减 1.5、
                                                不乘 Chain；非相对暴伤再乘）
一定時間         /param6                         持续时间（游戏秒，45/60）
防御力/移動速度/ —（3000 无规则槽）              整行 hint（G4）
回復系/クリ発生率 等
==============  =============================  ==============================================

硬边界（scope §1.2/§5/§8，逐行强制）：

* **3005/3006 自身参数一律不消费、不立规则**：3005 param1∈{1,2}/param2∈{1..4} 为 Chain
  发动侧配置、3006 param1/param2/param3/param5/param6 为 mana 侧配置（语义未定，0 规则——
  派发证据 ``output/ordinary_effects/ability3000/dispatch.txt:10``/``qualification.txt:26``
  均 ``cmp w0,#0xbb8``（=3000）即返回，处理器入口未被既有原生证据覆盖，occurrence 补证
  不可行）；本行值行只经相邻/自身 3000 载体套用 3000 规则，**不得写「3005 规则」**。
* **只升「推断」，绝不升「确认」**：值行 numeric_evidence/association_evidence 一律「推断」；
  行级标注「推断（模板批 7 共鳴）」、evidence_scope=TEMPLATE_BATCH7_SYMPATHY（行级 metadata
  键 ``inference_b7``，与 inference_pilot/b3/b4/b5/b6 并列）；不进整行确认统计；「唯一 3000
  载体＋形状匹配」是数据侧结构对应，永不据此升「确认」。
* **对象披露（双源，逐值行 note 固定口径）**：句面依据「戦場にいる⟨…⟩の」逐字在句（实测
  721 味方/73 自身）；记录侧＝``output/ordinary_effects/ability3000/README.md``——param0
  控制候选支持接受者（376 条源值 1→遍历候选；缺→持有者自身），iParam0/param9 筛选发动者
  （职业位图/所属），发动者须 IsAlive 且 _type=0。**iParam0/param9 筛选的是发动者、param0
  才是接受者侧，不得混写**（README 原文警示）。
* **条件逐字披露（双源）**：句面触发句逐字入 note（≪共鳴必殺≫を発動するたび 及
  ボスWAVE時/通常WAVE時/地形が…の時/自身を含む⟨X⟩所属が/⟨職業⟩組合/⟨斬突魔聖⟩武器 等实测
  变体）；记录侧＝bhSkill.OnStartSkill 于 _bSympathySkill@7c/_bKSympathySkill@7d/
  _bSSympathySkill@7e 开启时 checkSympathyySkillAbility（8 种标记组合）——照
  ability3000/README.md 口径披露，不简化为「共鳴時」。
* **非首段（批 6 裁决沿用）**：非首段行仅在归属已结构性化解（G1 唯一子串＋G5 唯一载体＋
  形状匹配）时晋级；逐行披露「句→载体为数据侧结构对应，引擎侧装载路径无原生核实」，
  **不写「段位↔槽位位置序对应」**（b6 §4.1/B5-R03 同性质）；同文多次/競争未化解一律 hint。
* **自识正文口径（批 7 新行；批 6 遗留 49 行句序歧义不继承）**：多段披露固定写「sympathy
  主记录正文句序：本句位于第 N 段（\\n 段切）／共 K 段；本行正文＝sympathy_skill_info.
  ability0 指向记录的 text；sub1 载体与同页其他记录的正文句序另计」。
* **证据按字段**（INFR-01）：值行 evidence 取 rules.json ``skilllist|3000|/paramN`` 的
  evidence——p1/p2/p6→origin（output/card_comparison_cid30236/）下 ``timed_support/*``
  3 件＋``../ordinary_effects/ability3000/*`` 3 件；p8→``critical/*`` 3 件＋
  ability3000 3 件；存在性检查，缺失显式失败（不产出死指针）。
* **样本域披露按登记口径**（INFR-02）：skilllist|3000 四条规则 occurrences 已登记
  （303/303/348/144，与 CACHE 382 条记录非零计数交叉验证一致）→逐行按登记口径披露
  （与批 6 bossskill|13 occurrences=None 的外推披露不同，本批口径更强）。
* **不跨记录合并、逐行不折叠**：同 cid 的 buff 段行与 sub1 无文本行不合并；3005/3006 主
  记录自身参数不进入值行；载体句外槽（param0/param3/param4/param5/param7/iParam0/param9
  等）只登记原值不分配给本句；30236 等 257 条既有 A 行不动（``not answers`` 守卫）；
  同页多共鳴 cid 不存在（sympathy_skill_info 每 cid 恰 1 条 ability0，实测 719/719）。
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path

import rules as R

B7_TAG = '推断（模板批 7 共鳴）'
B7_SCOPE = 'TEMPLATE_BATCH7_SYMPATHY'
B7_FAMILY = ('≪共鳴必殺≫を発動するたび、戦場にいる⟨TGT⟩の⟨ATTR⟩が一定時間上がる。'
             '（sympathy 组→skilllist 主记录/相邻 sub1 的 ability3000 载体）')

RULE_PARAMS = {'param1': '普通攻击的加算贡献（TimePowerUpData._attackNormal）',
               'param2': '技能攻击的加算贡献（_attackSkill）',
               'param6': '共鸣临时支持的正持续时间输入（setSupport3）',
               'param8': '暴伤系数加算贡献（_criticalDmgRate，不减 1.5、不乘 Chain）'}
# 句中属性→载体槽映射（scope §5.2 唯一映射表；攻撃力＝p1+p2 两条值行）。
ATTR_PARAMS = {'攻撃力': ('param1', 'param2'), 'クリティカル威力': ('param8',)}
DUR_PARAM = 'param6'
DUR_ATTR = '一定時間'
# G4：句中无规则属性词（审计 scan_b7_rows.py UNRULED_WORDS 逐字沿用；「回復」覆盖回復系）。
UNRULED_WORDS = ['防御力', '移動速度', 'HPが上限を超えて回復', '回復', '状態異常',
                 'クリティカル発生率', 'クリティカル攻撃', '呪い/封印', '暗闇', 'スロウ', '遅効', '毒']
_OBJECT = re.compile(r'戦場にいる(<[^<>]*>|自身)の')
_TRIGGER = re.compile(r'.{0,60}?≪共鳴必殺≫を発動するたび')
# G6 競争句（B6-RV-01 同法）：本句之外的 ally-buff 短语，属性集合与本句相同。
_COMPET = re.compile(r'の((?:攻撃力|クリティカル威力)(?:と(?:攻撃力|クリティカル威力))*)'
                     r'が一定時間(上がる|上がり)')

# INFR-01：rules.json skilllist|3000|/paramN 的 evidence 相对路径解析——
# '../ordinary_effects/…'→output/…；其余相对规则 origin＝output/card_comparison_cid30236/。
_CARD_COMPARISON_ROOT = 'output/card_comparison_cid30236/'
_EVIDENCE_EXPECTED = {'param1': (_CARD_COMPARISON_ROOT + 'timed_support/',
                                 'output/ordinary_effects/ability3000/'),
                      'param2': (_CARD_COMPARISON_ROOT + 'timed_support/',
                                 'output/ordinary_effects/ability3000/'),
                      'param6': (_CARD_COMPARISON_ROOT + 'timed_support/',
                                 'output/ordinary_effects/ability3000/'),
                      'param8': (_CARD_COMPARISON_ROOT + 'critical/',
                                 'output/ordinary_effects/ability3000/')}
_EVIDENCE_CACHE = {}


def _field_evidence(param):
    """按字段解析 rules.json skilllist|3000|/paramN 的 evidence 并做存在性检查（INFR-01）。"""
    if param in _EVIDENCE_CACHE:
        return _EVIDENCE_CACHE[param]
    rule = R.rule_for('skilllist', 3000, '/' + param)
    files = []
    for entry in (rule or {}).get('evidence') or []:
        items = entry if isinstance(entry, (list, tuple)) else [entry]
        for e in items:
            e = str(e)
            files.append('output/' + e[3:] if e.startswith('../') else _CARD_COMPARISON_ROOT + e)
    dirs = _EVIDENCE_EXPECTED[param]
    if not files or any(not p.startswith(dirs) for p in files):
        raise ValueError(f'批 7 证据解析异常（INFR-01）：skilllist|3000|/{param} 的 rules.json '
                         f'evidence 未解析为 {dirs} 下的文件，实际 {files!r}')
    missing = [p for p in files if not Path(p).is_file()]
    if missing:
        raise FileNotFoundError(f'批 7 证据文件缺失（INFR-01）：{missing}')
    _EVIDENCE_CACHE[param] = (dirs, files)
    return _EVIDENCE_CACHE[param]


def _num(raw):
    return (isinstance(raw, (int, float)) and not isinstance(raw, bool) and math.isfinite(raw))


def _active(raw):
    return raw is not None and raw != 0


def _seg_no(body, frag):
    """主记录正文的 \\n 段定位（自识正文口径）：本句位于第 N 段／共 K 段（空段不计）。"""
    segs = [s for s in body.split('\n') if s.strip()]
    needle = frag.strip()
    no = next((i + 1 for i, s in enumerate(segs) if needle in s), None)
    return no, len(segs)


def _competing_buffs(body, want, frag):
    """主记录正文本句之外、同属性集合的 ally-buff 句原文（G6；B6-RV-01 同法按「。」切句）。"""
    out = []
    for s in re.findall(r'[^。]*。', body or ''):
        if frag.strip() in s:
            continue
        ns = unicodedata.normalize('NFKC', s)
        for m in _COMPET.finditer(ns):
            if set(m.group(1).split('と')) == set(want):
                out.append(s)
                break
    return list(dict.fromkeys(out))


def _sample_domain_note(rule, param):
    """样本域披露（INFR-02）：skilllist|3000 规则 occurrences 已登记（303/303/348/144）→
    按登记口径披露（本批口径比批 6 的外推披露强；仍不属逐记录确认）。
    B6-RV-02 同法：origin 按 profiles/rules.json 登记值输出（rules.py 合并源条目无 origin 键，
    直接读会打印「origin None/未登记」——不属实）。"""
    occ = rule.get('occurrences')
    origin = _registered_rule(param).get('origin') or '未登记'
    return (f'该规则登记已核出现 {occ} 次（origin {origin}；样本域＝当前 v3 CACHE 普通 '
            'ability3000 的 382 条记录，conditions 原文「不推广其他共鸣类型」）；本行来源载体'
            '记录未逐条核对，按规则适用条件披露，不属逐记录确认')


_REGISTERED_RULES = None


def _registered_rule(param):
    """profiles/rules.json 登记的规则条目（origin 权威来源；B6-RV-02 同法。profiles/ 为本批
    只读共享依赖，已在 card_page_dependencies.data_paths 声明清单内）。"""
    global _REGISTERED_RULES
    if _REGISTERED_RULES is None:
        p = Path('output/character_skills/profiles/rules.json')
        _REGISTERED_RULES = json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}
    return _REGISTERED_RULES.get(f'skilllist|3000|/{param}') or {}


_TRIGGER_NATIVE = ('触发条件记录侧：bhSkill.OnStartSkill 于 _bSympathySkill@7c/_bKSympathySkill@7d/'
                   '_bSSympathySkill@7e 任一开启时调用 checkSympathyySkillAbility（8 种标记组合'
                   '检查通过）——output/ordinary_effects/ability3000/README.md 口径，不简化为「共鳴時」')

_OBJECT_NATIVE = ('记录侧＝output/ordinary_effects/ability3000/README.md——param0 控制候选支持'
                  '接受者（376 条源值 1→遍历候选；缺→持有者自身），iParam0/param9 筛选发动者'
                  '（职业位图/所属），发动者须 IsAlive 且 _type=0；iParam0/param9 为发动者侧、'
                  'param0 为接受者侧，不得混写')


def _object_note(subject_phrase):
    """对象披露（双源，逐值行 note 固定口径；scope §5.3）。"""
    return (f'对象披露（双源）：句面依据「{subject_phrase}」逐字在句；' + _OBJECT_NATIVE)


def _carrier_slots_note(carrier, claimed_params, carrier_key):
    """载体槽位登记：本句消费槽＋句外槽原值（不分配给本句，仅登记；p3/p4/p5/p7 语义未定）。"""
    consumed, idle, unknown = [], [], []
    for key in sorted(carrier):
        if not re.match(r'^(param|iParam|iparam|flag)\d', key):
            continue
        raw = carrier.get(key)
        if key in claimed_params:
            consumed.append(f'/{key}={raw!r}（本句消费）')
            continue
        label = ('（语义未定，不按相关性猜想消费）'
                 if key in ('param3', 'param4', 'param5', 'param7') else '')
        entry = f'/{key}={raw!r}' + label
        (idle if key in ('param0', 'iParam0', 'param9') else unknown).append(entry)
    parts = [f'载体 {carrier_key} 槽位登记：本句消费 ' + '、'.join(consumed)]
    if idle:
        parts.append('param0（接受者开关）/iParam0/param9（发动者职业位图/所属筛选）原值：'
                     + '、'.join(idle) + '——iParam0/param9 为发动者侧、param0 为接受者侧，不得混写')
    if unknown:
        parts.append('句外槽未分配（不归属本句，仅登记原值；p3/p4/p5/p7 无已确认规则）：'
                     + '、'.join(dict.fromkeys(unknown)))
    return '；'.join(parts)


def _promote(frag, cid, layer, claims, attrs, subject_phrase,
             trigger_text, main_sid, main_ability, carrier, carrier_role, seg_no, seg_count):
    """晋级行：值行全部来自唯一 ability3000 载体，逐行注明来源记录链（scope §5）。"""
    carrier_sid = carrier['skillid']
    carrier_layer = carrier['_layer']
    carrier_key = f'skilllist|{carrier_sid}|{carrier_layer}'
    main_key = f'skilllist|{main_sid}|{layer or carrier_layer}'
    role_desc = ('主记录自身（ability3000）' if carrier_role == 'main'
                 else '相邻 sub1 载体（skillid=M+1，ability3000；链接＝skillid+1 相邻＋形状匹配，'
                      '30236 确认先例 43023610→43023611 同机制）')
    chain_desc = f'sympathy_skill_info[_id={cid}].ability0→{main_key}→{carrier_key}'
    numeric_source = f'模板推断（批 7 共鳴：{chain_desc}）'
    answers = []
    claimed_params = []
    for attr in attrs:
        for param in ATTR_PARAMS[attr]:
            claimed_params.append(param)
            raw = carrier.get(param)
            if not _num(raw) or raw <= 0:
                return dict(kind='hint', reasons=[f'方向冲突（载体 /{param} 原值 {raw!r}<=0，'
                                                  '句称上升；保守留 hint）'],
                            subject=subject_phrase, attrs=attrs, claims=claims,
                            carrier_key=carrier_key, seg_no=seg_no, seg_count=seg_count)
            rule = R.rule_for('skilllist', 3000, '/' + param)
            converted = R.answer_for('skilllist', 3000, '/' + param, raw, carrier)
            evidence_dirs, evidence_files = _field_evidence(param)
            answers.append(dict(
                value=converted['value_text'],
                quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
                raw_value=raw, field_path='/' + param,
                numeric_source=numeric_source, numeric_evidence='推断',
                association_evidence='推断', evidence_scope=B7_SCOPE,
                rule_key=f'skilllist|3000|/{param}',
                rule_body_status=rule.get('status'), rule_status=rule.get('status'),
                conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
                conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
                evidence=list(evidence_files),
                source=dict(table='skilllist', record_id=carrier_sid, layer=carrier_layer,
                            record_key=carrier_key),
                note=(f'模板批 7 共鳴值行（来源载体＝{carrier_key}，{role_desc}）；'
                      f'句中「{attr}」→/{param} 映射（攻撃力＝param1+param2 两条值行）'
                      if attr == '攻撃力' else
                      f'模板批 7 共鳴值行（来源载体＝{carrier_key}，{role_desc}）；'
                      f'句中「{attr}」→/{param} 1:1 映射') +
                      f'；规则键 skilllist|3000|/{param}；原值 {raw}；'
                      f'方向审核：方向一致（原值 {raw}>0，{RULE_PARAMS[param]}，与句「上がる」'
                      f'方向一致）；证据目录 {evidence_dirs[0]} 及 output/ordinary_effects/ability3000/；'
                      f'{_object_note(subject_phrase)}；条件逐字：句面「'
                      f'{trigger_text}」；{_TRIGGER_NATIVE}；'
                      f'样本域：{_sample_domain_note(rule, param)}',
                quantitative=True))
    # 一定時間 → /param6（仅在载体 p6>0 时出值行；规则 limits「缺时间不推定永久；缺字段不补 0」）
    p6_raw = carrier.get(DUR_PARAM)
    dur_note = None
    if _num(p6_raw) and p6_raw > 0:
        claimed_params.append(DUR_PARAM)
        rule = R.rule_for('skilllist', 3000, '/' + DUR_PARAM)
        converted = R.answer_for('skilllist', 3000, '/' + DUR_PARAM, p6_raw, carrier)
        evidence_dirs, evidence_files = _field_evidence(DUR_PARAM)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=p6_raw, field_path='/' + DUR_PARAM,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B7_SCOPE,
            rule_key=f'skilllist|3000|/{DUR_PARAM}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_sid, layer=carrier_layer,
                        record_key=carrier_key),
            note=(f'模板批 7 共鳴值行（来源载体＝{carrier_key}，{role_desc}）；'
                  f'句中「{DUR_ATTR}」→/{DUR_PARAM} 1:1 映射；规则键 skilllist|3000|/{DUR_PARAM}；'
                  f'原值 {p6_raw}；方向审核：方向一致（正持续时间输入 {p6_raw}>0）；持续时间单位为游戏秒'
                  '（fixedDeltaTime 累计；非现实墙钟秒）；证据目录 ' + evidence_dirs[0] +
                  ' 及 output/ordinary_effects/ability3000/；'
                  f'{_object_note(subject_phrase)}；条件逐字：句面'
                  f'「{trigger_text}」；{_TRIGGER_NATIVE}；'
                  f'样本域：{_sample_domain_note(rule, DUR_PARAM)}'),
            quantitative=True))
    else:
        dur_note = ('句中「一定時間」的载体 /param6 槽不活性或非正值（原值 '
                    f'{p6_raw!r}），不产出持续时间值行（规则 limits：缺时间不推定永久；缺字段不补 0）')

    # --- 晋级行注记（不改变「推断」档位） --------------------------------------------------
    extra = []
    extra.append(_object_note(subject_phrase) + '。' + _TRIGGER_NATIVE)
    extra.append('跨记录归属依据（scope §5）：句→载体为数据侧结构对应——唯一 ability3000 载体'
                 '（候选＝主记录自身〔若 3000〕＋相邻 skillid+1〔若 3000〕，活性 ruled 槽↔句属性'
                 '形状匹配，主记录正文无同属性集合竞争 buff 句）；引擎侧装载路径无原生核实'
                 '（3005/3006 处理器入口未原生核实——output/ordinary_effects/ability3000/'
                 'dispatch.txt:10 派发在 3000(0xbb8) 即返回）；不写「段位↔槽位位置序对应」'
                 '（b6 §4.1/B5-R03 同性质）')
    extra.append(f'多段披露（自识正文口径）：sympathy 主记录正文句序——本行正文＝'
                 f'sympathy_skill_info[_id={cid}].ability0 指向记录的 text，共 {seg_count} 段'
                 f'（\\n 切），本句位于第 {seg_no} 段；sub1 载体与段序无位置对应关系（实测拆分'
                 '架构），sub1 载体与同页其他记录的正文句序另计')
    if dur_note:
        extra.append(dur_note)
    if main_ability != 3000:
        extra.append(f'主记录 ability={main_ability} 自身参数不消费（skilllist|3005/3006 无已确认'
                     '规则：3005 param1∈{1,2}/param2∈{1..4} 为 Chain 发动侧配置、3006 param 为 '
                     'mana 侧配置，语义未定；派发证据只到 3000；本行值行 rule_key 均为 '
                     'skilllist|3000|*，不得写「3005/3006 规则」）')
    extra.append('不跨记录合并（scope §8.6）：本行值行仅含来源载体 ' + carrier_key +
                 ' 的 skilllist|3000|/paramN 换算；同 cid 的其他 buff 段行与 sub1 无文本行不合并，'
                 '3005/3006 主记录自身参数不进入本行值行')
    extra.append(_carrier_slots_note(carrier, set(claimed_params), carrier_key))
    claimed_sorted = sorted(set(claimed_params))
    summary = (B7_TAG + '：buff 值行来源＝' + chain_desc + '（载体＝' + role_desc + '）；'
               '值行全部「推断」，不升「确认」，不进入整行确认。句→载体归属为数据侧结构对应：'
               '唯一 ability3000 载体＋活性 ruled 槽↔句属性形状匹配＋主记录正文无同属性集合'
               '竞争 buff 句；引擎侧装载路径无原生核实。' +
               f'sympathy 主记录正文共 {seg_count} 段（\\n 切），本句位于第 {seg_no} 段；'
               'sub1 载体与段序无位置对应关系。适用范围披露：'
               + '；'.join(_sample_domain_note(R.rule_for('skilllist', 3000, '/' + p), p)
                           for p in claimed_sorted) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject_phrase, attrs=list(attrs), claims=dict(claims),
                table='skilllist', main_skillid=main_sid, main_ability=main_ability,
                main_layer=layer, carrier_record_id=carrier_sid, carrier_layer=carrier_layer,
                carrier_role=carrier_role, carrier_name=carrier.get('name'),
                seg_no=seg_no, seg_count=seg_count)


def evaluate(record: dict, frag: str, group: str | None = None, layer: str | None = None,
             record_id=None, text: str | None = None, data=None, cid=None):
    """对一行做批 7 共鳴审核，返回 None（不属本批范围）或审核结果 dict。

    group：页面组（本批仅 sympathy 组）；layer/record_id：行记录（共鳴主记录 M）来源层与 id；
    text：行记录正文字段全文（clean 后）；data/cid：页级 Inputs 与 cid（相邻 sub1 载体解析用）。

    结果 dict：kind='promote'（answers/summary_reason/extra_reasons 等）或 'hint'（reasons）。
    """
    if data is None or cid is None or group != 'sympathy' or not isinstance(record, dict):
        return None
    # G2 buff 形状（scope §5.1）：≪共鳴必殺≫を発動するたび＋が一定時間上がる/上がり；
    # 不匹配→不属本批（非数值/装置/尾句行维持原样，scope §6 E1）。
    if '≪共鳴必殺≫を発動するたび' not in frag:
        return None
    if not re.search(r'が一定時間(上がる|上がり)', frag):
        return None
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    # G1 句归属：行 japanese 是主记录 text 的唯一子串。
    needle = frag.strip()
    same_count = wb.count(needle) if wb else 0
    seg_no, seg_count = _seg_no(wb, frag) if wb else (None, None)
    if same_count != 1:
        return dict(kind='hint', reasons=[f'G1：行句未在主记录正文中唯一出现（{same_count} 次）；'
                                          '同文多次/未定位一律留 hint'],
                    subject=None, attrs=[], table='skilllist', seg_no=seg_no, seg_count=seg_count)
    # G3 主记录类型（3001/3002/3004 旧型无规则）。
    main_ability = record.get('ability')
    main_sid = record.get('skillid')
    if main_ability not in (3000, 3005, 3006):
        return dict(kind='hint', reasons=[f'G3：主记录 ability={main_ability!r}（旧型 3001/3002/'
                                          '3004）无已确认规则，语义未核'],
                    subject=None, attrs=[], table='skilllist', seg_no=seg_no, seg_count=seg_count)
    # 主记录解析（与 links 同口径：CACHE 优先）。
    m = data.skill(main_sid) if main_sid is not None else None
    if m is None:
        return dict(kind='hint', reasons=[f'G5：主记录 skilllist|{main_sid} 未定位'],
                    subject=None, attrs=[], table='skilllist', seg_no=seg_no, seg_count=seg_count)
    mrec = dict(m['record'])
    mrec['_layer'] = m['layer']
    # 句属性主张与 G4 无规则属性门。
    claims = {'攻撃力': '攻撃力' in frag, 'クリティカル威力': 'クリティカル威力' in frag,
              DUR_ATTR: True}
    unruled = [w for w in UNRULED_WORDS if w in frag]
    if unruled:
        return dict(kind='hint', reasons=['G4：句含无已确认规则的属性（' + '、'.join(unruled) +
                                          '）：skilllist|3000 仅有 param1/param2/param6/param8 '
                                          '四条规则（p3/p4/p5/p7 语义未定，p4 实测为负值与「上がる」'
                                          '句向矛盾，不得按相关性猜想消费）；整行留 hint，不拆半晋级'],
                    subject=None, attrs=sorted(claims), table='skilllist', seg_no=seg_no,
                    seg_count=seg_count)
    if not (claims['攻撃力'] or claims['クリティカル威力']):
        return dict(kind='hint', reasons=['G4：本句无有规则的可映射属性（仅一定時間），无值行可产出'],
                    subject=None, attrs=[], table='skilllist', seg_no=seg_no, seg_count=seg_count)
    # 对象短语（scope §5.3：句面依据逐字在句；实测 794/794 全有）。
    obj = _OBJECT.search(frag)
    if obj is None:
        return dict(kind='hint', reasons=['G4：句中无逐字对象短语「戦場にいる⟨…⟩の」，对象无法从句面核证'],
                    subject=None, attrs=sorted(claims), table='skilllist', seg_no=seg_no,
                    seg_count=seg_count)
    subject_phrase = obj.group(0)
    mtrig = _TRIGGER.search(frag)
    trigger_text = mtrig.group(0) if mtrig else frag[:40] + '…'
    # G5 唯一载体：候选＝{M（若 ability=3000），M+1（若相邻记录 ability=3000）}；
    # 活性 ruled 槽 == 行主张属性（攻撃力⇔p1∧p2；クリ威力⇔p8；不得有行未主张的 ruled 活性槽）。
    cands = []
    if mrec.get('ability') == 3000:
        cands.append(('main', mrec))
    sub = data.skill(main_sid + 1) if main_sid is not None else None
    if sub is not None and (sub['record'] or {}).get('ability') == 3000:
        srec = dict(sub['record'])
        srec['_layer'] = sub['layer']
        cands.append(('sub1', srec))
    ok_carriers = []
    for role, rec in cands:
        p1a, p2a = _active(rec.get('param1')), _active(rec.get('param2'))
        p8a = _active(rec.get('param8'))
        need_atk = claims['攻撃力'] and p1a and p2a
        need_crt = claims['クリティカル威力'] and p8a
        extra_act = (p8a and not claims['クリティカル威力']) or ((p1a and p2a) and not claims['攻撃力'])
        if need_atk == claims['攻撃力'] and need_crt == claims['クリティカル威力'] \
                and not extra_act and p1a == p2a:
            ok_carriers.append((role, rec))
    act_desc = '；'.join(
        f"skilllist|{rec['skillid']}|{rec['_layer']} 活性 p1={rec.get('param1')!r} "
        f"p2={rec.get('param2')!r} p6={rec.get('param6')!r} p8={rec.get('param8')!r}"
        for _, rec in cands) or '无 ability3000 候选载体'
    if len(ok_carriers) == 0:
        return dict(kind='hint', reasons=['G5：主记录及相邻 skillid+1 无形状匹配的 ability3000 '
                                          '载体（活性 ruled 槽↔句主张属性不匹配；候选：' + act_desc +
                                          '）；部分同类句与载体未定槽 p7 的相关性待原生核实后复评'],
                    subject=subject_phrase, attrs=sorted(claims), table='skilllist',
                    seg_no=seg_no, seg_count=seg_count)
    if len(ok_carriers) > 1:
        return dict(kind='hint', reasons=[f'G5：{len(ok_carriers)} 个 ability3000 载体形状同时匹配'
                                          f'本句（{act_desc}），归属不能唯一化解（carrier-competition）'],
                    subject=subject_phrase, attrs=sorted(claims), table='skilllist',
                    seg_no=seg_no, seg_count=seg_count)
    role, carrier = ok_carriers[0]
    # G6 競争句检测（B6-RV-01 同法）：主记录正文本句之外同属性集合的 ally-buff 短语。
    competitors = _competing_buffs(wb, [a for a in ('攻撃力', 'クリティカル威力') if claims[a]], frag)
    if competitors:
        return dict(kind='hint', reasons=['G6：主记录正文存在与本句同属性集合（'
                                          + '・'.join(a for a in ('攻撃力', 'クリティカル威力')
                                                  if claims[a]) + '）的竞争 buff 句（'
                                          + '；'.join(competitors) + '）：唯一载体形状同时匹配本句'
                                          '与竞争句，归属不能唯一化解（按 INFR-05 不猜，留 hint）'],
                    subject=subject_phrase, attrs=sorted(claims), table='skilllist',
                    seg_no=seg_no, seg_count=seg_count)
    # G7 样本域：载体层 == CACHE（规则 conditions 登记域＝382 条 CACHE 记录）。
    if carrier['_layer'] != 'CACHE':
        return dict(kind='hint', reasons=['G7：载体记录 skilllist|' + str(carrier['skillid']) +
                                          '|APK 在规则样本域（conditions：仅当前 v3 CACHE 普通 '
                                          'ability3000 的 382 条记录）之外；APK 层 3000 记录 446 条'
                                          '值形同构但含 CACHE 域外值，扩域需独立原生核实，不静默扩域'],
                    subject=subject_phrase, attrs=sorted(claims), table='skilllist',
                    seg_no=seg_no, seg_count=seg_count)
    return _promote(frag, cid, layer, claims,
                    [a for a in ('攻撃力', 'クリティカル威力') if claims[a]], subject_phrase,
                    trigger_text, main_sid, main_ability, carrier, role, seg_no, seg_count)
