# -*- coding: utf-8 -*-
"""汇总 17 条规则的复核结论，生成 REPORT.md 与 verify_results.json。

输入：work/refcheck_20261023_lead/verify/{params_claims,flags_units_claims,namespace_claim}.json
输出：同目录 REPORT.md、verify_results.json
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verify_common import OUT_DIR, write_json  # noqa: E402

REPORT = os.path.join(OUT_DIR, "REPORT.md")
RESULTS = os.path.join(OUT_DIR, "verify_results.json")

REPRO = [
    r".venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/verify_01_params.py",
    r".venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/verify_02_flags_units.py",
    r".venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/verify_03_namespace.py",
    r".venv\Scripts\python.exe -B scripts/refcheck_20261023_lead/verify_build_report.py",
]


def load(name):
    with open(os.path.join(OUT_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def slot_n(slots, i):
    """val_counter 的槽号键经 JSON 落盘后变成字符串，两种都认。"""
    for k in (str(i), i):
        if k in slots:
            return slots[k].get("present", 0)
    return 0


def build_claims(p, f, n):
    """p=params_claims, f=flags_units_claims, n=namespace_claim"""
    c1 = p["claim1_type1009"]
    c2 = p["claim2_type116"]
    c3 = p["claim3_type1074"]
    c4 = p["claim4_type1051"]
    c5 = p["claim5_type58"]
    c6 = p["claim6_type2012"]
    c7 = p["claim7_type3000"]
    c8 = p["claim8_type99"]
    c9 = p["claim9_bossskill13"]
    c10 = p["claim10_type28"]
    c11 = p["claim11_type6"]
    c12 = p["claim12_type1029"]
    g = f["claim13_grid_unit"]["slots_checked"]
    it = f["claim14_attack_interval"]
    fl = f["claim15_overheal_flags"]
    z = f["claim16_zero_omission"]

    claims = []

    claims.append({
        "id": 1, "short": "skilllist type1009 法珠数分级",
        "declaration": "k 颗法珠时 = 基础值×k×m_k（m_1=1、m_2=p6、m_3=p7）；p1 攻击、p2 移动速度、p3 防御(负)、p4 暴击率、p5 暴击威力。",
        "denominator": c1["n"],
        "actual": (
            "skilllist ability=1009 共 %d 条。p1 全存在（0.1×17、0.05×9、0.125×7、0.04、0.2）；"
            "p6 全存在（0.75×32、1×2、0.625×1）；p7 全存在（0.6×31、1×2、0.75、0.5）；"
            "p2/p3/p4/p5 分别存在 %d/%d/%d/%d 条，且取值恒等于 ±p1（p3 恒负）。"
            % (c1["n"], slot_n(c1["slots"], 2), slot_n(c1["slots"], 3),
               slot_n(c1["slots"], 4), slot_n(c1["slots"], 5))),
        "hits": (
            "公式可验证部分 **2/2 成立**：技能名自带显式区间的两条全部吻合 —— "
            "137002「攻撃1.04～1.072」以 base=0.04 得 k=1:1.04、k=3:1.072；"
            "137003「攻撃1.125～1.225」以 base=0.125 得 k=1:1.125、k=3:1.225；"
            "两条的 k3/k1 增益比都是 1.8 = 3×0.6（=3×p7）。p1=攻击由名称「攻撃…」直接确认。"),
        "counter_examples": [
            "k=2 中间档（1.06 / 1.1875）在本快照没有任何名称或文本可对照，只能引用对方网站口径，我方无法独立验证。",
            "p2/p3/p4/p5 的属性归属无法从数据推出：35 条中这 4 个槽的取值恒等于 ±p1（如 40022009 全为 0.1、40034607 全为 0.2），同值不可分辨；我方 rules.json 无 skilllist|1009、dispatch_map 未覆盖 1009、记录无效果文本。",
            "40633905 / 40725108 / 40725109 / 42021107 等 p4 与 p5 同值同量级，属同一基础值复制。",
        ],
        "verdict": "部分成立",
        "verdict_note": "k×m_k 结构与 k=1/k=3 两档成立；属性槽 p2–p5 的语义、k=2 中间档无法判定。",
        "our_evidence": {"has_stronger": False, "level": "无",
                         "paths": [],
                         "note": "我方 rules.json 无 skilllist|1009 规则；属对方新增。"},
        "samples": [{"cid": None, "record": "skilllist 137002 / 137003（配置记录）"},
                    {"cid": None, "record": "skilllist 40022009 / 40034607（p1–p5 同值）"}],
    })

    claims.append({
        "id": 2, "short": "bossskill type116 随机攻击",
        "declaration": "p1=每次间隔秒、p2=次数、p4=每次伤害倍率；p6=1.5 常见（半径/周围），p8=0.5 含义不明。",
        "denominator": c2["n"],
        "actual": (
            "bossskill skillid0=116 共 %d 条。p1 存在 %d 条（缺失 %d）；**p1<1 的记录 %d 条（%.1f%%）**；"
            "p1 分布：1×58、0.5×42、0.1×10、0.25×7、0.05×5、2×5、2.5×4、1.1×3、1.5×3、3×3、"
            "0.3×2、0.125×2、0.275×2、7×1、0.2×1、0.15×1。"
            "p2 存在 103（25×25、15×21、10×17、20×10、5×8、17×4…）；p4 存在 150（42 种取值）；"
            "p6 存在 133（1.5×125、2.5×3、3.25×3、0.75、1）；p8 存在 134（0.5×106、0.4×10、0.725×6…）。"
            % (c2["n"], c2["p1_present"], c2["p1_missing"], c2["p1_lt_1"],
               100.0 * c2["p1_lt_1"] / c2["n"])),
        "hits": ("p6=1.5 常见（125/133）、p8=0.5 常见（106/134）两条“分布描述”与数据一致；"
                 "p1<1 并非个例而是 72/150 的多数，与对方「网站统一写 1 秒、游戏无最短 1 秒限制」的故事不矛盾"
                 "（但网站侧我们无法独立复核）。"),
        "counter_examples": [
            "「p1=间隔秒 / p2=次数 / p4=每次伤害倍率」三条语义我方无任何独立证据：无 116 规则、bossskill 无效果文本、boss_attack_types 未覆盖 116。",
            "p8 只有「0.5 常见」可核对，含义仍未知；其余 28 条（0.4/0.725/0.25…）无解释。",
            "对方未提的槽：p0（−1×132、10×1）、p3（32×141 等，疑为目标类型）、p5（0.001×121，疑为推力）、p9。",
        ],
        "verdict": "部分成立",
        "verdict_note": "分布描述成立；语义（p1 间隔 / p2 次数 / p4 倍率）未被我方数据证实或证伪。",
        "our_evidence": {"has_stronger": False, "level": "无", "paths": [],
                         "note": "我方无 bossskill|116 规则。"},
        "samples": [{"cid": None, "record": "bossskill 40029706 / 40034503 / 40130100"},
                    {"cid": None, "record": "40035409 p1=1 p4=0.75 p6=1.5 p8=0.5（无 p2）"}],
    })

    claims.append({
        "id": 3, "short": "skilllist type1074 自身被选择时",
        "declaration": "p1 攻击、p2 移动速度、p3 防御(1−x)、p6 暴击率、p7 暴击威力。",
        "denominator": c3["n"],
        "actual": ("skilllist ability=1074 共 %d 条（40035406 / 40634306 / 40768906），三条参数完全相同："
                   "p0=1、p1=1.05、p2=1.05、p3=0.95、p6=0.05、p7=0.05；无 p4/p5/p8/p9。"
                   "记录 text 仅「…のサブアビリティ１」占位，无效果文本。" % c3["n"]),
        "hits": ("数值结构与声明相容：p1/p2 为乘数形（1.05）、p3 为受伤量乘数（0.95→防御 +5%）、"
                 "p6/p7 为加算形（0.05），量纲分工与 type1095（p2/p3 乘算、p5/p6 加算）一致。"),
        "counter_examples": [
            "3 条记录参数完全同值，无法区分 5 个槽各自对应哪个属性。",
            "无效果文本、无原生证据、我方 rules.json 无 1074 → 任何槽位语义都无法证实。",
            "3 条记录的三张卡（cid354/6343/7689）都是同一批「異神」卡，样本高度同质。",
        ],
        "verdict": "无法判定",
        "verdict_note": "数值量纲相容但属性归属无证据；样本仅 3 条且完全同值。",
        "our_evidence": {"has_stronger": False, "level": "无", "paths": [],
                         "note": "我方 rules.json 无 skilllist|1074。"},
        "samples": [{"cid": 354, "record": "skilllist 40035406 p0=1 p1=1.05 p2=1.05 p3=0.95 p6=0.05 p7=0.05"}],
    })

    claims.append({
        "id": 4, "short": "skilllist type1051 治疗行动增减益",
        "declaration": "两条记录（我方 / p6=1 敌方）：p0 秒、p1 攻击、p2 移动、p3 防御、p4 暴击率、p5 暴击威力，取绝对值×100。",
        "denominator": c4["n"],
        "actual": ("skilllist ability=1051 共 %d 条。p6 只出现 1（%d 条），其余 %d 条无 p6。"
                   "**p6=1 的 %d 条 p1 全为负（%d/%d）**；**无 p6 的 %d 条 p1 全为正（%d/%d）**；"
                   "p3 相应翻转：p6=1 组 %d/%d 条 p3>0，无 p6 组 %d/%d 条 p3<0。"
                   "p0：30×39、10×3。p4/p5 各只有 3 条存在。"
                   % (c4["n"], c4["p6_eq_1"], c4["no_p6"], c4["p6_eq_1"], c4["p6_1_all_p1_negative"],
                      c4["p6_eq_1"], c4["no_p6"], c4["no_p6_all_p1_positive"], c4["no_p6"],
                      c4["p6_1_p3_positive"], c4["p6_eq_1"], c4["no_p6_p3_negative"], c4["no_p6"])),
        "hits": ("「两条记录、我方/p6=1 敌方」结构成立：17 条 p6=1 全部是敌方侧（负攻击 + 正受伤量），"
                 "25 条无 p6 全部是增益侧（正攻击 + 负受伤量）。取绝对值×100 只是显示换算，与符号约定自洽。"),
        "counter_examples": [
            "p1=攻击 / p2=移动 / p3=防御(受伤量) / p4=暴击率 / p5=暴击威力 的属性归属无文本、无原生证据；p4/p5 各只有 3 条。",
            "例外：47000656（p6=1、p1=−0.15、p4=−0.15、p5=−0.15、无 p2/p3）；另有 2 条无 p6 记录只有 p1/p4/p5（40129316、43010403）。",
            "p0 有 3 条是 10 秒（42010309、47000702、47001139），其余 30 秒，对方文档未提。",
        ],
        "verdict": "部分成立",
        "verdict_note": "「我方/敌方两条记录 + p6=1 标记」成立；5 个属性槽的语义未证。",
        "our_evidence": {"has_stronger": False, "level": "无", "paths": [],
                         "note": "我方 rules.json 无 skilllist|1051。"},
        "samples": [{"cid": 346, "record": "skilllist 40034603（增益侧 p1=0.3 p3=-0.3）/ 40034604（p6=1 敌方侧 p1=-0.3 p3=0.3）"},
                    {"cid": None, "record": "47000656 例外"}],
    })

    claims.append({
        "id": 5, "short": "skilllist type58 免疫死亡(Guts)",
        "declaration": "p0=1（无敌秒）、p4=复活 HP 回复量（称职业通用 100000）、p5=次数、p6=之后攻击力提升秒数、p7=获得法珠数。",
        "denominator": c5["n"],
        "actual": ("skilllist ability=58 共 %d 条。p0 恒为 1（7/7）。"
                   "**p4：50000×3、100000×2、450000×1（敌用）、100000000×1（敌用）**；"
                   "p5：3×3、1×2、8×1、2×1；p6 仅 1 条 = −1；p7 仅 1 条 = 1。" % c5["n"]),
        "hits": ("p0 恒 1、p4 是随卡变化的数值、p5 形如次数、p7=1 形如获珠数 —— 与声明的大方向相容。"
                 "职业通用记录 65000005「■職業_騎士_通常_Guts」p4=100000 确实存在。"),
        "counter_examples": [
            "**「职业通用 100000」不成立**：3 张玩家卡是 50000 —— 40839903 レアム(cid8399, jobtype4 骑士)、42010505 アインスロット(cid20105)、42030608 ギザザヤ(cid20306)；而 40035108 シルヴァ(cid351, jobtype 缺→0) 是 100000。骑士通用记录是 100000、骑士卡レアム却是 50000 → 既非职业决定，也不能断言「网站写 50000 全错」。",
            "p6 唯一取值 −1，与「之后攻击力提升的秒数」不符（负数）。",
            "p0=1 与「无敌 1 秒」之间没有任何数值证据（只有对方的用户确认）。",
        ],
        "verdict": "部分成立",
        "verdict_note": "p0/p5/p7 与「数值随卡变化」相容；其中「职业通用 100000」这一子断言被数据推翻（明确不成立）。",
        "our_evidence": {"has_stronger": False, "level": "无", "paths": [],
                         "note": "我方 rules.json 无 skilllist|58。"},
        "samples": [{"cid": 351, "record": "skilllist 40035108 p4=100000 p5=8"},
                    {"cid": 8399, "record": "40839903 p4=50000 p5=3（反例）"},
                    {"cid": 20306, "record": "42030608 p4=50000 p1=0.1 p2=0.1 p3=-0.1 p6=-1"}],
    })

    claims.append({
        "id": 6, "short": "skilllist type2012 SA 必杀增益",
        "declaration": "p0=持续秒、p4=暴击率×100、p5=暴击威力×100、p6=攻击间隔变化（基础间隔×(1+p6)）。",
        "denominator": c6["n"],
        "actual": ("skilllist ability=2012 共 %d 条。p0 全存在（30×373、300×16、100×8、24.15×4、60×3、22.5×2）。"
                   "p4 存在 %d、p5 存在 %d，**两者同时存在的 %d 条数值完全相等（%d/%d）**，另有 %d 条只有 p5。"
                   "p6 存在 %d 条（−0.325×91、−0.2×3、−0.33、−0.3、−0.3125）；p7：20×305、1×99；p8：31×307、64×99。"
                   % (c6["n"], c6["p4_present"], c6["p5_present"], c6["both_p4_p5"],
                      c6["both_p4_p5_equal"], c6["both_p4_p5"], c6["p5_present"] - c6["both_p4_p5"],
                      c6["p6_present"])),
        "hits": ("p0=持续游戏秒、p4=暴击率加算、p5=暴击伤害系数加算 —— **我方原生证据已确认**"
                 "（p4→TimePowerUpData+24 _critical、p5→+28 _criticalDmgRate）；本次数据侧佐证：p4 记录所属卡 304/308 的正文同时出现「クリティカル発生率」「クリティカル威力」。"
                 "p6：cid89 アセス 正文「また自身の攻撃速度が一定時間上がる」，其 SA 40008912 只带 p6=−0.325（p7=1、p8=64 自身），"
                 "且 1.5×(1−0.325)=**1.0125**、1.5×(1−0.3)=**1.05** 精确复现对方样例 → p6 与攻击速度/间隔相关有内证。"),
        "counter_examples": [
            "p4 与 p5 在 308/308 条里数值完全相等：单看数据无法区分两槽，必须靠我方原生证据（对方此处判断正确但依据不足）。",
            "p6=攻击间隔变化 我方**无原生证据**（ability2012 只核了 p0/p4/p5 的写入点）；97 条 p6 记录中只有 42 张持有卡正文出现「攻撃速度」，55 张没有（cid347/349/351/352/353/354 等 SA p6 记录）。",
            "(1+p6) 线性公式本身无独立验证，只有 1.0125/1.05 两个数值巧合吻合；p6 也可能是「攻击速度 +x%」而非「间隔 ×(1+x)」。",
        ],
        "verdict": "部分成立",
        "verdict_note": "p0/p4/p5 成立（我方更强）；p6 方向有单例内证，公式与语义未确认。",
        "our_evidence": {"has_stronger": True, "level": "原生确认（p0/p4/p5）",
                         "paths": ["output/ordinary_effects/ability2012/README.md（1025 字段，49 项原生检查）",
                                   "output/character_skills/profiles/rules.json（skilllist|2012|/param0、/param4、/param5）",
                                   "output/character_skills/inference_inventory/b8_crit2012_scope.md"],
                         "note": "p6 我方无规则，属对方新增候选。"},
        "samples": [{"cid": 89, "record": "skilllist 40008912 p0=30 p6=-0.325 p7=1 p8=64（攻击速度 SA）"},
                    {"cid": 354, "record": "40035412 p4=p5=0.3（暴击率/暴伤 SA）"}],
    })

    claims.append({
        "id": 7, "short": "skilllist type3000 共鸣能力 p4",
        "declaration": "p4 → 防御力 = 敌人ATK×(−p4×100)%。",
        "denominator": c7["n"],
        "actual": ("skilllist ability=3000 共 %d 条。p4 存在 %d 条（−0.025×126、−0.0125×43），"
                   "**p4 恒等于 −p1/4（%d/%d 条），也恒等于 −p8/4（29/29）**。"
                   "其余槽：p1 0.1×205/0.05×98、p2 同 p1、p3 0.1×30/0.05×16、p5 0.3×82/0.25×29、"
                   "p6 45×342/60×6、p8 0.1×116/0.05×28、p9 86 条。"
                   % (c7["n"], c7["p4_present"], c7["p4_equals_negative_p1_over_4"][0],
                      c7["p4_equals_negative_p1_over_4"][1])),
        "hits": ("**p4 = 防御力（方向）可由记录自带正文验证**：正文含「防御力」的 109 条中 91 条有 p4；"
                 "不含「防御力」的 90 条中只有 2 条有 p4。最强单例：40022310（カトリ cid223）"
                 "正文「味方の防御力が一定時間上がり、HPが上限を超えて回復し、呪い/封印を回復する」"
                 "→ 只带 p4=−0.025、p5=0.3、flag1_1=512，无 p1/p2。"
                 "**新发现**：p3 ↔ 移動速度（正文含「移動速度」的 41 条中 39 条有 p3；不含的 158 条 0 条有 p3）。"),
        "counter_examples": [
            "**「敌人ATK×」这个基数与「固定防御量」量纲在本快照没有任何证据**：全部正文都不写「敵の攻撃力の…」；我方 rules.json 明确 3000 的 p3/p4/p5/p7 未定；我方 99/2003 的 _defense 是受伤量乘算增量（−0.025 更可能是「受伤量 −2.5%」而非「敌ATK 的 2.5% 作为固定防御」）。",
            "p4 与 p1 严格成 −1/4 比例（148/148）说明它是同一基础值的 1/4 缩放，但基础值的语义未定。",
            "文本反例 18 条：正文含「防御力」却无 p4（如 40034110 正文两句分属不同子记录）。",
        ],
        "verdict": "部分成立",
        "verdict_note": "p4=防御力方向成立（新证据）；「敌人ATK×(−p4×100)%」的基数/量纲无法判定。",
        "our_evidence": {"has_stronger": False, "level": "我方明确未定",
                         "paths": ["output/character_skills/inference_inventory/yg_priority_list.md（「3000 的 p3/p4/p5/p7 语义未定」）",
                                   "output/ordinary_effects/ability3000/README.md（只确认 p1/p2/p6/p8）"],
                         "note": "我方未覆盖 p4；本次给出 p4=防御力 + p3=移動速度 两条新证据。"},
        "samples": [{"cid": 223, "record": "skilllist 40022310 p4=-0.025 p5=0.3 p6=45 flag1_1=512"},
                    {"cid": 1244, "record": "40124410 p4=-0.0125 p6=45（正文只有「防御力が上がる」）"}],
    })

    claims.append({
        "id": 8, "short": "skilllist type99 PowerDrain",
        "declaration": "p7 攻击、p8 移动速度、p9 防御(受伤量)、p0=秒。（对方 param_table 把 p8 标「防御力」、HANDOFF §5 又写 p9 移动速度，三处矛盾）",
        "denominator": c8["n"],
        "actual": ("skilllist ability=99 共 %d 条。**p7 存在 %d 条全为负**；**p8 存在 %d 条全为负**；"
                   "**p9 存在 %d 条全为正**；p0：30×103、60×19、10×6、20×3、−1×2。"
                   % (c8["n"], c8["p7_n"], c8["p8_n"], c8["p9_n"])),
        "hits": ("**开发命名直接写语义**（数据内证）：127007「デバフ(攻撃手段不問)・敵攻撃20秒10%DOWN」→ p7=−0.1；"
                 "127008「…敵移動20秒10%DOWN」→ p8=−0.1；127009「…敵防御20秒10%DOWN」→ p9=+0.1；"
                 "75013001/75013002/75013003「■リーダー_デバフ通常攻撃_攻撃力/防御力/移動速度_5％」分别只带 p7/p9/p8。"
                 "→ p7=攻击、p8=移动速度、p9=防御（受伤量）成立，且与我方原生结论一致。"),
        "counter_examples": [
            "p8=−10 的 3 条（47001198/47001199/47001200）是异常值/占位，不能参与换算。",
            "p4/p5/p6（各 23/21/23 条）我方无规则，对方本条未涉及。",
            "对方 param_table 的「p8=防御力」与 HANDOFF §5 的「p7/p8=攻击/防御、p9=移动速度」**两处都不成立**，与我方 2026-10-17 分析（output/reference_analysis/claude_cc_site_pages/README.md §4.2）一致。",
        ],
        "verdict": "成立",
        "verdict_note": "数据分布 + 开发命名 + 我方 192 项原生检查三重一致。",
        "our_evidence": {"has_stronger": True, "level": "原生确认",
                         "paths": ["output/ordinary_effects/ability99/README.md（192 项原生检查：p7→_attack、p9→_defense、p0→计时）",
                                   "output/character_skills/profiles/rules.json（skilllist|99|/param0,/param7,/param8,/param9）",
                                   "output/reference_analysis/claude_cc_site_pages/README.md §4.2（对方 param_table 冲突记录）"],
                         "note": "本次新增「开发命名」作为第二条独立证据。"},
        "samples": [{"cid": None, "record": "skilllist 127007/127008/127009（dev 命名三连）"},
                    {"cid": 89, "record": "40008903 p7=-0.3 p8=-0.3 p9=+0.3"},
                    {"cid": 6340, "record": "75013001 p7=-0.05（攻撃力5%DOWN）"}],
    })

    claims.append({
        "id": 9, "short": "bossskill type13 必杀增益",
        "declaration": "p1 攻击×100、p2 防御=自身ATK×(p2×10)%、p3 秒、p6 移动速度。",
        "denominator": c9["n"],
        "actual": ("bossskill skillid0=13 共 %d 条。p1/p2/p3 全存在，p6 缺 %d。"
                   "p2=p1/2 有 %d/%d（60 条例外如 40034105 p1=0.45、p2=p6=0.25）；"
                   "**p6 与 p2 完全相等 %d/%d**；p3：30×707、60×4、24.15×4、22.5×2、25×1。"
                   % (c9["n"], c9["p6_missing"], c9["p2_equals_p1_half"][0], c9["p2_equals_p1_half"][1],
                      c9["p6_equals_p2"][0], c9["p6_equals_p2"][1])),
        "hits": ("p1=攻击、p3=游戏秒、p6=移动速度 我方原生已确认（SupportData._attackUp=1+原值×Chain、"
                 "_moveUp、supportTime）；p2=防御=自身ATK×(p2×10)% 我方亦确认：guard=trunc(_normalAtk×p2×Chain)，"
                 "其中 _normalAtk=(CardInfo.ATK+belovedAtk)×0.1 —— 比对方声明多了 Chain 与向零截断。"),
        "counter_examples": [
            "**数据本身无法区分 p2 与 p6（715/715 完全相等）**：任何「看数值猜属性」的方法在这个类型上必然失效，只有原生代码能判定。对方旧版 NUMBER_RULES 的「p6=暴击威力」正是这类误判。",
            "60 条 p2≠p1/2，说明 p2 不是简单由 p1 派生（与「防御=(p2×10)%」的公式无关，但提醒不要用 p1 反推 p2）。",
            "p0/p4/p5/p7/p8/p9 在该类型 0 条存在。",
        ],
        "verdict": "成立",
        "verdict_note": "四个槽位语义全部与我方原生证据一致，且我方换算更精确。",
        "our_evidence": {"has_stronger": True, "level": "原生确认",
                         "paths": ["output/boss_heal/field_dictionary.json + README.md（type13 p1/p2/p3/p6）",
                                   "output/boss_chain/（type13 支持块实参序与 _normalAtk 构建）",
                                   "output/character_skills/profiles/rules.json（bossskill|13|/skillparam1,2,3,6）",
                                   "output/character_skills/inference_inventory/b9_debuff_scope.md"],
                         "note": "我方还确认了 Chain 系数与 trunc 整数化。"},
        "samples": [{"cid": 354, "record": "bossskill 40035402 p1=0.6 p2=0.3 p3=30 p6=0.3"},
                    {"cid": 89, "record": "40008902 / 40008905（普通/超共鸣两档）"}],
    })

    claims.append({
        "id": 10, "short": "skilllist type28 击杀获珠",
        "declaration": "p0–p2=击杀时获得法珠几率、p3–p5=地形条件追加几率、p6=地形编号（4=沙漠），不是减益。",
        "denominator": c10["n"],
        "actual": ("skilllist ability=28 共 %d 条。p0 0.1–0.3、p1 0.1–1、p2 0.1–1（p0=0.2×30 为主）。"
                   "**p3/p4/p5 各 %d 条且三者恒等**（0.8×5、0.1×6、0.05、0.2）；"
                   "p6 %d 条（20×5、13×3、15×2、2、3、4）；p9 45 条（3×27、2×18）。"
                   % (c10["n"], c10["terrain_records"],
                      sum(c10["p6_dist"].values()) if isinstance(c10["p6_dist"], dict) else 13)),
        "hits": ("p0–p2 = 击杀法珠概率阈值：我方原生确认（damageType 0/2/1 分别读 param0/param1/param2）；"
                 "p4/p5 = 地形命中时的附加阈值：原生确认（damageType2→p4，0/1→p5）；"
                 "p6 = 地形位索引：4 被整数化后左移成掩码 16，与チーカ「地形が砂漠の時…」文案相符；"
                 "「不是减益」成立。"),
        "counter_examples": [
            "**「p3–p5」中的 p3 不成立**：我方已核路径不读 param3，mana_chance/README.md 明确「param3=.8 未被此条已核路径读取，原值继续保留未知，不能按参数对称性补解释」；p3 只是在 13 条里恰好等于 p4/p5。",
            "「p6=地形编号（4=沙漠）」：4 在 13 条里只出现 1 条（43023602 チーカ）；常见值是 20(×5)、13(×3)、15(×2)。4=沙漠 只是单实例，p6 是位索引（1<<4=16）而非编号表。",
            "p7=20 的 1 条（42052308）与 p9（2/3）我方都没有规则。",
        ],
        "verdict": "部分成立",
        "verdict_note": "p0–p2、p4/p5、p6（位索引）、非减益 成立；p3 子断言不成立（我方原生证明该路径不读 p3）。",
        "our_evidence": {"has_stronger": True, "level": "原生确认（p0/p1/p2/p4/p5/p6）",
                         "paths": ["output/card_comparison_cid30236/mana_chance/README.md（14 项受控原生检查）",
                                   "output/character_skills/profiles/rules.json（skilllist|28|/param0,1,2,4,5,6）",
                                   "output/character_skills/profiles/rules.json（skilllist|28|/param3 无条目＝显式未解释）"],
                         "note": "我方还给出 damageType 映射顺序（0→p0、2→p1、1→p2），比对方笼统说法精确。"},
        "samples": [{"cid": 30236, "record": "skilllist 43023602 p0=p1=p2=0.2 p3=p4=p5=0.8 p6=4 p9=3"},
                    {"cid": None, "record": "42064402 p6=15；43024202 p6=13（反例：非 4）"}],
    })

    claims.append({
        "id": 11, "short": "skilllist type6 对特定种族",
        "declaration": "p0=种族编号、p1=伤害(x−1)、p3=受伤(1−x)。",
        "denominator": c11["n"],
        "actual": ("skilllist ability=6 共 %d 条。p0∈{1×5、34×3、9、3、26、36}；p1 1.03–1.35（全 >1）；"
                   "**p3 全为 1（12/12）**；无 p2/p4/p5/p6。"
                   "开发命名直写：75018001「■リーダー_人間特効_攻撃力_15%%」p0=1；75018002「…天魔特効…」p0=34；"
                   "105538「ドラゴンキラー」p0=9。" % c11["n"]),
        "hits": ("p1=伤害倍率、p3=受伤量倍率：我方原生 dispatch_map 确认 type6 与 type8 落在同一分支"
                 "（attack←param1、defence←param3），比对方统计更硬；p0=种族编号由技能名直写（人間=1、天魔=34）。"),
        "counter_examples": [
            "p3 全为 1，没有任何非 1 样本：(1−x) 的换算方向来自同族 type7/8 的规则与对方声明，本类型自身无样本。",
            "p0 的种族编号枚举只来自 4 个技能名，未与 homelist/race 表交叉核对（我方 rules.json 无 p0 规则）。",
        ],
        "verdict": "成立",
        "verdict_note": "三条语义均有数据/原生支持；p3 缺非中性样本。",
        "our_evidence": {"has_stronger": True, "level": "原生确认（p1/p3）",
                         "paths": ["output/character_skills/skilllist_types/dispatch_map.json（type6 attack←param1、defence←param3）",
                                   "output/character_skills/profiles/rules.json（skilllist|6|/param5,/param6）",
                                   "output/character_skills/skilllist_types/README.md（type6 与 type8 同分支）"],
                         "note": "我方未给 p0 规则；对方「p0=种族」是新的候选（命名级证据）。"},
        "samples": [{"cid": 352, "record": "leader 能力 75018001 p0=1 p1=1.15 p3=1（人間特効）"},
                    {"cid": None, "record": "105538 p0=9 p1=1.35（ドラゴンキラー）"}],
    })

    claims.append({
        "id": 12, "short": "skilllist type1029 追击倍率",
        "declaration": "param0 = 追击（追加攻击）倍率（对方 UPDATE 提出，证据为技能名直写倍率）。",
        "denominator": c12["n"],
        "actual": ("skilllist ability=1029 共 %d 条。p0 分布：1×37、0.5×15、0.05×2、0.08、0.75、0.1、0.15、0.025；"
                   "p4 仅 1 条=1。按名称族（全部 %d 条）：追撃 %d、EnchantWeapon/付与 %d、其他 %d。"
                   "EnchantWeapon 族 p0=0.5×14、1×12；追撃族 p0=0.05×2、0.1、0.15、0.025。"
                   % (c12["n"], c12["n"], c12["family_all"].get("追撃", 0),
                      c12["family_all"].get("EnchantWeapon/付与", 0), c12["family_all"].get("其他", 0))),
        "hits": ("**名称里直写「像倍率」的数字（带小数点或百分号）的 5 条，p0 全部与之相等（5/5）**："
                 "134001「追撃・追加攻撃倍率0.05」p0=0.05；75008001「■リーダー_追撃1_5%」p0=0.05；"
                 "75008002「…追撃2_10%」p0=0.1；75008003「…追撃3_15%」p0=0.15；75008101「…追撃1_2.5%」p0=0.025。"),
        "counter_examples": [
            "**类型不只承载追击**：全 59 条中 29 条名含 EnchantWeapon/付与（其中 23 条是 EnchantWeapon 族，p0=0.5×14、1×12、0.75…）+ 其余 sub 能力（p0 多为 1），名称不写倍率 → 「type1029 param0 = 追击倍率」不能整型套用。",
            "若有把「sub1」「_1」这类序号当倍率，会多出 5 条**假命中**（如「sub1異変に抗う力」p0=1）—— 本次已按「必须带小数点或百分号」过滤，只留 5 条真证据。",
            "p0=1（37 条）究竟是「1 倍追击」还是别的语义（如附魔开启）无证据。",
        ],
        "verdict": "部分成立",
        "verdict_note": "追撃族 5/5 命名吻合；EnchantWeapon/其他族 49 条不能确认同语义。",
        "our_evidence": {"has_stronger": False, "level": "无（我方未研究）",
                         "paths": ["output/reference_analysis/claude_cc_site_pages/README.md §5.2（10-17 已列为代码确认候选：29/29 决定性命中）"],
                         "note": "我方 rules.json 无 skilllist|1029；本次给出族分布与 5/59 命名级分母。"},
        "samples": [{"cid": 1298, "record": "skilllist 75008001 p0=0.05（追撃1_5%）"},
                    {"cid": 354, "record": "40035318 p0=0.5（EnchantWeapon，无倍率名）"}],
    })

    claims.append({
        "id": 13, "short": "范围格数 1 格 = 1.5 游戏单位",
        "declaration": "1 格 = 1.5 游戏单位（参数 ÷ 1.5 保留两位）。",
        "denominator": None,
        "actual": ("我方 rules.json 与全部 output/character_skills 文档中**没有任何「格」单位规则**（grep 无命中）。"
                   "几何槽与 1.5 整数倍的相容度：type112 爆炸半径 10.5（91/96 是 1.5 倍数）；"
                   "type22 前方到达延长 80/121；type105 范围长度 81/142；type3 范围长度 53/234；type47 半径 2/17。"),
        "hits": ("type112 的 10.5 = 7×1.5、type105 的 6.75/7.5/15、type3 的 4.5/3 等都与 1.5 体系相容 —— "
                 "数据不反对这个单位，但也无法排除其它单位。"),
        "counter_examples": [
            "反例：type47 半径 1.75×8（1.75/1.5 非整数）、type3 范围长度 3.5×60、type105 3.75/5.75。",
            "若单位取 0.75，type22 前方到达延长 105/121 命中，比 1.5 的 80/121 更好 —— 数据同样支持「0.75 单位」，无法区分。",
        ],
        "verdict": "无法判定",
        "verdict_note": "我方无「格」规则、无原生几何证据；数据与 1.5 相容但也与 0.75 相容。",
        "our_evidence": {"has_stronger": False, "level": "无", "paths": [],
                         "note": "该规则只影响显示层换算，不影响数值本身。"},
        "samples": [{"cid": None, "record": "bossskill type112 (96 条) p2/p3=10.5×91"}],
    })

    claims.append({
        "id": 14, "short": "攻击间隔按 0.1 秒截断 + 退出问题",
        "declaration": "攻击间隔显示按 0.1 秒截断（1.0125/1.05→1.0、1.505/1.575→1.5、1.8×0.5→0.9）；退出问题：游戏是否按帧/0.1 秒取整？",
        "denominator": it["sa2012_p6_records"],
        "actual": ("charainfo atkspeed 18 个取值（1.5×829、2×300、1.75×159、2.5×47、3×38、4×31、1.25×20、0.5×14…），"
                   "APK 29 个（含 2.1×2、2.2×12）。SA2012 p6 %d 条：−0.325×91、−0.3、−0.3125、−0.33、−0.2。"
                   % it["sa2012_p6_records"]),
        "hits": ("**5 个显示样例中 4 个可由本快照复现**：1.0125=1.5×0.675（=1+p6[−0.325]）、"
                 "1.05=1.5×0.7 或 1.4×0.75、1.575=2.1×0.75（APK atkspeed 2.1 × type57 p4=0.75）、0.9=1.2×0.75；"
                 "且这 5 个显示值全部等于 floor(x/0.1)×0.1（round 会把 1.575→1.6）→ 所称口径是「截断」而非「四舍五入」。"),
        "counter_examples": [
            "**1.505 无法由本快照任意 atkspeed×间隔倍率组合复现（0 命中）**；0.5 这个倍率在间隔类槽位（2012 p6、57 p4、7 p7）中未出现，故 1.8×0.5=0.9 的两个因数在本快照凑不齐（0.9 只能由 1.2×0.75 得到）。",
            "**退出问题无证据**：我方只确认游戏时间按 UnityEngine.Time.fixedDeltaTime 步进（output/card_comparison_cid30236/timed_support/README.md），没有「显示/生成层取整到 0.1 秒或到帧」的任何原生证据。",
            "我方 rules.json 没有任何 atkspeed 量化规则。",
        ],
        "verdict": "部分成立",
        "verdict_note": "「乘积来源 + floor 到 0.1」在 4/5 样例上可复现；1.505 不可复现；帧/0.1 秒取整（退出问题）无法判定。",
        "our_evidence": {"has_stronger": False, "level": "无（只有时间步进的间接证据）",
                         "paths": ["output/card_comparison_cid30236/timed_support/README.md（GetDeltaTime=fixedDeltaTime，游戏秒）"],
                         "note": "我方无 atkspeed 显示取整规则；对方这条是显示层口径。"},
        "samples": [{"cid": 89, "record": "atkspeed 1.5 × (1+(-0.325)) = 1.0125（SA 40008912）"},
                    {"cid": None, "record": "type57 p4=0.75 与 APK atkspeed 2.1 → 1.575"}],
    })

    claims.append({
        "id": 15, "short": "回复超上限标志位",
        "declaration": "skillflag0_1 / skillflag1_1（type64 用后者）位 256/512/1024/2048/4096 → 超上限 20/40/60/80/100%。",
        "denominator": 54 + 33 + 26,
        "actual": ("bossskill：**type27 %d/54 条用 skillflag0_1**（2048×18、1024×15、4096×14、512×6），0 条用 skillflag1_1；"
                   "**type64 33/33 条用 skillflag1_1**（2048×13、1024×10、4096×10），0 条用 skillflag0_1 → 「type64 用后者」成立。"
                   "skilllist：flag0_1 主要在 ability21(24)/1092(25)/1095(22)/19(16)；flag1_1 主要在 3000(109)/70(33)/1037(26)。"
                   "ability21 的 %d/26 条用 flag0_1（512×13、256×9、4096×2）。"
                   % (fl["type27"]["present"], fl["ability21"]["present"])),
        "hits": ("位表 256/512/1024/2048/4096 → 20/40/60/80/100% **与我方 boss_heal 常量表一致**"
                 "（bit[40,35,41,42,43,44]→[1.2,1.3,1.4,1.6,1.8,2.0]，含 bit35→1.3 且「从高位往低位取首个置位」已原生确认）。"
                 "数据侧新证据：type3000 有正文的 199 条中，正文含「上限を超えて」的 107 条有 81 条带 flag1_1"
                 "（512×56、256×25），不含该词的 92 条**零**带 flag1_1 → flag1_1 就是超上限位。"),
        "counter_examples": [
            "同一字段还承载非超上限位：bossskill skillflag0_1 出现 4×10、1×1；skilllist flag0_1 出现 16×4 → 不能「任意置位即按百分比」。",
            "256/512 也出现在非回复类型（1092 的 25 条=256、1095 的 16×256/6×512、70 的 7×256），无条件套用会造出假的超上限。",
            "skilllist 正文含「上限を超えて」的 285 条里只有 96 条带 flag 位，189 条两字段都没有（超上限量可能由 p5 等其它槽或兄弟记录承载）→ 标志位不是唯一来源。",
        ],
        "verdict": "成立",
        "verdict_note": "位表与字段分工成立；适用面需限定在回复类记录（同字段还承载其它位、且在非回复类型上出现同值）。",
        "our_evidence": {"has_stronger": True, "level": "原生确认（boss 侧）",
                         "paths": ["output/boss_heal/README.md + constants.json + checks.json（13 项原生：7 标志选择 + 6 HP 上限边界）",
                                   "output/character_skills/profiles/rules.json（bossskill|27|/skillflag0_1）",
                                   "output/character_skills/boss_heal_types/README.md（仅 act∈{0,4,5,6} 合入 HealSkill_HealFlag）"],
                         "note": "我方覆盖 boss 侧位表与选择算法（更强）；skilllist 侧（3000 flag1_1=超上限）是我方缺的，本次补上。"},
        "samples": [{"cid": None, "record": "bossskill 40232701 type27 skillflag0_1=1024→60%"},
                    {"cid": None, "record": "type64 skillflag1_1=2048→80%"},
                    {"cid": 223, "record": "skilllist 40022310 flag1_1=512（正文「HPが上限を超えて回復」）"}],
    })

    claims.append({
        "id": 16, "short": "缓存主表省略值为 0 的字段",
        "declaration": "charainfo.jobtype 与 weaponlist.type 缺失即 0（0=战士 / 斩）。",
        "denominator": z["jobtype_cache"]["records"],
        "actual": ("charainfo %d 条中 jobtype 只出现 %d 条，取值仅 1/2/3/4，**从不出现 0**；缺 jobtype 的 %d 条中能在 APK 找到同 cid 的 %d 条，"
                   "**APK jobtype 全部为 0（%d/%d）**；带 jobtype 且 APK 也有的 %d 条两侧完全一致（%d 同 / %d 异）。"
                   "weaponlist %d 条中 type 出现 %d 条，取值 1–6、8–11，**从无 0**；缺失 %d 条的名称基本都是刀剑类"
                   "（ノーマルソード/カタナ/斬馬刀/レイピア…）。"
                   % (z["jobtype_cache"]["records"], z["jobtype_cache"]["present"],
                      z["jobtype_missing_vs_apk"]["missing"], z["jobtype_missing_vs_apk"]["apk_found"],
                      z["jobtype_missing_vs_apk"]["apk_jobtype_0"], z["jobtype_missing_vs_apk"]["apk_found"],
                      z["jobtype_present_vs_apk"]["same"] + z["jobtype_present_vs_apk"]["diff"],
                      z["jobtype_present_vs_apk"]["same"], z["jobtype_present_vs_apk"]["diff"],
                      z["weaponlist_type"]["records"], z["weaponlist_type"]["present"],
                      z["weaponlist_type"]["missing"])),
        "hits": ("jobtype 缺失即 0：48/48 可核对样本一致；且 0 在缓存侧从不出现（分布与「0 被省略」一致）。"
                 "weaponlist.type 缺失即 0：0 在缓存侧从不出现，缺失项名称几乎全是斩类武器。"),
        "counter_examples": [
            "575 条缺 jobtype 的缓存记录中 527 条在 APK 找不到同 cid（多为敌用/较新卡），这部分只能靠「0 从不出现」外推，无法逐条核对。",
            "weaponlist 缺 type 的 823 条里约 461 条名称不含明显刀剑词（如「グルグラム」「グリーフサイズ」，仍多为剑），无法 100% 逐条确认是「斩」。",
            "缓存侧 jobtype 也从不出现 5(ALMIGHTY)，说明省略的不只是 0。",
        ],
        "verdict": "成立",
        "verdict_note": "两条「缺失即 0」均可独立证实；未核对部分已标明口径。",
        "our_evidence": {"has_stronger": False, "level": "我方无专门规则（只有枚举定义）",
                         "paths": ["output/character_skills/README.md §职业（JOB_TYPE 0 戦士…5 ALMIGHTY 枚举）"],
                         "note": "我方文档没有「缺失即 0」的文字结论；对方这条对我方是新信息，已独立证实。"},
        "samples": [{"cid": 351, "record": "charainfo 缺 jobtype（=0 战士），APK 同 cid jobtype=0"},
                    {"cid": None, "record": "weaponlist id 1 ノーマルソード 无 type（=0 斩）"}],
    })

    claims.append({
        "id": 17, "short": "SA(2012) 承载必杀增益暴击 + 按(表,ID)区分",
        "declaration": "必杀增益的暴击率/威力在 SA(type2012) 里，且数值归属按（表,ID）区分；skilllist 与 bossskill 同号 ID 会串值。",
        "denominator": n["id_overlap"]["bossskill_ids"],
        "actual": ("bossskill %d 个 skillid 中有 **%d 个（%.1f%%）与 skilllist 同号**。同号不同义实例：40008903 = "
                   "skilllist ability99（p7/p8/p9=−0.3/−0.3/+0.3）与 bossskill type74（p1=0.6、p2=3555、p3=32.75…）。"
                   "SA 链：bossskill 带 s_ability 的 954 条中 %d 条指向 skilllist 2012（307 有 p4、310 有 p5）；"
                   "charainfo.s_ability 150 条中 22 条指向 2012。"
                   % (n["id_overlap"]["bossskill_ids"], n["id_overlap"]["numeric_overlap"],
                      100.0 * n["id_overlap"]["overlap_ratio_of_bossskill"],
                      n["sa_ability_targets"]["bossskill_sa_2012"]["n"])),
        "hits": ("「必杀增益暴击率/威力在 SA(type2012)」成立（397 条 bossskill SA + 22 条 charainfo SA）；"
                 "「按（表,ID）区分」成立（2583 对同号，类型/语义/参数全不同）。"),
        "counter_examples": [
            "2012 的 p4/p5 同时存在时 **308/308 数值完全相等** → 不能靠数值判断哪个是暴击率、哪个是暴伤（必须用我方原生：p4→_critical、p5→_criticalDmgRate）。",
            "28 条 s_ability 指向的 id 不在 skilllist（跨表缺失），不能假设 SA 一定能在 skilllist 找到。",
        ],
        "verdict": "成立",
        "verdict_note": "两条子主张均成立，且我方数据模型已把命名空间分开（更强）。",
        "our_evidence": {"has_stronger": True, "level": "数据模型 + 原生",
                         "paths": ["output/character_skills/effect_ledger/README.md（namespace=layer/table/record_id/source_key，同号跨源不合并）",
                                   "output/character_skills/charainfo_types/README.md（charainfo.skillid[0] 与 bossskill.skillid0 同域；普通/Boss 分开）",
                                   "AGENTS.md §5（APK／缓存快照／普通／Boss 命名空间分开，同号 ID 不自动合并）",
                                   "output/character_skills/profiles/rules.json（规则键 skilllist|… / bossskill|… 自带命名空间）"],
                         "note": "对方此前的 Value.gid 串值 bug 我方 10-17 分析已记录（§3 修复项）。"},
        "samples": [{"cid": 89, "record": "skilllist 40008903(ability99) vs bossskill 40008903(type74)"},
                    {"cid": 354, "record": "bossskill 40035402.s_ability=40035412 → skilllist 2012 p4/p5"}],
    })
    return claims


def build_new_evidence():
    return [
        {"topic": "skilllist type3000 p3 = 移動速度",
         "evidence": "记录自带正文含「移動速度」的 41 条中 39 条有 p3；不含的 158 条 0 条有 p3。",
         "impact": "我方 rules.json 与 yg_priority_list.md 均把 p3 列为未定，可直接补规则（对象/资格仍需按 b7 既有门控）。",
         "grade": "数据内证（文本×槽位），建议升为「类型外推/待原生复核」"},
        {"topic": "skilllist type3000 p4 = 防御力",
         "evidence": "正文含「防御力」109 条中 91 条有 p4，不含的 90 条仅 2 条有；p4 恒等于 −p1/4（148/148）。",
         "impact": "补上我方明确未定的属性段；量纲/基数（受伤量乘算 vs 敌ATK 固定防御）仍需原生核写入字段。",
         "grade": "数据内证（文本×槽位）"},
        {"topic": "skilllist 侧超上限位（flag1_1 on ability3000）",
         "evidence": "3000 有正文 199 条：含「上限を超えて」107 条中 81 条带 flag1_1（512×56、256×25）；不含的 92 条 0 条带。",
         "impact": "我方目前只确认了 bossskill 侧（type27 flag0_1 / type64 flag1_1）；skilllist 侧可补同一位置表。",
         "grade": "数据内证；位表数值沿用 boss_heal 已确认常量"},
        {"topic": "type99 开发命名作为第二独立证据",
         "evidence": "127007/127008/127009「敵攻撃/敵移動/敵防御 20秒10%DOWN」分别只带 p7/p8/p9；75013001/2/3「攻撃力/防御力/移動速度_5%」分别只带 p7/p9/p8。",
         "impact": "可加入 rules.json skilllist|99 的 evidence，减少对原生单一来源的依赖，并作为对方文档纠错依据。",
         "grade": "命名级强证据（与原生一致）"},
        {"topic": "type2012 p6 候选语义（攻击间隔/攻击速度）",
         "evidence": "97 条（−0.325×91）；cid89 アセス 正文「自身の攻撃速度が一定時間上がる」且其 SA 只带 p6；1.5×(1−0.325)=1.0125、1.5×(1−0.3)=1.05。",
         "impact": "我方 ability2012 原生只核了 p0/p4/p5，p6 的写入字段未定位；建议作为原生专项候选（不要直接按 (1+p6) 写死）。",
         "grade": "单例内证 + 数值巧合，未达确认"},
        {"topic": "type1009 法珠数分级公式",
         "evidence": "137002「攻撃1.04～1.072」、137003「攻撃1.125～1.225」与 1+p1×k×m_k（k=1/3）完全吻合，k3/k1=1.8。",
         "impact": "可作公式候选；属性槽 p2–p5 语义与 k=2 中间档仍缺证据。",
         "grade": "命名级数值证据（2/2）"},
        {"topic": "type1029 追击倍率（族内）",
         "evidence": "名称里带真倍率（小数点/百分号）的 5 条全部与 p0 一致（5/5：134001 的 0.05、领袖追撃 5%/10%/15%/2.5%）；但 23 条 EnchantWeapon、25 条其他族无证据。",
         "impact": "可作候选但必须限定族；不能整型套用（p0=1 的 37 条尤其不能当「1 倍追击」直接写）。",
         "grade": "命名级强证据（限定范围）"},
        {"topic": "type58 Guts 的 p4 实际取值分布（纠正下游页面）",
         "evidence": "玩家卡 50000×3（cid8399/20105/20306）、100000×2（cid351、骑士通用 65000005）；敌用 450000 / 1e8。",
         "impact": "对方「职业通用 100000、网站写 50000 是错的」不成立；若下游按 100000 统一填会改错 3 张卡。",
         "grade": "解包原值（直接可读）"},
    ]


def build_contradictions():
    return [
        "**【8】type99 三处矛盾**：对方 `param_table` CONFIRMED「param8=防御力 −x×100%」；`HANDOFF.md` §5 又写「p7/p8 = 攻击/防御，p9 = 移动速度」；而数据（开发命名 127007/8/9、75013001/2/3）与我方 192 项原生检查一致指向 **p7=攻击、p8=移动速度、p9=防御(受伤量)**。两个错误版本都会导致页面上「移动速度」与「防御力」互换数值（数值大小相同，纯文字页看不出，但自动填入会错配）。",
        "**【9】type13 p6**：`NUMBER_RULES.md` 仍写「p6=暴击威力（网站实测）」，`HANDOFF.md` 已改为「p6=移动速度」。数据上 p6 与 p2 715/715 完全相等，页面上 p2/p6 数值必然相同 → 这两种说法在页面上**不可区分**，只有原生代码能判定（我方已确认 p6=移动速度）。旧版 NUMBER_RULES 不应再被引用。",
        "**【15】超上限位**：`UPDATE_追加指令.md` 说「41/42/43 位代码确认、40/44 位仅网站实测」，并称 `ability21` 也套同一规则；我方 boss_heal 常量表是整表 [40,35,41,42,43,44]→[1.2,1.3,1.4,1.6,1.8,2.0] 原生确认（含排列顺序与反序选择），且实际记录只出现 512/1024/2048/4096。`HANDOFF.md` §5 写的「skilllist 看 flag0_1 和 flag1_1」需要限定为回复类记录——skilllist 的 flag1_1 主要出现在 ability3000（共鸣 buff），flag0_1 出现在 21/1092/1095/19 等混合类型，同值 256/512 在非回复类型上也大量存在。",
        "**【5】type58**：`HANDOFF.md` 称「p4 复活 HP 回复量（职业通用 100000，网站写 50000 是错的，用户确认）」，但数据里 3 张玩家卡就是 50000，且骑士通用记录（100000）与骑士卡（50000）矛盾 → 「网站写 50000 是错的」至少对 3 张卡不成立。",
        "**【10】type28**：`HANDOFF.md` 写「p3–p5 为地形条件下的追加几率」，但我方原生路径只读 p4/p5，param3 从未被读取（mana_chance/README.md 明确不能按对称性补 p3）。",
        "**【6】type2012 p4/p5**：对方把 p4/p5 写成两个独立标签（暴击率/暴击威力），但数据上 308/308 条完全相等 —— 对方能区分两者只能是因为它的输入来自我方/原项目，其自身统计无法区分；引用时应注明依据来自本项目原生证据。",
    ]


def main():
    p = load("params_claims.json")
    f = load("flags_units_claims.json")
    n = load("namespace_claim.json")
    claims = build_claims(p, f, n)
    verdicts = Counter(c["verdict"] for c in claims)
    doc = {
        "generated_by": "scripts/refcheck_20261023_lead/verify_build_report.py",
        "generated_at": "2026-10-23",
        "scope": {
            "reviewed": "其他人的参考/claude_cc_site_pages 20261023 的 HANDOFF §5 与 10-22/10-23 章节、NUMBER_RULES.md、UPDATE_追加指令.md、param_table.json（17 条规则声明）",
            "data": ["output/cache_full_20261015_v3/decoded/*.data5.json.raw（skilllist/bossinfo/charainfo/weaponlist/sympathy_skilllist/leaderabilityinfo/extraabilitylist/jobabilityinfo）",
                     "output/base_master/_mdCharacter.json"],
            "not_read": ["output/reference_analysis/claude_cc_site_pages_20261023/",
                         "scripts/ref_analysis_claude_cc_20261023.py",
                         "docs/tasks/20261023-reference-analysis.md"],
            "method": "数据分布（分母/命中/反例优先）+ 数据内证（记录自带日文效果文本、开发命名、技能名显式数值）+ 我方既有原生证据对照；不使用对方文档结论作为依据。",
        },
        "summary": {"total": len(claims), "verdicts": dict(verdicts),
                    "sub_item_refuted": ["5:职业通用100000", "10:p3 属地形追加"]},
        "claims": claims,
        "contradictions_in_opponent_docs": build_contradictions(),
        "new_evidence_for_us": build_new_evidence(),
        "reproduce_commands": REPRO,
        "outputs": {"report": "work/refcheck_20261023_lead/verify/REPORT.md",
                    "results": "work/refcheck_20261023_lead/verify/verify_results.json",
                    "intermediate": ["params_claims.json", "flags_units_claims.json", "namespace_claim.json"]},
    }
    write_json(RESULTS, doc)
    write_report(doc)
    print("wrote", RESULTS)
    print("wrote", REPORT)
    print("verdicts:", dict(verdicts))


def write_report(doc):
    L = []
    A = L.append
    A("# 复核报告：claude_cc_site_pages 20261023 的 17 条数值规则（我方原始解包数据独立复核）")
    A("")
    A("复核日期：2026-10-23　｜　数据快照：`output/cache_full_20261015_v3/decoded/`（v3）＋ `output/base_master/`")
    A("")
    A("方法：**只读我方原始解包数据**，对每条声明给「分母 + 命中数 + 反例」，并附三类独立证据：")
    A("①数据分布（每类型取值分布／缺失与 0 的区分）；②数据内证（记录自带的日文效果文本、开发命名、技能名里显式写出的数值）；")
    A("③我方既有原生证据对照（`output/boss_heal/`、`output/boss_chain/`、`output/ordinary_effects/`、`rules.json`、`dispatch_map.json`）。")
    A("对方文档的结论**不作为**判断依据；也未读取禁读路径与其他并行对话产物。")
    A("")
    A("## 0. 结论速览")
    A("")
    s = doc["summary"]
    A("| 判定 | 条数 | 条目 |")
    A("|---|---|---|")
    vd = s["verdicts"]
    for label in ("成立", "部分成立", "不成立", "无法判定"):
        ids = [str(c["id"]) for c in doc["claims"] if c["verdict"] == label]
        A("| %s | %d | %s |" % (label, vd.get(label, 0), "、".join(ids) or "—"))
    A("")
    A("- **整体不成立：0 条**；但 2 条含**明确被数据推翻的子断言**：")
    for x in s["sub_item_refuted"]:
        A("  - %s" % x)
    A("- 最关键的 5 项：①**type99 的 p8/p9 语义**（我方数据+命名+原生三重一致，对方文档两个版本都错）；")
    A("  ②**type13 类「值恒等」陷阱**（p2≡p6 715/715，页面上看不出差别，只有原生能判）；")
    A("  ③**type58 的「职业通用 100000」被数据推翻**（3 张玩家卡是 50000）；")
    A("  ④**type3000 的 p4=防御力、p3=移動速度、flag1_1=超上限** 是我方原先明确未定、本次由记录自带正文拿到的**新证据**；")
    A("  ⑤**type28 的 p3** 被我方原生路径证明「未被读取」，对方把它当地形追加几率是错的。")
    A("")
    A("## 1. 逐条结论总表")
    A("")
    A("| # | 声明（要点） | 我方数据实际（分母/命中/反例） | 判定 | 我方是否已有更强证据 | 样例 |")
    A("|---|---|---|---|---|---|")
    for c in doc["claims"]:
        actual = c["actual"].replace("\n", " ")
        if len(actual) > 330:
            actual = actual[:330] + "…"
        ev = c["our_evidence"]
        evtxt = ("**有**（%s）：%s" % (ev["level"], ev["paths"][0]) if ev["has_stronger"]
                 else "无（%s）" % ev["level"])
        samples = "；".join(("cid%s %s" % (x["cid"], x["record"])) if x["cid"] else x["record"]
                            for x in c["samples"][:2])
        A("| %d | %s | %s | **%s** | %s | %s |" %
          (c["id"], c["short"], actual, c["verdict"], evtxt, samples.replace("|", "\\|")))
    A("")
    A("## 2. 逐条详证（反例优先）")
    A("")
    for c in doc["claims"]:
        A("### %d. %s —— **%s**" % (c["id"], c["short"], c["verdict"]))
        A("")
        A("- 声明：%s" % c["declaration"])
        if c.get("denominator"):
            A("- 分母：%s 条记录" % c["denominator"])
        A("- 我方数据实际：%s" % c["actual"])
        A("- 命中/支持：%s" % c["hits"])
        A("- 反例与缺口：")
        for x in c["counter_examples"]:
            A("  - %s" % x)
        A("- 判定：**%s** —— %s" % (c["verdict"], c["verdict_note"]))
        ev = c["our_evidence"]
        A("- 我方既有证据：%s" % ("**更强**" if ev["has_stronger"] else ev["level"]))
        for pth in ev["paths"]:
            A("  - `%s`" % pth)
        A("  - 备注：%s" % ev["note"])
        A("")
    A("## 3. 对方文档内部矛盾（本次数据复核可裁决的部分）")
    A("")
    for x in doc["contradictions_in_opponent_docs"]:
        A("- %s" % x)
    A("")
    A("## 4. 对我方有价值的新证据（本次复核产出）")
    A("")
    A("| 主题 | 证据 | 影响 | 证据等级 |")
    A("|---|---|---|---|")
    for x in doc["new_evidence_for_us"]:
        A("| %s | %s | %s | %s |" % (x["topic"], x["evidence"], x["impact"], x["grade"]))
    A("")
    A("## 5. 复现与产物")
    A("")
    A("脚本（前缀 `verify_`，均只读 `output/`）：")
    A("")
    A("```powershell")
    for cmd in doc["reproduce_commands"]:
        A(cmd)
    A("```")
    A("")
    A("产物：")
    for k, v in doc["outputs"].items():
        if isinstance(v, list):
            A("- %s：%s" % (k, "、".join("`%s`" % i for i in v)))
        else:
            A("- %s：`%s`" % (k, v))
    A("")
    A("## 6. 局限")
    A("")
    A("- 全程未抓网站、未重跑对方管线：对方「页面显示值」只能拿我方数据去复现乘积来源，不能核对网站文本本身。")
    A("- 「记录自带文本」只覆盖一部分记录（skilllist 2261/8634 有真实效果文本，其余是「…のサブアビリティ」占位），")
    A("  因此 type1074/1051/1009 的属性槽归属无法判定。")
    A("- 原生证据只引用我方既有产物，本轮**没有新增反汇编/受控原生实验**；凡标「未定」的都仍是未定。")
    A("- 统计口径：所有分母都是**当前 v3 缓存快照**的记录数，APK 主表只在 type16/14 的两处对照中使用，两域不合并。")
    A("")
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


if __name__ == "__main__":
    main()
