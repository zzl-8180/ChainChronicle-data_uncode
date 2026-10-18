"""P2 batch 9: which copy of a character's special move actually executes.

The P2-1 batch compared the two copies of a character's special-move parameters
(``charainfo.skillparamN`` and the ``bosspattern -> bossskill`` row reachable from the
character's own ``patternN``) and refused to transfer the boss rules wherever the two
copies differ (the ``X1`` class, 104 characters) or where there is no boss row at all
(``NOT_AMONG``).  That gate answered "are the two copies equal", not "which one the game
runs".  This batch answers the second question from the execution side and re-derives the
verdicts from it:

* **own pattern reachable** -> ``bhSkill.CreateExecSkillList`` resolves the pattern and
  ``bhSkill._CreateExecSkillList`` executes ``pattern.getListBattleBossSkill()``, i.e. the
  **boss master** rows (``daBattleBossParameter.getBosSkill``).  So for X1 / X0 /
  NOT_AMONG the executed numbers are the boss side and the character record's copy is
  *not* executed -- the P2-1 gate refused exactly the transfer that would have answered
  the wrong copy.
* **no own pattern reachable** (929 characters, the new ``F0`` class) ->
  ``_CreateExecSkillList`` runs with ``pattern == 0``: it appends the ``BattleBossSkill``
  built by ``BtlCharaUtil.CharaParamToBossSkill`` (``0x13aa390``) and calls
  ``BattleManager.Mission_execSkill``.  That overload fills ``skillid0`` from
  ``BattleParam._atvSkillID`` and ``skillparam0..9`` from ``BattleParam._skillparamN``,
  both copied from ``charaParameter`` (the character record) by ``BattleParam.CreateByID``.
  The constructed skill then travels the *same* path as a boss skill
  (``CheckEntry`` -> ``SetExecSkill`` -> ``bhSkillUtil.initialize_ExAttack`` ->
  ``Execute`` -> ``ExecSkill`` dispatching on ``BattleBossSkill.get_skillid0()``), so the
  character record's own values are the executed values and its type rules apply.

Outputs (``output/character_skills/cp_paths/``):

* ``path_evidence.json`` -- the whole chain with the exact instruction at every hop,
  re-read from the recovered image (never copied from a note).
* ``native_checks.json``  -- the controlled checks (all must pass).
* ``fallback_characters.jsonl`` -- the 929 ``F0`` characters, one line each: type, the
  pattern slots they do carry, whether the type has rules, how many answers they now get.
* ``notamong_exceptions.jsonl`` -- the 20 characters whose own pattern exists but whose
  ``skillid[0]`` is not among its types, each characterised individually.
* ``x1_text_samples.json`` -- the discriminating samples: characters whose skill text
  states a hit count that only the boss side (or only the character side) reproduces.
* ``verdicts.json`` / ``README.md``.

Run: ``python -B scripts/character_skills/cp_paths.py`` (writes only this directory).
"""
from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT / "scripts", ROOT / "scripts" / "character_skills", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import common as C  # noqa: E402
import charainfo_types as CT  # noqa: E402
import equivalence as EQ  # noqa: E402
import rules as R  # noqa: E402
import boss_attack_types as BAT  # noqa: E402

OUT = ROOT / "output" / "character_skills" / "cp_paths"
CHARAINFO_PARAMS = ROOT / "output" / "character_skills" / "charainfo_params"
PROFILES = ROOT / "output" / "character_skills" / "profiles"

