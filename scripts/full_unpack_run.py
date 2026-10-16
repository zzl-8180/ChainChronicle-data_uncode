"""Full unpack of acquired .bdl cache: decode (DecodeXorData) -> UnityFS -> export objects.

Usage (from project root, existing .venv):
    .venv\\Scripts\\python.exe -B scripts/full_unpack_run.py [--workers 8] [--limit N] [--category NAME]

- Input: output/cache_refresh_20261015/composite_inventory.jsonl (bdl rows only).
- Output root: output/full_unpack/ (objects/, ledger_bdl.jsonl, manifest at end).
- Resume: per-worker shard files in work/full_unpack/shards/ record completed paths;
  reruns skip inputs already marked ok with matching size.
- Originals are read-only. No APK/data5/media reinterpretation beyond object export.
"""
import argparse
import hashlib
import io
import json
import math
import os
import re
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INVENTORY = Path('output/cache_refresh_20261015/composite_inventory.jsonl')
OUTPUT = Path('output/full_unpack')
SHARDS = Path('work/full_unpack/shards')

_DECODER = None
_DECODER_KW = {}


def configure_decoder(native_image=None, apk=None, cert_hex=None, protection=None):
    """Set NativeDecoder init kwargs for this process (worker-safe: passed via task args)."""
    global _DECODER_KW, _DECODER
    kw = {}
    if native_image is not None:
        kw['image'] = Path(native_image)
    if protection is not None:
        kw['protection'] = Path(protection)
    if cert_hex is not None:
        kw['cert_hex'] = cert_hex
    elif apk is not None:
        kw['apk'] = Path(apk)
    _DECODER_KW = kw
    _DECODER = None


def get_decoder():
    global _DECODER
    if _DECODER is None:
        from decode_data5 import NativeDecoder
        _DECODER = NativeDecoder(**_DECODER_KW)
    return _DECODER


def sanitize(value):
    """Make typetree values JSON-safe: bytes -> hex box, non-finite float -> tagged box."""
    if isinstance(value, dict):
        return {str(k): sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(v) for v in value]
    if isinstance(value, (bytes, bytearray, memoryview)):
        b = bytes(value)
        if len(b) > 262144:
            return {'__bytes_hex_truncated__': b[:4096].hex(), 'full_length': len(b),
                    'sha256': hashlib.sha256(b).hexdigest()}
        return {'__bytes_hex__': b.hex()}
    if isinstance(value, float) and not math.isfinite(value):
        return {'__non_finite_float__': 'inf' if value > 0 else '-inf' if value < 0 else 'nan'}
    return value


def safe_name(name):
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', str(name))
    return name.strip().strip('.') or '(unnamed)'


