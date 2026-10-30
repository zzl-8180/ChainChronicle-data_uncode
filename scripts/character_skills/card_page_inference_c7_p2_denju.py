# -*- coding: utf-8 -*-
"""C7-B2 传授（denju）同记录绑定：2 行 / 5 效果（全 Y.G.）。

任务卡 ``docs/tasks/20261030-c7-p2-throughput-package.md``；预检
``output/character_skills/c7_p2_20261030/precheck/``（``precheck_report.md`` §3、
``batch_plan.json``、``candidates_all.jsonl`` 的 SRB-7250／SRB-30310、
``evidence_boundaries.md``）。

为什么是这两行
--------------
两行都是**传授（denju）原始链的 slot0 记录**，该记录与同卡基础档（``charainfo.pattern0``）
执行的子记录序列逐位相同，且同卡基础档行**已用同一记录同一槽**出过值：

* 7250 ``denju f0``：``denju.patternid0 = 40725003`` → ``bosspattern`` 槽
  ``[40725000 t13, 40725001 t51, 40725002 t105, 40725003 t22]``；slot0 的 t13
  四槽 ``.6/.3/30/.3`` 与同卡 ``special_move pattern0`` 首句行同 ``rule_key`` 同记录
  同值（该行由既有 ``yg1_remaining_ab`` 出值）。本行 6 条效果里 4 条（攻撃力／防御力／
  移動速度／継続時間）可得，句内「敵の攻撃力と防御力を下げる」2 条**保持未知**。
* 30310 ``denju f0``：``denju.patternid0 = 43031002`` → 槽
  ``[43031000 t64, 43031001 t13, 43031002 t74]``；slot0 的 t64 ``param1 = 1.5`` 与同卡
  ``pattern0`` 首句行同 ``rule_key`` 同记录同值（该行由既有 ``kyoumei_ab`` 出值）。
  本行 4 条效果里 1 条（回復）可得，另 3 条**保持未知**。

与 C6 G7-B1 同门法（``card_page_inference_g7_b1.py``）：链定档＋同记录＋同卡基行逐位相等。
差别是**本族每行链内只有一条本类型载体（无双段/首段歧义）**，因此不需要首/次段判别；
「次段」在这两行的对应物是**超共鳴档**（``charainfo.pattern1/pattern2`` 的另一条
``bosspattern``，值不同），只逐行披露为排除分支，不并入本行。

判据（逐行硬门，任一不符即拒绝，不猜）
------------------------------------
1. **行身份**：``row_id`` 在冻结准入表内、同卡、日语片段与该卡 ``denju.stext`` 的**首句**
   逐字相同；``context_text`` 与 ``denju.stext`` 逐字相同。
2. **同层**：行 ``source.layer == CACHE`` 且 ``source_key == CACHE/denju.data5.json.raw``；
   子记录只从 CACHE ``bossinfo`` 取，本模块**不读 APK 表**（``_mdBossInfo`` 同号记录不入）。
3. **链可达且唯一**：``denju[denju_id].patternid0`` 非空、在该层 ``bosspattern`` 唯一命中；
   ``pattern.sinfo`` 与 ``denju.stext`` 逐字相同（正文载体同一）；槽位从 0 连续、
   子记录 ``skillid`` 在本层 ``bossskill`` 唯一命中。
4. **链形状冻结**：槽内 ``skillid`` 序列与类型序列等于准入表（输入漂移即拒绝，
   不静默重绑）；slot0 类型＝本行绑定类型，活动 ``skillparam`` 集合与冻结集合逐位相等。
5. **同卡基行逐位相等**：``charainfo.pattern0`` 指向的 ``bosspattern`` 槽序列与本行链序列
   完全相同（同基础档）；该 ``charainfo`` 记录的对应 ``skillparam`` 与 slot0 逐位相等。
6. **同卡已披露值交叉核**：同卡 ``reference_field=pattern0`` 且句面为
   「已枚举的共鳴前缀 + 本行句身」的行上，本行每个 ``rule_key`` 都存在
   **同记录同原值**答案（只作确认，不作为来源；不是复制）。
7. **排除分支**：超共鳴档（``【超共鳴必殺/…】`` 另一 ``bosspattern``）的同类型 slot0
   逐值披露为排除；链内其余槽（后续句子的载体）只登记不绑定。
8. **去重**：本行已有同 ``rule_key`` 答案时一律不新增（同记录同值＝幂等跳过；
   同值异记录／同键异值＝只写行级披露，不新增、不改写）。
9. **暴击未知**：``bossskill|116|*`` 在 rules 中 0 键，本族不借 type13／2012 其他链补；
   这两行句面本身不含暴击项，marker 只登记该边界。

5 条答案的规则键（不新增规则键、不改 rules.json／rules.py／effect_ledger）
------------------------------------------------------------------------
* ``bossskill|13|/skillparam1``（攻击增益输入）、``/skillparam2``（固定防御值系数）、
  ``/skillparam3``（增益持续时间输入）、``/skillparam6``（移动速度增益输入）；
* ``bossskill|64|/skillparam1``（受击反应回复 reactive heal 基值系数；rules 状态
  「已确认（原生静态局部公式；reactive heal 基值；描述归属另作推断）」，原生点
  ``bhSkillUtil.Exec_REACTIVE_HEAL`` 0x119697c/0x1196988/0x119698c、
  ``CharaStatus.setReactiveHeal`` 0x1196aa4）。

账本侧：以上 5 键都已在 ``effect_ledger._RULE_KEY_EFFECT`` 的通用映射内
（攻撃力／防御力／継続時間／移動速度／回復（词表外）），答案带标准
``rule_key``／``table``／``record_id``／``layer``／``field_path`` 即被既有映射消费；
本模块的 ``binding.c7_p2_denju_binding`` 不被任何来源限定分支识别，**不改账本映射逻辑**。

数值来源
--------
答案的 ``raw_value`` 全部**逐字取自本行原始链的 slot0 记录**，并与同卡基础档行既有答案
逐位比对；不产生该卡此前未出现的数值（0 新增唯一数值）。答案文本不写最终伤害、
不写秒数换算、不做实机验证。
"""
from __future__ import annotations

