"""Build the layered delivery bundle (AGENTS.md §8.2): tools (A), research results (B), media manifest (C).

    .venv\\Scripts\\python.exe -B scripts/release/build_delivery_bundle.py

Writes output/share_bundle/20261016-delivery/:
  CC_delivery_tools_20261016.zip       A: complete source from `git archive HEAD` (scripts/docs/README/deps)
  CC_delivery_research_20261016.zip    B: v3 master data, APK master, field dictionaries, skill
                                       interpretations, evidences, review reports, query/display products
  media_manifest.json                  C: full_unpack media inventory, rebuild commands, optional split plan
  package_manifest.json                machine-readable master manifest (versions, scope, counts, sizes,
                                       SHA-256, exclusions, usage, dependencies)
  README.md                            unified release notes

Local build only; no upload. Media (20GB) is NOT copied — C ships manifest + rebuild method.
"""
import hashlib
import json
import subprocess
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'output/share_bundle/20261016-delivery'
DATE = '20261016'

B_INCLUDE = [
    'output/cache_full_20261015_v3',      # 核心：77 份完整解码 JSON + records.jsonl + 字段字典 + 分析 + 验证
    'output/base_master',                 # APK 内置主表 ChronicleArchiveData
    'output/card_comparison_cid30236',    # 逐描述技能解释 101 项 + 77 条合并规则 + 证据 + 对照页
    'output/ordinary_effects',            # 7 个普通效果类型的限定证据
    'output/boss_chain',                  # 必杀 type105/112/13 规则与证据
    'output/boss_heal',                   # 治疗 type27/13 规则与证据
    'output/sample',                      # 阶段D样本链
    'output/phase_d',                     # 阶段D安装/来源证据
    'output/validation',                  # data5/phase_a 验证报告
    'output/审查报告',                     # 历史独立审查报告
    'output/20261016-reproducibility-audit',  # 可复现性独立审查
    'output/card_images',                 # cid30236 图片绑定证据
    'output/char_roster',                 # 全角色名册展示成果
    'output/structured',                  # 阶段A结构化候选证据
    'output/cache_full_latest.json',      # 当前主表指针
    'output/cache_refresh_latest.json',   # 补采指针
]
B_EXCLUDE_NOTES = [
    'output/export（阶段E构建，1.40GB）：较早输入（11 个 data5）的稳定交付，主表数据已被 v3＋base_master 覆盖；本地保留，需要时可按清单另发',
    'output/field_guide（0.75GB）：绑定旧快照的字段指南；当前字段字典在 v3/analysis 与 card_comparison/boss_* 内',
    'output/full_unpack（20.24GB 媒体）：见 C 包 media_manifest.json 的清单与重建方法',
    'output/unity、decoded、protection、native、il2cpp、apk、phone_*、cache_refresh_20261015：可由工具包从输入重新生成的中间/对账产物，本地保留',
    'output/cache_full_20261015（v1）、cache_full_20261015_v2、single、share_bundle 既有 ZIP：历史版本，保留不重复分发',
]
STORE_ONLY = ('.png', '.zip', '.wav', '.jpg', '.jpeg', '.gz')

# P1-1（用户裁决 2026-10-17）：B 包不携带游戏衍生媒体与第三方截图。
# 结构化数据与研究证据全部保留；被排除项逐条登记在 package_manifest.json。
B_EXCLUDE_PATHS = (  # 精确文件或目录前缀
    'output/char_roster/icons/',
    'output/char_roster/index.html',
    'output/card_comparison_cid30236/reference.png',
    'output/card_comparison_cid30236/index.html',
)
B_EXCLUDE_MEDIA_IN = {  # 这些目录内按扩展名排除（游戏美术/资源封装）
    'output/card_images/': {'.png', '.unityfs'},
}


def b_excluded(rel):
    for prefix in B_EXCLUDE_PATHS:
        if rel == prefix or rel.startswith(prefix):
            return True
    for prefix, exts in B_EXCLUDE_MEDIA_IN.items():
        if rel.startswith(prefix) and Path(rel).suffix.lower() in exts:
            return True
    return False


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_tools_zip(dest):
    """A: git archive HEAD -> zip; return (file_entries, head)."""
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    archive = RELEASE / '_tools_head.zip'
    subprocess.check_call(['git', 'archive', '--format=zip', 'HEAD', '-o', str(archive)], cwd=ROOT)
    entries = []
    with zipfile.ZipFile(archive) as zin, zipfile.ZipFile(dest, 'w') as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            entries.append({'path': info.filename, 'bytes': len(data), 'sha256': sha_bytes(data)})
            zout.writestr(info.filename, data)
    archive.unlink()
    return entries, head


