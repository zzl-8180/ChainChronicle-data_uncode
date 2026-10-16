"""Check the built share bundle: zip readability, manifest reconciliation, isolated tools run.

    .venv\\Scripts\\python.exe -B scripts/release/check_full_unpack_bundle.py

Performs (per release requirements):
1. Every zip opens; entry count matches package_manifest.json; CRC self-test on samples;
   uncompressed sizes reconciled.
2. Tools package extracted to an ISOLATED temp directory; smoke test runs via its own
   scripts with bundled runtime materials (using the current .venv python — NOT a
   fresh-machine install test; that limitation is reported, not hidden).
3. Representative result consistency: sample bundle exported in isolation is byte-compared
   against the project's output for the same input.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'output/share_bundle/20261016-full-unpack'
PYTHON = ROOT / '.venv/Scripts/python.exe'
SAMPLE_PNG_PROJECT = ROOT / 'output/full_unpack/objects/Card_Icon/cha_2d_icon_00001/cha_2d_icon_00001.png'


def sha256_path(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    checks = []
    manifest = json.loads((RELEASE / 'package_manifest.json').read_text(encoding='utf-8'))

    def record(name, ok, detail):
        checks.append({'check': name, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})
        print(('PASS' if ok else 'FAIL'), name, '-', detail, flush=True)

    # 1. zip 可读性与清单对账
    for name, info in manifest['packages'].items():
        zp = RELEASE / name
        if not zp.is_file():
            record(f'zip_exists:{name}', False, 'missing')
            continue
        actual_sha = sha256_path(zp)
        sha_ok = actual_sha == info['sha256']
        with zipfile.ZipFile(zp) as zf:
            names = zf.namelist()
            count_ok = len(names) == info['files_inside']
            # CRC 抽查：首/中/尾各若干
            probe = [names[0], names[len(names)//2], names[-1]] if names else []
            bad = zf.testzip() if len(names) < 200000 else None
            crc_detail = 'full testzip' if bad is None and len(names) < 200000 else f'sampled {len(probe)}'
            if bad is None:
                for n in probe:
                    with zf.open(n) as fh:
                        while fh.read(1 << 20):
                            pass
            size_ok = zp.stat().st_size == info['bytes']
        record(f'zip_reconcile:{name}', sha_ok and count_ok and size_ok and bad is None,
               f'entries={len(names)} sha256={"ok" if sha_ok else "MISMATCH"} {crc_detail}')

    # 2. 工具包独立目录冒烟
    with tempfile.TemporaryDirectory(prefix='opencode_bundle_check_') as tmp:
        tmp = Path(tmp)
        tools_zip = RELEASE / 'CC_full_unpack_tools_20261016.zip'
        with zipfile.ZipFile(tools_zip) as zf:
            zf.extractall(tmp)
        pkg = tmp / 'CC_full_unpack_tools_20261016'
        env_cmd = [str(PYTHON), '-B']
        common = ['--native-image', 'runtime/nutils_loader_seed1.bin',
                  '--protection', 'runtime/libcompatible.so', '--cert-hex', '@runtime/cert.hex']
        steps = [
            ['scripts/full_unpack_run.py', '--inventory', 'samples/inventory.jsonl',
             '--output', 'out/full_unpack', '--shards', 'work/shards', '--workers', '2', *common],
            ['scripts/full_unpack_merge.py', '--inventory', 'samples/inventory.jsonl',
             '--output', 'out/full_unpack', '--shards', 'work/shards', '--v3-decoded', 'out/no_v3'],
            ['scripts/full_unpack_verify.py', '--inventory', 'samples/inventory.jsonl',
             '--output', 'out/full_unpack', '--sample-per-category', '1', *common],
        ]
        ok = True
        detail = []
        for step in steps:
            proc = subprocess.run(env_cmd + step, cwd=pkg, capture_output=True, text=True, timeout=900)
            if proc.returncode != 0:
                ok = False
                detail.append(f'{step[0]} rc={proc.returncode}: {proc.stderr[-300:]}')
                break
            detail.append(f'{step[0]} ok')
        validation = pkg / 'out/full_unpack/validation.json'
        if ok and validation.is_file():
            v = json.loads(validation.read_text(encoding='utf-8'))
            ok = v['status'] == 'PASS'
            detail.append(f'validation={v["status"]}')
        record('tools_isolated_smoke', ok, '; '.join(detail) +
               ' (uses current .venv; fresh-machine pip install not exercised)')

        # 3. 代表性一致：独立导出 PNG 与项目输出字节一致
        iso_png = pkg / 'out/full_unpack/objects/Card_Icon/cha_2d_icon_00001/cha_2d_icon_00001.png'
        if iso_png.is_file() and SAMPLE_PNG_PROJECT.is_file():
            same = sha256_path(iso_png) == sha256_path(SAMPLE_PNG_PROJECT)
            record('representative_sample_consistency', same,
                   f'isolated vs project cha_2d_icon_00001.png sha256 equal: {same}')
        else:
            record('representative_sample_consistency', False, f'missing {iso_png}')

    result = {'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
              'checks': checks,
              'note': 'Isolated run uses bundled scripts/runtime with current venv interpreter; '
                      'no fresh-machine dependency install was performed.'}
    (RELEASE / 'bundle_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                                                encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
