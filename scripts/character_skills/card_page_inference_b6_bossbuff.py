"""模板作用域推断层——批 6：味方全体必殺バフ家族（Top20 #1）bossskill 子记录解析。

设计与范围依据：``output/character_skills/inference_inventory/b6_bossbuff_scope.md``
（批 6 前置审计；逐行明细 work/character_skills_b6_bossbuff/fam1_classification.json：
全库家族 #1 共 2,139 行，其中 30236 两条既有基线 A 行（pattern1/pattern2，既有答案确认）
被 ``not answers`` 守卫排除、零变化——b6 评估 2,137 行＝2,139−2）。
20261020 B6-RV-01 修复后口径：晋级 **1,349**（bosspattern 602／denju 350／dlb 30／
charainfo 经同页同文 pattern 367）＋留 hint **788**（含同属性集合竞争 ally-buff 句 30 行
降级：「範囲内の味方」竞争句 24 行＋复合句内嵌「自身の…」短语 6 行——唯一 type13 的活性槽
形状同时匹配本句与竞争句且无已确认规则指定接受者，归属不能唯一化解，按 INFR-05 不猜）。

主缺口＝bossskill 子记录类型解析接入：bossskill 顶层记录 0 条，仅以 children 存在
（8,842 实例／5,462 distinct id），children 已带 effect_type（=skillid0）＋完整
answers/unexplained（profiles.py build_record）。「子记录类型无法解析」只是批 1 盘点
索引缺口（enrich_v2.py 只索引顶层）——本模块运行时从 ``profiles/records.jsonl``（经
``Inputs.old`` 已装载）构建 ``(table, record_id, layer) → 记录`` 索引取 children，
不重读解码 JSON、不重复 links 解析、不需要新解析器。records.jsonl 实测该键唯一
（0 冲突）；children 未存 slot，槽位披露从 links ``boss_skill_refs[].slot`` 取。

精确范围（scope §4/§5，门控 G1–G7 全部通过才晋级；任一不过→留 hint 并登记原因）：

* 行记录表 ``table ∈ {bosspattern, charainfo, denju, denju_limit_break_info,
  heroicskilllist}`` 且晋级前无既有答案（调用点 ``not answers`` 守卫）；
* 日文正文匹配家族 #1 模板：``norm_text``/``family_of`` 与批 1 盘点逐字节同法
  （NFKC＋数字→N＋占位→⟨X⟩/⟨Y⟩；连接词 その後、/さらに/ただし、/また/更に 剥离），
  终模板恰为 ``味方全体の⟨ATTR⟩が一定時間上がる。``（纯句；句后文本/数字变体不匹配）；
* **G1 链可达**：父记录（bosspattern/denju/dlb：自身记录；charainfo：同页同文
  bosspattern 记录，G5 唯一）在 records.jsonl 有 children；
* **G2 唯一载体**：父记录链上恰 1 个 type13 子记录（0→链缺口 hint；≥2→多 pattern 歧义
  hint）；只有 type13 可作载体，type46/55 等 status=None 类型即使链上也不消费；
* **G3 形状匹配**：活性槽 {p1,p2,p6 原值≠0} == 句中非 crit 属性集合（攻撃力→p1、
  防御力→p2、移動速度→p6）；且 p3（一定時間）≠0；
* **G4 crit 排除**：句含クリティカル属性→整行留 hint（bossskill|13 无 crit 槽规则），
  不拆半晋级；
* **G5 唯一 charainfo 映射**：charainfo 行的同文 pattern 记录须唯一（同文对应 2+ 个
  pattern 记录→归属歧义 hint；无同文 pattern 行→链不可达 hint）；
* **G6 无同记录冲突**：同父记录上另有 fam1 双句／fam11（自身バフ）／fam13（上げる）
  →hint（同一 t13 可能被多句主张）；G6 扩展（B6-RV-01，20261020）：父记录正文另含
  与本句同属性集合、同方向（上がる）的竞争 ally-buff 句——「範囲内の味方の⟨ATTR⟩が
  一定時間上がる」独立句，或复合句内嵌「自身の⟨ATTR⟩が…上がり」短语（按「。」逐句
  归一化后匹配，原整句家族匹配看不到）→hint，写明竞争句原文；
* **G7 同文一次**：同文在记录正文恰 1 次（charainfo 行按其同文 pattern 记录正文计，
  审计同口径）。

非首段口径（20261020 主持裁决，scope §4.1 替代口径）：「非首段留 hint」的本意是
「归属无法逐句化解时不猜」（INFR-05 先例），不是「非首段天然不可晋级」。本批非首段行
**仅在归属已结构性化解**（G2 唯一载体＋G3 形状匹配）时晋级；同文多次（G7）与方向冲突
仍一律留 hint。位置序论证不可用（段位↔skillid 槽位序实测无一一对对应）——行级 summary
与值行 note 按数据侧结构对应措辞披露（B5-R03 同性质），不写「段位↔槽位位置序对应」。

句式→类型→param 映射（唯一映射表，scope §5.2；规则键 rules.json ``bossskill|13|/skillparamN``）：

=============== ==================  ==================================================
句中成分        记录槽/规则键        值行数量类型（rules.py 换算器）
=============== ==================  ==================================================
攻撃力          /skillparam1        攻击增益输入（attackRate=原值×Chain；_attackUp=1+）
防御力          /skillparam2        固定防御量（系数已知）（guard=trunc(_normalAtk×…)；
                                    名义原始 ATK 系数=原值×0.1；语义按规则自身，不改写）
移動速度        /skillparam6        移动速度乘数（moveRate 同构）
一定時間        /skillparam3        持续时间（游戏秒，非墙钟秒）
クリティカル*   —（无规则）         整行留 hint（G4）
=============== ==================  ==================================================

硬边界（scope §5.5/§6/§8，逐行强制）：

* **只升「推断」，绝不升「确认」**：值行 numeric_evidence/association_evidence 一律
  「推断」；行级标注「推断（模板批 6 必殺バフ）」、evidence_scope=TEMPLATE_BATCH6_BOSSBUFF；
  不进入整行确认统计；「唯一 t13＋形状匹配」是数据侧结构对应，永不据此升「确认」。
* **对象＝味方全体仅句面依据**（§5.3）：「味方全体の」逐字在句中（家族定义保证）；
  t13 处理器的接受者选择逻辑无已确认规则（/iparam* 原值未解释，逐行登记原值），
  不得主张记录侧对象证据。
* **证据按字段**（INFR-01）：值行 evidence 取 rules.json ``bossskill|13|/skillparamN``
  的 evidence——p1/p3/p6→output/boss_heal/field_dictionary.json＋README.md；
  p2→output/boss_chain/type13_basis/ 6 件（含 trace.json/native_checks.json）。
  证据文件缺失显式失败，不产出死指针。
* **样本域披露按规则分支**（INFR-02；本批特有）：bossskill|13 各规则 occurrences=
  None（未登记已核样本域，与批 5 的 321 条已核样本域不同）→逐行披露「按类型规则外推」；
  p2 例外（occ=718，origin cid30236 对照词典）→按其登记口径披露。子记录层（APK/CACHE）
  照实登记。
* **方向审核**（§5.4）：p1/p6 原值>0（增益加算输入）、p2>0（guard）、p3>0（时长）；
  0 值槽已被 G3 排除；负值→hint。语义不换名：防御力值行保持规则自身语义
  「guard＝固定防御量（系数已知）」，不改写成受伤量倍率/减伤自由文案；p1/p6 是
  「增益输入（再乘 Chain）」，不写成最终面板倍率。
* **不跨记录合并**（§6.2）：charainfo 行与同文 pattern 行各自产出值行并各自注来源；
  同 pattern 多行（多等级）不折叠；伤害侧子记录（t22/t105/t112 等）与 skilllist 候选
  （同记录伤害段的 sub_effect/s_ability 参数）一律不进入 buff 句值行；
  charainfo 行自身 skillparam* 为伤害侧未执行副本，不消费。
* **逐行处理、不折叠**（§5.5-6）：同 pattern 的 sinfo 行与 charainfo 行各自晋级；
  多段披露逐行登记（◆ 段口径＋「。」句序（B6-RV-04，20261020）：◆ 段口径不传达句序，
  另行披露 buff 句位于正文第 N 句／共 M 句；与批 3–5 INFR-05 披露同口径）。
"""
from __future__ import annotations

