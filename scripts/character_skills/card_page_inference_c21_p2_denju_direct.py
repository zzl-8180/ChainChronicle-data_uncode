# -*- coding: utf-8 -*-
"""C21-P2：denju 全文一致直接链与唯一条件镜像候选（未接共享生产入口）。

范围
----
134 项／107 卡，全部 CACHE：133 项 ``DENJU_DIRECT``（``denju.stext`` 与 ``pattern.sinfo``
**逐字相等**）＋ CID30304 一项 ``DENJU_CONDITION_MIRROR``（denju 全文与 pattern 全文不相等，
但首句逐字一致且当前片段即首句）。身份由 ``c21_freeze_direct_damage.py`` 冻结在
``c21_direct_damage_targets.json``；本模块不保存预筛 raw。

解析与答案
----------
自建 ``DenjuView``（继承 C20 ``RawView``，只追加 CACHE ``denju`` 表及 decode_report 哈希核对）
与 denju 链 resolver；答案构建复用 ``card_page_inference_c20_direct_damage_common.build_answer``。
完整父集合＝``denju.patternid0..6`` 全部非空引用解引用的 pattern；``current_parent`` 是描述
来源父（patternid0），``selected`` 是答案分支父（唯一子记录），children／raw／来源指针／
合并与排除理由逐项保留。

边界
----
``numeric_evidence=确认`` 只指原值＋既有规则体；``association_evidence=推断``、
``binding=inferred``、``runtime_verified=False``。局部伤害输入不等于最终扣血、保证命中或
运行时选档。保护卡 30102／20234／30236／30239 零触碰；候选未接 card_page_data.py。
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import sys
import weakref
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_SCRIPTS = _HERE.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from project_layout_paths import write_path

import card_page_inference_c20_direct_damage_common as C20

MODULE_VERSION = 'c21_p2_denju_direct_20261111'
SCOPE = 'C21_P2_DENJU_DIRECT_20261111'
BINDING_KEY = 'c21_p2_denju_direct_binding'
MARKER_KEY = 'inference_c21_p2_denju_direct'
OUT_DIR_REL = 'output/character_skills/c21_p2_denju_direct_20261111'
MODULE_REL = 'scripts/character_skills/card_page_inference_c21_p2_denju_direct.py'
TARGETS_REL = 'scripts/character_skills/c21_direct_damage_targets.json'
FREEZE_SCHEMA = 'c21-direct-damage-targets-1'
DIRECT_MODEL = 'DENJU_DIRECT'
MIRROR_MODEL = 'DENJU_CONDITION_MIRROR'
DENJU_MODELS = (DIRECT_MODEL, MIRROR_MODEL)
DENJU_REFERENCE = 'denju.denju_id == cid'
DENJU_FILE = 'denju.data5.json.raw'
DENJU_SOURCE_KEY = 'CACHE/denju.data5.json.raw'
PATTERN_REF_RX = C20.PATTERN_REF_RX
MIRROR_CID = 30304
MIRROR_PATTERN_ID = 43030403
MIRROR_RECORD_ID = 43030400
MIRROR_TYPE = 22
MIRROR_SLOT = 'skillparam1'
IDENTITY_KEYS = ('cid', 'row_id', 'effect_id', 'layer', 'reference_field', 'model')
ScopeError = C20.ScopeError
NEGATIVE_CIDS = (30207, 278)
PROTECTED_CIDS = (30102, 20234, 30236, 30239)

_SPEC_CACHE = {}
_FREEZE_CACHE = {}
_VIEW_CACHE = weakref.WeakKeyDictionary()


class DenjuView(C20.RawView):
    """真实 Inputs 的只读视图；在 C20 RawView 之上追加 CACHE ``denju`` 表。"""

    def __init__(self, root, decoded=None, rules=None):
        super().__init__(root, decoded=decoded, rules=rules)
        self._load_denju()

    def _load_denju(self):
        snapshot = self.decoded.parent
        report = json.loads((snapshot / 'decode_report.json').read_text(encoding='utf-8-sig'))
        declared = {item.get('filename'): item.get('json_raw_sha256')
                    for item in report.get('files') or []}
        path = self.decoded / DENJU_FILE
        actual = C20.sha256_file(path)
        want = declared.get('denju.data5')
        if want != actual:
            raise ValueError('denju 输入哈希与 decode_report 不符：%s' % path)
        self.denju_docs = json.loads(path.read_text(encoding='utf-8-sig'))['denju']
        self.denju_index = {}
        for index, record in enumerate(self.denju_docs):
            self.denju_index.setdefault(record.get('denju_id'), []).append(index)
        self.versions['CACHE/denju'] = {
            'path': C20.CACHE_DECODED + '/' + DENJU_FILE,
            'declared_sha256': want, 'actual_sha256': actual,
        }

    def unique_denju(self, denju_id):
        hits = self.denju_index.get(denju_id) or []
        if len(hits) != 1:
            return None, None, len(hits)
        return self.denju_docs[hits[0]], hits[0], 1


def view_for(data):
    if isinstance(data, DenjuView):
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
    view = DenjuView(root, decoded=getattr(data, 'decoded', None),
                     rules=getattr(data, 'rule_metadata', None))
    try:
        _VIEW_CACHE[data] = view
    except TypeError:
        pass
    return view


def load_freeze(root):
    path = Path(root).resolve() / TARGETS_REL
    key = str(path)
    if key not in _FREEZE_CACHE:
        doc = json.loads(path.read_text(encoding='utf-8-sig'))
        if doc.get('schema') != FREEZE_SCHEMA or not doc.get('identity_only'):
            raise ValueError('冻结配置不是 C21 身份配置：%s' % path)
        for target in doc.get('targets') or []:
            if set(target) != set(IDENTITY_KEYS):
                raise ValueError('冻结身份键不符：%r' % sorted(target))
        _FREEZE_CACHE[key] = doc
    return _FREEZE_CACHE[key]


def targets_for(root):
    doc = load_freeze(root)
    return tuple(dict(target) for target in doc['targets']
                 if target.get('model') in DENJU_MODELS)


def spec_for(root):
    key = str(Path(root).resolve())
    if key not in _SPEC_CACHE:
        doc = load_freeze(root)
        if doc.get('scope_p2') != SCOPE:
            raise ValueError('冻结配置 P2 scope 不符：%r' % doc.get('scope_p2'))
        _SPEC_CACHE[key] = C20.BatchSpec(
            scope=SCOPE, module_version=MODULE_VERSION, binding_key=BINDING_KEY,
            marker_key=MARKER_KEY, module_file=MODULE_REL, out_dir=OUT_DIR_REL,
            targets=targets_for(root))
    return _SPEC_CACHE[key]


def _root_of(data):
    root = getattr(data, 'root', None)
    if root is None:
        raise TypeError('需要带 root 的真实 card_page_data.Inputs 或 RawView')
    return Path(root).resolve()


TARGETS = targets_for(Path(__file__).resolve().parents[2])
TARGET_CIDS = frozenset(target['cid'] for target in TARGETS)
TARGET_ROW_IDS = {cid: frozenset(t['row_id'] for t in TARGETS if t['cid'] == cid)
                  for cid in sorted(TARGET_CIDS)}
MIRROR_TARGETS = tuple(target for target in TARGETS
                       if target['model'] == MIRROR_MODEL)
MIRROR_ROW_IDS = frozenset(target['row_id'] for target in MIRROR_TARGETS)


def target_map(root):
    return {target['row_id']: target for target in spec_for(root).targets}


def _reject(reason, **detail):
    return {'status': 'REJECTED', 'reason': reason, 'answers': [], 'detail': detail}


def _children(view, pattern):
    slots = [slot for slot in range(7) if pattern.get('skillid%d' % slot)]
    if slots != list(range(len(slots))):
        raise ValueError('CHILD_SLOTS_NOT_CONTIGUOUS:%r' % slots)
    children = []
    for slot in slots:
        record_id = pattern.get('skillid%d' % slot)
        record, index, hits = view.skill('CACHE', record_id)
        if record is None:
            raise ValueError('CHILD_RECORD_NOT_UNIQUE:%s:%d' % (record_id, hits))
        children.append({'child_slot': slot, 'record_id': record_id, 'index': index,
                         'type': record.get('skillid0'), 'record': record})
    return children


def _first_sentence(text):
    return str(text or '').split('。')[0] + '。'


def _sha256_text(text):
    return hashlib.sha256(str(text).encode('utf-8')).hexdigest()


def _existing_same_record_answer(view, cid, row, selected):
    """同卡其它行是否已有同 rule_key＋同记录＋同原值答案（条件镜像的必要补证）。"""
    hits = []
    for _group, _skill, other in C20.iter_rows(view.card(cid)):
        if other.get('row_id') == row.get('row_id'):
            continue
        for answer in other.get('answers') or []:
            if (answer.get('rule_key') == selected['rule_key']
                    and answer.get('record_id') == selected['record_id']
                    and answer.get('raw_value') == selected['raw']):
                hits.append({'row_id': other.get('row_id'),
                             'field_path': answer.get('field_path'),
                             'group': _group.get('group')})
    return hits


def _parents(view, record, fragment_pointer):
    """denju.patternid0..6 的完整父集合（全部非空引用逐条解引用）。"""
    parents = []
    keys = sorted((key for key in record
                   if PATTERN_REF_RX.match(key.replace('patternid', 'pattern'))
                   and record.get(key)),
                  key=lambda key: int(key[9:]))
    for key in keys:
        pattern_id = record.get(key)
        pattern, index, hits = view.pattern('CACHE', pattern_id)
        if pattern is None:
            raise ValueError('PARENT_PATTERN_NOT_UNIQUE:%s:%s:%d' % (key, pattern_id, hits))
        parents.append({'reference_field': key, 'pattern_id': pattern_id, 'index': index,
                        'json_pointer': '%s/%d' % (
                            C20.source_prefix('CACHE', 'bosspattern'), index),
                        'record': pattern, 'children': _children(view, pattern)})
    if not parents:
        raise ValueError('DENJU_PATTERN_SET_EMPTY')
    return parents


def resolve_row(data, spec, cid, row, skill):
    target = target_map(_root_of(data)).get(row.get('row_id'))
    if target is None:
        return _reject('ROW_NOT_IN_FROZEN_SCOPE', row_id=row.get('row_id'))
    if cid != target['cid'] or row.get('cid') not in (None, cid):
        return _reject('CID_MISMATCH', cid=cid, row_cid=row.get('cid'))
    if cid in spec.protected_cids:
        return _reject('ZERO_TOUCH_CID')
    if (row.get('group') or skill.get('original_group')) != 'denju':
        return _reject('ROW_NOT_DENJU')
    if row.get('reference_field') != DENJU_REFERENCE \
            or skill.get('reference_field') != DENJU_REFERENCE:
        return _reject('REFERENCE_FIELD_MISMATCH')
    if skill.get('table') != 'denju' or skill.get('layer') != 'CACHE':
        return _reject('SKILL_SOURCE_MISMATCH',
                       table=skill.get('table'), layer=skill.get('layer'))
    if skill.get('record_id') != cid:
        return _reject('PAGE_RECORD_ID_MISMATCH', record_id=skill.get('record_id'))
    record, denju_index, hits = data.unique_denju(cid)
    if record is None:
        return _reject('DENJU_RECORD_NOT_UNIQUE', hits=hits)
    stext = str(record.get('stext') or '')
    if not stext:
        return _reject('DENJU_STEXT_MISSING')
    pattern_id = record.get('patternid0')
    if not pattern_id:
        return _reject('PATTERNID0_MISSING')
    source = row.get('source') or {}
    pointer = '/denju/%d' % denju_index
    if source.get('layer') != 'CACHE' or source.get('source_key') != DENJU_SOURCE_KEY:
        return _reject('ROW_SOURCE_LAYER_MISMATCH', layer=source.get('layer'),
                       source_key=source.get('source_key'))
    if source.get('json_pointer') != pointer:
        return _reject('ROW_SOURCE_POINTER_MISMATCH', want=pointer,
                       got=source.get('json_pointer'))
    if source.get('field_json_pointer') not in (None, pointer + '/stext'):
        return _reject('ROW_SOURCE_FIELD_POINTER_MISMATCH',
                       got=source.get('field_json_pointer'))
    if source.get('field') not in (None, '/stext'):
        return _reject('ROW_SOURCE_FIELD_MISMATCH', got=source.get('field'))
    if C20.canon(row.get('context_text')) != C20.canon(stext):
        return _reject('CONTEXT_TEXT_MISMATCH')
    if C20.canon(skill.get('original_text')) != C20.canon(stext):
        return _reject('SKILL_ORIGINAL_TEXT_MISMATCH')
    japanese = str(row.get('japanese') or '')
    if not japanese or stext.count(japanese) != 1:
        return _reject('FRAGMENT_SPAN_NOT_UNIQUE', count=stext.count(japanese))
    try:
        parents = _parents(data, record, pointer + '/stext')
    except ValueError as exc:
        return _reject('PARENT_GATE_FAILED', error=str(exc))
    current = [parent for parent in parents if parent['reference_field'] == 'patternid0']
    if len(current) != 1:
        return _reject('CURRENT_PARENT_NOT_UNIQUE', hits=len(current))
    current = current[0]
    pattern = current['record']
    sinfo = str(pattern.get('sinfo') or '')
    if not sinfo:
        return _reject('PATTERN_SINFO_MISSING')
    analysis = C20.LEDGER.analyze_row(row, table='denju')
    effects = [effect for effect in analysis.get('effects') or []
               if effect.get('record_type') == 'effect'
               and effect.get('effect_id') == target['effect_id']]
    # 幂等：本批答案写入后该效果变为 has_answer；只要效果类型仍是词表外伤害即继续，
    # 由 apply_to_groups 按身份跳过或登记冲突。
    if len(effects) != 1 or effects[0].get('effect_type') != 'ダメージ（词表外）':
        return _reject('TARGET_EFFECT_MISMATCH', effect_id=target['effect_id'],
                       found=[(e.get('effect_id'), e.get('effect_type'), e.get('status'))
                              for e in analysis.get('effects') or []])
    form, form_detail = C20.classify_clause(japanese)
    if form not in ('MULTIHIT', 'BIGMID'):
        return _reject('CLAUSE_FORM_NOT_ADMITTED', form=form, detail=form_detail)
    model = target['model']
    mirror = model == MIRROR_MODEL
    text_facts = {
        'stext_sha256': _sha256_text(stext),
        'sinfo_sha256': _sha256_text(sinfo),
        'full_text_equal': stext == sinfo,
        'canon_full_text_equal': C20.canon(stext) == C20.canon(sinfo),
        'first_sentence_equal': (C20.canon(_first_sentence(stext))
                                 == C20.canon(_first_sentence(sinfo))),
        'fragment_is_first_sentence': (C20.canon(japanese)
                                       == C20.canon(_first_sentence(stext))),
    }
    if not mirror:
        if stext != sinfo:
            return _reject('DENJU_STEXT_NOT_PATTERN_SINFO')
    else:
        if text_facts['canon_full_text_equal'] or not text_facts['first_sentence_equal'] \
                or not text_facts['fragment_is_first_sentence']:
            return _reject('MIRROR_TEXT_GATE_FAILED', facts=text_facts)
    try:
        selected = C20.select_carrier(
            data, {'form': form, 'form_detail': form_detail, 'layer': 'CACHE',
                   'target': {'model': model}}, current)
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return _reject('SOURCE_OR_CONDITION_GATE_FAILED', error=str(exc))
    existing = []
    if mirror:
        if (cid != MIRROR_CID or pattern_id != MIRROR_PATTERN_ID
                or selected['record_id'] != MIRROR_RECORD_ID
                or selected['type'] != MIRROR_TYPE or selected['field'] != MIRROR_SLOT):
            return _reject('MIRROR_IDENTITY_NOT_FROZEN')
        existing = _existing_same_record_answer(data, cid, row, selected)
        if not existing:
            return _reject('MIRROR_EXISTING_SAME_RECORD_ANSWER_MISSING')
    return {
        'status': 'RESOLVED_CONTEXT', 'target': target, 'layer': 'CACHE',
        'denju': record, 'denju_index': denju_index,
        'current_parent': current, 'parents': parents,
        'parent_text': stext, 'japanese': japanese, 'sinfo': sinfo,
        'fragment_span': {'start': stext.find(japanese), 'end': stext.find(japanese)
                          + len(japanese), 'unit': 'char', 'fragment': japanese,
                          'parent_json_pointer': pointer + '/stext',
                          'denju_json_pointer': pointer},
        'analysis': analysis, 'effect': effects[0], 'form': form,
        'form_detail': form_detail, 'model': model, 'mirror': mirror,
        'text_facts': text_facts, 'existing_same_record_answers': existing,
        'page_source': dict(source),
    }


def condition_label(context):
    pattern_id = context['current_parent']['pattern_id']
    if context['mirror']:
        return ('仅当 denju.patternid0 %d 的首句分支被选中时；denju 全文与 pattern 全文'
                '不一致，本项是条件镜像（推断），不是全文一致的直接 denju' % pattern_id)
    return ('denju.patternid0 %d 被选中时；denju.stext 与 pattern.sinfo 逐字一致'
            % pattern_id)


def _answer_spec(selection, condition):
    return {'selection': selection, 'condition_label': condition,
            'related': [selection], 'merged': [], 'excluded': []}


def build_answer(data, spec, context, answer_spec):
    answer = C20.build_answer(data, spec, context, answer_spec)
    selected = answer_spec['selection']
    target = context['target']
    cid = target['cid']
    record = context['denju']
    pointer = '/denju/%d' % context['denju_index']
    chain = ['denju.denju_id=%d' % cid,
             'denju.patternid0=%d' % context['current_parent']['pattern_id'],
             'bosspattern.skillid%d=%d' % (selected['child_slot'], selected['record_id']),
             'bossskill.skillid=%d' % selected['record_id']]
    denju_block = {
        'table': 'denju', 'record_id': cid, 'layer': 'CACHE',
        'denju_index': context['denju_index'], 'json_pointer': pointer,
        'field_json_pointer': pointer + '/stext', 'source_key': DENJU_SOURCE_KEY,
        'patternid0': context['current_parent']['pattern_id'],
        'pattern_index': context['current_parent']['index'],
        'stext_sha256': context['text_facts']['stext_sha256'],
        'sinfo_sha256': context['text_facts']['sinfo_sha256'],
        'full_text_equal': context['text_facts']['full_text_equal'],
        'first_sentence_equal': context['text_facts']['first_sentence_equal'],
    }
    binding_payload = answer['binding'][spec.binding_key]
    binding_payload['denju'] = denju_block
    binding_payload['chain'] = chain
    binding_payload['model'] = context['model']
    if context['mirror']:
        mirror_block = {
            'verdict': 'CONDITION_MIRROR_ONLY',
            'first_sentence': _first_sentence(record.get('stext')),
            'denju_full_text': record.get('stext'),
            'pattern_full_text': context['sinfo'],
            'full_text_equal': False,
            'first_sentence_equal': True,
            'fragment_is_first_sentence': True,
            'existing_same_record_answers': context['existing_same_record_answers'],
            'note': ('首句身份一致；全文不一致（barrier 句被合并／拆分的措辞差异）。'
                     '本项只按条件镜像披露，关联为推断；独审可单独否决，'
                     '严格直接 899 项不依赖本项。'),
        }
        binding_payload['mirror'] = mirror_block
        answer['mirror'] = mirror_block
        answer['condition_label'] = answer_spec['condition_label']
        answer['conditions'].append('条件镜像：denju 全文与 pattern 全文不一致，'
                                    '只在首句身份与同记录同值答案同时成立时披露')
        answer['not_included']['mirror_disclosure'] = (
            'denju 全文与 pattern 全文不完全一致；不得把本项写成直接全文一致项')
        answer['player_text'] += ('本项是条件镜像：传授文本全文与必杀 pattern 全文不一致，'
                                  '只按首句身份与同记录同值旧答案披露，关联为推断。')
        answer['value'] += '（条件镜像：denju 全文与 pattern 全文不一致，仅首句一致）'
    answer['denju'] = denju_block
    answer['chain'] = chain
    answer['denju_text_check'] = dict(context['text_facts'])
    answer['conditions'].append(
        '来源链：denju.patternid0 → bosspattern 第%d槽 → bossskill %s；'
        'denju 行本身没有 skillparam 槽位'
        % (selected['child_slot'], selected['record_id']))
    if context['mirror']:
        answer['player_text'] += ('本项来自传授（denju）链，但传授文本全文与必杀 pattern 全文不一致：'
                                  '只按首句身份与同记录同值旧答案披露，关联为推断。')
    else:
        answer['player_text'] += ('本项来自传授（denju）链：传授文本与 pattern 正文逐字一致，'
                                  '数值取自该链选中的伤害记录。')
    return answer


def select_by_model(data, context):
    selected = C20.select_carrier(
        data, {'form': context['form'], 'form_detail': context['form_detail'],
               'layer': 'CACHE', 'target': {'model': context['model']}},
        context['current_parent'])
    return [_answer_spec(selected, condition_label(context))]


def evaluate(data, cid, row, *, scope=None, skill=None):
    spec = spec_for(_root_of(data))
    C20.require_scope(spec, scope)
    data = view_for(data)
    skill = skill or {}
    try:
        context = resolve_row(data, spec, cid, row, skill)
        if context['status'] == 'REJECTED':
            return context
        answer_specs = select_by_model(data, context)
        answers = [build_answer(data, spec, context, item) for item in answer_specs]
        if len(answers) != 1:
            return _reject('ANSWER_COUNT_MISMATCH', got=len(answers), want=1)
        return {
            'status': 'RESOLVED', 'reason': None, 'answers': answers,
            'target': context['target'], 'context': context,
            'selected': [C20._selection_public(item['selection']) for item in answer_specs],
            'analysis_summary': {
                'baseline_effect_status': context['effect'].get('status'),
                'baseline_split_flags': context['analysis'].get('split_flags'),
                'unresolved_effect_ids': [e.get('effect_id')
                                          for e in context['analysis'].get('effects') or []
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


def apply_to_groups(data, cid, groups, *, scope=None):
    spec = spec_for(_root_of(data))
    C20.require_scope(spec, scope)
    report = {'cid': cid, 'scope': scope, 'module_version': spec.module_version,
              'status': 'OUT_OF_SCOPE', 'rows': [], 'added': 0, 'skipped': 0,
              'conflicts': 0, 'rejected': 0}
    if cid not in C20.target_cids(spec):
        report['detail'] = ('保护卡' if cid in spec.protected_cids
                            else '不在本批冻结作用域')
        return report
    report['status'] = 'APPLIED'
    data = view_for(data)
    wanted = {target['row_id'] for target in spec.targets if target['cid'] == cid}
    for _group, skill, row in C20.iter_rows(groups):
        if row.get('row_id') not in wanted:
            continue
        result = evaluate(data, cid, row, scope=scope, skill=skill)
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
            if any(answer_identity(old, spec) == identity for old in existing):
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
        marker = row.get(MARKER_KEY)
        if to_add and marker is not None and marker.get('scope') != spec.scope:
            entry['conflicts'] = 1
            entry['conflict_detail'] = [{'reason': 'EXISTING_MARKER_SCOPE_CONFLICT'}]
            report['conflicts'] += 1
            report['rows'].append(entry)
            continue
        legacy = row.get('inference_yg1')
        if to_add and legacy is not None and legacy.get('scope') != spec.scope:
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
                       if reason not in C20.STALE_REASONS]
            note = ('%s：本行 denju 直接链主伤害效果已绑定局部伤害输入；'
                    '同句其它效果、句外强化与排除分支仍保留。' % spec.scope)
            if note not in reasons:
                reasons.append(note)
            row['unknown_reasons'] = reasons
            row[MARKER_KEY] = {
                'scope': spec.scope, 'module': spec.module_version,
                'answer_identities': [list(answer_identity(answer, spec))
                                      for answer in to_add],
                'association': '推断', 'runtime_verified': False,
                'mirror': any(answer.get('mirror') for answer in to_add),
            }
            # 账本显式变体绑定：effect_binding 存在时必须由 inference_yg1.pattern_ids 指认，
            # 否则 effect_ledger 不会消费该答案（与 C20 同一机制）。
            legacy = row.get('inference_yg1')
            if legacy is None:
                legacy = {'scope': spec.scope, 'mirror': False, 'pattern_ids': [],
                          'pattern_records': [], 'formula_types': []}
                row['inference_yg1'] = legacy
            for answer in to_add:
                effect_binding = answer['effect_binding']
                pattern_id = effect_binding['pattern_id']
                if pattern_id not in legacy['pattern_ids']:
                    legacy['pattern_ids'].append(pattern_id)
                if answer['quantity_kind'] not in legacy['formula_types']:
                    legacy['formula_types'].append(answer['quantity_kind'])
                legacy['pattern_records'].append({
                    'pattern_id': pattern_id,
                    'child_id': effect_binding['child_id'],
                    'field_path': effect_binding['field_path'],
                    'condition_label': answer['condition_label'],
                    'scope': spec.scope,
                })
                if answer.get('mirror'):
                    legacy['mirror'] = True
        report['rows'].append(entry)
    return report


def _find_row(data, cid, row_id):
    found = [(skill, row) for _group, skill, row in C20.iter_rows(data.card(cid))
             if row.get('row_id') == row_id]
    return found


def _exclusion_reason(view, cid, row, record):
    form, detail = C20.classify_clause(row.get('japanese'))
    if form in ('MULTIHIT', 'BIGMID'):
        gate = 'GATE_NOT_EVALUATED'
        pattern_id = (record or {}).get('patternid0')
        if pattern_id:
            pattern, index, _hits = view.pattern('CACHE', pattern_id)
            if pattern is not None:
                try:
                    children = _children(view, pattern)
                    C20.select_carrier(
                        view, {'form': form, 'form_detail': detail, 'layer': 'CACHE',
                               'target': {'model': DIRECT_MODEL}},
                        {'pattern_id': pattern_id, 'children': children,
                         'record': pattern, 'reference_field': DENJU_REFERENCE,
                         'index': index})
                    gate = 'SELECTABLE'
                except (ValueError, TypeError, KeyError, IndexError) as exc:
                    gate = str(exc)
        if gate != 'SELECTABLE':
            return ('DENJU_DAMAGE_ROW_CARRIER_GATE_FAILED',
                    'denju 伤害行不在冻结表，且载体门不通过（%s）：不得按值任取' % gate)
        return ('DENJU_DAMAGE_ROW_OUTSIDE_FROZEN_SET',
                'denju 伤害行载体可选但不在冻结表：必须复核，不得静默略过')
    if form == 'SMALL':
        return ('DENJU_SMALL_NOT_ADMITTED', '小伤害段不纳入直接多段／大伤害批次')
    if form == 'INTERVAL':
        return ('DENJU_INTERVAL_NOT_ADMITTED', '一定間隔／周期伤害不纳入本批')
    if form == 'PLAIN':
        return ('DENJU_PLAIN_NOT_ADMITTED', '无 N回／大／中限定的伤害句不纳入本批')
    return ('DENJU_NON_DAMAGE_ROW', '非对敌伤害实例（增益／回复／异常／屏障等），不纳入本批')


def _mirror_rejection(view, cid, row, record):
    """非目标行若不是全文一致，检查是否“首句一致的条件镜像候选”，并说明拒绝原因。"""
    stext = str(record.get('stext') or '')
    pattern_id = record.get('patternid0')
    if not stext or not pattern_id:
        return None
    pattern, _index, _hits = view.pattern('CACHE', pattern_id)
    if pattern is None:
        return None
    sinfo = str(pattern.get('sinfo') or '')
    if not sinfo or C20.canon(stext) == C20.canon(sinfo):
        return None
    japanese = str(row.get('japanese') or '')
    if C20.canon(japanese) != C20.canon(_first_sentence(stext)) \
            or C20.canon(_first_sentence(stext)) != C20.canon(_first_sentence(sinfo)):
        return None
    form, detail = C20.classify_clause(japanese)
    try:
        if form not in ('MULTIHIT', 'BIGMID'):
            raise ValueError('CLAUSE_FORM_NOT_ADMITTED:%s' % form)
        children = _children(view, pattern)
        C20.select_carrier(view, {'form': form, 'form_detail': detail, 'layer': 'CACHE',
                                  'target': {'model': MIRROR_MODEL}},
                           {'pattern_id': pattern_id, 'children': children,
                            'record': pattern, 'reference_field': DENJU_REFERENCE,
                            'index': _index})
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return {'reason_code': 'CONDITION_MIRROR_REJECTED',
                'reason': '首句一致但载体／形态门不通过，不作为条件镜像',
                'detail': str(exc)}
    return {'reason_code': 'CONDITION_MIRROR_NOT_FROZEN',
            'reason': '首句一致但不在冻结的唯一镜像身份内',
            'detail': '仅 CID30304 的 patternid0=43030403→43030400 type22 获准'}


def _mirror_universe(data, spec):
    """全库 denju 记录：全文不一致的行逐条登记；证明条件镜像唯一。"""
    targets = {target['row_id']: target for target in spec.targets}
    out = []
    for cid in sorted(data.denju_index):
        hits = data.denju_index.get(cid) or []
        if len(hits) != 1:
            continue
        record = data.denju_docs[hits[0]]
        stext = str(record.get('stext') or '')
        pattern_id = record.get('patternid0')
        if not stext or not pattern_id:
            continue
        pattern, _index, _phits = data.pattern('CACHE', pattern_id)
        if pattern is None:
            continue
        sinfo = str(pattern.get('sinfo') or '')
        if not sinfo or C20.canon(stext) == C20.canon(sinfo):
            continue
        first = _first_sentence(stext)
        first_sinfo = _first_sentence(sinfo)
        rows = [(skill, row) for _g, skill, row in C20.iter_rows(data.card(cid))
                if C20.canon(row.get('japanese')) == C20.canon(first)]
        entry = {'category': 'CONDITION_MIRROR_UNIVERSE', 'cid': cid,
                 'denju_index': hits[0], 'patternid0': pattern_id,
                 'stext_sha256': _sha256_text(stext),
                 'sinfo_sha256': _sha256_text(sinfo),
                 'full_text_equal': False,
                 'first_sentence_equal': C20.canon(first) == C20.canon(first_sinfo),
                 'rows': [row.get('row_id') for _skill, row in rows]}
        if C20.canon(first) != C20.canon(first_sinfo):
            entry.update(reason_code='CONDITION_MIRROR_FIRST_SENTENCE_DIFFERS',
                         accepted=False,
                         reason='denju 首句与 pattern 首句不一致，不构成条件镜像')
            out.append(entry)
            continue
        accepted = [target for _skill, row in rows
                    for target in [targets.get(row.get('row_id'))]
                    if target is not None and target.get('model') == MIRROR_MODEL]
        if accepted:
            entry.update(reason_code='CONDITION_MIRROR_ACCEPTED', accepted=True,
                         reason='唯一冻结镜像：首句一致、全文不一致、同记录同值旧答案存在',
                         row_id=accepted[0]['row_id'])
            out.append(entry)
            continue
        rejection = None
        for skill, row in rows:
            rejection = _mirror_rejection(data, cid, row, record)
            if rejection:
                break
        entry.update(rejection or {
            'reason_code': 'CONDITION_MIRROR_NOT_FROZEN',
            'reason': '首句一致但不在冻结的唯一镜像身份内',
        }, accepted=False)
        out.append(entry)
    return out


def build_candidates(root):
    root = Path(root).resolve()
    spec = spec_for(root)
    data = DenjuView(root)
    doc = load_freeze(root)
    items, exclusions = [], []
    for target in spec.targets:
        cid = target['cid']
        found = _find_row(data, cid, target['row_id'])
        if len(found) != 1:
            exclusions.append({'category': 'TARGET', 'cid': cid,
                               'row_id': target['row_id'],
                               'reason_code': 'TARGET_ROW_NOT_UNIQUE', 'hits': len(found)})
            continue
        skill, row = found[0]
        result = evaluate(data, cid, row, scope=spec.scope, skill=skill)
        if result['status'] != 'RESOLVED':
            exclusions.append({'category': 'TARGET', 'cid': cid, 'row_id': target['row_id'],
                               'effect_id': target['effect_id'],
                               'japanese': row.get('japanese'),
                               'reason_code': result.get('reason'),
                               'detail': result.get('detail')})
            continue
        context = result['context']
        items.append({
            'cid': cid, 'row_id': target['row_id'], 'effect_id': target['effect_id'],
            'layer': target['layer'], 'reference_field': target['reference_field'],
            'model': target['model'], 'mirror': context['mirror'],
            'japanese': row.get('japanese'), 'context_text': row.get('context_text'),
            'fragment_span': context['fragment_span'],
            'page_source': row.get('source'),
            'existing_answers': copy.deepcopy(row.get('answers') or []),
            'baseline_effect': copy.deepcopy(context['effect']),
            'baseline_split_flags': context['analysis'].get('split_flags'),
            'denju_parent': {
                'record_id': cid, 'denju_index': context['denju_index'],
                'json_pointer': '/denju/%d' % context['denju_index'],
                'patternid0': context['current_parent']['pattern_id'],
                'stext_sha256': context['text_facts']['stext_sha256'],
                'sinfo_sha256': context['text_facts']['sinfo_sha256'],
                'full_text_equal': context['text_facts']['full_text_equal'],
                'first_sentence_equal': context['text_facts']['first_sentence_equal'],
            },
            'chain': [parent['reference_field'] + '=' + str(parent['pattern_id'])
                      for parent in context['parents']],
            'complete_parent_set': [C20._parent_public(parent)
                                    for parent in context['parents']],
            'selected': result['selected'], 'answers': result['answers'],
            'analysis_summary': result['analysis_summary'],
        })
    target_rows = {target['row_id'] for target in spec.targets}
    for cid in sorted(C20.target_cids(spec)):
        card = data.card(cid)
        record, _index, _hits = data.unique_denju(cid)
        for group, skill, row in C20.iter_rows(card):
            group_name = group.get('group') or skill.get('original_group')
            if group_name != 'denju':
                continue
            row_id = row.get('row_id')
            if row_id in target_rows:
                continue
            base = {'category': 'DENJU', 'cid': cid, 'row_id': row_id,
                    'japanese': row.get('japanese'),
                    'fragment_index': row.get('fragment_index'),
                    'page_source': row.get('source')}
            mirror = _mirror_rejection(data, cid, row, record) if record else None
            if mirror:
                exclusions.append(dict(base, **mirror))
                continue
            code, reason = _exclusion_reason(data, cid, row, record or {})
            exclusions.append(dict(base, reason_code=code, reason=reason))
    for cid in spec.protected_cids:
        exclusions.append({'category': 'PROTECTED', 'cid': cid,
                           'reason_code': 'ZERO_TOUCH_CID',
                           'reason': '保护卡整卡零触碰'})
    for cid in spec.negative_cids:
        exclusions.append({'category': 'NAMED_NEGATIVE', 'cid': cid,
                           'reason_code': 'EXISTING_ANSWER_OR_UNCLOSED_MECHANISM',
                           'reason': '30207已有正式答案；278动画映射未闭合；本批零新增'})
    answers = [answer for item in items for answer in item['answers']]
    candidate = {
        'schema': 'c21-p2-denju-direct-candidates-1', 'candidate_only': True,
        'batch': 'P2', 'module': spec.module_version,
        'module_path': spec.module_file,
        'module_sha256': C20.sha256_file(root / spec.module_file),
        'common_module_path': 'scripts/character_skills/'
                              'card_page_inference_c20_direct_damage_common.py',
        'common_module_sha256': C20.sha256_file(
            root / 'scripts/character_skills/card_page_inference_c20_direct_damage_common.py'),
        'freeze': {'path': TARGETS_REL, 'sha256': C20.sha256_file(root / TARGETS_REL),
                   'schema': doc.get('schema'), 'counts': doc.get('counts'),
                   'identity_only': True},
        'scope': spec.scope, 'binding_key': spec.binding_key,
        'targets': [dict(target) for target in spec.targets],
        'baseline': C20.baseline_identity(root),
        'inputs': {
            'decoded': data.versions,
            'rules': {'path': C20.RULES_REL,
                      'sha256': C20.sha256_file(data.rules_path),
                      'key_count': len(data.rules)},
            'pages': {str(cid): {'path': C20.PAGES_REL + '/%d/card.json' % cid,
                                 'sha256': data.page_sha256(cid)}
                      for cid in sorted(C20.target_cids(spec))},
        },
        'items': items, 'answers': answers,
        'counts': {
            'target_rows': len(spec.targets), 'resolved_rows': len(items),
            'cids': len({item['cid'] for item in items}), 'effects': len(items),
            'answers': len(answers), 'exclusions': len(exclusions),
            'direct': sum(1 for item in items if not item['mirror']),
            'mirror': sum(1 for item in items if item['mirror']),
            'by_model': {model: sum(1 for item in items if item['model'] == model)
                         for model in sorted({target['model'] for target in spec.targets})},
        },
        'limits': [
            '候选实现，未接共享 card_page_data.py；正式 pages/rules/ledger 未改，未运行全库生成。',
            '133 项严格直接要求 denju.stext 与 pattern.sinfo 逐字相等；CID30304 是唯一'
            '条件镜像（全文不一致、首句一致），独审可单独否决。',
            'numeric=确认仅指原值与既有规则体；association=推断，runtime_verified=False。',
            '没有新原生执行或实机；静态链补证不证明运行时装载、缓存新鲜度、最终扣血或命中。',
            '反響、随机／周期／召唤、屏障、回复、增益、异常与同型多记录不并入；'
            '30102 的 denju 行因保护卡零触碰不纳入。',
        ],
    }
    excluded_doc = {
        'schema': 'c21-p2-denju-direct-exclusions-1', 'candidate_only': True,
        'batch': 'P2', 'scope': spec.scope, 'items': exclusions,
        'mirror_universe': _mirror_universe(data, spec),
        'counts': {'items': len(exclusions),
                   'by_reason': dict(sorted(_reason_counts(exclusions).items()))},
        'policy': ('逐一登记目标卡内未纳入的 denju 行与保护卡／命名反例；排除不等于“无效果”。'
                   '全文不一致的行若首句一致，按条件镜像候选逐条说明拒绝原因。'
                   'mirror_universe 覆盖全库 denju 记录，证明条件镜像唯一。'),
    }
    excluded_doc['counts']['mirror_universe'] = len(excluded_doc['mirror_universe'])
    excluded_doc['counts']['mirror_accepted'] = sum(
        1 for item in excluded_doc['mirror_universe'] if item.get('accepted'))
    return candidate, excluded_doc


def _reason_counts(items):
    out = {}
    for item in items:
        code = item.get('reason_code') or 'UNKNOWN'
        out[code] = out.get(code, 0) + 1
    return out


def write_outputs(root):
    root = Path(root).resolve()
    out = write_path(root / OUT_DIR_REL, root=root)
    out.mkdir(parents=True, exist_ok=True)
    candidate, exclusions = build_candidates(root)
    cpath, epath = out / 'candidates.json', out / 'exclusions.json'
    cpath.write_bytes(C20.json_dump(candidate).encode('utf-8'))
    epath.write_bytes(C20.json_dump(exclusions).encode('utf-8'))
    record = {
        'schema': 'c21-p2-denju-direct-run-record-1',
        'module': MODULE_VERSION, 'scope': SCOPE,
        'module_sha256': C20.sha256_file(root / MODULE_REL),
        'common_module_path': candidate['common_module_path'],
        'common_module_sha256': candidate['common_module_sha256'],
        'freeze_sha256': C20.sha256_file(root / TARGETS_REL),
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat(),
        'command': './.venv/Scripts/python.exe -X utf8 -I -B %s --root . --write' % MODULE_REL,
        'baseline': candidate['baseline'], 'counts': candidate['counts'],
        'outputs': {'candidates_sha256': C20.sha256_file(cpath),
                    'exclusions_sha256': C20.sha256_file(epath)},
        'limits': candidate['limits'],
    }
    rpath = out / 'run_record.json'
    rpath.write_bytes(C20.json_dump(record).encode('utf-8'))
    return {'counts': candidate['counts'],
            'outputs': {'candidates': str(cpath), 'exclusions': str(epath),
                        'run_record': str(rpath)}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=SCOPE + ' 候选构建')
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    if args.write:
        result = write_outputs(args.root)
    else:
        candidate, _exclusions = build_candidates(args.root)
        result = {'counts': candidate['counts'], 'scope': SCOPE}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        counts = result['counts']
        print('C21-P2: targets=%s resolved=%s answers=%s cids=%s direct=%s mirror=%s '
              'exclusions=%s'
              % (counts.get('target_rows'), counts.get('resolved_rows'),
                 counts.get('answers'), counts.get('cids'), counts.get('direct'),
                 counts.get('mirror'), counts.get('exclusions')))
        for key, value in (result.get('outputs') or {}).items():
            print('%s: %s' % (key, value))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
