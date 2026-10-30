"""Safety checks for exact-file cleanup; uses only new temporary fixtures."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import cleanup_20261023 as C


class CleanupSafetyTests(unittest.TestCase):
    def test_allowlist_retains_reports_receipts_and_unrelated_files(self):
        group='output/character_skills/pages/_batch/ge60/runs/example'
        self.assertTrue(C.payload_kind(group,group+'/transactions/7229/backup/card.json','run'))
        self.assertTrue(C.payload_kind(group,group+'/transactions/7229/backup/index.html','run'))
        for path in ('cohort_report.json','transactions/7229/backup/receipt.json',
                     'transactions/7229/backup/before.json','transactions/7229/new/card.json'):
            self.assertFalse(C.payload_kind(group,group+'/'+path,'run'))
        self.assertFalse(C.payload_kind('work/replay','work/replay/metrics.json','ledger'))
        self.assertTrue(C.payload_kind('work/replay','work/replay/ledger.jsonl','ledger'))

    def test_boundaries_and_links_fail_closed(self):
        base=C.ROOT/'work/storage_retention_20261023'
        base.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='cleanup-guard-',dir=base) as tmp:
            root=Path(tmp).resolve()
            file=root/'work/allowed/card.json'
            file.parent.mkdir(parents=True)
            file.write_text('temporary fixture')
            self.assertEqual(C.safe_file(root,'work/allowed/card.json','work/allowed'),file)
            for relative,group in [('work/allowed/card.json','work/other'),
                                   ('work/allowed/../allowed/card.json','work/allowed'),
                                   (str(file),'work/allowed'),('work/allowed','work/allowed')]:
                with self.assertRaises(ValueError):C.safe_file(root,relative,group)
            original=Path.lstat
            def linked(path):
                if path==file.parent:return SimpleNamespace(st_mode=0,st_file_attributes=0x400)
                return original(path)
            with patch.object(Path,'lstat',linked):
                with self.assertRaises(ValueError):C.safe_file(root,'work/allowed/card.json','work/allowed')
            self.assertTrue(file.exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
