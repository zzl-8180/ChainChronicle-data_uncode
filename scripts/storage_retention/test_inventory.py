"""Small inventory fixtures: disjoint totals and reference/recovery protection."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import inventory as I

ROOT = Path(__file__).resolve().parents[2]


class InventoryTests(unittest.TestCase):
    def setUp(self):
        base = ROOT/'work/storage_retention_20261023'
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='inventory-test-', dir=base)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, value):
        path = self.root/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8')
        return path

    def test_work_parent_child_totals_and_active_protection(self):
        self.write('work/closed/replay/1/card.json', 'abc')
        self.write('work/closed/replay/nested/scratch/result.txt', 'defg')
        self.write('work/closed/pages_before.json', 'baseline')
        self.write('work/closed/check.py', 'script')
        self.write('work/active/replay/1/card.json', 'abcde')
        errors = []
        units, tops = I.work_inventory(self.root, [], {'active': {'docs/tasks/active.md'}}, errors)
        self.assertFalse(errors)
        self.assertEqual(sum(r['bytes'] for r in units), sum(r['bytes'] for r in tops.values()))
        replay = next(r for r in units if r['path']=='work/closed/replay')
        self.assertEqual(replay['bytes'], 7)
        self.assertEqual(replay['action'], 'REVIEW_REPLAY')
        self.assertEqual(sum(r['reclaimable_bytes'] for r in units), 7)
        self.assertEqual(next(r for r in units if r['path']=='work/active/replay')['action'], 'KEEP')
        self.assertEqual(next(r for r in units if r['kind']=='BASELINE_SNAPSHOT')['action'], 'KEEP')

    def test_runs_keep_two_coherent_sets_and_referenced_old_baseline(self):
        pages = self.root/'output/character_skills/pages'
        old_id = None
        for generation in range(3):
            for index, cohort in enumerate(I.COHORTS):
                run_id = f'2026102{generation}T010000000000Z-{index:08x}'
                relative = f'output/character_skills/pages/_batch/{cohort}/runs/{run_id}'
                self.write(relative+'/transactions/1/backup/card.json', 'data')
                self.write(relative+'/transactions/1/backup/index.html', 'html')
                self.write(relative+'/transactions/1/backup/receipt.json', 'receipt')
                self.write(relative+'/cohort_report.json', json.dumps(dict(signature=str(generation),
                           cohort_complete=True, completed=1, expected=1, failed=[])))
                if generation==0 and index==0:
                    old_id = run_id
        errors = []
        with contextlib.redirect_stdout(io.StringIO()):
            rows = I.run_inventory(self.root, pages, {old_id: {'review/closed.md'}}, errors)
        self.assertFalse(errors)
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(r['action']=='KEEP' for r in rows), 8)
        self.assertEqual(next(r for r in rows if r['run_id']==old_id)['action'], 'ARCHIVE_REVIEW')
        self.assertEqual(sum(r['reclaimable_bytes'] for r in rows), 32)
        self.assertTrue(all(r['backup_payload_bytes']==8 for r in rows))

    def test_pinned_baseline_is_kept_and_signature_drift_rejected(self):
        self.write('review.md', 'Historical acceptance with limits')
        self.write('work/baseline/pages/_batch/campaign_latest.json', '{"report":"report.json"}')
        self.write('work/baseline/pages/report.json', '{"signature":"accepted"}')
        pin = dict(path='work/baseline', reason='review baseline', evidence=['review.md'],
                   pages_path='work/baseline/pages', campaign_signature='accepted')
        row = dict(path='work/baseline', action='REVIEW_REPLAY', reclaimable_bytes=50, reasons=[], references=[])
        I.apply_pins(self.root, [row], dict(pins=[pin]))
        self.assertEqual((row['action'], row['reclaimable_bytes']), ('KEEP', 0))
        pin['campaign_signature'] = 'changed'
        with self.assertRaises(ValueError):
            I.apply_pins(self.root, [row], dict(pins=[pin]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
