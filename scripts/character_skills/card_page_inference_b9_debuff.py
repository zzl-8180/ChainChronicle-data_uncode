"""模板作用域推断层——批 9：敵デバフ（Top20 #6 家族；skilllist ability99 PowerDrain 载体）。

设计与范围依据：``output/character_skills/inference_inventory/b9_debuff_scope.md``
（批 9 前置审计；逐行明细 work/character_skills_b9_debuff/debuff_rows_classified.json、
promotable99.json）。广筛行集（C 行，敵＋攻/防/移＋下がる/下げる、排除「敵から受ける…下げ」
我方被击句）＝**全库 973 行/451 cid（Y.G. 208/77）**；逐行分类 9 类，实测可晋级候选
**全库 35 行/35 cid（Y.G. 11）**，全部为 skilllist（能力容器）行、attack_hit 触发、
own sub_effect 链上唯一 ability99（SA_PowerDrain）载体（CACHE 层 133 条样本域内），
估值 ≈138 值行（每行 攻/防/移各 1＋时长 1）；其余 938 行按逐行原因留 hint。

关键结论（scope §1）：敌方减益的已确认规则**只有 skilllist|99（PowerDrain）一族 4 条**
（/param0 时长（occ 133）//param7 受击目标攻击倍率加算（126）//param8 移速因子加算
（**1 条**，已核 ID 仅 43023616）//param9 受伤量倍率加算（123）——p9 正值＝「防御力
下がる」的表现层口径，**不是固定防御减少**）；bossskill 140 条中无任何敌方减益规则；
et13 换算器硬编码「+」方向（rules.py:1349-1365）。载体 2003（SA_PowerDrain，265+148 条）
形状与 99 同构（431 行 6 种属性组合全自洽，p7≤0/p8≤0/p9≥0）但**域外无规则、无证据目录**
→一律留 hint（no-rule-2003），扩域需 ability2003 原生专项。

精确范围（scope §5.1，门 P1–P6＋B1 防线全部通过才晋级；任一不过→留 hint 并登记原因）：

* **P1 句面**：行 japanese 含「敵」＋下降谓词（下がる/下がり/下げる/下げ）＋攻/防/移
  属性名；「敵から受ける…下げ」我方被击减伤句一律不在本批（返回 None）；
  **B1 逐字对象门**：敌方减益半句＝首个下降谓词所在句段（前界「。」/「、」），该句段必须
  同时含「敵」与 ≥1 个属性名——「味方/自身…」主语的下降半句不得挂敌方减益值
  （30338 假阳性防线的镜像门：我方增益句同样不得挂敌方减益值）；
* **P2 表与链**：行记录=skilllist（能力容器）/supporterskill；own sub_effect 链（行记录
  自身 sub 字段经 profiles 装配、link_kind='sub_effect' 的单层子记录）恰可达 skilllist
  ability=99 记录；**载体层==CACHE 且 id∈当前 v3 CACHE 普通 ability99 的 133 条样本域**
  （APK 99×199 条载体经批 13 扩域——rules.json 四键两域分源＋occurrences_apk——委托
  card_page_inference_b13_apkext.handle_99_apk 按载体层域接管：晋级键 inference_b13 或
  hint；扩域前的域外 hint 口径仅对批 13 之前有效）；
* **P3 载体唯一**：恰 1 个 99 载体（0→hint:no-99-carrier；≥2→hint:multi-carrier）；
* **P4 形状（双向）**：句 敵減益半句 攻撃力⇔/param7 活性、移動速度⇔/param8 活性、
  防御力⇔/param9 活性；载体活性 p7/p8/p9 槽不得超出句面主张（缺槽=缺失不补 0）；
  p1–p6 槽无规则，句外槽仅登记原值不分配（13 行 60 秒档 p4/p5/p6 活性照实披露；
  复合句「自身の…上がる」半句不属本批（fam11/自身バフ侧），登记不分配）；
* **P4b 竞争句（批 6 G6 检测扩展）**：行记录正文内其它含「敵＋下降谓词＋本句同属性」的
  下降句（本句除外）存在→归属歧义 hint（实测 35 行 0 例；20261022 B13-R01 修复：
  frag/候选句同一 NFKC 规范化管线＋属性词边界感知（属性防御力≠防御力），伪竞争只减不增）；
* **P5 方向（代码语义）**：p7/p8 活性值≤0（负值加算=下降；**加算池 Σ 汇总后 clamp，
  非乘数<1、非独立 debuff 槽**）；p9 活性值≥0（受伤量倍率加算=「防御力下がる」的表现
  层，按规则 conversion 原口径，不改写成固定防御减量）；p0>0=时长值行（游戏秒）、
  -1=无正计时标记（登记口径，不出时长值行）；冲突→hint:direction-mismatch；
* **P6 跨 cid 载体竞争守卫**（批 8 G8 同法；审计实测 0 例，进程内登记）；
* **B1 防线（逐行强制）**：99 载体主张**只对 skilllist 容器行自身 sub_effect 链有效**；
  pattern/denju/charainfo 行的 sub_effect children 含 profiles 装配的 ID 碰撞伪影
  （profiles.py:426-428 subs_by_parent 按 record_id 跨表匹配）——pattern 行一律不经
  sub_effect 消费；et13 我方增益输入候选（keyword 级）一律拒绝。

映射与值行（scope §5.1/§5.2；值行 rule_key 只允许 ``skilllist|99|/param0|/param7|/param8|/param9``）：

================  ========  ========================================================
句中成分          规则键     值行数量类型（rules.py 换算器，方向按符号）
================  ========  ========================================================
攻撃力（敵減益）  /param7   受击目标攻击倍率加算贡献；负值→因子下降（0.7 等）
移動速度（敵減益）/param8   移速因子加算增量；负值→×0.7 等（occ=1 逐行披露）
防御力（敵減益）  /param9   受伤量倍率加算贡献；正值→受伤量因子 1.3 等
一定時間          /param0   支持计时输入（游戏秒）；-1=无正计时标记不出值行
================  ========  ========================================================

硬边界（scope §5.2，逐行强制）：

* **只升「推断」，绝不升「确认」**：值行 numeric_evidence/association_evidence 一律
  「推断」；行级标注「推断（模板批 9 敵デバフ）」、evidence_scope=
  TEMPLATE_BATCH9_DEBUFF（行级 metadata 键 ``inference_b9``，与 pilot/b3–b8 并列）；
  不进整行确认统计；「唯一 sub99 载体＋形状匹配」是数据侧结构对应，永不升「确认」。
* **规则本体与本条归属分开披露**：值行 note 固定写明「规则本体：已确认（静态及受控原生
  局部规则）——指规则本身；本条数值归属＝推断（模板批 9），不升确认」。
* **证据按字段**（INFR-01）：值行 evidence 取 rules.json skilllist|99|/paramN 的
  evidence——timed_support/＋ordinary_effects/ability99/（p0/p7/p9）、movement/
  （p8）；存在性检查，缺失显式失败（不产出死指针）。
* **样本域披露按登记口径**（INFR-02）：occurrences 133/126/1/123 已登记；p8 已核样本域
  仅 43023616 单条，外推逐行披露；本行来源载体记录未逐条核对，不属逐记录确认。
* **条件/对象逐字披露**：句面条件文本（攻撃時/一定確率で/与えたダメージ量に応じて 等）
  全句逐字入 note；对象=「敵」逐字（攻撃した敵/範囲内の全ての敵 等原样引用）＋记录侧
  setSupport2 受击目标路径（timed_support/drain_enemy_mapping.txt：get_param7/8/9→
  setSupport2）。
* **不跨记录合并**：载体句外槽（param1–param6 等）只登记原值不分配；普通 1110→1095
  自身增益段、共鳴、暴击段均不在本批（各自归批 5/7/8 口径）。
* **既有行不动**：A 行含敵デバフ句不动（``not answers`` 守卫）；批 1–8 晋级键与 hint 键
  不重写；30236 基线不动。
"""
from __future__ import annotations

