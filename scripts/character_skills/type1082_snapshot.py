"""Preserve missing/drifted source dependencies without touching old snapshots."""
import ast
import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'work/character_skills_pivot/snapshots/20261019-pre-pivot-a7bf4d21'
SKIP_VERIFIED = {'description_bindings.py', 'batch_bindings.py', 'p3b7_bindings.py',
                 'p3b8_bindings.py', 'p3b9_bindings.py', 'p3b10_bindings.py'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot-name')
    args = parser.parse_args()
    old = json.loads((OLD / 'manifest.json').read_text(encoding='utf-8'))
    frozen = {r['source_path']: r['sha256'] for r in old['files']}
    # Parse source rather than importing modules that can read production outputs.
    pending = [ROOT / p for p in frozen if p.endswith('.py')]
    seen, configs = set(), set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [x.name.split('.')[0] for x in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module.split('.')[0]]
            for name in modules:
                for directory in [path.parent, ROOT/'scripts/character_skills', ROOT/'scripts']:
                    candidate = directory / (name + '.py')
                    if candidate.is_file():
                        pending.append(candidate)
                        break
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                name = node.value
                if name.endswith(('.json', '.js')):
                    # Only code-local configuration; output/raw game files stay external.
                    for candidate in [path.parent/name, ROOT/name]:
                        if candidate.is_file() and candidate.is_relative_to(ROOT/'scripts'):
                            configs.add(candidate)
    selected = sorted(seen | configs | set((ROOT/'scripts/character_skills').glob('type1082*.py')) |
                      {ROOT/'docs/tasks/20261019-character-skills-type1082.md'})
    rows, delta = [], []
    for path in selected:
        rel = path.relative_to(ROOT).as_posix()
        if path.name in SKIP_VERIFIED and rel in frozen:
            status = 'user_verified_old_snapshot_not_rehashed'
            actual = frozen[rel]
        else:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if rel in frozen:
                status = 'unchanged_old_snapshot' if actual == frozen[rel] else 'drift'
            else:
                status = 'missing_from_old_snapshot'
        rows.append(dict(path=rel, sha256=actual, status=status))
        if status in ('drift', 'missing_from_old_snapshot'):
            delta.append(path)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    name = args.snapshot_name or ('20261019-type1082-dependencies-' + stamp)
    if Path(name).name != name:
        raise ValueError('snapshot-name must be one directory name')
    out = OLD.parent / name
    out.mkdir()
    for path in delta:
        dest = out/'files'/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    report = dict(created_at_utc=stamp, old_snapshot=OLD.relative_to(ROOT).as_posix(),
                  scope='AST local import closure of old snapshot Python sources plus code-local json/js literals',
                  excluded='game inputs, output data dependencies, .venv; six user-verified modules not rechecked',
                  source_dependencies=rows, delta_count=len(delta),
                  head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  limitation='source preservation only; no claim HEAD or clean-directory reproduction passes')
    (out/'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (out/'git_status.txt').write_text(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True), encoding='utf-8')
    print(json.dumps(dict(snapshot=out.relative_to(ROOT).as_posix(), dependencies=len(rows), delta=len(delta),
                          changed=[r for r in rows if r['status'] in ('drift','missing_from_old_snapshot')]), ensure_ascii=False))


if __name__ == '__main__':
    main()
