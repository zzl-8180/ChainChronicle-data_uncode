"""模板作用域推断层——批 14：APK 域外扩域第二批（ability2012×211／ability1095×52 载体）。

前置与依据（批 14 前置审计
``output/character_skills/inference_inventory/b14_apkext_scope.md``，2026-10-22）：

* rules.json 八键（skilllist|2012 三键＋skilllist|1095 五键）样本域已由「仅当前 v3
  CACHE」扩为「CACHE＋APK 主表两域分源」（``rules.py`` ``_b14_apkext_domain_update``；
  单键保留、新增伴生字段 ``occurrences_apk``＝APK 存在数（中性口径：存储 0.0＝中性不计，
  与 CACHE 缺失不计同语义；p2/p3=1.0、p6=1.5 中性与 CACHE 同口径计入），不拆双键）；
* 全域公式核对 0 违例：2012×211×3 键经 SupportGuest 夹具逐条 replay（含 iParam0≠0×16
  条以扩展夹具走 CheckJobFlag 真实体）、1095×52×5 键按批 12 同法五窗口 replay
  （work/character_skills_b14_impl/；2012 侧证据落 output/ordinary_effects/ability2012/
  native_checks.json 顶层 b14_extension）；
* **升级项（经主持授权）**：BtlCharaUtil.CheckJobFlag 非零分支体（0x13ab388–0x13ab458）
  自既有恢复的原生镜像提取（``output/ordinary_effects/ability2012/checkjobflag_body.txt``）——
  iParam0≠0 时逐成员读职业（成员+0x28→+0xf8 的 ParamS_int.get_Value）、
  ``lsl w8,1,w0``→``tst w8,w19`` 位命中保留、未命中移出成员列表（＝按位图
  (1<<成员职业)&iParam0 过滤味方成员；与 ability1017/3000 元数据 JobType 位图同型）；
  职业过滤受控检查 6 项（命中/未命中/混合成员两侧）全过；未开真机。

本批行集＝批 8 遗留 APK ability2012 域外 hint 行 **196**（195 晋级＋1 G6 句无对象词留守）
＋批 11/12 遗留 APK ability1095 域外 hint 行 **27**（17 晋级＋10 P4 形状不符留守）；
**78 行跨层**（CACHE 层行＋APK 载体，全 b8 族）按**载体所在层**域归类取值，不得跨层读取
（批 13 §2.3 先例）。113 载体（86×2012＋27×1095）全在 APK 主表、与 CACHE skilllist
同号 0 交集；两域同号 19 条（15×2012＋4×1095）全部非载体——分源不合并、逐行披露。

接线（载体域门扩展）：批 8/11 的 APK 域外出口处委托本模块——

* B8.evaluate 的 G5 样本域门（载体层==APK）→ :func:`handle_2012_apk`
  （G4 形状/G6 对象/G7 方向/G8 守卫→晋级或 hint，与批 8 同门同序）；
* B11.evaluate 的 P2 域门（载体层==APK）→ :func:`handle_1095_apk`
  （P4/P5/G1′/P3→晋级或 hint，与批 11 同门同序）。

返回 dict 带 ``b14_ext=True`` 标记：promote 由行级键 ``inference_b14`` 登记（批 12/13
replaces_hint 先例，替换对应 ``inference_b8_hint``/``inference_b11_hint``，不双登记；
166 行批 6 让渡注记随晋级一并行级替换——crit 主张已由本链值行兑现，不残留 hint 键）；
hint（G6 object-unstated、P4 shape-mismatch 等）**不带** b14_ext 标记、经 B8/B11 原有
hint 键（inference_b8_hint/inference_b11_hint）写出、理由改写为实际门（不再是
carrier-out-of-domain）。其余行零变化。

值行政策 parity：

* 2012 侧与批 8 CACHE 侧完全一致——p4 暴击率 pp 加算（对 0 加算增量）、p5 暴伤系数
  增量（不减 1095 的 1.5 基准）；批 8 未出 p0 时长值行（D1 裁决归批 6 t13 /skillparam3），
  本批同政策不新增时长值行；中性 0.0 槽不出值行（P4 形状门：存储 0.0＝不活性）；
* 1095 侧与批 12 完全一致——p1/p2/p3/p5/p6 按句主张活性槽出值行：p5 暴击 pp 直接加算
  （不套 Always3 减 1.5）、p6 delta=原值−1.5、p2 移动乘算、p3 受伤量口径（不是固定防御量）。

iParam0 条件接线（8 载体×27 行，audit §5 方案）：值行带结构化 ``condition_label``＝句面
条件短语逐字（「戦士の味方の場合」等，与句内首个「、」前条件节同值、不换算），渲染层按
条件分组首屏显示（批 4 先例：无 condition_label＝「基础」组）——职业条件作为条件分组
披露、不并入基础值；note 记录侧 iParam0 位图解码双源披露（``rules.py`` 既有
``decode_job_mask`` 复用）；句面职业词位集合==解码位集合逐行断言（27/27，不符留 hint
不硬猜）。

硬边界：只升「推断」；不进整行确认；APK 装载路径无原生核实，永不据此升「确认」；
批 1–13 行与计数不动（本批只接管批 8/11 的 APK 域外 hint 行）；30236 基线卡行/值零触碰。
"""
from __future__ import annotations

