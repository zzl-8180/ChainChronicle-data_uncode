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
import struct
import unicodedata
from pathlib import Path

import common as C
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


# ---- R1 整改（20261023）：HP 条件分支保留（空 sinfo 不排除）--------------------------------
# 缺陷与依据：独立复审 independent_20261023_goal_recheck §R1＋b17_final_supplement §R1补充
# ——空 sinfo 的 pattern 不是「无执行分支」：bosspattern 记录自带 hpstart/hpend 档位字段，
# 各档位可引用不同 type13 子记录（值可不同）。非空 sinfo 唯一命中／同文 pattern 唯一匹配
# 把多档位收敛成单档无条件值行＝适用范围/完整性缺陷（10210/2320 denju f1＋skilltext f1）。
# 处置：源记录引用 ≥2 个 pattern 且 hpstart/hpend 分成多个档位条件组时，逐档位出值行
# （condition_label＝原值逐字拼接，如「HP 51–100%」）；同一档位内多个 pattern 值签名一致→
# 单组值（同值兜底逐字披露）；同一档位内值签名不同且无文本对应→该档位具体待办（不猜）。
# HP 边界运行时语义（开闭区间/取整/百分比口径）未核实——标签保留原值＋推断档＋待核查
# 注记，不给无条件结论；描述后续句「…残りHP量に応じて変化する」为前句增益答案的共享
# 条件引用（前句不缺条件单独结清）。
HP_VAR_MARK = '残りHP量に応じて変化'
HP_BOUNDARY_NOTE = ('HP 档位边界运行时语义（开闭区间/取整/百分比口径）未核实——条件标签为'
                    '原始 hpstart/hpend 值逐字拼接（「%」为剩余HP百分比口径的描述性标注），'
                    '不并入数值换算、不升确认；如与实机不符以原值复核（待核查）')
_R1_BRANCH_NOTE = ('HP 条件分支保留（R1 整改，20261023）：源记录引用的全部 pattern（含空 '
                   'sinfo 分支——空文字不等于无执行分支）按 hpstart/hpend 分档；各档位 '
                   'type13 值逐项绑定该分支条件出值行，不合并不平均不选代表值')


def hp_cond_label(hpstart, hpend):
    """档位条件标签（原值逐字；字段缺失以「?」占位——缺失不补值，与 0 区分）。"""
    return 'HP %s–%s%%' % ('?' if hpstart is None else hpstart,
                           '?' if hpend is None else hpend)


def hp_var_in(text):
    return HP_VAR_MARK in (text or '')


def hp_var_sentence(text):
    """「随HP变化」句原文（共享条件引用的逐字出处；无则 None）。"""
    for s in re.findall(r'[^。]*。', text or ''):
        if HP_VAR_MARK in s:
            return s
    return None


def _f32(x):
    return struct.unpack('f', struct.pack('f', float(x)))[0]


def _t13_sig(child):
    """children 格式 t13 记录 → (p1,p2,p3,p6) float32 值签名（表示差不记为值差）。"""
    vals = []
    for q in ('skillparam1', 'skillparam2', 'skillparam3', 'skillparam6'):
        raw = _raw_of(child, q)
        vals.append(_f32(raw) if _num(raw) else raw)
    return tuple(vals)


_BOSS_INFO = {}


def _boss_index(table, layer):
    """bosspattern/bossskill 按 ID 索引（layer 分源取值，不跨层合并；common.Tables 同源文件，
    均在 card_page_dependencies.data_paths 声明清单内）。"""
    key = (table, layer)
    if key not in _BOSS_INFO:
        t = C.Tables()(table)
        _BOSS_INFO[key] = dict(t.cache) if layer == 'CACHE' else dict(t.apk)
    return _BOSS_INFO[key]


def pattern_record_of(pid, prefer_layer=None):
    """pattern 记录定位：优先调用方登记层，否则 common.Tables 语义（CACHE 优先、APK 回退）。
    返回 (record|None, layer|None)。同号跨层不合并——实际解析层随返回值逐字登记。"""
    if prefer_layer is not None:
        rows = _boss_index('bosspattern', prefer_layer).get(pid)
        if rows:
            return rows[0], prefer_layer
    rows = _boss_index('bosspattern', 'CACHE').get(pid)
    if rows:
        return rows[0], 'CACHE'
    rows = _boss_index('bosspattern', 'APK').get(pid)
    return (rows[0], 'APK') if rows else (None, None)


def _pattern_t13_sids(prec, layer):
    """pattern 原始记录 skillidX 槽 → [(skillid, layer)]（仅 type13 载体；layer 同 pattern 层）。"""
    out = []
    for j in range(8):
        sid = (prec or {}).get(f'skillid{j}')
        if not sid:
            continue
        rows = _boss_index('bossskill', layer).get(sid)
        s = rows[0] if rows else None
        if s and s.get('skillid0') == 13:
            out.append((sid, layer))
    return out


