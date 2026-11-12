"""Read-only gates for exactly two batch2 directories and five v2 junctions.

No payload mutation, mkdir, rename, move, deletion, imports of business modules,
or command execution. Only an explicitly selected receipt under tooling may be
created. Native PowerShell mutations are separately listed in the bound runbook.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

EVIDENCE = Path("docs/project-layout/20261108-directory-batch2-ready-v1")
INVENTORY_SHA = "e2aec985a2c7a8683bd786e9e37c1b573f3d8eabbde831dd1ada1511e45930c6"
SUFFIX = ".batch2-20261108-"
CYCLES = ("C14", "C15", "C16", "C17", "C18")
REPARSE = 0x400
MOUNT_TAG = 0xa0000003


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalized(path):
    text = os.fspath(path)
    if text.startswith("\\\\?\\"):
        text = text[4:]
    return os.path.normcase(os.path.abspath(text))


def inside(repo, relative):
    rel = Path(relative)
    require(not rel.is_absolute() and ".." not in rel.parts, "Unsafe relative path")
    path = repo / rel
    path.relative_to(repo)
    return path


def ordinary(path, directory):
    s = path.lstat()
    require(not getattr(s, "st_file_attributes", 0) & REPARSE, "Reparse forbidden: " + str(path))
    require(stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode), "Wrong type: " + str(path))
    return s


def exists_lstat(path):
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


def ancestors(path, missing_ok=False):
    result = []
    absent = False
    for p in reversed((path, *path.parents)):
        if absent or not exists_lstat(p):
            require(missing_ok, "Missing ancestor: " + str(p))
            absent = True
            result.append({"path": str(p), "exists": False})
        else:
            s = ordinary(p, True)
            result.append({"path": str(p), "dev": s.st_dev, "ino": s.st_ino, "exists": True})
    return result


def vacant(path):
    info = ancestors(path.parent, missing_ok=True)
    require(not exists_lstat(path), "Destination/name already exists (including dangling reparse): " + str(path))
    return info


def identity(s):
    return {"dev": s.st_dev, "ino": s.st_ino, "bytes": s.st_size,
            "mtime_ns": s.st_mtime_ns, "nlink": s.st_nlink}


def verify_tree(root, expected, through_alias=False, hash_paths=None):
    if through_alias:
        ancestors(root.parent)
    else:
        ancestors(root)
    found_files = {}
    found_dirs = {}
    stack = [(root, ".")]
    while stack:
        folder, relative = stack.pop()
        # Top junction was verified separately, ordinary descendants remain strict.
        s = folder.stat() if through_alias and relative == "." else ordinary(folder, True)
        found_dirs[relative] = {"dev": s.st_dev, "ino": s.st_ino}
        with os.scandir(folder) as entries:
            for entry in entries:
                child = Path(entry.path)
                rel = entry.name if relative == "." else relative + "/" + entry.name
                # Windows DirEntry.stat may report dev/ino/nlink as zero; use lstat
                # for the same real file identity fields as the frozen inventory.
                before = child.lstat()
                require(not getattr(before, "st_file_attributes", 0) & REPARSE, "Nested reparse forbidden: " + str(child))
                if stat.S_ISDIR(before.st_mode):
                    stack.append((child, rel))
                else:
                    require(stat.S_ISREG(before.st_mode), "Nonregular payload: " + str(child))
                    digest = sha(child) if hash_paths is None or rel in hash_paths else None
                    after = child.lstat()
                    require(identity(before) == identity(after), "File changed during hash: " + str(child))
                    found_files[rel] = identity(after)
                    if digest is not None:
                        found_files[rel]["sha256"] = digest
    wanted_files = {x["path"]: {k: x[k] for k in ("dev", "ino", "bytes", "mtime_ns", "nlink")} for x in expected["files"]}
    for x in expected["files"]:
        if hash_paths is None or x["path"] in hash_paths:
            wanted_files[x["path"]]["sha256"] = x["sha256"]
    wanted_dirs = {x["path"]: {"dev": x["dev"], "ino": x["ino"]} for x in expected["directories"]}
    require(found_files == wanted_files, "Exact payload membership/content/identity differs: " + str(root))
    require(found_dirs == wanted_dirs, "Exact directory membership/identity differs: " + str(root))
    return {"root": str(root), "files": len(found_files), "bytes": sum(x["bytes"] for x in found_files.values()),
            "directory_count": len(found_dirs), "all_file_ids_and_metadata_match": True,
            "content_sha_checked": sum("sha256" in x for x in found_files.values()),
            "full_payload_sha_verified": hash_paths is None}


def alias_path(repo, expected, role):
    path = inside(repo, expected["path"])
    return path if role == "formal" else path.with_name(path.name + SUFFIX + role)


def verify_alias(repo, inventory, cycle, role, target, content=True, created=None):
    expected = next(x for x in inventory["v2_aliases"] if x["cycle"] == cycle)
    path = alias_path(repo, expected, role)
    ancestors(path.parent)
    s = path.lstat()
    require(getattr(s, "st_file_attributes", 0) & REPARSE and getattr(s, "st_reparse_tag", None) == MOUNT_TAG,
            "Expected NTFS mount-point junction: " + str(path))
    target_path = inside(repo, inventory["directories"][1]["source" if target == "old" else "target"])
    raw_target = os.readlink(path)
    require(normalized(raw_target) == normalized(target_path), "Wrong junction target: " + str(path))
    if target == "old":
        require((s.st_dev, s.st_ino) == (expected["dev"], expected["ino"]), "Old junction identity changed: " + str(path))
        require(raw_target == expected["target"], "Old raw junction target changed: " + str(path))
    else:
        require((s.st_dev, s.st_ino) != (expected["dev"], expected["ino"]), "New junction reuses old identity unexpectedly")
        if created:
            require((s.st_dev, s.st_ino) == (created["dev"], created["ino"]), "next->formal identity not retained")
    result = {"cycle": cycle, "role": role, "path": str(path), "dev": s.st_dev, "ino": s.st_ino,
              "tag": hex(s.st_reparse_tag), "raw_target": raw_target, "content_checked": content}
    if content:
        ancestors(target_path)
        result["tree"] = verify_tree(path, inventory["directories"][1], through_alias=True,
                                     hash_paths={"decode_report.json", "tables.csv", "decoded/helper.data5.json.raw"})
    return result


def load_inventory(repo):
    path = repo / EVIDENCE / "source-inventory.json"
    ancestors(path.parent)
    ordinary(path, False)
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == INVENTORY_SHA, "Frozen source inventory SHA mismatch")
    value = json.loads(raw)
    require(value["files"] == 98 and value["bytes"] == 122302114, "Wrong inventory totals")
    require([(x["source"], x["target"], x["count"], x["bytes"]) for x in value["directories"]] == [
        ("output/single", "projects/unpack/history/single", 3, 4131868),
        ("output/cache_full_20261015_v2", "projects/unpack/data/cache/cache_full_20261015_v2", 95, 118170246)], "Wrong move scope")
    require(tuple(x["cycle"] for x in value["v2_aliases"]) == CYCLES, "Wrong junction scope")
    return value


def load_bindings(repo):
    path = repo / EVIDENCE / "tooling/bindings.json"
    ancestors(path.parent)
    ordinary(path, False)
    raw = path.read_bytes()
    binding = json.loads(raw)
    require(set(binding["code_candidates"]) == {"scripts/decode_cache_snapshot.py", "scripts/verify_cache_snapshot.py"}, "Both code candidates must be bound")
    for relative, expected in binding["files"].items():
        p = inside(repo, relative)
        ancestors(p.parent)
        ordinary(p, False)
        require(sha(p) == expected, "Bound code/manifest changed: " + relative)
    return binding, hashlib.sha256(raw).hexdigest()


def protected_observations(repo):
    source = repo / EVIDENCE / "protected-before.json"
    baseline = json.loads(source.read_text(encoding="utf-8"))["files"]
    result = []
    for relative, before in baseline.items():
        p = inside(repo, relative)
        ancestors(p.parent)
        s = ordinary(p, False)
        observed = {**identity(s), "sha256": sha(p)}
        frozen = relative.startswith("output/storage_retention/")
        if frozen:
            require(observed["sha256"] == before["sha256"], "Frozen protection changed: " + relative)
        result.append({"path": relative, "current": observed, "baseline_sha256": before["sha256"],
                       "matches_baseline": observed["sha256"] == before["sha256"],
                       "policy": "FROZEN_NO_CHANGE" if frozen else "OBSERVE_OWNER_MAY_LEGITIMATELY_CHANGE"})
    return result


def authorization(repo, args, inventory, binding_sha):
    require(args.authorization and args.authorization_sha256, "Future gate requires separately approved authorization receipt + its SHA")
    path = Path(args.authorization).absolute()
    path.relative_to(repo / EVIDENCE / "tooling")
    ancestors(path.parent)
    ordinary(path, False)
    auth_raw = path.read_bytes()
    require(hashlib.sha256(auth_raw).hexdigest() == args.authorization_sha256, "Authorization receipt SHA mismatch")
    auth = json.loads(auth_raw)
    require(auth["scope"] == "batch2-20261108" and auth["user_physical_authorization"] is True,
            "No separate explicit user physical authorization recorded")
    require(bool(auth["user_authorization_reference"].strip()), "Missing user authorization evidence reference")
    require(auth["bindings_sha256"] == binding_sha and auth["inventory_sha256"] == INVENTORY_SHA, "Authorization binding mismatch")
    preflight_path = inside(repo, auth["source_preflight_receipt_path"])
    preflight_path.relative_to(repo / EVIDENCE / "tooling")
    ancestors(preflight_path.parent)
    ordinary(preflight_path, False)
    preflight_raw = preflight_path.read_bytes()
    require(hashlib.sha256(preflight_raw).hexdigest() == auth["source_preflight_receipt_sha256"], "Full source preflight receipt changed")
    preflight = json.loads(preflight_raw)
    require(preflight["read_only_pass"] is True and preflight["command"] == "preflight" and preflight["bindings_sha256"] == binding_sha,
            "Preflight failed or bound to different code/manifest")
    require([x["content_sha_checked"] for x in preflight["roots"]] == [3, 95], "Preflight must hash all98 sources")
    handoff = auth["one_owner_handoff"]
    require(handoff["confirmed"] is True and handoff["reuse_scripts_approved"] is True and handoff["write_domain_released"] is True,
            "Owner handoff/decoder approval/write-domain release missing")
    require(handoff["roots_no_writers"] == [x["source"] for x in inventory["directories"]], "Both roots must be released")
    require(handoff["v2_alias_window_released"] == [x["path"] for x in inventory["v2_aliases"]], "Five alias scoped windows must be released")
    require(handoff["issuer"].strip() and handoff["reference"].strip(), "Owner handoff evidence missing")
    start = dt.datetime.fromisoformat(handoff["window_start_utc"])
    end = dt.datetime.fromisoformat(handoff["window_end_utc"])
    require(start.tzinfo is not None and end.tzinfo is not None and start <= dt.datetime.now(dt.timezone.utc) <= end,
            "Owner window absent/not current/expired")
    preflight_time = dt.datetime.fromisoformat(preflight["utc"])
    require(preflight_time.tzinfo is not None and start <= preflight_time <= end,
            "Full98 source preflight must be fresh within this owner window; retain old preparation receipt")
    require(auth["keep_previous_junctions"] is True and auth["resume_new_formal_in_same_scope"] is True,
            "Retained previous aliases / scoped completion of new formal not approved")
    return args.authorization_sha256


def roots(repo, inventory, locations, full_indices=()):
    result = []
    for index, (expected, location) in enumerate(zip(inventory["directories"], locations)):
        actual = inside(repo, expected[location])
        missing = inside(repo, expected["target" if location == "source" else "source"])
        require(actual.drive.lower() == repo.drive.lower() == missing.drive.lower(), "Cross-volume/root drive forbidden")
        result.append(verify_tree(actual, expected, hash_paths=None if index in full_indices else set()))
        vacant(missing)
    return result


def progression(repo, inventory, current=None, phase="before", created=None):
    result = []
    selected = CYCLES.index(current) if current else len(CYCLES)
    for index, cycle in enumerate(CYCLES):
        expected = inventory["v2_aliases"][index]
        completed = index < selected or (index == selected and phase == "formal")
        if completed:
            result.append(verify_alias(repo, inventory, cycle, "formal", "new", created=created if cycle == current else None))
            result.append(verify_alias(repo, inventory, cycle, "previous", "old", content=False))
            vacant(alias_path(repo, expected, "next"))
        elif index == selected and phase == "previous":
            vacant(alias_path(repo, expected, "formal"))
            result.append(verify_alias(repo, inventory, cycle, "previous", "old", content=False))
            result.append(verify_alias(repo, inventory, cycle, "next", "new", created=created))
        else:
            result.append(verify_alias(repo, inventory, cycle, "formal", "old", content=False))
            vacant(alias_path(repo, expected, "previous"))
            if index == selected and phase == "next":
                result.append(verify_alias(repo, inventory, cycle, "next", "new"))
            else:
                vacant(alias_path(repo, expected, "next"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "gate", "check-alias", "check-root"))
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--authorization-sha256")
    parser.add_argument("--stage", choices=("before-move-single", "after-move-single", "before-move-v2", "after-move-v2", "before-alias-next", "after-alias-next", "after-alias-previous", "after-alias-formal", "verify"))
    parser.add_argument("--cycle", choices=CYCLES)
    parser.add_argument("--role", choices=("formal", "next", "previous"))
    parser.add_argument("--target", choices=("old", "new"))
    parser.add_argument("--root", choices=("single", "v2"))
    parser.add_argument("--location", choices=("source", "target"))
    parser.add_argument("--identity-only", action="store_true")
    parser.add_argument("--created-receipt", type=Path)
    args = parser.parse_args()
    repo = args.repo.absolute()
    result = {"schema_version": 1, "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "command": args.command,
              "stage": args.stage, "cycle": args.cycle, "read_only_pass": False,
              "physical_mutations_performed": 0, "gate_is_not_user_authorization": True}
    try:
        require(os.name == "nt" and repo.drive.lower() == "e:", "Production checker requires Windows E: repository")
        ancestors(repo)
        inventory = load_inventory(repo)
        binding, binding_sha = load_bindings(repo)
        result["bindings_sha256"] = binding_sha
        result["inventory_sha256"] = INVENTORY_SHA
        result["protected_observations"] = protected_observations(repo)
        code_states = {}
        for relative, code in binding["code_candidates"].items():
            live = sha(repo / relative)
            require(live in (code["live_before_sha256"], code["candidate_sha256"]), "Unreviewed live code: " + relative)
            code_states[relative] = {"live_sha256": live, "candidate_sha256": code["candidate_sha256"],
                                     "state": "CANDIDATE_APPLIED" if live == code["candidate_sha256"] else "BEFORE_APPLY"}
        result["code_states"] = code_states
        if args.command == "preflight":
            result["roots"] = roots(repo, inventory, ("source", "source"), full_indices=(0, 1))
            result["aliases"] = []
            for expected in inventory["v2_aliases"]:
                cycle = expected["cycle"]
                result["aliases"].append(verify_alias(repo, inventory, cycle, "formal", "old", content=False))
                for role in ("next", "previous"):
                    vacant(alias_path(repo, expected, role))
            result["execution_authorized"] = False
        else:
            auth_sha = authorization(repo, args, inventory, binding_sha)
            result["authorization_sha256"] = auth_sha
            require(all(x["state"] == "CANDIDATE_APPLIED" for x in code_states.values()),
                    "Both live scripts must equal approved candidate SHAs before physical steps")
            result["authorization_receipt_validated_not_independently_granted"] = True
            if args.command == "check-root":
                require(args.root and args.location, "check-root needs --root and --location")
                selected = inventory["directories"][0 if args.root == "single" else 1]
                result["root"] = verify_tree(inside(repo, selected[args.location]), selected)
                vacant(inside(repo, selected["target" if args.location == "source" else "source"]))
            elif args.command == "check-alias":
                require(args.cycle and args.role and args.target, "check-alias needs cycle/role/target")
                require(not args.identity_only or args.target == "old", "Identity-only is only allowed for retained old junctions")
                result["alias"] = verify_alias(repo, inventory, args.cycle, args.role, args.target, content=not args.identity_only)
            else:
                require(args.stage, "gate needs --stage")
                if args.stage == "before-move-single":
                    result["roots"] = roots(repo, inventory, ("source", "source"))
                    result["aliases"] = progression(repo, inventory, "C14", "before")
                elif args.stage in ("after-move-single", "before-move-v2"):
                    result["roots"] = roots(repo, inventory, ("target", "source"), full_indices=(0,) if args.stage == "after-move-single" else ())
                    result["aliases"] = progression(repo, inventory, "C14", "before")
                else:
                    result["roots"] = roots(repo, inventory, ("target", "target"), full_indices=(1,) if args.stage == "after-move-v2" else ())
                    if args.stage == "after-move-v2":
                        result["aliases"] = progression(repo, inventory, "C14", "before")
                    elif args.stage == "verify":
                        result["aliases"] = progression(repo, inventory)
                    else:
                        require(args.cycle, "Alias gate needs cycle")
                        phase = {"before-alias-next": "before", "after-alias-next": "next", "after-alias-previous": "previous", "after-alias-formal": "formal"}[args.stage]
                        created = None
                        if phase in ("previous", "formal"):
                            require(args.created_receipt, "Need retained after-next receipt to bind next->formal file ID")
                            created_path = args.created_receipt.absolute()
                            created_path.relative_to(repo / EVIDENCE / "tooling")
                            ancestors(created_path.parent)
                            ordinary(created_path, False)
                            created_raw = created_path.read_bytes()
                            receipt = json.loads(created_raw)
                            require(receipt["read_only_pass"] is True and receipt["stage"] == "after-alias-next" and receipt["cycle"] == args.cycle,
                                    "Wrong/failed created receipt")
                            require(receipt["bindings_sha256"] == binding_sha and receipt["authorization_sha256"] == auth_sha,
                                    "Created receipt binding/window mismatch")
                            created = next(x for x in receipt["aliases"] if x["cycle"] == args.cycle and x["role"] == "next")
                            result["created_receipt_sha256"] = hashlib.sha256(created_raw).hexdigest()
                        result["aliases"] = progression(repo, inventory, args.cycle, phase, created)
        if args.command != "preflight":
            authorization(repo, args, inventory, binding_sha)
        result["read_only_pass"] = True
        result["limitations"] = ["No whole-machine writer/handle proof or atomic check/mutation lock; owner scoped window remains required.",
                                 "Two sequential directory renames are not an atomic junction exchange.",
                                 "Live owner-controlled mainline observations may change legitimately; checker never locks or edits them."]
    except (ValueError, OSError, KeyError, StopIteration, TypeError) as error:
        result["error"] = str(error)
    if args.receipt:
        receipt = args.receipt.absolute()
        receipt.relative_to(repo / EVIDENCE / "tooling")
        ancestors(receipt.parent)
        require(not exists_lstat(receipt), "Receipt exists; never overwrite prior evidence")
        with open(receipt, "x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
    print(json.dumps({k: v for k, v in result.items() if k != "protected_observations"}, ensure_ascii=True))
    return 0 if result["read_only_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
