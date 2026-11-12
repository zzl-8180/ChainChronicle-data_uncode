/* A missing historical row binding is not negative evidence. These narrow
 * structural checks independently join actual executors to original prose. */
const assert=require('node:assert/strict');
const shapes={3:/前方範囲内.*ダメージを与え/,55:/直線範囲上.*ダメージを与え/,
 110:/前方範囲内.*\d+回ダメージを与え/,112:/ダメージを与え.*(?:設置|攻撃範囲)/};
function executors(raw,boss){
 return Object.entries(raw).filter(([k,v])=>/^skillid\d+$/.test(k) && v!==0)
  .map(([slot,id])=>({slot,record:boss.find(r=>r.skillid===id)}));
}
function evaluate({source:s,row,effect,base,alt,boss,baseRecord,rule,nativeType,supportRecords,supportRules,intervalProof}){
 const type=Number(s.rule?.split('|')[1]),shape=shapes[type];
 if(!shape || s.field!=='/skillparam1' || effect.label!=='伤害' || !rule?.status?.startsWith('已确认') || !/伤害|攻击/.test(rule.meaning_zh))return null;
 const rejection={bindingKnown:false,bindingKind:'semantic_fallback',evidence:[]};
 const reject=why=>({...rejection,evidence:[why]});
 if(!base || !alt || !baseRecord || base.patternid!==s.baseBranchId || alt.patternid!==s.branchId)return reject('父记录身份未完整核实');
 const before=executors(base,boss),after=executors(alt,boss);
 if([...before,...after].some(e=>!e.record))return reject('完整执行链含未定位记录，不能排除其他伤害载体');
 const first=before.filter(e=>e.record.skillid0===type),last=after.filter(e=>e.record.skillid0===type);
 if(first.length!==1 || last.length!==1)return reject('实际执行链存在多个同类伤害载体，效果对应待核');
 if(first[0].slot!==s.parentSlot || last[0].slot!==s.parentSlot || first[0].record.skillid!==baseRecord.skillid || last[0].record.skillid!==s.recordId || baseRecord.skillparam1!==s.donorRaw || last[0].record.skillparam1!==s.raw)return reject('原始父槽与伤害字段身份不一致');
 if(!Number.isFinite(s.raw) || s.raw<=0 || (base.flag??0)!==(alt.flag??0) || (base.sname||'')!==(alt.sname||''))return reject('父类别或数值范围未核实');
 const sentences=(base.sinfo || '').split('。').filter(Boolean),matches=sentences.filter(t=>shape.test(t));
 if(matches.length!==1 || !row.original.includes(matches[0]) || effect.answers.length===0)return reject('原文存在多个或未找到对应形状的伤害句');
 if(type===110 && Number(row.original.match(/(\d+)回ダメージ/)?.[1])!==baseRecord.skillparam6)return reject('原文连击次数与载体不一致');
 const ownHp=type===3 && row.original==='【共鳴必殺/連撃】自身と前方範囲内の全ての敵にダメージを与える。'
  && sentences[1]==='ダメージ量は自身の残りHP量に応じて変化する'
  && /^その後、一定間隔.*ランダム.*周囲に小ダメージ/.test(sentences[2] || '')
  && [before,after].every(chain=>JSON.stringify(chain.map(e=>[e.slot,e.record.skillid0]))===JSON.stringify([['skillid0',3],['skillid1',116],['skillid2',13]]));
 if(!ownHp && [before,after].some(chain=>chain.some(e=>![type,13].includes(e.record.skillid0))))return reject('完整执行链含其他攻击或未解释类型，仍需区分效果归属');
 if(!ownHp && /自身と|反響|受けたダメージ/.test(row.original))return reject('原句含自损或其他伤害机制，不能用唯一主载体覆盖');
 const allowed=new Set(['skillid','skillparam1','name','sname','spmotname']);
 // A separately proven attached enemy debuff may vary without relabeling the
 // main damage input. Unknown attached abilities are deliberately not ignored.
 const attachedBefore=supportRecords?.find(r=>r.skillid===baseRecord.s_ability);
 const attachedAfter=supportRecords?.find(r=>r.skillid===last[0].record.s_ability);
 const debuffFields=['param7','param8','param9'];
 const debuffCompatible=attachedBefore && attachedAfter && [attachedBefore,attachedAfter].every(r=>r.ability===2003 && r.param3===1 && (!r.sub || Array.isArray(r.sub) && r.sub.length===0))
  && debuffFields.every(k=>supportRules?.[`skilllist|2003|/${k}`]?.status?.startsWith('已确认'))
  && [...new Set([...Object.keys(attachedBefore),...Object.keys(attachedAfter)])].every(k=>['skillid','name',...debuffFields].includes(k) || k==='text' && attachedBefore.text===attachedBefore.name && attachedAfter.text===attachedAfter.name || JSON.stringify(attachedBefore[k])===JSON.stringify(attachedAfter[k]));
 if(debuffCompatible)allowed.add('s_ability');
 if(ownHp)allowed.add('s_ability');
 const changed=[...new Set([...Object.keys(baseRecord),...Object.keys(last[0].record)])].filter(k=>!allowed.has(k) && JSON.stringify(baseRecord[k])!==JSON.stringify(last[0].record[k]));
 if(changed.length)return reject(`对象、形状或其他字段变化仍待核：${changed.join('、')}`);
 if(ownHp){
  assert.equal(nativeType?.handler,'bhSkill.Exec_ATTACK_AREA');
  assert.equal(nativeType?.slots?.atk_rate?.slot,1);
  assert.equal(intervalProof?.type,116);assert.equal(intervalProof?.enum,'SKILL_TYPE.INTERVAL_FALL2');
  assert.equal(intervalProof?.entry,116);assert.equal(intervalProof?.method?.name,'Exec_INTERVAL_FALL2');
  assert.equal(intervalProof?.method?.declaring_type,'bhSkillUtil');assert.equal(intervalProof?.method?.native_rva,'0x119d924');
  if(before[1].record.skillid!==after[1].record.skillid || before[2].record.skillid!==after[2].record.skillid)return reject('后续执行载体变化，需单独复核');
 }
 return {bindingKnown:true,bindingKind:ownHp?'hp_first_enemy_area':'single_damage_executor',
  ...(ownHp?{valuePrefix:'对敌系数',unresolvedScope:'自身受到的伤害数值尚未解出'}:{}),
  evidence:[`完整原表执行链 ${before.map(e=>`${e.slot}:type${e.record.skillid0}`).join('、')}；候选父槽 ${s.parentSlot} → ${s.recordId} / ${s.field}`,
   `主线规则 ${s.rule} 的已核单次伤害输入；唯一匹配原句：${row.original}`,
   ownHp?'首次对敌范围伤害与后续type116周期攻击分开（output/sample/active_skill_trace.json，INTERVAL_FALL2 @0x119d924）；s_ability自损及type116伤害未解释，不套用本系数':'唯一实际伤害执行载体＋原文几何机制对应，关联为结构推断；不推算命中数、总伤害或最终扣血',
   ...(debuffCompatible && baseRecord.s_ability!==last[0].record.s_ability?['附加2003子链对象/触发/其他字段相同，仅已核param7/8/9敌减益贡献变化；不改变本次主伤害输入范围']:[])]};
}
module.exports={evaluate,executors};
