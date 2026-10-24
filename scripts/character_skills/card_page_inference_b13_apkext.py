"""模板作用域推断层——批 13：APK 域外扩域（ability99×199／ability2003×148 载体）。

前置与依据（批 13 前置审计
``output/character_skills/inference_inventory/b13_apkext_scope.md``，2026-10-22）：

* rules.json 九键（skilllist|99 四键＋skilllist|2003 五键）样本域已由「仅当前 v3
  CACHE」扩为「CACHE＋APK 主表两域分源」（``rules.py`` ``_b13_apkext_domain_update``；
  单键保留、新增伴生字段 ``occurrences_apk``＝APK 存在数，不拆双键）；APK 99×199／
  2003×148 全量分布 0 方向反例、触发限定词↔阈值组合逐行一致（PROMOTABLE 278 行
  0 违例）；2003 处理器证据已含 APK 记录受控实测（批 10 native_checks 31222712/50009）；
  99 处理器最小新增 2 条 APK 记录受控检查（31020502 全路＋31221605 分数阈值）＋两型
  APK 全域公式核对（99×199×3 路、2003×148×Skill 路，0 失败；
  ``work/character_skills_b13_impl_apkext/``，复用批 9/10 夹具，无新反汇编、未实机）。

本批行集＝批 9 遗留 APK 99 域外 hint 行 **94**（86 晋级＋8 multi-carrier 留守）＋批 10
遗留 APK 2003 域外 hint 行 **192**（全晋级；其中 **63 行跨层**：行在 CACHE 层、载体在
APK 层，按载体层域归类——audit §2.3）。载体层判定规则：行层≠载体层时一律按**载体所在
层**的域取值，不得跨层读取（两域 5＋5 个同号记录参数值不同，命名空间不合并）。

接线（载体域门扩展）：批 9/10 的 APK 域外出口处委托本模块——

* B9.evaluate 的 ``apk99 and not c99`` 分支 → :func:`handle_99_apk`
  （多载体→hint multi-carrier；单载体→P4 形状/P5 方向/P4b 竞争句/P6 守卫→晋级或 hint）；
* B10.evaluate 的 P2 域门（载体层≠CACHE 或不在 CACHE 265 域）→ :func:`handle_2003_apk`
  （P4/P5/P6→晋级或 hint）。

返回 dict 带 ``b13_ext=True`` 标记：promote 由行级键 ``inference_b13`` 登记（批 12
replaces_hint 先例，替换对应 ``inference_b9_hint``/``inference_b10_hint``，不双登记）；
hint（multi-carrier 等）写入 ``inference_b13_hint``。B9/B10 对这些行不再产出旧域外
hint（评估结果整体被本模块结果替代）；其余行（P1 不过、CACHE 载体等）零变化。

门控（逐行重验；与批 9/10 同门同序，仅样本域换为扩后两域）：

* P4 形状（双向）：敵減益半句属性 ⇔ 载体 p7/p8/p9 活性（缺槽＝缺失不补 0）；
* P5 方向（代码语义）：p7/p8≤0（负值加算＝下降）、p9≥0（受伤量加算＝「防御力下がる」
  的表现层口径，不是固定防御减少）；
* P4b 竞争句（批 6 G6 检测扩展）；
* P6 跨 cid 载体竞争守卫（本批进程内登记，键 (层,id)——与批 9/10 的 CACHE 登记
  分开，两域同号 ID 不串）；
* 载体唯一（multi-carrier→hint，双侧值披露；audit §2.3 的 8 行）。

披露（逐行强制）：

* **两层区分**：「规则本体：已确认（静态及受控原生局部规则）——样本域已扩至 CACHE＋APK
  两域分源（批 13 证据见上）」与「本条数值归属＝推断（模板批 13 APK 扩域），不升确认」；
* 层披露：行层与载体层逐行注明（跨层行写明「载体来自 APK 主表、行在 CACHE 层（或反之）；
  按载体所在层域归类取值，不得跨层读取」；APK/APK 行写明两方均在 APK 主表层）；
* APK 特有形态逐行披露：99 分数阈值（p1/p2/p3∉{0,1}，概率值登记不分配）、99 p0=0
  （真实零、语义未核）、2003 p3=0.15（50009，Skill 型着弹 15% 概率触发）、p0 新正值
  （4.5/5/10/15/18/20/25/45/50/90/120，按「正值=游戏秒原样存」口径，未逐值实机核对）；
* 证据按字段（INFR-01）：值行 evidence 取 rules.json 九键的 evidence（与批 9/10 同一套
  目录，存在性检查）；
* 样本域披露按登记口径（INFR-02）：occurrences（CACHE 存在数，不变）＋occurrences_apk
  （APK 存在数）；载体记录未逐条核对，不属逐记录确认。

硬边界：只升「推断」；不进整行确认；APK 装载路径无原生核实，永不据此升「确认」；
批 1–12 行与计数不动（本批只接管批 9/10 的 APK 域外 hint 行）；30236 基线零触碰；
2290 属性门行、b8 crit-2012 域外 184 行、b11/12 1095 域外 39 行不属本批。
"""
from __future__ import annotations

import re

import rules as R
import card_page_inference_b6_bossbuff as B6

