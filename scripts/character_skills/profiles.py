"""Item 3 - per-character skill answers (JSON / CSV / self-contained HTML).

Consumes ``output/character_skills/links/character_skills.jsonl`` and applies the
confirmed rule layer (``rules.py``, reused from field_dictionary.json +
verified_parameter_views.json). Every answer keeps the raw value, the rule text,
the unit/base, target, conditions, source location and evidence status.

Outputs are normalised so the same skill record is stored once:

* ``rules.json``      - one entry per confirmed rule, keyed ``table|type|field``
* ``records.jsonl``   - one entry per resolved record (answer + fragment level)
* ``profiles.jsonl``  - one entry per character, referencing record keys
* ``answers.csv`` / ``descriptions.csv`` / ``characters.csv`` - flat views
* ``index.html``      - self-contained viewer (cid / name query, per-character page)

A character is never silently declared complete: the status is explicitly scoped
to "already confirmed rules in this batch" and untouched fragments stay visible.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common as C  # noqa: E402
import equivalence as EQ  # noqa: E402
import rules as R  # noqa: E402
import description_bindings as DB  # noqa: E402
import batch_bindings as BB  # noqa: E402
import p3b7_bindings as B7  # noqa: E402
import p3b8_bindings as B8  # noqa: E402
import p3b9_bindings as B9  # noqa: E402
import p3b10_bindings as B10  # noqa: E402

LINKS = C.ROOT / "output" / "character_skills" / "links" / "character_skills.jsonl"
OUT = C.ROOT / "output" / "character_skills" / "profiles"
CID30236 = C.CARD_COMPARISON / "description_effects.json"

TEXT_SOURCE = {
    "skilllist": ("text", "name"),
    "heroicskilllist": ("text", "name"),
    "bosspattern": ("sinfo", "sname"),
    "charainfo": ("skilltext", "skillname"),
    "supporterskill": ("text", "name"),
    "leader_ability": ("text", None),
    "job_ability": ("text", None),
    "extra_ability_info": ("text", "name"),
    "passive_info": ("text", "name"),
    "denju": ("stext", "sname"),
    "denju_limit_break_info": ("stext", "sname"),
    "crossworld_ability_info": (None, None),
    "bossskill": (None, None),
}

KEYWORD_HINT = [
    (("攻撃力", "与えるダメージ"), ("攻击倍率", "攻击加算增量", "技能基值倍率", "攻击增益输入")),
    # damage-type base-value multipliers and heal-type base-value multipliers must
    # not be mixed: 技能基值倍率(回复) only matches recovery wording

    (("防御力", "受けるダメージ", "ダメージを減少"), ("受伤量倍率", "受伤量加算增量", "固定防御量（系数已知）",
                                            "屏障固定防御量系数")),
    (("移動速度",), ("移动速度乘数", "移动因子增加量")),
    (("クリティカル発生率", "クリティカル率"), ("暴击概率加算贡献",)),
    (("クリティカル威力", "クリティカルダメージ"), ("暴击伤害系数加算贡献",)),
    (("攻撃間隔", "攻撃速度"), ("攻击间隔乘数",)),
    (("回復", "HPが"), ("暴击回复比例", "暴击回复HP上限档位", "回复HP上限档位", "技能基值倍率(回复)")),
    (("マナ", "法珠"), ("Chain获珠数量", "概率阈值", "玛那数量配置", "概率阈值增加量")),
    (("Chain",), ()),
    (("一定時間", "秒間"), ("持续时间", "时间间隔", "地形变化的正持续时间")),
    (("地形", "砂漠", "森林", "荒地", "街中", "洞窟", "雪山"), ("地形条件编码",)),
    (("回", "回まで", "回数"), ("次数上限", "次数")),
]

REASON_TEXT = {
    "NO_RULE_FOR_TYPE": "该表・该类型下的这个字段没有本批已确认规则",
    "NON_FINITE_VALUE": "原值不是有限数值，未做数值换算",
    "CHARAINFO_EQUIVALENCE_UNPROVEN":
        "该 charainfo 记录的原值不是战斗执行值，或没有可对齐的执行侧记录，因此不把 boss 规则迁到这里"
        "（X1／X0：自身 pattern 可解析，执行取 pattern 侧的 bossskill；本记录 skillparam 是未执行的副本；"
        "NOT_AMONG：自身 pattern 的类型集合不含 skillid[0]；两侧原值与路径见 "
        "output/character_skills/charainfo_params/ 与 output/character_skills/cp_paths/）",
}

RECORD_STORE: dict[str, dict] = {}
RULE_KEYS: dict[str, dict] = {}


def rule_key(table, etype, field_path):
    return f"{table}|{etype}|{field_path}"


def register_rule(rule: dict) -> str:
    key = rule_key(rule.get("table"), rule.get("effect_type"), rule.get("field_path"))
    if key not in RULE_KEYS:
        RULE_KEYS[key] = {
            "table": rule.get("table"),
            "effect_type": rule.get("effect_type"),
            "field_path": rule.get("field_path"),
            "meaning_zh": rule.get("meaning_zh"),
            "unit": rule.get("unit"),
            "conversion": rule.get("conversion"),
            "base_definition": rule.get("base_definition"),
            "target": rule.get("target"),
            "conditions": rule.get("applicability"),
            "evidence": rule.get("evidence"),
            "status": rule.get("status"),
            "limits": rule.get("limits"),
            "occurrences": rule.get("occurrences"),
            "origin": rule.get("origin") or "output/card_comparison_cid30236/field_dictionary.json",
        }
    return key


def split_fragments(text: str) -> list[str]:
    if not text:
        return []
    text = text.replace("\\n", "\n")
    cut = text.find("[i][c]")
    if cut > 0:
        text = text[:cut]
    parts = []
    for line in text.split("\n"):
        for chunk in line.split("。"):
            chunk = chunk.strip()
            if not chunk:
                continue
            parts.extend(p.strip() for p in chunk.split("◆") if p.strip())
    out = []
    for p in parts:
        p = p.rstrip("。").strip()
        if p and p not in out:
            out.append(p)
    return out


def record_type(rec: dict, table: str):
    if table in ("skilllist", "heroicskilllist", "supporterskill"):
        return rec.get("ability")
    if table == "bossskill":
        return rec.get("skillid0")
    if table == "charainfo":
        # grouping hint only: the reference analysis groups charainfo params by
        # skillid[0]. This project has no confirmed rule on that grouping, so the
        # value is carried for gap ranking / lead matching, not as a rule type.
        return rec.get("skillid0")
    return None


def type_field(table: str) -> str:
    if table == "bossskill":
        return "skillid0"
    if table == "charainfo":
        return "skillid[0]"
    return "ability"


VIEW_INDEX: dict | None = None


def view_index() -> dict:
    """(table, record_id, field) -> True for every field instance the earlier lines
    actually reviewed. Used to separate 'this record/field was reviewed' from
    'the rule was applied to this type without a record-level review'.
    """
    global VIEW_INDEX
    if VIEW_INDEX is None:
        idx = set()
        for p in (C.CARD_COMPARISON / "verified_parameter_views.json",
                  C.ROOT / "output" / "boss_heal" / "verified_parameter_views.json"):
            if not p.exists():
                continue
            for r in json.loads(p.read_text(encoding="utf-8")):
                field = r.get("field_path") or ""
                if not field.startswith("/"):
                    field = "/" + field
                idx.add((r.get("table"), r.get("record_id"), field))
        VIEW_INDEX = idx
    return VIEW_INDEX


def evidence_scope(table: str, record_id, field_path: str) -> str:
    return ("IN_REVIEWED_VIEW" if (table, record_id, field_path) in view_index()
            else "BY_TYPE_EXTRAPOLATED")


def collect_answers(rec: dict, table: str, effect_type, record_id=None):
    """(answers, unexplained) for every param-like field present in the record.

    For ``charainfo`` the boss rule set is served through the equivalence alias
    (see ``rules.rule_index``), so every candidate field is first put through the
    record-level gate in ``equivalence.field_allowed``. A field that fails the gate
    stays unexplained with an explicit reason code -- the transfer is never
    assumed, and the two states ("equivalence proven" / "not proven") stay apart.
    """
    answers, unexplained = [], []
    for key in sorted(rec):
        if not R.is_param_like(key):
            continue
        value = rec[key]
        if isinstance(value, bool) or value is None:
            continue
        fpath = "/" + key
        if not isinstance(value, (int, float)):
            unexplained.append({"f": fpath, "raw": value, "reason": "NON_FINITE_VALUE"})
            continue
        # A charainfo field only gets an answer when the record-level equivalence
        # clears it. Fields whose rule would come from the boss alias but whose value
        # is not value-identical to the matched boss stay unexplained.
        rule = R.rule_for(table, effect_type, fpath)
        gate_class = None
        if table == "charainfo" and rule is not None:
            ok, why = EQ.field_allowed(record_id, fpath)
            if not ok:
                unexplained.append({"f": fpath, "raw": value,
                                    "reason": "CHARAINFO_EQUIVALENCE_UNPROVEN",
                                    "detail": why})
                continue
            gate_class = why
        if rule is None:
            unexplained.append({"f": fpath, "raw": value, "reason": "NO_RULE_FOR_TYPE"})
            continue
        ans = R.answer_for(table, effect_type, fpath, value, rec)
        item = {
            "f": fpath,
            "raw": value,
            "rule_key": register_rule(rule),
            "value": ans.get("value_text"),
            "kind": ans.get("quantity_kind"),
            "unit": ans.get("unit"),
            "status": ans.get("answer_status"),
            "scope": evidence_scope(table, record_id if record_id is not None
                                    else (rec.get("skillid") or rec.get("patternid") or rec.get("cid")),
                                    fpath),
        }
        if ans.get("note"):
            item["note"] = ans["note"]
        if table == "charainfo" and gate_class and gate_class.startswith(EQ.NO_PATTERN_FALLBACK):
            path_note = ("证据路径（P2 第 9 批）：本角色自身 pattern 无可达 boss 技能 → "
                         "CharaParamToBossSkill(0x13aa390) 把本记录 skillid[0]／skillparamN 构造成执行用 "
                         "BattleBossSkill 并经同一 ExecSkill 派发；若当次必杀由传授链/英雄技 pattern 承担则以那一侧为准")
            if rule.get('answer_kind') == 'remaining_five':
                item['note'] = path_note + ('；' + item['note'] if item.get('note') else '')
            else:
                item["note"] = (item["note"] + "；" + path_note) if item.get("note") else path_note
        answers.append(item)
    return answers, unexplained


def build_record(entry: dict, base_by_record: dict, sub_effect_refs=None) -> str:
    """Register (or reuse) the normalised record and return its key."""
    table = entry.get("table")
    rec = entry.get("record") or {}
    etype = record_type(rec, table)
    tf = type_field(table) if etype is not None else "text"
    rkey = f"{table}|{entry.get('reference_id')}|{entry.get('layer')}|{tf}={etype}"
    if rkey in RECORD_STORE:
        return rkey

    text_field, name_field = TEXT_SOURCE.get(table, (None, None))
    text = rec.get(text_field) if text_field else None
    name = rec.get(name_field) if name_field else None
    answers, unexplained = collect_answers(rec, table, etype, entry.get("reference_id"))

    children = []
    child_sources = [(entry.get("boss_skill_refs") or [], "boss_skill"),
                     (entry.get("sa_ability_refs") or [], "boss_skill.s_ability"),
                     (entry.get("skill_refs") or [], "ability_ref"),
                     (entry.get("sympathy_skill_refs") or [], "sympathy_ref"),
                     (sub_effect_refs or [], "sub_effect")]
    for refs, kind in child_sources:
        for sub in refs:
            if not sub.get("resolved") or not sub.get("record"):
                continue
            stable = sub.get("table") or "skilllist"
            stype = record_type(sub["record"], stable)
            cans, cun = collect_answers(sub["record"], stable, stype, sub.get("reference_id"))
            children.append({
                "link_kind": kind,
                "table": stable,
                "namespace": sub.get("namespace"),
                "record_id": sub.get("reference_id"),
                "layer": sub.get("layer"),
                "type_field": type_field(stable) if stable in ("skilllist", "heroicskilllist",
                                                               "supporterskill", "bossskill") else None,
                "effect_type": stype,
                "answers": cans,
                "unexplained": cun,
                "source": sub.get("source"),
            })

    fragments = []
    # candidates carry their owning record so the same field path on two different
    # records (e.g. /skillparam1 of a damage skill vs of a heal skill) is not collapsed
    cands_src = [(table, entry.get("reference_id"), a) for a in answers]
    cands_src += [(ch["table"], ch["record_id"], a) for ch in children for a in ch["answers"]]
    for frag in split_fragments(text):
        frag = frag[:400]
        uniq, seen, shown_keys = [], set(), {}
        for kws, kinds in KEYWORD_HINT:
            if not kinds or not any(k in frag for k in kws):
                continue
            for ct, cid, a in cands_src:
                # identity stays per record (different records may carry the same field),
                # but the *display* row is folded on (field, value) so sibling records of
                # the same type do not produce visibly duplicated candidate lines
                key = (ct, cid, a["f"])
                shown = (a["f"], a["value"])
                if a.get("kind") in kinds and a.get("status") == "CONFIRMED_NUMERIC" and key not in seen:
                    seen.add(key)
                    if shown in shown_keys:
                        uniq[shown_keys[shown]]["n"] = uniq[shown_keys[shown]].get("n", 1) + 1
                        continue
                    shown_keys[shown] = len(uniq)
                    uniq.append({"f": a["f"], "value": a["value"], "table": ct, "record_id": cid})
        base_hits = [b for b in (base_by_record.get((table, entry.get("reference_id")))
                                 or base_by_record.get((table, None), []))
                     if b.get("description_fragment_ja")
                     and (b["description_fragment_ja"] in frag or frag in b["description_fragment_ja"])]
        if base_hits:
            status = "BASELINE_DESCRIPTION_ANSWER"
            for b in base_hits:
                uniq.append({"f": b.get("effect_id"), "value": b.get("readable_value"),
                             "from_baseline": True})
        elif uniq:
            status = "INFERRED_KEYWORD_HINT"
        else:
            status = "UNEXPLAINED_FRAGMENT"
        item = {"t": frag, "status": status, "cands": uniq}
        if table == "skilllist" and etype == 8 and not base_hits:
            binding, rejection = DB.bind_type8(entry, frag, answers, children)
            if binding:
                item.update(status=DB.STATUS, binding=binding, cands=binding["fields"])
            else:
                item["binding_rejection"] = rejection
        if table == "skilllist" and etype == 26 and not base_hits:
            from type26_mana import bind_type26
            binding, rejection = bind_type26(entry, frag, answers, children)
            if binding:
                item.update(status=DB.STATUS, binding=binding, cands=binding["fields"])
            else:
                item["binding_rejection"] = rejection
        # P3B6's queue is separate from the old editorial decisions. A queue
        # membership check only selects the structural recogniser; its native,
        # grammar, source, subtree and all-reference guards still have to pass.
        if not base_hits and not item.get("binding") and f"{table}|{entry.get('reference_id')}" in BB.scope()['records']:
            binding, rejection = BB.bind(entry, frag, answers, children)
            if binding:
                item.update(status=DB.STATUS, binding=binding, cands=binding['fields'])
                item.pop('binding_rejection', None)
        if not base_hits and not item.get("binding") and f"{table}|{entry.get('reference_id')}" in B7.scope()['records']:
            binding, rejection = B7.bind(entry, frag, answers, children)
            if binding:
                item.update(status=DB.STATUS, binding=binding, cands=binding['fields'])
                item.pop('binding_rejection', None)
        if not base_hits and not item.get("binding") and f"{table}|{entry.get('reference_id')}" in B8.scope()['records']:
            binding, rejection = B8.bind(entry, frag, answers, children)
            if binding:
                item.update(status=DB.STATUS, binding=binding, cands=binding['fields'])
                item.pop('binding_rejection', None)
        if not base_hits and not item.get("binding") and f"{table}|{entry.get('reference_id')}" in B9.scope()['records']:
            binding, rejection = B9.bind(entry, frag, answers, children)
            if binding:
                item.update(status=DB.STATUS, binding=binding, cands=binding['fields'])
                item.pop('binding_rejection', None)
        if not base_hits and not item.get("binding") and f"{table}|{entry.get('reference_id')}" in B10.scope()['records']:
            binding, rejection = B10.bind(entry, frag, answers, children)
            if binding:
                item.update(status=DB.STATUS, binding=binding, cands=binding['fields'])
                item.pop('binding_rejection', None)
        fragments.append(item)

    RECORD_STORE[rkey] = {
        "rec_key": rkey,
        "table": table,
        "namespace": entry.get("namespace"),
        "record_id": entry.get("reference_id"),
        "layer": entry.get("layer"),
        "type_field": type_field(table) if etype is not None else None,
        "effect_type": etype,
        "type_hint": ({"field": "charainfo.skillid[0]", "value": rec.get("skillid0"),
                       "note": ("必杀技效果类型（与 bossskill.skillid0 同域）；参考分析也按该值给 charainfo 参数分组。"
                                "本项目对该参数没有已确认规则，故只作分组与线索，不作答案")}
                      if table == "charainfo" else None),
        "name": name,
        "text": text,
        "link_status": entry.get("link_status"),
        "source": entry.get("source"),
        "answers": answers,
        "unexplained": unexplained,
        "fragments": fragments,
        "children": children,
        "baseline_answers": [
            {k2: b.get(k2) for k2 in ("effect_id", "description_fragment_ja", "effect_zh",
                                      "readable_value", "quantity_kind", "unit", "target",
                                      "condition", "duration", "answer_status", "evidence")}
            for b in (base_by_record.get((table, entry.get("reference_id")))
                      or base_by_record.get((table, None), []))
        ],
        "sub_ids": list(rec.get("sub") or []),
    }
    return rkey


def load_baseline() -> dict:
    if not CID30236.exists():
        return {}
    rows = json.loads(CID30236.read_text(encoding="utf-8"))
    by = collections.defaultdict(list)
    for r in rows:
        by[r["cid"]].append(r)
    return by


BASELINE = load_baseline()


def build_character(row: dict) -> dict:
    base_rows = BASELINE.get(row["cid"], [])
    base_by_record = collections.defaultdict(list)
    for b in base_rows:
        base_by_record[(b.get("description_table"), b.get("description_record_id"))].append(b)

    subs_by_parent = collections.defaultdict(list)
    for s in row.get("sub_effect_refs") or []:
        subs_by_parent[s.get("parent_record_id")].append(s)

    groups_out = []
    char_answers = char_unexpl = char_ans_view = 0
    frag_total = frag_attr = frag_hint = frag_base = frag_internal = 0
    frag_confirmed = frag_reviewed = 0
    frag_unique = set()

    for g in row["groups"]:
        refs = []
        for e in g["records"]:
            rkey = build_record(e, base_by_record, subs_by_parent.get(e.get("reference_id")))
            stored = RECORD_STORE[rkey]
            all_ans = list(stored["answers"]) + [a for ch in stored["children"] for a in ch["answers"]]
            char_answers += len(all_ans)
            char_ans_view += sum(1 for a in all_ans if a.get("scope") == "IN_REVIEWED_VIEW")
            char_unexpl += len(stored["unexplained"]) + sum(len(ch["unexplained"]) for ch in stored["children"])
            for f in stored["fragments"]:
                frag_total += 1
                frag_unique.add((stored["table"], stored["record_id"], f["t"]))
                # records whose text is only an internal label (text == name) are not
                # user-facing descriptions
                if stored["text"] and stored["name"] and stored["text"].strip() == stored["name"].strip():
                    frag_internal += 1
                if f["status"] == "BASELINE_DESCRIPTION_ANSWER":
                    frag_attr += 1
                    frag_base += 1
                    frag_confirmed += 1
                elif f["status"] == DB.STATUS:
                    frag_attr += 1
                    frag_confirmed += 1
                    frag_reviewed += 1
                elif f["status"] == "INFERRED_KEYWORD_HINT":
                    frag_attr += 1
                    frag_hint += 1
            refs.append({
                "rec_key": rkey,
                "reference_field": e.get("reference_field"),
                "link_status": e.get("link_status"),
                "ambiguous": e.get("ambiguous"),
                "alternative_candidates": e.get("alternative_candidates"),
            })
        groups_out.append({"group": g["group"], "label": g["label"],
                           "records": refs, "unresolved": g.get("unresolved") or [],
                           "annotations": g.get("annotations") or []})

    broken = len(row["unresolved"])
    total_answers = char_answers + len(base_rows)
    # "完整" is deliberately strict: every description fragment must have a real
    # answer (a keyword hint alone is NOT enough) and there must be no broken link.
    if not total_answers:
        status = "仅未知"
    elif frag_total - frag_confirmed == 0 and broken == 0:
        status = "完整"
    else:
        status = "部分"

    return {
        "cid": row["cid"],
        "name": row.get("name"),
        "title": row.get("title"),
        "rarity": row.get("rarity"),
        "job_name": (None if row.get("job_name") in (None, "未知") else row.get("job_name")),
        "job_name_raw": row.get("job_name"),
        "roster_source": row.get("roster_source"),
        "charainfo_layer": row.get("charainfo_layer"),
        "charainfo_source": row.get("charainfo_source"),
        "status_scope": "本批已确认规则范围内（不是全机制已解释）",
        "status": status,
        "coverage": {
            "records": row["counts"]["records"],
            "answers": char_answers,
            "answers_in_reviewed_view": char_ans_view,
            "answers_by_type_extrapolated": char_answers - char_ans_view,
            "unexplained_fields": char_unexpl,
            "descriptions": frag_total,
            "descriptions_unique": len(frag_unique),
            "descriptions_unique_key": "每角色页内按 (表, 记录, 片段) 去重后求和；跨角色共享记录会各计一次", 
            "descriptions_internal_label": frag_internal,
            "descriptions_with_answer": frag_total - (frag_total - frag_attr),
            "fragments_attributed": frag_attr,
            "fragments_attributed_confirmed": frag_confirmed,
            "fragments_attributed_hint_only": frag_hint,
            "descriptions_attributed": frag_attr,
            "descriptions_with_hint": frag_hint,
            "descriptions_from_baseline": frag_base,
            "descriptions_reviewed_bindings": frag_reviewed,
            "descriptions_unexplained": frag_total - frag_attr,
            "descriptions_per_page_unique": len(frag_unique),
            "descriptions_global_unique": None,
            "broken_links": broken,
            "sub_effect_refs": row["counts"]["sub_effect_refs"],
            "annotations": row["counts"].get("annotations", 0),
            "baseline_answers": len(base_rows),
        },
        "groups": groups_out,
        "baseline": base_rows,
        "unresolved": row["unresolved"],
        "sub_effect_refs": [{"parent_record_id": s.get("parent_record_id"),
                             "reference_id": s.get("reference_id"),
                             "table": s.get("table"),
                             "layer": s.get("layer"),
                             "resolved": s.get("resolved")}
                            for s in row["sub_effect_refs"]],
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>角色技能档案（已确认规则范围内）</title>
<style>
:root{--bg:#12151c;--fg:#e7ebf3;--dim:#9aa6bd;--card:#1b2029;--line:#2a3240;--ok:#5fd6a0;--warn:#e6c07b;--bad:#e88a8a;--acc:#7cb7ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 "Yu Gothic UI","Meiryo",system-ui,sans-serif}
header{position:sticky;top:0;background:#0e1117ee;padding:10px 16px;border-bottom:1px solid var(--line);z-index:9}
h1{font-size:16px;margin:0 0 8px}
input{background:#0b0e14;border:1px solid var(--line);color:var(--fg);padding:7px 10px;border-radius:6px;width:320px;font-size:14px}
button{background:#232a36;border:1px solid var(--line);color:var(--fg);padding:6px 10px;border-radius:6px;cursor:pointer;margin-left:6px}
button:hover{border-color:var(--acc)}
main{padding:16px;max-width:1200px;margin:0 auto}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:0 0 14px}
.meta{color:var(--dim);font-size:12.5px}
.tag{display:inline-block;border:1px solid var(--line);border-radius:5px;padding:0 6px;margin:2px 6px 2px 0;font-size:12px}
.grp{margin:12px 0 0;border-top:1px dashed var(--line);padding-top:10px}
.grp>h3{margin:0 0 6px;font-size:14px;color:var(--acc)}
table{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0 0}
th,td{border:1px solid var(--line);padding:5px 7px;text-align:left;vertical-align:top}
th{background:#161b23;color:var(--dim);font-weight:600}
.raw{color:var(--dim);font-family:Consolas,monospace;font-size:12px}
.st-CONFIRMED_NUMERIC,.st-BASELINE_DESCRIPTION_ANSWER,.st-REVIEWED_DESCRIPTION_BINDING{color:var(--ok)}
.st-CONFIRMED_FORMULA_ONLY,.st-INFERRED_KEYWORD_HINT{color:var(--warn)}
.st-UNEXPLAINED_FIELD,.st-UNEXPLAINED_FRAGMENT{color:var(--bad)}
details{margin:6px 0}
summary{cursor:pointer;color:var(--dim)}
pre{white-space:pre-wrap;word-break:break-word;background:#0b0e14;border:1px solid var(--line);border-radius:6px;padding:8px;font-size:12.5px}
.miss{color:var(--bad)}
ul.nav{list-style:none;display:flex;flex-wrap:wrap;gap:6px;padding:0;margin:8px 0 0}
ul.nav li a{color:var(--acc);text-decoration:none;border:1px solid var(--line);border-radius:5px;padding:1px 7px;font-size:12px}
footer{color:var(--dim);font-size:12px;padding:10px 16px 40px;text-align:center}
</style></head><body>
<header>
<h1>《锁链战记》角色技能档案 —— 已确认规则范围内（P1＋P2＋P3 试点）</h1>
<div>
<input id="q" placeholder="输入 cid 或角色名，如 30236 / チーカ" autocomplete="off">
<button onclick="go()">查询</button>
<button onclick="pick()">随机一个</button>
<span class="meta" id="stat"></span>
</div>
<ul class="nav" id="nav"></ul>
</header>
<main id="view"></main>
<footer>数据由 scripts/character_skills/profiles.py 生成；答案原值／单位／依据来自本项目已确认规则，未解释项显式列出。</footer>
<script>const RULES=__RULES__,RECS=__RECS__,CHARS=__CHARS__,REASON=__REASON__,STAT=__STAT__;
__QUERY_JS__
</script></body></html>
"""

