# -*- coding: utf-8 -*-
"""正式 2236 页玩家视角版式渲染层（2026-10-20 版式迁移定稿）。

版式来源：output/character_skills/dbstyle_samples/DESIGN.md 与三张定稿示例
（30236/7616/10001.html，渲染器 card_page_dbstyle_sample.py）；用户已确认定稿
（「暂时按这个来搞」）。本模块把该版式推广为正式主渲染层，经 card_page_batch.py
受控接入（`from card_page_render_v2 import page`）；旧 card_page_render.py 保留，
仅供 11 卡试点入口（card_page.py）与历史产物对照，不再被 batch 使用。

与定稿示例一致的版式要素：
- 首屏阅读层级：卡名行（CID/卡名/称号/★/COST）→ 四联指标一行小字 → 立绘区
  （主图＋小图条带）→ 基础信息表（值＋证据徽章）→ 13 组技能区（阅读主体）；
- 每条描述行＝日文原文（17px 视觉主体）＋紧随的数值 chips；chip 颜色即证据等级：
  确认=绿实、确认（类型外推）=绿虚框＋「外推」小字、推断=橙、未知=灰（显示「未知」）；
  附加小字：「关联未知」（数值确认但字段关联未证）；
- 右上角固定吸顶图例（四档讲人话定义＋提示语；窄屏 ≤760px 媒体查询回退文档流），
  `<!-- legend:start/end -->` 标记包围，位于页面第一个 <details> 之前；
- 13 组导航保留（无配置组显示「本输入快照未关联」）；
- 全部审计内容入折叠层（默认收起，信息一条不删）：每行一个「▶ 详情」（通用渲染
  该行/答案全部键——规则键/card.json 原值/证据目录/适用范围/来源指针/条件/
  unknown_reasons 全文/绑定条件/多段披露/上下文全文等，不设白名单）；每个技能一个
  「▶ 技能记录审计」；基础信息证据细节、立绘绑定标注、立绘区审计、页脚来源映射
  各自折叠；intro 说明文字（推断层口径、日文短语对照、指标方法）折叠但不删除。

与定稿示例的差异（仅技术载体，版式不变）：
- 立绘改为从 pages/art/<cid>/{card,whole,icon}.png 相对路径引用（不 base64，
  控制页面体积）；art 文件由本模块 `--copy-art` 从 output/full_unpack/objects/
  {Card_OrgSize,Trimmed_Whole,Card_Icon}/cha_2d_*_<cid>/ 复制；
- 主图显示比例（2026-10-20 修正轮）：Card_OrgSize 存储 512×512 方形，但游戏 UI 控件
  640×960＝2:3 竖版（followup/REPORT.txt，APK prefab 最小序列化前缀解析），故主图按
  2:3 非均匀缩放显示（aspect-ratio:2/3，object-fit:fill＝游戏 UI 行为）；whole/icon
  维持 1:1；逐图绑定标注与立绘区审计含显示比例依据文本；
- 页脚/顶栏改为正式产物声明；数据仍全部来自 card.json 原值，证据等级不升级、
  不删除，只收起；无来源区域沿用「外部/网站维护」惯例，不编造数值。

兼容钩子（card_page.validate 结构自检依赖）：行容器带 data-row-id/data-row-class/
data-evidence（按此属性顺序）、日文原文为独立的 <p class="jp">、13 组 section 带
data-group、页面内嵌 <script type="application/json" id="card-data">（=card）。

绑定依据统一文案（与定稿示例一致）：命名规则绑定：CharacterFactory.
GetCharaTextureName* 方法证据（cid 计算纹理名），见
output/card_images/cid30236/binding_evidence.json；解包台账
output/full_unpack/ledger.jsonl。cid30236 另按
output/card_images/cid30236/manifest.json 如实标注（头像 CONFIRMED、全身未定位、
局部立绘已导出）。缺图 cid 显示「本输入快照未取得」并列出尝试路径，不借图。
"""
import argparse
import html
import json
import shutil
import sys
from pathlib import Path

from card_page_policy import summary_text, INFERENCE_STATUS
# P3（目标整改 §三.4/A8，20261023）：行首屏同句呈现未解决效果——判定与效果账本同源
# （effect_ledger.analyze_row 单一事实来源），未解决不呈现为完整、推断不呈现为确认。
import effect_ledger as EFFECT_LEDGER

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PAGES = ROOT / 'output' / 'character_skills' / 'pages'
ART_SRC = ROOT / 'output' / 'full_unpack' / 'objects'

NO_SOURCE = '外部/网站维护'
BINDING_EVIDENCE_REL = 'output/card_images/cid30236/binding_evidence.json'
LEDGER_REL = 'output/full_unpack/ledger.jsonl'
BINDING_TEXT = ('命名规则绑定：CharacterFactory.GetCharaTextureName* 方法证据'
                '（cid 计算纹理名），见 ' + BINDING_EVIDENCE_REL +
                '；解包台账 ' + LEDGER_REL)
MANIFEST_REL_30236 = 'output/card_images/cid30236/manifest.json'
MANIFEST_STATUS_30236 = 'PORTRAIT_CONFIRMED_FULL_BODY_NOT_LOCATED_PARTIAL_ART_EXPORTED'
# cid -> kind -> 追加标注（仅转述已核实的 manifest 内容，不外推；与定稿示例一致）
ART_EXTRA_ANNOT = {
    30236: {
        'card': 'cid30236 manifest 标注该卡面为 CARD_VARIANT_CONTAINER_AND_VISUAL_MATCH'
                '（原图含龙、背景、卡框、标题及星级烘焙，不是独立立绘）',
        'whole': 'cid30236 manifest 标注为 CONFIRMED_CLIENT_ID_BINDING，但该图是'
                 '「原始透明上半身图；画面边缘截断身体及装饰，不是完整全身立绘」',
        'icon': 'cid30236 manifest 标注为 CONFIRMED_CLIENT_ID_BINDING（头像；'
                '卡框与星级已烘焙在原始纹理中）',
    },
}
MANIFEST_NOTE_30236 = (
    'cid30236 manifest 状态（' + MANIFEST_REL_30236 + '）：' + MANIFEST_STATUS_30236
    + '——头像 CONFIRMED_CLIENT_ID_BINDING；全身未定位、局部立绘已导出。'
      '本页整卡与局部图均按命名规则绑定标注，不视为全身体已确认。')
# 显示比例依据（2026-10-20 修正轮）：卡面纹理存储 512×512 方形，但游戏 UI 显示为 2:3 竖版。
# 证据：output/card_images/cid30236/followup/REPORT.txt——CharaInfoCard._cardTexture 指向
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
    """(kind, full_unpack 对象目录, 源文件名, pages/art 目标文件名, 页面标签)。"""
    return [
        ('card', f'Card_OrgSize/cha_2d_card_{padded}', f'cha_2d_card_{padded}.png',
         'card.png', '主图｜整卡 Card_OrgSize'),
        ('whole', f'Trimmed_Whole/cha_2d_whole_{padded}', f'cha_2d_whole_{padded}.png',
         'whole.png', 'Trimmed_Whole 全身'),
        ('icon', f'Card_Icon/cha_2d_icon_{padded}', f'cha_2d_icon_{padded}.png',
         'icon.png', 'Card_Icon 头像'),
    ]


