"""Verify a completed full reader against current source rows and the ledger.

Only a new validation receipt is written. This does not build or translate anything.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path
from rerun_output import require_new_files, review_output, write_new_text
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit

from branch_reading import condition_context
from presentation import confidence, TECHNICAL
from translation_bridge import issues, numbers, Translator


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'), parse_constant=reject_constant)


def reject_constant(value):
    raise ValueError('Non-standard JSON number: ' + value)


def same(a, b):
    """Retain null, booleans and number types rather than Python's 0 == False."""
    return json.dumps(a, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(b, sort_keys=True, ensure_ascii=False, allow_nan=False)


def payload(path, variable, cid=None):
    text = path.read_text(encoding='utf-8-sig')
    if cid is None:
        pattern = r'\s*window\.' + re.escape(variable) + r'\s*=\s*'
    else:
        pattern = r'\s*window\.CC_DETAILS\s*=\s*window\.CC_DETAILS\s*\|\|\s*\{\}\s*;\s*window\.CC_DETAILS\[\s*' + re.escape(json.dumps(str(cid))) + r'\s*\]\s*=\s*'
    match = re.match(pattern, text)
    if not match:
        raise ValueError('Unexpected local data-script format')
    value, end = json.JSONDecoder(parse_constant=reject_constant).raw_decode(text, match.end())
    if text[end:].strip() != ';':
        raise ValueError('Unexpected content after JSON payload')
    return value


# Execute the actual output app with two pending rows. Hidden <details> text
# does not count as visible, so this checks the display contract, not keywords.
PENDING_JS = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class El {
 constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.attrs={};this.classList={add(){},remove(){}};}
 append(...items){this.children.push(...items);}
 prepend(...items){this.children.unshift(...items);}
 replaceChildren(...items){this.children=items;this.textContent='';}
 addEventListener(){} setAttribute(k,v){this.attrs[k]=v;}
 remove(){} focus(){} scrollIntoView(){}
}
const main=new El('main'),footer=new El('footer');
const scan=(el,id)=>el.id===id?el:el.children.map(c=>typeof c==='object'?scan(c,id):null).find(Boolean);
function visible(el){return el.textContent+el.children.filter(c=>el.tag!=='details'||el.open||c.tag==='summary').map(c=>typeof c==='object'?visible(c):c).join('');}
const row=(id,jp)=>({id,original:jp,textZh:'中文待核对',translationStatus:'pending',effects:[],unboundAnswers:[]});
const window={CC_CATALOG:{meta:{detailMode:'per-card'},cards:[{cid:1,name:'Verification fixture',counts:{}}]},
 CC_DETAILS:{'1':{groups:[{label:'技能',skills:[{name:'测试',conditions:[{conditionRowId:'condition',conditionTitle:'强化条件'}],rows:[row('normal','NORMAL_JP_MARKER'),row('condition','CONDITION_JP_MARKER')]}]}]}},
 setTimeout,clearTimeout,scrollTo(){},addEventListener(){},matchMedia:()=>({matches:true})};
