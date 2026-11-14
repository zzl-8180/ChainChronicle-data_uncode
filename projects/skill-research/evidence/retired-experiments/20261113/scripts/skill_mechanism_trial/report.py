"""Package the reviewed, isolated experiment; never writes production data."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from versioned_outputs import experiment_report_source, fresh_output, report_links
from datetime import datetime
from html import escape
from html.parser import HTMLParser
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = experiment_report_source('skill_mechanism_trial', ROOT/'output/skill_mechanism_trial/20261104')


def read(relative):
    return json.loads((BASE / relative).read_text(encoding='utf-8-sig'))


def write(output, relative, data):
    (output / relative).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seconds(start, end):
    return (datetime.fromisoformat(end.replace('Z', '+00:00')) -
            datetime.fromisoformat(start.replace('Z', '+00:00'))).total_seconds()


def main():
    verdict = read('review/verdict.json')
    comparison = read('comparison.json')
    manifest = read('input/manifest.json')
    frozen = read('arm_freeze_manifest.json')
    start = read('experiment_start.json')
    assert verdict['all_checks_passed']
    assert verdict['equal_reviewed_outcome_comparison']['holds']
    assert not comparison['input_hash_mismatches']
    for relative, info in manifest['files'].items():
        assert digest(BASE / 'input' / relative) == info['sha256'], relative
    for files in frozen['arms'].values():
        for relative, expected in files.items():
            assert digest(BASE / relative) == expected, relative

    reviewed = {t['task_id']: t for t in verdict['arms']['family_attack']['tasks']}
    accepted = []
    for task in read('family_attack/task_results.json')['tasks']:
        decision = reviewed[task['task_id']]
        if decision['accepted_description_candidates']:
            accepted.append({'submission': task, 'independent_review': decision,
                             'status': 'CANDIDATE_ONLY_NOT_PRODUCTION',
                             'association_confidence': 'inferred',
                             'review_reference': 'review/verdict.json',
                             'frozen_source_root': 'input/'})
    assert len(accepted) == 2
    output = fresh_output('projects/skill-research/experiments/skill_mechanism_trial/reports','report')
    write(output,'accepted_candidates.json', {
        'snapshot': verdict['snapshot'], 'scope': 'Two conditional partial description bindings; existing numeric rule',
        'new_formulas': 0, 'confirmed_description_answers': 0, 'production_promotions': 0,
        'candidates': accepted,
    })
    timing = verdict['equal_reviewed_outcome_comparison']
    serial = timing['card_serial_seconds']
    parallel = timing['family_parallel_seconds']
    cumulative = timing['family_cumulative_agent_seconds']
    prep = seconds(start['common_experiment_start_utc'], start['preparation_end_utc'])
    review = seconds(verdict['started_at'], verdict['finished_at'])
    values = verdict['independent_values']
    rows = ''.join(
        f'<tr><td>{key} / {cid}</td><td>「攻撃力が上がる。」</td>'
        f'<td>局部攻击 ×{values[key]["raw_value"]}（+{values[key]["increase_percent"]:g}%）</td>'
        f'<td>推断级候选；记录 {values[key]["record_id"]} / param1</td></tr>'
        for key, cid in [('A1', 30110), ('A2', 30333)])
    report = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>实际未解技能：机制族并行对照实验</title>
<style>body{{max-width:1040px;margin:40px auto;padding:0 24px;font:16px/1.75 system-ui,sans-serif;color:#213047;background:#f7f9fc}}
h1,h2{{line-height:1.35}}h2{{margin-top:32px}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{padding:12px;border:1px solid #d6dfeb;text-align:left}}th{{background:#eaf0f8}}a{{color:#1764a3}}.callout{{padding:20px;background:#e9f3f1;border-left:5px solid #23856d}}code{{overflow-wrap:anywhere}}small{{color:#53657b}}</style>
<h1>实际未解技能：机制族研究＋并行解算</h1>
<p>2026-11-04（北京时间） · 冻结快照 <code>{escape(verdict['snapshot'])}</code></p>
<div class="callout"><strong>新增 2 条经独立审查接受的推断级描述绑定；本次没有显示提速。</strong><br>
4 个固定未解目标中，两个攻击目标取得条件性候选，两个回复目标仍未知。新增已确认描述答案 0、新公式 0、正式晋级 0。两种方法的验收结果相同。</div>
<h2>实际取得了什么</h2>
<table><tr><th>目标 / 卡 ID</th><th>原文</th><th>候选数值</th><th>证据范围</th></tr>{rows}
<tr><td>B1 / 30107</td><td>区域持续回复／超上限句</td><td>未解</td><td>bossskill type108，字段消费证据缺失</td></tr>
<tr><td>B2 / 30313</td><td>区域持续回复／超上限句</td><td>未解</td><td>同族缺口；不能从其他回复类型套公式</td></tr></table>
<p>攻击候选复用已经确认的 ability1095.param1 局部公式。本次新增的是“描述归属”：角色实际引用→父记录→唯一1095子记录→单独攻击句。旧 P4 模板要求整条记录的效果槽与句子匹配，附带暴伤字段导致原本没有答案；实验只提出单效果部分绑定，没有放宽或通过旧 P4 门控。</p>
<p><strong>这两个数值以该能力已经装载、IsEnableAbility 通过为条件。</strong>它们仅表示本项局部攻击贡献，不代表角色总攻击、面板攻击或最终伤害；不合并 WAVE、暴击和其他能力。原生装载及全文归属仍未闭合，因此只接受“推断”，不升级为“确认”。两种方法发现同两条，去重后是2条，不是4条。</p>
<p>两个回复目标虽然均有原值 1.5、2、30，但冻结证据包没有适用的 type108 字段消费者证据。不能将其称为回复倍率、2秒、30秒或次数，也不能推出超上限百分比。未解目标保留在分母中；这不等于已证明整个仓库不存在相关证据。</p>
<h2>同等验收成果下的时间</h2>
<table><tr><th>路线</th><th>研究经过时间</th><th>累计代理作业时间</th><th>结果</th></tr>
<tr><td>逐卡串行：A1→B1→A2→B2</td><td>{serial:g}秒（5分7秒）</td><td>{serial:g}秒</td><td>2候选＋2未解</td></tr>
<tr><td>机制族并行：攻击族＋回复族</td><td>{parallel:g}秒（5分11秒）</td><td>{cumulative:g}秒（8分22秒）</td><td>2候选＋2未解</td></tr></table>
<p>并行比串行多 {parallel-serial:g} 秒（约 {(parallel/serial-1)*100:.1f}%），加速比 {serial/parallel:.3f}。差距很小，不能解释为稳定变慢；本次可直接支持的结论是<strong>未观察到节省时间</strong>。两族累计代理时间增加 {cumulative-serial:g} 秒（约 {(cumulative/serial-1)*100:.1f}%），并行不能视为免费节省计算资源。</p>
<p>攻击族311秒，回复族191秒，并行完成时间由较慢的攻击族决定。逐卡控制组允许自然复用已读资料，因此它也能在第二张同族卡上复用知识。每条线的时长均含思考、工具等待、记录与验证；活跃推理和服务排队没有独立计量。</p>
<p>公共准备约 {prep:.1f} 秒；独立审查约 {review:.1f} 秒，均未计入上表。审查的盲读阶段与研究尾部重叠，不能直接累加为端到端耗时。最后报告整合未单独计时。以上是 AI 代理墙钟时间，<strong>不能直接换算成工程师人时，也不能据此下调此前的人时区间</strong>。</p>
<h2>对照与隔离</h2>
<p>研究前固定4个真实未解目标，基线答案为空。三个研究代理继承同一模型配置、读取同一冻结输入、不互读结果；控制组逐卡，处理组按机制族并行。独立审查先盲读来源并保存判断，全部提交冻结后才读取三组成果。目标与口径在派发前固定；协议JSON于研究开始后、首条结果返回前保存，不声称提前注册。</p>
<p>输入47文件，17,822,978字节；三组提交18文件均保持冻结哈希。独审216项检查通过，包含原值、引用、基线和哈希核对；没有重新执行原生代码或实机验证。验证数量不是解出答案的数量。</p>
<p>写入限 <code>scripts/skill_mechanism_trial/</code>、本输出目录及本任务卡。排除C15五张目标卡与两张保护卡；没有写入C15、正式规则、页面、账本或共享交接。实验脚本是固定两条人工审查绑定的复算，不是可用于任意新卡的通用解算器。</p>
<h2>如何使用这次结果</h2>
<p>机制族路线可以产出可审查候选，但此处突破来自缩小绑定粒度、复用既有公式，而非发现新机制；两个方法都做到了。回复族缺少共同证据时，多代理并不能补齐证据。仅4目标、每族2张、单次且未随机化，还同时改变了分组与代理数，无法把效果归因于某一个因素。</p>
<p>下一轮可在更多同族目标上先比较“单代理逐卡”与“单代理按族”以测量分组收益，再比较多个独立机制族的串并行；固定输入、盲审标准和预算，同时记录准备、研究、复核与人工介入。对已知公式优先批量验证描述绑定，对未知机制先补公共消费者证据，再分卡验证。此次不继续扩大样本、不启动C15变更。</p>
<h2>复核入口</h2><ul>
<li><a href="accepted_candidates.json">两条候选及条件、来源、独审意见（JSON）</a></li>
<li><a href="review/REPORT.md">独立审查报告</a> · <a href="review/verdict.json">验收结论</a> · <a href="review/validation.json">216项检查</a></li>
<li><a href="comparison.json">对照统计</a> · <a href="analysis_protocol.json">实验口径</a> · <a href="input/targets.json">目标与未解基线</a></li>
<li><a href="input/manifest.json">冻结输入清单</a> · <a href="arm_freeze_manifest.json">研究提交哈希</a></li>
<li><a href="card_serial/timing.json">逐卡计时</a> · <a href="family_attack/timing.json">攻击族计时</a> · <a href="family_heal/timing.json">回复族计时</a></li>
</ul><p><small>只读复算：项目根目录运行 .venv\\Scripts\\python.exe -B scripts/skill_mechanism_trial/report.py，仅更新本实验交付文件。研究过程本身无法由这些脚本自动重演。</small></p></html>'''
    report = report_links(report, BASE, output)
    (output / 'report.html').write_text(report, encoding='utf-8')

    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                self.links.extend(v for k, v in attrs if k == 'href')
    parser = Links()
    parser.feed(report)
    assert all((output / link).is_file() for link in parser.links)
    source_files = sorted((ROOT / 'scripts/skill_mechanism_trial').glob('*.py'))
    for path in source_files:
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    write(output,'delivery_validation.json', {
        'passed': True, 'input_hashes_checked': len(manifest['files']),
        'arm_hashes_checked': sum(map(len, frozen['arms'].values())),
        'report_links_checked': len(parser.links), 'source_files_parsed': len(source_files),
        'independent_review_checks': read('review/validation.json')['counts'],
        'same_reviewed_outcome': True, 'common_preparation_seconds': prep,
        'independent_review_seconds': review, 'candidate_count': len(accepted),
    })
    files = [p for p in BASE.rglob('*') if p.is_file() and p.name != 'delivery_manifest.json'] + [p for p in output.rglob('*') if p.is_file()] + source_files
    write(output,'delivery_manifest.json', {'scope': 'Isolated experiment; no production promotion',
        'files': {p.relative_to(ROOT).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(files)}})
    print(json.dumps({'passed': True, 'candidates': len(accepted), 'report_links': len(parser.links),
                      'report': str(output / 'report.html')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