import re
import unicodedata

import rules as R
import card_page_inference_b6_bossbuff as B6
import card_page_inference_b8_crit2012 as B8
import card_page_inference_b11_sa1095 as B11
import card_page_inference_b12_1095ext as B12

B14_TAG = '推断（模板批 14 APK 扩域）'
B14_SCOPE = 'TEMPLATE_BATCH14_APKEXT'
B14_FAMILY = ('クリティカル／自身增益家族 APK 扩域第二批（批 14）——skilllist ability2012 '
              '（SA_SupportTarget，APK 主表 211 条）与 ability1095（Always3，APK 主表 '
              '52 条）载体：批 8 的 APK 域外 hint 行与批 11/12 的 APK 域外 hint 行按载体'
              '层域晋级（rules.json 八键样本域扩至 CACHE＋APK 两域分源、occurrences_apk '
              '登记；行层≠载体层时按载体层域归类取值，不得跨层读取）')

EVIDENCE_NOTE_2012 = ('批 14 APK 扩域证据（CheckJobFlag 非零分支体 0x13ab388–0x13ab458 片段'
                      '＝升级项经主持授权自既有恢复的原生镜像提取，未开真机；APK 211 条×3 键'
                      '全域公式核对 0 失败＋4 边界（40033812/41100413/40322511/40429211）＋6 项'
                      '职业过滤受控检查）：output/ordinary_effects/ability2012/native_checks.json '
                      '顶层 b14_extension＋checkjobflag_body.txt')

EVIDENCE_NOTE_1095 = ('批 14 APK 扩域证据（1095×52×5 键全域公式核对 260 项 0 失败＋3 边界'
                      '（40034001/41123201/40033901）；批 12 同法五窗口，无新反汇编、未实机）：'
                      'work/character_skills_b14_impl/b14_apk_checks_1095.json'
                      '（output/ordinary_effects/ability1095/ 不在本批写入边界，未合并，'
                      '整合者可按需合并）')

# 句面职业词→JobType 位（audit b14_special_audit.py name2bit 逐字沿用）
_NAME2BIT = {'戦士': 0, '战士': 0, '弓使い': 1, '弓手': 1, '魔法使い': 2, '法师': 2,
             '魔導士': 2, '僧侶': 3, '僧侣': 3, '騎士': 4, '骑士': 4}


