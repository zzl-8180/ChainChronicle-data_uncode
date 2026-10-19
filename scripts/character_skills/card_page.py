"""Build only the authorized eleven pilot cards; no full-roster mode."""
import argparse
import collections
import hashlib
import json
import sys
import time
from pathlib import Path
from html.parser import HTMLParser

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from card_page_data import Inputs,SAMPLES,GROUPS,build_card,original_numbers
from card_page_render import page,audit_page
from card_page_policy import metrics,summary_text,INFERENCE_STATUS


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


class VerifyHTML(HTMLParser):
    def __init__(self): super().__init__(); self.rows=[]; self.groups=[]; self.jp=[]; self.in_jp=False; self.payload=''; self.in_payload=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'data-row-id' in a: self.rows.append((a['data-row-id'],a['data-row-class'],a['data-evidence']))
        if 'data-group' in a: self.groups.append(a['data-group'])
        if tag=='p' and a.get('class')=='jp': self.in_jp=True; self.jp.append('')
        if tag=='script' and a.get('id')=='card-data': self.in_payload=True
    def handle_endtag(self,tag):
        if tag=='p': self.in_jp=False
        if tag=='script': self.in_payload=False
    def handle_data(self,data):
        if self.in_jp:self.jp[-1]+=data
        if self.in_payload:self.payload+=data


def choose_samples(card):
    rows=[r for g in card['groups'] for s in g['skills'] for r in s['rows']]
    if len(rows)<=10:return rows
    selected=[]
    def take(row):
        if row and row not in selected:selected.append(row)
    # Existing A/B/C, multiple groups, stages and source types; deterministic.
    for cls in ('A','B','C'):take(next((r for r in rows if r['row_class']==cls),None))
    for group,_ in GROUPS:take(next((r for r in rows if r['group']==group),None))
    if len(selected)>10:selected=selected[:10]
    # Prefer source-aware baseline risk rows (Chain, fixed defence, different stages).
    risk=[r for r in rows if any(a.get('effect_id') and any(k in a['effect_id'] for k in ('guard','front','param4','chain','interval')) for a in r['answers'])]
    if card['cid']==30236:
        mandatory=[]
        for pid in (43023601,43023600,43023602):
            mandatory.append(next((r for r in rows if any(a.get('record_id')==pid and a.get('effect_id') for a in r['answers'])),None))
        for row in reversed(mandatory):
            if row and row not in selected:selected.insert(0,row)
        selected=selected[:10]
    for row in risk+list(reversed(rows))+rows:
        if len(selected)>=10:break
        take(row)
    return selected


def validate(card,html):
    parser=VerifyHTML();parser.feed(html)
    rows=[r for g in card['groups'] for s in g['skills'] for r in s['rows']]
    assert parser.groups==[g[0] for g in GROUPS]
    assert parser.rows==[(r['row_id'],r['row_class'],r['evidence']) for r in rows]
    assert parser.jp==[r['japanese'] for r in rows]
    assert json.loads(parser.payload)==card
    assert len({r['row_id'] for r in rows})==len(rows)
    c=card['coverage'];assert c['A']+c['B']+c['C']==c['N_all']==c['N_num'] and c['E']==0
    assert all(r['answers'] for r in rows if r['row_class']=='A')
    assert all(r['unknown_reasons'] for r in rows if r['row_class']=='C')
    assert all(r['original_A'] <= (r['row_class']=='A') for r in rows)
    return dict(cid=card['cid'],passed=True,groups=13,rows=len(rows),json_html_consistent=True,
                original_text_preserved=True,sample_count=min(10,len(rows)))


