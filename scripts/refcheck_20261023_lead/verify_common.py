# -*- coding: utf-8 -*-
"""复核 claude_cc_site_pages 20261023 数值规则：公共加载与工具。

只读 output/cache_full_20261015_v3/decoded 与 output/base_master。
不写任何 output/ 既有产物；调用方负责把结果写到 work/refcheck_20261023_lead/verify。
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DECODED = os.path.join(ROOT, "output", "cache_full_20261015_v3", "decoded")
BASE_MASTER = os.path.join(ROOT, "output", "base_master")
OUT_DIR = os.path.join(ROOT, "work", "refcheck_20261023_lead", "verify")
SCRIPTS_REL = "scripts/refcheck_20261023_lead"


def cache_table(name: str):
    """读缓存解码主表（*.data5.json.raw，UTF-8 JSON）。"""
    path = os.path.join(DECODED, name + ".data5.json.raw")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apk_table(name: str):
    path = os.path.join(BASE_MASTER, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class Db:
    def __init__(self):
        self.skilllist = cache_table("skilllist")["skilllist"]
        bi = cache_table("bossinfo")["bossinfo"]
        self.bossskill = bi["bossskill"]
        self.bosspattern = bi["bosspattern"]
        self.charainfo = cache_table("charainfo")["charainfo"]
        self._cid = None
        self._pat2skill = None

    # ---- 索引 ----
    @property
    def cid_index(self):
        if self._cid is None:
            self._cid = {r["cid"]: r for r in self.charainfo}
        return self._cid

    @property
    def pattern_index(self):
        """patternid -> {skillid0/1/2...} 指向的 bossskill.skillid 列表"""
        if self._pat2skill is None:
            idx = {}
            for p in self.bosspattern:
                ids = [p[k] for k in ("skillid0", "skillid1", "skillid2", "skillid3")
                       if k in p and p[k]]
                idx[p["patternid"]] = ids
            self._pat2skill = idx
        return self._pat2skill

    @property
    def skill_by_id(self):
        if not hasattr(self, "_sbid"):
            self._sbid = {}
            for r in self.bossskill:
                self._sbid.setdefault(r["skillid"], r)
        return self._sbid

    def cids_of_pattern(self, patternid):
        out = []
        for c in self.charainfo:
            for k in range(0, 8):
                if c.get("pattern%d" % k) == patternid:
                    out.append(c["cid"])
                    break
        return out

    def characters_of_bossskill(self, skillid):
        """返回引用了该 bossskill.skillid 的 cid 列表（经 charainfo.patternN -> bosspattern）。"""
        out = []
        for p in self.bosspattern:
            ids = [p.get("skillid0"), p.get("skillid1"), p.get("skillid2"), p.get("skillid3")]
            if skillid in ids:
                out.extend(self.cids_of_pattern(p["patternid"]))
        return sorted(set(out))

    def characters_of_ability(self, skillid):
        """skilllist 能力被哪些 cid 引用（charainfo.skillid[1:] / pattern / sub 等直接扫描）。"""
        out = []
        for c in self.charainfo:
            ids = c.get("skillid") or []
            if skillid in ids:
                out.append(c["cid"])
                continue
            for k in range(0, 8):
                pid = c.get("pattern%d" % k)
                if pid is None:
                    continue
                for sid in self.pattern_index.get(pid, ()):
                    rec = self.skill_by_id.get(sid)
                    if rec is not None and rec.get("s_ability") == skillid:
                        out.append(c["cid"])
                        break
        return sorted(set(out))


def type_of(rec, table):
    return rec.get("ability") if table == "skilllist" else rec.get("skillid0")


def params(rec, prefix="param"):
    """存在的参数槽（区分缺失与 0）：返回 [(idx, value)]"""
    out = []
    for k, v in rec.items():
        if k.startswith(prefix) and k[len(prefix):].isdigit():
            out.append((int(k[len(prefix):]), v))
    return sorted(out)


def pstr(rec, prefix="param", rng=10):
    parts = []
    for i in range(rng):
        key = prefix + str(i)
        if key in rec:
            parts.append("p%d=%s" % (i, rec[key]))
    return " ".join(parts)


def val_counter(records, prefix="param"):
    """每个槽位的取值分布（只统计存在字段，缺失单列）。"""
    present = defaultdict(Counter)
    missing = Counter()
    for r in records:
        for i in range(0, 11):
            key = prefix + str(i)
            if key in r:
                present[i][r[key]] += 1
            else:
                missing[i] += 1
    res = {}
    for i in sorted(present):
        cnt = present[i]
        res[i] = {
            "present": sum(cnt.values()),
            "missing": missing[i],
            "distinct": len(cnt),
            "top": [[v, n] for v, n in cnt.most_common(12)],
        }
    for i in sorted(missing):
        if i not in res:
            res[i] = {"present": 0, "missing": missing[i], "distinct": 0, "top": []}
    return res


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=False)
    return path


def out(name):
    return os.path.join(OUT_DIR, name)


def md_cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")
