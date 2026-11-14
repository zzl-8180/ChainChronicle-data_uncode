"""Assemble a complete, isolated Reader from an accepted increment and display revision."""
import argparse
from collections import Counter
from copy import deepcopy
from html import escape
from pathlib import Path
import json
import os
import re
import shutil
import stat
import tempfile

from build import dump, js, read, reference_names, require_stage, rows
from incremental_frontend import build_frontend, digest, replace_once
from incremental_sync import FORMAL, ROOT, TEMPLATE, baseline_reader, card_hashes, payload, require
from reference_copy import load_reference
from reference_sources_v2 import FROZEN_SOURCE_ROOT, OLD_ROOT, ReferenceSourceMap
from translation_bridge import Translator

FINAL5 = 'audit/final5_evidence_20261107'
DATA_SIDECARS = {'catalog.js','branch_candidates.js','branch_conditions.js','branch_assessments.js','mana_costs.js'}
FROZEN = {
    'audit/reference_pairs.json':'26288eff1f10b7547644283a00cdb90b68e19c05cddd08712133b8fd6a8e51e7',
    f'{FINAL5}/sparse_receipt.json':'aa948748b0d87eba971afa9df89634cf625b4deea3c83a277504a6463dc4cd39',
    f'{FINAL5}/random_pool_receipt.json':'a46438616c6b26aa81ebc5c47463d90d302840507f104e4290ad9f9d858ee2b5',
}


def collect_closure_inputs(root):
    paths = (root/'scripts/skill_reader_preview/rerun_output.py',
             root/'scripts/versioned_outputs.py',
             root/'work/20261113-final5-readonly-v1/fresh-process-verification.json')
    return {p: digest(p) for p in paths}


def verify_read_set(read_set):
    for p, h in read_set.items():
        require(digest(p) == h, 'Input changed during assembly: ' + str(p))


def freeze_inventory():
    paths = {TEMPLATE/p:h for p,h in FROZEN.items()}
    paths[ROOT/'projects/reference-analysis/README.md'] = '3da8f0d974de35f342513cde85b8f4760a4b7571bb140e6d267f69d5c7a2010c'
    prior = read(ROOT/'work/20261113-final5-readonly-v1/fresh-process-verification.json')
    for x in prior['receipts'].values():
        paths[Path(x['source'])] = x['source_sha256']
        for path in x['hardlink_paths']:
            paths[Path(path)] = x['sha256']
    inventory = {}
    for p,h in paths.items():
        info = p.stat()
        attributes = getattr(info,'st_file_attributes',0)
        require(digest(p)==h, 'Frozen SHA mismatch: '+str(p))
        if p.name in prior['receipts']:
            old = prior['receipts'][p.name]
            require(attributes & 1 and info.st_ino==old['file_id'] and info.st_dev==old['volume'] and
                    info.st_nlink==len(old['hardlink_paths']), 'Frozen final5 file identity changed: '+str(p))
        inventory[str(p)] = {'sha256':h,'attributes':attributes,'nlink':info.st_nlink,'fileId':info.st_ino}
    return inventory