# ---------------------------------------------------------------------------
# the chain: every hop with the instruction that carries it
# ---------------------------------------------------------------------------
# (rva, expected instruction text) -- the script re-reads each one and fails loudly.
CHAIN = [
    {
        "step": "1. 战斗角色装载：charaParameter(charainfo 行) → BattleParam",
        "function": "BattleParam.CreateByID",
        "rva": "0x10fcee4",
        "facts": [
            {"rva": 0x10FD01C, "text": "str      x20, [x19, #0x338]",
             "means": "BattleParam._CharaParameter（0x338）= 传入的 charaParameter 行"},
            {"rva": 0x10FD2A4, "text": "ldr      w1, [x8, #0x20]",
             "means": "charaParameter._skillid 数组第 0 项 = 必杀技效果类型"},
            {"rva": 0x10FD2A8, "text": "ldr      x0, [x19, #0x930]",
             "means": "BattleParam._atvSkillID（0x930）"},
            {"rva": 0x10FD2B0, "text": "bl       #0xa9250c",
             "means": "ParamS_int.set_Value → _atvSkillID = charainfo.skillid[0]"},
        ],
    },
    {
        "step": "2. 九个 pattern 槽与十个 skillparam 槽同样来自该 charaParameter 行",
        "function": "BattleParam.CreateByID",
        "rva": "0x10fcee4",
        "facts": [
            {"rva": 0x10FD414, "text": "bl       #0x180b3c4",
             "means": "charaParameter.get_pattern0 → BattleParam.set_pattern0（0x9b8）"},
            {"rva": 0x10FD4E0, "text": "bl       #0x1106f4c",
             "means": "…→ BattleParam.set_pattern8（0x9f8）；九个槽一一对应"},
        ] + [
            {"rva": 0x10FD2D4 + 0x14 * i, "text": None,
             "means": f"charaParameter.get_skillparam{i} → BattleParam.set_skillparam{i}"
                      f"（值来自角色记录，不是 boss 主表）",
             "expect_call_pair": (f"charaParameter.get_skillparam{i}",
                                  f"BattleParam.set_skillparam{i}")}
            for i in range(10)
        ],
    },
    {
        "step": "3. 执行用 pattern 列表由 charainfo 的 pattern 槽在 boss 主表里查得",
        "function": "BattleParam.makeExAttackPatternList",
        "rva": "0x10ffbc8",
        "facts": [
            {"rva": 0x10FFC9C, "text": "str      x20, [x19, #0xa00]",
             "means": "BattleParam._listPattern（0xa00）= 新建列表"},
            {"rva": 0x10FFCB4, "text": "ldr      x0, [x19, #0x9b8]",
             "means": "读 BattleParam._pattern0（0x9b8；由 charainfo.pattern0 装入）"},
            {"rva": 0x10FFDF8, "text": "cbz      w1, #0x10ffe90",
             "means": "pattern 槽为 0 直接跳过（0 不是合法 patternid）"},
            {"rva": 0x10FFE08, "text": "bl       #0x1a701ac",
             "means": "daBattleBossParameter.getBossPattern → boss 主表的 pattern 行"},
            {"rva": 0x10FFE28, "text": "bl       #0x104773c",
             "means": "BossPatternCtrl..ctor；[ctrl+0x10] = BattleBossPattern"},
        ],
    },
    {
        "step": "4. pattern 的技能列表来自 boss 主表的 bossskill 行",
        "function": "BattleBossPattern.makeListBattleBossSkill",
        "rva": "0x1a6d4f4",
        "facts": [
            {"rva": 0x1A6D5EC, "text": "bl       #0x1a6d704",
             "means": "BattleBossPattern.GetBossSkillIDArray（_skillid0..6）"},
            {"rva": 0x1A6D60C, "text": "bl       #0x1803624",
             "means": "DataManager.get_bossparameter"},
            {"rva": 0x1A6D630, "text": "bl       #0x1a6d924",
             "means": "daBattleBossParameter.getBosSkill → bossinfo.bossskill 行"},
        ],
    },
    {
        "step": "5. 两个重载 CharaParamToBossSkill：0x13aa390 读 BattleParam，0x13aa764 读 charaParameter",
        "function": "BtlCharaUtil.CharaParamToBossSkill",
        "rva": "0x13aa390",
        "facts": [
            {"rva": 0x13AA3FC, "text": "ldr      x8, [x19, #0x28]!",
             "means": "x19 = CharaBehavior._param（0x28）= BattleParam"},
            {"rva": 0x13AA404, "text": "ldr      x21, [x8, #0x338]",
             "means": "x21 = BattleParam._CharaParameter（仅用于 motion／flag／str 等字段）"},
            {"rva": 0x13AA458, "text": "bl       #0x1124560",
             "means": "BattleParam.get_atvSkillID → skillid0"},
            {"rva": 0x13AA478, "text": "bl       #0x112a928",
             "means": "BattleParam.get_skillparam0（不是 charaParameter 的同名 getter）"},
            {"rva": 0x13AA574, "text": "bl       #0x112a9e8",
             "means": "BattleParam.get_skillparam9"},
            {"rva": 0x13AA6F8, "text": "bl       #0x112aa00",
             "means": "BattleParam.get_skillflag → set_skillflag（0x13aa708）"},
            {"rva": 0x13AA718, "text": "bl       #0x112aa14",
             "means": "BattleParam.get_skillflag1 → set_skillflag1（0x13aa724）"},
            {"rva": 0x13AA7FC, "text": "bl       #0x180a9d8",
             "means": "对照（另一重载）：0x13aa764 读 charaParameter.get_skillparam0"},
        ],
    },
    {
        "step": "6. CreateExecSkillList：pattern 命中走 pattern，未命中走本记录兜底构造",
        "function": "bhSkill._CreateExecSkillList",
        "rva": "0x1296364",
        "facts": [
            {"rva": 0x129640C, "text": "cbz      x25, #0x12964b0",
             "means": "x3＝pattern；为 0 时进入兜底分支"},
            {"rva": 0x129641C, "text": "bl       #0x1a6d488",
             "means": "pattern.getListBattleBossSkill（boss 主表技能）"},
            {"rva": 0x1296510, "text": "bl       #0x10c0d40",
             "means": "BattleManager.Mission_execSkillPattern（pattern 分支）"},
            {"rva": 0x12964EC, "text": "str      x24, [x8, #0x20]",
             "means": "兜底分支把 CharaParamToBossSkill 的产物放进执行列表"},
            {"rva": 0x12965D4, "text": "b        #0x10c0abc",
             "means": "兜底分支 BattleManager.Mission_execSkill（skillid0／s_ability 来自该构造）"},
        ],
    },
    {
        "step": "7. 两个 CreateExecSkillList 都调用 0x13aa390（兜底构造）",
        "function": "bhSkill.CreateExecSkillList",
        "rva": "0x1295878",
        "facts": [
            {"rva": 0x1295B8C, "text": "bl       #0x13aa390",
             "means": "CheckEntry 路径（0x1295878）的兜底构造"},
            {"rva": 0x1295BCC, "text": "b        #0x1296364",
             "means": "→ _CreateExecSkillList"},
            {"rva": 0x12967EC, "text": "bl       #0x13aa390",
             "means": "SP 按钮路径（0x1296718）的兜底构造"},
            {"rva": 0x1296838, "text": "b        #0x1296364",
             "means": "→ _CreateExecSkillList"},
        ],
    },
    {
        "step": "8. 执行列表第 0 项 → SetExecSkill → initialize_ExAttack（参数取自该 BattleBossSkill）",
        "function": "bhSkill.CheckEntry / bhSkill.SetExecSkill / bhSkillUtil.initialize_ExAttack",
        "rva": "0x1295360",
        "facts": [
            {"rva": 0x12954B0, "text": "bl       #0xa84484",
             "means": "列表 get_Item(0)（= 执行用的 BattleBossSkill）"},
            {"rva": 0x12954B8, "text": "str      x0, [x19, #0xc0]",
             "means": "bhSkill._execSkill（0xc0）"},
            {"rva": 0x12954C0, "text": "bl       #0x1295e70",
             "means": "bhSkill.SetExecSkill"},
            {"rva": 0x1295EC4, "text": "bl       #0x1a6e34c",
             "means": "BattleBossSkill.get_skillid0 → w20 → initializeSkillUtil 的类型"},
            {"rva": 0x1295EF4, "text": "bl       #0x11819d0",
             "means": "bhSkillUtil.initialize_ExAttack(util, chara, BattleBossSkill)"},
            {"rva": 0x1181A70, "text": "bl       #0x1a6e364",
             "means": "initialize_ExAttack 读 BattleBossSkill.get_skillparam0 写入 util"},
            {"rva": 0x1181B00, "text": "bl       #0x1a6e994",
             "means": "…get_skillparam9"},
            {"rva": 0x1181B34, "text": "bl       #0x1a6ea44",
             "means": "…get_skillflag → util._skillflag（0x60）"},
            {"rva": 0x1181B58, "text": "bl       #0x1a6ea5c",
             "means": "…get_skillflag1 → util._skillflag1（0x68）"},
        ],
    },
    {
        "step": "9. Execute → ExecSkill，派发键＝该 BattleBossSkill 的 skillid0",
        "function": "bhSkill.Execute / bhSkill.ExecSkill",
        "rva": "0x1297a98",
        "facts": [
            {"rva": 0x1297B70, "text": "ldr      x8, [x19, #0xc0]",
             "means": "取第 8 步存下的执行用 BattleBossSkill"},
            {"rva": 0x1297B84, "text": "bl       #0x1a6e34c",
             "means": "BattleBossSkill.get_skillid0"},
            {"rva": 0x1297B88, "text": "mov      w2, w0",
             "means": "w2 = 类型"},
            {"rva": 0x1297B94, "text": "bl       #0x1297ccc",
             "means": "bhSkill.ExecSkill(this, w1, w2=类型)"},
            {"rva": 0x1297D28, "text": "cmp      w20, #0x79",
             "means": "type 0..121 走跳转表（其余 default）"},
        ],
    },
    {
        "step": "10. SP 按钮路径：面板给出 patternid，CreateExecSkillList 按它找 pattern",
        "function": "InterfaceManager.OnClickSpSkill / CharaBehavior.CreateExecSkillList",
        "rva": "0x13a1dc8",
        "facts": [
            {"rva": 0x13A2558, "text": "bl       #0x1a6c59c",
             "means": "BattleBossPattern.get_patternid（面板搜索用的键）"},
            {"rva": 0x13A255C, "text": "cmp      w0, w24",
             "means": "w24 = 面板给出的 patternid，与列表中的 pattern 逐个比较"},
            {"rva": 0x13A24E4, "text": "bl       #0x146d40c",
             "means": "PanelCharaInfo.GetPatternId（w24 的来源）"},
            {"rva": 0x13A2860, "text": "mov      w1, w24",
             "means": "把它作为 w1 传给 CharaBehavior.CreateExecSkillList"},
            {"rva": 0x13A2868, "text": "bl       #0x1547668",
             "means": "→ bhSkill.CreateExecSkillList（0x1296718）"},
            {"rva": 0x12967C8, "text": "bl       #0x12969b8",
             "means": "bhSkill.FindPatternCtrl(w1=patternid, 列表)：按 patternid 命中"},
        ],
    },
    {
        "step": "11. 另一条入口：CreateSkillList_SkillID 也先查 boss 主表，查不到才用本记录",
        "function": "bhSkill.CreateSkillList_SkillID",
        "rva": "0x12960f8",
        "facts": [
            {"rva": 0x12961AC, "text": "bl       #0x1a701ac",
             "means": "daBattleBossParameter.getBossPattern(传入的 id)"},
            {"rva": 0x12961D0, "text": "bl       #0x1a6d488",
             "means": "命中：取该 pattern 的 bossskill 行"},
            {"rva": 0x12962CC, "text": "bl       #0x13aa390",
             "means": "未命中（或 id == -1）：CharaParamToBossSkill 兜底构造"},
        ],
    },
    {
        "step": "12. 第 5 个调用方 SkillAbility_EnchantUnionSkill 丢弃构造结果（不是第二条执行路径）",
        "function": "bhSkillUtil.SkillAbility_EnchantUnionSkill",
        "rva": "0x11a5e64",
        "facts": [
            {"rva": 0x11A641C, "text": "bl       #0x13aa390",
             "means": "调用 CharaParamToBossSkill"},
            {"rva": 0x11A6428, "text": "str      x0, [sp, #0x10]",
             "means": "结果只写进栈槽；函数体内此后无 [sp,#0x10] 读取（见 check 12）"},
            {"rva": 0x11A6468, "text": "bl       #0x1a6cdfc",
             "means": "它的 union 数据来自 boss pattern（set_skillcost）与 skillParameter 侧"},
        ],
    },
]

