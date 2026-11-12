# -*- coding: utf-8 -*-
"""C20-P1 Y.G. pattern来源行直接伤害候选；未接共享生产入口。"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import card_page_inference_c20_direct_damage_common as C20

MODULE_VERSION = 'c20_p1_yg_direct_damage_20261108'
SCOPE = 'C20_P1_YG_DIRECT_DAMAGE_20261108'
BLOCKING_KEY = 'c20_p1_yg_direct_damage_binding'
MARKER_KEY = 'inference_c20_p1_yg_direct_damage'
OUT_DIR_REL = 'output/character_skills/c20_p1_yg_direct_damage_20261108'
MODULE_REL = 'scripts/character_skills/card_page_inference_c20_p1_yg_direct_damage.py'
ScopeError = C20.ScopeError


def target(cid, fragment, model='DIRECT'):
    row_id = '%d-special_move-special_move-pattern0-lvorder0-f%d' % (cid, fragment)
    return {'cid': cid, 'row_id': row_id, 'effect_id': row_id + '#e00',
            'layer': 'CACHE', 'reference_field': 'pattern0', 'model': model}


TARGETS = (
    target(7250, 1), target(7250, 2), target(30105, 2), target(30107, 3),
    target(30220, 1), target(30223, 3), target(30225, 1), target(30301, 1),
    target(30329, 1), target(30334, 2),
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
