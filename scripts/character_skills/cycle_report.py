#!/usr/bin/env python3
"""Generate versioned, database-style cycle result and remaining-work HTML pages.

The pages are generated from formal card pages and the effect ledger. Cycle-specific
batch summaries are declared below; all character names, Japanese source text and
current answer values are read back from the formal products at generation time.
"""
from __future__ import annotations

import argparse
import collections
import copy
import csv
import hashlib
import html
import json
import os
import re
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
    "C14": {
        "title": "C14｜2003 敌减益与 Boss 伤害直接链周期",
        "campaign": "8d96f313e71a122bf208cfe149a260df2017d98a35ebd9b109b7e9afe54cf62c",
        "snapshot": "8d96f313-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c14_delivery_20261103/pre_rebuild/cards",
        "delivery_review": "output/character_skills/review/c14_delivery_final_20261103_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261103-c14-delivery-package.md",
        "batches": [
            {
                "id": "C14-P1",
                "name": "2003 敌方减益直接载体链补隙",
                "binding": "c14_p1_2003",
                "task": "docs/tasks/20261102-c14-p1-2003-enemy-debuff.md",
                "review": "output/character_skills/review/c14_p1_2003_enemy_debuff_20261102_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "16行63答案：Y.G.12＋同域非Y.G.51。仅补not answers守卫跳过的B10/B13直接载体行；p9为受伤量倍率，不是固定防御减少；仅Skill型着弹，关联保持推断。",
            },
            {
                "id": "C14-P2",
                "name": "charainfo.pattern0 Boss 伤害直接链",
                "binding": "c14_p2_boss_damage_direct",
                "task": "docs/tasks/20261102-c14-p2-boss-damage-direct.md",
                "review": "output/character_skills/review/c14_p2_boss_damage_direct_20261102_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "10行10答案，全部Y.G.；pattern0原文、类型、N回param6与伤害槽逐行对应。局部伤害输入公式，非最终扣血；denju非首段6行与其他档位不并入。",
            },
        ],
    },
    "C15": {
        "title": "C15｜denju 非首段伤害直接链周期",
        "campaign": "65839ad742869b73949926049f85cdb1fab08d7e9bed8c721adc5ac32fa66e8b",
        "snapshot": "65839ad7-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c15_delivery_20261103/pre_rebuild/cards",
        "use_player_text_default": True,
        "allow_c14_p2_page_sha_drift": True,
        "delivery_review": "output/character_skills/review/c15_delivery_final_20261103_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261103-c15-delivery-package.md",
        "batches": [
            {
                "id": "C15-P1",
                "name": "denju.patternid0 非首段伤害直接链",
                "binding": "c15_p1_denju_damage_direct",
                "task": "docs/tasks/20261103-c15-p1-denju-damage-direct.md",
                "review": "output/character_skills/review/c15_p1_denju_damage_direct_20261103_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "5卡6行6答案，全部Y.G.；只按denju.patternid0→bosspattern→bossskill唯一链定源，不按同文复制。N回匹配type105/110的param6，大／中间隔只取允许类型；局部伤害输入公式，关联保持推断，P2/P3未启动。",
            },
        ],
    },
    "C16": {
        "title": "C16｜1095 逐效果部分绑定周期",
        "campaign": "09258f11cc04beda8662133cf8bf3be5ee77d36543d7290315b857e663406858",
        "snapshot": "09258f11-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c16_delivery_20261104/pre_rebuild/cards",
        "use_player_text_default": True,
        "allow_c14_p2_page_sha_drift": True,
        "delivery_review": "output/character_skills/review/c16_delivery_final_20261104_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261104-c16-delivery-package.md",
        "batches": [
            {
                "id": "C16-P1",
                "name": "skilllist ability1095 逐效果部分绑定",
                "binding": "c16_p1_1095_partial_binding",
                "task": "docs/tasks/20261104-c16-p1-1095-partial-binding.md",
                "review": "output/character_skills/review/c16_p1_1095_partial_20261104_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "23卡23行49答案：Y.G.23＋同域非Y.G.26。仅按真实charainfo.skillid[n]→父skilllist→唯一1095子记录→字段重算；复用既有五键，不全局删除旧P4，不跨层借值，额外活性槽与条件增强不并入，关联保持推断。",
            },
        ],
    },
    "C17": {
        "title": "C17｜1095 攻击逐效果部分绑定周期",
        "campaign": "dc38910014d6f4629ec13e2afc6d46e8ea2dbdc6568c48c8169fad15518417b2",
        "snapshot": "dc389100-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c17_delivery_20261106/pre_rebuild/cards",
        "use_player_text_default": True,
        "allow_c14_p2_page_sha_drift": True,
        "delivery_review": "output/character_skills/review/c17_delivery_final_20261106_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261106-c17-delivery-package.md",
        "batches": [
            {
                "id": "C17-P1",
                "name": "skilllist ability1095 仅攻击逐效果部分绑定",
                "binding": "c17_p1_1095_attack_partial_binding",
                "task": "docs/tasks/20261106-c17-p1-1095-attack-partial.md",
                "review": "output/character_skills/review/c17_p1_1095_attack_partial_20261106_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "3卡3行3答案，全部Y.G.。只按真实charainfo.skillid[n]→父skilllist→唯一1095子记录→/param1重算；额外param6与句外条件强化不并入，复用既有规则与账本映射，关联保持推断，P2/P3未启动。",
            },
        ],
    },
    "C18": {
        "title": "C18｜1095 同类攻击外推周期",
        "campaign": "01c05f78bd54263efd40991b96e3aed2a421cce3e0845e5e49bb4fcd03d114c3",
        "snapshot": "01c05f78-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c18_delivery_20261106/pre_rebuild/cards",
        "use_player_text_default": True,
        "allow_c14_p2_page_sha_drift": True,
        "delivery_review": "output/character_skills/review/c18_delivery_final_20261106_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261106-c18-delivery-package.md",
        "batches": [
            {
                "id": "C18-P1",
                "name": "skilllist ability1095 同类攻击外推",
                "binding": "c18_p1_1095_attack_partial_binding",
                "task": "docs/tasks/20261106-c18-p1-1095-attack-partial.md",
                "review": "output/character_skills/review/c18_p1_1095_attack_partial_20261106_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "2卡2行2答案，全部非Y.G.。6341提高22.5%、20333提高37.5%；只按真实charainfo.skillid[n]→父skilllist→唯一1095子记录→/param1重算，额外param6与句外条件强化不并入，关联保持推断，P2/P3未启动。",
            },
        ],
    },
    "C19": {
        "title": "C19｜1095 与 type8 同族扩大周期",
        "campaign": "99bee2a166e5ec5f9c03ac97b555d4ada2f6f30d1535258add16bc64c7227c66",
        "snapshot": "99bee2a1-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c19_delivery_20261107/pre_rebuild/cards",
        "use_player_text_default": True,
        "allow_c14_p2_page_sha_drift": True,
        "delivery_review": "output/character_skills/review/c19_delivery_final_20261107_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261107-c19-delivery-package.md",
        "batches": [
            {
                "id": "C19-P1",
                "name": "CACHE 1095 同族扩大",
                "binding": "c19_p1_1095_attack_families_binding",
                "task": "docs/tasks/20261107-c19-p1-1095-attack-families.md",
                "review": "output/character_skills/review/c19_attack_candidates_20261107_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "130行404答案：攻击130、移速74、减伤71、暴击率90、暴伤39。直接父与唯一sub两种1095载体，缺param5不补零，额外param6与句外条件强化不并入，关联保持推断。",
            },
            {
                "id": "C19-P2",
                "name": "APK type8 基础攻击",
                "binding": "c19_p2_type8_basic_attack_binding",
                "task": "docs/tasks/20261107-c19-p2-type8-basic-attack.md",
                "review": "output/character_skills/review/c19_attack_candidates_20261107_deepseek/REPORT.md",
                "verdict": "例行独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断",
                "notes": "1063提高35%、1238提高75%、12220提高10%。APK原层整句与source span消歧，旧B3/B4/B11拒绝原因保留，type96未决与其他条件不并入。",
            },
        ],
    },
    "C20": {
        "title": "C20｜P1 Y.G. 与 P2 非 Y.G. 条件选档直接伤害周期",
        "campaign": "754f04b6f552fc2a993c7c7b1de233fc7d138cbac35497c28ce12478a30f4373",
        "snapshot": "754f04b6-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c20_delivery_20261108/corrective_rebuild/cards",
        "use_player_text_default": True,
        "allow_c14_p2_page_sha_drift": True,
        "disclose_row_unresolved": True,
        "disclose_row_split_flags": True,
        "show_player_scope_default": True,
        "split_effect_answer_summary": True,
        "effect_label": "伤害效果",
        "split_panel_note": "效果与答案不是同一口径：P2 的 HP 档、Chain 等分支在同一效果下给出多条答案，因此 18 个效果对应 25 条答案，不合并成一个数汇报。",
        "delivery_review": "output/character_skills/review/c20_delivery_final_20261108_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261108-c20-delivery-package.md",
        "candidate_review": "output/character_skills/review/c20_attack_candidates_20261108_deepseek/REPORT.md",
        "expected_totals": {
            "rows": 18, "cards": 16, "answers": 25, "effects": 18,
            "yg_answers": 10, "non_yg_answers": 15,
            "yg_effects": 10, "non_yg_effects": 8,
            "p1": {"rows": 10, "cards": 9, "answers": 10, "effects": 10},
            "p2": {"rows": 8, "cards": 7, "answers": 15, "effects": 8},
        },
        "batches": [
            {
                "id": "C20-P1",
                "name": "P1｜Y.G. 必殺直接伤害（CACHE，10行10效果10答案）",
                "binding": "c20_p1_yg_direct_damage",
                "task": "docs/tasks/20261108-c20-p1-yg-direct-damage.md",
                "review": "output/character_skills/review/c20_attack_candidates_20261108_deepseek/REPORT.md",
                "verdict": "候选独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断；交付包正式生成 48/48 PASS",
                "notes": "9卡10行10效果10答案，全部Y.G.，只取缓存层。按父记录的唯一子槽定位到伤害记录。数值是局部伤害输入（技能基值倍率），不是最终扣血、保证命中或实机伤害。缺参数不补零，其它档位／其它记录与句外强化不并入；句面到记录的归属为推断，未做运行时验证。同句未解子句（击飞、眩晕等）按行级拆分标志默认披露。",
            },
            {
                "id": "C20-P2",
                "name": "P2｜非 Y.G. 条件选档直接伤害（CACHE＋APK，8行8效果15答案）",
                "binding": "c20_p2_nonyg_direct_damage",
                "task": "docs/tasks/20261108-c20-p2-nonyg-direct-damage.md",
                "review": "output/character_skills/review/c20_attack_candidates_20261108_deepseek/REPORT.md",
                "verdict": "候选独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、零阻断；交付包正式生成 48/48 PASS",
                "notes": "7卡8行8效果15答案，全部非Y.G.，缓存与安装包按行分层。HP档、Chain、次数上限、地形、职业法珠／废料计数等必要条件按完整父集合逐条给出；同一效果的多档答案属正常分支，不重复计效果。12226增强档按原表精度保留，不按玩家文案四舍五入。20332自身受伤与另一类效果另论；归属推断、未实机，最终扣血未验证。",
            },
        ],
    },
    "C21": {
        "title": "C21｜全角色 special 与 denju 直接多段／大伤害来源绑定周期",
        "campaign": "5492e173e3fa7c918eb3a2a701d6471e4a84246927e9450cf1cd99d3bc74e010",
        "snapshot": "5492e173-cf9451c6ff47fcfb",
        "rules": "294 键，SHA-16 cf9451c6ff47fcfb",
        "before_cards": "output/character_skills/c21_delivery_20261111/pre_rebuild/cards",
        "use_player_text_default": True,
        "allow_c14_p2_page_sha_drift": True,
        "disclose_row_unresolved": True,
        "disclose_row_split_flags": True,
        "show_player_scope_default": True,
        "split_effect_answer_summary": True,
        "effect_label": "伤害效果",
        "split_panel_note": "效果与答案分别统计：本批每行恰一个目标伤害效果并新增一条答案，因此二者均为900；这不代表900行或518张卡已经全部解释完成。P1=766，P2=134；严格直接来源899项，CID30304首句条件镜像1项。",
        "delivery_review": "output/character_skills/review/c21_delivery_final_20261111_deepseek/REPORT.md",
        "delivery_task": "docs/tasks/20261111-c21-delivery-package.md",
        "expected_totals": {
            "rows": 900, "cards": 518, "answers": 900, "effects": 900,
            "yg_answers": 11, "non_yg_answers": 889,
            "yg_effects": 11, "non_yg_effects": 889,
            "p1": {"rows": 766, "cards": 517, "answers": 766, "effects": 766},
            "p2": {"rows": 134, "cards": 107, "answers": 134, "effects": 134},
        },
        "batches": [
            {
                "id": "C21-P1",
                "name": "P1｜special 直接伤害（CACHE 259＋APK 507，766行766效果766答案）",
                "binding": "c21_p1_special_direct_binding",
                "task": "docs/tasks/20261111-c21-p1-special-direct.md",
                "review": "output/character_skills/review/c21_special_candidates_20261111_deepseek/REPORT.md",
                "verdict": "候选独立审查通过；正式独立终审23/23、阻断0",
                "notes": "517卡766行766效果766答案，含Y.G.超共鸣直接伤害10项。逐行按同层charainfo→bosspattern→bossskill重导，CACHE与APK不混源；多段次数与skillparam6一致，大／中伤害使用单发型，反響不借首次直接攻击槽。数值是局部伤害输入，关联推断，未做新原生或实机验证。",
            },
            {
                "id": "C21-P2",
                "name": "P2｜denju 直接伤害与首句条件镜像（全部CACHE，134行134效果134答案）",
                "binding": "c21_p2_denju_direct_binding",
                "task": "docs/tasks/20261111-c21-p2-denju-direct.md",
                "review": "output/character_skills/review/c21_denju_candidates_20261111_deepseek/REPORT.md",
                "verdict": "候选独立审查通过；正式独立终审23/23、阻断0",
                "notes": "107卡134行134效果134答案：133项传授全文一致的直接denju，加上CID30304一项首句条件镜像。父集合从denju记录重导，不误用charainfo；CID30304全文不一致明示，不与直接项混计。局部伤害输入不等于最终扣血或命中，关联均为推断。",
            },
        ],
    },
}

