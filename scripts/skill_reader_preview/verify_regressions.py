"""Regression cases from observed reader mistakes, independent of total counts."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path
from rerun_output import require_new_files, review_output, write_new_text
import json
from translation_bridge import Translator, issues
from verify_full import payload
from presentation import answer
from build import rows as source_rows
from branch_reading import condition_context

root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report', type=Path, help='Path to a new validation receipt')
args=parser.parse_args()
target=write_path(args.report) if args.report else review_output('regressions')/'regression_checks.json'
require_new_files(target)
out=read_path(root/'output/character_skills/reader_full_20261106',root=root)
t=Translator(root)
checks=[]
def check(name, passed):
    checks.append({'name':name,'passed':bool(passed)})
    assert passed,name

jp='戦闘不能になった際に1回耐え、HPが回復し、一定時間ダメージを受けなくなる。'
check('one survival event is not one HP',bool(issues(jp,'保留1HP，回复HP并在一定时间内不受伤害。')))
body='前方範囲内の全ての敵に大ダメージを与え、弾き飛ばす。'
a=t.translate('【共鳴必殺/連撃】'+body)
b=t.translate('【超共鳴必殺/連撃】'+body)
c=t.translate('【決戦必殺/1回のみ】'+body)
check('same prose does not share a cached skill header',a['textZh'].startswith('【共鸣必杀/') and b['textZh'].startswith('【超共鸣必杀/'))
check('one-use restriction survives header translation','仅1次' in c['textZh'] and c['translationStatus']!='pending')
if t.semantic:
    d=t.translate('【連撃】【返還】自身の攻撃力が一定時間上がる。')
    check('adjacent skill headers are not stripped twice',d['textZh'].startswith('【连击】【返还】'))
    d=t.translate('バリアは防御無視攻撃によるダメージと炎/氷属性ダメージも防ぐ。')
    check('barrier applicability does not assert complete damage immunity','也有效' in d['textZh'] and '挡下' not in d['textZh'])
check('extra critical-rate effect is rejected',bool(issues('クリティカル威力が上がる。','暴击率和暴击威力提高。')))
check('damage magnitude is not area size',bool(issues('敵に大ダメージを与える。','对敌人造成大范围伤害。')))
check('Chain lower bound is retained',bool(issues('1stChain以上で威力が上がる。','达成1stChain时威力提高。')))
card=payload(out/'data/cards/350.js','CC_DETAILS',350)
rows=[r for g in card['groups'] for s in g['skills'] for r in s['rows']]
row=next(r for r in rows if r['id']=='350-special_move-special_move-pattern0-lvorder0-f0')
answers=[a for e in row['effects'] for a in e['answers']]
normal=next(a for a in answers if a['source']['raw']==25)
enhanced=next(a for a in answers if a['source']['raw']==27.5)
check('25 refers to initial area hit','首次范围伤害' in normal['mappingNote'])
check('27.5 association remains inferred',enhanced['confidence']=='inferred' and '推测' in enhanced['mappingNote'])
linked=next(r for r in rows if r['id']==enhanced['relatedDescription']['rowId'])
check('enhancement points to its real condition','1stChain以上' in linked['original'])
skill=next(s for g in card['groups'] for s in g['skills'] if row in s['rows'])
condition=next(c for c in skill['conditions'] if c['conditionRowId']==linked['id'])
check('trailing condition keeps all five effect scopes',set(condition['conditionScope'])=={'法珠消耗','必杀威力','反响威力','回复量','我方增益'})
source350=json.loads(read_path(root/'output/character_skills/pages/350/card.json',root=root).read_bytes())
for group in source350['groups']:
    for source_skill in group['skills']:
        if any(r['japanese']=='止まっていると効果が上がる。' for r in source_skill['rows']):
            promoted={c['conditionRowId'] for c in condition_context(source_skill).get('conditions',[])}
            stop=next(r for r in source_skill['rows'] if r['japanese']=='止まっていると効果が上がる。')
            check('local standing-still clause stays beside its original effect',stop['row_id'] not in promoted)
def source_answer(cid,predicate):
    data=json.loads((root/f'output/character_skills/pages/{cid}/card.json').read_bytes())
    for r in source_rows(data):
        for a in r['answers']:
            if predicate(a):return answer(a,cid,r['japanese'])
    raise AssertionError('Regression source no longer present')

# Actual formerly misleading source families, not synthetic format snapshots.
families=json.loads(read_path(root/'output/character_skills/reader_semantic_20261107/numeric_families.json',root=root).read_bytes())
def family(fid):
    ex=next(f for f in families if f['id']==fid)['examples'][0]
    return answer(ex['answer'],int(ex['rowId'].split('-')[0]),ex['japanese'])
v=family('4b936ba7bddbdd0c')
check('person-count critical bonus keeps second tier','2名' in v['text'] and '+35.0 个百分点' in v['text'])
v=family('06a95fbcd709d350')
check('one probability answer keeps all three attack modes',all(w in v['text'] for w in ('通常攻击','暴击','必杀技','25%','100%')))
check('job-specific mana is not any mana','任意职业' not in family('08ccf5dd1096d047')['condition'])
v=family('66dea4b9172b94da')
check('backline applicability survives semicolon','后备有效' in v['condition'])
v=family('55a64802eab35930')
check('once per Chain survives semicolon','同一Chain最多触发一次' in v['condition'])
v=family('0ada98c4bd6c204e')
check('healing bonus is not direct healing amount','回复量提高 1%' in v['text'])
v=family('c8c4ddc88ddf0cf5')
check('no mana is not a one-mana threshold',v['text']=='不持有任何法珠时')
v=source_answer(20329,lambda a:a.get('quantity_kind')=='敌方/攻击力效果量百分比')
check('coordinated final decrease verb reaches first attribute','攻击力降低 25%' in v['text'])
report={'passed':True,'checks':checks}
write_new_text(target, json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(checks)}))
