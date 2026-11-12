"""Check the complete retained-purple denominator against the integrated review."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from copy import deepcopy
from pathlib import Path
from rerun_output import require_new_files, write_new_text, write_path

ROOT=Path(__file__).resolve().parents[2]


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def key(item):
    s=item['source']; b=s.get('originalBinding') or {}
    for name in ('g1_b1_binding','c12_p3_skilltext_mirror_binding','c8_p1_t27_binding','c11_p1_t114_binding'):
        if name in b:
            b=b[name];break
    return json.dumps([item['rowId'],s.get('effectId') or item['effect'],s.get('layer'),s.get('branchId'),s.get('recordId'),
                       s.get('rule'),s.get('field'),s.get('raw'),item['text'],b.get('pattern_id'),
                       s.get('effectId'),s.get('answerIndex')],ensure_ascii=False)


def verify(out,audit_dir='audit/c19_closeout_20261107', report_path=None):
    audit=out/audit_dir
    report_path = report_path or write_path(audit/'condition_validation.json')
    require_new_files(report_path)
    before=read(out/'audit/final5_evidence_20261107/inventory.json')
    screened=read(audit/'condition_closeout_receipt.json')
    after=read(audit/'inventory.json')
    c19=read(audit/'c19_validation.json')
    assert c19['status']=='PASS'
    drift_cids={i['cid'] for i in c19['oldAnswerViewChanges']}
    old={key(i):i for i in before['items']};new={key(i):i for i in after['items']}
    assert len(old)==len(new)==2222 and set(old)==set(new), 'full candidate identities changed'
    purple={k:i for k,i in old.items() if i['review']['status']=='purple'}
    checks={key(i):i for i in screened['items']}
    assert len(purple)==len(checks)==760 and set(purple)==set(checks), 'not every old purple was screened'
    for rel,h in screened['inputs'].items():
        assert sha256((ROOT/rel).read_bytes()).hexdigest()==h, 'screening source drift: '+rel
    promoted=[];retained=[]
    for k,b in old.items():
        a=new[k];r=a['review']
        sa,sb=deepcopy(a['source']),deepcopy(b['source'])
        if a['cid'] in drift_cids:
            for s in (sa,sb):
                binding=(s.get('originalBinding') or {}).get('g1_b1_binding')
                if binding and 'page_sha256' in binding:binding['page_sha256']='C19_VALIDATED_FINGERPRINT_ONLY'
        assert sa==sb and a['text']==b['text'], 'candidate source/value mutated beyond accepted C19 fingerprint drift'
        if b['review']['status']=='inferred':
            assert r['status']=='inferred','previous conclusion changed without a new review'
            continue
        screen=checks[k]
        if r['status']=='inferred':
            assert r['numericKnown'] and r['bindingKnown'] and r['conditionKnown']
            assert screen['selectionResolved'] and r.get('selectionResolved')
            parent=screened['parents'][screen['parentKey']]
            assert r['condition']==parent['conditionLabel'], 'label differs from reviewed selector'
            if 'random' in parent['selectionKind'] or 'weighted_prediction_counter_pool' in parent['selectionKind']:
                assert '随机' in r['condition'], 'random choice shown as deterministic'
            promoted.append({'cid':a['cid'],'rowId':a['rowId'],'effect':a['effect'],'condition':r['condition']})
        else:
            assert r['shortReason'], 'retained unknown has no explanation'
            assert not (r['numericKnown'] and r['bindingKnown'] and r['conditionKnown']), 'fully resolved item incorrectly retained'
            retained.append({'cid':a['cid'],'rowId':a['rowId'],'effect':a['effect'],'reason':r['shortReason'],
                             'conditionGap':screen['conditionGap']})
    report={'pass':True,'counts':{'screened':760,'promoted':len(promoted),'retained':len(retained),
                                'currentInferred':after['stats']['inferred'],'currentPurple':after['stats']['purple']},
            'retainedReasons':dict(Counter(i['reason'] for i in retained)),
            'promoted':promoted,'retained':retained,
            'checks':['complete 760 original identities','2222 values and sources preserved except separately validated C19 fingerprint drift','input hashes unchanged',
                      'promotion requires fresh numeric/effect/selection checks','random choice explicitly labeled',
                      'remaining unknowns retain reasons; no promotion based only on old eligibility flag']}
    write_new_text(report_path, json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'pass':True,'counts':report['counts'],'retainedReasons':report['retainedReasons']},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--audit-dir',default='audit/c19_closeout_20261107')
    p.add_argument('--report',type=Path,help='Path to a new validation receipt')
    args=p.parse_args()
    verify(args.output.resolve(),args.audit_dir, write_path(args.report) if args.report is not None else None)
