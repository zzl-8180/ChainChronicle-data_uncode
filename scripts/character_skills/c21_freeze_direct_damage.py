# -*- coding: utf-8 -*-
"""C21 冻结器：从当前正式来源重新冻结 900 项直接伤害身份。

只写身份，不写 raw
------------------
输出 ``scripts/character_skills/c21_direct_damage_targets.json`` 的每个 target 仅含
``cid``／``row_id``／``effect_id``／``layer``／``reference_field``／``model``。倍率、槽位、
记录 ID、下标、指针、片段 span 一律不写入配置；生产模块运行时从当前 CACHE/APK 原表重导。

两批范围（逐行真实重导，不用旧候选清单）
----------------------------------------
P1 ``DIRECT``（special_move 的 patternN 直接行）
  766 行／517 卡；CACHE 259／APK 507；含 Y.G. 超共鸣直接伤害 10 项。
  逐行门：group=special_move；reference_field=patternN；同层 charainfo 唯一且
  ``charainfo.patternN == skill.record_id``；bosspattern 唯一；行 source 指针等于
  ``/bossinfo/bosspattern/<i>``（CACHE）或 ``/bosspattern/<i>``（APK）且字段为 ``/sinfo``；
  pattern.sinfo＝skill.original_text＝row.context_text（canon）；片段在父文恰出现一次；
  子槽从 0 连续且子记录在全表唯一；恰一个未解 ``ダメージ（词表外）`` 效果；句面形态为
  ``N回ダメージ``（多段 type105/110 且 ``skillparam6==N`` 恰一条）或 ``大／中ダメージ``
  （单发型 type3/22/55/74 恰一条）；类型槽在既有规则中唯一且落在既定伤害槽；原值有限正数；
  本行无同 ``rule_key`` 旧答案。保护卡 30102／20234／30236／30239 零触碰（20234 的
  pattern1 行因此不属于本批）。

P2 ``DENJU_DIRECT``（denju 全文一致的直接链）
  133 行／106 卡，全部 CACHE。逐行门：group=denju；layer=CACHE；skill.record_id==cid；
  denju 记录按 ``denju_id==cid`` 唯一；``patternid0`` 唯一命中 bosspattern；
  ``denju.stext`` 与 ``pattern.sinfo`` **逐字相等**；片段在 stext 恰出现一次；
  子槽连续唯一；形态／``skillparam6``／单发型／规则槽同 P1；原值有限正数；无同规则旧答案；
  保护卡零触碰（30102 的 denju 行因此不属于本批）。

P2 ``DENJU_CONDITION_MIRROR``（唯一条件镜像，CID30304）
  denju 全文与 pattern 全文**不相等**，但首句逐字一致，且当前片段恰为该首句；
  ``patternid0=43030403 → bossskill 43030400 type22 /skillparam1=15``；同卡普通共鸣
  pattern0 行已有同记录同值答案。只此 1 项，独审可单独否决；严格直接 899 项不依赖它。

不纳入：反響、随机／周期／召唤、屏障、回复、增益、异常、skilltext 非唯一镜像、同型多记录
无法唯一选定项。冻结器不猜、不取邻近档位、不为凑数放宽；任何预期数量不符即失败且不写盘。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_SCRIPTS = _HERE.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from project_layout_paths import read_path

import card_page_inference_c20_direct_damage_common as C20

SCHEMA = 'c21-direct-damage-targets-1'
TARGETS_REL = 'scripts/character_skills/c21_direct_damage_targets.json'
SCOPE_P1 = 'C21_P1_SPECIAL_DIRECT_20261111'
SCOPE_P2 = 'C21_P2_DENJU_DIRECT_20261111'
DECODED_REL = C20.CACHE_DECODED
DENJU_FILE = 'denju.data5.json.raw'
PAGES_REL = 'output/character_skills/pages'
RULES_REL = 'output/character_skills/profiles/rules.json'
CARD_PAGE_DATA_REL = 'scripts/character_skills/card_page_data.py'
PATTERN_REF_RX = re.compile(r'^pattern(\d+)$')
DENJU_REFERENCE = 'denju.denju_id == cid'
YG_TITLE_RX = re.compile(r'《Y\.G\.')
MIRROR_CID = 30304
MIRROR_PATTERN_ID = 43030403
MIRROR_RECORD_ID = 43030400
MIRROR_MODEL = 'DENJU_CONDITION_MIRROR'
DIRECT_MODEL = 'DENJU_DIRECT'
P1_MODEL = 'DIRECT'
PROTECTED_CIDS = (30102, 20234, 30236, 30239)

EXPECTED = {
    'total': 900,
    'cids': 518,
    'strict_direct': 899,
    'conditional_mirror': 1,
    'p1_rows': 766,
    'p1_cids': 517,
    'p1_cache': 259,
    'p1_apk': 507,
    'p1_yg': 10,
    'p2_rows': 134,
    'p2_cids': 107,
    'p2_direct': 133,
    'p2_mirror': 1,
}


class FreezeError(RuntimeError):
    pass


def identity(target):
    return {key: target[key] for key in
            ('cid', 'row_id', 'effect_id', 'layer', 'reference_field', 'model')}


def page_cids(view):
    return sorted(int(path.name) for path in view.pages.iterdir()
                  if path.is_dir() and path.name.isdigit())


def card_title(view, cid):
    doc = view.card(cid)
    for field in (doc.get('basic') or {}).get('fields') or []:
        if field.get('key') == 'title':
            return field.get('raw_value')
    return None


def _record_rows(rows, key):
    out = {}
    for i, rec in enumerate(rows):
        out.setdefault(rec.get(key), []).append(i)
    return out


class DenjuTables:
    """CACHE ``denju`` 只读表；哈希与 decode_report 声明一致才使用。"""

    def __init__(self, root, decoded):
        self.root = Path(root).resolve()
        self.decoded = Path(decoded)
        snapshot = self.decoded.parent
        report = json.loads((snapshot / 'decode_report.json').read_text(encoding='utf-8-sig'))
        declared = {item.get('filename'): item.get('json_raw_sha256')
                    for item in report.get('files') or []}
        path = self.decoded / DENJU_FILE
        actual = C20.sha256_file(path)
        want = declared.get('denju.data5')
        if want != actual:
            raise FreezeError('denju 输入哈希与 decode_report 不符：%s' % path)
        self.rows = json.loads(path.read_text(encoding='utf-8-sig'))['denju']
        self.index = _record_rows(self.rows, 'denju_id')
        self.version = {'path': DECODED_REL + '/' + DENJU_FILE,
                        'declared_sha256': want, 'actual_sha256': actual}

    def unique(self, denju_id):
        hits = self.index.get(denju_id) or []
        if len(hits) != 1:
            return None, None, len(hits)
        return self.rows[hits[0]], hits[0], 1


def _children(view, layer, pattern):
    """pattern 的子记录；槽位必须从 0 连续、record 在全表唯一。"""
    slots = [slot for slot in range(7) if pattern.get('skillid%d' % slot)]
    if slots != list(range(len(slots))):
        raise FreezeError('CHILD_SLOTS_NOT_CONTIGUOUS')
    children = []
    for slot in slots:
        record_id = pattern.get('skillid%d' % slot)
        record, index, hits = view.skill(layer, record_id)
        if record is None:
            raise FreezeError('CHILD_RECORD_NOT_UNIQUE:%s:%d' % (record_id, hits))
        children.append({'child_slot': slot, 'record_id': record_id, 'index': index,
                         'type': record.get('skillid0'), 'record': record})
    return children


def _carrier(view, layer, form, detail, parent, model):
    return C20.select_carrier(view, {'form': form, 'form_detail': detail, 'layer': layer,
                                     'target': {'model': model}}, parent)


def _damage_effect(row, table):
    import effect_ledger as LEDGER
    analysis = LEDGER.analyze_row(row, table=table)
    effects = [effect for effect in analysis.get('effects') or []
               if effect.get('record_type') == 'effect'
               and effect.get('effect_type') == 'ダメージ（词表外）'
               and effect.get('status') == 'unresolved']
    return analysis, effects


def scan_p1(view, tally):
    """P1 special_move patternN 直接行。"""
    out = []
    for cid in page_cids(view):
        if cid in PROTECTED_CIDS:
            tally[('P1', 'PROTECTED_CID')] += 1
            continue
        card = view.card(cid)
        for group, skill, row in C20.iter_rows(card):
            if (group.get('group') or skill.get('original_group')) != 'special_move':
                continue
            reference = row.get('reference_field') or ''
            if not PATTERN_REF_RX.match(reference):
                continue
            layer = skill.get('layer')
            form, detail = C20.classify_clause(row.get('japanese'))
            if form not in ('MULTIHIT', 'BIGMID'):
                tally[('P1', 'FORM_NOT_ADMITTED:' + str(form))] += 1
                continue
            try:
                analysis, effects = _damage_effect(row, 'bosspattern')
            except Exception as exc:  # noqa: BLE001
                tally[('P1', 'ANALYZE_ROW_FAILED:' + type(exc).__name__)] += 1
                continue
            if len(effects) != 1:
                tally[('P1', 'DAMAGE_EFFECT_COUNT:%d' % len(effects))] += 1
                continue
            if skill.get('table') != 'bosspattern':
                tally[('P1', 'NOT_BOSSPATTERN')] += 1
                continue
            pattern_id = skill.get('record_id')
            if isinstance(pattern_id, bool) or not isinstance(pattern_id, int) or pattern_id <= 0:
                tally[('P1', 'PATTERN_ID_INVALID')] += 1
                continue
            chara, _chara_index, hits = view.charainfo(layer, cid)
            if chara is None:
                tally[('P1', 'CHARAINFO_NOT_UNIQUE')] += 1
                continue
            if chara.get(reference) != pattern_id:
                tally[('P1', 'CHARAINFO_LINK_MISMATCH')] += 1
                continue
            pattern, pattern_index, hits = view.pattern(layer, pattern_id)
            if pattern is None:
                tally[('P1', 'PATTERN_NOT_UNIQUE')] += 1
                continue
            source = row.get('source') or {}
            pointer = '%s/%d' % (C20.source_prefix(layer, 'bosspattern'), pattern_index)
            if (source.get('json_pointer') != pointer
                    or source.get('field_json_pointer') != pointer + '/sinfo'
                    or source.get('layer') != layer):
                tally[('P1', 'ROW_SOURCE_MISMATCH')] += 1
                continue
            parent_text = str(pattern.get('sinfo') or '')
            if (not parent_text or C20.canon(parent_text) != C20.canon(row.get('context_text'))
                    or C20.canon(parent_text) != C20.canon(skill.get('original_text'))):
                tally[('P1', 'TEXT_MISMATCH')] += 1
                continue
            japanese = str(row.get('japanese') or '')
            if not japanese or parent_text.count(japanese) != 1:
                tally[('P1', 'FRAGMENT_NOT_UNIQUE')] += 1
                continue
            try:
                children = _children(view, layer, pattern)
            except FreezeError as exc:
                tally[('P1', str(exc).split(':')[0])] += 1
                continue
            try:
                selected = _carrier(view, layer, form, detail,
                                    {'pattern_id': pattern_id, 'children': children,
                                     'record': pattern, 'reference_field': reference,
                                     'index': pattern_index}, P1_MODEL)
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                tally[('P1', str(exc).split(':')[0])] += 1
                continue
            same = [answer for answer in row.get('answers') or []
                    if answer.get('rule_key') == selected['rule_key']]
            if same:
                tally[('P1', 'EXISTING_SAME_RULE_ANSWER')] += 1
                continue
            target = {
                'cid': cid, 'row_id': row['row_id'],
                'effect_id': effects[0]['effect_id'], 'layer': layer,
                'reference_field': reference, 'model': P1_MODEL,
            }
            out.append({'target': target, 'record_id': selected['record_id'],
                        'type': selected['type'], 'raw': selected['raw'],
                        'slot': selected['field'], 'pattern_id': pattern_id,
                        'child_slot': selected['child_slot'], 'form': form,
                        'yg': bool(YG_TITLE_RX.search(str(card_title(view, cid) or '')))})
    return out


def scan_p2(view, denju, tally):
    """P2 denju 直接行与唯一条件镜像。"""
    direct, mirror = [], []
    for cid in page_cids(view):
        if cid in PROTECTED_CIDS:
            tally[('P2', 'PROTECTED_CID')] += 1
            continue
        card = view.card(cid)
        record, _index, hits = denju.unique(cid)
        for group, skill, row in C20.iter_rows(card):
            if (group.get('group') or skill.get('original_group')) != 'denju':
                continue
            if skill.get('layer') != 'CACHE':
                tally[('P2', 'LAYER_NOT_CACHE')] += 1
                continue
            if skill.get('record_id') != cid:
                tally[('P2', 'PAGE_RECORD_ID_MISMATCH')] += 1
                continue
            form, detail = C20.classify_clause(row.get('japanese'))
            if form not in ('MULTIHIT', 'BIGMID'):
                tally[('P2', 'FORM_NOT_ADMITTED:' + str(form))] += 1
                continue
            if record is None:
                tally[('P2', 'DENJU_NOT_UNIQUE:%d' % hits)] += 1
                continue
            pattern_id = record.get('patternid0')
            if not pattern_id:
                tally[('P2', 'PATTERNID0_MISSING')] += 1
                continue
            pattern, pattern_index, phits = view.pattern('CACHE', pattern_id)
            if pattern is None:
                tally[('P2', 'PATTERN_NOT_UNIQUE:%d' % phits)] += 1
                continue
            stext = str(record.get('stext') or '')
            sinfo = str(pattern.get('sinfo') or '')
            if not stext or not sinfo:
                tally[('P2', 'TEXT_MISSING')] += 1
                continue
            japanese = str(row.get('japanese') or '')
            if not japanese or stext.count(japanese) != 1:
                tally[('P2', 'FRAGMENT_NOT_UNIQUE')] += 1
                continue
            try:
                analysis, effects = _damage_effect(row, 'denju')
            except Exception as exc:  # noqa: BLE001
                tally[('P2', 'ANALYZE_ROW_FAILED:' + type(exc).__name__)] += 1
                continue
            if len(effects) != 1:
                tally[('P2', 'DAMAGE_EFFECT_COUNT:%d' % len(effects))] += 1
                continue
            try:
                children = _children(view, 'CACHE', pattern)
                selected = _carrier(view, 'CACHE', form, detail,
                                    {'pattern_id': pattern_id, 'children': children,
                                     'record': pattern, 'reference_field': DENJU_REFERENCE,
                                     'index': pattern_index}, DIRECT_MODEL)
            except FreezeError as exc:
                tally[('P2', str(exc).split(':')[0])] += 1
                continue
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                tally[('P2', str(exc).split(':')[0])] += 1
                continue
            same = [answer for answer in row.get('answers') or []
                    if answer.get('rule_key') == selected['rule_key']]
            if same:
                tally[('P2', 'EXISTING_SAME_RULE_ANSWER')] += 1
                continue
            target = {'cid': cid, 'row_id': row['row_id'],
                      'effect_id': effects[0]['effect_id'], 'layer': 'CACHE',
                      'reference_field': DENJU_REFERENCE}
            base = {'target': target, 'record_id': selected['record_id'],
                    'type': selected['type'], 'raw': selected['raw'],
                    'slot': selected['field'], 'pattern_id': pattern_id,
                    'child_slot': selected['child_slot'], 'form': form,
                    'denju_index': _index, 'pattern_index': pattern_index}
            if stext == sinfo:
                target['model'] = DIRECT_MODEL
                direct.append(base)
                continue
            # 条件镜像门：首句逐字一致且当前片段即首句；全文不相等。
            first_text = stext.split('。')[0] + '。'
            first_sinfo = sinfo.split('。')[0] + '。'
            first_ok = (C20.canon(first_text) == C20.canon(first_sinfo)
                        and C20.canon(japanese) == C20.canon(first_text)
                        and C20.canon(stext) != C20.canon(sinfo))
            if not first_ok:
                tally[('P2', 'MIRROR_FIRST_SENTENCE_MISMATCH')] += 1
                continue
            if (cid != MIRROR_CID or pattern_id != MIRROR_PATTERN_ID
                    or selected['record_id'] != MIRROR_RECORD_ID
                    or selected['type'] != 22 or selected['field'] != 'skillparam1'):
                tally[('P2', 'MIRROR_IDENTITY_NOT_FROZEN')] += 1
                continue
            existing_same = []
            for _g, _s, other in C20.iter_rows(card):
                for answer in other.get('answers') or []:
                    if (answer.get('rule_key') == selected['rule_key']
                            and answer.get('record_id') == selected['record_id']
                            and answer.get('raw_value') == selected['raw']
                            and other.get('row_id') != row['row_id']):
                        existing_same.append(other.get('row_id'))
            if not existing_same:
                tally[('P2', 'MIRROR_EXISTING_ANSWER_MISSING')] += 1
                continue
            target['model'] = MIRROR_MODEL
            base['existing_same_rule_rows'] = sorted(set(existing_same))
            mirror.append(base)
    return direct, mirror


def _counts(p1, p2_direct, p2_mirror):
    p1_layers = Counter(item['target']['layer'] for item in p1)
    direct_layers = Counter(item['target']['layer'] for item in p2_direct)
    cids = ({item['target']['cid'] for item in p1}
            | {item['target']['cid'] for item in p2_direct}
            | {item['target']['cid'] for item in p2_mirror})
    return {
        'total': len(p1) + len(p2_direct) + len(p2_mirror),
        'cids': len(cids),
        'strict_direct': len(p1) + len(p2_direct),
        'conditional_mirror': len(p2_mirror),
        'p1': {'rows': len(p1), 'cids': len({i['target']['cid'] for i in p1}),
               'cache': p1_layers.get('CACHE', 0), 'apk': p1_layers.get('APK', 0),
               'yg': sum(1 for item in p1 if item['yg']),
               'multihit': sum(1 for item in p1 if item['form'] == 'MULTIHIT'),
               'bigmid': sum(1 for item in p1 if item['form'] == 'BIGMID')},
        'p2': {'rows': len(p2_direct) + len(p2_mirror),
               'cids': len({i['target']['cid'] for i in p2_direct}
                           | {i['target']['cid'] for i in p2_mirror}),
               'direct': len(p2_direct), 'mirror': len(p2_mirror),
               'cache': direct_layers.get('CACHE', 0) + len(p2_mirror),
               'apk': 0,
               'multihit': sum(1 for item in p2_direct if item['form'] == 'MULTIHIT'),
               'bigmid': sum(1 for item in p2_direct if item['form'] == 'BIGMID')},
    }


def _assert(counts):
    problems = []
    if counts['total'] != EXPECTED['total']:
        problems.append('total=%d want %d' % (counts['total'], EXPECTED['total']))
    if counts['cids'] != EXPECTED['cids']:
        problems.append('cids=%d want %d' % (counts['cids'], EXPECTED['cids']))
    if counts['strict_direct'] != EXPECTED['strict_direct']:
        problems.append('strict_direct=%d want %d'
                        % (counts['strict_direct'], EXPECTED['strict_direct']))
    if counts['conditional_mirror'] != EXPECTED['conditional_mirror']:
        problems.append('conditional_mirror=%d want %d'
                        % (counts['conditional_mirror'], EXPECTED['conditional_mirror']))
    p1, p2 = counts['p1'], counts['p2']
    for key, want in (('rows', EXPECTED['p1_rows']), ('cids', EXPECTED['p1_cids']),
                      ('cache', EXPECTED['p1_cache']), ('apk', EXPECTED['p1_apk']),
                      ('yg', EXPECTED['p1_yg'])):
        if p1[key] != want:
            problems.append('p1.%s=%d want %d' % (key, p1[key], want))
    for key, want in (('rows', EXPECTED['p2_rows']), ('cids', EXPECTED['p2_cids']),
                      ('direct', EXPECTED['p2_direct']), ('mirror', EXPECTED['p2_mirror'])):
        if p2[key] != want:
            problems.append('p2.%s=%d want %d' % (key, p2[key], want))
    if problems:
        raise FreezeError('冻结数量与任务卡不符：' + '; '.join(problems))


def _dedupe(targets, label):
    seen, out = set(), []
    for target in targets:
        key = target['effect_id']
        if key in seen:
            raise FreezeError('%s effect_id 重复：%s' % (label, key))
        seen.add(key)
        out.append(target)
    rows = [target['row_id'] for target in out]
    if len(set(rows)) != len(rows):
        raise FreezeError('%s row_id 重复' % label)
    return out


def scan(root):
    root = Path(root).resolve()
    view = C20.RawView(root)
    denju = DenjuTables(root, view.decoded)
    tally = Counter()
    p1 = scan_p1(view, tally)
    p2_direct, p2_mirror = scan_p2(view, denju, tally)
    counts = _counts(p1, p2_direct, p2_mirror)
    _assert(counts)
    targets = [_dedupe([item['target'] for item in p1], 'P1'),
               _dedupe([item['target'] for item in p2_direct], 'P2-direct'),
               _dedupe([item['target'] for item in p2_mirror], 'P2-mirror')]
    ordered = sorted(targets[0], key=lambda t: (t['cid'], t['row_id']))
    ordered += sorted(targets[1], key=lambda t: (t['cid'], t['row_id']))
    ordered += sorted(targets[2], key=lambda t: (t['cid'], t['row_id']))
    pages = read_path(root / PAGES_REL, root=root)
    campaign_pointer = json.loads((pages / '_batch/campaign_latest.json')
                                  .read_text(encoding='utf-8-sig'))
    campaign = json.loads((pages / campaign_pointer['report']).read_text(encoding='utf-8-sig'))
    rules_path = read_path(root / RULES_REL, root=root)
    doc = {
        'schema': SCHEMA,
        'scope_p1': SCOPE_P1,
        'scope_p2': SCOPE_P2,
        'identity_only': True,
        'identity_keys': ['cid', 'row_id', 'effect_id', 'layer', 'reference_field', 'model'],
        'models': {'p1': P1_MODEL, 'p2_direct': DIRECT_MODEL,
                   'p2_mirror': MIRROR_MODEL},
        'generated_from': {
            'cache_decoded': dict(view.versions.get('CACHE/bossinfo') or {},
                                  denju=denju.version),
            'apk': {key: value for key, value in view.versions.items()
                    if key.startswith('APK/')},
            'pages': {'campaign': campaign.get('signature'), 'path': PAGES_REL},
            'rules': {'path': RULES_REL,
                      'sha256': C20.sha256_file(rules_path),
                      'key_count': len(view.rules)},
            'card_page_data': {'path': CARD_PAGE_DATA_REL,
                               'sha256': C20.sha256_file(root / CARD_PAGE_DATA_REL)},
        },
        'counts': counts,
        'rejection_tally': {'%s|%s' % key: value for key, value in sorted(tally.items())},
        'targets': [identity(target) for target in ordered],
    }
    return doc, {'p1': p1, 'p2_direct': p2_direct, 'p2_mirror': p2_mirror,
                 'tally': tally, 'view': view, 'denju': denju}


def write_targets(root, doc):
    path = Path(root).resolve() / TARGETS_REL
    payload = json.dumps(doc, ensure_ascii=False, indent=1, allow_nan=False) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload.encode('utf-8'))
    return path, C20.sha256_file(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description='C21 直接伤害身份冻结器（只写身份配置）')
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--audit', action='store_true',
                        help='在 work/c21_direct_damage_20261111/ 写逐行审计（可含 raw）')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    doc, detail = scan(root)
    result = {'counts': doc['counts'], 'targets': len(doc['targets'])}
    if args.audit:
        audit_dir = root / 'work/c21_direct_damage_20261111'
        audit_dir.mkdir(parents=True, exist_ok=True)
        audit = {
            'schema': 'c21-freeze-audit-1',
            'counts': doc['counts'],
            'rejection_tally': doc['rejection_tally'],
            'p1': detail['p1'],
            'p2_direct': detail['p2_direct'],
            'p2_mirror': detail['p2_mirror'],
        }
        path = audit_dir / 'freeze_audit.json'
        path.write_bytes((json.dumps(audit, ensure_ascii=False, indent=1,
                                     allow_nan=False) + '\n').encode('utf-8'))
        result['audit'] = str(path)
    if args.write:
        path, digest = write_targets(root, doc)
        result['output'] = str(path)
        result['sha256'] = digest
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        counts = result['counts']
        print('C21 freeze: total=%d cids=%d strict=%d mirror=%d | P1 %d/%d CACHE %d APK %d YG %d'
              % (counts['total'], counts['cids'], counts['strict_direct'],
                 counts['conditional_mirror'], counts['p1']['rows'], counts['p1']['cids'],
                 counts['p1']['cache'], counts['p1']['apk'], counts['p1']['yg']))
        print('            P2 %d/%d direct=%d mirror=%d CACHE=%d'
              % (counts['p2']['rows'], counts['p2']['cids'], counts['p2']['direct'],
                 counts['p2']['mirror'], counts['p2']['cache']))
        if 'output' in result:
            print('wrote %s sha256=%s' % (result['output'], result['sha256']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
