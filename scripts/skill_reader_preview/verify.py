"""Check source alignment and the preview's known semantic regression boundaries."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
from versioned_outputs import fresh_output
import json
import re
import unicodedata
from presentation import readable_value, confidence
from build import CIDS, rows, read, HERE

def main():
    root=HERE.parents[1]
    out=read_path(root/'output/character_skills/reader_preview_20261106',root=root)
    def payload(name,variable):
        s=(out/f'data/{name}.js').read_text(encoding='utf-8')
        return json.loads(s[len(f'window.{variable}='):-2])
    catalog=payload('catalog','CC_CATALOG');details=payload('cards','CC_DETAILS')
    checks=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    check('full catalog has 2236 unique cards',len(catalog['cards'])==len({c['cid'] for c in catalog['cards']})==2236)
    check('six detail cards',set(details)==set(map(str,CIDS)))
    expected_rows,expected_answers=0,0
    for cid in CIDS:
        source=read(read_path(root/f'output/character_skills/pages/{cid}/card.json',root=root))
        original={r['row_id']:r for r in rows(source)}
        displayed=[r for g in details[str(cid)]['groups'] for s in g['skills'] for r in s['rows']]
        check(f'{cid}: all descriptions retained',set(original)=={r['id'] for r in displayed})
        for r in displayed:
            old=original[r['id']]
            check(f'{r["id"]}: original exact',r['original']==old['japanese'])
            original_numbers=set(re.findall(r'\d+(?:\.\d+)?',unicodedata.normalize('NFKC',r['original'])))
            translated_numbers=set(re.findall(r'\d+(?:\.\d+)?',r['textZh']))
            check(f'{r["id"]}: explicit numbers retained in Chinese',original_numbers<=translated_numbers)
            check(f'{r["id"]}: reviewed terminology',not any(t in r['textZh'] for t in ('大范围伤害','原地','副队伍','主队伍','黑暗','击飞','暴击伤害','队伍最前面','最低档','护盾可以叠加')))
            presented=r['unboundAnswers']+[a for e in r['effects'] for a in e['answers']]
            check(f'{r["id"]}: every answer retained',{a['source']['answerIndex'] for a in presented}==set(range(len(old['answers']))))
            for a in presented:
                src=old['answers'][a['source']['answerIndex']]
                check(f'{r["id"]}: numeric/source fidelity',
                      a['source']['raw']==src.get('raw_value') and a['source']['originalAnswer']==src.get('value')
                      and a['source']['allSources']==(src.get('source') or {})
                      and a['confidence']==confidence(src))
                check(f'{r["id"]}: no code terms in reading layer',not any(t in a['text']+' '+a['condition'] for t in ('float32','trunc','pattern','param','normalAtk','本样稿')))
            expected_rows+=1;expected_answers+=len(old['answers'])
    check('245 rows and 334 answers',expected_rows==245 and expected_answers==334)
    en=next(r for g in details['350']['groups'] for s in g['skills'] for r in s['rows'] if r['id']=='350-special_move-special_move-pattern0-lvorder0-f0')
    aa=[a for e in en['effects'] for a in e['answers']]
    normal=next(a for a in aa if a['source']['raw']==25)
    enhanced=next(a for a in aa if a['source']['raw']==27.5)
    check('25 tied to first damage, not echo','首次范围伤害' in normal['mappingNote'])
    check('27.5 association is visibly tentative','推测' in enhanced['mappingNote'] and enhanced['confidence']=='inferred')
    linked=next(r for g in details['350']['groups'] for s in g['skills'] for r in s['rows'] if r['id']==enhanced['relatedDescription']['rowId'])
    check('27.5 links actual Chain condition','1stChain以上' in linked['original'])
    check('raw branch conditions retained',enhanced['source']['originalBinding']['conditions_raw']['chs']==2)
    sk=next(s for g in details['350']['groups'] for s in g['skills'] if any(r['id']==en['id'] for r in s['rows']))
    check('trailing condition promoted without losing original row',sk['conditionRowId']==linked['id'])
    check('explicit scope covers all five topics',set(sk['conditionScope'])=={'法珠消耗','必杀威力','反响威力','回复量','我方增益'})
    check('condition effect labels use exact original spans',[e['label'] for e in linked['effects']]==['必杀威力','反响威力','回复量','我方增益'])
    cases=[
        ({'quantity_kind':'攻击增加比例','value':'+60%（局部倍率1+0.6×Chain）'},'连携修正'),
        ({'quantity_kind':'屏障固定防御量系数','value':'固定防御量=trunc(接受者当前normalAtk×float32(2×请求系数))'},'技能修正'),
        ({'rule_key':'skilllist|1017|/param3','quantity_kind':'受伤量倍率','raw_value':.85},'15%'),
        ({'rule_key':'skilllist|1095|/param5','quantity_kind':'暴击概率加算贡献','raw_value':.35},'35 个百分点'),
    ]
    for a,fragment in cases:check('wording regression: '+fragment,fragment in readable_value(a,cid=30236)[0])
    check('shield not equated with chain','连携' not in readable_value(cases[1][0],cid=30236)[0])
    check('known value with inferred association stays inferred',confidence({'numeric_evidence':'确认','association_evidence':'推断'})=='inferred')
    result={'passed':True,'checks':len(checks),'rows':expected_rows,'answers':expected_answers,'snapshot':catalog['meta']['snapshot']}
    report_dir=fresh_output('projects/reader/reports/review','preview-verification')
    (report_dir/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
