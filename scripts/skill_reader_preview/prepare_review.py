"""Freeze a local Web review manifest and source copy; does not start a reviewer."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path, write_path, path_reference

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def data_ref(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path_reference(path, root=ROOT)


def document_source(name):
    logical = ROOT/'docs/tasks'/name
    return logical, logical.relative_to(ROOT).as_posix()


def guard_input(rel):
    logical = (ROOT/rel).resolve()
    if not logical.is_relative_to(ROOT.resolve()):
        raise ValueError('Mainline guard path escapes source namespace: ' + rel)
    return logical if Path(rel).parts[0] == 'scripts' else read_path(logical, root=ROOT)


def prepare(reader, target, audit_dir='audit/c19_closeout_20261107', document_names=None):
    reader = read_path(reader, root=ROOT)
    target = write_path(target, root=ROOT)
    if target.exists():
        raise FileExistsError('Review input snapshots are immutable; select a new target')
    audit = reader / audit_dir
    required = ['c19_validation.json', 'confidence_validation.json', 'condition_validation.json',
                'browser_validation.json', 'mainline_unchanged.json', 'publish_receipt.json']
    for name in required:
        p = audit / name
        obj = json.loads(p.read_text(encoding='utf-8'))
        if name != 'publish_receipt.json' and not (obj.get('pass') is True or obj.get('passed') is True or obj.get('status') == 'PASS'):
            raise ValueError('Missing passing closeout evidence: '+str(p))
    if not json.loads((reader/'validation.json').read_text('utf-8')).get('passed'):
        raise ValueError('Reader validation failed')
    files = {}
    for p in sorted(reader.rglob('*')):
        if p.is_file():
            files[data_ref(p)] = {'bytes':p.stat().st_size, 'sha256':digest(p)}
    source_files = [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                    and p.suffix in {'.py','.js','.json','.css','.html','.md'}]
    target.mkdir(parents=True)
    source = {}
    for p in source_files:
        dest = target/'source'/p.relative_to(HERE)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest)
        source[p.relative_to(ROOT).as_posix()] = {'sha256':digest(p),'snapshot':dest.relative_to(target).as_posix()}
    documents = {}
    for name in (document_names or ['20261107-reader-c19-closeout.md', '20261107-reader-mainline-evidence-handoff.md',
                 '20261107-reader-thirdparty-review-prompt.md']):
        logical, key = document_source(name)
        p = read_path(logical, root=ROOT)
        dest = target/'documents'/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest)
        documents[key] = {'sha256':digest(p),'snapshot':dest.relative_to(target).as_posix()}
    mainline = json.loads((audit/'mainline_guard.json').read_text('utf-8'))
    for rel, expected in mainline.items():
        if digest(guard_input(rel)) != expected:
            raise ValueError('Mainline changed before review freeze: '+rel)
    data = {'schema':'reader-review-input-v1','createdAt':datetime.now(timezone.utc).isoformat(),
            'status':'PREPARED_NOT_REVIEWED', 'reader':data_ref(reader),
            'snapshot':json.loads((reader/'build_receipt.json').read_text('utf-8'))['snapshot'],
            'readerFiles':files,'sourceFiles':source,'documents':documents,'mainlineGuard':mainline,
            'externalDependencies':[
                'output/character_skills/pages/art/: shared images; retain sibling directory layout',
                'output/base_master and output/cache_full_20261015_v3/decoded: original decoded tables',
                'work/protection/il2cpp_loader_seed1.bin and metadata_aei_decoded.bin: bounded native evidence inputs',
                'Existing frozen semantic review/reference files and the C19 accepted report: see migration receipt'],
            'scope':'Local independent-review inputs, not a standalone unpack release or a completed third-party review'}
    manifest = target/'manifest.json'
    manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (target/'manifest.sha256').write_text(digest(manifest)+'  manifest.json\n',encoding='utf-8')
    return {'status':data['status'],'readerFiles':len(files),'sourceFiles':len(source),'manifest':str(manifest)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reader',type=Path,default=ROOT/'output/character_skills/reader_full_20261106')
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--audit-dir',default='audit/c19_closeout_20261107')
    parser.add_argument('--document',action='append')
    args=parser.parse_args()
    print(json.dumps(prepare(args.reader.resolve(),args.target.resolve(),args.audit_dir,args.document),ensure_ascii=False))