def art_model(cid):
    """逐条目立绘模型：相对路径引用（不 base64）；缺失时如实记录尝试路径，不借图。"""
    padded = str(cid).zfill(5)
    extras = ART_EXTRA_ANNOT.get(cid, {})
    items = []
    for kind, subdir, fname, dest, label in art_kinds(padded):
        src_rel = f'output/full_unpack/objects/{subdir}/{fname}'
        dest_rel = f'output/character_skills/pages/art/{cid}/{dest}'
        item = dict(kind=kind, label=label, src_rel=src_rel, dest_rel=dest_rel,
                    url=f'../art/{cid}/{dest}', binding=BINDING_TEXT,
                    extra=extras.get(kind), tried=[])
        src_path = ROOT / src_rel
        if src_path.is_file():
            item['bytes'] = src_path.stat().st_size
        else:
            item['tried'] = [src_rel, src_rel.rsplit('/', 1)[0] + '/objects_index.json']
        items.append(item)
    return items


def copy_art(cids, pages_dir):
    """从 full_unpack objects 复制立绘 PNG 到 pages/art/<cid>/；返回统计。"""
    pages_dir = Path(pages_dir)
    counts = dict(card=0, whole=0, icon=0)
    missing = {k: [] for k in counts}
    total_bytes = 0
    for cid in cids:
        padded = str(cid).zfill(5)
        for kind, subdir, fname, dest, _label in art_kinds(padded):
            src = ROOT / 'output' / 'full_unpack' / 'objects' / subdir / fname
            target = pages_dir / 'art' / str(cid) / dest
            if src.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.is_file() or target.stat().st_size != src.stat().st_size:
                    shutil.copy2(src, target)
                counts[kind] += 1
                total_bytes += target.stat().st_size
            else:
                missing[kind].append(cid)
    return dict(counts=counts, missing=missing, total_bytes=total_bytes,
                directories=len(list((pages_dir / 'art').glob('[0-9]*'))))


def esc(v):
    return html.escape('' if v is None else str(v), quote=True)


