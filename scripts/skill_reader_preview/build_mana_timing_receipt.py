"""Reproduce the mana-only static receipt. Owns mana_timing_receipt.json only.

Does not read or write selection_receipt.json/review_selection.py. Does not
change reader artifacts, decoded sources, or source cards.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'output/character_skills/reader_full_20261106/audit/selection_order_20261107/native'
OUTPUT = HERE / 'mana_timing_receipt.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_hashes = {}
    for rel, expected in [
        ('work/protection/il2cpp_loader_seed1.bin',
         '562a6975fe722d39842a3c7daa3982785c04beaf503c4fe1cc6fbbec3cd047c1'),
        ('work/protection/metadata_aei_decoded.bin',
         '07d582df6318e128424e41b93a8a6e86b238b9be14832756a780e47fb70443b1'),
    ]:
        digest = sha(ROOT / rel)
        assert digest == expected, f'Source version mismatch: {rel}'
        source_hashes[rel] = digest

    indices = [4927, 4928, 4925, 4932, 8233, 8234, 8237, 8266,
               7894, 5173, 8271, 4924, 9116, 6698, 6377, 8943,
               5174, 8166, 8179, 8174, 8187]
    method_hashes = {}
    for index in indices:
        # Our excerpts retain the declaring type in the basename. The other
        # investigator independently owns index_name.txt files in this folder.
        files = [p for p in HERE.glob(f'{index}_*.txt')
                 if p.name.split('_', 2)[1] in {
                     'bhExAttack', 'bhSkill', 'PanelManaGage', 'InterfaceManager',
                     'BtlCharaUtil', 'CharaMarker', 'CharaBehavior', 'PlayerManager',
                     'PanelCharaInfo'}]
        assert len(files) == 1, f'Method excerpt missing/ambiguous: {index}'
        method_hashes[files[0].relative_to(ROOT).as_posix()] = sha(files[0])

    facts = [
        dict(id='M1', fact='Job getter uses mask0x1df, Scrap getter mask0x20. Both count matching ManaIcon._ManasFlag entries in PanelManaGage._manaList.',
             rvas=['0x1242d7c..0x1242d80', '0x1242df0..0x1242df4', '0x1242cd8..0x1242d74'],
             methods=[8233, 8234, 8237]),
        dict(id='M2', fact='getPatternAttackList takes subMana in w5 and skill_cost in w7. With subMana true it subtracts an effective prediction cost from JOB count and clamps to0; it does not subtract from Scrap count. Cost>=3 has Boost/Tenma reduction paths.',
             rvas=['0x100a120..0x100a128', '0x100a3c8..0x100a434', '0x100ad60..0x100ad88'], methods=[4927]),
        dict(id='M3', fact='For eligible player patterns flag bit0x100 clear chooses the job-count gate; set chooses the Scrap-count gate. mns/mne are inclusive; both0 bypass.',
             rvas=['0x100a670..0x100a714'], methods=[4927]),
        dict(id='M4', fact='Ordinary PanelCharaInfo.UpdateCharaInfo calls GetExecSkillInfo with patternId out pointer sp+0x50. GetExecSkillInfo calls think_attack with bFirst=false,bAllRandom=false,bSkillCount=false,subMana=true,nextChain=true and writes selected pattern ID; UI stores this at this+0x1dc.',
             rvas=['0x146cd30..0x146cd8c', '0x13aadd8..0x13aae10', '0x146d018..0x146d024'], methods=[8179, 9116]),
        dict(id='M5', fact='Normal OnClickSpSkill consumes selected mana via ExecSpSkill, later reads cached PanelCharaInfo.GetPatternId and passes it to CharaBehavior.CreateExecSkillList.',
             rvas=['0x13a21ac', '0x13a24e4', '0x13a2868', '0x146d40c'], methods=[7894, 8266, 8166]),
        dict(id='M6', fact='CharaBehavior forwards to EXPLICIT-ID bhSkill overload RVA1296718. This finds the pattern controller by ID and increments use count. It does not rerun the selector.',
             rvas=['0x1547750', '0x129692c..0x1296964'], methods=[6377, 5174]),
        dict(id='M7', fact='AUTOMATIC bhSkill overload RVA1295878 is separate: three think_attack calls have bFirst=false,subMana=false,nextChain=false. Do not substitute this path for normal cached-ID UI execution.',
             rvas=['0x129595c..0x1295980', '0x1295a60..0x1295a84', '0x1295b14..0x1295b38'], methods=[5173]),
        dict(id='M8', fact='IsExistEnoughMana availability checks use bFirst=true,subMana=true,nextChain=true. Display selection uses bFirst=false. Availability and execution/display selection are not the same mode.',
             rvas=['0x1245678..0x124569c', '0x12456f4..0x1245718', '0x13aadd8..0x13aadfc'], methods=[8271, 9116]),
    ]
    wanted = {30765400: 7654, 30765401: 7654,
              31203200: 12032, 31203201: 12032,
              31222600: 12226, 31222601: 12226,
              42061900: 20619, 42061901: 20619}
    parents = []
    for layer, rel in [('APK', 'output/base_master/_mdBossInfo.json'),
                       ('CACHE', 'output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw')]:
        path = ROOT / rel
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        data = data.get('bossinfo', data)
        source_hashes[rel] = sha(path)
        for index, raw in enumerate(data['bosspattern']):
            pid = raw['patternid']
            if pid not in wanted:
                continue
            scrap = bool(raw.get('flag', 0) & 0x100)
            low, high = raw.get('mns', 0), raw.get('mne', 0)
            # Runtime getter defaults are disclosed separately from raw presence.
            assert (low, high) != (0, 0)
            parent = dict(cid=wanted[pid], layer=layer, patternId=pid,
                          file=rel, pointer=('/bossinfo' if layer == 'CACHE' else '') + f'/bosspattern/{index}',
                          raw=raw, counter='scrap' if scrap else 'job_after_prediction_cost',
                          runtimeRangeInclusive=[low, high],
                          counterExpression='GetCurrentScrapManaNum()' if scrap else
                          'max(0,GetCurrentJobManaNum()-effectivePredictionCost)',
                          proposedSelectorLabel=(f'选档预测时斯库拉普{low}–{high}个' if scrap else
                                                 f'选档预测扣费后职业法珠{low}–{high}颗'),
                          scope='Selector-local necessary condition; normal UI executes the cached predicted ID.')
            parents.append(parent)
    assert len(parents) == 8
    five = {31203200, 31222600, 31222601, 42061900, 30765400}
    receipt = dict(
        owner='branch_inventory_review',
        scope='Bounded static read of existing recovered APK56021 image. No game/runtime validation, new decoding or UI/mainline writes.',
        sourceHashes=source_hashes, methodExcerptHashes=method_hashes,
        generator={'file': Path(__file__).relative_to(ROOT).as_posix(), 'sha256': sha(Path(__file__))},
        facts=facts, parentLabels=parents,
        fiveInvestigatedCandidates=[p for p in parents if p['patternId'] in five],
        conclusions=[
            'UI prediction occurs before click and simulates JOB cost subtraction; Scrap prediction count is unchanged.',
            'Normal UI clicks debit mana, then execute the cached predicted pattern ID without a second selector invocation.',
            '12032,12226,20619 use Scrap intervals matching their original threshold descriptions.',
            '7654 uses predicted remaining JOB count. Pre-click>=4 is only valid under effective prediction cost1; do not universally convert it from nominal character data.',
        ],
        remainingGaps=[
            dict(topic='Prediction cache freshness', methods=['PanelCharaInfo.Update 0x146be3c', 'PanelCharaInfo.UpdateCharaInfo 0x146cc40', 'InterfaceManager.OnClickSpSkill 0x13a1dc8'],
                 requiredProof='Refresh scheduling and intervening state changes between cached prediction and click; not required to state selector-local interval semantics.'),
            dict(topic='7654 universal before-cost threshold', methods=['BattleParam.get_skillCost 0x1105f6c', 'getPatternAttackList 0x100a3e4..0x100a434/0x100ad60..0x100ad80'],
                 requiredProof='Runtime effective prediction cost, reductions, special resource behavior. Nominal sourcecost1 alone is insufficient.'),
            dict(topic='Non-UI trigger modes', methods=['bhSkill.CreateExecSkillList() 0x1295878', 'bhSkill.CreateExecSkillList(patternId,...) 0x1296718'],
                 requiredProof='Trace any non-UI caller separately; the overloads have different selection behavior.'),
        ],
        stopBoundary='One ordinary UI write/click/explicit-ID chain only. No exhaustive callback/scheduling or special-trigger review.')
    OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(OUTPUT), 'facts': len(facts),
                      'methodHashes': len(method_hashes), 'parentLabels': len(parents)}))


if __name__ == '__main__':
    main()
