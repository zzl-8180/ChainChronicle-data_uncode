"""Consume the installed cleanup source map without modifying frozen readers."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from reference_sources_v2 import ReferenceSourceMap, _safe_file

ROOT=Path(__file__).resolve().parents[2]
MAP=ROOT/'operations/records/cleanup-retirement/20261113-v2/reference-source-map.json'
def digest(p):return hashlib.sha256(_safe_file(p).read_bytes()).hexdigest()
def route():
    raw=_safe_file(MAP).read_bytes();m=json.loads(raw)
    if m.get('status')!='INSTALLED' or m.get('effective') is not True or m.get('approved') is not True:
        raise ValueError('source map not activated')
    auth=ROOT/m['authorization']['path']
    if digest(auth)!=m['authorization']['sha256']:raise ValueError('authorization changed')
    a=json.loads(auth.read_bytes())
    if a.get('approved') is not True or a.get('execution_authorized') is not True or a['run_id']!=m['run_id']:
        raise ValueError('source map approval mismatch')
    if m['new_relative_root']!='projects/reader/data/reference_sources/cc_20261027':raise ValueError('unregistered source root')
    manifest=ROOT/m['allowlist']['manifest']
    if digest(manifest)!=m['allowlist']['sha256']:raise ValueError('allowlist changed')
    frozen=ROOT/m['frozen_document']['path']
    if digest(frozen)!=m['frozen_document']['sha256']:raise ValueError('frozen pairs changed')
    r=ReferenceSourceMap.from_manifest(manifest,ROOT/m['new_relative_root'])
    return m,r,manifest,hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--reference');g.add_argument('--output',type=Path)
    args=p.parse_args();m,r,manifest,map_sha=route()
    if args.reference:
        target,fragment=r.resolve_from_root(m['old_absolute_root'],args.reference)
        print(json.dumps(dict(path=str(target),fragment=fragment,sha256=digest(target),mapping_sha256=map_sha),ensure_ascii=False));return
    command=[sys.executable,'-E','-s','-B',
      '-X','pycache_prefix='+str(sys.pycache_prefix or ROOT/'work/20261114-cleanup-execution-r1/unused-pycache'),
      str(ROOT/'scripts/skill_reader_preview/assemble_reviewed_reader.py'),
      '--output',str(args.output.absolute()),'--base-reader',str(ROOT/'projects/reader/site/c21-incremental-20261112'),
      '--revision',str(ROOT/'output/character_skills/cycle_reports/C21_r01_20261112'),
      '--review',str(ROOT/'output/character_skills/review/direction_c21_20261112_thirdparty_r01_recheck'),
      '--reference-root',str(r.destination_root),'--source-map-manifest',str(manifest)]
    print(json.dumps(dict(event='INSTALLED_SOURCE_MAP_CONSUMED',mapping_sha256=map_sha,command=command),ensure_ascii=False),flush=True)
    result=subprocess.run(command,cwd=ROOT)
    if result.returncode:raise SystemExit(result.returncode)
    if digest(MAP)!=map_sha:raise ValueError('map changed during consumer')
    print(json.dumps(dict(event='INSTALLED_SOURCE_CONSUMER_EXIT_0',mapping_sha256=map_sha,formal_reader_overwritten=False)))
if __name__=='__main__':main()
