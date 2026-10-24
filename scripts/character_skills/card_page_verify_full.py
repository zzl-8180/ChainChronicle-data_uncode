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
  6 inference_source_coverage  推断答案逐答案 source 覆盖（M2 契约；DS-GR-10 修复
                        20261023：统计双侧——推断答案带 source 计 ok、不带计 fail，
                        非"ok=0/failed=0"的 no-op）
  7 inference_value_equality   推断答案原值与来源记录字段值精确相等
  8 chip_evidence_colors       首屏 chip 颜色档位与 evidence 一致（逐行 chip 类多重集
                        == 按答案证据推导；并单列「推断→绿」「确认→橙」事件，应为 0）
  9 campaign_reconciliation    四联计数与 campaign 对账（逐卡 coverage 重新聚合 ==
                        campaign_report coverage/summary；逐卡 summary == policy.metrics）
 10 entry_pages         入口页指标与 run 指针一致（复用 card_page_index.entry_pages_consistency）
 11 ledger_row_coverage          每行账本入口存在（pages 行集合 ↔ ledger 描述入口，双向；P3）
 12 ledger_complete_no_unresolved 账本「完整」描述未解决项=0 且无拆分待核查标志（P3）
 13 ledger_answer_refs_resolve   账本答案引用可解析到 pages 现有 answers（P3）
 14 ledger_backlog_setdiff       正式待办集合差为空＋带 hint 行在账本有待办踪迹（P3）
 15 page_ledger_unresolved_sync  页面未解决区/拆分待核查呈现与账本行状态逐行一致
                        （DS-GR-01 修复；DS-GR-R4 扩展 20261023：内容级——类型/方向/
                        ダメージ对象标记多重集＋has_answer ダメージ效果的对象一致
                        （答案对象 vs 主张子句对象，独立重derive；R1 口径））
 （11–15 由目标整改 §三.4/A2/A3/A4/DS-GR-01/R4 要求新增；对账对象 --ledger 须先按当前
   pages 重建）

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
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card_page_cohorts import sha as file_sha
from card_page_dependencies import data_paths
from card_page_policy import metrics as policy_metrics
from card_page_index import entry_pages_consistency, metric_values_from_summary

DEFAULT_PAGES = Path("output/character_skills/pages")
DEFAULT_OUT = Path("work/character_skills_phase2_20261021/verify_full_latest.json")
DEFAULT_LEDGER = Path("output/character_skills/effect_ledger")
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


# 行首屏未解决区（card_page_render_v2.unresolved_effects_html）：
# <div class="unresolved-effects" data-unresolved="N"><span class="unres-item">…</span>…
# （无未解决项时该 div 不渲染）
UNRES_DIV_RE = re.compile(
    r'<div class="unresolved-effects" data-unresolved="(\d+)">(.*?)</div>', re.S)
UNRES_ITEM_RE = re.compile(r'<span class="unres-item">([^<]*)</span>')
# 拆分待核查短句映射——与 card_page_render_v2._UNRES_FLAG_SHORT 同步（若改动须同改，
# 否则第 15 项内容级核对会误报）。
UNRES_FLAG_SHORT = {
    'S1_zero_claims': '词表未识别出效果主张（不能排除词表外效果）',
    'S2_unconfirmed_numbers': '原文数字语义未确认（如次数/阈值；含主张子句内数字——R2 整改）',
    'S3_uncovered_clauses': '存在未被效果主张覆盖的子句（定性机制待核查）',
    'S3b_residual_mechanisms': '正文含词表外机制词且无答案覆盖（状态异常等待核查——R2 整改）',
    'S4_unconsumed_typed_answers': '存在未对应句面主张的答案（归属缺口）',
    'S5_hp_branch_coverage': 'HP 档位分支覆盖不完整（R1 整改）',
    'S5_hp_variation_unbound': '「随HP变化」句的增益答案缺 HP 档位绑定（R1 整改）',
    'S6_unresolved_conditions': '概率类条件无载体映射与解析状态（R2 整改）',
    'S7_same_cond_alt_t13': '同 HP 条件组内其余 pattern→t13 值不同、选取维度未解析（R1-High 复审整改）',
}
# 对象维度标记（R4 内容级；与账本 _clause_object/_answer_object 同语义的独立复刻——
# 自伤/敌方分列；检查器不 import 账本实现，保持校验独立性）。
R1_SELF_MARKS_ANSWER = ('自身受到伤害', '自分')
R1_ENEMY_MARKS_ANSWER = ('对敌', '敵')
R1_SELF_MARKS_CLAUSE = ('自身', '自分')
R1_ENEMY_MARKS_CLAUSE = ('敵',)
R1_DAMAGE_TYPES = frozenset({'ダメージ（词表外）', '受けるダメージ（词表外）',
                             '与えるダメージ（词表外）'})
