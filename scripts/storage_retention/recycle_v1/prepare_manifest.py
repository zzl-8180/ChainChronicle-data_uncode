from pathlib import Path
import json,gzip,csv,hashlib,re,collections,datetime,os,stat
root=Path.cwd();out=root/'output/storage_retention/recycle_g1_20261027';old=root/'output/storage_retention/recycle_plan_20261027';seed=root/'output/storage_retention/cleanup_options_20261026'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
facts=json.loads((old/'plan_facts.json').read_text(encoding='utf-8'));state_path=root/'output/character_skills/pages/_batch/retention/state.json';state=json.loads(state_path.read_text(encoding='utf-8'))
protected_runs=set(facts['minimum_protected_union_runs']);protected_runs|={k for k,v in state['reservations'].items() if v['status']!='RELEASED'}
fixed=[]
for rel in ['work/20261020-pilot1017/compare_fix_full.py','work/b8_review_deepseek/make_review_outputs.py','work/character_skills_b10_rv_fix/compare_fix.py']:
 text=(root/rel).read_text(encoding='utf-8');matches=set(re.findall(r'_batch/(?:ge60|40to59|20to39|remaining)/runs/\d{8}T\d{12}Z-[0-9a-f]{8}',text));protected_runs|=matches;fixed.append({'consumer':rel,'sha256':h(root/rel),'run_paths':sorted(matches),'policy':'保守原路径保留；不依赖离线恢复即可读'})
