"""Build a scoped research handoff, preserving all original experiment files."""
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'output/skill_mechanism_scale/20261104'
RELEASE=ROOT/'output/share_bundle/20261104-mechanism-first-handoff-r1'
PAYLOAD=RELEASE/'payload'
ISOLATED=ROOT/'work/mechanism_first_handoff_20261104/isolated_readback'
SNAPSHOT='8d96f313-cf9451c6ff47fcfb'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def stable_copy(src,dst):
    before=sha(src); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    assert sha(dst)==before==sha(src),str(src)
    return before

README='''# 机制优先批量解卡 研究交接包

这是范围明确的研究交接包（B类成果），用于接收已有实验结果和安排后续已授权主线。方法已并入仓库现行方案§1.6；本包没有实施生产接入。不是全项目备份、完整解包发行、新缓存或新卡自动解算工具。

## 先读与使用

1. 阅读 [执行细则与验收标准](EXECUTION_PLAN.md)，再看 [49项推断](data/accepted49.json)、[4项待补证](data/pending4.json)、[61效果去向](data/effect_disposition61.json) 和 [剩余缺口](GAPS.md)。
2. 用Python 3.10或更高版本，在解压目录运行 `python -I -B verify_bundle.py`。仅标准库、无安装/网络/手机要求；程序只读包内文件，结果打印到终端，不重写历史审查。非零退出表示包不完整或来源/计数/算术不符。
3. 需要上下文时看 [实验报告](evidence/experiment/report.html)、[独审报告](evidence/experiment/review/REPORT.md)、[逐项裁决](evidence/experiment/review/verdict.json)。核验通过仍不等于当前主线可直接晋级。
4. 将 [主持提示词](HOST_PROMPT.md) 交给现任主持。包内路径以解压根为准；提示词中的项目路径用于已有仓库，另一台机器须定位其实际仓库根。没有自动向主持发送。

## 数量与证据等级

- 冻结基线：`8d96f313-cf9451c6ff47fcfb`（C14实验快照），31卡31描述61未解效果。
- 严格接受49项局部数值推断，23卡/23描述/23来源记录；Y.G.23项/15卡，非Y.G.26项/8卡。
- 20607另有4项仅页面上游支持候选，缺原始角色引用，单独待补证，不计49。
- 严格未知12效果＝待补证4＋20607暴击率1＋type108回复7。
- 完全确认描述绑定0，新公式0，正式晋级0。三路线重复发现只计一次。现有公式的原值复算不是新公式。
- 能力装载、相应资格/列表分派满足时的局部贡献；不表示整卡最终攻击、最终HP损失、完整暴击概率或实机结果。

## 接入当前主线

主持先核当前正式campaign/snapshot/rules及在途任务，逐项给出仍未解可接入、已存在不新增、来源/语义冲突、版本变化待核。C15可能已前进，不能把49当当前净增承诺。不向正在生成/送审的C15包插入候选；后续周期按用户当场授权安排。既有公式证据和独审可按未变范围复用，新消费者、部分绑定门控和当前基线差异仍需必要验证。

`accepted49.json`保留实验完整答案字段与审查分级；source.input_relative_path应从 `evidence/experiment/input/` 解析，JSON指针在该文件内使用。每项的日文、effect_id、原值、单位、条件、证据等级均保留。原始charainfo/skilllist/bossinfo、31张冻结页面、规则与已有小证据报告共74文件随包提供，核源无需作者历史工作目录。

## 缺失与边界

本包不含兼容APK角色原表（20607上游引用待补）、type108尚未取得的消费者证据、实机记录、游戏APK/媒体、整个项目工具链、最新C15正式输出或完整主线运行依赖。移动/暴击部分继承已确认规则与报告，不冒充本次重做原生。参考路径中更早报告未全部收入，其缺件和证据继承范围沿独审披露。当前主线接入/重新从APK解包需要原仓库及其声明依赖，包内核验只针对冻结研究证据与完整性。

`evidence/experiment/`原样保存全部扩样实验文件；其中历史清单/脚本使用原布局，按证据归档，勿在冻结副本上重跑生成器。`evidence/research_scripts/`保留实验整合脚本用于阅读，非本包执行入口。唯一推荐只读入口为 `verify_bundle.py`。`context/plan_integration_excerpt.md`是方法条款快照，当前规范以仓库最新版为准；不会用旧模型/进度替代当前主持配置。

## 校验和复现范围

`manifest.json`列出全部包成员（自身除外）的大小、SHA-256和来源锚点。核验器检查成员全集、74输入/研究提交哈希、49/4分档、61效果去向、严格49的原始角色→父→唯一载体→字段链及既有公式算术，并核其推断等级。它复用已归档的语义裁决，不重新证明绑定或执行原生。

打包方将ZIP解压到独立目录，从该目录用现有Python `-I -B` 运行包内核验器。实际结果、环境版本、ZIP哈希和大小见发行目录 `release_manifest.json`。这是目录隔离验证，不是新机器安装测试。所有文件仅本地交付，未上传或发布。
'''

