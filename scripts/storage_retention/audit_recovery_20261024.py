"""Read-only recovery-source audit. Writes only a new dedicated report folder."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import os
import struct
import sys
import subprocess
import zipfile
import tarfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/storage_retention/recovery_audit_20261024'

def save(name, obj):
    with (OUT / name).open('w', encoding='utf-8') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)

def digest_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def main():
    OUT.mkdir(exist_ok=True)
    if any(p.name not in ('targets.json','recycle_bin.json') for p in OUT.iterdir()):
        raise FileExistsError('Completed scan results are never overwritten')
    prior = json.loads((ROOT/'output/storage_retention/referenced_runs_20261024/prior_cleanup_replay_limitations.json').read_text(encoding='utf-8'))
    runs = sorted({r['run_path'] for r in prior['findings']})
    targets = []
    log = ROOT/'output/storage_retention/cleanup_20261023/after_rebuild/deleted_files.jsonl'
    for line in log.open(encoding='utf-8'):
        row = json.loads(line)
        if row['group'] in runs:
            row['exists_now'] = (ROOT/row['path']).exists()
            targets.append(row)
    assert len(runs) == 11 and all(r['sha256'] for r in targets)
    save('targets.json', targets)
    wanted = {r['sha256'] for r in targets}
    sizes = {r['size'] for r in targets}
    matches = collections.defaultdict(list)
    errors = []
    # Parse only recycle metadata; retain details only for this workspace.
    recycle = {'volume': 'E:', 'metadata_entries': 0, 'project_entries': [], 'errors': []}
    try:
        for sid in Path('E:/$Recycle.Bin').iterdir():
            if not sid.is_dir():
                continue
            try:
                for ip in sid.glob('$I*'):
                    if not ip.is_file():
                        continue
                    recycle['metadata_entries'] += 1
                    b = ip.read_bytes()
                    version, size, stamp = struct.unpack('<QQQ', b[:24])
                    original = b[28 if version == 2 else 24:].decode('utf-16-le', errors='replace').rstrip('\x00')
                    op = original.replace('\\', '/').lower().rstrip('/')
                    rp = str(ROOT).replace('\\', '/').lower()
                    if op.startswith(rp+'/') or op == rp or rp.startswith(op+'/'):
                        recycle['project_entries'].append(dict(metadata=str(ip), original=original, size=size, payload=str(ip.with_name('$R'+ip.name[2:])), payload_exists=ip.with_name('$R'+ip.name[2:]).exists()))
            except OSError as e:
                recycle['errors'].append(str(e))
    except OSError as e:
        recycle['errors'].append(str(e))
    save('recycle_bin.json', recycle)
    print(json.dumps({'phase':'targets', 'runs':len(runs),'files':len(targets),'bytes':sum(r['size'] for r in targets),'recycle_project_entries':len(recycle['project_entries'])}), flush=True)
    # Filename inventory, not full reads of original media/data or dependencies.
    excluded = ['.git','.venv','tools','raw','output/full_unpack','output/storage_retention','.codex','.agents']
    # rg invocation failed in the low-memory host; bounded native traversal fallback.
    def walk_files():
        for base, dirs, names in os.walk(ROOT, followlinks=False):
            relbase = Path(base).relative_to(ROOT)
            dirs[:] = [d for d in dirs if (relbase/d).as_posix() not in excluded
                       and not os.lstat(Path(base)/d).st_file_attributes & 0x400]
            for name in names:
                if name in ('receipt.json','card.json','index.html') or Path(name).suffix.lower() in ('.zip','.7z','.tar','.gz','.rar'):
                    yield relbase/name
    archives = []
    counts = collections.Counter()
    checked = set()
    for rel in walk_files():
        counts[rel.name if rel.name in ('receipt.json','card.json','index.html') else 'archive'] += 1
        if rel.suffix.lower() in ('.zip','.7z','.tar','.gz','.rar'):
            archives.append(rel)
        if rel.name != 'receipt.json':
            continue
        try:
            r = json.loads((ROOT/rel).read_text(encoding='utf-8-sig'))
            for name, sha in r.get('files',{}).items():
                if name not in ('card.json','index.html') or not isinstance(sha,str):
                    continue
                candidate = rel.parent/name
                if sha not in wanted or len(matches.get(sha,[])) >= 2 or candidate.as_posix() in checked or not (ROOT/candidate).is_file():
                    continue
                checked.add(candidate.as_posix())
                actual = digest_file(ROOT/candidate)
                if actual == sha:
                    matches[sha].append(dict(kind='file',path=candidate.as_posix(),size=(ROOT/candidate).stat().st_size,verified_sha256=actual))
                else:
                    errors.append(dict(path=candidate.as_posix(),error='receipt_hash_mismatch',declared=sha,actual=actual))
        except (OSError,ValueError,AttributeError) as e:
            errors.append(dict(path=rel.as_posix(),error=str(e)))
        if counts['receipt.json'] % 25000 == 0:
            print(json.dumps(dict(phase='receipts',processed=counts['receipt.json'],matched_unique=len(matches))),flush=True)
    save('search_scope.json', dict(excluded=excluded,counts=dict(counts),archives=[p.as_posix() for p in archives],scope_note='All project files except unrelated raw/unpacked media/dependencies and own audit reports; no arbitrary other user directories.'))
    save('receipt_matches.json', matches)
    print(json.dumps(dict(phase='receipt_complete',matched_unique=len(matches),targets_unique=len(wanted))),flush=True)
    # Check remaining standalone files by size/hash, including those without receipts.
    fallback = 0
    by_size = collections.defaultdict(set)
    for row in targets:
        by_size[row['size']].add(row['sha256'])
    for rel in walk_files():
        if rel.name not in ('card.json','index.html'):
            continue
        key = rel.as_posix()
        if key in checked:
            continue
        try:
            size = (ROOT/rel).stat().st_size
            if size not in sizes:
                continue
            # All relevant hashes already found need no extra equivalent copies.
            remaining = by_size[size] - matches.keys()
            if not remaining:
                continue
            actual = digest_file(ROOT/rel)
            fallback += 1
            if actual in wanted:
                matches[actual].append(dict(kind='file',path=key,size=size,verified_sha256=actual))
        except OSError as e:
            errors.append(dict(path=key,error=str(e)))
    save('loose_file_matches.json', matches)
    print(json.dumps(dict(phase='loose_complete',matched_unique=len(matches),fallback_hashed=fallback)),flush=True)
    archive_stats = []
    for rel in archives:
        if rel.suffix.lower() != '.zip':
            archive_stats.append(dict(path=rel.as_posix(),status='unsupported_not_scanned'))
            continue
        total = candidate_count = match_count = 0
        try:
            with zipfile.ZipFile(ROOT/rel) as z:
                for info in z.infolist():
                    total += 1
                    if info.is_dir() or info.file_size not in sizes:
                        continue
                    if Path(info.filename).name not in ('card.json','index.html'):
                        continue
                    remaining = by_size[info.file_size] - matches.keys()
                    if not remaining:
                        continue
                    candidate_count += 1
                    b = z.read(info)
                    actual = hashlib.sha256(b).hexdigest()
                    if actual in wanted:
                        match_count += 1
                        matches[actual].append(dict(kind='zip_member',path=rel.as_posix(),member=info.filename,size=len(b),verified_sha256=actual))
            archive_stats.append(dict(path=rel.as_posix(),status='checked',entries=total,hashed_candidates=candidate_count,matches=match_count))
        except (OSError,ValueError,zipfile.BadZipFile) as e:
            archive_stats.append(dict(path=rel.as_posix(),status='error',error=str(e)))
        print(json.dumps(dict(phase='archive',path=rel.as_posix(),matched_unique=len(matches))),flush=True)
    save('archive_scan.json',archive_stats)
    save('verified_sources.json',matches)
    save('errors.json',errors)
    results=[]
    for run in runs:
        rows=[r for r in targets if r['group']==run]
        counts={name:dict(total=sum(Path(r['path']).name==name for r in rows),recoverable=sum(Path(r['path']).name==name and r['sha256'] in matches for r in rows)) for name in ('card.json','index.html')}
        results.append(dict(run_path=run,counts=counts,total_bytes=sum(r['size'] for r in rows),recoverable_bytes=sum(r['size'] for r in rows if r['sha256'] in matches)))
    save('summary.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),runs=results,target_files=len(targets),target_unique_hashes=len(wanted),matched_unique_hashes=len(matches),recoverable_files=sum(r['sha256'] in matches for r in targets),unmatched_files=sum(r['sha256'] not in matches for r in targets),fallback_hashed=fallback,errors=len(errors),restored_files=0,deletions=0))
    print(json.dumps(results),flush=True)

def wide_scan():
    """Additional renamed JSON/HTML and archive member search; no restoration."""
    if (OUT/'wide_summary.json').exists():
        raise FileExistsError('Wide scan already recorded')
    targets = json.loads((OUT/'targets.json').read_text(encoding='utf-8'))
    matches = json.loads((OUT/'verified_sources.json').read_text(encoding='utf-8'))
    scope = json.loads((OUT/'search_scope.json').read_text(encoding='utf-8'))
    missing_by_size = collections.defaultdict(set)
    for r in targets:
        if r['sha256'] not in matches:
            missing_by_size[r['size']].add(r['sha256'])
    before = len(matches)
    hashed = 0
    errors = []
    command=['rg','--files','--hidden','--no-ignore','--threads','2']
    for pattern in ('*.json','*.html','*.htm','*.bak','*.old','!card.json','!index.html'):
        command += ['-g',pattern]
    for exclude in scope['excluded']:
        command += ['-g','!'+exclude+'/**']
    # Stream filename inventory to disk to avoid the earlier capture_output memory spike.
    with (OUT/'renamed_candidates.txt').open('wb') as stream:
        result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError('rg wide inventory failed: '+result.stderr.decode('utf-8',errors='replace'))
    for line in (OUT/'renamed_candidates.txt').open(encoding='utf-8'):
        p=ROOT/line.rstrip('\r\n')
        try:
            if p.lstat().st_file_attributes & 0x400:
                continue
            size=p.stat().st_size
            remaining=missing_by_size.get(size,set()) - matches.keys()
            if not remaining:
                continue
            actual=digest_file(p); hashed+=1
            if actual in remaining:
                matches[actual]=[dict(kind='file',path=p.relative_to(ROOT).as_posix(),size=size,verified_sha256=actual)]
        except OSError as e:
            errors.append(dict(path=str(p),error=str(e)))
    for rel in scope['archives']:
        if rel.lower().endswith(('.tar','.tar.gz','.tgz')):
            try:
                with tarfile.open(ROOT/rel, 'r:*') as tar:
                    for info in tar:
                        if not info.isfile():
                            continue
                        remaining=missing_by_size.get(info.size,set()) - matches.keys()
                        if not remaining:
                            continue
                        stream=tar.extractfile(info)
                        h=hashlib.sha256()
                        for block in iter(lambda:stream.read(1024*1024),b''):
                            h.update(block)
                        actual=h.hexdigest(); hashed+=1
                        if actual in remaining:
                            matches[actual]=[dict(kind='tar_member',path=rel,member=info.name,size=info.size,verified_sha256=actual)]
            except (OSError,tarfile.TarError) as e:
                errors.append(dict(path=rel,error=str(e)))
            continue
        if not rel.lower().endswith('.zip'):
            continue
        try:
            with zipfile.ZipFile(ROOT/rel) as z:
                for info in z.infolist():
                    if info.is_dir() or Path(info.filename).name in ('card.json','index.html'):
                        continue
                    remaining=missing_by_size.get(info.file_size,set()) - matches.keys()
                    if not remaining:
                        continue
                    data=z.read(info); actual=hashlib.sha256(data).hexdigest(); hashed+=1
                    if actual in remaining:
                        matches[actual]=[dict(kind='zip_member',path=rel,member=info.filename,size=len(data),verified_sha256=actual)]
        except (OSError,zipfile.BadZipFile) as e:
            errors.append(dict(path=rel,error=str(e)))
    save('verified_sources_final.json', matches)
    save('wide_summary.json',dict(new_matching_hashes=len(matches)-before,hashed_candidates=hashed,errors=errors,restored_files=0,deletions=0))
    print(json.dumps(dict(new_matching_hashes=len(matches)-before,hashed_candidates=hashed,errors=len(errors))),flush=True)

def report():
    if (OUT/'recovery_plan.json').exists():
        raise FileExistsError('Final report already recorded')
    targets=json.loads((OUT/'targets.json').read_text(encoding='utf-8'))
    matches=json.loads((OUT/'verified_sources_final.json').read_text(encoding='utf-8'))
    previous=json.loads((ROOT/'output/storage_retention/referenced_runs_20261024/decisions.json').read_text(encoding='utf-8'))
    categories={r['path']:r['category'] for r in previous}
    plan=[]; grouped=collections.defaultdict(list); holds={}; receipt_issues=[]
    for t in targets:
        sources=matches.get(t['sha256'],[])
        row=dict(target=t['path'],run=t['group'],size=t['size'],sha256=t['sha256'],recoverable=bool(sources),sources=sources)
        plan.append(row); grouped[t['group']].append(row)
        if Path(t['path']).name=='card.json':
            receipt=ROOT/Path(t['path']).parent/'receipt.json'
            try:
                d=json.loads(receipt.read_text(encoding='utf-8'))
                if d.get('files',{}).get('card.json')!=t['sha256']:
                    receipt_issues.append(dict(path=t['path'],error='receipt/log mismatch'))
            except (OSError,ValueError) as e:
                receipt_issues.append(dict(path=t['path'],error=str(e)))
        for source in sources:
            key=source['path']
            if '/transactions/' in key:
                key=key.split('/transactions/')[0]
            if key not in holds:
                holds[key]=dict(path=key,previous_149_category=categories.get(key,'outside_original_149'),reason='Verified exact recovery source; protect until recovery and validation are complete',source_files=set(),target_files=set())
            holds[key]['source_files'].add(source['path'])
            holds[key]['target_files'].add(t['path'])
    save('recovery_plan.json',plan)
    csvrows=[dict(target=r['target'],size=r['size'],sha256=r['sha256'],recoverable=r['recoverable'],source_kind=r['sources'][0]['kind'] if r['sources'] else '',source_path=r['sources'][0]['path'] if r['sources'] else '',source_member=r['sources'][0].get('member','') if r['sources'] else '') for r in plan]
    with (OUT/'recovery_plan.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
    save('unresolved_files.json',[r for r in plan if not r['recoverable']])
    summary=[]
    for run, rows in sorted(grouped.items()):
        counts={name:dict(total=sum(Path(r['target']).name==name for r in rows),recoverable=sum(Path(r['target']).name==name and r['recoverable'] for r in rows)) for name in ('card.json','index.html')}
        summary.append(dict(run_path=run,counts=counts,total_bytes=sum(r['size'] for r in rows),recoverable_bytes=sum(r['size'] for r in rows if r['recoverable']),unresolved_bytes=sum(r['size'] for r in rows if not r['recoverable']),full_payload_recoverable=all(r['recoverable'] for r in rows)))
    for r in holds.values():
        r['source_files']=sorted(r['source_files']);r['target_files']=sorted(r['target_files'])
    save('recovery_source_holds.json',list(holds.values()))
    totals=dict(runs=summary,target_files=len(plan),recoverable_files=sum(r['recoverable'] for r in plan),unresolved_files=sum(not r['recoverable'] for r in plan),total_bytes=sum(r['size'] for r in plan),recoverable_bytes=sum(r['size'] for r in plan if r['recoverable']),unresolved_bytes=sum(r['size'] for r in plan if not r['recoverable']),fully_recoverable_runs=sum(r['full_payload_recoverable'] for r in summary),receipt_issues=receipt_issues,restored_files=0,deletions=0,cleanup_paused=True)
    save('final_summary.json',totals)
    lines=['# 11 个 run 恢复来源核验结果','','分子是已找到且 SHA-256 与删除日志一致的文件数；分母是该 run 被删文件数。这里只列恢复来源，没有恢复或删除文件。','','| cohort / run | JSON 可恢复 | HTML 可恢复 | 可恢复 GiB | 尚无精确来源 GiB |','|---|---:|---:|---:|---:|']
    for r in summary:
        p=Path(r['run_path']); c=r['counts']; lines.append(f"| {p.parts[-3]} / {p.name} | {c['card.json']['recoverable']}/{c['card.json']['total']} | {c['index.html']['recoverable']}/{c['index.html']['total']} | {r['recoverable_bytes']/2**30:.4f} | {r['unresolved_bytes']/2**30:.4f} |")
    lines+=['','逐文件来源与原哈希：[recovery_plan.csv](recovery_plan.csv)、[recovery_plan.json](recovery_plan.json)。未找到来源：[unresolved_files.json](unresolved_files.json)。供体保护清单：[recovery_source_holds.json](recovery_source_holds.json)。']
    (OUT/'RUNS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in totals.items() if k!='runs'}),flush=True)

if __name__ == '__main__':
    if '--wide' in sys.argv:
        wide_scan()
    elif '--report' in sys.argv:
        report()
    else:
        main()
