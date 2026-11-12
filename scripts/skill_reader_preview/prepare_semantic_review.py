"""Freeze every description into auditable, number-parameterized review units."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
from collections import defaultdict, Counter
from hashlib import sha256
import json,re,unicodedata
from translation_bridge import Translator,canonical,body_copy
from build import rows,read,HERE
from review_output import parse_review_id, review_directory, write_new_text

ROOT=HERE.parents[1]
NUM=re.compile(r'\d+(?:\.\d+)?')
def skeleton(jp):
    jp=canonical(jp)
    values=[]
    def number(m):
        values.append(m[0]);return '{n'+str(len(values)-1)+'}'
    return NUM.sub(number,jp),values

def main(review_id=None):
    out=review_directory(ROOT,review_id)
    if (out/'manifest.json').exists():
        raise FileExistsError('Review inputs already frozen. Use a new audit batch for changed sources; do not overwrite this manifest or its packets.')
    (out/'packets').mkdir()
    (out/'results').mkdir(exist_ok=True)
    t=Translator(ROOT)
    units={};rowmap=[];hashes={}
    for path in sorted(read_path(ROOT/'output/character_skills/pages',root=ROOT).glob('[0-9]*/card.json'),key=lambda p:int(p.parent.name)):
        blob=path.read_bytes();card=json.loads(blob);cid=int(path.parent.name)
        hashes[str(cid)]=sha256(blob).hexdigest()
        for group in card['groups']:
            for skill in group['skills']:
                for row in skill['rows']:
                    jp=row['japanese'];key,values=skeleton(jp)
                    uid=sha256(key.encode()).hexdigest()[:16]
                    tr=t.translate(jp)
                    if uid not in units:
                        candidates=[]
                        if tr['translationStatus']!='pending':candidates.append(body_copy(tr['textZh']))
                        for p in t.refs.get(canonical(jp),[]):
                            zh=body_copy(p['textZh'])
                            if zh not in candidates:candidates.append(zh)
                        units[uid]={'id':uid,'jpPattern':key,'japanese':jp,'numbers':values,
                            'currentChinese':body_copy(tr['textZh']) if tr['translationStatus']!='pending' else None,
                            'previousStatus':tr['translationStatus'],'candidates':candidates[:3],
                            'exampleRow':row['row_id'],'sourceFile':f'output/character_skills/pages/{cid}/card.json',
                            'context':skill.get('original_text',''),'occurrences':0}
                    units[uid]['occurrences']+=1
                    rowmap.append({'rowId':row['row_id'],'cid':cid,'unitId':uid,'japanese':jp,'numbers':values,
                                   'group':group['group'],'context':skill.get('original_text',''),
                                   'answerCount':len(row['answers'])})
    ordered=sorted(units.values(),key=lambda u:(u['previousStatus']=='pending',-u['occurrences'],u['id']))
    # Keeping all statuses interleaved prevents "already Chinese" exemption.
    reviewable=[u for u in ordered if u['previousStatus']!='pending'];pending=[u for u in ordered if u['previousStatus']=='pending']
    ordered=[]
    while reviewable or pending:
        for arr in (reviewable,pending,pending):
            if arr:ordered.append(arr.pop(0))
    manifest=[]
    for index in range(0,len(ordered),60):
        batch=index//60
        packet=ordered[index:index+60]
        name=f'packet_{batch:03}.json'
        write_new_text(out/'packets'/name,json.dumps(packet,ensure_ascii=False,indent=2))
        manifest.append({'packet':name,'units':len(packet),'ids':[u['id'] for u in packet]})
    write_new_text(out/'units.json',json.dumps(units,ensure_ascii=False))
    with (out/'rows.jsonl').open('x',encoding='utf-8') as f:
        for row in rowmap:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    report={'sourceHashes':hashes,'rows':len(rowmap),'units':len(units),'packets':manifest,
            'previousUnitStatuses':dict(Counter(u['previousStatus'] for u in units.values()))}
    write_new_text(out/'manifest.json',json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({**{k:v for k,v in report.items() if k not in ('sourceHashes','packets')},'output':str(out)},ensure_ascii=False))

if __name__=='__main__':main(parse_review_id(__doc__))
