"""Audit source branches, then add a provisional reader overlay, never ledger answers.

Run against the reviewed reader and current pages. All original reader sentences
must still match; numerical donors are the frozen reader's existing effect-bound
answers. Alternative values come from the SAME slot/type/layer in real edges.
No pattern order, HP range, flag bit or parameter magnitude decodes a selector.
"""
import argparse
import copy
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import unicodedata

from presentation import answer, TECHNICAL
from rerun_output import read_path, require_new_files, review_output, write_new_text

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LABELS = {'攻击力', '防御', '移动速度', '暴击率', '暴击威力', '持续时间', '伤害', '回复', '生命回复'}
ANCHORS = {'攻击力': '攻击力', '防御': '防御力', '移动速度': '移动速度',
           '暴击率': '暴击率', '暴击威力': '暴击威力', '持续时间': '一定时间|一段时间',
           '伤害': '伤害', '回复': '回复', '生命回复': '回复'}
SCOPE_LABELS = {'必杀威力', '反响威力', '回复量', '我方增益', '敌方减益与我方增益'}


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def reader(p):
    return json.loads(p.read_text(encoding='utf-8').split(']=', 1)[1].strip().removesuffix(';'))


def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def identity(rec):
    return rec['table'], rec['layer'], rec['record_id']


def raw(rec):
    return rec.get('raw_record') or {}


def record_map(skill):
    result = {}
    for r in skill.get('record_evidence', []):
        key = identity(r)
        if key in result and raw(result[key]) != raw(r):
            raise ValueError('Conflicting source record: '+str(key))
        result[key] = r
    return result


def parent(skill):
    return record_map(skill).get(('bosspattern', skill.get('layer'), skill.get('record_id')))


def slots(record):
    return {k: v for k, v in raw(record).items() if re.fullmatch(r'skillid\d+', k)}


def graph_pairs(base, other):
    """Slot identity is retained even if a child is referenced more than once."""
    bm, om = record_map(base), record_map(other)
    bp, op = parent(base), parent(other)
    if not bp or not op:
        return [], '缺少可核对的父记录'
    pairs, issues = [], []
    for slot, bid in slots(bp).items():
        oid = slots(op).get(slot)
        b = bm.get(('bossskill', base['layer'], bid))
        o = om.get(('bossskill', other['layer'], oid))
        if not b or not o or raw(b).get('skillid0') != raw(o).get('skillid0'):
            issues.append(slot+'类型或引用不一致')
            continue
        pairs.append((slot, b, o))
        if raw(b).get('s_ability') is not None or raw(o).get('s_ability') is not None:
            ba = bm.get(('skilllist', base['layer'], raw(b).get('s_ability')))
            oa = om.get(('skilllist', other['layer'], raw(o).get('s_ability')))
            if ba and oa and raw(ba).get('ability') == raw(oa).get('ability'):
                pairs.append((slot+'/s_ability', ba, oa))
            else:
                issues.append(slot+'附加能力类型或引用不一致')
    if set(slots(op))-set(slots(bp)):
        issues.append('候选含额外执行槽；不推算执行次数或总伤害')
    return pairs, '；'.join(issues)


def rule_type(rec):
    return raw(rec).get('skillid0') if rec['table'] == 'bossskill' else raw(rec).get('ability')


def known_fields(rec):
    return {a.get('f') for a in rec.get('answers', []) if a.get('rule_key') and finite(a.get('raw'))}


def compatible(b, o):
    """Unknown changed fields may encode target, geometry, trigger or context."""
    ignored = {'skillid', 'name', 'sname', 'text', 'description', 'sinfo', 's_ability', 'spmotname'}
    # Only known amount slots are allowed to differ. Type2012 param7/8 target,
    # type2003 param3 trigger and all other flags/objects stay identical.
    amount_fields = {
        ('bossskill', 13): {'skillparam1', 'skillparam2', 'skillparam3', 'skillparam6'},
        ('skilllist', 2003): {'param0', 'param7', 'param8', 'param9'},
        ('skilllist', 2012): {'param0', 'param4', 'param5'},
    }.get((b['table'], rule_type(b)))
    if amount_fields is None:
        amount_fields = {a['f'].lstrip('/') for a in b.get('answers', [])
                         if a.get('f') and a.get('rule_key') and any(t in a.get('kind', '')
                         for t in ('倍率', '系数', '持续时间', '次数', '间隔', '上限'))
                         and '用途' not in a.get('kind', '') and '消费点未定' not in a.get('kind', '')}
    different = [k for k in set(raw(b)) | set(raw(o)) if k not in ignored | amount_fields
                 and (k in raw(b), raw(b).get(k)) != (k in raw(o), raw(o).get(k))]
    return different


