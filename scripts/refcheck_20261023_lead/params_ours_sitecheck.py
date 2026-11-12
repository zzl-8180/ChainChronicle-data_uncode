# -*- coding: utf-8 -*-
"""params_ours_sitecheck.py — 我方已确认语义 ↔ 对方网站统计命中率（对方表里的 hits/cards_with_value）。

我方语义来自 output/ordinary_effects/*、output/boss_chain、output/boss_heal 与 10-17 核对：
  skilllist 7/1008：p1 攻击力 (x-1)，p3 防御力 (1-x)
  skilllist 1017：p1 攻击力，p3 防御力（+ p2 未知）
  skilllist 1095：p1 攻击力，p2 移动因子，p3 防御力，p5 暴击率加算，p6 暴伤 delta(=p6-1.5)
  skilllist 3000：p1 普攻倍率加算，p2 技能倍率加算，p6 持续时间，p8 暴伤系数加算
  skilllist 99：p0 时间，p1/2/3 触发阈值，p4/5/6 自身 attack/move/defense，p7 目标 attack，p8 目标 move，p9 目标 defense
  skilllist 2003：p0 时间，p7 目标 attack，p8 目标 move，p9 目标 defense
  skilllist 2012：p0 时间(游戏秒)，p4 暴击率加算(pp)，p5 暴伤系数加算，p7 数量上限，p8 TARGET_TYPE
  bossskill 13：p1 攻击力 x100，p2 防御力 ATK*x10%，p3 秒，p6 移动速度 x100
  bossskill 27：p1 回复倍，p2 间隔秒，p3 次
  bossskill 105：p1 伤害倍，p6 次
  bossskill 112：p1 伤害倍，p4 间隔秒，p5 次，p7 推力(无换算)，p8 九位置掩码
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
import params_common as P  # noqa: E402

OURS = [
    ("skilllist", 7, "param1", "攻击力 (x-1)x100 %"), ("skilllist", 7, "param3", "防御力 (1-x)x100 %"),
    ("skilllist", 1008, "param1", "攻击力"), ("skilllist", 1008, "param3", "防御力"),
    ("skilllist", 1017, "param1", "攻击力"), ("skilllist", 1017, "param3", "防御力"),
    ("skilllist", 1095, "param1", "攻击力"), ("skilllist", 1095, "param2", "移动因子（乘算）"),
    ("skilllist", 1095, "param3", "防御力"), ("skilllist", 1095, "param5", "暴击率加算(pp)"),
    ("skilllist", 1095, "param6", "暴伤 delta=p6-1.5"),
    ("skilllist", 3000, "param1", "普攻倍率加算"), ("skilllist", 3000, "param2", "技能倍率加算"),
    ("skilllist", 3000, "param6", "持续时间(游戏秒)"), ("skilllist", 3000, "param8", "暴伤系数加算"),
    ("skilllist", 99, "param0", "时间"), ("skilllist", 99, "param1", "Normal 触发阈值"),
    ("skilllist", 99, "param2", "Critical 触发阈值"), ("skilllist", 99, "param3", "Skill 触发阈值"),
    ("skilllist", 99, "param4", "自身 _attack"), ("skilllist", 99, "param5", "自身 _move"),
    ("skilllist", 99, "param6", "自身 _defense"), ("skilllist", 99, "param7", "目标 _attack"),
    ("skilllist", 99, "param8", "目标 _move"), ("skilllist", 99, "param9", "目标 _defense"),
    ("skilllist", 2003, "param0", "时间"), ("skilllist", 2003, "param4", "自身 _attack"),
    ("skilllist", 2003, "param5", "自身 _move"), ("skilllist", 2003, "param6", "自身 _defense"),
    ("skilllist", 2003, "param7", "目标 _attack"), ("skilllist", 2003, "param8", "目标 _move"),
    ("skilllist", 2003, "param9", "目标 _defense"),
    ("skilllist", 2012, "param0", "时间(游戏秒)"), ("skilllist", 2012, "param4", "暴击率加算(pp)"),
    ("skilllist", 2012, "param5", "暴伤系数加算"), ("skilllist", 2012, "param7", "数量上限"),
    ("skilllist", 2012, "param8", "TARGET_TYPE"),
    ("bossskill", 13, "param1", "攻击力 x100"), ("bossskill", 13, "param2", "防御力 ATK*x10"),
    ("bossskill", 13, "param3", "持续时间秒"), ("bossskill", 13, "param6", "移动速度 x100"),
    ("bossskill", 27, "param1", "回复倍"), ("bossskill", 27, "param2", "间隔秒"), ("bossskill", 27, "param3", "次"),
    ("bossskill", 105, "param1", "伤害倍"), ("bossskill", 105, "param6", "次"),
    ("bossskill", 112, "param1", "伤害倍"), ("bossskill", 112, "param4", "间隔秒"), ("bossskill", 112, "param5", "次"),
    ("bossskill", 112, "param7", "推力(无换算)"), ("bossskill", 112, "param8", "九位置掩码"),
]
new = P.load(P.NEW1 / "param_table.json")
rows = {P.key(r): r for r in new["rows"]}
print(f"{'table':10s} {'type':5s} {'slot':8s} {'我方语义':22s} {'对方标签':10s} {'hits/all':>12s} {'dec':>9s}  status")
agree_n = tot = 0
for t, ty, slot, ours in OURS:
    r = rows.get((t, ty, slot))
    if not r:
        print(f"{t:10s} {ty:5d} {slot:8s} {ours:22s} {'—— 无行 ——'}")
        continue
    tot += 1
    agree = r["label"] in ours or ours in (r["label"] or "")
    agree_n += bool(agree)
    print(f"{t:10s} {ty:5d} {slot:8s} {ours:22s} {r['label'] or '-':10s} "
          f"{r['hits']:5d}/{r['cards_with_value']:<6d} {r['decisive_hits']:4d}/{r['decisive_cases']:<4d} "
          f"{r['status']}{'' if agree else '   <- 标签不一致'}")
print(f"\n我方已确认语义中，对方表存在对应行 {tot} 条，标签一致 {agree_n} 条")