import collections
import json
import math
import re
import unicodedata
from pathlib import Path

import rules as R
import card_page_inference_type8 as TYPE8
from card_page_positions import fragment_positions

B6_TAG = '推断（模板批 6 必殺バフ）'
B6_SCOPE = 'TEMPLATE_BATCH6_BOSSBUFF'
B6_FAMILY = '味方全体の⟨ATTR⟩が一定時間上がる。（bosspattern/denju/dlb/charainfo→bossskill type13 子记录）'

TABLES = ('bosspattern', 'charainfo', 'denju', 'denju_limit_break_info', 'heroicskilllist')

# ---- 家族模板（与批 1 enrich_v2.py / build_families_v2.py 及批 6 审计 scan_fam1.py 逐字节同法）----
_ATTRS = ['クリティカル威力', 'クリティカル発生率', 'クリティカル率', 'クリティカル',
          '通常攻撃威力', '攻撃間隔', '攻撃速度', '移動速度', '防御力', '攻撃力',
          '受けるダメージ', '与えるダメージ', 'HP', '効果']
_attr_alt = '|'.join(re.escape(a) for a in sorted(_ATTRS, key=len, reverse=True))
_RUN = re.compile(r'(?:%s)(?:と(?:%s))+' % (_attr_alt, _attr_alt))
_PRED = r'(?:が|を|も)[^。、]{0,10}?(?:上がる|上がり|下がる|下がり|上げる|下げる|回復する|回復し|早くなる|遅くなる)'
_SINGLE = re.compile(r'(?:%s)(?=%s)' % (_attr_alt, _PRED))
_CONNECTIVES = ['その後、', 'さらに', 'ただし、', 'また', '更に']

