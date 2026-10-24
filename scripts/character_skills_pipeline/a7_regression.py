"""A7 规则层回归用例（P4 目标整改；七类预期语义，独立于账本自检运行）。

用例语义来自整改任务书 §四 A7 与第三方审查 GOAL_ALIGNMENT.md 的独立主张，
预期值按语义独立写出（不读实现内部状态做预期）；每例运行 effect_ledger.analyze_row
（账本派生层）并对断言结果。含真实数据用例（重建前后证据）与合成用例。

用法：./.venv/Scripts/python.exe -B output/character_skills/effect_ledger/acceptance/a7_regression.py
（或 work/character_skills_goal_rectification/a7_regression.py——两副本用例同一套 29 例）

acceptance 副本路径修正（20261023 文档债务修正包，A7-ACCEPTANCE-COPY-STALE）：ROOT 不再
固定 parents[2]（acceptance 目录层级更深，原写法解析到 output/character_skills →
ModuleNotFoundError: effect_ledger），改为向上查找含
scripts/character_skills/effect_ledger.py 的祖先目录；结果写本目录 a7_regression_results.json。
"""
import collections
import json
import sys
from pathlib import Path


def _find_root():
    here = Path(__file__).resolve()
    for cand in here.parents:
        if (cand / 'scripts' / 'character_skills' / 'effect_ledger.py').exists():
            return cand
    raise SystemExit('未找到仓库根（缺少 scripts/character_skills/effect_ledger.py）')


ROOT = _find_root()
sys.path.insert(0, str(ROOT / 'scripts' / 'character_skills'))
import os
os.chdir(ROOT)
from effect_ledger import analyze_row

results = []


def case(name, expect_desc, got, expect, ok):
    results.append(dict(case=name, expect=expect_desc, got=got, passed=bool(ok)))


# ---- 用例 1（复合句只补部分值后仍待办）：349 f3 的批 8 阶段形态（重建前快照真实数据）----
# 语义（GOAL_ALIGNMENT.md G01）：句主张攻/防/移/双暴击/时间，answers 仅两项暴击值
# → 该行必须仍是待办（部分），4 项未解决不得清零。
syn349 = dict(
    row_id='SYN-349-f3', cid=349, group='special_move', stage='档位 1', level=None,
    reference_field='pattern0', fragment_index=3,
    japanese='その後、味方全体の攻撃力と防御力と移動速度とクリティカル発生率とクリティカル威力が一定時間上がる。',
    original_numeric_items=[], answers=[
        dict(value='暴击率 +30 个百分点（对 0 的加算增量）', quantity_kind='暴击概率加算贡献',
             unit='个百分点', raw_value=0.3, field_path='/param4',
             rule_key='skilllist|2012|/param4', numeric_evidence='推断',
             association_evidence='推断', numeric_source='模板推断（批 8 暴击 2012 链）',
             source=dict(table='skilllist', record_id=40034914, layer='CACHE')),
        dict(value='暴击伤害系数 +0.3', quantity_kind='暴击伤害系数加算贡献', unit='系数增量',
             raw_value=0.3, field_path='/param5', rule_key='skilllist|2012|/param5',
             numeric_evidence='推断', association_evidence='推断',
             numeric_source='模板推断（批 8 暴击 2012 链）',
             source=dict(table='skilllist', record_id=40034914, layer='CACHE')),
    ])
r = analyze_row(syn349)
n_unres = sum(1 for e in r['effects'] if e['status'] == 'unresolved')
bp = r['breakpoint']
case('A7-1 复合句只补部分值后仍待办',
     '未解决=4（攻/防/移/时长）、断点=True、行级=部分',
     dict(unresolved=n_unres, breakpoint=bp),
     dict(unresolved=4, breakpoint=True),
     n_unres == 4 and bp)

# ---- 用例 2（非 C 行仍待办）：同上合成行 row_class=A —— 账本不看 row_class，----
# A 行未解决效果照常入队（对照：build_inventory 旧版对非 C 行 continue 的缺陷）。
case('A7-2 非C行仍待办（A 行未解决照常入队）',
     'A 行合成行产生未解决效果条目（backlog kind=effect 语义）',
     dict(unresolved_effects=[e['effect_id'] for e in r['effects'] if e['status'] == 'unresolved'][:2]),
     dict(nonempty=True),
     any(e['status'] == 'unresolved' for e in r['effects']))

# ---- 用例 3（补齐后退出未解队列）：真实重建后 349 f3 —— 六主张全部有答案、----
# 无拆分标志 → 行级完整、不在 backlog（重建后 pages 实测）。
pages = ROOT / 'output' / 'character_skills' / 'pages'
card = json.loads((pages / '349' / 'card.json').read_text(encoding='utf-8-sig'))
row = next(rr for g in card['groups'] for s in g['skills'] for rr in s['rows']
           if rr['row_id'] == '349-special_move-special_move-pattern0-lvorder0-f3')
r3 = analyze_row(row)
n_ans = sum(1 for e in r3['effects'] if e['status'] == 'has_answer')
case('A7-3 补齐后退出未解队列（真实 349 f3 重建后）',
     'has_answer=6、未解决=0、无拆分标志（退出队列前提）',
     dict(has_answer=n_ans, unresolved=sum(1 for e in r3['effects'] if e['status'] == 'unresolved'),
          flags=[f['code'] for f in r3['split_flags']]),
     dict(has_answer=6, unresolved=0, flags=[]),
     n_ans == 6 and not any(e['status'] == 'unresolved' for e in r3['effects']) and not r3['split_flags'])

# ---- 用例 4（拆分未完成不得完整）：真实重建后带 S2 标志的行（原文有数字、答案也存在）----
# 语义：原文数字语义未确认（数量角色为词面启发式）→ 不得判完整，须拆分待核查。
# DS-GR-04 修复（20261023）：不再测试内自算「完整=not flags」同义反复——直接调用账本真实
# 行级派生 effect_ledger._emit_row（与 ledger.jsonl 生成同一路径），断言其产出的
# ledger_row_status 为「拆分待核查」（不为完整）。
sys.path.insert(0, str(ROOT / 'scripts' / 'character_skills'))
import effect_ledger as EL
card2 = json.loads((pages / '2243' / 'card.json').read_text(encoding='utf-8-sig'))
row2 = next(rr for g in card2['groups'] for s in g['skills'] for rr in s['rows']
            if rr['row_id'] == '2243-ability-ability-skillid_1_-lvorder0-f0')
