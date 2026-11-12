"""Screen every purple final5 item against complete same-layer character refs.

Writes independent work receipts only. The reusable parents map is display
selection evidence, not an effect binding or an answer/rule modification.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
AUDIT = 'output/character_skills/reader_full_20261106/audit/'
SELECT = AUDIT + 'selection_order_20261107/native/'
FINAL = AUDIT + 'final5_evidence_20261107/'
SCOPE = ('当前同模式资格成立时的普通手动UI选档预测快照；执行沿用缓存ID。'
         '使用阶段限当前控制器列表生命周期，不保证跨波、复活或重建不重置。')
LIMITS = ['静态原生证据与原表枚举，未做实机验证。',
          '不将bFirst=true资格检测、自动无ID重选、显式外部ID执行当作普通UI预测。',
          '不保证选档缓存刷新即时，不将预测扣费后区间换算成所有场景的发动前阈值。',
          '随机权重/分布只指单次预测调用，不代表实际点击或施放频率。',
          '这里只解释父选择；同句效果归属、附加能力、最终伤害、命中和成功次数仍沿用各自证据。']
FIELDS = ('hpstart', 'hpend', 'priority', 'limit', 'bgf', 'mns', 'mne',
          'chs', 'che', 'posp', 'pose', 'tid', 'flag')
SUPPORTED_FLAGS = {0, 4, 8, 256, 260, 8192, 8448, 32768}
INPUTS = {}
CACHE = {}


def pin(rel, expected=None):
    digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    if expected is not None:
        assert digest == expected, f'Evidence changed: {rel}'
    if rel in INPUTS:
        assert INPUTS[rel] == digest, f'Source changed during read: {rel}'
    INPUTS[rel] = digest
    return digest


def read(rel):
    pin(rel)
    if rel not in CACHE:
        CACHE[rel] = json.loads((ROOT / rel).read_text(encoding='utf-8-sig'))
    return CACHE[rel]


def indexed(rows, key):
    result = {row[key]: (i, row) for i, row in enumerate(rows)}
    assert len(result) == len(rows), key
    return result


def binding(source):
    value = source.get('originalBinding') or {}
    for key in ('g1_b1_binding', 'c12_p3_skilltext_mirror_binding',
                'c8_p1_t27_binding', 'c11_p1_t114_binding'):
        if key in value:
            value = value[key]
            break
    return value


def identity(item):
    source = item['source']
    bind = binding(source)
    # Keep the old changes tuple as a prefix, but include explicit binding and
    # answer index: CID30204 has two legitimate answers colliding in that tuple.
    return [item['rowId'], item['effect'], source.get('layer'),
            source.get('branchId'), source.get('recordId'), source.get('rule'),
            source.get('field'), source.get('raw'), item['text'],
            bind.get('pattern_id'), source.get('effectId'), source.get('answerIndex')]


def exclusive(left, right):
    """Only two disjoint predicates actually proven in the native selector."""
    if (left & 4 and right & 8) or (left & 8 and right & 4):
        return 'SSkillGaugeFull: bit2要求满槽，bit3要求非满槽（0x100a7ac..7d8）'
    if ((left & 8192 and right & 49152) or
            (right & 8192 and left & 49152)):
        return ('CanKSympathy|CanSSympathy：为真排除bit13，'
                '为假排除bit14/15（0x100a5b0..5d8、0x100ab70..abac）')
    return None


def eligible(records, *, hp=50, chain=1, stage=0, count=0, counts=None):
    result = []
    counts = counts or {}
    for raw in records:
        pid = raw['patternid']
        if not raw.get('hpstart', 0) <= hp <= raw.get('hpend', 0):
            continue
        if raw.get('bgf', 0) and not raw['bgf'] & stage:
            continue
        if raw.get('limit', 0) and counts.get(pid, 0) >= raw['limit']:
            continue
        low, high = raw.get('mns', 0), raw.get('mne', 0)
        if (low or high) and not low <= count <= high:
            continue
        low, high = raw.get('chs', 0), raw.get('che', 0)
        if (low or high) and not low <= chain <= high:
            continue
        result.append(raw)
    return result


def choose(rows, draw=0):
    acc = 0
    for raw in rows:
        before = acc
        acc += raw.get('priority', 0)
        if before <= draw < acc:
            return raw['patternid']
    return rows[0]['patternid'] if rows else None


def all_choices(rows):
    total = sum(r.get('priority', 0) for r in rows)
    # All integer draws, not merely endpoints or maximum-weight candidates.
    return {choose(rows, draw) for draw in (range(total) if total else [0])}


def zero(records, fields):
    return all(r.get(field, 0) == 0 for r in records for field in fields)


def terrain_label(mask, terrain):
    names = sorted({x['raw']['bg_name'] for x in terrain
                    if x['raw']['flag'] & mask})
    exact = {
        4: ('森林', '森林夜'), 16: ('砂漠', '砂漠夜'),
        192: ('ほこら', '洞窟', '遺跡'),
        262656: ('城中', '街中', '街中夜'), 32768: ('高地',),
        1114112: ('海中', '砂浜', '砂浜夜', '船上', '船上夜'),
        1179648: ('海中', '砂浜', '砂浜夜', '船上', '船上夜'),
    }
    labels = {4: '森林（含夜间）', 16: '沙漠（含夜间）',
              192: '祠堂／洞窟／遗迹', 262656: '城中／街中（含夜间）',
              32768: '高地', 1114112: '沙滩／船上／海中（含夜间）',
              1179648: '沙滩／船上／海中（含夜间）'}
    if mask == 8192 and names and all('夜' in n for n in names):
        return '夜间', names
    if mask in exact and tuple(names) == exact[mask]:
        return labels[mask], names
    return None, names


def model(records, terrain):
    """Admit bounded exact deterministic families; record counterexamples otherwise."""
    result = {'selectionResolved': False, 'conditionGap': '', 'probes': []}
    labels, order, unavailable = {}, {}, set()
    ids = [r['patternid'] for r in records]
    n = len(ids)
    full_hp = all(r.get('hpstart', 0) == 0 and r.get('hpend', 0) == 100
                  for r in records)
    weights = [r.get('priority', 0) for r in records]
    limits = [r.get('limit', 0) for r in records]
    kind = None
    # Complete ordered controller prefix. Parent/child names or amounts play no
    # role in this proof; all actual same-mode refs are included.
    if (n >= 2 and full_hp and zero(records, ('bgf', 'mns', 'mne', 'chs', 'che'))
            and sorted(limits) == [0] + [1] * (n - 1)
            and sum(w > 0 for w in weights) == 1):
        counts = dict.fromkeys(ids, 0)
        sequence = []
        for cast in range(n + 2):
            rows = eligible(records, counts=counts)
            picks = all_choices(rows)
            assert len(picks) == 1
            picked = picks.pop()
            result['probes'].append({'cast': cast + 1, 'countsBefore': counts.copy(),
                                     'eligibleIds': [r['patternid'] for r in rows],
                                     'allRandomDrawsSelect': picked})
            sequence.append(picked)
            counts[picked] += 1
        terminal = records[limits.index(0)]['patternid']
        complete_sequence = (len(set(sequence[:n])) == n and set(sequence[:n]) == set(ids)
                             and sequence[n - 1:] == [terminal] * 3)
        if complete_sequence:
            kind = 'complete_linear_controller_lifetime'
        prose = ''.join(r.get('sinfo', '') for r in records)
        max_prose = set(map(int, re.findall(r'最大(\d+)回', prose))) == {n - 1}
        strength_prose = bool(re.search(r'使用.*(?:上が|変動)', prose))
        for index, pid in enumerate(sequence[:n] if complete_sequence else []):
            order[pid] = index
            if max_prose and strength_prose:
                labels[pid] = '初始' if index == 0 else f'使用后强化{index}次' + ('（最大）' if index == n - 1 else '')
            else:
                labels[pid] = ('初次施放' if index == 0 else
                               f'当前技能状态已施放{index}次' + ('及以后' if index == n - 1 else ''))
    # Existing forest-limit3 is a joint model. Generalize only the actual
    # proven weight/base shape, with full background and local-count probes.
    if (kind is None and n == 2 and full_hp
            and zero(records, ('mns', 'mne', 'chs', 'che'))):
        bases = [r for r in records if not r.get('bgf', 0)
                 and not r.get('priority', 0) and not r.get('limit', 0)]
        boosts = [r for r in records if r.get('bgf', 0) > 0 and r.get('priority', 0) > 0]
        if len(bases) == len(boosts) == 1:
            base, boost = bases[0], boosts[0]
            name, names = terrain_label(boost['bgf'], terrain)
            cap = boost.get('limit', 0)
            if name and cap in (0, 3):
                for background in terrain:
                    bg = background['raw']
                    for uses in (range(cap + 2) if cap else [0]):
                        counts = {boost['patternid']: uses}
                        rows = eligible(records, stage=bg['flag'], counts=counts)
                        expected = boost['patternid'] if bg['flag'] & boost['bgf'] and (not cap or uses < cap) else base['patternid']
                        assert all_choices(rows) == {expected}
                        result['probes'].append({'backgroundId': bg['id'], 'backgroundFlag': bg['flag'],
                                                'backgroundName': bg['bg_name'], 'boostControllerUses': uses,
                                                'allRandomDrawsSelect': expected})
                if cap:
                    counts = {boost['patternid']: 0, base['patternid']: 0}
                    for flag, expected in [(boost['bgf'], boost['patternid']), (0, base['patternid']),
                                           (boost['bgf'], boost['patternid']), (boost['bgf'], boost['patternid']),
                                           (boost['bgf'], base['patternid'])]:
                        assert all_choices(eligible(records, stage=flag, counts=counts)) == {expected}
                        counts[expected] += 1
                labels[boost['patternid']] = f'{name}' + (f'，该地形分支已用不足{cap}次' if cap else '')
                labels[base['patternid']] = f'其他地形（非{name}）' + (f'，或该地形分支已用满{cap}次' if cap else '')
                order = {boost['patternid']: 1, base['patternid']: 0}
                kind = 'full_terrain_weight_pair' if not cap else 'full_terrain_local_limit_pair'
                result['terrain'] = {'mask': boost['bgf'], 'matchedRawNames': names,
                                     'knownBackgroundDenominator': len(terrain)}
    # Sparse primary JSON zero weight vs positive peer; no thresholds invented.
    if (kind is None and full_hp and zero(records, ('limit', 'bgf', 'mns', 'mne', 'chs', 'che'))
            and sum(w > 0 for w in weights) == 1):
        picks = all_choices(eligible(records))
        assert len(picks) == 1
        selected = picks.pop()
        result['probes'].append({'allRandomDrawsSelect': selected,
                                 'weightsInSourceOrder': weights})
        for pid in ids:
            labels[pid] = '当前选档' if pid == selected else '本模式常规选档不选用'
            order[pid] = 0 if pid == selected else 1
            if pid != selected:
                unavailable.add(pid)
        kind = 'full_unconditional_single_positive_weight'
    # Inclusive mana ranges can reuse M1-M6 algorithm for new exact families.
    # Neither first-positive nor max-weight is used to hide overlapping ranges.
    if (kind is None and full_hp and zero(records, ('limit', 'bgf', 'chs', 'che'))
            and not zero(records, ('mns', 'mne'))):
        intervals = sorted((r.get('mns', 0), r.get('mne', 0), r['patternid']) for r in records)
        valid = all(-1 <= low <= high <= 12 for low, high, _ in intervals)
        probes = []
        for count in range(13):
            rows = eligible(records, count=count)
            picks = all_choices(rows)
            total = sum(r.get('priority', 0) for r in rows)
            distribution = Counter(choose(rows, draw) for draw in (range(total) if total else [0]))
            probes.append({'selectorCount': count, 'eligibleIds': [r['patternid'] for r in rows],
                           'possibleSelectedIds': sorted(picks, key=lambda x: -1 if x is None else x),
                           'drawDenominator': total or 1,
                           'selectedDrawCounts': dict(distribution)})
        result['probes'].extend(probes)
        if valid and all(len(p['possibleSelectedIds']) == 1 and p['possibleSelectedIds'][0] is not None for p in probes):
            scrap = bool(records[0].get('flag', 0) & 256)
            selected_ranges = []
            for pid in ids:
                counts = [p['selectorCount'] for p in probes if p['possibleSelectedIds'] == [pid]]
                if not counts:
                    valid = False
                    break
                low, high = min(counts), max(counts)
                if counts != list(range(low, high + 1)):
                    valid = False
                    break
                selected_ranges.append((low, high, pid))
            for index, (low, high, pid) in enumerate(sorted(selected_ranges) if valid else []):
                labels[pid] = f'选档时废料{low}–{high}个' if scrap else f'预测扣费后职业法珠{low}–{high}颗'
                order[pid] = index
            if valid:
                kind = 'full_deterministic_prediction_counter_ranges'
        if (kind is None and valid and all(p['eligibleIds'] for p in probes)):
            # Overlapping nonzero weights are a fully described random pool,
            # not a deterministic tier. Retain exact conditional fractions.
            # Counts are selector snapshots, never guaranteed click frequencies.
            scrap = bool(records[0].get('flag', 0) & 256)
            for index, pid in enumerate(ids):
                counts = [p['selectorCount'] for p in probes if pid in p['possibleSelectedIds']]
                if not counts:
                    labels[pid] = '本模式常规选档不选用'
                    unavailable.add(pid)
                else:
                    spans = []
                    for value in counts:
                        if spans and value == spans[-1][1] + 1:
                            spans[-1][1] = value
                        else:
                            spans.append([value, value])
                    text = '／'.join(f'{low}–{high}' for low, high in spans)
                    label = f'选档时废料{text}个' if scrap else f'预测扣费后职业法珠{text}颗'
                    labels[pid] = label + '；每次预测按有效候选权重随机选档'
                order[pid] = min(counts) if counts else 13 + index
            kind = 'full_weighted_prediction_counter_pool'
            result['counterDomain'] = '当前非负selectorCounter的0..12闭区间；超出12不推广'
        else:
            overlaps = [p for p in probes if len(p['possibleSelectedIds']) > 1]
            result['conditionGap'] = ('法珠区间有重叠且存在多个可抽中父，不能改写成唯一档；'
                                      + f'反例计数{overlaps[0]["selectorCount"]}可选{overlaps[0]["possibleSelectedIds"]}'
                                      if overlaps else '法珠范围未形成0..12确定且连续的逐父选中区间；不能补齐未覆盖/特殊负值含义')
    if (kind is None and full_hp and zero(records, ('limit', 'bgf', 'mns', 'mne', 'chs', 'che'))
            and n >= 2 and all(w > 0 for w in weights)):
        total = sum(weights)
        draws = {pid: [] for pid in ids}
        for draw in range(total):
            draws[choose(records, draw)].append(draw)
        assert set(draws) == set(ids) and all(len(draws[pid]) == weights[index] for index, pid in enumerate(ids))
        for index, pid in enumerate(ids):
            labels[pid] = f'普通UI每次预测随机选档（权重{weights[index]}/{total}）'
            order[pid] = index
            result['probes'].append(dict(parentId=pid, integerDrawRange=[min(draws[pid]), max(draws[pid])],
                                         selectedDrawCount=len(draws[pid]), totalDraws=total))
        kind = 'full_weighted_random_pool_at_prediction'
    # HP/Chain parents may already show known; recheck full same-mode selection.
    if kind is None and zero(records, ('limit', 'bgf', 'mns', 'mne')):
        probes, bad = [], None
        has_gates = not zero(records, ('hpstart', 'chs', 'che')) or any(r.get('hpend', 0) != 100 for r in records)
        if has_gates:
            for hp in range(101):
                for chain in range(6):
                    rows = eligible(records, hp=hp, chain=chain)
                    picks = all_choices(rows)
                    # Empty states are disclosed, not assigned to a base.
                    if len(rows) > 1:
                        bad = {'hpCentile': hp, 'selectorChainCount': chain,
                               'eligibleIds': [r['patternid'] for r in rows], 'possibleSelectedIds': sorted(picks)}
                        break
                    probes.append({'hpCentile': hp, 'selectorChainCount': chain,
                                   'selected': next(iter(picks)) if picks else None})
                if bad:
                    break
            result['probes'].extend(probes)
            if bad:
                result['counterexample'] = bad
                result['conditionGap'] = '同一HP/Chain状态仍有多个候选，现有阈值仅为必要门；需单独推导完整权重后的选择区间'
            else:
                for index, raw in enumerate(records):
                    pid = raw['patternid']
                    parts = []
                    low, high = raw.get('hpstart', 0), raw.get('hpend', 0)
                    if low != 0 or high != 100:
                        parts.append(f'HP整数百分比{low}–{high}%')
                    low, high = raw.get('chs', 0), raw.get('che', 0)
                    if low or high:
                        names = {0: 'Chain无效或已连锁重置0', 1: '0thChain', 2: '1stChain',
                                 3: '2ndChain', 4: '3rdChain', 5: 'MaxChain'}
                        parts.append(names[low] if low == high else f'{names[low]}–{names[high]}')
                    labels[pid] = ' · '.join(parts) or '本模式常规选档'
                    order[pid] = index
                kind = 'full_hp_chain_deterministic_partition'
    if kind:
        result.update(selectionResolved=True, selectionKind=kind, labels=labels,
                      orders=order, unavailable=sorted(unavailable), conditionGap='')
    elif not result['conditionGap']:
        result['conditionGap'] = ('完整同模式父集合不符合已证确定性模板；需核实际随机池/附加状态语义，'
                                  f'权重={weights}、limit={limits}')
    return result


def run(out):
    pin(Path(__file__).relative_to(ROOT).as_posix())
    invrel = FINAL + 'inventory.json'
    inv = read(invrel)
    selected = [(i, item) for i, item in enumerate(inv['items']) if item['review']['status'] == 'purple']
    assert len(selected) == 760
    # review_confidence rebuilds its current inventory. Keep that observational
    # hash in provenance, but validate an immutable copy at consumption time.
    out.mkdir(parents=True, exist_ok=True)
    baseline = out / 'baseline_inventory.json'
    baseline_bytes = (ROOT / invrel).read_bytes()
    baseline_digest = INPUTS[invrel]
    assert hashlib.sha256(baseline_bytes).hexdigest() == baseline_digest
    if baseline.exists():
        assert baseline.read_bytes() == baseline_bytes, 'Use a new versioned output directory for a changed baseline'
    else:
        baseline.write_bytes(baseline_bytes)
    baseline_rel = baseline.resolve().relative_to(ROOT).as_posix()
    pin(baseline_rel, baseline_digest)
    proof = read(SELECT + 'native_selection_proof.json')
    native = 'work/protection/il2cpp_loader_seed1.bin'
    metadata = 'work/protection/metadata_aei_decoded.bin'
    pin(native, proof['nativeSHA256'])
    pin(metadata, proof['metadataSHA256'])
    mana = read(SELECT + 'mana_timing_receipt.json')
    sparse = read(FINAL + 'sparse_receipt.json')
    hp_proof = read(AUDIT + 'player_conditions_20261107/native_conditions.json')
    assert hp_proof['native_sha256'] == proof['nativeSHA256']
    assert hp_proof['metadata_sha256'] == proof['metadataSHA256']
    for receipt in (mana, sparse):
        for rel, digest in receipt.get('methodExcerptHashes', {}).items():
            pin(rel, digest)
    for rel in ('4927_getPatternAttackList.txt', '4928_think_attack.txt',
                '4090_makeExAttackPatternList.txt', '5174_CreateExecSkillList.txt',
                '5176_FindPatternCtrl.txt', '9116_GetExecSkillInfo.txt', 'setListPattern.txt'):
        pin(SELECT + rel)
    pin(AUDIT + 'player_conditions_20261107/native_conditions.txt')
    terrain = read('output/ordinary_effects/ability7/trace.json')
    assert terrain['native_sha256'] == proof['nativeSHA256']
    backgrounds = terrain['background_source_records']
    tables = {}
    for layer, bossfile, charfile, skillfile in [
        ('APK', 'output/base_master/_mdBossInfo.json', 'output/base_master/_mdCharacter.json', 'output/base_master/_mdSkill.json'),
        ('CACHE', 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw',
         'output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw',
         'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')]:
        boss = read(bossfile)
        boss = boss if layer == 'APK' else boss['bossinfo']
        tables[layer] = dict(file=bossfile, prefix='' if layer == 'APK' else '/bossinfo',
                             parents=indexed(boss['bosspattern'], 'patternid'),
                             boss=indexed(boss['bossskill'], 'skillid'), charfile=charfile,
                             chars=indexed(read(charfile)['charainfo'], 'cid'), skillfile=skillfile,
                             abilities=indexed(read(skillfile)['skilllist'], 'skillid'))
    output_items, parents, cohorts = [], {}, {}
    for original_index, old in selected:
        source = old['source']
        bind = binding(source)
        origin = source.get('allSources') or {}
        layer = source.get('layer') or origin.get('layer') or bind.get('layer')
        pid = source.get('branchId') or bind.get('pattern_id') or (bind.get('parent_chain') or {}).get('pattern_id')
        item = dict(originalInventoryIndex=original_index, identity=identity(old),
                    cid=old['cid'], rowId=old['rowId'], effect=old['effect'], text=old['text'],
                    source=source, before=old['review'], parentKey=f'{layer}:{pid}' if pid else None,
                    selectionResolved=False, conditionGap='')
        cardrel = f'output/character_skills/pages/{old["cid"]}/card.json'
        card = read(cardrel)
        item['mainlineCard'] = dict(file=cardrel, sha256=INPUTS[cardrel])
        if old['review']['bindingKind'] == 'count_scaling':
            data = source['originalBinding']['inference_c11_p2_union_count']
            item.update(conditionGap='能力人数增长比例与人数上限未符号化；父必杀selector证据不能消除此缺口',
                        abilityThresholdKnown=data.get('condition'), abilityFilterKnown=data.get('filter'),
                        preservedUnknowns=data.get('disclosure'), selectionApplicability='OUTSIDE_BOSS_SELECTOR')
            output_items.append(item)
            continue
        meta = tables.get(layer)
        if pid is None and meta is not None:
            # An exact C19 row source and matching real child edge can restore
            # the parent identity (30310); a name/number in prose cannot.
            hits = []
            childid = source.get('recordId') or origin.get('record_id')
            for group in card['groups']:
                for skill in group['skills']:
                    if skill.get('table') != 'bosspattern' or skill.get('layer') != layer:
                        continue
                    rows = [r for r in skill.get('rows', []) if r['row_id'] == old['rowId']]
                    found = meta['parents'].get(skill.get('record_id'))
                    child = meta['boss'].get(childid)
                    if (len(rows) == 1 and found and child
                            and any(v == childid for k, v in found[1].items() if re.fullmatch(r'skillid\d+', k))
                            and source.get('field', '/')[1:] in child[1]
                            and child[1][source['field'][1:]] == source.get('raw')):
                        hits.append(skill['record_id'])
            if len(set(hits)) == 1:
                pid = hits[0]
                item['parentKey'] = f'{layer}:{pid}'
                item['parentIdentityRecovery'] = 'C19精确row_id所属父、同层原表父子边及源字段原值一致；不证明效果绑定'
        if meta is None or pid not in meta['parents'] or old['cid'] not in meta['chars']:
            item['conditionGap'] = '未能以原source/originalBinding在同层原表唯一恢复父或charainfo；不猜父ID'
            output_items.append(item)
            continue
        charindex, chara = meta['chars'][old['cid']]
        refs = sorted(((int(k[7:]), k, v) for k, v in chara.items()
                       if re.fullmatch(r'pattern\d+', k) and isinstance(v, int) and v), key=lambda x: x[0])
        refids = [v for _, _, v in refs]
        pindex, raw = meta['parents'][pid]
        item['parentRaw'] = raw
        item['parentSource'] = dict(file=meta['file'], pointer=f'{meta["prefix"]}/bosspattern/{pindex}')
        key = f'{old["cid"]}:{layer}:{raw.get("flag", 0)}'
        item['cohortKey'] = key
        if '-denju-' in old['rowId'] and pid not in refids:
            item.update(selectionApplicability='DENJU_DISTINCT_CONTROLLER_LIST',
                        conditionGap='传授父由denju.patternid0独立引用，不在charainfo控制器集合；本轮不把普通必杀完整父分母移植到传授。原条件保留，效果多载体绑定缺口仍在。',
                        conditionPreviouslyKnownButNotReproved=True)
            output_items.append(item)
            continue
        if key not in cohorts:
            problems = []
            if pid not in refids:
                problems.append('目标父不在该层charainfo真实pattern引用中')
            if len(refids) != len(set(refids)):
                problems.append('charainfo重复引用同父，需核重复控制器及FindPatternCtrl首命中')
            missing = [ident for ident in refids if ident not in meta['parents']]
            if missing:
                problems.append(f'同层完整父集合缺记录{missing}，不可逐字段混入另一层')
            flag = raw.get('flag', 0)
            if flag not in SUPPORTED_FLAGS:
                problems.append(f'目标flag={flag}含未准入模式/状态位，需核对应消费链')
            records, allparents, excluded = [], [], []
            for _, field, ident in refs:
                if ident not in meta['parents']:
                    continue
                ix, pr = meta['parents'][ident]
                childrows = []
                for slot, childid in pr.items():
                    if not re.fullmatch(r'skillid\d+', slot) or not childid:
                        continue
                    got = meta['boss'].get(childid)
                    child = got[1] if got else None
                    attached = []
                    todo = [child.get('s_ability')] if child and child.get('s_ability') else []
                    seen = set()
                    while todo:
                        aid = todo.pop(0)
                        if aid in seen:
                            continue
                        seen.add(aid)
                        found = meta['abilities'].get(aid)
                        ar = found[1] if found else None
                        attached.append(dict(recordId=aid, raw=ar,
                                             source=dict(file=meta['skillfile'], pointer=f'/skilllist/{found[0]}') if found else None))
                        if ar:
                            todo.extend(v for v in ar.get('sub', []) if v)
                    childrows.append(dict(slot=slot, recordId=childid, raw=child,
                                          source=dict(file=meta['file'], pointer=f'{meta["prefix"]}/bossskill/{got[0]}') if got else None,
                                          attachedAbilityClosure=attached))
                descriptor = dict(referenceField=field, parentId=ident, raw=pr,
                                  source=dict(file=meta['file'], pointer=f'{meta["prefix"]}/bosspattern/{ix}'),
                                  executors=childrows)
                allparents.append(descriptor)
                if pr.get('flag', 0) == flag:
                    records.append(pr)
                else:
                    exclusion = exclusive(flag, pr.get('flag', 0))
                    excluded.append(dict(parentId=ident, flag=pr.get('flag', 0), exclusion=exclusion))
                    if not exclusion:
                        problems.append(f'不同flag父{ident}(flag={pr.get("flag", 0)})未证明与目标互斥，不能按同名排除')
            for pr in records:
                nulls = [f for f in FIELDS if f in pr and pr[f] is None]
                if nulls:
                    problems.append(f'父{pr["patternid"]}显式null字段{nulls}不按缺键0处理')
                if layer == 'APK' and any(f not in pr for f in FIELDS):
                    problems.append(f'APK父{pr["patternid"]}缺字段，CACHE primary默认不能移植到AB')
                if any(pr.get(f, 0) for f in ('posp', 'pose', 'tid')):
                    problems.append(f'父{pr["patternid"]}含位置门/形态tid，需核精确位置消费或形态切换链')
                if any(not isinstance(pr.get(f, 0), (int, float)) for f in FIELDS):
                    problems.append(f'父{pr["patternid"]}含非数值状态字段')
                elif (pr.get('priority', 0) < 0 or pr.get('limit', 0) < 0
                      or not 0 <= pr.get('hpstart', 0) <= pr.get('hpend', 0) <= 100
                      or not 0 <= pr.get('chs', 0) <= pr.get('che', 0) <= 5):
                    problems.append(f'父{pr["patternid"]}状态/权重超出已证准入值域')
            pageids = {s['record_id'] for g in card['groups'] if g['group'] == 'special_move'
                       for s in g['skills'] if s.get('table') == 'bosspattern'}
            result = (dict(selectionResolved=False, conditionGap='；'.join(dict.fromkeys(problems)), probes=[])
                      if problems else model(records, backgrounds))
            cohorts[key] = dict(cid=old['cid'], layer=layer, flag=flag,
                                characterSource=dict(file=meta['charfile'], pointer=f'/charainfo/{charindex}',
                                                     patternReferencesInNativeOrder=[{k: v} for _, k, v in refs]),
                                completeCharacterParentIds=refids, allParents=allparents,
                                actualSameModeParentIds=[r['patternid'] for r in records],
                                differentFlagExclusions=excluded,
                                currentC19PageParentIds=sorted(pageids),
                                currentC19PageMatchesThisLayer=set(refids) == pageids,
                                sourceLayerNote='以候选实际层为分母，C19采用另一层时不把两层引用强行混合；对账差异另存。',
                                fieldPresence={r['patternid']: {f: 'missing-runtime0' if f not in r else ('explicit-null' if r[f] is None else 'present') for f in FIELDS} for r in records},
                                executionScope='完整子执行槽与s_ability/sub闭包仅披露，不据附加链差异改写原效果绑定；选择器在加入候选前不读取这些子记录。',
                                **result)
        cohort = cohorts[key]
        item['selectionResolved'] = cohort['selectionResolved']
        item['conditionGap'] = cohort['conditionGap']
        if old['review'].get('randomPoolKnown'):
            item['conditionGap'] = '普通随机池已证；动画sp_komodia01/02/03与真实卡面映射、状态位消费仍缺证'
            item['selectionResolved'] = False
        if item['selectionResolved']:
            label = cohort['labels'][pid]
            fact = ('完整同层charainfo引用、不同flag互斥、原生资格门与权重/计数逐态枚举通过；'
                    '父选择结论不消费效果量大小、同名或附加链相等假设。')
            parent = dict(cid=old['cid'], branchId=pid, parentRaw=raw,
                          parentSource=item['parentSource'], selectionResolved=True,
                          conditionLabel=label, selectionOrder=cohort['orders'][pid],
                          selectionKind=cohort['selectionKind'], reason=fact, scope=SCOPE,
                          limits=LIMITS, selectionUnavailable=pid in cohort.get('unavailable', []),
                          cohortKey=key, evidence=[SELECT + 'native_selection_proof.json',
                                                 SELECT + 'mana_timing_receipt.json',
                                                 FINAL + 'sparse_receipt.json'])
            if cohort['selectionKind'] == 'full_weighted_prediction_counter_pool':
                parent['predictionProbabilityByCount'] = [
                    dict(selectorCount=p['selectorCount'], numerator=p['selectedDrawCounts'].get(pid, 0),
                         denominator=p['drawDenominator'], eligibleIds=p['eligibleIds']) for p in cohort['probes']]
                parent['limits'] = LIMITS + ['抽选分布仅指每次预测调用；不解释为实际点击/施放频率，也不推广到计数大于12。']
            if cohort['selectionKind'] in ('full_terrain_weight_pair', 'full_terrain_local_limit_pair'):
                parent['limits'] = LIMITS + [f'地形名称仅覆盖当前原表的{len(backgrounds)}条背景；未知背景不泛化。']
            pkey = item['parentKey']
            if pkey in parents:
                assert parents[pkey]['parentRaw'] == raw
                assert parents[pkey]['conditionLabel'] == label, f'Context-specific conflicting label: {pkey}'
            parents[pkey] = parent
            item.update(conditionLabel=label, selectionOrder=parent['selectionOrder'],
                        selectionKind=parent['selectionKind'], selectionUnavailable=parent['selectionUnavailable'])
        item['bindingStillUnknown'] = not old['review']['bindingKnown']
        item['numericStillUnknown'] = not old['review']['numericKnown']
        item['eligibleToInferAfterBindingRecheck'] = bool(item['selectionResolved'] and
                                                        old['review']['bindingKnown'] and old['review']['numericKnown'])
        item['conditionPreviouslyKnownButNotReproved'] = bool(old['review']['conditionKnown'] and not item['selectionResolved'])
        output_items.append(item)
    assert len(output_items) == 760
    assert len({json.dumps(x['identity'], ensure_ascii=False) for x in output_items}) == 760
    # Display labels also apply to ordinary source answers in the same proven
    # cohort. Keep the original candidate-only map and its statistics intact.
    # A cohort rejected by a per-item guard (278's missing card-face mapping)
    # cannot enter this wider consumer map merely because its random pool exists.
    resolved_cohort_parents = {}
    accepted_cohorts = {parent['cohortKey'] for parent in parents.values()}
    cohort_coverage = {}
    for cohort_key in sorted(accepted_cohorts):
        cohort = cohorts[cohort_key]
        assert cohort['selectionResolved']
        template = next(parent for parent in parents.values() if parent['cohortKey'] == cohort_key)
        descriptors = {record['parentId']: record for record in cohort['allParents']}
        assert set(cohort['labels']) == set(cohort['actualSameModeParentIds'])
        assert set(cohort['orders']) == set(cohort['labels'])
        covered = []
        for pid, label in cohort['labels'].items():
            descriptor = descriptors[pid]
            parent = dict(template, branchId=pid, parentRaw=descriptor['raw'],
                          parentSource=descriptor['source'], conditionLabel=label,
                          selectionOrder=cohort['orders'][pid],
                          selectionUnavailable=pid in cohort.get('unavailable', []))
            if cohort['selectionKind'] == 'full_weighted_prediction_counter_pool':
                parent['predictionProbabilityByCount'] = [
                    dict(selectorCount=p['selectorCount'], numerator=p['selectedDrawCounts'].get(pid, 0),
                         denominator=p['drawDenominator'], eligibleIds=p['eligibleIds']) for p in cohort['probes']]
            parent_key = f'{cohort["layer"]}:{pid}'
            if parent_key in resolved_cohort_parents:
                assert resolved_cohort_parents[parent_key] == parent, f'Conflicting full-cohort parent: {parent_key}'
            if parent_key in parents:
                assert parents[parent_key] == parent, f'Candidate parent changed: {parent_key}'
            resolved_cohort_parents[parent_key] = parent
            covered.append(parent_key)
        cohort_coverage[cohort_key] = covered
    assert set(parents) <= set(resolved_cohort_parents)
    cohort_parent_validation = dict(
        acceptedCohorts=len(accepted_cohorts), resolvedCohortParents=len(resolved_cohort_parents),
        additionalNonCandidateParents=len(set(resolved_cohort_parents) - set(parents)),
        completeCoverageByCohort=cohort_coverage,
        perItemGuardPreserved=[key for key, cohort in cohorts.items()
                               if cohort['selectionResolved'] and key not in accepted_cohorts])
    counterexamples = [
        dict(name='weights-not-max', passed=all_choices([{'patternid': 1, 'priority': 100}, {'patternid': 2, 'priority': 50}]) == {1, 2}),
        dict(name='all-zero-preserves-order', passed=choose([{'patternid': 2}, {'patternid': 1}]) == 2),
        dict(name='missing-hpend-not100', passed=eligible([{'patternid': 1}], hp=1) == []),
        dict(name='same-name-does-not-exclude-different-flag', passed=exclusive(8192, 8448) is None),
        dict(name='ordinary-super-gauge-exclusive', passed=exclusive(8, 4) is not None),
        dict(name='sympathy-mode-exclusive', passed=exclusive(8192, 32768) is not None),
        dict(name='same-mode-extra-bit-not-exclusive', passed=exclusive(8192, 9216) is None),
        dict(name='overlapping-mana-keeps-two-choices', passed=len(all_choices(eligible([{'patternid': 1, 'hpend': 100, 'mne': 6, 'priority': 100}, {'patternid': 2, 'hpend': 100, 'mns': 3, 'mne': 12, 'priority': 100}], count=4))) == 2),
    ]
    assert all(x['passed'] for x in counterexamples)
    stats = dict(denominator=len(output_items), parentDenominator=len({i['parentKey'] for i in output_items if i['parentKey']}),
                 conditionResolved=sum(x['selectionResolved'] for x in output_items),
                 newConditionResolved=sum(x['selectionResolved'] and not x['before']['conditionKnown'] for x in output_items),
                 eligibleToInferAfterBindingRecheck=sum(x.get('eligibleToInferAfterBindingRecheck', False) for x in output_items),
                 bindingRemainsUnknownAfterCondition=sum(x['selectionResolved'] and not x['before']['bindingKnown'] for x in output_items),
                 resolvedParents=len(parents), fullCohorts=len(cohorts),
                 models=dict(Counter(x.get('selectionKind') for x in output_items if x['selectionResolved'])),
                 beforeReasons=dict(Counter(x['before']['shortReason'] for x in output_items)),
                 unresolvedReasons=dict(Counter(x['conditionGap'] for x in output_items if not x['selectionResolved'])))
    report = dict(schema=1, scope=SCOPE, limits=LIMITS,
                  baselineInventory=dict(file=invrel, sha256=baseline_digest, snapshotFile=baseline_rel),
                  baselineStats=inv['stats'], stats=stats, inputs=INPUTS,
                  nativeCallPath={'load': sparse['sourceLoaderFacts'],
                                  'ordinaryUI': mana['facts'],
                                  'weightedAndCount': proof['semantics'],
                                  'sameLayerPolicy': 'APK与CACHE分别建立真实charainfo父集合；不用当前页面选中层替换历史候选层。'},
                  counterexamples=counterexamples, parents=parents,
                  resolvedCohortParents=resolved_cohort_parents,
                  resolvedCohortParentValidation=cohort_parent_validation,
                  cohorts=cohorts, items=output_items)
    for rel, digest in INPUTS.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, f'Source changed: {rel}'
    # Mutable producer output is no longer an active dependency after snapshot.
    del INPUTS[invrel]
    out.mkdir(parents=True, exist_ok=True)
    (out / 'condition_closeout_receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'summary.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/reader_condition_closeout/run_20261107_r05')
    run(parser.parse_args().output)
