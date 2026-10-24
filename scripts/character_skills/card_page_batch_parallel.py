"""Parallel driver for the four frozen cohorts (tooling improvement, 20261023).

Equivalence-first design (task docs/tasks/20261023-character-skills-parallel-cohort.md):
- Each cohort is still built by the untouched serial implementation
  card_page_batch.py, launched as a separate *process* (subprocess, not threads:
  card_page_data.Inputs.__init__ does os.chdir and mutates module-level globals
  card_page_data.py:455-457, so any in-process parallelism would be unsafe).
- Per-cohort write surfaces are disjoint by construction: card folders out/<cid>/
  are partitioned by the frozen manifest (card_page_cohorts.py:21-23 asserts 2236
  unique members split into the four cohorts), and _batch/<cohort>/** is
  cohort-private. The only cross-cohort shared write is the campaign aggregation
  (card_page_batch.campaign -> out/_batch/campaign_latest.json), which reads the
  other cohorts' latest.json pointers.
- This driver therefore launches each cohort with --defer-campaign (the only
  change to the serial entry; without the flag its behavior is byte-identical to
  before), waits for all selected cohorts to succeed, then performs the campaign
  aggregation itself as a single writer by calling the SAME card_page_batch.campaign
  function. Aggregation iterates m['cohorts'].items() in manifest order
  (card_page_batch.py:86), so the aggregated content is independent of completion
  order. The campaign report is hosted in the run directory of the last selected
  cohort in manifest order (default 'remaining'), reproducing the serial final
  state where the last-executed cohort writes the final campaign snapshot.
- The serial entry stays the fallback: card_page_batch.py --cohort <c> ... as before.

Failure path: if any cohort subprocess exits non-zero, no aggregation runs
(campaign would snapshot a stale/partial signature set); rerun the same command
with --resume to reuse every successful card and retry failures per cohort.

usage (repo root):
  & .\\.venv\\Scripts\\python.exe -B scripts/character_skills/card_page_batch_parallel.py ^
      --input-root . --manifest output/character_skills/r2_preparation/cohorts/manifest.json ^
      --output output/character_skills/pages --execute --jobs 4
  (without --execute: plan-only, cohorts planned sequentially, nothing generated)
"""
import argparse
import concurrent.futures
import json
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent


def cohort_command(args,cohort,execute):
    cmd=[sys.executable,'-B',str(HERE/'card_page_batch.py'),
         '--input-root',str(args.input_root),'--manifest',str(args.manifest),
         '--cohort',cohort,'--output',str(args.output),'--defer-campaign']
    if execute:cmd.append('--execute')
    if args.resume:cmd.append('--resume')
    return cmd


def run_cohort(args,cohort,execute):
    started=time.perf_counter()
    proc=subprocess.run(cohort_command(args,cohort,execute),capture_output=True,
                        text=True,encoding='utf-8',errors='replace')
    wall=time.perf_counter()-started
    summary=None
    if proc.returncode==0:
        lines=[l for l in proc.stdout.splitlines() if l.strip()]
        try:summary=json.loads(lines[-1]) if lines else None
        except ValueError:summary=None
    return dict(cohort=cohort,returncode=proc.returncode,wall_seconds=wall,
                generation_seconds=(summary or {}).get('seconds'),
                summary=summary,stdout_tail=proc.stdout[-2000:] if proc.returncode else '',
                stderr_tail=proc.stderr[-2000:] if proc.returncode else '')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--jobs',type=int,default=2,help='Concurrent cohort processes (2 or 4 measured)')
    p.add_argument('--cohorts',nargs='+',choices=('ge60','40to59','20to39','remaining'),default=None,
                   help='Subset of cohorts (default: all four in manifest order)')
    p.add_argument('--campaign-host-cohort',default=None,
                   help='Cohort whose run directory hosts the final campaign report '
                        '(default: last selected cohort in manifest order, i.e. remaining, '
                        'matching the serial execution order final state)')
    p.add_argument('--execute',action='store_true');p.add_argument('--resume',action='store_true')
    args=p.parse_args()
    manifest=args.manifest.resolve();m=json.loads(manifest.read_text(encoding='utf-8'))
    order=[c for c in m['cohorts'] if args.cohorts is None or c in args.cohorts]
    if args.cohorts is not None and sorted(order)!=sorted(args.cohorts):
        raise SystemExit(f'[FAIL] --cohorts 子集无效：{sorted(args.cohorts)} ⊄ manifest {list(m["cohorts"])}')
    host=args.campaign_host_cohort or order[-1]
    if host not in order:raise SystemExit(f'[FAIL] campaign 宿主 cohort {host} 不在本次集合内')
    out=args.output.resolve()
    plan=dict(mode='EXECUTE' if args.execute else 'PLAN_ONLY',driver=__file__,jobs=args.jobs,
              cohorts=order,schedule=sorted(order,key=lambda c:-len(m['cohorts'][c])),
              campaign_host_cohort=host,output=str(out))
    if not args.execute:
        # Plan mode is cheap and per-cohort; run sequentially without --execute.
        results=[run_cohort(args,c,execute=False) for c in order]
        print(json.dumps({**plan,'cohort_results':[{k:r[k] for k in ('cohort','returncode','summary')} for r in results]},
                         ensure_ascii=True));return
    start=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,args.jobs)) as pool:
        results=list(pool.map(lambda c:run_cohort(args,c,True),plan['schedule']))
    failed=[r for r in results if r['returncode']!=0 or not r['summary']]
    if failed:
        print(json.dumps({**plan,'status':'COHORT_FAILED','cohort_results':results,'wall_seconds':time.perf_counter()-start,
                          'note':'未执行 campaign 聚合（存在失败 cohort）；带 --resume 重跑同一命令可复用成功卡并按 cohort 重试。'},
                         ensure_ascii=True))
        raise SystemExit(1)
    # Single-writer campaign aggregation: reuse the serial implementation verbatim.
    pointers={}
    for c in order:
        ptr=out/'_batch'/c/'latest.json'
        if not ptr.is_file():raise SystemExit(f'[FAIL] cohort {c} 未写出 latest.json：{ptr}')
        pointers[c]=json.loads(ptr.read_text(encoding='utf-8'))
    reports={c:json.loads((out/pointers[c]['report']).read_text(encoding='utf-8')) for c in order}
    signatures={reports[c]['signature'] for c in order}
    if len(signatures)!=1:
        raise SystemExit(f'[FAIL] 各 cohort 签名不一致（代码/输入在运行间隙变化？）：{ {c:s[:12] for c,s in ((c,reports[c]["signature"]) for c in order)} }')
    import card_page_batch as B
    host_dir=(out/pointers[host]['report']).parent
    agg_start=time.perf_counter()
    B.campaign(out,m,reports[host]['signature'],host,reports[host],host_dir)
    agg_wall=time.perf_counter()-agg_start
    total=time.perf_counter()-start
    print(json.dumps({**plan,'status':'OK','signature':reports[host]['signature'],
                      'campaign_report':pointers[host]['report'].replace('cohort_report.json','campaign_report.json'),
                      'campaign_aggregation_seconds':agg_wall,
                      'cohort_results':[{k:r[k] for k in ('cohort','wall_seconds','generation_seconds','summary')} for r in results],
                      'wall_seconds':total},ensure_ascii=True))


if __name__=='__main__':main()
