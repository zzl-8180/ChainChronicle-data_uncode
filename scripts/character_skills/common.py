"""Shared loaders for the character-skill interpretation pipeline (P1).

Read-only over existing unpacked artefacts. No network, no re-unpacking.

Namespaces are kept strictly apart: a reference ID is always resolved inside the
*same* table it came from (skilllist / heroicskilllist / bossskill / bosspattern /
denju / ...), and the cache snapshot is preferred per ID with an APK fallback only
when that ID is missing from the cache. Records are never merged field by field.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "output" / "cache_full_20261015_v3"
DECODED = CACHE_DIR / "decoded"
BASE_MASTER = ROOT / "output" / "base_master"
RECORDS_JSONL = CACHE_DIR / "records.jsonl"
ROSTER_JSON = ROOT / "output" / "char_roster" / "data" / "playable_characters.json"
ROSTER_OTHER_JSON = ROOT / "output" / "char_roster" / "data" / "other_characters.json"
CARD_COMPARISON = ROOT / "output" / "card_comparison_cid30236"
REFERENCE_ANALYSIS = ROOT / "output" / "reference_analysis" / "claude_cc_site_pages"

SNAPSHOT_ID = "cache_full_20261015_v3"

# ---------------------------------------------------------------------------
# table descriptions
# ---------------------------------------------------------------------------
# key -> (namespace label, relative path inside the .data5.json.raw, id field, source file stem)
CACHE_TABLES = {
    "skilllist": ("普通技能/能力", ("skilllist",), "skillid", "skilllist"),
    "heroicskilllist": ("英雄技", ("skilllist",), "skillid", "heroicskilllist"),
    "sympathy_skilllist": ("共鸣", ("sympathy_skill_info",), "_id", "sympathy_skilllist"),
    "extraabilitylist": ("Extra", ("extra_ability_info",), "cid", "extraabilitylist"),
    "leaderabilityinfo": ("Leader", ("leader_ability",), "cid", "leaderabilityinfo"),
    "jobabilityinfo": ("Class", ("job_ability",), None, "jobabilityinfo"),
    "passivelist": ("PASSIVE", ("passive_info",), "cid", "passivelist"),
    "supporterskill": ("羁绊(支援)", ("supporterskill",), "ability_id", "supporterskill"),
    "crossworldabilitylist": ("CrossWorld", ("crossworld_ability_info",), "_id", "crossworldabilitylist"),
    "denju": ("传授", ("denju",), "denju_id", "denju"),
    "denju_lblist": ("传授突破", ("denju_limit_break_info",), "cid", "denju_lblist"),
    "charainfo": ("角色", ("charainfo",), "cid", "charainfo"),
    "bosspattern": ("Boss/必杀 pattern", ("bossinfo", "bosspattern"), "patternid", "bossinfo"),
    "bossskill": ("Boss/必杀 skill", ("bossinfo", "bossskill"), "skillid", "bossinfo"),
    "battleinfo": ("战场背景", ("battle_bg",), "id", "battleinfo"),
    "worldinfo_chara_place": ("所属", ("chara_place",), "id", "worldinfo"),
}

APK_TABLES = {
    "skilllist": ("普通技能/能力", "_mdSkill.json", ("skilllist",), "skillid"),
    "bosspattern": ("Boss/必杀 pattern", "_mdBossInfo.json", ("bosspattern",), "patternid"),
    "bossskill": ("Boss/必杀 skill", "_mdBossInfo.json", ("bossskill",), "skillid"),
    "charainfo": ("角色", "_mdCharacter.json", ("charainfo",), "cid"),
    "supporterskill": ("羁绊(支援)", "_mdSAbirity.json", ("supporterskill",), "ability_id"),
}

def enable_utf8_console() -> None:
    """Make stdout/stderr able to carry the Japanese/Chinese text this tool prints.

    On a default Chinese Windows console stdout is cp936; any katakana middle dot or
    other unencodable character then raises UnicodeEncodeError. Every entry point
    calls this so the CLI works without the caller having to set PYTHONUTF8.
    """
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


_JSON_CACHE: dict[Path, object] = {}


def load_json(path: Path):
    """Load a JSON document once per process."""
    path = Path(path)
    if path not in _JSON_CACHE:
        with path.open(encoding="utf-8") as fh:
            _JSON_CACHE[path] = json.load(fh)
    return _JSON_CACHE[path]


def _dig(doc, path):
    cur = doc
    for key in path:
        if isinstance(cur, dict):
            cur = cur[key]
        else:
            raise KeyError(path)
    return cur


def cache_rows(key: str) -> list[dict]:
    ns, path, _idf, stem = CACHE_TABLES[key]
    doc = load_json(DECODED / f"{stem}.data5.json.raw")
    return _dig(doc, path)


def apk_rows(key: str) -> list[dict]:
    if key not in APK_TABLES:
        return []
    ns, fname, path, _idf = APK_TABLES[key]
    doc = load_json(BASE_MASTER / fname)
    return _dig(doc, path)


def _index(rows, id_field):
    out = {}
    for r in rows:
        out.setdefault(r[id_field], []).append(r)
    return out


class Table:
    """Per-ID cache-preferred table with an APK fallback in the same namespace."""

    def __init__(self, key: str):
        self.key = key
        self.namespace = CACHE_TABLES[key][0]
        self.id_field = CACHE_TABLES[key][2]
        self.cache = _index(cache_rows(key), self.id_field) if self.id_field else {}
        self.has_apk = key in APK_TABLES
        if self.has_apk:
            apk_field = APK_TABLES[key][3]
            assert apk_field == self.id_field, (key, apk_field, self.id_field)
            self.apk = _index(apk_rows(key), self.id_field)
        else:
            self.apk = {}

    def get(self, ident):
        """Return (record, layer) or (None, None). Cache wins per ID."""
        rows = self.cache.get(ident)
        if rows:
            return rows[0], "CACHE"
        rows = self.apk.get(ident)
        if rows:
            return rows[0], "APK"
        return None, None

    def ids(self):
        return set(self.cache) | set(self.apk)


class Tables:
    def __init__(self):
        self._t: dict[str, Table] = {}

    def __call__(self, key: str) -> Table:
        if key not in self._t:
            self._t[key] = Table(key)
        return self._t[key]

    def get(self, key, ident):
        return self._t[key].get(ident) if key in self._t else self(key).get(ident)


# ---------------------------------------------------------------------------
# byte-level location index (cache side) built from records.jsonl
# ---------------------------------------------------------------------------
_LOCATION: dict | None = None


def _location_index():
    global _LOCATION
    if _LOCATION is not None:
        return _LOCATION
    idx = {}
    with RECORDS_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            stem = r["source_key"].split("/", 1)[1].rsplit(".data5", 1)[0]
            raw = r["raw"]
            if not isinstance(raw, dict):
                continue
            ident = None
            for cand in ("skillid", "patternid", "cid", "denju_id", "_id", "ability_id", "id"):
                v = raw.get(cand)
                if isinstance(v, (int, float, str)) and not isinstance(v, bool):
                    ident = v
                    break
            if ident is None:
                continue
            idx[(stem, r["table"], ident)] = r
    _LOCATION = idx
    return idx


def cache_location(table_key: str, ident) -> dict | None:
    """Byte location of a cache record, keyed by (source stem, table, id)."""
    stem = table_key if table_key in ("skilllist", "heroicskilllist") else table_key
    table = {
        "skilllist": "skilllist",
        "heroicskilllist": "skilllist",
        "bosspattern": "bosspattern",
        "bossskill": "bossskill",
        "charainfo": "charainfo",
        "denju": "denju",
        "sympathy_skilllist": "sympathy_skill_info",
        "extraabilitylist": "extra_ability_info",
        "leaderabilityinfo": "leader_ability",
        "passivelist": "passive_info",
        "supporterskill": "supporterskill",
        "crossworldabilitylist": "crossworld_ability_info",
        "battleinfo": "battle_bg",
    }.get(table_key, table_key)
    row = _location_index().get((stem, table, ident))
    if row is None:
        return None
    return {
        "record_key": row["record_key"],
        "source_key": row["source_key"],
        "layer": row["layer"],
        "original_file": row["original_file"],
        "source_sha256": row["source_sha256"],
        "json_pointer": row["location"]["json_pointer"],
        "byte_begin": row["location"]["byte_begin"],
        "byte_end_exclusive": row["location"]["byte_end_exclusive"],
        "raw_record_sha256": row["location"]["raw_record_sha256"],
    }


_APK_REPORT: dict | None = None


def apk_report() -> dict:
    global _APK_REPORT
    if _APK_REPORT is None:
        _APK_REPORT = load_json(BASE_MASTER / "report.json")
    return _APK_REPORT


def apk_location(fname: str, table_key: str, ident, record: dict) -> dict:
    """Source stamp for an APK-master record (index in the exported JSON + hashes)."""
    doc = load_json(BASE_MASTER / fname)
    ns, path, id_field = APK_TABLES[table_key][0], APK_TABLES[table_key][2], APK_TABLES[table_key][3]
    rows = _dig(doc, path)
    pointer = None
    for i, r in enumerate(rows):
        if r is record:
            pointer = "/" + "/".join(path) + f"/{i}"
            break
    blob = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    rep = apk_report()
    return {
        "record_key": f"APK/{fname}#{pointer}",
        "source_key": f"APK/{fname}",
        "layer": "APK",
        "original_file": f"output/base_master/{fname}",
        "json_pointer": pointer,
        "raw_record_sha256": hashlib.sha256(blob).hexdigest(),
        "master_source": rep.get("source"),
        "master_source_sha256": rep.get("source_sha256"),
        "master_converted_sha256": rep.get("converted_sha256"),
    }


def location(table_key: str, ident, layer: str, record: dict) -> dict:
    """Uniform source stamp for a resolved record."""
    if layer == "CACHE":
        loc = cache_location(table_key, ident)
        if loc:
            return loc
        return {
            "record_key": f"CACHE/{table_key}.data5.json.raw#{ident}",
            "source_key": f"CACHE/{table_key}.data5.json.raw",
            "layer": "CACHE",
            "original_file": None,
            "json_pointer": None,
            "note": "定位索引未命中；记录来自解码 JSON",
        }
    fname = APK_TABLES[table_key][1]
    return apk_location(fname, table_key, ident, record)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def roster() -> list[dict]:
    return load_json(ROSTER_JSON)


def write_json(path: Path, obj, *, indent=1):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=indent)
        fh.write("\n")


def write_jsonl(path: Path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n")


def write_csv(path: Path, header, rows):
    import csv

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
