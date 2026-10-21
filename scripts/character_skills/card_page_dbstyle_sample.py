# -*- coding: utf-8 -*-
"""数据库样式示例渲染器（展示层实验，仅样例，不是正式 card_page 生成器）。

参照「其他人的参考/数据库-《Y.G.1515》光耀の騎士 カイン.png」的版式做深色底展示层示例。
2026-10-20 第三轮改版（按玩家反馈「太乱了」重排首屏阅读层级）：
- 首屏每行＝日文原文（视觉主体，最大字号）＋紧随的数值 chips；chip 颜色即证据等级：
  确认=绿、确认（类型外推）=绿+虚线框+「外推」小字、推断=橙、未知=灰（显示「未知」）；
- 首屏不再出现任何审计口径副行（类型/单位/card.json 原值/换算/条件长文/来源指针等）；
- 每行一个「▶ 详情」<details>（默认收起）：规则键、card.json 原值、单位/类型、证据目录、
  适用范围（同类型外推等）、来源指针、条件长文、unknown_reasons 全文、绑定条件、
  多段披露（上下文全文/片段序号）、REVIEWED_RECORD 等审计字符串——通用渲染全部键，
  不删除任何证据信息，只是默认收起；
- 技能头保留名称/费用/档位/等级；技能级记录审计（original_text、record_evidence、
  forward_links 等）入技能级折叠；
- 页面顶部四联指标压缩为一行小字；基础信息区长证据文本、立绘绑定标注同样收入折叠
  （徽章与图片保留在首屏）。

2026-10-20 第四轮（玩家视角图例）：页面右上角固定吸顶小卡显示证据等级图例（滚动跟随；
窄屏媒体查询回退为文档流块，不溢出），四档各配讲人话定义＋一句「颜色只表示证据等级」
提示；图例不在折叠层内，首屏可见；内置自检：四档定义与提示语各恰好出现一次、
图例位置在第一个折叠层之前。

其余不变：
- 输入 cid 列表，从 output/character_skills/pages/<cid>/card.json 读数据；
- 输出单文件 HTML 到 output/character_skills/dbstyle_samples/<cid>.html；
- 数据全部来自 card.json 原值，不新增/推测任何数值或字段；
- 无来源区域按既定惯例显示「外部/网站维护」；
- 立绘区使用 full_unpack 解包产物原 PNG（base64 内嵌），逐图绑定标注收入折叠；
  主图显示比例 2:3 竖版（游戏 UI 控件 640×960，followup/REPORT.txt；whole/icon 维持 1:1）；
  缺失时显示「本输入快照未取得」并列出尝试路径，不借用其他 cid 的图；
- 内置自检逐行比对：日文原文、数值文案、规则键/原值/证据目录（折叠层内）、行数与
  汇总一致，立绘 data URI 与绑定标注必须在页面中。
"""
import argparse
import base64
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PAGES = ROOT / 'output' / 'character_skills' / 'pages'
DEFAULT_OUT = ROOT / 'output' / 'character_skills' / 'dbstyle_samples'
DEFAULT_CIDS = [30236, 7616, 10001]

NO_SOURCE = '外部/网站维护'

# ---- 立绘（full_unpack 解包产物原文件）----
ART_ROOT = ROOT / 'output' / 'full_unpack' / 'objects'
BINDING_EVIDENCE_REL = 'output/card_images/cid30236/binding_evidence.json'
LEDGER_REL = 'output/full_unpack/ledger.jsonl'
# 绑定依据统一文案（方法证据为 cid 参数化通用方法，证据文件现存于 cid30236 目录）
BINDING_TEXT = ('命名规则绑定：CharacterFactory.GetCharaTextureName* 方法证据'
                '（cid 计算纹理名），见 ' + BINDING_EVIDENCE_REL +
                '；解包台账 ' + LEDGER_REL)
MANIFEST_REL_30236 = 'output/card_images/cid30236/manifest.json'
MANIFEST_STATUS_30236 = 'PORTRAIT_CONFIRMED_FULL_BODY_NOT_LOCATED_PARTIAL_ART_EXPORTED'
# cid -> kind -> 追加标注（仅写已核实的文件内容，不外推）
ART_EXTRA_ANNOT = {
    30236: {
        'main': 'cid30236 manifest 标注该卡面为 CARD_VARIANT_CONTAINER_AND_VISUAL_MATCH'
                '（原图含龙、背景、卡框、标题及星级烘焙，不是独立立绘）',
        'whole': 'cid30236 manifest 标注为 CONFIRMED_CLIENT_ID_BINDING，但该图是'
                 '「原始透明上半身图；画面边缘截断身体及装饰，不是完整全身立绘」',
        'icon': 'cid30236 manifest 标注为 CONFIRMED_CLIENT_ID_BINDING（头像；'
                '卡框与星级已烘焙在原始纹理中）',
    },
}
# 30236 页级 manifest 状态标注（如实转述，不把整卡说成全身体已确认）
MANIFEST_NOTE_30236 = (
    'cid30236 manifest 状态（' + MANIFEST_REL_30236 + '）：' + MANIFEST_STATUS_30236
    + '——头像 CONFIRMED_CLIENT_ID_BINDING；全身未定位、局部立绘已导出。'
      '本页整卡与局部图均按命名规则绑定标注，不视为全身体已确认。')

# 显示比例依据（2026-10-20 修正轮，与正式渲染层 card_page_render_v2 同口径）：
# 卡面纹理存储 512×512 方形，但游戏 UI 显示为 2:3 竖版。证据：
# output/card_images/cid30236/followup/REPORT.txt——CharaInfoCard._cardTexture 指向
# UITexture 109376/CardOrg，控件 640×960、aspectRatio≈0.6667、UV 覆盖整张纹理（APK prefab
# 最小序列化前缀解析，非完整 UI 树恢复或实机测量）；头像 42×42 与上半身 512×512 的使用
# 场景是 1:1。本仓库 4313 张 Card_OrgSize PNG 实测全部 512×512（2026-10-20 全量尺寸普查）。
FOLLOWUP_REPORT_REL = 'output/card_images/cid30236/followup/REPORT.txt'
DISPLAY_RATIO_NOTE_CARD = ('显示比例：存储 512×512；显示 2:3 竖版（游戏 UI 控件 640×960，'
                           'APK prefab 证据 ' + FOLLOWUP_REPORT_REL +
                           '；最小序列化前缀解析，非实机测量）')
