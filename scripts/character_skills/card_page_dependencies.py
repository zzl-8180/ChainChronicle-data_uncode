"""Bounded source/data dependency declarations for this presentation runner."""
import ast
from pathlib import Path


def source_paths(root):
    pending=list((root/'scripts/character_skills').glob('card_page*.py'))+[root/'scripts/build_char_roster.py',root/'scripts/chica_move_rules.py']
    found=set()
    while pending:
        path=pending.pop()
        if path in found or not path.is_file():continue
        found.add(path)
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.module else []
            for name in names:
                for parent in (path.parent,root/'scripts',root/'scripts/character_skills'):
                    candidate=parent/(name.replace('.', '/')+'.py')
                    if candidate.is_file():pending.append(candidate);break
    return sorted(found)


def data_paths(root):
    relative=['output/character_skills/'+p for p in ('profiles/profiles.jsonl','profiles/records.jsonl','profiles/rules.json','links/character_skills.jsonl','type1082/native_checks.json',
              'skilllist_types/field_dictionary.json','skilllist_types/filter_dictionary.json','boss_attack_types/field_dictionary.json','boss_heal_types/field_dictionary.json','remaining_five/field_dictionary.json')]
    relative+=['output/cache_full_20261015_v3/decoded/'+p+'.data5.json.raw' for p in ('charainfo','skilllist','bossinfo','jobabilityinfo','worldinfo','homelist','extraabilitylist','passivelist','denju_lblist')]
    relative+=['output/base_master/'+p for p in ('_mdSkill.json','_mdCharacter.json','_mdBossInfo.json','_mdSAbirity.json')]
    relative+=['output/card_comparison_cid30236/'+p+'.json' for p in ('description_effects','field_dictionary','verified_parameter_views','movement/trace')]
    relative+=['output/boss_heal/field_dictionary.json','output/ordinary_effects/ability7/trace.json']
    return [root/p for p in relative]