FAM1 = '味方全体の⟨ATTR⟩が一定時間上がる。'
FAM11 = '自身の⟨ATTR⟩が一定時間上がる。'
FAM13 = '味方全体の⟨ATTR⟩を一定時間上げる。'
_FAMS = (FAM1, FAM11, FAM13)


def _norm_text(t):
    t = unicodedata.normalize('NFKC', t).strip()
    t = re.sub(r'[0-9]+', 'N', t)
    t = re.sub(r'(<[^<>]*>)|(＜[^＜＞]*＞)', '⟨X⟩', t)
    t = re.sub(r'(≪[^≪≫]*≫)', '⟨Y⟩', t)
    return t


def _family_of(template):
    t = _RUN.sub('⟨ATTR⟩', template)
    t = _SINGLE.sub('⟨ATTR⟩', t)
    for c in _CONNECTIVES:
        if t.startswith(c):
            t = t[len(c):]
    return t


# ---- 句式→槽位 1:1 映射（scope §5.2；bossskill|13 仅此 4 条规则）--------------------------
ATTR_PARAM = {'攻撃力': 'skillparam1', '防御力': 'skillparam2', '移動速度': 'skillparam6'}
DUR_PARAM = 'skillparam3'
DUR_ATTR = '一定時間'
# 句中属性识别顺序（audit_part4 attrs_of 同法：按列表序对模板做包含判定）。
_ATTR_DETECT = ('クリティカル発生率', 'クリティカル威力', 'クリティカル率', 'クリティカル',
                '移動速度', '防御力', '攻撃力', 'HP', '受けるダメージ', '与えるダメージ')

_EVIDENCE_CACHE = {}


def _field_evidence(field):
    """按字段解析 rules.json bossskill|13|/skillparamN 的 evidence 并做存在性检查（INFR-01）。

    p1/p3/p6（boss_heal 字典来源）：evidence 为 ('output/boss_heal/field_dictionary.json',
    'output/boss_heal/README.md')；p2（cid30236 对照词典来源）：6 条 '../boss_chain/…' 相对
    路径，解析根与试点同法（origin=output/card_comparison_cid30236/）→ output/boss_chain/…。
    """
    if field in _EVIDENCE_CACHE:
        return _EVIDENCE_CACHE[field]
    rule = R.rule_for('bossskill', 13, '/' + field)
    files = []
    for entry in (rule or {}).get('evidence') or []:
        items = entry if isinstance(entry, (list, tuple)) else [entry]
        for e in items:
            e = str(e)
            files.append('output/' + e[3:] if e.startswith('../') else e)
    expected_dir = ('output/boss_chain/type13_basis/' if field == 'skillparam2'
                    else 'output/boss_heal/')
    if not files or any(not p.startswith(expected_dir) for p in files):
        raise ValueError(f'批 6 证据解析异常（INFR-01）：bossskill|13|/{field} 的 rules.json '
                         f'evidence 未解析为 {expected_dir} 下的文件，实际 {files!r}')
    missing = [p for p in files if not Path(p).is_file()]
    if missing:
        raise FileNotFoundError(f'批 6 证据文件缺失（INFR-01）：{missing}')
    _EVIDENCE_CACHE[field] = (expected_dir, files)
    return _EVIDENCE_CACHE[field]


# ---- G6 扩展：同属性集合竞争 ally-buff 句检测（B6-RV-01，20261020 修复）------------------
# 原 G6 只按家族模板匹配整句（fam1 双句/fam11/fam13），漏两类竞争句：
#   ①「（さらに/また）範囲内の味方の⟨ATTR⟩が一定時間上がる」（家族模板不含该主语，整句不匹配
#      fam1/11/13 → fam_counts 看不到）；
#   ②复合句内嵌的「自身の⟨ATTR⟩が一定時間上がり」短语（按「。」切分的整句以敵デバフ开头，
#      family_of 不匹配）。
# 修复：对父记录正文按「。」逐句归一化后，用主语＋属性连词串＋「一定時間上がる/上がり」
# 形状匹配竞争短语；主语为味方全体且句属性集合与本句相同的匹配即本句自身（唯一 t13 已被
# G2/G3 归属），排除；主语为其它 ally 主语（範囲内の味方/味方/自身）且属性集合与本句相同
# →竞争句（唯一 t13 的活性槽形状同时匹配两句，归属不能唯一化解→按 INFR-05 留 hint，
# hint 写明竞争句原文）。方向仅取上がる/上がり（ally 增益）；敵の…下がる 不构成竞争。
_COMPET_SUBJ = r'(味方全体|範囲内の味方|味方|自身)'
_COMPET_RUN = r'((?:%s)(?:と(?:%s))*)' % (_attr_alt, _attr_alt)
_COMPET_PRED = r'が一定時間(上がる|上がり)'
_COMPET = re.compile(_COMPET_SUBJ + 'の' + _COMPET_RUN + _COMPET_PRED)


