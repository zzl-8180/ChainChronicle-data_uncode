# -*- coding: utf-8 -*-
"""Y.G. 优先清单 · 步骤1：从审查 coverage_refined.json 提取 2,066 剩余目标并与当前 pages 富化。

数据源：
- 审查分母/分子：output/character_skills/review/independent_20261020_codex_audit/coverage_refined.json
  （yg=true & inferred=false → 2,066 剩余；yg=true & inferred=true → 278 已点亮）
- 当前页面富化：output/character_skills/pages/<cid>/card.json（row_class、inference_* 键、
  context_text、所属 skill 的 table）
- Y.G. 卡集：output/character_skills/profiles/characters.csv title 含「Y.G.」
- 归一函数：批 1 同法逐字节复用（work/character_skills_inference_inventory/enrich_v2.py:10-19
  norm_text；build_families_v2.py:6-23 family_of）
- **正式剩余效果队列（20261023 目标整改 P2 修正）**：
  output/character_skills/effect_ledger/backlog.json——效果账本派生的正式待办
  （全部未解决效果＋全部拆分待核查描述，行级完整度独立于 A/C/证据档；
  由 scripts/character_skills/effect_ledger.py 从当前 pages 重建）。
  修正前缺陷（审查 GOAL_ALIGNMENT.md G01 证据链 / 任务卡 §发现3）：本脚本 line 91 对
  非 C 行登记 not_C 后 continue——部分完成行（A/partial，如 cid349/cid6335）的剩余效果
  永远进不了本队列。修正：①非 C 行不再跳过（富化保留、登记 row_class，仅记 mismatch
  诊断）；②正式待办以效果账本 backlog 为准——本脚本消费 backlog（按 row_id 关联并输出
  官方队列构成），供 enrich_records/assign_candidates 选题链使用；不再以 coverage_refined
  旧分母或 C 行过滤作为剩余工作总量。

只读 pages/profiles/审查产物/效果账本；输出仅写本目录。
"""
import json, csv, re, os, sys, io, unicodedata, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(ROOT)

# ---------- 批 1 同法归一（enrich_v2.py:10-19 / build_families_v2.py:6-23） ----------
def norm_text(t):
    t = unicodedata.normalize('NFKC', t).strip()
    t = re.sub(r'[0-9]+', 'N', t)
    t = re.sub(r'(<[^<>]*>)|(＜[^＜＞]*＞)', '⟨X⟩', t)
    t = re.sub(r'(≪[^≪≫]*≫)', '⟨Y⟩', t)
    return t

ATTRS = [
    'クリティカル威力', 'クリティカル発生率', 'クリティカル率', 'クリティカル',
    '通常攻撃威力', '攻撃間隔', '攻撃速度', '移動速度', '防御力', '攻撃力',
    '受けるダメージ', '与えるダメージ', 'HP', '効果',
]
attr_alt = '|'.join(re.escape(a) for a in sorted(ATTRS, key=len, reverse=True))
RUN = re.compile(r'(?:%s)(?:と(?:%s))+' % (attr_alt, attr_alt))
PRED = r'(?:が|を|も)[^。、]{0,10}?(?:上がる|上がり|下がる|下がり|上げる|下げる|回復する|回復し|早くなる|遅くなる)'
SINGLE = re.compile(r'(?:%s)(?=%s)' % (attr_alt, PRED))
CONNECTIVES = ['その後、', 'さらに', 'ただし、', 'また', '更に']

def family_of(template):
    t = RUN.sub('⟨ATTR⟩', template)
    t = SINGLE.sub('⟨ATTR⟩', t)
    for c in CONNECTIVES:
        if t.startswith(c):
            t = t[len(c):]
    return t

