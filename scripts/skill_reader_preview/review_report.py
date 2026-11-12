"""Build the acceptance report from completed review and validation receipts."""
from collections import Counter
from html import escape
from hashlib import sha256
from pathlib import Path
import json,re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path
from merge_semantic_review import collect,AUDIT,ROOT


def read(path):
    return json.loads(read_path(path, root=ROOT).read_text(encoding='utf8'))


def main():
    summary,results=collect()
    if not summary['complete']:
        raise ValueError('Review incomplete; acceptance report cannot be generated')
    out=ROOT/'output/character_skills/reader_full_20261106'
    validation=read(out/'validation.json')
    if not validation['passed'] or validation.get('semanticReviewUnits')!=summary['expectedUnits']:
        raise ValueError('Current complete semantic review must pass full validation first')
    units=read(AUDIT/'units.json')
    receipt=read(out/'build_receipt.json')
    master_path=Path(__file__).parent/'semantic_sentences.json'
    master=read(master_path)
    if receipt['adapterHashes'].get(master_path.name)!=sha256(master_path.read_bytes()).hexdigest():
        raise ValueError('Reader was not built from current semantic review')
    if any(master['units'][uid]['resultHash']!=r['resultHash'] for uid,r in results.items()):
        raise ValueError('Review results changed after merge; merge and rebuild first')
    changed=[];ambiguities=[];row_verdicts=Counter()
    for line in read_path(AUDIT/'rows.jsonl', root=ROOT).read_text(encoding='utf8').splitlines():
        row=json.loads(line);row_verdicts[results[row['unitId']]['verdict']]+=1
    for uid,result in results.items():
        if result.get('displayNote'):
            ambiguities.append({'unitId':uid,'exampleRow':units[uid]['exampleRow'],'note':result['displayNote']})
        if result['verdict']!='corrected':continue
        unit=units[uid]
        zh=re.sub(r'\{n(\d+)\}',lambda m:unit['numbers'][int(m[1])],result['zhPattern'])
        changed.append({'unitId':uid,'cid':unit['exampleRow'].split('-')[0],
                        'exampleRow':unit['exampleRow'],'japanese':unit['japanese'],
                        'before':unit['currentChinese'],'after':zh,'note':result.get('note',''),
                        'occurrences':unit['occurrences'],'packet':result['packet']})
    changed.sort(key=lambda x:(-x['occurrences'],int(x['cid'])))
    report={'passed':True,'cards':receipt['summary']['cards'],'descriptions':receipt['detailRows'],
            'answers':validation['counts']['sourceAnswers'],'units':summary['expectedUnits'],
            'unitVerdicts':summary['verdicts'],'rowVerdicts':dict(row_verdicts),
            'snapshot':receipt['snapshot'],'builtAt':receipt['builtAt'],
            'verifiedAt':validation['verifiedAt'],'sourceAmbiguities':ambiguities,'corrections':changed}
    write_path(out/'audit/semantic_review.json', root=ROOT).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    esc=lambda s:escape(str(s or ''))
    ambiguity_html=''.join(f'<li><a href="../#card={esc(a["exampleRow"].split("-")[0])}">角色 {esc(a["exampleRow"].split("-")[0])}</a>：{esc(a["note"])}</li>' for a in ambiguities)
    cards=[]
    for item in changed:
        cards.append(f'''<article><h3><a href="../#card={esc(item['cid'])}">角色 {esc(item['cid'])}</a>
          <small>同句式覆盖 {item['occurrences']} 条描述</small></h3>
          <dl><dt>日文原句</dt><dd lang="ja">{esc(item['japanese'])}</dd>
          <dt>修改前</dt><dd class="before">{esc(item['before'])}</dd>
          <dt>修改后</dt><dd class="after">{esc(item['after'])}</dd>
          <dt>核对说明</dt><dd>{esc(item['note'])}</dd></dl>
          <details><summary>定位</summary>{esc(item['exampleRow'])} · {esc(item['packet'])} · {esc(item['unitId'])}</details></article>''')
    html=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>全库语义排查验收</title><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#11101a;color:#eee9f5;font:16px/1.7 system-ui,sans-serif}}
    main{{max-width:1050px;margin:auto;padding:28px 22px 70px}}a{{color:#a8d7ef}}h1{{font-size:30px;line-height:1.3}}
    .stats{{display:flex;gap:16px;flex-wrap:wrap}}.stats p{{background:#242033;padding:14px 20px;border-radius:12px}}
    b{{color:#a9dfbd}}small,dt,details{{color:#bbb4c8}}article{{padding:15px 0 25px;border-top:1px solid #40394c}}
    dd{{margin:0 0 12px;overflow-wrap:anywhere}}dt{{font-size:13px}}h3{{margin-bottom:8px}}small{{font-weight:400;font-size:13px;margin-left:10px}}
    .before{{color:#d9b8a6}}.after{{color:#afe2c0}}input{{width:100%;padding:13px;background:#242033;color:inherit;border:1px solid #79718b;border-radius:8px;font:inherit}}
    summary{{cursor:pointer}}:focus-visible{{outline:3px solid #b5d7ff;outline-offset:3px}}[hidden]{{display:none}}
    </style><main><nav><a href="../">角色目录</a> · <a href="../#all">全部角色索引</a></nav>
    <h1>全库语义排查验收</h1><p>已有中文与此前缺译的内容均纳入本轮核对。下方列出旧中文修正，原文和修改前后可以直接比较。</p>
    <div class="stats"><p><b>{report['cards']:,}</b> 名角色</p><p><b>{report['descriptions']:,}</b> 条描述</p>
    <p><b>{report['answers']:,}</b> 项现有答案</p><p><b>{report['units']:,}</b> 种完整句式</p></div>
    <p>句式审查：保留 {summary['verdicts'].get('pass',0):,} 项，修正旧中文 {len(changed):,} 项，补译 {summary['verdicts'].get('translated',0):,} 项。相同完整句式仅合并文字审查，每行的实际数字、来源与条件仍分别核验。</p>
    <p>文字由子代理逐项对照日文复核；数值按计算含义和条件表达审查，再对全部行运行来源、参数、显示与条件绑定检查。程序检查与文字审查分别留存。此报告不代表实机验证，也不把未知数值或推断条件提升为已确认。</p>
    <p>本轮修复了多档数值遗漏、法珠条件泛化、分号后限制丢失、回复量提高误读、零法珠条件，以及局部强化被错误前置等问题。每项答案仍保留原始置信度与依据。</p>
    <p>仍需证据确认的原文歧义：</p><ul>{ambiguity_html}</ul>
    <p><a href="semantic_review.json">完整修正清单 JSON</a> · <a href="translation_rows.jsonl">逐条描述与审查定位</a> · <a href="../validation.json">全量校验结果</a> · <a href="../../reader_semantic_20261107/review_progress.json">分片覆盖清单</a></p>
    <p>构建时间：{esc(report['builtAt'])}；验收时间：{esc(report['verifiedAt'])}。这是冻结快照的验收；主线更新后需重新核对变化并构建。</p>
    <h2>旧中文修正清单</h2><label for="search">搜索角色编号、原句、中文或核对说明</label><input id="search" type="search" placeholder="例如：法珠、后备、350">
    <p id="count">共 {len(changed)} 项修正</p><section>{''.join(cards)}</section>
    <script>const items=[...document.querySelectorAll('article')];document.querySelector('#search').addEventListener('input',e=>{{const q=e.target.value.toLowerCase().trim();let n=0;for(const el of items){{el.hidden=!el.textContent.toLowerCase().includes(q);if(!el.hidden)n++}}document.querySelector('#count').textContent=`显示 ${{n}} / ${{items.length}} 项修正`}});</script></main></html>'''
    write_path(out/'audit/semantic_review.html', root=ROOT).write_text(html,encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('corrections','snapshot')},ensure_ascii=False))


if __name__=='__main__':main()