def build_research_zip(dest):
    """B: walk B_INCLUDE; per-file SHA-256; store already-compressed, deflate the rest.

    Returns (entries, excluded): excluded lists media items kept out per P1-1 ruling.
    """
    entries, excluded = [], []
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
        for item in B_INCLUDE:
            base = ROOT / item
            if base.is_file():
                files = [base]
            else:
                files = sorted(p for p in base.rglob('*') if p.is_file())
            for path in files:
                rel = path.relative_to(ROOT).as_posix()
                if b_excluded(rel):
                    excluded.append({'path': rel, 'bytes': path.stat().st_size})
                    continue
                data = path.read_bytes()
                entries.append({'path': rel, 'bytes': len(data), 'sha256': sha_bytes(data)})
                if path.suffix.lower() in STORE_ONLY:
                    zout.writestr(zipfile.ZipInfo(rel), data, compress_type=zipfile.ZIP_STORED)
                else:
                    zout.writestr(rel, data)
    return entries, excluded


def build_media_manifest():
    """C: inventory from ledger + object stats; per-category media dir sizes; rebuild commands."""
    full = ROOT / 'output/full_unpack'
    ledger_rows = [json.loads(line) for line in (full / 'ledger.jsonl').open(encoding='utf-8')]
    coverage = json.loads((full / 'coverage.json').read_text(encoding='utf-8'))
    categories = {}
    for row in ledger_rows:
        if not row['path'].endswith('.bdl'):
            continue
        cat = row['path'].split('/')[2]
        c = categories.setdefault(cat, {'bdl_files': 0, 'input_bytes': 0, 'status': {}})
        c['bdl_files'] += 1
        c['input_bytes'] += row['size']
        st = row['processing_status']
        c['status'][st] = c['status'].get(st, 0) + 1
    for cat_dir in sorted((full / 'objects').iterdir()):
        if not cat_dir.is_dir():
            continue
        total = sum(p.stat().st_size for p in cat_dir.rglob('*') if p.is_file())
        categories.setdefault(cat_dir.name, {'bdl_files': 0, 'input_bytes': 0, 'status': {}})
        categories[cat_dir.name]['exported_bytes'] = total
    return {
        'package': 'C. 大型媒体资源包（清单＋重建方法；本轮未复制媒体文件）',
        'source_output': 'output/full_unpack/（目录总量 903,402 个文件 / 21,727,783,139 B ≈ 20.24 GiB；'
                       '其中 objects/ 下 903,396 个导出文件；56 类 exported_bytes 合计 ≈20.18 GiB 仅导出媒体）',
        'input_scope': 'composite_inventory 68,993 个缓存文件中的 68,655 个 bdl（100% 解码展开成功）；'
                       '77 个 data5 在 B 包；261 个其他文件分类排除（理由见 output/full_unpack/ledger.jsonl）',
        'object_stats': coverage['bdl_object_types'],
        'bdl_objects_exported': coverage['bdl_objects_exported'],
        'categories': categories,
        'rebuild': {
            'prerequisites': 'A 包工具＋兼容 APK＋游戏缓存（或既有归档）；先生成原生镜像（README §4 A1—A3）',
            'inventory_format': 'JSONL：{"path":"files/Bundle/<类别>/.../<名>.bdl","bytes":<大小>,"work_file":"<本地路径>"}',
            'commands': [
                'scripts/full_unpack_run.py --inventory <清单> --output <输出目录> --workers 8（分片续跑）',
                'scripts/full_unpack_merge.py --inventory <清单> --output <输出目录>',
                'scripts/full_unpack_verify.py --inventory <清单> --output <输出目录>',
                'scripts/full_unpack_finalize.py --inventory <清单> --output <输出目录>',
            ],
            'resume': 'work/full_unpack/shards/ 记录已完成路径，重跑自动跳过；输入未变不重新解码',
        },
        'optional_split_plan': [
            '按 output/full_unpack/objects/ 的 56 个类别目录拆分（categories 字段给出各类 bdl 数与导出字节数）',
            '或按对象类型：Texture2D PNG 73,490／AudioClip WAV 17,389／Mesh OBJ 50,051／TextAsset 2,845／typetree JSON',
            '单包控制在当时 GitHub Release 附件限制内；每包附本清单相应子集与 SHA-256',
        ],
        'license_boundary': '解包媒体为 SEGA 游戏资源，公开分发前必须检查版权与许可；默认仅本地或授权范围使用',
    }


