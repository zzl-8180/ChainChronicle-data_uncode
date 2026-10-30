"""Synthetic fixtures are permanent; each invocation creates a fresh test tree."""
import csv
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid
import zipfile

HERE = Path(__file__).absolute().parent
PROJECT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("archive_store", HERE / "archive_store.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
RUN = PROJECT / "work/storage_recycle_g1_20261027/archive_tests" / uuid.uuid4().hex


class ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RUN.mkdir(parents=True, exist_ok=False)
        print(f"fixtures retained at {RUN}", flush=True)

    def setUp(self):
        self.base = RUN / self._testMethodName
        self.base.mkdir()
        self.root = self.base / "合成 项目根"
        self.root.mkdir()
        self.manifest = self.base / "plan.csv.gz"
        self.vault = self.base / "vault"
        self.rows = []

    def add(self, name, content, classification="ELIGIBLE_A"):
        name = self.path(name)
        p = self.root.joinpath(*name.split("/"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        self.rows.append({"path": name, "bytes": len(content),
                          "sha256": hashlib.sha256(content).hexdigest(),
                          "classification": classification})
        return p

    def path(self, label):
        run_hash = hashlib.sha256(label.encode("utf-8")).hexdigest()[:8]
        leaf = "index.html" if label.endswith(".html") else "card.json"
        return ("output/character_skills/pages/_batch/ge60/runs/"
                f"20261027T123456000000Z-{run_hash}/transactions/30236/backup/{leaf}")

    def save(self):
        with gzip.open(self.manifest, "xt", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256", "classification"])
            w.writeheader()
            w.writerows(self.rows)

    def build(self, **kw):
        self.save()
        return a.build(self.root, self.manifest, self.vault,
                       reserve_free_gib=kw.pop("reserve_free_gib", 0),
                       max_added_gib=kw.pop("max_added_gib", 0.02), **kw)

    def request(self, paths, name="request.json"):
        p = self.base / name
        with p.open("x", encoding="utf-8") as f:
            json.dump(paths, f, ensure_ascii=False)
        return p

    def assert_failed_build(self):
        report = a.read_json(self.vault / "build_report.json")
        self.assertEqual(report["status"], "FAIL")
        with self.assertRaises(a.ArchiveError):
            a.load_verified(self.vault)

    def test_dedup_versions_unicode_and_new_process_restore(self):
        self.add("旧 run/角色/card.json", b"old-version")
        self.add("another/card.json", b"old-version")
        self.add("new run/card.json", b"new-version")
        self.add("empty.json", b"")
        ignored = self.add("protected.bin", b"keep", "HOLD")
        report = self.build()
        self.assertEqual(report["statistics"]["source_paths"], 4)
        self.assertEqual(report["statistics"]["unique_contents"], 3)
        self.assertEqual(report["statistics"]["readback_members"], 3)
        self.assertEqual(report["skipped_manifest_rows"], 1)
        self.assertEqual(a.verify(self.vault)["status"], "PASS")
        _, _, _, mappings = a.load_verified(self.vault)
        self.assertEqual(mappings[self.path("旧 run/角色/card.json")]["member"], mappings[self.path("another/card.json")]["member"])
        self.assertNotEqual(mappings[self.path("new run/card.json")]["member"], mappings[self.path("another/card.json")]["member"])
        for row in mappings.values():
            self.assertEqual(row["metadata"]["linkcount"], 1)
            self.assertIn("ctime_ns", row["metadata"])
            self.assertIn("attrs", row["metadata"])
        request = self.request(list(mappings))
        dest = self.base / "restored"
        # Deliberately use an unrelated nonexistent root; restore has no source option.
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run([str(PROJECT / ".venv/Scripts/python.exe"), "-X", "utf8", "-B",
                               str(HERE / "archive_store.py"), "restore", "--vault", str(self.vault),
                               "--request", str(request), "--dest", str(dest)],
                              cwd=self.base, env=env, capture_output=True, text=True, encoding="utf-8")
        (self.base / "subprocess_stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (self.base / "subprocess_stderr.txt").write_text(proc.stderr, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in mappings:
            self.assertEqual((dest / name).read_bytes(), (self.root / name).read_bytes())
            self.assertEqual((dest / name).stat().st_mtime_ns, mappings[name]["mtime_ns"])
        self.assertEqual(ignored.read_bytes(), b"keep")

    def test_every_duplicate_source_is_hashed(self):
        self.add("first", b"correct")
        other = self.add("second", b"incorrect")
        self.rows[1].update(bytes=7, sha256=self.rows[0]["sha256"])
        # Same advertised size and SHA, but different actual bytes.
        other.write_bytes(b"WRONG!!")
        with self.assertRaisesRegex(a.ArchiveError, "source SHA"):
            self.build()
        self.assert_failed_build()
        self.assertEqual(other.read_bytes(), b"WRONG!!")

    def test_source_hash_error_and_no_overwrite_vault(self):
        src = self.add("card", b"one")
        self.rows[0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(a.ArchiveError, "source SHA"):
            self.build()
        self.assert_failed_build()
        self.assertEqual(src.read_bytes(), b"one")
        before = (self.vault / "build_report.json").read_bytes()
        with self.assertRaises(a.ArchiveError):
            a.build(self.root, self.manifest, self.vault, 0, .02)
        self.assertEqual(before, (self.vault / "build_report.json").read_bytes())

    def test_corrupt_volume_rejected_before_restore_output(self):
        self.add("one", b"abcdef")
        self.build()
        volume = self.vault / "volume-000001.zip"
        # This modifies only the synthetic fault fixture, never a real vault.
        with volume.open("r+b") as f:
            f.seek(48)
            f.write(b"CORRUPTED")
        with self.assertRaisesRegex(a.ArchiveError, "volume hash"):
            a.verify(self.vault)
        reports = list(self.vault.glob("verify_report-*.json"))
        self.assertEqual(a.read_json(reports[-1])["status"], "FAIL")
        dest = self.base / "not-created"
        with self.assertRaises(a.ArchiveError):
            a.restore(self.vault, self.request([self.path("one")]), dest)
        self.assertFalse(dest.exists())

    def test_restore_traversal_missing_and_existing_conflict(self):
        self.add("a/b", b"old")
        self.build()
        for i, bad in enumerate(["../escaped", "/absolute", "a/../../bad", "C:/ads", "a\\b", "NUL", "a:stream", "a/./b"]):
            with self.subTest(path=bad), self.assertRaises(a.ArchiveError):
                a.restore(self.vault, self.request([bad], f"bad-{i}.json"), self.base / f"dest-{i}")
        with self.assertRaisesRegex(a.ArchiveError, "missing requested"):
            a.restore(self.vault, self.request(["absent"], "missing.json"), self.base / "missing-dest")
        dest = self.base / "existing"
        dest.mkdir()
        conflict = dest / "a"
        conflict.write_bytes(b"different")
        with self.assertRaisesRegex(a.ArchiveError, "independent new"):
            a.restore(self.vault, self.request([self.path("a/b")]), dest)
        self.assertEqual(conflict.read_bytes(), b"different")

    def test_budget_failures_preserve_sources_and_diagnostics(self):
        src = self.add("noise", os.urandom(180000))
        before = a.hash_file(src)
        with self.assertRaisesRegex(a.ArchiveError, "max-added"):
            self.build(max_added_gib=130000 / a.GIB)
        self.assert_failed_build()
        self.assertEqual(a.hash_file(src), before)
        self.assertLessEqual(sum(p.stat().st_size for p in self.vault.iterdir()), 130000)
        # Separate new vault for reserve-free failure; never remove earlier fixtures.
        self.vault = self.base / "reserve-vault"
        with patch.object(a.shutil, "disk_usage", return_value=shutil_usage(a.GIB + 8192)):
            with self.assertRaisesRegex(a.ArchiveError, "reserve-free"):
                a.build(self.root, self.manifest, self.vault, 1, .02)
        self.assert_failed_build()
        self.assertTrue(src.exists())

    def test_rolling_volumes_and_full_readback(self):
        for i in range(4):
            self.add(f"{i}.bin", os.urandom(3000))
        with patch.object(a, "VOLUME_TARGET", 2000), patch.object(a, "VOLUME_HARD", 12000):
            report = self.build()
        self.assertEqual(report["statistics"]["volume_count"], 4)
        self.assertEqual(a.verify(self.vault)["statistics"]["readback_members"], 4)

    def test_case_collision_traversal_and_hardlink_hold(self):
        src = self.add("safe", b"one")
        self.rows.append({**self.rows[0], "path": "../outside"})
        with self.assertRaisesRegex(a.ArchiveError, "unsafe path"):
            self.build()
        self.assert_failed_build()
        self.vault = self.base / "hardlink-vault"
        try:
            os.link(src, self.root / "second-link")
        except PermissionError as exc:
            (self.base / "hardlink_creation_result.json").write_text(
                json.dumps({"error": str(exc)}), encoding="utf-8")
            self.skipTest("sandbox denied hardlink creation; nlink rejection tested separately")
        with self.assertRaisesRegex(a.ArchiveError, "hardlink HOLD"):
            a.build(self.root, self.manifest, self.vault, 0, .02)
        self.assertEqual(src.stat().st_nlink, 2)
        self.assert_failed_build()

    def test_casefold_collision(self):
        self.add("Card.json", b"old")
        self.rows.append({**self.rows[0], "path": self.rows[0]["path"].upper()})
        with self.assertRaisesRegex(a.ArchiveError, "case-colliding"):
            self.build()
        self.assert_failed_build()

    def test_symlink_or_junction_refused(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "card.json").write_bytes(b"private")
        link = (self.root / self.path("linked")).parent
        link.parent.mkdir(parents=True)
        if os.name == "nt":
            # Junctions need no developer mode/admin and exercise Windows reparse handling.
            proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                                  capture_output=True)
            (self.base / "junction_creation_result.json").write_text(
                json.dumps({"returncode": proc.returncode, "stdout": repr(proc.stdout),
                            "stderr": repr(proc.stderr)}), encoding="utf-8")
            if proc.returncode:
                self.skipTest("sandbox denied junction creation; diagnostic retained; attribute rejection tested separately")
        else:
            link.symlink_to(outside, target_is_directory=True)
        self.rows = [{"path": self.path("linked"), "bytes": 7,
                      "sha256": hashlib.sha256(b"private").hexdigest(), "classification": "ELIGIBLE_A"}]
        with self.assertRaisesRegex(a.ArchiveError, "reparse/"):
            self.build()
        self.assert_failed_build()

    def test_reparse_attribute_rejected(self):
        from types import SimpleNamespace
        src = self.add("normal", b"plain")
        s = src.stat()
        fake = SimpleNamespace(st_mode=s.st_mode, st_nlink=1, st_file_attributes=a.REPARSE)
        with self.assertRaisesRegex(a.ArchiveError, "reparse/symlink"):
            a.check_stat(fake)
        fake.st_file_attributes = 0
        fake.st_nlink = 2
        with self.assertRaisesRegex(a.ArchiveError, "hardlink HOLD"):
            a.check_stat(fake)

    def test_eligible_label_cannot_include_protected_tree_or_arbitrary_path(self):
        self.add("safe", b"safe")
        self.rows[0]["path"] = ("output/character_skills/pages/_batch/retained_payloads/"
                                 "ge60/runs/20261027T123456000000Z-12345678/transactions/30236/backup/card.json")
        with self.assertRaisesRegex(a.ArchiveError, "outside the real A payload shape"):
            self.build()
        self.assert_failed_build()

    def test_windows_ads_refused(self):
        if os.name != "nt":
            self.skipTest("Windows ADS fixture")
        src = self.add("adsfile", b"main")
        with open(str(src) + ":secret", "xb") as f:
            f.write(b"extra")
        with self.assertRaisesRegex(a.ArchiveError, "alternate data stream HOLD"):
            self.build()
        self.assert_failed_build()

    def test_member_content_and_mapping_completeness_are_checked(self):
        self.add("a", b"known")
        self.build()
        catalog = a.read_json(self.vault / "catalog.json")
        # A separately built malicious fixture with matching outer volume SHA must still fail readback.
        evil = self.base / "malicious"
        evil.mkdir()
        for name in ("plan_manifest.csv.gz", "index.jsonl"):
            (evil / name).write_bytes((self.vault / name).read_bytes())
        with zipfile.ZipFile(evil / "volume-000001.zip", "x", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(a.member_name(self.rows[0]["sha256"], 5), b"WRONG")
        sha, size = a.hash_file(evil / "volume-000001.zip")
        catalog["volumes"][0].update(sha256=sha, bytes=size)
        with self.assertRaisesRegex(a.ArchiveError, "readback SHA"):
            a.verify_core(evil, catalog)
        incomplete = self.base / "incomplete"
        incomplete.mkdir()
        (incomplete / "plan_manifest.csv.gz").write_bytes(self.manifest.read_bytes())
        (incomplete / "index.jsonl").write_bytes(b"")
        (incomplete / "volume-000001.zip").write_bytes((evil / "volume-000001.zip").read_bytes())
        catalog["index_sha256"] = a.hash_file(incomplete / "index.jsonl")[0]
        with self.assertRaisesRegex(a.ArchiveError, "incomplete source mapping"):
            a.verify_core(incomplete, catalog)

    def test_zip_slip_extra_member_and_volume_are_rejected(self):
        self.add("a", b"known")
        self.build()
        catalog = a.read_json(self.vault / "catalog.json")
        evil = self.base / "zip-slip"
        evil.mkdir()
        for name in ("plan_manifest.csv.gz", "index.jsonl"):
            (evil / name).write_bytes((self.vault / name).read_bytes())
        with zipfile.ZipFile(evil / "volume-000001.zip", "x", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("../escape", b"known")
        sha, size = a.hash_file(evil / "volume-000001.zip")
        catalog["volumes"][0].update(sha256=sha, bytes=size)
        with self.assertRaisesRegex(a.ArchiveError, "unsafe ZIP member"):
            a.verify_core(evil, catalog)
        self.assertFalse((self.base / "escape").exists())
        (self.vault / "volume-999999.zip").write_bytes(b"unlisted")
        with self.assertRaisesRegex(a.ArchiveError, "unlisted/missing"):
            a.verify(self.vault)

    def test_volume_hard_limit_and_reserved_volume_name_never_overwritten(self):
        source = self.add("noise", os.urandom(5000))
        before = a.hash_file(source)
        with patch.object(a, "VOLUME_TARGET", 1000), patch.object(a, "VOLUME_HARD", 2000):
            with self.assertRaisesRegex(a.ArchiveError, "volume hard limit"):
                self.build()
        self.assert_failed_build()
        self.assertEqual(a.hash_file(source), before)
        self.assertLessEqual((self.vault / "volume-000001.zip").stat().st_size, 2000)
        # Interference at the point of first member creation must never truncate the intruder.
        self.vault = self.base / "name-collision"
        original = a.read_file

        from contextlib import contextmanager
        @contextmanager
        def inject(path):
            if Path(path) == source:
                with (self.vault / "volume-000001.zip").open("xb") as f:
                    f.write(b"foreign file")
            with original(path) as opened:
                yield opened

        with patch.object(a, "read_file", inject):
            with self.assertRaises(FileExistsError):
                a.build(self.root, self.manifest, self.vault, 0, .02)
        self.assertEqual((self.vault / "volume-000001.zip").read_bytes(), b"foreign file")
        self.assert_failed_build()

    def test_malformed_manifest_and_no_eligible_rows_fail_closed(self):
        self.add("protected", b"keep", "PROTECTED")
        with self.assertRaisesRegex(a.ArchiveError, "no ELIGIBLE_A"):
            self.build()
        self.assert_failed_build()
        self.vault = self.base / "malformed-vault"
        bad = self.base / "malformed.csv.gz"
        with gzip.open(bad, "xt", encoding="utf-8") as f:
            f.write("path,bytes\na,1\n")
        with self.assertRaisesRegex(a.ArchiveError, "manifest requires"):
            a.build(self.root, bad, self.vault, 0, .02)
        self.assert_failed_build()


def shutil_usage(free):
    from collections import namedtuple
    return namedtuple("Usage", "total used free")(10**12, 10**12 - free, free)


if __name__ == "__main__":
    program = unittest.main(verbosity=2, exit=False)
    result = program.result
    summary = {"status": "PASS_WITH_SKIPS" if result.wasSuccessful() and result.skipped else
               "PASS" if result.wasSuccessful() else "FAIL",
               "tests_run": result.testsRun, "failures": [(str(t), msg) for t, msg in result.failures],
               "errors": [(str(t), msg) for t, msg in result.errors],
               "skipped": [(str(t), msg) for t, msg in result.skipped],
               "code_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                               for name in ("archive_store.py", "test_archive_store.py", "README_ARCHIVE.md")
                               if (HERE / name).exists()}}
    with (RUN / "test_result.json").open("x", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    sys.exit(0 if result.wasSuccessful() else 1)