def _competing_ally_buffs(body, attrs):
    """父记录正文内与本句同属性集合、同方向（上がる/上がり）的其它 ally-buff 句（原文）。

    按「。」切句（复合句内的 fam11/範囲内の味方 短语同样可见），逐句归一化后匹配
    _COMPET；味方全体 主语的匹配视为本句自身（fam1 双句/同文多次已由 G6/G7 覆盖），
    仅收集其它 ally 主语且属性集合与本句非 crit 属性集合完全相同的短语所在句。
    返回去重后的竞争句原文列表（含句号）。
    """
    want = set(attrs)
    out = []
    for s in re.findall(r'[^。]*。', body or ''):
        ns = _norm_text(s)
        for m in _COMPET.finditer(ns):
            if m.group(1) == '味方全体':
                continue
            if set(m.group(2).split('と')) != want:
                continue
            out.append(s)
            break
    return list(dict.fromkeys(out))


def _raw_of(child, field):
    for a in child.get('answers') or []:
        if a.get('f') == '/' + field:
            return a.get('raw')
    for u in child.get('unexplained') or []:
        if u.get('f') == '/' + field:
            return u.get('raw')
    return None


def _num(raw):
    return (isinstance(raw, (int, float)) and not isinstance(raw, bool)
            and math.isfinite(raw))


def _direction_text(param, raw):
    """方向审核（scope §5.4）：p1/p6 增益输入>0、p2 guard>0、p3 时长>0；负值冲突。"""
    label = {'skillparam1': '攻击增益输入', 'skillparam2': 'guard 固定防御量（系数已知）',
             'skillparam6': '移动速度增益输入', 'skillparam3': '持续时间'}[param]
    return (f'方向一致（原值 {raw}>0，{label}，与句「上がる」方向一致）' if raw > 0
            else f'方向冲突（原值 {raw}<=0，句称上升；保守留 hint）')


# ---- 运行时子记录解析（scope §5.1；读 Inputs.old（records.jsonl 页记录子集），不重读解码 JSON）----
_PAGE_CACHE = {}


def _page_ctx(data, cid):
    """页级上下文（每卡构建一次，进程内缓存）：记录索引＋pattern 片段集＋家族行计数。"""
    key = (id(data), cid)
    hit = _PAGE_CACHE.get(key)
    if hit is not None:
        return hit[1]
    links = data.links[cid]
    rec_index = {}
    for r in data.old.values():
        rec_index[(r.get('table'), str(r.get('record_id')), r.get('layer'))] = r
    # 同页 bosspattern 记录及其片段集（charainfo G5 映射用；与行生成同一 fragment_positions 口径）
    pattern_frags = []
    for g in links.get('groups') or []:
        if g.get('group') != 'special_move':
            continue
        for e in g.get('records') or []:
            if e.get('table') != 'bosspattern':
                continue
            fragset = {sp['japanese'] for sp in fragment_positions((e.get('record') or {}).get('sinfo', ''))}
            pattern_frags.append((e, fragset))
    # G6 家族行计数：按父记录键聚合全页条目的家族片段（与审计 fam_rows_by_parent 同口径——
    # 按条目×片段计数，同位置别名行按（pk,ref,句,跨度）去重，对应 card.json 的合并行）。
    fam_counts = {}
    seen_frag = set()
    text_field = {'charainfo': 'skilltext', 'bosspattern': 'sinfo', 'denju': 'stext',
                  'denju_limit_break_info': 'stext'}
    for g in links.get('groups') or []:
        for e in g.get('records') or []:
            table = e.get('table')
            rec = e.get('record') or {}
            tf = text_field.get(table, 'text')
            pk = (table, str(e.get('reference_id')), e.get('layer'))
            ref = e.get('reference_field')
            for sp in fragment_positions(rec.get(tf, '')):
                fam = _family_of(_norm_text(sp['japanese']))
                if fam not in _FAMS:
                    continue
                dedup = (pk, ref, sp['japanese'], tuple(sp['raw_span']))
                if dedup in seen_frag:
                    continue
                seen_frag.add(dedup)
                fam_counts.setdefault(pk, collections.Counter())[fam] += 1
    ctx = dict(rec_index=rec_index, pattern_frags=pattern_frags, fam_counts=fam_counts)
    _PAGE_CACHE[key] = (data, ctx)  # 连同 data 持强引用，避免 id 复用串页
    return ctx


