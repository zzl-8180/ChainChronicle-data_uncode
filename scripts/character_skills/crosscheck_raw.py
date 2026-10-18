"""Independent evidence cross-check (implementation self-check, NOT the R1 review).

This script deliberately does **not** import ``common``/``rules``/``profiles`` and
does not read the pipeline's intermediate files for its own derivation: it walks
the raw decoded ``.data5.json.raw`` documents and the APK master JSON directly,
recomputes what the association should contain, and only then compares against the
generated artefacts. Its purpose is to catch the case where the pipeline verifies
its own output.

Checks
------
A. character sample: re-derive every skill reference from raw charainfo and compare
   the (group, table, reference_id) multiset with ``links/character_skills.jsonl``
B. field sample: re-read the raw value at the recorded JSON pointer for a sample of
   rule answers and compare with the value stored in ``profiles/records.jsonl``
C. byte-location sample: re-open the cache source and confirm the recorded byte
   range still contains a JSON object whose fields match the stored record
D. super-limit bits: recompute bit -> cap ratio from boss_heal constants and compare
   with the answer text produced for a real type27 record (if one exists)
E. scope: recompute 2236 / 2233 and the only-ours set straight from the raw inputs
F. charainfo equivalence: re-derive the class counts (universe 1287, E0 1110) from the
   raw charainfo / bosspattern / bossskill documents, with the same cache-preferred
   per-ID resolution rule, and compare against ``charainfo_params/equivalence.json``
G. charainfo answers: for sampled answers, re-read the raw charainfo value and the
   matched bossskill value and require them to be equal (the transfer premise)
H. skilllist ability types 8 (Always) / 26 (ManaGet): re-read the raw records and check
   every stored answer value, the int-truncated mana count, and that a record whose text
   says the damage taken increases is answered as such (direction)
I. the two critical accumulators: re-read every crit answer's raw value and check the
   caliber split (percentage points vs coefficient increment) and the per-path clamp bounds

Writes only ``output/character_skills/validation/crosscheck_raw.json``.
"""
from __future__ import annotations

import collections
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "output" / "character_skills"
DECODED = ROOT / "output" / "cache_full_20261015_v3" / "decoded"
BASE_MASTER = ROOT / "output" / "base_master"
SAMPLE_STEP = 97  # every 97th roster row -> ~23 characters


def jload(p):
    with Path(p).open(encoding="utf-8") as fh:
        return json.load(fh)


def jl(p):
    with Path(p).open(encoding="utf-8") as fh:
        return [json.loads(l) for l in fh]


def raw_cache(name, *path):
    cur = jload(DECODED / f"{name}.data5.json.raw")
    for k in path:
        cur = cur[k]
    return cur


def raw_master(fname, *path):
    cur = jload(BASE_MASTER / fname)
    for k in path:
        cur = cur[k]
    return cur


def iter_holders():
    """Every answer holder in ``records.jsonl``: top-level records and their embedded
    child (sub-effect) records.

    Children carry no ``rec_key`` and the same child record can be embedded in several
    parents, so callers that must count *unique* answer rows key on
    (table, record_id, layer, field); callers that reproduce the page / record-level
    calibers count instances. Before P2 batch 5 the H/I/J regions walked only the
    top-level records, which left the majority of answers (they live in children)
    unverified -- e.g. only 159 of the 672 same-leaf answers are top-level.
    """
    for r in jl(BASE / "profiles" / "records.jsonl"):
        yield r.get("rec_key"), r
        for ch in r.get("children") or []:
            if isinstance(ch, dict) and "answers" in ch:
                yield (r.get("rec_key") or "?") + "|child", ch


