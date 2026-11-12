"""Bounded source/data dependency declarations and relocation-safe signatures."""
import ast
import hashlib
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import layout_active, read_path


DATA_DEPENDENCY_RELATIVE = tuple(
    ['output/character_skills/' + p for p in (
        'profiles/profiles.jsonl', 'profiles/records.jsonl', 'profiles/rules.json',
        'links/character_skills.jsonl', 'type1082/native_checks.json',
        'skilllist_types/field_dictionary.json', 'skilllist_types/filter_dictionary.json',
        'boss_attack_types/field_dictionary.json', 'boss_heal_types/field_dictionary.json',
        'remaining_five/field_dictionary.json')]
    + ['output/cache_full_20261015_v3/decoded/' + p + '.data5.json.raw' for p in (
        'charainfo', 'skilllist', 'bossinfo', 'jobabilityinfo', 'worldinfo', 'homelist',
        'extraabilitylist', 'passivelist', 'denju_lblist', 'sympathy_skilllist')]
    + ['output/base_master/' + p for p in (
        '_mdSkill.json', '_mdCharacter.json', '_mdBossInfo.json', '_mdSAbirity.json')]
    + ['output/card_comparison_cid30236/' + p + '.json' for p in (
        'description_effects', 'field_dictionary', 'verified_parameter_views', 'movement/trace')]
    + ['output/character_skills/boss_heal_types/type_rules.json',
       'output/character_skills/boss_heal_types/native_checks.json']
    + ['output/boss_heal/field_dictionary.json', 'output/ordinary_effects/ability7/trace.json',
       'output/cache_full_20261015_v3/records.jsonl']
)


class DependencySignatureError(ValueError):
    pass


def source_paths(root):
    pending = list((root / 'scripts/character_skills').glob('card_page*.py')) + [
        root / 'scripts/build_char_roster.py', root / 'scripts/chica_move_rules.py']
    found = set()
    while pending:
        path = pending.pop()
        if path in found or not path.is_file():
            continue
        found.add(path)
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for name in names:
                for parent in (path.parent, root / 'scripts', root / 'scripts/character_skills'):
                    candidate = parent / (name.replace('.', '/') + '.py')
                    if candidate.is_file():
                        pending.append(candidate)
                        break
    return sorted(found)


def effective_data_root(root, *, data_root=None):
    """Resolve the configured repository root or validate an explicit data binding."""
    root = Path(root).resolve()
    explicit = Path(data_root).resolve() if data_root is not None else None
    if not layout_active():
        return explicit if explicit is not None else root
    configured = read_path(root, root=root).resolve()
    if explicit is not None and explicit != configured:
        raise DependencySignatureError(f'显式数据根与启用布局冲突：{explicit} ≠ {configured}')
    return configured


def data_paths(root, *, logical=False, data_root=None):
    """Return stable logical keys or their read_path-resolved physical files."""
    if logical:
        return [Path(path) for path in DATA_DEPENDENCY_RELATIVE]
    base = effective_data_root(root, data_root=data_root)
    return [read_path(base / path, root=base) for path in DATA_DEPENDENCY_RELATIVE]


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _dependency_snapshot(root, data_root):
    return [(key, path, sha256_file(path) if path.is_file() else 'MISSING')
            for key, path in zip(DATA_DEPENDENCY_RELATIVE, data_paths(root, data_root=data_root), strict=True)]


def _logical_declaration(snapshot):
    return [{'path': key, 'sha256': digest} for key, _, digest in snapshot]


def dependency_declaration(root, *, data_root=None, require_files=False):
    """Build the single ordered declaration used by builders and verifiers."""
    snapshot = _dependency_snapshot(root, data_root)
    missing = [f'{key} ({path})' for key, path, digest in snapshot if digest == 'MISSING']
    if require_files and missing:
        raise DependencySignatureError('依赖文件缺失：' + ', '.join(missing))
    return _logical_declaration(snapshot)


def dependency_signature(declared):
    """Preserve the original dependency signature serialization exactly."""
    return hashlib.sha256(json.dumps(declared, sort_keys=True).encode()).hexdigest()


