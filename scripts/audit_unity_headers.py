"""Inspect only the pre-existing MonoBehaviour header failures, preserving raw bytes."""
import hashlib
import json
from pathlib import Path

import UnityPy


def main():
    source = Path('work/apk/assets/bin/Data/data.unity3d')
    evidence = Path('output/unity/mono_errors.jsonl')
    failures = [json.loads(line) for line in evidence.open(encoding='utf-8')]
    wanted = {(row['asset_file'], row['path_id']): row for row in failures}
    assert len(wanted) == len(failures), 'Ambiguous object identities'
    env = UnityPy.load(str(source))
    rows = []
    for obj in env.objects:
        key = (obj.assets_file.name, obj.path_id)
        if key not in wanted:
            continue
        original = wanted[key]
        assert obj.byte_start == original['byte_start']
        assert obj.byte_size == original['byte_size']
        raw = obj.get_raw_data()
        head = obj.parse_monobehaviour_head()
        null = head.m_Script.m_PathID == 0
        rows.append({
            'asset_file': key[0], 'path_id': key[1], 'byte_start': obj.byte_start,
            'byte_size': obj.byte_size, 'script_file_id': head.m_Script.m_FileID,
            'script_path_id': head.m_Script.m_PathID, 'name': head.m_Name,
            'raw_hex': raw.hex(), 'sha256': hashlib.sha256(raw).hexdigest(),
            'original_error': original['error'],
            'classification': 'NULL_SCRIPT_POINTER' if null else 'UNRESOLVED_SCRIPT',
            'meaning_status': 'UNKNOWN; no named gameplay fields established',
        })
    assert len(rows) == len(wanted), 'Missing requested object'
    result = {
        'status': 'TARGETED_READ_COMPLETED', 'source': source.as_posix(),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'basis': 'Only existing error rows; no bulk media export or new target discovery scan',
        'error_list': evidence.as_posix(),
        'error_list_sha256': hashlib.sha256(evidence.read_bytes()).hexdigest(),
        'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'UnityPy': UnityPy.__version__, 'count': len(rows),
        'sizes': sorted({row['byte_size'] for row in rows}),
        'all_null_script': all(row['script_path_id'] == 0 for row in rows),
        'rows': rows,
        'limit': 'Original dereference failures remain; this is not successful typed gameplay parsing or whole-APK coverage proof',
    }
    output = Path('output/field_guide/unity_header_gap_audit.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'count', 'sizes', 'all_null_script')}))


if __name__ == '__main__':
    main()