DISPLAY_RATIO_NOTES_1_1 = {
    'whole': '显示比例：维持 1:1（同报告使用场景依据：上半身 PanelSortieLoginNext._texChara '
             '控件 512×512，1:1 有据；半身 face 变体无其他界面比例依据，不套卡面比例）',
    'icon': '显示比例：维持 1:1（同报告使用场景依据：头像 CardKizunaButton._charaIcon '
            '控件 42×42，1:1 有据）',
}
DISPLAY_RATIO_AUDIT = (
    '显示比例依据（' + FOLLOWUP_REPORT_REL + '；APK prefab 最小序列化前缀解析，'
    '非实机测量、非完整 UI 树恢复）：主图 Card_OrgSize 存储 512×512 方形（本仓库 4313 张 '
    'Card_OrgSize PNG 实测全部 512×512），游戏 UI CharaInfoCard._cardTexture 指向 '
    'UITexture 109376/CardOrg，控件 640×960、aspectRatio≈0.6667、UV 覆盖整张纹理——'
    '显示比例应为 2:3 竖版；本页主图按 2:3 非均匀缩放显示（浏览器等价于游戏 UI 把整张'
    '方形纹理铺进 640×960 控件的行为，源 PNG 未改）。Trimmed_Whole 与 Card_Icon 维持 '
    '1:1 显示（头像 42×42、上半身 512×512 的使用场景依据；半身 face 变体无其他界面'
    '比例依据，保留 1:1）。')


def art_kinds(padded):
    """(kind, 对象目录相对路径, 文件名, 页面标签)。"""
    return [
        ('main', f'Card_OrgSize/cha_2d_card_{padded}', f'cha_2d_card_{padded}.png',
         '主图｜整卡 Card_OrgSize'),
        ('whole', f'Trimmed_Whole/cha_2d_whole_{padded}', f'cha_2d_whole_{padded}.png',
         'Trimmed_Whole 全身'),
        ('icon', f'Card_Icon/cha_2d_icon_{padded}', f'cha_2d_icon_{padded}.png',
         'Card_Icon 头像'),
    ]


def load_art(cid):
    """从 full_unpack objects 读取立绘 PNG，返回逐条目模型（base64 内嵌）。"""
    padded = str(cid).zfill(5)
    extras = ART_EXTRA_ANNOT.get(cid, {})
    items = []
    for kind, subdir, fname, label in art_kinds(padded):
        rel = f'output/full_unpack/objects/{subdir}/{fname}'
        path = ART_ROOT / subdir / fname
        item = dict(kind=kind, label=label, rel=rel, binding=BINDING_TEXT,
                    extra=extras.get(kind), data_uri=None, tried=[])
        if path.is_file():
            raw = path.read_bytes()
            item['data_uri'] = 'data:image/png;base64,' + base64.b64encode(raw).decode('ascii')
            item['bytes'] = len(raw)
        else:
            # 缺失：如实记录尝试路径；不借其他 cid 的图
            item['tried'] = [rel, rel.rsplit('/', 1)[0] + '/objects_index.json']
        items.append(item)
    return items

# basic.fields 中本示例基础表需要的字段顺序（key -> 展示行名）
REQUIRED_BASIC_ROWS = [
    ('jobtype', '职业'),
    ('home', '所属'),
    ('attack_type', '攻击类型'),
    ('growth', '成长'),
    ('critical', '暴击几率'),
    ('atkspeed', '攻击速度'),
    ('obtain', '获得来源'),
    ('illustrator', '画师'),
    ('voice', '声优'),
    ('debut', '登场日期'),
]
# 额外展示的已确认字段（同样来自 basic.fields，不造值）
EXTRA_BASIC_ROWS = [
    ('weaponid', '武器ID'),
    ('iniap', '主表初始ATK'),
    ('inihp', '主表初始HP'),
    ('profile', '介绍'),
]


def esc(v):
    return html.escape(str(v), quote=True)


def basic_field_lookup(basic):
    out = {}
    for f in basic.get('fields', []):
        out.setdefault(f.get('key'), f)
    return out


def build_basic_rows(data):
    """组装基础信息表行；每行 (label, display, evidence, note)。"""
    basic = data.get('basic', {})
    fields = basic_field_lookup(basic)
    ext = {e.get('label'): e.get('value') for e in basic.get('external', [])}
    art = basic.get('card_art', {})
    rows = []
    for key, label in REQUIRED_BASIC_ROWS:
        if key in fields:
            f = fields[key]
            rows.append((label, f.get('display_value'), f.get('evidence'),
                         f.get('note') or f.get('mapping_evidence') or ''))
        elif key == 'attack_type':
            raw = basic.get('raw_record', {}).get('battletype')
            note = 'card.json 无该字段已审显示值；主表 battletype 原值 ' + (
                str(raw) + ' 存在但无已证实名称映射，不造值' if raw is not None else '缺失')
            rows.append((label, NO_SOURCE, '未知', note))
        elif key == 'obtain':
            rows.append((label, NO_SOURCE, '未知', 'card.json 未提供获得来源字段，不造值'))
        elif key == 'illustrator':
            rows.append((label, ext.get('画师', NO_SOURCE), '确认', 'basic.external 原值'))
        elif key == 'voice':
            rows.append((label, ext.get('声优', NO_SOURCE), '确认', 'basic.external 原值'))
        elif key == 'debut':
            rows.append((label, ext.get('日期', NO_SOURCE), '未知', 'basic.external 日期为外部资料'))
    for key, label in EXTRA_BASIC_ROWS:
        if key in fields:
            f = fields[key]
            rows.append((label, f.get('display_value'), f.get('evidence'),
                         f.get('note') or ''))
    return rows, art


def row_evidence_label(row):
    """行级证据展示：确认 / 确认（类型外推）/ 推断 / 未知。"""
    ev = row.get('evidence')
    scope = row.get('evidence_scope') or []
    if ev == '确认':
        if any('BY_TYPE_EXTRAPOLATED' in str(s) for s in scope):
            return '确认（类型外推）'
        return '确认'
    if ev == '推断':
        return '推断'
    return '未知'


EVID_CLASS = {'确认': 'ev-conf', '确认（类型外推）': 'ev-conf-ext', '推断': 'ev-inf', '未知': 'ev-unk'}


# ---- 证据等级图例（第四轮）：讲人话定义；口径与 card.json 四档标注一致，不改判 ----
LEGEND_DEFINITIONS = [
    ('确认', 'ev-conf',
     '这个数值有逐条核过的证据链（代码规则或原文审核记录），不是猜的。'),
    ('确认·类型外推', 'ev-conf-ext',
     '证据来自同类型技能的规则，适用到这条上没有逐条再审，但规则本身已核。'),
    ('推断', 'ev-inf',
     '按句式模板和数据字段推出来的值，方向大概率对，但没逐条审定，可能错配。'),
    ('未知', 'ev-unk',
     '原文没写数值，目前也没有能用的证据；点开详情能看到缺什么。'),
]
LEGEND_NOTE = '颜色只表示证据等级，数值都可在 ▶详情 里查到出处。'


def build_legend():
    """右上角吸顶图例小卡；窄屏由 CSS 媒体查询回退为文档流块。"""
    items = ''.join(
        f'<div class="legend-item"><span class="chip {cls}">{esc(label)}</span>'
        f'<span class="legend-desc">{esc(desc)}</span></div>'
        for label, cls, desc in LEGEND_DEFINITIONS)
    return ('<!-- legend:start -->'
            '<div class="legend" id="evidence-legend">'
            '<div class="legend-title">数值颜色＝证据等级</div>'
            f'{items}<div class="legend-note">{esc(LEGEND_NOTE)}</div></div>'
            '<!-- legend:end -->')