import json
import re
import unicodedata

import rules as R
import card_page_inference_b6_bossbuff as B6
import card_page_inference_b8_crit2012 as B8

B9_TAG = '推断（模板批 9 敵デバフ）'
B9_SCOPE = 'TEMPLATE_BATCH9_DEBUFF'
B9_FAMILY = ('敵デバフ家族（「攻撃した敵の⟨ATTR⟩が（一定時間）下がる。」及同形变体；'
             'skilllist/supporterskill 容器行 own sub_effect 链→skilllist ability99 '
             'PowerDrain 载体）')

# P2：行记录表。skilllist/supporterskill 可晋级；bosspattern/denju/dlb/charainfo/heroic
# 只做逐行 hint 登记（B1 防线：99 载体主张只对 skilllist 容器行自身 sub_effect 链有效）。
TABLES = ('skilllist', 'supporterskill', 'bosspattern', 'charainfo', 'denju',
          'denju_limit_break_info', 'heroicskilllist')

PROMOTABLE_TABLES = ('skilllist', 'supporterskill')

ATTRS3 = ('攻撃力', '防御力', '移動速度')
SLOT_OF = {'攻撃力': 'param7', '移動速度': 'param8', '防御力': 'param9'}
DOWN_WORDS = ('下がる', '下がり', '下げる', '下げ')

# ---- INFR-01：rules.json skilllist|99|/paramN 的 evidence 相对路径解析 ----
# p0/p7/p9 → timed_support/＋ordinary_effects/ability99/（p0 另有 difference_sources/＋movement/
# 采用政策条目）；p8 → movement/。所有文件必须落在允许前缀集合内，缺失显式失败。
_CARD_COMPARISON_ROOT = 'output/card_comparison_cid30236/'
_EVIDENCE_EXPECTED = {'param0': (_CARD_COMPARISON_ROOT + 'timed_support/',
                                 'output/ordinary_effects/ability99/',
                                 _CARD_COMPARISON_ROOT + 'difference_sources/',
                                 _CARD_COMPARISON_ROOT + 'movement/'),
                      'param7': (_CARD_COMPARISON_ROOT + 'timed_support/',
                                 'output/ordinary_effects/ability99/'),
                      'param9': (_CARD_COMPARISON_ROOT + 'timed_support/',
                                 'output/ordinary_effects/ability99/'),
                      'param8': (_CARD_COMPARISON_ROOT + 'movement/',)}
_EVIDENCE_CACHE = {}

_REGISTERED_RULES = None


def _registered_rule(param):
    """profiles/rules.json 登记的规则条目（origin 权威来源；B8._registered_rule 同法）。"""
    global _REGISTERED_RULES
    if _REGISTERED_RULES is None:
        p = B8.Path('output/character_skills/profiles/rules.json')
        _REGISTERED_RULES = json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}
    return _REGISTERED_RULES.get(f'skilllist|99|/{param}') or {}