# C19-R01仅重建展示，不改变原C19的周期配置或正式答案消费路径。
CYCLES["C19_R01"] = copy.deepcopy(CYCLES["C19"])
CYCLES["C19_R01"].update({
    "title": "C19-R01｜同句未解效果就地披露整改",
    "disclose_row_unresolved": True,
    "rectification_display": "R01",
    "direction_review": "output/character_skills/review/direction_c19_20261107_thirdparty/REPORT.md",
    "rectification_task": "docs/tasks/20261107-c19-r01-row-unresolved-rectification.md",
    "original_cycle_report": "output/character_skills/cycle_reports/C19/index.html",
})

# C20-R01只补展开层的父集合与分支证据，不改变正式答案消费路径。
CYCLES["C20_R01"] = copy.deepcopy(CYCLES["C20"])
CYCLES["C20_R01"].update({
    "title": "C20-R01｜F01 完整父集合与合并／排除分支披露",
    "rectification_display": "F01",
    "direction_review": "output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/v05/REPORT.md",
    "rectification_task": "docs/tasks/20261109-c20-f01-expanded-parents.md",
    "original_cycle_report": "output/character_skills/cycle_reports/C20/index.html",
    "expected_batch_prefix": "C20",
})

CYCLES["C20_R02"] = copy.deepcopy(CYCLES["C20_R01"])
CYCLES["C20_R02"].update({
    "title": "C20-R02｜F01 描述来源父与本答案分支父标记",
    "rectification_stage": "PARENT_MARKER",
    "direction_review": "output/character_skills/review/c20_post_closeout_independent_recheck_20261109_deepseek/f01_recheck_v01/REPORT.md",
    "rectification_task": "docs/tasks/20261109-c20-f01-parent-marker-r02.md",
    "original_cycle_report": "output/character_skills/cycle_reports/C20_r01_20261109/index.html",
})

# C21-R01只改默认条件表达与展开证据，正式答案、原C21成果和原第三方裁决不变。
CYCLES["C21_R01"] = copy.deepcopy(CYCLES["C21"])
CYCLES["C21_R01"].update({
    "title": "C21-R01｜F01／F02 必要条件与玩家Chain档位展示整改",
    "condition_display": "C21_R01",
    "rectification_c21_conditions": True,
    "direction_review": "output/character_skills/review/direction_c21_20261112_thirdparty/REPORT.md",
    "rectification_task": "docs/tasks/20261112-c21-r01-condition-display.md",
    "original_cycle_report": "output/character_skills/cycle_reports/C21/index.html",
    "expected_batch_prefix": "C21",
})

CSS = """
:root{--bg:#f4f6f9;--panel:#fff;--ink:#202938;--muted:#64748b;--line:#dbe3ec;--blue:#1d4ed8;--green:#047857;--amber:#b45309;--violet:#6d28d9}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI","Noto Sans CJK SC","Microsoft YaHei",sans-serif;line-height:1.6}
header{background:linear-gradient(120deg,#172554,#1e40af);color:white;padding:28px 34px}header h1{margin:0 0 8px;font-size:26px}header p{margin:4px 0;color:#dbeafe}main{max-width:1500px;margin:24px auto;padding:0 18px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:20px;margin:18px 0;box-shadow:0 2px 8px #0f172a0a}
h2{font-size:21px;margin:0 0 12px}h3{font-size:17px;margin:18px 0 8px}.muted{color:var(--muted)}.small{font-size:13px}.stats{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}.stat{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:8px 12px;font-weight:600;color:#1e40af}.badge{display:inline-block;border-radius:5px;padding:1px 7px;font-size:12px;margin-right:5px;background:#e2e8f0;color:#334155}.badge.pass{background:#d1fae5;color:#065f46}.badge.unknown{background:#fef3c7;color:#92400e}.badge.infer{background:#ede9fe;color:#5b21b6}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}th{background:#eaf0f7;font-weight:700}tr:nth-child(even) td{background:#f8fafc}.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}@media(max-width:640px){.table-wrap table{min-width:720px}}.jp{font-family:"Noto Sans CJK JP","Yu Gothic","Hiragino Kaku Gothic ProN",sans-serif}.name{font-weight:650;white-space:nowrap}.num{font-variant-numeric:tabular-nums;white-space:nowrap}.links a{color:var(--blue);margin-right:14px}details{cursor:pointer}details summary{color:var(--blue)}.value{max-width:760px;white-space:pre-wrap}.warning{background:#fff7ed;border-left:4px solid var(--amber);padding:10px 14px}.footer{color:var(--muted);font-size:12px;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}.metric{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:10px}.metric b{display:block;font-size:20px;color:#1e40af}
.table-wrap{overflow-x:auto}.value{overflow-wrap:anywhere}code{overflow-wrap:anywhere;word-break:break-word}details.unresolved-effect{margin:6px 0;padding:6px 8px;background:#fff7ed;border-left:3px solid var(--amber)}details.unresolved-effect summary{color:#92400e}details.unresolved-effect .value{color:#78350f}
.answer-default{margin:0 0 4px}.answer-default-meta{background:#f1f5f9;border-left:3px solid #94a3b8;padding:4px 8px;border-radius:4px;margin:4px 0}.unresolved-row{margin:6px 0;padding:6px 8px;background:#fff7ed;border-left:3px solid var(--amber)}.unresolved-row>details{display:inline-block;margin-left:6px;vertical-align:top}
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
    backlog_by_id = {}
    if cfg.get("disclose_row_unresolved"):
        backlog_by_id = {item["backlog_id"]: item
                         for item in load_json(LEDGER / "backlog.json")
                         if item.get("kind") == "effect"}
    rows = []
    removed = []
    stats = {"id": batch["id"], "rows": 0, "cards": set(), "answers": 0, "effect_net": 0,
             "yg_answers": 0, "non_yg_answers": 0, "yg_effect_net": 0, "non_yg_effect_net": 0,
             "before_unresolved": 0, "after_unresolved": 0,
             "complete_net": 0, "yg_complete_net": 0, "non_yg_complete_net": 0, "s4_after": 0}
    for cid in sorted(int(path.stem) for path in (ROOT / cfg["before_cards"]).glob("*.json")):
        before_data = before_card_data(cid, cfg)
        after_data = card_data(cid, cfg)
        before_rows, after_rows = row_map(before_data), row_map(after_data)
        for row_id, after_row in after_rows.items():
            before_row = before_rows.get(row_id)
            before_answers = (before_row or {}).get("answers") or []
            after_answers = after_row.get("answers") or []
            if after_answers[:len(before_answers)] != before_answers:
                # C15重建会重算既有C14-P2答案的构建前页面指纹。仅在该周期、
                # 答案数不变且剥离此单字段后完全一致时跳过；其他改值仍硬失败。
                if len(after_answers) != len(before_answers) or not cfg.get("allow_c14_p2_page_sha_drift"):
                    raise ValueError(f"旧答案被改写：{row_id}")
                normalized_before = copy.deepcopy(before_answers)
                normalized_after = copy.deepcopy(after_answers)
                for answer in normalized_before + normalized_after:
                    g1_b1 = (answer.get("binding") or {}).get("g1_b1_binding") or {}
                    g1_b1.pop("page_sha256", None)
                if normalized_after != normalized_before:
                    raise ValueError(f"旧答案被改写（非page_sha256字段）：{row_id}")
                continue
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
            yg = "Y.G." in character_name(after_data)
            prefix = "yg" if yg else "non_yg"
            stats[f"{prefix}_answers"] += len(appended)
            stats[f"{prefix}_effect_net"] += after_counts["has_answer"] - before_counts["has_answer"]
            stats[f"{prefix}_complete_net"] += int(row_status(after_analysis) == "完整") - int(row_status(before_analysis) == "完整")
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
            unresolved_effects = []
            if cfg.get("disclose_row_unresolved"):
                for effect in after_analysis.get("effects") or []:
                    if effect.get("status") != "unresolved":
                        continue
                    evidence = backlog_by_id.get(effect["effect_id"])
                    if not evidence or evidence.get("row_id") != row_id:
                        raise ValueError(f"正式backlog缺少同row_id未解证据：{effect['effect_id']}")
                    unresolved_effects.append(dict(effect, gap_evidence=evidence))
            row_split_flags = list(after_analysis.get("split_flags") or [])
            rows.append({"cid": cid, "name": character_name(after_data), "row_id": row_id,
                         "japanese": after_row.get("japanese", ""),
                         "reference_field": after_row.get("reference_field"),
                         "stage": after_row.get("stage"), "level": after_row.get("level"),
                         "fragment_index": after_row.get("fragment_index"),
                         "before": before_row, "after": after_row, "answers": appended,
                         **({"unresolved_effects": unresolved_effects}
                            if cfg.get("disclose_row_unresolved") else {}),
                         **({"row_split_flags": row_split_flags}
                            if cfg.get("disclose_row_split_flags") else {})})
    if stats["rows"] == 0:
        raise ValueError(f"批次没有新增答案：{batch['id']}")
    stats["cards"] = len(stats["cards"])
    return {"stats": stats, "rows": rows, "removed_effects": removed}



def relative_href(output_dir: Path, target: str) -> str:
    """Return a relative link from the report directory to a project-root target."""
    return os.path.relpath(ROOT / target, output_dir).replace(os.sep, "/")


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def scope_answer_disclosure(answer: dict):
    """Render parent order and branch evidence already present in C20 answer bindings."""
    disclosure = next((value for value in (answer.get("binding") or {}).values()
                       if isinstance(value, dict) and "complete_parent_set" in value), None)
    if not disclosure:
        return ""
    current = disclosure.get("current_parent") or {}
    selected = disclosure.get("selected") or {}
    parents = disclosure.get("complete_parent_set") or []
    first_ref = str((parents[0] if parents else {}).get("reference_field") or "")
    parent_owner = "denju" if disclosure.get("denju") or first_ref.startswith("patternid") else "charainfo"
    parts = [f'<div class="parent-set-disclosure"><b>完整父集合（按 {parent_owner} 引用顺序）</b><ol>']
    for index, parent in enumerate(disclosure.get("complete_parent_set") or [], 1):
        is_description_source = (parent.get("reference_field") == current.get("reference_field")
                                 and parent.get("pattern_id") == current.get("pattern_id"))
        is_answer_branch = (parent.get("reference_field") == selected.get("reference_field")
                            and parent.get("pattern_id") == selected.get("pattern_id"))
        markers = []
        if is_description_source:
            markers.append("当前描述来源父")
        if is_answer_branch:
            markers.append("本答案分支父")
        marker_html = "；" + "；".join(f"<b>{marker}</b>" for marker in markers) if markers else ""
        pointer = parent.get("json_pointer") or parent.get("pattern_json_pointer") or "未单列"
        parts.append(
            f'<li>引用顺序 {index}：{html.escape(str(parent.get("reference_field") or "未单列"))}'
            f'；pattern={html.escape(str(parent.get("pattern_id")))}'
            f'；pattern_index={html.escape(str(parent.get("pattern_index")))}'
            f'；pattern_json_pointer=<code>{html.escape(str(pointer))}</code>'
            f'{marker_html}<br>'
            f'原始条件：{html.escape(compact_json(parent.get("conditions_raw") or {}))}<br>'
            f'子记录（按 slot 顺序）：{html.escape(compact_json(parent.get("children") or []))}</li>')
    parts.append('</ol></div>')
    for field, label, css_class in (("merged_disclosures", "合并分支", "merged-branch-disclosure"),
                                    ("excluded_branch_values", "排除分支", "excluded-branch-disclosure")):
        for index, item in enumerate(disclosure.get(field) or [], 1):
            selection = item.get("selection") or {}
            source = selection.get("source") or {}
            pattern_pointer = (selection.get("pattern_json_pointer") or selection.get("json_pointer")
                               or "未单列")
            parts.append(
                f'<div class="{css_class}"><b>{label} {index}</b>：'
                f'{html.escape(str(selection.get("reference_field") or "未单列"))}'
                f'；pattern={html.escape(str(selection.get("pattern_id")))}'
                f'；pattern_index={html.escape(str(selection.get("pattern_index")))}'
                f'；pattern_json_pointer=<code>{html.escape(str(pattern_pointer))}</code><br>'
                f'原始条件：{html.escape(compact_json(selection.get("parent_conditions_raw") or {}))}<br>'
                f'child_slot={html.escape(str(selection.get("child_slot")))}'
                f'；record={html.escape(str(selection.get("record_id")))}'
                f'；record_index={html.escape(str(selection.get("record_index")))}'
                f'；type={html.escape(str(selection.get("type")))}'
                f'；field={html.escape(str(selection.get("field")))}'
                f'；raw={html.escape(compact_json(selection.get("raw_value")))}'
                f'；raw_state={html.escape(str(selection.get("raw_state")))}<br>'
                f'规则键：{html.escape(str(selection.get("rule_key") or "未单列"))}'
                f'；来源层：{html.escape(str(source.get("layer") or "未单列"))}'
                f'；记录指针：<code>{html.escape(str(source.get("json_pointer") or "未单列"))}</code>'
                f'；字段指针：<code>{html.escape(str(source.get("field_json_pointer") or "未单列"))}</code><br>'
                f'理由：{html.escape(str(item.get("reason") or "未单列"))}</div>')
    mirror = disclosure.get("mirror") or {}
    if mirror:
        parts.append(
            '<div class="condition-mirror-disclosure"><b>首句条件镜像（不是全文一致直接绑定）</b><br>'
            f'全文一致：{html.escape(str(mirror.get("full_text_equal")))}'
            f'；首句一致：{html.escape(str(mirror.get("first_sentence_equal")))}'
            f'；当前片段为首句：{html.escape(str(mirror.get("fragment_is_first_sentence")))}<br>'
            f'首句：{html.escape(str(mirror.get("first_sentence") or "未单列"))}<br>'
            f'denju全文：{html.escape(str(mirror.get("denju_full_text") or "未单列"))}<br>'
            f'pattern全文：{html.escape(str(mirror.get("pattern_full_text") or "未单列"))}<br>'
            f'同记录既有答案：{html.escape(compact_json(mirror.get("existing_same_record_answers") or []))}<br>'
            f'说明：{html.escape(str(mirror.get("note") or "未单列"))}</div>')
    return "".join(parts)


def c21_binding(answer: dict):
    """Return the unique C21 disclosure binding without altering the formal answer."""
    return next((value for value in (answer.get("binding") or {}).values()
                 if isinstance(value, dict) and str(value.get("scope") or "").startswith("C21_")
                 and "complete_parent_set" in value), {})


def c21_default_player_text(answer: dict, default_text: str):
    """Keep denju source mechanics in the expanded layer, not the player summary."""
    binding = c21_binding(answer)
    if binding.get("scope") != "C21_P2_DENJU_DIRECT_20261111":
        return default_text
    base = default_text.split("条件：", 1)[0]
    base = base.split("本项来自传授", 1)[0].split("本项是条件镜像", 1)[0].strip()
    if binding.get("model") == "DENJU_CONDITION_MIRROR":
        addition = ("仅适用于传授首句分支；传授全文与必杀原文不完全一致，"
                    "本项是首句条件镜像，关联为推断。")
    else:
        addition = "本项来自传授链，传授原文与所选分支原文逐字一致；句面归属为推断。"
    return f"{base} {addition}"


def c21_default_conditions(answer: dict, conditions):
    binding = c21_binding(answer)
    if binding.get("scope") != "C21_P2_DENJU_DIRECT_20261111":
        return conditions
    mirror = binding.get("model") == "DENJU_CONDITION_MIRROR"
    readable = []
    for condition in conditions:
        text = str(condition)
        if text.startswith("来源链："):
            continue
        if "denju.patternid" in text or "denju.stext" in text or "pattern.sinfo" in text:
            text = ("仅当传授首句分支被选中时；传授全文与必杀原文不完全一致，"
                    "本项仅为首句条件镜像（推断）" if mirror else
                    "对应传授分支被选中，且传授原文与该分支原文逐字一致")
        elif text.startswith("条件镜像："):
            text = "条件镜像：传授全文与必杀原文不完全一致，仅在首句身份及同来源同值答案同时成立时披露"
        text = text.replace("CACHE静态原表", "静态数据对应").replace("denju", "传授")
        if text and text not in readable:
            readable.append(text)
    return readable


def c21_r01_raw_conditions(answer: dict):
    """Read only the selected answer branch; never borrow a sibling branch's gates."""
    selected = c21_binding(answer).get("selected") or {}
    raw = selected.get("parent_conditions_raw") or selected.get("conditions_raw")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"C21_R01缺少selected分支原始条件：{answer.get('record_id')}")
    return raw


