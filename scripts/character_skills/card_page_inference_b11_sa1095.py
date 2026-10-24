"""模板作用域推断层——批 11：普通自身增益 1095 链（skilllist 父→sub ability1095 Always3）。

设计与范围依据：``output/character_skills/inference_inventory/b11_sa1095_scope.md``
（批 11 前置审计；逐行明细 work/character_skills_b11_sa1095/b11_rows_classified.json、
代表样本 b11_samples.json——8 行独立重导核对，不依赖分类文件结论）。

链（本批命名空间，与批 5/批 8 分清，scope §0 三链表）：

* **本批**：普通 skilllist **父记录**（ability=1110 UniverseMana／26 ManaGet／
  1089 PirikaExtend／1017 StrengthJob2 等，父自身 param 全中性）的 ``sub[]`` 数组指向
  **ability=1095（Always3）** 记录；行正文片段「⟨ATTR⟩(と⟨ATTR⟩)*が上がる。」↔
  1095 sub 的非中性活性槽。**链载体＝行记录自身的 sub[] 数组**（数据侧数组字段），
  与批 9 的 sub_effect 链、批 10 的 s_ability 链、批 5 的 job_ability 跨表链互不混用。
* **批 5**：``job_ability``→``skill_ids``→``skilllist|65000001``（＝1095，跨表链）；
  65000001 **不被任何 skilllist.sub 引用**（审计实测）——两链零重叠、各自登记
  （行级键 ``inference_b5`` vs ``inference_b11``）。批 5 晋级 211 行为他表行，
  本批行宇宙（普通 skilllist 行）与之表别不同。
* **批 8**：``bossskill.s_ability``→skilllist ability=2012（暴击链），与本链无共同载体。

规则库存（rules.json 既有 5 键，本批**不登记新键**；occurrences 口径不统一——scope §1.1，
引用时显式注明）：p1/p3＝字段存在数（407，全 407 条根记录实测存在）＝**全域已确认**；
p2/p5/p6＝**已核 ID 数**（65000001；p6 加 43023601）＝**域外槽**。证据目录
``output/ordinary_effects/ability1095/``（README/trace/native_checks 32 项/5 反汇编片段）
＋复用 ``output/card_comparison_cid30236/ordinary_rules|movement|critical/``。

行集（scope §3）：全库普通 skilllist C/hint 行 12,285（Y.G. 775）；有 1095 sub
**1,070 行（Y.G. 388；父 CACHE 921＋APK 149）** 全部为干净 C 行（0 既有 hint/晋级键，
与批 1–10 无行冲突）；逐行分类：**PROMOTABLE（tier A）34 行（全库）/23（Y.G.）**，
主张恰＝{p1}；**tier B 94 行**形状完美但主张含 p2/p5/p6（规则域外）——本批按 scope
§5.3 **保守案（默认推荐）**整行留 hint ``slot-rule-not-in-domain``，不出部分值行
（「一描述一行值」纪律统一：p2/p5/p6 换算现规则已核样本不含本记录，按已确认单项纪律
不出值；规则域扩展另立批，扩展后 295 值行可解锁）；multi-1095-sub 与 direction-mismatch
结构性为 0（每父恰 1 个 1095 sub：230↔230；sub 值域实测无反向）。

晋级门（scope §5.2，批 8 P 门＋批 5 严格句纪律，逐行重验）：

* **P0 链**：行源＝普通 skilllist 记录（group ∉ {sympathy, crossworld}）；
  **行记录自身 sub[] 恰 1 个 ability=1095 记录**（≥2 → hint:multi-1095-sub；
  0 个 → 返回 None 非本批；父记录 ability==1095 → 相邻集，返回 None 另行批次——
  行源＝1095 自身记录、对象常为味方，scope §4.2/样本 8）；
* **P1 片段**：japanese 恰为基础句正则 ``^(自身の)?(5属性)(と…)*が上がる。?$``
  ——含条件节/其他主张/敵侧/味方对象的片段不进（各归 conditional/mixed/
  non-base/enemy-debuff 桶，不静默丢弃）；零主张片段（攻撃間隔/サブパーティ等）
  返回 None 不占 hint（审计口径：no-claim-fragment 630 行非候选）；
* **P2 域**：sub 记录经 CACHE 优先解析（data.skill）须落在 v3 CACHE 407 条样本域
  （APK 层 → 批 14 扩域后委托 card_page_inference_b14_apkext.handle_1095_apk 按载体层域
  接管；本模块 P2 出口的 APK 旧域外 hint 措辞已被批 14 取代）；
* **P3 唯一**：行↔父↔sub 一对一（候选池实测 0 竞争；进程内跨 cid 守卫防御性保留）；
* **P4 形状（双向）**：主张属性集 == 非中性活性槽集（中性：p1=p2=p3=p4=1、p6=1.5、
  p5 缺席；**中性不补写、缺字段不补零**（rule limits 口径）；p4/p7/p8 语义未推广、
  活性即形状不等 → hint:shape-mismatch 逐行披露未主张活性槽值）；
* **P5 方向**：上がる 句 ↔ p1>1／p3<1（受伤量口径＝防御上升）／p2>1／p5>0／p6>1.5
  （全库实测无反向值；方向门为兜底）；
* **P6 对象**：句面不得含 味方（基础句正则已保证）；**对象依据＝rules.json target
  逐字「装有此能力的接受者自身；安装来源/资格另论」**——本家族句面省略主语
  （无「自身の」前缀），逐行披露；
* **G1′ 句唯一**：japanese 在父正文（\\n 还原后）恰 1 次子串（审计候选 186 行 186/186
  通过；失败 → hint 归属歧义不晋级）。

值行（tier A；rule_key 只允许 ``skilllist|1095|/param1|/param3``；经 rules.py 既有
1095 换算器出值）：攻撃力→/param1（攻击×p1，本项提高 (p1−1)×100%）；防御力→/param3
（受伤量×p3，本项减伤 (1−p3)×100%，**不是固定防御量**）。p2/p5/p6 不出值行（域外槽，
保守案）；p0 全缺（1095 无时限槽）、p4/p7/p8 语义未推广，均不消费。

硬边界（沿用批 9/10 口径）：

* 只升「推断」：值行 numeric/association 一律「推断」；行级标注
  「推断（模板批 11 自身增益 1095）」、evidence_scope=TEMPLATE_BATCH11_SA1095、行级
  metadata 键 ``inference_b11``；不进整行确认；「基础句↔Always(1095)、条件句↔其他 sub
  的分工为数据侧形状对照＋条件结构对应，无引擎侧装载原生核实」（scope §5.4 诚实声明，
  b5 §5.5-4 同款）——永不据此升「确认」。
* **规则本体与本条归属分开披露**：值行 note 固定写明「规则本体：已确认（静态及受控
  原生局部规则）——指规则本身；本条数值归属＝推断（模板批 11），不升确认」。
* **证据按字段**（INFR-01）：值行 evidence 取 rules.json skilllist|1095|/paramN 的
  evidence（origin output/card_comparison_cid30236/field_dictionary.json；ordinary_rules/
  movement/ critical/ 等相对路径解析根＝output/card_comparison_cid30236/，
  ../ordinary_effects/ ability1095/ 解析为 output/ordinary_effects/ability1095/）；
  存在性检查，缺失显式失败。
* **样本域披露按登记口径**（INFR-02）：p1/p3 occurrences=407（存在数口径）、
  p2/p5/p6 occurrences=1/1/2（**已核 ID 数口径**：65000001/43023601，非本 sub）——
  行级键级汇总披露一次并显式注明两种口径不统一（scope §1.1/§6）；本行来源 sub 记录
  未逐条核对，不属逐记录确认。
* **条件文本逐字入 note**；中性槽不补写；同父其他 sub（非 1095）登记不消费，
  条件增强半句/敵侧半句归属其他 sub 为形状对照推断。
* **不跨记录合并**：既有批 1–10 晋级行与 hint 键不动；批 5 65000001 链不入本批任何
  值行。
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import rules as R
import card_page_inference_b6_bossbuff as B6

B11_TAG = '推断（模板批 11 自身增益 1095）'
B11_SCOPE = 'TEMPLATE_BATCH11_SA1095'
B11_FAMILY = ('普通自身增益家族・ability1095 Always3 载体（「⟨ATTR⟩(と⟨ATTR⟩)*が上がる。」'
              '基础句；skilllist 父记录 sub[]→skilllist ability1095 载体；句面省略主语，'
              '对象由链 target=装有者自身）')

# P2/P3：行记录表——普通 skilllist 行（group ∉ {sympathy, crossworld} 由接线门保证）。
TABLES = ('skilllist',)

# 5 属性→1095 sub 槽映射（scope §5.1，全部已确认规则）。
ATTR_SLOT = {'攻撃力': 'param1', '防御力': 'param3', '移動速度': 'param2',
             'クリティカル発生率': 'param5', 'クリティカル威力': 'param6'}
# 中性值（rule limits 口径：中性不补写、缺字段不补零；p5 中性=缺席）。
NEUTRAL = {'param1': 1, 'param2': 1, 'param3': 1, 'param4': 1, 'param6': 1.5}
# 基础句正则（audit classify_b11_rows.py BASE_RE 逐字沿用）。
BASE_RE = re.compile(
    r'^(?:自身の)?(攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力)'
    r'(?:と(?:攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力))*が上がる。?$')
ATTR_RE = re.compile(r'攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力')
COND_RE = re.compile(r'より前に|より後ろに|いると効果|以上の時|以下の時|敵陣に|自陣に|'
                     r'いる場合|たび、|たびに効果|止まって|移動する|所持していると|'
                     r'効果が上がり|効果が上がる|効果時間|ほど、|なければ|いると、')
OTHER_CLAIM_RE = re.compile(r'攻撃間隔|回復|ＨＰ|HP|弾き|貫通|弾速|マナ|ゴールド|経験値|'
                            r'宝箱|状態異常|ダウン|範囲|射撃|接触|通常攻撃力|'
                            r'遠距離|近接|スクラップ')
ENEMY_RE = re.compile(r'攻撃した敵の|敵の攻撃力|敵の防御力')
# 现规则全域槽（occurrences=407＝407 条根记录全存在）；p2/p5/p6 已核 ID 数口径（域外）。
DOMAIN_SLOTS = {'param1', 'param3'}
RULED_ID_SLOTS = {'param2': ['65000001'], 'param5': ['65000001'],
                  'param6': ['43023601', '65000001']}

# ---- INFR-01：rules.json skilllist|1095|/paramN 的 evidence 解析（本批不登记新键， ----
# ---- 复用既有登记；相对路径解析根＝规则 origin output/card_comparison_cid30236/） ----
_CARD_COMPARISON_ROOT = 'output/card_comparison_cid30236/'
_EVIDENCE_CACHE = {}


def _resolve_field_evidence(param):
    """按字段把 rules.json rule["evidence"] 解析为项目根相对路径，返回文件列表。
    惯例与批 1 试点（card_page_inference_1017.py）同：'../'→output/，其余相对 origin
    （card_comparison_cid30236）。"""
    rule = R.rule_for('skilllist', 1095, '/' + param)
    files = []
    for entry in (rule or {}).get('evidence') or []:
        e = str(entry)
        if e.startswith('../'):
            files.append('output/' + e[3:])
        else:
            files.append(_CARD_COMPARISON_ROOT + e)
    # p1/p3 证据＝ability1095 三件（本能力）＋ordinary_rules 三件（param1/param3 通用规则
    # 证据，批 1 试点裁定口径）；缺失 ability1095 件或出现第三种前缀即异常。
    expected = ('output/ordinary_effects/ability1095/' if param in ('param1', 'param3')
                else _CARD_COMPARISON_ROOT)
    if (not files
            or any(not (p.startswith(expected) or p.startswith(_CARD_COMPARISON_ROOT))
                   for p in files)
            or (param in ('param1', 'param3')
                and not any(p.startswith(expected) for p in files))):
        raise ValueError(f'批 11 证据解析异常（INFR-01）：skilllist|1095|/{param} 的 rules.json '
                         f'evidence 未解析出 {expected} 下的文件，实际 {files!r}')
    return files


def _field_evidence(param):
    if param not in _EVIDENCE_CACHE:
        files = _resolve_field_evidence(param)
        missing = [p for p in files if not Path(p).is_file()]
        if missing:
            raise FileNotFoundError(f'批 11 证据文件缺失（INFR-01）：{missing}')
        _EVIDENCE_CACHE[param] = files
    return _EVIDENCE_CACHE[param]


# ---- P2 样本域：当前 v3 CACHE 普通 ability1095 的 407 条根记录 ----
def _domain1095(data):
    return {sid for sid, (i, rec) in data.cache_skill.items()
            if (rec or {}).get('ability') == 1095}


_ORIGIN_FALLBACK = 'output/card_comparison_cid30236/field_dictionary.json'


def _rule_origin(rule):
    # field_dictionary.json 既有键经 rules.py rule_for 不带 origin；rules.json 登记处
    # origin=该文件（scope §1.1）。缺省时按登记处回退，不写 None。
    return rule.get('origin') or _ORIGIN_FALLBACK


def _sample_domain_note(rule):
    """单键口径（scope §1.1 登记；批 12 扩域后五键统一为字段存在数口径——
    批 11 时的 p2/p5/p6「已核 ID 数」1/1/2 已由批 12 取代，历史口径见 rules.json
    limits「批12扩域」注记；本句动态引用 rules.json 登记值）。"""
    return (f'该规则登记 occurrences={rule.get("occurrences")}（origin '
            f'{_rule_origin(rule)}；口径：批 12 扩域后 p1/p2/p3/p5/p6 五键统一为'
            '字段存在数口径（p1/p3=407、p2=407、p5=211、p6=407）；批 11 时 p2/p5/p6 '
            '为已核 ID 数口径（65000001；p6 加 43023601）已由批 12 扩域取代；'
            '本行来源 sub 记录未逐条核对，'
            '按规则适用条件披露，不属逐记录确认')


def _sample_domain_summary():
    """行级适用范围披露：五键 occurrences 键级汇总一次＋口径注明（B10-RV-03/-04 同法；
    批 12 扩域后五键统一为字段存在数口径，动态引用 rules.json 登记值；批 14 扩域后另
    披露 occurrences_apk）。"""
    parts = []
    for p in ('param1', 'param2', 'param3', 'param5', 'param6'):
        r = R.rule_for('skilllist', 1095, '/' + p)
        parts.append(f'/{p}={r.get("occurrences")}+{r.get("occurrences_apk")}')
    return ('（键级 occurrences（CACHE）＋occurrences_apk（APK）汇总披露一次，origin '
            'rules.json 登记值；批 12 扩域后 CACHE 侧五键均为字段存在数口径——批 11 时 '
            'p2/p5/p6 已核 ID 数口径（65000001；p6 加 43023601）已由批 12 扩域取代，历史'
            '口径见 rules.json limits 注记；批 14 扩域（2026-10-22）：APK 侧 52 条已分配'
            '（occurrences_apk 登记，中性口径：p5 存储 0.0 不计、p2/p3=1.0/p6=1.5 中性'
            '计入）、两域分源不得跨层取值）：'
            f'{("、".join(parts))}；样本域＝CACHE 普通 skilllist '
            'ability1095（Always3）的 407 条根记录＋APK 主表 ability1095 的 52 条记录'
            '（两域分源）；'
            '本行来源 sub 记录未逐条核对，按规则适用条件披露，不属逐记录确认')


_TARGET_NOTE = ('对象披露（双源）：句面无对象词（本家族省略主语——scope §2.2 基础句形态）；'
                '链目标＝rules.json target 逐字「装有此能力的接受者自身；安装来源/资格另论」'
                '→对象=自身')

_NATIVE_NOTE = ('记录侧＝1095 GetAbilityAttack/GetAbilityDefence 数据路径'
                '（output/ordinary_effects/ability1095/ 既有证据：attack_getter/attack_multiply/'
                'attack_dispatch/defence_getter_multiply/defence_dispatch 5 片段＋'
                'native_checks 32 项＝8 ID×2 字段×资格真假；复用未重跑）；'
                '父技能 sub[] 如何安装 1095 到角色（装载路径）无原生核实——'
                '行保持推断（scope §6 边界）')

_ASSIGN_NOTE = ('跨记录归属依据（b11 scope §5.2/§5.4）：句→1095 sub 为数据侧结构对应：'
                '行记录自身 sub[] 恰 1 个 ability=1095 记录（每父恰 1：230 父↔230 sub，'
                '无共享；65000001 不被任何 skilllist.sub 引用——批 5 跨表链零重叠）＋'
                '基础句主张属性集↔sub 非中性活性槽集双向相等（P4）＋方向一致（P5）；'
                '基础句↔Always(1095)、条件句↔其他 sub 的分工为数据侧形状对照＋条件结构'
                '对应，无引擎侧装载原生核实——本条归属不因晋级升「确认」')


def _hint(table, reasons, subject=None, attrs=(), sent_no=None, sent_total=0, **extra):
    out = dict(kind='hint', reasons=reasons, subject=subject, attrs=list(attrs), table=table,
               sent_no=sent_no, sent_total=sent_total)
    out.update(extra)
    return out


def _active_slots(sub):
    """1095 sub 非中性活性槽：已知 5 槽＋未推广槽（p4/p7/p8）（audit 同法）。"""
    known, unknown = [], []
    for attr, slot in ATTR_SLOT.items():
        raw = sub.get(slot)
        present = raw is not None
        if slot == 'param5':
            act = present and raw != 0
        else:
            act = present and raw != NEUTRAL.get(slot)
        if act:
            known.append(attr)
    if sub.get('param4') not in (None, 1):
        unknown.append('param4')
    for k in ('param7', 'param8'):
        if sub.get(k) not in (None, 0):
            unknown.append(k)
    return known, unknown


def _shape_check(claimed, sub):
    """P4 形状（双向）：主张属性集 ⇔ 活性槽集；未推广槽活性即不等。返回 (ok, mism)。"""
    known, unknown = _active_slots(sub)
    mism = []
    claim_set = set(claimed)
    known_set = set(known)
    if claim_set - known_set:
        mism.append('句主张 %s 但 1095 sub 槽不活性 %s' % (
            sorted(claim_set - known_set),
            {ATTR_SLOT[a]: sub.get(ATTR_SLOT[a]) for a in sorted(claim_set - known_set)}))
    if known_set - claim_set:
        mism.append('1095 sub 活性槽 %s 未被句主张 %s' % (
            {ATTR_SLOT[a]: sub.get(ATTR_SLOT[a]) for a in sorted(known_set - claim_set)},
            sorted(known_set - claim_set)))
    if unknown:
        mism.append('未推广槽活性 p4/p7/p8=%s（语义无规则，形状不可等）' % (
            {s: sub.get(s) for s in unknown},))
    return (not mism), mism


def _direction_note(attr, raw):
    if attr == '攻撃力':
        return (f'方向一致（原值 {raw}>1：攻击因子乘原值＝提高；本项提高 (原值−1)×100%）'
                if raw > 1 else f'方向冲突（原值 {raw!r} 与攻撃力「上がる」冲突，需>1）')
    if attr == '防御力':
        return (f'方向一致（原值 {raw}<1：受伤量乘原值＝受伤量降＝防御上升；本项减伤 '
                f'(1−原值)×100%；不是固定防御量）'
                if raw < 1 else f'方向冲突（原值 {raw!r} 与防御力「上がる」冲突，受伤量口径需<1）')
    if attr == '移動速度':
        return (f'方向一致（原值 {raw}>1：移动因子乘原值＝提高）'
                if raw > 1 else f'方向冲突（原值 {raw!r} 与移動速度「上がる」冲突，需>1）')
    if attr == 'クリティカル発生率':
        return (f'方向一致（原值 {raw}>0：暴击概率直接加算，不套 Always3 减 1.5 规则）'
                if raw > 0 else f'方向冲突（原值 {raw!r} 与暴击率「上がる」冲突，需>0）')
    return (f'方向一致（原值 {raw}>1.5：暴伤系数 delta=原值−1.5）'
            if raw > 1.5 else f'方向冲突（原值 {raw!r} 与暴伤「上がる」冲突，需>1.5）')


def _promote(frag, table, layer, record_id, cid, claimed, subject_phrase, sub_id, subrec,
             parent_ability, other_sub_abilities, sent_no, sent_total):
    """晋级行（tier A）：值行全部来自唯一 1095 sub（主张⊆{param1,param3}）。"""
    sub_key = f'skilllist|{sub_id}|CACHE'
    parent_key = f'skilllist|{record_id}|{layer}'
    chain_desc = (f'{parent_key} sub[]→{sub_key}'
                  f'(ability1095,Always3"{(subrec.get("name") or "")[:20]}")')
    numeric_source = f'模板推断（批 11 SA1095：{chain_desc}）'
    answers = []
    for attr in claimed:
        param = ATTR_SLOT[attr]
        raw = subrec.get(param)
        rule = R.rule_for('skilllist', 1095, '/' + param)
        converted = R.answer_for('skilllist', 1095, '/' + param, raw, subrec)
        evidence_files = _field_evidence(param)
        if param == 'param1':
            unit_desc = '单位：本项攻击倍率（攻击因子乘原值；提高 (原值−1)×100%；无量纲倍率，非百分点加算）'
        else:
            unit_desc = ('单位：受伤量倍率（受伤量乘原值；本项减伤 (1−原值)×100%；'
                         '不是固定防御量）')
        answers.append(dict(
            value=converted['value_text'],
            quantity_kind=converted.get('quantity_kind'), unit=converted.get('unit'),
            raw_value=raw, field_path='/' + param,
            numeric_source=numeric_source, numeric_evidence='推断',
            association_evidence='推断', evidence_scope=B11_SCOPE,
            rule_key=f'skilllist|1095|/{param}',
            rule_body_status=rule.get('status'), rule_status=rule.get('status'),
            conversion=rule.get('conversion'), base_definition=rule.get('base_definition'),
            conditions=rule.get('applicability'), rule_limits=rule.get('limits'),
            evidence=list(evidence_files),
            source=dict(table='skilllist', record_id=sub_id, layer='CACHE',
                        record_key=sub_key),
            note=(f'模板批 11 SA1095 值行（来源 sub＝{sub_key}，ability=1095；链：'
                  f'{chain_desc}）；基础句「{frag}」的「{attr}」→/{param} 映射'
                  '（scope §5.1 字段映射）；'
                  f'规则键 skilllist|1095|/{param}；原值 {raw}；{unit_desc}；'
                  f'规则本体：{rule.get("status")}（rules.json 登记口径，指规则本身）；'
                  '本条数值归属＝推断（模板批 11：唯一 sub[]→1095 载体＋句面形状匹配为'
                  '数据侧结构对应，引擎侧行→载体装载路径无原生核实），不升确认；'
                  f'方向审核：{_direction_note(attr, raw)}；'
                  '证据按字段（INFR-01）：rules.json skilllist|1095|/'
                  f'{param} evidence→output/ordinary_effects/ability1095/（README/trace/'
                  'native_checks 32 项/5 反汇编片段）＋复用 output/card_comparison_cid30236/'
                  'ordinary_rules/；'
                  f'{_TARGET_NOTE}；'
                  f'条件逐字：句面「{frag}」；'
                  f'样本域：{_sample_domain_note(rule)}'),
            quantitative=True))

    # --- 晋级行注记（不改变「推断」档位） --------------------------------------------------
    extra = [
        _NATIVE_NOTE,
        _ASSIGN_NOTE,
        ('B1 防线披露：本批载体主张只认行记录（父 skilllist）自身 sub[] 数组内 ability=1095 '
         '记录；批 9 sub_effect 链、批 10 s_ability 链、批 5 job_ability 跨表链均不消费'
         '（三套 1095 相关命名空间分清，scope §0；65000001 不入本批任何值行）'),
        _TARGET_NOTE,
    ]
    if other_sub_abilities:
        extra.append('同父其他 sub 登记（不消费、不跨记录合并）：ability=' +
                     '、'.join(str(a) for a in other_sub_abilities) +
                     '；条件增强半句/敵侧半句（如有）归属这些 sub 为形状对照推断'
                     '（scope §2.2），本值行不吸收其数值')
    else:
        extra.append('同父其他 sub：无（父 sub[] 仅此 1 个 1095 记录）')
    extra.append('中性槽不补写、缺字段不补零（rule limits 口径）；1095 无 param0 时限槽'
                 '（审计 0/407）；p4/p7/p8 语义未推广（本行 sub 未活性，活性即形状不符留 hint）')
    summary = (B11_TAG + '：自身增益值行来源＝' + chain_desc + '；值行全部「推断」，不升'
               '「确认」，不进入整行确认。句→sub 归属为数据侧结构对应：唯一 sub[]→1095 '
               '载体＋基础句主张↔非中性活性槽形状匹配（双向）＋方向一致；'
               '基础句↔Always(1095)、条件句↔其他 sub 分工为形状对照＋条件结构对应，'
               '装载路径无原生核实。'
               + (f'正文句序：本句位于第 {sent_no} 句／共 {sent_total} 句（以「。」切分）。'
                  if sent_no else '正文句序未能定位。')
               + '适用范围披露' + _sample_domain_summary() + '。')
    return dict(kind='promote', answers=answers, summary_reason=summary, extra_reasons=extra,
                subject=subject_phrase, attrs=list(claimed),
                claims={a: ATTR_SLOT[a] for a in claimed},
                table=table, parent_ability=parent_ability,
                sub_record_id=sub_id, sub_layer='CACHE', sub_name=subrec.get('name'),
                via='own_sub_array',
                sent_no=sent_no, sent_total=sent_total)


# ---- P6 跨 cid 载体竞争守卫（进程内登记；审计候选池实测 0 例）----
_CLAIMS = {}


def evaluate(record: dict, frag: str, table: str, group: str | None = None,
             layer: str | None = None, record_id=None, text: str | None = None,
             data=None, cid=None):
    """对一行做批 11 SA1095 审核，返回 None（不属本批范围）或审核结果 dict。

    record：行源父 skilllist 记录 dict（含 sub[]）；frag：行片段；group：组 id
    （sympathy/crossworld 不属本批，接线门亦保证）；data/cid：页级 Inputs 与 cid。
    返回非 None ⇔ 行父记录 sub[] 上存在 ability=1095 记录（本批候选）。
    """
    if data is None or cid is None or table not in TABLES or not isinstance(record, dict):
        return None
    j = frag
    # 相邻集排除：行源＝1095 自身记录（scope §4.2；对象常为味方、多重不符，另行批次）
    if record.get('ability') == 1095:
        return None
    sub_ids = [s for s in (record.get('sub') or []) if isinstance(s, int)]
    subs1095 = []
    for sid in sub_ids:
        w = data.skill(sid)
        if w is not None and (w.get('record') or {}).get('ability') == 1095:
            subs1095.append((sid, w['layer'], w['record']))
    if not subs1095:
        return None  # 无 1095 sub：非本批（审计 no-1095-sub 10,845 行）
    # --- 句序披露（批 9/10 同法） -------------------------------------------------------------
    body = (text or '').replace('\\n', '\n')
    cut = body.find('[i][c]')
    wb = body[:cut] if cut >= 0 else body
    _sents = [s for s in re.findall(r'[^。]*。', wb)]
    sent_no = next((i + 1 for i, s in enumerate(_sents) if frag.strip() in s), None)
    sent_total = len(_sents)

    if len(subs1095) > 1:
        det = '；'.join(f'skilllist|{sid}|{lay}' for sid, lay, _r in subs1095)
        return _hint(table, [f'P3：父记录 sub[] 上 {len(subs1095)} 个 ability=1095 记录'
                             f'（归属歧义，multi-1095-sub）：{det}'
                             '——审计实测结构性为 0（每父恰 1），本守卫为防御性保留；'
                             '不晋级'],
                     sent_no=sent_no, sent_total=sent_total)
    sid, sub_layer, subrec = subs1095[0]
    # --- P1 片段主张解析（audit classify 同法；零主张片段不占 hint） ---------------------------
    claimed = list(dict.fromkeys(ATTR_RE.findall(j)))
    if not claimed:
        return None  # no-claim-fragment（攻撃間隔/サブパーティ/回復等）：非候选，不占 hint
    if ENEMY_RE.search(j):
        return _hint(table, ['敌侧主张：「攻撃した敵の…」＝敵側（批 9 载体族），非 1095 '
                             '自身链（enemy-debuff-fragment）——1095 sub 非本句载体，'
                             '不跨记录合并、不晋级'],
                     sent_no=sent_no, sent_total=sent_total)
    m = BASE_RE.match(j)
    if not m:
        cond = COND_RE.search(j)
        other = OTHER_CLAIM_RE.search(j)
        kind = 'conditional-fragment' if cond else ('mixed-fragment' if other
                                                    else 'non-base-shape')
        detail = {'conditional-fragment': '条件增强半句（条件节）——归属在同父其他 sub/跨行'
                                          '耦合（scope §2.2），不归 1095 sub',
                  'mixed-fragment': '基础主张＋其他主张（攻撃間隔/回復/状態異常等）同句——'
                                    '整句不可全归 1095 sub，不跨记录合并',
                  'non-base-shape': '非基础句形态（味方对象句/付与効果句等）'}[kind]
        return _hint(table, [f'P1：非基础句（{kind}）：{detail}；1095 sub 存在但本片段'
                             '不晋级（留 hint 不静默丢弃）'],
                     sent_no=sent_no, sent_total=sent_total)
    # --- P6 对象（基础句形态下句面无味方；防御性保留） ------------------------------------------
    if '味方' in j and '自身' not in j:
        return _hint(table, ['P6：句面含「味方」——1095 规则 target=装有者自身，对象冲突'
                             '（object-ally），不晋级'],
                     subject='味方', attrs=claimed, sent_no=sent_no, sent_total=sent_total)
    # --- P2 域：sub 须在 v3 CACHE 407 条样本域 ------------------------------------------------
    # 批 14 APK 扩域（2026-10-22）：rules.json 1095 五键样本域扩至 CACHE＋APK 两域分源
    # （occurrences_apk 登记）后，APK 层 1095 载体（52 条扩后域）在此委托批 14 模块按
    # 载体层域接管：P4/P5/G1′/P3 门控后晋级（行级键 inference_b14，替换本批旧域外 hint，
    # 不双登记）或 hint（实际门）。
    if sub_layer != 'CACHE' or sid not in _domain1095(data):
        if sub_layer == 'APK':
            import card_page_inference_b14_apkext as B14
            return B14.handle_1095_apk(record=record, frag=j, table=table, layer=layer,
                                       record_id=record_id, cid=cid, text=text, data=data,
                                       sent_no=sent_no, sent_total=sent_total,
                                       sub_id=sid, subrec=subrec)
        p_all = ('；'.join(f'/{p}={subrec.get(p)!r}' for p in
                          ('param1', 'param2', 'param3', 'param5', 'param6')))
        return _hint(table, [f'P2：唯一 sub[]→skilllist ability=1095（Always3）载体 '
                             f'skilllist|{sid}|{sub_layer} 在 APK 52 条扩后域与 CACHE 407 条'
                             '样本域之外（防御性分支：批 14 扩域后 APK 载体已委托批 14 接管，'
                             '本分支理论不可达）；'
                             f'sub 关键槽：{p_all}'],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    # --- P4 形状（双向＋未推广槽） --------------------------------------------------------------
    ok, mism = _shape_check(claimed, subrec)
    if not ok:
        return _hint(table, ['P4：形状不符（shape-mismatch，双向）：' + '；'.join(mism) +
                             '（缺槽＝缺失不补 0，rules limits 口径；主张在条件半句行的'
                             '载体主张不归本片段——批 8 同法）'],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    # --- P5 方向 ----------------------------------------------------------------------------------
    dir_bad = []
    for attr in claimed:
        raw = subrec.get(ATTR_SLOT[attr])
        good = {'攻撃力': lambda v: v > 1, '防御力': lambda v: v < 1,
                '移動速度': lambda v: v > 1, 'クリティカル発生率': lambda v: v > 0,
                'クリティカル威力': lambda v: v > 1.5}[attr](raw)
        if not good:
            dir_bad.append(_direction_note(attr, raw))
    if dir_bad:
        return _hint(table, ['P5：方向冲突（direction-mismatch）：' + '；'.join(dir_bad)],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    # --- G1′ 句唯一（frag 在父正文恰 1 次） --------------------------------------------------------
    jk = lambda t: B6.unicodedata.normalize('NFKC', t).strip()
    n_hits = jk(wb).count(jk(frag))
    if n_hits != 1:
        return _hint(table, [f'G1′：片段在父正文出现 {n_hits} 次（≠1）——多档同文归属歧义，'
                             '不晋级'],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    # --- P3 跨 cid 载体竞争守卫（审计候选池实测 0 例） ----------------------------------------------
    others = _CLAIMS.get(sid, set()) - {cid}
    if others:
        return _hint(table, [f'P3：跨 cid 载体竞争：1095 sub skilllist|{sid}|CACHE 已被 '
                             f'cid {",".join(map(str, sorted(others)))} 的行主张'
                             '（进程内登记；审计实测 0 例，本守卫为防御性保留）；不晋级'],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total)
    # --- 分级：主张槽是否全部在现规则域（p1/p3=407 存在数全域；p2/p5/p6 已核 ID 数域外） -----------
    beyond = sorted(s for s in (ATTR_SLOT[a] for a in claimed) if s not in DOMAIN_SLOTS)
    if beyond:
        det = '；'.join(f'/{s} 现规则已核 ID 仅 {RULED_ID_SLOTS[s]}（非本 sub '
                        f'skilllist|{sid}）' for s in beyond)
        return _hint(table, [f'P4 形状完美但部分槽规则域外（slot-rule-not-in-domain，tier B，'
                             f'保守案 scope §5.3）：{det}；该属性槽换算已核样本不含本记录，'
                             '按「一描述一行值」纪律不出部分值行，整行留 hint 待规则域扩展'
                             '（扩展后可解锁；p2/p5/p6 occurrences=1/1/2 为已核 ID 数口径）；'
                             '不静默丢弃'],
                     subject='（省略主语）', attrs=claimed, sent_no=sent_no,
                     sent_total=sent_total, tier='B', beyond_slots=beyond)
    _CLAIMS.setdefault(sid, set()).add(cid)
    other_sub_abilities = [((data.skill(s) or {}).get('record') or {}).get('ability')
                           for s in sub_ids if s != sid]
    return _promote(frag, table, layer, record_id, cid, claimed, '（省略主语）',
                    sid, subrec, record.get('ability'), other_sub_abilities,
                    sent_no, sent_total)
