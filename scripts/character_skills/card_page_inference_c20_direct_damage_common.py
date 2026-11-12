# -*- coding: utf-8 -*-
"""C20 直接伤害候选共用解析器。

本模块不自行接线。P1/P2 只提供冻结身份、显式 scope 与条件模型；所有 raw、记录 ID、
下标、JSON pointer 和片段 span 都在运行期从当前 CACHE/APK 原始记录重导。生产代码不读取
Web JS、展示层 audit 或调查 work 文件；这些材料仅在答案 evidence 中作为静态补证引用。

直接父与条件父都必须从同层 charainfo 的真实 pattern 引用集合解引用。当前父、旧候选父、
同记录多父与同值异记录分别登记；公式复用不把句面归属升级为确认。
"""
from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime
import hashlib
import json
import math
import re
import struct
import sys
import unicodedata
import weakref
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_SCRIPTS = _HERE.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from project_layout_paths import read_path, write_path

import effect_ledger as LEDGER
import rules as RULES
import card_page_inference_c14_p2_boss_damage_direct as C14

LEDGER_SCOPE = 'G1_B1_MIRROR_20261029'
EXACT = 'RESOLVED_EXACT_DECODED_RECORD'
CACHE_SNAPSHOT = 'output/cache_full_20261015_v3'
CACHE_DECODED = CACHE_SNAPSHOT + '/decoded'
PAGES_REL = 'output/character_skills/pages'
RULES_REL = 'output/character_skills/profiles/rules.json'
APK_CHARA_REL = 'output/base_master/_mdCharacter.json'
APK_BOSS_REL = 'output/base_master/_mdBossInfo.json'
DAMAGE_SLOT = dict(C14.DAMAGE_SLOT)
SINGLE_TYPES = tuple(C14.SINGLE_TYPES)
MULTI_TYPES = tuple(C14.MULTI_TYPES)
STALE_REASONS = set(C14._STALE_REASONS)
CONDITION_FIELDS = ('patternid', 'hpstart', 'hpend', 'priority', 'limit', 'bgf',
                    'mns', 'mne', 'chs', 'che', 'scost', 'flag', 'sinfo', 'sname')
MULTIHIT_RX = re.compile(r'(\d+)回ダメージ')
BIGMID_RX = re.compile(r'(?:大|中)ダメージ')
SMALL_RX = re.compile(r'小ダメージ')
INTERVAL_RX = re.compile(r'一定間隔でダメージ')
PATTERN_REF_RX = re.compile(r'^pattern(\d+)$')


@dataclasses.dataclass(frozen=True)
class BatchSpec:
    scope: str
    module_version: str
    binding_key: str
    marker_key: str
    module_file: str
    out_dir: str
    targets: tuple
    negative_cids: tuple = (30207, 278)
    protected_cids: tuple = (30102, 20234, 30236, 30239)


class ScopeError(RuntimeError):
    pass