def _sample_domain_note(rule, et, param):
    """INFR-02：扩域后单键样本域披露（occurrences CACHE 口径不变＋occurrences_apk）。"""
    return (f'该规则登记 occurrences={rule.get("occurrences")}（CACHE 存在数口径，批 14 未改）'
            f'＋occurrences_apk={rule.get("occurrences_apk")}（APK 存在数，中性口径：2012 '
            'p4/p5 与 1095 p5 的存储 0.0＝中性不计，p2/p3=1.0、p6=1.5 中性与 CACHE 同口径'
            f'计入；origin {rule.get("origin")}）；样本域＝两域分源（批 14 扩域：①当前 v3 '
            f'CACHE 普通 skilllist ability{et} 记录；②APK 主表 output/base_master/'
            f'_mdSkill.json ability{et} 记录；命名空间不合并、同号记录分源不合并（2012 侧 15 '
            '条、1095 侧 4 条，逐键清单见 rules.json conditions；行侧载体按载体所在层取值'
            '不得跨层读取））；本行来源载体记录未逐条核对，按规则适用条件披露，不属逐记录确认')


def _layer_note(row_layer):
    """层披露（逐行强制）：行层与载体层关系＋跨层归类口径（批 13 同法）。"""
    if row_layer == 'APK':
        return ('层披露：行与载体均在 APK 主表层（行层=APK、载体层=APK；APK 记录来源 '
                'output/base_master/_mdSkill.json）；不与 CACHE 层同号记录（如有）跨层取值')
    return ('跨层披露：载体来自 APK 主表（skilllist|…|APK，output/base_master/_mdSkill.json）、'
            '行在 CACHE 层——按载体所在层（APK）域归类取值（批 14 审计 §0），'
            '不与 CACHE 层同号记录（如有）跨层读取')


def _iparam0_notes(crec, frag):
    """iParam0 条件披露（双源）：位图解码（decode_job_mask）＋句面逐字条件。
    返回 (condition_label 或 None, note 或 None, 阻塞原因或 None)。"""
    mask = crec.get('iParam0')
    if not (isinstance(mask, (int, float)) and not isinstance(mask, bool) and mask):
        return None, None, None
    prefix = frag.split('、')[0]
    if 'の場合' not in prefix:
        return None, None, (f'iParam0≠0（{mask}）但句面条件节无「の場合」短语，条件无法逐字'
                            '接线（condition-unstated），不晋级')
    words = [w for w in _NAME2BIT if w in frag]
    sent_bits = sorted({_NAME2BIT[w] for w in words})
    d = R.decode_job_mask(mask)
    if sent_bits != d['bits']:
        return None, None, (f'iParam0 位图解码位 {d["bits"]} 与句面职业词位 {sent_bits} '
                            '不一致（句面职业词：' + '、'.join(words) + '）——归属未化解，'
                            '不硬猜，不晋级')
    note = (f'/iParam0={int(mask)}（位图 1<<JobType；decode_job_mask→'
            f'{"、".join(d["jobs"])}；成员列表经 BtlCharaUtil.CheckJobFlag 按位图 '
            f'(1<<成员职业)&{int(mask)} 过滤——命中保留、未命中移出（b14_extension 片段 '
            '0x13ab388–0x13ab458＋受控检查；=0 旁路为 CACHE 侧既有口径）；'
            f'句面条件（逐字）「{prefix}」——按 condition_label 条件分组披露，不并入基础值）')
    return prefix, note, None


def _sent_no_total(text, frag):
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    _sents = [s for s in re.findall(r'[^。]*。', wb)]
    sent_no = next((i + 1 for i, s in enumerate(_sents) if frag.strip() in s), None)
    return sent_no, len(_sents)


# ---- P6/G8 跨 cid 载体竞争守卫（键 (层,id)；与批 8/11 的 CACHE 登记分开，同号 ID 不串）----
_CLAIMS = {}


def _hint(table, reasons, subject=None, attrs=(), sent_no=None, sent_total=0, **extra):
    out = dict(kind='hint', reasons=reasons, subject=subject, attrs=list(attrs), table=table,
               sent_no=sent_no, sent_total=sent_total)
    out.update(extra)
    return out


def _replaced_note(b8_side):
    return ('本行批 %s 时因载体在 APK 层整行留 hint carrier-out-of-domain；批 14 八键'
            '样本域扩至 CACHE＋APK 两域分源后经本行级审核：'
            % ('8' if b8_side else '11/12'))


