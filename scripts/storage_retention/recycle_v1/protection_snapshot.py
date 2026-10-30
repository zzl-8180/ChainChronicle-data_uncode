
from pathlib import Path
import gzip,csv,json,hashlib,sys,os
root=Path.cwd();out=root/'output/storage_retention/recycle_g1_20261027'
mode=sys.argv[1]; paths=set()
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
if mode=='before':
 with gzip.open(out/'plan_manifest_v3.csv.gz','rt',encoding='utf-8-sig') as f:
  paths.update(r['path'] for r in csv.DictReader(f) if r['classification']!='ELIGIBLE_A')
 for base in ['output/character_skills/profiles','output/character_skills/effect_ledger','output/character_skills/crit_absorb_20261026','output/character_skills/s5_nonterrain_20261026','output/character_skills/inference_inventory','output/character_skills/review']:
  if (root/base).exists():
   for d,dirs,files in os.walk(root/base,followlinks=False):
    dirs[:]=[n for n in dirs if not (Path(d)/n).is_symlink()]
    paths.update((Path(d)/n).relative_to(root).as_posix() for n in files)
 for d in (root/'output/character_skills/pages').iterdir():
  if d.is_dir() and d.name.isdigit():paths.update(p.relative_to(root).as_posix() for p in d.iterdir() if p.is_file())
 prot=json.loads((out/'protection_manifest_v3.json').read_text(encoding='utf-8'))
 paths.update(x['path'] for x in prot['observed_sources']); paths.update(x['consumer'] for x in prot['fixed_consumers'])
 paths.update(prot['exact_source_holds'])
 with gzip.open(out/'protection_hash_before.jsonl.gz','xt',encoding='utf-8') as f:
  for name in sorted(paths):
   p=root/name
   try:
    before=p.stat();sha=digest(p);after=p.stat();row={'path':name,'sha256':sha,'bytes':after.st_size,'stable':(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)}
   except OSError as ex:row={'path':name,'error':str(ex)}
   f.write(json.dumps(row,ensure_ascii=False)+'\n')
 print('SNAPSHOT',len(paths),flush=True)
else:
 changed=[];errors=[];n=0
 with gzip.open(out/'protection_hash_before.jsonl.gz','rt',encoding='utf-8') as f,gzip.open(out/'protection_hash_after.jsonl.gz','xt',encoding='utf-8') as dst:
  for line in f:
   old=json.loads(line);p=root/old['path']
   try:
    row={'path':old['path'],'sha256':digest(p),'bytes':p.stat().st_size};row['same']=row['sha256']==old.get('sha256') and row['bytes']==old.get('bytes')
    if not row['same']:changed.append(row)
   except OSError as ex:row={'path':old['path'],'error':str(ex)};errors.append(row)
   dst.write(json.dumps(row,ensure_ascii=False)+'\n');n+=1
 result={'status':'PASS_SCOPED_HASH' if not changed and not errors else 'CONCURRENT_CHANGE_OR_ERROR_REVIEW_REQUIRED','files':n,'changed':changed,'errors':errors,'scope':'v3 protected seed rows, P ZIPs, formal per-card files, profiles/effect ledger, cycle task outputs, character review and live pointers; not complete raw/media/dependency tree'}
 with (out/'protection_postcheck.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps({'status':result['status'],'files':n,'changes':len(changed),'errors':len(errors)}),flush=True)