def reviewed_conditions(folder, review_folder, base):
    mp = folder/'final_manifest.json'
    manifest = read(mp)
    checks = read(review_folder/'evidence.json')
    verdict = read(review_folder/'verdict.json')
    run = read(review_folder/'run_log.json')
    handoff = read(folder/'handoff_verification.json')
    require(manifest['snapshot']==base['snapshot']['snapshot_id'] and
            manifest['campaign']==base['snapshot']['campaign_signature'], 'Revision targets a different snapshot')
    require(verdict['verdict']=='PASS_WITH_EXPLICIT_SCOPE_LIMITS' and verdict['blocking_count']==0 and
            verdict['F01']==verdict['F02']=='CLOSED' and run['exit_code']==0 and
            len(checks['checks'])==verdict['checks_total']==verdict['checks_passed'] and
            all(x['passed'] is True for x in checks['checks']), 'Display revision has no completed independent approval')
    require(digest(mp)==handoff['final_manifest_sha256'] and
            handoff['registered_files']==len(manifest['files']), 'Revision manifest/handoff mismatch')
    bound = [mp, folder/'condition_ledger.json']
    for p in bound:
        h = checks['input_fingerprints'][(p.relative_to(ROOT)).as_posix()]['sha256']
        require(digest(p)==h, 'Independent review input differs: '+p.name)
    for rel,x in manifest['files'].items():
        p = (folder/rel).resolve()
        require(p.is_relative_to(folder) and p.stat().st_size==x['bytes'] and digest(p)==x['sha256'],
                'Revision delivery file mismatch: '+rel)
    entries = read(folder/'condition_ledger.json')
    independent = read(review_folder/'answer_ledger.json')
    by_row = {x['row_id']:x for x in independent}
    require(len(entries)==len(independent)==len(by_row)==verdict['independent_condition_rows_passed'] and
            {x['row_id'] for x in entries}==set(by_row), 'Independent condition coverage differs')
    for x in entries:
        v = by_row[x['row_id']]
        require(v['passed'] is True and v['condition_ledger_entry']==x and
                v['selected_raw_recomputed']==x['raw_conditions'], 'Independent condition proof differs: '+x['row_id'])
    return manifest, entries


def references(stage, reference_root, allowlist, read_set):
    mapping = ReferenceSourceMap.from_manifest(allowlist, reference_root)
    source_hashes = {}
    for line in allowlist.read_text(encoding='utf-8-sig').splitlines():
        item = json.loads(line)
        if item['action'] != 'REHOME':
            continue
        rel = item['path'][len(OLD_ROOT):]
        file, _ = mapping.resolve(rel)
        h = digest(file)
        require(h==item['sha256'] and file.stat().st_size==item['logical_bytes'], 'Simulated source differs: '+rel)
        source_hashes[rel] = h
        read_set[file] = h
    names = reference_names(ROOT, reference_root, allowlist)
    pairs = load_reference(reference_root, allowlist)
    extracted = load_reference.last_audit
    frozen = read(TEMPLATE/'audit/reference_pairs.json')
    require(frozen['source_root']==FROZEN_SOURCE_ROOT, 'Unexpected frozen reference root')
    refs = set()
    count = 0

    def visit(obj):
        nonlocal count
        if isinstance(obj, dict):
            for k,v in obj.items():
                if k == 'source' and isinstance(v,str) and v.startswith('cards/'):
                    visit_ref(v)
                elif k == 'sources' and isinstance(v,list):
                    for ref in v:
                        if isinstance(ref,str) and ref.startswith('cards/'):
                            visit_ref(ref)
                else:
                    visit(v)
        elif isinstance(obj,list):
            for item in obj:
                visit(item)

    def visit_ref(ref):
        nonlocal count
        f, anchor = mapping.resolve_from_root(frozen['source_root'],ref)
        require(anchor == '#'+ref.split('#',1)[1] and f.is_file(), 'Reference fragment changed')
        refs.add(ref.split('#',1)[0])
        count += 1

    for key in ('pairs','conflicts','unpaired_articles'):
        require(extracted[key]==frozen[key], 'Simulated reference extraction differs: '+key)
        visit(frozen[key])
    require(len(names)==2233 and len(pairs)==5164 and len(refs)==2231 and count==29206,
            'Reference source coverage differs')
    dump(stage/'audit/reference-extraction.json', extracted)
    return names, extracted, {'names':len(names),'uniquePairs':len(pairs),'referenceOccurrences':count,
                             'referencedPages':len(refs),'allowlistMembers':len(source_hashes),
                             'fileHashes':source_hashes}


def reproduce_chinese(stage, cids, extracted):
    # The reviewed sentence layer remains authoritative. The simulated
    # reference extraction is independently audited in references().
    translator = Translator(ROOT)
    require(translator.semantic and len(extracted['pairs'])==5164, 'Reviewed Chinese inputs are incomplete')
    statuses = Counter()
    for cid in cids:
        for row in rows(payload(stage/f'data/cards/{cid}.js')):
            translated = translator.translate(row['original'])
            require(all(row.get(k)==translated.get(k) for k in ('textZh','translationStatus','translationSource','translationNote')),
                    'Simulated source does not reproduce reviewed Chinese: '+row['id'])
            statuses[row['translationStatus']] += 1
    return dict(statuses)


