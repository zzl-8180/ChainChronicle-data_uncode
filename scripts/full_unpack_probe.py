"""Probe bdl decodability across all Bundle categories with representative samples.

For each category, decode a few samples with the existing NativeDecoder
DecodeXorData path, verify the UnityFS signature, and enumerate object types
via UnityPy. Read-only on inputs; writes a JSON report to work/full_unpack/.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from decode_data5 import NativeDecoder

INVENTORY = Path('output/cache_refresh_20261015/composite_inventory.jsonl')
REPORT = Path('work/full_unpack/probe_report.json')


def category_of(path):
    parts = path.split('/')
    # files/Bundle/<cat>/... or files/Bundle/<cat>/<sub>/...
    return parts[2] if len(parts) >= 4 else '(root)'


def main():
    rows = [json.loads(line) for line in INVENTORY.open(encoding='utf-8')]
    bdl = [r for r in rows if r['path'].endswith('.bdl')]
    by_cat = defaultdict(list)
    for r in bdl:
        by_cat[category_of(r['path'])].append(r)

    decoder = NativeDecoder()
    report = {'categories': {}, 'failures': []}
    import UnityPy

    for cat in sorted(by_cat):
        members = sorted(by_cat[cat], key=lambda r: r['bytes'])
        # 抽样：最小、中位、最大各一
        picks = [members[0], members[len(members)//2], members[-1]]
        cat_info = {'count': len(members), 'samples': []}
        for r in picks:
            sample = {'path': r['path'], 'bytes': r['bytes']}
            try:
                raw = Path(r['work_file']).read_bytes()
                assert len(raw) == r['bytes'], 'size mismatch'
                watermark = decoder.e.heap  # 每样本结束后复位受控堆
                pointer = decoder.e.allocate(len(raw), raw)
                accepted = decoder.call(0x2097c, pointer, len(raw))
                converted = bytes(decoder.e.uc.mem_read(pointer, len(raw)))
                decoder.e.heap = watermark
                sample['accepted'] = accepted
                sample['unityfs'] = converted.startswith(b'UnityFS\0')
                sample['tail_unchanged'] = converted[256:] == raw[256:] if len(raw) > 256 else None
                if sample['unityfs']:
                    env = UnityPy.load(converted)
                    types = Counter(o.type.name for o in env.objects)
                    sample['object_types'] = dict(types)
                    names = [o.peek_name() for o in env.objects][:8]
                    sample['object_names'] = names
                else:
                    sample['header_hex'] = converted[:16].hex()
            except Exception as exc:  # noqa: BLE001 - 探针记录所有异常
                sample['error'] = f'{type(exc).__name__}: {exc}'
                report['failures'].append({'category': cat, **sample})
            cat_info['samples'].append(sample)
        report['categories'][cat] = cat_info
        ok = sum(1 for s in cat_info['samples'] if s.get('unityfs'))
        print(f'{cat:20s} {cat_info["count"]:6d} files, {ok}/{len(picks)} samples UnityFS')

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('report:', REPORT)


if __name__ == '__main__':
    main()