desc4, eff4 = [], []
EL._emit_row(row2, {'table': 'ability', 'skill': None}, False,
             dict(snapshot_id='a7-case4', campaign_signature=None, rules_json_sha256_16=None, pages_root='output/character_skills/pages'), 'a7-case4', desc4, eff4)
derived_status4 = desc4[0]['ledger_row_status']
page_answers4 = len(row2['answers'])   # 「有答案」＝页面行携带答案（开局玛那），非效果级匹配数
s2 = any(f['code'] == 'S2_unconfirmed_numbers' for f in desc4[0]['split_flags'])
flags4 = [f['code'] for f in desc4[0]['split_flags']]
# R2 复审整改第二轮（20261023）：2243 的数字（マナ1つ，数量角色）在角色绑定规则下已
# 能映射到其结构化数量答案——S2 解除；行仍因 S1/S3（无效果主张/未覆盖子句）保持
# 拆分待核查。用例语义「有答案且有数字的行不得判完整」不变；S2 专项由 A7-17/A7-21 承担。
case('A7-4 拆分未完成不得完整（2243 有答案且有数字，真实行级派生）',
     '调用账本 _emit_row 真实派生：页面行有答案（≥1）且有拆分标志 ⇒ '
     'ledger_row_status=拆分待核查（不得完整）；第二轮下该行标志为 S1/S3'
     '（数字已按角色绑定映射，S2 解除）',
     dict(page_answers=page_answers4, flags=flags4, ledger_row_status=derived_status4),
     dict(page_answers='>=1', ledger_row_status='拆分待核查', has_split_flags=True),
     page_answers4 >= 1 and flags4 and derived_status4 == '拆分待核查')

# ---- 用例 5（hint 变化不丢待办）：批 17（20261023）后 30229 f0 已由槽位分区晋级
# （原 b15_hint 行清零），改用当前 pages 中仍带 inference_b15_hint 的真实行（确定性
# 取 cid 升序首行）——语义不变：行级 hint 键存在 ⇒ 账本有待办踪迹（未解决效果或拆分标志）。
# 批 17（20261023）后 58 条 b15_hint 行全部晋级清零（30 H1＋28 H2/b14）——本用例改用
# 当前 pages 仍带任一 hint 键的真实行（确定性取 cid 升序首个带 hint 行；批 17 后存量
# hint=b6 315/b8 233/b7 687 等），语义不变：行级 hint 键存在 ⇒ 账本有待办踪迹。
_h_rows = []
for _d in sorted(pages.iterdir(), key=lambda p: (len(p.name), p.name)):
    if not (_d.is_dir() and (_d / 'card.json').is_file()):
        continue
    _card5 = json.loads((_d / 'card.json').read_text(encoding='utf-8-sig'))
    for _g in _card5['groups']:
        for _s in _g['skills']:
            for _r in _s['rows']:
                if any(k.startswith('inference_') and k.endswith('_hint') for k in _r):
                    _h_rows.append((_d.name, _r))
                    break
            else:
                continue
            break
        else:
            continue
        break
    else:
        continue
    break
if _h_rows:
    _cid5, row3 = _h_rows[0]
    r5 = analyze_row(row3)
    n_unres5 = sum(1 for e in r5['effects'] if e['status'] == 'unresolved')
    has_h = any(k.startswith('inference_') and k.endswith('_hint') for k in row3)
    has_trace = n_unres5 > 0 or bool(r5['split_flags'])
    case('A7-5 hint 变化不丢待办（真实 hint 行 cid%s %s）' % (_cid5, row3['row_id'][:40]),
         '行有 hint 键且账本有待办踪迹（未解决≥1 或拆分标志）',
         dict(hint=has_h, unresolved=n_unres5, flags=[f['code'] for f in r5['split_flags']]),
         dict(hint=True, has_trace=True),
         has_h and has_trace)
else:
    case('A7-5 hint 变化不丢待办', '当前 pages 存在 hint 行', dict(found=0),
         dict(found='>=1'), False)

# ---- 用例 6（原值 0 与缺失/null 区别）：两行同形 FAM1 句、t13 载体 p4/p5 一个存 0.0、----
# 一个字段缺失——批 6 G4 hint 文本如实区分 0.0 与 None（真实键值，card_page_data 让渡注记）。
h301 = json.loads((pages / '301' / 'card.json').read_text(encoding='utf-8-sig'))
h2328 = json.loads((pages / '2328' / 'card.json').read_text(encoding='utf-8-sig'))
note301 = next(rr for g in h301['groups'] for s in g['skills'] for rr in s['rows']
               if rr['row_id'] == '301-special_move-special_move-pattern1-lvorder1-f1')
note2328 = next(rr for g in h2328['groups'] for s in g['skills'] for rr in s['rows']
                if rr['row_id'] == '2328-special_move-special_move-skilltext-lvorder1-f1')
def yield_note(row):
    """行级让渡注记（批 15/14/8 行级替换先例；重建后 b15 行在 inference_b15）。"""
    for k in ('inference_b15', 'inference_b14', 'inference_b8'):
        m = row.get(k) or {}
        if m.get('b6_yield_note_replaced'):
            return m['b6_yield_note_replaced']
    return row.get('inference_b6_hint') or ''


y301 = yield_note(note301)
y2328 = yield_note(note2328)
case('A7-6a 原值 0（存储 0.0）',
     '301（APK 载体）hint 注记含「0.0/0.0」（存储零），不是 None',
     dict(note=y301[-40:]),
     dict(has_00='0.0/0.0' in y301),
     '0.0/0.0' in y301)
case('A7-6b 缺失（None）',
     '2328（CACHE 载体）hint 注记含「None/None」（字段缺失），不是 0.0',
     dict(note=y2328[-40:]),
     dict(has_none='None/None' in y2328),
     'None/None' in y2328)
# 账本侧：数字语义三态独立——NA 判定子句不得含数字；答案 raw_value=0 的加算答案方向=None
# （不冒充上升）。合成：加算答案 raw 0 → 方向 None。
r6 = analyze_row(dict(
    row_id='SYN-zero', cid=0, group='special_move', stage='', level=None, reference_field='',
    fragment_index=0, japanese='味方全体の攻撃力が上がる。', original_numeric_items=[],
    answers=[dict(value='暴击率 +0 个百分点', quantity_kind='暴击概率加算贡献', raw_value=0,
                  field_path='/param4', rule_key='skilllist|2012|/param4',
                  numeric_evidence='推断', association_evidence='推断')]))