def badge(label, cls=None):
    cls = cls or EVID_CLASS.get(label, 'ev-unk')
    return f'<span class="badge {cls}">{esc(label)}</span>'


# ---- 折叠层（审计）：通用键值渲染，全部键保留，不删除任何证据信息 ----
ROW_AUDIT_LABELS = {
    'row_id': '行ID', 'cid': 'CID', 'group': '组', 'stage': '档位', 'level': '等级',
    'reference_field': '引用字段', 'fragment_index': '片段序号', 'context_text': '上下文全文（多段披露）',
    'row_class': '行类别', 'original_numeric_items': '原文数字项', 'original_A': '原文A行',
    'evidence': '行证据', 'numeric_evidence': '数值证据', 'association_evidence': '关联证据',
    'partial': '部分解释', 'unknown_reasons': '未知原因全文', 'source': '来源指针',
    'raw_value_states': '原值状态', 'raw_state_summary': '原值状态摘要',
    'source_evidence_ref': '证据引用键', 'old_fragment_status': '旧片段状态',
    'old_candidates_reused': '旧候选复用', 'mechanism_added': '新增机制',
    'evidence_scope': '适用范围', 'binding_conditions': '绑定条件',
    'source_position': '来源位置', 'source_span_id': '来源跨度ID',
    'merge_key': '合并键', 'alias_references': '别名引用', 'japanese': '日文原文',
    'answers': '逐答案',
    'inference_pilot': '推断层元数据（批1试点 type1017）',
    'inference_pilot_hint': '批1试点 hint',
    'inference_b3': '推断层元数据（批3 type8）', 'inference_b3_hint': '批3 hint',
    'inference_b4': '推断层元数据（批4 条件扩展）', 'inference_b4_hint': '批4 hint',
    'inference_b5': '推断层元数据（批5 跨表 type1017）', 'inference_b5_hint': '批5 hint',
    'inference_b6': '推断层元数据（批6 必殺バフ）', 'inference_b6_hint': '批6 hint',
    'inference_b7': '推断层元数据（批7 共鳴）', 'inference_b7_hint': '批7 hint',
}
# 批 6 复验 Low（49/367 行）句序口径澄清（渲染层，card.json 不变；scope §7 方案 A）。
CHARAINFO_SENTENCE_ORDER_NOTE = (
    '句序口径澄清（批 7 实施轮，渲染层）：句序注记的「本记录正文句序」指 charainfo 行自身正文'
    '（charainfo.skilltext）句序；同页 pattern 正文句序另计，两者不相互替代')
ANSWER_AUDIT_LABELS = {
    'value': '数值文案', 'quantity_kind': '类型', 'unit': '单位', 'raw_value': 'card.json 原值',
    'field_path': '字段路径', 'conversion': '换算', 'base_definition': '基值定义',
    'target': '对象', 'conditions': '条件', 'duration': '持续时间', 'rule_limits': '规则限制',
    'note': '备注', 'numeric_source': '数值来源', 'numeric_evidence': '数值证据',
    'association_evidence': '关联证据', 'evidence_scope': '适用范围', 'table': '表',
    'record_id': '记录ID', 'source': '来源指针', 'rule_key': '规则键', 'evidence': '证据目录',
    'effect_id': '效果ID', 'baseline_declared_description_id': '基线描述ID',
    'context': '原句片段', 'quantitative': '定量', 'binding': '绑定', 'rule_status': '规则状态（兼容别名，=rule_body_status）',
    'rule_body_status': '规则本体状态', 'condition_label': '条件标签（原文逐字，首屏分组键）',
}
SKILL_AUDIT_LABELS = {
    'skill_id': '技能ID', 'name': '名称', 'original_group': '原始组', 'record_id': '记录ID',
    'table': '表', 'layer': '层', 'source': '来源', 'text_field': '文本字段',
    'original_text': '技能原文全文', 'reference_field': '引用字段', 'cost': '费用',
    'cost_state': '费用状态', 'record_evidence': '记录证据', 'forward_links': '前向链接',
    'old_rec_key': '旧记录键', 'link_status': '链接状态',
    'baseline_metadata_answers': '基线元数据答案', 'association_evidence': '关联证据',
    'level_note': '等级说明', 'level_state': '等级状态', 'stage': '档位', 'level': '等级',
    'rows': '描述行',
}


def audit_value_html(val):
    """折叠层取值：bool 转是/否；字符串列表逐条 li；嵌套结构 pretty JSON。"""
    if val is True:
        return '是'
    if val is False:
        return '否'
    if isinstance(val, list) and val and all(isinstance(x, str) for x in val):
        return '<ul class="audit-list">' + ''.join('<li>' + esc(x) + '</li>' for x in val) + '</ul>'
    if isinstance(val, (dict, list)):
        return '<pre class="audit-pre">' + esc(json.dumps(val, ensure_ascii=False, indent=1)) + '</pre>'
    return esc(val)


def render_audit(obj, labels, skip=()):
    """通用审计渲染：按对象全部键输出 kv 行；空值跳过（信息不丢，原 JSON 中本就为空）。"""
    parts = []
    for k, v in obj.items():
        if k in skip or v is None or v == '' or v == [] or v == {}:
            continue
        label = labels.get(k, k)
        if k == 'rule_status' and isinstance(v, str):
            # B5-R01（批5审查）同款：规则级状态限定口径，与 card_page_render_v2 同步。
            v = f'规则级状态（规则本体{v}；不代表本值归属确认）'
        parts.append(f'<div class="kv"><span class="kv-k">{esc(label)}</span>'
                     f'<span class="kv-v">{audit_value_html(v)}</span></div>')
    return ''.join(parts)


def answer_chip(a, row, out_checks):
    """首屏数值 chip：颜色即证据等级；数值文案保持现有换算结果。"""
    val = a.get('value')
    if val is not None:
        out_checks.append(('answer_value:' + row.get('row_id', ''), esc(val)))
    nev = a.get('numeric_evidence') or '未知'
    scope = a.get('evidence_scope')
    if isinstance(scope, str):
        scope = [scope]
    scope = list(scope or []) + list(row.get('evidence_scope') or [])
    if nev == '确认' and any('BY_TYPE_EXTRAPOLATED' in str(s) for s in scope):
        label, cls = '确认（类型外推）', 'ev-conf-ext'
    else:
        label, cls = nev, EVID_CLASS.get(nev, 'ev-unk')
    if cls == 'ev-unk' or not val:
        # 未知：灰 chip 显示「未知」（原值/原因在折叠层）
        return f'<span class="chip ev-unk" title="证据：未知">未知</span>'
    body = esc(val)
    if cls == 'ev-conf-ext':
        body += '<span class="chip-tag">外推</span>'
    if a.get('association_evidence') == '未知' and nev == '确认':
        # L1（20261021 独立审查整改）：原文数字 chip 追加「原文已写」小字，与「关联未知」
        # 并存；限定 numeric_source='原文'（基线答案不标）。与 card_page_render_v2 同步。
        body += '<span class="chip-assoc">关联未知</span>'
        if a.get('numeric_source') == '原文':
            body += '<span class="chip-assoc">原文已写</span>'
    return f'<span class="chip {cls}" title="证据：{esc(label)}">{body}</span>'


