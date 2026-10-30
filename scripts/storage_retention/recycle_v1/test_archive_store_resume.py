
from pathlib import Path
import importlib.util,csv,gzip,json,hashlib,zipfile,uuid,unittest
ROOT=Path.cwd();BASE=ROOT/'work/storage_recycle_g1_20261027/resume_tests'/uuid.uuid4().hex;BASE.mkdir(parents=True)
spec=importlib.util.spec_from_file_location('resume_archive',ROOT/'scripts/storage_retention/recycle_v1/archive_store_resume.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def sha(b):return hashlib.sha256(b).hexdigest()
def fixture(name):
 root=BASE/name;root.mkdir();vault=root/'vault';vault.mkdir()
 values=[b'closed original'*50,b'incomplete content'*50,b'closed original'*50,b'new historical variant'*100]
 rows=[];old=[]
 for i,data in enumerate(values,1):
  rel=f'output/character_skills/pages/_batch/ge60/runs/20261019T010101000000Z-12345678/transactions/{i}/backup/card.json';p=root/rel;p.parent.mkdir(parents=True);p.write_bytes(data)
  row={'path':rel,'bytes':len(data),'sha256':sha(data),'classification':'ELIGIBLE_A'};rows.append(row)
  if i<=2:
   st=p.stat();meta=a.snapshot(st);old.append({**{k:row[k] for k in ['path','bytes','sha256']},'volume':f'volume-{i:06d}.zip','member':a.member_name(row['sha256'],len(data)),'mtime_ns':meta['mtime_ns'],'metadata':meta})
 m=root/'manifest.csv.gz'
 with gzip.open(m,'wt',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 (vault/'plan_manifest.csv.gz').write_bytes(m.read_bytes())
 with zipfile.ZipFile(vault/'volume-000001.zip','w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(old[0]['member'],values[0])
 (vault/'volume-000002.zip').write_bytes(b'PK incomplete retained diagnostic')
 events=[{'event':'manifest_snapshotted','sha256':sha(m.read_bytes())},{'event':'volume_closed_pending_readback','name':'volume-000001.zip','bytes':(vault/'volume-000001.zip').stat().st_size,'sha256':sha((vault/'volume-000001.zip').read_bytes())}]
 (vault/'build_events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events),encoding='utf-8')
 (vault/'index.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in old),encoding='utf-8')
 return root,m,vault,rows
class Tests(unittest.TestCase):
 def test_resume_restore_and_preserve(self):
  r,m,v,rows=fixture('normal');before={p.name:sha(p.read_bytes()) for p in v.iterdir()}
  report=a.resume(r,m,v,15,1);self.assertEqual(report['status'],'PASS');self.assertEqual(report['resumption']['reused_source_paths'],1)
  self.assertEqual(report['statistics']['source_paths'],4);self.assertEqual(report['statistics']['unique_contents'],3)
  for name,digest in before.items():self.assertEqual(sha((v/name).read_bytes()),digest)
  a.load_verified(v);req=r/'request.json';req.write_text(json.dumps([x['path'] for x in rows]),encoding='utf-8');dest=r/'恢复 中文 space'
  a.restore(v,req,dest)
  for x in rows:self.assertEqual(sha((dest/x['path']).read_bytes()),x['sha256'])
  with self.assertRaises(a.ArchiveError):a.resume(r,m,v,15,1)
 def test_bad_closed_volume_stops_before_outputs(self):
  r,m,v,rows=fixture('badclosed');p=v/'volume-000001.zip';p.write_bytes(p.read_bytes()+b'changed')
  with self.assertRaises(a.ArchiveError):a.resume(r,m,v,15,1)
  self.assertFalse((v/'index_resumed.jsonl').exists());self.assertTrue((r/rows[0]['path']).exists())
 def test_changed_unprocessed_source_fails_closed(self):
  r,m,v,rows=fixture('changedsource');(r/rows[1]['path']).write_bytes(b'changed')
  with self.assertRaises(a.ArchiveError):a.resume(r,m,v,15,1)
  self.assertEqual(json.loads((v/'build_report.json').read_text())['status'],'FAIL')
 def test_manifest_binding_mismatch(self):
  r,m,v,rows=fixture('badmanifest');m.write_bytes(m.read_bytes()+b'changed')
  with self.assertRaises(a.ArchiveError):a.resume(r,m,v,15,1)
 def test_quarantine_is_explicitly_preserved_and_checked(self):
  r,m,v,rows=fixture('quarantine');a.resume(r,m,v,15,1);(v/'volume-000002.zip').write_bytes(b'changed')
  with self.assertRaises(a.ArchiveError):a.load_verified(v)
 def test_budget_counts_existing_files(self):
  r,m,v,rows=fixture('budget')
  with self.assertRaises(a.ArchiveError):a.resume(r,m,v,15,0)
  self.assertFalse((v/'index_resumed.jsonl').exists())
suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests);res=unittest.TextTestRunner(verbosity=2).run(suite)
d={'status':'PASS' if res.wasSuccessful() else 'FAIL','tests_run':res.testsRun,'failures':res.failures,'errors':res.errors,'module_sha256':sha((ROOT/'scripts/storage_retention/recycle_v1/archive_store_resume.py').read_bytes()),'fixture_root':str(BASE)}
(BASE/'test_result.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(d,ensure_ascii=False));raise SystemExit(0 if res.wasSuccessful() else 1)