import math
import re
import struct
import unicodedata
from pathlib import Path

MODULE_VERSION = "c7_p2_denju_binding_20261030"
SCOPE = "C7_P2_DENJU_SAME_RECORD_20261030"
EVIDENCE_SCOPE = "DENJU_SAME_RECORD_20261030"
#: 行级 marker 键（不覆盖其他批次键）。
MARKER_KEY = "inference_c7_p2_denju"
EXACT = "RESOLVED_EXACT_DECODED_RECORD"
ZERO_TOUCH_CIDS = frozenset({30236, 30239})

#: 行日语片段（与 denju.stext 首句逐字相同；canon 后比较）。
CLAUSES = {
    7250: ("【連撃/領域】味方全体の攻撃力と防御力と移動速度が一定時間上がり、"
           "範囲内の全ての敵の攻撃力と防御力を下げる。"),
    30310: ("【連撃/反響】味方全体にダメージを受けるたびに上限を超えて小回復し、"
            "全状態異常を回復する効果を与える。"),
}
#: 共鳴前缀（**逐个枚举**，不做任意标签剥离；R8b 的宽松匹配只作敏感性披露）。
TAGS = {7250: "連撃/領域", 30310: "連撃/反響"}


def base_prefixes(cid):
    tag = TAGS[cid]
    return ("【共鳴必殺/%s】" % tag, "【超共鳴必殺/%s】" % tag)


#: t13 四槽（句面效果, 槽字段, 模板键）——与 C6 G7-B1 同表。
SLOTS_T13 = (("攻撃力", "skillparam1", "attack"),
             ("防御力", "skillparam2", "defense"),
             ("移動速度", "skillparam6", "move"),
             ("継続時間", "skillparam3", "duration"))
SLOT_T64 = ("回復", "skillparam1", "heal")
T13_RULE_PREFIX = "bossskill|13|/"
T64_RULE_KEY = "bossskill|64|/skillparam1"

HUMAN = {
    "attack": ("技能连锁系数为1时，味方全体攻击提升{s}%；实际提升受连锁系数影响"
               "（传授行绑定；共鳴基础档，非升级段）"),
    "defense": ("获得固定防御加成：guard = trunc(float32(_normalAtk × float32({r} × Chain)))；"
                "已核玩家构造分支的名义原始攻击系数约 {p}%；不是固定比例减伤"
                "（传授行绑定；共鳴基础档）"),
    "move": ("技能连锁系数为1时，味方全体移动速度提升{s}%；实际提升受连锁系数影响"
             "（传授行绑定；共鳴基础档）"),
    "duration": ("这组攻击、固定防御与移速加成的支持计时为{s}游戏秒"
                 "（传授行绑定；共鳴基础档）"),
    "heal": ("本技能基值输入 = floor/clamp(float32(B × {r}))（B=getBasicSkillAttack(true)，"
             "已含 Chain），写入 CharaStatus.setReactiveHeal：描述称味方全体每次受到伤害时"
             "「上限を超えて小回復」；不证明超上限保留比例、触发次数与间隔，也不是最终 HP 回复"
             "（传授行绑定；共鳴基础档；描述归属推断）"),
}
_STALE_REASONS = {
    "原文未提供该效果数值，尚无已审定的句内字段归属",
    "此描述尚无可适用的已确认数值或新增机制证据",
}

#: 冻结准入表（2026-10-30 由原始 CACHE 记录独立重导一致后固化；输入漂移即拒绝）。
_ADMITTED_LIST = [
    dict(
        cid=7250,
        row_id="7250-denju-denju-denju_denju_id____cid-lvorder0-f0",
        denju_index=620,
        pattern_id=40725003,
        chain_ids=[40725000, 40725001, 40725002, 40725003],
        chain_types=[13, 51, 105, 22],
        bound_type=13,
        fields=["skillparam1", "skillparam2", "skillparam3", "skillparam6"],
        active_params=["skillparam1", "skillparam2", "skillparam3", "skillparam6"],
        unbound_params=[],
        values={"skillparam1": 0.6, "skillparam2": 0.3,
                "skillparam3": 30, "skillparam6": 0.3},
        base_tier_pointer="charainfo.pattern0",
        base_tier_pattern=40725000,
        super_tier_pointer="charainfo.pattern2",
        super_tier_pattern=40725002,
        super_tier_record=40725008,
        super_tier_values={"skillparam1": 0.75, "skillparam2": 0.375,
                           "skillparam3": 30, "skillparam6": 0.375},
        unbound_slots=["skillid1", "skillid2", "skillid3"],
        unbound_note=("slot1 t51／slot2 t105／slot3 t22 属本行之后的子句（敌方减益、"
                      "10回ダメージ、大ダメージ），不绑定到本行；敌方减益 2 条保持未知"),
    ),
    dict(
        cid=30310,
        row_id="30310-denju-denju-denju_denju_id____cid-lvorder0-f0",
        denju_index=1468,
        pattern_id=43031002,
        chain_ids=[43031000, 43031001, 43031002],
        chain_types=[64, 13, 74],
        bound_type=64,
        fields=["skillparam1"],
        active_params=["skillparam1", "skillparam2", "skillparam3"],
        unbound_params=["skillparam2", "skillparam3"],
        values={"skillparam1": 1.5},
        base_tier_pointer="charainfo.pattern0",
        base_tier_pattern=43031000,
        super_tier_pointer="charainfo.pattern1",
        super_tier_pattern=43031001,
        super_tier_record=43031003,
        super_tier_values={"skillparam1": 1.75},
        unbound_slots=["skillid1", "skillid2"],
        unbound_note=("slot1 t13／slot2 t74 属本行之后的子句（其后句的增益与伤害段）。"
                      "slot1 t13 的四槽与 7250 基础档同签名，但本行句面无攻/防/移表述，"
                      "不绑定；本行另 3 条效果保持未知"),
    ),
]
ADMITTED = {item["row_id"]: item for item in _ADMITTED_LIST}
ADMITTED_CIDS = frozenset(item["cid"] for item in _ADMITTED_LIST)

