"""Frozen-cohort runner: default plan-only; immutable run reports and persistent audit queues."""
import argparse
import datetime
import hashlib
import json
import time
import uuid
from pathlib import Path

from card_page import dump,validate,choose_samples
from card_page_data import Inputs,build_card
from card_page_render import page
from card_page_policy import metrics,summary_text
from card_page_cohorts import sha
from card_page_dependencies import source_paths,data_paths
from card_page_write import commit,reusable,state,retention,ArtifactWriteError


def aggregate(stats):
    cov={k:sum(s['coverage'][k] for s in stats) for k in ('N_all','E','N_num','A','B','C','original_A','partial_A')}
    cov['evidence_cross']={c:{e:sum(s['coverage']['evidence_cross'][c][e] for s in stats) for e in ('确认','推断','未知')} for c in ('A','B','C')}
    return cov


def audit_rows(card):
    return [dict(cid=card['cid'],row_id=r['row_id'],japanese=r['japanese'],page=f'{card["cid"]}/index.html#{r["row_id"]}',
                 row_class=r['row_class'],source=r['source'],review_status='NOT_REVIEWED',reviewer=None,decision=None,
                 issue=None,evidence=None,fix_recheck_status=None) for r in choose_samples(card)]


def inventory(out,m,cohort,signature):
    stats=[];audit=[];pending=[];invalid=[];latest_failures=[]
    for cid in m['cohorts'][cohort]:
        folder=out/str(cid)
        valid=reusable(folder,signature)
        attempt_path=out/'_batch'/cohort/'card_latest'/f'{cid}.json'
        if attempt_path.is_file():
            attempt=json.loads(attempt_path.read_text(encoding='utf-8'))
            if attempt.get('status')=='FAILED' and attempt.get('signature')==signature:
                latest_failures.append({**attempt,'current_artifacts_reusable':valid})
        if valid:
            card=json.loads((folder/'card.json').read_text(encoding='utf-8'))
            stats.append(dict(cid=cid,coverage=card['coverage'],summary=card['summary']))
            if cid in m['review_cids']:audit+=audit_rows(card)
        else:
            pending.append(cid)
            if (folder/'receipt.json').exists() or (folder/'reuse_blocked.json').exists():invalid.append(cid)
    return stats,audit,pending,invalid,latest_failures


def campaign(out,m,signature,cohort,report,run_dir):
    """Keep the latest matching signed snapshot of each cohort; old runs stay immutable."""
    reports=[];queue=[];snapshots=[];latest_failures=[]
    for key,expected in m['cohorts'].items():
        pointer=out/'_batch'/key/'latest.json'
        if key==cohort:current=report;path=run_dir/'cohort_report.json'
        elif pointer.is_file():
            path=out/json.loads(pointer.read_text(encoding='utf-8'))['report']
            current=json.loads(path.read_text(encoding='utf-8'))
        else:current=None;path=None
        valid=current is not None and current.get('signature')==signature
        snapshots.append(dict(cohort=key,report=path.relative_to(out).as_posix() if path else None,
                              status='MATCHING_SIGNATURE_SNAPSHOT' if valid else 'STALE_SIGNATURE' if current else 'NOT_GENERATED',
                              completed=current['completed'] if valid else 0,expected=len(expected)))
        if valid:
            reports+=current['statistics']
            latest_failures+=current['unresolved_latest_failures']
            queue_path=path.parent/'audit_queue.json';queue+=json.loads(queue_path.read_text(encoding='utf-8'))
    cov=aggregate(reports);result=dict(signature=signature,cohort_snapshots=snapshots,completed=len(reports),expected=len(m['members']),
            campaign_complete=len(reports)==len(m['members']),coverage=cov,summary=metrics(cov),
            audited=0,review_required_cards=len(m['review_cids']),queue_cards=len({r['cid'] for r in queue}),unresolved_latest_failures=latest_failures,
            status='Generation snapshots, not completed human review. Artifact hashes verified as of each referenced run; stale signatures excluded.')
    dump(run_dir/'campaign_report.json',result);dump(run_dir/'campaign_audit_queue.json',queue)
    dump(out/'_batch/campaign_latest.json',dict(report=(run_dir/'campaign_report.json').relative_to(out).as_posix(),
                                              audit_queue=(run_dir/'campaign_audit_queue.json').relative_to(out).as_posix()))


