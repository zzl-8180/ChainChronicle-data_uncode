"""Supply source-verified parent conditions; never promote selector semantics."""
import argparse
import json
from hashlib import sha256
from pathlib import Path
from rerun_output import read_path, require_new_files, review_output, write_new_text

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def build_conditions(root, out, destination=None):
    destination = destination or out
    sidecar = destination/'data/branch_conditions.js'
    evidence = destination/'audit/player_conditions_20261107/parent_sources.json'
    require_new_files(sidecar, evidence)
    wanted = set()
    observations = []

    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            source = value.get('source')
            if isinstance(source, dict):
                binding = source.get('originalBinding') or {}
                binding = binding.get('g1_b1_binding') or binding.get('c12_p3_skilltext_mirror_binding') or binding
                all_sources = source.get('allSources') or {}
                layer = source.get('layer') or (all_sources.get('layer') if isinstance(all_sources, dict) else None) or binding.get('layer')
                for ident in (source.get('branchId'), source.get('baseBranchId'), binding.get('pattern_id')):
                    if layer in ('APK', 'CACHE') and ident is not None:
                        wanted.add((layer, ident))
                if source.get('conditionsRaw') and source.get('branchId') is not None:
                    observations.append((layer, source['branchId'], source['conditionsRaw']))
            for item in value.values():
                walk(item)

    for file in sorted((out/'data/cards').glob('*.js')):
        walk(json.loads(file.read_text(encoding='utf-8').split(']=', 1)[1].strip().removesuffix(';')))
    walk(json.loads((out/'data/branch_candidates.js').read_text(encoding='utf-8').split('=', 1)[1].strip().removesuffix(';')))
    found, sources = {}, {}
    for layer, relative, pointer in (
        ('APK', 'output/base_master/_mdBossInfo.json', '/bosspattern'),
        ('CACHE', 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw', '/bossinfo/bosspattern'),
    ):
        content = read_path(root/relative, root=root).read_bytes()
        digest = sha256(content).hexdigest()
        master = json.loads(content)
        records = master['bosspattern'] if layer == 'APK' else master['bossinfo']['bosspattern']
        sources[layer] = {'file': relative, 'sha256': digest}
        for index, record in enumerate(records):
            ident = record.get('patternid')
            if (layer, ident) not in wanted:
                continue
            key = f'{layer}:{ident}'
            if key in found:
                raise ValueError(f'Duplicate parent {key}')
            found[key] = {'raw': record, 'source': {'file': relative, 'pointer': f'{pointer}/{index}', 'sha256': digest}}
    for layer, ident, raw in observations:
        if found.get(f'{layer}:{ident}', {}).get('raw') != raw:
            raise ValueError(f'Overlay parent differs from primary record: {layer}:{ident}')
    missing = [f'{layer}:{ident}' for layer, ident in sorted(wanted) if f'{layer}:{ident}' not in found]
    result = {'schema': 1, 'sources': sources, 'records': found, 'missing': missing,
              'scope': 'Exact parent fields only; absence is not zero; conditions do not confirm candidate effect bindings.'}
    write_new_text(sidecar, 'window.CC_BRANCH_CONDITIONS='+json.dumps(result, ensure_ascii=False, separators=(',', ':'))+';\n')
    report = {'requested': len(wanted), 'resolved': len(found), 'missing': missing, 'overlayParentsChecked': len(observations), 'sources': sources}
    write_new_text(evidence, json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, help='Use an explicit stage for both input and new sidecars')
    args = parser.parse_args()
    destination = review_output('branch-conditions', args.output)
    source = destination if args.output else read_path(args.root/'output/character_skills/reader_full_20261106', root=args.root)
    build_conditions(args.root.resolve(), source, destination)
