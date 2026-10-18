"""Item 2 - character -> skill-group association for the whole playable roster.

Every skill reference found in a ``charainfo`` record is resolved inside its own
namespace only (ordinary ``skilllist``, ``heroicskilllist``, ``bossskill`` /
``bosspattern``, ``denju``, support tables). The cache snapshot is preferred per
ID; the APK built-in master is used only when that ID is absent from the cache.
Same-numbered IDs in different namespaces are never merged, and same-named
characters with different cids are never merged.

Broken links are kept and reported, never dropped silently.

Note on ``charainfo.skillid[0]`` -- it is the special move's **effect type**, not a
skill reference, and it is therefore not resolved to any record:

* among the 1307 roster characters that carry a ``patternN``, 1287 have
  ``skillid[0]`` equal to one of the ``skillid0`` values of their *own* pattern's
  ``bossskill`` records, and 1110/1286 of those have ``charainfo.skillparam*``
  value-identical to the matching ``bossskill``'s ``skillparam*``;
* the 98 same-numbered ``denju`` rows are records of *another* character
  (``denju#v.sname`` equals the ``skillname`` of the character whose cid is ``v``),
  and the same-numbered entries in the APK skilllist small-id block are a legacy
  ability pool whose prose names yet another character.

The slot is therefore reported as a type annotation (no record, no answer, no broken
link), listing the value, the character's own pattern effect types and a verdict; the
same-numbered records of the other namespaces are noted as unrelated coincidences.
The character's own ``skillparam*`` / ``skillflag*`` fields stay on the character
record and are still shown as unexplained (no ``charainfo`` rule exists).

``denju`` (P2 batch 7) is a *reference* row as well: it carries the taught skill's
name/text/cost and ``patternid0..5`` but no parameter slots, so its effects are
reached through ``denju.patternidN -> bosspattern -> bossskill`` -- the same helper the
character's own ``patternN`` uses. Association is by ``denju.denju_id == cid`` (measured
on 1500/1504 rows), never by name; rows whose ``sname`` differs from the character's
``skillname`` are linked by id only and say so in ``link_status``.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common as C  # noqa: E402

OUT = C.ROOT / "output" / "character_skills" / "links"

PATTERN_FIELDS = [f"pattern{i}" for i in range(9)]

GROUP_LABELS = {
    "special_move": "必杀技",
    "ability": "能力",
    "sa": "SA(能力旗标)",
    "sympathy": "共鸣",
    "leader": "Leader能力",
    "class": "Class能力",
    "extra": "Extra能力",
    "passive": "PASSIVE",
    "bond": "羁绊(支援)",
    "heroic": "英雄技",
    "slot0": "必杀技效果类型(skillid[0])",
    "denju": "传授必杀技(denju)",
    "denju_lb": "传授突破(denju_limit_break_info)",
    "crossworld": "CrossWorld",
}


class Linker:
    def __init__(self):
        self.t = C.Tables()
        self.cache_chara = {r["cid"]: r for r in C.cache_rows("charainfo")}
        self.apk_chara = {r["cid"]: r for r in C.apk_rows("charainfo")}
        self.sympathy = {r["_id"]: r for r in C.cache_rows("sympathy_skilllist")}
        self.leader = {}
        for r in C.cache_rows("leaderabilityinfo"):
            self.leader.setdefault(r.get("cid"), []).append(r)
        self.job = list(C.cache_rows("jobabilityinfo"))
        self.extra = {r["cid"]: r for r in C.cache_rows("extraabilitylist")}
        self.passive = {r["cid"]: r for r in C.cache_rows("passivelist")}
        self.support = {r["ability_id"]: r for r in C.cache_rows("supporterskill")}
        self.crossworld = {r["_id"]: r for r in C.cache_rows("crossworldabilitylist")}
        self.heroic = C.cache_rows("heroicskilllist")
        self.denju_lb = {r["cid"]: r for r in C.cache_rows("denju_lb")} if "denju_lb" in C.CACHE_TABLES else {}
        if not self.denju_lb:
            raw = C.load_json(C.DECODED / "denju_lblist.data5.json.raw")
            self.denju_lb = {r["cid"]: r for r in raw["denju_limit_break_info"]}

        # value -> cids that literally carry that value in a skill/pattern slot
        self.value_owner = collections.defaultdict(set)
        for cid, rec in list(self.cache_chara.items()) + list(self.apk_chara.items()):
            vals = list(rec.get("skillid") or [])
            vals += [rec.get(f) for f in PATTERN_FIELDS]
            for v in vals:
                if isinstance(v, int) and v:
                    self.value_owner[v].add(cid)

        self.heroic_links = self._build_heroic_links()

        self.job_by_cid = collections.defaultdict(list)
        for j in self.job:
            for cid in j.get("cids") or []:
                self.job_by_cid[cid].append(j)

        # denju_id == cid observation (kept as a measured statistic, not a rule)
        den = C.cache_rows("denju")
        allc = {**self.apk_chara, **self.cache_chara}
        self.denju_id_is_cid = sum(1 for d in den if d["denju_id"] in allc)
        self.denju_id_name_match = sum(
            1 for d in den if (allc.get(d["denju_id"]) or {}).get("skillname") == d["sname"])
        self.denju_total = len(den)

    # -- helpers -----------------------------------------------------------
    def _resolve(self, table_key, ident, *, ref_field, refers_to):
        if ident in (0, None):
            return None
        rec, layer = self.t(table_key).get(ident)
        if rec is None:
            return {
                "resolved": False,
                "reference_field": ref_field,
                "reference_id": ident,
                "expected_table": table_key,
                "expected_namespace": C.CACHE_TABLES[table_key][0],
                "refers_to": refers_to,
                "apk_fallback_available": table_key in C.APK_TABLES,
                "note": (f"{table_key} 命名空间内（缓存与 APK 回退均）无此 ID；保留断链"
                         if table_key in C.APK_TABLES else
                         f"{table_key} 命名空间内（缓存）无此 ID；APK 主表未导出该表，回退不可用；保留断链"),
            }
        return {
            "resolved": True,
            "reference_field": ref_field,
            "reference_id": ident,
            "table": table_key,
            "namespace": C.CACHE_TABLES[table_key][0],
            "layer": layer,
            "refers_to": refers_to,
            "record": rec,
            "source": C.location(table_key, ident, layer, rec),
        }

    def _build_heroic_links(self):
        links = collections.defaultdict(list)
        for h in self.heroic:
            hid = h["skillid"]
            pats = [h.get(k) for k in ("boss_pattern", "boss_pattern2", "boss_pattern3") if h.get(k)]
            confirmed = sorted({c for p in pats for c in self.value_owner.get(p, ())})
            derived = sorted({(p // 100) % 100000 for p in pats})
            links[hid] = {
                "heroic_id": hid,
                "boss_patterns": pats,
                "confirmed_cids": confirmed,
                "derived_cids": derived,
                "link_status": "CONFIRMED_DIRECT_REF" if confirmed else "INFERRED_FROM_ID_PATTERN",
            }
        return links

    # -- main --------------------------------------------------------------
    def link(self, cid):
        rec = self.cache_chara.get(cid)
        layer = "CACHE"
        if rec is None:
            rec = self.apk_chara.get(cid)
            layer = "APK"
        if rec is None:
            return {
                "cid": cid, "charainfo_layer": None, "groups": [],
                "unresolved": [{"resolved": False, "reference_field": "charainfo", "reference_id": cid,
                                "expected_table": "charainfo", "note": "缓存与 APK 均无该 cid 的角色记录"}],
                "counts": {"references": 1, "resolved": 0, "unresolved": 1, "records": 0,
                           "sub_effect_refs": 0},
            }

        groups = collections.OrderedDict()
        unresolved = []
        stats = collections.Counter()

        def bucket(key):
            if key not in groups:
                groups[key] = {"group": key, "label": GROUP_LABELS[key], "records": [], "unresolved": [],
                               "namespace_notes": [], "annotations": []}
            return groups[key]

        def count(sub):
            if sub is None:
                return False
            stats["references"] += 1
            if sub.get("resolved"):
                stats["resolved"] += 1
            else:
                stats["unresolved"] += 1
            return True

        def add(key, entry, ref_field, refers_to, extra=None):
            if entry is None:
                return
            count(entry)
            if extra:
                entry.update(extra)
            if entry["resolved"]:
                bucket(key)["records"].append(entry)
            else:
                bucket(key)["unresolved"].append(entry)
                unresolved.append(entry)

        def resolve_pattern(v, ref_field, refers_to, bucket_key):
            """bosspattern -> its bossskill list (+ each skill's s_ability cross-ref).

            The pattern record is the *container* of the effect parameters: the
            effect type is ``bossskill.skillid0`` and the slots are
            ``bossskill.skillparamN``. Both the character's own ``patternN`` and the
            ``denju.patternidN`` of the taught-skill row go through this helper, so
            the two paths cannot drift apart (P2 batch 7).
            """
            pat = self._resolve("bosspattern", v, ref_field=ref_field, refers_to=refers_to)
            if pat is None:
                return None
            if pat["resolved"]:
                prefs = []
                for k in sorted(kk for kk in pat["record"] if kk.startswith("skillid")):
                    bv = pat["record"][k]
                    if not bv:
                        continue
                    sub = self._resolve("bossskill", bv, ref_field=f"bosspattern[{v}].{k}",
                                        refers_to="Boss/必杀 skill")
                    count(sub)
                    if sub and not sub["resolved"]:
                        unresolved.append(sub)
                        bucket(bucket_key)["unresolved"].append(sub)
                    prefs.append({"slot": k, "reference_id": bv,
                                  "resolved": bool(sub and sub["resolved"]),
                                  **(sub or {})})
                pat["boss_skill_refs"] = prefs
                # Boss skill records carry their own ability id in `s_ability`;
                # that id lives in the ordinary skilllist namespace. Recorded as an
                # explicit cross-reference of the field, never as a same-number merge.
                sa_refs = []
                for sub in prefs:
                    sub_rec = sub.get("record")
                    if not sub_rec or not sub_rec.get("s_ability"):
                        continue
                    r2 = self._resolve("skilllist", sub_rec["s_ability"],
                                       ref_field=f"bossskill[{sub['reference_id']}].s_ability",
                                       refers_to="Boss skill.s_ability → 普通 skilllist（SA/超过能力）")
                    count(r2)
                    if r2 and not r2["resolved"]:
                        unresolved.append(r2)
                        bucket(bucket_key)["unresolved"].append(r2)
                    sa_refs.append({"parent_skill": sub["reference_id"], **(r2 or {})})
                pat["sa_ability_refs"] = sa_refs
            return pat

        # 1. slot 0 of skillid[] is the special move's effect type, not a reference.
        #    Recorded as an annotation: no record, no answer, no broken link.
        skillid = rec.get("skillid") or []
        v0 = skillid[0] if skillid else 0
        own_types = []
        for f in PATTERN_FIELDS:
            pv = rec.get(f)
            if not pv:
                continue
            prec, _ = self.t("bosspattern").get(pv)
            if not prec:
                continue
            for k in sorted(kk for kk in prec if kk.startswith("skillid")):
                bv = prec.get(k)
                if not bv:
                    continue
                brec, _ = self.t("bossskill").get(bv)
                if brec and brec.get("skillid0") is not None and brec["skillid0"] not in own_types:
                    own_types.append(brec["skillid0"])
        if own_types:
            verdict = ("MATCHES_OWN_PATTERN_EFFECT_TYPE" if v0 in own_types
                       else "NOT_AMONG_OWN_PATTERN_TYPES")
        elif v0:
            verdict = "TYPE_ONLY_NO_PATTERN_IN_CACHE_OR_APK"
        else:
            verdict = "TYPE_ZERO_UNSET"
        same_number = []
        if v0:
            for tbl, note in (("skilllist", "同号 skilllist 小号段记录；其正文指向别的角色，与本槽位无关"),
                              ("denju", "同号 denju 行（另一张表，键为 denju_id）；denju_id 与 cid 高度重合，"
                              "1500/1504 行落在角色表、其中 1276 行名称与该 cid 的 skillname 一致，"
                              "但并非每行都能对上属主，因此该同号行只作无关记录登记，不据此推断归属")):
                r2, l2 = self.t(tbl).get(v0)
                if r2 is not None:
                    same_number.append({"table": tbl, "layer": l2, "record_id": v0,
                                        "name": r2.get("name") or r2.get("sname"), "note": note})
        # The note must follow *this* character's verdict: the previous single sentence
        # ("此处只是类型槽原值为 0") was wrong for the other three verdicts. P2-9 rewrote it
        # per verdict, together with the execution-side verdict of the equivalence gate.
        note_by_verdict = {
            "TYPE_ZERO_UNSET": ("该角色有必杀技名与说明文本，此处只是类型槽原值为 0（旧类型/未设置）；"
                                "该必杀技的参数在角色记录自身的 skillparam0..9／skillflag 上，"
                                "按类型 0（Exec_ATTACK_NORMAL）的规则给答案。"),
            "TYPE_ONLY_NO_PATTERN_IN_CACHE_OR_APK": (
                "该角色有必杀技名与说明文本，但缓存与 APK 里都找不到它的 pattern。"
                "按 P2 第 9 批的**执行侧裁决**（F0 类）：战斗执行用角色记录自身的 skillparam0..9／skillflag"
                "（CharaParamToBossSkill 0x13aa390 构造执行用 BattleBossSkill → _CreateExecSkillList 的 pattern==0 分支），"
                "因此已按 skillid[0] 的类型规则出数值答案；若当次必杀由传授链（denju）或英雄技 pattern 承担，"
                "实际执行取那一侧（页面相应分组已给）。路径证据见 output/character_skills/cp_paths/。"),
            "MATCHES_OWN_PATTERN_EFFECT_TYPE": (
                "该角色的必杀技由自身 pattern 承载（该 pattern 的 bossskill 已作为子记录列出并出答案）。"
                "按 P2 第 9 批的执行侧裁决：**战斗执行取 pattern（boss 主表）侧的 bossskill**；"
                "角色记录自身的 skillparam0..9／skillflag 是另一份副本，两侧数值是否相同见 "
                "output/character_skills/charainfo_params/（E0/E1/E2 相同；X0/X1 不同，此时不给 charainfo 侧数值答案）。"),
            "NOT_AMONG_OWN_PATTERN_TYPES": (
                "该角色的 skillid[0] 不在自身 pattern 的类型集合内（P2 第 1 批起登记为 NOT_AMONG 疑点）。"
                "按 P2 第 9 批的执行侧裁决：**战斗执行取 pattern 侧的 bossskill**，角色记录自身的 "
                "skillparam0..9 副本不参与执行，因此该槽位对执行没有作用（逐人定性见 "
                "output/character_skills/cp_paths/notamong_exceptions.jsonl）。"),
        }
        annotation = {
            "slot": "skillid[0]",
            "raw_value": v0,
            "interpretation": "必杀技效果类型（与 bossskill.skillid0 同域），不是技能引用",
            "verdict": verdict,
            "own_pattern_effect_types": sorted(own_types),
            "same_number_unrelated_records": same_number,
            "evidence": [
                "本项目复算：1307 个带 pattern 的角色中 1287 个 skillid[0] ∈ 自身 pattern 的 bossskill.skillid0 集合",
                "1110/1286 个角色的 charainfo.skillparam* 与其匹配 bossskill 的 skillparam* 逐值相同"
                "（口径＝skillparam1..6 严格比较、剔除 cid 1285；E0 类见 "
                "output/character_skills/charainfo_params/equivalence.json）",
                "98 个同号 denju 行全部满足 denju#v.sname == charainfo[cid=v].skillname（属于另一个角色）",
                "R1 独立审查 output/character_skills/review/r1_20261017_independent/：该槽位原被误当 skilllist 引用",
                "P2 第 1 批原生证据：BtlCharaUtil.CharaParamToBossSkill 把 charainfo 的 skillid[0] 与 "
                "skillparam0..9 按下标对齐写入 BattleBossSkill（调用方 CharaInfoCharaModel.PlaySpMotion、"
                "BtlCharaUtil.GetDenjuSkill）；类型派发见 output/character_skills/charainfo_types/",
                "P2 第 9 批执行侧证据：自身 pattern 可解析 → 执行 pattern（boss 主表）的 bossskill；"
                "无 pattern（F0）→ 执行角色记录自身参数（output/character_skills/cp_paths/path_evidence.json）",
            ],
            "note": note_by_verdict[verdict],
        }
        stats["annotations"] += 1
        bucket("slot0").setdefault("annotations", []).append(annotation)

        # 2. ordinary abilities
        for i, sid in enumerate(skillid[1:], start=1):
            add("ability", self._resolve("skilllist", sid, ref_field=f"skillid[{i}]",
                                         refers_to="普通 skilllist 能力"), f"skillid[{i}]", "skilllist")
        # 3. SA ability flag
        add("sa", self._resolve("skilllist", rec.get("s_ability"), ref_field="s_ability",
                                refers_to="普通 skilllist 能力（SA 旗标）"), "s_ability", "skilllist")

        # 4. patterns -> bosspattern -> bossskill
        for f in PATTERN_FIELDS:
            v = rec.get(f)
            if not v:
                continue
            pat = resolve_pattern(v, f, "Boss/必杀 pattern", "special_move")
            if pat is None:
                continue
            add("special_move", pat, f, "bosspattern")

        # 4b. the character's own special-move text (charainfo.skillname/skilltext)
        if rec.get("skillname") or rec.get("skilltext"):
            sm_text = {"resolved": True, "table": "charainfo", "namespace": "角色必杀技文本",
                       "reference_field": "skilltext", "reference_id": cid, "layer": layer,
                       "refers_to": "角色记录自身的必杀技名与说明（charainfo.skillname/skilltext）",
                       "record": {"skillname": rec.get("skillname"), "skilltext": rec.get("skilltext"),
                                  "skillid0": (rec.get("skillid") or [0])[0],
                                  "skillid0_ref": "charainfo.skillid[0]",
                                  **{f"skillparam{i}": rec.get(f"skillparam{i}") for i in range(10)},
                                  "skillflag0_0": rec.get("skillflag0_0"), "skillflag0_1": rec.get("skillflag0_1"),
                                  "skillflag1_0": rec.get("skillflag1_0"), "skillflag1_1": rec.get("skillflag1_1"),
                                  "iparam0": rec.get("iparam0"), "iparam1": rec.get("iparam1"),
                                  "skill_cost": rec.get("skill_cost")},
                       "source": C.location("charainfo", cid, layer, rec)}
            count(sm_text)
            bucket("special_move")["records"].append(sm_text)

        # 1b. denju table keyed by denju_id (observed: equals a cid in 1500/1504 rows)
        den_rec = self.t("denju").get(cid)
        if den_rec[0] is not None:
            drec = den_rec[0]
            name_same = bool(drec.get("sname") is not None and drec.get("sname") == rec.get("skillname"))
            dent = {"resolved": True, "table": "denju", "namespace": "传授必杀技",
                    "reference_field": "denju.denju_id == cid", "reference_id": cid,
                    "layer": den_rec[1], "refers_to": "传授必杀技（sname/stext/scost ± patternid0..5）",
                    "link_status": ("按 denju_id==cid 关联（该行 sname 与角色 skillname 一致）" if name_same else
                                    "按 denju_id==cid 关联（该行 sname 与角色 skillname 不同；只按 ID 关联，"
                                    "不按名称推断该行归属）"),
                    "name_matches_charainfo_skillname": name_same,
                    "record": drec, "source": C.location("denju", cid, den_rec[1], drec),
                    "denju_pattern_refs": [], "boss_skill_refs": [], "sa_ability_refs": []}
            count(dent)
            bucket("denju")["records"].append(dent)
            seen_denju_skills = set()
            # P2 batch 7: a denju row carries **no** param slots -- only the name/text,
            # cost and patternid0..5. The effect type and parameters live in the
            # referenced bosspattern -> bossskill chain, exactly as they do for
            # charainfo.patternN. Resolved through the same helper so the two paths
            # cannot drift.
            for i in range(9):
                pv = drec.get(f"patternid{i}")
                if not pv:
                    continue
                pat = resolve_pattern(pv, f"denju.patternid{i}",
                                      "传授必杀技 pattern（denju → bosspattern）", "denju")
                if pat is None:
                    continue
                count(pat)
                dent["denju_pattern_refs"].append({
                    "slot": f"patternid{i}", "reference_id": pv, "resolved": pat["resolved"],
                    "layer": pat.get("layer"), "sname": (pat.get("record") or {}).get("sname"),
                    "sinfo": (pat.get("record") or {}).get("sinfo"),
                    "scost": (pat.get("record") or {}).get("scost"),
                })
                # The pattern record itself is *not* registered as a page record: its
                # `sinfo` is the same description text as the denju row in 819/940
                # resolvable rows, so a second record would only duplicate the fragment.
                # Only its skills are attached, as children of the denju entry.
                if not pat["resolved"]:
                    unresolved.append(pat)
                    bucket("denju")["unresolved"].append(pat)
                    continue
                for r in pat.get("boss_skill_refs") or []:
                    if not r.get("resolved"):
                        continue
                    key = (r.get("reference_id"), r.get("layer"))
                    if key in seen_denju_skills:
                        continue
                    seen_denju_skills.add(key)
                    dent.setdefault("boss_skill_refs", []).append(r)
                for r in pat.get("sa_ability_refs") or []:
                    if not r.get("resolved"):
                        continue
                    key = ("sa", r.get("reference_id"), r.get("layer"))
                    if key in seen_denju_skills:
                        continue
                    seen_denju_skills.add(key)
                    dent.setdefault("sa_ability_refs", []).append(r)

        # 5. sympathy (keyed by cid)
        symp = self.sympathy.get(cid)
        if symp:
            entry = self._resolve("skilllist", symp.get("ability0"),
                                  ref_field=f"sympathy_skill_info[_id={cid}].ability0",
                                  refers_to="共鸣 ability（skilllist 命名空间）")
            if entry:
                entry["context"] = {"sympathy_id": cid}
            add("sympathy", entry, "sympathy_skill_info.ability0", "skilllist")

        # 6. leader
        for lr in self.leader.get(cid, []):
            entry = {"resolved": True, "table": "leader_ability", "namespace": "Leader",
                     "reference_field": f"leader_ability[cid={cid}]", "reference_id": cid,
                     "layer": "CACHE", "refers_to": "Leader 能力文本与 skill_ids",
                     "record": lr, "source": C.location("leaderabilityinfo", cid, "CACHE", lr),
                     "skill_refs": [], "sympathy_skill_refs": []}
            count(entry)
            for i, sid in enumerate(lr.get("skill_ids") or []):
                sub = self._resolve("skilllist", sid, ref_field=f"leader_ability[cid={cid}].skill_ids[{i}]",
                                    refers_to="Leader→skilllist")
                count(sub)
                if sub and not sub["resolved"]:
                    unresolved.append(sub)
                    bucket("leader")["unresolved"].append(sub)
                entry["skill_refs"].append(sub or {"resolved": False, "reference_id": sid, "note": "空引用"})
            for i, sid in enumerate(lr.get("sympathy_skill_ids") or []):
                sub = self._resolve("skilllist", sid, ref_field=f"leader_ability[cid={cid}].sympathy_skill_ids[{i}]",
                                    refers_to="Leader共鸣→skilllist")
                count(sub)
                if sub and not sub["resolved"]:
                    unresolved.append(sub)
                    bucket("leader")["unresolved"].append(sub)
                entry["sympathy_skill_refs"].append(sub or {"resolved": False, "reference_id": sid, "note": "空引用"})
            bucket("leader")["records"].append(entry)

        # 7. class (job ability)
        for jr in self.job_by_cid.get(cid, []):
            entry = {"resolved": True, "table": "job_ability", "namespace": "Class",
                     "reference_field": "job_ability.cids contains cid", "reference_id": cid,
                     "layer": "CACHE", "refers_to": "Class（职业共通）能力文本与 skill_ids",
                     "record": jr, "source": C.location("jobabilityinfo", cid, "CACHE", jr),
                     "skill_refs": []}
            count(entry)
            for i, sid in enumerate(jr.get("skill_ids") or []):
                sub = self._resolve("skilllist", sid, ref_field=f"job_ability.skill_ids[{i}]",
                                    refers_to="Class→skilllist")
                count(sub)
                if sub and not sub["resolved"]:
                    unresolved.append(sub)
                    bucket("class")["unresolved"].append(sub)
                entry["skill_refs"].append(sub or {"resolved": False, "reference_id": sid, "note": "空引用"})
            bucket("class")["records"].append(entry)

        # 8. extra
        ex = self.extra.get(cid)
        if ex:
            for i, ab in enumerate(ex.get("extra_abilities") or []):
                entry = {"resolved": True, "table": "extra_ability_info", "namespace": "Extra",
                         "reference_field": f"extra_abilities[{i}]", "reference_id": cid,
                         "layer": "CACHE", "refers_to": "Extra 能力（含等级档）",
                         "record": ab, "source": C.location("extraabilitylist", cid, "CACHE", ex),
                         "skill_refs": []}
                count(entry)
                for j, sid in enumerate(ab.get("skill_ids") or []):
                    sub = self._resolve("skilllist", sid, ref_field=f"extra_abilities[{i}].skill_ids[{j}]",
                                        refers_to="Extra→skilllist")
                    count(sub)
                    if sub and not sub["resolved"]:
                        unresolved.append(sub)
                        bucket("extra")["unresolved"].append(sub)
                    entry["skill_refs"].append(sub or {"resolved": False, "reference_id": sid, "note": "空引用"})
                bucket("extra")["records"].append(entry)

        # 9. passive
        pv = self.passive.get(cid)
        if pv:
            for i, ab in enumerate(pv.get("passives") or []):
                entry = {"resolved": True, "table": "passive_info", "namespace": "PASSIVE",
                         "reference_field": f"passives[{i}]", "reference_id": cid,
                         "layer": "CACHE", "refers_to": "PASSIVE（队伍能力，含等级档）",
                         "record": ab, "source": C.location("passivelist", cid, "CACHE", pv),
                         "skill_refs": []}
                count(entry)
                for j, sid in enumerate(ab.get("skill_ids") or []):
                    sub = self._resolve("skilllist", sid, ref_field=f"passives[{i}].skill_ids[{j}]",
                                        refers_to="PASSIVE→skilllist")
                    count(sub)
                    if sub and not sub["resolved"]:
                        unresolved.append(sub)
                        bucket("passive")["unresolved"].append(sub)
                    entry["skill_refs"].append(sub or {"resolved": False, "reference_id": sid, "note": "空引用"})
                bucket("passive")["records"].append(entry)

        # 10. bond / supporter
        sp = self.support.get(cid)
        if sp:
            entry = {"resolved": True, "table": "supporterskill", "namespace": "羁绊(支援)",
                     "reference_field": "supporterskill.ability_id == cid", "reference_id": cid,
                     "layer": "CACHE", "refers_to": "羁绊（支援）技能文本与 abi0/abi1",
                     "record": sp, "source": C.location("supporterskill", cid, "CACHE", sp),
                     "skill_refs": []}
            count(entry)
            for k in ("abi0", "abi1"):
                sub = self._resolve("skilllist", sp.get(k), ref_field=f"supporterskill.{k}",
                                    refers_to="羁绊→skilllist")
                count(sub)
                if sub and not sub["resolved"]:
                    unresolved.append(sub)
                    bucket("bond")["unresolved"].append(sub)
                entry["skill_refs"].append(sub or {"resolved": False, "reference_id": sp.get(k), "note": "空引用"})
            bucket("bond")["records"].append(entry)

        # 11. denju limit break
        dlb = self.denju_lb.get(cid)
        if dlb:
            for i, item in enumerate(dlb.get("denju_limit_break") or []):
                pat = item.get("patternid0")
                # each list item is its own BattleDenju roll (per limit-break level), so the
                # record key must not collapse the five items of one cid into one record
                entry = {"resolved": True, "table": "denju_limit_break_info", "namespace": "传授突破",
                         "reference_field": f"denju_limit_break[{i}]", "reference_id": f"{cid}#{i}",
                         "layer": "CACHE", "refers_to": "传授限界突破必杀技文本 + patternid0",
                         "record": item,
                         "source": C.location("denju_lblist", cid, "CACHE", dlb),
                         "boss_skill_refs": []}
                count(entry)
                if pat:
                    sub = resolve_pattern(pat, f"denju_limit_break[{i}].patternid0",
                                          "传授突破→bosspattern", "denju_lb")
                    count(sub)
                    if sub and not sub["resolved"]:
                        unresolved.append(sub)
                        bucket("denju_lb")["unresolved"].append(sub)
                    entry["boss_skill_refs"].append(sub or {"resolved": False, "reference_id": pat})
                    # P2 batch 7: the pattern's own skill list is where the effect
                    # parameters live; register those skills so the taught skill gets
                    # readable answers instead of only an unexplained pattern node.
                    for r in (sub or {}).get("boss_skill_refs") or []:
                        if r.get("resolved"):
                            entry["boss_skill_refs"].append(r)
                bucket("denju_lb")["records"].append(entry)

        # 12. heroic
        for hid, link in self.heroic_links.items():
            if cid in link["confirmed_cids"] or (not link["confirmed_cids"] and cid in link["derived_cids"]):
                hrec = next(h for h in self.heroic if h["skillid"] == hid)
                entry = {"resolved": True, "table": "heroicskilllist", "namespace": "英雄技",
                         "reference_field": "heroicskilllist.boss_pattern → cid",
                         "reference_id": hid, "layer": "CACHE",
                         "refers_to": "英雄技（appear/boss_pattern/powup）",
                         "link_status": link["link_status"],
                         "record": hrec, "source": C.location("heroicskilllist", hid, "CACHE", hrec),
                         "boss_skill_refs": []}
                count(entry)
                for pat in link["boss_patterns"]:
                    sub = self._resolve("bosspattern", pat, ref_field=f"heroicskilllist[{hid}].boss_pattern",
                                        refers_to="英雄技→bosspattern")
                    count(sub)
                    if sub and not sub["resolved"]:
                        unresolved.append(sub)
                        bucket("heroic")["unresolved"].append(sub)
                    entry["boss_skill_refs"].append(sub or {"resolved": False, "reference_id": pat})
                bucket("heroic")["records"].append(entry)

        # 13. crossworld
        cw = self.crossworld.get(cid)
        if cw:
            entry = self._resolve("skilllist", cw.get("ability0"),
                                  ref_field=f"crossworld_ability_info[_id={cid}].ability0",
                                  refers_to="CrossWorld ability（skilllist 命名空间）")
            if entry:
                entry["context"] = {"crossworld_id": cw.get("crossworld_id")}
            add("crossworld", entry, "crossworld_ability_info.ability0", "skilllist")

        # sub-effect references (one proven level of expansion)
        sub_refs = []
        seen = set()
        for g in groups.values():
            for r in g["records"]:
                if r.get("table") != "skilllist":
                    continue
                for sid in r["record"].get("sub") or []:
                    key = (r["reference_id"], sid)
                    if key in seen:
                        continue
                    seen.add(key)
                    sub = self._resolve("skilllist", sid, ref_field=f"skilllist[{r['reference_id']}].sub",
                                        refers_to="子效果（单层展开）")
                    count(sub)
                    if sub and not sub["resolved"]:
                        unresolved.append(sub)
                    sub_refs.append({"parent_record_id": r["reference_id"],
                                     **({k: v for k, v in (sub or {}).items()})})

        records_total = sum(len(g["records"]) for g in groups.values())
        return {
            "cid": cid,
            "charainfo_layer": layer,
            "charainfo_source": C.location("charainfo", cid, layer, rec),
            "groups": list(groups.values()),
            "sub_effect_refs": sub_refs,
            "unresolved": unresolved,
            "counts": {
                "references": stats["references"],
                "resolved": stats["resolved"],
                "unresolved": stats["unresolved"],
                "records": records_total,
                "sub_effect_refs": len(sub_refs),
                "annotations": stats["annotations"],
            },
        }


def main():
    C.enable_utf8_console()
    linker = Linker()
    roster = C.roster()
    rows = []
    agg = collections.Counter()
    per_group = collections.Counter()
    layer_usage = collections.Counter()
    unresolved_rows = []
    for r in roster:
        link = linker.link(r["cid"])
        link["name"] = r.get("name")
        link["title"] = r.get("title")
        link["roster_source"] = r.get("data_source")
        link["rarity"] = r.get("rarity")
        link["job_name"] = r.get("job_name")
        rows.append(link)
        agg["characters"] += 1
        for k, v in link["counts"].items():
            agg[k] += v
        if not link["counts"]["references"] == link["counts"]["resolved"] + link["counts"]["unresolved"]:
            raise AssertionError(f"reconcile failed for cid {r['cid']}")
        for g in link["groups"]:
            per_group[g["group"]] += len(g["records"])
            for rec in g["records"]:
                layer_usage[(g["group"], rec.get("layer") or rec.get("table") or "?")] += 1
        for u in link["unresolved"]:
            u = dict(u)
            u["cid"] = r["cid"]
            u["name"] = r.get("name")
            unresolved_rows.append(u)

    # empty references (a nested ref list entry whose id was 0/absent) are recorded in the
    # group records with note=="空引用"; count them so the accounting is explicit
    empty_refs = 0
    for r in rows:
        for g in r["groups"]:
            for rec in g["records"]:
                for key in ("skill_refs", "sympathy_skill_refs", "boss_skill_refs"):
                    for sub in rec.get(key) or []:
                        if sub.get("note") == "空引用":
                            empty_refs += 1
        r["counts"]["empty_refs"] = 0
    for r in rows:
        n = 0
        for g in r["groups"]:
            for rec in g["records"]:
                for key in ("skill_refs", "sympathy_skill_refs", "boss_skill_refs"):
                    for sub in rec.get(key) or []:
                        if sub.get("note") == "空引用":
                            n += 1
        r["counts"]["empty_refs"] = n
    agg["empty_refs"] = empty_refs
    agg["characters_with_unresolved"] = sum(1 for r in rows if r["counts"]["unresolved"])
    agg["characters_with_no_records"] = sum(1 for r in rows if r["counts"]["records"] == 0)
    agg["reconcile_ok"] = agg["references"] == agg["resolved"] + agg["unresolved"]

    C.write_jsonl(OUT / "character_skills.jsonl", rows)
    C.write_json(OUT / "link_summary.json", {
        "generated_by": "scripts/character_skills/link_skills.py",
        "inputs": {
            "charainfo_cache": "output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw",
            "charainfo_apk": "output/base_master/_mdCharacter.json",
            "skilllist_cache": "output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw",
            "skilllist_apk": "output/base_master/_mdSkill.json",
            "bossinfo_cache": "output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw",
            "bossinfo_apk": "output/base_master/_mdBossInfo.json",
            "support_tables": "output/cache_full_20261015_v3/decoded/{heroicskilllist,sympathy_skilllist,leaderabilityinfo,jobabilityinfo,extraabilitylist,passivelist,supporterskill,crossworldabilitylist,denju,denju_lblist}.data5.json.raw",
        },
        "resolution_rule": "逐 ID 缓存优先，缺记录才回退 APK 同命名空间；不逐字段合并；同号不同命名空间不合并",
        "totals": dict(agg),
        "records_per_group": dict(per_group),
        "records_per_group_layer": {f"{k[0]}|{k[1]}": v for k, v in sorted(layer_usage.items())},
        "unresolved_count": len(unresolved_rows),
        "empty_refs": {"count": agg["empty_refs"],
                       "note": "各辅助表 skill_ids／abi0／abi1 里原值为 0（槽位为空）的引用；"
                               "登记在组记录的 *_refs 中但不算引用计数，故 44669 账目闭合"},
        "unresolved_by_table": dict(collections.Counter(u.get("expected_table") for u in unresolved_rows)),
        "unresolved_by_reference_field": dict(collections.Counter(
            (u.get("reference_field") or "?").split(".")[0].split("[")[0] for u in unresolved_rows).most_common(30)),
        "observations": {
            "denju_id_equals_a_cid": linker.denju_id_is_cid,
            "denju_id_name_matches_that_cid_skillname": linker.denju_id_name_match,
            "denju_rows": linker.denju_total,
            "note": ("charainfo.skillid[0] 是必杀技效果类型（与 bossskill.skillid0 同域），不是技能引用，"
                     "因此不产生 resolved/unresolved 引用，只产生 1 条类型标注（每角色 1 条，共 2236）。"
                     "依据：1307 个带 pattern 的角色中 1287 个 skillid[0] ∈ 自身 pattern 的 bossskill.skillid0 集合；"
                     "1110/1286 个角色的 charainfo.skillparam* 与其匹配 bossskill 的 skillparam* 逐值相同；"
                     "98 个同号 denju 行属于 cid 等于该值的另一个角色。同号记录（skilllist 小号段／denju）"
                     "仅登记为 same_number_unrelated_records，不按同号合并。"
                     "该定性由 R1 独立审查提出（review/r1_20261017_independent），实施者复算确认后落盘。"
                     "P2 第 1 批补充：类型域的原生派发索引见 output/character_skills/charainfo_types/；"
                     "charainfo 参数与 boss 规则的记录级等价与例外清单见 "
                     "output/character_skills/charainfo_params/。"),
        },
        "broken_link_policy": "断链保留：写入 unresolved_links.jsonl 与每角色 unresolved，不静默丢弃、不填默认值",
        "denju_chain_note": (
            "P2 第 7 批：denju（传授必杀技）行自身没有 skillparam 槽位，只有 sname/stext/scost/"
            "patternid0..5；效果类型与参数在它引用的 bosspattern→bossskill 链上。link_skills 因此把 "
            "denju.patternidN 解析到 bosspattern，再取该 pattern 的 bossskill 列表作为该 denju 记录的"
            "boss_skill_refs（与 charainfo.patternN 走同一个 resolve_pattern 助手，两条路径不会分叉）。"
            "pattern 记录本身不另登记为页面记录（其 sinfo 与 denju.stext 在 819/940 条可解析行上完全相同，"
            "登记会造成描述片段重复）；解析结果与 pattern 文本写在 denju_pattern_refs。"
            "关联规则：denju.denju_id == cid（实测 1500/1504 落在角色表），不按名称关联；"
            "名称不一致的行只按 ID 关联并在 link_status 注明。"),
    })
    C.write_jsonl(OUT / "unresolved_links.jsonl", unresolved_rows)
    header = ["cid", "name", "reference_field", "reference_id", "expected_table",
              "expected_namespace", "refers_to", "note"]
    C.write_csv(OUT / "unresolved_links.csv", header, [[u.get(h) for h in header] for u in unresolved_rows])

    print(json.dumps(dict(agg), ensure_ascii=False, indent=2))
    print("records per group:", json.dumps(dict(per_group), ensure_ascii=False))
    print("unresolved tables:", json.dumps(dict(collections.Counter(u.get("expected_table") for u in unresolved_rows)), ensure_ascii=False))
    print("unresolved fields:", json.dumps(dict(collections.Counter(
        (u.get("reference_field") or "?").split(".")[0].split("[")[0] for u in unresolved_rows)), ensure_ascii=False))


if __name__ == "__main__":
    main()
