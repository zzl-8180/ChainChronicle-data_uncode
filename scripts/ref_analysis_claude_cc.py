"""整体分析：claude_cc_site_pages（他人下游项目）核对脚本（只读对方目录，结果写 output/reference_analysis/）。

产出：
- output/reference_analysis/claude_cc_site_pages/param_table_crosscheck.csv  全部 1610 行逐条核对
- output/reference_analysis/claude_cc_site_pages/crosscheck_summary.json     分组统计与重点清单
- output/reference_analysis/claude_cc_site_pages/version_sample_check.json   版本/数据抽样比对
- output/reference_analysis/claude_cc_site_pages/inventory_stats.json        产物盘点统计

运行：.venv\\Scripts\\python.exe -B scripts/ref_analysis_claude_cc.py
"""
import csv
import json
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEIRS = ROOT / "其他人的参考" / "claude_cc_site_pages"
OURS_CACHE = ROOT / "output" / "cache_full_20261015_v3" / "decoded"
OURS_APK = ROOT / "output" / "base_master"
OUT = ROOT / "output" / "reference_analysis" / "claude_cc_site_pages"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 本项目已确认规则（证据：output/ordinary_effects/*/README.md、output/boss_chain、
# output/boss_heal，含 field_dictionary.json；2026-10-17 由分析任务整理）。
# 值：None = 只确认含义/资格，无数值换算；(label, conversion, unit, note) = 数值规则。
# ---------------------------------------------------------------------------
RULES = {
    # bossskill
    ("bossskill", 105, "param1"): ("伤害", "raw", "倍", "本项目确认：每次攻击的技能基值系数（不是总倍率）；B 内已含 Chain"),
    ("bossskill", 105, "param6"): ("次", "raw", "次", "本项目确认：每目标连击尝试上限，不保证实际命中次数"),
    ("bossskill", 112, "param1"): ("伤害", "raw", "倍", "本项目确认：设置陷阱阶段 B×p1，之后不再乘 Chain"),
    ("bossskill", 112, "param4"): ("间隔", "raw", "秒", "本项目确认：游戏秒"),
    ("bossskill", 112, "param5"): ("次", "raw", "次", "本项目确认：每陷阱对象爆发上限，非每目标"),
    ("bossskill", 112, "param0"): (None, "本项目确认含义：fireType 选择（1 须有敌/2 不检查）"),
    ("bossskill", 112, "param7"): (None, "本项目确认含义：推力原样传递；転倒视觉对应为推断"),
    ("bossskill", 112, "param8"): (None, "本项目确认含义：位掩码映射 6×3 九位置模板"),
    ("bossskill", 112, "param9"): (None, "本项目确认含义：跳过旧对象清理（两段执行=九位置各两层）"),
    ("bossskill", 13, "param1"): ("攻击力", "x100", "%", "本项目确认：局部攻击因子 1+p1×Chain"),
    ("bossskill", 13, "param2"): ("防御力", "x*10 (ATK*%)", "ATK%", "本项目确认：固定防御系数，名义=p2×0.1→原始ATK%（仅玩家构建缩放分支；非减伤%）"),
    ("bossskill", 13, "param3"): ("持续时间", "raw", "秒", "本项目确认：游戏秒"),
    ("bossskill", 13, "param6"): ("移动速度", "x100", "%", "本项目确认：局部移动因子 1+p6×Chain"),
    ("bossskill", 27, "param1"): ("回复", "raw", "倍", "本项目确认：单次回复的技能基值系数"),
    ("bossskill", 27, "param2"): ("间隔", "raw", "秒", "本项目确认：游戏秒"),
    ("bossskill", 27, "param3"): ("次", "raw", "次", "本项目确认：回复次数"),
    # skilllist
    ("skilllist", 7, "param0"): (None, "本项目确认含义：地形编码（两位十进制拆组转位），非攻击力%"),
    ("skilllist", 7, "param1"): ("攻击力", "(x-1)x100", "%", "本项目确认：本项攻击乘数（64 条）"),
    ("skilllist", 7, "param3"): ("防御力", "(1-x)x100", "%", "本项目确认：本项受伤量乘数；负值=增伤"),
    ("skilllist", 99, "param0"): ("持续时间", "raw", "秒", "本项目确认：计时输入游戏秒；-1=无正时间倒计时（非 0 秒）"),
    ("skilllist", 99, "param1"): (None, "本项目确认含义：Normal 触发阈值（源值全 1）"),
    ("skilllist", 99, "param2"): (None, "本项目确认含义：Skill 触发阈值（源值全 1）"),
    ("skilllist", 99, "param3"): (None, "本项目确认含义：Critical 触发阈值（源值全 1）"),
    ("skilllist", 99, "param7"): ("攻击力", "-x*100", "%", "本项目确认：受击目标 Support2 _attack 增量"),
    ("skilllist", 99, "param8"): ("移动速度", "-x*100", "%", "本项目单样本解释（チーカ 43023616=-.3）：受击目标移动；本项目确认 param9 才是防御（受伤量）"),
    ("skilllist", 99, "param9"): ("防御力", "x100", "%", "本项目确认：受击目标 Support2 _defense 增量（源值+.05~+.35，受伤量倍率贡献）"),
    ("skilllist", 1008, "param0"): (None, "本项目确认含义：地形编码（同 ability7），非攻击力%"),
    ("skilllist", 1008, "param1"): ("攻击力", "(x-1)x100", "%", "本项目确认：本项攻击乘数（37 条）"),
    ("skilllist", 1008, "param3"): ("防御力", "(1-x)x100", "%", "本项目确认：本项受伤量乘数"),
    ("skilllist", 1017, "param0"): (None, "本项目确认含义：提供者自身是否可接受（0 只排除自身；321 条全 1）"),
    ("skilllist", 1017, "param1"): ("攻击力", "(x-1)x100", "%", "本项目确认（321 条）"),
    ("skilllist", 1017, "param3"): ("防御力", "(1-x)x100", "%", "本项目确认（321 条）"),
    ("skilllist", 1095, "param1"): ("攻击力", "(x-1)x100", "%", "本项目确认（407 条）"),
    ("skilllist", 1095, "param3"): ("防御力", "(1-x)x100", "%", "本项目确认（407 条）"),
    ("skilllist", 3000, "param1"): ("攻击力", "x100", "%", "本项目确认：Support3 普攻倍率加算（pp）"),
    ("skilllist", 3000, "param2"): ("攻击力", "x100", "%", "本项目确认：Support3 技能倍率加算（pp）"),
    ("skilllist", 3000, "param6"): ("持续时间", "raw", "秒", "本项目确认：游戏秒；缺失≠永久"),
    ("skilllist", 3000, "param8"): ("暴击威力", "x100", "%", "本项目确认：Support3 暴伤系数加算"),
    # 本项目已确认但对方 param_table 无行的类型，在汇总里单独说明：
    # skilllist 2012 param0/param4/param5；bossskill 27 skillflag0_1（超上限位 40/35/41/42/43/44）
}


def norm_their(table, typ, slot):
    """charainfo 行镜像同 type 的 bossskill 规则（对方自己声明的假设）。"""
    if table == "charainfo":
        return ("bossskill", typ, slot), True
    return (table, typ, slot), False


def crosscheck():
    rows = json.loads((THEIRS / "param_table.json").read_text(encoding="utf-8"))["rows"]
    out_rows, summary = [], Counter()
    conflicts, upgrades, notable = [], [], []
    for r in rows:
        key, mirrored = norm_their(r["table"], r["type"], r["slot"])
        rule = RULES.get(key)
        verdict, note = "", ""
        if rule is None:
            verdict = "本项目未研究"
            if r["status"] == "统计推断":
                verdict = "本项目未研究·对方统计推断"
                notable.append(r)
        elif rule[0] is None:
            verdict = "本项目已确认含义（无数值换算）"
            note = rule[1]
            if r["status"] in ("弱证据", "统计推断"):
                note += "；对方数值标签疑为误配"
        else:
            elabel, econv, eunit, enote = rule
            match = (r["label"] == elabel and r["conversion"] == econv and r["unit"] == eunit)
            if r["status"] == "解包确认":
                if match:
                    verdict = "一致（对方解包确认↔本项目确认）"
                else:
                    verdict = "冲突（对方解包确认与本项目不一致）"
                    conflicts.append((r, enote))
            elif r["status"] == "统计推断":
                if match:
                    verdict = "一致·对方推断吻合本项目确认（可升级为解包确认）"
                    upgrades.append(r)
                else:
                    verdict = "存疑（对方推断与本项目确认规则不同）"
                    conflicts.append((r, enote))
            else:
                verdict = "本项目已确认·对方未采用"
            note = enote
        if mirrored and not verdict.startswith("本项目未研究"):
            verdict = "镜像:" + verdict
            note = "charainfo 行为对方假设的 bossskill 同型镜像；本项目证据在 bossskill 记录上。" + note
        summary[verdict.split("（")[0]] += 1
        out_rows.append({
            "table": r["table"], "type": r["type"], "slot": r["slot"],
            "对方状态": r["status"], "对方标签": r["label"], "对方换算": r["conversion"], "对方单位": r["unit"],
            "hits": r["hits"], "decisive": r["decisive_hits"], "hit_rate": r["hit_rate"],
            "cards_with_value": r["cards_with_value"],
            "核对结论": verdict, "备注": note,
            "对方例证": r.get("examples", ""), "对方备选": r.get("alternatives", ""),
        })
    with open(OUT / "param_table_crosscheck.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    # 重点：未研究类型里的强统计推断（值得本项目验证的候选）
    cand = sorted((r for r in notable if r["decisive_hits"] >= 10),
                  key=lambda r: -r["decisive_hits"])
    result = {
        "总行数": len(out_rows),
        "结论分布": dict(summary.most_common()),
        "冲突清单": [
            {"table": r["table"], "type": r["type"], "slot": r["slot"], "对方": f'{r["status"]} {r["label"]} {r["conversion"]} {r["unit"]}',
             "本项目证据": note}
            for r, note in conflicts],
        "可升级为本项目确认的行数": len(upgrades),
        "值得本项目验证的未研究类型候选(decisive>=10)": [
            {"table": r["table"], "type": r["type"], "slot": r["slot"],
             "对方推断": f'{r["label"]} {r["conversion"]} {r["unit"]}',
             "hits": r["hits"], "decisive": r["decisive_hits"], "例证": r.get("examples", "")[:120]}
            for r in cand],
        "对方无行但本项目已确认": [
            "skilllist type2012 param0(游戏秒)/param4(暴击率加算pp)/param5(暴伤系数加算)：param_table 无任何行",
            "bossskill type27 skillflag0_1 超上限位(40/35/41/42/43/44→1.2/1.3/1.4/1.6/1.8/2.0)：param_table 不覆盖 flag 字段",
        ],
    }
    (OUT / "crosscheck_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def load_our_cache(name, key, idf="cid"):
    return {r[idf]: r for r in json.loads((OURS_CACHE / f"{name}.data5.json.raw").read_bytes().decode("utf-8"))[key]}


def version_sample_check():
    res = {"样本": [], "计数对比": {}}
    # 1) 缓存卡 cid30236（チーカ）charainfo 字段比对
    their_card = json.loads(next((THEIRS / "cards").glob("cid30236*")).joinpath("card.json").read_text(encoding="utf-8"))
    our_chara = load_our_cache("charainfo", "charainfo")[30236]
    b = their_card["basic"]
    checks = [
        ("rarity", b["rarity"], our_chara["rarity"]),
        ("cost", b["cost"], our_chara["cost"]),
        ("skillname", their_card["skill"]["name"], our_chara["skillname"]),
        ("skilltext", their_card["skill"]["text_jp"], our_chara["skilltext"]),
        ("inihp", b["inihp"], our_chara["inihp"]),
        ("source", their_card["source"], "CACHE"),
    ]
    res["样本"].append({"卡": "cid30236(缓存)", "逐项": [{"字段": n, "对方": str(v1)[:60], "本项目": str(v2)[:60], "一致": v1 == v2} for n, v1, v2 in checks]})
    # 2) ability99 raw 比对（43023616，位于 abilities[].over_skills）
    our_skills = load_our_cache("skilllist", "skilllist", "skillid")
    our99 = our_skills[43023616]

    def find_skill(x):
        if isinstance(x, dict):
            if x.get("skillid") == 43023616:
                return x
            for k in ("sub", "over_skills", "linked_skill"):
                for y in x.get(k) or []:
                    hit = find_skill(y)
                    if hit:
                        return hit
        return None

    their99 = next(filter(None, (find_skill(a) for a in their_card["abilities"])))
    stripped = {k: v for k, v in our99.items() if k not in ("text", "flavor", "timestamp")}
    res["样本"].append({"卡": "cid30236 ability99(43023616) raw",
                        "一致": their99["raw"] == stripped,
                        "对方字段数": len(their99["raw"]), "本项目字段数(剥离后)": len(stripped),
                        "差异键": [k for k in set(their99["raw"]) | set(stripped) if their99["raw"].get(k) != stripped.get(k)]})
    # 2b) bossskill raw 比对（cid2327 エレミア type27 治疗 40232701）
    their2327 = json.loads(next((THEIRS / "cards").glob("cid2327*")).joinpath("card.json").read_text(encoding="utf-8"))
    our_boss = {r["skillid"]: r for r in json.loads((OURS_CACHE / "bossinfo.data5.json.raw").read_bytes().decode("utf-8"))["bossinfo"]["bossskill"]}
    tslot = next(s for pt in their2327["skill"]["patterns"] for s in pt["slots"] if s["skillid"] == 40232701)
    our27 = our_boss[40232701]
    res["样本"].append({"卡": "cid2327 bossskill type27(40232701) raw",
                        "一致": tslot["raw"] == our27,
                        "差异键": [k for k in set(tslot["raw"]) | set(our27) if tslot["raw"].get(k) != our27.get(k)]})
    # 3) APK 卡 cid4（ヴォルグ）
    apk_chara = {r["cid"]: r for r in json.loads((OURS_APK / "_mdCharacter.json").read_bytes().decode("utf-8"))["charainfo"]}
    their4 = json.loads(next(p.joinpath("card.json") for p in (THEIRS / "cards").iterdir() if p.is_dir() and p.name.startswith("cid4") and not p.name[4].isdigit()).read_text(encoding="utf-8"))
    our4 = apk_chara[4]
    res["样本"].append({"卡": "cid4(APK)", "source": their4["source"],
                        "skillname一致": their4["skill"]["name"] == our4["skillname"],
                        "rarity一致": their4["basic"]["rarity"] == our4["rarity"]})
    # 4) 计数对比
    cache_count = sum(1 for c in load_our_cache("charainfo", "charainfo").values() if "rarity" in c)
    apk_playable = sum(1 for c in apk_chara.values() if c.get("illustrator") and c.get("skillname") and c.get("rarity"))
    res["计数对比"] = {
        "本项目缓存 charainfo(有rarity)": cache_count,
        "本项目 APK playable": apk_playable,
        "对方声明": "缓存 409 / 安装包 1824 / 共 2233",
    }
    # 5) 交付包内含 master_data/decoded 路径核实（对方输入目录名虽不同，内容路径应一致）
    with zipfile.ZipFile(ROOT / "output" / "share_bundle" / "CC_analysis_data_20261016.zip") as z:
        names = z.namelist()
    res["交付包抽样"] = {
        "总条目": len(names),
        "含decoded路径": sorted({n.split("/")[0] + "/" + n.split("/")[1] for n in names if "/" in n})[:10],
        "含charainfo": [n for n in names if "charainfo" in n][:5],
    }
    (OUT / "version_sample_check.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


def inventory_stats():
    cards = list((THEIRS / "cards").glob("*/card.json"))
    src = Counter()
    for c in cards:
        src[json.loads(c.read_text(encoding="utf-8")).get("source")] += 1
    mr = json.loads((THEIRS / "match_result.json").read_text(encoding="utf-8"))
    st = Counter(v["status"] for v in mr.values())
    mm = json.loads((THEIRS / "manual_matches.json").read_text(encoding="utf-8"))
    tr = sorted(p.name for p in (THEIRS / "translations").glob("*.json"))
    imgs = sum(1 for p in (THEIRS / "cards").glob("*/card.png")), sum(1 for p in (THEIRS / "cards").glob("*/icon.png"))
    res = {
        "card.json 数": len(cards), "source 分布": dict(src),
        "match_result 状态分布": dict(st.most_common()),
        "manual_matches 条数(不含_note)": len([k for k in mm if k != "_note"]),
        "translations": tr,
        "card.png": imgs[0], "icon.png": imgs[1],
        "UPDATE 提及但副本缺失": ["translations/354.json", "scripts 内 is_party()（队伍能力）", "index.html cid 数值排序"],
    }
    (OUT / "inventory_stats.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(json.dumps(crosscheck(), ensure_ascii=False, indent=2)[:3000])
    print("---- version sample ----")
    print(json.dumps(version_sample_check(), ensure_ascii=False, indent=2))
    print("---- inventory ----")
    print(json.dumps(inventory_stats(), ensure_ascii=False, indent=2))