def source_identity(a):
    s = a.get('source') or {}
    ss = s if isinstance(s, list) else [s]
    return {(x.get('table'), x.get('layer'), x.get('record_id')) for x in ss if isinstance(x, dict)}


def conditions(skill):
    result = []
    for r in skill['rows']:
        jp = unicodedata.normalize('NFKC', r['japanese'])
        if re.search(r'次に.{0,20}(?:使用|発動)|次の必殺', jp):
            continue
        if re.search(r'(?:効果|(?<!クリティカル)威力|回復量).{0,25}(?:上が[るり]|高くな[るり]|強くな[るり]|増加|延長)', jp):
            result.append(r)
    return result


def scope_for(effect, row):
    if effect['label'] == '伤害':
        return '反响威力' if '反響' in row['original'] else '必杀威力'
    if effect['label'] in ('回复', '生命回复'):
        return '回复量'
    if re.search(r'敵.{0,25}(?:攻撃力|防御力|移動速度)', row['original']):
        return '敌方减益与我方增益'
    return '我方增益'


def anchor_safe(row, effect):
    label, text = effect['label'], row['textZh']
    if label not in ANCHORS or row.get('translationStatus') == 'pending' or row.get('translationNote'):
        return False
    if len([e for e in row['effects'] if e['label'] == label]) != 1:
        return False
    if label == '伤害' and re.search('反响|暴击|受到|承受|减伤|伤害降低|伤害减少', text):
        return False
    if label == '持续时间' and re.search('每隔|每过|间隔', text):
        return False
    return len(re.findall(ANCHORS[label], text)) == 1


def format_candidate(ca, donor, other_rec, cid, original):
    k = donor.get('quantity_kind') or ca.get('kind', '')
    # Field rules whose consumer is still unknown never become a purple effect.
    if '消费点未定' in ca.get('kind', '') or '用途待' in ca.get('value', ''):
        return None
    a = {'value': ca.get('value'), 'quantity_kind': k, 'raw_value': ca['raw'],
         'field_path': ca['f'], 'rule_key': ca['rule_key'], 'source': other_rec['source'],
         'numeric_evidence': '确认', 'association_evidence': '推断',
         'conditions': '', 'note': ca.get('rule_limits', '')}
    view = answer(a, cid=cid, original=original)
    if not view['text'] or '待' in view['text'] or TECHNICAL.search(view['text']):
        return None
    return view


def semantic_damage_targets(base, pairs, br, ca, vr):
    """Fallback only for field rules explicitly proven to be damage inputs.

    No type64/76 consumer-unknown inference and no textual effect order matching.
    Multi-attack branches use the interpreter's specific shape, never slot order.
    """
    if br['table'] != 'bossskill' or not any(x in ca.get('kind','') for x in ('技能基值倍率','伤害输入倍率')) or '回复' in ca.get('kind',''):
        return []
    patterns={55:r'直線範囲上.*ダメージを与え',110:r'前方範囲内.*\d+回ダメージを与え',
              3:r'前方範囲内.*ダメージを与え',74:r'(?:前方範囲内|自身中心範囲内).*ダメージを与え',
              112:r'ダメージを与え.*(?:設置|攻撃範囲)'}
    typ=rule_type(br)
    if typ not in patterns:return []
    targets=[]
    for rr in base['rows']:
        r=vr.get(rr['row_id'])
        if not r or not re.search(r'ダメージを与え',r['original']):continue
        if not re.search(patterns[typ],r['original']):continue
        # Count actual executor records, including types with unknown numeric
        # rules. An unexplained type103 frontal hit still competes with type3.
        potential={3:'front',74:'front',103:'front',110:'front',55:'line',112:'placed'}
        shape=potential[typ]
        competing={identity(b) for _,b,_ in pairs if b['table']=='bossskill'
                   and potential.get(rule_type(b))==shape}
        if len(competing)!=1:continue
        for e in r['effects']:
            if e['label']=='伤害' and anchor_safe(r,e):
                targets.append((r,e,{'quantity_kind':ca.get('kind'),'rule_key':ca['rule_key'],
                    'field_path':ca['f'],'raw_value':raw(br).get(ca['f'].lstrip('/')),
                    'source':{'table':br['table'],'layer':br['layer'],'record_id':br['record_id']}}))
    return targets


