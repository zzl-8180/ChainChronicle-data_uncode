# -*- coding: utf-8 -*-
"""params_report.py — 用模板生成 REPORT.md（大表由脚本渲染，避免手抄出错）。

输入：scripts/refcheck_20261023_lead/params_REPORT_template.md（含 {{ADDED_TABLE}} 等占位符）
      work/refcheck_20261023_lead/params/{new_rows_since_1017,candidate_list_40,_stats}.json
输出：work/refcheck_20261023_lead/params/REPORT.md
"""
import json
import sys

import params_common as P

sys.stdout.reconfigure(encoding="utf-8")
OUT = P.OUT
TPL = P.ROOT / "scripts" / "refcheck_20261023_lead" / "params_REPORT_template.md"


def esc(s, n=None):
    s = (s or "").replace("|", "\\|").replace("\n", " ")
    return s if n is None else (s[:n] + "…" if len(s) > n else s)


def added_table(d):
    out = ["| # | table | type | slot | status | label | 换算 | 单位 | 命中/出现 | 决定性/总 | 例证（截断） |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(d["added"], 1):
        out.append(f"| {i} | {r['table']} | {r['type']} | {r['slot']} | {r['status']} | {esc(r['label'])} | "
                   f"{esc(r['conversion']) or '—'} | {esc(r['unit']) or '—'} | {r['hits']}/{r['cards_with_value']} | "
                   f"{r['decisive_hits']}/{r['decisive_cases']} | {esc(r['examples'], 70) or '（空）'} |")
    return "\n".join(out)


def changed_table(d):
    out = ["| # | table | type | slot | 改判内容 | 现标签 | 命中/出现 | 决定性/总 | 备注 |",
           "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(d["changed"], 1):
        cf = r.get("changed_fields", {})
        parts = []
        for k in ("status", "label", "conversion", "unit"):
            if k in cf:
                a, b = esc(cf[k]["from"]) or "（空）", esc(cf[k]["to"]) or "（空）"
                if k == "status":
                    parts.append(f"状态 {a} → **{b}**")
                elif k == "label":
                    parts.append(f"标签 {a} → **{b}**")
                elif k == "conversion":
                    parts.append(f"换算 {a} → {b}")
                else:
                    parts.append(f"单位 {a} → {b}")
        out.append(f"| {i} | {r['table']} | {r['type']} | {r['slot']} | {'；'.join(parts)} | {esc(r['label']) or '—'} | "
                   f"{r['hits']}/{r['cards_with_value']} | {r['decisive_hits']}/{r['decisive_cases']} | "
                   f"{esc(r['site_statistics'], 60)} |")
    return "\n".join(out)


def candidate_table(c):
    out = ["| 序 | 来源 | table | type | slot | 语义 | 换算 | 单位 | 命中/出现 | 决定性/总 | 我方是否已覆盖该类型 | 建议 |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in c["candidates"]:
        out.append(f"| {e['rank']} | {e['tag']} | {e['table']} | {e['type']} | {e['slot']} | {esc(e['label'])} | "
                   f"{esc(e['conversion']) or '—'} | {esc(e['unit']) or '—'} | {e['hits']}/{e['cards_with_value']} | "
                   f"{e['decisive_hits']}/{e['decisive_cases']} | {'是' if e['our_type_covered'] else '**否**'} | "
                   f"{e['recommend']}{('（' + e['conflict_note'] + '）') if e['conflict_note'] else ''} |")
    return "\n".join(out)


def ours_table():
    """我方已确认语义 ↔ 对方表行（含网站命中率）。数据来源见 params_ours_sitecheck.py。"""
    new = P.load(P.NEW1 / "param_table.json")
    rows = {P.key(r): r for r in new["rows"]}
    items = [
        ("skilllist", 7, "param1", "攻击力 (x-1)x100"), ("skilllist", 7, "param3", "防御力 (1-x)x100"),
        ("skilllist", 1008, "param1", "攻击力"), ("skilllist", 1008, "param3", "防御力"),
        ("skilllist", 1017, "param1", "攻击力"), ("skilllist", 1017, "param3", "防御力"),
        ("skilllist", 1095, "param1", "攻击力"), ("skilllist", 1095, "param2", "移动因子（乘算）"),
        ("skilllist", 1095, "param3", "防御力"), ("skilllist", 1095, "param5", "暴击率加算（pp）"),
        ("skilllist", 1095, "param6", "暴伤 delta=p6−1.5"),
        ("skilllist", 3000, "param1", "普攻倍率加算"), ("skilllist", 3000, "param2", "技能倍率加算"),
        ("skilllist", 3000, "param6", "持续时间（游戏秒）"), ("skilllist", 3000, "param8", "暴伤系数加算"),
        ("skilllist", 99, "param0", "时间"), ("skilllist", 99, "param1", "Normal 触发阈值"),
        ("skilllist", 99, "param3", "Skill 触发阈值"), ("skilllist", 99, "param7", "目标 _attack"),
        ("skilllist", 99, "param8", "目标 _move"), ("skilllist", 99, "param9", "目标 _defense"),
        ("skilllist", 2003, "param0", "时间"), ("skilllist", 2003, "param7", "目标 _attack"),
        ("skilllist", 2003, "param8", "目标 _move"), ("skilllist", 2003, "param9", "目标 _defense"),
        ("skilllist", 2003, "param5", "自身 _move"), ("skilllist", 2003, "param6", "自身 _defense"),
        ("skilllist", 2012, "param0", "时间（游戏秒）"), ("skilllist", 2012, "param4", "暴击率加算（pp）"),
        ("skilllist", 2012, "param5", "暴伤系数加算"), ("skilllist", 2012, "param7", "数量上限"),
        ("skilllist", 2012, "param8", "TARGET_TYPE"),
        ("bossskill", 13, "param1", "攻击力 x100"), ("bossskill", 13, "param2", "防御力 ATK*x10"),
        ("bossskill", 13, "param3", "持续时间秒"), ("bossskill", 13, "param6", "移动速度 x100"),
        ("bossskill", 27, "param1", "回复倍"), ("bossskill", 27, "param2", "间隔秒"),
        ("bossskill", 27, "param3", "次"), ("bossskill", 105, "param1", "伤害倍"), ("bossskill", 105, "param6", "次"),
        ("bossskill", 112, "param1", "伤害倍"), ("bossskill", 112, "param4", "间隔秒"),
        ("bossskill", 112, "param5", "次"), ("bossskill", 112, "param7", "推力（无换算）"),
        ("bossskill", 112, "param8", "九位置掩码"),
    ]
    out = ["| table | type | slot | 我方语义 | 对方标签 | 对方 status | 网站命中/出现 | 决定性/总 |",
           "|---|---|---|---|---|---|---|---|"]
    for t, ty, slot, ours in items:
        r = rows.get((t, ty, slot))
        if not r:
            out.append(f"| {t} | {ty} | {slot} | {ours} | — 无行 — | | | |")
            continue
        out.append(f"| {t} | {ty} | {slot} | {ours} | {esc(r['label']) or '—'} | {r['status']} | "
                   f"{r['hits']}/{r['cards_with_value']} | {r['decisive_hits']}/{r['decisive_cases']} |")
    return "\n".join(out)


def main():
    d = json.loads((OUT / "new_rows_since_1017.json").read_text(encoding="utf-8"))
    c = json.loads((OUT / "candidate_list_40.json").read_text(encoding="utf-8"))
    st = json.loads((OUT / "_stats.json").read_text(encoding="utf-8"))
    tpl = TPL.read_text(encoding="utf-8")
    subs = {
        "{{ADDED_TABLE}}": added_table(d),
        "{{CHANGED_TABLE}}": changed_table(d),
        "{{CANDIDATE_TABLE}}": candidate_table(c),
        "{{OURS_TABLE}}": ours_table(),
        "{{STATUS_NEW}}": json.dumps(st["status_new"], ensure_ascii=False),
        "{{STATUS_OLD}}": json.dumps(st["status_old"], ensure_ascii=False),
        "{{STATUS_NEW_RAW}}": json.dumps(st["status_new_raw"], ensure_ascii=False),
        "{{STATUS_OLD_RAW}}": json.dumps(st["status_old_raw"], ensure_ascii=False),
        "{{ADDED_N}}": str(d["added_count"]),
        "{{CHANGED_N}}": str(d["changed_count"]),
        "{{RECOUNT_N}}": str(d["recount_only_count"]),
        "{{POOL_N}}": str(c["pool_size"]),
    }
    for k, v in subs.items():
        tpl = tpl.replace(k, v)
    left = [k for k in subs if k in tpl]
    (OUT / "REPORT.md").write_text(tpl, encoding="utf-8")
    print(f"wrote {OUT / 'REPORT.md'}  ({len(tpl)} chars); 未替换占位符: {left or '无'}")


if __name__ == "__main__":
    main()