def build_hp_branches(refs, t13_pool, sinfo_hit_pid=None):
    """把源记录全部 pattern 引用（含空 sinfo）整理成 HP 档位条件组。

    refs：[(slot, pid, layer, pattern_raw_record|None)]（slot 序）；
    t13_pool：{child_key: children 格式 t13 记录}（父记录/页记录 children 的并集——逐分支
    按 pattern skillidX 对号入座，不在池中的分支记具体待办，不静默丢弃）；
    sinfo_hit_pid：sinfo 含本行片段的 pattern id（可为 None——多档位下文本命中只用于同档位
    异值时的对号，不再作排除依据）。
    返回 (groups, all_sigs)：
      groups＝[dict(cond,label,members,child,child_key,sig,peers,fail)]（cond 首次出现序）；
      all_sigs＝全部分支值签名集合（调用方判定是否多档位）。
    """
    branches = []
    for slot, pid, layer, prec in refs:
        if prec is None:
            branches.append(dict(slot=slot, pid=pid, layer=layer, cond=None, label=None,
                                 t13s=[], fail=f'pattern 记录未定位（bosspattern|{pid}）'))
            continue
        cond = (prec.get('hpstart'), prec.get('hpend'))
        t13s = []
        for sid, sid_layer in _pattern_t13_sids(prec, layer):
            child_key = f'bossskill|{sid}|{sid_layer}'
            child = t13_pool.get(child_key)
            t13s.append(dict(sid=sid, layer=sid_layer, child_key=child_key, child=child,
                             sig=_t13_sig(child) if child is not None else None))
        branches.append(dict(slot=slot, pid=pid, layer=layer, cond=cond,
                             label=hp_cond_label(*cond), t13s=t13s, fail=None))
    groups = []
    for b in branches:
        g = next((g for g in groups if g['cond'] == b['cond']), None)
        if g is None:
            g = dict(cond=b['cond'], label=b['label'], members=[], t13s=[])
            groups.append(g)
        g['members'].append(b)
        g['t13s'].extend(b['t13s'])
    for g in groups:
        g['sigs'] = {t['sig'] for t in g['t13s'] if t['sig'] is not None}
        g['child'] = g['child_key'] = g['sig'] = None
        g['peers'] = []
        g['fail'] = None
        if any(m.get('fail') for m in g['members']) and not g['t13s']:
            g['fail'] = '；'.join(m['fail'] for m in g['members'] if m.get('fail'))
            continue
        if not g['t13s']:
            g['fail'] = '该 HP 档位引用的 pattern 无 type13 子记录（链上类型非 13 或 skillid 缺失）'
            continue
        if len(g['sigs']) > 1:
            # 同档位多值：sinfo 文本命中可对号时取命中分支（与现行单命中同据）；
            # 否则无文本区分——该档位不猜，记具体待办。
            hit = next((t for m in g['members'] if m['pid'] == sinfo_hit_pid
                        for t in m['t13s']), None)
            if hit is not None and hit['sig'] is not None:
                g['child'], g['child_key'], g['sig'] = hit['child'], hit['child_key'], hit['sig']
                others = [t for t in g['t13s'] if t is not hit]
                g['peers'] = [(t['child_key'], t['sig']) for t in others]
                g['fail'] = ('同 HP 档位内其他 pattern 槽值不同（%s）——本档位值取 sinfo 文本命中'
                             '分支（%s），其余选取维度（突破档/优先级等）未解析，记待核查'
                             % ('；'.join(f'{k}={s}' for k, s in g['peers']), hit['child_key']))
            else:
                g['fail'] = ('同一 HP 档位内 %d 个 type13 值签名不同（%s）且无 sinfo 文本对应'
                             '——归属歧义，不猜' % (len(g['sigs']),
                                                   '；'.join(f'{t["child_key"]}={t["sig"]}'
                                                            for t in g['t13s'])))
            continue
        t = g['t13s'][0]
        if t['child'] is None:
            g['fail'] = (f'档位 t13（{t["child_key"]}）不在父记录 children（链未解析）——具体待办，'
                         '不静默取值')
            continue
        g['child'], g['child_key'], g['sig'] = t['child'], t['child_key'], t['sig']
        g['peers'] = [(t2['child_key'], t2['sig']) for t2 in g['t13s'][1:]]
    all_sigs = {t['sig'] for g in groups for t in g['t13s'] if t['sig'] is not None}
    return groups, all_sigs