def pretty(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


# ---- 基础信息表：全部 basic.fields（不设子集，信息一条不删） ---------------------------
def basic_field_lookup(basic):
    out = {}
    for f in basic.get('fields', []):
        out.setdefault(f.get('key'), f)
    return out


def field_display(f):
    value = '缺失' if f['raw_state'] == 'missing' else 'null' if f['raw_state'] == 'null' else f['raw_value']
    value = f.get('display_value', value)
    if isinstance(value, (list, dict)):
        value = pretty(value)
    return value


def badge(label, cls=None):
    cls = cls or EVID_CLASS.get(label, 'ev-unk')
    return f'<span class="badge {cls}">{esc(label)}</span>'


def row_evidence_label(row):
    """行级证据展示：确认 / 确认（类型外推）/ 确认（部分类型外推）/ 推断 / 未知；
    模板推断行沿用行级 evidence_label（如「推断（模板批 4 条件扩展）」）。"""
    ev = row.get('evidence')
    if row.get('evidence_label'):
        return row['evidence_label']
    if ev == '确认':
        return scope_confirm_label(ev, row.get('evidence_scope') or [])
    return ev if ev == '推断' else '未知'


def scope_confirm_label(evidence, scopes):
    """H-01 口径：REVIEWED_RECORD=确认；全 BY_TYPE_EXTRAPOLATED=确认（类型外推）；
    混合=确认（部分类型外推）。判定不降级，仅披露 scope。"""
    if evidence != '确认':
        return evidence
    scope_list = [str(s) for s in (scopes or []) if s]
    if not scope_list or all(s == 'REVIEWED_RECORD' for s in scope_list):
        return evidence
    if all(s == 'BY_TYPE_EXTRAPOLATED' for s in scope_list):
        return '确认（类型外推）'
    return '确认（部分类型外推）'


EVID_CLASS = {'确认': 'ev-conf', '确认（类型外推）': 'ev-conf-ext', '确认（部分类型外推）': 'ev-conf',
              '推断': 'ev-inf', '未知': 'ev-unk'}


# ---- 证据等级图例（定稿第四轮）：讲人话定义；口径与 card.json 四档标注一致，不改判 ----
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


# ---- 折叠层（审计）：通用键值渲染，全部键保留，不删除任何证据信息 ----
ROW_AUDIT_LABELS = {
    'row_id': '行ID', 'cid': 'CID', 'group': '组', 'stage': '档位', 'level': '等级',
    'reference_field': '引用字段', 'fragment_index': '片段序号', 'context_text': '上下文全文（多段披露）',
    'row_class': '行类别', 'original_numeric_items': '原文数字项', 'original_A': '原文A行',
    'evidence': '行证据', 'numeric_evidence': '数值证据', 'association_evidence': '关联证据',
    'evidence_label': '行证据标签', 'partial': '部分解释', 'unknown_reasons': '未知原因全文',
    'source': '来源指针', 'raw_value_states': '原值状态', 'raw_state_summary': '原值状态摘要',
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
    'inference_b8': '推断层元数据（批8 暴击 2012 链）', 'inference_b8_hint': '批8 hint',
    'inference_b9': '推断层元数据（批9 敵デバフ ability99 载体）', 'inference_b9_hint': '批9 hint',
    'inference_b10': '推断层元数据（批10 SA2003 载体）', 'inference_b10_hint': '批10 hint',
    'inference_b11': '推断层元数据（批11 自身增益 1095）', 'inference_b11_hint': '批11 hint',
    'inference_b12': '推断层元数据（批12 1095 扩域）', 'inference_b12_hint': '批12 hint',
    'inference_b13': '推断层元数据（批13 APK 扩域）', 'inference_b13_hint': '批13 hint',
    'inference_b14': '推断层元数据（批14 APK 扩域第二批）', 'inference_b14_hint': '批14 hint',
    'inference_b15': '推断层元数据（批15 并集归属：t13 槽∪2012 暴击链）',
    'inference_b15_hint': '批15 并集归属未成立（具体缺口）',
    'inference_b17': '推断层元数据（批17 P0 收尾：槽位分区/时长槽共享/denju patternid 映射）',
    'inference_b17_hint': '批17 P0 收尾未成立（具体缺口）',
    'same_cond_alt_t13': '同 HP 条件组其余 pattern→t13 分支披露（R1-High 复审整改；原值逐字＋选取维度未解析待办）',
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
    'evidence_paths': '证据路径件', 'mapping_note': '映射备注', 'condition': '条件（原文数字项）',
}
SKILL_AUDIT_LABELS = {
    'skill_id': '技能ID', 'name': '名称', 'original_group': '原始组', 'record_id': '记录ID',
    'table': '表', 'layer': '层', 'source': '来源', 'text_field': '文本字段',
    'original_text': '技能原文全文', 'reference_field': '引用字段', 'cost': '费用',
    'cost_state': '费用状态', 'record_evidence': '记录证据', 'forward_links': '前向链接',
    'old_rec_key': '旧记录键', 'link_status': '链接状态',
    'baseline_metadata_answers': '基线元数据答案', 'association_evidence': '关联证据',
    'level_note': '等级说明', 'level_state': '等级状态', 'stage': '档位', 'level': '等级',
    'rows': '描述行', 'alias_row_ids': '别名行ID', 'empty_reason': '空行原因',
    'internal_label': '内部标签',
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
        return '<pre class="audit-pre">' + esc(pretty(val)) + '</pre>'
    return esc(val)


def render_audit(obj, labels, skip=()):
    """通用审计渲染：按对象全部键输出 kv 行；空值跳过（信息不丢，原 JSON 中本就为空）。"""
    parts = []
    for k, v in obj.items():
        if k in skip or v is None or v == '' or v == [] or v == {}:
            continue
        label = labels.get(k, k)
        if k == 'rule_status' and isinstance(v, str):
            # B5-R01（批5审查）：值行证据=「推断」的语境里裸露规则级「已确认」字样会产生
            # 「本值已确认」的归属歧义——显示为规则级限定口径；card.json 数据层保留 rules.json
            # 原值（字段语义＝该规则键的规则级状态，可由 rule_key 反查），不触动数据。
            v = f'规则级状态（规则本体{v}；不代表本值归属确认）'
        parts.append(f'<div class="kv"><span class="kv-k">{esc(label)}</span>'
                     f'<span class="kv-v">{audit_value_html(v)}</span></div>')
    return ''.join(parts)


def answer_chip(a, row):
    """首屏数值 chip：颜色即证据等级；数值文案保持现有换算结果。"""
    val = a.get('value')
    nev = a.get('numeric_evidence') or '未知'
    scope = a.get('evidence_scope')
    if isinstance(scope, str):
        scope = [scope]
    scope = list(scope or []) + list(row.get('evidence_scope') or [])
    label = scope_confirm_label(nev, scope) if nev == '确认' else nev
    cls = EVID_CLASS.get(label, 'ev-unk')
    if cls == 'ev-unk' or not val:
        # 未知：灰 chip 显示「未知」（原值/原因在折叠层）
        return '<span class="chip ev-unk" title="证据：未知">未知</span>'
    body = esc(val)
    if cls == 'ev-conf-ext':
        body += '<span class="chip-tag">外推</span>'
    if a.get('association_evidence') == '未知' and nev == '确认':
        # L1（20261021 独立审查整改）：原文数字 chip 追加「原文已写」小字，与「关联未知」
        # 并存——绿色只表示原文逐字确认，不表示参数归属已确认；确认/类型外推/推断/未知
        # 四档语义不变。限定 numeric_source='原文'（基线答案不标）。
        body += '<span class="chip-assoc">关联未知</span>'
        if a.get('numeric_source') == '原文':
            body += '<span class="chip-assoc">原文已写</span>'
    return f'<span class="chip {cls}" title="证据：{esc(label)}">{body}</span>'


def chip_groups_html(answers, row):
    """H1（20261021 独立审查整改）：批 4 条件扩展行的首屏 chips 分组显示。

    带结构化 condition_label（批 4 条件增幅值行，逐字条件原文）的答案按条件值分组；
    无 condition_label 的答案（基础句值行）归「基础」组。组标签首屏可见、不需展开详情；
    组内按原 answers 顺序；同行多个不同条件（理论上不出现——批 4 单条件链）分别分组。
    不合并数值、不改证据等级；无 condition_label 的行维持原样（不引入分组）。
    """
    if not any(a.get('condition_label') for a in answers):
        return ''.join(answer_chip(a, row) for a in answers)
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
                     + ''.join(answer_chip(a, row) for a in base) + '</span>')
    for cl in cond_order:
        parts.append('<span class="chip-group"><span class="chip-group-label">条件：'
                     + esc(cl) + '</span>'
                     + ''.join(answer_chip(a, row) for a in cond_groups[cl]) + '</span>')
    return ''.join(parts)


_UNRES_FLAG_SHORT = {
    'S1_zero_claims': '词表未识别出效果主张（不能排除词表外效果）',
    'S2_unconfirmed_numbers': '原文数字语义未确认（如次数/阈值；含主张子句内数字——R2 整改）',
    'S3_uncovered_clauses': '存在未被效果主张覆盖的子句（定性机制待核查）',
    'S3b_residual_mechanisms': '正文含词表外机制词且无答案覆盖（状态异常等待核查——R2 整改）',
    'S4_unconsumed_typed_answers': '存在未对应句面主张的答案（归属缺口）',
    'S5_hp_branch_coverage': 'HP 档位分支覆盖不完整（R1 整改）',
    'S5_hp_variation_unbound': '「随HP变化」句的增益答案缺 HP 档位绑定（R1 整改）',
    'S6_unresolved_conditions': '概率类条件无载体映射与解析状态（R2 整改）',
    'S7_same_cond_alt_t13': '同 HP 条件组内其余 pattern→t13 值不同、选取维度未解析（R1-High 复审整改）',
}


def unresolved_effects_html(row):
    """P3（目标整改 §三.4/A8）：首屏同句呈现仍未解决的效果——可读短句列表；
    判定与效果账本 effect_ledger.analyze_row 同源（单一事实来源）。
    未解决不呈现为完整（不使用数值 chip 样式）；推断不呈现为确认（证据档颜色不变，
    已解释效果仍由 chips 呈现）。纯定性 NA 判定与已回答效果不出现在此。"""
    res = EFFECT_LEDGER.analyze_row(row)
    parts = []
    for e in res['effects']:
        if e['status'] != 'unresolved':
            continue
        etype = e['effect_type']
        dirword = {'up': '上升', 'down': '下降'}.get(e['direction'], '')
        # R4（DS-GR-R1/R4 修复，20261023 复验）：ダメージ 类未解决主张标注对象维度
        # （自身/敵）——与账本 effect.object 同源，供 verify_full 第 15 项内容级核对，
        # 读者可分辨自伤/敌方伤害（对象不可判时不标注）。
        objmark = ''
        if etype in EFFECT_LEDGER._DAMAGE_TYPES and e.get('object'):
            objmark = '（自身）' if e['object'] == 'self' else '（敵）'
        if etype in EFFECT_LEDGER._OUTSIDE_TYPES:
            cand = '效果类型在当前词表外，待语义核查'
        elif res['breakpoint']:
            cand = '候选 bossskill type13 槽（并集归属），核查中'
        elif row.get('inference_b15_hint'):
            cand = '并集归属未成立（见批15 hint），核查中'
        elif row.get('inference_b17_hint'):
            cand = '批17 收尾归属未成立（见批17 hint），核查中'
        else:
            cand = '候选来源定位中'
        parts.append(f'未解：{etype}{dirword}{objmark}（{cand}）')
    for f in res['split_flags']:
        parts.append('拆分待核查：' + _UNRES_FLAG_SHORT.get(f['code'], f['code']))
    if not parts:
        return ''
    items = ''.join(f'<span class="unres-item">{esc(p)}</span>' for p in parts)
    return (f'<div class="unresolved-effects" data-unresolved="{len(parts)}">'
            f'<span class="unres-title">仍未解决（{len(parts)}）</span>{items}</div>')


def render_row(row):
    """首屏＝日文原文＋数值 chips＋未解决效果短句；全部审计内容收入单个 <details>（默认收起）。"""
    rid = row.get('row_id', '')
    answers = row.get('answers', [])
    if answers:
        chips = chip_groups_html(answers, row)
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
    return (f'<div class="row" data-row-id="{esc(rid)}" data-row-class="{esc(row["row_class"])}"'
            f' data-evidence="{esc(row["evidence"])}">'
            f'<p class="jp" lang="ja">{esc(row.get("japanese", ""))}</p>'
            f'<div class="chips">{chips}</div>{unresolved_effects_html(row)}{fold}</div>')


def render_skill(skill):
    meta = []
    if skill.get('cost') is not None and skill.get('cost_state') not in ('missing', 'null'):
        meta.append('费用 ' + esc(skill['cost']))
    if skill.get('stage'):
        meta.append(esc(skill['stage']))
    if skill.get('level') is not None:
        meta.append('Lv ' + esc(skill['level']))
    name_html = esc(skill.get('name') or '（无名称）')
    rows_html = ''.join(render_row(r) for r in skill.get('rows', []))
    if not skill.get('rows'):
        rows_html = f'<div class="empty">{esc(skill.get("empty_reason") or "本输入快照无描述行")}</div>'
    # 技能级记录审计（original_text / record_evidence / forward_links / baseline_metadata_answers
    # 等）收入折叠；通用渲染全部键（rows 除外）。
    skill_fold = (f'<details class="skill-detail"><summary>▶ 技能记录审计</summary>'
                  f'{render_audit(skill, SKILL_AUDIT_LABELS, skip=("rows",))}</details>')
    return (f'<article class="skill"><header class="skill-head"><span class="skill-name">{name_html}</span>'
            f'<span class="skill-meta">{"｜".join(meta)}</span></header>{rows_html}{skill_fold}</article>')


def build_basic_rows(data):
    """基础信息表全部字段＋external；折叠层用逐字段全键 JSON。"""
    basic = data.get('basic', {})
    rows = []
    for f in basic.get('fields', []):
        rows.append((f.get('label') or f.get('key'), field_display(f),
                     f.get('evidence') or '未知', f))
    return rows, basic.get('card_art', {}), basic.get('external', [])


def render_html(card):
    cid = card['cid']
    basic = card['basic']
    fields = basic_field_lookup(basic)
    cov = card['coverage']
    name_f = fields['name']
    name = name_f['raw_value']
    title_f = fields['title']
    # R-07/S-01：称号缺失/null/空字符串按缺失口径显示 display_value，不渲染空标题。
    title = title_f['raw_value'] if title_f['raw_state'] in ('present', 'zero') and title_f['raw_value'] not in ('', None) \
        else (title_f.get('display_value') or '称号未知')
    rarity = fields['rarity']['raw_value']
    cost = fields['cost']['raw_value']
    cost_state = fields['cost']['raw_state']
    stars = ('★' * int(rarity)) if isinstance(rarity, int) and rarity > 0 else NO_SOURCE
    top = (f'<div class="card-top"><div class="title-line">'
           f'<span class="cid">CID {cid}</span>'
           f'<span class="card-name" lang="ja">{esc(name)}</span>'
           f'<span class="card-title" lang="ja">{esc(title)}</span></div>'
           f'<div class="sub-line"><span class="stars">{esc(stars)}</span>'
           f'<span class="cost">COST {esc(cost) if cost is not None and cost_state not in ("missing", "null") else esc(NO_SOURCE)}</span>'
           f'<span class="layer">{esc(basic.get("layer", ""))} · 声明输入版本</span></div></div>')
    # 四联指标：压缩为一行小字（A 数值/公式行｜整行确认｜原文A｜C 仅未知）
    metric_bits = []
    for key, label in (('A', 'A 数值/公式行'), ('whole_row_confirmed', '整行确认'),
                       ('original_A', '原文A'), ('C', 'C 仅未知')):
        mm = card['summary'][key]
        metric_bits.append(f'{esc(label)} {mm["count"]}/{mm["denominator"]}')
    metrics_line = '<div class="metrics-line">指标：' + '｜'.join(metric_bits) + '</div>'
    legend = build_legend()
    # intro 折叠：推断层口径/指标方法/审查指针（原 intro 全文，收起不删）
    intro = (f'<details class="intro-detail"><summary>▶ 阅读说明与推断层口径（指标方法/审查状态）</summary>'
             f'<p class="small intro-text">每行保留日文原文。A＝数值／公式，B＝新增机制，C＝仅未知。'
             f'数值证据与字段关联分别标注；原文数字不代表已证实参数归属。'
             f'整行确认＝该行全部答案的字段关联均为「确认」（任一答案关联未知——含全部原文数字答案——即不计整行确认；'
             f'该行显示「字段／描述关联：未知」）。整行确认分两类口径：记录级 REVIEWED_RECORD'
             f'（逐记录审定的既有逐描述证据）与类型外推 BY_TYPE_EXTRAPOLATED（冻结模板按同类型记录推广，'
             f'无逐记录人工审定）；后者在本页 chip 显式标注「确认（类型外推）」，不与记录级混用。'
             f'模板作用域推断层（批1 type1017 试点／批3 type8 严格子集／批4 条件扩展双记录映射）：'
             f'只升「推断」档，行级标注「推断（模板…）」，不使用「确认」字样、不进入整行确认，'
             f'审核未通过或有疑点的同句行留 hint 维持 C。范围与留 hint 规则见 '
             f'<a href="../README.md">pages/README.md §13、§14、§15、§16</a>。'
             f'原文A＝答案来自该行日文原文明确写出的数字（不代表参数归属已证）。'
             f'指标方法见 <a href="../../r2_preparation/README.md">r2_preparation/README.md</a>。'
             f'独立审查状态与逐行审查队列不在本目录：见 <code>pages/_batch/&lt;cohort&gt;/latest.json</code> '
             f'所指运行目录的 cohort_report.md 与 audit_queue.json；本目录仅含 card.json、index.html、receipt.json。</p>'
             f'<p class="small intro-text">{esc(INFERENCE_STATUS["message"] + "；" + INFERENCE_STATUS["zero_inference_meaning"] + "。B=0：" + INFERENCE_STATUS["B_zero_reason"])}</p>'
             f'<p class="small intro-text">「条件：…」、对象／所属前缀、付与注记、值行括注中出现的日文短语，'
             f'均为该行日文原文的同句逐字引用；逐字性是证据标签的一部分，本页不翻译、不改写。'
             f'常见短语对照（仅为阅读辅助，不改变证据口径）：状態異常の敵がいると＝当有异常状态的敌人时；'
             f'敵陣にいると＝处于敌阵时；敵陣の奥に行く程＝越深入敌阵；ボスWAVE時＝Boss wave 时；'
             f'地形が砂浜/船上/海中の時＝地形为沙滩／船上／海中时；年代記の力を発動した時＝发动年代记之力时；'
             f'N人以上で同じ敵を攻撃すると＝当N人以上攻击同一敌人时；'
             f'自身がヒロイックスキルに設定されていると＝当自身被设定为英雄技（ヒロイックスキル）时；'
             f'戦場にいる味方＝战场上的我方；メインパーティの〈…〉所属＝主队伍中〈…〉所属；'
             f'味方全体＝我方全体；1stキャラクターに付与＝赋予1st角色。</p></details>')
    # 基础信息表：值＋证据徽章在首屏；逐字段证据/备注/全键 JSON 收入页面级一个折叠
    basic_trs = []
    basic_fold_kvs = []
    basic_rows, art, external = build_basic_rows(card)
    for label, disp, ev, f in basic_rows:
        ev_badge = badge(NO_SOURCE if disp == NO_SOURCE else (ev or '未知'))
        if ev == '确认' and disp != NO_SOURCE:
            ev_badge = badge('确认')
        basic_trs.append(f'<tr><th>{esc(label)}</th><td>{esc(disp)} {ev_badge}</td></tr>')
        basic_fold_kvs.append(
            f'<div class="kv"><span class="kv-k">{esc(label)}</span><span class="kv-v">'
            f'证据：{esc(ev or "未知")}｜{esc(f.get("note") or "")}'
            f'<pre class="audit-pre">{esc(pretty(f))}</pre></span></div>')
    basic_fold = (f'<details class="basic-detail"><summary>▶ 基础信息证据细节（逐字段证据/备注/全键）</summary>'
                  f'{"".join(basic_fold_kvs)}</details>')
    ext_pills = ''.join(f'<span class="pill">{esc(item["label"])}：{esc(item["value"])}</span>'
                        for item in external)
    # 立绘区：pages/art 相对路径引用（不 base64）；绑定标注/审计收入折叠
    art_items = art_model(cid)
    main_items = [it for it in art_items if it['kind'] == 'card']
    strip_items = [it for it in art_items if it['kind'] != 'card']
    art_html_parts = []
    for it in main_items + strip_items:
        cls = 'art-main' if it['kind'] == 'card' else 'art-thumb'
        if it.get('bytes') is not None:
            bind_bits = [f'文件：{esc(it["src_rel"])}（{it["bytes"]} 字节 PNG）',
                         f'本页引用：{esc(it["dest_rel"])}（相对路径，不内嵌）',
                         f'绑定依据：{esc(it["binding"])}']
            ratio_note = (DISPLAY_RATIO_NOTE_CARD if it['kind'] == 'card'
                          else DISPLAY_RATIO_NOTES_1_1.get(it['kind']))
            if ratio_note:
                bind_bits.append(esc(ratio_note))
            if it.get('extra'):
                bind_bits.append(esc(it['extra']))
            art_html_parts.append(
                f'<figure class="{cls}">'
                f'<img class="art-img" src="{it["url"]}" alt="{esc(it["label"])} (cid {cid})">'
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
    art_audit_bits = []
    # 绑定口径页级说明（全部页统一；有图页逐图另有「▶ 绑定标注」折叠）：
    # full_unpack 解包产物按命名规则绑定复制到 pages/art/；未取得的图不借用其他 cid 的图。
    art_audit_bits.append(f'<div class="art-bind">立绘取用与绑定口径：'
                          f'CharacterFactory.GetCharaTextureName* 方法证据（cid 计算纹理名），'
                          f'完整依据见 {esc(BINDING_EVIDENCE_REL)}；解包台账 {esc(LEDGER_REL)}。'
                          f'full_unpack 解包产物（output/full_unpack/objects/'
                          f'{{Card_OrgSize,Trimmed_Whole,Card_Icon}}/cha_2d_*_&lt;cid&gt;/）'
                          f'按命名规则绑定复制到 pages/art/&lt;cid&gt;/；'
                          f'缺图 cid 显示「本输入快照未取得」并列出尝试路径，不借用其他 cid 的图。</div>')
    art_audit_bits.append(f'<div class="art-bind">{esc(DISPLAY_RATIO_AUDIT)}</div>')
    if cid == 30236:
        art_audit_bits.append(f'<div class="art-bind">{esc(MANIFEST_NOTE_30236)}</div>')
    art_audit_bits.append(
        f'<div class="art-bind">card.json basic.card_art（card_page 主管线）状态：'
        f'{esc(art.get("status", "NO_VERIFIED_BINDING"))}'
        + (f'；{esc(art.get("note", ""))}' if art.get('note') else '')
        + '。立绘区独立于主管线（full_unpack 解包产物按命名规则绑定复制到 pages/art/），'
          '绑定依据见各图折叠标注。</div>')
    art_audit = (f'<details class="art-audit"><summary>▶ 立绘区审计（manifest/主管线状态）</summary>'
                 f'{"".join(art_audit_bits)}</details>')
    art_block = f'<div class="art-block">{"".join(art_html_parts)}{art_audit}</div>'
    # 右侧等级成长区：整块外部/网站维护（沿用定稿示例）
    lv_block = ('<div class="external-block"><div class="ext-title">等级 ATK/HP 表与成长曲线</div>'
                '<div class="ext-value">' + esc(NO_SOURCE) + '</div>'
                '<div class="ext-note">等级成长表在 card.json 中即标注为外部资料；'
                '本页不按截图或参考页编造任何等级数值与曲线。</div></div>')
    # 技能区：13 组导航（无配置组「本输入快照未关联」）＋组标签列
    nav = ''.join(f'<a href="#group-{esc(g["group"])}">{esc(g["label"])}</a>' for g in card['groups'])
    group_html = []
    for g in card['groups']:
        body_bits = []
        if g['skills']:
            body_bits.append(''.join(render_skill(s) for s in g['skills']))
        else:
            body_bits.append('<p class="empty">本输入快照未关联；不代表游戏没有此组。</p>')
        if g.get('unresolved'):
            body_bits.append('<p class="unknown">关联缺失：存在未解析引用；原始引用保留如下。</p>'
                             + details('未解析引用', g['unresolved']))
        for annotation in g.get('annotations', []):
            body_bits.append(
                f'<details class="group-annot"><summary>{esc(annotation.get("slot", ""))} = '
                f'{esc(annotation.get("raw_value"))}（必杀效果类型，非技能引用，不计描述分母）</summary>'
                f'<pre class="audit-pre">{esc(pretty(annotation))}</pre></details>')
        group_html.append(
            f'<section class="skill-group" id="group-{esc(g["group"])}" data-group="{esc(g["group"])}">'
            f'<div class="group-head"><h2>{esc(g["label"])}</h2>'
            f'<span class="small muted">{esc(g["status"])}</span></div>{"".join(body_bits)}</section>')
    # 页脚：本页处理状态＋来源映射折叠＋快照/输入根＋版式声明
    footer = (f'<footer class="coverage"><h2>本页处理状态</h2><p>{esc(summary_text(card["summary"]))}</p>'
              f'<p>A {cov["A"]} / {cov["N_num"]}＝{cov["A_rate"]:.1%}'
              + (f'；B {cov["B"]}' if cov.get('B') is not None else '')
              + f'；C {cov["C"]}。全部描述 {cov["N_all"]}，排除 E={cov["E"]}，A部分填充 {cov["partial_A"]}。</p>'
              f'<p>原文A {cov["original_A"]}；链新增A {cov["chain_new_A_rows"]}。'
              f'旧确认＋提示仅作历史参考，不冒充新A率。</p>'
              + details('证据交叉数量、来源与旧→新行映射', dict(coverage=cov, sources=card['sources']))
              + '</footer>'
              f'<footer>输入：{esc(card["sources"]["snapshot"])}｜输入根：{esc(card["sources"].get("input_root", ""))}。'
              f'网站一致／差异待实际对照，外部资料不覆盖本页原值。未实机验证。</footer>'
              '<footer>版式：2026-10-20 定稿玩家视角版式（dbstyle_samples/DESIGN.md；日文原文主体＋颜色即证据等级'
              '的数值 chips；审计内容收入 ▶详情 折叠层，信息一条不删）。颜色语义：绿=确认｜绿虚线+外推='
              '确认（类型外推）｜橙=推断｜灰=未知；立绘相对路径引用 pages/art/，命名规则绑定依据见各图折叠标注。'
              '批 4 条件扩展行的 chips 按组显示：基础＝无条件常时值行；条件：⟨逐字条件原文⟩＝该组数值仅在'
              '该条件成立时由子记录施加（组间不合乘）；绿 chip 的「原文已写｜关联未知」＝原文数字逐字确认、'
              '字段归属未证。</footer>')
    payload = pretty(card).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)} · {cid} 技能解读</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="topbar">锁链战记 角色技能页 · 玩家视角版式（2026-10-20 定稿迁移）</div>
