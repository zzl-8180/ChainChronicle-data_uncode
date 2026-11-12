"""Keep independent Reader reports and staged evidence separate from frozen files."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path
from versioned_outputs import fresh_output, require_new_files, write_new_text


def review_output(label, stage=None):
    if stage is None:
        return fresh_output("projects/reader/reports/review", label)
    return write_path(stage)
