
from pathlib import Path
import json,hashlib,os,shutil
root=Path.cwd();o=root/'output/storage_retention/recycle_g1_20261027';v=root/'output/storage_retention/vault_g1_checkpoint_20261027'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def h(p):
 z=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024**2),b''):z.update(b)
 return z.hexdigest()
def size_tree(p):
 total=0
 for d,dirs,files in os.walk(p,followlinks=False):
  dirs[:]=[n for n in dirs if not (getattr((Path(d)/n).lstat(),'st_file_attributes',0)&1024)]
  for n in files:
   f=Path(d)/n
   if not (getattr(f.lstat(),'st_file_attributes',0)&1024):total+=f.stat().st_size
 return total
build=load(v/'build_report.json');restore=load(o/'restore_consumer_result.json')
assert build['status']=='PASS' and restore['status']=='PASS'
assert (o/'postprocess_result.json').exists()
stats=build['statistics'];review=load(o/'plan_summary_v4_review.json')
post=load(o/'protection_postcheck.json');supp=load(o/'protection_supplement_postcheck.json')
# Additional consumer holds: source content freshly checked against audited v3 identities.
audit=load(o/'consumer_audit.json');bad=[]
for r in audit['potential_candidate_union']:
 p=root/r['path']
 if p.stat().st_size!=r['bytes'] or h(p)!=r['sha256']:bad.append(r['path'])
