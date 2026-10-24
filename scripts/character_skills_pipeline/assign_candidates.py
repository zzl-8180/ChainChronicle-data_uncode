# -*- coding: utf-8 -*-
"""Y.G. 优先清单 · 步骤3：官方队列选题视图的不相交候选归属＋通用模板（非 Y.G.）同形状收益。

DS-GR-02 修复（20261023 DeepSeek 整改审查）：本脚本原先读取 yg_remaining_rows.json
（coverage_refined 2,066 行 Y.G. 旧池），yg_candidates.json 停留在 2026-10-21——官方
backlog 未成为实际选题输入。现改为消费当前队列：

输入：
- work/character_skills_yg_priority/yg_backlog_view_enriched.json —— 步骤2 富化后的
  官方队列选题视图（P0 断点 ∪ Y.G.，源自当前 effect_ledger/backlog.json）；
- output/character_skills/effect_ledger/backlog.json —— 正式队列全集（78,427 项口径锚点；
  非视图项＝P2，作通用模板收益单列，不并入 Y.G. 进展）；
- work/character_skills_yg_priority/inventory_summary.json —— 步骤1 的官方队列构成
  （含富化池↔backlog 两个集合差的行数来源与去向口径）。

输出：yg_candidates.json（meta 带当前日期与 backlog 锚点）。
候选正则与优先级与上一版逐字相同（审查确认归属逻辑本身无缺陷，缺陷只在输入未接入）。
"""
import json, re, sys, io, os, collections, datetime, unicodedata, hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(ROOT)

# R3 线 B 整改（20261023）：正式选题产物（yg_candidates*.json）由主持整合时以本脚本
# 正常路径重建；本线验证运行用环境变量 R3B_OUT_DIR 把输出重定向到 scratch 目录
# （work/character_skills_r3_root_fix/scratch/），不触碰正式产物。默认＝脚本所在目录（正式）。
_OUT_DIR = os.environ.get('R3B_OUT_DIR') or os.path.join(ROOT, 'work', 'character_skills_yg_priority')

def norm_text(t):
    t = unicodedata.normalize('NFKC', t or '').strip()
    t = re.sub(r'[0-9]+', 'N', t)
    t = re.sub(r'(<[^<>]*>)|(＜[^＜＞]*＞)', '⟨X⟩', t)
    t = re.sub(r'(≪[^≪≫]*≫)', '⟨Y⟩', t)
    return t

enr = json.load(open('work/character_skills_yg_priority/yg_backlog_view_enriched.json', encoding='utf-8'))
items = enr['items']
summary = enr['summary']

# (候选ID, 值类型, Y.G.独有?, 行匹配正则（原始日文文本）)——与上一版逐字相同
CANDS = [
    ('YG2 共鳴アビリティ 3005/3006/3000 残部', '攻撃/回复（增益输入）＋时间', True, r'共鳴アビリティ'),
    ('YG1 共鳴必殺/超共鳴必殺（本体・Interval・バフ・回復）', '攻撃（倍率/Interval）＋时间', True, r'共鳴必殺'),
    ('YG3 反響範囲（cid 350 系）', '攻撃（一部伝播）＋条件', True, r'反響'),
    ('YG4 設置/戦闘不能・弾き飛ばし耐性装置', '时间＋生存（定性量化条件）', True, r'設置|戦闘不能'),
    ('YG5 遠距離弾速/貫通/盾破壊（job_ability 弓兵科）', '攻撃（威力/速度）', True, r'弾速|盾を破壊|貫通する'),
    ('YG6 時の楔/万象マナ', '回复（徐々回復）＋攻撃', True, r'時の楔|万象'),
    ('G1 必殺ダメージ骨格（大/中/小ダメージ・弾き飛ばし・状態異常付帯）', '攻撃（倍率）', False, r'ダメージを与え|ダメージを与える|の⟨ATTR⟩を下げ'),
    ('G2 敵デバフ（同時に攻撃した敵/攻撃時…下がる）', '减伤（敌攻防降）＋时间', False, r'(?:攻撃した敵|敵の[^。]{0,12}?(?:が|を)[^。、]{0,10}?(?:下がる|下がり|下げる|下げ、)|敵の(?:攻撃力|防御力|移動速度)が下が)'),
    ('G5 状態異常回復（同時に…回復系）', '回复（解除/量化）', False, r'状態異常'),
    ('G3 クリティカル吸収/クリ専用効果', '暴击＋回复', False, r'クリティカル攻撃時|クリティカル攻撃でダメージ|クリティカル攻撃が範囲'),
    ('G4 Chain 威力/Chain 数応効', '攻撃（倍率）', False, r'Chain'),
    ('G6 バリア（防御無視/炎氷/回数）', '减伤（バリア回数）', False, r'バリア'),
    ('G0 必殺技威力アップ族（et2/et1017・bossskill|2 规则在）', '攻撃（倍率）', False, r'必殺技の威力が上が|必殺技の威力が上がり|の必殺技の威力が上が'),
    ('G7 味方全体/戦場バフ残部（fam1 残＋条件バフ・超回復句）', '攻撃/减伤/暴击（增益输入）＋时间', False, r'味方全体|戦場にいる|味方の⟨ATTR⟩|⟨X⟩所属'),
    ('G8 サブパーティ在阵バフ', '攻撃/减伤（增益输入）', False, r'サブパーティ'),
    ('G9 自身バフ残部/条件バフ（1110 容器・WAVE/地形/マナ条件）', '攻撃/减伤/暴击＋时间', False, r'.'),
]
NONVAL = ('非数值候选 定性限定句', r'^(?:この効果はサブパーティでも発動する。|この効果は、サブパーティでも発動する。|自身が必殺技発動中に条件を満たした場合は発動しない。|発動中は移動と通常攻撃ができない。|移動すると元に戻る。)$')

# R3 整改（20261023 复审 §R3）：分类输入＝完整语境分层（子句→全句→行日文）＋目标效果
# （span 定位该效果自己的语境）＋技能类别（page_group/page_table 随项记录并聚合），
# 不再把效果片段（「攻撃力」等）单独交给旧句式分类器。多分类关系：一项效果可命中多个
# 候选——主分类按 CANDS 优先序取首个命中（YG 专项先于通用残部，G9 捕获为末位兜底），
# 其余命中记入 also_candidates（单列 also_items 计数，**不重复计入 items**——闭包
# sum(items)==视图项数保持，多分类关系在 also_* 与 meta.note 写明）。
#
# R3 复审整改第二轮（20261023 §R3b 语境不约束分类）：两级通道分离——
#   * 效果级局部机制（伤害/增益/屏障/反響等）：只在该效果**自己的**子句/全句里匹配
#     （效果项不再用行日文 'full' 级匹配——旧实现 full 级兜住一切，clause/sentence 置空
#     后 7,157 项主分类/also 变化为 0，语境形同摆设；复审实测）。split 项的行日文即其
#     自身范围，sentence 级照旧。
#   * 技能级专项标签（如【共鳴必殺/連撃】）：从 context_text 的【…】头部标记取得
#     （_skill_tags），只可记入（skill_tags 字段＋also_candidates），**不得覆盖目标效果
#     局部语境的归属**；仅当本效果局部语境无任何命中时才作为主分类（basis=skill_tag，
#     逐项注明局部未命中——此时技能级标签是仅有的可定位依据）。
#   * 主分类/附加分类每项带可定位依据：主分类=context_basis；附加分类=also_candidates
#     ＋also_basis（逐附加项的命中层级/标记来源）；闭包规则不变（items 按主分类恰一次）。
G9_ID = CANDS[-1][0] if CANDS[-1][0].startswith('G9') else next(
    c for c, *_ in CANDS if c.startswith('G9'))
_SKILL_TAG_CANDS = [(cid, pat) for cid, _vt, _yg, pat in CANDS
                    if cid.startswith('YG')]


def _skill_tags(context_text):
    """技能级专项标记：context_text 的【…】头部标记 → 命中的 YG 候选（逐项带标记原文）。
    只读【…】头（技能名级标记），不扫正文——正文词形属效果级局部语境，由局部通道判定。"""
    headers = ' '.join(re.findall(r'【([^】]+)】', context_text or ''))
    if not headers:
        return []
    out = []
    for cid, pat in _SKILL_TAG_CANDS:
        m = re.search(pat, headers)
        if m:
            out.append(dict(candidate=cid, marker=m.group(0),
                            source='context_text【…】技能级标记'))
    return out