def _field_evidence(param):
    """按字段解析 rules.json skilllist|99|/paramN 的 evidence 并做存在性检查（INFR-01）。"""
    if param in _EVIDENCE_CACHE:
        return _EVIDENCE_CACHE[param]
    rule = R.rule_for('skilllist', 99, '/' + param)
    files = []
    for entry in (rule or {}).get('evidence') or []:
        items = entry if isinstance(entry, (list, tuple)) else [entry]
        for e in items:
            e = str(e)
            files.append('output/' + e[3:] if e.startswith('../') else _CARD_COMPARISON_ROOT + e)
    dirs = _EVIDENCE_EXPECTED[param]
    if not files or any(not any(p.startswith(d) for d in dirs) for p in files):
        raise ValueError(f'批 9 证据解析异常（INFR-01）：skilllist|99|/{param} 的 rules.json '
                         f'evidence 未解析为 {dirs} 下的文件，实际 {files!r}')
    missing = [p for p in files if not B8.Path(p).is_file()]
    if missing:
        raise FileNotFoundError(f'批 9 证据文件缺失（INFR-01）：{missing}')
    _EVIDENCE_CACHE[param] = (dirs, files)
    return _EVIDENCE_CACHE[param]


# ---- P2 样本域：当前 v3 CACHE 普通 ability99 的 133 条记录（decoded skilllist 实测）----
def _domain99(data):
    return {sid for sid, (i, rec) in data.cache_skill.items() if (rec or {}).get('ability') == 99}


# ---- 链索引（批 9 审计 audit_promotable.py 同法：data.old＝profiles/records.jsonl，----
# ---- 按 (table, record_id, layer) 建 children 索引；不重读解码 JSON、不改 profiles）----
_IDX_CACHE = {}


def _chain_index(data):
    key = id(data)
    hit = _IDX_CACHE.get(key)
    if hit is not None:
        return hit[1]
    pc = {}
    for o in data.old.values():
        pc[(o.get('table'), str(o.get('record_id')), o.get('layer'))] = list(o.get('children') or [])
    _IDX_CACHE[key] = (data, pc)  # 连同 data 持强引用，避免 id 复用串页
    return pc


def _ability_by_id(data, sid):
    """审计同法：先 CACHE 解码索引按 id 取；CACHE 无该 id 才看 APK（99 域外载体）。"""
    w = data.cache_skill.get(sid)
    if w is not None:
        return 'CACHE', (w[1] or {})
    w2 = data.apk_skill.get(sid)
    if w2 is not None:
        return 'APK', (w2[1] or {})
    return None, None


# ---- P1：敵減益半句（首个下降谓词所在句段；B1 逐字对象门）----
def _debuff_clause(j):
    """返回 (clause, attrs, subject_phrase)。clause=从「。」/「、」后到首个下降谓词（含）；
    attrs=句段内的攻/防/移属性；subject=句段内「敵」为止的逐字短语（如「攻撃した敵」）。
    B13-R01b-residual 修复（20261022 批 14 重建）：frag 侧属性提取与候选句侧
    _sentence_attrs 应用同一 ``(?<!属性)`` 负向断言（此前本函数仍用裸子串——「属性防御力」
    会在 frag 侧构成「防御力」主张，与候选句侧边界感知不对称）。负向断言只收窄属性集：
    only-shrink（全语料回归增大 0、已晋级行 0 翻转，见 work/character_skills_b14_impl/）。"""
    hits = [(j.find(w), w) for w in DOWN_WORDS if j.find(w) >= 0]
    if not hits:
        return None, [], None
    pos, word = min(hits, key=lambda x: x[0])
    start = max(j.rfind('。', 0, pos), j.rfind('、', 0, pos)) + 1
    clause = j[start:pos + len(word)]
    attrs = _sentence_attrs(clause)
    m = re.search(r'[^。、]*敵', clause)
    subject = m.group(0) if m else None
    return clause, attrs, subject


def _sent_attrs_all(j):
    return [a for a in ATTRS3 if a in j]


def _active(v):
    return v is not None and v != 0


def _is_debuff_sentence(s):
    return ('敵' in s and any(w in s for w in DOWN_WORDS)
            and _sentence_attrs(s) and '敵から受ける' not in s)


def _norm_text(t):
    """B13-R01a 修复（20261022 DeepSeek 定向审查）：fragment 侧与候选侧使用完全相同的
    规范化管线（NFKC＋strip）。此前只对候选句做 NFKC、未规范化 frag——全角「！」在
    NFKC 后变半宽，使「frag.strip() in NFKC(s)」对自身句为 False、自身句排除失败被
    当竞争句（13029 确认误判根因）。规范化在两侧对称后，包含判定只可能多排除、
    不可能新增竞争句（过匹配修正只减不增）。"""
    return unicodedata.normalize('NFKC', t or '').strip()


def _sentence_attrs(s):
    """B13-R01b 修复（20261022 DeepSeek 定向审查）：属性词边界感知——「属性防御力」等
    「属性」前缀复合词不构成攻/防/移主张（元素防御≠本批通用防御力；「属性攻撃力」
    等其它属性 taxonomy 复合词同理排除，语料实测当前仅「属性防御力」出现：
    CACHE 2 条/APK 13 条）。负向断言只收窄候选句属性集，不可能新增竞争句。"""
    return [a for a in ATTRS3 if re.search(r'(?<!属性)' + re.escape(a), s)]


def _competing_debuff_sentences(text, frag, attrs):
    """P4b（批 6 G6 竞争句检测扩展）：行记录正文内其它「敵＋下降谓词＋本句属性」下降句。
    返回去重后的竞争句原文列表（含句号）。

    B13-R01 修复（20261022）：①frag 与候选句经同一 _norm_text 管线后再做自身句排除
    （R01a）；②候选句属性集按 _sentence_attrs 边界感知提取、与 frag 侧主张属性集求交
    才算竞争（R01b——「属性防御力」句不再冒充「防御力」竞争句，2290 误判根因）。
    门的语义不变：竞争＝候选句与敵減益半句主张相同属性（交集非空）；两处修复均只会
    减少伪竞争、不得新增任何竞争判定（已晋级行不受影响，重建实测 0 翻转）。"""
    want = set(attrs)
    frag_n = _norm_text(frag)
    out = []
    for s in re.findall(r'[^。]*。', (text or '').replace('\\n', '\n')):
        s_n = _norm_text(s)
        if frag_n and frag_n in s_n:
            continue
        if not _is_debuff_sentence(s_n):
            continue
        if want & set(_sentence_attrs(s_n)):
            out.append(s)
    return list(dict.fromkeys(out))


