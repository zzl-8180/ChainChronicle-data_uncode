"""Decode every acquired data5, preserve per-file failures and export exact record spans."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from decode_data5 import NativeDecoder
from export_master import parse_records, strict_load, typed_value
from decode_cache_variants import decode_variant


def sha(data):return hashlib.sha256(data).hexdigest()


def located_tables(raw):
    """Descend dictionary wrappers only; arrays keep their ordered nested contents."""
    decoder=json.JSONDecoder()
    def walk(block,prefix='',base=0):
        text=block.decode('utf-8');pos=1;cursor=byte_cursor=0
        while True:
            while text[pos].isspace():pos+=1
            if text[pos]=='}':break
            key,pos=decoder.raw_decode(text,pos)
            while text[pos].isspace():pos+=1
            assert text[pos]==':'
            pos+=1
            while text[pos].isspace():pos+=1
            begin=pos;value,end=decoder.raw_decode(text,pos)
            byte_cursor+=len(text[cursor:begin].encode('utf-8'));byte_begin=byte_cursor
            byte_cursor+=len(text[begin:end].encode('utf-8'));byte_end=byte_cursor;cursor=end
            pointer=prefix+'/'+key.replace('~','~0').replace('/','~1')
            if isinstance(value,list):
                _,items=parse_records(block,key)
                for _,location in items:
                    location['json_pointer']=prefix+location['json_pointer']
                    location['byte_begin']+=base;location['byte_end_exclusive']+=base
                yield pointer,items
            elif isinstance(value,dict):
                yield from walk(block[byte_begin:byte_end],pointer,base+byte_begin)
            pos=end
            while text[pos].isspace():pos+=1
            if text[pos]==',':pos+=1
    yield from walk(raw)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reuse-dir',type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    decoded_dir=args.output/'decoded';decoded_dir.mkdir()
    old_report=json.loads(Path('output/decoded/report.json').read_bytes())
    old={Path(r['source']).name:r for r in old_report['files']}
    verified={}
    if args.reuse_dir:
        earlier=json.loads((args.reuse_dir/'decode_report.json').read_bytes())
        for row in earlier['files']:
            if row['status']=='DECODED':verified[row['filename']]=(row['native_validation'],Path(row['json_file']))
        for path in (args.reuse_dir/'recovered_variants').glob('*.report.json'):
            meta=json.loads(path.read_bytes())
            verified[meta['filename']]=(meta,path.with_name(meta['filename']+'.json.raw'))
    sources=list(args.work.rglob('*.data5'))
    assert sources,'No acquired data5 files'
    assert len({p.name for p in sources})==len(sources),'Repeated basename needs explicit namespace'
    priority={'bossinfo.data5':0,'charainfo.data5':1,'skilllist.data5':2}
    sources.sort(key=lambda p:(priority.get(p.name,3),p.name))
    results=[];tables=[];count=0
    with (args.output/'records.jsonl').open('w',encoding='utf-8') as records:
        for source in sources:
            raw=source.read_bytes();row={'source':str(source),'filename':source.name,'source_sha256':sha(raw),'source_bytes':len(raw)}
            try:
                previous=old.get(source.name)
                reused=verified.get(source.name)
                if reused and reused[0]['source_sha256']==row['source_sha256']:
                    meta,path=reused;plaintext=path.read_bytes()
                    assert sha(plaintext)==meta['json_raw_sha256']
                    document=strict_load(plaintext);row['method']='REUSE_THIS_SNAPSHOT_VERIFIED_DECODE'
                elif previous and previous['source_sha256']==row['source_sha256']:
                    plaintext=Path('output/decoded',source.name+'.json.raw').read_bytes()
                    assert sha(plaintext)==previous['json_raw_sha256']
                    document=strict_load(plaintext);meta=previous
                    row['method']='REUSE_EXACT_CIPHERTEXT_AND_VERIFIED_JSON'
                else:
                    decoder=NativeDecoder()
                    try:decoded=decoder.decode(raw,source.name)
                    except ValueError as error:
                        if not any(message in str(error) for message in ('Observed gzip signature','Execution limit')):raise
                        decoded=decode_variant(raw,source.name)
                    plaintext=decoded['json_raw'];document=strict_load(plaintext);meta=decoded['meta']
                    row['method']='EXISTING_NATIVE_DECODER'
                    del decoder
                out=decoded_dir/(source.name+'.json.raw');out.write_bytes(plaintext)
                row.update(status='DECODED',json_file=str(out),json_raw_sha256=sha(plaintext),native_validation=meta)
                arrays=[key for key,value in document.items() if isinstance(value,list)]
                row['non_array_top_fields']=[key for key in document if key not in arrays]
                row['tables']={}
                located_arrays=list(located_tables(plaintext))
                if not located_arrays or source.name=='const.data5':
                    located_arrays=[('@document',[(document,{'json_pointer':'','ordinal_zero_based':0,'byte_begin':0,'byte_end_exclusive':len(plaintext),'raw_record_sha256':sha(plaintext)})])]
                for table_path,located in located_arrays:
                    table=table_path.rsplit('/',1)[-1] if table_path.startswith('/bossinfo/') or table_path.count('/')<=1 else table_path.strip('/')
                    for value,location in located:
                        span=plaintext[location['byte_begin']:location['byte_end_exclusive']]
                        assert typed_value(strict_load(span))==typed_value(value)
                        record={'record_key':'CACHE/'+source.name+'.json.raw#'+location['json_pointer'],
                                'source_key':'CACHE/'+source.name+'.json.raw','layer':'CACHE','table':table,'table_path':table_path,
                                'snapshot_id':args.output.name,'original_file':str(source),'source_sha256':row['source_sha256'],
                                'location':location,'raw':value,'analysis_named_table':table=='@document'}
                        records.write(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n');count+=1
                    row['tables'][table_path]=len(located)
                    tables.append({'file':source.name,'table':table,'records':len(located),'basis':'Decoded array boundary' if table!='@document' else 'Root document analysis view','json_file':str(out)})
                row['exported_record_views']=sum(row['tables'].values())
            except Exception as exc:
                row.update(status='FAILED_RETAINED',error=f'{type(exc).__name__}: {exc}')
            results.append(row)
            (args.output/'decode_progress.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({k:row[k] for k in ('filename','status','method','tables','error') if k in row},ensure_ascii=True),flush=True)
    report={'status':'PASS' if all(r['status']=='DECODED' for r in results) else 'PARTIAL_FAILURES_RETAINED',
            'input_files':len(sources),'decoded_files':sum(r['status']=='DECODED' for r in results),'exported_record_views':count,
            'files':results,'tables':tables,'producer_sha256':sha(Path(__file__).read_bytes()),
            'decoder_sha256':sha(Path('scripts/decode_data5.py').read_bytes()),'native_provenance':{k:v for k,v in old_report.items() if k not in ('files','status','scope')},
            'variant_parser_sha256':sha(Path('scripts/decode_cache_variants.py').read_bytes()),
            'limits':['Current acquired data5 only; bdl containers preserved raw and not yet decoded','All raw JSON fields retained; no inferred live values','Non-array wrapper fields remain in complete source JSON; @document counts are not game entities']}
    (args.output/'decode_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with (args.output/'tables.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['file','table','records','basis','json_file']);writer.writeheader();writer.writerows(tables)
    print(json.dumps({k:report[k] for k in ('status','input_files','decoded_files','exported_record_views')}),flush=True)


if __name__=='__main__':main()