def chip_groups_html(answers, row, out_checks):
    """H1（20261021 独立审查整改）：批 4 条件扩展行的首屏 chips 分组显示（与
    card_page_render_v2.chip_groups_html 同口径）：无 condition_label＝「基础」组；
    带 condition_label（逐字条件原文）按条件值分组、组内按原顺序；组标签首屏可见、
    不需展开详情；不合乘、不改证据等级；无 condition_label 的行维持原样。"""
    if not any(a.get('condition_label') for a in answers):
        return ''.join(answer_chip(a, row, out_checks) for a in answers)
    base, cond_order, cond_groups = [], [], {}
    for a in answers:
        cl = a.get('condition_label')
        if cl is None:
            base.append(a)
        else:
            if cl not in cond_groups:
                cond_groups[cl] = []
                cond_order.append(cl)
            cond_groups[cl].append(a)
    parts = []
    if base:
        parts.append('<span class="chip-group"><span class="chip-group-label">基础</span>'
                     + ''.join(answer_chip(a, row, out_checks) for a in base) + '</span>')
    for cl in cond_order:
        parts.append('<span class="chip-group"><span class="chip-group-label">条件：'
                     + esc(cl) + '</span>'
                     + ''.join(answer_chip(a, row, out_checks) for a in cond_groups[cl]) + '</span>')
    return ''.join(parts)


def render_row(row, out_checks):
    """首屏＝日文原文＋数值 chips；全部审计内容收入单个 <details>（默认收起）。"""
    rid = row.get('row_id', '')
    out_checks.append(('row_japanese:' + rid, esc(row.get('japanese', ''))))
    answers = row.get('answers', [])
    if answers:
        chips = chip_groups_html(answers, row, out_checks)
        ans_audit = ''.join(
            f'<div class="audit-ans"><div class="audit-ans-title">答案 {i + 1}</div>'
            f'{render_audit(a, ANSWER_AUDIT_LABELS)}</div>'
            for i, a in enumerate(answers))
        ans_sec = (f'<div class="audit-sec"><div class="audit-title">逐答案（规则键/原值/'
                   f'单位类型/证据目录/适用范围/条件/来源指针）</div>{ans_audit}</div>')
    else:
        chips = '<span class="chip ev-unk">未知</span>'
        ans_sec = ''
    ev_label = row_evidence_label(row)
    # 批 6 复验 Low（49/367 行）句序口径澄清（渲染层，card.json 不变；scope §7 方案 A），
    # 与 card_page_render_v2 同步。
    b6_meta = row.get('inference_b6') or {}
    charainfo_note = (f'<div class="kv"><span class="kv-k">句序口径澄清</span>'
                      f'<span class="kv-v">{esc(CHARAINFO_SENTENCE_ORDER_NOTE)}</span></div>'
                      if isinstance(b6_meta, dict) and b6_meta.get('table') == 'charainfo' else '')
    row_audit = (f'<div class="kv"><span class="kv-k">行证据等级</span>'
                 f'<span class="kv-v">{esc(ev_label)}</span></div>'
                 + charainfo_note
                 + render_audit(row, ROW_AUDIT_LABELS, skip=('answers', 'japanese')))
    row_sec = f'<div class="audit-sec"><div class="audit-title">行级审计</div>{row_audit}</div>'
    fold = (f'<details class="row-detail"><summary>▶ 详情（规则键/原值/证据/来源/条件）</summary>'
            f'{ans_sec}{row_sec}</details>')
    return (f'<div class="row" data-row-id="{esc(rid)}">'
            f'<div class="row-jp">{esc(row.get("japanese", ""))}</div>'
            f'<div class="chips">{chips}</div>{fold}</div>')


def render_skill(skill, out_checks):
    meta = []
    if skill.get('cost') is not None:
        meta.append('费用 ' + (esc(skill['cost']) if skill.get('cost_state') == 'present' else esc(NO_SOURCE)))
        out_checks.append(('skill_cost:' + skill.get('skill_id', ''), esc(skill['cost'])))
    if skill.get('stage'):
        meta.append(esc(skill['stage']))
    if skill.get('level') is not None:
        meta.append('Lv ' + esc(skill['level']))
    name_html = esc(skill.get('name') or '（无名称）')
    out_checks.append(('skill_name:' + skill.get('skill_id', ''), name_html))
    rows_html = ''.join(render_row(r, out_checks) for r in skill.get('rows', []))
    # 技能级记录审计（original_text / record_evidence / forward_links 等）收入折叠
    skill_fold = (f'<details class="skill-detail"><summary>▶ 技能记录审计</summary>'
                  f'{render_audit(skill, SKILL_AUDIT_LABELS, skip=("rows",))}</details>')
    return (f'<div class="skill"><div class="skill-head"><span class="skill-name">{name_html}</span>'
            f'<span class="skill-meta">{"｜".join(meta)}</span></div>{rows_html}{skill_fold}</div>')


def build_model(cid, pages_dir):
    path = pages_dir / str(cid) / 'card.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('cid') != cid:
        raise ValueError(f'{path}: cid 不一致 {data.get("cid")} != {cid}')
    basic_rows, art = build_basic_rows(data)
    groups_present, groups_empty, skills = [], [], []
    for g in data.get('groups', []):
        if g.get('skills'):
            groups_present.append(g)
            for sk in g['skills']:
                skills.append(sk)
        else:
            groups_empty.append(g.get('label') or g.get('group'))
    s = data.get('summary', {})
    metrics = [(k, s.get(k, {})) for k in ('A', 'whole_row_confirmed', 'original_A', 'C')]
    return dict(cid=cid, data=data, basic_rows=basic_rows, art=art, art_items=load_art(cid),
                groups_present=groups_present, groups_empty=groups_empty,
                metrics=metrics, sources=data.get('sources', {}),
                src_path=path)


