"""Apply an independently accepted mainline delta to an isolated reader snapshot."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from html import escape
from pathlib import Path
import json
import re
import shutil
import sys
import tempfile

from build import dump, js, read, rows
from incremental_frontend import build_frontend, digest
from presentation import answer, effect_label, num

ROOT = Path(__file__).resolve().parents[2]
FORMAL = ROOT / 'output/character_skills'
TEMPLATE = FORMAL / 'reader_full_20261106'
READER = ROOT / 'projects/reader'
RUNTIME = ('index.html', 'app.js', 'branches.js', 'inline.js', 'levels.js', 'style.css')
ROW_STATE = {'answers', 'association_evidence', 'numeric_evidence', 'unknown_reasons',
             'evidence_scope', 'row_class', 'partial', 'inference_yg1'}
ROW_STATUS = {'完整':'complete', '部分':'partial', '未解析':'unparsed', '拆分待核查':'review'}


class ReviewNeeded(ValueError):
    """A changed card whose semantics cannot be carried forward automatically."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def review(condition, message):
    if not condition:
        raise ReviewNeeded(message)


def payload(path):
    sep = ']=' if path.parent.name == 'cards' else '='
    return json.loads(path.read_text(encoding='utf-8-sig').split(sep, 1)[1].strip().removesuffix(';'))


def source_package(manifest_path, verdict_path):
    m, v = read(manifest_path), read(verdict_path)
    require(v.get('verdict') in ('PASS', 'PASS_WITH_EXPLICIT_SCOPE_LIMITS'),
            'Independent formal acceptance is absent')
    require(v.get('f01_status', 'CLOSED') == 'CLOSED' and not v.get('blockers') and
            not v.get('blocking') and not v.get('blocking_count'),
            'Independent verdict has open findings')
    report_path = manifest_path.parent / 'report_data.json'
    require(digest(report_path) == m['files']['report_data.json']['sha256'], 'Accepted delta hash differs')
    d = read(report_path)
    require((m['snapshot'], m['campaign']) == (d['snapshot'], d['campaign']), 'Accepted delta snapshot differs')
    entries = [r for batch in d['batch_results'] for r in batch['rows']]
    changes = {r['row_id']: r for r in entries}
    require(len(changes) == len(entries), 'Duplicate accepted row')
    if isinstance(m.get('scope', {}).get('answers'), int):
        n = sum(len(r['after']['answers']) - len((r.get('before') or {}).get('answers', [])) for r in entries)
        require(n == m['scope']['answers'], 'Accepted answer denominator differs')
    evidence = []
    if v.get('submitted_manifest_sha256') is not None:
        require(v['submitted_manifest_sha256'] == digest(manifest_path),
                'Independent verdict does not bind the supplied final manifest')
    else:
        evidence = verify_pre_delivery_review(manifest_path, verdict_path, m, v, entries)
    return m, d, changes, evidence