EVIDENCE = [
    "output/character_skills/c7_p2_20261030/precheck/precheck_report.md",
    "output/character_skills/c7_p2_20261030/precheck/batch_plan.json",
    "output/character_skills/c7_p2_20261030/precheck/evidence_boundaries.md",
    "scripts/character_skills/card_page_inference_g7_b1.py",
    "scripts/character_skills/cp_paths.py",
]
LIMIT = ("slot0 记录属本行的归属为推断（链序＋同卡基础档已披露值一致，未新增原生证据）；"
         "超共鳴档为排除分支，不并入本行；不写最终伤害、不做秒数换算、不做实机验证。")

_TABLES = {}


def _read(path: Path):
    import json
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def tables(data):
    """CACHE 解码主表（按 root 缓存；只读）。"""
    root = Path(getattr(data, "root", Path("."))).resolve()
    key = str(root)
    if key not in _TABLES:
        base = root / "output/cache_full_20261015_v3/decoded"
        boss = _read(base / "bossinfo.data5.json.raw")["bossinfo"]
        patterns, skills = {}, {}
        for i, rec in enumerate(boss.get("bosspattern") or []):
            patterns.setdefault(rec.get("patternid"), []).append((i, rec))
        for i, rec in enumerate(boss.get("bossskill") or []):
            skills.setdefault(rec.get("skillid"), []).append((i, rec))
        denju = {rec["denju_id"]: (i, rec)
                 for i, rec in enumerate(_read(base / "denju.data5.json.raw")["denju"])}
        chara = {rec["cid"]: rec
                 for rec in _read(base / "charainfo.data5.json.raw")["charainfo"]}
        _TABLES[key] = dict(patterns=patterns, skills=skills, denju=denju, chara=chara,
                            skills_all=boss.get("bossskill") or [], root=root)
    return _TABLES[key]


def canon(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(text or "")))


def tag_body(text):
    """剥离句首【…】后的句身（**只用于敏感性披露**，不作准入判据）。"""
    return re.sub(r"^(?:【[^】]*】)+", "", canon(text))


def _num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return ("%.6f" % f).rstrip("0").rstrip(".")


def _f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def raw_state(raw, present=True):
    """缺失 / null / 非有限 / 负值 / 真零 / 有限分开标注（不把任何一档补成 0）。"""
    if not present:
        return "MISSING"
    if raw is None:
        return "NULL"
    if isinstance(raw, bool):
        return "NON_FINITE"
    try:
        f = float(raw)
    except (TypeError, ValueError):
        return "NON_FINITE"
    if not math.isfinite(f):
        return "NON_FINITE"
    if f < 0:
        return "NEGATIVE"
    if f == 0:
        return "ZERO"
    return "FINITE"


# ---------------------------------------------------------------- 链与基行

def chain_of(tab, cid, adm=None):
    """denju 原始链 → (chain|None, rejection)。"""
    adm = adm or next(i for i in _ADMITTED_LIST if i["cid"] == cid)
    hit = tab["denju"].get(cid)
    if hit is None:
        return None, "DENJU_RECORD_MISSING"
    didx, denju = hit
    pid = denju.get("patternid0")
    if not pid:
        return None, "PATTERN_POINTER_MISSING"
    pats = tab["patterns"].get(pid) or []
    if len(pats) != 1:
        return None, "BOSSPATTERN_NOT_UNIQUE"
    pidx, pattern = pats[0]
    if not pattern.get("sinfo") or canon(pattern.get("sinfo")) != canon(denju.get("stext")):
        return None, "PATTERN_TEXT_MISMATCH"
    slots = [(slot, pattern.get("skillid%d" % slot)) for slot in range(7)
             if pattern.get("skillid%d" % slot)]
    if [s for s, _ in slots] != list(range(len(slots))):
        return None, "SLOT_NOT_CONTIGUOUS"
    children = []
    for slot, sid in slots:
        hits = tab["skills"].get(sid) or []
        if len(hits) != 1:
            return None, "SKILL_NOT_UNIQUE(%s)" % sid
        k_index, rec = hits[0]
        children.append(dict(slot="skillid%d" % slot, skillid=sid, index=k_index,
                             type=rec.get("skillid0"), record=rec,
                             params={k: v for k, v in rec.items()
                                     if k.startswith("skillparam")}))
    return dict(denju_index=didx, denju_record=denju, pattern_id=pid,
                pattern_index=pidx, pattern=pattern, children=children,
                layer="CACHE"), None


def base_tier_of(tab, cid, adm, chain):
    """同卡基础档（charainfo.pattern0）与超共鳴档的独立重导（只读）。"""
    chara = tab["chara"].get(cid)
    out = dict(chara_present=chara is not None)
    if chara is None:
        return out
    pid0 = chara.get("pattern0")
    out["base_tier_pattern"] = pid0
    pats = tab["patterns"].get(pid0) or []
    out["base_tier_unique"] = len(pats) == 1
    if len(pats) == 1:
        _, base_pattern = pats[0]
        out["base_tier_slots"] = [base_pattern.get("skillid%d" % s)
                                  for s in range(len(chain["children"]))]
        out["base_tier_same_sequence"] = (
            out["base_tier_slots"] == [c["skillid"] for c in chain["children"]])
        out["base_tier_sinfo"] = base_pattern.get("sinfo")
    out["chara_params"] = {k: v for k, v in chara.items() if k.startswith("skillparam")}
    out["chara_ten_slot_match"] = all(
        out["chara_params"].get(f) == chain["children"][0]["params"].get(f)
        for f in adm["fields"])
    return out


def super_tier_of(tab, cid, adm):
    """超共鳴档（另一 ``bosspattern``）的同类型 slot0（只作排除披露）。"""
    chara = tab["chara"].get(cid) or {}
    out = []
    for i in range(1, 5):
        pid = chara.get("pattern%d" % i)
        if not pid:
            continue
        pats = tab["patterns"].get(pid) or []
        if len(pats) != 1:
            continue
        _, pattern = pats[0]
        sinfo = str(pattern.get("sinfo") or "")
        if "超共鳴" not in sinfo:
            continue
        sid = pattern.get("skillid0")
        hits = tab["skills"].get(sid) or []
        if len(hits) != 1 or hits[0][1].get("skillid0") != adm["bound_type"]:
            continue
        rec = hits[0][1]
        out.append(dict(pointer="charainfo.pattern%d" % i, pattern_id=pid,
                        record_id=sid, type=rec.get("skillid0"),
                        values={f: rec.get(f) for f in adm["fields"]},
                        clause=sinfo[:120]))
    return out