GAPS='''# 剩余缺口及完成条件

| 缺口 | 影响 | 下一项证据与完成条件 |
|---|---|---|
| 20607原始角色上游引用缺件 | 4项局部候选暂不进入严格49 | 在既有兼容APK主表中核角色/版本身份、skillid[1]→42060700→42060701；不得从samechara、页面数字或相似ID反推。补齐后重核条件与当前基线，独审可调整分档；不是补一个文件就自动确认 |
| 20607暴击概率无适用字段 | 1效果仍未知 | 1095缺param5；同父type51 param0=.4只有观察。需适用消费者/规则和该描述归属证据，不能补零或套1095概率公式 |
| type108周期/超上限回复缺消费者证据 | 7效果未知，逐卡定位见effect_disposition61.json | 需适用代码读点/局部消费公式、对象、时点、持续/次数、超上限及分支条件；原值1.25/1.5、2、30或相邻type13/26/27不构成替代证明 |
| 装载、资格、实际来源叠加和最终战斗值未验证 | 所有49项只为有条件的局部推断 | 继续保留已装载/资格通过及排除其他来源条件；用户另有运行时目标时才在相应授权范围取证。不是单项数值交付必须恢复完整引擎 |
| 当前基线与生产消费者尚未接入 | 当前正式净增未知；正式晋级0 | 主持在稳定当前版本逐项对账后建候选模块，按主线已有正反例/独审/生成/账本/保护检查验收；不能直接导入实验JSON或删掉旧P4 |
| 通用新卡适用性和长期提速未证明 | 不承诺任意新卡或固定提速比 | 实验固定样本不是通用求解器；分组优先、并行可选，后续实际批次继续记录同等级收益和总投入，不为完善统计重跑无变化历史 |

49项的剩余运行时限制不阻止保留推断成果；4项缺上游原件不阻塞成熟Y.G.项。是否新增原生/实机/采集工作由对应授权任务决定，本包不自动触发。
'''