def generation_signature(manifest_sha256, source_signature):
    return hashlib.sha256((manifest_sha256 + source_signature).encode()).hexdigest()


def campaign_signature(generation, dependency_sig):
    return hashlib.sha256((generation + dependency_sig).encode()).hexdigest()


def _c21_physical_key(key):
    # Frozen C21 four-cohort key spelling, from the 20261109 migration mapping.
    # The active layout may move any of these files without changing this spelling.
    for logical, historical in (
        ('output/cache_full_20261015_v3/', 'projects/unpack/data/cache/cache_full_20261015_v3/'),
        ('output/base_master/', 'projects/unpack/data/apk/base_master/'),
        ('output/card_comparison_cid30236/', 'projects/skill-research/evidence/card_comparison_cid30236/'),
        ('output/boss_heal/', 'projects/skill-research/evidence/boss_heal/'),
        ('output/ordinary_effects/', 'projects/skill-research/evidence/ordinary_effects/'),
    ):
        if key.startswith(logical):
            return historical + key[len(logical):]
    return key


C21_PHYSICAL_DEPENDENCY_KEYS = tuple(map(_c21_physical_key, DATA_DEPENDENCY_RELATIVE))
COHORTS = ('ge60', '40to59', '20to39', 'remaining')
SIGNATURE_FIELDS = ('dependency_signature', 'manifest_sha256', 'source_signature', 'signature')


