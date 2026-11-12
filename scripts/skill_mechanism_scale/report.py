"""Render the final independently adjudicated experiment summary, isolated only."""
import ast
import hashlib
import json
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from versioned_outputs import experiment_report_source, fresh_output, report_links

ROOT=Path(__file__).resolve().parents[2]
BASE=experiment_report_source('skill_mechanism_scale',ROOT/'output/skill_mechanism_scale/20261104')
def load(name): return json.loads((BASE/name).read_text(encoding='utf-8-sig'))
def save(output,name,data): (output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def duration(s): return f'{int(s//60)}分{s%60:.1f}秒'
def cell(x): return escape(str(x))

def main():
    s=load('final_summary.json'); c=load('collection.json'); m=load('input/manifest.json'); f=load('arm_freeze_manifest.json')
    for path,info in m['files'].items(): assert digest(BASE/'input'/path)==info['sha256'],path
    for paths in f['arms'].values():
        for path,h in paths.items(): assert digest(BASE/path)==h,path
    t=c['observed_timing']
    method_rows=''.join(f'<tr><td>{cell(x[0])}</td><td>{duration(x[1])}</td><td>{duration(x[2])}</td><td>{cell(x[3])}</td></tr>' for x in [
        ('逐卡串行（A）',t['card_serial_seconds'],t['card_serial_seconds'],s['method_outcomes']['card_serial']),
        ('先机制、分组串行（B）',t['family_serial_seconds'],t['family_serial_seconds'],s['method_outcomes']['family_serial']),
        ('先机制、分组并行（C）',t['family_parallel_span_seconds'],t['family_parallel_sum_seconds'],s['method_outcomes']['parallel'])])
    table=''.join(f'<tr><td>{cell(r["cid"])}</td><td>{cell(r["task_id"])}</td><td>{cell(r["japanese"])}</td><td>{cell(r["accepted_count"])}</td><td>{cell(r["result_zh"])}</td><td>{cell(r["scope_zh"])}</td></tr>' for r in s['card_rows'])
    phase_rows=''.join(f'<tr><td>{cell(x["arm"])}</td><td>{cell(x["phase"])}</td><td>{duration(x["seconds"])}</td></tr>' for x in s.get('phase_rows',[]))
    paragraphs=lambda values: ''.join('<p>'+cell(x)+'</p>' for x in values)
    max_time=max(t['card_serial_seconds'],t['family_serial_seconds'],t['family_parallel_span_seconds'])
    bars=''.join(f'<div class="barrow"><span>{name}</span><div class="bar" style="width:{sec/max_time*72:.2f}%">{duration(sec)}</div></div>' for name,sec in [('逐卡串行',t['card_serial_seconds']),('分组串行',t['family_serial_seconds']),('分组并行',t['family_parallel_span_seconds'])])
    html=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>31卡扩样：机制分组与并行的效果</title><style>
body{{max-width:1120px;margin:36px auto;padding:0 24px;background:#f7f9fc;color:#263449;font:16px/1.75 system-ui,sans-serif}}
h1,h2{{line-height:1.35}}h2{{margin-top:32px}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{border:1px solid #d7e0eb;padding:10px;text-align:left;vertical-align:top}}th{{background:#eaf0f7}}a{{color:#17639c}}code{{overflow-wrap:anywhere}}
.callout{{padding:20px;border-left:5px solid #237d70;background:#e9f3f1}}.barrow{{display:flex;align-items:center;margin:10px 0;gap:10px}}.barrow span{{width:90px;flex-shrink:0}}.bar{{background:#286c94;color:white;padding:8px;min-width:100px;box-sizing:border-box}}small{{color:#53647a}}.scroll{{overflow-x:auto}}
</style><h1>31卡扩样实验：先研究机制，是否更快？</h1>
<p>2026-11-04 · 快照 <code>{cell(s['snapshot'])}</code> · 仅本地独立实验，正式晋级0</p>
<div class="callout"><strong>{cell(s['headline'])}</strong>{paragraphs(s['plain_conclusion'])}</div>
<h2>分开看分组与并行</h2>{bars}
<table><tr><th>路线</th><th>实际经过时间</th><th>累计代理作业时间</th><th>独审后成果</th></tr>{method_rows}</table>
{paragraphs(s['timing_interpretation'])}
<p>以上计时包含分析、编写辅助程序、工具等待、逐卡核验和提交前检查。累计代理时间是各代理墙钟时长之和，不是CPU占用、token费用或工程师人时。共同准备、独审与最终整合另列；未将脚本几毫秒的执行速度冒充解读技能的速度。</p>
<h2>到底新增多少可靠答案</h2>{paragraphs(s['reliability_interpretation'])}
<p>新增量以效果项计数：一个描述可能有攻击、减伤、移速等多个效果；三条路线得出同一项只计一次。新增是原先没有答案的描述归属，已存在的原值与公式不再计作新公式。当前样本61效果的未解/候选分布、低证据项与拒绝原因全部保留。</p>
<details open><summary>31张卡逐项结果（同一描述的多个效果合并展示）</summary><div class="scroll"><table><tr><th>卡ID</th><th>目标</th><th>原文</th><th>接受项数</th><th>局部数值或缺口</th><th>证据范围</th></tr>{table}</table></div></details>
<h2>这轮实际测了什么</h2>
<p>31卡31描述61个基线未解效果，31条不同机制载体；18张Y.G.卡。24条1095自身增益按单属性、双属性、至少三属性各8条分层，另有7条108区域回复，每张卡只取一个档位。排除上轮4张卡、C15五张目标卡及保护卡，按Y.G.优先和固定hash选择，没有按字段数值或研究结果挑选。快照中目标答案全部为空。</p>
<p>A按固定交错顺序逐卡研究，允许自然复用知识和辅助脚本；B先研究机制与共同判断标准，再按族批量核对；C用相同机制优先方式、两个代理各研究一个族。各组同模型配置、同输入、无历史上下文、互不读取结果。统一提供上轮独审先验，避免只让一组免费继承旧知识。</p>
<p>这是<strong>已有机制规则下的描述绑定与批量核验</strong>实验。没有测量从零逆向一个全新机制，也不能把本轮效率直接套到全项目剩余工时。108族欠缺共同消费者证据，不能因有1.25/1.5、2、30这些原值就输出回复倍率、间隔、持续时间或超上限。</p>
<h2 id="limits">计量限制与可靠性边界</h2>{paragraphs(s['limitations'])}
<p>参考 <a href="https://www.itl.nist.gov/div898/handbook/pri/section3/pri332.htm">NIST实验设计说明</a>，执行者与运行时段属于需要控制的干扰因素。本轮记录这些限制，但不是完成了随机重复的区组实验；31卡不等于31次独立的“方法速度”重复，不能据此编造统计置信区间。</p>
<details><summary>阶段计时（各组记录粒度不同，不能机械相减归因）</summary><table><tr><th>组</th><th>实际记录阶段</th><th>耗时</th></tr>{phase_rows}</table></details>
<h2>独立验收与隔离</h2>{paragraphs(s['validation_notes'])}
<p>写入限定本任务脚本、本实验输出和独立任务卡。没有运行正式生成器、修改C15/生产规则/页面/账本，也没有安装依赖、执行新原生代码或手机实机验证。冻结输入是74文件、46,457,071字节；旧实验产物保持不变。</p>
<h2>复核与复算</h2><ul>
<li><a href="accepted_candidates.json">去重后候选、来源、条件和审查分级</a> · <a href="final_summary.json">汇总数据</a></li>
<li><a href="review/REPORT.md">独立审查报告</a> · <a href="review/verdict.json">逐组结论</a> · <a href="review/pre_review.json">未看提交前的盲审判断</a> · <a href="review/review_timing.json">审查分阶段计时</a></li>
<li><a href="collection.json">实测时间与原值核对</a> · <a href="protocol.json">派发前协议</a> · <a href="sample_facts.json">样本数量口径</a></li>
<li><a href="input/manifest.json">冻结输入</a> · <a href="input/targets.json">31条目标及未解基线</a> · <a href="arm_freeze_manifest.json">四组提交冻结哈希</a></li>
<li><a href="card_serial/REPORT.md">逐卡组</a> · <a href="family_serial/REPORT.md">分组串行组</a> · <a href="parallel_attack/REPORT.md">并行攻击组</a> · <a href="parallel_heal/REPORT.md">并行回复组</a></li>
</ul><p><small>从项目根目录以 .venv\\Scripts\\python.exe -B 依次运行 scripts/skill_mechanism_scale/collect.py、summarize.py、report.py（后两者同目录）可复算统计与展示，仅写本目录；这些程序不会重新执行代理研究。冻结输入准备器拒绝覆盖已有快照。</small></p></html>'''
    output=fresh_output('projects/skill-research/experiments/skill_mechanism_scale/reports','report')
    html=report_links(html,BASE,output)
    (output/'report.html').write_text(html,encoding='utf-8')
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.links=[]
        def handle_starttag(self,tag,attrs):
            if tag=='a': self.links += [v for k,v in attrs if k=='href' and not v.startswith('https://')]
    links=Links();links.feed(html)
    assert all((output/link).is_file() for link in links.links)
    scripts=sorted((ROOT/'scripts/skill_mechanism_scale').glob('*.py'))
    for p in scripts: ast.parse(p.read_text(encoding='utf-8-sig'),str(p))
    save(output,'delivery_validation.json',{'passed':True,'input_hashes_checked':len(m['files']),
        'arm_hashes_checked':sum(len(x) for x in f['arms'].values()),'local_links_checked':len(links.links),
        'source_files_parsed':len(scripts),'independent_review':s['validation_notes']})
    files=[p for p in BASE.rglob('*') if p.is_file() and p.name!='delivery_manifest.json']+[p for p in output.glob('*') if p.is_file()]+scripts
    save(output,'delivery_manifest.json',{'scope':'Isolated experiment, not production promotion',
        'files':{p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(files)}})
    print(json.dumps({'passed':True,'report':str(output/'report.html'),'links':len(links.links)},ensure_ascii=True))

if __name__=='__main__': main()
