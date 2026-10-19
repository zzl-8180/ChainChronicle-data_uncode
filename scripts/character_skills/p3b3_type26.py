"""P3B3 source ledger, before/after accounting and bounded regression checks."""
from __future__ import annotations
import collections
import csv
import hashlib
import json
import os
import subprocess
import struct
import sys
from pathlib import Path
import common as C
import type26_mana as M

BASE=C.ROOT/'output/character_skills'
OUT=BASE/'type26_mana'
BEFORE=C.ROOT/'work/character_skills_p3b3/before'


def rows(path):
    return [json.loads(s) for s in Path(path).open(encoding='utf-8')]


def holders(records):
    for r in records:
        yield r['rec_key'],r
        for ch in r['children']:yield r['rec_key'],ch


def canon(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))


def main():
    C.enable_utf8_console()
    old=rows(BEFORE/'records.jsonl');now=rows(BASE/'profiles/records.jsonl')
    oldp=rows(BEFORE/'profiles.jsonl');profiles=rows(BASE/'profiles/profiles.jsonl')
    checks=[]
    def check(name,passed,**detail):checks.append(dict(name=name,passed=bool(passed),**detail))
    def answer_multiset(recs):
        return collections.Counter((parent,r['table'],r['record_id'],canon(a))
            for parent,r in holders(recs) for a in r['answers'])
    ca,cb=answer_multiset(old),answer_multiset(now)
    missing=ca-cb;added=cb-ca
    check('old_complete_answer_objects_and_multiplicity',not missing,lost=sum(missing.values()),before=sum(ca.values()))
    check('only_type26_param0_added',all(json.loads(k[3])['rule_key']=='skilllist|26|/param0' for k in added),added=sum(added.values()))
    old_rules=C.load_json(BEFORE/'rules.json');new_rules=C.load_json(BASE/'profiles/rules.json')
    check('old_rule_objects',all(new_rules[k]==v for k,v in old_rules.items()),old_rules=len(old_rules))
    old_by={r['rec_key']:r for r in old};new_by={r['rec_key']:r for r in now}
    baseline_lost=[];binding_lost=[]
    for key,r in old_by.items():
        nr=new_by[key]
        if r['baseline_answers']!=nr['baseline_answers']:baseline_lost.append(key)
        for f in r['fragments']:
            if f.get('binding') or f['status']=='BASELINE_DESCRIPTION_ANSWER':
                if f not in nr['fragments']:binding_lost.append(key)
    check('old_baseline_and_type8_bindings_complete_objects',not baseline_lost and not binding_lost,
          baseline_lost=baseline_lost,binding_lost=binding_lost)
    check('type8_accepted_artifact_unchanged',(BEFORE/'accepted_type8.jsonl').read_bytes()==
          (BASE/'description_bindings/type8/accepted.jsonl').read_bytes())
    s0=C.load_json(BEFORE/'summary.json');s1=C.load_json(BASE/'profiles/summary.json')
    t0,t1=s0['totals'],s1['totals']
    check('status_and_accounting',s0['status_counts']==s1['status_counts'] and
          t1['baseline_answers']==101 and t1['broken_links']==3 and t1['descriptions']==41595 and
          t1['rule_answers_in_reviewed_view']==t0['rule_answers_in_reviewed_view'] and
          t1['rule_answers']-t0['rule_answers']==t0['unexplained_fields']-t1['unexplained_fields'])
    uses=collections.defaultdict(list)
    for p in profiles:
        for g in p['groups']:
            for ref in g['records']:
                uses[ref['rec_key']].append(dict(cid=p['cid'],name=p['name'],group=g['group'],
                    reference_field=ref['reference_field'],character_source=p['charainfo_source']))
    tab=C.Tables();bindings=[];field_ledger=[];affected=set();pointers_ok=True
    for parent,r in holders(now):
        aa=[a for a in r['answers'] if r['table']=='skilllist' and r['effect_type']==26 and a['f']=='/param0']
        if not aa:continue
        raw,layer=tab('skilllist').get(r['record_id'])
        loc=C.location('skilllist',r['record_id'],layer,raw)
        pointers_ok &= r['source']==loc and all(a['raw']==raw['param0'] and a['scope']=='BY_TYPE_EXTRAPOLATED' for a in aa)
        affected.update(u['cid'] for u in uses[parent])
        field_ledger.append(dict(parent_rec_key=parent,table=r['table'],record_id=r['record_id'],source=loc,
            raw_record=raw,answers=aa,page_references=uses[parent]))
    check('all_new_field_sources_and_scope',pointers_ok,normalized_rows=len(field_ledger))
    # Independent path: open the original JSON files directly, walk each pointer,
    # and derive the count without C.Tables/location or M.signed_count/convert.
    documents={};payloads={};raw_results=[]
    for item in field_ledger:
        source=item['source']
        # CACHE original_file is the encrypted acquisition input; source_key names
        # its declared decoded JSON in the same frozen snapshot, not that binary.
        path=(C.ROOT/'output/cache_full_20261015_v3/decoded'/source['source_key'].split('/',1)[1]
              if source['layer']=='CACHE' else C.ROOT/source['original_file'])
        if str(path) not in documents:
            payloads[str(path)]=path.read_bytes()
            documents[str(path)]=json.loads(payloads[str(path)])
        raw=documents[str(path)]
        for part in source['json_pointer'].split('/')[1:]:
            part=part.replace('~1','/').replace('~0','~')
            raw=raw[int(part)] if isinstance(raw,list) else raw[part]
        blob=(payloads[str(path)][source['byte_begin']:source['byte_end_exclusive']]
              if source['layer']=='CACHE' else canon(raw).encode('utf-8'))
        sha=hashlib.sha256(blob).hexdigest()
        value=raw['param0'];v=struct.unpack('<f',struct.pack('<f',value))[0]
        assert 0<=v<=3, 'this raw cross-check explicitly covers declared finite source range0..3'
        count=int(v)
        expected=(f'战斗开始时按持有者职业授予 {count} 个基础玛那（param0产线）' if count else
                  f'原值 {value} → 原生整数化 {count} < 1：param0这条基础产线不授予玛那')
        passed=(sha==source['raw_record_sha256'] and json.loads(blob)==raw and raw==item['raw_record'] and
                all(a['raw']==value and a['value']==expected for a in item['answers']))
        raw_results.append(dict(parent_rec_key=item['parent_rec_key'],record_id=item['record_id'],
            original_file=str(path.relative_to(C.ROOT)),input_file=source['original_file'],json_pointer=source['json_pointer'],raw=value,
            count_derived_independently=count,passed=passed))
    C.write_json(OUT/'raw_crosscheck.json',dict(rows=len(raw_results),
        distinct_sources=len({(r['original_file'],r['json_pointer']) for r in raw_results}),
        derivation='stdlib direct JSON pointer + SHA256 (APK canonical, CACHE exact byte range) + float32→int; no common/rules/new converter for derivation',
        samples=raw_results))
    check('independent_raw_every_new_normalized_row',len(raw_results)==sum(added.values()) and
          all(r['passed'] for r in raw_results),rows=len(raw_results),distinct_sources=len({(r['original_file'],r['json_pointer']) for r in raw_results}))
    for ident in M.REVIEWED:
        key=f'skilllist|{ident}|APK|ability=26';r=new_by[key];prev=old_by[key]
        raw,layer=tab('skilllist').get(ident)
        f=next(f for f in r['fragments'] if f.get('binding'))
        cp=[]
        for u in uses[key]:
            cr,cl=tab('charainfo').get(u['cid']);idx=int(u['reference_field'].split('[')[1].split(']')[0])
            assert cr['skillid'][idx]==ident and u['character_source']==C.location('charainfo',u['cid'],cl,cr)
            cp.append(dict(u,character_record=cr))
        bindings.append(dict(record_id=ident,decision='INCLUDED_PENDING_INDEPENDENT_REVIEW',source=r['source'],
            raw_record=raw,fragment_before=prev['fragments'],fragment_after=f,characters=cp,
            native_evidence='output/character_skills/type26_mana/native_evidence.json',limits=M.LIMITS))
    check('reviewed_two_pure_sentences',len(bindings)==2 and all(x['raw_record']['sub']==[] and
          len(x['fragment_before'])==1 and x['fragment_before'][0]['status']=='UNEXPLAINED_FRAGMENT' for x in bindings))
    check('missing_null_values_stay_unexplained',all(not any(a['f']=='/param0' for a in r['answers'])
          for _,r in holders(now) if r['table']=='skilllist' and r['effect_type']==26 and
          ('param0' not in (tab('skilllist').get(r['record_id'])[0] or {}) or
           (tab('skilllist').get(r['record_id'])[0] or {}).get('param0') is None)))
    # Guard tests alter the pinned record while preserving the actual source stamp.
    raw,layer=tab('skilllist').get(3101);entry=dict(table='skilllist',layer=layer,reference_id=3101,
        record=raw,source=C.location('skilllist',3101,layer,raw))
    ans=new_by['skilllist|3101|APK|ability=26']['answers'];fragment=M.REVIEWED[3101][1]
    check('positive_binding',M.bind_type26(entry,fragment,ans,[])[0] is not None)
    rejections=[]
    for bad in [dict(entry,layer='CACHE'),dict(entry,reference_id=3103),
                dict(entry,record=dict(raw,param0=2)),dict(entry,record=dict(raw,sub=[3102])),
                dict(entry,source=dict(entry['source'],raw_record_sha256='wrong'))]:
        rejections.append(M.bind_type26(bad,fragment,ans,[])[0] is None)
    check('pinned_binding_negative_guards',all(rejections),cases=len(rejections))
    check('wrong_fragment_or_child_rejected',M.bind_type26(entry,'マナを２つ持った状態で戦闘を開始する',ans,[])[0] is None
          and M.bind_type26(entry,fragment,ans,[{'record_id':3102}])[0] is None)
    with (BASE/'profiles/answers.csv').open(encoding='utf-8-sig',newline='') as stream:
        header=next(csv.reader(stream))
    check('csv_answer_contract','evidence_scope' in header and 'note' in header and 'unit' in header)
    # Default GBK CLI subprocesses; logs use bytes to avoid PowerShell transcoding.
    cli=[];env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936')
    for cid in sorted({x['cid'] for b in bindings for x in b['characters']})[:1]+[30236]:
        for flag in [[],['--json']]:
            run=subprocess.run([sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),
                '--cid',str(cid),*flag],cwd=C.ROOT,env=env,capture_output=True)
            log=OUT/f'cli_{cid}_{"json" if flag else "text"}.log';log.write_bytes(run.stdout+run.stderr)
            valid=run.returncode==0 and (not flag or json.loads(run.stdout.decode('utf-8'))['characters'][0]['cid']==cid)
            cli.append(dict(cid=cid,mode='json' if flag else 'text',returncode=run.returncode,passed=valid))
    check('cli_default_gbk',all(x['passed'] for x in cli),cases=cli)
    C.write_jsonl(OUT/'field_answers.jsonl',field_ledger)
    C.write_jsonl(OUT/'bindings.jsonl',bindings)
    C.write_csv(OUT/'bindings.csv',['record_id','fragment','field','raw','value','scope','cids'],
        [[b['record_id'],b['fragment_after']['t'],'/param0',b['raw_record']['param0'],
          b['fragment_after']['binding']['fields'][0]['value'],'BY_TYPE_EXTRAPOLATED',
          ','.join(str(u['cid']) for u in b['characters'])] for b in bindings])
    transitions=[dict(cid=a['cid'],before=a['status'],after=b['status']) for a,b in zip(oldp,profiles) if a['status']!=b['status']]
    increment=dict(field_answers_added_pages=t1['rule_answers']-t0['rule_answers'],
        field_answers_added_normalized_rows=t1['rule_answers_unique_records']-t0['rule_answers_unique_records'],
        field_answers_added_parent_holder_keys=t1['rule_answers_parent_holder_keys']-t0['rule_answers_parent_holder_keys'],
        field_affected_characters=len(affected),field_affected_cids=sorted(affected),
        field_source_records=len({(r['table'],r['record_id'],r['source']['layer']) for r in field_ledger}),
        fragments_added_unique_records=len(bindings),fragments_added_page_references=sum(len(b['characters']) for b in bindings),
        effect_slots_added_unique_records=2,effect_slots_added_page_references=sum(len(b['characters']) for b in bindings),
        binding_affected_cids=sorted({u['cid'] for b in bindings for u in b['characters']}),
        before_totals=t0,after_totals=t1,status_transitions=transitions,
        independent_review_status='P3B3_PENDING; earlier batch review conclusions do not cover this batch')
    C.write_json(OUT/'increment.json',increment)
    report=dict(generated_by='scripts/character_skills/p3b3_type26.py',checks=checks,
        passed=sum(c['passed'] for c in checks),total=len(checks))
    C.write_json(OUT/'validation.json',report)
    print(json.dumps({k:v for k,v in increment.items() if k not in ['before_totals','after_totals','field_affected_cids']},ensure_ascii=False))
    print(json.dumps(dict(checks=f"{report['passed']}/{report['total']}")))
    if report['passed']!=report['total']:raise SystemExit(1)


if __name__=='__main__':main()
