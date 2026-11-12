"""Verify only CID12236's two super rows and CID5300's forest/use-count pair.

Owns sparse_receipt.json in this directory. No reader/mainline writes.
Runtime defaults below apply ONLY to the verified fresh primary JSON load path.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'output/character_skills/reader_full_20261106/audit/final5_evidence_20261107/native/sparse'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(rel):
    path = ROOT / rel
    INPUTS[rel] = digest(path)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def select(records, hp, stage, counts, draw):
    # Fresh primary JSON load: ctor initializes hpstart/hpend/priority to0;
    # FromJSONDictionary overwrites only keys present. Missing limit getter=0.
    eligible = [r for r in records if r.get('hpstart', 0) <= hp <= r.get('hpend', 0)
                and (not r.get('bgf', 0) or r['bgf'] & stage)
                and (not r.get('limit', 0) or counts[r['patternid']] < r['limit'])]
    acc = 0
    for r in eligible:
        previous = acc
        acc += r.get('priority', 0)
        if previous <= draw < acc:
            return r['patternid']
    return eligible[0]['patternid'] if eligible else None


INPUTS = {}
if __name__ == '__main__':
    INPUTS[Path(__file__).relative_to(ROOT).as_posix()] = digest(Path(__file__))
    bossrel = 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw'
    boss = read(bossrel)['bossinfo']
    parents = {r['patternid']: (i, r) for i, r in enumerate(boss['bosspattern'])}
    charrel = 'output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw'
    chars = read(charrel)['charainfo']
    terrain = read('output/ordinary_effects/ability7/trace.json')
    nativehash = digest(ROOT / 'work/protection/il2cpp_loader_seed1.bin')
    assert nativehash == terrain['native_sha256']
    proof = read('output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/native_selection_proof.json')
    assert proof['nativeSHA256'] == nativehash
    INPUTS['work/protection/il2cpp_loader_seed1.bin'] = nativehash
    INPUTS['work/protection/metadata_aei_decoded.bin'] = digest(ROOT / 'work/protection/metadata_aei_decoded.bin')
    assert INPUTS['work/protection/metadata_aei_decoded.bin'] == proof['metadataSHA256']
    evidence = {}
    for path in sorted(HERE.glob('*.txt')):
        evidence[path.relative_to(ROOT).as_posix()] = digest(path)
    prefix = 'output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/'
    for name in ['4928_think_attack.txt', '4927_getPatternAttackList.txt',
                 '5174_CreateExecSkillList.txt', '9116_GetExecSkillInfo.txt', '4619_ctor.txt']:
        evidence[prefix + name] = digest(ROOT / (prefix + name))
    receipts = []
    for cid, ids, flag in [(12236, [41223602, 41223605], 32768),
                           (5300, [40530000, 40530001], 8192)]:
        char = next(r for r in chars if r['cid'] == cid)
        refs = [v for k, v in char.items() if k.startswith('pattern') and k[7:].isdigit() and v]
        assert len(refs) == len(set(refs)) and all(v in parents for v in refs)
        card = read(f'output/character_skills/pages/{cid}/card.json')
        assert set(refs) == {s['record_id'] for g in card['groups'] if g['group']=='special_move' for s in g['skills'] if s.get('table')=='bosspattern'}
        records = [parents[v][1] for v in refs if parents[v][1].get('flag', 0) == flag]
        assert [r['patternid'] for r in records] == ids
        assert len({r.get('sname') for r in records}) == 1
        assert all(r.get('hpend') == 100 for r in records), 'Current upper HP bounds are explicit, not invented defaults'
        assert all(r.get('hpstart', 0) == 0 for r in records)
        assert all(r.get(k, 0) == 0 for r in records for k in ('mns', 'mne', 'chs', 'che', 'posp', 'pose', 'tid'))
        sources = [dict(file=bossrel, pointer=f'/bossinfo/bosspattern/{parents[i][0]}', raw=parents[i][1]) for i in ids]
        probes = []
        if cid == 12236:
            assert 'priority' not in records[0] and records[1]['priority'] == 100
            assert all(r.get('limit', 0) == r.get('bgf', 0) == 0 for r in records)
            counts = dict.fromkeys(ids, 0)
            for hp in range(101):
                choices = {select(records, hp, 0, counts, draw) for draw in range(100)}
                assert choices == {41223605}
                probes.append({'hp': hp, 'allDraws': [0, 99], 'selected': 41223605})
            labels = {'41223605': '超共鸣模式：当前常规UI预测选中',
                      '41223602': '超共鸣模式：当前常规UI预测不选用的旧候选'}
            reason = 'Missing priority stays ctor0 on verified JSON path; explicit100 branch covers every random draw. bFirst=true availability is a separate mode.'
        else:
            assert records[0]['bgf'] == 4 and records[0]['limit'] == 3 and records[0]['priority'] == 100
            assert all(records[1].get(k, 0) == 0 for k in ('bgf', 'limit', 'priority'))
            forest = [r['raw'] for r in terrain['background_source_records'] if r['raw']['flag'] & 4]
            assert forest and all(r['bg_name'] in ('森林', '森林夜') for r in forest)
            for b in terrain['background_source_records']:
                b = b['raw']
                for uses in range(6):
                    counts = {40530000: uses, 40530001: 0}
                    expected = 40530000 if b['flag'] & 4 and uses < 3 else 40530001
                    total = 100 if expected == 40530000 else 0
                    choices = {select(records, 50, b['flag'], counts, draw)
                               for draw in (range(total) if total else [0])}
                    assert choices == {expected}
                    probes.append({'backgroundId': b['id'], 'backgroundName': b['bg_name'],
                                   'forestControllerUses': uses, 'selected': expected})
            # Leaving the forest does not consume the forest controller's uses.
            counts = {40530000: 0, 40530001: 0}
            for stage, expected in [(4, 40530000), (0, 40530001), (4, 40530000),
                                    (4, 40530000), (4, 40530001), (0, 40530001)]:
                assert select(records, 50, stage, counts, 0) == expected
                counts[expected] += 1
            labels = {'40530000': '森林（含夜间），当前森林附加分支已施放少于3次',
                      '40530001': '非森林，或当前森林附加分支已施放3次及以上'}
            reason = 'Joint terrain and per-controller use-count proof; unlimited base is selected by zero-total first-eligible fallback after the weighted forest branch becomes ineligible.'
        receipts.append(dict(cid=cid, sourceParents=sources, allCharacterPatternIds=refs,
                             conditionLabels=labels, reason=reason, probes=probes,
                             scope='Common mode eligibility holds. Current controller-list lifetime and normal UI cached prediction only; no battle-global never-reset guarantee.'))
    # Counterexample: a truly missing upper bound does NOT become100 here.
    assert select([{'patternid': 1, 'priority': 100}], 1, 0, {1: 0}, 0) is None
    report = dict(owner='branch_inventory_review', sourceHashes=INPUTS,
                  methodExcerptHashes=evidence, sourceLoaderFacts=[
        {'fact': 'getMasterBossInfo callback calls DataManager bossparameter primary JSON loader, then sorts.', 'rva': '0x19e789c..0x19e7900'},
        {'fact': 'Primary JSON loader allocates a fresh BattleBossPattern per row and calls its ctor then FromJSONDictionary.', 'rva': '0x1a709e4..0x1a70a5c'},
        {'fact': 'Ctor initializes hpstart,hpend,priority ParamS_int to0. JSON setters only execute for present keys; no missing-hpend->100 branch.', 'rvas': ['0x1a6e114..0x1a6e164', '0x1a6db34..0x1a6db9c', '0x1a6dd40..0x1a6dd64']},
        {'fact': 'getBossPattern first searches primary objects; only absent record null falls back to AB. Missing fields do not cause fieldwise AB merge.', 'rva': '0x1a701ac..0x1a701e0'},
        {'fact': 'AB uses FromScriptableObject -> daBattleBossParameter_J.ToObject into ab_bosspattern; not the primary CACHE row path. Its conversion defaults are not generalized here.', 'rva': '0x1a70c54..0x1a70c6c'},
    ], items=receipts, negativeTests=['Missing hpend remains0 on this fresh primary JSON path; HP1 does not qualify. Never default it to100.'],
        limits=['Static existing image only; not game validation.', 'J/AB conversion defaults are not asserted; present CACHE records take primary lookup.', 'Normal UI bFirst=false route only; availability bFirst=true may return another first eligible pattern.', 'No full loading/network schedule or cache-freshness claim.'])
    report['parents'] = {}
    for item in receipts:
        for parent in item['sourceParents']:
            raw=parent['raw'];pid=raw['patternid'];cid=item['cid']
            unused=cid==12236 and pid==41223602
            label=('旧分支（常规选档不选用）' if unused else '当前选档') if cid==12236 else ('森林（含夜间），森林分支已用不足3次' if pid==40530000 else '非森林，或森林分支已用满3次')
            report['parents'][f'CACHE:{pid}']={'cid':cid,'branchId':pid,'parentRaw':raw,'parentSource':{'file':parent['file'],'pointer':parent['pointer']},'selectionResolved':True,'selectionUnavailable':unused,'conditionLabel':label,'selectionOrder':(1 if unused else 0) if cid==12236 else (1 if pid==40530000 else 0),'selectionKind':'verified_primary_json_weight_pair' if cid==12236 else 'verified_forest_limit3','reason':item['reason'],'scope':item['scope'],'limits':report['limits']}
    report['inputs']={**INPUTS,**evidence}
    for rel,expected in report['inputs'].items():
        assert digest(ROOT/rel)==expected, f'Source changed during review: {rel}'
    (HERE.parents[1] / 'sparse_receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'cards': len(receipts), 'targetRows': 3, 'models': '12236 0/100 plus5300 forest/limit3',
                      'receipt': str(HERE.parents[1] / 'sparse_receipt.json')}))
