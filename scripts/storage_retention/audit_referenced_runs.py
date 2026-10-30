"""Read-only audit of the original 149 referenced runs; never deletes/archives."""
from collections import Counter, defaultdict
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zlib

import inventory as I

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/storage_retention/referenced_runs_20261024'
SOURCE=ROOT/'output/storage_retention/20261023/inventory_v3/runs.json'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def pointers():
    batch=ROOT/'output/character_skills/pages/_batch'
    paths=list(batch.glob('*/latest.json'))+[batch/'campaign_latest.json']
    return {p.relative_to(ROOT).as_posix():dict(sha256=sha(p),content=I.load(p)) for p in paths}

def main():
    OUT.mkdir(exist_ok=False)
    rows=[r for r in I.load(SOURCE) if r['action']=='ARCHIVE_REVIEW']
    assert len(rows)==149
    before=pointers()
    token_map=defaultdict(list)
    for row in rows:
        for token,kind in [(row['run_id'],'run_id'),(row['run_id'].split('-')[-1],'run_suffix'),
                           (row['signature'][:8],'campaign_signature_prefix')]:
            token_map[token].append((row['path'],kind))
    tokens=re.compile('|'.join(re.escape(t) for t in sorted(token_map,key=len,reverse=True)))
    scan=subprocess.run(['rg','--files','-g','*.py','-g','*.md','scripts','docs','work',
        'output/character_skills/review'],cwd=ROOT,capture_output=True,check=True)
    candidates={ROOT/p for p in scan.stdout.decode('utf-8').splitlines()}
    candidates|={ROOT/p for r in rows for p in r['references']}
    candidates|={ROOT/p for p in ('AGENTS.md','HANDOFF.md','STATUS.md','README.md','output/character_skills/pages/README.md')}
    # Add small independent review JSON, including new evidence since inventory v3.
    issues=[]
    for p,info in I.files_under(ROOT/'output/character_skills/review',issues):
        if p.suffix in ('.json','.jsonl') and info.st_size<=2*1024**2:candidates.add(p)
    refs=[];sources={};payload_sources={}
    for path in sorted(candidates):
        rel=path.relative_to(ROOT).as_posix()
        if '/storage_retention/' in rel or 'retention-cleanup' in rel or 'run-retention' in rel or 'referenced-runs-audit' in rel:
            continue  # Our inventories quote every ID, not an independent dependency.
        try:content=path.read_text(encoding='utf-8-sig')
        except (OSError,UnicodeError) as e:
            issues.append(dict(path=rel,error=str(e)));continue
        if not tokens.search(content):continue
        sources[rel]=dict(sha256=sha(path),bytes=path.stat().st_size)
        lines=content.splitlines()
        payload_context=bool(re.search(r'transactions|backup/card\.json|backup.*index\.html',content))
        found=set()
        for n,line in enumerate(lines,1):
            matches=list(tokens.finditer(line))
            for match in matches:
                for target,kind in token_map[match.group(0)]:
                    refs.append(dict(run_path=target,source=rel,line=n,match_kind=kind,
                       token=match.group(0),text=line[:1800],payload_terms_in_source=payload_context))
                    found.add(target)
        if payload_context:
            payload_sources[rel]=dict(runs=sorted(found),
                payload_lines=[dict(line=n,text=t[:1800]) for n,t in enumerate(lines,1)
                               if re.search(r'transactions|backup|旧状态|旧快照',t,re.I)])
    I.save(OUT/'reference_occurrences.json',refs)
    I.save(OUT/'reference_sources.json',sources)
    I.save(OUT/'payload_reference_sources.json',payload_sources)
    print(f'References indexed: {len(refs)} occurrences in {len(sources)} files',flush=True)
    results=[]
    for i,row in enumerate(rows,1):
        run=ROOT/row['path'];counts=Counter();backup=defaultdict(dict);metadata={};errors=[]
        for file,info in I.files_under(run,errors):
            rel=file.relative_to(run);parts=rel.parts
            payload=len(parts)==4 and parts[0]=='transactions' and parts[1].isdigit() and parts[2]=='backup' and parts[3] in ('card.json','index.html')
            counts['bytes']+=info.st_size;counts['files']+=1
            if payload:
                counts['payload_bytes']+=info.st_size;counts['payload_files']+=1
                backup[parts[1]][parts[3]+'_size']=info.st_size
            elif len(parts)==4 and parts[2]=='backup' and parts[3]=='receipt.json':
                receipt=I.load(file)
                backup[parts[1]].update(signature=receipt.get('signature'),declared_files=receipt.get('files',{}))
            if len(parts)==1:metadata[rel.as_posix()]=sha(file)
        sigs=Counter(v.get('signature') or 'NO_RECEIPT' for v in backup.values() if 'card.json_size' in v)
        declared=[dict(cid=cid,**v) for cid,v in sorted(backup.items(),key=lambda x:int(x[0]))]
        manifest_hash=hashlib.sha256(json.dumps(declared,sort_keys=True).encode()).hexdigest()
        current=I.load(run/'cohort_report.json')
        result=dict(**row,current_bytes=counts['bytes'],current_files=counts['files'],
            payload_bytes=counts['payload_bytes'],payload_files=counts['payload_files'],
            retained_bytes=counts['bytes']-counts['payload_bytes'],backup_signatures=dict(sigs),
            backup_cards=sum('card.json_size' in v for v in backup.values()),
            backup_pairs=sum('card.json_size' in v and 'index.html_size' in v for v in backup.values()),
            declared_backup_manifest_sha256=manifest_hash,top_metadata_sha256=metadata,
            current_report_success=not current.get('failed') and not current.get('unresolved_latest_failures'),
            measurement_matches_original=(counts['bytes']==row['bytes']),scan_errors=errors)
        results.append(result);issues+=errors
        if i%10==0 or i==len(rows):print(f'Measured {i}/149 referenced runs',flush=True)
    I.save(OUT/'measurements.json',results)
    I.save(OUT/'scan_summary.json',dict(created_at=datetime.now(timezone.utc).isoformat(),
        scope='Original 149 ARCHIVE_REVIEW runs only; no deletions, moves, archive or production writes',
        total_bytes=sum(r['current_bytes'] for r in results),payload_bytes=sum(r['payload_bytes'] for r in results),
        run_count=len(results),reference_files=len(sources),reference_occurrences=len(refs),
        pointers_before=before,pointers_after=pointers(),issues=issues,
        limitations='Logical size; receipt-declared backup identities, no full-content rehash/compression trial. '
                    'Sources: all md/py in scripts/docs/work/review plus original references, review JSON/JSONL <=2MiB. '
                    'Search includes full run IDs, unique 8-char suffixes and 8-char campaign prefixes; dynamic references need manual mapping.'))
    print(json.dumps(dict(runs=len(results),bytes=sum(r['current_bytes'] for r in results),
          payload_bytes=sum(r['payload_bytes'] for r in results),issues=len(issues))),flush=True)

