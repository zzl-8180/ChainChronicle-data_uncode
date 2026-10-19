"""Offline, escaped card-detail layout and sample audit view."""
import html
import json
from card_page_policy import summary_text,INFERENCE_STATUS


def esc(value): return html.escape('' if value is None else str(value),quote=True)
def pretty(value): return json.dumps(value,ensure_ascii=False,indent=2)

CSS='''
:root{--paper:#f6f4ed;--panel:#fffefb;--ink:#243448;--muted:#617083;--line:#dce0dd;--gold:#aa7b2d;--ok:#176349;--warn:#8c5e15;--soft:#edf3ef}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.75 system-ui,"Microsoft YaHei",sans-serif}a{color:#245a78;text-underline-offset:3px}a:focus-visible,summary:focus-visible{outline:3px solid #c19136;outline-offset:4px}main{max-width:1260px;margin:auto;padding:32px 30px 70px}h1,h2,h3,p{margin:0}h1{font-size:34px;line-height:1.3;font-weight:700}h2{font-size:22px}h3{font-size:19px;line-height:1.5}.eyebrow{font-size:12px;letter-spacing:.15em;text-transform:uppercase;color:var(--gold);font-weight:700}.muted{color:var(--muted)}.small{font-size:12px}.card-head{display:grid;grid-template-columns:1fr 190px;gap:26px;background:#233b50;color:white;padding:36px;border-radius:14px}.card-head .muted{color:#d1dbe0}.title{font-size:17px;margin:8px 0 18px}.seal{border:1px solid #81939f;border-radius:10px;display:flex;align-items:center;justify-content:center;min-height:155px;text-align:center;padding:18px;color:#e0e6ea;font-size:13px}.meta{display:flex;flex-wrap:wrap;gap:8px}.pill{border:1px solid #d1d9df;border-radius:5px;padding:2px 8px;display:inline-block;font-size:12px;white-space:normal}.card-head .pill{border-color:#60788b}.intro{margin:22px 0;padding:17px 20px;background:#fff9e9;border-left:3px solid var(--gold);border-radius:4px}.basic{margin:26px 0}.basic-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin:16px 0;border-top:1px solid var(--line);border-left:1px solid var(--line)}.basic-item{margin:0;padding:12px 16px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);background:var(--panel);overflow-wrap:anywhere}.basic-item dt{color:var(--muted);font-size:12px}.basic-item dd{margin:4px 0 0;font-weight:600}.basic-item.wide{grid-column:1/-1}.layout{display:grid;grid-template-columns:170px minmax(0,1fr);gap:28px;align-items:start}.skill-groups{position:sticky;top:24px;display:flex;flex-direction:column;gap:3px;border-left:2px solid var(--line);padding-left:12px}.skill-groups a{text-decoration:none;color:var(--muted);padding:6px 10px;font-size:13px}.skill-groups a:hover{background:#e8edea;color:var(--ink)}.skill-group{margin-bottom:30px;scroll-margin-top:20px}.group-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline;border-bottom:2px solid #a6b4b7;padding:0 0 9px;margin-bottom:16px}.empty{padding:16px 20px;background:#eeefeb;border-radius:6px;color:var(--muted)}.skill{background:var(--panel);border:1px solid var(--line);border-radius:10px;margin:0 0 18px;overflow:hidden}.skill-head{padding:18px 22px;border-bottom:1px solid var(--line);background:#f3f4ee}.skill-head .meta{margin:8px 0}.effect-row{padding:18px 22px;border-bottom:1px solid var(--line);scroll-margin-top:24px;overflow-wrap:anywhere}.effect-row:last-child{border-bottom:0}.effect-row[data-row-class=A]{border-left:3px solid #368869}.effect-row[data-row-class=B]{border-left:3px solid #b88831}.effect-row[data-row-class=C]{border-left:3px solid #b4bdc4}.jp{font-family:"Yu Gothic","Meiryo",system-ui,sans-serif;font-size:16px;line-height:1.85;white-space:pre-wrap}.row-meta{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}.e-confirm{color:#175d47;background:#e8f2eb}.e-infer{color:#795318;background:#fff1d7}.e-unknown{color:#556171;background:#edf0f3}.value{display:block;margin:7px 0;padding:9px 12px;background:var(--soft);border-radius:5px;font-size:14px}.value strong{font-size:12px;margin-right:7px;color:#356349}.conditions{display:block;font-size:12px;color:#536958;margin-top:4px;white-space:pre-wrap}.unknown{font-size:13px;color:#6c5b45;background:#faf5ea;border-radius:4px;padding:9px 12px;margin-top:9px}.source{margin-top:10px;color:var(--muted);font-size:12px}.source summary{cursor:pointer;padding:5px 0}.source pre{max-height:440px;overflow:auto;white-space:pre-wrap;background:#f0f2ef;padding:14px;border-radius:5px;word-break:break-word}.coverage{margin-top:32px;padding:24px;background:#e8ede9;border-radius:8px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);background:#f0f2ed}.table-wrap{overflow:auto}.audit{max-width:1400px}.audit td{min-width:130px}.audit .jp{font-size:14px}.audit td:first-child{min-width:90px}.audit td:last-child{max-width:470px}code{font-size:12px;overflow-wrap:anywhere}footer{color:var(--muted);font-size:12px;margin-top:22px}
@media(max-width:900px){main{padding:20px 18px 50px}.basic-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.layout{grid-template-columns:1fr}.skill-groups{position:static;flex-direction:row;flex-wrap:wrap;padding:8px 0;border:0;border-bottom:1px solid var(--line);gap:3px}.skill-groups a{padding:5px 9px}.card-head{padding:25px;grid-template-columns:1fr 145px}.seal{min-height:120px}h1{font-size:28px}}
@media(max-width:540px){main{padding:12px 12px 36px}.card-head{grid-template-columns:1fr;padding:23px}.seal{min-height:64px}.basic-grid{grid-template-columns:1fr}.basic-item.wide{grid-column:auto}.effect-row,.skill-head{padding:15px 16px}.jp{font-size:15px}.group-head{gap:8px}h2{font-size:21px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
'''