const document={head:new El('head'),createElement:t=>new El(t),createTextNode:t=>({textContent:t,children:[]}),getElementById:id=>id==='main'?main:scan(main,id),querySelector:()=>footer};
const path=require('path'),ctx={window};
for(const file of ['branches.js','inline.js','levels.js'])vm.runInNewContext(fs.readFileSync(path.join(path.dirname(process.argv[1]),file),'utf8'),ctx);
for(const key of ['CC_BRANCHES','CC_INLINE','CC_LEVELS'])if(ctx[key])window[key]=ctx[key];
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{window,document,location:{hash:'#card=1'},URLSearchParams,Date,Promise,Map,Set,Number,String,Array,JSON,requestAnimationFrame:f=>f(),CustomEvent:class{}});
setImmediate(()=>{const s=visible(main);assert(s.includes('中文待核对'));assert(s.includes('NORMAL_JP_MARKER'));assert(s.includes('CONDITION_JP_MARKER'));console.log('pending original visible in normal and promoted condition rows');});
"""


def verify(root, out):
    counts = Counter()
    failure_counts = Counter()
    failures = []
    media = {}
    translation_status = Counter()

    def check(ok, kind, location='', detail=None):
        counts['checks'] += 1
        if ok:
            return
        failure_counts[kind] += 1
        if len(failures) < 300:
            failures.append({'check': kind, 'location': str(location), 'detail': detail})

    def media_ref(ref, location):
        if not ref:
            return
        counts['mediaReferences'] += 1
        parsed = urlsplit(str(ref))
        if parsed.scheme or parsed.netloc:
            check(False, 'media_must_be_local', location, ref)
            return
        path = (out / unquote(parsed.path)).resolve()
        check(path.is_file(), 'media_file_exists', location, ref)
        if path.is_file():
            media[str(path)] = path.stat().st_size

    base = read_path(root / 'output/character_skills', root=root)
    source_pages = base / 'pages'
    receipt = read(out / 'build_receipt.json')
    semantic_path=Path(__file__).parent/'semantic_sentences.json'
    semantic_translator=Translator(root) if semantic_path.exists() else None
    metrics = read(base / 'effect_ledger/metrics.json')
    check(same(receipt['snapshot'], metrics['snapshot']), 'current_snapshot_matches_receipt')
    rule_hash = sha256((base / 'profiles/rules.json').read_bytes()).hexdigest()[:16]
    check(rule_hash == metrics['snapshot']['rules_json_sha256_16'], 'current_rules_match_receipt')
    catalog = payload(out / 'data/catalog.js', 'CC_CATALOG')
    cards = catalog['cards']
    ids = [str(c['cid']) for c in cards]
    sources = {p.parent.name: p for p in source_pages.glob('*/card.json') if p.parent.name.isdigit()}
    check(len(ids) == len(set(ids)) == len(sources) == 2236, 'all_2236_unique_cards')
    check(set(ids) == set(sources), 'all_current_source_cards_listed')
    check(catalog.get('meta', {}).get('detailMode') == 'per-card', 'per_card_detail_contract')
    check(catalog.get('meta', {}).get('snapshot') == metrics['snapshot']['snapshot_id'], 'catalog_snapshot')
    check(set(map(str, receipt['detailCards'])) == set(ids), 'receipt_detail_cards')
    check({p.stem for p in (out / 'data/cards').glob('*.js')} == set(ids), 'detail_files_match_catalog')

    ledger_rows = defaultdict(list)
    per_card = defaultdict(lambda: {'description': Counter(), 'effect': Counter()})
    with (base / 'effect_ledger/ledger.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            entry = json.loads(line, parse_constant=reject_constant)
            cid = str(entry['cid'])
            snapshot = entry.get('snapshot_id') or entry.get('input_snapshot', {}).get('snapshot_id')
            check(snapshot == metrics['snapshot']['snapshot_id'], 'ledger_snapshot', cid)
            if entry['record_type'] == 'description':
                per_card[cid]['description'][entry['ledger_row_status']] += 1
            else:
                per_card[cid]['effect'][entry['status']] += 1
                ledger_rows[entry['description_ref']].append(entry)

    for card in cards:
        cid = str(card['cid'])
        counts['cards'] += 1
        media_ref(card.get('icon'), cid + '/icon')
        d, e = per_card[cid]['description'], per_card[cid]['effect']
        expected_counts = {'answer': e['has_answer'], 'unresolved': e['unresolved'], 'complete': d['完整'], 'partial': d['部分'], 'unparsed': d['未解析'], 'review': d['拆分待核查'], 'descriptions': sum(d.values())}
        check(same(card.get('counts'), expected_counts), 'catalog_counts_match_ledger_not_unbound', cid)
        check(bool(card.get('hasDetail') or card.get('prototype')), 'card_detail_available', cid)
        try:
            raw = sources[cid].read_bytes()
            original = json.loads(raw, parse_constant=reject_constant)
            detail = payload(out / f'data/cards/{cid}.js', 'CC_DETAILS', cid)
        except Exception as error:
            check(False, 'read_card_payload', cid, repr(error))
            continue
        check(sha256(raw).hexdigest() == receipt['sourceHashes'].get(cid), 'source_hash_matches_build', cid)
        check(str(detail.get('cid')) == cid, 'detail_cid', cid)
        media_ref(detail.get('art'), cid + '/card')
        source_groups = [g for g in original['groups'] if any(s['rows'] for s in g['skills'])]
        output_groups = detail.get('groups', [])
        check([g['group'] for g in source_groups] == [g.get('id') for g in output_groups], 'group_boundaries', cid)
        seen_row_ids = set()
        for source_group, output_group in zip(source_groups, output_groups):
            original_skills = [s for s in source_group['skills'] if s['rows']]
            output_skills = output_group.get('skills', [])
            check(len(original_skills) == len(output_skills), 'skill_boundaries', cid + '/' + source_group['group'])
            for source_skill, output_skill in zip(original_skills, output_skills):
                source_rows, output_rows = source_skill['rows'], output_skill.get('rows', [])
                check([r['row_id'] for r in source_rows] == [r.get('id') for r in output_rows], 'all_rows_in_original_order', cid)
                contexts = condition_context(source_skill).get('conditions', [])
                shown_contexts = output_skill.get('conditions', [])
                if not shown_contexts and output_skill.get('conditionRowId'):
                    shown_contexts = [{key: value for key, value in output_skill.items() if key.startswith('condition')}]
                check(same(shown_contexts, contexts), 'condition_rows_and_explicit_scope_preserved', cid)
                counts['conditionContexts'] += len(shown_contexts)
                for context in shown_contexts:
                    check(context.get('conditionRowId') in {r['row_id'] for r in source_rows}, 'condition_stays_in_skill', cid, context.get('conditionRowId'))
                for source_row, row in zip(source_rows, output_rows):
                    rid = source_row['row_id']
                    counts['rows'] += 1
                    check(rid not in seen_row_ids, 'unique_row_id', rid)
                    seen_row_ids.add(rid)
                    check(row.get('original') == source_row['japanese'], 'japanese_verbatim', rid)
                    status = row.get('translationStatus')
                    translation_status[str(status)] += 1
                    check(status in ('reviewed', 'template', 'pending'), 'translation_status_declared', rid)
                    if semantic_translator:check(status=='reviewed','all_rows_semantically_reviewed',rid)
                    if status != 'pending':
                        problems = issues(source_row['japanese'], row.get('textZh', ''))
                        if semantic_translator:
                            approved=semantic_translator.translate(source_row['japanese'])
                            check(row.get('textZh')==approved['textZh'], 'matches_reviewed_sentence',rid)
                            check(row.get('translationNote','')==approved.get('translationNote',''),'source_ambiguity_note_preserved',rid)
                            check(same(row.get('semanticReview'),approved['semanticReview']), 'semantic_review_provenance',rid)
                            check(source_row['japanese'].count('【')==row['textZh'].count('【'),'embedded_skill_headers_preserved',rid)
                        else:check(not problems, 'sentence_translation_gate', rid, problems)
                        equal_numbers = numbers(source_row['japanese']) == numbers(row.get('textZh', ''))
                        counts['literalNumberRowsUnchanged'] += equal_numbers
                        check(equal_numbers, 'literal_number_counts_unchanged', rid)
                    else:
                        counts['literalNumberRowsDeferredPending'] += 1
                        check(bool(row.get('original')), 'pending_original_retained', rid)
                    expected_effects = ledger_rows[rid]
                    shown_effects = row.get('effects', [])
                    check([x['effect_id'] for x in expected_effects] == [x.get('id') for x in shown_effects], 'all_effects_in_ledger_order', rid)
                    used = set()
                    views = []
                    for expected_effect, shown_effect in zip(expected_effects, shown_effects):
                        check(shown_effect.get('status') == expected_effect['status'], 'effect_status_unchanged', rid)
                        expected_indices = [ref['answer_index'] for ref in expected_effect.get('answer_refs', [])]
                        shown_answers = shown_effect.get('answers', [])
                        check([a.get('source', {}).get('answerIndex') for a in shown_answers] == expected_indices, 'effect_answer_bindings_unchanged', rid)
                        used.update(expected_indices)
                        for view in shown_answers:
                            check(view.get('source', {}).get('effectId') == expected_effect['effect_id'], 'answer_effect_id', rid)
                        views.extend(shown_answers)
                    unbound = row.get('unboundAnswers', [])
                    unbound_indices = [a.get('source', {}).get('answerIndex') for a in unbound]
                    check(unbound_indices == [i for i in range(len(source_row['answers'])) if i not in used], 'unbound_exactly_unreferenced_answers', rid)
                    counts['unboundAnswers'] += len(unbound)
                    views.extend(unbound)
                    check({a.get('source', {}).get('answerIndex') for a in views} == set(range(len(source_row['answers']))), 'every_answer_index_retained', rid)
                    counts['sourceAnswers'] += len(source_row['answers'])
                    for view in views:
                        counts['answerViews'] += 1
                        evidence = view.get('source', {})
                        index = evidence.get('answerIndex')
                        valid_index = type(index) is int and 0 <= index < len(source_row['answers'])
                        check(valid_index, 'valid_answer_index', rid, index)
                        if not valid_index:
                            continue
                        answer = source_row['answers'][index]
                        check(evidence.get('rowId') == rid, 'answer_row_id', rid)
                        for key, source_key in [('raw', 'raw_value'), ('originalAnswer', 'value'), ('originalConditions', 'conditions'), ('originalConditionLabel', 'condition_label'), ('originalBinding','binding'), ('originalEffectBinding','effect_binding'), ('limitations', 'note'), ('numericEvidence', 'numeric_evidence'), ('associationEvidence', 'association_evidence'), ('evidenceScope', 'evidence_scope'), ('field', 'field_path'), ('rule', 'rule_key')]:
                            check(same(evidence.get(key), answer.get(source_key)), 'answer_source_' + key, rid, index)
                        check(same(evidence.get('allSources'), answer.get('source') or {}), 'all_sources_preserved', rid, index)
                        check(view.get('confidence') == confidence(answer), 'confidence_not_promoted', rid, index)
                        check(not TECHNICAL.search(' '.join(str(view.get(k) or '') for k in ('text', 'note', 'condition'))), 'no_technical_tokens_in_reading_layer', rid, index)
                        reading=' '.join(str(view.get(k) or '') for k in ('text','condition'))
                        check(not re.search(r'[ぁ-ゖァ-ヺ]|pattern|skilltext|hold_mana|mana_count|isCurrent|ability|句面|掩码',reading),'numeric_copy_is_readable_chinese',rid,index)
                        text=view.get('text','')
                        check('原文幅度' not in text and '换算说明待整理' not in text,'numeric_copy_complete',rid,index)
                        check(text.count('（')==text.count('）') and text.count('(')==text.count(')'),'numeric_explanation_not_truncated',rid,index)
                        rule=answer.get('rule_key') or ''
                        if rule.startswith('skilllist|28|'):
                            fields=(answer.get('binding') or {}).get('fields') or []
                            labels={'0':'通常攻击','2':'暴击','1':'必杀技','0/1':'通常攻击／必杀技'}
                            for field in fields:
                                if field.get('damage_type') not in labels:continue
                                check(labels[field['damage_type']] in text,'every_probability_mode_visible',rid,index)
                                expected=float(field['raw'])*100
                                actual=[float(n) for n in re.findall(r'([+-]?[\d.]+)(?:%|个百分点)',text)]
                                check(any(abs(n-expected)<=max(1e-5,abs(expected)*1e-5) for n in actual),'every_probability_value_visible',rid,index)
                        if rule.startswith('skilllist|67|') and '逐条累加' in str(answer.get('value')):
                            tiers=re.findall(r'(\d+)人\s*([+-][\d.]+)',answer['value'])
                            for people,amount in tiers:
                                check(f'{people}名符合条件的角色 {amount}' in text,'all_person_count_tiers_visible',rid,index)
                        if view.get('relatedDescription'):
                            check(view['relatedDescription'].get('rowId') in {r['row_id'] for r in source_rows}, 'related_condition_within_skill', rid)

    check(counts['rows'] == receipt['detailRows'] == sum(metrics['descriptions']['by_ledger_status'].values()), 'all_description_counts_match')
    check(counts['cards'] == receipt['summary']['cards'], 'all_card_counts_match')
    check(counts['sourceAnswers'] > 0, 'source_answers_checked')
    summary = {'cards': len(cards), 'withAnswer': sum(c['counts']['answer'] > 0 for c in cards), 'noAnswer': sum(c['counts']['answer'] == 0 for c in cards), 'complete': sum(c['status'] == '全部描述完整' for c in cards)}
    check(same(catalog['summary'], summary) and same(receipt['summary'], summary), 'summary_uses_ledger_effects')
    for relative in ('index.html', 'style.css', 'app.js', 'data/catalog.js'):
        check((out / relative).is_file(), 'frontend_file_exists', relative)
    index = (out / 'index.html').read_text(encoding='utf-8-sig')
    check(not re.search(r'<script[^>]+src=[\"\']data/cards\.js[\"\']', index), 'no_whole_library_detail_preload')
    node = shutil.which('node')
    js_results = {}
    if node:
        for name, command in [('syntax', [node, '--check', str(out / 'app.js')]), ('pendingOriginalVisible', [node, '-e', PENDING_JS, str(out / 'app.js')])]:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
            js_results[name] = {'passed': result.returncode == 0, 'output': (result.stdout + result.stderr).strip()[:2000]}
            check(result.returncode == 0, 'javascript_' + name, 'app.js', js_results[name]['output'])
    else:
        check(False, 'javascript_node_required', detail='Install Node.js to verify actual pending-row visibility')
    counts['uniqueMediaFiles'] = len(media)
    counts['uniqueMediaBytes'] = sum(media.values())
    return {'passed': not failure_counts, 'scope': 'all current cards; exact reviewed translation match, per-answer source/condition binding preservation, numeric display families and local media. Model sentence reviews and automated checks are separately recorded.', 'semanticReviewUnits':len(semantic_translator.semantic['units']) if semantic_translator else 0, 'snapshot': metrics['snapshot'], 'builtAt': receipt['builtAt'], 'verifiedAt': datetime.now(timezone.utc).isoformat(), 'counts': dict(counts), 'translationStatus': dict(translation_status), 'failureCounts': dict(failure_counts), 'failures': failures, 'failureDetailsTruncated': sum(failure_counts.values()) > len(failures), 'javascript': js_results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, help='Completed reader output directory')
    parser.add_argument('--report', type=Path, help='Path to a new validation receipt')
    args = parser.parse_args()
    root = args.root.resolve()
    out = read_path(args.output or root / 'output/character_skills/reader_full_20261106', root=root).resolve()
    if args.report is not None:
        target = write_path(args.report, root=root)
    elif args.output is not None:
        target = write_path(args.output / 'validation.json', root=root)
    else:
        target = review_output('full-validation') / 'validation.json'
    require_new_files(target)
    try:
        report = verify(root, out)
    except Exception as error:
        report = {'passed': False, 'verifiedAt': datetime.now(timezone.utc).isoformat(), 'fatalError': f'{type(error).__name__}: {error}'}
    write_new_text(target, json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: report[key] for key in ('passed', 'counts', 'failureCounts', 'fatalError') if key in report}, ensure_ascii=False))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