def c21_r01_chain_label(chs: int, che: int):
    labels = {
        (0, 0): "未设置Chain区间条件（仅指该字段；其他必要条件另列）",
        (0, 1): "通常（0thChain）当前分支",
        (0, 2): "通常（0th）至1stChain当前分支",
        (0, 3): "通常（0th）至2ndChain（适用玩家Chain路径；原始0的特殊无Chain路径见展开说明）",
        (0, 4): "通常（0th）至3rdChain（适用玩家Chain路径；原始0的特殊无Chain路径见展开说明）",
        (2, 5): "1stChain以上（含MaxChain）当前分支",
        (4, 5): "3rdChain至MaxChain当前分支",
    }
    key = (chs, che)
    if key not in labels:
        raise ValueError(f"C21_R01未登记的Chain区间：{key}")
    return labels[key]


def c21_r01_mana_disclosure(raw: dict):
    """Separate text-explicit facts from unresolved mana/scrap timing and selection semantics."""
    text = str(raw.get("sinfo") or "")
    known = []
    scrap_gate = re.search(r"スクラップが(\d+)(?:個|つ)以上", text)
    mana_gate = re.search(r"マナが(\d+)つ以上で(?:必殺技を)?発動", text)
    mana_ceiling = re.search(r"マナが(\d+)つ以下で発動", text)
    if scrap_gate:
        known.append(f"原文含‘斯库拉普不少于{scrap_gate.group(1)}个’的条件描述")
    if mana_gate:
        known.append(f"原文含‘法珠不少于{mana_gate.group(1)}个时发动’的描述")
    if mana_ceiling:
        known.append(f"原文含‘法珠不超过{mana_ceiling.group(1)}个时发动’的描述")
    if "マナが多いほど" in text:
        known.append("原文含‘法珠越多威力越高’的强化描述，本项不解释该增幅")
    if not known:
        if "スクラップ" in text:
            known.append("原文含斯库拉普相关描述")
        elif "マナ" in text:
            known.append("原文含法珠相关描述")
        else:
            known.append("原表存在法珠／废料计数门")
    if "スクラップ" in text and ("生成" in text or "破壊" in text):
        known.append("原文另有斯库拉普生成／破坏描述，不并入本伤害答案")
    unknown = [
        "原始计数区间的具体对象未完全确认",
        "扣费前后阈值、重置时机及本分支完整选档未验证",
    ]
    return "；".join(known + unknown), known, unknown


def c21_r01_condition_projection(answer: dict, conditions):
    raw = c21_r01_raw_conditions(answer)
    chs = raw.get("chs") or 0
    che = raw.get("che") or 0
    limit = raw.get("limit")
    bgf = raw.get("bgf")
    mne = raw.get("mne")
    necessary = [c21_r01_chain_label(chs, che)]
    kinds = []
    if (chs, che) in ((0, 3), (0, 4), (4, 5)):
        kinds.append("chain")
    if limit == 1:
        kinds.append("limit")
        necessary.append("本分支已使用次数小于1次（不是整个技能第几次；重置时机、优先级／切换边界及完整选档未验证）")
    elif limit not in (None, 0):
        raise ValueError(f"C21_R01未登记的使用次数门：{limit}")
    if bgf == 1114112:
        kinds.append("terrain")
        necessary.append("地形为沙滩／船上／海中（按原文；必要条件；不据此推导另一分支为地形补集）")
    elif bgf == 4096:
        kinds.append("terrain")
        necessary.append("地形为荒地（按原文；必要条件；不据此推导另一分支为地形补集）")
    elif bgf not in (None, 0):
        raise ValueError(f"C21_R01未登记的地形门：{bgf}")
    mana_known = []
    mana_unknown = []
    if mne not in (None, 0):
        kinds.append("mana")
        mana_text, mana_known, mana_unknown = c21_r01_mana_disclosure(raw)
        necessary.append(mana_text)
    retained = []
    internal_labels = (
        "当前基础档", "Chain计数", "0thChain（通常）当前档", "0th／1stChain当前档",
        "1stChain以上（含MaxChain）当前档",
    )
    for condition in c21_default_conditions(answer, list(conditions)):
        text = str(condition)
        if any(label in text for label in internal_labels):
            continue
        if text and text not in retained:
            retained.append(text)
    readable = []
    for text in necessary + retained:
        if text and text not in readable:
            readable.append(text)
    return {
        "raw": raw, "chain": [chs, che], "necessary": necessary,
        "conditions": readable, "kinds": kinds,
        "mana_known": mana_known, "mana_unknown": mana_unknown,
    }


def c21_r01_default_player_text(answer: dict, default_text: str):
    binding = c21_binding(answer)
    if binding.get("scope") == "C21_P2_DENJU_DIRECT_20261111":
        base = c21_default_player_text(answer, default_text)
    else:
        base = default_text.split("条件：", 1)[0].strip()
    necessary = c21_r01_condition_projection(answer, [])["necessary"]
    return f"{base} 条件：{'；'.join(necessary)}"


def c21_r01_expanded_condition(answer: dict):
    projection = c21_r01_condition_projection(answer, [])
    raw = projection["raw"]
    chs, che = projection["chain"]
    special = ("原始chs=0可包含特殊无Chain路径；玩家档位标签只用于适用玩家Chain路径，"
               "完整选档与运行时装载未验证。" if chs == 0 and che >= 3 else
               "完整选档与运行时装载未验证。")
    mana = ""
    if projection["mana_unknown"]:
        mana = f'<br>法珠／废料未知边界：{html.escape("；".join(projection["mana_unknown"]))}'
    return (f'<div class="c21-r01-condition-evidence"><b>C21-R01本答案分支条件证据</b><br>'
            f'玩家可读必要条件：{html.escape("；".join(projection["necessary"]))}<br>'
            f'selected.parent_conditions_raw：<code>{html.escape(compact_json(raw))}</code><br>'
            f'Chain原始区间：[{chs}, {che}]；{html.escape(special)}'
            f'{mana}</div>')


def answer_block(answer: dict, row: dict, output_dir: Path, cid: int, use_player_text: bool = False,
                 show_scope: bool = False, condition_display: str | None = None):
    source = answer.get("source") or {}
    table = answer.get("table") or source.get("table") or "未单列"
    record_id = answer.get("record_id")
    if record_id is None:
        record_id = source.get("record_id")
    if record_id is None:
        record_id = "未单列"
    layer = answer.get("layer") or source.get("layer") or "未单列"
    field_path = (answer.get("field_path") or source.get("field_path")
                  or source.get("field") or "未单列")
    record_key = source.get("record_key") or "未单列"
    pointer = source.get("json_pointer")
    source_display = pointer or record_key
    pointer_display = pointer or "未单列（不伪造；当前 source 未提供）"
    conditions = answer.get("conditions") or row.get("conditions") or row.get("condition") or "未单列"
    if not isinstance(conditions, str):
        conditions = json.dumps(conditions, ensure_ascii=False, separators=(",", ":"))
    condition_label = answer.get("condition_label") or row.get("condition_label") or "未单列"
    obj = answer.get("target") or answer.get("object") or row.get("object") or row.get("target") or "未单列"
    evidence = f"numeric={answer.get('numeric_evidence')}；association={answer.get('association_evidence')}；scope={answer.get('evidence_scope')}"
    player_text = answer.get("player_text") if use_player_text else None
    if player_text:
        default_text = str(player_text)
        if condition_display == "C21_R01":
            default_text = c21_r01_default_player_text(answer, default_text)
        else:
            default_text = c21_default_player_text(answer, default_text)
        if answer.get("association_evidence") == "推断" and "推断" not in default_text:
            default_text += " 句面到来源的关联为推断。"
        summary = html.escape(default_text)
        precise = f'精确公式／研究说明：{html.escape(str(answer.get("value") or "未列值"))}<br>'
    else:
        summary = (f'{html.escape(str(answer.get("quantity_kind") or answer.get("unit") or "答案"))}：'
                   f'{html.escape(str(answer.get("value") or "未列值"))}')
        precise = ""
    if show_scope:
        # C20／C21：默认层给对象、局部量纲与必要条件；公式、原值、表／字段／指针与排除项留在展开层。
        scope = answer.get("player_scope") if isinstance(answer.get("player_scope"), dict) else {}
        bits = []
        obj_disp = scope.get("object") or obj
        if obj_disp and obj_disp != "未单列":
            bits.append(f"对象：{html.escape(str(obj_disp))}")
        qty_disp = scope.get("quantity") or answer.get("quantity_kind")
        if qty_disp:
            bits.append(f"局部量：{html.escape(str(qty_disp))}"
                        f"（{html.escape(str(scope.get('unit') or answer.get('unit') or '未单列'))}）")
        scope_conditions = scope.get("conditions")
        if isinstance(scope_conditions, str):
            scope_conditions = [scope_conditions]
        if not scope_conditions:
            scope_conditions = [conditions] if isinstance(conditions, str) else list(conditions)
        scope_conditions = c21_default_conditions(answer, scope_conditions)
        if condition_display == "C21_R01":
            scope_conditions = c21_r01_condition_projection(answer, scope_conditions)["conditions"]
        cond_disp = "；".join(html.escape(str(c)) for c in scope_conditions if c) or "未单列"
        unknowns = [str(u) for u in scope.get("unknowns") or [] if u]
        duration = scope.get("duration")
        exclude_html = (f'排除／不并入与仍未验证：{html.escape("；".join(unknowns))}<br>'
                        if unknowns else "")
        duration_html = f'持续／周期：{html.escape(str(duration))}<br>' if duration else ""
        rectified_condition_html = (c21_r01_expanded_condition(answer)
                                    if condition_display == "C21_R01" else "")
        return (f'<div class="answer-default">{summary}</div>'
                f'<div class="answer-default-meta small">{"；".join(bits) or "对象：未单列"}<br>'
                f'必要条件：{cond_disp}</div>'
                f'<details><summary>展开：公式、原值、表／字段／指针与排除</summary><div class="value small">'
                f'{precise}'
                f'单位／量纲：{html.escape(str(answer.get("unit") or "未单列"))}<br>'
                f'表：{html.escape(str(table))}<br>'
                f'对象：{html.escape(str(obj))}<br>'
                f'逐行 condition_label：{html.escape(str(condition_label))}<br>'
                f'规则适用域 conditions：{html.escape(str(conditions))}<br>'
                f'{duration_html}'
                f'阶段：{html.escape(str(row.get("stage") or row.get("reference_field") or "未单列"))}'
                f'　fragment={html.escape(str(row.get("fragment_index")))}<br>'
                f'规则键：{html.escape(str(answer.get("rule_key") or "无"))}<br>'
                f'原值：{html.escape(str(answer.get("raw_value")))}；记录：{html.escape(str(record_id))}'
                f'（{html.escape(str(layer))}）<br>'
                f'record_key：{html.escape(str(record_key))}<br>'
                f'字段：{html.escape(str(field_path))}<br>'
                f'来源：{html.escape(str(source_display))}<br>'
                f'逐答案 json_pointer：{html.escape(str(pointer_display))}<br>'
                f'{rectified_condition_html}'
                f'{scope_answer_disclosure(answer)}'
                f'{exclude_html}'
                f'证据：{html.escape(evidence)}</div></details>')
    return (f'<details><summary>{summary}</summary><div class="value small">'
            f'{precise}'
            f'单位／量纲：{html.escape(str(answer.get("unit") or "未单列"))}<br>'
            f'表：{html.escape(str(table))}<br>'
            f'对象：{html.escape(str(obj))}<br>'
            f'逐行 condition_label：{html.escape(str(condition_label))}<br>'
            f'规则适用域 conditions：{html.escape(str(conditions))}<br>'
            f'阶段：{html.escape(str(row.get("stage") or row.get("reference_field") or "未单列"))}'
            f'　fragment={html.escape(str(row.get("fragment_index")))}<br>'
            f'规则键：{html.escape(str(answer.get("rule_key") or "无"))}<br>'
            f'原值：{html.escape(str(answer.get("raw_value")))}；记录：{html.escape(str(record_id))}'
            f'（{html.escape(str(layer))}）<br>'
            f'record_key：{html.escape(str(record_key))}<br>'
            f'字段：{html.escape(str(field_path))}<br>'
            f'来源：{html.escape(str(source_display))}<br>'
            f'逐答案 json_pointer：{html.escape(str(pointer_display))}<br>'
            f'证据：{html.escape(evidence)}</div></details>')


