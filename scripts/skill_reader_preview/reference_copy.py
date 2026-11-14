from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from collections import Counter
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path
from rerun_output import require_new_files, review_output, write_new_text

NUMBERED_PARENS = re.compile(r"（[^（）]*(?:\d|？|\?|ATK)[^（）]*）|\([^()]*?(?:\d|？|\?|ATK)[^()]*?\)", re.I)
CN_TITLE = re.compile(r"^\s*【[^】]*】\s*")
JP_NAME = re.compile(r"^\s*[^：:\n]{1,80}[：:]\s*")
SPLIT_CLAUSE = re.compile(r"(?<=。)|(?<=！)|(?<=？)")
TERM_EQUIV = (
    ("眩晕", "眩晕"), ("眩暈", "眩晕"),
    ("暴击伤害", "暴击威力"), ("暴击威力", "暴击威力"),
    ("法珠", "法珠"), ("法珠", "法珠"),
    ("后备队伍", "副队伍"), ("后备队伍", "副队伍"),
    ("主要队伍", "主队伍"), ("主要队伍", "主队伍"),
    ("击飞", "弹飞"), ("暗盲", "黑暗"),
    ("通常攻击", "普通攻击"), ("通常回复", "普通回复"),
)


def _norm_zh(text: str) -> str:
    text = re.sub(r"\s+", "", text)
    for a, b in TERM_EQUIV:
        text = text.replace(a, b)
    return text


def _clean_zh(text: str) -> str:
    text = html.unescape(text).replace("\u3000", " ").strip()
    text = CN_TITLE.sub("", text)
    text = NUMBERED_PARENS.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_jp(text: str) -> str:
    # Keep source line breaks: Japanese fragments may be line-separated in div.jp.
    text = html.unescape(text).replace("\u3000", " ").replace("\r", "").strip()
    text = JP_NAME.sub("", text, count=1)
    text = re.sub(r"^\s*【[^】]*】\s*", "", text)
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")).strip()


def _jp_blocks(text: str) -> list[str]:
    blocks = []
    for block in re.split(r"◆|\n+", text):
        block = block.strip()
        if not block:
            continue
        blocks.extend(x.strip() for x in re.split(r"(?<=[。！？])", block) if x.strip())
    return blocks


def _zh_sentences(text: str, comma_fallback: bool = False) -> list[str]:
    if comma_fallback:
        # Conservative retry for known independent follow-up clauses only.
        text = re.sub(r"(?<=[，,])(?=(?:发动中不能|此效果在|移动后恢复))", "§", text)
        pieces = re.split("§", text)
    else:
        pieces = [text]
    out = []
    for piece in pieces:
        for part in re.split(r"[；;。！？]+", piece):
            part = CN_TITLE.sub("", part.strip())
            if part:
                out.append(part)
    return out


