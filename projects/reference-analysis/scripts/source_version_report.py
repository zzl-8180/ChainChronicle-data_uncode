"""B01-R fixed historical source identity/structure report; standard library only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


SOURCES = (
    ("old", "其他人的参考/claude_cc_site_pages/param_table.json",
     "4a92c6220d1e1a11403bf4ff51223b91f2c4e3091a06a1f92e78ef315d815929"),
    ("first_20261023", "其他人的参考/claude_cc_site_pages 20261023/param_table.json",
     "bb3d33e133c9d746afc28a35f043575f11f3391f57d465249b344077c65e5e58"),
)


def no_reparse(path):
    """Check lexical ancestors before resolve can hide a Windows junction."""
    for node in (path, *path.parents):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"reparse/symlink path forbidden: {node}")


def absolute(path):
    return Path(os.path.abspath(path))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_source(root, source):
    identity, relative, expected = source
    path = root / relative
    no_reparse(path)
    raw = path.read_bytes()
    actual = digest(raw)
    if actual != expected:
        raise ValueError(f"source hash mismatch: {relative}; expected {expected}; actual {actual}")
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("rows"), list):
        raise ValueError(f"expected object with rows array: {relative}")
    keys = []
    for row in data["rows"]:
        key = (row["table"], row["type"], row["slot"])
        if not (isinstance(key[0], str) and type(key[1]) is int and isinstance(key[2], str)):
            raise ValueError(f"invalid (table,type,slot) key: {relative}")
        keys.append(key)
    unique = set(keys)
    if len(unique) != len(keys):
        raise ValueError(f"duplicate keys in source: {relative}")
    return {"id": identity, "path": relative, "bytes": len(raw), "sha256": actual,
            "top_level_keys": sorted(data), "rows": len(keys), "unique_keys": len(unique),
            "duplicate_keys": len(keys) - len(unique)}, unique


def generate(root, out):
    no_reparse(root)
    no_reparse(out)
    if not root.is_dir():
        raise ValueError("root must be an existing directory")
    report_root = root / "projects/reference-analysis/reports"
    if out.parent != report_root or out.name in ("", ".", ".."):
        raise ValueError("out must be a direct new version directory under root/projects/reference-analysis/reports")
    if out.exists():
        raise FileExistsError(f"output already exists; preserved: {out}")
    sources = [load_source(root, item) for item in SOURCES]
    before, after = (item[1] for item in sources)
    report = {
        "schema_version": 1, "track": "B01-R", "report_kind": "fixed_external_source_structure",
        "scope": "Two historical external param_table JSON identities, structure and (table,type,slot) key sets only.",
        "limitations": ["Not game-value, conversion, translation or rule-semantic validation.",
                        "No current pages/rules/reader inputs; no external code executed.",
                        "Full rows and parameter values are not included; sources remain external read-only inputs.",
                        "This report does not establish B01-D or complete release qualification."],
        "sources": [item[0] for item in sources],
        "key_comparison": {"from": SOURCES[0][0], "to": SOURCES[1][0],
                           "common": len(before & after), "added": len(after - before),
                           "removed": len(before - after),
                           "added_keys": sorted(after - before), "removed_keys": sorted(before - after)},
    }
    # Recheck exact sources before the first write; source drift is a hard failure.
    for source in report["sources"]:
        path = root / source["path"]
        no_reparse(path)
        if digest(path.read_bytes()) != source["sha256"]:
            raise ValueError(f"source changed during report: {source['path']}")
    no_reparse(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# B01-R 固定历史来源结构报告", "", report["scope"], "",
             "仅核来源身份、JSON结构与键集合；不判断数值、换算、译文或游戏语义正确性。", "",
             "[机器可读报告](report.json)", "", "固定只读来源：", ""]
    for source in report["sources"]:
        relative_link = Path(os.path.relpath(root / source["path"], out)).as_posix()
        from urllib.parse import quote
        lines.append(f"- [{source['path']}]({quote(relative_link)})：{source['bytes']} 字节，{source['rows']} 行，SHA-256 `{source['sha256']}`。")
    lines += ["", "输入原件不复制、不修改；共同键只证明键相同，不证明对应行内容或含义相同。",
              "", "本试点不读取当前技能规则、角色页、账本或阅读器，不执行第三方／历史发行脚本。",
              "B01-R与B01-D分别验收；本报告不构成完整发行验收。", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = generate(absolute(args.root), absolute(args.out))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"track": "B01-R", "sources": len(report["sources"]),
                      "key_comparison": {k: v for k, v in report["key_comparison"].items() if not k.endswith("_keys")}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