def verify_pre_delivery_review(manifest_path, verdict_path, manifest, verdict, rows):
    """A review run before report packaging binds the delta via its own answer ledger."""
    formal = manifest.get('reviews', {}).get('formal_final')
    require(isinstance(formal, str) and (ROOT/formal).resolve() == (verdict_path.parent/'REPORT.md').resolve(),
            'Independent verdict does not bind the supplied final manifest')
    folder = verdict_path.parent
    handoff = manifest_path.parent/'handoff_verification.json'
    delivery = read(handoff)
    require(delivery.get('status') in ('PASS','PASS_WITH_EXPLICIT_SCOPE_LIMITS') and
            delivery.get('final_manifest_sha256') == digest(manifest_path) and
            delivery.get('registered_files') == len(manifest['files']) and
            all(delivery.get('checks', {}).values()), 'Delivery handoff does not match the final manifest')
    files = []
    for name, item in manifest['files'].items():
        p = (manifest_path.parent/name).resolve()
        require(p.is_relative_to(manifest_path.parent.resolve()) and
                p.stat().st_size == item['bytes'] and digest(p) == item['sha256'], 'Delivery file differs: ' + name)
        files.append(p)
    evidence, independent, run_log = (folder/n for n in ('evidence.json','answer_ledger.json','run_log.json'))
    checks, audited, log = read(evidence)['checks'], read(independent), read(run_log)
    n = sum(len(r['after']['answers'])-len(r['before']['answers']) for r in rows)
    require(n > 0 and n == verdict['independent_recomputations'] == audited['count'] ==
            audited['formal_match'] == audited['candidate_match'], 'Independent answer count differs')
    require(log['exit_code'] == 0 and log['verdict'] == verdict['verdict'] and
            len(checks) == verdict['checks_total'] == verdict['checks_passed'] ==
            log['checks_total'] == log['checks_passed'] and all(x['ok'] is True for x in checks),
            'Independent execution or checks did not pass')
    require(any(isinstance(x['detail'], dict) and x['detail'].get('campaign') == manifest['campaign']
                and x['detail'].get('campaign_complete') is True for x in checks),
            'Independent evidence does not identify the accepted completed campaign')

    expected = Counter()
    for row in rows:
        rid = row['row_id']
        for a in row['after']['answers'][len(row['before']['answers']):]:
            ids = {b['effect_id'] for b in a['binding'].values() if isinstance(b, dict)
                   and b.get('row_id') == rid and b.get('effect_id')}
            require(len(ids) == 1, 'Accepted answer effect is ambiguous: ' + rid)
            s = a['source']
            expected[(str(row['cid']), rid, ids.pop(), a['layer'], a['record_id'], a['field_path'],
                      a['raw_value'], a['rule_key'], ''.join(a['unit'].split()),
                      s['json_pointer'], s['raw_record_sha256'])] += 1
    observed = Counter((str(a['cid']), a['row_id'], a['effect_id'], a['layer'], a['record_id'],
                        '/' + a['field'].lstrip('/'), a['raw'], a['rule_key'], ''.join(a['unit'].split()),
                        a['pointer'], a['raw_record_sha256']) for a in audited['entries']
                       if a['formal_match'] is True and a['candidate_match'] is True)
    require(observed == expected and len(audited['entries']) == n, 'Independent answer ledger differs from delivered delta')
    return [handoff, evidence, independent, run_log, folder/'REPORT.md', *files]


def baseline_reader(path):
    inc = path / 'incremental_receipt.json'
    if inc.exists():
        receipt = read(inc)
        require(receipt.get('schema') == 'reader-incremental-v1' and receipt.get('complete') is True,
                'Baseline reader has unincorporated cards')
        hashes = receipt['runtimeHashes']
    else:
        receipt = read(path / 'build_receipt.json')
        require(receipt.get('validation') == 'PASSED_DATA_ALIGNMENT', 'Unverified reader baseline')
        proof = read(path / 'audit/c19_r01_fix_20261107/sidecar_adaptation.json')
        require(proof['targetSnapshot'] == receipt['snapshot'] and proof['pass'], 'Baseline sidecars are unverified')
        hashes = proof['runtimeHashes']
    require(set(hashes) >= {f'data/cards/{cid}.js' for cid in receipt['sourceHashes']},
            'Baseline runtime hash inventory does not cover the card set')
    for rel, expected in hashes.items():
        p = (path / rel).resolve()
        require(p.is_relative_to(path) and digest(p) == expected, 'Reader baseline hash differs: ' + rel)
    return receipt


def card_hashes(root, accepted_hashes, signature):
    """Check live receipts or the exact card hashes of a frozen accepted input."""
    card_paths = {p.parent.name:p for p in (root/'pages').glob('*/card.json') if p.parent.name.isdigit()}
    hashes = {}
    if accepted_hashes is not None:
        require(set(card_paths) == set(accepted_hashes), 'Frozen card set differs')
    for cid, p in card_paths.items():
        h = digest(p)
        if accepted_hashes is None:
            r = read(p.parent/'receipt.json')
            require(r['status'] == 'SUCCESS' and r['signature'] == signature and
                    r['files']['card.json'] == h and not (p.parent/'reuse_blocked.json').exists(),
                    'Mainline card receipt does not match the accepted snapshot: ' + cid)
        else:
            require(accepted_hashes[cid] == h, 'Frozen card hash differs: ' + cid)
        hashes[cid] = h
    return card_paths, hashes


