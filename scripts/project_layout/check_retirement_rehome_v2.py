"""Read-only S7 v2 verification. Writes an exclusive receipt under an allowed root."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys


REVIEW = "docs/project-layout/20261113-cleanup-review-v2"
PREP = "work/20261113-cleanup-prep-v2/s7"
PREP_DOCS = "docs/project-layout/20261113-cleanup-prep-v2"
CHECKER = "scripts/project_layout/check_retirement_rehome_v2.py"
RECEIPTS = "operations/records/retired-packaging-rehome/20261113"
OLD_BUNDLE = "operations/history/retired-packaging/20261108/share_bundle/20261104-mechanism-first-handoff-r1"
BUNDLE = "projects/skill-research/evidence/mechanism-first-handoff/20261104"
HISTORICAL_MANIFEST = "output/share_bundle/20261104-mechanism-first-handoff-r1/payload/manifest.json"
IGNORE = "operations/history/retired-packaging/.gitignore"
PROTECTION = "output/storage_retention/recycle_g1_20261027"
CYCLES = ("c14_c15_20261104", "c16_20261106", "c17_c18_20261106", "c19_20261107")
FROZEN = {
    f"{PROTECTION}/P_preservation.json": "10e5b3d71d990b22fa8c53c595cc0be439707fb1dc4a36c589e537034724998f",
    f"{PROTECTION}/protection_manifest_v7.json": "2db5e6fd3b277884e4de47603760c22deb8db5ccdf6b8bbb8b235c1326b1de17",
    "docs/project-layout/20261108-packaging-full-retirement-v1/full-disposition.jsonl": "274c6cd5602b591047ce2b2c907b4e5d9bb33ff55b190b0bb8678ec586e82ef1",
}
LEGACY_MAP = "docs/project-layout/20261108-packaging-runtime-ready-v1/runtime/locations.json"
MOUNT_POINT = 0xA0000003
DEVICE_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    require(isinstance(value, str) and value and not any(ch in value for ch in "\\:"),
            f"Unsafe path: {value}")
    require(all(part not in ("", ".", "..") and part == part.rstrip(" .")
                and not any(ord(ch) < 32 or ch in '<>"|?*' for ch in part)
                and part.split(".")[0].upper() not in DEVICE_NAMES
                for part in value.split("/")), f"Unsafe path: {value}")
    require(PurePosixPath(value).as_posix() == value, f"Noncanonical path: {value}")
    return value


def reparse(st):
    return bool(getattr(st, "st_file_attributes", 0) & 1024) or stat.S_ISLNK(st.st_mode)


def checked(root, relative, kind="file"):
    path = root / canonical(relative)
    for parent in reversed(path.relative_to(root).parents):
        current = root / parent
        st = current.lstat()
        require(stat.S_ISDIR(st.st_mode) and not reparse(st), f"Unsafe ancestor: {current}")
    if kind == "leaf":
        return path
    st = path.lstat()
    wanted = stat.S_ISREG if kind == "file" else stat.S_ISDIR
    require(wanted(st.st_mode) and not reparse(st), f"Unsafe {kind}: {path}")
    return path


def stamp(st):
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_nlink


def raw(root, relative):
    path = checked(root, relative)
    before = stamp(path.lstat())
    with path.open("rb") as stream:
        require(stamp(os.fstat(stream.fileno())) == before, f"Identity drift: {relative}")
        content = stream.read()
    require(stamp(checked(root, relative).lstat()) == before, f"Read drift: {relative}")
    return content


def identity(content):
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def document(root, relative):
    return json.loads(raw(root, relative))


def same(content, expected, label):
    require(identity(content) == {k: expected[k] for k in ("bytes", "sha256")}, f"Content mismatch: {label}")


def unique(rows, field):
    result = {}
    for row in rows:
        path = canonical(row[field])
        require(path.casefold() not in result, f"Duplicate {field}: {path}")
        result[path.casefold()] = row
    return result


def files_under(root, relative):
    base = checked(root, relative, "directory")
    result = set()
    todo = [base]
    while todo:
        for child in todo.pop().iterdir():
            st = child.lstat()
            require(not reparse(st), f"Reparse within payload: {child}")
            if stat.S_ISDIR(st.st_mode):
                todo.append(child)
            else:
                require(stat.S_ISREG(st.st_mode), f"Unexpected payload entry: {child}")
                result.add(child.relative_to(base).as_posix())
    return result


def is_missing(root, relative):
    try:
        checked(root, relative, "leaf").lstat()
    except FileNotFoundError:
        return True
    return False


def real_record(value):
    require(all(value.get(key, False) is False for key in ("simulated", "test_only", "fixture")),
            "Simulation/test/fixture record cannot authorize a formal stage")


def approved(value, bindings, lineage):
    real_record(value)
    require(value.get("schema_version") == 2 and value.get("status") == "APPROVED"
            and value.get("approved") is True, "Missing explicit approved record")
    require(all(value.get(k) == v for k, v in {**bindings, **lineage}.items()),
            "Approval package or lineage mismatch")


def bound_document(root, path, digest):
    data = raw(root, path)
    require(isinstance(digest, str) and identity(data)["sha256"] == digest,
            f"Bound document SHA-256 mismatch: {path}")
    return json.loads(data)


def stage_path(path, run_id):
    require(canonical(path).startswith(f"{RECEIPTS}/{run_id}/"),
            "Formal stage evidence must be in its registered run directory")
    return path


def verify_prep_review(root, args, approval, pkg_sha):
    require(args.prep_package == f"{PREP_DOCS}/PACKAGE.json", "Expected current prep PACKAGE")
    prep = bound_document(root, args.prep_package, approval.get("prep_package_sha256"))
    artifacts = unique(prep["artifacts"], "path")
    required = [CHECKER, f"{PREP_DOCS}/EXECUTION-CONTRACT.md", f"{PREP_DOCS}/REFRESH-AND-APPROVAL.md",
                f"{PREP_DOCS}/s7/README.md", "scripts/skill_reader_preview/build.py",
                "scripts/skill_reader_preview/reference_copy.py", "scripts/skill_reader_preview/reference_sources_v2.py",
                args.mapping]
    for path in required:
        require(path.casefold() in artifacts, f"Missing prep artifact: {path}")
        same(raw(root, path), artifacts[path.casefold()], path)
    # Check the executing module as well as the registered repository path.
    same(Path(__file__).read_bytes(), artifacts[CHECKER.casefold()], "executing __file__")
    review_path = canonical(args.independent_review_verdict)
    require(review_path.startswith("docs/project-layout/") and review_path.endswith("/verdict.json"),
            "Independent verdict must be a registered review document")
    verdict = bound_document(root, review_path, approval.get("independent_review_verdict_sha256"))
    real_record(verdict)
    require(verdict.get("verdict") == "PREPARATION_REVIEW_PASS_WITH_IMPLEMENTATION_GATES"
            and verdict.get("blocking_findings") == [], "Independent review has not passed")
    require(verdict.get("reviewed_package") == {"path": args.prep_package,
            "sha256": approval["prep_package_sha256"]}, "Independent review prep binding mismatch")
    return dict(v2_package_sha256=pkg_sha, prep_package_sha256=approval["prep_package_sha256"],
                independent_review_verdict_sha256=approval["independent_review_verdict_sha256"])


def verify_scope(approval, mode, rehome):
    require(approval.get("scope") == f"S7_{mode}"
            and set(approval["rehome_ids"]) == {r["id"] for r in rehome.values()}
            and len(approval["rehome_ids"]) == 148, "Approval scope mismatch")


def verify_journal(root, path, digest, status, bindings, lineage, rehome):
    journal_doc = bound_document(root, stage_path(path, lineage["run_id"]), digest)
    real_record(journal_doc)
    require(journal_doc.get("schema_version") == 2
            and all(journal_doc.get(k) == v for k, v in {**bindings, **lineage}.items()),
            "Journal package or lineage mismatch")
    journal = unique(journal_doc["files"], "path")
    require(set(journal) == set(rehome), "Journal REHOME coverage mismatch")
    for key, row in rehome.items():
        event = journal[key]
        require(all(event[k] == row[k] for k in ("id", "path", "target", "sha256", "logical_bytes"))
                and event["status"] == status, f"Journal stage or identity mismatch: {row['id']}")


def verify_target_receipt(root, args, approval, bindings, lineage, rehome):
    receipt = bound_document(root, stage_path(args.target_receipt, args.run_id), approval.get("target_receipt_sha256"))
    real_record(receipt)
    require(receipt.get("mode") == "TARGET_VALIDATION" and receipt.get("status") == "PASS_TARGET_VALIDATION"
            and receipt.get("target_validation_status") == "PASS" and receipt.get("post_rehome_status") == "NOT_RUN",
            "Target receipt is not a prior TARGET pass")
    expected = {**bindings, **lineage, "mapping_path": args.mapping, "mapping_sha256": approval["mapping_sha256"],
                "prep_package_path": args.prep_package, "independent_review_verdict_path": args.independent_review_verdict,
                "rehome_checked": 148, "bundle_files_checked": 139, "manifest_members_checked": 135,
                "s6_survivor_refs_checked": 168, "frozen_plans_checked": 4, "keep_checked": 12,
                "junctions_checked": 5, "original_junctions_unchanged": True, "original_sources_checked": 148}
    require(all(receipt.get(k) == v for k, v in expected.items()), "Target receipt lineage, binding or coverage mismatch")
    target_approval = bound_document(root, stage_path(receipt["approval_path"], args.run_id), receipt["approval_sha256"])
    approved(target_approval, bindings, lineage)
    verify_scope(target_approval, "TARGET_VALIDATION", rehome)
    require(target_approval.get("states_sha256") is None and target_approval.get("target_receipt_sha256") is None
            and target_approval.get("mapping_sha256") == approval["mapping_sha256"]
            and target_approval.get("journal_sha256") == receipt["journal_sha256"],
            "Target approval evidence mismatch")
    verify_journal(root, receipt["journal_path"], receipt["journal_sha256"], "COPIED_VERIFIED", bindings, lineage, rehome)
    require(receipt["journal_sha256"] != approval["journal_sha256"], "TARGET and POST journals must be distinct")
    return receipt


def verify_formal_chain(root, args, pkg_sha, rehome):
    final = args.mode == "POST_REHOME"
    require(args.approval and args.journal and args.prep_package and args.independent_review_verdict
            and bool(args.states) == final and bool(args.target_receipt) == final and not args.fixture,
            f"{args.mode} requires bound approval/journal/prep/review; states and target-receipt only for POST_REHOME")
    require(isinstance(args.run_id, str) and args.run_id and canonical(args.run_id) == args.run_id
            and "/" not in args.run_id, "Missing or invalid run_id")
    approval_raw = raw(root, stage_path(args.approval, args.run_id))
    approval = json.loads(approval_raw)
    real_record(approval)
    reference = approval.get("approval_reference")
    require(isinstance(reference, str) and reference.strip() == reference and bool(reference), "Missing approval_reference")
    lineage = dict(run_id=args.run_id, approval_reference=reference)
    bindings = verify_prep_review(root, args, approval, pkg_sha)
    approved(approval, bindings, lineage)
    verify_scope(approval, args.mode, rehome)
    require(approval.get("mapping_sha256") == identity(raw(root, args.mapping))["sha256"], "Mapping approval mismatch")
    verify_journal(root, args.journal, approval.get("journal_sha256"), "MOVED" if final else "COPIED_VERIFIED",
                   bindings, lineage, rehome)
    link_states = None
    target = None
    if final:
        link_states = bound_document(root, stage_path(args.states, args.run_id), approval.get("states_sha256"))
        approved(link_states, bindings, lineage)
        target = verify_target_receipt(root, args, approval, bindings, lineage, rehome)
    else:
        require(approval.get("states_sha256") is None and approval.get("target_receipt_sha256") is None,
                "TARGET approval must not bind POST-only evidence")
    evidence = {**bindings, **lineage, "prep_package_path": args.prep_package,
                "independent_review_verdict_path": args.independent_review_verdict,
                "mapping_path": args.mapping, "mapping_sha256": approval["mapping_sha256"],
                "journal_path": args.journal, "journal_sha256": approval["journal_sha256"],
                "approval_path": args.approval, "approval_sha256": identity(approval_raw)["sha256"],
                "states_path": args.states, "states_sha256": approval.get("states_sha256"),
                "target_receipt_path": args.target_receipt, "target_receipt_sha256": approval.get("target_receipt_sha256"),
                "target_journal_sha256": target["journal_sha256"] if target else None,
                "target_approval_sha256": target["approval_sha256"] if target else None}
    return evidence, link_states, bindings, lineage


def junction(root, row):
    path = checked(root, row["path"], "leaf")
    st = path.lstat()
    observed = (st.st_dev, st.st_ino, getattr(st, "st_reparse_tag", 0), os.readlink(path))
    require(observed[:3] == (row["dev"], row["ino"], MOUNT_POINT)
            and row["reparse_tag"] == MOUNT_POINT
            and observed[3] == row["target_raw"], f"Junction identity or target mismatch: {row['path']}")


def target_string(path):
    return os.path.normcase(os.path.normpath(str(path).removeprefix("\\\\?\\")))


def verify_junctions(root, baseline, proposal, bindings, lineage):
    approved(proposal, bindings, lineage)
    states = unique(proposal["states"], "path")
    require(set(states) == set(baseline), "Expected all five approved S7 junction states")
    for key, old in baseline.items():
        row = states[key]
        path = old["path"]
        require(row["path"] == path, f"Junction path spelling mismatch: {path}")
        action = row["action"]
        if action == "RETIRE":
            require(row["target"] is None and is_missing(root, path), f"Expected retired junction: {path}")
        elif action == "KEEP":
            junction(root, old)
            require(target_string(root / canonical(row["target"])) == target_string(old["target_raw"]),
                    f"Expected unchanged target: {path}")
            checked(root, row["target"], "directory")
        elif action == "REDIRECT":
            target = checked(root, row["target"], "directory")
            require(target_string(target) != target_string(old["target_raw"])
                    and not target.is_relative_to(root / "output/share_bundle"), f"Invalid redirect: {path}")
            leaf = checked(root, path, "leaf")
            target_raw = os.readlink(leaf)
            require(target_string(target_raw) == target_string(target), f"Wrong redirected target: {path}")
            junction(root, {**row, "target_raw": target_raw})
            probe = row["readback"]
            content = raw(root, f"{row['target']}/{canonical(probe['relative_path'])}")
            same(content, probe, f"redirected target probe {path}")
        else:
            raise ValueError(f"Unapproved junction action: {action}")
        parent = path.rsplit("/", 1)[0]
        checked(root, parent, "directory")
        for role in ("previous", "next"):
            require(is_missing(root, f"{path}.retirement-{role}-20261108"), f"Unexpected {role}: {path}")


def verify(root, args, report):
    pkg = raw(root, f"{REVIEW}/PACKAGE.json")
    pkg_sha = identity(pkg)["sha256"]
    require(pkg_sha == args.package_sha256, "Review package SHA-256 mismatch")
    package = json.loads(pkg)
    require(package["version"] == "v2", "Expected v2 package")
    artifacts = unique(package["artifacts"], "path")
    content = {}
    for name in ("s7.jsonl", "s6.jsonl", "link-plan.json"):
        rel = f"{REVIEW}/{name}"
        content[name] = raw(root, rel)
        same(content[name], artifacts[rel.casefold()], rel)
    s7 = [json.loads(line) for line in content["s7.jsonl"].splitlines()]
    rehome = {key: row for key, row in unique(s7, "path").items() if row["action"] == "REHOME"}
    keep = [row for row in s7 if row["action"] == "KEEP"]
    targets = unique(rehome.values(), "target")
    require(len(rehome) == 148 and len(keep) == 12 and not set(targets) & set(unique(s7, "path")),
            "S7 coverage or source/target collision")
    mapping = document(root, args.mapping)
    require(mapping["schema_version"] == 1 and mapping["package_sha256"] == pkg_sha, "Mapping package mismatch")
    require(mapping["status"] == "PROPOSED" and mapping["effective"] is False, "Expected proposed inactive mapping")
    require(mapping["locations"] == {row["path"]: row["target"] for row in rehome.values()}, "Location map differs from frozen REHOME")
    states = unique(json.loads(content["link-plan.json"]), "path")
    baseline = {key: row for key, row in states.items()
                if row["proposed_action"] == "RETIRE_OR_REDIRECT_AFTER_SHARED_ADAPTATION"}
    require(len(baseline) == 5, "Expected five baseline junctions")
    for key, expected in FROZEN.items():
        require(identity(raw(root, key))["sha256"] == expected, f"Frozen identity mismatch: {key}")
    legacy = raw(root, LEGACY_MAP)
    require(identity(legacy)["sha256"] == mapping["frozen_legacy_map_sha256"], "Legacy map changed")

    mode = args.mode
    if mode in ("TARGET_VALIDATION", "POST_REHOME"):
        final = mode == "POST_REHOME"
        evidence, link_states, bindings, lineage = verify_formal_chain(root, args, pkg_sha, rehome)
        report.update(evidence)
        for row in rehome.values():
            require(not is_missing(root, row["target"]), f"Formal REHOME target missing: {row['target']}")
        for row in rehome.values():
            if final:
                require(is_missing(root, row["path"]), f"Expected retired source: {row['path']}")
            else:
                same(raw(root, row["path"]), {"bytes": row["logical_bytes"], "sha256": row["sha256"]}, row["path"])
        if final:
            verify_junctions(root, baseline, link_states, bindings, lineage)
        else:
            for row in baseline.values():
                junction(root, row)
            report.update(original_sources_checked=148, original_junctions_unchanged=True)
        for key in set(states) - set(baseline):
            junction(root, states[key])
    else:
        require(not any(getattr(args, key) for key in ("approval", "journal", "states", "prep_package",
                    "independent_review_verdict", "target_receipt", "run_id")),
                "Approval artifacts are only valid in TARGET_VALIDATION or POST_REHOME")
        require(bool(args.fixture) == (mode == "SIMULATION"), "SIMULATION requires an isolated fixture root")
        if args.fixture:
            require(canonical(args.fixture).startswith(f"{PREP}/fixtures/"), "Fixture must be under isolated fixture root")
            checked(root, args.fixture, "directory")
        if mode == "INPUT_VALIDATION":
            for row in rehome.values():
                require(is_missing(root, row["target"]), f"REHOME target already exists: {row['target']}")
            for row in baseline.values():
                junction(root, row)

    bundle_count = 0
    native_count = 0
    p222_count = 0
    skill_count = 0
    manifest_raw = None
    observed_bundle = {}
    for row in rehome.values():
        path = row["path"] if mode == "INPUT_VALIDATION" else row["target"]
        if args.fixture:
            path = f"{args.fixture}/{path}"
        data = raw(root, path)
        same(data, {"bytes": row["logical_bytes"], "sha256": row["sha256"]}, path)
        if row["target"].startswith(f"{BUNDLE}/"):
            inside = row["target"][len(BUNDLE) + 1:]
            require(row["path"] == f"{OLD_BUNDLE}/{inside}", f"Bundle relative path changed: {inside}")
            observed_bundle[inside] = identity(data)
            if inside == "payload/manifest.json":
                manifest_raw = data
            bundle_count += 1
        if row["target"].startswith("projects/unpack/research/retained-native-inputs/20261113/"):
            native_count += 1
        if row["target"].startswith("operations/records/retired-packaging-identities/20261113/P222/"):
            wanted = document(root, f"{PROTECTION}/P_preservation.json")["files"][221]
            require(wanted["source_existing_protected"] == row["frozen_source_path"], "P222 source mismatch")
            same(data, wanted, "P222")
            require(len(data) == 12340, "P222 length mismatch")
            p222_count += 1
        for date in ("20261021", "20261022"):
            bundle_id = f"cc_skill_values_{date}"
            if not row["target"].endswith(f"/{bundle_id}/manifest.json"):
                continue
            manifest = json.loads(data)
            require(manifest["bundle_id"] == bundle_id and len(unique(manifest["files"], "path")) > 0
                    and manifest["campaign"]["signature"], f"Invalid skill manifest identity: {bundle_id}")
            skill_count += 1
    require((bundle_count, native_count, p222_count, skill_count) == (139, 6, 1, 2)
            and manifest_raw, "REHOME group coverage mismatch")
    bundle_root = OLD_BUNDLE if mode == "INPUT_VALIDATION" else BUNDLE
    if args.fixture:
        bundle_root = f"{args.fixture}/{bundle_root}"
    members = json.loads(manifest_raw)["files"]
    require(len(members) == 135 and files_under(root, bundle_root) == set(observed_bundle), "Bundle file set mismatch")
    outer = {"README.md", "release_manifest.json", "isolation_receipt.json", "payload/manifest.json"}
    require(set(observed_bundle) == outer | {f"payload/{canonical(key)}" for key in members}, "Manifest member set mismatch")
    for key, wanted in members.items():
        require(observed_bundle[f"payload/{key}"] == {k: wanted[k] for k in ("bytes", "sha256")}, f"Manifest member mismatch: {key}")
    for cycle in CYCLES:
        base = f"output/storage_retention/cycle_closeout_{cycle}"
        plan = raw(root, f"{base}/plan.json")
        binding = raw(root, f"{base}/plan_binding.json")
        for name, data in (("plan", plan), ("plan_binding", binding)):
            require(identity(data)["sha256"] == mapping["frozen_plans"][f"{base}/{name}.json"], f"Frozen {name} changed: {cycle}")
        require(identity(plan)["sha256"] == json.loads(binding)["plan_sha256"], f"Plan binding mismatch: {cycle}")
        same(manifest_raw, json.loads(plan)["protected_files"][HISTORICAL_MANIFEST], f"Historical manifest identity {cycle}")
    refs = 0
    for line in content["s6.jsonl"].splitlines():
        row = json.loads(line)
        if row["action"] != "DELETE_CANDIDATE" or not row["surviving_evidence_path"].startswith(f"{BUNDLE}/"):
            continue
        source = rehome[row["current_surviving_evidence_path"].casefold()]
        require(row["surviving_evidence_path"] == source["target"]
                and row["sha256"] == source["sha256"] and row["logical_bytes"] == source["logical_bytes"],
                f"S6 survivor mapping mismatch: {row['id']}")
        refs += 1
    require(refs == 168, "S6 survivor count mismatch")
    for row in keep:
        same(raw(root, row["path"]), {"bytes": row["logical_bytes"], "sha256": row["sha256"]}, row["path"])
    require(IGNORE in {row["path"] for row in keep}, "Missing retained archive ignore")
    ignore = subprocess.run(["git", "-C", str(root), "check-ignore", "-v", "--no-index", "--",
                             "operations/history/retired-packaging/20261108/.s7-ignore-probe"],
                            check=True, capture_output=True, text=True, encoding="utf-8").stdout
    require(ignore.startswith(IGNORE + ":"), "Archive root ignore did not supply expected match")
    report.update(rehome_checked=148, bundle_files_checked=139, manifest_members_checked=135,
                  s6_survivor_refs_checked=refs, frozen_plans_checked=4, keep_checked=12,
                  junctions_checked=5 if mode != "SIMULATION" else 0,
                  post_rehome_status="PASS" if mode == "POST_REHOME" else "NOT_RUN")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("INPUT_VALIDATION", "SIMULATION", "TARGET_VALIDATION", "POST_REHOME"), required=True)
    parser.add_argument("--package-sha256", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--receipt", required=True)
    for arg in ("fixture", "approval", "journal", "states", "prep-package", "independent-review-verdict", "target-receipt", "run-id"):
        parser.add_argument(f"--{arg}")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        receipt_root = RECEIPTS if args.mode in ("TARGET_VALIDATION", "POST_REHOME") else f"{PREP}/receipts"
        require(canonical(args.receipt).startswith(f"{receipt_root}/"), "Receipt outside permitted root")
        if args.mode in ("TARGET_VALIDATION", "POST_REHOME"):
            require(args.run_id and "/" not in canonical(args.run_id), "Missing or invalid run_id")
            stage_path(args.receipt, args.run_id)
        receipt = checked(root, args.receipt, "leaf")
        require(receipt.suffix == ".json", "Expected JSON receipt")
        report = {"schema_version": 2, "mode": args.mode, "v2_package_sha256": args.package_sha256,
                  "status": "FAIL", "post_rehome_status": "NOT_RUN", "target_validation_status": "NOT_RUN"}
        with receipt.open("x", encoding="utf-8") as stream:
            try:
                verify(root, args, report)
                report["status"] = f"PASS_{args.mode}"
                if args.mode == "TARGET_VALIDATION":
                    report["target_validation_status"] = "PASS"
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
                report["error"] = str(error)
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["status"] != "FAIL" else 1
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
