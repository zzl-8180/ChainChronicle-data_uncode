"""Sparse B02 frontend path; fixed original payload and media remain read-only."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CODE = ROOT / 'scripts/skill_reader_preview'
SOURCE = ROOT / 'output/character_skills/reader_full_20261106'
CANDIDATE = ROOT / 'projects/reader/site/b02-20261108-v1'
REPORTS = ROOT / 'projects/reader/reports/b02-20261108-v1'
LEGACY_REPORTS = ROOT / 'output/project-layout/b02-20261108-v1'
DOCS = ROOT / 'docs/project-layout/20261108-b02-candidate-v1'
MEDIA = ROOT / 'output/character_skills/pages/art'
C18 = ROOT / 'output/character_skills/reader_c18_before_c19_20261107'
LABEL_BASELINE = ROOT / 'output/character_skills/reader_c19_before_r01_20261107'
SNAPSHOT = '99bee2a1-cf9451c6ff47fcfb'
DATA_BASE = '../../../../output/character_skills/reader_full_20261106/data/'
MEDIA_BASE = '../../../../output/character_skills/pages/art/'
EVIDENCE_BASE = '../../../../output/character_skills/reader_full_20261106/audit/'
WEB = ('index.html', 'app.js', 'inline.js', 'branches.js', 'levels.js', 'style.css')
LIMIT = 9 * 1024 * 1024
READS, BLOCKED = {}, []
_hashing = False


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def read(path):
    return json.loads(path.read_text('utf-8-sig'))


def size():
    roots = (HERE, CANDIDATE, REPORTS, LEGACY_REPORTS, DOCS)
    total = sum(p.stat().st_size for root in roots if root.exists() for p in root.rglob('*') if p.is_file())
    ignore = CANDIDATE.parent / '.gitignore'
    return total + (ignore.stat().st_size if ignore.is_file() else 0)


def budget(addition=0):
    current = size()
    if current + addition > LIMIT:
        raise ValueError(f'B02 space limit: {current}+{addition}>{LIMIT} bytes')
    return current


def write(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    budget(len(data))
    with path.open('xb') as stream:
        stream.write(data)


def no_links(path):
    for p in (path, *path.parents):
        if p.exists() and (p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Linked/reparse path refused: ' + str(p))


def within(path, roots):
    path = Path(path).absolute()
    no_links(path)
    actual = path.resolve()
    return any(actual == root or actual.is_relative_to(root) for root in roots)


def guard(roots):
    def hook(event, args):
        global _hashing
        if _hashing:
            return
        paths = []
        if event == 'open' and not isinstance(args[0], int):
            path, _mode, flags = args
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                paths = [path]
                budget()
            else:
                p = Path(path).absolute()
                if p.is_relative_to(ROOT) and not any(p.is_relative_to(root) for root in roots) and p.is_file():
                    no_links(p)
                    key = rel(p)
                    if key not in READS:
                        _hashing = True
                        try:
                            READS[key] = digest(p)
                        finally:
                            _hashing = False
        elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime'):
            paths = [args[0]]
        elif event in ('os.rename', 'os.link', 'os.symlink'):
            paths = list(args[:2])
        for path in paths:
            if not within(path, roots):
                BLOCKED.append({'event': event, 'path': str(path)})
                raise PermissionError('B02 write outside approved roots: ' + str(path))
    sys.addaudithook(hook)


def module(name):
    if str(CODE) not in sys.path:
        sys.path.insert(0, str(CODE))
    return importlib.import_module(name)


def runtime_hashes():
    receipt = read(SOURCE / 'build_receipt.json')
    names = ['build_receipt.json', 'frontend_receipt.json', *WEB, 'data/catalog.js']
    names += ['data/' + name + '.js' for name in ('branch_candidates', 'branch_conditions', 'mana_costs', 'branch_assessments')]
    names += ['data/cards/' + cid + '.js' for cid in receipt['sourceHashes']]
    result = {}
    for name in sorted(set(names)):
        no_links(SOURCE / name)
        result[name] = digest(SOURCE / name)
    return result


def candidate_bytes():
    output = {name: (SOURCE / name).read_bytes() for name in WEB}
    app = output['app.js'].decode('utf-8')
    before = "  const catalog = window.CC_CATALOG;"
    after = "  const paths = window.CC_B02_PATHS;\n  if (!paths || paths.snapshot !== '" + SNAPSHOT + "') throw new Error('Missing B02 fixed paths');\n" + before
    assert app.count(before) == 1
    app = app.replace(before, after)
    before = "'查看本轮核对结果与修改对照'"
    assert app.count(before) == 1
    app = app.replace(before, "'查看源版本审查（历史）'")
    before = "      reviewLink.href = 'audit/semantic_review.html';"
    after = "      reviewLink.href = paths.evidenceBase + 'semantic_review.html'; reviewLink.target = '_blank'; reviewLink.rel = 'noopener';"
    assert app.count(before) == 1
    app = app.replace(before, after)
    before = '    img.src = txt(src); img.alt = alt;'
    after = "    img.src = txt(src).startsWith('../pages/art/') ? paths.mediaBase + txt(src).slice('../pages/art/'.length) : txt(src); img.alt = alt;"
    assert app.count(before) == 1
    app = app.replace(before, after)
    before = '      script.src = `${file}?v='
    after = "      script.src = `${paths.dataBase}${file.slice('data/'.length)}?v="
    assert app.count(before) == 1
    app = app.replace(before, after)
    output['app.js'] = app.encode('utf-8')
    index = output['index.html'].decode('utf-8')
    assert index.count('<script src="data/') == 5
    index = index.replace('<script src="data/', '<script src="' + DATA_BASE)
    index = index.replace('  <script src="' + DATA_BASE + 'catalog.js', '  <script src="paths.js"></script>\n  <script src="' + DATA_BASE + 'catalog.js')
    index = re.sub(r'app\.js\?v=[0-9a-f]+', 'app.js?v=' + sha256(output['app.js']).hexdigest()[:12], index)
    output['index.html'] = index.encode('utf-8')
    config = {'snapshot': SNAPSHOT, 'dataBase': DATA_BASE, 'mediaBase': MEDIA_BASE, 'evidenceBase': EVIDENCE_BASE}
    output['paths.js'] = ('window.CC_B02_PATHS = Object.freeze(' + json.dumps(config, ensure_ascii=False) + ');\n').encode('utf-8')
    return output


def preflight():
    for path in (ROOT, SOURCE, C18, LABEL_BASELINE, MEDIA, CODE, CANDIDATE, REPORTS, LEGACY_REPORTS):
        no_links(path)
    receipt = read(SOURCE / 'build_receipt.json')
    assert receipt['snapshot']['snapshot_id'] == SNAPSHOT
    assert read(SOURCE / 'frontend_receipt.json')['snapshot'] == receipt['snapshot']
    assert read(ROOT / 'output/character_skills/effect_ledger/metrics.json')['snapshot'] == receipt['snapshot']
    data = candidate_bytes()
    for path in evidence_files():
        no_links(path)
        assert path.is_file(), 'Missing declared historical evidence: ' + str(path)
    assert (CANDIDATE / DATA_BASE).resolve() == SOURCE / 'data'
    assert (CANDIDATE / MEDIA_BASE).resolve() == MEDIA
    budget(sum(map(len, data.values())) + 2_000_000)
    assert shutil.disk_usage(ROOT).free > sum(map(len, data.values())) + 2_000_000
    return {'snapshot': receipt['snapshot'], 'sourceDataRoot': rel(SOURCE), 'candidate': rel(CANDIDATE),
            'candidateEstimatedBytes': sum(map(len, data.values())), 'currentTaskBytes': size(),
            'hardLimitBytes': LIMIT, 'freeBytes': shutil.disk_usage(ROOT).free,
            'mediaRoot': rel(MEDIA), 'dataBase': DATA_BASE, 'mediaBase': MEDIA_BASE,
            'baselines': {'c19Conservation': rel(C18), 'r01Labels': rel(LABEL_BASELINE)}}


def receive(run):
    if CANDIDATE.exists():
        raise FileExistsError('Existing candidate refused')
    info = preflight()
    before = runtime_hashes()
    output = candidate_bytes()
    CANDIDATE.mkdir(parents=True)
    for name, data in output.items():
        budget(len(data))
        with (CANDIDATE / name).open('xb') as stream:
            stream.write(data)
    assert runtime_hashes() == before, 'Source drift during receive'
    write(run / 'source-runtime.json', before)
    result = {'status': 'PASS', 'runId': run.name, **info, 'candidateFrontendHashes': frontend_check(),
              'claim': 'Sparse frontend received; source data/media/audits were not copied or changed; no candidate validation claim yet'}
    write(run / 'receipt.json', result)
    return result


def frontend_check():
    wanted = candidate_bytes()
    assert {p.name for p in CANDIDATE.iterdir()} == set(wanted), 'Unexpected candidate file set'
    for name, data in wanted.items():
        path = CANDIDATE / name
        no_links(path)
        assert path.stat().st_nlink == 1, 'Hardlink refused: ' + name
        assert path.read_bytes() == data, 'Unexpected frontend change: ' + name
    return {name: sha256(data).hexdigest() for name, data in wanted.items()}


def received_identity(receive_run):
    if not receive_run or not re.fullmatch(r'[A-Za-z0-9_-]+', receive_run):
        raise ValueError('Explicit --receive-run is required for validate/serve')
    base = REPORTS / receive_run
    if not os.path.lexists(base):
        base = LEGACY_REPORTS / receive_run
    no_links(base)
    receipt = read(base / 'receipt.json')
    assert receipt['status'] == 'PASS' and receipt['candidate'] == rel(CANDIDATE)
    assert receipt['candidateFrontendHashes'] == frontend_check(), 'Frontend differs from receive receipt'
    hashes = read(base / 'source-runtime.json')
    assert runtime_hashes() == hashes, 'Source changed since receive'
    return {'receiveRun': receive_run, 'receiptSHA256': digest(base / 'receipt.json'),
            'sourceRuntimeManifestSHA256': digest(base / 'source-runtime.json')}


def node(run, name, args):
    for arg in args:
        p = Path(arg)
        if p.is_file():
            digest(p)  # include subprocess code/evidence in guarded read manifest
    proc = subprocess.run(['node', *map(str, args)], cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace')
    write(run / (name + '-process.json'), {'command': ['node', *map(str, args)], 'exitCode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr})
    assert proc.returncode == 0, name + ' exited ' + str(proc.returncode)
    budget()


def validate(run, receive_run):
    preflight()
    received = received_identity(receive_run)
    frontend = frontend_check()
    before = runtime_hashes()
    # This only validates the existing source adaptation identity and source
    # hashes. Original semantic proofs are inherited with their original scope;
    # none of their historical PASS files is a new B02 semantic execution.
    source_receipt = SOURCE / 'audit/c19_r01_fix_20261107/sidecar_adaptation.json'
    adaptation = module('revalidate_sidecars').verify_adaptation(SOURCE, source_receipt, ROOT)
    write(run / 'source-identity-validation.json', {'status': 'PASS', 'runId': run.name,
          'receipt': rel(source_receipt), 'receiptSHA256': digest(source_receipt),
          'claim': 'Original source adaptation identity and primary source hashes checked; semantic proofs not rerun'})
    # These checks consume actual candidate frontend bytes with source data.
    for name in ('app.js', 'paths.js', 'inline.js', 'branches.js', 'levels.js'):
        node(run, name.replace('.', '-'), ['--check', CANDIDATE / name])
    node(run, 'branch-wiring', [CODE / 'verify_branch_wiring.js', '--output', SOURCE, '--web-root', CANDIDATE,
         '--receipt', SOURCE / 'audit/c19_closeout_20261107/condition_closeout_receipt.json'])
    assert runtime_hashes() == before, 'Source drift during validation'
    assert frontend_check() == frontend, 'Candidate drift during validation'
    write(run / 'composition.json', {'schema': 'b02-sparse-composition-v1', 'status': 'PASS', 'runId': run.name,
          'candidateFrontendHashes': frontend, 'sourceRuntimeHashes': before,
          'receivedIdentity': received,
          'sourceSidecarAdaptation': {'path': rel(source_receipt), 'sha256': digest(source_receipt)},
          'paths': {'dataBase': DATA_BASE, 'mediaBase': MEDIA_BASE, 'evidenceBase': EVIDENCE_BASE},
          'claim': 'Fresh source identity checks plus actual candidate frontend/planner composition; semantic proofs inherited, browser acceptance separate; historical source seal does not seal candidate'})
    return {'status': 'PASS', 'runId': run.name, 'snapshot': SNAPSHOT, 'sidecarCounts': adaptation['counts'],
            'sourceIdentityChecks': ['runtime hashes', 'existing adaptation/source hashes'],
            'candidateFrontendProofs': ['exact permitted transforms', 'actual JS syntax', 'branch wiring'],
            'scopeLimits': ['No browser claim in this result', 'No full builder port, payload copy, media copy, publication, new semantics or game runtime verification', 'Full/C19/R01/V01 semantic proofs inherited unchanged with original scope; not reexecuted in B02']}


def serve(port, receive_run):
    if port == 8768:
        raise ValueError('8768 reserved for existing service')
    frontend_check()
    received_identity(receive_run)
    allowed_files = {(SOURCE / name).resolve() for name in runtime_hashes() if name.startswith('data/')}
    allowed_files.update((SOURCE / name).resolve() for name in WEB)
    allowed_files.update(p.resolve() for p in evidence_files())
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)
        def send_head(self):
            target = ROOT / unquote(urlsplit(self.path).path).lstrip('/')
            if target.resolve() in (SOURCE.resolve(), CANDIDATE.resolve()):
                self.send_response(302)
                self.send_header('Location', '/' + rel(target.resolve()) + '/index.html')
                self.end_headers()
                return None
            try:
                no_links(target)
                allowed = within(target, [CANDIDATE.resolve(), MEDIA.resolve()]) or target.resolve() in allowed_files
            except ValueError:
                allowed = False
            if not allowed or not target.is_file():
                self.send_error(404)
                return None
            # Open precisely the file that was authorized, rather than letting
            # SimpleHTTP translate the URL a second time with different rules.
            stream = target.resolve().open('rb')
            self.send_response(200)
            self.send_header('Content-type', self.guess_type(str(target)))
            self.send_header('Content-Length', str(os.fstat(stream.fileno()).st_size))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return stream
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print('http://127.0.0.1:' + str(port) + '/' + rel(CANDIDATE) + '/index.html', flush=True)
    server.serve_forever()


def evidence_files():
    return [SOURCE / 'audit/semantic_review.html', SOURCE / 'audit/semantic_review.json',
            SOURCE / 'audit/translation_rows.jsonl', SOURCE / 'validation.json',
            ROOT / 'output/character_skills/reader_semantic_20261107/review_progress.json']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['preflight', 'receive', 'validate', 'serve'])
    parser.add_argument('--run-id')
    parser.add_argument('--port', type=int, default=8779)
    parser.add_argument('--receive-run', help='Exact previously accepted receive run for validate/serve')
    args = parser.parse_args()
    if args.action == 'serve':
        return serve(args.port, args.receive_run)
    if args.action == 'preflight':
        print(json.dumps(preflight(), ensure_ascii=False))
        return
    if not args.run_id or not re.fullmatch(r'[A-Za-z0-9_-]+', args.run_id):
        raise ValueError('Fresh simple --run-id required')
    run = REPORTS / args.run_id
    no_links(run)
    if os.path.lexists(run) or os.path.lexists(LEGACY_REPORTS / args.run_id):
        raise FileExistsError('Existing run refused; keep diagnostics')
    roots = [run.resolve()]
    if args.action == 'receive':
        if CANDIDATE.exists():
            raise FileExistsError('Existing candidate refused')
        roots += [CANDIDATE.resolve(), (CANDIDATE.parent / '.gitignore').resolve()]
    REPORTS.mkdir(parents=True, exist_ok=True)
    run.mkdir()
    # Parent directories are created explicitly before the guarded candidate write.
    if args.action == 'receive':
        CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
    guard(roots)
    try:
        if args.action == 'receive':
            ignore = CANDIDATE.parent / '.gitignore'
            no_links(ignore)
            if not ignore.exists():
                data = b'/b02-20261108-v1/\n'
                budget(len(data))
                with ignore.open('xb') as stream:
                    stream.write(data)
        status = receive(run) if args.action == 'receive' else validate(run, args.receive_run)
        for name, expected in list(READS.items()):
            assert digest(ROOT / name) == expected, 'Input drift during run: ' + name
        write(run / 'result.json', status)
    except Exception as error:
        write(run / 'failure.json', {'status': 'FAIL', 'runId': run.name, 'error': repr(error)})
        raise
    finally:
        write(run / 'input-manifest.json', {'actualProjectReadsSHA256': READS, 'blockedWrites': BLOCKED,
              'adapterSHA256': {p.name: digest(p) for p in HERE.iterdir() if p.is_file()},
              'taskBytesBeforeThisManifest': size(), 'hardLimitBytes': LIMIT,
              'generatedAt': datetime.now(timezone.utc).isoformat()})
    print(json.dumps({'status': status['status'], 'report': rel(run), 'taskBytes': budget()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
