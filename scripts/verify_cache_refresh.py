"""Validate refreshed cache against retained base, without overwriting either."""
import json,hashlib,tarfile,csv
from pathlib import Path
from collections import Counter
P=Path('output/phone_refresh_20261015');D=Path('output/cache_refresh_20261015');OLD=Path('output/cache_full_20261015_v3');BASE='raw/phone_20261015_full_02';NEW='raw/phone_20261015_refresh_02';WORK=Path('work/phone_20261015_refresh_02')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
plan=load(P/'plan.json');prefix=plan['base'];selected={r['relative']:r for r in plan['files']};checks=[];payloads={}
with tarfile.open(NEW+'/external_cache.tar') as arc:
 for m in arc:
  if not m.isfile():continue
  assert m.name in selected
  digest=hashlib.sha256(arc.extractfile(m).read()).hexdigest();local=WORK/m.name
  assert sha(local)==digest and local.stat().st_size==selected[m.name]['size']
  payloads[m.name]=digest
assert set(payloads)==set(selected)
checks.append({'name':'242_archive_members_equal_work_copy','pass':True,'files':len(payloads)})
a=load(OLD/'decode_report.json');b=load(D/'decode_report.json');byname={r['filename']:r for r in a['files']};data5=[]
for r in b['files']:
 old=byname[r['filename']]
 assert r['status']=='DECODED' and r['source_sha256']==old['source_sha256'] and r['json_raw_sha256']==old['json_raw_sha256']
 assert sha(r['source'])==r['source_sha256'] and sha(r['json_file'])==r['json_raw_sha256']
 assert Path(r['json_file']).read_bytes()==Path(old['json_file']).read_bytes()
 data5.append({'filename':r['filename'],'ciphertext_sha256':r['source_sha256'],'json_sha256':r['json_raw_sha256'],'status':'BYTE_IDENTICAL_TO_V3','tables':r['tables']})
assert len(data5)==77;save(D/'data5_comparison.json',data5)
checks.append({'name':'77_ciphertexts_and_full_json_identical','pass':True})
oldrecords=[json.loads(l) for l in (OLD/'records.jsonl').open(encoding='utf-8')];newrecords=[json.loads(l) for l in (D/'records.jsonl').open(encoding='utf-8')]
assert len(oldrecords)==len(newrecords)==39047
for a,b in zip(oldrecords,newrecords):
 for key in ('record_key','source_key','layer','table','table_path','source_sha256','location','raw','analysis_named_table'):assert a[key]==b[key],(key,a['record_key'])
checks.append({'name':'39047_records_values_types_order_locations_unchanged','pass':True})
oldmembers={}
with tarfile.open(BASE+'/external_cache.tar') as arc:
 for m in arc:
  if m.isfile():oldmembers[m.name]=(m.size,int(m.mtime))
stat=load(P/'stat.json');inventory=[json.loads(l) for l in (P/'inventory.jsonl').open(encoding='utf-8')]
assert {r['path']:r['size'] for r in stat}=={r['path']:r['size'] for r in inventory}
rows=[]
for r in stat:
 name=r['path'][len(prefix):]
 if name not in selected:assert oldmembers[name]==(r['size'],r['mtime'])
 rows.append({'path':name,'bytes':r['size'],'phone_mtime':r['mtime'],'archive':NEW+'/external_cache.tar' if name in selected else BASE+'/external_cache.tar','archive_member':name,'work_file':str(WORK/name) if name in selected else str(Path('work/phone_20261015_full_02')/name),'basis':'FRESHLY_COLLECTED_LOCAL_HASH' if name in selected else 'PRIOR_ACQUISITION_SAME_PATH_SIZE_MTIME','sha256_this_refresh':payloads.get(name),'limit':'not atomic; unchanged media not rehashed on phone'})
assert len(rows)==68993
with (D/'composite_inventory.jsonl').open('w',encoding='utf-8') as f:
 for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
checks.append({'name':'68993_paths_have_explicit_archive_provenance','pass':True})
newnames=[r for r in rows if r['path'] not in oldmembers];assert len(newnames)==165 and all(r['path'].endswith('.bdl') for r in newnames)
with (D/'added_resources.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(newnames[0]));w.writeheader();w.writerows(newnames)
save(D/'added_resources.json',newnames)
coverage=[]
for category,extension in [('data5结构化文件','.data5'),('bdl容器','.bdl'),('其他文件',None)]:
 count=sum((Path(r['path']).suffix==extension if extension else Path(r['path']).suffix not in ('.data5','.bdl')) for r in rows)
 coverage.append({'category':category,'expected_in_phone_listing':count,'available_base_plus_refresh':count,'freshly_collected':sum((Path(r['path']).suffix==extension if extension else Path(r['path']).suffix not in ('.data5','.bdl')) for r in rows if r['path'] in selected),'decoded_files':77 if extension=='.data5' else None,'exported_record_views':39047 if extension=='.data5' else None,'remaining':'字段解释及既有未关联项仍保留' if extension=='.data5' else '结构化目标语义未知，不能按扩展名排除','needs_phone':'当前比较无需手机；全游戏/私有范围未知'})
save(D/'coverage_audit.json',coverage)
with (D/'coverage_audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(coverage[0]));w.writeheader();w.writerows(coverage)
save(D/'checks.json',{'status':'PASS','checks':checks,'prior_native_validation':'reused only after exact ciphertext and JSON match; no fresh native execution claimed','new_resources':165,'data5_changed':0,'limits':['No full-game index','No atomic snapshot','Same-size/time media not content-compared','No new semantic interpretations']})
print(json.dumps({'checks':len(checks),'data5_identical':77,'new_bdl':165,'composite_files':len(rows),'coverage':coverage},ensure_ascii=False))
