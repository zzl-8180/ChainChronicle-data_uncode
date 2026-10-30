"""Isolated retention boundary/concurrency and real runner integration checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/character_skills'))
import run_retention as R


class RetentionTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT/'work/storage_retention_20261023'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='test-', dir=scratch)
        self.pages = Path(self.temp.name)/'pages'
        self.pages.mkdir()
        self.old = self.pages/'_batch/ge60/runs/legacy/transactions/1/backup/card.json'
        self.old.parent.mkdir(parents=True)
        self.old.write_bytes(b'old protected evidence')

    def tearDown(self):
        self.assertEqual(self.old.read_bytes(), b'old protected evidence')
        self.temp.cleanup()  # Only this test's newly-created fixture directory.

    def run_path(self, name):
        return self.pages/'_batch/ge60/runs'/name

    def configure(self, max_bytes=1024**2, max_runs=12):
        with R._locked(self.pages) as path:
            state = R._state(path)
            state.update(max_bytes=max_bytes, max_runs=max_runs)
            R._save(path, state)

    def state(self):
        return R._read(self.pages/'_batch/retention/state.json')

    def test_legacy_preserved_and_exact_byte_boundary(self):
        card = self.pages/'1/card.json'
        card.parent.mkdir()
        card.write_bytes(b'x'*100)
        self.configure(max_bytes=4196)
        reservation = R.reserve_run(self.pages, self.run_path('one'), [1])
        self.assertEqual(reservation['reserved_bytes'], 4196)
        with self.assertRaises(R.RetentionLimitError):
            R.reserve_run(self.pages, self.run_path('two'), [1])
        self.assertEqual(card.read_bytes(), b'x'*100)
        self.assertEqual(len(self.state()['reservations']), 1)

    def test_run_count_and_no_rebuild(self):
        self.configure(max_runs=1)
        R.reserve_run(self.pages, self.run_path('one'), [1])
        self.assertEqual(R.reserve_run(self.pages, self.run_path('reuse'), [])['status'], 'NO_REBUILD')
        with self.assertRaises(R.RetentionLimitError):
            R.reserve_run(self.pages, self.run_path('two'), [1])

    def test_interrupted_run_reservation_survives(self):
        self.configure(max_runs=1)
        R.reserve_run(self.pages, self.run_path('interrupted'), [1])
        # No report/transaction is produced, simulating a crash after admission.
        with self.assertRaises(R.RetentionLimitError):
            R.reserve_run(self.pages, self.run_path('later'), [1])

    def test_release_requires_evidence_and_removed_payload(self):
        self.configure(max_runs=1)
        run = self.run_path('one')
        R.reserve_run(self.pages, run, [1])
        key = run.relative_to(self.pages).as_posix()
        evidence = Path(self.temp.name)/'disposition.md'
        with self.assertRaises(ValueError):
            R.release_reservation(self.pages, key, evidence)
        evidence.write_text('Fixture archive/cleanup disposition', encoding='utf-8')
        payload = run/'transactions/1/backup/card.json'
        payload.parent.mkdir(parents=True)
        payload.write_text('preserve')
        with self.assertRaises(R.RetentionLimitError):
            R.release_reservation(self.pages, key, evidence)
        self.assertEqual(payload.read_text(), 'preserve')
        # A separate fixture with no payload represents a completed cleanup.
        self.configure(max_runs=2)
        cleared = self.run_path('cleared')
        R.reserve_run(self.pages, cleared, [1])
        receipt = cleared/'transactions/1/backup/receipt.json'
        receipt.parent.mkdir(parents=True)
        receipt.write_text('{}')
        R.release_reservation(self.pages, cleared.relative_to(self.pages).as_posix(), evidence)
        self.assertEqual(receipt.read_text(), '{}')
        self.assertEqual(sum(r['status']=='RETAINED' for r in self.state()['reservations'].values()), 1)

    def test_path_escape_and_invalid_policy_fail_closed(self):
        with self.assertRaises(ValueError):
            R.reserve_run(self.pages, self.pages.parent/'elsewhere', [1])
        self.configure()
        path = self.pages/'_batch/retention/state.json'
        state = self.state()
        state['max_bytes'] = 0
        R._save(path, state)
        with self.assertRaises(R.RetentionLimitError):
            R.reserve_run(self.pages, self.run_path('one'), [1])

    def test_four_processes_share_two_slots(self):
        self.configure(max_runs=2)
        program = (
            'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
            'from run_retention import reserve_run; '
            'reserve_run(Path(sys.argv[2]),Path(sys.argv[3]),[1])')
        children = [subprocess.Popen([sys.executable, '-B', '-c', program,
                    str(ROOT/'scripts/character_skills'), str(self.pages), str(self.run_path(str(i)))],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(4)]
        for child in children:
            child.communicate(timeout=45)
        self.assertEqual(sorted(c.returncode for c in children), [0, 0, 1, 1])
        self.assertEqual(len(self.state()['reservations']), 2)

    def test_existing_lock_never_stolen(self):
        folder = self.pages/'_batch/retention'
        folder.mkdir(parents=True)
        lock = folder/'reservation.lock'
        lock.write_text('another owner')
        with self.assertRaises(R.RetentionLimitError):
            with R._locked(self.pages, timeout=0.1):
                self.fail('must not acquire')
        self.assertEqual(lock.read_text(), 'another owner')

    def test_real_batch_entry_rejects_before_input_build_or_page_write(self):
        self.configure(max_bytes=1)
        cmd = [sys.executable, '-B', str(ROOT/'scripts/character_skills/card_page_batch.py'),
               '--input-root', str(ROOT), '--manifest', str(ROOT/'output/character_skills/r2_preparation/cohorts/manifest.json'),
               '--output', str(self.pages), '--cohort', 'ge60', '--cid', '7229', '--execute']
        result = subprocess.run(cmd, capture_output=True, timeout=90)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Backup retention limit reached BEFORE page writes', result.stderr)
        self.assertFalse((self.pages/'7229').exists())
        self.assertEqual(self.state()['reservations'], {})
        self.assertEqual(list(self.pages.glob('_batch/*/runs/*/transactions')),
                         [self.old.parents[2]])


if __name__ == '__main__':
    unittest.main(verbosity=2)
