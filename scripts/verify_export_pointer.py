"""Five bounded pointer regressions; outputs only to a new explicit test directory.

Run from the project root. Does not edit production latest, inputs or old builds.
The corrupted payload is a separate test copy retained for diagnosis.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-root',type=Path,required=True,help='New independent test directory; must not already exist')
    parser.add_argument('--other-build',type=Path,required=True,help='Existing different build; used only as pointer value')
    args=parser.parse_args()
    project=Path.cwd().resolve()
    target=args.output_root.resolve()
    if target.exists() or target==project or target in project.parents:
        raise ValueError('Test output must be a new independent subdirectory, never the project or an ancestor')
    official=(project/'output/export').resolve()
    if target==official or target.is_relative_to(official) or official.is_relative_to(target):
        raise ValueError('Pointer tests must not write within or above formal exports')
    other=args.other_build.resolve()
    other_manifest=load(other/'manifest.json')
    foreign={'snapshot_id':other_manifest['snapshot_id'],'build_id':other_manifest['build_id'],'directory':other.as_posix()}
    official_pointer=(official/'latest.json').read_bytes()
    target.mkdir(parents=True)
    export_root=target/'export'
    pointer=export_root/'latest.json'
    cases=[]

    def run(root,label,success=True):
        result=subprocess.run([sys.executable,'-B','scripts/export_master.py','--output-root',str(root)],cwd=project,capture_output=True,text=True,encoding='utf-8')
        (target/(label+'.stdout.txt')).write_text(result.stdout,encoding='utf-8')
        (target/(label+'.stderr.txt')).write_text(result.stderr,encoding='utf-8')
        assert (result.returncode==0)==success,(label,result.returncode,result.stderr)
        return json.loads(result.stdout.strip()) if success else result

    result=run(export_root,'01_first_export')
    assert result['status'] in ('EXPORTED','EXPORTED_WITH_PRESERVED_ANOMALIES')
    selected=load(pointer)
    directory=Path(selected['directory']).resolve()
    assert directory.is_relative_to(export_root.resolve())
    manifest=load(directory/'manifest.json')
    assert selected['snapshot_id']==manifest['snapshot_id'] and selected['build_id']==manifest['build_id']
    assert selected['build_id']!=foreign['build_id'],'other-build must be a different build'
    expected_files={p.relative_to(directory).as_posix():digest(p) for p in directory.rglob('*') if p.is_file()}
    cases.append({'case':'first_export_creates_selected_pointer','status':'PASS'})

    result=run(export_root,'02_reuse')
    assert result['status']=='EXISTING_SNAPSHOT_VERIFIED' and load(pointer)==selected
    cases.append({'case':'same_build_reused_after_validation','status':'PASS'})

    pointer.unlink()  # this independent test pointer only
    assert not pointer.exists()
    result=run(export_root,'03_missing_pointer')
    assert result['status']=='EXISTING_SNAPSHOT_VERIFIED' and load(pointer)==selected
    cases.append({'case':'missing_pointer_restored','status':'PASS'})

    save(pointer,foreign)
    result=run(export_root,'04_other_pointer')
    assert result['status']=='EXISTING_SNAPSHOT_VERIFIED' and load(pointer)==selected
    assert expected_files=={p.relative_to(directory).as_posix():digest(p) for p in directory.rglob('*') if p.is_file()}
    cases.append({'case':'other_build_pointer_reselected_without_payload_changes','status':'PASS'})

    corrupt_root=target/'corrupt_export'
    corrupt_build=corrupt_root/selected['snapshot_id']/selected['build_id']
    assert corrupt_build.resolve().is_relative_to(target) and not corrupt_build.exists()
    shutil.copytree(directory,corrupt_build)
    corrupted=corrupt_build/'anomalies.jsonl'
    corrupted.write_bytes(corrupted.read_bytes()+b'INJECTED_CHECKSUM_FAILURE\n')
    corrupt_pointer=corrupt_root/'latest.json'
    save(corrupt_pointer,foreign)
    before=corrupt_pointer.read_bytes()
    corrupt_hashes={p.relative_to(corrupt_build).as_posix():digest(p) for p in corrupt_build.rglob('*') if p.is_file()}
    failure=run(corrupt_root,'05_checksum_failure',success=False)
    assert 'Existing immutable export differs: anomalies.jsonl' in failure.stderr
    assert corrupt_pointer.read_bytes()==before
    assert corrupt_hashes=={p.relative_to(corrupt_build).as_posix():digest(p) for p in corrupt_build.rglob('*') if p.is_file()}
    cases.append({'case':'checksum_failure_keeps_pointer_and_test_payload_unchanged','status':'PASS'})
    assert (official/'latest.json').read_bytes()==official_pointer
    report={'status':'PASS','case_count':len(cases),'cases':cases,'project_root':str(project),
            'test_output_root':str(target),'selected_build':str(directory),'other_build_read_only':str(other),
            'formal_pointer_unchanged_during_tests':True,'valid_test_payload_unchanged':True,
            'corrupted_copy_retained':str(corrupt_build),'test_script_sha256':digest(Path(__file__)),
            'exporter_sha256':digest(project/'scripts/export_master.py')}
    save(target/'pointer_checks.json',report)
    print(json.dumps({'status':'PASS','cases':len(cases),'report':str(target/'pointer_checks.json'),'build':str(directory)},ensure_ascii=False))


if __name__=='__main__':
    main()
