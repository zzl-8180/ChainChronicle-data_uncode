
from pathlib import Path
import json,gzip,hashlib,os,sys
root=Path.cwd();out=root/'output/storage_retention/recycle_g1_20261027'
def h(p):
 z=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):z.update(b)
 return z.hexdigest()
if sys.argv[1]=='before':
 prot=json.loads((out/'protection_manifest_v3.json').read_text(encoding='utf-8'))
 added=['output/character_skills/'+x+'/' for x in ['cycle2_rectification_20261026','mana_b_batch_20261026','mana_ledger_mapping_20261026','s5_terrain_20261026']]
 prot['prefixes']=sorted(set(prot['prefixes']+added));prot['snapshot_scope_notice']='补充基线在归档运行期间采集；源均只读，不冒充回收前冻结全项目'
 with (out/'protection_manifest_v4.json').open('x',encoding='utf-8') as f:json.dump(prot,f,ensure_ascii=False,indent=2)
 bases=added+['output/character_skills/pages/_batch/retained_payloads/']+['output/character_skills/pages/'+r for r in prot['protected_runs']]
 pages=root/'output/character_skills/pages'
 paths={p.relative_to(root).as_posix() for p in pages.iterdir() if p.is_file()}
 for base in bases:
  for d,dirs,files in os.walk(root/base,followlinks=False):paths.update((Path(d)/n).relative_to(root).as_posix() for n in files)
 with gzip.open(out/'protection_supplement_before.jsonl.gz','xt',encoding='utf-8') as f:
  for name in sorted(paths):
   p=root/name
   try:row={'path':name,'bytes':p.stat().st_size,'sha256':h(p)}
   except OSError as ex:row={'path':name,'error':str(ex)}
   f.write(json.dumps(row,ensure_ascii=False)+'\n')
 print('SUPPLEMENT_SNAPSHOT',len(paths),flush=True)
else:
 n=0;changes=[];errors=[]
 with gzip.open(out/'protection_supplement_before.jsonl.gz','rt',encoding='utf-8') as f,gzip.open(out/'protection_supplement_after.jsonl.gz','xt',encoding='utf-8') as dst:
  for line in f:
   old=json.loads(line);p=root/old['path']
   try:
    row={'path':old['path'],'bytes':p.stat().st_size,'sha256':h(p)};row['same']=row['sha256']==old.get('sha256') and row['bytes']==old.get('bytes')
    if not row['same']:changes.append(row)
   except OSError as ex:row={'path':old['path'],'error':str(ex)};errors.append(row)
   dst.write(json.dumps(row,ensure_ascii=False)+'\n');n+=1
 result={'status':'PASS_SUPPLEMENT_HASH' if not changes and not errors else 'CONCURRENT_CHANGE_OR_ERROR_REVIEW_REQUIRED','files':n,'changes':changes,'errors':errors,'scope':'保护清单全部精确run、retained_payloads整树、四个补充周期目录、pages根文件；不含所有原始输入/媒体/依赖','capture_timing':'G1归档期间补充采集'}
 with (out/'protection_supplement_postcheck.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps({'status':result['status'],'files':n,'changes':len(changes),'errors':len(errors)}),flush=True)
