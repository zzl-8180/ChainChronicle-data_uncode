"""charainfo special-move parameters: equivalence + answers (P2 batch 1, items 2-5).

Turns the APK-era character special-move parameter block (``charainfo.skillparam0..9``
plus ``charainfo.skillid[0]``) into answers, using the boss rule set that is already
confirmed -- but only where the record-level equivalence actually holds.

Outputs (``output/character_skills/charainfo_params/``):

* ``equivalence.json``   -- the rule itself: premise, native evidence, class table.
* ``characters.jsonl``   -- one row per roster character: class, matched boss
                            records, both sides' raw parameter values, source.
* ``exceptions.jsonl``   -- the in-universe characters the transfer does *not*
                            cover, with the class and the concrete evidence.
* ``answers.jsonl``      -- the field-level answers produced through the gate.
* ``summary.json``       -- counts, the dual caliber, and the delta against the
                            captured P1 baseline (when present).
* ``README.md``.

Run with ``--snapshot-baseline`` once, against the pre-change ``profiles/``
outputs, to capture the "before" numbers used for the delta report.
"""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import common as C  # noqa: E402
import equivalence as EQ  # noqa: E402
import rules as R  # noqa: E402

OUT = C.ROOT / "output" / "character_skills" / "charainfo_params"
PROFILES = C.ROOT / "output" / "character_skills" / "profiles"
WORK = C.ROOT / "work" / "character_skills_p2"
BASELINE = WORK / "profiles_baseline_before_charainfo.json"
NATIVE_INDEX = C.ROOT / "output" / "character_skills" / "charainfo_types" / "type_dispatch_index.json"

SLOTS_ALL = list(range(10))


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_baseline():
    """Capture the pre-change profile numbers for the delta report."""
    summary_path = PROFILES / "summary.json"
    if not summary_path.exists():
        raise SystemExit("找不到 profiles/summary.json，无法取基线")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    per_char = {}
    with (PROFILES / "characters.csv").open(encoding="utf-8") as fh:
        import csv
        for row in csv.DictReader(fh):
            per_char[row["cid"]] = {
                "status": row.get("status"),
                "unexplained_fields": int(row.get("unexplained_fields") or 0),
                "answers": int(row.get("answers") or 0),
            }
    WORK.mkdir(parents=True, exist_ok=True)
    payload = {"source": "output/character_skills/profiles/summary.json",
               "source_sha256": _sha256(summary_path),
               "summary": summary, "characters": per_char}
    C.write_json(BASELINE, payload)
    print(json.dumps({"baseline": str(BASELINE), "characters": len(per_char)},
                     ensure_ascii=False))


def _answers_for(cid, verdict):
    """Apply the boss rules to this character's charainfo parameters, through the gate."""
    rec, layer = EQ.tables()["charainfo"].get(cid)
    if rec is None or not verdict.get("applicable"):
        return []
    etype = verdict.get("skillid0")
    out = []
    for field in [f"skillparam{i}" for i in SLOTS_ALL] + list(EQ.FLAG_FIELDS):
        value = rec.get(field)
        if value is None or isinstance(value, bool):
            continue
        ok, reason = EQ.field_allowed(cid, "/" + field)
        if not ok:
            continue
        rule = R.rule_for("charainfo", etype, "/" + field)
        if rule is None:
            continue
        ans = R.answer_for("charainfo", etype, "/" + field, value, rec)
        out.append({
            "cid": cid,
            "table": "charainfo",
            "effect_type": etype,
            "field_path": "/" + field,
            "raw_value": value,
            "quantity_kind": ans.get("quantity_kind"),
            "value_text": ans.get("value_text"),
            "unit": ans.get("unit"),
            "answer_status": ans.get("answer_status"),
            "evidence_scope": "BY_TYPE_EXTRAPOLATED",
            "equivalence_class": verdict.get("class"),
            "equivalence_gate": reason,
            "matched_bossskill": verdict.get("matched_bossskill"),
            "rule_source": "output/character_skills/profiles/rules.json",
        })
    return out


