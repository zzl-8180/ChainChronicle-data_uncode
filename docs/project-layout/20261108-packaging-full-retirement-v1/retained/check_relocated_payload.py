"""New read-only maintenance entry; never imports/runs any historical cleanup module.

Checks the relocated payload manifest against the four unchanged historical plans.
--payload-root is mandatory: no fallback to output/share_bundle is permitted.
The optional frozen verifier is the handoff's documented read-only verifier only.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys

OLD = 'output/share_bundle/20261104-mechanism-first-handoff-r1/payload/manifest.json'
CYCLES = ['c14_c15_20261104', 'c16_20261106', 'c17_c18_20261106', 'c19_20261107']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--payload-root', type=Path, required=True)
    parser.add_argument('--run-frozen-verifier', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve()
    payload = args.payload_root.resolve()
    deny = (repo / 'output/share_bundle').resolve()
    assert not payload.is_relative_to(deny), 'Old share_bundle root is forbidden'
    denied = []

    def audit(event, values):
        if event in {'open', 'os.scandir', 'os.listdir'} and values and isinstance(values[0], (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(values[0])).absolute()
            if p.is_relative_to(deny):
                denied.append(str(p))
                raise RuntimeError('Forbidden old-root access: ' + str(p))
        if event == 'open' and len(values) > 2 and isinstance(values[2], int):
            if values[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                raise RuntimeError('Read-only checker refused a write')

    sys.addaudithook(audit)
    manifest = payload / 'manifest.json'
    data = manifest.read_bytes()
    observed = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    cycles = []
    for cycle in CYCLES:
        plan = repo / ('output/storage_retention/cycle_closeout_' + cycle + '/plan.json')
        frozen = json.loads(plan.read_text(encoding='utf-8'))
        expected = frozen['protected_files'][OLD]
        assert observed == expected, cycle
        cycles.append({'plan':plan.relative_to(repo).as_posix(), 'historical_key': OLD, 'match':True, 'expected':expected})
    checked = 0
    members = json.loads(data)['files']
    actual = {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file() and p != manifest}
    assert actual == set(members)
    for rel, expected in members.items():
        p = (payload / rel).resolve()
        assert p.is_relative_to(payload), rel
        raw = p.read_bytes()
        assert len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], rel
        checked += 1
    verifier = None
    if args.run_frozen_verifier:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            runpy.run_path(str(payload / 'verify_bundle.py'), run_name='__main__')
        verifier = json.loads(out.getvalue())
        assert verifier['passed'] is True
    print(json.dumps({'status':'PASS_READONLY_RELOCATION_SIMULATION' if 'isolated_readback' in payload.parts else 'PASS_RELOCATED_PAYLOAD', 'payload_root':str(payload), 'manifest':observed, 'manifest_members_checked':checked, 'historical_protected_manifest_checks':cycles, 'frozen_verifier':verifier, 'old_root_access_attempts':denied, 'scope':'Only frozen handoff contents and protected-manifest equality. Not a replay of cleanup postchecks, reconciliation, production or whole archive.', 'deleted':0,'moved':0}, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