def _sample_domain_note(rule, param, occ_extra=''):
    occ = rule.get('occurrences')
    origin = _registered_rule(param).get('origin') or '未登记'
    occ_apk = rule.get('occurrences_apk')
    return (f'该规则登记已核出现 {occ} 次（CACHE 存在数口径，批 13 未改）'
            + (f'＋occurrences_apk={occ_apk}（APK 存在数）' if occ_apk is not None else '')
            + f'（origin {origin}；样本域＝批 13 扩域后两域分源：①当前 v3 CACHE 普通 '
            f'ability99 的 133 条记录；②APK 主表 output/base_master/_mdSkill.json '
            f'ability99 的 199 条记录——命名空间不合并、5 个同号记录中 3 组为两域真实'
            f'参数值分歧、2 组仅缺省/float32 表示差（逐组明细见 rules.json 九键 '
            f'conditions；行侧载体按载体所在层取值不得跨层{occ_extra}）；本行来源载体记录未逐条核对，'
            '按规则适用条件披露，不属逐记录确认')


def _slots_note(crec, claimed_slots):
    """载体槽位登记：本句消费槽＋句外槽原值（不分配给本句，仅登记；scope §5.1 P4）。"""
    consumed, idle = [], []
    for key in sorted(crec):
        if not re.match(r'^(param|iParam|iparam|skillparam|flag|skillflag)\d', key):
            continue
        raw = crec.get(key)
        entry = f'/{key}={raw!r}'
        (consumed if key in claimed_slots else idle).append(entry)
    parts = ['载体槽位登记：本句消费 ' + '、'.join(consumed)]
    if idle:
        parts.append('句外槽未分配（不归属本句，仅登记原值；param0 为支持计时（本句时长值行'
                     '消费时另行列示），ability99 无 param1–param6 换算规则；60 秒档变体'
                     'p4/p5/p6 活性照实披露不分配）：' + '、'.join(idle))
    return '；'.join(parts)


def _direction_note(param, raw):
    """P5 方向审核（代码语义；scope §5.3 负值/独立槽口径）。"""
    if param in ('param7', 'param8'):
        label = '攻撃力' if param == 'param7' else '移動速度'
        return (f'方向一致（原值 {raw}<0：负值加算＝{label}下降贡献——直接写目标 _attack/_move、'
                'Σ 汇总后 clamp(1+Σ)；加算池与增益同池，非乘数<1、非独立 debuff 槽；与句'
                '「下がる/下げる」方向一致）' if raw < 0 else
                f'方向冲突（原值 {raw}>0 与 {label}下降冲突——加算正值为上升贡献）')
    if param == 'param9':
        return (f'方向一致（原值 {raw}>0：受伤量倍率加算＝受击目标受伤量因子上升——正文写作'
                '「防御力下がる」的表现层口径（规则 conversion 原口径，不是固定防御减少）；'
                '加算池与增益同池，非独立负向槽）' if raw > 0 else
                f'方向冲突（原值 {raw}<0 与受伤量加算口径（防御下降的表现层）冲突）')
    return f'方向登记（原值 {raw!r}）'


def _p0_note(p0_raw, with_row):
    if isinstance(p0_raw, (int, float)) and not isinstance(p0_raw, bool) and p0_raw > 0:
        if with_row:
            return (f'载体 /param0={p0_raw}（支持计时输入，{p0_raw} 游戏秒，游戏 delta 扣减、'
                    '不乘 Chain；两次支持提交共用计时；本行已出时长值行）；')
        return (f'载体 /param0={p0_raw}（支持计时输入，{p0_raw} 游戏秒——登记口径；'
                '句面无「一定時間」时长主张，不出时长值行）；')
    if p0_raw == -1:
        return ('载体 /param0=-1（无正计时标记（登记口径），实际持续语义未核——'
                '不出时长值行）；')
    return f'载体 /param0={p0_raw!r}（缺失/非正值不补数，不出时长值行）；'


# ---- 披露口径（固定文案）----
_NATIVE_TARGET = ('记录侧＝setSupport2 受击目标路径（timed_support/drain_enemy_mapping.txt：'
                  'get_param7/8/9 → setSupport2，param7/9 写本次受击目标 _attack/_defense、'
                  'param8 写 _move；param0 为攻击者与目标两次提交共用的计时输入）——'
                  'output/ordinary_effects/ability99/ 口径')

_B1_DISCLOSURE = ('B1 防线披露（30338 假阳性）：本批 99 载体主张只对 skilllist 容器行自身 '
                  'sub_effect 链有效；pattern/denju/charainfo 行的 sub_effect children 含 '
                  'profiles 装配的 ID 碰撞伪影（profiles.py:426-428 按 record_id 跨表挂子），'
                  'pattern 行不经 sub_effect 消费；et13 我方增益输入候选（换算器硬编码「+」方向，'
                  'rules.py:1349-1365）一律拒绝')


def _hint(table, reasons, subject=None, attrs=(), sent_no=None, sent_total=0, **extra):
    out = dict(kind='hint', reasons=reasons, subject=subject, attrs=list(attrs), table=table,
               sent_no=sent_no, sent_total=sent_total)
    out.update(extra)
    return out


