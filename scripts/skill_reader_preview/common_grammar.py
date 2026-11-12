"""Conservative full-match translations for recurring Japanese skill clauses.

This module changes display wording only. It does not read or infer numeric answers.
Unsupported or only partially recognized sentences return None.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


ATTRIBUTES = {
    "攻撃力": "攻击力",
    "防御力": "防御力",
    "移動速度": "移动速度",
    "クリティカル発生率": "暴击率",
    "クリティカル威力": "暴击威力",
    "威力": "威力",
}
OBJECTS = {
    "戦場にいる味方": "战场上我方",
    "味方全体": "我方全体",
    "攻撃した敵": "受到攻击的敌人",
    "自身": "自身",
    "味方": "我方",
    "範囲内の味方": "范围内我方",
}


def _attrs(text: str) -> str | None:
    """Parse an exact Japanese attribute list joined only by と."""
    parts = text.split("と")
    if not parts or any(part not in ATTRIBUTES for part in parts):
        return None
    return "、".join(ATTRIBUTES[p] for p in parts)


def _grammar(sentence: str) -> str | None:
    # Normalizing only Japanese full-width Arabic digits is safe: the source
    # token itself supplies the value, and no value is inferred from data.
    sentence = sentence.translate(str.maketrans("０１２３４５６７８９", "0123456789"))

    # Full-match area-attack grammar. Magnitude and action labels are mapped
    # only when the complete clause matches these known forms.
    m = re.fullmatch(r"(?:その後、)?(前方範囲内|直線範囲上)の全ての敵に(小|中|大)ダメージを与え(?:、弾き飛ばし、(ダウン|呪い)にする|、弾き飛ばす|、(転倒|ダウン)させる)?。", sentence)
    if m:
        area, magnitude, status1, status2 = m.groups()
        size = {"小": "小", "中": "中", "大": "大"}[magnitude]
        target = "前方范围内" if area == "前方範囲内" else "直线范围上"
        tail = "并弹飞" if "弾き飛ば" in sentence else ""
        status = status1 or status2
        if status:
            status_zh = {"ダウン": "眩晕", "転倒": "击倒", "呪い": "诅咒"}[status]
            tail += f"，使其陷入{status_zh}状态"
        return ("之后，" if sentence.startswith("その後") else "") + f"对{target}的全部敌人造成{size}伤害{tail}。"

    m = re.fullmatch(r"(?:直線範囲上|前方範囲内)にいる全ての敵に(\d+)回ダメージを与え、弾き飛ばし、暗闇/スロウ/ダウンにする。", sentence)
    if m:
        area = "直线范围上" if sentence.startswith("直線") else "前方范围内"
        return f"对{area}的全部敌人造成{m[1]}次伤害并弹飞，使其陷入暗盲、缓速和眩晕状态。"
    m = re.fullmatch(r"(?:直線範囲上|前方範囲内)にいる全ての敵に(\d+)回ダメージを与え、転倒させる。", sentence)
    if m:
        area = "直线范围上" if sentence.startswith("直線") else "前方范围内"
        return f"对{area}的全部敌人造成{m[1]}次伤害并使其倒地。"
    m = re.fullmatch(r"(?:直線範囲上|前方範囲内)の全ての敵に(\d+)回ダメージを与え、転倒させる。", sentence)
    if m:
        area = "直线范围上" if sentence.startswith("直線") else "前方范围内"
        return f"对{area}的全部敌人造成{m[1]}次伤害并使其倒地。"
    m = re.fullmatch(r"(?:直線範囲上|前方範囲内)にいる全ての敵に一定間隔でダメージを与える。", sentence)
    if m:
        area = "直线范围上" if sentence.startswith("直線") else "前方范围内"
        return f"每隔一段时间对{area}的全部敌人造成伤害。"
    if sentence == "ダッシュ範囲上にいる全ての敵に中ダメージを与え、さらに弾き飛ばす。":
        return "对冲刺范围内的全部敌人造成中伤害并弹飞。"
    m = re.fullmatch(r"(?:直線範囲上|前方範囲内)にいる全ての敵に一定間隔でダメージを与え、弾き飛ばす。", sentence)
    if m:
        area = "直线范围上" if sentence.startswith("直線") else "前方范围内"
        return f"每隔一段时间对{area}的全部敌人造成伤害并弹飞。"

    # Backline bonuses are stated as three independent percentages. Keep each
    # source value attached to its own attribute.
    m = re.fullmatch(r"サブパーティにいると、メインパーティの攻撃力が(\d+)%上がり、防御力が(\d+)%上がり、移動速度が(\d+)%上がる。", sentence)
    if m:
        atk, defense, speed = m.groups()
        return f"自身处于后备队伍时，主要队伍攻击力提高{atk}%、防御力提高{defense}%、移动速度提高{speed}%。"

    # Reflecting ranged attacks: percentage is damage reduction before
    # reflection; do not reinterpret it as reflected damage.
    m = re.fullmatch(r"また遠距離通常攻撃のダメージを(\d+)%下げ、敵を貫通して反射する。", sentence)
    if m:
        return f"此外，受到的远距离通常攻击伤害降低{m[1]}%，并将攻击以可贯穿敌人的形式反射。"

    # Explicit no-mana activation, limited to the stated one use.
    m = re.fullmatch(r"マナを1つも所持していない時、(\d+)回だけ必殺技を発動できる。", sentence)
    if m:
        return f"1颗法珠也未持有时，仅可发动必杀技{m[1]}次。"
    m = re.fullmatch(r"ただし、最大で(\d+)マナまでしか所持できない。", sentence)
    if m:
        return f"但最多只能持有{m[1]}颗法珠。"

    # Common conditions and combined numeric clauses.
    m = re.fullmatch(r"残りHPが(\d+)分の(\d+)(以上|以下)の場合、攻撃力が増加し、受けるダメージが減少する。", sentence)
    if m:
        den, num, bound = m.groups()
        relation = "至少" if bound == "以上" else "至多"
        return f"剩余HP{relation}{num}/{den}时，攻击力提高，受到的伤害减少。"
    m = re.fullmatch(r"残りHPが(\d+)分の(\d+)(以上|以下)になると攻撃力が増加する。", sentence)
    if m:
        den, num, bound = m.groups()
        relation = "达到或高于" if bound == "以上" else "降至或低于"
        return f"剩余HP{relation}{num}/{den}时，攻击力提高。"
    m = re.fullmatch(r"残りHPが(\d+)分の(\d+)(以上|以下)になると受けるダメージが減少する。", sentence)
    if m:
        den, num, bound = m.groups()
        relation = "达到或高于" if bound == "以上" else "降至或低于"
        return f"剩余HP{relation}{num}/{den}时，受到的伤害减少。"
    m = re.fullmatch(r"攻撃力が(\d+)%上がり、(\d+)WAVE進むたび、全ての職業で使用できるマナを(\d+)つ獲得する。", sentence)
    if m:
        pct, waves, mana = m.groups()
        return f"攻击力提高{pct}%；每推进{waves}个WAVE，获得{mana}颗全职业通用法珠。"
    m = re.fullmatch(r"(\d+)WAVE進むたび、全ての職業で使用できるマナを(\d+)つ獲得する。", sentence)
    if m:
        waves, mana = m.groups()
        return f"每推进{waves}个WAVE，获得{mana}颗全职业通用法珠。"
    m = re.fullmatch(r"また敵を(\d+)体倒すたび、全ての職業で使用できるマナを(\d+)つ獲得する。", sentence)
    if m:
        kills, mana = m.groups()
        return f"此外，每击败{kills}名敌人，获得{mana}颗全职业通用法珠。"
    m = re.fullmatch(r"攻撃力が(\d+)%上がり、戦場にいるHPが上限を超えた味方の攻撃力が(\d+)%上がる。", sentence)
    if m:
        own, ally = m.groups()
        return f"攻击力提高{own}%；战场上HP超过上限的我方队员，攻击力提高{ally}%。"
    m = re.fullmatch(r"攻撃力が(\d+)%上がり、マナを所持していると味方全体の攻撃力が(\d+)%上がる。", sentence)
    if m:
        own, ally = m.groups()
        return f"攻击力提高{own}%；持有法珠时，我方全体攻击力提高{ally}%。"
    m = re.fullmatch(r"攻撃力が(\d+)%上がり、ボスWAVE時、味方全体の攻撃力が(\d+)%上がる。", sentence)
    if m:
        own, ally = m.groups()
        return f"攻击力提高{own}%；Boss WAVE期间，我方全体攻击力提高{ally}%。"

    # Chain and mana wording only when its complete trigger is present.
    m = re.fullmatch(r"また自身以外の味方が(\d+)(?:st|nd|rd|th)Chainを達成した時、次に自身が必殺技を発動する時に必要なマナが(\d+)つ減る。", sentence)
    if m:
        chain, mana = m.groups()
        suffix = {"1": "st", "2": "nd", "3": "rd"}.get(chain, "th")
        return f"此外，自身以外的我方队员达成{chain}{suffix}Chain后，自身下一次发动必杀技所需法珠减少{mana}颗。"
    if sentence == "マナの獲得はChain数に応じて確率が上がり、MaxChain時は必ず獲得する。":
        return "获得法珠的概率随Chain数增加；达到MaxChain时必定获得。"
    if sentence == "Chain毎におじゃまぷよの威力が上がる。":
        return "障碍ぷよ的威力随Chain数提高。"
    if sentence == "味方がマナを消費すると、同じChain内で次に使用する必殺技の威力が上がる。":
        return "我方消耗法珠后，同一Chain内下一次发动的必杀技威力提高。"
    if sentence == "1stChain以上で必殺技の威力と味方にかかる効果が上がる。":
        return "达到1stChain以上时，必杀技威力及赋予我方的效果提高。"
    if sentence == "1stChain以上で必殺技の威力と回復量と味方にかかる効果が上がる。":
        return "达到1stChain以上时，必杀技威力、回复量及赋予我方的效果提高。"
    if sentence == "1stChain以上で必殺技の威力と敵と味方にかかる効果が上がる。":
        return "达到1stChain以上时，必杀技威力及赋予敌我双方的效果提高。"
    m = re.fullmatch(r"(\d+)ndChain以上で必殺技を発動する時に必要なマナが(\d+)つ減る。", sentence)
    if m:
        return f"达到{m[1]}ndChain以上时，发动必杀技所需法珠减少{m[2]}颗。"
    m = re.fullmatch(r"(\d+)ndChain以上で威力が上がり、(ダウン効果を追加する|弾き飛ばす効果が上がる)。", sentence)
    if m:
        effect = "追加眩晕效果" if m[2] == "ダウン効果を追加する" else "弹飞效果增强"
        return f"达到{m[1]}ndChain以上时，威力提高，并{effect}。"

    # Mana quantity and activation changes.
    m = re.fullmatch(r"最大マナ数が(\d+)つ増加する。", sentence)
    if m:
        return f"最大法珠数增加{m[1]}颗。"
    if sentence == "最大マナ数の増加量が多いほど効果が上がり、さらにクリティカル発生率とクリティカル威力が上がる。":
        return "最大法珠数增加越多，效果越强；暴击率和暴击威力也会提高。"
    if sentence == "マナが多いほど効果が上がる。":
        return "持有的法珠越多，效果越强。"
    if sentence == "マナが多いほど必殺技の威力が上がる。":
        return "持有的法珠越多，必杀技威力越高。"
    if sentence == "マナを所持していると効果が上がり、マナが多いほど効果が上がる。":
        return "持有法珠时效果提高，法珠越多效果越强。"
    m = re.fullmatch(r"(\d+)マナ以上所持している時、効果が上がる。", sentence)
    if m:
        return f"持有至少{m[1]}颗法珠时，效果提高。"
    if sentence == "また自身の攻撃速度が一定時間上がる。":
        return "此外，自身攻击速度在一定时间内提高。"
    m = re.fullmatch(r"その間、自身の攻撃力が(\d+)%上がり、ダメージを受けない。", sentence)
    if m:
        return f"期间自身攻击力提高{m[1]}%，且不会受到伤害。"
    m = re.fullmatch(r"HPが(\d+)上がる。", sentence)
    if m:
        return f"HP提高{m[1]}。"

    # High-frequency pending formulations, kept as independent complete clauses.
    if sentence == "味方が必殺ボタンを使用して必殺技を発動すると、同じChain内で次に使用する必殺技の威力が上がる。":
        return "我方使用必杀按钮发动必杀技后，同一Chain内下一次发动的必杀技威力提高。"
    m = re.fullmatch(r"その後、前方範囲内の全ての敵に(小|中|大)ダメージを与え、弾き飛ばす。", sentence)
    if m:
        size = {"小": "小", "中": "中", "大": "大"}[m[1]]
        return f"之后，对前方范围内的全部敌人造成{size}伤害并弹飞。"
    if sentence == "戦闘不能になった際に1回耐え、HPが回復し、一定時間ダメージを受けなくなる。":
        return "受到致命伤时可承受1次，随后回复HP，并在一定时间内不会受到伤害。"
    if sentence == "敵を倒した時、一定確率でマナを獲得する。":
        return "击败敌人时，有一定概率获得法珠。"
    if sentence == "この必殺技で敵を倒した時、一定確率でマナを獲得する。":
        return "用此必杀技击败敌人时，有一定概率获得法珠。"
    if sentence == "バリアは炎/氷属性ダメージも防ぐ。":
        return "防护罩也能抵挡火属性和冰属性伤害。"
    if sentence == "また自身の攻撃速度が一定時間上がる。":
        return "此外，自身攻击速度在一定时间内提高。"
    if sentence == "移動することで効果時間が延長される。":
        return "移动会延长效果持续时间。"
    if sentence == "反響範囲内の敵を攻撃した際、同範囲内の敵全てにダメージの一部を与える。":
        return "攻击反响范围内的敌人时，也会对该范围内的全部敌人造成部分伤害。"
    if sentence == "その後、味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。":
        return "之后，在一定时间内每隔一段时间小幅回复我方全体HP，回复可超过上限。"
    if sentence == "サブパーティにいると、メインパーティの攻撃力と防御力と移動速度が上がる。":
        return "自身处于后备队伍时，主要队伍的攻击力、防御力和移动速度提高。"
    if sentence == "サブパーティにいると、メインパーティの攻撃力と防御力が上がる。":
        return "自身处于后备队伍时，主要队伍的攻击力和防御力提高。"
    if sentence == "自身がサブパーティにいると、メインパーティの攻撃力と防御力が上がる。":
        return "自身处于后备队伍时，主要队伍的攻击力和防御力提高。"
    if sentence == "この効果は5人まで上昇する。":
        return "此效果随人数提升，最多按5人计算。"
    m = re.fullmatch(r"この効果は(\d+)人まで上昇する。", sentence)
    if m:
        return f"此效果随人数提升，最多按{m[1]}人计算。"
    if sentence == "また戦闘時、味方の戦士と魔法使いの攻撃力と防御力と移動速度が上がる。":
        return "战斗中，我方战士和法师的攻击力、防御力和移动速度提高。"
    if sentence == "戦闘時、味方の戦士と弓使いの攻撃力と防御力と移動速度が上がる。":
        return "战斗中，我方战士和弓手的攻击力、防御力和移动速度提高。"
    if sentence == "戦闘時、味方の戦士と魔法使いの攻撃力と防御力と移動速度が上がる。":
        return "战斗中，我方战士和法师的攻击力、防御力和移动速度提高。"
    if sentence == "また1stChain以上を達成した時、一定確率で万象マナを1つ獲得する。":
        return "此外，达成1stChain以上时，有一定概率获得1颗万象法珠。"
    if sentence == "また2ndChainを達成した時、全ての職業で使用できるマナを1つ獲得する。":
        return "此外，达成2ndChain时，获得1颗全职业通用法珠。"
    if sentence == "また2ndChainを達成した時、全ての職業で使用できるマナを2つ獲得する。":
        return "此外，达成2ndChain时，获得2颗全职业通用法珠。"
    if sentence == "また3rdChainを達成した時、全ての職業で使用できるマナを1つ獲得する。":
        return "此外，达成3rdChain时，获得1颗全职业通用法珠。"
    if sentence == "また3rdChainを達成した時、全ての職業で使用できるマナを2つ獲得する。":
        return "此外，达成3rdChain时，获得2颗全职业通用法珠。"
    if sentence == "所持できるマナの数が1つ増える。":
        return "可持有的法珠数量增加1颗。"
    if sentence == "この効果は2回まで発動する。":
        return "此效果最多发动2次。"
    if sentence == "範囲攻撃を行うと元に戻る。":
        return "进行范围攻击后恢复原状。"
    if sentence == "味方全体のHPを小回復する。":
        return "小幅回复我方全体HP。"
    if sentence == "同時に味方全体のHPを上限を超えて中回復する。":
        return "同时中幅回复我方全体HP，回复可超过上限。"
    if sentence == "その後、味方全体のHPを上限を超えて中回復する。":
        return "之后中幅回复我方全体HP，回复可超过上限。"
    if sentence == "その後、味方全体のHPを上限を超えて小回復する。":
        return "之后小幅回复我方全体HP，回复可超过上限。"
    if sentence == "その後、味方全体のHPを上限を超えて中回復し、全状態異常を回復する。":
        return "之后中幅回复我方全体HP（可超过上限），并解除全部异常状态。"
    if sentence == "ただし、連続では発動しない。":
        return "但不会连续发动。"
    if sentence == "また最大時、自身の攻撃速度が一定時間上がる効果が追加される。":
        return "此外，达到最大时会追加自身攻击速度在一定时间内提高的效果。"
    if sentence == "敵を10体倒すたび、全ての職業で使用できるマナを1つ獲得する。":
        return "每击败10名敌人，获得1颗全职业通用法珠。"
    if sentence == "また敵を10体倒すたび、全ての職業で使用できるマナを2つ獲得する。":
        return "此外，每击败10名敌人，获得2颗全职业通用法珠。"
    if sentence == "この技は初回のみ1マナで発動できる。":
        return "此技能仅首次可消耗1颗法珠发动。"
    if sentence == "この必殺技は初回のみ使用可能。":
        return "此必杀技仅限首次使用。"
    if sentence == "マナスロット時にマナが2つ以上出やすくなる。":
        return "转动法珠槽时，更容易出现2颗以上法珠。"
    if sentence == "通常回復の回復量が上がり、回復範囲が広がる。":
        return "通常回复量提高，回复范围扩大。"
    if sentence == "その間、ダメージを受けない。":
        return "期间不会受到伤害。"
    if sentence == "光球は敵を転倒させる。":
        return "光球会使敌人倒地。"
    if sentence == "また設置範囲内の味方が一定時間、戦闘不能にならなくなる。":
        return "此外，设置范围内的我方队员在一定时间内不会陷入战斗不能状态。"
    if sentence == "WAVEが進むたび、味方全体のHPが回復する。":
        return "每推进一个WAVE，我方全体HP回复。"
    if sentence == "近接通常攻撃力が上がり、攻撃間隔が早くなる。":
        return "近战通常攻击力提高，攻击间隔缩短。"
    if sentence == "攻撃間隔が早くなり、敵の攻撃で弾き飛ばなくなる。":
        return "攻击间隔缩短，且不会被敌人攻击弹飞。"
    if sentence == "マナスロットの回転速度が遅くなる。":
        return "法珠槽转动速度变慢。"
    if sentence == "戦闘で獲得するゴールドが増える。":
        return "战斗中获得的金币增加。"
    if sentence == "戦闘で獲得する経験値が増える。":
        return "战斗中获得的经验值增加。"
    if sentence == "バリアは防御力を上げ、全状態異常を防ぎ、攻撃を反射する。":
        return "防护罩会提高防御力、防止全部异常状态，并反射攻击。"
    if sentence == "バリアは防御力を上げ、攻撃を反射する。":
        return "防护罩会提高防御力并反射攻击。"
    if sentence == "その後、前方範囲内の全ての敵に大ダメージを与え、弾き飛ばす。":
        return "之后，对前方范围内的全部敌人造成大伤害并弹飞。"
    if sentence == "前方範囲内の全ての敵に小ダメージを与える。":
        return "对前方范围内的全部敌人造成小伤害。"
    if sentence == "前方範囲内の全ての敵に中ダメージを与える。":
        return "对前方范围内的全部敌人造成中伤害。"
    if sentence == "【共鳴必殺/連撃】直線範囲上にいる全ての敵に一定間隔でダメージを与え、弾き飛ばす。":
        return "【共鸣必杀/连击】每隔一段时间对直线范围上的全部敌人造成伤害并弹飞。"
    if sentence == "【連撃】直線範囲上にいる全ての敵に一定間隔でダメージを与え、弾き飛ばす。":
        return "【连击】每隔一段时间对直线范围上的全部敌人造成伤害并弹飞。"
    if sentence == "【連撃】前方範囲内の全ての敵に15回ダメージを与え、弾き飛ばし、暗闇/スロウ/ダウンにする。":
        return "【连击】对前方范围内的全部敌人造成15次伤害并弹飞，使其陷入暗盲、缓速和眩晕状态。"
    if sentence == "【共鳴必殺/連撃】前方範囲内の全ての敵に4回ダメージを与え、転倒させる。":
        return "【共鸣必杀/连击】对前方范围内的全部敌人造成4次伤害并使其倒地。"
    if sentence == "【共鳴必殺/連撃】前方範囲内の全ての敵に2回ダメージを与え、転倒させる。":
        return "【共鸣必杀/连击】对前方范围内的全部敌人造成2次伤害并使其倒地。"
    if sentence == "【共鳴必殺/連撃】前方範囲内の全ての敵に5回ダメージを与え、転倒させる。":
        return "【共鸣必杀/连击】对前方范围内的全部敌人造成5次伤害并使其倒地。"
    if sentence == "【共鳴必殺/連撃】前方範囲内の全ての敵に8回ダメージを与え、転倒させる。":
        return "【共鸣必杀/连击】对前方范围内的全部敌人造成8次伤害并使其倒地。"
    if sentence == "【共鳴必殺/連撃】前方範囲内の全ての敵に小ダメージを与え、転倒させる。":
        return "【共鸣必杀/连击】对前方范围内的全部敌人造成小伤害并使其倒地。"
    if sentence == "【共鳴必殺/連撃】前方範囲内の全ての敵に大ダメージを与え、弾き飛ばし、ダウンにする。":
        return "【共鸣必杀/连击】对前方范围内的全部敌人造成大伤害并弹飞，使其眩晕。"
    if sentence == "【共鳴必殺/連撃】前方範囲内の全ての敵に中ダメージを与え、弾き飛ばし、ダウンにする。":
        return "【共鸣必杀/连击】对前方范围内的全部敌人造成中伤害并弹飞，使其眩晕。"
    if sentence == "【連撃】前方範囲内の全ての敵に中ダメージを与え、弾き飛ばし、ダウンにする。":
        return "【连击】对前方范围内的全部敌人造成中伤害并弹飞，使其眩晕。"
    if sentence == "【連撃】前方範囲内の全ての敵に中ダメージを与え、弾き飛ばす。":
        return "【连击】对前方范围内的全部敌人造成中伤害并弹飞。"
    if sentence == "【英雄技】直線範囲上にいる全ての敵に一定間隔でダメージを与える。":
        return "【英雄技能】每隔一段时间对直线范围上的全部敌人造成伤害。"
    if sentence == "【英雄技】ダッシュ範囲上にいる全ての敵に中ダメージを与え、さらに弾き飛ばす。":
        return "【英雄技能】对冲刺路径上的全部敌人造成中伤害并弹飞。"
    if sentence == "バリアは防御無視攻撃によるダメージと炎/氷属性ダメージも防ぐ。":
        return "防护罩也能抵挡无视防御的攻击伤害，以及火、冰属性伤害。"
    if sentence == "ただし、自身がヒロイックスキルに設定されているときは発動しない。":
        return "但自身被设为英雄技能时，此效果不会发动。"
    if sentence == "1stChain以上で必殺技を発動する時に必要なマナが1つ減り、必殺技の威力と味方にかかる効果が上がる。":
        return "达到1stChain以上时，发动必杀技所需法珠减少1颗，且必杀技威力及赋予我方的效果提高。"
    if sentence == "1stChain以上で必殺技を発動する時に必要なマナが1つ減り、必殺技の威力と敵と味方にかかる効果が上がる。":
        return "达到1stChain以上时，发动必杀技所需法珠减少1颗，且必杀技威力及赋予敌我双方的效果提高。"
    if sentence == "2ndChain以上で必殺技を発動する時に必要なマナが2つ減り、必殺技の威力と味方にかかる効果が上がる。":
        return "达到2ndChain以上时，发动必杀技所需法珠减少2颗，且必杀技威力及赋予我方的效果提高。"
    if sentence == "さらに遠距離通常攻撃の弾速が早くなり、敵を貫通するようになり、貫通するたびに威力を増す。":
        return "此外，远距离通常攻击弹速加快并可贯穿敌人，每次贯穿后威力提高。"
    if sentence == "さらに遠距離通常攻撃の弾速が早くなり、敵を貫通するようになり、貫通するたびに威力を増し、盾を破壊する。":
        return "此外，远距离通常攻击弹速加快并可贯穿敌人，每次贯穿后威力提高，并能破坏盾牌。"
    if sentence == "さらに攻撃時、攻撃した敵の攻撃力と防御力と移動速度が一定時間下がる。":
        return "此外，攻击时会使受到攻击的敌人攻击力、防御力和移动速度在一定时间内降低。"
    if sentence == "その後、自身以外の味方の攻撃力と防御力と移動速度を一定時間上げる。":
        return "之后，在一定时间内提高自身以外我方队员的攻击力、防御力和移动速度。"
    if sentence == "さらに自身以外の味方の攻撃力と防御力と移動速度を一定時間上げる。":
        return "此外，在一定时间内提高自身以外我方队员的攻击力、防御力和移动速度。"
    if sentence == "自身を含む味方が必殺技を発動するたび、味方全体のHPが回復する。":
        return "每当包含自身在内的我方队员发动必杀技，我方全体回复HP。"
    if sentence == "自身を含む<味方>が≪共鳴必殺≫を発動するたび、戦場にいる<味方>の攻撃力が一定時間上がり、HPが上限を超えて回復する。":
        return "每当包含自身在内的我方队员发动共鸣必杀，战场上我方攻击力在一定时间内提高，并回复HP（可超过上限）。"
    if sentence == "自身を含む<味方>が≪共鳴必殺≫を発動するたび、戦場にいる<味方>の攻撃力とクリティカル威力が一定時間上がり、HPが上限を超えて回復する。":
        return "每当包含自身在内的我方队员发动共鸣必杀，战场上我方攻击力和暴击威力在一定时间内提高，并回复HP（可超过上限）。"
    if sentence == "ボスWAVE時、自身を含む<味方>が≪共鳴必殺≫を発動するたび、戦場にいる<味方>のクリティカル威力が一定時間上がる。":
        return "Boss WAVE期间，每当包含自身在内的我方队员发动共鸣必杀，战场上我方暴击威力在一定时间内提高。"
    if sentence == "WAVEが進むたび、最もHPの低い自身を含む味方1人を回復する。":
        return "每推进一个WAVE，回复包含自身在内的我方队员中HP最低的1人。"
    if sentence == "その後、味方全体にダメージを受けるたびに上限を超えて小回復し、全状態異常を回復する効果を与える。":
        return "之后，赋予我方全体以下效果：每次受到伤害时小幅回复HP（可超过上限），并解除全部异常状态。"
    if sentence == "またクリティカル攻撃時、クリティカル攻撃が5回になり、クリティカル威力が上がり、範囲攻撃になる。":
        return "此外，暴击攻击变为5次攻击，暴击威力提高，并变为范围攻击。"
    if sentence == "戦場に自身以外の味方がいると効果が上がり、さらにクリティカル発生率とクリティカル威力が上がり、HPが徐々に回復する。":
        return "战场上有自身以外的我方队员时效果提高，暴击率和暴击威力也会提高，HP逐渐回复。"
    if sentence == "戦場に自身以外の味方がいると効果が上がり、さらにクリティカル威力が上がり、HPが徐々に回復する。":
        return "战场上有自身以外的我方队员时效果提高，暴击威力也会提高，HP逐渐回复。"
    if sentence == "自身より後ろに味方がいると効果が上がり、さらにクリティカル発生率とクリティカル威力が上がり、HPが徐々に回復する。":
        return "自身后方有我方队员时效果提高，暴击率和暴击威力也会提高，HP逐渐回复。"
    if sentence == "戦場に自身以外の味方がいると効果が上がり、さらにクリティカル発生率とクリティカル威力が上がる。":
        return "战场上有自身以外的我方队员时效果提高，暴击率和暴击威力也会提高。"
    if sentence == "戦場に自身以外の味方がいると効果が上がり、さらにクリティカル威力が上がる。":
        return "战场上有自身以外的我方队员时效果提高，暴击威力也会提高。"
    if sentence == "戦闘時、移動速度が上昇する。":
        return "战斗中移动速度提高。"
    if sentence == "その後、一定時間、味方全体の通常攻撃に追撃を付加する。":
        return "之后，在一定时间内为我方全体的通常攻击附加追击效果。"
    if sentence == "必殺技で倒すと獲得しやすくなる。":
        return "用必杀技击败敌人时，法珠更容易掉落。"
    if sentence == "クリティカル攻撃か必殺技で倒すと獲得しやすくなる。":
        return "以暴击攻击或必杀技击败敌人时，法珠更容易掉落。"
    if sentence == "また設置範囲内の味方が一定時間、戦闘不能にならなくなる。":
        return "此外，设置范围内的我方队员在一定时间内不会陷入战斗不能状态。"
    if sentence == "また最大時、自身の攻撃速度が一定時間上がる効果が追加される。":
        return "此外，达到最大时会追加自身攻击速度在一定时间内提高的效果。"
    if sentence == "その後、前方範囲内の全ての敵に大ダメージを与え、弾き飛ばし、スロウ/ダウンにする。":
        return "之后，对前方范围内的全部敌人造成大伤害并弹飞，使其陷入缓速和眩晕状态。"
    m = re.fullmatch(r"使用すると必殺技を発動する時に必要なマナが(\d+)つ減り、必殺技の威力と味方にかかる効果が上がり、最大(\d+)回まで変動する。", sentence)
    if m:
        return f"使用后，发动必杀技所需法珠减少{m[1]}颗，必杀技威力及赋予我方的效果提高；最多变化{m[2]}次。"
    m = re.fullmatch(r"使用すると必殺技を発動する時に必要なマナが(\d+)つ減り、必殺技の威力と敵と味方にかかる効果が上がり、最大(\d+)回まで変動する。", sentence)
    if m:
        return f"使用后，发动必杀技所需法珠减少{m[1]}颗，必杀技威力及赋予敌我双方的效果提高；最多变化{m[2]}次。"
    if sentence == "遠距離通常攻撃のダメージを下げ、敵を貫通して反射する。":
        return "远距离通常攻击造成的伤害降低，并会贯穿敌人后反射。"
    if sentence == "その後、設置範囲内の全ての敵の攻撃力と防御力を下げる。":
        return "之后，降低设置范围内全部敌人的攻击力和防御力。"
    if sentence == "さらに自身の攻撃速度が一定時間上がる。":
        return "此外，自身攻击速度在一定时间内提高。"
    if sentence == "また自身の攻撃速度が一定時間上がる。":
        return "此外，自身攻击速度在一定时间内提高。"
    if sentence == "戦闘時、味方の戦士と弓使いと魔法使いの攻撃力と防御力と移動速度が上がる。":
        return "战斗中，我方战士、弓手和法师的攻击力、防御力及移动速度提高。"
    if sentence == "その後、味方全体のHPを上限を超えて中回復する。":
        return "之后中幅回复我方全体HP，回复可超过上限。"
    if sentence == "その後、味方全体のHPを上限を超えて小回復する。":
        return "之后小幅回复我方全体HP，回复可超过上限。"
    if sentence == "自身より後ろに味方がいると効果が上がり、さらにクリティカル発生率とクリティカル威力が上がる。":
        return "自身后方有我方队员时效果提高，暴击率和暴击威力也会提高。"
    if sentence == "戦場に自身以外の味方がいると効果が上がり、さらにクリティカル発生率とクリティカル威力が上がる。":
        return "战场上有自身以外的我方队员时效果提高，暴击率和暴击威力也会提高。"
    if sentence == "通常回復の回復量が上がり、回復範囲が広がる。":
        return "通常回复量提高，回复范围扩大。"
    if sentence == "遠距離通常攻撃の威力が上がり、弾速が早くなり、敵を貫通するようになり、貫通するたびに威力を増す。":
        return "远距离通常攻击威力提高、弹速加快并可贯穿敌人；每次贯穿后威力提高。"
    if sentence == "HPが25%以上の時、効果が上がり、さらにクリティカル発生率とクリティカル威力が上がる。":
        return "HP在25%以上时，效果提高，暴击率和暴击威力也会提高。"
    if sentence == "バリアは防御力を上げ、全状態異常を防ぎ、攻撃を反射する。":
        return "防护罩会提高防御力、防止全部异常状态，并反射攻击。"
    if sentence == "バリアは防御力を上げ、攻撃を反射する。":
        return "防护罩会提高防御力并反射攻击。"
    if sentence == "一定時間が経過すると効果が上がる。":
        return "经过一段时间后，效果提高。"
    if sentence == "その後、味方全体にダメージを受けるたびに上限を超えて小回復する効果を与える。":
        return "之后，使我方全体每次受到伤害时都小幅回复HP，回复可超过上限。"
    if sentence == "必殺技の威力と回復量と味方にかかる効果は使用すると上がり、最大1回まで上がる。":
        return "发动后，必杀技威力、回复量及赋予我方的效果会提高；最多提高1次。"
    if sentence == "必殺技の威力と敵と味方にかかる効果は使用するたびに上がり、最大2回まで上がる。":
        return "每次发动后，必杀技威力及赋予敌我双方的效果都会提高；最多提高2次。"
    if sentence == "この必殺技で敵を倒した時、全ての必殺技が使えるマナを獲得する。":
        return "用此必杀技击败敌人时，获得可用于所有必杀技的法珠。"
    if sentence == "【英雄技】ダッシュ範囲上にいる全ての敵に中ダメージを与え、さらに弾き飛ばす。":
        return "【英雄技能】对冲刺路径上的全部敌人造成中伤害并弹飞。"
    if sentence == "【英雄技】直線範囲上にいる全ての敵に一定間隔でダメージを与える。":
        return "【英雄技能】每隔一段时间对直线范围上的全部敌人造成伤害。"
    if sentence == "またスロウにならない。":
        return "此外，不会陷入缓速状态。"
    if sentence == "また暗闇にならない。":
        return "此外，不会陷入暗盲状态。"
    if sentence == "また凍結にならない。":
        return "此外，不会陷入冻结状态。"
    if sentence == "敵の攻撃で弾き飛ばなくなり、全状態異常にならない。":
        return "不会被敌人攻击弹飞，也不会陷入任何异常状态。"
    if sentence == "バリアは防御力を上げ、全状態異常を防ぎ、攻撃を反射する。":
        return "防护罩会提高防御力、防止全部异常状态，并反射攻击。"
    if sentence == "バリアは防御力を上げ、攻撃を反射する。":
        return "防护罩会提高防御力并反射攻击。"
    if sentence == "また遠距離通常攻撃のダメージを90%下げ、敵を貫通して反射する。":
        return "此外，受到的远距离通常攻击伤害降低90%，并将攻击以可贯穿敌人的形式反射。"
    if sentence == "また遠距離通常攻撃のダメージを50%下げ、敵を貫通して反射する。":
        return "此外，远距离通常攻击造成的伤害降低50%，并会贯穿敌人后反射。"
    if sentence == "また遠距離通常攻撃のダメージを60%下げ、敵を貫通して反射する。":
        return "此外，远距离通常攻击造成的伤害降低60%，并会贯穿敌人后反射。"
    if sentence == "また遠距離通常攻撃のダメージを70%下げ、敵を貫通して反射する。":
        return "此外，远距离通常攻击造成的伤害降低70%，并会贯穿敌人后反射。"
    if sentence == "また遠距離通常攻撃のダメージを80%下げ、敵を貫通して反射する。":
        return "此外，远距离通常攻击造成的伤害降低80%，并会贯穿敌人后反射。"

    # Numeric enemy-count and generic direct-damage clauses.
    m = re.fullmatch(r"(?:また)?敵を(\d+)体倒すたび、全ての職業で使用できるマナを(\d+)つ獲得する。", sentence)
    if m:
        return f"每击败{m[1]}名敌人，获得{m[2]}颗全职业通用法珠。"
    m = re.fullmatch(r"(?:前方範囲内|直線範囲上)の全ての敵に(小|中|大)ダメージを与え、弾き飛ばす。", sentence)
    if m:
        size = {"小": "小", "中": "中", "大": "大"}[m[1]]
        area = "前方范围内" if sentence.startswith("前方") else "直线范围上"
        return f"对{area}的全部敌人造成{size}伤害并弹飞。"
    m = re.fullmatch(r"その後、前方範囲内の全ての敵に(小|中|大)ダメージを与え、弾き飛ばし、(ダウン|呪い)にする。", sentence)
    if m:
        size = {"小": "小", "中": "中", "大": "大"}[m[1]]
        status = {"ダウン": "眩晕", "呪い": "诅咒"}[m[2]]
        return f"之后，对前方范围内的全部敌人造成{size}伤害并弹飞，使其陷入{status}状态。"
    m = re.fullmatch(r"(?:その後、)?前方範囲内の全ての敵に(\d+)回ダメージを与え、弾き飛ばし、暗闇/スロウ/ダウンにする。", sentence)
    if m:
        return f"对前方范围内的全部敌人造成{m[1]}次伤害并弹飞，使其陷入暗盲、缓速和眩晕状态。"
    m = re.fullmatch(r"直線範囲上の全ての敵に(小|中|大)ダメージを与え、弾き飛ばす。", sentence)
    if m:
        size = {"小": "小", "中": "中", "大": "大"}[m[1]]
        return f"对直线范围上的全部敌人造成{size}伤害并弹飞。"

    # Resonance ability trigger with explicit self-inclusive ally scope.
    m = re.fullmatch(r"自身を含む<味方>が≪共鳴必殺≫を発動するたび、戦場にいる<味方>の(.+?)が一定時間上がる。", sentence)
    if m:
        attrs = _attrs(m[1])
        if attrs:
            return f"每当包含自身在内的我方队员发动共鸣必杀，战场上我方的{attrs}在一定时间内提高。"

    # Explicit duration, immunity, and per-hit recovery.
    if sentence == "またスロウにならない。":
        return "此外，不会陷入缓速状态。"
    if sentence == "また暗闇にならない。":
        return "此外，不会陷入暗盲状态。"
    if sentence == "また凍結にならない。":
        return "此外，不会陷入冻结状态。"
    m = re.fullmatch(r"(\d+)体以上の味方がいる時、効果が上がる。", sentence)
    if m:
        return f"我方至少有{m[1]}名队员时，效果提高。"

    # Subject + attributes + rise/fall, with an optional explicit duration.
    m = re.fullmatch(r"(?:(その後、|さらに|また|同時に))?(?:(戦場にいる味方|味方全体|攻撃した敵|自身|味方|範囲内の味方)の)?(.+?)が(一定時間)?(上がる|下がる)。", sentence)
    if m:
        adverb, obj, raw_attrs, duration, direction = m.groups()
        attrs = _attrs(raw_attrs)
        if attrs:
            subject = (OBJECTS[obj] + "的") if obj else ""
            time = "在一定时间内" if duration else ""
            verb = "提高" if direction == "上がる" else "降低"
            lead = {"その後、": "之后，", "さらに": "此外，", "また": "此外，", "同時に": "同时，"}.get(adverb, "")
            return f"{lead}{subject}{attrs}{time}{verb}。"

    # Same scope, but the source uses the transitive 上げる form.
    m = re.fullmatch(r"(さらに|また|その後、)?(?:(戦場にいる味方|味方全体|攻撃した敵|自身|味方|範囲内の味方)の)?(.+?)を(一定時間)?上げる。", sentence)
    if m:
        adverb, obj, raw_attrs, duration = m.groups()
        attrs = _attrs(raw_attrs)
        if attrs:
            subject = (OBJECTS[obj] + "的") if obj else ""
            time = "在一定时间内" if duration else ""
            lead = {"その後、": "之后，", "さらに": "此外，", "また": "此外，"}.get(adverb, "")
            return f"{lead}{subject}{attrs}{time}提高。"

    # Exact, high-frequency standalone clauses. Do not generalize partial phrases.
    exact = {
        "この効果はサブパーティでも発動する。": "此效果在后备队伍时也会发动。",
        "この効果は、サブパーティでも発動する。": "此效果在后备队伍时也会发动。",
        "発動中は移動と通常攻撃ができない。": "效果发动期间无法移动或进行通常攻击。",
        "ただし、連続で発動しない。": "但不会连续发动。",
        "ただし連続で発動しない。": "但不会连续发动。",
        "また、同じChain内で1回しか発動しない。": "此外，同一Chain内最多发动1次。",
        "同じChain内で1回しか発動しない。": "同一Chain内最多发动1次。",
        "ただし同じChain内で1つしか獲得できない。": "但同一Chain内最多只能获得1个。",
        "ただし、この効果で0マナにはならない。": "但此效果不会使法珠消耗降至0颗。",
        "この効果で0マナにはならない。": "此效果不会使法珠消耗降至0颗。",
        "この技は0マナで発動できる。": "此技能可消耗0颗法珠发动。",
        "この技は0マナで発動でき、発動時、万象マナを1つ獲得する。": "此技能可消耗0颗法珠发动，发动时获得1颗万象法珠。",
        "全ての必殺技が使えるマナを1つ持った状態で戦闘を開始する。": "战斗开始时持有1颗可用于所有必杀技的法珠。",
        "全ての職業で使用できるマナを1つ持った状態で戦闘を開始する。": "战斗开始时持有1颗全职业通用法珠。",
        "全ての職業で使用できるマナを2つ持った状態で戦闘を開始する。": "战斗开始时持有2颗全职业通用法珠。",
        "マナを1つ持った状態で戦闘を開始する。": "战斗开始时持有1颗法珠。",
        "マナを2つ持った状態で戦闘を開始する。": "战斗开始时持有2颗法珠。",
        "マナを１つ持った状態で戦闘を開始する。": "战斗开始时持有1颗法珠。",
        "時の楔を1つ持った状態で戦闘を開始する。": "战斗开始时持有1个时之楔。",
        "この効果は戦闘に参加していない場合でも発動する。": "即使未参加战斗，此效果也会发动。",
        "その後、一定間隔ごとにランダムで敵1体とその周囲に小ダメージを与え、転倒させる。": "之后，每隔一段时间随机对1名敌人及其周围造成小伤害，并使其倒地。",
        "攻撃間隔が早くなる。": "攻击间隔缩短。",
        "攻撃する度に効果時間が延長される。": "每次攻击都会延长效果持续时间。",
        "効果はWAVE中続き、WAVEが進むたびに上書きされる。": "效果持续至本WAVE结束，并在进入下一WAVE时覆盖。",
        "自身の場合、効果が上がる。": "作用于自身时，效果提高。",
        "効果には上限があり、移動すると元に戻る。": "效果有上限，移动后恢复原状。",
        "止まっていると効果が徐々に上がる。": "静止不动时，效果逐渐提高。",
    }
    if sentence in exact:
        return exact[sentence]

    # Numeric grammar: preserve only numbers/units literally present in source.
    m = re.fullmatch(r"(攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力|威力)が(\d+(?:\.\d+)?)%(一定時間)?上がる。", sentence)
    if m:
        attr, value, duration = m.groups()
        lead = "在一定时间内，" if duration else ""
        return f"{lead}{ATTRIBUTES[attr]}提高{value}%。"
    m = re.fullmatch(r"味方が必殺ボタンを使用して必殺技を発動すると、同じChain内で次に使用する必殺技のChainによる威力の上昇量が(\d+)%上がる。", sentence)
    if m:
        return f"我方使用必杀按钮发动必杀技后，同一Chain内下一次必杀技由Chain带来的威力提升量增加{m[1]}%。"
    m = re.fullmatch(r"(攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力|威力)が上がる。", sentence)
    if m:
        return f"{ATTRIBUTES[m[1]]}提高。"

    m = re.fullmatch(r"1stChain以上で必殺技を発動する時に必要なマナが(\d+)つ減る。", sentence)
    if m:
        return f"达到1stChain以上时，发动必杀技所需法珠减少{m[1]}颗。"
    m = re.fullmatch(r"この効果は戦闘中に(\d+)回のみ発動する。", sentence)
    if m:
        return f"此效果在每场战斗中仅发动{m[1]}次。"
    m = re.fullmatch(r"効果はそれぞれが(\d+)回ダメージを受けるまで続く。", sentence)
    if m:
        return f"此效果对各对象分别持续，直到该对象受到{m[1]}次伤害。"
    m = re.fullmatch(r"攻撃は(\d+)回まで継続する。", sentence)
    if m:
        return f"攻击最多持续{m[1]}次。"
    m = re.fullmatch(r"(\d+)回ダメージを与え、弾き飛ばす。", sentence)
    if m:
        return f"造成{m[1]}次伤害并弹飞敌人。"
    return None


def translate(japanese: str) -> str | None:
    """Translate a fully recognized sentence; return None if any clause is unknown."""
    if not isinstance(japanese, str):
        return None
    source = japanese.strip()
    label = ""
    m = re.match(r"^【([^】]+)】", source)
    if m:
        tag = m.group(1)
        label_map = {"共鳴アビリティ": "共鸣能力", "共鳴必殺/連撃": "共鸣必杀/连击",
                     "連撃": "连击", "英雄技": "英雄技能", "超必殺": "超必杀"}
        if tag not in label_map:
            return None
        label = f"【{label_map[tag]}】"
        source = source[m.end():]
    if not source and label:
        return label
    result = _grammar(source)
    if result is None:
        return None
    return label + result


def coverage_report(path: Path | None = None) -> dict:
    """Summarize exact-match coverage over unmatched_sentences.json without writing files."""
    if path is None:
        path = (Path(__file__).resolve().parents[2] / "output" / "character_skills" /
                "reader_full_20261106" / "audit" / "unmatched_sentences.json")
    rows = json.loads(path.read_text(encoding="utf-8"))
    top = rows[:100]
    covered_top = [(text, count, translate(text)) for text, count in top if translate(text) is not None]
    covered_all = [(text, count) for text, count in rows if translate(text) is not None]
    return {
        "unique_sentences": len(rows),
        "unique_occurrences": sum(count for _, count in rows),
        "top100_covered_unique": len(covered_top),
        "top100_total_unique": len(top),
        "top100_covered_occurrences": sum(count for _, count, _ in covered_top),
        "top100_total_occurrences": sum(count for _, count in top),
        "all_covered_unique": len(covered_all),
        "all_covered_occurrences": sum(count for _, count in covered_all),
        "top100_examples": [{"japanese": s, "count": n, "chinese": zh}
                            for s, n, zh in covered_top[:12]],
    }


if __name__ == "__main__":
    print(json.dumps(coverage_report(), ensure_ascii=False, indent=2))