def details(label,value): return '<details class="source"><summary>'+esc(label)+'</summary><pre>'+esc(pretty(value))+'</pre></details>'


def answer_html(a):
    value='<span class="value"><strong>'+esc(a['numeric_source'])+' · '+esc(a['numeric_evidence'])+'</strong>'+esc(a['value'])
    conditions=[]
    for key,label in [('target','对象'),('conditions','条件'),('duration','时间'),('note','注'),('rule_limits','限制')]:
        if a.get(key): conditions.append(label+'：'+str(a[key]))
    if conditions: value+='<span class="conditions">'+esc('\n'.join(conditions))+'</span>'
    return value+'</span>'


def row_html(row):
    cls={'确认':'e-confirm','推断':'e-infer','未知':'e-unknown'}[row['evidence']]
    out=f'<div class="effect-row" id="{esc(row["row_id"])}" data-row-id="{esc(row["row_id"])}" data-row-class="{row["row_class"]}" data-evidence="{row["evidence"]}">'
    out+='<p class="jp" lang="ja">'+esc(row['japanese'])+'</p><div class="row-meta">'
    out+='<span class="pill">'+row['row_class']+(' · 部分填充' if row['partial'] else '')+'</span>'
    out+='<span class="pill '+cls+'">整行证据：'+row['evidence']+'</span>'
    out+='<span class="pill e-confirm">数值：'+row['numeric_evidence']+'</span>' if row['row_class']=='A' else ''
    out+='<span class="pill">字段／描述关联：'+row['association_evidence']+'</span></div>'
    out+=''.join(answer_html(a) for a in row['answers'])
    if row['unknown_reasons']: out+='<p class="unknown">'+esc(row['raw_state_summary']+'；'+'；'.join(row['unknown_reasons']))+'</p>'
    out+=details('来源、原值状态与逐项证据',row)
    return out+'</div>'


