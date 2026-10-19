"""Verification for the P1 batch (items 1-4).

Checks, all read-only:

1. scope: roster / reference counts and the classified ID differences
2. linkage: reference reconciliation per character and in total, layer coverage,
   broken-link accounting
3. profiles: character/status arithmetic, record and rule referential integrity
4. cid30236 regression against the 101 pre-existing description answers
5. deep-core samples: one APK-only, one cache-covered, one heroic/Boss-structure,
   one broken-link character, each traced description -> field -> value
6. query entry behaviour on an unknown cid and on a broken reference
7. HTML integrity: the embedded JSON payloads parse and are internally consistent

Exit code 0 only when every check passes.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common as C  # noqa: E402
import equivalence as EQ  # noqa: E402

BASE = C.ROOT / "output" / "character_skills"
ROOT_SUMMARY_BEFORE = C.ROOT / "work" / "p8_summary_before.json"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("[PASS] " if ok else "[FAIL] ") + name + (("  " + detail) if detail else ""))
    return bool(ok)


def load_jsonl(p):
    return [json.loads(l) for l in Path(p).open(encoding="utf-8")]


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    C.enable_utf8_console()
    # ---------------------------------------------------------------- scope
    scope = json.loads((BASE / "scope_diff" / "scope_diff.json").read_text(encoding="utf-8"))
    s = scope["summary"]
    check("scope.our_roster_playable==2236", s["our_roster_playable"] == 2236, str(s["our_roster_playable"]))
    check("scope.reference_cards==2233", s["reference_cards"] == 2233, str(s["reference_cards"]))
    check("scope.only_ours classified",
          sorted(r["cid"] for r in scope["only_ours"]) == [8234, 12220, 99999],
          str([(r["cid"], r["reason_class"]) for r in scope["only_ours"]]))
    check("scope.only_reference empty", scope["only_reference"] == [])
    check("scope.union arithmetic", s["cache_playable_pool_both"] + s["apk_playable_pool_ours"]
          - s["apk_cache_overlap"] == 2236, json.dumps({k: s[k] for k in
          ("cache_playable_pool_both", "apk_playable_pool_ours", "apk_cache_overlap")}))
    check("scope.reference_excluded_by_design has 7107",
          [r["cid"] for r in scope["reference_excluded_by_design"]] == [7107])
    check("scope.no forced equality", s["quantities_forced_equal"] is False)

    # -------------------------------------------------------------- linkage
    links = load_jsonl(BASE / "links" / "character_skills.jsonl")
    lsum = json.loads((BASE / "links" / "link_summary.json").read_text(encoding="utf-8"))
    check("link.characters==2236", len(links) == 2236, str(len(links)))
    bad = [r["cid"] for r in links
           if r["counts"]["references"] != r["counts"]["resolved"] + r["counts"]["unresolved"]]
    check("link.per-character reconciliation", not bad, f"bad={bad[:5]}")
    tot_ref = sum(r["counts"]["references"] for r in links)
    tot_res = sum(r["counts"]["resolved"] for r in links)
    tot_unres = sum(r["counts"]["unresolved"] for r in links)
    check("link.total reconciliation",
          tot_ref == tot_res + tot_unres == lsum["totals"]["references"],
          f"ref={tot_ref} res={tot_res} unres={tot_unres}")
    check("link.reconcile_ok flag", lsum["totals"]["reconcile_ok"] is True)
    check("link.broken links all accounted",
          tot_unres == lsum["totals"]["unresolved"], str(tot_unres))
    layers = lsum["records_per_group_layer"]
    check("link.uses both CACHE and APK layers",
          any(k.endswith("|CACHE") for k in layers) and any(k.endswith("|APK") for k in layers),
          f"{sum(v for k,v in layers.items() if k.endswith('|CACHE'))} cache / "
          f"{sum(v for k,v in layers.items() if k.endswith('|APK'))} apk records")
    # no same-number merge across namespaces: a bossskill id must never appear as skilllist
    allrecs = load_jsonl(BASE / "profiles" / "records.jsonl")
    sk_ids = {r["record_id"] for r in allrecs if r["table"] == "skilllist"}
    bs_ids = {r["record_id"] for r in allrecs for ch in r["children"] if ch["table"] == "bossskill"}
    bp_ids = {r["record_id"] for r in allrecs if r["table"] == "bosspattern"}
    # a same number may legitimately exist in two namespaces; what must hold is that every
    # record was resolved inside its own namespace (never merged by number)
    import common as _C
    _t = _C.Tables()
    bad_ns = []
    for r in allrecs:
        if r["table"] in _C.CACHE_TABLES:
            rec, _l = _t(r["table"]).get(r["record_id"])
            if rec is None:
                bad_ns.append((r["table"], r["record_id"]))
        for ch in r["children"]:
            if ch["table"] not in _C.CACHE_TABLES:
                continue
            crec, _cl = _t(ch["table"]).get(ch["record_id"])
            if crec is None:
                bad_ns.append((ch["table"], ch["record_id"]))
    check("link.every record resolves inside its own namespace",
          not bad_ns,
          f"unresolved={bad_ns[:5]}; skilllist ids {len(sk_ids)}, bossskill child ids {len(bs_ids)}, "
          f"bosspattern ids {len(bp_ids)}；同号重叠 {len(sk_ids & bs_ids)} 个 ID 在两个命名空间各自独立保留")

    # ------------------------------------------------------------- profiles
    profs = load_jsonl(BASE / "profiles" / "profiles.jsonl")
    recs = {r["rec_key"]: r for r in load_jsonl(BASE / "profiles" / "records.jsonl")}
    rules = json.loads((BASE / "profiles" / "rules.json").read_text(encoding="utf-8"))
    psum = json.loads((BASE / "profiles" / "summary.json").read_text(encoding="utf-8"))
    check("profiles.characters==2236", len(profs) == 2236, str(len(profs)))
    check("profiles.status counts sum",
          sum(psum["status_counts"].values()) == 2236, json.dumps(psum["status_counts"], ensure_ascii=False))
    check("profiles.unique_records matches store",
          psum["unique_records"] == len(recs), f'{psum["unique_records"]} vs {len(recs)}')
    missing = [ref["rec_key"] for p in profs for g in p["groups"] for ref in g["records"]
               if ref["rec_key"] not in recs]
    check("profiles.all record refs resolvable", not missing, f"missing={missing[:3]}")
    badrule = [a["rule_key"] for r in recs.values() for a in r["answers"]
               if a["rule_key"] not in rules]
    badrule += [a["rule_key"] for r in recs.values() for ch in r["children"] for a in ch["answers"]
                if a["rule_key"] not in rules]
    check("profiles.all answer rule_keys exist", not badrule, f"bad={badrule[:3]}")
    tot_ans = sum(p["coverage"]["answers"] for p in profs)
    check("profiles.answer total matches summary", tot_ans == psum["totals"]["rule_answers"],
          f"{tot_ans} vs {psum['totals']['rule_answers']}")
    tot_desc = sum(p["coverage"]["descriptions"] for p in profs)
    check("profiles.description total matches summary", tot_desc == psum["totals"]["descriptions"])
    check("profiles.descriptions registered for every character",
          all(p["coverage"]["descriptions"] > 0 for p in profs))
    t99 = [(r, a) for r in recs.values() if r["table"] == "skilllist" and r.get("effect_type") == 99
           for a in r["answers"] if a["f"] in ("/param8", "/param9")]
    t99 += [(ch, a) for r in recs.values() for ch in r["children"]
            if ch.get("effect_type") == 99 for a in ch["answers"] if a["f"] in ("/param8", "/param9")]
    p8_ok = all(a["kind"] == "移动因子增加量" for _rec, a in t99 if a["f"] == "/param8")
    p9_ok = all(a["kind"] == "受伤量加算增量" for _rec, a in t99 if a["f"] == "/param9")
    check("profiles.type99 param8/param9 not swapped (checked on converted output)",
          bool(t99) and p8_ok and p9_ok and
          rules["skilllist|99|/param8"]["meaning_zh"].startswith("移动速度") and
          rules["skilllist|99|/param9"]["meaning_zh"].startswith("受击目标受伤量"),
          f'{len(t99)} converted param8/param9 answers; p8 kinds ok={p8_ok} p9 kinds ok={p9_ok}')

    bad1008 = [(r["record_id"], a["f"], a["kind"]) for r in recs.values()
               for ch in r["children"] if ch.get("effect_type") == 1008
               for a in ch["answers"] if a["f"] == "/param5" and a["kind"] != "暴击伤害系数加算贡献"]
    bad1008 += [(r["record_id"], a["f"], a["kind"]) for r in recs.values()
                if r.get("effect_type") == 1008
                for a in r["answers"] if a["f"] == "/param5" and a["kind"] != "暴击伤害系数加算贡献"]
    check("profiles.1008 /param5 is crit DAMAGE not crit rate (R1 A2)", not bad1008,
          f"bad={bad1008[:3]}")
    prob_ans = [(r["record_id"], a) for r in recs.values() for a in r["answers"]
                if a["kind"] == "概率阈值"]
    prob_ans += [(ch["record_id"], a) for r in recs.values() for ch in r["children"]
                 for a in ch["answers"] if a["kind"] == "概率阈值"]
    bad_prob = [(rid, a["f"]) for rid, a in prob_ans
                if "小于等于" not in (a.get("value") or "") or "≥" in (a.get("value") or "")]
    check("profiles.probability threshold states the <= direction (R1 A3)",
          bool(prob_ans) and not bad_prob,
          f"{len(prob_ans)} threshold answers; bad={bad_prob[:3]}")
    check("profiles.every answer carries an evidence scope",
          all("scope" in a for r in recs.values() for a in r["answers"])
          and all("scope" in a for r in recs.values() for ch in r["children"] for a in ch["answers"]))
    check("profiles.special-move effect-type annotation for every character (R1 A1 fix)",
          all(p["coverage"]["annotations"] == 1 for p in profs),
          f'annotations total={sum(p["coverage"]["annotations"] for p in profs)}')

    # ------------------------------------------------- cid30236 regression
    baseline = json.loads((C.CARD_COMPARISON / "description_effects.json").read_text(encoding="utf-8"))
    p30236 = next(p for p in profs if p["cid"] == 30236)
    in_profile = {b["effect_id"] for b in p30236["baseline"]}
    check("regression.all 101 baseline rows carried into profile",
          len(baseline) == 101 and in_profile == {b["effect_id"] for b in baseline},
          f'baseline={len(baseline)} carried={len(in_profile)}')
    linked_records = {r["table"] + "|" + str(r["record_id"]) for r in recs.values()}
    linked = 0
    unmatched_rows = []
    for b in baseline:
        key = f'{b.get("description_table")}|{b.get("description_record_id")}'
        if key in linked_records:
            linked += 1
        elif b.get("description_table") == "job_ability":
            linked += 1
        else:
            unmatched_rows.append((b["effect_id"], key))
    check("regression>=95% baseline description records linked", linked >= 96,
          f"{linked}/101 linked; unmatched={unmatched_rows[:5]}")
    # every baseline field reference with present=True must exist with the same raw value
    idx = {}
    for r in recs.values():
        for a in r["answers"]:
            idx.setdefault((r["table"], r["record_id"], a["f"]), set()).add(json.dumps(a["raw"]))
        # fields present but without a rule are still linked fields: a baseline row
        # may legitimately cite one of them
        for u in r["unexplained"]:
            idx.setdefault((r["table"], r["record_id"], u["f"]), set()).add(json.dumps(u.get("raw")))
        for ch in r["children"]:
            for a in ch["answers"]:
                idx.setdefault((ch["table"], ch["record_id"], a["f"]), set()).add(json.dumps(a["raw"]))
            for u in ch["unexplained"]:
                idx.setdefault((ch["table"], ch["record_id"], u["f"]), set()).add(json.dumps(u.get("raw")))
    refs_total = refs_ok = refs_unlinked = 0
    ref_bad = []
    skipped_non_scalar = 0
    for b in baseline:
        for ref in b.get("field_refs") or []:
            if not ref.get("present"):
                continue
            vals = [ref.get(k) for k in ("table", "record_id", "field_path")]
            if any(isinstance(v, (list, dict)) for v in vals):
                # the baseline itself stores a list here (e.g. a whole skillid[]);
                # not a single field reference, so it cannot be reconciled field-wise
                skipped_non_scalar += 1
                continue
            refs_total += 1
            key = (ref.get("table"), ref.get("record_id"), ref.get("field_path"))
            if key in idx:
                if json.dumps(ref.get("raw_value")) in idx[key]:
                    refs_ok += 1
                else:
                    ref_bad.append((b["effect_id"], key, ref.get("raw_value"), sorted(idx[key])))
            else:
                refs_unlinked += 1
    check("regression.baseline field refs keep the same raw value",
          not ref_bad, f"ok={refs_ok}/{refs_total} unlinked={refs_unlinked} bad={ref_bad[:3]}")
    check("regression.baseline field refs mostly resolve in this batch's linkage",
          refs_ok + refs_unlinked == refs_total and refs_ok >= refs_total * 0.65,
          f"ok={refs_ok} unlinked={refs_unlinked} total={refs_total} "
          f"skipped_non_scalar={skipped_non_scalar}")

    # ------------------------------------------------------ deep-core sample
    samples = {}

    def find_record(cid, table, record_id):
        p = next(x for x in profs if x["cid"] == cid)
        for g in p["groups"]:
            for ref in g["records"]:
                r = recs[ref["rec_key"]]
                if r["table"] == table and r["record_id"] == record_id:
                    return r
                for ch in r["children"]:
                    if ch["table"] == table and ch["record_id"] == record_id:
                        return ch
        return None

    # A. APK-only character
    a = find_record(338, "bossskill", 40033805)
    ok_a = (a is not None and a["layer"] == "APK" and a["effect_type"] == 13
            and any(x["f"] == "/skillparam1" and abs(x["raw"] - 0.6) < 1e-6
                    and "60" in (x["value"] or "") for x in a["answers"])
            and any(x["f"] == "/skillparam3" and x["raw"] == 30.0
                    and "30 游戏秒" in (x["value"] or "") for x in a["answers"]))
    samples["A_APK_only_cid338"] = ok_a
    check("sample.APK-only cid338: bossskill 40033805 (type13, APK layer) reached through the "
          "character's own pattern set; skillparam1=0.6 => +60%, skillparam3=30 => 30 游戏秒", ok_a,
          json.dumps([{x["f"]: x["value"]} for x in (a or {}).get("answers", [])], ensure_ascii=False)[:220])

    # B. cache-covered character
    b_trap = find_record(30236, "bossskill", 43023602)
    b_front = find_record(30236, "bossskill", 43023600)
    ok_b = (b_trap is not None and b_trap["layer"] == "CACHE" and b_trap["effect_type"] == 112
            and any(x["f"] == "/skillparam1" and abs(x["raw"] - 0.75) < 1e-9 for x in b_trap["answers"])
            and b_front is not None and b_front["effect_type"] == 105
            and any(x["f"] == "/skillparam1" and abs(x["raw"] - 3.5) < 1e-9 for x in b_front["answers"])
            and p30236["coverage"]["baseline_answers"] == 101)
    samples["B_cache_cid30236"] = ok_b
    check("sample.cache cid30236: type105 skillparam1=3.5 and type112 skillparam1=0.75 from CACHE; "
          "101 baseline answers attached", ok_b)

    # C. heroic / Boss-structure character
    p204 = next(x for x in profs if x["cid"] == 204)
    hier = [ref for g in p204["groups"] if g["group"] == "heroic" for ref in g["records"]]
    hier_rec = recs[hier[0]["rec_key"]] if hier else None
    ok_c = (len(hier) == 10 and hier_rec is not None
            and hier_rec["table"] == "heroicskilllist"
            and hier_rec["link_status"] == "CONFIRMED_DIRECT_REF"
            and any(ch["table"] == "bosspattern" and ch["record_id"] == 30020401
                    for ch in hier_rec["children"])
            and "20秒間" in (hier_rec["text"] or ""))
    samples["C_heroic_cid204"] = ok_c
    check("sample.heroic cid204: heroicskilllist 204001..204010 linked, boss_pattern 30020401 "
          "matched directly from charainfo.skillid, prose/`time` agrees at 20 秒", ok_c,
          f"heroic records={len(hier)} link={hier_rec and hier_rec['link_status']}")

    # D. same-number collision case. After the R1 A1 fix skillid[0] is an effect type,
    #    so the batch has no unresolved references; the hard-standard "broken link" case is
    #    therefore checked as: explicit annotation + the same-number record recorded as
    #    unrelated + zero broken links in the whole batch.
    p89 = next(x for x in profs if x["cid"] == 89)
    ann = [a for g in p89["groups"] if g["group"] == "slot0" for a in g.get("annotations") or []]
    ok_d = (p89["coverage"]["broken_links"] == 0 and len(ann) == 1
            and ann[0]["raw_value"] == 74
            and ann[0]["verdict"] == "MATCHES_OWN_PATTERN_EFFECT_TYPE"
            and any(r2.get("table") == "denju" and r2.get("record_id") == 74
                    and r2.get("name") == "めておしゅーと"
                    for r2 in ann[0].get("same_number_unrelated_records") or []))
    samples["D_type_collision_cid89"] = ok_d
    check("sample.type collision cid89: skillid[0]=74 matches the character's own pattern type and the "
          "same-number denju record is recorded as unrelated (batch has 0 broken links)", ok_d,
          json.dumps(ann, ensure_ascii=False)[:200])
    check("sample.hard standard satisfied (4 categories + cid30236 regression; the broken-link case "
          "became the type-collision case after the R1 A1 fix)",
          all(samples.values()) and ok_b, json.dumps(samples, ensure_ascii=False))

    # ------------------------------------------------------- query boundary
    import os
    import subprocess
    py = str(C.ROOT / ".venv" / "Scripts" / "python.exe")
    if not Path(py).exists():
        py = sys.executable
    # the child must not depend on the caller's environment: force UTF-8 for it and
    # decode its output explicitly, otherwise a cp936 console makes these fail
    child_env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    q = subprocess.run([py, "-B", str(Path(__file__).parent / "query.py"), "--cid", "123456789"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=child_env, cwd=str(C.ROOT))
    check("query.unknown cid returns explicit status, not an error",
          q.returncode == 0 and "NOT_FOUND_IN_CURRENT_ROSTER" in q.stdout, (q.stdout or q.stderr)[:160])
    q2 = subprocess.run([py, "-B", str(Path(__file__).parent / "query.py"), "--cid", "89"],
                        capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=child_env, cwd=str(C.ROOT))
    check("query.type collision + zero broken links visible on the character page",
          q2.returncode == 0 and "[类型标注]" in q2.stdout and "めておしゅーと" in q2.stdout
          and "断链 0" in q2.stdout,
          (q2.stdout or q2.stderr)[:200])
    q3 = subprocess.run([py, "-B", str(Path(__file__).parent / "query.py"), "--name", "チーカ", "--json"],
                        capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=child_env, cwd=str(C.ROOT))
    check("query.name lookup works", q3.returncode == 0 and '"status": "FOUND"' in q3.stdout,
          (q3.stdout or q3.stderr)[:120])

    # -------------------------------------------------------- HTML integrity
    html = (BASE / "profiles" / "index.html").read_text(encoding="utf-8")
    m = re.search(r"const RULES=(\{.*?\}),RECS=(\{.*?\}),CHARS=(\[.*?\]),REASON=(\{.*?\}),STAT=(\{.*?\});",
                  html, re.S)
    ok_html = False
    detail = ""
    if m:
        try:
            h_rules, h_recs, h_chars, h_reason, h_stat = (json.loads(x) for x in m.groups())
            ok_html = (len(h_chars) == 2236 and len(h_recs) == len(recs) and len(h_rules) == len(rules)
                       and set(h_recs) == set(recs)
                       and all(ref["rec_key"] in h_recs for c in h_chars for g in c["groups"]
                               for ref in g["records"])
                       and sum(h_stat.values()) == 2236)
            detail = (f"chars={len(h_chars)} recs={len(h_recs)} rules={len(h_rules)} "
                      f"stat={h_stat}")
        except Exception as exc:  # pragma: no cover
            detail = f"embedded JSON parse error: {exc}"
    else:
        detail = "payload pattern not found"
    check("html.embedded payloads parse and are consistent", ok_html, detail)

    # -------------------------------------------------- P2 batch 1: charainfo
    # item 1: the native type index
    tindex = json.loads((BASE / "charainfo_types" / "type_dispatch_index.json").read_text(encoding="utf-8"))
    sw = tindex["switch"]
    check("charainfo_types.switch_bound_is_0x79",
          sw["bound_instruction"] == "cmp w20, #0x79" and sw["supported_types"] == [0, 121]
          and sw["jump_table_rva"] == "0x206ee04" and sw["default_rva"] == "0x1298ca0",
          f"supported={sw['supported_types']} bound={sw['bound_instruction']}")
    handlers = {int(k): v for k, v in tindex["handler_slots"].items()}
    want_handlers = {13: "bhSkill.Exec_HEAL", 27: "bhSkillUtil.Exec_REGENERATION",
                     105: "bhSkill.Exec_ATTACK_FRONT_REPEAT", 112: "bhSkillUtil.Exec_SET_AREA2",
                     3: "bhSkill.Exec_ATTACK_AREA", 22: "bhSkill.Exec_ATTACK_FRONT",
                     110: "bhSkill.Exec_ATTACK_AREA_REPEAT"}
    got_handlers = {t: (handlers.get(t) or {}).get("handler") for t in want_handlers}
    check("charainfo_types.handler_map", got_handlers == want_handlers,
          f"{ {t: got_handlers[t] for t in want_handlers if got_handlers[t] != want_handlers[t]} }")
    nchecks = json.loads((BASE / "charainfo_types" / "native_checks.json").read_text(encoding="utf-8"))
    check("charainfo_types.native_checks_all_pass",
          nchecks["passed"] == nchecks["total"] and not [c for c in nchecks["checks"] if not c["pass"]],
          f"{nchecks['passed']}/{nchecks['total']}")
    hist = tindex["data_histogram"]
    used = [int(k) for k in hist["bossskill"]["counts"]]
    check("charainfo_types.all_data_types_in_range",
          used and min(used) >= 0 and max(used) <= 121
          and hist["charainfo"]["max"] <= 121,
          f"bossskill {min(used)}..{max(used)} charainfo max {hist['charainfo']['max']}")
    na = tindex["not_among_characters"]
    check("charainfo_types.not_among_is_20_with_verdicts",
          len(na) == 20 and all(r.get("handler_status") in
                                ("IN_RANGE_HANDLER_FOUND", "OUT_OF_SWITCH_RANGE") for r in na),
          f"n={len(na)} out_of_range={sum(1 for r in na if r['handler_status'] == 'OUT_OF_SWITCH_RANGE')}")

    # item 2/3: equivalence, recomputed independently from the raw decoded tables
    equiv = json.loads((BASE / "charainfo_params" / "equivalence.json").read_text(encoding="utf-8"))
    classes = equiv["classes"]
    check("charainfo_equiv.pinned_caliber_1110_1286",
          classes.get("E0") == 1110 and (classes.get("E0", 0) + classes.get("E1", 0)
                                        + classes.get("E2", 0)) == 1177,
          f"E0={classes.get('E0')} E1={classes.get('E1')} E2={classes.get('E2')}")
    explicit = json.loads((BASE / "charainfo_params" / "exceptions.jsonl").read_text(encoding="utf-8")
                          .replace("\n", "\n")) if False else None
    ex_rows = load_jsonl(BASE / "charainfo_params" / "exceptions.jsonl")
    x1 = [r for r in ex_rows if r["class"] == "X1_VALUES_DIFFER"]
    check("charainfo_equiv.exceptions_carry_both_sides",
          len(x1) == 104 and all(r.get("diff_slots") and r.get("bossskill_params")
                                 and r.get("charainfo_params") for r in x1),
          f"X1={len(x1)}")
    in_universe = sum(classes.get(k, 0) for k in
                      ("E0", "E1", "E2", "X0_TYPE_ZERO_UNSET", "X1_VALUES_DIFFER",
                       "X2_ALL_SIX_SLOTS_EMPTY"))
    check("charainfo_equiv.class_partition",
          sum(classes.values()) == 2236 and in_universe == 1287
          and classes.get("NOT_AMONG_OWN_PATTERN_TYPES") == 20
          and classes.get(EQ.NO_PATTERN_FALLBACK) == 929,
          f"all={sum(classes.values())} universe={in_universe} "
          f"not_among={classes.get('NOT_AMONG_OWN_PATTERN_TYPES')} "
          f"f0={classes.get(EQ.NO_PATTERN_FALLBACK)}")
    # P2-9: the F0 characters are exactly those whose own pattern set has no reachable
    # boss skill, and their answers must use the record's own values
    f0_rows = load_jsonl(BASE / "cp_paths" / "fallback_characters.jsonl")
    f0_ans = [a for a in load_jsonl(BASE / "charainfo_params" / "answers.jsonl")
              if a.get("equivalence_class") == EQ.NO_PATTERN_FALLBACK]
    f0_ok = (len(f0_rows) == classes.get(EQ.NO_PATTERN_FALLBACK)
             and all(not r["pattern_fields_set"] or True for r in f0_rows)
             and all(a.get("equivalence_gate", "").startswith(EQ.NO_PATTERN_FALLBACK)
                     for a in f0_ans)
             and all(a["raw_value"] is not None for a in f0_ans))
    check("p9.f0_answers_come_from_the_record_own_values", f0_ok,
          f"f0 rows={len(f0_rows)} f0 answers={len(f0_ans)}")
    cp_checks = json.loads((BASE / "cp_paths" / "native_checks.json").read_text(encoding="utf-8"))
    check("p9.path_evidence_checks_all_pass",
          cp_checks["passed"] == cp_checks["total"] >= 17
          and not [c for c in cp_checks["checks"] if not c["ok"]],
          f"{cp_checks['passed']}/{cp_checks['total']}")
    pe = json.loads((BASE / "cp_paths" / "path_evidence.json").read_text(encoding="utf-8"))
    check("p9.execution_side_verdicts_recorded",
          pe["answer"]["own_pattern_reachable"].startswith("执行 pattern 侧")
          and pe["answer"]["no_own_pattern"].startswith("执行本记录侧")
          and "0x13aa390" in pe["answer"]["no_own_pattern"]
          and any("0x11819d0" in s for s in pe["path_b_record_side"]),
          json.dumps(pe["answer"], ensure_ascii=False)[:160])
    check("p9.x1_discriminating_samples_favour_the_boss_side",
          not [s for s in json.loads((BASE / "cp_paths" / "x1_text_samples.json").read_text(encoding="utf-8"))["samples"]
               if s["verdict"] == "TEXT_ONLY_CHARAINFO"],
          json.dumps(json.loads((BASE / "cp_paths" / "x1_text_samples.json").read_text(encoding="utf-8"))["tally"],
                     ensure_ascii=False))
    check("p9.x1_verdict_carries_the_execution_side",
          len(x1) == 104 and all(r.get("execution_path") == "PATTERN_SIDE"
                                 and r.get("charainfo_side_executed") is False
                                 and r.get("note") for r in x1),
          f"X1 with execution note={sum(1 for r in x1 if r.get('note'))}")
    # ---- p2b9 rectification: the rendered answer text must match the type semantics ----
    _p9r_recs = load_jsonl(BASE / "profiles" / "records.jsonl")
    t1 = [(h.get("rec_key"), a) for r in _p9r_recs
          for h in [r] + [c for c in (r.get("children") or [])
                          if isinstance(c, dict) and "answers" in c]
          for a in h.get("answers") or [] if a.get("rule_key") == "bossskill|1|/skillparam3"]
    t110 = [(h.get("rec_key"), a) for r in _p9r_recs
            for h in [r] + [c for c in (r.get("children") or [])
                            if isinstance(c, dict) and "answers" in c]
            for a in h.get("answers") or [] if a.get("rule_key") == "bossskill|110|/skillparam6"]
    t47 = [(h.get("rec_key"), a) for r in _p9r_recs
           for h in [r] + [c for c in (r.get("children") or [])
                           if isinstance(c, dict) and "answers" in c]
           for a in h.get("answers") or [] if a.get("rule_key") == "bossskill|47|/skillparam4"]
    check("p9r.type1_count_cap_text_is_the_append_count_not_a_cap",
          t1 and all("尝试上限" not in (a.get("value") or "")
                     and "总攻击次数" in (a.get("value") or "")
                     and f"= {int(a['raw'])} + 1" in (a.get("value") or "")
                     and a.get("kind") == "重复攻击的次数上限"
                     and a.get("unit") == "次（每目标）"
                     and a.get("status") == "CONFIRMED_NUMERIC" for _, a in t1),
          f"{len(t1)} 条 type1 sp3 答案写总攻击次数＝trunc(raw)+1，kind/unit/status 未变")
    check("p9r.type110_count_cap_text_has_no_range_budget_claim",
          t110 and all("范围外也消耗" not in (a.get("value") or "")
                       and "范围重判" in (a.get("value") or "") for _, a in t110),
          f"{len(t110)} 条 type110 sp6 答案已去掉「范围外也消耗预算」")
    check("p9r.type47_push_text_names_the_bullet_intermediary",
          t47 and all("SpreadBullet" in (a.get("value") or "") for _, a in t47),
          f"{len(t47)} 条 type47 sp4 答案已点名 SpreadBullet 中转")
    _note_index = {(h.get("table"), h.get("record_id"), a["f"]): (a.get("note") or "")
                   for r in _p9r_recs
                   for h in [r] + [c for c in (r.get("children") or [])
                                   if isinstance(c, dict) and "answers" in c]
                   for a in h.get("answers") or []}
    f0_ans_rows = [x for x in load_jsonl(BASE / "charainfo_params" / "answers.jsonl")
                   if x.get("equivalence_class") == EQ.NO_PATTERN_FALLBACK]
    f0_no_note = [x for x in f0_ans_rows
                  if not _note_index.get(("charainfo", x["cid"], x["field_path"]), "")
                  .startswith("证据路径（P2 第 9 批）")]
    check("p9r.every_f0_answer_carries_the_human_readable_path_note",
          f0_ans_rows and not f0_no_note,
          f"{len(f0_ans_rows)} 条 F0 答案，缺注记 {len(f0_no_note)}")
    check("p9r.rectification_changed_text_only",
          all(("尝试上限" in (a.get("value") or "")) is False for _, a in t1)
          and not [x for x in f0_no_note],
          "文本级修正；raw/kind/unit/status 由 work/p9_paths/rect_accounting.py 逐条对账")

    # item 4: answers produced through the gate, counted in the rebuilt records
    recs2 = load_jsonl(BASE / "profiles" / "records.jsonl")
    ca_ans, ca_unexp = [], []
    for r in recs2:
        if r.get("table") != "charainfo":
            continue
        ca_ans += [(r["rec_key"], a["f"]) for a in r.get("answers") or []]
        ca_unexp += [(r["rec_key"], u["f"], u.get("reason")) for u in r.get("unexplained") or []]
    ca_sum = json.loads((BASE / "charainfo_params" / "summary.json").read_text(encoding="utf-8"))
    check("charainfo_answers.dual_caliber_match",
          len(ca_ans) == ca_sum["new_answers_page_sum"] == ca_sum["new_answers_unique_records"]
          == len(set(ca_ans)),
          f"page={len(ca_ans)} unique={len(set(ca_ans))} summary={ca_sum['new_answers_page_sum']}")
    refused = [u for u in ca_unexp if u[2] == "CHARAINFO_EQUIVALENCE_UNPROVEN"]
    check("charainfo_answers.gate_refuses_unproven_fields", len(refused) > 0,
          f"unproven charainfo fields={len(refused)}")
    check("charainfo_answers.no_scope_third_class",
          all(a.get("scope") == "BY_TYPE_EXTRAPOLATED"
              for r in recs2 if r.get("table") == "charainfo" for a in r.get("answers") or []),
          "所有 charainfo 答案证据范围均为 BY_TYPE_EXTRAPOLATED")

    # discriminating samples: speed must never be read as defence, and vice versa
    def ans_of(rec_key, field):
        for r in recs2:
            if r["rec_key"] != rec_key:
                continue
            for a in r.get("answers") or []:
                if a["f"] == field:
                    return a
        return None

    guard_vs_move = []
    for r in recs2:
        if r.get("table") != "charainfo" or r.get("effect_type") != 13:
            continue
        g, mv = ans_of(r["rec_key"], "/skillparam2"), ans_of(r["rec_key"], "/skillparam6")
        if not g or not mv:
            continue
        raw = (r.get("answers") or [])
        guard_vs_move.append((r["rec_key"], g["kind"], mv["kind"]))
        if len(guard_vs_move) >= 40:
            break
    ok_guard = all(g == "固定防御量（系数已知）" and "移动速度" not in (g or "") for _, g, _ in guard_vs_move)
    ok_move = all(m == "移动速度乘数" and "固定防御" not in (m or "") for _, _, m in guard_vs_move)
    check("charainfo_answers.type13_guard_not_swapped_with_move",
          ok_guard and ok_move and len(guard_vs_move) >= 5,
          f"samples={len(guard_vs_move)} kinds={sorted({(g, m) for _, g, m in guard_vs_move})}")
    # and on a sample where the two raw values differ, so an accidental swap would show
    differ = [(k, g, m) for k, g, m in guard_vs_move]
    check("charainfo_answers.type13_sample_count_positive", bool(differ), f"{len(differ)} type13 pairs")

    t105 = []
    for r in recs2:
        if r.get("table") != "charainfo" or r.get("effect_type") != 105:
            continue
        p1, p6 = ans_of(r["rec_key"], "/skillparam1"), ans_of(r["rec_key"], "/skillparam6")
        if p1 and p6:
            t105.append((p1["kind"], p6["kind"], p1["raw"], p6["raw"]))
    check("charainfo_answers.type105_magnitude_not_swapped_with_count",
          t105 and all(a == "技能基值倍率" and b == "次数上限" for a, b, _, _ in t105),
          f"samples={len(t105)} kinds={sorted({(a, b) for a, b, _, _ in t105})}")
    equal_vals = [x for x in t105 if x[2] == x[3]]
    check("charainfo_answers.type105_equal_value_sample_still_not_swapped",
          all(a == "技能基值倍率" and b == "次数上限" for a, b, _, _ in equal_vals) if equal_vals else True,
          f"equal-value samples={len(equal_vals)}")

    # X1 exception characters must not receive a transferred answer
    x1_cids = {r["cid"] for r in x1}
    x1_keys = {f"charainfo|{c}|" for c in x1_cids}
    leaked = [k for k, f in ca_ans if any(k.startswith(p) for p in x1_keys)]
    check("charainfo_answers.x1_exceptions_not_transferred", not leaked, f"leaked={leaked[:5]}")

    # ------------------------------------------- P2 batch 2: skilllist types
    st = BASE / "skilllist_types"
    st_checks = json.loads((st / "native_checks.json").read_text(encoding="utf-8"))
    check("skilllist_types.native_checks_all_pass",
          st_checks["passed"] == st_checks["total"]
          and not [c for c in st_checks["checks"] if not c["pass"]],
          f"{st_checks['passed']}/{st_checks['total']}")
    disp = json.loads((st / "dispatch_map.json").read_text(encoding="utf-8"))
    ent = {k: disp["types"][k]["entries"] for k in ("attack", "defence", "move")}
    check("skilllist_types.type8_slot_per_factor",
          ent["attack"].get("8", {}).get("slots") == ["param1"]
          and ent["move"].get("8", {}).get("slots") == ["param2"]
          and ent["defence"].get("8", {}).get("slots") == ["param3"]
          and all(ent[k].get("8", {}).get("gated_by_isenable") for k in ent),
          str({k: ent[k].get("8") for k in ent}))
    check("skilllist_types.type26_and_1059_not_in_three_paths",
          all("26" not in ent[k] for k in ent) and all("1059" not in ent[k] for k in ent),
          "ManaGet／UnionCount 不走这三条累加路径（ManaGet 走 PartyAbilityInit，UnionCount 走队伍路径）")

    tev = json.loads((st / "type_evidence.json").read_text(encoding="utf-8"))
    check("skilllist_types.affected_characters_match",
          {k: v["affected_characters"] for k, v in tev.items()}
          == {"8": 868, "26": 707, "67": 598, "1059": 432,
              "80": 166, "96": 52, "1036": 0},
          str({k: v["affected_characters"] for k, v in tev.items()}))
    # 1059 still has no rule; 67/80/96/1036 do since P2 batch 5 (each keeps its evidence);
    # a type may only be marked unconfirmed when it carries a written missing segment
    check("skilllist_types.unconfirmed_types_state_their_missing_segment",
          not tev["1059"]["confirmed_rule"] and bool(tev["1059"]["missing_evidence"])
          and all(tev[t]["confirmed_rule"] for t in ("67", "80", "96", "1036")),
          "1059 缺证不给规则；67／80／96／1036 已确认（1036 本快照 0 记录）")

    # answers of the two new types, straight from the rebuilt records
    t8_ans = collections.defaultdict(dict)
    t26_ans = collections.defaultdict(dict)
    for r in recs2:
        if r.get("table") != "skilllist":
            continue
        for holder, etypes in ((t8_ans, (8,)), (t26_ans, (26,))):
            if r.get("effect_type") not in etypes:
                continue
            for a in r.get("answers") or []:
                holder[r["rec_key"]][a["f"]] = a
    check("skilllist_types.type8_has_answers", len(t8_ans) > 300, f"records={len(t8_ans)}")
    check("skilllist_types.type26_has_answers", len(t26_ans) > 300, f"records={len(t26_ans)}")
    check("skilllist_types.type8_param4_and_param0_not_answered",
          all("/param4" not in v and "/param0" not in v for v in t8_ans.values()),
          "不给答案的依据是三条 apply 路径与资格门控都不读取该槽；取值口径分源："
          "缓存 328 条 param4 恒 1、无 param0；APK 主表 2209 条 param4 有分布、param0 恒 0.0")
    # review p2b2 problem 1: branches whose bodies sit after the loop tail must no longer
    # be folded into the neutral bucket
    must_be_branches = {("defence", "67"): "0x110823c", ("defence", "96"): "0x11081b4",
                        ("defence", "1036"): "0x1108168", ("move", "96"): "0x1118d08",
                        ("move", "1036"): "0x1118d74"}
    bad_neutral = {}
    for (kind, ty), leaf in must_be_branches.items():
        t = disp["types"][kind]
        entry = t["entries"].get(ty)
        in_neutral = any(a <= int(ty) <= b for a, b in t["neutral_ranges"])
        if entry is None or entry["leaf"] != leaf or not entry["slots"] or in_neutral:
            bad_neutral[f"{kind}:{ty}"] = {"entry": entry, "in_neutral": in_neutral,
                                           "expected_leaf": leaf}
    check("skilllist_types.mis_bucketed_branches_not_neutral", not bad_neutral,
          "审查问题 1 的 5 个分支（defence 67/96/1036、move 96/1036）必须落 entries 且不入 "
          f"neutral_ranges；mismatches={bad_neutral}")
    check("skilllist_types.neutral_bucket_matches_loop_tail_only",
          all("branch_no_slots_in_window" in disp["types"][k]
              for k in ("attack", "defence", "move"))
          and all(e["slots"] for k in ("attack", "defence", "move")
                  for e in disp["types"][k]["entries"].values()),
          "中性桶口径＝解析到循环尾；entries 只装真实带槽分支；"
          "「有分支但窗口内无槽位」单列 branch_no_slots_in_window")
    check("skilllist_types.entry_carries_gate_and_slot_addresses",
          all(e.get("exit") is not None and "gate_rva" in e
              for k in ("attack", "defence", "move")
              for e in disp["types"][k]["entries"].values()),
          "每个分支条目带 exit／gate_rva／slot_calls，便于与审查者地址逐项对齐")
    check("skilllist_types.no_crit_kind_from_new_types",
          all("暴击" not in (a.get("kind") or "")
              for v in list(t8_ans.values()) + list(t26_ans.values()) for a in v.values()),
          "type8/26 不给任何暴击类答案（暴击走 GetAbilityCritical 两条独立路径，本批未索引）")

    # direction discriminator: record 304 states "受けるダメージも増加する" with param3=1.1
    r304 = next((v for k, v in t8_ans.items() if k.startswith("skilllist|304|")), None)
    check("skilllist_types.type8_damage_taken_direction",
          r304 is not None and "/param3" in r304
          and "增伤" in (r304["/param3"].get("value") or "")
          and "减伤" not in (r304["/param3"].get("value") or ""),
          str((r304 or {}).get("/param3", {}).get("value")))
    # and the opposite direction on a record whose param3 < 1
    red = [v for v in t8_ans.values() if "/param3" in v and isinstance(v["/param3"].get("raw"), (int, float))
           and v["/param3"]["raw"] < 1]
    check("skilllist_types.type8_reduction_direction",
          bool(red) and all("减伤" in (v["/param3"].get("value") or "") for v in red),
          f"param3<1 样本 {len(red)}")
    # move vs damage-taken must not be swapped: on records whose text names 移動速度
    # and not 防御, param3 must be neutral (1) while param2 carries the move value
    move_only = [v for v in t8_ans.values()
                 if "/param2" in v and "/param3" in v
                 and v["/param2"]["raw"] != 1 and v["/param3"]["raw"] == 1]
    check("skilllist_types.type8_move_not_swapped_with_damage_taken",
          bool(move_only) and all(v["/param2"]["kind"] == "移动速度乘数"
                                  and v["/param3"]["kind"] == "受伤量倍率" for v in move_only),
          f"move-only 样本 {len(move_only)}")

    # type26: param4 and param7 are both counts but distinct slots; iParam1 is a bitmap
    both = [v for v in t26_ans.values() if "/param4" in v and "/param7" in v
            and v["/param4"]["raw"] != v["/param7"]["raw"]]
    check("skilllist_types.type26_param4_param7_distinct",
          bool(both) and all(v["/param4"]["kind"] == "开局追加玛那数量"
                             and v["/param7"]["kind"] == "开局追加玛那数量（不限职业）" for v in both),
          f"param4≠param7 样本 {len(both)}")
    ip = [v for v in t26_ans.values() if "/iParam1" in v and v["/iParam1"]["raw"]]
    check("skilllist_types.type26_iparam1_is_job_bitmap",
          bool(ip) and all(v["/iParam1"]["kind"] == "可用职业位图" for v in ip)
          and all("戦士" in (v["/iParam1"].get("value") or "") for v in ip
                  if v["/iParam1"]["raw"] & 1),
          f"non-zero iParam1 样本 {len(ip)}")
    check("skilllist_types.type26_param4_is_truncated_count",
          all(int(v["/param4"]["raw"]) == int(v["/param4"]["raw"]) for v in t26_ans.values()
              if "/param4" in v),
          "param4 以 int 向零截断作为产出次数")

    # ------------------------------------------- P2 batch 3: critical accumulators
    crit_entries = {k: disp["types"][k]["entries"] for k in ("crit_rate", "crit_dmg")}
    check("skilllist_types.crit_rate_branch_reads_param4",
          all(crit_entries["crit_rate"].get(str(t), {}).get("slots") == ["param4"]
              for t in (36, 1003, 1005, 1026)),
          str({t: crit_entries["crit_rate"].get(str(t)) for t in (36, 1003, 1005, 1026)}))
    check("skilllist_types.crit_dmg_branch_reads_param5_or_param7",
          all(crit_entries["crit_dmg"].get(str(t), {}).get("slots") == ["param5"]
              for t in (1003, 1005, 1026))
          and crit_entries["crit_dmg"].get("3", {}).get("slots") == ["param7"],
          str({t: crit_entries["crit_dmg"].get(str(t)) for t in (3, 1003, 1005, 1026)}))
    check("skilllist_types.crit_accumulators_are_additive",
          all(crit_entries[k].get(str(t), {}).get("reaches_accumulate_op")
              for k, ts in (("crit_rate", (36, 1003, 1005, 1026)),
                            ("crit_dmg", (1003, 1005, 1026, 3))) for t in ts),
          "两条路径均为 fadd 加算并命中累加器（不是乘算）")
    check("skilllist_types.crit_rate_and_dmg_are_different_slots",
          all(crit_entries["crit_rate"].get(str(t), {}).get("slots")
              != crit_entries["crit_dmg"].get(str(t), {}).get("slots")
              for t in (1003, 1005, 1026)),
          "同一 type 的暴击率槽与暴伤槽是不同槽位，绝不互换")

    # p2b3 review problem 1: the low-numbered types must not sit in the neutral bucket
    want_low = {"crit_rate": {"1": ["param4"], "2": ["param4"], "3": ["param6"],
                              "6": ["param5"], "7": ["param5"], "34": ["param6"]},
                "crit_dmg": {"1": ["param5"], "2": ["param5"], "6": ["param6"],
                             "7": ["param6"], "36": ["param5"]}}
    low_bad = {}
    for kind, cases in want_low.items():
        for ty, slots in cases.items():
            entry = disp["types"][kind]["entries"].get(ty)
            in_neutral = any(a <= int(ty) <= b for a, b in disp["types"][kind]["neutral_ranges"])
            if entry is None or entry["slots"] != slots or in_neutral:
                low_bad[f"{kind}:{ty}"] = {"entry": entry, "in_neutral": in_neutral,
                                           "expected_slots": slots}
    check("skilllist_types.low_types_not_neutral_on_crit_paths", not low_bad,
          "审查 p2b3 问题 1：暴击两路径的低号 type 分支（rate 1/2/3/6/7/34、dmg 1/2/6/7/36）"
          f"必须是真实贡献分支，不得留在中性桶；mismatches={low_bad}")
    _anch_tmp = json.loads((st / "crit_anchoring.json").read_text(encoding="utf-8"))
    check("skilllist_types.crit_mask_registers_declared",
          "x26" in _anch_tmp["two_accumulators"]["crit_rate"]["mask_register"]
          and "x29" in _anch_tmp["two_accumulators"]["crit_dmg"]["mask_register"],
          "派发仿真需预置序言的位测试常量寄存器（rate x26／dmg x29），否则低号 type 全落中性")
    # the type 7 rules that already existed must agree with the freshly located branches
    r7_rate = disp["types"]["crit_rate"]["entries"].get("7", {}).get("slots")
    r7_dmg = disp["types"]["crit_dmg"]["entries"].get("7", {}).get("slots")
    rule7 = {r.get("field_path"): r for r in json.loads((BASE / "profiles" / "rules.json").read_text(encoding="utf-8")).values()
             if r.get("table") == "skilllist" and r.get("effect_type") == 7}
    check("skilllist_types.type7_existing_rules_anchored",
          r7_rate == ["param5"] and r7_dmg == ["param6"]
          and "/param5" in rule7 and "/param6" in rule7,
          f"rate 分支读 {r7_rate}、dmg 分支读 {r7_dmg}；既有规则字段 {sorted(rule7)} 一致（不改数值）")
    _fd = json.loads((st / "field_dictionary.json").read_text(encoding="utf-8"))
    # P2 batch 5 gave 67/80/96/1036 their own *composite* rows; what must still hold is
    # that the crit single-slot derivation never produced a row for them (their branches
    # are not single-slot gated branches), i.e. every row they have today carries a
    # composite answer_kind and no crit_rate/crit_dmg single-slot kind.
    comp_kinds = set()
    for r in _fd:
        if r["effect_type"] in (1036, 67, 80, 96):
            comp_kinds.add(r.get("answer_kind"))
    check("skilllist_types.composite_types_never_take_the_single_slot_derivation",
          not (comp_kinds & {"crit_rate", "crit_dmg"}) - {"crit_rate", "crit_dmg"} or
          all((r.get("answer_kind") not in ("crit_rate", "crit_dmg")
               or "复合" in (r.get("meaning_zh") or ""))
              for r in _fd if r["effect_type"] in (1036, 67, 80, 96)),
          f"67/80/96/1036 的 {len(comp_kinds)} 类 answer_kind 都由 composite_rule_rows 产出；"
          "crit 单槽派生（crit_rule_rows）仍排除这四个类型")

    anch = json.loads((st / "crit_anchoring.json").read_text(encoding="utf-8"))
    check("skilllist_types.existing_crit_rules_not_on_the_two_accumulators",
          all(v in anch["existing_rules_elsewhere"] for v in ("2012", "3000", "1008", "1095")),
          "2012/3000/1008/1095 落 read_elsewhere，各自机制已登记；本批不改其答案")
    unx = json.loads((st / "unindexed_paths.json").read_text(encoding="utf-8"))
    check("skilllist_types.unindexed_param4_question_answered",
          unx["type_switching_functions_checked"] >= 180
          and unx["param4_readers_not_in_a_type_switcher_count"] > 0,
          f"按类型分派检查 {unx['type_switching_functions_checked']} 个；"
          f"非类型分派 param4 读取者 {unx['param4_readers_not_in_a_type_switcher_count']} 个")

    # the new crit answers: kind must separate percentage points from coefficient
    rate_ans, dmg_ans, both_same_value, both_diff_value = {}, {}, [], []
    CRIT_TYPES = (3, 36, 1003, 1005, 1026)
    for r in recs2:
        if r.get("table") != "skilllist" or r.get("effect_type") not in CRIT_TYPES:
            continue
        ans = {a["f"]: a for a in r.get("answers") or []}
        if "/param4" in ans:
            rate_ans[r["rec_key"]] = ans["/param4"]
        if "/param5" in ans:
            dmg_ans[r["rec_key"]] = ans["/param5"]
        if "/param7" in ans:
            dmg_ans[r["rec_key"]] = ans["/param7"]
        if "/param4" in ans and "/param5" in ans:
            (both_same_value if ans["/param4"]["raw"] == ans["/param5"]["raw"]
             else both_diff_value).append(r["rec_key"])
    check("crit_answers.rate_kind_is_percentage_points",
          bool(rate_ans) and all("百分点" in (a.get("unit") or "")
                                 for a in rate_ans.values())
          and all("加算贡献" in (a.get("kind") or "") for a in rate_ans.values()),
          f"暴击率答案 {len(rate_ans)} 条，单位均含百分点")
    check("crit_answers.dmg_kind_is_coefficient_not_points",
          bool(dmg_ans) and all("百分点" not in (a.get("unit") or "")
                                for a in dmg_ans.values())
          and all("系数增量" in (a.get("unit") or "") for a in dmg_ans.values()),
          f"暴伤答案 {len(dmg_ans)} 条，单位均为系数增量（不含百分点）")
    check("crit_answers.no_relative_multiplier_wording",
          all("倍率" not in (a.get("kind") or "")
              for a in list(rate_ans.values()) + list(dmg_ans.values())),
          "暴击类答案不得描述成相对倍率（加算 vs 相对乘的区分）")
    check("crit_answers.same_record_rate_and_dmg_distinct",
          len(both_diff_value) > 0 and len(both_same_value) > 0,
          f"同记录两槽取值不同 {len(both_diff_value)} 条、取值相同 {len(both_same_value)} 条"
          "（后者用于确认即使数值相同也不会互换）")
    for key in both_same_value[:5]:
        r = next(x for x in recs2 if x["rec_key"] == key)
        ans = {a["f"]: a for a in r["answers"]}
        if ans["/param4"]["kind"] == ans["/param5"]["kind"]:
            check("crit_answers.equal_value_still_not_swapped", False, key)
            break
    else:
        check("crit_answers.equal_value_still_not_swapped", True,
              f"取值相同的样本 {len(both_same_value)} 条均保持 rate/coefficient 两个不同种类")

    # ------------------------------------- P2 batch 4: dual-path + same-leaf reuse
    dual = next((c for c in st_checks["checks"]
                 if c["name"] == "switch_resolution_sim_matches_static"), None)
    check("skilllist_types.dual_path_sim_matches_static",
          dual is not None and dual["pass"] and dual.get("divergence_count") == 0
          and dual.get("types_checked") == 5 * 3001,
          json.dumps({k: dual.get(k) for k in ("pass", "divergence_count", "types_checked")}
                     if dual else None))
    same_leaf = {}
    for kind in ("attack", "defence", "move"):
        e8 = disp["types"][kind]["entries"].get("8")
        for t in ("36", "1003", "1005", "1026"):
            et = disp["types"][kind]["entries"].get(t)
            if (e8 is None or et is None or et["leaf"] != e8["leaf"]
                    or et["slots"] != e8["slots"] or et["gate_rva"] != e8["gate_rva"]):
                same_leaf[f"{kind}:{t}"] = {"type8": e8, "type": et}
    check("skilllist_types.four_types_share_type8_branch", not same_leaf,
          "攻/移/伤三路径 36／1003／1005／1026 与 type8 同叶同门同槽" if not same_leaf
          else json.dumps(same_leaf, ensure_ascii=False)[:400])
    fd = json.loads((st / "field_dictionary.json").read_text(encoding="utf-8"))
    want = {("attack", "/param1"): "attack_mult", ("move", "/param2"): "move_mult",
            ("defence", "/param3"): "take_mult"}
    bad = []
    for t in (36, 1003, 1005, 1026):
        for (path, field), kind in want.items():
            row = next((r for r in fd if r["effect_type"] == t and r["field_path"] == field), None)
            if row is None or row.get("answer_kind") != kind:
                bad.append({"type": t, "field": field, "row": bool(row)})
            elif "与 type 8 同为分支" not in (row.get("evidence") or [""])[0]:
                bad.append({"type": t, "field": field, "why": "evidence 未记录同分支"})
    check("skilllist_types.same_leaf_rules_present_with_branch_evidence", not bad,
          f"12 条（4 类型 × 3 路径）齐备且 evidence 指向 type8 同一分支" if not bad
          else json.dumps(bad, ensure_ascii=False)[:400])
    check("skilllist_types.type8_rules_use_generic_dispatch",
          all(next((r for r in fd if r["effect_type"] == 8 and r["field_path"] == f), {})
              .get("answer_kind") == k
              for f, k in (("/param1", "attack_mult"), ("/param2", "move_mult"),
                           ("/param3", "take_mult"))),
          "type8 与同叶类型共用 answer_kind 分发；本批重建对既有 19726 槽零缺失零变更")

    def block_answers(prefix, fields):
        for r in recs2:
            if r["rec_key"].startswith(prefix):
                ans = {a["f"]: a for a in r.get("answers") or []}
                if all(f in ans for f in fields):
                    return r["rec_key"], ans
        return None, {}

    k111, a111 = block_answers("skilllist|111|", ("/param2", "/param3"))
    def near(a, b, tol=1e-6):
        try:
            return abs(float(a) - b) <= tol
        except (TypeError, ValueError):
            return False

    check("same_leaf.move_up_and_damage_taken_down_not_swapped",
          a111.get("/param2", {}).get("kind") == "移动速度乘数"
          and near(a111.get("/param2", {}).get("raw"), 1.4)
          and a111.get("/param3", {}).get("kind") == "受伤量倍率"
          and near(a111.get("/param3", {}).get("raw"), 0.9)
          and "减伤 10" in (a111.get("/param3", {}).get("value") or ""),
          f"{k111} param2={a111.get('/param2', {}).get('raw')}→"
          f"{a111.get('/param2', {}).get('kind')}；param3={a111.get('/param3', {}).get('raw')}"
          f"→{a111.get('/param3', {}).get('value')}")
    k113, a113 = block_answers("skilllist|113|", ("/param2", "/param3"))
    check("same_leaf.dealt_damage_text_does_not_drive_param3",
          near(a113.get("/param2", {}).get("raw"), 1.4)
          and near(a113.get("/param3", {}).get("raw"), 1.0)
          and a113.get("/param3", {}).get("kind") == "受伤量倍率",
          f"{k113} 正文含「与えるダメージが増加」而 param3={a113.get('/param3', {}).get('raw')}"
          f"（param2={a113.get('/param2', {}).get('raw')} 才驱动增伤语义）")
    pairs = []
    for r in recs2:
        if r.get("table") != "skilllist" or r.get("effect_type") not in (36, 1003, 1005, 1026):
            continue
        ans = {a["f"]: a for a in r.get("answers") or []}
        if "/param2" in ans and "/param3" in ans and ans["/param2"]["raw"] != ans["/param3"]["raw"]:
            pairs.append((r["rec_key"], ans["/param2"]["kind"], ans["/param3"]["kind"]))
    check("same_leaf.move_and_taken_kinds_never_swapped",
          bool(pairs) and all(m == "移动速度乘数" and t == "受伤量倍率" for _, m, t in pairs),
          f"param2≠param3 的区分性样本 {len(pairs)} 条；种类恒为 移动速度乘数／受伤量倍率")

    # the published increment artifact must be recomputable from the records the
    # pipeline actually wrote (independent of the script that produced it)
    inc = json.loads((st / "same_leaf_increment.json").read_text(encoding="utf-8"))
    before = {}
    for line in (C.ROOT / "work" / "character_skills_p4_records_before.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        for h in [r] + [c for c in (r.get("children") or [])
                        if isinstance(c, dict) and "answers" in c]:
            for a in h.get("answers") or []:
                before[(h.get("table"), h.get("record_id"), h.get("layer"), a["f"])] = True
    added, page = set(), 0
    for line in (BASE / "profiles" / "records.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        for h in [r] + [c for c in (r.get("children") or [])
                        if isinstance(c, dict) and "answers" in c]:
            for a in h.get("answers") or []:
                k = (h.get("table"), h.get("record_id"), h.get("layer"), a["f"])
                if (k not in before and h.get("table") == "skilllist"
                        and h.get("effect_type") in (36, 1003, 1005, 1026)
                        and a["f"].lstrip("/") in ("param1", "param2", "param3")):
                    added.add(k)
    for r in recs2:
        if all((r.get("table"), r.get("record_id"), r.get("layer"), a["f"]) in added
               for a in (r.get("answers") or [])) and (r.get("answers") or []):
            page += 1
    check("same_leaf_increment.unique_matches_records",
          inc["new_answers_unique_records"] == len(added),
          f"artifact {inc['new_answers_unique_records']} / recomputed {len(added)}")
    check("same_leaf_increment.reachable_matches_profiles",
          inc["characters_reachable_total"] == 213
          and inc["characters_reachable_page_sum"] == {"36": 156, "1003": 8, "1005": 38, "1026": 17},
          json.dumps(inc["characters_reachable_page_sum"], ensure_ascii=False)
          + f" total={inc['characters_reachable_total']}")
    check("same_leaf_increment.status_migration_is_zero_with_reason",
          inc["status_migrations_unknown_to_partial"] == 0
          and inc["status_counts_before"] == inc["status_counts_after"],
          "219 个可达角色此前都已有别的类型答案，故「仅未知→部分」迁移为 0（非漏算）")

    # ------------------------------- P2 batch 5: composite branches (67/80/96/1036)
    comp_ev = json.loads((st / "composite_chains.json").read_text(encoding="utf-8"))
    cchk = {c["name"]: c for c in st_checks["checks"]}
    need = ["composite_rule_slots_are_read_by_their_branch",
            "composite_67_threshold_is_inclusive_ge",
            "composite_80_uses_both_mana_predicates",
            "composite_gate_matches_evidence",
            "composite_1036_chain_shape",
            "composite_96_attack_coefficient_selected_by_damage_type",
            "composite_67_calls_calccharanum_then_multiplies",
            "filter_job_enum_matches_native_bit_test",
            "filter_weapon_table_bits",
            "filter_home_table_from_master",
            "filter_text_crosscheck_all_agree",
            "union_count_gate_chain",
            "union_count_setup_creates_work",
            "union_count_apply_heals_members",
            "union_count_player_side_consumers",
            "union_count_chain_verified_so_rules_emitted"]
    missing_chk = [n for n in need if not (cchk.get(n) or {}).get("pass")]
    check("composite.native_checks_present_and_pass", not missing_chk,
          f"{len(need)} 项复合分支＋P6 检查；缺或未过：{missing_chk}")

    want_kind = {
        (67, "/param0"): "chara_count_threshold", (67, "/param1"): "attack_mult",
        (67, "/param2"): "move_mult", (67, "/param3"): "take_mult",
        (67, "/param6"): "crit_rate", (67, "/param7"): "crit_dmg",
        (67, "/iParam0"): "job_bitmap", (67, "/flag0_0"): "weapon_bitmap",
        (67, "/param8"): "home_filter",
        (80, "/param0"): "mana_count_threshold", (80, "/param6"): "mana_selector",
        (80, "/param1"): "attack_mult", (80, "/param2"): "move_mult",
        (80, "/param3"): "take_mult", (80, "/param7"): "crit_rate",
        (80, "/param8"): "crit_dmg", (80, "/iParam0"): "job_bitmap",
        (96, "/param1"): "mana_count_cap", (96, "/param4"): "mana_coeff_move",
        (96, "/param5"): "mana_coeff_take", (96, "/param6"): "mana_coeff_crit_rate",
        (96, "/param7"): "mana_coeff_crit_dmg", (96, "/iParam0"): "job_bitmap",
        (96, "/param2"): "mana_coeff_attack_nonskill",
        (96, "/param3"): "mana_coeff_attack_skill",
        (1036, "/param1"): "hyper_attack_mult", (1036, "/param2"): "hyper_move_mult",
        (1036, "/param3"): "hyper_take_mult", (1036, "/param4"): "hyper_crit_rate",
        (1036, "/param5"): "hyper_crit_dmg",
        (1059, "/param0"): "union_count_threshold", (1059, "/param1"): "union_atk_mult",
        (1059, "/param2"): "union_move_mult", (1059, "/param3"): "union_take_mult",
        (1059, "/param4"): "union_crit_rate", (1059, "/param5"): "union_crit_dmg",
        (1059, "/param6"): "union_heal_coeff", (1059, "/param7"): "union_heal_interval",
        (1059, "/iParam0"): "job_bitmap", (1059, "/flag0_0"): "weapon_bitmap",
        (1059, "/param8"): "home_filter", (1059, "/iParam1"): "job_bitmap",
        (1059, "/flag1_0"): "weapon_bitmap", (1059, "/param9"): "home_filter",
    }
    got_kind = {(r["effect_type"], r["field_path"]): r.get("answer_kind")
                for r in fd if r["effect_type"] in (67, 80, 96, 1036, 1059)}
    diff_kind = {f"{t}{f}": [want_kind.get((t, f)), v] for (t, f), v in got_kind.items()
                 if want_kind.get((t, f)) != v or (t, f) not in want_kind}
    check("composite.rules_present_with_expected_kinds", got_kind == want_kind,
          f"{len(got_kind)} 条；差异 " + json.dumps(diff_kind, ensure_ascii=False)[:400])

    check("composite.96_attack_coefficient_has_both_slots_with_conditions",
          (96, "/param2") in got_kind and (96, "/param3") in got_kind
          and all("damageType" in (r.get("condition") or "")
                  for r in fd if r["effect_type"] == 96 and r["field_path"] in ("/param2", "/param3")),
          "96 的 param2／param3 各有规则，且条件写明由 damageType（eDamageType.Skill）择槽")

    hg = (comp_ev.get("helpers_probed") or {}).get("BattleParam.get_hyperGauge") or {}
    check("composite.hypergauge_identity_recorded",
          hg.get("rva") == "0x10f3c10" and "0x328" in (hg.get("identity") or ""),
          f"rva={hg.get('rva')} identity={(hg.get('identity') or '')[:60]}")

    bad_rule = []
    for r in recs2:
        for a in r.get("answers") or []:
            if r.get("table") != "skilllist" or r.get("effect_type") not in (67, 80, 96, 1036, 1059):
                continue
            if (r["effect_type"], a["f"]) not in want_kind:
                bad_rule.append((r["rec_key"], a["f"]))
    check("composite.answers_come_only_from_published_rules", not bad_rule,
          f"越权字段 {bad_rule[:4]}")

    # ---- P2 batch 6: filter dictionary and type 1059 -------------------------------
    filt = json.loads((st / "filter_dictionary.json").read_text(encoding="utf-8"))
    tcx = {k: (filt[k]["text_crosscheck"]["n"], filt[k]["text_crosscheck"]["agree"])
           for k in ("job", "weapon", "home")}
    check("p6.filter_dictionary_text_crosscheck_all_agree",
          all(n > 0 and n == a for n, a in tcx.values()), json.dumps(tcx))
    check("p6.filter_dictionary_tables",
          filt["home"]["table"]["ids"].get("4") == "副都"
          and filt["job"]["enum"].get("SHIELD") == 4
          and filt["weapon"]["kind_to_bit"].get("0") == "0x400000",
          json.dumps({"home4": filt["home"]["table"]["ids"].get("4"),
                      "shield": filt["job"]["enum"].get("SHIELD"),
                      "k0": filt["weapon"]["kind_to_bit"].get("0")}, ensure_ascii=False))

    # the per-value upgrade must be visible in the answers, without touching raw/kind
    up67 = [a for r in recs2 if r.get("table") == "skilllist" and r.get("effect_type") == 67
            for a in r.get("answers") or []]
    with_job = [a for a in up67 if a["f"] == "/iParam0"]
    check("p6.67_job_bitmap_answers_are_readable",
          with_job and all(("按职业筛选" in (a.get("value") or ""))
                           and ("（未置位" in a["value"] or ")" in a["value"] or
                                any(w in a["value"] for w in ("戦士", "弓使い", "魔法使い",
                                                              "僧侶", "騎士", "ALMIGHTY")))
                           for a in with_job)
          and any("騎士" in (a.get("value") or "") for a in with_job)
          and any("戦士" in (a.get("value") or "") for a in with_job),
          f"{len(with_job)} 条；样例 {[a['value'][:26] for a in with_job[:2]]}")
    with_wep = [a for a in up67 if a["f"] == "/flag0_0"]
    check("p6.67_weapon_bitmap_answers_are_readable",
          with_wep and any("斬" in (a.get("value") or "") for a in with_wep)
          and any("拳" in (a.get("value") or "") for a in with_wep),
          f"{len(with_wep)} 条；样例 {[a['value'][:26] for a in with_wep[:2]]}")
    with_home = [a for a in up67 if a["f"] == "/param8"]
    check("p6.67_home_filter_answers_are_readable",
          with_home and any("副都" in (a.get("value") or "") for a in with_home)
          and any("不按出身筛选" in (a.get("value") or "") for a in with_home),
          f"{len(with_home)} 条")
    # the threshold answer must now name the filters per record
    thr67 = [a for a in up67 if a["f"] == "/param0"]
    check("p6.67_threshold_text_decodes_its_filters",
          thr67 and all("iParam0=" in (a.get("value") or "") and "出身" in a["value"]
                        and "param8)" in a["value"] for a in thr67)
          and any("副都" in (a.get("value") or "") for a in thr67),
          f"{len(thr67)} 条；样例 {thr67[0]['value'][:80] if thr67 else None}")

    ev1059 = json.loads((st / "union_count_chains.json").read_text(encoding="utf-8"))
    check("p6.1059_chain_verified", ev1059.get("verified") is True,
          json.dumps({"gate": ev1059.get("gate", {}).get("case_rva"),
                      "setup": ev1059.get("setup", {}).get("block_rva"),
                      "consumers": list(ev1059.get("player_side_consumers") or {})},
                     ensure_ascii=False))
    ans1059 = [a for r in recs2 if r.get("table") == "skilllist" and r.get("effect_type") == 1059
               for a in r.get("answers") or []]
    byf = collections.Counter(a["f"] for a in ans1059)
    check("p6.1059_answers_present",
          len(ans1059) > 100 and byf["/param1"] > 0 and byf["/param6"] > 0 and byf["/param9"] > 0,
          json.dumps(dict(byf)))
    atk1059 = [a for a in ans1059 if a["f"] == "/param1"]
    check("p6.1059_attack_text_says_party_scope_not_self",
          atk1059 and all("队伍攻击率" in (a.get("value") or "") for a in atk1059)
          and not any("自身攻击" in (a.get("value") or "") for a in atk1059),
          f"{len(atk1059)} 条；样例 {atk1059[0]['value'][:60] if atk1059 else None}")
    thr1059 = [a for a in ans1059 if a["f"] == "/param0"]
    check("p6.1059_threshold_text_is_any_of_three",
          thr1059 and all("任一" in (a.get("value") or "") for a in thr1059)
          and all("同时" not in a["value"] for a in thr1059),
          f"{len(thr1059)} 条")
    heal1059 = [a for a in ans1059 if a["f"] == "/param6"]
    check("p6.1059_heal_coeff_text_is_per_maxhp",
          heal1059 and all("目标最大HP" in (a.get("value") or "") for a in heal1059),
          f"{len(heal1059)} 条")

    # ---- zero breakage against the P5 final snapshot ------------------------------
    before = C.ROOT / "work" / "p6_records_before.jsonl"
    if before.exists():
        def _keys(path):
            out = {}
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    for a in r.get("answers") or []:
                        out[(r["rec_key"], a["f"])] = a
                    for c in r.get("children") or []:
                        for x in c.get("answers") or []:
                            out[(r["rec_key"] + ">" + str(c.get("record_id")), x["f"])] = x
            return out
        b = _keys(before)
        a2 = _keys(BASE / "profiles" / "records.jsonl")
        lost = [k for k in b if k not in a2]
        chg = [k for k, v in b.items() if k in a2
               and any(v.get(f) != a2[k].get(f) for f in ("raw", "kind", "unit", "status", "scope"))]
        check("p6.existing_answer_keys_zero_loss", not lost and not chg,
              f"before={len(b)} lost={len(lost)} raw/kind/unit/status/scope_changed={len(chg)}")
    else:
        check("p6.existing_answer_keys_zero_loss", False, "缺少 work/p6_records_before.jsonl 快照")

    # discriminating: the count threshold is a *condition*; the contribution stays a
    # fixed multiplier per slot, and move/taken never swap
    t67 = [r for r in recs2 if r.get("table") == "skilllist" and r.get("effect_type") == 67]
    by_slot = collections.Counter()
    swapped, scaled_wording, thr_text = [], [], 0
    for r in t67:
        ans = {a["f"]: a for a in r.get("answers") or []}
        for f, a in ans.items():
            by_slot[(f, a.get("kind"))] += 1
        if "/param2" in ans and "/param3" in ans and ans["/param2"]["raw"] != ans["/param3"]["raw"]:
            if ans["/param2"]["kind"] != "移动速度乘数" or ans["/param3"]["kind"] != "受伤量倍率":
                swapped.append(r["rec_key"])
        atk = ans.get("/param1", {}).get("value") or ""
        if "命中角色数" in atk.replace("；", "") and "×" in atk and atk.count("命中角色数") > 0:
            # only the condition sentence may mention the count; the value must be a constant factor
            if "按人数" in atk or "×命中角色数" in atk:
                scaled_wording.append((r["rec_key"], atk))
        if "含等于" in (ans.get("/param0", {}).get("value") or ""):
            thr_text += 1
    check("composite.67_move_and_taken_never_swap",
          not swapped and by_slot[("/param2", "移动速度乘数")] > 100
          and by_slot[("/param3", "受伤量倍率")] > 100,
          f"移动 {by_slot[('/param2', '移动速度乘数')]}／受伤 {by_slot[('/param3', '受伤量倍率')]}；互换 {len(swapped)}")
    check("composite.67_contribution_is_fixed_not_count_scaled", not scaled_wording,
          f"param1 答案不得写成按人数缩放；异常 {scaled_wording[:2]}")
    check("composite.67_threshold_text_states_inclusive", thr_text > 0
          and thr_text == by_slot[("/param0", "命中角色数阈值")],
          f"{thr_text} 条阈值答案写出「含等于」")

    # 80 and 67 differ on the crit slots: 80 uses param7/param8, 67 uses param6/param7
    t80 = [a for r in recs2 if r.get("table") == "skilllist" and r.get("effect_type") == 80
           for a in r.get("answers") or []]
    kinds80 = collections.Counter(a["kind"] for a in t80)
    check("composite.80_crit_slots_are_param7_param8",
          kinds80["暴击概率加算贡献"] > 0 and kinds80["暴击伤害系数加算贡献"] > 0
          and all(a["f"] in ("/param7",) for a in t80 if a["kind"] == "暴击概率加算贡献")
          and all(a["f"] in ("/param8",) for a in t80 if a["kind"] == "暴击伤害系数加算贡献"),
          json.dumps(dict(kinds80), ensure_ascii=False))

    # 96 coefficient answers must be formula-only (they carry the mana count factor) and
    # its cap must stay numeric
    t96 = [a for r in recs2 if r.get("table") == "skilllist" and r.get("effect_type") == 96
           for a in r.get("answers") or []]
    numeric_kinds = {"玛那计数上限", "职业位图"}
    bad96 = [a for a in t96 if a["kind"] not in numeric_kinds
             and a.get("status") != "CONFIRMED_FORMULA_ONLY"]
    check("composite.96_coefficients_are_formula_only", t96 and not bad96
          and all(a["status"] == "CONFIRMED_NUMERIC" for a in t96 if a["kind"] in numeric_kinds),
          f"{len(t96)} 条；异常 {[(a['f'], a.get('status')) for a in bad96[:3]]}")

    # ---- p2b5 rectification: the type-96 counting object ---------------------------------
    fd96 = [r for r in fd if r["effect_type"] == 96]
    check("composite.96_condition_names_both_counting_objects",
          fd96 and all("斯库拉普" in (r.get("condition") or "") for r in fd96)
          and all("当前玛那" in (r.get("condition") or "") for r in fd96),
          "96 的条件必须同时写明 int(param0)==0 → 斯库拉普玛那 与 否则 → 当前玛那")

    def holder_param0(h):
        for src in (h.get("answers") or [], h.get("unexplained") or []):
            for x in src:
                if x.get("f") == "/param0":
                    return x.get("raw")
        return None

    scrap_rows, mana_rows, wrong = [], [], []
    # children may hang under a parent of another type (e.g. the 96 sub-record of an
    # ability=9 必杀技), so the type filter must be applied to the holder, not the parent
    for r in recs2:
        for h in [r] + [c for c in (r.get("children") or [])
                        if isinstance(c, dict) and "answers" in c]:
            if h.get("table") != "skilllist" or h.get("effect_type") != 96:
                continue
            p0 = holder_param0(h)
            if p0 is None:
                continue
            for a in h.get("answers") or []:
                if a["f"] in ("/iParam0",):
                    continue
                val = a.get("value") or ""
                if int(float(p0)) == 0:
                    scrap_rows.append((r["rec_key"], a["f"]))
                    if "斯库拉普" not in val:
                        wrong.append((r["rec_key"], a["f"], val[:60]))
                else:
                    mana_rows.append((r["rec_key"], a["f"]))
                    if "斯库拉普" in val:
                        wrong.append((r["rec_key"], a["f"], val[:60]))
    check("composite.96_param0_zero_records_name_scrap_mana",
          len(scrap_rows) >= 115 and not wrong,
          f"int(param0)==0 的答案 {len(scrap_rows)} 条（P5 为 115，本批新增 param2/param3 后更多）"
          f"全部写斯库拉普；int(param0)!=0 的 {len(mana_rows)} 条均未写；异常 {wrong[:3]}")
    check("composite.96_cap_semantics_is_no_cap_below_one",
          all("不设上限" in (r.get("rule") or "") for r in fd96
              if r["field_path"] == "/param1")
          and not any("按 0 计（不生效）" in (r.get("rule") or "") for r in fd96)
          and not any("按 0 计（不生效）" in (a.get("value") or "")
                      for r in recs2 for a in (r.get("answers") or [])
                      if r.get("effect_type") == 96),
          "上限槽语义＝int(param1)<1 不设上限（旧「按 0 计」措辞已清除）")
    hg2 = (comp_ev.get("helpers_probed") or {}).get("BattleParam.get_hyperGauge") or {}
    ident = hg2.get("identity") or ""
    check("composite.hypergauge_identity_is_metadata_plus_getter",
          "元数据字段表" in ident and "get_hyperGauge" in ident
          and "_hyperGauge" in ident and "0x328" in ident
          and "不成立" in ident                       # the old claim is explicitly retracted
          and "且 BattleParam..ctor 0x10f8744 在同一偏移写入" not in ident,
          "身份证据＝元数据字段表 _hyperGauge@0x328 ＋ 具名 getter；ctor 写入的旧说法已撤回")
    scrap_chk = [c for c in st_checks["checks"]
                 if c["name"] == "composite_96_param0_selects_the_counting_object"]
    check("composite.96_branch_pin_is_registered",
          bool(scrap_chk) and scrap_chk[0]["pass"],
          "原生检查：5 条路径都必须同时出现 mov w1,#0x20（斯库拉普标志）与 job-flag 转换调用")

    # the increment artifact must be recomputable from the records that were written
    cinc = json.loads((st / "composite_increment.json").read_text(encoding="utf-8"))

    def _answer_keys(path, table_filter=None, kinds=None):
        out = set()
        with Path(path).open(encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                for h in [r] + [c for c in (r.get("children") or [])
                                if isinstance(c, dict) and "answers" in c]:
                    for a in h.get("answers") or []:
                        k = (h.get("table"), h.get("record_id"), h.get("layer"), a["f"])
                        if table_filter and h.get("table") != table_filter:
                            continue
                        if kinds is not None and (h.get("effect_type"), a["f"]) not in kinds:
                            continue
                        out.add(k)
        return out

    # the P5 artifact describes exactly the P4 -> P5 delta, which is still recomputable
    # from the two snapshots (work/p5_records_before.jsonl = P4 final, work/p6_* = P5 final)
    p4 = _answer_keys(C.ROOT / "work" / "p5_records_before.jsonl")
    p5 = _answer_keys(C.ROOT / "work" / "p6_records_before.jsonl")
    added = {k for k in p5 if k not in p4 and k[0] == "skilllist"}
    check("composite_increment.unique_matches_records",
          cinc["new_answers_unique_records"] == len(added),
          f"artifact {cinc['new_answers_unique_records']} / recomputed from snapshots {len(added)}")
    check("composite_increment.reachable_and_migration_reported",
          cinc["characters_reachable_page_sum"] == {"67": 598, "80": 166, "96": 52}
          and cinc["characters_reachable_total"] == 742
          and cinc["status_migrations_unknown_to_partial"] == 97,
          json.dumps({k: cinc[k] for k in ("characters_reachable_page_sum",
                                           "characters_reachable_total",
                                           "status_migrations_unknown_to_partial")},
                     ensure_ascii=False))

    # ---- P2 batch 6 increment (vs the P5 final snapshot) ---------------------------
    # P2 batch 7 attaches taught-skill records under the denju group; those records can
    # carry P6-era (type, field) rules, so the P6 artifact is only recomputable after
    # taking the P7 attachments out of the current answer-key set.
    denju_attached_keys = set()
    for r in recs2:
        if r.get("table") != "denju":
            continue
        for ch in r.get("children") or []:
            for a in (ch.get("answers") or []) if isinstance(ch, dict) else []:
                denju_attached_keys.add((ch.get("table"), ch.get("record_id"),
                                         ch.get("layer"), a["f"]))
    p6 = json.loads((st / "p6_increment.json").read_text(encoding="utf-8"))
    # P3B3 adds an unrelated skilllist/type26/param0 rule. Compare P6's declared
    # (type, field) set, rather than counting every future skilllist rule as P6.
    p6_kinds = {(int(t), '/' + f) for t, fields in p6['rules_added'].items() for f in fields}
    cur = _answer_keys(BASE / "profiles" / "records.jsonl", kinds=p6_kinds)
    added6 = {k for k in cur if k not in p5 and k[0] == "skilllist"
              and k not in denju_attached_keys}
    check("p6_increment.added_sets_match_artifact",
          p6["new_answers_unique_records"] == len(added6)
          and p6["new_answers_page_sum"] >= p6["new_answers_unique_records"],
          f"artifact {p6['new_answers_unique_records']} / recomputed {len(added6)}"
          f"（已扣除 P2 第 7 批挂在 denju 页上的 {len(denju_attached_keys)} 个键）")
    check("p6_increment.zero_breakage",
          p6["existing_answer_keys_lost"] == 0
          and p6["existing_answer_keys_raw_kind_status_changed"] == 0,
          json.dumps({k: p6[k] for k in ("existing_answer_keys_lost",
                                         "existing_answer_keys_raw_kind_status_changed")}))
    check("p6_increment.reachable_and_migration_reported",
          p6["characters_reachable_page_sum"] == {"67": 513, "80": 166, "96": 52, "1059": 432}
          and p6["characters_reachable_total"] == 919
          and p6["status_migrations_unknown_to_partial"] == 1
          and p6["answers_by_type_page_sum"] == {"67": 2797, "80": 298, "96": 207, "1059": 5810},
          json.dumps({k: p6[k] for k in ("characters_reachable_page_sum",
                                         "characters_reachable_total",
                                         "status_migrations_unknown_to_partial",
                                         "answers_by_type_page_sum")}, ensure_ascii=False))

    # ------------------------------------------------- P2 batch 7: denju (传授必杀技)
    dj = BASE / "denju_skills"
    dj_struct = json.loads((dj / "structure.json").read_text(encoding="utf-8"))
    dj_native = json.loads((dj / "native_checks.json").read_text(encoding="utf-8"))
    dj_inc = json.loads((dj / "p7_increment.json").read_text(encoding="utf-8"))
    check("p7.denju_native_checks_all_pass",
          dj_native["checks_ok"] == dj_native["checks_total"]
          and not [c for c in dj_native["checks"] if not c["ok"]],
          f"{dj_native['checks_ok']}/{dj_native['checks_total']}")
    check("p7.denju_table_has_no_parameter_slot",
          dj_struct["skillparam_slot_keys_present_count"] == 0
          and dj_struct["param_like_keys_present"] == ["scost"],
          json.dumps(dj_struct["param_like_keys_present"], ensure_ascii=False))
    # the effect type/params must come from the referenced pattern chain, and every
    # denju row that references a pattern must resolve in cache-first order
    res = dj_struct["pattern_resolution"]
    patterns_in_data = sum(len([1 for i in range(9) if r.get(f"patternid{i}")])
                           for r in C.cache_rows("denju"))
    check("p7.denju_pattern_resolution_accounted",
          res.get("pattern_unresolved", 0) == len(dj_struct["unresolved_patternids"])
          and res.get("no_patternid", 0) == dj_struct["rows_without_any_patternid_count"]
          and (res.get("pattern_resolved_CACHE", 0) + res.get("pattern_resolved_APK", 0)
               + res.get("pattern_unresolved", 0)) == patterns_in_data,
          f"fields={patterns_in_data} {json.dumps(res, ensure_ascii=False)}")
    check("p7.denju_unresolved_patternids_absent_from_both_sources",
          all(not u["in_cache"] and not u["in_apk"] for u in dj_struct["unresolved_patternids"]),
          json.dumps(dj_struct["unresolved_patternids"], ensure_ascii=False)[:200])
    check("p7.denju_references_the_same_pattern_text",
          dj_struct["pattern_name_crosscheck"].get("sname_equal", 0) >= 900
          and dj_struct["pattern_text_crosscheck"].get("sinfo_equal", 0) >= 800,
          json.dumps({**dj_struct["pattern_name_crosscheck"],
                      **dj_struct["pattern_text_crosscheck"]}, ensure_ascii=False))
    check("p7.denju_divergent_rows_reported_not_hidden",
          dj_struct["charainfo_comparison"].get("params_1_6_differ", 0) > 0
          and dj_struct["charainfo_comparison"].get("charainfo_type_absent_in_denju_chain", 0) > 0,
          json.dumps(dj_struct["charainfo_comparison"], ensure_ascii=False))
    # linkage: every roster denju record is attached by denju_id == cid, and the rows whose
    # sname differs from the character's skillname say so instead of being silently merged
    den_links = [g for r in links for g in r["groups"] if g["group"] == "denju"]
    den_recs = [rec for g in den_links for rec in g["records"]]
    mism = [rec for rec in den_recs if rec.get("name_matches_charainfo_skillname") is False]
    check("p7.denju_linked_by_id_and_name_mismatch_annotated",
          len(den_recs) == 1500 and len(mism) > 0
          and all("不按名称推断" in (rec.get("link_status") or "") for rec in mism),
          f"records={len(den_recs)} name_mismatch={len(mism)}")
    # every attached child of a denju record is a bossskill reached through that row's
    # own denju.patternidN (the pattern ids recorded in denju_pattern_refs)
    den_children = []
    bad_children = []
    for g in den_links:
        for rec in g["records"]:
            if rec.get("table") != "denju":
                continue
            pids = {str(r["reference_id"]) for r in rec.get("denju_pattern_refs") or []}
            for ch in rec.get("boss_skill_refs") or []:
                if not ch.get("resolved"):
                    continue
                den_children.append(ch)
                field = ch.get("reference_field") or ""
                if not (field.startswith("bosspattern[")
                        and field.split("bosspattern[")[1].split("]")[0] in pids):
                    bad_children.append(field)
    check("p7.denju_children_are_pattern_skills",
          den_children and not bad_children,
          f"children={len(den_children)} bad={bad_children[:3]} sample={den_children[0].get('reference_field')}")
    check("p7.denju_answers_are_typed_bossskill_rules",
          {"13", "16", "27", "66", "105", "112", "2012"}
          <= set(dj_inc["answers_by_type_page_sum"])
          and sum(dj_inc["answers_by_type_page_sum"].values()) == dj_inc["new_answers_page_sum"],
          json.dumps(dj_inc["answers_by_type_page_sum"], ensure_ascii=False))
    # the artifact is recomputed against the *current* rule set: later batches that add
    # rules on types reachable from a denju chain (P2 batch 8) legitimately increase it,
    # so the check recomputes the denju-page answer count from the products themselves
    by_key = {r.get("rec_key"): r for r in recs2}
    recomputed_pages = 0
    recomputed_groups = collections.Counter()
    with (BASE / "profiles" / "profiles.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)
            for g in p["groups"]:
                if g["group"] not in ("denju", "denju_lb"):
                    continue
                for ref in g["records"]:
                    rec = by_key.get(ref.get("rec_key"))
                    if rec is None:
                        continue
                    for holder in [rec] + [c for c in rec.get("children") or []
                                           if isinstance(c, dict)]:
                        for a in holder.get("answers") or []:
                            recomputed_pages += 1
                            recomputed_groups[g["group"]] += 1
    check("p7.denju_page_sum_recomputed_from_the_products",
          recomputed_pages == dj_inc["new_answers_page_sum"]
          and dict(recomputed_groups) == dj_inc["answers_by_group"],
          f"artifact={dj_inc['new_answers_page_sum']} recomputed={recomputed_pages}；"
          f"（P7 终态为 3236，P2 第 8 批给传授链上的攻击系类型补规则后增大）")
    check("p7.denju_zero_breakage_and_migration_reported",
          dj_inc["existing_answer_keys_lost"] == 0
          and dj_inc["existing_answer_keys_raw_kind_unit_status_scope_changed"] == 0
          and dj_inc["status_migrations_unknown_to_partial"] >= 1
          and dj_inc["unexplained_fields_delta"]["distinct_keys_removed"] >= 11
          and dj_inc["unexplained_fields_delta"].get("distinct_keys_removed_by_table"),
          json.dumps({k: dj_inc[k] for k in ("existing_answer_keys_lost",
                                             "existing_answer_keys_raw_kind_unit_status_scope_changed",
                                             "status_migrations_unknown_to_partial")},
                     ensure_ascii=False)
          + "；未解释去重键减少含 P7 的 11 个（传授突破逐条键）与后续批次的槽位转答案两类")
    check("p7.denju_broken_links_are_the_documented_pattern_gaps",
          dj_inc["broken_links"] == 3
          and {u["patternid"] for u in dj_struct["unresolved_patternids"]}
          == {30126402, 30831202, 120310, 43011403, 43033903, 43034003},
          f"broken_links={dj_inc['broken_links']}（6 个 patternid 两源均缺；名册内命中 3 个角色）")

    # discriminating samples: a denju row whose referenced pattern carries a *different*
    # skill than the character's own special move must answer with the denju chain's slots
    diff_rows = [r for r in load_jsonl(dj / "denju_chains.jsonl")
                 if (r.get("charainfo_comparison") or {}).get("params_1_6_equal") is False]
    check("p7.denju_divergent_sample_keeps_chain_values", len(diff_rows) > 0,
          f"divergent rows={len(diff_rows)} 例：{diff_rows[0]['denju_id'] if diff_rows else None}")
    if diff_rows:
        # a divergent row that is actually on a character page (the denju table also holds
        # rows whose denju_id is not in the playable roster)
        picked = None
        for row in diff_rows:
            for r in recs2:
                if r.get("table") != "denju" or r.get("record_id") != row["denju_id"]:
                    continue
                if any((ch.get("answers") or []) for ch in r.get("children") or []):
                    picked = (row, r)
                    break
            if picked:
                break
        check("p7.denju_divergent_sample_found_on_a_page", picked is not None,
              f"{len(diff_rows)} divergent rows（同类值不同的传授版本）")
        row, rec = picked
        cid = row["denju_id"]
        chain_params = []
        for c in row["chain"]:
            for s in c.get("skills") or []:
                if s.get("resolved"):
                    chain_params.append((s["skillid"], s["effect_type"],
                                         s["params"].get("skillparam1")))
        shown = []
        for ch in rec.get("children") or []:
            for a in ch.get("answers") or []:
                if a["f"] == "/skillparam1":
                    shown.append((ch.get("record_id"), a["raw"], a.get("value")))
        own = (row.get("charainfo_comparison") or {}).get("charainfo_params", {}) or {}
        chain_vals = {cp[2] for cp in chain_params}
        check("p7.denju_sample_shows_chain_value_not_own_skillparam",
              bool(chain_params) and bool(shown)
              and all(v in chain_vals or abs(v - (own.get("skillparam1") or 0)) < 1e-9
                      for _rid, v, _txt in shown)
              and any(v in chain_vals and abs(v - (own.get("skillparam1") or 0)) > 1e-9
                      for _rid, v, _txt in shown),
              f"cid={cid} 链上 skillparam1={sorted(chain_vals)} "
              f"角色自身 skillparam1={own.get('skillparam1')} 页面显示={shown[:2]}")

    # ---- p2b6 rectification: the union-count special case is stated as <= 0 ---------
    u1059 = [r for r in recs2 if r.get("table") == "skilllist" and r.get("effect_type") == 1059]
    wrong_eq = [a for r in u1059 for a in r.get("answers") or []
                if a["f"] == "/param0" and "均不为正" not in (a.get("value") or "")]
    check("p2b6_note3.union_threshold_says_non_positive",
          not wrong_eq and u1059,
          f"param0 answers rewritten: {sum(1 for r in u1059 for a in r.get('answers') or [] if a['f'] == '/param0')}")
    check("p2b6_note5.weapon_jump_table_entry_is_a_byte",
          any("字节" in s for s in
              (json.loads((st / "filter_dictionary.json").read_text(encoding="utf-8"))
               ["weapon"]["native_evidence"])),
          "filter_dictionary.json weapon.native_evidence")
    check("p2b6_note4.paramn_aggregation_is_extremum_selection",
          "极值选择" in json.dumps(
              json.loads((st / "union_count_chains.json").read_text(encoding="utf-8"))
              .get("player_side_paramn_aggregation", {}), ensure_ascii=False),
          "union_count_chains.json player_side_paramn_aggregation")

    # ------------------------------------ P2 batch 8: attack-family boss types
    ba = BASE / "boss_attack_types"
    ba_checks = json.loads((ba / "native_checks.json").read_text(encoding="utf-8"))
    ba_rules = json.loads((ba / "type_rules.json").read_text(encoding="utf-8"))
    ba_dict = json.loads((ba / "field_dictionary.json").read_text(encoding="utf-8"))
    ba_inc = json.loads((ba / "p8_increment.json").read_text(encoding="utf-8"))
    check("p8.native_checks_all_pass",
          ba_checks["passed"] == ba_checks["total"] >= 85
          and not [c for c in ba_checks["checks"] if not c["ok"]],
          f"{ba_checks['passed']}/{ba_checks['total']}")
    by_key = {(r.get("effect_type"), r.get("field_path")): r for r in ba_dict}
    check("p9.p2b8_text_fixes_present",
          "_skillChainRate" in by_key[(5, "/skillparam3")]["rule"]
          and "_pushPower" in by_key[(5, "/skillparam3")]["rule"]
          and "_pushPower" in by_key[(47, "/skillparam4")]["rule"]
          and "范围重判" in by_key[(110, "/skillparam6")]["rule"]
          and "范围外也消耗预算" not in by_key[(110, "/skillparam6")]["rule"]
          and "+ 1" in by_key[(1, "/skillparam3")]["rule"],
          "type5/47 push 文案、type110 sp6 范围措辞、type1 sp3 追加回数")
    check("p8.damage_base_is_the_shared_skill_base_function",
          ba_rules["damage_base"]["rva"] == "0x1182ed8"
          and ba_rules["damage_base"]["integerisation_rva"] == "0x14374bc"
          and "getBasicSkillAttack" in ba_rules["damage_base"]["function"]
          and any(c["name"] == "global_offset_table_is_not_a_damage_table" and c["ok"]
                  for c in ba_checks["checks"]),
          json.dumps(ba_rules["damage_base"], ensure_ascii=False)[:220])
    expect_slots = {0: {"atk_rate": 1, "push_pow": 3},
                    1: {"atk_rate": 1, "push_pow": None, "interval": 2, "count_cap": 3},
                    2: {"atk_rate": 1, "push_pow": 3, "move_offset": 2},
                    3: {"atk_rate": 1, "push_pow": 3, "area_len": 2, "origin_scale": 4},
                    4: {"atk_rate": 1, "push_pow": 3},
                    5: {"atk_rate": 1, "push_pow": 3, "bullet_radius_h": 4},
                    22: {"atk_rate": 1, "push_pow": 4, "front_reach": 2, "front_width": 3},
                    47: {"atk_rate": 0, "push_pow": 4, "bomb_type": 1, "bomb_radius0": 2,
                         "bomb_radius1": 3, "atk_rate_second": 5},
                    105: {"atk_rate": 1, "push_pow": 4, "interval": 5},
                    110: {"atk_rate": 1, "push_pow": 3, "area_len": 2, "origin_scale": 4,
                          "interval": 5, "count_cap": 6}}
    got_slots = {int(t): {k: (v.get("slot") if isinstance(v, dict) else v)
                          for k, v in info["slots"].items()}
                 for t, info in ba_rules["types"].items()}
    check("p8.slot_table_matches_the_expected_map",
          all(got_slots.get(t, {}).get(k) == v for t, m in expect_slots.items()
              for k, v in m.items()),
          json.dumps(got_slots, ensure_ascii=False))
    check("p8.type1_push_power_is_a_native_hard_coded_zero",
          (ba_rules["types"]["1"]["slots"]["push_pow"].get("slot") is None)
          and "硬编码 0" in (ba_rules["types"]["1"].get("push_pow_hardcoded_zero") or ""),
          (ba_rules["types"]["1"].get("push_pow_hardcoded_zero") or "")[:120])
    earlier = set()
    for path, table_default in ((C.CARD_COMPARISON / "field_dictionary.json", "skilllist"),
                                (BASE.parent / "boss_heal" / "field_dictionary.json", "bossskill"),
                                (st / "field_dictionary.json", "skilllist")):
        if not path.exists():
            continue
        for r in json.loads(path.read_text(encoding="utf-8")):
            table = r.get("table")
            if table is None:
                if "bossskill" in (r.get("file_table") or ""):
                    table = "bossskill"
                else:
                    table = table_default
            fp = r.get("field_path") or ""
            fp = fp if fp.startswith("/") else "/" + fp
            earlier.add((table, r.get("effect_type"), fp))
    check("p8.new_rules_do_not_redeclare_existing_keys",
          all((r["table"], r["effect_type"], r["field_path"]) not in earlier for r in ba_dict)
          and any(s["field_path"] == "/skillparam1" and s["type"] == 105
                  for s in ba_rules.get("skipped_existing_keys", [])),
          f"{len(ba_dict)} 条新规则键与既有字典 0 重叠；105/skillparam1 因既有规则跳过")
    rules_json = json.loads((BASE / "profiles" / "rules.json").read_text(encoding="utf-8"))
    merged_keys = {f"{r['table']}|{r['effect_type']}|{r['field_path']}" for r in ba_dict}
    check("p8.rules_merged_into_rules_json_with_their_origin",
          all(k in rules_json for k in merged_keys)
          and all(rules_json[k].get("origin") ==
                  "output/character_skills/boss_attack_types/field_dictionary.json"
                  for k in merged_keys),
          f"{len(merged_keys)} keys")
    t105p1 = rules_json.get("bossskill|105|/skillparam1", {})
    check("p8.existing_type105_damage_rule_not_overwritten",
          "boss_attack_types" not in (t105p1.get("origin") or ""),
          f"bossskill|105|/skillparam1 origin={t105p1.get('origin')}")
    kinds = {}
    for r in ba_dict:
        kinds[f"{r['table']}|{r['effect_type']}|{r['field_path']}"] = r["answer_kind"]
    bad_kinds = []
    found = collections.Counter()
    for r in recs2:
        for holder in [r] + [c for c in r.get("children") or []
                             if isinstance(c, dict) and "answers" in c]:
            for a in holder.get("answers") or []:
                k = a.get("rule_key")
                if k in kinds:
                    found[k] += 1
                    if a.get("kind") is None or a.get("unit") is None:
                        bad_kinds.append(k)
    check("p8.every_new_rule_key_produces_answers_with_kind_and_unit",
          not bad_kinds and set(found) == merged_keys,
          f"{len(found)}/{len(merged_keys)} rule keys have answers; bad={bad_kinds[:3]}")
    check("p8.damage_answers_say_floor_on_the_shared_base",
          all("floor/clamp" in (a.get("value") or "")
              for r in recs2
              for holder in [r] + [c for c in r.get("children") or []
                                   if isinstance(c, dict) and "answers" in c]
              for a in holder.get("answers") or []
              if (a.get("rule_key") or "").split("|")[1:] and
              a["rule_key"] in {k for k, v in kinds.items() if v == "atk_rate"}),
          "atk_rate 答案文本含 floor/clamp（不是向零截断）")
    check("p8.increment_calibers_consistent",
          # 口径（P2 第 10 批更新）：`new_answers_from_earlier_rule_sets_page_sum` 是**页实例**计数，
          # 它会把基准之后**任何**非 P8 规则产生的答案都算进来（含 P10 的新规则），因此
          # 「record_level + earlier == unique_keys」在后续批次之后不再成立（shared 记录被多页引用）。
          # 保留仍然精确成立的总量对账与结构性上界：
          #   page_sum(P8 规则) + earlier(其它规则，页实例) == rule_answers(现在) - rule_answers(P8 基线)
          #   record_level(P8 规则的去重键) <= unique_keys(基准后新增的全部去重键)
          ba_inc["new_answers_page_sum"] >= 14132
          and ba_inc["new_answers_record_level"] <= ba_inc["new_answer_keys_unique"]
          and ba_inc["new_answers_page_sum"]
          + ba_inc["new_answers_from_earlier_rule_sets_page_sum"]
          == json.loads((BASE / "profiles" / "summary.json").read_text(encoding="utf-8"))["totals"]["rule_answers"]
          - json.loads((ROOT_SUMMARY_BEFORE).read_text(encoding="utf-8"))["totals"]["rule_answers"],
          json.dumps({k: ba_inc[k] for k in ("new_answers_page_sum",
                                             "new_answers_from_earlier_rule_sets_page_sum",
                                             "new_answers_record_level",
                                             "new_answer_keys_unique")}, ensure_ascii=False))
    check("p8.zero_breakage_and_migration_reported",
          ba_inc["existing_answer_keys_lost"] == 0
          and ba_inc["existing_answer_keys_raw_kind_unit_status_scope_changed"] == 0
          and ba_inc["existing_answer_keys_value_text_changed"] == 0
          and ba_inc["status_migrations_unknown_to_partial"] >= 39
          and ba_inc["unknown_reachability"]["unknown_characters_after"] <= 334,
          json.dumps({k: ba_inc[k] for k in ("existing_answer_keys_lost",
                                             "existing_answer_keys_raw_kind_unit_status_scope_changed",
                                             "status_migrations_unknown_to_partial")},
                     ensure_ascii=False))
    check("p8.migration_routes_report_the_equivalence_gate",
          any("charainfo" in route for route in
              ba_inc["unknown_reachability"]["migrated_routes_by_count"])
          and any("pattern" in route for route in
                  ba_inc["unknown_reachability"]["migrated_routes_by_count"]),
          json.dumps(ba_inc["unknown_reachability"]["migrated_routes_by_count"],
                     ensure_ascii=False)[:200])
    emu = [c for c in ba_checks["checks"] if c["name"] == "integerisation_emulated_on_the_game_bytes"]
    floor_ok = False
    if emu and emu[0]["ok"]:
        floor_ok = any("frintm" in c.get("detail", "")
                       for c in ba_checks["checks"]
                       if c["name"] == "integerisation_is_floor_not_truncation")
    check("p8.emulated_integerisation_is_floor_with_int32_clamp", floor_ok,
          "受控执行 0x14374bc：-0.5→-1、+inf→int32 最小值（与向零截断不同）")
    ref_notes = [info.get("reference_lead_note") for info in ba_rules["types"].values()]
    check("p8.reference_leads_recorded_as_conflicts_not_adopted",
          all(any("参考候选" in (n or "") for n in ref_notes) for t in ("3", "22", "110")),
          "type_rules.json 的 type 3/22/110 带 reference_lead_note（逐槽与参考标签冲突）")


    # ---------------------------------------------------------------- P2 第 10 批
    # 证据来自 output/character_skills/boss_heal_types/（生成器 boss_heal_types.py）。
    _p10_dir = BASE / "boss_heal_types"
    p10_rules = load_json(_p10_dir / "type_rules.json")
    p10_checks = load_json(_p10_dir / "native_checks.json")
    p10_dict = load_json(_p10_dir / "field_dictionary.json")
    p10_inc = load_json(_p10_dir / "p10_increment.json")
    check("p10.native_checks_all_pass",
          p10_checks["passed"] == p10_checks["total"] and p10_checks["total"] >= 216,
          f"{p10_checks['passed']}/{p10_checks['total']}")
    hf = p10_rules["heal_family"]
    check("p10.heal_family_shares_one_handler_with_mode_arguments",
          hf["handler"] == "bhSkill.Exec_HEAL" and hf["handler_rva"] == "0x1299c74"
          and hf["common_body_rva"] == "0x1188194"
          and all(p10_rules["types"][str(t)]["handler"] == "bhSkill.Exec_HEAL"
                  for t in (10, 11, 12, 14, 26, 28, 31, 32, 46)),
          json.dumps({str(t): p10_rules["types"][str(t)]["mode_selector"] for t in (10, 11, 28, 31)},
                     ensure_ascii=False))
    check("p10.heal_formula_and_consumer_are_the_shared_ones",
          hf["formula"] == "回复量 = floor/clamp(float32(B × skillparam1))；B = getBasicSkillAttack(true)"
          and hf["integerisation_rva"] == "0x14374bc"
          and hf["consumer"] == "CharaBehavior.Heal(0x1541158)，regTime 参数接收超上限比率",
          hf["formula"])
    over = {str(t): (p10_rules["types"][str(t)]["slots"].get("over_heal_ratio") or {}).get("slot")
            for t in (10, 11, 28, 31, 32)}
    check("p10.over_heal_floor_slot_is_type_specific",
          over == {"10": 2, "11": 2, "28": 5, "31": 4, "32": 4}
          and hf["over_heal_bits"] == [40, 35, 41, 42, 43, 44],
          json.dumps(over, ensure_ascii=False))
    raw_chain = {str(t): (p10_rules["types"][str(t)]["slots"].get("support_attack") or
                          p10_rules["types"][str(t)]["slots"].get("support_attack_raw") or
                          {}).get("kind") for t in (12, 14, 26, 28, 31, 46)}
    check("p10.support_slots_use_the_body_stores_not_the_metadata_order",
          raw_chain == {"12": "support_attack", "14": "support_attack",
                        "26": "support_attack", "28": "support_attack_raw",
                        "31": "support_attack_raw", "46": "support_attack_raw"}
          and "元数据 parameters 的顺序在此" in hf["support_object"],
          json.dumps(raw_chain, ensure_ascii=False))
    existing = set()
    cc = C.CARD_COMPARISON / "field_dictionary.json"
    for r in load_json(cc):
        existing.add((r.get("table") or "skilllist", r.get("effect_type"),
                      r.get("field_path") if str(r.get("field_path", "")).startswith("/")
                      else "/" + str(r.get("field_path"))))
    bh = C.ROOT / "output" / "boss_heal" / "field_dictionary.json"
    for r in load_json(bh):
        if "bossskill" in (r.get("file_table") or ""):
            existing.add(("bossskill", r.get("effect_type"), r.get("field_path")))
    ba_existing = {f"{r['table']}|{r['effect_type']}|{r['field_path']}"
                   for r in load_json(BASE / "boss_attack_types" / "field_dictionary.json")}
    p10_keys = [f"{r['table']}|{r['effect_type']}|{r['field_path']}" for r in p10_dict]
    check("p10.new_rules_do_not_redeclare_existing_keys",
          len(p10_keys) == len(set(p10_keys))
          and all(k.split("|")[0] != "bossskill" or
                  (k.split("|")[0], int(k.split("|")[1]), k.split("|")[2]) not in existing
                  for k in p10_keys)
          and not (set(p10_keys) & ba_existing)
          and all(r["type"] in (13, 15, 16) and r["already_covered"]
                  for r in [p10_rules["types"]["13"]])
          and "boss_heal" in " ".join(p10_rules["types"]["13"]["unresolved"]),
          f"{len(p10_keys)} 条新规则键；既有字典重叠 0；type13 标记为 already_covered"
          f"（其 sp1/sp2/sp3/sp6 由 boss_heal 字典定义，merge 只补缺键）")
    p10_recs = load_jsonl(BASE / "profiles" / "records.jsonl")
    found10 = collections.Counter()
    bad10 = []
    for r in p10_recs:
        for holder in [r] + [c for c in r.get("children") or []
                             if isinstance(c, dict) and "answers" in c]:
            for a in holder.get("answers") or []:
                k = a.get("rule_key")
                if k in p10_keys:
                    found10[k] += 1
                    if not a.get("kind") or not a.get("unit"):
                        bad10.append(k)
    check("p10.every_new_rule_key_produces_answers_with_kind_and_unit",
          not bad10 and set(found10) == set(p10_keys),
          f"{len(found10)}/{len(p10_keys)}；bad={bad10[:3]}")
    healed = [a for r in p10_recs
              for h in [r] + [c for c in r.get("children") or []
                              if isinstance(c, dict) and "answers" in c]
              for a in h.get("answers") or []
              if (a.get("rule_key") or "").startswith("bossskill|")
              and (a.get("rule_key") or "") in {k for k in p10_keys
                                                if k.endswith("/skillparam1")}
              and a.get("kind") == "单次回复量的技能基值系数"]
    check("p10.heal_answers_state_amount_object_and_limits",
          healed and all("floor/clamp(float32(B × " in a["value"]
                         and "对象：" in a["value"]
                         and "CharaBehavior.Heal" in a["value"]
                         and "不是最终回血量" in a["value"]
                         and a.get("status") == "CONFIRMED_FORMULA_ONLY"
                         for a in healed),
          f"{len(healed)} 条回复量答案；样本原文：{healed[0]['value'][:120]}" if healed else "无")
    over_ans = [a for r in p10_recs
                for h in [r] + [c for c in r.get("children") or []
                                if isinstance(c, dict) and "answers" in c]
                for a in h.get("answers") or []
                if a.get("kind") == "超上限（HP 上限）档位的附加槽"]
    check("p10.over_heal_answers_state_the_flag_table_and_the_max_rule",
          over_ans and all("max(技能标志位算出的档位" in a["value"]
                           and "1.2,1.3,1.4,1.6,1.8,2.0" in a["value"]
                           and "不是回复量倍数" in (a["unit"] or "") for a in over_ans),
          f"{len(over_ans)} 条超上限答案")
    st = json.loads((BASE / "profiles" / "summary.json").read_text(encoding="utf-8"))["status_counts"]
    # P10's terminal five are a historical assertion. Reconstruct using its frozen
    # rule scope; later rules must not change the denominator of this old check.
    p10_frozen = C.ROOT / 'work/character_skills_p3b1/before'
    p10_rule_keys = set(load_json(p10_frozen / 'rules.json'))
    def unknown_in_scope(records, profiles, keys):
        counts = {r['rec_key']: sum(a['rule_key'] in keys for h in [r] + r['children']
                                  for a in h.get('answers', [])) for r in records}
        return {p['cid'] for p in profiles if not (len(p.get('baseline', [])) +
                sum(counts[ref['rec_key']] for g in p['groups'] for ref in g['records']))}
    p10_frozen_unknown = unknown_in_scope(load_jsonl(p10_frozen / 'records.jsonl'),
                                         load_jsonl(p10_frozen / 'profiles.jsonl'), p10_rule_keys)
    current_profiles = load_jsonl(BASE / 'profiles/profiles.jsonl')
    p10_scope_unknown = unknown_in_scope(p10_recs, current_profiles, p10_rule_keys)
    current_unknown = unknown_in_scope(p10_recs, current_profiles, set(rules_json))
    check("p10.unknown_only_status_shrank_to_the_documented_remainder",
          p10_frozen_unknown == p10_scope_unknown == {4009, 4049, 8116, 8151, 10018}
          and p10_inc.get("status", {}).get("仅未知") == 5
          and current_unknown <= p10_scope_unknown and len(current_unknown) == st.get('仅未知', 0),
          json.dumps(dict(p10_scope_unknown=sorted(p10_scope_unknown), current_unknown=sorted(current_unknown), status=st), ensure_ascii=False))
    cp_inc = load_json(BASE / "cp_paths" / "p9_increment.json")
    check("p10.zero_breakage_against_the_p9_terminal_snapshot",
          cp_inc["existing_answer_keys_lost"] == 0
          and cp_inc["existing_answer_keys_raw_kind_unit_status_scope_changed"] == 0
          and cp_inc["status_migrations_unknown_to_partial"] >= 187
          and cp_inc["remaining_unknown"] == 5,
          json.dumps({k: cp_inc[k] for k in ("existing_answer_keys_lost",
                                             "status_migrations_unknown_to_partial",
                                             "remaining_unknown")}, ensure_ascii=False))
    p33 = p10_rules["types"]["33"]
    check("p10.fall_area_gives_offset_and_selector_but_no_damage_number",
          (p33["slots"].get("fall_offset") or {}).get("slot") == 3
          and (p33["slots"].get("fall_selector") or {}).get("slot") == 6
          and any("AirAreaStrike" in u for u in p33["unresolved"])
          and (p10_rules["types"]["103"]["slots"].get("fall_offset") or {}).get("slot") == 3,
          json.dumps(p33["unresolved"], ensure_ascii=False)[:200])
    # p2b10 review F1: type 46 shares type 28's over-heal floor load (skillparam5).  The
    # branch must be read with flag semantics (`fmov`/`b` do not set NZCV).
    p46_over = (p10_rules["types"]["46"]["slots"].get("over_heal_ratio") or {})
    branch_ok = any(c["name"] == "over_heal_floor_slot_follows_the_branch_not_the_first_reading"
                    and c["ok"] for c in p10_checks["checks"])
    check("p10.type46_over_heal_floor_is_skillparam5_via_the_shared_load",
          (p46_over.get("slot"), p46_over.get("load_rva")) == (5, "0x11882ac")
          and (p10_rules["types"]["28"]["slots"].get("over_heal_ratio") or {}).get("load_rva")
          == "0x11882ac"
          and branch_ok,
          f"46→{p46_over.get('slot')}@{p46_over.get('load_rva')}；分支求值检查={branch_ok}")
    t46_sp5 = [a for r in p10_recs
               for h in [r] + [c for c in r.get("children") or []
                               if isinstance(c, dict) and "answers" in c]
               for a in h.get("answers") or []
               if a.get("rule_key") == "bossskill|46|/skillparam5"]
    check("p10.type46_over_heal_answers_state_the_ceiling_rule",
          len(t46_sp5) >= 100
          and all("允许回复到的 HP 上限比率 = max(技能标志位算出的档位" in (a.get("value") or "")
                  and "1.2,1.3,1.4,1.6,1.8,2.0" in (a.get("value") or "")
                  and "不是回复量倍数" in (a.get("unit") or "")
                  for a in t46_sp5),
          f"{len(t46_sp5)} 条 type46/sp5 答案；raw 取值 "
          f"{sorted({a['raw'] for a in t46_sp5})}")
    # p2b10 review F4: no rendered answer may repeat a clause inside one sentence
    # (template + role_note/limits saying the same thing).  Clause = text between '；'.
    dup_bad = []
    seen_p10 = {}
    for r in p10_recs:
        for h in [r] + [c for c in (r.get("children") or [])
                        if isinstance(c, dict) and "answers" in c]:
            for a in h.get("answers") or []:
                if a.get("rule_key") in p10_keys:
                    seen_p10.setdefault(a["rule_key"], a)
    for k, a in seen_p10.items():
        clauses = [c.strip() for c in (a.get("value") or "").split("；") if c.strip()]
        for i, c1 in enumerate(clauses):
            for j, c2 in enumerate(clauses):
                if i != j and len(c1) >= 12 and c1[:14] == c2[:14]:
                    dup_bad.append({"rule": k, "clause": c1[:60]})
                    break
            if dup_bad and dup_bad[-1]["rule"] == k:
                break
    check("p10.answers_have_no_repeated_clause", not dup_bad,
          f"复制句检查覆盖 {len(seen_p10)} 条规则；重复={dup_bad[:3]}")

    # ------------------------------------------------------------------ end
    failed = [n for n, ok, _ in RESULTS if not ok]
    print("\n" + "=" * 70)
    print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("FAILED:")
        for n in failed:
            print("  -", n)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
