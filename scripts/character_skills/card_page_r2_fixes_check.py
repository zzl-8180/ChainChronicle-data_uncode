"""Only F1–F5 targeted checks with authorized pilot cards and controlled IO faults."""
import argparse
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import card_page_batch as B
import card_page_write as W
from card_page import dump
from card_page_data import Inputs,SAMPLES,build_card
from card_page_dependencies import data_paths


def rows(card):return [r for g in card['groups'] for s in g['skills'] for r in s['rows']]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.input_root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);checks=[];observed=set()
    def ck(name,condition,**details):
        assert condition,(name,details)
        checks.append(dict(name=name,passed=True,**details))
    original_open=Path.open
    def record_open(path,*args,**kwargs):
        mode=args[0] if args else kwargs.get('mode','r')
        if 'r' in mode:observed.add(path.resolve())
        return original_open(path,*args,**kwargs)
    with patch.object(Path,'open',record_open):
        data=Inputs(root,SAMPLES);cards={cid:build_card(data,cid) for cid in SAMPLES}
    declared={p.resolve() for p in data_paths(root)}
    data_reads={p for p in observed if p.is_relative_to(root/'output')}
    ck('F2_actual_pilot_data_read_closure',data_reads<=declared,observed=[p.relative_to(root).as_posix() for p in sorted(data_reads)],undeclared=[str(p) for p in data_reads-declared])
    nested=[root/'output/cache_full_20261015_v3/decoded'/f'{s}.data5.json.raw' for s in ('extraabilitylist','passivelist','denju_lblist')]
    ck('F2_all_three_nested_sources_observed_and_declared',all(p in observed and p in declared for p in nested))
    def duplicate(cid,modify=None):
        original=copy.deepcopy(data.links[cid]);g=next(g for g in data.links[cid]['groups'] if g['group']=='ability')
        alias=copy.deepcopy(g['records'][0])
        if modify:modify(alias)
        g['records'].insert(0,alias)
        try:return build_card(data,cid)
        finally:data.links[cid]=original
    alias=duplicate(29)
    ck('F4_real_build_cid29_same_reference_alias_merged',alias['coverage']['N_all']==2 and alias['coverage']['same_position_aliases_merged']==1,
       rows=[dict(row_id=r['row_id'],aliases=r['alias_references']) for r in rows(alias)])
    alias30236=duplicate(30236)
    keys=('row_id','japanese','answers','evidence','level','reference_field','stage')
    ck('F4_inserted_alias_does_not_shift_later_rows_or_old_bindings',
       [{k:r[k] for k in keys} for r in rows(cards[30236])]==[{k:r[k] for k in keys} for r in rows(alias30236)])
    for label,change in [('different_slot',lambda e:e.update(reference_field='skillid[2]')),
                         ('different_parent_condition',lambda e:e['record'].update(limit_break=1)),
                         ('different_actual_level',lambda e:e['record'].update(lv=2))]:
        different=duplicate(29,change)
        ck('F4_'+label+'_not_merged',different['coverage']['N_all']==3 and different['coverage']['same_position_aliases_merged']==0)
    speed=next(f for f in cards[7229]['basic']['fields'] if f['key']=='atkspeed')
    ck('F5_raw_confirmed_units_inferred_and_manual_s0_limit_visible',speed['raw_value']==2 and speed['display_value']=='2.0秒/下'
       and speed['raw_value_evidence']=='确认' and speed['unit_evidence'].startswith('推断') and '手工s0' in speed['note'] and '未全证charainfo→BattleParam' in speed['note'])
    manifest=root/'output/character_skills/r2_preparation/cohorts/manifest.json';batch=out/'batch'
    def run(cohort,cid,resume=False):return B.run(SimpleNamespace(input_root=root,manifest=manifest,cohort=cohort,cid=[cid],execute=True,resume=resume,output=batch))
    def report(result):return json.loads((batch/result['report']).read_text(encoding='utf-8'))
    # Reuse one already-loaded declared input set; all actual builds remain authorized pilots.
    with patch.object(B,'Inputs',lambda *_:data):
        first=run('ge60',7229);first_files={p:B.sha(p) for p in (batch/first['report']).parent.glob('*.json')}
        second=run('40to59',30236);latest=json.loads((batch/'_batch/campaign_latest.json').read_text(encoding='utf-8'))
        queue=json.loads((batch/latest['audit_queue']).read_text(encoding='utf-8'))
        ck('F1_sequential_cohorts_keep_histories_and_both_queues',all(B.sha(p)==h for p,h in first_files.items()) and {r['cid'] for r in queue}=={7229,30236})
        third=run('ge60',30004);current=report(third)
        ck('F1_same_cohort_subset_retains_previous_success_and_debt',current['completed']==2 and current['expected']==34 and not current['cohort_complete']
           and current['requested']==1 and current['subset'] and current['unreviewed_cards']==2)
        resumed=run('ge60',7229,True);ck('F1_resume_preserves_full_cohort_inventory',resumed['reused']==1 and resumed['completed']==2)
        # Signature changes are injected at hashing only. Never edit the original inputs.
        original_sha=B.sha
        for index,path in enumerate(nested):
            def changed_sha(candidate,target=path,digit=str(index+1)):
                return digit*64 if candidate==target else original_sha(candidate)
            with patch.object(B,'sha',changed_sha):changed=run('ge60',7229,True)
            changed_report=report(changed)
            ck('F2_signature_invalidation_'+path.stem,changed['reused']==0 and 30004 in changed_report['stale_or_invalid_cids'] and changed_report['completed']==1)
        # Return to the real signature, then inject the second artifact replacement.
        restored=run('ge60',7229);before=W.state(batch/'7229');original_build=B.build_card;original_replace=W.os.replace
        def modified_build(*args):
            card=original_build(*args);card['fault_probe']='new payload for rollback proof';return card
        def fail_html(source,target):
            if Path(target)==batch/'7229/index.html':raise OSError('injected second artifact replace failure')
            return original_replace(source,target)
        with patch.object(B,'build_card',modified_build),patch.object(W.os,'replace',fail_html):failed=run('ge60',7229)
        failure=report(failed)['failed'][0]
        ck('F3_second_replace_failure_restores_card_html_receipt',W.state(batch/'7229')==before and failure['previous_artifacts_retained'] and failure['previous_state_restored'] and not failure['affected_paths'])
        ck('F1_failed_rebuild_keeps_prior_success_and_review_queue',report(failed)['completed']==2 and report(failed)['unreviewed_cards']==2)
        other_subset=run('ge60',30004,True)
        ck('F1_other_subset_does_not_erase_prior_unresolved_failure',not report(other_subset)['failed'] and [f['cid'] for f in report(other_subset)['unresolved_latest_failures']]==[7229])
        real_copy=W.shutil.copy2
        def fail_rollback(source,target,*args,**kwargs):
            if Path(source).parent.name=='backup' and Path(target)==batch/'7229/card.json':raise OSError('injected card rollback failure')
            return real_copy(source,target,*args,**kwargs)
        with patch.object(B,'build_card',modified_build),patch.object(W.os,'replace',fail_html),patch.object(W.shutil,'copy2',fail_rollback):partial=run('ge60',7229)
        partial_failure=report(partial)['failed'][0]
        ck('F3_rollback_failure_reports_paths_and_blocks_success_reuse',not partial_failure['previous_artifacts_retained'] and partial_failure['reuse_forbidden']
           and str(batch/'7229/card.json') in partial_failure['affected_paths'] and (batch/'7229/reuse_blocked.json').is_file()
           and not W.reusable(batch/'7229',report(partial)['signature']) and 7229 in report(partial)['stale_or_invalid_cids'])
        repaired=run('ge60',7229,True)
        ck('F3_next_resume_rebuilds_blocked_set_and_recovers',repaired['reused']==0 and not (batch/'7229/reuse_blocked.json').exists() and repaired['completed']==2)
    dump(out/'checks.json',dict(status='IMPLEMENTATION_TARGETED_SELF_CHECK_NOT_INDEPENDENT_R2',checks=checks,passed=len(checks),
         authorized_cids_built=[29,30236,7229,30004],full_cohort_executed=False,raw_inputs_modified=False,
         limitations=['No OS power-loss/concurrent-reader transaction guarantee','Audit queues remain NOT_REVIEWED; no completed human review inferred']))
    print(json.dumps(dict(passed=len(checks),checks=str(out/'checks.json'))))


if __name__=='__main__':main()
