
from pathlib import Path
import time,json,subprocess,sys
root=Path.cwd();out=root/'output/storage_retention/recycle_g1_20261027';vault=root/'output/storage_retention/vault_g1_checkpoint_20261027'
python=str(root/'.venv/Scripts/python.exe')
start=time.monotonic()
while not (vault/'build_report.json').exists():
 if time.monotonic()-start>7200:raise RuntimeError('Build report not available after bounded 2h; no dependent action')
 time.sleep(5)
# Report is exclusively written at end. Permit only bounded wait for completion of its write.
for attempt in range(10):
 try:build=json.loads((vault/'build_report.json').read_text(encoding='utf-8'));break
 except (json.JSONDecodeError,PermissionError):time.sleep(1)
else:raise RuntimeError('build report unreadable')
if build.get('status')!='PASS':raise RuntimeError('Build not PASS; no dependent action')
print('ARCHIVE_BUILD_PASS',json.dumps(build['statistics']),flush=True)
commands=[
 ['scripts/storage_retention/recycle_v1/archive_store_checkpoint.py','restore','--vault',str(vault),'--request',str(out/'restore_request_v3.json'),'--dest',str(root/'work/storage_recycle_g1_20261027/完整恢复 中文 space')],
 ['scripts/storage_retention/recycle_v1/validate_restored_consumer.py'],
 ['scripts/storage_retention/recycle_v1/protection_snapshot.py','after'],
 ['scripts/storage_retention/recycle_v1/protection_supplement.py','after']
]
results=[]
for i,args in enumerate(commands):
 print('START_POSTCHECK',i,args[0],flush=True)
 r=subprocess.run([python,'-X','utf8','-B',*args],cwd=root,capture_output=True)
 record={'step':i,'args':args,'returncode':r.returncode,'stdout':r.stdout.decode('utf-8',errors='replace'),'stderr':r.stderr.decode('utf-8',errors='replace')}
 with (out/('postprocess_step_'+str(i)+'.json')).open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
 results.append(record)
 print('FINISH_POSTCHECK',i,r.returncode,record['stdout'][-400:],flush=True)
 if r.returncode:raise RuntimeError('Postcheck failed; artifacts retained; no retry')
with (out/'postprocess_result.json').open('x',encoding='utf-8') as f:json.dump({'status':'PIPELINE_COMPLETED_CHECK_REPORTS','steps':results,'G2_approved':False},f,ensure_ascii=False,indent=2)
print('POSTPROCESS_COMPLETE_G2_STILL_BLOCKED',flush=True)