def main():
    C.enable_utf8_console()
    OUT.mkdir(parents=True, exist_ok=True)

    idx = EQ.index()
    roster = {row["cid"]: row for row in C.roster()}

    rows = []
    answers = []
    for cid, verdict in sorted(idx.items()):
        row = dict(verdict)
        row["name"] = (roster.get(cid) or {}).get("name")
        row["answers"] = _answers_for(cid, verdict)
        answers += row["answers"]
        rows.append(row)
    C.write_jsonl(OUT / "characters.jsonl", rows)

    exceptions = [r for r in rows if r["class"] in
                  ("X0_TYPE_ZERO_UNSET", "X1_VALUES_DIFFER", "X2_ALL_SIX_SLOTS_EMPTY",
                   "NOT_AMONG_OWN_PATTERN_TYPES")]
    C.write_jsonl(OUT / "exceptions.jsonl", exceptions)
    C.write_jsonl(OUT / "answers.jsonl", answers)

    # ---- dual caliber ------------------------------------------------------
    page_sum = len(answers)
    unique = len({(a["cid"], a["field_path"]) for a in answers})

    # ---- delta against the captured P1 baseline ---------------------------
    delta = None
    if BASELINE.exists():
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        per = base.get("characters") or {}
        by_cid = collections.defaultdict(int)
        for a in answers:
            by_cid[str(a["cid"])] += 1
        changed = [cid for cid, n in by_cid.items()
                   if n and (per.get(cid) or {}).get("status") == "仅未知"]
        # every entry in by_cid is a *new* charainfo answer, so this is the count of
        # characters that gained at least one answer in this batch
        gained = [cid for cid, n in by_cid.items() if n]
        delta = {
            "baseline": str(BASELINE.relative_to(C.ROOT)).replace("\\", "/"),
            "baseline_summary_sha256": base.get("source_sha256"),
            "baseline_answers_page_sum": base["summary"].get("totals", {}).get("rule_answers"),
            "baseline_answers_unique_records":
                base["summary"].get("totals", {}).get("rule_answers_unique_records"),
            "baseline_unexplained_fields": base["summary"].get("totals", {}).get("unexplained_fields"),
            "baseline_characters_partial": (base["summary"].get("status_counts") or {}).get("部分"),
            "baseline_characters_unknown_only": (base["summary"].get("status_counts") or {}).get("仅未知"),
            "new_charainfo_answers": page_sum,
            "charainfo_unexplained_drop": page_sum,
            "charainfo_unexplained_drop_note": (
                "每个新答案恰好替代一条原先未解释的 charainfo 参数记录，故两数相等"),
            "characters_gaining_first_answer": len(changed),
            "characters_gaining_first_answer_note": (
                "这些角色在**基线快照（P1 期）**中是『仅未知』。基线取自 P1，因此该数包含 P2 各批"
                "累积（P2 第 1 批为 0：当时获得 charainfo 答案的角色此前已因 bossskill 等表有答案；"
                "P2 第 8 批后有角色经本门控首次获得答案，逐条原因见 "
                "output/character_skills/boss_attack_types/p8_increment.json 的 unknown_reachability）"),
            "characters_with_more_answers": len(gained),
            "characters_with_more_answers_note": (
                "本批至少新增一条 charainfo 答案的角色数；这些角色此前已因 bossskill 等表有答案，"
                "故角色状态（部分）不变，变化体现在答案条数与未解释字段数上"),
        }
    else:
        delta = {"note": "未捕获 P1 基线（work/character_skills_p2/profiles_baseline_before_charainfo.json 不存在）；"
                         "本次不报增量，请先用 --snapshot-baseline 取基线"}

    native = {}
    if NATIVE_INDEX.exists():
        ni = json.loads(NATIVE_INDEX.read_text(encoding="utf-8"))
        native = {
            "type_dispatch_index": "output/character_skills/charainfo_types/type_dispatch_index.json",
            "supported_type_range": ni["switch"]["supported_types"],
            "bound_instruction": ni["switch"]["bound_instruction"],
            "handler_of_type_13": (ni["handler_slots"].get("13") or {}).get("handler"),
            "handler_of_type_27": (ni["handler_slots"].get("27") or {}).get("handler"),
        }

    C.write_json(OUT / "equivalence.json", {
        "premise": ("charainfo.skillid[0] 与 bossskill.skillid0 同域；"
                    "BtlCharaUtil.CharaParamToBossSkill 把 charaParameter 的 skillid[0] 与 "
                    "skillparam0..9 按下标对齐写入 BattleBossSkill，调用方为 "
                    "CharaInfoCharaModel.PlaySpMotion 与 BtlCharaUtil.GetDenjuSkill"),
        "native_evidence": native,
        "native_detail": "output/character_skills/charainfo_types/native_checks.json",
        "universe_definition": EQ.summary()["universe_definition"],
        "classes": EQ.summary()["classes"],
        "class_meanings": {
            "E0": "skillparam1..6 严格逐值相同（R2 复核钉死的口径）→ 可迁移，槽位 1..6",
            "E1": "float32 取整后相同（JSON 表示差异）→ 可迁移，槽位 1..6",
            "E2": "把 charainfo 缺省槽读作 0.0 后相同 → 可迁移，槽位 1..6",
            EQ.NO_PATTERN_FALLBACK: (
                "自身 pattern0..8 在 boss 主表中没有可达 bossskill（执行用 pattern 列表为空）→ "
                "战斗执行走 _CreateExecSkillList 的 pattern==0 兜底构造，把本记录 skillid[0]／skillparam0..9 "
                "经 CharaParamToBossSkill(0x13aa390) 变成执行用 BattleBossSkill，由同一 ExecSkill 派发 "
                "→ 槽位 0..9＋skillflag 由构造直接携带，本记录原值即执行值（P2 第 9 批）"),
            "X0_TYPE_ZERO_UNSET": "类型槽原值 0，按类型对齐无意义 → 不迁移",
            "X1_VALUES_DIFFER": ("两侧数值确有不同 → 不迁移，两侧原值都保留；P2 第 9 批判定：自身 pattern "
                                 "可解析，执行取 pattern 侧，本记录副本不是执行值"),
            "X2_ALL_SIX_SLOTS_EMPTY": "charainfo 侧 1..6 全空 → 无可解释值",
            "NOT_AMONG_OWN_PATTERN_TYPES": ("skillid[0] 不在自身 pattern 的 boss 类型集合内 → 无可对齐记录；"
                                            "执行取 pattern 侧，本记录副本不是执行值"),
        },
        "slot_scope": ("E0/E1/E2 默认只覆盖 skillparam1..6；当十槽归一后同样相等时扩展到 "
                       "skillparam0/7/8/9（all_ten_slots_equal）。F0 由构造直接覆盖 0..9 与 "
                       "skillflag0_0/0_1/1_0/1_1（BattleBossSkill 逐字段复制）"),
        "evidence_scope": "BY_TYPE_EXTRAPOLATED（沿用现有两类证据范围，未新增第三类）",
        "not_transferable": ("X1／X0／X2／NOT_AMONG 一律不产生数值答案；F0 产生答案（路径证据见 "
                             "output/character_skills/cp_paths/path_evidence.json）"),
    })
    C.write_json(OUT / "summary.json", {
        "universe_definition": EQ.summary()["universe_definition"],
        "classes": EQ.summary()["classes"],
        "applicable_characters": EQ.summary()["applicable_characters"],
        "applicable_characters_note": EQ.summary()["applicable_characters_note"],
        "value_comparison_universe": EQ.summary()["value_comparison_universe"],
        "strict_1_6_exact_r2_caliber": EQ.summary()["strict_1_6_exact_r2_caliber"],
        "all_ten_slots_equal_characters": EQ.summary()["all_ten_slots_equal"],
        "new_answers_page_sum": page_sum,
        "new_answers_unique_records": unique,
        "new_answers_dual_caliber_note": (
            "charainfo 记录每个 cid 唯一，页求和与唯一记录数相同（与共享 bossskill 记录的双口径不同）"),
        "answers_by_type": dict(collections.Counter(a["effect_type"] for a in answers).most_common()),
        "answers_by_field": dict(collections.Counter(a["field_path"] for a in answers).most_common()),
        "answers_by_equivalence_class":
            dict(collections.Counter(a["equivalence_class"] for a in answers).most_common()),
        "delta_vs_p1_baseline": delta,
    })

    readme = f"""# charainfo 必杀技参数：等价规则与答案（P2 第 1 批 项2–5）

只由 `scripts/character_skills/charainfo_params.py` 生成。规则层复用 `profiles/rules.json`
（origin 可溯），不新增语义。

## 什么时候可以把 boss 规则用到角色记录上

原生依据（两条，对应两类可迁移判定）：

1. `BtlCharaUtil.CharaParamToBossSkill` 把角色记录的 `skillid[0]`、`skillparam0..9`
   **按下标对齐**写入 `BattleBossSkill`（调用方 `CharaInfoCharaModel.PlaySpMotion`、
   `BtlCharaUtil.GetDenjuSkill`）。这证明**槽位语义**可以迁移，但**数值**要逐角色核对，
   因此本目录先做记录级等价判定，再谈答案。
2. **执行侧路径（P2 第 9 批）**：自 CharacterFactory/Panel 到 `bhSkill.CreateExecSkillList`
   的两条分支——自身 pattern 可解析时执行 pattern（boss 主表）的 bossskill；
   pattern 列表为空时执行 `CharaParamToBossSkill(0x13aa390)` 用本记录原值构造的
   `BattleBossSkill`（`pattern==0` 兜底分支）。因此**无 pattern 的角色**（F0）无需数值比较，
   本记录原值即执行值；**有 pattern 的角色**（E0/E1/E2 数值相同、X0/X1 不同）执行取 pattern 侧。
   路径逐指令证据见 `../cp_paths/path_evidence.json`。

类别（universe = {EQ.summary()['universe_definition']}，共 {sum(EQ.summary()['classes'].values())} 角色）：

| 类 | 判据 | 角色数 | 是否迁移 |
|---|---|---|---|
| E0 | skillparam1..6 严格逐值相同 | {EQ.summary()['classes'].get('E0')} | 是，槽位 1..6 |
| E1 | float32 取整后相同 | {EQ.summary()['classes'].get('E1')} | 是，槽位 1..6 |
| E2 | 缺省槽读作 0.0 后相同 | {EQ.summary()['classes'].get('E2')} | 是，槽位 1..6 |
| F0 | 自身 pattern 无可达 boss 技能（执行走兜底构造） | {EQ.summary()['classes'].get(EQ.NO_PATTERN_FALLBACK)} | 是，槽位 0..9＋flag |
| X0 | 类型槽原值 0 | {EQ.summary()['classes'].get('X0_TYPE_ZERO_UNSET')} | 否 |
| X1 | 数值确有不同 | {EQ.summary()['classes'].get('X1_VALUES_DIFFER')} | 否 |
| X2 | 1..6 全空（cid 1285） | {EQ.summary()['classes'].get('X2_ALL_SIX_SLOTS_EMPTY')} | 否 |
| — | skillid[0] 不在自身 pattern 类型集合内 | {EQ.summary()['classes'].get('NOT_AMONG_OWN_PATTERN_TYPES')} | 否 |

E0 = **{EQ.summary()['strict_1_6_exact_r2_caliber']}/1286**，与 R2 第三方审查复核钉死的口径一致
（全十槽严格比较为 1098/1287）。E1／E2 为归一后的子类，单独列出，不并入严格计数。
F0 的判据与 E 类**不同性质**（不作数值比较，而是路径判定），因此单列，不与 E0/E1/E2 相加。

E0 = **{EQ.summary()['strict_1_6_exact_r2_caliber']}/1286**，与 R2 第三方审查复核钉死的口径一致
（全十槽严格比较为 1098/1287）。E1／E2 为归一后的子类，单独列出，不并入严格计数。

## 覆盖增量

- 新增答案 **{page_sum}** 条（页求和）；唯一记录 **{unique}** 条。
- charainfo 未解释字段下降 **{page_sum}**（每个新答案替代一条原先 `NO_RULE_FOR_TYPE` 记录）。
- 证据范围沿用 `BY_TYPE_EXTRAPOLATED`（按类型套用），未新增第三类。

## 不迁移的部分（必须显式保留）

- X1（{EQ.summary()['classes'].get('X1_VALUES_DIFFER')} 角色）两侧原值都写进 `exceptions.jsonl`，
  不选一侧、不填零；这些角色的 charainfo 参数在档案里保持未解释（P2 第 9 批注记：执行取 pattern 侧，
  本记录副本不是执行值）。
- X0／X2／NOT_AMONG 各自注明原因；NOT_AMONG 现在只指「自身 pattern 存在但类型集合不含 skillid[0]」的
  {EQ.summary()['classes'].get('NOT_AMONG_OWN_PATTERN_TYPES')} 个角色，逐人定性见
  `../cp_paths/notamong_exceptions.jsonl` 与 `../charainfo_types/type_dispatch_index.json`。

## 重跑

```powershell
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/charainfo_params.py --snapshot-baseline   # 仅第一次，取 P1 基线
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/profiles.py
& .\\.venv\\Scripts\\python.exe -B scripts/character_skills/charainfo_params.py
```
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({"new_answers": page_sum, "unique": unique,
                      "classes": EQ.summary()["classes"],
                      "out": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    if "--snapshot-baseline" in sys.argv:
        C.enable_utf8_console()
        snapshot_baseline()
    else:
        main()