B13_TAG = '推断（模板批 13 APK 扩域）'
B13_SCOPE = 'TEMPLATE_BATCH13_APKEXT'
B13_FAMILY = ('敵デバフ家族 APK 扩域（批 13）——skilllist ability99（PowerDrain，APK 主表 '
              '199 条）与 ability2003（SA_PowerDrain，APK 主表 148 条）载体：批 9/10 的 APK '
              '域外 hint 行按载体层域晋级（rules.json 九键样本域扩至 CACHE＋APK 两域分源；'
              '行层≠载体层时按载体层域归类取值，不得跨层读取）')

B9_TABLES = ('skilllist', 'supporterskill')          # 批 9 侧接管行表
B10_TABLES = ('bosspattern', 'denju', 'denju_limit_break_info', 'charainfo')
TABLES = B9_TABLES + B10_TABLES                      # 接线用超集

_EVIDENCE_NOTE_99 = ('批 13 APK 扩域证据（本批写入边界落 work/，未合并 '
                     'output/ordinary_effects/ability99|2003/ 既有 native_checks.json）：'
                     'work/character_skills_b13_impl_apkext/b13_apk_checks_99.json'
                     '（99 处理器 31020502 全路＋31221605 分数阈值 2 条 APK 记录受控检查＋'
                     'APK 199 条×3 路全域公式核对 0 失败）与 b13_apk_checks_2003.json'
                     '（2003 APK 148 条×Skill 路全域公式核对 0 失败）；无新反汇编、未实机')


def _sample_domain_note(rule, param):
    """INFR-02：扩域后单键样本域披露（occurrences CACHE 口径不变＋occurrences_apk）。
    R02 修复（20261022）：同号措辞精确化——真实参数值分歧与缺省/float32 表示差分列，
    明细以 rules.json 九键 conditions 为准。"""
    return (f'该规则登记 occurrences={rule.get("occurrences")}（CACHE 存在数口径，批 13 未改）'
            f'＋occurrences_apk={rule.get("occurrences_apk")}（APK 存在数；origin '
            f'{rule.get("origin")}）；样本域＝两域分源（批 13 扩域：①当前 v3 CACHE 普通 '
            'skilllist 记录；②APK 主表 output/base_master/_mdSkill.json 记录；命名空间不'
            '合并、5 个同号记录中 7 组为两域真实参数值分歧、3 组仅缺省/float32 表示差'
            '（逐组明细见 rules.json 九键 conditions；行侧载体按载体所在层取值不得跨层））；'
            '本行来源载体记录未逐条核对，按规则适用条件披露，不属逐记录确认')


def _sample_domain_summary(et):
    """行级适用范围披露：键级 occurrences＋occurrences_apk 汇总一次（批 10 B10-RV-03 同法）。"""
    params = ('param0', 'param3', 'param7', 'param8', 'param9') if et == 2003 else \
             ('param0', 'param7', 'param8', 'param9')
    occ = '、'.join(
        f'/{p}={R.rule_for("skilllist", et, "/" + p).get("occurrences")}'
        f'+{R.rule_for("skilllist", et, "/" + p).get("occurrences_apk")}' for p in params)
    return ('（键级 occurrences（CACHE）＋occurrences_apk（APK）汇总披露一次；origin '
            f'rules.json 登记值）：{occ}；样本域＝两域分源（批 13 扩域）：CACHE 普通 skilllist '
            f'ability{et} 存在数＋APK 主表 _mdSkill.json ability{et} 存在数，命名空间不合并、'
            '不得跨层取值；本行来源载体记录未逐条核对，按规则适用条件披露，不属逐记录确认')


def _layer_note(row_layer):
    """层披露（逐行强制）：行层与载体层关系＋跨层归类口径。"""
    if row_layer == 'APK':
        return ('层披露：行与载体均在 APK 主表层（行层=APK、载体层=APK；APK 记录来源 '
                'output/base_master/_mdSkill.json）；不与 CACHE 层同号记录（如有）跨层取值')
    return ('跨层披露：载体来自 APK 主表（skilllist|…|APK，output/base_master/_mdSkill.json）、'
            '行在 CACHE 层——按载体所在层（APK）域归类取值（批 13 审计 §2.3），'
            '不与 CACHE 层同号记录（如有）跨层读取')


def _trigger99_note(crec):
    """99 三路触发披露（阈值无规则键、概率值登记不分配；audit §1.3 逐行一致口径）。"""
    def fmt(v):
        return repr(v) if isinstance(v, float) else repr(v)
    p1, p2, p3 = crec.get('param1'), crec.get('param2'), crec.get('param3')
    frac = [v for v in (p1, p2, p3)
            if isinstance(v, (int, float)) and not isinstance(v, bool)
            and v not in (0, 1)]
    base = ('触发披露（99 三路门，与 2003 单路不同；阈值无规则键、概率值登记不分配）：'
            f'Normal→param1={fmt(p1)}、Critical→param2={fmt(p2)}、Skill→param3={fmt(p3)}'
            '（阈值>0 且 Random.Range(0,1)≤阈值才触发；句面限定词与阈值组合逐行一致——'
            '批 13 审计 §1.3）')
    if frac:
        base += (f'；本载体含分数概率阈值 {"/".join(repr(v) for v in frac)}＝「一定確率で」类'
                 '概率触发（APK 侧分数阈值×23 同形态），概率值登记不分配')
    return base + '；'