class _ArticleParser(HTMLParser):
    """Collect each article's data-copy and its first raw details div.jp."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.articles: list[dict[str, str]] = []
        self.cur: dict[str, Any] | None = None
        self.depth = 0
        self.jp_depth: int | None = None
        self.jp_chunks: list[str] = []
        self.in_jp = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        at = dict(attrs)
        if tag == "article" and "data-copy" in at:
            self.cur = {"zh": at.get("data-copy") or "", "jp": ""}
            self.depth = 1
        elif self.cur is not None:
            if tag == "article":
                self.depth += 1
            classes = (at.get("class") or "").split()
            if tag == "div" and "jp" in classes and not self.cur["jp"]:
                self.in_jp = True
                self.jp_depth = self.depth
            elif self.in_jp and tag not in {"br", "img", "hr", "meta", "link", "input"}:
                self.jp_depth = (self.jp_depth or self.depth) + 1

    def handle_endtag(self, tag: str) -> None:
        if self.cur is None:
            return
        if self.in_jp and tag == "div" and self.jp_depth is not None:
            self.jp_depth -= 1
            if self.jp_depth <= self.depth:
                self.cur["jp"] = "".join(self.jp_chunks).strip()
                self.jp_chunks = []
                self.in_jp = False
                self.jp_depth = None
        if tag == "article":
            self.depth -= 1
            if self.depth <= 0:
                if self.cur.get("jp"):
                    self.articles.append({"zh": str(self.cur["zh"]), "jp": str(self.cur["jp"])})
                self.cur = None
                self.depth = 0

    def handle_data(self, data: str) -> None:
        if self.cur is not None and self.in_jp:
            self.jp_chunks.append(data)


def _source_articles(root: Path, source_map=None):
    cards = root / "cards"
    if not cards.exists():
        raise FileNotFoundError(f"reference cards directory not found: {cards}")
    if source_map is not None:
        paths = (source_map.resolve(member)[0] for member in sorted(source_map.members)
                 if member.startswith('cards/'))
    else:
        paths = (card_dir / 'unpack.html' for card_dir in sorted(cards.iterdir())
                 if card_dir.is_dir() and (card_dir / 'unpack.html').exists())
    for path in paths:
        parser = _ArticleParser()
        parser.feed(path.read_text(encoding="utf-8"))
        for index, article in enumerate(parser.articles):
            yield path, index, article


def _audit(root: Path, source_map=None):
    candidates: dict[str, list[dict[str, str]]] = defaultdict(list)
    audit: dict[str, Any] = {
        "version": 1,
        "source_root": str(root),
        "articles_seen": 0,
        "paired_sentences": 0,
        "unpaired_articles": [],
        "conflicts": [],
        "number_check": {"checked": 0, "mismatch": []},
        "method": "article data-copy + first details div.jp; strict ordered pairing after ◆/line/semicolon/full-stop splits; conservative Chinese comma retry before fixed clause starters; strip Chinese numeric/？/ATK parentheticals; reject unsupported Chinese body numbers",
    }
    normalize = lambda t: unicodedata.normalize("NFKC", t)
    for path, index, item in _source_articles(root, source_map):
        audit["articles_seen"] += 1
        zh = _clean_zh(item["zh"])
        jp = _clean_jp(item["jp"])
        zh_blocks = [_clean_zh(x) for x in re.split(r"\s*◆\s*", zh) if _clean_zh(x)]
        jp_blocks = [x.strip() for x in re.split(r"◆|\n+", jp) if x.strip()]
        if len(zh_blocks) != len(jp_blocks):
            zh_blocks, jp_blocks = [zh], [jp]
        tentative: list[tuple[str, str, str]] = []
        failure = None
        for bi, (zb, jb) in enumerate(zip(zh_blocks, jp_blocks)):
            block_method = "ordered_sentence_pair"
            js = _jp_blocks(jb)
            zs = _zh_sentences(zb)
            if len(zs) != len(js):
                fallback = _zh_sentences(zb, comma_fallback=True)
                if len(fallback) == len(js):
                    zs, block_method = fallback, "ordered_pair_comma_clause_retry"
                else:
                    failure = {"zh_sentence_count": len(zs), "zh_comma_retry_count": len(fallback), "jp_sentence_count": len(js), "block": bi}
                    break
            tentative.extend((z, j, block_method) for z, j in zip(zs, js))
        source = f"{path.relative_to(root).as_posix()}#article[{index}]"
        if failure:
            audit["unpaired_articles"].append({"source": source, **failure})
            continue
        # Validate the whole article before adding anything, so a number anomaly cannot partially leak candidates.
        anomalies = []
        for zsent, jsent, _ in tentative:
            audit["number_check"]["checked"] += 1
            jp_nums = Counter(re.findall(r"\d+(?:\.\d+)?", normalize(jsent)))
            zh_nums = Counter(re.findall(r"\d+(?:\.\d+)?", normalize(zsent)))
            extra = list((zh_nums - jp_nums).elements())
            if extra:
                anomalies.append({"jp": jsent, "zh": zsent, "zh_numbers_not_in_jp": sorted(extra), "source": source})
        if anomalies:
            audit["number_check"]["mismatch"].extend(anomalies)
            audit["unpaired_articles"].append({"source": source, "reason": "unsupported_chinese_body_number", "number_anomalies": anomalies})
            continue
        for zsent, jsent, pair_method in tentative:
            candidates[jsent].append({"textZh": zsent, "source": source, "method": pair_method})
            audit["paired_sentences"] += 1
    resolved: dict[str, dict[str, str]] = {}
    for jp, rows in candidates.items():
        unique: dict[str, dict[str, str]] = {}
        for row in rows:
            key = _norm_zh(row["textZh"])
            if key not in unique:
                unique[key] = {**row, "sources": [row["source"]]}
            elif row["source"] not in unique[key]["sources"]:
                unique[key]["sources"].append(row["source"])
        if len(unique) == 1:
            row = next(iter(unique.values()))
            row.pop("sources", None)
            resolved[jp] = row
        else:
            audit["conflicts"].append({"japanese": jp, "candidates": list(unique.values())})
    audit["resolved_sentences"] = len(resolved)
    audit["pairs"] = resolved
    audit["candidate_japanese_sentences"] = len(candidates)
    audit["conflict_count"] = len(audit["conflicts"])
    audit["unpaired_article_count"] = len(audit["unpaired_articles"])
    audit["number_mismatch_count"] = len(audit["number_check"]["mismatch"])
    return resolved, audit


def load_reference(root: str | Path, source_map_manifest=None) -> dict[str, dict[str, str]]:
    """Return unreviewed sentence candidates keyed by exact Japanese sentence."""
    root = Path(root)
    source_map = None
    if source_map_manifest is not None:
        from reference_sources_v2 import ReferenceSourceMap
        root = root.absolute()
        source_map = ReferenceSourceMap.from_manifest(source_map_manifest, root)
    resolved, audit = _audit(root, source_map)
    load_reference.last_audit = audit
    return resolved


load_reference.last_audit = {}  # populated by load_reference


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2] / "其他人的参考" / "CC解包数据_给GPT_20261027" / "claude_cc_site_pages")
    ap.add_argument("--audit", type=Path, help="Path to a new report file")
    ap.add_argument("--source-map-manifest", type=Path, help="Explicit reviewed S5 allowlist; no global route activation")
    args = ap.parse_args()
    if args.source_map_manifest is None:
        args.root = read_path(args.root, root=Path(__file__).resolve().parents[2])
    args.audit = write_path(args.audit) if args.audit else review_output("reference-pairs") / "reference_pairs.json"
    require_new_files(args.audit)
    resolved = load_reference(args.root, args.source_map_manifest)
    audit = load_reference.last_audit
    write_new_text(args.audit, json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"resolved_sentences": len(resolved), "candidate_sentences": audit["candidate_japanese_sentences"], "articles_seen": audit["articles_seen"], "paired": audit["paired_sentences"], "conflicts": audit["conflict_count"], "unpaired_articles": audit["unpaired_article_count"], "number_mismatches": audit["number_mismatch_count"], "audit": str(args.audit)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
