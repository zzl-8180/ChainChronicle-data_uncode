"""Read-only census; writes only this experiment's candidate inventory."""
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
from versioned_outputs import experiment_output
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
OUT = experiment_output('skill_mechanism_scale')
EXCLUDE = {7250,30105,30301,30329,30334,30236,30239,20234,30110,30333,30107,30313}

def read(p):
    return json.loads(read_path(ROOT / p, root=ROOT).read_text(encoding='utf-8-sig'))

def main():
    skills = {x['skillid']:x for x in read('output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')['skilllist']}
    boss = read('output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw')['bossinfo']
    patterns = {x['patternid']:x for x in boss['bosspattern']}
    bs = {x['skillid']:x for x in boss['bossskill']}
    descriptions = []
    with read_path(ROOT/'output/character_skills/effect_ledger/ledger.jsonl', root=ROOT).open(encoding='utf-8') as f:
        for line in f:
            x = json.loads(line)
            if x['record_type']=='description' and x['cid'] not in EXCLUDE and x['effect_status_counts']['unresolved'] and not x['answer_ref_count']:
                descriptions.append(x)
    cards = {}
    found = []
    for d in descriptions:
        cid = d['cid']
        if cid not in cards:
            cards[cid] = read(f'output/character_skills/pages/{cid}/card.json')
        for g in cards[cid]['groups']:
            for s in g['skills']:
                r = next((r for r in s['rows'] if r['row_id']==d['row_id']),None)
                if r is None or r['answers'] or s.get('layer')!='CACHE': continue
                fam = None
                rec = skills.get(s.get('record_id'),{}) if s['table']=='skilllist' else {}
                child = [skills.get(i,{}) for i in rec.get('sub',[])]
                types = [c.get('ability') for c in child]
                if re.fullmatch(r'攻撃力(?:と(?:防御力|移動速度|クリティカル発生率|クリティカル威力))*が上がる。',r['japanese']) and types.count(1095)==1: fam='attack1095'
                if 'WAVE' in r['japanese'] and '攻撃力' in r['japanese'] and types.count(4)==1: fam='wave4'
                if '敵' in r['japanese'] and ('下が' in r['japanese'] or '低下' in r['japanese']) and (rec.get('ability')==2003 or 2003 in types): fam='debuff2003'
                source = s.get('source',{})
                if s['table']=='bosspattern':
                    pat = patterns.get(s.get('record_id'),{})
                    children = [bs.get(v,{}) for k,v in pat.items() if k.startswith('skillid') and isinstance(v,int)]
                    types = [c.get('skillid0') for c in children]
                    if 108 in types and '回復' in r['japanese'] and ('一定間隔' in r['japanese'] or '上限' in r['japanese']): fam='heal108'
                if fam:
                    found.append({'family':fam,'cid':cid,'row_id':r['row_id'],'japanese':r['japanese'],'types':types,
                                  'source_skill':{k:s.get(k) for k in ['table','record_id','layer','reference_field','source']},
                                  'baseline_description':d})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'census.json').write_text(json.dumps(found,ensure_ascii=False,indent=2),encoding='utf-8')
    print(Counter(x['family'] for x in found))
    for fam in sorted({x['family'] for x in found}):
        print(fam)
        for x in [x for x in found if x['family']==fam][:16]:
            print(x['cid'],x['row_id'],x['japanese'],x['types'])

if __name__=='__main__': main()