<div class="wrap">
{top}
{metrics_line}
{legend}
{intro}
<div class="top-grid">
<div class="panel">{art_block}<table class="basic">{''.join(basic_trs)}</table>{basic_fold}<div class="meta ext-pills">{ext_pills}</div></div>
<div class="panel side">{lv_block}</div>
</div>
<div class="layout"><nav class="skill-groups" aria-label="技能分组">{nav}</nav><div>
{''.join(group_html)}
</div></div>
{footer}
</div>
<script type="application/json" id="card-data">{payload}</script>
</body>
</html>
"""


def page(card):
    """正式入口（card_page_batch 使用）：签名与旧 card_page_render.page 一致。"""
    return render_html(card)


def details(label, value):
    return ('<details class="source"><summary>' + esc(label) + '</summary><pre>'
            + esc(pretty(value)) + '</pre></details>')


CSS = ''':root{--paper:#141418;--panel:#222228;--ink:#d8d8de;--muted:#8a8a94;--line:#34343c;--gold:#c8b06a}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Microsoft YaHei","Hiragino Kaku Gothic ProN",system-ui,sans-serif;font-size:14px;line-height:1.7}
a{color:#8ab4c8;text-underline-offset:3px}a:focus-visible,summary:focus-visible{outline:2px solid #c19136;outline-offset:2px}
.wrap{max-width:1100px;margin:0 auto;padding:16px}
.topbar{background:#101014;padding:10px 16px;font-size:13px;color:#9a9aa2;border-bottom:1px solid #2c2c34}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:14px 16px;margin:12px 0}
.card-top .card-name{font-size:20px;font-weight:bold;color:#fff;margin-right:10px}
.card-top .card-title{color:var(--gold)}
.card-top .cid{color:#8a8a94;margin-right:10px;font-size:12px}
.sub-line{margin-top:6px}
.stars{color:#e8c84a;margin-right:16px}
.cost{color:#e8e8ee;margin-right:16px}
.layer{color:#7a7a84;font-size:12px}
.metrics-line{font-size:11px;color:#8a8a94;margin:2px 0 10px;letter-spacing:.3px}
.intro-detail{margin:0 0 10px}
.intro-detail summary{cursor:pointer;color:#8a8a94;font-size:12px}
.intro-text{font-size:12px;color:#9a9aa2;margin:8px 0;line-height:1.8}
.top-grid{display:grid;grid-template-columns:minmax(340px,1fr) minmax(240px,290px);gap:14px;align-items:start}
table.basic{width:100%;border-collapse:collapse}
table.basic th{text-align:left;background:#17171b;color:#a8a8b2;padding:5px 10px;width:110px;font-weight:normal;border-bottom:1px solid #2c2c34;vertical-align:top}
table.basic td{padding:5px 10px;border-bottom:1px solid #2c2c34;word-break:break-word}
details.basic-detail{margin-top:8px}
details.basic-detail summary{cursor:pointer;color:#8a8a94;font-size:12px}
.ext-pills{margin-top:10px}
.pill{border:1px solid #3c3c46;border-radius:5px;padding:2px 8px;display:inline-block;font-size:12px;margin:2px 4px 2px 0;color:#b8b8c2;white-space:normal}
.art-block{border:1px solid var(--line);border-radius:6px;background:#1b1b20;padding:12px;margin-bottom:10px}
.art-main{margin:0 0 10px;text-align:center}
/* 主图显示比例（2026-10-20 修正）：游戏 UI 控件 640×960=2:3 竖版（followup/REPORT.txt）；
   源 PNG 为 512×512 方形，object-fit:fill 默认拉伸＝游戏 UI 的非均匀缩放行为；whole/icon 维持 1:1 */
.art-main .art-img{width:min(340px,100%);aspect-ratio:2/3;height:auto;object-fit:fill}
.art-strip{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
.art-thumb{margin:0;flex:0 1 220px;text-align:center}
.art-thumb .art-img{max-width:200px;max-height:260px;width:auto}
.art-caption{font-size:12px;color:#8a8a94;margin-top:4px;word-break:break-all}
.art-bind-detail summary,.art-tried summary{cursor:pointer;color:#9a9aa2;font-size:12px;margin-top:2px}
.art-bind{color:#b8b8c2;font-size:12px;margin-top:4px;text-align:left;line-height:1.6}
.art-missing .art-caption{color:#c8c8d0}
.art-miss-line{color:#e8a86c;font-weight:bold;margin:6px 0}
.art-tried ul{margin:4px 0 0;color:#8a8a94;font-size:12px;padding-left:20px;text-align:left}
details.art-audit{margin-top:8px}
details.art-audit summary{cursor:pointer;color:#9a9aa2;font-size:12px}
.external-block{border:1px solid var(--line);border-radius:6px;background:#1b1b20;padding:14px;text-align:center}
.ext-title{color:#a8a8b2;margin-bottom:8px}
.ext-value{font-size:16px;color:#9a9aa2;letter-spacing:2px}
.ext-note{font-size:12px;color:#7a7a84;margin-top:10px;text-align:left}
.badge{display:inline-block;font-size:11px;padding:1px 7px;border-radius:9px;margin-left:6px;vertical-align:middle;white-space:nowrap}
.ev-conf{background:rgba(70,160,90,.25);color:#7ddc8d;border:1px solid rgba(70,160,90,.5)}
.ev-conf-ext{background:rgba(70,160,90,.25);color:#7ddc8d;border:1px dashed rgba(70,160,90,.7)}
.ev-inf{background:rgba(220,140,50,.2);color:#e8a86c;border:1px solid rgba(220,140,50,.5)}
.ev-unk{background:rgba(130,130,140,.15);color:#9a9aa2;border:1px solid rgba(130,130,140,.4)}
.layout{display:grid;grid-template-columns:170px minmax(0,1fr);gap:20px;align-items:start;margin-top:6px}
.skill-groups{position:sticky;top:12px;display:flex;flex-direction:column;gap:3px;border-left:2px solid var(--line);padding-left:12px}
.skill-groups a{text-decoration:none;color:var(--muted);padding:5px 9px;font-size:13px;border-radius:4px}
.skill-groups a:hover{background:#26262e;color:var(--ink)}
.skill-group{margin-bottom:26px;scroll-margin-top:20px}
.group-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline;border-bottom:2px solid #3a3a46;padding:0 0 8px;margin-bottom:12px}
.group-head h2{font-size:19px;color:#c8c8d0;margin:0}
.empty{padding:12px 14px;background:#1b1b20;border-radius:6px;color:var(--muted);font-size:13px}
.skill{background:var(--panel);border:1px solid var(--line);border-radius:6px;margin:0 0 16px;overflow:hidden}
.skill-head{padding:12px 16px;border-bottom:1px solid #2c2c34;background:#1d1d23}
.skill-name{color:#fff;font-weight:bold;margin-right:12px;font-size:16px}
.skill-meta{color:#8a8a94;font-size:12px}
.row{padding:12px 16px;border-top:1px dashed #2c2c34}
.row:first-of-type{border-top:none}
.row-jp,.row p.jp{font-size:17px;line-height:1.7;color:#f2f2f6;margin:0 0 7px;font-family:"Yu Gothic","Meiryo","Microsoft YaHei",system-ui,sans-serif}
.chips{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
/* P3 未解决效果短句（同句呈现已解释＋未解决；不使用数值 chip 样式，不呈现为完整） */
.unresolved-effects{margin-top:4px;font-size:12px;line-height:1.7}
.unresolved-effects .unres-title{color:#c8a44a;margin-right:8px}
.unresolved-effects .unres-item{display:inline-block;border:1px dashed #5a5245;border-radius:5px;
  padding:1px 7px;margin:2px 6px 2px 0;color:#c8b98f;white-space:normal}
.chip{display:inline-block;font-size:14px;font-weight:bold;padding:2px 10px;border-radius:4px;line-height:1.5}
.chip.ev-conf{background:rgba(70,160,90,.2);color:#7ddc8d;border:1px solid rgba(70,160,90,.6)}
.chip.ev-conf-ext{background:rgba(70,160,90,.2);color:#7ddc8d;border:1px dashed rgba(70,160,90,.75)}
.chip.ev-inf{background:rgba(220,140,50,.16);color:#e8a86c;border:1px solid rgba(220,140,50,.55)}
.chip.ev-unk{background:rgba(130,130,140,.12);color:#9a9aa2;border:1px solid rgba(130,130,140,.35);font-weight:normal}
.chip-tag{font-size:10px;font-weight:normal;color:#a8d8a8;border:1px dashed rgba(125,220,141,.6);border-radius:3px;padding:0 4px;margin-left:5px;vertical-align:1px}
.chip-assoc{font-size:10px;font-weight:normal;color:#9a9aa2;margin-left:6px}
/* H1（20261021 整改）：批 4 条件扩展行首屏 chips 分组——组标签首屏可见、不需展开详情 */
.chip-group{display:inline-flex;flex-wrap:wrap;gap:6px;align-items:center;margin-right:12px;padding-right:10px;border-right:1px dotted #3c3c46}
.chip-group-label{display:inline-block;font-size:11px;font-weight:normal;color:#c8c8d0;background:#26262e;border:1px solid #3c3c46;border-radius:4px;padding:1px 8px;max-width:420px;white-space:normal}
details.row-detail{margin-top:5px}
details.row-detail summary{cursor:pointer;color:#8a8a94;font-size:12px;user-select:none;list-style:none}
details.row-detail summary::-webkit-details-marker{display:none}
details.row-detail summary::before{content:'▶';margin-right:5px;font-size:10px;color:#6a6a74}
details.row-detail[open] summary::before{content:'▼'}
details.row-detail[open] summary{color:#b8b8c2}
details.skill-detail{margin:8px 16px 12px}
details.skill-detail summary{cursor:pointer;color:#6a6a74;font-size:11px;user-select:none;list-style:none}
details.skill-detail summary::-webkit-details-marker{display:none}
details.skill-detail summary::before{content:'▶';margin-right:4px;font-size:9px;color:#5a5a64}
details.skill-detail[open] summary::before{content:'▼'}
details.source{margin:8px 0}
details.source summary{cursor:pointer;color:#8a8a94;padding:5px 0;font-size:12px}
details.source pre{max-height:440px;overflow:auto;white-space:pre-wrap;background:#17171b;padding:12px;border-radius:5px;word-break:break-word;font-size:11px}
details.group-annot{margin:6px 0}
details.group-annot summary{cursor:pointer;color:#8a8a94;font-size:12px}
.unknown{font-size:13px;color:#c8a06a;background:#241f18;border-radius:4px;padding:9px 12px;margin:8px 0}
.audit-sec{margin-top:10px;border-top:1px solid #2c2c34;padding-top:8px}
.audit-title{color:var(--gold);font-size:12px;margin-bottom:6px}
.audit-ans{border-left:2px solid #34343c;padding-left:10px;margin-bottom:8px}
.audit-ans-title{color:#9a9aa2;font-size:11px;margin-bottom:2px}
.kv{display:flex;gap:10px;font-size:12px;line-height:1.7;align-items:flex-start}
.kv-k{flex:0 0 150px;color:#8a8a94;word-break:break-all}
.kv-v{flex:1;color:#b8b8c2;word-break:break-word}
.audit-pre{margin:2px 0;font-size:11px;line-height:1.5;color:#9aa0aa;background:#17171b;border:1px solid #2c2c34;border-radius:4px;padding:6px 8px;white-space:pre-wrap;word-break:break-all;max-width:100%;overflow-x:auto}
.audit-list{margin:2px 0;padding-left:18px}
/* ---- 证据等级图例：右上角固定吸顶小卡（滚动跟随）；窄屏回文档流，不溢出 ---- */
.legend{position:fixed;top:8px;right:8px;z-index:30;width:296px;max-width:calc(100vw - 16px);background:rgba(16,16,20,.96);border:1px solid #34343c;border-radius:6px;padding:8px 10px;font-size:11px;color:#b8b8c2;box-shadow:0 2px 10px rgba(0,0,0,.5)}
.legend-title{color:#c8c8d0;font-weight:bold;font-size:12px;margin-bottom:6px}
.legend-item{display:flex;gap:7px;align-items:flex-start;margin:4px 0;line-height:1.55}
.legend-item .chip{flex:0 0 auto;font-size:11px;padding:0 7px;line-height:1.7}
.legend-desc{flex:1;min-width:0;word-break:break-word}
.legend-note{margin-top:6px;padding-top:5px;border-top:1px solid #2c2c34;color:#8a8a94}
@media (max-width:760px){.legend{position:static;width:auto;max-width:none;margin:0 0 10px;box-shadow:none}.top-grid{grid-template-columns:1fr}.layout{grid-template-columns:1fr}.skill-groups{position:static;flex-direction:row;flex-wrap:wrap;padding:6px 0;border:0;border-bottom:1px solid var(--line)}}
footer.coverage{margin-top:26px;padding:18px;background:#1b1b20;border-radius:8px}
footer.coverage h2{font-size:16px;color:#c8c8d0;margin:0 0 8px}
footer{color:#7a7a84;font-size:12px;margin-top:14px;line-height:1.7}
h2{font-size:15px;color:#c8c8d0;margin:16px 0 8px}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}'''


def run_checks(card, doc):
    """页面级自检（定稿示例同款双通道之一）：图例/行数/折叠层/审计内容/art 引用。"""
    failures = []
    if len(doc) < 1000:
        failures.append('HTML 过小')
    for gone in ('class="ans-sub"', '｜换算：', 'class="value"'):
        if gone in doc:
            failures.append(f'首屏仍残留旧版式标记: {gone}')
    d = card
    rows = [r for g in d['groups'] for s in g['skills'] for r in s['rows']]
    for rid in (r['row_id'] for r in rows):
        if doc.count(f'data-row-id="{esc(rid)}"') != 1:
            failures.append(f'row_id 出现次数不为 1: {rid}')
    n_fold = doc.count('<details class="row-detail">')
    if n_fold != len(rows):
        failures.append(f'row-detail 折叠数 {n_fold} != 行数 {len(rows)}')
    # H1（20261021 整改）：带 condition_label 的批 4 行必须按组显示；组标签首屏可见
    for r in rows:
        labels = sorted({a['condition_label'] for a in r.get('answers', [])
                         if a.get('condition_label')})
        if not labels:
            continue
        if '<span class="chip-group">' not in doc:
            failures.append(f'批4行 chips 未分组显示: {r["row_id"]}')
        for cl in labels:
            if f'<span class="chip-group-label">条件：{esc(cl)}</span>' not in doc:
                failures.append(f'批4行缺少条件组标签: {r["row_id"]}: {cl[:40]}')
    for r in rows:
        if f'<span class="kv-v">{esc(r["row_id"])}</span>' not in doc:
            failures.append(f'折叠层缺少行ID可见文本: {r["row_id"]}')
        for u in (r.get('unknown_reasons') or []):
            if esc(u) not in doc:
                failures.append(f'折叠层缺少未知原因全文: {r["row_id"]}: {u[:40]}')
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
    a_cnt = sum(1 for r in rows if r['row_class'] == 'A')
    c_cnt = sum(1 for r in rows if r['row_class'] == 'C')
    s = d.get('summary', {})
    if a_cnt != s.get('A', {}).get('count'):
        failures.append(f'A 行数 {a_cnt} != summary.A.count {s.get("A", {}).get("count")}')
    if c_cnt != s.get('C', {}).get('count'):
        failures.append(f'C 行数 {c_cnt} != summary.C.count {s.get("C", {}).get("count")}')
    unk_chip_cnt = doc.count('<span class="chip ev-unk"')
    if unk_chip_cnt < c_cnt:
        failures.append(f'未知灰 chip 数 {unk_chip_cnt} < C 行数 {c_cnt}')
    # 图例：首屏（第一个折叠层之前）＋四档定义/提示语各恰好一次＋四档 chip 齐全
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
        for _label, cls, _desc in LEGEND_DEFINITIONS:
            if f'<span class="chip {cls}">' not in legend_block:
                failures.append(f'图例缺少 chip 类名: {cls}')
    # 13 组导航与空组限定
    for g in d['groups']:
        if doc.count(f'data-group="{esc(g["group"])}"') != 1:
            failures.append(f'data-group 出现次数不为 1: {g["group"]}')
        if not g['skills'] and '本输入快照未关联' not in doc:
            failures.append(f'空组缺少「本输入快照未关联」: {g["group"]}')
    # 立绘：相对路径引用存在且目标文件在盘上；缺失回退与尝试路径完整
    art_root = DEFAULT_PAGES / 'art'
    for it in art_model(card['cid']):
        tag = 'art_' + it['kind']
        if it.get('bytes') is not None:
            if f'src="{it["url"]}"' not in doc:
                failures.append(f'{tag}: 页面缺少立绘引用 {it["url"]}')
            if not (art_root / str(card['cid']) / Path(it['url']).name).is_file():
                failures.append(f'{tag}: art 文件不在盘上 {it["dest_rel"]}')
        else:
            if '本输入快照未取得' not in doc:
                failures.append(f'{tag}: 缺失图未显示「本输入快照未取得」')
            for t in it['tried']:
                if esc(t) not in doc:
                    failures.append(f'{tag}: 页面缺少尝试路径 {t}')
        if esc(it['binding']) not in doc:
            failures.append(f'{tag}: 页面缺少绑定依据标注')
        ratio_note = (DISPLAY_RATIO_NOTE_CARD if it['kind'] == 'card'
                      else DISPLAY_RATIO_NOTES_1_1.get(it['kind']))
        if it.get('bytes') is not None and ratio_note and esc(ratio_note) not in doc:
            failures.append(f'{tag}: 页面缺少显示比例标注')
        if it.get('extra') and esc(it['extra']) not in doc:
            failures.append(f'{tag}: 页面缺少追加标注')
    if card['cid'] == 30236 and esc(MANIFEST_NOTE_30236) not in doc:
        failures.append('art_manifest: 页面缺少 cid30236 manifest 状态标注')
    # 显示比例（2026-10-20 修正轮）：主图 2:3 竖版缩放 CSS＋页级审计依据文本必须齐全
    if 'aspect-ratio:2/3' not in doc:
        failures.append('主图显示比例 CSS 缺少 aspect-ratio:2/3（2:3 竖版）')
    if esc(DISPLAY_RATIO_AUDIT) not in doc:
        failures.append('页面缺少立绘区审计显示比例依据文本')
    return failures


def main():
    ap = argparse.ArgumentParser(description='玩家视角版式正式渲染层（card_page_render_v2）')
    ap.add_argument('--copy-art', action='store_true', help='从 full_unpack objects 复制立绘到 pages/art/')
    ap.add_argument('--pages-dir', default=str(DEFAULT_PAGES))
    ap.add_argument('--cids', default='', help='逗号分隔 cid；缺省=读 cohort manifest 全 2236')
    args = ap.parse_args()
    pages_dir = Path(args.pages_dir)
    if args.copy_art:
        if args.cids:
            cids = [int(c) for c in args.cids.split(',') if c.strip()]
        else:
            m = json.loads((ROOT / 'output/character_skills/r2_preparation/cohorts/manifest.json')
                           .read_text(encoding='utf-8'))
            cids = [mem['cid'] for mem in m['members']]
        stats = copy_art(cids, pages_dir)
        missing_none = sorted(cid for cid in cids
                              if all(cid in stats['missing'][k] for k in ('card', 'whole', 'icon')))
        print(json.dumps({**stats, 'missing': {k: len(v) for k, v in stats['missing'].items()},
                          'missing_none_cids': missing_none},
                         ensure_ascii=False))
        return
    ap.error('use --copy-art; page rendering is driven by card_page_batch.py')


if __name__ == '__main__':
    main()
