#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全角色名册生成器：合并缓存/APK charainfo，分类复制头像，输出 CSV/JSON/HTML 画廊。

数据来源（全部只读）：
- output/base_master/_mdCharacter.json                          APK 内置主表 charainfo（7800 条）
- output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw 缓存 charainfo（1488 条）
- output/cache_full_20261015_v3/decoded/worldinfo.data5.json.raw chara_place 所属名称表（22 条）
- output/full_unpack/objects/Card_Icon/                          头像 PNG（bdl 解包产物）

合并规则（沿用项目逐 ID 条件回退约定）：cid 在缓存 charainfo 中存在时取缓存记录，否则取 APK 记录；
不做逐字段合并。玩家实际解锁/装载状态不在本工具范围。

输出（可重建展示目录）：output/char_roster/
  data/playable_characters.{csv,json}  可玩角色（is_enemy!=1 且 rarity>=1）
  data/other_characters.{csv,json}     NPC/敌人等其他角色
  data/summary.json                    统计与缺失清单
  data/verification.json               数量/文件核对结果
  icons/playable/job{J}_{职业名}/{稀有度}星/{cid:05d}_{名称}.png
  icons/other/{cid:05d}_{名称}.png
  index.html                           画廊（职业/稀有度分区，可搜索，离线可用）
  README.md / manifest.json