a0 = r6['answer_refs'][0]['direction']
case('A7-6c 原值 0 不冒充方向',
     'raw_value=0 的加算答案方向=None（既非 up 也非 down）',
     dict(direction=a0), dict(direction=None), a0 is None)

# ---- 用例 7（跨命名空间不可误合并）：同号异层异值实证——真实同号记录 skilllist|42030603：
# CACHE 层 /param7=-0.2、APK 层 /param7=-0.15000000596046448（两域真实分源，本例运行时
# 从两份源文件重读原值，不采信交接文字）。同一句面、同一 rule_key 的两条合成行（各绑定
# 一层真实记录），经真实行级派生 _emit_row 各自成账本行——断言：①两条账本行 namespace
# layer 各归各层；②各自行内答案引用 raw_value 恰为本层记录原值（不得出现另一层值）；
# ③两层原值确实不同（异值前提成立）——账本分源不合并由①②③共同实证。
sys.path.insert(0, str(ROOT / 'scripts' / 'character_skills'))
cache_doc = json.loads((ROOT / 'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw')
                       .read_text(encoding='utf-8'))
apk_doc = json.loads((ROOT / 'output/base_master/_mdSkill.json').read_text(encoding='utf-8'))
rec_cache = next(r for r in cache_doc['skilllist'] if str(r.get('skillid')) == '42030603')
rec_apk = next(r for r in apk_doc['skilllist'] if str(r.get('skillid')) == '42030603')


def syn_row(rid, layer, raw):
    return dict(
        row_id=rid, cid=4203, group='ability', stage='档位 1', level=None,
        reference_field='skillid_1', fragment_index=0,
        japanese='敵の攻撃力が下がる。', original_numeric_items=[],
        answers=[dict(value=f'攻击 +{raw}', quantity_kind='攻击力加算贡献', unit='系数',
                      raw_value=raw, field_path='/param7', rule_key='skilllist|99|/param7',
                      numeric_evidence='推断', association_evidence='推断',
                      source=dict(table='skilllist', record_id=42030603, layer=layer))],
        row_class='A', evidence='推断', source=dict(table='skilllist', record_id=42030603,
                                                   layer=layer))


rows7 = [('CACHE', rec_cache.get('param7'), syn_row('SYN-42030603-cache', 'CACHE', rec_cache.get('param7'))),
         ('APK', rec_apk.get('param7'), syn_row('SYN-42030603-apk', 'APK', rec_apk.get('param7')))]
out7 = {}
for layer, raw_true, row7 in rows7:
    d7, e7 = [], []
    EL._emit_row(row7, {'table': 'skilllist', 'skill': None}, False,
                 dict(snapshot_id='a7-case7', campaign_signature=None, rules_json_sha256_16=None, pages_root='output/character_skills/pages'), 'a7-case7', d7, e7)
    ns_layer = d7[0]['namespace']['layer']
    ref_raws = [r.get('raw_value') for e in e7 for r in (e.get('answer_refs') or [])]
    out7[layer] = dict(ns_layer=ns_layer, raw_true=raw_true, matched_raws=ref_raws,
                       has_answer=sum(1 for e in e7 if e['status'] == 'has_answer'))
ok7 = (out7['CACHE']['ns_layer'] == 'CACHE' and out7['APK']['ns_layer'] == 'APK'
       and out7['CACHE']['matched_raws'] == [rec_cache.get('param7')]
       and out7['APK']['matched_raws'] == [rec_apk.get('param7')]
       and out7['CACHE']['raw_true'] != out7['APK']['raw_true']
       and out7['CACHE']['has_answer'] == 1 and out7['APK']['has_answer'] == 1)
case('A7-7 跨命名空间不误合并（真实同号异层异值 42030603：CACHE p7=-0.2 vs APK p7=-0.150…）',
     '同一 rule_key 两层各自成账本行：namespace.layer 各归各层、答案 raw=本层记录原值、'
     '两层原值不同且互不出现（分源不合并）',
     out7,
     dict(cache_layer='CACHE', apk_layer='APK', no_cross_consumption=True),
     ok7)


# ---- 用例 8/9（DS-GR-R1 对象约束匹配，20261023 复验）：真实行 6252/8228 ——ダメージ ----
# 匹配加对象维度：敌方ダメージ 主张（与え/敵）↔敌方伤害答案；自伤主张（受け+自身）↔
# 自伤答案；跨对象不硬配——无同对象答案时主张留未解决并注明（object_unmatched_note）。
def _ans_obj(a):
    t = str(a.get('quantity_kind') or '') + str(a.get('value') or '')
    s = ('自身受到伤害' in t) or ('自分' in t)
    e = ('对敌' in t) or ('敵' in t)
    return 'self' if s and not e else 'enemy' if e and not s else None


def r1_state(rid_page):
    """返回行内ダメージ effects 的对象约束状态（供两用例断言）。"""
    cardx = json.loads((pages / rid_page.split('-')[0] / 'card.json').read_text(encoding='utf-8-sig'))
    rowx = next(rr for g in cardx['groups'] for s in g['skills'] for rr in s['rows']
                if rr['row_id'] == rid_page)
    rx = EL.analyze_row(rowx)
    out = []
    for e in rx['effects']:
        if e['effect_type'] != 'ダメージ（词表外）':
            continue
        bound = None
        if e['status'] == 'has_answer':
            idx = e['answer_refs'][0]['resolvable_key']['answer_index']
            bound = _ans_obj(rowx['answers'][idx])
        out.append(dict(effect_id=e['effect_id'], object=e.get('object'), status=e['status'],
                        bound_answer_object=bound,
                        object_unmatched_note=bool(e.get('object_unmatched_note'))))
    return out


def r1_ok(state):
    """对象约束语义：has_answer 效果的绑定答案对象==主张对象（或答案对象不可判）；
    跨对象绑定=0。"""
    for e in state:
        if e['status'] == 'has_answer':
            if e['object'] is not None and e['bound_answer_object'] not in (None, e['object']):
                return False
    return True