# R3 第四轮整改（20261023 复验问题 R3-RESIDUAL-SENTENCE-SIBLING ＋ Medium
# R3-EFFECT-TYPE-NOOP）：候选适用性·效果类型/技能语境声明表——句式族 → 允许的
# effect_type 集合（types）与技能级语境（page_groups）。声明依据＝各候选**子句级命中**
# （命中词位于本效果自己的子句＝可信局部语境）的 effect_type 实测分布
# （yg_candidates_items.json clause-basis 逐项统计，20261023 实测）＋任务卡指定语义：
#   * G1 必殺ダメージ / G0 必殺技威力 → ダメージ/威力（词表外）/効果（任务卡例）；
#   * G5 状態異常回復 → 回復/状態異常族（効果（词表外）为状態異常付与・無効等容器类型；
#     継続時間为 clause 级实测 2 例的状態異常相关时长）；
#   * G2 敵デバフ → 攻撃/防御/移動/継続時間（clause 级 440 例仅此四类）；
#   * YG1 共鳴必殺 → 技能级 special_move 语境（page_groups；types 不限制——共鳴必殺
#     技文内效果类型覆盖全谱，clause 级实测 340 例含ダメージ/攻撃/防御/移動/時長/暴击/回復）；
#   * YG2 共鳴アビリティ → 技能级 sympathy 语境（clause 级 0 例；sentence/skill_tag
#     级实测全部在 sympathy）；
#   * 其余候选按 clause 级实测类型分布声明（G3 另含クリティカル発生率/威力两类型——
#     クリティカル族机制同源；G6 clause 级 71 例为ダメージ 69＋防御力 2）。
# 生效位置（本版整改）：**仅 sentence 回退路径的主分类选取与技能级标签主分类**（_et_ok）
# ——clause 路径不检查（子句是本效果自己的话，任务卡口径）；split 项全句即自身范围，
# 亦不检查。这闭合「空钩子」问题：表非空且实际参与 sentence 回退分类。
EFFECT_TYPE_LIMITS = {
    'G0': dict(types={'ダメージ（词表外）', '威力（词表外）', '効果（词表外）'},
               page_groups=None),
    'G1': dict(types={'ダメージ（词表外）', '威力（词表外）', '効果（词表外）'},
               page_groups=None),
    'G2': dict(types={'攻撃力', '防御力', '移動速度', '継続時間'}, page_groups=None),
    'G5': dict(types={'回復（词表外）', 'HP回復', '効果（词表外）', '継続時間'},
               page_groups=None),
    'G6': dict(types={'ダメージ（词表外）', '防御力'}, page_groups=None),
    'G3': dict(types={'クリティカル（発生率/威力未区分）', 'クリティカル発生率',
                      'クリティカル威力', 'ダメージ（词表外）'}, page_groups=None),
    'G4': dict(types={'威力（词表外）', '効果（词表外）'}, page_groups=None),
    'YG1': dict(types=None, page_groups={'special_move'}),
    'YG2': dict(types=None, page_groups={'sympathy'}),
    'YG3': dict(types={'威力（词表外）', '効果（词表外）', 'ダメージ（词表外）',
                       '回復（词表外）'}, page_groups=None),
    'YG4': dict(types={'攻撃力', '防御力', '継続時間', 'ダメージ（词表外）'},
                page_groups=None),
    'YG5': dict(types={'威力（词表外）'}, page_groups=None),
    'YG6': dict(types={'効果（词表外）'}, page_groups=None),
    # MANA＝必要マナ減り机制词族（R3F-30225-SHARED-MISLABEL 修复）：非候选族——仅用于
    # _unowned_sibling_check 兄弟机制判定（_et_ok 不受影响：无候选 ID 以 MANA 开头）。
    # 声明 types=∅＝该机制的子句从不承载任何效果类型的归属（独立技能级必要マナ减少），
    # 无 effect 记录动作子句含该词 → 未登记兄弟机制。
    'MANA': dict(types=set(), page_groups=None),
}


def _et_ok(cid, it):
    """候选适用性检查（R3 第四轮整改）：声明了 types 时要求效果 effect_type 在集合内；
    声明了 page_groups 时要求技能语境（page_group）在集合内；无声明＝不过滤。
    仅在 sentence 回退路径主分类选取与技能级标签主分类处调用——clause 路径不检查。"""
    lim = EFFECT_TYPE_LIMITS.get(cid.split(' ')[0])
    if not lim:
        return True  # 无声明＝不过滤（G7/G8/G9 残部类不声明）
    if lim.get('types') is not None and (it.get('effect_type') or '') not in lim['types']:
        return False
    pg = lim.get('page_groups')
    if pg is not None and (it.get('page_group') or '') not in pg:
        return False
    return True


# ---- R3 第四轮整改：机制词族表（只读复用，不改 effect_ledger）--------------------------
# 机制词 → 候选族：候选机制名词（CANDS 正则的机制词形）＋ effect_ledger.py 的机制词族
# 审计口径（_MECHANISM_WORD_FAMILY 的状態異常状态词组、防御・無効化機構词组——只读引用）。
# 仅用于「无 effect 记录子句」的兄弟机制判定（复验 Medium：489 合法共享中 ~90 实为
# 缺 effect 记录的兄弟机制，G5 47/YG4 18/YG5 12/YG3 10/G6 3）。
_MECH_FAMILY_WORDS = (
    ('YG1', ('共鳴必殺',)),
    ('YG2', ('共鳴アビリティ',)),
    ('YG3', ('反響',)),
    ('YG4', ('設置', '戦闘不能')),
    ('YG5', ('盾を破壊', '弾速', '貫通する')),
    ('YG6', ('時の楔', '万象')),
    ('G1', ('ダメージを与え',)),
    ('G2', ('攻撃した敵', '下がる', '下がり', '下げる', '下げ、')),
    ('G5', ('状態異常', '暗闇', '猛毒', '毒', '凍結', '転倒', 'スタン', 'ダウン',
            '眠り', '石化', '呪い', '魅了', '沈黙')),
    ('G3', ('クリティカル攻撃',)),
    ('G4', ('Chain',)),
    ('G6', ('バリア', '盾', 'シールド', 'ガード', '無効化', '軽減', '弱点')),
    ('G0', ('必殺技の威力',)),
    # R3F-30225-SHARED-MISLABEL 修复（20261024 DeepSeek 复验 Low）：必要マナ減り
    # （「1stChain以上で必殺技を発動する時に必要なマナが1つ減り」等 37 种句形）为独立
    # 技能级机制（必要マナ数减少），无对应候选族、无自有 effect 记录——不是共享条件
    # 句段；登记为词族＋空声明类型（EFFECT_TYPE_LIMITS['MANA'].types=∅），任何效果
    # 类型不兼容 → 无 effect 记录动作子句含该词＝未登记兄弟机制（降附加，候选保留）。
    ('MANA', ('必要なマナ', '必要マナ')),
)


# F1F2 补修（20261024 总指挥验收 阻塞A）：Chain 的序数阈值/达成触发语境
# （「1stChain以上で…」「2ndChainを達成した時」「Chainが3以上」等）是触发条件，
# 不是 G4 机制主张（Chain 威力/Chain 数応効——如「同じChain内で」「Chain数に応じて」
# 「Chainによる威力」）。与「属性防御力」负向断言同法：登记机制词时排除阈值语境。
_CHAIN_THRESHOLD_RE = re.compile(
    r'(?:\d+(?:st|nd|rd|th)|第\d+)Chain(?:以上|を達成|が\d|の数が)')


def _chain_threshold_at(text, i):
    """text 中第 i 位的 'Chain' 是否处于序数阈值/达成触发语境。"""
    seg = (text or '')[max(0, i - 8):i + 12]
    return bool(_CHAIN_THRESHOLD_RE.search(seg))


def _mech_words_of(text):
    """文本中出现的机制词→族列表（词面×族，去重保序）。
    F1F2 补修：Chain 仅在全部出现处均为序数阈值语境时不登记为 G4 机制词。"""
    out = []
    for fam, words in _MECH_FAMILY_WORDS:
        for w in words:
            if w not in (text or ''):
                continue
            if fam == 'G4' and w == 'Chain':
                occ = list(re.finditer(re.escape(w), text))
                if occ and all(_chain_threshold_at(text, m.start()) for m in occ):
                    continue
            out.append((w, fam))
    return out


# 命中词所在子句切分（与 effect_ledger/enrich 的子句切分同法：。、！？\n）
_KW_CLAUSE_RE = re.compile(r'[^。、！？\n]+')

_ROW_CLAUSE_OWNERS = None  # row_id -> {clause: [effect_id, ...]}（懒建，见下）