UNRESOLVED_PLAYER_LABELS = {
    "クリティカル発生率": "同句暴击率增幅仍未确定",
    "攻撃間隔（词表外）": "同句攻击间隔仍未确定",
    "回復（词表外）": "同句回复／状态恢复效果仍未确定",
    "HP回復": "同句 HP 回复效果仍未确定",
    "ダメージ（词表外）": "同句伤害相关效果仍未确定",
}


def unresolved_block(effect: dict):
    effect_id = effect["effect_id"]
    effect_type = effect.get("effect_type") or "未分类效果"
    label = UNRESOLVED_PLAYER_LABELS.get(effect_type, f"同句{effect_type}仍未确定")
    suffix = "#" + effect_id.rsplit("#", 1)[-1]
    evidence = effect["gap_evidence"]
    candidates = "；".join(str(x) for x in evidence.get("candidate_sources") or []) or "未单列"
    return (f'<details class="unresolved-effect" data-row-id="{html.escape(effect["description_ref"], quote=True)}" '
            f'data-effect-id="{html.escape(effect_id, quote=True)}"><summary>{html.escape(label)}'
            f' <code>{html.escape(suffix)}</code></summary><div class="value small">'
            f'原句片段：{html.escape(str(effect.get("snippet") or "未单列"))}'
            f'；span={html.escape(json.dumps(effect.get("span"), ensure_ascii=False))}'
            f'；状态：unresolved<br>'
            f'effect_id：<code>{html.escape(effect_id)}</code><br>'
            f'账本缺口：{html.escape(str(evidence.get("gap") or "未单列"))}<br>'
            f'阻断原因：{html.escape(str(evidence.get("blocker") or "未单列"))}<br>'
            f'候选证据：{html.escape(candidates)}<br>'
            f'下一步：{html.escape(str(evidence.get("next_step") or "未单列"))}<br>'
            f'证据来源：output/character_skills/effect_ledger/backlog.json；'
            f'backlog_id=<code>{html.escape(str(evidence.get("backlog_id") or effect_id))}</code></div></details>')


SPLIT_FLAG_LABELS = {
    "S3_uncovered_clauses": "同句有未被效果主张覆盖的子句",
    "S3b_residual_mechanisms": "同句含词表外机制词，未建立结构化覆盖",
}


def split_flag_block(flag: dict):
    """行级拆分待核查标志的默认中文披露；子句位置与账本口径留展开层。"""
    code = str(flag.get("code") or "未分类")
    label = SPLIT_FLAG_LABELS.get(code, f"同句仍未核查（{code}）")
    phrases = []
    seen = set()
    for item in flag.get("detail") or []:
        if not isinstance(item, dict):
            continue
        text = item.get("clause") or item.get("text") or item.get("word")
        idx = item.get("clause_index")
        key = (text, idx)
        if text and key not in seen:
            seen.add(key)
            phrases.append(str(text) + (f"（子句#{idx}）" if idx is not None else ""))
    seq = "；".join(phrases) or "未单列"
    return (f'<div class="unresolved-row small"><span class="badge unknown">同句未解</span> '
            f'{html.escape(label)}：{html.escape(seq)}'
            f'<details><summary>展开：子句位置、机制词与账本口径</summary><div class="value small">'
            f'行级拆分标志：<code>{html.escape(code)}</code><br>'
            f'原因口径：{html.escape(str(flag.get("reason") or "未单列"))}<br>'
            f'明细：{html.escape(json.dumps(flag.get("detail") or [], ensure_ascii=False))}<br>'
            f'来源：正式页当前行的 effect_ledger.analyze_row split_flags</div></details></div>')


def render_new_answers(cfg: dict, batch: dict, output_dir: Path):
    computed = new_answer_rows(cfg, batch)
    rows = []
    for item in computed["rows"]:
        cid = item["cid"]
        answers = "<br>".join(
            answer_block(ans, item, output_dir, cid,
                         use_player_text=cfg.get("use_player_text_default", False),
                         show_scope=cfg.get("show_player_scope_default", False),
                         condition_display=cfg.get("condition_display"))
            for ans in item["answers"])
        unknowns = "".join(unresolved_block(effect) for effect in item.get("unresolved_effects", []))
        if answers and unknowns:
            unknowns = "<br>" + unknowns
        split_html = "".join(split_flag_block(flag) for flag in item.get("row_split_flags") or [])
        if answers and split_html:
            split_html = "<br>" + split_html
        page_path = history_card_path(cid, cfg["history_run_tag"]) if cfg.get("history_run_tag") else PAGES / str(cid) / "card.json"
        href = relative_href(output_dir, str(page_path.relative_to(ROOT)))
        rows.append(
            f'<tr data-cid="{cid}"><td class="name"><a href="{href}">{html.escape(item["name"])}</a><br>'
            f'<span class="muted small">cid{cid}</span></td><td class="jp">{html.escape(item["japanese"])}</td>'
            f'<td class="small"><code>{html.escape(item["row_id"])}</code><br>'
            f'<span class="muted">{html.escape(str(item["stage"] or item["reference_field"] or ""))}</span></td>'
            f'<td>{answers}{split_html}{unknowns}</td></tr>')
    stats = computed["stats"]
    stat_text = [f"{stats['rows']} 行 / {stats['cards']} 卡",
                 f"新增答案：Y.G. {stats['yg_answers']}／非 Y.G. {stats['non_yg_answers']}",
                 f"效果净增：Y.G. {stats['yg_effect_net']}／非 Y.G. {stats['non_yg_effect_net']}",
                 f"完整增量：Y.G. {stats['yg_complete_net']:+d}／非 Y.G. {stats['non_yg_complete_net']:+d}",
                 f"S4 {stats['s4_after']}",
                 f"unresolved {stats['before_unresolved']}→{stats['after_unresolved']}"]
    if cfg.get("split_effect_answer_summary"):
        stat_text.insert(0, f"效果净增 {stats['effect_net']}／答案新增 {stats['answers']}（不同口径，分列）")
    return {"html": "".join(rows), "stat_text": stat_text, "computed": computed}


def render_index(cycle_id: str, cfg: dict, metrics: dict, output_dir: Path):
    batches = []
    computed_all = []
    for batch in cfg["batches"]:
        rows = []
        if batch.get("binding"):
            rendered = render_new_answers(cfg, batch, output_dir)
            rows.append(rendered["html"])
            batch["computed_stats"] = rendered["stat_text"]
            computed_all.append(rendered["computed"])
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
    split_panel = ""
    if cfg.get("split_effect_answer_summary") and computed_all:
        effects_total = sum(item["stats"]["effect_net"] for item in computed_all)
        answers_total = sum(item["stats"]["answers"] for item in computed_all)
        rows_total = sum(item["stats"]["rows"] for item in computed_all)
        cards_total = len({row["cid"] for item in computed_all for row in item["rows"]})
        split_rows = [row for item in computed_all for row in item["rows"] if row.get("row_split_flags")]
        split_flag_total = sum(len(row["row_split_flags"]) for row in split_rows)
        disclosed_effects = sum(len(row.get("unresolved_effects") or [])
                                for item in computed_all for row in item["rows"])
        disclosure_note = ("本批目标行没有其它效果级未解项" if disclosed_effects == 0 else
                           "同句其它效果级未解仍就地披露，不计入本批净增")
        split_panel = f'''<section class="panel"><h2>本批规模：效果与答案分列</h2>
<div class="grid">
<div class="metric"><b>{effects_total}</b>{html.escape(cfg.get("effect_label", "效果"))}净增（行内效果，不是答案条数）</div>
<div class="metric"><b>{answers_total}</b>新增答案（同一效果的多档分支各计一条答案）</div>
<div class="metric"><b>{rows_total} 行 / {cards_total} 卡</b>归属变化的行与卡（并集）</div>
<div class="metric"><b>{len(split_rows)} 行 / {split_flag_total} 项</b>同句未解（行级拆分标志，默认披露）</div>
</div>
<p class="small">{html.escape(cfg.get("split_panel_note", "效果与答案不是同一口径，不合并成一个数汇报。"))}同句未解在效果级为 {disclosed_effects} 项（{disclosure_note}），其余未解内容以行级拆分标志在每行默认列出，展开可见子句位置与口径。</p>
</section>'''
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
    elif cycle_id == "C14":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0</span></p>
<p>15卡26行73答案／73效果净增，Y.G.22／同域非Y.G.51，完整+0、部分+1、S4 0；全库生成仅一次，final_diff 31/31、只读验证29/29、隔离27卡54文件一致。推断、局部公式、denju非首段与浏览器／实机未测边界保留；第三方方向审查待用户安排，C15不启动。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{task_href}">C14交付任务卡</a></p></section>'''
    elif cycle_id == "C15":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0</span></p>
<p>5卡6行6答案／6效果净增，全部Y.G.；完整／部分／未解析／拆分待核查增量均0，A+1／C−1、S4 0。全库生成仅一次，final_diff 36/36、只读验证32/32、隔离17卡34文件一致。另有4张C14-P2信息性指纹工件差异卡，不计C15收益，其余2,227卡逐字节不变。关联推断、局部公式与第三方浏览器／实机未测边界保留；P2/P3未启动，第三方方向审查待用户安排，C16不启动。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{task_href}">C15交付任务卡</a></p></section>'''
    elif cycle_id == "C16":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0</span></p>
<p>23卡23行49答案／49效果净增，Y.G.23／同域非Y.G.26；完整+23、未解析−23，A/C/整行推断/S4均0。全库生成仅一次，final_diff 36/36、只读验证30/30、隔离35卡70文件一致。另有9张既有page_sha256信息性指纹漂移卡，不计C16收益，其余2,205卡逐字节不变。关联推断、局部贡献与第三方浏览器／实机未测边界保留；P2/P3未启动，第三方方向审查待用户安排，C17不启动。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{task_href}">C16交付任务卡</a></p></section>'''
    elif cycle_id == "C17":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0</span></p>
<p>3卡3行3答案／3效果净增，全部Y.G.；完整+3、未解析−3，A/C/整行推断/S4均0。全库生成仅一次，final_diff 36/36、只读验证31/31、隔离16卡32文件一致。另有9张既有page_sha256信息性指纹漂移卡，不计C17收益，其余2,224卡逐字节不变。额外param6与句外条件强化不并入，关联推断、局部贡献与第三方浏览器／实机未测边界保留；P2/P3未启动，第三方方向审查待用户安排，C18不启动。</p>
<p class="small warning">终审N01–N08保留：交接旧状态由收口更新；冻结模块文档头的“未接线”为候选时历史原文；首次构建后中断缺独立机器回执；指纹值指构建时输入页而非构建后正式页；展开层conditions保留能力编号，默认player_text无内部术语；隔离目录48文件中32个card.json/index.html参与比较；目标行旧unknown_reasons未刷新属既有展示遗留；生成器曾预写审查徽章，现已在终审完成后以verdict无阻断为生成闸门重建。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{task_href}">C17交付任务卡</a></p></section>'''
    elif cycle_id == "C18":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0</span></p>
