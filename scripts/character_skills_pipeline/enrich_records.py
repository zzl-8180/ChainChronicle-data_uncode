# -*- coding: utf-8 -*-
"""Y.G. 优先清单 · 步骤2：对官方队列选题视图（yg_backlog_view.json）做记录级富化。

DS-GR-02 修复（20261023 DeepSeek 整改审查）：本脚本原先读取 yg_remaining_rows.json
（2,066 行 coverage_refined Y.G. 旧池），使官方 backlog 未成为实际选题输入。现改为：

输入：
- work/character_skills_yg_priority/yg_backlog_view.json —— 步骤1（build_inventory）从
  当前 effect_ledger/backlog.json 派生的选题视图（P0 断点 ∪ Y.G. 项；backlog 78,427 项
  为正式队列，本视图为其 Y.G./断点子集）；
- output/character_skills/profiles/records.jsonl（顶层记录 effect_type 与 children）；
- output/character_skills/pages/<cid>/card.json（row_id → table/record_id/日文原文定位）。

输出：work/character_skills_yg_priority/yg_backlog_view_enriched.json（逐 backlog 项附
页面行定位与记录 effect_type，供 assign_candidates 选题）＋ 控制台汇总。
只读 pages/profiles/backlog；输出仅写本目录。
"""
import json, re, sys, io, collections, os, unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(ROOT)

VIEW = 'work/character_skills_yg_priority/yg_backlog_view.json'
OUT = 'work/character_skills_yg_priority/yg_backlog_view_enriched.json'

items = json.load(open(VIEW, encoding='utf-8'))
print('yg_backlog_view items:', len(items))