def _trigger2003_note(crec):
    p3 = crec.get('param3')
    base = ('触发条件（与 ability99 的 param1/param3/param2 三路不同，逐行披露）：'
            '仅 Skill 型着弹（damageType==1）经 param3×Random.Range 门触发；'
            'Normal/Critical 永不触发（output/ordinary_effects/ability2003/ 受控 '
            'type_gate_kind0/kind2 实测 0 提交）')
    if isinstance(p3, (int, float)) and not isinstance(p3, bool) and p3 != 1:
        base += (f'；载体 /param3={p3!r}（APK 特有形态：Skill 型着弹 {p3 * 100:g}% 概率触发'
                 '——逐行披露；概率值登记不分配）')
    else:
        base += f'；载体 /param3={p3!r} → Skill 着弹即触发'
    return base


def _p0_note_b13(p0_raw, with_row, et):
    """p0 披露：批 9/10 口径＋APK 特有 0 值分支。"""
    if p0_raw == 0:
        return (f'载体 /param0=0（APK schema 真实零；语义未核、登记不分配——audit §1.1 '
                'APK 特有形态披露（17547/25510/28053 同形态）；不出时长值行）；')
    if et == 99:
        import card_page_inference_b9_debuff as B9
        return B9._p0_note(p0_raw, with_row)
    import card_page_inference_b10_sa2003 as B10
    return B10._p0_note(p0_raw, with_row)


def _slots_note(crec, claimed_slots, et):
    """载体槽位登记（批 9/10 同法；分数阈值/自身侧披露随型）。"""
    consumed, idle = [], []
    for key in sorted(crec):
        if not re.match(r'^(param|iParam|iparam|skillparam|flag|skillflag)\d', key):
            continue
        entry = f'/{key}={crec.get(key)!r}'
        (consumed if key in claimed_slots else idle).append(entry)
    parts = ['载体槽位登记：本句消费 ' + '、'.join(consumed)]
    if idle:
        if et == 99:
            idle_note = ('句外槽未分配（不归属本句，仅登记原值；param0 为支持计时（本句时长值行'
                         '消费时另行列示），param1/param2/param3 为三路触发阈值（无规则键、'
                         '概率值登记不分配），param4/5/6 自身侧无 99 换算规则——复合句自身半句'
                         '登记不分配）：')
        else:
            idle_note = ('句外槽未分配（不归属本句，仅登记原值；param0 为支持计时（本句时长值行'
                         '消费时另行列示）；param3 为 Skill 型触发阈值（触发条件披露于值行 '
                         'note，不出值行）；param1/param2 全库无记录、param4/5/6 自身侧提交'
                         '未登记换算——复合句自身半句不属本批，登记不分配）：')
        parts.append(idle_note + '、'.join(idle))
    return '；'.join(parts)


def _unit_desc(param, raw, et):
    if param == 'param7':
        return '单位：攻击倍率加算增量（显示百分点；负值＝加算下降贡献，非乘数）'
    if param == 'param8':
        if et == 2003:
            return '单位：速度因子加算增量（负值＝加算下降贡献）'
        return ('单位：速度因子加算增量（负值＝加算下降贡献）；p8 语义证据基座仍为已核 ID '
                '43023616 单条受控检查（CACHE 侧 occurrences=1 已核 ID 数口径）——本行载体为 '
                'APK 侧存在数口径（82 条）登记的外推，逐行披露、不得升格')
    return ('受伤量倍率 +{}（受伤量因子 {}；不是固定防御减少 {}%）——正文写作「防御」'
            '的表现层口径'.format(raw, 1 + raw, f'{raw * 100:g}'))


_HINT_META = None


def _hint(table, reasons, subject=None, attrs=(), sent_no=None, sent_total=0, **extra):
    out = dict(kind='hint', reasons=reasons, subject=subject, attrs=list(attrs), table=table,
               sent_no=sent_no, sent_total=sent_total, b13_ext=True)
    out.update(extra)
    return out


# ---- P6 跨 cid 载体竞争守卫（键 (层,id)；与批 9/10 的 CACHE 登记分开，同号 ID 不串）----
_CLAIMS = {}


def _route_mismatch_note(frag, apk99):
    """R03 修辅助（20261022 DeepSeek 定向审查）：句面触发限定词与各载体阈值路逐行比对，
    路由不符的载体逐行披露（仅披露，判定不变——multi-carrier 仍一律不晋级）。
    审计 §1.3 口径：p1>0=通常攻撃路、p2>0=クリティカル路、p3>0=必殺技/Skill 路。"""
    qual = []
    if '通常攻撃' in frag:
        qual.append(('通常攻撃', 'param1'))
    if 'クリティカル' in frag:
        qual.append(('クリティカル', 'param2'))
    if '必殺技' in frag:
        qual.append(('必殺技', 'param3'))
    if not qual:
        return ''
    bad = []
    for sid, crec in apk99:
        for name, p in qual:
            v = crec.get(p)
            if not (isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0):
                bad.append(f'skilllist|{sid}|APK：句面「{name}…」但 /{p}={v!r}（该路阈值'
                           '不活性，句面限定词与该载体路由不符——如实披露）')
    if not bad:
        return '；句面限定词↔载体阈值路逐行比对：无不符'
    return '；句面限定词↔载体阈值路逐行比对（不符项）：' + '；'.join(bad)


