"""Inventory every displayed answer by mathematical and condition wording."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
from collections import defaultdict
from hashlib import sha256
import json,re
from build import HERE
from presentation import answer
from branch_reading import explain
from review_output import parse_review_id, review_directory, write_new_text

ROOT=HERE.parents[1]
def normalize(s):return re.sub(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?','N',str(s))
def main(review_id=None):
    out=review_directory(ROOT,review_id)
    families={};entries=[]
    for path in read_path(ROOT/'output/character_skills/pages',root=ROOT).glob('[0-9]*/card.json'):
        card=json.loads(path.read_bytes());cid=int(path.parent.name)
        for g in card['groups']:
            for s in g['skills']:
                for row in s['rows']:
                    for index,a in enumerate(row['answers']):
                        v=explain(answer(a,cid),a,row,s,{})
                        key=(a.get('rule_key'),a.get('quantity_kind'),normalize(a.get('value')),normalize(v['text']),normalize(v['condition']))
                        fid=sha256(json.dumps(key,ensure_ascii=False).encode()).hexdigest()[:16]
                        if fid not in families:
                            families[fid]={'id':fid,'rule':a.get('rule_key'),'kind':a.get('quantity_kind'),
                                'sourceValuePattern':key[2],'displayPattern':key[3],'conditionPattern':key[4],
                                'examples':[],'count':0}
                        f=families[fid];f['count']+=1
                        if len(f['examples'])<2:f['examples'].append({'rowId':row['row_id'],'japanese':row['japanese'],
                            'context':row.get('context_text'),'answer':a,'display':v})
                        entries.append({'rowId':row['row_id'],'answerIndex':index,'familyId':fid})
    ordered=sorted(families.values(),key=lambda f:((f['rule'] or ''),f['kind'] or '',f['id']))
    write_new_text(out/'numeric_families.json',json.dumps(ordered,ensure_ascii=False,indent=2))
    with (out/'numeric_rows.jsonl').open('x',encoding='utf8') as f:
        for e in entries:f.write(json.dumps(e,ensure_ascii=False)+'\n')
    write_new_text(out/'numeric_compact.json',json.dumps([{k:v for k,v in f.items() if k!='examples'}|{'sample':{k:f['examples'][0]['answer'].get(k) for k in ('raw_value','value','unit','condition_label','conditions')},'display':{k:f['examples'][0]['display'].get(k) for k in ('text','condition','note','branchLabel','mappingNote')}} for f in ordered],ensure_ascii=False,indent=2))
    print(json.dumps({'answers':len(entries),'families':len(families),'output':str(out)}))
if __name__=='__main__':main(parse_review_id(__doc__))