def baseline_data_files(base, receipt):
    expected = {f'data/{n}' for n in DATA_SIDECARS}
    expected |= {f'data/cards/{cid}.js' for cid in receipt['sourceHashes']}
    listed = {p for p in receipt['runtimeHashes'] if p.startswith('data/')}
    require(expected==listed, 'Unexpected baseline data hash inventory')
    actual = set()
    for current, directories, files in os.walk(base/'data',followlinks=False):
        folder=Path(current)
        for item in (folder,*(folder/d for d in directories),*(folder/f for f in files)):
            info=item.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,
                    'Reparse point in Reader baseline: '+str(item))
        require(folder in (base/'data',base/'data/cards') and
                all(folder/d==base/'data/cards' for d in directories), 'Unexpected Reader data directory')
        actual.update((folder/f).relative_to(base).as_posix() for f in files)
    require(actual==expected, f'Baseline data set differs; extra={sorted(actual-expected)}, missing={sorted(expected-actual)}')
    return sorted(expected)


def compact_condition(entry):
    necessary = entry['display_necessary_conditions']
    kind, = entry['kinds']
    if kind == 'limit':
        match = re.match(r'(本分支已使用次数小于\d+次)（', necessary[-1])
        require(match, 'Unknown usage-limit wording')
        return match[1] + '（重置与选档待确认）'
    if kind == 'terrain':
        return necessary[-1].split('（按原文',1)[0]
    if kind == 'mana':
        return '；'.join(entry['mana_known'] + ['计数对象、扣费时点及选档待确认'])
    require(kind=='chain', 'Unknown reviewed condition kind')
    return necessary[-1].split('（适用玩家Chain路径',1)[0]


def patch_card(card, entries):
    lookup = {r['id']:r for r in rows(card)}
    applied = []
    for x in entries:
        row = lookup[x['row_id']]
        effect, = [e for e in row['effects'] if e['id']==x['effect_id']]
        selected = x['selected']
        matches = []
        for a in effect['answers']:
            s = a['source']
            for binding in (s.get('originalBinding') or {}).values():
                if isinstance(binding,dict) and binding.get('selected')==selected:
                    matches.append(a)
        a, = matches
        s = a['source']
        require(a.get('syncFormal') and x['formal_answer_unchanged'] and not x['runtime_verified'] and
                (s['rowId'],s['effectId'],s['allSources'],s['raw'],s['field'],s['rule'])==
                (row['id'],effect['id'],x['source'],selected['raw_value'],'/'+selected['field'],selected['rule_key']) and
                (x['record_id'],x['pattern_id'],x['layer'],x['raw_conditions'])==
                (selected['record_id'],selected['pattern_id'],selected['source']['layer'],selected['parent_conditions_raw']),
                'Display target identity mismatch: '+row['id'])
        prior = {'condition':a['condition'],'displayBranch':deepcopy(a['displayBranch'])}
        label = compact_condition(x)
        a['condition'] = '；'.join(x['display_necessary_conditions'])
        a['displayBranch']['conditionLabel'] = label
        # The established condition wording may explicitly state what is unknown.
        # Keep the binding and color; the label describes evidence, not a resolved selector.
        a['source']['reviewedDisplayCondition'] = x
        applied.append({'cid':x['cid'],'rowId':row['id'],'effectId':effect['id'],
                        'answerIndex':s['answerIndex'],'before':prior,'label':label})
    return applied


def keep_reviewed_conditions_distinct(stage):
    """Keep an R01 necessary condition attached even beside an equal old value."""
    inline = stage/'inline.js'
    text = inline.read_text(encoding='utf-8')
    text = replace_once(text, 'const existing=values.find(v=>v.text===text && v.color===color);',
                        """const reviewed=answer.source?.reviewedDisplayCondition;
      const existing=values.find(v=>v.text===text && v.color===color &&
        (reviewed || v.answer.source?.reviewedDisplayCondition
          ? v.answer.displayBranch?.conditionLabel===answer.displayBranch?.conditionLabel
          : true));""")
    inline.write_text(text,encoding='utf-8')
    index=stage/'index.html'
    index.write_text(re.sub(r'(?<=src="inline.js\?v=)[0-9a-f]{12}',digest(inline)[:12],
                            index.read_text(encoding='utf-8')),encoding='utf-8')