<p>2卡2行2答案／2效果净增，全部非Y.G.；完整+2、未解析−2，Y.G./A/C/整行推断/S4均0。全库生成仅一次且未resume，final_diff 36/36、只读验证32/32、隔离18卡36文件一致。另有9张既有page_sha256信息性指纹漂移卡，不计C18收益，其余2,225卡逐字节不变。额外param6与句外条件强化不并入，关联推断、局部贡献与第三方浏览器／实机未测边界保留；P2/P3未启动，与C17联合第三方方向审查待安排，C19不启动。</p>
<p class="small warning">终审与候选N01–N05保留：候选answers_total为序列化长度、run_record基线空值、父层／跨槽1095负例、候选K12同解析器及未使用常量均已登记；本包以独立重导和当前metrics为准。两行完整度不等于语义确认，展开层conditions含能力编号；Y.G. backlog因本批全部非Y.G.而保持8,511，未误写为8,509。C17历史成果不变，两周期联合审查尚未执行。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{task_href}">C18交付任务卡</a></p></section>'''
    elif cycle_id == "C19_R01":
        review_href = relative_href(output_dir, cfg["direction_review"])
        task_href = relative_href(output_dir, cfg["rectification_task"])
        final_href = relative_href(output_dir, cfg["delivery_review"])
        original_href = relative_href(output_dir, cfg["original_cycle_report"])
        third_party = f'''<section class="panel"><h2>第三方R01整改与停止点</h2>
<p><span class="badge unknown">原第三方 REQUEST_CHANGES（R01）</span> <span class="badge infer">R01整改完成，待原第三方定向复核</span></p>
<p>本版只在35条对应成果行就地补出同句45个未解效果；默认摘要说明具体未知项，展开保留effect_id、原句片段及正式账本缺口证据。133行407条既有答案、来源、条件、推断等级、统计及4行既有split_flags不变，不新增语义答案。</p>
<p class="small warning">R02：617.3秒仅为run_formal.py总运行时间，正式生成为133.24秒，不称为整个周期。R03：12个同号记录存在原始表示差异，其中11个实质值差、1个仅float32表示差（CID20713／42071301）；全部P1仍只取CACHE。第三方浏览器UNTESTED，主持实际浏览器项目另见回执。</p>
<p class="links small"><a href="{review_href}">原第三方REQUEST_CHANGES</a><a href="{task_href}">R01整改任务卡</a><a href="{final_href}">旧正式独立终审</a><a href="{original_href}">原C19成果前像</a></p></section>'''
    elif cycle_id == "C19":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0</span></p>