def _gate_parent(parent, attrs, has_crit, same_count, fam_counter, competitors=()):
    """G2–G7 门控（audit_part4 classify 同序；返回 (reasons, t13_child)）。

    competitors：父记录正文内与本句同属性集合的竞争 ally-buff 句原文（G6 扩展，B6-RV-01）。
    """
    boss_kids = [c for c in parent.get('children') or [] if c.get('table') == 'bossskill']
    ets = [c.get('effect_type') for c in boss_kids]
    t13 = [c for c in boss_kids if c.get('effect_type') == 13]
    if not t13:
        return ['父记录无可解析的 type13 增益子记录（链上类型=%s）' % (ets,)], None
    if len(t13) > 1:
        return ['父记录有 %d 个 type13 子记录（传授多 pattern），本行无逐 pattern 文本对应' % len(t13)], None
    c = t13[0]
    raws = {q: _raw_of(c, q) for q in ('skillparam1', 'skillparam2', 'skillparam6',
                                       'skillparam3', 'skillparam4', 'skillparam5')}
    exp = {ATTR_PARAM[a] for a in attrs if a in ATTR_PARAM}
    act = {q for q in ('skillparam1', 'skillparam2', 'skillparam6') if _num(raws.get(q)) and raws.get(q) != 0}
    if act != exp:
        return ['形状不符：句属性槽 %s ≠ 活性槽 %s' % (sorted(exp), sorted(act))], None
    if not (_num(raws[DUR_PARAM]) and raws[DUR_PARAM] != 0):
        return ['持续时间槽 skillparam3 无非零值'], None
    if has_crit:
        return ['句含クリティカル属性，bossskill|13 无 crit 槽已确认规则（p4/p5 原值 %s/%s）'
                % (raws['skillparam4'], raws['skillparam5'])], None
    if same_count > 1:
        return ['同文在记录正文出现 %d 次' % same_count], None
    fam1_n = fam_counter.get(FAM1, 0)
    if fam1_n > 1:
        return ['同记录有 %d 条本家族句（多 buff 句共享同一 type13）' % fam1_n], None
    if fam_counter.get(FAM11) or fam_counter.get(FAM13):
        return ['同记录另有自身バフ/上げる句家族行，type13 归属可能冲突'], None
    if competitors:
        return ['同记录存在同属性集合（%s）、同方向（上がる）的竞争 ally-buff 句（%s）：'
                '唯一 type13 的活性槽形状同时匹配本句与竞争句，无已确认规则指定接受者，'
                '归属不能唯一化解（G2＋G3 不足；按 INFR-05 不猜，留 hint）'
                % ('・'.join(sorted(set(attrs))), '；'.join(competitors))], None
    return [], c


def _iparam_note(child):
    parts = []
    for u in (child.get('unexplained') or []) + (child.get('answers') or []):
        f = u.get('f') or ''
        if f.lstrip('/').lower().startswith('iparam'):
            parts.append(f'{f}={u.get("raw")!r}')
    if not parts:
        return '该子记录无 /iparam* 字段'
    seen = list(dict.fromkeys(parts))
    return '、'.join(seen) + '（原值未解释）'


def _sample_domain_note(field, rule):
    """样本域披露（INFR-02；按规则 occurrences 分支——scope §5.5-3）。

    B6-RV-02（20261020 修复）：rules.py 合并源条目未携带 origin 键（合并源
    output/card_comparison_cid30236/field_dictionary.json 自身无 origin 键），此前 p2 分支
    会打印「origin None」——不属实。改为按 profiles/rules.json 登记的 origin 输出
    （bossskill|13|/skillparam2 登记 origin=output/card_comparison_cid30236/field_dictionary.json）。
    """
    occ = rule.get('occurrences')
    if occ is None:
        return ('该规则已核样本域未登记（occurrences=None）；规则证据为 output/boss_chain/'
                'type13_basis 受控原生片段＋output/boss_heal 字典，按类型规则外推，不属逐记录确认')
    origin = rule.get('origin') or _registered_rule(field).get('origin') or '未登记'
    return (f'该规则登记已核出现 {occ} 次（origin {origin}）；本行来源子记录未逐条'
            '核对，按规则适用条件披露（含限定玩家构建分支等），不属逐记录确认')


_REGISTERED_RULES = None


def _registered_rule(field):
    """profiles/rules.json 登记的规则条目（origin 权威来源；profiles/ 为本批只读共享依赖，
    已在 card_page_dependencies.data_paths 声明清单内）。"""
    global _REGISTERED_RULES
    if _REGISTERED_RULES is None:
        p = Path('output/character_skills/profiles/rules.json')
        _REGISTERED_RULES = json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}
    return _REGISTERED_RULES.get(f'bossskill|13|/{field}') or {}


