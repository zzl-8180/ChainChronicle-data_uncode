# -*- coding: utf-8 -*-
"""角色技能数值成果包构建（版本化导出）：cc_skill_values_<日期>。

内容（白名单，与 output/character_skills/share_manifest_20261021/ 一致）：
  pages/<cid>/{card.json,index.html,receipt.json} × 2236
  pages/{index.html,all_cards.html,README.md}
  pages/art/<cid>/{card,whole,icon}.png × 6672
  ＋包根 README.md、manifest.json
默认排除 pages/_batch/（历史运行备份，约 37.8GB）、review/、inference_inventory/、
work/、raw/、scripts/、原始缓存与 APK、profiles/rules 原始输入。

动作：复制（保持相对路径结构）→ 逐文件 SHA-256 → 汇总 campaign/批次/Y.G. 指标 →
与上一版 manifest 逐文件比对（新增/变更/删除）→ 写 README.md 与 manifest.json →
压缩 zip（Deflate）→ 从 zip 读回逐条对账。只读源目录，不修改 pages 产物。

护栏（打包基线）：
  * 固定机器检查报告须为 PASS 且 campaign 签名与当前一致（--verify-report）；
  * 复制时校验 2236 张 receipt 的签名均等于当前 campaign 签名；
  * 复制结束后重读 campaign_latest，若 run/签名期间变化则中止（避免混批快照）。

用法（仓库根）：
  & .\\.venv\\Scripts\\python.exe -B scripts/release/build_skill_values_bundle.py
  可选：--bundle-id <id> --pages <dir> --out <dir> --zip <path>
        --prev-manifest <旧 manifest.json>（默认自动取上一版）
        --verify-report <verify_full_latest.json>
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ_CN = timezone(timedelta(hours=8))
CHUNK = 1 << 20
ZIP_LEVEL = 6

REQUIRED_CARD_FILES = ("card.json", "index.html", "receipt.json")
PAGES_TOP_FILES = ("index.html", "all_cards.html", "README.md")

BATCH_LABELS = {
    "pilot": "批1 试点 type1017",
    "b3": "批3 type8",
    "b4": "批4 条件扩展",
    "b5": "批5 跨表扩展",
    "b6": "批6 必殺バフ",
    "b7": "批7 共鳴",
    "b8": "批8 暴击 2012 链",
    "b9": "批9 敵デバフ",
    "b10": "批10 ability2003",
    "b11": "批11 自身增益 1095",
    "b12": "批12 1095 扩域",
    "b13": "批13 APK 扩域（99/2003）",
    "b14": "批14 APK 扩域（2012/1095，审查进行中）",
}
BATCH_ORDER = list(BATCH_LABELS)

# 进度文档当前块（docs/tasks/character-skills-progress.md，2026-10-22）中无法由
# card.json 直接重算的 Y.G. 口径常数；打包时如实标注来源与日期。
YG_UNIQUE_TEXT = 30
YG_REMAINING = 1796
ALL_REMAINING_DERIVED = 18010
REVIEW_STATE = (
    "批 1–13 定向审查闭合（PASS_WITH_EXPLICIT_SCOPE_LIMITS）；"
    "批 14（2012/1095 APK 域外扩域）实施完成、DeepSeek 定向审查进行中——"
    "该批 212 行/418 值行的披露文本可能随后续修复变化，但数值与判定已过固定机器检查"
)


def now_cn() -> str:
    return datetime.now(TZ_CN).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def copy_hashed(src: Path, dst: Path) -> tuple[int, str]:
    """复制并同流计算 SHA-256，返回 (bytes, sha256)。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    total = 0
    with src.open("rb") as fsrc, dst.open("wb") as fdst:
        for block in iter(lambda: fsrc.read(CHUNK), b""):
            h.update(block)
            fdst.write(block)
            total += len(block)
    shutil.copystat(src, dst)
    return total, h.hexdigest()


def collect_items(pages: Path) -> tuple[list[str], list[tuple[str, Path]]]:
    cids = sorted(d.name for d in pages.iterdir() if d.is_dir() and d.name.isdigit())
    if not cids:
        raise SystemExit(f"[FAIL] 未在 {pages} 找到角色页目录")
    items: list[tuple[str, Path]] = []
    for cid in cids:
        for name in REQUIRED_CARD_FILES:
            src = pages / cid / name
            if not src.is_file():
                raise SystemExit(f"[FAIL] 缺必需产物：{src}")
            items.append((f"pages/{cid}/{name}", src))
    for name in PAGES_TOP_FILES:
        src = pages / name
        if not src.is_file():
            raise SystemExit(f"[FAIL] 缺入口/说明文件：{src}")
        items.append((f"pages/{name}", src))
    art_root = pages / "art"
    if not art_root.is_dir():
        raise SystemExit(f"[FAIL] 缺立绘目录：{art_root}")
    for d in sorted(p for p in art_root.iterdir() if p.is_dir()):
        for f in sorted(p for p in d.iterdir() if p.is_file()):
            items.append((f"pages/art/{d.name}/{f.name}", f))
    return cids, items


def load_campaign(pages: Path) -> dict:
    latest = pages / "_batch" / "campaign_latest.json"
    pointer = json.loads(latest.read_text(encoding="utf-8"))
    report_path = pages / pointer["report"]  # campaign_latest 中 report 相对 pages/ 根
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return {
        "pointer": pointer["report"],
        "campaign_latest": "_batch/campaign_latest.json",
        "run_id": str(report_path.parent.name),
        "signature": report.get("signature"),
        "completed": report.get("completed"),
        "expected": report.get("expected"),
        "campaign_complete": report.get("campaign_complete"),
        "cohort_snapshots": report.get("cohort_snapshots", []),
        "summary": report.get("summary", {}),
        "entry_pages_snapshot": report.get("entry_pages"),
    }


