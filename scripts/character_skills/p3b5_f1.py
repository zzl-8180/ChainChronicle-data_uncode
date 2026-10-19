"""F1 rectification: preserve the actual native multi-candidate loop and attack tail."""
from __future__ import annotations
import collections,hashlib,json,os,struct,subprocess,sys
from pathlib import Path
import common as C
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
import unicorn.arm64_const as R
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from remaining_five import rule_rows
BASE=C.ROOT/'output/character_skills';OUT=BASE/'remaining_five'
BEFORE=C.ROOT/'work/character_skills_p3b5/r1_before/output/character_skills'
def rows(p):return [json.loads(x) for x in Path(p).open(encoding='utf8')]
def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def holders(rr):
 for p in rr:
  for h in [p]+p['children']:yield p['rec_key'],h
def native():
 raw=(C.ROOT/'work/protection/il2cpp_loader_seed1.bin').read_bytes();samples=[]
 dis=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 pins={0x1199d68:'ldr s0, [x19, #0xc0]',0x1199d6c:'fcmp s0, #0.0',0x1199d70:'b.gt #0x1199d8c',
       0x1199d74:'add w23, w23, #1',0x1199d78:'cmp w25, w23',0x1199d7c:'b.eq #0x1199d8c',
       0x1199d80:'ldr x0, [x19, #0x128]',0x1199d84:'cbnz x0, #0x1199ce0'}
 actual={}
 for a in pins:
  i=next(dis.disasm(raw[a:a+4],a));actual[a]=i.mnemonic+' '+i.op_str
 assert actual==pins
 for reset in [0,-.5,.5]:
  u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0,(len(raw)+4095)&~4095);u.mem_write(0,raw)
  u.mem_map(0x40000000,0x20000);u.reg_write(R.UC_ARM64_REG_SP,0x4001f000)
  def reg(name,v):u.reg_write(getattr(R,'UC_ARM64_REG_'+name),v)
  def put(off,fmt,value):u.mem_write(0x40000000+off,struct.pack(fmt,value))
  reg('X19',0x40001000);reg('X27',0x40002000);reg('X26',0x40003000);reg('W25',2);reg('W23',0)
  put(0x1128,'<Q',0x40004000);put(0x10b8,'<Q',0x40005000);put(0x5018,'<I',0)
  put(0x3000,'<Q',0x40006000);put(0x60e0,'<I',1);put(0x1048,'<f',reset);put(0x10c8,'<I',5)
  for i in range(2):put(0x7010+i*0x100,'<Q',0x40008000+i*0x100);put(0x8018+i*0x100,'<I',1)
  trace=[]
  def hook(uc,a,size,data):
   if a==0xa84484:
    idx=uc.reg_read(R.UC_ARM64_REG_W1);reg('X0',0x40007000+idx*0x100);reg('PC',uc.reg_read(R.UC_ARM64_REG_LR))
   elif a==0x1eb8358:reg('W0',0);reg('PC',uc.reg_read(R.UC_ARM64_REG_LR))
   elif a==0x13aeea4:reg('W0',1);reg('PC',uc.reg_read(R.UC_ARM64_REG_LR))
   elif a==0x119a47c:reg('PC',0x119a608)
   elif a==0x119a620:
    trace.append(struct.unpack('<I',uc.mem_read(0x400010c8,4))[0]);reg('PC',0x1199d68)
  u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x1199ce0,0x1199d8c,count=250)
  expected=[6] if reset>0 else [6,7]
  samples.append(dict(cooldown_reset=reset,initial_count=5,positive_entry_threshold=6,qualified_candidates=2,
     attack_counts=trace,expected=expected,passed=trace==expected))
 result=dict(image_sha256=hashlib.sha256(raw).hexdigest(),passed=all(r['passed'] for r in samples),samples=samples,
  pins=[dict(rva=hex(a),instruction=pins[a]) for a in pins],
  scope='Entry gate already permits initial count5<threshold6. Execute actual inner candidate loop and actual attack tail; mock only list lookup/null/hit, skip unrelated attack body.',
  independent_review_source='output/character_skills/review/p3b5_20261019_remaining_five/native_fragments.json',
  limitation='Not a full battle/device simulation. Time/count entry gate evidence remains the initial reviewed native evidence.')
 C.write_json(OUT/'f1_native_evidence.json',result);assert result['passed']
 C.write_json(OUT/'field_dictionary.json',rule_rows())
 print('F1 native counterexample 3/3; six rule rows rebuilt')