CLAUSE_SPLIT_RE = re.compile(r'[^。、！？\n]+')


def _r1_clause_object(clause: str):
    """对象分类（账本 _clause_object 同语义的独立复刻）：与え→enemy、受け/負う→self、
    DS-GR-R1b（20261023）：自身に/自分に…与える＝自我指向赋予→self（に格＝赋予对象；
    「敵に」并存时保守维持 enemy 原口径）、动词缺失退回词面（自身/自分 ↔ 敵；
    両存/均缺＝None）。"""
    if "与え" in clause:
        self_dat = "自身に" in clause or "自分に" in clause
        if self_dat and "敵に" not in clause:
            return "self"
        return "enemy"
    if "受け" in clause or "負う" in clause:
        return "self"
    has_self = any(m in clause for m in R1_SELF_MARKS_CLAUSE)
    has_enemy = any(m in clause for m in R1_ENEMY_MARKS_CLAUSE)
    if has_self and not has_enemy:
        return "self"
    if has_enemy and not has_self:
        return "enemy"
    return None


def _r1_answer_object(quantity_kind, value):
    text = (str(quantity_kind or '') + str(value or ''))
    if any(m in text for m in R1_SELF_MARKS_ANSWER):
        return 'self'
    if any(m in text for m in R1_ENEMY_MARKS_ANSWER):
        return 'enemy'
    return None


def html_unresolved_by_row(html_text: str):
    """解析每行首屏未解决区：{row_id: (data-unresolved 计数, [item 短句文本])}
    （无未解决区的行记 (0, [])）。R4 内容级核对用 item 原文。"""
    rows = {}
    divs = list(ROW_DIV_RE.finditer(html_text))
    for i, m in enumerate(divs):
        end = divs[i + 1].start() if i + 1 < len(divs) else len(html_text)
        seg = html_text[m.end():end]
        um = UNRES_DIV_RE.search(seg)
        if um:
            rows[m.group(1)] = (int(um.group(1)), UNRES_ITEM_RE.findall(um.group(0)))
        else:
            rows[m.group(1)] = (0, [])
    return rows


def r1_parent_chain_assert(row, branches):
    """R1-Medium 复审整改（20261023，verify 第 16 项扩展）：HP 档位分支行的父链
    provenance 与 condition_label 一致性。

    依据：复审 recheck_rectification_20261023_deepseek R1-20332-PARENT-PROVENANCE——
    同值 t13 跨档引用的行（20332 两行），numeric_source 父链与注记 reference_field/
    「本档位 pattern 引用」段固定首档 patternid0/pattern0，与该答案 condition_label
    对应的档位 pattern 矛盾（每行 16 答案中 12 个）。原第 16 项只核对 t13 槽值/来源/
    标签，未覆盖父链文本。断言（逐答案，按标签分组——同档多 pattern 时任一即可）：
      ①numeric_source 须含「<patternN>→bosspattern|<该档 pattern id>|」（逐档父链）；
      ②注记 reference_field 短语（denju 形「bosspattern[pid].slotN」／charainfo 形
        「经 pattern 记录（bosspattern|pid|）」）中的 pattern id 须属该标签的档位集合；
      ③注记「本档位 pattern 引用：」段须列出该标签档位集合的全部 pattern 记录键。
    branches＝第 16 项的 (fld, pid, blay, (hpstart, hpend), t13s) 元组列。
    返回违例文本列表（空＝通过）。"""
    import re as _re
    by_lab = {}
    for f, pid, blay, cond, t13s in branches:
        lab = "HP %s–%s%%" % (cond[0] if cond[0] is not None else "?",
                              cond[1] if cond[1] is not None else "?")
        by_lab.setdefault(lab, []).append((f, pid, blay))
    bad = []
    for a in row.get("answers") or []:
        lab = a.get("condition_label")
        if lab not in by_lab:
            continue
        cands = by_lab[lab]
        pids = {str(p) for _f, p, _l in cands}
        ns = str(a.get("numeric_source") or "")
        if not any(f"{f}→bosspattern|{pid}|" in ns for f, pid, _l in cands):
            bad.append(f"{lab}: numeric_source 父链未引用本档 pattern "
                       f"（须含 {' 或 '.join(f'{f}→bosspattern|{p}|' for f, p, _ in cands)}；"
                       f"实际 {ns[:160]}）")
        note = str(a.get("note") or "")
        m_ref = _re.search(r"「bosspattern\[(\d+)\]\.", note)
        if m_ref and m_ref.group(1) not in pids:
            bad.append(f"{lab}: 注记 reference_field 短语固定 bosspattern[{m_ref.group(1)}]"
                       f"，不属本档 {sorted(pids)}")
        m_pat = _re.search(r"经 pattern 记录（bosspattern\|(\d+)", note)
        if m_pat and m_pat.group(1) not in pids:
            bad.append(f"{lab}: 注记 pattern 记录短语固定 bosspattern|{m_pat.group(1)}|"
                       f"，不属本档 {sorted(pids)}")
        seg = note.split("本档位 pattern 引用：", 1)
        seg = seg[1].split("；")[0] if len(seg) == 2 else ""
        miss = [f"＝bosspattern|{p}|" for p in sorted(pids)
                if f"＝bosspattern|{p}|" not in seg]
        if seg and miss:
            bad.append(f"{lab}: 注记「本档位 pattern 引用」段缺 {miss}")
    return bad


