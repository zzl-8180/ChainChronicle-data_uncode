"""Build the full-unpack share bundle: tools package + results packages (no audio per request).

    .venv\\Scripts\\python.exe -B scripts/release/build_full_unpack_bundle.py

Writes output/share_bundle/20261016-full-unpack/:
  CC_full_unpack_tools_20261016.zip           portable decode/export pipeline + runtime materials + samples
  CC_full_unpack_results_data_20261016.zip    ledger, indexes, all JSON/TXT objects, master data (data5 decoded)
  CC_full_unpack_results_images_20261016.zip  all Texture2D PNG (stored, already compressed)
  CC_full_unpack_results_models_20261016.zip  all Mesh OBJ
  README.md, package_manifest.json

Audio WAV (17389 files) is EXCLUDED by explicit user request 2026-10-16; regenerable with the
tools package from the original cache. No phone re-collection involved.
"""
import hashlib
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'output/share_bundle/20261016-full-unpack'
FULL = ROOT / 'output/full_unpack'
V3 = ROOT / 'output/cache_full_20261015_v3'
INVENTORY = ROOT / 'output/cache_refresh_20261015/composite_inventory.jsonl'
DATE = '20261016'

TOOLS_NAME = f'CC_full_unpack_tools_{DATE}.zip'
DATA_NAME = f'CC_full_unpack_results_data_{DATE}.zip'
IMAGES_NAME = f'CC_full_unpack_results_images_{DATE}.zip'
MODELS_NAME = f'CC_full_unpack_results_models_{DATE}.zip'

TOOL_SCRIPTS = ['apk_certificate.py', 'protection_emulate.py', 'decode_data5.py',
                'full_unpack_probe.py', 'full_unpack_run.py', 'full_unpack_merge.py',
                'full_unpack_verify.py', 'full_unpack_finalize.py']
RUNTIME_FILES = [
    (ROOT / 'work/protection/nutils_loader_seed1.bin', 'nutils_loader_seed1.bin'),
    (ROOT / 'work/apk/lib/arm64-v8a/libcompatible.so', 'libcompatible.so'),
]
SAMPLES = [
    ('work/phone_20261015_full_02/files/Bundle/Card_Icon/cha_2d_icon_00001.bdl',
     'files/Bundle/Card_Icon/cha_2d_icon_00001.bdl'),
    ('work/phone_20261015_full_02/files/Bundle/BGM/BGMTable.bdl',
     'files/Bundle/BGM/BGMTable.bdl'),
    ('work/phone_20261015_full_02/files/Bundle/Motion/animal_l/el_attack_bite01.bdl',
     'files/Bundle/Motion/animal_l/el_attack_bite01.bdl'),
    ('work/phone_20261015_full_02/files/Bundle/Weapon/weapon001_body.bdl',
     'files/Bundle/Weapon/weapon001_body.bdl'),
]


