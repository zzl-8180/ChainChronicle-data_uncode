"""Fail closed before legacy historical comparisons can read partial baselines or write old reports."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


class ReplayInputError(ValueError):
    pass


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def inspect_old(runs, expected_count=2236):
    """Use plans and transaction directories, never payload existence, to define coverage.

    Overlapping runs retain the original first-transaction-wins order. A missing
    earlier backup is an error even when a later run has the same cid.
    """
    errors, missing, paths, declared, hashes = [], [], {}, set(), {}
    for run in map(Path, runs):
        plan = run / 'plan.json'
        trans = run / 'transactions'
        if not plan.is_file() or not trans.is_dir():
            errors.append('missing plan/transactions: ' + str(run))
            continue
        declared.update(str(c) for c in read_json(plan)['cids'])
        for cd in sorted(trans.iterdir()):
            if not cd.is_dir() or not cd.name.isdigit():
                continue
            fp = cd / 'backup/card.json'
            paths.setdefault(cd.name, fp)
            if not fp.is_file():
                missing.append(str(fp))
                continue
            receipt = cd / 'backup/receipt.json'
            before = cd / 'backup/before.json'
            if not receipt.is_file() or not before.is_file():
                errors.append('missing backup provenance: ' + str(cd))
                continue
            expected = read_json(receipt).get('files', {}).get('card.json')
            if not expected or read_json(before).get('card.json') != expected:
                errors.append('inconsistent backup hashes: ' + str(cd))
                continue
            actual = digest(fp)
            if actual != expected:
                errors.append('backup hash mismatch: ' + str(fp))
            hashes[str(fp.resolve())] = actual
    if len(declared) != expected_count or set(paths) != declared:
        errors.append('incomplete baseline coverage: planned=%s transactions=%s expected=%s' %
                      (len(declared), len(paths), expected_count))
    return dict(status='BLOCKED' if missing or errors else 'INPUTS_COMPLETE',
                expected_cards=expected_count, transaction_cards=len(paths),
                missing_count=len(missing), missing=missing, errors=errors,
                paths={c: str(p.resolve()) for c, p in paths.items()}, old_hashes=hashes)


def inspect_new(pages, cids, signature):
    pages = Path(pages).resolve()
    found = {p.name for p in pages.iterdir() if p.is_dir() and p.name.isdigit()}
    if found != set(cids):
        raise ReplayInputError('new-side card set differs from the complete historical baseline')
    hashes = {}
    for cid in sorted(cids):
        card, receipt = pages / cid / 'card.json', pages / cid / 'receipt.json'
        if not card.is_file() or not receipt.is_file():
            raise ReplayInputError('missing new card/receipt: ' + cid)
        rec = read_json(receipt)
        actual = digest(card)
        if rec.get('status') != 'SUCCESS' or rec.get('signature') != signature:
            raise ReplayInputError('wrong new-side version/status: ' + cid)
        if rec.get('files', {}).get('card.json') != actual:
            raise ReplayInputError('new-side hash mismatch: ' + cid)
        if str(read_json(card).get('cid')) != cid:
            raise ReplayInputError('new-side cid mismatch: ' + cid)
        hashes[str(card)] = actual
    return hashes


def validate_comparison(comparison, binding, expected_count):
    provenance = comparison.get('_replay_guard', {})
    if (provenance.get('status') != 'PASS' or provenance.get('binding') != binding
            or provenance.get('expected_cards') != expected_count
            or provenance.get('script_name') != 'compare_zero_change.py'
            or comparison.get('stats', {}).get('cards') != expected_count
            or any(comparison.get(k) for k in ('missing', 'rowset', 'batch_key'))):
        raise ReplayInputError('拒绝未绑定同一完整输入的旧／失败对账结果')


class Replay:
    def __init__(self, script, runs, argv=None, expected_count=2236, metrics=False):
        self.script = Path(script).resolve()
        self.root = self.script.parents[2]
        parser = argparse.ArgumentParser(description='历史复验：先检查完整输入；禁止覆盖旧结果。')
        parser.add_argument('--check-inputs', action='store_true', help='只核查旧输入，不生成审查结论')
        parser.add_argument('--new-pages', type=Path, help='已冻结的对应历史新版本页面目录')
        parser.add_argument('--expected-new-signature', help='从对应历史审查核实的完整新版本签名')
        parser.add_argument('--out-dir', type=Path, help='尚不存在的新结果目录')
        if metrics:
            parser.add_argument('--comparison-result', type=Path)
            parser.add_argument('--aux-dir', type=Path, help='历史辅助材料目录（样例来源，不重新证明人工判定）')
        self.args = parser.parse_args(argv)
        if sys.flags.optimize:
            parser.error('旧比较含 assert，禁止使用 python -O/-OO 绕过断言')
        check = inspect_old(runs, expected_count)
        self.check = check
        if self.args.check_inputs:
            print(json.dumps({k: v for k, v in check.items() if k not in ('paths', 'old_hashes')}, ensure_ascii=False))
            raise SystemExit(2 if check['status'] == 'BLOCKED' else 0)
        if check['status'] == 'BLOCKED':
            print(json.dumps({k: v for k, v in check.items() if k not in ('paths', 'old_hashes')}, ensure_ascii=False))
            parser.error('历史旧输入不完整；未比较、未写入结果。')
        if not all((self.args.new_pages, self.args.expected_new_signature, self.args.out_dir)):
            parser.error('复验必须显式提供 --new-pages、--expected-new-signature、--out-dir')
        self.pages = self.args.new_pages.resolve()
        live = self.root / 'output/character_skills/pages'
        if self.pages == live.resolve():
            parser.error('禁止将当前正式 pages 自动当成历史新版本；请提供冻结副本')
        signature = self.args.expected_new_signature
        if len(signature) != 64 or any(c not in '0123456789abcdef' for c in signature):
            parser.error('expected-new-signature 必须是完整 SHA-256')
        new_hashes = inspect_new(self.pages, check['paths'], signature)
        binding = dict(old_hashes=check['old_hashes'], new_hashes=new_hashes,
                       expected_new_signature=signature)
        self.binding = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
        self.out = self.args.out_dir.resolve()
        # Never permit output below original work/review or production pages.
        for forbidden in (self.root / 'work', live, self.root / 'output/character_skills/review', self.pages):
            if self.out == forbidden.resolve() or forbidden.resolve() in self.out.parents:
                parser.error('输出必须位于旧 work／审查／页面输入之外的新目录')
        if self.out.exists():
            parser.error('输出目录已存在，拒绝覆盖：' + str(self.out))
        if metrics:
            if signature != '8cfbbd91c62486b13313948d915e486936ba104c461d8e25ae60b5783b2982f2':
                parser.error('此历史样例／指标生成器仅适用原初审版本 8cfbbd91…')
            if not self.args.comparison_result or not self.args.aux_dir:
                parser.error('指标必须提供本次完整对账结果与历史辅助材料目录')
            comparison = read_json(self.args.comparison_result)
            validate_comparison(comparison, self.binding, expected_count)
            self.comparison = comparison
            for name in ('b8_rows_all.jsonl', 'verify_promoted_chains.jsonl', 'verify_hints_report.json',
                         'characters.csv', 'yg_remaining_rows.json'):
                if not (self.args.aux_dir / name).is_file():
                    parser.error('缺少历史辅助材料：' + name)
        self.record = dict(status='RUNNING', script_name=self.script.name,
                           script=str(self.script), script_sha256=digest(self.script),
                           helper_sha256=digest(__file__), expected_cards=expected_count,
                           binding=self.binding, inputs=binding,
                           warning='输入完整性通过不等于历史审查结论已重验；签名须与历史审查对应。')
        self.out.mkdir(parents=True, exist_ok=False)
        self._write_record()

    def _write_record(self):
        # This file belongs to this newly created directory only.
        (self.out / 'run_record.json').write_text(json.dumps(self.record, ensure_ascii=False, indent=2), encoding='utf-8')

    def finish(self, ok, **details):
        self.record.update(status='PASS' if ok else 'FAIL', details=details)
        self._write_record()
        if not ok:
            raise SystemExit('FAIL: 历史复验条件未满足；见独立结果目录')
        print('PASS: 完整输入的本次比较完成；结果另存于', self.out)

    def stamp(self):
        return {k: self.record[k] for k in ('status', 'script_name', 'binding', 'expected_cards')}