def hp_branch_note_of(label, cond, members, peers, shared_cond_text,
                      gains_uniform=None):
    """档位条件注记（b6/b17 分支值行共用；原值逐字＋边界待核查＋共享条件引用）。

    gains_uniform（R1-Low 复审整改 20261023）：全档位增益 t13 值签名是否一致（True/False/
    None＝未判定）。共享 HP 变化句以「ダメージ量」开头时（原文 HP 变化句的句面对象是
    ダメージ量，非增益）：增益值各档同值→注记明确「增益值不随 HP 变化、HP 档位标签为
    源记录分支结构标签（保守归因披露）」——不再写「本行增益答案受…约束」（复审
    R1-20332-BUFF-HP-LABEL：该表述把增益过度归因于 HP 条件）；增益各档不同值→维持
    「受…约束」表述（此时增益确随 HP 档位分支取值）。"""
    miss = ('；hpstart 字段缺失于该层 pattern 记录（缺失不补值，与 0 区分）'
            if cond[0] is None else '')
    member_desc = '、'.join(f'{m["slot"]}＝bosspattern|{m["pid"]}|{m["layer"]}'
                            for m in members)
    peer_desc = ('；同档位其他 pattern 引用（' + '；'.join(str(k) for k, _ in peers)
                 + '）与本档位取值 t13 逐槽同值（兜底披露，不合并不跨记录取值）' if peers else '')
    if shared_cond_text and shared_cond_text.startswith('ダメージ量') and gains_uniform:
        shared = ('；源记录 HP 变化句「%s」的句面对象是ダメージ量（伤害子句），原文未把增益'
                  '表述为随 HP 变化；本行增益 t13 各 HP 档位逐槽同值，增益值不随 HP 变化——'
                  '本行 HP 档位标签为源记录分支结构标签（保守归因披露：增益与该 HP 句无已'
                  '确认关联，标签仅标注取值所在分支，不把增益解读为 HP 相关）'
                  % shared_cond_text)
    elif shared_cond_text:
        shared = ('；本行增益答案受同描述后续句「%s」约束（共享条件引用——增益值按 HP 档位分支'
                  '绑定，前句不缺条件单独结清）' % shared_cond_text)
    else:
        shared = ('；源记录引用多 HP 档位 pattern（本描述文本未写 HP 变化句；档位条件来自'
                  '源记录分支结构，逐字披露）')
    return (f'HP 档位条件：{label}（本档位 pattern 引用：{member_desc}，'
            f'hpstart={cond[0]}／hpend={cond[1]} 原值逐字{miss}；{HP_BOUNDARY_NOTE}）'
            f'{peer_desc}{shared}；{_R1_BRANCH_NOTE}')


def _branch_value_row(attr, param, raw, child, child_key, chain_desc, slot_desc,
                      sent_no, sent_total, section_no, section_count, label, cond,
                      members, peers, dur=False, shared_cond_text=None,
                      gains_uniform=None):
    """HP 档位分支值行（批 6 值行结构＋档位条件绑定；条件不并入数值换算）。"""
    rule = R.rule_for('bossskill', 13, '/' + param)
    converted = R.answer_for('bossskill', 13, '/' + param, raw, child)
    evidence_dir, evidence_files = _field_evidence(param)
    attr_label = DUR_ATTR if dur else attr
    hp_note = hp_branch_note_of(label, cond, members, peers, shared_cond_text,
                                gains_uniform=gains_uniform)
    note = (
        f'模板批 6 必殺バフ值行（HP 档位分支；来源记录＝{child_key}，{chain_desc}）；'
        f'句中「{attr_label}」→/{param} 1:1 映射；规则键 bossskill|13|/{param}；原值 {raw}；'
        f'方向审核 {_direction_text(param, raw)}；证据目录 {evidence_dir}；'
        f'对象「味方全体」为句面依据，该 type13 处理器的接受者选择逻辑无已确认规则'
        f'（{_iparam_note(child)}）；样本域：{_sample_domain_note(param, rule)}；'
        f'{slot_desc}；{hp_note}'
        + (f'；正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）'
           if sent_no else '；正文句序未能定位')
        + (f'；◆ 段：第 {section_no}／共 {section_count} 段（◆段口径不传达句序）'
           if section_no else ''))
    return dict(
        value=converted['value_text'],
        quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
        raw_value=raw, field_path='/' + param,
        condition_label=label,
        numeric_source=f'模板推断（批 6 必殺バフ：{chain_desc}）',
        numeric_evidence='推断', association_evidence='推断', evidence_scope=B6_SCOPE,
        rule_key=f'bossskill|13|/{param}',
        rule_body_status=rule.get('status'), rule_status=rule.get('status'),
        conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
        conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
        evidence=list(evidence_files),
        source=dict(table='bossskill', record_id=child.get('record_id'),
                    layer=child.get('layer'), record_key=child_key),
        note=note, quantitative=True)