# =====================================================================================
# 批 8 侧接管（bosspattern/charainfo/denju/dlb 行；t13→s_ability 链 APK 2012 载体）
# =====================================================================================
def handle_2012_apk(frag, table, layer, record_id, cid, rate, power, claims, subject_phrase,
                    obj, direction, carrier, text):
    """批 8 G5 域门出口（B8.evaluate 的载体层==APK 分支）。

    G4/G6/G7/G8 逐行门控（与批 8 同门同序，仅样本域换为扩后两域）→ 晋级（b14_ext）
    或 hint（具体阻塞；不带 b14_ext，批 8 原有 hint 键写出、理由为实际门）。"""
    crec = carrier['record']
    carrier_id = carrier['carrier_id']
    sent_no, sent_total = _sent_no_total(text, frag)
    replaced = _replaced_note(True)

    # iParam0 条件接线前置核对（8 载体 27 行；不符留 hint 不硬猜）
    condition_label, iparam0_note, iparam0_block = _iparam0_notes(crec, frag)
    if iparam0_block:
        return _hint(table, ['G5/iParam0：' + iparam0_block + '；' + replaced + '仍留 hint'],
                     subject=subject_phrase, attrs=list(claims.values()),
                     sent_no=sent_no, sent_total=sent_total)

    # --- G4 属性形状（双向；批 8 同门；APK 存储 0.0＝不活性＝中性不计） -----------------------
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
        return _hint(table, ['G4：形状不符：' + '；'.join(mism) + '（缺槽＝缺失不补 0、存储 0.0＝'
                             '中性不计入活性，rules limits 口径）；' + replaced +
                             '形状不符→仍留 hint（实际门）'],
                     subject=subject_phrase, attrs=list(claims.values()),
                     sent_no=sent_no, sent_total=sent_total)

    # --- G6 对象相容（批 8 同门三分支） ------------------------------------------------------
    p8 = crec.get('param8')
    if obj == 'ally_all' and p8 == 64:
        return _hint(table, ['G6：句面对象＝味方全体 vs 载体 /param8=64（MYSELF）不符'],
                     subject=subject_phrase, attrs=list(claims.values()),
                     sent_no=sent_no, sent_total=sent_total)
    if obj == 'self' and p8 == 31:
        return _hint(table, ['G6：句面对象＝自身 vs 载体 /param8=31（pGROUP_ALL）不符'],
                     subject=subject_phrase, attrs=list(claims.values()),
                     sent_no=sent_no, sent_total=sent_total)
    if obj == '?':
        return _hint(table, ['G6：句无对象词（味方全体/全ての味方/自身/味方），无法与载体 /param8 '
                             '交叉核对（object-unstated）；' + replaced +
                             '实际门＝G6 对象词缺失（域门已由批 14 扩域解除，与域无关）'],
                     subject=subject_phrase, attrs=list(claims.values()),
                     sent_no=sent_no, sent_total=sent_total)

    # --- G7 方向（批 8 同门） ----------------------------------------------------------------
    if direction == 'down':
        return _hint(table, ['G7：句向「下がる/下がり」与 p4/p5 正值加算增益方向冲突'
                             '（direction-mismatch）'], subject=subject_phrase,
                     attrs=list(claims.values()), sent_no=sent_no, sent_total=sent_total)
    if direction == '?':
        return _hint(table, ['G7：句无上下方向词（direction-unstated）'],
                     subject=subject_phrase, attrs=list(claims.values()),
                     sent_no=sent_no, sent_total=sent_total)

    # --- G8 跨 cid 载体竞争守卫（键 (APK,id)；批 8 CACHE 登记分开） ---------------------------
    claim_key = ('APK', carrier_id)
    others = _CLAIMS.get(claim_key, set()) - {cid}
    if others:
        return _hint(table, [f'G8：跨 cid 载体竞争：载体 skilllist|{carrier_id}|APK 已被 '
                             f'cid {",".join(map(str, sorted(others)))} 的行主张（进程内登记；'
                             '审计实测 0 例，本守卫为防御性保留）'],
                     subject=subject_phrase, attrs=list(claims.values()),
                     sent_no=sent_no, sent_total=sent_total)

    # --- 晋级 --------------------------------------------------------------------------------
    _CLAIMS.setdefault(claim_key, set()).add(cid)
    pid = carrier['pattern_id']
    carrier_key = f'skilllist|{carrier_id}|APK'
    relay_key = f"bossskill|{carrier['relay_id']}|{carrier['relay_layer']}"
    pattern_key = f'bosspattern|{pid}|{carrier["relay_layer"]}'
    head = f'charainfo|{record_id}|{layer}→同页同文 ' if table == 'charainfo' else \
           '' if table == 'bosspattern' else f'{table}|{record_id}|{layer}→'
    chain_desc = (f'{head}{pattern_key}→{relay_key}(type13,slot {carrier["relay_slot"]})'
                  f'→s_ability→{carrier_key}(ability2012)')
    numeric_source = f'模板推断（批 14 APK 扩域：{chain_desc}）'
    direction_word = {'up': '上がる/上がり/上げる', 'down': '下がる/下がり'}.get(direction, direction)
    answers = []
    claimed_params = []
    p0_raw = crec.get('param0')
    for attr, want in (('クリティカル発生率', rate), ('クリティカル威力', power)):
        if not want:
            continue
        param = 'param4' if attr == 'クリティカル発生率' else 'param5'
        claimed_params.append(param)
        raw = crec.get(param)
        rule = R.rule_for('skilllist', 2012, '/' + param)
        converted = R.answer_for('skilllist', 2012, '/' + param, raw, crec)
        evidence_dirs, evidence_files = B8._field_evidence(param)
        unit_desc = ('单位：百分点（原值×100；对 0 加算增益，非「以 N% 概率施加支持」）'
                     if param == 'param4' else
                     '单位：系数增量（暴伤系数 +原值；不减 1095 的 1.5 基准，非最终伤害相对增加）')
        answer = dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B14_SCOPE,
            rule_key=f'skilllist|2012|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=carrier_id, layer='APK',
                        record_key=carrier_key),
            note=(f'模板批 14 APK 扩域值行（来源载体＝{carrier_key}，ability=2012；链：'
                  f'{chain_desc}）；句中「{attr}」→/{param} 1:1 映射；规则键 '
                  f'skilllist|2012|/{param}；原值 {raw}；{unit_desc}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）——样本域'
                  '已扩至 CACHE＋APK 两域分源（批 14：APK 211 条×3 键全域公式核对 0 失败＋'
                  'CheckJobFlag 非零分支体片段（升级项经主持授权）＋边界/职业过滤受控检查，'
                  '无新反汇编来源镜像、未实机）；'
                  '本条数值归属＝推断（模板批 14 APK 扩域：唯一 t13→s_ability 载体＋句面形状'
                  '匹配为数据侧结构对应，引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'方向审核：方向一致（原值 {raw}>0，与句「{direction_word}」方向一致）；'
                  f'证据目录 {evidence_dirs[0]} 及 output/ordinary_effects/ability2012/；'
                  f'{B8._object_note(subject_phrase, crec.get("param8"))}；'
                  f'条件逐字：句面「{frag}」；{B8._TRIGGER_NATIVE}；'
                  f'{B8._p0_note(p0_raw)}'
                  + (f'iParam0 条件披露（双源）：{iparam0_note}；' if iparam0_note else '')
                  + f'{_layer_note(layer)}；'
                  f'样本域：{_sample_domain_note(rule, 2012, param)}'),
            quantitative=True)
        if condition_label:
            answer['condition_label'] = condition_label
        answers.append(answer)
    if not claimed_params:
        # 不可达（G4 已保证至少一向主张与活性对应）；防御性登记
        raise AssertionError('批 14 handle_2012_apk：无主张属性（G4 应已拦截）')

    extra = [B8._object_note(subject_phrase, crec.get('param8')) + '；' + B8._TRIGGER_NATIVE,
             EVIDENCE_NOTE_2012]
    if condition_label:
        extra.append('iParam0 职业过滤披露：' + iparam0_note +
                     '；条件不并入基础值（首屏条件分组，批 4 condition_label 先例）')
    extra.append('跨记录归属依据（b8 scope §4.2 同法＋批 14 扩域）：句→2012 载体为数据侧结构'
                 '对应：唯一 type13 中继＋s_ability 字段＋句 crit 属性↔载体活性槽形状匹配'
                 '（G4 双向）；引擎侧 s_ability 装载路径无原生核实，行保持推断——永不据此升'
                 '「确认」')
    if carrier['relay_layer'] != 'APK':
        extra.append(f'跨层链披露：本链 pattern/bossskill 中继段为 {carrier["relay_layer"]} 层'
                     f'记录；s_ability 目标为 APK 层 skilllist 记录（本载体 ∈ 批 14 扩后 APK '
                     '域 211 条）；按载体所在层域归类取值，不得跨层读取')
    if sent_no:
        extra.append(f'多段披露：本记录正文共 {sent_total} 句（以「。」切分），本句位于第 '
                     f'{sent_no} 句；非首段行按唯一载体＋形状匹配化解归属（批 6 §4.1 裁决口径'
                     '沿用），不写「段位↔槽位位置序对应」')
    else:
        extra.append('多段披露：正文句序未能定位（片段不在按「。」切分的句列中）')
    extra.append('同句非 crit 属性不出本批值行（批 14 值行只消费 skilllist|2012|/param4|/'
                 'param5，与批 8 同政策）：t13 侧攻撃力/防御力/移動速度/一定時間归批 6 口径'
                 '（既有批 6 hint/值行保留原状，不重写批 6 键）；D1 裁决：时长值行仍归批 6 '
                 't13 /skillparam3，本批不出 p0 时长值行')
    extra.append(B8._slots_note(crec, set(claimed_params)))
    extra.append(_layer_note(layer))
    claimed_sorted = sorted(set(claimed_params))
    summary = (B14_TAG + '：crit 值行来源＝' + chain_desc + '；值行全部「推断」，不升「确认」，'
               '不进入整行确认。本行批 8 时因载体在 APK 层留 hint carrier-out-of-domain；'
               '批 14 rules.json 2012 三键样本域扩至 CACHE＋APK 两域分源（occurrences_apk '
               '登记）后按载体层域晋级，行级键按行级替换为 inference_b14（不双登记）。'
               '句→载体归属为数据侧结构对应：唯一 type13 中继＋s_ability 字段＋句 crit 属性↔'
               '载体活性槽形状匹配；引擎侧 s_ability 装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露：'
               + '；'.join(_sample_domain_note(R.rule_for('skilllist', 2012, '/' + p), 2012, p)
                           for p in claimed_sorted) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject_phrase, attrs=list(claims), claims=dict(claims),
                table=table, pattern_record_id=pid,
                relay_record_id=carrier['relay_id'], relay_type=carrier['relay_type'],
                relay_slot=carrier['relay_slot'], carrier_record_id=carrier_id,
                carrier_layer='APK', carrier_name=crec.get('name'), via='own',
                cross_layer=layer != 'APK', condition_rows=bool(condition_label),
                replaces_hint='inference_b8_hint', b14_ext=True,
                sent_no=sent_no, sent_total=sent_total)