st8 = r1_state('6252-special_move-special_move-pattern0-lvorder0-f0')
# 6252 f0：仅一枚「自身受到伤害…90%」答案——敌方主张（与え）必须未解决＋注明对象不符，
# 自伤主张（受け+自身）必须获得该答案；修复前 e00 敌方主张错拿自伤答案。
ok8 = (r1_ok(st8)
       and any(e['object'] == 'enemy' and e['status'] == 'unresolved'
               and e['object_unmatched_note'] for e in st8)
       and any(e['object'] == 'self' and e['status'] == 'has_answer'
               and e['bound_answer_object'] == 'self' for e in st8))
case('A7-8 对象约束匹配（真实 6252 f0：敌方ダメージ主张↔敌方答案/未解决＋注明；自伤主张↔自伤答案）',
     '修复前「自身受到伤害」答案错配敌方主张（e00 has_answer/自伤 unresolved）；修复后'
     '敌方主张未解决＋object_unmatched_note、自伤主张 has_answer、跨对象绑定 0',
     st8,
     dict(enemy_unresolved_with_note=True, self_has_answer=True, no_cross_binding=True),
     ok8)

st9 = r1_state('8228-special_move-special_move-pattern1-lvorder1-f0')
ok9 = r1_ok(st9) and any(e['object'] == 'self' and e['status'] == 'has_answer'
                         and e['bound_answer_object'] == 'self' for e in st9) \
      and any(e['object'] == 'enemy' and e['status'] == 'unresolved'
              and e['object_unmatched_note'] for e in st9)
case('A7-9 对象约束匹配（真实 8228 pattern1 f0：同上；未映射「数量：1体」答案不参与）',
     '同用例 8 语义；另「数量：1体」等无效果类型答案不进入对象匹配池',
     st9,
     dict(enemy_unresolved_with_note=True, self_has_answer=True, no_cross_binding=True),
     ok9)

# ---- 用例 10–14（批 17 P0 收尾，20261023；重建后真实行）：H1 槽位分区／H2 时长槽共享／
# 多 t13 denju patternid 映射／P2 溢出／DS-GR-R1b 自我指向赋予对象标签。全部为重建后
# pages 真实行＋analyze_row 真实派生。

# A7-10（H1 槽位分区）：10212 pattern2 f2——FAM1+crit 行，竞争句「自身の攻撃速度…」
# 属性不在 ATTR_PARAM 词表→分区成立；本行 6 值行（crit×2 由 2012 链＋攻/防/移/時長 t13 槽）。
card10 = json.loads((pages / '10212' / 'card.json').read_text(encoding='utf-8-sig'))
row10 = next(rr for g in card10['groups'] for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '10212-special_move-special_move-pattern2-lvorder2-f2')
b17m10 = row10.get('inference_b17') or {}
r10 = analyze_row(row10)
keys10 = sorted(a.get('rule_key') for a in row10['answers'])
ok10 = (b17m10.get('path') == 'H1_partition'
        and 'inference_b15_hint' not in row10 and 'inference_b8' not in row10
        and keys10 == ['bossskill|13|/skillparam1', 'bossskill|13|/skillparam2',
                       'bossskill|13|/skillparam3', 'bossskill|13|/skillparam6',
                       'skilllist|2012|/param4', 'skilllist|2012|/param5']
        and all(e['status'] == 'has_answer' for e in r10['effects'])
        and '競争' not in ''.join(row10['unknown_reasons'])
        and any('竞争句' in rr and '不能持有本 t13 任何槽' in rr
                for rr in row10['unknown_reasons']))
case('A7-10 H1 槽位分区（真实 10212 f2：竞争句属性不在槽词表→分区，本行获 t13 全活性槽＋时长）',
     'inference_b17/H1_partition、crit(2012)＋攻/防/移/時長(t13) 六值行、无残留 hint 键、'
     '行注记含分区论证',
     dict(path=b17m10.get('path'), keys=keys10,
          unresolved=sum(1 for e in r10['effects'] if e['status'] == 'unresolved')),
     dict(path='H1_partition', six_answers=True, unresolved=0),
     ok10)

# A7-11（H2 时长槽共享）：11004 denju f2——时长值行引同一 t13 /skillparam3；硬前提
# ①兄弟 FAM1 行批 6 同 t13 晋级＋②载体 param0==t13 p3 逐字披露在注记。
card11 = json.loads((pages / '11004' / 'card.json').read_text(encoding='utf-8-sig'))
row11 = next(rr for g in card11['groups'] for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '11004-denju-denju-denju_denju_id____cid-lvorder0-f2')
b17m11 = row11.get('inference_b17') or {}
r11 = analyze_row(row11)
dur11 = next(a for a in row11['answers'] if a.get('rule_key') == 'bossskill|13|/skillparam3')
reasons11 = ''.join(row11['unknown_reasons'])
ok11 = (b17m11.get('path') == 'H2_duration_share'
        and dur11.get('raw_value') == 20.0
        and dur11.get('source', {}).get('record_key') == 'bossskill|41100405|APK'
        and (b17m11.get('crit_chain') or {}).get('carrier_record_id') == 41100413
        and '槽共享' in reasons11 and '不合并不乘积' in reasons11
        and 'param0 原值 20.0' in reasons11 and 'p3 原值 20.0' in reasons11
        and all(e['status'] == 'has_answer' for e in r11['effects'])
        and 'inference_b15_hint' not in row11)
case('A7-11 H2 时长槽共享（真实 11004 f2：D1 裁决——时长值行引同一 t13 /skillparam3，'
     '硬前提①②逐行实测入注记）',
     'inference_b17/H2_duration_share、时长 raw 20.0 来源 bossskill|41100405|APK、'
     'crit 链载体 41100413、注记含槽共享＋两值一致披露、行级无 b15_hint 残留',
     dict(path=b17m11.get('path'), dur_raw=dur11.get('raw_value'),
          chain=(b17m11.get('crit_chain') or {}).get('carrier_record_id')),
     dict(path='H2_duration_share', dur_raw=20.0, chain=41100413),
     ok11)

# A7-12（多 t13 denju patternid 映射）：20510 denju f1——patternid0→bosspattern
# 42051003 sinfo 唯一命中→boss_skill_refs skillid3 归属→t13 42051003；其余 t13
# 42051005 逐槽同值（兜底披露）。
card12 = json.loads((pages / '20510' / 'card.json').read_text(encoding='utf-8-sig'))
row12 = next(rr for g in card12['groups'] for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '20510-denju-denju-denju_denju_id____cid-lvorder0-f1')
b17m12 = row12.get('inference_b17') or {}
raws12 = sorted((a.get('field_path'), a.get('raw_value')) for a in row12['answers']
                if a.get('rule_key', '').startswith('bossskill|13'))
