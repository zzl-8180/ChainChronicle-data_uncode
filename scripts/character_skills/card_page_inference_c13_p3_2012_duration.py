# -*- coding: utf-8 -*-
"""C13-P3 ``bosspattern`` 档位行 ↔ 同卡 ``charainfo.skilltext`` 同文行：2012 攻速时长镜像（候选）。

任务卡 ``docs/tasks/20261031-c13-p3-2012-duration-mirror.md``；C13 总卡
``docs/tasks/20261031-c13-cycle.md``；候选扫描 ``work/c13_20261031/mirror_scan.json``。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；正式 pages、
``rules.json``、``effect_ledger.py`` 的映射表均未改动；本阶段不运行正式全库生成。

本批做什么、不做什么
--------------------
本批**不是**新数值发现，也**不是**按句面文本或数值回填。三行档位行（``bosspattern`` 行）已有
同一条 ``skilllist`` ability 2012 记录提供的 ``/param6`` 攻速间隔因子答案，账本里同行的
「継続時間」主张仍未解。同卡 ``charainfo.skilltext`` 的**同一句**（同字面）已由既有生产模块
从**同一条 2012 记录**答出 ``/param0 = 30``（``skilllist|2012|/param0``，游戏秒）。本批只把这
一条时长答案按「本档 pattern 自己的链」补到档位行：

* 30255 ``pattern0`` ``…f3``「さらに自身の攻撃速度が一定時間上がる。」
  → pattern 43025500 / slot skillid3 → bossskill 43025503（type13）→ s_ability 43025512。
* 30306 ``pattern0`` ``…f5``「また自身の攻撃速度が一定時間上がる。」
  → pattern 43030600 / slot skillid4 → bossskill 43030604（type13）→ s_ability 43030613。
* 30306 ``pattern1`` ``…f5``（同句）→ pattern 43030601 / slot skillid4 → bossskill 43030607
  （type13）→ s_ability **43030613**（与 pattern0 共享同一子记录）。

**不做**：不重答 ``/param6``（既有答案逐字节保留）；不写最终攻速、动作周期、永久、实际装载或
实机；不把间隔因子当动作周期；不新增规则键（``rules.json`` 已有 ``skilllist|2012|/param0``）；
不改账本映射；不处理其他卡（20234／30102／30236／30239 硬拒绝，30255／30306 之外硬拒绝）。

为什么不能只按文本或数值镜像
----------------------------
三行要求同时成立（任一不符即拒，不做「答一半」）：

1. **同卡同文**：档位行所在 ``bosspattern.sinfo`` 与同卡 ``charainfo.skilltext`` 全文逐字相同
   （30306 ``pattern1`` 为【超共鳴必殺】块，全文与 skilltext **不同**——只要求该**单句**逐字
   相同，并在 gates 里显式披露 ``body_equal_to_skilltext=False``；不把全文镜像当成本行证据）。
2. **同记录**：档位行已有 ``/param6`` 答案与 skilltext 同句行已有 ``/param0`` 答案的
   ``record_id``、``json_pointer``、``raw_record_sha256`` 三者逐项相等，且都等于本档链
   ``pattern → skillidN → bossskill.s_ability → skilllist(ability=2012)`` 唯一命中的记录。
3. **同 slot／同原值**：链上的 type13 子记录 slot 与 ``/param6`` 答案 ``binding.path.slot`` 相等；
   2012 记录 ``param8=64(MYSELF)``、``param7=1``、``flag=0``、无 ``sub``、``param0=30>0``、
   ``param6`` 与本行既有答案原值逐位相等。
4. **同 raw**：按页面 ``source.byte_begin/byte_end_exclusive`` 在
   ``output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw`` 上取字节切片，
   ``sha256`` 必须等于答案里的 ``raw_record_sha256``，且切片解析出的记录与索引记录全等。
   （页面 ``source.original_file`` 标签写作 ``skilllist.data5``，实测字节范围落在解码
   ``.json.raw`` 上；本模块按实测口径核验并在答案里显式标注，不静默改写历史标签。）

因此 30306 两个 pattern 虽然共享 2012 子记录，答案仍各自保留自己的 ``pattern_id``／``slot``／
``boss_id``／``condition_label``，不合并来源、不互相替代。

证据边界
--------
规则本体（``skilllist|2012|/param0``：正 param0 原样传 setSupport2 支持时间、按游戏 delta 扣减、
不乘 Chain）是既有已确认字段局部规则；「本句 → 本档 2012 记录」是结构归属，**推断**。本批
继承同行既有答案的 ``numeric_evidence=推断``／``association_evidence=推断``，不升格。

账本
----
``effect_ledger._RULE_KEY_EFFECT`` **没有** ``skilllist|2012|/param0`` 的显式键映射。但
``analyze_row`` 既有「rule_key 未命中时按 ``quantity_kind``／value 词面回退」的通用路径会把这个
``quantity_kind='持续时间'`` 的答案绑到「継続時間」主张上（与既有 3000／2003 时长答案同一通用
口径，不是本模块新增的映射）。内存干跑：追加本答案后 継続時間 unresolved→has_answer、
攻撃速度（词表外）仍 has_answer、无新 effect 类型、``promotion_keys`` 仍空。本模块**不修改**
``effect_ledger.py``，也不新增专用映射；该通用回退的可接受性由独立审查判定。

接口
----
``tables(data)`` / ``clone_tables(tab)``       CACHE 解码主表只读索引（可注入／深拷贝）。
``pattern_chain(tab, pattern_id)``             档位行 → 子记录链（唯一命中＋槽位连续）。
``evaluate(data, cid, row, *, groups=None, tab=None, ledger=True, scope_cids=None)``  单行判定（不写）。
``build_answers(data, cid, res, *, tab=None)`` 本行候选答案对象（数量＝1）。
``apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None, ledger=True)`` 正式页消费
（候选未接线）。
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from project_layout_paths import read_path

MODULE_VERSION = 'c13_p3_2012_duration_20261031'
#: 候选标记：本模块**未**接入共享接线，正式生成前不得当作已交付规则。
CANDIDATE_ONLY = True
#: 本批证据 scope（写进答案 ``evidence_scope``）。
SCOPE = 'C13_P3_2012_DURATION_MIRROR_20261031'
#: 结构判定自身 scope（只出现在 binding 里，供逐行溯源）。
STRUCTURE_SCOPE = 'C13_P3_2012_DURATION_STRUCTURE_20261031'
#: 答案内 binding 的键名（**不**写行级 ``inference_*`` 顶层键：那会变成账本 promotion_key）。
BINDING_KEY = 'c13_p3_2012_duration_binding'

#: 行所在层与表（本批只认 CACHE ``bossinfo.bosspattern`` 行）。
TABLE = 'bosspattern'
LAYER = 'CACHE'
GROUP = 'special_move'
REF_PREFIX = 'pattern'
SKILLTEXT_TABLE = 'charainfo'
SKILLTEXT_FIELD = 'skilltext'
SOURCE_KEY = 'CACHE/bossinfo.data5.json.raw'
SKILLLIST_SOURCE_KEY = 'CACHE/skilllist.data5.json.raw'
CHARAINFO_SOURCE_KEY = 'CACHE/charainfo.data5.json.raw'
CACHE_DIR = 'output/cache_full_20261015_v3/decoded'
SNAPSHOT_ID = 'cache_full_20261015_v3'

#: 保护／禁推卡：判定前硬拒绝（30102 禁推卡；30236／30239 保护卡；20234 既有边界）。
ZERO_TOUCH_CIDS = frozenset({20234, 30102, 30236, 30239})
#: 本批卡级边界（不是数值查找表）：只有这两张卡的该句行可被接受。
SCOPE_CIDS = frozenset({30255, 30306})

#: 目标键（既有已确认规则；本模块不新增规则键）。
TARGET_RULE_KEY = 'skilllist|2012|/param0'
PEER_PARAM6_RULE_KEY = 'skilllist|2012|/param6'
TARGET_FIELD = '/param0'
PEER_PARAM6_FIELD = '/param6'
PARAM0_EXPECTED = 30

#: 账本词面效果类型（只读核对，不改映射）。
EFFECT_DURATION = '継続時間'
EFFECT_SPEED = '攻撃速度（词表外）'

#: 目标单句模板：只认「さらに／また + 自身 + 攻撃速度 + 一定時間上がる。」整句。
SELF_SPEED_RE = re.compile(r'^(?:さらに|また)自身の攻撃速度が一定時間上がる。$')
#: 值文禁写项（不得把时长写成最终攻速／周期／永久／装载）。
FORBIDDEN_VALUE_WORDS = ('最终攻速', '永久', '动作周期', '实际装载', '实机', '面板',
                         '最终伤害', '最终HP', '间隔因子', '每击周期')
#: 允许出现在目标行上的既有答案键（本批只认这一条既有答案）。
ALLOWED_EXISTING_KEYS = frozenset({PEER_PARAM6_RULE_KEY})
EVIDENCE = [
    'docs/tasks/20261031-c13-p3-2012-duration-mirror.md',
    'work/c13_20261031/mirror_scan.json',
    'output/character_skills/profiles/rules.json',
    'output/ordinary_effects/ability2012/README.md',
]
LIMIT = ('原值为既有已确认字段局部规则的输入（正 param0＝Support2 支持时间，游戏秒，按游戏 '
         'delta 扣减，不乘 Chain）；「本句 → 本档 2012 记录」为结构归属，关联＝推断。不证明最终 '
         '攻速、动作／每击周期、永久、实际装载、实机、超上限或最终扣血；不宣称整行完整。'
         '30306 pattern0／pattern1 共享 2012 子记录但来源分别按各自 pattern／slot 保留。'
         '账本无 ``skilllist|2012|/param0`` 显式键映射，靠既有 quantity_kind 词面回退消费；'
         '本模块不改共享账本，该回退口径由独立审查判定。')

_TABLES = {}


# ---------------------------------------------------------------- 基础工具
def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def canon(text):
    """NFKC＋去空白（句面比较口径；与既有模块一致）。"""
    return re.sub(r'\s+', '', str(text or ''))


def num_state(value, present=True):
    """缺失／null／布尔／非有限／有限 分开标注（不把任何一档补成 0）。"""
    if not present:
        return 'MISSING'
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'NON_FINITE'
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 'NON_FINITE'
    return 'FINITE' if math.isfinite(f) else 'NON_FINITE'


def num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


# ---------------------------------------------------------------- 只读主表
def tables(data):
    """CACHE 解码主表（按 root 缓存；只读）。索引均为 ``id -> [(array_index, record)]``。"""
    root = Path(getattr(data, 'root', Path('.'))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = read_path(root / CACHE_DIR, root=root)
        paths = {
            SOURCE_KEY: base / 'bossinfo.data5.json.raw',
            SKILLLIST_SOURCE_KEY: base / 'skilllist.data5.json.raw',
            CHARAINFO_SOURCE_KEY: base / 'charainfo.data5.json.raw',
        }
        missing = [str(p) for p in paths.values() if not p.exists()]
        if missing:
            raise FileNotFoundError('CACHE 解码主表缺失: %s' % missing)
        boss = _read(paths[SOURCE_KEY])['bossinfo']
        chara_all = _read(paths[CHARAINFO_SOURCE_KEY])['charainfo']
        patterns, boss_skills, skilllist, chara = {}, {}, {}, {}
        for i, rec in enumerate(boss.get('bosspattern') or []):
            patterns.setdefault(rec.get('patternid'), []).append((i, rec))
        for i, rec in enumerate(boss.get('bossskill') or []):
            boss_skills.setdefault(rec.get('skillid'), []).append((i, rec))
        for i, rec in enumerate(_read(paths[SKILLLIST_SOURCE_KEY])['skilllist']):
            skilllist.setdefault(rec.get('skillid'), []).append((i, rec))
        for i, rec in enumerate(chara_all):
            chara.setdefault(rec.get('cid'), []).append((i, rec))
        _TABLES[key] = dict(root=root, paths=paths, patterns=patterns,
                            boss_skills=boss_skills, skilllist=skilllist,
                            chara=chara, chara_all=chara_all, byte_cache={})
    return _TABLES[key]


def clone_tables(tab):
    """深拷贝主表索引（反例用例在副本上篡改，不动只读缓存）。用 deepcopy 保留 int 键。"""
    out = {}
    for name in ('patterns', 'boss_skills', 'skilllist', 'chara', 'chara_all'):
        out[name] = copy.deepcopy(tab[name])
    out.update(root=tab['root'], paths=tab['paths'], byte_cache={})
    return out


def unique_hit(index, record_id):
    hits = index.get(record_id) or []
    if len(hits) != 1:
        return None, 'NOT_UNIQUE(%d)' % len(hits)
    return hits[0], None


def resolve_pointer(doc, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        return None, 'POINTER_FORMAT'
    node = doc
    for part in pointer.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(node, list):
            try:
                i = int(part)
            except ValueError:
                return None, 'POINTER_INDEX'
            if not 0 <= i < len(node):
                return None, 'POINTER_RANGE'
            node = node[i]
        elif isinstance(node, dict):
            if part not in node:
                return None, 'POINTER_KEY'
            node = node[part]
        else:
            return None, 'POINTER_TYPE'
    return node, None


def file_sha256(tab, source_key):
    """整份解码 JSON 字节的 sha256（只读、带缓存；供来源清单核对）。"""
    cache = tab.setdefault('byte_cache', {})
    if source_key not in cache:
        cache[source_key] = Path(tab['paths'][source_key]).read_bytes()
    return hashlib.sha256(cache[source_key]).hexdigest()


def raw_bytes(tab, source_key, begin, end):
    """按页面记录的字节范围读取解码 JSON 原始字节（只读、带缓存）。"""
    if source_key not in tab['paths']:
        return None, 'SOURCE_KEY_UNKNOWN'
    if not isinstance(begin, int) or isinstance(begin, bool):
        return None, 'BYTE_BEGIN_INVALID'
    if not isinstance(end, int) or isinstance(end, bool):
        return None, 'BYTE_END_INVALID'
    if begin < 0 or end <= begin:
        return None, 'BYTE_RANGE_INVALID'
    cache = tab.setdefault('byte_cache', {})
    if source_key not in cache:
        cache[source_key] = Path(tab['paths'][source_key]).read_bytes()
    blob = cache[source_key]
    if end > len(blob):
        return None, 'BYTE_RANGE_OUT_OF_FILE'
    return blob[begin:end], None


def card_entries(groups):
    """``[(group_name, skill, row)]``（顺序即页面顺序）。"""
    out = []
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                out.append((group.get('group'), skill, row))
    return out


# ---------------------------------------------------------------- 记录链
def pattern_chain(tab, pattern_id):
    """档位行 bosspattern→skillidN→bossskill 链（唯一命中＋槽位从 0 连续）。"""
    hit, err = unique_hit(tab['patterns'], pattern_id)
    if err:
        return None, 'PATTERN_RECORD_%s' % err
    index, pattern = hit
    slots = [(i, pattern.get('skillid%d' % i)) for i in range(10)
             if pattern.get('skillid%d' % i) is not None]
    if [i for i, _ in slots] != list(range(len(slots))):
        return None, 'PATTERN_SLOT_NOT_CONTIGUOUS'
    if not slots:
        return None, 'PATTERN_NO_SLOT'
    children = []
    for slot_index, skill_id in slots:
        child_hit, child_err = unique_hit(tab['boss_skills'], skill_id)
        if child_err:
            return None, 'BOSSSKILL_%s_%s' % (skill_id, child_err)
        child_index, child = child_hit
        children.append(dict(slot='skillid%d' % slot_index, skillid=skill_id,
                             index=child_index, type=child.get('skillid0'),
                             record=child))
    return dict(pattern_id=pattern_id, pattern=pattern, index=index,
                children=children), None


def carrier_from_chain(chain):
    """取链上的 type13 子记录（唯一时才允许作为 2012 的 ``s_ability`` 中继）。"""
    return [c for c in chain['children'] if c['type'] == 13]


def _reject(code, gates, detail=None):
    return {'accepted': False, 'rejection': code, 'detail': detail, 'gates': gates}


# ---------------------------------------------------------------- 单行判定
def evaluate(data, cid, row, *, groups=None, tab=None, ledger=True, scope_cids=None):
    """单行判定（不写入）。``groups`` 为该卡页面 ``groups``；``scope_cids`` 由调用方显式声明。

    判定顺序（任一不符即拒）：
      D0 卡级边界：cid 合法／非零触碰卡／在 ``SCOPE_CIDS``／在调用方声明 scope；
      D1 行身份＋层＋skill 表／slot 字段；
      D2 单句模板（只认「さらに／また自身の攻撃速度が一定時間上がる。」）；
      D3 档位行原记录：patternid 唯一命中、页面指针、正文全文、出现次数、source_position；
      D4 同卡 skilltext 同文行：charainfo 唯一命中、指针、全文、同句唯一；
      D5 原记录链：pattern→skillidN→bossskill(type13)→s_ability→skilllist(2012)，逐项参数；
      D6 本行既有 param6 答案 = 同一记录／指针／sha／原值，且 binding.path 与链一致；
      D7 同句 skilltext 行既有 param6 与 param0 答案 = 同一记录／指针／sha／原值；
      D8 同 raw：按字节范围重算 sha256 并回读切片记录；
      D9 批前未答＋旧答案保护＋幂等；
      D10 账本基线（継続時間恰一次未解、攻撃速度恰一次已答；不改映射）。
    """
    gates = {'cid': cid, 'row_id': (row or {}).get('row_id') if isinstance(row, dict) else None}

    # ---- D0 卡级边界
    if isinstance(cid, bool) or not isinstance(cid, int):
        return _reject('CID_INVALID', gates)
    if cid in ZERO_TOUCH_CIDS:
        return _reject('ZERO_TOUCH_CID', gates)
    if cid not in SCOPE_CIDS:
        return _reject('CID_OUTSIDE_BATCH', gates, {'scope': sorted(SCOPE_CIDS)})
    if scope_cids is None:
        return _reject('NO_SCOPE_DECLARED', gates)
    if isinstance(scope_cids, (str, bytes)):
        return _reject('SCOPE_INVALID', gates)
    try:
        declared = frozenset(scope_cids)
    except TypeError:
        return _reject('SCOPE_INVALID', gates)
    if cid not in declared:
        return _reject('CID_NOT_IN_DECLARED_SCOPE', gates, {'scope': sorted(map(str, declared))})

    if not isinstance(row, dict) or not row.get('row_id'):
        return _reject('ROW_INVALID', gates)
    tab = tab or tables(data)
    entries = card_entries(groups)
    if not entries:
        return _reject('GROUPS_REQUIRED', gates)
    mine = [e for e in entries if e[2] is row]
    if len(mine) != 1:
        same_id = [e for e in entries if e[2].get('row_id') == row.get('row_id')]
        if len(same_id) > 1:
            return _reject('ROW_ID_DUPLICATE', gates)
        if not same_id:
            return _reject('ROW_NOT_IN_GROUPS', gates)
        mine = same_id
    group_name, skill, row = mine[0]

    # ---- D1 行身份＋层＋skill 表／slot
    if group_name != GROUP or row.get('group') != GROUP:
        return _reject('GROUP_MISMATCH', gates)
    if row.get('cid') != cid:
        return _reject('CID_MISMATCH', gates, {'row_cid': row.get('cid')})
    ref = str(row.get('reference_field') or '')
    skill_ref = str(skill.get('reference_field') or '')
    if not ref.startswith(REF_PREFIX) or ref != skill_ref:
        return _reject('ROW_REFERENCE_FIELD_DRIFT', gates,
                       {'row': ref, 'skill': skill_ref})
    if skill.get('table') != TABLE or skill.get('layer') != LAYER:
        return _reject('SKILL_TABLE_LAYER_DRIFT', gates,
                       {'table': skill.get('table'), 'layer': skill.get('layer')})
    ssrc = skill.get('source') or {}
    if ssrc.get('layer') != LAYER or ssrc.get('source_key') != SOURCE_KEY:
        return _reject('SKILL_SOURCE_DRIFT', gates)
    rsrc = row.get('source') or {}
    if rsrc.get('layer') != LAYER or rsrc.get('source_key') != SOURCE_KEY:
        return _reject('ROW_SOURCE_DRIFT', gates)
    if str(rsrc.get('field') or '') != '/sinfo':
        return _reject('ROW_SOURCE_FIELD_DRIFT', gates, {'field': rsrc.get('field')})
    if str(rsrc.get('json_pointer') or '') != str(ssrc.get('json_pointer') or ''):
        return _reject('ROW_SKILL_POINTER_DRIFT', gates,
                       {'row': rsrc.get('json_pointer'), 'skill': ssrc.get('json_pointer')})

    # ---- D2 单句模板
    text = canon(row.get('japanese'))
    if not text or not SELF_SPEED_RE.match(text):
        return _reject('CLAUSE_UNSUPPORTED', gates, {'japanese': row.get('japanese')})
    if text.count('攻撃速度') != 1 or text.count('一定時間') != 1:
        return _reject('CLAUSE_WORD_COUNT', gates, {'japanese': row.get('japanese')})
    gates['clause'] = {'japanese': row.get('japanese'), 'canon': text}

    # ---- D3 档位行原记录
    pattern_id = skill.get('record_id')
    if isinstance(pattern_id, bool) or not isinstance(pattern_id, int):
        return _reject('PATTERN_ID_INVALID', gates, {'record_id': pattern_id})
    chain, chain_err = pattern_chain(tab, pattern_id)
    if chain_err:
        return _reject('CHAIN_%s' % chain_err, gates)
    pattern = chain['pattern']
    pointer = '/bossinfo/bosspattern/%d' % chain['index']
    if str(ssrc.get('json_pointer') or '') != pointer:
        return _reject('PATTERN_POINTER_DRIFT', gates,
                       {'page': ssrc.get('json_pointer'), 'actual': pointer})
    if str(rsrc.get('field_json_pointer') or '') != pointer + '/sinfo':
        return _reject('ROW_FIELD_POINTER_DRIFT', gates,
                       {'row': rsrc.get('field_json_pointer'), 'actual': pointer + '/sinfo'})
    body = pattern.get('sinfo') or ''
    if not canon(body):
        return _reject('PATTERN_TEXT_MISSING', gates)
    if str(skill.get('original_text') or '') != body:
        return _reject('PATTERN_TEXT_DRIFT', gates,
                       {'skill_chars': len(skill.get('original_text') or ''), 'raw_chars': len(body)})
    if canon(row.get('context_text')) != canon(body):
        return _reject('CONTEXT_TEXT_DRIFT', gates)
    if canon(body).count(text) != 1:
        return _reject('CLAUSE_OCCURRENCE(%d)' % canon(body).count(text), gates)
    positions = fragment_positions(body)
    ordinal = row.get('fragment_index')
    position = row.get('source_position') or {}
    if (isinstance(ordinal, bool) or not isinstance(ordinal, int)
            or not 0 <= ordinal < len(positions)):
        return _reject('FRAGMENT_INDEX_INVALID', gates, {'fragment_index': ordinal})
    expected = positions[ordinal]
    if (canon(position.get('japanese')) != canon(expected['japanese'])
            or position.get('raw_span') != expected['raw_span']
            or position.get('clean_span') != expected['clean_span']
            or canon(expected['japanese']) != text):
        return _reject('SOURCE_POSITION_DRIFT', gates,
                       {'page': position, 'actual': expected})
    gates['pattern'] = {'pattern_id': pattern_id, 'index': chain['index'],
                        'pointer': pointer, 'reference_field': ref,
                        'fragment_index': ordinal,
                        'child_ids': [c['skillid'] for c in chain['children']],
                        'child_types': [c['type'] for c in chain['children']]}

    # ---- D4 同卡 skilltext 同文行
    chara_hit, chara_err = unique_hit(tab['chara'], cid)
    if chara_err:
        return _reject('CHARAINFO_RECORD_%s' % chara_err, gates)
    chara_index, chara = chara_hit
    skilltext_skills = [s for g in (groups or []) for s in (g.get('skills') or [])
                        if str(s.get('reference_field') or '') == SKILLTEXT_FIELD]
    if len(skilltext_skills) != 1:
        return _reject('SKILLTEXT_SKILL_NOT_UNIQUE(%d)' % len(skilltext_skills), gates)
    text_skill = skilltext_skills[0]
    if text_skill.get('table') != SKILLTEXT_TABLE or text_skill.get('layer') != LAYER:
        return _reject('SKILLTEXT_TABLE_LAYER_DRIFT', gates)
    if text_skill.get('record_id') != cid:
        return _reject('SKILLTEXT_RECORD_ID_DRIFT', gates, {'record_id': text_skill.get('record_id')})
    tsrc = text_skill.get('source') or {}
    chara_pointer = '/charainfo/%d' % chara_index
    if str(tsrc.get('json_pointer') or '') != chara_pointer:
        return _reject('CHARAINFO_POINTER_DRIFT', gates,
                       {'page': tsrc.get('json_pointer'), 'actual': chara_pointer})
    full = chara.get('skilltext') or ''
    if not canon(full):
        return _reject('CHARAINFO_TEXT_MISSING', gates)
    if str(text_skill.get('original_text') or '') != full:
        return _reject('CHARAINFO_TEXT_DRIFT', gates)
    peers = [r for r in (text_skill.get('rows') or [])
             if isinstance(r, dict) and canon(r.get('japanese')) == text]
    if not peers:
        return _reject('SKILLTEXT_PEER_MISSING', gates, {'japanese': text})
    if len(peers) != 1:
        return _reject('SKILLTEXT_PEER_NOT_UNIQUE(%d)' % len(peers), gates)
    peer_row = peers[0]
    if peer_row.get('cid') != cid or canon(peer_row.get('context_text')) != canon(full):
        return _reject('SKILLTEXT_PEER_IDENTITY_DRIFT', gates)
    psrc = peer_row.get('source') or {}
    if str(psrc.get('field') or '') != '/' + SKILLTEXT_FIELD:
        return _reject('SKILLTEXT_PEER_SOURCE_FIELD_DRIFT', gates)
    if canon(full).count(text) != 1:
        return _reject('SKILLTEXT_PEER_OCCURRENCE(%d)' % canon(full).count(text), gates)
    peer_positions = fragment_positions(full)
    peer_ordinal = peer_row.get('fragment_index')
    peer_position = peer_row.get('source_position') or {}
    if (isinstance(peer_ordinal, bool) or not isinstance(peer_ordinal, int)
            or not 0 <= peer_ordinal < len(peer_positions)):
        return _reject('SKILLTEXT_FRAGMENT_INDEX_INVALID', gates)
    peer_expected = peer_positions[peer_ordinal]
    if (canon(peer_position.get('japanese')) != canon(peer_expected['japanese'])
            or peer_position.get('raw_span') != peer_expected['raw_span']
            or peer_position.get('clean_span') != peer_expected['clean_span']):
        return _reject('SKILLTEXT_SOURCE_POSITION_DRIFT', gates,
                       {'page': peer_position, 'actual': peer_expected})
    gates['skilltext'] = {'window_index': chara_index, 'pointer': chara_pointer,
                          'peer_row_id': peer_row.get('row_id'),
                          'peer_fragment_index': peer_ordinal,
                          'body_equal_to_skilltext': canon(body) == canon(full),
                          'body_chars': len(body), 'skilltext_chars': len(full)}

    # ---- D5 原记录链：pattern→bossskill(type13)→s_ability→skilllist(2012)
    children13 = carrier_from_chain(chain)
    if len(children13) != 1:
        return _reject('CHAIN_TYPE13_NOT_UNIQUE(%d)' % len(children13), gates)
    b13 = children13[0]
    relay_id = b13['record'].get('s_ability')
    if isinstance(relay_id, bool) or not isinstance(relay_id, int) or relay_id <= 0:
        return _reject('CHAIN_2012_RELAY_MISSING', gates, {'s_ability': relay_id})
    record_hit, record_err = unique_hit(tab['skilllist'], relay_id)
    if record_err:
        return _reject('CHAIN_2012_%s' % record_err, gates, {'record_id': relay_id})
    record_index, record = record_hit
    if record.get('ability') != 2012:
        return _reject('CHAIN_2012_ABILITY_DRIFT', gates, {'ability': record.get('ability')})
    if record.get('flag') != 0:
        return _reject('CHAIN_2012_FLAG_DRIFT', gates, {'flag': record.get('flag')})
    if record.get('param8') != 64:
        return _reject('CHAIN_2012_TARGET_DRIFT', gates, {'param8': record.get('param8')})
    if num(record.get('param7')) != 1:
        return _reject('CHAIN_2012_PARAM7_DRIFT', gates, {'param7': record.get('param7')})
    if record.get('iParam0') not in (None, 0):
        return _reject('CHAIN_2012_IPARAM0_DRIFT', gates, {'iParam0': record.get('iParam0')})
    sub = record.get('sub')
    if sub not in (None, []):
        return _reject('CHAIN_2012_SUB_NOT_EMPTY', gates, {'sub': sub})
    p0 = record.get('param0')
    p0_state = num_state(p0, present='param0' in record)
    gates['chain'] = {'pattern_id': pattern_id, 'slot': b13['slot'],
                      'boss_id': b13['skillid'], 'boss_index': b13['index'],
                      'boss_type': b13['type'], 's_ability': relay_id,
                      'record_id': relay_id, 'record_index': record_index,
                      'record_pointer': '/skilllist/%d' % record_index,
                      'param0': {'raw': p0, 'state': p0_state},
                      'param6': {'raw': record.get('param6'),
                                 'state': num_state(record.get('param6'),
                                                    present='param6' in record)},
                      'child_ids': [c['skillid'] for c in chain['children']],
                      'child_types': [c['type'] for c in chain['children']]}
    if p0_state != 'FINITE':
        return _reject('CHAIN_2012_PARAM0_%s' % p0_state, gates)
    if float(p0) <= 0:
        return _reject('CHAIN_2012_PARAM0_NON_POSITIVE', gates, {'param0': p0})
    if float(p0) != float(PARAM0_EXPECTED):
        return _reject('CHAIN_2012_PARAM0_NOT_30', gates, {'param0': p0})
    p6 = record.get('param6')
    if num_state(p6, present='param6' in record) != 'FINITE':
        return _reject('CHAIN_2012_PARAM6_MISSING', gates, {'param6': p6})
    if float(p6) >= 0:
        return _reject('CHAIN_2012_PARAM6_NOT_NEGATIVE', gates, {'param6': p6})

    # ---- D6 本行既有 param6 答案 = 同一记录／指针／sha／原值，binding 与链一致
    existing = [a for a in (row.get('answers') or []) if isinstance(a, dict)]
    param6_answers = [a for a in existing if a.get('rule_key') == PEER_PARAM6_RULE_KEY]
    if not param6_answers:
        return _reject('TARGET_PARAM6_MISSING', gates)
    if len(param6_answers) != 1:
        return _reject('TARGET_PARAM6_AMBIGUOUS(%d)' % len(param6_answers), gates)
    cadence = param6_answers[0]
    if str(cadence.get('field_path') or '') != PEER_PARAM6_FIELD:
        return _reject('TARGET_PARAM6_FIELD_DRIFT', gates, {'field_path': cadence.get('field_path')})
    if cadence.get('record_id') != relay_id:
        return _reject('TARGET_PARAM6_RECORD_DRIFT', gates,
                       {'answer': cadence.get('record_id'), 'chain': relay_id})
    csrc = cadence.get('source') or {}
    record_pointer = '/skilllist/%d' % record_index
    if str(csrc.get('json_pointer') or '') != record_pointer:
        return _reject('TARGET_PARAM6_POINTER_DRIFT', gates,
                       {'answer': csrc.get('json_pointer'), 'chain': record_pointer})
    sha = csrc.get('raw_record_sha256')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
        return _reject('TARGET_PARAM6_RAW_SHA_MISSING', gates)
    if num_state(cadence.get('raw_value')) != 'FINITE' or float(cadence['raw_value']) != float(p6):
        return _reject('TARGET_PARAM6_RAW_DRIFT', gates,
                       {'answer': cadence.get('raw_value'), 'record': p6})
    path = ((cadence.get('binding') or {}).get('path') or {})
    expected_path = {'pattern_id': pattern_id, 'slot': b13['slot'],
                     'boss_id': b13['skillid'], 'ordinary_sub_path': [relay_id]}
    gates['target_param6'] = {'answer_index': existing.index(cadence),
                              'record_id': cadence.get('record_id'),
                              'json_pointer': csrc.get('json_pointer'),
                              'raw_record_sha256': sha,
                              'raw_value': cadence.get('raw_value'),
                              'binding_path': path}
    if path != expected_path:
        return _reject('SLOT_BINDING_DRIFT', gates, {'page': path, 'chain': expected_path})

    # ---- D7 同句 skilltext 行既有 param6 与 param0 答案 = 同一记录／指针／sha／原值
    peer_answers = [a for a in (peer_row.get('answers') or []) if isinstance(a, dict)]
    peer6 = [a for a in peer_answers if a.get('rule_key') == PEER_PARAM6_RULE_KEY]
    peer0 = [a for a in peer_answers if a.get('rule_key') == TARGET_RULE_KEY]
    if not peer6:
        return _reject('PEER_PARAM6_MISSING', gates, {'peer_row_id': peer_row.get('row_id')})
    if len(peer6) != 1:
        return _reject('PEER_PARAM6_AMBIGUOUS(%d)' % len(peer6), gates)
    if not peer0:
        return _reject('PEER_PARAM0_MISSING', gates, {'peer_row_id': peer_row.get('row_id')})
    if len(peer0) != 1:
        return _reject('PEER_PARAM0_AMBIGUOUS(%d)' % len(peer0), gates)
    for answer, field, value, code in (
            (peer6[0], PEER_PARAM6_FIELD, p6, 'PEER_PARAM6'),
            (peer0[0], TARGET_FIELD, p0, 'PEER_PARAM0')):
        if str(answer.get('field_path') or '') != field:
            return _reject('%s_FIELD_DRIFT' % code, gates, {'field_path': answer.get('field_path')})
        if answer.get('record_id') != relay_id:
            return _reject('%s_RECORD_DRIFT' % code, gates,
                           {'answer': answer.get('record_id'), 'chain': relay_id})
        asrc = answer.get('source') or {}
        if str(asrc.get('json_pointer') or '') != record_pointer:
            return _reject('%s_POINTER_DRIFT' % code, gates,
                           {'answer': asrc.get('json_pointer'), 'chain': record_pointer})
        if asrc.get('raw_record_sha256') != sha:
            return _reject('%s_RAW_SHA_DRIFT' % code, gates,
                           {'answer': asrc.get('raw_record_sha256'), 'chain': sha})
        if num_state(answer.get('raw_value')) != 'FINITE' or float(answer['raw_value']) != float(value):
            return _reject('%s_RAW_DRIFT' % code, gates,
                           {'answer': answer.get('raw_value'), 'record': value})
        if answer.get('table') is not None and answer.get('table') != 'skilllist':
            return _reject('%s_TABLE_DRIFT' % code, gates, {'table': answer.get('table')})
        if answer.get('layer') != LAYER:
            return _reject('%s_LAYER_DRIFT' % code, gates, {'layer': answer.get('layer')})
    peer0_source = peer0[0].get('source') or {}
    peer0_path = (((peer0[0].get('remaining_ab_binding') or {}).get('carrier_path')) or {})
    gates['peer_answers'] = {
        'peer_row_id': peer_row.get('row_id'),
        'record_id': peer0[0].get('record_id'),
        'json_pointer': peer0_source.get('json_pointer'),
        'raw_record_sha256': peer0_source.get('raw_record_sha256'),
        'param0_raw': peer0[0].get('raw_value'),
        'param6_raw': peer6[0].get('raw_value'),
        'carrier_path': peer0_path,
        'carrier_path_matches_target': peer0_path == expected_path,
        'peer_value': peer0[0].get('value'),
    }

    # ---- D8 同 raw：按字节范围重算 sha256 并回读切片记录
    begin = csrc.get('byte_begin')
    end = csrc.get('byte_end_exclusive')
    if begin != peer0_source.get('byte_begin') or end != peer0_source.get('byte_end_exclusive'):
        return _reject('RAW_BYTE_RANGE_DRIFT', gates,
                       {'target': [begin, end], 'peer': [peer0_source.get('byte_begin'),
                                                         peer0_source.get('byte_end_exclusive')]})
    chunk, byte_err = raw_bytes(tab, SKILLLIST_SOURCE_KEY, begin, end)
    if byte_err:
        return _reject('RAW_BYTES_%s' % byte_err, gates, {'begin': begin, 'end': end})
    actual_sha = hashlib.sha256(chunk).hexdigest()
    if actual_sha != sha:
        return _reject('RAW_BYTES_SHA_MISMATCH', gates,
                       {'recorded': sha, 'actual': actual_sha})
    try:
        parsed = json.loads(chunk.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _reject('RAW_BYTES_UNPARSEABLE', gates, {'error': repr(exc)})
    if parsed != record:
        return _reject('RAW_BYTES_RECORD_MISMATCH', gates)
    if (parsed.get('skillid') != relay_id or parsed.get('ability') != 2012
            or num(parsed.get('param0')) != float(p0) or num(parsed.get('param6')) != float(p6)):
        return _reject('RAW_BYTES_VALUE_DRIFT', gates)
    gates['raw'] = {'source_key': SKILLLIST_SOURCE_KEY, 'byte_begin': begin,
                    'byte_end_exclusive': end, 'bytes': len(chunk),
                    'sha256': actual_sha}

    # ---- D9 批前未答＋旧答案保护＋幂等
    extras = [a.get('rule_key') for a in existing if a.get('rule_key') not in ALLOWED_EXISTING_KEYS]
    already0 = [a for a in existing if a.get('rule_key') == TARGET_RULE_KEY]
    if already0:
        same = [a for a in already0
                if a.get('record_id') == relay_id
                and num_state(a.get('raw_value')) == 'FINITE'
                and float(a['raw_value']) == float(p0)]
        if len(already0) == len(same):
            return _reject('ALREADY_PRESENT_SAME', gates,
                           {'record_id': relay_id, 'raw_value': p0})
        return _reject('ALREADY_ANSWERED', gates,
                       {'disclosure': '本行已有同 rule_key 答案；不新增、不改写',
                        'answers': [{'record_id': a.get('record_id'),
                                     'raw_value': a.get('raw_value')} for a in already0]})
    if extras:
        return _reject('EXTRA_ANSWER', gates, {'rule_keys': sorted(set(map(str, extras)))})
    gates['existing'] = {'rule_keys': sorted(a.get('rule_key') for a in existing),
                         'target_param6_index': existing.index(cadence)}

    # ---- D10 账本基线（只读 analyze_row；不改映射）
    if ledger:
        try:
            import effect_ledger as ledger_mod
        except Exception as exc:  # pragma: no cover - 环境缺模块时显式失败
            return _reject('LEDGER_UNAVAILABLE', gates, {'error': repr(exc)})
        analyzed = ledger_mod.analyze_row(dict(row), TABLE)
        effects = analyzed.get('effects') or []
        duration = [e for e in effects if e.get('effect_type') == EFFECT_DURATION]
        speed = [e for e in effects if e.get('effect_type') == EFFECT_SPEED]
        if len(duration) != 1 or len(speed) != 1:
            return _reject('LEDGER_EFFECT_SHAPE', gates,
                           {'effects': [e.get('effect_type') for e in effects]})
        if duration[0].get('status') != 'unresolved':
            return _reject('LEDGER_DURATION_ALREADY_RESOLVED', gates,
                           {'status': duration[0].get('status')})
        if speed[0].get('status') != 'has_answer':
            return _reject('LEDGER_SPEED_NOT_ANSWERED', gates,
                           {'status': speed[0].get('status')})
        gates['ledger'] = {
            'effects': [{'effect_type': e.get('effect_type'),
                         'status': e.get('status')} for e in effects],
            'promotion_keys': list(analyzed.get('promotion_keys') or []),
            'explicit_key_mapping': 'ABSENT_IN_RULE_KEY_EFFECT',
            'consume_path': 'analyze_row 既有 quantity_kind=持续时间 词面回退',
            'note': ('本批不修改 effect_ledger.py；追加本答案后同句 継続時間 由既有通用词面回退'
                     '绑定为 has_answer，攻撃速度（词表外）保持 has_answer，不新增 effect 类型。'),
        }

    return {'accepted': True, 'rejection': None, 'gates': gates,
            'row': row, 'skill': skill, 'peer_row': peer_row,
            'pattern_id': pattern_id, 'reference_field': ref,
            'pattern_pointer': pointer, 'chara_pointer': chara_pointer,
            'type13': b13, 'record': record, 'record_index': record_index,
            'record_pointer': record_pointer, 'record_sha256': sha,
            'byte_begin': begin, 'byte_end_exclusive': end,
            'param0': p0, 'param6': p6, 'binding_path': expected_path,
            'target_param6': cadence, 'peer_param0': peer0[0],
            'body_equal_to_skilltext': canon(body) == canon(full)}


def fragment_positions(raw):
    """解码 JSON 字段字符串的稳定分片（与 ``card_page_positions.fragment_positions`` 同口径）。"""
    text = str(raw or '')
    chars, mapping, i = [], [], 0
    while i < len(text):
        if text[i:i + 2] == '\\n':
            chars.append('\n')
            mapping.append((i, i + 2))
            i += 2
        else:
            chars.append(text[i])
            mapping.append((i, i + 1))
            i += 1
    out, start = [], 0
    body = ''.join(chars)
    for match in list(re.finditer(r'。|\n|◆', body)) + [None]:
        end = len(body) if match is None else (
            match.end() if match.group() == '。' else match.start())
        a, b = start, end
        while a < b and body[a] in ' ◆\r\t\n':
            a += 1
        while b > a and body[b - 1] in ' ◆\r\t\n':
            b -= 1
        if a < b:
            out.append(dict(japanese=body[a:b], clean_span=[a, b],
                            raw_span=[mapping[a][0], mapping[b - 1][1]]))
        if match is not None:
            start = match.end()
    return out


# ---------------------------------------------------------------- 答案构造
def _source(res, peer_source, tab=None):
    out = {
        'record_key': '%s#%s' % (SKILLLIST_SOURCE_KEY, res['record_pointer']),
        'source_key': SKILLLIST_SOURCE_KEY,
        'layer': LAYER,
        'snapshot_id': SNAPSHOT_ID,
        'original_file': '%s/skilllist.data5.json.raw' % CACHE_DIR,
        'original_file_label_historical': peer_source.get('original_file'),
        'table': 'skilllist',
        'table_path': '/skilllist',
        'json_pointer': res['record_pointer'],
        'ordinal_zero_based': res['record_index'],
        'byte_begin': res['byte_begin'],
        'byte_end_exclusive': res['byte_end_exclusive'],
        'raw_record_sha256': res['record_sha256'],
        'source_verification': 'VERIFIED_RAW_BYTES',
        'record_id': res['record']['skillid'],
        'field_path': TARGET_FIELD,
        'byte_source': 'decoded_json_raw_bytes',
    }
    if tab is not None:
        out['decoded_json_sha256'] = file_sha256(tab, SKILLLIST_SOURCE_KEY)
    return out


def _conditions(res):
    return ('仅该档必杀（%s / pattern %d，slot %s → bossskill %d）被选中时适用；句面对象自身；'
            '时间原值与同行 param6 来自同一 skilllist %d（ability=2012，param8=64 MYSELF，'
            'param7=1，flag=0，sub 为空）；不从全体增益、敌方减益时间或间隔因子借用；'
            '不证明实际装载、最终攻速、永久或实机。'
            % (res['reference_field'], res['pattern_id'], res['type13']['slot'],
               res['type13']['skillid'], res['record']['skillid']))


def _note(res):
    return ('来自同一自身加速支持记录（与同行 param6 同记录）的正 param0；不从旧 value 字符串取数，'
            '不借全体增益或敌方减益时间。同句行 %s 的 carrier_path 是 %s；本行按自己的 '
            'pattern／slot 重新核链，共享子记录不合并来源。实际装载和选档仍未实机验证。'
            % (res['peer_row'].get('row_id'),
               json.dumps(res['gates'].get('peer_answers', {}).get('carrier_path'),
                          ensure_ascii=False, sort_keys=True)))


def build_answers(data, cid, res, *, tab=None):
    """本行候选答案（数量＝1；与同句 skilltext 行既有 param0 值文一致）。"""
    if not res or not res.get('accepted'):
        return []
    import rules as R
    record = res['record']
    answer = R.answer_for('skilllist', 2012, TARGET_FIELD, record['param0'], record,
                          source_layer='CACHE')
    if answer is None:
        return []
    answer = json.loads(json.dumps(answer, ensure_ascii=False, allow_nan=False))
    peer_value = res['peer_param0'].get('value')
    value = peer_value if isinstance(peer_value, str) else '这项自身加速持续30游戏秒（推断）。'
    answer.update(
        value=value,
        rule_key=TARGET_RULE_KEY,
        table='skilllist',
        record_id=record['skillid'],
        layer=LAYER,
        source=_source(res, res['peer_param0'].get('source') or {}, tab),
        target='自身',
        conditions=_conditions(res),
        condition_label='%s / pattern %d 被选中时' % (res['reference_field'], res['pattern_id']),
        numeric_evidence='推断',
        association_evidence='推断',
        evidence_scope=SCOPE,
        rule_body_status='复用既有字段局部规则，句内归属为推断',
        numeric_source='真实CACHE记录；规则本体已确认，句→载体为结构推断',
        quantitative=True,
        supporting_fields=[{'field_path': PEER_PARAM6_FIELD,
                            'raw_value': res['param6']}],
        note=_note(res),
        evidence=list(dict.fromkeys(list(answer.get('evidence') or []) + list(EVIDENCE))),
    )
    answer[BINDING_KEY] = {
        'scope': SCOPE,
        'structure_scope': STRUCTURE_SCOPE,
        'row_id': res['row'].get('row_id'),
        'pattern_id': res['pattern_id'],
        'reference_field': res['reference_field'],
        'slot': res['type13']['slot'],
        'boss_id': res['type13']['skillid'],
        'record_id': record['skillid'],
        'json_pointer': res['record_pointer'],
        'raw_record_sha256': res['record_sha256'],
        'byte_begin': res['byte_begin'],
        'byte_end_exclusive': res['byte_end_exclusive'],
        'decoded_json_sha256': answer['source'].get('decoded_json_sha256'),
        'param0_raw': res['param0'],
        'param6_raw': res['param6'],
        'peer_text_row_id': res['peer_row'].get('row_id'),
        'peer_text_pointer': res['chara_pointer'],
        'peer_record_id': res['peer_param0'].get('record_id'),
        'peer_json_pointer': (res['peer_param0'].get('source') or {}).get('json_pointer'),
        'peer_raw_record_sha256': (res['peer_param0'].get('source') or {}).get('raw_record_sha256'),
        'peer_carrier_path': res['gates'].get('peer_answers', {}).get('carrier_path'),
        'peer_carrier_path_matches_target':
            res['gates'].get('peer_answers', {}).get('carrier_path_matches_target'),
        'body_equal_to_skilltext': res['body_equal_to_skilltext'],
        'clause_identity': 'same_card_same_clause',
        'mirror_attribution': 'INFERENCE',
    }
    return [answer]


# ---------------------------------------------------------------- 正式页消费（候选未接线）
def apply_to_groups(data, cid, groups, *, scope_cids=None, tab=None, ledger=True):
    """把本批答案追加到页面 groups（候选未接线；调用方必须显式声明 scope）。"""
    report = dict(scope=SCOPE, cid=cid, answers_added=0, additions=[], rejections=[],
                  rows_seen=0)
    if scope_cids is None:
        report['rejections'].append(dict(reason='NO_SCOPE_DECLARED'))
        return report
    if isinstance(scope_cids, (str, bytes)):
        report['rejections'].append(dict(reason='SCOPE_INVALID'))
        return report
    try:
        declared = frozenset(scope_cids)
    except TypeError:
        report['rejections'].append(dict(reason='SCOPE_INVALID'))
        return report
    if cid not in declared:
        report['rejections'].append(dict(reason='CID_NOT_IN_DECLARED_SCOPE'))
        return report
    tab = tab or tables(data)
    for group in groups or []:
        if group.get('group') != GROUP:
            continue
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                report['rows_seen'] += 1
                if not str(row.get('reference_field') or '').startswith(REF_PREFIX):
                    continue
                if not SELF_SPEED_RE.match(canon(row.get('japanese'))):
                    continue
                res = evaluate(data, cid, row, groups=groups, tab=tab,
                               ledger=ledger, scope_cids=declared)
                if not res['accepted']:
                    report['rejections'].append(dict(row_id=row.get('row_id'),
                                                     reason=res['rejection'],
                                                     detail=res.get('detail')))
                    continue
                answers = build_answers(data, cid, res, tab=tab)
                if len(answers) != 1:
                    report['rejections'].append(dict(row_id=row.get('row_id'),
                                                     reason='ANSWER_BUILD_FAILED'))
                    continue
                answer = answers[0]
                row.setdefault('answers', []).append(answer)
                row['evidence_scope'] = list(dict.fromkeys(
                    list(row.get('evidence_scope') or []) + [SCOPE]))
                row['partial'] = True
                report['answers_added'] += 1
                report['additions'].append(dict(row_id=row.get('row_id'),
                                                rule_key=answer['rule_key'],
                                                record_id=answer['record_id'],
                                                raw_value=answer['raw_value'],
                                                answer_index=len(row['answers']) - 1))
    return report