def _promote(frag, table, layer, record_id, text, body, subject, attrs, section_no, section_count,
             parent_rec_key, parent_table, parent_record_id, parent_layer, child, via, via_desc,
             pattern_rec_key, boss_skill_refs, sent_no=None, sent_total=0):
    """晋级行：值行全部来自父记录唯一 type13 子记录，逐行注明来源记录链（scope §5.5）。"""
    child_id = child.get('record_id')
    child_layer = child.get('layer')
    child_key = f'bossskill|{child_id}|{child_layer}'
    chain_desc = parent_rec_key + '→' + child_key
    if via == 'charainfo_via_pattern':
        chain_desc = f'charainfo|{record_id}|{layer}→同页同文 {pattern_rec_key}→' + child_key
    # 槽位（records.jsonl children 未存 slot；从 links boss_skill_refs 取，scope §1.3）
    slot = None
    for r in boss_skill_refs or []:
        if r.get('table') == 'bossskill' and str(r.get('reference_id')) == str(child_id):
            slot = r.get('slot')
            break
    slot_desc = (f'bossskill 子记录经父记录 boss_skill_refs 槽位 {slot} 引用（records.jsonl '
                 'children 未存 slot，槽位取自 links 现产物）' if slot else
                 'links boss_skill_refs 未登记该子记录槽位（如实登记，不以 children 顺序推断）')
    numeric_source = f'模板推断（批 6 必殺バフ：{chain_desc}）'
    answers = []
    claimed = set()
    for attr in attrs:
        param = ATTR_PARAM[attr]
        claimed.add(param)
        raw = _raw_of(child, param)
        rule = R.rule_for('bossskill', 13, '/' + param)
        converted = R.answer_for('bossskill', 13, '/' + param, raw, child)
        evidence_dir, evidence_files = _field_evidence(param)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B6_SCOPE,
            rule_key=f'bossskill|13|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='bossskill', record_id=child_id, layer=child_layer,
                        record_key=child_key),
            note=(f'模板批 6 必殺バフ值行（来源记录＝{child_key}，{via_desc}）；'
                  f'句中「{attr}」→/{param} 1:1 映射；规则键 bossskill|13|/{param}；'
                  f'原值 {raw}；方向审核 {_direction_text(param, raw)}；证据目录 {evidence_dir}；'
                  f'对象「味方全体」为句面依据，该 type13 处理器的接受者选择逻辑无已确认规则'
                  f'（{_iparam_note(child)}）；样本域：{_sample_domain_note(param, rule)}；'
                  f'{slot_desc}'),
            quantitative=True))
    # 一定時間 → /skillparam3（持续时间，游戏秒；G3 已保证非零）
    raw = _raw_of(child, DUR_PARAM)
    rule = R.rule_for('bossskill', 13, '/' + DUR_PARAM)
    converted = R.answer_for('bossskill', 13, '/' + DUR_PARAM, raw, child)
    evidence_dir, evidence_files = _field_evidence(DUR_PARAM)
    answers.append(dict(
        value=converted['value_text'],
        quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
        raw_value=raw, field_path='/' + DUR_PARAM,
        numeric_source=numeric_source, numeric_evidence='推断',
        association_evidence='推断', evidence_scope=B6_SCOPE,
        rule_key=f'bossskill|13|/{DUR_PARAM}',
        rule_body_status=rule.get('status'), rule_status=rule.get('status'),
        conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
        conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
        evidence=list(evidence_files),
        source=dict(table='bossskill', record_id=child_id, layer=child_layer,
                    record_key=child_key),
        note=(f'模板批 6 必殺バフ值行（来源记录＝{child_key}，{via_desc}）；'
              f'句中「{DUR_ATTR}」→/{DUR_PARAM} 1:1 映射；规则键 bossskill|13|/{DUR_PARAM}；'
              f'原值 {raw}；方向审核 {_direction_text(DUR_PARAM, raw)}；证据目录 {evidence_dir}；'
              '持续时间单位为游戏秒（fixedDeltaTime 累计；非现实墙钟秒）；'
              f'样本域：{_sample_domain_note(DUR_PARAM, rule)}；{slot_desc}'),
        quantitative=True))

    # --- 晋级行注记（不改变「推断」档位） --------------------------------------------------
    extra = []
    extra.append('对象披露（scope §5.3）：对象「味方全体」为句面依据；该 type13 处理器的接受者'
                 '选择逻辑无已确认规则（' + _iparam_note(child) + '），不主张记录侧对象证据')
    extra.append('跨记录归属依据（scope §5.5-4）：句→记录归属为数据侧结构对应——唯一 type13 '
                 '增益子记录＋句属性集合↔活性槽形状匹配＋同记录无同属性集合的竞争 ally-buff 句'
                 '（G6 竞争句检测，B6-RV-01 修复后全量复扫 0 新增）；'
                 'sub/link 引擎侧装载路径与接受者选择无原生核实')
    if sent_no:
        extra.append(f'多段披露（scope §5.5-5）：本记录共 {section_count} 个◆段，buff 句位于第 '
                     f'{section_no} ◆段（◆段口径不传达句序）；正文句序：buff 句位于第 {sent_no} '
                     f'句／共 {sent_total} 句（以「。」切分）；段位与 bossskill 槽位序无一一对对应'
                     '（批 6 审计实测），归属依据见上；非首段行按唯一载体＋形状匹配化解归属'
                     '（20261020 主持裁决，B5-R03 同性质披露）')
    else:
        extra.append(f'多段披露（scope §5.5-5）：本记录共 {section_count} 个◆段，buff 句位于第 '
                     f'{section_no} ◆段（◆段口径不传达句序；正文句序未能定位：片段不在可见正文'
                     '按「。」切分的句列中）；段位与 bossskill 槽位序无一一对对应'
                     '（批 6 审计实测），归属依据见上；非首段行按唯一载体＋形状匹配化解归属'
                     '（20261020 主持裁决，B5-R03 同性质披露）')
    extra.append('槽位披露：' + slot_desc)
    extra.append('不跨记录合并（scope §6.2）：本行值行仅含来源记录 ' + child_key +
                 ' 的 skillparam 换算；同记录伤害侧子记录（t22/t105/t112 等）与 skilllist 候选'
                 '（同记录伤害段参数）不进入本行值行'
                 + ('；charainfo 行自身 skillparam* 为伤害侧未执行副本，不消费' if via == 'charainfo_via_pattern' else ''))
    unclaimed = []
    for u in (child.get('answers') or []) + (child.get('unexplained') or []):
        f = u.get('f') or ''
        m = re.fullmatch(r'/skill(param\d+|flag\d+_?\d*)', f)
        if not m or m.group(1) in claimed:
            continue
        unclaimed.append(f'{f}={u.get("raw")!r}' + ('（原值 0，未被本句主张）' if u.get('raw') == 0 else ''))
    if unclaimed:
        extra.append('t13 子记录句外槽未分配（不归属本句，仅登记原值；crit 槽 p4/p5 无已确认规则）：'
                     + '、'.join(dict.fromkeys(unclaimed)))
    summary = (B6_TAG + '：buff 值行来源＝' + chain_desc + '（' + via_desc + '）；'
               '值行全部「推断」，不升「确认」，不进入整行确认。句→记录归属为数据侧结构对应：'
               '唯一 type13 增益子记录＋句属性集合↔活性槽形状匹配＋同记录无同属性集合的竞争 '
               'ally-buff 句（G6 竞争句检测，B6-RV-01 修复后全量复扫 0 新增）；'
               '引擎侧装载与接受者选择无原生核实。本记录共 ' + str(section_count) + ' 个◆段，'
               'buff 句位于第 ' + str(section_no) + ' ◆段（段位与槽位序无一一对对应；◆段口径'
               '不传达句序）'
               + (f'；正文句序：buff 句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）'
                  if sent_no else '；正文句序未能定位') + '。适用范围披露：'
               + '；'.join(_sample_domain_note(p, R.rule_for('bossskill', 13, '/' + p))
                           for p in sorted(claimed | {DUR_PARAM})) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject, attrs=list(attrs), table=table,
                parent_record_id=parent_record_id, parent_table=parent_table,
                parent_layer=parent_layer, chain_record_id=child_id, chain_layer=child_layer,
                chain_slot=slot, via=via, pattern_record_id=pattern_rec_key,
                section_no=section_no, section_count=section_count,
                sent_no=sent_no, sent_total=sent_total)


