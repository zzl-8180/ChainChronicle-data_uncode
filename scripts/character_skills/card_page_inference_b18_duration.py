#!/usr/bin/env python3
"""Source-derived B18 duration consumer.

Wire after the existing YG1 consumers as:

    import card_page_inference_b18_duration as B18_DURATION
    B18_DURATION.apply_to_groups(data, cid, groups)

Runtime inputs are the existing card_page_data.Inputs object and the in-memory
groups built from links/profiles plus the declared decoded cache. This module
never reads candidate JSONL/CSV, generated pages, effect_ledger, or task
reports. Every answer keeps the exact decoded record pointer and raw hash.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCOPE = "B18_DURATION_SOURCE_DERIVED_PARTIAL"
RULE_3000 = "skilllist|3000|/param6"
RULE_2003 = "skilllist|2003|/param0"
RULE_T13 = "bossskill|13|/skillparam3"
TARGET_RULES = {RULE_3000, RULE_2003, RULE_T13}

# Scheduling guard from the user's HOLD decision. These rows remain unresolved
# even if a later generic shape happens to resemble a duration candidate.
HOLD_ROW_IDS = {
    "4316-special_move-special_move-pattern0-lvorder0-f1",
    "4316-special_move-special_move-pattern1-lvorder1-f1",
    "4316-special_move-special_move-skilltext-lvorder2-f1",
    "30105-special_move-special_move-pattern0-lvorder0-f1",
    "30105-special_move-special_move-pattern1-lvorder1-f1",
    "30105-special_move-special_move-skilltext-lvorder2-f1",
    "30111-special_move-special_move-pattern0-lvorder0-f1",
    "30111-special_move-special_move-pattern2-lvorder2-f1",
    "30111-special_move-special_move-skilltext-lvorder3-f1",
}
ABILITY3000_ROW_IDS = {
    "30002-sympathy-sympathy-sympathy_skill_info__id_30002__ability0-lvorder0-f0",
    "30101-sympathy-sympathy-sympathy_skill_info__id_30101__ability0-lvorder0-f0",
    "30102-sympathy-sympathy-sympathy_skill_info__id_30102__ability0-lvorder0-f0",
    "30103-sympathy-sympathy-sympathy_skill_info__id_30103__ability0-lvorder0-f0",
    "30104-sympathy-sympathy-sympathy_skill_info__id_30104__ability0-lvorder0-f0",
    "30107-sympathy-sympathy-sympathy_skill_info__id_30107__ability0-lvorder0-f0",
    "30201-sympathy-sympathy-sympathy_skill_info__id_30201__ability0-lvorder0-f0",
    "30202-sympathy-sympathy-sympathy_skill_info__id_30202__ability0-lvorder0-f0",
    "30203-sympathy-sympathy-sympathy_skill_info__id_30203__ability0-lvorder0-f0",
    "30204-sympathy-sympathy-sympathy_skill_info__id_30204__ability0-lvorder0-f0",
    "30205-sympathy-sympathy-sympathy_skill_info__id_30205__ability0-lvorder0-f0",
    "30206-sympathy-sympathy-sympathy_skill_info__id_30206__ability0-lvorder0-f0",
    "30207-sympathy-sympathy-sympathy_skill_info__id_30207__ability0-lvorder0-f0",
    "30208-sympathy-sympathy-sympathy_skill_info__id_30208__ability0-lvorder0-f0",
    "30214-sympathy-sympathy-sympathy_skill_info__id_30214__ability0-lvorder0-f0",
    "30219-sympathy-sympathy-sympathy_skill_info__id_30219__ability0-lvorder0-f0",
    "30220-sympathy-sympathy-sympathy_skill_info__id_30220__ability0-lvorder0-f0",
    "30221-sympathy-sympathy-sympathy_skill_info__id_30221__ability0-lvorder0-f0",
    "30222-sympathy-sympathy-sympathy_skill_info__id_30222__ability0-lvorder0-f0",
    "30223-sympathy-sympathy-sympathy_skill_info__id_30223__ability0-lvorder0-f0",
    "30224-sympathy-sympathy-sympathy_skill_info__id_30224__ability0-lvorder0-f0",
    "30225-sympathy-sympathy-sympathy_skill_info__id_30225__ability0-lvorder0-f0",
    "30226-sympathy-sympathy-sympathy_skill_info__id_30226__ability0-lvorder0-f0",
    "30228-sympathy-sympathy-sympathy_skill_info__id_30228__ability0-lvorder0-f0",
    "30229-sympathy-sympathy-sympathy_skill_info__id_30229__ability0-lvorder0-f0",
    "30237-sympathy-sympathy-sympathy_skill_info__id_30237__ability0-lvorder0-f0",
    "30238-sympathy-sympathy-sympathy_skill_info__id_30238__ability0-lvorder0-f0",
    "30241-sympathy-sympathy-sympathy_skill_info__id_30241__ability0-lvorder0-f0",
    "30252-sympathy-sympathy-sympathy_skill_info__id_30252__ability0-lvorder0-f0",
    "30254-sympathy-sympathy-sympathy_skill_info__id_30254__ability0-lvorder0-f0",
    "30255-sympathy-sympathy-sympathy_skill_info__id_30255__ability0-lvorder0-f0",
    "30262-sympathy-sympathy-sympathy_skill_info__id_30262__ability0-lvorder0-f0",
    "30301-sympathy-sympathy-sympathy_skill_info__id_30301__ability0-lvorder0-f0",
    "30302-sympathy-sympathy-sympathy_skill_info__id_30302__ability0-lvorder0-f0",
    "30303-sympathy-sympathy-sympathy_skill_info__id_30303__ability0-lvorder0-f0",
    "30304-sympathy-sympathy-sympathy_skill_info__id_30304__ability0-lvorder0-f0",
    "30305-sympathy-sympathy-sympathy_skill_info__id_30305__ability0-lvorder0-f0",
    "30306-sympathy-sympathy-sympathy_skill_info__id_30306__ability0-lvorder0-f0",
    "30307-sympathy-sympathy-sympathy_skill_info__id_30307__ability0-lvorder0-f0",
    "30308-sympathy-sympathy-sympathy_skill_info__id_30308__ability0-lvorder0-f0",
    "30317-sympathy-sympathy-sympathy_skill_info__id_30317__ability0-lvorder0-f0",
    "30327-sympathy-sympathy-sympathy_skill_info__id_30327__ability0-lvorder0-f0",
    "30328-sympathy-sympathy-sympathy_skill_info__id_30328__ability0-lvorder0-f0",
    "30333-sympathy-sympathy-sympathy_skill_info__id_30333__ability0-lvorder0-f0",
    "30337-sympathy-sympathy-sympathy_skill_info__id_30337__ability0-lvorder0-f0",
}

MULTI_PATTERN_ROW_IDS = {
    "10215-special_move-special_move-skilltext-lvorder3-f2",
    "10215-special_move-special_move-skilltext-lvorder3-f4",
    "1303-special_move-special_move-skilltext-lvorder3-f2",
    "1303-special_move-special_move-skilltext-lvorder3-f3",
    "2331-special_move-special_move-skilltext-lvorder3-f1",
    "2331-special_move-special_move-skilltext-lvorder3-f3",
    "30101-special_move-special_move-skilltext-lvorder3-f2",
    "30102-special_move-special_move-skilltext-lvorder3-f1",
    "30103-special_move-special_move-skilltext-lvorder2-f4",
    "30103-special_move-special_move-skilltext-lvorder2-f5",
    "30104-special_move-special_move-skilltext-lvorder2-f4",
    "30105-special_move-special_move-skilltext-lvorder2-f3",
    "30106-special_move-special_move-skilltext-lvorder2-f3",
    "30108-special_move-special_move-skilltext-lvorder3-f3",
    "30109-special_move-special_move-skilltext-lvorder3-f2",
    "30110-special_move-special_move-skilltext-lvorder3-f4",
    "30111-special_move-special_move-skilltext-lvorder3-f3",
    "30112-special_move-special_move-skilltext-lvorder3-f1",
    "30112-special_move-special_move-skilltext-lvorder3-f3",
    "30113-special_move-special_move-skilltext-lvorder3-f2",
    "30201-special_move-special_move-skilltext-lvorder3-f2",
    "30202-special_move-special_move-skilltext-lvorder2-f2",
    "30203-special_move-special_move-skilltext-lvorder3-f3",
    "30204-special_move-special_move-skilltext-lvorder3-f2",
    "30205-special_move-special_move-skilltext-lvorder2-f3",
    "30206-special_move-special_move-skilltext-lvorder3-f2",
    "30207-special_move-special_move-skilltext-lvorder9-f1",
    "30208-special_move-special_move-skilltext-lvorder3-f1",
    "30210-special_move-special_move-skilltext-lvorder3-f1",
    "30210-special_move-special_move-skilltext-lvorder3-f3",
    "30214-special_move-special_move-skilltext-lvorder6-f4",
    "30218-special_move-special_move-skilltext-lvorder2-f1",
    "30218-special_move-special_move-skilltext-lvorder2-f2",
    "30221-special_move-special_move-skilltext-lvorder3-f2",
    "30224-special_move-special_move-skilltext-lvorder3-f1",
    "30224-special_move-special_move-skilltext-lvorder3-f3",
    "30226-special_move-special_move-skilltext-lvorder2-f2",
    "30228-special_move-special_move-skilltext-lvorder2-f2",
    "30230-special_move-special_move-skilltext-lvorder3-f1",
    "30230-special_move-special_move-skilltext-lvorder3-f2",
    "30234-special_move-special_move-skilltext-lvorder2-f1",
    "30234-special_move-special_move-skilltext-lvorder2-f2",
    "30237-special_move-special_move-skilltext-lvorder2-f1",
    "30237-special_move-special_move-skilltext-lvorder2-f3",
    "30238-special_move-special_move-skilltext-lvorder3-f1",
    "30238-special_move-special_move-skilltext-lvorder3-f3",
    "30239-special_move-special_move-skilltext-lvorder3-f1",
    "30241-special_move-special_move-skilltext-lvorder3-f2",
    "30242-special_move-special_move-skilltext-lvorder3-f1",
    "30242-special_move-special_move-skilltext-lvorder3-f3",
    "30243-special_move-special_move-skilltext-lvorder3-f2",
    "30244-special_move-special_move-skilltext-lvorder3-f2",
    "30245-special_move-special_move-skilltext-lvorder3-f1",
    "30245-special_move-special_move-skilltext-lvorder3-f3",
    "30246-special_move-special_move-skilltext-lvorder3-f1",
    "30246-special_move-special_move-skilltext-lvorder3-f2",
    "30247-special_move-special_move-skilltext-lvorder3-f2",
    "30248-special_move-special_move-skilltext-lvorder3-f2",
    "30249-special_move-special_move-skilltext-lvorder3-f1",
    "30249-special_move-special_move-skilltext-lvorder3-f3",
    "30250-special_move-special_move-skilltext-lvorder3-f2",
    "30251-special_move-special_move-skilltext-lvorder3-f2",
    "30252-special_move-special_move-skilltext-lvorder3-f1",
    "30256-special_move-special_move-skilltext-lvorder3-f2",
    "30257-special_move-special_move-skilltext-lvorder3-f2",
    "30258-special_move-special_move-skilltext-lvorder3-f2",
    "30261-special_move-special_move-skilltext-lvorder3-f2",
    "30262-special_move-special_move-skilltext-lvorder3-f2",
    "30262-special_move-special_move-skilltext-lvorder3-f3",
    "30302-special_move-special_move-skilltext-lvorder2-f1",
    "30303-special_move-special_move-skilltext-lvorder2-f3",
    "30304-special_move-special_move-skilltext-lvorder3-f3",
    "30305-special_move-special_move-skilltext-lvorder2-f4",
    "30306-special_move-special_move-skilltext-lvorder2-f3",
    "30306-special_move-special_move-skilltext-lvorder2-f4",
    "30307-special_move-special_move-skilltext-lvorder3-f1",
    "30308-special_move-special_move-skilltext-lvorder2-f1",
    "30308-special_move-special_move-skilltext-lvorder2-f3",
    "30309-special_move-special_move-skilltext-lvorder2-f2",
    "30310-special_move-special_move-skilltext-lvorder2-f2",
    "30312-special_move-special_move-skilltext-lvorder3-f2",
    "30312-special_move-special_move-skilltext-lvorder3-f3",
    "30313-special_move-special_move-skilltext-lvorder2-f1",
    "30314-special_move-special_move-skilltext-lvorder2-f2",
    "30314-special_move-special_move-skilltext-lvorder2-f4",
    "30315-special_move-special_move-skilltext-lvorder3-f2",
    "30317-special_move-special_move-skilltext-lvorder3-f1",
    "30317-special_move-special_move-skilltext-lvorder3-f4",
    "30318-special_move-special_move-skilltext-lvorder3-f2",
    "30320-special_move-special_move-skilltext-lvorder3-f1",
    "30320-special_move-special_move-skilltext-lvorder3-f3",
    "30321-special_move-special_move-skilltext-lvorder2-f1",
    "30321-special_move-special_move-skilltext-lvorder2-f3",
    "30322-special_move-special_move-skilltext-lvorder3-f2",
    "30322-special_move-special_move-skilltext-lvorder3-f3",
    "30324-special_move-special_move-skilltext-lvorder3-f1",
    "30324-special_move-special_move-skilltext-lvorder3-f3",
    "30326-special_move-special_move-skilltext-lvorder6-f1",
    "30326-special_move-special_move-skilltext-lvorder6-f3",
    "30327-special_move-special_move-skilltext-lvorder3-f2",
    "30328-special_move-special_move-skilltext-lvorder2-f1",
    "30328-special_move-special_move-skilltext-lvorder2-f2",
    "30329-special_move-special_move-skilltext-lvorder3-f2",
    "30330-special_move-special_move-skilltext-lvorder3-f1",
    "30330-special_move-special_move-skilltext-lvorder3-f3",
    "30332-special_move-special_move-skilltext-lvorder3-f1",
    "30332-special_move-special_move-skilltext-lvorder3-f3",
    "30333-special_move-special_move-skilltext-lvorder3-f3",
    "30335-special_move-special_move-skilltext-lvorder3-f2",
    "30335-special_move-special_move-skilltext-lvorder3-f3",
    "30336-special_move-special_move-skilltext-lvorder3-f1",
    "30337-special_move-special_move-skilltext-lvorder3-f3",
    "30338-special_move-special_move-skilltext-lvorder3-f2",
    "30338-special_move-special_move-skilltext-lvorder3-f4",
    "349-special_move-special_move-skilltext-lvorder3-f2",
    "349-special_move-special_move-skilltext-lvorder3-f3",
    "350-special_move-special_move-skilltext-lvorder3-f2",
    "351-special_move-special_move-skilltext-lvorder3-f2",
    "352-special_move-special_move-skilltext-lvorder3-f2",
    "353-special_move-special_move-skilltext-lvorder3-f2",
    "4315-special_move-special_move-skilltext-lvorder3-f2",
    "4316-special_move-special_move-skilltext-lvorder2-f3",
    "7251-special_move-special_move-skilltext-lvorder3-f1",
    "7251-special_move-special_move-skilltext-lvorder3-f3",
}

ADMITTED_ROW_IDS = ABILITY3000_ROW_IDS | MULTI_PATTERN_ROW_IDS
BLOCKED_MULTI_NO_BRANCH = {"30236-special_move-special_move-skilltext-lvorder3-f2"}


def _number_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return False
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return False
    if not math.isfinite(left) or not math.isfinite(right):
        return False
    # B18 same-value admission is exact. No tolerance is allowed between
    # adjacent float32 values or values such as 30 and 30 + 1e-8.
    return left == right


def _positive(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def _all_equal(values: list[Any]) -> bool:
    return bool(values) and all(_number_equal(values[0], value) for value in values[1:])


def _object_signature(japanese: str) -> str:
    if "攻撃した敵" in japanese:
        return "attacked_enemy"
    if "味方全体" in japanese:
        return "ally_all"
    if "自身" in japanese and "味方" not in japanese:
        return "self"
    return "unclassified"


def _mode(japanese: str) -> str | None:
    obj = _object_signature(japanese)
    if obj == "attacked_enemy" and "下がる" in japanese:
        return "skilllist_2003_param0"
    if obj in {"ally_all", "self"} and "上がる" in japanese:
        return "bossskill_13_param3"
    return None


def _rule_key_for_mode(mode: str) -> str:
    return RULE_2003 if mode == "skilllist_2003_param0" else RULE_T13


def _canonical_record_sha256(record: dict[str, Any]) -> str:
    encoded = json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _yg(data, cid: int) -> bool:
    profile = data.profiles.get(cid) or {}
    return "Y.G." in str(profile.get("title") or "")


def _all_rows(groups: list[dict[str, Any]]):
    for group in groups:
        for skill in group.get("skills", []):
            for row in skill.get("rows", []):
                yield group, skill, row


def _clean_text(value: Any) -> str:
    return str(value or "").replace("\\n", "\n")


def _cache_character(data, cid: int):
    character = getattr(data, "cache_chara", {}).get(cid)
    if character is not None:
        return character
    if "charainfo" not in data.raw_docs:
        path = data.decoded / "charainfo.data5.json.raw"
        if not path.is_file():
            return None
        data.raw_docs["charainfo"] = json.loads(path.read_text(encoding="utf-8"))
    return next(
        (record for record in data.raw_docs["charainfo"].get("charainfo", []) if record.get("cid") == cid),
        None,
    )


def _decoded_record(data, table: str, record_id: int):
    """Return (record, actual pointer) from Inputs/original decoded data."""
    if table == "skilllist":
        indexed = data.cache_skill.get(record_id)
        if not indexed:
            return None, None
        index, record = indexed
        return record, f"/skilllist/{index}"
    if table in {"bosspattern", "bossskill"}:
        if "bossinfo" not in data.raw_docs:
            path = data.decoded / "bossinfo.data5.json.raw"
            if not path.is_file():
                return None, None
            data.raw_docs["bossinfo"] = json.loads(path.read_text(encoding="utf-8"))
        doc = data.raw_docs["bossinfo"]
        key = "patternid" if table == "bosspattern" else "skillid"
        for index, record in enumerate(doc.get("bossinfo", {}).get(table, [])):
            if record.get(key) == record_id:
                return record, f"/bossinfo/{table}/{index}"
    if table == "charainfo":
        record = _cache_character(data, record_id)
        if record is None:
            return None, None
        if "charainfo" not in data.raw_docs:
            path = data.decoded / "charainfo.data5.json.raw"
            if not path.is_file():
                return None, None
            data.raw_docs["charainfo"] = json.loads(path.read_text(encoding="utf-8"))
        for index, candidate in enumerate(data.raw_docs["charainfo"].get("charainfo", [])):
            if candidate.get("cid") == record_id:
                return candidate, f"/charainfo/{index}"
    return None, None


def _source_stamp_index(data):
    """Load the existing raw-record index, never task manifests or pages."""
    if hasattr(data, "_b18_source_stamp_index"):
        return data._b18_source_stamp_index
    path = data.decoded.parent / "records.jsonl"
    if not path.is_file():
        data._b18_source_stamp_index = {}
        return data._b18_source_stamp_index
    index = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("table") in {"skilllist", "bosspattern", "bossskill", "charainfo"}:
                record_key = record.get("record_key")
                if record_key:
                    index[record_key] = record
    data._b18_source_stamp_index = index
    return index


def _exact_source(data, source: dict[str, Any] | None, table: str, record_id: int):
    """Validate identity and return the exact original raw-record stamp."""
    if not isinstance(source, dict):
        return None, None, "SOURCE_MISSING"
    record, actual_pointer = _decoded_record(data, table, record_id)
    if record is None or actual_pointer is None:
        return None, None, "DECODED_RECORD_MISSING"
    if source.get("layer") != "CACHE":
        return None, None, "SOURCE_LAYER_NOT_CACHE"
    if source.get("json_pointer") and source.get("json_pointer") != actual_pointer:
        return None, None, "SOURCE_POINTER_MISMATCH"
    if source.get("table") and source.get("table") != table:
        return None, None, "SOURCE_TABLE_MISMATCH"
    if source.get("record_id") is not None and source.get("record_id") != record_id:
        return None, None, "SOURCE_RECORD_ID_MISMATCH"
    stamps = _source_stamp_index(data)
    stamp = None
    raw_key = "patternid" if table == "bosspattern" else "cid" if table == "charainfo" else "skillid"
    for value in stamps.values():
        if (
            (value.get("location") or {}).get("json_pointer") == actual_pointer
            and value.get("table") == table
            and (value.get("raw") or {}).get(raw_key) == record_id
        ):
            stamp = value
            break
    if stamp is None:
        return None, None, "ORIGINAL_RECORD_STAMP_MISSING"
    if source.get("source_key") and source.get("source_key") != stamp.get("source_key"):
        return None, None, "SOURCE_KEY_MISMATCH"
    if source.get("record_key") and "#" in source.get("record_key") and source.get("record_key") != stamp.get("record_key"):
        return None, None, "SOURCE_RECORD_KEY_MISMATCH"
    location = stamp.get("location") or {}
    if location.get("json_pointer") != actual_pointer:
        return None, None, "ORIGINAL_POINTER_MISMATCH"
    if stamp.get("raw") != record:
        return None, None, "ORIGINAL_RECORD_PAYLOAD_MISMATCH"
    if source.get("raw_record_sha256") and source.get("raw_record_sha256") != location.get("raw_record_sha256"):
        return None, None, "RAW_RECORD_HASH_MISMATCH"
    if source.get("source_sha256") and source.get("source_sha256") != stamp.get("source_sha256"):
        return None, None, "SOURCE_FILE_HASH_MISMATCH"
    return record, stamp, None


def _enrich_source(source: dict[str, Any], stamp: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(source)
    location = stamp.get("location") or {}
    result.update(
        source_key=stamp.get("source_key"),
        record_key=stamp.get("record_key"),
        layer=stamp.get("layer"),
        original_file=stamp.get("original_file"),
        source_sha256=stamp.get("source_sha256"),
        json_pointer=location.get("json_pointer"),
        byte_begin=location.get("byte_begin"),
        byte_end_exclusive=location.get("byte_end_exclusive"),
        raw_record_sha256=location.get("raw_record_sha256"),
        snapshot_id=stamp.get("snapshot_id"),
    )
    return result


def _field_source(
    source: dict[str, Any],
    *,
    table: str,
    record_id: int,
    layer: str,
    field_path: str,
) -> dict[str, Any]:
    result = deepcopy(source)
    pointer = result["json_pointer"]
    for key in ("source_key", "record_key", "source_sha256", "raw_record_sha256"):
        if not result.get(key):
            raise ValueError(f"source stamp missing {key}")
    result.update(
        table=table,
        record_id=record_id,
        layer=layer,
        field_path=field_path,
        field=field_path,
        field_json_pointer=pointer + field_path,
        parent_record_sha256=result.get("parent_record_sha256"),
    )
    return result


def _raw_skill_slots(parent_record: dict[str, Any]):
    slots = []
    for key, value in parent_record.items():
        if not key.startswith("skillid") or not key[7:].isdigit():
            continue
        if isinstance(value, int) and not isinstance(value, bool):
            slots.append((key, value))
    return sorted(slots, key=lambda item: int(item[0][7:]))


def _raw_condition_label(parent_record: dict[str, Any]) -> str:
    start = parent_record.get("hpstart")
    end = parent_record.get("hpend")
    start_text = "?" if start is None else str(start)
    end_text = "?" if end is None else str(end)
    return f"HP {start_text}–{end_text}%"


def _raw_duration_carrier(data, parent_record: dict[str, Any], mode: str):
    """Resolve the duration child through the actual parent slot chain."""
    candidates = []
    for boss_slot, boss_id in _raw_skill_slots(parent_record):
        boss_record, boss_pointer = _decoded_record(data, "bossskill", boss_id)
        if boss_record is None or boss_record.get("skillid") != boss_id:
            continue
        if mode == "bossskill_13_param3":
            if boss_record.get("skillid0") != 13:
                continue
            field_path = "/skillparam3"
            duration = boss_record.get("skillparam3")
            ability_record = boss_record
            ability_record_id = boss_id
            ability_pointer = boss_pointer
            ordinary_pointer = None
            ordinary_child_slot = None
        else:
            ability_id = boss_record.get("s_ability")
            if not isinstance(ability_id, int) or isinstance(ability_id, bool):
                continue
            ability_record, ability_pointer = _decoded_record(data, "skilllist", ability_id)
            if (
                ability_record is None
                or ability_record.get("ability") != 2003
                or ability_record.get("skillid") != ability_id
            ):
                continue
            field_path = "/param0"
            duration = ability_record.get("param0")
            ability_record_id = ability_id
            ordinary_pointer = ability_pointer
            ordinary_child_slot = "s_ability"
        candidates.append(
            {
                "boss_reference_slot": boss_slot,
                "boss_record_id": boss_id,
                "boss_json_pointer": boss_pointer,
                "boss_record": deepcopy(boss_record),
                "ordinary_child_slot": ordinary_child_slot,
                "ordinary_record_id": ability_record_id,
                "ordinary_json_pointer": ordinary_pointer,
                "ordinary_record": deepcopy(ability_record),
                "field_path": field_path,
                "raw_value": duration,
            }
        )
    if len(candidates) != 1:
        return None, f"RAW_DURATION_CARRIER_COUNT_{len(candidates)}"
    candidate = candidates[0]
    if not _positive(candidate["raw_value"]):
        return None, "RAW_DURATION_NOT_POSITIVE"
    if mode == "skilllist_2003_param0" and candidate["ordinary_record"].get("param3") != 1:
        return None, "RAW_2003_PARAM3_GATE_MISMATCH"
    return candidate, None


def _row_identity_error(data, cid: int, group: dict[str, Any], skill: dict[str, Any], row: dict[str, Any]):
    """Require cid, row id, raw source, text and both spans to be the same row."""
    failures = []
    row_id = row.get("row_id")
    if not isinstance(row_id, str) or not row_id.startswith(f"{cid}-"):
        failures.append("ROW_ID_CID_MISMATCH")
    if row.get("cid") != cid:
        failures.append("ROW_CID_MISMATCH")
    if row.get("group") != group.get("group"):
        failures.append("ROW_GROUP_MISMATCH")
    source = row.get("source")
    if not isinstance(source, dict):
        return None, dict(reason="ROW_SOURCE_MISSING", detail=failures)
    table = skill.get("table")
    record_id = skill.get("record_id")
    # Host integration: the skill must actually be referenced by this card.
    # A genuine other-card record is not sufficient after relabelling the row.
    linked = False
    layer = skill.get("layer") or (skill.get("source") or {}).get("layer")
    for actual_group in getattr(data, "links", {}).get(cid, {}).get("groups", []):
        if actual_group.get("group") != skill.get("original_group", group.get("group")):
            continue
        for entry in actual_group.get("records", []):
            if (entry.get("table") == table and entry.get("layer") == layer
                    and entry.get("reference_id") == record_id
                    and entry.get("reference_field") == skill.get("reference_field")):
                actual_source = data.precise_source(entry)
                expected_source = skill.get("source") or {}
                if all(actual_source.get(k) == expected_source.get(k) and actual_source.get(k) is not None
                       for k in ("record_key", "source_key", "json_pointer")):
                    linked = True
    if not linked:
        return None, dict(reason="CARD_ACTUAL_SKILL_REFERENCE_MISMATCH", detail=failures)
    skill_record, skill_stamp, skill_reason = _exact_source(
        data, skill.get("source"), table, record_id
    )
    row_record, row_stamp, row_reason = _exact_source(data, source, table, record_id)
    if skill_reason:
        failures.append("SKILL_" + skill_reason)
    if row_reason:
        failures.append("ROW_" + row_reason)
    if skill_record is not None and row_record is not None and skill_record != row_record:
        failures.append("ROW_SKILL_RAW_RECORD_MISMATCH")
    if (
        skill_stamp is not None
        and row_stamp is not None
        and skill_stamp.get("record_key") != row_stamp.get("record_key")
    ):
        failures.append("ROW_SKILL_RECORD_KEY_MISMATCH")
    if skill.get("record_id") != record_id:
        failures.append("SKILL_RECORD_ID_CHANGED")

    text_field = {
        "skilllist": "text",
        "bosspattern": "sinfo",
        "charainfo": "skilltext",
    }.get(table)
    if text_field is None:
        failures.append("ROW_TABLE_UNSUPPORTED")
    position = row.get("source_position")
    if not isinstance(position, dict):
        failures.append("SOURCE_POSITION_MISSING")
    else:
        japanese = row.get("japanese")
        if position.get("japanese") != japanese:
            failures.append("SOURCE_POSITION_JAPANESE_MISMATCH")
        if position.get("field_pointer") != source.get("field_json_pointer"):
            failures.append("SOURCE_POSITION_FIELD_POINTER_MISMATCH")
        if position.get("source_key") != source.get("source_key"):
            failures.append("SOURCE_POSITION_SOURCE_KEY_MISMATCH")
        raw_text = _clean_text((row_record or {}).get(text_field))
        raw_span = position.get("raw_span")
        clean_span = position.get("clean_span")
        for label, span in (("RAW_SPAN", raw_span), ("CLEAN_SPAN", clean_span)):
            if not (
                isinstance(span, list)
                and len(span) == 2
                and all(isinstance(value, int) and not isinstance(value, bool) for value in span)
                and 0 <= span[0] <= span[1] <= len(raw_text)
            ):
                failures.append(label + "_INVALID")
                continue
            if raw_text[span[0]:span[1]] != row.get("japanese"):
                failures.append(label + "_TEXT_MISMATCH")
    if failures:
        return None, dict(reason="ROW_IDENTITY_OR_SOURCE_MISMATCH", detail=sorted(set(failures)))
    return row_record, None


def _rule_metadata(data, key: str) -> dict[str, Any]:
    rule = (data.rule_metadata or {}).get(key)
    return deepcopy(rule) if isinstance(rule, dict) else {}


def _duration_answer(
    row: dict[str, Any], rule_key: str
) -> list[dict[str, Any]]:
    return [
        answer
        for answer in row.get("answers", [])
        if answer.get("quantity_kind") == "持续时间"
        and answer.get("rule_key") == rule_key
    ]


def _already_duration(row: dict[str, Any]) -> bool:
    return any(
        answer.get("quantity_kind") == "持续时间"
        or answer.get("rule_key") in TARGET_RULES
        for answer in row.get("answers", [])
    )


def _base_answer(
    *,
    data,
    row: dict[str, Any],
    rule_key: str,
    duration: float | int,
    source: dict[str, Any],
    association_note: str,
    binding: dict[str, Any],
) -> dict[str, Any]:
    rule = _rule_metadata(data, rule_key)
    return {
        "value": f"该句共同持续时间为{duration:g}游戏秒（时长单项部分答案）",
        "quantity_kind": "持续时间",
        "unit": "游戏秒（fixedDeltaTime 累计）",
        "raw_value": duration,
        "quantitative": True,
        "numeric_source": f"既有字段局部规则 {rule_key}",
        "numeric_evidence": "确认",
        "association_evidence": "推断",
        "evidence_scope": SCOPE,
        "answer_status": "CONFIRMED_NUMERIC",
        "rule_key": rule_key,
        "table": source.get("table"),
        "record_id": source.get("record_id"),
        "layer": source.get("layer"),
        "field_path": source.get("field_path"),
        "source": deepcopy(source),
        "rule_body_status": rule.get("status"),
        "rule_status": rule.get("status"),
        "conversion": rule.get("conversion"),
        "base_definition": rule.get("base_definition"),
        "rule_limits": rule.get("limits"),
        "conditions": rule.get("applicability") or rule.get("conditions"),
        "evidence": deepcopy(rule.get("evidence") or []),
        "condition_label": association_note,
        "b18_duration_binding": deepcopy(binding),
        "partial_answer": True,
        "other_claims_remain_unknown": True,
        "row_fully_complete_claimed": False,
        "note": (
            "仅把原文“一定時間”的持续时间挂到本句；其他属性增量、完整对象名单、"
            "实际装载/最终战斗结果另论。多 pattern 项只给条件化分支时长，不选择分支。"
        ),
    }


def _append_answer(row: dict[str, Any], answer: dict[str, Any]) -> int:
    row.setdefault("answers", [])
    if _already_duration(row) and not _duration_answer(row, answer["rule_key"]):
        # A different duration carrier already answers the same claim.
        return -1
    duplicate = any(
        existing.get("rule_key") == answer.get("rule_key")
        and existing.get("record_id") == answer.get("record_id")
        and _number_equal(existing.get("raw_value"), answer.get("raw_value"))
        for existing in row["answers"]
    )
    if duplicate:
        return -2
    row["answers"].append(answer)
    row["partial"] = True
    row["row_fully_complete_claimed"] = False
    row.setdefault("b18_duration_partial_claims", []).append(
        {
            "rule_key": answer["rule_key"],
            "record_id": answer["record_id"],
            "field_path": answer["field_path"],
            "raw_value": answer["raw_value"],
            "unit": answer["unit"],
        }
    )
    return len(row["answers"]) - 1


def _apply_ability3000(data, cid: int, group: dict[str, Any], skill: dict[str, Any], row: dict[str, Any], report: dict[str, Any]):
    if group.get("group") != "sympathy" or skill.get("table") != "skilllist":
        return False
    record_id = skill.get("record_id")
    record, row_error = _row_identity_error(data, cid, group, skill, row)
    if row_error:
        report["rejections"].append({"row_id": row.get("row_id"), **row_error})
        return True
    pointer = f"/skilllist/{data.cache_skill[record_id][0]}"
    if not record or record.get("ability") != 3000:
        return False
    if "一定時間" not in row.get("japanese", ""):
        return False
    if row.get("japanese", "").count("一定時間") != 1:
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "ABILITY3000_DURATION_CLAIM_COUNT"})
        return True
    raw = record.get("param6")
    if not _positive(raw):
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "ABILITY3000_PARAM6_NOT_POSITIVE"})
        return True
    source = skill.get("source") or {}
    verified_record, stamp, reason = _exact_source(data, source, "skilllist", record_id)
    if reason or verified_record != record:
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "ABILITY3000_" + str(reason or "RECORD_MISMATCH")})
        return True
    field_source = _field_source(
        _enrich_source(source, stamp),
        table="skilllist",
        record_id=record_id,
        layer="CACHE",
        field_path="/param6",
    )
    answer = _base_answer(
        data=data,
        row=row,
        rule_key=RULE_3000,
        duration=raw,
        source=field_source,
        association_note="D1：ability3000 只先交付共同持续时间",
        binding={
            "kind": "ability3000_own_record",
            "source_row_id": row.get("row_id"),
            "record_id": record_id,
            "record_pointer": pointer,
            "param6": raw,
            "other_attributes_remain_unknown": True,
        },
    )
    index = _append_answer(row, answer)
    if index >= 0:
        report["answers_added"] += 1
        report["additions"].append(
            {
                "row_id": row.get("row_id"),
                "kind": "ability3000_own_record",
                "answer_index": index,
                "rule_key": RULE_3000,
                "record_id": record_id,
                "source_json_pointer": field_source["json_pointer"],
                "raw_value": raw,
            }
        )
    else:
        report["skipped"].append({"row_id": row.get("row_id"), "reason": "ALREADY_PRESENT_OR_CONFLICT", "code": index})
    return True


def _pattern_skill_index(groups: list[dict[str, Any]], cid: int):
    result: dict[int, dict[str, Any]] = {}
    for group in groups:
        if group.get("group") != "special_move":
            continue
        for skill in group.get("skills", []):
            if (
                skill.get("table") == "bosspattern"
                and str(skill.get("reference_field", "")).startswith("pattern")
                and isinstance(skill.get("record_id"), int)
            ):
                result[skill["record_id"]] = skill
    return result


def _apply_multi_pattern(
    data,
    cid: int,
    group: dict[str, Any],
    skill: dict[str, Any],
    row: dict[str, Any],
    pattern_skills: dict[int, dict[str, Any]],
    report: dict[str, Any],
):
    if not (group.get("group") == "special_move" and skill.get("table") == "charainfo"):
        return False
    row_record, row_error = _row_identity_error(data, cid, group, skill, row)
    if row_error:
        report["rejections"].append({"row_id": row.get("row_id"), **row_error})
        return True
    character_record = _cache_character(data, cid)
    if character_record is None:
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "CACHE_CHARACTER_MISSING"})
        return True
    same_cond = row.get("same_cond_alt_t13")
    if not isinstance(same_cond, dict):
        return False
    japanese = row.get("japanese", "")
    mode = _mode(japanese)
    if mode is None:
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "MULTI_OBJECT_OR_MODE_UNKNOWN"})
        return True
    if japanese.count("一定時間") != 1:
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "MULTI_DURATION_CLAIM_COUNT"})
        return True
    expected_rule = _rule_key_for_mode(mode)
    text_branches = [
        branch for branch in same_cond.get("branches", []) if not branch.get("sinfo_empty")
    ]
    pids: list[int] = []
    for branch in text_branches:
        pid = branch.get("pid")
        if pid not in pids:
            pids.append(pid)
    if len(pids) < 2:
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "MULTI_TEXT_BRANCH_LT2"})
        return True

    branches = []
    failures = []
    for pid in pids:
        meta = [branch for branch in text_branches if branch.get("pid") == pid]
        parent_skill = pattern_skills.get(pid)
        if not meta or not parent_skill or parent_skill.get("layer") != meta[0].get("layer"):
            failures.append("PARENT_MISSING")
            continue
        reference_slot = meta[0].get("slot")
        if character_record.get(reference_slot) != pid:
            failures.append("CHARACTER_PARENT_SLOT_MISMATCH")
            continue
        if parent_skill.get("reference_field") != reference_slot:
            failures.append("PARENT_SKILL_REFERENCE_SLOT_MISMATCH")
            continue
        parent_verified, parent_stamp, parent_reason = _exact_source(
            data, parent_skill.get("source"), "bosspattern", pid
        )
        if parent_reason:
            failures.append("PARENT_" + parent_reason)
            continue
        if parent_verified.get("patternid") != pid:
            failures.append("PARENT_PATTERN_ID_MISMATCH")
            continue
        expected_cond_label = _raw_condition_label(parent_verified)
        if meta[0].get("cond_label") != expected_cond_label:
            failures.append("PARENT_CONDITION_LABEL_MISMATCH")
            continue
        if japanese not in _clean_text(parent_verified.get("sinfo")):
            failures.append("PARENT_RAW_TEXT_MISSING")
            continue
        raw_carrier, carrier_reason = _raw_duration_carrier(data, parent_verified, mode)
        if carrier_reason:
            failures.append(carrier_reason)
            continue
        exact_parent_rows = [
            candidate
            for candidate in parent_skill.get("rows", [])
            if candidate.get("japanese") == japanese
        ]
        if len(exact_parent_rows) != 1:
            failures.append(f"PARENT_OBJECT_ROWS_{len(exact_parent_rows)}")
            continue
        parent_row = exact_parent_rows[0]
        parent_row_record, parent_row_error = _row_identity_error(
            data, cid, group, parent_skill, parent_row
        )
        if parent_row_error:
            failures.append("PARENT_ROW_" + str(parent_row_error.get("reason")))
            continue
        if parent_row_record != parent_verified:
            failures.append("PARENT_ROW_RAW_MISMATCH")
            continue
        duration_answers = _duration_answer(parent_row, expected_rule)
        if len(duration_answers) != 1:
            failures.append(f"DURATION_ANSWERS_{len(duration_answers)}")
            continue
        source_answer = duration_answers[0]
        child_table = source_answer.get("table") or (source_answer.get("source") or {}).get("table")
        child_id = source_answer.get("record_id") or (source_answer.get("source") or {}).get("record_id")
        if child_table not in {"skilllist", "bossskill"} or not isinstance(child_id, int):
            failures.append("CHILD_IDENTITY_MISSING")
            continue
        if source_answer.get("field_path") != raw_carrier["field_path"]:
            failures.append("DURATION_FIELD_PATH_MISMATCH")
            continue
        if child_table != ("skilllist" if mode == "skilllist_2003_param0" else "bossskill"):
            failures.append("CHILD_TABLE_MODE_MISMATCH")
            continue
        if child_id != raw_carrier["ordinary_record_id"]:
            failures.append("CHILD_NOT_BOUND_TO_PARENT_SLOT")
            continue
        duration = source_answer.get("raw_value")
        if not _positive(duration):
            failures.append("CHILD_DURATION_NOT_POSITIVE")
            continue
        actual_field_value = raw_carrier["ordinary_record"].get(raw_carrier["field_path"].lstrip("/"))
        if not _number_equal(actual_field_value, duration):
            failures.append("CHILD_RAW_FIELD_VALUE_MISMATCH")
            continue
        child_record, child_stamp, child_reason = _exact_source(
            data,
            source_answer.get("source"),
            child_table,
            child_id,
        )
        if child_reason:
            failures.append("CHILD_" + child_reason)
            continue
        if child_record != raw_carrier["ordinary_record"]:
            failures.append("CHILD_RAW_RECORD_MISMATCH")
            continue
        if mode == "skilllist_2003_param0":
            if child_record.get("ability") != 2003:
                failures.append("CHILD_NOT_ABILITY2003")
                continue
            if not _number_equal(child_record.get("param0"), duration):
                failures.append("CHILD_PARAM0_MISMATCH")
                continue
        else:
            if child_record.get("skillid0") != 13:
                failures.append("CHILD_NOT_TYPE13")
                continue
            if not _number_equal(child_record.get("skillparam3"), duration):
                failures.append("CHILD_PARAM3_MISMATCH")
                continue
            if len(meta) != 1:
                failures.append("CHILD_T13_MULTI_CARRIER")
                continue
            meta_p3 = meta[0].get("raws", {}).get("skillparam3")
            if not _number_equal(meta_p3, duration):
                failures.append("CHILD_T13_META_MISMATCH")
                continue
        branches.append(
            {
                "slot": reference_slot,
                "parent_reference_slot": reference_slot,
                "character_parent_reference_id": character_record.get(reference_slot),
                "parent_id": pid,
                "parent_source": _enrich_source(parent_skill.get("source") or {}, parent_stamp),
                "parent_record_sha256": _canonical_record_sha256(parent_verified),
                "parent_condition_label": expected_cond_label,
                "parent_raw_record": deepcopy(parent_verified),
                "object_signature": _object_signature(japanese),
                "rule_key": expected_rule,
                "boss_reference_slot": raw_carrier["boss_reference_slot"],
                "boss_record_id": raw_carrier["boss_record_id"],
                "ordinary_child_slot": raw_carrier["ordinary_child_slot"],
                "child_table": child_table,
                "child_record_id": child_id,
                "child_source": _enrich_source(source_answer.get("source") or {}, child_stamp),
                "field_path": raw_carrier["field_path"],
                "raw_value": duration,
                "unit": source_answer.get("unit"),
                "decoded_parent_id": parent_verified.get("patternid"),
                "decoded_child_ability": child_record.get("ability"),
                "decoded_child_skillid0": child_record.get("skillid0"),
                "decoded_child_param0": child_record.get("param0"),
                "decoded_child_skillparam3": child_record.get("skillparam3"),
            }
        )

    if failures:
        report["rejections"].append(
            {"row_id": row.get("row_id"), "reason": "MULTI_SOURCE_GATE", "detail": sorted(set(failures))}
        )
        return True
    if len(branches) != len(pids):
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "MULTI_BRANCH_COUNT_MISMATCH"})
        return True
    if not _all_equal([branch["raw_value"] for branch in branches]):
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "MULTI_DURATION_DIFF"})
        return True
    if len({branch["object_signature"] for branch in branches}) != 1:
        report["rejections"].append({"row_id": row.get("row_id"), "reason": "MULTI_OBJECT_DIFF"})
        return True

    first = branches[0]
    source = _field_source(
        first["child_source"],
        table=first["child_table"],
        record_id=first["child_record_id"],
        layer="CACHE",
        field_path=first["field_path"],
    )
    answer = _base_answer(
        data=data,
        row=row,
        rule_key=expected_rule,
        duration=first["raw_value"],
        source=source,
        association_note="有正文 pattern 逐档对象和时长一致；具体分支未定位",
        binding={
            "kind": "multi_pattern_conditional_duration",
            "source_row_id": row.get("row_id"),
            "branch_count": len(branches),
            "branch_selection_resolved": False,
            "branches": branches,
        },
    )
    index = _append_answer(row, answer)
    if index >= 0:
        report["answers_added"] += 1
        report["additions"].append(
            {
                "row_id": row.get("row_id"),
                "kind": mode,
                "answer_index": index,
                "rule_key": expected_rule,
                "record_id": first["child_record_id"],
                "source_json_pointer": source["json_pointer"],
                "raw_value": first["raw_value"],
                "branch_count": len(branches),
            }
        )
    else:
        report["skipped"].append({"row_id": row.get("row_id"), "reason": "ALREADY_PRESENT_OR_CONFLICT", "code": index})
    return True


def apply_to_groups(data, cid: int, groups: list[dict[str, Any]]) -> dict[str, Any]:
    """Append source-derived B18 partial duration answers in memory.

    The function is intentionally additive: existing answers and hints are not
    removed or rewritten, and rows with another duration carrier are skipped.
    """
    report = {
        "scope": SCOPE,
        "cid": cid,
        "answers_added": 0,
        "additions": [],
        "rejections": [],
        "skipped": [],
        "hold_guard_rows_seen": 0,
    }
    if not _yg(data, cid):
        return report
    pattern_skills = _pattern_skill_index(groups, cid)
    row_ids = [row.get("row_id") for _, _, row in _all_rows(groups)]
    if len(set(row_ids)) != len(row_ids):
        report["rejections"].append({"reason": "DUPLICATE_ROW_ID"})
        return report

    for group, skill, row in list(_all_rows(groups)):
        row_id = row.get("row_id") or ""
        if row_id in HOLD_ROW_IDS:
            report["hold_guard_rows_seen"] += 1
            report["skipped"].append({"row_id": row_id, "reason": "HOLD_18"})
            continue
        if row_id in BLOCKED_MULTI_NO_BRANCH:
            report["skipped"].append({"row_id": row_id, "reason": "NO_REVIEWED_MULTI_BRANCH_METADATA"})
            continue
        # Static reviewed admission boundary. Current numeric values and source
        # stamps are still read live from Inputs and the original record index.
        if row_id not in ADMITTED_ROW_IDS:
            continue
        if _already_duration(row):
            report["skipped"].append({"row_id": row_id, "reason": "DURATION_ALREADY_PRESENT"})
            continue
        if _apply_ability3000(data, cid, group, skill, row, report):
            continue
        _apply_multi_pattern(data, cid, group, skill, row, pattern_skills, report)
    return report
