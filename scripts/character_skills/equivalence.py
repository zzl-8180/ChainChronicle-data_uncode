"""charainfo.skillparam* <-> bossskill.skillparam* : record-level equivalence rule.

Why a rule is needed
--------------------
The APK-era character record (``charainfo`` / APK ``charaParameter_J``) carries its
own copy of the special-move parameters (``skillparam0..9``); the newer
``bosspattern -> bossskill`` records carry a second copy reached through the
character's own ``patternN`` fields. The two copies are not equivalent by
construction, so reusing the confirmed boss rule set on the character record needs
an explicit, testable premise.

The premise, and its native backing
-----------------------------------
``BtlCharaUtil.CharaParamToBossSkill`` reads a ``charaParameter`` and writes
``skillid[0] -> skillid0`` plus ``skillparamN -> skillparamN`` (index aligned, no
shift, no reorder) into a fresh ``BattleBossSkill`` -- the same class
``bhSkillUtil.initialize_ExAttack`` consumes and the same ``skillid0`` domain
``bhSkill.ExecSkill`` dispatches on. Its callers are
``CharaInfoCharaModel.PlaySpMotion`` and ``BtlCharaUtil.GetDenjuSkill``.
So the *slot semantics* transfer; the *values* still have to be checked per record,
which is what the classes below do.

The second premise (added by the P2-9 batch, from the execution side)
-------------------------------------------------------------------
The two premises above only compare the two *copies*.  Where the copies disagree,
the execution path decides which copy the game actually uses, and that is a code
question, not a value question.  The path (``output/character_skills/cp_paths/``)
is:

* ``bhSkill.CreateExecSkillList`` (``0x1295878`` / ``0x1296718``) resolves the
  character's own ``patternN`` -> ``BattleBossPatternCtrl`` list
  (``BattleParam.makeExAttackPatternList`` ``0x10ffbc8``, filled from
  ``charaParameter.patternN`` in ``BattleParam.CreateByID`` ``0x10fcee4``).
  A *hit* goes to ``bhSkill._CreateExecSkillList`` (``0x1296364``) with the pattern
  and executes ``pattern.getListBattleBossSkill()`` -- the **boss master** rows
  (``BattleBossPattern.makeListBattleBossSkill`` ``0x1a6d4f4`` ->
  ``daBattleBossParameter.getBosSkill``).
* A *miss* (the character has no reachable pattern skill) goes through
  ``BtlCharaUtil.CharaParamToBossSkill`` (``0x13aa390``), which builds a
  ``BattleBossSkill`` from ``BattleParam`` -- and ``BattleParam._atvSkillID`` /
  ``_skillparam0..9`` were copied from ``charaParameter`` (``charainfo``) by
  ``BattleParam.CreateByID`` (``0x10fd2a4`` ``get skillid[0]`` -> ``set_atvSkillID``;
  ``0x10fd2d4..`` ``get_skillparamN`` -> ``set_skillparamN``).
  ``_CreateExecSkillList`` with ``pattern == 0`` appends that skill and calls
  ``BattleManager.Mission_execSkill``; ``bhSkill.CheckEntry`` (``0x1295360``) feeds
  it to ``SetExecSkill`` (``0x1295e70``) -> ``bhSkillUtil.initialize_ExAttack``
  (``0x11819d0``, which copies ``BattleBossSkill.get_skillparamN`` into the util)
  -> ``bhSkill.Execute`` (``0x1297a98``) -> ``bhSkill.ExecSkill`` (``0x1297ccc``)
  with ``w2 = BattleBossSkill.get_skillid0()``.

So: **with** a reachable own pattern the boss master copy executes; **without** one
the character record copy executes (the "fallback").  The value-equality classes
below stay the caliber the R2 review pinned; the new class ``F0`` carries the
record's *own* values into the same handler, so no value comparison is needed for
it -- but it applies only to characters whose own pattern set is empty.

Classes (universe = roster characters whose ``skillid[0]`` is among their own
pattern's ``bossskill`` types; 1287 characters, of which one -- cid 1285 -- has all
six slots empty and is excluded from the rate, as pinned by the R2 review)

======  ===========================================================  =====  ==============
class   test                                                         n      applicable
======  ===========================================================  =====  ==============
E0      strict ``==`` on skillparam1..6, some type-matched boss       1110   slots 1..6
E1      equal after float32 rounding on 1..6 (JSON repr skew)          15   slots 1..6
E2      E1 plus charainfo-omitted (null) read as 0.0                    52   slots 1..6
F0      own pattern set is empty -> the record's own copy executes      929   slots 0..9
X0      ``skillid[0] == 0`` (type slot unset)                            5   none
X1      values genuinely differ on 1..6                                104   none
X2      all six slots null (cid 1285)                                    1   none
NT      own pattern exists but ``skillid[0]`` is not among its types    20   none
======  ===========================================================  =====  ==============

E0 is the exact caliber the R2 review recomputed and pinned
("1110/1286, skillparam1..6, strict"); the all-ten-slot strict figure is 1098/1287.
E1/E2 are stated as *normalised* sub-classes and never mixed into the strict count.

When ``all ten slots`` also agree after normalisation the transfer covers
skillparam0/7/8/9 as well (that is where the type112 rules live).
"""
from __future__ import annotations

