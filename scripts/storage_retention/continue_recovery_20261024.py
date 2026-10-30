"""Read-only evidence search and exact-byte materialization; no deletion/overwrite."""
from pathlib import Path
import argparse, collections, hashlib, html, json, os, re, subprocess, zipfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/storage_retention/recovery_followup_20261024'
INPUT=ROOT/'output/storage_retention/restore_20261024/remaining_targets.json'

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(name,obj):
    OUT.mkdir(exist_ok=True)
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def targets():
    rows=load(INPUT)
    return rows,{r['sha256']:r for r in rows}

def materialize(data,row,source):
    assert len(data)==row['size'] and hashlib.sha256(data).hexdigest()==row['sha256']
    p=OUT/'materialized'/row['sha256']/Path(row['path']).name
    p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():
        with p.open('xb') as f:f.write(data)
    assert sha(p)==row['sha256']
    return dict(path=p.relative_to(ROOT).as_posix(),size=len(data),sha256=row['sha256'],source=source)

def packages():
    rows,wanted=targets();by_size=collections.defaultdict(set)
    for row in rows:by_size[row['size']].add(row['sha256'])
    results=[];found={}
    for name in ('cc_skill_values_20261021','cc_skill_values_20261022'):
        p=ROOT/'output/share_bundle'/f'{name}.zip'
        checked=0;total=0;declared_matches=[];manifest_size_errors=[]
        with zipfile.ZipFile(p) as z:
            manifest=load(ROOT/'output/share_bundle'/name/'manifest.json')
            archived=json.loads(z.read(f'{name}/manifest.json'))
            assert manifest==archived
            infos={i.filename:i for i in z.infolist()}
            for entry in archived['files']:
                if entry['sha256'] in wanted:declared_matches.append(entry)
                member=f'{name}/'+entry['path']
                if member not in infos or infos[member].file_size!=entry['bytes']:
                    manifest_size_errors.append(member)
            for info in infos.values():
                if info.is_dir():continue
                if Path(info.filename).name in ('card.json','index.html'):total+=1
                if info.file_size not in by_size:continue
                data=z.read(info);checked+=1;digest=hashlib.sha256(data).hexdigest()
                if digest in wanted:
                    found[digest]=materialize(data,wanted[digest],dict(kind='zip_member',archive=p.relative_to(ROOT).as_posix(),member=info.filename))
            results.append(dict(bundle=name,archive=p.relative_to(ROOT).as_posix(),created_at=archived.get('created_at'),campaign=archived.get('campaign'),entries=len(infos),card_html_files=total,manifest_entries=len(archived['files']),manifest_matches=declared_matches,manifest_size_errors=manifest_size_errors,actual_size_candidates_hashed=checked))
        print(json.dumps(dict(bundle=name,hashed=checked,found=len(found))),flush=True)
    save('share_packages.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),remaining_targets=len(rows),identification_evidence='docs/tasks/20261023-reference-check-lead.md:16',packages=results,exact_sources=found,deleted_files=0))

def iter_objects(path):
    """Stream an object-of-card-objects without loading the 487 MB document."""
    decoder=json.JSONDecoder()
    with path.open(encoding='utf-8') as f:
        buffer='';pos=0;eof=False
        def more():
            nonlocal buffer,pos,eof
            buffer=buffer[pos:];pos=0;chunk=f.read(262144)
            buffer+=chunk;eof=not chunk
        def ws():
            nonlocal pos
            while True:
                while pos<len(buffer) and buffer[pos].isspace():pos+=1
                if pos<len(buffer) or eof:return
                more()
        more();ws();assert buffer[pos]=='{';pos+=1
        while True:
            ws()
            if buffer[pos]=='}':return
            if buffer[pos]==',':pos+=1;ws()
            while True:
                try:key,end=decoder.raw_decode(buffer,pos);break
                except json.JSONDecodeError:
                    if eof:raise
                    more()
            pos=end;ws();assert buffer[pos]==':';pos+=1;ws()
            while True:
                try:value,end=decoder.raw_decode(buffer,pos);break
                except json.JSONDecodeError:
                    if eof:raise
                    more()
            pos=end
            yield key,value

def snapshot():
    rows,wanted=targets();json_targets=[r for r in rows if r['path'].endswith('/card.json')]
    by_cid=collections.defaultdict(list)
    for row in json_targets:by_cid[row['path'].split('/transactions/')[1].split('/')[0]].append(row)
    p=ROOT/'work/character_skills_b10_fix2/pages_before.json'
    found={};count=0;relevant=0
    for cid,card in iter_objects(p):
        count+=1
        if str(cid) not in by_cid:continue
        relevant+=1
        # Exact historical dump implementation: ensure_ascii=False, indent=2, newline.
        # Try both line-ending variants; only an original SHA-256 match is accepted.
        text=json.dumps(card,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        for label,data in [('original_dump_lf',text.encode('utf-8')),('original_dump_crlf',text.replace('\n','\r\n').encode('utf-8'))]:
            digest=hashlib.sha256(data).hexdigest()
            if digest in wanted:
                found[digest]=materialize(data,wanted[digest],dict(kind='complete_card_in_snapshot',path=p.relative_to(ROOT).as_posix(),cid=str(cid),serialization=label))
        if count%500==0:print(json.dumps(dict(phase='snapshot',cards=count,relevant=relevant,found=len(found))),flush=True)
    save('full_snapshot.json',dict(path=p.relative_to(ROOT).as_posix(),source_sha256=sha(p),cards=count,relevant_cards=relevant,exact_sources=found,scope='Complete card objects serialized by historical dump; no field editing or guessed values',deleted_files=0))
    print(json.dumps(dict(phase='snapshot_complete',cards=count,found=len(found))),flush=True)

def receipt_sweep():
    rows,wanted=targets();extra=load(ROOT/'output/storage_retention/recovery_audit_20261024/additional_four_unresolved.json')['files']
    selected={r['sha256']:r for r in extra}; OUT.mkdir(exist_ok=True)
    patterns=OUT/'critical_hashes.txt'
    with patterns.open('x',encoding='ascii') as f:f.write('\n'.join(selected)+'\n')
    command=['rg','-l','-F','--hidden','--no-ignore','--threads','2','-f',str(patterns),'-g','receipt.json']
    for exclude in ('.git','.venv','tools','raw','output/full_unpack','output/storage_retention','.codex','.agents'):
        command+=['-g','!'+exclude+'/**']
    command+=['.']
    with (OUT/'critical_receipts.txt').open('xb') as output:
        result=subprocess.run(command,cwd=ROOT,stdout=output,stderr=subprocess.PIPE)
    if result.returncode not in (0,1):raise RuntimeError(result.stderr.decode('utf-8',errors='replace'))
    found={};count=0
    for line in (OUT/'critical_receipts.txt').open(encoding='utf-8'):
        receipt=ROOT/line.strip();count+=1;data=load(receipt)
        for name,digest in data.get('files',{}).items():
            p=receipt.parent/name
            if digest not in selected or not p.is_file():continue
            payload=p.read_bytes()
            if hashlib.sha256(payload).hexdigest()==digest:
                found[digest]=dict(path=p.relative_to(ROOT).as_posix(),size=len(payload),sha256=digest,source=dict(kind='existing_file',receipt=receipt.relative_to(ROOT).as_posix()))
    save('critical_receipt_search.json',dict(scope='Project-wide exact hash search across receipt.json, excluding original media and dependencies',receipts_matched=count,target_files=len(extra),exact_sources=found,deleted_files=0))
    print(json.dumps(dict(phase='critical_receipts',receipts=count,found=len(found))),flush=True)

def ordered_snapshot():
    """Restore dict insertion order lost by the full snapshot's sort_keys=True.

    Values come only from the full historical snapshot. Nearby complete files
    supply dictionary ordering, never values. Original SHA-256 is the acceptance gate.
    """
    rows,wanted=targets()
    critical=load(ROOT/'output/storage_retention/recovery_audit_20261024/additional_four_unresolved.json')['files']
    by_cid={r['path'].split('/transactions/')[1].split('/')[0]:r for r in critical if r['path'].endswith('/card.json')}
    candidates=load(ROOT/'output/storage_retention/recovery_audit_20261024/additional_four_recovery.json')['candidate_runs']
    def reorder(value,template):
        if isinstance(value,dict):
            if not isinstance(template,dict) or value.keys()!=template.keys():raise ValueError('different key set')
            return {key:reorder(value[key],template[key]) for key in template}
        if isinstance(value,list):
            if not isinstance(template,list) or len(value)!=len(template):raise ValueError('different list shape')
            return [reorder(a,b) for a,b in zip(value,template)]
        return value
    found={};attempts=[]
    path=ROOT/'work/character_skills_b10_fix2/pages_before.json'
    for cid,card in iter_objects(path):
        if cid not in by_cid:continue
        row=by_cid[cid]
        for candidate in candidates:
            p=ROOT/candidate/'transactions'/cid/'backup/card.json'
            if not p.is_file():continue
            try:
                rebuilt=reorder(card,load(p))
            except ValueError:
                continue
            text=json.dumps(rebuilt,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
            for label,data in [('historical_dump_lf',text.encode('utf-8')),('historical_dump_crlf',text.replace('\n','\r\n').encode('utf-8'))]:
                digest=hashlib.sha256(data).hexdigest()
                attempts.append(dict(cid=cid,ordering_template=p.relative_to(ROOT).as_posix(),serialization=label,size=len(data),sha256=digest,exact=digest==row['sha256']))
                if digest==row['sha256']:
                    found[digest]=materialize(data,row,dict(kind='complete_snapshot_restored_key_order',snapshot=path.relative_to(ROOT).as_posix(),cid=cid,ordering_template=p.relative_to(ROOT).as_posix(),serialization=label))
            if row['sha256'] in found:break
    save('ordered_snapshot.json',dict(source_sha256=sha(path),scope='Critical 21 full JSON objects, values unchanged, key order supplied by nearby complete files',exact_sources=found,attempts=attempts,deleted_files=0))
    print(json.dumps(dict(phase='ordered_snapshot',found=len(found),attempts=len(attempts))),flush=True)

def reconstruct_html():
    rows,wanted=targets()
    critical=load(ROOT/'output/storage_retention/recovery_audit_20261024/additional_four_unresolved.json')['files']
    html_rows={r['path'].split('/transactions/')[1].split('/')[0]:r for r in critical if r['path'].endswith('/index.html')}
    cards=load(OUT/'ordered_snapshot.json')['exact_sources'];found={};attempts=[]
    def differences(old,new,path=()):
        if isinstance(old,dict):
            assert old.keys()==new.keys()
            return [d for k in old for d in differences(old[k],new[k],path+(k,))]
        if isinstance(old,list):
            assert len(old)==len(new)
            return [d for i,(a,b) in enumerate(zip(old,new)) for d in differences(a,b,path+(i,))]
        return [] if old==new else [dict(path=list(path),old=old,new=new)]
    for item in cards.values():
        provenance=item['source'];cid=provenance['cid'];row=html_rows[cid]
        old=load(ROOT/item['path']);new_path=ROOT/provenance['ordering_template'];new=load(new_path)
        diffs=differences(old,new);mapping={};ambiguous=False
        for diff in diffs:
            if not isinstance(diff['old'],str) or not isinstance(diff['new'],str):ambiguous=True;break
            a=diff['old'];b=diff['new']
            pairs=[(b,a),(html.escape(b,quote=True),html.escape(a,quote=True)),
                   (json.dumps(b,ensure_ascii=False)[1:-1],json.dumps(a,ensure_ascii=False)[1:-1])]
            pairs += [(b.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026'),a.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026'))]
            for x,y in pairs:
                if x in mapping and mapping[x]!=y:ambiguous=True
                mapping[x]=y
        source=new_path.with_name('index.html')
        if ambiguous or not mapping or not source.is_file():
            attempts.append(dict(cid=cid,status='skipped_ambiguous_or_missing_template'));continue
        template=source.read_bytes();text=template.decode('utf-8')
        pattern=re.compile('|'.join(re.escape(s) for s in sorted(mapping,key=len,reverse=True)))
        rebuilt=pattern.sub(lambda m:mapping[m.group()],text).encode('utf-8')
        digest=hashlib.sha256(rebuilt).hexdigest()
        attempts.append(dict(cid=cid,changes=diffs,size=len(rebuilt),sha256=digest,exact=digest==row['sha256']))
        if digest==row['sha256']:
            found[digest]=materialize(rebuilt,row,dict(kind='historical_html_exact_reverse',old_card=item['path'],template=source.relative_to(ROOT).as_posix(),template_sha256=hashlib.sha256(template).hexdigest(),changes=diffs))
    save('reconstructed_html.json',dict(scope='Restore old strings from verified historical card; original HTML SHA-256 must match',exact_sources=found,attempts=attempts,deleted_files=0))
    print(json.dumps(dict(phase='reconstructed_html',found=len(found),attempts=len(attempts))),flush=True)

def restore_found():
    from restore_20261024 import safe_path, protected
    rows,wanted=targets();found={}
    for name in ('share_packages.json','full_snapshot.json','ordered_snapshot.json','reconstructed_html.json','critical_receipt_search.json'):
        p=OUT/name
        if p.exists():found.update(load(p)['exact_sources'])
    selected=[r for r in rows if r['sha256'] in found]
    logged={}
    journal=ROOT/'output/storage_retention/cleanup_20261023/after_rebuild/deleted_files.jsonl'
    with journal.open(encoding='utf-8') as f:
        for line in f:
            d=json.loads(line)
            if d['sha256'] in found:logged[d['path']]=d
    for row in selected:
        assert logged[row['path']]['sha256']==row['sha256'] and logged[row['path']]['size']==row['size']
        dest=safe_path(row['path'],target=True)
        if dest.exists() and sha(dest)!=row['sha256']:raise FileExistsError(str(dest))
        src=safe_path(found[row['sha256']]['path'])
        assert src.is_file() and src.stat().st_size==row['size'] and sha(src)==row['sha256']
    restored=[];already=[];before=protected()
    with (OUT/'restore_journal.jsonl').open('x',encoding='utf-8',buffering=1) as log:
        for row in selected:
            source=safe_path(found[row['sha256']]['path']);data=source.read_bytes()
            assert len(data)==row['size'] and hashlib.sha256(data).hexdigest()==row['sha256']
            dest=safe_path(row['path'],target=True)
            if dest.exists():
                assert sha(dest)==row['sha256'];already.append(row['path'])
            else:
                assert dest.parent.is_dir()
                with dest.open('xb') as f:assert f.write(data)==len(data)
                restored.append(row['path'])
            assert sha(dest)==row['sha256']
            log.write(json.dumps(dict(path=row['path'],sha256=row['sha256'],size=row['size'],source=found[row['sha256']]),ensure_ascii=False)+'\n')
    selected_paths={r['path'] for r in selected}
    remaining=[r for r in rows if r['path'] not in selected_paths]
    save('remaining_targets.json',remaining)
    assert all(sha(safe_path(r['path'],target=True))==r['sha256'] for r in selected)
    save('restoration.json',dict(restored_files=len(restored),already_present_verified=len(already),verified_files=len(selected),restored_bytes=sum(r['size'] for r in selected if r['path'] in restored),remaining_files=len(remaining),remaining_bytes=sum(r['size'] for r in remaining),deleted_files=0,overwritten_files=0,pointers_unchanged=before==protected(),status='PASS'))
    print(json.dumps(dict(restored=len(restored),verified=len(selected),remaining=len(remaining))),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['packages','snapshot','receipts','ordered-snapshot','html','restore']);a=p.parse_args()
    {'packages':packages,'snapshot':snapshot,'receipts':receipt_sweep,'ordered-snapshot':ordered_snapshot,'html':reconstruct_html,'restore':restore_found}[a.mode]()