def promote_hp_branches(frag, table, layer, record_id, subject, attrs, section_no,
                        section_count, via, via_desc, groups, sent_no, sent_total,
                        slot_desc_of, chain_desc_of, shared_cond_text, noncrit,
                        gate_fails=None):
    """HP 档位分支晋级行（b6 路径：charainfo 同文 pattern／denju 直接行；R1 整改）。

    groups：build_hp_branches 产出的档位条件组（含 child/fail/peers）；
    slot_desc_of/chain_desc_of：per 档位回调（group→槽位披露/链描述）；
    gate_fails：行级门失败原因列表（非空→整行 hint，不硬配）。"""
    if gate_fails:
        return dict(kind='hint', hp_branch_mode=True,
                    reasons=['HP 条件分支保留（R1 整改）：行级门未通过——' + '；'.join(gate_fails)])
    labels = [g['label'] for g in groups if g['label']]
    # 增益 t13 各档位是否逐槽同值（R1-Low 整改：HP 变化句对象为ダメージ量时的归因措辞依据）
    _gains_sigs = {g['sig'] for g in groups if g['child'] is not None and g['sig'] is not None}
    gains_uniform = len(_gains_sigs) == 1 if _gains_sigs else None
    answers, claimed = [], set()
    branch_todos = []
    for g in groups:
        if g['fail'] and g['child'] is None:
            branch_todos.append('档位待办（%s，pattern 引用：%s）：%s'
                                % (g['label'],
                                   '、'.join(f'{m["slot"]}＝bosspattern|{m["pid"]}|{m["layer"]}'
                                             for m in g['members']),
                                   g['fail']))
            continue
        child = g['child']
        raws = {q: _raw_of(child, q) for q in
                ('skillparam1', 'skillparam2', 'skillparam6', 'skillparam3')}
        ok = True
        for attr in noncrit:
            param = ATTR_PARAM[attr]
            raw = raws[param]
            if not (_num(raw) and raw != 0):
                branch_todos.append('档位待办（%s）：形状不符（U3）——句主张「%s」但本档位 t13 '
                                    '槽 /%s 不活性（%r）——缺失不补 0'
                                    % (g['label'], attr, param, raw))
                ok = False
                break
        if ok and not (_num(raws[DUR_PARAM]) and raws[DUR_PARAM] != 0):
            branch_todos.append('档位待办（%s）：持续时间槽 skillparam3 无非零值（%r）'
                                % (g['label'], raws[DUR_PARAM]))
            ok = False
        if not ok:
            continue
        for attr in noncrit:
            param = ATTR_PARAM[attr]
            claimed.add(param)
            answers.append(_branch_value_row(
                attr, param, raws[param], child, g['child_key'],
                chain_desc_of(g), slot_desc_of(g), sent_no, sent_total, section_no,
                section_count, g['label'], g['cond'], g['members'], g['peers'],
                shared_cond_text=shared_cond_text, gains_uniform=gains_uniform))
        claimed.add(DUR_PARAM)
        # R1-Low 复验整改（20261023，recheck R1-LOW-ATTRIBUTION-RESIDUAL）：时长槽
        # /skillparam3 分支值行同样传入 gains_uniform——HP 变化句句面对象为ダメージ量且
        # 各档 t13 逐槽同值时，时长行与 p1/p2/p6 增益行共用精确化归因口径（不再保留
        # 「本行增益答案受…约束」旧措辞——时长值不是增益、且各档 t13 逐槽同值含时长槽，
        # 时长取值确不随 HP 档位变化）。
        answers.append(_branch_value_row(
            None, DUR_PARAM, raws[DUR_PARAM], child, g['child_key'],
            chain_desc_of(g), slot_desc_of(g), sent_no, sent_total, section_no,
            section_count, g['label'], g['cond'], g['members'], g['peers'], dur=True,
            shared_cond_text=shared_cond_text, gains_uniform=gains_uniform))
    if not answers:
        return dict(kind='hint', hp_branch_mode=True,
                    reasons=(branch_todos or ['HP 条件分支保留（R1 整改）：无档位可出值']))
    extra = ['%s——源记录引用 %d 个 pattern、分 %d 个 HP 档位条件组（%s）；值行全部「推断」，'
             '不升「确认」，不进入整行确认' % (_R1_BRANCH_NOTE, sum(len(g['members']) for g in groups),
                                              len(groups), '、'.join(labels))]
    extra += branch_todos
    for g in groups:
        if g['child'] is not None and g['peers']:
            extra.append('档位 %s 同值兜底披露：本档位取值＝%s；其余 pattern 引用 t13 %s'
                         % (g['label'], g['child_key'],
                            '；'.join(f'{k}（值签名 {s}）' for k, s in g['peers'])))
    unclaimed = []
    for g in groups:
        if g['child'] is None:
            continue
        for u in (g['child'].get('answers') or []) + (g['child'].get('unexplained') or []):
            f = u.get('f') or ''
            m = re.fullmatch(r'/(param\d+|iParam\d+|iparam\d+|skillparam\d+|skillflag\d+|flag\d+_?\d*)', f)
            if not m or m.group(1) in claimed:
                continue
            unclaimed.append(f'[{g["label"]}] {f}={u.get("raw")!r}'
                             + ('（原值 0，未被本句主张）' if u.get('raw') == 0 else ''))
    if unclaimed:
        extra.append('t13 子记录句外槽未分配（不归属本句，仅登记原值；按档位分组）：'
                     + '、'.join(dict.fromkeys(unclaimed)))
    summary = (B6_TAG + '（HP 条件分支，R1 整改）：值行来源＝' + via_desc
               + '；按源记录全部 pattern 引用分 %d 个 HP 档位条件组（%s）逐档出值；'
                 '空 sinfo 分支不排除；HP 边界运行时语义待核查（原值保留＋推断档）；'
                 '值行全部「推断」，不升「确认」，不进入整行确认。' % (len(groups), '、'.join(labels))
               + '；'.join(extra))
    return dict(kind='promote', hp_branch_mode=True, answers=answers,
                summary_reason=summary, extra_reasons=extra,
                hp_branch_conditions=labels,
                hp_branch_conditions_expected=labels,
                subject=subject, attrs=list(attrs), table=table,
                parent_record_id=record_id, parent_table=table, parent_layer=layer,
                chain_record_id=next((g['child'].get('record_id') for g in groups
                                      if g['child'] is not None), None),
                chain_layer=next((g['child'].get('layer') for g in groups
                                  if g['child'] is not None), None),
                chain_slot=None, via=via, pattern_record_id=None,
                section_no=section_no, section_count=section_count,
                sent_no=sent_no, sent_total=sent_total)


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


