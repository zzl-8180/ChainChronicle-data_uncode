
from pathlib import Path
import csv,gzip,json,hashlib,collections
out=Path('output/storage_retention/recycle_g1_20261027')
with gzip.open(out/'plan_manifest_v2.csv.gz','rt',encoding='utf-8-sig',newline='') as f:
 reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
extra=[]
for r in rows:
 if r['classification']=='ELIGIBLE_A' and '/runs/20261026T' in r['path']:
  r['classification']='PROTECTED';r['protection_reason']='本周期全部20261026前像保守保护，不依赖RELEASED或静态campaign列表';extra.append(r['path'])
with gzip.open(out/'plan_manifest_v3.csv.gz','xt',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
prot=json.loads((out/'protection_manifest_v2.json').read_text(encoding='utf-8'));prot['additional_protection']='全部/runs/20261026T及后续在途前像，RELEASED不解除';prot['extra_cycle_paths']=extra
with (out/'protection_manifest_v3.json').open('x',encoding='utf-8') as f:json.dump(prot,f,ensure_ascii=False,indent=2)
eligible={r['path']:r for r in rows if r['classification']=='ELIGIBLE_A'}
old=json.loads((out/'restore_sample_request.json').read_text(encoding='utf-8'))
coverage=old['coverage'];coverage['largest']=max(eligible,key=lambda k:int(eligible[k]['bytes']))
paths=set(p for p in old['paths'] if p in eligible);paths.add(coverage['largest'])
assert all(p in eligible for p in coverage['same_content_multiple_paths']+coverage['different_historical_versions']+[coverage['incident_restored_file']])
micro=set(coverage['same_content_multiple_paths']+coverage['different_historical_versions']+[coverage['incident_restored_file'],coverage['largest']])
assert len(micro)<=10 and sum(int(eligible[p]['bytes']) for p in micro)<=64*1024**2
with gzip.open(out/'micro_manifest.csv.gz','xt',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(eligible[p] for p in sorted(micro))
for name,obj in [('restore_request_v3.json',sorted(paths)),('micro_restore_request.json',sorted(micro)),('restore_coverage_v3.json',coverage)]:
 with (out/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
counts=collections.defaultdict(lambda:[0,0])
for r in rows:counts[r['classification']][0]+=1;counts[r['classification']][1]+=int(r['bytes'])
summary={'counts':dict(counts),'additional_cycle_protected':len(extra),'manifest_sha256':hashlib.sha256((out/'plan_manifest_v3.csv.gz').read_bytes()).hexdigest(),'micro_files':len(micro),'micro_bytes':sum(int(eligible[p]['bytes']) for p in micro),'restore_files':len(paths),'G2_approved':False}
with (out/'plan_summary_v3.json').open('x',encoding='utf-8') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
print(json.dumps(summary,ensure_ascii=False))
