"""R1 source-only repair verification against the frozen pilot JSON files."""
import argparse
import collections
import copy
import json
from pathlib import Path

from card_page import validate
from card_page_data import Inputs,SAMPLES


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def pointer(doc,path):
    for token in path.lstrip('/').split('/'):
        token=token.replace('~1','/').replace('~0','~')
        doc=doc[int(token)] if isinstance(doc,list) else doc[token]
    return doc


def differences(before,after,path=''):
    if isinstance(before,dict) and isinstance(after,dict):
        out=[]
        for key in sorted(before.keys()|after.keys()):
            part=path+'/'+str(key)
            if key not in before or key not in after:out.append(part)
            else:out+=differences(before[key],after[key],part)
        return out
    if isinstance(before,list) and isinstance(after,list) and len(before)==len(after):
        return [p for i,(a,b) in enumerate(zip(before,after)) for p in differences(a,b,path+'/'+str(i))]
    return [] if before==after else [path]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--before',type=Path,required=True)
    args=p.parse_args();root=args.input_root.resolve();out=args.output.resolve();before=args.before.resolve()
    cards={cid:read(out/str(cid)/'card.json') for cid in SAMPLES}
    diffs={};unchanged=[]
    for cid,card in cards.items():
        old=read(before/(str(cid)+'.json'));changes=differences(old,card)
        # No changed path may escape a provenance object, including levels/conditions/values.
        assert all('source' in path.split('/') or 'new_source' in path.split('/') for path in changes),(cid,changes)
        assert old['coverage']==card['coverage']
        diffs[str(cid)]=changes
        if not changes:unchanged.append(cid)
        validate(card,(out/str(cid)/'index.html').read_text(encoding='utf-8'))
    gaps=read(root/'output/character_skills/review/r1_20261019_card_pages/source_gaps.json')
    docs={};resolved=[]
    for gap in gaps['occurrences']:
        source=pointer(cards[gap['cid']],gap['location'])
        path=root/source['original_file']
        assert path.is_file(),(gap,path)
        if path not in docs:docs[path]=read(path)
        raw=pointer(docs[path],source['json_pointer'])
        assert isinstance(raw,dict)
        if gap.get('table')=='bosspattern':assert raw['patternid']==gap['record_id']
        if gap.get('table')=='bossskill':assert raw['skillid']==gap['record_id']
        if gap.get('table')=='job_ability':assert gap['record_id'] in raw['cids']
        resolved.append(dict(cid=gap['cid'],location=gap['location'],table=gap.get('table'),record_id=gap.get('record_id'),
                             source_key=source['source_key'],original_file=source['original_file'],json_pointer=source['json_pointer']))
    actual=[]
    for cid,card in cards.items():
        for group in card['groups']:
            for skill in group['skills']:
                for e in skill['record_evidence']:
                    if e['layer']=='CACHE' and e['table'] in ('bosspattern','bossskill','job_ability'):
                        source=e['source'];path=root/source['original_file']
                        if path not in docs:docs[path]=read(path)
                        assert pointer(docs[path],source['json_pointer'])==e['raw_record']
                        actual.append((cid,e['table'],e['record_id'],source['json_pointer']))
    unique=sorted(set(actual));counts=collections.Counter(x[1] for x in unique)
    assert counts==dict(bosspattern=8,bossskill=25,job_ability=3),counts
    totals={k:sum(c['coverage'][k] for c in cards.values()) for k in ('N_all','A','B','C','original_A')}
    assert totals==dict(N_all=387,A=185,B=0,C=202,original_A=165)
    # Targeted ambiguity/absence boundaries: fixtures are in-memory, never published locators.
    fixture=object.__new__(Inputs);fixture.root=root;fixture.decoded=root/'output/cache_full_20261015_v3/decoded'
    real=read(fixture.decoded/'jobabilityinfo.data5.json.raw');row=next(r for r in real['job_ability'] if 30236 in r.get('cids',[]))
    fake=copy.deepcopy(row);fake['text']='DIFFERENT RECORD WITH THE SAME CID'
    fixture.raw_docs={'jobabilityinfo':{'job_ability':[fake,row]}}
    entry=dict(table='job_ability',reference_id=30236,layer='CACHE',record=row,source={})
    selected=fixture.precise_source(entry)
    assert selected['json_pointer']=='/job_ability/1'
    fixture.raw_docs={'jobabilityinfo':{'job_ability':[row,copy.deepcopy(row)]}}
    ambiguous=fixture.precise_source(entry);assert ambiguous['json_pointer'] is None and ambiguous['source_resolution'].startswith('UNKNOWN')
    fixture.decoded=root/'work/character_skills_card_pages/r1_source_fix/nonexistent_decoded_fixture'
    missing=fixture.precise_source(entry);assert missing['json_pointer'] is None and missing['source_resolution']=='UNKNOWN_MISSING_DECODED_FILE'
    report=dict(status='IMPLEMENTATION_R1_SOURCE_ONLY_FIX_PENDING_INDEPENDENT_RECHECK',
                all_card_non_source_content_unchanged=True,all_11_html_json_consistent=True,totals_unchanged=totals,
                baseline_101_and_all_field_values_conditions_levels_unchanged=True,
                source_gaps_closed=len(resolved),source_gaps_unique=len(gaps['unique_references']),
                real_references_verified=len(unique),real_reference_counts=dict(counts),
                changed_cards=[int(cid) for cid,items in diffs.items() if items],unchanged_cards=unchanged,
                changed_source_attribute_paths=diffs,resolved_gap_occurrences=resolved,
                class_boundary_fixtures=dict(full_record_match_not_first=True,exact_duplicate_ambiguity_is_unknown=True,missing_file_is_unknown=True),
                examples=[r for r in resolved if r['location'] in ('/groups/0/skills/0/source','/groups/5/skills/0/source')])
    (out/'source_fix_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k in ('source_gaps_closed','source_gaps_unique','real_references_verified','real_reference_counts','changed_cards','totals_unchanged')},ensure_ascii=True))


if __name__=='__main__':main()