def patch_for(entry, rid):
    return entry.setdefault('rows', {}).setdefault(rid, {})


def answer_evidence(a):
    return {k:copy.deepcopy(a[k]) for k in ('f','raw','rule_key','value','kind','unit','status','conversion','base_definition','rule_limits') if k in a} | {'evidence':(a.get('details') or {}).get('evidence',[])}


def audit(root, out, destination=None):
    destination = destination or out
    sidecar = destination/'data/branch_candidates.js'
    inventory_file = destination/'audit/branch_candidates_20261107/inventory.json'
    require_new_files(sidecar, inventory_file)
    receipt = read(out/'build_receipt.json')
    overlay, inventory, hashes, source_inventory, same_cond_inventory = {}, [], {}, [], []
    totals = Counter()
    for f in sorted((out/'data/cards').glob('*.js')):
        view = reader(f)
        cid = view['cid']
        path = root/f'output/character_skills/pages/{cid}/card.json'
        data_bytes = path.read_bytes()
        hashes[str(cid)] = sha256(data_bytes).hexdigest()
        card = json.loads(data_bytes)
        totals['cards'] += 1
        vr = {r['id']: r for g in view['groups'] for s in g['skills'] for r in s['rows']}
        mr = {r['row_id']: r for g in card['groups'] for s in g['skills'] for r in s['rows']}
        for rid, r in vr.items():
            if rid not in mr or mr[rid]['japanese'] != r['original']:
                raise ValueError('Reader sentence changed: '+rid)
        entry = {'rows': {}}
        patterns = {(s['layer'],s['record_id']):s for g in card['groups'] for s in g['skills'] if parent(s)}
        for rid,r in mr.items():
            disclosure=r.get('same_cond_alt_t13') or {}
            if disclosure.get('branches'):
                same_cond_inventory.append({'cid':cid,'rowId':rid,'branches':[
                    {'pid':b.get('pid'),'layer':b.get('layer'),
                     'state':('有正文，保留独立描述' if patterns[(b.get('layer'),b.get('pid'))]['rows'] else '无正文，纳入分支审查')
                        if (b.get('layer'),b.get('pid')) in patterns else '无可核对父记录，不绑定'}
                    for b in disclosure['branches']]})
        for group in card['groups']:
            # Census includes every no-row skill, even non-strengthening SA data.
            for s in group['skills']:
                if s['rows']:
                    continue
                source_inventory.append({'cid': cid, 'group': group['group'], 'ref': s['reference_field'],
                    'id': s['record_id'], 'layer': s['layer'], 'textPresent': bool(s.get('original_text')),
                    'recordCount': len(s.get('record_evidence', [])),
                    'knownParameters': sum(len(r.get('answers', [])) for r in s.get('record_evidence', []))})
            if group['group'] != 'special_move':
                continue
            text_skills = [s for s in group['skills'] if s['rows'] and parent(s)]
            for alt in [s for s in group['skills'] if not s['rows'] and parent(s)]:
                ap = parent(alt)
                event = {'cid': cid, 'branchId': alt['record_id'], 'layer': alt['layer'],
                         'reference': alt['reference_field'], 'parentSource': ap['source'],
                         'conditionsRaw': raw(ap), 'fields': [], 'status': '', 'target': None}
                inventory.append(event)
                bases = [s for s in text_skills if s['layer'] == alt['layer']
                         and s.get('name') and s.get('name') == alt.get('name')
                         and (raw(parent(s)).get('flag'), 'flag' in raw(parent(s))) ==
                             (raw(ap).get('flag'), 'flag' in raw(ap))]
                profile_direct = False
                if not bases and not text_skills:
                    profiles = [s for s in group['skills'] if s['reference_field']=='skilltext' and s['rows']]
                    if len(profiles)==1:
                        # Older cards have only character prose, and unnamed patterns.
                        # Reuse the actual pattern graph; do not invent an ordinary tier.
                        bases=[{**alt,'rows':profiles[0]['rows'],'original_text':profiles[0]['original_text']}]
                        profile_direct=True
                if len(bases) != 1:
                    event['status'] = '无唯一同名同类别正文分支'
                    event['candidateBases'] = [s['record_id'] for s in bases]
                    records=[{'table':r['table'],'id':r['record_id'],'layer':r['layer'],
                              'source':r['source'],'raw':raw(r)} for r in alt.get('record_evidence',[])]
                    entry.setdefault('unmappedBranches',[]).append({'branchId':alt['record_id'],
                        'reason':'没有唯一对应的技能正文，保留分支参数待核对。','records':records})
                    for s in bases:
                        for cr in conditions(s):
                            if cr['row_id'] in vr:
                                patch_for(entry,cr['row_id']).setdefault('unmappedBranches',[]).append(entry['unmappedBranches'][-1])
                    # No guessing a target when ordinary/super or names differ.
                    continue
                base = bases[0]
                event['target'] = base['record_id']
                event['profileDirect'] = profile_direct
                conds = conditions(base)
                pairs, graph_issue = graph_pairs(base, alt)
                event['graphNote'] = graph_issue
                mapped_keys, displayed_keys = set(), set()
                blockers = []
                for slot, br, ar in pairs:
                    differences = compatible(br, ar)
                    if '/s_ability' in slot:
                        ps=slot.split('/')[0]
                        parent_pair=next((p for p in pairs if p[0]==ps),None)
                        if parent_pair:
                            differences += ['父执行槽:'+x for x in compatible(parent_pair[1],parent_pair[2])]
                    for ca in ar.get('answers', []):
                        key = (*identity(ar), ca.get('f'), slot)
                        if not ca.get('rule_key') or not finite(ca.get('raw')):
                            continue
                        field_event = {'slot':slot, 'table':ar['table'], 'record':ar['record_id'],
                            'field':ca['f'], 'rule':ca['rule_key'], 'raw':ca['raw'],
                            'baseRecord':br['record_id'], 'status':'无法唯一对应效果'}
                        event['fields'].append(field_event)
                        if differences:
                            field_event['reason'] = '对象/触发/未知字段不同：'+','.join(differences)
                            continue
                        if raw(ar).get(ca['f'].lstrip('/')) != ca['raw']:
                            raise ValueError('Candidate rule/raw mismatch')
                        targets = []
                        for rr in base['rows']:
                            r = vr.get(rr['row_id'])
                            if not r:
                                continue
                            for e in r['effects']:
                                if not anchor_safe(r, e):
                                    continue
                                for va in e['answers']:
                                    if va.get('source', {}).get('rule') != ca['rule_key']:
                                        continue
                                    donors = [a for a in rr['answers'] if a.get('rule_key') == ca['rule_key']
                                              and a.get('raw_value') == va['source'].get('raw')
                                              and (identity(br) in source_identity(a) or
                                                   (a.get('binding') or {}).get('skill_id') == br['record_id'])]
                                    # Existing formula answers may encode source in binding rather than source.
                                    if not donors:
                                        donors = [a for a in rr['answers'] if a.get('rule_key') == ca['rule_key']
                                                  and a.get('raw_value') == va['source'].get('raw')
                                                  and a.get('field_path') == ca['f']
                                                  and raw(br).get(ca['f'].lstrip('/')) == a.get('raw_value')
                                                  and len([x for _,x,_ in pairs if x['table'] == br['table'] and
                                                      rule_type(x) == rule_type(br) and raw(x).get(ca['f'].lstrip('/')) == a['raw_value']]) == 1]
                                    if donors:
                                        targets.append((r, e, donors[0]))
                        if not targets:
                            targets=semantic_damage_targets(base,pairs,br,ca,vr)
                            if targets:field_event['bindingMethod']='同父槽已知伤害规则＋唯一出伤句/已核类型形状'
                        unique = {(r['id'],e['id']):(r,e,a) for r,e,a in targets}
                        if len(unique) != 1:
                            field_event['reason'] = '没有唯一已绑定同规则同父槽的句内位置'
                            continue
                        r, effect, donor = next(iter(unique.values()))
                        field_event['rowId'], field_event['effectId'] = r['id'], effect['id']
                        # Compare within THIS target effect only. Super/bond reuse is not coverage.
                        duplicate = any(a['source'].get('rule') == ca['rule_key'] and
                                        a['source'].get('raw') == ca['raw'] for a in effect['answers'])
                        scope = scope_for(effect,r)
                        links = []
                        for cr in conds:
                            cv = vr.get(cr['row_id'])
                            if not cv or base['rows'].index(cr) <= next(i for i,x in enumerate(base['rows']) if x['row_id']==r['id']):
                                continue
                            scopes = {e['label'] for e in cv['effects']}
                            matching = scope if scope in scopes else ('敌方减益与我方增益' if scope=='我方增益' and '敌方减益与我方增益' in scopes else None)
                            if matching:
                                links.append((cr, matching))
                        view_answer = format_candidate(ca, donor, ar, cid, r['original'])
                        if view_answer is None:
                            field_event['reason'] = '字段消费意义或可读换算尚未确认'
                            continue
                        if duplicate:
                            field_event['status'] = '该效果已展示相同候选参数'
                            displayed_keys.add(key)
                        else:
                            view_answer.update({'branchCandidate':True,'candidateLabel':'候选',
                                'branchLabel':'另一分支 · 条件待确认',
                                'condition':'与本技能强化条件的对应待确认' if links else '分支适用条件待确认',
                                'mappingNote':'同名同类别技能的同一执行槽、同类型记录及同规则字段对应；实际选档未确认。'})
                            view_answer['source'].update({'branchId':alt['record_id'],'baseBranchId':base['record_id'],
                                'layer':ar['layer'],'recordId':ar['record_id'],'parentSlot':slot,
                                'parentSource':ap['source'],'conditionsRaw':raw(ap),'recordRaw':raw(ar),
                                'donorRowId':r['id'],'donorRule':ca['rule_key'],'donorRaw':donor.get('raw_value'),
                                'baseRecordSource':br['source'],'originalRecordAnswer':answer_evidence(ca),
                                'sourceCardSHA256':hashes[str(cid)],'scope':'READER_PROVISIONAL_BRANCH_OVERLAY',
                                'rule':ca['rule_key'],'field':ca['f'],'raw':ca['raw'],
                                'numericEvidence':'复用该记录已有规则解释；未新增机制证明',
                                'associationEvidence':'推测对应本句；条件选择未确认'})
                            patch = patch_for(entry,r['id'])
                            additions = patch.setdefault('additions',[])
                            if not any(x['effectId']==effect['id'] and x['answer']['source']['branchId']==alt['record_id']
                                       and x['answer']['source']['recordId']==ar['record_id']
                                       and x['answer']['source']['field']==ca['f'] for x in additions):
                                additions.append({'effectId':effect['id'],'answer':view_answer})
                            # If the mainline had a record rule but no sentence answer,
                            # show the base input as a candidate as well as the alternate.
                            if field_event.get('bindingMethod') and not profile_direct:
                                ba=next((a for a in br.get('answers',[]) if a.get('rule_key')==ca['rule_key'] and a.get('f')==ca['f']),None)
                                if ba and finite(ba.get('raw')) and not any(a['source'].get('rule')==ca['rule_key'] and a['source'].get('raw')==ba['raw'] for a in effect['answers']):
                                    bv=format_candidate(ba,donor,br,cid,r['original'])
                                    if bv and not any(x['effectId']==effect['id'] and x['answer']['source']['branchId']==base['record_id'] and x['answer']['source']['field']==ba['f'] for x in additions):
                                        bv.update({k:copy.deepcopy(v) for k,v in view_answer.items() if k not in ('text','source','detailNote','note')})
                                        bv['candidateLabel']='原描述候选'
                                        bv['source'].update(copy.deepcopy(view_answer['source']))
                                        bv['source'].update({'branchId':base['record_id'],'recordId':br['record_id'],
                                            'parentSource':parent(base)['source'],'conditionsRaw':raw(parent(base)),
                                            'recordRaw':raw(br),'originalRecordAnswer':answer_evidence(ba),'raw':ba['raw'],
                                            'file':br['source'].get('original_file'),'pointer':br['source'].get('json_pointer'),
                                            'allSources':br['source'],'originalAnswer':ba.get('value')})
                                        additions.insert(0,{'effectId':effect['id'],'answer':bv})
                            field_event['status'] = '句内候选'
                            mapped_keys.add(key)
                        # Identical parameters (e.g. duration) do not establish any strengthening.
                        if ca['raw'] != raw(br).get(ca['f'].lstrip('/')):
                            for cr, cs in links:
                                patch=patch_for(entry,cr['row_id'])
                                item={'targetRowId':r['id'],'labels':[effect['label']],'branchId':alt['record_id']}
                                if item not in patch.setdefault('candidateLinks',[]):patch['candidateLinks'].append(item)
                                if cs not in patch.setdefault('knownCandidateScopes',[]):patch['knownCandidateScopes'].append(cs)
                accepted = [x for x in event['fields'] if x['status'] in ('句内候选','该效果已展示相同候选参数')]
                event['status'] = '已有候选对应' if accepted else '已有参数但效果对应待核对'
                # Retain unknown raw parameters, too. A rule-less field isn't missing data.
                records = [{'table':x['table'],'id':x['record_id'],'layer':x['layer'],
                            'source':x['source'],'raw':raw(x)} for x in alt.get('record_evidence',[])]
                for cr in conds:
                    if cr['row_id'] not in vr:
                        continue
                    patch=patch_for(entry,cr['row_id'])
                    patch.setdefault('unmappedBranches',[]).append({'branchId':alt['record_id'],
                        'reason':'已有分支记录；句内候选仅覆盖有明确效果对应的字段，其余字段与条件仍待核对。',
                        'records':records})
                if not conds:
                    entry.setdefault('unmappedBranches',[]).append({'branchId':alt['record_id'],
                        'reason':'该分支没有可唯一关联的强化条件句；已能对应的字段见正文，其他参数保留待核。','records':records})
        if entry['rows'] or entry.get('unmappedBranches'):
            overlay[str(cid)]=entry
    # Freeze/check all reads before writing. Reader source and mainline can be concurrent.
    for cid,digest in hashes.items():
        if sha256((root/f'output/character_skills/pages/{cid}/card.json').read_bytes()).hexdigest()!=digest:
            raise ValueError('Mainline changed during scan: '+cid)
    totals['noRowSkills']=len(source_inventory)
    totals['noRowPatterns']=len(inventory)
    totals['patchedCards']=len(overlay)
    totals['additions']=sum(len(p.get('additions',[])) for e in overlay.values() for p in e['rows'].values())
    totals['conditionRows']=sum(bool(p.get('candidateLinks')) for e in overlay.values() for p in e['rows'].values())
    totals['sameConditionRows']=len(same_cond_inventory)
    result={'schema':1,'readerSnapshot':receipt['snapshot'],'summary':dict(totals),'cards':overlay}
    write_new_text(sidecar, 'window.CC_BRANCH_CANDIDATES='+json.dumps(result,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n')
    report={'summary':dict(totals),'branchStatus':dict(Counter(e['status'] for e in inventory)),
            'fieldStatus':dict(Counter(f['status'] for e in inventory for f in e['fields'])),
            'sourceHashes':hashes,'readerSourceHashes':receipt['sourceHashes'],
            'noRowSkills':source_inventory,'sameConditionRows':same_cond_inventory,'branches':inventory,
            'limits':['展示候选不计主线已解数；未证明运行时选档。','非唯一对象/触发/字段不同或用途未定不强绑。']}
    write_new_text(inventory_file, json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k in ('summary','branchStatus','fieldStatus')},ensure_ascii=False))
    return result,report


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--output', type=Path, help='Use an explicit stage for both input and new sidecars')
    args=ap.parse_args()
    destination = review_output('branch-candidates', args.output)
    source = destination if args.output else read_path(args.root/'output/character_skills/reader_full_20261106', root=args.root)
    audit(args.root, source, destination)