def report(cards,checks,elapsed,out,stage="R2_PREPARATION_PENDING_INDEPENDENT_REVIEW"):
    samples=[r for card in cards for r in choose_samples(card)]
    for card in cards:
        n=sum(r['cid']==card['cid'] for r in samples)
        assert n==min(10,card['coverage']['N_all'])
    stats=[dict(cid=c['cid'],summary=c['summary'],**c['coverage']) for c in cards]
    cids=[c['cid'] for c in cards]
    rep=dict(status=stage,cids=cids,
             statistics=stats,validation=checks,generation_seconds=round(elapsed,3),
             old_reference=dict(core10='63/322=19.6% 确认+提示',all11='79/384=20.6% 确认+提示',not_new_A_rate=True),
             denominator_policy='N_all按cid/13组/实际引用/档位等级/真实片段；E=0；不计空组/内部标签，不因未知删行',
             original_A_manifest=[dict(cid=r['cid'],row_id=r['row_id'],japanese=r['japanese'],numeric_items=r['original_numeric_items']) for c in cards for g in c['groups'] for s in g['skills'] for r in s['rows'] if r['original_A']],
             chain_policy='原文A先建立；链目标已有规则只在来源层复用，未证句内归属不把规则列表挂到每句；新增A/新增行内数值均0',
             samples=samples,all_7229_B=[r for c in cards if c['cid']==7229 for g in c['groups'] for s in g['skills'] for r in s['rows'] if r['row_class']=='B'],
             denominator_changes=[dict(cid=c['cid'],old=c['coverage']['old_descriptions'],new=c['coverage']['N_all'],
                                       leader_sympathy_added=c['coverage']['leader_sympathy_rows_added'],
                                       internal_labels_excluded=c['coverage']['internal_labels_excluded'],
                                       actual_repeat_occurrences_retained=c['coverage']['repeated_actual_occurrences_retained']) for c in cards],
             variant_metadata_audit=[dict(cid=c['cid'],skill_id=s['skill_id'],record_id=s['record_id'],source=s['source'],
                                          name=s['name'],original_text=s['original_text'],answers=s['baseline_metadata_answers'],
                                          counted_in_N_all=False) for c in cards if c['cid']==30236 for g in c['groups'] for s in g['skills']
                                     if s['record_id']==43023600 and s['baseline_metadata_answers']],
             baseline_30236=[dict(effect_id=k,mapped_row_ids=v['mapped_row_ids'],mapped_skill_ids=v['mapped_skill_ids'],mapping_status='MAPPED' if v['mapped_row_ids'] else 'SKILL_HEADER_METADATA' if v['mapped_skill_ids'] else 'SOURCE_REGISTRY_ONLY_NO_UNIQUE_FRAGMENT',
                                 execution_description_id=v['execution_description_id'],
                                 declared_description_record_id=v['answer'].get('description_record_id')) for c in cards if c['cid']==30236 for k,v in c['sources']['baseline_registry'].items()],
             references=[dict(cid=cid,local_status='本地缺8151' if cid==8151 else '仅参考版式，未复制数据',
                              website_status='13001未有匹配链接' if cid==13001 else '待主持/独立R1实际浏览核验') for cid in cids],
             limitations=['No browser visual acceptance claimed by implementer.','No real-device execution or new native research.',
                          'Original numbers can make A while field/description association stays unknown.',
                          'Baseline empty-fragment items stay in the source registry until uniquely located; no arbitrary attachment.',
                          'No new candidate templates; prior keyword candidates are not promoted.'])
    rep['totals']={key:sum(s[key] for s in stats) for key in ('N_all','E','N_num','A','B','C','original_A','partial_A','chain_target_associations','chain_targets_with_rules','chain_new_A_rows','chain_new_value_items_in_rows')}
    rep['totals']['A_rate']=rep['totals']['A']/rep['totals']['N_num'] if rep['totals']['N_num'] else 0
    rep['totals']['evidence_cross']={cls:{e:sum(s['evidence_cross'][cls][e] for s in stats) for e in ('确认','推断','未知')} for cls in ('A','B','C')}
    rep['summary']=metrics(rep['totals']);rep['implementation_status']=INFERENCE_STATUS
    dump(out/'pilot_report.json',rep)
    (out/'pilot_samples.html').write_text(audit_page(samples),encoding='utf-8')
    (out/'pilot_samples.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in samples),encoding='utf-8')
    mapping=[m for c in cards for m in c['sources']['old_to_new']]
    (out/'old_to_new_rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in mapping),encoding='utf-8')
    md=['# 11张角色技能页样本（实施自检）','','用户已确认旧11张；此为R2准备版，待独立R2；未生成全量。','',
        '[逐行抽查表](pilot_samples.html) · [机器可读报告](pilot_report.json) · [old→new映射](old_to_new_rows.jsonl)','',
        '| CID | 旧描述 | 新N_all/E/N_num | A/A率 | B/C | 原文A | A部分填充 | 链目标关联/有规则 |',
        '|---|---:|---|---|---|---:|---:|---|']
    for r in stats:md.append(f"| [{r['cid']}]({r['cid']}/index.html) | {r['old_descriptions']} | {r['N_all']}/{r['E']}/{r['N_num']} | {r['A']} / {r['A_rate']:.1%} | {r['B']}/{r['C']} | {r['original_A']} | {r['partial_A']} | {r['chain_target_associations']}/{r['chain_targets_with_rules']} |")
    md+=['','四项并列：'+summary_text(rep['summary']),'',INFERENCE_STATUS['message']+'；'+INFERENCE_STATUS['zero_inference_meaning']+'。B0：'+INFERENCE_STATUS['B_zero_reason'],'','| CID | A率 | 整行确认率 | 原文A数/率 | C数/率 |','|---|---|---|---|---|']
    for c in cards:md.append('| '+str(c['cid'])+' | '+' | '.join(str(c['summary'][k]['count'])+'/'+str(c['summary'][k]['denominator'])+f" ({c['summary'][k]['rate']:.1%})" for k in ('A','whole_row_confirmed','original_A','C'))+' |')
    baseline_rows=sum(bool(b['mapped_row_ids']) for b in rep['baseline_30236']);baseline_headers=sum(bool(b['mapped_skill_ids']) for b in rep['baseline_30236'])
    md+=['','原文A清单先于链复用建立，原文数字注明效果量/阈值/次数等身份；ID与1st编号不算量。E=0。B不靠翻译或复述凑数。链上字段规则在具体归属未证时只留在对应技能来源层，本次链新增A和新增行内数值均0。','',
         '旧基线10卡63/322=19.6%、11卡79/384=20.6%为确认＋提示，不能直接与新A率称为同口径提升。新旧分母差异以逐引用原文和old→new映射审计。',
         '', (f'30236的101项既有答案完整保留于card.json的baseline_registry；{baseline_rows}项映射实际描述行，{baseline_headers}项映射技能头部的条件档位/配置，不新增描述行。沙漠pattern43023600无独立sinfo，不能捏造正文；按原condition及实际子记录链显示沙漠值，保留原declared description ID。自身/全体Class依据原target及65000001/65000002实际引用分开。旧基线文件未修改。' if rep['baseline_30236'] else '本次子集未包含30236，未生成其101项基线映射。'),
         '', f"分母修正：Leader.sympathy_text补{sum(s['leader_sympathy_rows_added'] for s in stats)}行；保留原表确实重复的{sum(s['repeated_actual_occurrences_retained'] for s in stats)}次句子出现；排除{sum(s['internal_labels_excluded'] for s in stats)}条SA内部标签但保留配置与来源（非E）。总N_all由旧{sum(s['old_descriptions'] for s in stats)}变为{rep['totals']['N_all']}。逐项见JSON denominator_changes及old→new映射。",
         '', '参考版式仅用卡头、基础表、技能分组与折叠来源结构。网站状态由主持/独立R1实际浏览核验；本地8151缺卡、13001无匹配链接，不强配。空组只说明“本输入快照未见配置／未关联”。',
         '', f'生成与必要结构自检耗时：{elapsed:.2f}秒；不是全量生成/逐卡审查吞吐估计。所有页面13组，JSON/HTML行、原文及嵌入数据一致。未声称实施浏览器视觉验收。','',
         '运行：`& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/card_page_r2_prep.py --input-root . --output output/character_skills/r2_preparation`。可用 `--cid` 选择上述11张的子集，其他cid拒绝。输入根须含声明的现有解包、profiles/links/rules与规则证据产物；不依赖参考目录。','',
         '## 抽样行','']
    for r in samples:
        values='；'.join(a['value'] for a in r['answers']) or '未知'
        md+=['- ['+str(r['cid'])+' / '+r['group']+' / '+r['stage']+']('+str(r['cid'])+'/index.html#'+r['row_id']+') — '+r['row_class']+'；数值'+r['numeric_evidence']+'／关联'+r['association_evidence'],
             '  - 日文：'+r['japanese'].replace('\n',' '),'  - 值／机制：'+values.replace('\n',' '),
             '  - 原因：'+'；'.join(r['unknown_reasons'])]
    (out/'pilot_report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    return rep


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-root',type=Path,default=HERE.parents[1])
    parser.add_argument('--output',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--pilot',action='store_true');mode.add_argument('--cid',type=int,nargs='+')
    args=parser.parse_args();cids=SAMPLES if args.pilot else tuple(dict.fromkeys(args.cid))
    if not set(cids)<=set(SAMPLES):parser.error('Only the authorized eleven pilot cids are supported')
    root=args.input_root.resolve();out=args.output.resolve();start=time.perf_counter()
    data=Inputs(root,cids);cards=[];checks=[]
    for cid in cids:
        card=build_card(data,cid);html=page(card);checks.append(validate(card,html));cards.append(card)
        dump(out/str(cid)/'card.json',card);(out/str(cid)/'index.html').write_text(html,encoding='utf-8')
    assert original_numbers('HPが50%以上の時、攻撃力が上がる')[0]['role']=='HP条件阈值'
    assert not original_numbers('1stChain以上を達成した時')
    assert original_numbers('HPが1000上がる')[0]['value']=='1000'
    rep=report(cards,checks,time.perf_counter()-start,out)
    print(json.dumps(dict(cids=cids,stats=rep['statistics'],generation_seconds=rep['generation_seconds']),ensure_ascii=True))


if __name__=='__main__':main()
