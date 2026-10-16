"""Read-only ADB probe and explicit pulls of this game's files; no device mutations."""
import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["probe", "pull"])
    parser.add_argument("--adb", type=Path, default=Path("tools/platform-tools/adb.exe"))
    parser.add_argument("--serial")
    parser.add_argument("--package", default="com.sega.chainchronicle")
    parser.add_argument("--output", type=Path, default=Path("output/phone"))
    parser.add_argument("--remote", action="append", default=[])
    parser.add_argument("--plan", type=Path, help="JSON with explicit paths selected from the probe inventory")
    parser.add_argument("--method", choices=["pull", "exec-out"], default="pull")
    parser.add_argument("--snapshot", default=datetime.now(timezone(timedelta(hours=8))).strftime("phone_%Y%m%d_%H%M%S"))
    args = parser.parse_args()
    if args.plan:
        args.remote.extend(json.loads(args.plan.read_text(encoding="utf-8"))["paths"])
    if not re.fullmatch(r"[A-Za-z0-9_.]+", args.package):
        parser.error("Invalid package name")
    adb = str(args.adb.resolve())

    def run(argv, timeout=60):
        try:
            proc = subprocess.run([adb, *argv], capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            return {"exit_code": 124, "stdout": (exc.stdout or b"").decode("utf-8", "replace").strip(),
                    "stderr": f"ADB operation timed out after {timeout} seconds; partial output retained"}
        return {"exit_code": proc.returncode, "stdout": proc.stdout.decode("utf-8", "replace").strip(),
                "stderr": proc.stderr.decode("utf-8", "replace").strip()}

    devices = run(["devices"])
    available = [line.split() for line in devices["stdout"].splitlines()[1:] if line.strip()]
    ready = [row[0] for row in available if len(row) >= 2 and row[1] == "device"]
    if args.serial:
        ready = [serial for serial in ready if serial == args.serial]
    if len(ready) != 1:
        summary = {"status": "NO_SINGLE_AUTHORIZED_DEVICE", "device_count": len(available),
                   "ready_count": len(ready), "states": [r[1] for r in available if len(r)>1],
                   "adb_exit_code": devices["exit_code"],
                   "adb_error": devices["stderr"]}
        if devices["exit_code"]:
            summary["status"] = "ADB_QUERY_FAILED"
        save_json(args.output / "connection.json", summary)
        print(json.dumps(summary))
        return 3
    serial = ready[0]

    def shell(command):
        return run(["-s", serial, "shell", command])

    user_result = shell("am get-current-user")
    user = user_result["stdout"]
    if not user.isdigit():
        raise RuntimeError("Could not identify Android user")
    apk_result = shell(f"pm path --user {user} {args.package}")
    apk_paths = [line[len("package:"):] for line in apk_result["stdout"].splitlines() if line.startswith("package:")]
    if not apk_paths:
        save_json(args.output / "probe.json", {"status": "PACKAGE_NOT_FOUND_FOR_CURRENT_USER", "user": user,
                                              "package": args.package, "pm_result": apk_result})
        return 4
    roots = [f"/storage/emulated/{user}/Android/data/{args.package}/files",
             f"/storage/emulated/{user}/Android/data/{args.package}/cache",
             f"/storage/emulated/{user}/Android/obb/{args.package}"]
    if args.mode == "probe":
        package_info = shell(f"dumpsys package {args.package}")
        versions = [line.strip() for line in package_info["stdout"].splitlines()
                    if re.match(r"\s*(versionCode=|versionName=)", line)]
        result = {"status": "PROBED", "package": args.package, "android_user": int(user),
                  "device_alias": hashlib.sha256(serial.encode()).hexdigest()[:12],
                  "android_version": shell("getprop ro.build.version.release")["stdout"],
                  "android_sdk": shell("getprop ro.build.version.sdk")["stdout"],
                  "version_lines": versions, "apk_paths": apk_paths,
                  "private_storage_status": "NOT_CHECKED", "paths": []}
        inventory = []
        for root in roots:
            quoted = shlex.quote(root)
            listing = shell(f"ls -ld {quoted}")
            if listing["exit_code"] != 0:
                error = listing["stderr"] or listing["stdout"]
                state = "PERMISSION_DENIED" if "Permission denied" in error else "NOT_FOUND" if "No such file" in error else "ERROR"
                result["paths"].append({"path": root, "status": state, "result": listing})
                continue
            scan = shell(f"find {quoted} -type f -print0 | xargs -0 -r -n 100 stat -c '%s|%n'")
            rows = []
            for line in scan["stdout"].splitlines():
                size, sep, path = line.partition("|")
                if sep and size.isdigit() and path.startswith(root + "/"):
                    row = {"path": path, "size": int(size), "root": root,
                           "candidate_by_name": bool(re.search(r"master|manifest|catalog|index|version|\.db$|\.scr$|chronicle", path[len(root):], re.I))}
                    inventory.append(row)
                    rows.append(row)
            state = "LISTED" if scan["exit_code"] == 0 else "PARTIAL_LISTING"
            if not rows and scan["exit_code"] == 0:
                state = "EMPTY"
            result["paths"].append({"path": root, "status": state, "files": len(rows),
                                    "bytes": sum(r["size"] for r in rows), "exit_code": scan["exit_code"],
                                    "stderr": scan["stderr"]})
        save_json(args.output / "probe.json", result)
        args.output.mkdir(parents=True, exist_ok=True)
        with (args.output / "inventory.jsonl").open("w", encoding="utf-8") as out:
            for row in inventory:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(json.dumps({"status": result["status"], "package": args.package,
                          "version_lines": versions, "paths": result["paths"],
                          "named_candidates": sum(r["candidate_by_name"] for r in inventory)}, ensure_ascii=False, indent=2))
        return 0 if all(p["status"] in ("LISTED", "EMPTY", "NOT_FOUND") for p in result["paths"]) else 5
    if not args.remote:
        parser.error("pull requires one or more explicit --remote paths after reviewing the inventory")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.snapshot):
        parser.error("Invalid snapshot id")
    dest_root = Path("raw") / args.snapshot
    if dest_root.exists():
        raise FileExistsError("Snapshot already exists; choose a new id, never overwrite a collected snapshot")
    rows = []
    for remote in args.remote:
        path = PurePosixPath(remote)
        if ".." in path.parts or not (remote in apk_paths or any(remote == root or remote.startswith(root+"/") for root in roots)):
            raise ValueError(f"Remote path outside verified game paths: {remote}")
    dest_root.mkdir(parents=True)
    for index, remote in enumerate(args.remote):
        dest = dest_root / f"item_{index:02d}" / PurePosixPath(remote).name
        dest.parent.mkdir(parents=True)
        if args.method == "exec-out":
            size_result = shell(f"stat -c '%s' {shlex.quote(remote)}")
            if size_result["exit_code"] != 0 or not size_result["stdout"].isdigit():
                raise ValueError("exec-out requires an existing regular file with a known size")
            expected_size = int(size_result["stdout"])
            with dest.open("wb") as out:
                try:
                    proc = subprocess.run([adb, "-s", serial, "exec-out", f"cat {shlex.quote(remote)}"],
                                          stdout=out, stderr=subprocess.PIPE, timeout=3600)
                    pull = {"exit_code": proc.returncode, "stderr": proc.stderr.decode("utf-8", "replace")}
                except subprocess.TimeoutExpired:
                    pull = {"exit_code": 124, "stderr": "binary file copy timed out; partial file preserved"}
            if dest.stat().st_size != expected_size:
                pull["exit_code"] = pull["exit_code"] or 7
                pull["stderr"] += f"; size mismatch expected {expected_size}, received {dest.stat().st_size}"
        else:
            pull = run(["-s", serial, "pull", remote, str(dest.resolve())], timeout=3600)
        row = {"remote": remote, "local": dest.as_posix(), "exit_code": pull["exit_code"],
               "status": "COPIED" if pull["exit_code"] == 0 else "COPY_FAILED",
               "stderr": pull["stderr"], "method": args.method}
        files = [dest] if dest.is_file() else list(dest.rglob("*")) if dest.is_dir() else []
        row["file_count"] = sum(f.is_file() for f in files)
        row["bytes"] = sum(f.stat().st_size for f in files if f.is_file())
        if dest.is_file():
            row["sha256_local"] = hashlib.sha256(dest.read_bytes()).hexdigest()
        rows.append(row)
        save_json(dest_root / "acquisition.json", {"package": args.package, "user": int(user),
                                                 "version_pairing": "CHECK_PROBE_AND_APK", "items": rows,
                                                 "scope": "explicit listed paths only; not full game cache"})
        print(json.dumps({k: v for k, v in row.items() if k != "stderr"}, ensure_ascii=False), flush=True)
    return 0 if all(r["exit_code"] == 0 for r in rows) else 6


if __name__ == "__main__":
    sys.exit(main())
