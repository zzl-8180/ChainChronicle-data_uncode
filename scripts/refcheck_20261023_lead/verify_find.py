# -*- coding: utf-8 -*-
"""按 skillid 查记录、所属角色与相关文本。只读。"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from verify_common import Db, cache_table, pstr  # noqa: E402


def build_owners():
    """skillid -> [(来源, cid)] 反向索引（能力侧 skilllist.skillid）。"""
    idx = {}

    def add(sid, src, cid):
        idx.setdefault(sid, []).append((src, cid))

    sym = cache_table("sympathy_skilllist")["sympathy_skill_info"]
    for r in sym:
        cid = r.get("_id")
        for k, v in r.items():
            if k.startswith("ability") and v:
                add(v, "sympathy_skilllist", cid)
    lead = cache_table("leaderabilityinfo")["leader_ability"]
    for r in lead:
        for v in (r.get("skill_ids") or []) + (r.get("sympathy_skill_ids") or []):
            add(v, "leaderabilityinfo", r.get("cid"))
    extra = cache_table("extraabilitylist")["extra_ability_info"]
    for r in extra:
        for ab in r.get("extra_abilities") or []:
            for v in ab.get("skill_ids") or []:
                add(v, "extraabilitylist", r.get("cid"))
    job = cache_table("jobabilityinfo")["job_ability"]
    for i, r in enumerate(job):
        for v in r.get("skill_ids") or []:
            for c in r.get("cids") or []:
                add(v, "jobabilityinfo", c)
    return idx


def main(argv):
    db = Db()
    owners = build_owners()
    sl = {r["skillid"]: r for r in db.skilllist}
    bs = db.skill_by_id
    target_ids = []
    for a in argv:
        target_ids.extend(int(x) for x in a.split(","))
    for sid in target_ids:
        print("=" * 90)
        print("ID", sid)
        if sid in sl:
            r = sl[sid]
            print("[skilllist] ability=%s name=%s" % (r.get("ability"), r.get("name")))
            print("  params:", pstr(r, "param"))
            print("  text:", (r.get("text") or "").replace("\n", " / ")[:400])
            print("  flavor:", (r.get("flavor") or "").replace("\n", " / ")[:200])
        if sid in bs:
            r = bs[sid]
            print("[bossskill] type=%s" % r.get("skillid0"))
            print("  params:", pstr(r, "skillparam"))
            print("  s_ability:", r.get("s_ability"))
        for src, cid in owners.get(sid, []):
            c = db.cid_index.get(cid)
            print("  owner %s cid=%s name=%s title=%s job=%s" %
                  (src, cid, c.get("name") if c else "?", c.get("title") if c else "?",
                   c.get("jobtype") if c else "?"))
            if c and c.get("skillname"):
                print("     mainskill:", c["skillname"])
                print("     maintext:", (c.get("skilltext") or "").replace("\n", " / ")[:400])
        if sid not in sl and sid not in bs:
            print("  (记录不在 skilllist/bossskill)")


if __name__ == "__main__":
    main(sys.argv[1:])