运行（项目根目录）：.venv\\Scripts\\python.exe -B scripts/build_char_roster.py
仅标准库。
"""
import csv
import base64
import hashlib
import html
import json
import os
import shutil
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APK_CHAR = os.path.join(ROOT, 'output', 'base_master', '_mdCharacter.json')
CACHE_CHAR = os.path.join(ROOT, 'output', 'cache_full_20261015_v3', 'decoded', 'charainfo.data5.json.raw')
CACHE_WORLD = os.path.join(ROOT, 'output', 'cache_full_20261015_v3', 'decoded', 'worldinfo.data5.json.raw')
ICON_SRC_ROOT = os.path.join(ROOT, 'output', 'full_unpack', 'objects', 'Card_Icon')
OUT_DIR = os.path.join(ROOT, 'output', 'char_roster')

# 职业编号→名称：依据 spmotname 动作名相关分布推断（jobtype2↔magi、3↔heal、1↔snip/shoo、0/4↔近战系），
# 与 Chain Chronicle 五职业一致；主表内未找到官方职业名表，状态为“推断”。
JOB_NAMES = {0: '戦士', 1: '弓使い', 2: '魔法使い', 3: '僧侶', 4: '騎士'}
JOB_NAMES_CN = {0: '战士', 1: '弓手', 2: '法师', 3: '僧侣', 4: '骑士'}
JOB_UNKNOWN = '未知'

SAFE_REPLACE = str.maketrans({'\\': '＿', '/': '＿', ':': '＿', '*': '＿', '?': '＿',
                              '"': '＿', '<': '＿', '>': '＿', '|': '＿'})


def safe_name(name):
    s = (name or '').translate(SAFE_REPLACE).strip().rstrip('.')
    return s or 'noname'


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def icon_source(cid):
    """返回 full_unpack 中该 cid 头像 PNG 的绝对路径；不存在返回 None。"""
    base = f'cha_2d_icon_{cid:05d}'
    p = os.path.join(ICON_SRC_ROOT, base, base + '.png')
    return p if os.path.exists(p) else None


def main():
    t0 = time.time()
    apk_records = load_json(APK_CHAR)['charainfo']
    cache_records = load_json(CACHE_CHAR)['charainfo']
    place_records = load_json(CACHE_WORLD)['chara_place']
    place_names = {int(p['id']): p['name'] for p in place_records}

    cache_map = {r['cid']: r for r in cache_records}
    apk_map = {r['cid']: r for r in apk_records}
    merged_cids = sorted(set(apk_map) | set(cache_map))

    playable, other = [], []
    for cid in merged_cids:
        src = 'cache' if cid in cache_map else 'apk'
        r = cache_map.get(cid) or apk_map[cid]
        is_enemy = r.get('is_enemy')          # APK 字段；缓存记录无此字段为 None
        rarity = r.get('rarity')
        job = r.get('jobtype')
        affil = r.get('home') if r.get('home') is not None else r.get('place')
        row = {
            'cid': cid,
            'name': r.get('name'),
            'title': r.get('title'),
            'rarity': rarity,
            'jobtype': job,
            'job_name': JOB_NAMES.get(job, JOB_UNKNOWN),
            'affiliation_id': affil,
            'affiliation_name': place_names.get(affil),
            'cost': r.get('cost'),
            'maxlv': r.get('maxlv'),
            'skillname': r.get('skillname'),
            'illustrator': r.get('illustrator'),
            'voice_artist': r.get('voice_artist'),
            'profile': r.get('profile'),
            'is_enemy': is_enemy,
            'chara_type': r.get('chara_type'),  # 仅缓存记录存在
            'data_source': src,
            'icon_path': None,                   # 相对 output/char_roster 的正斜杠路径
            'icon_status': 'missing',
        }
        # 可玩判定：非敌人（is_enemy 0 或缓存记录缺省 None）且稀有度 >=1
        row['category'] = 'playable' if (is_enemy != 1 and rarity is not None and rarity >= 1) else 'other'
        (playable if row['category'] == 'playable' else other).append(row)

    # ---- 复制头像并回填路径 ----
    copied = 0
    size_mismatch = []
    for row in playable + other:
        cid = row['cid']
        src = icon_source(cid)
        if not src:
            continue
        nm = safe_name(row['name'])
        if row['category'] == 'playable':
            job = row['jobtype']
            job_dir = f"job{job}_{JOB_NAMES[job]}" if job in JOB_NAMES else 'job_unknown'
            rel = f"icons/playable/{job_dir}/{row['rarity']}星/{cid:05d}_{nm}.png"
        else:
            rel = f"icons/other/{cid:05d}_{nm}.png"
        dst = os.path.join(OUT_DIR, *rel.split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        if os.path.getsize(dst) != os.path.getsize(src):
            size_mismatch.append(cid)
        row['icon_path'] = rel
        row['icon_status'] = 'ok'
        copied += 1

    # ---- 数据文件 ----
    data_dir = os.path.join(OUT_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)

    csv_field_map = {
        'playable_characters': ['cid', 'name', 'title', 'rarity', 'jobtype', 'job_name',
                                'affiliation_id', 'affiliation_name', 'cost', 'maxlv',
                                'illustrator', 'voice_artist', 'data_source',
                                'icon_status', 'icon_path'],
        'other_characters': ['cid', 'name', 'title', 'rarity', 'is_enemy', 'chara_type',
                             'data_source', 'icon_status', 'icon_path'],
    }
    for rows, stem in ((playable, 'playable_characters'), (other, 'other_characters')):
        fields = csv_field_map[stem]
        with open(os.path.join(data_dir, stem + '.csv'), 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for row in rows:
                w.writerow({k: row.get(k) for k in fields})
        with open(os.path.join(data_dir, stem + '.json'), 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)

    missing_playable = [r['cid'] for r in playable if r['icon_status'] != 'ok']
    newest_block = [r for r in playable if 30000 <= r['cid'] < 40000]
    summary = {
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'merged_characters_total': len(merged_cids),
        'apk_records': len(apk_records),
        'cache_records': len(cache_records),
        'cache_overlay_applied_to_apk_same_cid': len(set(apk_map) & set(cache_map)),
        'playable_count': len(playable),
        'other_count': len(other),
        'icons_copied': copied,
        'playable_icon_missing': missing_playable,
        'playable_by_rarity': dict(sorted(Counter(r['rarity'] for r in playable).items())),
        'playable_by_job': {JOB_NAMES.get(k, JOB_UNKNOWN): v for k, v in
                            sorted(Counter(r['jobtype'] for r in playable).items(),
                                   key=lambda kv: (kv[0] is None, kv[0]))},
        'other_with_icon': sum(1 for r in other if r['icon_status'] == 'ok'),
        'job_name_basis': 'spmotname 动作名相关分布推断（主表无官方职业名表），状态=推断',
        'job_unknown_note': '127 条可玩角色为新版缓存记录格式，记录本身无 jobtype 字段；'
                            '武器类型与同名传播均不能唯一确定职业，未做推断，归入“未知”。',
        'newness': {
            'direct_date_field': None,
            'note': 'charainfo 全部 117 个键无逐角色实装日期字段（仅 revision 版本号）；'
                    'denju/skilllist 等 timestamp 为表级更新时间，booklist.release_time 绑定剧情非角色。',
            'global_cid_order': 'cid 全局顺序≠出卡顺序（用户指出，已核实）：5xxxx 换装段在 APK 内置主表、'
                                '30xxx 反而不在；编号块是命名空间/系统分配，不是时间轴；'
                                '同角色新版本编号递增（如 ラザフォード 337→20805→30108）只说明版本先后。',
            'newest_cid_block': '可玩角色 30xxx 段共 %d 条，仅存在于缓存增量主表（APK 内置主表可玩最大 cid=59104）。'
                                '段级“最新一批”判断成立（见锚点），但段内先后顺序无任何证据，不按 cid 排序解释新旧。'
                                % len(newest_block),
            'anchors': ['30002 ミレニア 首次出现于带日期剧情 2026-08-20（APK 打包后 2 天，唯一名）',
                        '30255 マルカ 首次出现 2026-05-28（唯一名）',
                        '30210 ファールラート / 30215 アストリット 首次出现 2026-10-15（唯一名）',
                        '方法：416 本带 release_time 的 booklist 剧情全文匹配 509 个唯一名可玩角色，117 个命中；'
                        '30xxx 段命中 4 个全部在 2026 年。首次出现=该名在带日期剧情中的最早提及，'
                        '是实装时间的上界（老角色晚期才登场会偏晚，不能单独证明新）。'],
            'cache_delta_also_updates_old': '缓存增量主表同时携带 %d 条低编号老角色记录（如 cid 89 アセス），'
                                '属记录更新，“在增量中”不等于“新出”。'
                                % sum(1 for r in playable if r['data_source'] == 'cache' and r['cid'] < 30000),
            'apk_master_built': '2026-08-18（APK zip 条目日期，APK 5.6.2/56021 打包时间）；'
                                '内置主表数据截止更早：30255 マルカ 2026-05-28 已登场剧情却不在 APK 主表，截止不晚于该日附近',
            'cache_snapshot': '2026-10-15（手机缓存采集日）',
        },
        'icon_source': 'output/full_unpack/objects/Card_Icon（手机缓存 bdl 解包，覆盖范围=已下载缓存）',
    }
    with open(os.path.join(data_dir, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    # ---- HTML 画廊 ----
    write_html(playable, other, summary)

    # ---- manifest ----
    manifest = {
        'generated_at': summary['generated_at'],
        'script': os.path.relpath(os.path.abspath(__file__), ROOT),
        'script_sha256': sha256_of(os.path.abspath(__file__)),
        'inputs': {os.path.relpath(p, ROOT): {'sha256': sha256_of(p), 'bytes': os.path.getsize(p)}
                   for p in (APK_CHAR, CACHE_CHAR, CACHE_WORLD)},
        'icon_source_dir': os.path.relpath(ICON_SRC_ROOT, ROOT),
        'outputs': {
            'playable_characters': len(playable),
            'other_characters': len(other),
            'icons_copied': copied,
            'html': 'index.html',
        },
        'merge_rule': '逐 ID 条件回退：cid 命中缓存 charainfo 取缓存，否则取 APK；不逐字段合并',
    }
    with open(os.path.join(OUT_DIR, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    # ---- 核对 ----
    checks = []
    def check(name, ok, detail):
        checks.append({'check': name, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})

    check('merged_total', len(merged_cids) == len(playable) + len(other),
          f'{len(merged_cids)} = {len(playable)}+{len(other)}')
    check('unique_cid', len({r['cid'] for r in playable + other}) == len(merged_cids),
          f'{len(merged_cids)} unique')
    on_disk = 0
    for row in playable + other:
        if row['icon_status'] == 'ok' and os.path.exists(os.path.join(OUT_DIR, *row['icon_path'].split('/'))):
            on_disk += 1
    check('icons_on_disk', on_disk == copied, f'{on_disk}/{copied}')
    check('icon_size_match', not size_mismatch, f'mismatch={size_mismatch[:10]}')
    with open(os.path.join(OUT_DIR, 'index.html'), encoding='utf-8') as f:
        html_text = f.read()
    newest_icon_ok = sum(1 for r in newest_block if r['icon_status'] == 'ok')
    embedded = html_text.count('data:image/png;base64,')
    check('html_embedded_images', embedded == copied + newest_icon_ok,
          f'{embedded}/{copied + newest_icon_ok}（含最新批次区块重复展示 {newest_icon_ok}）')
    expected_cards = len(playable) + len(newest_block)
    check('html_cards_and_rows',
          html_text.count('class="card"') == expected_cards and
          html_text.count('class="orow"') == len(other),
          f"cards={html_text.count('class="card"')}/{expected_cards} "
          f"rows={html_text.count('class="orow"')}/{len(other)}")
    check('missing_playable_icons_recorded', True,
          f'{len(missing_playable)}: {missing_playable}')
    verification = {'checks': checks,
                    'all_pass': all(c['status'] == 'PASS' for c in checks),
                    'elapsed_sec': round(time.time() - t0, 2)}
    with open(os.path.join(data_dir, 'verification.json'), 'w', encoding='utf-8') as f:
        json.dump(verification, f, ensure_ascii=False, indent=1)

    write_readme(summary, verification)

    print(json.dumps({'playable': len(playable), 'other': len(other),
                      'icons_copied': copied, 'missing_playable': missing_playable,
                      'all_pass': verification['all_pass']}, ensure_ascii=False, indent=1))
    return 0 if verification['all_pass'] else 1


def esc(s):
    return html.escape('' if s is None else str(s), quote=True)


def data_uri(rel_path):
    """把 output/char_roster 下的相对路径 PNG 读成 data URI（单文件 HTML 内嵌用）。"""
    with open(os.path.join(OUT_DIR, *rel_path.split('/')), 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode('ascii')


def write_html(playable, other, summary):
    parts = ['''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>锁链战记 全角色名册</title>
<style>
body{font-family:"Microsoft YaHei",system-ui,sans-serif;margin:16px;background:#fafafa;color:#222}
h1{font-size:22px} h2{margin:26px 0 6px;border-left:6px solid #c9a227;padding-left:8px}
h3{margin:16px 0 6px;color:#555}
.meta{color:#666;font-size:13px}
#q{width:320px;padding:6px;font-size:14px}
.grid{display:flex;flex-wrap:wrap;gap:10px}
.card{width:128px;background:#fff;border:1px solid #ddd;border-radius:6px;padding:6px;text-align:center}
.card img{width:128px;height:128px;display:block}
.card .nm{font-weight:700;font-size:13px;margin-top:4px;word-break:break-all}
.card .ti{font-size:11px;color:#777;min-height:2.4em;word-break:break-all}
.card .ci{font-size:11px;color:#999}
.noicon{width:128px;height:128px;display:flex;align-items:center;justify-content:center;
 background:#eee;color:#999;font-size:11px;border:1px dashed #bbb}
table{border-collapse:collapse;font-size:12px;background:#fff}
td,th{border:1px solid #ddd;padding:3px 6px}
tr.orow img{width:48px;height:48px;vertical-align:middle}
.nav a{margin-right:10px}
</style></head><body>
''']
    parts.append(f'<h1>锁链战记 全角色名册</h1>')
    parts.append(f'<p class="meta">生成：{esc(summary["generated_at"])}　'
                 f'合并主表 {summary["merged_characters_total"]} 条（APK {summary["apk_records"]} + 缓存 {summary["cache_records"]}，逐 ID 缓存优先）　'
                 f'可玩角色 {summary["playable_count"]}（头像缺 {len(summary["playable_icon_missing"])}）　'
                 f'NPC/敌人 {summary["other_count"]}（有头像 {summary["other_with_icon"]}）</p>')
    parts.append('<p class="meta">本文件为单文件自包含 HTML（全部头像已内嵌 base64，无需联网与外部文件），'
                 '职业名为推断（依据见 README）；头像来自手机缓存解包，未下载的角色无图标。'
                 '本页为数据展示，不代表玩家已解锁。</p>')
    parts.append('<p>搜索：<input id="q" type="search" placeholder="cid / 名称 / 称号"></p>')

    def card_html(row):
        s = f'{row["cid"]} {row["name"] or ""} {row["title"] or ""}'
        h = f'<div class="card" data-s="{esc(s)}">'
        if row['icon_status'] == 'ok':
            h += f'<img loading="lazy" src="{data_uri(row["icon_path"])}" alt="{esc(row["name"])}">'
        else:
            h += '<div class="noicon">图标未取得</div>'
        h += (f'<div class="nm">{esc(row["name"])}</div>'
              f'<div class="ti">{esc(row["title"])}</div>'
              f'<div class="ci">cid {row["cid"]}</div></div>')
        return h

    # 最新编号批次（推断最近新增）：30xxx 段；5xxxx 为换装/版本卡、99999 ダミィ 为占位记录，不计入
    newest = sorted((r for r in playable if 30000 <= r['cid'] < 40000), key=lambda x: -x['cid'])
    parts.append(f'<h2 id="newest">最新一批：30xxx 段（{len(newest)}，段级判断）</h2>')
    parts.append('<p class="meta">主表无逐角色实装日期字段，<strong>cid 全局顺序≠出卡顺序</strong>'
                 '（5xxxx 换装段在 APK 内置主表、30xxx 反而不在；编号块是系统分配不是时间轴；段内先后顺序无证据）。'
                 '本段仅按“段级”判定为最新一批：全部记录只存在于缓存增量主表（快照 2026-10-15），'
                 '且可追踪的 4 个唯一名角色在带日期剧情中首次出现均在 2026 年'
                 '（30002 ミレニア 2026-08-20，即 APK 2026-08-18 打包后 2 天；30255 マルカ 2026-05-28；'
                 '30210 ファールラート／30215 アストリット 2026-10-15）。'
                 '下表按 cid 降序仅为展示约定，<strong>不代表段内新旧排序</strong>。'
                 '5xxxx 段为换装/版本卡、99999 ダミィ 为占位记录，不计入本区。</p>')
    parts.append('<div class="grid">')
    for row in newest:
        parts.append(card_html(row))
    parts.append('</div>')

    # 职业分区
    by_job = {}
    for row in playable:
        by_job.setdefault(row['jobtype'], []).append(row)
    nav = [f'<a href="#newest">最新编号（{len(newest)}）</a>']
    for job in sorted(by_job, key=lambda j: (j is None, j)):
        jn = JOB_NAMES.get(job, JOB_UNKNOWN)
        jcn = JOB_NAMES_CN.get(job, '')
        nav.append(f'<a href="#job{job}">{esc(jn)}{esc(jcn)}（{len(by_job[job])}）</a>')
    nav.append(f'<a href="#other">NPC/敌人（{len(other)}）</a>')
    parts.append('<p class="nav">' + ''.join(nav) + '</p>')

    for job in sorted(by_job, key=lambda j: (j is None, j)):
        jn = JOB_NAMES.get(job, JOB_UNKNOWN)
        jcn = JOB_NAMES_CN.get(job, '')
        parts.append(f'<h2 id="job{job}">{esc(jn)} {esc(jcn)}（{len(by_job[job])}）</h2>')
        by_r = {}
        for row in by_job[job]:
            by_r.setdefault(row['rarity'], []).append(row)
        for r in sorted(by_r, reverse=True):
            rows = sorted(by_r[r], key=lambda x: x['cid'])
            parts.append(f'<h3>稀有度 {r}★（{len(rows)}）</h3><div class="grid">')
            for row in rows:
                parts.append(card_html(row))
            parts.append('</div>')

    # NPC/敌人表
    parts.append(f'<h2 id="other">NPC／敌人等其他角色（{len(other)}）</h2>')
    parts.append('<table><tr><th>头像</th><th>cid</th><th>名称</th><th>称号</th><th>rarity</th>'
                 '<th>is_enemy</th><th>来源</th></tr>')
    for row in sorted(other, key=lambda x: x['cid']):
        s = f'{row["cid"]} {row["name"] or ""} {row["title"] or ""}'
        img = f'<img loading="lazy" src="{data_uri(row["icon_path"])}" alt="">' if row['icon_status'] == 'ok' else ''
        parts.append(f'<tr class="orow" data-s="{esc(s)}"><td>{img}</td><td>{row["cid"]}</td>'
                     f'<td>{esc(row["name"])}</td><td>{esc(row["title"])}</td>'
                     f'<td>{esc(row["rarity"])}</td><td>{esc(row["is_enemy"])}</td>'
                     f'<td>{esc(row["data_source"])}</td></tr>')
    parts.append('</table>')
    parts.append('''<script>
const q=document.getElementById('q');
q.addEventListener('input',()=>{
 const v=q.value.trim().toLowerCase();
 for(const el of document.querySelectorAll('.card,.orow')){
  el.style.display=(!v||el.dataset.s.toLowerCase().includes(v))?'':'none';
 }
});
</script></body></html>''')
    with open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))


def write_readme(summary, verification):
    lines = f"""# 全角色名册（char_roster）