def _rows(groups):
    return {r["row_id"]: r for g in groups or [] for s in g.get("skills") or []
            for r in s.get("rows") or []}


def _base_answers(rows, rid, cid, adm):
    """同卡「已枚举共鳴前缀 + 本行句身」行上的答案（逐字同文；只作交叉核）。

    返回 (primary, secondary, relaxed)：
      primary  = ``reference_field == pattern0`` 且句面逐字等于已枚举前缀＋句身；
      secondary= ``reference_field == skilltext`` 的同口径行（只披露）；
      relaxed  = 任意「剥离句首【…】后同文」的行（**R8b 敏感性披露，不作准入**）。
    """
    body = tag_body(CLAUSES[cid])
    prefixes = base_prefixes(cid)
    primary, secondary, relaxed = [], [], []
    for other in rows.values():
        if other["row_id"] == rid:
            continue
        ja = canon(other.get("japanese"))
        exact = any(ja == canon(p + tag_body(CLAUSES[cid])) for p in prefixes)
        rel = tag_body(other.get("japanese")) == body
        if not (exact or rel):
            continue
        for ans in other.get("answers") or []:
            item = dict(row_id=other["row_id"], rule_key=ans.get("rule_key"),
                        record_id=ans.get("record_id"), raw_value=ans.get("raw_value"),
                        field_path=ans.get("field_path"),
                        reference_field=other.get("reference_field"))
            if exact and other.get("reference_field") == "pattern0":
                primary.append(item)
            elif exact and other.get("reference_field") == "skilltext":
                secondary.append(item)
            if rel:
                relaxed.append(item)
    return primary, secondary, relaxed


def _same_signature_count(tab, record):
    """同签名的其他记录数（同值异记录披露；按记录绑定，不按值配对）。

    签名取该记录的**全部** ``skillparam*`` 键值（不只绑定槽），因此
    「同值异记录」的计数与预检口径一致（7250 四槽签名 253 条；30310 三槽签名 3 条）。
    """
    bound_type = record.get("skillid0")
    sig = {k: v for k, v in record.items() if k.startswith("skillparam")}
    n = 0
    for rec in tab["skills_all"]:
        if rec.get("skillid0") != bound_type:
            continue
        if {k: v for k, v in rec.items() if k.startswith("skillparam")} == sig:
            n += 1
    return n


# ---------------------------------------------------------------- 单行判定