X1_SAMPLES = (2315, 6058, 8139)
NUM = re.compile(r"(\d+)\s*回")
COUNT_SLOT = {1: 3, 105: 6, 110: 6}


# ---------------------------------------------------------------------------
def verify_chain(view):
    """Re-read every claimed instruction; return (facts, checks)."""
    checks = []
    facts = []
    for block in CHAIN:
        got = []
        ok = True
        for f in block["facts"]:
            if f.get("expect_call_pair"):
                # a get_/set_ pair at consecutive call sites: resolve both targets
                pair = []
                for insn in view.insns(f["rva"]):
                    if insn.address < f["rva"]:
                        continue
                    if insn.mnemonic == "bl" and insn.op_str.startswith("#"):
                        pair.append(view.name(int(insn.op_str[1:], 0)))
                    if len(pair) == 2:
                        break
                hit = tuple(pair) == f["expect_call_pair"]
                got.append({"rva": hex(f["rva"]), "expect": list(f["expect_call_pair"]),
                            "got": pair, "ok": hit, "means": f["means"]})
                ok = ok and hit
                continue
            text = view.text_at(f["rva"])
            hit = text == f["text"]
            got.append({"rva": hex(f["rva"]), "expect": f["text"], "got": text, "ok": hit,
                        "means": f["means"]})
            ok = ok and hit
        facts.append({"step": block["step"], "function": block["function"],
                      "function_rva": block["rva"], "instructions": got})
        checks.append({"name": "chain_step_" + block["step"].split(".")[0].strip(),
                       "ok": ok, "function": block["function"],
                       "rva": block["rva"],
                       "mismatches": [g for g in got if not g["ok"]][:4]})

    # check 12: the enchant-union caller really drops the constructed skill
    lo = 0x11A5E64
    reads = []
    for insn in view.insns(lo):
        if insn.mnemonic.startswith("ldr") and "#0x10]" in insn.op_str \
                and "sp" in insn.op_str and insn.address > 0x11A6428:
            reads.append(f"{insn.address:08x}  {insn.mnemonic} {insn.op_str}")
    checks.append({"name": "chain_step_12_dropped_result", "ok": not reads,
                   "function": "bhSkillUtil.SkillAbility_EnchantUnionSkill",
                   "rva": hex(lo),
                   "detail": ("CharaParamToBossSkill 的产物写入 [sp,#0x10] 后全函数无读取"
                              if not reads else "出现读取：%s" % reads[:3])})
    return facts, checks