with (o/'consumer_holds_postcheck.json').open('x',encoding='utf-8') as f:json.dump({'status':'PASS' if not bad else 'HOLD_CHANGED','files':len(audit['potential_candidate_union']),'changed':bad,'basis':'v3 content identity plus archive fresh source hash, then current source rehash'},f,ensure_ascii=False,indent=2)
owned=[o,v,root/'output/storage_retention/vault_g1_20261027',root/'work/storage_recycle_g1_20261027',root/'scripts/storage_retention/recycle_v1']
footprints={p.relative_to(root).as_posix():size_tree(p) for p in owned};overhead=sum(footprints.values())
a=review['counts']['ELIGIBLE_A'][1];p=review['counts']['P_PENDING_SMALL_CLOSURE'][1];gib=1024**3
summary={'status':'G1_ARCHIVE_PASS_RECYCLE_AND_PROTECTION_REVIEW_BLOCKED','archive':stats,'resumption':build.get('resumption',{}),'archive_build':'PASS','restore_consumer':'PASS','review_manifest_sha256':review['sha256'],'archive_manifest_sha256':build['input_manifest_sha256'],'review_A_bytes':a,'review_P_bytes':p,'new_consumer_holds_bytes':review['counts']['PROTECTED_CONSUMER'][1],'owned_logical_bytes':footprints,'owned_logical_total_bytes_before_final_reports':overhead,'space_estimate':{'current_released_bytes':0,'conservative_lower_bytes':0,'A_only_nominal_upper_bytes':max(0,a-overhead),'A_plus_P_nominal_upper_bytes':max(0,a+p-overhead),'basis':'logical bytes only, not measured NTFS physically reclaimable; includes retained failed vault and fixtures; no current budget credit; final report small growth excluded'},'disk_free_bytes_now':shutil.disk_usage(root).free,'protection_postcheck':post['status'],'protection_supplement_postcheck':supp['status'],'consumer_holds_postcheck':'PASS' if not bad else 'HOLD_CHANGED','G2_authorized':False,'G3_agent_implementation':'FORBIDDEN','blockers':['Actual recycle identity/hash restore and failure branches not tested; normal-context aggregate occupancy known, effective quota and safe prompt handling still unproven','Dynamic consumer audit remains incomplete','No permanent safeguard PASS or user explicit unlock plus exact G2 list approval','P exact-byte duplicate proof / contract exception not settled','Protection postchecks: 7 changed and 2 now absent scratch files; existing mainline retirement note matches hashes, still requires host acceptance; G2 full protection baseline must be rebuilt']}
with (o/'FINAL_SUMMARY.json').open('x',encoding='utf-8') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
report=f"""# G1 材料交付：归档通过，回收能力阻塞
本轮用户已授权 G1；未授权 G2。总体结论 **G1 归档与恢复通过；回收能力、保护差异待复核 / G2 BLOCKED**，不能写成 G1 全绿。代理永远不交付或执行 G3 最终释放。

## 当前结果
| 项目 | 实证与状态 |
|---|---|
| W 当前 HTML | 全排除；2236逐卡HTML和根入口与候选无交叉 |
| M 媒体 | 全暂缓；761241媒体文件与候选无交叉 |
| A 归档范围 | {stats['source_paths']:,}原路径，{stats['source_logical_bytes']/gib:.3f}GiB；仅只读保管 |
| A 内容保管 | {stats['unique_contents']:,}种SHA+长度，{stats['unique_logical_bytes']/gib:.3f}GiB唯一逻辑内容，{stats['volume_count']}卷 |
| ZIP 实际逻辑占用 | {stats['volume_bytes']/gib:.3f}GiB；全部{stats['readback_members']:,}成员流式解压SHA+长度通过，原路径→成员→卷全量对账 |
| 恢复 | 新进程、中文/空格路径、同内容多路径、不同历史版本、最大文件、事故恢复文件；39条恢复及{restore['cards']}卡真实旧run输入消费者通过 |
| 固定消费者新增保护 | 10528文件/{review['counts']['PROTECTED_CONSUMER'][1]/gib:.3f}GiB已移出候选，原路径保留；归档只是额外副本 |
| 当前A审议范围 | 196905文件，{a/gib:.3f}GiB；动态消费者未闭合，仍不能执行 |
| P三个ZIP | {p/gib:.3f}GiB；旧源码/规则小闭包约4.91MB已保管，原审查/44输入/隔离树保留；原ZIP未回收 |
| 回收站真实测试 | BLOCKED。15本地检查和18模拟模型通过不能代替12项真实Shell验证 |
| 保护后验 | 初始19700项：{post['status']}；补充74213项：{supp['status']}；新消费者10528项：{'PASS' if not bad else 'HOLD_CHANGED'}。集合有交叉，不相加当唯一文件数 |

保护后验是声明范围内的哈希实证，不是全项目不可变快照：原始输入/全部媒体/依赖树没有全量前后哈希。补充基线在只读归档期间采集；变更详情见各postcheck，不能将其他任务写入静默判为本任务通过。G2前须建立当时完整保护基线并核对当前任务卡。

## 使用哪份清单
- **主持审议**：plan_manifest_v4_review.csv.gz，SHA-256：{review['sha256']}。
- **归档输入绑定**：plan_manifest_v3.csv.gz，SHA-256：{build['input_manifest_sha256']}。它是只读保管范围的较大集合，不能当作回收白名单。
- **当前保护**：protection_manifest_v7.json；含周期/前像、全部明确固定消费者、retained_payloads、正式产物、隔离树、旧/新campaign与所有本任务记录。
- v1混入保留区的问题已排除；v1/v2/旧restore_sample_request只留诊断，禁止用于执行。所有v4审议项的SHA来自冻结内容身份；G2前必须再次逐源重算。

## 空间口径
当前释放 **0字节**。本轮自有归档/中断诊断/恢复/夹具/工具/报告合计约{overhead/gib:.3f}GiB逻辑新增，其中未合格旧归档保留约0.88GiB，未擅自清理。
以当前收紧范围减去上述实测新增，A单独的名义上界约{max(0,a-overhead)/gib:.3f}GiB；A+P约{max(0,a+p-overhead)/gib:.3f}GiB，保守下界均为0。这是未来用户完成最终处置后的逻辑估算，非NTFS物理可释放保证；P契约和未知消费者可能进一步降低收益。旧112GiB数字失效。回收站阶段不释放空间，不把这些估算计入当前预算。

## 不通过项与后续门槛
1. 早期沙箱查询/桌面访问拒绝；正常本机上下文只读复测已成功，E盘回收站现有4,638,780,922字节（约4.32GiB）、11项。有效配额和永久删除提示控制仍未证明。注册表原值MaxCapacity=27647、NukeOnDelete=0不能当117GiB级有效配额证明。没有真实回收后端，没有任何实际入站；停止保源。
2. 需在明确可控的执行环境完成真实合成入站→自身条目定位→同hash恢复、失败/取消/部分成功/重启等验证。不得用模拟或源路径消失冒充通过。NanaZip只读查询获准在沙箱外成功，不等于回收动作获准或已验收。
3. 仍有动态历史消费者UNKNOWN。固定交叉已保护；不得把无命中或归档可恢复当作现有脚本可直接读。
4. 永久防误删机制PASS或用户明示解禁，加精确G2清单SHA逐项批准，缺一不能回收。P尚无存活同hash ZIP副本证明，方向同意不能自动消除安全处置契约冲突。
5. G2前源SHA/长度、保护集合、归档健康和恢复可用重新核验。拟分批：首批≤10件且≤64MiB，后续提议≤100件且≤256MiB；未获批准，不具执行效力。
6. G3只能用户本人决定；代理无清空、最终释放功能。

## 主要验收材料
- ADJUSTED_PLAN.md及本报告的新结论；journal_receipt_schema.json是格式设计，非可执行回收器。
- ../vault_g1_checkpoint_20261027/build_report.json、catalog.json、index_resumed.jsonl、各有效volume ZIP及restore_report。
- micro_checkpoint_postcheck.json、restore_consumer_result.json、postprocess_step_0.json（新进程恢复会再次全量读回归档）。
- consumer_audit.json/md、consumer_holds_postcheck.json、protection_*postcheck.json及压缩前后哈希清单。
- recycle_tests/20261026T165510Z_f293680c2e35/REPORT.md与report.json，区分ACTUAL_LOCAL、SIMULATED、ACTUAL_SHELL；正常上下文只读复测见recycle_tests/20261026T174520Z_2ff01a81430f/report.json。
- P_preservation.json及P_small_closure；旧review/isolated始终原位。
- 新工具17/17 Windows测试；checkpoint版记录位于work/storage_recycle_g1_20261027/archive_tests/checkpoint-bb803a22bf87450d8be56e605919c3f6/test_result.json。旧工具/中断过程全保留。
- WizTree只读小目录导出成功；NanaZip 7.0沙箱外信息查询和只读ZIP交叉检验成功。NanaZip检查不替代SHA；未新增安装或变更全局配置。

声明：本轮未删除任何文件、未回收任何真实候选或合成夹具、未做最终释放、未改全局回收/清理设置、未改retention/state.json、未做Git操作、未联系其他既有对话、未启动新研究或原生提取，未实施W/M两组排除项。仅使用用户授权的原生子代理。
"""
report+='\n## 保护差异需主持确认\n两份后验合计7处变更（任务卡/进度、批3辅助脚本与报告、pages/README），2个当前不存在路径是crit_absorb_20261026/scratch/ledger_prebuild/backlog.json与ledger.jsonl。前基线大小分别83,171,992和199,733,666字节，SHA详见protection_postcheck.json。\n'
report+='主线已有scratch/ledger_prebuild_equivalence.json自述退役这两份一次性对照产物，其记录的两个SHA与本轮前基线完全一致；previous_pages_compact、previous_ledger_compact、previous_ledger_effects均仍可读，分别覆盖41665、41665、69733项。本轮未恢复或修改这些保护路径；该说明只是已有证据，不代替本轮授权或相同字节可恢复性证明，保护面仍不判PASS。见protection_difference_explanation_v2.json；需主持接受差异并确认第三方审查前像依赖完整，不能直接重设基线抹平差异。\n'
report+='回收站配额UI只读核查因Computer Use应用授权超时未进入目标窗口，未改设置。正常上下文的汇总查询可用，不等于真实回收/恢复矩阵通过。\n'
report+='\n## 暂停后的进度复用\n'
resumption=build.get('resumption',{})
report+=f"复用{resumption.get('reused_closed_volumes')}个已闭卷、{resumption.get('reused_source_paths')}条原路径映射，不从头重跑。闭卷先按旧日志容器SHA/长度核对并100%解压复验。复用源hash来自暂停前实读；续建时其余源逐件新读hash，未来G2仍必须重新核全部当前源。\n"
report+='原index.jsonl、build_events.jsonl、未封口volume-000007.zip原样保留；新的完整索引为index_resumed.jsonl，未封口卷仅作为quarantine诊断，不能承载有效映射。verify/restore必须使用archive_store_resume.py。续建6项专用测试和5文件真实内容微批续建/恢复/源hash对照通过，见resume_micro_postcheck.json。\n'
native=load(o/'wiztree_batch_summary_v2.json')
report+='\n## WizTree只读容量交叉证据\n实际非管理员扫描约32.9秒；目录容量有包含关系，不能跨层相加。原始CSV与summary_v2留存。\n\n|目录|逻辑GiB|磁盘分配GiB|\n|---|---:|---:|\n'
for row in native['root_and_direct_children']:
 name=row['path'].replace('\\','/').rstrip('/').split('/')[-1]
 report+=f"|{name}|{row['logical_bytes']/gib:.3f}|{row['allocated_bytes']/gib:.3f}|\n"