import struct

import common as C

PATTERN_FIELDS = [f"pattern{i}" for i in range(9)]
SLOTS_1_6 = list(range(1, 7))
SLOTS_ALL = list(range(10))
# The P2-9 class: the character has no reachable pattern skill, so the special move
# that actually executes is the BattleBossSkill built from this very record
# (charaParameter -> BattleParam -> CharaParamToBossSkill -> _CreateExecSkillList
# pattern==0 branch).  It carries skillparam0..9 *and* the two skillflag words, so no
# value comparison against a boss record is possible or needed.
NO_PATTERN_FALLBACK = "F0_NO_PATTERN_FALLBACK"
CLASS_APPLICABLE = {"E0", "E1", "E2", NO_PATTERN_FALLBACK}
# charainfo fields outside the skillparam block that the confirmed boss rule set also
# touches (the type27 over-limit rule lives on skillflag0_1). Under E0/E1/E2 they are
# not covered by the record-level presence premise, so each one needs its own value
# check; under F0 they are copied into the executed BattleBossSkill by construction.
FLAG_FIELDS = ("skillflag0_0", "skillflag0_1", "skillflag1_0", "skillflag1_1")
CLASS_NO_TRANSFER = ("X0_TYPE_ZERO_UNSET", "X1_VALUES_DIFFER", "X2_ALL_SIX_SLOTS_EMPTY",
                     "NOT_AMONG_OWN_PATTERN_TYPES", "NO_CHARAINFO")
PATTERN_EVIDENCE = "output/character_skills/cp_paths/path_evidence.json"
NOTAMONG_NOTE = ("自身 pattern 存在且可解析：战斗执行取 pattern（boss 主表）的 bossskill 行"
                 "（这些行已作为 bosspattern 子记录出答案）；本记录的 skillparam 副本不参与执行")

_INDEX: dict | None = None
_TABLES: dict | None = None


def _f32(x):
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return x
    return struct.unpack("<f", struct.pack("<f", float(x)))[0]


def tables():
    global _TABLES
    if _TABLES is None:
        _TABLES = {
            "charainfo": C.Tables()("charainfo"),
            "bosspattern": C.Tables()("bosspattern"),
            "bossskill": C.Tables()("bossskill"),
        }
    return _TABLES


def pattern_boss_refs(rec, pat_t, skill_t):
    """Every bossskill reachable from the character's own pattern fields."""
    refs = []
    for f in PATTERN_FIELDS:
        pv = rec.get(f)
        if not pv:
            continue
        prec, _ = pat_t.get(pv)
        if not prec:
            continue
        for k in sorted(kk for kk in prec if kk.startswith("skillid")):
            bv = prec.get(k)
            if not bv:
                continue
            brec, layer = skill_t.get(bv)
            if brec is None:
                continue
            refs.append({"pattern": pv, "slot": k, "skillid": bv, "layer": layer, "record": brec})
    return refs