生成：{summary['generated_at']}　重建：`.venv\\Scripts\\python.exe -B scripts/build_char_roster.py`（项目根目录，仅标准库）

## 内容

| 路径 | 说明 |
|---|---|
| `index.html` | **单文件自包含画廊**（全部头像 base64 内嵌，约 80MB，无需联网/外部文件）：可玩角色按 职业→稀有度 分区，NPC/敌人列表，支持 cid/名称/称号搜索 |
| `data/playable_characters.csv/.json` | 可玩角色 {summary['playable_count']} 条（is_enemy≠1 且 rarity≥1） |
| `data/other_characters.csv/.json` | NPC/敌人等其他角色 {summary['other_count']} 条 |
| `data/summary.json` | 统计、缺失清单、推断依据 |
| `data/verification.json` | 生成核对（{'全部 PASS' if verification['all_pass'] else '存在 FAIL，需检查'}） |
| `icons/playable/job{{编号}}_{{职业名}}/{{稀有度}}星/` | 可玩角色头像（128×128 PNG，带游戏内稀有度边框） |
| `icons/other/` | 有头像的其他角色（{summary['other_with_icon']} 个） |
| `manifest.json` | 输入文件哈希、脚本哈希、合并规则 |

## 数据来源与合并规则

- APK 内置主表 `output/base_master/_mdCharacter.json` charainfo {summary['apk_records']} 条。
- 缓存主表 `output/cache_full_20261015_v3/decoded/charainfo.data5.json.raw` charainfo {summary['cache_records']} 条。
- 逐 ID 条件回退：cid 命中缓存取缓存记录，否则取 APK；不逐字段合并。同 cid 覆盖 {summary['cache_overlay_applied_to_apk_same_cid']} 条。
- 合并后共 {summary['merged_characters_total']} 个唯一 cid。角色条数不等于玩家已解锁/可用卡牌数。