def read_characters_csv(repo: Path) -> set[int]:
    path = repo / "output/character_skills/profiles/characters.csv"
    rows = list(csv.DictReader(io.StringIO(path.read_bytes().decode("utf-8-sig"))))
    return {int(r["cid"]) for r in rows if "Y.G." in (r.get("title") or "")}


def load_verify(repo: Path, path: Path, campaign: dict) -> dict:
    if not path.is_file():
        raise SystemExit(f"[FAIL] 缺固定机器检查报告：{path}（先跑 card_page_verify_full.py）")
    rep = json.loads(path.read_text(encoding="utf-8"))
    verdict = str(rep.get("verdict", "")).upper()
    sig = (rep.get("campaign") or {}).get("signature")
    if sig != campaign["signature"]:
        raise SystemExit(f"[FAIL] 机器检查报告签名 {str(sig)[:16]} ≠ 当前 campaign {campaign['signature'][:16]}")
    if verdict != "PASS":
        raise SystemExit(f"[FAIL] 固定机器检查未 PASS（verdict={verdict}）；按交付纪律不打包")
    checks = rep.get("checks", [])

    def ck(c: dict) -> str:
        # 检查器报告项名键为 "check"（旧版可能写作 "name"）
        return str(c.get("check") or c.get("name") or "")

    return {
        "report": str(path.relative_to(repo)).replace("\\", "/"),
        "generated_at": rep.get("generated_at"),
        "verdict": verdict,
        "checks_pass": sum(1 for c in checks if str(c.get("status", "")).upper() == "PASS"),
        "checks_total": len(checks),
        "campaign_run_id": (rep.get("campaign") or {}).get("run_id"),
        "campaign_signature": sig,
        "noted": {ck(c): len(c.get("noted") or []) for c in checks if c.get("noted")},
        "source_dereference_ok": next((c.get("ok") for c in checks if ck(c) == "source_dereference"), None),
        "inference_value_equality_ok": next((c.get("ok") for c in checks if ck(c) == "inference_value_equality"), None),
        "entry_pages": next((c.get("counters", {}).get("entry_status") for c in checks if ck(c) == "entry_pages"), None),
    }


def load_prev_manifest(repo: Path, explicit: str | None, bundle_id: str) -> dict | None:
    if explicit:
        p = (repo / explicit).resolve()
        if not p.is_file():
            raise SystemExit(f"[FAIL] 指定的上一版 manifest 不存在：{p}")
        return {"path": p, "data": json.loads(p.read_text(encoding="utf-8"))}
    cands = []
    for p in sorted((repo / "output/share_bundle").glob("cc_skill_values_*/manifest.json")):
        if p.parent.name == bundle_id:
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        cands.append((data.get("created_at", ""), p, data))
    if not cands:
        return None
    cands.sort(key=lambda x: x[0])
    return {"path": cands[-1][1], "data": cands[-1][2]}


def classify(rel: str) -> str:
    if rel == "README.md":
        return "bundle_readme"
    if rel.startswith("pages/art/"):
        return "art"
    if rel in ("pages/index.html", "pages/all_cards.html", "pages/README.md"):
        return "top"
    if rel.endswith("/card.json"):
        return "card_json"
    if rel.endswith("/index.html"):
        return "card_html"
    if rel.endswith("/receipt.json"):
        return "receipt"
    return "other"


def human_bytes(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n:,} B（{n / (1024 ** 3):.2f} GiB）"
    if n >= 1024 ** 2:
        return f"{n:,} B（{n / (1024 ** 2):.2f} MiB）"
    if n >= 1024:
        return f"{n:,} B（{n / 1024:.1f} KiB）"
    return f"{n:,} B"


def diff_against_previous(records: list[dict], prev: dict | None) -> dict | None:
    if not prev:
        return None
    pdata = prev["data"]
    old = {f["path"]: f for f in pdata.get("files", [])}
    new = {r["path"]: r for r in records}
    by_cat: dict[str, dict] = {}
    added = removed = changed = unchanged = 0
    for rel, rec in new.items():
        cat = classify(rel)
        slot = by_cat.setdefault(cat, {"added": 0, "removed": 0, "changed": 0, "unchanged": 0, "bytes_delta": 0})
        o = old.get(rel)
        if o is None:
            added += 1
            slot["added"] += 1
            slot["bytes_delta"] += rec["bytes"]
        elif o.get("bytes") != rec["bytes"] or o.get("sha256") != rec["sha256"]:
            changed += 1
            slot["changed"] += 1
            slot["bytes_delta"] += rec["bytes"] - o.get("bytes", 0)
        else:
            unchanged += 1
            slot["unchanged"] += 1
    for rel in set(old) - set(new):
        if rel == "README.md":
            continue  # 包根 README.md 每版重写，不计入差异统计
        removed += 1
        cat = classify(rel)
        slot = by_cat.setdefault(cat, {"added": 0, "removed": 0, "changed": 0, "unchanged": 0, "bytes_delta": 0})
        slot["removed"] += 1
        slot["bytes_delta"] -= old[rel].get("bytes", 0)
    by_cat.pop("bundle_readme", None)
    return {
        "previous_bundle_id": pdata.get("bundle_id"),
        "previous_created_at": pdata.get("created_at"),
        "previous_campaign": {
            "run_id": (pdata.get("campaign") or {}).get("run_id"),
            "signature": (pdata.get("campaign") or {}).get("signature"),
        },
        "previous_manifest": prev["path"].as_posix(),
        "bundle_readme_note": "包根 README.md 由每版构建重写，不计入逐文件差异统计",
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
        "by_category": by_cat,
    }


