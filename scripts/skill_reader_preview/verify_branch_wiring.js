/* Reverse checks over resolved parents and selection-resolved answers. No data writes. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const args=process.argv.slice(2),arg=(key,fallback)=>args.includes(key)?args[args.indexOf(key)+1]:fallback;
const report=arg('--report');
if(report&&fs.lstatSync(path.resolve(report),{throwIfNoEntry:false}))throw new Error('Choose a new validation receipt: '+report);
const out=path.resolve(arg('--output','output/character_skills/reader_full_20261106'));
const web=path.resolve(arg('--web-root',out));
const inline=require(path.join(web,'inline.js')),branches=require(path.join(web,'branches.js')),levels=require(path.join(web,'levels.js'));
const load=relative=>{const context={window:{}};vm.runInNewContext(fs.readFileSync(path.join(out,relative),'utf8'),context);return JSON.parse(JSON.stringify(context.window));};
const candidates=load('data/branch_candidates.js').CC_BRANCH_CANDIDATES,conditions=load('data/branch_conditions.js').CC_BRANCH_CONDITIONS,assessments=load('data/branch_assessments.js').CC_BRANCH_ASSESSMENTS;
const receipt=JSON.parse(fs.readFileSync(path.resolve(arg('--receipt',path.join(out,'audit/c19_closeout_20261107/condition_closeout_receipt.json'))),'utf8'));
const slots=raw=>Object.fromEntries(Object.entries(raw).filter(([key])=>/^skillid\d+$/.test(key)).sort(([a],[b])=>a.localeCompare(b)));
const strip=answer=>Object.fromEntries(Object.entries(answer).filter(([key])=>!['displayBranch','displayBranches','displayAssessment'].includes(key)));
const files=fs.readdirSync(path.join(out,'data/cards')).filter(file=>/^\d+\.js$/.test(file));
const used=new Set(),targets={},missing=[],aliases=[],selectionTargets=[];
let checks=0,selectionResolved=0,sourceAnswers=0;
function equal(actual,expected,message){assert.deepEqual(actual,expected,message);checks++;}
for(const file of files){
  const cid=String(parseInt(file)),card=load(`data/cards/${cid}.js`).CC_DETAILS[cid],overlaid=branches.apply(card,candidates.cards[cid]);
  for(const group of inline.orderGroups(inline.mergeGroups(overlaid.groups)))for(const skill of levels.groupSkills(group)){
    const prepared=inline.prepareSkill(skill,conditions.records,assessments.records,assessments.resolvedParents);
    equal(prepared.rows.flatMap(r=>r.effects.flatMap(e=>e.answers.map(strip))),skill.rows.flatMap(r=>r.effects.flatMap(e=>e.answers.map(strip))),`${cid}: presentation preserves every source answer`);
    sourceAnswers+=skill.rows.flatMap(r=>r.effects.flatMap(e=>e.answers)).length;
    for(const branch of prepared.branchTable || []){
      used.add(branch.key);
      if(branch.displayAliasOf){
        const donor=prepared.branchTable.find(item=>item.key===branch.displayAliasOf);
        equal(slots(branch.raw),slots(donor.raw),`${branch.key}: complete executor identities match`);
        equal(assessments.resolvedParents[branch.key].cohortKey,assessments.resolvedParents[donor.key].cohortKey,`${branch.key}: exact cohort`);
        equal(branch.values.map(({displayAliasOf,...value})=>value),donor.values,`${branch.key}: alias copies bound values only`);
        aliases.push({key:branch.key,donor:donor.key,values:branch.values.length});
      }
    }
    for(const row of prepared.rows)for(const effect of row.effects)for(const answer of effect.answers){
      if(!answer.displayAssessment?.selectionResolved)continue;
      selectionResolved++;
      if(!answer.displayBranch){missing.push({cid,rowId:row.id,effect:effect.label});continue;}
      equal(answer.displayBranch.key,answer.displayAssessment.selectionKey,`${row.id}: explicit assessment parent`);
      equal(answer.displayBranch.raw,assessments.resolvedParents[answer.displayAssessment.selectionKey].parentRaw,`${row.id}: complete parent raw`);
      equal(answer.displayBranch.conditionLabel,answer.displayAssessment.condition,`${row.id}: visible condition`);
      if([353,30236,30257,30310].includes(Number(cid)))selectionTargets.push({cid,rowId:row.id,effect:effect.label,text:answer.text,condition:answer.displayBranch.conditionLabel,status:answer.displayAssessment.status});
    }
    if(cid==='30207'&&prepared.branchTable?.some(item=>item.key==='CACHE:43020700')){
      targets.cid30207={branches:prepared.branchTable.map(b=>({key:b.key,condition:b.conditionLabel,values:b.values})),rows:prepared.rows.map(row=>({id:row.id,inserts:inline.plan(row).inserts.map(item=>({label:item.effect.label,segments:item.segments?.map(s=>({text:s.text,conditions:s.conditionLabel,keys:s.branches.map(b=>b.key)}))}))}))};
      for(const id of [43020701,43020702,43020703]){
        const b=prepared.branchTable.find(item=>item.key===`CACHE:${id}`);
        assert(b,`${id}: real parent must be visible`);checks++;
        equal(b.values.map(value=>value.label),['伤害','攻击力','防御','移动速度','暴击率','暴击威力','持续时间'],`${id}: damage and all six buff-row values must be visible`);
        assert(b.values.some(value=>value.label==='伤害'&&value.text==='系数 15倍'));checks++;
      }
      const damage=inline.plan(prepared.rows[0]).inserts.find(item=>item.effect.label==='伤害').segments.find(segment=>segment.text.includes('15倍')&&!segment.text.includes('17.5'));
      equal(damage.branches.map(b=>b.key).sort(),[43020700,43020701,43020702,43020703].map(id=>`CACHE:${id}`).sort(),'15x shows all four true parent conditions');
    }
    if(['10210','20332'].includes(cid)&&group.id==='denju'){
      for(const row of prepared.rows)for(const effect of row.effects){
        const ordered=inline.orderedAnswers(effect.answers),hp=ordered.map(a=>a.condition.match(/^HP (\d+)–(\d+)%$/));
        if(hp.length&&hp.every(Boolean)){
          equal(hp.map(m=>Number(m[1])),hp.map(m=>Number(m[1])).sort((a,b)=>b-a),`${cid}: HP order`);
          equal(ordered.length,effect.answers.length,`${cid}: equal values in distinct HP conditions retained`);
          (targets.denju ||= []).push({cid,label:effect.label,values:ordered.map(a=>({text:a.text,condition:a.condition}))});
        }
      }
    }
  }
}
equal(missing,[],'all selection-resolved answers have a display branch');
equal(Object.keys(receipt.resolvedCohortParents).filter(key=>!used.has(key)),[],'every resolved cohort parent participates in a display table');
equal(selectionResolved,883,'selection-resolved denominator is unchanged');
equal(Object.keys(assessments.records).length,2222,'assessment denominator is unchanged');
const result={status:'PASS',checks,cards:files.length,sourceAnswers,assessments:2222,selectionResolved,resolvedCohortParents:Object.keys(receipt.resolvedCohortParents).length,missing,aliases,selectionTargets,targets};
if(report)fs.writeFileSync(path.resolve(report),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:result.status,checks,cards:result.cards,selectionResolved,resolvedCohortParents:result.resolvedCohortParents,aliases,report}));
