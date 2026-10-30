"""Task-scoped cleanup: only the user-authorized v3 candidates, narrowed by audit.

No recursive deletion. Retain all metadata and unique evidence. Prepare first;
execute requires the exact plan SHA-256 and rechecks paths, pointers and files.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

import inventory as I

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'output/storage_retention/cleanup_20261023'
ORIGINAL = ROOT/'output/storage_retention/20261023/inventory_v3'
PAGES = ROOT/'output/character_skills/pages'
PHASES = [
    ('b670cd42', 'output/character_skills/review/inference_b9_debuff_20261021_deepseek/RECHECK.md', '页面及推断批1–9；当前看板明确这些批次审查闭合'),
    ('ab364b87', 'output/character_skills/review/inference_b10_sa2003_20261022_deepseek/RECHECK2.md', '批10最终复验，RV-01..06闭合'),
    ('d65ef732', 'output/character_skills/review/inference_b12_1095ext_20261022_deepseek/REPORT.md', '批12通过并明确取代批11过期页面'),
    ('8f6732fa', 'output/character_skills/review/inference_b13_apkext_20261022_deepseek/recheck_20261022/REPORT.md', '批13修复轮通过，High关闭；含修复前中间轮'),
    ('546a170b', 'output/character_skills/review/inference_b14_apkext_20261022_deepseek/REPORT.md', '批14通过，未发现需要重建的缺陷'),
    ('91d15160', 'output/character_skills/review/goal_rectification_20261023_deepseek/recheck2_20261023/REPORT.md', '目标整改第二轮复验通过，R1/R2/R3/R5按报告范围闭合'),
    ('598ec4f8', 'output/character_skills/review/inference_b17_p0finale_20261023_deepseek/recheck_20261023/REPORT.md', '批17修复终态可接受，数据/零回退/签名独立通过'),
]
REVIEW_GOAL = 'output/character_skills/review/goal_rectification_20261023_deepseek/recheck2_20261023/REPORT.md'
REVIEW_B17 = 'output/character_skills/review/inference_b17_p0finale_20261023_deepseek/recheck_20261023/REPORT.md'
REVIEW_CACHE = 'output/20261016-reproducibility-audit/review/review_20261016_recheck/README.md'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safe_file(root, relative, group):
    """Verify lexical/resolved boundaries AND every ancestor before unlink."""
    root = root.resolve()
    rel = Path(relative)
    grp = Path(group)
    if rel.is_absolute() or grp.is_absolute() or '..' in rel.parts or '..' in grp.parts:
        raise ValueError('Absolute/traversing manifest path rejected')
    path = root/rel
    allowed = root/grp
    if not path.is_relative_to(allowed) or path == allowed or not allowed.is_relative_to(root) or allowed == root:
        raise ValueError('Not a file strictly inside the named candidate')
    for part in [path, *path.parents]:
        if part == root:
            break
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f'Link/reparse point rejected: {part}')
    if path.resolve(strict=True) != path or not path.is_file():
        raise ValueError(f'Resolved path changed/not a regular file: {path}')
    return path


def payload_kind(group, relative, kind):
    """Narrow filename allowlists. Everything else is evidence to retain."""
    parts = Path(relative).relative_to(Path(group)).parts
    name = parts[-1]
    if kind == 'run':
        return len(parts)==4 and parts[0]=='transactions' and parts[1].isdigit() and parts[2]=='backup' and name in ('card.json','index.html')
    if kind in ('pages','union'):
        return name in ('card.json','index.html') and len(parts)>1 and (parts[-2].isdigit() or
               (parts[-2] in ('backup','new') and len(parts)>2 and parts[-3].isdigit()))
    if kind == 'ledger':
        return len(parts)==1 and name in ('ledger.jsonl','backlog.json')
    if kind == 'cache':
        return parts == ('records.jsonl',) or (parts[0]=='decoded' and name.endswith(('.json','.raw')))
    if kind == 'statistical':
        return (len(parts)==5 and parts[0]=='claude_cc_site_pages' and parts[1]=='cards'
                and parts[3:] == ('data','card.json')) or parts == ('site_diff','out','site_parsed.json')
    return False


def protected_snapshot(all_runs, deleting_groups):
    result = {}
    # All run metadata (including the 149 excluded runs), current pointers and
    # current receipts are immutable guards; payload paths are disjoint by construction.
    paths = list((PAGES/'_batch').glob('*/latest.json')) + list((PAGES/'_batch').glob('*/plan_latest.json'))
    paths += [PAGES/'_batch/campaign_latest.json']
    for row in all_runs:
        paths += [p for p in (ROOT/row['path']).glob('*') if p.is_file()]
    paths += list(PAGES.glob('[0-9]*/receipt.json'))
    pin = ROOT/'work/character_skills_recheck_rectification/replay_final/pages'
    paths += list(pin.glob('[0-9]*/receipt.json')) + [pin/'_batch/campaign_latest.json']
    for path in paths:
        result[path.relative_to(ROOT).as_posix()] = sha(path)
    return result


def work_decision(row):
    path = row['path']
    if path.startswith('work/review_r2r3_root_fix_deepseek/'):
        return 'KEEP', None, [], '当前R3 sentence残余整改仍进行中，不能确认该复验目录无后续依赖'
    if '/character_skills_parallel_cohort/' in path:
        return 'CLEAN', 'pages', ['docs/tasks/20261023-character-skills-parallel-cohort.md',
                 'work/character_skills_parallel_cohort/equivalence_serial_vs_par2.json',
                 'work/character_skills_parallel_cohort/equivalence_serial_vs_par4.json'], '并行任务已完成，两个4472文件等价检查通过；报告/比较器/回执原地保留'
    if '/character_skills_b17_impl/' in path:
        return 'CLEAN', 'ledger' if 'ledger_replay' in path else 'pages', [REVIEW_B17], '批17定向复验闭合；复跑数据可移除，独立审查和校验回执保留'
    if '/character_skills_goal_rectification/' in path or '/review_goal_rectification_deepseek/' in path:
        return 'CLEAN', 'union' if path.endswith('/union_build') else 'ledger', [REVIEW_GOAL], '目标整改第二轮闭合；旧迭代/复跑已被终态取代，保留差异、metrics、README和独立报告'
    if path.startswith(('work/review_20261016/', 'work/review2_20261016/')):
        return 'CLEAN', 'cache', [REVIEW_CACHE, 'docs/tasks/20261016-reproducibility-audit.md'], '77文件复跑独立复审通过；原始v3数据保留，decode_report/progress/tables保留'
    if '/reference_analysis_20261023/' in path:
        return 'CLEAN', 'statistical', ['docs/tasks/20261023-reference-analysis.md',
                'output/reference_analysis/claude_cc_site_pages_20261023/late_bundle/isolated_replay.json'], '任务已完成，统计复跑byte_equal/semantic_equal均true；仅删除输入镜像，保留脚本和参数表结果'
    return 'KEEP', None, [], '没有足够闭合证据'


def prepare():
    plan_path = BASE/'cleanup_plan.json'
    if plan_path.exists():
        raise FileExistsError('Do not overwrite a prepared plan')
    original_runs = I.load(ORIGINAL/'runs.json')
    original_work = I.load(ORIGINAL/'work.json')
    runs = [r for r in original_runs if r['action']=='CANDIDATE_AFTER_REVIEW']
    work = [r for r in original_work if r['action']=='REVIEW_REPLAY']
    assert len(runs)==119 and len(work)==18
    fresh_runs = {r['path']:r for r in I.load(BASE/'preflight_inventory/runs.json')}
    fresh_work = {r['path']:r for r in I.load(BASE/'preflight_inventory/work.json')}
    phases = []
    for prefix, evidence, reason in PHASES:
        rows = [r for r in original_runs if (r.get('signature') or '').startswith(prefix) and r['complete_success']]
        assert {r['cohort'] for r in rows} == set(I.COHORTS), prefix
        assert (ROOT/evidence).is_file()
        phases.append(dict(signature=rows[0]['signature'], cutoff=max(r['run_id'] for r in rows),
                           evidence=evidence, reason=reason,
                           retained_reports=[r['path']+'/cohort_report.json' for r in rows]))
    decisions = []
    for row in runs:
        current = fresh_runs[row['path']]
        assert current['action']=='CANDIDATE_AFTER_REVIEW' and current['bytes']==row['bytes']
        report = I.load(ROOT/row['path']/'cohort_report.json')
        phase = next((p for p in phases if row['run_id']<=p['cutoff']), None)
        success = not report['failed'] and not report['unresolved_latest_failures'] and report['requested_completed']==report['requested']
        clean = phase is not None and success
        decisions.append(dict(path=row['path'], kind='run', action='CLEAN' if clean else 'KEEP',
             evidence=[phase['evidence']] if clean else [],
             closure=phase if clean else None,
             reason=('已被同批次/后续闭合终态取代；中间run不冒充独立审定。'+phase['reason']) if clean
             else '近期R1/R2/R3整改仍有后续活动依赖可能，保守保留', expected_original_bytes=row['bytes']))
    for row in work:
        action, kind, evidence, reason = work_decision(row)
        if fresh_work[row['path']]['action']=='KEEP':
            action='KEEP'; reason='新盘点发现保护/活动任务标记'
        decisions.append(dict(path=row['path'], kind=kind, action=action, evidence=evidence, reason=reason,
                              expected_original_bytes=row['bytes']))
    # Curated closure checks are recorded; never promote merely from the string PASS.
    replay = I.load(ROOT/'output/reference_analysis/claude_cc_site_pages_20261023/late_bundle/isolated_replay.json')
    assert replay['byte_equal'] and replay['semantic_equal'] and replay['exit_code']==0
    for name in ('equivalence_serial_vs_par2.json','equivalence_serial_vs_par4.json'):
        result = I.load(ROOT/'work/character_skills_parallel_cohort'/name)
        assert result.get('equivalent') is True
    all_files = []
    evidence_hashes = {}
    skips = []
    for index, decision in enumerate(decisions):
        if decision['action']!='CLEAN':
            continue
        group = decision['path']
        for evidence in decision['evidence']:
            evidence_hashes[evidence] = sha(ROOT/evidence)
        errors = []
        count = size = 0
        for file, info in I.files_under(ROOT/group, errors):
            rel = file.relative_to(ROOT).as_posix()
            if not payload_kind(group, rel, decision['kind']):
                continue
            safe_file(ROOT, rel, group)
            # Existing receipt hashes identify original bytes without hashing GB twice.
            receipt = file.parent/'receipt.json'
            digest = None
            if file.name in ('card.json','index.html') and receipt.exists():
                digest = I.load(receipt).get('files', {}).get(file.name)
            if decision['kind']=='run':
                before = I.load(file.parent/'before.json')
                assert digest and digest==before[file.name], file
            if not digest:
                digest = sha(file)
            all_files.append(dict(path=rel, group=group, kind=decision['kind'], size=info.st_size,
                                  mtime_ns=info.st_mtime_ns, sha256=digest))
            size += info.st_size; count += 1
        if any(e['error']!='REPARSE_POINT_SKIPPED' for e in errors):
            raise RuntimeError(errors)
        skips += errors
        decision.update(delete_files=count, delete_bytes=size)
        print(f'prepared {index+1}/{len(decisions)} {group}: {count} files', flush=True)
    assert len({f['path'] for f in all_files})==len(all_files)
    protected = protected_snapshot(original_runs, {d['path'] for d in decisions if d['action']=='CLEAN'})
    assert not set(protected) & {f['path'] for f in all_files}
    excluded = {r['path'] for r in original_runs if r['action']=='ARCHIVE_REVIEW'}
    assert len(excluded)==149 and not excluded & {f['group'] for f in all_files}
    summary = dict(prepared_at=now(), root=str(ROOT), authorized_source=str(ORIGINAL),
        authorization='User requested audit then cleanup of original 119 runs/18 work trees; only closed inactive subset',
        no_recursive_delete=True, decisions=decisions, files=all_files, evidence_sha256=evidence_hashes,
        protected_sha256=protected, excluded_149=sorted(excluded), skipped_links=skips,
        total_files=len(all_files), total_bytes=sum(f['size'] for f in all_files),
        current_activity='Current progress explicitly says R3 sentence follow-up in progress; 24 late runs and its replay kept; other app chats for this project idle/notLoaded at read; no other Python build process observed')
    I.save(plan_path, summary)
    I.csv_write(BASE/'decisions.csv', decisions, ['path','action','kind','delete_files','delete_bytes','reason','evidence'])
    I.save(BASE/'decisions.json', decisions)
    print(json.dumps(dict(plan=str(plan_path), sha256=sha(plan_path), files=len(all_files), bytes=summary['total_bytes']), ensure_ascii=True), flush=True)


def check_guards(plan):
    for relative, digest in plan['protected_sha256'].items():
        if sha(ROOT/relative)!=digest:
            raise RuntimeError(f'Protected file changed: {relative}')
    for relative, digest in plan['evidence_sha256'].items():
        if sha(ROOT/relative)!=digest:
            raise RuntimeError(f'Closure evidence changed: {relative}')


def reconcile_rebuild():
    """One audited retry after the observed c019af0b build; never reset a journal."""
    previous=I.load(BASE/'execution_result.json')
    assert previous['deleted_files']==0 and previous['planned_files_absent']==0
    assert (BASE/'deleted_files.jsonl').stat().st_size==0
    original=I.load(BASE/'cleanup_plan.json')
    pointer=I.load(PAGES/'_batch/campaign_latest.json')
    campaign=I.load(PAGES/pointer['report'])
    assert campaign['signature'].startswith('c019af0b')
    assert campaign['campaign_complete'] and campaign['completed']==campaign['expected']==2236
    assert not campaign['unresolved_latest_failures']
    new_runs=[]
    for cohort in I.COHORTS:
        report_path=PAGES/I.load(PAGES/'_batch'/cohort/'latest.json')['report']
        report=I.load(report_path)
        assert report['signature']==campaign['signature']
        assert report['requested']==report['requested_completed']
        assert not report['failed'] and not report['unresolved_latest_failures']
        new_runs.append(report_path.parent.relative_to(ROOT).as_posix())
    assert not set(new_runs) & {d['path'] for d in original['decisions']}
    changed={}
    for relative, digest in original['protected_sha256'].items():
        current=sha(ROOT/relative)
        if current!=digest:
            rel=(ROOT/relative).relative_to(PAGES)  # Non-page changes fail here.
            allowed=(len(rel.parts)==2 and rel.parts[0].isdigit() and rel.name=='receipt.json') or (
                rel.parts[0]=='_batch' and 'runs' not in rel.parts and rel.name in
                ('latest.json','plan_latest.json','campaign_latest.json'))
            assert allowed, relative
            changed[relative]=dict(before=digest,after=current)
    for relative,digest in original['evidence_sha256'].items():
        assert sha(ROOT/relative)==digest, relative
    rows=[dict(path=p.relative_to(ROOT).as_posix()) for p in (PAGES/'_batch').glob('*/runs/*') if p.is_dir()]
    refreshed=protected_snapshot(rows,set())
    retention=PAGES/'_batch/retention/state.json'
    refreshed[retention.relative_to(ROOT).as_posix()]=sha(retention)
    attempt=BASE/'after_rebuild'
    attempt.mkdir(exist_ok=False)
    audit=dict(observed_at=now(), previous_deleted_files=0, previous_log_bytes=0,
        original_plan_sha256=sha(BASE/'cleanup_plan.json'), campaign=campaign['signature'],
        new_runs_preserved=new_runs, changed_protected_files=changed,
        decision='Only current pointers/receipts changed; old run metadata and 14 closure evidence files unchanged. '
                 'Latest-only build readers checked in card_page_batch.py and parallel driver. '
                 'Other active Codex thread is auditing workflow documents. R3 follow-up, its recent runs, '
                 'all new runs and its work remain protected; deletion files are identical to original plan.')
    I.save(attempt/'concurrent_build_recheck.json',audit)
    original['protected_sha256']=refreshed
    original['prepared_at']=now()
    original['current_activity']=audit['decision']
    original['parent_plan_sha256']=audit['original_plan_sha256']
    audit_rel=(attempt/'concurrent_build_recheck.json').relative_to(ROOT).as_posix()
    original['evidence_sha256'][audit_rel]=sha(attempt/'concurrent_build_recheck.json')
    check_guards(original)
    I.save(attempt/'cleanup_plan.json',original)
    print(json.dumps(dict(plan=str(attempt/'cleanup_plan.json'),sha256=sha(attempt/'cleanup_plan.json'),
         protected_files=len(refreshed),changed_current_files=len(changed),new_runs=new_runs)),flush=True)


def execute(expected_hash):
    path = BASE/'cleanup_plan.json'
    if sha(path)!=expected_hash:
        raise ValueError('Plan checksum mismatch')
    plan = I.load(path)
    assert Path(plan['root']).resolve()==ROOT
    check_guards(plan)
    original_runs = I.load(ORIGINAL/'runs.json')
    original_work = I.load(ORIGINAL/'work.json')
    authorized = {r['path'] for r in original_runs if r['action']=='CANDIDATE_AFTER_REVIEW'}
    authorized |= {r['path'] for r in original_work if r['action']=='REVIEW_REPLAY'}
    groups = {d['path']:d for d in plan['decisions'] if d['action']=='CLEAN'}
    assert set(groups)<=authorized and not set(groups) & set(plan['excluded_149'])
    for index, entry in enumerate(plan['files'], 1):
        assert entry['group'] in groups and entry['kind']==groups[entry['group']]['kind']
        assert payload_kind(entry['group'], entry['path'], entry['kind'])
        # Full ancestor/reparse/content checks occur immediately before unlink.
        # This whole-plan pass only detects changes before any deletion begins.
        relative=Path(entry['path']); group=Path(entry['group'])
        if relative.is_absolute() or group.is_absolute() or '..' in relative.parts or '..' in group.parts:
            raise ValueError('Invalid manifest path')
        file = ROOT/relative
        if not file.is_relative_to(ROOT/group) or file==ROOT/group:
            raise ValueError('File outside candidate')
        info = file.stat()
        if (info.st_size, info.st_mtime_ns)!=(entry['size'],entry['mtime_ns']):
            raise RuntimeError(f'Payload changed after preparation: {file}')
        if index % 10000 == 0:
            print(f'pre-delete boundary/metadata checks: {index}/{len(plan["files"])} files', flush=True)
    log = BASE/'deleted_files.jsonl'
    if log.exists():
        raise FileExistsError('Execution already attempted; reconcile its journal before any rerun')
    before = shutil.disk_usage(ROOT).free
    I.save(BASE/'execution_start.json', dict(time=now(), free_bytes=before, plan_sha256=expected_hash))
    completed = Counter(); group_bytes=Counter(); error=None
    try:
        with log.open('x',encoding='utf-8', buffering=1) as stream:
            current = None
            for entry in plan['files']:
                if entry['group']!=current:
                    if current:
                        print(f'deleted payload {current}: {completed[current]} files', flush=True)
                    current=entry['group']
                    # Fast pointer gate between groups; full evidence/guards before and after.
                    for relative,digest in plan['protected_sha256'].items():
                        if relative.endswith(('/latest.json','/campaign_latest.json','/retention/state.json')):
                            if sha(ROOT/relative)!=digest:
                                raise RuntimeError(f'Pointer changed while cleaning: {relative}')
                file=safe_file(ROOT,entry['path'],entry['group'])
                info=file.stat()
                if (info.st_size, info.st_mtime_ns)!=(entry['size'],entry['mtime_ns']) or sha(file)!=entry['sha256']:
                    raise RuntimeError(f'Payload bytes changed / receipt mismatch: {file}')
                file.unlink()  # Exact regular file only, after validated absolute boundary.
                stream.write(json.dumps(entry,ensure_ascii=False)+'\n')
                completed[current]+=1;group_bytes[current]+=entry['size']
    except Exception as failure:
        error=repr(failure)
    verification_error=None
    try:
        check_guards(plan)
    except Exception as failure:
        verification_error=repr(failure)
    for group, count in completed.items():
        I.save(ROOT/group/'payload_cleanup_20261023.json', dict(cleaned_at=now(), removed_files=count,
               removed_logical_bytes=group_bytes[group], plan=path.relative_to(ROOT).as_posix(),
               journal=log.relative_to(ROOT).as_posix(),
               scope='Generated payload only; reports/signatures/receipts and evidence retained', error=error))
    absent=sum(not (ROOT/e['path']).exists() for e in plan['files'])
    after=shutil.disk_usage(ROOT).free
    result=dict(status='COMPLETE' if not error and not verification_error and absent==len(plan['files']) else 'PARTIAL_STOPPED',
        completed_at=now(), deleted_files=sum(completed.values()), deleted_logical_bytes=sum(group_bytes.values()),
        deleted_groups=dict(completed), group_bytes=dict(group_bytes), free_bytes_before=before,free_bytes_after=after,
        measured_free_space_increase_bytes=after-before, planned_files_absent=absent,
        all_protected_hashes_unchanged=verification_error is None, error=error, verification_error=verification_error,
        note='Free-space delta includes concurrent writes and this task journal; logical bytes are exact successful unlinks. No directories/junctions deleted.')
    I.save(BASE/'execution_result.json',result)
    print(json.dumps(result,ensure_ascii=True,indent=2),flush=True)
    if result['status']!='COMPLETE':
        raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--execute-plan-sha256')
    mode.add_argument('--reconcile-observed-rebuild',action='store_true')
    parser.add_argument('--attempt-dir', help='Named child of the task report directory for a reconciled retry')
    args=parser.parse_args()
    if args.attempt_dir:
        if not args.execute_plan_sha256 or Path(args.attempt_dir).name != args.attempt_dir or args.attempt_dir in ('.','..'):
            parser.error('attempt-dir must be one directory name and is execute-only')
        attempt=(BASE/args.attempt_dir).resolve(strict=True)
        if attempt.parent != BASE.resolve():
            parser.error('attempt-dir escapes report directory')
        BASE=attempt
    if args.prepare:
        prepare()
    elif args.reconcile_observed_rebuild:
        reconcile_rebuild()
    else:
        execute(args.execute_plan_sha256)