## 头像来源与缺失

- 头像 = `output/full_unpack/objects/Card_Icon/cha_2d_icon_<cid 5位起零填充>/`（手机缓存 bdl 解包产物）。
- 缓存只含已下载资源：可玩角色缺头像 {len(summary['playable_icon_missing'])} 个：{summary['playable_icon_missing']}；NPC/敌人多数无图标属未下载或本无卡面图标。
- APK 侧仅有 Blank/empty 占位纹理，无正式头像资源。

## 字段与推断说明

- 职业名（jobtype 0–4 → 戦士/弓使い/魔法使い/僧侶/騎士）为**推断**：依据 spmotname 动作名相关分布，主表内未发现官方职业名表。
- 127 条可玩角色（新版缓存记录格式）记录本身无 `jobtype` 字段，归入“未知”：武器类型→职业为一对多（实测 weaponlist.type 与 jobtype 交叉分布不唯一），同名传播存在同名多职业反例（如 ロレッタ 0/1/4），均不可靠，未做推断。
- 所属名 = `home`（缓存）或 `place`（APK）字段经 worldinfo.data5 `chara_place` 表映射；映射不到保留 null。
- `data_source` 标记该 cid 取值来自 cache 还是 apk；`chara_type` 仅缓存记录存在。
- 本目录不解释字段语义之外的数值，不代表玩家解锁状态或当前加载版本。

