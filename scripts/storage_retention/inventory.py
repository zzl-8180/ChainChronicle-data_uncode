"""Read-only run/work inventory. No delete, move, archive, or pointer updates."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import time

COHORTS = ('ge60', '40to59', '20to39', 'remaining')
RUN_ID = re.compile(r'20\d{6}T\d{12}Z-[0-9a-f]{8}')
REPLAY = re.compile(r'^(?:replay.*|.*_replay(?:_.*)?|union_build|scratch|sandbox_pages_.*)$', re.I)
BASELINE = re.compile(r'^old_(?:pages|cards|card_json).*$', re.I)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def files_under(root, errors):
    """scandir caches Windows size metadata; do not stat every Path again.

    Never follow junctions/symlinks. An incomplete scan is explicitly reported.
    """
    stack = [str(root)]
    retries = Counter()
    while stack:
        parent = stack.pop()
        try:
            with os.scandir(parent) as iterator:
                entries = list(iterator)
                for entry in entries:
                    try:
                        info = entry.stat(follow_symlinks=False)
                        if entry.is_symlink() or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                            errors.append(dict(path=entry.path, error='REPARSE_POINT_SKIPPED'))
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            yield Path(entry.path), info
                    except OSError as error:
                        errors.append(dict(path=entry.path, error=str(error)))
        except OSError as error:
            if isinstance(error, PermissionError) and retries[parent] < 2:
                retries[parent] += 1
                time.sleep(0.05)
                stack.append(parent)
                continue
            errors.append(dict(path=parent, error=str(error)))


def references(root, errors):
    texts = []
    candidates = [root / n for n in ('AGENTS.md', 'README.md', 'HANDOFF.md', 'STATUS.md')]
    for base in (root/'scripts', root/'docs/tasks', root/'output/character_skills/review'):
        for path, info in files_under(base, errors):
            if path.suffix in ('.py', '.md', '.json') and info.st_size <= 2 * 1024 ** 2:
                candidates.append(path)
    for path in candidates:
        try:
            content = path.read_text(encoding='utf-8-sig').replace('\\', '/')
        except (OSError, UnicodeError) as error:
            errors.append(dict(path=str(path), error=str(error)))
            continue
        texts.append((path.relative_to(root).as_posix(), content))
    run_refs = defaultdict(set)
    active_work = defaultdict(set)
    for source, content in texts:
        for run_id in RUN_ID.findall(content):
            run_refs[run_id].add(source)
        if source.startswith('docs/tasks/') and re.search(r'状态[^\n]*(?:进行中|待独立复验|实施中)', content[:1800]):
            for name in re.findall(r'work/([^/\s`\"\'<>；;，,）)]+)', content):
                active_work[name].add(source)
    return texts, run_refs, active_work


def run_inventory(root, pages, run_refs, errors):
    batch = pages / '_batch'
    protected = defaultdict(set)
    # Pointer targets are metadata dependencies even if timestamps are older.
    pointers = [batch/'campaign_latest.json']
    pointers += [batch/c/n for c in COHORTS for n in ('latest.json', 'plan_latest.json')]
    pointer_before = {}
    for ptr in pointers:
        if ptr.exists():
            pointer_before[str(ptr)] = ptr.read_bytes()
            try:
                for value in load(ptr).values():
                    if isinstance(value, str):
                        for run_id in RUN_ID.findall(value):
                            protected[run_id].add('CURRENT_POINTER:' + ptr.relative_to(root).as_posix())
            except (ValueError, OSError) as error:
                errors.append(dict(path=str(ptr), error=str(error)))
    for folder in pages.iterdir():
        if not folder.name.isdigit() or not folder.is_dir():
            continue
        blocker = folder/'reuse_blocked.json'
        if blocker.exists():
            for run_id in RUN_ID.findall(blocker.read_text(encoding='utf-8')):
                protected[run_id].add('RECOVERY_BLOCKER:' + str(blocker.relative_to(root)))
    runs = []
    signatures = defaultdict(list)
    for cohort in COHORTS:
        run_root = batch/cohort/'runs'
        for run in sorted(run_root.iterdir()):
            if not run.is_dir():
                continue
            counters = Counter()
            error_start = len(errors)
            for file, info in files_under(run, errors):
                parts = file.relative_to(run).parts
                category = 'backup' if 'backup' in parts else 'stage' if 'new' in parts else 'metadata'
                counters[category + '_bytes'] += info.st_size
                counters[category + '_files'] += 1
                if category == 'backup' and file.name in ('card.json', 'index.html'):
                    counters['backup_payload_bytes'] += info.st_size
            report = {}
            try:
                if (run/'cohort_report.json').exists():
                    report = load(run/'cohort_report.json')
            except (ValueError, OSError) as error:
                errors.append(dict(path=str(run), error=str(error)))
            row = dict(path=run.relative_to(root).as_posix(), cohort=cohort, run_id=run.name,
                       signature=report.get('signature'), completed=report.get('completed'),
                       expected=report.get('expected'), scan_complete=len(errors)==error_start,
                       failed=len(report.get('failed', [])), references=sorted(run_refs.get(run.name, [])),
                       has_report=bool(report), **dict(counters))
            row['bytes'] = sum(counters[k] for k in ('backup_bytes', 'stage_bytes', 'metadata_bytes'))
            row['files'] = sum(counters[k] for k in ('backup_files', 'stage_files', 'metadata_files'))
            row['complete_success'] = bool(report.get('cohort_complete')) and not row['failed'] and not report.get('unresolved_latest_failures')
            if row['complete_success'] and row['signature']:
                signatures[row['signature']].append(row)
            runs.append(row)
        print(f'scanned runs: {cohort}', flush=True)
    coherent = [rows for rows in signatures.values() if {r['cohort'] for r in rows} == set(COHORTS)]
    coherent.sort(key=lambda rows:max(r['run_id'] for r in rows), reverse=True)
    for rows in coherent[:2]:
        for cohort in COHORTS:
            newest = max((r for r in rows if r['cohort']==cohort), key=lambda r:r['run_id'])
            protected[newest['run_id']].add('RECENT_COHERENT_BASELINE_NOT_ASSUMED_REVIEWED')
    for row in runs:
        reasons = sorted(protected[row['run_id']])
        if not row['scan_complete']:
            reasons.append('INCOMPLETE_SCAN')
        if row['failed'] or row.get('stage_bytes', 0) or (not row['has_report'] and row.get('backup_bytes', 0)):
            reasons.append('FAILED_OR_INTERRUPTED_RECOVERY_REQUIRES_REVIEW')
        if reasons:
            action = 'KEEP'
        elif row['references']:
            action = 'ARCHIVE_REVIEW'
            reasons.append('HISTORICAL_REFERENCE: preserve review baseline or archive with path mapping before cleanup')
        else:
            action = 'CANDIDATE_AFTER_REVIEW'
            reasons.append('Unreferenced by scanned text; superseded payload. Absence of textual reference is not proof of no dependency.')
        reasons.append('KEEP_ALL_RUN_METADATA: reports, signatures, queues, receipts/before.json and failure records')
        # Keep small receipt/before files even in proposed backup cleanup.
        # Exact payload is card.json + index.html ONLY; measure separately below.
        row.update(action=action, reasons=reasons,
                   reclaimable_bytes=row.get('backup_payload_bytes', 0) if action != 'KEEP' else 0)
    for ptr, content in pointer_before.items():
        if Path(ptr).read_bytes() != content:
            errors.append(dict(path=ptr, error='POINTER_CHANGED_DURING_SCAN'))
    return runs


def work_inventory(root, texts, active_work, errors):
    work = root/'work'
    units = {}
    top_totals = defaultdict(Counter)
    for file, info in files_under(work, errors):
        parts = file.relative_to(work).parts
        top = parts[0]
        top_totals[top]['bytes'] += info.st_size
        top_totals[top]['files'] += 1
        chosen = None
        kind = None
        for i, part in enumerate(parts[:-1]):
            if REPLAY.fullmatch(part):
                chosen = Path('work', *parts[:i+1]).as_posix()
                kind = 'REPLAY_TREE'
                break
            if BASELINE.fullmatch(part):
                chosen = Path('work', *parts[:i+1]).as_posix()
                kind = 'BASELINE_TREE'
                break
        if chosen:
            pass
        elif re.match(r'pages_before.*\.json$', parts[-1]):
            chosen = Path('work', *parts).as_posix()
            kind = 'BASELINE_SNAPSHOT'
        else:
            chosen = (Path('work')/top).as_posix() + ' [other retained files]'
            kind = 'OTHER'
        row = units.setdefault(chosen, dict(path=chosen, kind=kind, top=top, bytes=0, files=0))
        row['bytes'] += info.st_size
        row['files'] += 1
    for row in units.values():
        prefix = row['path'].split(' [')[0]
        refs = [src for src, content in texts if prefix in content]
        top_refs = [src for src, content in texts if 'work/'+row['top']+'/' in content or 'work/'+row['top']+'`' in content]
        active = sorted(active_work.get(row['top'], []))
        row.update(references=refs, parent_references=top_refs, active_tasks=active)
        if row['kind']=='REPLAY_TREE' and not active:
            row.update(action='REVIEW_REPLAY', reclaimable_bytes=row['bytes'],
                       reasons=['Replay/sandbox/scratch name is a candidate hint, not proof of disposable content.',
                                'Keep audit reports/scripts, comparison manifests and unique fixtures before removal; confirm no live writer.',
                                'Listed bytes are a gross upper bound before evidence extraction.'])
        else:
            row.update(action='KEEP', reclaimable_bytes=0,
                       reasons=['ACTIVE_OR_UNCLOSED_TASK' if active else 'BASELINE_EVIDENCE' if row['kind'] in ('BASELINE_SNAPSHOT', 'BASELINE_TREE')
                                else 'NOT_A_VERIFIED_REPLAY: may contain native runtime, inputs, source snapshots, unique audit evidence'])
    return list(units.values()), dict(top_totals)


def csv_write(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(row.get(k), ensure_ascii=False) if isinstance(row.get(k), (list, dict))
                             else row.get(k) for k in fields})


def apply_pins(root, rows, config):
    for pin in config.get('pins', []):
        for evidence in pin['evidence']:
            if not (root/evidence).is_file():
                raise ValueError(f'Pinned evidence missing: {evidence}')
        if pin.get('pages_path'):
            pages = root/pin['pages_path']
            ptr = load(pages/'_batch/campaign_latest.json')
            if load(pages/ptr['report'])['signature'] != pin['campaign_signature']:
                raise ValueError(f'Pinned baseline changed: {pages}')
        found = False
        for row in rows:
            if row['path'] == pin['path'] or row['path'].startswith(pin['path']+'/'):
                row.update(action='KEEP', reclaimable_bytes=0)
                row['reasons'].append('PINNED_BASELINE: '+pin['reason'])
                row['references'] = sorted(set(row['references']) | set(pin['evidence']))
                found = True
        if not found:
            raise ValueError(f'Pinned tree not inventoried: {pin["path"]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--out', type=Path, required=True, help='New dedicated report directory; refuses existing outputs')
    parser.add_argument('--reuse-runs-from', type=Path,
                        help='Explicitly reuse earlier run measurements, preserving their timestamp; rescan work only')
    parser.add_argument('--pins', type=Path, default=Path(__file__).with_name('pins.json'))
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    errors = []
    texts, run_refs, active = references(root, errors)
    print(f'reference files: {len(texts)}', flush=True)
    pages = root/'output/character_skills/pages'
    run_measured_at = datetime.now(timezone.utc).isoformat()
    if args.reuse_runs_from:
        previous = load(args.reuse_runs_from/'summary.json')
        if Path(previous['root']).resolve() != root:
            raise ValueError('Cached inventory belongs to a different project')
        runs = load(args.reuse_runs_from/'runs.json')
        actual = {p.relative_to(root).as_posix() for c in COHORTS for p in (pages/'_batch'/c/'runs').iterdir() if p.is_dir()}
        if actual != {r['path'] for r in runs}:
            raise ValueError('Run set changed; full rescan required')
        for row in runs:
            for reason in row['reasons']:
                if reason.startswith('CURRENT_POINTER:'):
                    ptr = root/reason.split(':', 1)[1]
                    if row['run_id'] not in ptr.read_text(encoding='utf-8'):
                        raise ValueError('Current pointer changed; full rescan required')
        run_measured_at = previous.get('run_measured_at', previous['created_at'])
        errors += [issue for issue in load(args.reuse_runs_from/'scan_issues.json') if '/work/' not in issue['path'].replace('\\', '/')]
        print('using explicitly cached run measurements; directory set and current pointers unchanged', flush=True)
    else:
        runs = run_inventory(root, pages, run_refs, errors)
    print('scanning work metadata', flush=True)
    work, top = work_inventory(root, texts, active, errors)
    pins = load(args.pins)
    apply_pins(root, runs + work, pins)
    save(out/'pins.json', pins)
    summary = dict(created_at=datetime.now(timezone.utc).isoformat(), root=str(root),
                   run_measured_at=run_measured_at, reused_run_inventory=str(args.reuse_runs_from) if args.reuse_runs_from else None,
                   scope='Existing pages/_batch/<cohort>/runs and work only; no deletions',
                   measurement='Logical bytes from directory metadata, not physical allocated bytes. No full-content hashes or archive compression estimate.',
                   reference_scope='scripts + docs/tasks + root docs + character_skills/review (.py/.md/.json <=2 MiB); dynamic refs and other chats are not exhaustively known',
                   run_count=len(runs), run_bytes=sum(r['bytes'] for r in runs),
                   work_bytes=sum(r['bytes'] for r in work), reference_files=len(texts), scan_issues=len(errors),
                   immediate_deletion_authorized=False, groups={})
    for label, rows in (('runs', runs), ('work', work)):
        groups = {}
        for action in sorted({r['action'] for r in rows}):
            selected = [r for r in rows if r['action']==action]
            groups[action] = dict(items=len(selected), bytes=sum(r['bytes'] for r in selected),
                                  conditional_reclaimable_bytes=sum(r['reclaimable_bytes'] for r in selected))
        summary['groups'][label] = groups
    save(out/'runs.json', runs)
    save(out/'work.json', work)
    save(out/'work_top_totals.json', top)
    save(out/'scan_issues.json', errors)
    save(out/'summary.json', summary)
    csv_write(out/'runs.csv', runs, ['path','cohort','run_id','signature','action','bytes','backup_payload_bytes',
                                   'reclaimable_bytes','files','failed','reasons','references'])
    csv_write(out/'work.csv', work, ['path','kind','action','bytes','reclaimable_bytes','files','reasons',
                                   'active_tasks','references','parent_references'])
    lines = ['# run / work 清理候选清单（只读）', '',
             '没有删除、搬移或归档任何现有文件。下列空间都是逻辑字节合计；不是无条件可删除量，也不是压缩后的净回收量。', '',
             f'- run：{len(runs)} 个，{summary["run_bytes"]/2**30:.3f} GiB。',
             f'- work：{summary["work_bytes"]/2**30:.3f} GiB。',
             f'- 扫描异常/跳过：{len(errors)}，详见 scan_issues.json。', '',
             '| 范围 | 分类 | 项数 | 当前 GiB | 条件回收上限 GiB |',
             '|---|---|---:|---:|---:|']
    for label, groups in summary['groups'].items():
        for action, group in groups.items():
            lines.append(f'| {label} | {action} | {group["items"]} | {group["bytes"]/2**30:.3f} | {group["conditional_reclaimable_bytes"]/2**30:.3f} |')
    lines += ['', '## 判定与保留理由', '',
              '- KEEP：当前指针、最近两组同签名完整基线、恢复失败/中断或进行中任务；不列为清理对象。最近完整基线不冒充已审版本。',
              '- pins.json 锁定一套实际保有完整页面/账本的历史验收基线，启动盘点时验证其 campaign 签名。历史曾通过不保证后续未发现缺陷。',
              '- run 自身 signature 描述当次新产物；transactions/backup 保存替换前内容。回滚/归档须读 backup/receipt.json 的签名，不能按 run 名字直接恢复。',
              '- CANDIDATE_AFTER_REVIEW：扫描文本未发现具体 run ID 引用的旧备份；仍须核查动态引用与审查闭合后才可处理。',
              '- ARCHIVE_REVIEW：已有文档/审查引用，先保留所需基线或归档并登记来源映射；回收量是迁出 payload 的毛上限。',
              '- REVIEW_REPLAY：work 中名称像 replay/union_build/scratch/sandbox_pages 且未匹配进行中任务的目录；须先分离独有证据，不等于整个目录已证明可删。',
              '- 所有 run 报告、签名、队列、失败记录、before.json、receipt.json 保留。run 回收量仅计 backup/card.json 和 backup/index.html。',
              '- work 的 OTHER 是扣除单列 replay、sandbox、old_pages/cards 与 pages_before 后的互斥剩余文件，不可按该聚合路径执行整目录删除；原生恢复材料、代码快照、旧基线默认保留。',
              f'- run 测量时间：{run_measured_at}；复用前报告：{summary["reused_run_inventory"] or "无"}。复用时复核 run 目录集合和指针，历史大文件不再次扫描，分类沿用原测量。',
              '- 清单不自动判断审查通过；文本引用扫描不覆盖聊天上下文或所有动态拼接路径。清理前重扫，核对活动写入及当前指针。', '',
              '## 文件', '', '- runs.csv / runs.json：每个 run 的路径、大小、候选量、保留理由和具体引用。',
              '- work.csv / work.json：work 互斥分组、保留理由、活动任务和引用。',
              '- work_top_totals.json：work 一级目录原始总量，可与互斥清单对账。',
              '- summary.json / scan_issues.json：机器可读汇总与扫描缺口。', '',
              '## 最大 work 复跑候选', '', '| 路径 | GiB | 状态 |', '|---|---:|---|']
    for row in sorted((r for r in work if r['kind']=='REPLAY_TREE'), key=lambda r:r['bytes'], reverse=True)[:25]:
        lines.append(f'| `{row["path"]}` | {row["bytes"]/2**30:.3f} | {row["action"]} |')
    (out/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True, indent=2), flush=True)


if __name__ == '__main__':
    main()