def build_readme(meta: dict) -> str:
    m = meta["metrics"]
    cat = meta["categories"]
    yg = meta["yg"]
    ch = meta.get("changes")
    lines: list[str] = []
    add = lines.append
    add(f"# 角色技能数值成果包 `{meta['bundle_id']}`")
    add("")
    add(f"构建时间：{meta['created_at']}（Asia/Shanghai）。数据面 `output/character_skills/pages/`，")
    add("2236 卡玩家视角页；本包含页面所需全部文件（每卡数据＋页面＋回执＋立绘），解压后可直接离线浏览。")
    add("")
    add("> 本包由项目侧本地构建并核对，**不发送、不上传、不公开**；对外发送由包持有者本人执行。")
    add("")
    add("## 1. 包内容（白名单）")
    add("")
    add("| 路径 | 文件数 | 字节 | 说明 |")
    add("|---|---:|---:|---|")
    add(f"| `pages/<cid>/card.json` | {cat['card_json']:,} | {cat['card_json_bytes']:,} | 每卡数据主体（行/答案/来源/证据/coverage） |")
    add(f"| `pages/<cid>/index.html` | {cat['card_html']:,} | {cat['card_html_bytes']:,} | 每卡离线页面（玩家视角版式） |")
    add(f"| `pages/<cid>/receipt.json` | {cat['receipt']:,} | {cat['receipt_bytes']:,} | 生成回执（run_id/签名/产物哈希） |")
    add(f"| `pages/index.html`、`pages/all_cards.html`、`pages/README.md` | {cat['top']} | {cat['top_bytes']:,} | 选择器页、全卡列表、数据模型与口径说明 |")
    add(f"| `pages/art/<cid>/*.png` | {cat['art']:,} | {cat['art_bytes']:,} | 立绘/全身/头像（card/whole/icon） |")
    add("| `manifest.json` | 1 | — | 机器可读清单（逐文件路径/字节/SHA-256/合计） |")
    add("| `README.md`（本文件） | 1 | — | 内容说明、口径、证据等级、断点与来源 |")
    add("")
    add(f"- `pages/` 子树：**{meta['pages_total']['files']:,} 个文件、{human_bytes(meta['pages_total']['bytes'])}**；")
    add("  包根另含 `README.md`、`manifest.json` 两个元文件。**精确合计以 `manifest.json` 的 `totals` 为准**。")
    add(f"- 压缩包：`{meta['zip_name']}`（ZIP，Deflate，compress level {ZIP_LEVEL}；压缩包内顶层目录 `{meta['bundle_id']}/`）。")
    add("")
    add("**默认排除**（与 `output/character_skills/share_manifest_20261021/` 一致）：`pages/_batch/`")
    add("（历史运行备份，约 171,971 文件 / 37.8GB，不删除、不入包）、`review/`、`inference_inventory/`、")
    add("`work/`、`raw/`、`scripts/`、原始缓存/APK 与 `profiles/`/`rules/` 原始输入。")
    add("")
    if ch:
        add("### 1.1 与上一版的差异（逐文件哈希对账）")
        add("")
        pv = ch["previous_campaign"]
        add(f"上一版 `{ch['previous_bundle_id']}`（{ch['previous_created_at']}，campaign `{pv.get('run_id')}`、")
        add(f"签名 `{str(pv.get('signature'))[:16]}…`）→ 本版 campaign `{meta['campaign']['run_id']}`、")
        add(f"签名 `{meta['campaign']['signature'][:16]}…`。逐文件比对：")
        add("")
        add(f"- **新增 {ch['added']} 个、删除 {ch['removed']} 个、变更 {ch['changed']:,} 个、未变 {ch['unchanged']:,} 个**")
        add("")
        add("| 类别 | 新增 | 删除 | 变更 | 未变 | 字节变化 |")
        add("|---|---:|---:|---:|---:|---:|")
        labels = {
            "card_json": "每卡 card.json",
            "card_html": "每卡 index.html",
            "receipt": "每卡 receipt.json",
            "top": "入口两页＋pages/README.md",
            "art": "立绘",
            "bundle_readme": "包根 README.md",
        }
        for key, label in labels.items():
            s = ch["by_category"].get(key)
            if not s:
                continue
            add(f"| {label} | {s['added']} | {s['removed']} | {s['changed']:,} | {s['unchanged']:,} | {s['bytes_delta']:+,} |")
        add("")
        add(f"- 包根 `README.md` 由每版构建重写，不计入上表逐文件差异；`manifest.json` 同理不入清单。")
        add(f"- 本版对应页面重建后 campaign：A {m['A']:,}（{m['A'] / m['N_all'] * 100:.1f}%）、C {m['C']:,}、")
        add(f"  整行推断 {m['inferred']:,}、整行确认 {m['confirmed']}、原文A {m['original_A']:,}（分母 {m['N_all']:,}）。")
        add(f"- 变化来源：{meta['batch_delta_note']}；立绘零变化（本版不重建图片）。")
        add("")
    add("## 2. 数据模型与口径入口")
    add("")
    add("`pages/README.md` 是本包的数据模型契约与口径权威说明（schema、字段语义、证据等级、逐答案来源、")
    add("审查队列口径、各推断批次 §13–§26）。消费要点：")
    add("")
    add("- 数值以 `raw_value` / `unit` 为准；`value`/`quantity_kind` 是显示文案与开放文本标签，**不当枚举、不当分组键**。")
    add("- 行分类 A/B/C：A＝有数值/公式的行，B＝部分，C＝无数字量化的未知行；序号与分母见各卡 `coverage`。")
    add(f"- 页面分母 **{m['N_all']:,} 行**（2236 卡）。A {m['A']:,}（{m['A'] / m['N_all'] * 100:.1f}%）、")
    add(f"  C {m['C']:,}（{m['C'] / m['N_all'] * 100:.1f}%）、原文A {m['original_A']:,}、整行确认 {m['confirmed']}、")
    add(f"  整行推断 {m['inferred']:,}。")
    add("- 行级 `evidence`（确认/推断/未知）与答案级 `numeric_evidence`/`association_evidence` 分开；")
    add("  **整行确认＝该行全部答案 `association_evidence` 均为「确认」**（R-01 口径）。")
    add("- 推断答案逐条带 `source`（六字段 `table/record_id/layer/source_key/json_pointer/field_path`）；")
    add("  批 4 条件增幅指向子记录（`link_kind:\"sub_effect\"`），其余按同记录继承（`inheritance:\"same_record_as_row_source\"`）；")
    add("  APK 扩域批（13/14）按载体所在层取值，不跨层合并。")
    add("- `rule_body_status`（= `rule_status` 兼容别名）**只描述规则本体**，本值的句内归属看")
    add("  `numeric_evidence`/`association_evidence`；不得因 `rule_body_status` 为「已确认」而把推断值当确认。")
    add("- 批 4 条件增幅与批 14 iParam0 职业过滤答案带 `condition_label`（条件原文逐字），页面首屏按")
    add("  「基础／条件：⟨逐字条件⟩」分组；基础句与条件增幅分列、不合乘、不跨记录合并数值。")
    add("")
    add("## 3. 证据等级与数值四层（图例）")
    add("")
    add("页面颜色即证据等级（与 `card.json` 字段一致）：")
    add("")
    add("| 显示档位 | `card.json` 口径 | 行数 | 颜色 |")
    add("|---|---|---:|---|")
    add(f"| 确认（记录级） | `association_evidence=确认` 且 `numeric_evidence=确认`，逐记录审定 | {m['confirmed_record']} | 绿（实线） |")
    add(f"| 确认（类型外推） | 同上但属冻结模板同类型推广、无逐记录人工审定 | {m['confirmed_by_type']} | 绿（带限定） |")
    add(f"| 推断 | 模板作用域推断层（批 1–14），规则本体确认、句内归属未获引擎原生核实 | {m['inferred']:,} | 橙 |")
    add(f"| 未知 | 无数字量化或无证据（原文保留，标灰；**不等同于零**） | {m['C']:,} | 灰 |")
    add("")
    add("数值按来源与确定性分**四层**，导出时原样保留、未做任何「清洗」：")
    add("")
    add("1. **原文数字**：数字在日文原文中逐字写出（`numeric_source=\"原文\"`、`numeric_evidence=\"确认\"`、")
    add("   `association_evidence=\"未知\"`）——数字可信，但对应哪个字段/参数未知，页面标「原文已写｜关联未知」。")
    add(f"2. **记录级确认**：`numeric_source=\"既有逐描述证据\"` 且关联人工审定（REVIEWED_RECORD，{m['confirmed_record']} 行，集中在 30236 基线）。")
    add(f"3. **类型外推确认**：冻结模板按同类型记录推广（BY_TYPE_EXTRAPOLATED，{m['confirmed_by_type']} 行），标注「确认（类型外推）」、限定可见，不降级。")
    add(f"4. **推断**：模板作用域推断层 {m['inference_answers']:,} 条答案 / {m['inferred']:,} 行（批 1–14），")
    add("   **推断值未逐记录人工审定**，不得改写为「确认」，不得用于对外宣称已确认数值。")
    add("")
    add("推断批次拆分（行级，`.coverage` 计数）：")
    add("")
    add("| 批次 | 晋级行 | 留 hint 行 |")
    add("|---|---:|---:|")
    for key in BATCH_ORDER:
        b = meta["batches"].get(key)
        if not b:
            continue
        add(f"| {BATCH_LABELS[key]} | {b['promoted']:,} | {b['hinted']:,} |")
    add(f"| **合计** | **{m['inferred']:,}** | — |")
    add("")
    add("## 4. 断点、未知与已知缺口（如实声明）")
    add("")
    add(f"- **C 行 {m['C']:,} 行（{m['C'] / m['N_all'] * 100:.1f}%）无数字量化**：多数为原文未写出数值、或仅有叙述性文本，")
    add("  页面保留原文并标灰，不填 0、不猜测。")
    add("- **推断层留 hint 的行**（有候选但证据不足，未晋级）逐行在 `coverage` 中以 `inference_b*/hinted` 键登记，")
    add("  各批 hint：pilot 4、b3 141、b4 135、b5 46、b6 622、b7 687、b8 233、b9 323、b10 90、b11 295、b13 8")
    add("  ——**同一行可能同时带多个批次键，不可直接相加**；hint ≠ 已确认，也 ≠ 永久未知。")
    add(f"- **批 14 审查状态**：{meta['review_state']}。")
    add(f"- **Y.G.（新卡）优先集**：{yg['cards']} 卡、{yg['rows']:,} 行；A {yg['A']:,}、推断 {yg['inferred']:,} 行／{yg['inferred_cards']} 卡、")
    add(f"  唯一 NFKC 正文 {yg['unique_text']}（据 `docs/tasks/character-skills-progress.md` 2026-10-22 当前块）、确认 {yg['confirmed']}；")
    add(f"  剩余待补目标 {yg['remaining']:,} 行（优先集口径）。")
    add("- **30236 基线 3 处显式登记缺失**：`description_effects.json` 自身登记 `present:false、raw_value:null`")
    add("  （`/bossinfo/bosspattern/1170/scost`、`/skilllist/6405/iParam0`×2），页面忠实保留，固定机器检查按 PASS-with-NOTED 单列，")
    add("  不是坏指针、也不修改原始输入。")
    add(f"- **缺立绘按 2236 卡分母如实回退**：card.png 缺 {meta['art_missing']['card']} 卡、whole.png 缺 {meta['art_missing']['whole']} 卡")
    add(f"  （{', '.join(meta['art_missing']['whole_cids'])}）、icon.png 缺 {meta['art_missing']['icon']} 卡（{', '.join(meta['art_missing']['icon_cids'])}）；")
    add("  缺图卡页面显示占位，不借用其他 cid 图片。")
    add("- **固定机器检查覆盖范围**（`card_page_verify_full.py`，10/10 PASS）：回执/签名、产物哈希、29 项数据依赖、")
    add("  行集合与 row_id 唯一、来源解引用、推断答案 source 覆盖、推断值与原记录精确相等、首屏 chip 颜色档位、")
    add("  campaign 四联对账、入口页一致性。**显式不检查**：`.data5` 原始字节范围/记录级 SHA 的字节级复核、")
    add("  折叠层文本逐字比对、浏览器渲染交互与视觉验收。")
    add("- 页面/数据未包含：战斗引擎最终结算、玩家解锁状态、等级 ATK/HP 的运行时公式（仅初始值与成长原值）；")
    add("  这些不在「一条描述→数值」交付范围内。")
    add("")
    add("## 5. 来源快照与 campaign")
    add("")
    add("| 项 | 值 |")
    add("|---|---|")
    add("| 数据快照 | `output/cache_full_20261015_v3/`（77 个缓存 data5 完整解码 JSON） |")
    add("| APK 主表 | `com.sega.chainchronicle` **5.6.2 / versionCode 56021**（Unity 2021.3.58f1），`output/base_master/` |")
    add("| 连续快照引用 | `output/cache_full_latest.json` → `cache_full_20261015_v3`；APK 与缓存分源保留，不按同号 ID 合并 |")
    add(f"| campaign run | `{meta['campaign']['run_id']}` |")
    add(f"| campaign 签名 | `{meta['campaign']['signature']}` |")
    add(f"| campaign 报告 | `{meta['campaign']['pointer']}`（相对 pages/ 根） |")
    add(f"| 完成度 | {meta['campaign']['completed']}/{meta['campaign']['expected']} 卡，campaign_complete={meta['campaign']['campaign_complete']} |")
    add(f"| 固定机器检查 | {meta['verify']['verdict']}（{meta['verify']['checks_pass']}/{meta['verify']['checks_total']} 项；{meta['verify']['report']}） |")
    add("")
    add("四个 cohort 快照（全部 MATCHING_SIGNATURE_SNAPSHOT）：")
    add("")
    add("| cohort | 完成/预期 | run |")
    add("|---|---:|---|")
    for c in meta["campaign"]["cohort_snapshots"]:
        run = c["report"].split("/")[-2]
        add(f"| {c['cohort']} | {c['completed']}/{c['expected']} | `{run}` |")
    add("")
    add("## 6. 版权与再分发边界（重要）")
    add("")
    add("- 页面中的**日语原文、角色名与立绘**为 SEGA 游戏资产（`com.sega.chainchronicle` 5.6.2），")
    add("  版权归原权利人。本包**仅供接收方开发参考**；再分发、公开、商用或二次发布需由接收方另行评估合规性并取得必要授权。")
    add("- 数值解释、证据标注、页面与清单为本项目整理成果，引用时请保留证据等级标注（尤其「推断」与")
    add("  「确认（类型外推）」），不得去标注后当作官方/已确认数值传播。")
    add("- 本包不含账号凭据、设备私钥、个人数据或原始手机缓存；不含 APK 与原始 `.data5` 输入。")
    add("")
    add("## 7. 使用与校验")
    add("")
    add(f"1. 解压 `{meta['zip_name']}`，用浏览器直接打开 `pages/index.html`（选择器）或")
    add("   `pages/all_cards.html`（全卡列表）；单卡页面 `pages/<cid>/index.html` 可离线打开，立绘用相对路径 `../art/<cid>/`。")
    add("2. 机器读取：以 `pages/<cid>/card.json` 为主体；字段与口径见 `pages/README.md`。")
    add("3. 校验：`manifest.json` 的 `files[]` 给出每个文件相对路径、字节数与 SHA-256，`totals` 为合计。")
    add("   PowerShell 示例：`Get-FileHash -Algorithm SHA256 pages\\30236\\card.json`，与清单条目比对；")
    add("   或按清单逐条重算并统计不一致数（应为 0）。")
    add("4. 清单 `manifest.json` 不含自身哈希（无法自指）；对外校验以 `files[]` 覆盖的文件为准。")
    add("")
    add("## 8. 机器可读清单结构（manifest.json）")
    add("")
    add("`bundle_id`、`created_at`、`source`（缓存/APK 快照）、`campaign`（run/签名/cohorts/入口页实时检查）、")
    add("`review_state`（批次审查状态）、`metrics`（四联＋推断答案数）、`inference_batches`（逐批晋级/hint）、")
    add("`yg_metrics`、`evidence_levels`、`categories`、`art_missing`、`changes_vs_previous`（与上一版逐文件差异）、")
    add("`fixed_machine_check`、`files[]`（`path`/`bytes`/`sha256`，按路径排序）、`totals`、`excluded`。")
    add("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="output/character_skills/pages")
    ap.add_argument("--bundle-id", default=None, help="默认 cc_skill_values_<YYYYMMDD>")
    ap.add_argument("--out", default=None)
    ap.add_argument("--zip", default=None)
    ap.add_argument("--check-out", default=None)
    ap.add_argument("--prev-manifest", default=None)
    ap.add_argument("--verify-report", default="work/character_skills_phase2_20261021/verify_full_latest.json")
    ap.add_argument("--force", action="store_true", help="允许覆盖已存在的输出目录/压缩包")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    pages = (repo / args.pages).resolve()
    bundle_id = args.bundle_id or f"cc_skill_values_{datetime.now(TZ_CN).strftime('%Y%m%d')}"
    out = (repo / args.out).resolve() if args.out else (repo / "output/share_bundle" / bundle_id)
    zip_path = (repo / args.zip).resolve() if args.zip else (repo / "output/share_bundle" / f"{bundle_id}.zip")
    check_path = (repo / (args.check_out or f"work/{bundle_id}_build/check.json")).resolve()

    if not pages.is_dir():
        print(f"[FAIL] pages 目录不存在：{pages}")
        return 2
    if out.exists() and not args.force:
        print(f"[FAIL] 输出目录已存在：{out}（如需重建请加 --force）")
        return 2
    if zip_path.exists() and not args.force:
        print(f"[FAIL] 压缩包已存在：{zip_path}（如需重建请加 --force）")
        return 2

    t0 = time.time()
    print("[0/6] 基线护栏：campaign／固定机器检查")
    campaign = load_campaign(pages)
    verify = load_verify(repo, (repo / args.verify_report).resolve(), campaign)
    print(f"      campaign {campaign['run_id']} 签名 {campaign['signature'][:16]}…；验证 {verify['verdict']} {verify['checks_pass']}/{verify['checks_total']}")

    print(f"[1/6] 收集白名单文件：{pages}")
    cids, items = collect_items(pages)
    yg_cids = read_characters_csv(repo)
    print(f"      角色页 {len(cids)}；待复制文件 {len(items):,}（其中 Y.G. 卡 {len(yg_cids)}）")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    print("[2/6] 复制并计算 SHA-256（同时解析 card.json/receipt.json 汇总指标）")
    records: list[dict] = []
    lib = dict(rows=0, A=0, C=0, origA=0, conf=0, inf=0, rec=0, bytype=0)
    yg = dict(rows=0, A=0, C=0, origA=0, conf=0, inf=0, rec=0, bytype=0, inferred_cards=0)
    batches: dict[str, dict] = {}
    answers_inf = 0
    receipt_sig_mismatch = 0
    for i, (rel, src) in enumerate(items, 1):
        dst = out / rel
        size, digest = copy_hashed(src, dst)
        records.append({"path": rel, "bytes": size, "sha256": digest})
        if rel.endswith("/card.json"):
            card = json.loads(dst.read_text(encoding="utf-8"))
            cid = int(card.get("cid", Path(rel).parts[1]))
            s, cov = card["summary"], card.get("coverage", {})
            targets = [lib] + ([yg] if cid in yg_cids else [])
            card_inf = s["whole_row_inferred"]["count"]
            for agg in targets:
                agg["rows"] += s["N_all"]
                agg["A"] += s["A"]["count"]
                agg["C"] += s["C"]["count"]
                agg["origA"] += s["original_A"]["count"]
                agg["conf"] += s["whole_row_confirmed"]["count"]
                agg["inf"] += card_inf
                agg["rec"] += s["whole_row_confirmed_scopes"]["record"]
                agg["bytype"] += s["whole_row_confirmed_scopes"]["by_type_extrapolated"]
            if cid in yg_cids and card_inf > 0:
                yg["inferred_cards"] += 1
            for key, val in cov.items():
                if not key.startswith("inference_"):
                    continue
                rest = key[len("inference_"):]
                batch_key, _, kind = rest.rpartition("_")
                if kind not in ("promoted", "hinted") or batch_key not in BATCH_LABELS:
                    continue
                slot = batches.setdefault(batch_key, {"promoted": 0, "hinted": 0})
                slot[kind] += val
            for g in card.get("groups", []):
                for sk in g.get("skills", []):
                    for row in sk.get("rows", []):
                        for a in row.get("answers", []):
                            if a.get("numeric_evidence") == "推断":
                                answers_inf += 1
        elif rel.endswith("/receipt.json"):
            rec = json.loads(dst.read_text(encoding="utf-8"))
            if rec.get("signature") != campaign["signature"]:
                receipt_sig_mismatch += 1
        if i % 1000 == 0 or i == len(items):
            print(f"      {i:,}/{len(items):,} 文件（{sum(r['bytes'] for r in records):,} B）")

    if receipt_sig_mismatch:
        print(f"[FAIL] {receipt_sig_mismatch} 张卡 receipt 签名 ≠ 当前 campaign 签名；快照可能正在重建，中止")
        return 5
    campaign_after = load_campaign(pages)
    if campaign_after["signature"] != campaign["signature"] or campaign_after["run_id"] != campaign["run_id"]:
        print(f"[FAIL] 复制期间 campaign 发生变化（{campaign['run_id']} → {campaign_after['run_id']}）；中止")
        return 5
    print(f"      receipt 签名 2236/2236 与 campaign 一致；批次键 {len(batches)} 个；推断答案 {answers_inf:,}")

    if lib["A"] != campaign["summary"]["A"]["count"] or lib["inf"] != campaign["summary"]["whole_row_inferred"]["count"]:
        print(f"[FAIL] 页面重聚合（A={lib['A']} / 推断={lib['inf']}）与 campaign_report 不一致；中止")
        return 5
    print(f"      页面重聚合与 campaign 一致：A {lib['A']:,} / 推断 {lib['inf']:,} / C {lib['C']:,}")

    records.sort(key=lambda r: r["path"])
    rec_card_json = [r for r in records if r["path"].endswith("/card.json")]
    rec_card_html = [r for r in records if r["path"].endswith("/index.html") and r["path"].count("/") == 2]
    rec_receipt = [r for r in records if r["path"].endswith("/receipt.json")]
    rec_top = [r for r in records if r["path"] in {f"pages/{n}" for n in PAGES_TOP_FILES}]
    rec_art = [r for r in records if r["path"].startswith("pages/art/")]
    categories = {
        "card_json": len(rec_card_json), "card_json_bytes": sum(r["bytes"] for r in rec_card_json),
        "card_html": len(rec_card_html), "card_html_bytes": sum(r["bytes"] for r in rec_card_html),
        "receipt": len(rec_receipt), "receipt_bytes": sum(r["bytes"] for r in rec_receipt),
        "top": len(rec_top), "top_bytes": sum(r["bytes"] for r in rec_top),
        "art": len(rec_art), "art_bytes": sum(r["bytes"] for r in rec_art),
    }
    if categories["card_json"] != len(cids) or categories["receipt"] != len(cids):
        print(f"[FAIL] 分类计数异常：{categories}")
        return 3

    art_dirs = {p.name: {f.name for f in p.iterdir() if f.is_file()} for p in (pages / "art").iterdir() if p.is_dir()}
    missing_card = sorted((c for c in cids if "card.png" not in art_dirs.get(c, set())), key=int)
    missing_whole = sorted((c for c in cids if "whole.png" not in art_dirs.get(c, set())), key=int)
    missing_icon = sorted((c for c in cids if "icon.png" not in art_dirs.get(c, set())), key=int)
    art_missing = {
        "card": len(missing_card), "card_cids": missing_card,
        "whole": len(missing_whole), "whole_cids": missing_whole,
        "icon": len(missing_icon), "icon_cids": missing_icon,
    }

    prev = load_prev_manifest(repo, args.prev_manifest, bundle_id)
    changes = diff_against_previous(records, prev)
    if changes:
        print(f"[3/6] 与上一版差异：新增 {changes['added']} / 删除 {changes['removed']} / 变更 {changes['changed']:,} / 未变 {changes['unchanged']:,}")

    pages_total = {"files": len(records), "bytes": sum(r["bytes"] for r in records)}
    promoted_sum = sum(b["promoted"] for b in batches.values())
    metrics = {
        "N_all": campaign["summary"]["N_all"],
        "A": lib["A"], "C": lib["C"], "original_A": lib["origA"],
        "confirmed": lib["conf"], "confirmed_record": lib["rec"], "confirmed_by_type": lib["bytype"],
        "inferred": lib["inf"], "inference_answers": answers_inf,
        "promoted_sum_check": promoted_sum,
    }
    meta = {
        "bundle_id": bundle_id,
        "created_at": now_cn(),
        "source": {
            "repo_relative": "output/character_skills/pages",
            "cache_snapshot": "output/cache_full_20261015_v3/",
            "cache_pointer": "output/cache_full_latest.json",
            "apk": {
                "package": "com.sega.chainchronicle", "version_name": "5.6.2",
                "version_code": 56021, "unity": "2021.3.58f1", "base_master": "output/base_master/",
            },
            "roster": f"{len(cids)} 个 cid（卡片目录）",
        },
        "campaign": {
            "run_id": campaign["run_id"], "signature": campaign["signature"],
            "completed": campaign["completed"], "expected": campaign["expected"],
            "campaign_complete": campaign["campaign_complete"],
            "pointer": campaign["pointer"],
            "cohort_snapshots": campaign["cohort_snapshots"],
            "entry_pages_snapshot": campaign["entry_pages_snapshot"],
            "entry_pages_note": "campaign_report 内嵌 entry_pages 为写报告时快照（可能 STALE）；"
                                "实时一致性以 fixed_machine_check.entry_pages 为准",
        },
        "review_state": REVIEW_STATE,
        "metrics": metrics,
        "batches": batches,
        "yg": {
            "cards": len(yg_cids), "rows": yg["rows"], "A": yg["A"], "C": yg["C"],
            "original_A": yg["origA"], "confirmed": yg["conf"], "inferred": yg["inf"],
            "inferred_cards": yg["inferred_cards"],
            "unique_text": YG_UNIQUE_TEXT, "remaining": YG_REMAINING,
            "remaining_all_derived": ALL_REMAINING_DERIVED,
            "source": "docs/tasks/character-skills-progress.md 当前块（2026-10-22）",
        },
        "evidence_levels": [
            {"key": "确认", "scope": "REVIEWED_RECORD", "rows": lib["rec"], "color": "绿（实线）"},
            {"key": "确认（类型外推）", "scope": "BY_TYPE_EXTRAPOLATED", "rows": lib["bytype"], "color": "绿（带限定）"},
            {"key": "推断", "scope": "TEMPLATE_INFERENCE", "rows": lib["inf"], "color": "橙",
             "note": "批 1–14；批 14 审查进行中；推断值未逐记录人工审定，不得当确认"},
            {"key": "未知", "scope": "UNKNOWN", "rows": lib["C"], "color": "灰"},
        ],
        "categories": categories,
        "art_missing": art_missing,
        "pages_total": pages_total,
        "verify": verify,
        "changes": changes,
        "zip_name": zip_path.name,
        "excluded": [
            "output/character_skills/pages/_batch/（历史运行备份，约 171,971 文件 / 37.8GB，不删除、不入包）",
            "output/character_skills/review/",
            "output/character_skills/inference_inventory/",
            "work/",
            "raw/",
            "scripts/（含生成器与检查器，原始开发仓库可另行提供）",
            "profiles/、rules/、links/ 原始输入",
            "原始 APK 与 .data5 缓存（由包持有者自备）",
        ],
    }
    b8_14 = sum(batches[k]["promoted"] for k in BATCH_ORDER if k not in ("pilot", "b3", "b4", "b5", "b6", "b7") and k in batches)
    b10_14 = sum(batches[k]["promoted"] for k in ("b10", "b11", "b12", "b13", "b14") if k in batches)
    meta["batch_delta_note"] = f"批 10–14 晋级 {b10_14:,} 行、批 8–14 合计 {b8_14:,} 行（批 14 审查进行中）"

    print("[4/6] 写 README.md 与 manifest.json")
    readme_path = out / "README.md"
    readme_path.write_text(build_readme(meta), encoding="utf-8", newline="\n")
    readme_sha = sha256_file(readme_path)
    manifest_files = records + [{"path": "README.md", "bytes": readme_path.stat().st_size, "sha256": readme_sha}]
    manifest_files.sort(key=lambda r: r["path"])
    totals = {"files": len(manifest_files), "bytes": sum(r["bytes"] for r in manifest_files)}
    manifest = {
        "bundle_id": bundle_id,
        "created_at": meta["created_at"],
        "generator": "scripts/release/build_skill_values_bundle.py",
        "scope_note": "组合X＝全量页面包（pages 全量＋入口两页＋pages/README.md＋art 立绘）；_batch 默认排除",
        "source": meta["source"],
        "campaign": meta["campaign"],
        "review_state": meta["review_state"],
        "metrics": metrics,
        "inference_batches": {k: {"label": BATCH_LABELS[k], **batches[k]} for k in BATCH_ORDER if k in batches},
        "yg_metrics": meta["yg"],
        "evidence_levels": meta["evidence_levels"],
        "categories": categories,
        "art_missing": art_missing,
        "pages_total": pages_total,
        "changes_vs_previous": changes,
        "fixed_machine_check": verify,
        "files": manifest_files,
        "totals": totals,
        "manifest_self_note": "manifest.json 自身无法自指哈希，不计入 files/totals；校验以 files[] 为范围",
        "excluded": meta["excluded"],
        "license_note": (
            "日语原文与立绘为 SEGA 游戏资产，仅供接收方开发参考；再分发/公开/商用需另行评估合规性。"
            "推断值未逐记录人工审定，不得改写为确认。"
        ),
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    manifest_bytes = manifest_path.stat().st_size
    print(f"      manifest.json {manifest_bytes:,} B；files {totals['files']:,}；合计 {totals['bytes']:,} B")

    print(f"[5/6] 压缩 zip（Deflate level {ZIP_LEVEL}）→ {zip_path}")
    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    zip_entries = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=ZIP_LEVEL, allowZip64=True) as zf:
        for p in sorted(out.rglob("*")):
            if not p.is_file():
                continue
            zf.write(p, arcname=f"{bundle_id}/{p.relative_to(out).as_posix()}")
            zip_entries += 1
            if zip_entries % 2000 == 0:
                print(f"      {zip_entries:,} 条目已写入")

    print("[6/6] 从 zip 读回逐条对账")
    expected = {f["path"]: f for f in manifest_files}
    expected["manifest.json"] = {"path": "manifest.json", "bytes": manifest_bytes, "sha256": sha256_file(manifest_path)}
    seen: set[str] = set()
    mismatched: list[dict] = []
    total_read = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in [n for n in zf.namelist() if not n.endswith("/")]:
            rel = name[len(bundle_id) + 1:]
            seen.add(rel)
            info = zf.getinfo(name)
            h = hashlib.sha256()
            with zf.open(name, "r") as f:
                for block in iter(lambda: f.read(CHUNK), b""):
                    h.update(block)
                    total_read += len(block)
            exp = expected.get(rel)
            if exp is None:
                mismatched.append({"path": rel, "problem": "unexpected_in_zip"})
            elif info.file_size != exp["bytes"] or h.hexdigest() != exp["sha256"]:
                mismatched.append({"path": rel, "problem": "size_or_sha_mismatch"})
    missing_in_zip = sorted(set(expected) - seen)
    zip_bytes = zip_path.stat().st_size
    zip_sha = sha256_file(zip_path)
    result = {
        "bundle_id": bundle_id,
        "checked_at": now_cn(),
        "zip": str(zip_path.relative_to(repo)).replace("\\", "/"),
        "zip_name": zip_path.name,
        "zip_bytes": zip_bytes,
        "zip_sha256": zip_sha,
        "zip_entries": len(seen),
        "manifest_files": totals["files"],
        "manifest_bytes_total": totals["bytes"],
        "expected_zip_entries": len(expected),
        "unexpected_in_zip": [m for m in mismatched if m["problem"] == "unexpected_in_zip"],
        "missing_in_zip": missing_in_zip,
        "mismatched": [m for m in mismatched if m["problem"] != "unexpected_in_zip"],
        "reconcile_pass": not mismatched and not missing_in_zip and len(seen) == len(expected),
        "bytes_read_back": total_read,
        "elapsed_seconds": round(time.time() - t0, 1),
        "campaign_run": campaign["run_id"],
        "campaign_signature": campaign["signature"],
        "fixed_machine_check": f"{verify['report']}（{verify['verdict']} {verify['checks_pass']}/{verify['checks_total']}）",
        "changes_vs_previous": changes,
        "metrics": metrics,
        "art_missing": {k: v for k, v in art_missing.items() if not k.endswith("_cids")},
    }
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    print("")
    print(f"[DONE] 包目录：{out}")
    print(f"       压缩包：{zip_path}（{human_bytes(zip_bytes)}，SHA-256 {zip_sha}）")
    print(f"       zip 条目 {len(seen):,}（README.md 计入 files；manifest.json 另计 1）")
    print(f"       manifest files={totals['files']:,} bytes={totals['bytes']:,}；对账={'PASS' if result['reconcile_pass'] else 'FAIL'}")
    if changes:
        print(f"       较上一版：新增 {changes['added']} / 删除 {changes['removed']} / 变更 {changes['changed']:,} / 未变 {changes['unchanged']:,}")
    if not result["reconcile_pass"]:
        print(f"[FAIL] 对账失败：missing={missing_in_zip[:5]} mismatched={result['mismatched'][:5]} unexpected={result['unexpected_in_zip'][:5]}")
        return 4
    print(f"       对账明细：{check_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