def sha256_path(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


TOOLS_README = """# CC 缓存资源完整解包工具包（2026-10-16）

将游戏手机缓存中的 .bdl 容器解码（DecodeXorData → UnityFS）并导出对象：
Texture2D→PNG、AudioClip→WAV、TextAsset→TXT、Mesh→OBJ、AnimationClip/MonoBehaviour/其他→typetree JSON。
支持批量、断点续跑、抽样验证。本包自包含：含运行所需的恢复材料与 4 个冒烟测试样本。

## 环境

- Windows / Linux，Python 3.10+（已在 3.12.14 验证）
- `pip install -r requirements.txt`（UnityPy 1.25.4、pillow 12.3.0、unicorn 2.1.4）

## 冒烟测试（包根目录执行）

```bash
python scripts/full_unpack_run.py --inventory samples/inventory.jsonl --output out/full_unpack \
  --shards work/shards --native-image runtime/nutils_loader_seed1.bin \
  --protection runtime/libcompatible.so --cert-hex @runtime/cert.hex --workers 2
python scripts/full_unpack_merge.py --inventory samples/inventory.jsonl --output out/full_unpack \
  --shards work/shards --v3-decoded out/no_v3
python scripts/full_unpack_verify.py --inventory samples/inventory.jsonl --output out/full_unpack \
  --native-image runtime/nutils_loader_seed1.bin --protection runtime/libcompatible.so \
  --cert-hex @runtime/cert.hex --sample-per-category 1
```

预期：4/4 bdl 解码，validation.json 状态 PASS。产物在 out/full_unpack/objects/。

## 批量运行自己的缓存

1. 按 samples/inventory.jsonl 的格式准备清单：每行 JSON——`path`（files/Bundle/... 相对路径）、
   `bytes`、`archive`、`archive_member`、`work_file`（指向你本机上 bdl 的实际位置）、`phone_mtime`。
   其余字段可填 null/空串。
2. 同上三条命令，换成你的清单与输出目录。分片文件在 --shards 目录，中断后重跑自动跳过已完成项。
3. `--category NAME` 只跑一类；`--retry-list 文件` 强制重跑指定路径；`--workers N` 并发。

## runtime/ 材料说明（见 PROVENANCE.md）

- nutils_loader_seed1.bin：从游戏库恢复的原生镜像，DecodeXorData 所在；SHA256 见 PACKAGE_INFO.json。
- libcompatible.so：APK 内保护/重定位模型库（arm64-v8a），原生初始化必需。
- cert.hex：APK 签名证书（公开信息，任何 APK 持有者均可自行提取），用于原生初始化；不是账号凭据。
  若你持有 com.sega.chainchronicle 5.6.2 APK，可改用 `--apk 路径` 代替 --cert-hex。

## 限制

- 仅处理本快照观察到的 bdl 包装（XOR 头 + UnityFS）；其他格式需另行研究。
- AudioClip 导出为 PCM WAV（Vorbis 解码）；文本按 UTF-8 保留；typetree 字节值转 hex 字段。
- 字段语义不在本工具范围内；导出即结构化，解释另属分析任务。
"""


def stage_tools(staging):
    root = staging / f'CC_full_unpack_tools_{DATE}'
    (root / 'scripts').mkdir(parents=True)
    (root / 'runtime').mkdir()
    (root / 'samples').mkdir()
    for name in TOOL_SCRIPTS:
        shutil.copy2(ROOT / 'scripts' / name, root / 'scripts' / name)
    for src, dst in RUNTIME_FILES:
        shutil.copy2(src, root / 'runtime' / dst)
    shutil.copy2(ROOT / 'work/full_unpack/cert.hex', root / 'runtime' / 'cert.hex')
    (root / 'runtime' / 'PROVENANCE.md').write_text(
        '# runtime 材料来源\n\n'
        '- nutils_loader_seed1.bin：由 APK libnutils.so 经项目信号探针恢复的加载态镜像（ARM64），\n'
        '  DecodeXorData(rva 0x2097c) 所在。SHA256=3fd354b5baa099fc97df7ab33de8acd9bfdf1b8048e8a11650379e46ca756444\n'
        '- libcompatible.so：APK lib/arm64-v8a 原文件，保护/重定位模型。SHA256=79b6ae193625494b5facbc1c7eafa5bb16c4252dd9050fe10caee2393aa8767c\n'
        '- cert.hex：APK 签名证书 DER 的 hex（c7f59f410e836b6aaa9678b97e699a9a61062704ef8f463dab245d718f82bbb7 为证书 SHA256）。\n'
        '  公开信息，用于原生初始化等价物；不含任何账号/设备私有数据。\n',
        encoding='utf-8')
    for src_rel, inv_path in SAMPLES:
        shutil.copy2(ROOT / src_rel, root / 'samples' / Path(inv_path).name)
    rows = []
    for src_rel, inv_path in SAMPLES:
        src = ROOT / src_rel
        rows.append({'path': inv_path, 'bytes': src.stat().st_size, 'phone_mtime': 0,
                     'archive': 'samples', 'archive_member': inv_path,
                     'work_file': f'samples/{Path(inv_path).name}',
                     'basis': 'BUNDLED_SAMPLE', 'sha256_this_refresh': None, 'limit': ''})
    with (root / 'samples' / 'inventory.jsonl').open('w', encoding='utf-8') as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    (root / 'README.md').write_text(TOOLS_README, encoding='utf-8')
    (root / 'requirements.txt').write_text(
        'UnityPy==1.25.4\npillow==12.3.0\nunicorn==2.1.4\n', encoding='ascii')
    info = {
        'package': f'CC_full_unpack_tools_{DATE}', 'kind': 'tools',
        'created': DATE, 'python_verified': '3.12.14',
        'scripts': {n: sha256_path(ROOT / 'scripts' / n) for n in TOOL_SCRIPTS},
        'runtime': {dst: sha256_path(src) for src, dst in RUNTIME_FILES},
        'cert_hex_file_sha256': sha256_path(ROOT / 'work/full_unpack/cert.hex'),
        'samples': len(SAMPLES),
    }
    (root / 'PACKAGE_INFO.json').write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return root


def zip_dir(src_root, zip_path, arc_prefix):
    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for dirpath, _, files in os.walk(src_root):
            for f in files:
                full = Path(dirpath) / f
                arc = f'{arc_prefix}/{full.relative_to(src_root).as_posix()}'
                zf.write(full, arc)
                count += 1
    return count


def add_entries(zf, entries, stats, compression=zipfile.ZIP_DEFLATED, level=6):
    for full, arc in entries:
        zf.write(full, arc, compression)
        stats['files'] += 1
        stats['bytes'] += full.stat().st_size
        if stats['files'] % 50000 == 0:
            print(f'    ... {stats["files"]} files', flush=True)


def build_results():
    """Walk output/full_unpack once; write data/images/models zips (skip .wav per user request)."""
    objects = FULL / 'objects'
    packs = {
        'data': zipfile.ZipFile(RELEASE / DATA_NAME, 'w', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True),
        'images': zipfile.ZipFile(RELEASE / IMAGES_NAME, 'w', zipfile.ZIP_STORED, allowZip64=True),
        'models': zipfile.ZipFile(RELEASE / MODELS_NAME, 'w', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True),
    }
    stats = {k: {'files': 0, 'bytes': 0} for k in packs}
    skipped_wav = {'files': 0, 'bytes': 0}
    try:
        # 根文档进 data 包
        root_docs = [f for f in FULL.iterdir() if f.is_file()]
        add_entries(packs['data'], [(f, f'full_unpack/{f.name}') for f in sorted(root_docs)], stats['data'])
        for dirpath, _, files in os.walk(objects):
            for f in files:
                full = Path(dirpath) / f
                ext = full.suffix.lower()
                arc = f'full_unpack/objects/{full.relative_to(objects).as_posix()}'
                if ext == '.wav':
                    skipped_wav['files'] += 1
                    skipped_wav['bytes'] += full.stat().st_size
                elif ext == '.png':
                    add_entries(packs['images'], [(full, arc)], stats['images'])
                elif ext == '.obj':
                    add_entries(packs['models'], [(full, arc)], stats['models'])
                else:
                    add_entries(packs['data'], [(full, arc)], stats['data'])
        # 主表数据（77 data5 已解码 JSON 及视图/分析）进 data 包
        master = []
        for f in sorted((V3 / 'decoded').glob('*.json.raw')):
            master.append((f, f'master_data/decoded/{f.name}'))
        for name in ('records.jsonl', 'tables.csv', 'README.md', 'manifest.json'):
            f = V3 / name
            if f.is_file():
                master.append((f, f'master_data/{name}'))
        for f in sorted((V3 / 'analysis').glob('*')):
            if f.is_file():
                master.append((f, f'master_data/analysis/{f.name}'))
        add_entries(packs['data'], master, stats['data'])
    finally:
        for zf in packs.values():
            zf.close()
    return stats, skipped_wav


def main():
    t0 = time.time()
    RELEASE.mkdir(parents=True, exist_ok=True)
    staging = RELEASE / 'staging'
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    print('[1/3] tools package', flush=True)
    tools_root = stage_tools(staging)
    tools_count = zip_dir(tools_root, RELEASE / TOOLS_NAME, f'CC_full_unpack_tools_{DATE}')
    shutil.rmtree(staging)
    print(f'  tools: {tools_count} files', flush=True)

    print('[2/3] results packages (audio excluded by request)', flush=True)
    stats, skipped_wav = build_results()
    for k, v in stats.items():
        print(f'  {k}: {v["files"]} files, {v["bytes"]/1048576:.0f} MiB raw', flush=True)
    print(f'  skipped wav: {skipped_wav["files"]} files, {skipped_wav["bytes"]/1048576:.0f} MiB', flush=True)

    print('[3/3] manifest', flush=True)
    coverage = json.loads((FULL / 'coverage.json').read_text(encoding='utf-8'))
    manifest = {
        'release': '20261016-full-unpack',
        'created': time.strftime('%Y-%m-%d %H:%M:%S'),
        'input': {
            'composite_inventory': 'output/cache_refresh_20261015/composite_inventory.jsonl',
            'composite_inventory_sha256': sha256_path(INVENTORY),
            'archives': ['raw/phone_20261015_full_02/external_cache.tar',
                         'raw/phone_20261015_refresh_02/external_cache.tar'],
            'scope': '68993 phone-cache files (68655 bdl + 77 data5 + 261 other); not whole-game coverage',
        },
        'packages': {
            TOOLS_NAME: {'kind': 'tools', 'files_inside': tools_count,
                         'bytes': (RELEASE / TOOLS_NAME).stat().st_size,
                         'sha256': sha256_path(RELEASE / TOOLS_NAME),
                         'contents': 'scripts, runtime recovery materials, smoke-test samples, README, requirements'},
            DATA_NAME: {'kind': 'results-data', 'files_inside': stats['data']['files'],
                        'raw_bytes': stats['data']['bytes'],
                        'bytes': (RELEASE / DATA_NAME).stat().st_size,
                        'sha256': sha256_path(RELEASE / DATA_NAME),
                        'contents': 'full_unpack root docs (ledger/coverage/validation/manifest/cid_index/README), '
                                    'all objects JSON+TXT, master_data (77 decoded data5 JSON + views + analysis)'},
            IMAGES_NAME: {'kind': 'results-images', 'files_inside': stats['images']['files'],
                          'raw_bytes': stats['images']['bytes'],
                          'bytes': (RELEASE / IMAGES_NAME).stat().st_size,
                          'sha256': sha256_path(RELEASE / IMAGES_NAME),
                          'contents': 'all 73490 Texture2D PNG at full_unpack/objects/**; stored (already compressed)'},
            MODELS_NAME: {'kind': 'results-models', 'files_inside': stats['models']['files'],
                          'raw_bytes': stats['models']['bytes'],
                          'bytes': (RELEASE / MODELS_NAME).stat().st_size,
                          'sha256': sha256_path(RELEASE / MODELS_NAME),
                          'contents': 'all 50051 Mesh OBJ at full_unpack/objects/**'},
        },
        'exclusions': {
            'audio_wav': {'files': skipped_wav['files'], 'raw_bytes': skipped_wav['bytes'],
                          'reason': 'EXCLUDED BY USER REQUEST 2026-10-16 (不要音频). Not a decode failure: '
                                    'all 17389 AudioClips decoded ok in the source run; regenerate WAV with the tools package.'},
            'non_game_files': 'UnityShaderCache 206 / ad-SDK 34 / macOS junk 17 / il2cpp engine 4 — see ledger.jsonl reasons',
            'apk_embedded_media': 'APK-side media not bulk-exported (index exists in project); out of this release scope',
        },
        'source_coverage': coverage,
        'code_versions': {f'scripts/{n}': sha256_path(ROOT / 'scripts' / n) for n in TOOL_SCRIPTS} |
                         {'scripts/release/build_full_unpack_bundle.py': sha256_path(Path(__file__))},
        'usage': 'Extract all results packages into the same directory to reconstruct full_unpack/ + master_data/. '
                 'objects_index.json files reference .wav paths that are not included (audio excluded).',
    }
    (RELEASE / 'package_manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'done in {(time.time()-t0)/60:.1f} min', flush=True)


if __name__ == '__main__':
    main()
