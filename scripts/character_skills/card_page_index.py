# -*- coding: utf-8 -*-
"""角色技能页索引页生成器（任务 20261020-character-skills-index-pages）。

为正式角色技能页（output/character_skills/pages/<cid>/index.html，v2 玩家版式）
生成两个纯静态、离线可用的入口页（与 per-card 页面同目录）：

  pages/index.html      选择器首页：cid / 名称 / 称号（日文原文）即时搜索，
                        结果为 头像小图＋CID＋名称/称号，点击跳 <cid>/index.html；
  pages/all_cards.html  全卡列表页：2236 行（头像＋CID＋名称/称号，按 cid 升序、
                        懒加载头像），顶部 cid/名称搜索过滤＋数量统计。

数据口径：
- 每卡 cid/name/title 全部取自该卡 pages/<cid>/card.json 的 basic.fields
  display_value（与 per-card 页 R-07 修复口径一致：字段缺失时显示 display_value
  如「外部/网站维护」，不造值）；
- 头像一律指向本 cid 自己的 pages/art/<cid>/icon.png（相对路径、不内嵌 base64、
  不跨 cid 借图）；缺 icon 的 cid 生成时即改为「未取得」占位块；
- 库快照信息取自 card.json sources.snapshot（逐卡核对为同一值）；
- 四联总指标读 pages/_batch/campaign_latest.json 所指 campaign_report.json 的
  summary（四 cohort 汇总），并在生成时与本脚本 EXPECTED_CAMPAIGN（基线值存档于
  docs/tasks/20261021-character-skills-audit-rectify.md §M1）交叉核对，
  不一致即显式失败，不静默写出过期数值。

自检（run_checks，每次生成都跑）：
- 条目数=manifest 全 2236、cid 唯一、每卡 card.json/index.html 存在；
- 生成的 HTML 重新解析：内嵌 JSON 与 card.json basic 逐卡全量比对（2236/2236）；
- 全部跳转目标 <cid>/index.html 存在；全部 <img src> 在盘上存在且 cid=行 cid
  （无跨 cid 借图）；缺头像集合恰为缺 icon 清单；
- 盘上 art/<cid>/{card,whole,icon} 缺图集合与迁移任务卡清单逐一核对。

用法（仓库根）：
  & .\\.venv\\Scripts\\python.exe -B scripts/character_skills/card_page_index.py --execute
  （缺 --execute 只做数据提取与检查、不写 HTML）
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

DEFAULT_PAGES = Path("output/character_skills/pages")
DEFAULT_MANIFEST = Path("output/character_skills/r2_preparation/cohorts/manifest.json")

# YG1第二批20261024内存全库预估：40行C→A，A17522/C24143/推断3397；原文A与确认不变。
# 下列批17说明保留历史依据；本轮依据见yg1_batch2_20261024/preview_full.json及最终差异。
# 指标基线（M1，20261021 独立审查整改）：对齐当前 campaign run（pages/_batch/
# campaign_latest.json 所指，批 17 重建后实测——A 17,476/C 24,189/
# 整行推断 3,351＝批 15 后 3,318＋33（批 17 晋级 92 行中 59 行原为 b8/b14 推断行
# evidence 不变，仅 33 行 P2 溢出 C→A 新入推断计数；首次预测 3,410 误按 92 行全计，
# 重建实测 3,351 后更正并整轮重跑统一签名）；整行确认 266 不变（记录级 18＋类型外推
# 248）；批 15 后基线 A 17,443/C 24,222/推断 3,318 与更早各批基线均为历史值；
# 生成时与 campaign_report.json
# 现值交叉核对，任何一项不一致都显式失败，不允许静默写出过期数值。
EXPECTED_CAMPAIGN = {
    "N_all": 41665,
    "A": 17522,
    "whole_row_confirmed": 266,
    "scope_record": 18,
    "scope_by_type_extrapolated": 248,
    "original_A": 13859,
    "C": 24143,
    "whole_row_inferred": 3397,
}
# 缺图 cid 清单（README §16.2 / 迁移任务卡 §2；59103 三类皆缺，故单列集合不含它）
MISSING_CARD = {
    227, 239, 269, 290, 306, 309, 315, 2239, 2244, 2308, 4239, 4286, 4305,
    5242, 5245, 5283, 5288, 6278, 6295, 6311, 7107, 7639, 8234, 8242, 8291,
    8341, 9211, 12220, 13001, 13208, 59103,
}
MISSING_ICON = {7107, 8234, 13001, 59103}
MISSING_WHOLE = {59103}


# ---------------------------------------------------------------- 数据提取

def field_of(fields: list, key: str):
    """取 basic.fields 中 key 的 (display_value, raw_state)。"""
    for f in fields:
        if f.get("key") == key:
            return f.get("display_value"), f.get("raw_state")
    return None, "absent"


def load_entries(pages_dir: Path, manifest: Path):
    """逐卡读 card.json basic，提取 cid/name/title/icon 状态。"""
    members = json.loads(manifest.read_text(encoding="utf-8"))["members"]
    cids = [int(m["cid"]) for m in members]
    entries = []
    snapshots = set()
    for cid in cids:
        card_path = pages_dir / str(cid) / "card.json"
        page_path = pages_dir / str(cid) / "index.html"
        if not card_path.is_file():
            raise SystemExit(f"[FAIL] 缺 card.json：{card_path}")
        if not page_path.is_file():
            raise SystemExit(f"[FAIL] 缺跳转目标：{page_path}")
        card = json.loads(card_path.read_text(encoding="utf-8"))
        basic = card.get("basic") or {}
        fields = basic.get("fields") or []
        name, name_state = field_of(fields, "name")
        title, title_state = field_of(fields, "title")
        if name is None:
            raise SystemExit(f"[FAIL] cid {cid} basic.fields 无 name 字段")
        snap = (card.get("sources") or {}).get("snapshot")
        if not snap:
            raise SystemExit(f"[FAIL] cid {cid} sources.snapshot 缺失")
        snapshots.add(snap)
        entries.append({
            "cid": cid,
            "name": name,
            "title": title if title is not None else "",
            "name_state": name_state,
            "title_state": title_state,
            "icon": 1 if (pages_dir / "art" / str(cid) / "icon.png").is_file() else 0,
        })
    if len(snapshots) != 1:
        raise SystemExit(f"[FAIL] sources.snapshot 不唯一：{sorted(snapshots)!r}")
    entries.sort(key=lambda e: e["cid"])
    return entries, snapshots.pop()


def metric_values_from_summary(summary: dict) -> dict:
    """从 policy.metrics 形状的 summary 提取入口页展示的 8 个指标值（不含 report_rel）。"""
    scopes = summary["whole_row_confirmed_scopes"]
    return {
        "N_all": summary["N_all"],
        "A": summary["A"]["count"],
        "whole_row_confirmed": summary["whole_row_confirmed"]["count"],
        "scope_record": scopes["record"],
        "scope_by_type_extrapolated": scopes["by_type_extrapolated"],
        "original_A": summary["original_A"]["count"],
        "C": summary["C"]["count"],
        "whole_row_inferred": summary["whole_row_inferred"]["count"],
    }


def load_campaign_metrics(pages_dir: Path) -> dict:
    """读 _batch/campaign_latest.json 所指 campaign_report.json 的 summary。"""
    ptr = pages_dir / "_batch" / "campaign_latest.json"
    report_rel = json.loads(ptr.read_text(encoding="utf-8"))["report"]
    report_path = (pages_dir / report_rel).resolve()
    if not report_path.is_file():
        raise SystemExit(f"[FAIL] campaign report 不存在：{report_path}")
    s = json.loads(report_path.read_text(encoding="utf-8"))["summary"]
    metrics = metric_values_from_summary(s)
    metrics["report_rel"] = report_rel
    for k, v in EXPECTED_CAMPAIGN.items():
        if metrics.get(k) != v:
            raise SystemExit(
                f"[FAIL] 四联指标与 EXPECTED_CAMPAIGN 基线不一致：{k} 现值 "
                f"{metrics.get(k)!r} ≠ 基线 {v!r}（{report_path}）。"
                f"指标已变化，请先更新本脚本 EXPECTED_CAMPAIGN 与页面文案，不要静默沿用。"
            )
    return metrics


# ---------------------------------------------------------------- 入口页一致性检查（M1）
# 供 card_page_batch.campaign 完成检查与 card_page_verify_full 复用：入口页展示的
# 指标与 run 指针必须等于当前 campaign，否则明确标注 STALE，不允许静默陈旧。

METRIC_LINE_RES = {
    "A": re.compile(r"A ([\d,]+)/([\d,]+)（数值/公式行率）"),
    "whole_row_confirmed": re.compile(r"整行确认 ([\d,]+)/([\d,]+)（记录级 ([\d,]+)＋类型外推 ([\d,]+)）"),
    "original_A": re.compile(r"原文A ([\d,]+)/"),
    "C": re.compile(r"C仅未知 ([\d,]+)/"),
    "whole_row_inferred": re.compile(r"整行推断 ([\d,]+)/"),
}


def parse_entry_pointer(text: str):
    """入口页 HTML 中标注的 campaign_report 相对路径（pages/…）。"""
    m = re.search(r"pages/(_batch/[^<\s\"']+campaign_report\.json)", text)
    return m.group(1) if m else None


def parse_entry_metrics(text: str):
    """解析 index.html 指标行为数值 dict；任一段缺失返回 None。"""
    def num(s):
        return int(s.replace(",", ""))
    vals = {}
    for key, pat in METRIC_LINE_RES.items():
        m = pat.search(text)
        if not m:
            return None
        if key == "whole_row_confirmed":
            vals["whole_row_confirmed"] = num(m.group(1))
            vals["scope_record"] = num(m.group(3))
            vals["scope_by_type_extrapolated"] = num(m.group(4))
        elif key in ("A", "original_A", "C", "whole_row_inferred"):
            vals[key] = num(m.group(1))
        if key in ("A", "whole_row_confirmed"):
            vals.setdefault("N_all", num(m.group(2)))
    return vals if len(vals) >= 8 else None


def entry_pages_consistency(pages_dir: Path, summary: dict, report_rel: str) -> dict:
    """入口两页与当前 campaign 的一致性检查（batch 完成检查/全量机器检查共用）。

    返回 dict(status=CURRENT/STALE/NOT_FOUND, index=…, all_cards=…, detail=[…])；
    STALE 只标注并在调用方暴露，不静默。"""
    result = {"status": "CURRENT", "index": None, "all_cards": None, "detail": []}
    expected = metric_values_from_summary(summary)
    expected_pointer = report_rel  # parse_entry_pointer 捕获的是 pages/ 之后的相对路径
    for name in ("index.html", "all_cards.html"):
        path = pages_dir / name
        if not path.is_file():
            result[name.replace(".html", "")] = "NOT_FOUND"
            result["status"] = "STALE"
            result["detail"].append(f"{name} 不存在")
            continue
        text = path.read_text(encoding="utf-8")
        pointer = parse_entry_pointer(text)
        if pointer != expected_pointer:
            result[name.replace(".html", "")] = "STALE"
            result["status"] = "STALE"
            result["detail"].append(
                f"{name} run 指针过期：页内 {pointer!r} ≠ 当前 {expected_pointer!r}")
            continue
        if name == "index.html":
            got = parse_entry_metrics(text)
            if got is None:
                result["index"] = "STALE"
                result["status"] = "STALE"
                result["detail"].append("index.html 指标行解析失败（版式或文案变化？）")
            else:
                bad = {k: (got[k], expected[k]) for k in expected if got.get(k) != expected[k]}
                if bad:
                    result["index"] = "STALE"
                    result["status"] = "STALE"
                    result["detail"].append(f"index.html 指标过期（页内≠当前 campaign）：{bad}")
                else:
                    result["index"] = "CURRENT"
        else:
            result["all_cards"] = "CURRENT"
    return result


# ---------------------------------------------------------------- HTML 构建

CSS = """
:root{--paper:#141418;--panel:#222228;--ink:#d8d8de;--muted:#8a8a94;--line:#34343c;--gold:#c8b06a}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Microsoft YaHei","Hiragino Kaku Gothic ProN",system-ui,sans-serif;font-size:14px;line-height:1.7}
a{color:#8ab4c8;text-underline-offset:3px}a:focus-visible{outline:2px solid #c19136;outline-offset:2px}
.wrap{max-width:1100px;margin:0 auto;padding:16px}
.topbar{background:#101014;padding:10px 16px;font-size:13px;color:#9a9aa2;border-bottom:1px solid #2c2c34}
h1{font-size:19px;color:#fff;margin:6px 0 2px}
.sub{font-size:12px;color:#8a8a94;margin:0 0 12px}
.metrics-line{font-size:11px;color:#8a8a94;margin:2px 0 10px;letter-spacing:.3px}
.src-note{font-size:11px;color:#6f6f78;margin:2px 0 12px;word-break:break-all}
.src-note code{color:#8a8a94}
.searchbox{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px 16px;margin:12px 0}
.searchbox input{width:100%;background:#101014;border:1px solid #3c3c46;border-radius:5px;color:#e8e8ee;font-size:15px;padding:8px 10px;font-family:inherit}
.searchbox input:focus{outline:2px solid #c19136;outline-offset:1px}
.hint{font-size:12px;color:#8a8a94;margin:6px 0 0}
.count-line{font-size:12px;color:#9a9aa2;margin:8px 0 4px}
.list{margin:8px 0 24px;padding:0;list-style:none}
.list li{border-bottom:1px solid #2c2c34}
.list a{display:flex;align-items:center;gap:10px;padding:5px 6px;text-decoration:none;color:var(--ink)}
.list a:hover{background:#1b1b20}
.avatar{flex:0 0 40px;width:40px;height:40px;border-radius:4px;background:#101014;object-fit:contain;border:1px solid #2c2c34}
.noimg{flex:0 0 40px;width:40px;height:40px;border-radius:4px;background:#101014;border:1px dashed #3c3c46;color:#6f6f78;font-size:10px;display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.2}
.cid{flex:0 0 72px;color:#8a8a94;font-size:12px;font-variant-numeric:tabular-nums}
.nm{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.nm em{font-style:normal;color:var(--gold);font-size:12px;margin-left:8px}
.more{font-size:12px;color:#8a8a94;padding:8px 6px}
.allgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:6px;margin:8px 0 24px}
.allgrid a{display:flex;align-items:center;gap:8px;background:var(--panel);border:1px solid var(--line);border-radius:5px;padding:4px 8px;text-decoration:none;color:var(--ink);min-width:0}
.allgrid a:hover{background:#1b1b20;border-color:#4a4a56}
.allgrid .cid{flex-basis:56px}
.footer{border-top:1px solid #2c2c34;margin-top:20px;padding:10px 0 30px;font-size:12px;color:#8a8a94}
@media (max-width:600px){.allgrid{grid-template-columns:1fr 1fr}.cid{flex-basis:52px}}
"""


def _json_for_script(obj) -> str:
    """内嵌 <script type=application/json> 用的 JSON（防 </script> 提前闭合）。"""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def fmt(n: int) -> str:
    return f"{n:,}"


def _avatar_html(cid: int, icon: int, cls: str, lazy: bool) -> str:
    if icon:
        loading = ' loading="lazy"' if lazy else ""
        return (f'<img class="avatar" src="art/{cid}/icon.png"{loading} '
                f'width="40" height="40" alt="头像 (cid {cid})">')
    return '<span class="noimg" title="本输入快照未取得 icon">未取得</span>'


def build_index_html(entries, snapshot: str, metrics: dict) -> bytes:
    m = metrics
    metric_line = (
        f'A {fmt(m["A"])}/{fmt(m["N_all"])}（数值/公式行率）　·　'
        f'整行确认 {fmt(m["whole_row_confirmed"])}/{fmt(m["N_all"])}'
        f'（记录级 {m["scope_record"]}＋类型外推 {m["scope_by_type_extrapolated"]}）　·　'
        f'原文A {fmt(m["original_A"])}/{fmt(m["N_all"])}　·　'
        f'C仅未知 {fmt(m["C"])}/{fmt(m["N_all"])}'
    )
    compact = [[e["cid"], e["name"], e["title"], e["icon"]] for e in entries]
    n_icon = sum(e["icon"] for e in entries)
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>角色技能页 · 选择器（按 CID 或名称）</title>
<style>{CSS}</style>
</head>
<body>
<div class="topbar">角色技能页（v2 玩家版式） · 纯静态离线索引 · 数据全部来自各卡 card.json 原值</div>
<div class="wrap">
<h1>角色技能页选择器</h1>
<p class="sub">共 {len(entries)} 张卡 · 库快照：{html.escape(snapshot)} · 头像 {fmt(n_icon)} 张（缺 icon {len(entries) - n_icon} 张：7107、8234、13001、59103，本输入快照未取得，不借图）</p>
<p class="metrics-line">{html.escape(metric_line)}　·　整行推断 {fmt(m['whole_row_inferred'])}/{fmt(m['N_all'])}</p>
<p class="src-note">指标来源：<code>pages/{html.escape(m['report_rel'])}</code>（四 cohort 汇总，campaign_latest.json 指针；分母 N_all={fmt(m['N_all'])} 为 2236 卡全部描述行）。生成器 <code>scripts/character_skills/card_page_index.py</code> 生成时与脚本内基线（存档 docs/tasks/20261021-character-skills-audit-rectify.md §M1）交叉核对。</p>
<div class="searchbox">
  <input id="q" type="search" autocomplete="off" placeholder="输入 CID（数字）或 名称／称号（日文，支持部分匹配）" aria-label="按 CID 或名称搜索">
  <p class="hint">输入数字按 CID 前缀匹配；输入日文按 名称／称号 部分匹配。点击结果行进入该卡技能页；回车跳到第一个匹配。</p>
</div>
<p class="count-line" id="count"></p>
<ul class="list" id="list"></ul>
<p class="more" id="more"></p>
<div class="footer">
  <a href="all_cards.html">全卡列表页（2236 张，CID＋名称＋头像）</a> ·
  <a href="README.md">本目录 README（口径与审查记录）</a><br>
  头像为命名规则绑定（CharacterFactory.GetCharaTextureName*，见 <code>output/card_images/</code>
  binding_evidence 与 <code>pages/README.md</code> §16.2）；缺图显示「未取得」，不借用其他 cid 的图。
</div>
</div>
<script type="application/json" id="cards-data">{_json_for_script(compact)}</script>
<script>
"use strict";
var DATA=JSON.parse(document.getElementById("cards-data").textContent.replace(/<\\\\\\//g,"</"));
var listEl=document.getElementById("list"),countEl=document.getElementById("count"),moreEl=document.getElementById("more");
var MAXSHOW=100;
function norm(s){{return s.toLowerCase();}}
function matches(e,q){{ // e=[cid,name,title,icon]
  if(!q)return true;
  if(/^\\d+$/.test(q)&&String(e[0]).indexOf(q)===0)return true;
  return norm(e[1]).indexOf(q)>=0||(e[2]&&norm(e[2]).indexOf(q)>=0)||String(e[0]).indexOf(q)>=0;
}}
function row(e){{
  var li=document.createElement("li");
  var a=document.createElement("a");a.href=e[0]+"/index.html";
  var av;
  if(e[3]){{av=document.createElement("img");av.className="avatar";av.src="art/"+e[0]+"/icon.png";av.loading="lazy";av.width=40;av.height=40;av.alt="头像 (cid "+e[0]+")";}}
  else{{av=document.createElement("span");av.className="noimg";av.title="本输入快照未取得 icon";av.textContent="未取得";}}
  var cid=document.createElement("span");cid.className="cid";cid.textContent=e[0];
  var nm=document.createElement("span");nm.className="nm";nm.textContent=e[1];
  if(e[2]){{var em=document.createElement("em");em.textContent=e[2];nm.appendChild(em);}}
  a.appendChild(av);a.appendChild(cid);a.appendChild(nm);li.appendChild(a);
  return li;
}}
function render(){{var q=norm(document.getElementById("q").value.trim());
  var hits=DATA.filter(function(e){{return matches(e,q);}});
  listEl.textContent="";
  var show=Math.min(hits.length,MAXSHOW);
  for(var i=0;i<show;i++)listEl.appendChild(row(hits[i]));
  countEl.textContent=hits.length?"匹配 "+hits.length+" 张"+(show<hits.length?"（显示前 "+MAXSHOW+" 条）":""):"（无匹配）";
  moreEl.textContent=show<hits.length?"改用全卡列表页的页内过滤可看全部 2236 行：":"";
  if(show<hits.length){{var a=document.createElement("a");a.href="all_cards.html";a.textContent="打开全卡列表页";moreEl.appendChild(a);}}
}}
document.getElementById("q").addEventListener("input",render);
document.getElementById("q").addEventListener("keydown",function(ev){{if(ev.key==="Enter"){{var q=norm(this.value.trim());var hits=DATA.filter(function(e){{return matches(e,q);}});if(hits.length)location.href=hits[0][0]+"/index.html";}}}});
render();
</script>
</body>
</html>
"""
    return doc.encode("utf-8")


def build_all_cards_html(entries, snapshot: str, metrics: dict) -> bytes:
    n_icon = sum(e["icon"] for e in entries)
    rows = []
    for e in entries:
        nm = html.escape(e["name"])
        if e["title"]:
            nm += f' <em>{html.escape(e["title"])}</em>'
        rows.append(
            f'<a href="{e["cid"]}/index.html" data-k="{html.escape(str(e["cid"]) + " " + e["name"] + " " + e["title"]).lower()}">'
            f'{_avatar_html(e["cid"], e["icon"], "avatar", True)}'
            f'<span class="cid">{e["cid"]}</span><span class="nm">{nm}</span></a>'
        )
    miss = sorted(set(e["cid"] for e in entries if not e["icon"]))
    miss_txt = "、".join(str(c) for c in miss)
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>全卡列表（{len(entries)} 张 · CID＋名称＋头像）</title>
<style>{CSS}</style>
</head>
<body>
<div class="topbar">角色技能页（v2 玩家版式） · 全卡列表 · 数据全部来自各卡 card.json 原值</div>
<div class="wrap">
<h1>全卡列表</h1>
<p class="sub">共 {fmt(len(entries))} 张 · 库快照：{html.escape(snapshot)} · 有头像 {fmt(n_icon)} 张 · 头像缺失 {len(miss)} 张（{miss_txt}，本输入快照未取得，不借图） · 按 CID 升序</p>
<div class="searchbox">
  <input id="q" type="search" autocomplete="off" placeholder="页内过滤：输入 CID 或 名称／称号（日文，部分匹配）" aria-label="过滤全卡列表">
  <p class="hint">过滤只隐藏不匹配的行，不改数据。</p>
</div>
<p class="count-line" id="count">当前显示 {fmt(len(entries))} 张</p>
<div class="allgrid" id="grid">
{chr(10).join(rows)}
</div>
<div class="footer">
  <a href="index.html">返回选择器首页（即时搜索）</a> ·
  <a href="README.md">本目录 README（口径与审查记录）</a><br>
  头像（<code>art/&lt;cid&gt;/icon.png</code>）懒加载；缺 icon 的行显示「未取得」占位，
  不借用其他 cid 的图。四联指标同首页（来源 <code>pages/{html.escape(metrics['report_rel'])}</code>）。
</div>
</div>
<script>
"use strict";
var q=document.getElementById("q"),grid=document.getElementById("grid"),countEl=document.getElementById("count");
var ROWS=[].slice.call(grid.querySelectorAll("a"));
q.addEventListener("input",function(){{
  var s=this.value.trim().toLowerCase(),n=0;
  ROWS.forEach(function(a){{
    var hit=!s||a.getAttribute("data-k").indexOf(s)>=0;
    a.style.display=hit?"":"none";if(hit)n++;
  }});
  countEl.textContent="当前显示 "+n+" 张"+(s?"（共 {len(entries)} 张）":"");
}});
</script>
</body>
</html>
"""
    return doc.encode("utf-8")


# ---------------------------------------------------------------- 自检

HREF_RE = re.compile(r'href="(\d+)/index\.html"')
IMG_RE = re.compile(r'<img class="avatar" src="art/(\d+)/icon\.png"')


def run_checks(pages_dir: Path, entries, html_index: bytes, html_all: bytes, skip_disk: bool = False):
    """生成后自检；skip_disk=True 时（--execute 前）跳过需要写盘的核对。"""
    problems = []
    idx_text = html_index.decode("utf-8")
    all_text = html_all.decode("utf-8")

    # 1. 条目完整性
    cids = [e["cid"] for e in entries]
    if len(cids) != len(set(cids)):
        problems.append("cid 有重复")
    if len(entries) != 2236:
        problems.append(f"条目数 {len(entries)} ≠ 2236")

    # 2. index.html 内嵌 JSON 与 entries 全量一致（重解析，不引用构建变量）
    m = re.search(r'<script type="application/json" id="cards-data">(.*?)</script>', idx_text, re.S)
    embedded = None
    if not m:
        problems.append("index.html 未找到 cards-data JSON")
    else:
        embedded = json.loads(m.group(1).replace("<\\/", "</"))
        if len(embedded) != len(entries):
            problems.append(f"内嵌 JSON 条数 {len(embedded)} ≠ {len(entries)}")
        for got, exp in zip(embedded, entries):
            if got[0] != exp["cid"] or got[1] != exp["name"] or got[2] != exp["title"] or got[3] != exp["icon"]:
                problems.append(f"内嵌 JSON 与 entries 不一致：{got[:3]!r}")
                break

    # 3. 跳转目标存在：index.html 目标由内嵌 JSON 驱动（JS 拼 e[0]+"/index.html"），
    #    all_cards.html 为静态 href；两页各自的目标集合都必须等于 2236 cid 全集。
    idx_targets = {int(e[0]) for e in embedded} if embedded is not None else set()
    if idx_targets != set(cids):
        problems.append(f"index.html 内嵌 JSON 目标集合与 2236 cid 不一致")
    all_hrefs = {int(x) for x in HREF_RE.findall(all_text)}
    if all_hrefs != set(cids):
        problems.append(f"all_cards.html 跳转集合与 2236 cid 不一致"
                        f"（多 {len(all_hrefs - set(cids))}、少 {len(set(cids) - all_hrefs)}）")
    if not skip_disk:
        for src_name, targets in (("index.html", idx_targets), ("all_cards.html", all_hrefs)):
            bad = [c for c in targets if not (pages_dir / str(c) / "index.html").is_file()]
            if bad:
                problems.append(f"{src_name} 跳转目标缺失：{bad[:10]}")
        for link in ("all_cards.html", "README.md"):
            if not (pages_dir / link).is_file():
                problems.append(f"index.html 引用的 {link} 不存在")

    # 4. 头像引用：存在、无跨 cid 借图、缺图集合正确。
    #    index.html 的头像由 JS 按内嵌 JSON 的 icon 位动态产出（icon=1 → img art/<cid>/icon.png，
    #    icon=0 → 「未取得」占位），故按 JSON 位核对盘上文件；all_cards.html 为静态 DOM。
    if embedded is not None:
        icon1 = [int(e[0]) for e in embedded if e[3]]
        icon0 = sorted(int(e[0]) for e in embedded if not e[3])
        if not skip_disk:
            missing_file = [c for c in icon1 if not (pages_dir / "art" / str(c) / "icon.png").is_file()]
            if missing_file:
                problems.append(f"index.html（JSON icon=1）引用了不存在的头像：{missing_file[:10]}")
        if icon0 != sorted(MISSING_ICON):
            problems.append(f"index.html JSON 缺头像集合 {icon0} ≠ 任务卡缺 icon 清单 {sorted(MISSING_ICON)}")
        if 'av.src="art/"+e[0]+"/icon.png"' not in idx_text or "未取得" not in idx_text:
            problems.append("index.html JS 头像/「未取得」占位分支与预期不一致（应按 icon 位二选一，不借图）")
    img_cids = [int(x) for x in IMG_RE.findall(all_text)]
    if len(img_cids) != len(set(img_cids)):
        problems.append("all_cards.html 头像引用有重复")
    if not skip_disk:
        missing_file = [c for c in img_cids if not (pages_dir / "art" / str(c) / "icon.png").is_file()]
        if missing_file:
            problems.append(f"all_cards.html 引用了不存在的头像：{missing_file[:10]}")
    noimg = all_text.count('<span class="noimg"')
    if noimg != len(MISSING_ICON):
        problems.append(f"all_cards.html 「未取得」占位 {noimg} ≠ 缺 icon {len(MISSING_ICON)}")
    if any(str(c) + '/icon.png' in all_text for c in MISSING_ICON):
        problems.append("all_cards.html 为缺 icon 的 cid 引用了头像（应为占位）")

    # 5. 盘上缺图集合与迁移任务卡清单核对
    if not skip_disk:
        art_cids = {int(p.name) for p in (pages_dir / "art").iterdir() if p.is_dir()}
        for kind, expected in (("card", MISSING_CARD), ("whole", MISSING_WHOLE), ("icon", MISSING_ICON)):
            have = {c for c in art_cids if (pages_dir / "art" / str(c) / f"{kind}.png").is_file()}
            missing_on_disk = set(cids) - have
            if missing_on_disk != expected:
                problems.append(f"缺 {kind} 集合与任务卡清单不一致：盘上多/少 "
                                f"{sorted(missing_on_disk ^ expected)[:10]}")
        # 59103 全缺且不出现在任何头像引用
        if "59103/icon.png" in idx_text + all_text:
            problems.append("59103 不应有任何头像引用")

    return problems


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-root", type=Path, default=Path("."))
    ap.add_argument("--pages-dir", type=Path, default=DEFAULT_PAGES)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--execute", action="store_true", help="写入两页 HTML（缺省只提取＋检查）")
    args = ap.parse_args()

    root = args.input_root.resolve()
    pages_dir = (root / args.pages_dir).resolve() if not args.pages_dir.is_absolute() else args.pages_dir
    manifest = (root / args.manifest).resolve() if not args.manifest.is_absolute() else args.manifest

    entries, snapshot = load_entries(pages_dir, manifest)
    metrics = load_campaign_metrics(pages_dir)
    n_icon = sum(e["icon"] for e in entries)
    print(f"[OK] 提取 {len(entries)} 条（有头像 {n_icon}，缺 icon {sorted(set(e['cid'] for e in entries if not e['icon']))}）")
    print(f"[OK] 库快照：{snapshot}")
    print(f"[OK] 四联指标（campaign 汇总，与迁移任务卡核对一致）：A {metrics['A']}/{metrics['N_all']}，"
          f"整行确认 {metrics['whole_row_confirmed']}，原文A {metrics['original_A']}，C {metrics['C']}")

    html_index = build_index_html(entries, snapshot, metrics)
    html_all = build_all_cards_html(entries, snapshot, metrics)
    print(f"[OK] 构建体积：index.html {len(html_index):,} B，all_cards.html {len(html_all):,} B")

    # 预写检查不查盘（跳转目标已由 load_entries 逐一验证；写盘后有完整磁盘核对）
    problems = run_checks(pages_dir, entries, html_index, html_all, skip_disk=True)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        raise SystemExit(1)
    print("[OK] 自检通过（跳转/头像/占位/内嵌 JSON/缺图集合）")

    if args.execute:
        out_i = pages_dir / "index.html"
        out_a = pages_dir / "all_cards.html"
        out_i.write_bytes(html_index)
        out_a.write_bytes(html_all)
        # 写盘后用盘上文件再跑一遍完整自检（含磁盘存在性核对）
        problems = run_checks(pages_dir, entries, out_i.read_bytes(), out_a.read_bytes(), skip_disk=False)
        if problems:
            for p in problems:
                print(f"[FAIL] 写盘后核对：{p}")
            raise SystemExit(1)
        print(f"[OK] 已写入 {out_i}（{out_i.stat().st_size:,} B）与 {out_a}（{out_a.stat().st_size:,} B），写盘后自检通过")
    else:
        print("[DRY-RUN] 未写盘（加 --execute 写入）")


if __name__ == "__main__":
    main()