def _params(rec, slots):
    return [rec.get(f"skillparam{i}") for i in slots]


def _strict(a, b):
    return a == b


def _f32eq(a, b):
    for x, y in zip(a, b):
        if x is None or y is None:
            if x is not y:
                return False
            continue
        if _f32(x) != _f32(y):
            return False
    return True


def _f32eq_nullzero(a, b):
    for x, y in zip(a, b):
        if _f32(0.0 if x is None else x) != _f32(0.0 if y is None else y):
            return False
    return True


def classify(cid, rec=None, layer=None):
    """Equivalence verdict for one character (cache-preferred record)."""
    t = tables()
    if rec is None:
        rec, layer = t["charainfo"].get(cid)
    if rec is None:
        return {"cid": cid, "class": "NO_CHARAINFO", "applicable": False,
                "applicable_slots": [], "reason": "名册/缓存与 APK 中都没有该 cid 的角色记录"}
    skillid = rec.get("skillid") or []
    v0 = skillid[0] if skillid else 0
    refs = pattern_boss_refs(rec, t["bosspattern"], t["bossskill"])
    own_types = sorted({r["record"].get("skillid0") for r in refs
                        if r["record"].get("skillid0") is not None})
    tm = [r for r in refs if r["record"].get("skillid0") == v0]
    base = {
        "cid": cid, "charainfo_layer": layer, "skillid0": v0,
        "own_pattern_types": own_types,
        "matched_bossskill": [r["skillid"] for r in tm],
        "matched_detail": [{"skillid": r["skillid"], "pattern": r["pattern"], "slot": r["slot"],
                            "layer": r["layer"]} for r in tm],
        "charainfo_params": {f"skillparam{i}": rec.get(f"skillparam{i}") for i in SLOTS_ALL},
        "bossskill_params": [[b.get(f"skillparam{i}") for i in SLOTS_ALL] for b in
                             (r["record"] for r in tm)],
        "charainfo_source": C.location("charainfo", cid, layer, rec),
    }
    if not refs:
        base.update({
            "class": NO_PATTERN_FALLBACK,
            "applicable": True,
            "applicable_slots": list(SLOTS_ALL),
            "applicable_flags": list(FLAG_FIELDS),
            "execution_path": "CHARA_SIDE_FALLBACK",
            "execution_evidence": PATTERN_EVIDENCE,
            "pattern_fields_set": [f for f in PATTERN_FIELDS if rec.get(f)],
            "pattern_boss_refs": 0,
            "reason": ("自身 pattern0..8 在 boss 主表中没有可达的 bossskill（执行用 pattern 列表为空），"
                       "战斗执行走 _CreateExecSkillList 的 pattern==0 兜底构造："
                       "CharaParamToBossSkill(0x13aa390) 用 BattleParam._atvSkillID（← charainfo.skillid[0]）"
                       "与 _skillparam0..9（← BattleParam.CreateByID 复制的 charainfo.skillparamN）"
                       "构造 BattleBossSkill 并由同一 ExecSkill 派发执行，因此本记录原值即执行值"),
            "note": ("槽位语义按 skillid[0] 的类型规则（该 BattleBossSkill 的 skillid0 就是本记录 skillid[0]）；"
                     "若当次战斗的必杀技由传授链（denju）或英雄技 pattern 承担，则以那一侧为准"
                     "（本页相应分组已给答案）"),
        })
        return base
    if v0 not in own_types:
        base.update({
            "class": "NOT_AMONG_OWN_PATTERN_TYPES",
            "applicable": False, "applicable_slots": [],
            "execution_path": "PATTERN_SIDE",
            "execution_evidence": PATTERN_EVIDENCE,
            "reason": "skillid[0] 不在角色自身 pattern 的 bossskill 类型集合内，没有可对齐的 boss 记录",
            "note": NOTAMONG_NOTE,
        })
        return base
    if cid == 1285 or all(rec.get(f"skillparam{i}") is None for i in SLOTS_1_6):
        base.update({"class": "X2_ALL_SIX_SLOTS_EMPTY", "applicable": False,
                     "applicable_slots": [],
                     "reason": "charainfo 侧 skillparam1..6 全为空（无值可解释）"})
        return base
    cp6 = _params(rec, SLOTS_1_6)
    cp10 = _params(rec, SLOTS_ALL)
    tm6 = [_params(r["record"], SLOTS_1_6) for r in tm]
    tm10 = [_params(r["record"], SLOTS_ALL) for r in tm]

    # NOTE on ordering: the value classes are tested *before* the type-0 check so
    # that the E0 count is byte-for-byte the caliber the R2 review pinned
    # (1110/1286). 14 of those characters have skillid[0] == 0 and parameters that
    # strictly equal a same-type boss record; they are flagged in
    # ``type_zero_member`` and produce no answer because rules.json holds no rule
    # for type 0 either way.
    klass = None
    if any(_strict(cp6, b) for b in tm6):
        klass = "E0"
    elif any(_f32eq(cp6, b) for b in tm6):
        klass = "E1"
    elif any(_f32eq_nullzero(cp6, b) for b in tm6):
        klass = "E2"
    if klass is None:
        if v0 == 0:
            base.update({"class": "X0_TYPE_ZERO_UNSET", "applicable": False,
                         "applicable_slots": [],
                         "execution_path": "PATTERN_SIDE",
                         "execution_evidence": PATTERN_EVIDENCE,
                         "reason": "类型槽原值为 0（未设置），按类型对齐无意义；该槽原值本身仍是 0",
                         "note": "自身 pattern 存在且可解析，战斗执行取 pattern 侧（见 NOTAMONG 注）"})
            return base
        diffs = sorted({f"skillparam{i}" for b in tm6 for i in SLOTS_1_6
                        if _f32(cp6[i - 1]) != _f32(b[i - 1])})
        base.update({
            "class": "X1_VALUES_DIFFER", "applicable": False, "applicable_slots": [],
            "execution_path": "PATTERN_SIDE",
            "execution_evidence": PATTERN_EVIDENCE,
            "charainfo_side_executed": False,
            "reason": ("charainfo 与自身 pattern 命中的 bossskill 在 skillparam1..6 上数值不同；"
                       "不能把 boss 规则迁到角色记录，两侧原值都保留"),
            "note": ("执行侧判定（P2 第 9 批）：自身 pattern 可解析 → 战斗执行取 pattern（boss 主表）的 "
                     "bossskill 行，本记录的 skillparam 副本不是执行值；差异槽 " + "、".join(diffs) +
                     "。区分性样本：cid 2315／6058／8139 的正文回数只与 boss 侧一致；"
                     "详见 output/character_skills/cp_paths/"),
            "diff_slots": diffs,
        })
        return base
    all10 = any(_f32eq_nullzero(cp10, b) for b in tm10)
    slots = list(SLOTS_ALL) if all10 else list(SLOTS_1_6)
    base.update({
        "class": klass, "applicable": True, "applicable_slots": slots,
        "all_ten_slots_equal": all10,
        "type_zero_member": v0 == 0,
        "execution_path": "PATTERN_SIDE",
        "execution_evidence": PATTERN_EVIDENCE,
        "executed_values_equal_to_charainfo": True,
        "note_execution": ("战斗执行取 pattern 侧的 bossskill 行；本类两侧数值相同（E0/E1/E2 判据），"
                           "因此本记录原值＝执行值"),
        "reason": {
            "E0": "skillparam1..6 与命中的 bossskill 严格逐值相同",
            "E1": "skillparam1..6 与命中的 bossskill 在 float32 取整后相同（JSON 表示差异）",
            "E2": "skillparam1..6 在把 charainfo 缺省槽读作 0.0 后与命中的 bossskill 相同",
        }[klass],
        "note": ("十槽同样成立，规则可覆盖 skillparam0/7/8/9" if all10
                 else "仅 1..6 成立，规则只覆盖 skillparam1..6"),
    })
    return base


