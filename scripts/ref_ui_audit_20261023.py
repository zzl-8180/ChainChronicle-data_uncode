"""Static UI audit only; does not run reference scripts or alter their pages."""
import hashlib
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from project_layout_paths import read_path
from versioned_outputs import fresh_output
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
FIRST = read_path(ROOT / '其他人的参考/claude_cc_site_pages 20261023', root=ROOT)
LATE = read_path(ROOT / '其他人的参考/claude_cc_site_pages_给GPT_20261023/claude_cc_site_pages', root=ROOT)
OURS = read_path(ROOT / 'output/character_skills/pages', root=ROOT)


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.tags = Counter()
        self.classes = Counter()
        self.ids = set()
        self.images = []
        self.controls = []
        self.links = []
        self.headings = []
        self.source_spans = []
        self.capture = None
        self.collected = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags[tag] += 1
        self.classes.update(a.get('class', '').split())
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'img':
            src = a.get('src', '')
            url = urlsplit(src)
            local = bool(src) and not url.scheme and not url.netloc
            self.images.append({'src': src, 'alt': a.get('alt'), 'local_exists': (self.path.parent / unquote(url.path)).is_file() if local else None})
        if tag in ('input', 'select', 'button'):
            self.controls.append({'tag': tag, **a})
        if tag == 'a':
            self.links.append(a)
        if 'data-src' in a:
            self.source_spans.append({'tag': tag, **a})
        if tag in ('h1', 'h2', 'h3', 'title', 'summary', 'button'):
            self.capture = tag
            self.collected = []

    def handle_data(self, data):
        if self.capture:
            self.collected.append(data)

    def handle_endtag(self, tag):
        if tag == self.capture:
            self.headings.append({'tag': tag, 'text': ''.join(self.collected).strip()})
            self.capture = None

    def result(self, raw):
        missing_links = []
        for a in self.links:
            u = urlsplit(a.get('href', ''))
            if u.path and not u.scheme and not u.netloc and not (self.path.parent / unquote(u.path)).exists():
                missing_links.append(a)
        return {'path': self.path.relative_to(ROOT).as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                'tags': dict(self.tags), 'classes': dict(self.classes), 'headings': self.headings,
                'controls': self.controls, 'image_count': len(self.images),
                'missing_local_images': [r for r in self.images if r['local_exists'] is False],
                'empty_or_missing_alt_count': sum(not r['alt'] for r in self.images),
                'internal_anchor_links': [r for r in self.links if r.get('href', '').startswith('#')],
                'non_anchor_links_sample': [r for r in self.links if not r.get('href', '').startswith('#')][:6],
                'missing_local_link_count': len(missing_links), 'missing_local_link_samples': missing_links[:3],
                'source_span_count': len(self.source_spans),
                'source_spans_with_tabindex': sum('tabindex' in r for r in self.source_spans),
                'source_span_samples': self.source_spans[:3]}


def main():
    paths = []
    for root in (FIRST, LATE):
        paths.extend([root / 'index_unpack.html', root / 'index.html'])
        for cid in (30236, 351, 10210):
            dirs = [p for p in (root / 'cards').glob(f'cid{cid}*') if p.is_dir() and not p.name[len(f'cid{cid}'):len(f'cid{cid}') + 1].isdigit()]
            assert len(dirs) == 1, (cid, dirs)
            paths.append(dirs[0] / 'unpack.html')
    paths.extend(OURS / f for f in ('index.html', 'all_cards.html'))
    paths.extend(OURS / str(cid) / 'index.html' for cid in (30236, 351, 10210))
    pages = []
    for path in paths:
        raw = path.read_bytes()
        parser = Page(path)
        parser.feed(raw.decode('utf-8-sig'))
        pages.append(parser.result(raw))
    sources = [LATE / 'scripts/unpack_theme.py', LATE / 'scripts/render_unpack.py',
               ROOT / 'scripts/character_skills/card_page_render_v2.py', ROOT / 'scripts/character_skills/card_page_index.py']
    source_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    OUT = fresh_output("projects/reference-analysis/reports", "reference-ui")
    (OUT / 'static_evidence.json').write_text(json.dumps({'method': 'HTMLParser and source inspection; no browser rendering or interaction execution',
        'pages': pages, 'source_hashes': source_hashes}, ensure_ascii=False, indent=2), encoding='utf-8')
    for p in pages:
        print(json.dumps({k: p[k] for k in ('path', 'bytes', 'image_count', 'source_span_count')}, ensure_ascii=False),
              'missing_images', len(p['missing_local_images']), 'anchor_links', len(p['internal_anchor_links']))


if __name__ == '__main__':
    main()