def require_scope(spec, scope):
    if scope is None:
        raise ScopeError('缺少 scope：必须显式传入 %r' % spec.scope)
    if scope != spec.scope:
        raise ScopeError('scope 不符：收到 %r，只接受 %r' % (scope, spec.scope))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def record_sha256(record):
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def canon(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def num_text(value):
    return C14.num_text(value)


def f32(value):
    return struct.unpack('<f', struct.pack('<f', float(value)))[0]


def raw_state(record, field):
    return C14.raw_state(record.get(field), field in record)


def json_dump(value):
    return json.dumps(value, ensure_ascii=False, indent=1, allow_nan=False) + '\n'


def iter_rows(card_or_groups):
    groups = card_or_groups.get('groups') if isinstance(card_or_groups, dict) else card_or_groups
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                yield group, skill, row


def source_prefix(layer, kind):
    if layer == 'CACHE':
        return '/bossinfo/' + kind
    if layer == 'APK':
        return '/' + kind
    raise ValueError('未知来源层：%r' % layer)


def source_file(layer):
    if layer == 'CACHE':
        return CACHE_DECODED + '/bossinfo.data5.json.raw'
    if layer == 'APK':
        return APK_BOSS_REL
    raise ValueError(layer)


def source_key(layer):
    return ('CACHE/bossinfo.data5.json.raw' if layer == 'CACHE'
            else 'APK/_mdBossInfo.json')


def conditions_raw(record):
    return {key: record[key] for key in CONDITION_FIELDS if key in record}


def classify_clause(text):
    text = str(text or '')
    if 'ダメージ' not in text:
        return None, {'reason': 'NO_DAMAGE_WORD'}
    for mark in ('ダメージが上がる', 'ダメージが下がる', 'ダメージが増', 'ダメージが減'):
        if mark in text:
            return None, {'reason': 'DAMAGE_MODIFIER_NOT_INSTANCE', 'mark': mark}
    for mark in ('受ける', '受け', '味方'):
        if mark in text:
            return None, {'reason': 'DAMAGE_RECEIVER_NOT_ENEMY', 'mark': mark}
    if '敵' not in text:
        return None, {'reason': 'NO_ENEMY_TARGET'}
    match = MULTIHIT_RX.search(text)
    if match:
        return 'MULTIHIT', {'n': int(match.group(1)), 'clause': match.group(0)}
    match = BIGMID_RX.search(text)
    if match:
        return 'BIGMID', {'clause': match.group(0)}
    match = INTERVAL_RX.search(text)
    if match:
        return 'INTERVAL', {'clause': match.group(0)}
    match = SMALL_RX.search(text)
    if match:
        return 'SMALL', {'clause': match.group(0)}
    return 'PLAIN', {'clause': 'ダメージ'}


class RawView:
    """真实 Inputs 的只读记录视图；不修改 Inputs 类或实例。"""

    def __init__(self, root, decoded=None, rules=None):
        self.root = Path(root).resolve()
        self.decoded = (read_path(Path(decoded), root=self.root) if decoded is not None
                        else read_path(self.root / CACHE_DECODED, root=self.root))
        self.pages = read_path(self.root / PAGES_REL, root=self.root)
        self.rules_path = read_path(self.root / RULES_REL, root=self.root)
        self.rules = (rules if isinstance(rules, dict) and rules else
                      json.loads(self.rules_path.read_text(encoding='utf-8-sig')))
        self.versions = {}
        self.layers = {}
        self._cards = {}
        self._load_cache()
        self._load_apk()

    def _load_cache(self):
        snapshot = self.decoded.parent
        report = json.loads((snapshot / 'decode_report.json').read_text(encoding='utf-8-sig'))
        declared = {item.get('filename'): item.get('json_raw_sha256')
                    for item in report.get('files') or []}
        docs = {}
        for stem in ('charainfo', 'bossinfo'):
            path = self.decoded / (stem + '.data5.json.raw')
            actual = sha256_file(path)
            want = declared.get(stem + '.data5')
            if want != actual:
                raise ValueError('CACHE输入哈希与decode_report不符：%s' % path)
            docs[stem] = json.loads(path.read_text(encoding='utf-8-sig'))
            self.versions['CACHE/' + stem] = {
                'path': CACHE_DECODED + '/' + stem + '.data5.json.raw',
                'declared_sha256': want, 'actual_sha256': actual,
            }
        chara = docs['charainfo']['charainfo']
        boss = docs['bossinfo']['bossinfo']
        self.layers['CACHE'] = self._index_layer(chara, boss['bosspattern'], boss['bossskill'])

    def _load_apk(self):
        chara_path = read_path(self.root / APK_CHARA_REL, root=self.root)
        boss_path = read_path(self.root / APK_BOSS_REL, root=self.root)
        chara = json.loads(chara_path.read_text(encoding='utf-8-sig'))['charainfo']
        boss = json.loads(boss_path.read_text(encoding='utf-8-sig'))
        self.layers['APK'] = self._index_layer(chara, boss['bosspattern'], boss['bossskill'])
        self.versions['APK/charainfo'] = {
            'path': APK_CHARA_REL, 'actual_sha256': sha256_file(chara_path),
        }
        self.versions['APK/bossinfo'] = {
            'path': APK_BOSS_REL, 'actual_sha256': sha256_file(boss_path),
        }

    @staticmethod
    def _index_layer(chara_rows, pattern_rows, skill_rows):
        chara_index, pattern_index, skill_index = {}, {}, {}
        for i, rec in enumerate(chara_rows):
            chara_index.setdefault(rec.get('cid'), []).append(i)
        for i, rec in enumerate(pattern_rows):
            pattern_index.setdefault(rec.get('patternid'), []).append(i)
        for i, rec in enumerate(skill_rows):
            skill_index.setdefault(rec.get('skillid'), []).append(i)
        return {'charainfo_rows': chara_rows, 'pattern_docs': pattern_rows,
                'skill_docs': skill_rows, 'charainfo_index': chara_index,
                'pattern_index': pattern_index, 'skill_index': skill_index}

    @staticmethod
    def _unique(rows, index, key):
        hits = index.get(key) or []
        if len(hits) != 1:
            return None, None, len(hits)
        return rows[hits[0]], hits[0], 1

    def charainfo(self, layer, cid):
        view = self.layers[layer]
        return self._unique(view['charainfo_rows'], view['charainfo_index'], cid)

    def pattern(self, layer, pattern_id):
        view = self.layers[layer]
        return self._unique(view['pattern_docs'], view['pattern_index'], pattern_id)

    def skill(self, layer, skill_id):
        view = self.layers[layer]
        return self._unique(view['skill_docs'], view['skill_index'], skill_id)

    def card(self, cid):
        if cid not in self._cards:
            path = self.pages / str(cid) / 'card.json'
            self._cards[cid] = {
                'path': path, 'sha256': sha256_file(path),
                'doc': json.loads(path.read_text(encoding='utf-8-sig')),
            }
        return self._cards[cid]['doc']

    def page_sha256(self, cid):
        self.card(cid)
        return self._cards[cid]['sha256']

    def boss_source(self, layer, kind, index, record, field=None):
        pointer = '%s/%d' % (source_prefix(layer, kind), index)
        source = {
            'table': kind, 'record_id': record.get('patternid' if kind == 'bosspattern' else 'skillid'),
            'layer': layer, 'source_key': source_key(layer),
            'original_file': source_file(layer), 'json_pointer': pointer,
            'record_key': '%s#%s' % (source_key(layer), pointer),
            'record_index': index, 'source_resolution': EXACT,
            'raw_record_sha256': record_sha256(record),
            'raw_record_sha256_basis': 'UTF-8 compact JSON, sorted keys, ensure_ascii=false',
        }
        if field is not None:
            source.update(field_path='/' + field, field='/' + field,
                          field_json_pointer=pointer + '/' + field)
        return source


_VIEW_CACHE = weakref.WeakKeyDictionary()


def view_for(data):
    if isinstance(data, RawView):
        return data
    try:
        cached = _VIEW_CACHE.get(data)
    except TypeError:
        cached = None
    if cached is not None:
        return cached
    root = getattr(data, 'root', None)
    if root is None:
        raise TypeError('需要真实 card_page_data.Inputs 或 RawView')
    view = RawView(root, decoded=getattr(data, 'decoded', None),
                   rules=getattr(data, 'rule_metadata', None))
    try:
        _VIEW_CACHE[data] = view
    except TypeError:
        pass
    return view


def target_map(spec):
    return {target['row_id']: target for target in spec.targets}


def target_cids(spec):
    return frozenset(target['cid'] for target in spec.targets)


def _reject(reason, **detail):
    return {'status': 'REJECTED', 'reason': reason, 'answers': [], 'detail': detail}


def _parent_public(parent):
    return {
        'reference_field': parent['reference_field'], 'pattern_id': parent['pattern_id'],
        'pattern_index': parent['index'], 'json_pointer': parent['json_pointer'],
        'conditions_raw': conditions_raw(parent['record']),
        'children': [{'child_slot': child['child_slot'], 'record_id': child['record_id'],
                      'type': child['type'], 'record_index': child['index']}
                     for child in parent['children']],
    }


def _selection_public(selection):
    return {
        'reference_field': selection['parent']['reference_field'],
        'pattern_id': selection['parent']['pattern_id'],
        'pattern_index': selection['parent']['index'],
        'pattern_json_pointer': selection['parent']['json_pointer'],
        'parent_conditions_raw': conditions_raw(selection['parent']['record']),
        'child_slot': selection['child_slot'], 'record_id': selection['record_id'],
        'record_index': selection['index'], 'type': selection['type'],
        'field': selection['field'], 'raw_value': selection['raw'],
        'raw_state': selection['raw_state'], 'rule_key': selection['rule_key'],
        'source': selection['source'],
    }


def resolve_row(data, spec, cid, row, skill):
    target = target_map(spec).get(row.get('row_id'))
    if target is None:
        return _reject('ROW_NOT_IN_FROZEN_SCOPE', row_id=row.get('row_id'))
    if cid != target['cid'] or row.get('cid') not in (None, cid):
        return _reject('CID_MISMATCH', cid=cid, row_cid=row.get('cid'))
    if cid in spec.protected_cids:
        return _reject('ZERO_TOUCH_CID')
    if (row.get('group') or skill.get('original_group')) != 'special_move':
        return _reject('ROW_NOT_SPECIAL_MOVE')
    layer = target['layer']
    reference = target['reference_field']
    if row.get('reference_field') != reference or skill.get('reference_field') != reference:
        return _reject('REFERENCE_FIELD_MISMATCH', want=reference)
    if skill.get('table') != 'bosspattern' or skill.get('layer') != layer:
        return _reject('SKILL_SOURCE_MISMATCH', table=skill.get('table'), layer=skill.get('layer'))
    pattern_id = skill.get('record_id')
    if isinstance(pattern_id, bool) or not isinstance(pattern_id, int) or pattern_id <= 0:
        return _reject('PATTERN_RECORD_ID_INVALID', record_id=pattern_id)
    chara, chara_index, hits = data.charainfo(layer, cid)
    if chara is None:
        return _reject('CHARAINFO_NOT_UNIQUE', hits=hits, layer=layer)
    if chara.get(reference) != pattern_id:
        return _reject('CHARAINFO_PATTERN_LINK_MISMATCH', got=chara.get(reference), want=pattern_id)
    pattern, pattern_index, hits = data.pattern(layer, pattern_id)
    if pattern is None:
        return _reject('BOSSPATTERN_NOT_UNIQUE', hits=hits, pattern_id=pattern_id)
    src = row.get('source') or {}
    pointer = '%s/%d' % (source_prefix(layer, 'bosspattern'), pattern_index)
    if src.get('json_pointer') != pointer or src.get('field_json_pointer') != pointer + '/sinfo':
        return _reject('ROW_SOURCE_POINTER_MISMATCH', want=pointer,
                       got=src.get('json_pointer'), got_field=src.get('field_json_pointer'))
    if src.get('layer') != layer:
        return _reject('ROW_SOURCE_LAYER_MISMATCH', got=src.get('layer'), want=layer)
    parent_text = str(pattern.get('sinfo') or '')
    if not parent_text:
        return _reject('PATTERN_SINFO_MISSING')
    if canon(parent_text) != canon(row.get('context_text')):
        return _reject('CONTEXT_TEXT_MISMATCH')
    if canon(parent_text) != canon(skill.get('original_text')):
        return _reject('SKILL_ORIGINAL_TEXT_MISMATCH')
    japanese = str(row.get('japanese') or '')
    start = parent_text.find(japanese)
    if not japanese or start < 0 or parent_text.count(japanese) != 1:
        return _reject('FRAGMENT_SPAN_NOT_UNIQUE', count=parent_text.count(japanese))
    analysis = LEDGER.analyze_row(row, table='bosspattern')
    effects = [effect for effect in analysis.get('effects') or []
               if effect.get('record_type') == 'effect'
               and effect.get('effect_id') == target['effect_id']]
    if len(effects) != 1 or effects[0].get('effect_type') != 'ダメージ（词表外）':
        return _reject('TARGET_EFFECT_MISMATCH', effect_id=target['effect_id'],
                       found=[(e.get('effect_id'), e.get('effect_type'))
                              for e in analysis.get('effects') or []])
    form, form_detail = classify_clause(japanese)
    allowed_forms = {'DIRECT': {'MULTIHIT', 'BIGMID', 'INTERVAL'},
                     'HP_CHAIN': {'PLAIN'}, 'USE_ONCE_NORMAL': {'INTERVAL'},
                     'CURRENT_SUPER_UI': {'INTERVAL'}, 'TERRAIN_SHARED': {'INTERVAL'},
                     'JOB_AFTER_COST': {'SMALL'}, 'SCRAP_BASE_SAME_VALUE': {'SMALL'},
                     'SCRAP_TWO_TIER': {'MULTIHIT', 'BIGMID'}}
    if form not in allowed_forms[target['model']]:
        return _reject('CLAUSE_FORM_NOT_ADMITTED', form=form, detail=form_detail)
    parents = []
    refs = sorted((key for key, value in chara.items()
                   if PATTERN_REF_RX.match(key) and value), key=lambda key: int(key[7:]))
    for ref in refs:
        pid = chara.get(ref)
        prec, pidx, phits = data.pattern(layer, pid)
        if prec is None:
            return _reject('PARENT_PATTERN_NOT_UNIQUE', reference_field=ref,
                           pattern_id=pid, hits=phits)
        children = []
        slots = [slot for slot in range(7) if prec.get('skillid%d' % slot)]
        if slots != list(range(len(slots))):
            return _reject('CHILD_SLOTS_NOT_CONTIGUOUS', pattern_id=pid, slots=slots)
        for slot in slots:
            sid = prec.get('skillid%d' % slot)
            rec, ridx, rhits = data.skill(layer, sid)
            if rec is None:
                return _reject('CHILD_RECORD_NOT_UNIQUE', pattern_id=pid,
                               child_slot=slot, record_id=sid, hits=rhits)
            children.append({'child_slot': slot, 'record_id': sid, 'index': ridx,
                             'type': rec.get('skillid0'), 'record': rec})
        parents.append({'reference_field': ref, 'pattern_id': pid, 'index': pidx,
                        'json_pointer': '%s/%d' % (source_prefix(layer, 'bosspattern'), pidx),
                        'record': prec, 'children': children})
    current = [parent for parent in parents if parent['pattern_id'] == pattern_id]
    if len(current) != 1:
        return _reject('CURRENT_PARENT_NOT_IN_COMPLETE_SET', hits=len(current))
    return {
        'status': 'RESOLVED_CONTEXT', 'target': target, 'layer': layer,
        'charainfo': chara, 'charainfo_index': chara_index,
        'current_parent': current[0], 'parents': parents,
        'parent_text': parent_text, 'japanese': japanese,
        'fragment_span': {'start': start, 'end': start + len(japanese),
                          'unit': 'char', 'fragment': japanese,
                          'parent_json_pointer': pointer + '/sinfo'},
        'analysis': analysis, 'effect': effects[0], 'form': form, 'form_detail': form_detail,
        'page_source': dict(src),
    }


def select_carrier(data, context, parent):
    form, detail = context['form'], context['form_detail']
    model = context['target']['model']
    if form == 'MULTIHIT':
        n = detail['n']
        hits = [child for child in parent['children']
                if child['type'] in MULTI_TYPES and child['record'].get('skillparam6') == n]
        if len(hits) != 1:
            raise ValueError('MULTIHIT_CARRIER_NOT_UNIQUE:%s:%d' % (parent['pattern_id'], len(hits)))
    else:
        types = SINGLE_TYPES
        if form == 'INTERVAL':
            types = (55,) if model != 'DIRECT' else SINGLE_TYPES
        elif form in ('SMALL', 'PLAIN'):
            types = (3,)
        hits = [child for child in parent['children'] if child['type'] in types]
        if len(hits) != 1:
            raise ValueError('SINGLE_CARRIER_NOT_UNIQUE:%s:%d' % (parent['pattern_id'], len(hits)))
    child = hits[0]
    etype = child['type']
    if etype not in DAMAGE_SLOT:
        raise ValueError('TYPE_WITHOUT_CONFIRMED_DAMAGE_RULE:%s' % etype)
    slot, rule_keys = C14.unique_damage_slot(data.rules, etype)
    if slot is None or slot != DAMAGE_SLOT[etype]:
        raise ValueError('DAMAGE_SLOT_NOT_UNIQUE:%s:%r' % (etype, rule_keys))
    rule_key = 'bossskill|%d|/%s' % (etype, slot)
    if rule_key not in LEDGER.G1B1_RULE_EFFECT:
        raise ValueError('RULE_NOT_G1B1_CONSUMABLE:' + rule_key)
    state = raw_state(child['record'], slot)
    if state != 'FINITE':
        raise ValueError('RAW_NOT_FINITE_POSITIVE:%s:%s' % (child['record_id'], state))
    raw = child['record'][slot]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(raw) or raw <= 0:
        raise ValueError('RAW_NOT_FINITE_POSITIVE:%s' % child['record_id'])
    layer = context['layer']
    return {
        'parent': parent, 'child_slot': child['child_slot'], 'record_id': child['record_id'],
        'index': child['index'], 'type': etype, 'field': slot, 'raw': raw,
        'raw_state': state, 'rule_key': rule_key, 'record': child['record'],
        'source': data.boss_source(layer, 'bossskill', child['index'], child['record'], slot),
    }


def _value(record, key):
    value = record.get(key, 0)
    return 0 if value is None else value


def _same_cohort(context, parents, *, scost=False):
    current = context['current_parent']['record']
    flag = _value(current, 'flag')
    return [parent for parent in parents
            if _value(parent['record'], 'flag') == flag
            and (not scost or _value(parent['record'], 'scost') == _value(current, 'scost'))]


def _select_many(data, context, parents):
    return [select_carrier(data, context, parent) for parent in parents]


def _answer_spec(selection, condition, related=None, merged=None, excluded=None):
    return {'selection': selection, 'condition_label': condition,
            'related': related if related is not None else [selection],
            'merged': merged or [], 'excluded': excluded or []}


def direct_condition(current):
    record = current['record']
    chs, che = _value(record, 'chs'), _value(record, 'che')
    if (chs, che) == (0, 0):
        scope = '当前基础档（未设置Chain区间条件）'
    elif (chs, che) == (0, 1):
        scope = '0thChain（通常）当前档'
    elif (chs, che) == (0, 2):
        scope = '0th／1stChain当前档'
    elif (chs, che) == (2, 5):
        scope = '1stChain以上（含MaxChain）当前档'
    else:
        scope = 'Chain计数%d–%d当前档' % (chs, che)
    return '仅%s被选中时；其它档位的数值不并入' % scope


def select_by_model(data, context):
    model = context['target']['model']
    parents = context['parents']
    current = context['current_parent']
    if model == 'DIRECT':
        selected = select_carrier(data, context, current)
        return [_answer_spec(selected, direct_condition(current))]
    if model == 'HP_CHAIN':
        cohort = _same_cohort(context, parents)
        if len(cohort) != 8:
            raise ValueError('HP_PARENT_SET_NOT_COMPLETE:%d' % len(cohort))
        selected = _select_many(data, context, cohort)
        groups = {}
        for item in selected:
            groups.setdefault(item['record_id'], []).append(item)
        if len(groups) != 4:
            raise ValueError('HP_UNIQUE_RECORD_GROUP_COUNT:%d' % len(groups))
        out = []
        for group in groups.values():
            if len(group) != 2 or len({item['raw'] for item in group}) != 1:
                raise ValueError('HP_CHAIN_GROUP_NOT_SHARED_RECORD')
            bands = {(_value(item['parent']['record'], 'hpstart'),
                      _value(item['parent']['record'], 'hpend')) for item in group}
            chains = {(_value(item['parent']['record'], 'chs'),
                       _value(item['parent']['record'], 'che')) for item in group}
            if len(bands) != 1 or chains != {(0, 1), (2, 5)}:
                raise ValueError('HP_CHAIN_CONDITION_PARTITION_MISMATCH')
            lo, hi = next(iter(bands))
            primary = next(item for item in group
                           if (_value(item['parent']['record'], 'chs'),
                               _value(item['parent']['record'], 'che')) == (0, 1))
            condition = ('自身当前HP整数百分比为%d–%d%%（含边界）；0thChain（通常）与1stChain以上（含MaxChain）的来源相同'
                         % (lo, hi))
            out.append(_answer_spec(primary, condition, related=group,
                                    merged=[item for item in group if item is not primary]))
        out.sort(key=lambda item: -_value(item['selection']['parent']['record'], 'hpstart'))
        bands = [(_value(item['selection']['parent']['record'], 'hpstart'),
                  _value(item['selection']['parent']['record'], 'hpend')) for item in out]
        if bands != [(76, 100), (51, 75), (26, 50), (0, 25)]:
            raise ValueError('HP_BAND_COVERAGE_MISMATCH:%r' % bands)
        return out
    if model == 'USE_ONCE_NORMAL':
        cohort = _same_cohort(context, parents, scost=True)
        if len(cohort) != 2:
            raise ValueError('USE_ONCE_PARENT_COUNT:%d' % len(cohort))
        selected = _select_many(data, context, cohort)
        limited = [item for item in selected if _value(item['parent']['record'], 'limit') == 1]
        base = [item for item in selected if _value(item['parent']['record'], 'limit') == 0]
        if len(limited) != 1 or len(base) != 1 or limited[0]['record_id'] == base[0]['record_id']:
            raise ValueError('USE_ONCE_STAGE_AMBIGUOUS')
        return [
            _answer_spec(limited[0], '当前同一控制器尚未使用（使用次数不足1次）；执行沿用当前界面缓存档位'),
            _answer_spec(base[0], '当前同一控制器已使用1次后，采用强化1次档（最大强化1次）；不保证跨波、复活或重建不重置'),
        ]
    if model == 'CURRENT_SUPER_UI':
        cohort = _same_cohort(context, parents)
        if len(cohort) != 2:
            raise ValueError('SUPER_PARENT_COUNT:%d' % len(cohort))
        selected = _select_many(data, context, cohort)
        current_items = [item for item in selected if item['parent'] is current]
        if len(current_items) != 1 or _value(current['record'], 'priority') <= 0:
            raise ValueError('CURRENT_SUPER_NOT_POSITIVE_WEIGHT')
        others = [item for item in selected if item['parent'] is not current]
        if len(others) != 1 or _value(others[0]['parent']['record'], 'priority') != 0:
            raise ValueError('OLD_SUPER_CANDIDATE_NOT_ZERO_WEIGHT')
        excluded = [dict(item=others[0], reason='旧候选父：priority缺失时构造0，当前常规UI预测不选用；不重复计答案')]
        return [_answer_spec(current_items[0],
                             '超共鸣模式且当前常规界面预测选中；旧候选不并入',
                             excluded=excluded)]
    if model == 'TERRAIN_SHARED':
        cohort = _same_cohort(context, parents, scost=True)
        if len(cohort) != 2:
            raise ValueError('TERRAIN_PARENT_COUNT:%d' % len(cohort))
        selected = _select_many(data, context, cohort)
        forest = [item for item in selected
                  if _value(item['parent']['record'], 'bgf') == 4
                  and _value(item['parent']['record'], 'limit') == 3]
        base = [item for item in selected
                if _value(item['parent']['record'], 'bgf') == 0
                and _value(item['parent']['record'], 'limit') == 0]
        if len(forest) != 1 or len(base) != 1:
            raise ValueError('TERRAIN_BASE_PAIR_MISMATCH')
        if forest[0]['record_id'] != base[0]['record_id'] or forest[0]['raw'] != base[0]['raw']:
            raise ValueError('TERRAIN_NOT_SHARED_RECORD')
        primary = next(item for item in selected if item['parent'] is current)
        condition = ('常规基础分支使用同一伤害来源；森林（含夜间）且当前控制器该地形分支使用不足3次时，'
                     '亦使用这一来源；非森林或次数耗尽回退基础分支，次数不保证跨波/复活/重建不重置')
        return [_answer_spec(primary, condition, related=selected,
                             merged=[item for item in selected if item is not primary])]
    if model == 'JOB_AFTER_COST':
        cohort = _same_cohort(context, parents, scost=True)
        if len(cohort) != 2:
            raise ValueError('JOB_PARENT_COUNT:%d' % len(cohort))
        selected = _select_many(data, context, cohort)
        selected.sort(key=lambda item: _value(item['parent']['record'], 'mns'))
        ranges = [(_value(item['parent']['record'], 'mns'),
                   _value(item['parent']['record'], 'mne')) for item in selected]
        if ranges != [(0, 2), (3, 12)] or len({item['record_id'] for item in selected}) != 2:
            raise ValueError('JOB_COUNTER_PARTITION_MISMATCH:%r' % ranges)
        return [_answer_spec(item,
                             '普通界面选档预测扣费后职业法珠%d–%d颗（含边界；执行沿用缓存档位）'
                             % (_value(item['parent']['record'], 'mns'),
                                _value(item['parent']['record'], 'mne')))
                for item in selected]
    if model == 'SCRAP_BASE_SAME_VALUE':
        cohort = _same_cohort(context, parents, scost=True)
        if len(cohort) != 2:
            raise ValueError('SCRAP_BASE_PARENT_COUNT:%d' % len(cohort))
        selected = _select_many(data, context, cohort)
        selected.sort(key=lambda item: _value(item['parent']['record'], 'mns'))
        ranges = [(_value(item['parent']['record'], 'mns'),
                   _value(item['parent']['record'], 'mne')) for item in selected]
        if ranges != [(0, 3), (4, 12)] or selected[0]['raw'] != selected[1]['raw']:
            raise ValueError('SCRAP_SAME_VALUE_PARTITION_MISMATCH:%r' % ranges)
        if selected[0]['record_id'] == selected[1]['record_id']:
            raise ValueError('SCRAP_SAME_VALUE_REQUIRES_DISTINCT_RECORDS')
        if selected[0]['parent'] is not current:
            raise ValueError('SCRAP_CURRENT_NOT_BASE_PARENT')
        condition = ('普通界面选档时废料0–12个；0–3与4–12两个不同来源的原值相同，合记一项'
                     '（执行沿用缓存档位）')
        return [_answer_spec(selected[0], condition, related=selected,
                             merged=[dict(item=selected[1],
                                          reason='4–12废料分支为同值异记录，只披露，不重复计答案')])]
    if model == 'SCRAP_TWO_TIER':
        cohort = _same_cohort(context, parents)
        if len(cohort) != 2:
            raise ValueError('SCRAP_TWO_TIER_PARENT_COUNT:%d' % len(cohort))
        selected = _select_many(data, context, cohort)
        selected.sort(key=lambda item: _value(item['parent']['record'], 'mns'))
        ranges = [(_value(item['parent']['record'], 'mns'),
                   _value(item['parent']['record'], 'mne')) for item in selected]
        if (len(ranges) != 2 or ranges[0][0] != 0 or ranges[0][1] < 0
                or ranges[1] != (ranges[0][1] + 1, 12)
                or len({item['record_id'] for item in selected}) != 2):
            raise ValueError('SCRAP_TWO_TIER_PARTITION_MISMATCH:%r' % ranges)
        if selected[0]['parent'] is not current:
            raise ValueError('SCRAP_CURRENT_NOT_LOWER_PARENT')
        out = [_answer_spec(item,
                            '普通界面选档时废料%d–%d个（含边界；执行沿用缓存档位）'
                            % (_value(item['parent']['record'], 'mns'),
                               _value(item['parent']['record'], 'mne')))
               for item in selected]
        excluded = []
        for parent in parents:
            if parent in cohort:
                continue
            item = select_carrier(data, context, parent)
            excluded.append({'item': item,
                             'reason': '其它模式／超共鸣父不并入本行条件答案，只在答案内登记排除'})
        if excluded:
            out[0]['excluded'].extend(excluded)
        return out
    raise ValueError('UNKNOWN_CONDITION_MODEL:' + model)


def other_sentences(text, current):
    out = []
    for part in str(text or '').replace('\n', '。').split('。'):
        part = part.strip()
        if part and canon(part) != canon(current).rstrip('。'):
            out.append(part)
    return out


def build_answer(data, spec, context, answer_spec):
    selected = answer_spec['selection']
    layer, record = context['layer'], selected['record']
    raw, field, etype = selected['raw'], selected['field'], selected['type']
    rule_key = selected['rule_key']
    rule = RULES.answer_for('bossskill', etype, '/' + field, raw, record, source_layer=layer)
    if not rule or rule.get('value_text') is None:
        raise ValueError('既有规则无法回答：' + rule_key)
    condition = answer_spec['condition_label']
    num = num_text(raw)
    cid = context['target']['cid']
    if context['form'] == 'MULTIHIT':
        n = context['form_detail']['n']
        player = ('这一句对敌方造成伤害：每次伤害输入按技能基础攻击的%s倍计算；原文%d回是攻击次数，'
                  '不是把倍率再乘成最终总伤。条件：%s。' % (num, n, condition))
    else:
        player = '这一句对敌方造成伤害：伤害输入按技能基础攻击的%s倍计算。条件：%s。' % (num, condition)
    if cid == 20332:
        player = player.replace('这一句对敌方造成伤害', '这一句中对前方敌人的部分', 1)
        player += '同句自身受伤与后续周期攻击另论，不在本项回答。'
    player += '这是处理器收到的局部输入，实际扣血和命中未验证。'
    source = dict(selected['source'])
    effect_id = context['target']['effect_id']
    related = [_selection_public(item) for item in answer_spec['related']]
    merged = []
    for item in answer_spec['merged']:
        if isinstance(item, dict) and 'item' in item:
            merged.append({'selection': _selection_public(item['item']), 'reason': item['reason']})
        else:
            merged.append({'selection': _selection_public(item), 'reason': '同记录多父合记，不重复计答案'})
    excluded = []
    for item in answer_spec['excluded']:
        excluded.append({'selection': _selection_public(item['item']), 'reason': item['reason']})
    all_parents = [_parent_public(parent) for parent in context['parents']]
    binding_payload = {
        'scope': spec.scope, 'module': spec.module_version, 'effect_id': effect_id,
        'row_id': context['target']['row_id'], 'cid': cid,
        'model': context['target']['model'], 'binding': 'inferred',
        'association_evidence': '推断', 'runtime_verified': False,
        'condition_label': condition, 'rule_key': rule_key,
        'record_id': selected['record_id'], 'layer': layer,
        'current_parent': _parent_public(context['current_parent']),
        'complete_parent_set': all_parents, 'selected': _selection_public(selected),
        'related_sources': related, 'merged_disclosures': merged,
        'excluded_branch_values': excluded, 'fragment_span': context['fragment_span'],
        'selection_facts': '静态原表与既有选择器补证；必要条件不等于完整运行时证明',
        'native_evidence': '复用既有规则体及静态原生补证；本批没有新原生执行或实机验证',
    }
    g1 = {
        'scope': LEDGER_SCOPE, 'structure_scope': spec.scope, 'module': spec.module_version,
        'cid': cid, 'row_id': context['target']['row_id'], 'effect_id': effect_id,
        'rule_key': rule_key, 'field_path': '/' + field, 'table': 'bossskill',
        'record_id': selected['record_id'], 'layer': layer, 'source': source,
        'pattern_id': selected['parent']['pattern_id'], 'child_slot': selected['child_slot'],
        'binding': 'inferred', 'runtime_verified': False,
    }
    others = other_sentences(context['parent_text'], context['japanese'])
    unresolved_others = [
        {'effect_id': effect.get('effect_id'), 'effect_type': effect.get('effect_type'),
         'status': effect.get('status'), 'snippet': effect.get('snippet')}
        for effect in context['analysis'].get('effects') or []
        if effect.get('record_type') == 'effect' and effect.get('effect_id') != effect_id
        and effect.get('status') == 'unresolved'
    ]
    not_included = {
        'other_sentences': others, 'other_unresolved_effects': unresolved_others,
        'merged_or_excluded_branch_values': merged + excluded,
        'note': '其它句子、效果、旧候选父与排除分支不借值；同句未解效果仍按原effect_id披露',
    }
    if cid == 20332:
        not_included['self_damage_and_periodic_attack'] = '自身受伤与后续type116周期攻击另论'
    conditions = [condition, '仅本项局部伤害输入，不推广为最终扣血、保证命中或完整选档证明',
                  layer + '静态原表；运行时装载、缓存新鲜度和实际执行未实机验证']
    evidence = [
        'docs/tasks/20261108-c20-cycle.md',
        'docs/tasks/20261108-c20-web-absorption-assessment.md',
        'docs/tasks/20261107-reader-mainline-evidence-handoff.md',
    ]
    model = context['target']['model']
    if model == 'DIRECT':
        evidence += ['docs/tasks/20261102-c14-p2-boss-damage-direct.md',
                     'output/character_skills/c14_p2_boss_damage_direct_20261102/README.md']
    else:
        evidence.append('output/character_skills/reader_full_20261106/audit/c19_closeout_20261107/condition_closeout_receipt.json')
    if model == 'HP_CHAIN':
        evidence.append('output/character_skills/reader_full_20261106/audit/player_conditions_20261107/native_conditions.json')
    if model in ('USE_ONCE_NORMAL', 'CURRENT_SUPER_UI'):
        evidence.append('output/character_skills/reader_full_20261106/audit/final5_evidence_20261107/sparse_receipt.json')
    if model == 'TERRAIN_SHARED':
        evidence += ['output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/native_selection_proof.json',
                     'output/ordinary_effects/ability7/trace.json']
    if model in ('JOB_AFTER_COST', 'SCRAP_BASE_SAME_VALUE', 'SCRAP_TWO_TIER'):
        evidence.append('output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/mana_timing_receipt.json')
    binding = {
        'scope': spec.scope, 'pattern_id': selected['parent']['pattern_id'],
        'slot': 'skillid%d' % selected['child_slot'], 'child_id': selected['record_id'],
        'condition': condition, 'g1_b1_binding': g1, spec.binding_key: binding_payload,
        'fields': [{'f': '/' + field, 'raw': raw}],
    }
    effect_binding = {
        'row_id': context['target']['row_id'], 'effect_type': 'ダメージ（词表外）',
        'span': list(context['effect']['span']),
        'variant_group': '%s|%s|%s' % (context['target']['row_id'], spec.scope,
                                       context['effect']['span']),
        'pattern_id': selected['parent']['pattern_id'], 'child_id': selected['record_id'],
        'field_path': '/' + field,
    }
    answer = {
        'value': (rule['value_text'] + '；条件：' + condition +
                  '；来源：%s bossskill %s /%s（下标%d）。仅局部伤害输入，未验证最终扣血或命中。'
                  % (layer, selected['record_id'], field, selected['index'])),
        'player_text': player,
        'player_scope': {
            'object': '前方范围内的敌人（同句自身受伤另论）' if cid == 20332 else '句面敌人',
            'quantity': rule.get('kind') or '技能基值倍率', 'unit': rule.get('unit'),
            'conditions': conditions, 'duration': '不适用（本项是伤害输入；持续与周期效果另论）',
            'unknowns': ['最终扣血、实际命中、运行时装载和完整执行结果未验证',
                         '句面到该记录的归属为推断', '其它句子、效果和排除分支不并入'],
        },
        'quantity_kind': rule.get('kind') or '技能基值倍率',
        'unit': rule.get('unit'), 'unit_raw': rule.get('unit'),
        'raw_value': raw, 'effective_float32': f32(raw), 'normalized_value': raw,
        'quantitative': True, 'numeric_source': '既有原生静态局部规则＋%s bossskill原始记录' % layer,
        'numeric_evidence': '确认', 'association_evidence': '推断',
        'answer_status': rule.get('answer_status') or rule.get('rule_status') or 'CONFIRMED_FORMULA_ONLY',
        'evidence_scope': spec.scope, 'rule_key': rule_key, 'field_path': '/' + field,
        'table': 'bossskill', 'record_id': selected['record_id'], 'layer': layer,
        'source': source, 'original_text': context['japanese'],
        'context': context['parent_text'], 'condition_label': condition,
        'conditions': conditions, 'target': '前方敌人（自身受伤另论）' if cid == 20332 else '敌',
        'binding': binding, 'effect_binding': effect_binding,
        'not_included': not_included,
        'note': ('原值与既有规则体已核；句面归属为推断。B=getBasicSkillAttack(true)已含Chain，'
                 '不重复乘Chain；本项不是最终扣血。关联推断、未实机、运行时缓存与选档边界保留。'),
        'evidence': evidence,
    }
    return answer


def evaluate(data, cid, row, *, scope=None, skill=None, spec):
    require_scope(spec, scope)
    data = view_for(data)
    skill = skill or {}
    try:
        context = resolve_row(data, spec, cid, row, skill)
        if context['status'] == 'REJECTED':
            return context
        answer_specs = select_by_model(data, context)
        answers = [build_answer(data, spec, context, item) for item in answer_specs]
        expected = 1 if context['target']['model'] in {
            'DIRECT', 'CURRENT_SUPER_UI', 'TERRAIN_SHARED', 'SCRAP_BASE_SAME_VALUE'} else None
        if expected is not None and len(answers) != expected:
            return _reject('ANSWER_COUNT_MISMATCH', got=len(answers), want=expected)
        return {
            'status': 'RESOLVED', 'reason': None, 'answers': answers,
            'target': context['target'], 'context': context,
            'selected': [_selection_public(item['selection']) for item in answer_specs],
            'analysis_summary': {
                'baseline_effect_status': context['effect'].get('status'),
                'baseline_split_flags': context['analysis'].get('split_flags'),
                'unresolved_effect_ids': [e.get('effect_id') for e in context['analysis'].get('effects') or []
                                          if e.get('record_type') == 'effect'
                                          and e.get('status') == 'unresolved'],
            },
        }
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return _reject('SOURCE_OR_CONDITION_GATE_FAILED', error=str(exc))


def answer_identity(answer, spec):
    binding = (answer.get('binding') or {}).get(spec.binding_key) or {}
    return (answer.get('rule_key'), answer.get('record_id'), answer.get('field_path'),
            answer.get('raw_value'), answer.get('condition_label'), answer.get('layer'),
            binding.get('effect_id'), binding.get('scope'))


def apply_to_groups(data, cid, groups, *, scope=None, spec):
    require_scope(spec, scope)
    report = {'cid': cid, 'scope': scope, 'module_version': spec.module_version,
              'status': 'OUT_OF_SCOPE', 'rows': [], 'added': 0, 'skipped': 0,
              'conflicts': 0, 'rejected': 0}
    if cid not in target_cids(spec):
        report['detail'] = '保护卡' if cid in spec.protected_cids else '不在本批冻结作用域'
        return report
    report['status'] = 'APPLIED'
    data = view_for(data)
    wanted = {target['row_id'] for target in spec.targets if target['cid'] == cid}
    for _group, skill, row in iter_rows(groups):
        if row.get('row_id') not in wanted:
            continue
        result = evaluate(data, cid, row, scope=scope, skill=skill, spec=spec)
        entry = {'row_id': row.get('row_id'), 'status': result['status'],
                 'reason': result.get('reason'), 'added': 0, 'skipped': 0, 'conflicts': 0}
        if result['status'] != 'RESOLVED':
            entry['detail'] = result.get('detail')
            report['rejected'] += 1
            report['rows'].append(entry)
            continue
        existing = row.setdefault('answers', [])
        to_add, to_skip, conflicts = [], [], []
        for answer in result['answers']:
            identity = answer_identity(answer, spec)
            exact = [old for old in existing if answer_identity(old, spec) == identity]
            if exact:
                to_skip.append(answer)
                continue
            same_rule = [old for old in existing if old.get('rule_key') == answer.get('rule_key')]
            if same_rule:
                conflicts.append({'rule_key': answer.get('rule_key'),
                                  'record_id': answer.get('record_id'),
                                  'reason': 'EXISTING_RULE_ANSWER_NOT_IDENTICAL'})
            else:
                to_add.append(answer)
        if conflicts:
            entry['conflicts'] = len(conflicts)
            entry['conflict_detail'] = conflicts
            report['conflicts'] += len(conflicts)
            report['rows'].append(entry)
            continue
        if to_add and row.get('inference_yg1') is not None \
                and row['inference_yg1'].get('scope') != spec.scope:
            entry['conflicts'] = 1
            entry['conflict_detail'] = [{'reason': 'EXISTING_YG1_SCOPE_CONFLICT'}]
            report['conflicts'] += 1
            report['rows'].append(entry)
            continue
        for answer in to_add:
            existing.append(answer)
        entry['added'], entry['skipped'] = len(to_add), len(to_skip)
        report['added'] += len(to_add)
        report['skipped'] += len(to_skip)
        if to_add:
            row['row_class'] = 'A'
            row['partial'] = True
            row['association_evidence'] = '推断'
            row['numeric_evidence'] = '确认'
            old_scope = row.get('evidence_scope') or []
            if isinstance(old_scope, str):
                old_scope = [old_scope]
            row['evidence_scope'] = list(dict.fromkeys(list(old_scope) + [spec.scope]))
            reasons = [reason for reason in row.get('unknown_reasons') or []
                       if reason not in STALE_REASONS]
            note = ('%s：本行主伤害效果已按真实pattern/bossskill来源绑定局部伤害输入；'
                    '同句其它效果、句外强化和排除分支仍保留。' % spec.scope)
            if note not in reasons:
                reasons.append(note)
            row['unknown_reasons'] = reasons
            row[spec.marker_key] = {
                'scope': spec.scope, 'module': spec.module_version,
                'answer_identities': [list(answer_identity(answer, spec)) for answer in to_add],
                'association': '推断', 'runtime_verified': False,
            }
            marker = row.get('inference_yg1')
            if marker is None:
                marker = {'scope': spec.scope, 'mirror': False, 'pattern_ids': [],
                          'pattern_records': [], 'formula_types': []}
                row['inference_yg1'] = marker
            for answer in to_add:
                eb = answer['effect_binding']
                pid = eb['pattern_id']
                if pid not in marker['pattern_ids']:
                    marker['pattern_ids'].append(pid)
                if answer['quantity_kind'] not in marker['formula_types']:
                    marker['formula_types'].append(answer['quantity_kind'])
                marker['pattern_records'].append({
                    'pattern_id': pid, 'child_id': eb['child_id'],
                    'field_path': eb['field_path'], 'condition_label': answer['condition_label'],
                    'scope': spec.scope,
                })
        report['rows'].append(entry)
    return report


def baseline_identity(root):
    root = Path(root)
    pages = read_path(root / PAGES_REL, root=root)
    pointer = json.loads((pages / '_batch/campaign_latest.json').read_text(encoding='utf-8-sig'))
    campaign = json.loads((pages / pointer['report']).read_text(encoding='utf-8-sig'))
    metrics = json.loads(read_path(root / 'output/character_skills/effect_ledger/metrics.json', root=root)
                         .read_text(encoding='utf-8-sig'))
    return {'campaign': campaign.get('signature'),
            'snapshot': (metrics.get('snapshot') or {}).get('snapshot_id')}


def build_candidates(root, spec):
    root = Path(root).resolve()
    data = RawView(root)
    items, exclusions = [], []
    by_row = target_map(spec)
    for target in spec.targets:
        cid = target['cid']
        card = data.card(cid)
        found = [(skill, row) for _group, skill, row in iter_rows(card)
                 if row.get('row_id') == target['row_id']]
        if len(found) != 1:
            exclusions.append({'category': 'TARGET', 'cid': cid, 'row_id': target['row_id'],
                               'reason_code': 'TARGET_ROW_NOT_UNIQUE', 'hits': len(found)})
            continue
        skill, row = found[0]
        result = evaluate(data, cid, row, scope=spec.scope, skill=skill, spec=spec)
        if result['status'] != 'RESOLVED':
            exclusions.append({'category': 'TARGET', 'cid': cid, 'row_id': target['row_id'],
                               'effect_id': target['effect_id'], 'japanese': row.get('japanese'),
                               'reason_code': result.get('reason'), 'detail': result.get('detail')})
            continue
        context = result['context']
        items.append({
            'cid': cid, 'row_id': target['row_id'], 'effect_id': target['effect_id'],
            'layer': target['layer'], 'reference_field': target['reference_field'],
            'model': target['model'], 'japanese': row.get('japanese'),
            'context_text': row.get('context_text'), 'fragment_span': context['fragment_span'],
            'page_source': row.get('source'), 'existing_answers': copy.deepcopy(row.get('answers') or []),
            'baseline_effect': copy.deepcopy(context['effect']),
            'baseline_split_flags': context['analysis'].get('split_flags'),
            'complete_parent_set': [_parent_public(parent) for parent in context['parents']],
            'selected': result['selected'], 'answers': result['answers'],
            'analysis_summary': result['analysis_summary'],
        })
    target_rows = set(by_row)
    for cid in sorted(target_cids(spec)):
        card = data.card(cid)
        for group, skill, row in iter_rows(card):
            row_id = row.get('row_id')
            if row_id in target_rows:
                continue
            group_name = group.get('group') or skill.get('original_group')
            if group_name == 'denju':
                exclusions.append({'category': 'DENJU', 'cid': cid, 'row_id': row_id,
                                   'reason_code': 'DENJU_OUT_OF_SCOPE',
                                   'reason': '传授行不复制本批charainfo/pattern答案'})
                continue
            if group_name != 'special_move':
                continue
            form, detail = classify_clause(row.get('japanese'))
            if form is not None:
                exclusions.append({'category': 'OTHER_PATTERN_ROW', 'cid': cid, 'row_id': row_id,
                                   'japanese': row.get('japanese'), 'form': form,
                                   'form_detail': detail, 'reason_code': 'DAMAGE_ROW_OUT_OF_FROZEN_SCOPE',
                                   'reason': '其它pattern/超共鸣/镜像行不自动外推'})
    for cid in spec.negative_cids:
        exclusions.append({'category': 'NAMED_NEGATIVE', 'cid': cid,
                           'reason_code': 'EXISTING_ANSWER_OR_UNCLOSED_MECHANISM',
                           'reason': '30207已有正式答案；278动画映射未闭合；本批零新增'})
    for cid in spec.protected_cids:
        exclusions.append({'category': 'PROTECTED', 'cid': cid, 'reason_code': 'ZERO_TOUCH_CID',
                           'reason': '保护卡整卡零触碰'})
    answers = [answer for item in items for answer in item['answers']]
    module_path = root / spec.module_file
    common_path = _HERE / 'card_page_inference_c20_direct_damage_common.py'
    candidate = {
        'schema': 'c20-direct-damage-candidates-1', 'candidate_only': True,
        'module': spec.module_version,
        'module_path': module_path.relative_to(root).as_posix(),
        'module_sha256': sha256_file(module_path),
        'common_module_path': common_path.relative_to(root).as_posix(),
        'common_module_sha256': sha256_file(common_path),
        'scope': spec.scope, 'binding_key': spec.binding_key,
        'targets': [dict(target) for target in spec.targets],
        'baseline': baseline_identity(root),
        'inputs': {
            'decoded': data.versions,
            'rules': {'path': RULES_REL, 'sha256': sha256_file(data.rules_path),
                      'key_count': len(data.rules)},
            'pages': {str(cid): {'path': PAGES_REL + '/%d/card.json' % cid,
                                 'sha256': data.page_sha256(cid)} for cid in sorted(target_cids(spec))},
        },
        'items': items, 'answers': answers,
        'counts': {
            'target_rows': len(spec.targets), 'resolved_rows': len(items),
            'cids': len({item['cid'] for item in items}), 'effects': len(items),
            'answers': len(answers), 'exclusions': len(exclusions),
            'by_model': {model: sum(1 for item in items if item['model'] == model)
                         for model in sorted({target['model'] for target in spec.targets})},
        },
        'limits': [
            '候选实现，未接共享card_page_data.py；正式pages/rules/ledger未改，未运行全库生成。',
            'numeric=确认仅指原值与既有规则体；association=推断，runtime_verified=False。',
            '没有新原生执行或实机；静态选择器补证不证明运行时装载、缓存新鲜度、最终扣血或命中。',
            '同记录多父与同值异记录按条件模型合记披露，不重复计答案；旧候选父不计新增。',
            '其它pattern、denju、句外强化、自身受伤、回复、异常、增益与周期效果不并入。',
        ],
    }
    excluded_doc = {
        'schema': 'c20-direct-damage-exclusions-1', 'candidate_only': True,
        'scope': spec.scope, 'items': exclusions,
        'counts': {'items': len(exclusions)},
    }
    return candidate, excluded_doc


def write_outputs(root, spec):
    root = Path(root).resolve()
    out = write_path(root / spec.out_dir, root=root)
    out.mkdir(parents=True, exist_ok=True)
    candidate, exclusions = build_candidates(root, spec)
    cpath, epath = out / 'candidates.json', out / 'exclusions.json'
    cpath.write_bytes(json_dump(candidate).encode('utf-8'))
    epath.write_bytes(json_dump(exclusions).encode('utf-8'))
    record = {
        'schema': 'c20-direct-damage-run-record-1', 'module': spec.module_version,
        'module_sha256': candidate['module_sha256'],
        'common_module_sha256': candidate['common_module_sha256'],
        'scope': spec.scope, 'generated_at_utc': datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat(),
        'command': './.venv/Scripts/python.exe -X utf8 -I -B %s --write' % spec.module_file,
        'baseline': candidate['baseline'], 'counts': candidate['counts'],
        'outputs': {
            'candidates_sha256': sha256_file(cpath), 'exclusions_sha256': sha256_file(epath),
        },
        'limits': candidate['limits'],
    }
    rpath = out / 'run_record.json'
    rpath.write_bytes(json_dump(record).encode('utf-8'))
    return {'counts': candidate['counts'],
            'outputs': {'candidates': str(cpath), 'exclusions': str(epath), 'run_record': str(rpath)}}


def main(spec, argv=None):
    parser = argparse.ArgumentParser(description=spec.scope + ' 候选构建')
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    result = (write_outputs(args.root, spec) if args.write else
              {'counts': build_candidates(args.root, spec)[0]['counts'], 'scope': spec.scope})
    print(json.dumps(result, ensure_ascii=args.json is False, indent=1))
    return 0
