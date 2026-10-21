# -*- coding: utf-8 -*-
"""角色技能数值成果包构建：cc_skill_values_20261021（组合X＝全量页面包）。

内容（白名单，与 output/character_skills/share_manifest_20261021/ 一致）：
  pages/<cid>/{card.json,index.html,receipt.json} × 2236
  pages/{index.html,all_cards.html,README.md}
  pages/art/<cid>/{card,whole,icon}.png × 6672
  ＋包根 README.md、manifest.json
默认排除 pages/_batch/（历史运行备份，约 37.8GB）、review/、inference_inventory/、
work/、raw/、scripts/、原始缓存与 APK、profiles/rules 原始输入。

动作：复制（保持相对路径结构）→ 逐文件 SHA-256 → 写 manifest.json（含合计）→
写 README.md → 压缩 zip（Deflate）→ 从 zip 重新读回逐条对账（路径/字节/SHA-256）。
只读源目录，不修改 pages 产物。发送/上传/公开不在本脚本范围。

用法（仓库根）：
  & .\\.venv\\Scripts\\python.exe -B scripts/release/build_skill_values_bundle.py
  可选：--pages <dir> --out <dir> --zip <path> --force
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

BUNDLE_ID = "cc_skill_values_20261021"
TZ_CN = timezone(timedelta(hours=8))
CHUNK = 1 << 20
ZIP_LEVEL = 6

REQUIRED_CARD_FILES = ("card.json", "index.html", "receipt.json")
PAGES_TOP_FILES = ("index.html", "all_cards.html", "README.md")

EVIDENCE_LEVELS = [
    {
        "key": "确认",
        "scope": "REVIEWED_RECORD",
        "label_zh": "确认（记录级）",
        "color": "绿（实线）",
        "meaning": "逐记录审定的既有逐描述证据（例如 30236 基线），数值与字段关联均经人工核对。",
        "count_rows": 18,
    },
    {
        "key": "确认（类型外推）",
        "scope": "BY_TYPE_EXTRAPOLATED",
        "label_zh": "确认（类型外推）",
        "color": "绿（带限定）",
        "meaning": "冻结模板按同类型记录推广，规则本体确认，但无逐记录人工审定；渲染层显式标注限定。",
        "count_rows": 248,
    },
    {
        "key": "推断",
        "scope": "TEMPLATE_INFERENCE",
        "label_zh": "推断",
        "color": "橙",
        "meaning": (
            "模板作用域推断层（批 1–9）：规则本体经确认，句内归属为数据侧结构对应，"
            "引擎侧装载路径多无原生核实；逐行标注批次来源，多候选一律留 hint。"
            "推断值未逐记录人工审定，不得当确认使用。"
        ),
        "count_rows": 2461,
    },
    {
        "key": "未知",
        "scope": "UNKNOWN",
        "label_zh": "未知",
        "color": "灰",
        "meaning": "无数值量化或无证据可给，页面保留原文并如实标灰；不等同于零。",
        "count_rows": 25079,
    },
]


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
    # campaign_latest 中的 report 路径相对 pages/ 根
    report_path = pages / pointer["report"]
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return {
        "campaign_latest": "_batch/campaign_latest.json",
        "campaign_report": pointer["report"],
        "run_id": str(report_path.parent.name),
        "signature": report.get("signature"),
        "completed": report.get("completed"),
        "expected": report.get("expected"),
        "campaign_complete": report.get("campaign_complete"),
        "completed_text": {
            "A": report["summary"]["A"]["count"],
            "A_denominator": report["summary"]["A"]["denominator"],
            "whole_row_confirmed": report["summary"]["whole_row_confirmed"]["count"],
            "whole_row_confirmed_scopes": report["summary"]["whole_row_confirmed_scopes"],
            "original_A": report["summary"]["original_A"]["count"],
            "C": report["summary"]["C"]["count"],
            "whole_row_inferred": report["summary"]["whole_row_inferred"]["count"],
            "N_all": report["summary"]["N_all"],
            "whole_row_inference_batches": {
                "pilot_type1017": 337,
                "b3_type8": 40,
                "b4_cond": 37,
                "b5_xtable": 211,
                "b6_bossbuff": 1349,
                "b7_sympathy": 106,
                "b8_crit2012": 346,
                "b9_debuff": 35,
            },
        },
        "cohort_snapshots": report.get("cohort_snapshots", []),
    }


def human_bytes(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n:,} B（{n / (1024 ** 3):.2f} GiB）"
    if n >= 1024 ** 2:
        return f"{n:,} B（{n / (1024 ** 2):.2f} MiB）"
    if n >= 1024:
        return f"{n:,} B（{n / 1024:.1f} KiB）"
    return f"{n:,} B"


def build_readme(meta: dict) -> str:
    m = meta["campaign"]["completed_text"]
    cat = meta["categories"]
    missing = meta["art_missing"]
    lines = []
    add = lines.append
    add(f"# 角色技能数值成果包 `{BUNDLE_ID}`")
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
    add(f"- 压缩包：`{meta['zip_name']}`（ZIP，Deflate，compress level {ZIP_LEVEL}；压缩包内顶层目录 `{BUNDLE_ID}/`）。")
    add("")
    add("**默认排除**（与 `output/character_skills/share_manifest_20261021/` 一致）：`pages/_batch/`")
    add("（历史运行备份，约 171,971 文件 / 37.8GB，不删除、不入包）、`review/`、`inference_inventory/`、")
    add("`work/`、`raw/`、`scripts/`、原始缓存/APK 与 `profiles/`/`rules/` 原始输入。")
    add("")
    add("## 2. 数据模型与口径入口")
    add("")
    add("`pages/README.md` 是本包的数据模型契约与口径权威说明（schema、字段语义、证据等级、逐答案来源、")
    add("审查队列口径）。消费要点：")
    add("")
    add("- 数值以 `raw_value` / `unit` 为准；`value`/`quantity_kind` 是显示文案与开放文本标签，**不当枚举、不当分组键**。")
    add("- 行分类 A/B/C：A＝有数值/公式的行，B＝部分，C＝无数字量化的未知行；序号与分母见各卡 `coverage`。")
    add(f"- 页面分母 **{m['N_all']:,} 行**（2236 卡）。A {m['A']:,}（{m['A']/m['A_denominator']*100:.1f}%）、")
    add(f"  C {m['C']:,}（{m['C']/m['A_denominator']*100:.1f}%）、原文A {m['original_A']:,}、整行确认 {m['whole_row_confirmed']}、")
    add(f"  整行推断 {m['whole_row_inferred']:,}。")
    add("- 行级 `evidence`（确认/推断/未知）与答案级 `numeric_evidence`/`association_evidence` 分开；")
    add("  **整行确认＝该行全部答案 `association_evidence` 均为「确认」**（R-01 口径）。")
    add("- 推断答案逐条带 `source`（六字段 `table/record_id/layer/source_key/json_pointer/field_path`）；")
    add("  批 4 条件增幅指向子记录（`link_kind:\"sub_effect\"`），其余按同记录继承（`inheritance:\"same_record_as_row_source\"`）。")
    add("- `rule_body_status`（= `rule_status` 兼容别名）**只描述规则本体**，本值的句内归属看")
    add("  `numeric_evidence`/`association_evidence`；不得因 `rule_body_status` 为「已确认」而把推断值当确认。")
    add("- 批 4 条件增幅答案带 `condition_label`（条件原文逐字），页面首屏按「基础／条件：⟨逐字条件⟩」分组；")
    add("  基础句与条件增幅分列、不合乘、不跨记录合并数值。")
    add("")
    add("## 3. 证据等级与数值四层（图例）")
    add("")
    add("页面颜色即证据等级（与 `card.json` 字段一致）：")
    add("")
    add("| 显示档位 | `card.json` 口径 | 行数 | 颜色 |")
    add("|---|---|---:|---|")
    add("| 确认（记录级） | `association_evidence=确认` 且 `numeric_evidence=确认`，逐记录审定 | 18 | 绿（实线） |")
    add("| 确认（类型外推） | 同上但属冻结模板同类型推广、无逐记录人工审定 | 248 | 绿（带限定） |")
    add("| 推断 | 模板作用域推断层（批 1–9），规则本体确认、句内归属未获引擎原生核实 | 2,461 | 橙 |")
    add("| 未知 | 无数字量化或无证据（原文保留，标灰；**不等同于零**） | 25,079 | 灰 |")
    add("")
    add("数值按来源与确定性分**四层**，导出时原样保留、未做任何「清洗」：")
    add("")
    add("1. **原文数字**：数字在日文原文中逐字写出（`numeric_source=\"原文\"`、`numeric_evidence=\"确认\"`、")
    add("   `association_evidence=\"未知\"`）——数字可信，但对应哪个字段/参数未知，页面标「原文已写｜关联未知」。")
    add("2. **记录级确认**：`numeric_source=\"既有逐描述证据\"` 且关联人工审定（REVIEWED_RECORD，目前 18 行，集中在 30236 基线）。")
    add("3. **类型外推确认**：冻结模板按同类型记录推广（BY_TYPE_EXTRAPOLATED，248 行），标注「确认（类型外推）」、限定可见，不降级。")
    add("4. **推断**：模板作用域推断层 8,162 条答案 / 2,461 行（批 1–9），**推断值未逐记录人工审定**，")
    add("   不得改写为「确认」，不得用于对外宣称已确认数值。")
    add("")
    add("## 4. 断点、未知与已知缺口（如实声明）")
    add("")
    add(f"- **C 行 {m['C']:,} 行（{m['C']/m['A_denominator']*100:.1f}%）无数字量化**：多数为原文未写出数值、或仅有叙述性文本，")
    add("  页面保留原文并标灰，不填 0、不猜测。")
    add("- **推断层留 hint 的行**（有候选但证据不足，未晋级）逐行在 `coverage` 中以 `inference_b*/hinted` 键登记；")
    add("  各批 hint 计数为 pilot 4、b3 141、b4 135、b5 46、b6 788、b7 687、b8 428、b9 938——**同一行可能同时带多个批次键，")
    add("  不可直接相加**；hint ≠ 已确认，也 ≠ 永久未知。")
    add(f"- **Y.G.（新卡）优先集**：109 卡、5,805 行；推断累计 448 行／108 卡／唯一 NFKC 正文 25；")
    add("  剩余待补目标 1,896 行（优先集口径）。")
    add("- **30236 基线 3 处显式登记缺失**：`description_effects.json` 自身登记 `present:false、raw_value:null`")
    add("  （`/bossinfo/bosspattern/1170/scost`、`/skilllist/6405/iParam0`×2），页面忠实保留，固定机器检查按 PASS-with-NOTED 单列，")
    add("  不是坏指针、也不修改原始输入。")
    add(f"- **缺立绘按 2236 卡分母如实回退**：card.png 缺 {missing['card']} 卡、whole.png 缺 {missing['whole']} 卡")
    add(f"  （{', '.join(missing['whole_cids'])}）、icon.png 缺 {missing['icon']} 卡（{', '.join(missing['icon_cids'])}）；")
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
    add(f"| campaign 报告 | `{meta['campaign']['campaign_report']}`（相对 pages/ 根） |")
    add(f"| 完成度 | {meta['campaign']['completed']}/{meta['campaign']['expected']} 卡，campaign_complete={meta['campaign']['campaign_complete']} |")
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
    add("1. 解压 `" + meta["zip_name"] + "`，用浏览器直接打开 `pages/index.html`（选择器）或")
    add("   `pages/all_cards.html`（全卡列表）；单卡页面 `pages/<cid>/index.html` 可离线打开，立绘用相对路径 `../art/<cid>/`。")
    add("2. 机器读取：以 `pages/<cid>/card.json` 为主体；字段与口径见 `pages/README.md`。")
    add("3. 校验：`manifest.json` 的 `files[]` 给出每个文件相对路径、字节数与 SHA-256，`totals` 为合计。")
    add("   PowerShell 示例：`Get-FileHash -Algorithm SHA256 pages\\30236\\card.json`，与清单条目比对；")
    add("   或按清单逐条重算并统计不一致数（应为 0）。")
    add("4. 清单 `manifest.json` 不含自身哈希（无法自指）；对外校验以 `files[]` 覆盖的文件为准。")
    add("")
    add("## 8. 机器可读清单结构（manifest.json）")
    add("")
    add("`bundle_id`、`created_at`、`source`（缓存/APK 快照）、`campaign`（run/签名/cohorts/四联）、")
    add("`evidence_levels`（本文件 §3 图例的机器版）、`categories`（分子类文件数与字节）、`art_missing`（缺图集合）、")
    add("`files[]`（`path`/`bytes`/`sha256`，按路径排序）、`totals`（`files`/`bytes`）、`excluded`（排除项）。")
    add("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="output/character_skills/pages")
    ap.add_argument("--out", default=f"output/share_bundle/{BUNDLE_ID}")
    ap.add_argument("--zip", default=f"output/share_bundle/{BUNDLE_ID}.zip")
    ap.add_argument("--check-out", default="work/20261022_skill_values_bundle/check.json")
    ap.add_argument("--force", action="store_true", help="允许覆盖已存在的输出目录/压缩包")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    pages = (repo / args.pages).resolve()
    out = (repo / args.out).resolve()
    zip_path = (repo / args.zip).resolve()
    check_path = (repo / args.check_out).resolve()

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
    print(f"[1/5] 收集白名单文件：{pages}")
    cids, items = collect_items(pages)
    campaign = load_campaign(pages)
    print(f"      角色页 {len(cids)}；待复制文件 {len(items):,}")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    print("[2/5] 复制并计算 SHA-256")
    records: list[dict] = []
    for i, (rel, src) in enumerate(items, 1):
        dst = out / rel
        size, digest = copy_hashed(src, dst)
        records.append({"path": rel, "bytes": size, "sha256": digest})
        if i % 1000 == 0 or i == len(items):
            print(f"      {i:,}/{len(items):,} 文件（{sum(r['bytes'] for r in records):,} B）")

    records.sort(key=lambda r: r["path"])

    # 按文件名精确分类（card.json/index.html/receipt.json 都在 pages/<cid>/ 下）
    rec_card_json = [r for r in records if r["path"].startswith("pages/") and r["path"].endswith("/card.json")]
    rec_card_html = [r for r in records if r["path"].startswith("pages/") and r["path"].endswith("/index.html") and r["path"].count("/") == 2]
    rec_receipt = [r for r in records if r["path"].startswith("pages/") and r["path"].endswith("/receipt.json")]
    rec_top = [r for r in records if r["path"] in {f"pages/{n}" for n in PAGES_TOP_FILES}]
    rec_art = [r for r in records if r["path"].startswith("pages/art/")]
    categories = {
        "card_json": len(rec_card_json),
        "card_json_bytes": sum(r["bytes"] for r in rec_card_json),
        "card_html": len(rec_card_html),
        "card_html_bytes": sum(r["bytes"] for r in rec_card_html),
        "receipt": len(rec_receipt),
        "receipt_bytes": sum(r["bytes"] for r in rec_receipt),
        "top": len(rec_top),
        "top_bytes": sum(r["bytes"] for r in rec_top),
        "art": len(rec_art),
        "art_bytes": sum(r["bytes"] for r in rec_art),
    }
    if categories["card_json"] != len(cids) or categories["receipt"] != len(cids):
        print(f"[FAIL] 分类计数异常：{categories}")
        return 3

    # 缺图集合（按 2236 卡分母）
    art_dirs = {p.name: {f.name for f in p.iterdir() if f.is_file()} for p in (pages / "art").iterdir() if p.is_dir()}
    missing_card = [c for c in cids if "card.png" not in art_dirs.get(c, set())]
    missing_whole = [c for c in cids if "whole.png" not in art_dirs.get(c, set())]
    missing_icon = [c for c in cids if "icon.png" not in art_dirs.get(c, set())]
    art_missing = {
        "card": len(missing_card),
        "card_cids": missing_card,
        "whole": len(missing_whole),
        "whole_cids": missing_whole,
        "icon": len(missing_icon),
        "icon_cids": missing_icon,
    }

    pages_total = {"files": len(records), "bytes": sum(r["bytes"] for r in records)}
    meta = {
        "bundle_id": BUNDLE_ID,
        "created_at": now_cn(),
        "source": {
            "repo_relative": "output/character_skills/pages",
            "cache_snapshot": "output/cache_full_20261015_v3/",
            "cache_pointer": "output/cache_full_latest.json",
            "apk": {
                "package": "com.sega.chainchronicle",
                "version_name": "5.6.2",
                "version_code": 56021,
                "unity": "2021.3.58f1",
                "base_master": "output/base_master/",
            },
            "roster": "2236 个 cid（卡片目录）",
        },
        "campaign": campaign,
        "evidence_levels": EVIDENCE_LEVELS,
        "categories": categories,
        "art_missing": art_missing,
        "pages_total": pages_total,
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

    print("[3/5] 写 README.md 与 manifest.json")
    # README 先写，manifest 再收它的哈希
    readme_path = out / "README.md"
    readme_path.write_text(build_readme(meta), encoding="utf-8", newline="\n")
    readme_size = readme_path.stat().st_size
    readme_sha = sha256_file(readme_path)
    manifest_files = records + [{"path": "README.md", "bytes": readme_size, "sha256": readme_sha}]
    manifest_files.sort(key=lambda r: r["path"])
    totals = {"files": len(manifest_files), "bytes": sum(r["bytes"] for r in manifest_files)}
    manifest = {
        "bundle_id": BUNDLE_ID,
        "created_at": meta["created_at"],
        "generator": "scripts/release/build_skill_values_bundle.py",
        "scope_note": "组合X＝全量页面包（pages 全量＋入口两页＋pages/README.md＋art 立绘）；_batch 默认排除",
        "source": meta["source"],
        "campaign": meta["campaign"],
        "evidence_levels": EVIDENCE_LEVELS,
        "categories": categories,
        "art_missing": art_missing,
        "pages_total": pages_total,
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

    print(f"[4/5] 压缩 zip（Deflate level {ZIP_LEVEL}）→ {zip_path}")
    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    zip_entries = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=ZIP_LEVEL, allowZip64=True) as zf:
        for p in sorted(out.rglob("*")):
            if not p.is_file():
                continue
            arc = f"{BUNDLE_ID}/{p.relative_to(out).as_posix()}"
            zf.write(p, arcname=arc)
            zip_entries += 1
            if zip_entries % 2000 == 0:
                print(f"      {zip_entries:,} 条目已写入")

    print("[5/5] 从 zip 读回逐条对账")
    expected = {f["path"]: f for f in manifest_files}
    expected["manifest.json"] = {"path": "manifest.json", "bytes": manifest_bytes, "sha256": sha256_file(manifest_path)}
    seen: set[str] = set()
    mismatched: list[dict] = []
    total_read = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        for name in names:
            rel = name[len(BUNDLE_ID) + 1:]
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
                continue
            if info.file_size != exp["bytes"] or h.hexdigest() != exp["sha256"]:
                mismatched.append({"path": rel, "problem": "size_or_sha_mismatch", "zip_bytes": info.file_size, "manifest_bytes": exp["bytes"]})
    missing_in_zip = sorted(set(expected) - seen)
    zip_bytes = zip_path.stat().st_size
    zip_sha = sha256_file(zip_path)
    result = {
        "bundle_id": BUNDLE_ID,
        "checked_at": now_cn(),
        "zip": str(zip_path.relative_to(repo)),
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
        "fixed_machine_check": "work/character_skills_phase2_20261021/verify_full_latest.json（10/10 PASS）",
        "art_missing": {k: v for k, v in art_missing.items() if not k.endswith("_cids")},
    }
    check_path.parent.mkdir(parents=True, exist_ok=True)
    check_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    print("")
    print(f"[DONE] 包目录：{out}")
    print(f"       压缩包：{zip_path}（{human_bytes(zip_bytes)}，SHA-256 {zip_sha}）")
    print(f"       zip 条目 {len(seen):,}（README.md 计入 files；manifest.json 另计 1）")
    print(f"       manifest files={totals['files']:,} bytes={totals['bytes']:,}；对账={'PASS' if result['reconcile_pass'] else 'FAIL'}")
    if not result["reconcile_pass"]:
        print(f"[FAIL] 对账失败：missing={missing_in_zip[:5]} mismatched={result['mismatched'][:5]} unexpected={result['unexpected_in_zip'][:5]}")
        return 4
    print(f"       对账明细：{check_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
