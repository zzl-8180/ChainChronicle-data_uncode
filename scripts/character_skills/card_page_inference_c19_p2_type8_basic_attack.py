# -*- coding: utf-8 -*-
"""C19-P2 APK ``skilllist`` ability=8（type8）**基础攻击逐效果局部绑定**——3 项候选（**未接线**）。

任务卡 ``docs/tasks/20261107-c19-p2-type8-basic-attack.md``；周期卡
``docs/tasks/20261107-c19-cycle.md``；方向评估 ``docs/tasks/20261107-c19-direction-assessment.md``；
交付包卡 ``docs/tasks/20261107-c19-delivery-package.md``；方法
``docs/角色技能完整解读实施方案.md`` §1.3／§1.6。

**本文件是候选实现，未接入共享接线**：``card_page_data.py`` 未 import 本模块；
``rules.json``／``rules.py``／``effect_ledger.py``／C16／C17／C18 模块／正式 ``pages``／账本均未改动；
本阶段不运行正式全库生成或 resume。模块只读 APK 内置主表（``output/base_master/``）与
``profiles/rules.json``，并由调用方传入真实 ``card_page_data.Inputs`` 与页面行对象
（``build_card`` 产物）。

作用域（严格 3 个 effect，全部槽位 ``/param1``，全部 APK 层）
============================================================  ==========================================================  ======  ==================
cid                                                           row_id                                                      effect  句面
============================================================  ==========================================================  ======  ==================
1063                                                          ``1063-ability-ability-skillid_1_-lvorder0-f1``             #e00    攻撃力が上がる。
1238                                                          ``1238-ability-ability-skillid_2_-lvorder1-f0``             #e00    攻撃力が上がる。
12220                                                         ``12220-ability-ability-skillid_1_-lvorder0-f0``            #e00    攻撃力が上がる。
============================================================  ==========================================================  ======  ==================

**冻结表只含身份与结构**（cid／row_id／effect_id／槽／主张／rule_key／句面／句序号／段序号／
载体形态／父记录能力号／兄弟记录能力号多重集／句外线索／句外归纳）。本模块**不保存、不导入任何
预筛 raw、归一化值或载体记录 ID**；raw 与派生值一律由「APK charainfo → 父 skilllist →
唯一 type8 记录 → ``/param1`` → ``rules.answer_for``」重算。任务卡给出的载体 ID 与原值只在
``check_candidate.py`` **计算之后**作回归比对。

来源链（APK 原层，逐行硬门；任一不符即拒绝，不猜、不跨记录、不补零）
--------------------------------------------------------------------
G1  **角色上游**：APK ``charainfo[cid]`` 全表恰 1 条，且与 ``Inputs.apk_chara`` 逐值相同。
G2  **角色身份**：行 ``cid`` 与调用 cid 相同。
G3  **引用形态**：行 ``group == 'ability'`` 且 ``reference_field`` 恰为 ``skillid[n]``。
G4  **槽位**：``charainfo.skillid[n]`` 为存在正整数（不越界、不取 0 占位）。
G5  **父记录唯一**：该 skillid 在 APK ``skilllist`` 全表恰 1 条；``Inputs.apk_skill`` 的
    下标与记录逐项相同；调用方 skill 的 ``record_id``／``layer`` 不与父记录矛盾。
G6  **行来源是 APK 父文**：``source.layer == 'APK'``、
    ``source.source_key == 'APK/_mdSkill.json'``、``json_pointer == /skilllist/<父下标>``、
    ``field_json_pointer == …/text``；``skill.record_evidence`` 内嵌 ``raw_record`` 与原文逐值相同。
G7  **整句／fragment／source span 三元消歧**：
    (a) 父文按「◆ 开段、。收句」重建段句表（确定性）；行 ``fragment_index`` 指向的句在
        去掉段首 ``◆`` 装饰后与行日语逐字相同；该句的 clean span 与 ``source_position.clean_span``
        相同；``source_position.raw_span`` 在原文（字面 ``\\n`` 未清理）上亦逐字相同。
    (b) 行日语在整条父文中作为**整句**只出现 1 次（作为子串可多次出现，但其余出现均在更长句内，
        不可能成为本句载体），据此排除同文跨句冒认。
    (c) 句面必须是纯基础主张：以「攻撃力」起、以「。」收，且不含条件／对象／其他属性词
        （防御・移動・クリティカル・WAVE・HP・スクラップ・マナ・敵・味方・一定時間・回・範囲）。
G8  **type8 载体唯一**：``{父记录} ∪ sub[]`` 中 ability==8 的记录恰 1 条；载体形态（父或 sub）
    与冻结表一致；父记录能力号与 sub 中非载体兄弟的能力号多重集与冻结表逐项相同
    （记录变化即拒绝，不静默沿用）。
G9  **字段门**：载体 ``/param1`` 状态 present、有限且 >1（方向为升）；``/param0 == 0`` 且
    ``iParam0 == 0``（本批冻结载体的常时结构；非 0 即拒绝，不猜其语义）；``/param2 == 1``、
    ``/param3 == 1``（已确认规则口径的中性乘数，即该记录不携带移动／减伤值）；其余槽位逐项登记。
G10 **规则复用**：只调用 ``rules.answer_for('skilllist', 8, '/param1', raw, 载体,
    source_layer='APK')``；本模块不新增公式、不新增规则键、不新增账本映射。
G11 **消费对齐**：真实 ``effect_ledger.analyze_row`` 下本行恰 1 个 ``#e`` effect、类型
    ``攻撃力``、方向 ``up``；本模块只在 claim 相符时出答案。

逐效果局部作用域 ≠ 旧模板放行
------------------------------
旧 B3 因「第 1 段段中句＋同段句后有后续文本」留 hint、旧 B4 因「句后文本含兄弟记录承载不了的
其他效果主张（P-C）」留 hint、旧 B11 的域是 CACHE ability1095（APK 载体域外）；三者的既有
``inference_b3_hint``／``inference_b4_hint``／``unknown_reasons`` 与账本 unresolved 记录**原样
保留、不删除、不改写**（答案里逐条转述为 ``retained_old_rejections``）。本模块只对 3 个冻结
effect 的**整句 span** 绑定唯一 type8 记录的 ``/param1``：条件句与其他效果由兄弟记录承载
（G8/G9 逐项登记且不并入），因此不是把旧模板的整行晋级条件放宽，也不改变 B3/B4/B11 的任何
判定。旧模板仍按原口径拒绝它们未覆盖的行。

证据分档（不得升格）
--------------------
G1–G11 与字段原值为结构／原值证据；句面主张→该 type8 记录 ``/param1`` 的归属为**推断**。
答案写 ``numeric_evidence='确认'``（既有已确认规则体＋APK 原始记录）、
``association_evidence='推断'``、``binding='inferred'``、``runtime_verified=False``、
``evidence_scope=SCOPE``。这是「既有规则与当前原值已确认」，不是完整语义确认，也不是实机确认。

明确不处理
----------
* 1063 三条 type67 条件记录（兄弟记录，逐项登记拒绝，不并入）。
* 1238 的 WAVE 父 type4、HP≥50%（type36）、2WAVE（type1040）、其余 WAVE 短时增益（type64）
  各有分工：只登记，不并入；同卡 WAVE 句行不在本作用域。
* 12220 第二段 type96（择槽未决）、第三段 type97、第四段 type1019：只登记，不并入。
* CACHE 命名空间：本批 3 个 cid 在 CACHE charainfo／skilllist 均无同号记录（逐项核对并写入
  ``source.cross_layer``），不借值、不合并；其他机制族、其他能力号、其他槽位、新原生、实机、
  新缓存、清理、Git、发布一律不启动。
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from project_layout_paths import read_path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:            # 允许从任意工作目录直接导入
    sys.path.insert(0, str(_HERE))

import effect_ledger as LEDGER             # 只读：真实消费者
import rules as R                          # 只读：既有规则与公式

MODULE_VERSION = 'c19_p2_type8_basic_attack_20261107'
#: 本作用域（缺省／错误／空 scope 一律硬拒绝；见 ``ScopeError``）。
SCOPE = 'C19_P2_TYPE8_BASIC_ATTACK_20261107'
CARRIER_ABILITY = 8
SLOT = 'param1'
RULE_KEY = 'skilllist|8|/param1'
CLAIM = '攻撃力'
SENTENCE_ZH = '攻击力上升'
UNIT = '攻击倍率（无量纲）；本项增加以百分比表示'
APK_SKILLLIST_REL = 'output/base_master/_mdSkill.json'
APK_CHARAINFO_REL = 'output/base_master/_mdCharacter.json'
APK_SKILLLIST_SOURCE_KEY = 'APK/_mdSkill.json'
CACHE_SKILLLIST_REL = 'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw'
CACHE_CHARAINFO_REL = 'output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw'
RESOLVED_EXACT = 'RESOLVED_EXACT_APK_MASTER_RECORD'
CARRIER_SLOTS = ('param0', 'param1', 'param2', 'param3', 'param4', 'param5', 'param6',
                 'param7', 'param8', 'param9', 'iParam0', 'iParam1')
#: 句面纯基础主张的边界词：出现任一即说明本句不是无条件基础攻击句（G7c）。
CLAIM_BLOCK_WORDS = ('防御', '移動', 'クリティカル', 'WAVE', 'HP', 'スクラップ', 'マナ',
                     '敵', '味方', '一定時間', '回', '範囲')
#: type8 既有三键（``rules.json`` skilllist|8|/param1..3）；其余槽"只登记不解释"。
TYPE8_RULE_SLOTS = ('param1', 'param2', 'param3')


def _target(cid, row_id, sentence, sentence_index, segment_index, parent_ability,
            carrier_form, sibling_abilities, cues, summary):
    return dict(cid=cid, row_id=row_id, effect_id=f'{row_id}#e00', slot=SLOT,
                claim=CLAIM, rule_key=RULE_KEY, sentence=sentence,
                sentence_index=sentence_index, segment_index=segment_index,
                parent_ability=parent_ability, carrier_form=carrier_form,
                sibling_abilities=tuple(sorted(sibling_abilities)),
                out_of_sentence_cues=tuple(cues),
                out_of_sentence_summary=summary)


#: 3 项 effect 冻结身份。**不含 raw／归一化值／载体记录 ID**；载体由 G8 从 APK 原记录结构定位。
TARGETS = (
    _target(
        1063, '1063-ability-ability-skillid_1_-lvorder0-f1', '攻撃力が上がる。',
        sentence_index=1, segment_index=0, parent_ability=8, carrier_form='parent',
        sibling_abilities=(67, 67, 67),
        cues=('戦場に自身以外の<騎士>の味方がいると', '2人以上いると', '3人以上いると'),
        summary=('骑士友方在场时自身防御力提升、2 人以上时移动速度提升、'
                 '3 人以上时暴击发生率提升')),
    _target(
        1238, '1238-ability-ability-skillid_2_-lvorder1-f0', '攻撃力が上がる。',
        sentence_index=0, segment_index=0, parent_ability=4, carrier_form='sub',
        sibling_abilities=(36, 64, 1040),
        cues=('HPが50％以上の時、さらに効果が上がり', 'WAVEが進むたび、攻撃力が上がる',
              'さらに2WAVE毎に防御力が上がる',
              'WAVEが進むたび、自身の防御力とクリティカル発生率を一定時間上げる'),
        summary=('WAVE 推进时的回复与屏障、HP 50% 以上时进一步增强并提高暴击发生率、'
                 '每 2 WAVE 的防御力提升、WAVE 推进时防御力与暴击发生率的短时提升')),
    _target(
        12220, '12220-ability-ability-skillid_1_-lvorder0-f0', '攻撃力が上がる。',
        sentence_index=0, segment_index=0, parent_ability=1018, carrier_form='sub',
        sibling_abilities=(96, 97, 1019),
        cues=('スクラップが多いほど、攻撃力が上がる',
              'スクラップを所持しているとWAVE開始時に',
              '攻撃を8回当てると自身とミカエラの攻撃力'),
        summary=('废料越多攻击力越高、持有废料时 WAVE 开始时转换为骑士玛那、'
                 '攻击 8 次时自身与米凯拉攻击力短时提升')),
)

TARGET_CIDS = tuple(t['cid'] for t in TARGETS)
BY_ROW = {(t['cid'], t['row_id']): t for t in TARGETS}
BY_EFFECT = {t['effect_id']: t for t in TARGETS}
TARGET_ROW_IDS = {cid: {t['row_id'] for t in TARGETS if t['cid'] == cid} for cid in TARGET_CIDS}

#: 保护／既有交付边界卡：本模块结构上不可达，零新增（旧答案原样保留）。
PROTECTED_CIDS = (30236, 30239, 30102, 20234)
#: 相邻已交付卡（C16／C17／C18 与 C13 type8 族）：本批不认领，零新增。
ADJACENT_DELIVERED_CIDS = (30110, 30237, 30333, 6341, 20333)
NEGATIVE_CIDS = PROTECTED_CIDS + ADJACENT_DELIVERED_CIDS


class ScopeError(RuntimeError):
    """缺省／错误／空 scope——硬拒绝，不做默认回退。"""


def require_scope(scope):
    if scope is None:
        raise ScopeError(f'缺少 scope 参数：必须显式传入 {SCOPE!r}（不设默认值）')
    if not isinstance(scope, str) or not scope:
        raise ScopeError(f'scope 为空或非字符串：收到 {scope!r}，本模块只接受 {SCOPE!r}')
    if scope != SCOPE:
        raise ScopeError(f'scope 不符：收到 {scope!r}，本模块只接受 {SCOPE!r}')


# ---------------------------------------------------------------- 文本／数值小工具（只读）
def canon(text):
    """NFKC＋去空白（与既有批次同口径）；只用于线索包含判定，不用于 span 计算。"""
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', str(text or '')))


def raw_state(record, slot):
    """字段状态分档（missing／null／bool／non-numeric／non-finite／negative／zero／present）。"""
    if slot not in record:
        return 'missing'
    value = record[slot]
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'bool'
    if not isinstance(value, (int, float)):
        return 'non-numeric'
    if not math.isfinite(value):
        return 'non-finite'
    if value < 0:
        return 'negative'
    if value == 0:
        return 'zero'
    return 'present'


def num_text(value):
    """乘数文本：沿用 ``rules._num`` 的 ``%.6g`` 口径（不新增换算）。"""
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return '%.6g' % f


def percent_text(delta):
    """百分比文本：沿用 ``rules._mult_kind`` 的 ``%.6g`` 口径（不新增换算）。"""
    return '%.6g' % float(delta)


def normalized_value(raw):
    """既有 conversion「本项攻击 +(param1-1)×100%」的归一化表达；只为回归比对与展示。"""
    return float('%.6g' % ((float(raw) - 1.0) * 100.0))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def clean_text(text):
    """把解码 JSON 文本里的字面 ``\\n`` 还原为换行（``clean_span`` 坐标系）。"""
    return (text or '').replace('\\n', '\n')


# ---------------------------------------------------------------- 段／句切分（G7）
def segment_sentences(text):
    """按「◆ 开段、。收句」确定性切分；返回 ``(clean, sentences)``。

    ``sentences[i]`` 为 ``dict(index, segment, start, end, raw, core_start, core)``：
    ``start/end`` 是 clean 文本偏移；``core`` 去掉段首 ``◆``／换行／空白装饰；
    ``core_start`` 是 ``core`` 在 clean 文本中的起点。同一记录可多次出现同一句面，
    因此调用方必须同时核对句序号与 span（G7）。
    """
    clean = clean_text(text)
    starts = [m.start() for m in re.finditer('◆', clean)]
    bounds = []
    if not starts or starts[0] != 0:
        bounds.append((0, starts[0] if starts else len(clean)))
    for k, s in enumerate(starts):
        bounds.append((s, starts[k + 1] if k + 1 < len(starts) else len(clean)))
    out = []
    for seg_i, (bs, be) in enumerate(bounds):
        block = clean[bs:be]
        if not block.strip('\n \u3000'):
            continue
        for m in re.finditer(r'[^。]*。|[^。]+$', block):
            piece = m.group(0)
            if not piece or not piece.strip('\n \u3000'):
                continue
            core = piece
            lead = 0
            while lead < len(core) and core[lead] in '◆\n \u3000':
                lead += 1
            out.append(dict(index=len(out), segment=seg_i, start=bs + m.start(),
                            end=bs + m.end(), raw=piece, core=core[lead:],
                            core_start=bs + m.start() + lead))
    return clean, out


# ---------------------------------------------------------------- 只读主表（唯一性／跨层核对）
_RAW_CACHE = {}


def apk_tables(root):
    """按 root 缓存 APK 主表原文与 skillid／cid → 下标列表（含重复计数）。"""
    key = str(Path(root).resolve())
    if key not in _RAW_CACHE:
        base = Path(root)
        skill = json.loads(read_path(base / APK_SKILLLIST_REL, root=base).read_text(encoding='utf-8-sig'))['skilllist']
        chara = json.loads(read_path(base / APK_CHARAINFO_REL, root=base).read_text(encoding='utf-8-sig'))['charainfo']
        skill_index, chara_index = {}, {}
        for i, rec in enumerate(skill):
            skill_index.setdefault(rec.get('skillid'), []).append(i)
        for i, rec in enumerate(chara):
            chara_index.setdefault(rec.get('cid'), []).append(i)
        _RAW_CACHE[key] = dict(
            skilllist=skill, charainfo=chara, skill_index=skill_index, chara_index=chara_index,
            skilllist_sha256=sha256_file(read_path(base / APK_SKILLLIST_REL, root=base)),
            charainfo_sha256=sha256_file(read_path(base / APK_CHARAINFO_REL, root=base)))
    return _RAW_CACHE[key]


def cache_presence(root):
    """**只登记** CACHE 命名空间是否同号存在（不取任何数值）：证明不跨源借值、不合并。"""
    key = 'cache:' + str(Path(root).resolve())
    if key not in _RAW_CACHE:
        base = Path(root)
        chara = json.loads(read_path(base / CACHE_CHARAINFO_REL, root=base).read_text(encoding='utf-8-sig'))['charainfo']
        skill = json.loads(read_path(base / CACHE_SKILLLIST_REL, root=base).read_text(encoding='utf-8-sig'))['skilllist']
        chara_index, skill_index = {}, {}
        for i, rec in enumerate(chara):
            chara_index.setdefault(rec.get('cid'), []).append(i)
        for i, rec in enumerate(skill):
            skill_index.setdefault(rec.get('skillid'), []).append(i)
        _RAW_CACHE[key] = dict(chara_index=chara_index, skill_index=skill_index,
                               charainfo_count=len(chara), skilllist_count=len(skill))
    return _RAW_CACHE[key]


def cross_layer_block(data, cid, ids):
    """CACHE 同号存在性（0＝无同号记录）；本模块**只登记、不读取、不合并**。"""
    pres = cache_presence(data.root)
    return dict(
        modules=['CACHE/' + Path(CACHE_CHARAINFO_REL).name,
                 'CACHE/' + Path(CACHE_SKILLLIST_REL).name],
        cache_charainfo_records=pres['charainfo_count'],
        cache_skilllist_records=pres['skilllist_count'],
        cid_in_cache_charainfo=len(pres['chara_index'].get(cid) or []),
        skillid_matches_in_cache={str(s): len(pres['skill_index'].get(s) or []) for s in ids},
        note=('CACHE 命名空间只作同号存在性登记；本模块不读取、不借用、不合并其数值，'
              'APK 与 CACHE 不合并计数。'))


# ---------------------------------------------------------------- 链解析（G1–G9）
def _gate(gates, code, ok, detail, **extra):
    gates.append(dict(code=code, ok=bool(ok), detail=detail, **extra))
    return bool(ok)


def _reject(gates, code, detail, **extra):
    _gate(gates, code, False, detail, **extra)
    return dict(status='REJECTED', reason=code, detail=detail, gates=gates)


def _sentence_purity(sentence):
    """G7c：纯基础主张（攻撃力…。）——不含量／对象／其他属性词。"""
    text = canon(sentence)
    return (text.startswith('攻撃力') and text.endswith('。')
            and not [w for w in CLAIM_BLOCK_WORDS if w in text])


def resolve_chain(data, cid, row, skill=None, target=None):
    """APK charainfo → 父 skilllist → 唯一 type8 记录；返回结构证据，不产出数值答案。"""
    gates = []
    tgt = target if target is not None else BY_ROW.get((cid, row.get('row_id')))
    if tgt is None:
        return _reject(gates, 'G0_ROW_NOT_IN_SCOPE',
                       f'行 {row.get("row_id")!r} 不在 C19-P2 冻结表内')
    apk = apk_tables(data.root)

    # ---- G1 APK charainfo
    idxs = apk['chara_index'].get(cid) or []
    if len(idxs) != 1:
        return _reject(gates, 'G1_APK_CHARAINFO_NOT_UNIQUE',
                       f'APK charainfo cid={cid} 匹配 {len(idxs)} 条，要求恰 1 条', cid=cid)
    chara = apk['charainfo'][idxs[0]]
    bound_chara = data.apk_chara.get(cid)
    if bound_chara is None or bound_chara != chara:
        return _reject(gates, 'G1_APK_CHARAINFO_INPUT_MISMATCH',
                       f'Inputs.apk_chara[cid={cid}] 与 APK 解码原文不一致', cid=cid)
    _gate(gates, 'G1_APK_CHARAINFO_NOT_UNIQUE', True,
          f'APK charainfo 唯一：/charainfo/{idxs[0]}')

    # ---- G2 角色身份
    if int(row.get('cid', -1)) != int(cid):
        return _reject(gates, 'G2_ROW_CID_MISMATCH',
                       f"行 cid={row.get('cid')!r} 与调用 cid={cid} 不一致")

    # ---- G3 引用形态
    ref = str(row.get('reference_field') or '')
    m = re.fullmatch(r'skillid\[(\d+)\]', ref)
    if not m or row.get('group') != 'ability':
        return _reject(gates, 'G3_ROW_NOT_ABILITY_SKILLID_REFERENCE',
                       f'行 group={row.get("group")!r}／reference_field={ref!r} 不是 '
                       'ability skillid[n]：非 APK 能力行结构上不适用',
                       group=row.get('group'), reference_field=ref)
    slot_index = int(m.group(1))
    _gate(gates, 'G3_ROW_NOT_ABILITY_SKILLID_REFERENCE', True, f'ability {ref} 引用形态成立')

    # ---- G4 槽位
    skillids = chara.get('skillid') or []
    if (slot_index >= len(skillids) or not isinstance(skillids[slot_index], int)
            or isinstance(skillids[slot_index], bool) or skillids[slot_index] <= 0):
        return _reject(gates, 'G4_APK_CHARAINFO_SKILLID_SLOT_MISSING',
                       f'charainfo.skillid[{slot_index}] 缺失或非正整数：{skillids!r}')
    sid = skillids[slot_index]
    _gate(gates, 'G4_APK_CHARAINFO_SKILLID_SLOT_MISSING', True,
          f'charainfo.skillid[{slot_index}] = {sid}')

    # ---- G5 父记录唯一
    pidx_list = apk['skill_index'].get(sid) or []
    if len(pidx_list) != 1:
        return _reject(gates, 'G5_APK_PARENT_NOT_UNIQUE',
                       f'skillid={sid} 在 APK skilllist 全表匹配 {len(pidx_list)} 条，要求恰 1 条',
                       parent_skillid=sid)
    pidx = pidx_list[0]
    parent = apk['skilllist'][pidx]
    bound_parent = data.apk_skill.get(sid)
    if bound_parent is None or bound_parent[0] != pidx or bound_parent[1] != parent:
        return _reject(gates, 'G5_APK_PARENT_INPUT_MISMATCH',
                       f'Inputs.apk_skill[skillid={sid}] 与 APK 解码原文下标／记录不一致',
                       parent_skillid=sid)
    if skill is not None:
        if skill.get('record_id') not in (None, sid):
            return _reject(gates, 'G5_APK_PARENT_INPUT_MISMATCH',
                           f"skill.record_id={skill.get('record_id')!r} != "
                           f'charainfo.skillid[{slot_index}]={sid}')
        if skill.get('layer') not in (None, 'APK'):
            return _reject(gates, 'G5_APK_PARENT_INPUT_MISMATCH',
                           f"skill.layer={skill.get('layer')!r} 不是 APK 层")
    _gate(gates, 'G5_APK_PARENT_NOT_UNIQUE', True,
          f'父记录唯一：skillid={sid} @ /skilllist/{pidx}（ability={parent.get("ability")}）')

    # ---- G6 行来源是 APK 父文
    src = row.get('source') or {}
    want = f'/skilllist/{pidx}'
    if (src.get('layer') != 'APK' or src.get('source_key') != APK_SKILLLIST_SOURCE_KEY
            or src.get('json_pointer') != want
            or src.get('field_json_pointer') != want + '/text'):
        return _reject(gates, 'G6_ROW_SOURCE_NOT_APK_PARENT_TEXT',
                       f'行来源 {src.get("layer")!r}／{src.get("source_key")!r}／'
                       f'{src.get("json_pointer")!r}／{src.get("field_json_pointer")!r} '
                       f'不是 APK 父文 {want}/text')
    if skill is not None:
        evidence = [e for e in skill.get('record_evidence') or []
                    if e.get('table') == 'skilllist' and e.get('record_id') == sid
                    and e.get('layer') == 'APK']
        if len(evidence) != 1 or evidence[0].get('raw_record') != parent:
            return _reject(gates, 'G6_ROW_SOURCE_NOT_APK_PARENT_TEXT',
                           'skill.record_evidence 内嵌 raw_record 与 APK 原文不唯一或不相等',
                           evidence_records=len(evidence))
    _gate(gates, 'G6_ROW_SOURCE_NOT_APK_PARENT_TEXT', True,
          f'行来源 = APK {want}/text（父记录 sha256={src.get("raw_record_sha256", "")[:12]}…）')

    # ---- G7 整句／fragment／source span 三元消歧
    clean, sents = segment_sentences(parent.get('text'))
    pos = row.get('source_position') or {}
    cspan, rspan = pos.get('clean_span'), pos.get('raw_span')
    japanese = row.get('japanese')
    fidx = row.get('fragment_index')

    def _span_ok(span, limit):
        return (isinstance(span, list) and len(span) == 2
                and all(isinstance(x, int) and not isinstance(x, bool) for x in span)
                and 0 <= span[0] < span[1] <= limit)

    if not _span_ok(cspan, len(clean)) or not _span_ok(rspan, len(parent.get('text') or '')):
        return _reject(gates, 'G7_SPAN_MISSING',
                       f'source_position span 缺失或越界：clean={cspan!r} raw={rspan!r}')
    if clean[cspan[0]:cspan[1]] != japanese:
        return _reject(gates, 'G7_CLEAN_SPAN_MISMATCH',
                       f'clean_span 文本 {clean[cspan[0]:cspan[1]]!r} 与行日语 {japanese!r} 不相同')
    raw_text = parent.get('text') or ''
    if raw_text[rspan[0]:rspan[1]] != japanese:
        return _reject(gates, 'G7_RAW_SPAN_MISMATCH',
                       f'raw_span 文本 {raw_text[rspan[0]:rspan[1]]!r} 与行日语 {japanese!r} 不相同')
    if not isinstance(fidx, int) or isinstance(fidx, bool) or not 0 <= fidx < len(sents):
        return _reject(gates, 'G7_FRAGMENT_INDEX_OUT_OF_RANGE',
                       f'fragment_index={fidx!r} 不在段句表 0..{len(sents) - 1}')
    sent = sents[fidx]
    if sent['core'] != japanese:
        return _reject(gates, 'G7_FRAGMENT_INDEX_MISMATCH',
                       f'句序号 {fidx} 的句（去装饰）{sent["core"]!r} 与行日语 {japanese!r} 不相同')
    if (sent['core_start'], sent['end']) != (cspan[0], cspan[1]):
        return _reject(gates, 'G7_SENTENCE_SPAN_DISAGREES_WITH_SOURCE',
                       f'句 span {(sent["core_start"], sent["end"])} 与 clean_span '
                       f'{(cspan[0], cspan[1])} 不一致')
    if sent['segment'] != tgt['segment_index'] or fidx != tgt['sentence_index']:
        return _reject(gates, 'G7_POSITION_NOT_FROZEN',
                       f'段/句位置 (seg={sent["segment"]}, idx={fidx}) 与冻结 '
                       f'(seg={tgt["segment_index"]}, idx={tgt["sentence_index"]}) 不符')
    dups = [s['index'] for s in sents if s['core'] == japanese]
    if len(dups) != 1:
        return _reject(gates, 'G7_SENTENCE_NOT_UNIQUE',
                       f'该句面在整条父文中作为整句出现 {len(dups)} 次（须恰 1 次）：{dups}',
                       sentence_indices=dups)
    if not _sentence_purity(japanese):
        return _reject(gates, 'G7_SENTENCE_NOT_PURE_BASE_CLAIM',
                       f'句面 {japanese!r} 不是纯基础攻击主张（含条件/对象/其他属性词）')
    _gate(gates, 'G7_SENTENCE_SPAN_OK', True,
          f'整句消歧：段 {sent["segment"]} 第 {fidx} 句，clean span {list(cspan)}／raw span '
          f'{list(rspan)} 与句序号三元一致；整句唯一（子串 {clean.count(japanese)} 次，'
          f'其余在更长句内）；句面为纯基础主张',
          clean_span=list(cspan), raw_span=list(rspan), segment=sent['segment'],
          sentence_index=fidx, substring_occurrences=clean.count(japanese))

    # 句外线索：必须在父文出现、且不在本行（证明条件/其他效果确在句外）
    parent_canon = canon(parent.get('text'))
    row_canon = canon(japanese)
    cue_rows = []
    cue_ok = True
    for cue in tgt['out_of_sentence_cues']:
        cue_c = canon(cue)
        in_parent = bool(cue_c) and cue_c in parent_canon
        in_row = cue_c in row_canon
        cue_ok &= in_parent and not in_row
        cue_rows.append(dict(cue=cue, in_parent_text=in_parent, in_row_fragment=in_row))
    if not cue_ok:
        return _reject(gates, 'G7B_OUT_OF_SENTENCE_CUE_UNVERIFIED',
                       '句外线索未在父文出现或出现在本行内：披露与句面边界不一致',
                       cues=cue_rows)
    _gate(gates, 'G7B_OUT_OF_SENTENCE_CUE_UNVERIFIED', True,
          f'{len(cue_rows)} 条句外线索均在父文、均不在本行（其他句条件/效果未并入）',
          cues=cue_rows)

    # ---- G8 type8 载体唯一 + 兄弟结构冻结
    subs = []
    for sub_slot, sub_sid in enumerate(parent.get('sub') or []):
        lst = apk['skill_index'].get(sub_sid) or []
        if len(lst) != 1:
            return _reject(gates, 'G8_APK_SUB_NOT_UNIQUE',
                           f'sub skillid={sub_sid} 在 APK 全表匹配 {len(lst)} 条',
                           sub_skillid=sub_sid)
        srec = apk['skilllist'][lst[0]]
        bind = data.apk_skill.get(sub_sid)
        if bind is None or bind[0] != lst[0] or bind[1] != srec:
            return _reject(gates, 'G8_APK_SUB_INPUT_MISMATCH',
                           f'sub skillid={sub_sid} 的 Inputs 记录与 APK 原文不一致')
        subs.append(dict(skillid=sub_sid, index=lst[0], record=srec,
                         ability=srec.get('ability'), sub_slot=sub_slot))
    if int(parent.get('ability') or 0) != int(tgt['parent_ability']):
        return _reject(gates, 'G8_PARENT_ABILITY_CHANGED',
                       f'父记录 ability={parent.get("ability")!r} 与冻结 '
                       f'{tgt["parent_ability"]} 不符')
    candidates = []
    if parent.get('ability') == CARRIER_ABILITY:
        candidates.append(dict(record=parent, record_id=sid, index=pidx,
                               ability=CARRIER_ABILITY, form='parent', sub_slot=None))
    for sub in subs:
        if sub['ability'] == CARRIER_ABILITY:
            candidates.append(dict(record=sub['record'], record_id=sub['skillid'],
                                   index=sub['index'], ability=CARRIER_ABILITY,
                                   form='sub', sub_slot=sub['sub_slot']))
    if len(candidates) != 1:
        return _reject(gates, 'G8_TYPE8_CARRIER_NOT_UNIQUE',
                       f'{{父记录}} ∪ sub[] 中 ability=8 的记录 {len(candidates)} 条，要求恰 1 条'
                       '（不按 sub[0] 假设、不取邻近记录）',
                       abilities=[parent.get('ability')] + [s['ability'] for s in subs])
    carrier = candidates[0]
    if carrier['form'] != tgt['carrier_form']:
        return _reject(gates, 'G8_CARRIER_FORM_CHANGED',
                       f'载体形态 {carrier["form"]!r} 与冻结 {tgt["carrier_form"]!r} 不符')
    sibling_abilities = sorted(s['ability'] for s in subs
                               if not (carrier['form'] == 'sub'
                                       and s['skillid'] == carrier['record_id']))
    if sibling_abilities != list(tgt['sibling_abilities']):
        return _reject(gates, 'G8_SIBLING_STRUCTURE_CHANGED',
                       f'sub 非载体兄弟能力号 {sibling_abilities} 与冻结 '
                       f'{list(tgt["sibling_abilities"])} 不符（记录变化，不静默沿用）',
                       sibling_abilities=sibling_abilities)
    _gate(gates, 'G8_TYPE8_CARRIER_NOT_UNIQUE', True,
          f'唯一 type8 载体：skillid={carrier["record_id"]} @ '
          f'{"/skilllist/%d" % carrier["index"]}（形态 {carrier["form"]}）；'
          f'非载体兄弟能力号 {sibling_abilities} 与冻结一致')

    # ---- G9 字段门
    record = carrier['record']
    states = {slot: raw_state(record, slot) for slot in CARRIER_SLOTS}
    raw = record.get(SLOT)
    if states[SLOT] != 'present' or not isinstance(raw, (int, float)) or isinstance(raw, bool) \
            or not math.isfinite(raw):
        return _reject(gates, 'G9_CLAIM_SLOT_NOT_PRESENT',
                       f'载体 /{SLOT} 状态={states[SLOT]}：不补零、不借相邻记录')
    if float(raw) <= 1.0:
        return _reject(gates, 'G9_DIRECTION_NOT_UP',
                       f'载体 /{SLOT}={raw!r} 不大于 1：与句面「攻撃力が上がる」方向不符')
    if states['param0'] != 'zero' or states['iParam0'] != 'zero':
        return _reject(gates, 'G9_CARRIER_HAS_CONDITION_SLOT',
                       f'载体 param0={record.get("param0")!r}／iParam0={record.get("iParam0")!r} '
                       '非 0：与冻结的 type8 常时基础载体结构不符（可能是条件载体），拒绝')
    if states['param2'] != 'present' or not _close(record.get('param2'), 1.0):
        return _reject(gates, 'G9_PARAM2_NOT_NEUTRAL',
                       f'载体 /param2={record.get("param2")!r} 非既有规则口径的中性 1')
    if states['param3'] != 'present' or not _close(record.get('param3'), 1.0):
        return _reject(gates, 'G9_PARAM3_NOT_NEUTRAL',
                       f'载体 /param3={record.get("param3")!r} 非既有规则口径的中性 1')
    _gate(gates, 'G9_CLAIM_SLOT_NOT_PRESENT', True,
          f'载体 /{SLOT}={raw!r}（present, >1）；param0/iParam0=0（冻结常时结构）；'
          'param2/param3=1（中性乘数，不携带移动/减伤值）', field_states=states)

    sentence_rows = [dict(index=s['index'], segment=s['segment'],
                          start=s['start'], end=s['end'], text=s['raw'],
                          core=s['core'], claimed=(s['index'] == fidx),
                          segment_first=(s['index'] == 0
                                         or sents[s['index'] - 1]['segment'] != s['segment']))
                     for s in sents]
    sibling_records = []
    for sub in subs:
        if carrier['form'] == 'sub' and sub['skillid'] == carrier['record_id']:
            continue
        sibling_records.append(dict(
            skillid=sub['skillid'], ability=sub['ability'], index=sub['index'],
            json_pointer=f'/skilllist/{sub["index"]}', sub_slot=sub['sub_slot'],
            params={k: sub['record'].get(k) for k in CARRIER_SLOTS
                    if sub['record'].get(k) is not None}))
    ids_for_cache = [sid] + [s['skillid'] for s in subs] + \
                    ([carrier['record_id']] if carrier['form'] == 'sub' else [])
    return dict(
        status='RESOLVED', reason=None, gates=gates, cid=cid, row_id=row.get('row_id'),
        charainfo=dict(table='charainfo', record_id=cid, index=idxs[0],
                       json_pointer=f'/charainfo/{idxs[0]}',
                       field_json_pointer=f'/charainfo/{idxs[0]}/skillid',
                       reference_field=ref, skillid_slot=slot_index,
                       source_key='APK/_mdCharacter.json'),
        parent=dict(table='skilllist', record_id=sid, index=pidx,
                    json_pointer=f'/skilllist/{pidx}', ability=parent.get('ability'),
                    text=parent.get('text'), record=parent),
        carrier=dict(table='skilllist', record_id=carrier['record_id'], index=carrier['index'],
                     json_pointer=f'/skilllist/{carrier["index"]}',
                     ability=CARRIER_ABILITY, form=carrier['form'],
                     sub_slot=carrier['sub_slot'], record=carrier['record'],
                     record_key=f'{APK_SKILLLIST_SOURCE_KEY}#/skilllist/{carrier["index"]}'),
        sub_abilities=[dict(skillid=s['skillid'], ability=s['ability'], index=s['index'],
                            sub_slot=s['sub_slot']) for s in subs],
        siblings=sibling_records,
        sibling_abilities=sibling_abilities,
        field_states=states,
        sentence=dict(index=fidx, segment=sent['segment'], clean_span=list(cspan),
                      raw_span=list(rspan), text=japanese,
                      substring_occurrences=clean.count(japanese),
                      sentence_occurrences=len(dups),
                      segment_first=sentence_rows[fidx]['segment_first']),
        sentences=sentence_rows,
        cues=cue_rows,
        cross_layer=cross_layer_block(data, cid, ids_for_cache),
        fragment=dict(row_id=row.get('row_id'), japanese=japanese,
                      parent_field_json_pointer=want + '/text', fragment_index=fidx),
    )


def _close(value, target):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value) and abs(float(value) - float(target)) < 1e-9


# ---------------------------------------------------------------- 排除登记（逐项、不并入）
def collect_exclusions(chain):
    """载体未主张槽位与兄弟记录：只登记，不产出答案（存在≠归属）。

    ``/param1`` 是本句唯一主张；``/param2``／``/param3`` 为既有规则已确认的中性乘数，
    其余 type8 无规则槽位只登记原值与状态。兄弟记录（type67／36／1040／64／96／97／1019）
    同样逐条登记并标 ``EXCLUDED_RECORD_NOT_THIS_SENTENCE``。
    """
    record = chain['carrier']['record']
    fields = []
    for slot in CARRIER_SLOTS:
        if slot == SLOT:
            continue
        state = chain['field_states'].get(slot) or raw_state(record, slot)
        value = record.get(slot)
        if state in ('missing', 'null'):
            code, detail = 'EXCLUDED_FIELD_ABSENT', '载体无该字段（缺席＝不产出，不补零）'
        elif state == 'zero':
            code, detail = 'EXCLUDED_FIELD_ZERO', '载体存 0；不当作答案（不补零）'
        elif slot in ('param2', 'param3') and _close(value, 1.0):
            code, detail = ('EXCLUDED_FIELD_NEUTRAL',
                            '既有规则口径的中性乘数 1：该记录不携带移动/减伤值，本句亦未主张')
        elif slot in TYPE8_RULE_SLOTS:
            code, detail = 'EXCLUDED_FIELD_NOT_CLAIMED', '载体有值，但本句未主张该属性：不并入'
        else:
            code, detail = ('EXCLUDED_FIELD_NO_TYPE8_RULE',
                            'type8 无该槽位已确认规则，且本句未主张：只登记原值，不解释')
        fields.append(dict(slot=slot, state=state, raw_value=value, code=code, detail=detail))

    records = []
    for sub in chain.get('siblings') or []:
        records.append(dict(
            skillid=sub['skillid'], ability=sub['ability'], index=sub['index'],
            json_pointer=sub['json_pointer'], sub_slot=sub['sub_slot'],
            params=dict(sub['params']),
            code='EXCLUDED_RECORD_NOT_THIS_SENTENCE',
            detail=('同父其他能力记录：登记为可能承载本句之外条件/其他效果的记录（对应关系为推断，'
                    '本批不确认其语义）；不借值、不并入、不跨记录相乘')))
    if chain['carrier']['form'] == 'sub':
        records.append(dict(
            skillid=chain['parent']['record_id'], ability=chain['parent']['ability'],
            index=chain['parent']['index'], json_pointer=chain['parent']['json_pointer'],
            sub_slot=None,
            params={k: chain['parent']['record'].get(k) for k in CARRIER_SLOTS
                    if chain['parent']['record'].get(k) is not None},
            code='EXCLUDED_PARENT_NOT_THIS_SENTENCE',
            detail=('父记录（能力号≠8）：其 param 按该能力号的其他语义登记，本模块不借值、'
                    '不并入、不推断其句面归属')))
    return fields, records


# ---------------------------------------------------------------- 答案构造（G9/G10）
def _source_block(chain):
    carrier = chain['carrier']
    return {
        'layer': 'APK',
        'table': 'skilllist',
        'record_id': carrier['record_id'],
        'record_index': carrier['index'],
        'record_key': carrier['record_key'],
        'source_key': APK_SKILLLIST_SOURCE_KEY,
        'original_file': APK_SKILLLIST_REL,
        'json_pointer': carrier['json_pointer'],
        'field_path': '/' + SLOT,
        'field': '/' + SLOT,
        'field_json_pointer': f'{carrier["json_pointer"]}/{SLOT}',
        'carrier_slot': ('parent' if carrier['form'] == 'parent'
                         else f'sub[{carrier["sub_slot"]}]'),
        'carrier_ability': CARRIER_ABILITY,
        'parent_record_id': chain['parent']['record_id'],
        'parent_record_index': chain['parent']['index'],
        'parent_json_pointer': chain['parent']['json_pointer'],
        'parent_text': chain['parent']['text'],
        'charainfo': chain['charainfo'],
        'row_fragment': chain['fragment'],
        'sentence': dict(chain['sentence']),
        'sentences': [dict(s) for s in chain['sentences']],
        'cues': [dict(c) for c in chain['cues']],
        'sub_abilities': [dict(s) for s in chain['sub_abilities']],
        'cross_layer': chain['cross_layer'],
        'source_resolution': RESOLVED_EXACT,
    }


def _retained_old_rejections(row):
    """旧 B3／B4／B11 拒绝原因逐条保留（原文照抄，不改写、不删除）。"""
    out = []
    for key, source in (('inference_b3_hint', 'B3_type8'), ('inference_b4_hint', 'B4_cond')):
        text = row.get(key)
        if text:
            out.append(dict(source=source, field=key, text=str(text), retained=True,
                            scope_note=('旧模板按整行/段中句口径的拒绝原因保留；本项只按单个 effect '
                                        '的整句 span 绑定唯一 type8 记录的 /param1，不放宽旧模板')))
    if not out:
        out.append(dict(source='B3_B4', field=None, retained=True,
                        text='该行在旧批中未登记 B3/B4 hint（父记录能力号不是 8，或句面不在 type8 模板域）',
                        scope_note='未登记不等于已放行：本项证据独立按 G1–G11 重建'))
    out.append(dict(
        source='B11_SA1095', field=None, retained=True,
        text=('B11 域是 CACHE ability1095 自身增益（APK 52 sub/35 父登记为 carrier-out-of-domain）；'
              '本项载体能力号为 8，不是 1095'),
        scope_note=('本模块不复用 B11 的 skilllist|1095|/param1，也不据 B11 域外结论放行任何 1095 行；'
                    '本项只用既有 skilllist|8|/param1')))
    return out


def player_sentence(raw, target):
    """玩家可读中文（§1.3）：对象／数值／单位／条件／未并入部分／未解边界。"""
    pct = (float(raw) - 1.0) * 100.0
    return (f'自身攻击力提高 {percent_text(pct)}%'
            f'（本能力单独生效时攻击力变为 {num_text(raw)} 倍）。'
            f'本项只对应「{SENTENCE_ZH}」这一句；同一能力描述中其他句子写的其他效果'
            f'（{target["out_of_sentence_summary"]}）不并入本项；最终数值未实机验证。')


def build_answer(chain, target, data):
    """按冻结 target 构造单条答案；字段缺失/零/规则缺失 → ``(None, reason)``。"""
    carrier = chain['carrier']['record']
    state = chain['field_states'].get(SLOT)
    if state != 'present':
        return None, dict(code='FIELD_' + state.upper(),
                          detail=f'type8 载体 skillid={chain["carrier"]["record_id"]} 字段 /{SLOT} '
                                 f'状态={state}：不补零、不借相邻记录')
    raw = carrier[SLOT]
    rule = R.answer_for('skilllist', CARRIER_ABILITY, '/' + SLOT, raw, carrier,
                        source_layer='APK')
    if not rule:
        return None, dict(code='RULE_MISSING',
                          detail=f'rules.answer_for 未返回 skilllist|8|/{SLOT}')

    conditions = [
        '接受者自身已装载该能力，且对应能力列表/类型分派（能力编号 8）通过时生效'
        '（type8 常时「IsEnableAbility 无条件下通过」）',
        '仅本句「攻撃力が上がる。」的局部贡献；同段其他句子写的条件增强与其他效果不并入',
        '本句无对象限定词（无味方/敵/範囲等），按 type8 原生对象＝装有者自身',
        '本条来自 APK 内置主表静态记录；运行时装载与资格未实机验证',
    ]
    unknowns = [
        '运行时实际装载与资格未核实（未实机）',
        '与其他来源的实际叠加与最终战斗数值未验证',
        '本句面到该 type8 记录 /param1 的归属为推断，不当作完整语义确认',
        f'同段其他句子的条件强化（{target["out_of_sentence_summary"]}）未并入本项，其数值另论',
        'APK 与 CACHE 命名空间不合并：本批 3 个 cid 在 CACHE 无同号记录（见 source.cross_layer）',
    ]
    fields, records = collect_exclusions(chain)
    answer = {
        'value': rule.get('value_text'),
        'normalized_value': normalized_value(raw),
        'player_text': player_sentence(raw, target),
        'player_scope': {
            'object': '自身（能力装载者）',
            'quantity': rule.get('quantity_kind'),
            'unit': UNIT,
            'conditions': conditions,
            'duration': '本句未涉及持续时间；同段的「一定時間」类描述属于其他句子，未纳入本项',
            'unknowns': unknowns,
        },
        'quantity_kind': rule.get('quantity_kind'),
        'unit': UNIT,
        'rule_unit': rule.get('unit'),
        'raw_value': raw,
        'field_path': '/' + SLOT,
        'numeric_source': ('既有已确认规则（profiles/rules.json 的 ' + RULE_KEY +
                           '；证据 skilllist_types/native_checks.json、GetAbilityAttack '
                           '分支 0x1107958，换算复用 ordinary_effects/ability7）'
                           '＋APK 内置主表 skilllist 原始记录'),
        'numeric_evidence': '确认',
        'association_evidence': '推断',
        'answer_status': rule.get('answer_status'),
        'evidence_scope': SCOPE,
        'rule_key': RULE_KEY,
        'table': 'skilllist',
        'record_id': chain['carrier']['record_id'],
        'layer': 'APK',
        'target': rule.get('target'),
        'conversion': rule.get('conversion'),
        'base_definition': rule.get('base_definition'),
        'conditions': '；'.join(conditions),
        'rule_applicability': rule.get('conditions'),
        'rule_limits': rule.get('rule_limits'),
        'rule_status': rule.get('rule_status'),
        'original_text': chain['fragment'].get('japanese'),
        'not_included': {
            'sentence_scope': f'仅「{target["sentence"]}」这一句（整句 span）',
            'out_of_sentence_cues': [dict(c) for c in chain['cues']],
            'out_of_sentence_summary': target['out_of_sentence_summary'],
            'other_sentences': [dict(index=s['index'], segment=s['segment'], text=s['core'],
                                     claimed=s['claimed'])
                                for s in chain['sentences'] if not s['claimed']],
            'sibling_records': records,
            'extra_slots_excluded': fields,
            'retained_old_rejections': _retained_old_rejections(chain.get('row') or {}),
            'note': ('条件句、其他属性与其他效果按兄弟记录登记（对应关系为推断），逐项登记但不并入；'
                     '本项不是整条能力记录的合计，也不跨记录相乘'),
        },
        'excluded_carrier_fields': fields,
        'source': _source_block(chain),
        'binding': {'c19_p2_type8_basic_attack_binding': {
            'scope': SCOPE,
            'row_id': target['row_id'],
            'effect_id': target['effect_id'],
            'claim': target['claim'],
            'slot': SLOT,
            'rule_key': RULE_KEY,
            'carrier_table': 'skilllist',
            'carrier_record_id': chain['carrier']['record_id'],
            'carrier_layer': 'APK',
            'carrier_form': chain['carrier']['form'],
            'carrier_slot': ('parent' if chain['carrier']['form'] == 'parent'
                             else f'sub[{chain["carrier"]["sub_slot"]}]'),
            'parent_record_id': chain['parent']['record_id'],
            'charainfo_record_id': chain['cid'],
            'sentence_index': chain['sentence']['index'],
            'segment_index': chain['sentence']['segment'],
            'clean_span': chain['sentence']['clean_span'],
            'raw_span': chain['sentence']['raw_span'],
            'raw_value': raw,
            'binding': 'inferred',
            'runtime_verified': False,
        }},
        'details': rule,
    }
    return answer, None


# ---------------------------------------------------------------- 公开 API
def evaluate(data, cid, row, *, scope=None, skill=None):
    """解析单行并返回候选答案（不写入）。``scope`` 缺省/错误/空 → ``ScopeError``。"""
    require_scope(scope)
    out = dict(cid=cid, row_id=row.get('row_id'), scope=scope,
               module_version=MODULE_VERSION, answers=[], rejected=[],
               excluded_fields=[], excluded_records=[], matched_effects=[],
               missing_targets=[])
    target = BY_ROW.get((cid, row.get('row_id')))
    if target is None:
        out['status'] = 'ROW_OUT_OF_SCOPE'
        out['reason'] = 'ROW_NOT_IN_FROZEN_SCOPE'
        return out

    # 兄弟记录在链解析阶段已按真实下标解引用并冻结（无跨行全局状态）。
    chain = resolve_chain(data, cid, row, skill=skill, target=target)
    out['chain'] = dict(status=chain['status'], reason=chain.get('reason'),
                        detail=chain.get('detail'), gates=chain.get('gates') or [],
                        carrier=(None if chain['status'] != 'RESOLVED' else dict(
                            record_id=chain['carrier']['record_id'],
                            index=chain['carrier']['index'],
                            form=chain['carrier']['form'],
                            carrier_slot=chain['carrier']['sub_slot'],
                            parent_record_id=chain['parent']['record_id'],
                            parent_index=chain['parent']['index'])),
                        field_states=chain.get('field_states'),
                        sentence=chain.get('sentence'),
                        cross_layer=chain.get('cross_layer'))
    if chain['status'] != 'RESOLVED':
        out['status'] = 'REJECTED'
        out['reason'] = chain.get('reason')
        return out
    chain['row'] = row

    analysis = LEDGER.analyze_row(row, table='skilllist')
    effects = [e for e in analysis.get('effects') or []
               if e.get('record_type') == 'effect' and '#e' in e.get('effect_id', '')]
    by_id = {e['effect_id']: e for e in effects}
    effect = by_id.get(target['effect_id'])
    if effect is None:
        out['missing_targets'].append(dict(effect_id=target['effect_id'],
                                          detail='该 effect_id 未出现在当前解析结果'))
        out['status'] = 'RESOLVED_PARTIAL'
        return out
    claim_ok = (effect.get('effect_type') == target['claim']
                and effect.get('direction') in (None, 'up'))
    out['matched_effects'].append(dict(
        effect_id=target['effect_id'], effect_type=effect.get('effect_type'),
        direction=effect.get('direction'), status_before=effect.get('status'),
        claim_expected=target['claim'], claim_matches=claim_ok))
    if not claim_ok:
        out['rejected'].append(dict(effect_id=target['effect_id'], slot=target['slot'],
                                    code='CLAIM_MISMATCH',
                                    detail=f'行内 effect {effect.get("effect_type")!r}／'
                                           f'{effect.get("direction")!r} 与冻结主张 '
                                           f'{target["claim"]!r}（上升）不符'))
    else:
        answer, why = build_answer(chain, target, data)
        if answer is None:
            out['rejected'].append(dict(effect_id=target['effect_id'],
                                        slot=target['slot'], **why))
        else:
            out['answers'].append(answer)

    fields, records = collect_exclusions(chain)
    out['excluded_fields'] = fields
    out['excluded_records'] = records
    out['status'] = 'RESOLVED_ALL' if len(out['answers']) == 1 else 'RESOLVED_PARTIAL'
    out['analysis_summary'] = dict(
        effect_status=[dict(effect_id=e['effect_id'], effect_type=e['effect_type'],
                            status=e['status']) for e in effects],
        split_flags=analysis.get('split_flags'),
        unmatched_answer_refs=[r for r in analysis.get('answer_refs') or []
                               if r.get('matched_effect_id') is None])
    return out


def apply_to_groups(data, cid, groups, *, scope=None):
    """把 C19-P2 答案写入 ``build_card`` 产出的 groups（仅内存）；幂等，第二次 0 新增。"""
    require_scope(scope)
    report = dict(cid=cid, scope=scope, module_version=MODULE_VERSION,
                  status='OUT_OF_SCOPE', rows=[], added=0, skipped=0, conflicts=0,
                  rejected=0, excluded_fields=0, excluded_records=0)
    if cid not in TARGET_CIDS:
        report['detail'] = (f'cid={cid} 不在 C19-P2 三项白名单：零新增'
                            '（保护卡/相邻已交付卡结构上不可达）')
        return report
    report['status'] = 'APPLIED'
    for group in groups or []:
        for skill in group.get('skills') or []:
            for row in skill.get('rows') or []:
                rid = row.get('row_id')
                if rid not in TARGET_ROW_IDS.get(cid, set()):
                    continue
                result = evaluate(data, cid, row, scope=scope, skill=skill)
                entry = dict(row_id=rid, status=result['status'],
                             reason=result.get('reason'),
                             matched_effects=result.get('matched_effects'),
                             rejected=result.get('rejected'),
                             excluded_fields=result.get('excluded_fields'),
                             excluded_records=result.get('excluded_records'),
                             added=0, skipped=0, conflicts=0)
                if result['status'] == 'REJECTED':
                    report['rejected'] += 1
                    report['rows'].append(entry)
                    continue
                existing = row.setdefault('answers', [])
                for answer in result['answers']:
                    same = [a for a in existing
                            if a.get('rule_key') == answer.get('rule_key')
                            and a.get('field_path') == answer.get('field_path')]
                    if same:
                        if all(a.get('raw_value') == answer.get('raw_value') for a in same):
                            entry['skipped'] += 1
                            report['skipped'] += 1
                        else:
                            entry['conflicts'] += 1
                            report['conflicts'] += 1
                        continue
                    existing.append(answer)
                    entry['added'] += 1
                    report['added'] += 1
                entry['excluded_fields'] = result.get('excluded_fields')
                entry['excluded_records'] = result.get('excluded_records')
                report['excluded_fields'] += len(result.get('excluded_fields') or [])
                report['excluded_records'] += len(result.get('excluded_records') or [])
                report['rows'].append(entry)
    return report


def scope_dump():
    """机器可读冻结作用域（只含身份与结构，不含 raw／value／载体记录 ID）。"""
    return dict(module_version=MODULE_VERSION, scope=SCOPE,
                targets=[dict(t) for t in TARGETS],
                protected_cids=list(PROTECTED_CIDS),
                adjacent_delivered_cids=list(ADJACENT_DELIVERED_CIDS),
                counts=dict(items=len(TARGETS), cids=len(TARGET_CIDS),
                            rows=len(BY_ROW), slots=[SLOT], rule_keys=[RULE_KEY]))


def module_hashes(root):
    """模块与关键输入的 SHA-256（README/检查结果记录用）。"""
    root = Path(root)
    files = [Path(__file__), _HERE / 'effect_ledger.py', _HERE / 'rules.py',
             _HERE / 'card_page_data.py',
             root / 'output/character_skills/profiles/rules.json',
             root / APK_SKILLLIST_REL, root / APK_CHARAINFO_REL]
    return {str(p.relative_to(root)).replace('\\', '/'): sha256_file(p) for p in files}
