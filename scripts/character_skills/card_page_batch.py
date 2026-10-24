"""Frozen-cohort runner: default plan-only; immutable run reports and persistent audit queues."""
import argparse
import datetime
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

from card_page import dump,validate,choose_samples
from card_page_data import Inputs,build_card
# 版式迁移（2026-10-20 定稿）：主渲染层切换为 card_page_render_v2（玩家视角版式，
# 定稿依据 output/character_skills/dbstyle_samples/DESIGN.md 与三张示例）；旧
# card_page_render.page 保留给 11 卡试点入口（card_page.py），不再被 batch 使用。
from card_page_render_v2 import page
# M1（20261021 独立审查整改）：campaign 完成检查复用入口页生成器的一致性检查。
from card_page_index import entry_pages_consistency
from card_page_policy import metrics,summary_text
from card_page_cohorts import sha
from card_page_dependencies import source_paths,data_paths
from card_page_write import commit,reusable,state,retention,ArtifactWriteError
from run_retention import reserve_run


def aggregate(stats):
    cov={k:sum(s['coverage'][k] for s in stats) for k in ('N_all','E','N_num','A','B','C','original_A','partial_A')}
    cov['evidence_cross']={c:{e:sum(s['coverage']['evidence_cross'][c][e] for s in stats) for e in ('确认','推断','未知')} for c in ('A','B','C')}
    # 模板作用域推断层试点（type1017）、批 3（type8）与批 4（条件扩展）晋级/留 hint 行数随 cohort 聚合透传。
    for key in ('inference_pilot_promoted','inference_pilot_hinted','inference_b3_promoted','inference_b3_hinted',
                'inference_b4_promoted','inference_b4_hinted','inference_b5_promoted','inference_b5_hinted',
                'inference_b6_promoted','inference_b6_hinted','inference_b7_promoted','inference_b7_hinted',
                'inference_b8_promoted','inference_b8_hinted','inference_b9_promoted','inference_b9_hinted',
                'inference_b10_promoted','inference_b10_hinted','inference_b11_promoted',
                'inference_b11_hinted','inference_b12_promoted','inference_b13_promoted',
                'inference_b13_hinted','inference_b14_promoted','inference_b15_promoted',
                'inference_b15_hinted','inference_b17_promoted','inference_b17_hinted'):
        cov[key]=sum(s['coverage'].get(key,0) for s in stats)
    # H-01：整行确认的记录级/类型外推拆分随 cohort 聚合透传。
    scopes={}
    for s in stats:
        for key,value in (s['coverage'].get('confirmed_rows_by_scope') or {}).items():
            scopes[key]=scopes.get(key,0)+value
    cov['confirmed_rows_by_scope']=scopes
    return cov


