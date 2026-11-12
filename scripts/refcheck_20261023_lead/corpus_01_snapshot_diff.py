# -*- coding: utf-8 -*-
"""快照差异：新版1 vs 新版2(嵌套 claude_cc_site_pages) vs 旧版基线。

只读输入，输出 work/refcheck_20261023_lead/corpus/snapshot_diff.json + file_diff.jsonl
用法: .venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/corpus_01_snapshot_diff.py
"""
import os, sys, json, hashlib, time

ROOT = r"E:\代码项目\锁链战记数据解包"
REF = os.path.join(ROOT, "其他人的参考")
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead", "corpus")

TREES = {
    "new1": os.path.join(REF, "claude_cc_site_pages 20261023"),
    "new2": os.path.join(REF, "claude_cc_site_pages_给GPT_20261023", "claude_cc_site_pages"),
    "old":  os.path.join(REF, "claude_cc_site_pages"),
}

SKIP_HASH_LIMIT = 8 * 1024 * 1024  # 超过 8MB 不算哈希（本快照无此情况，防御）


def sha256(path, limit=SKIP_HASH_LIMIT):
    h = hashlib.sha256()
    total = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            total += len(b)
            if total > limit:
                return None
            h.update(b)
    return h.hexdigest()


def walk_top(tree):
    """返回 {relpath: (size, mtime, sha256_or_None)}；assets/ 只统计不哈希。"""
    out = {}
    for root, dirs, files in os.walk(tree):
        rel_root = os.path.relpath(root, tree)
        if rel_root == ".":
            rel_root = ""
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.normpath(os.path.join(rel_root, fn)).replace("\\", "/")
            try:
                st = os.stat(full)
            except OSError:
                continue
            h = None
            if not rel.startswith("assets/") and st.st_size <= SKIP_HASH_LIMIT:
                try:
                    h = sha256(full)
                except OSError:
                    h = None
            out[rel] = {"size": st.st_size, "mtime": int(st.st_mtime), "sha256": h}
    return out


def tree_summary(m):
    total = sum(v["size"] for v in m.values())
    return {
        "file_count": len(m),
        "total_bytes": total,
        "total_mb": round(total / 1048576.0, 2),
        "mtime_min": min((v["mtime"] for v in m.values()), default=0),
        "mtime_max": max((v["mtime"] for v in m.values()), default=0),
    }


def classify(rel):
    if rel.startswith("assets/"):
        return "assets"
    if rel.startswith("cards/"):
        return "cards"
    if rel.startswith("scripts/"):
        return "scripts"
    if rel.startswith("translations/"):
        return "translations"
    return "root"


def compare(a_name, b_name, A, B):
    """A,B: dict rel->meta。返回差异列表。"""
    rows = []
    only_a = sorted(set(A) - set(B))
    only_b = sorted(set(B) - set(A))
    common = sorted(set(A) & set(B))
    for rel in common:
        a, b = A[rel], B[rel]
        same_hash = a["sha256"] is not None and b["sha256"] is not None and a["sha256"] == b["sha256"]
        if same_hash:
            continue
        rows.append({
            "kind": classify(rel),
            "rel": rel,
            "status": "same_path_diff_content",
            "size_a": a["size"], "size_b": b["size"],
            "mtime_a": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a["mtime"])),
            "mtime_b": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(b["mtime"])),
            "sha_a": (a["sha256"] or "")[:16], "sha_b": (b["sha256"] or "")[:16],
            "delta": b["size"] - a["size"],
        })
    for rel in only_a:
        rows.append({"kind": classify(rel), "rel": rel, "status": "only_in_" + a_name,
                     "size_a": A[rel]["size"], "size_b": 0, "delta": -A[rel]["size"]})
    for rel in only_b:
        rows.append({"kind": classify(rel), "rel": rel, "status": "only_in_" + b_name,
                     "size_a": 0, "size_b": B[rel]["size"], "delta": B[rel]["size"]})
    return rows


def aggregate(rows):
    """按 kind+status 聚合计数与字节。"""
    agg = {}
    for r in rows:
        k = r["kind"] + "|" + r["status"]
        e = agg.setdefault(k, {"count": 0, "bytes_a": 0, "bytes_b": 0})
        e["count"] += 1
        e["bytes_a"] += r.get("size_a", 0)
        e["bytes_b"] += r.get("size_b", 0)
    return agg


