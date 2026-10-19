"""Individually reviewed type8 prose correspondences, NOT a Japanese parser.

Only pinned APK skilllist records are eligible. Exact text is a change guard,
not proof: each selected fragment also has a reviewed semantic-to-effect mapping,
a unique local native consumer, and no sibling contribution on the same path.
Existing numeric answers and their evidence_scope are never upgraded or rewritten.
"""
from __future__ import annotations

import collections
import functools
import hashlib
import json
from pathlib import Path

import common as C

OUT = C.ROOT / "output/character_skills/description_bindings/type8"
PROFILES = C.ROOT / "output/character_skills/profiles"
STATUS = "REVIEWED_DESCRIPTION_BINDING"
STRENGTH = "逐记录人工语义对应＋原值与原生效果规则支持；不是机器码解析日文"
CONDITION = "本记录实际装载到持有者 BattleParam 时；type8 的 IsEnableAbility 无条件通过"
DURATION = "本项常时贡献：本记录处于装载状态期间；没有计时秒数，不代填 0 秒"
PATHS = {"/param1": ("attack", "攻击力", "攻击倍率"),
         "/param2": ("move", "移动速度", "移动速度乘数"),
         "/param3": ("defence", "受伤量", "受伤量倍率")}

# Each row was read as a whole record, including the other sentences and sub IDs.
# The mappings are editorial evidence, not deductions from a keyword hit count.
# For 304, the negative consequence explicitly says damage RECEIVED increases.
# For 349, the following guard-only sentence belongs to sub 350/type25; its
# neutral generic-defence branch distinguishes it from this type8 param3.
# For 30023600, sub 30023601/type51 is neutral on the attack path; its separate
# critical-rate sentence remains unknown, even though attack is now answerable.
REVIEWED = {
    301: ("5952256e6af813db02f6ff422408b9d3898d0fefc2312158faf220fff3953853",
          "戦闘時、移動速度が上昇する", "battle_move_up", {"/param2": 1}),
    305: ("968fe7c5434ee0f851d1a068d80e43d85c3a746f5d22eb6f42ba805100e7d93f",
          "戦闘時、移動速度が大きく上昇する", "battle_move_large_up", {"/param2": 1}),
    310: ("0bd137bfbf98b303e9ec8f00fdda26c71729d9e2c1ef7a526c39fe271f624536",
          "戦闘時、攻撃力が増加する", "battle_attack_up", {"/param1": 1}),
    314: ("47974289224d0b1427b30675d38dc9a876638116fd79a071fd877cb766b2040f",
          "戦闘時、受けるダメージが減少する", "battle_received_damage_down", {"/param3": -1}),
    316: ("8fe46fd984ce4d65735f9ecd0e07e602869deedaae5c05b8acfdc3413752be86",
          "戦闘時、攻撃力と移動速度が上昇する", "battle_attack_move_up", {"/param1": 1, "/param2": 1}),
    373: ("51433d71f0f3419c4b1c229d25c2659993a575e14ee85c505e67d8074bbb3b0f",
          "戦闘時、攻撃力と移動速度が上昇する", "battle_attack_move_up", {"/param1": 1, "/param2": 1}),
    304: ("2afe6ebc8d3756385eb3f661677b5d833fabf1bf2a6d06a2cd82b16e4c7bf64c",
          "死に場所を探して無謀な戦い方をするせいで、攻撃力は増加するが、受けるダメージも増加する",
          "attack_up_received_damage_up", {"/param1": 1, "/param3": 1}),
    349: ("feac605ed7b96db99239f856c843b5e8036a853831084808e3d5cd4103508943",
          "敵から受けるダメージが減少する", "received_damage_down_separate_guard", {"/param3": -1}),
    28045: ("e3bf7bf483f34e53073ce9cf516955a515300e4f0210d0f1a6964bff73346b4c",
            "ちょっと休ませておくれ！移動速度が下がる", "move_down", {"/param2": -1}),
    30023600: ("2917ce7c776ba75df8c80ef66b335aebe7c3f78d3be14e30a3345d47e6426971",
               "攻撃力が上がる", "attack_up_separate_critical", {"/param1": 1}),
}