def render_html(m):
    cid = m['cid']
    d = m['data']
    rec = d['basic'].get('raw_record', {})
    name = rec.get('name') or NO_SOURCE
    title = rec.get('title') or ''
    rarity = rec.get('rarity')
    cost = rec.get('cost')
    checks = []
    # 顶部
    stars = ('★' * int(rarity)) if isinstance(rarity, int) and rarity > 0 else NO_SOURCE
    top = (f'<div class="card-top"><div class="title-line">'
           f'<span class="cid">CID {cid}</span>'
           f'<span class="card-name">{esc(name)}</span>'
           f'<span class="card-title">{esc(title)}</span></div>'
           f'<div class="sub-line"><span class="stars">{esc(stars)}</span>'
           f'<span class="cost">COST {esc(cost) if cost is not None else esc(NO_SOURCE)}</span>'
           f'<span class="layer">{esc(d["basic"].get("layer", ""))}</span></div></div>')
    if cost is not None:
        checks.append(('top_cost', esc(cost)))
    checks.append(('top_name', esc(name)))
    # 顶部四联指标：压缩为一行小字
    metric_bits = []
    for key, mm in m['metrics']:
        cnt = mm.get('count'); den = mm.get('denominator')
        label = {'A': 'A 数值/公式行', 'whole_row_confirmed': '整行确认',
                 'original_A': '原文A', 'C': 'C 仅未知'}[key]
        metric_bits.append(f'{esc(label)} {cnt}/{den}')
        checks.append(('metric:' + key, f'{cnt}/{den}'))
    metrics_line = ('<div class="metrics-line">指标：' + '｜'.join(metric_bits)
                    + '</div>')
    legend = build_legend()
    checks.append(('legend_present', 'id="evidence-legend"'))
    # 基础表：徽章保留在首屏；证据/备注长文本收入折叠
    basic_trs = []
    basic_fold_kvs = []
    for label, disp, ev, note in m['basic_rows']:
        disp_html = esc(disp)
        checks.append(('basic:' + label, disp_html)) if ev != '未知' else None
        ev_badge = badge(NO_SOURCE if disp == NO_SOURCE else (ev or '未知'))
        if ev == '确认' and disp != NO_SOURCE:
            ev_badge = badge('确认')
        basic_trs.append(f'<tr><th>{esc(label)}</th><td>{disp_html} {ev_badge}</td></tr>')
        detail_bits = [f'证据：{esc(ev or "未知")}']
        if note:
            detail_bits.append(esc(note))
        basic_fold_kvs.append(f'<div class="kv"><span class="kv-k">{esc(label)}</span>'
                              f'<span class="kv-v">{("｜".join(detail_bits))}</span></div>')
    basic_fold = (f'<details class="basic-detail"><summary>▶ 基础信息证据细节</summary>'
                  f'{"".join(basic_fold_kvs)}</details>') if basic_fold_kvs else ''
    # 卡面立绘区：full_unpack 解包产物原 PNG（base64 内嵌）；绑定标注收入折叠
    art_note = m['art'].get('note', '')
    art_items = m['art_items']
    main_items = [it for it in art_items if it['kind'] == 'main']
    strip_items = [it for it in art_items if it['kind'] != 'main']
    art_html_parts = []
    for it in main_items + strip_items:
        cls = 'art-main' if it['kind'] == 'main' else 'art-thumb'
        if it.get('data_uri'):
            bind_bits = [f'文件：{esc(it["rel"])}（{it["bytes"]} 字节 PNG，base64 内嵌）',
                         f'绑定依据：{esc(it["binding"])}']
            ratio_note = (DISPLAY_RATIO_NOTE_CARD if it['kind'] == 'main'
                          else DISPLAY_RATIO_NOTES_1_1.get(it['kind']))
            if ratio_note:
                bind_bits.append(esc(ratio_note))
            if it.get('extra'):
                bind_bits.append(esc(it['extra']))
            art_html_parts.append(
                f'<figure class="{cls}">'
                f'<img class="art-img" src="{it["data_uri"]}" alt="{esc(it["label"])} (cid {cid})">'
                f'<figcaption class="art-caption">{esc(it["label"])}'
                f'<details class="art-bind-detail"><summary>▶ 绑定标注</summary>'
                f'<div class="art-bind">{"<br>".join(bind_bits)}</div></details>'
                f'</figcaption></figure>')
        else:
            tried = ''.join(f'<li>{esc(t)}</li>' for t in it['tried'])
            art_html_parts.append(
                f'<figure class="{cls} art-missing">'
                f'<figcaption class="art-caption">{esc(it["label"])}'
                '<div class="art-miss-line">本输入快照未取得</div>'
                f'<details class="art-tried"><summary>尝试路径</summary><ul>{tried}</ul></details>'
                '</figcaption></figure>')
    # 立绘区审计（manifest 状态＋card.json card_art 状态）收入折叠
    art_audit_bits = []
    if cid == 30236:
        art_audit_bits.append(f'<div class="art-bind">{esc(MANIFEST_NOTE_30236)}</div>')
    art_audit_bits.append(
        f'<div class="art-bind">card.json basic.card_art（card_page 主管线）状态：'
        f'{esc(m["art"].get("status", "NO_VERIFIED_BINDING"))}'
        + (f'；{esc(art_note)}' if art_note else '')
        + '。本立绘区独立于主管线，绑定依据见各图折叠标注。</div>')
    art_audit_bits.append(f'<div class="art-bind">{esc(DISPLAY_RATIO_AUDIT)}</div>')
    art_audit = (f'<details class="art-audit"><summary>▶ 立绘区审计（manifest/主管线状态）</summary>'
                 f'{"".join(art_audit_bits)}</details>')
    art_block = f'<div class="art-block">{"".join(art_html_parts)}{art_audit}</div>'
    # 右侧等级成长区：整块外部/网站维护
    lv_block = ('<div class="external-block"><div class="ext-title">等级 ATK/HP 表与成长曲线</div>'
                '<div class="ext-value">' + esc(NO_SOURCE) + '</div>'
                '<div class="ext-note">等级成长表在 card.json 中即标注为外部资料；'
                '本示例不按截图或参考页编造任何等级数值与曲线。</div></div>')
    # 技能区
    group_html = []
    for g in m['groups_present']:
        skills_html = ''.join(render_skill(sk, checks) for sk in g['skills'])
        group_html.append(
            f'<div class="group"><div class="group-label">{esc(g.get("label") or g.get("group"))}</div>'
            f'<div class="group-body">{skills_html}</div></div>')
    empty_html = ''
    if m['groups_empty']:
        items = ''.join(f'<span class="empty-chip">{esc(l)}：本输入快照未关联</span>' for l in m['groups_empty'])
        empty_html = f'<div class="empty-groups">{items}</div>'
    # 页脚：数据快照/来源＋声明（四联指标已上移至顶部一行小字）
    snapshot = m['sources'].get('snapshot', '')
    input_root = m['sources'].get('input_root', '')
    footer = ('<div class="footer">'
              f'<div class="foot-note">数据快照：{esc(snapshot)}｜输入根：{esc(input_root)}'
              f'｜来源：{esc(m["src_path"].relative_to(ROOT).as_posix())}</div>'
              '<div class="foot-note">示例渲染，数据来自 card.json；展示层实验产物，'
              '不属于正式 card_page 生成器输出。无来源区域显示「' + esc(NO_SOURCE) + '」，未编造数值。'
              '颜色语义：绿=确认｜绿虚线+外推=确认（类型外推）｜橙=推断｜灰=未知；'
              '各行「▶ 详情」折叠层含规则键、原值、证据目录、来源指针与条件全文，审计信息不丢失。</div></div>')
    doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>cid {cid} 数据库样式示例</title>
