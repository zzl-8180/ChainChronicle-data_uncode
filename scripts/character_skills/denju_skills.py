"""P2 batch 7 -- ``denju`` (传授必杀技 / taught special move): structure, native path, answers.

What the table actually is
--------------------------
The cache snapshot has 1504 ``denju`` rows. They carry ``denju_id`` plus the taught
skill's name/text/cost (``sname``/``stext``/``scost``), ``develop_only``, ``timestamp``,
``weaponChange`` and **``patternid0..5`` -- and no parameter slot of any kind**
(``skillparamN`` does not exist on this table). So the effect type and the numbers are
not on the ``denju`` row; they sit in the ``bosspattern -> bossskill`` chain the row
points at, exactly as they do for ``charainfo.patternN``.

This module therefore:

* reads the structure straight from the decoded snapshot (key inventory, resolution of
  ``patternidN`` in both sources, name/text cross-checks against the referenced pattern);
* re-reads the native path from the recovered image and asserts the whole chain
  instruction by instruction (``BtlCharaUtil.GetDenjuSkill`` ->
  ``CharaParamToBossSkill`` + ``GetDenjuPattern`` ; ``BattleParam.InitlizeDenjuSkill`` ;
  ``BtlCharaUtil.GetExecSkillInfo`` ; ``EnableDenjuSkill``), so ``rules.json``'s
  ``bossskill`` rules may be applied to the denju chain;
* records the per-row chain in ``denju_chains.json`` **including the rows where the
  referenced pattern's skill differs from the character's own special move** (the
  "イミテイト" family), which is where a careless association would produce wrong
  numbers;
* reports the batch increment in the three calibers used by the other batches.

The links themselves are produced by ``link_skills.py`` (``resolve_pattern`` is shared
with the ``charainfo.patternN`` path); this module is evidence and reporting only and
never writes into ``profiles/``.

Outputs (``output/character_skills/denju_skills/``): ``structure.json``,
``native_checks.json``, ``denju_chains.json``, ``p7_increment.json``, ``README.md``.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT / "scripts", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import common as C  # noqa: E402
import rules as R  # noqa: E402
import skilllist_types as S  # noqa: E402

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM  # noqa: E402

OUT = ROOT / "output" / "character_skills" / "denju_skills"
PROF = ROOT / "output" / "character_skills" / "profiles"
LINKS = ROOT / "output" / "character_skills" / "links" / "character_skills.jsonl"
RECORDS_BEFORE = ROOT / "work" / "p7_records_before.jsonl"
SUMMARY_BEFORE = ROOT / "work" / "p7_summary_before.json"

DIS = Cs(CS_ARCH_ARM64, CS_MODE_ARM)

# --- guest RVAs re-read by the checks below (see native_checks.json for the reads) --
CHARA_PARAM_TO_BOSS_SKILL = 0x13AA764
GET_DENJU_SKILL = 0x13ABB38
GET_DENJU_PATTERN = 0x13ABB84
INITLIZE_DENJU_SKILL = 0x10FE034
INITLIZE_DENJU_SKILL_ALT = 0x10FA8F8          # call site 1 in BattleParam.CreatePlayer
GET_EXEC_SKILL_INFO = 0x13AAAA0
ENABLE_DENJU_SKILL = 0x13ABA4C
GET_BATTLE_DENJU_CHARA = 0x13AB800
GET_BATTLE_DENJU_FRIEND = 0x13AB96C
DA_DENJU_PARAMETER_GETINFO = 0xf97880
DA_DENJU_MASTER_GET = 0xf95CEC
DA_LIMITBREAK_DENJU_GETDENJU = 0xe25058
THINK_ATTACK = 0x1008D40
SET_SKILLID = 0x1a6e340
MAKE_LIST_BOSS_SKILL = 0x1a6d4f4

# fields of BattleParam that the denju path fills (offsets from the metadata field list)
BATTLEPARAM_DENJU_FIELDS = {"_denjuSkill": 0xA10, "_denjuListPattern": 0xA18, "_denju": 0xA20}
# fields of BattleDenju / BattleDenju_J: the JSON key set of the ``denju`` table
BATTLEDENJU_J_KEYS = ["denju_id", "patternid0", "patternid1", "patternid2", "patternid3",
                      "patternid4", "patternid5", "patternid6", "weaponChange", "scost",
                      "sname", "stext", "sinfo", "lv"]
DENJU_PARAM_SLOT_PREFIX = "skillparam"


# ---------------------------------------------------------------------------
# native access helpers
# ---------------------------------------------------------------------------
def load_native():
    return S.load_native()


def method_index(md, declaring: str, name: str):
    for i, row in enumerate(md.methods):
        if md.string(row[0]) != name:
            continue
        if md.string(md.types[row[1]][0]) == declaring:
            return i
    return None


def method_rva(md, native, declaring: str, name: str):
    i = method_index(md, declaring, name)
    if i is None:
        return None
    return int(native.method(i)["native_rva"], 16)


def body(native, rva):
    lo, hi = S.func_bounds(native, rva)
    return list(DIS.disasm(native.raw[lo:hi], lo)), lo, hi


def callee_of(native, md, insn):
    if insn.mnemonic not in ("bl", "b") or not insn.op_str.startswith("#"):
        return None, None
    tgt = int(insn.op_str[1:], 16)
    for mi in native.method_by_rva.get(tgt, []):
        m = native.method(mi)
        return m["declaring_type"] + "." + m["name"], tgt
    return None, tgt


def call_sequence(native, md, rva):
    """[(address, mnemonic, op_str, callee-name-or-None)] for one method body."""
    ins, _lo, _hi = body(native, rva)
    out = []
    for insn in ins:
        name, _t = callee_of(native, md, insn)
        out.append((insn.address, insn.mnemonic, insn.op_str, name))
    return out


def callers_of(native, targets):
    """Every ``bl``/``b`` in the image whose target is one of ``targets``."""
    tset = set(targets)
    found = []
    ptrs = sorted({p for p in native.pointers if p})
    for i, a in enumerate(ptrs):
        idx = native.method_by_rva.get(a)
        if not idx:
            continue
        end = ptrs[i + 1] if i + 1 < len(ptrs) else len(native.raw)
        if end - a > 0x4000:
            continue
        for insn in DIS.disasm(native.raw[a:end], a):
            if insn.mnemonic not in ("bl", "b") or not insn.op_str.startswith("#"):
                continue
            if int(insn.op_str[1:], 16) not in tset:
                continue
            m = native.method(idx[0])
            found.append((insn.address, m["declaring_type"] + "." + m["name"], a))
    return found


# ---------------------------------------------------------------------------
# 1. structure of the denju table (data side)
# ---------------------------------------------------------------------------
def denju_structure(linker_stats: dict | None = None) -> dict:
    rows = C.cache_rows("denju")
    keys = collections.Counter()
    for r in rows:
        for k in r:
            keys[k] += 1
    slot_keys = sorted(k for k in keys if k.startswith(DENJU_PARAM_SLOT_PREFIX))
    param_like = sorted(k for k in keys if R.is_param_like(k))
    pat = C.Tables()("bosspattern")

    resolution = collections.Counter()
    names = collections.Counter()
    texts = collections.Counter()
    types_hist = collections.Counter()
    unresolved = []
    no_pattern = []
    per_row = []
    for d in rows:
        cid = d["denju_id"]
        pids = [(f"patternid{i}", d[f"patternid{i}"]) for i in range(9)
                if d.get(f"patternid{i}")]
        if not pids:
            resolution["no_patternid"] += 1
            no_pattern.append({"denju_id": cid, "sname": d.get("sname")})
            continue
        chain = []
        for field, pv in pids:
            prec, layer = pat.get(pv)
            if prec is None:
                resolution["pattern_unresolved"] += 1
                unresolved.append({"denju_id": cid, "sname": d.get("sname"),
                                   "field": field, "patternid": pv,
                                   "in_cache": pv in pat.cache, "in_apk": pv in pat.apk})
                chain.append({"field": field, "patternid": pv, "resolved": False})
                continue
            resolution["pattern_resolved_" + layer] += 1
            if prec.get("sname") is not None:
                names["sname_equal" if prec.get("sname") == d.get("sname") else "sname_differs"] += 1
            else:
                names["sname_empty_on_pattern"] += 1
            if prec.get("sinfo") is not None:
                texts["sinfo_equal" if prec.get("sinfo") == d.get("stext") else "sinfo_differs"] += 1
                if prec.get("sinfo") != d.get("stext") and prec.get("sinfo") and d.get("stext"):
                    texts["sinfo_differs_both_nonempty"] += 1
            else:
                texts["sinfo_empty_on_pattern"] += 1
            skills = []
            for k in sorted(kk for kk in prec if kk.startswith("skillid")):
                bv = prec.get(k)
                if not bv:
                    continue
                brec, blayer = C.Tables()("bossskill").get(bv)
                if brec is None:
                    resolution["boss_skill_unresolved"] += 1
                    skills.append({"slot": k, "skillid": bv, "resolved": False})
                    continue
                types_hist[brec.get("skillid0")] += 1
                skills.append({"slot": k, "skillid": bv, "layer": blayer, "resolved": True,
                               "effect_type": brec.get("skillid0"),
                               "params": {f"skillparam{i}": brec.get(f"skillparam{i}")
                                          for i in range(10)},
                               "flags": {f: brec.get(f) for f in
                                         ("skillflag0_0", "skillflag0_1", "skillflag1_0",
                                          "skillflag1_1", "iparam1", "s_ability")}})
            chain.append({"field": field, "patternid": pv, "layer": layer,
                          "sname": prec.get("sname"), "sinfo": prec.get("sinfo"),
                          "scost": prec.get("scost"), "skills": skills})
        per_row.append({"denju_id": cid, "sname": d.get("sname"), "stext": d.get("stext"),
                        "scost": d.get("scost"), "develop_only": d.get("develop_only"),
                        "weaponChange": d.get("weaponChange"), "chain": chain})

    # charainfo side: is the denju chain the same skill the character already has?
    chara = C.Tables()("charainfo")
    agree = collections.Counter()
    for row in per_row:
        cr, _cl = chara.get(row["denju_id"])
        if cr is None:
            agree["no_charainfo"] += 1
            continue
        if (cr.get("skillname") is not None
                and cr.get("skillname") == row["sname"]):
            agree["charainfo_skillname_equal"] += 1
        else:
            agree["charainfo_skillname_differs"] += 1
        c0 = (cr.get("skillid") or [0])[0]
        all_skills = [s for c in row["chain"] for s in c.get("skills") or []
                      if s.get("resolved")]
        types = {s.get("effect_type") for s in all_skills}
        if c0 in types:
            agree["charainfo_type_present_in_denju_chain"] += 1
            same = [s for s in all_skills if s.get("effect_type") == c0]
            row["charainfo_comparison"] = {
                "charainfo_skillid0": c0,
                "charainfo_params": {f"skillparam{i}": cr.get(f"skillparam{i}") for i in range(10)},
                "denju_chain_matching_skills": [s["skillid"] for s in same],
            }
            ok = False
            for s in same:
                if all(_f32(s["params"].get(f"skillparam{i}")) ==
                       _f32(cr.get(f"skillparam{i}")) for i in range(1, 7)):
                    ok = True
            agree["params_1_6_equal" if ok else "params_1_6_differ"] += 1
            row["charainfo_comparison"]["params_1_6_equal"] = ok
        else:
            agree["charainfo_type_absent_in_denju_chain"] += 1
            row["charainfo_comparison"] = {"charainfo_skillid0": c0,
                                           "denju_chain_types": sorted(t for t in types
                                                                       if t is not None)}

    payload = {
        "generated_by": "scripts/character_skills/denju_skills.py",
        "sources": {
            "cache": "output/cache_full_20261015_v3/decoded/denju.data5.json.raw",
            "cache_limit_break": "output/cache_full_20261015_v3/decoded/denju_lblist.data5.json.raw",
            "bosspattern": "cache bossinfo.data5.json.raw (2149 rows) with output/base_master/_mdBossInfo.json fallback (5177 rows)",
        },
        "row_count": len(rows),
        "key_inventory": dict(sorted(keys.items())),
        "skillparam_slot_keys_present": slot_keys,
        "skillparam_slot_keys_present_count": len(slot_keys),
        "param_like_keys_present": param_like,
        "structure_conclusion": (
            "denju 行没有 skillparamN／flag 等效果参数槽位；效果类型与数值在 patternidN 指向的 "
            "bosspattern→bossskill 链上（bossskill.skillid0 是类型、skillparamN 是槽位）"),
        "pattern_resolution": dict(sorted(resolution.items())),
        "pattern_name_crosscheck": dict(sorted(names.items())),
        "pattern_text_crosscheck": dict(sorted(texts.items())),
        "crosscheck_caliber": ("按 `patternidN` **引用字段**计数（995 个；一行最多 6 个 patternid），"
                               "不是按行；两侧计数之和＝可解析字段数 989（＝995−6 未解析）"),
        "denju_chain_effect_type_histogram": {str(k): v for k, v in
                                              sorted(types_hist.items(),
                                                     key=lambda x: (-x[1], str(x[0])))},
        "charainfo_comparison": dict(sorted(agree.items())),
        "unresolved_patternids": unresolved,
        "rows_without_any_patternid": no_pattern,
        "rows_without_any_patternid_count": len(no_pattern),
        "denju_limit_break_info": _denju_lb_structure(),
        "boundary_note": (
            "patternidN 在两个源都找不到行 ⇒ 该 denju 行没有可用的效果记录，保持未解释并计入断链；"
            "不填默认值、不猜类型。charainfo_comparison 的 params_1_6_differ / type_absent 是"
            "「传授版本与被传授者自身必杀技不同值」的行，答案以 denju 链的 bossskill 为准，"
            "不拿角色自身 skillparam 替换"),
    }
    if linker_stats:
        payload["linker_observations_recheck"] = linker_stats
    return payload, per_row


def _f32(x):
    import struct
    if x is None:
        return None
    try:
        return struct.unpack("<f", struct.pack("<f", float(x)))[0]
    except (TypeError, ValueError, OverflowError):
        return x


def _denju_lb_structure() -> dict:
    raw = C.load_json(C.DECODED / "denju_lblist.data5.json.raw")
    rows = raw["denju_limit_break_info"]
    items = [it for r in rows for it in (r.get("denju_limit_break") or [])]
    keys = collections.Counter()
    for it in items:
        for k in it:
            keys[k] += 1
    return {
        "source": "output/cache_full_20261015_v3/decoded/denju_lblist.data5.json.raw",
        "table": "denju_limit_break_info",
        "rows": len(rows),
        "cids": sorted(r["cid"] for r in rows),
        "item_count": len(items),
        "item_keys": dict(sorted(keys.items())),
        "note": ("传授突破表：键为 cid，每行 5 个 BattleDenju 形状的条目（与 denju 行同键集，"
                 "无 skillparamN）。BattleParam.InitlizeDenjuSkill 的 BattleDenju 参数来自 "
                 "daLimitBreakDenju.GetDenju(cid, limitBreak)：先查本表，未命中回退普通 denju 表"
                 "（daDenjuParameter.GetInfo）；两张表经同一访问器进入同一下游"
                 "（MakePatternList → GetBossPattern → think_attack）。"),
    }


# ---------------------------------------------------------------------------
# 2. the native chain
# ---------------------------------------------------------------------------
def native_evidence():
    md, native = load_native()
    checks = []

    def add(name, ok, **kw):
        checks.append({"check": name, "ok": bool(ok), **kw})

    # -- 2.1 CharaParamToBossSkill copies skillid[0] and skillparam0..9 in index order
    seq = call_sequence(native, md, CHARA_PARAM_TO_BOSS_SKILL)
    seq_names = [c[3] for c in seq]
    want = []
    for i in range(10):
        want.append(f"charaParameter.get_skillparam{i}")
        want.append(f"BattleBossSkill.set_skillparam{i}")
    got = [n for n in seq_names if n and (n.startswith("charaParameter.get_skillparam")
                                          or n.startswith("BattleBossSkill.set_skillparam"))]
    add("chara_param_to_boss_skill_slot_aligned", got == want,
        rva=hex(CHARA_PARAM_TO_BOSS_SKILL), pairs=got,
        note="源侧 skillparamN 逐个写入目标侧同名槽（下标对齐，无移位/重排）")
    add("chara_param_to_boss_skill_type_from_skillid0",
        "BattleBossSkill.set_skillid0" in seq_names
        and "charaParameter.get_skillid" not in [n for n in seq_names if n],
        rva=hex(CHARA_PARAM_TO_BOSS_SKILL),
        read_site=[hex(a) for a, m, o, n in seq if n == "BattleBossSkill.set_skillid0"],
        note="类型槽来自 charaParameter._skillid 列表首元素（ldr x8,[x19,#0x98]; ldr w1,[x8,#0x20]），"
             "不是来自 denju 行")
    add("chara_param_to_boss_skill_requires_skillid_list",
        "charaParameter.get_skillparam0" in seq_names
        and any("0x1a6e340" in o for a, m, o, n in seq),
        rva=hex(CHARA_PARAM_TO_BOSS_SKILL),
        note="先 set_skillid(0)；_skillid 列表为空时整函数返回 null（denju 行不提供该列表）")

    # -- 2.2 GetDenjuSkill = CharaParamToBossSkill + GetDenjuPattern
    seq = call_sequence(native, md, GET_DENJU_SKILL)
    names = [c[3] for c in seq if c[3]]
    add("get_denju_skill_pairs_both_outputs",
        names[:2] == ["BtlCharaUtil.GetDenjuPattern", "BtlCharaUtil.CharaParamToBossSkill"],
        rva=hex(GET_DENJU_SKILL), calls=names,
        note="第 2 出参＝GetDenjuPattern(charaParam, limitBreak)，第 3 出参＝CharaParamToBossSkill(charaParam)")
    skillid_stores = [c for c in seq if c[3] == "BattleBossSkill.set_skillid"]
    add("get_denju_skill_overwrites_record_id",
        bool(skillid_stores)
        and any(i[1] == "mov" and i[2] == "w1, #-1" for i in seq),
        rva=hex(GET_DENJU_SKILL),
        store_site=[hex(c[0]) for c in skillid_stores],
        note="返回前把 BattleBossSkill.skillid 置 -1（记录号为 -1，不是类型槽 skillid0）")

    # -- 2.3 GetDenjuPattern reads the limit-break denju master
    seq = call_sequence(native, md, GET_DENJU_PATTERN)
    names = [c[3] for c in seq if c[3]]
    add("get_denju_pattern_reads_limit_break_denju",
        "DataManager.get_limitBreakDenju" in names
        and "daLimitBreakDenju.GetDenju" in names
        and "BattleDenju.MakePatternList" in names
        and "BattleDenju.getPatternList" in names,
        rva=hex(GET_DENJU_PATTERN), calls=names,
        note="pattern 列表＝daLimitBreakDenju.GetDenju(cid, limitBreak) → BattleDenju.MakePatternList/getPatternList")

    # -- 2.4 InitlizeDenjuSkill fills the three BattleParam fields
    seq = call_sequence(native, md, INITLIZE_DENJU_SKILL)
    names = [c[3] for c in seq if c[3]]
    stores = [(hex(a), m, o) for a, m, o, _n in seq if m == "str" and "#0xa20" in o]
    add("initlize_denju_skill_stores_battledenju_and_patterns",
        bool(stores) and "BossPatternCtrl..ctor" in names
        and "BattleBossPattern.makeListBattleBossSkill" in names
        and any("add" in m and "#0xa10" in o for a, m, o, _n in seq),
        rva=hex(INITLIZE_DENJU_SKILL), stores=stores, calls=names,
        note="_denju@0xa20=BattleDenju；GetDenjuSkill 的第 3 出参写到 this+0xa10（_denjuSkill）；"
             "pattern 列表逐个包 BossPatternCtrl 后追加到 _denjuListPattern@0xa18")
    add("initlize_denju_skill_requires_both_args",
        any(m == "cbz" and o.startswith("x20,") for _a, m, o, _n in seq)
        and any(m == "cbz" and o.startswith("x23,") for _a, m, o, _n in seq),
        rva=hex(INITLIZE_DENJU_SKILL),
        note="sup_chara 或 denju 为空时直接返回（不建 denju 技能）")
    add("initlize_denju_skill_only_battlefields_callers",
        {n for _a, n, _b in callers_of(native, [INITLIZE_DENJU_SKILL])} == {"BattleParam.CreatePlayer"},
        callers=sorted({n for _a, n, _b in callers_of(native, [INITLIZE_DENJU_SKILL])}),
        note="战斗侧唯一调用方是 BattleParam.CreatePlayer（0x10fa8f8 / 0x10faaf4 两处）")

    # -- 2.5 the exec path uses the denju pattern, not the CharaParamToBossSkill product
    seq = call_sequence(native, md, GET_EXEC_SKILL_INFO)
    names = [c[3] for c in seq if c[3]]
    reads_denju = [hex(a) for a, m, o, _n in seq if "#0xa20]" in o]
    reads_patterns = [hex(a) for a, m, o, _n in seq if "#0xa18]" in o]
    add("get_exec_skill_info_denju_branch",
        "BattleParam.get_isSelectDenjuSkill" in names
        and "BattleDenju.get_skillname" in names
        and "BattleDenju.get_skillcost" in names
        and "bhExAttack.think_attack" in names
        and reads_denju and reads_patterns,
        rva=hex(GET_EXEC_SKILL_INFO), calls=names,
        reads_denju=reads_denju, reads_denju_patterns=reads_patterns,
        note="名字与费用取自 BattleDenju（denju 行）；实际攻击由 think_attack 用 _denjuListPattern@0xa18 "
             "的 pattern 执行 ⇒ 数值走 denju 链的 bossskill，而不是 CharaParamToBossSkill 的产物")

    # -- 2.6 EnableDenjuSkill gates
    seq = call_sequence(native, md, ENABLE_DENJU_SKILL)
    names = [c[3] for c in seq if c[3]]
    add("enable_denju_skill_gates",
        "charaParameter.get_isDenjuFrom" in names and "charaParameter.get_isDenjuTo" in names
        and "charaParameter.get_jobtype" in names
        and "daLimitBreakDenju.GetDenju" in names,
        rva=hex(ENABLE_DENJU_SKILL), calls=names,
        note="条件：接收方 isDenjuFrom、传授方 isDenjuTo、双方 jobtype 相同、传授方在该 limitBreak 有 denju")
    add("get_battle_denju_uses_enable_and_limit_break_table",
        "BtlCharaUtil.EnableDenjuSkill" in [n for n in
                                            (c[3] for c in call_sequence(native, md, GET_BATTLE_DENJU_CHARA))
                                            if n]
        and "daLimitBreakDenju.GetDenju" in [n for n in
                                             (c[3] for c in call_sequence(native, md, GET_BATTLE_DENJU_CHARA))
                                             if n],
        rva=hex(GET_BATTLE_DENJU_CHARA),
        note="GetBattleDenju(charaId, supCharaId, supCharaLimitBreak) 先门控，再经 "
             "daLimitBreakDenju.GetDenju 取记录（限界突破表优先，未命中回退普通 denju 表）")

    # -- 2.7 the denju table is a *different* table from DenjuMasterData, and is not
    #        read by any battle path
    keys = [f["name"] for f in native.fields(_type_index(md, "BattleDenju_J"))]
    add("denju_table_json_keys_match_battledenju_j", keys == BATTLEDENJU_J_KEYS,
        got=keys, expected=BATTLEDENJU_J_KEYS,
        note="denju 行的 JSON 键集＝BattleDenju_J；其中没有 skillparamN")
    master_keys = [f["name"] for f in native.fields(_type_index(md, "DenjuMasterData_J"))]
    add("denju_master_data_is_another_table", master_keys == ["cid", "initiation", "forget"],
        got=master_keys,
        note="daDenjuMaster/DenjuMasterData（cid/initiation/forget）是「谁能传授给谁」的关系表，"
             "不是本批的 denju 技能表；两者不混用")
    consumers = {n for _a, n, _b in callers_of(native, [DA_DENJU_PARAMETER_GETINFO])}
    battle_consumers = sorted(c for c in consumers if c.startswith(("BattleParam.", "BtlCharaUtil.",
                                                                    "CharaBehavior.", "bhSkill")))
    # NOTE (p2b7 review P1): the check name says "no battle consumer", but
    # ``all_callers`` itself lists ``daLimitBreakDenju.GetDenju`` -- that accessor
    # falls back to ``daDenjuParameter.GetInfo(cid)`` when the limit-break table has
    # no entry, so the plain denju table *is* reached from the battle path.  The
    # predicate kept here is the narrower, true statement: GetInfo has no caller that
    # is a BattleParam/BtlCharaUtil/CharaBehavior/bhSkill method directly.
    add("denju_getinfo_has_no_direct_battle_caller", not battle_consumers,
        all_callers=sorted(consumers), battle_side_callers=battle_consumers,
        note="daDenjuParameter.GetInfo 没有直接的战斗侧调用方（调用方见 all_callers，多为 "
             "CardInfo.Get*Denju 等 UI/卡面路径）；但它经 daLimitBreakDenju.GetDenju 的**未命中回退**"
             "被战斗路径到达（GetDenju 先查 denju_lblist，未命中则 DataManager.get_denju + GetInfo），"
             "战斗侧的 denju 记录经 daLimitBreakDenju.GetDenju 取得"
             "（denju_lblist 优先，未命中回退普通 denju 表）")

    # -- 2.8 BattleParam field offsets (the three denju fields)
    fields = {f["name"]: int(f["offset"], 16) for f in native.fields(_type_index(md, "BattleParam"))}
    add("battle_param_denju_field_offsets",
        all(fields.get(k) == v for k, v in BATTLEPARAM_DENJU_FIELDS.items()),
        got={k: hex(fields[k]) for k in BATTLEPARAM_DENJU_FIELDS if k in fields},
        expected={k: hex(v) for k, v in BATTLEPARAM_DENJU_FIELDS.items()},
        note="_denjuSkill/_denjuListPattern/_denju 的偏移由元数据字段表确认，与指令里的立即数一致")

    # -- 2.9 cross-check with the P2-1 anchoring
    add("chara_param_to_boss_skill_callers",
        {"CharaInfoCharaModel.PlaySpMotion", "BtlCharaUtil.GetDenjuSkill"}
        <= {n for _a, n, _b in callers_of(native, [CHARA_PARAM_TO_BOSS_SKILL])},
        callers=sorted({n for _a, n, _b in callers_of(native, [CHARA_PARAM_TO_BOSS_SKILL])}),
        note="与 P2 第 1 批相同的调用方结论（本批复读）")

    payload = {
        "generated_by": "scripts/character_skills/denju_skills.py",
        "evidence_kind": "CONTROLLED_NATIVE_FRAGMENT",
        "native_sha256": _sha(native.raw),
        "metadata_sha256": _sha(md.raw),
        "image": "work/protection/il2cpp_loader_seed1.bin",
        "metadata": "work/protection/metadata_aei_decoded.bin",
        "checks": checks,
        "checks_ok": sum(1 for c in checks if c["ok"]),
        "checks_total": len(checks),
        "chain_summary": (
            "BattleParam.CreatePlayer → BtlCharaUtil.GetBattleDenju(门控 EnableDenjuSkill：接收方 "
            "isDenjuFrom／传授方 isDenjuTo／同 jobtype／daLimitBreakDenju.GetDenju≠null) → "
            "BattleParam.InitlizeDenjuSkill(sup_chara, limitBreak, BattleDenju) → "
            "BtlCharaUtil.GetDenjuSkill(charaParam=sup_chara) → 〔A〕CharaParamToBossSkill → "
            "_denjuSkill@0xa10（记录号置 -1）〔B〕GetDenjuPattern → daLimitBreakDenju → "
            "BattleDenju.MakePatternList → BossPatternCtrl 列表 → _denjuListPattern@0xa18；"
            "战斗执行时 BtlCharaUtil.GetExecSkillInfo 用 _denju 取名字/费用并以 _denjuListPattern "
            "调 bhExAttack.think_attack ⇒ 攻防数值来自 denju 链的 pattern→bossskill"),
    }
    return payload


def _type_index(md, name):
    for i, row in enumerate(md.types):
        if md.string(row[0]) == name:
            return i
    raise KeyError(name)


def _sha(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# 3. increment (three calibers) + zero destruction
# ---------------------------------------------------------------------------
def _record_answer_keys(path: Path):
    """{(table, record_id, layer, field): (record_key, effect_type)} incl. children."""
    out = {}
    if not path.exists():
        return out
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            for holder in [r] + [c for c in (r.get("children") or [])
                                 if isinstance(c, dict) and "answers" in c]:
                for a in holder.get("answers") or []:
                    out[(holder.get("table"), holder.get("record_id"), holder.get("layer"),
                         a["f"])] = (holder.get("effect_type"), holder.get("record_id"))
    return out


def _full_answers(path: Path):
    """{(table, record_id, layer, field): answer-dict} over records *and* children."""
    out = {}
    if not path.exists():
        return out
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            for holder in [r] + [c for c in (r.get("children") or [])
                                 if isinstance(c, dict) and "answers" in c]:
                for a in holder.get("answers") or []:
                    out[(holder.get("table"), holder.get("record_id"), holder.get("layer"),
                         a["f"])] = a
    return out


def _unexplained_keys(path: Path):
    out = set()
    if not path.exists():
        return out
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            for holder in [r] + [c for c in (r.get("children") or [])
                                 if isinstance(c, dict) and "unexplained" in c]:
                for u in holder.get("unexplained") or []:
                    out.add((holder.get("table"), holder.get("record_id"),
                             holder.get("layer"), u["f"]))
    return out


def p7_increment() -> dict:
    old = json.loads(SUMMARY_BEFORE.read_text(encoding="utf-8")) if SUMMARY_BEFORE.exists() else None
    summary = json.loads((PROF / "summary.json").read_text(encoding="utf-8"))
    before = _record_answer_keys(RECORDS_BEFORE)
    now = _record_answer_keys(PROF / "records.jsonl")
    new_keys = {k for k in now if k not in before}
    lost = sorted(k for k in before if k not in now)

    # answers physically attached to the denju / denju_lb groups, per page, plus the
    # migration test ("this character had no answer at all before this batch")
    by_type = collections.Counter()
    by_group = collections.Counter()
    chars = collections.defaultdict(set)
    shared_pages = 0
    migrated = 0
    with (PROF / "profiles.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)
            before_on_page = 0
            for g in p["groups"]:
                for ref in g["records"]:
                    old_rec = _record_body(ref.get("rec_key"), before_snapshot=True)
                    if old_rec is None:
                        continue
                    before_on_page += len(old_rec.get("answers") or [])
                    before_on_page += sum(len(c.get("answers") or [])
                                          for c in old_rec.get("children") or []
                                          if isinstance(c, dict))
            before_on_page += len(p.get("baseline") or [])
            hit = set()
            for g in p["groups"]:
                if g["group"] not in ("denju", "denju_lb"):
                    continue
                for ref in g["records"]:
                    rec = _record_body(ref.get("rec_key"))
                    if rec is None:
                        continue
                    holders = [rec] + [c for c in rec.get("children") or []
                                       if isinstance(c, dict) and "answers" in c]
                    for holder in holders:
                        for a in holder.get("answers") or []:
                            key = (holder.get("table"), holder.get("record_id"),
                                   holder.get("layer"), a["f"])
                            by_type[holder.get("effect_type")] += 1
                            by_group[g["group"]] += 1
                            hit.add(holder.get("effect_type"))
                            if key in before:
                                shared_pages += 1
            for t in hit:
                chars[t].add(p["cid"])
            if hit and not before_on_page:
                migrated += 1

    unexplained_now = _unexplained_keys(PROF / "records.jsonl")
    unexplained_then = _unexplained_keys(RECORDS_BEFORE)
    unexplained_added = len(unexplained_now - unexplained_then)
    unexplained_removed = len(unexplained_then - unexplained_now)

    full_before = _full_answers(RECORDS_BEFORE)
    full_now = _full_answers(PROF / "records.jsonl")
    changed_fields = sorted(
        k for k, v in full_before.items()
        if k in full_now and any(full_now[k].get(f) != v.get(f)
                                 for f in ("raw", "kind", "unit", "status", "scope")))
    changed_values = sorted(k for k, v in full_before.items()
                            if k in full_now and "value" in v
                            and full_now[k].get("value") != v.get("value"))

    payload = {
        "batch": "P2 第 7 批",
        "scope": "denju（传授必杀技）记录→bosspattern→bossskill 链",
        "new_answers_page_sum": sum(by_type.values()),
        "new_answers_page_sum_note": (
            "按角色页引用计数，统计对象是**当前规则集**下挂在 denju／denju_lb 页上的答案行；"
            "P7 批次当时（P7 终态）为 3236 条，见 `P7_HANDOFF.md` 与 `README.md` §3.7。"
            "晚于 P7 的批次若给 denju 链上的类型补了规则（例如 P2 第 8 批的攻击系类型 0/1/2/3/4/5/22/47/110），"
            "本数会随之增大，不再等于 summary.rule_answers 的整体批次差"
            f"（当前整体差 {summary['totals']['rule_answers']} − "
            f"{(old or {}).get('totals', {}).get('rule_answers')}）"),
        "new_answers_reachable_from_denju_groups": sum(by_type.values()),
        "new_answers_record_level": (summary["totals"]["rule_answers_unique_records"]
                                     - (old or {}).get("totals", {})
                                     .get("rule_answers_unique_records", 0)),
        "new_answer_keys_unique": len(new_keys),
        "answers_by_group": dict(sorted(by_group.items())),
        "answers_on_pre_existing_answer_keys": shared_pages,
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(by_type.items(),
                                                                 key=lambda x: -x[1])},
        "characters_reachable_total": len({c for s in chars.values() for c in s}),
        "characters_reachable_page_sum": {str(t): len(v) for t, v in sorted(chars.items())},
        "status_migrations_unknown_to_partial": migrated,
        "status_counts_before": (old or {}).get("status_counts"),
        "status_counts_after": summary.get("status_counts"),
        "existing_answer_keys_lost": len(lost),
        "existing_answer_keys_lost_detail": lost[:20],
        "existing_answer_keys_raw_kind_unit_status_scope_changed": len(changed_fields),
        "existing_answer_keys_value_text_changed": len(changed_values),
        "existing_answer_keys_value_text_changed_sample": changed_values[:10],
        "unexplained_fields_delta": {
            "before": (old or {}).get("totals", {}).get("unexplained_fields"),
            "after": summary["totals"]["unexplained_fields"],
            "delta": (summary["totals"]["unexplained_fields"]
                      - (old or {}).get("totals", {}).get("unexplained_fields", 0)),
            "distinct_keys_added": unexplained_added,
            "distinct_keys_removed": unexplained_removed,
            "distinct_keys_removed_by_table": dict(sorted(
                collections.Counter(k[0] for k in (unexplained_then - unexplained_now)).items())),
            "note": ("页求和口径的未解释字段在 denju 页上列出新挂上的传授技能子记录，故总数上升。"
                     "按（表,记录,层,字段）去重的未解释键的减少有两个来源："
                     "①传授突破子记录改为逐条键（denju_limit_break_info 的 5 个条目此前共用键 "
                     "`cid`，现为 `cid#i`）后旧合并键消失；"
                     "②晚于 P7 的批次把槽位从「未解释」变成「答案」（例如 P2 第 8 批的攻击系槽位），"
                     "这类减少对应真实答案，逐类见表 `distinct_keys_removed_by_table`；"
                     f"P7 批次当时 removed＝11（只含①）。顶层记录数 13569 → 13613"
                     "（＋44＝11 个 cid × 4 个先前被合并掉的条目）；其余新增都是挂在 denju 记录下的子记录"),
        },
        "broken_links": summary["totals"]["broken_links"],
        "broken_links_note": ("denju.patternidN 在缓存与 APK 两个源都不存在的行计为断链，"
                              "逐条列在 structure.json.unresolved_patternids"),
        "caliber_note": ("页求和＝按角色页引用计数；记录级＝summary.rule_answers_unique_records"
                         "（records.jsonl 内就地求和）；新增唯一键＝（表,记录,层,字段）新键。"
                         "denju 链多数 bossskill 记录此前已由角色自身 pattern 可达，"
                         f"因此 {sum(by_type.values())} 条引用里只有 {len(new_keys)} 条落在新键上。"
                         "本批同时把传授突破（denju_lblist）的 5 个条目从共用键改为逐条键，"
                         "其答案计入 answers_by_group.denju_lb"),
    }
    C.write_json(OUT / "p7_increment.json", payload)
    return payload


_RECORD_BY_KEY: dict | None = None
_OLD_BY_KEY: dict | None = None


def _record_body(rec_key, before_snapshot: bool = False):
    global _RECORD_BY_KEY, _OLD_BY_KEY
    cache, path = ((_OLD_BY_KEY, RECORDS_BEFORE) if before_snapshot
                   else (_RECORD_BY_KEY, PROF / "records.jsonl"))
    if cache is None:
        cache = {}
        if path.exists():
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    r = json.loads(line)
                    cache[r.get("rec_key")] = r
        if before_snapshot:
            _OLD_BY_KEY = cache
        else:
            _RECORD_BY_KEY = cache
    return cache.get(rec_key)


# ---------------------------------------------------------------------------
# 4. entry point
# ---------------------------------------------------------------------------
def run():
    C.enable_utf8_console()
    OUT.mkdir(parents=True, exist_ok=True)
    link_summary = json.loads((LINKS.parent / "link_summary.json").read_text(encoding="utf-8"))
    stats, per_row = denju_structure(link_summary.get("observations"))
    native = native_evidence()
    C.write_json(OUT / "structure.json", stats)
    C.write_json(OUT / "native_checks.json", native)
    C.write_jsonl(OUT / "denju_chains.jsonl", per_row)
    chains = {"generated_by": "scripts/character_skills/denju_skills.py",
              "rows": len(per_row),
              "columns": ["denju_id", "sname", "stext", "scost", "develop_only", "weaponChange",
                          "chain[] = {field, patternid, layer, sname, sinfo, scost, "
                          "skills[]{slot, skillid, layer, effect_type, params, flags}}",
                          "charainfo_comparison"],
              "rows_with_chain": sum(1 for r in per_row if r["chain"]),
              "rows_without_chain": sum(1 for r in per_row if not r["chain"]),
              "file": "denju_chains.jsonl"}
    C.write_json(OUT / "denju_chains.json", chains)
    inc = p7_increment()
    C.write_json(OUT / "p7_increment.json", inc)

    ok = sum(1 for c in native["checks"] if c["ok"])
    print(json.dumps({
        "denju_rows": stats["row_count"],
        "skillparam_slot_keys": stats["skillparam_slot_keys_present_count"],
        "pattern_resolution": stats["pattern_resolution"],
        "native_checks": f"{ok}/{native['checks_total']}",
        "new_answers_page_sum": inc["new_answers_page_sum"],
        "new_answer_keys_unique": inc["new_answer_keys_unique"],
        "status_migrations": inc["status_migrations_unknown_to_partial"],
        "broken_links": inc["broken_links"],
    }, ensure_ascii=False, indent=1))
    return 0 if ok == native["checks_total"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
