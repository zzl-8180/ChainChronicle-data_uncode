"""Read-only audit of the 20261023 collaborator bundle. Standard library only.

Writes a fresh reference-analysis report version.
No imported collaborator module is executed; focused functions are AST-extracted.
"""
import ast
import argparse
import csv
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from project_layout_paths import read_path
from versioned_outputs import fresh_output
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
NEW = read_path(ROOT / '其他人的参考/claude_cc_site_pages 20261023', root=ROOT)
OLD = read_path(ROOT / '其他人的参考/claude_cc_site_pages', root=ROOT)
OUT = None
CACHE = read_path(ROOT / 'output/cache_full_20261015_v3/decoded', root=ROOT)
APK = read_path(ROOT / 'output/base_master', root=ROOT)
USABLE = {'解包确认', '用户确认', '统计推断', '参考推断'}


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def csvout(name, rows):
    if not rows:
        return
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in r.items()})


def walk(obj, path=''):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk(v, path + '/' + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, path + '/' + str(i))


def extracted(path, names, env):
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    nodes = []
    for n in tree.body:
        name = n.name if isinstance(n, ast.FunctionDef) else (
            n.targets[0].id if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) else None)
        if name in names:
            nodes.append(n)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)


def main():
    rules_path = read_path(ROOT / 'output/character_skills/profiles/rules.json', root=ROOT)
    rules_hash = sha(rules_path)
    rules = read(rules_path)
    metrics_path = read_path(ROOT / 'output/character_skills/effect_ledger/metrics.json', root=ROOT)
    metrics_hash = sha(metrics_path)
    inventory = []
    for p in NEW.rglob('*'):
        if p.is_file():
            inventory.append({'path': p.relative_to(NEW).as_posix(), 'bytes': p.stat().st_size})
    csvout('file_inventory.csv', inventory)
    old_rows = { (r['table'], r['type'], r['slot']): r for r in read(OLD/'param_table.json')['rows'] }
    new_data = read(NEW/'param_table.json')
    joined = []
    for r in new_data['rows']:
        key = (r['table'], r['type'], r['slot'])
        field = '/' + ('skill'+r['slot'] if r['table'] == 'bossskill' else r['slot'])
        rk = f"{r['table']}|{r['type']}|{field}"
        ours = rules.get(rk)
        before = old_rows.get(key)
        changed = [k for k in r if before is None or r[k] != before.get(k)]
        joined.append({**r, 'delta': 'added' if before is None else 'changed' if changed else 'unchanged',
                       'changed_fields': changed, 'old_label': before.get('label') if before else None,
                       'old_conversion': before.get('conversion') if before else None,
                       'old_status': before.get('status') if before else None,
                       'our_rule_key': rk if ours else None,
                       'our_meaning': ours.get('meaning_zh') if ours else None,
                       'our_conversion': ours.get('conversion') if ours else None,
                       'our_status': ours.get('status') if ours else None,
                       'our_limits': ours.get('limits') if ours else None,
                       'our_evidence': ours.get('evidence') if ours else None})
    csvout('param_table_crosscheck.csv', joined)
    save('param_table_delta.json', [r for r in joined if r['delta'] != 'unchanged'])
    cache_skill = read(CACHE/'skilllist.data5.json.raw')['skilllist']
    apk_skill = read(APK/'_mdSkill.json')['skilllist']
    cache_boss = read(CACHE/'bossinfo.data5.json.raw')['bossinfo']
    apk_boss = read(APK/'_mdBossInfo.json')
    tables = {}
    for layer, sk, bs in [('CACHE', cache_skill, cache_boss), ('APK', apk_skill, apk_boss)]:
        tables[layer, 'skilllist'] = {r['skillid']: r for r in sk}
        tables[layer, 'bossskill'] = {r['skillid']: r for r in bs['bossskill']}
        tables[layer, 'bosspattern'] = {r['patternid']: r for r in bs['bosspattern']}
    cards, card_paths = {}, {}
    occurrences = defaultdict(list)
    source_checks, mismatch = Counter(), []
    unique_records = set()
    pattern_omissions = []
    for p in sorted((NEW/'cards').glob('*/data/card.json')):
        c = read(p); cid = c['cid']; cards[cid] = c; card_paths[cid] = p
        for pointer, obj in walk(c):
            if 'raw' not in obj or 'skillid' not in obj or 'type' not in obj or not isinstance(obj['raw'], dict):
                continue
            raw = obj['raw']; table = 'bossskill' if 'skillid0' in raw else 'skilllist'
            layer = obj.get('source'); sid = obj['skillid']
            occurrences[table, obj['type']].append({'cid': cid, 'yg': 'Y.G.' in c['jp_name'],
                'source': layer, 'skillid': sid, 'pointer': pointer, 'raw': raw})
            unique_records.add((layer, table, sid))
            src = tables.get((layer, table), {}).get(sid)
            if src is None:
                source_checks['missing_source'] += 1
                mismatch.append({'cid':cid, 'pointer':pointer, 'reason':'missing source', 'layer':layer, 'table':table, 'id':sid})
                continue
            differences = {k:{'bundle':v,'source':src.get(k),'present':k in src} for k,v in raw.items() if k not in src or src[k] != v}
            source_checks['different' if differences else 'equal_present_fields'] += 1
            if differences:
                mismatch.append({'cid':cid,'pointer':pointer,'layer':layer,'table':table,'id':sid,'differences':differences})
        for pointer,obj in walk(c):
            if 'patternid' not in obj or 'slots' not in obj:
                continue
            src=tables.get((obj.get('source'),'bosspattern'),{}).get(obj['patternid'])
            if src and any(k in src for k in ['hpstart','hpend']):
                pattern_omissions.append({'cid':cid,'pointer':pointer,'patternid':obj['patternid'],
                    'source':obj.get('source'),'hpstart':src.get('hpstart'),'hpend':src.get('hpend'),
                    'bundle_has_hp_fields':any(k in obj for k in ['hpstart','hpend'])})
    save('source_mismatches.json', mismatch)
    csvout('pattern_hp_fields.csv', pattern_omissions)
    candidates=[]
    for r in joined:
        if r['status'] not in USABLE:
            continue
        occ=occurrences.get((r['table'],r['type']),[])
        cids=sorted({o['cid'] for o in occ}); yg=sorted({o['cid'] for o in occ if o['yg']})
        raw_slot=('skill'+r['slot']) if r['table']=='bossskill' else r['slot']
        present=[o for o in occ if isinstance(o['raw'].get(raw_slot),(int,float)) and o['raw'][raw_slot]!=0]
        nonzero_cids=sorted({o['cid'] for o in present}); nonzero_yg=sorted({o['cid'] for o in present if o['yg']})
        candidates.append({'table':r['table'],'type':r['type'],'slot':r['slot'],'label':r['label'],
            'conversion':r['conversion'],'status':r['status'],'hits':r['hits'],'decisive_hits':r['decisive_hits'],
            'existing_rule_key':r['our_rule_key'],'changed_since_old':r['delta']!='unchanged',
            'cards_referencing_type':len(cids),'yg_cards_referencing_type':len(yg),'yg_cids':yg,
            'cards_with_nonzero_slot':len(nonzero_cids),'yg_cards_with_nonzero_slot':len(nonzero_yg),
            'yg_nonzero_cids':nonzero_yg,
            'sample_cids':cids[:12], 'note':'引用类型覆盖，未证明本字段非零、适用于对应句或能新增答案；charainfo未在嵌套raw统计中'})
    candidates.sort(key=lambda r:(bool(r['existing_rule_key']),-r['yg_cards_referencing_type'],-r['decisive_hits']))
    csvout('candidate_rules.csv',candidates)
    focus=[]
    for key in [('skilllist',1009),('skilllist',1051),('skilllist',1074),('skilllist',48),('skilllist',23),('skilllist',58),('skilllist',2012),('bossskill',116),('skilllist',9),('skilllist',1104),('skilllist',1014),('skilllist',1091),('skilllist',2018)]:
        occ=occurrences[key]; cids=sorted({o['cid'] for o in occ}); yg=sorted({o['cid'] for o in occ if o['yg']})
        unique={ (o['source'],o['skillid']):o for o in occ }
        focus.append({'table':key[0],'type':key[1],'cards':len(cids),'yg_cards':len(yg),'cids':cids,'yg_cids':yg,
            'unique_source_records':len(unique),'samples':list(unique.values())[:8]})
    save('focus_candidates.json',focus)
    # Focused regression probes execute only extracted pure functions, never build/render mains.
    env={'re':re,'math':math,'unicodedata':unicodedata}
    extracted(NEW/'scripts/infer_params.py',{'TRANSFORMS'},env)
    extracted(NEW/'scripts/render_pages.py',{'explainable'},env)
    env['rp']=SimpleNamespace(explainable=env['explainable'],_fmt=lambda x:f'{x:g}')
    extracted(NEW/'scripts/unpack_text.py',{'NUM','LABEL','NAMED','STAT_WORDS','jp_numbers','backed','scrub','fill_unknowns'},env)
    probe=[]
    def test(name, inp, result, note):
        probe.append({'name':name,'input':inp,'actual_output':result,'interpretation':note})
    test('unrelated_number_survives','攻击力（30%）增加；只有30秒原值',
         env['scrub']('攻击力（30%）增加',[],[30],''),'原值30秒可为错误的30%背书；仅数相等，无字段/单位约束')
    test('interval_floor','基础1.5，倍率0.7，待核1.05秒',
         env['scrub']('攻击间隔（→1.0秒）',[],[0.7],'',interval=1.5),'输出1.0不是1.05；0.1秒截断是展示政策，未证明运行时')
    vals=[SimpleNamespace(label='攻击力',unit='%',value=20,where='',gid=('skilllist',1)),
          SimpleNamespace(label='攻击力',unit='%',value=20,where='',gid=('skilllist',2))]
    test('equal_values_competing_records','攻击力（？%）增加；两个不同记录都是20%',
         env['fill_unknowns']('攻击力（？%）增加',vals),'按值元组合并两个载体，数值唯一不等于来源唯一')
    test('whole_card_fallback','本栏无载体；别栏唯一20%',
         env['fill_unknowns']('攻击力（？%）增加',[],vals[:1]),'跨栏回退可填20%；正式绑定需真实引用和条件')
    save('focused_probes.json',probe)
    page_samples=[]
    for cid,terms in [(10210,['防御力','HP〉']), (2320,['防御力']), (7235,['1.5%']), (1296,['0.05秒']), (10001,['暴击率'])]:
        p=card_paths[cid].parent.parent/'unpack.html'
        t=html.unescape(re.sub('<[^>]+>',' ',p.read_text(encoding='utf-8')))
        t=re.sub(r'\s+',' ',t)
        page_samples.append({'cid':cid,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),
            'snippets':{term:[t[max(0,m.start()-60):m.start()+240] for m in list(re.finditer(re.escape(term),t))[:3]] for term in terms}})
    save('page_samples.json',page_samples)
    # Locate current unresolved descriptions for focused leads; these are keyword candidates, not proven bindings.
    focus_keywords={'116':r'一定間隔|ランダム', '1009':r'マナスロット', '1051':r'回復行動',
                    '48':r'反射', '58':r'致死|致命|HPが0|ＨＰが０|耐え', '2012':r'攻撃間隔|攻撃速度'}
    focus_by_type={str(x['type']):set(x['cids']) for x in focus}
    gap_rows=[]
    with read_path(ROOT/'output/character_skills/effect_ledger/ledger.jsonl', root=ROOT).open(encoding='utf-8') as f:
        for line in f:
            row=json.loads(line)
            if row.get('record_type')!='description' or row.get('ledger_row_status')=='完整':
                continue
            for typ,pattern in focus_keywords.items():
                if row['cid'] in focus_by_type[typ] and re.search(pattern,row.get('japanese','')):
                    gap_rows.append({'candidate_type':typ,'cid':row['cid'],'yg':row.get('yg'),
                        'row_id':row['row_id'],'status':row['ledger_row_status'],'japanese':row['japanese'],
                        'namespace':row['namespace'],'note':'卡引用该类型且正文关键词命中；未证明本句与该载体的绑定'})
    csvout('focused_gap_rows.csv',gap_rows)
    script_delta=[]
    for p in sorted((NEW/'scripts').glob('*.py')):
        old=OLD/'scripts'/p.name
        script_delta.append({'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size,
                             'old_exists':old.exists(),'same_as_old':old.exists() and sha(old)==sha(p)})
    save('script_manifest.json',script_delta)
    newkeys={(r['table'],r['type'],r['slot']) for r in new_data['rows']}
    ours_cids={int(p.name) for p in read_path(ROOT/'output/character_skills/pages', root=ROOT).iterdir() if p.is_dir() and p.name.isdigit()}
    summary={'date':'2026-10-23','bundle':str(NEW.relative_to(ROOT)),
        'files':len(inventory),'bytes':sum(x['bytes'] for x in inventory),
        'extensions':dict(Counter(Path(x['path']).suffix for x in inventory)),
        'cards':len(cards),'sources':dict(Counter(c['source'] for c in cards.values())),
        'section_presence':{k:sum(bool(c.get(k)) for c in cards.values()) for k in ['denju','heroic','passive','crossworld','leader','job_ability','sympathy','extra']},
        'denju_lb_cards':sum(bool((c.get('denju') or {}).get('limit_break')) for c in cards.values()),
        'translations':sorted(p.name for p in (NEW/'translations').glob('*.json')),
        'paired_cards':new_data['paired_cards'],'param_rows':len(joined),
        'status_counts':dict(Counter(r['status'] for r in joined)),
        'delta_counts':dict(Counter(r['delta'] for r in joined)),
        'removed_param_keys':sorted(set(old_rows)-newkeys),
        'semantic_changed_existing':sum(r['delta']=='changed' and any(k in r['changed_fields'] for k in ['status','label','conversion','unit']) for r in joined),
        'usable_rules':len(candidates),'usable_with_our_exact_key':sum(bool(r['existing_rule_key']) for r in candidates),
        'usable_without_our_exact_key':sum(not r['existing_rule_key'] for r in candidates),
        'unmapped_usable_by_table':dict(Counter(r['table'] for r in candidates if not r['existing_rule_key'])),
        'new_or_semantic_changed_usable':sum(r['status'] in USABLE and (r['delta']=='added' or any(k in r['changed_fields'] for k in ['status','label','conversion','unit'])) for r in joined),
        'focused_gap_rows':dict(Counter(r['candidate_type'] for r in gap_rows)),
        'focused_gap_rows_yg':dict(Counter(r['candidate_type'] for r in gap_rows if r['yg'])),
        'hit_rate_above_1':[{'table':r['table'],'type':r['type'],'slot':r['slot'],'hits':r['hits'],'denominator':r['cards_with_value']} for r in joined if r['hit_rate']>1],
        'source_checks':dict(source_checks),'unique_raw_records':len(unique_records),
        'our_rule_count':len(rules),'our_rules_sha256':rules_hash,'our_metrics_sha256':metrics_hash,
        'our_snapshot':read(metrics_path)['snapshot'],
        'our_inputs_stable':rules_hash==sha(rules_path) and metrics_hash==sha(metrics_path),
        'our_cids_missing_in_bundle':sorted(ours_cids-set(cards)),
        'bundle_cids_not_in_ours':sorted(set(cards)-ours_cids),
        'external_dependencies':{x:(NEW.parent/x).exists() for x in ['site_diff/out/site_parsed.json','CC_full_unpack_results_data_20261016/master_data/decoded','base_master','CC_full_unpack_results_images_20261016/full_unpack/objects']}}
    save('summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def late_replay():
    """Replay inference from packaged JSON inputs in a separate tree; no network/rendering."""
    dest=ROOT/'work/reference_analysis_20261023'/OUT.name/'statistical_replay'
    if dest.exists():
        raise FileExistsError('Replay output already exists; preserve it and inspect its report.')
    project=dest/'claude_cc_site_pages'
    project.mkdir(parents=True)
    inputs=[]
    for p in (NEW/'cards').glob('*/data/card.json'):
        inputs.append((p,project/p.relative_to(NEW)))
    inputs += [(NEW/'scripts/infer_params.py', project/'scripts/infer_params.py'),
               (NEW.parent/'site_diff/out/site_parsed.json',dest/'site_diff/out/site_parsed.json')]
    for src,dst in inputs:
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
    result=subprocess.run([sys.executable,'-X','utf8','-B',str(project/'scripts/infer_params.py')],
                          cwd=project,capture_output=True,text=True,encoding='utf-8')
    expected=read(NEW/'param_table.json')
    actual=read(project/'param_table.json') if (project/'param_table.json').exists() else None
    report={'command':'python -X utf8 -B scripts/infer_params.py','cwd':str(project.relative_to(ROOT)),
            'input_files':len(inputs),'input_bytes':sum(p.stat().st_size for p,_ in inputs),
            'python':sys.version,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
            'semantic_equal':actual==expected,'byte_equal':(project/'param_table.json').exists() and sha(project/'param_table.json')==sha(NEW/'param_table.json'),
            'scope':'仅统计参数表重建；不代表规则语义正确；未安装新环境、未重建card.json或全站页面'}
    save('isolated_replay.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


def late_extras():
    outer=NEW.parent
    files=[p for p in outer.rglob('*') if p.is_file()]
    cards=[]; unions=[]; raw_new=set(); raw_old=set()
    for p in sorted((NEW/'cards').glob('*/data/card.json')):
        a=read(p); old=OLD/p.relative_to(NEW); b=read(old)
        for obj,seen in [(a,raw_new),(b,raw_old)]:
            for ptr,o in walk(obj):
                if isinstance(o.get('raw'),dict) and 'skillid' in o and 'type' in o:
                    seen.add((o.get('source'),'bossskill' if 'skillid0' in o['raw'] else 'skilllist',o['skillid']))
        ac=json.loads(json.dumps(a)); bc=json.loads(json.dumps(b))
        for obj in [ac,bc]:
            obj['basic'].pop('buddy_id',None);obj['basic'].pop('buddy_of',None)
            for _,o in walk(obj):
                o.pop('union',None)
        cards.append({'cid':a['cid'],'byte_same':p.read_bytes()==old.read_bytes(),
            'same_after_removing_buddy_union':ac==bc,'buddy_id':a['basic'].get('buddy_id'),'buddy_of':a['basic'].get('buddy_of')})
        for ptr,o in walk(a):
            if o.get('union'):
                u=o['union'];unions.append({'cid':a['cid'],'pointer':ptr,'parent_pattern':o.get('patternid'),
                    'sa':u.get('sa'),'granted_pattern':u['pattern']['patternid'],'seconds':u.get('seconds')})
    csvout('card_delta.csv',cards);csvout('union_links.csv',unions)
    support=[]
    for p in (outer/'CC_full_unpack_results_data_20261016/master_data/decoded').glob('*'):
        q=CACHE/p.name
        support.append({'name':p.name,'sha256':sha(p),'same_as_our_cache':q.exists() and p.read_bytes()==q.read_bytes()})
    env={'rules':lambda:{},'ENEMY_TYPES':(99,2003),'CONV':{},
         'Value':lambda *a:{'label':a[0],'value':a[1],'status':a[3],'field':a[6]}}
    extracted(NEW/'scripts/numbers.py',{'_emit'},env)
    values=[]
    env['_emit']('bossskill',27,{'skillflag0_1':264},'skillparam',-1,'synthetic',values)
    env2={'re':re}
    extracted(NEW/'scripts/unpack_theme.py',{'_hover'},env2)
    probes=[{'name':'overheal_bit35_vs_bit40','synthetic':True,'input_high_flags':264,
        'actual_output':values,'expected_overcap_percent':30,
        'evidence':'output/boss_heal/constants.json bits=[40,35,41,42,43,44], reverse selection; no live-game test this turn'},
        {'name':'hover_does_not_filter_effect_label','synthetic':True,'context':'防御力（20%），候选仅攻击力20%',
         'actual_output':env2['_hover']('20%',{(20,'%'):['攻击力20% ← attack parameter']}),
         'interpretation':'仅数字与单位匹配，未把前文防御标签传入；提示不是唯一语义绑定'}]
    save('late_focused_probes.json',probes)
    report={'outer_files':len(files),'outer_bytes':sum(p.stat().st_size for p in files),
        'card_count':len(cards),'cards_byte_same':sum(c['byte_same'] for c in cards),
        'cards_same_except_buddy_union':sum(c['same_after_removing_buddy_union'] for c in cards),
        'buddy_mains':sum(bool(c['buddy_id']) for c in cards),'buddy_children':sum(bool(c['buddy_of']) for c in cards),
        'union_links':len(unions),'union_cards':len({u['cid'] for u in unions}),
        'new_raw_record_keys':sorted(raw_new-raw_old),'removed_raw_record_keys':sorted(raw_old-raw_new),
        'support_tables':support,
        'site_inputs':[{ 'path':p.relative_to(outer).as_posix(),'sha256':sha(p),'records':len(read(p)),'bytes':p.stat().st_size}
                       for p in (outer/'site_diff/out').glob('*.json')]}
    save('late_delta_summary.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition',choices=['first','late'],default='first')
    parser.add_argument('--replay',action='store_true')
    parser.add_argument('--extras',action='store_true')
    args=parser.parse_args()
    if args.edition=='late':
        OLD=NEW
        NEW=read_path(ROOT/'其他人的参考/claude_cc_site_pages_给GPT_20261023/claude_cc_site_pages', root=ROOT)
    if (args.extras or args.replay) and args.edition!='late':
        parser.error('--extras and --replay require --edition late')
    OUT=fresh_output('projects/reference-analysis/reports','claude-20261023-'+args.edition)
    if args.extras:
        late_extras()
    elif args.replay:
        late_replay()
    else:
        main()