def report():
    rows=I.load(OUT/'measurements.json');refs=I.load(OUT/'reference_occurrences.json')
    summary=I.load(OUT/'scan_summary.json')
    assert len(rows)==149 and not summary['issues']
    assert not (OUT/'decisions.json').exists(), 'Do not overwrite reviewed decisions'
    rules=[
        dict(id='ge60_polish',suffixes=['313e0c28'],prefixes=[],reason='polish 复验明确逐卡核对该 run 的 backup；old_cards 仅是 JSON 副本，不能替代整套旧 HTML/回执。',evidence=['output/character_skills/review/ge60_20261019_deepseek/RECHECK2.md','work/ge60_deepseek_recheck2/recheck2.py']),
        dict(id='40to59_recheck',suffixes=['5ac350e9','4085a36d'],prefixes=[],reason='40to59 复验直接用这两个新 run 的旧备份，核对 324 卡零变化；保留实际比较输入。',evidence=['output/character_skills/review/40to59_20261020_deepseek/RECHECK.md','output/character_skills/review/40to59_20261020_deepseek/checks_recheck/recheck_zero_change_backup.json']),
        dict(id='20to39_recheck',suffixes=['aa629f69','20d940d0','40959198'],prefixes=[],reason='20to39 复验直接读取 NEW 三个 run 的 backup，核对 760 卡；OLD 的队列引用不等于读取 OLD 的备份。',evidence=['output/character_skills/review/20to39_20261020_deepseek/RECHECK.md','work/20to39_deepseek_review/recheck_core.py','work/20to39_deepseek_review/recheck_zero_change.py']),
        dict(id='pilot1017',suffixes=['4f2abd71','22d2c01b'],prefixes=['950c3495'],reason='1017 历史对账脚本硬编码读取这些事务 backup/card.json，包含不同修复轮，不以最终报告代替比较输入。',evidence=['work/20261020-pilot1017/compare_full_rows.py','work/20261020-pilot1017/compare_fix_full.py','work/20261020-pilot1017/compare_final_round.py','work/review_inference1017_deepseek/recheck.py']),
        dict(id='layout_before',suffixes=[],prefixes=['7da4ab64'],reason='首次版式迁移四 cohort 的 backup 是迁移前页面；审查以其逐卡锚定 old_card_json。保留旧 HTML 与 JSON 的成套关系。',evidence=['output/character_skills/review/layout_migration_20261020_deepseek/REPORT.md']),
        dict(id='rectify_before',suffixes=[],prefixes=['c4bce1bb'],reason='整改边界对账实际读取这四个 run 的 backup；文档所称 bc726985 状态存放在新 run 的 backup 中，不能误归档 bc726985 自己的更早 backup。',evidence=['work/character_skills_rectify_summary_20261021/diff_card_rebuild.py','work/deepseek_review_20261021/verify_boundary.py','output/character_skills/review/rectify_20261021_deepseek/REPORT.md']),
        dict(id='b8_microfix',suffixes=[],prefixes=['8cfbbd91','0d646a89'],reason='批8微修脚本与独立 RECHECK 分别使用这两轮事务旧状态；保留可恢复的对比输入，不能仅留统计摘要。',evidence=['work/character_skills_b8_crit2012/microfix_old_new_diff.py','output/character_skills/review/inference_b8_crit2012_20261021_deepseek/RECHECK.md']),
        dict(id='b10_fix',suffixes=[],prefixes=['3cb73f2f'],reason='批10修复对账读取本轮部分 cohort 的备份；保守保留整轮四 cohort，避免按单个脚本片段拆散历史对比状态。',evidence=['work/character_skills_b10_rv_fix/compare_fix.py','docs/tasks/20261022-character-skills-inference-b10-sa2003.md']),
        dict(id='b10_transient',suffixes=[],prefixes=['ab364b87'],reason='复验专门指出最终 run 的 backup 是 transient wrong-family 中间态，不是真正 RECHECK 比较基线。应连同该限制归档，防止将其错误恢复为验收态。',evidence=['output/character_skills/review/inference_b10_sa2003_20261022_deepseek/checks/recheck2_summary.json','work/review_b10_sa2003_deepseek/write_recheck2_summary.py']),
    ]
    active_evidence=['docs/tasks/character-skills-progress.md','docs/tasks/20261023-character-skills-rectification-r2r3.md','docs/tasks/20261023-character-skills-r2r3-root-fix.md','scripts/storage_retention/pins.json']
    closure='docs/tasks/character-skills-progress.md'
    phase_proofs=[
        ('20261021T144024','output/character_skills/review/inference_b9_debuff_20261021_deepseek/RECHECK.md'),
        ('20261021T184733','output/character_skills/review/inference_b10_sa2003_20261022_deepseek/RECHECK2.md'),
        ('20261022T005650','output/character_skills/review/inference_b12_1095ext_20261022_deepseek/REPORT.md'),
        ('20261022T031647','output/character_skills/review/inference_b13_apkext_20261022_deepseek/recheck_20261022/REPORT.md'),
        ('20261022T041520','output/character_skills/review/inference_b14_apkext_20261022_deepseek/REPORT.md'),
        ('20261022T200708','output/character_skills/review/goal_rectification_20261023_deepseek/recheck2_20261023/REPORT.md'),
        ('20261022T233519','output/character_skills/review/inference_b17_p0finale_20261023_deepseek/recheck_20261023/REPORT.md'),
    ]
    by_run=defaultdict(list)
    for ref in refs:by_run[ref['run_path']].append(ref)
    decision=[];proofs={}
    for row in rows:
        matches=[rule for rule in rules if row['signature'][:8] in rule['prefixes'] or row['run_id'].split('-')[-1] in rule['suffixes']]
        phase=next((p for cutoff,p in phase_proofs if row['run_id']<cutoff),None)
        if row['signature'][:8] in {'112cbd12','0b66de96','2306af95'}:
            category='KEEP_FULL';reason='当前 R1 保护与 R2/R3 后续整改仍引用这组版本。保留现存完整事务旧文件；run 签名不等于 backup 版本，已钉的 replay_final 也不能直接替代这些不同旧状态。'
            evidence=active_evidence;rule_id='active_r1_r2_r3'
        elif 'NO_RECEIPT' in row['backup_signatures']:
            category='ARCHIVE_FIRST';reason='早期 backup 中存在无 receipt 的旧页面，无法用标准旧签名锚定其来源；先保留原字节和 before.json 归档，不直接抛弃。'
            evidence=[row['path']+'/cohort_report.json'];rule_id='legacy_no_receipt'
        elif matches:
            assert len(matches)==1
            rule=matches[0];category='ARCHIVE_FIRST';reason=rule['reason'];evidence=rule['evidence'];rule_id=rule['id']
        else:
            assert phase, row['path']
            category='METADATA_ONLY';reason='引用用于报告、签名、队列、版本或历史说明；未发现需要这个 run 自身 backup 的实际读者。后续阶段已闭合，且历史实物基线另行保留；允许放弃恢复这份更早页面的能力，原记录不删。'
            evidence=[closure,phase]+row['references'];rule_id='historical_metadata_reference'
        assert row['measurement_matches_original'] and row['current_report_success']
        for source in evidence:
            if source not in proofs:proofs[source]=sha(ROOT/source)
        decision.append(dict(path=row['path'],cohort=row['cohort'],run_id=row['run_id'],category=category,
            reason=reason,rule_id=rule_id,new_signature=row['signature'],backup_signatures=row['backup_signatures'],
            current_bytes=row['current_bytes'],payload_bytes=row['payload_bytes'],records_retained_bytes=row['retained_bytes'],
            payload_files=row['payload_files'],backup_cards=row['backup_cards'],backup_pairs=row['backup_pairs'],
            cleanup_candidate_bytes=row['payload_bytes'] if category=='METADATA_ONLY' else 0,
            off_volume_archive_candidate_bytes=row['payload_bytes'] if category=='ARCHIVE_FIRST' else 0,
            evidence=evidence,reference_source_count=len({x['source'] for x in by_run[row['path']]}),
            reference_kinds=sorted({x['match_kind'] for x in by_run[row['path']]}),
            scope='Only transactions/<cid>/backup/card.json and index.html; preserve all other files',
            execution_authorized=False))
    # Explicit source-role review prevents false positives from OLD constants/comments.
    exceptions=[
        dict(suffix='9857e9b9',source='work/20to39_deepseek_review/recheck_core.py',reason='OLD references audit_queue at line 114; backup loop uses NEW. This old run has zero backup payload anyway.'),
        dict(suffix='bc726985',source='work/character_skills_rectify_summary_20261021/diff_card_rebuild.py',reason='Comment names the pre-fix state; RUNS actually reads four c4bce1bb runs, all ARCHIVE_FIRST.'),
        dict(suffix='bc726985',source='work/deepseek_review_20261021/verify_boundary.py',reason='Only historical state in docstring; actual backup reader resolves run_id from current card receipts. Preserve current/new run, not an unrelated earlier backup.'),
        dict(suffix='770f54b4',source='work/ge60_deepseek_recheck2/recheck2.py',reason='PREV only assigned and never used; actual backup reads RUN 313e0c28 (ARCHIVE_FIRST).'),
    ]
    for e in exceptions:proofs[e['source']]=sha(ROOT/e['source'])
    groups={}
    for category in ('KEEP_FULL','ARCHIVE_FIRST','METADATA_ONLY'):
        selected=[d for d in decision if d['category']==category]
        groups[category]=dict(runs=len(selected),payload_bytes=sum(d['payload_bytes'] for d in selected),
            total_bytes=sum(d['current_bytes'] for d in selected),payload_files=sum(d['payload_files'] for d in selected),
            nonempty_runs=sum(d['payload_bytes']>0 for d in selected))
    assert sum(g['runs'] for g in groups.values())==149
    assert sum(g['payload_bytes'] for g in groups.values())==summary['payload_bytes']
    # Compression only in memory, never an archive. A deterministic small sample per run.
    samples=[]
    for d in decision:
        if d['category']!='ARCHIVE_FIRST' or not d['payload_bytes']:continue
        trans=ROOT/d['path']/'transactions'
        folders=sorted([p for p in trans.iterdir() if p.is_dir() and
            any((p/'backup'/name).is_file() for name in ('card.json','index.html'))],key=lambda p:p.name)
        chosen={0,len(folders)//2,len(folders)-1};raw=compressed=count=0
        for i in chosen:
            for name in ('card.json','index.html'):
                file=folders[i]/'backup'/name
                if not file.is_file():continue
                z=zlib.compressobj(level=6,wbits=-15)
                with file.open('rb') as stream:
                    for block in iter(lambda:stream.read(1024*1024),b''):
                        raw+=len(block);compressed+=len(z.compress(block))
                compressed+=len(z.flush());count+=1
        assert raw
        samples.append(dict(run_path=d['path'],sample_files=count,sample_raw_bytes=raw,
            sample_deflate_bytes=compressed,estimated_payload_deflate_bytes=round(d['payload_bytes']*compressed/raw)))
    I.save(OUT/'decisions.json',decision)
    fields=['category','cohort','run_id','path','payload_bytes','records_retained_bytes','cleanup_candidate_bytes',
        'off_volume_archive_candidate_bytes','reason','new_signature','backup_signatures','evidence','reference_source_count','execution_authorized']
    I.csv_write(OUT/'decisions.csv',decision,fields)
    for category in groups:I.csv_write(OUT/(category.lower()+'.csv'),[d for d in decision if d['category']==category],fields)
    I.save(OUT/'manual_reference_review.json',dict(rules=rules,exceptions=exceptions,evidence_sha256=proofs))
    I.save(OUT/'compression_sample.json',dict(method='3 transaction folders per archival run (first/middle/last sorted), up to 6 files; raw DEFLATE level 6 in memory; not a validated archive or a statistical confidence interval.',runs=samples,
        sample_files=sum(x['sample_files'] for x in samples),sample_raw_bytes=sum(x['sample_raw_bytes'] for x in samples),
        estimated_payload_deflate_bytes=sum(x['estimated_payload_deflate_bytes'] for x in samples)))
    I.save(OUT/'classification_summary.json',dict(created_at=datetime.now(timezone.utc).isoformat(),groups=groups,
        records_retained_bytes=sum(d['records_retained_bytes'] for d in decision),
        direct_cleanup_candidate_bytes=groups['METADATA_ONLY']['payload_bytes'],
        additional_off_volume_archive_bytes=groups['ARCHIVE_FIRST']['payload_bytes'],
        additional_same_volume_deflate_saving_estimate=groups['ARCHIVE_FIRST']['payload_bytes']-sum(x['estimated_payload_deflate_bytes'] for x in samples),
        deleted_files=0,moved_files=0,archives_created=0,production_writes=0,
        pointers_unchanged=summary['pointers_before']==summary['pointers_after'],
        all_149_sizes_equal_previous_inventory=all(r['measurement_matches_original'] for r in rows)))
    print(json.dumps(dict(groups=groups,estimated_payload_deflate_bytes=sum(x['estimated_payload_deflate_bytes'] for x in samples)),indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',action='store_true',help='Classify the existing read-only scan; no archive or cleanup')
    args=parser.parse_args()
    if args.report:report()
    else:main()
