
from pathlib import Path
import json,hashlib,sys,importlib.util
root=Path.cwd();out=root/'output/storage_retention/recycle_g1_20261027';dest=root/'work/storage_recycle_g1_20261027/完整恢复 中文 space'
coverage=json.loads((out/'restore_coverage_v3.json').read_text(encoding='utf-8'))
run=coverage['complete_small_run']
spec=importlib.util.spec_from_file_location('historical_replay_guard',root/'scripts/storage_retention/replay_guard.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
plan=json.loads((root/run/'plan.json').read_text(encoding='utf-8'));n=len(set(map(str,plan['cids'])))
original=mod.inspect_old([root/run],expected_count=n)
assert original['status']=='INPUTS_COMPLETE',original['errors']
metadata=[run+'/plan.json']
for cid in plan['cids']:
 metadata +=[run+'/transactions/'+str(cid)+'/backup/'+name for name in ['before.json','receipt.json']]
copies=[]
for rel in metadata:
 src=root/rel;dst=dest/rel;data=src.read_bytes();dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(data)
 sha=hashlib.sha256(data).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==sha
 copies.append({'path':rel,'sha256':sha,'bytes':len(data)})
restored=mod.inspect_old([dest/run],expected_count=n)
assert restored['status']=='INPUTS_COMPLETE',restored['errors']
a={k:mod.digest(v) for k,v in original['paths'].items()};b={k:mod.digest(v) for k,v in restored['paths'].items()};assert a==b
paths=json.loads((out/'restore_request_v3.json').read_text(encoding='utf-8'));checks=[]
for p in paths:
 original_hash=mod.digest(root/p);restored_hash=mod.digest(dest/p);assert original_hash==restored_hash
 checks.append({'path':p,'sha256':restored_hash,'bytes':(dest/p).stat().st_size})
report={'status':'PASS','fresh_process':True,'consumer':'scripts/storage_retention/replay_guard.py:inspect_old','consumer_sha256':mod.digest(root/'scripts/storage_retention/replay_guard.py'),'consumer_scope':'真实旧run输入完整性和收据/前像SHA消费；不是完整历史语义审查重跑','run':run,'cards':n,'source_status':original['status'],'restored_status':restored['status'],'same_hash_by_cid':a==b,'restored_files':checks,'metadata_copies':copies,'coverage':coverage,'source_deleted':False}
with (out/'restore_consumer_result.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'PASS','cards':n,'restore_files':len(checks),'metadata_copies':len(copies)},ensure_ascii=False))
