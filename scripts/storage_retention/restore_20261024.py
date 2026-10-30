"""Restore only previously verified, deleted historical payloads. Never delete/overwrite."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / 'output/storage_retention/recovery_audit_20261024'
OUT = ROOT / 'output/storage_retention/restore_20261024'
JOURNAL = ROOT / 'output/storage_retention/cleanup_20261023/after_rebuild/deleted_files.jsonl'
PAGE_PREFIX = 'output/character_skills/pages/_batch/'

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save_new(name, value):
    with (OUT/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)

def safe_path(relative, target=False):
    rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts or ':' in relative or '\\' in relative:
        raise ValueError(f'Invalid project-relative path: {relative}')
    full=ROOT/rel
    if not full.resolve().is_relative_to(ROOT):
        raise ValueError(f'Escaped project: {relative}')
    current=ROOT
    for part in rel.parts:
        current=current/part
        if current.exists() and current.lstat().st_file_attributes & 0x400:
            raise ValueError(f'Reparse point: {current}')
    if target:
        assert relative.startswith(PAGE_PREFIX), relative
        assert rel.name in ('card.json','index.html'), relative
        assert len(rel.parts)==11, relative
        assert rel.parts[5]=='runs' and rel.parts[7]=='transactions' and rel.parts[9]=='backup', relative
        assert rel.parts[8].isdigit(), relative
    return full

def protected():
    result={}
    batch=ROOT/'output/character_skills/pages/_batch'
    for p in batch.glob('*/latest.json'):
        result[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in [batch/'campaign_latest.json']:
        if p.is_file():
            result[p.relative_to(ROOT).as_posix()]=sha(p)
    return result

def prepare():
    OUT.mkdir(exist_ok=False)
    original=load(AUDIT/'recovery_plan.json')
    extra_targets=load(AUDIT/'additional_four_targets.json')
    extra_sources=load(AUDIT/'additional_four_recovery.json')['sources']
    rows=[dict(target=r['target'],size=r['size'],sha256=r['sha256'],sources=r['sources'],scope='original_11') for r in original if r['recoverable']]
    rows += [dict(target=r['path'],size=r['size'],sha256=r['sha256'],sources=extra_sources[r['sha256']],scope='additional_4') for r in extra_targets if r['sha256'] in extra_sources]
    rows.sort(key=lambda r:r['target'])
    assert len(rows)==7938 and len({r['target'] for r in rows})==7938
    wanted={r['target']:r for r in rows}
    logged=set()
    with JOURNAL.open(encoding='utf-8') as stream:
        for line in stream:
            deleted=json.loads(line)
            if deleted['path'] in wanted:
                row=wanted[deleted['path']]
                assert row['sha256']==deleted['sha256'] and row['size']==deleted['size']
                logged.add(deleted['path'])
    assert logged==wanted.keys()
    for row in rows:
        dest=safe_path(row['target'], target=True)
        if dest.exists() and (not dest.is_file() or dest.stat().st_size!=row['size'] or sha(dest)!=row['sha256']):
            raise FileExistsError(f'Existing target conflicts; no overwrite allowed: {dest}')
        valid=[]
        for source in row['sources']:
            assert source['kind']=='file', source
            assert source['verified_sha256']==row['sha256'] and source['size']==row['size']
            path=safe_path(source['path'])
            if path.is_file() and path.stat().st_size==row['size']:
                valid.append(source)
        if not valid:
            raise FileNotFoundError(f'No surviving source: {row["target"]}')
        row['sources']=valid
    required=sum(r['size'] for r in rows if not (ROOT/r['target']).exists())
    free=shutil.disk_usage(ROOT).free
    if free < required+512*1024*1024:
        raise OSError('Not enough disk space; nothing will be deleted to make room')
    inputs={p.relative_to(ROOT).as_posix():sha(p) for p in [AUDIT/'recovery_plan.json',AUDIT/'additional_four_targets.json',AUDIT/'additional_four_recovery.json',JOURNAL]}
    plan=dict(prepared_at=now(),authorization='Restore exact verified copies to original missing paths; no deletion or overwrite',rows=rows,files=len(rows),bytes=sum(r['size'] for r in rows),required_new_bytes=required,free_bytes=free,input_hashes=inputs,protected_pointers=protected())
    save_new('plan.json',plan)
    print(json.dumps(dict(files=len(rows),bytes=plan['bytes'],required_new_bytes=required,plan_sha256=sha(OUT/'plan.json'))),flush=True)

def restore(sample=False):
    plan=load(OUT/'plan.json')
    for relative,digest in plan['input_hashes'].items():
        if sha(ROOT/relative)!=digest:
            raise RuntimeError(f'Audit input changed: {relative}')
    rows=plan['rows']
    if sample:
        chosen={}
        for row in rows:
            parts=Path(row['target']).parts
            key=(row['scope'],parts[4],parts[-1])
            chosen.setdefault(key,row)
        rows=list(chosen.values())
    mode='sample' if sample else 'execute'
    journal=OUT/(mode+'_journal.jsonl')
    if journal.exists():
        raise FileExistsError('Execution already attempted; inspect its journal before retry')
    # Preflight all destinations before the first write.
    for row in rows:
        dest=safe_path(row['target'],target=True)
        if dest.exists() and (not dest.is_file() or sha(dest)!=row['sha256']):
            raise FileExistsError(f'Target conflict: {dest}')
    count=collections.Counter(); total=0; error=None
    before=protected()
    with journal.open('x',encoding='utf-8',buffering=1) as log:
        try:
            for index,row in enumerate(rows,1):
                dest=safe_path(row['target'],target=True)
                if dest.exists():
                    if sha(dest)!=row['sha256']:
                        raise FileExistsError(f'Existing destination changed: {dest}')
                    status='ALREADY_PRESENT_VERIFIED'; source_path=None
                else:
                    payload=None; source_path=None
                    for source in row['sources']:
                        src=safe_path(source['path'])
                        with src.open('rb') as stream:
                            data=stream.read()
                        if len(data)==row['size'] and hashlib.sha256(data).hexdigest()==row['sha256']:
                            payload=data; source_path=source['path'];break
                    if payload is None:
                        raise ValueError(f'No exact source bytes: {row["target"]}')
                    # Parent directories are expected to survive; create only missing backup ancestors.
                    if not dest.parent.is_dir():
                        dest.parent.mkdir(parents=True,exist_ok=True)
                    dest=safe_path(row['target'],target=True)
                    with dest.open('xb') as stream:
                        written=stream.write(payload)
                        stream.flush()
                        if written!=row['size']:
                            raise OSError(f'Incomplete write; preserved for inspection: {dest}')
                    if dest.stat().st_size!=row['size'] or sha(dest)!=row['sha256']:
                        raise ValueError(f'Restored file failed verification; preserved: {dest}')
                    status='RESTORED_VERIFIED';total+=row['size']
                    del payload,data
                entry=dict(time=now(),target=row['target'],sha256=row['sha256'],size=row['size'],source=source_path,status=status)
                log.write(json.dumps(entry,ensure_ascii=False)+'\n'); count[status]+=1
                if index%250==0:
                    os.fsync(log.fileno())
                    print(json.dumps(dict(mode=mode,processed=index,total=len(rows),counts=dict(count))),flush=True)
        except Exception as exc:
            error=repr(exc)
            log.write(json.dumps(dict(time=now(),status='ERROR_FILES_PRESERVED',error=error),ensure_ascii=False)+'\n')
        log.flush();os.fsync(log.fileno())
    result=dict(finished_at=now(),mode=mode,selected_files=len(rows),counts=dict(count),restored_bytes=total,error=error,pointers_unchanged=before==protected(),deleted_files=0,overwritten_files=0)
    save_new(mode+'_result.json',result)
    print(json.dumps(result),flush=True)
    if error:
        raise RuntimeError(error)

def verify():
    if (OUT/'verification.json').exists():
        raise FileExistsError('Verification already recorded')
    plan=load(OUT/'plan.json'); failures=[]
    for index,row in enumerate(plan['rows'],1):
        p=safe_path(row['target'],target=True)
        if not p.is_file() or p.stat().st_size!=row['size'] or sha(p)!=row['sha256']:
            failures.append(row['target'])
        if index%1000==0:
            print(json.dumps(dict(phase='independent_verify',checked=index,total=len(plan['rows']))),flush=True)
    # Measure remaining original deletion targets; never fill them with later versions.
    all_rows=load(AUDIT/'targets.json')+load(AUDIT/'additional_four_targets.json')
    remaining=[]; unexpected=[]
    restored={r['target'] for r in plan['rows']}
    for row in all_rows:
        path=safe_path(row['path'],target=True)
        if row['path'] not in restored:
            if path.exists():
                unexpected.append(dict(path=row['path'],sha256=sha(path)))
            else:
                remaining.append(row)
    save_new('remaining_targets.json',remaining)
    result=dict(verified_at=now(),status='PASS' if not failures else 'FAIL',verified_files=len(plan['rows'])-len(failures),verified_bytes=sum(r['size'] for r in plan['rows']) if not failures else None,failures=failures,remaining_missing_files=len(remaining),remaining_missing_bytes=sum(r['size'] for r in remaining),unexpected_existing=unexpected,pointers_unchanged_since_prepare=plan['protected_pointers']==protected(),deleted_files=0,overwritten_files=0)
    save_new('verification.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true');mode.add_argument('--sample',action='store_true');mode.add_argument('--execute',action='store_true');mode.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.sample:restore(sample=True)
    elif args.execute:restore()
    else:verify()
