"""Deterministic stratified selection and immutable common research packet."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'output/skill_mechanism_scale/20261104'
PACKET = BASE/'input'
SEED = 'mechanism-scale-20261104-v1'

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    assert not (PACKET/'manifest.json').exists(), 'Do not overwrite frozen input'
    started=now()
    census=read(BASE/'census.json')
    heals={}
    for x in sorted((x for x in census if x['family']=='heal108'),key=lambda x:(x['cid'],x['baseline_description']['slot']['stage'],x['row_id'])):
        heals.setdefault(x['cid'],x)
    def order(x): return (not x['baseline_description']['yg'],sha((SEED+x['row_id']).encode()))
    attack=[x for x in census if x['family']=='attack1095' and x['cid'] not in heals]
    groups=[sorted([x for x in attack if x['japanese'].count('と')==0],key=order),
            sorted([x for x in attack if x['japanese'].count('と')==1],key=order),
            sorted([x for x in attack if x['japanese'].count('と')>=2],key=order)]
    assert all(len(g)>=8 for g in groups)
    selected=[dict(x,stratum=i+1) for i,g in enumerate(groups) for x in g[:8]]
    selected=sorted(selected,key=lambda x:sha((SEED+x['row_id']).encode()))
    targets=[dict(x,task_id=f'A{i+1:02}') for i,x in enumerate(selected)]
    targets += [dict(x,task_id=f'H{i+1:02}',stratum='heal') for i,x in enumerate(sorted(heals.values(),key=order))]
    assert len(targets)==31 and len({x['cid'] for x in targets})==31
    manifest={'started_at':started,'files':{},'selection_seed':SEED}
    def freeze(rel):
        src=ROOT/rel
        before=src.stat()
        b=src.read_bytes()
        after=src.stat()
        assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),rel
        dest=PACKET/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(b)
        manifest['files'][rel]={'sha256':sha(b),'bytes':len(b)}
        return json.loads(b) if rel.endswith('.json') else None
    metrics=freeze('output/character_skills/effect_ledger/metrics.json')
    manifest['snapshot']=metrics['snapshot']['snapshot_id']
    freeze('output/character_skills/profiles/rules.json')
    for name in ['charainfo','skilllist','bossinfo']:
        freeze(f'output/cache_full_20261015_v3/decoded/{name}.data5.json.raw')
    for folder in ['output/ordinary_effects/ability1095','output/character_skills/boss_heal_types','output/boss_heal']:
        for path in (ROOT/folder).iterdir():
            if path.is_file() and path.suffix in ['.md','.json','.txt']:
                assert path.stat().st_size<4*1024**2
                freeze(path.relative_to(ROOT).as_posix())
    for name in ['card_page_inference_b11_sa1095.py','card_page_inference_b12_1095ext.py','skilllist_types.py','boss_heal_types.py','rules.py']:
        freeze('scripts/character_skills/'+name)
    # Prior common knowledge is supplied equally, not rediscovered in just one arm.
    freeze('output/skill_mechanism_trial/20261104/review/REPORT.md')
    rows={x['row_id']:x for x in targets}
    ledger=ROOT/'output/character_skills/effect_ledger/ledger.jsonl'
    before=ledger.stat(); digest=hashlib.sha256()
    for x in targets: x['baseline_effects']=[]
    with ledger.open('rb') as f:
        for line in f:
            digest.update(line); x=json.loads(line)
            if x['record_type']=='description' and x['row_id'] in rows:
                rows[x['row_id']]['baseline_description']=x
            if x['record_type']=='effect' and x['description_ref'] in rows:
                rows[x['description_ref']]['baseline_effects'].append(x)
    after=ledger.stat()
    assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    manifest['ledger_source']={'sha256':digest.hexdigest(),'bytes':after.st_size}
    for t in targets:
        card=freeze(f'output/character_skills/pages/{t["cid"]}/card.json')
        row=next(r for g in card['groups'] for s in g['skills'] for r in s['rows'] if r['row_id']==t['row_id'])
        assert not row['answers']
        assert t['baseline_description']['input_snapshot']['snapshot_id']==manifest['snapshot']
        assert t['baseline_effects'] and all(x['status']=='unresolved' for x in t['baseline_effects'])
        t['baseline_answers']=[]
    for rel,info in manifest['files'].items(): assert sha((ROOT/rel).read_bytes())==info['sha256'],rel
    save(PACKET/'targets.json',targets)
    manifest['files']['targets.json']={'sha256':sha((PACKET/'targets.json').read_bytes()),'bytes':(PACKET/'targets.json').stat().st_size}
    manifest['finished_at']=now()
    manifest['total_bytes']=sum(x['bytes'] for x in manifest['files'].values())
    assert manifest['total_bytes']<100*1024**2
    save(PACKET/'manifest.json',manifest)
    a=[x['task_id'] for x in targets if x['family']=='attack1095']; h=[x['task_id'] for x in targets if x['family']=='heal108']
    interleaved=[]
    for i in range(8):
        interleaved+=a[i*3:i*3+3]
        if i<len(h): interleaved.append(h[i])
    protocol={
        'frozen_at':now(),'snapshot':manifest['snapshot'],'selection':'24 attack1095 (8 plain,8 two-attribute,8 >=3-attribute); one heal108 stage per each of7 other cards; YG priority then fixed hash; no value-based selection',
        'targets':len(targets),'cards':len({x['cid'] for x in targets}),'seed':SEED,
        'arms':{'card_serial':interleaved,'family_serial':a+h,'parallel_attack':a,'parallel_heal':h},
        'method':{'card_serial':'One fresh agent, card-first in fixed interleaved order; natural reuse and helpers allowed, no deliberate repeated work; do not pre-solve all targets.',
                  'family_serial':'One fresh agent; study shared mechanisms and decision criteria first, then batch cards in family order; per-card validation required.',
                  'parallel':'Two fresh agents with same family-first approach, each owns one family, no shared results.'},
        'timing':'Real UTC start before reading packet; append phase timestamps when events occur. Never synthesize task durations. Separate mechanism study/card validation/packaging. Bulk script execution time is not human/agent reasoning time. Each arm 20min soft budget; report incomplete work.',
        'comparison':'A vs B = grouping/batching operational contrast; B vs C = parallel deployment contrast. Equal outcome comparison only after independent review, else report accuracy/coverage tradeoff. One run, agent variance and scheduling wave confounds; no significance or universal speed claims.',
        'dispatch':'A/B simultaneously first, C two agents in second wave due to available slots. Record observed span AND summed agent times; never report simulated sum-minus-max as measured speedup. All agents same inherited model; no history.',
        'review':'Blind source-first independent review after all submissions frozen; reviewer may do blind study during second wave but cannot see submissions before freeze.',
        'counting':'Distinct effect_id+source+field accepted answers. Confirmed description bindings, inferred scoped candidates, raw observations separate. Deduplicate arms, report source record count and card count. No promotion and no new formulas unless separately proved.',
        'authority':'Only input packet readable for research; only own arm writable. No production import or execution, native execution, installation, external services, C15 changes, or subdelegation.',
        'output_contract':'task_results.json: arm,started_at,finished_at,tasks[]. Each task task_id,cid,row_id,japanese,status,answers[],remaining_unknowns,evidence. Each answer effect_id,field_path,raw_value,rule_key,value,unit,conditions,numeric_evidence,association_evidence,source{layer,table,record_id,json_pointer,input_relative_path},novelty_category. Observations outside answers. timing.json real phases and per-task timing if observable; otherwise mark grouped batch timing; REPORT.md; validation script/results. Same schema all arms.',
    }
    save(BASE/'protocol.json',protocol)
    for arm in [*protocol['arms'],'review']: (BASE/arm).mkdir(exist_ok=True)
    print(json.dumps({'targets':len(targets),'cards':31,'bytes':manifest['total_bytes'],'snapshot':manifest['snapshot'],'families':{'attack1095':24,'heal108':7}}))

if __name__=='__main__': main()