def _member_of(groups, child_key):
    """取值 t13 所在的 pattern 引用成员（全组搜索；仅诊断用途）。"""
    for g in groups:
        for m in g['members']:
            for t in m['t13s']:
                if t['child_key'] == child_key:
                    return g, m
    return None, None


def _member_in_group(g, child_key, prefer_pid=None):
    """本档位（group）内取值 t13 的 pattern 引用成员（R1-Medium 复审整改 20261023）。

    缺陷与依据：复审 recheck_rectification_20261023_deepseek R1-20332-PARENT-PROVENANCE
    ——同值 t13 可被多个 HP 档位的 pattern 引用（如 20332 四档均引 bossskill|42033206），
    ``_member_of``（全组搜索）恒返回首档 pattern（patternid0/pattern0），致 12/16 答案的
    numeric_source 父链与 condition_label 矛盾。修复：父链/槽位披露只在**本档位成员**内
    对号；同档位内优先 sinfo 文本命中成员（prefer_pid），否则取引用序首个含该 t13 的成员。
    """
    hit = None
    for m in g['members']:
        if prefer_pid is not None and m['pid'] == prefer_pid and \
                any(t['child_key'] == child_key for t in m['t13s']):
            hit = m
            break
    if hit is None:
        hit = next((m for m in g['members']
                    if any(t['child_key'] == child_key for t in m['t13s'])), None)
    return hit


def _charainfo_hp_branches(ctx, data, cid, layer, frag, attrs, noncrit, pe,
                           section_no, section_count, sent_no, sent_total, body):
    """charainfo 行 HP 档位分支路径（R1 整改）。非多档位返回 None（走原单档路径）。"""
    full = (data.apk_chara if layer == 'APK' else data.cache_chara).get(cid)
    if full is None:
        return None
    refs = []
    for i in range(9):
        pid = full.get(f'pattern{i}')
        if not pid:
            continue
        prec, lay2 = pattern_record_of(pid)
        refs.append((f'pattern{i}', pid, lay2, prec))
    if len(refs) <= 1:
        return None
    conds = {(p.get('hpstart'), p.get('hpend')) for _, _, _, p in refs if p is not None}
    if len(conds) <= 1:
        return None
    # t13 池：同页 pattern 页记录 children（children 格式，含 answers/unexplained 披露）
    pool, pe_by_pid = {}, {}
    for e, _fs in ctx['pattern_frags']:
        pe_by_pid.setdefault(e.get('reference_id'), e)
        pk = ('bosspattern', str(e.get('reference_id')), e.get('layer'))
        parent = ctx['rec_index'].get(pk)
        for c in (parent or {}).get('children') or []:
            if c.get('table') == 'bossskill' and c.get('effect_type') == 13:
                pool[f'bossskill|{c.get("record_id")}|{c.get("layer")}'] = c
    groups, _sigs = build_hp_branches(refs, pool, sinfo_hit_pid=pe.get('reference_id'))

    def slot_desc_of(g):
        # R1-Medium 复审整改 20261023：只在本档位成员内对号（同值 t13 跨档引用时不得固定首档）
        m = _member_in_group(g, g['child_key'], prefer_pid=pe.get('reference_id'))
        pid_m = m['pid'] if m else None
        slot = None
        for r in (pe_by_pid.get(pid_m) or {}).get('boss_skill_refs') or []:
            if r.get('table') == 'bossskill' and \
                    str(r.get('reference_id')) == str(g['child'].get('record_id')):
                slot = r.get('slot')
                break
        slot_src = 'links'
        if slot is None and pid_m is not None:
            # links boss_skill_refs 按子记录去重（同 t13 跨 pattern 只登记首 pattern 的
            # reference_field）——槽位回退读 pattern 原始记录 skillidX（数据侧事实）
            prec_m, lay_m = pattern_record_of(pid_m)
            fb = next((f'skillid{j}' for j in range(8)
                       if str((prec_m or {}).get(f'skillid{j}'))
                       == str(g['child'].get('record_id'))), None)
            if fb:
                slot, slot_src = fb, 'pattern_record'
        return (f'bossskill 子记录经 pattern 记录（bosspattern|{pid_m}）boss_skill_refs '
                f'槽位 {slot} 引用（records.jsonl children 未存 slot，槽位取自 links 现产物）'
                if slot_src == 'links' and slot else
                (f'bossskill 子记录经 pattern 记录（bosspattern|{pid_m}）的 {slot} 槽引用'
                 '（links boss_skill_refs 该 pattern 未单独登记——登记按子记录去重；'
                 '槽位读自 pattern 原始记录）' if slot else
                 'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）'))

    def chain_desc_of(g):
        m = _member_in_group(g, g['child_key'], prefer_pid=pe.get('reference_id'))
        slot = m['slot'] if m else '?'
        pid_m = m['pid'] if m else '?'
        lay_m = m['layer'] if m else '?'
        return (f'charainfo|{cid}|{layer}→{slot}→bosspattern|{pid_m}|{lay_m}→{g["child_key"]}'
                '（charainfo 行自身 skillparam* 为伤害侧未执行副本，不消费）')

    return promote_hp_branches(
        frag, 'charainfo', layer, cid, '味方全体', attrs, section_no, section_count,
        'charainfo_via_pattern', f'charainfo|{cid}|{layer}→全部 pattern 引用分档',
        groups, sent_no, sent_total, slot_desc_of, chain_desc_of,
        hp_var_sentence(body), noncrit)