# records.jsonl 索引：key = f'{table}|{record_id}'
rec = {}
with open('output/character_skills/profiles/records.jsonl', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        rec['%s|%s' % (d.get('table'), d.get('record_id'))] = d
print('records.jsonl loaded:', len(rec))

# 行 → 记录：row_id → (table, record_id)（经 pages card.json；row_id 前缀 cid）
def iter_page_rows(cid):
    d = json.load(open('output/character_skills/pages/%d/card.json' % cid, encoding='utf-8'))
    for grp in d['groups']:
        for sk in grp.get('skills', []):
            for row in sk.get('rows', []):
                yield row, sk.get('table'), sk.get('record_id')

row2rec = {}
row_text = {}
row_context = {}
row_group = {}
cids = sorted({it['cid'] for it in items})
for cid in cids:
    d = json.load(open('output/character_skills/pages/%d/card.json' % cid, encoding='utf-8'))
    for grp in d['groups']:
        for sk in grp.get('skills', []):
            for row in sk.get('rows', []):
                row2rec[row['row_id']] = (sk.get('table'), sk.get('record_id'))
                row_text[row['row_id']] = row.get('japanese')
                row_context[row['row_id']] = row.get('context_text')
                row_group[row['row_id']] = grp.get('group')

enriched = []
miss_row = miss_rec = miss_span = 0

# R3 整改（20261023 复审 §R3）：效果项不再只传 snippet（「攻撃力」「ダメージ」等片段——
# 旧句式分类器需要完整语境，7,157 效果项全部落入 G9 兜底）。逐效果定位上下文：
#   * 片段（snippet）→ span（由 ledger.jsonl effect 条目按 backlog_id==effect_id 关联取回；
#     未命中时在行 NFKC 文本中定位首次出现）；
#   * span 所在子句（「。、！？」切分，与 effect_ledger._CLAUSE_RE 同法）与所在全句
#     （「。」切分）；
#   * 完整描述＝行日文（japanese）＋行上下文全文（context_text）；
#   * 技能类别＝page_group/page_table。
# 目标效果（effect_type/snippet）参与分类的方式＝用其 span 定位该效果**自己**的子句/全句
# 语境——多效果描述逐效果各归各的语境，不把整条描述交给「全文首匹配」；一项效果可命中
# 多个候选时主分类按 CANDS 序取首个、其余记入 also_candidates 单列计数（assign_candidates）。

_CLAUSE_RE = re.compile(r'[^。、！？\n]+')
_SENT_RE = re.compile(r'[^。！？\n]*[。！？]?')


def locate(text_n, span=None, snippet=None):
    """返回 (clause, sentence, span_used)；定位失败返回 (None, None, None)。"""
    seg = None
    start = None
    if span and 0 <= span[0] < span[1] <= len(text_n):
        seg = text_n[span[0]:span[1]]
        start = span[0]
    elif snippet and snippet in text_n:
        start = text_n.find(snippet)
        seg = text_n[start:start + len(snippet)]
    if seg is None:
        return None, None, None
    end = start + len(seg)
    clause = sent = None
    for m in _CLAUSE_RE.finditer(text_n):
        if m.start() <= start and end <= m.end():
            clause = m.group(0)
            break
    for m in _SENT_RE.finditer(text_n):
        if m.start() <= start and end <= m.end() and m.group(0).strip():
            sent = m.group(0)
            break
    return clause, sent, [start, end]


# 账本 effect 条目索引：effect_id → span（账本 NFKC 文本坐标系）
ledger_span = {}
if os.path.exists('output/character_skills/effect_ledger/ledger.jsonl'):
    with open('output/character_skills/effect_ledger/ledger.jsonl', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            if d.get('record_type') == 'effect':
                ledger_span[d['effect_id']] = d.get('span')

for it in items:
    e = dict(it)
    tr = row2rec.get(it['row_id'])
    if tr is None:
        miss_row += 1
        e['page_table'] = e['page_record_id'] = None
        e['rec_effect_type'] = None
        e['children_ets'] = []
        e['japanese'] = row_text.get(it['row_id'])
    else:
        table, rid = tr
        e['page_table'], e['page_record_id'] = table, rid
        e['japanese'] = row_text.get(it['row_id'])
        d = rec.get('%s|%s' % (table, rid))
        e['rec_effect_type'] = d.get('effect_type') if d else None
        e['children_ets'] = [ch.get('effect_type') for ch in (d.get('children') or [])] if d else []
        if d is None:
            miss_rec += 1
    e['page_group'] = row_group.get(it['row_id'])
    e['context_text'] = row_context.get(it['row_id'])
    text_n = unicodedata.normalize('NFKC', e.get('japanese') or '')
    # 选题文本：effect 项保留片段（text=snippet，逐效果定位语境另附）；split 项用行日文全文
    e['text'] = it.get('snippet') or ''
    if it.get('kind') != 'effect' and e['japanese']:
        e['text'] = e['japanese']
        e['sentence'] = e['japanese']
        e['clause'] = None
        e['span_in_row'] = None
    else:
        clause, sent, span = locate(text_n, ledger_span.get(it['backlog_id']),
                                    it.get('snippet')) if e['japanese'] else (None, None, None)
        if it.get('kind') == 'effect' and e['japanese'] and clause is None:
            miss_span += 1
        e['clause'] = clause
        e['sentence'] = sent
        e['span_in_row'] = span
    enriched.append(e)

summary = dict(
    view_items=len(enriched),
    by_kind=dict(collections.Counter(e['kind'] for e in enriched)),
    by_priority=dict(collections.Counter(e.get('priority') or 'P2' for e in enriched)),
    yg_items=sum(1 for e in enriched if e.get('yg')),
    breakpoint_items=sum(1 for e in enriched if e.get('breakpoint')),
    row_join_missing=miss_row, record_join_missing=miss_rec,
    effect_context_missing=miss_span,
    effect_context_stats=dict(
        effect_items=sum(1 for e in enriched if e.get('kind') == 'effect'),
        effect_items_with_clause=sum(1 for e in enriched
                                     if e.get('kind') == 'effect' and e.get('clause')),
        effect_items_with_sentence=sum(1 for e in enriched
                                       if e.get('kind') == 'effect' and e.get('sentence')),
        effect_items_with_context_text=sum(1 for e in enriched
                                           if e.get('kind') == 'effect' and e.get('context_text'))),
    by_page_group=dict(collections.Counter(str(e.get('page_group')) for e in enriched)),
    effect_type_top=dict(collections.Counter(str(e.get('effect_type')) for e in enriched).most_common(12)),
    source_view=VIEW,
    note='官方队列选题视图（build_inventory 自当前 effect_ledger/backlog.json 派生）的记录级富化；'
         'R3 整改（20261023 复审 §R3）：效果项逐效果定位语境（片段→span→子句/全句）＋完整'
         '描述（japanese+context_text）＋技能类别（page_group/page_table），不再只传 snippet'
         '（R3 前 7,157 效果项全部落入 G9 兜底）；backlog_id 与来源字段原样保留；'
         '不再以 coverage_refined 2,066 行旧池为选题输入（DS-GR-02 修复，20261023）',
)
json.dump(dict(summary=summary, items=enriched), open(OUT, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
