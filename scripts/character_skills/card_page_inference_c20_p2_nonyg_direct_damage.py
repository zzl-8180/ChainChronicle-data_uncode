# -*- coding: utf-8 -*-
"""C20-P2 非Y.G.条件选档直接伤害候选；未接共享生产入口。"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import card_page_inference_c20_direct_damage_common as C20

MODULE_VERSION = 'c20_p2_nonyg_direct_damage_20261108'
SCOPE = 'C20_P2_NONYG_DIRECT_DAMAGE_20261108'
BLOCKING_KEY = 'c20_p2_nonyg_direct_damage_binding'
MARKER_KEY = 'inference_c20_p2_nonyg_direct_damage'
OUT_DIR_REL = 'output/character_skills/c20_p2_nonyg_direct_damage_20261108'
MODULE_REL = 'scripts/character_skills/card_page_inference_c20_p2_nonyg_direct_damage.py'
ScopeError = C20.ScopeError


def target(cid, pattern_index, fragment, layer, model):
    row_id = '%d-special_move-special_move-pattern%d-lvorder%d-f%d' % (
        cid, pattern_index, pattern_index, fragment)
    reference = 'pattern%d' % pattern_index
    return {'cid': cid, 'row_id': row_id, 'effect_id': row_id + '#e00',
            'layer': layer, 'reference_field': reference, 'model': model}


TARGETS = (
    target(20332, 0, 0, 'APK', 'HP_CHAIN'),
    target(12236, 1, 0, 'CACHE', 'USE_ONCE_NORMAL'),
    target(12236, 3, 0, 'CACHE', 'CURRENT_SUPER_UI'),
    target(5300, 1, 0, 'CACHE', 'TERRAIN_SHARED'),
    target(7654, 0, 0, 'APK', 'JOB_AFTER_COST'),
    target(12032, 0, 0, 'APK', 'SCRAP_BASE_SAME_VALUE'),
    target(12226, 0, 0, 'APK', 'SCRAP_TWO_TIER'),
    target(20619, 0, 0, 'CACHE', 'SCRAP_TWO_TIER'),
)
SPEC = C20.BatchSpec(scope=SCOPE, module_version=MODULE_VERSION,
                     binding_key=BLOCKING_KEY, marker_key=MARKER_KEY,
                     module_file=MODULE_REL, out_dir=OUT_DIR_REL, targets=TARGETS)
TARGET_CIDS = frozenset(C20.target_cids(SPEC))
TARGET_ROW_IDS = {cid: frozenset(t['row_id'] for t in TARGETS if t['cid'] == cid)
                  for cid in sorted(TARGET_CIDS)}
NEGATIVE_CIDS = SPEC.negative_cids
PROTECTED_CIDS = SPEC.protected_cids


def evaluate(data, cid, row, *, scope=None, skill=None):
    return C20.evaluate(data, cid, row, scope=scope, skill=skill, spec=SPEC)


def apply_to_groups(data, cid, groups, *, scope=None):
    return C20.apply_to_groups(data, cid, groups, scope=scope, spec=SPEC)


def build_candidates(root):
    return C20.build_candidates(root, SPEC)


def write_outputs(root):
    return C20.write_outputs(root, SPEC)


def main(argv=None):
    return C20.main(SPEC, argv)


if __name__ == '__main__':
    raise SystemExit(main())