def _denju_hp_branches(record, text, table, layer, record_id, attrs, noncrit,
                       section_no, section_count, sent_no, sent_total,
                       boss_skill_refs, ctx, frag):
    """denju 直接行 HP 档位分支路径（R1 整改；children 按 links 去重后单 t13 的多 pattern
    denju——如 20332）。非多档位返回 None（走原单档路径）。"""
    refs = []
    for i in range(9):
        pid = (record or {}).get(f'patternid{i}')
        if not pid:
            continue
        prec, lay2 = pattern_record_of(pid)
        refs.append((f'patternid{i}', pid, lay2, prec))
    if len(refs) <= 1:
        return None
    conds = {(p.get('hpstart'), p.get('hpend')) for _, _, _, p in refs if p is not None}
    if len(conds) <= 1:
        return None
    hits = [pid for slot, pid, lay2, p in refs
            if p is not None and frag in {sp['japanese'] for sp in fragment_positions(
                str(p.get('sinfo') or '').replace('\\n', '\n'))}]
    pool = {}
    parent = ctx['rec_index'].get((table, str(record_id), layer))
    for c in (parent or {}).get('children') or []:
        if c.get('table') == 'bossskill' and c.get('effect_type') == 13:
            pool[f'bossskill|{c.get("record_id")}|{c.get("layer")}'] = c
    groups, _sigs = build_hp_branches(refs, pool, sinfo_hit_pid=hits[0] if len(hits) == 1 else None)

    def slot_desc_of(g):
        # R1-Medium 复审整改 20261023：只在本档位成员内对号（同值 t13 跨档引用时不得固定首档）
        m = _member_in_group(g, g['child_key'], prefer_pid=hits[0] if len(hits) == 1 else None)
        pid_m = m['pid'] if m else None
        lay_m = m['layer'] if m else None
        slot = None
        for r in boss_skill_refs or []:
            if r.get('table') == 'bossskill' and \
                    str(r.get('reference_id')) == str(g['child'].get('record_id')) and \
                    str(r.get('reference_field') or '').startswith(f'bosspattern[{pid_m}].'):
                slot = r.get('slot')
                break
        if slot is None and pid_m is not None:
            # links boss_skill_refs 按子记录去重（同 t13 跨 pattern 只登记首 pattern 的
            # reference_field，如 20332 的 bossskill|42033206 仅登记于 bosspattern[42033210]）
            # ——槽位回退读本档 pattern 原始记录 skillidX（数据侧事实，非顺序推断）。
            prec_m, _ = pattern_record_of(pid_m, prefer_layer=lay_m)
            slot = next((f'skillid{j}' for j in range(8)
                         if str((prec_m or {}).get(f'skillid{j}'))
                         == str(g['child'].get('record_id'))), None)
            return (f'bossskill 子记录经 pattern 记录（bosspattern|{pid_m}|{lay_m}）的 '
                    f'{slot} 槽引用（links boss_skill_refs 该 pattern 未单独登记——登记按'
                    '子记录去重；槽位读自 pattern 原始记录）' if slot else
                    'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）')
        return (f'bossskill 子记录经父记录 boss_skill_refs reference_field'
                f'「bosspattern[{pid_m}].{slot}」引用' if slot else
                'links boss_skill_refs 未登记该子记录槽位（如实登记，不以顺序推断）')

    def chain_desc_of(g):
        m = _member_in_group(g, g['child_key'], prefer_pid=hits[0] if len(hits) == 1 else None)
        slot = m['slot'] if m else '?'
        pid_m = m['pid'] if m else '?'
        lay_m = m['layer'] if m else '?'
        return f'denju|{record_id}|{layer}→{slot}→bosspattern|{pid_m}|{lay_m}→{g["child_key"]}'

    return promote_hp_branches(
        frag, table, layer, record_id, '味方全体', attrs, section_no, section_count,
        'own', f'denju|{record_id}|{layer}→全部 patternid 引用分档',
        groups, sent_no, sent_total, slot_desc_of, chain_desc_of,
        hp_var_sentence(text), noncrit)


