# -*- coding: utf-8 -*-
"""抽 20 张卡：对方 card.json 字段结构 + 我方页面同卡对照。

输出:
  work/refcheck_20261023_lead/corpus/sample_cards.jsonl      每卡结构快照
  work/refcheck_20261023_lead/corpus/sample_mainline_compare.json  同卡我方组/行对照
用法: .venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/corpus_04_card_sample.py
"""
import os, sys, json, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus_cards as cc

ROOT = r"E:\代码项目\锁链战记数据解包"
OUT = os.path.join(ROOT, "work", "refcheck_20261023_lead", "corpus")
OURPAGES = os.path.join(ROOT, "output", "character_skills", "pages")


def nonempty(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() not in ("", "null")
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def structure(j):
    """返回 {section: {nonempty: bool, detail}}"""
    b = j.get("basic") or {}
    sk = j.get("skill") or {}
    dj = j.get("denju") or {}
    return {
        "basic": {"keys": len(b), "nonempty_illustrator": nonempty(b.get("illustrator")),
                  "atknumber": b.get("atknumber"), "shotspeed": b.get("shotspeed"),
                  "crinumber": b.get("crinumber"), "movspeed": b.get("movspeed"),
                  "jobtype": b.get("jobtype"), "weapon_type": b.get("weapon_type"),
                  "buddy_id": b.get("buddy_id"), "buddy_of": b.get("buddy_of"),
                  "maxlv": b.get("maxlv"), "limit_break": b.get("limit_break")},
        "skill": {"name": sk.get("name"), "charainfo_type": sk.get("charainfo_type"),
                  "patterns": len(sk.get("patterns") or []),
                  "slots_of_pattern0": len(((sk.get("patterns") or [{}])[0]).get("slots") or []),
                  "sa_type": (sk.get("sa") or {}).get("type") if isinstance(sk.get("sa"), dict) else None,
                  "sa_name": (sk.get("sa") or {}).get("name") if isinstance(sk.get("sa"), dict) else None,
                  "union": any(p.get("union") for p in (sk.get("patterns") or []))},
        "abilities": {"count": len(j.get("abilities") or []),
                      "types": [a.get("type") for a in (j.get("abilities") or [])],
                      "subs": [len(a.get("sub") or []) for a in (j.get("abilities") or [])]},
        "extra": {"count": len(j.get("extra") or []),
                  "types": sorted({s.get("type") for e in (j.get("extra") or []) for s in (e.get("skills") or [])})},
        "sympathy": {"present": nonempty(j.get("sympathy")),
                     "type": ((j.get("sympathy") or {}).get("skill") or {}).get("type")},
        "bond": {"present": nonempty(j.get("bond")),
                 "skills": len((j.get("bond") or {}).get("skills") or []),
                 "name": (j.get("bond") or {}).get("name")},
        "leader": {"present": nonempty(j.get("leader")),
                   "skills": len((j.get("leader") or {}).get("skills") or []),
                   "sympathy_skills": len((j.get("leader") or {}).get("sympathy_skills") or [])},
        "job_ability": {"present": nonempty(j.get("job_ability")),
                        "skills": len((j.get("job_ability") or {}).get("skills") or [])},
        "passive": {"present": nonempty(j.get("passive")),
                    "levels": len((j.get("passive") or {}).get("levels") or []),
                    "is_all_home": (j.get("passive") or {}).get("is_all_home")},
        "crossworld": {"present": nonempty(j.get("crossworld")),
                       "type": ((j.get("crossworld") or {}).get("skill") or {}).get("type")},
        "heroic": {"present": nonempty(j.get("heroic")),
                   "levels": len((j.get("heroic") or {}).get("levels") or []),
                   "patterns": len((j.get("heroic") or {}).get("patterns") or [])},
        "denju": {"present": nonempty(j.get("denju")), "mana": dj.get("mana"),
                  "patterns": len(dj.get("patterns") or []),
                  "limit_break_versions": len(dj.get("limit_break") or []),
                  "weapon_change": dj.get("weapon_change")},
        "site": {"status": (j.get("site") or {}).get("status"),
                 "candidates": (j.get("site") or {}).get("candidates")},
        "images": os.path.basename(str(j.get("images")))[:40],
    }


def mainline(cid):
    p = os.path.join(OURPAGES, str(cid), "card.json")
    if not os.path.exists(p):
        return {"page_exists": False}
    j = json.load(open(p, encoding="utf-8"))
    g = []
    for grp in j.get("groups") or []:
        rows = sum(len(s.get("rows") or []) for s in (grp.get("skills") or []))
        cls = {}
        for s in (grp.get("skills") or []):
            for r in (s.get("rows") or []):
                cls[r.get("row_class")] = cls.get(r.get("row_class"), 0) + 1
        g.append({"group": grp.get("group"), "label": grp.get("label"),
                  "skills": len(grp.get("skills") or []), "rows": rows,
                  "class": cls, "status": grp.get("status")})
    return {"page_exists": True, "schema": j.get("schema_version"),
            "groups": g, "coverage": {k: j["coverage"].get(k) for k in
                                      ("N_all", "A", "C", "E", "A_rate", "C_rate")},
            "website_status": (j.get("reference_comparison") or {}).get("website_status")}


def pick_cids(idx):
    cids = sorted(idx, key=lambda x: (len(x), x))
    yg = []
    for cid in cids:
        d = idx[cid][0][0]
        if "Y.G." in d:
            yg.append(cid)
    # 分层挑选 + 固定种子随机补足
    fixed = ["30236", "351", "13001", "10001", "4", "1", "204", "284", "292", "10211"]
    fixed = [c for c in fixed if c in idx]
    rng = random.Random(20261023)
    yg_sample = rng.sample(yg, min(6, len(yg)))
    pool = [c for c in cids if c not in fixed and c not in yg_sample]
    rnd = rng.sample(pool, max(0, 20 - len(fixed) - len(yg_sample)))
    sel = []
    for c in fixed + yg_sample + rnd:
        if c not in sel:
            sel.append(c)
    meta = {"fixed": fixed, "yg_sample": yg_sample, "random": rnd, "seed": 20261023,
            "yg_total": len(yg)}
    return sel, meta


def main():
    os.makedirs(OUT, exist_ok=True)
    idx = cc.index_by_cid(cc.BASES["new2"])
    sel, meta = pick_cids(idx)
    print("抽样", len(sel), "张；Y.G. 全库", meta["yg_total"])
    recs = []
    cmp = {}
    for cid in sel:
        d, p = idx[cid][0]
        j = json.load(open(os.path.join(cc.data_path(p), "card.json"), encoding="utf-8"))
        rec = {"cid": int(cid), "dir": d, "source": j.get("source"),
               "jp_name": j.get("jp_name"), "card_json_bytes": os.path.getsize(os.path.join(cc.data_path(p), "card.json")),
               "structure": structure(j)}
        recs.append(rec)
        cmp[cid] = mainline(cid)
    with open(os.path.join(OUT, "sample_cards.jsonl"), "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(OUT, "sample_mainline_compare.json"), "w", encoding="utf-8") as f:
        json.dump({"sample_meta": meta, "sample": sel, "mainline": cmp}, f, ensure_ascii=False, indent=1)
    # 控制台简表
    print(f"{'cid':>8s} {'src':5s} {'ability':>7s}{'extra':>6s}{'symp':>5s}{'leader':>7s}{'bond':>5s}{'passive':>8s}{'heroic':>7s}{'denju':>6s}{'dLB':>4s}{'sa':>4s}{'site':>5s}")
    for r, cid in zip(recs, sel):
        s = r["structure"]
        print(f"{cid:>8s} {r['source']:5s} {s['abilities']['count']:7d}{s['extra']['count']:6d}"
              f"{int(s['sympathy']['present']):5d}{int(s['leader']['present']):7d}{int(s['bond']['present']):5d}"
              f"{s['passive']['levels']:8d}{s['heroic']['levels']:7d}{int(s['denju']['present']):6d}"
              f"{s['denju']['limit_break_versions']:4d}{int(bool(s['skill']['sa_type'])):4d}"
              f"{int(bool(s['site']['candidates'])):5d}")
    print("已写 sample_cards.jsonl / sample_mainline_compare.json")


if __name__ == "__main__":
    main()
