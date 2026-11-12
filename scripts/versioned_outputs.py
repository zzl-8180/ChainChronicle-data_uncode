"""Fresh output directories for independent reruns and multi-step experiments."""
from datetime import datetime, timezone
import os
from os.path import relpath
from pathlib import Path
import re

from project_layout_paths import read_path, write_path


def fresh_output(parent, label, output=None):
    if output is None:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        output = Path(parent) / f'{label}-{stamp}'
    directory = write_path(output)
    if directory.resolve() != directory.absolute():
        raise ValueError(f'Output path must be a direct directory: {directory}')
    directory.mkdir(parents=True)
    return directory


def require_new_files(*paths):
    for path in paths:
        if path.resolve() != path.absolute():
            raise ValueError(f"Output must be a direct path: {path}")
        if path.exists():
            raise FileExistsError(f"Choose a new output path: {path}")


def write_new_text(path, content):
    require_new_files(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(content)


def experiment_report_source(family, original):
    if 'CC_EXPERIMENT_RUN_ID' in os.environ:
        return experiment_output(family)
    return read_path(original)


def report_links(document, source, output):
    def replace_link(match):
        link = match[1]
        if '://' in link or (output / link).is_file():
            return match[0]
        return f'href="{Path(relpath(source / link, output)).as_posix()}"'
    return re.sub(r'href="([^"]+)"', replace_link, document)


def experiment_output(family):
    run_id = os.environ.get('CC_EXPERIMENT_RUN_ID', '')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', run_id):
        raise ValueError('Set CC_EXPERIMENT_RUN_ID to one new version name (letters, digits, underscores or hyphens).')
    directory = write_path(Path('projects/skill-research/experiments') / family / 'runs' / run_id)
    if directory.resolve() != directory.absolute():
        raise ValueError(f'Experiment output must be a direct directory: {directory}')
    return directory
