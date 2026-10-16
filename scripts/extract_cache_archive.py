"""Extract a collected archive to a working copy and reconcile every listed file."""
import argparse
import json
import shutil
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    acquisition=json.loads((args.snapshot/'acquisition.json').read_bytes())
    assert acquisition['status']=='STREAM_COPIED_NEEDS_VALIDATION'
    user=acquisition['probe']['android_user']
    prefix=f'/storage/emulated/{user}/Android/data/com.sega.chainchronicle/'
    inventory=[json.loads(line) for line in (args.snapshot/'inventory.jsonl').open(encoding='utf-8')]
    expected={r['path'][len(prefix):]:r for r in inventory if r['path'].startswith(prefix)}
    args.work.mkdir(parents=True,exist_ok=False)
    args.output.mkdir(parents=True,exist_ok=False)
    seen=set();types=Counter();mismatches=[];unsupported=[];total_bytes=0
    with (args.output/'files.jsonl').open('w',encoding='utf-8') as log, tarfile.open(args.snapshot/'external_cache.tar','r:') as archive:
        for member in archive:
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] not in ('files','cache'):
                raise ValueError(f'Unsafe archive path: {member.name}')
            destination=args.work.joinpath(*path.parts)
            if member.isdir():
                destination.mkdir(parents=True,exist_ok=True);continue
            if not member.isfile():
                unsupported.append({'name':member.name,'type':repr(member.type)});continue
            key=path.as_posix()
            assert key not in seen, f'Duplicate tar member: {key}'
            seen.add(key);destination.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(member) as source, destination.open('xb') as target:
                header=source.read(64);target.write(header);shutil.copyfileobj(source,target,1024*1024)
            size=destination.stat().st_size
            assert size==member.size, f'Truncated extracted member: {key}'
            kind=next((label for signature,label in ((b'UnityFS\0','UnityFS'),(b'UnityRaw\0','UnityRaw'),(b'UnityWeb\0','UnityWeb'),
                      (b'PK\x03\x04','ZIP'),(b'SQLite format 3\0','SQLite'),(b'\x1f\x8b','gzip')) if header.startswith(signature)),
                      'data5_candidate' if path.suffix=='.data5' else 'EMPTY' if not size else 'OTHER_UNCLASSIFIED')
            types[kind]+=1;total_bytes+=size
            old=expected.get(key)
            status='SIZE_MATCH' if old and old['size']==size else 'SIZE_CHANGED' if old else 'NEW_SINCE_INVENTORY'
            row={'path':key,'local':destination.as_posix(),'bytes':size,'inventory_bytes':old['size'] if old else None,
                 'inventory_status':status,'format_by_header':kind,'header64_hex':header.hex()}
            log.write(json.dumps(row,ensure_ascii=False)+'\n')
            if status!='SIZE_MATCH':mismatches.append(row)
            if len(seen)%10000==0:print(json.dumps({'extracted_files':len(seen),'bytes':total_bytes}),flush=True)
    missing=sorted(set(expected)-seen)
    result={'status':'PASS' if not(missing or mismatches or unsupported) else 'DIFFERENCES_RETAINED',
            'snapshot':str(args.snapshot),'work':str(args.work),'expected_files':len(expected),'extracted_files':len(seen),
            'bytes':total_bytes,'header_formats':dict(types),'missing':missing,'differences':mismatches,'unsupported':unsupported,
            'limit':'File names and sizes match acquisition inventory; not atomic or full-game coverage; no full media dual-end hashes'}
    (args.output/'extraction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('missing','differences','unsupported')}),flush=True)


if __name__=='__main__':main()
