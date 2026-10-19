"""P3B4 accounting and independent original-JSON audit; no prose bindings added."""
from __future__ import annotations
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import common as C

BASE=C.ROOT/'output/character_skills';OUT=BASE/'type9_crit'
BEFORE=C.ROOT/'work/character_skills_p3b4/before'


def rows(p):return [json.loads(s) for s in Path(p).open(encoding='utf-8')]
def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def holders(rr):
    for r in rr:
        yield r['rec_key'],r
        for ch in r['children']:yield r['rec_key'],ch


def main():
    C.enable_utf8_console();checks=[]
    def check(name,passed,**detail):checks.append(dict(name=name,passed=bool(passed),**detail))
    old=rows(BEFORE/'profiles/records.jsonl');now=rows(BASE/'profiles/records.jsonl')
    oldp=rows(BEFORE/'profiles/profiles.jsonl');newp=rows(BASE/'profiles/profiles.jsonl')
    def multiset(rr):return collections.Counter((parent,r['table'],r['record_id'],canon(a)) for parent,r in holders(rr) for a in r['answers'])
    ca,cb=multiset(old),multiset(now);missing=ca-cb;added=cb-ca
    check('old_complete_answer_objects_and_multiplicity',not missing,before=sum(ca.values()),lost=sum(missing.values()))
    check('only_type9_param0_added',all(json.loads(k[3])['rule_key']=='skilllist|9|/param0' for k in added),added=sum(added.values()))
    a=C.load_json(BEFORE/'profiles/rules.json');b=C.load_json(BASE/'profiles/rules.json')
    check('all_old_rule_objects_preserved',all(b[k]==v for k,v in a.items()),before=len(a),after=len(b))
    new_by={r['rec_key']:r for r in now};changed=[]
    for r in old:
        nr=new_by[r['rec_key']]
        if r['baseline_answers']!=nr['baseline_answers'] or r['fragments']!=nr['fragments']:changed.append(r['rec_key'])
    check('baseline101_and_all31_type8_type26_bindings_and_fragments_preserved',not changed,changed=changed)
    binding_paths=[p for p in (BEFORE/'description_bindings/type8').glob('*.json*')]
    binding_paths+=[p for p in (BEFORE/'type26_mana').glob('bindings.json*')]
    check('prior_binding_artifact_bytes_unchanged',all(p.read_bytes()==(BASE/p.relative_to(BEFORE)).read_bytes() for p in binding_paths),files=[str(p.relative_to(BEFORE)) for p in binding_paths])
    s0=C.load_json(BEFORE/'profiles/summary.json');s1=C.load_json(BASE/'profiles/summary.json');t0=s0['totals'];t1=s1['totals']
    desc_keys=['descriptions','descriptions_attributed','descriptions_with_hint','descriptions_from_baseline','descriptions_reviewed_bindings','descriptions_unexplained','fragments_attributed_confirmed']
    check('description_and_scope_accounting',all(t0[k]==t1[k] for k in desc_keys) and t1['baseline_answers']==101 and
          t1['broken_links']==3 and t0['rule_answers_in_reviewed_view']==t1['rule_answers_in_reviewed_view'] and
          t1['rule_answers']-t0['rule_answers']==t0['unexplained_fields']-t1['unexplained_fields'])
    uses=collections.defaultdict(list)
    for p in newp:
        for g in p['groups']:
            for ref in g['records']:uses[ref['rec_key']].append(dict(cid=p['cid'],name=p['name'],group=g['group'],reference_field=ref['reference_field']))
    ledger=[];affected=set()
    for parent,r in holders(now):
        if r['table']!='skilllist' or r['effect_type']!=9:continue
        aa=[a for a in r['answers'] if a['f']=='/param0']
        if not aa:continue
        affected.update(u['cid'] for u in uses[parent])
        ledger.append(dict(parent_rec_key=parent,record_id=r['record_id'],source=r['source'],answers=aa,page_references=uses[parent]))
    # Independent derivation: stdlib direct original-file pointers/hashes and literal
    # coefficient rendering, without C.Tables/location/rules or type9_bullet.convert.
    docs={};payloads={};results=[];source_rows={};nonfinite=[]
    for r in ledger:
        src=r['source'];p=(C.ROOT/'output/cache_full_20261015_v3/decoded'/src['source_key'].split('/',1)[1]
                          if src['layer']=='CACHE' else C.ROOT/src['original_file'])
        if p not in docs:payloads[p]=p.read_bytes();docs[p]=json.loads(payloads[p])
        raw=docs[p]
        for part in src['json_pointer'].split('/')[1:]:
            part=part.replace('~1','/').replace('~0','~');raw=raw[int(part)] if isinstance(raw,list) else raw[part]
        blob=(payloads[p][src['byte_begin']:src['byte_end_exclusive']] if src['layer']=='CACHE' else canon(raw).encode('utf-8'))
        v=raw['param0'];assert isinstance(v,(int,float)) and 0<=v<=2.25
        if v==1:direction='系数1（中性）；仍经float32和整数化，可能因精度变化'
        elif v==0:direction='下一次输入归零'
        elif v>1:direction='后续输入增加'
        else:direction='后续输入衰减'
        expected=f'贯通命中后伤害输入 ×{v:.7g}（{direction}；首次不乘本项；逐次整数化）'
        passed=(raw['ability']==9 and raw['skillid']==r['record_id'] and json.loads(blob)==raw and
                hashlib.sha256(blob).hexdigest()==src['raw_record_sha256'] and
                all(a['raw']==v and a['value']==expected and a['scope']=='BY_TYPE_EXTRAPOLATED' and
                    a['unit']=='无量纲系数（非概率/百分点）' and 'SHOT_THROUGH' in a['note'] and
                    'bCheckAbility=true' in a['note'] and '首次命中先用当前伤害输入' in a['note'] for a in r['answers']))
        results.append(dict(parent_rec_key=r['parent_rec_key'],record_id=r['record_id'],layer=src['layer'],
            original_file=str(p.relative_to(C.ROOT)),json_pointer=src['json_pointer'],raw=v,expected=expected,passed=passed))
        source_rows[(src['layer'],src['json_pointer'])]=dict(source=src,record=raw)
    C.write_json(OUT/'raw_crosscheck.json',dict(derivation='stdlib original JSON pointer + source hash + literal coefficient/direction; no new converter as oracle',
        rows=len(results),distinct_sources=len(source_rows),passed=sum(r['passed'] for r in results),results=results))
    check('all_new_rows_independently_read_from_original_json',all(r['passed'] for r in results) and len(results)==sum(added.values()),
          rows=len(results),sources=len(source_rows))
    # Every selected type9 record is separately accounted. CACHE wins the entire ID.
    selected={};inventory=[]
    for layer,path in [('APK',C.ROOT/'output/base_master/_mdSkill.json'),('CACHE',C.ROOT/'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')]:
        rr=json.loads(path.read_bytes())['skilllist'];ss=[(i,r) for i,r in enumerate(rr) if r.get('ability')==9]
        inventory.append(dict(layer=layer,records=len(ss),present=sum('param0'in r for _,r in ss),missing=sum('param0'not in r for _,r in ss),
            null=sum(r.get('param0','MISSING') is None for _,r in ss),zero=sum('param0'in r and r['param0']==0 for _,r in ss),
            distribution=dict(collections.Counter(str(r.get('param0','MISSING')) for _,r in ss))))
        # Override by ID for every cache record, including a different ability type.
        for i,r in enumerate(rr):selected[r['skillid']]=(layer,i,r)
    selected=[dict(layer=l,json_pointer=f'/skilllist/{i}',record=r) for l,i,r in selected.values() if r.get('ability')==9]
    missing_ids={r['record']['skillid'] for r in selected if 'param0'not in r['record'] or r['record']['param0'] is None}
    check('cache_id_precedence_no_field_borrowing',all(r['record_id'] not in missing_ids for r in ledger),missing_or_null_ids=sorted(missing_ids))
    # Absent/null are not converted and zero is retained, with its different answer.
    check('zero_retained_and_not_missing',any(r['raw']==0 and '归零' in r['expected'] for r in results))
    C.write_json(OUT/'source_inventory.json',dict(snapshot=C.SNAPSHOT_ID,source_counts=inventory,selected_records=len(selected),
        selected=selected,policy='CACHE whole record per ID; no field fallback; no raw mutation'))
    C.write_jsonl(OUT/'source_records.jsonl',list(source_rows.values()));C.write_jsonl(OUT/'field_answers.jsonl',ledger)
    transitions=[dict(cid=p['cid'],before=p['status'],after=q['status']) for p,q in zip(oldp,newp) if p['status']!=q['status']]
    source_counts=collections.Counter(s['source']['layer'] for s in source_rows.values())
    increment=dict(field_answers_added_pages=t1['rule_answers']-t0['rule_answers'],field_answers_added_normalized_rows=t1['rule_answers_unique_records']-t0['rule_answers_unique_records'],
        field_answers_added_parent_holder_keys=t1['rule_answers_parent_holder_keys']-t0['rule_answers_parent_holder_keys'],
        field_source_records=len(source_rows),field_source_layers=dict(source_counts),field_affected_characters=len(affected),field_affected_cids=sorted(affected),
        fragments_added_unique_records=0,fragments_added_page_references=0,effect_slots_added_unique_records=0,effect_slots_added_page_references=0,
        before_totals=t0,after_totals=t1,before_status=s0['status_counts'],after_status=s1['status_counts'],status_transitions=transitions,
        rejected_lead='暴击率(x−1)×100候选被原生身份和消费反证，未修改只读参考分析',independent_review_status='P3B4_PENDING')
    check('delta_three_calibers',len(ledger)==increment['field_answers_added_normalized_rows']==increment['field_answers_added_parent_holder_keys'] and
          sum(len(r['page_references']) for r in ledger)==increment['field_answers_added_pages'])
    check('character_status_zero_migration',not transitions and s0['status_counts']==s1['status_counts'])
    with (BASE/'profiles/answers.csv').open(encoding='utf-8-sig',newline='') as f:
        csvrows=list(csv.DictReader(f))
    # The shared CSV is compared to the same materialised answer set by the general verifier.
    check('csv_contract_and_new_coefficient',any('贯通命中后伤害输入' in canon(r) for r in csvrows) and 'evidence_scope' in csvrows[0])
    env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936');cli=[]
    sample_cids=sorted(affected)[:1]+[30236]
    for cid in sample_cids:
        for mode in ['text','json']:
            run=subprocess.run([sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),'--cid',str(cid),*(['--json'] if mode=='json' else [])],cwd=C.ROOT,env=env,capture_output=True)
            (OUT/f'cli_{cid}_{mode}.log').write_bytes(run.stdout+run.stderr)
            ok=run.returncode==0 and (mode!='json' or json.loads(run.stdout.decode('utf-8'))['characters'][0]['cid']==cid)
            cli.append(dict(cid=cid,mode=mode,passed=ok,returncode=run.returncode))
    check('related_cli_default_gbk',all(r['passed'] for r in cli),samples=cli)
    C.write_json(OUT/'increment.json',increment)
    report=dict(generated_by='scripts/character_skills/p3b4_type9.py',checks=checks,passed=sum(c['passed'] for c in checks),total=len(checks))
    C.write_json(OUT/'validation.json',report)
    print(json.dumps({k:v for k,v in increment.items() if k not in ['before_totals','after_totals','field_affected_cids']},ensure_ascii=False))
    print(json.dumps(dict(checks=f"{report['passed']}/{report['total']}")))
    if report['passed']!=report['total']:raise SystemExit(1)


if __name__=='__main__':main()