<p>133卡133行407答案／407效果净增，Y.G.52／非Y.G.355；完整+95、部分+34、未解析−129，A/C/整行推断/S4均0。全库生成仅一次且未resume，final_diff 36/36、只读验证32/32、隔离24卡48文件一致。绝对变化并集139卡（133目标∪9漂移，交集3），其余2,097卡逐字节不变。关联推断、局部贡献与第三方浏览器／实机未测边界保留；P3未启动，第三方方向审查待用户安排，C20不启动。</p>
<p class="small warning">候选N01–N05保留：45个其他effect未解、4行既有split_flags未新增、12个APK同名不同值只取CACHE、type8既有quantity_kind回退。终审F1文档哈希已同步为当前run_prechecks.py；F2并集139（7250／30107／30220同时是目标与漂移），不写成142。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{task_href}">C19交付任务卡</a></p></section>'''
    elif cycle_id == "C20_R02":
        review_href = relative_href(output_dir, cfg["direction_review"])
        task_href = relative_href(output_dir, cfg["rectification_task"])
        final_href = relative_href(output_dir, cfg["delivery_review"])
        original_href = relative_href(output_dir, cfg["original_cycle_report"])
        third_party = f'''<section class="panel"><h2>原Sol F01父标记整改与停止点</h2>
<p><span class="badge unknown">原Sol REQUEST_CHANGES（F01 OPEN）</span> <span class="badge infer">父标记整改完成，待原Sol再次定向复验</span></p>
<p>R01已补齐25份完整父集合、6项合并和2项排除；原Sol复验380项中373项通过，剩余7条答案的父标记语义问题由本版处理。本版把描述来源行父明确标为“当前描述来源父”，把binding.selected对应父明确标为“本答案分支父”；两者相同时同时标注。</p>
<p class="small warning">7条反例按同一数据规则修复，其余18条保留同父双标记。完整父集合顺序、原始条件、children、合并／排除字段和理由不变；16卡18行18效果25答案及正式pages／rules／effect_ledger不改。N01不纳入，浏览器、新原生与实机继续UNTESTED。</p>
<p class="links small"><a href="{review_href}">原Sol F01复验</a><a href="{task_href}">R02整改任务卡</a><a href="{final_href}">旧正式独立终审</a><a href="{original_href}">C20-R01历史成果</a></p></section>'''
    elif cycle_id == "C20_R01":
        review_href = relative_href(output_dir, cfg["direction_review"])
        task_href = relative_href(output_dir, cfg["rectification_task"])
        final_href = relative_href(output_dir, cfg["delivery_review"])
        original_href = relative_href(output_dir, cfg["original_cycle_report"])
        third_party = f'''<section class="panel"><h2>原Sol F01整改与停止点</h2>
<p><span class="badge unknown">原Sol REQUEST_CHANGES（F01）</span> <span class="badge infer">展示整改完成，待原Sol定向复验</span></p>
<p>本版只在25条答案的展开层补齐完整父引用顺序、原始条件、子记录，以及具体合并／排除分支的pattern、record、raw、来源指针和理由。16卡18行18效果25答案及既有数值、条件、证据等级不变；15行21项行级拆分机制继续默认披露。</p>
<p class="small warning">原审查349项中348项通过，唯一阻断为展示F01；25条答案的独立重导和真实消费者检查已通过。本版不修改正式pages／rules／effect_ledger，不运行正式生成或resume。N01为非阻断且不纳入本轮。浏览器、新原生执行与实机继续UNTESTED，静态HTML解析不冒充视觉验收。</p>
<p class="links small"><a href="{review_href}">原Sol REQUEST_CHANGES</a><a href="{task_href}">F01整改任务卡</a><a href="{final_href}">旧正式独立终审</a><a href="{original_href}">原C20冻结成果</a></p></section>'''
    elif cycle_id == "C20":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        candidate_href = relative_href(output_dir, cfg["candidate_review"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立终审 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0（27/27 通过）</span></p>
<p>16卡18行、18个伤害效果净增、25条答案新增（P1 9卡10答案／P2 7卡15答案），效果与答案分列不合并。账本有答案效果 21505→21523（+18）、未解 48160→48142（−18）、backlog −18；四档 完整+3／部分+0／未解析−3／拆分待核查+0；Y.G. 有答案 +10、非Y.G. +8；整行推断与拆分新增均 0，0 新规则键。正式全库生成仅一次（重算 111.16 秒），账本自检、固定检查、最后差异、回归与 24 卡 48 文件隔离复跑全部通过。</p>
<p class="small warning">范围限制（保留、不改写）：句面到记录的关联全部为推断，未做运行时验证；未做实机验证与新原生执行，不写最终扣血／保证命中／运行时装载。数值证据为"确认"只指原值与既有规则体。HP整数百分比、Chain、控制器使用阶段、森林次数上限、职业法珠／废料计数及界面缓存时点仍是运行时未证事项。20332自身受伤与另一类效果另论；其它记录、denju、回复、增益、异常、周期攻击及句外强化不并入。增强档按原表精度保留，不按玩家文案四舍五入。9张既有卡的页面指纹变化只重算该信息性字段，不计本批语义收益；成立的是本批目标卡与指纹漂移卡并集之外逐字节不变。第三方方向审查未做。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{candidate_href}">候选独立审查</a><a href="{task_href}">C20交付任务卡</a></p></section>'''
    elif cycle_id == "C21_R01":
        review_href = relative_href(output_dir, cfg["direction_review"])
        task_href = relative_href(output_dir, cfg["rectification_task"])
        final_href = relative_href(output_dir, cfg["delivery_review"])
        original_href = relative_href(output_dir, cfg["original_cycle_report"])
        third_party = f'''<section class="panel"><h2>原第三方F01／F02整改与停止点</h2>
<p><span class="badge unknown">原第三方 REQUEST_CHANGES（F01／F02）</span> <span class="badge infer">展示整改完成，待原第三方定向复验</span></p>
<p>本版只整改默认条件表达与展开证据：F01共70条／51卡（40条使用次数、6条地形、24条法珠相关），F02共19条／15卡，合计89条／66卡。使用次数、地形、法珠与Chain均按本答案selected分支重导；法珠原文事实与扣费前后／选档未知分开，内部Chain计数转换为玩家档位。</p>
<p class="small warning">900条机器答案、raw、来源、父集合、账本和正式pages不变；原C21成果、manifest与原第三方裁决保留。新增89条condition_ledger及逐条展开raw证据，0值特殊无Chain路径和完整选档未验证继续披露。浏览器、新原生与实机UNTESTED；主持不自行关闭F01／F02。</p>
<p class="links small"><a href="condition_ledger.json">89条条件台账</a><a href="condition_ledger.csv">条件台账CSV</a><a href="{review_href}">原第三方REQUEST_CHANGES</a><a href="{task_href}">R01整改任务卡</a><a href="{final_href}">原正式独立终审</a><a href="{original_href}">原C21冻结成果</a></p></section>'''
    elif cycle_id == "C21":
        review_href = relative_href(output_dir, cfg["delivery_review"])
        task_href = relative_href(output_dir, cfg["delivery_task"])
        third_party = f'''<section class="panel"><h2>正式独立审查与停止点</h2>
<p><span class="badge pass">正式独立终审 PASS_WITH_EXPLICIT_SCOPE_LIMITS</span> <span class="badge infer">阻断 0（23/23；900项独立重导）</span></p>
<p>518卡900行、900个伤害效果净增、900条答案新增：P1 766，P2 134；Y.G. 11／非Y.G. 889；严格直接899项＋CID30304首句条件镜像1项。has_answer +900／unresolved −900／backlog −900；完整+56／部分+1／未解析−57；A+502／C−502／整行推断+0／S4+0。900答案不等于900行或518卡全部解释完成，其它同句未解效果4项继续就地披露。</p>
<p>全库正式生成仅一次（jobs4），verify_full 17/17、账本9/9、A7 29/29、final_diff 36/36、validate_formal 26/26；固定cohort隔离复跑525卡1050文件逐字节一致，不称任意分组复现。默认层只显示可读的局部贡献和必要条件；公式、raw、表名、字段、指针、完整父集合与条件镜像证据在展开层。</p>
<p class="small warning">关联均为推断、runtime_verified=False；局部伤害输入不等于最终扣血、保证命中或运行时装载，未做新原生或实机。交付包部分历史检查名／说明残留C20“16卡／18行”字样，实际集合断言与独立终审均为518卡900行；原始回执不追溯改写，收口勘误承接。第三方方向审查PENDING；浏览器UNTESTED，不启动C22、清理、Git或发布。</p>
<p class="links small"><a href="{review_href}">正式独立终审</a><a href="{task_href}">C21交付任务卡</a></p></section>'''
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(cfg['title'])}</title><style>{CSS}</style></head>
<body><header><h1>{html.escape(cfg['title'])}</h1><p>数据库样式｜本周期新增解析成果（由正式页面与账本生成）</p>
<p>campaign <code>{cfg['campaign']}</code></p><p>snapshot <code>{cfg['snapshot']}</code>　rules {html.escape(cfg['rules'])}</p></header>
<main><section class="panel"><h2>周期末总览</h2><div class="grid">{cards}</div>
<p class="small">计数口径：有答案／未解为效果级；完整／部分／未解析／拆分为描述行级；Y.G. 为 109 张优先卡子集，均非全游戏分母。绝对出数、绑定修正、披露-only、split 状态整理分列，不合并成一个收益数。</p>
<p class="links"><a href="remaining.html">查看预计剩余工程量 →</a></p></section>
{split_panel}
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


def disclosure_summary(cfg: dict, batch_results: list):
    """统计默认层披露的同句未解内容：效果级未解项与行级拆分标志。"""
    rows = [row for result in batch_results for row in result["rows"]]
    flags = [flag for row in rows for flag in (row.get("row_split_flags") or [])]
    return {
        "effect_level_unresolved_effects": sum(len(row.get("unresolved_effects") or []) for row in rows),
        "rows_with_effect_level_unresolved": sum(1 for row in rows if row.get("unresolved_effects")),
        "row_split_flag_rows": sum(1 for row in rows if row.get("row_split_flags")),
        "row_split_flags": len(flags),
        "split_flag_codes": sorted({str(flag.get("code")) for flag in flags}),
        "default_visible": True,
        "formal_answers_changed": False,
        "formal_pages_or_ledger_regenerated": False,
    }


def write_c21_answer_ledger(output_dir: Path, batch_results: list, condition_display: str | None = None):
    """Write one auditable ledger entry per C21 answer from the real before/after diff."""
    entries = []
    for result in batch_results:
        for row in result["rows"]:
            for answer in row["answers"]:
                binding = c21_binding(answer)
                source = answer.get("source") or {}
                entries.append({
                    "batch": result["stats"]["id"],
                    "cid": row["cid"], "row_id": row["row_id"], "effect_id": binding.get("effect_id"),
                    "model": binding.get("model"), "scope": binding.get("scope"),
                    "value": answer.get("value"), "player_text": answer.get("player_text"),
                    "display_player_text": (c21_r01_default_player_text(answer, str(answer.get("player_text") or ""))
                                             if condition_display == "C21_R01" else
                                             c21_default_player_text(answer, str(answer.get("player_text") or ""))),
                    "quantity_kind": answer.get("quantity_kind"), "unit": answer.get("unit"),
                    "raw_value": answer.get("raw_value"), "effective_float32": answer.get("effective_float32"),
                    "normalized_value": answer.get("normalized_value"), "target": answer.get("target"),
                    "condition_label": answer.get("condition_label"), "conditions": answer.get("conditions"),
                    "display_conditions": (c21_r01_condition_projection(
                        answer, list((answer.get("player_scope") or {}).get("conditions") or []))["conditions"]
                        if condition_display == "C21_R01" else c21_default_conditions(
                            answer, list((answer.get("player_scope") or {}).get("conditions") or []))),
                    "numeric_evidence": answer.get("numeric_evidence"),
                    "association_evidence": answer.get("association_evidence"),
                    "answer_status": answer.get("answer_status"), "evidence_scope": answer.get("evidence_scope"),
                    "binding": binding.get("binding"), "runtime_verified": binding.get("runtime_verified"),
                    "rule_key": answer.get("rule_key"), "field_path": answer.get("field_path"),
                    "table": answer.get("table"), "record_id": answer.get("record_id"),
                    "layer": answer.get("layer"), "source": source,
                    "current_parent": binding.get("current_parent"), "selected": binding.get("selected"),
                    "complete_parent_set": binding.get("complete_parent_set"),
                    "fragment_span": binding.get("fragment_span"), "denju": binding.get("denju"),
                    "mirror": binding.get("mirror"), "effect_binding": answer.get("effect_binding"),
                })
    if len(entries) != 900 or len({entry["effect_id"] for entry in entries}) != 900:
        raise ValueError(f"C21答案台账应为900个不同效果，实际{len(entries)}")
    (output_dir / "answer_ledger.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    columns = ["batch", "cid", "row_id", "effect_id", "model", "layer", "table", "record_id",
               "rule_key", "field_path", "raw_value", "effective_float32", "normalized_value", "unit",
               "target", "condition_label", "numeric_evidence", "association_evidence", "answer_status",
               "evidence_scope", "binding", "runtime_verified", "json_pointer", "raw_record_sha256",
               "current_parent", "selected", "complete_parent_set", "fragment_span", "mirror"]
    with (output_dir / "answer_ledger.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for entry in entries:
            row = {key: entry.get(key) for key in columns}
            row["json_pointer"] = (entry.get("source") or {}).get("json_pointer")
            row["raw_record_sha256"] = (entry.get("source") or {}).get("raw_record_sha256")
            for key in ("current_parent", "selected", "complete_parent_set", "fragment_span", "mirror"):
                row[key] = compact_json(row.get(key))
            writer.writerow(row)
    return entries


def c21_r01_condition_entries(batch_results: list):
    entries = []
    for result in batch_results:
        for row in result["rows"]:
            for answer in row["answers"]:
                projection = c21_r01_condition_projection(
                    answer, list((answer.get("player_scope") or {}).get("conditions") or []))
                kinds = projection["kinds"]
                if not kinds:
                    continue
                selected = c21_binding(answer).get("selected") or {}
                entries.append({
                    "finding": "F02" if kinds == ["chain"] else "F01",
                    "cid": row["cid"], "row_id": row["row_id"], "effect_id": c21_binding(answer).get("effect_id"),
                    "record_id": answer.get("record_id"), "pattern_id": selected.get("pattern_id"),
                    "layer": answer.get("layer"), "kinds": kinds,
                    "raw_chain_range": projection["chain"], "raw_conditions": projection["raw"],
                    "context_text": projection["raw"].get("sinfo"),
                    "display_necessary_conditions": projection["necessary"],
                    "display_conditions": projection["conditions"],
                    "mana_known": projection["mana_known"], "mana_unknown": projection["mana_unknown"],
                    "selected": selected, "source": answer.get("source") or {},
                    "formal_answer_unchanged": True,
                    "runtime_verified": False,
                })
    if (len(entries) != 89 or len({entry["cid"] for entry in entries}) != 66
            or sum("limit" in entry["kinds"] for entry in entries) != 40
            or sum("terrain" in entry["kinds"] for entry in entries) != 6
            or sum("mana" in entry["kinds"] for entry in entries) != 24
            or sum("chain" in entry["kinds"] for entry in entries) != 19):
        raise ValueError("C21_R01条件台账未精确覆盖89条／66卡及40/6/24/19分组")
    return entries


def write_c21_r01_condition_ledger(output_dir: Path, batch_results: list):
    entries = c21_r01_condition_entries(batch_results)
    (output_dir / "condition_ledger.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    columns = ["finding", "cid", "row_id", "effect_id", "record_id", "pattern_id", "layer",
               "kinds", "raw_chain_range", "raw_conditions", "context_text",
               "display_necessary_conditions", "display_conditions", "mana_known", "mana_unknown",
               "formal_answer_unchanged", "runtime_verified"]
    with (output_dir / "condition_ledger.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for entry in entries:
            row = {key: entry.get(key) for key in columns}
            for key in ("kinds", "raw_chain_range", "raw_conditions", "display_necessary_conditions",
                        "display_conditions", "mana_known", "mana_unknown"):
                row[key] = compact_json(row.get(key))
            writer.writerow(row)
    return entries


def generation_record(cycle_id: str, cfg: dict, metrics: dict, output_dir: Path,
                      batch_results: list, remaining: list, unique_pairs: set, before_pairs: set):
    outputs = {}
    for name in ("index.html", "remaining.html", "report_data.json", "README.md", "verification.json",
                 "browser_verification.json", "answer_ledger.json", "answer_ledger.csv",
                 "condition_ledger.json", "condition_ledger.csv"):
        path = output_dir / name
        if path.is_file():
            outputs[name] = {"bytes": path.stat().st_size, "sha256": file_sha(path)}
    metrics_path = ROOT / cfg["metrics_path"] if cfg.get("metrics_path") else LEDGER / "metrics.json"
    record = {
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
        "third_party_verdict": ("REQUEST_CHANGES（F01／F02；原裁决未改）" if cycle_id == "C21_R01"
                                else "REQUEST_CHANGES（F01父标记语义；原Sol裁决未改）" if cycle_id == "C20_R02"
                                else "REQUEST_CHANGES（F01；原Sol裁决未改）" if cycle_id == "C20_R01"
                                else "REQUEST_CHANGES（R01；原裁决未改）" if cycle_id == "C19_R01"
                                else "PASS_WITH_EXPLICIT_SCOPE_LIMITS（F1 manifest/handoff 已补齐，待原第三方定向复核）" if cycle_id == "C20"
                                else "PENDING（待用户安排第三方方向审查）" if cycle_id in ("C13", "C14", "C15", "C16", "C17", "C18", "C19", "C21")
                                else "REQUEST_CHANGES（R01/R02；原裁决未改）"),
        "rectification_status": ("F01／F02展示整改完成，待原第三方定向复验" if cycle_id == "C21_R01"
                                 else "F01父标记整改完成，待原Sol再次定向复验" if cycle_id == "C20_R02"
                                 else "F01展示整改完成，待原Sol定向复验" if cycle_id == "C20_R01"
                                 else "R01整改完成，待原第三方定向复核" if cycle_id == "C19_R01"
                                 else "第三方方向复核已完成；F1 manifest/handoff 已补齐，待原第三方定向复核" if cycle_id == "C20"
                                 else "正式交付与例行独立审查完成，待用户安排第三方方向审查" if cycle_id in ("C13", "C14", "C15", "C16", "C17", "C18", "C19", "C21")
                                 else "整改完成，待原第三方定向复查"),
    }
    if cfg.get("rectification_display") == "R01":
        record["inputs"]["direction_review"] = cfg["direction_review"]
        record["inputs"]["original_cycle_report"] = cfg["original_cycle_report"]
        record["display_rectification"] = {
            "finding": "R01",
            "affected_rows": 35,
            "affected_effects": 45,
            "formal_answers_changed": False,
            "formal_pages_or_ledger_regenerated": False,
            "status": "IMPLEMENTED_PENDING_ORIGINAL_THIRD_PARTY_RECHECK",
        }
    if cfg.get("rectification_display") == "F01":
        record["inputs"]["direction_review"] = cfg["direction_review"]
        record["inputs"]["original_cycle_report"] = cfg["original_cycle_report"]
        record["display_rectification"] = {
            "finding": "F01",
            "affected_answers": (7 if cfg.get("rectification_stage") == "PARENT_MARKER" else 25),
            "rectification_stage": cfg.get("rectification_stage") or "EXPANDED_DISCLOSURE",
            "complete_parent_sets": 25,
            "merged_disclosures": sum(len((answer.get("binding") or {}).get(key, {}).get("merged_disclosures") or [])
                                      for result in batch_results for row in result["rows"] for answer in row["answers"]
                                      for key in ("c20_p1_yg_direct_damage_binding", "c20_p2_nonyg_direct_damage_binding")),
            "excluded_branch_values": sum(len((answer.get("binding") or {}).get(key, {}).get("excluded_branch_values") or [])
                                          for result in batch_results for row in result["rows"] for answer in row["answers"]
                                          for key in ("c20_p1_yg_direct_damage_binding", "c20_p2_nonyg_direct_damage_binding")),
            "formal_answers_changed": False,
            "formal_pages_or_ledger_regenerated": False,
            "status": "IMPLEMENTED_PENDING_ORIGINAL_SOL_RECHECK",
        }
    if cfg.get("disclose_row_split_flags"):
        record["display_disclosure"] = disclosure_summary(cfg, batch_results)
        if cfg.get("delivery_review"):
            record["inputs"]["delivery_review"] = cfg["delivery_review"]
        if cfg.get("candidate_review"):
            record["inputs"]["candidate_review"] = cfg["candidate_review"]
    if cfg.get("rectification_c21_conditions"):
        record["inputs"]["direction_review"] = cfg["direction_review"]
        record["inputs"]["original_cycle_report"] = cfg["original_cycle_report"]
        record["display_rectification"] = {
            "findings": ["F01", "F02"], "affected_answers": 89, "affected_cards": 66,
            "f01_answers": 70, "f02_answers": 19,
            "condition_ledger": "condition_ledger.json",
            "formal_answers_changed": False,
            "formal_pages_or_ledger_regenerated": False,
            "status": "IMPLEMENTED_PENDING_ORIGINAL_THIRD_PARTY_RECHECK",
        }
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle", required=True, choices=sorted(CYCLES))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.output.is_absolute():
        args.output = (ROOT / args.output).resolve()
    cfg = CYCLES[args.cycle]
    if args.cycle in ("C17", "C18", "C19", "C19_R01", "C20", "C20_R01", "C20_R02", "C21", "C21_R01"):
        final_review = load_json(ROOT / cfg["delivery_review"].replace("REPORT.md", "verdict.json"))
        blocking = final_review.get("blocking")
        if isinstance(blocking, list):
            blocking_count = len(blocking)
        else:
            blocking_count = final_review.get("blocking_count", blocking if blocking is not None else -1)
        if final_review.get("verdict") != "PASS_WITH_EXPLICIT_SCOPE_LIMITS" or blocking_count != 0:
            raise SystemExit(f"{args.cycle} 正式独立终审未无阻断通过；不生成成果页")
    metrics = metrics_summary(cfg)
    if metrics["snapshot"] != cfg["snapshot"]:
        raise SystemExit(f"账本 snapshot {metrics['snapshot']} 与周期声明 {cfg['snapshot']} 不一致；请先更新生成器配置")
    args.output.mkdir(parents=True, exist_ok=True)
    if args.cycle in ("C20_R01", "C20_R02"):
        placeholders = {
            "browser_verification.json": {
                "status": "UNTESTED", "browser": "UNTESTED",
                "reason": "本轮未启动浏览器做桌面／窄屏实际渲染；只有静态HTML解析和链接存在性检查。",
                "static_verification": "verification_detailed.json（PENDING）",
                "runtime_verified": False,
                "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            },
            "verification_detailed.json": {"cycle": args.cycle, "finding": "F01", "status": "PENDING"},
            "expanded_display_audit.json": {"cycle": args.cycle, "finding": "F01", "status": "PENDING"},
        }
        if args.cycle == "C20_R02":
            placeholders["answer_ledger.json"] = {"cycle": args.cycle, "finding": "F01", "status": "PENDING"}
        for name, value in placeholders.items():
            path = args.output / name
            if not path.exists():
                path.write_text(json.dumps(value, ensure_ascii=False, indent=1, allow_nan=False) + "\n", encoding="utf-8")
        if args.cycle == "C20_R02" and not (args.output / "answer_ledger.csv").exists():
            (args.output / "answer_ledger.csv").write_text("status\nPENDING\n", encoding="utf-8")
    if cfg.get("rectification_c21_conditions"):
        placeholders = {
            "browser_verification.json": {
                "status": "UNTESTED", "browser": "UNTESTED",
                "reason": "本轮未启动浏览器做桌面／窄屏实际渲染；只有静态HTML解析和链接存在性检查。",
                "static_verification": "verification_detailed.json（PENDING）",
                "runtime_verified": False,
                "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            },
            "verification_detailed.json": {"cycle": args.cycle, "findings": ["F01", "F02"], "status": "PENDING"},
        }
        for name, value in placeholders.items():
            path = args.output / name
            if not path.exists():
                path.write_text(json.dumps(value, ensure_ascii=False, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    (args.output / "index.html").write_text(render_index(args.cycle, cfg, metrics, args.output), encoding="utf-8")
    (args.output / "remaining.html").write_text(render_remaining(args.cycle, cfg, metrics), encoding="utf-8")
    groups, split_count = remaining_groups(cfg)
    batch_results = [new_answer_rows(cfg, batch) for batch in cfg["batches"] if batch.get("binding")]
    if args.cycle in ("C21", "C21_R01"):
        write_c21_answer_ledger(args.output, batch_results, cfg.get("condition_display"))
    if cfg.get("rectification_c21_conditions"):
        write_c21_r01_condition_ledger(args.output, batch_results)
    before_tag = "20261030T203110" if args.cycle == "C11" else "20261031T015918" if args.cycle in ("C12", "C13") else None
    before_pairs = all_answer_pairs(before_tag) if args.cycle in ("C11", "C12", "C13") else set()
    unique_pairs = new_answer_pairs(cfg) - before_pairs if args.cycle in ("C11", "C12", "C13") else set()
    data = {"cycle": args.cycle, "campaign": cfg["campaign"], "snapshot": cfg["snapshot"], "rules": cfg["rules"],
            "metrics": metrics, "batches": cfg["batches"], "batch_results": batch_results,
            "remaining_by_type": groups, "split_check_rows": split_count,
            "new_rule_value_pairs": sorted(unique_pairs),
            "before_rule_value_pair_count": len(before_pairs)}
    if cfg.get("rectification_c21_conditions"):
        condition_entries = c21_r01_condition_entries(batch_results)
        data["display_rectification"] = {
            "findings": ["F01", "F02"],
            "original_direction_review": cfg["direction_review"],
            "original_cycle_report": cfg["original_cycle_report"],
            "status": "IMPLEMENTED_PENDING_ORIGINAL_THIRD_PARTY_RECHECK",
            "affected_answers": 89, "affected_cards": 66,
            "f01_answers": 70, "f01_cards": 51,
            "f01_direct_answers": 46, "f01_direct_cards": 34,
            "limit_answers": 40, "terrain_answers": 6, "mana_answers": 24,
            "f02_answers": 19, "f02_cards": 15,
            "condition_ledger": "condition_ledger.json",
            "formal_answers_changed": False,
            "formal_pages_or_ledger_regenerated": False,
            "original_third_party_recheck": "PENDING",
        }
    if cfg.get("rectification_display") == "R01":
        unresolved_rows = [item for result in batch_results for item in result["rows"]
                           if item.get("unresolved_effects")]
        data["display_rectification"] = {
            "finding": "R01",
            "original_direction_review": cfg["direction_review"],
            "original_cycle_report": cfg["original_cycle_report"],
            "status": "IMPLEMENTED_PENDING_ORIGINAL_THIRD_PARTY_RECHECK",
            "affected_rows": len(unresolved_rows),
            "affected_effects": sum(len(item["unresolved_effects"]) for item in unresolved_rows),
            "formal_answers_changed": False,
            "formal_pages_or_ledger_regenerated": False,
            "r02_timing_wording": "617.3秒仅为run_formal.py总运行时间；正式生成为133.24秒，不是整个C19周期。",
            "r03_source_wording": "12个同号记录存在原始表示差异，其中11个实质值差、1个仅float32表示差（CID20713／42071301）；只取CACHE。",
        }
    if cfg.get("rectification_display") == "F01":
        data["display_rectification"] = {
            "finding": "F01",
            "original_direction_review": cfg["direction_review"],
            "original_cycle_report": cfg["original_cycle_report"],
            "status": "IMPLEMENTED_PENDING_ORIGINAL_SOL_RECHECK",
            "affected_answers": (7 if cfg.get("rectification_stage") == "PARENT_MARKER" else 25),
            "rectification_stage": cfg.get("rectification_stage") or "EXPANDED_DISCLOSURE",
            "complete_parent_sets": 25,
            "merged_disclosures": sum(len((answer.get("binding") or {}).get(key, {}).get("merged_disclosures") or [])
                                      for result in batch_results for row in result["rows"] for answer in row["answers"]
                                      for key in ("c20_p1_yg_direct_damage_binding", "c20_p2_nonyg_direct_damage_binding")),
            "excluded_branch_values": sum(len((answer.get("binding") or {}).get(key, {}).get("excluded_branch_values") or [])
                                          for result in batch_results for row in result["rows"] for answer in row["answers"]
                                          for key in ("c20_p1_yg_direct_damage_binding", "c20_p2_nonyg_direct_damage_binding")),
            "formal_answers_changed": False,
            "formal_pages_or_ledger_regenerated": False,
            "n01_in_scope": False,
        }
    disclosure = None
    if cfg.get("disclose_row_split_flags"):
        disclosure = disclosure_summary(cfg, batch_results)
        data["display_disclosure"] = disclosure
    (args.output / "report_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    checks = {
        "snapshot_matches": metrics["snapshot"] == cfg["snapshot"],
        "new_answer_rows_generated": all(result["stats"]["rows"] > 0 for result in batch_results),
        "remaining_unresolved_matches_metrics": sum(g["all"] for g in groups) == metrics["unresolved"]["all"],
        "remaining_yg_matches_metrics": sum(g["yg"] for g in groups) == metrics["unresolved"]["yg"],
        "backlog_matches_metrics": sum(g["all"] for g in groups) + split_count == metrics["backlog"],
        "unique_pairs_expected": len(unique_pairs) == (8 if args.cycle == "C11" else 2 if args.cycle == "C13" else 0) if args.cycle in ("C11", "C12", "C13") else True,
    }
    if cfg.get("rectification_c21_conditions"):
        condition_entries = c21_r01_condition_entries(batch_results)
        checks["c21_r01_condition_inventory_89_66"] = (
            len(condition_entries) == 89 and len({entry["cid"] for entry in condition_entries}) == 66)
        checks["c21_r01_f01_inventory_70_51"] = (
            sum(entry["finding"] == "F01" for entry in condition_entries) == 70
            and len({entry["cid"] for entry in condition_entries if entry["finding"] == "F01"}) == 51)
        checks["c21_r01_f02_inventory_19_15"] = (
            sum(entry["finding"] == "F02" for entry in condition_entries) == 19
            and len({entry["cid"] for entry in condition_entries if entry["finding"] == "F02"}) == 15)
        checks["c21_r01_condition_kinds_40_6_24_19"] = (
            sum("limit" in entry["kinds"] for entry in condition_entries) == 40
            and sum("terrain" in entry["kinds"] for entry in condition_entries) == 6
            and sum("mana" in entry["kinds"] for entry in condition_entries) == 24
            and sum("chain" in entry["kinds"] for entry in condition_entries) == 19)
    if cfg.get("rectification_display") == "R01":
        checks["row_unresolved_mapping_35_45"] = (
            data["display_rectification"]["affected_rows"] == 35
            and data["display_rectification"]["affected_effects"] == 45
        )
    if cfg.get("rectification_display") == "F01":
        f01_answers = [answer for result in batch_results for row in result["rows"] for answer in row["answers"]]
        f01_bindings = [next(value for value in (answer.get("binding") or {}).values()
                             if isinstance(value, dict) and "complete_parent_set" in value)
                        for answer in f01_answers]
        checks["f01_complete_parent_sets_25"] = (
            len(f01_answers) == len(f01_bindings) == 25
            and all(binding["complete_parent_set"] for binding in f01_bindings))
        checks["f01_branch_counts_match"] = (
            sum(len(binding.get("merged_disclosures") or []) for binding in f01_bindings) == 6
            and sum(len(binding.get("excluded_branch_values") or []) for binding in f01_bindings) == 2)
        if cfg.get("rectification_stage") == "PARENT_MARKER":
            def parent_identity(parent):
                return parent.get("reference_field"), parent.get("pattern_id")
            differences = 0
            identities_ok = True
            for binding in f01_bindings:
                parents = [parent_identity(parent) for parent in binding["complete_parent_set"]]
                source = parent_identity(binding["current_parent"])
                selected = parent_identity(binding["selected"])
                differences += source != selected
                identities_ok &= parents.count(source) == 1 and parents.count(selected) == 1
            checks["parent_marker_identities_25_and_7_differences"] = differences == 7 and identities_ok
    if cfg.get("expected_totals"):
        exp = cfg["expected_totals"]
        by_batch = {result["stats"]["id"]: result for result in batch_results}
        totals = {
            "rows": sum(result["stats"]["rows"] for result in batch_results),
            "cards": len({item["cid"] for result in batch_results for item in result["rows"]}),
            "answers": sum(result["stats"]["answers"] for result in batch_results),
            "effects": sum(result["stats"]["effect_net"] for result in batch_results),
            "yg_answers": sum(result["stats"]["yg_answers"] for result in batch_results),
            "non_yg_answers": sum(result["stats"]["non_yg_answers"] for result in batch_results),
            "yg_effects": sum(result["stats"]["yg_effect_net"] for result in batch_results),
            "non_yg_effects": sum(result["stats"]["non_yg_effect_net"] for result in batch_results),
        }
        totals_check_key = ("c20_expected_totals_match" if args.cycle.startswith("C20")
                            else f"{args.cycle.lower()}_expected_totals_match")
        checks[totals_check_key] = all(
            totals[key] == exp[key] for key in ("rows", "cards", "answers", "effects",
                                                "yg_answers", "non_yg_answers",
                                                "yg_effects", "non_yg_effects"))
        stat_key_map = {"rows": "rows", "answers": "answers", "effects": "effect_net"}
        for batch_key in ("p1", "p2"):
            batch_id = f"{cfg.get('expected_batch_prefix', args.cycle)}-{batch_key.upper()}"
            stats = by_batch.get(batch_id, {}).get("stats")
            expected = exp.get(batch_key) or {}
            checks[f"expected_{batch_key}_match"] = bool(stats) and all(
                stats[stat_key_map[key]] == value
                for key, value in expected.items() if key in stat_key_map)
            checks[f"expected_{batch_key}_cards_match"] = bool(stats) and stats["cards"] == expected.get("cards")
        if exp["effects"] != exp["answers"]:
            checks["effects_and_answers_counted_separately"] = (
                totals["effects"] != totals["answers"]
                and any(len(item["answers"]) > 1 for result in batch_results for item in result["rows"]))
        else:
            checks["effects_and_answers_counted_separately"] = (
                totals["effects"] == exp["effects"] and totals["answers"] == exp["answers"]
                and all(len(item["answers"]) == 1 for result in batch_results for item in result["rows"]))
    verification = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
                    "metrics": metrics, "batch_results": batch_results,
                    "new_rule_value_pairs": sorted(unique_pairs),
                    "before_rule_value_pair_count": len(before_pairs)}
    if disclosure is not None:
        verification["display_disclosure"] = disclosure
    if cfg.get("expected_totals"):
        verification["expected_totals"] = cfg["expected_totals"]
        verification["observed_totals"] = totals
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
    elif args.cycle == "C14":
        status_text = "正式交付与正式独立终审完成，待用户安排第三方方向审查"
        verdict_text = "正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断 0"
        review_links = (f"- [C14交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})")
        generation_note = "C14 使用当前正式页面与账本及首建前像。未再次运行正式全库生成；正式生成与固定检查已在交付包内完成，P3未启动。"
        limits_note = "P1数值归属为推断，p9为受伤量倍率、仅Skill型着弹；P2为局部伤害输入公式，denju非首段6行保持未知。25行仍拆分待核查，1行未解析转部分，完整+0；浏览器／实机未测。"
    elif args.cycle == "C15":
        status_text = "正式交付与正式独立终审完成，待用户安排第三方方向审查"
        verdict_text = "正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断 0"
        review_links = (f"- [C15交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})")
        generation_note = "C15 使用当前正式页面与账本及首建前像。未再次运行正式全库生成；正式生成与固定检查已在交付包内完成，P2/P3未启动。"
        limits_note = "6行仍拆分待核查，完整／部分／未解析／拆分增量均0，A+1／C−1；数值规则体确认不等于句→记录关联确认，关联保持推断。仅写局部伤害输入公式，不写最终扣血、保证命中、运行时选档或实机结果。另有4张C14-P2信息性指纹工件差异卡，不计C15收益，其余2,227卡逐字节不变。主持侧浏览器实际覆盖与超时项见回执；第三方浏览器与实机未测。"
    elif args.cycle == "C16":
        status_text = "正式交付与正式独立终审完成，待用户安排第三方方向审查"
        verdict_text = "正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断 0"
        review_links = (f"- [C16交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})")
        generation_note = "C16 使用当前正式页面与账本及首建前像。未再次运行正式全库生成；正式生成与固定检查已在交付包内完成，P2/P3未启动。"
        limits_note = "完整+23、未解析−23，A/C/整行推断/S4均0；数值规则体确认不等于句→1095字段归属确认，关联保持推断。答案仅为接受者自身已装载且资格／列表／类型分派通过时的单一载体局部贡献，不含其他来源、后续条件强化或最终叠加值。另有9张既有page_sha256信息性指纹漂移卡，不计C16收益，其余2,205卡逐字节不变。主持侧浏览器实际覆盖与超时项见回执；第三方浏览器与实机未测。"
    elif args.cycle == "C17":
        status_text = "正式交付与正式独立终审完成，待用户安排第三方方向审查"
        verdict_text = "正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断 0"
        review_links = (f"- [C17交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})")
        generation_note = "C17 使用当前正式页面与账本及首建前像。未再次运行正式全库生成；正式生成与固定检查已在交付包内完成，P2/P3未启动。"
        limits_note = "完整+3、未解析−3，A/C/整行推断/S4均0；数值规则体确认不等于句→1095字段归属确认，关联保持推断。仅认领三个攻击效果，额外param6与句外条件强化不并入；最终叠加与实机未验证。另有9张既有page_sha256信息性指纹漂移卡，不计C17收益，其余2,224卡逐字节不变；指纹指构建时输入页。终审N01–N08保留：交接旧状态由收口更新，冻结模块候选时文档头不改，首次构建后中断缺独立机器回执，展开层conditions含能力编号但默认player_text无内部术语，隔离目录48文件中32个card.json/index.html参与比较，目标行旧unknown_reasons未刷新属既有展示遗留；生成器曾预写徽章，现已在终审完成后以verdict无阻断为闸门重建。主持侧浏览器实际覆盖与未测项见回执；第三方浏览器与实机未测。"
    elif args.cycle == "C18":
        status_text = "正式交付与正式独立终审完成，待与C17联合第三方方向审查"
        verdict_text = "正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断 0"
        review_links = (f"- [C18交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})")
        generation_note = "C18 使用当前正式页面与账本及首建前像。未再次运行正式全库生成；正式生成仅一次且未resume，P2/P3未启动。"
        limits_note = "完整+2、未解析−2，Y.G./A/C/整行推断/S4均0；数值规则体确认不等于句→1095字段归属确认，关联保持推断。仅认领两个非Y.G.攻击效果，额外param6与句外条件强化不并入；最终叠加与实机未验证。另有9张既有page_sha256信息性指纹漂移卡，不计C18收益，其余2,225卡逐字节不变；指纹指构建时输入页。候选N01–N05及父层／跨槽1095未知保留；两行完整度不等于语义确认。Y.G. backlog保持8,511。C17历史成果不变，联合第三方审查尚未执行；主持侧浏览器实际覆盖与未测项见回执，第三方浏览器与实机未测。"
    elif args.cycle == "C19_R01":
        status_text = "R01整改完成，待原第三方定向复核"
        verdict_text = "原第三方REQUEST_CHANGES（R01）保留；主持未改写为PASS"
        review_links = (f"- [原第三方REQUEST_CHANGES]({relative_href(args.output, cfg['direction_review'])})\n"
                        f"- [R01整改任务卡]({relative_href(args.output, cfg['rectification_task'])})\n"
                        f"- [旧正式独立终审]({relative_href(args.output, cfg['delivery_review'])})\n"
                        f"- [原C19成果前像]({relative_href(args.output, cfg['original_cycle_report'])})")
        generation_note = "C19-R01只使用同版本正式页面与账本重建成果展示。未运行正式全库生成、run_formal.py、resume或隔离卡页生成，未修改正式pages／ledger／rules；原C19目录和原第三方裁决保留。"
        limits_note = "本版仅将35行45个同句未解效果补入默认阅读层，展开保留effect_id与正式backlog缺口证据。133行407条既有答案、来源、条件、推断等级、统计和4行既有split_flags不变，新增语义答案0。R02正确口径为run_formal.py总运行617.3秒、正式生成133.24秒，不是整个周期；R03为12个同号记录原始表示差异＝11个实质值差＋1个仅float32表示差（CID20713／42071301），CACHE答案不变。第三方浏览器UNTESTED，主持实际浏览器项目见回执；停在待原第三方定向复核。"
    elif args.cycle == "C19":
        status_text = "正式交付与正式独立终审完成，待第三方方向审查"
        verdict_text = "正式独立审查 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断 0"
        review_links = (f"- [C19交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})")
        generation_note = "C19 使用当前正式页面与账本及首建前像。未再次运行正式全库生成；正式生成仅一次且未resume，P3未启动。"
        limits_note = "133卡133行407答案／407效果净增，Y.G.52／非Y.G.355；完整+95、部分+34、未解析−129，A/C/整行推断/S4均0。数值规则体确认不等于句→载体字段归属确认，关联保持推断。缺param5不补零，额外param6与句外条件强化不并入；130行仍有45个其他effect未解，4行既有split_flags未新增。绝对变化并集139卡（交集7250／30107／30220），其余2,097卡逐字节不变；终审F1文档哈希已同步、F2不写成142。候选N01–N05保留；12个APK同名不同值只取CACHE，type8既有quantity_kind回退。C17/C18历史成果不变，第三方方向审查尚未执行；主持侧浏览器实际覆盖与未测项见回执，第三方浏览器与实机未测。"
    elif args.cycle == "C20_R02":
        status_text = "F01父标记整改完成，待原Sol再次定向复验"
        verdict_text = "原Sol REQUEST_CHANGES（F01 OPEN）保留；本版未改写原裁决"
        review_links = (f"- [原Sol F01复验]({relative_href(args.output, cfg['direction_review'])})\n"
                        f"- [R02整改任务卡]({relative_href(args.output, cfg['rectification_task'])})\n"
                        f"- [旧正式独立终审]({relative_href(args.output, cfg['delivery_review'])})\n"
                        f"- [C20-R01历史成果]({relative_href(args.output, cfg['original_cycle_report'])})")
        generation_note = "C20-R02只修正展开层父标记：current_parent标为当前描述来源父，selected对应父标为本答案分支父；两者相同时同时标注。未修改机器答案、binding、正式pages／ledger／rules，不运行正式生成或resume；C20-R01及原Sol复验保留。"
        limits_note = "本版统一处理25答案，7条来源父与分支父不同的反例逐项闭合，其余18条同父双标记。16卡18行18个伤害效果净增、25条答案及全部父集合、6项合并、2项排除不变；15行21项行级拆分继续默认披露。N01不纳入，浏览器、新原生与实机UNTESTED。停在待原Sol再次定向复验，不启动C21、清理、Git或发布。"
    elif args.cycle == "C20_R01":
        status_text = "F01展示整改完成，待原Sol定向复验"
        verdict_text = "原Sol REQUEST_CHANGES（F01）保留；本版未改写原裁决"
        review_links = (f"- [原Sol复审REQUEST_CHANGES]({relative_href(args.output, cfg['direction_review'])})\n"
                        f"- [F01整改任务卡]({relative_href(args.output, cfg['rectification_task'])})\n"
                        f"- [旧正式独立终审]({relative_href(args.output, cfg['delivery_review'])})\n"
                        f"- [原C20冻结成果]({relative_href(args.output, cfg['original_cycle_report'])})")
        generation_note = "C20-R01只使用同版本正式页面与账本重建成果展示，新增C20_R01配置及展开层父集合／分支披露。未运行正式全库生成、run_formal、corrective-rebuild、resume或隔离卡页生成，未修改正式pages／ledger／rules；原C20目录和原Sol裁决保留。"
        limits_note = "本版仅在25条答案的展开层补齐完整父引用顺序、原始条件、子记录与具体合并／排除分支。16卡18行18个伤害效果净增、25条答案新增及既有数值、条件、证据等级不变；15行21项行级拆分机制继续默认披露。N01非阻断且不纳入。关联推断、runtime_verified=False、未实机、未做新原生执行；浏览器UNTESTED，静态HTML解析不冒充视觉验收。停在待原Sol定向复验，不启动C21、清理、Git或发布。"
    elif args.cycle == "C20":
        status_text = "第三方方向复核已完成；F1 manifest/handoff 已补齐，待原第三方定向复核"
        verdict_text = "正式独立终审 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断 0（27/27）"
        review_links = (f"- [C20交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})\n"
                        f"- [候选独立审查]({relative_href(args.output, cfg['candidate_review'])})")
        generation_note = "C20 只用当前正式页面（campaign 754f04b6f552）、当前账本与交付包纠正性重建前像生成展示。未运行 run_formal、resume、第二次全库生成、隔离卡页生成或任何正式写入；未修改 pages／ledger／rules／交付包。"
        limits_note = "16卡18行、18个伤害效果净增、25条答案新增（P1 9卡10答案／P2 7卡15答案），效果与答案分列，不按同数口径汇报。默认层显示对象、局部量与必要条件；公式、原值、表名、字段、指针与排除项在展开层。同句未解：本批目标行没有其它效果级未解项（0 项），未解内容以行级拆分标志（未被覆盖的子句，如「弾き飛ばす」；词表外机制词，如「ダウン」「暗闇」「転倒」）在每行默认列出，展开可见子句位置与账本口径。关联全部为推断、未做运行时验证，未实机、未做新原生执行；不写最终扣血、保证命中或运行时装载。整行推断与拆分新增均 0；A +9／C −9（整行状态随效果出数移动，不是新增解释证据）；0 新规则键。9张既有卡的页面指纹变化只重算该信息性字段，不计本批收益；不宣称范围外卡逐字节不变。C19 及其 R01 成果与第三方裁决不变；第三方方向复核已完成，F1 manifest/handoff 已补齐，浏览器渲染与实机未测，待原第三方定向复核。"
    elif args.cycle == "C21_R01":
        status_text = "F01／F02展示整改完成，待原第三方定向复验"
        verdict_text = "原第三方REQUEST_CHANGES保留；本版未改写原裁决，F01／F02尚未关闭"
        review_links = (f"- [原第三方REQUEST_CHANGES]({relative_href(args.output, cfg['direction_review'])})\n"
                        f"- [R01整改任务卡]({relative_href(args.output, cfg['rectification_task'])})\n"
                        f"- [原正式独立终审]({relative_href(args.output, cfg['delivery_review'])})\n"
                        f"- [原C21冻结成果]({relative_href(args.output, cfg['original_cycle_report'])})")
        generation_note = "C21-R01只用当前正式页面、当前账本和pre_rebuild前像重建展示，新增89条条件台账与selected分支展开证据。未运行正式生成、resume、隔离卡页生成或账本生成；正式pages／rules／ledger／机器答案、原C21成果与原第三方审查均未修改。"
        limits_note = "518卡900行、900个伤害效果净增、900条答案新增不变。整改覆盖F01 70条／51卡（46条直接漏项＋24条法珠相关）与F02 19条／15卡，合计89条／66卡。40条limit=1显示本分支已使用次数小于1次；6条地形按原文显示；24条法珠逐项区分原文事实与扣费前后／计数对象／选档未知；19条Chain按玩家档位显示，0值特殊路径与完整选档未验证留展开层。900条答案、raw、来源、父集合、账本不变，其它811条不借入条件。浏览器UNTESTED，静态解析不冒充视觉验收；待原第三方定向复验，不启动C22、清理、Git或发布。"
    elif args.cycle == "C21":
        status_text = "正式交付与正式独立终审完成，待第三方方向审查"
        verdict_text = "正式独立终审 PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻断0（23/23；900项独立重导）"
        review_links = (f"- [C21交付任务卡]({relative_href(args.output, cfg['delivery_task'])})\n"
                        f"- [正式独立终审]({relative_href(args.output, cfg['delivery_review'])})\n"
                        f"- [审查入口路径修复]({relative_href(args.output, 'output/character_skills/review/c21_delivery_final_20261111_deepseek/REPAIR.md')})")
        generation_note = "C21只使用当前正式页面、当前账本和pre_rebuild前像生成展示及900答案台账。未运行run_formal、resume、第二次全库生成、隔离卡页生成或账本生成；正式pages／ledger／rules／交付包未修改。"
        limits_note = "518卡900行、900个伤害效果净增、900条答案新增（P1 766／P2 134；Y.G.11／非Y.G.889），严格直接899项＋CID30304首句条件镜像1项。900答案不等于900行或518卡全部解释完成；完整+56／部分+1／未解析−57，其它同句未解效果4项继续就地披露。默认层只显示可读的局部贡献和必要条件；完整日文、公式、raw、表名、字段、指针、父集合与镜像差异放展开层。关联推断、runtime_verified=False；未做新原生或实机，不写最终扣血、保证命中或运行时装载。固定cohort隔离525卡1050文件不称任意分组复现。交付包部分历史检查名／说明残留C20“16卡／18行”字样，实际集合断言与独立终审均为518卡900行；原始回执保留，由收口勘误承接。第三方方向审查PENDING，浏览器UNTESTED；不启动C22、清理、Git或发布。"
    else:
        status_text = "整改完成，待原第三方定向复查"
        verdict_text = "第三方原裁决 REQUEST_CHANGES（R01/R02）未改"
        review_links = (f"- [第三方原裁决]({report_url})\n"
                        f"- [第三方整改要求]({rectification_url})\n"
                        f"- [本轮整改任务卡]({task_url})")
        generation_note = "C11 使用 C12 run 中保存的 C11 前像与 C11 账本；C12 使用当前正式页面与账本。未运行正式全库生成或第二次全库生成，未修改正式 pages、rules 或正式账本。第三方统计仅作交叉核对，不是生产唯一输入。"
        limits_note = "数值关联保持推断；S3/S7、hint、放置条件、Boss 模式 pattern 选取、M→sub1 引擎装载、1059 人数比例与五人上限保持未知。历史待办不构成下一批授权，backlog 不是互斥的角色完成率。"
    if (args.output / "browser_verification.json").is_file():
        if args.cycle in ("C20", "C20_R01", "C20_R02", "C21", "C21_R01"):
            browser_line = "- `browser_verification.json`：UNTESTED（未启动浏览器做桌面／窄屏实际渲染）；静态 HTML 解析与链接存在性检查见 `verification_detailed.json`。"
        else:
            browser_line = "- `browser_verification.json`：真实浏览器桌面／窄屏阅读、答案展开和来源链接检查。"
    else:
        browser_line = "- 未生成 `browser_verification.json`：本轮未做真实浏览器渲染检查；静态 HTML 解析与链接存在性检查见 `verification_detailed.json`。"
    detailed_line = ("- `verification_detailed.json`：默认／展开分层、同句未解披露、链接与只读性的逐项对账。"
                     if (args.output / "verification_detailed.json").is_file() else "")
    expanded_audit_line = ("- `expanded_display_audit.json`：25条答案逐条展开文本、完整父集合及合并／排除字段对账。"
                           if (args.output / "expanded_display_audit.json").is_file() else "")
    ledger_answer_count = sum(len(item["answers"]) for result in batch_results for item in result["rows"])
    answer_ledger_line = (f"- `answer_ledger.json`／`answer_ledger.csv`：{ledger_answer_count}条答案的来源父、分支父及逐条验证台账。"
                          if (args.output / "answer_ledger.json").is_file()
                          and (args.output / "answer_ledger.csv").is_file() else "")
    condition_ledger_line = ("\n- `condition_ledger.json`／`condition_ledger.csv`：89条F01／F02答案的selected原始条件、玩家可读条件及法珠已知／未知台账。"
                             if (args.output / "condition_ledger.json").is_file()
                             and (args.output / "condition_ledger.csv").is_file() else "")
    manifest_line = ("- `final_manifest.json`：交付文件与 SHA-256 清单（不含自身和 handoff_verification.json）。\n"
                     "- `handoff_verification.json`：单向 final_manifest 哈希回执。")
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
{browser_line}
{detailed_line}
{expanded_audit_line}
{answer_ledger_line}{condition_ledger_line}
- `run_record.json`：生成器、真实输入、命令和输出清单。
{manifest_line}

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
