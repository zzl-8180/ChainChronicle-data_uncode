/* Reverse-denominator R01 audit. Reads the selected production directory by default.
 * Usage: node verify_r01_production.js READER [--output DIR] [--source MODULE_DIR]
 * Never writes into READER or changes historical audit receipts. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const {freshReviewDirectory}=require('./review_output.cjs');
const argv=process.argv.slice(2),root=path.resolve(argv[0]||'output/character_skills/reader_full_20261106');
function option(key,fallback){const i=argv.indexOf(key);return i<0?fallback:argv[i+1];}
const explicitOutput=option('--output',null),source=path.resolve(option('--source',root));
const out=explicitOutput?path.resolve(explicitOutput):freshReviewDirectory('r01-production');
if(explicitOutput){
 for(let parent=out;;parent=path.dirname(parent)){
  if(fs.lstatSync(parent,{throwIfNoEntry:false})&&path.relative(parent,fs.realpathSync(parent)))throw new Error('Output path uses a link: '+parent);
  if(parent===path.dirname(parent))break;
 }
 fs.mkdirSync(out,{recursive:true});
}
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
function load(rel){const ctx={window:{}};vm.runInNewContext(fs.readFileSync(path.join(root,rel),'utf8'),ctx,{filename:rel});return JSON.parse(JSON.stringify(ctx.window));}
const inline=require(path.join(source,'inline.js')),branches=require(path.join(source,'branches.js')),levels=require(path.join(source,'levels.js'));
const candidates=load('data/branch_candidates.js').CC_BRANCH_CANDIDATES,conditions=load('data/branch_conditions.js').CC_BRANCH_CONDITIONS,assessments=load('data/branch_assessments.js').CC_BRANCH_ASSESSMENTS;
const newAudit=path.join(root,'audit/c19_r01_fix_20261107');
const receiptFile=path.join(fs.existsSync(path.join(newAudit,'condition_closeout_receipt.json'))?newAudit:path.join(root,'audit/c19_closeout_20261107'),'condition_closeout_receipt.json'),receipt=read(receiptFile);
const failures=[],checks={};function check(ok,kind,detail){checks[kind]=(checks[kind]||0)+1;if(!ok)failures.push({kind,detail});}
const parentViews=new Map(),selection=[],targets=[],rawAnswers=new Map(),sameText=[],profileDuplicates=[],allBranchRows=[];
const answerId=(row,effect,answer)=>JSON.stringify([row.id,effect.id,inline.answerKey(answer)]);
function branchList(answer){return answer.displayBranches|| (answer.displayBranch?[answer.displayBranch]:[]);}
const files=fs.readdirSync(path.join(root,'data/cards')).filter(n=>/^\d+\.js$/.test(n)).sort((a,b)=>parseInt(a)-parseInt(b));
for(const file of files){
 const cid=String(parseInt(file)),raw=load(`data/cards/${cid}.js`).CC_DETAILS[cid];
 for(const g of raw.groups||[])for(const s of g.skills||[])for(const r of s.rows||[])for(const e of r.effects||[])for(const a of e.answers||[])rawAnswers.set(answerId(r,e,a),{cid,rowId:r.id,effect:e.label,answer:a});
 const special=(raw.groups||[]).filter(g=>g.key==='special_move'||g.label==='必杀技').flatMap(g=>g.skills||[]).flatMap(s=>s.rows||[]);
 const denju=(raw.groups||[]).filter(g=>g.key==='denju'||g.label==='传授').flatMap(g=>g.skills||[]).flatMap(s=>s.rows||[]);
 for(const r of special)for(const d of denju)if(r.original&&r.original===d.original)sameText.push({cid:Number(cid),specialRowId:r.id,denjuRowId:d.id,original:r.original,textZh:r.textZh,onlyCharacterInfo:(r.effects||[]).every(e=>!(e.answers||[]).length)});
 const applied=branches.apply(raw,candidates.cards[cid]);
 const merged=inline.orderGroups(inline.mergeGroups(applied.groups));
 const specialGroup=merged.find(g=>g.label==='必杀技'),denjuGroup=merged.find(g=>g.label==='传授');
 if(specialGroup?.skills?.length&&specialGroup.skills.every(s=>s.sourceKind==='character_profile')){
  for(const s of specialGroup.skills)for(const d of denjuGroup?.skills||[])if(JSON.stringify(s.rows.map(r=>r.original))===JSON.stringify(d.rows.map(r=>r.original)))profileDuplicates.push({cid:Number(cid),specialRows:s.rows.map(r=>r.id),denjuRows:d.rows.map(r=>r.id),originals:s.rows.map(r=>r.original)});
 }
 for(const group of merged)for(const skill0 of levels.groupSkills(group)){
  const skill=inline.prepareSkill(skill0,conditions.records,assessments.records,assessments.resolvedParents);
  for(const b of skill.branchTable||[]){const view={cid:Number(cid),tableId:b.tableId,key:b.key,condition:b.conditionLabel,conditionKnown:b.conditionKnown,raw:b.raw,values:b.values,order:b.order,displayAliasOf:b.displayAliasOf,executionSlots:b.executionSlots,displayExclusionReason:b.displayExclusionReason};if(!parentViews.has(b.key))parentViews.set(b.key,[]);parentViews.get(b.key).push(view);allBranchRows.push(view);}
  for(const row of skill.rows||[]){
   const shown=levels.displayRow(row,inline.answerKey),plan=shown.levelRows||shown.extraLevelStage?levels.presentation(shown,inline):inline.plan(shown);
   for(const effect of row.effects||[])for(const answer of effect.answers||[]){
    const review=answer.displayAssessment;if(!review?.selectionResolved)continue;
    const refs=branchList(answer),entries=(skill.branchTable||[]).filter(b=>refs.some(r=>r.key===b.key));
    const insertion=(plan.inserts||[]).find(i=>(i.answers||[i.answer]).includes(answer));
    const visible=(plan.visible||[]).find(i=>i.effect===effect);
    const matchingValues=entries.flatMap(b=>(b.values||[]).filter(v=>v.rowId===row.id&&v.label===effect.label&&v.text===inline.compact(answer,effect.label)).map(v=>({parent:b.key,condition:b.conditionLabel,value:v})));
    const item={cid:Number(cid),rowId:row.id,effect:effect.label,answerId:answerId(row,effect,answer),text:answer.text,confidence:answer.confidence,color:inline.candidate(answer)?'branch-candidate':answer.confidence,reviewStatus:review.status,condition:review.condition,selectionKey:review.selectionKey,refs:refs.map(b=>({key:b.key,condition:b.conditionLabel,known:b.conditionKnown})),location:insertion?'inline':visible?'visible-comparison':'not-directly-displayed',branchValues:matchingValues};selection.push(item);
    check(refs.length>0,'selection_has_display_branch',item);
    check(refs.some(b=>b.conditionKnown&&b.conditionLabel),'selection_has_condition',item);
    check(Boolean(insertion||visible||matchingValues.length),'selection_condition_value_position',item);
   }
   if((cid==='30207'&&row.id.endsWith('pattern0-lvorder0-f0'))||(cid==='30310'&&row.id.includes('-denju-'))){targets.push({cid:Number(cid),rowId:row.id,text:row.textZh,effects:row.effects,unknown:row.unknownEffects,plan,branches:skill.branchTable});}
  }
 }
}
check(files.length===2236,'card_denominator',files.length);
check(selection.length===883,'selection_denominator',selection.length);
const parentCoverage=Object.entries(receipt.resolvedCohortParents).map(([key,p])=>{
 const views=(parentViews.get(key)||[]).filter(v=>v.cid===Number(p.cid));
 const item={key,cid:p.cid,parentSource:p.parentSource,condition:p.conditionLabel,selectionUnavailable:p.selectionUnavailable||false,views};
 check(views.length>0,'resolved_parent_present',item);
 for(const v of views){check(JSON.stringify(v.raw)===JSON.stringify(p.parentRaw),'resolved_parent_exact_raw',{key,tableId:v.tableId});check(v.conditionKnown&&v.condition===(p.selectionUnavailable?'本模式常规选档不选用':p.conditionLabel),'resolved_parent_condition',{key,tableId:v.tableId,actual:v.condition});check((v.values||[]).length>0||Boolean(v.displayExclusionReason),'resolved_parent_values_or_explicit_exclusion',{key,tableId:v.tableId,reason:v.displayExclusionReason});
  if(v.displayAliasOf){const donor=allBranchRows.find(d=>d.key===v.displayAliasOf&&d.tableId===v.tableId);check(Boolean(donor),'alias_donor_present',{key,donor:v.displayAliasOf});if(donor)for(let slot=0;slot<7;slot++)check((v.raw?.[`skillid${slot}`]||0)===(donor.raw?.[`skillid${slot}`]||0),'alias_exact_execution_slot',{key,donor:donor.key,slot,actual:v.raw?.[`skillid${slot}`],expected:donor.raw?.[`skillid${slot}`]});}
 }
 return item;
});
check(parentCoverage.length===394,'parent_denominator',parentCoverage.length);
const cohort=receipt.cohorts['30207:CACHE:8192'],b01=targets.find(t=>t.cid===30207),probe=cohort.probes.find(p=>p.selectorCount===1);
check(cohort.actualSameModeParentIds.length===8,'B01_parent_denominator',cohort.actualSameModeParentIds);
for(const id of cohort.actualSameModeParentIds)check(b01?.branches?.some(b=>b.key===`CACHE:${id}`),'B01_all_eight',id);
for(const [id,end]of [[43020700,0],[43020701,2],[43020702,4],[43020703,6]]){const b=b01?.branches?.find(b=>b.key===`CACHE:${id}`);check(b?.conditionLabel?.includes(`0–${end}`)&&b.values?.some(v=>v.rowId===b01.rowId&&/15倍/.test(v.text)),'B01_fifteen_value_and_range',{id,branch:b});}
const count15=[43020701,43020702,43020703].reduce((n,id)=>n+(probe.selectedDrawCounts[id]||0),0);check(count15===300&&probe.drawDenominator===500,'B01_count1_probe',{count15,probe});
// Independently enumerate all integer draws from the eight same-mode parents,
// preserving native source order. Do not derive eligibility from prose labels
// or copy the receipt's eligibleIds/selectedDrawCounts into the calculation.
const manaParents=cohort.allParents.filter(p=>cohort.actualSameModeParentIds.includes(p.parentId));
const manaMatrix=[];
check(cohort.probes.length===13&&new Set(cohort.probes.map(p=>p.selectorCount)).size===13,'B01_probe_domain',cohort.probes.map(p=>p.selectorCount));
for(let count=0;count<=12;count++){
 const frozen=cohort.probes.find(p=>p.selectorCount===count);
 const eligible=manaParents.filter(p=>{const low=p.raw.mns??0,high=p.raw.mne??0;return !(low||high)||(low<=count&&count<=high);});
 const denominator=eligible.reduce((n,p)=>n+(p.raw.priority??0),0),drawCounts={};
 check(denominator>0,'B01_positive_draw_pool',count);
 for(let draw=0;draw<denominator;draw++){
  let cursor=0,chosen=null;
  for(const p of eligible){const next=cursor+(p.raw.priority??0);if(cursor<=draw&&draw<next){chosen=p.parentId;break;}cursor=next;}
  check(chosen!==null,'B01_each_draw_has_parent',{count,draw});
  drawCounts[chosen]=(drawCounts[chosen]||0)+1;
 }
 const eligibleIds=eligible.map(p=>p.parentId),possibleSelectedIds=Object.keys(drawCounts).map(Number).sort((a,b)=>a-b);
 check(JSON.stringify(eligibleIds)===JSON.stringify(frozen?.eligibleIds),'B01_mana_eligibility',{count,actual:eligibleIds,receipt:frozen?.eligibleIds});
 check(denominator===frozen?.drawDenominator,'B01_mana_denominator',{count,actual:denominator,receipt:frozen?.drawDenominator});
 check(JSON.stringify(possibleSelectedIds)===JSON.stringify(frozen?.possibleSelectedIds),'B01_mana_possible_parents',{count,actual:possibleSelectedIds,receipt:frozen?.possibleSelectedIds});
 const parentRows=manaParents.map(p=>{
  const b=b01?.branches?.find(b=>b.key===`CACHE:${p.parentId}`),damage=p.executors.find(e=>e.slot==='skillid0')?.raw.skillparam1;
  const selected=drawCounts[p.parentId]||0,expected=frozen?.selectedDrawCounts?.[p.parentId]||0;
  check(selected===expected,'B01_mana_exact_parent_weight',{count,parentId:p.parentId,actual:selected,receipt:expected});
  for(const field of ['mns','mne','priority'])check((b?.raw?.[field]??0)===(p.raw[field]??0),'B01_production_parent_mana_raw',{count,parentId:p.parentId,field,production:b?.raw?.[field],receipt:p.raw[field]});
  const damageValues=(b?.values||[]).filter(v=>v.rowId===b01.rowId&&v.label==='伤害');
  check(damageValues.length>0&&damageValues.every(v=>v.text===`系数 ${damage}倍`),'B01_mana_production_damage_value',{count,parentId:p.parentId,damage,damageValues});
  return {parentId:p.parentId,source:p.source,rawManaFields:{mns:p.raw.mns??0,mne:p.raw.mne??0,priority:p.raw.priority??0},missingRawFields:['mns','mne','priority'].filter(k=>!(k in p.raw)),eligible:eligibleIds.includes(p.parentId),selectedDraws:selected,receiptSelectedDraws:expected,fraction:`${selected}/${denominator}`,damage,production:{key:b?.key,tableId:b?.tableId,condition:b?.conditionLabel,damageValues,allValues:b?.values,displayAliasOf:b?.displayAliasOf}};
 });
 const aggregate={};for(const p of parentRows){const key=String(p.damage);aggregate[key]=(aggregate[key]||0)+p.selectedDraws;}
 manaMatrix.push({selectorCount:count,eligibleIds,possibleSelectedIds,drawDenominator:denominator,selectedDrawCounts:drawCounts,damageDrawCounts:aggregate,parents:parentRows});
}
const b02spec=[[353,'pattern0-lvorder0-f3','回复输入系数 1.25倍'],[30257,'pattern1-lvorder1-f3','回复输入系数 1.25倍'],[30236,'pattern1-lvorder1-f2','攻击力提高 60%'],[30236,'pattern1-lvorder1-f2','固定防御'],[30310,'pattern0-lvorder0-f0','回复输入系数 1.5倍'],[30310,'pattern1-lvorder1-f0','回复输入系数 1.75倍']];
const b02Colors=['inferred','inferred','confirmed','confirmed','branch-candidate','branch-candidate'];
const b02=b02spec.map(([cid,suffix,text],index)=>{const matches=selection.filter(s=>s.cid===cid&&s.rowId.endsWith(suffix)&&s.text.includes(text));check(matches.length===1,'B02_target_identity',{cid,suffix,text,matches});check(matches[0]?.color===b02Colors[index],'B02_color_preserved',{cid,suffix,text,expected:b02Colors[index],actual:matches[0]?.color});return matches[0];});
const b03=targets.find(t=>t.cid===30310),heal=b03?.effects?.find(e=>e.answers?.some(a=>a.source?.rule==='bossskill|64|/skillparam1'));
check(heal&&/回复/.test(heal.label)&&!/解除异常/.test(heal.label),'B03_heal_label',heal);
check(b03?.effects?.some(e=>/解除异常/.test(e.label)&&!e.answers?.length&&e.status!=='has_answer'),'B03_anomaly_independent_unresolved',b03?.effects);
const healInsert=b03?.plan?.inserts?.find(i=>i.effect.id===heal?.id),healVisible=b03?.plan?.visible?.find(i=>i.effect.id===heal?.id);
check(Boolean(healInsert||healVisible),'B03_heal_visible',b03?.rowId);
if(healInsert)check(/小(?:幅)?回复$/.test(b03.text.slice(0,healInsert.end)),'B03_heal_anchor',{text:b03.text,end:healInsert.end});
const oldInventory=read(path.join(root,'audit/final5_evidence_20261107/inventory.json')),newInventory=read(path.join(root,'audit/c19_closeout_20261107/inventory.json'));
let rebuiltInventory=null;
if(fs.existsSync(path.join(newAudit,'inventory.json'))){
 rebuiltInventory=read(path.join(newAudit,'inventory.json'));
 check(rebuiltInventory.stats.inferred===1936&&rebuiltInventory.stats.purple===286&&rebuiltInventory.items.length===2222,'rebuilt_inventory_denominator',rebuiltInventory.stats);
 rebuiltInventory.items.forEach((item,index)=>{const old=newInventory.items[index];check(item.rowId===old.rowId&&item.text===old.text&&item.source.raw===old.source.raw&&item.source.rule===old.source.rule&&item.review.status===old.review.status,'rebuilt_inventory_status_value_preserved',{index,rowId:item.rowId,oldStatus:old.review.status,newStatus:item.review.status});});
}
const promotions=newInventory.items.map((x,i)=>({x,i,before:oldInventory.items[i]})).filter(x=>x.before.review.status==='purple'&&x.x.review.status==='inferred');
const n06=promotions.filter(({x})=>x.source.branchId==null).map(({x,i,before})=>{
 const base=[...rawAnswers.values()].find(v=>v.rowId===x.rowId&&v.effect===x.effect&&v.answer.text===x.text&&v.answer.source?.answerIndex===x.source.answerIndex);
 check(Boolean(base),'N06_existing_base_answer',{index:i,row:x.rowId});
 check(before.text===x.text&&before.source.raw===x.source.raw,'N06_value_unchanged',i);
 return {inventoryIndex:i,cid:x.cid,rowId:x.rowId,effect:x.effect,answerIndex:x.source.answerIndex,text:x.text,raw:x.source.raw,source:x.source,before:before.review,after:x.review,counting:'included in the 474 display promotions; not one of 407 new answers',existingBaseAnswer:base?.answer,finalConditionReceiptSHA256:hash(receiptFile)};
});
check(promotions.length===474&&n06.length===15&&new Set(n06.map(x=>x.rowId)).size===14,'N06_denominators',{promotions:promotions.length,baseAnswers:n06.length,rows:new Set(n06.map(x=>x.rowId)).size});
const receiptHash=hash(receiptFile),legacyValidation=read(path.join(root,'audit/c19_closeout_20261107/cohort_parent_validation.json'));
const n03={receiptFile,receiptSHA256:receiptHash,historicalValidationSHA256:hash(path.join(root,'audit/c19_closeout_20261107/cohort_parent_validation.json')),historicalRecordedReceiptSHA256:legacyValidation.receiptSHA256,historicalMatchesFinal:legacyValidation.receiptSHA256===receiptHash,historicalUnchanged:true,validation:'This new reverse scan binds to the final receipt bytes above; historical audit is preserved.'};
fs.mkdirSync(out,{recursive:true});
const emit=(name,value)=>fs.writeFileSync(path.join(out,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
emit('n03_final_receipt_binding.json',n03);emit('n06_existing_base_display_promotions.json',n06);emit('resolved_parent_coverage.json',parentCoverage);emit('selection_resolved_positions.json',selection);emit('same_text_cross_groups.json',sameText);emit('profile_only_cross_group_duplicates.json',profileDuplicates);emit('b02_targets.json',b02);
emit('b01_mana_matrix.json',{receiptFile,receiptSHA256:hash(receiptFile),cohortKey:'30207:CACHE:8192',domain:'selectorCount 0..12 inclusive; no extrapolation beyond 12',method:'Independent inclusive mns/mne gates (missing getters default 0), native parent order, cumulative priority integer draws; compares each parent with receipt probes and production branch values.',excludedDifferentModeParents:cohort.allParents.filter(p=>!cohort.actualSameModeParentIds.includes(p.parentId)).map(p=>({parentId:p.parentId,flag:p.raw.flag,source:p.source})),rows:manaMatrix});
const result={pass:failures.length===0,scriptSHA256:hash(__filename),root,moduleDirectory:source,modules:Object.fromEntries(['inline','branches','levels'].map(n=>[n,hash(path.join(source,n+'.js'))])),receiptSHA256:receiptHash,counts:{cards:files.length,resolvedParents:parentCoverage.length,selectionResolved:selection.length,missingParents:parentCoverage.filter(p=>!p.views.length).length,missingDisplayBranch:selection.filter(s=>!s.refs.length).length,sameTextCards:new Set(sameText.map(s=>s.cid)).size,profileOnlySameTextCards:new Set(profileDuplicates.map(s=>s.cid)).size,n06:n06.length,rebuiltInferred:rebuiltInventory?.stats.inferred,rebuiltPurple:rebuiltInventory?.stats.purple},checks,failures,b01:{count15,denominator:probe.drawDenominator},b02,b03:{rowId:b03?.rowId,label:heal?.label,healInsert:Boolean(healInsert),healVisible:Boolean(healVisible)},limits:['Node production-model audit; DOM/browser behavior requires separate browser acceptance.','N03 new binding is recomputed; historical mismatching receipt is deliberately not rewritten.','N06 comparison uses frozen C18 final5 inventory versus C19 closeout inventory and verifies base-answer presence in actual card data.']};emit('validation.json',result);console.log(JSON.stringify({pass:result.pass,counts:result.counts,failedChecks:failures.length,output:out}));process.exitCode=result.pass?0:1;