# ---- R1-High 复审整改（20261023）：same_cond_diff_vals 产品层披露 ---------------------------
# 缺陷与依据：复审 recheck_rectification_20261023_deepseek R1-SAME-COND-DISCLOSURE——
# 同一 HP 条件组内多 pattern 引用不同 t13 值签名的行（230 行），现行取 sinfo 文本命中分支
# 出值，其余 pattern→t13 的原值只在筛查工作文件（r1_screen.json）有，产品层（row JSON）
# 219/230 行至少缺一个其余 t13 id——处置表所称「他 pattern 异值兜底披露」未落地。
# 修复口径（按审查 action，不硬猜归属）：晋级行/C 行的 row JSON 增加逐分支披露（其余
# pattern→t13 记录键＋p1/p2/p3/p6 槽值原值逐字＋与本行取值同/异）＋「同 HP 条件组、
# 选取维度（突破档/优先级）未解析」待办说明；异值行由账本 S7_same_cond_alt_t13 入
# backlog 具体项（缺口/已有证据/下一步）。值行数值/归属零变化。
SAME_COND_TAG = '同 HP 条件组其余 pattern→t13 分支披露（R1-High 复审整改，20261023）'
_SAME_COND_TODO = ('同 HP 条件组、选取维度（突破档/优先级/条件句↔pattern 对应）未解析'
                   '——异值不并入本行值行、不猜测归属（待办见账本 S7_same_cond_alt_t13：'
                   '缺口/已有证据/下一步）')


def _t13_raws(child):
    return {q: _raw_of(child, q) for q in ('skillparam1', 'skillparam2', 'skillparam3',
                                           'skillparam6')}


