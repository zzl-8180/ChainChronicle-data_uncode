"""Compose output/full_unpack/manifest.json from ledger, coverage and validation results.

    .venv\\Scripts\\python.exe -B scripts/full_unpack_finalize.py
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path('output/full_unpack')
SCRIPTS = ['scripts/full_unpack_probe.py', 'scripts/full_unpack_run.py',
           'scripts/full_unpack_merge.py', 'scripts/full_unpack_verify.py',
           'scripts/full_unpack_finalize.py', 'scripts/decode_data5.py',
           'scripts/protection_emulate.py', 'scripts/apk_certificate.py']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    out_dir = args.output
    coverage = json.loads((out_dir / 'coverage.json').read_text(encoding='utf-8'))
    validation = json.loads((out_dir / 'validation.json').read_text(encoding='utf-8'))
    import UnityPy
    from PIL import Image
    import unicorn
    manifest = {
        'task': 'full_unpack_20261016',
        'created_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'input': {
            'composite_inventory': 'output/cache_refresh_20261015/composite_inventory.jsonl',
            'composite_inventory_sha256': sha('output/cache_refresh_20261015/composite_inventory.jsonl'),
            'archives': ['raw/phone_20261015_full_02/external_cache.tar',
                         'raw/phone_20261015_refresh_02/external_cache.tar'],
            'scope': '68993 files listed on phone external cache at refresh time; not a whole-game coverage claim',
        },
        'code_versions': {s: sha(s) for s in SCRIPTS},
        'dependencies': {'UnityPy': UnityPy.__version__, 'Pillow': Image.__version__,
                         'unicorn': unicorn.__version__,
                         'python': '3.12.14 (.venv)'},
        'decode_route': {
            'bdl': 'NativeDecoder.DecodeXorData (native rva 0x2097c, guest emulation) transforms first 256 bytes; result is standard UnityFS; objects exported via UnityPy.',
            'data5': 'Reused verified output/cache_full_20261015_v3/decoded/*.json.raw (native AES + gzip JSON), unchanged in refresh.',
        },
        'coverage': coverage,
        'validation': {'status': validation['status'], 'checks': len(validation['checks'])},
        'outputs': {
            'ledger': 'ledger.jsonl',
            'objects_root': 'objects/',
            'coverage': 'coverage.json',
            'validation': 'validation.json',
            'cid_index': 'cid_index.json',
        },
    }
    (out_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('manifest written; validation:', validation['status'])


if __name__ == '__main__':
    main()