KEY_FILES = [
    "HANDOFF.md", "index.html", "index_unpack.html", "param_table.json", "param_table.csv",
    "param_table.html", "leader_condition_map.json", "match_result.json", "manual_matches.json",
    "not_on_site.csv", "NUMBER_RULES.md", "UPDATE_追加指令.md", "给GPT_请先读我.md", "打开页面.bat",
    "cards/index.json", "code_mappings.json", "confirmed_4_5.json", "confirm_matches.html",
]


def key_files(m):
    out = {}
    for rel in KEY_FILES:
        if rel in m:
            v = m[rel]
            out[rel] = {"size": v["size"], "mtime": v["mtime"],
                        "mtime_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["mtime"])),
                        "sha256_16": (v["sha256"] or "")[:16]}
        else:
            out[rel] = None
    return out


def dir_breakdown(m):
    """按相对路径的首段+扩展名聚合文件数与字节。"""
    b = {}
    for rel, v in m.items():
        parts = rel.split("/")
        head = parts[0] if len(parts) > 1 else "(root)"
        ext = os.path.splitext(rel)[1].lower() or "(noext)"
        k = head + "|" + ext
        e = b.setdefault(k, {"count": 0, "bytes": 0})
        e["count"] += 1
        e["bytes"] += v["size"]
    return dict(sorted(b.items(), key=lambda kv: -kv[1]["bytes"]))


def main():
    os.makedirs(OUT, exist_ok=True)
    trees = {}
    for k, p in TREES.items():
        if not os.path.isdir(p):
            print("缺失快照:", k, p)
            sys.exit(1)
        t0 = time.time()
        trees[k] = walk_top(p)
        print("扫描 %s: %d 文件, %.1fs" % (k, len(trees[k]), time.time() - t0))

    summaries = {k: tree_summary(m) for k, m in trees.items()}
    for k, s in summaries.items():
        s["mtime_min_iso"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s["mtime_min"]))
        s["mtime_max_iso"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s["mtime_max"]))
        s["dir_breakdown"] = dir_breakdown(trees[k])
        s["key_files"] = key_files(trees[k])
        print(k, s["file_count"], s["total_mb"], s["mtime_min_iso"], "~", s["mtime_max_iso"])

    pairs = [("new1", "new2"), ("new1", "old"), ("new2", "old")]
    result = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "trees": {k: os.path.relpath(p, ROOT) for k, p in TREES.items()},
        "summaries": summaries,
        "pairs": {},
    }
    filesdumps = {}
    for a, b in pairs:
        A, B = trees[a], trees[b]
        rows = compare(a, b, A, B)
        agg = aggregate(rows)
        # 只落盘非 assets 的明细（assets 只留计数），避免 jsonl 过大
        detail = [r for r in rows if r["kind"] != "assets"]
        assets_rows = [r for r in rows if r["kind"] == "assets"]
        result["pairs"]["%s_vs_%s" % (a, b)] = {
            "summary_agg": agg,
            "assets_diff_count": len(assets_rows),
            "assets_bytes_a": sum(r["size_a"] for r in assets_rows),
            "assets_bytes_b": sum(r["size_b"] for r in assets_rows),
            "non_asset_diff_count": len(detail),
            "by_kind": {},
            "root_level_detail": [r for r in detail if r["kind"] != "cards"][:400],
        }
        # by_kind 直方图
        for r in detail:
            e = result["pairs"]["%s_vs_%s" % (a, b)]["by_kind"].setdefault(r["kind"], {})
            e[r["status"]] = e.get(r["status"], 0) + 1
        filesdumps["%s_vs_%s" % (a, b)] = detail

    with open(os.path.join(OUT, "snapshot_diff.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    for name, rows in filesdumps.items():
        with open(os.path.join(OUT, "file_diff_%s.jsonl" % name), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("已写:", os.path.join(OUT, "snapshot_diff.json"))
    for name, rows in filesdumps.items():
        print("  file_diff_%s.jsonl  %d 行" % (name, len(rows)))


if __name__ == "__main__":
    main()