r12 = analyze_row(row12)
ok12 = (b17m12.get('path') == 'MULTI_T13_PATTERNID'
        and b17m12.get('chain_record_id') == 42051003
        and raws12 == [('/skillparam1', 0.55), ('/skillparam2', 0.275),
                       ('/skillparam3', 30), ('/skillparam6', 0.275)]
        and all(e['status'] == 'has_answer' for e in r12['effects'])
        and any('唯一命中' in rr for rr in row12['unknown_reasons'])
        and 'inference_b6_hint' not in row12)
case('A7-12 多 t13 denju patternid 映射（真实 20510 f1：sinfo 唯一命中＋归属登记→'
     't13 42051003；其余 t13 同值兜底披露）',
     'inference_b17/MULTI_T13_PATTERNID、t13 四槽值 (0.55/0.275/30/0.275)、'
     '注记含唯一命中披露、不残留 b6_hint',
     dict(path=b17m12.get('path'), chain=b17m12.get('chain_record_id'), raws=raws12),
     dict(path='MULTI_T13_PATTERNID', chain=42051003,
          raws=[('/skillparam1', 0.55), ('/skillparam2', 0.275), ('/skillparam3', 30),
                ('/skillparam6', 0.275)]),
     ok12)

# A7-13（P2 溢出）：2320 denju f1——multi-t13 P2 行同法晋级（t13 40232005，
# p1=0.4000000059604645）；非 Y.G. 非 P0（priority 应为 P2）。
card13 = json.loads((pages / '2320' / 'card.json').read_text(encoding='utf-8-sig'))
row13 = next(rr for g in card13['groups'] for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '2320-denju-denju-denju_denju_id____cid-lvorder0-f1')
b17m13 = row13.get('inference_b17') or {}
p1_13 = next(a for a in row13['answers'] if a.get('rule_key') == 'bossskill|13|/skillparam1')
d13, e13 = [], []
EL._emit_row(row13, {'table': 'denju', 'skill': None}, False,
             dict(snapshot_id='a7-case13', campaign_signature=None,
                  rules_json_sha256_16=None, pages_root='output/character_skills/pages'),
             'a7-case13', d13, e13)
st13 = [e['status'] for e in e13]
prios13 = {e['unresolved']['priority'] for e in e13 if e['status'] == 'unresolved'}
# 批 17 复评实测：2320 f1 的攻/防/移/時長四主张全部 has_answer（无剩余主张）——
# 「P2 入队」仅当存在未解决主张时成立；本行断言＝全解＋（若有剩余主张）P2 档。
ok13 = (b17m13.get('path') == 'MULTI_T13_PATTERNID'
        and b17m13.get('chain_record_id') == 40232005
        and p1_13.get('raw_value') == 0.4000000059604645
        and 'unresolved' not in st13
        and all(pr == 'P2' for pr in prios13))
case('A7-13 P2 溢出多 t13（真实 2320 f1：t13 40232005、p1=0.400…，四主张全解无剩余）',
     'inference_b17/MULTI_T13_PATTERNID、p1 原值 0.4000000059604645、'
     '无未解决主张（若有则必须 P2 档）',
     dict(path=b17m13.get('path'), chain=b17m13.get('chain_record_id'),
          p1=p1_13.get('raw_value'), statuses=collections.Counter(st13)),
     dict(path='MULTI_T13_PATTERNID', chain=40232005, p1=0.4000000059604645,
          all_resolved=True),
     ok13)

# A7-14（DS-GR-R1b 自我指向赋予）：30230 f3——「一定間隔ごとに自身に小ダメージを
# 与える」主张对象应 self（に格＝赋予对象），非 enemy；该主张仍在队（ダメージ 词表外）。
row14 = None
card14 = json.loads((pages / '30230' / 'card.json').read_text(encoding='utf-8-sig'))
row14 = next(rr for g in card14['groups'] for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '30230-ability-ability-skillid_2_-lvorder1-f3')
r14 = analyze_row(row14)
e05 = next(e for e in r14['effects'] if e['effect_id'].endswith('#e05'))
ok14 = (e05.get('object') == 'self' and e05['status'] == 'unresolved')
case('A7-14 DS-GR-R1b 自我指向赋予对象标签（真实 30230 f3#e05：「自身に…与える」→self）',
     'effect.object=self（修复前 enemy）、主张仍在队（ダメージ 词表外未解决）',
     dict(obj=e05.get('object'), status=e05['status']),
     dict(obj='self', status='unresolved'),
     ok14)

