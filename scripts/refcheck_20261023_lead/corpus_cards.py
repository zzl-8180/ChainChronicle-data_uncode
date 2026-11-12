# -*- coding: utf-8 -*-
"""卡目录定位公共helper：新版1/新版2/旧版基线 卡名 -> data 目录。"""
import os

REF = r"E:\代码项目\锁链战记数据解包\其他人的参考"
BASES = {
    "new1": os.path.join(REF, "claude_cc_site_pages 20261023"),
    "new2": os.path.join(REF, "claude_cc_site_pages_给GPT_20261023", "claude_cc_site_pages"),
    "old":  os.path.join(REF, "claude_cc_site_pages"),
}


def card_dirs(base):
    """返回 {dir_name: full_path}。"""
    cd = os.path.join(base, "cards")
    out = {}
    for e in os.listdir(cd):
        p = os.path.join(cd, e)
        if os.path.isdir(p):
            out[e] = p
    return out


def parse_cid(dir_name):
    """'cid351《Y.G.1》...' -> '351'；按前导数字切分。"""
    s = dir_name
    if s.startswith("cid"):
        s = s[3:]
    i = 0
    while i < len(s) and s[i].isdigit():
        i += 1
    return s[:i] if i else None


def index_by_cid(base):
    idx = {}
    for d, p in card_dirs(base).items():
        cid = parse_cid(d)
        idx.setdefault(cid, []).append((d, p))
    return idx


def data_path(dir_path):
    """card 目录下的数据目录（快照统一的 'data'）。

    新版1/新版2/旧版都是 <card>/data/card.json。若不存在则回退到 <card>/card.json。
    """
    p = os.path.join(dir_path, "data")
    if os.path.isdir(p):
        return p
    if os.path.exists(os.path.join(dir_path, "card.json")):
        return dir_path
    return p
