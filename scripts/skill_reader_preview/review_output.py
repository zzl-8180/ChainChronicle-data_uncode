"""Select an independent reader review directory and keep existing reports."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import write_path


def parse_review_id(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--review-id',
        help='One folder name under projects/reader/reports/review (default: fresh UTC timestamp).',
    )
    return parser.parse_args().review_id


def review_directory(root, review_id=None):
    if review_id is None:
        review_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', review_id):
        raise ValueError('Review ID must be a single name using letters, digits, underscores or hyphens.')
    out = write_path(root / 'projects/reader/reports/review' / review_id, root=root)
    if out.resolve() != out:
        raise ValueError(f'Review output must be a direct directory: {out}')
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_new_text(path, text):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(text)
