"""Small file-set backup/rollback for a card rebuild; not an OS-crash transaction."""
import json
import os
import shutil

from card_page import dump
from card_page_cohorts import sha

ARTIFACTS=('card.json','index.html','receipt.json')
BLOCKER='reuse_blocked.json'


def state(folder):
    return {name:sha(folder/name) if (folder/name).is_file() else None for name in ARTIFACTS}


def retention(folder,before):
    after=state(folder);affected=[str(folder/name) for name in ARTIFACTS if before[name]!=after[name]]
    return dict(previous_artifacts_retained=all(before.values()) and not affected,
                previous_state_restored=not affected,previous_files=before,current_files=after,affected_paths=affected)


class ArtifactWriteError(RuntimeError):
    def __init__(self,error,detail):super().__init__(str(error));self.detail=detail


def reusable(folder,signature):
    if (folder/BLOCKER).exists():return False
    try:
        prior=json.loads((folder/'receipt.json').read_text(encoding='utf-8'))
        return (prior.get('status')=='SUCCESS' and prior.get('signature')==signature
                and set(prior.get('files',{}))=={'card.json','index.html'}
                and all((folder/name).is_file() and sha(folder/name)==digest for name,digest in prior['files'].items()))
    except (OSError,ValueError,TypeError):return False


def commit(folder,stage,backup,new_receipt):
    folder.mkdir(parents=True,exist_ok=True);backup.mkdir(parents=True,exist_ok=False)
    before=state(folder);blocked_before=(folder/BLOCKER).is_file();mutated=False
    try:
        for name in ARTIFACTS:
            if before[name] is not None:shutil.copy2(folder/name,backup/name)
        if blocked_before:shutil.copy2(folder/BLOCKER,backup/BLOCKER)
        dump(backup/'before.json',before)
        # Prevent SUCCESS reuse while the file set is being replaced.
        mutated=True;dump(folder/BLOCKER,dict(status='UPDATING',backup=str(backup)))
        dump(folder/'receipt.json',dict(status='UPDATING',signature=new_receipt['signature']))
        for name in ('card.json','index.html'):os.replace(stage/name,folder/name)
        dump(folder/'receipt.json',{**new_receipt,'status':'SUCCESS','files':{name:sha(folder/name) for name in ('card.json','index.html')}})
        (folder/BLOCKER).unlink()
    except Exception as error:
        rollback_errors=[]
        if mutated:
            for name in ARTIFACTS:
                try:
                    if before[name] is None:(folder/name).unlink(missing_ok=True)
                    else:shutil.copy2(backup/name,folder/name)
                except Exception as rollback_error:rollback_errors.append(dict(path=str(folder/name),error=str(rollback_error)))
        detail=retention(folder,before);detail['rollback_errors']=rollback_errors
        if detail['previous_state_restored'] and not rollback_errors:
            try:
                if blocked_before:shutil.copy2(backup/BLOCKER,folder/BLOCKER)
                else:(folder/BLOCKER).unlink(missing_ok=True)
            except Exception as rollback_error:
                rollback_errors.append(dict(path=str(folder/BLOCKER),error=str(rollback_error)))
        if rollback_errors or not detail['previous_state_restored']:
            # The blocker is checked independently of any old SUCCESS receipt.
            dump(folder/BLOCKER,dict(status='PARTIAL_REPLACEMENT_REUSE_FORBIDDEN',**detail))
            dump(folder/'receipt.json',dict(status='INVALID_PARTIAL_REPLACEMENT',signature=new_receipt['signature'],affected_paths=detail['affected_paths']))
            detail=retention(folder,before)|dict(rollback_errors=rollback_errors,reuse_forbidden=True)
        else:detail['reuse_forbidden']=blocked_before
        raise ArtifactWriteError(error,detail) from error