<style>
body{{margin:0;background:#141418;color:#d8d8de;font-family:"Microsoft YaHei","Hiragino Kaku Gothic ProN",sans-serif;font-size:14px;}}
.wrap{{max-width:1100px;margin:0 auto;padding:16px;}}
.topbar{{background:#101014;padding:10px 16px;font-size:13px;color:#9a9aa2;border-bottom:1px solid #2c2c34;}}
.panel{{background:#222228;border:1px solid #34343c;border-radius:6px;padding:14px 16px;margin:12px 0;}}
.card-top .card-name{{font-size:20px;font-weight:bold;color:#fff;margin-right:10px;}}
.card-top .card-title{{color:#c8b06a;}}
.card-top .cid{{color:#8a8a94;margin-right:10px;font-size:12px;}}
.sub-line{{margin-top:6px;}}
.stars{{color:#e8c84a;margin-right:16px;}}
.cost{{color:#e8e8ee;margin-right:16px;}}
.layer{{color:#7a7a84;font-size:12px;}}
.metrics-line{{font-size:11px;color:#8a8a94;margin:2px 0 10px;letter-spacing:.3px;}}
.top-grid{{display:grid;grid-template-columns:minmax(340px,1fr) minmax(260px,300px);gap:14px;align-items:start;}}
table.basic{{width:100%;border-collapse:collapse;}}
table.basic th{{text-align:left;background:#17171b;color:#a8a8b2;padding:5px 10px;width:110px;font-weight:normal;border-bottom:1px solid #2c2c34;vertical-align:top;}}
table.basic td{{padding:5px 10px;border-bottom:1px solid #2c2c34;word-break:break-word;}}
details.basic-detail{{margin-top:8px;}}
details.basic-detail summary{{cursor:pointer;color:#8a8a94;font-size:12px;}}
.art-block{{border:1px solid #34343c;border-radius:6px;background:#1b1b20;padding:12px;margin-bottom:10px;}}
.art-main{{margin:0 0 10px;text-align:center;}}
/* 主图显示比例（2026-10-20 修正）：游戏 UI 控件 640×960=2:3 竖版（followup/REPORT.txt）；
   源 PNG 为 512×512 方形，object-fit:fill 默认拉伸＝游戏 UI 的非均匀缩放行为；whole/icon 维持 1:1 */
.art-main .art-img{{width:min(340px,100%);aspect-ratio:2/3;height:auto;object-fit:fill;}}
.art-strip{{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;}}
.art-thumb{{margin:0;flex:0 1 220px;text-align:center;}}
.art-thumb .art-img{{max-width:200px;max-height:260px;width:auto;}}
.art-caption{{font-size:12px;color:#8a8a94;margin-top:4px;word-break:break-all;}}
.art-bind-detail summary{{cursor:pointer;color:#9a9aa2;font-size:12px;margin-top:2px;}}
.art-bind{{color:#b8b8c2;font-size:12px;margin-top:4px;text-align:left;line-height:1.6;}}
.art-missing .art-caption{{color:#c8c8d0;}}
.art-miss-line{{color:#e8a86c;font-weight:bold;margin:6px 0;}}
.art-tried summary{{cursor:pointer;color:#9a9aa2;font-size:12px;}}
.art-tried ul{{margin:4px 0 0;color:#8a8a94;font-size:12px;padding-left:20px;text-align:left;}}
details.art-audit{{margin-top:8px;}}
details.art-audit summary{{cursor:pointer;color:#9a9aa2;font-size:12px;}}
.external-block{{border:1px solid #34343c;border-radius:6px;background:#1b1b20;padding:14px;text-align:center;}}
.ext-title{{color:#a8a8b2;margin-bottom:8px;}}
.ext-value{{font-size:16px;color:#9a9aa2;letter-spacing:2px;}}
.ext-note{{font-size:12px;color:#7a7a84;margin-top:10px;text-align:left;}}
.badge{{display:inline-block;font-size:11px;padding:1px 7px;border-radius:9px;margin-right:6px;vertical-align:middle;white-space:nowrap;}}
.ev-conf{{background:rgba(70,160,90,.25);color:#7ddc8d;border:1px solid rgba(70,160,90,.5);}}
.ev-conf-ext{{background:rgba(70,160,90,.25);color:#7ddc8d;border:1px dashed rgba(70,160,90,.7);}}
.ev-inf{{background:rgba(220,140,50,.2);color:#e8a86c;border:1px solid rgba(220,140,50,.5);}}
.ev-unk{{background:rgba(130,130,140,.15);color:#9a9aa2;border:1px solid rgba(130,130,140,.4);}}
/* ---- 首屏阅读层级：日文原文为主体，数值 chips 紧随，颜色=证据等级 ---- */
.group{{display:grid;grid-template-columns:110px 1fr;border:1px solid #34343c;border-radius:6px;overflow:hidden;margin:12px 0;}}
.group-label{{background:#101014;color:#c8b06a;padding:12px 8px;text-align:center;font-weight:bold;letter-spacing:2px;}}
.group-body{{background:#222228;padding:4px 12px;}}
.skill{{border-bottom:1px solid #2c2c34;padding:10px 0;}}
.skill:last-child{{border-bottom:none;}}
.skill-head{{margin-bottom:6px;}}
.skill-name{{color:#fff;font-weight:bold;margin-right:12px;}}
.skill-meta{{color:#8a8a94;font-size:12px;}}
.row{{padding:10px 0;border-top:1px dashed #2c2c34;}}
.row-jp{{font-size:17px;line-height:1.7;color:#f2f2f6;margin-bottom:7px;}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;}}
.chip{{display:inline-block;font-size:14px;font-weight:bold;padding:2px 10px;border-radius:4px;line-height:1.5;}}
.chip.ev-conf{{background:rgba(70,160,90,.2);color:#7ddc8d;border:1px solid rgba(70,160,90,.6);}}
.chip.ev-conf-ext{{background:rgba(70,160,90,.2);color:#7ddc8d;border:1px dashed rgba(70,160,90,.75);}}
.chip.ev-inf{{background:rgba(220,140,50,.16);color:#e8a86c;border:1px solid rgba(220,140,50,.55);}}
.chip.ev-unk{{background:rgba(130,130,140,.12);color:#9a9aa2;border:1px solid rgba(130,130,140,.35);font-weight:normal;}}
.chip-tag{{font-size:10px;font-weight:normal;color:#a8d8a8;border:1px dashed rgba(125,220,141,.6);border-radius:3px;padding:0 4px;margin-left:5px;vertical-align:1px;}}
.chip-assoc{{font-size:10px;font-weight:normal;color:#9a9aa2;margin-left:6px;}}
/* H1（20261021 整改）：批 4 条件扩展行首屏 chips 分组——组标签首屏可见、不需展开详情 */
.chip-group{{display:inline-flex;flex-wrap:wrap;gap:6px;align-items:center;margin-right:12px;padding-right:10px;border-right:1px dotted #3c3c46;}}
.chip-group-label{{display:inline-block;font-size:11px;font-weight:normal;color:#c8c8d0;background:#26262e;border:1px solid #3c3c46;border-radius:4px;padding:1px 8px;max-width:420px;white-space:normal;}}
/* ---- 折叠层：全部审计内容，默认收起 ---- */
details.row-detail{{margin-top:5px;}}
details.row-detail summary{{cursor:pointer;color:#8a8a94;font-size:12px;user-select:none;list-style:none;}}
details.row-detail summary::-webkit-details-marker{{display:none;}}
details.row-detail summary::before{{content:'▶';margin-right:5px;font-size:10px;color:#6a6a74;}}
details.row-detail[open] summary::before{{content:'▼';}}
details.row-detail[open] summary{{color:#b8b8c2;}}
details.skill-detail{{margin-top:8px;}}
details.skill-detail summary{{cursor:pointer;color:#6a6a74;font-size:11px;user-select:none;list-style:none;}}
details.skill-detail summary::-webkit-details-marker{{display:none;}}
details.skill-detail summary::before{{content:'▶';margin-right:4px;font-size:9px;color:#5a5a64;}}
details.skill-detail[open] summary::before{{content:'▼';}}
.audit-sec{{margin-top:10px;border-top:1px solid #2c2c34;padding-top:8px;}}
.audit-title{{color:#c8b06a;font-size:12px;margin-bottom:6px;}}
.audit-ans{{border-left:2px solid #34343c;padding-left:10px;margin-bottom:8px;}}
.audit-ans-title{{color:#9a9aa2;font-size:11px;margin-bottom:2px;}}
.kv{{display:flex;gap:10px;font-size:12px;line-height:1.7;align-items:flex-start;}}
.kv-k{{flex:0 0 150px;color:#8a8a94;word-break:break-all;}}
.kv-v{{flex:1;color:#b8b8c2;word-break:break-word;}}
.audit-pre{{margin:2px 0;font-size:11px;line-height:1.5;color:#9aa0aa;background:#17171b;border:1px solid #2c2c34;border-radius:4px;padding:6px 8px;white-space:pre-wrap;word-break:break-all;max-width:100%;overflow-x:auto;}}
.audit-list{{margin:2px 0;padding-left:18px;}}
.empty-groups{{margin:10px 0;}}
.empty-chip{{display:inline-block;background:#1b1b20;border:1px solid #34343c;color:#8a8a94;border-radius:4px;padding:3px 10px;margin:2px 6px 2px 0;font-size:12px;}}
/* ---- 证据等级图例：右上角固定吸顶小卡（滚动跟随）；窄屏回文档流，不溢出 ---- */
.legend{{position:fixed;top:8px;right:8px;z-index:30;width:296px;max-width:calc(100vw - 16px);background:rgba(16,16,20,.96);border:1px solid #34343c;border-radius:6px;padding:8px 10px;font-size:11px;color:#b8b8c2;box-shadow:0 2px 10px rgba(0,0,0,.5);}}
.legend-title{{color:#c8c8d0;font-weight:bold;font-size:12px;margin-bottom:6px;}}
.legend-item{{display:flex;gap:7px;align-items:flex-start;margin:4px 0;line-height:1.55;}}
.legend-item .chip{{flex:0 0 auto;font-size:11px;padding:0 7px;line-height:1.7;}}
.legend-desc{{flex:1;min-width:0;word-break:break-word;}}
.legend-note{{margin-top:6px;padding-top:5px;border-top:1px solid #2c2c34;color:#8a8a94;}}
@media (max-width:760px){{.legend{{position:static;width:auto;max-width:none;margin:0 0 10px;box-shadow:none;}}}}
.footer{{border-top:1px solid #34343c;margin-top:18px;padding-top:12px;}}
.foot-note{{color:#7a7a84;font-size:12px;margin-top:8px;line-height:1.6;}}
h2{{font-size:15px;color:#c8c8d0;margin:18px 0 8px;}}
</style>
</head>
<body>
<div class="topbar">锁链战记 角色技能页 · 数据库样式示例（展示层实验，非正式产物）</div>
<div class="wrap">
{top}
{metrics_line}
{legend}
<div class="top-grid">
<div class="panel">{art_block}<table class="basic">{''.join(basic_trs)}</table>{basic_fold}</div>
<div class="panel">{lv_block}</div>
</div>
<h2>技能（{len(m['groups_present'])} 组有配置）</h2>
{''.join(group_html)}
{empty_html}
{footer}
</div>
</body>
</html>
"""
    return doc, checks


def run_checks(m, doc, checks):
    failures = []
    if len(doc) < 1000:
        failures.append('HTML 过小')
    # 首屏可读性回归：旧审计副行类名必须已消失
    for gone in ('class="ans-sub"', 'class="row-meta"', 'class="row-head"',
                 'card.json 原值：', '｜换算：'):
        if gone in doc:
            failures.append(f'首屏仍残留旧审计副行标记: {gone}')
    # 立绘区自检：base64 非空且在页面中 / 绑定标注文本在页面中（折叠层内）/ 缺失回退正确
    for it in m['art_items']:
        tag = 'art_' + it['kind']
        if it.get('data_uri'):
            if it['data_uri'] not in doc:
                failures.append(f'{tag}: 页面缺少 data URI（base64 为空或未内嵌）')
            if len(it['data_uri']) <= len('data:image/png;base64,'):
                failures.append(f'{tag}: base64 为空')
        else:
            if '本输入快照未取得' not in doc:
                failures.append(f'{tag}: 缺失图未显示「本输入快照未取得」')
            for t in it['tried']:
                if esc(t) not in doc:
                    failures.append(f'{tag}: 页面缺少尝试路径 {t}')
        if esc(it['binding']) not in doc:
            failures.append(f'{tag}: 页面缺少绑定依据标注')
        ratio_note = (DISPLAY_RATIO_NOTE_CARD if it['kind'] == 'main'
                      else DISPLAY_RATIO_NOTES_1_1.get(it['kind']))
        if it.get('data_uri') and ratio_note and esc(ratio_note) not in doc:
            failures.append(f'{tag}: 页面缺少显示比例标注')
        if it.get('extra') and esc(it['extra']) not in doc:
            failures.append(f'{tag}: 页面缺少追加标注')
    # 显示比例（2026-10-20 修正轮）：主图 2:3 竖版缩放 CSS＋页级审计依据文本必须齐全
    if 'aspect-ratio:2/3' not in doc:
        failures.append('主图显示比例 CSS 缺少 aspect-ratio:2/3（2:3 竖版）')
    if esc(DISPLAY_RATIO_AUDIT) not in doc:
        failures.append('页面缺少立绘区审计显示比例依据文本')
    if m['cid'] == 30236:
        if esc(MANIFEST_NOTE_30236) not in doc:
            failures.append('art_manifest: 页面缺少 cid30236 manifest 状态标注')
    for name, needle in checks:
        if not needle or needle == 'None' or needle == '外部/网站维护':
            # 显示为外部/网站维护的行不比对具体值；仅要求页面确实含该占位
            needle = esc(NO_SOURCE)
        if needle not in doc:
            failures.append(f'{name}: 页面缺少期望内容 {needle[:80]}')
    # 行数量核对：每个 row_id 必须恰好出现一次
    d = m['data']
    row_ids = [r['row_id'] for g in m['groups_present'] for sk in g['skills'] for r in sk.get('rows', [])]
    for rid in row_ids:
        if doc.count(f'data-row-id="{esc(rid)}"') != 1:
            failures.append(f'row_id 出现次数不为 1: {rid}')
    # 每行一个「▶ 详情」折叠层；行ID 在折叠层可见文本中
    n_fold = doc.count('<details class="row-detail">')
    if n_fold != len(row_ids):
        failures.append(f'row-detail 折叠数 {n_fold} != 行数 {len(row_ids)}')
    # H1（20261021 整改）：带 condition_label 的批 4 行必须按组显示；组标签首屏可见
    # （与 card_page_render_v2.run_checks 同口径）
    for g in m['groups_present']:
        for sk in g['skills']:
            for r in sk.get('rows', []):
                labels = sorted({a['condition_label'] for a in r.get('answers', [])
                                 if a.get('condition_label')})
                if not labels:
                    continue
                if '<span class="chip-group">' not in doc:
                    failures.append(f'批4行 chips 未分组显示: {r.get("row_id")}')
                for cl in labels:
                    if f'<span class="chip-group-label">条件：{esc(cl)}</span>' not in doc:
                        failures.append(f'批4行缺少条件组标签: {r.get("row_id")}: {cl[:40]}')
    for rid in row_ids:
        if f'<span class="kv-v">{esc(rid)}</span>' not in doc:
            failures.append(f'折叠层缺少行ID可见文本: {rid}')
    # 无信息丢失：折叠层必须含规则键 / card.json 原值 / 证据目录 / 适用范围 / 未知原因全文
    for g in m['groups_present']:
        for sk in g['skills']:
            for r in sk.get('rows', []):
                for u in (r.get('unknown_reasons') or []):
                    if esc(u) not in doc:
                        failures.append(f'折叠层缺少未知原因全文: {r.get("row_id")}: {u[:40]}')
                for item in (r.get('evidence_scope') or []):
                    if isinstance(item, str) and esc(item) not in doc:
                        failures.append(f'折叠层缺少行适用范围: {item}')
                for a in r.get('answers', []):
                    for key in ('rule_key', 'evidence', 'evidence_scope', 'raw_value',
                                'conditions', 'conversion'):
                        v = a.get(key)
                        if v is None or v == '' or v == []:
                            continue
                        if isinstance(v, list):
                            for x in v:
                                if isinstance(x, str) and esc(x) not in doc:
                                    failures.append(f'折叠层缺少答案.{key} 项: {x[:40]}')
                        elif esc(v) not in doc:
                            failures.append(f'折叠层缺少答案.{key}: {str(v)[:40]}')
    # 汇总数核对：模型 A/C 行数与 summary 一致；未知灰 chip 至少覆盖每个 C 行
    a_cnt = sum(1 for g in m['groups_present'] for sk in g['skills'] for r in sk.get('rows', []) if r.get('row_class') == 'A')
    c_cnt = sum(1 for g in m['groups_present'] for sk in g['skills'] for r in sk.get('rows', []) if r.get('row_class') == 'C')
    s = d.get('summary', {})
    if a_cnt != s.get('A', {}).get('count'):
        failures.append(f'A 行数 {a_cnt} != summary.A.count {s.get("A", {}).get("count")}')
    if c_cnt != s.get('C', {}).get('count'):
        failures.append(f'C 行数 {c_cnt} != summary.C.count {s.get("C", {}).get("count")}')
    unk_chip_cnt = doc.count('<span class="chip ev-unk"')
    if unk_chip_cnt < c_cnt:
        failures.append(f'未知灰 chip 数 {unk_chip_cnt} < C 行数 {c_cnt}')
    # 图例自检：图例块存在于首屏（第一个折叠层之前，即不在任何 details 内）；
    # 四档定义与提示语各恰好出现一次
    legend_start = doc.find('<!-- legend:start -->')
    legend_end = doc.find('<!-- legend:end -->')
    if legend_start == -1 or legend_end == -1:
        failures.append('页面缺少证据图例块（legend 标记未找到）')
    else:
        legend_block = doc[legend_start:legend_end + len('<!-- legend:end -->')]
        first_details = doc.find('<details')
        if first_details != -1 and legend_start > first_details:
            failures.append('图例位于第一个折叠层之后（应首屏可见、不在折叠层内）')
        for label, _cls, desc in LEGEND_DEFINITIONS:
            if doc.count(esc(desc)) != 1:
                failures.append(f'图例定义出现次数!=1: {label}: {desc[:30]}')
        if doc.count(esc(LEGEND_NOTE)) != 1:
            failures.append('图例提示语出现次数!=1')
        # 图例内四档 chip 类名齐全（绿实/绿虚/橙/灰各一）
        for _label, cls, _desc in LEGEND_DEFINITIONS:
            if f'<span class="chip {cls}">' not in legend_block:
                failures.append(f'图例缺少 chip 类名: {cls}')
    return failures


def main():
    ap = argparse.ArgumentParser(description='数据库样式示例渲染器（展示层实验）')
    ap.add_argument('--cids', default=','.join(map(str, DEFAULT_CIDS)))
    ap.add_argument('--pages-dir', default=str(DEFAULT_PAGES))
    ap.add_argument('--out-dir', default=str(DEFAULT_OUT))
    args = ap.parse_args()
    pages_dir = Path(args.pages_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cids = [int(c) for c in args.cids.split(',') if c.strip()]
    ok = True
    for cid in cids:
        m = build_model(cid, pages_dir)
        doc, checks = render_html(m)
        failures = run_checks(m, doc, checks)
        out = out_dir / f'{cid}.html'
        if failures:
            ok = False
            print(f'[FAIL] cid {cid}: {len(failures)} 项不一致')
            for f in failures[:20]:
                print('   -', f)
            continue
        out.write_text(doc, encoding='utf-8')
        d = m['data']
        s = d.get('summary', {})
        n_answers = sum(len(r.get('answers', [])) for g in m['groups_present'] for sk in g['skills'] for r in sk.get('rows', []))
        n_infer = sum(1 for g in m['groups_present'] for sk in g['skills'] for r in sk.get('rows', [])
                      for a in r.get('answers', []) if a.get('numeric_evidence') == '推断')
        print(f'[OK] cid {cid} -> {out.relative_to(ROOT).as_posix()} '
              f'({len(doc)} 字节; 行 {s.get("A", {}).get("count")}A/{s.get("C", {}).get("count")}C/'
              f'{s.get("N_num")}总; 整行确认 {s.get("whole_row_confirmed", {}).get("count")}; '
              f'原文A {s.get("original_A", {}).get("count")}; 答案行 {n_answers} (推断 {n_infer}); '
              f'自检 {len(checks)} 项 + 行数/折叠/审计核对通过)')
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