QUERY_JS = r"""
const byCid=new Map(),byName=new Map();
CHARS.forEach(d=>{byCid.set(String(d.cid),d);if(d.name){const a=byName.get(d.name)||[];a.push(d);byName.set(d.name,a);}});
const STAT_ZH={'CONFIRMED_NUMERIC':'已确认数值','CONFIRMED_FORMULA_ONLY':'已确认公式（数值另含运行时因子）',
 'UNEXPLAINED_FIELD':'未解释字段','UNEXPLAINED_FRAGMENT':'未解释片段（本批无规则）',
 'INFERRED_KEYWORD_HINT':'仅关键词提示（推断归属，非代码确认）','BASELINE_DESCRIPTION_ANSWER':'已有逐描述答案（cid30236 基线）',
 'REVIEWED_DESCRIPTION_BINDING':'已审定描述对应（原值／原生效果规则支持）'};
const SCOPE_ZH={'IN_REVIEWED_VIEW':'该字段已在既有证据视图中被逐条评审',
 'BY_TYPE_EXTRAPOLATED':'按类型套用（该记录本身未被逐条评审）'};
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function rawJson(v){return esc(JSON.stringify(v));}
function altText(u){
  const alts=u.alternative_candidates||[];
  if(!alts.length)return '<span class="raw">无</span>';
  return alts.map(a=>esc(a.table+' #'+a.record_id+(a.sname?(' '+a.sname):''))).join('<br>');
}
function ruleRow(a){
  const r=RULES[a.rule_key];if(!r)return '';
  const ev=Array.isArray(r.evidence)?r.evidence.join(' ; '):r.evidence;
  return '<tr><td></td><td colspan="6" class="raw">换算：'+esc(r.conversion||'')+
    '　基数：'+esc(r.base_definition||'（见规则条件）')+
    '　依据：'+esc(ev||'')+'　规则状态：'+esc(r.status||'')+
    (r.limits?('　边界：'+esc(r.limits)):'')+'</td></tr>';
}
function answersTable(list){
  if(!list||!list.length)return '<div class="miss">本记录没有已确认规则答案。</div>';
  let h='<table><tr><th>字段</th><th>原值</th><th>答案</th><th>数量类型／单位</th><th>对象</th><th>条件</th><th>证据范围</th><th>状态</th></tr>';
  list.forEach(a=>{const r=RULES[a.rule_key]||{};
    h+='<tr><td>'+esc(a.f)+'</td><td class="raw">'+rawJson(a.raw)+'</td><td>'+esc(a.value||'')+(a.note?(' <span class="raw">'+esc(a.note)+'</span>'):'')+'</td>'+
       '<td>'+esc(a.kind||'-')+' ／ '+esc(a.unit||'-')+'</td><td>'+esc(r.target||'-')+'</td><td>'+esc(r.conditions||'-')+'</td>'+
       '<td class="raw" title="'+esc(SCOPE_ZH[a.scope]||'')+'">'+esc(a.scope==='IN_REVIEWED_VIEW'?'已逐条评审':'按类型套用')+'</td>'+
       '<td class="st-'+esc(a.status)+'">'+esc(STAT_ZH[a.status]||a.status)+'</td></tr>';
    h+=ruleRow(a);});
  return h+'</table>';
}
function unexplHtml(list){
  if(!list||!list.length)return '';
  let h='<details><summary>未解释字段 '+list.length+'</summary><table><tr><th>字段</th><th>原值</th><th>原因</th></tr>';
  list.forEach(u=>{h+='<tr><td>'+esc(u.f)+'</td><td class="raw">'+rawJson(u.raw)+'</td><td>'+esc(REASON[u.reason]||u.reason)+'</td></tr>';});
  return h+'</table></details>';
}
function fragHtml(list){
  if(!list||!list.length)return '';
  let h='<details><summary>描述片段（'+list.length+'）</summary><table><tr><th>原文片段</th><th>片段归属</th><th>候选答案</th></tr>';
  list.forEach(f=>{const c=(f.cands||[]).map(x=>esc(x.value)+' <span class="raw">'+esc(x.f)+(x.from_baseline?' (已有答案)':'')+'</span>').join('<br>')||'<span class="miss">未解释</span>';
    const b=f.binding;
    const detail=b?('<br><span class="raw">'+esc(b.strength)+'<br>对象：'+esc(b.target)+'；条件：'+esc(b.condition)+'；时间：'+esc(b.duration)+
      '<br>模板：'+esc(b.template_id)+'；来源：'+esc((b.source||{}).record_key)+'；'+esc(b.limits)+'</span>'):'';
    h+='<tr><td>'+esc(f.t)+'</td><td class="st-'+esc(f.status)+'">'+esc(STAT_ZH[f.status]||f.status)+
      (f.binding_rejection?('<br><span class="raw">试点未绑定：'+esc(f.binding_rejection)+'</span>'):'')+'</td><td>'+c+detail+'</td></tr>';});
  return h+'</table></details>';
}
function renderChar(d){
  const c=d.coverage;let h='<div class="card">';
  h+='<h2 style="margin:0 0 4px">'+esc(d.name)+' <span class="meta">cid '+esc(d.cid)+'</span></h2>';
  const job=(d.job_name?esc(d.job_name):(d.job_name_raw==='未知'?'职业：名册缺值':'职业：-'));
  h+='<div class="meta">'+esc(d.title||'')+'　稀有度 '+(d.rarity==null?'-':d.rarity)+'　'+job+'　角色记录来源 '+esc(d.charainfo_layer)+'</div>';
  h+='<div style="margin:8px 0"><span class="tag">状态 '+esc(d.status)+'（'+esc(d.status_scope)+'）</span>'+
     '<span class="tag">技能记录 '+c.records+'</span><span class="tag">规则答案 '+c.answers+'（已逐条评审 '+c.answers_in_reviewed_view+'／按类型套用 '+c.answers_by_type_extrapolated+'）</span>'+
     (c.baseline_answers?('<span class="tag">已有逐描述答案 '+c.baseline_answers+'</span>'):'')+
     '<span class="tag">描述片段 '+c.descriptions+'（本页求和；去重 '+c.descriptions_unique+'，其中记录内部标签 '+c.descriptions_internal_label+'）</span>'+
     '<span class="tag">有归属 '+c.descriptions_attributed+' ＝已有答案 '+c.descriptions_from_baseline+' ＋审定对应 '+c.descriptions_reviewed_bindings+' ＋仅关键词提示 '+c.descriptions_with_hint+'／未解释 '+c.descriptions_unexplained+'</span>'+
     '<span class="tag">必杀技类型标注 '+c.annotations+'</span>'+
     '<span class="tag">未解释字段 '+c.unexplained_fields+'</span><span class="tag">断链 '+c.broken_links+'</span></div>';
  if(d.baseline&&d.baseline.length){
    h+='<div class="grp"><h3>已有逐描述答案（cid30236 基线，直接引用，不重做研究）</h3>'+
       '<table><tr><th>片段</th><th>中文效果</th><th>可读数值</th><th>数量类型</th><th>单位</th><th>对象／条件</th><th>状态</th></tr>';
    d.baseline.forEach(b=>{h+='<tr><td>'+esc(b.description_fragment_ja)+'</td><td>'+esc(b.effect_zh)+'</td><td>'+esc(b.readable_value)+'</td>'+
      '<td>'+esc(b.quantity_kind||'-')+'</td><td>'+esc(b.unit||'-')+'</td><td>'+esc((b.target||'-')+' ／ '+(b.condition||'-'))+'</td>'+
      '<td class="st-'+esc(b.answer_status)+'">'+esc(STAT_ZH[b.answer_status]||b.answer_status)+'</td></tr>';
      if(b.evidence)h+='<tr><td></td><td colspan="6" class="raw">依据：'+esc(b.evidence)+'</td></tr>';});
    h+='</table></div>';
  }
  if(d.unresolved&&d.unresolved.length){
    h+='<details class="miss"><summary>断链 '+d.unresolved.length+' 条（保留，不静默丢弃）</summary><table><tr><th>引用字段</th><th>原 ID</th><th>期望表</th><th>同号候选（未合并）</th><th>说明</th></tr>';
    d.unresolved.forEach(u=>{h+='<tr><td>'+esc(u.reference_field)+'</td><td>'+esc(u.reference_id)+'</td><td>'+esc(u.expected_table)+'</td>'+
      '<td>'+altText(u)+'</td><td>'+esc(u.note)+'</td></tr>';});
    h+='</table></details>';
  }
  d.groups.forEach(g=>{
    const ann=g.annotations||[];
    if(!g.records.length&&!(g.unresolved||[]).length&&!ann.length)return;
    h+='<div class="grp"><h3>'+esc(g.label)+'</h3>';
    ann.forEach(a=>{
      h+='<table><tr><th>槽位</th><th>原值</th><th>解释</th><th>本角色自身的必杀技效果类型</th><th>判定</th></tr>'+
         '<tr><td>'+esc(a.slot)+'</td><td class="raw">'+esc(a.raw_value)+'</td><td>'+esc(a.interpretation)+'</td>'+
         '<td class="raw">'+esc((a.own_pattern_effect_types||[]).join('、')||'（本角色无 pattern，缓存与 APK 都缺）')+'</td>'+
         '<td class="raw">'+esc(a.verdict)+'</td></tr>'+
         '<tr><td></td><td colspan="4" class="raw">'+esc(a.note)+'</td></tr>';
      (a.same_number_unrelated_records||[]).forEach(r2=>{
        h+='<tr><td></td><td colspan="4" class="raw">同号无关记录：'+esc(r2.table+' #'+r2.record_id+' '+(r2.name||''))+'　'+esc(r2.note)+'</td></tr>';});
      (a.evidence||[]).forEach(e=>{h+='<tr><td></td><td colspan="4" class="raw">依据：'+esc(e)+'</td></tr>';});
      h+='</table>';
    });
    if((g.unresolved||[]).length){
      h+='<details class="miss"><summary>本组断链 '+g.unresolved.length+'</summary><table><tr><th>引用字段</th><th>原 ID</th><th>期望表</th><th>同号候选（未合并）</th></tr>';
      g.unresolved.forEach(u=>{h+='<tr><td>'+esc(u.reference_field)+'</td><td>'+esc(u.reference_id)+'</td><td>'+esc(u.expected_table)+'</td><td>'+altText(u)+'</td></tr>';});
      h+='</table></details>';
    }
    g.records.forEach(ref=>{const r=RECS[ref.rec_key];if(!r)return;
      h+='<div style="margin:8px 0 0"><b>'+esc(r.name||r.namespace||r.table)+'</b> '+
         '<span class="raw">'+esc(r.table)+' #'+esc(r.record_id)+
         (r.effect_type!=null?(' '+esc(r.type_field)+'='+esc(r.effect_type)):'')+(r.layer?(' ['+esc(r.layer)+']'):'')+'</span>';
      if(ref.ambiguous)h+=' <span class="tag miss">槽位歧义：同号另一命名空间仅登记候选，未合并</span>';
      if(ref.link_status)h+=' <span class="tag">'+esc(ref.link_status)+'</span>';
      if((ref.alternative_candidates||[]).length)h+='<div class="raw">同号候选：'+ref.alternative_candidates.map(a=>esc(a.table+' #'+a.record_id+(a.sname?(' '+a.sname):''))).join('；')+'</div>';
      if(r.source&&r.source.record_key)h+='<div class="raw">来源 '+esc(r.source.record_key)+
        (r.source.byte_begin!=null?('　字节 '+r.source.byte_begin+'–'+r.source.byte_end_exclusive):'')+
        (r.source.original_file?('　原文件 '+esc(r.source.original_file)):'')+'</div>';
      if(r.text)h+='<details open><summary>原文</summary><pre>'+esc(r.text)+'</pre></details>';
      h+=answersTable(r.answers);
      h+=unexplHtml(r.unexplained);
      (r.children||[]).forEach(ch=>{
        h+='<div style="margin-left:12px;border-left:2px solid var(--line);padding-left:8px">'+
           '<span class="raw">子记录 ['+esc(ch.link_kind||'?')+'] '+esc(ch.table)+' #'+esc(ch.record_id)+
           (ch.effect_type!=null?(' '+esc(ch.type_field)+'='+esc(ch.effect_type)):'')+'</span>'+
           answersTable(ch.answers)+unexplHtml(ch.unexplained)+'</div>';
      });
      h+=fragHtml(r.fragments);
      h+='</div>';
    });
    h+='</div>';
  });
  return h+'</div>';
}
function show(d){document.getElementById('view').innerHTML=renderChar(d);location.hash='cid='+d.cid;}
function showCid(c){const d=byCid.get(String(c));if(d)show(d);}
function go(){const q=document.getElementById('q').value.trim();if(!q)return pick();
  const d=byCid.get(q);
  if(d){show(d);return;}
  const list=byName.get(q)||[];
  if(list.length===1){show(list[0]);return;}
  if(list.length>1){
    let h='<div class="card"><b>名称「'+esc(q)+'」对应 '+list.length+' 个 cid</b>（同名不同 cid 不合卡，请选择）<table><tr><th>cid</th><th>称号</th><th>稀有度</th><th>状态</th></tr>';
    list.forEach(x=>{h+='<tr><td><a href="javascript:void(0)" onclick="showCid('+x.cid+')">'+esc(x.cid)+'</a></td><td>'+esc(x.title||'')+'</td><td>'+esc(x.rarity)+'</td><td>'+esc(x.status)+'</td></tr>';});
    h+='</table></div>';
    document.getElementById('view').innerHTML=h;return;
  }
  document.getElementById('view').innerHTML='<div class="card miss">未找到 cid 或名称「'+esc(q)+'」的角色。已知角色 '+CHARS.length+' 个（名册可玩范围）。</div>';}
function pick(){show(CHARS[Math.floor(Math.random()*CHARS.length)]);}
function fromHash(){const m=location.hash.match(/cid=(\d+)/);if(m){const d=byCid.get(m[1]);if(d){document.getElementById('q').value=m[1];document.getElementById('view').innerHTML=renderChar(d);return true;}}return false;}
document.getElementById('q').addEventListener('keydown',e=>{if(e.key==='Enter')go();});
document.getElementById('stat').textContent='共 '+CHARS.length+' 个角色；完整 '+(STAT['完整']||0)+'／部分 '+(STAT['部分']||0)+'／仅未知 '+(STAT['仅未知']||0);
const nav=document.getElementById('nav');
['完整','部分','仅未知'].forEach(k=>{const li=document.createElement('li');const a=document.createElement('a');a.href='javascript:void(0)';
  a.textContent=k+' ('+(STAT[k]||0)+')';a.onclick=()=>{const d=CHARS.find(x=>x.status===k);if(d)show(d);};li.appendChild(a);nav.appendChild(li);});
window.addEventListener('hashchange',fromHash);
if(!fromHash()){const d=byCid.get('30236')||CHARS[0];document.getElementById('view').innerHTML=renderChar(d);}
"""