# ---------- 1. Y.G. 卡集 ----------
yg_cids = []
with open('output/character_skills/profiles/characters.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if 'Y.G.' in (r.get('title') or ''):
            yg_cids.append(int(r['cid']))
assert len(yg_cids) == 109, len(yg_cids)

# ---------- 2. 审查覆盖行 ----------
cov = json.load(open('output/character_skills/review/independent_20261020_codex_audit/coverage_refined.json', encoding='utf-8'))
rows = cov['rows']
yg_rem = [r for r in rows if r['yg'] and not r['inferred']]
yg_inf = [r for r in rows if r['yg'] and r['inferred']]
non_yg_rem = [r for r in rows if not r['yg'] and not r['inferred']]
print('YG remaining=%d inferred=%d nonYG remaining=%d' % (len(yg_rem), len(yg_inf), len(non_yg_rem)))
assert len(yg_rem) == 2066 and len(yg_inf) == 278

# ---------- 3. 当前 pages 富化 ----------
def iter_page_rows(cid):
    d = json.load(open('output/character_skills/pages/%d/card.json' % cid, encoding='utf-8'))
    for grp in d['groups']:
        for sk in grp.get('skills', []):
            for row in sk.get('rows', []):
                yield row, sk.get('table')

page = {}
total_c = total_a = 0
for cid in yg_cids:
    for row, table in iter_page_rows(cid):
        page[row['row_id']] = (row, table)
        if row.get('row_class') == 'C':
            total_c += 1
        elif row.get('row_class') == 'A':
            total_a += 1
print('YG pages rows: C=%d A=%d total=%d' % (total_c, total_a, len(page)))

mismatch = {'missing': [], 'not_C': []}
enriched = []
for r in yg_rem:
    if r['row_id'] not in page:
        mismatch['missing'].append(r['row_id'])
        continue
    row, table = page[r['row_id']]
    # P2 修正（20261023）：非 C 行不再 continue——部分完成行（A/partial）的剩余效果
    # 必须留在队列（row_class 仅作登记；剩余效果以效果账本 backlog 为准，见下）。
    if row.get('row_class') != 'C':
        mismatch['not_C'].append(r['row_id'])
    inf_keys = sorted(k for k in row if k.startswith('inference_') and not k.endswith('_hint'))
    hint_keys = sorted(k for k in row if k.startswith('inference_') and k.endswith('_hint'))
    enriched.append({
        'row_id': r['row_id'], 'cid': row['cid'], 'table': table,
        'group': row.get('group'), 'japanese': row.get('japanese'),
        'context_text': row.get('context_text'),
        'row_class': row.get('row_class'),
        'partial': bool(row.get('partial')),
        'answers_n': len(row.get('answers') or []),
        'inf_keys': inf_keys, 'hint_keys': hint_keys,
        'text': r['text'],
        'template': norm_text(r['text']), 'family': family_of(norm_text(r['text'])),
    })
print('mismatch: missing=%d not_C=%d（not_C 行已保留在队列，仅诊断登记）'
      % (len(mismatch['missing']), len(mismatch['not_C'])))

# ---------- 3b. 正式剩余效果队列＝效果账本 backlog（P2 修正，20261023） ----------
# backlog 由 scripts/character_skills/effect_ledger.py 从当前 pages 重建（一效果一条＋
# 拆分待核查描述），包含 A 类部分行/已晋级/带 hint 行的剩余效果——行级完整度独立于
# A/C 与证据档。本脚本消费它：按 row_id 关联到富化行，并输出官方队列构成供选题链使用。
BACKLOG_PATH = 'output/character_skills/effect_ledger/backlog.json'
backlog = json.load(open(BACKLOG_PATH, encoding='utf-8'))
backlog_by_row = collections.defaultdict(list)
for item in backlog:
    backlog_by_row[item['row_id']].append(item)
enriched_row_ids = {e['row_id'] for e in enriched}
for e in enriched:
    e['backlog_item_ids'] = sorted(b['backlog_id'] for b in backlog_by_row.get(e['row_id'], []))
    e['backlog_kinds'] = sorted({b['kind'] for b in backlog_by_row.get(e['row_id'], [])})
    e['backlog_priorities'] = sorted({b['priority'] for b in backlog_by_row.get(e['row_id'], [])})
# 断点/Y.G. 优先（任务书 §三.3/§五：衔接断点与 Y.G. 优先；backlog.priority 已编码）
official_queue = {
    'source': BACKLOG_PATH,
    'total_items': len(backlog),
    'by_kind': dict(collections.Counter(b['kind'] for b in backlog)),
    'by_priority': dict(collections.Counter(b['priority'] for b in backlog)),
    'yg_items': sum(1 for b in backlog if b['yg']),
    'breakpoint_items': sum(1 for b in backlog if b.get('breakpoint')),
    'joined_to_enriched_rows': sum(1 for e in enriched if e['backlog_item_ids']),
    'enriched_rows_without_backlog_items': sum(1 for e in enriched if not e['backlog_item_ids']),
    # P1 时尚未入本富化集的 backlog 行（非 Y.G. 或 coverage_refined 已点亮行）——
    # 证明正式队列不再受 coverage_refined/C 行过滤限制：
    'backlog_rows_outside_enriched': len(set(backlog_by_row) - enriched_row_ids),
    'priority_rule': ('P0=衔接断点行（已有 2012 暴击答案且句面攻/防/移/时长主张未解决）；'
                      'P1=Y.G. 卡其余未解决/待核查；P2=其他（effect_ledger/README.md 定义）'),
}
# 选题用子队列：P0 断点优先，其次 Y.G.（不覆盖 backlog 本身——官方队列始终是
# effect_ledger/backlog.json，本文件只是选题视图）
yg_backlog_view = [b for b in backlog if b.get('breakpoint') or b['yg']]
json.dump(yg_backlog_view, open('work/character_skills_yg_priority/yg_backlog_view.json', 'w',
                                encoding='utf-8'), ensure_ascii=False, indent=1)
print('official queue (effect ledger backlog): total=%d P0=%d P1=%d P2=%d yg=%d breakpoint=%d'
      % (official_queue['total_items'],
         official_queue['by_priority'].get('P0', 0), official_queue['by_priority'].get('P1', 0),
         official_queue['by_priority'].get('P2', 0), official_queue['yg_items'],
         official_queue['breakpoint_items']))
print('joined to enriched rows: %d; backlog rows outside enriched: %d'
      % (official_queue['joined_to_enriched_rows'], official_queue['backlog_rows_outside_enriched']))

# 已点亮 278 行的形状（供候选去重）
inf_rows = []
for r in yg_inf:
    if r['row_id'] in page:
        row, table = page[r['row_id']]
        inf_rows.append({'row_id': r['row_id'], 'table': table,
                         'inf_keys': sorted(k for k in row if k.startswith('inference_') and not k.endswith('_hint')),
                         'template': norm_text(r['text']), 'family': family_of(norm_text(r['text']))})
inf_fam = collections.Counter(x['family'] for x in inf_rows)
inf_keys_by_fam = {}
for x in inf_rows:
    inf_keys_by_fam.setdefault(x['family'], set()).update(x['inf_keys'])

# ---------- 4. 五类数值类型（重叠计数，按题给类型） ----------
TYPE_RE = {
    '攻撃（倍率/加算/速度）': r'攻撃力|攻撃速度|攻撃間隔|通常攻撃威力|与えるダメージ|威力',
    '减伤/固定防御': r'防御力|受けるダメージ|ダメージを受けなく|守り|防御',
    '暴击（率/伤害）': r'クリティカル',
    '回复（量/间隔）': r'回復',
    '时间（持续/间隔/冷却）': r'一定時間|秒|間隔|短縮|延長|再使用|クール',
}
def type_hits(text):
    hits = []
    for name, pat in TYPE_RE.items():
        if re.search(pat, text):
            hits.append(name)
    return hits

for e in enriched:
    e['types'] = type_hits(e['text'])

# 不相交主类型（单属性行用主类型；多类型行按优先级 暴击>回复>减伤/防御>攻撃>时间；纯时间/其他单列）
PRIORITY = ['暴击（率/伤害）', '回复（量/间隔）', '减伤/固定防御', '攻撃（倍率/加算/速度）', '时间（持续/间隔/冷却）']
for e in enriched:
    hits = e['types']
    if not hits:
        e['primary'] = '其他/移動速度等'
    elif len(hits) == 1:
        e['primary'] = hits[0]
    else:
        e['primary'] = min(hits, key=PRIORITY.index) + '（复合）'

# ---------- 5. 家族统计 ----------
fam = collections.defaultdict(lambda: {
    'rows': 0, 'cids': set(), 'tables': collections.Counter(),
    'texts': set(), 'types': collections.Counter(), 'primary': collections.Counter(),
    'inf_keys': set(), 'hint': 0, 'examples': [],
})
for e in enriched:
    d = fam[e['family']]
    d['rows'] += 1
    d['cids'].add(e['cid'])
    d['tables'][e['table']] += 1
    d['texts'].add(e['text'])
    for t in e['types']:
        d['types'][t] += 1
    d['primary'][e['primary']] += 1
    d['inf_keys'].update(e['inf_keys'])
    if e['hint_keys']:
        d['hint'] += 1
    if len(d['examples']) < 2:
        d['examples'].append({'cid': e['cid'], 'row_id': e['row_id'], 'text': e['text']})

fam_out = []
for k, d in fam.items():
    fam_out.append({
        'family': k, 'rows': d['rows'], 'cids': len(d['cids']),
        'unique_texts': len(d['texts']),
        'tables': dict(d['tables']), 'types': dict(d['types']),
        'primary': dict(d['primary']),
        'lit_before_families': inf_fam.get(k, 0),
        'inf_keys_same_family': sorted(inf_keys_by_fam.get(k, set())),
        'hint_rows': d['hint'],
        'examples': d['examples'],
    })
fam_out.sort(key=lambda x: -x['rows'])

# ---------- 6. Y.G. 独有机制标记 ----------
YG_MARKERS = {
    '共鳴必殺/超共鳴必殺': r'共鳴必殺',
    '共鳴アビリティ': r'共鳴アビリティ',
    '万象マナ': r'万象',
    '年代記/時空軍/未来所属': r'年代記|時空軍|未来',
    '設置/戦闘不能': r'設置|戦闘不能',
    '反響': r'反響',
    '時の楔': r'時の楔',
}
for f in fam_out:
    marks = [m for m, pat in YG_MARKERS.items() if re.search(pat, f['family'])]
    f['yg_markers'] = marks

# ---------- 7. 全库（非 Y.G.）剩余行，供通用模板收益单列 ----------
non_yg_texts = [r['text'] for r in non_yg_rem]
non_yg_norm = [norm_text(t) for t in non_yg_texts]
non_yg_fam = collections.Counter(family_of(t) for t in non_yg_norm)

# ---------- 8. rules.json 键与证据目录现状 ----------
rules = json.load(open('output/character_skills/profiles/rules.json', encoding='utf-8'))
rule_keys = list(rules.keys()) if isinstance(rules, dict) else [r.get('key') for r in rules]
sl_ets = collections.Counter(k.split('|')[1] if k.count('|') >= 1 else '?' for k in rule_keys if k.startswith('skilllist|'))
bs_ets = collections.Counter(k.split('|')[1] for k in rule_keys if k.startswith('bossskill|'))
ev_dirs = sorted(p for p in
                 ['output/ordinary_effects/ability%d' % int(e) for e in sl_ets if str(e).isdigit()]
                 if os.path.isdir(p))
print('rules.json keys=%d  skilllist|et top=%s  bossskill|et top=%s' % (len(rule_keys), sl_ets.most_common(12), bs_ets.most_common(12)))
print('evidence dirs:', ev_dirs)

out = {
    'yg_cids_n': len(yg_cids),
    'official_queue': official_queue,
    'coverage_counts': {'yg_remaining': len(enriched), 'yg_inferred': len(inf_rows),
                        'nonyg_remaining': len(non_yg_rem),
                        'yg_pages_C': total_c, 'yg_pages_A': total_a,
                        'mismatch_missing': len(mismatch['missing']), 'mismatch_not_C': len(mismatch['not_C'])},
    'type_overlap': dict(collections.Counter(t for e in enriched for t in e['types'])),
    'type_overlap_unique_texts': {t: len({e['text'] for e in enriched if t in e['types']}) for t in TYPE_RE},
    'type_primary': dict(collections.Counter(e['primary'] for e in enriched)),
    'type_primary_unique_texts': {p: len({e['text'] for e in enriched if e['primary'] == p}) for p in set(e['primary'] for e in enriched)},
    'inferred_families': inf_fam.most_common(30),
    'rules': {'n_keys': len(rule_keys), 'skilllist_ets': dict(sl_ets), 'bossskill_ets': dict(bs_ets),
              'evidence_dirs': ev_dirs},
}
json.dump(out, open('work/character_skills_yg_priority/inventory_summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(enriched, open('work/character_skills_yg_priority/yg_remaining_rows.json', 'w', encoding='utf-8'), ensure_ascii=False)
json.dump(fam_out, open('work/character_skills_yg_priority/yg_remaining_families.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump({'families': {k: v for k, v in non_yg_fam.most_common()},
           'rows': len(non_yg_rem)},
          open('work/character_skills_yg_priority/nonyg_remaining_families.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('--- type overlap ---')
for t, n in out['type_overlap'].items():
    print('%s: rows=%d unique=%d' % (t, n, out['type_overlap_unique_texts'][t]))
print('--- type primary (disjoint) ---')
for p, n in sorted(out['type_primary'].items(), key=lambda x: -x[1]):
    print('%s: rows=%d unique=%d' % (p, n, out['type_primary_unique_texts'][p]))
print('--- top 25 remaining families ---')
for f in fam_out[:25]:
    print('%5d rows %3d cid u%d  %s  %s' % (f['rows'], f['cids'], f['unique_texts'],
          ','.join('%s:%d' % x for x in f['tables'].items()), f['family'][:60]))
print('--- inferred 278 families ---')
for k, n in inf_fam.most_common(30):
    print('%5d  %s' % (n, k[:70]))
