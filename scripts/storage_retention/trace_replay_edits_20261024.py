"""Reconstruct pre-edit sources from inverse edits, accepting only recorded original SHA256."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/storage_retention/replay_safety_20261024'
originals = json.loads((ROOT / 'output/storage_retention/recovery_audit_20261024/script_impact.json').read_text(encoding='utf-8'))
records = []


def rep(s, a, b=''):
    assert s.count(a) == 1, a
    return s.replace(a, b, 1)


for row in originals:
    path = row['source']
    current = (ROOT / path).read_text(encoding='utf-8-sig')
    old = current
    if path.endswith('compare_full_rows.py') or path.endswith('compare_fix_full.py'):
        old = rep(old, 'import sys\n')
        start = old.index('\nsys.path.insert(')
        end = old.index('PAGES = replay.pages\n', start) + len('PAGES = replay.pages\n')
        old = old[:start] + old[end:]
        start = old.index('replay.finish(')
        old = old[:start]
        if path.endswith('compare_full_rows.py'):
            old = rep(old, "replay.out / 'full_row_changes.jsonl', 'x'", "pathlib.Path(__file__).parent / 'full_row_changes.jsonl', 'w'")
        else:
            old = rep(old, "replay.out / 'fix_changes_full.jsonl', 'x'", "pathlib.Path(__file__).parent / 'fix_changes_full.jsonl', 'w'")
    elif path.endswith('compare_zero_change.py'):
        old = rep(old, 'import sys\n')
        old = rep(old, 'ROOT = Path(__file__).resolve().parents[2]\n',
                  "ROOT = Path(r'E:\\代码项目\\锁链战记数据解包')\nPAGES = ROOT / 'output/character_skills/pages'\n")
        start = old.index('sys.path.insert(')
        end = old.index('PAGES = replay.pages\n', start) + len('PAGES = replay.pages\n')
        old = old[:start] + old[end:]
        start = old.index('ok = (stats')
        end = old.index('with open(replay.out', start)
        old = old[:start] + old[end:]
        old = rep(old, "replay.out / 'zero_change_result.json', 'x'", "ROOT / 'work/b8_review_deepseek/zero_change_result.json', 'w'")
        old = rep(old, "rowset=rowset_mismatch, missing=missing_rows,\n                   _replay_guard=dict(replay.stamp(), status='PASS'))", "rowset=rowset_mismatch, missing=missing_rows)")
        old = old[:old.index('replay.finish(True,')]
    elif path.endswith('old_new_diff.py'):
        start = old.index('ROOT = Path(__file__).resolve().parents[2]')
        end = old.index('PAGES = replay.pages\n', start) + len('PAGES = replay.pages\n')
        block = old[start:end]
        dstart = block.index('OLD_RUNS = ')
        dend = block.index('OLD_PAGES = ')
        run_def = block[dstart:dend]
        old = old[:start] + old[end:]
        old = rep(old, "for cohort in ('ge60', '40to59', '20to39', 'remaining'):", run_def + "for cohort in ('ge60', '40to59', '20to39', 'remaining'):")
        old = rep(old, 'run_dir = OLD_PAGES /', 'run_dir = PAGES /')
        old = rep(old, '        # 有事务却无旧文件是缺件，绝不能解释成 REUSED。\n        if not old_path.is_file():\n            raise FileNotFoundError(old_path)\n',
                  '        # REUSED 卡无 transactions/backup；attempt 状态可从 run 报告 attempts 推断，这里\n        # 以 backup/card.json 是否存在判定是否重建。\n        if not old_path.is_file():\n            s[\'reused\'] += 1\n            continue\n')
        old = rep(old, "elif stats['rebuilt'] == 2236:", 'else:')
        old = rep(old, "open(replay.out / 'old_new_diff.json', 'x'", "open('work/character_skills_b8_crit2012/old_new_diff.json', 'w'")
        old = old[:old.index('replay.finish(')]
    elif path.endswith('compare_fix.py'):
        old = rep(old, 'from pathlib import Path\n')
        start = old.index('ROOT = Path(__file__).resolve().parents[2]')
        end = old.index('replay = Replay(__file__, [ROOT / p for p in RUN_DIRS])\n', start) + len('replay = Replay(__file__, [ROOT / p for p in RUN_DIRS])\n')
        old = old[:start] + old[end:]
        old = rep(old, "glob.glob(str(replay.pages / '[0-9]*' / 'card.json'))", "glob.glob('output/character_skills/pages/*/card.json')")
        old = old.replace('if int(c) in CHARAINFO_CIDS', 'if c in CHARAINFO_CIDS')
        old = old[:old.index('\nreplay.finish(')]
    elif path.endswith('make_review_outputs.py'):
        old = rep(old, 'import sys\n')
        start = old.index('ROOT = Path(__file__).resolve().parents[2]')
        end = old.index('CHECKS = REV', start)
        old = old[:start] + "ROOT = Path(r'E:\\代码项目\\锁链战记数据解包')\nWORK = ROOT / 'work/b8_review_deepseek'\nREV = ROOT / 'output/character_skills/review/inference_b8_crit2012_20261021_deepseek'\n" + old[end:]
        old = rep(old, "open(WORK / 'characters.csv', encoding='utf-8-sig')", "open(ROOT / 'output/character_skills/profiles/characters.csv', encoding='utf-8')")
        old = rep(old, 'P = replay.pages', "P = ROOT / 'output/character_skills/pages'")
        old = rep(old, '            raise FileNotFoundError(f)', '            continue')
        old = rep(old, "(WORK / 'yg_remaining_rows.json')", "(ROOT / 'work/character_skills_yg_priority/yg_remaining_rows.json')")
        old = rep(old, "replay.comparison['stats']", "json.loads((WORK / 'zero_change_result.json').read_text(encoding='utf-8'))['stats']")
        for k in ('changed', 'nonb8', 'batch_key'):
            old = rep(old, "replay.comparison['" + k + "']", "json.loads((WORK / 'zero_change_result.json').read_text(encoding='utf-8'))['" + k + "']")
        old = rep(old, "historical_receipt_context=dict(cards=2236, status='HISTORICAL_REFERENCE_NOT_RERUN'", "receipts=dict(cards=2236, status='SUCCESS'")
        start = old.index("    verify_full='NOT_RERUN',")
        end = old.index('\n)', start)
        old = old[:start] + "    verify_full='10/10 PASS'," + old[end:]
        old = rep(old, "for item in ce.values():\n    item['pass_'] = None\n    item['status'] = 'HISTORICAL_REFERENCE_NOT_RERUN'\n")
        old = old[:old.index('replay.finish(')]
    else:
        raise AssertionError(path)
    variants = [old.encode('utf-8'), old.replace('\n', '\r\n').encode('utf-8')]
    variants += [b'\xef\xbb\xbf' + x for x in variants[:]]
    matches = [data for data in variants if hashlib.sha256(data).hexdigest() == row['source_sha256']]
    record = dict(source=path, recorded_original_sha256=row['source_sha256'],
                  current_sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),
                  exact_original_reconstructed=bool(matches))
    if matches:
        before = OUT / 'source_before' / path
        before.parent.mkdir(parents=True, exist_ok=True)
        with before.open('xb') as f:
            f.write(matches[0])
        diff = ''.join(difflib.unified_diff(old.splitlines(True), current.splitlines(True),
                                            fromfile='before/' + path, tofile='after/' + path))
        dest = OUT / 'source_diffs' / (Path(path).parent.name + '_' + Path(path).name + '.diff')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('x', encoding='utf-8') as f:
            f.write(diff)
        record.update(before_copy=str(before.relative_to(ROOT)), diff=str(dest.relative_to(ROOT)))
    records.append(record)
    print(path, 'exact original SHA match:', bool(matches), flush=True)
with (OUT / 'source_traceability.json').open('x', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
assert all(r['exact_original_reconstructed'] for r in records)
