"""Bounded, isolated route experiments. No production imports or writes.

prepare: freeze selected inputs once; run: use frozen files only.
Timing measures local verification, never semantic research or human hours.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import copy
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
from versioned_outputs import experiment_output
import random
import statistics
import sys
import time
from types import SimpleNamespace

PROJECT = Path(__file__).resolve().parents[2]
OUT = experiment_output('skill_route_experiments')
FROZEN = OUT / 'inputs'
EXCLUDED = {7250, 30105, 30301, 30329, 30334, 30236, 30239}
RAW = 'output/cache_full_20261015_v3/decoded/'


def low_priority():
    if os.name == 'nt':
        kernel = ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000):
            raise OSError('Cannot set BELOW_NORMAL_PRIORITY_CLASS')


def inside(path, root):
    try:
        Path(path).resolve().relative_to(root)
        return True
    except (ValueError, TypeError):
        return False


def guard(frozen_reads=False):
    def hook(event, args):
        if event != 'open' or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path, mode, flags = args[:3]
        write = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if write and not inside(path, OUT):
            raise PermissionError('Experiment write outside output denied: ' + str(path))
        if frozen_reads and inside(path, PROJECT) and not any(inside(path, p) for p in
                [OUT, Path(__file__).parent, PROJECT / '.venv']):
            raise PermissionError('Live project read during frozen experiment denied: ' + str(path))
    sys.addaudithook(hook)


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def prepare():
    if (FROZEN / 'manifest.json').exists():
        raise RuntimeError('Frozen manifest exists; use run to reuse it, do not overwrite it')
    started = time.perf_counter()
    manifest = {'excluded_cids': sorted(EXCLUDED), 'sources': {}, 'selection_seed': 20261103}

    def freeze(rel, target=None):
        p = PROJECT / rel if rel.startswith('scripts/') else read_path(PROJECT / rel, root=PROJECT)
        before = p.stat()
        blob = p.read_bytes()
        after = p.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError('Input changed while reading: ' + rel)
        q = FROZEN / (target or rel)
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes(blob)
        manifest['sources'][rel] = {'sha256': sha(blob), 'bytes': len(blob),
                                    'frozen': q.relative_to(FROZEN).as_posix()}
        return json.loads(blob) if p.suffix == '.json' else blob

    metrics = freeze('output/character_skills/effect_ledger/metrics.json', 'metrics.json')
    freeze('output/character_skills/profiles/rules.json', 'rules.json')
    freeze('scripts/character_skills/card_page_inference_g1_structure.py', 'g1_structure.py')
    for name in ['bossinfo', 'charainfo', 'denju']:
        freeze(RAW + name + '.data5.json.raw')
    ledger = read_path(PROJECT / 'output/character_skills/effect_ledger/ledger.jsonl',root=PROJECT)
    before = ledger.stat()
    digest = hashlib.sha256()
    rows, effects, row_ids = [], [], set()
    with ledger.open('rb') as stream:
        for line in stream:
            digest.update(line)
            d = json.loads(line)
            if d['record_type'] == 'description' and d['yg']:
                rows.append(d)
                row_ids.add(d['row_id'])
            elif d['record_type'] == 'effect' and d['description_ref'] in row_ids:
                effects.append(d)
    after = ledger.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError('Ledger changed while freezing')
    if len(rows) != metrics['descriptions']['total']['yg'] or len(effects) != metrics['effects']['identified_total']['yg']:
        raise AssertionError('Frozen ledger/metrics mismatch or ledger ordering changed')
    anchors = {r['input_snapshot']['snapshot_id'] for r in rows}
    if anchors != {metrics['snapshot']['snapshot_id']}:
        raise AssertionError('Mixed ledger snapshot')
    manifest['ledger'] = {'source': 'output/character_skills/effect_ledger/ledger.jsonl', 'sha256': digest.hexdigest(),
                          'bytes': after.st_size, 'snapshot_ids': sorted(anchors)}
    write_json(FROZEN / 'yg_ledger.json', {'descriptions': rows, 'effects': effects})
    pool = sorted({r['cid'] for r in rows} - EXCLUDED)
    fixed = [x for x in [351, 4315, 7251] if x in pool]
    cids = sorted(fixed + random.Random(20261103).sample([x for x in pool if x not in fixed], 15))
    for cid in cids:
        freeze(f'output/character_skills/pages/{cid}/card.json', f'cards/{cid}.json')
    manifest['sample_cids'] = cids
    manifest['snapshot'] = metrics['snapshot']['snapshot_id']
    drift = []
    for rel, entry in manifest['sources'].items():
        source = PROJECT / rel if rel.startswith('scripts/') else read_path(PROJECT / rel, root=PROJECT)
        if sha(source.read_bytes()) != entry['sha256']:
            drift.append(rel)
    if drift:
        write_json(OUT / 'freeze_failure.json', {'changed_sources': drift})
        raise RuntimeError('Production advanced during freeze; do not use mixed inputs')
    manifest['freeze_source_check'] = 'UNCHANGED_DURING_FREEZE'
    manifest['freeze_seconds'] = time.perf_counter() - started
    manifest['frozen_bytes'] = sum(p.stat().st_size for p in FROZEN.rglob('*') if p.is_file())
    if manifest['frozen_bytes'] > 80 * 1024**2:
        raise RuntimeError('Snapshot exceeds 80 MiB ceiling')
    write_json(FROZEN / 'manifest.json', manifest)
    print(json.dumps({'prepared': len(cids), 'bytes': manifest['frozen_bytes'], 'seconds': manifest['freeze_seconds']}))


def load_g1():
    spec = importlib.util.spec_from_file_location('frozen_g1', FROZEN / 'g1_structure.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_rows(card):
    return [(g['group'], s, r) for g in card['groups'] for s in g['skills'] for r in s['rows']]


def verification_tasks(cards):
    tasks = []
    for card in cards:
        for group, skill, row in all_rows(card):
            for i, a in enumerate(row.get('answers', [])):
                source = a.get('source') or {}
                key = a.get('rule_key', '')
                if a.get('layer') == 'CACHE' and a.get('table') == 'bossskill' and key:
                    tasks.append({'cid': card['cid'], 'row_id': row['row_id'], 'answer_index': i,
                        'rule_key': key, 'record_id': a.get('record_id'), 'raw_value': a.get('raw_value'),
                        'field': a.get('field_path'), 'source': source})
    return tasks


def verify_one(task, records):
    hits = [r for r in records if r.get('skillid') == task['record_id']] if isinstance(records, list) else records.get(task['record_id'], [])
    key = task['rule_key'].split('|')
    field = str(task['field'] or '').lstrip('/')
    rec = hits[0] if len(hits) == 1 else {}
    source = task['source']
    return {'row_id': task['row_id'], 'answer_index': task['answer_index'], 'record_id': task['record_id'],
        'raw_matches': len(hits) == 1 and field in rec and rec[field] == task['raw_value'],
        'type_matches': len(key) == 3 and str(rec.get('skillid0')) == key[1],
        'source_id_matches': source.get('record_id') == task['record_id'],
        'source_layer_matches': source.get('layer') == 'CACHE'}


def source_index(records):
    result = collections.defaultdict(list)
    for rec in records:
        result[rec['skillid']].append(rec)
    return dict(result)


def route_baseline(tasks, raw_text):
    # Deliberately simple reference implementation, NOT the current production baseline.
    return [verify_one(t, json.loads(raw_text)['bossinfo']['bossskill']) for t in tasks]


def route_index(tasks, raw_text):
    index = source_index(json.loads(raw_text)['bossinfo']['bossskill'])
    return [verify_one(t, index) for t in tasks]


def route_dedup(tasks, raw_text):
    index = source_index(json.loads(raw_text)['bossinfo']['bossskill'])
    cache, out = {}, []
    for task in tasks:
        key = json.dumps({k: v for k, v in task.items() if k not in ('cid', 'row_id', 'answer_index')}, sort_keys=True, ensure_ascii=False)
        if key not in cache:
            cache[key] = verify_one(task, index)
        out.append({**cache[key], 'row_id': task['row_id'], 'answer_index': task['answer_index']})
    return out


WORKER_INDEX = None


def worker_init(raw_text):
    global WORKER_INDEX
    low_priority()
    guard(True)
    WORKER_INDEX = source_index(json.loads(raw_text)['bossinfo']['bossskill'])


def verify_chunk(tasks):
    return [verify_one(t, WORKER_INDEX) for t in tasks]


def measure(fn, *args, rounds=3):
    times, result = [], None
    for _ in range(rounds):
        started = time.perf_counter()
        result = fn(*args)
        times.append(time.perf_counter() - started)
    return result, {'seconds': times, 'median_seconds': statistics.median(times)}


def g1_replay(cards, g1):
    chara = read_json(FROZEN / (RAW + 'charainfo.data5.json.raw'))['charainfo']
    denju = read_json(FROZEN / (RAW + 'denju.data5.json.raw'))['denju']
    cache_chara = {r['cid']: r for r in chara}
    denjus = {r['denju_id']: r for r in denju}
    links = {cid: {'groups': [{'group': 'denju', 'records': [{'table': 'denju', 'record': r}]}]} for cid, r in denjus.items()}
    data = SimpleNamespace(root=FROZEN, cache_chara=cache_chara, links=links)
    results, cases = [], []
    oracle_records = read_json(FROZEN / (RAW + 'bossinfo.data5.json.raw'))['bossinfo']['bossskill']
    for card in cards:
        cid = card['cid']
        rows = all_rows(card)
        mirrors = [(gn, s, r) for gn, s, r in rows if g1.row_kind(gn, r.get('reference_field'))]
        patterns = [(gn, s, r) for gn, s, r in rows if str(r.get('reference_field', '')).startswith('pattern')]
        injective = {}
        for gn, skill, row in mirrors:
            parent, err = g1.resolve_parent(data, cid, g1.row_kind(gn, row.get('reference_field')), skill.get('layer'))
            form, detail = g1.classify_clause(row.get('japanese'))
            if err or form in (None, 'PLAIN'):
                continue
            _, pattern, children = g1.children_of(data, skill.get('layer'), parent['pattern_id'])
            if not pattern or g1.canon(pattern.get('sinfo')) != g1.canon(parent['text']):
                continue
            chosen, _ = g1.select_child(children, form, detail)
            if chosen:
                injective.setdefault((parent['pattern_id'], g1.canon(parent['text'])), {}).setdefault(chosen['skillid'], []).append(row['row_id'])
        for gn, skill, row in mirrors:
            row = {**row, '_group': gn}
            parent, err = g1.resolve_parent(data, cid, g1.row_kind(gn, row.get('reference_field')), skill.get('layer'))
            inj = injective.get((parent['pattern_id'], g1.canon(parent['text']))) if not err else None
            base, relaxed = g1._base_answers(patterns, row.get('japanese'))
            args = dict(injective=inj, base_answers=base, base_answers_tag=relaxed)
            res = g1.evaluate(data, cid, row, skill.get('layer'), **args)
            hidden = g1.evaluate(data, cid, row, skill.get('layer'), injective=inj, base_answers=[])
            selected = res.get('selected') or {}
            # Independent check against the original decoded array, not select_child's own expected output.
            oracle = next((r for r in oracle_records if r['skillid'] == selected.get('skillid')), None) if selected else None
            existing = [a for a in row.get('answers', []) if a.get('rule_key') == selected.get('rule_key')]
            record_matches = [a for a in existing if a.get('record_id') == selected.get('skillid') and a.get('raw_value') == selected.get('raw')]
            item = {'cid': cid, 'row_id': row['row_id'], 'verdict': res.get('verdict'), 'rejection': res.get('rejection'),
                    'without_base_answer': hidden.get('verdict') or hidden.get('rejection'), 'selected': selected,
                    'raw_oracle_matches': oracle is not None and oracle.get(str(selected.get('slot', '')).lstrip('/')) == selected.get('raw'),
                    'existing_same_record_value_count': len(record_matches)}
            results.append(item)
            if res.get('verdict') == 'VALUE_AND_BINDING' and len(cases) < 6 and cid not in {c[1] for c in cases}:
                cases.append((data, cid, row, skill.get('layer'), args, res))
    return results, cases


def mutation_experiments(g1, cases):
    results = []
    for n, (data, cid, row, layer, args, baseline) in enumerate(cases):
        original = g1._bossinfo(data.root)
        pid = baseline['parent']['pattern_id']
        pattern = original['patterns'][pid]
        ids = [pattern[1].get('skillid' + str(i)) for i in range(4)]
        small = {'patterns': {pid: copy.deepcopy(pattern)}, 'skills': {i: copy.deepcopy(original['skills'][i]) for i in ids if i in original['skills']}}
        for mode in ['same_fixture', 'renumber_ids', 'new_raw_consistent', 'new_raw_all_equivalent_carriers', 'raw_changed_without_crosscheck',
                     'missing_crosscheck', 'cross_layer', 'parent_text_mismatch', 'missing_raw',
                     'null_raw', 'negative_raw', 'bool_raw', 'unsupported_type', 'ambiguous_different_value']:
            db = copy.deepcopy(small)
            newcid, newpid = cid, pid
            newrow, newargs = copy.deepcopy(row), copy.deepcopy(args)
            parentrec = copy.deepcopy(baseline['parent']['record'])
            chosen_id = baseline['selected']['skillid']
            slot = baseline['selected']['slot'].lstrip('/')
            if mode == 'renumber_ids':
                shift = 900000000
                newcid, newpid = cid + shift, pid + shift
                pat = db['patterns'].pop(pid)
                pat[1]['patternid'] = newpid
                for i in range(4):
                    k = 'skillid' + str(i)
                    if pat[1].get(k): pat[1][k] += shift
                db['patterns'][newpid] = pat
                db['skills'] = {sid + shift: (idx, {**rec, 'skillid': sid + shift}) for sid, (idx, rec) in db['skills'].items()}
                chosen_id += shift
                parentrec['patternid0' if baseline['kind'] == 'DENJU' else 'pattern0'] = newpid
                parentrec['denju_id' if baseline['kind'] == 'DENJU' else 'cid'] = newcid
                newrow['row_id'] = str(newcid) + '-synthetic'
                shifted_objects = set()
                for key in ['base_answers', 'base_answers_tag']:
                    for a in newargs[key]:
                        if id(a) not in shifted_objects and isinstance(a.get('record_id'), int):
                            a['record_id'] += shift
                            shifted_objects.add(id(a))
                if newargs['injective']:
                    newargs['injective'] = {sid + shift: names for sid, names in newargs['injective'].items()}
            rec = db['skills'][chosen_id][1]
            same_n_carriers = [sid for sid, (_, child) in db['skills'].items()
                               if child.get('skillid0') in (105, 110)
                               and rec.get('skillid0') in (105, 110)
                               and child.get('skillparam6') == rec.get('skillparam6')]
            competing = len(same_n_carriers) > 1
            if mode in ['new_raw_consistent', 'new_raw_all_equivalent_carriers', 'raw_changed_without_crosscheck']:
                rec[slot] += 0.125
                changed_ids = {chosen_id}
                if mode == 'new_raw_all_equivalent_carriers':
                    for sid in same_n_carriers:
                        if sid != chosen_id:
                            db['skills'][sid][1][slot] += 0.125
                            changed_ids.add(sid)
                if mode in ['new_raw_consistent', 'new_raw_all_equivalent_carriers']:
                    for key in ['base_answers', 'base_answers_tag']:
                        for a in newargs[key]:
                            if a.get('record_id') in changed_ids and a.get('rule_key') == baseline['selected']['rule_key']:
                                a['raw_value'] = rec[slot]
            if mode == 'missing_crosscheck': newargs['base_answers'] = []
            if mode == 'parent_text_mismatch': parentrec['stext' if baseline['kind'] == 'DENJU' else 'skilltext'] = 'unrelated text'
            if mode == 'missing_raw': rec.pop(slot, None)
            if mode == 'null_raw': rec[slot] = None
            if mode == 'negative_raw': rec[slot] = -1
            if mode == 'bool_raw': rec[slot] = True
            if mode == 'unsupported_type':
                for _, child in db['skills'].values(): child['skillid0'] = 999999
            if mode == 'ambiguous_different_value':
                # Synthetic corruption: add a competing child, replacing a different
                # reference only when the real pattern has all four slots occupied.
                free = next((i for i in range(4) if not db['patterns'][newpid][1].get('skillid' + str(i))), None)
                if free is None:
                    free = next(i for i in range(4) if db['patterns'][newpid][1].get('skillid' + str(i)) != chosen_id)
                duplicate = {**rec, 'skillid': chosen_id + 800000000, slot: float(rec[slot]) + 1}
                db['skills'][duplicate['skillid']] = (99999, duplicate)
                db['patterns'][newpid][1]['skillid' + str(free)] = duplicate['skillid']
            root = FROZEN / f'synthetic-{n}-{mode}'
            g1._BOSSINFO_CACHE[str(root.resolve())] = db
            fixture = SimpleNamespace(root=root, cache_chara={newcid: parentrec},
                links={newcid: {'groups': [{'group': 'denju', 'records': [{'table': 'denju', 'record': parentrec}]}]}})
            res = g1.evaluate(fixture, newcid, newrow, 'APK' if mode == 'cross_layer' else layer, **newargs)
            if mode in ['new_raw_consistent', 'raw_changed_without_crosscheck'] and competing:
                expected = 'REJECT: changing only one of multiple same-N carriers creates conflicting values'
                passed = bool(res.get('rejection'))
            elif mode in ['same_fixture', 'renumber_ids', 'new_raw_consistent', 'new_raw_all_equivalent_carriers']:
                expected = 'VALUE_AND_BINDING'
                passed = res.get('verdict') == expected and res['selected']['skillid'] == chosen_id and res['selected']['raw'] == rec[slot]
            elif mode in ['missing_crosscheck', 'raw_changed_without_crosscheck']:
                expected = 'FIELD_VALUE_ONLY (no description binding)'
                passed = res.get('verdict') == 'FIELD_VALUE_ONLY'
            else:
                expected = 'REJECT'
                passed = bool(res.get('rejection'))
            results.append({'case': n, 'original_cid': cid, 'original_row_id': row['row_id'], 'mode': mode, 'expected': expected,
                            'observed': res.get('rejection') or res.get('verdict'), 'passed': passed})
            del g1._BOSSINFO_CACHE[str(root.resolve())]
    return results


def grouping(ledger, tasks):
    rows = {r['row_id']: r for r in ledger['descriptions'] if r['cid'] not in EXCLUDED}
    unresolved = [e for e in ledger['effects'] if e['description_ref'] in rows and e['status'] == 'unresolved']
    pending = [r for r in rows.values() if r['ledger_row_status'] != '完整']
    exact = collections.defaultdict(list)
    for r in pending: exact[r['japanese_nfkc']].append(r)
    cross_context = [text for text, rr in exact.items() if len({(r['namespace']['layer'], r['namespace']['table'], r['skill_category']) for r in rr}) > 1]
    family = collections.defaultdict(set)
    for t in tasks: family[t['rule_key']].add(t['cid'])
    return {'remaining_rows': len(pending), 'exact_text_groups': len(exact),
        'same_text_multiple_source_context_groups': len(cross_context),
        'same_text_multiple_context_examples': [{'text': t, 'rows': [r['row_id'] for r in exact[t]][:8]} for t in cross_context[:6]],
        'unresolved_effects': len(unresolved),
        'effect_type_sentence_groups': len({(e['effect_type'], rows[e['description_ref']]['japanese_nfkc']) for e in unresolved}),
        'rule_families_in_verification_sample': len(family),
        'card_family_pairs': sum(len(cids) for cids in family.values()),
        'families': {k: sorted(v) for k, v in sorted(family.items())},
        'limits': 'Grouping only; textual or rule-key equivalence does not prove identical objects, conditions, stages or source identity.'}


def run():
    input_hashes = {p.relative_to(FROZEN).as_posix(): sha(p.read_bytes()) for p in FROZEN.rglob('*') if p.is_file()}
    manifest = read_json(FROZEN / 'manifest.json')
    for entry in manifest['sources'].values():
        if sha((FROZEN / entry['frozen']).read_bytes()) != entry['sha256']:
            raise AssertionError('Frozen input hash mismatch')
    cards = [read_json(FROZEN / f'cards/{cid}.json') for cid in manifest['sample_cids']]
    tasks = verification_tasks(cards)
    if not tasks: raise AssertionError('Empty sample')
    raw_text = (FROZEN / (RAW + 'bossinfo.data5.json.raw')).read_text(encoding='utf-8-sig')
    results = {'snapshot': manifest['snapshot'], 'sample_cids': manifest['sample_cids'], 'tasks': len(tasks),
               'limits': ['No new semantic answers delivered', 'No future cache or true unseen-card validation',
                          'Machine timing is not engineering person-hours', 'Two-process verification is not multi-agent research']}
    expected, results['reference_naive'] = measure(route_baseline, tasks, raw_text)
    indexed, results['indexed'] = measure(route_index, tasks, raw_text)
    warm_index = source_index(json.loads(raw_text)['bossinfo']['bossskill'])
    indexed_warm, results['indexed_warm'] = measure(lambda: [verify_one(t, warm_index) for t in tasks])
    deduped, results['deduplicated'] = measure(route_dedup, tasks, raw_text)
    results['exact_equality'] = {'indexed': indexed == expected, 'indexed_warm': indexed_warm == expected, 'deduplicated': deduped == expected}
    results['source_checks'] = {key: {'pass': sum(bool(x[key]) for x in expected), 'total': len(expected)} for key in ['raw_matches', 'type_matches', 'source_id_matches', 'source_layer_matches']}
    results['unique_source_checks'] = len({json.dumps({k: v for k, v in t.items() if k not in ('cid', 'row_id', 'answer_index')}, sort_keys=True) for t in tasks})
    chunks = [[t for t in tasks if t['cid'] == cid] for cid in manifest['sample_cids']]
    chunks = [c for c in chunks if c]
    cold_times, warm_times, parallel_output = [], [], None
    for _ in range(3):
        start = time.perf_counter()
        with concurrent.futures.ProcessPoolExecutor(max_workers=2, initializer=worker_init, initargs=(raw_text,)) as pool:
            parallel_output = [x for chunk in pool.map(verify_chunk, chunks) for x in chunk]
            cold_times.append(time.perf_counter() - start)
            start_warm = time.perf_counter()
            warm = [x for chunk in pool.map(verify_chunk, chunks) for x in chunk]
            warm_times.append(time.perf_counter() - start_warm)
            assert warm == parallel_output
    results['two_process'] = {'cold_seconds': cold_times, 'warm_seconds': warm_times,
                              'cold_median_seconds': statistics.median(cold_times), 'warm_median_seconds': statistics.median(warm_times),
                              'exact_equality': parallel_output == expected, 'workers': 2, 'priority': 'BELOW_NORMAL'}
    results['grouping'] = grouping(read_json(FROZEN / 'yg_ledger.json'), tasks)
    g1 = load_g1()
    replay, cases = g1_replay(cards, g1)
    mutations = mutation_experiments(g1, cases)
    results['structure'] = {'rows': len(replay), 'verdicts': dict(collections.Counter(x['verdict'] or x['rejection'] for x in replay)),
        'without_crosscheck': dict(collections.Counter(x['without_base_answer'] for x in replay)),
        'selected': sum(bool(x['selected']) for x in replay), 'raw_oracle_matches': sum(x['raw_oracle_matches'] for x in replay),
        'existing_same_record_value_rows': sum(x['existing_same_record_value_count'] > 0 for x in replay),
        'mutation_cases': len(mutations), 'mutation_pass': sum(x.get('passed') is True for x in mutations),
        'mutation_fail': sum(x.get('passed') is False for x in mutations), 'mutation_skip': sum('passed' not in x for x in mutations)}
    guard_checks = {}
    for name, mode, flags in [('production_read_denied', 'r', 0), ('production_write_denied', 'w', os.O_WRONLY)]:
        try:
            sys.audit('open', str(PROJECT / 'production-guard-probe-never-created'), mode, flags)
            guard_checks[name] = False
        except PermissionError:
            guard_checks[name] = True
    current_hashes = {p.relative_to(FROZEN).as_posix(): sha(p.read_bytes()) for p in FROZEN.rglob('*') if p.is_file()}
    results['isolation'] = {'guard_checks': guard_checks, 'frozen_files': len(input_hashes),
                            'frozen_unchanged': current_hashes == input_hashes,
                            'script_sha256': sha(Path(__file__).read_bytes()), 'read_scope': 'frozen files and runtime only',
                            'write_scope': str(OUT), 'guard_is_os_sandbox': False}
    write_json(OUT / 'input_hashes.json', input_hashes)
    write_json(OUT / 'verification_tasks.json', tasks)
    write_json(OUT / 'source_checks.json', expected)
    write_json(OUT / 'structure_replay.json', replay)
    write_json(OUT / 'structure_mutations.json', mutations)
    write_json(OUT / 'results.json', results)
    assert all(results['exact_equality'].values()) and parallel_output == expected
    assert results['structure']['mutation_fail'] == 0
    assert all(guard_checks.values()) and current_hashes == input_hashes
    print(json.dumps({k: v for k, v in results.items() if k != 'grouping'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    low_priority()
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'run'])
    args = parser.parse_args()
    if args.command == 'prepare':
        OUT.mkdir(parents=True)
    guard(args.command == 'run')
    (prepare if args.command == 'prepare' else run)()