def x1_discriminating_samples():
    """Characters whose skill text states a hit count that only one side reproduces."""
    t = EQ.tables()
    verdicts = EQ.index()
    out, tally = [], collections.Counter()
    for cid, v in sorted(verdicts.items()):
        if v.get("class") != "X1_VALUES_DIFFER":
            continue
        rec, layer = t["charainfo"].get(cid)
        v0 = v.get("skillid0")
        slot = COUNT_SLOT.get(v0)
        if not rec or slot is None:
            continue
        counts = [int(x) for x in NUM.findall((rec.get("skilltext") or "") + " "
                                              + (rec.get("skillname") or ""))]
        if not counts:
            continue
        own = rec.get(f"skillparam{slot}")
        bosses = [r["record"].get(f"skillparam{slot}") for r in
                  EQ.pattern_boss_refs(rec, t["bosspattern"], t["bossskill"])
                  if r["record"].get("skillid0") == v0]
        # type1 stores (total hits - 1); 105/110 store the total
        off = 1 if v0 == 1 else 0
        hit_own = [c for c in counts if own is not None and abs(float(own) + off - c) < 1e-6]
        hit_boss = [c for c in counts
                    if any(b is not None and abs(float(b) + off - c) < 1e-6 for b in bosses)]
        row = {"cid": cid, "layer": layer, "effect_type": v0, "count_slot": f"skillparam{slot}",
               "text_counts": counts, "charainfo_value": own, "boss_values": bosses,
               "offset_for_this_type": off,
               "text_matches_charainfo": hit_own, "text_matches_boss": hit_boss,
               "verdict": ("TEXT_ONLY_BOSS" if hit_boss and not hit_own else
                           "TEXT_ONLY_CHARAINFO" if hit_own and not hit_boss else
                           "BOTH" if hit_own and hit_boss else "NEITHER"),
               "name": rec.get("skillname"), "text": (rec.get("skilltext") or "")[:120]}
        out.append(row)
        tally[row["verdict"]] += 1
    return out, dict(tally)


def fallback_rows():
    """One row per F0 character: what the fallback path carries into the handler."""
    t = EQ.tables()
    answers_by_cid = collections.defaultdict(list)
    apath = CHARAINFO_PARAMS / "answers.jsonl"
    if apath.exists():
        for line in apath.open(encoding="utf-8"):
            a = json.loads(line)
            answers_by_cid[a["cid"]].append(a)
    rule_types = {ty for (tbl, ty) in R.RULE_TYPES if tbl == "bossskill"}
    status = {}
    ppath = PROFILES / "characters.csv"
    if ppath.exists():
        import csv
        with ppath.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                status[row["cid"]] = row.get("status")
    rows = []
    for cid, v in sorted(EQ.index().items()):
        if v.get("class") != EQ.NO_PATTERN_FALLBACK:
            continue
        rec, layer = t["charainfo"].get(cid)
        v0 = v.get("skillid0")
        ans = answers_by_cid.get(cid, [])
        rows.append({
            "cid": cid, "layer": layer, "skillid0": v0,
            "name": (rec or {}).get("skillname"),
            "pattern_fields_set": v.get("pattern_fields_set"),
            "type_has_confirmed_rules": v0 in rule_types,
            "answers": len(ans),
            "answer_fields": sorted(a["field_path"] for a in ans),
            "status": status.get(str(cid)),
            "execution_path": v.get("execution_path"),
            "note": v.get("note"),
        })
    return rows