def _promote(frag, table, layer, record_id, cid, attrs, claims, subject_phrase, clause,
             carrier, sent_no, sent_total, competitors):
    """晋级行：值行全部来自唯一 skilllist 99 载体（p7/p8/p9＋p0），逐行注明来源链（scope §5.2）。"""
    carrier_id, crec = carrier
    carrier_key = f'skilllist|{carrier_id}|CACHE'
    row_key = f'{table}|{record_id}|{layer}'
    chain_desc = (f'{row_key} own sub_effect→{carrier_key}(ability99,SA_PowerDrain'
                  f'"{(crec.get("name") or "")[:20]}")')
    numeric_source = f'模板推断（批 9 敵デバフ：{chain_desc}）'
    answers = []
    claimed_slots = []
    p0_raw = crec.get('param0')
    p0_row_due = bool('一定時間' in frag and isinstance(p0_raw, (int, float))
                      and not isinstance(p0_raw, bool) and p0_raw > 0)
    for attr in ATTRS3:
        if attr not in attrs:
            continue
        param = SLOT_OF[attr]
        claimed_slots.append(param)
        raw = crec.get(param)
        rule = R.rule_for('skilllist', 99, '/' + param)
        converted = R.answer_for('skilllist', 99, '/' + param, raw, crec)
        evidence_dirs, evidence_files = _field_evidence(param)
        if param == 'param7':
            unit_desc = ('单位：攻击倍率加算增量（显示百分点；负值＝加算下降贡献，非乘数）')
        elif param == 'param8':
            unit_desc = ('单位：速度因子加算增量（负值＝加算下降贡献）；p8 已核样本域仅 1 条'
                         '（43023616，movement 证据）——本行载体为规则适用域内外推，逐行披露')
        else:
            # B9-R01 修复（20261021 定向审查）：括注百分比与主值同一口径——:g 格式化
            # （0.175→17.5%，不再经 int(round(·)) 银行家舍入写成 18%）。
            unit_desc = ('受伤量倍率 +{}（受伤量因子 {}；不是固定防御减少 {}%）——正文写作「防御」'
                         '的表现层口径'.format(raw, 1 + raw, f'{raw * 100:g}'))
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B9_SCOPE,
            rule_key=f'skilllist|99|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_id, layer='CACHE',
                        record_key=carrier_key),
            note=(f'模板批 9 敵デバフ值行（来源载体＝{carrier_key}，ability=99；链：{chain_desc}）；'
                  f'句中敵減益半句「{clause}」的「{attr}」→/{param} 1:1 映射；规则键 '
                  f'skilllist|99|/{param}；原值 {raw}；{unit_desc}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）；'
                  '本条数值归属＝推断（模板批 9：唯一 sub99 载体＋句面形状匹配为数据侧结构对应，'
                  '引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'方向审核：{_direction_note(param, raw)}；'
                  f'证据目录 {evidence_dirs[0]} 及 output/ordinary_effects/ability99/；'
                  f'对象披露（双源）：句面依据「{subject_phrase}」逐字在句（对象=敌方，逐字）；'
                  f'{_NATIVE_TARGET}；'
                  f'条件逐字：句面「{frag}」；'
                  f'{_p0_note(p0_raw, with_row=p0_row_due)}'
                  f'样本域：{_sample_domain_note(rule, param)}'),
            quantitative=True))
    # 时长值行（一定時間→/param0；p0>0 才出值行，-1/缺失按登记口径）
    if p0_row_due:
        param = 'param0'
        claimed_slots.append(param)
        rule = R.rule_for('skilllist', 99, '/' + param)
        converted = R.answer_for('skilllist', 99, '/' + param, p0_raw, crec)
        evidence_dirs, evidence_files = _field_evidence(param)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=p0_raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B9_SCOPE,
            rule_key='skilllist|99|/param0',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_id, layer='CACHE',
                        record_key=carrier_key),
            note=(f'模板批 9 敵デバフ时长值行（来源载体＝{carrier_key}，ability=99；链：'
                  f'{chain_desc}）；句中「一定時間」→/param0 1:1 映射；规则键 '
                  f'skilllist|99|/param0；原值 {p0_raw}；单位：游戏秒（支持计时输入，'
                  '游戏 delta 扣减、不乘 Chain）；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）；'
                  '本条数值归属＝推断（模板批 9：唯一 sub99 载体＋句面形状匹配为数据侧结构对应，'
                  '引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'证据目录 {evidence_dirs[0]} 及 output/ordinary_effects/ability99/；'
                  f'条件逐字：句面「{frag}」；'
                  f'样本域：{_sample_domain_note(rule, param)}'),
            quantitative=True))

    # --- 晋级行注记（不改变「推断」档位） --------------------------------------------------
    extra = []
    extra.append(_NATIVE_TARGET)
    extra.append('跨记录归属依据（b9 scope §5.1）：句→99 载体为数据侧结构对应：唯一 sub99 载体'
                 '（P2/P3：own sub_effect 链恰 1 个 CACHE 层 ability99 记录∈133 条样本域）＋'
                 '敵減益半句属性↔载体活性槽形状匹配（P4 双向）＋方向按符号（P5：p7/p8≤0 加算'
                 '下降、p9≥0 受伤量加算）；引擎侧行→载体装载路径无原生核实，行保持推断——'
                 '永不据此升「确认」')
    extra.append(_B1_DISCLOSURE)
    if competitors:
        extra.append('P4b 竞争句披露（不阻塞）：本记录正文内另有敵下降句（'
                     + '、'.join(c.strip()[:40] for c in competitors) + '）；本句按唯一载体＋'
                     '敵減益半句形状匹配化解归属（批 6 §4.1 裁决口径沿用）')
    extra.append('复合句披露：'
                 + ('本句另含非本批半句（「自身/味方…」侧、或回復等），其数值不属批 9（fam11/'
                    '自身バフ等侧另行处理），登记不分配；载体句外槽（含 60 秒档 p4/p5/p6）'
                    '无 99 规则，仅登记原值不分配' if re.search(r'自身|味方', frag)
                    else '本句为单一敵減益句；载体句外槽（param1–param6 等）无 99 规则，'
                         '仅登记原值不分配'))
    extra.append(_slots_note(crec, set(claimed_slots)))
    claimed_sorted = sorted(set(claimed_slots))
    summary = (B9_TAG + '：敵デバフ值行来源＝' + chain_desc + '；值行全部「推断」，不升「确认」，'
               '不进入整行确认。句→载体归属为数据侧结构对应：唯一 sub99 载体（批 13 扩域后'
               '两域分源样本域；本行载体为 CACHE 层）＋'
               '敵減益半句形状匹配＋方向按符号（p7/p8 负值加算下降、p9 正值受伤量加算＝「防御」'
               '表现层）；引擎侧装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露：'
               + '；'.join(_sample_domain_note(R.rule_for('skilllist', 99, '/' + p), p)
                           for p in claimed_sorted) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject_phrase, attrs=list(claims), claims=dict(claims),
                table=table, carrier_record_id=carrier_id, carrier_layer='CACHE',
                carrier_name=crec.get('name'), via='own_sub_effect', sent_no=sent_no,
                sent_total=sent_total)


