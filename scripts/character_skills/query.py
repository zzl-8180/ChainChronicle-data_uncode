"""Read-only character query over the generated P1 profiles.

Usage (from the project root):

    .venv\\Scripts\\python.exe -B scripts/character_skills/query.py --cid 30236
    .venv\\Scripts\\python.exe -B scripts/character_skills/query.py --name チーカ
    .venv\\Scripts\\python.exe -B scripts/character_skills/query.py --cid 30236 --json
    .venv\\Scripts\\python.exe -B scripts/character_skills/query.py --list-gaps

A missing cid, a name that matches nothing and a skill whose reference is broken
all return an explicit status instead of an error or an empty page.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common as C  # noqa: E402

PROFILES = C.ROOT / "output" / "character_skills" / "profiles"


def load():
    chars = [json.loads(l) for l in (PROFILES / "profiles.jsonl").open(encoding="utf-8")]
    recs = {r["rec_key"]: r for r in (json.loads(l) for l in (PROFILES / "records.jsonl").open(encoding="utf-8"))}
    rules = json.loads((PROFILES / "rules.json").read_text(encoding="utf-8"))
    return chars, recs, rules


def find(chars, cid=None, name=None):
    if cid is not None:
        for c in chars:
            if c["cid"] == cid:
                return [c]
        return []
    needle = (name or "").casefold()
    return [c for c in chars if needle and (needle in (c.get("name") or "").casefold()
                                            or needle in (c.get("title") or "").casefold())]


def render(c: dict, recs: dict, rules: dict) -> str:
    cov = c["coverage"]
    out = [f"cid {c['cid']}　{c.get('name')}　{c.get('title') or ''}　"
           f"稀有度 {c.get('rarity')}　"
           + (c.get("job_name") or ("职业：名册缺值" if c.get("job_name_raw") == "未知" else "职业：-"))
           + f"　角色记录来源 {c.get('charainfo_layer')}",
           f"状态 {c['status']}（{c['status_scope']}）　技能记录 {cov['records']}"
           f"　已有逐描述答案 {cov['baseline_answers']}",
           f"描述片段 {cov['descriptions']}（本页求和；去重 {cov['descriptions_unique']}）"
           f"　有归属 {cov['descriptions_attributed']}＝已有答案 {cov['descriptions_from_baseline']}"
           f"＋仅关键词提示 {cov['descriptions_with_hint']}／未解释 {cov['descriptions_unexplained']}"
           f"　未解释字段 {cov['unexplained_fields']}　必杀技类型标注 {cov['annotations']}"
           f"　断链 {cov['broken_links']}",
           f"规则答案 {cov['answers']}（已逐条评审 {cov['answers_in_reviewed_view']}"
           f"／按类型套用 {cov['answers_by_type_extrapolated']}）"]
    if c.get("charainfo_source"):
        src = c["charainfo_source"]
        out.append(f"角色记录来源定位：{src.get('record_key')}"
                   + (f"　字节 {src.get('byte_begin')}–{src.get('byte_end_exclusive')}"
                      if src.get("byte_begin") is not None else ""))
    out.append("")
    REASON_ZH = {"NO_RULE_FOR_TYPE": "该表・该类型下的这个字段没有本批已确认规则",
                 "NON_FINITE_VALUE": "原值不是有限数值",
                 "CHARAINFO_EQUIVALENCE_UNPROVEN":
                     "该 charainfo 记录的原值不是战斗执行值，或没有可对齐的执行侧记录，"
                     "因此不把 boss 规则迁到这里（X1／X0：自身 pattern 可解析，执行取 pattern 侧的 bossskill，"
                     "本记录 skillparam 是未执行的副本；NOT_AMONG：自身 pattern 的类型集合不含 skillid[0]；"
                     "路径见 output/character_skills/cp_paths/，两侧原值见 charainfo_params/）"}
    for g in c["groups"]:
        if not g["records"] and not g["unresolved"] and not g.get("annotations"):
            continue
        out.append(f"== {g['label']} ==")
        for a in g.get("annotations") or []:
            out.append(f"  [类型标注] {a['slot']} = {a['raw_value']} → {a['interpretation']}")
            out.append(f"    本角色自身必杀技效果类型：{a['own_pattern_effect_types'] or '（无 pattern）'}"
                       f"　判定：{a['verdict']}")
            for r2 in a.get("same_number_unrelated_records") or []:
                out.append(f"    同号无关记录：{r2['table']} #{r2['record_id']} {r2.get('name') or ''}　{r2['note']}")
            for ev in a.get("evidence") or []:
                out.append(f"    依据：{ev}")
            out.append(f"    说明：{a['note']}")
        for u in g["unresolved"]:
            alt = "；同号候选：" + "、".join(
                f"{a['table']} #{a['record_id']}" + (f" {a.get('sname')}" if a.get("sname") else "")
                for a in (u.get("alternative_candidates") or [])) if u.get("alternative_candidates") else ""
            out.append(f"  [断链] {u.get('reference_field')} -> {u.get('reference_id')}"
                       f"（期望 {u.get('expected_table')}：{u.get('expected_namespace')}）{u.get('note')}{alt}")
        for ref in g["records"]:
            r = recs.get(ref["rec_key"])
            if not r:
                out.append(f"  [缺失记录] {ref['rec_key']}")
                continue
            head = (f"  {r.get('name') or r.get('namespace') or r.get('table')} "
                    f"[{r.get('table')} #{r.get('record_id')}"
                    + (f" {r.get('type_field')}={r.get('effect_type')}" if r.get("effect_type") is not None else "")
                    + (f" {r.get('layer')}" if r.get("layer") else "") + "]")
            out.append(head)
            if ref.get("ambiguous"):
                out.append("    （槽位歧义：同号另一命名空间仅登记候选，未合并）")
            if ref.get("link_status"):
                out.append(f"    关联状态：{ref['link_status']}")
            if r.get("source", {}).get("record_key"):
                s = r["source"]
                out.append(f"    来源：{s['record_key']}"
                           + (f"　字节 {s.get('byte_begin')}–{s.get('byte_end_exclusive')}"
                              if s.get("byte_begin") is not None else ""))
            if r.get("text"):
                out.append("    原文：" + r["text"].replace("\n", " / ")[:300])
            for a in r["answers"]:
                rule = rules.get(a["rule_key"]) or {}
                scope = ("已逐条评审" if a.get("scope") == "IN_REVIEWED_VIEW" else "按类型套用")
                out.append(f"      {a['f']} = {json.dumps(a['raw'], ensure_ascii=False)} → {a.get('value')}"
                           f"　[{a.get('kind')}／{a.get('unit')}]　{a.get('status')}／证据范围={scope}"
                           + (f"　对象={rule.get('target')}" if rule.get("target") else ""))
                if a.get("note"):
                    out.append(f"        注：{a['note']}")
            for u in r["unexplained"]:
                out.append(f"      {u['f']} = {json.dumps(u.get('raw'), ensure_ascii=False)} → 未解释"
                           f"（{REASON_ZH.get(u['reason'], u['reason'])}）")
            for ch in r["children"]:
                out.append(f"    子记录 [{ch['table']} #{ch['record_id']} {ch['type_field']}={ch['effect_type']}]")
                for a in ch["answers"]:
                    rule = rules.get(a["rule_key"]) or {}
                    scope = ("已逐条评审" if a.get("scope") == "IN_REVIEWED_VIEW" else "按类型套用")
                    out.append(f"      {a['f']} = {json.dumps(a['raw'], ensure_ascii=False)} → {a.get('value')}"
                               f"　[{a.get('kind')}／{a.get('unit')}]　{a.get('status')}／证据范围={scope}"
                               + (f"　对象={rule.get('target')}" if rule.get("target") else ""))
                for u in ch["unexplained"]:
                    out.append(f"      {u['f']} = {json.dumps(u.get('raw'), ensure_ascii=False)} → 未解释"
                               f"（{REASON_ZH.get(u['reason'], u['reason'])}）")
        out.append("")
    if c.get("baseline"):
        out.append(f"== 已有逐描述答案（{len(c['baseline'])} 条，cid30236 基线） ==")
        for b in c["baseline"]:
            out.append(f"  {b.get('effect_id')}　{b.get('description_fragment_ja')}"
                       f" → {b.get('readable_value')}　[{b.get('quantity_kind')}／{b.get('unit')}]")
        out.append("")
    return "\n".join(out)


def main():
    C.enable_utf8_console()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cid", type=int)
    g.add_argument("--name")
    g.add_argument("--list-gaps", action="store_true",
                   help="打印缺口队列摘要（output/character_skills/gaps/）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if args.list_gaps:
        summary = json.loads((C.ROOT / "output" / "character_skills" / "gaps" / "gap_queue.json")
                             .read_text(encoding="utf-8"))
        print(json.dumps({"counts": summary["counts"], "policy": summary["policy"],
                          "top_field_gaps": summary["field_gaps"][:15],
                          "type_gaps": [{k: v for k, v in r.items() if k != "candidate_leads"}
                                        for r in summary["type_gaps"][:15]],
                          "broken_links": summary["broken_links"]},
                         ensure_ascii=False, indent=2))
        return

    chars, recs, rules = load()
    hits = find(chars, args.cid, args.name)
    if not hits:
        payload = {
            "status": "NOT_FOUND_IN_CURRENT_ROSTER",
            "query": {"cid": args.cid, "name": args.name},
            "roster_characters": len(chars),
            "note": ("该 cid／名称不在本批已处理的可玩名册（2236）内；不是脚本错误，也不是空页面。"
                     "可先用 --list-gaps 或 output/character_skills/scope_diff/ 确认范围。"),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else
              f"[NOT_FOUND_IN_CURRENT_ROSTER] cid={args.cid} name={args.name}\n"
              f"{payload['note']}\n名册角色数：{len(chars)}")
        return
    if args.json:
        print(json.dumps({"status": "FOUND", "matches": len(hits),
                          "characters": [dict(c, materialised_records={
                              ref["rec_key"]: recs.get(ref["rec_key"])
                              for g in c["groups"] for ref in g["records"]}) for c in hits]},
                         ensure_ascii=False, indent=2))
        return
    print(f"[FOUND] 匹配到 {len(hits)} 个角色\n")
    for c in hits:
        print(render(c, recs, rules))


if __name__ == "__main__":
    main()