def run(args):
    out = args.output.absolute()
    require_stage(ROOT,out)
    require(not out.exists(), 'Use a fresh isolated output')
    base = args.base_reader.resolve()
    receipt = baseline_reader(base)
    data_files = baseline_data_files(base,receipt)
    require('displayRevision' not in receipt, 'Use the accepted pre-revision Reader as baseline')
    metrics = FORMAL/'effect_ledger/metrics.json'
    rules = FORMAL/'profiles/rules.json'
    ledger = FORMAL/'effect_ledger/ledger.jsonl'
    scripts = Path(__file__).resolve().parent
    code = ('assemble_reviewed_reader.py','build.py','reference_copy.py','reference_sources_v2.py',
            'incremental_sync.py','incremental_frontend.py','translation_bridge.py',
            'presentation.py','branch_reading.py','wording.py','semantic_sentences.json',
            'reviewed_sentences.json','extra_reviewed_sentences.json','audited_sentence_fixes.json')
    read_set = {p:digest(p) for p in (metrics,rules,ledger,FORMAL/'pages/_batch/campaign_latest.json',
                                    args.source_map_manifest,base/'incremental_receipt.json',
                                    *(scripts/n for n in code),
                                    *(TEMPLATE/n for n in ('index.html','app.js','inline.js')),
                                    *(base/n for n in ('style.css','branches.js','levels.js')))}
    read_set.update(collect_closure_inputs(ROOT))
    require(read(metrics)['snapshot']==receipt['snapshot'] and
            read_set[rules][:16]==receipt['snapshot']['rules_json_sha256_16'], 'Current mainline has changed')
    for p,h in receipt['inputs'].items():
        path=Path(p).resolve()
        require(path.is_relative_to(ROOT) and digest(path)==h, 'Accepted baseline input changed: '+p)
        read_set[path]=h
    paths, hashes = card_hashes(FORMAL,None,receipt['snapshot']['campaign_signature'])
    require(hashes==receipt['sourceHashes'], 'Current cards differ from the accepted Reader baseline')
    frozen_before = freeze_inventory()
    revision, entries = reviewed_conditions(args.revision.resolve(),args.review.resolve(),receipt)
    for name in ('final_manifest.json','condition_ledger.json','handoff_verification.json'):
        path=args.revision/name
        read_set[path]=digest(path)
    for name,item in revision['files'].items():
        read_set[args.revision/name]=item['sha256']
    for name in ('verdict.json','evidence.json','answer_ledger.json','run_log.json'):
        path=args.review/name
        read_set[path]=digest(path)
    out.parent.mkdir(parents=True,exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=out.name+'-stage-',dir=out.parent))
    (stage/'data/cards').mkdir(parents=True)
    for rel in data_files:
        shutil.copy2(base/rel,stage/rel)
        require(digest(stage/rel)==receipt['runtimeHashes'][rel], 'Baseline data changed while copying: '+rel)
    for n in ('style.css','branches.js','levels.js'):
        shutil.copy2(base/n,stage/n)
    (stage/'audit').mkdir()
    names, extracted, reference_proof = references(stage,args.reference_root,args.source_map_manifest,read_set)
    reference_proof['reproducedChineseRows'] = reproduce_chinese(stage,hashes,extracted)
    reference_proof['translationAuthority'] = 'reviewed semantic sentences; simulated extraction independently compared to frozen pairs'
    catalog = payload(base/'data/catalog.js')
    require({str(c['cid']) for c in catalog['cards']}==set(hashes), 'Catalog card coverage differs')
    for c in catalog['cards']:
        zh = names.get(c['cid'],'')
        title, _, name = zh.rpartition(' ')
        require((c['nameZh'],c['titleZh'])==(name or zh or c['name'],title),
                'Reference name does not reproduce accepted catalog: '+str(c['cid']))
        c.update(nameZh=name or zh or c['name'],titleZh=title)
    catalog['meta']['displayRevision'] = revision['cycle']
    catalog['meta']['acceptedCycle'] = revision['cycle']+' 模拟来源候选'
    js(stage/'data/catalog.js','CC_CATALOG',catalog)
    groups = {}
    for x in entries:
        groups.setdefault(str(x['cid']),[]).append(x)
    applied = []
    for cid, group in groups.items():
        card = payload(base/f'data/cards/{cid}.js')
        applied.extend(patch_card(card,group))
        raw=json.dumps(card,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('</','<\\/')
        (stage/f'data/cards/{cid}.js').write_text(f'window.CC_DETAILS=window.CC_DETAILS||{{}};window.CC_DETAILS["{cid}"]={raw};\n',encoding='utf-8')
    require(len(applied)==len(entries), 'Revision did not apply once per answer')
    for rel,h in FROZEN.items():
        dest=stage/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(TEMPLATE/rel,dest)
        require(digest(dest)==h and dest.stat().st_nlink==1, 'Evidence copy is not independent: '+rel)
        if rel.startswith(FINAL5):
            if not getattr(dest.stat(),'st_file_attributes',0) & 1:
                dest.chmod(stat.S_IREAD)
            require(getattr(dest.stat(),'st_file_attributes',0)&1, 'Candidate final5 evidence not read-only')
    build_frontend(stage,TEMPLATE,escape(revision['cycle'])+' 模拟来源候选')
    keep_reviewed_conditions_distinct(stage)
    links = ' '.join(f'<a href="index.html#card={cid}">{cid}</a>' for cid in sorted(groups,key=int))
    (stage/'pilot-report.html').write_text(
        f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        f'<title>{escape(revision["cycle"])} 条件修订</title><link rel="stylesheet" href="style.css">'
        f'<main id="main"><a href="index.html">返回角色目录</a><h1>{escape(revision["cycle"])} 条件修订</h1>'
        f'<p>{len(entries)} 条已审条件覆盖 {len(groups)} 张卡。</p><p>{links}</p></main></html>',encoding='utf-8')
    verify_read_set(read_set)
    for rel in data_files:
        require(digest(base/rel)==receipt['runtimeHashes'][rel], 'Reader baseline changed during assembly: '+rel)
    for cid,p in paths.items():
        require(digest(p)==hashes[cid], 'Mainline card changed during assembly: '+cid)
    frozen_after = freeze_inventory()
    require(frozen_before==frozen_after, 'Frozen evidence changed during assembly')
    verify_read_set(read_set)  # freeze_inventory rereads the upstream receipt
    result = {**receipt,'displayRevision':revision['cycle'],'baseReaderReceiptSHA256':digest(base/'incremental_receipt.json'),
              'conditionManifestSHA256':digest(args.revision/'final_manifest.json'),
              'conditionLedgerSHA256':digest(args.revision/'condition_ledger.json'),
              'conditionReviewVerdictSHA256':digest(args.review/'verdict.json'),
              'referenceSimulation':reference_proof,'conditionApplications':applied,
              'conditionKinds':dict(Counter(k for x in entries for k in x['kinds'])),
              'inputs':{str(p.resolve()):h for p,h in read_set.items()},
              'baseDataHashes':{p:receipt['runtimeHashes'][p] for p in data_files},
              'frozenBefore':frozen_before,'frozenAfter':frozen_after,
              'runtimeHashes':{p.relative_to(stage).as_posix():digest(p) for p in stage.rglob('*') if p.is_file()}}
    dump(stage/'incremental_receipt.json',result)
    stage.rename(out)
    print(json.dumps({'status':'PASS_SIMULATION_ONLY','stage':str(out),'snapshot':receipt['snapshot']['snapshot_id'],
                      'displayRevision':revision['cycle'],'cards':len(paths),'conditionAnswers':len(applied),
                      'names':len(names),'pairs':reference_proof['uniquePairs'],'referencedPages':reference_proof['referencedPages']},
                     ensure_ascii=False))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    for option in ('output','base-reader','revision','review','reference-root','source-map-manifest'):
        cli.add_argument('--'+option,type=Path,required=True)
    run(cli.parse_args())