def main():
    assert not (RELEASE/'release_manifest.json').exists(),'Delivered release is immutable; choose a new release ID'
    assert not ISOLATED.exists(),'Do not overwrite an earlier isolated readback'
    size=sum(p.stat().st_size for p in SOURCE.rglob('*') if p.is_file())
    assert shutil.disk_usage(ROOT).free>size*3+20*1024**2,'Not enough room for payload, ZIP and readback'
    PAYLOAD.mkdir(parents=True,exist_ok=True)
    originals={}
    for p in sorted(SOURCE.rglob('*')):
        if p.is_file():
            rel=p.relative_to(SOURCE)
            originals[p.relative_to(ROOT).as_posix()]=stable_copy(p,PAYLOAD/'evidence/experiment'/rel)
    for p in (ROOT/'scripts/skill_mechanism_scale').glob('*.py'):
        originals[p.relative_to(ROOT).as_posix()]=stable_copy(p,PAYLOAD/'evidence/research_scripts'/p.name)
    for source,dest in [
        ('docs/tasks/20261104-mechanism-first-execution.md','EXECUTION_PLAN.md'),
        ('docs/tasks/20261104-mechanism-first-host-prompt.md','HOST_PROMPT.md'),
        ('scripts/release/verify_mechanism_handoff.py','verify_bundle.py')]:
        originals[source]=stable_copy(ROOT/source,PAYLOAD/dest)
    plan_path=ROOT/'docs/角色技能完整解读实施方案.md'
    plan=plan_path.read_text(encoding='utf-8')
    excerpt=plan[plan.index('## 1.6 '):plan.index('## 2. ')]
    excerpt=excerpt.replace('tasks/20261104-mechanism-first-execution.md','../EXECUTION_PLAN.md').replace('tasks/20261104-mechanism-first-host-prompt.md','../HOST_PROMPT.md')
    (PAYLOAD/'context').mkdir(exist_ok=True)
    (PAYLOAD/'context/plan_integration_excerpt.md').write_text('# 现行方案的方法增补快照\n\n来源：docs/角色技能完整解读实施方案.md；本文件仅存§1.6，不替代当前主线状态或其他章节。\n\n'+excerpt,encoding='utf-8')
    (PAYLOAD/'README.md').write_text(README,encoding='utf-8')
    (PAYLOAD/'GAPS.md').write_text(GAPS,encoding='utf-8')
    candidates=load(SOURCE/'accepted_candidates.json'); targets=load(SOURCE/'input/targets.json')
    strict=candidates['strict_inferred_answers']; pending=candidates['pending_page_supported_candidates']
    common={'snapshot':SNAPSHOT,'adoption_status':'NOT_APPLIED_TO_PRODUCTION','source_input_root':'evidence/experiment/input/',
            'review':'evidence/experiment/review/verdict.json','current_baseline_reconciliation':'REQUIRED_AT_ADOPTION'}
    save(PAYLOAD/'data/accepted49.json',{**common,'evidence_grade':'INFERRED_FULL_RAW_CHAIN','items':strict})
    save(PAYLOAD/'data/pending4.json',{**common,'evidence_grade':'PENDING_RAW_UPSTREAM_NOT_ACCEPTED','items':pending})
    accepted_ids={x['answer']['effect_id'] for x in strict}; pending_ids={x['answer']['effect_id'] for x in pending}
    states=[]
    for t in targets:
        for e in t['baseline_effects']:
            eid=e['effect_id']
            if eid in accepted_ids:
                state='ACCEPTED_INFERRED_FULL_CHAIN'; gap='运行时装载/资格与最终叠加未核；当前基线及生产消费者待对账验收'
            elif eid in pending_ids:
                state='PENDING_RAW_UPSTREAM'; gap='20607缺原始角色引用；仅页面支持，四项不计严格接受'
            else:
                state='UNKNOWN'; gap='type108适用消费者/时序/超上限语义缺失' if t['family']=='heal108' else '1095缺param5；type51观察不可借用规则'
            states.append({'task_id':t['task_id'],'cid':t['cid'],'row_id':t['row_id'],'effect_id':eid,
                           'japanese':t['japanese'],'yg':t['baseline_description']['yg'],'baseline_effect':e,
                           'source_skill':t['source_skill'],'handoff_status':state,'remaining_gap':gap})
    save(PAYLOAD/'data/effect_disposition61.json',{**common,'strict_unresolved':12,'items':states})
    counts={'strict_inferred_answers':49,'strict_cards':23,'yg_inferred_answers':23,'yg_cards':15,
            'non_yg_inferred_answers':26,'non_yg_cards':8,'pending_candidates':4,'strict_unresolved_effects':12,
            'baseline_effects':61,'confirmed_description_answers':0,'new_formulas':0,'production_promotions':0}
    files={p.relative_to(PAYLOAD).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(PAYLOAD.rglob('*')) if p.is_file() and p!=PAYLOAD/'manifest.json'}
    manifest={'schema':'mechanism-first-handoff-1','created_at':datetime.now(timezone.utc).isoformat(),
              'release_id':RELEASE.name,'category':'B_SCOPED_RESEARCH_HANDOFF_NOT_FULL_UNPACK','snapshot':SNAPSHOT,
              'counts':counts,'files':files,'file_count':len(files),'logical_bytes':sum(v['bytes'] for v in files.values()),
              'original_source_sha256':originals,'current_plan_source_sha256':sha(plan_path),
              'dependencies':{'offline_bundle_verification':'Python>=3.10, standard library only; no external inputs',
                              'production_adoption':'Current project checkout, its declared dependencies and a stable current snapshot; not provided here'},
              'not_included':['APK character raw table for20607','new type108 consumer evidence','runtime/live-game proof','APK/media/full project toolchain','current C15 outputs'],
              'limits':['49 are inferred local contributions, not confirmed bindings','4 page-supported candidates are pending','No production consumer implemented','Directory-isolation check, not fresh-machine install']}
    save(PAYLOAD/'manifest.json',manifest)
    # Fail before archiving if payload extraction or derived lists are inconsistent.
    preliminary=subprocess.run([sys.executable,'-I','-B',str(PAYLOAD/'verify_bundle.py')],cwd=PAYLOAD,capture_output=True,text=True,encoding='utf-8')
    assert preliminary.returncode==0,preliminary.stdout+preliminary.stderr
    archive=RELEASE/'mechanism_first_handoff_r1.zip'
    assert not archive.exists(),'Preserve previous archive; use a new release ID'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(PAYLOAD.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(PAYLOAD).as_posix())
    ISOLATED.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():
            destination=(ISOLATED/name).resolve()
            assert destination.is_relative_to(ISOLATED.resolve()),name
        z.extractall(ISOLATED)
    checked=subprocess.run([sys.executable,'-I','-B',str(ISOLATED/'verify_bundle.py')],cwd=ISOLATED,capture_output=True,text=True,encoding='utf-8')
    save(RELEASE/'isolation_receipt.json',{'command':['python','-I','-B','verify_bundle.py'],'cwd':str(ISOLATED),
         'exit_code':checked.returncode,'stdout':checked.stdout,'stderr':checked.stderr,'environment':'Existing project Python; isolated directory, no installation test'})
    assert checked.returncode==0,checked.stdout+checked.stderr
    result=json.loads(checked.stdout)
    assert all(sha(ROOT/rel)==h for rel,h in originals.items()),'Original source changed while packaging'
    save(RELEASE/'release_manifest.json',{'release_id':RELEASE.name,'category':manifest['category'],'counts':counts,
         'archive':{'file':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive)},
         'payload_manifest_sha256':sha(PAYLOAD/'manifest.json'),'payload_files_including_manifest':len(files)+1,
         'validation':result,'isolation_receipt':'isolation_receipt.json','published':False})
    (RELEASE/'README.md').write_text('# 机制优先研究交接发行\n\n阅读 [交接说明](payload/README.md)、[执行细则](payload/EXECUTION_PLAN.md)、[主持提示词](payload/HOST_PROMPT.md)。\n\n独立包：[mechanism_first_handoff_r1.zip](mechanism_first_handoff_r1.zip)。49项推断与4项待补证严格分开，正式晋级0。核验与ZIP哈希见 [release_manifest.json](release_manifest.json)，隔离读回见 [isolation_receipt.json](isolation_receipt.json)。\n',encoding='utf-8')
    print(json.dumps({'passed':True,'archive_bytes':archive.stat().st_size,'payload_files':len(files)+1,'verification':result},ensure_ascii=True))

if __name__=='__main__': main()