# P3B1's ten records were independently reviewed. P3B2 is a separate fixed-record
# editorial addition, pending its own independent review; it is not extrapolation
# from the matching sentence. No binding behaviour or old evidence_scope changes.
P3B1_IDS = frozenset(REVIEWED)
P3B2_REVIEWED = {
    302: ("d63f3e723d44ac937ebc42c4a7486d282e60939b91036a1a3a3f56e5e5bb7550",
          "戦闘時、移動速度が上昇する", "battle_move_up", {"/param2": 1}),
    309: ("2749333b8e9dbbcd724c39f595576979534566117fc1e117d1b733925c35d5c7",
          "戦闘時、移動速度が上昇する", "battle_move_up", {"/param2": 1}),
    312: ("6883a0f9d9d777d40ef3aa1c9b7a9aa4984bcad4b15950855ed5c143780387f8",
          "戦闘時、移動速度が上昇する", "battle_move_up", {"/param2": 1}),
    317: ("14eff7f2c81431e3167b73b8c90581b1be4e7eb6610ab0307678df09c18ecf7a",
          "戦闘時、移動速度が上昇する", "battle_move_up", {"/param2": 1}),
    318: ("687868cd06a97c2d5fba37861dd492dab76fd149ab47e2bb77106762a2f0dc5b",
          "戦闘時、移動速度が上昇する", "battle_move_up", {"/param2": 1}),
    322: ("52bb371acb953fc42db44ad620ba669df0e8d53a1e064715118e430c4ecc2199",
          "戦闘時、移動速度が上昇する", "battle_move_up", {"/param2": 1}),
    353: ("b9336853062fcea2c955fd13c463519f35e04e4d1243794d426197a754350ac0",
          "戦闘時、移動速度が大きく上昇する", "battle_move_large_up", {"/param2": 1}),
    357: ("9778c60d3759f110771de064cd062eab7cb6aef18e9b40be5153458b51eb9db7",
          "戦闘時、移動速度が上昇する", "battle_move_up", {"/param2": 1}),
    368: ("f1733bbb09742d8657df233d5f72ddeee3ca22d722d7d12d6ec59abae5caedee",
          "戦闘時、攻撃力が増加する", "battle_attack_up", {"/param1": 1}),
    372: ("743fb1b8d1a84380f3f1be394778140d9324d55ed590fc3c9d831a244accef20",
          "戦闘時、攻撃力が増加する", "battle_attack_up", {"/param1": 1}),
    376: ("a3fdce5173765d9a7f7ea27e580d9ff62fd7d7094b5fad2a1acb7ceb7c2fb1e0",
          "戦闘時、攻撃力と移動速度が上昇する", "battle_attack_move_up", {"/param1": 1, "/param2": 1}),
}
REVIEWED.update(P3B2_REVIEWED)

EXCLUSION_NOTES = {
    345: "sub346/type1会走同一移动消费者；即使param2=1，本批不新增条件子效果的值中性推理，保留提示",
    347: "后文有战士/魔法使光环及持有者排除；sub348/type20在自身移动派发中性不足以证明跨对象路径边界，保留提示",
    424: "sub425/426/427/type67进入同一攻击路径；即使param1=1，本批不新增条件子效果的值中性推理，保留提示",
    30124100: "sub30124101/type56敌阵攻防另有对象/位置条件；普通攻击派发中性不足以排除其他消费者，保留提示",
    340: "同记录还有抗倒地句；不能用攻/移/受伤三槽确认整个复合描述",
    335: "同句有最大HP与攻击、受伤量；本批不证明最大HP槽，也不把局部答案当整句已覆盖",
    28034: "明确写魔法使い的攻击；对象不是可直接认作自身的无条件句",
    30022100: "只可考虑无条件移动句；一定距離/一定時間的攻击句不能绑到中性 param1=1；本记录未纳入",
    42013050: "后文明确絆所属装载条件；其原生装载门槛未在本批逐项核实",
    40422700: "CACHE源；HP门槛及后续毒/暗闇多效果不在逐记录试点范围",
    364: "受伤量增加与回复同句；param3可有局部答案，但本批未审定完整片段的回复对应",
}