def audit_rows(card):
    """G-15：在既有每卡≥10行抽样（不足10行全列）之上，保证每个有实际行的 configured skill
    至少1个不同实际 row_id 入队；技能多的卡队列可超过10行。合并别名行的技能由共享的
    规范行代表（同实际位置，无法再拆出不同 row_id），按 alias_row_ids 说明。"""
    selected={}
    for r in choose_samples(card):selected[r['row_id']]=r
    for s in (s for g in card['groups'] for s in g['skills'] if s['rows']):
        if not any(r['row_id'] in selected for r in s['rows']):
            selected[s['rows'][0]['row_id']]=s['rows'][0]
    rows={r['row_id']:r for g in card['groups'] for s in g['skills'] for r in s['rows']}
    return [dict(cid=card['cid'],row_id=r['row_id'],japanese=r['japanese'],page=f'{card["cid"]}/index.html#{r["row_id"]}',
                 row_class=r['row_class'],source=r['source'],review_status='NOT_REVIEWED',reviewer=None,decision=None,
                 issue=None,evidence=None,fix_recheck_status=None)
            for r in sorted(selected.values(),key=lambda r:[row['row_id'] for row in rows.values()].index(r['row_id']))]


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
    # M1（20261021 独立审查整改）：campaign 完成时核对入口页（index.html/all_cards.html）
    # 的指标与 run 指针是否等于本次 campaign；过期/缺失时在 campaign_report 的
    # entry_pages 字段明确标注 STALE/NOT_FOUND 并向 stderr 发警告，不允许静默陈旧。
    report_rel=(run_dir/'campaign_report.json').relative_to(out).as_posix()
    result['entry_pages']=entry_pages_consistency(out,result['summary'],report_rel)
    dump(run_dir/'campaign_report.json',result);dump(run_dir/'campaign_audit_queue.json',queue)
    dump(out/'_batch/campaign_latest.json',dict(report=report_rel,
                                              audit_queue=(run_dir/'campaign_audit_queue.json').relative_to(out).as_posix()))
    if result['entry_pages']['status']!='CURRENT':
        print(f"[WARN] 入口页与当前 campaign 不一致（entry_pages={result['entry_pages']['status']}）："
              f"{'; '.join(result['entry_pages']['detail'])}"
              f"——请重跑 scripts/character_skills/card_page_index.py --execute 刷新，不要带着过期入口页交付。",
              file=sys.stderr)


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
              inference_layer='模板作用域推断层已启用十七批（type1017 试点 337 行＋批 3 type8 严格子集 '
                              'Tier1 40 行＋批 4 条件扩展候选 37 行＋批 5 跨表扩展 job_ability/'
                              'supporterskill 211 行＋批 6 必殺バフ bossskill type13 子记录解析 '
                              '1,349 行（B6-RV-01 修复：30 行同属性竞争句降级留 hint）＋批 7 共鳴 '
                              'sympathy ability3000 载体解析＋批 8 暴击 2012 链载体解析＋批 9 '
                              '敵デバフ skilllist own sub_effect→ability99 载体解析＋批 10 '
                              'SA_PowerDrain ability2003 载体解析（批 9 C1 遗留 431 行闭合，'
                              'rules.py 2003 注册处五键）＋批 11 普通自身增益 skilllist 父 '
                              'sub[]→ability1095 Always3 载体解析（tier A 34 行）＋批 12 '
                              '1095 扩域（rules.json 三键 p2/p5/p6 occurrences 407/211/407 '
                              '存在数口径后，批 11 tier B 94 行整行晋级、行级键 '
                              'inference_b12 按行级替换批 11 tier B hint，不双登记）＋批 13 '
                              'APK 扩域（rules.json 99 四键＋2003 五键样本域扩至 CACHE＋APK '
                              '两域分源＋occurrences_apk 后，批 9 APK 域外 94 行与批 10 APK '
                              '域外 192 行在 B9/B10 载体域门委托 B13 按载体层域接管：晋级 '
                              '278 行键 inference_b13、8 行 multi-carrier 留 hint '
                              'inference_b13_hint；不双登记）＋批 14 APK 扩域第二批'
                              '（rules.json 2012 三键＋1095 五键样本域扩至 CACHE＋APK 两域'
                              '分源＋occurrences_apk 后，批 8 APK 域外 196 行与批 11/12 APK '
                              '域外 27 行在 B8 G5/B11 P2 域门委托 B14 按载体层域接管：晋级 '
                              '212 行键 inference_b14、11 行按实际门（G6 对象词缺失 1＋P4 '
                              '形状不符 10）留 hint；iParam0≠0 8 载体 27 行 condition_label '
                              '条件分组披露；不双登记）＋批 15 并集归属（t13 槽∪2012 暴击链，'
                              'U1–U5 门）＋批 17 P0 断点收尾（槽位分区/时长槽共享 D1 裁决/'
                              'denju patternid 映射＋P2 溢出，行级键 inference_b17、'
                              '不双登记）＋R1 整改（20261023 独立复审：HP 档位条件分支'
                              '保留——denju patternid 全引用分档与 charainfo 同文 pattern/'
                              'denju 直接行逐档出值，condition_label「HP 51–100%」式原值'
                              '边界＋待核查注记，空 sinfo 不排除））；只升「推断」档；'
                              '候选晋级及一般机制择句仍未实现',
              summary={k:dict(count=None,denominator=None,rate=None,status='NOT_GENERATED') for k in ('A','whole_row_confirmed','original_A','C')},
              permission_boundary='本轮按任务卡 docs/tasks/20261023-character-skills-recheck-rectification.md '
                                  '授权执行复审整改 R1（HP 条件分支）：b17 _run_multi 与 b6 '
                                  '同文 pattern/denju 直接行路径改为沿源记录全部 pattern 引用'
                                  '保留条件分支（空 sinfo 不排除），逐档位绑定出值；effect_ledger '
                                  '分支覆盖完成判定＋S5 标志；rules.json 零改动；30236 基线'
                                  '零触碰；批 8/14/15 及其余批 6 既有答案零触碰（8 行 HP 多档位'
                                  '行按分支补齐）；'
                                  '四 cohort 全量重建')
    dump(run_dir/'plan.json',plan)
    if not args.execute:
        dump(out/'_batch'/args.cohort/'plan_latest.json',dict(plan=(run_dir/'plan.json').relative_to(out).as_posix()))
        return plan
    declared=[dict(path=p.relative_to(root).as_posix(),sha256=sha(p) if p.exists() else 'MISSING') for p in data_paths(root)]
    dependency_signature=hashlib.sha256(json.dumps(declared,sort_keys=True).encode()).hexdigest()
    signature=hashlib.sha256((generation+dependency_signature).encode()).hexdigest()
    # Bound new backup growth; legacy runs remain untouched. Shared reservation
    # is atomic across parallel cohorts and survives failed/interrupted builds.
    retention_reservation=reserve_run(out,run_dir,[cid for cid in cids
        if not (args.resume and reusable(out/str(cid),signature))])
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
    result=dict(plan=plan,retention_reservation=retention_reservation,signature=signature,source_signature=source_signature,dependency_signature=dependency_signature,
                manifest_sha256=sha(manifest),attempts=attempts,requested=len(cids),requested_completed=len(attempts)-len(failed),
                completed=len(stats),expected=len(expected),subset=plan['subset'],cohort_complete=len(stats)==len(expected),
                reused=reused,failed=failed,unresolved_latest_failures=latest_failures,pending_cids=pending,stale_or_invalid_cids=invalid,coverage=cov,summary=metrics(cov),
                statistics=stats,seconds=time.perf_counter()-start,review_status='Queue is NOT_REVIEWED; external review decisions stay in versioned review records',
                unreviewed_cards=len({r['cid'] for r in audit}))
    dump(run_dir/'cohort_report.json',result);dump(run_dir/'audit_queue.json',audit)
    (run_dir/'cohort_report.md').write_text(summary_text(result['summary'])+f'\n本次请求{len(cids)}/{len(expected)}；本次成功{result["requested_completed"]}；失败{len(failed)}。当前同签名cohort累计完成{len(stats)}/{len(expected)}；cohort_complete={result["cohort_complete"]}；未核读卡{result["unreviewed_cards"]}。B={cov["B"]}；部分A={cov["partial_A"]}。\n推断层暂不启用；B0不代表无机制。\n',encoding='utf-8')
    dump(out/'_batch'/args.cohort/'latest.json',dict(report=(run_dir/'cohort_report.json').relative_to(out).as_posix(),audit_queue=(run_dir/'audit_queue.json').relative_to(out).as_posix()))
    # 并行驱动（card_page_batch_parallel.py，20261023）以 --defer-campaign 把唯一的跨
    # cohort 共享写（_batch/campaign_latest.json 聚合）剥离出子进程，改由驱动在全部
    # cohort 成功后单写者调用同一 campaign() 完成；不带该标志的串行行为逐字节不变。
    if not getattr(args,'defer_campaign',False):campaign(out,m,signature,args.cohort,result,run_dir)
    return dict(completed=len(stats),expected=len(expected),requested_completed=result['requested_completed'],cohort_complete=result['cohort_complete'],
                reused=reused,failed=len(failed),report=(run_dir/'cohort_report.json').relative_to(out).as_posix(),summary=result['summary'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--cohort',choices=('ge60','40to59','20to39','remaining'),required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--cid',type=int,nargs='+',help='Explicit subset within the frozen cohort')
    p.add_argument('--defer-campaign',action='store_true',help='Skip the cross-cohort campaign aggregation (card_page_batch_parallel.py runs it single-writer after all cohorts); serial behavior unchanged without this flag')
    print(json.dumps(run(p.parse_args()),ensure_ascii=True))


if __name__=='__main__':main()