def run(args):
    manifest=args.manifest.resolve();m=json.loads(manifest.read_text(encoding='utf-8'))
    if sha(manifest.parent/m['frozen_csv'])!=m['source_sha256']:raise ValueError('Frozen roster hash mismatch')
    root=args.input_root.resolve();out=args.output.resolve()
    if sha(root/m['source'])!=m['source_sha256']:raise ValueError('Current roster differs from frozen cohort')
    expected=m['cohorts'][args.cohort];cids=expected
    if args.cid:
        if not set(args.cid)<=set(expected):raise ValueError('Subset cid is outside the explicit frozen cohort')
        cids=list(dict.fromkeys(args.cid))
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    run_dir=out/'_batch'/args.cohort/'runs'/stamp;run_dir.mkdir(parents=True,exist_ok=False)
    source_signature=hashlib.sha256(''.join(str(p.relative_to(root))+sha(p) for p in source_paths(root)).encode()).hexdigest()
    generation=hashlib.sha256((sha(manifest)+source_signature).encode()).hexdigest()
    plan=dict(mode='EXECUTE' if args.execute else 'PLAN_ONLY',cohort=args.cohort,cids=cids,count=len(cids),expected=len(expected),
              subset=list(cids)!=list(expected),manifest_sha256=sha(manifest),source_signature=source_signature,generation_signature=generation,
              run_id=stamp,run_directory=run_dir.relative_to(out).as_posix(),review_required_cids=[cid for cid in cids if cid in m['review_cids']],
              inference_layer='暂不启用；候选晋级及一般机制择句未实现',
              summary={k:dict(count=None,denominator=None,rate=None,status='NOT_GENERATED') for k in ('A','whole_row_confirmed','original_A','C')},
              permission_boundary='R2通过前不执行全量，过审后等主持按已确认顺序调度；当前追加修复完成后先暂停')
    dump(run_dir/'plan.json',plan)
    if not args.execute:
        dump(out/'_batch'/args.cohort/'plan_latest.json',dict(plan=(run_dir/'plan.json').relative_to(out).as_posix()))
        return plan
    declared=[dict(path=p.relative_to(root).as_posix(),sha256=sha(p) if p.exists() else 'MISSING') for p in data_paths(root)]
    dependency_signature=hashlib.sha256(json.dumps(declared,sort_keys=True).encode()).hexdigest()
    signature=hashlib.sha256((generation+dependency_signature).encode()).hexdigest()
    dump(run_dir/'signatures.json',dict(signature=signature,source_signature=source_signature,manifest_sha256=sha(manifest),dependency_signature=dependency_signature,data_dependencies=declared))
    try:data=Inputs(root,cids)
    except Exception as error:
        dump(run_dir/'initialization_failure.json',dict(status='INITIALIZATION_FAILED',cids=cids,error_type=type(error).__name__,error=str(error),signature=signature))
        raise
    attempts=[];reused=0;start=time.perf_counter()
    for cid in cids:
        folder=out/str(cid);before=state(folder);card=None
        try:
            if args.resume and reusable(folder,signature):reused+=1;status='REUSED'
            else:
                card=build_card(data,cid);html=page(card);validate(card,html)
                stage=run_dir/'transactions'/str(cid)/'new';dump(stage/'card.json',card);(stage/'index.html').write_text(html,encoding='utf-8')
                commit(folder,stage,stage.parent/'backup',dict(signature=signature,source_signature=source_signature,
                       dependency_signature=dependency_signature,manifest_sha256=sha(manifest),run_id=stamp))
                status='GENERATED'
            attempts.append(dict(cid=cid,status=status,signature=signature))
        except Exception as error:
            detail=error.detail if isinstance(error,ArtifactWriteError) else retention(folder,before)
            failure=dict(cid=cid,error_type=type(error).__name__,error=str(error),signature=signature,status='FAILED',**detail)
            dump(run_dir/'failures'/f'{cid}.json',failure);attempts.append(failure)
        finally:
            card=None
            dump(out/'_batch'/args.cohort/'card_latest'/f'{cid}.json',{**attempts[-1],'run_directory':run_dir.relative_to(out).as_posix()})
    stats,audit,pending,invalid,latest_failures=inventory(out,m,args.cohort,signature);cov=aggregate(stats)
    failed=[a for a in attempts if a['status']=='FAILED']
    result=dict(plan=plan,signature=signature,source_signature=source_signature,dependency_signature=dependency_signature,
                manifest_sha256=sha(manifest),attempts=attempts,requested=len(cids),requested_completed=len(attempts)-len(failed),
                completed=len(stats),expected=len(expected),subset=plan['subset'],cohort_complete=len(stats)==len(expected),
                reused=reused,failed=failed,unresolved_latest_failures=latest_failures,pending_cids=pending,stale_or_invalid_cids=invalid,coverage=cov,summary=metrics(cov),
                statistics=stats,seconds=time.perf_counter()-start,review_status='Queue is NOT_REVIEWED; external review decisions stay in versioned review records',
                unreviewed_cards=len({r['cid'] for r in audit}))
    dump(run_dir/'cohort_report.json',result);dump(run_dir/'audit_queue.json',audit)
    (run_dir/'cohort_report.md').write_text(summary_text(result['summary'])+f'\n本次请求{len(cids)}/{len(expected)}；本次成功{result["requested_completed"]}；失败{len(failed)}。当前同签名cohort累计完成{len(stats)}/{len(expected)}；cohort_complete={result["cohort_complete"]}；未核读卡{result["unreviewed_cards"]}。B={cov["B"]}；部分A={cov["partial_A"]}。\n推断层暂不启用；B0不代表无机制。\n',encoding='utf-8')
    dump(out/'_batch'/args.cohort/'latest.json',dict(report=(run_dir/'cohort_report.json').relative_to(out).as_posix(),audit_queue=(run_dir/'audit_queue.json').relative_to(out).as_posix()))
    campaign(out,m,signature,args.cohort,result,run_dir)
    return dict(completed=len(stats),expected=len(expected),requested_completed=result['requested_completed'],cohort_complete=result['cohort_complete'],
                reused=reused,failed=len(failed),report=(run_dir/'cohort_report.json').relative_to(out).as_posix(),summary=result['summary'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--cohort',choices=('ge60','40to59','20to39','remaining'),required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--cid',type=int,nargs='+',help='Explicit subset within the frozen cohort')
    print(json.dumps(run(p.parse_args()),ensure_ascii=True))


if __name__=='__main__':main()