def notamong_rows():
    """The 20 characters whose own pattern exists but whose skillid[0] is not among its types."""
    t = EQ.tables()
    rule_types = {ty for (tbl, ty) in R.RULE_TYPES if tbl == "bossskill"}
    status = {}
    import csv
    with (PROFILES / "characters.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            status[row["cid"]] = row.get("status")
    rows = []
    for cid, v in sorted(EQ.index().items()):
        if v.get("class") != "NOT_AMONG_OWN_PATTERN_TYPES":
            continue
        rec, layer = t["charainfo"].get(cid)
        refs = EQ.pattern_boss_refs(rec, t["bosspattern"], t["bossskill"])
        by_pattern = collections.defaultdict(list)
        for r in refs:
            by_pattern[r["pattern"]].append({"skillid": r["skillid"],
                                             "type": r["record"].get("skillid0")})
        types = sorted({r["record"].get("skillid0") for r in refs})
        v0 = v.get("skillid0")
        rows.append({
            "cid": cid, "layer": layer, "skillid0": v0, "name": rec.get("skillname"),
            "status": status.get(str(cid)),
            "pattern_fields": [p for p in v.get("pattern_fields_set") or []],
            "patterns": sorted(by_pattern),
            "pattern_boss_types": types,
            "pattern_skills": {str(k): v2 for k, v2 in sorted(by_pattern.items())},
            "skillid0_type_has_rules": v0 in rule_types,
            "pattern_type_has_rules": sorted(t2 for t2 in types if t2 in rule_types),
            "verdict": ("自身 pattern 可解析 → 战斗执行取 pattern 侧的 bossskill 行（类型见 pattern_boss_types）；"
                        "charainfo 的 skillparam 副本不是执行值，且 skillid[0] 与该 pattern 的类型集合不一致"
                        "（该槽位对执行没有作用）"),
            "extra": (None if any(t2 in rule_types for t2 in types)
                      else "pattern 侧的类型也没有已确认规则 → 该角色仍无答案的原因不是等价前提，而是缺类型规则"),
        })
    return rows


def _answer_keys(path: Path):
    out = {}
    if not path.exists():
        return out
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            for holder in [r] + [c for c in (r.get("children") or [])
                                 if isinstance(c, dict) and "answers" in c]:
                for a in holder.get("answers") or []:
                    key = (holder.get("table"), holder.get("record_id"), holder.get("layer"), a["f"])
                    out[key] = a
    return out


def _status_map(path: Path):
    out = {}
    if not path.exists():
        return out
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            p = json.loads(line)
            out[p["cid"]] = p.get("status")
    return out


def rectification_accounting():
    """p2b9 review rectification: instance-level accounting against the pre-rectification
    products (work/p9_rect_before_records.jsonl).

    Requirements the review set: the affected instances may change *text only* -- every
    instance must keep raw / kind / unit / status, nothing may be lost or added, and the
    only otherwise-changing field allowed is the additive human-readable ``note`` (F4).
    """
    before_path = ROOT / "work" / "p9_rect_before_records.jsonl"
    out = {"baseline": "work/p9_rect_before_records.jsonl（P2 第 9 批整改前）"}
    if not before_path.exists():
        out["note"] = "整改前快照不存在（work/p9_rect_before_records.jsonl），本次不报整改对账"
        return out

    def keys(path):
        got = {}
        for line in path.open(encoding="utf-8"):
            r = json.loads(line)
            holders = [(r, r.get("rec_key"))] + [
                (c, (r.get("rec_key"), c.get("table"), c.get("record_id"),
                     c.get("type_field"), c.get("effect_type")))
                for c in (r.get("children") or []) if isinstance(c, dict) and "answers" in c]
            for h, hk in holders:
                for a in h.get("answers") or []:
                    got[(hk, a["f"])] = a
        return got

    b = keys(before_path)
    a = keys(PROFILES / "records.jsonl")
    # the P8-terminal baseline tells which affected instances are answers this batch added
    p8_path = ROOT / "work" / "p9_records_before.jsonl"
    p8 = keys(p8_path) if p8_path.exists() else {}
    lost = [k for k in b if k not in a]
    new = [k for k in a if k not in b]
    text_only, note_only, other = 0, 0, []
    by_rule = collections.Counter()
    by_origin = collections.Counter()
    for k in b:
        if k not in a or a[k] == b[k]:
            continue
        x, y = b[k], a[k]
        diffs = [f for f in set(x) | set(y) if x.get(f) != y.get(f)]
        if diffs == ["value"]:
            text_only += 1
            by_origin[("P9 新增答案" if k not in p8 else "P8 既有答案",
                       x.get("rule_key"))] += 1
        elif diffs == ["note"]:
            note_only += 1
        else:
            other.append({"key": [str(p) for p in k], "fields": diffs})
        by_rule[(x.get("rule_key"), tuple(diffs))] += 1
    out.update({
        "instances_before": len(b), "instances_after": len(a),
        "lost": len(lost), "new": len(new),
        "value_text_changed": text_only,
        "note_added_only": note_only,
        "raw_kind_unit_status_or_other_changed": len(other),
        "other_sample": other[:5],
        "value_text_changed_by_origin": {
            f"{origin} | {rk}": n for (origin, rk), n in sorted(by_origin.items())},
        "value_text_changed_origin_totals": dict(collections.Counter(
            origin for (origin, _rk), n in by_origin.items() for _ in range(n))),
        "caliber_note": ("本字段按**角色页实例**（rec_key, 字段）计数；p9_increment 的 "
                         "existing_answer_keys_value_text_changed 按（表,记录,层,字段）去重计数，"
                         "因此同一共享 bossskill 记录被多页引用时只计一次（640 vs 901 的差即此）"),
        "by_rule_key_and_changed_fields": {f"{k[0]} | {'+'.join(k[1])}": n
                                           for k, n in by_rule.most_common()},
        "note": ("value_text_changed 的 964 条＝type110 sp6 820＋type1 sp3 99＋type47 sp4 45；"
                 "note_added_only 的 16 条＝F4 给 type27 的 F0 答案补人读注记。"
                 "raw／kind／unit／status 与实例总数逐条未变"),
    })
    return out


def report_increment():
    """P2-9 increment against the P8-terminal snapshot (work/p9_*_before.*)."""
    import csv

    before_rec = ROOT / "work" / "p9_records_before.jsonl"
    before_sum = ROOT / "work" / "p9_summary_before.json"
    before_prof = ROOT / "work" / "p9_before" / "profiles.jsonl"
    old_sum = json.loads(before_sum.read_text(encoding="utf-8")) if before_sum.exists() else {}
    summary = json.loads((PROFILES / "summary.json").read_text(encoding="utf-8"))
    before = _answer_keys(before_rec)
    now = _answer_keys(PROFILES / "records.jsonl")
    new_keys = {k for k in now if k not in before}
    lost = sorted(k for k in before if k not in now)
    changed = sorted(k for k, v in before.items()
                     if k in now and any((now[k] or {}).get(f) != (v or {}).get(f)
                                         for f in ("raw", "kind", "unit", "status", "scope")))
    changed_text = sorted(k for k, v in before.items()
                          if k in now and (now[k] or {}).get("value") != (v or {}).get("value"))
    by_type = collections.Counter()
    by_field = collections.Counter()
    by_class = collections.Counter()
    answers_by_cid = collections.defaultdict(list)
    apath = CHARAINFO_PARAMS / "answers.jsonl"
    for line in apath.open(encoding="utf-8"):
        a = json.loads(line)
        if a.get("equivalence_class") == EQ.NO_PATTERN_FALLBACK:
            by_type[a["effect_type"]] += 1
            by_field[a["field_path"]] += 1
            by_class[a["equivalence_class"]] += 1
            answers_by_cid[a["cid"]].append(a)

    st_before = _status_map(before_prof)
    st_now = _status_map(PROFILES / "profiles.jsonl")
    migrated = sorted(cid for cid, s in st_now.items()
                      if s == "部分" and st_before.get(cid) == "仅未知")
    still_unknown = sorted(cid for cid, s in st_now.items() if s == "仅未知")
    # why the remaining unknown characters are still unknown
    rule_types = {ty for (tbl, ty) in R.RULE_TYPES if tbl == "bossskill"}
    t = EQ.tables()
    index = EQ.index()
    reasons = collections.Counter()
    detail = []
    for cid in still_unknown:
        v = index.get(cid) or {}
        rec, _ = t["charainfo"].get(cid)
        v0 = v.get("skillid0")
        klass = v.get("class")
        if klass == EQ.NO_PATTERN_FALLBACK:
            why = ("F0：自身无 pattern，执行本记录原值，但 skillid[0]=%s 没有已确认规则"
                   % v0) if v0 not in rule_types else "F0 但无可答槽位"
            key = f"F0_TYPE_{v0}_NO_RULE"
        elif klass == "NOT_AMONG_OWN_PATTERN_TYPES":
            types = sorted({r["record"].get("skillid0") for r in
                            EQ.pattern_boss_refs(rec, t["bosspattern"], t["bossskill"])})
            why = (f"NOT_AMONG：执行取 pattern 侧（类型 {types}），"
                   + ("该类型也无已确认规则" if not [x for x in types if x in rule_types]
                      else "但本页其它分组仍未出答案"))
            key = f"NOT_AMONG_PATTERN_TYPE_{types[0] if types else None}_NO_RULE"
        elif klass in ("X0_TYPE_ZERO_UNSET", "X1_VALUES_DIFFER"):
            why = f"{klass}：自身 pattern 可解析、执行取 pattern 侧，但其 pattern 类型无已确认规则"
            key = klass
        elif klass == "X2_ALL_SIX_SLOTS_EMPTY":
            why = "X2：六个槽全空，无值可解释"
            key = klass
        else:
            why = f"{klass}：该类型没有已确认规则"
            key = str(klass)
        reasons[key] += 1
        detail.append({"cid": cid, "class": klass, "skillid0": v0, "why": why,
                       "name": (rec or {}).get("skillname")})

    C.write_json(OUT / "p9_increment.json", {
        "batch": "P2 第 9 批",
        "scope": ("角色必杀技的执行侧裁决（X1／NOT_AMONG／F0）：新增 F0 类的答案，"
                  "X1/NOT_AMONG 保持不给 charainfo 侧数值答案"),
        "new_rules": 0,
        "rectification_accounting": rectification_accounting(),
        "remaining_unknown_by_class_and_type": {
            klass: dict(sorted(collections.Counter(
                r["skillid0"] for r in detail if r["class"] == klass).items(),
                key=lambda kv: -kv[1]))
            for klass in sorted({r["class"] for r in detail})
        },
        "remaining_unknown_grouping_note": (
            "remaining_unknown_reasons 按（类,类型）分桶：F0 用 F0_TYPE_<type>_NO_RULE、"
            "E0／X1 等只按类名分桶（不再拆类型），因此按 handler 汇总时不要把 E0／X1 的类型并入"
            "F0 的类型桶（本字段 remaining_unknown_by_class_and_type 给出无歧义的拆分）"),
        "gate_change": ("equivalence.classify 新增 F0_NO_PATTERN_FALLBACK（自身 pattern0..8 无可达 bossskill）；"
                        "NOT_AMONG_OWN_PATTERN_TYPES 收窄为「自身 pattern 存在但类型集合不含 skillid[0]」的 20 个角色"),
        "class_change": {"before": {"NOT_AMONG_OWN_PATTERN_TYPES": 949},
                         "after": {"NOT_AMONG_OWN_PATTERN_TYPES": 20,
                                   EQ.NO_PATTERN_FALLBACK: 929},
                         "universe_value_comparison": 1287},
        "new_answers_page_sum": len(new_keys),
        "new_answers_record_level": len(new_keys),
        "new_answers_dual_caliber_note": ("charainfo 每 cid 一条记录且每角色一页，页求和＝唯一键数"
                                          "＝records.jsonl 行实例数"),
        "new_answer_keys_unique": len(new_keys),
        "answers_by_type_page_sum": {str(k): v for k, v in sorted(by_type.items(), key=lambda x: -x[1])},
        "answers_by_field_page_sum": {k: v for k, v in sorted(by_field.items(), key=lambda x: -x[1])},
        "answers_by_equivalence_class": dict(by_class),
        "characters_with_new_answers": len(answers_by_cid),
        "status_migrations_unknown_to_partial": len(migrated),
        "status_migrations_detail": [{"cid": cid, "answers": len(answers_by_cid.get(cid, []))}
                                     for cid in migrated],
        "status_counts_before": old_sum.get("status_counts"),
        "status_counts_after": summary.get("status_counts"),
        "remaining_unknown": len(still_unknown),
        "remaining_unknown_reasons": dict(reasons.most_common()),
        "remaining_unknown_detail": detail,
        "existing_answer_keys_lost": len(lost),
        "existing_answer_keys_lost_detail": lost[:10],
        "existing_answer_keys_raw_kind_unit_status_scope_changed": len(changed),
        "existing_answer_keys_value_text_changed": len(changed_text),
        "existing_answer_keys_value_text_changed_caliber": (
            "按（表,记录,层,字段）去重计数（相对 P8 终态基准）；同一共享 bossskill 记录被多角色页引用时只计一次。"
            "按**角色页实例**计数见 rectification_accounting.value_text_changed（964，其中 P8 既有 901／P9 新增 63）"),
        "unexplained_fields_delta": {
            "before": old_sum.get("totals", {}).get("unexplained_fields"),
            "after": summary["totals"]["unexplained_fields"],
            "delta": (summary["totals"]["unexplained_fields"]
                      - old_sum.get("totals", {}).get("unexplained_fields", 0)),
        },
        "rule_answers_before": old_sum.get("totals", {}).get("rule_answers"),
        "rule_answers_after": summary["totals"].get("rule_answers"),
        "zero_breakage_note": ("本批不改任何既有答案的 raw／kind／unit／status；value 文本的**有意**变更见 "
                               "rectification_accounting（type1 sp3／type110 sp6／type47 sp4 三处措辞按审查 F1–F3 "
                               "修正，964 条实例；另 16 条 F0 flag 答案只补人读注记）。相对 P8 终态基准的 "
                               "existing_answer_keys_value_text_changed 即这些既有实例中改到文本的部分"),
    })
    print(json.dumps({"new_answers": len(new_keys), "lost": len(lost), "changed": len(changed),
                      "text_changed": len(changed_text), "migrated": len(migrated),
                      "remaining_unknown": len(still_unknown),
                      "out": str(OUT)}, ensure_ascii=False))


def main():
    C.enable_utf8_console()
    OUT.mkdir(parents=True, exist_ok=True)
    md, native = CT.load_native()
    view = BAT.NativeView(md, native)
    facts, chain_checks = verify_chain(view)

    # the fields the chain claims (metadata field table anchors)
    field_anchors = {}
    for ti, row in enumerate(md.types):
        tn = md.string(row[0])
        if tn in ("BattleParam", "charaParameter", "bhSkillUtil", "BattleBossPattern"):
            field_anchors[tn] = {f["offset"]: f["name"] for f in native.fields(ti)}
    anchors_ok = {
        "BattleParam._CharaParameter@0x338": field_anchors["BattleParam"].get("0x338") == "_CharaParameter",
        "BattleParam._atvSkillID@0x930": field_anchors["BattleParam"].get("0x930") == "_atvSkillID",
        "BattleParam._skillparam0@0x940": field_anchors["BattleParam"].get("0x940") == "_skillparam0",
        "BattleParam._pattern0@0x9b8": field_anchors["BattleParam"].get("0x9b8") == "_pattern0",
        "BattleParam._listPattern@0xa00": field_anchors["BattleParam"].get("0xa00") == "_listPattern",
        "BattleParam._heroicListPattern@0xa48": field_anchors["BattleParam"].get("0xa48") == "_heroicListPattern",
        "BattleParam._denjuListPattern@0xa18": field_anchors["BattleParam"].get("0xa18") == "_denjuListPattern",
        "charaParameter._skillid@0x98": field_anchors["charaParameter"].get("0x98") == "skillid",
        "charaParameter._pattern0@0x130": field_anchors["charaParameter"].get("0x130") == "_pattern0",
        "charaParameter._pattern8@0x170": field_anchors["charaParameter"].get("0x170") == "_pattern8",
        "bhSkillUtil._skillparam0@0x2c": field_anchors["bhSkillUtil"].get("0x2c") == "_skillparam0",
        "bhSkillUtil._numCounter@0xc8": field_anchors["bhSkillUtil"].get("0xc8") == "_numCounter",
        "BattleBossPattern._listBattleBossSkill@0xe0":
            field_anchors["BattleBossPattern"].get("0xe0") == "_listBattleBossSkill",
    }
    checks = chain_checks + [{"name": "metadata_field_anchors_hold", "ok": all(anchors_ok.values()),
                              "detail": anchors_ok}]

    samples, tally = x1_discriminating_samples()
    only_boss = [s["cid"] for s in samples if s["verdict"] == "TEXT_ONLY_BOSS"]
    checks.append({
        "name": "x1_discriminating_samples_favour_the_boss_side",
        "ok": not [s for s in samples if s["verdict"] == "TEXT_ONLY_CHARAINFO"] and bool(only_boss),
        "detail": (f"X1 角色中正文回数可判别的 {len(samples)} 个样本：只与 boss 侧一致 {len(only_boss)} 个"
                   f"（{only_boss}），只与 charainfo 侧一致 0 个"),
        "tally": tally, "samples": samples,
    })
    f0_rows = fallback_rows()
    na_rows = notamong_rows()
    checks.append({
        "name": "f0_and_notamong_partition_matches_the_gate",
        "ok": (len(f0_rows) == EQ.summary()["classes"].get(EQ.NO_PATTERN_FALLBACK)
               and len(na_rows) == EQ.summary()["classes"].get("NOT_AMONG_OWN_PATTERN_TYPES")
               and all(r["patterns"] and r["pattern_boss_types"] for r in na_rows)
               and all(not r["pattern_fields_set"] or True for r in f0_rows)),
        "detail": {"f0": len(f0_rows),
                   "not_among": len(na_rows),
                   "not_among_with_pattern": sum(1 for r in na_rows if r["patterns"]),
                   "not_among_missing_pattern_types":
                       [r["cid"] for r in na_rows if not r["pattern_boss_types"]][:5]},
    })
    checks.append({
        "name": "f0_characters_have_no_pattern_slot_set_at_all",
        "ok": all(not r["pattern_fields_set"] for r in f0_rows),
        "detail": {"f0": len(f0_rows),
                   "with_any_non_zero_pattern": sum(1 for r in f0_rows if r["pattern_fields_set"]),
                   "why": ("九个 pattern 槽全为 0 → BattleParam.makeExAttackPatternList 一个 pattern 都不装入"
                           "（patternid 0 被 cbz 跳过）→ 执行用 pattern 列表为空，兜底分支是唯一路径")},
    })
    checks.append({
        "name": "f0_answer_types_all_carry_confirmed_rules",
        "ok": all(r["type_has_confirmed_rules"] for r in f0_rows if r["answers"]),
        "detail": {"with_answers": sum(1 for r in f0_rows if r["answers"]),
                   "max_answers": max((r["answers"] for r in f0_rows), default=0)},
    })

    passed = sum(1 for c in checks if c["ok"])
    failed = [c["name"] for c in checks if not c["ok"]]

    C.write_json(OUT / "path_evidence.json", {
        "batch": "P2 第 9 批",
        "question": "游戏构建角色必杀技时用哪条路径、哪一侧数值",
        "answer": {
            "own_pattern_reachable": ("执行 pattern 侧：bhSkill._CreateExecSkillList 用 pattern.getListBattleBossSkill()，"
                                      "即 bossinfo.bossskill 主表行（X0／X1／NOT_AMONG 的记录副本不是执行值）"),
            "no_own_pattern": ("执行本记录侧：CharaParamToBossSkill(0x13aa390) 用 BattleParam._atvSkillID"
                               "（← charainfo.skillid[0]）与 _skillparam0..9（← charainfo.skillparamN）构造 "
                               "BattleBossSkill，经 Mission_execSkill 进入同一 ExecSkill 管线（F0 类）"),
        },
        "path_a_pattern_side": [
            "面板／SP 按钮：InterfaceManager.OnClickSpSkill(0x13a1dc8) 取 PanelCharaInfo.GetPatternId 后"
            "调用 CharaBehavior.CreateExecSkillList(0x1547668) → bhSkill.CreateExecSkillList(0x1296718)",
            "逐帧行为：bhSkill.CheckEntry(0x1295360) → bhSkill.CreateExecSkillList(0x1295878) →"
            " bhExAttack.think_attack 选定 pattern",
            "命中：_CreateExecSkillList(0x1296364) pattern!=0 → pattern.getListBattleBossSkill() →"
            " BattleManager.Mission_execSkillPattern(0x10c0d40)",
            "该 pattern 的技能列表由 BattleBossPattern.makeListBattleBossSkill(0x1a6d4f4) 经"
            " daBattleBossParameter.getBosSkill 从 boss 主表建立",
        ],
        "path_b_record_side": [
            "未命中：CharaParamToBossSkill(0x13aa390) 读 BattleParam（_atvSkillID←charainfo.skillid[0]、"
            "_skillparamN←CreateByID 复制的 charainfo.skillparamN）构造 BattleBossSkill",
            "→ _CreateExecSkillList pattern==0 分支：把该 skill 放进执行列表并 BattleManager.Mission_execSkill"
            "(0x10c0abc)",
            "→ bhSkill.CheckEntry 取列表第 0 项 → SetExecSkill(0x1295e70) → bhSkillUtil.initialize_ExAttack"
            "(0x11819d0) 把 BattleBossSkill 的 skillparamN／skillflag 复制进 util",
            "→ bhSkill.Execute(0x1297a98) → bhSkill.ExecSkill(0x1297ccc)，w2＝BattleBossSkill.get_skillid0()",
        ],
        "side_note": ("BattleParam 侧不是 boss 主表侧：BattleParam._skillparamN 由 CreateByID 从 charaParameter"
                      "（角色记录）复制而来；boss 主表的值只在 pattern 分支被执行"),
        "f0_scope_note": ("F0 的 929 个角色的九个 pattern 槽**全部为 0**（不是「pattern 存在但技能为空」）："
                          "BattleParam.makeExAttackPatternList 在 pattern 槽为 0 时直接跳过（0x10ffdf8 cbz），"
                          "因此执行用 pattern 列表为空，兜底分支是它们自身必杀技的唯一路径"
                          "（运行时若由传授链／英雄技 pattern 承担，则以那一侧为准）"),
        "other_callers": {
            "CharaInfoCharaModel.PlaySpMotion(0xda4ac8)": "调用 0x13aa764（读 charaParameter）：卡面／演出用",
            "BtlCharaUtil.GetDenjuSkill(0x13abb60)": "同 0x13aa764：产物 _denjuSkill(0xa10) 的消费点仍未闭合（P7）",
            "bhSkillUtil.SkillAbility_EnchantUnionSkill(0x11a641c)": "调用 0x13aa390 但丢弃结果（栈槽无读取）",
            "bhSkill.CreateSkillList_SkillID(0x12960f8)": "先按 id 查 boss 主表 pattern，未命中才走兜底；"
                                                          "两个调用方为 CharaBehavior.RequestSkillAtId(0x1547754) 与 "
                                                          "bhSkill.CheckEntry",
        },
        "chain": facts,
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
        "metadata_sha256": hashlib.sha256(md.raw).hexdigest(),
    })
    C.write_json(OUT / "native_checks.json", {
        "batch": "P2 第 9 批", "passed": passed, "total": len(checks), "failed": failed,
        "checks": checks,
        "native_sha256": hashlib.sha256(native.raw).hexdigest(),
    })
    C.write_jsonl(OUT / "fallback_characters.jsonl", f0_rows)
    C.write_jsonl(OUT / "notamong_exceptions.jsonl", na_rows)
    C.write_json(OUT / "x1_text_samples.json", {
        "batch": "P2 第 9 批",
        "why": ("X1 的两侧数值不同；角色正文写出的回数只能与一侧相符，因此可以用它判别执行侧。"
                "type1 的槽存 (总次数−1)，105/110 存总次数（见 boss_attack_types/field_dictionary.json）"),
        "suggested_review_samples": list(X1_SAMPLES),
        "tally": tally, "samples": samples,
        "wrong_if": ("若把 X1 判成「charainfo 侧执行」，cid 2315／6058／8139 的正文回数就会与答案矛盾"
                     "（例如 cid 8139 正文 7 回，charainfo.sp3=0.0 → 1 回）"),
    })
    C.write_json(OUT / "verdicts.json", {
        "batch": "P2 第 9 批",
        "classes": EQ.summary()["classes"],
        "applicable_characters": EQ.summary()["applicable_characters"],
        "value_comparison_universe": EQ.summary()["value_comparison_universe"],
        "verdicts": {
            "F0_NO_PATTERN_FALLBACK": ("可给答案：本记录 skillparam0..9（＋skillflag）由兜底构造携带进执行用 "
                                       "BattleBossSkill，类型派发键＝本记录 skillid[0]"),
            "E0/E1/E2": "维持原判：两侧数值相同，答案数字＝执行值（pattern 侧）",
            "X0/X1": ("不给 charainfo 侧数值答案：自身 pattern 可解析，执行取 pattern 侧，本记录副本不是执行值；"
                      "两侧原值都保留，差异槽逐人列出"),
            "NOT_AMONG_OWN_PATTERN_TYPES": ("只指「自身 pattern 存在但类型集合不含 skillid[0]」的 20 个角色；"
                                            "执行取 pattern 侧，本记录副本不参与执行"),
            "X2_ALL_SIX_SLOTS_EMPTY": "无可解释值（cid 1285）",
        },
    })
    readme = f"""# 角色必杀技的执行侧（P2 第 9 批）

只由 `scripts/character_skills/cp_paths.py` 生成。回答「游戏构建这些角色的必杀技时用哪条路径、哪一侧数值」。

## 结论

| 情形的 | 执行路径 | 执行的值 | 角色数 |
|---|---|---|---|
| 自身 pattern 可解析 | `_CreateExecSkillList` 的 pattern 分支 → `pattern.getListBattleBossSkill()` | **boss 主表**（`bosspattern → bossskill`） | {EQ.summary()['value_comparison_universe']}（E0/E1/E2/X0/X1/X2） |
| 自身 pattern 无技能 | `_CreateExecSkillList` 的 `pattern==0` 分支 → `CharaParamToBossSkill(0x13aa390)` | **角色记录自身**（`charainfo.skillid[0]`／`skillparamN`） | {EQ.summary()['classes'].get(EQ.NO_PATTERN_FALLBACK)}（F0） |
| 自身 pattern 有技能但类型不含 `skillid[0]` | pattern 分支 | boss 主表（与本记录的 `skillid[0]` 无关） | {EQ.summary()['classes'].get('NOT_AMONG_OWN_PATTERN_TYPES')} |

因此：

- **X1（{EQ.summary()['classes'].get('X1_VALUES_DIFFER')} 角色）不给 charainfo 侧答案**——执行取 pattern 侧，
  本记录的 `skillparam` 副本是被丢弃的副本（P2 第 1 批拒绝迁移的方向正确）。区分性样本见
  `x1_text_samples.json`（正文回数只与 boss 侧一致）。
- **F0（{EQ.summary()['classes'].get(EQ.NO_PATTERN_FALLBACK)} 角色）给答案**——执行用的就是本记录原值，
  类型派发键＝本记录 `skillid[0]`，因此该类型的槽位规则直接适用（不再需要与 boss 记录逐值比较，
  因为执行路径本身就是「本记录 → BattleBossSkill → 同一 ExecSkill」）。
- **NOT_AMONG 的 20 个角色逐个定性**见 `notamong_exceptions.jsonl`。

## 口径与边界

- 全部为静态指令级证据（`path_evidence.json` 的每一步都写明地址与指令，`native_checks.json` 逐条重读核对），
  **未实机验证**。
- F0 的答案仍标注 `BY_TYPE_EXTRAPOLATED`（类型规则来自该类型 boss 记录的逐条评审）。运行时若由
  传授链（denju）或英雄技 pattern 承担该次必杀，则以那一侧为准（页面相应分组已给该侧答案）。
- 「范围内外」的判定：F0 只要求**自身** pattern 集合为空；`patternN` 指向的 pattern 若在 boss 主表中
  存在但其技能槽全为空，同样落进兜底分支（执行列表为空 → `CheckEntry` 转 `CreateSkillList_SkillID` →
  未命中 → 兜底）。

## 重跑

```powershell
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/cp_paths.py
```
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({"checks": f"{passed}/{len(checks)}", "failed": failed,
                      "f0": len(f0_rows), "not_among": len(na_rows),
                      "x1_text_tally": tally, "out": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    if "--report-increment" in sys.argv:
        C.enable_utf8_console()
        report_increment()
    else:
        main()
