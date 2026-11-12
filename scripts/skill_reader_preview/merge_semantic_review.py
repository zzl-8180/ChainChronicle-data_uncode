"""Validate model-read review packets; never mark absent packets reviewed."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path
from versioned_outputs import fresh_output
from collections import Counter
from hashlib import sha256
import argparse,json,re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
AUDIT=ROOT/'output/character_skills/reader_semantic_20261107'
PLACEHOLDER=re.compile(r'\{n\d+\}')

def collect(audit=AUDIT, complete=False, output_dictionary=None, *, progress_output=None):
    audit=read_path(audit,root=ROOT)
    manifest=json.loads((audit/'manifest.json').read_text(encoding='utf8'))
    merged={};missing=[];errors=[];stats=Counter()
    for packet in manifest['packets']:
        name=packet['packet'];path=audit/'results'/name
        if not path.exists():missing.append(name);continue
        originals=json.loads((audit/'packets'/name).read_text(encoding='utf8'))
        try:results=json.loads(path.read_text(encoding='utf-8-sig'))
        except Exception as e:errors.append([name,str(e)]);continue
        if not isinstance(results,list) or [x.get('id') for x in results]!=packet['ids']:
            errors.append([name,'ID order or coverage differs']);continue
        for original,result in zip(originals,results):
            uid=result['id'];zh=result.get('zhPattern')
            if uid in merged:errors.append([name,uid,'duplicate']);continue
            if not isinstance(zh,str):errors.append([name,uid,'not text']);continue
            if Counter(PLACEHOLDER.findall(zh))!=Counter(PLACEHOLDER.findall(original['jpPattern'])):
                errors.append([name,uid,'placeholder multiset differs']);continue
            if re.search(r'\d',PLACEHOLDER.sub('',zh)):
                errors.append([name,uid,'unbound numeral']);continue
            if original['jpPattern'] and not zh.strip():errors.append([name,uid,'empty text']);continue
            if original['jpPattern'].count('【')!=zh.count('【'):
                errors.append([name,uid,'embedded skill header omitted']);continue
            if any(s in original['jpPattern'] for s in ('倒す','倒した','倒して')) and '転倒' not in original['jpPattern'] and '击倒' in zh:
                errors.append([name,uid,'kill trigger confused with knockdown status']);continue
            if result.get('verdict') not in ('pass','corrected','translated'):
                errors.append([name,uid,'verdict missing']);continue
            merged[uid]={**result,'jpPattern':original['jpPattern'],'packet':name,
                'inputHash':sha256(json.dumps(original,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                'resultHash':sha256(path.read_bytes()).hexdigest()}
            stats[result['verdict']]+=1
    summary={'expectedUnits':manifest['units'],'reviewedUnits':len(merged),'missingPackets':missing,
             'errors':errors,'verdicts':dict(stats),'complete':not missing and not errors and len(merged)==manifest['units']}
    if progress_output is not None:
        with write_path(progress_output,root=ROOT).open('x',encoding='utf8') as stream:
            json.dump(summary,stream,ensure_ascii=False,indent=2)
    if errors:raise ValueError(json.dumps(errors[:30],ensure_ascii=False))
    if complete:
        if not summary['complete']:raise ValueError('Review packets incomplete')
        # Refuse to apply a review to a changed source snapshot.
        for cid,digest in manifest['sourceHashes'].items():
            path=read_path(ROOT/'output/character_skills/pages'/cid/'card.json',root=ROOT)
            if sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Source changed: '+cid)
        destination=write_path(output_dictionary or HERE/'semantic_sentences.json',root=ROOT)
        with destination.open('x' if output_dictionary is not None else 'w',encoding='utf8') as stream:
            json.dump({'sourceHashes':manifest['sourceHashes'],'units':merged},stream,ensure_ascii=False,indent=2)
    return summary,merged

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--complete',action='store_true')
    parser.add_argument('--audit',type=Path,default=AUDIT)
    parser.add_argument('--output-dictionary',type=Path)
    parser.add_argument('--output',type=Path,help='Fresh independent report directory')
    args=parser.parse_args()
    out=fresh_output('projects/reader/reports/review','semantic-merge',args.output)
    dictionary=args.output_dictionary or out/'semantic_sentences.json'
    if args.complete and write_path(dictionary,root=ROOT).exists():
        raise FileExistsError(dictionary)
    s,_=collect(audit=args.audit,complete=args.complete,output_dictionary=dictionary,
                progress_output=out/'review_progress.json')
    print(json.dumps({k:v for k,v in s.items() if k!='missingPackets'}|{'missingPacketCount':len(s['missingPackets']),'output':str(out)},ensure_ascii=False))