# ---- P6 跨 cid 载体竞争守卫（进程内登记；审计全库交叉检查实测 0 例）----
_CLAIMS = {}


# ---- pattern/charainfo 行的逐行 hint（938 行归属未化解登记；scope §5.2-7）----
def _shape_check_text(attrs, crec):
    """C1 hint 附形状核对结果（scope §3.1 映射；披露用，不构成消费依据）。"""
    parts = []
    ok = True
    for attr, slot in SLOT_OF.items():
        raw = crec.get(slot)
        act = _active(raw)
        claimed = attr in attrs
        if claimed != act:
            ok = False
        parts.append(f'{attr}↔/{slot}=' + (f'活性({raw!r})' if act else f'不活性({raw!r})'))
    return ('一致' if ok else '不一致'), '；'.join(parts)


def _pattern_chain_hint(data, pc, kids, attrs, table, subject):
    """bosspattern/denju/dlb（及 charainfo 经同文 pattern）行的链分类 hint（审计 §3 同法）。"""
    t13 = [c for c in kids if c.get('table') == 'bossskill' and c.get('effect_type') == 13]
    sa2003, dup = [], False
    for c in kids:
        if c.get('table') != 'skilllist' or c.get('link_kind') != 'boss_skill.s_ability':
            continue
        sid = c.get('record_id')
        lay, crec = _ability_by_id(data, sid)
        if crec is not None and crec.get('ability') == 2003:
            sa2003.append((sid, lay, crec))
    uniq = {}
    for sid, lay, crec in sa2003:
        uniq.setdefault((sid, lay), crec)
    dup = len(sa2003) > len(uniq)
    if len(uniq) > 1:
        det = '；'.join(f'skilllist|{sid}|{lay}' for (sid, lay) in uniq)
        return _hint(table, [f'C3：链上 {len(uniq)} 个不同 s_ability→2003（SA_PowerDrain）载体'
                             f'（归属歧义，multi-carrier）：{det}'
                             + ('；另有多中继同指（dup_relay）' if dup else '')],
                     subject=subject, attrs=attrs)
    if len(uniq) == 1:
        (sid, lay), crec = next(iter(uniq.items()))
        ok, detail = _shape_check_text(attrs, crec)
        return _hint(table, [f'C1：链上唯一 s_ability→skilllist ability=2003（SA_PowerDrain）载体 '
                             f'skilllist|{sid}|{lay}；形状核对（p7↔攻撃力/p8↔移動速度/p9↔防御力，'
                             f'431 行 6 种属性组合全自洽）：{ok}——{detail}；但 ability2003 无已'
                             '确认规则/无换算器/无证据目录（rules.json 99 族规则样本域明写仅 '
                             'ability99 的 133 条；2003 与 99 形状同构≠同规则），形状一致不构成'
                             '消费依据→留 hint（no-rule-2003；扩域需 ability2003 原生专项）'],
                     subject=subject, attrs=attrs)
    if t13:
        signs = []
        for c in t13:
            vals = {}
            for a in (c.get('answers') or []):
                fp = a.get('f') or a.get('field_path')
                if fp and fp.startswith('/skillparam'):
                    vals.setdefault(fp, a.get('raw'))
            signs.append(f"bossskill|{c.get('record_id')}|{c.get('layer')}"
                         f"（{','.join(f'{k}={v!r}' for k, v in sorted(vals.items())[:4])}）")
        # B9-R03 修复（20261021 定向审查）：parent sub_effect 的 ability99 记录为 profiles
        # 装配层 ID 碰撞伪影（profiles.py:426-428）——本分支按 B1 防线本就不消费 sub_effect，
        # 但 hint 须逐行披露该伪影存在（判定不变，仅补披露）。
        art99 = []
        for c in kids:
            if c.get('table') == 'skilllist' and c.get('link_kind') == 'sub_effect':
                lay, crec = _ability_by_id(data, c.get('record_id'))
                if crec is not None and crec.get('ability') == 99:
                    art99.append(f"skilllist|{c.get('record_id')}|{lay}")
        reasons = [f'C2：链上只有正値 bossskill type13 我方增益输入候选（无 2003/99 载体）：'
                   f'{"；".join(signs)}；et13 换算器硬编码「+」方向（rules.py:1349-1365），'
                   '关键词候选挂到敌方减益句＝方向翻转假阳性——B1 防线（30338）：逐字'
                   '对象/方向审核拒绝（direction-conflict-t13）']
        if art99:
            reasons.append(f'披露：parent sub_effect 存在 ability99 伪影（{"、".join(art99)}），'
                           '按 B1 防线不消费、profiles 装配层 ID 碰撞伪影见任务卡遗留')
        return _hint(table, reasons, subject=subject, attrs=attrs)
    return _hint(table, ['C4：链上无 t13/99/2003 任一减益载体（no-debuff-carrier）'],
                 subject=subject, attrs=attrs)


