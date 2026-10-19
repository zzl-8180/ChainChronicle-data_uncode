# P3B9 描述批量绑定

- 负责人：C `/root/p3b9_implement`；2026-10-19；状态：C已完成并冻结停写，待独立新D。
- 目标：比较普通 type8 攻防移与既有 Boss 纯句族，找到可证且覆盖收益较高的有限队列；候选不计真实覆盖。
- 写入：本任务卡、`work/character_skills_p3b9/`、`output/character_skills/description_bindings/p3b9_batch/`。
- 共享源码、正式 profiles/gaps、根交接、主持进度、旧批证据/审查、原始输入与依赖只读。
- 已核：B8 D R1 通过；其 PENDING 为阶段冻结。现存其他任务写入未接管。
- A结果：type8三效果148来源/页/角色、77种实际子类型；80含generic同路径、68仅generic中性。3条落在窄已知消费者集合仍需语义/条件审定，没有得到几十/百条可证队列。主持补充后找到普通type67现成规则条件纯句178初选，去14带sub/1非整源后163来源/页/cid；156主等价候选＋6原文未排自身但阈值2的差异＋1持有者jobtype缺失，均未绑定。建议type67优先，Boss type0纯单敌26/type3周围全敌20为两个备选，type22现成18保留。详见`output/character_skills/description_bindings/p3b9_batch/PHASE_A.md`第0节。
- 核验：64受控Boss候选均唯一APK原行、准确source/F0/控制/local公式和自身引用；另4旗标反例保留。12份开工快照及当前正式文件hash不变；没有新增绑定/字段、没有新原生测试或正式重建。
- B授权：最多162条（156主候选＋6阈值差异），30620310缺持有者jobtype保留未知；Boss46/type8不扩。必要独立模块/scope与profiles/gaps、本线根交接整合已授权，旧批审查/交接及主持进度只读。
- B进展：9/9有界native通过，实际同阵营alive列表后额外active/职业聚合位图和AND筛选，未直接排自身；五worker真实参数/Calc/阈值1/2/2.9/乘加已核。162当前原表引用均ordinary skillid[3]，全反向sub为0、无范围外当前引用；scope冻结全部原表/原行/范围与未来变更拒绝。绑定预检162/162，未为原始缺失字段补0。
- B实际：162唯一/162页描述、336唯一/336页效果槽、162角色，全部hint升级；当前真实370/提示11437/未知29788、分母41595。字段三口径0，2233部分/0仅未知/3完整不变；82013完整答案/重复、149旧绑定/强度、277/287、101/31、三旧完整profile和全部非目标/未知保留。
- C自检：native9/9、专项10/10、边界2117/2117、标准JSON根162/全引用162/反向sub0，GBK14/DOM338、verify189/189、A—P与12相关产物一次重建字节一致。6条阈值差异在可见condition明确展示，聚合职业位图和真实alive/active门控不省略。
- 稳定性后仅前置已有source/raw冻结检查以拒绝非法selector；主持同意定向167/167（162正式完整binding不变＋字符串/正负inf/NaN/bool拒绝不抛异常）。没有重复总链、CLI/DOM或native，没有改变正式产物。
- 下一步：`P3B9_HANDOFF.md`、README/ledger/来源/排除/冻结清单交新D；C停写，整改续本C，复验续同D。C自检不是独立审查。
