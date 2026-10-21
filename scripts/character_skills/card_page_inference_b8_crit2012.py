"""模板作用域推断层——批 8：暴击增益（bossskill.s_ability→skilllist ability2012 真实链）。

设计与范围依据：``output/character_skills/inference_inventory/b8_crit2012_scope.md``
（批 8 前置审计；逐行明细 work/character_skills_b8_crit2012/b8_rows_classified.json：
候选池＝C 行∪批 6/7 hint 行且含 クリティカル＝全库 3,837 行／Y.G. 629 行；实测晋级候选
**全库 343 行（~686 值行）／Y.G. 159 行（~318 值行）**——bosspattern 224／denju 83／
charainfo 36、122 cid（Y.G. 60）〔审计预分类口径；实施含 20607 系三行跨层链晋级后实际为
bosspattern 225／denju 84／charainfo 37、123 cid＝346 行，差异来源见 pages/README.md
§21.3——B8-R03 计数注记〕；其余 3,494 行按逐行原因留 hint。实施逐行审核还可能
再收缩（非承诺值）。）

关键结构（cid349 先例，audit_samples.py 独立重建链逐记录核实）：bosspattern
（``/bossinfo/bosspattern/N``，skillidN）→ bossskill（skillid0=13，s_ability 字段）→
skilllist（ability=2012，SA_SupportTarget）载体上的 ``/param4``（暴击率加算，pp）与
``/param5``（暴伤系数加算）。批 6 hint 原因「p4/p5 原值 None/None」对 bossskill 记录
本身正确，但漏了链上 2012 载体——**bossskill|13 无 crit 槽规则与「crit 值在 s_ability
指向的 2012 记录上」两个事实相容**。profiles 层已以 ``link_kind='boss_skill.s_ability'``
解析该链且子记录带全 answers（40034914：/param0+/param4+/param5 三条
CONFIRMED_NUMERIC IN_REVIEWED_VIEW）——本模块运行时复用 links/profiles 既有解析
（boss_skill_refs／sa_ability_refs／denju_pattern_refs 均带完整 raw record，全部已解析，
实测 0 条 unresolved），不重读解码 JSON、不需要新解析器。

精确范围（scope §4.1，门控 G1–G8 全部通过才晋级；任一不过→留 hint 并登记原因）：

* 行记录表 ``table ∈ {bosspattern, charainfo, denju, denju_limit_break_info,
  heroicskilllist}``，日文含 クリティカル（覆盖 クリティカル発生率/威力；实测无
  暴撃/クリ率 独立词形），晋级前无既有答案（调用点 ``not answers`` 守卫）；
* **G1 句归属**：行 japanese 是行源父记录正文（bosspattern.sinfo／denju.stext／
  charainfo 经同页同文 pattern 行的 sinfo，b6 G5/G7 同法）恰 1 次子串；
* **G2 链可达**：父记录 patternidN→pattern→skillidN 槽位→bossskill（links 全部已
  解析，槽位未唯一对位→hint）；bosspattern 行以行记录 raw 的 skillidN 槽位逐一对位
  boss_skill_refs（防漏中继）；denju/dlb 行 pattern raw 不在页内，按
  boss_skill_refs.reference_field 的 ``bosspattern[pid]`` 分组枚举；
* **G3 载体唯一**：pattern 链上 t13→s_ability→2012 载体恰 1 个（0→hint:
  no-2012-chain；≥2→hint:multi-carrier）。中继必须 type13（非 13 中继→hint:
  relay-non13——2012 规则虽按 skilllist 记录生效，但行→记录的句子归属模型以 cid349
  先例的 t13 形状为准，非 t13 中继的语义耦合无先例，不猜）；
* **G4 属性形状**：句含クリティカル発生率⇔载体 /param4 活性（存在且≠0）；句含
  クリティカル威力⇔/param5 活性；载体活性 crit 槽不得超出句面主张（防跨段误配）；
  缺槽＝缺失不补 0（rules limits：param4/5 缺失保持缺失，不导出默认 0）；
* **G5 样本域**：载体层==CACHE 且 id ∈ 当前 v3 CACHE 普通 ability2012 的 406 条
  规则样本域（decoded skilllist 实测同集）；APK 载体→hint（域外，不扩域；
  批 7 §6 E4 同口径）；
* **G6 对象相容**：句面对象 vs 载体 /param8（31=pGROUP_ALL／64=MYSELF）：味方全体×64
  →hint；自身×31→hint；句无对象词→hint:object-unstated。p8 只作相容核对
  （trigger_context 输入，未推广为独立字段规则——ability2012 README 口径逐字披露）；
* **G7 方向**：句「上がる/上がり/上げる」且 p4/p5>0；「下がる」→hint（实测候选 0 例）；
  无方向词→hint:direction-unstated；
* **G8 同 cid 多表行／跨 cid 守卫**：pattern/charainfo/denju 行各自出值行、各自注来源
  （denju stext 为同技能文本的标题变体抄本，非競争）；跨 cid 同载体→hint（审计
  交叉检查实测 0 例；守卫为进程内登记，跨 cohort 进程不共享——以审计全库 0 例为准）。

映射与值行（scope §4.2；值行 rule_key 只允许 ``skilllist|2012|/param4|/param5``）：

================  =========================  ==============================================
句中成分          规则键                      值行数量类型（rules.py 换算器）
================  =========================  ==============================================
クリティカル発生率 /param4                     暴击率加算（+原值×100 个百分点，对 0 加算；
                                             非「以 N% 概率施加」）
クリティカル威力  /param5                     暴伤系数增量 +原值（不减 1095 的 1.5 基准）
一定時間（本链）  载体 /param0                **D1 裁决：时长值行仍归批 6 t13 /skillparam3**；
                                             b8 不出 p0 值行，仅在 note 登记载体 p0
                                             （trigger_context）
非 crit 属性      —（bossskill t13 侧）        批 6 逻辑；b8 不重复出值行（既有 hint 保留原状）
================  =========================  ==============================================

硬边界（scope §4.2/§5，逐行强制）：

* **只升「推断」，绝不升「确认」**：值行 numeric_evidence/association_evidence 一律
  「推断」；行级标注「推断（模板批 8 暴击 2012 链）」、evidence_scope=
  TEMPLATE_BATCH8_CRIT2012（行级 metadata 键 ``inference_b8``，与
  inference_pilot/b3/b4/b5/b6/b7 并列）；不进整行确认统计；「唯一 type13 中继＋
  s_ability 字段＋形状匹配」是数据侧结构对应，永不据此升「确认」。
* **规则本体与本条归属分开披露**：值行 note 固定写明「规则本体：已确认（静态及受控
  原生局部规则，occurrences 308/311）——指规则本身；本条数值归属＝推断（模板批 8），
  不升确认」；rule_body_status/rule_status 字段保留 rules.json 原值（渲染层按
  B5-R01 方案 A 限定口径显示，不裸露「已确认」）。
* **证据按字段**（INFR-01）：值行 evidence 取 rules.json ``skilllist|2012|/param4|/param5``
  的 evidence——``critical/*``（origin 根 output/card_comparison_cid30236/）＋
  ``../ordinary_effects/ability2012/*``；存在性检查，缺失显式失败（不产出死指针）。
* **样本域披露按登记口径**（INFR-02）：三条规则 occurrences（406/308/311）已登记且
  前置审计与 v3 CACHE 实测交叉验证一致→逐行按登记口径披露（比批 6 bossskill|13
  occ=None 的外推披露强）；本行来源载体记录未逐条核对，不属逐记录确认。
* **条件/对象逐字披露（双源）**：句面触发文本（その後、/必殺技発動時/共鳴/HP 阈值等）
  与对象短语（味方全体の/自身の 等）逐字入 note；记录侧＝ability2012 README
  （OnActionSkillAbility 附加能力阶段、非暴击命中触发、setSupport2、param0/4/5 原样
  写入不乘 Chain、Support2 上限 [0,.5]/[-1.5,1]、31 不是 1017 职业位图且 GROUP_ALL
  不等于全部必然选中）。
* **不跨记录合并**：同 cid 的 pattern/charainfo/denju 行各自出值行；同载体多句＝同技能
  文本抄本；载体句外槽（param0/1/2/3/6/7/8/9、iParam*）只登记原值不分配给本句；
  普通 1110→1095 自身增益暴击段单列不进本批（普通 skilllist 行不在本批表集）；
  b7 共鳴家族行（sympathy 组）不在本批表集。
* **既有行不动**：A 行 1,217 含 crit 不动（``not answers`` 守卫）；批 1–7 晋级键与
  hint 键不重写；30236 基线不动。
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import rules as R
import card_page_inference_type8 as TYPE8
import card_page_inference_b6_bossbuff as B6

B8_TAG = '推断（模板批 8 暴击 2012 链）'
B8_SCOPE = 'TEMPLATE_BATCH8_CRIT2012'
B8_FAMILY = ('クリティカル発生率／クリティカル威力が（一定時間）上がる。'
             '（bosspattern/denju/charainfo 行→bossskill type13 中继→s_ability→'
             'skilllist ability2012 载体）')

TABLES = ('bosspattern', 'charainfo', 'denju', 'denju_limit_break_info', 'heroicskilllist')

# ---- 句面属性/对象/方向（审计 scan_b8_rows.py sent_attrs/sent_object/sent_direction 逐字沿用）----
CRIT_TRIGGER = 'クリティカル'


def _sent_attrs(j):
    return (('クリティカル発生率' in j) or ('クリ発生率' in j),
            ('クリティカル威力' in j) or ('クリ威力' in j))


def _sent_direction(j):
    if '下がる' in j or '下がり' in j:
        return 'down'
    if '上がる' in j or '上がり' in j or '上げる' in j:
        return 'up'
    return '?'


def _sent_object(j):
    if '味方全体' in j or '全ての味方' in j:
        return 'ally_all'
    if '自身' in j:
        return 'self'
    if '味方' in j:
        return 'ally'
    return '?'


_OBJECT_PHRASE = (('味方全体', '味方全体'), ('全ての味方', '全ての味方'), ('自身', '自身'), ('味方', '味方'))

# ---- INFR-01：rules.json skilllist|2012|/param4|/param5 的 evidence 相对路径解析 ----
_CARD_COMPARISON_ROOT = 'output/card_comparison_cid30236/'
_EVIDENCE_EXPECTED = {'param4': (_CARD_COMPARISON_ROOT + 'critical/',
                                 'output/ordinary_effects/ability2012/'),
                      'param5': (_CARD_COMPARISON_ROOT + 'critical/',
                                 'output/ordinary_effects/ability2012/')}
_EVIDENCE_CACHE = {}

_REGISTERED_RULES = None


def _registered_rule(param):
    """profiles/rules.json 登记的规则条目（origin 权威来源；B6-RV-02 同法：rules.py 合并
    源条目无 origin 键，直接读会打印「origin None/未登记」——不属实。profiles/ 为本批
    只读共享依赖，已在 card_page_dependencies.data_paths 声明清单内）。"""
    global _REGISTERED_RULES
    if _REGISTERED_RULES is None:
        p = Path('output/character_skills/profiles/rules.json')
        _REGISTERED_RULES = json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}
    return _REGISTERED_RULES.get(f'skilllist|2012|/{param}') or {}


def _field_evidence(param):
    """按字段解析 rules.json skilllist|2012|/paramN 的 evidence 并做存在性检查（INFR-01）。"""
    if param in _EVIDENCE_CACHE:
        return _EVIDENCE_CACHE[param]
    rule = R.rule_for('skilllist', 2012, '/' + param)
    files = []
    for entry in (rule or {}).get('evidence') or []:
        items = entry if isinstance(entry, (list, tuple)) else [entry]
        for e in items:
            e = str(e)
            files.append('output/' + e[3:] if e.startswith('../') else _CARD_COMPARISON_ROOT + e)
    dirs = _EVIDENCE_EXPECTED[param]
    if not files or any(not p.startswith(dirs) for p in files):
        raise ValueError(f'批 8 证据解析异常（INFR-01）：skilllist|2012|/{param} 的 rules.json '
                         f'evidence 未解析为 {dirs} 下的文件，实际 {files!r}')
    missing = [p for p in files if not Path(p).is_file()]
    if missing:
        raise FileNotFoundError(f'批 8 证据文件缺失（INFR-01）：{missing}')
    _EVIDENCE_CACHE[param] = (dirs, files)
    return _EVIDENCE_CACHE[param]


# ---- G5 样本域：当前 v3 CACHE 普通 ability2012 的 406 条记录（decoded skilllist 实测）----
_DOMAIN_CACHE = {}


def _r2012_domain(data):
    key = id(data)
    hit = _DOMAIN_CACHE.get(key)
    if hit is not None:
        return hit[1]
    domain = {sid for sid, (_, rec) in data.cache_skill.items() if rec.get('ability') == 2012}
    _DOMAIN_CACHE[key] = (data, domain)  # 连同 data 持强引用，避免 id 复用串页
    return domain


# ---- G2 链可达：pattern→skillidN→bossskill(type13)→s_ability→skilllist(2012) ----
_SLOT_RE = re.compile(r'^skillid\d+$')
_RF_PATTERN = re.compile(r'bosspattern\[(\d+)\]')


def _relay_entries(pid, precord, boss_skill_refs):
    """枚举一个 pattern 上的 bossskill 中继（links boss_skill_refs 全部已解析，实测 0
    unresolved）。precord 给定时（bosspattern 行＝行记录自身；charainfo 行＝同页同文
    pattern 记录）按 raw skillidN 槽位逐一对位（防漏中继）；否则（denju/dlb 行 pattern
    记录不在页内）按 reference_field 的 bosspattern[pid] 分组枚举已解析槽位。
    返回 (entries, gaps)：entries=[(slot, ref), …]；gaps=链完整性缺口说明列表。"""
    entries, gaps = [], []
    if precord is not None:
        slots = [(k, v) for k, v in precord.items() if _SLOT_RE.match(k) and isinstance(v, int) and v]
        by_slot = {}
        for b in boss_skill_refs or []:
            if b.get('slot') and b.get('record'):
                by_slot.setdefault(b['slot'], []).append(b)
        raw_slots = {s for s, _ in slots}
        for slot, bsid in slots:
            cand = [b for b in by_slot.get(slot, []) if str(b.get('reference_id')) == str(bsid)]
            if len(cand) != 1:
                gaps.append(f'pattern 槽位 {slot}={bsid} 的 bossskill 在 links 未唯一解析'
                            f'（{len(cand)} 条）')
                continue
            entries.append((slot, cand[0]))
        for slot, lst in sorted(by_slot.items()):
            if slot not in raw_slots:
                gaps.append(f'links 槽位 {slot}（{lst[0].get("reference_id")}）不在 pattern raw '
                            'skillidN 槽位中（链完整性异常）')
    else:
        for b in boss_skill_refs or []:
            if not b.get('slot') or not b.get('record'):
                continue
            m = _RF_PATTERN.search(str(b.get('reference_field') or ''))
            if m is None or m.group(1) != str(pid):
                continue
            entries.append((b.get('slot'), b))
    return entries, gaps


def _carrier_of(bentry, sa_ability_refs, data):
    """中继 bossskill 的 s_ability 目标 skilllist 记录（links sa_ability_refs 优先；
    未挂载时回退 data.skill 解码索引——dlb 链实测走此回退，APK 载体随后被 G5 拦截）。"""
    brec = bentry.get('record') or {}
    tgt = brec.get('s_ability')
    if not (isinstance(tgt, int) and not isinstance(tgt, bool) and tgt):
        return None
    se = next((x for x in sa_ability_refs or []
               if str(x.get('parent_skill')) == str(bentry.get('reference_id'))
               and str(x.get('reference_id')) == str(tgt)), None)
    if se is not None and se.get('record'):
        return dict(record=se['record'], layer=se.get('layer'), via='links sa_ability_refs')
    w = data.skill(tgt)
    if w is None:
        return None
    return dict(record=w['record'], layer=w['layer'],
                via=f'data.skill 解码索引回退（links sa_ability_refs 未挂载；s_ability={tgt}）')


def _pattern_carriers(pid, precord, boss_skill_refs, sa_ability_refs, data):
    """一个 pattern 的 t13→s_ability→2012 载体（uniq by (carrier_id, layer)）＋
    非 t13 中继登记＋链缺口。中继类型≠13 但 s_ability 指向 2012 的记入 relay_non13
    （audit 同法；不指向 2012 的中继不登记）。"""
    entries, gaps = _relay_entries(pid, precord, boss_skill_refs)
    carriers, relay_non13 = [], []
    for slot, b in entries:
        brec = b.get('record') or {}
        tgt = brec.get('s_ability')
        if not (isinstance(tgt, int) and not isinstance(tgt, bool) and tgt):
            continue
        c = _carrier_of(b, sa_ability_refs, data)
        if c is None:
            gaps.append(f'中继 bossskill|{b.get("reference_id")}|{b.get("layer")} 的 '
                        f's_ability={tgt} 未解析到 skilllist 记录（链缺口）')
            continue
        crec = c['record']
        if (crec or {}).get('ability') != 2012:
            continue
        ent = dict(carrier_id=tgt, layer=c['layer'], record=crec, via=c['via'],
                   relay_id=b.get('reference_id'), relay_layer=b.get('layer'),
                   relay_type=brec.get('skillid0'), relay_slot=slot, pattern_id=pid)
        (carriers if brec.get('skillid0') == 13 else relay_non13).append(ent)
    uniq = {}
    for e in carriers:
        uniq.setdefault((e['carrier_id'], e['layer']), e)
    return list(uniq.values()), relay_non13, gaps


def _pattern_ids(rec, prefix='patternid'):
    return [(k, v) for k, v in rec.items() if k.startswith(prefix)
            and isinstance(v, int) and not isinstance(v, bool) and v]


# ---- G8 守卫：跨 cid 同载体主张（进程内登记；审计全库交叉检查实测 0 例）----
_CLAIMS = {}


# ---- B8-R01/R02 微修（20261021 定向审查，披露专用，不改判定）：bossinfo 索引 ----
# CACHE 解码 bossinfo 与 APK _mdBossInfo 均在 card_page_dependencies.data_paths 声明清单内；
# 只读索引，用于 ①heroic 行 boss_pattern 链的实际原因登记（原「记录无 pattern 字段」不实）
# ②denju/dlb 多 pattern 行的多条 type13 中继同指唯一载体的如实披露。
_BI_CACHE = None


def _bossinfo_idx():
    global _BI_CACHE
    if _BI_CACHE is None:
        cache = json.loads(Path('output/cache_full_20261015_v3/decoded/'
                                'bossinfo.data5.json.raw').read_text(encoding='utf-8'))['bossinfo']
        apk = json.loads(Path('output/base_master/_mdBossInfo.json').read_text(encoding='utf-8'))
        _BI_CACHE = ({r.get('patternid'): r for r in cache['bosspattern']},
                     {r.get('skillid'): r for r in cache['bossskill']},
                     {r.get('patternid'): r for r in apk['bosspattern']},
                     {r.get('skillid'): r for r in apk['bossskill']})
    return _BI_CACHE


def _s_ability_desc(brec, plat, data):
    """一条中继 bossskill 的 s_ability 目标描述（含目标 skilllist 层与 ability，若有）。"""
    sa = brec.get('s_ability')
    if isinstance(sa, int) and not isinstance(sa, bool) and sa:
        w = data.skill(sa)
        ab = (w['record'] or {}).get('ability') if w else None
        tlay = w['layer'] if w else '?'
        return sa, (f's_ability={sa}→skilllist|{sa}|{tlay} ability={ab}'), (ab == 2012)
    return sa, f's_ability={sa!r}（无 s_ability 指向）', False


def _heroic_chain_hint(record, data, subject_phrase, claims):
    """B8-R01（披露专用，恒返回 hint 或 None，不改晋级判定）：heroicskilllist 记录实有
    boss_patternN 字段——原 hint 文案「记录无 pattern 字段」不实。按实际链解析登记原因：
    逐条 boss_pattern 解析 pattern→skillidN 槽位→bossskill 中继（类型）→s_ability 目标
    （skilllist 层与 ability），链上无 s_ability→2012 即如实写明（no-2012-chain）。"""
    pats = [(k, v) for k, v in record.items()
            if re.match(r'^boss_pattern\d*$', k) and isinstance(v, int)
            and not isinstance(v, bool) and v]
    if not pats:
        return None
    cbp, cbs, abp, abs_ = _bossinfo_idx()
    segs, hits2012 = [], []
    for field, pid in pats:
        prec = cbp.get(pid)
        plat = 'CACHE'
        if prec is None:
            prec, plat = abp.get(pid), 'APK'
        if prec is None:
            segs.append(f'{field}={pid}（CACHE/APK bosspattern 均未解析到该 pattern 记录）')
            continue
        bs = cbs if plat == 'CACHE' else abs_
        relays = []
        for k, v in sorted(prec.items()):
            if not (_SLOT_RE.match(k) and isinstance(v, int) and v):
                continue
            brec = bs.get(v)
            if brec is None:
                relays.append(f'bossskill|{v}（{plat} 层未解析到记录）')
                continue
            sa, desc, is2012 = _s_ability_desc(brec, plat, data)
            if is2012:
                hits2012.append(f'bossskill|{v}|{plat}（{desc}）')
            relays.append(f'bossskill|{v}|{plat} type{brec.get("skillid0")} {desc}')
        segs.append(f'{field}={pid}（{plat} 层 pattern）→ ' + '；'.join(relays))
    if hits2012:
        reason = ('G3：heroic boss_pattern 链上存在 s_ability→skilllist ability2012 载体（'
                  + '、'.join(hits2012) + '），但本微修（B8-R01）为披露专用路径，不改晋级判定，'
                  '行保持 hint（如需晋级须按 G1–G8 全门控另批重审）')
    else:
        reason = ('G3：heroic boss_pattern 可达，但链上无 type13→s_ability→2012 载体'
                  '（no-2012-chain）：' + '；'.join(segs) + '。B8-R01 披露修正：原「记录无 '
                  'pattern 字段」不实——记录实有 boss_pattern 字段，实际原因＝链上无 '
                  's_ability→skilllist ability2012；本微修仅改披露文本，hint 判定不变')
    return _hint('heroicskilllist', [reason], subject=subject_phrase, attrs=claims)


def _multi_relay_disclosure(table, record_id, layer, pats, carrier, data):
    """B8-R02（披露专用）：denju/dlb 行记录含多条 patternidN 且链上多条 type13→2012 中继
    同指唯一载体时，如实披露「唯一」实为载体唯一（多 pattern/多中继同指），数值不受影响。
    中继按 pattern 原始记录（bossinfo 索引）逐槽清点，非 links 去重后口径。条件按现场数据
    计算（实测全库仅 20510 denju 行满足），不满足返回 None（文案零变化）。"""
    if len(pats) < 2:
        return None
    cbp, cbs, abp, abs_ = _bossinfo_idx()
    relays = []
    for plat, pid in pats:
        bp, bs = (cbp, cbs) if plat == 'CACHE' else (abp, abs_)
        prec = bp.get(pid)
        if prec is None:
            continue
        for k, v in sorted(prec.items()):
            if not (_SLOT_RE.match(k) and isinstance(v, int) and v):
                continue
            brec = bs.get(v)
            if brec is None or brec.get('skillid0') != 13:
                continue
            sa, _, is2012 = _s_ability_desc(brec, plat, data)
            if is2012:
                relays.append(f'{pid}.{k}→bossskill|{v}|{plat}')
    if len(relays) < 2:
        return None
    return (f'多 pattern/多中继披露（B8-R02）：本行记录 {table}|{record_id}|{layer} 含 '
            f'{len(pats)} 条 patternidN（' + '、'.join(str(p) for _, p in pats) + '），链上共 '
            f'{len(relays)} 条 type13→s_ability→2012 中继（' + '、'.join(relays)
            + f'）同指同一载体 skilllist|{carrier["carrier_id"]}|{carrier["layer"]}——'
            '「唯一 type13 中继」在本行按「载体唯一（多 pattern/多中继同指）」理解，'
            f"载体与数值不受影响；本值行取 pattern {carrier['pattern_id']}→"
            f"bossskill|{carrier['relay_id']}|{carrier['relay_layer']}"
            f"(slot {carrier['relay_slot']}) 链")


# ---- 披露文案（固定口径）----
_TRIGGER_NATIVE = ('记录侧触发链＝bhSkillUtil.OnActionSkillAbility() 遍历本次已装入的附加能力数组、'
                   '经 IsEnableSkillAbility 及 2012 跳表进入 SkillAbility_SupportTarget（仅在 '
                   '_isSkillAbilityAction=false 时分派，属技能动作附加能力阶段、非暴击命中触发）；'
                   'SkillAbility_SupportTarget 把 param0 存 v8、param4/5 原样写 '
                   'TimePowerUpData+24/+28，再按目标 setSupport2(time=param0,type=2012)，'
                   '两暴击贡献与时间不乘 Chain；Support2 聚合默认概率增量夹 [0,.5]、暴伤系数增量夹 '
                   '[-1.5,1]（局部贡献非最终暴击率/最终暴伤倍率）——'
                   'output/ordinary_effects/ability2012/README.md 口径')

_P8_DESC = {31: 'TARGET_TYPE.pGROUP_ALL（ability2012 README 口径：31 不是 1017 职业位图；'
               'GROUP_ALL 不等于全部对象必然被选中，实际还受 GetMemberList 列表与 bAll 影响）',
            64: 'TARGET_TYPE.MYSELF'}


def _object_note(subject_phrase, p8_raw):
    p8 = (f'载体 /param8={p8_raw}（{_P8_DESC.get(p8_raw, f"原值 {p8_raw!r}；枚举语义未核")}）'
          if p8_raw is not None else '载体 /param8 缺失（缺失不补 0）')
    return (f'对象披露（双源）：句面依据「{subject_phrase}」逐字在句；记录侧＝{p8}；'
            'param7/8 仅 trigger_context 中标明调用输入/局部上限及剩余边界，尚未作为独立'
            '字段规则推广——仅作相容核对，非对象确认')


def _p0_note(p0_raw):
    if isinstance(p0_raw, (int, float)) and not isinstance(p0_raw, bool) and p0_raw:
        return (f'载体 /param0={p0_raw} 登记（正临时支持计时输入，{p0_raw} 游戏秒，'
                'trigger_context；D1 裁决：时长值行仍归批 6 t13 /skillparam3 口径，'
                '本批不出 p0 值行）；')
    return (f'载体 /param0={p0_raw!r}（缺失/非正值不补数）；')


def _sample_domain_note(rule, param):
    """样本域披露（INFR-02）：skilllist|2012 三条规则 occurrences 已登记（406/308/311）且
    前置审计与 v3 CACHE 实测交叉验证一致→按登记口径披露（比批 6 occ=None 外推强）。"""
    occ = rule.get('occurrences')
    origin = _registered_rule(param).get('origin') or '未登记'
    return (f'该规则登记已核出现 {occ} 次（origin {origin}；样本域＝当前 v3 CACHE 普通 '
            'ability2012 的 406 条记录：param4 存在 308 条全>0、param5 存在 311 条全>0、'
            '缺槽保持缺失不导出 0）；本行来源载体记录未逐条核对，按规则适用条件披露，'
            '不属逐记录确认')


def _slots_note(carrier_rec, claimed):
    """载体槽位登记：本句消费槽＋句外槽原值（不分配给本句，仅登记）。"""
    consumed, idle = [], []
    for key in sorted(carrier_rec):
        if not re.match(r'^(param|iParam|iparam|skillparam|flag|skillflag)\d', key):
            continue
        raw = carrier_rec.get(key)
        entry = f'/{key}={raw!r}'
        if key in claimed:
            consumed.append(entry)
        else:
            idle.append(entry)
    parts = [f'载体槽位登记：本句消费 ' + '、'.join(consumed)]
    if idle:
        parts.append('句外槽未分配（不归属本句，仅登记原值；param0 为支持计时/param7·param8 为 '
                     'trigger_context，其余槽 2012 无已确认规则）：' + '、'.join(idle))
    return '；'.join(parts)


def _hint(table, reasons, subject=None, attrs=(), sent_no=None, sent_total=0, **extra):
    out = dict(kind='hint', reasons=reasons, subject=subject, attrs=list(attrs), table=table,
               sent_no=sent_no, sent_total=sent_total)
    out.update(extra)
    return out


def _promote(frag, table, layer, record_id, cid, attrs, claims, subject_phrase, rate, power,
             via, via_desc, chain_head, carrier, sent_no, sent_total,
             carrier_source_note=None, g3_phrase='唯一 type13 中继'):
    """晋级行：值行全部来自唯一 skilllist 2012 载体（p4+p5），逐行注明来源记录链（scope §4.2）。"""
    crec = carrier['record']
    carrier_id = carrier['carrier_id']
    carrier_layer = carrier['layer']
    pid = carrier['pattern_id']
    carrier_key = f'skilllist|{carrier_id}|{carrier_layer}'
    relay_key = f"bossskill|{carrier['relay_id']}|{carrier['relay_layer']}"
    pattern_key = f'bosspattern|{pid}|{carrier["relay_layer"]}'
    head = f'{chain_head}→' if chain_head else ''
    chain_desc = (f'{head}{pattern_key}→{relay_key}'
                  f"(type13,slot {carrier['relay_slot']})→s_ability→"
                  f'skilllist|{carrier_id}|{carrier_layer}(ability2012)')
    numeric_source = f'模板推断（批 8 暴击 2012 链：{chain_desc}）'
    direction = _sent_direction(frag)
    direction_word = {'up': '上がる/上がり/上げる', 'down': '下がる/下がり'}.get(direction, direction)
    answers = []
    claimed_params = []
    p0_raw = crec.get('param0')
    p8_raw = crec.get('param8')
    for attr, want in (('クリティカル発生率', rate), ('クリティカル威力', power)):
        if not want:
            continue
        param = 'param4' if attr == 'クリティカル発生率' else 'param5'
        claimed_params.append(param)
        raw = crec.get(param)
        rule = R.rule_for('skilllist', 2012, '/' + param)
        converted = R.answer_for('skilllist', 2012, '/' + param, raw, crec)
        evidence_dirs, evidence_files = _field_evidence(param)
        unit_desc = ('单位：百分点（原值×100；对 0 加算增益，非「以 N% 概率施加支持」）'
                     if param == 'param4' else
                     '单位：系数增量（暴伤系数 +原值；不减 1095 的 1.5 基准，非最终伤害相对增加）')
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B8_SCOPE,
            rule_key=f'skilllist|2012|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_id, layer=carrier_layer,
                        record_key=carrier_key),
            note=(f'模板批 8 暴击 2012 链值行（来源载体＝{carrier_key}，ability=2012；链：'
                  f'{chain_desc}）；句中「{attr}」→/{param} 1:1 映射；规则键 '
                  f'skilllist|2012|/{param}；原值 {raw}；{unit_desc}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）；'
                  '本条数值归属＝推断（句→载体为数据侧结构对应，引擎侧 s_ability 装载路径'
                  '无原生核实），不升确认；'
                  f'方向审核：方向一致（原值 {raw}>0，与句「{direction_word}」方向一致）；'
                  f'证据目录 {evidence_dirs[0]} 及 output/ordinary_effects/ability2012/；'
                  f'{_object_note(subject_phrase, p8_raw)}；'
                  f'条件逐字：句面「{frag}」；{_TRIGGER_NATIVE}；'
                  f'{_p0_note(p0_raw)}样本域：{_sample_domain_note(rule, param)}'
                  + (f'；链层披露：中继段 {carrier["relay_layer"]} 层→载体 {carrier_layer} 层'
                     '（跨层链，样本域按载体记录判定）' if carrier['relay_layer'] != carrier_layer else '')
                  + (f'；{carrier_source_note}' if carrier_source_note else '')),
            quantitative=True))

    # --- 晋级行注记（不改变「推断」档位） --------------------------------------------------
    extra = []
    extra.append(_object_note(subject_phrase, p8_raw) + '；' + _TRIGGER_NATIVE)
    if carrier['relay_layer'] != carrier_layer:
        # 跨层链（如 cid20607：pattern/bossskill 段仅 APK 层可见，s_ability 目标由 links
        # 解析到 v3 CACHE skilllist 记录∈406 条样本域）：G5 按载体记录自身所属层判定，
        # 中继段层差异如实登记（与批 6「子记录层照实登记」同口径）。
        extra.append(f'跨层链披露：本链 pattern/bossskill 中继段为 {carrier["relay_layer"]} 层记录'
                     f'（pattern→bossskill 段仅该层可见）；s_ability 目标由 links 解析到 '
                     f'{carrier_layer} 层 skilllist 记录（本载体 ∈ 规则样本域＝当前 v3 CACHE 普通 '
                     'ability2012 的 406 条记录）；G5 样本域门以载体记录自身所属层判定，'
                     '中继段层差异如实登记，不据此扩域或降级')
    extra.append('跨记录归属依据（b8 scope §4.2）：句→2012 载体为数据侧结构对应：' + g3_phrase
                 + '＋s_ability 字段＋句 crit 属性↔载体活性槽形状匹配；引擎侧 s_ability '
                 '装载路径无原生核实，行保持推断——永不据此升「确认」')
    if carrier_source_note:
        extra.append(carrier_source_note)
    if sent_no:
        extra.append(f'多段披露：本记录正文共 {sent_total} 句（以「。」切分），本句位于第 '
                     f'{sent_no} 句；非首段行按唯一载体＋形状匹配化解归属（批 6 §4.1 裁决口径'
                     '沿用），不写「段位↔槽位位置序对应」')
    else:
        extra.append('多段披露：正文句序未能定位（片段不在按「。」切分的句列中）；非首段行按'
                     '唯一载体＋形状匹配化解归属（批 6 §4.1 裁决口径沿用），不写「段位↔槽位'
                     '位置序对应」')
    extra.append('同句非 crit 属性不出本批值行（批 8 只消费 skilllist|2012|/param4|/param5）：'
                 't13 侧攻撃力/防御力/移動速度/一定時間归批 6 口径（既有批 6 hint/值行保留'
                 '原状，不重写批 6 键）')
    extra.append(_slots_note(crec, set(claimed_params)))
    if carrier.get('via') and not carrier['via'].startswith('links'):
        extra.append('载体解析路径：' + carrier['via'])
    claimed_sorted = sorted(set(claimed_params))
    summary = (B8_TAG + '：crit 值行来源＝' + chain_desc + '；值行全部「推断」，不升「确认」，'
               '不进入整行确认。句→载体归属为数据侧结构对应：' + g3_phrase + '＋s_ability '
               '字段＋句 crit 属性↔载体活性槽形状匹配；引擎侧 s_ability 装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露：'
               + '；'.join(_sample_domain_note(R.rule_for('skilllist', 2012, '/' + p), p)
                           for p in claimed_sorted) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject_phrase, attrs=list(claims), claims=dict(claims),
                table=table, pattern_record_id=pid, relay_record_id=carrier['relay_id'],
                relay_type=carrier['relay_type'], relay_slot=carrier['relay_slot'],
                carrier_record_id=carrier_id, carrier_layer=carrier_layer,
                carrier_name=crec.get('name'), via=via, sent_no=sent_no,
                sent_total=sent_total)


def evaluate(record: dict, frag: str, table: str, layer: str | None = None, record_id=None,
             text: str | None = None, data=None, cid=None, boss_skill_refs=None,
             sa_ability_refs=None):
    """对一行做批 8 暴击 2012 链审核，返回 None（不属本批范围）或审核结果 dict。

    table：行记录表（TABLES 五表）；layer/record_id：行记录来源层与 id；text：行记录
    正文字段全文（clean 后）；data/cid：页级 Inputs 与 cid（links refs 与解码索引）；
    boss_skill_refs/sa_ability_refs：行记录（或 charainfo 同文 pattern 记录）的 links
    槽位引用（带完整 raw record）。

    结果 dict：kind='promote'（answers/summary_reason/extra_reasons 等）或 'hint'（reasons）。
    """
    if data is None or cid is None or table not in TABLES or not isinstance(record, dict):
        return None
    if CRIT_TRIGGER not in frag:
        return None
    rate, power = _sent_attrs(frag)
    direction = _sent_direction(frag)
    obj = _sent_object(frag)
    subject_phrase = next((p for p, _ in _OBJECT_PHRASE if p in frag), None)
    claims = {'クリティカル発生率': rate, 'クリティカル威力': power}

    # --- 行→pattern 解析（G2 链可达第一步）------------------------------------------------
    ctx = None
    precord = None
    refs_bsr = boss_skill_refs
    refs_sar = sa_ability_refs
    g1_text = text or ''
    if table == 'bosspattern':
        pid = record.get('patternid')
        if not (isinstance(pid, int) and not isinstance(pid, bool)):
            return _hint(table, [f'G2：行记录无整数 patternid（{pid!r}），pattern 链不可达'],
                         subject=subject_phrase, attrs=claims)
        precord = record
        pats = [(layer, pid)]
    elif table == 'charainfo':
        ctx = B6._page_ctx(data, cid)
        matched = [(e, frags) for e, frags in ctx['pattern_frags'] if frag in frags]
        pat_ids = {(str(e.get('reference_id')), e.get('layer')) for e, _ in matched}
        if not matched:
            # audit 同法：同页无同文 pattern 行时先看 charainfo.s_ability→2012 结构路由
            # （s_ability 在原始 charainfo 记录上；links 条目的 record 为执行副本无该字段，
            # 故从 Inputs 已装载的 cache_chara/apk_chara 原始记录取）
            craw = (data.cache_chara.get(cid) if layer == 'CACHE' else data.apk_chara.get(cid))
            if craw is None:
                craw = data.cache_chara.get(cid, data.apk_chara.get(cid)) or {}
            sa = craw.get('s_ability') if isinstance(craw.get('s_ability'), int) else None
            tr = data.skill(sa) if sa else None
            if tr is not None and (tr['record'] or {}).get('ability') == 2012:
                return _hint(table, ['同页无同文 pattern 行；charainfo.s_ability='
                                     f'{sa}→skilllist 2012（{tr["layer"]} 层，载体 /param4='
                                     f'{tr["record"].get("param4")!r}/'
                                     f'/param5={tr["record"].get("param5")!r}）结构路径存在，但该路由'
                                     '无先例（charainfo-sa-route），不晋级'])
            return _hint(table, ['charainfo 行：同页无同文 bosspattern 行，pattern 链不可达'
                                 '（b6 H5 同法）'], subject=subject_phrase, attrs=claims)
        if len(pat_ids) > 1:
            return _hint(table, [f'charainfo 行：同文对应 {len(pat_ids)} 个 pattern 记录'
                                 f'（{",".join(sorted(p[0] for p in pat_ids))[:60]}），归属歧义'
                                 '（b6 G5 同法）'], subject=subject_phrase, attrs=claims)
        pe = matched[0][0]
        precord = pe.get('record') or {}
        pid = precord.get('patternid')
        if not (isinstance(pid, int) and not isinstance(pid, bool)):
            return _hint(table, [f'charainfo 经同页同文行：pattern 记录无整数 patternid（{pid!r}）'],
                         subject=subject_phrase, attrs=claims)
        pats = [(pe.get('layer'), pid)]
        refs_bsr = pe.get('boss_skill_refs')
        refs_sar = pe.get('sa_ability_refs')
        # G1：charainfo 行按其同文 pattern 记录正文计（b6 G7 同法）
        ptext = str(precord.get('sinfo', '') or '').replace('\\n', '\n')
        g1_text = ptext
    else:  # denju / denju_limit_break_info / heroicskilllist
        prefix = 'pattern' if table == 'heroicskilllist' else 'patternid'
        pfields = _pattern_ids(record, prefix)
        if not pfields and table == 'heroicskilllist':
            # B8-R01 微修（披露专用，不改判定）：heroicskilllist 记录实有 boss_patternN 字段，
            # 原因按实际链解析登记（恒留 hint）。
            heroic = _heroic_chain_hint(record, data, subject_phrase, claims)
            if heroic is not None:
                return heroic
        if not pfields:
            label = {'denju': 'denju 记录无 patternidN 字段',
                     'denju_limit_break_info': 'dlb 块无 patternidN 字段（链断）',
                     'heroicskilllist': 'heroicskilllist 记录无 pattern 字段（raw_keys='
                                        + str(list(record.keys())[:12]) + '）'}.get(table, '无 pattern 字段')
            return _hint(table, ['G2：' + label + '，pattern 链不可达'], subject=subject_phrase,
                         attrs=claims)
        pats = [(layer, v) for _, v in pfields]

    # --- G1 句归属：行 japanese 是父记录正文恰 1 次子串 ------------------------------------
    same_count = g1_text.count(frag.strip())
    if same_count != 1:
        return _hint(table, [f'G1：行句在父记录正文出现 {same_count} 次（须恰 1 次）；'
                             '同文多次/未定位一律留 hint'], subject=subject_phrase, attrs=claims)

    # --- G2/G3：逐 pattern 链解析→载体唯一 -------------------------------------------------
    carriers, relay_non13, gaps = [], [], []
    for plat, pid in pats:
        c1, r1, g1 = _pattern_carriers(pid, precord, refs_bsr, refs_sar, data)
        for x in c1 + r1:
            x['pattern_id'] = pid
        carriers.extend(c1)
        relay_non13.extend(r1)
        gaps.extend(g1)
    carriers_u = list({(c['carrier_id'], c['layer']): c for c in carriers}.values())
    if not carriers_u:
        if relay_non13:
            return _hint(table, ['G3：链上有 s_ability→2012 但中继 bossskill 非 type13（类型 '
                                 + ','.join(str(x['relay_type']) for x in relay_non13)
                                 + '）：行→记录的句子归属模型以 cid349 先例的 t13 形状为准，'
                                 '非 t13 中继的语义耦合无先例，不猜（relay-non13）'],
                         subject=subject_phrase, attrs=claims)
        return _hint(table, ['G3：pattern 链上无 type13→s_ability→2012 载体（no-2012-chain）'
                             + ('；链缺口：' + '；'.join(dict.fromkeys(gaps)) if gaps else '')],
                     subject=subject_phrase, attrs=claims)
    if gaps:
        return _hint(table, ['G2：pattern 链完整性缺口（存在未唯一对位的 bossskill 槽位，'
                             '无法排除其亦指向 2012 载体）：' + '；'.join(dict.fromkeys(gaps))],
                     subject=subject_phrase, attrs=claims)
    if len(carriers_u) > 1:
        det = '；'.join(f"skilllist|{c['carrier_id']}|{c['layer']}"
                        f"(relay {c['relay_id']},p4={c['record'].get('param4')!r})"
                        for c in carriers_u)
        return _hint(table, [f'G3：{len(carriers_u)} 个 t13→2012 载体（归属歧义，multi-carrier）：'
                             + det], subject=subject_phrase, attrs=claims)
    carrier = carriers_u[0]
    crec = carrier['record']

    # --- G5 样本域：载体层==CACHE 且 id ∈ 406 条 v3 规则样本域 ------------------------------
    if carrier['layer'] != 'CACHE' or carrier['carrier_id'] not in _r2012_domain(data):
        return _hint(table, [f'G5：载体 skilllist|{carrier["carrier_id"]}|{carrier["layer"]} 在 '
                             '规则样本域（conditions：仅当前 v3 CACHE 普通 ability2012 的 406 条'
                             '记录）之外；APK 层 2012 记录 211 条值形同构但含 CACHE 域外值'
                             '（如 float32 值/0.0 槽），扩域需独立原生核实，不静默扩域'
                             '（carrier-out-of-domain）'], subject=subject_phrase, attrs=claims)

    # --- G4 属性形状：句 crit 属性⇔载体活性 crit 槽（双向，防跨段误配）-----------------------
    def _active(key):
        raw = crec.get(key)
        return raw is not None and raw != 0

    mism = []
    if rate and not _active('param4'):
        mism.append(f'句含クリティカル発生率但载体 /param4 不活性({crec.get("param4")!r})')
    if power and not _active('param5'):
        mism.append(f'句含クリティカル威力但载体 /param5 不活性({crec.get("param5")!r})')
    if (not rate) and _active('param4'):
        mism.append(f'载体 /param4 活性({crec.get("param4")!r})但句无クリティカル発生率')
    if (not power) and _active('param5'):
        mism.append(f'载体 /param5 活性({crec.get("param5")!r})但句无クリティカル威力')
    if mism:
        # B8-I02 微修（披露专用）：形状不符留 hint 的行，若载体 /param8 与句面对象同时
        # 不相容（味方全体×64／自身×31），一并披露（G4 已足以留 hint，判定不变）。
        p8v = crec.get('param8')
        g6extra = ''
        if (obj, p8v) in (('ally_all', 64), ('self', 31)):
            g6extra = (f'；另披露（G6 相容核对，B8-I02）：载体 /param8={p8v}（{_P8_DESC[p8v]}）'
                       f'与句面对象「{subject_phrase}」不符——G4 形状不符已足以留 hint，'
                       '此处一并登记对象不符，判定不变')
        return _hint(table, ['G4：形状不符：' + '；'.join(mism) + '（缺槽＝缺失不补 0，'
                             'rules limits 口径）' + g6extra], subject=subject_phrase, attrs=claims)

    # --- G6 对象相容（p8 仅 trigger_context 相容核对；scope §4.1 三分支）---------------------
    p8 = crec.get('param8')
    if obj == 'ally_all' and p8 == 64:
        return _hint(table, [f'G6：句面对象＝味方全体 vs 载体 /param8=64（MYSELF）不符'],
                     subject=subject_phrase, attrs=claims)
    if obj == 'self' and p8 == 31:
        return _hint(table, [f'G6：句面对象＝自身 vs 载体 /param8=31（pGROUP_ALL）不符'],
                     subject=subject_phrase, attrs=claims)
    if obj == '?':
        return _hint(table, ['G6：句无对象词（味方全体/全ての味方/自身/味方），无法与载体 /param8 '
                             '交叉核对（object-unstated）'], subject=subject_phrase, attrs=claims)

    # --- G7 方向 ----------------------------------------------------------------------------
    if direction == 'down':
        return _hint(table, ['G7：句向「下がる/下がり」与 p4/p5 正值加算增益方向冲突'
                             '（direction-mismatch）'], subject=subject_phrase, attrs=claims)
    if direction == '?':
        return _hint(table, ['G7：句无上下方向词（direction-unstated）'],
                     subject=subject_phrase, attrs=claims)

    # --- G8 跨 cid 同载体守卫（进程内登记；审计全库交叉检查实测 0 例）-------------------------
    claim_key = (carrier['carrier_id'], carrier['layer'])
    others = _CLAIMS.get(claim_key, set()) - {cid}
    if others:
        return _hint(table, [f'G8：跨 cid 载体竞争：载体 {claim_key} 已被 cid '
                             f'{",".join(map(str, sorted(others)))} 的行主张（进程内登记；'
                             '审计全库交叉检查实测 0 例，本守卫为防御性保留）'],
                     subject=subject_phrase, attrs=claims)
    _CLAIMS.setdefault(claim_key, set()).add(cid)

    # --- 句序披露 -----------------------------------------------------------------------------
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    _sents = [s for s in re.findall(r'[^。]*。', wb)]
    sent_no = next((i + 1 for i, s in enumerate(_sents) if frag.strip() in s), None)
    sent_total = len(_sents)

    via = 'charainfo_via_pattern' if table == 'charainfo' else 'own'
    # B8-R02 微修（披露专用）：denju/dlb 多 pattern 行且链上多条 type13→2012 中继同指
    # 唯一载体时，披露「唯一」实为载体唯一（实测全库仅 20510 denju 行满足；判定/数值不变）。
    multi_note = None
    g3_phrase = '唯一 type13 中继'
    if precord is None and len(pats) > 1:
        multi_note = _multi_relay_disclosure(table, record_id, layer, pats, carrier, data)
        if multi_note:
            g3_phrase = '载体唯一（多 pattern/多条 type13 中继同指）'
    chain_head = (f'charainfo|{record_id}|{layer}→同页同文 ' if table == 'charainfo'
                  else '' if table == 'bosspattern' else f'{table}|{record_id}|{layer}')
    via_desc = ('经同页同文 bosspattern 记录（charainfo 行自身 skillparam* 不消费）'
                if table == 'charainfo' else '行记录自身链')
    return _promote(frag, table, layer, record_id, cid,
                    [a for a, w in (('クリティカル発生率', rate), ('クリティカル威力', power)) if w],
                    claims, subject_phrase, rate, power, via, via_desc,
                    chain_head, carrier, sent_no, sent_total,
                    carrier_source_note=multi_note, g3_phrase=g3_phrase)
