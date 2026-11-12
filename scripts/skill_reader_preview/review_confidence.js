/* Reconcile display uncertainty against frozen bindings and decoded records.
 * Does not write formal answers, frozen cards, or the branch candidate overlay. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const inline=require('./web/inline'),branches=require('./web/branches');
const damageStructure=require('./review_damage_structure');
const root=path.resolve(__dirname,'../..');
const {readPath,writePath}=require('./project_layout_paths.cjs');
const {freshReviewDirectory}=require('./review_output.cjs');
const argv=process.argv.slice(2);
function option(name){
 const index=argv.indexOf(name);
 if(index<0)return null;
 if(!argv[index+1]||argv[index+1].startsWith('--'))throw new Error('Missing value for '+name);
 return argv[index+1];
}
function inside(child,parent){
 const rel=path.relative(parent,child);
 return !path.isAbsolute(rel)&&rel!=='..'&&!rel.startsWith('..'+path.sep);
}
function requireDirect(target){
 for(let current=target;;current=path.dirname(current)){
  const stat=fs.lstatSync(current,{throwIfNoEntry:false});
  if(stat&&path.relative(current,fs.realpathSync(current))!=='')throw new Error('Output path uses a link: '+current);
  if(current===path.dirname(current))break;
 }
}
const stageOption=option('--output'),inputOption=option('--input'),auditDir=option('--audit-dir');
const replace=argv.includes('--replace-stage-assessments');
if((stageOption&&inputOption)||(!stageOption&&(auditDir||replace)))throw new Error('Use --input for independent review, or --output for a writable Reader stage.');
const formal=path.join(root,'output/character_skills');
const stage=stageOption&&writePath(path.resolve(stageOption),root);
if(stage){
 requireDirect(stage);
 if(inside(stage,formal)||inside(stage,readPath(formal,root)))throw new Error('Use a separate Reader stage: '+stage);
 const stageParents=['work','projects/reader/site','projects/reader/pilots'].map(parent=>path.join(root,parent));
 if(inside(stage,root)&&!stageParents.some(parent=>inside(stage,parent)&&path.relative(parent,stage)!=='')){
  throw new Error('Use a named Reader stage under work or projects/reader: '+stage);
 }
 const auditRoot=path.join(stage,'audit');
 requireDirect(auditRoot);
 if(fs.existsSync(auditRoot)&&fs.readdirSync(auditRoot,{recursive:true,withFileTypes:true}).some(entry=>entry.name==='stage_seal.json')){
  throw new Error('Reader stage is sealed. Use a new stage.');
 }
}
const out=readPath(stageOption||inputOption?path.resolve(stageOption||inputOption):path.join(formal,'reader_full_20261106'),root);
const stageAudit=auditDir&&path.resolve(stage,auditDir);
if(stageAudit&&(path.isAbsolute(auditDir)||!inside(stageAudit,path.join(stage,'audit'))||stageAudit===path.join(stage,'audit')))throw new Error('--audit-dir must name a version under the stage audit directory');
if(stageAudit){
 requireDirect(stageAudit);
 for(const name of ['inventory.json','changes.json']){
  if(fs.lstatSync(path.join(stageAudit,name),{throwIfNoEntry:false}))throw new Error('Choose a new audit version: '+stageAudit);
 }
}
const stageSidecar=stage&&path.join(stage,'data/branch_assessments.js');
if(stageSidecar){
 requireDirect(stageSidecar);
 const stat=fs.lstatSync(stageSidecar,{throwIfNoEntry:false});
 if(stat&&(!replace||!stat.isFile()||stat.nlink!==1))throw new Error('Use a new stage sidecar, or explicitly replace an unshared stage file: '+stageSidecar);
}
const sourcePath=file=>{
 const logical=path.resolve(root,file);
 if(logical!==root&&!logical.startsWith(root+path.sep))throw new Error('Source path escapes candidate root: '+file);
 return file.replace(/\\/g,'/').startsWith('scripts/')?logical:readPath(logical,root);
};
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const context={window:{}};
for(const name of ['branch_candidates','branch_conditions','mana_costs'])vm.runInNewContext(fs.readFileSync(path.join(out,`data/${name}.js`),'utf8'),context);
const overlay=JSON.parse(JSON.stringify(context.window.CC_BRANCH_CANDIDATES.cards)),parents=JSON.parse(JSON.stringify(context.window.CC_BRANCH_CONDITIONS.records));
const previous=read(path.join(out,'audit/branch_candidates_20261107/inventory.json'));
const files=new Map(),sourceHashes={},frozenHashes={},records={},items=[],stats={cards:0,reviewed:0,inferred:0,purple:0,reasons:{},bindingKinds:{}};
const invariantFile=path.join(out,'audit/trigger_evidence_20261107/branch_invariance_receipt.json');
const invariantReceipt=fs.existsSync(invariantFile)?read(invariantFile):{inputs:{},items:[]};
for(const [file,digest] of Object.entries(invariantReceipt.inputs)){
 assert.equal(sha(fs.readFileSync(sourcePath(file))),digest,`invariance source changed: ${file}`);
 sourceHashes[file]=digest;
}
const invariantKey=(rowId,s)=>JSON.stringify([rowId,s.layer,s.branchId,s.recordId,s.rule,s.field,s.raw]);
const invariants=new Map(invariantReceipt.items.filter(i=>i.branchInvariant).map(i=>[invariantKey(i.rowId,i.source),i]));
const partialFile=path.join(out,'audit/trigger45_evidence_20261107/partial_conditions_receipt.json');
const partialReceipt=fs.existsSync(partialFile)?read(partialFile):{inputs:{},items:[]};
for(const [file,digest] of Object.entries(partialReceipt.inputs)){
 assert.equal(sha(fs.readFileSync(sourcePath(file))),digest,`partial trigger source changed: ${file}`);
 sourceHashes[file]=digest;
}
const partials=new Map(partialReceipt.items.filter(i=>i.partialCondition).map(i=>[invariantKey(i.rowId,i.source),i]));
const partialParents=new Map(partialReceipt.items.filter(i=>i.partialCondition).map(i=>[`${i.source.layer}:${i.source.branchId}`,i]));
const selectionFile=path.join(out,'audit/selection_order_20261107/selection_receipt.json');
const selectionReceipt=fs.existsSync(selectionFile)?read(selectionFile):{inputs:{},parents:{}};
for(const [file,digest] of Object.entries(selectionReceipt.inputs)){
 assert.equal(sha(fs.readFileSync(sourcePath(file))),digest,`selection evidence changed: ${file}`);sourceHashes[file]=digest;
}
const finalSparseFile=path.join(out,'audit/final5_evidence_20261107/sparse_receipt.json');
const finalRandomFile=path.join(out,'audit/final5_evidence_20261107/random_pool_receipt.json');
const finalSparse=fs.existsSync(finalSparseFile)?read(finalSparseFile):{inputs:{},parents:{}};
const finalRandom=fs.existsSync(finalRandomFile)?read(finalRandomFile):{inputs:{},items:[]};
const closeoutFile=path.join(out,'audit/c19_closeout_20261107/condition_closeout_receipt.json');
const closeout=fs.existsSync(closeoutFile)?read(closeoutFile):{inputs:{},parents:{},items:[]};
for(const receipt of [finalSparse,finalRandom,closeout])for(const [file,digest] of Object.entries(receipt.inputs)){
 assert.equal(sha(fs.readFileSync(sourcePath(file))),digest,`final five evidence changed: ${file}`);sourceHashes[file]=digest;
}
Object.assign(selectionReceipt.parents,finalSparse.parents);
Object.assign(selectionReceipt.parents,closeout.parents,closeout.resolvedCohortParents);
const closeoutKey=(rid,label,text,s)=>JSON.stringify([rid,s.effectId || label,s.layer,s.branchId,s.recordId,s.rule,s.field,s.raw,text,binding({source:s}).pattern_id,s.effectId,s.answerIndex]);
const closeoutItems=new Map(closeout.items.map(i=>[closeoutKey(i.rowId,i.effect,i.text,i.source),i]));
const randomParents=new Map(finalRandom.items.map(item=>[`${item.layer}:${item.branchId}`,item]));
function point(ref){
 const file=ref?.file || ref?.original_file, pointer=ref?.pointer || ref?.json_pointer;
 if(!file || !pointer)return null;
 const logical=path.resolve(root,file);
 if(!logical.startsWith(path.join(root,'output')+path.sep))return null;
 const absolute=readPath(logical,root);
 if(!files.has(absolute)){const bytes=fs.readFileSync(absolute);sourceHashes[file]=sha(bytes);files.set(absolute,JSON.parse(bytes.toString('utf8').replace(/^\uFEFF/,'')));}
 return pointer.split('/').slice(1).reduce((v,k)=>v?.[k.replace(/~1/g,'/').replace(/~0/g,'~')],files.get(absolute));
}
const recordTables=new Map();
function sourceRecord(a){
 const located=point(a.source) || point(a.source?.allSources);if(located)return located;
 const s=a.source || {},origin=s.allSources || {},b=binding(a),layer=s.layer || origin.layer || b.layer,table=origin.table || s.rule?.split('|')[0],id=s.recordId ?? origin.record_id ?? b.record_id;
 if(!['APK','CACHE'].includes(layer) || !['bossskill','skilllist'].includes(table) || id==null)return null;
 const key=`${layer}:${table}`;
 if(!recordTables.has(key)){
  const file=table==='bossskill'?context.window.CC_BRANCH_CONDITIONS.sources[layer].file:layer==='APK'?'output/base_master/_mdSkill.json':'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw';
  const pointer=table==='bossskill' && layer==='CACHE'?'/bossinfo/bossskill':`/${table}`;
  const all=point({file,pointer});const indexed=new Map();
  for(const record of all){assert(!indexed.has(record.skillid),'record identity must be unique within layer/table');indexed.set(record.skillid,record);}
  recordTables.set(key,indexed);
 }
 return recordTables.get(key).get(id) || null;
}
function binding(a){const b=a.source?.originalBinding || {};const selected=b.g1_b1_binding || b.c12_p3_skilltext_mirror_binding || b.c8_p1_t27_binding || b.c11_p1_t114_binding || b;return selected.parent_chain?{...selected,pattern_id:selected.parent_chain.pattern_id}:selected;}
function parent(a){return a.reviewParent || parents[a.displayBranch?.key || `${a.source?.layer || a.source?.allSources?.layer || binding(a).layer}:${a.source?.branchId ?? binding(a).pattern_id}`];}
function bossTable(layer,table){return point({file:context.window.CC_BRANCH_CONDITIONS.sources[layer]?.file,pointer:layer==='APK'?`/${table}`:`/bossinfo/${table}`});}
function recoverBoundParent(a,row,skill){
 const b=binding(a);
 if(!a.source?.originalBinding?.c8_p1_t27_binding || b.pattern_pointer!=='denju.patternid0' || !row.id.includes('-denju-') || skill.branchTable?.some(branch=>branch.id!==b.pattern_id))return a;
 const patterns=bossTable(b.layer,'bosspattern'),index=patterns?.findIndex(p=>p.patternid===b.pattern_id);
 if(index==null || index<0)return a;
 const raw=patterns[index];
 if(!raw.sinfo?.includes(row.original) || raw[b.bound_slot]!==b.record_id)return a;
 const branch={key:`${b.layer}:${b.pattern_id}`,id:b.pattern_id,layer:b.layer,raw,proseContext:true};
 inline.describeBranches([branch]);
 const source={file:context.window.CC_BRANCH_CONDITIONS.sources[b.layer].file,pointer:`${b.layer==='APK'?'':'/bossinfo'}/bosspattern/${index}`};
 return {...a,displayBranch:branch,reviewParent:{raw,source}};
}
function numeric(a){
 const s=a.source || {},record=sourceRecord(a),parts=(s.rule || '').split('|');
 return Boolean(record && parts.length===3 && parts[2]===s.field && Number(record[parts[0]==='bossskill'?'skillid0':'ability'])===Number(parts[1]) && Object.hasOwn(record,s.field.slice(1)) && record[s.field.slice(1)]===s.raw && ['confirmed','inferred'].includes(a.confidence));
}
function edges(a){
 const p=parent(a);if(!p)return [];
 assert.deepEqual(point(p.source),p.raw,'parent metadata matches decoded source');
 const s=a.source || {},rec=sourceRecord(a),id=rec?.skillid;
 const layer=a.displayBranch?.layer || s.layer || s.allSources?.layer || binding(a).layer;
 if(!rec || id==null)return [];
 const bossFile=context.window.CC_BRANCH_CONDITIONS.sources[layer]?.file;
 const bossPath=sourcePath(bossFile);
 const boss=files.get(bossPath) || (point({file:bossFile,pointer:'/'}),files.get(bossPath));
 const bossRows=layer==='APK'?boss.bossskill:boss.bossinfo.bossskill;
 const result=[];
 for(const [slot,child] of Object.entries(p.raw).filter(([k])=>/^skillid\d+$/.test(k))){
  if(s.rule.startsWith('bossskill|') && child===id)result.push(slot);
  if(s.rule.startsWith('skilllist|')){
   const owner=bossRows.find(r=>r.skillid===child);
   if(owner?.s_ability===id)result.push(slot+'/s_ability');
  }
 }
 return result;
}
function assess(a,row,effect,frozen,skill){
 // Old manually reviewed records carry fields in an explicit source array.
 if(!a.source?.rule && a.source?.associationEvidence==='确认' && Array.isArray(a.source.allSources)){
  const field=effect.label==='攻击力'?'/skillparam1':effect.label==='防御'?'/skillparam2':null;
  const matches=a.source.allSources.filter(s=>s.table==='bossskill' && s.present===true && s.field_path===field);
  if(matches.length===1){const origin=matches[0];a={...a,source:{...a.source,allSources:origin,rule:`bossskill|13|${field}`,field,raw:origin.raw_value}};}
 }
 // A separate source receipt identifies the displayed skill's exact parent.
 // Use it only for the same original prose, never for an unnamed alternate.
 if(!a.displayBranch || !parent(a)?.raw){
  const cost=context.window.CC_MANA_COSTS.records[skill.rows[0].id],ref=cost?.source;
  const raw=ref?.table==='bosspattern'?point(ref):null;
  const b=binding(a);
  if(raw && raw.patternid===ref.recordId && (b.pattern_id==null || b.pattern_id===raw.patternid) && raw.sinfo?.includes(row.original)){
   const branch={key:`${ref.layer}:${raw.patternid}`,id:raw.patternid,layer:ref.layer,raw,proseContext:true};inline.describeBranches([branch]);
   a={...a,displayBranch:branch,reviewParent:{raw,source:ref}};
  }
 }
 a=recoverBoundParent(a,row,skill);
 const s=a.source || {},b=binding(a),ob=s.originalBinding || {};
 const result={status:'purple',conditionKnown:Boolean(a.displayBranch?.conditionKnown),condition:a.displayBranch?.conditionLabel || '',bindingKind:'unresolved',bindingKnown:false,numericKnown:false,shortReason:'记录与效果对应待确认',evidence:[]};
 if(ob.inference_c11_p2_union_count){
  const count=ob.inference_c11_p2_union_count;
  result.numericKnown=numeric(a);result.bindingKnown=count.row_id===row.id && count.rule_key===s.rule && count.field_path===s.field && count.record_id===sourceRecord(a)?.skillid;
  result.bindingKind='count_scaling';result.shortReason='逐人增长方式待确认';result.evidence.push('原绑定披露per_person_scaling与人数上限未闭合');return result;
 }
 result.numericKnown=numeric(a);
 const actualEdges=edges(a);
 const parentId=a.displayBranch?.id ?? b.pattern_id;
 if(s.rule==='skilllist|3000|/param6' && effect.label==='持续时间' && s.evidenceScope==='B18_DURATION_SOURCE_DERIVED_PARTIAL'){
  const rec=sourceRecord(a);
  result.bindingKnown=Boolean(rec?.text?.includes(row.original) && (row.original.match(/一定時間/g)||[]).length===1 && row.effects.filter(e=>e.label==='持续时间').length===1 && s.raw>0);
  result.conditionKnown=result.bindingKnown;result.condition='原文所述共鸣触发时';result.bindingKind='own_record_duration';result.evidence.push('本行源记录ability3000.param6；唯一持续时间原句与记录text核对');
 }else if(s.rule==='bossskill|27|/skillparam1' && ob.c8_p1_t27_binding){
  result.bindingKnown=Boolean(b.row_id && [row.id,...(row.aliasIds||[])].includes(b.row_id) && b.rule_key===s.rule && b.field_path===s.field && b.record_id===sourceRecord(a)?.skillid && b.bound_type===27 && actualEdges.includes(b.bound_slot) && ['回复','生命回复'].includes(effect.label) && /回復/.test(row.original));
  result.bindingKind='explicit_heal_binding';result.evidence.push('旧t27唯一回复载体绑定；原父槽、子记录、字段和句面核对');
 }else if(s.scope!=='READER_PROVISIONAL_BRANCH_OVERLAY' && s.rule==='bossskill|114|/skillparam1' && effect.label==='伤害'){
  const p=parent(a),boss=point({file:p?.source.file || p?.source.original_file,pointer:a.displayBranch?.layer==='APK'?'/bossskill':'/bossinfo/bossskill'});
  const typed=boss?.filter(r=>r.skillid0===114 && Object.entries(p.raw).some(([k,v])=>/^skillid\d+$/.test(k) && v===r.skillid));
  result.bindingKnown=Boolean(p?.raw.sinfo?.includes(row.original) && /ダッシュ/.test(row.original) && /\d+回.*ダメージ/.test(row.original) && typed?.length===1 && typed[0].skillid===sourceRecord(a)?.skillid && actualEdges.length===1);
  result.bindingKind='explicit_dash_binding';result.evidence.push('本段冲刺重复伤害句与原父链唯一type114核对；不推算次数或总伤害');
 }else if(s.evidenceScope==='REVIEWED_RECORD' && s.associationEvidence==='确认' && /^bossskill\|13\|/.test(s.rule || '')){
  result.bindingKnown=actualEdges.length===1;result.bindingKind='legacy_reviewed_fields';result.evidence.push('旧逐句确认关联；allSources显式字段、原值和本段真实父链复核');
 }else if(/^C13_P3_2012_DURATION_MIRROR/.test(s.evidenceScope || '') && s.rule==='skilllist|2012|/param0' && effect.label==='持续时间'){
  const rec=sourceRecord(a),peer=row.effects.flatMap(e=>e.answers).filter(d=>d.source?.rule==='skilllist|2012|/param6' && d.source?.allSources?.record_id===rec?.skillid);
  result.bindingKnown=Boolean(peer.length===1 && rec.param7===1 && rec.param8===64 && !(rec.sub || []).length && /自身.*攻撃速度.*一定時間/.test(row.original) && actualEdges.length===1);
  result.bindingKind='same_record_speed_duration';result.evidence.push('本句自身加速与时长同一2012支持记录；对象、原值、父链复核');
 }else if(s.scope==='READER_PROVISIONAL_BRANCH_OVERLAY'){
  assert.deepEqual(sourceRecord(a),s.recordRaw,'candidate full record unchanged; old compatibility receipt must not hide changed fields');
  const donorRow=frozen.get(s.donorRowId);
  const donors=(donorRow?.effects || []).filter(e=>e.id===effect.id || e.label===effect.label && donorRow.effects.filter(x=>x.label===e.label).length===1).flatMap(e=>e.answers).filter(d=>!d.branchCandidate && ['inferred','confirmed'].includes(d.confidence) && d.source?.rule===s.donorRule && d.source?.raw===s.donorRaw);
  const base=parents[`${s.layer}:${s.baseBranchId}`];
  const auditEvent=previous.branches.find(v=>v.cid===Number(row.id.split('-')[0]) && v.branchId===s.branchId && v.layer===s.layer);
  const checked=auditEvent?.fields.find(f=>f.record===s.recordId && f.field===s.field && f.rule===s.rule && f.slot===s.parentSlot && f.rowId===s.donorRowId && f.effectId===effect.id && f.status==='句内候选' && !f.bindingMethod);
  const good=donors.filter(d=>{
   const record=sourceRecord(d),source=d.source?.allSources;
   if(!record || !source || source.layer!==s.layer || source.table!==(s.rule || '').split('|')[0] || record[s.field.slice(1)]!==s.donorRaw)return false;
   const fieldSlot=s.parentSlot?.split('/')[0];
   if(!s.parentSlot?.includes('/'))return base?.raw[fieldSlot]===source.record_id && record.skillid===source.record_id;
   const boss=point({file:base?.source.file,pointer:s.layer==='APK'?'/bossskill':'/bossinfo/bossskill'});
   return boss?.find(v=>v.skillid===base.raw[fieldSlot])?.s_ability===source.record_id && record.skillid===source.record_id;
  });
  result.bindingKnown=Boolean(checked && good.length===1 && actualEdges.includes(s.parentSlot));
  result.bindingKind=donors.length?'same_slot_donor':'semantic_fallback';
  result.evidence.push(result.bindingKnown?'冻结同效果供体＋已审同父槽同规则字段＋原表引用核验':'未能同时核实正式供体和父槽；句式/形状回退不作已绑定');
  if(result.bindingKnown)result.evidence.push(`供体 ${s.donorRowId} / ${s.donorRule} / ${s.donorRaw}`);
  else if(!donors.length){
   const rule=point({file:'output/character_skills/profiles/rules.json',pointer:'/'+s.rule.replace(/~/g,'~0').replace(/\//g,'~1')});
   const nativeType=s.rule==='bossskill|3|/skillparam1'?point({file:'output/character_skills/boss_attack_types/type_rules.json',pointer:'/types/3'}):null;
   const trace=pointer=>point({file:'output/sample/active_skill_trace.json',pointer});
   const intervalProof={type:trace('/active_type_raw'),enum:trace('/active_type_enum'),entry:trace('/dispatch/entry_index'),method:trace('/methods/3')};
   assert.equal(trace('/native_image_sha256'),point({file:'output/character_skills/boss_attack_types/type_rules.json',pointer:'/native_sha256'}));
   assert.equal(trace('/metadata_sha256'),point({file:'output/character_skills/boss_attack_types/type_rules.json',pointer:'/metadata_sha256'}));
   const supportRecords=point({file:s.layer==='APK'?'output/base_master/_mdSkill.json':'output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw',pointer:'/skilllist'});
   const supportRules=Object.fromEntries(['param7','param8','param9'].map(f=>{const k=`skilllist|2003|/${f}`;return [k,point({file:'output/character_skills/profiles/rules.json',pointer:'/'+k.replace(/\//g,'~1')})];}));
   const structural=damageStructure.evaluate({source:s,row,effect,base:base?.raw,alt:parent(a)?.raw,boss:bossTable(s.layer,'bossskill'),baseRecord:point(s.baseRecordSource),rule,nativeType,supportRecords,supportRules,intervalProof});
   if(structural){Object.assign(result,structural);result.evidence.push(`规则定位：output/character_skills/profiles/rules.json#/${s.rule}`);}
  }
 }else if(ob.c12_p3_skilltext_mirror_binding){
  const peer=frozen.get(b.peer_row_id);
  const hits=(peer?.effects || []).filter(e=>e.label===effect.label).flatMap(e=>e.answers).filter(d=>d.source?.rule===s.rule && d.source?.raw===s.raw && d.source?.allSources?.record_id===b.record_id);
  result.bindingKnown=Boolean(peer?.original===row.original && hits.length===1 && b.pattern_id===parentId && actualEdges.length===1);
  result.bindingKind='exact_peer_mirror';result.evidence.push(`明确同文同效果镜像来源 ${b.peer_row_id}`);
 }else if(s.originalEffectBinding && b.pattern_id!=null){
  const eb=s.originalEffectBinding,span=eb.span;
  const original=frozen.get(eb.row_id);
  result.bindingKnown=Boolean(original && [row.id,...(row.aliasIds || [])].includes(eb.row_id) && eb.pattern_id===b.pattern_id && b.pattern_id===parentId && actualEdges.includes(b.slot) && Array.isArray(span) && span.length===2 && span[0]>=0 && span[1]>span[0] && span[1]<=original.original.length && (effect.label!=='伤害' || /ダメージ/.test(original.original.slice(...span))));
  result.bindingKind='exact_effect_span';result.evidence.push(`原效果绑定 ${eb.row_id} / ${JSON.stringify(span)} / ${b.slot}`);
 }else if(ob.g1_b1_binding){
  const unique=b.record_selection==='RECORD_UNIQUE' || b.selection?.record_note==='RECORD_UNIQUE';
  const selected=b.selection?.records;
  result.bindingKnown=Boolean(unique && Array.isArray(selected) && selected.length===1 && selected[0]===b.record_id && [row.id,...(row.aliasIds || [])].includes(b.row_id) && b.rule_key===s.rule && b.field_path===s.field && sourceRecord(a)?.skillid===b.record_id && actualEdges.length===1);
  result.bindingKind='unique_record_binding';result.evidence.push(unique?'原绑定的唯一记录与父链逐项核对':'同值但非唯一记录，不能据数值相同解除对应疑问');
 }
 const branchKey=`${a.displayBranch?.layer || s.layer || s.allSources?.layer || b.layer}:${a.displayBranch?.id ?? s.branchId ?? b.pattern_id}`;
 const selection=selectionReceipt.parents[branchKey];
 if(selection){
  assert.deepEqual(parent(a)?.raw,selection.parentRaw,'resolved selection matches actual complete parent');
  result.conditionKnown=true;result.condition=selection.selectionUnavailable?'本模式常规选档不选用':selection.conditionLabel;result.selectionResolved=true;
  result.selectionKind=selection.selectionKind;result.selectionOrder=selection.selectionOrder;result.selectionKey=branchKey;
  result.selectionUnavailable=Boolean(selection.selectionUnavailable);
  result.evidence.push(selection.reason,selection.scope,...selection.limits,`完整候选与状态枚举：${(closeout.parents[branchKey] || closeout.resolvedCohortParents?.[branchKey])?'audit/c19_closeout_20261107/condition_closeout_receipt.json':'audit/selection_order_20261107/selection_receipt.json'} parents.${branchKey}`);
 }
 const invariant=invariants.get(invariantKey(row.id,s));
 if(invariant && result.bindingKnown && result.numericKnown && !result.conditionKnown){
  assert.deepEqual(s,invariant.source,'constant branch receipt matches complete original source');
  result.branchInvariant=true;result.evidence.push(`完整charainfo父引用与当前主线页面对账；同层同名同flag全部 ${invariant.allCohortParents.join('、')} 的本项输入相同，触发选择尚未完全解释；见audit/trigger_evidence_20261107/branch_invariance_receipt.json`);
 }
 if(result.bindingKnown && result.numericKnown && (result.conditionKnown || result.branchInvariant)){result.status='inferred';result.shortReason='';result.evidence.push('本次仅解除本项数值疑问；沿用推断等级，未做实机验证');}
 else if(result.bindingKnown && result.numericKnown){result.shortReason='条件待确认';}
 else if(!result.numericKnown){result.shortReason='数值来源待复核';}
 else if(!result.conditionKnown){result.shortReason='条件及效果对应待确认';}
 if(s.rule==='bossskill|64|/skillparam1' && !result.bindingKnown)result.shortReason='回复数值与本效果对应待确认';
 const exactPartial=partials.get(invariantKey(row.id,s));
 const partial=exactPartial || partialParents.get(`${a.displayBranch?.layer || s.layer || s.allSources?.layer || b.layer}:${a.displayBranch?.id ?? s.branchId ?? b.pattern_id}`);
 if(partial && result.status==='purple' && !result.selectionResolved){
  if(exactPartial)assert.deepEqual(s,partial.source,'partial condition matches complete original source');
  assert.deepEqual(parent(a)?.raw,partial.parentRaw,'partial condition matches actual parent');
  result.partialCondition=partial.partialCondition;result.shortReason='分支选取待确认';
  result.evidence.push(...partial.evidence.map(e=>`${e.file} ${e.rva || JSON.stringify(e.pointers || e.pointer || e.lines)}：${e.fact}`),...partial.limits);
 }
 const random=randomParents.get(branchKey);
 if(random && result.status==='purple'){
  assert.deepEqual(parent(a)?.raw,random.parentRaw,'random pool matches complete actual parent');
  result.randomPoolKnown=true;result.cardFaceMappingKnown=false;result.shortReason='具体卡面对应待确认';
  result.evidence.push('普通随机池为30027800/01/02三个等权分支；30027803为满超必杀槽模式，不能混入普通池。','这里只确认每次选档的区间，不代表实际点击频率；sp_komodia01/02/03尚未绑定实际卡面，不能按后缀命名。','完整候选、动画入口和DOWN缺口见audit/final5_evidence_20261107/random_pool_receipt.json');
 }
 const screened=closeoutItems.get(closeoutKey(row.id,effect.label,a.text,s));
 if(screened){
  assert.deepEqual(s,screened.source,'condition screen matches the complete candidate source');
  result.conditionScreened=true;
  if(screened.conditionGap){
   result.conditionGap=screened.conditionGap;
   result.evidence.push(`本轮完整父集合核查缺口：${screened.conditionGap}`);
   if(!result.conditionKnown && result.bindingKnown && result.shortReason==='条件待确认'){
    result.shortReason=/位置|形态/.test(screened.conditionGap)?'位置或形态条件待确认':/法珠/.test(screened.conditionGap)?'法珠选档待确认':/flag|模式/.test(screened.conditionGap)?'技能状态条件待确认':'分支选取待确认';
   }
  }
 }
 return result;
}
for(const file of fs.readdirSync(path.join(out,'data/cards')).filter(f=>f.endsWith('.js'))){
 const filename=path.join(out,'data/cards',file),bytes=fs.readFileSync(filename);
 frozenHashes[file]=sha(bytes);
 const card=JSON.parse(bytes.toString('utf8').split(']=')[1].trim().replace(/;$/,''));stats.cards++;
 const frozen=new Map(card.groups.flatMap(g=>g.skills.flatMap(s=>s.rows.map(r=>[r.id,r]))));
 const groups=inline.mergeGroups(branches.apply(card,overlay[card.cid]).groups);
 for(const group of groups)for(const rawSkill of group.skills){
  const skill=inline.prepareSkill(rawSkill,parents);
  for(const row of skill.rows)for(const effect of row.effects)for(const answer of effect.answers){
   if(!inline.candidate(answer))continue;
   const review=assess(answer,row,effect,frozen,skill);records[inline.reviewKey(row,effect,answer)]=review;
   stats.reviewed++;stats[review.status==='inferred'?'inferred':'purple']++;
   stats.reasons[review.shortReason || '已解除分支疑问']=(stats.reasons[review.shortReason || '已解除分支疑问']||0)+1;
   stats.bindingKinds[review.bindingKind]=(stats.bindingKinds[review.bindingKind]||0)+1;
   items.push({cid:card.cid,rowId:row.id,effect:effect.label,text:answer.text,source:answer.source,review});
  }
 }
}
assert.equal(stats.cards,2236);
for(const [file,digest] of Object.entries(frozenHashes))assert.equal(sha(fs.readFileSync(path.join(out,'data/cards',file))),digest,'frozen reader stayed unchanged throughout audit');
for(const [file,digest] of Object.entries(sourceHashes))assert.equal(sha(fs.readFileSync(sourcePath(file))),digest,'decoded source stayed unchanged throughout audit');
const report={stats,scope:'Display assessment only; inferred never becomes confirmed. Frozen data, candidate overlay and mainline statistics unchanged.',sourceHashes,frozenHashes,items};
const audit=stageAudit||freshReviewDirectory('confidence');
fs.mkdirSync(audit,{recursive:true});
fs.writeFileSync(path.join(audit,'inventory.json'),JSON.stringify(report,null,2),{flag:'wx'});
const priorFile=path.join(out,closeout.items.length?'audit/final5_evidence_20261107/inventory.json':'audit/selection_order_20261107/inventory.json');
if(fs.existsSync(priorFile)){
 const prior=read(priorFile),key=i=>JSON.stringify([i.rowId,i.effect,i.source.layer,i.source.branchId,i.source.recordId,i.source.rule,i.source.field,i.source.raw,i.text]);
 const old=new Map(prior.items.map(i=>[key(i),i]));
 const state=r=>[r.status,r.bindingKnown,r.conditionKnown,r.partialCondition,r.shortReason];
 const changes=items.flatMap(i=>{const before=old.get(key(i));return before && JSON.stringify(state(before.review))!==JSON.stringify(state(i.review))?[{cid:i.cid,rowId:i.rowId,text:i.text,source:i.source,before:before.review,after:i.review}]:[];});
 fs.writeFileSync(path.join(audit,'changes.json'),JSON.stringify({previousSHA256:sha(fs.readFileSync(priorFile)),previous:prior.stats,current:stats,changes},null,2),{flag:'wx'});
}
const inputHashes=Object.fromEntries(['branch_candidates','branch_conditions','mana_costs'].map(n=>[n,sha(fs.readFileSync(path.join(out,`data/${n}.js`)))]));
const assessments=stageSidecar||path.join(audit,'branch_assessments.js');
const content='window.CC_BRANCH_ASSESSMENTS='+JSON.stringify({records,resolvedParents:{...selectionReceipt.parents,...closeout.resolvedCohortParents},inputHashes,stats,scope:report.scope}).replace(/<\//g,'<\\/')+';\n';
if(replace&&fs.existsSync(assessments)){
 requireDirect(assessments);
 const stat=fs.lstatSync(assessments);
 if(!stat.isFile()||stat.nlink!==1)throw new Error('Stage sidecar is not an unshared file: '+assessments);
 const candidate=assessments+'.'+crypto.randomUUID()+'.tmp';
 fs.writeFileSync(candidate,content,{flag:'wx'});
 fs.renameSync(candidate,assessments);
}else{
 fs.writeFileSync(assessments,content,{flag:'wx'});
}
console.log(JSON.stringify(stats,null,2));
