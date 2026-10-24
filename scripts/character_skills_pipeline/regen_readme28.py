# -*- coding: utf-8 -*-
"""pages/README.md §28 再生成器（DS-GR-03 修复，20261023）：§28 数字由当前
output/character_skills/effect_ledger/metrics.json 生成（生成器输出，非手写）。

每次 effect_ledger 重建后运行；替换 pages/README.md 中「## 28. 」节（到下一个「## 」
标题或文件尾），其余节零触碰。逐项取自 metrics.json：完整/部分/未解析/拆分待核查/
已识别效果/有答案/未解决/有依据不适用（全库＋Y.G. 单列）、证据档组合、backlog 构成。

用法：./.venv/Scripts/python.exe -B work/character_skills_goal_rectification/regen_readme28.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METRICS = ROOT / 'output/character_skills/effect_ledger/metrics.json'
README = ROOT / 'output/character_skills/pages/README.md'
GENERATOR = 'work/character_skills_goal_rectification/regen_readme28.py'

m = json.loads(METRICS.read_text(encoding='utf-8'))
d, e, b, rows = m['descriptions'], m['effects'], m['backlog'], m['rows']
# 辅助历史指标（A/C、原文A、整行确认/推断）取自当前 campaign_report（与账本同快照），
# 不硬编码旧数字。
_ptr = json.loads((ROOT / 'output/character_skills/pages/_batch/campaign_latest.json')
                  .read_text(encoding='utf-8-sig'))
_camp = json.loads((ROOT / 'output/character_skills/pages' / _ptr['report'])
                   .read_text(encoding='utf-8-sig'))
cov, summ = _camp['coverage'], _camp['summary']
st = e['by_status']
grades = e['evidence_grade_profiles']
grades_yg = e['evidence_grade_profiles_yg']
bp = b['by_priority']

def g(prof, key):
    return prof.get(key, 0)

section = f"""## 28. 效果级指标与效果账本（20261023 目标整改 P3/P4——逐描述、逐效果解析；看板口径）

<!-- 生成器输出：本节数字由 {GENERATOR} 从 output/character_skills/effect_ledger/metrics.json 逐项生成（DS-GR-03 修复，20261023），非手写；账本重建后重跑该脚本同步本节。 -->

由当前 pages 全量 card.json 驱动的效果账本与正式待办（生成器
`scripts/character_skills/effect_ledger.py`，输出 `output/character_skills/effect_ledger/`：
ledger.jsonl 一效果一条＋每条描述唯一入口、backlog.json 正式待办、metrics.json、README.md）。
下列为账本当前 metrics.json 实测值（输入快照 campaign `{(m['snapshot']['campaign_signature'] or '')[:8]}…`、
rules.json `{m['snapshot']['rules_json_sha256_16']}`、snapshot_id `{m['snapshot']['snapshot_id']}`；
复跑命令与字段定义见该目录 README）；本节逐项与 metrics.json 相等（生成器保证，非抄录）。

| 指标 | 全库 | Y.G. | 定义/分母 |
|---|---|---|---|
| 描述总数 | {d['total']['all']:,} | {d['total']['yg']:,} | 全部 card.json 行（重算，不硬编码） |
| 完整描述 | {d['complete']['all']:,} | {d['complete']['yg']:,} | 行内全部已识别效果有答案或有依据不适用、无拆分待核查标志 |
| 部分描述 | {d['partial']['all']:,} | {d['partial']['yg']:,} | 既有有答案/不适用、又有未解决，无拆分标志 |
| 未解析描述 | {d['unparsed']['all']:,} | {d['unparsed']['yg']:,} | 有已识别效果但全部未解决 |
| 拆分待核查描述 | {d['split_check']['all']:,} | {d['split_check']['yg']:,} | 零识别/数字语义未确认/未覆盖子句/答案未对应主张 |
| 已识别效果 | {e['identified_total']['all']:,} | {e['identified_total']['yg']:,} | 当前词表从句面识别的主张＋定性 NA 条目——**不是全库全部效果数**（拆分待核查行中未识别效果未计入），不得据此算总完成率 |
| 有答案效果 | {st['has_answer']['all']:,} | {st['has_answer']['yg']:,} | 含证据档（证据档与完整度分开计数） |
| 未解决效果 | {st['unresolved']['all']:,} | {st['unresolved']['yg']:,} | 进入 backlog（kind=effect） |
| 有依据不适用 | {st['justified_na']['all']:,} | {st['justified_na']['yg']:,} | 每条带逐字子句 na_basis（「できない」禁止型窄类，不用 NA 兜底） |

- 证据档独立计数（有答案效果按所引答案 numeric/association 组合）：推断 {g(grades,'推断'):,}／
  未知+确认 {g(grades,'未知+确认'):,}／确认 {g(grades,'确认'):,}／推断+确认 {g(grades,'推断+确认'):,}；Y.G.：推断 {g(grades_yg,'推断'):,}／
  未知+确认 {g(grades_yg,'未知+确认'):,}／确认 {g(grades_yg,'确认'):,}／推断+确认 {g(grades_yg,'推断+确认'):,}。
- 正式待办 backlog {b['total']:,} 项（P0 衔接断点 {bp.get('P0',0):,}／P1 Y.G. {bp.get('P1',0):,}／
  P2 其他 {bp.get('P2',0):,}；Y.G. 项 {b['yg_total']:,}）；集合差双向为空由固定检查
  card_page_verify_full.py 第 14 项保证。
- **辅助历史指标（口径注明，不充当剩余效果总量；取自当前 campaign_report）**：
  原文A {cov.get('original_A', 0):,}（原文数字仅确认原文，不证明语义完整）；
  A {cov.get('A', 0):,}／C {cov.get('C', 0):,}（行级有无数值/未知，不是已解释率）；
  整行确认 {summ.get('whole_row_confirmed', {}).get('count', 0):,}、
  整行推断 {summ.get('whole_row_inferred', {}).get('count', 0):,}
  （行级证据档，非效果级完整度）。
- 批 15（并集归属）行级键 `inference_b15`：{cov.get('inference_b15_promoted', 0):,} 行
  （crit 段批 8/14 既有值行零触碰＋非 crit/时长段 t13 槽值行，各注来源载体与层）；
  `inference_b15_hint` {cov.get('inference_b15_hinted', 0):,} 行（并集归属不成立的具体缺口）。
  行首屏以「仍未解决（N）」短句列出未解决效果与拆分待核查原因
  （渲染层 card_page_render_v2.py，与账本 analyze_row 同源；页面未解决区与账本行状态
  逐行一致性由固定检查第 15 项 page_ledger_unresolved_sync 保证——DS-GR-01 修复）；
  未解决不呈现为完整、推断不呈现为确认（固定检查第 8 项 chip 颜色档位继续保证）。
"""

text = README.read_text(encoding='utf-8')
pat = re.compile(r'## 28\. .*?(?=^## \d+\. |\Z)', re.S | re.M)
if not pat.search(text):
    raise SystemExit('未找到 §28 节，中止（不盲写）')
new_text = pat.sub(lambda _m: section, text, count=1)
README.write_text(new_text, encoding='utf-8')
print('§28 rewritten from metrics.json:',
      dict(complete=d['complete']['all'], partial=d['partial']['all'],
           unparsed=d['unparsed']['all'], split=d['split_check']['all'],
           has_answer=st['has_answer']['all'], unresolved=st['unresolved']['all'],
           na=st['justified_na']['all'], backlog=b['total']))
