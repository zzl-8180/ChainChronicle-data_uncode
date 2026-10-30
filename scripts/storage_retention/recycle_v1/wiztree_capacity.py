
from pathlib import Path
import subprocess,json,time
root=Path.cwd();o=root/'output/storage_retention/recycle_g1_20261027';target=root/'output/character_skills/pages/_batch';csv=o/'wiztree_batch_directories.csv';assert not csv.exists()
args=['C:/Program Files/WizTree/WizTree64.exe',str(target),'/export='+str(csv),'/admin=0','/exportfiles=0','/exportfolders=1','/sortby=2']
t=time.perf_counter();record={'source':str(target),'mode':'read-only non-admin directory-only CSV','no_candidate_changes':True}
try:
 r=subprocess.run(args,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
 record.update(returncode=r.returncode,stdout=r.stdout.decode('utf-8',errors='replace')[:1000],stderr=r.stderr.decode('utf-8',errors='replace')[:1000])
except Exception as e:record['error']=str(e)
record.update(seconds=time.perf_counter()-t,export_exists=csv.exists(),bytes=csv.stat().st_size if csv.exists() else None)
(o/'wiztree_batch_result.json').open('x',encoding='utf-8').write(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps(record,ensure_ascii=False))