def read_ledger(path, snapshot, watched, metrics):
    desc, effects, counts = {}, defaultdict(dict), defaultdict(Counter)
    status_count, descriptions = Counter(), Counter()
    with path.open(encoding='utf-8-sig') as stream:
        for line in stream:
            e = json.loads(line)
            require((e.get('snapshot_id') or e.get('input_snapshot', {}).get('snapshot_id')) == snapshot,
                    'Mixed ledger snapshots')
            cid = str(e['cid'])
            if e['record_type'] == 'description':
                kind = e['ledger_row_status']
                descriptions[kind] += 1
                counts[cid][ROW_STATUS[kind]] += 1
                counts[cid]['descriptions'] += 1
                if cid in watched:
                    require(e['row_id'] not in desc, 'Duplicate ledger description')
                    desc[e['row_id']] = e
            elif e['record_type'] == 'effect':
                kind = e['status']
                status_count[kind] += 1
                if kind in ('has_answer','unresolved'):
                    counts[cid]['answer' if kind == 'has_answer' else 'unresolved'] += 1
                if cid in watched:
                    bucket = effects[e['description_ref']]
                    require(e['effect_id'] not in bucket, 'Duplicate ledger effect')
                    bucket[e['effect_id']] = e
    require(dict(descriptions) == metrics['descriptions']['by_ledger_status'], 'Description totals differ')
    require(dict(status_count) == {k:v['all'] for k,v in metrics['effects']['by_status'].items()}, 'Effect totals differ')
    return desc, effects, counts


def delta_proof(a, rid, eid):
    exact = [v for v in (a.get('binding') or {}).values() if isinstance(v, dict)
             and v.get('row_id') == rid and v.get('effect_id') == eid and isinstance(v.get('selected'), dict)]
    if len(exact) != 1:
        return None
    proof = exact[0]
    selected = proof['selected']
    source = a.get('source') or {}
    review(selected.get('source') == source and
           (selected.get('record_id'), selected.get('rule_key'), selected.get('raw_value'),
            selected.get('pattern_id'), '/' + selected.get('field', '')) ==
           (a.get('record_id'), a.get('rule_key'), a.get('raw_value'),
            a['binding'].get('pattern_id'), a.get('field_path')),
           '正式选档与答案来源不一致')
    return proof


