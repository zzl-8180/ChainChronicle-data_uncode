"""Deduplicate the independent verdict; keep missing-source candidates separate."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_layout_paths import read_path
from versioned_outputs import experiment_output
from collections import Counter
from datetime import datetime

ROOT=Path(__file__).resolve().parents[2]
BASE=experiment_output('skill_mechanism_scale')
def read(p): return json.loads((BASE/p).read_text(encoding='utf-8-sig'))
def save(p,x): (BASE/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def time(x): return datetime.fromisoformat(x.replace('Z','+00:00'))
def key(a):
    s=a['source']
    return '|'.join(str(x) for x in [a['effect_id'],s['layer'],s['table'],s['record_id'],a['field_path']])

def main():
    v=read('review/verdict.json'); validation=read('review/validation.json'); collected=read('collection.json')
    assert validation['failed']==0 and collected['all_source_checks_passed']
    for comparison in v['method_equal_sets'].values():
        assert comparison['strict_accepted']['equal_identity_sets']
        assert comparison['strict_accepted']['equal_normalized_values_units_scopes']
    selected=v['arms']['family_serial']['tasks']
    strict=[]; pending=[]
    for task in selected:
        for a in task['accepted_answers']:
            assert a['review_grade']=='ACCEPT_INFERRED'
            strict.append({'task_id':task['task_id'],'cid':task['cid'],'row_id':task['row_id'],
                           'japanese':task['japanese'],'answer':a,'status':'EXPERIMENTAL_NOT_PRODUCTION'})
        for a in task['unresolved_answers']:
            pending.append({'task_id':task['task_id'],'cid':task['cid'],'row_id':task['row_id'],
                            'japanese':task['japanese'],'answer':a,'status':'PENDING_RAW_SOURCE_EVIDENCE_NOT_ACCEPTED'})
    assert {key(x['answer']) for x in strict}==set(v['deduplicated_outcome']['accepted_keys'])
    assert len(strict)==49 and len(pending)==4
    save('accepted_candidates.json',{
        'scope':'Full raw-source-chain scoped inferences only; not confirmed bindings or production promotions',
        'snapshot':collected['snapshot'],'strict_inferred_answers':strict,
        'pending_page_supported_candidates':pending,'confirmed_answers':[],'new_formulas':0,
        'production_promotions':0,'review_reference':'review/verdict.json',
    })
    labels={'local_attack_increase_percent':('攻击','%'),
            'local_damage_reduction_percent':('减伤','%'),
            'local_movement_increase_percent':('移速','%'),
            'critical_probability_percentage_points':('暴击概率','个百分点'),
            'critical_damage_coefficient_increment':('暴伤系数增量','（加算倍率）')}
    rows=[]
    for task in selected:
        answers=task['accepted_answers']; displays=[]
        for a in answers:
            n=a['review_normalized']; label,unit=labels[n['unit']]
            displays.append(f'{label} {n["value"]:+g}{unit}')
        if answers:
            scope='完整原始引用链支持；仅单项局部贡献，装载/资格条件下的关联推断；非整卡最终值'
        elif task['task_id']=='A04':
            scope='原始角色引用缺件，4项页面支持候选另存待补证，暴击率无适用字段'
        else:
            scope='type108消费者语义缺失；原值不计答案'
        rows.append({'task_id':task['task_id'],'cid':task['cid'],'japanese':task['japanese'],
                     'accepted_count':len(answers),'result_zh':'；'.join(displays) or '未解', 'scope_zh':scope})
    phase_rows=[]
    for arm in collected['arms']:
        timing=read(f'{arm}/timing.json')
        if arm=='card_serial':
            start=time(timing['started_at']); end=time(timing['finished_at'])
            first=time(next(e['at'] for e in timing['events'] if e['phase']=='card_validation_started'))
            tail=time(next(e['at'] for e in timing['events'] if e['phase']=='independent_validation_started'))
            for name,left,right in [('准备与首卡研究',start,first),('逐卡工作阶段',first,tail),('独立验证与整理',tail,end)]:
                phase_rows.append({'arm':arm,'phase':name,'seconds':(right-left).total_seconds()})
        else:
            for phase in timing['phases']:
                start=phase.get('started_at') or phase['started_at_utc']; end=phase.get('finished_at') or phase['finished_at_utc']
                phase_rows.append({'arm':arm,'phase':phase.get('phase',phase.get('name')),'seconds':(time(end)-time(start)).total_seconds()})
        added=collected['arms'][arm]['completion_adjustment_seconds']
        if added: phase_rows.append({'arm':arm,'phase':'最后封存检查追加尾段','seconds':added})
    t=collected['observed_timing']; d=v['deduplicated_outcome']
    overhead=(t['family_parallel_sum_seconds']/t['family_serial_seconds']-1)*100
    summary={
        'snapshot':collected['snapshot'],'headline':'分组串行本轮少用22.4%；再并行少用12.9%。严格接受49项推断答案，完全确认0项。',
        'plain_conclusion':[
            '先弄清共同机制，再批量核对卡片，在这轮比逐卡处理更省时间。并行又缩短了一些等待时间，但累计代理投入增加。',
            '三种方法最终拥有相同的49项严格接受答案，分布在23张卡；这些都是有完整原始来源链支持的局部推断，不是实机确认或整卡全面解完。'],
        'method_outcomes':{'card_serial':'49项严格推断；另4项待补证','family_serial':'49项严格推断；另4项待补证','parallel':'49项严格推断；缺件卡留未知'},
        'timing_interpretation':[
            f'A→B比较分组/批量策略：节省{t["grouping_difference_seconds"]:.1f}秒，约{t["grouping_saving_percent"]:.1f}%。两组连页面支持的4项弱候选也相同，严格答案的身份、数值、单位和范围均一致。',
            f'B→C比较分组后的并行部署：共同49项严格答案下再少{t["parallel_difference_seconds"]:.1f}秒，约{t["parallel_saving_percent"]:.1f}%；A→C整体少{t["combined_saving_percent"]:.1f}%。C没有提交那4项缺原始角色链的弱候选，因此全部提交物并不完全相同；不能把12.9%认定为纯并行的因果收益。',
            f'C累计代理投入{t["family_parallel_sum_seconds"]:.1f}秒，比B多{overhead:.1f}%。较快拿到结果与减少总投入是两件事。并行研究结束原记录为287.4秒；主表加入5.965秒封存后最终检查，采用293.3秒。'],
        'reliability_interpretation':[
            '可靠新增口径：49项通过独审、完整原始角色→父技能→载体→字段来源链支持的推断级数值解释，23张卡/23条描述/23条载体；全部三条路线重复发现只计一次。严格确认的描述绑定0，新公式0，正式写库0。',
            '另4项来自20607：局部数值算术与CACHE父子记录可核，但原始角色引用表未在冻结包，只有页面支持，隔离为待补证候选，不混入49项。',
            '61个基线未解效果中，严格接受49，仍未解12（含上述4项待补证、该卡1项暴击率缺证、7项区域回复缺证）。回复原值观察、相同公式复算不计新答案。',
            '攻击/减伤/移速是本项局部贡献；暴击概率用百分点，暴伤是系数加算增量。必须满足相应能力装载、资格/列表分派条件，不包含其他来源、条件增强或最终结算。'],
        'limitations':[
            '样本来自两个机制族，主要测试既有局部公式的归属解释；不能外推新机制逆向、全部角色或整卡完成速度。三个方法各运行一次，31卡不是31次独立方法实验。',
            'A/B第一波同时运行，C第二波运行；虽继承同模型配置，代理个体差异、服务器排队、工具等待和运行时段均未独立控制。以上比例是本轮观测，不是稳定节省承诺或统计显著性结论。',
            'A/B自然复用知识未被禁止。各组允许辅助程序且验证实现不同，自检数量不同不能比较为可靠性高低；统一质量依据来自独立审查。',
            '共同输入普查/准备和最终报告整合未完整单独计时，不隐去后冒充端到端节省。独审分盲读与最终裁决两阶段，中间空闲不算连续作业；首个盲读时间戳晚于初始目录/协议读取，前段时长未知。',
            '分组并行组对缺原始角色表更保守，最终只在共同严格接受集上等价，不能用更多弱候选作为更高产量，也不能把本次差异归因于并行本身。'],
        'validation_notes':[
            f'独审先只看冻结来源保存pre_review，再在四组提交哈希冻结后看答案；{validation["passed"]}项独立检查通过、失败{validation["failed"]}，审查{validation["submitted_answers_checked"]}项提交数值（含跨路线重复），最终去重49项严格接受。',
            f'74份输入、{validation["frozen_arm_files"]}份研究提交哈希保持不变；独审没有导入或执行研究组/生产实现。原值算术核对不能代替语义审查，后者逐卡载于review/verdict.json与REPORT.md。',
            '独审没有重新执行游戏原生代码或实机验证；部分移动/暴击数值证据继承已确认规则与报告，不能写成这轮重做了原生证明。'],
        'outcome':d,'method_equal_sets':v['method_equal_sets'],'card_rows':rows,'phase_rows':phase_rows,
        'effect_type_counts':dict(Counter(a['answer']['review_normalized']['unit'] for a in strict)),
    }
    save('final_summary.json',summary)
    print(json.dumps({'strict_inferred':len(strict),'pending':len(pending),'cards':d['cards'],'confirmed':d['confirmed']}))

if __name__=='__main__': main()
