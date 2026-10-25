"""Strict resolver for the 3005 -> bosspattern -> bossskill.s_ability chain.

This module intentionally stops at configuration edges.  It does not calculate
seconds, inspect HP, infer runtime activation, or merge same-numbered records from
different namespaces.  The public contract is documented in CANDIDATE_INTERFACE.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

CONTRACT_VERSION = "grant-resolver/v1"
RUNTIME_STATUS = "CONFIG_EDGE_CANDIDATE_ONLY"
INTERPRETATION_STATUS = "CONFIG_REFERENCE_VERIFIED_RUNTIME_UNPROVEN"
ROOT_ABILITY = 3005
COMPANION_ABILITY = 3000
ATTACK_INTERVAL_ABILITY = 2012

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
COMMON_DIR = PROJECT_ROOT / "scripts" / "character_skills"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

import common as C  # noqa: E402

SLOT_RE = re.compile(r"^skillid(\d+)$")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_record(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _as_reference(value: Any) -> int | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


@dataclass
class Lookup:
    """One namespace+ID lookup, including ambiguity/source failures."""

    records: list[dict[str, Any]] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)


class RecordStore(Protocol):
    def lookup(self, table_key: str, ident: int) -> Lookup:
        ...


class DefaultRecordStore:
    """Read-only APK/CACHE store with exact record stamps and strict ambiguity checks."""

    def __init__(self) -> None:
        self.tables = C.Tables()
        self._cache_source_entries: dict[tuple[str, str, int], list[dict[str, Any]]] | None = None

    @staticmethod
    def _cache_meta(table_key: str) -> tuple[str, str, str]:
        _namespace, path, id_field, stem = C.CACHE_TABLES[table_key]
        return path[-1], id_field, stem

    def _load_cache_sources(self) -> dict[tuple[str, str, int], list[dict[str, Any]]]:
        if self._cache_source_entries is not None:
            return self._cache_source_entries
        wanted: dict[tuple[str, str], str] = {}
        for key in C.CACHE_TABLES:
            table_name, id_field, stem = self._cache_meta(key)
            wanted[(f"CACHE/{stem}.data5.json.raw", table_name)] = id_field
        index: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
        with C.RECORDS_JSONL.open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                source_key = row.get("source_key")
                table_name = row.get("table")
                id_field = wanted.get((source_key, table_name))
                if id_field is None or not isinstance(row.get("raw"), dict):
                    continue
                ident = row["raw"].get(id_field)
                if isinstance(ident, bool) or not isinstance(ident, int):
                    continue
                index.setdefault((source_key, table_name, ident), []).append(row)
        self._cache_source_entries = index
        return index

    def _cache_item(self, table_key: str, ident: int, raw: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
        table_name, _id_field, stem = self._cache_meta(table_key)
        source_key = f"CACHE/{stem}.data5.json.raw"
        matches = [
            row for row in self._load_cache_sources().get((source_key, table_name, ident), [])
            if row.get("raw") == raw
        ]
        problems: list[str] = []
        details: list[str] = []
        if len(matches) != 1:
            problems.append("SOURCE_STAMP_MISSING" if not matches else "SOURCE_STAMP_AMBIGUOUS")
            details.append(
                f"{table_key}:{ident} has {len(matches)} exact CACHE source records in {C.RECORDS_JSONL.as_posix()}"
            )
            source: dict[str, Any] = {
                "record_key": None,
                "source_key": source_key,
                "layer": "CACHE",
                "source_verification": "UNVERIFIED",
            }
        else:
            row = matches[0]
            loc = row.get("location") or {}
            begin = loc.get("byte_begin")
            end = loc.get("byte_end_exclusive")
            expected_hash = loc.get("raw_record_sha256")
            actual_hash = None
            decoded_path = C.DECODED / source_key.split("/", 1)[1]
            blob = b''
            if (isinstance(begin, int) and isinstance(end, int)
                    and 0 <= begin < end <= decoded_path.stat().st_size):
                with decoded_path.open("rb") as fh:
                    fh.seek(begin)
                    blob = fh.read(end - begin)
                    actual_hash = hashlib.sha256(blob).hexdigest()
            if not expected_hash or actual_hash != expected_hash:
                problems.append("SOURCE_HASH_MISMATCH")
                details.append(
                    f"{table_key}:{ident} CACHE raw byte hash {actual_hash!r} != stamp {expected_hash!r}"
                )
            try:
                decoded_record = json.loads(blob)
            except (ValueError, UnicodeDecodeError):
                decoded_record = None
            if decoded_record != raw:
                problems.append("SOURCE_RAW_OBJECT_MISMATCH")
                details.append(f"{table_key}:{ident} returned raw differs from its decoded byte slice")
            source = {
                "record_key": row.get("record_key"),
                "source_key": source_key,
                "layer": "CACHE",
                "snapshot_id": row.get("snapshot_id"),
                "original_file": row.get("original_file"),
                "source_sha256": row.get("source_sha256"),
                "table": table_name,
                "table_path": row.get("table_path"),
                "json_pointer": loc.get("json_pointer"),
                "ordinal_zero_based": loc.get("ordinal_zero_based"),
                "byte_begin": begin,
                "byte_end_exclusive": end,
                "raw_record_sha256": expected_hash,
                "source_verification": "VERIFIED_RAW_BYTES" if not problems else "FAILED",
            }
        return {"raw": raw, "source": source}, problems, details

    def _apk_item(self, table_key: str, ident: int, raw: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
        problems: list[str] = []
        details: list[str] = []
        fname = C.APK_TABLES[table_key][1]
        try:
            loc = C.apk_location(fname, table_key, ident, raw)
        except (KeyError, TypeError, ValueError) as exc:
            problems.append("SOURCE_STAMP_MISSING")
            details.append(f"{table_key}:{ident} APK source stamp failed: {exc}")
            source: dict[str, Any] = {
                "record_key": None,
                "source_key": f"APK/{fname}",
                "layer": "APK",
                "source_verification": "UNVERIFIED",
            }
        else:
            actual_hash = _sha256_record(raw)
            if not loc.get("json_pointer") or actual_hash != loc.get("raw_record_sha256"):
                problems.append("SOURCE_HASH_MISMATCH" if actual_hash != loc.get("raw_record_sha256") else "SOURCE_STAMP_MISSING")
                details.append(f"{table_key}:{ident} APK canonical source hash/pointer check failed")
            loc["source_verification"] = "VERIFIED_RAW_BYTES" if not problems else "FAILED"
            source = loc
        return {"raw": raw, "source": source}, problems, details

    def lookup(self, table_key: str, ident: int) -> Lookup:
        table = self.tables(table_key)
        cache_rows = list(table.cache.get(ident, []))
        apk_rows = list(table.apk.get(ident, []))
        reasons: list[str] = []
        details: list[str] = []
        if not cache_rows and not apk_rows:
            reasons.append("MISSING_RECORD")
            details.append(f"{table_key}:{ident} is absent from CACHE and APK in this namespace")
        if cache_rows and apk_rows:
            reasons.append("DUAL_SOURCE_RECORD")
            details.append(
                f"{table_key}:{ident} exists in both CACHE ({len(cache_rows)}) and APK ({len(apk_rows)}); "
                "no layer was silently preferred"
            )
        if len(cache_rows) > 1 or len(apk_rows) > 1:
            reasons.append("NON_UNIQUE_RECORD")
            details.append(
                f"{table_key}:{ident} has {len(cache_rows)} CACHE and {len(apk_rows)} APK records"
            )
        records: list[dict[str, Any]] = []
        for raw in cache_rows:
            item, item_problems, item_details = self._cache_item(table_key, ident, raw)
            records.append(item)
            reasons.extend(item_problems)
            details.extend(item_details)
        for raw in apk_rows:
            item, item_problems, item_details = self._apk_item(table_key, ident, raw)
            records.append(item)
            reasons.extend(item_problems)
            details.extend(item_details)
        return Lookup(records=records, reason_codes=reasons, details=details)


class GrantResolver:
    """Resolve one explicitly described grant path without semantic calculation."""

    def __init__(self, store: RecordStore | None = None) -> None:
        self.store = store or DefaultRecordStore()

    def resolve_sympathy(self, sympathy_id: int | str) -> dict[str, Any]:
        ident = _as_reference(sympathy_id)
        if ident is None:
            return self._empty_rejection("sympathy", sympathy_id, "INVALID_QUERY_ID", "sympathy ID is not a positive integer")
        run = _ResolutionRun(self.store, {"mode": "sympathy", "id": ident})
        sympathy = run.node_for_reference(
            "sympathy_skilllist", ident, role="sympathy", reference_field="query", raw_value=ident
        )
        if sympathy is None:
            return run.finish()
        run.chain["sympathy"] = {"node_id": sympathy["node_id"]}
        ability0 = _as_reference(sympathy["raw"].get("ability0"))
        if ability0 is None:
            run.reject(
                "SYMPATHY_ABILITY0_MISSING",
                "sympathy_skill_info.ability0 is absent, zero, or not an integer reference",
                node_id=sympathy["node_id"],
                field="ability0",
                raw_value=sympathy["raw"].get("ability0"),
            )
            root = None
        else:
            root = run.node_for_reference(
                "skilllist",
                ability0,
                role="ordinary_root",
                reference_field="sympathy_skill_info.ability0",
                raw_value=sympathy["raw"].get("ability0"),
                parent=sympathy,
            )
        if root is not None:
            run.resolve_root(root)
        return run.finish()

    def resolve_ordinary(self, root_id: int | str) -> dict[str, Any]:
        ident = _as_reference(root_id)
        if ident is None:
            return self._empty_rejection("ordinary", root_id, "INVALID_QUERY_ID", "ordinary root ID is not a positive integer")
        run = _ResolutionRun(self.store, {"mode": "ordinary", "id": ident})
        root = run.node_for_reference(
            "skilllist", ident, role="ordinary_root", reference_field="query", raw_value=ident
        )
        if root is not None:
            run.resolve_root(root)
        return run.finish()

    @staticmethod
    def _empty_rejection(mode: str, raw_id: Any, code: str, message: str) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "query": {"mode": mode, "id": raw_id},
            "status": "rejected",
            "runtime_status": RUNTIME_STATUS,
            "interpretation_status": INTERPRETATION_STATUS,
            "reason_codes": [code],
            "rejections": [{"code": code, "message": message}],
            "nodes": [],
            "edges": [],
            "chain": _empty_chain(),
            "consumer_payload": _empty_consumer_payload(),
            "limits": _limits(),
        }


def _empty_chain() -> dict[str, Any]:
    return {
        "sympathy": None,
        "ordinary_root": None,
        "companion_subskills": [],
        "boss_pattern": None,
        "boss_slots": [],
        "attack_interval_2012_grants": [],
    }


def _empty_consumer_payload() -> dict[str, Any]:
    return {
        "attack_interval_2012": [],
        "companion_skills": [],
        "damage_only_boss_slots": [],
        "non_2012_s_ability_links": [],
    }


def _limits() -> list[str]:
    return [
        "Configuration references only; runtime loading, activation, targeting, and refresh/expiry are unproven.",
        "No seconds or final attack interval is calculated.",
        "No HP field is read or modified.",
        "Same-numbered IDs are distinct when their tables/namespaces differ.",
        "str0 is resolved only in bosspattern; no same-number skilllist fallback is allowed.",
    ]


class _ResolutionRun:
    def __init__(self, store: RecordStore, query: dict[str, Any]) -> None:
        self.store = store
        self.query = query
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self.rejections: list[dict[str, Any]] = []
        self.chain = _empty_chain()
        self.consumer = _empty_consumer_payload()

    def reject(
        self,
        code: str,
        message: str,
        *,
        node_id: str | None = None,
        field: str | None = None,
        raw_value: Any = None,
        details: list[str] | None = None,
    ) -> None:
        entry: dict[str, Any] = {"code": code, "message": message}
        if node_id is not None:
            entry["node_id"] = node_id
        if field is not None:
            entry["field"] = field
        if raw_value is not None:
            entry["raw_value"] = raw_value
        if details:
            entry["details"] = details
        self.rejections.append(entry)

    def _edge(
        self,
        *,
        parent: dict[str, Any] | None,
        target: dict[str, Any] | None,
        table_key: str,
        reference_field: str,
        raw_value: Any,
        resolved: bool,
    ) -> dict[str, Any]:
        source = (parent or {}).get("source") or {}
        edge = {
            "edge_id": f"E{len(self.edges) + 1:04d}",
            "from_node_id": (parent or {}).get("node_id"),
            "to_node_id": (target or {}).get("node_id"),
            "target_table": table_key,
            "reference_field": reference_field,
            "raw_value": raw_value,
            "resolved": resolved,
            "source_record_key": source.get("record_key"),
            "source_layer": source.get("layer"),
            "raw_record_sha256": source.get("raw_record_sha256"),
        }
        self.edges.append(edge)
        return edge

    def node_for_reference(
        self,
        table_key: str,
        ident: int,
        *,
        role: str,
        reference_field: str,
        raw_value: Any,
        parent: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        lookup = self.store.lookup(table_key, ident)
        for code, detail in zip(lookup.reason_codes, lookup.details or [None] * len(lookup.reason_codes)):
            self.reject(
                code,
                f"Cannot uniquely resolve {table_key}:{ident} in its own namespace",
                node_id=(parent or {}).get("node_id"),
                field=reference_field,
                raw_value=raw_value,
                details=[detail] if detail else None,
            )
        if lookup.reason_codes:
            self._edge(
                parent=parent,
                target=None,
                table_key=table_key,
                reference_field=reference_field,
                raw_value=raw_value,
                resolved=False,
            )
            return None
        if len(lookup.records) != 1:
            self.reject(
                "NON_UNIQUE_RECORD",
                f"Expected one record for {table_key}:{ident}, found {len(lookup.records)}",
                node_id=(parent or {}).get("node_id"),
                field=reference_field,
                raw_value=raw_value,
            )
            self._edge(parent=parent, target=None, table_key=table_key, reference_field=reference_field,
                       raw_value=raw_value, resolved=False)
            return None
        item = lookup.records[0]
        raw = item.get("raw")
        source = item.get("source") or {}
        parent_source = (parent or {}).get('source') or {}
        if (source.get('layer') != 'CACHE'
                or (parent is not None and
                    (parent_source.get('layer') != source.get('layer')
                     or parent_source.get('snapshot_id') != source.get('snapshot_id')))):
            self.reject('CROSS_LAYER_OR_SNAPSHOT_EDGE',
                        f'{table_key}:{ident} is outside the same CACHE snapshot chain',
                        node_id=(parent or {}).get('node_id'),
                        field=reference_field, raw_value=raw_value)
            self._edge(parent=parent, target=None, table_key=table_key,
                       reference_field=reference_field, raw_value=raw_value, resolved=False)
            return None
        id_field = C.CACHE_TABLES[table_key][2]
        if not isinstance(raw, dict) or raw.get(id_field) != ident:
            self.reject(
                "RECORD_ID_MISMATCH",
                f"{table_key} record does not carry {id_field}={ident}",
                node_id=(parent or {}).get("node_id"),
                field=reference_field,
                raw_value=raw_value,
            )
            self._edge(parent=parent, target=None, table_key=table_key, reference_field=reference_field,
                       raw_value=raw_value, resolved=False)
            return None
        if source.get("source_verification") != "VERIFIED_RAW_BYTES":
            self.reject(
                "SOURCE_STAMP_MISSING",
                f"{table_key}:{ident} lacks a verified source stamp",
                node_id=(parent or {}).get("node_id"),
                field=reference_field,
                raw_value=raw_value,
            )
            self._edge(parent=parent, target=None, table_key=table_key, reference_field=reference_field,
                       raw_value=raw_value, resolved=False)
            return None
        node_id = f"{table_key}:{ident}"
        node = self.nodes.get(node_id)
        if node is None:
            node = {
                "node_id": node_id,
                "table": table_key,
                "namespace": C.CACHE_TABLES[table_key][0],
                "id": ident,
                "role": role,
                "raw": raw,
                "source": source,
            }
            self.nodes[node_id] = node
        if parent is not None:
            self._edge(
                parent=parent,
                target=node,
                table_key=table_key,
                reference_field=reference_field,
                raw_value=raw_value,
                resolved=True,
            )
        return node

    def _valid_ref_or_reject(
        self,
        value: Any,
        *,
        parent: dict[str, Any],
        field_name: str,
        missing_code: str,
        invalid_code: str,
    ) -> int | None:
        if value in (None, "", 0):
            self.reject(
                missing_code,
                f"{field_name} is absent or zero",
                node_id=parent["node_id"],
                field=field_name,
                raw_value=value,
            )
            self._edge(parent=parent, target=None, table_key="", reference_field=field_name,
                       raw_value=value, resolved=False)
            return None
        ident = _as_reference(value)
        if ident is None:
            self.reject(
                invalid_code,
                f"{field_name} is not an integer reference",
                node_id=parent["node_id"],
                field=field_name,
                raw_value=value,
            )
            self._edge(parent=parent, target=None, table_key="", reference_field=field_name,
                       raw_value=value, resolved=False)
            return None
        return ident

    def resolve_root(self, root: dict[str, Any]) -> None:
        self.chain["ordinary_root"] = {"node_id": root["node_id"]}
        ability = _as_reference(root["raw"].get("ability"))
        if ability != ROOT_ABILITY:
            self.reject(
                "ROOT_ABILITY_NOT_3005",
                f"ordinary root ability is {ability!r}, expected {ROOT_ABILITY}",
                node_id=root["node_id"],
                field="ability",
                raw_value=root["raw"].get("ability"),
            )
            return

        sub = root["raw"].get("sub")
        if not isinstance(sub, list):
            self.reject(
                "ROOT_SUB_INVALID",
                "ordinary root sub must be a list of skilllist references",
                node_id=root["node_id"],
                field="sub",
                raw_value=sub,
            )
        else:
            for index, sub_value in enumerate(sub):
                if sub_value in (None, 0, ""):
                    continue
                sub_id = self._valid_ref_or_reject(
                    sub_value,
                    parent=root,
                    field_name=f"sub[{index}]",
                    missing_code="ROOT_SUB_INVALID",
                    invalid_code="ROOT_SUB_INVALID",
                )
                if sub_id is None:
                    continue
                companion = self.node_for_reference(
                    "skilllist",
                    sub_id,
                    role="companion_subskill",
                    reference_field=f"sub[{index}]",
                    raw_value=sub_value,
                    parent=root,
                )
                if companion is None:
                    continue
                companion_ability = _as_reference(companion["raw"].get("ability"))
                if companion_ability != COMPANION_ABILITY:
                    self.reject(
                        "COMPANION_ABILITY_NOT_3000",
                        f"companion ability is {companion_ability!r}, expected {COMPANION_ABILITY}",
                        node_id=companion["node_id"],
                        field="ability",
                        raw_value=companion["raw"].get("ability"),
                    )
                self.chain["companion_subskills"].append(
                    {
                        "node_id": companion["node_id"],
                        "reference_field": f"sub[{index}]",
                        "ability": companion["raw"].get("ability"),
                    }
                )
                self.consumer["companion_skills"].append(
                    {
                        "node_id": companion["node_id"],
                        "reference_field": f"sub[{index}]",
                        "ability": companion["raw"].get("ability"),
                        "raw": companion["raw"],
                        "source": companion["source"],
                    }
                )

        pattern_id = self._valid_ref_or_reject(
            root["raw"].get("str0"),
            parent=root,
            field_name="str0",
            missing_code="ROOT_STR0_MISSING",
            invalid_code="ROOT_STR0_INVALID",
        )
        if pattern_id is None:
            return
        pattern = self.node_for_reference(
            "bosspattern",
            pattern_id,
            role="boss_pattern",
            reference_field="str0",
            raw_value=root["raw"].get("str0"),
            parent=root,
        )
        if pattern is None:
            return
        self.chain["boss_pattern"] = {"node_id": pattern["node_id"]}
        self.resolve_pattern_slots(pattern)

    def resolve_pattern_slots(self, pattern: dict[str, Any]) -> None:
        fields: list[tuple[int, str]] = []
        for name in pattern["raw"]:
            match = SLOT_RE.match(name)
            if match:
                fields.append((int(match.group(1)), name))
        fields.sort()
        if not fields:
            self.reject(
                "PATTERN_HAS_NO_BOSS_SKILLS",
                "bosspattern contains no skillidN references",
                node_id=pattern["node_id"],
            )
            return
        for _ordinal, field_name in fields:
            raw_value = pattern["raw"].get(field_name)
            if raw_value in (None, 0, ""):
                continue
            boss_id = self._valid_ref_or_reject(
                raw_value,
                parent=pattern,
                field_name=field_name,
                missing_code="BOSS_SLOT_REFERENCE_MISSING",
                invalid_code="BOSS_SLOT_REFERENCE_INVALID",
            )
            if boss_id is None:
                continue
            boss = self.node_for_reference(
                "bossskill",
                boss_id,
                role="boss_skill",
                reference_field=field_name,
                raw_value=raw_value,
                parent=pattern,
            )
            if boss is None:
                continue
            s_ability_value = boss["raw"].get("s_ability")
            slot = {
                "slot_field": field_name,
                "boss_node_id": boss["node_id"],
                "effect_type_skillid0": boss["raw"].get("skillid0"),
                "s_ability": s_ability_value,
                "s_ability_target_node_id": None,
            }
            if s_ability_value in (None, 0, ""):
                slot["link_status"] = "NO_S_ABILITY_EDGE_DAMAGE_ONLY"
                self.chain["boss_slots"].append(slot)
                self.consumer["damage_only_boss_slots"].append(
                    {
                        "slot_field": field_name,
                        "boss_node_id": boss["node_id"],
                        "s_ability": s_ability_value,
                        "raw": boss["raw"],
                        "source": boss["source"],
                    }
                )
                continue
            target_id = self._valid_ref_or_reject(
                s_ability_value,
                parent=boss,
                field_name="s_ability",
                missing_code="S_ABILITY_REFERENCE_MISSING",
                invalid_code="S_ABILITY_REFERENCE_INVALID",
            )
            if target_id is None:
                self.chain["boss_slots"].append(slot)
                continue
            target = self.node_for_reference(
                "skilllist",
                target_id,
                role="s_ability_target",
                reference_field="s_ability",
                raw_value=s_ability_value,
                parent=boss,
            )
            if target is None:
                slot["link_status"] = "S_ABILITY_TARGET_UNRESOLVED"
                self.chain["boss_slots"].append(slot)
                continue
            slot["s_ability_target_node_id"] = target["node_id"]
            target_ability = _as_reference(target["raw"].get("ability"))
            if target_ability == ATTACK_INTERVAL_ABILITY:
                slot["link_status"] = "ATTACK_INTERVAL_2012_EDGE"
                grant_id = f"{boss['node_id']}--{field_name}-->{target['node_id']}"
                grant = {
                    "grant_id": grant_id,
                    "boss_node_id": boss["node_id"],
                    "pattern_slot": field_name,
                    "target_node_id": target["node_id"],
                    "target_namespace": target["namespace"],
                    "ability": target["raw"].get("ability"),
                    "raw": target["raw"],
                    "source": target["source"],
                    "path_node_ids": [],
                    "evidence_records": {
                        "ordinary_root": self._evidence_for_node((self.chain.get("ordinary_root") or {}).get("node_id")),
                        "companion_subskills": [
                            self._evidence_for_node(item.get("node_id"))
                            for item in self.chain["companion_subskills"]
                        ],
                        "boss_pattern": self._evidence_for_node(pattern["node_id"]),
                        "boss_slot": self._evidence_for_node(boss["node_id"]),
                        "s_ability_target": self._evidence_for_node(target["node_id"]),
                    },
                    "semantic_status": "RAW_ONLY_NOT_INTERPRETED",
                    "interpretation_status": INTERPRETATION_STATUS,
                }
                # The path is filled after the root context is known below.
                grant["path_node_ids"] = self._path_to(pattern, boss, target)
                self.chain["attack_interval_2012_grants"].append(
                    {
                        "grant_id": grant_id,
                        "boss_node_id": boss["node_id"],
                        "pattern_slot": field_name,
                        "target_node_id": target["node_id"],
                    }
                )
                self.consumer["attack_interval_2012"].append(grant)
            else:
                slot["link_status"] = "NON_2012_S_ABILITY_EDGE"
                self.consumer["non_2012_s_ability_links"].append(
                    {
                        "slot_field": field_name,
                        "boss_node_id": boss["node_id"],
                        "target_node_id": target["node_id"],
                        "ability": target_ability,
                        "raw": target["raw"],
                        "source": target["source"],
                    }
                )
            self.chain["boss_slots"].append(slot)

    def _evidence_for_node(self, node_id: str | None) -> dict[str, Any] | None:
        if node_id is None:
            return None
        node = self.nodes.get(node_id)
        if node is None:
            return None
        return {"node_id": node_id, "raw": node["raw"], "source": node["source"]}

    def _path_to(self, pattern: dict[str, Any], boss: dict[str, Any], target: dict[str, Any]) -> list[str]:
        root_id = (self.chain.get("ordinary_root") or {}).get("node_id")
        path = [root_id, pattern["node_id"], boss["node_id"], target["node_id"]]
        return [entry for entry in path if entry]

    def finish(self) -> dict[str, Any]:
        grants = self.consumer["attack_interval_2012"]
        if not grants:
            self.reject(
                "NO_2012_S_ABILITY",
                f"the resolved chain contains no ordinary skilllist target with ability={ATTACK_INTERVAL_ABILITY}",
            )
        elif len(grants) > 1:
            self.reject(
                "MULTIPLE_2012_PATHS",
                f"the resolved chain contains {len(grants)} distinct attack-interval grant paths",
            )
        reason_codes = list(dict.fromkeys(entry["code"] for entry in self.rejections))
        status = "resolved_candidate" if not reason_codes and len(grants) == 1 else "rejected"
        return {
            "contract_version": CONTRACT_VERSION,
            "query": self.query,
            "status": status,
            "runtime_status": RUNTIME_STATUS,
            "interpretation_status": INTERPRETATION_STATUS,
            "reason_codes": reason_codes,
            "rejections": self.rejections,
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "chain": self.chain,
            "consumer_payload": self.consumer,
            "limits": _limits(),
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve 3005/boss-pattern/2012 configuration grant edges")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sympathy", metavar="ID", help="resolve sympathy_skill_info ability0")
    group.add_argument("--ordinary", metavar="ID", help="resolve an ordinary skilllist root")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    C.enable_utf8_console()
    args = _build_parser().parse_args(argv)
    resolver = GrantResolver()
    if args.sympathy is not None:
        result = resolver.resolve_sympathy(args.sympathy)
    else:
        result = resolver.resolve_ordinary(args.ordinary)
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2, separators=(",", ":") if args.compact else None))
    return 0 if result["status"] == "resolved_candidate" else 2


if __name__ == "__main__":
    raise SystemExit(main())