def _ensure_row_clause_owners():
    """兄弟子句归属判定数据源（R3 第四轮整改，问题 1）：账本**全部** effect 记录（含无
    待办效果）的 span→所在子句映射（line B 605 复查 review_605.py 的 join 机制同法：
    行 NFKC 文本按 _KW_CLAUSE_RE 切分，span 所在子句登记 effect_id；effect_id 即
    backlog effect 项的 backlog_id——enrich/assign 现行 join 口径）。"""
    global _ROW_CLAUSE_OWNERS
    if _ROW_CLAUSE_OWNERS is not None:
        return
    owners = {}
    _page_cache = {}

    def _row_ja(rid):
        try:
            cid = int(str(rid).split('-', 1)[0])
        except ValueError:
            return None
        if cid not in _page_cache:
            try:
                page = json.load(open('output/character_skills/pages/%d/card.json' % cid,
                                      encoding='utf-8'))
                _page_cache[cid] = {row['row_id']: row.get('japanese')
                                    for grp in page['groups']
                                    for sk in grp.get('skills', [])
                                    for row in sk.get('rows', [])}
            except (ValueError, FileNotFoundError):
                _page_cache[cid] = {}
        return _page_cache[cid].get(rid)

    with open('output/character_skills/effect_ledger/ledger.jsonl', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            if d.get('record_type') != 'effect':
                continue
            rid = d.get('description_ref')
            span = d.get('span')
            if not isinstance(rid, str) or not span:
                continue
            ja = _row_ja(rid)
            if not ja:
                continue
            text_n = unicodedata.normalize('NFKC', ja)
            if not (0 <= span[0] < span[1] <= len(text_n)):
                continue
            start, end = span
            for m in _KW_CLAUSE_RE.finditer(text_n):
                if m.start() <= start and end <= m.end():
                    owners.setdefault(rid, {}).setdefault(m.group(0), []).append(
                        d['effect_id'])
                    break
    _ROW_CLAUSE_OWNERS = owners


# 无 effect 记录子句的「技能级头/触发包装」形态（复验 r3_tallies2.py kind 判据同法）：
# 【…】头／≪…≫包装／以触发助词结尾的子句＝共享条件句段，机制词不作兄弟机制判据
# （如「【共鳴アビリティ】1stChain以上で…≪共鳴必殺≫を発動した時」的 Chain 是触发
# 条件不是 Chain 威力机制）；动作子句才做机制词族检查。
# N1 修复（20261024 原 Codex 最终复验 N1）：「際」与「時」同义触发词尾（際/際に/際は），
# 与「時」同等待遇——词尾命中后仍须过机制词族兼容检查，不等于一律共享。
_TRIGGER_TAIL_RE = re.compile(r'(たび|時|際[には]?|以上で|場合|中|条件|に応じて|ごとに)$')

# F2 修复（20261024 Codex 最终复审 F2）：技能级标记片段（【…】/≪…≫）剥离用正则——
# 标记存在不得使整段独立动作免检。
_MARKER_FRAG_RE = re.compile(r'【[^】]*】|≪[^≪]*≫')

# F1 修复（20261024 Codex 最终复审 F1）：条件形态收尾（肯定依据之一——条件/时机/范围
# 子句对全句各效果共同生效；含「いると/あると/とき」等条件形）。
# N1 修复（20261024 原 Codex 最终复验 N1）：增补「際」形态（際/際に/際は）——
# 与「時」同义的触发词尾；配对验证：仅把「攻撃した際」换成「攻撃した時」即恢复
# shared，证明遗漏在词尾表而非归属逻辑。机制词族兼容检查不变（含不兼容族机制词的
# 「際」子句仍拒绝共享）。
_COND_TAIL_RE = re.compile(r'(いると|あると|とき|時|際[には]?|たび|場合|以上で|に応じて|ごとに|中|条件|のみ|限り|なら)$')

# N2 修复（20261024 原 Codex 最终复验 N2）：无谓语修饰短语识别——
# 词表按全语料 undetermined 子句实测落地（890 事件/93 唯一子句逐条核对：
# work/character_skills_n1n2_fix_20261024/probe_undetermined.json 与 simulate_n2.py）。
# 含任一谓语形态即非「无谓语修饰语」——含完整独立动作的前段（F1 反例形态
# 「…した／…する＋顿号」）由本条件排除，不当作未完成对象短语。
_PREDICATE_RE = re.compile(
    r'(する|した|して|せず|しな|させ|される|できる|なる|なっ|なり|なら|ある|あり|あった'
    r'|いる|いた|上が|上げ|下が|下げ|与え|発動|回復|飛ば|獲得|倒|進む|進み|動く|動か|動き'
    r'|攻撃|開始|終了|受け|防ぐ|防ぎ|破壊|消費|付与|付加|無効|軽減|吸収|反射|追撃|迎撃'
    r'|復活|蘇生|貫通|超え|耐え|減る|減り|減ら|増え|増や|落ち|落と|延び|伸び|残る|残り'
    r'|続く|続い|含む|含み|持つ|持ち|かかる|かかり|消え|現れ|発生|変更|追加|除去|作成'
    r'|生じ|置く|置い|来る|来た|行く|行っ|負う|負い|派生|止ま|止め|早ま|早め|遅れ|切る'
    r'|切り|抜く|抜き|打つ|打ち|撃つ|撃ち|放つ|放ち|引く|引き|押す|押し|入る|入り|入れ'
    r'|出る|出し|取る|取り|取っ|使う|使い|使っ|用い|変わる|変わり|決まる|決まり|定め'
    r'|選ぶ|選び|及ぶ|及び|渡る|渡り|越え|通る|通り|抜ける|抜け|挟む|潜む|沈む|浮く'
    r'|寄せ|近づ|離れ|触れ|囲む|包む|張る|貼る|付く|付き|付け|着く|設け|設置|施す|施し'
    r'|整う|整え|備え|備わる|解除|解く|奪う|奪い|助け|救う|癒す|治す|直す|戻る|戻り'
    r'|戻っ|返す|返し|巡る|強ま|強め|弱ま|弱め|高ま|高め|低め|振る|撒く|巻く|応じ|伴う'
    r'|伴い|限り|限る|溜め|溜ま|貯め|貯ま|掛か|集め|集ま|分け|変え|装備|装着|狙う|狙い'
    r'|構え|走る|走り|言う|言い|話す|示す|記す|刻む|祈る|願う|望む|求め|舞う|死ぬ|生き'
    r'|逃げ|隠れ|燃や|燃え|凍る|溶け|砕く|散る|絶つ|断つ|立つ|立ち|立て|座る|伏せ|鳴る'
    r'|光る|撃破|唱え|掲げ)')
# 修饰语承接的对象标记与冲突目标阵营（对象切换不继承）。
_MOD_OBJ_RE = re.compile(r'を|が')
_ENEMY_TGT_RE = re.compile(r'敵|相手')
_ALLY_TGT_RE = re.compile(r'味方|仲間|自身|自分')

# L1 边界补修（20261024 总指挥 N1/N2 验收补充更正，唯一剩余阻塞）：显式对象覆盖——
# 区分「同属我方」与「对象相同」：自身不能仅因属我方阵营就继承前段全体对象短语。
# 「实体×属性」邻近搭配（实体＋全体/全員可选＋6 字内接属性词）视为显式对象；取子句中
# 最后一个搭配归类——「自身を含む味方全体のHPを…」归 ALLY（自身仅作从属修饰不构成
# 覆盖），「自身のHPのみを小回復する」归 SELF（显式覆盖）。任一方无搭配＝无显式对象
# 重述，不冲突（如 223 的「上限を超えて小回復する」）。
_OBJ_ATTR_RE = re.compile(
    r'(自身|自分|味方|仲間|敵|相手)(?:全体|全員)?[^、。]{0,6}?'
    r'(?:HP|攻撃力|防御力|移動速度|クリティカル発生率|クリティカル威力|魔力)')
_OBJ_CLASS = {'自身': 'SELF', '自分': 'SELF', '味方': 'ALLY', '仲間': 'ALLY',
              '敵': 'ENEMY', '相手': 'ENEMY'}


def _object_class(text):
    """文本的显式对象身份：SELF/ALLY/ENEMY/None（最后一个实体×属性搭配归所在类）。"""
    ent = None
    for _m in _OBJ_ATTR_RE.finditer(text or ''):
        ent = _m.group(1)
    return _OBJ_CLASS.get(ent) if ent else None


def _modifier_continuation(kwcl, it):
    """N2：无谓语的对象/时长修饰语对后接谓语的承接（共享肯定依据③）。
    「その後、味方全体のHPを一定時間、一定間隔ごとに上限を超えて小回復する。」中
    「味方全体のHPを一定時間」给出同一回复动作的对象与时长，并非独立兄弟机制。
    五条件全部满足才成立（任一不满足＝无肯定依据，不判非共享）：
      (a) 剥离技能级标记后含 を/が 对象标记——确为对象/主语修饰短语；
      (b) 剥离后无动作谓语（_PREDICATE_RE）——含完整独立动作的前段不当作
          未完成对象短语；
      (c) 句内紧邻 kwcl 的下一子句＝本效果自身子句——修饰语直接承接本效果谓语；
      (d) 自身子句不含与 kwcl 阵营相反的显式目标名词——敌我切换不继承；
      (e) 显式对象覆盖检查（_object_class）——双方均带显式对象且类不同（SELF/ALLY/
          ENEMY）→ 冲突：后段已明确限定「自身のHPのみ」等自身对象时，不凭前段全体
          对象短语建立承接；仅出现「自身」字样但不构成实体×属性搭配时不误拒绝。"""
    body = _MARKER_FRAG_RE.sub('', kwcl or '').strip('、。 　')
    if not body or not _MOD_OBJ_RE.search(body):
        return False
    if _PREDICATE_RE.search(body):
        return False
    sent = it.get('sentence') or ''
    own = (it.get('clause') or '').strip()
    if not own:
        return False
    clauses = [cm.group(0) for cm in _KW_CLAUSE_RE.finditer(sent)]
    try:
        idx = clauses.index((kwcl or '').strip())
    except ValueError:
        return False
    if idx + 1 >= len(clauses) or clauses[idx + 1].strip() != own:
        return False
    ke, ka = bool(_ENEMY_TGT_RE.search(body)), bool(_ALLY_TGT_RE.search(body))
    oe, oa = bool(_ENEMY_TGT_RE.search(own)), bool(_ALLY_TGT_RE.search(own))
    if (ke ^ ka) and (oe ^ oa) and ke != oe:
        return False
    kc, oc = _object_class(body), _object_class(own)
    if kc and oc and kc != oc:
        return False
    return True


def _shared_shape(kwcl):
    """共享形态判定（F2 修复版）：先剥离技能级标记片段（【…】/≪…≫）再判——
    纯标记头/触发包装（剥离后为空）仍豁免；触发/条件收尾且剥离后无机制词仍豁免；
    含动作/机制内容的子句不因标记存在而免检。"""
    c = kwcl or ''
    stripped = _MARKER_FRAG_RE.sub('', c).strip('、。 　')
    if not stripped:
        return True
    if _TRIGGER_TAIL_RE.search(stripped) and not _mech_words_of(stripped):
        return True
    return False


def _positive_shared_evidence(kwcl, it, mech):
    """F1：共享关系的肯定依据（无类型/机制冲突≠共享）。
    肯定依据三类：①纯条件/范围子句——条件形态收尾且无机制词（如「自身がサブパーティに
    いると」「戦場に味方がいる場合」，对全句各效果共同生效的范围/时机限定）；
    ②机制词族与本效果类型兼容（在 EFFECT_TYPE_LIMITS 声明内）且子句为条件形态
    （如「クリティカル攻撃時」「反響範囲内の敵を攻撃した際」对兼容效果——共享触发
    条件）；③（N2）无谓语对象/时长修饰语承接本效果谓语（_modifier_continuation——
    如「味方全体のHPを一定時間」承接后接的回复子句；机制词已在上游 flagged 检查
    排除冲突，此处不再复查）。
    仅在条件词尾不命中时尝试③——条件形态判定优先，两路径语义不相交。"""
    c = (kwcl or '').strip()
    if not _COND_TAIL_RE.search(c):
        return _modifier_continuation(kwcl, it)
    if not mech:
        return True
    et = it.get('effect_type') or ''
    for _w, fam in mech:
        lim = EFFECT_TYPE_LIMITS.get(fam)
        if lim and lim.get('types') is not None and et not in lim['types']:
            return False
    return True


def _unowned_sibling_check(cid, kwcl, it):
    """无 effect 记录子句的判定（复验 Medium 问题 2 判据＋Codex 最终复审 F1 修复）。
    形态先判：技能级头/触发包装/触发助词收尾（剥离标记后无机制词）→ 真共享。
    动作/陈述子句逐机制词判定：
      (i) 该族候选声明了 EFFECT_TYPE_LIMITS 且本效果 effect_type 不在声明内 → 兄弟机制；
      (ii) 该效果自身子句已含**另一族**机制词（本效果机制另有归属的正面证据）且该词
           族与自身子句族不同 → 兄弟机制。
    两者皆不成立时（F1）：**无冲突≠共享**——须肯定依据（_positive_shared_evidence：
    纯条件形态或族兼容＋条件形态）才算真共享；无依据 → 'undetermined'（归属无法确定，
    不作主分类、候选保留附加＋待定位理由）。
    返回 (verdict, mech_words, flagged)，verdict ∈ shared/sibling_unreg/undetermined。"""
    mech = _mech_words_of(kwcl or '')
    if _shared_shape(kwcl):
        return 'shared', mech, []
    flagged = []
    et = it.get('effect_type') or ''
    own_fams = {f for _w, f in _mech_words_of(it.get('clause') or '')}
    for w, fam in mech:
        lim = EFFECT_TYPE_LIMITS.get(fam)
        if lim and lim.get('types') is not None and et not in lim['types']:
            flagged.append('机制词「%s」属 %s 族（声明类型 %s，本效果类型「%s」不在内）'
                           % (w, fam, '、'.join(sorted(lim['types'])) or '（なし）',
                              et or '（无）'))
        elif own_fams - {fam}:
            flagged.append('机制词「%s」属 %s 族，与本效果自身子句的机制词族（%s）不同'
                           % (w, fam, '、'.join(sorted(own_fams - {fam}))))
    if flagged:
        return 'sibling_unreg', mech, flagged
    if not _positive_shared_evidence(kwcl, it, mech):
        return 'undetermined', mech, []
    return 'shared', mech, []


def _sentence_hit_info(cid, m, it):
    """全句命中词的子句归属判定（R3 第四轮整改，复验 High 问题 1＋Codex 最终复审 F1）：
      (a) 命中词所在子句＝本效果自身子句（span 重合）→ klass='own'——正常语境命中；
      (b) 同句另一效果的子句（账本 effect span join 有主、非本效果）→ klass='sibling'
          ——不得作主分类（兄弟效果机制）；
      (c) 不属任何 effect 子句 → 机制词族检查：与本效果类型不匹配 → klass='sibling_unreg'
          （账本无 effect 记录的兄弟机制，同样不得作主分类）；无冲突但有共享肯定依据
          （纯条件形态或族兼容＋条件形态）→ klass='shared'（合法共享可作主分类）；
          无冲突且无肯定依据 → klass='undetermined'（归属无法确定——不作主分类，
          候选保留附加＋待定位理由；F1：无冲突不证明共享）。"""
    sent = it.get('sentence') or ''
    kwcl = next((cm.group(0) for cm in _KW_CLAUSE_RE.finditer(sent)
                 if cm.start() <= m.start() and m.end() <= cm.end()), None)
    if kwcl is None:
        # 词形跨顿号（如 G2 的 [^。]{0,12} 可跨、）——取命中起点所在子句（span 重合判定）。
        # R3F-CROSS-CLAUSE-KWCL 修复（20261024 DeepSeek 复验 Medium）：子句按出现序递增，
        # 保留**最后一个** start<=命中起点 的子句（即命中起点所在子句）——旧实现 next()
        # 取的是句中首子句（如「その後」），与注释语义不符；owners/机制词族判定随正确
        # 子句生效。
        kwcl = None
        for cm in _KW_CLAUSE_RE.finditer(sent):
            if cm.start() <= m.start():
                kwcl = cm.group(0)
            else:
                break
    own = it.get('clause')
    if kwcl is not None and own is not None and kwcl == own:
        return dict(klass='own', kwcl=kwcl, owners=[], mech=_mech_words_of(kwcl))
    owners = []
    if kwcl is not None:
        _ensure_row_clause_owners()
        owners = [e for e in (_ROW_CLAUSE_OWNERS.get(it.get('row_id'), {}) or {})
                  .get(kwcl, []) if e != it.get('backlog_id')]
    if owners:
        return dict(klass='sibling', kwcl=kwcl, owners=owners, mech=_mech_words_of(kwcl))
    sib, mech, flagged = _unowned_sibling_check(cid, kwcl, it)
    if sib == 'sibling_unreg':
        return dict(klass='sibling_unreg', kwcl=kwcl, owners=[], mech=mech,
                    flagged=flagged)
    if sib == 'undetermined':
        return dict(klass='undetermined', kwcl=kwcl, owners=[], mech=mech)
    return dict(klass='shared', kwcl=kwcl, owners=[], mech=mech)


def _sibling_basis_text(info):
    """兄弟机制命中降附加时的 also_basis 文本（注明归属拒绝依据＋命中词子句原文）。"""
    kw = (info.get('kwcl') or '')[:48]
    if info['klass'] == 'sibling':
        return ('兄弟效果 ⟨%s⟩ 的机制，不作本效果归属依据（命中词位于同句兄弟效果子句'
                '「%s」）' % (','.join(info['owners']), kw))
    if info['klass'] == 'sibling_unreg':
        return ('同句未登记兄弟机制（该子句无 effect 记录但机制词族与本效果类型不匹配），'
                '不作本效果归属依据（命中词子句「%s」；%s）'
                % (kw, '；'.join(info.get('flagged') or []) or '机制词 %s'
                   % '、'.join('%s→%s' % (w, f) for w, f in info.get('mech') or [])))
    return None


def assign_item(it):
    """返回 (primary, basis_level, also_candidates, fallback_reason|None, skill_tags,
    also_basis)。also_basis＝逐附加分类的可定位依据（层级/技能标记来源/兄弟机制拒绝依据）。

    R3 第三轮整改（20261023 复审 §R3 根因，线 B）：命中分两层——
      * 第 1 层＝子句级：先收集全部 clause 命中，按 CANDS 优先序取首个为主分类；
      * 第 2 层＝全句级：仅当无任何子句命中时，才按 CANDS 序取首个全句命中为主分类；
        已有子句命中时，全句命中一律降为附加分类（also_candidates＋also_basis 注明层级）。
    旧实现先遍历 CANDS、再对每个候选依次找 clause/sentence 命中并取 matched[0]——只保证
    「单个候选内部子句优先」，不保证「本效果子句优先于别的候选的全句命中」：高优先级候选
    （G5 状態異常回復、YG2 共鳴アビリティ等）的全句命中压过当前效果自己的子句命中。
    真实反例 349-ability-ability-skillid_2_-lvorder1-f2#e00/e01/e02（攻撃/防御/时长，
    子句「味方全体の攻撃力と防御力が一定時間上がり」命中 G7）被同句后面的
    「全状態異常を回復する」以 G5 全句命中抢占主分类。技能级标签与共享条件不删除：
    skill_tags/also_candidates/also_basis 原样保留可定位依据。

    R3 第四轮整改（20261023 复验 High R3-RESIDUAL-SENTENCE-SIBLING ＋ Medium×2）：
    无子句命中时的全句回退**逐候选判定命中词所在子句的归属**（_sentence_hit_info）——
      (a) 命中词子句属当前效果自身（span 重合）→ 正常作主分类；
      (b) 属同句另一效果的子句（兄弟，账本 effect span join 有主）→ 不得作主分类：
          降为 also_candidates（also_basis 注明「兄弟效果 ⟨效应 ID⟩ 的机制，不作本
          效果归属依据」）；属无 effect 记录但机制词族与本效果类型不匹配的子句
          （未登记兄弟机制）同 (b) 处理；
      (c) 不属任何 effect 子句（技能级头【…】/≪…≫触发包装/共享条件句段）→ 合法共享，
          可作主分类（context_basis 仍为 sentence；逐项 sentence_fallback 字段与
          also_basis 注明依据）。
    且候选的 effect_type/技能语境声明（EFFECT_TYPE_LIMITS）在 sentence 回退路径主分类
    选取与技能级标签主分类处生效——不兼容的候选不得作主分类（clause 路径不检查：子句
    是本效果自己的话）。主分类按无命中路径顺延（skill_tag/G9 兜底＋具体理由）。"""
    ja = it.get('japanese') or ''
    if re.match(NONVAL[1], ja or ''):
        return NONVAL[0], 'full', [], None, [], []
    if it.get('kind') == 'effect':
        # 效果项：局部通道＝该效果自己的子句→全句（不再用行日文 full 级——多机制描述
        # 里其他句的机制词形不属于本效果，复审 §R3b 反例证明 full 级使语境失效）
        levels = (('clause', it.get('clause') or ''),
                  ('sentence', it.get('sentence') or ''))
    else:
        # split/其他项：行日文即本项自身范围（其目标就是整条描述）——全句即自身范围，
        # 无兄弟子句判定与 effect_type 限制问题
        levels = (('sentence', it.get('sentence') or ja),)
    # 逐候选求命中层级与命中位置：候选内部仍子句优先于全句（同一候选只记其最高层）；
    # effect_type 适用性不在匹配层过滤（仅约束 sentence 回退的主分类选取，见下）。
    hit_level, hit_match = {}, {}
    for cid, _vt, _yg, pat in CANDS:
        if cid.startswith('G9'):
            continue  # G9＝兜底，不参与专项命中（其正则 r'.' 匹配一切文本，无信息量）
        for lvl, txt in levels:
            if not txt:
                continue
            m = re.search(pat, txt)
            if m:
                hit_level[cid] = lvl
                hit_match[cid] = m
                break
    _order = {cid: i for i, (cid, *_r) in enumerate(CANDS)}
    # 分层收集：clause 命中与 sentence 命中各自按 CANDS 序排列（两集合不相交——
    # 每个候选只记最高层）
    clause_matched = sorted((c for c, l in hit_level.items() if l == 'clause'),
                            key=_order.get)
    sentence_matched = sorted((c for c, l in hit_level.items() if l == 'sentence'),
                              key=_order.get)
    stags = _skill_tags(it.get('context_text'))
    if clause_matched:
        # 第 1 层：子句命中为主分类（CANDS 序取首个）。全句命中降为附加（第 2 层）；
        # 技能级标签只记入不覆盖；全句上下文与共享条件保留在 also_candidates/also_basis。
        # R3 第四轮整改：附加的全句命中逐个判定命中词子句归属——兄弟效果子句/未登记
        # 兄弟机制的命中在 also_basis 注明拒绝依据（不删除——保留可定位依据）。
        also, also_basis = [], []
        for c in clause_matched[1:]:
            also.append(c)
            also_basis.append(dict(candidate=c, basis='clause'))
        for c in sentence_matched:
            info = _sentence_hit_info(c, hit_match[c], it)
            also.append(c)
            also_basis.append(dict(candidate=c,
                                   basis=_sibling_basis_text(info)
                                   or 'sentence（全句回退层：非本效果子句命中，子句命中存在时降为附加）'))
        for s in stags:
            if s['candidate'] in clause_matched or s['candidate'] in sentence_matched:
                continue
            also.append(s['candidate'])
            also_basis.append(dict(candidate=s['candidate'],
                                   basis='skill_tag（' + s['source'] + '）'))
        return clause_matched[0], 'clause', also, None, stags, also_basis
    if sentence_matched:
        # 第 2 层：无任何子句命中时全句回退。R3 第四轮整改：逐候选判定命中词子句归属
        # 与候选适用性——own/合法 shared（且声明兼容）才可作主分类；兄弟（有主/未登记）
        # 与声明不兼容的命中降为 also（also_basis 注明拒绝依据），主分类顺延下一候选；
        # 全部不可采时走无命中路径（skill_tag/G9 兜底＋具体理由）。
        primary = primary_info = None
        also, also_basis, demoted = [], [], []
        for c in sentence_matched:
            if it.get('kind') == 'effect':
                # 效果项：全句是次级通道——逐候选判定命中词子句归属与候选适用性
                info = _sentence_hit_info(c, hit_match[c], it)
                ok = (info['klass'] == 'own') or (info['klass'] == 'shared'
                                                  and _et_ok(c, it))
            else:
                # split/其他项：行日文即本项自身范围（无兄弟子句概念，适用性不检查——
                # 与 clause 路径同理），保持既有行为
                info = None
                ok = True
            if primary is None and ok:
                primary, primary_info = c, info
                continue
            also.append(c)
            sib_text = _sibling_basis_text(info) if info is not None else None
            if sib_text:
                also_basis.append(dict(candidate=c, basis=sib_text))
            elif info is None:
                # split/其他项在先候选之后的其余全句命中——保持既有披露
                also_basis.append(dict(candidate=c, basis='sentence'))
            elif info['klass'] == 'own':
                also_basis.append(dict(
                    candidate=c,
                    basis='sentence（命中词位于本效果自身子句「%s」——词形跨顿号致子句级'
                          '未匹配；按 CANDS 序列于在先候选之后，降为附加）'
                          % ((info['kwcl'] or '')[:48])))
            elif info['klass'] == 'shared' and _et_ok(c, it):
                # 合法共享且声明兼容——仅因 CANDS 序列于在先候选之后而未作主分类
                also_basis.append(dict(
                    candidate=c,
                    basis='sentence（合法共享子句「%s」——不属任何 effect 子句的技能级头/'
                          '触发包装/共享条件句段；按 CANDS 序列于在先候选之后，降为附加）'
                          % ((info.get('kwcl') or '')[:48])))
            elif info['klass'] == 'undetermined':
                # F1：归属无法确定——命中词子句为同句动作/陈述，与当前效果的共享关系
                # 无肯定依据（无冲突不证明共享）；候选保留待定位，不作主分类
                also_basis.append(dict(
                    candidate=c,
                    basis='sentence（归属无法确定：命中词子句「%s」为同句动作/陈述句段，'
                          '与当前效果的共享关系无肯定依据——候选保留待定位，不作本效果'
                          '主分类）' % ((info.get('kwcl') or '')[:48])))
            else:
                lim = EFFECT_TYPE_LIMITS.get(c.split(' ')[0]) or {}
                if info['klass'] == 'shared' and lim.get('page_groups') is not None \
                        and (it.get('page_group') or '') not in lim['page_groups']:
                    why = ('候选语境声明 page_groups⊆{%s}，本项技能语境 %s 不在内'
                           % (','.join(sorted(lim['page_groups'])),
                              it.get('page_group') or '（无）'))
                else:
                    why = '效果类型「%s」不在候选声明集合内' % (it.get('effect_type') or '（无）')
                also_basis.append(dict(
                    candidate=c,
                    basis='sentence（%s合法共享子句「%s」；候选适用性声明不兼容——%s，'
                          '不作本效果主分类）'
                          % ('' if info['klass'] == 'shared' else '非共享；',
                             (info.get('kwcl') or '')[:48], why)))
            demoted.append((c, info))
        if primary is not None:
            if it.get('kind') == 'effect':
                it['sentence_fallback'] = dict(
                    klass=primary_info['klass'],
                    keyword_clause=primary_info.get('kwcl'),
                    owners=primary_info.get('owners') or [],
                    mech_words=['%s→%s' % (w, f) for w, f in (primary_info.get('mech') or [])],
                    demoted=[dict(candidate=c, klass=i['klass'],
                                  owners=i.get('owners') or [])
                             for c, i in demoted])
            also += [s['candidate'] for s in stags
                     if s['candidate'] not in sentence_matched]
            also_basis += [dict(candidate=s['candidate'],
                                basis='skill_tag（' + s['source'] + '）')
                           for s in stags
                           if s['candidate'] not in sentence_matched]
            return primary, 'sentence', also, None, stags, also_basis
        # 全部全句命中不可采——落无命中路径（skill_tag/G9），理由带拒绝明细
        demote_why = []
        for c, info in demoted:
            if info['klass'] == 'sibling':
                demote_why.append('%s 命中词位于兄弟效果 ⟨%s⟩ 子句「%s」'
                                  % (c.split(' ')[0], ','.join(info['owners']),
                                     (info.get('kwcl') or '')[:32]))
            elif info['klass'] == 'sibling_unreg':
                demote_why.append('%s 命中词位于未登记兄弟机制子句「%s」（%s）'
                                  % (c.split(' ')[0], (info.get('kwcl') or '')[:32],
                                     '；'.join(info.get('flagged') or [])))
            elif info['klass'] == 'undetermined':
                demote_why.append('%s 命中词子句「%s」与当前效果的共享关系无肯定依据'
                                  '（归属无法确定，待定位）'
                                  % (c.split(' ')[0], (info.get('kwcl') or '')[:32]))
            else:
                demote_why.append('%s 候选适用性声明不兼容（效果类型=%s，语境=%s）'
                                  % (c.split(' ')[0], it.get('effect_type'),
                                     it.get('page_group')))
    else:
        demote_why = []
        demoted = []
        also = []
        also_basis = []
    if stags:
        # 局部语境无命中：技能级标记参与分类（唯一可定位依据），逐项注明局部未命中；
        # R3 第四轮整改：候选适用性（EFFECT_TYPE_LIMITS）同样约束技能级标签主分类——
        # 不兼容的标签降为 also（当前实测 YG1/YG2 技能级主分类全部在声明语境页组内，
        # 本检查为语义闭合、当前零翻转）。
        elig = [s for s in stags if _et_ok(s['candidate'], it)]
        if elig:
            s0 = elig[0]
            reason = ('本效果子句/全句无专项句式命中（子句「%s」/全句「%s」均无候选词形；'
                      '类别=%s，效果类型=%s）——按技能级标记「%s」归属（技能级标签，'
                      '非本效果局部语境；局部机制归属仍未定位）'
                      % ((it.get('clause') or '（无）')[:40],
                         (it.get('sentence') or '（无）')[:40],
                         it.get('page_group'), it.get('effect_type'),
                         s0['marker']))
            if demote_why:
                reason += '；全句回退命中不采为主分类：' + '；'.join(demote_why)
            # 被拒的全句回退命中降为 also（保留候选与依据，不丢失）；去除与新主分类重复项
            also = [c for c in also if c != s0['candidate']]
            also_basis = [b for b in also_basis if b['candidate'] != s0['candidate']]
            for s in stags:
                if s['candidate'] == s0['candidate'] or s['candidate'] in also:
                    continue
                also.append(s['candidate'])
                also_basis.append(dict(candidate=s['candidate'],
                                       basis='skill_tag（' + s['source'] + '）'))
            if len(elig) < len(stags):
                reason += '；技能级标记 %s 因候选适用性声明不兼容不作主分类' % (
                    '、'.join(s['candidate'].split(' ')[0] for s in stags
                              if not _et_ok(s['candidate'], it)),)
            return s0['candidate'], 'skill_tag', also, reason, stags, also_basis
    # 兜底：无专项句式命中——按技能类别与效果语境说明理由（G9＝自身バフ残部/条件バフ类）；
    # R3 第四轮整改：全句回退被拒绝的明细并入兜底理由（兄弟子句/未登记兄弟机制/适用性）；
    # 被拒命中降为 also_candidates（保留可定位依据，不丢失）。
    reason = ('无专项句式命中（子句「%s」/全句「%s」均无候选词形；类别=%s，'
              '效果类型=%s）——自身バフ残部/条件バフ兜底'
              % ((it.get('clause') or '（无）')[:40], (it.get('sentence') or '（无）')[:40],
                 it.get('page_group'), it.get('effect_type')))
    if demote_why:
        reason += '；全句回退命中不采为主分类：' + '；'.join(demote_why)
    return G9_ID, 'fallback', also, reason, stags, also_basis


def assign(t):
    """旧签名兼容（非 Y.G. 统计外的调用保留）：按整段文本匹配，语义同上（G9 兜底）。"""
    if re.match(NONVAL[1], t or ''):
        return NONVAL[0]
    for cid, _vt, _yg, pat in CANDS:
        if cid.startswith('G9'):
            continue
        if re.search(pat, t or ''):
            return cid
    return G9_ID


unc = []
fallback_reasons = 0
for it in items:
    it['cand'], it['context_basis'], also, reason, stags, also_basis = assign_item(it)
    it['also_candidates'] = also
    it['skill_tags'] = stags
    it['also_basis'] = also_basis
    if reason:
        it['fallback_reason'] = reason
        fallback_reasons += 1
    if it['cand'] == '?':
        unc.append(dict(backlog_id=it['backlog_id'], text=(it.get('text') or '')[:60]))
print('unassigned:', len(unc), '| fallback_reason_items:', fallback_reasons,
      '| skill_tag_primary:', sum(1 for it in items if it['context_basis'] == 'skill_tag'))

agg = collections.OrderedDict()
also_counter = collections.Counter()
for it in items:
    a = agg.setdefault(it['cand'], {'items': 0, 'rows': set(), 'cids': set(),
                                    'kinds': collections.Counter(),
                                    'priorities': collections.Counter(),
                                    'types': collections.Counter(),
                                    'categories': collections.Counter(),
                                    'basis': collections.Counter(),
                                    'fallback_reasons': []})
    a['items'] += 1
    a['rows'].add(it['row_id'])
    a['cids'].add(it['cid'])
    a['kinds'][it.get('kind') or '?'] += 1
    a['priorities'][it.get('priority') or 'P2'] += 1
    a['categories'][str(it.get('page_group') or it.get('page_table'))] += 1
    a['basis'][it.get('context_basis') or '?'] += 1
    if it.get('effect_type'):
        a['types'][str(it['effect_type'])] += 1
    if it.get('fallback_reason') and len(a['fallback_reasons']) < 3:
        a['fallback_reasons'].append(it['fallback_reason'])
    for c in it.get('also_candidates') or []:
        also_counter[c] += 1

# 通用（非 Y.G.）同形状收益：官方队列中不在选题视图的项（P2），按同一优先级归属，单列。
# R3 整改：非 Y.G. 统计采用与主链一致的输入语义——逐项取回行日文/上下文/类别并按
# assign_item 分层语境分类（不再把 snippet 片段单独交给分类器）。
backlog = json.load(open('output/character_skills/effect_ledger/backlog.json', encoding='utf-8'))
view_ids = {it['backlog_id'] for it in items}
nonyg = [b for b in backlog if b['backlog_id'] not in view_ids]

# 行索引（全部 backlog 行的页面定位：japanese/context/group/table）＋账本 span 索引
# R3 复审整改（20261023 §R3a）：_row_of 始终返回**所请求 row_id** 的语境——旧实现在
# 首次加载整卡填充缓存时把 out 一路改到最后并返回 out（＝该卡最后一行），使非 Y.G.
# 统计中每张卡的第一次查询用另一条技能的日文/类别/表名（复审实测 1,929 项语境错配、
# 其中 1,328 项分类改变；CID2 的 ability 行被读成该卡传授伤害句落 G1）。修复后
# 首查即返回 _row_idx[row_id]；所请求行不存在 → 显式 None（缓存该结论，不回退他行）。
_row_idx = {}


def _row_of(row_id):
    if row_id in _row_idx:
        return _row_idx[row_id]
    cid = int(str(row_id).split('-', 1)[0])
    try:
        d = json.load(open('output/character_skills/pages/%d/card.json' % cid, encoding='utf-8'))
    except (ValueError, FileNotFoundError):
        _row_idx[row_id] = None
        return None
    for grp in d['groups']:
        for sk in grp.get('skills', []):
            for row in sk.get('rows', []):
                _row_idx[row['row_id']] = dict(
                    japanese=row.get('japanese'), context=row.get('context_text'),
                    group=grp.get('group'), table=sk.get('table'))
    return _row_idx.get(row_id)


_LEDGER_SPAN = {}
with open('output/character_skills/effect_ledger/ledger.jsonl', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        if d.get('record_type') == 'effect':
            _LEDGER_SPAN[d['effect_id']] = d.get('span')

import unicodedata as _ud
_CLAUSE_RE = re.compile(r'[^。、！？\n]+')
_SENT_RE = re.compile(r'[^。！？\n]*[。！？]?')


def _context_of(b):
    """backlog 项 → enrich 同构的语境字段（japanese/clause/sentence/group/kind）。
    R3 复审整改（20261023）：携带 kind——效果项走局部通道（子句/全句），split 项走行日文；
    语境取自 _row_of 所请求行（首查即正确行，R3a 修复）。"""
    ri = _row_of(b['row_id'])
    ja = (ri or {}).get('japanese') if ri else None
    e = dict(japanese=ja, clause=None, sentence=None,
             row_id=b.get('row_id'), backlog_id=b.get('backlog_id'),
             page_group=(ri or {}).get('group') if ri else None,
             page_table=(ri or {}).get('table') if ri else None,
             context_text=(ri or {}).get('context') if ri else None,
             effect_type=b.get('effect_type'), kind=b.get('kind'))
    if b.get('kind') != 'effect':
        e['sentence'] = ja
        return e
    text_n = _ud.normalize('NFKC', ja or '')
    span = _LEDGER_SPAN.get(b['backlog_id'])
    seg, start = None, None
    if span and 0 <= span[0] < span[1] <= len(text_n):
        seg, start = text_n[span[0]:span[1]], span[0]
    elif b.get('snippet') and b['snippet'] in text_n:
        start = text_n.find(b['snippet'])
        seg = text_n[start:start + len(b['snippet'])]
    if seg:
        end = start + len(seg)
        for m in _CLAUSE_RE.finditer(text_n):
            if m.start() <= start and end <= m.end():
                e['clause'] = m.group(0)
                break
        for m in _SENT_RE.finditer(text_n):
            if m.start() <= start and end <= m.end() and m.group(0).strip():
                e['sentence'] = m.group(0)
                break
    return e


nonyg_stats = collections.Counter()
nonyg_uts = collections.defaultdict(set)
for b in nonyg:
    ctx = _context_of(b)
    c, _basis, _also, _reason, _st, _ab = assign_item(ctx)
    nonyg_stats[c] += 1
    nonyg_uts[c].add(norm_text(ctx.get('clause')
                               or ctx.get('sentence') or b.get('snippet') or ''))

out = []
for cand, a in agg.items():
    out.append({
        'candidate': cand, 'items': a['items'], 'rows': len(a['rows']),
        'cids': len(a['cids']), 'kinds': dict(a['kinds']), 'priorities': dict(a['priorities']),
        'types': dict(a['types']),
        'categories': dict(a['categories']), 'basis': dict(a['basis']),
        'also_items': also_counter.get(cand, 0),
        'fallback_reason_examples': a['fallback_reasons'],
        'nonyg_backlog': {'items': nonyg_stats.get(cand, 0),
                          'unique_texts': len(nonyg_uts.get(cand, set()))},
    })
out.sort(key=lambda x: -x['items'])

# 集合差口径（审查 DS-GR-02 指出的 296/35,731）：行数来源与去向逐项写明。
inv = json.load(open('work/character_skills_yg_priority/inventory_summary.json', encoding='utf-8'))
oq = inv['official_queue']
metrics = json.load(open('output/character_skills/effect_ledger/metrics.json', encoding='utf-8'))
pool_boundary = {
    'rows_without_backlog': {
        'count': oq['enriched_rows_without_backlog_items'],
        'source': ('coverage_refined（20261020 审查）yg=true&not inferred 的富化行中，'
                   '在当前 effect_ledger/backlog 无任何待办项的行'),
        '去向': ('不进入选题队列：行已完成（账本级完整，如 6335 f2 修复后退出）或该行'
                '当前无未解决效果/拆分项；仅保留在 build_inventory 的 yg_remaining_rows.json '
                '诊断登记，不冒充待办'),
    },
    'backlog_rows_outside_enriched': {
        'count': oq['backlog_rows_outside_enriched'],
        'source': ('官方 backlog（%d 项）中不在 coverage_refined 富化池的行——非 Y.G. 卡、'
                   '或 coverage_refined 已点亮行；行级待办以账本为准，不受旧池过滤' % oq['total_items']),
        '去向': ('仍由官方队列 effect_ledger/backlog.json 本身承载（P2 优先级为主）；'
                'Y.G. 选题视图只取 P0 断点∪Y.G.（%d 项）；通用形状收益以非视图 backlog 项'
                '（%d 项）计数单列，不并入 Y.G. 进展'
                % (len(items), len(nonyg))),
    },
}

# R3 修复前后分布对照——before 优先取独立复审对 R3 前规则的重放计数
# （selection_summary.json actual_counts：旧规则作用于 R3 前 enrich 输入 10,782 项；
#   其次回退上一次正式 yg_candidates.json；两者池规模差在对照中说明）
_before = None
_before_pool_items = None
_before_source = None
_sel = ROOT_OK = None
for _p in ('output/character_skills/review/independent_20261023_goal_recheck/selection_summary.json',
           'work/character_skills_yg_priority/yg_candidates.json'):
    try:
        _prev = json.load(open(_p, encoding='utf-8'))
        _counts = _prev.get('actual_counts') or {c['candidate']: c.get('items') for c in (_prev.get('candidates') or [])}
        if _counts:
            _before = dict(_counts)
            _before_pool_items = _prev.get('items') or ((_prev.get('meta') or {}).get('pool', {}).get('items'))
            _before_source = _p
            break
    except Exception:
        continue

# 代表性变化实例（≥5）：after≠before 的候选间迁移，逐例带 backlog_id/语境/主分类前后/依据
_after = {c['candidate']: c['items'] for c in out}
changed_examples = []

# R3-SENTENCE-FALLBACK（复验 Low 20261023）：sentence-only 命中计数——效果项主分类
# 命中级=sentence 且其子句对同一候选无命中的项数（次级通道的实际使用量，按 kind 分列）；
# 与仅技能级标签（skill_tag 主分类）项数一并固定，供验收范围声明。
_sentence_only = collections.Counter()
_skill_tag_only = collections.Counter()
_sf_klass = collections.Counter()
_sf_demote = collections.Counter()
for _it in items:
    if _it.get('context_basis') == 'sentence' and _it.get('clause') is not None:
        _pat = dict((_c2[0].split(' ')[0], _c2[3]) for _c2 in CANDS)
        _m2 = _pat.get(_it['cand'].split(' ')[0])
        if _m2 and not re.search(_m2, _it['clause']):
            _sentence_only[_it.get('kind') or '?'] += 1
    if _it.get('context_basis') == 'skill_tag':
        _skill_tag_only[_it.get('kind') or '?'] += 1
    _sf = _it.get('sentence_fallback')
    if _sf:
        _sf_klass[_sf['klass']] += 1
        for _d in _sf.get('demoted') or []:
            _sf_demote[_d['klass']] += 1


def _old_assign(t):
    """R3 前规则重放（旧 assign 逐字：NONVAL→CANDS 顺序首匹配，G9=r'.' 兜底）。"""
    if re.match(NONVAL[1], t or ''):
        return NONVAL[0]
    for cid, _vt, _yg, pat in CANDS:
        if re.search(pat, t or ''):
            return cid
    return '?'


for it in items:
    old_c = _old_assign(it.get('text') if it.get('kind') == 'effect' else (it.get('japanese') or ''))
    new_c = it['cand']
    if old_c != new_c and len(changed_examples) < 12:
        changed_examples.append(dict(
            backlog_id=it['backlog_id'], cid=it['cid'], kind=it.get('kind'),
            snippet=(it.get('text') or '')[:24],
            clause=(it.get('clause') or '')[:48],
            sentence=(it.get('sentence') or '')[:64],
            category=it.get('page_group'),
            before_old_rule_on_snippet=old_c,
            after_new_rule=new_c,
            basis=it['context_basis'],
            why=('R3 前效果项只传 snippet「%s」——无语境可匹配；现按 span 定位子句/全句'
                 '（%s 级命中）' % ((it.get('text') or '')[:16], it['context_basis']))))

meta = dict(
    generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    generator='work/character_skills_yg_priority/assign_candidates.py（R3 第四轮整改版 '
              '20261023·子句优先＋sentence 回退兄弟子句归属判定＋effect_type 适用性表）',
    generator_scripts={p: hashlib.sha256(
                           open(os.path.join(os.path.dirname(os.path.abspath(__file__)), p), 'rb').read()).hexdigest()
                       for p in ('build_inventory.py', 'enrich_records.py', 'assign_candidates.py')},
    generator_scripts_note='F03（20261024 流程调整）：选题链三脚本运行时内容 SHA-256，'
                           '与 backlog_anchor 共同定位本产物对应的代码与输入版本',
    input_chain=['build_inventory.py（消费 effect_ledger/backlog.json → yg_backlog_view.json）',
                 'enrich_records.py（视图记录级富化＋逐效果语境 → yg_backlog_view_enriched.json）',
                 'assign_candidates.py（本脚本：按目标效果语境分层归属 → yg_candidates.json）'],
    backlog_anchor=dict(
        source=oq['source'], total_items=oq['total_items'], by_kind=oq['by_kind'],
        by_priority=oq['by_priority'], yg_items=oq['yg_items'],
        snapshot_id=metrics['snapshot']['snapshot_id'],
        campaign_signature=metrics['snapshot']['campaign_signature']),
    pool=dict(source='yg_backlog_view_enriched.json', items=summary['view_items'],
              by_kind=summary['by_kind'], by_priority=summary['by_priority']),
    pool_boundary=pool_boundary,
    r3_rectification=dict(
        classification_input='逐效果分层语境（effect 片段 span→所在子句→所在全句）＋'
                             'context_text【…】技能级标记＋技能类别（page_group/page_table，'
                             '随项记录并按候选聚合 categories）；效果项局部通道不再用行日文 '
                             'full 级（R3 复审整改第二轮 §R3b：full 级使 clause/sentence '
                             '置空后分类零变化——语境形同摆设；split 项行日文即其自身范围照旧）',
        skill_tag_vs_local='技能级专项标签（如【共鳴必殺/連撃】，从 context_text【…】头取得）'
                           '只记入（skill_tags＋also_candidates＋also_basis），不得覆盖目标'
                           '效果局部语境的归属；效果级局部机制（伤害/增益/屏障/反響等）由'
                           '该效果自己的子句/全句判定为主分类；局部无命中时技能级标签才作为'
                           '主分类（basis=skill_tag，fallback_reason 注明局部未命中）',
        multi_class_relation='一项效果命中多个候选时：主分类按命中分层取——第 1 层子句'
                             '命中（CANDS 优先序首个）优先于第 2 层全句命中（仅无子句命中'
                             '时作主分类）；已有子句命中时全句命中降为附加分类'
                             '（also_candidates＋also_basis 注明 sentence 全句回退层）。'
                             'YG 专项先于通用残部，G9 捕获为末位兜底。'
                             '计数方式：items 按主分类恰一次（闭包 sum(items)==视图项数），'
                             'also_items 单列不计入闭包',
        clause_priority='R3 第三轮整改（20261023 复审 §R3 根因，线 B）：旧实现先遍历 '
                        'CANDS、再逐候选找 clause/sentence 命中取 matched[0]，高优先级'
                        '候选的全句命中（G5 状態異常回復/YG2 共鳴アビリティ等）压过当前'
                        '效果自己的子句命中——真实反例 349-…-f2#e00/e01/e02（攻撃/防御/'
                        '时长）被同句「全状態異常を回復する」抢为 G5。现改为命中分层：'
                        '子句级命中优先定主分类，全句级命中仅作回退并在有子句命中时降为'
                        '附加（also_basis 注明层级）；全句上下文与技能级标签不删除，'
                        'skill_tags/also_candidates/also_basis 保留可定位依据',
        effect_type_applicability='候选适用性·effect_type/技能语境（R3 第四轮整改，闭合'
                                  'R3-EFFECT-TYPE-NOOP 空钩子）：EFFECT_TYPE_LIMITS 已按'
                                  'clause 级命中实测类型分布＋任务卡指定语义填表（G0/G1→'
                                  'ダメージ・威力・効果；G2→攻撃/防御/移動/継続時間；G5→'
                                  '回復/HP回復/効果/継続時間；YG1→page_group=special_move'
                                  '（技能级共鳴必殺语境）；YG2→sympathy；其余按 clause 实测），'
                                  '在 sentence 回退路径主分类选取与技能级标签主分类处经 _et_ok '
                                  '生效——不兼容候选不得作主分类；clause 路径不检查（子句是'
                                  '本效果自己的话）；split 项全句即自身范围不检查。各族声明'
                                  '依据见代码注释与 meta.effect_type_limits_basis',
        effect_type_limits_basis=dict(
            (k.split(' ')[0], dict(types=(sorted(v['types']) if v.get('types') else None),
                                   page_groups=(sorted(v['page_groups'])
                                                if v.get('page_groups') else None)))
            for k, v in EFFECT_TYPE_LIMITS.items()),
        sentence_sibling_rule='R3 第四轮整改（闭合 R3-RESIDUAL-SENTENCE-SIBLING）：无子句'
                              '命中时的全句回退逐候选判定命中词所在子句归属——'
                              '(a) 命中词子句＝本效果自身子句（span 重合）→正常作主分类；'
                              '(b) 兄弟效果子句（账本 effect span→子句 join 有主，_ROW_'
                              'CLAUSE_OWNERS 懒建）→不得作主分类：降 also_candidates，'
                              'also_basis 注明「兄弟效果 ⟨效应 ID⟩ 的机制，不作本效果归属'
                              '依据」；无 effect 记录但机制词族与效果类型不匹配的子句'
                              '（_MECH_FAMILY_WORDS，只读复用 effect_ledger 机制词族口径）'
                              '＝未登记兄弟机制，同 (b)；(c) 技能级头【…】/≪…≫触发包装/'
                              '共享条件句段＝合法共享，可作主分类（sentence_fallback 字段'
                              '与 also_basis 注明依据）。主分类按无命中路径顺延'
                              '（skill_tag/G9 兜底＋逐项具体理由含拒绝明细）；'
                              'clause 路径零改动',
        sentence_fallback_klass=dict(
            by_klass=dict(_sf_klass),
            demoted_by_klass=dict(_sf_demote),
            note='sentence 回退路径效果项的命中词子句归属判定计数：klass=own（自身子句'
                 'span 重合）/shared（合法共享，作主分类）/sibling（兄弟效果子句，拒绝）/'
                 'sibling_unreg（未登记兄弟机制，拒绝）/none（全句命中全部不可采，走 '
                 'skill_tag/G9 路径，此时无 sentence_fallback 字段、拒绝明细在 '
                 'fallback_reason）；demoted_by_klass=被降附加命中的归属类别计数'),
        fallback_rule='G9 兜底保留：无局部命中且无技能级标记时归 G9（自身バフ残部/条件バフ类），'
                      'fallback_reason 逐项写明子句/全句/类别/效果类型',
        sentence_channel_scope='R3-SENTENCE-FALLBACK（DeepSeek 复验 Low 20261023→第四轮'
                               '整改闭合 High R3-RESIDUAL-SENTENCE-SIBLING 20261023）：'
                               '效果项语境通道＝子句（本效果自己的）→全句（次级）；第四轮'
                               '整改后全句回退命中不再无条件作主分类——命中词子句归属逐候选'
                               '判定（own/兄弟/未登记兄弟机制/合法共享，见 '
                               'sentence_sibling_rule），兄弟机制不再冒充本效果归属；'
                               '仅技能级标签归属的效果项（局部无命中、basis=skill_tag）与'
                               '全句命中全部被拒（klass=none）的效果项逐项带 fallback_reason'
                               '——均不冒充局部命中',
        sentence_only_counts=dict(by_kind=dict(_sentence_only),
                                  note='主分类命中级=sentence 且该效果自身子句对主候选无命中的项数'
                                       '（次级通道实际使用量，按 kind）'),
        skill_tag_only_counts=dict(by_kind=dict(_skill_tag_only),
                                   note='局部无命中、仅按 context_text【…】技能级标记归属的项数（按 kind）'),
        before_after=dict(before=_before, after=_after,
                          before_pool_items=_before_pool_items,
                          after_pool_items=len(items),
                          before_source=_before_source,
                          note='before=独立复审 selection_summary.json 对 R3 前规则的重放'
                               '主分类计数（selection_summary.items=%s，池为 R2 前 backlog '
                               '视图）；after=本次（%d 项，池含 R2 新增拆分项）——池规模差'
                               '在对照中计入' % (_before_pool_items, len(items))),
        changed_examples=changed_examples,
        acceptance='主分类分布/also_items/兜底理由/预期用例（349 共鳴必殺→YG1、共鳴'
                   'アビリティ→YG2、350 反響→YG3、真实普通自身增益→G9 且兜底理由成立）'
                   '与 backlog 集合对账共同验收，不以 unassigned=0 为唯一标准'),
    note='R3 整改（20261023 复审 §R3）＋R3 复审整改第二轮（20261023 §R3a/R3b）＋'
         'R3 第四轮整改（20261023 复验 High R3-RESIDUAL-SENTENCE-SIBLING/Medium '
         'R3-605-DISPOSITION-LEGAL-SHARED-OVERSTATED/Medium R3-EFFECT-TYPE-NOOP）：'
         '①_row_of 始终返回所请求行（旧实现首查返回该卡末行——1,929 项语境错配）；'
         '②效果项局部通道＝该效果自己的子句/全句（不再用行日文 full 级匹配），'
         '技能级专项标签（context_text【…】头）单列 skill_tags/also_basis 可定位依据、'
         '只记入不覆盖局部归属，局部无命中时才以 skill_tag 为主分类（basis=skill_tag）；'
         '③无子句命中时的全句回退逐候选判定命中词子句归属（own/兄弟/未登记兄弟机制/'
         '合法共享），兄弟机制降附加不作主分类（also_basis 注明效应 ID/机制词族依据）；'
         '④EFFECT_TYPE_LIMITS 按声明在 sentence 回退与技能级标签主分类处生效；'
         '候选词形规则与优先序不变（改动在语境通道、两级归属与回退归属判定）；'
         '选题队列=当前 backlog 派生的 yg_backlog_view（P0 断点∪Y.G.）',
)
json.dump({'meta': meta, 'candidates': out, 'unassigned_examples': unc[:20]},
          open(os.path.join(_OUT_DIR, 'yg_candidates.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
# R3 整改：逐项归属正式产物（主分类/语境层级/多分类/兜底理由）——验证与下游选题用
json.dump({'meta': dict(backlog_anchor=meta['backlog_anchor'],
                        generator=meta['generator'],
                        generated_at=meta['generated_at']),
           'items': [{k: it.get(k) for k in ('backlog_id', 'row_id', 'cid', 'kind',
                                             'priority', 'yg', 'breakpoint',
                                             'effect_type', 'snippet', 'text',
                                             'clause', 'sentence', 'japanese',
                                             'context_text', 'page_group', 'page_table',
                                             'cand', 'context_basis', 'also_candidates',
                                             'also_basis', 'skill_tags',
                                             'fallback_reason', 'sentence_fallback')}
                     for it in items]},
          open(os.path.join(_OUT_DIR, 'yg_candidates_items.json'), 'w',
               encoding='utf-8'), ensure_ascii=False, indent=1)

tot = 0
for c in out:
    print('%6d items %5d rows %4d cid | nonYG backlog items=%s | %s' % (
        c['items'], c['rows'], c['cids'],
        (c['nonyg_backlog'] or {}).get('items', '-'), c['candidate']))
    tot += c['items']
print('closure check: sum=%d / view %d / backlog total %d（差=P2 非视图项 %d，单列）'
      % (tot, len(items), len(backlog), len(nonyg)))