# ---- 用例 15–19（R2 整改 20261023：完成判定逐主张覆盖——真实行）---------------------
# A7-15（R2 真实·86 概率主张正式映射）：「また一定確率で攻撃した敵の防御力を一定時間下げる」
# ——概率条件引用必须有解析状态＋载体映射（批 13 披露的 skilllist|50009|APK /param3=15%）；
# 不得重新描述为数值未知，也不得以「条件词条登记」结清。行按新判定复评后保持完整。
row15 = next(rr for g in json.loads((pages / '86' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
             for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '86-denju-denju-denju_denju_id____cid-lvorder0-f1')
r15 = EL.analyze_row(row15, table='denju')
cond15 = next((rf for rf in r15['refs'] if rf['kind'] == 'condition' and rf['text'] == '一定確率'), None)
res15 = (cond15 or {}).get('resolution') or {}
ok15 = (res15.get('status') == 'mapped（推断）'
        and res15.get('value') == 0.15000000596046448
        and res15.get('field_path') == '/param3'
        and (res15.get('source') or {}).get('record_key') == 'skilllist|50009|APK'
        and res15.get('evidence_grade') == '推断'
        and not r15['split_flags']
        and all(e['status'] == 'has_answer' for e in r15['effects']))
case('A7-15 R2 86 概率主张正式映射（真实 86 denju f1）',
     '「一定確率」条件引用 resolution=mapped（推断）：值 0.15000000596046448、/param3、'
     '来源 skilllist|50009|APK、证据档推断；行无拆分标志（复评后仍完整）',
     dict(resolution=res15, flags=[f['code'] for f in r15['split_flags']]),
     dict(status='mapped（推断）', value=0.15000000596046448, field='/param3',
          source='skilllist|50009|APK'),
     ok15)

# A7-16（R2 真实·20905 阈值答案映射）：「…HPが25%以上の味方の攻撃力が2%上がる。」——
# 数字 25（HP条件阈值）经 原文角色↔答案 quantity_kind 映射、2 经答案值映射；行保持完整。
row16 = next(rr for g in json.loads((pages / '20905' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
             for s in g['skills'] for rr in s['rows']
             if rr['row_id'].endswith('extra-extra-extra_abilities_0_-lv1-f1'))
r16 = EL.analyze_row(row16)
nmap16 = {n['literal']: (n.get('mapping') or {}).get('basis') for n in r16['number_refs']}
case('A7-16 R2 20905 阈值数字映射（真实行）',
     'number 25→role_bound_answer（R2 复审整改第二轮 20261023：basis 由 answer_value 更名'
     '为角色绑定映射——角色↔quantity_kind/单位/数值三重绑定，语义更强）、'
     '2→role_bound_answer；无拆分标志',
     dict(nmap=nmap16, flags=[f['code'] for f in r16['split_flags']]),
     dict(_25='role_bound_answer', _2='role_bound_answer', flags=[]),
     nmap16.get('25') == 'role_bound_answer' and nmap16.get('2') == 'role_bound_answer'
     and not r16['split_flags'])

# A7-17（R2 真实·删除阈值答案后必须不完整）：同上真实行删除 HP条件阈值 答案——数字 25
# 失去映射 → S2，行级派生为拆分待核查（不得完整）。
import copy as _copy
row17 = _copy.deepcopy(row16)
row17['answers'] = [a for a in row17['answers'] if a.get('quantity_kind') != 'HP条件阈值']
d17, e17 = [], []
EL._emit_row(row17, {'table': 'extra', 'skill': None}, False,
             dict(campaign_signature=None, rules_json_sha256_16=None,
                  pages_root='output/character_skills/pages'), 'a7-r2', d17, e17)
case('A7-17 R2 删除 HP 阈值答案后不得完整（真实 20905 行派生）',
     '数字 25 无映射 → S2_unconfirmed_numbers；ledger_row_status=拆分待核查',
     dict(status=d17[0]['ledger_row_status'],
          flags=[f['code'] for f in d17[0]['split_flags']]),
     dict(status='拆分待核查', has_S2=True),
     d17[0]['ledger_row_status'] == '拆分待核查'
     and any(f['code'] == 'S2_unconfirmed_numbers' for f in d17[0]['split_flags']))

# A7-18（R2 真实·349 六项已补齐保持完整）：R2 新判定（条件解析/数字映射/残余监视）下
# 真实 349 f3 保持完整（回归保护）。
row18 = next(rr for g in json.loads((pages / '349' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
             for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '349-special_move-special_move-pattern0-lvorder0-f3')
r18 = EL.analyze_row(row18)
case('A7-18 R2 349 六项已补齐保持完整（真实行）',
     'has_answer=6、无拆分标志（R2 新判定下不变）',
     dict(has_answer=sum(1 for e in r18['effects'] if e['status'] == 'has_answer'),
          flags=[f['code'] for f in r18['split_flags']]),
     dict(has_answer=6, flags=[]),
     sum(1 for e in r18['effects'] if e['status'] == 'has_answer') == 6 and not r18['split_flags'])

# A7-19（R2 真实·小数 token 修正）：20643「攻撃力が5.5%上がり…」——小数 5.5 此前被切成
# '5'/'0.5' 两个整数 token 无法映射；R2 后单 token 5.5 经答案值映射（raw 5.5）。
# R2 复审整改第二轮（20261023）：映射 basis 更名 answer_value→role_bound_answer
# （升级为角色↔quantity_kind/单位/数值三重绑定；语义不变、绑定更强），本例预期随口径
# 同步，「5.5 单 token 不拆分＋有映射」的断言不变。
row19 = next(rr for g in json.loads((pages / '20643' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
             for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '20643-passive-passive-passives_1_-lvorder1-f0')
r19 = EL.analyze_row(row19)
lits19 = [(n['literal'], (n.get('mapping') or {}).get('basis')) for n in r19['number_refs']]
case('A7-19 R2 小数 token 修正（真实 20643：5.5% 不再拆成 5+0.5）',
     'number literal 恰为 5.5（非 5/0.5 两截）且映射 role_bound_answer（第二轮 basis 更名）；'
     '无拆分标志',
     dict(lits=lits19, flags=[f['code'] for f in r19['split_flags']]),
     dict(lits=[('5.5', 'role_bound_answer'), ('5.5', 'role_bound_answer')], flags=[]),
     lits19 == [('5.5', 'role_bound_answer'), ('5.5', 'role_bound_answer')] and not r19['split_flags'])

# ---- R2 复审整改第二轮增补真实用例（20261023）----------------------------------------
# A7-20（真实 20905）：数字角色绑定——HP 阈值数字须绑 HP条件阈值答案、效果量数字须绑
# 效果量答案；行完整。
row20 = next(rr for g in json.loads((pages / '20905' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
             for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '20905-extra-extra-extra_abilities_0_-lv1-f1')
r20 = EL.analyze_row(row20)
nm20 = [(n['literal'], n.get('role_label'), (n.get('mapping') or {}).get('basis'))
        for n in r20['number_refs']]
case('A7-20 R2二轮 数字角色绑定（真实 20905）',
     '25→HP条件阈值、2→攻击力效果量百分比，均 role_bound_answer；行完整无标志',
     dict(nummap=nm20, flags=[f['code'] for f in r20['split_flags']]),
     dict(has_hp_threshold=('25', 'HP条件阈值', 'role_bound_answer'),
          has_attack=('2', '攻击力效果量百分比', 'role_bound_answer')),
     ('25', 'HP条件阈值', 'role_bound_answer') in nm20
     and ('2', '攻击力效果量百分比', 'role_bound_answer') in nm20
     and not r20['split_flags'])

# A7-21（R2 复验整改第三轮 20261023 重写：真不同角色用例）——DeepSeek 复验 R2-ROLE-ALIAS-105
# 指出旧 A7-21（20221）的第三数字角色与存在答案 qk 完全相同（<謀略の世界>所属/暴击威力
# 效果量百分比），其 S2 来自消费检查、不能证明「不同角色不放行」；且效果类型词表补齐后
# 20221 已完整（R2-S2-CONSUMPTION-319 修复），S2 断言不再成立。
# 新用例＝真实行 2046（攻撃力/クリティカル威力 双答案同值 2）受控变体：删除暴击威力答案后
# 暴击威力角色的数字 2 面对同值攻击答案——旧类别别名（「效果量」字面）会放行，收紧后
# 角色检查必须拒绝；配套单元断言直接证明拒绝来自角色检查本身（非消费/位置）。
import copy as _c21
row21 = next(rr for g in json.loads((pages / '2046' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
             for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '2046-extra-extra-extra_abilities_0_-lv1-f0')
r21 = _c21.deepcopy(row21)
r21['answers'] = [a for a in r21['answers']
                  if '暴击威力' not in str(a.get('quantity_kind') or '')]
res21 = EL.analyze_row(r21)
unm21 = [(n['literal'], n.get('role_label'), n.get('same_label_answer_present'))
         for n in res21['number_refs'] if not n.get('mapping')]
# 单元断言：子类型鉴别本身（真实 qk 标签逐字）
compat_assert = (
    EL._role_qk_compat('暴击威力效果量百分比', 'effect_amount', '攻击力效果量百分比') is False
    and EL._role_qk_compat('必杀技威力效果量百分比', 'effect_amount', '攻击力效果量百分比') is False
    and EL._role_qk_compat('暴击威力效果量百分比', 'effect_amount', '味方全体/暴击威力效果量百分比') is True
    and EL._role_qk_compat('攻击力效果量百分比', 'effect_amount', '攻击力效果量百分比') is True)
# 消费事实：被删答案的行内，攻击答案确实被其同子句主张消费（故数字 2 的 S2 拒绝
# 不可能来自「攻击答案未被消费」）
attack_consumed = any(e['status'] == 'has_answer' and e['effect_type'] == '攻撃力'
                      for e in res21['effects'])
case('A7-21 R2复验整改 真不同子类型角色不放行（真实 2046 受控变体＋单元断言）',
     '①删除暴击威力答案后：暴击威力角色的数字 2 对同值攻击答案仍 S2（旧「效果量」别名'
     '会放行，收紧后拒绝）；same_label_answer_present=False（非消费链问题）；'
     '②单元断言：暴击威力/必杀技威力 ↔ 攻击力 全部 False、同子类型 True；'
     '③攻击答案确被消费（排除消费检查致因）',
     dict(flags=[f['code'] for f in res21['split_flags']], unmapped=unm21,
          attack_consumed=attack_consumed, compat_assert=compat_assert,
          jp=row21['japanese']),
     dict(has_S2=True, compat_all=True, attack_consumed=True),
     'S2_unconfirmed_numbers' in [f['code'] for f in res21['split_flags']]
     and any(l == '2' and rlp == '暴击威力效果量百分比' and sp is False for l, rlp, sp in unm21)
     and attack_consumed and compat_assert)

# A7-22（真实 47 バリア行）：监视表扩表后 バリア 词表外机制词无结构化覆盖→S3b，
# 待办带缺口/已有证据/下一步（gap/have/next_step）。
row22 = next(rr for g in json.loads((pages / '47' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
             for s in g['skills'] for rr in s['rows'] if 'バリア' in rr['japanese'])
r22 = EL.analyze_row(row22)
s3b22 = next((f for f in r22['split_flags'] if f['code'] == 'S3b_residual_mechanisms'), None)
case('A7-22 R2二轮 バリア残余待办（真实 47）',
     '含 S3b_residual_mechanisms 且命中词含「バリア」；detail 首项带 gap/have/next_step',
     dict(flags=[f['code'] for f in r22['split_flags']],
          words=[d['word'] for d in (s3b22 or {}).get('detail', [])],
          keys=sorted((s3b22 or {}).get('detail', [{}])[0])),
     dict(has_S3b=True, has_barrier=True, has_todo_fields=True),
     s3b22 is not None and any(d['word'] == 'バリア' for d in s3b22['detail'])
     and all(k in s3b22['detail'][0] for k in ('gap', 'have', 'next_step')))

# A7-23（真实 86 概率载体映射保留）：R2 一轮成果不回退（行＝denju 传授 f1，与复审
# reproduce/上轮回归同一 row_id；卡 86 其余含「一定確率」的行不在本例范围）。
row23 = next(rr for g in json.loads((pages / '86' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
             for s in g['skills'] for rr in s['rows']
             if rr['row_id'] == '86-denju-denju-denju_denju_id____cid-lvorder0-f1')
r23 = EL.analyze_row(row23, table='denju')
cond23 = next((rf for rf in r23['refs'] if rf['kind'] == 'condition' and rf['text'] == '一定確率'), None)
resol23 = (cond23 or {}).get('resolution') or {}
case('A7-23 R2二轮 86 概率载体映射保留（真实 86）',
     'resolution=mapped（推断）：/param3、来源 skilllist|50009|APK、无拆分标志',
     dict(resolution=resol23, flags=[f['code'] for f in r23['split_flags']]),
     dict(status='mapped（推断）', field_path='/param3'),
     resol23.get('status') == 'mapped（推断）' and resol23.get('field_path') == '/param3'
     and (resol23.get('source') or {}).get('record_key') == 'skilllist|50009|APK'
     and not r23['split_flags'])

# ---- A7-24…27（R2 复审整改第三轮 root-fix 增补，20261023；线 A GLM）------------------
# 语义来自复审 independent_20261023_r2r3_root_recheck/REPORT.md §R2 闭合标准：覆盖必须
# 指向有效的对应机制解析及证据，未知答案不能解除待办，其他效果的概率载体不能替本机制作证。
# A7-24（负例：未解析结构化答案不解除待办）：真实 349 f3 末增暗闇＋quantity_kind=暗闇／
# value=未知／raw_value=null／两证据未知／status=unresolved 的答案——行不完整＋暗闇
# 剩余效果待办保留（gap/have/next_step 齐备）。
row24 = _copy.deepcopy(row18)
row24['japanese'] = row24['japanese'].rstrip('。') + 'と同時に暗闇を付与する。'
row24['answers'].append(dict(value='未知', raw_value=None, quantity_kind='暗闇',
                             numeric_evidence='未知', association_evidence='未知',
                             status='unresolved', note=''))
r24 = EL.analyze_row(row24)
s3b24 = next((f for f in r24['split_flags'] if f['code'] == 'S3b_residual_mechanisms'), None)
d24 = next((d for d in (s3b24 or {}).get('detail', []) if d.get('word') == '暗闇'), None)
case('A7-24 R2三轮 未解析结构化答案不解除机制待办（真实 349 f3＋暗闇合成答案）',
     '行不完整（S3b）；暗闇待办保留且带 gap/have/next_step；'
     'facet 指出 quantity_kind 命中但答案未解析',
     dict(complete=all(e['status'] in ('has_answer', 'justified_na') for e in r24['effects'])
          and not r24['split_flags'],
          s3b_words=sorted({d['word'] for d in (s3b24 or {}).get('detail', [])}),
          todo_keys=sorted(d24 or {})),
     dict(complete=False, has_kuraume=True, todo_fields=True),
     not (all(e['status'] in ('has_answer', 'justified_na') for e in r24['effects'])
          and not r24['split_flags'])
     and d24 is not None and all(k in d24 for k in ('gap', 'have', 'next_step')))

# A7-25（负例：对照性载体注记不作证）：真实 86 传授行末增暗闇＋原概率载体答案注记末加
# 「暗闇仅作为对照词，不属于上述概率载体解释的效果。」——载体（skilllist|50009|APK，
# ability2003 デバフ系）无该机制槽位绑定披露 → 不覆盖；不依赖否定词黑名单。
row25 = _copy.deepcopy(row23_page := next(
    rr for g in json.loads((pages / '86' / 'card.json').read_text(encoding='utf-8-sig'))['groups']
    for s in g['skills'] for rr in s['rows']
    if rr['row_id'] == '86-denju-denju-denju_denju_id____cid-lvorder0-f1'))
row25['japanese'] = row25['japanese'].rstrip('。') + 'と同時に暗闇を付与する。'
row25['answers'][0]['note'] += ' 暗闇仅作为对照词，不属于上述概率载体解释的效果。'
r25 = EL.analyze_row(row25)
s3b25 = next((f for f in r25['split_flags'] if f['code'] == 'S3b_residual_mechanisms'), None)
d25 = next((d for d in (s3b25 or {}).get('detail', []) if d.get('word') == '暗闇'), None)
case('A7-25 R2三轮 对照性载体注记不作证（真实 86 传授行受控变体）',
     '行不完整（S3b）；暗闇待办保留（gap/have/next_step）；原概率载体披露未被借用',
     dict(complete=all(e['status'] in ('has_answer', 'justified_na') for e in r25['effects'])
          and not r25['split_flags'],
          s3b_words=sorted({d['word'] for d in (s3b25 or {}).get('detail', [])}),
          todo_keys=sorted(d25 or {})),
     dict(complete=False, has_kuraume=True, todo_fields=True),
     not (all(e['status'] in ('has_answer', 'justified_na') for e in r25['effects'])
          and not r25['split_flags'])
     and d25 is not None and all(k in d25 for k in ('gap', 'have', 'next_step')))

# A7-26（正例：有效机制答案解除待办）：349 f3＋バリア付与＋数值バリア回数答案 → 完整
# （定性机制可依有效证据解析，不一律降级）。
row26 = _copy.deepcopy(row18)
row26['japanese'] = row26['japanese'].rstrip('。') + 'と同時にバリアを付与する。'
row26['answers'].append(dict(value='1回', raw_value=1, quantity_kind='バリア回数', unit='次',
                             numeric_evidence='推断', association_evidence='推断',
                             status='mapped', note='A7 增补合成正例'))
r26 = EL.analyze_row(row26)
case('A7-26 R2三轮 有效机制答案解除待办（真实 349 f3＋バリア回数合成答案）',
     '行完整：全效果 has_answer、无拆分标志',
     dict(complete=all(e['status'] in ('has_answer', 'justified_na') for e in r26['effects'])
          and not r26['split_flags'],
          flags=[f['code'] for f in r26['split_flags']]),
     dict(complete=True, flags=[]),
     all(e['status'] in ('has_answer', 'justified_na') for e in r26['effects'])
     and not r26['split_flags'])

# A7-27（族核对：已登记能力族载体不得为非同族机制作证）：86 行载体注记含「暗闇」→/param
# 绑定字样但 ability=2003（ステータス減益登记族）——族不符仍不覆盖（正例对照：86 原行
# 无暗闇词面保持完整，见 A7-23）。
row27 = _copy.deepcopy(row23_page)
row27['japanese'] = row27['japanese'].rstrip('。') + 'と同時に暗闇を付与する。'
row27['answers'][0]['note'] += '；句中「暗闇」→/param3 1:1 映射（A7 增补合成：族不符路径）'
r27 = EL.analyze_row(row27)
s3b27 = next((f for f in r27['split_flags'] if f['code'] == 'S3b_residual_mechanisms'), None)
d27 = next((d for d in (s3b27 or {}).get('detail', []) if d.get('word') == '暗闇'), None)
case('A7-27 R2三轮 载体能力族不符不作证（真实 86 受控变体：ability2003≠状態異常族）',
     '行不完整（S3b）；暗闇待办保留且 have 注明能力族不符',
     dict(complete=all(e['status'] in ('has_answer', 'justified_na') for e in r27['effects'])
          and not r27['split_flags'],
          s3b_words=sorted({d['word'] for d in (s3b27 or {}).get('detail', [])}),
          have=(d27 or {}).get('have')),
     dict(complete=False, has_kuraume=True),
     not (all(e['status'] in ('has_answer', 'justified_na') for e in r27['effects'])
          and not r27['split_flags'])
     and d27 is not None and '能力族不符' in str(d27.get('have')))

# ---- 汇总 ----
failed = [r for r in results if not r['passed']]
print(json.dumps(dict(total=len(results), failed=len(failed), results=results),
                 ensure_ascii=False, indent=1))
import argparse
_report_parser = argparse.ArgumentParser(description='A7 semantic regressions; preserve old reports before overwriting')
_report_parser.add_argument('--out', type=Path, default=ROOT / 'output/character_skills/effect_ledger/acceptance/a7_regression_results.json')
out = _report_parser.parse_args().out
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dict(total=len(results), failed=len(failed), results=results),
                          ensure_ascii=False, indent=1), encoding='utf-8')
sys.exit(1 if failed else 0)