source_hold=root/'output/storage_retention/recovery_followup_20261024/source_holds.json';holds=set(json.loads(source_hold.read_text(encoding='utf-8'))['paths'])
explicit=['output/character_skills/crit_absorb_20261026/','output/character_skills/review/','output/character_skills/s5_nonterrain_20261026/','output/character_skills/s5_terrain_20261026/','output/character_skills/inference_inventory/','output/character_skills/profiles/','output/character_skills/effect_ledger/','output/character_skills/pages/art/','output/character_skills/pages/_batch/retained_payloads/','output/storage_retention/recycle_plan_20261027/','output/storage_retention/recycle_g1_20261027/','output/storage_retention/vault_g1_20261027/','work/storage_recycle_g1_20261027/','work/protection/','output/share_bundle/20261025-character-tools/isolated 中文 space/','output/base_master/','output/cache_full_20261015_v3/','raw/','.git/','.venv/','tools/','output/full_unpack/']
protection={'schema_version':1,'created_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'protected_runs':sorted(protected_runs),'fixed_consumers':fixed,'exact_source_holds':sorted(holds),'source_holds_file_sha256':h(source_hold),'prefixes':explicit,'semantic_protections':['全部独立审查/方向复核目录及其证据，原路径保留','全部本周期前像previous_pages_compact/previous_baseline/previous_checks/zero_touch，不因RELEASED解除','当前正式pages全保留，A仅严格列明且不在保护集中的历史batch/card.json/index.html','原件/原生证据/选题/A7/R3及pin/恢复材料/元数据全部保护','当前发行所有文件除三个成功ZIP均保护；44隔离输入和整树保护','W整组排除；M整组暂缓','本任务工具/执行记录/保管件永久排除候选'],'live_consumer_audit_complete':False,'live_consumer_audit_note':'已保守排除明确固定消费者；未知消费者由G1恢复契约和主持G2前复核，不能把未搜到当无消费者','observed_sources':[]}
for rel in ['docs/tasks/character-skills-progress.md','docs/tasks/20261026-crit-absorb-batch.md','output/character_skills/pages/_batch/campaign_latest.json','output/character_skills/pages/_batch/retention/state.json','scripts/storage_retention/pins.json']:
 p=root/rel;protection['observed_sources'].append({'path':rel,'sha256':h(p),'bytes':p.stat().st_size})
(out/'protection_manifest_v2.json').write_text(json.dumps(protection,ensure_ascii=False,indent=2),encoding='utf-8')
fields=['path','bytes','sha256','classification','category','consumer','recoverability','protection_reason','hash_basis','observed_bytes','observed_mtime_ns'];counts=collections.defaultdict(lambda:[0,0]);errors=[]
with gzip.open(out/'plan_manifest_v2.csv.gz','xt',encoding='utf-8-sig',newline='') as dest:
 w=csv.DictWriter(dest,fieldnames=fields);w.writeheader()
 with gzip.open(seed/'old_payload_archive_candidates.csv.gz','rt',encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   rel=r['path'];p=root/rel;run=r['run'];classification='ELIGIBLE_A';reason='种子内A载荷，G1仅允许只读保管；G2未批准';observed=None
   if not re.fullmatch(r'output/character_skills/pages/_batch/(?:ge60|40to59|20to39|remaining)/runs/\d{8}T\d{12}Z-[0-9a-f]{8}/transactions/\d+/backup/(?:card\.json|index\.html)',rel):classification='PROTECTED';reason='不符合真实历史run载荷形状；含retained_payloads等保护树'
   if any(rel.startswith(prefix) for prefix in explicit):classification='PROTECTED';reason='命中显式保护前缀'
   if run in protected_runs:classification='PROTECTED';reason='当前/旧完整campaign、095905、周期前像或固定历史消费者保护'
   if rel in holds:classification='PROTECTED';reason='事故恢复source_holds精确输入'
   try:
    st=p.lstat();observed=st
    if not stat.S_ISREG(st.st_mode) or getattr(st,'st_file_attributes',0)&1024 or st.st_nlink!=1:classification='HOLD_SPECIAL';reason='非普通文件/重解析点/多硬链接，不能自动处置'
    elif st.st_size!=int(r['bytes']):classification='HOLD_CHANGED';reason='当前大小与种子不一致'
   except FileNotFoundError:classification='ALREADY_ABSENT';reason='源已不存在，不重复处置'
   except OSError as ex:classification='HOLD_ERROR';reason=str(ex);errors.append({'path':rel,'error':str(ex)})
   row={'path':rel,'bytes':r['bytes'],'sha256':r['sha256'],'classification':classification,'category':'A','consumer':'历史复验消费者；明确固定读者已原位保护，其他候选需先归档和恢复契约/主持复核','recoverability':'G1归档100%读回＋映射＋恢复抽样＋最小消费者验收之前不得G2','protection_reason':reason,'hash_basis':'20261026实读SHA；archive build必须逐源重算后才成为已验证','observed_bytes':observed.st_size if observed else None,'observed_mtime_ns':observed.st_mtime_ns if observed else None}
   w.writerow(row);counts[classification][0]+=1;counts[classification][1]+=int(r['bytes'])
 for name in ['A_tools.zip','B_data_research.zip','C_character_pages_images.zip']:
  rel='output/share_bundle/20261025-character-tools/packages_retry/'+name;p=root/rel;st=p.stat();w.writerow({'path':rel,'bytes':st.st_size,'sha256':h(p),'classification':'P_PENDING_SMALL_CLOSURE','category':'P','consumer':'近期无分享意图；用户允许回收方向，G2尚未批准','recoverability':'旧源码/规则/审查小闭包和隔离树保留；旧ZIP身份将来不保证','protection_reason':'仅3个成功ZIP，不能扩至发行目录','hash_basis':'本轮重新读取SHA','observed_bytes':st.st_size,'observed_mtime_ns':st.st_mtime_ns});counts['P_PENDING_SMALL_CLOSURE'][0]+=1;counts['P_PENDING_SMALL_CLOSURE'][1]+=st.st_size
summary={'counts':dict(counts),'protected_run_count':len(protected_runs),'source_hold_count':len(holds),'metadata_errors':errors,'manifest_sha256':h(out/'plan_manifest_v2.csv.gz'),'eligibility_is_archive_read_authorization_only':True,'G2_approved':False,'W':'EXCLUDED','M':'DEFERRED','G3_agent_implementation':'FORBIDDEN','net_saving':'RECALCULATE_AFTER_G1; original112GiB not valid for reduced scope'}
(out/'plan_summary_v2.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))
