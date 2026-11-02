#!/usr/bin/env python3
"""Generate versioned, database-style cycle result and remaining-work HTML pages.

The pages are generated from formal card pages and the effect ledger. Cycle-specific
batch summaries are declared below; all character names, Japanese source text and
current answer values are read back from the formal products at generation time.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import html
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "output/character_skills/pages"
LEDGER = ROOT / "output/character_skills/effect_ledger"

CYCLES = {
    "C6": {
        "title": "C6｜获珠概率与必殺镜像绑定周期",
        "campaign": "4ddfca38451eafdb30df010fc6c6eee96b9e84ad799361961fd0ab4523274df1",
        "snapshot": "4ddfca38-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "batches": [
            {
                "id": "C6-B1",
                "name": "type28 获珠概率族",
                "task": "docs/tasks/20261029-kill-mana-batch.md",
                "review": "output/character_skills/review/kill_mana_20261029_deepseek/REPORT.md",
                "verdict": "例行独立初审 PASS、零阻断",
                "stats": ["+91 答案 / 80 卡", "绝对出数 1 答案（3 槽）", "相对归位 90 行", "Y.G. +2"],
                "notes": "相对句只引用同卡同技能基础阈值，不写 +N% 增幅或实机掉珠概率；8297 标域外类型外推＋推断。",
                "examples": [(8297, "敵を倒した時"), (203, "敵を倒した時"), (224, "敵を倒した時"), (2229, "敵を倒した時"), (6325, "敵を倒した時"), (6323, "敵を倒した時"), (30306, "クリティカル攻撃か必殺技"), (30312, "クリティカル攻撃か必殺技")],
            },
            {
                "id": "C6-B2",
                "name": "G1-B1 必殺ダメージ镜像绑定",
                "task": "docs/tasks/20261029-g1-b1-mirror-batch.md",
                "review": "output/character_skills/review/g1_b1_20261029_deepseek/REPORT.md",
                "verdict": "例行独立初审 PASS、零阻断",
                "stats": ["绑定 25 行 / 21 卡（全 Y.G.）", "0 新增唯一数值", "O02 排除 23 行 / 25 值", "行仍拆分待核查"],
                "notes": "19 行 denju 链＋6 行 charainfo.pattern0 定源，禁止同文复制；链外档位值逐行排除；关联为推断。",
                "examples": [(351, "その後、前方範囲内"), (2331, "その後、前方範囲内"), (7251, "その後、前方範囲内"), (30232, "さらに前方範囲内"), (30309, "その後、前方範囲内"), (30325, "その後、直線範囲上")],
            },
            {
                "id": "C6-B3",
                "name": "G7-B1 type13 首段味方增益",
                "task": "docs/tasks/20261029-g7-b1-first-segment-batch.md",
                "review": "output/character_skills/review/g7_b1_20261029_deepseek/REPORT.md",
                "verdict": "例行独立初审 PASS、零阻断",
                "stats": ["+12 效果 / 3 卡（全 Y.G.）", "首段 3 行 × 4 槽", "0 新增唯一数值", "暴击 6 项保持未知"],
                "notes": "首段由执行列表 item(0) 顺序证据＋同卡先例推断；次段逐行排除；type116 无规则，不猜补。",
                "examples": [(4316, "【連撃】味方全体"), (30105, "【連撃】味方全体"), (30111, "【連撃】味方全体")],
            },
        ],
    },
    "C7": {
        "title": "C7｜G1 结构推广与 denju 同记录绑定周期",
        "campaign": "80ca83d9ecbb5e0c8a4ff3e96c60b44ec28b03cc6a1f8b8d9b2a9fff820b4e13",
        "snapshot": "80ca83d9-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "batches": [
            {
                "id": "C7-B1",
                "name": "G1 结构推广（名单外新准入结构化，旧名单兼容路径保留）",
                "task": "docs/tasks/20261029-c7-p1-throughput-package.md",
                "review": "output/character_skills/review/c7_p1_final_20261029_deepseek/REPORT.md",
                "verdict": "最终独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "stats": ["+2 答案 / 2 卡（全 Y.G.）", "0 新增唯一数值", "0 新公式", "0 完整描述增量"],
                "notes": "名单外新准入已结构化，旧 25 行名单及兼容路径仍保留，未宣称完全退出旧名单；7251 仅登记同值异记录，不重复出数。",
                "examples": [
                    (30247, {"row_id": "30247-special_move-special_move-skilltext-lvorder3-f0"}),
                    (30258, {"row_id": "30258-special_move-special_move-skilltext-lvorder3-f0"}),
                    (7251, {"row_id": "7251-special_move-special_move-skilltext-lvorder3-f2", "role": "对照（未新增：同值异记录披露）"}),
                ],
            },
            {
                "id": "C7-B2",
                "name": "denju 同记录绑定",
                "task": "docs/tasks/20261030-c7-p2-throughput-package.md",
                "review": "output/character_skills/review/c7_p2_final_20261030_deepseek/REPORT.md",
                "verdict": "最终独立审查 PASS、零阻断",
                "stats": ["+5 答案 / 2 行（全 Y.G.）", "0 新增唯一数值", "0 新公式", "0 新规则键", "0 完整描述增量"],
                "notes": "G7 多段零安全新增，替换为 denju 同记录绑定；7250 四槽与 30310 一槽均为同卡已披露值，type64 映射独立成立。",
                "examples": [
                    (7250, {"row_id": "7250-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (30310, {"row_id": "30310-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                ],
            },
            {
                "id": "C7-B3",
                "name": "denju 伤害镜像首段",
                "task": "docs/tasks/20261030-c7-p3-throughput-package.md",
                "review": "output/character_skills/review/c7_p3_final_20261030_deepseek/REPORT.md",
                "verdict": "最终独立审查 PASS、零阻断",
                "stats": ["+28 答案 / 28 卡（全 Y.G.）", "0 新增唯一数值", "0 新公式", "0 新规则键", "0 完整描述增量"],
                "notes": "前缀只作辅助交叉核，不作准入主证；30336 因基档槽序列不匹配排除，7251 同链两条 15 回多段记录选取不唯一另拒；其余按直接链与同记录同原值门控，归属保持推断。",
                "examples": [
                    (350, {"row_id": "350-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (351, {"row_id": "351-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (2331, {"row_id": "2331-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (30305, {"row_id": "30305-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (30308, {"row_id": "30308-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (30312, {"row_id": "30312-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (30327, {"row_id": "30327-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (30335, {"row_id": "30335-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                ],
            },
        ],
    },
    "C8": {
        "title": "C8｜denju 余量与 t27 周期回复周期",
        "campaign": "f4e1bfb0c0c87f171c68db12a1c5791df7faf15e478db131205e230f7a708b84",
        "snapshot": "f4e1bfb0-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "batches": [
            {
                "id": "C8-B1",
                "name": "denju 首句伤害镜像余量",
                "task": "docs/tasks/20261030-c8-p1-throughput-package.md",
                "review": "output/character_skills/review/c8_p1_final_20261030_deepseek/RECHECK.md",
                "verdict": "最终初审语义通过；B1 整改定向复审 PASS、零阻断",
                "stats": ["+3 答案 / 3 行（全 Y.G.）", "0 新增唯一数值", "0 新公式", "0 新规则键", "0 完整描述增量"],
                "notes": "30104 按同卡基档 t51 先例准入，不借 G7 形态分类；30336 只绑 slot0，基档 slot1 记录分歧仅披露；7251 保持同值异记录与记录不唯一披露，不升格。",
                "examples": [
                    (30104, {"row_id": "30104-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (30336, {"row_id": "30336-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (7251, {"row_id": "7251-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                ],
            },
            {
                "id": "C8-B2",
                "name": "type27 周期回复",
                "task": "docs/tasks/20261030-c8-p1-throughput-package.md",
                "review": "output/character_skills/review/c8_p1_final_20261030_deepseek/RECHECK.md",
                "verdict": "最终初审语义通过；B1 整改定向复审 PASS、零阻断",
                "stats": ["+15 答案 / 15 行（全 Y.G.）", "仅 p1 单次回复系数", "p2/p3 仅字段值", "0 完整描述增量"],
                "notes": "每条执行链恰 1 条 type27、句面机制唯一；仅以来源限定 binding 把 p1 映射到回復（词表外），不整族映射。对象只由句面「味方全体」给出；不写最终 HP、超上限保留比例或实机间隔。4 行的状态异常回复仍未知。",
                "examples": [
                    (353, {"row_id": "353-special_move-special_move-pattern0-lvorder0-f3"}),
                    (10215, {"row_id": "10215-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                    (30104, {"row_id": "30104-denju-denju-denju_denju_id____cid-lvorder0-f2"}),
                    (30228, {"row_id": "30228-special_move-special_move-pattern0-lvorder0-f0"}),
                    (30257, {"row_id": "30257-special_move-special_move-pattern1-lvorder1-f3"}),
                    (30314, {"row_id": "30314-denju-denju-denju_denju_id____cid-lvorder0-f0"}),
                ],
            },
        ],
    },
    "C9": {
        "title": "C9｜t99 敌减益与 t64 受击回复周期",
        "campaign": "7d0d53196d5a0fad38031a02bbeb6eb5b53e3ec280384c188c7c8f23cc2d1184",
        "snapshot": "7d0d5319-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "batches": [
            {
                "id": "C9-B1",
                "name": "type99 敌方减益余量",
                "task": "docs/tasks/20261030-c9-p1-throughput-package.md",
                "review": "output/character_skills/review/c9_p1_final_20261030_deepseek/REPORT.md",
                "verdict": "最终独立审查 PASS、零阻断",
                "stats": ["+16 答案 / 4 行（全 Y.G.）", "复用既有 b9 gate", "0 新公式／规则键／映射", "0 完整描述增量"],
                "notes": "只冻结4行补齐被既有原文数字答案挡住的b9余量，不放宽全局not answers守卫，37个非Y.G.同形行不连带。p9为受伤量因子1.3而非固定防御−30%；p8已核样本域仅1条，关联保持推断。",
                "examples": [
                    (30101, {"row_id": "30101-ability-ability-skillid_1_-lvorder0-f2"}),
                    (30302, {"row_id": "30302-ability-ability-skillid_1_-lvorder0-f4"}),
                    (30305, {"row_id": "30305-ability-ability-skillid_1_-lvorder0-f3"}),
                    (30333, {"row_id": "30333-ability-ability-skillid_1_-lvorder0-f5"}),
                ],
            },
            {
                "id": "C9-B2",
                "name": "type64 受击回复",
                "task": "docs/tasks/20261030-c9-p1-throughput-package.md",
                "review": "output/character_skills/review/c9_p1_final_20261030_deepseek/REPORT.md",
                "verdict": "最终独立审查 PASS、零阻断",
                "stats": ["+7 答案 / 7 行（全 Y.G.）", "仅 param1 基值系数", "0 新公式／规则键／映射", "0 完整描述增量"],
                "notes": "采用t27同级「规则确认＋链内载体唯一＋句面机制唯一」标准；同卡0披露不作阻断，跨卡30310先例不直接放行。对象/触发只由句面给出，关联推断；不写最终HP、超上限保留比例、触发次数或实机间隔。",
                "examples": [
                    (30110, {"row_id": "30110-denju-denju-denju_denju_id____cid-lvorder0-f2"}),
                    (30110, {"row_id": "30110-special_move-special_move-pattern2-lvorder2-f2"}),
                    (30203, {"row_id": "30203-special_move-special_move-pattern0-lvorder0-f1"}),
                    (30203, {"row_id": "30203-special_move-special_move-pattern2-lvorder2-f1"}),
                    (30223, {"row_id": "30223-special_move-special_move-pattern0-lvorder0-f1"}),
                    (30223, {"row_id": "30223-special_move-special_move-pattern1-lvorder1-f1"}),
                ],
            },
        ],
    },
    "C10": {
        "title": "C10｜同卡同记录镜像整理周期",
        "campaign": "af9adec8c64a552db4d2003c6e2c86df3f2ae653cd93c429845f00c3bd7d4ff2",
        "snapshot": "af9adec8-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "batches": [
            {
                "id": "C10-B1",
                "name": "t27/t64 同卡同记录镜像整理",
                "task": "docs/tasks/20261030-c10-p1-throughput-package.md",
                "review": "output/character_skills/review/c10_p1_final_20261030_deepseek/REPORT.md",
                "verdict": "最终独立审查 PASS、零阻断",
                "stats": ["+6 答案 / 6 行（全 Y.G.）", "0 新增唯一数值", "0 新公式／规则键", "0 完整描述增量"],
                "notes": "只绑定此前未答的skilltext行，逐行与同卡基档同rule_key、同record_id、同原值；同文超共鳴异记录异值排除。t27另立来源限定scope，t64走既有映射；denju非首段6行缺同卡披露，维持未解。关联推断，不写最终HP/实机间隔。",
                "examples": [
                    (353, {"row_id": "353-special_move-special_move-skilltext-lvorder3-f3"}),
                    (30104, {"row_id": "30104-special_move-special_move-skilltext-lvorder2-f2"}),
                    (30257, {"row_id": "30257-special_move-special_move-skilltext-lvorder3-f3"}),
                    (30110, {"row_id": "30110-special_move-special_move-skilltext-lvorder3-f2"}),
                    (30203, {"row_id": "30203-special_move-special_move-skilltext-lvorder3-f1"}),
                    (30223, {"row_id": "30223-special_move-special_move-skilltext-lvorder2-f1"}),
                ],
            },
        ],
    },
    "C11": {
        "title": "C11｜t114、1059 与 1017 数值归位周期",
        "campaign": "14ff8b62ad995ab93d8bca3a69fcdfc926e7e2b689042b35c27d8e8409c81852",
        "snapshot": "14ff8b62-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "history_run_tag": "20261031T015918",
        "metrics_path": "output/character_skills/c12_delivery_20261031/pre_rebuild/ledger_metrics.json",
        "before_cards": "output/character_skills/c11_delivery_20261031/pre_rebuild/cards",
        "batches": [
            {
                "id": "C11-P1",
                "name": "t114 冲刺重复攻击与同记录镜像",
                "binding": "c11_p1_t114",
                "task": "docs/tasks/20261031-c11-p1-t114-direct.md",
                "review": "output/character_skills/review/c11_p1_t114_final_20261031_deepseek/REPORT.md",
                "verdict": "例行独立复审 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "四条直接行与两条同卡 pattern0 同记录镜像；原文25回保留，不用p4推次数，不写总伤害或最终HP。首次组合仅1.2/0.6/0.8，raw=1复用既有组合。",
            },
            {
                "id": "C11-P2",
                "name": "1059 UnionCount 队伍五属性增益",
                "binding": "c11_p2_union_count",
                "task": "docs/tasks/20261031-c11-p2-union-count.md",
                "review": "output/character_skills/review/c11_p2_union_count_20261031_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "五条键精确账本映射只改变消费依据，非解锁必要条件；p3为受伤量倍率，人数比例与五人上限未知，第二段不归属。",
            },
            {
                "id": "C11-P3",
                "name": "1017 サブパーティ条件攻防速",
                "binding": "c11_p3_strength_job2",
                "task": "docs/tasks/20261031-c11-p3-strength-job2.md",
                "review": "output/character_skills/review/c11_p3_strength_job2_20261031_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "只消费第二段三属性；首段和同段暴击子句不并入。S3保留，放置条件未编码，p2仅两个已核ID的类型外推。",
            },
        ],
    },
    "C12": {
        "title": "C12｜共鳴アビリティ与同文镜像归位周期",
        "campaign": "1be4165aecfcc3aa26f7597ab1e4cd20335fcaf2794e697c622786bdc6cedf73",
        "snapshot": "1be4165a-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c12_delivery_20261031/pre_rebuild/cards",
        "batches": [
            {
                "id": "C12-P1",
                "name": "3000 共鳴アビリティ攻击与暴伤段",
                "binding": "c12_p1_sympathy_attack",
                "task": "docs/tasks/20261031-c12-p1-sympathy-attack.md",
                "review": "output/character_skills/review/c12_p1_sympathy_attack_20261031_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS、零阻断",
                "notes": "p1普通攻击加算、p2技能攻击加算、p8暴伤系数加算；p6时长不重复。108答案与66效果净增分开，42个S4，unresolved 126→60。",
            },
            {
                "id": "C12-P2",
                "name": "3005→sub1 攻击与时长段",
                "binding": "c12_p2_sympathy_3005_sub1",
                "task": "docs/tasks/20261031-c12-p2-sympathy-3005-sub1.md",
                "review": "output/character_skills/review/c12_p2_sympathy_3005_sub1_20261031_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS、零阻断",
                "notes": "M为3005、子记录为3000，M字段不消费；仅数据侧结构对应，引擎装载未核实。102答案、68效果净增、34个S4。",
            },
            {
                "id": "C12-P3",
                "name": "skilltext 同卡同标签同文多槽镜像",
                "binding": "c12_p3_skilltext_mirror",
                "task": "docs/tasks/20261031-c12-p3-skilltext-mirror.md",
                "review": "output/character_skills/review/c12_p3_skilltext_mirror_20261031_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "同卡同标签唯一同文行与super异值定源；2003可挂非13子记录，不虚构13→2003边。S7与Boss模式pattern选取未知保留。",
            },
        ],
    },
    "C13": {
        "title": "C13｜supporterskill、回复与时长归位周期",
        "campaign": "f0b36c7f0c40284bf8c25a74e3014d34884c2deabaa436815f4de5e62abcb357",
        "snapshot": "f0b36c7f-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c13_delivery_20261031/pre_rebuild/cards",
        "delivery_review": "output/character_skills/review/c13_delivery_final_20261031_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261031-c13-delivery-package.md",
        "batches": [
            {
                "id": "C13-P1",
                "name": "supporterskill→abiN type8 基础增益",
                "binding": "c13_p1_supporterskill_type8",
                "task": "docs/tasks/20261031-c13-p1-supporterskill-type8.md",
                "review": "output/character_skills/review/c13_p1_supporterskill_type8_20261031_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "61行89答案；句首戦闘時属性链与ABI原文、唯一非中性槽逐项对应；CACHE缺ID才APK回退。规则体确认、装载关联推断；30302及条件／对象句保持未解。",
            },
            {
                "id": "C13-P2",
                "name": "t27 同卡同文回复镜像",
                "binding": "c13_p2_t27_mirror",
                "task": "docs/tasks/20261031-c13-p2-t27-skilltext-mirror.md",
                "review": "output/character_skills/review/c13_p2_t27_mirror_20261031_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS、零阻断",
                "notes": "3行3答案；只补p1单次回复系数，p2/p3仅披露；超共鳴异值不并入，S7与Boss pattern选取保持未知。",
            },
            {
                "id": "C13-P3",
                "name": "2012 同卡同记录攻速时长镜像",
                "binding": "c13_p3_2012_duration",
                "task": "docs/tasks/20261031-c13-p3-2012-duration-mirror.md",
                "review": "output/character_skills/review/c13_p3_2012_duration_20261031_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "3行3答案、完整+3；只补param0=30游戏秒，param6不重复；pattern/slot分别保留，时长消费走既有quantity_kind回退。",
            },
        ],
    },
}

CSS = """
:root{--bg:#f4f6f9;--panel:#fff;--ink:#202938;--muted:#64748b;--line:#dbe3ec;--blue:#1d4ed8;--green:#047857;--amber:#b45309;--violet:#6d28d9}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI","Noto Sans CJK SC","Microsoft YaHei",sans-serif;line-height:1.6}
header{background:linear-gradient(120deg,#172554,#1e40af);color:white;padding:28px 34px}header h1{margin:0 0 8px;font-size:26px}header p{margin:4px 0;color:#dbeafe}main{max-width:1500px;margin:24px auto;padding:0 18px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;margin:18px 0;box-shadow:0 2px 8px #0f172a0a}
h2{font-size:21px;margin:0 0 12px}h3{font-size:17px;margin:18px 0 8px}.muted{color:var(--muted)}.small{font-size:13px}.stats{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}.stat{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:8px 12px;font-weight:600;color:#1e40af}.badge{display:inline-block;border-radius:5px;padding:1px 7px;font-size:12px;margin-right:5px;background:#e2e8f0;color:#334155}.badge.pass{background:#d1fae5;color:#065f46}.badge.unknown{background:#fef3c7;color:#92400e}.badge.infer{background:#ede9fe;color:#5b21b6}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}th{background:#eaf0f7;font-weight:700}tr:nth-child(even) td{background:#f8fafc}.jp{font-family:"Noto Sans CJK JP","Yu Gothic","Hiragino Kaku Gothic ProN",sans-serif}.name{font-weight:650;white-space:nowrap}.num{font-variant-numeric:tabular-nums;white-space:nowrap}.links a{color:var(--blue);margin-right:14px}details{cursor:pointer}details summary{color:var(--blue)}.value{max-width:760px;white-space:pre-wrap}.warning{background:#fff7ed;border-left:4px solid var(--amber);padding:10px 14px}.footer{color:var(--muted);font-size:12px;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}.metric{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:10px}.metric b{display:block;font-size:20px;color:#1e40af}
.table-wrap{overflow-x:auto}.value{overflow-wrap:anywhere}code{overflow-wrap:anywhere;word-break:break-word}
@media(max-width:800px){main{padding:0 8px}header{padding:20px}table{font-size:12px}th,td{padding:5px}.name{white-space:normal}.value{max-width:100%}}
"""


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def history_card_path(cid: int, run_tag: str) -> Path:
    matches = sorted(PAGES.glob(f"_batch/*/runs/{run_tag}*/transactions/{cid}/backup/card.json"))
    if len(matches) != 1:
        raise ValueError(f"历史前像数量错误：cid={cid}, tag={run_tag}, matches={len(matches)}")
    return matches[0]


def card_data(cid: int, cfg: dict | None = None):
    if cfg and cfg.get("history_run_tag"):
        return load_json(history_card_path(cid, cfg["history_run_tag"]))
    return load_json(PAGES / str(cid) / "card.json")


def before_card_data(cid: int, cfg: dict):
    return load_json(ROOT / cfg["before_cards"] / f"{cid}.json")


def character_name(data):
    fields = {f["key"]: f.get("raw_value") for f in data["basic"]["fields"]}
    name = fields.get("name", "?")
    title = fields.get("title")
    return f"{name}{title}" if title and title.startswith("《") else (f"{name}《{title}》" if title else name)


def find_examples(cid: int, spec, cfg: dict | None = None):
    """Return examples selected by explicit row_id first, then Japanese substring."""
    if isinstance(spec, dict):
        row_id = spec.get("row_id")
        role = spec.get("role", "新增（本批）")
        needle = None
    else:
        row_id, role, needle = None, "新增（本批）", spec
    data = card_data(cid, cfg)
    name = character_name(data)
    out = []
    for group in data.get("groups", []):
        for skill in group.get("skills", []):
            for row in skill.get("rows", []):
                if row_id is not None:
                    if row.get("row_id") != row_id:
                        continue
                elif needle not in row.get("japanese", ""):
                    continue
                answers = [ans.get("value", "") for ans in row.get("answers") or [] if ans.get("value", "")]
                out.append({"cid": cid, "name": name, "row_id": row.get("row_id", ""),
                            "japanese": row.get("japanese", ""), "answers": answers,
                            "role": role, "marker": row.get("inference_g1_structure")})
    if not out:
        out.append({"cid": cid, "name": name, "row_id": row_id or "", "japanese": "",
                    "answers": [], "role": "未找到示例行", "marker": None})
    return out


def metrics_summary(cfg: dict | None = None):
    path = ROOT / cfg["metrics_path"] if cfg and cfg.get("metrics_path") else LEDGER / "metrics.json"
    m = load_json(path)
    d, e, b = m["descriptions"], m["effects"], m["backlog"]
    return {
        "snapshot": m["snapshot"]["snapshot_id"],
        "has_answer": e["by_status"]["has_answer"],
        "unresolved": e["by_status"]["unresolved"],
        "justified_na": e["by_status"]["justified_na"],
        "identified": e["identified_total"],
        "complete": d["complete"], "partial": d["partial"], "unparsed": d["unparsed"],
        "split": d["split_check"], "row_class": d["by_row_class"],
        "grades": d["row_evidence_grades"], "grades_yg": d["row_evidence_grades_yg"],
        "backlog": b["total"], "backlog_yg": b["yg_total"],
        "p0": b["by_priority"].get("P0", 0),
    }


def row_map(data: dict):
    return {row["row_id"]: row for group in data.get("groups", [])
            for skill in group.get("skills", []) for row in skill.get("rows", [])}


def status_counts(analysis: dict):
    counts = collections.Counter(effect.get("status") for effect in analysis.get("effects") or [])
    return {k: counts.get(k, 0) for k in ("has_answer", "unresolved", "justified_na")}


def row_status(analysis: dict):
    if analysis.get("split_flags"):
        return "拆分待核查"
    counts = status_counts(analysis)
    if counts["unresolved"] and counts["has_answer"]:
        return "部分"
    if counts["unresolved"]:
        return "未解析"
    if counts["has_answer"]:
        return "完整"
    return "未解析"


def new_answer_rows(cfg: dict, batch: dict):
    """Build all new answers from real before/after card JSON and compute ledger deltas."""
    sys.path.insert(0, str(ROOT / "scripts/character_skills"))
    import effect_ledger as EL
    rows = []
    removed = []
    stats = {"id": batch["id"], "rows": 0, "cards": set(), "answers": 0, "effect_net": 0,
             "before_unresolved": 0, "after_unresolved": 0,
             "complete_net": 0, "s4_after": 0}
    for cid in sorted(int(path.stem) for path in (ROOT / cfg["before_cards"]).glob("*.json")):
        before_data = before_card_data(cid, cfg)
        after_data = card_data(cid, cfg)
        before_rows, after_rows = row_map(before_data), row_map(after_data)
        for row_id, after_row in after_rows.items():
            before_row = before_rows.get(row_id)
            before_answers = (before_row or {}).get("answers") or []
            after_answers = after_row.get("answers") or []
            if after_answers[:len(before_answers)] != before_answers:
                raise ValueError(f"旧答案被改写：{row_id}")
            appended = after_answers[len(before_answers):]
            if not appended:
                continue
            binding_text = json.dumps([after_row.get(f"inference_{batch['binding']}"),
                                       [a.get("binding") for a in appended], appended], ensure_ascii=False)
            if batch["binding"] not in binding_text:
                continue
            before_analysis = EL.analyze_row(before_row) if before_row else {"effect_status_counts": {}}
            after_analysis = EL.analyze_row(after_row)
            before_counts, after_counts = status_counts(before_analysis), status_counts(after_analysis)
            stats["rows"] += 1
            stats["cards"].add(cid)
            stats["answers"] += len(appended)
            stats["effect_net"] += after_counts["has_answer"] - before_counts["has_answer"]
            stats["before_unresolved"] += before_counts["unresolved"]
            stats["after_unresolved"] += after_counts["unresolved"]
            stats["complete_net"] += int(row_status(after_analysis) == "完整") - int(row_status(before_analysis) == "完整")
            stats["s4_after"] += sum(1 for flag in after_analysis.get("split_flags") or []
                                     if str(flag.get("code", "")).startswith("S4"))
            after_status = {effect.get("effect_id"): effect.get("status")
                            for effect in after_analysis.get("effects") or []}
            for effect in before_analysis.get("effects") or []:
                if effect.get("status") == "unresolved" and after_status.get(effect.get("effect_id")) == "has_answer":
                    removed.append({"kind": "effect", "effect_id": effect.get("effect_id"),
                                    "effect_type": effect.get("effect_type"), "row_id": row_id,
                                    "cid": cid, "yg": "Y.G." in character_name(before_data),
                                    "blocker": "周期末仍未解的机制或归属；需逐行证据核查"})
            rows.append({"cid": cid, "name": character_name(after_data), "row_id": row_id,
                         "japanese": after_row.get("japanese", ""),
                         "reference_field": after_row.get("reference_field"),
                         "stage": after_row.get("stage"), "level": after_row.get("level"),
                         "fragment_index": after_row.get("fragment_index"),
                         "before": before_row, "after": after_row, "answers": appended})
    if stats["rows"] == 0:
        raise ValueError(f"批次没有新增答案：{batch['id']}")
    stats["cards"] = len(stats["cards"])
    return {"stats": stats, "rows": rows, "removed_effects": removed}



def relative_href(output_dir: Path, target: str) -> str:
    """Return a relative link from the report directory to a project-root target."""
    return os.path.relpath(ROOT / target, output_dir).replace(os.sep, "/")


def answer_block(answer: dict, row: dict, output_dir: Path, cid: int):
    source = answer.get("source") or {}
    pointer = source.get("json_pointer") or source.get("source_key") or "未单列"
    conditions = answer.get("conditions") or row.get("conditions") or row.get("condition") or "未单列"
    if not isinstance(conditions, str):
        conditions = json.dumps(conditions, ensure_ascii=False, separators=(",", ":"))
    condition_label = answer.get("condition_label") or row.get("condition_label") or "未单列"
    obj = answer.get("target") or answer.get("object") or row.get("object") or row.get("target") or "未单列"
    evidence = f"numeric={answer.get('numeric_evidence')}；association={answer.get('association_evidence')}；scope={answer.get('evidence_scope')}"
    return (f'<details><summary>{html.escape(str(answer.get("quantity_kind") or answer.get("unit") or "答案"))}：'
            f'{html.escape(str(answer.get("value") or "未列值"))}</summary><div class="value small">'
            f'单位／量纲：{html.escape(str(answer.get("unit") or "未单列"))}<br>'
            f'对象：{html.escape(str(obj))}<br>'
            f'逐行 condition_label：{html.escape(str(condition_label))}<br>'
            f'规则适用域 conditions：{html.escape(conditions)}<br>'
            f'阶段：{html.escape(str(row.get("stage") or row.get("reference_field") or "未单列"))}'
            f'　fragment={html.escape(str(row.get("fragment_index")))}<br>'
            f'规则键：{html.escape(str(answer.get("rule_key") or "无"))}<br>'
            f'原值：{html.escape(str(answer.get("raw_value")))}；记录：{html.escape(str(answer.get("record_id")))}'
            f'（{html.escape(str(answer.get("layer") or "未单列"))}）<br>'
            f'来源：{html.escape(str(pointer))}<br>证据：{html.escape(evidence)}</div></details>')


def render_new_answers(cfg: dict, batch: dict, output_dir: Path):
    computed = new_answer_rows(cfg, batch)
    rows = []
    for item in computed["rows"]:
        cid = item["cid"]
        answers = "<br>".join(answer_block(ans, item, output_dir, cid) for ans in item["answers"])
        page_path = history_card_path(cid, cfg["history_run_tag"]) if cfg.get("history_run_tag") else PAGES / str(cid) / "card.json"
        href = relative_href(output_dir, str(page_path.relative_to(ROOT)))
        rows.append(
            f'<tr data-cid="{cid}"><td class="name"><a href="{href}">{html.escape(item["name"])}</a><br>'
            f'<span class="muted small">cid{cid}</span></td><td class="jp">{html.escape(item["japanese"])}</td>'
            f'<td class="small"><code>{html.escape(item["row_id"])}</code><br>'
            f'<span class="muted">{html.escape(str(item["stage"] or item["reference_field"] or ""))}</span></td>'
            f'<td>{answers}</td></tr>')
    stats = computed["stats"]
    stat_text = [f"{stats['rows']} 行 / {stats['cards']} 卡",
                 f"新增答案：Y.G. {stats['answers']}／非 Y.G. 0",
                 f"效果净增：Y.G. {stats['effect_net']}／非 Y.G. 0",
                 f"完整增量：Y.G. {stats['complete_net']:+d}／非 Y.G. +0",
                 f"S4 {stats['s4_after']}",
                 f"unresolved {stats['before_unresolved']}→{stats['after_unresolved']}"]
    return {"html": "".join(rows), "stat_text": stat_text, "computed": computed}


def render_index(cycle_id: str, cfg: dict, metrics: dict, output_dir: Path):
    batches = []
    for batch in cfg["batches"]:
        rows = []
        if batch.get("binding"):
            rendered = render_new_answers(cfg, batch, output_dir)
            rows.append(rendered["html"])
            batch["computed_stats"] = rendered["stat_text"]
        for cid, spec in batch.get("examples", []):
            found = find_examples(cid, spec, cfg)
            for item in found:
                values = "<br>".join(html.escape(v) for v in item["answers"]) or '<span class="muted">无答案／保持未知</span>'
                values = f'<details><summary>查看当前答案（{len(item["answers"])} 条）</summary><div class="value">{values}</div></details>' if item["answers"] else values
                role = item["role"]
                role_html = html.escape(role)
                if role == "未找到示例行":
                    rows.append(f'<tr><td class="name">{html.escape(str(cid))}</td><td class="jp muted">{role_html}（{html.escape(spec if isinstance(spec, str) else spec.get("row_id", ""))}</td><td>—</td><td>—</td></tr>')
                    continue
                rows.append(
                    f'<tr data-cid="{cid}"><td class="name">{html.escape(item["name"])}<br><span class="muted small">cid{cid}</span></td>'
                    f'<td class="jp">{html.escape(item["japanese"])}</td><td class="small"><code>{html.escape(item["row_id"])}</code><br><span class="muted">{role_html}</span></td><td>{values}</td></tr>'
                )
        stats = "".join(f'<span class="stat">{html.escape(s)}</span>' for s in batch.get("computed_stats", batch.get("stats", [])))
        task_href = relative_href(output_dir, batch["task"])
        review_href = relative_href(output_dir, batch["review"])
        batches.append(f"""
<section class="panel"><h2>{html.escape(batch['id'])}｜{html.escape(batch['name'])}</h2>
<p><span class="badge pass">{html.escape(batch['verdict'])}</span></p>
<div class="stats">{stats}</div><p>{html.escape(batch['notes'])}</p>
<p class="links small"><a href="{task_href}">任务书</a><a href="{review_href}">独立审查报告</a></p>
<div class="table-wrap"><table><thead><tr><th style="width:22%">参考角色</th><th style="width:31%">日文原文</th><th style="width:22%">row_id／示例性质</th><th>当前答案／状态</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></section>""")
    cards = "".join(f'<div class="metric"><b>{v}</b>{k}</div>' for k, v in [
        ("有答案效果", f"{metrics['has_answer']['all']:,}（Y.G. {metrics['has_answer']['yg']:,}）"),
        ("未解效果", f"{metrics['unresolved']['all']:,}（Y.G. {metrics['unresolved']['yg']:,}）"),
        ("完整描述", f"{metrics['complete']['all']:,}（Y.G. {metrics['complete']['yg']:,}）"),
        ("剩余 backlog", f"{metrics['backlog']:,}（Y.G. {metrics['backlog_yg']:,}）"),
    ])
    third_party = ""
    if cycle_id in ("C11", "C12"):
        report_href = relative_href(output_dir, "output/character_skills/review/direction_c11_c12_20261031_thirdparty/REPORT.md")
        rectification_href = relative_href(output_dir, "output/character_skills/review/direction_c11_c12_20261031_thirdparty/RECTIFICATION.md")
        task_href = relative_href(output_dir, "docs/tasks/20261031-c11-c12-direction-review-rectification.md")
        third_party = f'''<section class="panel"><h2>独立审查与整改状态</h2>
<p><span class="badge unknown">第三方 REQUEST_CHANGES（R01／R02）</span> <span class="badge infer">整改完成，待原第三方定向复查</span></p>
<p>本页只补齐展示与交接，不把原裁决改写为通过。784条数值及限定关联交付已由第三方独立核实；未解决的机制、条件和证据边界继续保留。</p>
<p class="links small"><a href="{report_href}">第三方原裁决</a><a href="{rectification_href}">第三方整改要求</a><a href="{task_href}">本轮整改任务卡</a></p></section>'''
    elif cycle_id == "C13":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0</span></p>
<p>63卡67行95答案／95效果净增、完整+3、S4 0；全库生成仅一次，固定检查与隔离复跑已通过。推断、类型外推、装载／放置条件与Boss档位选择继续保留；第三方方向审查待用户安排，C14不启动。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{task_href}">C13交付任务卡</a></p></section>'''
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(cfg['title'])}</title><style>{CSS}</style></head>
<body><header><h1>{html.escape(cfg['title'])}</h1><p>数据库样式｜本周期新增解析成果（由正式页面与账本生成）</p>
<p>campaign <code>{cfg['campaign']}</code></p><p>snapshot <code>{cfg['snapshot']}</code>　rules {html.escape(cfg['rules'])}</p></header>
<main><section class="panel"><h2>周期末总览</h2><div class="grid">{cards}</div>
<p class="small">计数口径：有答案／未解为效果级；完整／部分／未解析／拆分为描述行级；Y.G. 为 109 张优先卡子集，均非全游戏分母。绝对出数、绑定修正、披露-only、split 状态整理分列，不合并成一个收益数。</p>
<p class="links"><a href="remaining.html">查看预计剩余工程量 →</a></p></section>
{''.join(batches)}
{third_party}
<section class="panel"><h2>边界与外部对照</h2><p>外部数据库／截图仅作对照，不覆盖游戏原值；CACHE 与 APK 分源，不跨层取值。静态规则、类型外推、结构关联和实机验证分档记录；镜像绑定不升级为记录级执行确认，未解机制继续保持未知。</p></section>
<p class="footer">本页由 <code>scripts/character_skills/cycle_report.py</code 生成；当前答案可展开核对。生成后如正式页面更新，需重新生成本页，不自动视为最新。</p>
</main></body></html>"""


def remaining_groups(cfg: dict | None = None):
    backlog = load_json(LEDGER / "backlog.json")
    if cfg and cfg.get("history_run_tag"):
        removed = []
        for batch in CYCLES["C12"]["batches"]:
            removed.extend(new_answer_rows(CYCLES["C12"], batch)["removed_effects"])
        backlog = backlog + removed
    effects = [x for x in backlog if x.get("kind") == "effect"]
    split_count = sum(1 for x in backlog if x.get("kind") == "description_split_check")
    groups = collections.defaultdict(list)
    for item in effects:
        groups[item.get("effect_type")].append(item)
    rows = []
    for effect_type, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        sample = next((x for x in items if x.get("yg")), items[0])
        cid = sample["cid"]
        try:
            data = card_data(cid, cfg)
            name = character_name(data)
            row = None
            for group in data.get("groups", []):
                for skill in group.get("skills", []):
                    row = next((r for r in skill.get("rows", []) if r.get("row_id") == sample["row_id"]), None)
                    if row:
                        break
                if row:
                    break
            sentence = row.get("japanese", "") if row else sample.get("snippet", "")
        except Exception:
            name, sentence = str(cid), sample.get("snippet", "")
        blockers = collections.Counter((x.get("blocker") or "").split("；")[0] for x in items)
        reason = blockers.most_common(1)[0][0]
        rows.append({"type": effect_type, "all": len(items), "yg": sum(bool(x.get("yg")) for x in items),
                     "name": name, "cid": cid, "sentence": sentence, "reason": reason})
    return rows, split_count


def render_remaining(cycle_id: str, cfg: dict, metrics: dict):
    groups, split_count = remaining_groups(cfg)
    rows = []
    for g in groups:
        rows.append(
            f'<tr><td>{html.escape(str(g["type"]))}</td><td class="num">{g["all"]:,} / {g["yg"]:,}</td>'
            f'<td class="jp">{html.escape(g["sentence"])}</td><td class="name">{html.escape(g["name"])}<br><span class="muted small">cid{g["cid"]}</span></td>'
            f'<td class="small">{html.escape(g["reason"])}</td></tr>'
        )
    cards = "".join(f'<div class="metric"><b>{v}</b>{k}</div>' for k, v in [
        ("完整描述", f"{metrics['complete']['all']:,}（Y.G. {metrics['complete']['yg']:,}）"),
        ("部分描述", f"{metrics['partial']['all']:,}（Y.G. {metrics['partial']['yg']:,}）"),
        ("未解析描述", f"{metrics['unparsed']['all']:,}（Y.G. {metrics['unparsed']['yg']:,}）"),
        ("未解效果", f"{metrics['unresolved']['all']:,}（Y.G. {metrics['unresolved']['yg']:,}）"),
        ("拆分待核查行", f"{split_count:,}（Y.G. {metrics['split']['yg']:,}）"),
        ("backlog 合计", f"{metrics['backlog']:,}（Y.G. {metrics['backlog_yg']:,}）"),
        ("P0 断点", str(metrics["p0"])),
    ])
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(cycle_id)}｜预计剩余工程量</title><style>{CSS}</style></head>
<body><header><h1>{html.escape(cycle_id)}｜预计剩余工程量</h1><p>以周期末正式账本为唯一计数来源｜{html.escape(metrics['snapshot'])}</p></header>
<main><section class="panel"><h2>剩余规模（当前快照）</h2><div class="grid">{cards}</div>
<p class="warning"><b>这不是全游戏完成度，也不是可信的固定批次数／工期承诺。</b> 剩余工作同时包含词表外机制（需要新的原生或规则证据）、句面到字段的归属证明、镜像/绑定修正和人工语义核查；各类成本差异很大，不能用单一平均速率换算。可预排的只是下一周期的有界候选，不能把全量 backlog 当作已具备出数条件。</p></section>
<section class="panel"><h2>按词条分类的未解效果</h2><p class="small">共 {sum(g['all'] for g in groups):,} 项；示例均为该词条的真实未解行（Y.G. 优先）。</p>
<div class="table-wrap"><table><thead><tr><th>词条（词面）</th><th>未解项（全部/Y.G.）</th><th style="width:40%">日文原文示例</th><th>参考角色</th><th>主要未解原因</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></section>
<section class="panel"><h2>后续估算口径与边界</h2><ul>
<li><b>词表外机制</b>：没有已确认规则映射到来源字段；需要新的原生证据、受控检查或类型级规则建立，不能按普通绑定批估算。</li>
<li><b>归属未证</b>：句面效果存在，但到具体记录/槽位的关联未经证明；可以逐族预检，有证单项先交付，其余保持未知。</li>
<li><b>拆分待核查</b>：{split_count:,} 行（Y.G. {metrics['split']['yg']:,}）含零识别、未覆盖子句、数字语义或答案对应问题，需逐行语义核查，不计为可直接新增数值的行数。</li>
<li><b>历史待办（不构成下一包准入或授权）</b>：G7-B2 登记口径、G7-B3 定性轨道、G1/G7 其余段、30239 回复间隔子项（须用户明示到行）与 20234 跨层审计；只供后续有界选题时重核，不能据此启动 20234 或扩大 30239 豁免，也不是全量 backlog 的消化承诺。</li></ul></section>
<p class="footer">生成器：<code>scripts/character_skills/cycle_report.py</code>。与 <a href="index.html">本周期成果页</a> 同版本。</p>
</main></body></html>"""


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def all_answer_pairs(run_tag: str | None):
    pairs = set()
    if run_tag:
        paths = PAGES.glob(f"_batch/*/runs/{run_tag}*/transactions/*/backup/card.json")
    else:
        paths = (PAGES / folder.name / "card.json" for folder in PAGES.iterdir()
                 if folder.is_dir() and folder.name.isdigit())
    for path in paths:
        data = load_json(path)
        for row in row_map(data).values():
            for answer in row.get("answers") or []:
                if answer.get("rule_key") and answer.get("raw_value") is not None:
                    pairs.add((answer["rule_key"], json.dumps(answer["raw_value"], ensure_ascii=False, sort_keys=True)))
    return pairs


def new_answer_pairs(cfg: dict):
    pairs = set()
    for batch in cfg["batches"]:
        for item in new_answer_rows(cfg, batch)["rows"]:
            for answer in item["answers"]:
                if answer.get("rule_key") and answer.get("raw_value") is not None:
                    pairs.add((answer["rule_key"], json.dumps(answer["raw_value"], ensure_ascii=False, sort_keys=True)))
    return pairs


def generation_record(cycle_id: str, cfg: dict, metrics: dict, output_dir: Path,
                      batch_results: list, remaining: list, unique_pairs: set, before_pairs: set):
    outputs = {}
    for name in ("index.html", "remaining.html", "report_data.json", "README.md", "verification.json", "browser_verification.json"):
        path = output_dir / name
        if path.is_file():
            outputs[name] = {"bytes": path.stat().st_size, "sha256": file_sha(path)}
    metrics_path = ROOT / cfg["metrics_path"] if cfg.get("metrics_path") else LEDGER / "metrics.json"
    return {
        "cycle": cycle_id,
        "campaign": cfg["campaign"],
        "snapshot": cfg["snapshot"],
        "rules": cfg["rules"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": {"path": "scripts/character_skills/cycle_report.py", "sha256": file_sha(Path(__file__).resolve())},
        "command": f"./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/cycle_report.py --cycle {cycle_id} --output {output_dir.relative_to(ROOT)}",
        "inputs": {
            "after_pages": (f"C12 run transactions backup (tag={cfg['history_run_tag']})"
                            if cfg.get("history_run_tag") else "output/character_skills/pages/<cid>/card.json"),
            "before_cards": cfg["before_cards"],
            "metrics": {"path": str(metrics_path.relative_to(ROOT)), "sha256": file_sha(metrics_path)},
            "current_backlog_for_remaining": "output/character_skills/effect_ledger/backlog.json",
            "third_party_report_reference_only": "output/character_skills/review/direction_c11_c12_20261031_thirdparty/REPORT.md",
        },
        "outputs": outputs,
        "batch_results": batch_results,
        "remaining_by_type": remaining,
        "new_rule_value_pairs": sorted(unique_pairs),
        "before_rule_value_pair_count": len(before_pairs),
        "status": "PASS",
        "third_party_verdict": ("PENDING（待用户安排第三方方向审查）" if cycle_id == "C13"
                                else "REQUEST_CHANGES（R01/R02；原裁决未改）"),
        "rectification_status": ("正式交付与例行独立审查完成，待用户安排第三方方向审查" if cycle_id == "C13"
                                 else "整改完成，待原第三方定向复查"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle", required=True, choices=sorted(CYCLES))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.output.is_absolute():
        args.output = (ROOT / args.output).resolve()
    cfg = CYCLES[args.cycle]
    metrics = metrics_summary(cfg)
    if metrics["snapshot"] != cfg["snapshot"]:
        raise SystemExit(f"账本 snapshot {metrics['snapshot']} 与周期声明 {cfg['snapshot']} 不一致；请先更新生成器配置")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "index.html").write_text(render_index(args.cycle, cfg, metrics, args.output), encoding="utf-8")
    (args.output / "remaining.html").write_text(render_remaining(args.cycle, cfg, metrics), encoding="utf-8")
    groups, split_count = remaining_groups(cfg)
    batch_results = [new_answer_rows(cfg, batch) for batch in cfg["batches"] if batch.get("binding")]
    before_tag = "20261030T203110" if args.cycle == "C11" else "20261031T015918" if args.cycle in ("C12", "C13") else None
    before_pairs = all_answer_pairs(before_tag) if args.cycle in ("C11", "C12", "C13") else set()
    unique_pairs = new_answer_pairs(cfg) - before_pairs if args.cycle in ("C11", "C12", "C13") else set()
    data = {"cycle": args.cycle, "campaign": cfg["campaign"], "snapshot": cfg["snapshot"], "rules": cfg["rules"],
            "metrics": metrics, "batches": cfg["batches"], "batch_results": batch_results,
            "remaining_by_type": groups, "split_check_rows": split_count,
            "new_rule_value_pairs": sorted(unique_pairs),
            "before_rule_value_pair_count": len(before_pairs)}
    (args.output / "report_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    checks = {
        "snapshot_matches": metrics["snapshot"] == cfg["snapshot"],
        "new_answer_rows_generated": all(result["stats"]["rows"] > 0 for result in batch_results),
        "remaining_unresolved_matches_metrics": sum(g["all"] for g in groups) == metrics["unresolved"]["all"],
        "remaining_yg_matches_metrics": sum(g["yg"] for g in groups) == metrics["unresolved"]["yg"],
        "backlog_matches_metrics": sum(g["all"] for g in groups) + split_count == metrics["backlog"],
        "unique_pairs_expected": len(unique_pairs) == (8 if args.cycle == "C11" else 2 if args.cycle == "C13" else 0) if args.cycle in ("C11", "C12", "C13") else True,
    }
    verification = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
                    "metrics": metrics, "batch_results": batch_results,
                    "new_rule_value_pairs": sorted(unique_pairs),
                    "before_rule_value_pair_count": len(before_pairs)}
    (args.output / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
    report_url = relative_href(args.output, "output/character_skills/review/direction_c11_c12_20261031_thirdparty/REPORT.md")
    rectification_url = relative_href(args.output, "output/character_skills/review/direction_c11_c12_20261031_thirdparty/RECTIFICATION.md")
    task_url = relative_href(args.output, "docs/tasks/20261031-c11-c12-direction-review-rectification.md")
    if args.cycle == "C13":
        status_text = "正式交付与例行独立审查完成，待用户安排第三方方向审查"
        verdict_text = "正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断 0"
        review_links = (f"- [C13交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})")
        generation_note = "C13 使用当前正式页面与账本及首建前像。未再次运行正式全库生成；正式生成与固定检查已在交付包内完成。"
        limits_note = "关联／装载／放置条件与Boss档位选择保持推断或未知；P1/P2拆分与S3/S7保留，P2 p2/p3仅披露，P3 param6不重复。历史待办不构成下一批授权。"
    else:
        status_text = "整改完成，待原第三方定向复查"
        verdict_text = "第三方原裁决 REQUEST_CHANGES（R01/R02）未改"
        review_links = (f"- [第三方原裁决]({report_url})\n"
                        f"- [第三方整改要求]({rectification_url})\n"
                        f"- [本轮整改任务卡]({task_url})")
        generation_note = "C11 使用 C12 run 中保存的 C11 前像与 C11 账本；C12 使用当前正式页面与账本。未运行正式全库生成或第二次全库生成，未修改正式 pages、rules 或正式账本。第三方统计仅作交叉核对，不是生产唯一输入。"
        limits_note = "数值关联保持推断；S3/S7、hint、放置条件、Boss 模式 pattern 选取、M→sub1 引擎装载、1059 人数比例与五人上限保持未知。历史待办不构成下一批授权，backlog 不是互斥的角色完成率。"
    readme = f"""# {args.cycle} 周期成果与剩余工程量

- 状态：**{status_text}**；{verdict_text}。
- campaign：`{cfg['campaign']}`
- snapshot：`{cfg['snapshot']}`
- rules：{cfg['rules']}

## 文件

- `index.html`：全部新增答案、日文原文、值、单位、对象、条件、阶段、证据档与来源。
- `remaining.html`：按本周期末账本的未解效果、拆分待核查、示例与估算边界。
- `report_data.json`：版本、完整批次结果、全部新增答案和剩余量机器数据。
- `verification.json`：机器对账结果，含首次组合与剩余量计数校验。
- `browser_verification.json`：真实浏览器桌面／窄屏阅读、答案展开和来源链接检查。
- `run_record.json`：生成器、真实输入、命令和输出清单。

## 生成

```bash
./.venv/Scripts/python.exe -X utf8 -I -B scripts/character_skills/cycle_report.py --cycle {args.cycle} --output {args.output.relative_to(ROOT)}
```

{generation_note}

## 审查与边界

{review_links}

{limits_note}
"""
    (args.output / "README.md").write_text(readme, encoding="utf-8")
    record = generation_record(args.cycle, cfg, metrics, args.output, batch_results, groups, unique_pairs, before_pairs)
    (args.output / "run_record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"cycle": args.cycle, "output": str(args.output),
                      "files": ["index.html", "remaining.html", "report_data.json", "README.md", "run_record.json", "verification.json"],
                      "has_answer": metrics["has_answer"], "backlog": metrics["backlog"], "split_check": split_count,
                      "new_rule_value_pairs": len(unique_pairs), "verification": verification["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