## 新旧判断（谁是新出的／靠后加进去的）

**主表没有逐角色实装日期字段**：charainfo 全部 117 个键中无 time/date 类字段（仅 revision 版本号）；denju、skilllist 等表的 timestamp 经核实为表级统一更新时间；booklist.release_time 精确到秒（2014—2026）但绑定的是剧情/活动而非角色。

**cid 全局顺序 ≠ 出卡顺序（用户指出，已核实成立）**：

- 5xxxx 换装段在 APK 内置主表中、30xxx 段反而不在——若编号即时间轴则不可能。编号块是命名空间/系统分配（主序列 1–9xxx→1xxxx→2xxxx→30xxx、换装 5xxxx、敌方 7xxxx/8xxxx、占位 99999），块间先后不能按数字比。
- 同角色新版本编号递增（ラザフォード 337→20805→30108、ヘリオス 201→30201）只说明版本先后，不给出日期。
- **段内顺序无证据**：30xxx 段内 30001→30338 的排列不能读作新旧排序。

**仍可成立的段级判断**（"最新一批：30xxx 段"区）：

1. 该段 101 条可玩记录全部只存在于缓存增量主表（快照 2026-10-15）；APK 内置主表可玩最大 cid=59104，无 30xxx 段。APK 5.6.2 打包于 2026-08-18，且内置主表数据截止更早（30255 マルカ 2026-05-28 已登场剧情却不在 APK 主表）。
2. 日期锚点旁证：416 本带 release_time 的 booklist 剧情全文匹配 509 个唯一名可玩角色、117 个命中；30xxx 段命中 4 个全部在 2026 年——30002 ミレニア 2026-08-20（APK 打包后 2 天）、30255 マルカ 2026-05-28、30210 ファールラート／30215 アストリット 2026-10-15。首次出现是实装上界（老角色晚期才登场会偏晚），不能单独证明新，但与增量批次证据方向一致。
3. 反例保护：增量主表同时携带 308 条低编号老角色（如 cid 89 アセス）的记录更新——"在增量中"不等于"新出"，故只按"段+锚点"联合判定，不按单条 data_source 判定新旧。

## 边界

- 输入为既有本地解包产物；本工具只读输入、只写 `output/char_roster/`。
- 不声明全游戏覆盖（私有目录/服务端范围未知）；未下载头像不重复采集。
"""
    with open(os.path.join(OUT_DIR, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(lines)


if __name__ == '__main__':
    sys.exit(main())
