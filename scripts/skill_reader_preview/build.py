"""Build a read-only player preview from the current accepted character data.

Run from any directory: python build.py --root PATH [--output PATH].
No downloads, installations, mutations to formal results, or external services.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path
from rerun_output import require_new_files

from presentation import effect_label, answer
from branch_reading import explain, skill_label, condition_context
from wording import description

HERE = Path(__file__).resolve().parent
CIDS = [350, 30239, 30337, 30236, 29, 1]

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def js(path, name, data):
    text = json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    path.write_text(f'window.{name}='+text.replace('</', '<\\/')+';\n', encoding='utf-8')

def rows(card):
    return [r for g in card['groups'] for s in g['skills'] for r in s['rows']]

def legacy_copy(root):
    """Reuse wording only where the original sentence is exactly unchanged."""
    base = read_path(root/'output/character_skills/ui_reading_preview_20261025', root=root)
    result = {}
    for cid in CIDS[:3]:
        copy = read(base/f'_research/copy_{cid}.json')['rows']
        if isinstance(copy, list): copy = {r['row_id']: r for r in copy}
        original = {r['row_id']: r['japanese'] for r in rows(read(base/f'_data/facts_{cid}.json'))}
        for rid, c in copy.items():
            t = c['effect']
            t = re.sub(r'^原文记录了(?:这条|该)(?:效果|说明|条件强化|连锁强化|分支|适用面|规则|本体效果)：', '', t)
            t = re.sub(r'[。；](?:但)?本样稿.*$', '。', t)
            t = re.sub(r'。原文记录了该效果.*$', '。', t)
            t = t.replace('反響範囲', '反响范围').replace('反響', '反响').replace('共鳴', '共鸣')
            t = t.replace('玛那', '法珠').replace('時の楔', '时之楔').replace('减速', '缓速').replace('倒地', '眩晕')
            t = t.replace('暴击发生率', '暴击率').replace('暴击威力', '暴击伤害').replace('必殺', '必杀')
            t = t.replace('首席角色', '首位角色').replace('近接通常攻击', '近战普通攻击')
            jp = original[rid]
            if jp == '止まっていると効果が上がる。':t = '停止不动时，效果进一步提高。'
            if jp == '移動すると元に戻る。':t = '移动后恢复原状。'
            if '这是对' in t:
                t = '停止不动时，效果进一步提高。' if '停止' in jp else '移动后恢复原状。'
            if '1stChain' in jp and '1st' not in t:
                t = re.sub(r'(连携数达到条件后|连锁数达到要求以上)', '达到1st Chain或以上后', t)
            if jp == '攻撃間隔が早くなる。':t = '攻击间隔缩短。'
            if jp == '止まっている時間が長いほど効果が上がる。':t = '停止不动的时间越长，效果越强。'
            result[rid] = {'original': jp, 'textZh': t}
    result.update(read(HERE/'reading_copy_extra.json')['rows'])
    for item in result.values():
        item['textZh']=description(item['original'],item['textZh'])
    return result

def reference_names(root, reference_root=None, source_map_manifest=None):
    if (reference_root is None) != (source_map_manifest is None):
        raise ValueError('Explicit reference root and source map manifest must be supplied together')
    if source_map_manifest is not None:
        from reference_sources_v2 import ReferenceSourceMap
        mapping = ReferenceSourceMap.from_manifest(source_map_manifest, reference_root)
        p, _ = mapping.resolve('index_unpack.html')
    else:
        p = read_path(root/'其他人的参考/CC解包数据_给GPT_20261027/claude_cc_site_pages/index_unpack.html', root=root)
    names = {}
    for attrs, inside in re.findall(r'<a\s+([^>]*class="cc(?: [^"]*)?"[^>]*)>(.*?)</a>', p.read_text(encoding='utf-8'), re.S):
        m, b = re.search(r'data-c="(\d+)"', attrs), re.search(r'<b>(.*?)</b>', inside, re.S)
        if m and b:names[int(m[1])] = unescape(re.sub('<[^>]+>', '', b[1]))
    return names

def require_stage(root, out):
    formal = read_path(root/'output/character_skills', root=root).resolve()
    physical = out.resolve()
    if physical.is_relative_to(formal):
        raise ValueError('Build into a separate Reader stage using --output.')
    if physical != out.absolute():
        raise ValueError('Reader output must be a direct path.')
    stage_parents = (root/'work', root/'projects/reader/site', root/'projects/reader/pilots')
    if physical.is_relative_to(root) and not any(
        physical != parent and physical.is_relative_to(parent) for parent in stage_parents
    ):
        raise ValueError('Use a named Reader stage under work or projects/reader.')
    if any((out/'audit').rglob('stage_seal.json')):
        raise ValueError('Reader stage is sealed. Use a new stage.')


def build(root, out, sample=False, semantic_migration=None, data_only=False,
          reference_root=None, source_map_manifest=None):
    require_stage(root, out)
    if not data_only:
        require_new_files(out/'build_receipt.json', out/'index.html',
                          out/'data/branch_candidates.js', out/'data/branch_conditions.js',
                          out/'data/mana_costs.js', out/'data/branch_assessments.js',
                          out/'audit/branch_candidates_20261107/inventory.json',
                          out/'audit/player_conditions_20261107/parent_sources.json',
                          out/'audit/mana_costs_20261107/inventory.json',
                          out/'audit/trigger_evidence_20261107/branch_invariance_receipt.json',
                          out/'audit/trigger45_evidence_20261107/partial_conditions_receipt.json',
                          out/'audit/selection_order_20261107/selection_receipt.json',
                          out/'audit/confidence/inventory.json', out/'audit/confidence/changes.json')
    base = read_path(root/'output/character_skills', root=root)
    pages = base/'pages'
    metrics_path = base/'effect_ledger/metrics.json'
    metric_bytes = metrics_path.read_bytes()
    metrics = json.loads(metric_bytes)
    campaign = read(pages/read(pages/'_batch/campaign_latest.json')['report'])
    snapshot = metrics['snapshot']
    if campaign['signature'] != snapshot['campaign_signature']:
        raise ValueError('正式页面与效果账本版本不同，请先由主线完成同步')
    if sha256((base/'profiles/rules.json').read_bytes()).hexdigest()[:16] != snapshot['rules_json_sha256_16']:
        raise ValueError('当前规则与效果账本版本不同，停止生成')
    if sample:
        copy = legacy_copy(root)
        translator = None
    else:
        from translation_bridge import Translator
        translator = Translator(root)
        if translator.semantic:
            reviewed_hashes = translator.semantic['sourceHashes']
            if semantic_migration:
                from migrate_c19 import validate_receipt
                migration = validate_receipt(root, semantic_migration, translator.semantic)
                reviewed_hashes = migration['sourceHashes']
            for cid,digest in reviewed_hashes.items():
                if sha256((pages/cid/'card.json').read_bytes()).hexdigest()!=digest:
                    raise ValueError('主线原文在语义复核后已变化：'+cid)
        copy = {}
    names = reference_names(root, reference_root, source_map_manifest)
    descriptions, effects = {}, defaultdict(list)
    stats = defaultdict(lambda: {'descriptions': Counter(), 'effects': Counter()})
    row_count, effect_count = Counter(), Counter()
    with (base/'effect_ledger/ledger.jsonl').open(encoding='utf-8') as f:
        for line in f:
            e = json.loads(line)
            entry_snapshot = e.get('snapshot_id') or e.get('input_snapshot', {}).get('snapshot_id')
            if entry_snapshot != snapshot['snapshot_id']:raise ValueError('账本混入其他版本')
            cid = e['cid']
            if e['record_type'] == 'description':
                stats[cid]['descriptions'][e['ledger_row_status']] += 1
                row_count[e['ledger_row_status']] += 1
                if not sample or cid in CIDS:
                    descriptions[e['row_id']] = {'japanese':e['japanese'],'ledger_row_status':e['ledger_row_status']}
            else:
                stats[cid]['effects'][e['status']] += 1
                effect_count[e['status']] += 1
                if not sample or cid in CIDS:effects[e['description_ref']].append(e)
    if dict(row_count) != metrics['descriptions']['by_ledger_status']:
        raise ValueError('描述统计不一致')
    for key, count in effect_count.items():
        if count != metrics['effects']['by_status'][key]['all']:raise ValueError('效果统计不一致')
    cards, details, hashes = [], {}, {}
    jobs = {'戦士':'战士','騎士':'骑士','魔法使い':'法师','弓使い':'弓手','僧侶':'僧侣'}
    homes = dict(zip(
        ['薄命の大陸','骸の世界','幻霊','幻獣の世界','精霊島','九領','迷宮山脈','謀略の世界','奈落の世界','年代記の大陸','潜艦の世界','神仙の世界','聖都','賢者の塔','義勇軍','幽夜の世界','遊戯の世界','鉄煙の大陸','罪の大陸','ｉｆの世界','ケ者の大陸','レムレス島'],
        ['薄命大陆','骸之世界','幻灵','幻兽世界','精灵岛','九领','迷宫山脉','谋略世界','奈落世界','年代记大陆','潜艇世界','神仙世界','圣都','贤者之塔','义勇军','幽夜世界','游戏世界','铁烟大陆','罪之大陆','if世界','兽者之里','雷姆雷斯岛']))
    group_names = {'leader':'队长能力','class':'职业能力','extra':'额外能力','sympathy':'共鸣能力','sa':'特殊能力','passive':'被动能力','heroic':'英雄技','crossworld':'跨世界能力'}
    total_rows = 0
    answer_indices = 0
    for cid in sorted(stats):
        path = pages/str(cid)/'card.json'
        data = path.read_bytes()
        card = json.loads(data)
        f = {v['key']: v.get('display_value') for v in card['basic']['fields']}
        current_rows = rows(card)
        total_rows += len(current_rows)
        d, e = stats[cid]['descriptions'], stats[cid]['effects']
        full = set(d) == {'完整'}
        label = '全部描述完整' if full else ('已有部分答案' if e['has_answer'] else '暂无效果答案')
        zh = names.get(cid, '')
        title_zh, _, name_zh = zh.rpartition(' ')
        cards.append({'cid':cid,'name':f.get('name',''),'title':f.get('title',''),
                      'nameZh':name_zh or zh or f.get('name',''), 'titleZh':title_zh,
                      'job':jobs.get(f.get('jobtype'), '职业待核对' if '外部' in str(f.get('jobtype')) else f.get('jobtype','')),
                      'home':homes.get(f.get('home'), f.get('home','')),
                      'rarity':f.get('rarity'),'yg':'Y.G.' in str(f.get('title','')),
                      'icon':(f'assets/icons/{cid}.png' if sample else f'../pages/art/{cid}/icon.png') if (pages/f'art/{cid}/icon.png').exists() else '',
                      'prototype':not sample or cid in CIDS,'hasDetail':not sample or cid in CIDS,'status':label,
                      'counts':{'answer':e['has_answer'],'unresolved':e['unresolved'],'complete':d['完整'],
                                'partial':d['部分'],'unparsed':d['未解析'],'review':d['拆分待核查'],
                                'descriptions':sum(d.values())}})
        if sample and cid not in CIDS:continue
        hashes[str(cid)] = sha256(data).hexdigest()
        if translator:
            for r in current_rows:
                translated=translator.translate(r['japanese'])
                copy[r['row_id']]={'original':r['japanese'],**translated}
                translator.record(r,translated)
        groups = []
        for g in card['groups']:
            skills = []
            for s in g['skills']:
                result_rows = []
                for r in s['rows']:
                    rid = r['row_id']
                    cr = copy.get(rid)
                    if not cr or cr['original'] != r['japanese']:
                        raise ValueError(f'中文稿缺失或原句已变化：{rid}')
                    desc = descriptions[rid]
                    if desc['japanese'] != r['japanese']:raise ValueError(f'描述与账本不一致：{rid}')
                    used, result_effects = set(), []
                    for effect in effects[rid]:
                        answers = []
                        for ref in effect.get('answer_refs', []):
                            idx = ref['answer_index']
                            a = r['answers'][idx]
                            for key in ('field_path', 'raw_value', 'rule_key'):
                                if a.get(key) != ref.get(key):raise ValueError(f'答案引用失配：{rid}/{idx}')
                            view = explain(answer(a, cid=cid, original=r['japanese']), a, r, s, copy)
                            view['source'].update({'rowId':rid, 'answerIndex':idx, 'effectId':effect['effect_id']})
                            answers.append(view)
                            used.add(idx)
                            answer_indices += 1
                        label = effect_label(effect, r['japanese'])
                        pending = '数值尚未解出'
                        if label=='解除异常状态':
                            pending = '效果已见于描述，机制细节待确认'
                        if label in ('附加效果','特殊效果','暴击攻击方式'):
                            pending = '具体效果仍待确认'
                        result_effects.append({'id':effect['effect_id'], 'label':label,
                                               'status':effect['status'],'answers':answers,'pendingText':pending})
                    unbound = []
                    for i, a in enumerate(r['answers']):
                        if i not in used:
                            view = explain(answer(a, cid=cid, original=r['japanese']), a, r, s, copy)
                            view['note'] = '这项数值已记录，与具体效果的对应仍需核对。' + view['note']
                            view['source'].update({'rowId':rid,'answerIndex':i})
                            unbound.append(view)
                    result_rows.append({'id':rid,'textZh':cr['textZh'],'original':r['japanese'],
                                        'translationStatus':cr.get('translationStatus','reviewed'),
                                        'translationSource':cr.get('translationSource','six-card reviewed copy'),
                                        'translationNote':cr.get('translationNote',''),
                                        'semanticReview':cr.get('semanticReview'),
                                        'review':desc['ledger_row_status']=='拆分待核查',
                                        'reviewMessage':'这段描述的效果与数值对应仍需核对；下面已列出的答案可单独查看。',
                                        'effects':result_effects,'unboundAnswers':unbound})
                if result_rows:
                    stage = s.get('stage') or ''
                    if g['group']=='special_move' and re.fullmatch(r'档位 \d+', stage):
                        stage = skill_label(s)
                    if s.get('reference_field')=='skilltext':stage = '角色资料中的必杀说明'
                    stage = re.sub(r'（原字段.*?）', '', stage).replace('Leader','队长').replace('Lv MAX','最高等级').replace('Lv ','等级 ')
                    if g['group'] not in ('special_move','extra') and re.fullmatch(r'档位 \d+',stage):stage=''
                    label = group_names.get(g['group'],g['label'])
                    name = s.get('name') or label
                    if name in ('Leader','Class','Extra') or name.startswith('■') or 'ability' in name.lower():name=label
                    skills.append({'name':name,'stage':stage,'sourceKind':'character_profile' if s.get('reference_field')=='skilltext' else 'skill_record','rows':result_rows, **condition_context(s)})
            if skills:groups.append({'id':g['group'],'label':group_names.get(g['group'],g['label']),'skills':skills})
        details[str(cid)] = {'cid':cid,'art':(f'assets/cards/{cid}.png' if sample else f'../pages/art/{cid}/card.png') if (pages/f'art/{cid}/card.png').exists() else '',
                             'groups':groups}
    if total_rows != sum(row_count.values()):raise ValueError('全库描述数量已变化，停止生成')
    # Check anchors again before writing a coherent preview snapshot.
    if metrics_path.read_bytes()!=metric_bytes:raise ValueError('读取期间主线已更新，请重新生成')
    for cid,h in hashes.items():
        if sha256((pages/cid/'card.json').read_bytes()).hexdigest()!=h:raise ValueError('读取期间角色数据变化')
    summary={'cards':len(cards),'withAnswer':sum(c['counts']['answer']>0 for c in cards),
             'noAnswer':sum(c['counts']['answer']==0 for c in cards),'complete':sum(c['status']=='全部描述完整' for c in cards)}
    catalog={'meta':{'snapshot':snapshot['snapshot_id'],'updated':metrics['generated_at'],
                      'prototypeIds':CIDS if sample else [],'detailMode':'bundled' if sample else 'per-card',
                      'buildVersion':datetime.now(timezone.utc).isoformat(),
                      'nameSource':'中文别名参考协作者20261027；数值及状态来自当前主线'},
             'summary':summary,'cards':cards}
    if semantic_migration:
        catalog['meta']['acceptedCycle'] = migration['acceptedCycle']
    if translator:
        counts=Counter(row['translationStatus'] for row in translator.audit)
        catalog['meta']['translations']={'readable':counts['reviewed']+counts['template'],'pending':counts['pending'],
                                        'note':('全部描述已逐句对照原文复核；数值可信度另行标色' if translator.semantic else '中文整理稿经过原文数字与关键语义检查，不等于全部人工复核')}
    out.mkdir(parents=True,exist_ok=True)
    for d in (['data','assets/icons','assets/cards'] if sample else ['data/cards','audit']):(out/d).mkdir(parents=True,exist_ok=True)
    for p in (HERE/'web').iterdir():
        if p.is_file():shutil.copy2(p,out/p.name)
    shutil.copy2(HERE/'README.md',out/'README.md')
    icon_bytes = 0
    for c in (cards if sample else []):
        if c['icon']:
            p=pages/f'art/{c["cid"]}/icon.png';icon_bytes+=p.stat().st_size
            dest=out/c['icon']
            if not dest.exists() or dest.stat().st_size!=p.stat().st_size:shutil.copy2(p,dest)
    for cid in (CIDS if sample else []):
        p=pages/f'art/{cid}/card.png'
        if p.exists():shutil.copy2(p,out/f'assets/cards/{cid}.png')
    js(out/'data/catalog.js','CC_CATALOG',catalog)
    if sample:js(out/'data/cards.js','CC_DETAILS',details)
    else:
        for cid,detail in details.items():
            text=json.dumps(detail,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('</','<\\/')
            (out/f'data/cards/{cid}.js').write_text(f'window.CC_DETAILS=window.CC_DETAILS||{{}};window.CC_DETAILS[{json.dumps(cid)}]={text};\n',encoding='utf-8')
    translation_summary=translator.write_audit(out/'audit') if translator else {'scope':'six reviewed prototype cards'}
    receipt={'snapshot':snapshot,'sourceHashes':hashes,'summary':summary,'descriptions':dict(row_count),
             'effects':dict(effect_count),'detailRows':sum(len(rows(detail)) for detail in details.values()),
             'detailCards':list(map(int,details)),'resolvedAnswerReferences':answer_indices,'iconBytes':icon_bytes,
             'translations':translation_summary,
             'builtAt':datetime.now(timezone.utc).isoformat(),'validation':'PASSED_DATA_ALIGNMENT'}
    receipt['adapterHashes']={p.name:sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.suffix in ('.py','.json')}
    if semantic_migration:
        migration_dest = out/'audit/c19_closeout_20261107/semantic_migration.json'
        migration_dest.parent.mkdir(parents=True,exist_ok=True)
        if semantic_migration.resolve() != migration_dest.resolve():
            shutil.copy2(semantic_migration,migration_dest)
        receipt['semanticMigration'] = {'path':str(migration_dest.relative_to(out)),
            'sha256':sha256(migration_dest.read_bytes()).hexdigest(), 'acceptedCycle':migration['acceptedCycle']}
    receipt['sidecarsRegenerated'] = not data_only and not sample
    if translator:receipt['referencePairsSHA256']=sha256((base/'reader_full_20261106/audit/reference_pairs.json').read_bytes()).hexdigest()
    dump(out/'build_receipt.json',receipt)
    if data_only:
        print(json.dumps({'snapshot':snapshot['snapshot_id'],'detailCards':len(details),
                          'resolvedAnswerReferences':answer_indices,'sidecarsRegenerated':False},ensure_ascii=False))
        return
    if not sample:
        from branch_candidates import audit as build_branch_candidates
        build_branch_candidates(root, out)
        from branch_conditions import build_conditions
        build_conditions(root, out)
        from mana_costs import build_costs
        build_costs(root, out)
        subprocess.run([sys.executable,str(HERE/'review_branch_invariance.py'),'--output',str(out)],check=True,cwd=root)
        if read_path(root/'output/character_skills/reader_full_20261106/audit/trigger45_evidence_20261107/controller_fields.json', root=root).is_file():
            subprocess.run([sys.executable,str(HERE/'review_partial_conditions.py'),'--output',str(out)],check=True,cwd=root)
        if read_path(root/'output/character_skills/reader_full_20261106/audit/selection_order_20261107/native/native_selection_proof.json', root=root).is_file():
            subprocess.run([sys.executable,str(HERE/'review_selection_order.py'),'--output',str(out)],check=True,cwd=root)
        subprocess.run(['node', str(HERE/'review_confidence.js'), '--output', str(out),
                        '--audit-dir', 'audit/confidence'], check=True, cwd=root)
    else:
        js(out/'data/branch_candidates.js','CC_BRANCH_CANDIDATES',{'cards':{}})
        js(out/'data/branch_conditions.js','CC_BRANCH_CONDITIONS',{'records':{}})
        js(out/'data/mana_costs.js','CC_MANA_COSTS',{'records':{}})
        js(out/'data/branch_assessments.js','CC_BRANCH_ASSESSMENTS',{'records':{}})
    version_assets(out)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('sourceHashes','detailCards')},ensure_ascii=False,indent=2))

def version_assets(out):
    """Avoid mixing cached old modules with a newly copied frontend."""
    html = (HERE/'web/index.html').read_text(encoding='utf-8')
    def version(match):
        name = match.group(2)
        asset = out/name
        if not asset.is_file():
            raise ValueError(f'Missing frontend asset: {name}')
        return f'{match.group(1)}="{name}?v={sha256(asset.read_bytes()).hexdigest()[:12]}"'
    html = re.sub(r'(src|href)="([^"?#]+\.(?:js|css))"', version, html)
    (out/'index.html').write_text(html, encoding='utf-8')

def refresh_frontend(out):
    """Rebuild just the UI against an already reviewed reader data snapshot."""
    receipt = read(out/'build_receipt.json')
    if not (out/'data/catalog.js').is_file():
        raise ValueError('Build the reader data before refreshing its frontend')
    if not (out/'data/branch_candidates.js').is_file():
        raise ValueError('先运行 branch_candidates.py 生成可追溯分支补充层，再刷新前端')
    for name in ('branch_conditions','mana_costs','branch_assessments'):
        if not (out/f'data/{name}.js').is_file():
            command='node scripts/skill_reader_preview/review_confidence.js' if name=='branch_assessments' else f'{name}.py'
            raise ValueError(f'先运行 {command} 生成有来源的展示旁注，再刷新前端')
    assessment = json.loads((out/'data/branch_assessments.js').read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
    for name,digest in assessment.get('inputHashes',{}).items():
        if sha256((out/f'data/{name}.js').read_bytes()).hexdigest()!=digest:
            raise ValueError('条件/候选输入已变，先运行 node scripts/skill_reader_preview/review_confidence.js')
    hashes = {}
    for path in (HERE/'web').iterdir():
        if path.is_file():
            shutil.copy2(path, out/path.name)
            hashes[path.name] = sha256(path.read_bytes()).hexdigest()
    version_assets(out)
    hashes['index.html'] = sha256((out/'index.html').read_bytes()).hexdigest()
    result = {'builtAt':datetime.now(timezone.utc).isoformat(),
              'dataBuiltAt':receipt['builtAt'],'snapshot':receipt['snapshot'],
              'scope':'frontend only; reviewed data and semantic receipts unchanged','webHashes':hashes}
    dump(out/'frontend_receipt.json',result)
    shutil.copy2(HERE/'README.md',out/'README.md')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=HERE.parents[1])
    ap.add_argument('--output',type=Path)
    ap.add_argument('--reference-root',type=Path,help='Explicit isolated reference source root; requires --source-map-manifest')
    ap.add_argument('--source-map-manifest',type=Path,help='Reviewed S5 allowlist; does not activate a global route')
    ap.add_argument('--sample',action='store_true',help='Build the original six-card scope in an explicit output directory')
    ap.add_argument('--frontend-only',action='store_true',help='Refresh web files without reading or regenerating mainline data')
    ap.add_argument('--semantic-migration',type=Path,help='Exact C19 migration receipt; retains whole-card source guard')
    ap.add_argument('--data-only',action='store_true',help='Build base data only; keep existing sidecars and historical evidence audits untouched. Validate sidecars then refresh frontend separately.')
    args=ap.parse_args()
    if (args.reference_root is None) != (args.source_map_manifest is None):
        ap.error('--reference-root and --source-map-manifest must be supplied together')
    if args.frontend_only and args.reference_root is not None:
        ap.error('Reference mapping is unused in --frontend-only mode')
    if args.output is None:
        ap.error('Use --output to select a separate Reader stage.')
    destination=write_path(args.output, root=args.root).absolute()
    if args.frontend_only:
        require_stage(args.root.resolve(), destination)
        refresh_frontend(destination)
    else:
        build(args.root.resolve(),destination,sample=args.sample,semantic_migration=args.semantic_migration,data_only=args.data_only,
              reference_root=args.reference_root,source_map_manifest=args.source_map_manifest)
