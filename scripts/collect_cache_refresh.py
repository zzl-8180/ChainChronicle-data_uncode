"""Collect explicit refresh plan as read-only tar stream; preserve old snapshot."""
import json,subprocess,re,shlex
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
plan_dir=Path('output/phone_refresh_20261015');dest=Path('raw/phone_20261015_refresh_02')
plan=json.loads((plan_dir/'plan.json').read_text(encoding='utf-8'));probe=json.loads((plan_dir/'probe.json').read_text(encoding='utf-8'))
adb=str(Path('tools/platform-tools/adb.exe').resolve());devices=subprocess.check_output([adb,'devices'],text=True)
ready=[s.split()[0] for s in devices.splitlines()[1:] if s.split()[1:]==['device']];assert len(ready)==1
names=[]
for r in plan['files']:
 p=PurePosixPath(r['relative']);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] in ('files','cache')
 assert '\n' not in str(p) and '\0' not in str(p)
 names.append(str(p))
assert re.fullmatch(r'/storage/emulated/\d+/Android/data/com\.sega\.chainchronicle/',plan['base'])
dest.mkdir(exist_ok=False)
for name in ('plan.json','probe.json'):(dest/name).write_bytes((plan_dir/name).read_bytes())
(dest/'inventory.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in plan['files']),encoding='utf-8')
report={'status':'COPYING','probe':probe,'scope':'Refresh subset: new/metadata-changed plus all data5; combine with old snapshot only via provenance','base_snapshot':plan['old_snapshot'],'started_utc':datetime.now(timezone.utc).isoformat(),'method':'adb exec-out tar with explicit validated paths; no device writes'}
def save():(dest/'acquisition.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
save()
with (dest/'external_cache.tar').open('xb') as out,(dest/'stderr.txt').open('xb') as err:
 p=subprocess.run([adb,'-s',ready[0],'exec-out',f"tar -C {plan['base']} -cf - "+" ".join(shlex.quote(name) for name in names)],stdout=out,stderr=err,timeout=300)
report.update(status='STREAM_COPIED_NEEDS_VALIDATION' if p.returncode==0 else 'FAILED_PARTIAL_PRESERVED',exit_code=p.returncode,ended_utc=datetime.now(timezone.utc).isoformat(),archive_bytes=(dest/'external_cache.tar').stat().st_size);save();print(json.dumps(report,ensure_ascii=False));raise SystemExit(p.returncode)