def aggregate(stats):
    """与 card_page_batch.aggregate（card_page_batch.py:22-36）同口径的逐卡聚合。"""
    cov = {k: sum(s["coverage"][k] for s in stats) for k in ("N_all", "E", "N_num", "A", "B", "C", "original_A", "partial_A")}
    cov["evidence_cross"] = {c: {e: sum(s["coverage"]["evidence_cross"][c][e] for s in stats)
                                 for e in ("确认", "推断", "未知")} for c in ("A", "B", "C")}
    for key in ("inference_pilot_promoted", "inference_pilot_hinted", "inference_b3_promoted", "inference_b3_hinted",
                "inference_b4_promoted", "inference_b4_hinted", "inference_b5_promoted", "inference_b5_hinted",
                "inference_b6_promoted", "inference_b6_hinted", "inference_b7_promoted", "inference_b7_hinted",
                "inference_b8_promoted", "inference_b8_hinted",
                "inference_b9_promoted", "inference_b9_hinted",
                "inference_b10_promoted", "inference_b10_hinted",
                "inference_b11_promoted", "inference_b11_hinted",
                "inference_b12_promoted", "inference_b13_promoted", "inference_b13_hinted",
                "inference_b14_promoted", "inference_b15_promoted", "inference_b15_hinted",
                "inference_b17_promoted", "inference_b17_hinted"):
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
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER,
                    help="效果账本目录（P3 新增检查 11–14 的对账对象；须先由 "
                         "scripts/character_skills/effect_ledger.py 按当前 pages 重建）")
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
    html_unres = {}   # 行 row_id → 首屏未解决区 data-unresolved 计数（检查 15 用）
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
        html_unres.update(html_unresolved_by_row(html_text))
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
                # 检查 6（DS-GR-10 修复 20261023）：M2 契约双侧统计——推断答案必须带
                # source（带=ok、不带=fail，非 no-op）；非推断答案带不带 source 均登记。
                if a.get("numeric_evidence") == "推断":
                    if (isinstance(src, dict) and src) or (isinstance(src, list) and src):
                        c6.add(True, None, inference_with_source=1)
                    else:
                        c6.add(False, f"{cid}/{r['row_id']}（numeric_source={a.get('numeric_source')!r}）推断答案无 source",
                               inference_answers_without_source=1)
                elif (isinstance(src, dict) and src) or (isinstance(src, list) and src):
                    c6.add(True, None, non_inference_with_source=1)
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
    c6.counters["note"] = ("检查 6 双侧统计（DS-GR-10 修复）：inference_with_source=带 source 的"
                           "推断答案（M2 契约覆盖数）；inference_answers_without_source 应为 0")
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

    # ---- 11–14 效果账本一致性（P3，20261023 目标整改 §三.4/A2/A3/A4；新增检查，
    #      不删既有 10 项、不扩大豁免、不降低证据规则。对账对象＝--ledger 目录下的
    #      ledger.jsonl/backlog.json，须先按当前 pages 重建；本节独立重读两侧数据，
    #      不复用 effect_ledger 生成路径的中间状态。） ----
    ledger_dir = (root / args.ledger) if not args.ledger.is_absolute() else args.ledger
    ledger_path = ledger_dir / "ledger.jsonl"
    backlog_path = ledger_dir / "backlog.json"
    c11 = Check("ledger_row_coverage", "每行账本入口存在（pages 行集合 ↔ ledger 描述入口，双向）")
    c12 = Check("ledger_complete_no_unresolved", "账本「完整」描述未解决项=0 且无拆分待核查标志")
    c13 = Check("ledger_answer_refs_resolve", "账本答案引用可解析到 pages 现有 answers")
    c14 = Check("ledger_backlog_setdiff", "正式待办集合差为空（未解决∪拆分待核查 ↔ backlog，双向）")
    c15 = Check("page_ledger_unresolved_sync",
                "页面未解决区与账本逐行一致（计数＋内容级：类型/方向/对象；"
                "DS-GR-01＋DS-GR-R4 修复；对象错配自伤/敌方分列）")
    if not ledger_path.is_file() or not backlog_path.is_file():
        for c in (c11, c12, c13, c14, c15):
            c.add(False, f"效果账本文件缺失：{ledger_path} / {backlog_path}（请先重建账本）")
            checks.append(c.done())
    else:
        ledger_desc, ledger_eff = {}, []
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("record_type") == "description":
                ledger_desc[rec["row_id"]] = rec
            elif rec.get("record_type") == "effect":
                ledger_eff.append(rec)
        pages_rows = {}
        pages_answers = {}
        for cid in disk_cids:
            card = load_json(pages / str(cid) / "card.json")
            for g in card["groups"]:
                for s in g["skills"]:
                    for r in s["rows"]:
                        pages_rows[r["row_id"]] = r
                        pages_answers[r["row_id"]] = [
                            (a.get("field_path"), a.get("raw_value")) for a in r.get("answers", [])]
        # c11：行集合双向一致
        only_pages = sorted(set(pages_rows) - set(ledger_desc))
        only_ledger = sorted(set(ledger_desc) - set(pages_rows))
        if only_pages:
            c11.add(False, f"pages 行缺账本入口 {len(only_pages)} 条（例：{only_pages[:5]}）")
        if only_ledger:
            c11.add(False, f"账本入口无对应 pages 行 {len(only_ledger)} 条（例：{only_ledger[:5]}）")
        if not only_pages and not only_ledger:
            c11.add(True)
        c11.counters.update(pages_rows=len(pages_rows), ledger_desc=len(ledger_desc),
                            only_pages=len(only_pages), only_ledger=len(only_ledger))
        # c12：完整描述未解决项=0（独立从账本条目重算）
        bad_complete, bad_split = [], 0
        for rid, d in ledger_desc.items():
            if d.get("ledger_row_status") == "完整":
                if d.get("effect_status_counts", {}).get("unresolved", 0) > 0 or d.get("split_flags"):
                    bad_complete.append(rid)
            if d.get("ledger_row_status") == "拆分待核查" and not d.get("split_flags"):
                bad_split += 1
        if bad_complete:
            c12.add(False, f"账本「完整」描述含未解决项/拆分标志 {len(bad_complete)} 条（例：{bad_complete[:5]}）")
        else:
            c12.add(True)
        if bad_split:
            c12.add(False, f"「拆分待核查」行无 split_flags {bad_split} 条")
        else:
            c12.add(True)
        c12.counters.update(complete_rows=sum(1 for d in ledger_desc.values()
                                              if d.get("ledger_row_status") == "完整"),
                            complete_with_unresolved=len(bad_complete))
        # c13：答案引用可解析（row_id+field_path+raw_value+answer_index，页面侧独立重读）
        bad_refs = 0
        resolved = 0
        for e in ledger_eff:
            for ref in e.get("answer_refs") or []:
                k = ref.get("resolvable_key") or {}
                triples = pages_answers.get(k.get("row_id"))
                idx = k.get("answer_index")
                if triples is None or not isinstance(idx, int) or not (0 <= idx < len(triples)):
                    bad_refs += 1
                    if bad_refs <= MAX_DETAILS:
                        c13.add(False, f"账本效果 {e['effect_id']} 答案引用不可解析（行缺/index 越界）")
                    continue
                fp, rv = triples[idx]
                if fp == k.get("field_path") and rv == k.get("raw_value"):
                    resolved += 1
                else:
                    bad_refs += 1
                    if bad_refs <= MAX_DETAILS:
                        c13.add(False, f"账本效果 {e['effect_id']} 答案引用不一致：账本 "
                                      f"{k.get('field_path')!r}/{k.get('raw_value')!r} ≠ 页面 {fp!r}/{rv!r}")
        if bad_refs == 0:
            c13.add(True)
        c13.counters.update(resolved=resolved, failures=bad_refs, effects=len(ledger_eff))
        # c14：backlog 集合差双向为空（账本独立重算 vs backlog.json）
        unresolved_ids = {e["effect_id"] for e in ledger_eff if e.get("status") == "unresolved"}
        split_ids = {rid for rid, d in ledger_desc.items()
                     if d.get("ledger_row_status") == "拆分待核查"}
        backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
        bl_eff = {b["backlog_id"] for b in backlog if b.get("kind") == "effect"}
        bl_split = {b["row_id"] for b in backlog if b.get("kind") == "description_split_check"}
        missing = (unresolved_ids - bl_eff) | (split_ids - bl_split)
        extra = (bl_eff - unresolved_ids) | (bl_split - split_ids)
        if missing or extra:
            c14.add(False, f"待办集合差非空：缺 {len(missing)}（例 {sorted(missing)[:3]}）、"
                           f"多 {len(extra)}（例 {sorted(extra)[:3]}）")
        else:
            c14.add(True)
        # hint 变化不丢待办（A9 口径的机器侧）：带 hint 的行必须有未解决效果或拆分标志
        lost = [rid for rid, r in pages_rows.items()
                if any(k.startswith("inference_") and k.endswith("_hint") for k in r)
                and rid in ledger_desc
                and ledger_desc[rid].get("effect_status_counts", {}).get("unresolved", 0) == 0
                and ledger_desc[rid].get("ledger_row_status") != "拆分待核查"
                and not ledger_desc[rid].get("effect_ids")]
        if lost:
            c14.add(False, f"带 hint 键但账本无任何待办踪迹 {len(lost)} 行（例：{lost[:5]}）")
        else:
            c14.add(True)
        c14.counters.update(backlog_items=len(backlog), unresolved=len(unresolved_ids),
                            split_check=len(split_ids), missing=len(missing), extra=len(extra))
        # c15 v2（DS-GR-R4 扩展，20261023 复验）：内容级核对——不再只比 data-unresolved 计数：
        # ① 计数：页面未解决区计数 == 账本 未解决效果数＋拆分标志数（原口径）；
        # ② 内容：页面未解 item 多重集（类型＋方向＋ダメージ 类对象标记）== 账本未解决效果
        #    （effect_type＋direction＋对象）——对象由检查器从页面行日文子句独立重derive
        #    （NFKC＋账本同法子句切分＋对象词面；不 import 账本实现，保持校验独立），
        #    自伤/敌方分列（DS-GR-R1：修复前 9 行在此 FAIL，修复后 0）；
        # ③ 对象一致（R1 捕获口径）：has_answer 的ダメージ 类效果，其匹配答案的对象
        #    （页面答案 quantity_kind/value 独立分类）须与主张子句对象一致——对象不可判
        #    不设限；修复前 9 行「自身受到伤害」答案错配敌方主张在此 FAIL。
        ledger_eff_by_row = {}
        for e in ledger_eff:
            ledger_eff_by_row.setdefault(e["description_ref"], []).append(e)
        pages_answer_full = {
            rid: [(a.get("quantity_kind"), a.get("value")) for a in r.get("answers", [])]
            for rid, r in pages_rows.items()}
        bad_sync, r1_violations = [], []
        page_shows = ledger_todo = 0
        for rid, d in ledger_desc.items():
            actual = html_unres.get(rid)
            cnt, items = actual if actual is not None else (None, [])
            row = pages_rows.get(rid)
            clauses = []
            if row is not None:
                t_n = unicodedata.normalize("NFKC", row.get("japanese") or "")
                clauses = CLAUSE_SPLIT_RE.findall(t_n)

            def _clause_obj(e):
                ci = e.get("clause_index")
                if not isinstance(ci, int) or not (0 <= ci < len(clauses)):
                    return None
                return _r1_clause_object(clauses[ci])

            expected_items = []
            for e in ledger_eff_by_row.get(rid, []):
                if e["status"] != "unresolved":
                    continue
                dirword = {"up": "上升", "down": "下降"}.get(e.get("direction"), "")
                objmark = ""
                if e["effect_type"] in R1_DAMAGE_TYPES:
                    cobj = _clause_obj(e)
                    if cobj:
                        objmark = "（自身）" if cobj == "self" else "（敵）"
                expected_items.append("未解：" + e["effect_type"] + dirword + objmark)
            for f in d.get("split_flags") or []:
                expected_items.append("拆分待核查：" + UNRES_FLAG_SHORT.get(f["code"], f["code"]))
            if actual is None:
                bad_sync.append(f"{rid}: 行未出现在页面 HTML")
                continue
            # 归一：仅对「未解：」项剥离末尾一段成对（…）＝render 的候选段（候选段可含
            # 嵌套括号，如「（候选 bossskill type13 槽（并集归属），核查中）」，须按
            # 平衡括号剥离；「拆分待核查：」短句文本本身含（…）注记，不剥离）。
            norm_items = []
            for it in items:
                if it.startswith("未解：") and it.endswith("）"):
                    depth = 0
                    for pos in range(len(it) - 1, -1, -1):
                        ch = it[pos]
                        if ch == "）":
                            depth += 1
                        elif ch == "（":
                            depth -= 1
                            if depth == 0:
                                it = it[:pos]
                                break
                norm_items.append(it)
            if cnt != len(expected_items):
                bad_sync.append(f"{rid}: 页面未解决区 {cnt} ≠ 账本 {len(expected_items)}")
            if Counter(norm_items) != Counter(expected_items):
                only_pg = sorted(set(norm_items) - set(expected_items))[:3]
                only_ld = sorted(set(expected_items) - set(norm_items))[:3]
                bad_sync.append(f"{rid}: 未解决区内容不一致（仅页面 {only_pg}／仅账本 {only_ld}）")
            if cnt > 0:
                page_shows += 1
            if d.get("ledger_row_status") != "完整":
                ledger_todo += 1
        # ③ 对象一致（R1 捕获口径；账本 effect.object 未设的旧账本同样可查——对象从子句重derive）
        for e in ledger_eff:
            if e.get("effect_type") in R1_DAMAGE_TYPES and e.get("status") == "has_answer":
                row = pages_rows.get(e["description_ref"])
                if row is None:
                    continue
                clauses = CLAUSE_SPLIT_RE.findall(
                    unicodedata.normalize("NFKC", row.get("japanese") or ""))
                ci = e.get("clause_index")
                cobj = (_r1_clause_object(clauses[ci])
                        if isinstance(ci, int) and 0 <= ci < len(clauses) else None)
                if cobj is None:
                    continue
                for ref in e.get("answer_refs") or []:
                    k = ref.get("resolvable_key") or {}
                    triples = pages_answer_full.get(k.get("row_id")) or []
                    idx = k.get("answer_index")
                    if not isinstance(idx, int) or not (0 <= idx < len(triples)):
                        continue   # 引用可解析性归第 13 项
                    aobj = _r1_answer_object(*triples[idx])
                    if aobj is not None and aobj != cobj:
                        r1_violations.append(dict(
                            effect_id=e["effect_id"], claim_object=cobj, answer_object=aobj,
                            answer_value=str(triples[idx][1])[:60]))
        extra_rows = [rid for rid, (c, _it) in html_unres.items()
                      if rid not in ledger_desc and c]
        if extra_rows:
            bad_sync.append(f"页面显示未解决但账本无入口 {len(extra_rows)} 行（例：{extra_rows[:5]}）")
        if bad_sync:
            c15.add(False, f"页面未解决区与账本不一致 {len(bad_sync)} 条（例：{bad_sync[:5]}）")
        else:
            c15.add(True)
        if r1_violations:
            c15.add(False, f"ダメージ 效果对象错配（自伤/敌方分列，DS-GR-R1 口径）"
                           f"{len(r1_violations)} 条（例：{r1_violations[:3]}）")
        else:
            c15.add(True)
        c15.counters.update(rows=len(ledger_desc), page_shows_unresolved=page_shows,
                            ledger_noncomplete=ledger_todo, mismatches=len(bad_sync),
                            content_rows_checked=len(ledger_desc),
                            r1_object_violations=len(r1_violations),
                            html_rows_parsed=len(html_unres))
        # ---- 16 R1 定向：HP 档位分支行逐档绑定原始 t13 值（独立重读 bossinfo/charainfo/
        #      denju 原始记录，不 import 推断/账本实现——_r1_clause_object 独立复刻先例） ----
        c16 = Check("r1_hp_branch_binding",
                    "R1 定向：hp_branch_conditions_expected 行的每档位值行与原始 bossinfo "
                    "t13 槽值逐项相等（来源/标签/条件绑定）")
        n16 = 0
        _BOSS_DOC = {}
        for _lay, _p in (("APK", "output/base_master/_mdBossInfo.json"),
                         ("CACHE", "output/cache_full_20261015_v3/decoded/bossinfo.data5.json.raw")):
            _doc = load_json(root / _p)
            _bb = _doc["bossinfo"] if "bossinfo" in _doc else _doc
            _BOSS_DOC[_lay] = ({r["patternid"]: r for r in _bb["bosspattern"]},
                               {r["skillid"]: r for r in _bb["bossskill"]})
        _CHA_DOC = {"APK": load_json(root / "output/base_master/_mdCharacter.json")["charainfo"],
                    "CACHE": load_json(root / "output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw")["charainfo"]}
        _DEN_DOC = {"CACHE": load_json(root / "output/cache_full_20261015_v3/decoded/denju.data5.json.raw")["denju"]}
        for rid, row in pages_rows.items():
            expected_labels = row.get("hp_branch_conditions_expected") or []
            if not expected_labels:
                continue
            n16 += 1
            src = row.get("source") or {}
            layer = src.get("layer")
            cid16 = row.get("cid")
            # 命名空间记录与 pattern 引用（charainfo=patternN；denju=patternidN；分源不跨层）
            if "denju" in rid.split("-", 2)[1:2] + [""] or (src.get("source_key") or "").endswith("denju.data5.json.raw"):
                rec0 = next((r for r in _DEN_DOC["CACHE"] if r["denju_id"] == cid16), None)
                flds = [f"patternid{i}" for i in range(9)]
            else:
                rec0 = next((r for r in _CHA_DOC.get(layer, []) if r["cid"] == cid16), None)
                flds = [f"pattern{i}" for i in range(9)]
            if rec0 is None:
                c16.add(False, f"{rid}: 命名空间记录未定位（cid={cid16} layer={layer}）")
                continue
            branches = []
            for f in flds:
                pid = rec0.get(f)
                if not pid:
                    continue
                blay = "CACHE" if pid in _BOSS_DOC["CACHE"][0] else "APK"
                prec = _BOSS_DOC[blay][0].get(pid)
                if prec is None:
                    continue
                t13s = []
                for j in range(8):
                    sid = prec.get(f"skillid{j}")
                    if not sid:
                        continue
                    s = _BOSS_DOC[blay][1].get(sid)
                    if s and s.get("skillid0") == 13:
                        t13s.append((sid, blay, s))
                branches.append((f, pid, blay, (prec.get("hpstart"), prec.get("hpend")), t13s))
            got_labels = sorted({a.get("condition_label") for a in row.get("answers") or []
                                 if a.get("condition_label")})
            exp_labels = sorted({"HP %s–%s%%" % (b[3][0] if b[3][0] is not None else "?",
                                                 b[3][1] if b[3][1] is not None else "?")
                                 for b in branches})
            if got_labels != exp_labels or got_labels != sorted(expected_labels):
                c16.add(False, f"{rid}: 档位标签 集 answers={got_labels} ≠ 记录分档={exp_labels} "
                              f"≠ 行 expected={sorted(expected_labels)}")
                continue
            # 每档位：答案值行逐槽等于该档 t13 原值（float32 口径），来源记录逐字一致
            import struct as _st

            def _f32(x):
                return _st.unpack("f", _st.pack("f", float(x)))[0]
            bad = []
            for f, pid, blay, cond, t13s in branches:
                lab = "HP %s–%s%%" % (cond[0] if cond[0] is not None else "?",
                                      cond[1] if cond[1] is not None else "?")
                cand_t13 = [t for t in t13s]
                if len(cand_t13) != 1:
                    bad.append(f"{lab}: t13 候选 {len(cand_t13)} 个")
                    continue
                sid, tlay, s = cand_t13[0]
                for q in (1, 2, 3, 6):
                    rv = s.get(f"skillparam{q}")
                    if not (isinstance(rv, (int, float)) and not isinstance(rv, bool) and rv != 0):
                        continue
                    a = next((a for a in row["answers"]
                              if a.get("condition_label") == lab
                              and a.get("field_path") == f"/skillparam{q}"), None)
                    if a is None:
                        bad.append(f"{lab}: /skillparam{q} 无值行")
                    elif _f32(a.get("raw_value")) != _f32(rv):
                        bad.append(f"{lab}: /skillparam{q} 答案 {a.get('raw_value')!r} ≠ 原值 {rv!r}")
                    elif (a.get("source") or {}).get("record_key") != f"bossskill|{sid}|{tlay}":
                        bad.append(f"{lab}: /skillparam{q} 来源 {((a.get('source') or {}).get('record_key'))} "
                                   f"≠ bossskill|{sid}|{tlay}")
            if bad:
                c16.add(False, f"{rid}: " + "；".join(bad[:6]))
            else:
                c16.add(True)
            # 第 16 项扩展（R1-Medium 复审整改 20261023）：父链文本与 condition_label
            # 一致性——numeric_source 父链/注记「本档位 pattern 引用」段须引用该档实际
            # pattern（不得固定首档；修复前数据上 FAIL，见
            # work/character_skills_recheck_rectification/parent_chain_prefix_fail_evidence.json）。
            pc_bad = r1_parent_chain_assert(row, branches)
            if pc_bad:
                c16.add(False, f"{rid}: 父链注记与条件标签不一致（R1-Medium）"
                               f"{len(pc_bad)} 处：" + "；".join(pc_bad[:4]))
        c16.counters.update(hp_branch_rows=n16)
        checks.append(c16.done())

        # ---- 17 R2 定向：完成判定与当前代码重算一致（账本新鲜度；语义正反例由
        #      a7/r2 回归与 r2_screen 承担——本检查不 import 账本实现以外的捷径，
        #      analyze_row 即账本实现本身：检测账本是否由当前代码/当前 pages 重建） ----
        c17 = Check("r2_completion_recompute",
                    "R2 定向：ledger 行状态/拆分标志 == 当前代码 analyze_row 全量重算"
                    "（检测账本与 pages/代码不同步）")
        import effect_ledger as _EL
        bad17 = []
        n17 = 0
        for rid, dsc in ledger_desc.items():
            row = pages_rows.get(rid)
            if row is None:
                continue
            n17 += 1
            res = _EL.analyze_row(row, table=(dsc.get("namespace") or {}).get("table"))
            flags_now = sorted(f["code"] for f in res["split_flags"])
            flags_led = sorted(f["code"] for f in dsc.get("split_flags") or [])
            st_now = (dsc.get("ledger_row_status"))
            if flags_now != flags_led:
                bad17.append(f"{rid}: 拆分标志 {flags_led} ≠ 重算 {flags_now}")
            elif st_now == "完整" and res["split_flags"]:
                bad17.append(f"{rid}: 账本完整但重算有标志 {flags_now}")
        if bad17:
            c17.add(False, f"重算不一致 {len(bad17)} 行（例：{bad17[:5]}）")
        else:
            c17.add(True)
        c17.counters.update(rows_recomputed=n17, mismatches=len(bad17))
        checks.append(c17.done())

        for c in (c11, c12, c13, c14, c15):
            checks.append(c.done())

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
                      "检查 6 为双侧统计（DS-GR-10 修复 20261023）：推断答案带 source 计 ok、"
                      "不带计 fail，不再是 ok=0/failed=0 的 no-op；检查 15 为内容级核对"
                      "（DS-GR-R4 扩展）：页面未解决区与账本逐行计数＋类型/方向/对象多重集"
                      "一致，且 has_answer ダメージ效果对象一致（DS-GR-R1 口径）",
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