report+='\n工具能力依据：https://diskanalyzer.com/guide 。其重复分组不比较内容，不能替代SHA或消费者审计。NanaZip官方项目：https://github.com/M2Team/NanaZip 。本机7.0命令行经受控沙箱外只读查询可用，微批ZIP交叉检验通过；没有安装新软件。\n'
with (o/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
prompt=f"""请只读复核 G1 材料，项目 E:\\代码项目\\锁链战记数据解包。
入口 output/storage_retention/recycle_g1_20261027/REPORT.md、FINAL_SUMMARY.json。
当前结论 G1归档通过，但回收能力未验收且保护面7处变化/2项临时产物已不存在，不能当作G2申请通过；请不要执行任何回收/删除。
审议清单 plan_manifest_v4_review.csv.gz SHA256={review['sha256']}；当前保护 protection_manifest_v7.json。
归档绑定v3，含新增保护项的额外副本；新增10528固定消费者载荷已移出v4候选，源仍保留。
请核对：全量成员SHA+长度/映射、39条恢复与真实最小消费者、保护面后验范围和缺口、P小闭包及同hash副本契约未决、回收站实际测试阻塞及有效配额未知（现有汇总占用已实测4.32GiB/11项）、journal/批参数。
重点：W全排除，M暂缓；44输入/整个隔离树/所有独审/本周期前像/095905和当前代均保护；G3永远用户本人决定。
请分别给出已通过项与缺口，不将模拟通过当真实Shell通过，不据只读归档放行G2，不以原112GiB凑数扩候选。
"""
with (o/'HOST_REVIEW_PROMPT.txt').open('x',encoding='utf-8') as f:f.write(prompt)
artifacts={}
for f in o.iterdir():
 if f.is_file() and f.suffix in ('.json','.md','.txt','.gz'):artifacts[f.name]={'bytes':f.stat().st_size,'sha256':h(f)}
with (o/'ARTIFACT_SHA256.json').open('x',encoding='utf-8') as f:json.dump(artifacts,f,ensure_ascii=False,indent=2)
task=root/'docs/tasks/20261027-storage-recycle-g1.md'
with task.open('a',encoding='utf-8') as f:f.write('\nG1交付：A归档/恢复/最小消费者完成；真实回收能力BLOCKED，G2未申请/未授权。以output/storage_retention/recycle_g1_20261027/REPORT.md和FINAL_SUMMARY.json为准；G3禁止代理实现。旧RUNNING_HANDOFF是历史记录，不表示仍有活跃构建。\n')
print(json.dumps({'status':summary['status'],'report':str(o/'REPORT.md'),'space':summary['space_estimate']},ensure_ascii=False))