def main():
    C.enable_utf8_console()
    rows = [json.loads(line) for line in LINKS.open(encoding="utf-8")]
    profiles = [build_character(r) for r in rows]
    status_count = collections.Counter(p["status"] for p in profiles)

    C.write_json(OUT / "rules.json", RULE_KEYS)
    C.write_jsonl(OUT / "records.jsonl", list(RECORD_STORE.values()))
    C.write_jsonl(OUT / "profiles.jsonl", profiles)

    ans_header = ["cid", "name", "group", "table", "namespace", "record_id", "effect_type",
                  "field_path", "raw_value", "value_text", "quantity_kind", "unit",
                  "answer_status", "evidence_scope", "rule_key", "source_key", "json_pointer", "note"]
    ans_rows = []
    for p in profiles:
        for g in p["groups"]:
            for ref in g["records"]:
                r = RECORD_STORE[ref["rec_key"]]

                def emit(a, rec):
                    ans_rows.append([p["cid"], p["name"], g["label"], rec.get("table"),
                                     rec.get("namespace"), rec.get("record_id"), rec.get("effect_type"),
                                     a.get("f"), json.dumps(a.get("raw"), ensure_ascii=False),
                                     a.get("value"), a.get("kind"), a.get("unit"), a.get("status"),
                                     a.get("scope", "IN_REVIEWED_VIEW") if a.get("status") != "UNEXPLAINED_FIELD" else "",
                                     a.get("rule_key"), (rec.get("source") or {}).get("source_key"),
                                     (rec.get("source") or {}).get("json_pointer"), a.get("note")])

                for a in r["answers"]:
                    emit(a, r)
                for ch in r["children"]:
                    for a in ch["answers"]:
                        emit(a, ch)
        for b in p["baseline"]:
            ans_rows.append([p["cid"], p["name"], b.get("group"), "baseline_description_effects",
                             "cid30236 已有研究", b.get("description_record_id"), None,
                             b.get("effect_id"), "", b.get("readable_value"), b.get("quantity_kind"),
                             b.get("unit"), b.get("answer_status"), "BASELINE_EXISTING_RESEARCH", None,
                             "output/card_comparison_cid30236/description_effects.json", None,
                             b.get("evidence")])
    C.write_csv(OUT / "answers.csv", ans_header, ans_rows)

    desc_header = ["cid", "name", "group", "table", "record_id", "fragment_ja",
                   "attribution_status", "candidate_count", "candidates", "binding_strength",
                   "binding_json", "binding_rejection"]
    desc_rows = []
    for p in profiles:
        for g in p["groups"]:
            for ref in g["records"]:
                r = RECORD_STORE[ref["rec_key"]]
                for f in r["fragments"]:
                    desc_rows.append([p["cid"], p["name"], g["label"], r.get("table"),
                                      r.get("record_id"), f["t"], f["status"], len(f["cands"]),
                                      " | ".join(f"{c['f']}={c['value']}" for c in f["cands"]),
                                      (f.get("binding") or {}).get("strength"),
                                      json.dumps(f["binding"], ensure_ascii=False) if f.get("binding") else "",
                                      f.get("binding_rejection")])
    C.write_csv(OUT / "descriptions.csv", desc_header, desc_rows)

    char_header = ["cid", "name", "title", "rarity", "job_name", "charainfo_layer", "status",
                   "records", "answers", "answers_in_reviewed_view", "answers_by_type_extrapolated",
                   "baseline_answers", "unexplained_fields", "annotations", "descriptions",
                   "descriptions_unique", "descriptions_internal_label", "fragments_attributed",
                   "descriptions_with_hint", "descriptions_from_baseline", "descriptions_reviewed_bindings",
                   "descriptions_unexplained", "fragments_attributed_confirmed",
                   "fragments_attributed_hint_only", "broken_links", "sub_effect_refs"]
    char_rows = []
    for p in profiles:
        c = p["coverage"]
        char_rows.append([p["cid"], p["name"], p["title"], p["rarity"], p.get("job_name_raw"),
                          p["charainfo_layer"], p["status"], c["records"], c["answers"],
                          c["answers_in_reviewed_view"], c["answers_by_type_extrapolated"],
                          c["baseline_answers"], c["unexplained_fields"], c["annotations"],
                          c["descriptions"], c["descriptions_unique"], c["descriptions_internal_label"],
                          c["fragments_attributed"], c["descriptions_with_hint"],
                          c["descriptions_from_baseline"], c["descriptions_reviewed_bindings"], c["descriptions_unexplained"],
                          c["fragments_attributed_confirmed"], c["fragments_attributed_hint_only"],
                          c["broken_links"], c["sub_effect_refs"]])
    C.write_csv(OUT / "characters.csv", char_header, char_rows)

    html = (HTML_TEMPLATE
            .replace("__RULES__", json.dumps(RULE_KEYS, ensure_ascii=False))
            .replace("__RECS__", json.dumps(RECORD_STORE, ensure_ascii=False))
            .replace("__CHARS__", json.dumps(profiles, ensure_ascii=False))
            .replace("__REASON__", json.dumps(REASON_TEXT, ensure_ascii=False))
            .replace("__STAT__", json.dumps(dict(status_count), ensure_ascii=False))
            .replace("__QUERY_JS__", QUERY_JS))
    (OUT / "index.html").write_text(html, encoding="utf-8", newline="\n")

    # C3/C4 denominators: unique-record answer rows and the per-page/global fragment split
    uniq_answer_rows = sum(len(r["answers"]) + sum(len(ch["answers"]) for ch in r["children"])
                           for r in RECORD_STORE.values())
    parent_holder_keys = {(r["rec_key"], h["table"], h["record_id"], a["rule_key"], a["f"])
                          for r in RECORD_STORE.values() for h in [r] + r["children"] for a in h["answers"]}
    per_char_answers = sum(p["coverage"]["answers"] for p in profiles)
    seen_refs = collections.Counter()
    for p in profiles:
        for g in p["groups"]:
            for ref in g["records"]:
                seen_refs[ref["rec_key"]] += 1
    shared_with_answers = [k for k, v in seen_refs.items() if v > 1
                           and (len(RECORD_STORE[k]["answers"])
                                + sum(len(ch["answers"]) for ch in RECORD_STORE[k]["children"])) > 0]
    global_frags = {(RECORD_STORE[ref["rec_key"]]["table"],
                     RECORD_STORE[ref["rec_key"]]["record_id"],
                     f["t"])
                    for p in profiles for g in p["groups"] for ref in g["records"]
                    for f in RECORD_STORE[ref["rec_key"]]["fragments"]}
    global_frag_count = len(global_frags)
    per_page_frag_count = sum(p["coverage"]["descriptions_unique"] for p in profiles)

    summary = {
        "generated_by": "scripts/character_skills/profiles.py",
        "input": "output/character_skills/links/character_skills.jsonl",
        "rule_source": R.load_rule_metadata(),
        "characters": len(profiles),
        "unique_records": len(RECORD_STORE),
        "unique_rules_used": len(RULE_KEYS),
        "status_counts": dict(status_count),
        "status_definition": {
            "完整": ("本批已确认规则范围内：每条描述片段都有**真实答案**（关键词提示不算归属）"
                     "且无断链；真实答案包括基线、逐记录审定及冻结队列结构规则对应，不放宽未知片段要求"),
            "部分": "有规则答案，但存在未解释片段或断链",
            "仅未知": "该角色在已确认规则与本批已有答案范围内没有任何答案，全部字段与描述显示为未解释",
            "注意": "状态是「本批规则范围」口径，不等于全部战斗机制已解释；每页显式列出未解释片段、未解释字段与断链",
        },
        "totals": {
            "rule_answers": sum(p["coverage"]["answers"] for p in profiles),
            "rule_answers_in_reviewed_view": sum(p["coverage"]["answers_in_reviewed_view"] for p in profiles),
            "rule_answers_by_type_extrapolated": sum(p["coverage"]["answers_by_type_extrapolated"] for p in profiles),
            "rule_answers_unique_records": uniq_answer_rows,
            "rule_answers_parent_holder_keys": len(parent_holder_keys),
            "rule_answers_duplicate_rows_in_records": uniq_answer_rows - len(parent_holder_keys),
            "rule_answers_parent_holder_key_definition": "(父记录rec_key, 答案所属表, 所属记录ID, rule_key, 字段)去重；不含角色cid，不能称页求和或归一记录行求和",
            "rule_answers_shared_duplication": per_char_answers - uniq_answer_rows,
            "rule_answers_key": ("rule_answers 为按角色页引用求和；rule_answers_unique_records 为按唯一记录求和。"
                                 "差额来自被多角色共享、且带答案的记录被重复引用"),
            "annotations": sum(p["coverage"]["annotations"] for p in profiles),
            "descriptions_unique_records_page": per_page_frag_count,
            "descriptions_globally_unique": global_frag_count,
            "descriptions_internal_label": sum(p["coverage"]["descriptions_internal_label"] for p in profiles),
            "descriptions_key": ("descriptions 为按角色页引用求和；descriptions_unique_records_page 为页内按"
                                 "(表, 记录, 片段) 去重后求和；descriptions_globally_unique 为全局同键去重；"
                                 "descriptions_internal_label 为正文等于记录名的内部标签"),
            "shared_records": {
                "records_referenced_by_multiple_characters": sum(1 for v in seen_refs.values() if v > 1),
                "of_which_carry_answers": len(shared_with_answers),
            },
            "baseline_answers": sum(p["coverage"]["baseline_answers"] for p in profiles),
            "unexplained_fields": sum(p["coverage"]["unexplained_fields"] for p in profiles),
            "descriptions": sum(p["coverage"]["descriptions"] for p in profiles),
            "descriptions_attributed": sum(p["coverage"]["descriptions_attributed"] for p in profiles),
            "descriptions_with_hint": sum(p["coverage"]["descriptions_with_hint"] for p in profiles),
            "descriptions_from_baseline": sum(p["coverage"]["descriptions_from_baseline"] for p in profiles),
            "descriptions_reviewed_bindings": sum(p["coverage"]["descriptions_reviewed_bindings"] for p in profiles),
            "descriptions_unexplained": sum(p["coverage"]["descriptions_unexplained"] for p in profiles),
            "fragments_attributed_confirmed": sum(p["coverage"]["fragments_attributed_confirmed"] for p in profiles),
            "fragments_attributed_hint_only": sum(p["coverage"]["fragments_attributed_hint_only"] for p in profiles),
            "broken_links": sum(p["coverage"]["broken_links"] for p in profiles),
        },
        "outputs": {
            "rules_json": "rules.json",
            "records_jsonl": "records.jsonl",
            "profiles_jsonl": "profiles.jsonl",
            "answers_csv": "answers.csv",
            "descriptions_csv": "descriptions.csv",
            "characters_csv": "characters.csv",
            "html": "index.html",
        },
    }
    C.write_json(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:2400])


if __name__ == "__main__":
    main()