def evaluate(record: dict, frag: str, table: str, layer: str | None = None, record_id=None,
             text: str | None = None, data=None, cid=None, boss_skill_refs=None):
    """对一行做批 6 必殺バフ审核，返回 None（不属本批范围）或审核结果 dict。

    table：行记录表（TABLES 五表）；layer/record_id：行记录来源层与 id；text：行记录
    正文字段全文（clean 后）；data/cid：页级 Inputs 与 cid（运行时子记录索引）；
    boss_skill_refs：行记录（或 charainfo 同文 pattern 记录）的 links 槽位引用。

    结果 dict：kind='promote'（answers/summary_reason/extra_reasons 等）或 'hint'（reasons）。
    """
    if data is None or cid is None or table not in TABLES or not isinstance(record, dict):
        return None
    template = _norm_text(frag)
    if _family_of(template) != FAM1:
        return None
    subject = '味方全体'
    attrs = list(dict.fromkeys(a for a in _ATTR_DETECT if a in template))
    has_crit = any(a.startswith('クリティカル') for a in attrs)
    noncrit = [a for a in attrs if a in ATTR_PARAM]
    unmapped = [a for a in attrs if not a.startswith('クリティカル') and a not in ATTR_PARAM]

    # --- 句位/段位/句序/同文次数（◆ 段口径复用 type8 helpers；同文计数=审计 same_in_ctx 口径） ----
    # B6-RV-04：◆ 段全为 (1,1) 不传达句位——补「。」句序（第 N 句／共 M 句）逐行披露。
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    starts = TYPE8._occurrences(wb, frag) if wb else []
    section_no = TYPE8._section_no(wb, starts[0])[0] if starts else None
    section_count = TYPE8._section_count(wb) if wb else None
    _sents = re.findall(r'[^。]*。', wb)
    sent_no = next((i + 1 for i, s in enumerate(_sents) if frag.strip() in s), None)
    sent_total = len(_sents)
    same_count = (text or '').count(frag.strip())

    ctx = _page_ctx(data, cid)
    reasons = []
    if table == 'charainfo':
        # G5：同页同文 bosspattern 记录须唯一（audit part4 同法：片段逐字相等）
        matched = [(e, frags) for e, frags in ctx['pattern_frags'] if frag in frags]
        pat_ids = {(str(e.get('reference_id')), e.get('layer')) for e, _ in matched}
        if not matched:
            return dict(kind='hint', reasons=['charainfo 行：同页无同文 bosspattern 行，pattern 链不可达'],
                        subject=subject, attrs=attrs, table=table, section_no=section_no,
                        section_count=section_count)
        if len(pat_ids) > 1:
            return dict(kind='hint', subject=subject, attrs=attrs, table=table,
                        section_no=section_no, section_count=section_count,
                        reasons=['charainfo 行：同文对应 %d 个 pattern 记录（%s），t13 归属歧义'
                                 % (len(pat_ids), ','.join(sorted(p[0] for p in pat_ids))[:60])])
        pe = matched[0][0]
        pattern_rec_key = f"bosspattern|{pe.get('reference_id')}|{pe.get('layer')}"
        prek = ('bosspattern', str(pe.get('reference_id')), pe.get('layer'))
        parent = ctx['rec_index'].get(prek)
        if parent is None:
            return dict(kind='hint', subject=subject, attrs=attrs, table=table,
                        section_no=section_no, section_count=section_count,
                        reasons=['charainfo 经同页同文行（%s）：父记录未定位' % pattern_rec_key])
        ptext = (pe.get('record') or {}).get('sinfo', '') or ''
        ptext = str(ptext).replace('\\n', '\n')
        pattern_same = ptext.count(frag.strip())
        pcut = ptext.find('[i][c]')
        pwb = ptext[:pcut] if pcut >= 0 else ptext
        sub_reasons, child = _gate_parent(parent, attrs, has_crit, pattern_same,
                                          ctx['fam_counts'].get(prek, collections.Counter()),
                                          _competing_ally_buffs(pwb, noncrit))
        if child is None:
            return dict(kind='hint', subject=subject, attrs=attrs, table=table,
                        section_no=section_no, section_count=section_count,
                        reasons=['charainfo 经同页同文行（%s）：%s' % (pattern_rec_key, '；'.join(sub_reasons))])
        via = 'charainfo_via_pattern'
        via_desc = ('经同页同文 bosspattern 记录（%s）的 type13 子记录；charainfo 行自身 '
                    'skillparam* 为 skillid[0] 匹配 boss 技能（伤害侧）的未执行副本，不消费'
                    % pattern_rec_key)
        result = _promote(frag, table, layer, record_id, text, body, subject, attrs,
                          section_no, section_count, pattern_rec_key, 'bosspattern',
                          pe.get('reference_id'), pe.get('layer'), child, via, via_desc,
                          pattern_rec_key, pe.get('boss_skill_refs'), sent_no, sent_total)
        return result

    # 直接行：父记录＝行记录自身（bosspattern/denju/dlb/heroicskilllist）
    rek = (table, str(record_id), layer)
    parent = ctx['rec_index'].get(rek)
    via_desc = '行记录自身的 type13 子记录（bosspattern/denju/dlb 链已由 links/profiles 解析）'
    if parent is None:
        reasons.append('父记录未定位')
    else:
        sub_reasons, child = _gate_parent(parent, attrs, has_crit, same_count,
                                          ctx['fam_counts'].get(rek, collections.Counter()),
                                          _competing_ally_buffs(wb, noncrit))
        if child is not None:
            if unmapped:
                reasons.append('句含无映射属性（%s），bossskill|13 无对应已确认规则'
                               % '、'.join(unmapped))
            else:
                return _promote(frag, table, layer, record_id, text, body, subject, attrs,
                                section_no, section_count, f'{table}|{record_id}|{layer}',
                                table, record_id, layer, child, 'own', via_desc, None,
                                boss_skill_refs, sent_no, sent_total)
        else:
            reasons.extend(sub_reasons)
    if unmapped and not any('无映射属性' in r for r in reasons):
        reasons.append('句含无映射属性（%s），bossskill|13 无对应已确认规则' % '、'.join(unmapped))
    if not reasons:
        reasons.append('本句所有属性均无可推断数值')
    return dict(kind='hint', reasons=reasons, subject=subject, attrs=attrs, table=table,
                section_no=section_no, section_count=section_count)