def row_same_cond_disclosure(record, table, layer, record_id, data, cid,
                             selected_key=None):
    """源记录 pattern 引用中「同一 HP 条件组内与本行取值 t13 值签名不同」的其余分支清单。

    table∈{charainfo,denju}：charainfo 行源记录＝本层完整记录（patternN）；denju 行＝行
    记录自身（patternidN）。selected_key＝本行取值 t13 记录键（晋级行传 chain_key；未
    晋级 C 行传 None——此时全部 t13 均列为待归属分支）。
    返回 None（不适用：引用≤1/多档位分支（已有逐档值行）/记录缺失）或
    dict(text=行注记文本, structured=结构化披露, has_diff=bool)。
    同号跨层不合并：pattern/bossskill 按实际解析层逐字登记；t13 不在链池→登记链缺口。
    """
    if table == 'charainfo':
        full = (data.apk_chara if layer == 'APK' else data.cache_chara).get(cid)
        flds = [f'pattern{i}' for i in range(9)]
    elif table == 'denju':
        full = record
        flds = [f'patternid{i}' for i in range(9)]
    else:
        return None
    if not isinstance(full, dict):
        return None
    refs = []
    for fld in flds:
        pid = full.get(fld)
        if not pid:
            continue
        prec, lay2 = pattern_record_of(pid)
        refs.append((fld, pid, lay2, prec))
    if len(refs) <= 1:
        return None
    conds = {(p.get('hpstart'), p.get('hpend')) for _, _, _, p in refs if p is not None}
    if len(conds) > 1:
        return None  # 多档位分支行：逐档值行已绑定各档 t13（不属 same_cond 口径）
    ctx = _page_ctx(data, cid)
    pool = {}
    if table == 'charainfo':
        for e, _fs in ctx['pattern_frags']:
            pk = ('bosspattern', str(e.get('reference_id')), e.get('layer'))
            for c in ((ctx['rec_index'].get(pk) or {}).get('children') or []):
                if c.get('table') == 'bossskill' and c.get('effect_type') == 13:
                    pool[f'bossskill|{c.get("record_id")}|{c.get("layer")}'] = c
    else:
        parent = ctx['rec_index'].get((table, str(record_id), layer))
        for c in (parent or {}).get('children') or []:
            if c.get('table') == 'bossskill' and c.get('effect_type') == 13:
                pool[f'bossskill|{c.get("record_id")}|{c.get("layer")}'] = c
    branches, sel_sig = [], None
    for fld, pid, lay2, prec in refs:
        if prec is None:
            branches.append(dict(slot=fld, pid=pid, layer=lay2, cond_label=None,
                                 t13_key=None, sig=None, raws=None, sinfo_empty=None,
                                 unresolved='pattern 记录未定位（bosspattern|%s）' % pid))
            continue
        cond = (prec.get('hpstart'), prec.get('hpend'))
        lab = hp_cond_label(*cond)
        sinfo_empty = not str(prec.get('sinfo') or '').replace('\\n', '\n')
        for sid, sid_lay in _pattern_t13_sids(prec, lay2):
            ck = f'bossskill|{sid}|{sid_lay}'
            if selected_key is not None and ck == selected_key:
                child = pool.get(ck)
                sel_sig = _t13_sig(child) if child is not None else None
                continue
            child = pool.get(ck)
            branches.append(dict(slot=fld, pid=pid, layer=lay2, cond_label=lab,
                                 t13_key=ck,
                                 sig=_t13_sig(child) if child is not None else None,
                                 raws=_t13_raws(child) if child is not None else None,
                                 sinfo_empty=sinfo_empty, unresolved=None))
    if not branches:
        return None
    # 仅「同一 HP 条件组内值签名≥2 个」需要披露（单值 multi-ref 行＝single_class，维持现行）
    all_sigs = ({b['sig'] for b in branches if b['sig'] is not None}
                | ({sel_sig} if sel_sig is not None else set()))
    if len(all_sigs) <= 1:
        return None
    has_diff = True
    cond0 = next(iter(conds)) if conds else None
    cond_txt = ('全部分支 hpstart/hpend＝%s/%s（同一 HP 条件组）'
                % ('?' if cond0[0] is None else cond0[0],
                   '?' if cond0[1] is None else cond0[1]) if cond0 else
                'pattern 档位字段未定位')
    parts = []
    for b in branches:
        if b['unresolved']:
            parts.append(f'{b["slot"]}＝bosspattern|{b["pid"]}|{b["layer"]}→{b["unresolved"]}')
            continue
        if b['sig'] is None:
            parts.append(f'{b["slot"]}＝bosspattern|{b["pid"]}|{b["layer"]}（{b["cond_label"]}；'
                         f'sinfo {"空" if b["sinfo_empty"] else "有正文"}）→{b["t13_key"]}'
                         '（t13 未在链上解析——链缺口待办）')
            continue
        same = (sel_sig is not None and b['sig'] == sel_sig)
        eq_txt = ('与本行取值 t13 逐槽同值' if same
                  else ('未归属（本行未取值）' if sel_sig is None
                        else '与本行取值 t13 槽值不同'))
        rws = b['raws']
        parts.append(f'{b["slot"]}＝bosspattern|{b["pid"]}|{b["layer"]}（{b["cond_label"]}；'
                     f'sinfo {"空" if b["sinfo_empty"] else "有正文"}）→{b["t13_key"]} '
                     f'槽值 p1={rws["skillparam1"]!r}/p2={rws["skillparam2"]!r}/'
                     f'p3={rws["skillparam3"]!r}/p6={rws["skillparam6"]!r}（原值逐字，'
                     f'{eq_txt}）')
    if selected_key is not None:
        text = (f'{SAME_COND_TAG}：本行取值 t13＝{selected_key}；源记录其余 pattern 引用'
                f'（{cond_txt}）：' + '；'.join(parts) + f'——{_SAME_COND_TODO}')
    else:
        text = (f'{SAME_COND_TAG}（本行未取值，登记待归属分支）：源记录引用 ≥2 个 pattern'
                f'（{cond_txt}），各分支 t13 载体槽值：' + '；'.join(parts) +
                f'——本句主张与这些载体值的字段归属未解析（当前无已确认规则映射本句词形到'
                f'这些槽），{_SAME_COND_TODO}')
    return dict(text=text,
                structured=dict(tag=SAME_COND_TAG, selected_key=selected_key,
                                selected_sig=(list(sel_sig) if isinstance(sel_sig, tuple)
                                              else sel_sig),
                                same_cond=cond_txt, has_diff=has_diff,
                                branches=[{k: (list(b[k]) if k == 'sig' and
                                               isinstance(b[k], tuple) else b[k])
                                           for k in
                                           ('slot', 'pid', 'layer', 'cond_label', 't13_key',
                                            'sig', 'raws', 'sinfo_empty', 'unresolved')}
                                          for b in branches]),
                has_diff=has_diff)


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
        # R1 整改（20261023）：同文 pattern 唯一命中只覆盖有正文的档位——源记录（本层
        # charainfo 完整记录）引用的全部 pattern（含空 sinfo）按 hpstart/hpend 分档；
        # 分成多个档位条件组时逐档出值（空 sinfo 不排除），不收敛到单档无条件值。
        br = _charainfo_hp_branches(ctx, data, cid, layer, frag, attrs, noncrit, pe,
                                    section_no, section_count, sent_no, sent_total,
                                    body)
        if br is not None:
            return br
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
                # R1 整改（20261023）：denju 直接行的 patternidN 引用（含空 sinfo）分成
                # 多个 HP 档位条件组时逐档出值（links children 按 (id,layer) 去重使 G2
                # 只见单 t13 的多 pattern denju——如 20332——同样保留分支条件）。
                if table == 'denju':
                    br = _denju_hp_branches(record, text, table, layer, record_id, attrs,
                                            noncrit, section_no, section_count,
                                            sent_no, sent_total, boss_skill_refs, ctx, frag)
                    if br is not None:
                        return br
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