def export_bundle(work_file, rel_path, expected_size, out_dir):
    """Decode one bdl and export its objects. Returns a ledger record dict."""
    record = {'path': rel_path, 'size': expected_size}
    raw = Path(work_file).read_bytes()
    if len(raw) != expected_size:
        record.update(status='error', error_or_unknown_reason=f'size mismatch: {len(raw)} != {expected_size}')
        return record
    record['source_sha256'] = hashlib.sha256(raw).hexdigest()

    decoder = get_decoder()
    watermark = decoder.e.heap
    try:
        pointer = decoder.e.allocate(len(raw), raw)
        accepted = decoder.call(0x2097c, pointer, len(raw))
        converted = bytes(decoder.e.uc.mem_read(pointer, len(raw)))
    finally:
        decoder.e.heap = watermark
    if accepted != 1 or not converted.startswith(b'UnityFS\0'):
        record.update(status='error', error_or_unknown_reason='DecodeXorData rejected or no UnityFS signature',
                      accepted=accepted, header_hex=converted[:16].hex())
        return record
    tail_ok = converted[256:] == raw[256:] if len(raw) > 256 else True
    record['decoded_sha256'] = hashlib.sha256(converted).hexdigest()
    record['decoded_bytes'] = len(converted)
    record['tail_unchanged'] = tail_ok

    import UnityPy  # per-process import
    try:
        env = UnityPy.load(converted)
    except Exception as exc:
        record.update(status='error', error_or_unknown_reason=f'UnityPy load: {type(exc).__name__}: {exc}')
        return record

    objects = list(env.objects)
    out_dir.mkdir(parents=True, exist_ok=True)
    index = {'bundle': rel_path, 'decoded_sha256': record['decoded_sha256'], 'objects': []}
    by_type = {}
    for o in objects:
        by_type.setdefault(o.type.name, []).append(o)
    record['object_types'] = {t: len(v) for t, v in sorted(by_type.items())}
    record['objects_exported'] = 0
    errors = []

    # 全包统一分配文件名：先按类型定扩展名，再跨类型查冲突，冲突加 path_id 后缀
    EXT = {'Texture2D': '.png', 'AudioClip': '.wav', 'TextAsset': '.txt', 'Mesh': '.obj',
           'AnimationClip': '.anim.json', 'MonoBehaviour': '.mono.json', 'AssetBundle': '.bundle.json'}
    planned = []  # (path_id, base, ext)
    for o in objects:
        otype = o.type.name
        ext = EXT.get(otype, '.typetree.json')
        planned.append((o.path_id, safe_name(o.peek_name() or ''), ext))
    name_count = {}
    for _, base, ext in planned:
        # Windows 大小写不敏感：按 lower 归并计数，冲突一律加 path_id 后缀
        name_count[(base.lower(), ext.lower())] = name_count.get((base.lower(), ext.lower()), 0) + 1
    files = {}
    for path_id, base, ext in planned:
        if name_count[(base.lower(), ext.lower())] > 1:
            files[path_id] = f'{base}_{path_id}{ext}'
        else:
            files[path_id] = f'{base}{ext}'
    # 跨类型同文件名（不同扩展名不冲突；同扩展名已按上处理）

    for otype, members in sorted(by_type.items()):

        for o in members:
            entry = {'type': otype, 'path_id': o.path_id, 'name': o.peek_name() or '',
                     'byte_size': o.byte_size}
            try:
                if otype == 'AssetBundle':
                    data = o.read_typetree()
                    fn = files[o.path_id]
                    (out_dir / fn).write_text(json.dumps(sanitize(data), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
                    entry['file'] = fn
                    entry['container'] = [c[0] for c in data.get('m_Container', [])]
                elif otype == 'Texture2D':
                    tex = o.read()
                    fn = files[o.path_id]
                    img = tex.image
                    img.save(out_dir / fn)
                    entry['file'] = fn
                    fmt = tex.m_TextureFormat
                    try:
                        from UnityPy.enums import TextureFormat
                        fmt_name = TextureFormat(int(fmt)).name
                    except (ValueError, ImportError):
                        fmt_name = f'UNKNOWN_{int(fmt)}'
                    entry['texture'] = {
                        'width': tex.m_Width, 'height': tex.m_Height,
                        'format': int(fmt),
                        'format_name': fmt_name,
                        'mip_count': getattr(tex, 'm_MipCount', None),
                        'image_mode': img.mode,
                        'stream': {'path': tex.m_StreamData.path, 'offset': tex.m_StreamData.offset,
                                   'size': tex.m_StreamData.size} if getattr(tex, 'm_StreamData', None) else None,
                    }
                elif otype == 'AudioClip':
                    clip = o.read()
                    tt = o.read_typetree()
                    fn = files[o.path_id]
                    saved = []
                    for sample_name, data in clip.samples.items():
                        target = out_dir / fn
                        if len(clip.samples) > 1:
                            target = out_dir / (fn[:-4] + '_' + safe_name(Path(sample_name).stem) + '.wav')
                        target.write_bytes(data)
                        saved.append({'file': target.name, 'bytes': len(data)})
                    if len(saved) == 1:
                        entry['file'] = saved[0]['file']
                    elif not saved:
                        entry['audio_empty'] = 'UnityPy returned no decoded samples; raw stream kept in bundle only'
                    entry['audio'] = {
                        'saved': saved,
                        'compression_format': tt.get('m_CompressionFormat'),
                        'frequency': tt.get('m_Frequency'), 'channels': tt.get('m_Channels'),
                        'bits_per_sample': tt.get('m_BitsPerSample'), 'length_seconds': tt.get('m_Length'),
                        'note': 'UnityPy decodes the Unity stream to PCM WAV; compression_format 1=Vorbis in Unity enum.'}
                elif otype == 'TextAsset':
                    script = o.read().m_Script
                    fn = files[o.path_id]
                    if isinstance(script, str):
                        (out_dir / fn).write_text(script, encoding='utf-8')
                        entry['file'] = fn
                        entry['text'] = {'encoding': 'utf-8', 'chars': len(script),
                                         'bom': script.startswith('﻿')}
                    else:
                        data = bytes(script)
                        fn = f'{safe_name(entry["name"])}_{o.path_id}.bin'
                        (out_dir / fn).write_bytes(data)
                        entry['file'] = fn
                        entry['text'] = {'encoding': 'binary', 'bytes': len(data)}
                elif otype == 'Mesh':
                    mesh = o.read()
                    fn = files[o.path_id]
                    (out_dir / fn).write_text(mesh.export(), encoding='utf-8')
                    entry['file'] = fn
                    entry['mesh'] = {'export': 'obj_text', 'name': mesh.m_Name}
                elif otype in ('AnimationClip', 'MonoBehaviour'):
                    fn = files[o.path_id]
                    try:
                        data = o.read_typetree()
                        (out_dir / fn).write_text(json.dumps(sanitize(data), ensure_ascii=False) + '\n', encoding='utf-8')
                        entry['file'] = fn
                    except Exception as exc:
                        raw_bytes = o.get_raw_data()
                        fn = f'{safe_name(entry["name"])}_{o.path_id}.bin'
                        (out_dir / fn).write_bytes(raw_bytes)
                        entry['file'] = fn
                        entry['typetree_error'] = f'{type(exc).__name__}: {exc}'
                        entry['raw_bytes_saved'] = len(raw_bytes)
                else:
                    fn = files[o.path_id]
                    try:
                        data = o.read_typetree()
                        (out_dir / fn).write_text(json.dumps(sanitize(data), ensure_ascii=False) + '\n', encoding='utf-8')
                        entry['file'] = fn
                    except Exception as exc:
                        entry['typetree_error'] = f'{type(exc).__name__}: {exc}'
                        try:
                            raw_bytes = o.get_raw_data()
                            fn = f'{safe_name(entry["name"])}_{o.path_id}.bin'
                            (out_dir / fn).write_bytes(raw_bytes)
                            entry['file'] = fn
                            entry['raw_bytes_saved'] = len(raw_bytes)
                        except Exception as exc2:
                            entry['raw_save_error'] = f'{type(exc2).__name__}: {exc2}'
                            errors.append(f'{otype}/{entry["name"]}: {entry["typetree_error"]}')
                record['objects_exported'] += 1
            except Exception as exc:
                entry['export_error'] = f'{type(exc).__name__}: {exc}'
                errors.append(f'{otype}/{entry.get("name")}: {entry["export_error"]}')
                try:
                    raw_bytes = o.get_raw_data()
                    fn = f'{safe_name(entry["name"])}_{o.path_id}.bin'
                    (out_dir / fn).write_bytes(raw_bytes)
                    entry['file'] = fn
                    entry['raw_bytes_saved'] = len(raw_bytes)
                except Exception:
                    pass
            index['objects'].append(entry)

    (out_dir / 'objects_index.json').write_text(
        json.dumps(index, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    rel_out = out_dir.relative_to(OUTPUT).as_posix()
    if errors:
        record.update(status='partial', error_or_unknown_reason='; '.join(errors[:5]),
                      error_count=len(errors), output_path=rel_out)
    else:
        record.update(status='ok', output_path=rel_out, error_or_unknown_reason=None)
    return record


def process_chunk(args):
    """Worker: process one deterministic chunk; skip files already done; append results."""
    chunk_id, chunk, done_paths, config = args
    global OUTPUT, SHARDS
    if config:
        # spawn worker 不继承父进程模块全局：输出/分片/解码器配置全部经任务参数传入
        if config.get('output'):
            OUTPUT = Path(config['output'])
        if config.get('shards'):
            SHARDS = Path(config['shards'])
        configure_decoder(native_image=config.get('native_image'), apk=config.get('apk'),
                          cert_hex=config.get('cert_hex'), protection=config.get('protection'))
    shard = SHARDS / f'chunk_{chunk_id:06d}.jsonl'
    # 若上次中断留下无换行的截断行，先补换行，避免新旧记录粘连
    if shard.exists() and shard.stat().st_size:
        with shard.open('rb+') as fh:
            fh.seek(-1, 2)
            if fh.read(1) != b'\n':
                fh.write(b'\n')
    done = 0
    with shard.open('a', encoding='utf-8') as fh:
        for work_file, rel_path, size in chunk:
            if rel_path in done_paths:
                continue
            rel = Path(rel_path)
            # 定位路径中的 Bundle 分量：files/Bundle/<cat>/[sub/]name.bdl -> objects/<cat>/[sub/]name
            parts = rel.parts
            if 'Bundle' not in parts:
                rec = {'path': rel_path, 'size': size, 'status': 'error',
                       'error_or_unknown_reason': "inventory path lacks 'Bundle' component; expected files/Bundle/<category>/... (see README bdl section)"}
                fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
                fh.flush()
                done += 1
                continue
            out_rel = Path('objects', *parts[parts.index('Bundle')+1:]).with_suffix('')
            out_dir = OUTPUT / out_rel
            try:
                rec = export_bundle(work_file, rel_path, size, out_dir)
            except Exception as exc:
                rec = {'path': rel_path, 'size': size, 'status': 'error',
                       'error_or_unknown_reason': f'worker: {type(exc).__name__}: {exc}'}
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            fh.flush()
            done += 1
    return chunk_id, done


def load_progress():
    """Read all shard files -> {path: (size, status)}."""
    progress = {}
    if SHARDS.is_dir():
        for shard in sorted(SHARDS.glob('chunk_*.jsonl')):
            for line in shard.open(encoding='utf-8'):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue  # 截断行（中断时）跳过，重跑该文件
                progress[rec['path']] = (rec.get('size'), rec.get('status'))
    return progress


def main():
    global OUTPUT, SHARDS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 4) - 2))
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--category', default='')
    parser.add_argument('--inventory', type=Path, default=INVENTORY)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--shards', type=Path, default=SHARDS)
    parser.add_argument('--native-image', default=None, help='recovered NUtils image (default: project path)')
    parser.add_argument('--protection', default=None, help='libcompatible.so from APK (default: project path)')
    parser.add_argument('--apk', default=None, help='APK for signing certificate (default: project path)')
    parser.add_argument('--cert-hex', default=None,
                        help='hex of APK signing certificate, or @file containing hex; overrides --apk')
    parser.add_argument('--retry-list', type=Path, default=None,
                        help='text file of bdl paths to force-reprocess (ignores progress)')
    args = parser.parse_args()

    OUTPUT = args.output
    SHARDS = args.shards
    cert_hex = args.cert_hex
    if cert_hex and cert_hex.startswith('@'):
        cert_hex = Path(cert_hex[1:]).read_text(encoding='ascii').strip()
    config = {'output': str(OUTPUT), 'shards': str(SHARDS), 'protection': args.protection,
              'native_image': args.native_image, 'apk': args.apk, 'cert_hex': cert_hex}
    configure_decoder(native_image=args.native_image, apk=args.apk, cert_hex=cert_hex,
                      protection=args.protection)
    rows = [json.loads(line) for line in args.inventory.open(encoding='utf-8')]
    bdl = [r for r in rows if r['path'].endswith('.bdl')]
    if args.category:
        bdl = [r for r in bdl if r['path'].split('/')[2] == args.category]
    bdl.sort(key=lambda r: r['path'])

    progress = load_progress()
    done_paths = {p for p, (size, status) in progress.items() if status in ('ok', 'partial')}
    if args.retry_list:
        retry = {line.strip() for line in args.retry_list.open(encoding='utf-8') if line.strip()}
        done_paths -= retry
    # 注意：done_paths 只按路径跳过；尺寸变化时不跳过（尺寸在变体名单另核）
    todo = [r for r in bdl if r['path'] not in done_paths]
    skipped = len(bdl) - len(todo)
    if args.limit:
        todo = todo[:args.limit]
    print(f'total bdl: {len(bdl)}, already done: {skipped}, this run: {len(todo)}, workers: {args.workers}')
    if not todo:
        print('nothing to do')
        return

    SHARDS.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    # 确定性分块：基于当前过滤后的完整排序清单，跨轮一致，chunk 文件可累积续跑
    tasks = [(r['work_file'], r['path'], r['bytes']) for r in bdl]
    per = math.ceil(len(tasks) / (args.workers * 8))
    work_items = []
    for i in range(0, len(tasks), per):
        chunk = tasks[i:i + per]
        if any(rel not in done_paths for _, rel, _ in chunk):
            work_items.append((i // per, chunk, done_paths, config))
    if args.limit:
        work_items = work_items[:max(1, math.ceil(args.limit / per))]

    t0 = time.time()
    done = 0
    if args.workers <= 1:
        for item in work_items:
            _, n = process_chunk(item)
            done += n
            print(f'progress {done}/{len(tasks)} ({done/max(1,time.time()-t0):.1f} f/s)', flush=True)
    else:
        import multiprocessing as mp
        with mp.Pool(args.workers) as pool:
            for _, n in pool.imap_unordered(process_chunk, work_items):
                done += n
                print(f'progress {done}/{len(tasks)} ({done/max(1,time.time()-t0):.1f} f/s)', flush=True)
    dt = time.time() - t0
    print(f'run finished: {done} files in {dt/60:.1f} min')
    print('shard results in', SHARDS, '- run merge step to build ledger/manifest')


if __name__ == '__main__':
    main()
