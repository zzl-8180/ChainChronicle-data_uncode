"""Read-only impact inventory and real-script fail-closed checks; write new evidence only."""
import ast
import csv
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/storage_retention/replay_safety_20261024'
SCRIPTS = [
    'work/20261020-pilot1017/compare_full_rows.py',
    'work/20261020-pilot1017/compare_fix_full.py',
    'work/b8_review_deepseek/compare_zero_change.py',
    'work/b8_review_deepseek/make_review_outputs.py',
    'work/character_skills_b8_crit2012/old_new_diff.py',
    'work/character_skills_b10_rv_fix/compare_fix.py']


def save(name, obj):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def preflight(name='real_script_preflight.json'):
    results = []
    for s in SCRIPTS:
        ast.parse((ROOT / s).read_text(encoding='utf-8-sig'))
        p = subprocess.run([str(ROOT / '.venv/Scripts/python.exe'), '-B', s, '--check-inputs'],
                           cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace',
                           env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        data = json.loads(next(l for l in p.stdout.splitlines() if l.startswith('{')))
        assert p.returncode == 2 and data['status'] == 'BLOCKED', (s, p.returncode, p.stderr)
        results.append(dict(script=s, script_sha256=sha(ROOT / s), exit_code=p.returncode,
                            check=data, stderr=p.stderr))
        print(s, 'BLOCKED', data['missing_count'], 'missing', flush=True)
    save(name, results)
    return results


def inventory():
    original = json.loads((ROOT / 'output/storage_retention/recovery_followup_20261024/remaining_targets.json').read_text(encoding='utf-8'))
    rows = []
    for item in original:
        p = Path(item['path'])
        assert not (ROOT / p).exists(), 'availability changed; re-audit before classifying'
        run = Path(item['group']).name
        cid = p.parts[-3]
        if run.startswith('20261021T110'):
            epoch = 'B8_PRE_BATCH'
            readers = SCRIPTS[2:5]
            evidence = 'output/character_skills/review/inference_b8_crit2012_20261021_deepseek/REPORT.md:140-155'
            impact = '无法重跑完整2236卡/41665行的非批8零变化、行集合不变与批1至7键零改写；最终微修基线不能替代pre-b8基线'
        elif run.startswith('20261020T051'):
            epoch = 'PILOT_INITIAL'
            readers = SCRIPTS[:1]
            evidence = 'output/character_skills/review/inference1017_20261020_deepseek/RECHECK.md:35-48'
            impact = '阻塞首轮试点前后整行全字段对账；独立复验另有12/17字段投影，不能恢复完整card或旧页面'
        elif run.startswith('20261020T05'):
            epoch = 'PILOT_REPAIR'
            readers = SCRIPTS[1:2]
            evidence = 'output/character_skills/review/inference1017_20261020_deepseek/RECHECK.md:35-48'
            impact = '阻塞早期修复轮整行全字段对账；后续完整基线仅比较最后轮次，不能代替早期修复前态'
        elif run.endswith('ee945002'):
            epoch = 'B10_INITIAL_REPAIR'
            readers = SCRIPTS[5:6]
            evidence = 'output/character_skills/review/inference_b10_sa2003_20261022_deepseek/RECHECK.md:86-101;RECHECK2.md:46-57'
            impact = '阻塞实施侧87卡/239行旧态完整比较；独立RECHECK使用coarse signature快照，最终RECHECK2另用已恢复四基线'
        else:
            raise AssertionError(run)
        if p.name == 'card.json':
            if epoch == 'B8_PRE_BATCH':
                priority = 'P1_MUST_RESTORE_INDEPENDENT_BASELINE'
                reason = '独立审查明确使用该旧JSON；要保留该项完整历史复跑能力，必须继续恢复原字节'
            else:
                priority = 'P2_RESTORE_EARLY_FULL_REPLAY'
                reason = '完整复跑该早期轮次必须恢复；当前最终验收不以这些缺件为直接基线，优先级低于P1；不得默认为可删'
        else:
            assert p.name == 'index.html'
            priority = 'P3_RESTORE_IF_OLD_UI_OR_BYTE_ROLLBACK_REQUIRED'
            reason = '六脚本均不读取旧HTML；恢复旧页面字节验证、布局核对或原现场回滚才需该文件；未获可放弃授权'
            readers = []
            impact = '旧页面内容无法重新哈希核对或查看；保留receipt/before哈希只能证明期望值，不能证明丢失字节'
        backup = ROOT / p.parent
        before = json.loads((backup / 'before.json').read_text(encoding='utf-8'))
        receipt = json.loads((backup / 'receipt.json').read_text(encoding='utf-8'))
        assert before[p.name] == receipt['files'][p.name] == item['sha256'], item['path']
        rows.append(dict(path=item['path'], run=run, cohort=p.parts[4], cid=cid,
                         file_type=p.name, size=item['size'], sha256=item['sha256'],
                         priority=priority, historical_epoch=epoch, reason=reason,
                         blocked_assertion=impact, direct_readers=';'.join(readers),
                         review_evidence=evidence, expected_backup_signature=receipt.get('signature'),
                         retained_hash_records_verified=True,
                         action='KEEP_HOLD_NO_DELETE; restore only original SHA256-matching bytes'))
    assert len(rows) == 4072
    save('all_missing_file_impacts.json', rows)
    with (OUT / 'all_missing_file_impacts.csv').open('x', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for prefix in ('P1', 'P2', 'P3'):
        save(prefix + '_recovery_list.json', [r for r in rows if r['priority'].startswith(prefix)])
    summary = []
    for group in sorted({(r['historical_epoch'], r['file_type']) for r in rows}):
        subset = [r for r in rows if (r['historical_epoch'], r['file_type']) == group]
        summary.append(dict(epoch=group[0], type=group[1], files=len(subset),
                            bytes=sum(r['size'] for r in subset), priority=subset[0]['priority']))
    save('impact_summary.json', summary)
    print('inventory', Counter(r['priority'] for r in rows), flush=True)


if __name__ == '__main__':
    if '--validate-only' not in sys.argv:
        inventory()
    preflight('real_script_preflight_final.json' if '--validate-only' in sys.argv else 'real_script_preflight.json')
    before = json.loads((OUT / 'protected_results_before.json').read_text(encoding='utf-8'))
    changed = [p for p, h in before.items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    assert not changed, changed
    save('validation.json', dict(status='PASS', old_results_checked=len(before), old_results_changed=changed,
                                 real_scripts_blocked=6, full_historical_replay_executed=False,
                                 deletions=0, old_review_overwrites=0,
                                 limitations='尚未恢复P1/P2输入，也未配齐对应历史新版本；本轮验证是防缺件与影响核查，不是历史审查重新通过。'))
    print('validation PASS; protected results unchanged', flush=True)