def _carrier_vals(crec):
    return (f'p0={crec.get("param0")!r},p7={crec.get("param7")!r},'
            f'p8={crec.get("param8")!r},p9={crec.get("param9")!r},'
            f'p1/p2/p3={crec.get("param1")!r}/{crec.get("param2")!r}/{crec.get("param3")!r}')


# =====================================================================================
# 批 9 侧接管（skilllist/supporterskill 行；own sub_effect 链 APK 99 载体）
# =====================================================================================
def handle_99_apk(frag, table, layer, record_id, cid, subject, attrs, sent_no, sent_total,
                  apk99, own_ability, text):
    """批 9 APK 域外出口（B9.evaluate 的 ``apk99 and not c99`` 分支）。

    ≥2 个 APK 载体 → hint multi-carrier（双侧值）；恰 1 → P4/P5/P4b/P6 逐行门控，
    全过 → 晋级（b13 标记）；任一不过 → hint（具体阻塞）。"""
    import card_page_inference_b9_debuff as B9
    import card_page_inference_b10_sa2003 as B10
    clause, _attrs2, subject2 = B9._debuff_clause(frag)
    replaced = ('本行批 9 时因载体在 APK 层整行留 hint carrier-out-of-domain；批 13 九键'
                '样本域扩至 CACHE＋APK 两域分源后经本行级审核：')
    if len(apk99) > 1:
        det = '；'.join(f'skilllist|{sid}|APK({_carrier_vals(c)})' for sid, c in apk99)
        # R03 修复（20261022 DeepSeek 定向审查）：不再统一写「阈值互补（疑通常/必殺分载）」
        # ——8 行 multi-carrier 的阈值组合关系互补/重叠逐行而异（5261 为 (1,1,1)/(0,1,0)
        # 子集重叠，非互补）；改为逐载体阈值组合列示（det 内 p1/p2/p3）＋句面限定词↔载体
        # 阈值路逐行比对披露（214 句面「通常攻撃時」但一载体仅 Skill 路）。判定不变。
        return _hint(table, [f'P3：{len(apk99)} 个 APK 层 99 载体（归属歧义，multi-carrier）：{det}'
                             '——两载体参数值不同、阈值组合逐载体列示（上列 p1/p2/p3；组合关系'
                             '互补或重叠逐行而异，不统一推断「阈值互补/通常・必殺分载」模型）'
                             + _route_mismatch_note(frag, apk99)
                             + '，句→载体归属无模型，'
                             '不晋级（批 9 C3/批 8 B8-R02 同判；批 10 的 4313 同值案亦未拆）'
                             '；' + replaced + '仍留 hint（键由 inference_b9_hint 行级替换为 '
                             'inference_b13_hint，不双登记）'],
                         subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    carrier_id, crec = apk99[0]
    carrier_key = f'skilllist|{carrier_id}|APK'
    row_key = f'{table}|{record_id}|{layer}'
    chain_desc = (f'{row_key} own sub_effect→{carrier_key}(ability99,SA_PowerDrain'
                  f'"{(crec.get("name") or "")[:20]}")')
    # P4 形状（双向；批 9 同门）
    mism = []
    for attr, slot in B9.SLOT_OF.items():
        claimed = attr in attrs
        act = B9._active(crec.get(slot))
        if claimed and not act:
            mism.append(f'敵減益半句含{attr}但载体 /{slot} 不活性({crec.get(slot)!r})')
        if (not claimed) and act:
            mism.append(f'载体 /{slot} 活性({crec.get(slot)!r})但敵減益半句无{attr}')
    if mism:
        return _hint(table, [f'P4：形状不符：' + '；'.join(mism) + '（缺槽＝缺失不补 0，'
                             'rules limits 口径）；' + replaced + '形状不符→仍留 hint'],
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    # P5 方向（代码语义；批 9 同门）
    dir_bad = []
    for param in ('param7', 'param8'):
        raw = crec.get(param)
        if B9._active(raw) and raw > 0:
            label = '攻撃力' if param == 'param7' else '移動速度'
            dir_bad.append(f'/{param}={raw}>0 与{label}下降冲突（加算正值为上升贡献）')
    p9 = crec.get('param9')
    if B9._active(p9) and p9 < 0:
        dir_bad.append(f'/param9={p9}<0 与受伤量加算口径（防御下降的表现层）冲突')
    if dir_bad:
        return _hint(table, ['P5：方向冲突（direction-mismatch）：' + '；'.join(dir_bad)
                             + '；' + replaced + '方向不符→仍留 hint'],
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    # P4b 竞争句
    competitors = B9._competing_debuff_sentences(text, frag, attrs)
    if competitors:
        return _hint(table, ['P4b：本记录正文内存在其它敵下降句主张同属性（归属歧义，'
                             'competing-debuff-sentence）：'
                             + '；'.join(c.strip()[:50] for c in competitors[:4])
                             + '；' + replaced + '归属歧义→仍留 hint'],
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    # B13-R01 修复轮 provenance（20261022 DeepSeek 定向审查；仅溯源、不参与门控）：
    # 按修复前检测器（frag 不规范化＋属性词子串匹配）复算一次——若首轮会误报竞争句而
    # 修复后为空，则本行晋级源于修复轮，行级 provenance 如实记录（不硬编码行号）。
    import unicodedata as _ud
    _frag_legacy = frag or ''
    _legacy = []
    for s in re.findall(r'[^。]*。', (text or '').replace('\\n', '\n')):
        if _frag_legacy.strip() and _frag_legacy.strip() in _ud.normalize('NFKC', s):
            continue
        if not ('敵' in s and any(w in s for w in B9.DOWN_WORDS)
                and any(a in s for a in B9.ATTRS3) and '敵から受ける' not in s):
            continue
        if set(attrs) & {a for a in B9.ATTRS3 if a in s}:
            _legacy.append(s)
    p4b_fix_round = None
    if _legacy:
        p4b_fix_round = ('P4b 修复轮 provenance（B13-R01，20261022）：本行批 13 首轮因 P4b '
                         '检测器缺陷误报竞争句整行留 hint（误报句：'
                         + '；'.join(c.strip()[:40] for c in _legacy[:2]) + '）；检测器修复'
                         '（frag/候选句同一 NFKC 规范化管线＋属性词边界感知——属性防御力≠'
                         '防御力）后竞争句为空，其余门（P4 形状/P5 方向/P6 守卫）逐行通过，'
                         '按 inference_b13 晋级；evidence=推断、归属推断分层披露不变，'
                         '不升确认')
    # P6 跨 cid 载体竞争守卫（键 (层,id)）
    others = _CLAIMS.get(('APK', carrier_id), set()) - {cid}
    if others:
        return _hint(table, [f'P6：跨 cid 载体竞争：载体 {carrier_key} 已被 '
                             f'cid {",".join(map(str, sorted(others)))} 的行主张（进程内登记）'
                             '；' + replaced + '竞争→仍留 hint'],
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    _CLAIMS.setdefault(('APK', carrier_id), set()).add(cid)

    numeric_source = f'模板推断（批 13 APK 扩域：{chain_desc}）'
    answers = []
    claimed_slots = []
    p0_raw = crec.get('param0')
    p0_row_due = bool('一定時間' in frag and isinstance(p0_raw, (int, float))
                      and not isinstance(p0_raw, bool) and p0_raw > 0)
    for attr in attrs:
        param = B9.SLOT_OF[attr]
        claimed_slots.append(param)
        raw = crec.get(param)
        rule = R.rule_for('skilllist', 99, '/' + param)
        converted = R.answer_for('skilllist', 99, '/' + param, raw, crec)
        evidence_dirs, evidence_files = B9._field_evidence(param)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B13_SCOPE,
            rule_key=f'skilllist|99|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_id, layer='APK',
                        record_key=carrier_key),
            note=(f'模板批 13 APK 扩域值行（来源载体＝{carrier_key}，ability=99；链：'
                  f'{chain_desc}）；句中敵減益半句「{clause}」的「{attr}」→/{param} 1:1 映射；'
                  f'规则键 skilllist|99|/{param}；原值 {raw}；'
                  f'{_unit_desc(param, raw, 99)}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）——样本域'
                  '已扩至 CACHE＋APK 两域分源（批 13：APK 199 条全量分布 0 方向反例＋触发'
                  '限定词↔阈值组合逐行一致＋2 条 APK 记录受控检查＋199×3 路全域公式核对 '
                  '0 失败，无新反汇编、未实机）；'
                  '本条数值归属＝推断（模板批 13 APK 扩域：唯一 sub99 载体＋句面形状匹配为'
                  '数据侧结构对应，引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'方向审核：{B9._direction_note(param, raw)}；'
                  f'证据目录 {evidence_dirs[0]} 及 output/ordinary_effects/ability99/；'
                  f'对象披露（双源）：句面依据「{subject}」逐字在句（对象=敌方，逐字）；'
                  f'{B9._NATIVE_TARGET}；'
                  f'条件逐字：句面「{frag}」；'
                  f'{_trigger99_note(crec)}'
                  f'{_p0_note_b13(p0_raw, with_row=p0_row_due, et=99)}'
                  f'{_layer_note(layer)}；'
                  f'样本域：{_sample_domain_note(rule, param)}'),
            quantitative=True))
    if p0_row_due:
        param = 'param0'
        claimed_slots.append(param)
        rule = R.rule_for('skilllist', 99, '/' + param)
        converted = R.answer_for('skilllist', 99, '/' + param, p0_raw, crec)
        evidence_dirs, evidence_files = B9._field_evidence(param)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=p0_raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B13_SCOPE,
            rule_key='skilllist|99|/param0',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_id, layer='APK',
                        record_key=carrier_key),
            note=(f'模板批 13 APK 扩域时长值行（来源载体＝{carrier_key}，ability=99；链：'
                  f'{chain_desc}）；句中「一定時間」→/param0 1:1 映射；规则键 '
                  f'skilllist|99|/param0；原值 {p0_raw}；单位：游戏秒（支持计时输入，'
                  '游戏 delta 扣减、不乘 Chain）；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）——样本域'
                  '已扩至 CACHE＋APK 两域分源（批 13，无新反汇编、未实机）；'
                  '本条数值归属＝推断（模板批 13 APK 扩域），不升确认；'
                  f'证据目录 {evidence_dirs[0]} 及 output/ordinary_effects/ability99/；'
                  f'条件逐字：句面「{frag}」；'
                  f'{_layer_note(layer)}；'
                  f'样本域：{_sample_domain_note(rule, param)}'),
            quantitative=True))

    extra = [B9._NATIVE_TARGET, _EVIDENCE_NOTE_99]
    if p4b_fix_round:
        extra.append(p4b_fix_round)
    extra.append('跨记录归属依据（b9 scope §5.1 同法＋批 13 扩域）：句→99 载体为数据侧结构'
                 '对应：唯一 sub99 载体（P2/P3：own sub_effect 链恰 1 个 APK 层 ability99 '
                 '记录∈199 条扩后域）＋敵減益半句属性↔载体活性槽形状匹配（P4 双向）＋方向'
                 '按符号（P5：p7/p8≤0 加算下降、p9≥0 受伤量加算）；引擎侧行→载体装载路径'
                 '无原生核实，行保持推断——永不据此升「确认」')
    extra.append(B9._B1_DISCLOSURE)
    if own_ability == 99:
        extra.append(f'行记录自身 ability=99（{layer} 层）——载体主张只认 sub_effect 链上的'
                     '扩后域 99 记录，行自身参数不消费')
    if competitors:
        extra.append('P4b 竞争句披露（不阻塞）：本记录正文内另有敵下降句（'
                     + '、'.join(c.strip()[:40] for c in competitors) + '）；本句按唯一载体＋'
                     '敵減益半句形状匹配化解归属（批 6 §4.1 裁决口径沿用）')
    extra.append('复合句披露：'
                 + ('本句另含非本批半句（「自身/味方…」侧、或回復等），其数值不属批 13（fam11/'
                    '自身バフ等侧另行处理），登记不分配' if re.search(r'自身|味方', frag)
                    else '本句为单一敵減益句'))
    extra.append(_slots_note(crec, set(claimed_slots), 99))
    extra.append(_layer_note(layer))
    claimed_sorted = sorted(set(claimed_slots))
    summary = (B13_TAG + '：敵デバフ值行来源＝' + chain_desc + '；值行全部「推断」，不升'
               '「确认」，不进入整行确认。本行批 9 时因载体在 APK 层留 hint '
               'carrier-out-of-domain；批 13 rules.json 九键样本域扩至 CACHE＋APK 两域分源'
               '（occurrences_apk 登记）后按载体层域晋级，行级键按行级替换为 inference_b13'
               '（不双登记）。句→载体归属为数据侧结构对应：唯一 sub99 载体（APK 199 条扩后'
               '域）＋敵減益半句形状匹配＋方向按符号（p7/p8 负值加算下降、p9 正值受伤量加算'
               '＝「防御」表现层）；引擎侧装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露' + _sample_domain_summary(99) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject, attrs=list(attrs), claims={a: True for a in attrs},
                table=table, carrier_record_id=carrier_id, carrier_layer='APK',
                carrier_name=crec.get('name'), via='own_sub_effect',
                cross_layer=layer != 'APK', replaces_hint='inference_b9_hint',
                p4b_fix_round=p4b_fix_round,
                b13_ext=True, sent_no=sent_no, sent_total=sent_total)