def account():
 checks=[]
 def ck(name,ok,**detail):checks.append(dict(name=name,passed=bool(ok),**detail))
 old=rows(BEFORE/'profiles/records.jsonl');now=rows(BASE/'profiles/records.jsonl');newby={r['rec_key']:r for r in now}
 def full(rr):return collections.Counter((p,h['table'],h['record_id'],canon(a)) for p,h in holders(rr) for a in h['answers'])
 pre=rows(C.ROOT/'work/character_skills_p3b5/before/profiles/records.jsonl')
 ck('all81916_old_answer_objects_and_multiplicity',not full(pre)-full(now))
 ck('all_fragments_baseline_and_source_preserved',all(r['fragments']==newby[r['rec_key']]['fragments'] and r['baseline_answers']==newby[r['rec_key']]['baseline_answers'] and r['source']==newby[r['rec_key']]['source'] and
    [(h['table'],h['record_id'],h['source']) for h in r['children']]==[(h['table'],h['record_id'],h['source']) for h in newby[r['rec_key']]['children']] for r in old))
 a={(p,h['table'],h['record_id'],x['rule_key'],x['f']):x for p,h in holders(old) for x in h['answers']}
 b={(p,h['table'],h['record_id'],x['rule_key'],x['f']):x for p,h in holders(now) for x in h['answers']}
 changed=[k for k in a if a[k]!=b[k]];allowed={f'bossskill|73|/skillparam{s}' for s in [5,6,7]}
 ck('only_type73_three_field_text_and_kind_changed',set(a)==set(b) and len(changed)==27 and all(k[3] in allowed and all(a[k][f]==b[k][f] for f in ['f','raw','rule_key','unit','status','scope']) for k in changed),changed_rows=len(changed),by_rule=dict(collections.Counter(k[3] for k in changed)))
 ro=C.load_json(BEFORE/'profiles/rules.json');rn=C.load_json(BASE/'profiles/rules.json')
 ck('old_rules_and_other_three_new_rules_preserved',set(ro)==set(rn) and {k for k in ro if ro[k]!=rn[k]}==allowed)
 so=C.load_json(BEFORE/'profiles/summary.json');sn=C.load_json(BASE/'profiles/summary.json')
 ck('all_counts_and_status_unchanged',so==sn and rows(BEFORE/'profiles/profiles.jsonl')==rows(BASE/'profiles/profiles.jsonl'))
 ck('initial_raw97_source52_and_binding_proofs_unchanged',all((BEFORE/'remaining_five'/p).read_bytes()==(OUT/p).read_bytes() for p in ['raw_crosscheck.json','source_records.jsonl','imuka_gate_trace.json','validation.json']))
 bindings=[p for folder in ['description_bindings/type8','type26_mana'] for p in (C.ROOT/'work/character_skills_p3b5/before'/folder).glob('*.json*') if 'bindings' in p.name or 'type8' in str(p.parent)]
 ck('all_type8_and_type26_binding_bytes_preserved',all(p.read_bytes()==(BASE/p.relative_to(C.ROOT/'work/character_skills_p3b5/before')).read_bytes() for p in bindings))
 # Update only materialised new-answer ledgers; the initial raw97 audit is retained.
 ledger=rows(OUT/'field_answers.jsonl')
 for r in ledger:r['answer']=b[r['parent_rec_key'],r['table'],r['record_id'],r['answer']['rule_key'],r['answer']['f']]
 C.write_jsonl(OUT/'field_answers.jsonl',ledger)
 target=C.load_json(OUT/'target_five.json')
 for r in target:
  for x in r['rows']:x['answer']=b[x['parent'],x['table'],x['record_id'],x['answer']['rule_key'],x['answer']['f']]
 C.write_json(OUT/'target_five.json',target)
 env=dict(os.environ,PYTHONUTF8='0',PYTHONIOENCODING='cp936');cli=[]
 for mode in ['json','text']:
  run=subprocess.run([sys.executable,'-B',str(C.ROOT/'scripts/character_skills/query.py'),'--cid','8151',*(['--json'] if mode=='json' else [])],cwd=C.ROOT,env=env,capture_output=True)
  (OUT/f'cli_8151_{mode}.log').write_bytes(run.stdout+run.stderr)
  cli.append(dict(mode=mode,passed=run.returncode==0 and not run.stderr and '候选遍历入口'.encode() in run.stdout))
 ck('GBK_json_and_text_new_entry_boundary',all(x['passed'] for x in cli),samples=cli)
 ck('new_rules_and_answers_trace_cooldown_counterexample',all('f1_native_evidence.json' in str(rn[k]['evidence']) for k in allowed) and
    all('本轮' in b[k]['note'] and '入口' in b[k]['note'] for k in changed))
 report=dict(status='INITIAL_D_REQUIRES_RECTIFICATION_F1_FIXED_PENDING_R2',checks=checks,passed=sum(r['passed'] for r in checks),total=len(checks),
  changed_rows=len(changed),unchanged_rows=len(a)-len(changed),counts=sn['totals'],status_counts=sn['status_counts'],
  raw_verification_reused='Initial C raw97/97 plus independent D raw97/97; full raw/source objects unchanged; no raw re-read needed')
 C.write_json(OUT/'rectification_validation.json',report);print(f"F1 checks {report['passed']}/{report['total']}; changed {len(changed)} rows")
 assert report['passed']==report['total']