def index() -> dict:
    """cid -> verdict, built once per process over the roster."""
    global _INDEX
    if _INDEX is None:
        _INDEX = {}
        for row in C.roster():
            cid = row["cid"]
            _INDEX[cid] = classify(cid)
    return _INDEX


def verdict(cid):
    return index().get(cid)


def matched_boss_records(cid):
    """[(skillid, record), ...] for bossskills whose type equals the character's."""
    t = tables()
    rec, _ = t["charainfo"].get(cid)
    if rec is None:
        return []
    v0 = (rec.get("skillid") or [0])[0]
    return [(r["skillid"], r["record"]) for r in pattern_boss_refs(rec, t["bosspattern"], t["bossskill"])
            if r["record"].get("skillid0") == v0]


def field_equal(cid, field: str):
    """Is ``field`` value-identical between charainfo and some type-matched boss?"

    Omitted slots on either side read as 0.0 (bossskill stores 0.0 where charainfo
    omits the key), and the comparison is float32-normalised so a JSON
    representation difference does not read as a divergence.
    """
    t = tables()
    rec, _ = t["charainfo"].get(cid)
    if rec is None:
        return False, None
    mine = _f32(0.0 if rec.get(field) is None else rec[field])
    for skillid, brec in matched_boss_records(cid):
        theirs = _f32(0.0 if brec.get(field) is None else brec[field])
        if mine == theirs:
            return True, skillid
    return False, None