def evaluate(data, cid, row, rows=None, tab=None, chain=None):
    """单行判定（不写入）。返回 dict(accepted, rejection, answers, gates, detail)。"""
    rid = row.get("row_id")
    if cid in ZERO_TOUCH_CIDS:
        return {"accepted": False, "rejection": "ZERO_TOUCH_CID"}
    adm = ADMITTED.get(rid)
    if adm is None:
        return {"accepted": False, "rejection": "NOT_IN_BATCH_SCOPE"}
    if adm["cid"] != cid:
        return {"accepted": False, "rejection": "CID_MISMATCH"}
    tab = tab or tables(data)
    rows = rows if rows is not None else {rid: row}
    gates = {"row_id": rid, "cid": cid}
    # 1. 行身份
    if canon(row.get("japanese")) != canon(CLAUSES[cid]):
        return {"accepted": False, "rejection": "ROW_TEXT_NOT_CLAUSE", "gates": gates}
    denju = tab["denju"].get(cid)
    if denju is None:
        return {"accepted": False, "rejection": "DENJU_RECORD_MISSING", "gates": gates}
    stext = denju[1].get("stext") or ""
    if canon(row.get("context_text")) != canon(stext):
        return {"accepted": False, "rejection": "CONTEXT_TEXT_MISMATCH", "gates": gates}
    first_sentence = stext.split("。")[0] + "。"
    gates["first_sentence_matches_row"] = canon(first_sentence) == canon(row.get("japanese"))
    if not gates["first_sentence_matches_row"]:
        return {"accepted": False, "rejection": "ROW_NOT_FIRST_SENTENCE", "gates": gates}
    # 2. 同层
    src = row.get("source") or {}
    gates["row_source"] = {k: src.get(k) for k in
                           ("record_key", "source_key", "layer", "json_pointer")}
    if src.get("layer") != "CACHE" or src.get("source_key") != "CACHE/denju.data5.json.raw":
        return {"accepted": False, "rejection": "ROW_LAYER_NOT_CACHE", "gates": gates}
    # 3. 链可达
    if chain is None:
        chain, err = chain_of(tab, cid, adm)
        if err:
            return {"accepted": False, "rejection": err, "gates": gates}
    gates.update(pattern_id=chain["pattern_id"], layer=chain["layer"],
                 slots=[c["slot"] for c in chain["children"]],
                 child_ids=[c["skillid"] for c in chain["children"]],
                 child_types=[c["type"] for c in chain["children"]])
    # 4. 链形状与冻结值
    if chain["pattern_id"] != adm["pattern_id"]:
        return {"accepted": False, "rejection": "PATTERN_ID_DRIFT",
                "detail": {"expected": adm["pattern_id"],
                           "actual": chain["pattern_id"]}, "gates": gates}
    if [c["skillid"] for c in chain["children"]] != adm["chain_ids"]:
        return {"accepted": False, "rejection": "CHAIN_IDS_DRIFT",
                "detail": {"expected": adm["chain_ids"],
                           "actual": [c["skillid"] for c in chain["children"]]},
                "gates": gates}
    if [c["type"] for c in chain["children"]] != adm["chain_types"]:
        return {"accepted": False, "rejection": "CHAIN_TYPES_DRIFT",
                "detail": {"expected": adm["chain_types"],
                           "actual": [c["type"] for c in chain["children"]]},
                "gates": gates}
    bound = chain["children"][0]
    if bound["type"] != adm["bound_type"]:
        return {"accepted": False, "rejection": "BOUND_TYPE_DRIFT", "gates": gates}
    present = sorted(k for k in bound["params"] if k.startswith("skillparam"))
    gates["bound_present_params"] = present
    gates["unbound_params"] = {f: bound["params"].get(f) for f in adm["unbound_params"]}
    values, states = {}, {}
    for f in adm["fields"]:
        raw = bound["params"].get(f)
        states[f] = raw_state(raw, present=f in bound["params"])
        values[f] = raw
    gates["bound_values"] = values
    gates["bound_value_states"] = states
    # 空值分档先于形状门：缺失/null/非有限/负值/真零各有独立拒绝原因，不并成「形状不符」。
    for f in adm["fields"]:
        if states[f] in ("MISSING", "NULL", "NON_FINITE", "NEGATIVE", "ZERO"):
            return {"accepted": False, "rejection": "BOUND_VALUE_%s" % states[f],
                    "detail": {f: values[f]}, "gates": gates}
    if present != sorted(adm["active_params"]):
        return {"accepted": False, "rejection": "BOUND_SLOT_SHAPE_DRIFT",
                "detail": {"expected": sorted(adm["active_params"]), "actual": present},
                "gates": gates}
    if values != adm["values"]:
        return {"accepted": False, "rejection": "BOUND_VALUE_DRIFT",
                "detail": {"expected": adm["values"], "actual": values}, "gates": gates}
    # 5. 同卡基础档逐位相等
    base_tier = base_tier_of(tab, cid, adm, chain)
    gates["base_tier"] = {k: v for k, v in base_tier.items() if k != "chara_params"}
    if not base_tier.get("chara_present") or base_tier.get("base_tier_pattern") != \
            adm["base_tier_pattern"]:
        return {"accepted": False, "rejection": "BASE_TIER_POINTER_DRIFT", "gates": gates}
    if not base_tier.get("base_tier_unique") or not base_tier.get("base_tier_same_sequence"):
        return {"accepted": False, "rejection": "BASE_TIER_SEQUENCE_MISMATCH", "gates": gates}
    if not base_tier.get("chara_ten_slot_match"):
        return {"accepted": False, "rejection": "CHARAINFO_TEN_SLOT_MISMATCH", "gates": gates}
    # 6. 同卡已披露值交叉核（同记录同原值）
    primary, secondary, relaxed = _base_answers(rows, rid, cid, adm)
    gates["base_answers"] = primary
    gates["base_answers_secondary"] = secondary
    want = []
    for f in adm["fields"]:
        want.append((("%s%s" % (T13_RULE_PREFIX, f)) if adm["bound_type"] == 13
                     else T64_RULE_KEY, f))
    missing, mismatched = [], []
    for rule_key, f in want:
        hits = [a for a in primary
                if a.get("rule_key") == rule_key and a.get("record_id") == bound["skillid"]]
        if not hits:
            missing.append(rule_key)
        elif any(a.get("raw_value") != values[f] for a in hits):
            mismatched.append({"rule_key": rule_key,
                               "base_values": [a.get("raw_value") for a in hits],
                               "bound": values[f]})
    gates["base_missing_rule_keys"] = missing
    gates["base_value_conflicts"] = mismatched
    if not primary:
        return {"accepted": False, "rejection": "NO_SAME_CARD_CORROBORATION", "gates": gates}
    if missing:
        return {"accepted": False, "rejection": "BASE_ANSWER_RULE_KEY_MISSING",
                "detail": missing, "gates": gates}
    if mismatched:
        return {"accepted": False, "rejection": "BASE_ANSWER_VALUE_CONFLICT",
                "detail": mismatched, "gates": gates}
    # 7. 排除分支（超共鳴档）
    super_tier = super_tier_of(tab, cid, adm)
    gates["super_tier"] = super_tier
    if not super_tier:
        return {"accepted": False, "rejection": "SUPER_TIER_NOT_FOUND", "gates": gates}
    if any(t["record_id"] == adm["super_tier_record"] and t["values"] != adm["super_tier_values"]
           for t in super_tier) or not any(t["record_id"] == adm["super_tier_record"]
                                           for t in super_tier):
        return {"accepted": False, "rejection": "SUPER_TIER_DRIFT",
                "detail": super_tier, "gates": gates}
    if any(t["values"] == values for t in super_tier):
        return {"accepted": False, "rejection": "SEGMENTS_INDISTINCT", "gates": gates}
    # 8. 既有答案（同键）不重复写：同记录同值＝幂等跳过；同值异记录／同键异值＝只披露
    existing = [a for a in row.get("answers") or []
                if a.get("rule_key") in ({T13_RULE_PREFIX + f for f in adm["fields"]}
                                         if adm["bound_type"] == 13 else {T64_RULE_KEY})]
    gates["existing_same_rule_key"] = [{"rule_key": a.get("rule_key"),
                                        "record_id": a.get("record_id"),
                                        "raw_value": a.get("raw_value")}
                                       for a in existing]
    skipped_keys, disclosures = [], []
    for rule_key, f in want:
        hits = [a for a in existing if a.get("rule_key") == rule_key]
        if not hits:
            continue
        if any(a.get("record_id") == bound["skillid"] and a.get("raw_value") == values[f]
               for a in hits):
            skipped_keys.append(rule_key)
        elif any(a.get("raw_value") == values[f] for a in hits):
            disclosures.append({"rule_key": rule_key,
                                "dedup": "SAME_VALUE_DIFF_RECORD_EXISTING",
                                "existing": [{"record_id": a.get("record_id"),
                                              "raw_value": a.get("raw_value")} for a in hits],
                                "selected": {"record_id": bound["skillid"],
                                             "raw_value": values[f]}})
        else:
            disclosures.append({"rule_key": rule_key,
                                "dedup": "CONFLICT_EXISTING_VALUE",
                                "existing": [{"record_id": a.get("record_id"),
                                              "raw_value": a.get("raw_value")} for a in hits],
                                "selected": {"record_id": bound["skillid"],
                                             "raw_value": values[f]}})
    gates["skipped_existing_rule_keys"] = skipped_keys
    gates["disclosures"] = disclosures
    if len(skipped_keys) + len(disclosures) == len(want):
        return {"accepted": False, "rejection": "ALREADY_ANSWERED",
                "gates": gates, "detail": disclosures}
    # 出答案（只为本行尚无同 rule_key 答案的字段）
    answers = []
    for (attr, field, kind) in (SLOTS_T13 if adm["bound_type"] == 13 else (SLOT_T64,)):
        if field not in adm["fields"]:
            continue
        rule_key = ("%s%s" % (T13_RULE_PREFIX, field) if adm["bound_type"] == 13
                    else T64_RULE_KEY)
        if rule_key in skipped_keys or any(d["rule_key"] == rule_key for d in disclosures):
            continue
        raw = values[field]
        converted = _answer_for(adm["bound_type"], field, raw, bound["record"])
        if converted is None:
            return {"accepted": False, "rejection": "RULE_UNAVAILABLE",
                    "detail": rule_key, "gates": gates}
        value = _value_text(kind, raw, converted)
        unbound_txt = ("" if not adm["unbound_params"] else
                       "同记录未绑定槽 %s（语义未确认，不猜）；"
                       % "/".join("%s=%s" % (f, _num(bound["params"].get(f)))
                                  for f in adm["unbound_params"]))
        note = ("slot0（denju 链 skillid0，type%d）的真实字段；该记录与同卡基础档 "
                "charainfo.pattern0（pattern %s）执行的子记录序列逐位相同，"
                "同规则键同记录同原值已在同卡基础档行披露（不新增唯一数值）。"
                "超共鳴档 pattern %s（记录 %s）值 %s 为排除分支，不并入本行。"
                "链内其余槽只登记不绑定；%s暴击项（t116 在 rules 中 0 键）保持未知。%s"
                % (adm["bound_type"], adm["base_tier_pattern"], adm["super_tier_pattern"],
                   adm["super_tier_record"],
                   "/".join(_num(adm["super_tier_values"][f]) for f in adm["fields"]),
                   unbound_txt, LIMIT))
        answer = {
            "value": value,
            "quantity_kind": converted.get("quantity_kind"),
            "unit": converted.get("unit"),
            "value_text": converted.get("value_text"),
            "raw_value": raw,
            "effective_float32": _f32(raw),
            "quantitative": True,
            "numeric_source": converted.get("numeric_source"),
            "numeric_evidence": converted.get("numeric_evidence"),
            "association_evidence": "推断",
            "evidence_scope": EVIDENCE_SCOPE,
            "answer_status": converted.get("answer_status"),
            "rule_key": rule_key,
            "table": "bossskill",
            "record_id": bound["skillid"],
            "layer": "CACHE",
            "field_path": "/" + field,
            "source": _source(bound, chain, field, adm),
            "rule_status": converted.get("rule_status"),
            "conversion": converted.get("conversion"),
            "base_definition": converted.get("base_definition"),
            "conditions": converted.get("conditions"),
            "rule_limits": converted.get("rule_limits"),
            "condition_label": ("传授（denju）发动期间、共鳴基础档生效时"
                                "（pattern %s 执行列表的 skillid0）" % chain["pattern_id"]),
            "target": "味方全体（实际接受者受各处理器成员列表筛选）",
            "binding": {"c7_p2_denju_binding": _marker(
                adm, chain, bound, base_tier, super_tier, values, field, rule_key,
                primary, secondary, relaxed, existing, tab)},
            "evidence": EVIDENCE[:],
            "note": note,
        }
        if kind == "defense":
            answer["exact_formula"] = ("trunc(float32(float32(normalAtk)×float32(%s×Chain)))"
                                       % _num(raw))
        answers.append(answer)
    if not answers:
        return {"accepted": False, "rejection": "NO_FIELD_IN_SCOPE", "gates": gates}
    return {"accepted": True, "rejection": None, "answers": answers, "gates": gates,
            "detail": None}


