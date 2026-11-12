# -*- coding: utf-8 -*-
"""C21-P1：special_move patternN 直接多段／大伤害候选（未接共享生产入口）。

范围
----
766 行／517 卡；CACHE 259／APK 507；含 Y.G. 超共鸣直接伤害 10 项。身份由
``scripts/character_skills/c21_freeze_direct_damage.py`` 从当前正式来源重导并冻结在
``scripts/character_skills/c21_direct_damage_targets.json``；本模块只按 ``model == DIRECT``
读取 cid／row_id／effect_id／layer／reference_field，**不保存也不读取预筛 raw**。

逐行判定、载体选择、答案构建与内存接线复用既有的
``card_page_inference_c20_direct_damage_common``（RawView／resolve_row／select_carrier／
build_answer／apply_to_groups）。每个答案保留完整父集合、``current_parent``（描述来源父）、
``selected``（答案分支父）、children、raw、来源指针、合并／排除分支与理由。

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
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_SCRIPTS = _HERE.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from project_layout_paths import write_path

import card_page_inference_c20_direct_damage_common as C20

MODULE_VERSION = 'c21_p1_special_direct_20261111'
SCOPE = 'C21_P1_SPECIAL_DIRECT_20261111'
BINDING_KEY = 'c21_p1_special_direct_binding'
MARKER_KEY = 'inference_c21_p1_special_direct'
OUT_DIR_REL = 'output/character_skills/c21_p1_special_direct_20261111'
MODULE_REL = 'scripts/character_skills/card_page_inference_c21_p1_special_direct.py'
TARGETS_REL = 'scripts/character_skills/c21_direct_damage_targets.json'
FREEZE_SCHEMA = 'c21-direct-damage-targets-1'
P1_MODEL = 'DIRECT'
IDENTITY_KEYS = ('cid', 'row_id', 'effect_id', 'layer', 'reference_field', 'model')
ScopeError = C20.ScopeError
NEGATIVE_CIDS = (30207, 278)
PROTECTED_CIDS = (30102, 20234, 30236, 30239)

_SPEC_CACHE = {}
_FREEZE_CACHE = {}


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
                 if target.get('model') == P1_MODEL)


def spec_for(root):
    key = str(Path(root).resolve())
    if key not in _SPEC_CACHE:
        doc = load_freeze(root)
        if doc.get('scope_p1') != SCOPE:
            raise ValueError('冻结配置 P1 scope 不符：%r' % doc.get('scope_p1'))
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
TARGET_CIDS = frozenset(C20.target_cids(spec_for(Path(__file__).resolve().parents[2])))
TARGET_ROW_IDS = {cid: frozenset(t['row_id'] for t in TARGETS if t['cid'] == cid)
                  for cid in sorted(TARGET_CIDS)}


def evaluate(data, cid, row, *, scope=None, skill=None):
    return C20.evaluate(data, cid, row, scope=scope, skill=skill,
                        spec=spec_for(_root_of(data)))


def apply_to_groups(data, cid, groups, *, scope=None):
    return C20.apply_to_groups(data, cid, groups, scope=scope,
                               spec=spec_for(_root_of(data)))


def _children(view, layer, pattern):
    slots = [slot for slot in range(7) if pattern.get('skillid%d' % slot)]
    if slots != list(range(len(slots))):
        raise ValueError('CHILD_SLOTS_NOT_CONTIGUOUS:%r' % slots)
    children = []
    for slot in slots:
        record_id = pattern.get('skillid%d' % slot)
        record, index, hits = view.skill(layer, record_id)
        if record is None:
            raise ValueError('CHILD_RECORD_NOT_UNIQUE:%s:%d' % (record_id, hits))
        children.append({'child_slot': slot, 'record_id': record_id, 'index': index,
                         'type': record.get('skillid0'), 'record': record})
    return children


def _first_diff(left, right, width=24):
    """首个差异位置与两侧片段（不做规范化，便于审查 literal 换行／转义差异）。"""
    left, right = str(left or ''), str(right or '')
    limit = min(len(left), len(right))
    index = next((i for i in range(limit) if left[i] != right[i]), limit)
    return {'first_diff_index': index, 'left_len': len(left), 'right_len': len(right),
            'left_slice': left[index:index + width],
            'right_slice': right[index:index + width]}


def _carrier_gate(view, layer, cid, skill, row):
    """Replay the freeze gates for an excluded row; return (code, detail)."""
    reference = row.get('reference_field') or ''
    if reference == 'skilltext':
        return 'SKILLTEXT_MIRROR_NOT_IN_SCOPE', 'skilltext 行不是 pattern 引用；非唯一镜像不纳入'
    if not C20.PATTERN_REF_RX.match(reference):
        return 'NOT_PATTERN_REFERENCE', reference or skill.get('reference_field')
    form, detail = C20.classify_clause(row.get('japanese'))
    if form == 'SMALL':
        return 'SMALL_DAMAGE_NOT_ADMITTED', detail
    if form == 'INTERVAL':
        return 'INTERVAL_DAMAGE_NOT_ADMITTED', detail
    if form == 'PLAIN':
        return 'PLAIN_DAMAGE_NOT_ADMITTED', detail
    if form not in ('MULTIHIT', 'BIGMID'):
        return 'CLAUSE_NOT_DAMAGE_INSTANCE', detail
    pattern_id = skill.get('record_id')
    chara, _chara_index, _hits = view.charainfo(layer, cid)
    if chara is None:
        return 'CHARAINFO_NOT_UNIQUE', None
    if chara.get(reference) != pattern_id:
        return 'CHARAINFO_LINK_MISMATCH', None
    pattern, pattern_index, _hits = view.pattern(layer, pattern_id)
    if pattern is None:
        return 'PATTERN_NOT_UNIQUE', None
    source = row.get('source') or {}
    pointer = '%s/%d' % (C20.source_prefix(layer, 'bosspattern'), pattern_index)
    if source.get('json_pointer') != pointer:
        return 'ROW_SOURCE_MISMATCH', None
    if C20.canon(pattern.get('sinfo')) != C20.canon(row.get('context_text')):
        return 'TEXT_MISMATCH', _first_diff(pattern.get('sinfo'), row.get('context_text'))
    japanese = str(row.get('japanese') or '')
    if not japanese or str(pattern.get('sinfo') or '').count(japanese) != 1:
        return 'FRAGMENT_NOT_UNIQUE', None
    try:
        children = _children(view, layer, pattern)
        selected = C20.select_carrier(
            view, {'form': form, 'form_detail': detail, 'layer': layer,
                   'target': {'model': P1_MODEL}},
            {'pattern_id': pattern_id, 'children': children, 'record': pattern,
             'reference_field': reference, 'index': pattern_index})
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return 'CARRIER_GATE_FAILED', str(exc)
    same = [answer for answer in row.get('answers') or []
            if answer.get('rule_key') == selected['rule_key']]
    if same:
        return 'EXISTING_SAME_RULE_ANSWER', selected['rule_key']
    return 'OUT_OF_FROZEN_SCOPE_UNCLASSIFIED', selected['rule_key']


def _enrich_exclusions(root, spec, exclusions):
    """把 special_move 非目标伤害行的排除原因细化为实际门失败原因。"""
    import effect_ledger as LEDGER
    view = C20.RawView(root)
    cache = {}
    for item in exclusions:
        if item.get('category') != 'OTHER_PATTERN_ROW':
            continue
        cid, row_id = item.get('cid'), item.get('row_id')
        key = (cid, row_id)
        if key not in cache:
            found = [(skill, row) for _g, skill, row in C20.iter_rows(view.card(cid))
                     if row.get('row_id') == row_id]
            if len(found) != 1:
                cache[key] = None
            else:
                skill, row = found[0]
                analysis = LEDGER.analyze_row(row, table='bosspattern')
                damage = [effect for effect in analysis.get('effects') or []
                          if effect.get('record_type') == 'effect'
                          and effect.get('effect_type') == 'ダメージ（词表外）']
                cache[key] = (skill, row, damage)
        cached = cache[key]
        if cached is None:
            continue
        skill, row, damage = cached
        unresolved = [effect for effect in damage if effect.get('status') == 'unresolved']
        item['damage_effects'] = len(damage)
        item['unresolved_damage_effects'] = len(unresolved)
        item['effect_statuses'] = sorted({effect.get('status') for effect in damage})
        if not unresolved:
            item['reason_code'] = 'DAMAGE_ROW_ALREADY_ANSWERED_OR_NOT_UNRESOLVED'
            item['reason'] = ('该 special_move 伤害行的主伤害效果已有答案或并非未解，'
                              '本批不重复新增；同句其它效果保持原状')
            continue
        if len(unresolved) != 1:
            item['reason_code'] = 'DAMAGE_EFFECT_NOT_SINGLE'
            item['reason'] = '该行未解伤害效果不是恰一个，无法唯一绑定，本批不取'
            continue
        code, detail = _carrier_gate(view, item.get('layer') or skill.get('layer'),
                                     cid, skill, row)
        item['gate_code'] = code
        if detail is not None:
            item['gate_detail'] = detail
        if code == 'EXISTING_SAME_RULE_ANSWER':
            item['reason_code'] = code
            item['reason'] = '本行已有同 rule_key 旧答案，本批不新增、不改写'
        elif code == 'CARRIER_GATE_FAILED':
            item['reason_code'] = code
            item['reason'] = ('同名伤害句的载体类型／skillparam6／规则槽无法唯一选定，'
                              '本批不按值任取')
        elif code == 'OUT_OF_FROZEN_SCOPE_UNCLASSIFIED':
            item['reason_code'] = code
            item['reason'] = '未命中冻结身份但门未给出原因：必须复核，不得静默略过'
        else:
            item['reason_code'] = code
            item['reason'] = '冻结门不通过（%s），本批不取' % code
    return exclusions


def build_candidates(root):
    root = Path(root).resolve()
    spec = spec_for(root)
    candidate, excluded_doc = C20.build_candidates(root, spec)
    doc = load_freeze(root)
    p2_rows = {target['row_id'] for target in doc['targets']
               if str(target.get('model', '')).startswith('DENJU_')}
    for item in excluded_doc['items']:
        if item.get('row_id') in p2_rows:
            item['reason_code'] = 'P2_DENJU_SCOPE_COVERED'
            item['reason'] = '该 denju 行由 C21-P2 denju 批次单独处理，P1 不复制其答案'
    _enrich_exclusions(root, spec, excluded_doc['items'])
    candidate['schema'] = 'c21-p1-special-direct-candidates-1'
    candidate['batch'] = 'P1'
    candidate['scope'] = SCOPE
    candidate['freeze'] = {
        'path': TARGETS_REL,
        'sha256': C20.sha256_file(root / TARGETS_REL),
        'schema': doc.get('schema'),
        'counts': doc.get('counts'),
        'identity_only': True,
    }
    candidate['counts']['freeze_targets'] = len(spec.targets)
    candidate['counts']['by_reason'] = dict(sorted(
        _reason_counts(excluded_doc['items']).items()))
    candidate['limits'] = [
        '候选实现，未接共享 card_page_data.py；正式 pages/rules/ledger 未改，未运行全库生成。',
        '身份来自 C21 冻结配置（只含 cid/row_id/effect_id/layer/reference_field/model），'
        'raw、记录 ID、下标、指针、span 在运行时从当前 CACHE/APK 原表重导。',
        'numeric=确认仅指原值与既有规则体；association=推断，runtime_verified=False。',
        '没有新原生执行或实机；静态选择器补证不证明运行时装载、缓存新鲜度、最终扣血或命中。',
        '句面 N回 ↔ skillparam6、大／中 ↔ 单发型是类型语义＋一致性推断；'
        '同型多记录、反響、随机／周期／召唤、屏障、回复、增益、异常不并入。',
        '保护卡 30102／20234／30236／30239 零触碰；Y.G. 超共鸣 10 项在本批内。',
        'denju 行由 P2 单独处理；本批 exclusions 只登记不复制。',
    ]
    excluded_doc['schema'] = 'c21-p1-special-direct-exclusions-1'
    excluded_doc['batch'] = 'P1'
    excluded_doc['policy'] = (
        '逐一登记本批候选宇宙内被排除的行；排除不等于“无效果”，只表示本批不产出答案。'
        '已答／非未解伤害行、同型多记录、非目标 special_move 行与 denju 行均保持原状。')
    excluded_doc['counts'] = {'items': len(excluded_doc['items']),
                              'by_reason': dict(sorted(
                                  _reason_counts(excluded_doc['items']).items()))}
    return candidate, excluded_doc


def write_outputs(root):
    root = Path(root).resolve()
    out = write_path(root / OUT_DIR_REL, root=root)
    out.mkdir(parents=True, exist_ok=True)
    candidate, exclusions = build_candidates(root)
    cpath, epath = out / 'candidates.json', out / 'exclusions.json'
    cpath.write_bytes(C20.json_dump(candidate).encode('utf-8'))
    epath.write_bytes(C20.json_dump(exclusions).encode('utf-8'))
    record = {
        'schema': 'c21-p1-special-direct-run-record-1',
        'module': MODULE_VERSION, 'scope': SCOPE,
        'module_sha256': C20.sha256_file(root / MODULE_REL),
        'common_module_path': 'scripts/character_skills/'
                              'card_page_inference_c20_direct_damage_common.py',
        'common_module_sha256': C20.sha256_file(
            root / 'scripts/character_skills/card_page_inference_c20_direct_damage_common.py'),
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


def _reason_counts(items):
    out = {}
    for item in items:
        code = item.get('reason_code') or 'UNKNOWN'
        out[code] = out.get(code, 0) + 1
    return out


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
        print('C21-P1: targets=%s resolved=%s answers=%s cids=%s exclusions=%s'
              % (counts.get('target_rows'), counts.get('resolved_rows'),
                 counts.get('answers'), counts.get('cids'), counts.get('exclusions')))
        for key, value in (result.get('outputs') or {}).items():
            print('%s: %s' % (key, value))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