def stable():
 paths=[p for f in ['profiles','charainfo_params'] for p in (BASE/f).rglob('*') if p.is_file()]
 paths += [OUT/p for p in ['field_dictionary.json','field_answers.jsonl','target_five.json','f1_native_evidence.json','rectification_validation.json','dom_validation.json','cli_8151_json.log','cli_8151_text.log']]
 def sha():return {str(p.relative_to(C.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 before=sha();native()
 for script in ['profiles','charainfo_params']:
  run=subprocess.run([sys.executable,'-B',str(C.ROOT/f'scripts/character_skills/{script}.py')],cwd=C.ROOT,capture_output=True)
  (C.ROOT/f'work/character_skills_p3b5/f1_stable_{script}.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0
 account();run=subprocess.run(['node','scripts/character_skills/p3b5_dom.js'],cwd=C.ROOT,capture_output=True);assert run.returncode==0
 after=sha();changed=[p for p in before if before[p]!=after[p]]
 C.write_json(OUT/'rectification_stability.json',dict(files=len(paths),passed=not changed,changed=changed,hashes=after));print('F1 stable',len(paths),'files; changed',changed);assert not changed
def freeze():
 initial=C.load_json(OUT/'frozen_manifest.json')
 paths=[C.ROOT/r['path'] for r in initial['files']]
 paths += [C.ROOT/'scripts/character_skills/p3b5_f1.py',OUT/'frozen_manifest.json']
 paths += [p for p in OUT.rglob('*') if p.is_file() and p.name!='rectification_manifest.json']
 rows=[dict(path=str(p.relative_to(C.ROOT)),size=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(set(paths))]
 previous={r['path']:r['sha256'] for r in initial['files']}
 diff=[r['path'] for r in rows if r['path'] in previous and r['sha256']!=previous[r['path']]]
 C.write_json(OUT/'rectification_manifest.json',dict(status='INITIAL_D_REQUIRES_RECTIFICATION_F1_FIXED_PENDING_R2',files=rows,changed_initial_paths=diff,
    preserved_initial_manifest_sha256=hashlib.sha256((OUT/'frozen_manifest.json').read_bytes()).hexdigest(),readonly_historical_scope=initial['readonly_historical_scope']))
 print('F1 frozen',len(rows),'files;',len(diff),'initial paths changed')
if __name__=='__main__':
 C.enable_utf8_console()
 if '--native' in sys.argv:native()
 elif '--stable' in sys.argv:stable()
 elif '--freeze' in sys.argv:freeze()
 else:account()