# =====================================================================================
# 批 11/12 侧接管（skilllist 行；父记录 sub[] APK 1095 载体）
# =====================================================================================
def handle_1095_apk(record, frag, table, layer, record_id, cid, text, data,
                    sent_no, sent_total, sub_id, subrec):
    """批 11 P2 域门出口（B11.evaluate 的载体层==APK 分支）。

    P4/P5/G1′/P3 逐行门控（与批 11 同门同序）→ 晋级（b14_ext）或 hint（具体阻塞；
    不带 b14_ext，批 11 原有 hint 键写出、理由为实际门）。批 11 的 P1/P6 对象门已在
    P2 之前通过；批 12 对 APK 载体不处理（其 P2 分支返回 None）。"""
    sub_key = f'skilllist|{sub_id}|APK'
    replaced = _replaced_note(False)
    claimed = list(dict.fromkeys(B11.ATTR_RE.findall(frag)))
    if not claimed:
        return _hint(table, ['P1：APK sub 存在但片段无属性主张（no-claim-fragment）——批 11 '
                             '口径不占候选；防御性留 hint'], subject='（省略主语）',
                     attrs=[], sent_no=sent_no, sent_total=sent_total)

    # --- P4 形状（双向＋未推广槽；批 11 同门；APK 存储 0.0/1.0/1.5 中性不活性） ---------------
    ok, mism = B11._shape_check(claimed, subrec)
    if not ok:
        return _hint(table, ['P4：形状不符（shape-mismatch，双向）：' + '；'.join(mism) +
                             '（缺槽＝缺失不补 0、存储 0.0/1.0/1.5＝中性不活性，rules limits '
                             '口径；该 10 行在 CACHE 域同样过不了 P4，与域无关——批 14 扩域'
                             '后实际门披露）；' + replaced + '形状不符→仍留 hint（实际门）'],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    # --- P5 方向（批 11 同门） ----------------------------------------------------------------
    dir_bad = []
    for attr in claimed:
        raw = subrec.get(B11.ATTR_SLOT[attr])
        good = {'攻撃力': lambda v: v > 1, '防御力': lambda v: v < 1,
                '移動速度': lambda v: v > 1, 'クリティカル発生率': lambda v: v > 0,
                'クリティカル威力': lambda v: v > 1.5}[attr](raw)
        if not good:
            dir_bad.append(B11._direction_note(attr, raw))
    if dir_bad:
        return _hint(table, ['P5：方向冲突（direction-mismatch）：' + '；'.join(dir_bad)],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    # --- G1′ 句唯一（批 11 同法：NFKC 归一后恰 1 次） -------------------------------------------
    jk = lambda t: B6.unicodedata.normalize('NFKC', t).strip()
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    if jk(wb).count(jk(frag)) != 1:
        return _hint(table, [f'G1′：片段在父正文出现 {jk(wb).count(jk(frag))} 次（≠1）——'
                             '多档同文归属歧义，不晋级'],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    # --- P3 跨 cid 载体竞争守卫（键 APK；批 11 CACHE 登记分开） ---------------------------------
    others = _CLAIMS.get(('APK', sub_id), set()) - {cid}
    if others:
        return _hint(table, [f'P3：跨 cid 载体竞争：1095 sub {sub_key} 已被 cid '
                             f'{",".join(map(str, sorted(others)))} 的行主张（进程内登记；'
                             '审计实测 0 例，本守卫为防御性保留）；不晋级'],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    _CLAIMS.setdefault(('APK', sub_id), set()).add(cid)

    # --- 晋级（值行政策与批 12 完全一致：p1/p2/p3/p5/p6 按句主张活性槽出值行） -------------------
    parent_key = f'skilllist|{record_id}|{layer}'
    chain_desc = (f'{parent_key} sub[]→{sub_key}(ability1095,Always3'
                  f'"{(subrec.get("name") or "")[:20]}")')
    numeric_source = f'模板推断（批 14 APK 扩域：{chain_desc}）'
    answers = []
    claimed_slots = []
    for attr in claimed:
        param = B11.ATTR_SLOT[attr]
        claimed_slots.append(param)
        raw = subrec.get(param)
        rule = R.rule_for('skilllist', 1095, '/' + param)
        converted = R.answer_for('skilllist', 1095, '/' + param, raw, subrec)
        evidence_files = B11._field_evidence(param)
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B14_SCOPE,
            rule_key=f'skilllist|1095|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=sub_id, layer='APK',
                        record_key=sub_key),
            note=(f'模板批 14 APK 扩域值行（来源 sub＝{sub_key}，ability=1095；链：'
                  f'{chain_desc}）；基础句「{frag}」的「{attr}」→/{param} 映射'
                  '（批 11 scope §5.1 字段映射原样沿用）；'
                  f'规则键 skilllist|1095|/{param}；原值 {raw}；{B12._unit_desc(param, raw)}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）——样本域'
                  '已扩至 CACHE＋APK 两域分源（批 14：APK 52 条×5 键全域公式核对 260 项 '
                  '0 失败＋3 边界记录受控检查，无新反汇编、未实机）；'
                  '本条数值归属＝推断（模板批 14 APK 扩域：唯一 sub[]→1095 载体＋句面形状'
                  '匹配为数据侧结构对应，引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'方向审核：{B11._direction_note(attr, raw)}；'
                  '证据按字段（INFR-01）：rules.json skilllist|1095|/'
                  f'{param} evidence→'
                  + ('output/ordinary_effects/ability1095/＋output/card_comparison_cid30236/'
                     'ordinary_rules/' if param in ('param1', 'param3') else
                     'output/card_comparison_cid30236/movement|critical/（origin 相对基）')
                  + '；'
                  f'{B11._TARGET_NOTE}；'
                  f'条件逐字：句面「{frag}」；'
                  f'{_layer_note(layer)}；'
                  f'样本域：{_sample_domain_note(rule, 1095, param)}'),
            quantitative=True))
    sub_ids = [s for s in (record.get('sub') or []) if isinstance(s, int)]
    other_sub_abilities = [((data.skill(s) or {}).get('record') or {}).get('ability')
                           for s in sub_ids if s != sub_id]
    extra = [B12._B12_NATIVE_NOTE, B12._B12_ASSIGN_NOTE, EVIDENCE_NOTE_1095,
             ('B14 替换溯源：本行批 11 时因载体在 APK 层整行留 hint carrier-out-of-domain'
              '（批 12 扩域仅 CACHE 域、APK 52 条仍域外）；批 14 八键样本域扩至 CACHE＋APK '
              '两域分源后按载体层域整行晋级——行级键由 inference_b11_hint 按行级替换为 '
              'inference_b14（不双登记）；值行政策与批 12 完全一致（p5 暴击 pp 直接加算、'
              'p6 delta=原值−1.5、p2 移动乘算、p3 受伤量口径）；中性槽（p2/p3=1.0、p6=1.5、'
              'p5=0.0）不补写不出值行'),
             ('B1 防线披露：本批载体主张只认行记录（父 skilllist）自身 sub[] 数组内 ability=1095 '
              '记录；批 9 sub_effect 链、批 10 s_ability 链、批 5 job_ability 跨表链均不消费'
              '（三套 1095 相关命名空间分清，批 11 scope §0；65000001 不入本批任何值行）'),
             B11._TARGET_NOTE]
    if other_sub_abilities:
        extra.append('同父其他 sub 登记（不消费、不跨记录合并）：ability=' +
                     '、'.join(str(a) for a in other_sub_abilities) +
                     '；条件增强半句/敵侧半句（如有）归属这些 sub 为形状对照推断'
                     '（批 11 scope §2.2），本值行不吸收其数值')
    else:
        extra.append('同父其他 sub：无（父 sub[] 仅此 1 个 1095 记录）')
    extra.append(_layer_note(layer))
    claimed_sorted = sorted(set(claimed_slots))
    summary = (B14_TAG + '：自身增益值行来源＝' + chain_desc + '；值行全部「推断」，不升'
               '「确认」，不进入整行确认。本行批 11 时因载体在 APK 层留 hint '
               'carrier-out-of-domain；批 14 rules.json 1095 五键样本域扩至 CACHE＋APK 两域'
               '分源（occurrences_apk 登记）后按载体层域整行晋级，行级键按行级替换为 '
               'inference_b14（不双登记）；值行政策与批 12 完全一致。句→sub 归属为数据侧'
               '结构对应：唯一 sub[]→1095 载体＋基础句主张↔非中性活性槽形状匹配（双向）＋'
               '方向一致；装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露：'
               + '；'.join(_sample_domain_note(R.rule_for('skilllist', 1095, '/' + p), 1095, p)
                           for p in claimed_sorted) + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject='（省略主语）', attrs=list(claimed),
                claims={a: B11.ATTR_SLOT[a] for a in claimed},
                table=table, parent_ability=record.get('ability'),
                sub_record_id=sub_id, sub_layer='APK', sub_name=subrec.get('name'),
                via='own_sub_array', cross_layer=layer != 'APK',
                replaces_hint='inference_b11_hint', b14_ext=True,
                sent_no=sent_no, sent_total=sent_total)
