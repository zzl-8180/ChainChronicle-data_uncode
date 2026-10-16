"""Read-only ID/name lookup over current cache and the generated field dictionary.

Run from project root. Unexplained source fields are explicitly returned, never
silently defaulted. Ordinary/Boss namespaces must be selected separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
from ordinary_effect_dictionary import context_3000,context_99

ROOT=Path('output/card_comparison_cid30236')
SOURCE=Path('output/cache_full_20261015_v3/records.jsonl')


def lookup(table,record_id=None,name=None):
    source_bytes=SOURCE.read_bytes()
    view_bytes=(ROOT/'verified_parameter_views.json').read_bytes()
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(source_bytes).hexdigest()==manifest['source_sha256'], 'Current source differs from generated dictionary'
    assert hashlib.sha256(view_bytes).hexdigest()==manifest['payloads']['verified_parameter_views.json'], 'Generated views differ from manifest'
    records=[json.loads(s) for s in source_bytes.decode('utf-8').splitlines()]
    id_field='skillid'
    candidates=[r for r in records if r['table']==table]
    if record_id is not None:
        candidates=[r for r in candidates if r['raw'].get(id_field)==record_id]
        if not candidates and table=='skilllist':
            # The existing fallback proof is per-ID; do not combine fields.
            proof=json.loads((ROOT/'skill_power/trace.json').read_text(encoding='utf-8'))
            candidates=[r for r in proof['source_records'] if r['layer']=='APK_AB' and r['raw'].get(id_field)==record_id]
    else:
        needle=name.casefold()
        candidates=[r for r in candidates if needle in '\n'.join(str(r['raw'].get(k) or '') for k in ('name','sname','text','sinfo')).casefold()]
    views=json.loads(view_bytes)
    results=[]
    for record in candidates:
        matched=[v for v in views if v['record_key']==record['record_key']]
        explained={v['field_path'][1:] for v in matched}
        raw=record['raw']
        unexplained={k:v for k,v in raw.items() if k.startswith(('param','iParam','str','flag','skillparam','skillflag')) and k not in explained}
        target_conditions={v['field_path']:{k:v[k] for k in ('raw_value','display_value','converted_value','json_pointer','evidence')}
                           for v in matched if (v['effect_type']==1017 and v['field_path'] in ('/param0','/iParam0')) or (v['effect_type'] in (7,1008) and v['field_path']=='/param0')}
        context=({99:context_99,3000:context_3000}[raw['ability']](record) if table=='skilllist' and raw.get('ability') in (99,3000)
                 else next((v['trigger_context'] for v in matched if v.get('trigger_context')),None))
        results.append(dict(record=record,explained_fields=matched,unexplained_present_fields=unexplained,
                            target_conditions=target_conditions,
                            trigger_context=context,
                            status='HAS_SCOPED_EXPLANATIONS' if matched else 'RAW_FOUND_CONTEXT_ONLY' if context else 'RAW_FOUND_NO_SCOPED_EXPLANATION',
                            limits='只返回已入生成字典的限定解释；其余原值保留，未证明当前装载或完整战斗效果。'))
    return dict(table=table,query_id=record_id,query_name=name,matches=len(results),results=results,
                status='FOUND' if results else 'NOT_FOUND_IN_CURRENT_CACHE_OR_DOCUMENTED_FALLBACK')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table',choices=('skilllist','bossskill'),default='skilllist')
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--id',type=int)
    group.add_argument('--name')
    args=parser.parse_args()
    print(json.dumps(lookup(args.table,args.id,args.name),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