def _value_text(kind, raw, converted):
    num = _num(raw)
    if kind == "attack":
        return HUMAN["attack"].format(s=_num(raw * 100))
    if kind == "move":
        return HUMAN["move"].format(s=_num(raw * 100))
    if kind == "duration":
        return HUMAN["duration"].format(s=num)
    if kind == "defense":
        return HUMAN["defense"].format(r=num, p=_num(raw * 10))
    if kind == "heal":
        return HUMAN["heal"].format(r=num)
    return converted.get("value_text") or num


def _answer_for(effect_type, field, raw, record):
    """既有规则的只读换算；t64 的 quantity_kind/value_text 用 rules.json 原文。

    ``rules.convert`` 里 t64 仍套用通用 ``skill_base_value`` 模板（「消费点未定」），
    与后登记的 ``rules.json`` 该键（reactive heal 基值、写入 setReactiveHeal）不一致；
    本模块**不改 rules.py**，只按 rules.json 的键记录取语义文本，并保留其 limits。
    """
    import rules as R
    converted = R.answer_for("bossskill", effect_type, "/" + field, raw, record,
                             source_layer="CACHE")
    if converted is None:
        return None
    rule = R.rule_for("bossskill", effect_type, "/" + field) or {}
    out = dict(converted)
    out.update(rule_status=rule.get("status"), conversion=rule.get("conversion"),
               base_definition=rule.get("base_definition"),
               conditions=rule.get("applicability"), rule_limits=rule.get("limits"),
               numeric_source="复用既有局部规则；记录归属为推断")
    out["numeric_evidence"] = "确认" if effect_type == 64 else "推断"
    if effect_type == 64:
        # rules.json 该键的本体语义（reactive heal），覆盖 convert 的旧通用模板文本。
        out["quantity_kind"] = "回复量输入（reactive heal 基值）"
        out["unit"] = rule.get("unit")
        out["value_text"] = rule.get("conversion")
        out["answer_status"] = "CONFIRMED_FORMULA_ONLY"
    return out