@functools.lru_cache(maxsize=1)
def dispatch():
    return C.load_json(C.ROOT / "output/character_skills/skilllist_types/dispatch_map.json")


def is_neutral(path, effect_type):
    if not isinstance(effect_type, int):
        return False
    data = dispatch()["types"][path]
    return any(lo <= effect_type <= hi for lo, hi in data["neutral_ranges"])


def bind_type8(entry, fragment, answers, children):
    """Return (binding, rejection); non-type8 callers should skip this function."""
    rec = entry.get("record") or {}
    if entry.get("table") != "skilllist" or rec.get("ability") != 8:
        return None, "OUTSIDE_SKILLLIST_TYPE8"
    # No cache fallback / ID collision / text-template extrapolation is allowed.
    if entry.get("layer") != "APK":
        return None, "SOURCE_LAYER_NOT_REVIEWED"
    spec = REVIEWED.get(entry.get("reference_id"))
    if spec is None:
        return None, "RECORD_NOT_IN_REVIEWED_PILOT"
    expected_sha, expected_fragment, template, fields = spec
    blob = json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(blob).hexdigest() != expected_sha:
        return None, "REVIEWED_RECORD_CHANGED"
    if fragment != expected_fragment:
        return None, "FRAGMENT_NOT_REVIEWED"
    source = entry.get("source") or {}
    if source.get("raw_record_sha256") != expected_sha or source.get("layer") != "APK":
        return None, "SOURCE_STAMP_MISMATCH"
    declared_subs = set(rec.get("sub") or [])
    resolved_subs = {ch["record_id"] for ch in children if ch.get("link_kind") == "sub_effect"}
    if declared_subs != resolved_subs:
        return None, "UNRESOLVED_SUBEFFECT"
    bound = []
    for field, sign in fields.items():
        path, meaning, kind = PATHS[field]
        native = dispatch()["types"][path]["entries"]["8"]
        if (native["slots"] != [field[1:]] or not native["gated_by_isenable"]
                or not native["reaches_accumulate_op"]):
            return None, "NATIVE_RULE_NOT_AS_REVIEWED"
        # Unknown or contributing sibling branches cannot be assumed harmless.
        if any(ch.get("table") != "skilllist" or not is_neutral(path, ch.get("effect_type"))
               for ch in children):
            return None, "SIBLING_PATH_NOT_PROVEN_NEUTRAL"
        hits = [a for a in answers if a["f"] == field and a.get("kind") == kind
                and a.get("status") == "CONFIRMED_NUMERIC"]
        if len(hits) != 1 or hits[0]["raw"] != rec.get(field[1:]):
            return None, "LOCAL_NUMERIC_ANSWER_NOT_UNIQUE"
        a = hits[0]
        if (a["raw"] - 1) * sign <= 0:
            return None, "DIRECTION_DOES_NOT_MATCH_RAW"
        bound.append({"f": field, "raw": a["raw"], "value": a["value"],
                      "kind": a["kind"], "unit": a["unit"], "status": a["status"],
                      "evidence_scope": a["scope"], "rule_key": a["rule_key"],
                      "table": "skilllist", "record_id": entry["reference_id"],
                      "semantic_effect": meaning,
                      "direction": "原值大于1" if sign == 1 else "原值小于1",
                      "native_path": path, "native": native})
    return {"template_id": template, "strength": STRENGTH,
            "status": "已确认（限定本记录的描述对应）", "target": "持有该能力的角色自身",
            "condition": CONDITION, "duration": DURATION,
            "rationale": ("完整片段的每个数值效果逐项对应本记录 type8 的唯一原生槽；"
                          "无其他同路径子效果；相邻的专属说明、暴击或格挡句不并入本片段。"
                          "双效果句分别保留两个槽，不把两个百分比合并。"),
            "source": source, "fields": bound,
            "siblings": [{"record_id": ch["record_id"], "effect_type": ch["effect_type"],
                          "neutral_on_bound_paths": [PATHS[f][0] for f in fields]}
                         for ch in children],
            "native_evidence": "output/character_skills/skilllist_types/dispatch_map.json",
            "eligibility_evidence": "output/character_skills/skilllist_types/native_checks.json#eligibility_types_8_26_are_unconditional",
            "limits": "只解释本项局部贡献；不证明当前账号解锁/装载，也不计算最终战斗数值；param0/param4仍未知"}, None


