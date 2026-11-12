# -*- coding: utf-8 -*-
"""C21 两批候选（900 项）的真实消费者独立机器检查。

固定入口::

    ./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/check_c21_candidate.py --root . --write

检查内容
--------
* 独立重读 CACHE／APK 原始 JSON（``json.loads``，不复用生产 RawView）核对 900 条的
  record_id／raw／JSON 指针／记录哈希／有限正数／float32；
* 真实 ``card_page_data.Inputs``＋``build_card`` 构造 518 张目标卡与反例卡，再用
  ``effect_ledger.analyze_row`` 实测答案消费、未消费、split_flags 与两次幂等；
* 完整父集合／current_parent／selected／children、规则重算、效果绑定、来源指针篡改、
  零 raw、既有答案与 scope 冲突原子性、保护卡与命名反例零新增；
* 共享 ``card_page_data.py``／``rules``／``effect_ledger``／正式 pages／账本前后哈希不变。

布局适配（不影响数据，只修既有共享代码里过期的逻辑路径）
--------------------------------------------------------
当前工作树已完成 2026-11-09 布局迁移，但若干既有推断模块仍保存逻辑路径
``output/cache_full_20261015_v3``，且 ``card_page_inference_type8``／
``card_page_inference_cond`` 以 ``Path(__file__).resolve().parents[1]`` 解析 ``scripts/``
证据路径（差一级）。这不是 C21 引入的问题，但会让真实 ``build_card`` 对部分目标卡直接抛错。
检查器在**内存中**把这些过期常量重绑到同一物理快照／正确父目录，逐项登记在
``harness_adaptations``；不写任何共享文件，不改判定逻辑。若逻辑路径仍存在（未迁移布局），
不执行适配。

本检查器只写两个候选目录的 ``check_result.json``；``--write`` 缺省时完全不写盘。
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import math
import sys
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_SCRIPTS = _HERE.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from project_layout_paths import read_path, write_path

CD_SHA = 'bfeaba72c19fd5753b87d4440936610e09e3adefac7ff30f2f66c3fe4c178b32'
RULES_SHA = 'cf9451c6ff47fcfb2707a845a799839b352acc10180c1ebc559f852a93affe67'
CAMPAIGN = '754f04b6f552fc2a993c7c7b1de233fc7d138cbac35497c28ce12478a30f4373'
SNAPSHOT = '754f04b6-cf9451c6ff47fcfb'
FREEZE_SHA = '425450f99d6792d9873b5a73cb08b34e633c6f58366fccb0b2e481b90e008459'
EXPECTED = {
    'total': 900, 'rows': 900, 'cids': 518, 'strict': 899, 'mirror': 1,
    'p1_rows': 766, 'p1_cids': 517, 'p1_cache': 259, 'p1_apk': 507, 'p1_yg': 10,
    'p2_rows': 134, 'p2_cids': 107, 'p2_direct': 133, 'p2_mirror': 1,
}
DECODED = 'output/cache_full_20261015_v3/decoded'
PAGES_REL = 'output/character_skills/pages'
LOGICAL_CACHE = 'output/cache_full_20261015_v3'
CACHE_FILES = {'chara': 'charainfo.data5.json.raw',
               'boss': 'bossinfo.data5.json.raw',
               'denju': 'denju.data5.json.raw'}
APK_CHARA = 'output/base_master/_mdCharacter.json'
APK_BOSS = 'output/base_master/_mdBossInfo.json'


def sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False)
                          .encode('utf-8')).hexdigest()


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def load_json(path):
    return json.loads(read_path(Path(path), root=ROOT).read_text(encoding='utf-8-sig'))


def rows_of(card_or_groups):
    groups = (card_or_groups.get('groups') if isinstance(card_or_groups, dict)
              else card_or_groups)
    return {row['row_id']: (skill, row) for group in groups or []
            for skill in group.get('skills') or [] for row in skill.get('rows') or []}


def row_hash(row):
    return hashlib.sha1(dump(row).encode('utf-8')).hexdigest()


def index_rows(rows, key):
    out = {}
    for i, record in enumerate(rows):
        out.setdefault(record.get(key), []).append(i)
    return out


def adapt_layout(root, report):
    """把既有推断模块里过期的逻辑快照路径重绑到当前物理位置（仅内存）。"""
    physical = str(read_path(root / LOGICAL_CACHE, root=root))
    decoded = str(read_path(root / DECODED, root=root))
    legacy_present = (root / LOGICAL_CACHE).exists()
    report['legacy_logical_path_present'] = legacy_present
    if legacy_present:
        report['applied'] = False
        report['reason'] = '旧逻辑路径仍存在，无需适配'
        return
    changes = []
    for name, module in list(sys.modules.items()):
        if not (name.startswith('card_page_inference_')
                or name in ('common', 'rules', 'skilllist_types')):
            continue
        for attr, value in list(vars(module).items()):
            if isinstance(value, str) and value.startswith(LOGICAL_CACHE):
                replacement = (decoded + value[len(LOGICAL_CACHE + '/decoded'):]
                               if value.startswith(LOGICAL_CACHE + '/decoded')
                               else physical + value[len(LOGICAL_CACHE):])
                setattr(module, attr, replacement)
                changes.append({'module': name, 'attr': attr, 'kind': 'logical_path',
                                'before': value, 'after': replacement})
    for name in ('card_page_inference_type8', 'card_page_inference_cond'):
        module = sys.modules.get(name)
        if module is None:
            continue
        before = getattr(module, '__file__', None)
        after = str(root / 'scripts' / 'character_skills' / (name + '.py'))
        if before != after:
            module.__file__ = after
            changes.append({'module': name, 'attr': '__file__', 'kind': 'evidence_root',
                            'before': before, 'after': after})
    report.update(applied=bool(changes), change_count=len(changes), changes=changes,
                  target_decoded=decoded)
    if changes:
        snapshot_dir = read_path(root / DECODED, root=root).parent
        declared = json.loads((snapshot_dir / 'decode_report.json')
                              .read_text(encoding='utf-8-sig'))
        declared = {item.get('filename'): item.get('json_raw_sha256')
                    for item in declared.get('files') or []}
        report['verified_physical_hashes'] = {
            key: {'expected': declared.get(key + '.data5'), 'actual': sha(read_path(
                root / DECODED / stem, root=root))}
            for key, stem in (('charainfo', 'charainfo.data5.json.raw'),
                              ('bossinfo', 'bossinfo.data5.json.raw'),
                              ('denju', 'denju.data5.json.raw'))}


def main(argv=None):
    parser = argparse.ArgumentParser(description='C21 两批候选独立机器检查')
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    global ROOT
    ROOT = Path(args.root).resolve()

    import card_page_data as D
    import effect_ledger as L
    import rules as RULE
    import card_page_inference_c20_direct_damage_common as C20
    import card_page_inference_c21_p1_special_direct as P1
    import card_page_inference_c21_p2_denju_direct as P2

    started = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    checks = []
    state = {'adapt': {}}

    def run(check_id, fn):
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, {'error': '%s: %s' % (type(exc).__name__, exc),
                                 'traceback': traceback.format_exc()[-4000:]}
        checks.append({'check_id': check_id, 'ok': bool(ok),
                       'detail': detail if isinstance(detail, (dict, list)) else {'value': detail}})
        print(('PASS' if ok else 'FAIL'), check_id, '—',
              json.dumps(detail, ensure_ascii=False, default=str)[:400], flush=True)
        return ok

    freeze = P1.load_freeze(ROOT)
    freeze_targets = freeze['targets']
    p1_targets = [t for t in freeze_targets if t['model'] == 'DIRECT']
    p2_targets = [t for t in freeze_targets if t['model'] != 'DIRECT']
    p1_rows = {t['row_id'] for t in p1_targets}
    p2_rows = {t['row_id'] for t in p2_targets}
    all_target_rows = p1_rows | p2_rows
    target_cids = sorted({t['cid'] for t in freeze_targets})
    extra_cids = sorted(set(P1.PROTECTED_CIDS) | set(P1.NEGATIVE_CIDS))
    pages_dir = read_path(ROOT / PAGES_REL, root=ROOT)
    page_cids = sorted(int(path.name) for path in pages_dir.iterdir()
                       if path.is_dir() and path.name.isdigit())
    other_cid = next(cid for cid in page_cids
                     if cid not in set(target_cids) and cid not in set(extra_cids))
    extra_cids.append(other_cid)
    all_cids = sorted(set(target_cids) | set(extra_cids))

    def c01():
        keys = {'cid', 'row_id', 'effect_id', 'layer', 'reference_field', 'model'}
        bad = [t for t in freeze_targets if set(t) != keys]
        effects = [t['effect_id'] for t in freeze_targets]
        rows = [t['row_id'] for t in freeze_targets]
        models = {m: sum(1 for t in freeze_targets if t['model'] == m)
                  for m in sorted({t['model'] for t in freeze_targets})}
        text = json.dumps(freeze_targets, ensure_ascii=False)
        banned = [token for token in ('raw_value', 'skillparam', 'bossskill/', 'record_id":')
                  if token in text]
        ok = (not bad and not banned and len(effects) == len(set(effects)) == EXPECTED['total']
              and len(rows) == len(set(rows)) == EXPECTED['total']
              and models == {'DENJU_CONDITION_MIRROR': 1, 'DENJU_DIRECT': 133, 'DIRECT': 766}
              and sha(ROOT / 'scripts/character_skills/c21_direct_damage_targets.json')
              == FREEZE_SHA)
        return ok, {'targets': len(freeze_targets), 'models': models,
                    'identity_keys': sorted(keys), 'banned_hits': banned,
                    'freeze_sha256': FREEZE_SHA, 'bad': bad[:5]}
    run('C01_frozen_identity_only_and_hash', c01)

    def c02():
        p1a, e1a = P1.build_candidates(ROOT)
        p1b, e1b = P1.build_candidates(ROOT)
        p2a, e2a = P2.build_candidates(ROOT)
        p2b, e2b = P2.build_candidates(ROOT)
        p1_disk = load_json(ROOT / P1.OUT_DIR_REL / 'candidates.json')
        p2_disk = load_json(ROOT / P2.OUT_DIR_REL / 'candidates.json')
        e1_disk = load_json(ROOT / P1.OUT_DIR_REL / 'exclusions.json')
        e2_disk = load_json(ROOT / P2.OUT_DIR_REL / 'exclusions.json')
        rr1 = load_json(ROOT / P1.OUT_DIR_REL / 'run_record.json')
        rr2 = load_json(ROOT / P2.OUT_DIR_REL / 'run_record.json')
        p1c, p2c = p1a['counts'], p2a['counts']
        ok = (stable(p1a) == stable(p1b) == stable(p1_disk)
              and stable(p2a) == stable(p2b) == stable(p2_disk)
              and stable(e1a) == stable(e1b) == stable(e1_disk)
              and stable(e2a) == stable(e2b) == stable(e2_disk)
              and p1c['target_rows'] == EXPECTED['p1_rows']
              and p1c['answers'] == EXPECTED['p1_rows'] and p1c['cids'] == EXPECTED['p1_cids']
              and p2c['target_rows'] == EXPECTED['p2_rows']
              and p2c['answers'] == EXPECTED['p2_rows'] and p2c['cids'] == EXPECTED['p2_cids']
              and p2c['direct'] == EXPECTED['p2_direct']
              and p2c['mirror'] == EXPECTED['p2_mirror']
              and rr1['outputs']['candidates_sha256'] == sha(ROOT / P1.OUT_DIR_REL / 'candidates.json')
              and rr2['outputs']['candidates_sha256'] == sha(ROOT / P2.OUT_DIR_REL / 'candidates.json'))
        state['p1_candidate'], state['p2_candidate'] = p1a, p2a
        state['p1_exclusions'], state['p2_exclusions'] = e1a, e2a
        return ok, {'p1': p1c, 'p2': p2c, 'deterministic': True}
    run('C02_candidate_determinism_and_counts', c02)

    def c03():
        rules = load_json(ROOT / 'output/character_skills/profiles/rules.json')
        metrics = load_json(ROOT / 'output/character_skills/effect_ledger/metrics.json')
        baseline = state['p1_candidate']['baseline']
        ok = (sha(ROOT / 'scripts/character_skills/card_page_data.py') == CD_SHA
              and sha(ROOT / 'output/character_skills/profiles/rules.json') == RULES_SHA
              and len(rules) == 294
              and baseline['campaign'] == CAMPAIGN
              and baseline['snapshot'] == SNAPSHOT
              and metrics['snapshot']['snapshot_id'] == SNAPSHOT)
        return ok, {'baseline': baseline, 'rules': len(rules),
                    'card_page_data': CD_SHA[:16]}
    run('C03_baseline_versions_and_shared_hashes', c03)

    data = D.Inputs(ROOT, set(all_cids))
    pre_error = None
    try:
        D.build_card(data, 203)
    except Exception as exc:  # noqa: BLE001
        pre_error = '%s: %s' % (type(exc).__name__, exc)
    state['adapt']['pre_adaptation_build_card_203'] = pre_error
    adapt_layout(ROOT, state['adapt'])

    built = {cid: D.build_card(data, cid) for cid in all_cids}
    state['built'] = built
    built_rows = {cid: rows_of(built[cid]) for cid in all_cids}
    state['inputs_attrs_after_build'] = set(vars(data))
    state['inputs_class'] = set(dir(D.Inputs))

    def c04():
        rows_found = {}
        for cid in target_cids:
            rows_found[cid] = built_rows[cid]
        missing = [row_id for row_id in all_target_rows
                   if not any(row_id in rows_found[cid] for cid in target_cids)]
        duplicated = []
        for row_id in all_target_rows:
            hits = [cid for cid in target_cids if row_id in rows_found[cid]]
            if len(hits) != 1:
                duplicated.append({'row_id': row_id, 'cids': hits})
        table = {}
        effects = {}
        for target in freeze_targets:
            skill, row = rows_found[target['cid']][target['row_id']]
            table[target['row_id']] = 'bosspattern' if target['model'] == 'DIRECT' else 'denju'
            analysis = L.analyze_row(row, table=table[target['row_id']])
            effects[target['row_id']] = analysis
        state['baseline_analysis'] = effects
        state['row_table'] = table
        bad = []
        for target in freeze_targets:
            analysis = effects[target['row_id']]
            hits = [e for e in analysis['effects'] if e.get('record_type') == 'effect'
                    and e.get('effect_id') == target['effect_id']]
            if len(hits) != 1 or hits[0].get('effect_type') != 'ダメージ（词表外）' \
                    or hits[0].get('status') != 'unresolved':
                bad.append({'row_id': target['row_id'],
                            'hits': [(e.get('effect_id'), e.get('status'))
                                     for e in analysis['effects']]})
        hashes = state['adapt'].get('verified_physical_hashes') or {}
        hashes_ok = all(item.get('expected') == item.get('actual')
                        for item in hashes.values()) if hashes else True
        return (not missing and not duplicated and not bad and hashes_ok), {
            'cards_built': len(all_cids), 'targets': len(freeze_targets),
            'missing': missing[:10], 'duplicated': duplicated[:10], 'bad': bad[:10],
            'pre_adaptation_build_error': pre_error,
            'adaptation': {'applied': state['adapt'].get('applied'),
                           'changes': state['adapt'].get('change_count'),
                           'legacy_present': state['adapt'].get('legacy_logical_path_present'),
                           'physical_hashes_ok': hashes_ok}}
    state['raw'] = {
        'CACHE': {'chara': None, 'boss': None, 'denju': None},
        'APK': {'chara': None, 'boss': None},
    }
    for key, filename in CACHE_FILES.items():
        doc = load_json(ROOT / DECODED / filename)
        state['raw']['CACHE'][key] = (doc['charainfo'] if key == 'chara'
                                      else doc['bossinfo'] if key == 'boss'
                                      else doc['denju'])
    state['raw']['APK']['chara'] = load_json(ROOT / APK_CHARA)['charainfo']
    state['raw']['APK']['boss'] = load_json(ROOT / APK_BOSS)
    raw_index = {}
    for layer in ('CACHE', 'APK'):
        docs = state['raw'][layer]
        boss = docs['boss']
        raw_index[layer] = {
            'chara_rows': docs['chara'],
            'chara': index_rows(docs['chara'], 'cid'),
            'pattern_rows': boss['bosspattern'],
            'pattern': index_rows(boss['bosspattern'], 'patternid'),
            'skill_rows': boss['bossskill'],
            'skill': index_rows(boss['bossskill'], 'skillid'),
        }
    raw_index['CACHE']['denju_rows'] = state['raw']['CACHE']['denju']
    raw_index['CACHE']['denju'] = index_rows(state['raw']['CACHE']['denju'], 'denju_id')
    state['raw_index'] = raw_index
    run('C04_real_inputs_build_card_all_900', c04)

    answers = [answer for item in state['p1_candidate']['items'] for answer in item['answers']]
    answers += [answer for item in state['p2_candidate']['items'] for answer in item['answers']]
    state['answers'] = answers

    def c05():
        failures, actual = [], {}
        for answer in answers:
            layer = answer['layer']
            source = answer['source']
            index = source['record_index']
            record = raw_index[layer]['skill_rows'][index]
            field = answer['field_path'].lstrip('/')
            target_key = (answer['effect_binding']['row_id'],
                          answer['effect_binding']['pattern_id'], answer['record_id'])
            actual[target_key] = answer['raw_value']
            checks_one = {
                'record_id': record.get('skillid') == answer['record_id'],
                'raw': record.get(field) == answer['raw_value'],
                'pointer': source['json_pointer'] ==
                           (('/bossinfo/bossskill/' if layer == 'CACHE' else '/bossskill/')
                            + str(index)),
                'field_pointer': source['field_json_pointer'] == source['json_pointer'] + '/' + field,
                'raw_hash': source['raw_record_sha256'] == stable(record),
                'source_key': source['source_key'] ==
                              ('CACHE/bossinfo.data5.json.raw' if layer == 'CACHE'
                               else 'APK/_mdBossInfo.json'),
                'table': answer['table'] == 'bossskill',
                'finite': isinstance(answer['raw_value'], (int, float))
                          and not isinstance(answer['raw_value'], bool)
                          and math.isfinite(answer['raw_value']) and answer['raw_value'] > 0,
                'float32': answer['effective_float32'] == C20.f32(answer['raw_value']),
                'field_path': answer['field_path'] == '/' + field,
            }
            if not all(checks_one.values()):
                failures.append({'row': answer['effect_binding']['row_id'],
                                 'record': answer['record_id'],
                                 'failed': [k for k, v in checks_one.items() if not v]})
        return (not failures and len(actual) == EXPECTED['total']), {
            'answers': len(actual), 'failures': failures[:10]}
    run('C05_independent_raw_source_all_900', c05)

    def c06():
        failures = []
        for item in state['p1_candidate']['items']:
            layer = item['layer']
            hits = raw_index[layer]['chara'].get(item['cid']) or []
            if len(hits) != 1:
                failures.append({'row': item['row_id'], 'why': 'charainfo_hits'})
                continue
            chara = raw_index[layer]['chara_rows'][hits[0]]
            actual = [(key, chara[key]) for key in sorted(
                (k for k in chara if k.startswith('pattern') and chara.get(k)),
                key=lambda k: int(k[7:]))]
            candidate = [(p['reference_field'], p['pattern_id'])
                         for p in item['complete_parent_set']]
            if actual != candidate:
                failures.append({'row': item['row_id'], 'why': 'parent_set',
                                 'actual': actual, 'candidate': candidate})
            answer = item['answers'][0]
            nested = answer['binding'][P1.BINDING_KEY]
            if chara.get(item['reference_field']) != nested['current_parent']['pattern_id']:
                failures.append({'row': item['row_id'], 'why': 'current_parent'})
            selected = nested['selected']
            pattern = raw_index[layer]['pattern_rows'][selected['pattern_index']]
            if pattern.get('patternid') != selected['pattern_id'] \
                    or pattern.get('skillid%d' % selected['child_slot']) != answer['record_id']:
                failures.append({'row': item['row_id'], 'why': 'child_link'})
        for item in state['p2_candidate']['items']:
            cid = item['cid']
            hits = raw_index['CACHE']['denju'].get(cid) or []
            if len(hits) != 1:
                failures.append({'row': item['row_id'], 'why': 'denju_hits'})
                continue
            record = raw_index['CACHE']['denju_rows'][hits[0]]
            actual = sorted((key, record[key]) for key in record
                            if key.startswith('patternid') and record.get(key))
            candidate = [(p['reference_field'], p['pattern_id'])
                         for p in item['complete_parent_set']]
            if actual != sorted(candidate):
                failures.append({'row': item['row_id'], 'why': 'denju_parent_set',
                                 'actual': actual, 'candidate': candidate})
            answer = item['answers'][0]
            nested = answer['binding'][P2.BINDING_KEY]
            if record.get('patternid0') != nested['current_parent']['pattern_id']:
                failures.append({'row': item['row_id'], 'why': 'denju_current_parent'})
            selected = nested['selected']
            pattern = raw_index['CACHE']['pattern_rows'][selected['pattern_index']]
            if pattern.get('patternid') != selected['pattern_id'] \
                    or pattern.get('skillid%d' % selected['child_slot']) != answer['record_id']:
                failures.append({'row': item['row_id'], 'why': 'denju_child_link'})
            if hits[0] != item['denju_parent']['denju_index']:
                failures.append({'row': item['row_id'], 'why': 'denju_index'})
        return not failures, {'rows': len(state['p1_candidate']['items'])
                              + len(state['p2_candidate']['items']),
                              'failures': failures[:10]}
    run('C06_complete_parent_sets_and_child_links', c06)

    def c07():
        failures = []
        for item, scope, binding_key in (
                [(i, P1.SCOPE, P1.BINDING_KEY) for i in state['p1_candidate']['items']]
                + [(i, P2.SCOPE, P2.BINDING_KEY) for i in state['p2_candidate']['items']]):
            for answer in item['answers']:
                record = raw_index[answer['layer']]['skill_rows'][answer['source']['record_index']]
                rule = RULE.answer_for('bossskill', record['skillid0'], answer['field_path'],
                                       answer['raw_value'], record,
                                       source_layer=answer['layer'])
                nested = answer['binding'][binding_key]
                expected_span = item['baseline_effect']['span']
                checks_one = {
                    'numeric': answer['numeric_evidence'] == '确认',
                    'association': answer['association_evidence'] == '推断',
                    'status': answer['answer_status'] == (rule.get('answer_status')
                                                          or rule.get('rule_status')
                                                          or 'CONFIRMED_FORMULA_ONLY'),
                    'scope': answer['evidence_scope'] == scope,
                    'inferred': nested['binding'] == 'inferred'
                                and nested['runtime_verified'] is False,
                    'g1': answer['binding']['g1_b1_binding']['scope'] == 'G1_B1_MIRROR_20261029',
                    'effect_span': answer['effect_binding']['span'] == expected_span,
                    'effect_type': answer['effect_binding']['effect_type'] == 'ダメージ（词表外）',
                    'pattern_binding': answer['binding']['pattern_id']
                                       == answer['effect_binding']['pattern_id'],
                    'rule_value': bool(rule) and answer['value'].startswith(rule['value_text']),
                    'not_included': bool(answer['not_included']),
                    'no_page_sha': 'page_sha256' not in answer,
                    'parents': bool(nested['complete_parent_set']) and bool(nested['selected']),
                }
                if not all(checks_one.values()):
                    failures.append({'row': item['row_id'], 'record': answer['record_id'],
                                     'failed': [k for k, v in checks_one.items() if not v]})
        return not failures, {'answers': len(answers), 'failures': failures[:10]}
    run('C07_rule_recompute_evidence_and_effect_bindings', c07)

    snapshot = {}
    for cid in all_cids:
        snapshot[cid] = {row_id: (row_hash(row), copy.deepcopy(row.get('answers') or []))
                         for row_id, (_skill, row) in built_rows[cid].items()}
    state['snapshot'] = snapshot

    p1_reports = {cid: P1.apply_to_groups(data, cid, built[cid]['groups'], scope=P1.SCOPE)
                  for cid in sorted({t['cid'] for t in p1_targets})}
    p2_reports = {cid: P2.apply_to_groups(data, cid, built[cid]['groups'], scope=P2.SCOPE)
                  for cid in sorted({t['cid'] for t in p2_targets})}
    state['p1_reports'], state['p2_reports'] = p1_reports, p2_reports

    def c08():
        added1 = sum(report['added'] for report in p1_reports.values())
        added2 = sum(report['added'] for report in p2_reports.values())
        bad1 = [cid for cid, report in p1_reports.items()
                if report['conflicts'] or report['rejected'] or report['status'] != 'APPLIED']
        bad2 = [cid for cid, report in p2_reports.items()
                if report['conflicts'] or report['rejected'] or report['status'] != 'APPLIED']
        return (added1 == EXPECTED['p1_rows'] and added2 == EXPECTED['p2_rows']
                and not bad1 and not bad2), {
            'p1_added': added1, 'p2_added': added2,
            'p1_bad': bad1[:10], 'p2_bad': bad2[:10]}
    run('C08_first_apply_expected_additions', c08)

    def c09():
        failures, remaining = [], 0
        for item, scope in ([(i, P1.SCOPE) for i in state['p1_candidate']['items']]
                            + [(i, P2.SCOPE) for i in state['p2_candidate']['items']]):
            skill, row = built_rows[item['cid']][item['row_id']]
            before = state['baseline_analysis'][item['row_id']]
            after = L.analyze_row(row, table=state['row_table'][item['row_id']])
            effect = next((e for e in after['effects']
                           if e.get('effect_id') == item['effect_id']), None)
            old_count = len(item['existing_answers'])
            new_refs = [ref for ref in after['answer_refs'] if ref['answer_index'] >= old_count]
            old_unmatched = sum(ref['matched_effect_id'] is None for ref in before['answer_refs'])
            new_unmatched = sum(ref['matched_effect_id'] is None for ref in new_refs)
            checks_one = {
                'effect_has_answer': bool(effect) and effect['status'] == 'has_answer',
                'effect_ref_count': bool(effect) and len(effect['answer_refs']) >= 1,
                'new_ref_count': len(new_refs) == 1,
                'new_unmatched': new_unmatched == 0,
                'new_refs_to_target': all(ref['matched_effect_id'] == item['effect_id']
                                          for ref in new_refs),
                'old_unmatched_unchanged': sum(ref['matched_effect_id'] is None
                                               for ref in after['answer_refs']) == old_unmatched,
                'split_unchanged': dump(after['split_flags']) == dump(before['split_flags']),
            }
            remaining += sum(1 for e in after['effects']
                             if e.get('record_type') == 'effect'
                             and e.get('status') == 'unresolved')
            if not all(checks_one.values()):
                failures.append({'row': item['row_id'],
                                 'failed': [k for k, v in checks_one.items() if not v]})
        return not failures, {'rows': len(state['p1_candidate']['items'])
                              + len(state['p2_candidate']['items']),
                              'remaining_unresolved_effects': remaining,
                              'failures': failures[:10]}
    run('C09_ledger_consumption_no_new_unmatched_or_split', c09)

    after_first = {cid: hashlib.sha1(dump(built[cid]['groups']).encode()).hexdigest()
                   for cid in all_cids}
    second1 = {cid: P1.apply_to_groups(data, cid, built[cid]['groups'], scope=P1.SCOPE)
               for cid in p1_reports}
    second2 = {cid: P2.apply_to_groups(data, cid, built[cid]['groups'], scope=P2.SCOPE)
               for cid in p2_reports}

    def c10():
        added = sum(r['added'] for r in second1.values()) + sum(r['added'] for r in second2.values())
        skipped = (sum(r['skipped'] for r in second1.values())
                   + sum(r['skipped'] for r in second2.values()))
        changed = [cid for cid in all_cids
                   if hashlib.sha1(dump(built[cid]['groups']).encode()).hexdigest()
                   != after_first[cid]]
        return (added == 0 and skipped == EXPECTED['total'] and not changed), {
            'added': added, 'skipped': skipped, 'changed': changed[:10]}
    run('C10_second_apply_zero_and_byte_identical', c10)

    def c11():
        attempts = []

        def reject(label, fn):
            try:
                fn()
            except (P1.ScopeError, P2.ScopeError) as exc:
                attempts.append({'call': label, 'ok': True, 'error': str(exc)})
                return True
            attempts.append({'call': label, 'ok': False})
            return False

        ok = True
        for module, target in ((P1, p1_targets[0]), (P2, p2_targets[0])):
            skill, row = built_rows[target['cid']][target['row_id']]
            before = dump(row)
            ok &= reject(module.MODULE_VERSION + ':evaluate_default',
                         lambda m=module, c=target['cid'], r=row, s=skill:
                         m.evaluate(data, c, r, skill=s))
            ok &= reject(module.MODULE_VERSION + ':evaluate_wrong',
                         lambda m=module, c=target['cid'], r=row, s=skill:
                         m.evaluate(data, c, r, scope='WRONG', skill=s))
            ok &= reject(module.MODULE_VERSION + ':evaluate_empty',
                         lambda m=module, c=target['cid'], r=row, s=skill:
                         m.evaluate(data, c, r, scope='', skill=s))
            ok &= reject(module.MODULE_VERSION + ':apply_default',
                         lambda m=module, c=target['cid']:
                         m.apply_to_groups(data, c, built[c]['groups']))
            ok &= reject(module.MODULE_VERSION + ':apply_wrong',
                         lambda m=module, c=target['cid']:
                         m.apply_to_groups(data, c, built[c]['groups'], scope='WRONG'))
            ok &= reject(module.MODULE_VERSION + ':apply_empty',
                         lambda m=module, c=target['cid']:
                         m.apply_to_groups(data, c, built[c]['groups'], scope=''))
            ok &= dump(row) == before
        return ok, {'attempts': attempts}
    run('C11_scope_hard_reject', c11)

    def c12():
        results = []
        alt1 = next(((cid, skill, row) for cid in target_cids
                     for row_id, (skill, row) in built_rows[cid].items()
                     if row_id not in all_target_rows
                     and (row.get('group') or skill.get('original_group')) == 'special_move'))
        alt2 = next(((cid, skill, row) for cid in target_cids
                     for row_id, (skill, row) in built_rows[cid].items()
                     if row_id not in all_target_rows
                     and (row.get('group') or skill.get('original_group')) == 'denju'))
        for module, (cid, skill, row) in ((P1, alt1), (P2, alt2)):
            result = module.evaluate(data, cid, row, scope=module.SCOPE, skill=skill)
            results.append({'module': module.MODULE_VERSION, 'row': row['row_id'],
                            'status': result['status'], 'reason': result.get('reason')})
        ok = all(r['status'] == 'REJECTED' and r['reason'] == 'ROW_NOT_IN_FROZEN_SCOPE'
                 for r in results)
        return ok, {'results': results}
    run('C12_nonfrozen_row_rejected', c12)

    def c13():
        details, ok = [], True
        for cid in extra_cids:
            before = dump(built[cid]['groups'])
            rep1 = P1.apply_to_groups(data, cid, built[cid]['groups'], scope=P1.SCOPE)
            rep2 = P2.apply_to_groups(data, cid, built[cid]['groups'], scope=P2.SCOPE)
            good = (rep1['status'] == 'OUT_OF_SCOPE' and rep1['added'] == 0
                    and rep2['status'] == 'OUT_OF_SCOPE' and rep2['added'] == 0
                    and dump(built[cid]['groups']) == before)
            ok &= good
            details.append({'cid': cid, 'p1': rep1['status'], 'p2': rep2['status'], 'ok': good})
        return ok, {'cards': details}
    run('C13_negative_protected_and_other_cards_zero', c13)

    def c14():
        failures = []
        for cid in all_cids:
            after = rows_of(built[cid])
            for row_id, (digest, old_answers) in state['snapshot'][cid].items():
                if row_id not in after:
                    failures.append({'cid': cid, 'row': row_id, 'why': 'row_missing'})
                    continue
                new_answers = after[row_id][1].get('answers') or []
                if new_answers[:len(old_answers)] != old_answers:
                    failures.append({'cid': cid, 'row': row_id, 'why': 'old_answer_prefix'})
                if row_id not in all_target_rows and row_hash(after[row_id][1]) != digest:
                    failures.append({'cid': cid, 'row': row_id, 'why': 'non_target_row_changed'})
        return not failures, {'rows': sum(len(v) for v in state['snapshot'].values()),
                              'failures': failures[:10]}
    run('C14_old_answers_prefix_and_non_target_rows', c14)

    def c15():
        failures = []
        for item, module in ([(i, P1) for i in state['p1_candidate']['items']]
                             + [(i, P2) for i in state['p2_candidate']['items']]):
            row = built_rows[item['cid']][item['row_id']][1]
            marker = row.get(module.MARKER_KEY) or {}
            answers_here = [a for a in row['answers']
                            if (a.get('binding') or {}).get(module.BINDING_KEY)]
            identities = marker.get('answer_identities')
            checks_one = {
                'scope': marker.get('scope') == module.SCOPE,
                'identities_list': isinstance(identities, list) and len(identities) == 1
                                   and all(isinstance(x, list) for x in identities),
                'answer_count': len(answers_here) == 1,
                'source_identity': all(a['source']['table'] == 'bossskill'
                                       and a['source']['record_id'] == a['record_id']
                                       and a['source']['layer'] == a['layer']
                                       and a['source']['field_path'] == a['field_path']
                                       for a in answers_here),
                'runtime_verified': marker.get('runtime_verified') is False,
            }
            if module is P2:
                checks_one['mirror_flag'] = (marker.get('mirror') is True) == bool(item['mirror'])
            if not all(checks_one.values()):
                failures.append({'row': item['row_id'],
                                 'failed': [k for k, v in checks_one.items() if not v]})
        return not failures, {'rows': EXPECTED['rows'], 'failures': failures[:10]}
    run('C15_marker_identity_and_source', c15)

    def c16():
        results = []
        for module, target in ((P1, p1_targets[0]), (P2, p2_targets[0])):
            skill, row = built_rows[target['cid']][target['row_id']]
            tampered = copy.deepcopy(row)
            tampered['source'] = dict(tampered.get('source') or {})
            tampered['source']['json_pointer'] = '/invalid/0'
            result = module.evaluate(data, target['cid'], tampered,
                                     scope=module.SCOPE, skill=skill)
            results.append({'module': module.MODULE_VERSION, 'status': result['status'],
                            'reason': result.get('reason')})
        ok = all(r['status'] == 'REJECTED' for r in results)
        return ok, {'results': results}
    run('C16_source_pointer_tamper_rejected', c16)

    def c17():
        details, ok = [], True
        for module, target, conflict_key in (
                (P1, p1_targets[0], 'inference_yg1'),
                (P2, p2_targets[0], P2.MARKER_KEY)):
            cid = target['cid']
            pristine = D.build_card(data, cid)
            groups = copy.deepcopy(pristine['groups'])
            row = rows_of(groups)[target['row_id']][1]
            answer = next(a for item in (state['p1_candidate']['items']
                                         if module is P1 else state['p2_candidate']['items'])
                          if item['row_id'] == target['row_id'] for a in item['answers'])
            row.setdefault('answers', []).append({'rule_key': answer['rule_key'],
                                                  'raw_value': -999, 'record_id': -1,
                                                  'field_path': answer['field_path']})
            before = dump(row)
            rep = module.apply_to_groups(data, cid, groups, scope=module.SCOPE)
            same_rule = (dump(rows_of(groups)[target['row_id']][1]) == before
                         and all(entry['added'] == 0 for entry in rep['rows']
                                 if entry['row_id'] == target['row_id']))
            groups2 = copy.deepcopy(pristine['groups'])
            row2 = rows_of(groups2)[target['row_id']][1]
            row2[conflict_key] = {'scope': 'OTHER_SCOPE'}
            before2 = dump(row2)
            rep2 = module.apply_to_groups(data, cid, groups2, scope=module.SCOPE)
            scope_atomic = (dump(rows_of(groups2)[target['row_id']][1]) == before2
                            and all(entry['added'] == 0 for entry in rep2['rows']
                                    if entry['row_id'] == target['row_id']))
            ok &= same_rule and scope_atomic and rep['conflicts'] > 0 and rep2['conflicts'] > 0
            details.append({'module': module.MODULE_VERSION, 'cid': cid,
                            'same_rule_atomic': same_rule, 'scope_atomic': scope_atomic,
                            'conflicts': rep['conflicts'], 'scope_conflicts': rep2['conflicts']})
        return ok, {'results': details}
    run('C17_existing_answer_and_scope_conflict_atomic', c17)

    def c18():
        results = []
        ok = True
        for module, view, target, table in (
                (P1, C20.RawView(ROOT), p1_targets[0], 'bosspattern'),
                (P2, P2.DenjuView(ROOT), p2_targets[0], 'denju')):
            skill, row = next((skill, row) for skill, row in rows_of(view.card(target['cid'])).values()
                              if row['row_id'] == target['row_id'])
            good = module.evaluate(view, target['cid'], row, scope=module.SCOPE, skill=skill)
            source = good['answers'][0]['source']
            record = view.layers[source['layer']]['skill_docs'][source['record_index']]
            field = good['answers'][0]['field_path'].lstrip('/')
            old = record[field]
            record[field] = 0
            bad = module.evaluate(view, target['cid'], row, scope=module.SCOPE, skill=skill)
            record[field] = old
            restored = module.evaluate(view, target['cid'], row, scope=module.SCOPE, skill=skill)
            one = (good['status'] == 'RESOLVED' and bad['status'] == 'REJECTED'
                   and 'RAW_NOT_FINITE_POSITIVE' in dump(bad)
                   and restored['status'] == 'RESOLVED')
            ok &= one
            results.append({'module': module.MODULE_VERSION, 'good': good['status'],
                            'mutated': bad.get('reason'), 'restored': restored['status'],
                            'ok': one})
        return ok, {'results': results}
    run('C18_raw_zero_rejected_and_restored', c18)

    def c19():
        texts = {name: (ROOT / path).read_text(encoding='utf-8') for name, path in (
            ('p1', P1.MODULE_REL), ('p2', P2.MODULE_REL),
            ('freeze', 'scripts/character_skills/c21_freeze_direct_damage.py'))}
        banned = ['scripts/skill_reader_preview', 'work/c21_direct_damage_20261111/',
                  'reader_full', 'audit/', 'import card_page_data']
        hits = []
        for name in ('p1', 'p2'):
            for token in banned:
                if token in texts[name]:
                    hits.append({'module': name, 'token': token})
        freeze_hits = [token for token in ('import card_page_data', 'reader_full', 'audit/')
                       if token in texts['freeze']]
        attrs_ok = set(vars(data)) == state['inputs_attrs_after_build']
        class_ok = set(dir(D.Inputs)) == state['inputs_class']
        return (not hits and not freeze_hits and attrs_ok and class_ok), {
            'banned_hits': hits, 'freeze_banned_hits': freeze_hits,
            'inputs_attrs_unchanged': attrs_ok, 'inputs_class_unchanged': class_ok}
    run('C19_production_dependencies_and_inputs_not_mutated', c19)

    def c20():
        failures = []
        banned = ('skillparam', 'bossskill', '/bossinfo', 'bosspattern', 'raw_value', 'floor/')
        for item in state['p1_candidate']['items']:
            for answer in item['answers']:
                text = answer['player_text']
                tokens = [token for token in banned if token in text]
                if tokens or '条件：' not in text or '未验证' not in text \
                        or not answer['player_scope']['conditions'] \
                        or not answer['player_scope']['unknowns']:
                    failures.append({'row': item['row_id'], 'tokens': tokens})
        for item in state['p2_candidate']['items']:
            answer = item['answers'][0]
            text = answer['player_text']
            tokens = [token for token in banned if token in text]
            need = ['传授（denju）链', '条件：', '未验证']
            if item['mirror']:
                need += ['条件镜像', '不一致']
            if tokens or not all(token in text for token in need):
                failures.append({'row': item['row_id'], 'tokens': tokens,
                                 'need': [token for token in need if token not in text]})
            if item['mirror'] and 'mirror' not in answer:
                failures.append({'row': item['row_id'], 'why': 'mirror_block_missing'})
        return not failures, {'answers': len(answers), 'failures': failures[:10]}
    run('C20_player_text_conditions_and_boundaries', c20)

    shared_paths = [
        ROOT / 'scripts/character_skills/card_page_data.py',
        ROOT / 'scripts/character_skills/effect_ledger.py',
        ROOT / 'scripts/character_skills/rules.py',
        ROOT / 'scripts/character_skills/c21_direct_damage_targets.json',
        ROOT / 'output/character_skills/profiles/rules.json',
        ROOT / 'output/character_skills/effect_ledger/ledger.jsonl',
        ROOT / 'output/character_skills/effect_ledger/backlog.json',
    ] + [ROOT / PAGES_REL / str(cid) / 'card.json' for cid in all_cids]
    state['watch_before'] = {str(path.relative_to(ROOT)): sha(path) for path in shared_paths}

    def c21():
        after = {str(path.relative_to(ROOT)): sha(path) for path in shared_paths}
        changed = [key for key, digest in after.items()
                   if state['watch_before'].get(key) != digest]
        return not changed, {'watched': len(after), 'changed': changed[:10]}
    run('C21_shared_files_and_pages_unmodified', c21)

    def c22():
        p2_items = state['p2_candidate']['items']
        mirrors = [item for item in p2_items if item['mirror']]
        direct = [item for item in p2_items if not item['mirror']]
        mirror = mirrors[0] if len(mirrors) == 1 else None
        universe = state['p2_exclusions'].get('mirror_universe') or []
        accepted = [entry for entry in universe if entry.get('accepted')]
        failures = []
        if len(mirrors) != 1 or mirrors[0]['cid'] != 30304:
            failures.append('mirror_count_or_cid')
        if any(item['model'] != P2.DIRECT_MODEL for item in direct):
            failures.append('direct_model')
        if any(not item['denju_parent']['full_text_equal'] for item in direct):
            failures.append('direct_full_text_not_equal')
        if mirror:
            answer = mirror['answers'][0]
            checks_one = {
                'full_text_unequal': mirror['denju_parent']['full_text_equal'] is False,
                'first_sentence_equal': mirror['denju_parent']['first_sentence_equal'] is True,
                'mirror_block': (answer.get('mirror') or {}).get('verdict')
                                == 'CONDITION_MIRROR_ONLY',
                'not_included': 'mirror_disclosure' in (answer.get('not_included') or {}),
                'binding_mirror': (answer['binding'][P2.BINDING_KEY].get('mirror') or {})
                                  .get('verdict') == 'CONDITION_MIRROR_ONLY',
                'record': answer['record_id'] == 43030400 and answer['raw_value'] == 15,
                'existing_same': bool((answer.get('mirror') or {})
                                      .get('existing_same_record_answers')),
            }
            for key, value in checks_one.items():
                if not value:
                    failures.append('mirror_' + key)
        if len(universe) != 3 or len(accepted) != 1 or accepted[0]['cid'] != 30304:
            failures.append('mirror_universe')
        if not any(entry['cid'] == 1292 and entry.get('accepted') is False for entry in universe):
            failures.append('near_mirror_1292_missing')
        return not failures, {'mirrors': len(mirrors), 'direct': len(direct),
                              'universe': [(e['cid'], e.get('accepted')) for e in universe],
                              'failures': failures}
    run('C22_mirror_uniqueness_and_disclosure', c22)

    def c23():
        p1_ex = state['p1_exclusions']['items']
        p2_ex = state['p2_exclusions']['items']
        p1_documented = {item['row_id'] for item in p1_ex if item.get('row_id')}
        p2_documented = {item['row_id'] for item in p2_ex if item.get('row_id')}
        p1_expected = set()
        for cid in sorted({t['cid'] for t in p1_targets}):
            for row_id, (skill, row) in built_rows[cid].items():
                group = row.get('group') or skill.get('original_group')
                if row_id in all_target_rows or group != 'special_move':
                    continue
                if C20.classify_clause(row.get('japanese'))[0] is not None:
                    p1_expected.add(row_id)
        p2_expected = set()
        for cid in sorted({t['cid'] for t in p2_targets}):
            for row_id, (skill, row) in built_rows[cid].items():
                group = row.get('group') or skill.get('original_group')
                if row_id in all_target_rows:
                    continue
                if group == 'denju':
                    p2_expected.add(row_id)
        missing1 = sorted(p1_expected - p1_documented)
        missing2 = sorted(p2_expected - p2_documented)
        protected = {item['cid'] for item in p1_ex + p2_ex
                     if item.get('reason_code') == 'ZERO_TOUCH_CID'}
        negatives = {item['cid'] for item in p1_ex + p2_ex
                     if item.get('reason_code') == 'EXISTING_ANSWER_OR_UNCLOSED_MECHANISM'}
        ok = (not missing1 and not missing2
              and protected == set(P1.PROTECTED_CIDS)
              and negatives == set(P1.NEGATIVE_CIDS))
        return ok, {'p1_documented': len(p1_documented), 'p1_expected': len(p1_expected),
                    'p2_documented': len(p2_documented), 'p2_expected': len(p2_expected),
                    'missing_p1': missing1[:10], 'missing_p2': missing2[:10],
                    'protected': sorted(protected), 'negatives': sorted(negatives)}
    run('C23_exclusions_reconcile', c23)

    def c24():
        titles = {}
        for cid in target_cids:
            doc = load_json(ROOT / PAGES_REL / str(cid) / 'card.json')
            titles[cid] = next((f.get('raw_value') for f in (doc.get('basic') or {})
                                .get('fields') or [] if f.get('key') == 'title'), None)
        yg = [item for item in state['p1_candidate']['items']
              if '《Y.G.' in str(titles.get(item['cid']) or '')]
        ok = (len(yg) == EXPECTED['p1_yg']
              and all(item['layer'] == 'CACHE' and item['reference_field'].startswith('pattern')
                      for item in yg))
        return ok, {'yg_rows': len(yg), 'cids': sorted({item['cid'] for item in yg})}
    run('C24_yg_ten_items_present', c24)

    def c25():
        failures = []
        single = (3, 22, 55, 74)
        multi = (105, 110)
        for item in state['p1_candidate']['items']:
            answer = item['answers'][0]
            layer = item['layer']
            selected = answer['binding'][P1.BINDING_KEY]['selected']
            pattern = raw_index[layer]['pattern_rows'][selected['pattern_index']]
            children = []
            for slot in range(7):
                sid = pattern.get('skillid%d' % slot)
                if sid:
                    index = (raw_index[layer]['skill'].get(sid) or [None])[0]
                    children.append({'slot': slot, 'record_id': sid,
                                     'type': raw_index[layer]['skill_rows'][index]['skillid0'],
                                     'record': raw_index[layer]['skill_rows'][index]})
            form = C20.classify_clause(item['japanese'])[0]
            checks_one = {'form': form in ('MULTIHIT', 'BIGMID'),
                          'type': selected['type'] in (multi if form == 'MULTIHIT' else single),
                          # 反響行只允许绑定 type74 的已确认伤害槽 /skillparam5，
                          # 不借「首次直接攻击」槽（/skillparam1）。
                          'type74_slot': (selected['type'] != 74
                                          or answer['field_path'] == '/skillparam5')}
            if form == 'MULTIHIT':
                n = C20.classify_clause(item['japanese'])[1]['n']
                hits = [c for c in children if c['type'] in multi
                        and c['record'].get('skillparam6') == n]
                checks_one['param6'] = len(hits) == 1
                checks_one['chosen'] = hits and hits[0]['record_id'] == answer['record_id']
            else:
                hits = [c for c in children if c['type'] in single]
                checks_one['single_unique'] = len(hits) == 1
                checks_one['chosen'] = hits and hits[0]['record_id'] == answer['record_id']
            if not all(checks_one.values()):
                failures.append({'row': item['row_id'],
                                 'failed': [k for k, v in checks_one.items() if not v]})
        return not failures, {'rows': len(state['p1_candidate']['items']),
                              'failures': failures[:10]}
    run('C25_p1_forms_match_param6_or_single', c25)

    def c26():
        failures = []
        for item in state['p2_candidate']['items']:
            record = raw_index['CACHE']['denju_rows'][item['denju_parent']['denju_index']]
            pattern = next((candidate for candidate in raw_index['CACHE']['pattern_rows']
                            if candidate.get('patternid') == record.get('patternid0')), None)
            if pattern is None:
                failures.append({'row': item['row_id'], 'why': 'pattern_missing'})
                continue
            equal = record.get('stext') == pattern.get('sinfo')
            expected = not item['mirror']
            if equal != expected:
                failures.append({'row': item['row_id'], 'equal': equal, 'mirror': item['mirror']})
            if item['mirror'] and not (str(record.get('stext')).startswith(
                    str(pattern.get('sinfo')).split('。')[0])):
                failures.append({'row': item['row_id'], 'why': 'first_sentence_prefix'})
        return not failures, {'rows': len(state['p2_candidate']['items']),
                              'failures': failures[:10]}
    run('C26_p2_direct_full_text_equality', c26)

    def c27():
        items = state['p1_candidate']['items'] + state['p2_candidate']['items']
        effect_ids = [answer['effect_binding']['row_id'] for answer in answers]
        ok = (len(items) == EXPECTED['rows'] == len(answers)
              and len(set(effect_ids)) == EXPECTED['rows']
              and len({item['cid'] for item in items}) == EXPECTED['cids']
              and sum(1 for item in state['p2_candidate']['items'] if item['mirror'])
              == EXPECTED['mirror']
              and EXPECTED['p1_rows'] + EXPECTED['p2_rows'] == EXPECTED['rows']
              and EXPECTED['p1_rows'] + EXPECTED['p2_direct'] == EXPECTED['strict'])
        return ok, {'rows': len(items), 'answers': len(answers),
                    'cids': len({item['cid'] for item in items}),
                    'effect_ids_unique': len(set(effect_ids))}
    run('C27_answer_and_effect_accounting', c27)

    def c28():
        passed = sum(1 for check in checks if check['ok'])
        after = {str(path.relative_to(ROOT)): sha(path) for path in shared_paths}
        changed = [key for key, digest in after.items()
                   if state['watch_before'].get(key) != digest]
        ok = passed == len(checks) and not changed
        return ok, {'checks': len(checks), 'passed': passed, 'changed': changed[:10]}
    run('C28_final_accounting_and_shared_zero_write', c28)

    passed = sum(1 for check in checks if check['ok'])
    summary = {'total': len(checks), 'passed': passed, 'failed': len(checks) - passed,
               'all_passed': passed == len(checks)}
    modules = {
        'p1': {'module': P1.MODULE_VERSION, 'scope': P1.SCOPE,
               'module_sha256': sha(ROOT / P1.MODULE_REL),
               'out_dir': P1.OUT_DIR_REL},
        'p2': {'module': P2.MODULE_VERSION, 'scope': P2.SCOPE,
               'module_sha256': sha(ROOT / P2.MODULE_REL),
               'out_dir': P2.OUT_DIR_REL},
    }
    result = {
        'schema': 'c21-candidate-check-result-1',
        'modules': modules,
        'common_module_sha256': sha(ROOT / 'scripts/character_skills/'
                                    'card_page_inference_c20_direct_damage_common.py'),
        'freeze': {'path': 'scripts/character_skills/c21_direct_damage_targets.json',
                   'sha256': sha(ROOT / 'scripts/character_skills/c21_direct_damage_targets.json')},
        'card_page_data_sha256': sha(ROOT / 'scripts/character_skills/card_page_data.py'),
        'baseline': state['p1_candidate']['baseline'],
        'counts': {
            'freeze_targets': len(freeze_targets),
            'p1': state['p1_candidate']['counts'],
            'p2': state['p2_candidate']['counts'],
            'answers': len(answers),
        },
        'check_summary': summary,
        'checks': checks,
        'harness_adaptations': state['adapt'],
        'candidates_sha256': {
            'p1': sha(ROOT / P1.OUT_DIR_REL / 'candidates.json'),
            'p2': sha(ROOT / P2.OUT_DIR_REL / 'candidates.json'),
        },
        'exclusions_sha256': {
            'p1': sha(ROOT / P1.OUT_DIR_REL / 'exclusions.json'),
            'p2': sha(ROOT / P2.OUT_DIR_REL / 'exclusions.json'),
        },
        'started_at_utc': started,
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat(),
        'command': ('./.venv/Scripts/python.exe -X utf8 -I -B '
                    'scripts/character_skills/check_c21_candidate.py --root . --write'),
        'limits': [
            '候选内存自检，不是独立语义审查；未运行正式全库生成、原生执行或实机。',
            'harness_adaptations 只把既有共享模块里过期的逻辑路径／证据根在内存中指向同一'
            '物理快照，未改共享文件；这是当前布局迁移后 build_card 可运行的先决条件。',
            '不验证最终扣血、命中、运行时装载与缓存新鲜度；条件镜像须独立审查决定去留。',
        ],
    }
    if args.write:
        payload = (json.dumps(result, ensure_ascii=False, indent=1, allow_nan=False)
                   + '\n').encode('utf-8')
        for out_dir in (P1.OUT_DIR_REL, P2.OUT_DIR_REL):
            path = write_path(ROOT / out_dir, root=ROOT) / 'check_result.json'
            path.write_bytes(payload)
            print('WROTE', path, flush=True)
    if args.json:
        print(json.dumps({'check_summary': summary, 'counts': result['counts']},
                         ensure_ascii=False, indent=1))
    print('RESULT', json.dumps(summary, ensure_ascii=False))
    return 0 if summary['all_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