def valid_sha256(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _error(code, message, **detail):
    return {'code': code, 'message': message, **detail}


def _evaluate_signature_record(record, snapshot, expected_campaign_signature):
    errors = []
    declared_now = _logical_declaration(snapshot)
    result = {
        'ok': False, 'path_format': 'invalid', 'errors': errors,
        'logical_dependency_signature_now': dependency_signature(declared_now),
        'logical_dependencies_now': declared_now,
        'recorded_dependencies_now': [],
        'recomputed_dependency_signature': None,
        'recomputed_campaign_signature': None,
        'missing': [], 'hash_mismatches': [],
    }
    if not isinstance(record, dict):
        errors.append(_error('RECORD_NOT_OBJECT', 'signatures.json 不是对象'))
        return result
    for field in SIGNATURE_FIELDS:
        if not valid_sha256(record.get(field)):
            errors.append(_error('SIGNATURE_FIELD_INVALID', '签名字段不是 64 位小写十六进制', field=field))
    recorded = record.get('data_dependencies')
    if not isinstance(recorded, list):
        errors.append(_error('DEPENDENCY_LIST_NOT_ARRAY', 'data_dependencies 不是数组'))
        return result
    paths = []
    seen = set()
    for index, item in enumerate(recorded):
        if (not isinstance(item, dict) or set(item) != {'path', 'sha256'}
                or not isinstance(item['path'], str) or not valid_sha256(item['sha256'])):
            errors.append(_error('DEPENDENCY_ENTRY_INVALID', '依赖项必须仅含 path 和有效 SHA-256', index=index))
            continue
        path = item['path']
        paths.append(path)
        folded = path.replace(chr(92), '/').casefold()
        if folded in seen:
            errors.append(_error('DUPLICATE_DEPENDENCY_PATH', '依赖清单存在重复路径', index=index, path=path))
        seen.add(folded)
    if len(recorded) != len(DATA_DEPENDENCY_RELATIVE):
        errors.append(_error('DEPENDENCY_COUNT_MISMATCH', '依赖清单数量不是33', actual=len(recorded)))
    if errors:
        return result

    keys = tuple(paths)
    if keys == DATA_DEPENDENCY_RELATIVE:
        result['path_format'] = 'logical'
    elif keys == C21_PHYSICAL_DEPENDENCY_KEYS:
        result['path_format'] = 'physical'
    else:
        differences = [
            {'index': index, 'got': got, 'logical_expected': logical, 'physical_expected': physical}
            for index, (got, logical, physical) in enumerate(
                zip(keys, DATA_DEPENDENCY_RELATIVE, C21_PHYSICAL_DEPENDENCY_KEYS, strict=True))
            if got != logical or got != physical
        ]
        errors.append(_error('MIXED_OR_UNKNOWN_PATH_FORMAT',
                             '完整有序依赖清单不匹配已登记的逻辑或 C21 物理格式',
                             differences=differences))
        return result

    recorded_sig = dependency_signature(recorded)
    if record['dependency_signature'] != recorded_sig:
        errors.append(_error('DEPENDENCY_SIGNATURE_MISMATCH', '原依赖记录数组签名不一致',
                             recorded=record['dependency_signature'], recomputed=recorded_sig))
    recomputed = []
    for index, (item, (_, actual, digest)) in enumerate(zip(recorded, snapshot, strict=True)):
        detail = {'index': index, 'path': item['path'], 'resolved_path': str(actual)}
        if digest == 'MISSING':
            result['missing'].append(detail)
            errors.append(_error('DEPENDENCY_FILE_MISSING', '依赖文件缺失', **detail))
        elif digest != item['sha256']:
            mismatch = {**detail, 'recorded_sha256': item['sha256'], 'actual_sha256': digest}
            result['hash_mismatches'].append(mismatch)
            errors.append(_error('DEPENDENCY_HASH_MISMATCH', '依赖文件内容哈希变化', **mismatch))
        recomputed.append({'path': item['path'], 'sha256': digest})
    result['recorded_dependencies_now'] = recomputed
    result['recomputed_dependency_signature'] = dependency_signature(recomputed)
    generation = generation_signature(record['manifest_sha256'], record['source_signature'])
    recomputed_campaign = campaign_signature(generation, record['dependency_signature'])
    result['recomputed_generation_signature'] = generation
    result['recomputed_campaign_signature'] = recomputed_campaign
    if record['signature'] != recomputed_campaign:
        errors.append(_error('CAMPAIGN_COMPOSITION_MISMATCH', 'campaign 组合签名复算不一致',
                             recorded=record['signature'], recomputed=recomputed_campaign))
    if expected_campaign_signature is not None and record['signature'] != expected_campaign_signature:
        errors.append(_error('CAMPAIGN_SIGNATURE_MISMATCH', '回执签名与 campaign 签名不一致',
                             recorded=record['signature'], expected=expected_campaign_signature))
    result['ok'] = not errors
    return result


def evaluate_signature_record(root, record, *, data_root=None, expected_campaign_signature=None):
    """Validate one record against the bound data, including its original signed array."""
    return _evaluate_signature_record(record, _dependency_snapshot(root, data_root),
                                      expected_campaign_signature)


def evaluate_campaign_records(root, records, *, data_root=None, expected_campaign_signature=None):
    """Validate exactly four cohorts against a common snapshot of the bound data."""
    if not isinstance(records, dict) or set(records) != set(COHORTS):
        return {'ok': False, 'path_formats': {}, 'record_results': {},
                'errors': [_error('COHORT_RECORDS_MISSING', 'cohort 签名回执必须覆盖四个正式组',
                                  expected=COHORTS, actual=list(records) if isinstance(records, dict) else None)]}
    snapshot = _dependency_snapshot(root, data_root)
    record_results = {
        name: _evaluate_signature_record(records[name], snapshot, expected_campaign_signature)
        for name in COHORTS
    }
    errors = [dict(error, cohort=name) for name, result in record_results.items()
              for error in result['errors']]
    formats = {name: result['path_format'] for name, result in record_results.items()}
    if 'invalid' not in formats.values() and len(set(formats.values())) != 1:
        errors.append(_error('GROUP_PATH_FORMAT_MISMATCH', '组间依赖路径格式不一致', formats=formats))
    for field in SIGNATURE_FIELDS:
        values = {name: record.get(field) for name, record in records.items() if isinstance(record, dict)}
        if len(values) == len(COHORTS) and all(map(valid_sha256, values.values())) and len(set(values.values())) != 1:
            errors.append(_error('GROUP_SIGNATURE_MISMATCH', f'组间 {field} 不一致',
                                 field=field, values=values))
    return {'ok': not errors, 'path_formats': formats, 'record_results': record_results,
            'errors': errors}