def main():
    C.enable_utf8_console()
    records = {r["rec_key"]: r for r in (json.loads(l) for l in (PROFILES / "records.jsonl").open(encoding="utf-8"))}
    chars = [json.loads(l) for l in (PROFILES / "profiles.jsonl").open(encoding="utf-8")]
    uses = collections.defaultdict(list)
    for p in chars:
        for g in p["groups"]:
            for ref in g["records"]:
                uses[ref["rec_key"]].append({"cid": p["cid"], "group": g["group"],
                    "reference_field": ref["reference_field"], "character_source": p["charainfo_source"]})
    accepted, excluded = [], []
    for r in records.values():
        if r["table"] != "skilllist" or r["effect_type"] != 8:
            continue
        for f in r["fragments"]:
            base = {"rec_key": r["rec_key"], "source": r["source"], "fragment": f["t"],
                    "characters": uses[r["rec_key"]], "attribution_status": f["status"]}
            if f.get("binding"):
                accepted.append(dict(base, binding=f["binding"]))
            else:
                excluded.append(dict(base, reason=f.get("binding_rejection"),
                                     review_note=EXCLUSION_NOTES.get(r["record_id"], "不在逐记录审定范围；维持原状态，不从文本模板外推"),
                                     retained_candidates=f["cands"]))
    C.write_jsonl(OUT / "accepted.jsonl", accepted)
    C.write_jsonl(OUT / "excluded.jsonl", excluded)
    summary = {"generated_by": "scripts/character_skills/description_bindings.py",
               "strength": STRENGTH, "reviewed_record_limit": len(REVIEWED),
               "batch_scopes": {
                   "P3B1": {"records": len(P3B1_IDS), "independent_review": "带明确限制通过；仅历史十条"},
                   "P3B2": {"records": len(P3B2_REVIEWED), "independent_review": "待独立审查；不借用P3B1通过结论"}},
               "numeric_field_answers_added": 0,
               "bound_fragments_unique_records": len(accepted),
               "bound_fragments_page_references": sum(len(x["characters"]) for x in accepted),
               "bound_effects_unique_records": sum(len(x["binding"]["fields"]) for x in accepted),
               "bound_effects_page_references": sum(len(x["characters"])*len(x["binding"]["fields"]) for x in accepted),
               "affected_characters": len({p["cid"] for x in accepted for p in x["characters"]}),
               "excluded_fragments_unique_records": len(excluded),
               "excluded_by_reason": dict(collections.Counter(x["reason"] for x in excluded)),
               "source_layers_accepted": dict(collections.Counter(x["source"]["layer"] for x in accepted)),
               "native_image_sha256": dispatch()["native_sha256"],
               "metadata_sha256": dispatch()["metadata_sha256"],
               "answer_scope_unchanged": "IN_REVIEWED_VIEW / BY_TYPE_EXTRAPOLATED only; binding status is separate"}
    C.write_json(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
