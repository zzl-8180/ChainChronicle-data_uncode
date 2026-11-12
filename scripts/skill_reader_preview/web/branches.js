/* Display overlay only. Frozen ledger rows and catalog totals remain unchanged. */
(function (root) {
  'use strict';
  const clone = value => JSON.parse(JSON.stringify(value));
  function apply(card, entry) {
    if (!card || !entry) return card;
    return {...card, unmappedBranches:clone(entry.unmappedBranches || []), groups:(card.groups || []).map(group=>({...group, skills:(group.skills || []).map(skill=>({...skill, rows:(skill.rows || []).map(row=>{
      const patch = entry.rows?.[row.id];
      if (!patch) return row;
      const result = clone(row);
      for (const addition of patch.additions || []) {
        const effect = (result.effects || []).find(effect=>effect.id === addition.effectId);
        if (!effect) continue;
        effect.sourceStatus = effect.sourceStatus || effect.status;
        effect.answers = [...(effect.answers || []), {...clone(addition.answer), branchCandidate:true, candidateLabel:addition.answer.candidateLabel || '强化候选'}];
        effect.status = 'has_answer';
      }
      result.knownCandidateScopes = clone(patch.knownCandidateScopes || []);
      result.candidateStatusText = patch.candidateStatusText || '';
      result.candidateLinks = clone(patch.candidateLinks || []);
      result.unmappedBranches = clone(patch.unmappedBranches || []);
      return result;
    })}))}))};
  }
  const api = {apply};
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.CC_BRANCHES = api;
})(typeof window === 'object' ? window : globalThis);