def main():
    t0 = time.time()
    RELEASE.mkdir(parents=True, exist_ok=False)
    tools_zip = RELEASE / f'CC_delivery_tools_{DATE}.zip'
    research_zip = RELEASE / f'CC_delivery_research_{DATE}.zip'

    tools_entries, head = build_tools_zip(tools_zip)
    research_entries, media_excluded = build_research_zip(research_zip)
    media = build_media_manifest()
    (RELEASE / 'media_manifest.json').write_text(json.dumps(media, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # 自校验：zip 可打开、条目数与清单一致、CRC 抽检
    checks = []
    for zpath, entries in ((tools_zip, tools_entries), (research_zip, research_entries)):
        with zipfile.ZipFile(zpath) as z:
            names = z.namelist()
            ok_count = len(names) == len(entries)
            bad = z.testzip()
        checks.append({'zip': zpath.name, 'entries': len(entries), 'count_match': ok_count,
                       'crc_selftest': 'PASS' if bad is None else f'FAIL: {bad}'})
        assert ok_count and bad is None
    # P1-1 核验：被排除路径不得出现在 B 包
    leaked = [e['path'] for e in media_excluded if any(e['path'] == x['path'] for x in research_entries)]
    assert not leaked, f'excluded media leaked into B zip: {leaked[:3]}'
    excl_summary = {
        'ruling': 'P1-1 用户裁决（2026-10-17）：B 包不携带游戏衍生媒体与第三方截图；结构化数据与研究证据全部保留',
        'excluded_files': len(media_excluded),
        'excluded_bytes': sum(e['bytes'] for e in media_excluded),
        'items': [
            {'scope': 'output/char_roster/icons/**（bdl 解包头像 2,656 PNG）与 output/char_roster/index.html（内嵌同批头像的自包含画廊）',
             'note': '名册 data/（9,169 cid 合并成品）、README（含日期证据链结论）、manifest、verification 已全部保留'},
            {'scope': 'output/card_images/cid30236/** 中的 5 个 .unityfs 与 7 个 .png（卡面等游戏美术）',
             'note': 'binding_evidence.json、manifest、反汇编 method_*.txt、followup 研究证据全部保留'},
            {'scope': 'output/card_comparison_cid30236/reference.png（用户提供的外部数据库截图，权限待确认）与 index.html（内嵌该截图）',
             'note': '101 项逐描述解释、field_dictionary、comparison/evidence CSV/JSON 全部保留'},
        ],
        'rebuild_note': '本地 output/ 完整保留；展示页与可视媒体可按 media_manifest.json 的 C 清单重建媒体后本地重建',
        'detail': media_excluded,
    }

    manifest = {
        'release_id': '20261016-delivery',
        'created': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'git_head': head,
        'packages': {
            'A_tools': {
                'file': tools_zip.name, 'bytes': tools_zip.stat().st_size,
                'sha256': sha_file(tools_zip), 'entries': len(tools_entries),
                'scope': '与 git HEAD 逐文件内容一致的全部跟踪文件（zip 内为 CRLF 行尾）：scripts/（含 full_unpack 管线与 release/）、docs/、README.md、requirements-lock.txt、AGENTS.md 等',
                'install': 'Python 3.12 + pip install -r requirements-lock.txt；输入（APK/缓存）用户自备',
                'files': tools_entries,
            },
            'B_research_results': {
                'file': research_zip.name, 'bytes': research_zip.stat().st_size,
                'sha256': sha_file(research_zip), 'entries': len(research_entries),
                'scope': 'v3 结构化数据（77 data5 完整解码＋39047 记录视图＋字段字典4671项＋13项检查）、APK 内置主表、'
                         '技能数值解释（101 项逐描述＋77 条合并规则＋7 类普通效果＋Boss 必杀/治疗证据）、'
                         '阶段D样本链、验证报告、独立审查报告、角色名册结构化成品（data/）、查询所需数据文件',
                'excluded': B_EXCLUDE_NOTES,
                'media_excluded': excl_summary,
                'usage': '解压到任意目录；records.jsonl / *.json.raw 可直接被程序读取；查询脚本在 A 包 scripts/query_effect_dictionary.py（--id 43023606 等，需本包 output/card_comparison_cid30236/ 数据文件）；展示 HTML 页因内嵌媒体未收录（见 media_excluded）',
                'files_digest': sha_bytes(json.dumps([e['path'] for e in research_entries], ensure_ascii=False).encode('utf-8')),
                'files': research_entries,
            },
            'C_media': {
                'file': 'media_manifest.json',
                'sha256': sha_file(RELEASE / 'media_manifest.json'),
                'scope': '媒体产物本轮不复制（目录总量 903,402 文件≈20.24 GiB；objects/ 下 903,396 导出文件；56 类导出媒体合计≈20.18 GiB）；清单＋重建命令＋可选分包方案',
                'note': '需要现成媒体分包时可运行 scripts/release/build_full_unpack_bundle.py（并行打包任务脚本，默认排除音频 WAV）',
            },
        },
        'verification': {
            'delivery_isolated_chain': 'work/delivery_20261016/final/：git archive 解包链代码（与最终 HEAD 除新增打包脚本与交接文档外零差异）独立目录，'
                                       'A1—A3 前置生成（镜像 SHA256=3fd354b5…）、data5 两包装格式 4 文件、bdl 2 样本、chronicle 主表，'
                                       '全部与既有可靠成果逐字节一致（详见 README 与交接）',
            'zip_checks': checks,
            'not_tested': ['全新机器从零安装 .venv', '非 Windows 平台', 'bdl 全量（68,655）在独立目录重跑（项目内已 100% 完成并有验证）'],
        },
        'license_boundary': 'APK／缓存／解包媒体为 SEGA 所有；本发行仅含自有工具源码与结构化研究成果；公开分发游戏资源前必须检查版权许可',
        'upload_status': '本地构建完成，未上传；推送 GitHub 或发布 Release 需用户授权',
    }
    (RELEASE / 'package_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'tools_mb': round(tools_zip.stat().st_size / 1e6, 1),
                      'research_mb': round(research_zip.stat().st_size / 1e6, 1),
                      'research_entries': len(research_entries),
                      'minutes': round((time.time() - t0) / 60, 1), 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
