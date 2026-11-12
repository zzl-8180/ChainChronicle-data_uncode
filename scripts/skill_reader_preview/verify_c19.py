"""Read-only C19/source/baseline checks; writes only this batch's validation."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from rerun_output import require_new_files, write_new_text, write_path
import re
import subprocess

from migrate_c19 import HERE, REPORT, FROZEN, card_rows, read, validate_receipt, canonical
from verify_effect_labels import validate_review, check_containers, BATCHES, R01_BATCH


def payload(path):
    text = path.read_text(encoding='utf-8-sig')
    return json.loads(text.split(']=',1)[1].strip().removesuffix(';'))


def view_rows(card):
    return {r['id']:r for g in card['groups'] for s in g['skills'] for r in s['rows']}


def views(row):
    return {a['source']['answerIndex']:a for a in [a for e in row['effects'] for a in e['answers']] + row['unboundAnswers']}


def without_fingerprint(value):
    value = deepcopy(value)
    if isinstance(value,dict):
        binding = (value.get('originalBinding') or {}).get('g1_b1_binding')
        if binding and 'page_sha256' in binding:
            binding['page_sha256'] = 'AUDITED_C19_FINGERPRINT_DRIFT'
    return value


INLINE_CHECK = r"""
const fs=require('fs'),path=require('path');
const [out,reportPath]=process.argv.slice(1);
const {plan,compact}=require(path.join(out,'inline.js'));
const report=JSON.parse(fs.readFileSync(reportPath,'utf8'));
const result={targetRows:0,answers:0,inlined:0,failures:[]};
for(const target of report.batch_results.flatMap(b=>b.rows)) {
 const text=fs.readFileSync(path.join(out,'data/cards',target.cid+'.js'),'utf8');
 const card=JSON.parse(text.split(']=')[1].trim().replace(/;$/,''));
 const row=card.groups.flatMap(g=>g.skills.flatMap(s=>s.rows)).find(r=>r.id===target.row_id);
 const p=plan(row); result.targetRows++;
 for(let i=target.before.answers.length;i<target.after.answers.length;i++) {
  result.answers++;
  const entry=p.inserts.find(e=>(e.answers||[e.answer]).some(a=>a.source.answerIndex===i));
  if(!entry){result.failures.push({rowId:row.id,index:i,reason:'new answer not in actual output inline.plan inserts'});continue;}
  const answer=(entry.answers||[entry.answer]).find(a=>a.source.answerIndex===i);
  const originalTokens=answer.text.match(/[\d.]+/g),shownTokens=compact(answer,entry.effect.label).match(/[\d.]+/g);
  if(JSON.stringify(originalTokens)!==JSON.stringify(shownTokens)) result.failures.push({rowId:row.id,index:i,reason:'numeric tokens lost during compact'});
  else result.inlined++;
 }
}
console.log(JSON.stringify(result));
"""


def write_result(result, dest):
    write_new_text(dest, json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'counts':result['counts'],
                     'oldAnswerViewChanges':len(result.get('oldAnswerViewChanges',[])),
                     'failures':result['failures'],'receipt':str(dest)},ensure_ascii=False))
    return result


def verify(root,out,baseline,audit_dir='audit/c19_closeout_20261107',label_review=None,
           label_baseline=None,label_batch=R01_BATCH):
    dest = write_path(out/audit_dir/'c19_validation.json')
    require_new_files(dest)
    counts,failures,changes = Counter(),[],[]
    def check(ok,kind,where='',detail=None):
        counts['checks'] += 1
        if not ok:
            counts['failed'] += 1
            if len(failures)<100:failures.append({'check':kind,'location':where,'detail':detail})
    label_fixes, label_proof = {}, None
    if label_review:
        try:
            if label_baseline is None:
                raise ValueError('label_review_missing_baseline: specify the independent pre-repair reader')
            label_proof = validate_review(out,label_baseline,
                root/'output/character_skills/effect_ledger/ledger.jsonl',label_review,label_batch)
            label_fixes = {c['effectId']:c for c in label_proof['changes']}
        except (ValueError, KeyError, TypeError, AssertionError, OSError) as error:
            check(False,'label_review_independent_proof',str(label_review),str(error))
            return write_result({'status':'FAIL','generatedAt':datetime.now(timezone.utc).isoformat(),
                'counts':dict(counts),'failures':failures,'oldAnswerViewChanges':[],
                'scope':'Label repair rejected before C19 acceptance; local proof is required'},dest)
    container_counts = Counter()
    used_label_fixes = set()
    receipt = read(out/'build_receipt.json')
    migration = out/receipt['semanticMigration']['path']
    check(sha256(migration.read_bytes()).hexdigest()==receipt['semanticMigration']['sha256'],'migration_receipt_hash')
    validated = validate_receipt(root,migration,read(HERE/'semantic_sentences.json'))
    check(receipt['sourceHashes']==validated['sourceHashes'],'whole_card_current_source_guard')
    report = read(root/REPORT)
    targets = {r['row_id']:r for b in report['batch_results'] for r in b['rows']}
    catalog = json.loads((out/'data/catalog.js').read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
    check(catalog['meta'].get('acceptedCycle')=='C19','visible_catalog_cycle')
    decoded = {}
    for cid in receipt['sourceHashes']:
        current = card_rows(read(root/f'output/character_skills/pages/{cid}/card.json'))
        old = view_rows(payload(baseline/f'data/cards/{cid}.js'))
        new = view_rows(payload(out/f'data/cards/{cid}.js'))
        check(list(old)==list(new)==list(current),'original_row_order_and_ids',cid)
        counts['cards']+=1
        for rid,row in new.items():
            counts['rows']+=1
            try:
                check_containers(row,container_counts)
            except ValueError as error:
                check(False,'answer_container_or_status_removal',rid,str(error))
            before = old[rid]
            for field in ('original','textZh','translationStatus','semanticReview','translationNote'):
                check(canonical(before.get(field))==canonical(row.get(field)),'unchanged_reviewed_'+field,rid)
            check([e['id'] for e in before['effects']]==[e['id'] for e in row['effects']],'effect_boundaries',rid)
            for old_effect,new_effect in zip(before['effects'],row['effects']):
                fix=label_fixes.get(new_effect['id'])
                repaired=bool(fix and fix['rowId']==rid and old_effect['label']==fix['old'] and new_effect['label']==fix['new']
                    and old_effect.get('pendingText')==fix['oldPendingText'] and new_effect.get('pendingText')==fix['newPendingText'])
                check(old_effect['label']==new_effect['label'] or repaired,'effect_labels_or_audited_span_repair',new_effect['id'])
                if repaired: used_label_fixes.add(new_effect['id'])
            aold,anew = views(before),views(row)
            check(set(anew)==set(range(len(current[rid]['answers']))),'all_formal_answer_indices',rid)
            for idx,a in aold.items():
                b = anew[idx]
                counts['oldAnswers']+=1
                check(canonical(without_fingerprint(a['source']))==canonical(without_fingerprint(b['source'])),'old_answer_full_source_preserved',f'{rid}:{idx}')
                check(a['confidence']==b['confidence'],'old_answer_confidence_preserved',f'{rid}:{idx}')
                if canonical(a)!=canonical(b):
                    changed = [k for k in a.keys()|b.keys() if canonical(a.get(k))!=canonical(b.get(k))]
                    changes.append({'cid':int(cid),'rowId':rid,'index':idx,'fields':changed,
                                    'before':{k:a.get(k) for k in changed if k!='source'},
                                    'after':{k:b.get(k) for k in changed if k!='source'},
                                    'sourceChange':'Only audited binding.g1_b1_binding.page_sha256' if 'source' in changed else None})
                check(a['text']==b['text'],'old_answer_display_value_preserved',f'{rid}:{idx}')
            if rid not in targets:
                check(set(aold)==set(anew),'no_non_C19_answer_additions',rid)
                continue
            target = targets[rid]
            counts['targetRows']+=1
            for effect in target['unresolved_effects']:
                shown = next((e for e in row['effects'] if e['id']==effect['effect_id']),None)
                check(shown is not None and shown['status']=='unresolved' and not shown['answers'] and bool(shown['pendingText']),'same_sentence_unknown_retained',effect['effect_id'])
                counts['sameSentenceUnknownEffects']+=1
            for idx in range(len(target['before']['answers']),len(target['after']['answers'])):
                a,b=current[rid]['answers'][idx],anew[idx]
                counts['newAnswers']+=1
                counts[a['rule_key']]+=1
                check(b['confidence']=='inferred','new_association_stays_inferred',f'{rid}:{idx}')
                check(b['source']['raw']==a['raw_value'] and b['source']['rule']==a['rule_key'],'new_raw_and_rule',f'{rid}:{idx}')
                check(b['source'].get('playerScope')==a['player_scope'] and b['source'].get('allSources')==a['source'],'new_object_conditions_and_source',f'{rid}:{idx}')
                check(b['text'].startswith('自身'),'new_object_is_self',f'{rid}:{idx}')
                # Independent formula/units check: p6 is above the 1.5 base,
                # p5 is probability points; multipliers use their own baselines.
                rule,raw=a['rule_key'],a['raw_value']
                expected = raw-1.5 if rule.endswith('/param6') else (raw*100 if rule.endswith('/param5') else abs(raw-1)*100)
                numbers=[float(n) for n in re.findall(r'\d+(?:\.\d+)?',b['text'])]
                check(any(abs(n-abs(expected))<0.0001 for n in numbers),'new_display_amount',f'{rid}:{idx}',b['text'])
                unit = '系数' if rule.endswith('/param6') else ('百分点' if rule.endswith('/param5') else '%')
                check(unit in b['text'],'new_display_unit',f'{rid}:{idx}',b['text'])
                if rule.endswith('/param3'):
                    check('受到的伤害' in b['text'] and '降低' in b['text'] and '固定防御' not in b['text'],'proportional_damage_reduction',f'{rid}:{idx}')
                src=a['source'];file=root/src['original_file']
                if str(file) not in decoded:decoded[str(file)]=read(file)
                record=decoded[str(file)]
                for part in src['json_pointer'].strip('/').split('/'):
                    record=record[int(part)] if isinstance(record,list) else record[part]
                value=record
                for part in a['field_path'].strip('/').split('/'):
                    value=value[int(part)] if isinstance(value,list) else value[part]
                check(type(value)==type(raw) and value==raw,'new_value_matches_original_decoded_record',f'{rid}:{idx}')
    check(counts['targetRows']==133 and counts['newAnswers']==407 and counts['sameSentenceUnknownEffects']==45,'C19_denominators')
    check(counts['oldAnswers']==35404 and len(changes)==16 and len({x['cid'] for x in changes})==9,'old_answers_and_fingerprint_denominators')
    process=subprocess.run(['node','-e',INLINE_CHECK,str(out),str(root/REPORT)],capture_output=True,text=True,encoding='utf-8',check=True)
    inline=json.loads(process.stdout)
    check(inline['answers']==407 and inline['inlined']==407 and not inline['failures'],'actual_output_inline_planner_preserves_all_407','inline.js',inline['failures'][:12])
    check(used_label_fixes==set(label_fixes),'all_span_label_repairs_consumed')
    counts['auditedLabelRepairs']=len(used_label_fixes)
    result={'status':'PASS' if not failures else 'FAIL','generatedAt':datetime.now(timezone.utc).isoformat(),
            'counts':dict(counts),'failures':failures,'oldAnswerViewChanges':changes,'inline':inline,
            'answerContainerConsistency':dict(container_counts),
            'labelProof':None if label_proof is None else {k:label_proof[k] for k in ('schema','batch','counts','consistency','ledgerSHA256','fixesSHA256')},
            'scope':'All 2236 cards, unchanged Chinese and old answer sources/confidence/values, 407 new source-backed values, units and self objects; 45 same-sentence unknowns. Does not claim runtime or browser validation.'}
    return write_result(result,dest)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=HERE.parents[1])
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--baseline',type=Path,help='Retained C18 reader; defaults to the pre-publication formal reader')
    ap.add_argument('--audit-dir',default='audit/c19_closeout_20261107')
    ap.add_argument('--label-review',type=Path,help='Verified span-local label repair receipt; original IDs and answer guards remain enforced')
    ap.add_argument('--label-baseline',type=Path,help='Independent pre-repair reader required with --label-review (R01: pre-R01 C19, not C18)')
    ap.add_argument('--label-batch',choices=BATCHES,default=R01_BATCH)
    args=ap.parse_args()
    result=verify(args.root.resolve(),args.output.resolve(),(args.baseline or args.root/FROZEN).resolve(),args.audit_dir,
                  args.label_review.resolve() if args.label_review else None,
                  args.label_baseline.resolve() if args.label_baseline else None,args.label_batch)
    raise SystemExit(0 if result['status']=='PASS' else 1)