# =====================================================================================
# 批 10 侧接管（bosspattern/denju/dlb/charainfo 行；s_ability 链 APK 2003 载体）
# =====================================================================================
def handle_2003_apk(frag, table, layer, record_id, cid, subject, attrs, clause, sent_no,
                    sent_total, via_note, dup_relay, sid, lay, crec, text,
                    via_pattern=None):
    """批 10 P2 域门出口（B10.evaluate 的 ``lay != 'CACHE' or sid not in domain`` 分支）。

    载体 ∈ APK 148 条扩后域 → P4/P5/P6 逐行门控，全过 → 晋级（b13 标记）；
    任一不过 → hint（具体阻塞）。lay 非 APK 的情形结构上不存在（CACHE 载体必在
    265 条域内），防御性留 hint。"""
    import card_page_inference_b9_debuff as B9
    import card_page_inference_b10_sa2003 as B10

    def _pre(reasons):
        return [via_note + r for r in reasons]

    replaced = ('本行批 10 时因载体在 APK 层整行留 hint carrier-out-of-domain；批 13 九键'
                '样本域扩至 CACHE＋APK 两域分源后经本行级审核：')
    if lay != 'APK':
        return _hint(table, _pre([f'P2：载体 skilllist|{sid}|{lay} 不在两域（CACHE 265 条/'
                                  f'APK 148 条）任一扩后域内（防御性分支；audit §2.3）']),
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    carrier_key = f'skilllist|{sid}|APK'
    row_key = f'{table}|{record_id}|{layer}'
    if via_pattern:
        pid, player = via_pattern
        chain_desc = (f'charainfo|{record_id}|{layer} 经同页同文 bosspattern|{pid}|{player}'
                      f'→s_ability→{carrier_key}'
                      f'(ability2003,SA_PowerDrain"{(crec.get("name") or "")[:20]}")')
    else:
        chain_desc = (f'{row_key} own children→boss_skill.s_ability→{carrier_key}'
                      f'(ability2003,SA_PowerDrain"{(crec.get("name") or "")[:20]}")')
    # P4 形状（双向；批 10 同门）
    ok, _detail, mism = B10._shape_check(attrs, crec)
    if not ok:
        return _hint(table, _pre([f'P4：形状不符：' + '；'.join(mism) +
                                  '（缺槽＝缺失不补 0，rules limits 口径）；' + replaced +
                                  '形状不符→仍留 hint']),
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    # P5 方向（代码语义；批 10 同门）
    dir_bad = []
    for param in ('param7', 'param8'):
        raw = crec.get(param)
        if B9._active(raw) and raw > 0:
            label = '攻撃力' if param == 'param7' else '移動速度'
            dir_bad.append(f'/{param}={raw}>0 与{label}下降冲突（加算正值为上升贡献）')
    p9 = crec.get('param9')
    if B9._active(p9) and p9 < 0:
        dir_bad.append(f'/param9={p9}<0 与受伤量加算口径（防御下降的表现层）冲突')
    if dir_bad:
        return _hint(table, _pre(['P5：方向冲突（direction-mismatch）：' + '；'.join(dir_bad)
                                  + '；' + replaced + '方向不符→仍留 hint']),
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    # P6 跨 cid 载体竞争守卫（键 (层,id)）
    others = _CLAIMS.get(('APK', sid), set()) - {cid}
    if others:
        return _hint(table, _pre([f'P6：跨 cid 载体竞争：载体 {carrier_key} 已被 '
                                  f'cid {",".join(map(str, sorted(others)))} 的行主张'
                                  '（进程内登记）；' + replaced + '竞争→仍留 hint']),
                     subject=subject, attrs=attrs, sent_no=sent_no, sent_total=sent_total)
    _CLAIMS.setdefault(('APK', sid), set()).add(cid)

    numeric_source = f'模板推断（批 13 APK 扩域：{chain_desc}）'
    answers = []
    claimed_slots = []
    p0_raw = crec.get('param0')
    p0_row_due = bool('一定時間' in frag and isinstance(p0_raw, (int, float))
                      and not isinstance(p0_raw, bool) and p0_raw > 0)
    for attr in B9.ATTRS3:
        if attr not in attrs:
            continue
        param = B9.SLOT_OF[attr]
        claimed_slots.append(param)
        raw = crec.get(param)
        rule = R.rule_for('skilllist', 2003, '/' + param)
        converted = R.answer_for('skilllist', 2003, '/' + param, raw, crec)
        evidence_files = B10._field_evidence(param)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B13_SCOPE,
            rule_key=f'skilllist|2003|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=sid, layer='APK',
                        record_key=carrier_key),
            note=(f'模板批 13 APK 扩域值行（来源载体＝{carrier_key}，ability=2003；链：'
                  f'{chain_desc}）；句中敵減益半句「{clause}」的「{attr}」→/{param} 1:1 映射；'
                  f'规则键 skilllist|2003|/{param}；原值 {raw}；'
                  f'{_unit_desc(param, raw, 2003)}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）——样本域'
                  '已扩至 CACHE＋APK 两域分源（批 13：APK 148 条全量分布 0 方向反例＋触发'
                  '限定词↔阈值组合逐行一致＋批 10 已含 APK 记录受控实测＋148×Skill 路全域'
                  '公式核对 0 失败，无新反汇编、未实机）；'
                  '本条数值归属＝推断（模板批 13 APK 扩域：唯一 s_ability→2003 载体＋句面'
                  '形状匹配为数据侧结构对应，引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'方向审核：{B10._direction_note(param, raw)}；'
                  f'证据目录 output/ordinary_effects/ability2003/（受控原生检查 8 项＋批 10 '
                  f'APK 记录检查，native_checks.json）；'
                  f'对象披露（双源）：句面依据「{subject}」逐字在句（对象=敌方，逐字）；'
                  f'{B10._NATIVE_TARGET}；'
                  f'条件逐字：句面「{frag}」；{_trigger2003_note(crec)}；'
                  f'{_p0_note_b13(p0_raw, with_row=p0_row_due, et=2003)}'
                  f'{_layer_note(layer)}；'
                  f'样本域：{_sample_domain_note(rule, param)}'),
            quantitative=True))
    if p0_row_due:
        param = 'param0'
        claimed_slots.append(param)
        rule = R.rule_for('skilllist', 2003, '/' + param)
        converted = R.answer_for('skilllist', 2003, '/' + param, p0_raw, crec)
        evidence_files = B10._field_evidence(param)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=p0_raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B13_SCOPE,
            rule_key='skilllist|2003|/param0',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=sid, layer='APK',
                        record_key=carrier_key),
            note=(f'模板批 13 APK 扩域时长值行（来源载体＝{carrier_key}，ability=2003；链：'
                  f'{chain_desc}）；句中「一定時間」→/param0 1:1 映射；规则键 '
                  f'skilllist|2003|/param0；原值 {p0_raw}；单位：游戏秒（支持计时输入，'
                  '游戏 delta 扣减、不乘 Chain；攻击者与受击目标两次提交共用计时）；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）——样本域'
                  '已扩至 CACHE＋APK 两域分源（批 13，无新反汇编、未实机）；'
                  '本条数值归属＝推断（模板批 13 APK 扩域），不升确认；'
                  f'证据目录 output/ordinary_effects/ability2003/（native_checks.json）；'
                  f'条件逐字：句面「{frag}」；{_trigger2003_note(crec)}；'
                  f'{_layer_note(layer)}；'
                  f'样本域：{_sample_domain_note(rule, param)}'),
            quantitative=True))

    extra = [B10._NATIVE_TARGET, _trigger2003_note(crec), _EVIDENCE_NOTE_99]
    if table == 'charainfo':
        p23 = ('P2/P3：同页同文 bosspattern 的 s_ability 链恰 1 个 APK 层 '
               'ability2003 记录∈148 条扩后域')
    else:
        p23 = ('P2/P3：own children 的 boss_skill.s_ability 链恰 1 个 APK 层 '
               'ability2003 记录∈148 条扩后域')
    extra.append('跨记录归属依据（b10 scope §4 同法＋批 13 扩域）：句→2003 载体为数据侧结构'
                 '对应：唯一 s_ability→2003 载体（' + p23 + '）＋敵減益半句属性↔载体活性槽'
                 '形状匹配（P4 双向）＋方向按符号（P5：p7/p8≤0 加算下降、p9≥0 受伤量加算）；'
                 '处理器/筛选/触发/提交侧为批 10 静态＋受控原生证据（8 项，已含 APK 记录实测）'
                 '＋批 13 APK 148 条全域公式核对，但引擎侧行→载体装载路径（本行运行时实际装载'
                 '该载体）无原生核实，行保持推断——永不据此升「确认」')
    extra.append(B10._b1_disclosure(table))
    if dup_relay:
        extra.append('多中继披露（不阻塞）：链上多条 s_ability 中继指向同一 APK 2003 载体 '
                     f'{carrier_key}（dup_relay）；载体唯一性按去重后恰 1 个判定（批 9 §3.1 '
                     '审计同法）')
    self_half_slots = {}
    if '自身の' in frag:
        self_half_slots = {p: crec.get(p) for p in ('param4', 'param5', 'param6')
                           if isinstance(crec.get(p), (int, float))
                           and not isinstance(crec.get(p), bool) and crec.get(p) != 0}
    if self_half_slots:
        extra.append('复合句自身半句披露：本句「自身の…」半句对应载体自身侧提交槽 '
                     + '、'.join(f'/{k}={v!r}' for k, v in sorted(self_half_slots.items()))
                     + '（受控 self_side_p4_and_zero_slots_apk 实测双向提交——APK 记录 '
                       '31222712 同形态）；param4/5/6 未登记换算（b10 scope §3），登记不分配、'
                       '不属本批值行')
    competitors = B9._competing_debuff_sentences(text, frag, attrs)
    if competitors:
        extra.append('P4b 竞争句披露（不阻塞；本批按审计门集判定，竞争句仅登记）：本记录正文内'
                     '另有敵下降句（' + '、'.join(c.strip()[:40] for c in competitors) + '）；'
                     '本句按唯一载体＋敵減益半句形状匹配化解归属（批 6 §4.1 裁决口径沿用）')
    extra.append('复合句披露：'
                 + ('本句另含非本批半句（「自身/味方…」侧、或回復等），其数值不属批 13'
                    '（fam11/自身バフ等侧另行处理），登记不分配' if re.search(r'自身|味方', frag)
                    else '本句为单一敵減益句'))
    extra.append(_slots_note(crec, set(claimed_slots), 2003))
    extra.append(_layer_note(layer))
    claimed_sorted = sorted(set(claimed_slots))
    summary = (B13_TAG + '：敵デバフ值行来源＝' + chain_desc + '；值行全部「推断」，不升'
               '「确认」，不进入整行确认。本行批 10 时因载体在 APK 层留 hint '
               'carrier-out-of-domain；批 13 rules.json 九键样本域扩至 CACHE＋APK 两域分源'
               '（occurrences_apk 登记）后按载体层域晋级，行级键按行级替换为 inference_b13'
               '（不双登记）。句→载体归属为数据侧结构对应：唯一 s_ability→2003 载体（APK 148 '
               '条扩后域）＋敵減益半句形状匹配＋方向按符号（p7/p8 负值加算下降、p9 正值受伤量'
               '加算＝「防御」表现层）；触发仅 Skill 型着弹（Normal/Critical 不触发，与 99 '
               '三路不同）；引擎侧行→载体装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露' + _sample_domain_summary(2003) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject, attrs=list(attrs), claims={a: True for a in attrs},
                table=table, carrier_record_id=sid, carrier_layer='APK',
                carrier_name=crec.get('name'), via='s_ability_chain',
                via_pattern=list(via_pattern) if via_pattern else None,
                cross_layer=layer != 'APK', replaces_hint='inference_b10_hint',
                b13_ext=True, sent_no=sent_no, sent_total=sent_total)