def _source(bound, chain, field, adm):
    pointer = "/bossinfo/bossskill/%d" % bound["index"]
    return {
        "table": "bossskill", "record_id": bound["skillid"], "layer": "CACHE",
        "field_path": "/" + field,
        "source_key": "CACHE/bossinfo.data5.json.raw",
        "original_file": "output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw",
        "json_pointer": pointer,
        "field": "/" + field,
        "field_json_pointer": pointer + "/" + field,
        "record_key": "CACHE/bossinfo.data5.json.raw#%s" % pointer,
        "source_resolution": EXACT,
        "note": ("按解码 JSON 的 bossskill.skillid 唯一命中；经本行 denju.patternid0 原始链"
                 "（pattern %s 的 skillid0）定源，且与同卡 charainfo.pattern0 基础档序列"
                 "逐位相同；不是同文复制" % chain["pattern_id"]),
    }


def _marker(adm, chain, bound, base_tier, super_tier, values, field, rule_key,
            primary, secondary, relaxed, existing, tab):
    body = tag_body(CLAUSES[adm["cid"]])
    return {
        "scope": SCOPE,
        "module": MODULE_VERSION,
        "cid": adm["cid"],
        "row_id": adm["row_id"],
        "rule_key": rule_key,
        "field_path": "/" + field,
        "record_id": bound["skillid"],
        "layer": "CACHE",
        "pattern_id": chain["pattern_id"],
        "pattern_slot": "patternid0",
        "bound_slot": "skillid0",
        "bound_type": adm["bound_type"],
        "denju_record": {"json_pointer": "/denju/%d" % chain["denju_index"]},
        "bound_values": dict(values),
        "unbound_params": {f: bound["params"].get(f) for f in adm["unbound_params"]},
        "base_tier": {
            "pointer": adm["base_tier_pointer"],
            "pattern_id": base_tier.get("base_tier_pattern"),
            "slots": base_tier.get("base_tier_slots"),
            "same_sequence": base_tier.get("base_tier_same_sequence"),
            "ten_slot_match": base_tier.get("chara_ten_slot_match"),
        },
        "base_answers": primary,
        "base_answers_secondary": secondary,
        "excluded_branches": {
            "super_tier": super_tier,
            "unbound_slots": adm["unbound_slots"],
            "unbound_note": adm["unbound_note"],
            "disposition": "EXCLUDED_NOT_BOUND",
        },
        "same_value_other_records": {
            "signature": {f: values[f] for f in adm["fields"]},
            "count": _same_signature_count(tab, bound["record"]),
            "signature_full": {k: v for k, v in bound["record"].items()
                               if k.startswith("skillparam")},
            "note": "同值异记录：按记录 id 绑定，不按值配对",
        },
        "crit_unknown": {
            "type116_rule_keys": 0,
            "claims": [],
            "note": ("本行句面无暴击项；bossskill|116|* 在 rules 中 0 键，"
                     "不借 type13/2012 其他链补"),
        },
        "r8b_sensitivity": {
            # 只用 JSON 原生类型（list 而非 tuple）：card_page.validate 要求
            # json.loads(HTML payload) == card 逐值相等，tuple 在往返后变 list 会失败。
            "tag_normalized_rows": sorted([list(p) for p in
                                           {(a.get("row_id"), a.get("rule_key"))
                                            for a in relaxed}]),
            "note": ("剥离句首【…】后的同文匹配只作敏感性披露，**不是准入判据**；"
                     "准入只认「已枚举共鳴前缀 + 本行句身」的逐字同文行"),
            "body": body,
        },
        "existing_same_rule_key": existing,
        "association": "推断",
        "native_evidence": ("none（本批不新增原生点；沿用既有 CheckEntry item(0) 顺序证据与 "
                            "t13/t64 已确认规则）"),
    }


def _append(row, answers):
    """写入答案与行级标记（幂等）。返回新增条数。"""
    key = lambda a: (a.get("rule_key"), a.get("record_id"), a.get("field_path"))
    existing = {key(a) for a in row.get("answers") or []}
    added = 0
    for answer in answers:
        if key(answer) in existing:
            continue
        row.setdefault("answers", []).append(answer)
        existing.add(key(answer))
        added += 1
    if not added:
        return 0
    row["row_class"] = "A"
    row["evidence"] = "推断"
    row["evidence_label"] = ("推断（C7-B2 传授同记录绑定：链定档＋同记录＋同卡基行逐位相等；"
                            "超共鳴档为排除分支）")
    row["partial"] = True
    row["numeric_evidence"] = "推断"
    row["association_evidence"] = "推断"
    scopes = row.get("evidence_scope") or []
    if isinstance(scopes, str):
        scopes = [scopes]
    row["evidence_scope"] = list(dict.fromkeys(list(scopes) + [EVIDENCE_SCOPE]))
    reasons = [r for r in (row.get("unknown_reasons") or []) if r not in _STALE_REASONS]
    binding = answers[0]["binding"]["c7_p2_denju_binding"]
    if binding["bound_type"] == 13:
        reasons.append("C7-B2：攻击力／固定防御系数／移动速度／持续游戏秒 4 项已按 denju "
                       "原始链 slot0（type13）同记录绑定出值；句内「敵の攻撃力と防御力を下げる」"
                       "2 项仍未知；超共鳴档为排除分支；暴击项 t116 在 rules 中 0 键。")
    else:
        reasons.append("C7-B2：受击回复（reactive heal 基值）1 项已按 denju 原始链 slot0"
                       "（type64）同记录绑定出值；同行另 3 条效果仍未知；超共鳴档为排除分支；"
                       "暴击项 t116 在 rules 中 0 键。")
    row["unknown_reasons"] = list(dict.fromkeys(reasons))
    marker = row.setdefault(MARKER_KEY, {
        "scope": SCOPE, "module": MODULE_VERSION, "cid": binding["cid"],
        "row_id": binding["row_id"], "pattern_id": binding["pattern_id"],
        "bound_slot": binding["bound_slot"], "bound_type": binding["bound_type"],
        "bound_values": binding["bound_values"], "base_tier": binding["base_tier"],
        "unbound_params": binding.get("unbound_params"),
        "base_answers": binding["base_answers"],
        "excluded_branches": binding["excluded_branches"],
        "same_value_other_records": binding["same_value_other_records"],
        "crit_unknown": binding["crit_unknown"],
        "r8b_sensitivity": binding["r8b_sensitivity"],
        "bindings": []})
    for answer in answers:
        m = answer["binding"]["c7_p2_denju_binding"]
        marker["bindings"].append({"rule_key": m["rule_key"], "field_path": m["field_path"],
                                   "record_id": m["record_id"],
                                   "values": m["bound_values"]})
    marker["bindings"] = list({(b["rule_key"], b["field_path"]): b
                               for b in marker["bindings"]}.values())
    return added