def field_allowed(cid, field_path: str):
    """(ok, reason) for transferring the boss rule of ``field_path`` to charainfo."""
    v = verdict(cid)
    if v is None:
        return False, "NOT_IN_ROSTER"
    klass = v.get("class")
    if klass in CLASS_NO_TRANSFER:
        return False, klass
    name = field_path.lstrip("/")
    if name.startswith("skillparam"):
        try:
            i = int(name[len("skillparam"):])
        except ValueError:
            return False, "FIELD_OUTSIDE_EQUIVALENCE_SCOPE"
        if i in v.get("applicable_slots", []):
            return True, klass
        # outside the canonical slot range: needs its own value check
        ok, _ = field_equal(cid, name)
        return (True, klass + "+FIELD_EQUAL") if ok else (False, "SLOT_NOT_IN_EQUIVALENCE_SCOPE")
    if name in FLAG_FIELDS:
        if klass == NO_PATTERN_FALLBACK:
            # the fallback BattleBossSkill is built with set_skillflag / set_skillflag1
            # straight from charaParameter, so the words travel by construction
            return True, klass + "+FIELD_CARRIED_BY_CONSTRUCTION"
        ok, _ = field_equal(cid, name)
        return (True, klass + "+FIELD_EQUAL") if ok else (False, "FIELD_NOT_VALUE_IDENTICAL")
    return False, "FIELD_OUTSIDE_EQUIVALENCE_SCOPE"


def summary():
    counts = {}
    for v in index().values():
        counts[v["class"]] = counts.get(v["class"], 0) + 1
    value_classes = ("E0", "E1", "E2", "X0_TYPE_ZERO_UNSET", "X1_VALUES_DIFFER",
                     "X2_ALL_SIX_SLOTS_EMPTY")
    applicable = sum(n for k, n in counts.items() if k in CLASS_APPLICABLE)
    all10 = sum(1 for v in index().values() if v.get("all_ten_slots_equal"))
    return {
        "universe_definition": (
            "名册可玩角色中，skillid[0] 属于其自身 pattern 可达 bossskill 类型集合的角色"),
        "classes": counts,
        "applicable_characters": applicable,
        "applicable_characters_note": (
            "可迁移＝E0＋E1＋E2＋F0；F0 是 P2 第 9 批新增的「自身无 pattern→记录自身参数即执行值」类，"
            "与 E 类的判据不同（不作数值比较）"),
        "value_comparison_universe": sum(counts.get(k, 0) for k in value_classes),
        "not_applicable_characters": sum(counts.values()) - applicable,
        "strict_1_6_exact_r2_caliber": counts.get("E0", 0),
        "all_ten_slots_equal": all10,
        "note": ("E0 = R2 复核钉死的口径（skillparam1..6 严格比较）；"
                 "E1/E2 为归一后的子类，单独列出，不并入严格计数"),
    }