def page(card):
    cid=card['cid']; basic=card['basic']; fields={f['key']:f for f in basic['fields']}; cov=card['coverage']
    name=fields['name']['raw_value']; title=fields['title']['raw_value']; rarity=fields['rarity']['raw_value']
    body='<main class="card"><header class="card-head"><div><p class="eyebrow">CHAIN CHRONICLE · SKILL NOTES</p><p class="title" lang="ja">'+esc(title)+'</p><h1 lang="ja">'+esc(name)+'</h1><div class="meta" style="margin-top:20px"><span class="pill">CID '+str(cid)+'</span><span class="pill">'+esc(rarity)+'★</span><span class="pill">'+esc(basic['layer'])+' · 声明输入版本</span></div></div><div class="seal">'+esc(basic['card_art']['note'])+'</div></header>'
    body+='<p class="intro">每行保留日文原文。A＝数值／公式，B＝新增机制，C＝仅未知。数值证据与字段关联分别标注；原文数字不代表已证实参数归属。独立审查状态见同目录报告。</p>'
    body+='<p class="intro">'+esc(summary_text(card['summary']))+'</p><p class="small">'+esc(INFERENCE_STATUS['message']+'；'+INFERENCE_STATUS['zero_inference_meaning']+'。B=0：'+INFERENCE_STATUS['B_zero_reason'])+'</p>'
    body+='<section class="basic"><h2>基础信息</h2><dl class="basic-grid">'
    for f in basic['fields']:
        value='缺失' if f['raw_state']=='missing' else 'null' if f['raw_state']=='null' else f['raw_value']
        value=f.get('display_value',value)
        if isinstance(value,(list,dict)): value=pretty(value)
        body+='<div class="basic-item'+(' wide' if f['key']=='profile' else '')+'"><dt>'+esc(f['label'])+'</dt><dd>'+esc(value)+'</dd><p class="small muted">'+esc(f['note'])+'</p>'+details('原值、格式化依据及字段来源',f)+'</div>'
    body+='</dl><div class="meta">'
    for item in basic['external']: body+='<span class="pill">'+esc(item['label'])+'：'+esc(item['value'])+'</span>'
    body+='</div></section><div class="layout"><nav class="skill-groups" aria-label="技能分组">'
    body+=''.join('<a href="#group-'+g['group']+'">'+esc(g['label'])+'</a>' for g in card['groups'])+'</nav><div>'
    for g in card['groups']:
        body+='<section class="skill-group" id="group-'+g['group']+'" data-group="'+g['group']+'"><div class="group-head"><h2>'+esc(g['label'])+'</h2><span class="small muted">'+esc(g['status'])+'</span></div>'
        if not g['skills'] and not g['annotations']: body+='<p class="empty">本输入快照未见配置／未关联；不代表游戏没有此组。</p>'
        if g['unresolved']: body+='<p class="unknown">关联缺失：存在未解析引用；原始引用保留如下。</p>'+details('未解析引用',g['unresolved'])
        for annotation in g['annotations']:
            body+='<p class="empty">'+esc(annotation.get('slot',''))+' = '+esc(annotation.get('raw_value'))+'；必杀效果类型，非技能引用，不计描述分母。</p>'+details('类型标注来源',annotation)
        for s in g['skills']:
            body+='<article class="skill"><header class="skill-head"><p class="eyebrow">'+esc(s['stage'])+'</p><h3 lang="ja">'+esc(s['name'] or '未命名配置')+'</h3><div class="meta"><span class="pill">'+esc(s['table'])+' #'+esc(s['record_id'])+'</span><span class="pill">'+esc(s['layer'])+'</span>'
            if s['cost_state'] not in ('missing','null'): body+='<span class="pill">耗玛那原值 '+esc(s['cost'])+'</span>'
            body+='</div><p class="small muted">'+esc(s['level_note'])+'</p>'
            if s['association_evidence']=='推断': body+='<p class="unknown">角色／技能关联：推断。保留原有ID模式关联，未升级为运行时确认。</p>'
            if s['forward_links']: body+='<p class="small">确认·链上复用（str0转发已证）：'+str(len(s['forward_links']))+'个目标关联；具体数值仅在已证句内归属时列入正文。</p>'
            if s['baseline_metadata_answers']:
                body+='<p class="small">既有条件档位／配置答案（不新增描述分母）：</p>'+''.join(answer_html(a) for a in s['baseline_metadata_answers'])
            body+=details('完整原文、原始记录引用、目标规则与门控', {k:v for k,v in s.items() if k!='rows'})+'</header>'
            body+=''.join(row_html(r) for r in s['rows'])
            if not s['rows']: body+='<div class="empty">'+esc(s['empty_reason'])+'</div>'
            body+='</article>'
        body+='</section>'
    body+='</div></div><footer class="coverage"><h2>本页处理状态</h2><p>'+esc(summary_text(card['summary']))+'</p><p>A '+str(cov['A'])+' / '+str(cov['N_num'])+'＝'+f'{cov["A_rate"]:.1%}'+'；B '+str(cov['B'])+'；C '+str(cov['C'])+'。全部描述 '+str(cov['N_all'])+'，排除 E='+str(cov['E'])+'，A部分填充 '+str(cov['partial_A'])+'。</p><p>原文A '+str(cov['original_A'])+'；链新增A '+str(cov['chain_new_A_rows'])+'。旧确认＋提示仅作历史参考，不冒充新A率。</p>'+details('证据交叉数量、来源与旧→新行映射',dict(coverage=cov,sources=card['sources']))+'</footer><footer>输入：'+esc(card['sources']['snapshot'])+'。网站一致／差异待实际对照，外部资料不覆盖本页原值。未实机验证。</footer></main>'
    payload=pretty(card).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(name)+' · '+str(cid)+' 技能解读</title><style>'+CSS+'</style></head><body>'+body+'<script type="application/json" id="card-data">'+payload+'</script></body></html>'


def audit_page(rows):
    body='<main class="audit"><p class="eyebrow">PILOT · IMPLEMENTATION AUDIT</p><h1>11张样本逐行抽查表</h1><p class="intro">每卡10个不同实际行；不足10行则全列。此表保存实施自检抽样，独立R2另行审查。链接直达页面对应行。</p><div class="table-wrap"><table><thead><tr><th>角色／档位</th><th>日文原文</th><th>分类与证据</th><th>数值／公式／机制</th><th>来源及未解项</th></tr></thead><tbody>'
    for r in rows:
        body+='<tr><td><a href="'+str(r['cid'])+'/index.html#'+esc(r['row_id'])+'">CID '+str(r['cid'])+'</a><br>'+esc(r['group'])+'<br>'+esc(r['stage'])+'</td><td class="jp" lang="ja">'+esc(r['japanese'])+'</td><td>'+r['row_class']+'<br>整行：'+r['evidence']+'<br>数值：'+r['numeric_evidence']+'<br>关联：'+r['association_evidence']+'</td><td>'+''.join(answer_html(a) for a in r['answers'])+'</td><td><p>'+esc('；'.join(r['unknown_reasons']))+'</p>'+details('定位与证据',r)+'</td></tr>'
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>样本实际行抽查</title><style>'+CSS+'</style></head><body>'+body+'</tbody></table></div></main></body></html>'
