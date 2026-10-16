"""Snapshot-specific checks for full external collection and envelope variants."""
import argparse
import csv
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

from build_field_guide import get_path
from decode_cache_variants import decode_variant,parse_variant
from export_master import strict_load,typed_value,sha,write_json


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True)
    args=parser.parse_args();out=args.input/'analysis';checks=[]
    report=strict_load((args.input/'decode_report.json').read_bytes())
    extraction=strict_load(Path('output/phone_full_20261015/extraction/extraction.json').read_bytes())
    assert extraction['status']=='PASS' and extraction['expected_files']==extraction['extracted_files']==68828
    assert not extraction['missing'] and not extraction['differences'] and not extraction['unsupported']
    checks.append('68828 archive members match complete external inventory by path and size; raw archive retained')
    assert report['input_files']==report['decoded_files']==77 and report['status']=='PASS'
    documents={};raws={};tables=Counter()
    for row in report['files']:
        source=Path(row['source']).read_bytes();raw=Path(row['json_file']).read_bytes()
        assert sha(source)==row['source_sha256'] and sha(raw)==row['json_raw_sha256']
        meta=row['native_validation'];assert meta['sha1_match'] and meta['gzip_crc_and_size']=='PASS'
        assert meta['source_sha256']==row['source_sha256'] and meta['json_raw_sha256']==sha(raw)
        key='CACHE/'+row['filename']+'.json.raw';raws[key]=raw;documents[key]=strict_load(raw)
    checks.append('All77 ciphertext/JSON hashes and native SHA1 plus gzip CRC/length evidence match current sources')
    records=[strict_load(line) for line in (args.input/'records.jsonl').open(encoding='utf-8')]
    assert len(records)==report['exported_record_views']==39047
    by_key={r['record_key']:r for r in records};assert len(by_key)==len(records)
    for r in records:
        loc=r['location'];raw=raws[r['source_key']][loc['byte_begin']:loc['byte_end_exclusive']]
        assert sha(raw)==loc['raw_record_sha256']
        assert typed_value(strict_load(raw))==typed_value(r['raw'])==typed_value(get_path(documents[r['source_key']],loc['json_pointer']))
        tables[(r['source_key'],r['table_path'])]+=1
    for row in report['files']:
        for table,count in row['tables'].items():assert tables[('CACHE/'+row['filename']+'.json.raw',table)]==count
    checks.append('39047 record/document views match exact JSON bytes and pointers, including nested Boss tables and scalar arrays')
    cards=[r for r in records if r['table']=='charainfo'];slots=Counter(len(r['raw'].get('skillid',[])) for r in cards)
    assert sum(slots.values())==1488
    for r in cards:assert r['raw']['skillid']==get_path(documents[r['source_key']],r['location']['json_pointer'])['skillid']
    checks.append('All character slot arrays remain complete and ordered; eight-slot runtime roles not inferred')
    for name in ('helper','search','bossinfo'):
        source=next(row for row in report['files'] if row['filename']==name+'.data5')
        decoded=decode_variant(Path(source['source']).read_bytes(),source['filename'])
        assert decoded['json_raw']==Path(source['json_file']).read_bytes()
        assert decoded['meta']['gzip_offset']==(0 if name in ('helper','search') else 6)
    checks.append('Repeated native decrypt matches new two offset0 files and known offset6 Boss file exactly')
    source=next(row for row in report['files'] if row['filename']=='helper.data5')
    original=decode_variant(Path(source['source']).read_bytes(),'helper.data5')
    p=original['plaintext'];payload=original['payload']
    def rejected(label,fn):
        try:fn()
        except (ValueError,EOFError,OSError):checks.append(label);return
        raise AssertionError('Invalid fixture accepted: '+label)
    damaged=bytearray(p);damaged[36]^=1
    rejected('Modified plaintext payload rejected by outer SHA1',lambda:parse_variant(bytes(damaged)))
    short=bytearray(p[:36]);part=payload[:-5];struct.pack_into('<I',short,12,len(part));short[16:36]=hashlib.sha1(part).digest()
    rejected('Truncated offset0 gzip with recomputed outer SHA1 rejected by gzip boundary/CRC',lambda:parse_variant(bytes(short)+part))
    cipher=bytearray(Path(source['source']).read_bytes());cipher[len(cipher)//2]^=1
    rejected('Modified ciphertext rejected by native envelope validation',lambda:decode_variant(bytes(cipher),'helper.data5'))
    rejected('Wrong filename rejected by native envelope validation',lambda:decode_variant(Path(source['source']).read_bytes(),'helper.data5x'))
    quest=next(r for r in report['files'] if r['filename']=='questdigest.data5')
    assert quest['native_validation']['execution_bound']=={'timeout_us':60000000,'instructions':120000000}
    assert quest['native_validation']['gzip_offset']==6
    checks.append('Large quest file retains bounded execution settings and existing offset6 integrity validation')
    summary=strict_load((out/'summary.json').read_bytes());sample=strict_load((out/'cid2327_patterns.json').read_bytes())
    assert len(sample['patterns'])==3 and len(sample['boss_skills'])==6
    assert all(r['resolution']['status']=='RESOLVED' and r['resolution']['layer']=='CACHE' for r in summary['previous_nine_missing_ids'])
    assert {r['raw']['skillid'] for r in sample['boss_skills']}==set(range(40232700,40232706))
    conflict=strict_load((out/'skill36000358_sources.json').read_bytes())['sources']
    assert conflict['CACHE'][0]['raw']['param1']==400 and conflict['APK'][0]['raw']['param1']==300
    checks.append('Sample3 patterns/6 Boss skills and prior9 missing IDs now present; source conflict400/300 remains separate')
    for csv_name,json_name in [('field_dictionary.csv','field_dictionary.json'),('coverage_audit.csv','coverage_audit.json'),
                               ('cid2327_pattern_fields.csv','cid2327_pattern_fields.json'),('highhp_fields.csv','highhp_fields.json')]:
        with (out/csv_name).open(encoding='utf-8-sig',newline='') as stream:count=sum(1 for _ in csv.DictReader(stream))
        assert count==len(strict_load((out/json_name).read_bytes()))
    dictionary=strict_load((out/'field_dictionary.json').read_bytes())
    with (out/'field_dictionary.csv').open(encoding='utf-8-sig',newline='') as stream:
        for index,row in enumerate(csv.DictReader(stream)):
            example=strict_load(row['原始值示例JSON（长值为有标识预览）'])
            if isinstance(example,dict) and example.get('truncated_for_csv'):
                assert example['full_value']==f'field_dictionary.json#/{index}/examples'
                assert json.dumps(dictionary[index]['examples'],ensure_ascii=False).startswith(example['preview'])
            else:assert typed_value(example)==typed_value(dictionary[index]['examples'])
    checks.append('CSV views and JSON counts agree; raw types, unknown values and source-specific records preserved')
    references=[strict_load(line) for line in (out/'references.jsonl').open(encoding='utf-8')]
    assert len(references)==summary['reference_count'] and sum(summary['reference_results'].values())==len(references)
    for ref in references:assert get_path(by_key[ref['parent_record_key']]['raw'],ref['field_path'])==ref['id_raw']
    coverage=strict_load((out/'coverage_audit.json').read_bytes());assert sum(r['acquired_files'] for r in coverage)==68828
    checks.append('Reference paths match raw values and all three inventory categories reconcile to68828; missing candidates retained')
    write_json(out/'checks.json',{'status':'PASS','checks':checks,'slot_lengths':dict(slots),'record_views':len(records),
                                 'scope':'This cache snapshot; not arbitrary future snapshot acceptance or live gameplay verification'})
    print(json.dumps({'status':'PASS','checks':len(checks),'records':len(records),'slot_lengths':dict(slots)}))


if __name__=='__main__':main()