def main():
    # console encoding only: this script intentionally does not import the pipeline's
    # common module, so the UTF-8 reconfiguration is inlined here
    import sys as _sys
    for _s in (_sys.stdout, _sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    report = {"generated_by": "scripts/character_skills/crosscheck_raw.py",
              "note": "实施者自检：直读原始解码 JSON／APK 主表，不经过本管道加载器；不是独立审查。",
              "checks": {}}
    ok_all = True

    # ------------------------------------------------------------------ E
    roster = jload(ROOT / "output" / "char_roster" / "data" / "playable_characters.json")
    ref = jload(ROOT / "其他人的参考" / "claude_cc_site_pages" / "match_result.json")
    ours = {r["cid"] for r in roster}
    theirs = {int(k) for k in ref}
    only_ours = sorted(ours - theirs)
    only_theirs = sorted(theirs - ours)
    scope = jload(BASE / "scope_diff" / "scope_diff.json")
    e_ok = (len(ours) == 2236 and len(theirs) == 2233
            and only_ours == [r["cid"] for r in scope["only_ours"]]
            and only_theirs == [] )
    report["checks"]["E_scope_raw"] = {
        "ok": e_ok, "ours": len(ours), "theirs": len(theirs),
        "only_ours": only_ours, "only_theirs": only_theirs,
        "pipeline_only_ours": [r["cid"] for r in scope["only_ours"]]}
    ok_all &= e_ok

    # ------------------------------------------------------------------ A
    cache_charainfo = {r["cid"]: r for r in raw_cache("charainfo", "charainfo")}
    apk_charainfo = {r["cid"]: r for r in jload(BASE_MASTER / "_mdCharacter.json")["charainfo"]}
    cache_skill = {r["skillid"] for r in raw_cache("skilllist", "skilllist")}
    apk_skill = {r["skillid"] for r in jload(BASE_MASTER / "_mdSkill.json")["skilllist"]}
    cache_bp = {r["patternid"] for r in raw_cache("bossinfo", "bossinfo", "bosspattern")}
    apk_bp = {r["patternid"] for r in jload(BASE_MASTER / "_mdBossInfo.json")["bosspattern"]}
    cache_bs = {r["skillid"] for r in raw_cache("bossinfo", "bossinfo", "bossskill")}
    apk_bs = {r["skillid"] for r in jload(BASE_MASTER / "_mdBossInfo.json")["bossskill"]}

    links = {r["cid"]: r for r in jl(BASE / "links" / "character_skills.jsonl")}
    sample = [r["cid"] for r in roster[::SAMPLE_STEP]]
    a_bad, a_checked = [], 0
    for cid in sample:
        rec = cache_charainfo.get(cid) or apk_charainfo.get(cid)
        if rec is None:
            a_bad.append({"cid": cid, "why": "raw charainfo missing"})
            continue
        expected = []
        sk = rec.get("skillid") or []
        # skillid[0] is the special move's effect type (R1 A1); it must NOT appear as a
        # resolved reference anywhere, only as an annotation
        for i, v in enumerate(sk[1:], start=1):
            if v:
                expected.append(("ability", "skilllist", v))
        if rec.get("s_ability"):
            expected.append(("sa", "skilllist", rec["s_ability"]))
        for i in range(9):
            v = rec.get(f"pattern{i}")
            if v:
                expected.append(("special_move", "bosspattern", v))
        if rec.get("skillname") or rec.get("skilltext"):
            expected.append(("special_move", "charainfo", cid))
        have, broken = [], []
        for g in links[cid]["groups"]:
            for ref in g["records"]:
                have.append((g["group"], ref["table"], ref["reference_id"]))
            for u in g["unresolved"]:
                broken.append((g["group"], u.get("expected_table"), u.get("reference_id")))
        # an id is resolvable only if it exists in the same namespace (cache or APK)
        skill_ids = cache_skill | apk_skill
        bp_ids = cache_bp | apk_bp

        def resolvable(group, table, ident):
            if table == "skilllist":
                return ident in skill_ids
            if table == "bosspattern":
                return ident in bp_ids
            return True  # charainfo record always exists

        exp_ok = [e for e in expected if resolvable(*e)]
        exp_broken = [e for e in expected if not resolvable(*e)]
        have_core = sorted(h for h in have if h[0] in ("ability", "sa", "special_move"))
        broken_core = sorted(b for b in broken if b[0] in ("ability", "sa", "special_move"))
        # slot0 must be an annotation carrying the raw value and a verdict
        anns = [a for g in links[cid]["groups"] if g["group"] == "slot0"
                for a in g.get("annotations") or []]
        ann_ok = (len(anns) == 1 and anns[0]["raw_value"] == (sk[0] if sk else 0)
                  and anns[0]["verdict"] in ("MATCHES_OWN_PATTERN_EFFECT_TYPE",
                                             "NOT_AMONG_OWN_PATTERN_TYPES",
                                             "TYPE_ONLY_NO_PATTERN_IN_CACHE_OR_APK",
                                             "TYPE_ZERO_UNSET"))
        a_checked += 1
        if sorted(exp_ok) != have_core or sorted(exp_broken) != broken_core or not ann_ok:
            a_bad.append({"cid": cid, "expected_resolved": sorted(exp_ok),
                          "pipeline_resolved": have_core,
                          "expected_broken": sorted(exp_broken),
                          "pipeline_broken": broken_core,
                          "slot0_annotation_ok": ann_ok,
                          "slot0_annotations": anns})
    report["checks"]["A_reference_rederivation"] = {
        "ok": not a_bad, "sampled": a_checked, "sample_step": SAMPLE_STEP,
        "mismatches": a_bad[:5], "mismatch_count": len(a_bad)}
    ok_all &= not a_bad

    # ------------------------------------------------------------------ B
    recs = {r["rec_key"]: r for r in jl(BASE / "profiles" / "records.jsonl")}
    b_bad, b_checked = [], 0
    for rkey in sorted(recs)[::211]:
        r = recs[rkey]
        src = r.get("source") or {}
        ptr = src.get("json_pointer")
        if not ptr:
            continue
        layer = r.get("layer")
        fields = [(a["f"], a["raw"]) for a in r["answers"]] + \
                 [(u["f"], u.get("raw")) for u in r["unexplained"]]
        if not fields:
            continue
        if layer == "CACHE":
            sk = src.get("source_key") or ""
            stem = sk.split("/")[-1].replace(".data5.json.raw", "")
            doc = jload(DECODED / f"{stem}.data5.json.raw")
        else:
            doc = jload(BASE_MASTER / src["source_key"].split("/")[-1])
        cur = doc
        try:
            for part in [p for p in ptr.split("/") if p != ""]:
                cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        except Exception as exc:  # pragma: no cover
            b_bad.append({"rec_key": rkey, "why": f"pointer walk failed: {exc}"})
            continue
        for f, raw in fields:
            key = f.lstrip("/")
            b_checked += 1
            got = cur.get(key, "<<absent>>")
            if got != raw:
                b_bad.append({"rec_key": rkey, "field": f, "stored": raw, "raw_source": got})
    report["checks"]["B_field_value_rederivation"] = {
        "ok": not b_bad, "fields_checked": b_checked, "mismatches": b_bad[:5],
        "mismatch_count": len(b_bad)}
    ok_all &= not b_bad

    # ------------------------------------------------------------------ C
    c_bad, c_checked = [], 0
    for rkey in sorted(recs)[::307]:
        r = recs[rkey]
        src = r.get("source") or {}
        if src.get("layer") != "CACHE" or src.get("byte_begin") is None:
            continue
        sk = src["source_key"]
        stem = sk.split("/")[-1].replace(".data5.json.raw", "")
        blob = (DECODED / f"{stem}.data5.json.raw").read_bytes()
        piece = blob[src["byte_begin"]:src["byte_end_exclusive"]]
        c_checked += 1
        try:
            obj = json.loads(piece.decode("utf-8"))
        except Exception as exc:
            c_bad.append({"rec_key": rkey, "why": f"byte slice not JSON: {exc}"})
            continue
        if not isinstance(obj, dict) or not (set(obj) & set(r["rec_key"].split("|"))):
            # the recorded range must at least be an object with the record's id field
            ident = int(r["rec_key"].split("|")[1])
            if ident not in [v for v in obj.values() if isinstance(v, int)]:
                c_bad.append({"rec_key": rkey, "why": "id not present in byte range object",
                              "keys": sorted(obj)[:8]})
    report["checks"]["C_byte_location_sample"] = {
        "ok": not c_bad, "slices_checked": c_checked, "mismatches": c_bad[:5],
        "mismatch_count": len(c_bad)}
    ok_all &= not c_bad

    # ------------------------------------------------------------------ D
    # D1: replay the recorded boss_heal native checks against the flag table
    constants = jload(ROOT / "output" / "boss_heal" / "constants.json")
    bits, values = constants["bits"]["values"], constants["values"]["values"]
    checks = jload(ROOT / "output" / "boss_heal" / "checks.json")["checks"]
    d_bad, d_checked = [], 0
    for c in checks:
        if c.get("case") != "native_flag_rate":
            continue
        flag = c["flag"]
        picked = None
        for i in range(len(bits) - 1, -1, -1):
            if flag >> bits[i] & 1:
                picked = values[i]
                break
        got = 1.0 if picked is None else picked
        d_checked += 1
        if abs(got - c["expected"]) > 1e-6:
            d_bad.append({"flag": flag, "expected": c["expected"], "recomputed": got})
    # D2: real type27 records in this batch -- the JSON field is the low 32 bits
    d_records = []
    for rkey, r in recs.items():
        cands = list(r["children"]) + ([r] if r["table"] == "bossskill" else [])
        for ch in cands:
            if ch.get("effect_type") != 27:
                continue
            for a in ch["answers"]:
                if a["f"] != "/skillflag0_1" or not isinstance(a["raw"], int):
                    continue
                shifted = a["raw"] << 32
                picked = None
                for i in range(len(bits) - 1, -1, -1):
                    if shifted >> bits[i] & 1:
                        picked = values[i]
                        break
                ratio = 1.0 if picked is None else picked
                txt = a.get("value") or ""
                d_records.append({"record_id": ch["record_id"], "raw": a["raw"],
                                  "expected_ratio": ratio, "text_has_ratio": f"{ratio:.6g}" in txt})
    d_rec_bad = [x for x in d_records if not x["text_has_ratio"]]
    report["checks"]["D_super_limit_bits"] = {
        "ok": not d_bad and not d_rec_bad,
        "native_checks_replayed": d_checked, "native_check_failures": d_bad[:5],
        "type27_records_with_flag": len(d_records),
        "type27_record_failures": d_rec_bad[:5],
        "bit_table": list(zip(bits, values)),
        "note": ("D1 独立重放 boss_heal/checks.json 的原生检查（不引用本管道的换算）；"
                 "D2 用真实 type27 记录的 skillflag0_1 低 32 位左移 32 位后重算档位，"
                 "确认页面答案文本里出现同一个比率。")}
    ok_all &= (not d_bad) and (not d_rec_bad)

    # ------------------------------------------------------------------ F
    # F: re-derive the charainfo <-> bossskill equivalence from the raw documents only
    #    (no pipeline module), and compare the class counts against the artefact.
    import struct as _struct

    def _f32(x):
        if x is None:
            return None
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            return x
        return _struct.unpack("<f", _struct.pack("<f", float(x)))[0]

    raw_chara_cache = {r["cid"]: r for r in raw_cache("charainfo", "charainfo")}
    raw_chara_apk = {r["cid"]: r for r in raw_master("_mdCharacter.json", "charainfo")}
    raw_pat_cache = {r["patternid"]: r for r in raw_cache("bossinfo", "bossinfo", "bosspattern")}
    raw_pat_apk = {r["patternid"]: r for r in raw_master("_mdBossInfo.json", "bosspattern")}
    raw_skill_cache = {r["skillid"]: r for r in raw_cache("bossinfo", "bossinfo", "bossskill")}
    raw_skill_apk = {r["skillid"]: r for r in raw_master("_mdBossInfo.json", "bossskill")}
    PAT = [f"pattern{i}" for i in range(9)]

    def _reach(rec):
        """Cache-preferred per-ID resolution, same rule as the pipeline's Table.get."""
        refs = {}
        for f in PAT:
            pv = rec.get(f)
            if not pv:
                continue
            prec = raw_pat_cache.get(pv) or raw_pat_apk.get(pv)
            if not prec:
                continue
            for k in sorted(kk for kk in prec if kk.startswith("skillid")):
                bv = prec.get(k)
                if not bv:
                    continue
                brec = raw_skill_cache.get(bv) or raw_skill_apk.get(bv)
                if brec is not None and brec.get("skillid") is not None:
                    refs[brec["skillid"]] = brec
        return list(refs.values())

    f_classes, f_universe = {}, 0
    f_class_by_cid = {}
    f_f0_bad = []
    for cid in sorted(ours):
        rec = raw_chara_cache.get(cid) or raw_chara_apk.get(cid)
        if rec is None:
            continue
        refs = _reach(rec)
        v0 = (rec.get("skillid") or [0])[0]
        if not refs:
            # P2-9: no reachable pattern skill -> the record's own copy is what
            # CharaParamToBossSkill/_CreateExecSkillList(pattern==0) executes
            f_classes["F0_NO_PATTERN_FALLBACK"] = f_classes.get("F0_NO_PATTERN_FALLBACK", 0) + 1
            f_class_by_cid[cid] = "F0_NO_PATTERN_FALLBACK"
            pats = [rec.get(f"pattern{i}") for i in range(9)]
            if any(pats):
                # every pattern slot is set yet none resolves to a boss skill: allowed,
                # but record it so the claim stays auditable
                resolved = [p for p in pats if p and (raw_pat_cache.get(p) or raw_pat_apk.get(p))]
                if resolved:
                    f_f0_bad.append({"cid": cid, "patterns": pats, "resolved": resolved})
            continue
        if v0 not in {b.get("skillid0") for b in refs}:
            f_classes["NOT_AMONG_OWN_PATTERN_TYPES"] = f_classes.get("NOT_AMONG_OWN_PATTERN_TYPES", 0) + 1
            f_class_by_cid[cid] = "NOT_AMONG_OWN_PATTERN_TYPES"
            continue
        f_universe += 1
        tm = [b for b in refs if b.get("skillid0") == v0]
        if all(rec.get(f"skillparam{i}") is None for i in range(1, 7)):
            f_classes["X2_ALL_SIX_SLOTS_EMPTY"] = f_classes.get("X2_ALL_SIX_SLOTS_EMPTY", 0) + 1
            f_class_by_cid[cid] = "X2_ALL_SIX_SLOTS_EMPTY"
            continue
        cp = [rec.get(f"skillparam{i}") for i in range(10)]
        strict = any([cp[i] for i in range(1, 7)] == [b.get(f"skillparam{i}") for i in range(1, 7)]
                     for b in tm)
        f32eq = any(all(_f32(cp[i]) == _f32(b.get(f"skillparam{i}")) for i in range(1, 7))
                    for b in tm)
        nz = any(all(_f32(0.0 if cp[i] is None else cp[i])
                     == _f32(0.0 if b.get(f"skillparam{i}") is None else b.get(f"skillparam{i}"))
                     for i in range(1, 7)) for b in tm)
        k = ("E0" if strict else "E1" if f32eq else "E2" if nz
             else "X0_TYPE_ZERO_UNSET" if v0 == 0 else "X1_VALUES_DIFFER")
        f_classes[k] = f_classes.get(k, 0) + 1
        f_class_by_cid[cid] = k

    art_equiv = jload(BASE / "charainfo_params" / "equivalence.json")["classes"]
    f_bad = {k: (f_classes.get(k, 0), art_equiv.get(k)) for k in set(f_classes) | set(art_equiv)
             if f_classes.get(k, 0) != art_equiv.get(k)}
    report["checks"]["F_charainfo_equivalence_rederivation"] = {
        "ok": not f_bad and f_universe == 1287 and f_classes.get("E0") == 1110,
        "recomputed": f_classes, "artefact": art_equiv, "universe": f_universe,
        "mismatches": f_bad,
        "f0_with_resolvable_pattern_but_no_skill": f_f0_bad[:5],
        "note": ("只读原始解码 charainfo/bossinfo 文档重推等价类别；universe 应为 1287、"
                 "E0 应为 1110（R2 复核钉死的口径）；F0＝自身 pattern 无可达 bossskill（P2 第 9 批）")}
    ok_all &= (not f_bad) and f_universe == 1287 and f_classes.get("E0") == 1110

    # ------------------------------------------------------------------ G
    # G: for sampled charainfo answers, re-read the raw charainfo value AND the matched
    #    bossskill value straight from the raw documents; they must be equal, because
    #    that equality is the whole premise of the transfer.
    g_bad, g_checked = [], 0
    g2_checked, g2_bad = 0, []
    ca_recs = {r["rec_key"]: r for r in recs.values() if r.get("table") == "charainfo"}
    for rkey in sorted(ca_recs)[::11]:
        r = ca_recs[rkey]
        cid = r["record_id"]
        if not r.get("answers"):
            continue
        rec = raw_chara_cache.get(cid) or raw_chara_apk.get(cid)
        if rec is None:
            g_bad.append({"rec_key": rkey, "why": "charainfo record missing from raw"})
            continue
        v0 = (rec.get("skillid") or [0])[0]
        tm = [b for b in _reach(rec) if b.get("skillid0") == v0]
        f0 = f_class_by_cid.get(cid) == "F0_NO_PATTERN_FALLBACK"
        for a in r["answers"]:
            field = a["f"].lstrip("/")
            g_checked += 1
            raw_val = rec.get(field)
            if raw_val != a["raw"]:
                g_bad.append({"rec_key": rkey, "field": field, "stored": a["raw"],
                              "raw_source": raw_val})
                continue
            if f0:
                # P2-9 caliber: the record's own value IS the executed value; the
                # premise to check is that the raw documents really hold no reachable
                # pattern boss skill for this character.
                g2_checked += 1
                if _reach(rec):
                    g2_bad.append({"rec_key": rkey, "why": "reachable pattern skill exists",
                                   "refs": [b.get("skillid") for b in _reach(rec)][:5]})
                continue
            if a["f"].startswith("/skillparam"):
                if not any(_f32(0.0 if b.get(field) is None else b.get(field))
                           == _f32(0.0 if raw_val is None else raw_val) for b in tm):
                    g_bad.append({"rec_key": rkey, "field": field,
                                  "why": "no type-matched bossskill with an equal value",
                                  "charainfo": raw_val,
                                  "matched": [b.get(field) for b in tm[:3]]})
    report["checks"]["G_charainfo_answer_raw_equality"] = {
        "ok": not g_bad, "answers_checked": g_checked, "mismatches": g_bad[:5],
        "mismatch_count": len(g_bad),
        "note": ("逐条重读原始 charainfo 值与匹配 bossskill 同槽值；两者必须相等，"
                 "否则该答案的迁移前提不成立（F0 类不适用——见 G2）")}
    ok_all &= not g_bad
    report["checks"]["G2_F0_answer_uses_record_own_value"] = {
        "ok": not g2_bad, "answers_checked": g2_checked, "mismatches": g2_bad[:5],
        "mismatch_count": len(g2_bad),
        "note": ("F0（无 pattern）类：答案原值必须等于原始 charainfo 记录原值，且该角色在两源文档里"
                 "都没有可达的 pattern bossskill（执行走兜底构造，不要求与 boss 侧相等）")}
    ok_all &= not g2_bad

    # ------------------------------------------------------------------ H
    # H: skilllist ability types 8 / 26 -- re-read the raw records straight from the
    #    decoded cache (and APK fallback) and check the stored answer values, the
    #    int-truncated mana count, and the damage-taken direction against the record text.
    holders = list(iter_holders())
    h_skill_cache = {r["skillid"]: r for r in raw_cache("skilllist", "skilllist")}
    h_skill_apk = {r["skillid"]: r for r in raw_master("_mdSkill.json", "skilllist")}
    h_bad, h_checked, h_dir, h_dir_bad = [], 0, 0, []
    h_seen, h_bad_seen, h_dir_seen = set(), set(), set()
    for rkey, r in holders:
        if r.get("table") != "skilllist" or r.get("effect_type") not in (8, 26):
            continue
        raw = h_skill_cache.get(r["record_id"]) or h_skill_apk.get(r["record_id"])
        if raw is None:
            h_bad.append({"rec_key": rkey, "why": "raw skilllist record missing"})
            continue
        if raw.get("ability") != r.get("effect_type"):
            h_bad.append({"rec_key": rkey, "why": "ability mismatch", "raw": raw.get("ability")})
        for a in r.get("answers") or []:
            ukey = (r.get("table"), r.get("record_id"), r.get("layer"), a["f"])
            if ukey in h_seen:
                continue
            h_seen.add(ukey)
            h_checked += 1
            field = a["f"].lstrip("/")
            if raw.get(field) != a["raw"]:
                h_bad.append({"rec_key": rkey, "field": field, "stored": a["raw"],
                              "raw_source": raw.get(field)})
            if r["effect_type"] == 26 and field == "param4":
                if not (a.get("value") or "").startswith(
                        f"战斗开始时追加 {int(a['raw'])} 个玛那") and int(a["raw"]) >= 1:
                    h_bad.append({"rec_key": rkey, "why": "param4 count text wrong",
                                  "raw": a["raw"], "text": a.get("value")})
        # direction: a type-8 record whose text says the damage taken increases must
        # carry param3 > 1 and be answered as 增伤, never as 减伤
        text = raw.get("text") or ""
        # only "damage TAKEN increases" -- "与えるダメージ…増加" (damage dealt) is a
        # different quantity and lives in a sub-ability record, so it must not match
        increases = bool(re.search(r"(受けるダメージ[^。]{0,12}増加|ダメージも増加)", text))
        if r.get("effect_type") == 8 and increases:
            ans = next((a for a in r.get("answers") or [] if a["f"] == "/param3"), None)
            dkey = (r.get("table"), r.get("record_id"), r.get("layer"))
            if dkey not in h_dir_seen:
                h_dir_seen.add(dkey)
                h_dir += 1
                if (ans is None or not (ans.get("raw") or 0) > 1
                        or "增伤" not in (ans.get("value") or "")):
                    h_dir_bad.append({"rec_key": rkey, "raw": raw.get("param3"),
                                      "answer": (ans or {}).get("value")})
        if r.get("effect_type") == 8 and any(a["f"] == "/param4" for a in r.get("answers") or []):
            h_bad.append({"rec_key": rkey, "why": "type8 param4 answered but has no native path"})
    report["checks"]["H_skilllist_types_8_26_raw"] = {
        "ok": not h_bad and not h_dir_bad,
        "answers_checked": h_checked, "mismatches": h_bad[:5], "mismatch_count": len(h_bad),
        "damage_increase_text_records": h_dir, "direction_failures": h_dir_bad[:5],
        "scope": "顶层记录＋内嵌子效果记录，按（表,记录,层,字段）去重",
        "note": ("逐条重读原始 skilllist 记录：答案原值必须等于原始 param 值；"
                 "type26 param4 必须按 int 截断成『追加 N 个玛那』；"
                 "type8 正文写「受けるダメージも増加」的记录 param3 必须 >1 且答成增伤")}
    ok_all &= (not h_bad) and (not h_dir_bad)

    # ------------------------------------------------------------------ I
    # I: P2 batch 3 -- the two critical accumulators. Re-read every crit answer's raw
    #    value from the decoded skilllist document and check the caliber split
    #    (percentage points vs coefficient) plus the per-path clamp bounds.
    # the (type, field) -> path mapping comes from the *published* rule dictionary, so a
    # new crit rule cannot slip past this check without being covered here
    crit_dict = jload(BASE / "skilllist_types" / "field_dictionary.json")
    CRIT_RATE = {r["effect_type"]: r["field_path"].lstrip("/") for r in crit_dict
                 if r.get("answer_kind") == "crit_rate"}
    CRIT_DMG = {r["effect_type"]: r["field_path"].lstrip("/") for r in crit_dict
                if r.get("answer_kind") == "crit_dmg"}
    report["checks"].setdefault("_crit_scope", {})
    report["checks"]["_crit_scope"] = {
        "crit_rate_types": {str(k): v for k, v in sorted(CRIT_RATE.items())},
        "crit_dmg_types": {str(k): v for k, v in sorted(CRIT_DMG.items())},
        "note": "从 field_dictionary.json 的 answer_kind 读取，覆盖全部已发布暴击规则"}
    i_bad, i_checked, i_rate, i_dmg = [], 0, 0, 0
    i_seen = set()
    for rkey, r in holders:
        if r.get("table") != "skilllist":
            continue
        et = r.get("effect_type")
        # the composite types (67/80/96/1036) also have crit slots, but their contribution
        # is gated by their own condition and covered by region K; keeping them out here
        # preserves this region's invariant (a single-slot branch whose slot *is* the
        # whole contribution, clamped after the loop)
        if et not in CRIT_RATE and et not in CRIT_DMG or et in (67, 80, 96, 1036):
            continue
        raw = h_skill_cache.get(r["record_id"]) or h_skill_apk.get(r["record_id"])
        if raw is None:
            i_bad.append({"rec_key": rkey, "why": "raw skilllist record missing"})
            continue
        for a in r.get("answers") or []:
            f = a["f"].lstrip("/")
            ukey = (r.get("table"), r.get("record_id"), r.get("layer"), a["f"])
            if ukey in i_seen:
                continue
            i_seen.add(ukey)
            if raw.get(f) != a["raw"]:
                i_bad.append({"rec_key": rkey, "field": f, "stored": a["raw"],
                              "raw_source": raw.get(f)})
                continue
            if f == CRIT_RATE.get(et):
                i_checked += 1
                i_rate += 1
                if "百分点" not in (a.get("unit") or ""):
                    i_bad.append({"rec_key": rkey, "field": f, "why": "rate answer is not in percentage points",
                                  "unit": a.get("unit")})
                if not 0.0 <= float(a["raw"]) <= 0.5:
                    i_bad.append({"rec_key": rkey, "field": f, "why": "rate value outside the path clamp [0,0.5]",
                                  "raw": a["raw"]})
            if f == CRIT_DMG.get(et):
                i_checked += 1
                i_dmg += 1
                if "系数增量" not in (a.get("unit") or ""):
                    i_bad.append({"rec_key": rkey, "field": f, "why": "dmg answer is not a coefficient increment",
                                  "unit": a.get("unit")})
                if not -1.0 <= float(a["raw"]) <= 2.0:
                    i_bad.append({"rec_key": rkey, "field": f, "why": "dmg value outside the path clamp [-1,2]",
                                  "raw": a["raw"]})
    report["checks"]["I_critical_accumulators"] = {
        "ok": not i_bad, "answers_checked": i_checked, "rate_answers": i_rate,
        "scope": "顶层记录＋内嵌子效果记录，按（表,记录,层,字段）去重",
        "dmg_answers": i_dmg, "mismatches": i_bad[:5], "mismatch_count": len(i_bad),
        "note": ("逐条重读原始 skilllist：暴击率答案必须是百分点、暴击伤害答案必须是系数增量，"
                 "且各自落在本路径的夹紧范围（rate [0,0.5]／dmg [-1,2]）内"),
    }
    ok_all &= not i_bad

    # ------------------------------------------------------------------ J
    # J: P2 batch 4 -- the four types that reuse type 8's branch. The (type, field)
    #    list is read from the *published* rule dictionary, so a new same-leaf rule
    #    cannot be added without being covered here. Each answer is re-read straight
    #    from the decoded skilllist document, and the two directions are separated:
    #    param3 is damage TAKEN (0.9 -> 减伤 10%), while "与えるダメージ" (damage dealt)
    #    must never be the thing that drives param3.
    same_leaf_dict = jload(BASE / "skilllist_types" / "field_dictionary.json")
    SL = {}
    for r in same_leaf_dict:
        if r.get("effect_type") in (36, 1003, 1005, 1026) and r.get("answer_kind") in (
                "attack_mult", "move_mult", "take_mult"):
            SL[(r["effect_type"], r["field_path"].lstrip("/"))] = r["answer_kind"]
    report["checks"]["_same_leaf_scope"] = {
        "rules": {f"{t}/{f}": k for (t, f), k in sorted(SL.items())},
        "note": ("从 field_dictionary.json 读取：36／1003／1005／1026 在攻/移/伤三路径"
                 "复用 type 8 分支的全部规则"),
    }
    j_bad, j_checked, j_dir, j_dir_bad = [], 0, 0, []
    j_seen, j_bad_seen, j_dir_seen = set(), set(), set()
    j_instances = 0
    for rkey, r in holders:
        if r.get("table") != "skilllist" or r.get("effect_type") not in (36, 1003, 1005, 1026):
            continue
        raw = h_skill_cache.get(r["record_id"]) or h_skill_apk.get(r["record_id"])
        if raw is None:
            j_bad.append({"rec_key": rkey, "why": "raw skilllist record missing"})
            continue
        for a in r.get("answers") or []:
            f = a["f"].lstrip("/")
            ukey = (r.get("table"), r.get("record_id"), r.get("layer"), a["f"])
            kind = SL.get((r["effect_type"], f))
            if kind is None or ukey in j_seen:
                continue
            j_seen.add(ukey)
            j_checked += 1
            if raw.get(f) != a["raw"]:
                j_bad.append({"rec_key": rkey, "field": f, "stored": a["raw"],
                              "raw_source": raw.get(f)})
                continue
            val = str(a.get("value") or "")
            v = float(a["raw"])
            if kind == "attack_mult":
                want = ("本项提高" if v > 1 else "本项降低" if v < 1 else "本项中性")
                if not val.startswith("自身攻击×") or want not in val:
                    j_bad.append({"rec_key": rkey, "field": f, "why": "attack slot wording",
                                  "raw": a["raw"], "text": val, "want": want})
            if kind == "move_mult":
                want = ("本项中性" if v == 1 else f"{(v - 1) * 100:+.6g}%")
                if not val.startswith("移动速度×") or want not in val:
                    j_bad.append({"rec_key": rkey, "field": f, "why": "move slot wording",
                                  "raw": a["raw"], "text": val, "want": want})
            if kind == "take_mult":
                want = ("本项减伤" if v < 1 else "本项增伤" if v > 1 else "本项中性")
                if not val.startswith("受伤量×") or want not in val:
                    j_bad.append({"rec_key": rkey, "field": f, "why": "take slot wording",
                                  "raw": a["raw"], "text": val, "want": want})
                # the reducing case is the one that gets confused with a flat defence
                # amount, so it must carry the disclaimer (the >1 case reads as 增伤)
                if v < 1 and "不是固定防御量" not in val:
                    j_bad.append({"rec_key": rkey, "field": f,
                                  "why": "take slot must disclaim flat defence", "text": val})
        # direction: damage-taken text must agree with param3's sign
        text = raw.get("text") or ""
        dkey = (r.get("table"), r.get("record_id"), r.get("layer"))
        if re.search(r"受けるダメージ[^。]{0,12}(減少|減る)", text):
            ans = next((a for a in r.get("answers") or [] if a["f"] == "/param3"), None)
            if dkey not in j_dir_seen:
                j_dir_seen.add(dkey)
                j_dir += 1
                if (ans is None or not float(ans.get("raw") or 0) < 1
                        or "减伤" not in (ans.get("value") or "")):
                    j_dir_bad.append({"rec_key": rkey, "raw": (raw.get("param3")),
                                      "answer": (ans or {}).get("value")})
        # the dealt-damage quantity never lives on param3: if a record's text only talks
        # about 与えるダメージ and answers param3, the answer must be neutral (==1)
        if (re.search(r"与えるダメージ[^。]{0,12}増加", text)
                and not re.search(r"受けるダメージ", text)):
            ans = next((a for a in r.get("answers") or [] if a["f"] == "/param3"), None)
            if (ans is not None and abs(float(ans.get("raw") or 0) - 1.0) > 1e-6
                    and dkey not in j_dir_seen):
                j_dir_seen.add(dkey)
                j_dir_bad.append({"rec_key": rkey, "why": "dealt-damage text drove param3",
                                  "raw": raw.get("param3"), "answer": ans.get("value")})
    report["checks"]["J_same_leaf_reuse"] = {
        "ok": not j_bad and not j_dir_bad, "answers_checked": j_checked,
        "scope": "顶层记录＋内嵌子效果记录，按（表,记录,层,字段）去重（子记录被多父共享只计一次）",
        "mismatches": j_bad[:5], "mismatch_count": len(j_bad),
        "damage_reduction_text_records": j_dir, "direction_failures": j_dir_bad[:5],
        "note": ("逐条重读原始 skilllist：答案原值等于原始 param；param3<1 答『减伤』、>1 答『增伤』，"
                 "且不得写成固定防御量；只写「与えるダメージが増加」的记录 param3 必须保持中性 1.0"),
    }
    ok_all &= (not j_bad) and (not j_dir_bad)

    # ------------------------------------------------------------------ K
    # K: P2 batch 5 -- the composite branches. The (type, field) -> answer_kind map is
    #    read from the *published* rule dictionary, so a new composite rule cannot be
    #    added without being covered here. Each answer's raw value is re-read straight
    #    from the decoded skilllist document and its wording is checked against the
    #    conversion that was traced in the native image (fixed multiplier vs a term that
    #    scales with the mana count / the hyper gauge).
    comp_dict = jload(BASE / "skilllist_types" / "field_dictionary.json")
    COMP = {(r["effect_type"], r["field_path"].lstrip("/")): r["answer_kind"]
            for r in comp_dict if r.get("effect_type") in (67, 80, 96, 1036)}
    report["checks"]["_composite_scope"] = {
        "rules": {f"{t}/{f}": k for (t, f), k in sorted(COMP.items())},
        "note": "从 field_dictionary.json 读取；96 的 param2／param3 自 P2 第 6 批起有规则"
                "（按调用方实参 damageType 择槽），不再是缺证槽",
    }
    k_bad, k_checked, k_dir, k_dir_bad = [], 0, 0, []
    k_seen, k_dir_seen, k_note = set(), set(), []
    k_scrap_pin, k_mana_pin = [], []
    for rkey, r in holders:
        et = r.get("effect_type")
        if r.get("table") != "skilllist" or et not in (67, 80, 96, 1036):
            continue
        raw = h_skill_cache.get(r["record_id"]) or h_skill_apk.get(r["record_id"])
        if raw is None:
            k_bad.append({"rec_key": rkey, "why": "raw skilllist record missing"})
            continue
        for a in r.get("answers") or []:
            f = a["f"].lstrip("/")
            ukey = (r.get("table"), r.get("record_id"), r.get("layer"), a["f"])
            kind = COMP.get((et, f))
            if kind is None or ukey in k_seen:
                continue
            k_seen.add(ukey)
            k_checked += 1
            if raw.get(f) != a["raw"]:
                k_bad.append({"rec_key": rkey, "field": f, "stored": a["raw"],
                              "raw_source": raw.get(f)})
                continue
            val = str(a.get("value") or "")
            v = float(a["raw"])
            n = int(v)
            want = None
            if kind == "attack_mult":
                want = "自身攻击×"
            elif kind == "move_mult":
                want = "移动速度×"
            elif kind == "take_mult":
                want = "受伤量×"
                if v < 1 and "不是固定防御量" not in val:
                    k_bad.append({"rec_key": rkey, "field": f, "why": "take<1 must disclaim flat defence",
                                  "text": val})
            elif kind == "crit_rate":
                want = "暴击率"
            elif kind == "crit_dmg":
                want = "暴击伤害系数"
            elif kind == "chara_count_threshold":
                want = f"命中角色数 ≥ {n}"
            elif kind == "mana_count_threshold":
                want = f"当前玛那"
                if f"≥ {n}" not in val:
                    k_bad.append({"rec_key": rkey, "field": f, "why": "mana threshold value missing",
                                  "text": val})
            elif kind == "mana_count_cap":
                want = f"min("
            elif kind == "mana_selector":
                want = "任一" if n == 0 else "所有"
            elif kind.startswith("mana_coeff_"):
                # the counting object is selected by the record's own param0: a truncated
                # zero takes the scrap-mana path (flag 0x20), anything else the job-flag
                # path. This is the branch the review found mis-worded, so it is pinned
                # per record rather than left to the static template.
                p0 = None
                for src in (r.get("answers") or [], r.get("unexplained") or []):
                    for x in src:
                        if x.get("f") == "/param0":
                            p0 = x.get("raw")
                if p0 is not None:
                    if int(float(p0)) == 0:
                        k_scrap_pin.append((rkey, int(float(p0)), "斯库拉普" in val))
                        if "斯库拉普" not in val:
                            k_bad.append({"rec_key": rkey, "field": f,
                                          "why": "int(param0)==0 must name the scrap mana",
                                          "param0": p0, "text": val})
                    else:
                        k_mana_pin.append((rkey, int(float(p0)), "斯库拉普" not in val))
                        if "斯库拉普" in val:
                            k_bad.append({"rec_key": rkey, "field": f,
                                          "why": "int(param0)!=0 must not name the scrap mana",
                                          "param0": p0, "text": val})
                want = "min("
                if kind in ("mana_coeff_move", "mana_coeff_take") and "1 +" not in val:
                    k_bad.append({"rec_key": rkey, "field": f, "why": "multiplicative term must read 1 +",
                                  "text": val})
            elif kind.startswith("hyper_"):
                want = "hyperGauge ÷ 1000"
                if kind in ("hyper_attack_mult", "hyper_move_mult", "hyper_take_mult") and "1 +" not in val:
                    k_bad.append({"rec_key": rkey, "field": f, "why": "multiplicative term must read 1 +",
                                  "text": val})
            if kind == "mana_count_cap":
                p0 = None
                for src in (r.get("answers") or [], r.get("unexplained") or []):
                    for x in src:
                        if x.get("f") == "/param0":
                            p0 = x.get("raw")
                if p0 is not None:
                    if int(float(p0)) == 0:
                        k_scrap_pin.append((rkey, int(float(p0)), "斯库拉普" in val))
                        if "斯库拉普" not in val:
                            k_bad.append({"rec_key": rkey, "field": f,
                                          "why": "cap answer must name the scrap mana",
                                          "param0": p0, "text": val})
                    else:
                        k_mana_pin.append((rkey, int(float(p0)), "斯库拉普" not in val))
                        if "斯库拉普" in val:
                            k_bad.append({"rec_key": rkey, "field": f,
                                          "why": "cap answer must not name the scrap mana",
                                          "param0": p0, "text": val})
                # the engine does not cap when the cap value is < 1, so the correct
                # statement must appear; the old wrong phrasing is checked separately
                # ("而非按 0 计" is a legitimate denial, not a claim)
                if "不设上限" not in val:
                    k_bad.append({"rec_key": rkey, "field": f,
                                  "why": "cap answer must state the <1 = no-cap semantics",
                                  "n": n, "text": val})
                if "时按 0 计（不生效）" in val:
                    k_bad.append({"rec_key": rkey, "field": f,
                                  "why": "old inverted cap wording still present",
                                  "text": val})
            if want is not None and want not in val:
                k_bad.append({"rec_key": rkey, "field": f, "why": "wording", "want": want, "text": val})
        if et == 96:
            for f in ("param2", "param3"):
                if raw.get(f) is None:
                    continue
                ans = next((x for x in r.get("answers") or [] if x["f"] == "/" + f), None)
                if ans is None:
                    k_bad.append({"rec_key": rkey, "field": f,
                                  "why": "96 attack slot has a raw value but no published answer"})
                    continue
                val = str(ans.get("value") or "")
                want_clause = ("≠ eDamageType.Skill" if f == "param2" else "== eDamageType.Skill")
                if want_clause not in val:
                    k_bad.append({"rec_key": rkey, "field": f, "why": "damageType clause missing",
                                  "want": want_clause, "text": val})
        # direction: text saying damage taken decreases must agree with param3 < 1
        text = raw.get("text") or ""
        dkey = (r.get("table"), r.get("record_id"), r.get("layer"))
        if re.search(r"受けるダメージ[^。]{0,12}(減少|減る)", text) and dkey not in k_dir_seen:
            ans = next((a for a in r.get("answers") or [] if a["f"] == "/param3"), None)
            if ans is not None:
                k_dir_seen.add(dkey)
                k_dir += 1
                v3 = float(ans.get("raw") or 0)
                if v3 > 1 and "增伤" in (ans.get("value") or ""):
                    # the answer contradicts the text's direction: that is a real inversion
                    k_dir_bad.append({"rec_key": rkey, "raw": raw.get("param3"),
                                      "answer": ans.get("value"), "text": text[:60]})
                elif v3 == 1:
                    # data outranks the description: record it, do not fail
                    k_note.append({"rec_key": rkey, "text": text[:60],
                                   "why": "正文写受伤量减少而 param3=1（本项中性），按数据优先记观察"})
    report["checks"]["K_composite_branches"] = {
        "ok": not k_bad and not k_dir_bad, "answers_checked": k_checked,
        "mismatches": k_bad[:5], "mismatch_count": len(k_bad),
        "damage_reduction_text_records": k_dir, "direction_failures": k_dir_bad[:5],
        "text_vs_data_observations": k_note[:5], "text_vs_data_count": len(k_note),
        "param0_scrap_pinned": {"records": len(k_scrap_pin),
                                "all_named_scrap": all(v[2] for v in k_scrap_pin)},
        "param0_mana_pinned": {"records": len(k_mana_pin),
                               "none_named_scrap": all(v[2] for v in k_mana_pin)},
        "scope": "顶层记录＋内嵌子效果记录，按（表,记录,层,字段）去重",
        "note": ("逐条重读原始 skilllist：原值必须等于记录字段值；固定倍率槽答成倍率，"
                 "按玛那/hyperGauge 缩放的槽必须写出该因子且乘算槽要写「1 +」；"
                 "96 的 param2／param3 必须带各自的 damageType 条件子句（param2 非 Skill／param3 Skill）；"
                 "96 的计数对象按记录自身 int(param0) 钉死"
                 "（==0 → 必须写斯库拉普玛那，!=0 → 必须不写）；96 的上限槽 <1 时必须写「不设上限」；"
                 "正文写受伤量减少而 param3=1 只记观察"
                 "（数据优先于正文），仅当答案方向与正文相反才判失败"),
    }
    ok_all &= (not k_bad) and (not k_dir_bad)

    # ---------------------------------------------------------------- P2 batch 6 (L)
    # filter dictionaries + type 1059, straight from the raw master/cache tables
    P6_SLOTS = {"67": ("iParam0", "flag0_0", "param8"),
                "80": ("iParam0",),
                "96": ("iParam0",),
                "1059": ("iParam0", "flag0_0", "param8", "iParam1", "flag1_0", "param9")}
    P6_NUM = {"1059": {"param0": "触发阈值", "param1": "队伍攻击率 ×", "param2": "移动速度 ×",
                       "param3": "受伤量 ×", "param4": "暴击率 += ", "param5": "暴击伤害系数",
                       "param6": "目标最大HP", "param7": "回复间隔"}}
    HOMES = {int(x["home_id"]): x["name"]
             for x in raw_cache("homelist", "homelist")}
    JOBS = {0: "戦士", 1: "弓使い", 2: "魔法使い", 3: "僧侶", 4: "騎士", 5: "ALMIGHTY"}
    WEP = {22: "斬", 23: "打", 24: "突", 25: "弓", 26: "魔", 27: "聖", 28: "拳", 29: "銃", 30: "狙"}
    l_bad, l_checked, l_by_type = [], 0, collections.Counter()
    l_decode_checked, l_decode_bad = 0, []
    l_seen = set()
    for rkey, r in holders:
        et = r.get("effect_type")
        tab = r.get("table")
        slots = P6_SLOTS.get(str(et))
        if tab != "skilllist" or not slots:
            continue
        raw = h_skill_cache.get(r["record_id"]) or h_skill_apk.get(r["record_id"])
        if raw is None:
            l_bad.append({"rec_key": rkey, "why": "raw skilllist record missing"})
            continue
        for a in r.get("answers") or []:
            f = a["f"].lstrip("/")
            ukey = (tab, r.get("record_id"), r.get("layer"), a["f"])
            if f not in slots or ukey in l_seen:
                continue
            l_seen.add(ukey)
            l_checked += 1
            l_by_type[et] += 1
            if raw.get(f) != a["raw"]:
                l_bad.append({"rec_key": rkey, "field": f, "stored": a["raw"],
                              "raw_source": raw.get(f)})
                continue
            val = str(a.get("value") or "")
            # the answer's decoded names must be re-derivable from the record's own raw value
            if f in ("iParam0", "iParam1"):
                want = [JOBS[i] for i in range(6) if int(a["raw"]) & (1 << i)]
                if want and not all(w in val for w in want):
                    l_decode_bad.append({"rec_key": rkey, "field": f, "want": want, "text": val})
                l_decode_checked += 1
            elif f in ("flag0_0", "flag1_0"):
                m = int(a["raw"]) & 0x7FC00000
                want = [WEP[i] for i in range(22, 31) if m & (1 << i)]
                if want and not all(f"{w}(" in val for w in want):
                    l_decode_bad.append({"rec_key": rkey, "field": f, "want": want, "text": val})
                l_decode_checked += 1
            elif f in ("param8", "param9"):
                n0 = int(a["raw"])
                groups = [x for x in (n0 % 100, (n0 // 100) % 100, (n0 // 10000) % 100) if x]
                want = [HOMES.get(g) for g in groups if HOMES.get(g)]
                if want and not all(w in val for w in want):
                    l_decode_bad.append({"rec_key": rkey, "field": f, "want": want, "text": val})
                if not groups and "不按出身筛选" not in val:
                    l_decode_bad.append({"rec_key": rkey, "field": f, "want": "0=不筛选", "text": val})
                l_decode_checked += 1
            if et == 1059 and f in P6_NUM["1059"]:
                want = P6_NUM["1059"][f]
                if want not in val:
                    l_bad.append({"rec_key": rkey, "field": f, "want": want, "text": val})
        if et == 1059 and r.get("answers"):
            thr = next((x for x in r["answers"] if x["f"] == "/param0"), None)
            if thr is not None and "任一" not in str(thr.get("value") or ""):
                l_bad.append({"rec_key": rkey, "field": "param0",
                              "why": "1059 count filter is OR (任一), 67 is AND",
                              "text": thr.get("value")})
    chain = jload(BASE / "skilllist_types" / "union_count_chains.json")
    l_bad += [] if chain.get("verified") else [{"why": "union_count_chains.verified is not true"}]
    report["checks"]["L_filters_and_union_count"] = {
        "ok": not l_bad and not l_decode_bad, "answers_checked": l_checked,
        "answers_by_type": {str(k): v for k, v in sorted(l_by_type.items())},
        "decode_checked": l_decode_checked,
        "mismatches": l_bad[:5], "mismatch_count": len(l_bad),
        "decode_mismatches": l_decode_bad[:5], "decode_mismatch_count": len(l_decode_bad),
        "homelist_ids": len(HOMES),
        "union_chain_verified": chain.get("verified"),
        "scope": "顶层记录＋内嵌子效果记录，按（表,记录,层,字段）去重",
        "note": ("筛选位答案必须由记录自身的 iParam0／flag0_0／flag1_0／param8／param9 原值重新解码"
                 "得到（职业位图逐位、武器位图取 0x7fc00000、出身按两位分组查 homelist）；"
                 "1059 的数值槽必须出现对应措辞，计数阈值必须写「任一」（与 67 的「同时」相反）"),
    }
    ok_all &= (not l_bad) and (not l_decode_bad)

    # ---------------------------------------------------------------- M: denju chain
    # Independent re-derivation straight from the decoded denju table: every answer a
    # denju page shows for a taught skill must be re-derivable from
    # denju.patternidN -> bosspattern -> bossskill in the raw sources, and the effect
    # type must equal that bossskill's skillid0.
    m_den = raw_cache("denju", "denju")
    m_lb_raw = raw_cache("denju_lblist", "denju_limit_break_info")
    m_pat_cache = {r["patternid"]: r for r in raw_cache("bossinfo", "bossinfo", "bosspattern")}
    m_pat_apk = {r["patternid"]: r for r in raw_master("_mdBossInfo.json", "bosspattern")}
    m_sk_cache = {r["skillid"]: r for r in raw_cache("bossinfo", "bossinfo", "bossskill")}
    m_sk_apk = {r["skillid"]: r for r in raw_master("_mdBossInfo.json", "bossskill")}
    m_want = {}          # denju_id -> {(patternid, skillid): raw skill record}
    m_bad, m_checked, m_unresolved = [], 0, 0
    m_sa_checked = 0
    for d in m_den:
        cid = d["denju_id"]
        for i in range(9):
            pv = d.get(f"patternid{i}")
            if not pv:
                continue
            pat = m_pat_cache.get(pv) or m_pat_apk.get(pv)
            if pat is None:
                m_unresolved += 1
                continue
            for k in sorted(kk for kk in pat if kk.startswith("skillid")):
                sv = pat.get(k)
                if not sv:
                    continue
                sk = m_sk_cache.get(sv) or m_sk_apk.get(sv)
                if sk is None:
                    m_unresolved += 1
                    continue
                m_want.setdefault(cid, {})[(pv, sv)] = sk
    # the denju rows' own parameter slots (there must be none) and the key set
    m_param_keys = sorted({k for d in m_den for k in d
                           if k.startswith("skillparam") or k.startswith("param")})
    m_denju_children = 0
    for rkey, r in holders:
        if r.get("table") != "denju":
            continue
        cid = r.get("record_id")
        for ch in r.get("children") or []:
            if not isinstance(ch, dict):
                continue
            kind = ch.get("link_kind")
            want = m_want.get(cid) or {}
            if kind == "boss_skill.s_ability":
                # the SA/超过能力 cross-reference: its skill id must be one of the
                # s_ability values of the skills reachable from this denju row
                sa_ids = {v.get("s_ability") for v in want.values() if v.get("s_ability")}
                m_sa_checked += 1
                if ch.get("record_id") not in sa_ids:
                    m_bad.append({"denju_id": cid, "sa_skill": ch.get("record_id"),
                                  "why": "该 SA skilllist 记录不在这条 denju 链的 s_ability 集合内",
                                  "chain_s_ability": sorted(x for x in sa_ids if x)})
                continue
            for a in ch.get("answers") or []:
                m_denju_children += 1
                want_recs = [v for (_p, sv), v in want.items() if sv == ch.get("record_id")]
                if not want_recs:
                    m_bad.append({"denju_id": cid, "child": ch.get("record_id"),
                                  "why": "该 bossskill 不能由该 denju 行的 patternidN 重新推出"})
                    continue
                want_rec = want_recs[0]
                f = a["f"].lstrip("/")
                if want_rec.get(f) != a["raw"]:
                    m_bad.append({"denju_id": cid, "skill": ch.get("record_id"), "field": f,
                                  "stored": a["raw"], "raw_source": want_rec.get(f)})
                if f == "skillid0" and a["raw"] != ch.get("effect_type"):
                    m_bad.append({"denju_id": cid, "skill": ch.get("record_id"),
                                  "why": "effect_type 与源记录 skillid0 不一致"})
                m_checked += 1
    # denju_lblist items must resolve to the same patterns that carry the answers
    m_lb_bad = []
    for row in m_lb_raw:
        for it in row.get("denju_limit_break") or []:
            pv = it.get("patternid0")
            if pv and not (m_pat_cache.get(pv) or m_pat_apk.get(pv)):
                m_lb_bad.append({"cid": row.get("cid"), "patternid0": pv})
    m_struct = None
    try:
        m_struct = jload(BASE / "denju_skills" / "structure.json")
    except OSError:
        m_struct = None
    m_bad += [] if m_param_keys == [] else [{"why": "denju 行出现了参数槽键", "keys": m_param_keys}]
    m_bad += [{"why": "denju_limit_break patternid0 无法解析", **x} for x in m_lb_bad]
    if m_struct is not None:
        if m_struct["skillparam_slot_keys_present_count"] != 0:
            m_bad.append({"why": "structure.json 声明存在 skillparam 槽"})
        if m_struct["row_count"] != len(m_den):
            m_bad.append({"why": "structure.json 行数与原始表不一致",
                          "json": m_struct["row_count"], "raw": len(m_den)})
        if len(m_struct["unresolved_patternids"]) != m_unresolved:
            m_bad.append({"why": "未解析 patternid 数与原始表复算不一致",
                          "json": len(m_struct["unresolved_patternids"]), "raw": m_unresolved})
    report["checks"]["M_denju_chain"] = {
        "ok": not m_bad, "denju_rows": len(m_den),
        "denju_rows_with_resolvable_chain": len(m_want),
        "answers_checked_on_denju_pages": m_checked,
        "sa_children_checked": m_sa_checked,
        "unresolved_pattern_or_skill_refs": m_unresolved,
        "param_slot_keys_on_denju_rows": m_param_keys,
        "denju_lb_rows": len(m_lb_raw),
        "denju_lb_items": sum(len(r.get("denju_limit_break") or []) for r in m_lb_raw),
        "structure_json_checked": m_struct is not None,
        "mismatch_count": len(m_bad), "mismatches": m_bad[:5],
        "scope": "顶层记录＋内嵌子记录；denju 页上的每条答案都从原始 denju→bosspattern→bossskill 重算",
        "note": ("denju 行必须没有 skillparam／param 槽位；挂到 denju 页上的每条答案必须能由该行"
                 "自己的 patternidN 解析出的 bossskill 原值重算得到；未解析引用计数必须与 "
                 "denju_skills/structure.json 一致"),
    }
    ok_all &= not m_bad

    # ------------------------------------------------------------------ N
    # attack-family boss types (P2 batch 8): every answer produced by the new slot
    # rules must be re-derivable from the raw decoded tables alone.  The damage base
    # itself is a native claim (checked in boss_attack_types/native_checks.json); the
    # *data* side checked here is: the slot the rule names is the slot the raw record
    # carries, the transfer to charainfo only happens where the value is identical to a
    # type-matched boss skill, and no reachable record silently loses an answer.
    nd = BASE / "boss_attack_types" / "field_dictionary.json"
    n_new = {}
    if nd.exists():
        for r in jload(nd):
            n_new[(r["table"], r["effect_type"], r["field_path"])] = r["answer_kind"]
    n_cache_boss = collections.defaultdict(list)
    for r in raw_cache("bossinfo", "bossinfo", "bossskill"):
        n_cache_boss[r.get("skillid")].append(r)
    n_apk_boss = collections.defaultdict(list)
    for r in raw_master("_mdBossInfo.json", "bossskill"):
        n_apk_boss[r.get("skillid")].append(r)

    def boss_rec(skillid, layer):
        rows = n_cache_boss.get(skillid) if layer == "CACHE" else n_apk_boss.get(skillid)
        if not rows and layer == "CACHE":
            rows = n_apk_boss.get(skillid)
        return rows[0] if rows else None

    def f32(x):
        if x is None or isinstance(x, bool) or not isinstance(x, (int, float)):
            return x
        return struct.unpack("<f", struct.pack("<f", float(x)))[0]

    def same_value(a, b):
        """The pipeline's own transfer caliber: float32-normalised, omitted reads as 0.0."""
        return f32(0.0 if a is None else a) == f32(0.0 if b is None else b)

    n_cache_chara = {r.get("cid"): r for r in raw_cache("charainfo", "charainfo")}
    n_apk_chara = {r.get("cid"): r for r in raw_master("_mdCharacter.json", "charainfo")}
    n_cache_pat = {r.get("patternid"): r for r in raw_cache("bossinfo", "bossinfo", "bosspattern")}
    n_apk_pat = {r.get("patternid"): r for r in raw_master("_mdBossInfo.json", "bosspattern")}

    n_checked = collections.Counter()
    n_f0 = collections.Counter()
    n_bad = []
    n_missing = []
    for r in jl(BASE / "profiles" / "records.jsonl"):
        for holder in [r] + [c for c in (r.get("children") or [])
                             if isinstance(c, dict) and "answers" in c]:
            table = holder.get("table")
            rid = holder.get("record_id")
            layer = holder.get("layer")
            for a in holder.get("answers") or []:
                rk = (a.get("rule_key") or "").split("|")
                if len(rk) != 3 or not rk[1].lstrip("-").isdigit():
                    continue
                kind = n_new.get((rk[0], int(rk[1]), rk[2]))
                if kind is None:
                    continue
                n_checked[kind] += 1
                field = a["f"].lstrip("/")
                if table == "bossskill":
                    raw = boss_rec(rid, layer)
                    if raw is None or raw.get(field) != a.get("raw"):
                        n_bad.append({"table": table, "record": rid, "layer": layer,
                                      "field": a["f"], "answer_raw": a.get("raw"),
                                      "raw": (raw or {}).get(field)})
                    continue
                # charainfo: raw equality plus the value-identical transfer premise
                raw = n_cache_chara.get(rid) or n_apk_chara.get(rid)
                if raw is None or raw.get(field) != a.get("raw"):
                    n_bad.append({"table": table, "record": rid, "field": a["f"],
                                  "answer_raw": a.get("raw"),
                                  "raw": (raw or {}).get(field)})
                    continue
                v0 = (raw.get("skillid") or [0])[0]
                ok_premise = False
                reachable = False
                for i in range(9):
                    pid = raw.get(f"pattern{i}")
                    if not pid:
                        continue
                    pat = n_cache_pat.get(pid) or n_apk_pat.get(pid)
                    if not pat:
                        continue
                    for k in sorted(kk for kk in pat if kk.startswith("skillid")):
                        b = boss_rec(pat.get(k), "CACHE") or boss_rec(pat.get(k), "APK")
                        if b is None:
                            continue
                        reachable = True
                        if b.get("skillid0") == v0 and same_value(b.get(field), a.get("raw")):
                            ok_premise = True
                if not reachable:
                    # P2-9 F0 caliber: no reachable pattern skill -> the record's own
                    # value is executed through the _CreateExecSkillList fallback, so no
                    # boss-side value equality is required (G2 covers the path premise)
                    n_f0[kind] += 1
                    continue
                if not ok_premise:
                    n_bad.append({"table": table, "record": rid, "field": a["f"],
                                  "answer_raw": a.get("raw"), "premise": "无同型且同值的 boss 记录"})
        # no reachable boss record of a new-rule type may silently lose its answer
        if r.get("table") == "bossskill" and r.get("effect_type") in {
                t for (tb, t, f) in n_new if tb == "bossskill"}:
            raw = boss_rec(r.get("record_id"), r.get("layer"))
            if raw is None:
                continue
            have = {a["f"] for holder in [r] + [c for c in (r.get("children") or [])
                                             if isinstance(c, dict)]
                    for a in holder.get("answers") or []}
            for (tb, t, f) in n_new:
                if tb == "bossskill" and t == r.get("effect_type") and raw.get(f.lstrip("/")) is not None \
                        and f not in have:
                    n_missing.append({"record": r.get("record_id"), "type": t, "field": f})
    report["checks"]["N_attack_family_slots"] = {
        "ok": not n_bad and not n_missing,
        "new_rule_keys": len(n_new),
        "answers_checked_by_kind": dict(sorted(n_checked.items())),
        "answers_checked_total": sum(n_checked.values()),
        "f0_answers_without_boss_premise": dict(sorted(n_f0.items())),
        "f0_answers_without_boss_premise_total": sum(n_f0.values()),
        "bossskill_and_charainfo_records_without_a_rule_answer": len(n_missing),
        "mismatch_count": len(n_bad),
        "mismatches": n_bad[:5],
        "missing_sample": n_missing[:5],
        "scope": ("顶层记录＋内嵌子记录；新规则命中的每条答案都从原始 bossskill／charainfo 表重算，"
                  "有 pattern 可解析的 charainfo 侧还要求与自身 pattern 命中的同型 boss 记录同值（迁移前提）；"
                  "无可达 pattern 的 charainfo 侧（F0）改为核对本记录原值，不要求 boss 侧同值"),
        "note": ("本区只核数据侧（槽位取值与迁移前提）；伤害基值为原生结论，"
                 "由 boss_attack_types/native_checks.json 的受控执行负责；F0 的执行路径前提由 G2 核对"),
    }
    ok_all &= not n_bad and not n_missing

    # ------------------------------------------------------------------ O
    # O: p2b9 rectification -- the *rendered answer text* of the three slots the review
    #    flagged must match the type-specific semantics (F1/F2/F3), and every F0 answer
    #    must carry its human-readable evidence-path note (F4).  Only the products are
    #    read here; the semantics behind the wording live in boss_attack_types/type_rules
    #    and cp_paths/path_evidence.json.
    o_bad, o_stats = [], collections.Counter()
    note_by_rid = {}
    for r in jl(BASE / "profiles" / "records.jsonl"):
        for h in [r] + [c for c in (r.get("children") or [])
                        if isinstance(c, dict) and "answers" in c]:
            for a in h.get("answers") or []:
                note_by_rid[(h.get("table"), h.get("record_id"), a["f"])] = a.get("note") or ""
                k, text = a.get("rule_key"), a.get("value") or ""
                if k == "bossskill|1|/skillparam3":
                    o_stats["type1_sp3"] += 1
                    n = int(a["raw"])
                    if "尝试上限" in text:
                        o_bad.append({"why": "type1 sp3 仍用旧「尝试上限」措辞",
                                      "rec": h.get("rec_key"), "raw": a["raw"], "text": text[:140]})
                    elif "总攻击次数" not in text or f"= {n} + 1" not in text:
                        o_bad.append({"why": "type1 sp3 未写出 总攻击次数＝trunc(raw)+1",
                                      "rec": h.get("rec_key"), "raw": a["raw"],
                                      "expect": f"= {n} + 1", "text": text[:140]})
                elif k == "bossskill|110|/skillparam6":
                    o_stats["type110_sp6"] += 1
                    if "范围外也消耗" in text:
                        o_bad.append({"why": "type110 sp6 仍含「范围外也消耗预算」",
                                      "rec": h.get("rec_key"), "text": text[:140]})
                elif k == "bossskill|47|/skillparam4":
                    o_stats["type47_sp4"] += 1
                    if "SpreadBullet" not in text:
                        o_bad.append({"why": "type47 sp4 缺 SpreadBullet 中转注记",
                                      "rec": h.get("rec_key"), "text": text[:140]})
    f0_ans, f0_ans_no_note = 0, 0
    for x in jl(BASE / "charainfo_params" / "answers.jsonl"):
        if x.get("equivalence_class") != "F0_NO_PATTERN_FALLBACK":
            continue
        f0_ans += 1
        note = note_by_rid.get(("charainfo", x.get("cid"), x["field_path"]), "")
        if not note.startswith("证据路径（P2 第 9 批）"):
            f0_ans_no_note += 1
            if len(o_bad) < 8:
                o_bad.append({"why": "F0 答案缺人读证据路径注记", "cid": x.get("cid"),
                              "field": x["field_path"], "note": note[:60]})
    report["checks"]["O_p2b9_answer_text_and_note_pinning"] = {
        "ok": not o_bad,
        "counts": dict(o_stats),
        "f0_answers": f0_ans,
        "f0_answers_without_human_note": f0_ans_no_note,
        "mismatch_count": len(o_bad), "mismatches": o_bad[:5],
        "scope": ("逐条读答案 value：type1 sp3 必须写「总攻击次数 = trunc(raw) + 1」且无「尝试上限」；"
                  "type110 sp6 不得含「范围外也消耗预算」；type47 sp4 必须点名 SpreadBullet；"
                  "由等价门控产出的 F0 答案必须带人读「证据路径（P2 第 9 批）」注记"),
        "note": ("本区只读产物文本、raw 与注记；措辞语义依据见 boss_attack_types/type_rules.json 与 "
                 "cp_paths/path_evidence.json；type105 的 sp6 不在本区（其语义确有范围重判）"),
    }
    ok_all &= not o_bad

    # ------------------------------------------------------------------ P
    # P: P2 batch 10 -- independently re-read the raw tables and check the new answers.
    #    (a) every new rule's answer raw value equals the *raw record field* it claims
    #    (b) the heal family's rendered wording carries the shared base/consumer, the
    #        target selection and the per-type over-heal slot
    #    (c) the _skillChainRate distinction is rendered (12/14 vs 28/31/46)
    #    (d) the type-43 repeat count uses the "+1" caliber, not a cap
    #    (e) the new rule keys do not collide with the three earlier dictionaries
    #    (f) the remaining "unknown only" characters are exactly the documented set
    p10_dict = jload(BASE / "boss_heal_types" / "field_dictionary.json")
    p10_keys = {f"{r['table']}|{r['effect_type']}|{r['field_path']}": r for r in p10_dict}
    earlier = set()
    for r in jload(ROOT / "output" / "card_comparison_cid30236" / "field_dictionary.json"):
        fp = r.get("field_path") or ""
        earlier.add((r.get("table") or "skilllist", r.get("effect_type"),
                     fp if fp.startswith("/") else "/" + fp))
    for r in jload(ROOT / "output" / "boss_heal" / "field_dictionary.json"):
        if "bossskill" in (r.get("file_table") or ""):
            fp = r.get("field_path") or ""
            earlier.add(("bossskill", r.get("effect_type"), fp if fp.startswith("/") else "/" + fp))
    for r in jload(BASE / "skilllist_types" / "field_dictionary.json"):
        earlier.add((r.get("table") or "skilllist", r.get("effect_type"), r.get("field_path")))
    for r in jload(BASE / "boss_attack_types" / "field_dictionary.json"):
        earlier.add((r["table"], r["effect_type"], r["field_path"]))

    def _raw_of(table, rid, field):
        """the raw slot value straight out of the unpacked table (cache first)."""
        if table == "bossskill":
            for row in raw_cache("bossinfo", "bossinfo", "bossskill"):
                if row.get("skillid") == rid:
                    return row.get(field.lstrip("/"))
        else:
            for row in raw_cache("charainfo", "charainfo"):
                if row.get("cid") == rid:
                    v = row.get(field.lstrip("/"))
                    if v is not None:
                        return v
                    for row2 in raw_master("_mdCharacter.json", "charainfo"):
                        if row2.get("cid") == rid:
                            return row2.get(field.lstrip("/"))
                    return None
        return None

    p_bad, p_stats = [], collections.Counter()
    p_heal_targets = collections.Counter()
    for r in jl(BASE / "profiles" / "records.jsonl"):
        for h in [r] + [c for c in (r.get("children") or [])
                        if isinstance(c, dict) and "answers" in c]:
            for a in h.get("answers") or []:
                k = a.get("rule_key")
                if k not in p10_keys:
                    continue
                p_stats["answers"] += 1
                p_stats[f"type{a['rule_key'].split('|')[1]}"] += 1
                raw = _raw_of(h.get("table"), h.get("record_id"), a["f"])
                if raw is not None and a.get("raw") != raw:
                    if len(p_bad) < 8:
                        p_bad.append({"why": "答案 raw 与原始表字段不一致", "rule": k,
                                      "rec": h.get("rec_key"), "answer_raw": a.get("raw"),
                                      "record_raw": raw})
                text = a.get("value") or ""
                kind = a.get("kind") or ""
                t = a["rule_key"].split("|")[1]
                if kind == "单次回复量的技能基值系数":
                    p_stats["heal_base"] += 1
                    # the Exec_HEAL family carries a per-type target selection; other
                    # heal_base types (75) only carry the shared formula/consumer.
                    fam = t in ("10", "11", "12", "14", "26", "28", "31", "32", "46")
                    if not ("floor/clamp(float32(B × " in text and "CharaBehavior.Heal" in text
                            and "不是最终回血量" in text
                            and (not fam or "对象：" in text)):
                        p_bad.append({"why": "heal_base 文本缺基值/消费点/对象/边界",
                                      "rec": h.get("rec_key"), "text": text[:160]})
                    elif fam and "对象：" in text:
                        p_heal_targets[text.split("对象：", 1)[1].split("；")[0][:14]] += 1
                elif kind == "超上限（HP 上限）档位的附加槽":
                    p_stats["over_heal"] += 1
                    if not ("max(技能标志位算出的档位" in text and "1.2,1.3,1.4,1.6,1.8,2.0" in text):
                        p_bad.append({"why": "over_heal 文本缺 max 规则或位表",
                                      "rec": h.get("rec_key"), "text": text[:160]})
                    if k == "bossskill|46|/skillparam5":
                        # p2b10 review F1: type 46 shares type 28's over-heal floor load
                        p_stats["type46_sp5"] += 1
                        if ("允许回复到的 HP 上限比率 = max(技能标志位算出的档位" not in text
                                or "1.2,1.3,1.4,1.6,1.8,2.0" not in text
                                or "不是回复量倍数" not in (a.get("unit") or "")):
                            p_bad.append({"why": "type46 sp5 未按超上限比率渲染",
                                          "rec": h.get("rec_key"), "raw": a.get("raw"),
                                          "text": text[:160]})
                elif kind == "支援的移动速度增益系数":
                    p_stats["support_move"] += 1
                    if "_skillChainRate" not in text:
                        p_bad.append({"why": "12/14 的移动支援应乘 _skillChainRate",
                                      "rec": h.get("rec_key"), "text": text[:160]})
                elif kind == "支援的攻击增益系数" and t in ("28", "31", "46"):
                    p_stats["support_attack_raw"] += 1
                    if "本类型不乘 _skillChainRate" not in text:
                        p_bad.append({"why": "28/31/46 的攻击支援不得是乘 chainRate 的写法",
                                      "rec": h.get("rec_key"), "text": text[:160]})
                elif kind == "支援的攻击增益系数" and t in ("12", "14", "26", "23"):
                    p_stats["support_attack_chain"] += 1
                    if "× _skillChainRate" not in text:
                        p_bad.append({"why": "12/14/26/23 的攻击支援应乘 _skillChainRate",
                                      "rec": h.get("rec_key"), "text": text[:160]})
                elif kind == "重复攻击的次数上限" and t == "43":
                    p_stats["type43_cap"] += 1
                    if f"= {int(a['raw'])} + 1" not in text or "尝试上限" in text:
                        p_bad.append({"why": "type43 回数缺少 +1 口径", "rec": h.get("rec_key"),
                                      "raw": a["raw"], "text": text[:160]})
                elif kind == "落点位置偏移":
                    p_stats["fall_offset"] += 1
                    if "夹到地面范围" not in text:
                        p_bad.append({"why": "落点偏移未写夹紧范围", "rec": h.get("rec_key"),
                                      "text": text[:160]})
    collide = sorted(k for k in p10_keys
                     if (k.split("|")[0], int(k.split("|")[1]), k.split("|")[2]) in earlier)
    if collide:
        p_bad.append({"why": "新规则键与既有字典重叠（merge 只补缺键）", "keys": collide[:5]})
    # (f) recompute the remaining unknown-only characters from the products: a character
    #     whose every referenced record carries no answer and which has no baseline entry.
    ans_count = {}
    for _r in jl(BASE / "profiles" / "records.jsonl"):
        parts = (_r.get("rec_key") or "").split("|")
        if len(parts) < 3:
            continue
        key3 = (parts[0], parts[1], parts[2])
        n = len(_r.get("answers") or [])
        n += sum(len(c.get("answers") or [])
                 for c in (_r.get("children") or []) if isinstance(c, dict))
        ans_count[key3] = ans_count.get(key3, 0) + n
    bl_count = {}
    for line in jl(BASE / "profiles" / "profiles.jsonl"):
        bl_count[line["cid"]] = len(line.get("baseline") or [])
    unknown_cids = []
    for line in jl(BASE / "links" / "character_skills.jsonl"):
        cid = line.get("cid")
        total = bl_count.get(cid, 0)
        for g in line.get("groups") or []:
            for ref in g.get("records") or []:
                total += ans_count.get((ref.get("table"), str(ref.get("reference_id")),
                                        ref.get("layer")), 0)
        if total == 0:
            unknown_cids.append(cid)
    p_stats["remaining_unknown"] = len(unknown_cids)
    if len(unknown_cids) != 5:
        p_bad.append({"why": "仅未知角色数与本批声明不符", "count": len(unknown_cids),
                      "cids": sorted(unknown_cids)[:10]})
    report["checks"]["P_p2b10_new_rule_answers_and_remaining_unknown"] = {
        "ok": not p_bad, "counts": dict(p_stats),
        "heal_targets": dict(p_heal_targets),
        "colliding_keys": collide[:5],
        "mismatch_count": len(p_bad), "mismatches": p_bad[:5],
        "scope": ("直读 bossinfo/charainfo 原始表与 profiles 产物：新规则答案的 raw 必须等于原始字段；"
                  "回复量的基值/消费点/对象/边界与超上限位表必须逐条出现在文本里；"
                  "乘/不乘 _skillChainRate 的支援槽必须按类型分别渲染；type43 的回数写 +1；"
                  "落点偏移写夹紧；新键不得与既有字典重叠；仅未知角色数必须等于本批声明"),
        "note": "本区不重算原生语义，只独立核对产物与原始表的一致性",
    }
    ok_all &= not p_bad

    report["overall_ok"] = bool(ok_all)
    out = BASE / "validation" / "crosscheck_raw.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "mismatches"}
                      for k, v in report["checks"].items()}, ensure_ascii=False, indent=2))
    print("overall_ok =", report["overall_ok"])
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