def _merge_disclosure(row, text, record_id, raw_value, dedup, rule_key=None):
    """只写行级披露（同值异记录／同键异值）：不新增答案、不改写既有值。"""
    marker = row.setdefault(MARKER_KEY, {
        "scope": SCOPE, "module": MODULE_VERSION, "row_id": row.get("row_id"),
        "bindings": []})
    marker.setdefault("disclosures", []).append({
        "dedup": dedup, "rule_key": rule_key,
        "record_id": record_id, "raw_value": raw_value,
        "existing_answers": [{"rule_key": a.get("rule_key"),
                              "record_id": a.get("record_id"),
                              "raw_value": a.get("raw_value")}
                             for a in row.get("answers") or []],
        "disclosure": text})


def apply_to_groups(data, cid, groups):
    """正式页消费：为 2 行冻结准入表写 slot0 绑定答案（不覆盖/不删除既有答案）。"""
    report = {"scope": SCOPE, "cid": cid, "evaluated": 0, "answers_added": 0,
              "additions": [], "rejections": [], "skipped_existing": 0,
              "marker_only": 0, "out_of_scope": True}
    if cid not in ADMITTED_CIDS:
        return report
    report["out_of_scope"] = False
    if cid in ZERO_TOUCH_CIDS:
        report["zero_touch"] = True
        report["rejections"].append({"reason": "ZERO_TOUCH_CID", "cid": cid})
        return report
    rows = _rows(groups)
    tab = tables(data)
    for rid, adm in ADMITTED.items():
        if adm["cid"] != cid:
            continue
        row = rows.get(rid)
        if row is None:
            report["rejections"].append({"row_id": rid, "reason": "ROW_NOT_FOUND"})
            continue
        report["evaluated"] += 1
        res = evaluate(data, cid, row, rows=rows, tab=tab)
        if not res["accepted"]:
            if res["rejection"] == "ALREADY_ANSWERED":
                disclosures = res.get("detail") or []
                if disclosures:
                    for d in disclosures:
                        text = ("本行已有同 rule_key 答案（%s）；冻结准入表选中的记录 %s 原值 %s，"
                                "判定 %s：不新增答案、不改写既有值，只披露。"
                                % ("、".join("%s=%s" % (a["record_id"], a["raw_value"])
                                             for a in d["existing"]),
                                   d["selected"]["record_id"], _num(d["selected"]["raw_value"]),
                                   d["dedup"]))
                        _merge_disclosure(row, text, d["selected"]["record_id"],
                                          d["selected"]["raw_value"], d["dedup"], d["rule_key"])
                    report["marker_only"] += 1
                    report.setdefault("markers", []).append(
                        {"row_id": rid,
                         "dedup": disclosures[0]["dedup"],
                         "disclosures": disclosures})
                else:
                    report["skipped_existing"] += 1
                    report.setdefault("markers", []).append(
                        {"row_id": rid, "dedup": "ALREADY_PRESENT_SAME"})
            else:
                report["rejections"].append({"row_id": rid, "reason": res["rejection"],
                                             "detail": res.get("detail")})
            continue
        added = _append(row, res["answers"])
        for d in (res.get("gates") or {}).get("disclosures") or []:
            text = ("本行已有同 rule_key 答案（%s）；冻结准入表选中的记录 %s 原值 %s，判定 %s："
                    "不新增答案、不改写既有值，只披露。"
                    % ("、".join("%s=%s" % (a["record_id"], a["raw_value"])
                                 for a in d["existing"]),
                       d["selected"]["record_id"], _num(d["selected"]["raw_value"]),
                       d["dedup"]))
            _merge_disclosure(row, text, d["selected"]["record_id"],
                              d["selected"]["raw_value"], d["dedup"], d["rule_key"])
            report["marker_only"] += 1
        if added:
            report["answers_added"] += added
            for answer in res["answers"]:
                report["additions"].append({
                    "row_id": rid, "record_id": answer["record_id"],
                    "rule_key": answer["rule_key"],
                    "field_path": answer["field_path"],
                    "raw_value": answer["raw_value"]})
        else:
            report["skipped_existing"] += 1
    return report


def _main(argv=None):
    import argparse
    import json
    ap = argparse.ArgumentParser(description="C7-B2 传授同记录绑定：只读探针（单行/单卡）")
    ap.add_argument("--cid", type=int)
    ap.add_argument("--row-id")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(".").resolve()
    import card_page_data as D
    cids = ([int(str(args.row_id).split("-", 1)[0])] if args.row_id
            else [args.cid] if args.cid else sorted(ADMITTED_CIDS))
    data = D.Inputs(root, cids)
    out = []
    for cid in cids:
        card = json.loads((root / "output/character_skills/pages" / str(cid) / "card.json")
                          .read_text(encoding="utf-8"))
        rows = _rows(card.get("groups") or [])
        targets = [r for r in ADMITTED.values() if r["cid"] == cid]
        if args.row_id:
            targets = [r for r in targets if r["row_id"] == args.row_id]
        for adm in targets:
            row = rows.get(adm["row_id"]) or {"row_id": adm["row_id"]}
            res = evaluate(data, cid, row, rows=rows)
            out.append({
                "row_id": adm["row_id"], "accepted": res["accepted"],
                "rejection": res["rejection"],
                "records": sorted({a["record_id"] for a in res.get("answers") or []}),
                "values": [{"rule_key": a["rule_key"], "raw_value": a["raw_value"]}
                           for a in res.get("answers") or []],
                "gates": res.get("gates")})
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for item in out:
            print(("OK  " if item["accepted"] else "REJ "), item["row_id"],
                  item.get("records"),
                  [v["raw_value"] for v in item.get("values") or []],
                  item.get("rejection") or "")
    return 0 if all(i["accepted"] for i in out) else 1


if __name__ == "__main__":
    raise SystemExit(_main())
