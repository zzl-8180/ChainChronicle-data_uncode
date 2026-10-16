"""Verify full-unpack outputs: ledger completeness, index<->disk consistency, media readability.

    .venv\\Scripts\\python.exe -B scripts/full_unpack_verify.py [--sample-per-category 3]

Checks (writes output/full_unpack/validation.json):
1. ledger covers every inventory row exactly once; bdl statuses all terminal (ok/partial/error).
2. For sampled bundles: every objects_index.json entry's file exists on disk;
   PNG reopens with recorded size/mode; WAV has RIFF/WAVE header; .txt decodes UTF-8;
   .obj/.json parse; AssetBundle m_Container path_ids exist among bundle objects.
3. No output directory contains files not referenced by its objects_index.json (no silent extras/overwrites).
4. Decoded-sha256 spot check: re-decode sampled bdl and compare with ledger value.
"""
import argparse
import hashlib
import json
import random
import struct
import sys
import wave
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INVENTORY = Path('output/cache_refresh_20261015/composite_inventory.jsonl')
OUTPUT = Path('output/full_unpack')


def fail(checks, name, detail):
    checks.append({'check': name, 'status': 'FAIL', 'detail': detail})


def ok(checks, name, detail):
    checks.append({'check': name, 'status': 'PASS', 'detail': detail})


