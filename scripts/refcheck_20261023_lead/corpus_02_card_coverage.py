# -*- coding: utf-8 -*-
"""全量 card.json 字段覆盖统计（流式，不整份驻留）。

输入（只读）: 新版2 的 claude_cc_site_pages/cards/<dir>/data/card.json，另对旧版基线做同样的键集统计。
输出: work/refcheck_20261023_lead/corpus/card_field_coverage.json
      work/refcheck_20261023_lead/corpus/cards_index.jsonl
用法: .venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/corpus_02_card_coverage.py
"""
import os, sys, json, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_cards as cc

ROOT = r"E:\代码项目\锁链战记数据解包"
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead", "corpus")


def nonempty(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != "" and v.strip() != "null"
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def walk(obj, prefix, acc):
    """acc[path] = {"present":n,"nonempty":n,"types":Counter,"samples":[...]}"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = k if not prefix else prefix + "." + k
            e = acc.setdefault(p, {"present": 0, "nonempty": 0, "types": collections.Counter(),
                                   "samples": []})
            e["present"] += 1
            if nonempty(v):
                e["nonempty"] += 1
            e["types"][type(v).__name__] += 1
            if len(e["samples"]) < 3 and nonempty(v) and not isinstance(v, (dict, list)):
                s = str(v)
                if s not in e["samples"]:
                    e["samples"].append(s[:120])
            walk(v, p, acc)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, prefix + "[]", acc)


def scan(base, want_index=False):
    idx = cc.index_by_cid(base)
    acc = {}
    per_card = []
    keytop = collections.Counter()
    cids = sorted(idx, key=lambda x: (len(x), x))
    n = 0
    for cid in cids:
        for dname, dpath in idx[cid]:
            f = os.path.join(cc.data_path(dpath), "card.json")
            if not os.path.exists(f):
                continue
            with open(f, "r", encoding="utf-8") as fh:
                j = json.load(fh)
            n += 1
            for k in j.keys():
                keytop[k] += 1
            walk(j, "", acc)
            if want_index:
                per_card.append({
                    "cid": j.get("cid"),
                    "dir": dname,
                    "source": j.get("source"),
                    "jp_name": j.get("jp_name"),
                    "rarity": (j.get("basic") or {}).get("rarity"),
                    "has_denju": nonempty(j.get("denju")),
                    "denju_patterns": len((j.get("denju") or {}).get("patterns") or []),
                    "has_sa": nonempty(((j.get("skill") or {}).get("sa"))),
                    "has_abilities": nonempty(j.get("abilities")),
                    "n_abilities": len(j.get("abilities") or []),
                    "has_extra": nonempty(j.get("extra")),
                    "n_extra": len(j.get("extra") or []),
                    "has_bond": nonempty(j.get("bond")),
                    "has_leader": nonempty(j.get("leader")),
                    "has_passive": nonempty(j.get("passive")),
                    "has_crossworld": nonempty(j.get("crossworld")),
                    "has_heroic": nonempty(j.get("heroic")),
                    "has_job_ability": nonempty(j.get("job_ability")),
                    "has_sympathy": nonempty(j.get("sympathy")),
                    "site_status": (j.get("site") or {}).get("status"),
                    "site_ids": [c.get("site_id") for c in ((j.get("site") or {}).get("candidates") or [])],
                    "size": os.path.getsize(f),
                })
    return n, acc, keytop, per_card


def finalize(acc, total):
    out = {}
    for p, e in acc.items():
        top = p.split(".")[0].split("[]")[0]
        out[p] = {
            "present": e["present"],
            "present_rate": round(e["present"] / total, 4) if total else 0,
            "nonempty": e["nonempty"],
            "nonempty_rate": round(e["nonempty"] / total, 4) if total else 0,
            "types": dict(e["types"]),
            "samples": e["samples"],
        }
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    print("扫描新版2 ...")
    n2, acc2, key2, per2 = scan(cc.BASES["new2"], want_index=True)
    print("  卡数:", n2)
    print("扫描旧版基线 ...")
    n_old, acc_old, key_old, _ = scan(cc.BASES["old"])
    print("  卡数:", n_old)
    print("扫描新版1 ...")
    n1, acc1, key1, _ = scan(cc.BASES["new1"])
    print("  卡数:", n1)

    cov2 = finalize(acc2, n2)
    cov_old = finalize(acc_old, n_old)
    cov1 = finalize(acc1, n1)

    # 键集差异：新版2 相对旧版新增的路径 / 旧版有新版无
    added = sorted(set(cov2) - set(cov_old))
    removed = sorted(set(cov_old) - set(cov2))
    # 非空率变化显著的公共路径
    changed = []
    for p in sorted(set(cov2) & set(cov_old)):
        a, b = cov_old[p]["nonempty_rate"], cov2[p]["nonempty_rate"]
        if abs(a - b) >= 0.05:
            changed.append({"path": p, "old_nonempty_rate": a, "new_nonempty_rate": b,
                            "old_nonempty": cov_old[p]["nonempty"], "new_nonempty": cov2[p]["nonempty"]})

    src = collections.Counter(c["source"] for c in per2)
    result = {
        "generated_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot_used": "new2 (claude_cc_site_pages_给GPT_20261023/claude_cc_site_pages)",
        "cards_total": {"new1": n1, "new2": n2, "old": n_old},
        "top_level_keys": dict(key2),
        "source_distribution": dict(src),
        "field_coverage": cov2,
        "field_coverage_old": {k: {"present": v["present"], "nonempty": v["nonempty"],
                                   "nonempty_rate": v["nonempty_rate"]} for k, v in cov_old.items()},
        "old_vs_new2": {
            "paths_only_in_new2": added,
            "paths_only_in_old": removed,
            "nonempty_rate_shifts_ge_5pct": changed,
        },
    }
    with open(os.path.join(OUT, "card_field_coverage.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "cards_index.jsonl"), "w", encoding="utf-8") as f:
        for c in per2:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print("已写 card_field_coverage.json / cards_index.jsonl")
    print("顶层键:", dict(key2))
    print("来源分布:", dict(src))
    print("新版2 相对旧版新增路径数:", len(added))
    for p in added[:60]:
        print("  +", p, cov2[p]["nonempty_rate"])
    print("非空率变化>=5%:", len(changed))
    for c in changed[:40]:
        print("  ~", c["path"], c["old_nonempty_rate"], "->", c["new_nonempty_rate"])


if __name__ == "__main__":
    main()