def evaluate(record: dict, frag: str, table: str, layer: str | None = None, record_id=None,
             text: str | None = None, data=None, cid=None):
    """对一行做批 9 敵デバフ审核，返回 None（不属本批范围）或审核结果 dict。

    table：行记录表（TABLES 七表）；layer/record_id：行记录来源层与 id；text：行记录
    正文字段全文（clean 后）；data/cid：页级 Inputs 与 cid（data.old 子记录索引）。

    结果 dict：kind='promote'（answers/summary_reason/extra_reasons 等）或 'hint'（reasons）。
    """
    if data is None or cid is None or table not in TABLES or not isinstance(record, dict):
        return None
    j = frag
    # --- P1 句面（审计广筛口径逐字沿用） ---------------------------------------------------
    if '敵' not in j:
        return None
    if not any(w in j for w in DOWN_WORDS):
        return None
    if not any(a in j for a in ATTRS3):
        return None
    if '敵から受ける' in j:
        return None  # 我方被击减伤句（非敌方减益），不在本批
    clause, attrs, subject = _debuff_clause(j)
    if clause is None or not attrs or not subject:
        # B1 逐字对象门：下降谓词句段无「敵」或无属性——敌/我方向归属不成立，绝不晋级
        if '属性防御力' in (clause or ''):
            # B9-R02 修复（20261021 定向审查）：「属性防御力を下げる」句段对象承接前句
            # 「攻撃した敵に」（敌方减益），此前误写「我方半句」——改为如实理由；
            # 仅披露文案修正，判定（hint、不晋级）与属性门不变。
            return _hint(table, [f'P1/B1：首个下降谓词句段「{clause}」＝敌方属性防御减益'
                                 '；属性防御力超出本批攻/防/移属性范围（属性门），归属未化解'
                                 '——不晋级（30338 防线镜像门）'],
                         subject=subject, attrs=attrs)
        return _hint(table, [f'P1/B1：首个下降谓词句段「{clause or "?"}」未同时含「敵」与攻/防/移'
                             '属性——敌方减益半句不成立（敵/方向归属未化解；我方半句不得挂敌方'
                             '减益值，30338 防线镜像门）'], subject=subject, attrs=attrs)
    claims = {a: True for a in attrs}
    pc = _chain_index(data)

    # --- 句序披露 --------------------------------------------------------------------------
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    _sents = [s for s in re.findall(r'[^。]*。', wb)]
    sent_no = next((i + 1 for i, s in enumerate(_sents) if frag.strip() in s), None)
    sent_total = len(_sents)

    # --- P2–P6（skilllist/supporterskill 行；B1：只认自身 sub_effect 链） -------------------
    if table in PROMOTABLE_TABLES:
        kids = [ch for ch in pc.get((table, str(record_id), layer), [])
                if ch.get('table') == 'skilllist' and ch.get('link_kind') == 'sub_effect']
        c99, apk99 = [], []
        for ch in kids:
            sid = ch.get('record_id')
            lay, crec = _ability_by_id(data, sid)
            if lay == 'CACHE' and crec.get('ability') == 99:
                c99.append((sid, crec))
            elif lay == 'APK' and crec.get('ability') == 99:
                apk99.append((sid, crec))
        own_ability = record.get('ability')
        own_note = (f'；行记录自身 ability={own_ability}（{layer} 层）——按 scope §5.1 P2，'
                    '载体主张只认 sub_effect 链上的域内 99 记录，行自身参数不消费'
                    if own_ability == 99 else '')
        if apk99 and not c99:
            # 批 13 APK 扩域（2026-10-22）：rules.json skilllist|99 四键样本域已扩至
            # CACHE＋APK 两域分源（occurrences_apk 登记），本出口委托批 13 模块按载体层
            # 域接管：单 APK 载体→P4/P5/P4b/P6 门控后晋级（行级键 inference_b13）或
            # hint；多载体→hint multi-carrier。返回 dict 带 b13_ext 标记（行级键
            # inference_b13/inference_b13_hint 替换本批旧域外 hint，不双登记）。
            import card_page_inference_b13_apkext as B13
            return B13.handle_99_apk(frag=j, table=table, layer=layer, record_id=record_id,
                                     cid=cid, subject=subject, attrs=attrs,
                                     sent_no=sent_no, sent_total=sent_total,
                                     apk99=apk99, own_ability=record.get('ability'),
                                     text=text)
        if not c99:
            sub_ids = [str(ch.get('record_id')) for ch in kids]
            return _hint(table, ['P2：own sub_effect 链上无 ability99 载体（no-99-carrier'
                                 + (f'；链上 sub 子记录：{",".join(sub_ids[:8])}' if sub_ids else
                                    '；行记录无 sub_effect 子记录') + '）' + own_note],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
        if len(c99) > 1:
            det = '；'.join(f'skilllist|{sid}|CACHE' for sid, _ in c99)
            return _hint(table, [f'P3：{len(c99)} 个 99 载体（归属歧义，multi-carrier）：{det}'],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
        carrier_id, crec = c99[0]
        domain = _domain99(data)
        if carrier_id not in domain:
            return _hint(table, [f'P2：99 载体 skilllist|{carrier_id}|CACHE 不在 133 条样本域'
                                 '（carrier-out-of-domain）'],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
        # P4 形状（双向；对敵減益半句属性）
        mism = []
        for attr, slot in SLOT_OF.items():
            claimed = attr in attrs
            act = _active(crec.get(slot))
            if claimed and not act:
                mism.append(f'敵減益半句含{attr}但载体 /{slot} 不活性({crec.get(slot)!r})')
            if (not claimed) and act:
                mism.append(f'载体 /{slot} 活性({crec.get(slot)!r})但敵減益半句无{attr}')
        if mism:
            return _hint(table, ['P4：形状不符：' + '；'.join(mism) + '（缺槽＝缺失不补 0，'
                                 'rules limits 口径）'],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
        # P5 方向（代码语义）
        dir_bad = []
        for param in ('param7', 'param8'):
            raw = crec.get(param)
            if _active(raw) and raw > 0:
                label = '攻撃力' if param == 'param7' else '移動速度'
                dir_bad.append(f'/{param}={raw}>0 与{label}下降冲突（加算正值为上升贡献）')
        p9 = crec.get('param9')
        if _active(p9) and p9 < 0:
            dir_bad.append(f'/param9={p9}<0 与受伤量加算口径（防御下降的表现层）冲突')
        if dir_bad:
            return _hint(table, ['P5：方向冲突（direction-mismatch）：' + '；'.join(dir_bad)],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
        # P4b 竞争句（批 6 G6 检测扩展）
        competitors = _competing_debuff_sentences(text, frag, attrs)
        if competitors:
            return _hint(table, ['P4b：本记录正文内存在其它敵下降句主张同属性（归属歧义，'
                                 'competing-debuff-sentence）：'
                                 + '；'.join(c.strip()[:50] for c in competitors[:4])],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
        # P6 跨 cid 载体竞争守卫
        others = _CLAIMS.get(carrier_id, set()) - {cid}
        if others:
            return _hint(table, [f'P6：跨 cid 载体竞争：载体 skilllist|{carrier_id}|CACHE 已被 '
                                 f'cid {",".join(map(str, sorted(others)))} 的行主张（进程内登记；'
                                 '审计全库交叉检查实测 0 例，本守卫为防御性保留）'],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
        _CLAIMS.setdefault(carrier_id, set()).add(cid)
        return _promote(frag, table, layer, record_id, cid, attrs, claims, subject, clause,
                        (carrier_id, crec), sent_no, sent_total, competitors)

    # --- hint 登记路径（B1：pattern/denju/dlb/charainfo/heroic 行不晋级） --------------------
    if table == 'charainfo':
        # G5 同法（批 6/批 8）：同页同文 bosspattern 记录须唯一
        ctx = B6._page_ctx(data, cid)
        jk = lambda t: unicodedata.normalize('NFKC', t).strip().rstrip('。').strip()
        matched = []
        for e, fragset in ctx['pattern_frags']:
            for fs in fragset:
                if jk(frag) in jk(fs) or jk(fs) in jk(frag):
                    matched.append(e)
                    break
        pat_ids = {(str(e.get('reference_id')), e.get('layer')) for e in matched}
        if len(pat_ids) > 1:
            return _hint(table, [f'charainfo 行：同文对应 {len(pat_ids)} 个 pattern 记录'
                                 f'（{",".join(sorted(p[0] for p in pat_ids))[:60]}），归属歧义'
                                 '（b6 G5 同法）'], subject=subject, attrs=attrs,
                         sent_no=sent_no, sent_total=sent_total)
        if not pat_ids:
            return _hint(table, ['charainfo 行：同页无同文 bosspattern 行，pattern 链不可达'
                                 '（b6 H5 同法）'], subject=subject, attrs=attrs,
                         sent_no=sent_no, sent_total=sent_total)
        pid, player = next(iter(pat_ids))
        kids = pc.get(('bosspattern', pid, player), [])
        if not kids:
            return _hint(table, [f'charainfo→同页同文 bosspattern|{pid}|{player}：该 pattern '
                                 '记录无 children（链缺口）'], subject=subject, attrs=attrs,
                         sent_no=sent_no, sent_total=sent_total)
        out = _pattern_chain_hint(data, pc, kids, attrs, table, subject)
        out['reasons'] = [f'charainfo 经同页同文 bosspattern|{pid}|{player}；' + r
                          for r in out['reasons']]
        return out
    if table == 'heroicskilllist':
        pats = [(k, v) for k, v in record.items()
                if re.match(r'^boss_pattern\d*$', k) and isinstance(v, int)
                and not isinstance(v, bool) and v]
        det = ('；boss_pattern 字段：' + '、'.join(f'{k}={v}' for k, v in pats[:4])) if pats else ''
        return _hint(table, ['heroic 行：boss_patternN 链不在 children 装配内（b8 B8-R01 同法'
                             '登记；本轮不解析，未晋级）' + det],
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    # bosspattern / denju / denju_limit_break_info：own children（B1：不经 sub_effect 消费）
    kids = pc.get((table, str(record_id), layer), [])
    if not kids:
        return _hint(table, [f'{table} 行：父记录无 children（链缺口）'],
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    return _pattern_chain_hint(data, pc, kids, attrs, table, subject)
