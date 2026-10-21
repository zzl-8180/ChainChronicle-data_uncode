# -*- coding: utf-8 -*-
"""角色技能页全量机器检查（M6，20261021 独立审查整改；此后作为每次变更的固定回归）。

对 output/character_skills/pages 当前交付面（2236 卡 + 入口两页）做一次性全量检查，
替代多轮全量人审（REPORT §10-P1：「对原值/来源/颜色/集合/计数运行一次固定全量机器检查」）。
只读：不修改 pages/_batch/profiles/原始输入的任何文件；报告写到 --out（默认 work/ 下）。

检查项（与整改任务卡 docs/tasks/20261021-character-skills-audit-rectify.md §M6 一致）：
  1 receipt_signature   receipt 状态与签名一致（SUCCESS、无 reuse_blocked、四签名字段
                        等于当前 campaign、run_id 等于所在 cohort run）
  2 artifact_hashes     产物哈希（receipt.files 的 card.json/index.html sha256 == 盘上）
  3 dependencies_29     29 项声明数据依赖存在且哈希未变，dependency_signature 可复算
  4 rows_rowids         行集合：每卡 row_id 唯一、row_class 计数==coverage、
                        HTML data-row-id 集合==card.json 行集合、总量==campaign N_all
  5 source_dereference  行级/逐答案 source 解引用（指针落到真实记录；字段存在；
                        registry 形状按 table/layer 唯一定位；显式 UNKNOWN 定位单列；
                        字段缺失但来源声明显式登记 present:false → PASS-with-note，
                        记入 ok 并单列 noted 明细）
  6 inference_source_coverage  推断答案逐答案 source 覆盖（M2 契约；代码已就绪、
                        统一重建未执行前会以当前缺口数 FAIL，不静默）
  7 inference_value_equality   推断答案原值与来源记录字段值精确相等
  8 chip_evidence_colors       首屏 chip 颜色档位与 evidence 一致（逐行 chip 类多重集
                        == 按答案证据推导；并单列「推断→绿」「确认→橙」事件，应为 0）
  9 campaign_reconciliation    四联计数与 campaign 对账（逐卡 coverage 重新聚合 ==
                        campaign_report coverage/summary；逐卡 summary == policy.metrics）
 10 entry_pages         入口页指标与 run 指针一致（复用 card_page_index.entry_pages_consistency）

已知不检查（显式声明，不冒充全查）：source 中原始 .data5 字节范围/原始记录 sha256
（属 work/ 原始文件字节层，不在本交付面重读范围）；details 折叠层文本逐字比对；
浏览器渲染/交互（见入口页任务卡的 localhost 烟雾测试）。

用法（仓库根）：
  & .\\.venv\\Scripts\\python.exe -B scripts/character_skills/card_page_verify_full.py
  可选：--out <path> --pages <dir> --max-details N
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
import traceback
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card_page_cohorts import sha as file_sha
from card_page_dependencies import data_paths
from card_page_policy import metrics as policy_metrics
from card_page_index import entry_pages_consistency, metric_values_from_summary

DEFAULT_PAGES = Path("output/character_skills/pages")
DEFAULT_OUT = Path("work/character_skills_phase2_20261021/verify_full_latest.json")
MAX_DETAILS = 20

# chip 颜色档位映射——与 card_page_render_v2.py:217 EVID_CLASS 及 :329 answer_chip
# 的推导一致（此处独立复刻，避免验证层直接引用渲染实现而失去校验意义）。
EVID_CLASS = {"确认": "ev-conf", "确认（类型外推）": "ev-conf-ext", "确认（部分类型外推）": "ev-conf",
              "推断": "ev-inf", "未知": "ev-unk"}
ROW_DIV_RE = re.compile(r'<div class="row" data-row-id="([^"]+)"')
CHIPS_DIV_RE = re.compile(r'<div class="chips">')
CHIP_CLASS_RE = re.compile(r'<span class="chip (ev-[a-z-]+)"')

# 仅 (table,record_id,layer) 无指针形状（批 5/6/7 值行）的登记表解析：
# (文件, 容器链, ID 字段)；id→record 索引首次使用时建立并复用。
# 依据 card_page_data.precise_source 的定位规则（CACHE→decoded JSON，APK→base_master）。
REGISTRY = {
    ("bossskill", "CACHE"): ("output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw", ("bossinfo", "bossskill"), "skillid"),
    ("bossskill", "APK"): ("output/base_master/_mdBossInfo.json", ("bossskill",), "skillid"),
    ("bosspattern", "CACHE"): ("output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw", ("bossinfo", "bosspattern"), "patternid"),
    ("bosspattern", "APK"): ("output/base_master/_mdBossInfo.json", ("bosspattern",), "patternid"),
    ("skilllist", "CACHE"): ("output/cache_full_20261015_v3/decoded/skilllist.data5.json.raw", ("skilllist",), "skillid"),
    ("skilllist", "APK"): ("output/base_master/_mdSkill.json", ("skilllist",), "skillid"),
}


class Check:
    def __init__(self, name, title):
        self.name = name
        self.title = title
        self.ok = 0
        self.failed = 0
        self.counters = {}
        self.details = []
        self.noted = []  # PASS-with-note 明细（如基线显式登记缺失，单列不混入 FAIL）

    def add(self, ok, detail=None, **counters):
        if ok:
            self.ok += 1
        else:
            self.failed += 1
            if detail is not None:
                if len(self.details) < MAX_DETAILS:
                    self.details.append(detail)
                elif len(self.details) == MAX_DETAILS:
                    self.details.append("…（超出明细上限，完整计数见 counters）")
        for k, v in counters.items():
            self.counters[k] = self.counters.get(k, 0) + v

    def note(self, detail):
        """登记一条 PASS-with-note（计入 ok，同时单列于报告 noted 列表）。"""
        self.ok += 1
        self.noted.append(detail)

    def done(self):
        return dict(check=self.name, title=self.title, status="PASS" if self.failed == 0 else "FAIL",
                    ok=self.ok, failed=self.failed, counters=self.counters, details=self.details,
                    noted=self.noted)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def pointer_get(doc, pointer: str):
    """RFC 6901 风格指针取值；失败抛 KeyError/IndexError/ValueError。"""
    if not pointer.startswith("/"):
        raise KeyError(f"非根相对指针 {pointer!r}")
    node = doc
    for tok in pointer[1:].split("/"):
        tok = tok.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            node = node[int(tok)]
        elif isinstance(node, dict):
            if tok not in node:
                raise KeyError(f"指针 {pointer!r} 在键 {tok!r} 处落空")
            node = node[tok]
        else:
            raise KeyError(f"指针 {pointer!r} 在 {tok!r} 处无法继续下探（{type(node).__name__}）")
    return node


class Docs:
    """惰性加载并缓存被解引用的 JSON 文档；registry 形状按 (文件,容器链) 建 id 索引。"""

    def __init__(self, root: Path):
        self.root = root
        self.docs = {}
        self.indexes = {}

    def _map_prefix(self, sk: str):
        if sk.startswith("CACHE/"):
            p = self.root / "output/cache_full_20261015_v3/decoded" / sk[len("CACHE/"):]
            if p.is_file():
                return p
        elif sk.startswith("APK/"):
            p = self.root / "output/base_master" / sk[len("APK/"):]
            if p.is_file():
                return p
        return None

    def file_for(self, src: dict):
        """source 声明 → 解码 JSON 文档路径。
        original_file 仅在其为 JSON 文档（.json/.json.raw）时采用；指向 work/ 原始
        *.data5 二进制时改用 source_key / record_key 前缀映射（CACHE/→decoded，
        APK/→base_master）。"""
        of = src.get("original_file")
        norm = str(of).replace("\\", "/") if of else None
        if norm and (norm.endswith(".json") or norm.endswith(".json.raw")):
            p = self.root / norm
            if p.is_file():
                return p
        sk = src.get("source_key") or ""
        p = self._map_prefix(sk) if sk else None
        if p:
            return p
        rk = src.get("record_key") or ""
        if "#" in rk:
            p = self._map_prefix(rk.split("#", 1)[0])
            if p:
                return p
        if norm:
            return self.root / norm
        return None

    def doc(self, path: Path):
        key = str(path)
        if key not in self.docs:
            self.docs[key] = load_json(path)
        return self.docs[key]

    def registry_index(self, rel: str, containers, idkey: str):
        key = (rel, containers, idkey)
        if key not in self.indexes:
            node = self.doc(self.root / rel)
            for c in containers:
                node = node[c]
            idx = {}
            for r in node:
                idx.setdefault(r.get(idkey), []).append(r)
            self.indexes[key] = idx
        return self.indexes[key]


def resolve_source(src, docs: Docs):
    """解引用一个 source 声明。返回 (record, error_detail)。
    error_detail None 表示成功。registry 形状按 id 字段唯一匹配（非唯一=失败）。"""
    record_key = src.get("record_key")
    if record_key and src.get("table") is not None:
        parts = str(record_key).split("|")
        if len(parts) == 3 and (parts[0] != str(src.get("table"))
                                or parts[1] != str(src.get("record_id"))
                                or parts[2] != str(src.get("layer"))):
            return None, f"record_key {record_key!r} 与 table/record_id/layer 不一致"
    if src.get("table") is not None and src.get("json_pointer") is None and src.get("source_key") is None:
        spec = REGISTRY.get((str(src.get("table")), str(src.get("layer"))))
        if spec is None:
            return None, f"registry 无 ({src.get('table')},{src.get('layer')}) 形状"
        rel, containers, idkey = spec
        try:
            idx = docs.registry_index(rel, containers, idkey)
        except (OSError, ValueError, KeyError) as e:
            return None, f"registry 文件/容器不可读：{rel} {e}"
        matches = idx.get(src.get("record_id"), [])
        if len(matches) != 1:
            return None, f"registry 匹配 {len(matches)} 条（非唯一/未命中）：{record_key}"
        return matches[0], None
    path = docs.file_for(src)
    if path is None:
        return None, f"无 original_file 且 source_key {src.get('source_key')!r} 前缀不可映射"
    if not path.is_file():
        return None, f"来源文件不存在：{path}"
    try:
        doc = docs.doc(path)
        jp = src.get("json_pointer")
        if jp is None:
            return None, f"json_pointer 为 None（{src.get('source_resolution') or src.get('note') or '无说明'}）"
        return pointer_get(doc, jp), None
    except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
        return None, f"指针落空：{src.get('source_key') or src.get('original_file')}#{src.get('json_pointer')}→{src.get('field')}：{type(e).__name__} {e}"


def field_registered_missing(src, docs: Docs):
    """基线 field_refs 的显式登记缺失判定（两条定位路径统一严格判定）：
    ① json_pointer 直指字段（.../<record>/<field>）；
    ② json_pointer 指向记录本体（.../<record>）且 field/field_path 指定字段。
    豁免必须同时满足：
    ① src 显式登记 present:false 且 raw_value 为 None（零/null/缺失不互换——有非空值却声明缺失不豁免）；
    ② 主 json_pointer 的父路径本身可解引用（失败确实只发生在末段字段；父记录经主指针解析，不接受仅用备用 location 兜底）；
    ③ 若带 location.json_pointer，主指针父路径必须与其一致（备用 location 不得纠正主指针）；
    ④ 父记录身份一致：记录携带声明表的 id 键且值==record_id（防落到其他记录）；
    ⑤ 目标字段在解析到的父记录中确实不存在。
    区分「记录不存在/字段缺失且未登记」（真 FAIL）与「字段缺失但已登记 present:false」
    （项目缺失/null/真实零分别处理约定下的有意登记，应 PASS-with-note）。"""
    if src.get("present") is not False:
        return False, None
    if src.get("raw_value") is not None:
        return False, None  # 有非空值却声明缺失：声明与 raw_value 不一致，不豁免
    jp = src.get("json_pointer")
    if not isinstance(jp, str) or not jp.startswith("/"):
        return False, None
    fpath = src.get("field_path") or src.get("field")
    if not fpath:
        return False, None
    field_last = str(fpath).lstrip("/").split("/")[-1]
    jp_clean = jp.rstrip("/")
    last = jp_clean.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")
    if last == field_last:
        # 路径①：json_pointer 直指字段，父路径为去掉末段
        if "/" not in jp_clean[1:]:
            return False, None
        parent = jp_clean.rsplit("/", 1)[0]
    else:
        # 路径②：json_pointer 指向记录本体，字段由 field/field_path 指定
        parent = jp_clean
    # ② 主指针父路径必须自身可解引用（失败只发生在末段）
    probe = dict(src, json_pointer=parent)
    record, err = resolve_source(probe, docs)
    if err is not None:
        return False, None  # 主指针父记录解不动 → 真 FAIL（错误索引/坏指针不得被豁免）
    # ③ location.json_pointer 若存在，必须与主指针父路径一致
    loc = src.get("location")
    loc_ptr = loc.get("json_pointer") if isinstance(loc, dict) else None
    if loc_ptr is not None and loc_ptr != parent:
        return False, None  # 主指针与 location 不一致 → 不豁免
    # ④ 记录身份核对：解析到的记录必须携带声明表的 id 键且值==record_id
    idkey = {"bossskill": "skillid", "bosspattern": "patternid", "skilllist": "skillid"}.get(str(src.get("table")))
    if idkey:
        if not isinstance(record, dict) or str(record.get(idkey)) != str(src.get("record_id")):
            return False, None
    # ⑤ 目标字段在父记录中确实不存在（字段实际存在 → 不豁免，按正常路径判定）
    if isinstance(record, dict) and field_last in record:
        return False, None
    detail = (f"字段 {fpath!r} 在记录 {src.get('record_key')} 内缺失，基线 field_refs "
              f"显式登记 present:false、raw_value=None"
              f"（主指针父路径 {parent} 可解且与声明记录一致；缺失/null 按约定有意登记）")
    return True, detail


def deref_one(src, docs: Docs):
    """解引用并核字段存在；返回 (status, detail)。status: OK/UNRESOLVED_EXPLICIT/NOTED/FAIL。
    json_pointer 落在标量（部分来源指针已含字段段）且与 field 一致时视为定位到值；
    字段缺失但来源声明显式登记 present:false 且记录本身可解 → NOTED（PASS-with-note）。"""
    if src.get("json_pointer") is None and src.get("source_key") is None and src.get("table") is None:
        return "FAIL", "source 为空，无任何定位字段"
    if src.get("json_pointer") is None and src.get("source_resolution", "").startswith("UNKNOWN"):
        return "UNRESOLVED_EXPLICIT", f"生成期显式未定位（{src.get('source_resolution')}）"
    jp = src.get("json_pointer")
    record, err = resolve_source(src, docs)
    if err is not None:
        registered, ndetail = field_registered_missing(src, docs)
        if registered:
            return "NOTED", ndetail
        return "FAIL", err
    fjp = src.get("field_json_pointer")
    if fjp:
        try:
            pointer_get(docs.doc(docs.file_for(src)), fjp)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
            return "FAIL", f"field_json_pointer 落空 {fjp!r}：{e}"
    field = src.get("field")
    if field and not fjp:
        if isinstance(record, dict):
            try:
                pointer_get(record, field)
            except (ValueError, KeyError, IndexError, TypeError) as e:
                registered, ndetail = field_registered_missing(src, docs)
                if registered:
                    return "NOTED", ndetail
                return "FAIL", f"字段 {field!r} 在记录内落空：{e}"
        elif not (isinstance(jp, str) and jp.rstrip("/").endswith(field)):
            return "FAIL", f"json_pointer {jp!r} 落在标量上，与 field {field!r} 不一致"
    return "OK", None


def value_at(record, field_path):
    return pointer_get(record, field_path) if field_path else record


def numbers_equal(a, b):
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return a == b


def expected_chip_classes(answers, row):
    """按 render_v2.answer_chip 语义推导每行首屏 chip 类多重集（独立复刻）。"""
    out = []
    for a in answers:
        nev = a.get("numeric_evidence") or "未知"
        scope = a.get("evidence_scope")
        scope = [scope] if isinstance(scope, str) else list(scope or [])
        scope += list(row.get("evidence_scope") or [])
        if nev == "确认":
            sl = [str(s) for s in scope if s]
            if not sl or all(s == "REVIEWED_RECORD" for s in sl):
                label = "确认"
            elif all(s == "BY_TYPE_EXTRAPOLATED" for s in sl):
                label = "确认（类型外推）"
            else:
                label = "确认（部分类型外推）"
        else:
            label = nev
        cls = EVID_CLASS.get(label, "ev-unk")
        if cls == "ev-unk" or not a.get("value"):
            cls = "ev-unk"
        out.append(cls)
    return Counter(out)


def html_chips_by_row(html_text: str):
    """解析每行首屏 chips div 内的 chip 类多重集。"""
    rows = {}
    divs = list(ROW_DIV_RE.finditer(html_text))
    for i, m in enumerate(divs):
        end = divs[i + 1].start() if i + 1 < len(divs) else len(html_text)
        seg = html_text[m.end():end]
        cm = CHIPS_DIV_RE.search(seg)
        if not cm:
            rows[m.group(1)] = None
            continue
        tail = seg[cm.end():]
        close = tail.find("</div>")
        chips_seg = tail[:close] if close >= 0 else tail
        rows[m.group(1)] = Counter(CHIP_CLASS_RE.findall(chips_seg))
    return rows


def aggregate(stats):
    """与 card_page_batch.aggregate（card_page_batch.py:22-36）同口径的逐卡聚合。"""
    cov = {k: sum(s["coverage"][k] for s in stats) for k in ("N_all", "E", "N_num", "A", "B", "C", "original_A", "partial_A")}
    cov["evidence_cross"] = {c: {e: sum(s["coverage"]["evidence_cross"][c][e] for s in stats)
                                 for e in ("确认", "推断", "未知")} for c in ("A", "B", "C")}
    for key in ("inference_pilot_promoted", "inference_pilot_hinted", "inference_b3_promoted", "inference_b3_hinted",
                "inference_b4_promoted", "inference_b4_hinted", "inference_b5_promoted", "inference_b5_hinted",
                "inference_b6_promoted", "inference_b6_hinted", "inference_b7_promoted", "inference_b7_hinted",
                "inference_b8_promoted", "inference_b8_hinted",
                "inference_b9_promoted", "inference_b9_hinted"):
        cov[key] = sum(s["coverage"].get(key, 0) for s in stats)
    scopes = {}
    for s in stats:
        for key, value in (s["coverage"].get("confirmed_rows_by_scope") or {}).items():
            scopes[key] = scopes.get(key, 0) + value
    cov["confirmed_rows_by_scope"] = scopes
    return cov


def main():
    global MAX_DETAILS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pages", type=Path, default=DEFAULT_PAGES)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--max-details", type=int, default=MAX_DETAILS)
    args = ap.parse_args()
    root = args.root.resolve()
    pages = (root / args.pages) if not args.pages.is_absolute() else args.pages
    MAX_DETAILS = max(1, args.max_details)

    started = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # --- 当前 campaign 指针与报告 ---
    ptr_rel = load_json(pages / "_batch/campaign_latest.json")
    campaign = load_json(pages / ptr_rel["report"])
    signature = campaign["signature"]
    run_id = Path(ptr_rel["report"]).parent.name
    cohort_ptrs = {}
    cohort_reports = {}
    for ch in ("ge60", "40to59", "20to39", "remaining"):
        cp = load_json(pages / "_batch" / ch / "latest.json")
        cohort_ptrs[ch] = cp
        cohort_reports[ch] = load_json(pages / cp["report"])
    # campaign_report 本身不含 dependency_signature/manifest_sha256（见 card_page_batch.campaign）；
    # receipt 与其所在 cohort 报告（即四个 run 的共同签名组成）比对。
    dep_sigs = {r.get("dependency_signature") for r in cohort_reports.values()}
    man_shas = {r.get("manifest_sha256") for r in cohort_reports.values()}
    if len(dep_sigs) != 1 or len(man_shas) != 1:
        raise SystemExit(f"[FAIL] 四 cohort 的 dependency_signature/manifest_sha256 不唯一：{dep_sigs} / {man_shas}")
    dependency_signature, manifest_sha256 = dep_sigs.pop(), man_shas.pop()
    manifest = load_json(root / "output/character_skills/r2_preparation/cohorts/manifest.json")
    members = {int(cid): ch for ch, cids in manifest["cohorts"].items() for cid in cids}
    disk_cids = sorted(int(p.name) for p in pages.iterdir() if p.name.isdigit() and p.is_dir())

    checks = []

    # ---- 1 receipt 状态与签名 ----
    c1 = Check("receipt_signature", "receipt 状态与签名一致")
    # ---- 2 产物哈希 ----
    c2 = Check("artifact_hashes", "receipt.files 产物哈希 == 盘上")
    blocker_hits, missing = [], []
    for cid in disk_cids:
        folder = pages / str(cid)
        rj = folder / "receipt.json"
        if not rj.is_file():
            c1.add(False, f"{cid}: receipt.json 缺失")
            missing.append(cid)
            continue
        try:
            rec = load_json(rj)
        except ValueError as e:
            c1.add(False, f"{cid}: receipt.json 不可解析：{e}")
            continue
        ch = members.get(cid)
        crep = cohort_reports.get(ch, {})
        crun = (Path(cohort_ptrs[ch]["report"]).parent.name if ch else None)
        if rec.get("status") != "SUCCESS":
            c1.add(False, f"{cid}: status={rec.get('status')!r} ≠ SUCCESS")
        if (folder / "reuse_blocked.json").is_file():
            blocker_hits.append(cid)
            c1.add(False, f"{cid}: reuse_blocked.json 存在（复用被禁）")
        if rec.get("signature") != signature:
            c1.add(False, f"{cid}: receipt.signature {str(rec.get('signature'))[:12]}… ≠ campaign {signature[:12]}…")
        if rec.get("dependency_signature") != dependency_signature:
            c1.add(False, f"{cid}: dependency_signature 与 cohort 报告不一致")
        if rec.get("manifest_sha256") != manifest_sha256:
            c1.add(False, f"{cid}: manifest_sha256 与 cohort 报告不一致")
        if ch and rec.get("run_id") != crun:
            c1.add(False, f"{cid}: run_id {rec.get('run_id')} ≠ cohort {ch} latest run {crun}")
        if rec.get("status") == "SUCCESS":
            c1.add(True)
        files = rec.get("files") or {}
        if set(files) != {"card.json", "index.html"}:
            c2.add(False, f"{cid}: receipt.files 键集 {sorted(files)} ≠ [card.json, index.html]")
        else:
            for name, digest in files.items():
                p = folder / name
                if not p.is_file():
                    c2.add(False, f"{cid}: 产物 {name} 缺失")
                elif file_sha(p) != digest:
                    c2.add(False, f"{cid}: {name} sha256 与 receipt 不一致")
                else:
                    c2.add(True)
    c1.counters["reuse_blocked_cards"] = len(blocker_hits)
    c1.counters["missing_receipts"] = len(missing)
    c1.counters["cards_total"] = len(disk_cids)
    if set(disk_cids) != set(members):
        c1.add(False, f"盘上 cid 集合与 manifest 2236 不一致（盘上 {len(disk_cids)}）")
    c1.counters["cards_on_disk"] = len(disk_cids)
    checks.append(c1.done())
    checks.append(c2.done())

    # ---- 3 29 项声明数据依赖 ----
    c3 = Check("dependencies_29", "29 项声明数据依赖存在、哈希未变、dependency_signature 可复算")
    deps = data_paths(root)
    declared = [dict(path=p.relative_to(root).as_posix(), sha256=file_sha(p) if p.is_file() else "MISSING") for p in deps]
    dep_sig_now = hashlib.sha256(json.dumps(declared, sort_keys=True).encode()).hexdigest()
    run_sigs = load_json((pages / Path(ptr_rel["report"]).parent / "signatures.json"))
    c3.counters["declared_count"] = len(deps)
    for d in declared:
        if d["sha256"] == "MISSING":
            c3.add(False, f"依赖缺失：{d['path']}")
        else:
            c3.add(True)
    if len(deps) != 29:
        c3.add(False, f"声明依赖数 {len(deps)} ≠ 29")
    else:
        c3.add(True)
    if dep_sig_now != run_sigs.get("dependency_signature"):
        changed = []
        rec_now = {d["path"]: d["sha256"] for d in declared}
        for d in run_sigs.get("data_dependencies", []):
            if rec_now.get(d["path"]) != d["sha256"]:
                changed.append(d["path"])
        c3.add(False, f"dependency_signature 复算不一致；变化文件：{changed[:10]}")
    else:
        c3.add(True)
    if run_sigs.get("dependency_signature") != signature:
        # 生成签名口径（card_page_batch.run）：generation=sha256(manifest_sha+source_signature)；
        # signature=sha256(generation+dependency_signature)。复算核对 campaign 签名组成。
        generation = hashlib.sha256((run_sigs.get("manifest_sha256", "") + run_sigs.get("source_signature", "")).encode()).hexdigest()
        expected_sig = hashlib.sha256((generation + run_sigs.get("dependency_signature", "")).encode()).hexdigest()
        if expected_sig != signature:
            c3.add(False, "signatures.json 的 manifest/source/dependency 组合复算 ≠ campaign 签名")
        else:
            c3.add(True)
    checks.append(c3.done())

    # ---- 共用容器 ----
    docs = Docs(root)
    c4 = Check("rows_rowids", "行集合/row_id 唯一（card.json↔HTML↔campaign 分母）")
    c5 = Check("source_dereference", "行级/逐答案 source 解引用")
    c6 = Check("inference_source_coverage", "推断答案逐答案 source 覆盖（M2 契约）")
    c7 = Check("inference_value_equality", "推断答案原值与来源记录字段精确相等")
    c8 = Check("chip_evidence_colors", "首屏 chip 颜色档位与 evidence 一致")
    stats = []
    total_rows = 0
    row_class_totals = Counter()
    for cid in disk_cids:
        folder = pages / str(cid)
        try:
            card = load_json(folder / "card.json")
            html_text = (folder / "index.html").read_text(encoding="utf-8")
        except (OSError, ValueError) as e:
            c4.add(False, f"{cid}: card.json/index.html 读取失败：{e}")
            continue
        rows = [r for g in card["groups"] for s in g["skills"] for r in s["rows"]]
        total_rows += len(rows)
        rids = [r["row_id"] for r in rows]
        dup = [k for k, v in Counter(rids).items() if v > 1]
        if dup:
            c4.add(False, f"{cid}: row_id 重复 {dup[:5]}")
        else:
            c4.add(True)
        if any(not r["row_id"].startswith(f"{cid}-") for r in rows):
            c4.add(False, f"{cid}: 存在 row_id 不以本卡 cid 开头")
        rcc = Counter(r["row_class"] for r in rows)
        cov = card["coverage"]
        if (rcc.get("A", 0), rcc.get("B", 0), rcc.get("C", 0)) != (cov["A"], cov["B"], cov["C"]) or cov["N_all"] != len(rows):
            c4.add(False, f"{cid}: row_class 计数 {dict(rcc)} 与 coverage A/B/C="
                          f"{(cov['A'], cov['B'], cov['C'])}/N_all={cov['N_all']} 不一致")
        else:
            c4.add(True)
        row_class_totals.update(rcc)
        # card.json 行集合 == HTML 行锚点集合
        html_rows = html_chips_by_row(html_text)
        if None in html_rows.values():
            bad = [k for k, v in html_rows.items() if v is None]
            c8.add(False, f"{cid}: HTML 行缺 chips 容器：{bad[:5]}")
        if set(html_rows) != set(rids):
            only_html = sorted(set(html_rows) - set(rids))[:5]
            only_card = sorted(set(rids) - set(html_rows))[:5]
            c4.add(False, f"{cid}: HTML data-row-id 与 card.json 行集合不一致（仅HTML {only_html}；仅card {only_card}）")
        else:
            c4.add(True)
        # 逐行：source 解引用、推断答案 source/值、chip 颜色
        for r in rows:
            if isinstance(r.get("source"), dict) and r["source"]:
                st, d = deref_one(r["source"], docs)
                if st == "OK":
                    c5.add(True)
                elif st == "UNRESOLVED_EXPLICIT":
                    c5.add(True, d, unresolved_explicit=1)
                elif st == "NOTED":
                    c5.note(f"{cid}/{r['row_id']} 行source：{d}")
                else:
                    c5.add(False, f"{cid}/{r['row_id']} 行source：{d}")
            answers = r.get("answers", [])
            for a in answers:
                src = a.get("source")
                if isinstance(src, list):
                    for it in src:
                        if isinstance(it, dict) and it:
                            st, d = deref_one(it, docs)
                            if st == "OK":
                                c5.add(True)
                            elif st == "UNRESOLVED_EXPLICIT":
                                c5.add(True, d, unresolved_explicit=1)
                            elif st == "NOTED":
                                c5.note(f"{cid}/{r['row_id']} 基线ref：{d}")
                            else:
                                c5.add(False, f"{cid}/{r['row_id']} 基线ref：{d}")
                elif isinstance(src, dict) and src:
                    st, d = deref_one(src, docs)
                    if st == "OK":
                        c5.add(True)
                    elif st == "UNRESOLVED_EXPLICIT":
                        c5.add(True, d, unresolved_explicit=1)
                    elif st == "NOTED":
                        c5.note(f"{cid}/{r['row_id']} 答案source：{d}")
                    else:
                        c5.add(False, f"{cid}/{r['row_id']} 答案source：{d}")
                elif a.get("numeric_evidence") == "推断":
                    c6.add(False, f"{cid}/{r['row_id']}（numeric_source={a.get('numeric_source')!r}）推断答案无 source",
                           inference_answers_without_source=1)
                else:
                    c6.add(True, None, non_inference_without_source=1)
                if a.get("numeric_evidence") == "推断" and isinstance(src, dict) and src:
                    rec, err = resolve_source(src, docs)
                    if err is not None:
                        c7.add(False, f"{cid}/{r['row_id']}：来源不可解：{err}")
                    else:
                        try:
                            val = value_at(rec, a.get("field_path"))
                        except (ValueError, KeyError, IndexError, TypeError) as e:
                            c7.add(False, f"{cid}/{r['row_id']}：field_path {a.get('field_path')!r} 落空：{e}")
                        else:
                            if numbers_equal(val, a.get("raw_value")):
                                c7.add(True)
                            else:
                                c7.add(False, f"{cid}/{r['row_id']}：原值 {a.get('raw_value')!r} ≠ 记录值 {val!r}"
                                              f"（{src.get('record_key')}#{a.get('field_path')}）")
            # chip 颜色：期望多重集 vs HTML 实际
            if html_rows.get(r["row_id"]) is not None:
                actual = html_rows[r["row_id"]]
                if not answers:
                    expect = Counter({"ev-unk": 1})
                else:
                    expect = expected_chip_classes(answers, r)
                if actual != expect:
                    c8.add(False, f"{cid}/{r['row_id']}：chip 类实际 {dict(actual)} ≠ 期望 {dict(expect)}")
                else:
                    c8.add(True)
                if expect.get("ev-inf", 0) > 0 and actual.get("ev-conf", 0) > expect.get("ev-conf", 0):
                    c8.add(False, f"{cid}/{r['row_id']}：出现推断→绿事件（期望推断 chip 之外的 ev-conf）",
                           infer_rendered_green=actual.get("ev-conf", 0) - expect.get("ev-conf", 0))
                if expect.get("ev-conf", 0) + expect.get("ev-conf-ext", 0) > 0 and \
                        actual.get("ev-inf", 0) > expect.get("ev-inf", 0):
                    c8.add(False, f"{cid}/{r['row_id']}：出现确认→橙事件（期望确认 chip 之外的 ev-inf）",
                           confirm_rendered_orange=actual.get("ev-inf", 0) - expect.get("ev-inf", 0))
        stats.append(dict(cid=cid, coverage=cov, summary=card["summary"]))
    c4.counters["rows_total"] = total_rows
    c4.counters["cards"] = len(disk_cids)
    c4.counters["row_class_totals"] = dict(row_class_totals)
    c4.add(False, f"总行数 {total_rows} ≠ campaign N_all {campaign['summary']['N_all']}") if total_rows != campaign["summary"]["N_all"] else c4.add(True)
    c6.counters["note"] = "推断答案无 source 属阶段一已就绪、统一重建未执行的已知缺口（M2 契约）"
    checks.append(c4.done())
    for c in (c5, c6, c7, c8):
        checks.append(c.done())

    # ---- 9 四联计数与 campaign 对账 ----
    c9 = Check("campaign_reconciliation", "逐卡 coverage 聚合与 campaign coverage/summary 对账")
    cov = aggregate(stats)
    ccov = campaign["coverage"]
    diffs = {}
    for k, v in cov.items():
        if ccov.get(k) != v:
            diffs[k] = (ccov.get(k), v)
    if diffs:
        c9.add(False, f"coverage 聚合与 campaign_report 不一致（campaign, 重算）：{json.dumps(diffs, ensure_ascii=False)[:600]}")
    else:
        c9.add(True)
    recomputed = policy_metrics(cov)
    sdiffs = {}
    for k in ("A", "whole_row_confirmed", "original_A", "C", "A_whole_row_unknown", "whole_row_inferred"):
        got, exp = recomputed[k]["count"], campaign["summary"][k]["count"]
        gden, eden = recomputed[k]["denominator"], campaign["summary"][k]["denominator"]
        if (got, gden) != (exp, eden):
            sdiffs[k] = (exp, eden, got, gden)
    sc = campaign["summary"]["whole_row_confirmed_scopes"]
    rc = recomputed["whole_row_confirmed_scopes"]
    if (sc.get("record"), sc.get("by_type_extrapolated"), sc.get("mixed")) != (rc.get("record"), rc.get("by_type_extrapolated"), rc.get("mixed")):
        sdiffs["whole_row_confirmed_scopes"] = (sc, rc)
    if sdiffs:
        c9.add(False, f"summary 计数与 policy.metrics 重算不一致（campaign, 重算）：{json.dumps(sdiffs, ensure_ascii=False)[:600]}")
    else:
        c9.add(True)
    # 逐卡 summary == policy.metrics(逐卡 coverage)
    card_sum_bad = 0
    for stt in stats:
        m = policy_metrics(stt["coverage"])
        for k in ("A", "whole_row_confirmed", "original_A", "C", "whole_row_inferred"):
            if stt["summary"][k]["count"] != m[k]["count"] or stt["summary"][k]["denominator"] != m[k]["denominator"]:
                card_sum_bad += 1
                c9.add(False, f"{stt['cid']}: summary.{k} 与 policy.metrics(coverage) 不一致") if card_sum_bad <= MAX_DETAILS else None
                break
        else:
            c9.add(True)
    c9.counters["cards_with_summary_mismatch"] = card_sum_bad
    c9.counters["inference_counters"] = {k: cov[k] for k in cov if k.startswith("inference_")}
    checks.append(c9.done())

    # ---- 10 入口页指标一致 ----
    c10 = Check("entry_pages", "入口页指标与 run 指针一致（M1）")
    entry = entry_pages_consistency(pages, campaign["summary"], ptr_rel["report"])
    c10.add(entry["status"] == "CURRENT", json.dumps(entry["detail"], ensure_ascii=False)[:600])
    all_text = (pages / "all_cards.html").read_text(encoding="utf-8") if (pages / "all_cards.html").is_file() else ""
    hrefs = set(int(x) for x in re.findall(r'href="(\d+)/index\.html"', all_text))
    if hrefs != set(members):
        c10.add(False, f"all_cards.html 跳转集合与 2236 manifest 不一致（多 {len(hrefs - set(members))}、少 {len(set(members) - hrefs)}）")
    else:
        c10.add(True)
    c10.counters["entry_status"] = entry["status"]
    checks.append(c10.done())

    # ---- 汇总 ----
    verdict = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    result = dict(tool="scripts/character_skills/card_page_verify_full.py",
                  generated_at=started,
                  root=str(root),
                  scope="output/character_skills/pages 当前交付面（2236 卡 + 入口两页）；_batch 只读指针/报告",
                  campaign=dict(pointer=ptr_rel["report"], run_id=run_id, signature=signature,
                                cohort_snapshots=[dict(cohort=s["cohort"], status=s["status"],
                                                       report=s["report"]) for s in campaign["cohort_snapshots"]]),
                  declared_dependencies=dict(count=len(deps), dependency_signature_now=dep_sig_now,
                                             dependency_signature_recorded=run_sigs.get("dependency_signature")),
                  checks=checks,
                  verdict=verdict,
                  notes=[
                      "不检查：source 内原始 .data5 字节范围/raw_record_sha256（原始字节层，不在本交付面）",
                      "不检查：details 折叠层文本逐字比对、浏览器渲染与交互",
                      "检查 6 在统一重建（阶段一代码已就绪）前会以当前无 source 推断答案数 FAIL，属如实反映",
                  ])
    out = (root / args.out) if not args.out.is_absolute() else args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[verify_full] campaign {run_id} 签名 {signature[:12]}…")
    for c in checks:
        print(f"  {c['status']:4} {c['check']}  ok={c['ok']} failed={c['failed']} "
              + ("counters=" + json.dumps(c["counters"], ensure_ascii=False) if c["counters"] else ""))
    print(f"[verify_full] 判定：{verdict}；报告：{out}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("[verify_full] 未执行完成（异常中止），不产出 PASS 判定", file=sys.stderr)
        sys.exit(2)