def main():
    global OUTPUT, INVENTORY
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample-per-category', type=int, default=3)
    parser.add_argument('--seed', type=int, default=20261016)
    parser.add_argument('--inventory', type=Path, default=INVENTORY)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--native-image', default=None)
    parser.add_argument('--protection', default=None)
    parser.add_argument('--apk', default=None)
    parser.add_argument('--cert-hex', default=None)
    args = parser.parse_args()

    OUTPUT, INVENTORY = args.output, args.inventory

    checks = []
    rows = [json.loads(line) for line in INVENTORY.open(encoding='utf-8')]
    ledger = [json.loads(line) for line in (OUTPUT / 'ledger.jsonl').open(encoding='utf-8')]

    # 1. 账本完整性
    inv_paths = [r['path'] for r in rows]
    led_paths = [e['path'] for e in ledger]
    if len(ledger) == len(rows) and set(inv_paths) == set(led_paths) and len(set(led_paths)) == len(led_paths):
        ok(checks, 'ledger_completeness', f'{len(ledger)} entries cover all inventory rows uniquely')
    else:
        fail(checks, 'ledger_completeness',
             f'inventory {len(rows)} vs ledger {len(ledger)}, unique {len(set(led_paths))}')

    bdl_entries = [e for e in ledger if e['path'].endswith('.bdl')]
    status_count = Counter(e['processing_status'] for e in bdl_entries)
    non_terminal = [e['path'] for e in bdl_entries if e['processing_status'] == 'not_processed']
    if non_terminal:
        fail(checks, 'bdl_terminal_status', f'{len(non_terminal)} bdl not processed')
    else:
        ok(checks, 'bdl_terminal_status', dict(status_count))

    # 2. 抽样内容检查
    by_cat = defaultdict(list)
    for e in bdl_entries:
        if e['processing_status'] in ('ok', 'partial'):
            by_cat[e['path'].split('/')[2]].append(e)
    rng = random.Random(args.seed)
    sampled = []
    for cat in sorted(by_cat):
        members = by_cat[cat]
        rng.shuffle(members)
        sampled.extend(members[:args.sample_per_category])

    problems = []
    media_stats = Counter()
    for e in sampled:
        out_dir = OUTPUT / e['output_path']
        idx_file = out_dir / 'objects_index.json'
        if not idx_file.is_file():
            problems.append((e['path'], 'objects_index.json missing'))
            continue
        index = json.loads(idx_file.read_text(encoding='utf-8'))
        on_disk = {p.name for p in out_dir.iterdir() if p.is_file() and p.name != 'objects_index.json'}
        referenced = set()
        path_ids = {o['path_id'] for o in index['objects']}
        container_refs = []
        for o in index['objects']:
            candidate_files = []
            if o.get('file'):
                candidate_files.append(o['file'])
            for s in (o.get('audio') or {}).get('saved', []):
                candidate_files.append(s['file'])
            for fn in candidate_files:
                referenced.add(fn)
                target = out_dir / fn
                if not target.is_file():
                    problems.append((e['path'], f'indexed file missing on disk: {fn}'))
                    continue
                if o['type'] == 'Texture2D' and fn.endswith('.png'):
                    try:
                        from PIL import Image
                        with Image.open(target) as img:
                            img.load()
                            t = o['texture']
                            if (img.width, img.height) != (t['width'], t['height']):
                                problems.append((e['path'], f'PNG size mismatch {fn}'))
                            if img.mode != t['image_mode']:
                                problems.append((e['path'], f'PNG mode mismatch {fn}'))
                        media_stats['png_ok'] += 1
                    except Exception as exc:
                        problems.append((e['path'], f'PNG unreadable {fn}: {exc}'))
                elif fn.endswith('.wav'):
                    head = target.read_bytes()[:12]
                    if head[:4] != b'RIFF' or head[8:12] != b'WAVE':
                        problems.append((e['path'], f'WAV header bad {fn}'))
                    else:
                        media_stats['wav_ok'] += 1
                elif fn.endswith('.txt'):
                    try:
                        target.read_text(encoding='utf-8')
                        media_stats['txt_ok'] += 1
                    except UnicodeDecodeError as exc:
                        problems.append((e['path'], f'text decode fail {fn}: {exc}'))
                elif fn.endswith('.obj'):
                    first = target.read_text(encoding='utf-8', errors='strict')[:2]
                    if first not in ('g ', 'v ', 'o ', '#', 'mt'):
                        problems.append((e['path'], f'obj suspicious head {fn}: {first!r}'))
                    else:
                        media_stats['obj_ok'] += 1
                elif fn.endswith('.json'):
                    try:
                        json.loads(target.read_text(encoding='utf-8'))
                        media_stats['json_ok'] += 1
                    except json.JSONDecodeError as exc:
                        problems.append((e['path'], f'json parse fail {fn}: {exc}'))
            if o['type'] == 'AssetBundle':
                for container_path in o.get('container', []):
                    container_refs.append(container_path)
        # 容器条目与对象对应：m_Container 的 asset path_id 应在对象列表
        bundle_obj = [o for o in index['objects'] if o['type'] == 'AssetBundle']
        if bundle_obj:
            bj = json.loads((out_dir / bundle_obj[0]['file']).read_text(encoding='utf-8'))
            for cpath, cval in bj.get('m_Container', []):
                pid = cval.get('asset', {}).get('m_PathID')
                if pid not in path_ids:
                    problems.append((e['path'], f'container {cpath} -> path_id {pid} not in objects'))
        extras = on_disk - referenced
        if extras:
            problems.append((e['path'], f'unreferenced files on disk: {sorted(extras)[:5]}'))

    if problems:
        fail(checks, 'sampled_bundle_consistency', f'{len(problems)} problems in {len(sampled)} sampled bundles',
             )
        checks[-1]['problems'] = problems[:50]
    else:
        ok(checks, 'sampled_bundle_consistency',
           f'{len(sampled)} bundles across {len(by_cat)} categories: index<->disk consistent, media readable',
           )
        checks[-1]['media_stats'] = dict(media_stats)

    # 3. 解码哈希抽查
    from decode_data5 import NativeDecoder
    dec_kw = {}
    if args.native_image:
        dec_kw['image'] = Path(args.native_image)
    if getattr(args, 'protection', None):
        dec_kw['protection'] = Path(args.protection)
    cert_hex = args.cert_hex
    if cert_hex and cert_hex.startswith('@'):
        cert_hex = Path(cert_hex[1:]).read_text(encoding='ascii').strip()
    if cert_hex:
        dec_kw['cert_hex'] = cert_hex
    elif args.apk:
        dec_kw['apk'] = Path(args.apk)
    decoder = NativeDecoder(**dec_kw)
    inv_by_path = {r['path']: r for r in rows}
    hash_problems = []
    for e in sampled[:20]:
        row = inv_by_path[e['path']]
        raw = Path(row['work_file']).read_bytes()
        wm = decoder.e.heap
        p = decoder.e.allocate(len(raw), raw)
        decoder.call(0x2097c, p, len(raw))
        conv = bytes(decoder.e.uc.mem_read(p, len(raw)))
        decoder.e.heap = wm
        digest = hashlib.sha256(conv).hexdigest()
        if digest != e.get('decoded_sha256'):
            hash_problems.append(e['path'])
    if hash_problems:
        fail(checks, 'decoded_sha256_spotcheck', hash_problems)
    else:
        ok(checks, 'decoded_sha256_spotcheck', f'{min(20, len(sampled))} re-decoded bundles match ledger sha256')

    result = {
        'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
        'checks': checks,
        'bdl_status_count': dict(status_count),
        'sampled_bundles': len(sampled),
        'note': 'Samples per category with fixed seed; not a full re-read of all exports.',
    }
    (OUTPUT / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
