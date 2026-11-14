"""Check experiment outputs and generate a local report, without production reads."""
import copy
import html
from html.parser import HTMLParser
import json
from pathlib import Path

import run as experiment


def main():
    experiment.low_priority()
    experiment.guard(True)
    out, frozen = experiment.OUT, experiment.FROZEN
    results = experiment.read_json(out / 'results.json')
    manifest = experiment.read_json(frozen / 'manifest.json')
    tasks = experiment.read_json(out / 'verification_tasks.json')
    checks = experiment.read_json(out / 'source_checks.json')
    mutations = experiment.read_json(out / 'structure_mutations.json')
    hashes = experiment.read_json(out / 'input_hashes.json')
    raw = (frozen / (experiment.RAW + 'bossinfo.data5.json.raw')).read_text(encoding='utf-8-sig')
    index = experiment.source_index(json.loads(raw)['bossinfo']['bossskill'])
    tests = []
    for name, expected_flag in [('wrong_raw', 'raw_matches'), ('wrong_record_id', 'raw_matches'),
                                ('wrong_type', 'type_matches'), ('wrong_field', 'raw_matches'),
                                ('wrong_source_id', 'source_id_matches'), ('wrong_source_layer', 'source_layer_matches')]:
        task = copy.deepcopy(tasks[0])
        if name == 'wrong_raw': task['raw_value'] = 999999999
        if name == 'wrong_record_id': task['record_id'] = -999999999
        if name == 'wrong_type': task['rule_key'] = 'bossskill|999999|' + task['field']
        if name == 'wrong_field': task['field'] = '/field_that_does_not_exist'
        if name == 'wrong_source_id': task['source']['record_id'] = -999999999
        if name == 'wrong_source_layer': task['source']['layer'] = 'APK'
        observed = experiment.verify_one(task, index)
        # Append the wrong case to the correct case: cached checking must not reuse
        # a success after changing a semantic/source input.
        pair = [tasks[0], task]
        dedup = experiment.route_dedup(pair, raw)
        direct = experiment.route_index(pair, raw)
        tests.append({'case': name, 'expected_false': expected_flag,
                      'passed': observed[expected_flag] is False and direct == dedup,
                      'observed': observed})
    checks_ok = all(all(row[k] for k in ['raw_matches', 'type_matches', 'source_id_matches', 'source_layer_matches']) for row in checks)
    summary = {'negative_source_cases': tests,
        'source_checks_all_pass': checks_ok,
        'counts_consistent': len(tasks) == len(checks) == results['tasks'],
        'mutations_all_pass': len(mutations) == results['structure']['mutation_cases'] and all(m['passed'] for m in mutations),
        'inputs_still_match': all(experiment.sha((frozen / p).read_bytes()) == digest for p, digest in hashes.items()),
        'sample_excludes_active_and_protected': not (set(results['sample_cids']) & experiment.EXCLUDED),
        'runner_hash_matches_results': experiment.sha(Path(experiment.__file__).read_bytes()) == results['isolation']['script_sha256'],
        'not_independent_third_party_review': True}
    assert all(t['passed'] for t in tests)
    assert all(summary[k] for k in ['source_checks_all_pass', 'counts_consistent', 'mutations_all_pass', 'inputs_still_match', 'sample_excludes_active_and_protected', 'runner_hash_matches_results'])
    experiment.write_json(out / 'validation.json', summary)
    s, group = results['structure'], results['grouping']
    esc = html.escape

    def table(headers, rows):
        return '<table><thead><tr>' + ''.join('<th>' + esc(str(h)) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + esc(str(v)) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'

    route_rows = [
        ['A 来源索引与共享读取', '可行；优先用于尚未复用的核查环节', f'{len(tasks)} 条原值/类型/来源核查一致；单次解析索引中位 {results["indexed"]["median_seconds"]:.4f}s', '参考基线是实验自建逐条解析器，不是生产程序；不得宣称项目整体加速数百倍。'],
        ['B 精确来源任务去重', '正确性可行；本批轻量工作不值得单独优化', f'{len(tasks)} → {results["unique_source_checks"]} 个唯一核查任务；去重中位 {results["deduplicated"]["median_seconds"]:.4f}s，略慢于仅索引', '节省的是重复核查次数。每次核查很便宜时，构造去重键反而更慢；不合并描述归属。'],
        ['C 按机制族分工', '组织可行；研究人时收益尚未计时', f'{group["card_family_pairs"]} 个角色×规则组合 → {group["rule_families_in_verification_sample"]} 个规则族；未完整描述 {group["remaining_rows"]} 行 → {group["exact_text_groups"]} 种原文', f'{group["same_text_multiple_source_context_groups"]} 种同文横跨不同来源上下文，只能集中研究，不能同文直接抄值。'],
        ['D 结构规则迁移／模拟新卡', '有条件可行；当前不能独立完成新卡全面解算', f'{s["rows"]} 行回放、{s["selected"]} 条选中原值核对通过、{s["verdicts"].get("VALUE_AND_BINDING",0)} 行绑定；{s["mutation_pass"]}/{s["mutation_cases"]} 变体符合预期', '删去已有答案交叉证据后，34 条均只剩字段值；改号/改值测试仅证明指定子族，不是真实新卡或全卡验收。'],
        ['E 两进程并行核查', '本小负载不推荐；结果一致但更慢', f'冷启动 {results["two_process"]["cold_median_seconds"]:.4f}s；预热 {results["two_process"]["warm_median_seconds"]:.4f}s；串行预热 {results["indexed_warm"]["median_seconds"]:.6f}s', '子进程计算不是多 AI 研究实验。独立且较重的研究任务仍可并行，但本轮没有测得其加速倍数。'],
    ]
    timing_rows = [
        ['自建逐条解析参考', results['reference_naive']['median_seconds'], '每条任务重新解析同一已读文本，含 JSON 解析；不是生产基准'],
        ['单进程共享索引', results['indexed']['median_seconds'], '含一次 JSON 解析和索引建立'],
        ['共享索引＋精确去重', results['deduplicated']['median_seconds'], '含一次解析、索引及去重键生成'],
        ['单进程预热索引', results['indexed_warm']['median_seconds'], '已建索引，仅实际核查'],
        ['两进程冷启动', results['two_process']['cold_median_seconds'], '包括池启动、传参和任务返回；不含退出回收'],
        ['两进程预热', results['two_process']['warm_median_seconds'], '已启动池及已建索引，含通信'],
    ]
    body = f'''<header><p class="eyebrow">独立实验 · 2026-11-03 启动 / 2026-11-04 完成</p>
<h1>角色技能解读：五条提速路线实验</h1>
<p class="lead">优先复用来源与机制，再考虑扩大并行。结构规则已经能迁移部分已知机制，但当前仍依赖基础答案；本批轻量核查增加进程反而更慢。</p></header>
<section><h2>范围与不干扰现有作业</h2>
<p>冻结快照 <code>{esc(results['snapshot'])}</code>；18 张卡、267 个已有 Boss 参数答案。角色选择为 3 张指定结构样本＋固定种子抽取 15 张卡，不是随机新卡总体样本。排除 C15 正在处理的 7250、30105、30301、30329、30334，以及保护卡 30236、30239。YG 分组分析也排除这七卡；完整冻结账本仅保留原始上下文，不研究排除卡。</p>
<p>只新增本实验脚本、任务记录和输出；未修改生产代码、正式角色页、规则、账本、latest、C15 文件或共享交接。冻结过程检测读取稳定性，运行只读冻结输入。26 个冻结文件前后哈希一致；生产路径读写拒绝探针通过。Python 审计钩子是代码级保护，不是操作系统隔离。最多两个低优先级进程；仍有短时 CPU/磁盘负载，不宣称零资源影响。</p>
<p>冻结文件 {manifest['frozen_bytes']/1024**2:.2f} MiB；未安装依赖、复制整库、启动 AI 子代理、做原生研究、运行正式生成或公开发布。未核验其他作业最终状态，不把外部作业自行产生的改动归入本实验。</p></section>
<section><h2>路线结论</h2>{table(['路线','判断','实测','边界'], route_rows)}</section>
<section><h2>同一核查负载的时间</h2><p>各路线执行 3 次，表列中位数；原始每次时间保存在 results.json。来源文本预先读入，时间不含输入文件读取、卡片载入、人工研究、语义审查和整包生成。并行测试始终最多两个 BELOW_NORMAL 子进程。共享工作区可能有其他负载；毫秒级结果只用于排除明显不划算的路线。</p>
{table(['路径','中位秒数','包括／不包括'],[(a,f'{b:.6f}',c) for a,b,c in timing_rows])}
<p>所有路线逐条结果完全一致。267 条原值、type、source.record_id 和 source.layer 检查各全部通过；另用 6 个错误原值/ID/type/字段/来源ID/来源层反例验证拒绝和缓存隔离。它们核查来源字段，不构成全部技能语义或最终伤害验证。</p></section>
<section><h2>模拟新卡揭示的能力边界</h2>
<p>直接调用冻结 G1 模块的只读判定，未调用生产生成器。140 条镜像候选中 34 条能定位字段值，23 条满足已有答案交叉核对后给出绑定判定，9 条仅字段值，2 条同值异记录，其余 106 条不属于该规则可处理范围。34 条选中值均与独立读取的原表记录一致；这只核对原值，不重新证明完整原生语义。33 条在当前镜像行已有同记录同原值答案，也不能据此把剩余 1 条宣布为新交付。</p>
<p><strong>隐藏全部基础答案后，绑定判定从 23 条降至 0 条，34 条仍可输出字段值。</strong>这是一项有用但严格受限的证据遮蔽实验：证明当前模块依赖基础答案，不能说明全工具链无法从新卡原表先产生基础答案。输入仍是旧卡的正式行和旧结构，没有未来版本或从原文起步的全卡盲测。</p>
<p>从 6 张不同角色各取一个已通过样本，共 84 项合成测试：保持原结构、整条关系改号、只改选中参数并同步交叉证据、同步修改全部同类候选、撤去/错配交叉证据、跨层、文本冲突、缺失/null/负数/布尔值、不支持的类型和竞争记录，最终 84/84 符合预期。新值取原值＋0.125，仅证明该窄域接受未列出的有限正数，不代表任意新值、机制或客户端版本兼容。</p>
<p>7251 的同 N 多候选原本同值，只改其中一条会产生不同值，正确结果是拒绝；同时修改所有同类候选并同步交叉证据才可保留原有证据等级。没有放宽原规则或修改生产实现。</p></section>
<section><h2>怎样组织后续研究</h2>
<p>建议先做 A＋C：按真实来源层/表/type/字段/对象/阶段划分机制族；共享字段证据和原值核查，把各角色的条件、档位和归属保留为独立任务。17 是本次已有答案样本的规则族数，不能当作整个剩余项目只有 17 个难题。115→17 只是减少重复准备的机会，不是已节省 85% 人时。</p>
<p>D 需要连接独立的基础答案生成路径后再做留出卡验证；不能把“已有答案支持的镜像通过”当作独立求解。当前 C15 正在推进直接链，实验不接管、不提交补丁，也不要求主线切换。</p>
<p>研究并行可采用一名整合者、两条独立机制研究线和一名独立审查者的流水安排，各自只写候选目录，公共规则与正式交付统一整合。此方案本轮只验证了按族分工的数据基础，没有启动或计时多代理研究，不承诺加速倍数。</p>
<p>下一阶段应在主线允许的独立范围选两种不同机制，分别比较按卡处理与按族处理，记录有效研究、核查、返修和等待；预先固定同等交付要求。真实新缓存到来后再核版本并测一张卡完整流程。本轮不能校准前次人时区间或证明单卡 1–3 小时完成。</p></section>
<section><h2>诊断与验证</h2>
<p>首轮 6 个改号失败来自夹具中 exact/relaxed 共享引用被重复改号，已按对象身份只修改一次；第二轮 2 个未达预期来自多候选同值边界，已根据原始候选明确“仅改一个应拒绝／全部同步可保留判定”，增加对应正例。初始结果及脚本均保留，不删除失败记录。最终没有修改 G1 原实现，没有降低其拒绝条件。</p>
<p>本报告和验证由本实验作者完成，不是独立第三方审查。HTML 进行结构/本地链接检查，未做浏览器视觉验收。</p>
<ul><li><a href="results.json">完整统计与三次计时</a></li><li><a href="validation.json">结果核对和来源反例</a></li><li><a href="structure_replay.json">140 行结构回放</a></li><li><a href="structure_mutations.json">84 个合成变体</a></li><li><a href="inputs/manifest.json">冻结输入清单与选择规则</a></li><li><a href="input_hashes.json">运行前后输入哈希</a></li><li><a href="diagnostics/initial_fixture_alias_failure/results.json">首轮夹具失败</a></li><li><a href="diagnostics/multi_carrier_expectation/results.json">多候选预期修正前记录</a></li></ul></section>
<section><h2>复跑</h2><p>在项目根目录使用现有环境；冻结输入已经存在，勿再次 prepare。run 会更新本实验目录的运行结果，随后重建报告。脚本仅支持本项目现有相对布局；没有宣称独立发行工具。</p>
<pre>&amp; .\\.venv\\Scripts\\python.exe -X utf8 -B scripts/skill_route_experiments/run.py run
&amp; .\\.venv\\Scripts\\python.exe -X utf8 -B scripts/skill_route_experiments/verify_and_report.py</pre>
<p>首次冻结命令是同一 run.py 的 prepare；它会拒绝覆盖已有冻结 manifest。未来不同版本应建立新的独立实验版本，不覆盖本次输入。</p></section>'''
    css = 'body{max-width:1120px;margin:32px auto;padding:0 22px;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif;color:#172330;background:#f6f8fa}header,section{background:white;padding:24px 30px;margin:18px 0;border:1px solid #dce3e9;border-radius:10px}h1{font-size:30px;line-height:1.35}h2{font-size:21px}.eyebrow{color:#527283}.lead{font-size:19px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #dce3e9;padding:10px;vertical-align:top;text-align:left}th{background:#edf3f7}a{color:#12689e}code,pre{overflow-wrap:anywhere;background:#eef3f6}pre{padding:14px;white-space:pre-wrap}@media(max-width:700px){body{padding:0 8px}header,section{padding:16px}table{font-size:12px}th,td{padding:5px}}'
    document = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>技能解读提速路线实验</title><style>' + css + '</style></head><body>' + body + '</body></html>'
    (out / 'report.html').write_text(document, encoding='utf-8')

    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
        def handle_starttag(self, tag, attrs):
            if tag == 'a': self.links.extend(v for k, v in attrs if k == 'href')
    parser = Links()
    parser.feed(document)
    missing = [link for link in parser.links if not (out / link).is_file()]
    assert not missing
    experiment.write_json(out / 'report_check.json', {'local_links': len(parser.links), 'missing_links': missing, 'browser_visual_check': 'NOT_RUN'})
    delivery = {'status': 'COMPLETE_BOUNDED_EXPERIMENT', 'new_production_answers': 0,
        'files': {p.relative_to(out).as_posix(): {'bytes': p.stat().st_size, 'sha256': experiment.sha(p.read_bytes())}
                  for p in out.rglob('*') if p.is_file() and p.name != 'delivery_manifest.json'},
        'source_scripts': {p.name: experiment.sha(p.read_bytes()) for p in Path(__file__).parent.glob('*.py')}}
    experiment.write_json(out / 'delivery_manifest.json', delivery)
    print(json.dumps({'validation': 'PASS', 'negative_source_cases': len(tests), 'links': len(parser.links), 'report': str(out / 'report.html'), 'files': len(delivery['files'])}))


if __name__ == '__main__':
    main()