def selected_identity(addition, eid, sel):
    s = addition['answer']['source']
    t = sel.get('source') or {}
    if (addition['effectId'], s.get('layer'), s.get('branchId'), s.get('recordId'),
        s.get('rule'), s.get('field'), s.get('raw'), s.get('parentSlot')) != (
            eid, t.get('layer'), sel.get('pattern_id'), sel.get('record_id'),
            sel.get('rule_key'), '/' + sel.get('field', ''), sel.get('raw_value'),
            'skillid' + str(sel.get('child_slot'))):
        return False
    parent = s.get('parentSource') or {}
    condition = s.get('conditionsRaw') or {}
    formal_condition = sel.get('parent_conditions_raw') or {}
    if not (t.get('record_key') and t.get('source_key') and sel.get('pattern_json_pointer')
            and formal_condition and formal_condition.get('patternid') == sel.get('pattern_id')
            and s.get('allSources', {}).get('record_key') == t['record_key']
            and (parent.get('source_key'), parent.get('json_pointer')) ==
                (t['source_key'], sel['pattern_json_pointer'])
            and all(k in condition and condition[k] == v for k,v in formal_condition.items())
            and condition.get(s['parentSlot']) == sel['record_id']
            and isinstance(s.get('recordRaw'), dict)):
        return False
    raw = json.dumps(s['recordRaw'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return sha256(raw.encode()).hexdigest() == t.get('raw_record_sha256')


def short_condition(a, proof):
    """Use only known formats. Unknown condition models keep the formal wording."""
    text = a.get('condition_label') or ''
    if not proof:
        return text
    model = proof.get('model')
    sel = proof['selected'].get('parent_conditions_raw') or {}
    if model == 'HP_CHAIN' and {'hpstart','hpend'} <= sel.keys() and '来源相同' in text:
        return f"HP {sel['hpstart']}–{sel['hpend']}%"
    if model in ('JOB_AFTER_COST','SCRAP_TWO_TIER') and 'mne' in sel:
        prefix, unit = ('预测扣费后职业法珠', '颗') if model == 'JOB_AFTER_COST' else ('选档时废料', '个')
        return f"{prefix} {sel.get('mns',0)}–{sel['mne']} {unit}"
    if model == 'SCRAP_BASE_SAME_VALUE':
        match = re.search(r'废料([\d–]+个)', text)
        if match:
            return '选档时废料 ' + match[1]
    if model == 'TERRAIN_SHARED':
        limit = next((x['selection']['parent_conditions_raw'].get('limit')
                      for x in proof.get('merged_disclosures', [])
                      if x['selection']['parent_conditions_raw'].get('bgf')), None)
        if limit and '森林（含夜间）' in text:
            return f'基础档／森林（含夜间，限本控制器前{limit}次）'
    if model == 'CURRENT_SUPER_UI':
        return '超共鸣当前选档'
    if model == 'DIRECT' and text.endswith('；其它档位的数值不并入'):
        if '未设置Chain区间条件' in text:
            return '当前基础档'
        return text.split('；')[0].removeprefix('仅').removesuffix('被选中时').replace('（通常）','').replace('当前档','档')
    if model == 'USE_ONCE_NORMAL':
        return text.split('；')[0].replace('当前同一控制器','本控制器')
    denju = proof.get('denju') or {}
    if model and model.startswith('DENJU_') and denju.get('patternid0') == proof['selected']['pattern_id']:
        if denju.get('full_text_equal') is True:
            return '传授当前选档'
        if denju.get('first_sentence_equal') is True and proof.get('mirror'):
            return '传授首句条件镜像'
    return text


def split_notes(flags):
    detail = '、'.join(d.get('word') or d.get('text', '') for f in flags
                     for d in f.get('detail', []) if isinstance(d, dict))
    labels = [cn for jp, cn in [('弾き飛ば','击飞'),('転倒','击倒'),('ダウン','眩晕'),
                                ('暗闇','暗盲'),('スロウ','缓速')] if jp in detail]
    return '同句待核对：' + ('、'.join(labels) if labels else '其余机制')


def audit_card(old, current, changes):
    """Compare a hash-verified preimage to the exact accepted current card."""
    left, right = deepcopy(old), deepcopy(current)
    for c in (left, right):
        for key in ('summary','coverage'):
            c.pop(key, None)  # Reader aggregates are independently derived from the ledger.
    lrows, rrows = ({r['row_id']:r for r in rows(c)} for c in (left, right))
    review(lrows.keys() == rrows.keys(), '描述新增、删除或重排，需要重新绑定')
    drifts = []
    for rid, r in rrows.items():
        before = lrows[rid]
        if rid in changes:
            d = changes[rid]
            review(d.get('before') == before and d.get('after') == r, '验收前后像与卡片不一致：' + rid)
            ignore = ROW_STATE | {k for k in before.keys() | r.keys() if k.startswith('inference_')}
            review({k:v for k,v in before.items() if k not in ignore} == {k:v for k,v in r.items() if k not in ignore},
                   '原文、上下文或非答案字段变化：' + rid)
            review(r['answers'][:len(before['answers'])] == before['answers'] and len(r['answers']) > len(before['answers']),
                   '旧答案被改写、删减或重排：' + rid)
            r.clear()
            r.update(deepcopy(before))
        elif r != before:
            # This metadata is a cross-check fingerprint, not the source
            # record hash. Allow only a proven before/after field difference.
            for idx, (a,b) in enumerate(zip(before['answers'], r['answers'])):
                x = (a.get('binding') or {}).get('g1_b1_binding') or {}
                y = (b.get('binding') or {}).get('g1_b1_binding') or {}
                u, v = x.get('page_sha256'), y.get('page_sha256')
                if u != v and all(isinstance(z,str) and re.fullmatch(r'[0-9a-f]{64}',z) for z in (u,v)):
                    y['page_sha256'] = u
                    drifts.append({'rowId':rid,'answerIndex':idx,'before':u,'after':v})
            review(r == before, '变动未列入已验收增量：' + rid)
    review(left == right, '技能结构、分支来源或卡片基础字段有变化')
    return drifts


def project_card(card, upstream, overlay, changes, desc, effects, cycle):
    """Return one card transaction and its exact dispositions. Fail closed per card."""
    view_rows = {r['id']:r for r in rows(card)}
    formal_rows = {r['row_id']:r for r in rows(upstream)}
    review(view_rows.keys() == formal_rows.keys(), 'Web 描述集合与主线不一致')
    adopted, dispositions, notices, unknowns = [], [], [], []
    for rid, r in view_rows.items():
        target = formal_rows[rid]
        d, es = desc.get(rid) or {}, effects[rid]
        review(r['original'] == target['japanese'] == d.get('japanese'), '中文或原句锚点失配：' + rid)
        review({e['id'] for e in r['effects']} == es.keys(), '效果拆分集合有变化：' + rid)
        old_count = len(changes[rid]['before']['answers']) if rid in changes else len(target['answers'])
        current_indexes = [a['source']['answerIndex'] for e in r['effects'] for a in e['answers']]
        current_indexes += [a['source']['answerIndex'] for a in r['unboundAnswers']]
        review(sorted(current_indexes) == list(range(old_count)), 'Web 旧答案集合失配：' + rid)
        for e in r['effects']:
            refs = es[e['id']].get('answer_refs', [])
            review(sorted(a['source']['answerIndex'] for a in e['answers']) ==
                   sorted(a['answer_index'] for a in refs if a['answer_index'] < old_count),
                   '旧答案对应效果有变化：' + rid)
            if not any(a['answer_index'] >= old_count for a in refs):
                review(e['status'] == es[e['id']]['status'], '非目标效果状态发生变化：' + rid)
        if rid not in changes:
            continue
        review(r['translationStatus'] != 'pending' and r.get('textZh'), '现有中文需复核：' + rid)
        flags = d.get('split_flags') or []
        if flags:
            r.update(review=True, syncFormalSplit=True, syncSplitFlags=flags, reviewMessage=split_notes(flags))
        patch = overlay.get('rows', {}).get(rid, {})
        remaining = [x for x in patch.get('additions', []) if not x['answer'].get('syncDisposition')]
        for idx, a in enumerate(target['answers'][old_count:], old_count):
            matches = [(eid, e, ref) for eid,e in es.items() for ref in e.get('answer_refs', []) if ref['answer_index'] == idx]
            review(len(matches) == 1, '正式账本未唯一绑定新答案：' + rid)
            eid, effect, ref = matches[0]
            review(effect['status'] == 'has_answer' and all(ref.get(k) == a.get(k)
                   for k in ('rule_key','field_path','raw_value','condition_label')), '账本答案引用失配：' + rid)
            e = next(e for e in r['effects'] if e['id'] == eid)
            span = effect.get('span') or []
            review(len(span) == 2 and 0 <= span[0] < span[1] <= len(r['original']) and
                   r['original'][span[0]:span[1]] == effect.get('snippet') and
                   e['label'] == effect_label(effect,r['original']) and e['label'] != '解除异常状态',
                   '效果原文片段或标签有歧义：' + eid)
            proof = delta_proof(a, rid, eid)
            v = answer(a, cid=card['cid'], original=r['original'])
            review(v['confidence'] in ('confirmed','inferred') and
                   bool(v['source']['pointer'] and v['source']['rule']) and v['text'] and
                   v['text'] != a.get('value'), '新数值、证据或玩家单位需核查：' + eid)
            v.update(syncFormal=True, readerOrigin=f'{cycle} 正式答案')
            v['source'].update(rowId=rid, effectId=eid, answerIndex=idx, playerScope=a.get('player_scope'),
                               originalPlayerText=a.get('player_text'), notIncluded=a.get('not_included'))
            if e['label'] == '伤害':
                v['source']['originalEffectBinding'] = {**(a.get('effect_binding') or {}), 'span':span}
            selections = []
            if proof:
                sel = proof['selected']
                v['condition'] = a.get('condition_label') or ''
                v['displayBranch'] = {'key':f"formal:{a['layer']}:{sel['pattern_id']}",
                                      'conditionKnown':bool(v['condition']), 'conditionLabel':short_condition(a,proof),
                                      'order':idx}
                selections = [('same_parent',sel,'同一效果、父分支、执行槽、规则、来源与原值')]
                for kind, field in [('merged_parent','merged_disclosures'),('excluded_parent','excluded_branch_values')]:
                    selections += [(kind,x['selection'],x['reason']) for x in proof.get(field,[])]
            saved = []
            for kind, selection, reason in selections:
                candidates = [x for x in remaining if selected_identity(x,eid,selection)]
                if len(candidates) > 1:
                    notices.append({'rowId':rid,'effectId':eid,'reason':'同一身份命中多个旧候选，保留所有候选'})
                    continue
                if not candidates:
                    continue
                old = candidates[0]
                remaining.remove(old)
                decision = {'rowId':rid,'effectId':eid,'kind':kind,'branchId':selection['pattern_id'],
                            'recordId':selection['record_id'],'raw':selection['raw_value'],'reason':reason,
                            'oldCandidate':deepcopy(old)}
                old['answer']['syncDisposition'] = kind
                saved.append(decision)
                dispositions.append(decision)
                if kind == 'excluded_parent':
                    r['syncExcluded'] = f"旧候选 {num(selection['raw_value'])}倍：{reason.split('；')[0]}"
            v['source']['syncPreviousCandidates'] = saved
            if '自身受伤另论' in str((a.get('player_scope') or {}).get('object','')):
                r['syncScopeGap'] = '自身受到的伤害数值尚未解出'
            e['answers'].append(v)
            e['status'] = 'has_answer'
            adopted.append({'rowId':rid,'effectId':eid,'answerIndex':idx,'raw':a['raw_value'],
                            'confidence':v['confidence'],'source':a['source'],'condition':a.get('condition_label')})
        relevant = {x['effectId'] for x in adopted if x['rowId'] == rid}
        notices += [{'rowId':rid,'effectId':x['effectId'],'reason':'未证明与正式答案等价，保留旧候选',
                     'candidate':x} for x in remaining if x['effectId'] in relevant]
        unknowns.append({'rowId':rid,'splitFlags':flags,'scopeGap':r.get('syncScopeGap'),
                         'unresolvedEffectIds':[eid for eid,e in es.items() if e['status'] == 'unresolved']})
    for g in card['groups']:
        for s in g['skills']:
            for prev, nxt in zip(s['rows'],s['rows'][1:]):
                if prev.get('syncScopeGap') and nxt['original'] == 'ダメージ量は自身の残りHP量に応じて変化する。':
                    nxt['syncHpQualifier'] = prev['id']
    return adopted, dispositions, notices, unknowns


def refresh_fingerprints(card, drift):
    by_row = {r['id']:r for r in rows(card)}
    for item in drift:
        row = by_row[item['rowId']]
        views = [a for e in row['effects'] for a in e['answers']] + row['unboundAnswers']
        match = [a for a in views if a['source']['answerIndex'] == item['answerIndex']]
        review(len(match) == 1, '来源指纹的旧答案身份失配')
        b = (match[0]['source'].get('originalBinding') or {}).get('g1_b1_binding') or {}
        review(b.get('page_sha256') == item['before'], 'Web 来源指纹不是已验收的前像')
        b['page_sha256'] = item['after']


def run(args):
    site, reports = READER/'site'/args.name, READER/'reports'/args.name
    require(not site.exists() and not reports.exists(), 'Use a fresh isolated name')
    base, source = args.base_reader.resolve(), args.source.resolve()
    m, delta, changes, acceptance_files = source_package(args.manifest, args.verdict)
    receipt = baseline_reader(base)
    # Bind the full read set, including the selected campaign and ledger.
    pointer = source/'pages/_batch/campaign_latest.json'
    report = (source/'pages'/read(pointer)['report']).resolve()
    require(report.is_relative_to(source/'pages'), 'Campaign report path escapes pages')
    metric_path, ledger_path = source/'effect_ledger/metrics.json', source/'effect_ledger/ledger.jsonl'
    inputs = {p:digest(p) for p in (args.manifest,args.verdict,args.manifest.parent/'report_data.json',
                                   pointer,report,metric_path,ledger_path,source/'profiles/rules.json',
                                   *acceptance_files)}
    metrics, campaign = read(metric_path), read(report)
    snapshot = metrics['snapshot']
    require((snapshot['snapshot_id'], snapshot['campaign_signature']) == (m['snapshot'],m['campaign']) and
            campaign['campaign_complete'] and campaign['signature'] == m['campaign'] and
            campaign['completed'] == campaign['expected'] and not campaign['unresolved_latest_failures'],
            'Formal source is incomplete or differs from independent acceptance')
    require(inputs[source/'profiles/rules.json'][:16] == snapshot['rules_json_sha256_16'], 'Rule hash differs')
    frozen = None
    if args.target_hashes:
        inputs[args.target_hashes] = digest(args.target_hashes)
        frozen = {k.split('/')[0]:v for k,v in read(args.target_hashes).items()
                  if re.fullmatch(r'\d+/card\.json',k)}
    paths, hashes = card_hashes(source,frozen,m['campaign'])
    before_hashes = receipt['sourceHashes']
    require(campaign['expected'] == len(hashes) == metrics['rows']['cards'], 'Formal card count differs')
    changed = {cid for cid in hashes if before_hashes.get(cid) != hashes[cid]}
    if receipt['snapshot']['snapshot_id'] == m['snapshot']:
        require(hashes == before_hashes, 'Snapshot id reused with different card hashes')
    by_card = defaultdict(dict)
    for rid,d in changes.items():
        by_card[str(d['cid'])][rid] = d
    if receipt['snapshot']['snapshot_id'] != m['snapshot']:
        require(by_card.keys() <= changed, 'Accepted delta includes cards with no observed source change')
    desc, effects, counts = read_ledger(ledger_path,m['snapshot'],changed,metrics)
    require(counts.keys() == hashes.keys(), 'Ledger card set differs')
    catalog = payload(base/'data/catalog.js')
    require({str(c['cid']) for c in catalog['cards']} == before_hashes.keys(), 'Baseline card index differs')
    overlay = payload(base/'data/branch_candidates.js')
    adopted, decisions, notices, unknowns, held, drifts = [], [], [], [], [], []
    outputs = {}
    active = dict(before_hashes)
    for cid in sorted(changed | (before_hashes.keys()-hashes.keys()), key=int):
        try:
            review(cid in paths and cid in before_hashes, '新增或移除角色，需要审定目录与原文')
            before = args.before_cards/f'{cid}.json'
            review(before.is_file() and digest(before) == before_hashes[cid], '缺少与 Web 基线匹配的完整卡片前像')
            current = read(paths[cid])
            review(str(current['cid']) == cid and str(read(before)['cid']) == cid, '卡片身份失配')
            drift = audit_card(read(before),current,by_card[cid])
            card = payload(base/'data/cards'/f'{cid}.js')
            candidate = deepcopy(overlay['cards'].get(cid, {}))
            a,b,c,u = project_card(card,current,candidate,by_card[cid],desc,effects,delta['cycle'])
            refresh_fingerprints(card,drift)
        except ReviewNeeded as err:
            held.append({'cid':cid,'reason':str(err),'beforeSHA256':before_hashes.get(cid),'afterSHA256':hashes.get(cid),
                         'acceptedRows':list(by_card[cid]),
                         'formalCard':str(paths[cid]) if cid in paths else None})
            continue
        for src, dst in ((a,adopted),(b,decisions),(c,notices),(u,unknowns),(drift,drifts)):
            dst.extend({'cid':cid,**entry} for entry in src)
        outputs[cid] = card
        if cid in overlay['cards']:
            overlay['cards'][cid] = candidate
        active[cid] = hashes[cid]
    held_ids = {x['cid'] for x in held}
    for c in catalog['cards']:
        cid = str(c['cid'])
        if cid not in held_ids:
            expected = {k:counts[cid][k] for k in c['counts']}
            require(cid in changed or c['counts'] == expected, 'Ledger-only changes need explicit review: ' + cid)
            c['counts'] = expected
            c['status'] = ('全部描述完整' if expected['complete'] == expected['descriptions'] else
                           '已有部分答案' if expected['answer'] else '暂无效果答案')
    catalog['summary'].update(withAnswer=sum(bool(c['counts']['answer']) for c in catalog['cards']),
                              noAnswer=sum(not c['counts']['answer'] for c in catalog['cards']),
                              complete=sum(c['counts']['complete'] == c['counts']['descriptions'] for c in catalog['cards']))
    complete = not held
    visible_snapshot = snapshot if complete else receipt['snapshot']
    catalog['meta'].update(snapshot=visible_snapshot['snapshot_id'], updated=metrics['generated_at'],
                           acceptedCycle=delta['cycle'] + (' 隔离同步' if complete else ' 部分同步'),
                           syncTarget=m['snapshot'], syncHeld=len(held))
    result = {'schema':'reader-incremental-v1','status':'aligned' if complete else 'review_required',
              'complete':complete,'snapshot':visible_snapshot,'targetSnapshot':snapshot,
              'baseSnapshot':receipt['snapshot']['snapshot_id'],'sourceHashes':active,
              'adopted':adopted,'candidateDecisions':decisions,'sameSentenceUnknowns':unknowns,
              'reviewQueue':held+notices,'heldCards':held,'fingerprintOnlyChanges':drifts,
              'changedCards':sorted(changed,key=int),'integratedCards':list(outputs),
              'counts':{'answers':len(adopted),'candidateDispositions':dict(Counter(x['kind'] for x in decisions)),
                        'splitFlags':sum(len(x['splitFlags']) for x in unknowns),'heldCards':len(held)},
              'inputs':{str(p):h for p,h in inputs.items()}}
    def verify_read_set():
        for p,h in inputs.items():
            require(digest(p) == h, 'Input changed during sync: ' + str(p))
        for cid,p in paths.items():
            require(digest(p) == hashes[cid], 'Mainline changed during sync: ' + cid)
    if args.plan:
        verify_read_set()
        print(json.dumps({'status':result['status'],'counts':result['counts'],'reviewQueue':result['reviewQueue']},ensure_ascii=False))
        return 2 if held else 0
    stage = Path(tempfile.mkdtemp(prefix=args.name+'-stage-',dir=site.parent))
    shutil.copytree(base/'data', stage/'data', copy_function=shutil.copy2)
    for name in RUNTIME:
        shutil.copy2(TEMPLATE/name,stage/name)
    for cid, card in outputs.items():
        raw = json.dumps(card,ensure_ascii=False,separators=(',', ':'),allow_nan=False).replace('</','<\\/')
        (stage/'data/cards'/f'{cid}.js').write_text(f'window.CC_DETAILS=window.CC_DETAILS||{{}};window.CC_DETAILS["{cid}"]={raw};\n',encoding='utf-8')
    js(stage/'data/catalog.js','CC_CATALOG',catalog)
    js(stage/'data/branch_candidates.js','CC_BRANCH_CANDIDATES',overlay)
    label = escape(delta['cycle']) + (' 隔离同步' if complete else ' 部分同步 · 有待核对卡')
    build_frontend(stage,TEMPLATE,label)
    write_report_page(stage,result,label)
    verify_read_set()
    result['runtimeHashes'] = {p.relative_to(stage).as_posix():digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}
    dump(stage/'incremental_receipt.json',result)
    reports.mkdir(parents=True)
    dump(reports/'reconciliation.json',result)
    stage.rename(site)
    print(json.dumps({'status':result['status'],'counts':result['counts'],'site':str(site),
                      'report':str(reports/'reconciliation.json')},ensure_ascii=False))
    return 2 if held else 0


def write_report_page(stage, result, label):
    links = ' '.join(f'<a href="index.html#card={cid}">{cid}</a>' for cid in result['integratedCards'])
    issues = ''.join(f"<li>{escape(x.get('rowId',x['cid']))}：{escape(x['reason'])}</li>" for x in result['reviewQueue'])
    (stage/'pilot-report.html').write_text(f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{label}</title>
<link rel="stylesheet" href="style.css"><main id="main"><p><a href="index.html">返回角色目录</a></p>
<h1>{label}</h1><p>目标快照 {escape(result['targetSnapshot']['snapshot_id'])}，已接入 {len(result['adopted'])} 条答案。</p>
<p>本次处理的角色：{links}</p><h2>待核对</h2>{'<ul>'+issues+'</ul>' if issues else '<p>没有需要核对的接入歧义。</p>'}
</main></html>""",encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--name',required=True,help='Fresh directory name within projects/reader/site and reports')
    ap.add_argument('--base-reader',type=Path,default=TEMPLATE)
    ap.add_argument('--source',type=Path,default=FORMAL,help='Root containing pages, profiles, and effect_ledger')
    ap.add_argument('--target-hashes',type=Path,help='Accepted frozen pages_sha256.json when replaying an isolated source')
    ap.add_argument('--before-cards',type=Path,required=True,help='Hash-verifiable flat <cid>.json preimages')
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--verdict',type=Path,required=True)
    ap.add_argument('--plan',action='store_true',help='Check and print the reconciliation without writing the site')
    args = ap.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,80}',args.name):
        ap.error('Use a plain isolated name')
    try:
        return run(args)
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({'status':'blocked','reason':str(error)},ensure_ascii=False),file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
