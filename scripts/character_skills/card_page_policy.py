"""Shared, explicitly separated presentation metrics and actual implementation state."""
INFERENCE_STATUS={
    'skill_candidate_promotion_enabled':False,
    'general_mechanism_layer_enabled':False,
    'template_inference_pilot_enabled':True,
    'template_inference_pilot_scope':'type1017「戦場バフ」纯句式家族（pilot_design.md 批 1：341 行/341 cid）；'
                                     '只升「推断」档，逐行对象位图审核，不进整行确认',
    'template_inference_b3_type8_enabled':True,
    'template_inference_b3_type8_scope':'家族 #3「⟨ATTR⟩が上がる。」type8 子集严格范围'
                                        '（b3_type8_scope.md 批 3：Tier1 40 行/40 cid，全 APK）；'
                                        '只升「推断」档，方向/句位/句后文本/同文次数逐行审核，不进整行确认',
    'template_inference_b4_cond_enabled':True,
    'template_inference_b4_cond_scope':'句后条件扩展——基础 type8 记录＋兄弟 sub 记录条件增幅，'
                                       '双记录映射（b4_cond_scope.md 批 4：审计行集 172 行，候选 37 行）；'
                                       '只升「推断」档，兄弟记录覆盖匹配/阈值核对/门控 A·B·C 分级逐行审核，'
                                       '基础句值行与条件增幅值行分列、各自注明来源记录，不跨记录合并数值',
    'template_inference_b5_xtable_enabled':True,
    'template_inference_b5_xtable_scope':'type1017 严格句跨表扩展——job_ability/supporterskill 行记录'
                                         '无参数槽，值行来源＝链上 skilllist 记录（job：段位↔skill_ids '
                                         '位置序→65000002；supporterskill：段位↔abi0/abi1 位置序→121009）'
                                         '（b5_xtable_scope.md 批 5：审计行集 257 行，候选 211 行）；'
                                         '只升「推断」档，段位↔链位置对应/对象位图/方向/未主张活性槽逐行审核，'
                                         '不跨记录合并数值，归属为数据侧结构对应（引擎侧装载路径无原生核实）',
    'template_inference_b6_bossbuff_enabled':True,
    'template_inference_b6_bossbuff_scope':'味方全体必殺バフ家族（Top20 #1）——bosspattern/denju/'
                                           'denju_limit_break_info/charainfo 行的 bossskill type13 '
                                           '子记录解析（b6_bossbuff_scope.md 批 6：审计行集 2,137 行，'
                                           '晋级 1,349——20261020 B6-RV-01 修复：同属性集合竞争 '
                                           'ally-buff 句 30 行降级留 hint）；只升「推断」档，G1–G7 门控'
                                           '（链可达/唯一 type13 载体/形状匹配/crit 排除/charainfo 同文 '
                                           'pattern 唯一/同记录家族冲突＋同属性竞争 ally-buff 句检测/'
                                           '同文一次）逐行审核；非首段行按唯一载体＋形状匹配'
                                           '化解归属（20261020 主持裁决，同文多次/方向冲突仍一律 hint）；'
                                           '不跨记录合并数值，归属为数据侧结构对应（引擎侧装载路径无原生核实）',
    'template_inference_b7_sympathy_enabled':True,
    'template_inference_b7_sympathy_scope':'共鳴アビリティ家族（sympathy 3000/3005/3006）——sympathy 组 '
                                          'skilllist 行的 ability3000 载体解析：值行来源＝主记录自身'
                                          '（若 3000）或相邻 sub1（skillid+1，ability3000）'
                                          '（b7_sympathy_scope.md 批 7：sympathy 组 2,232 行，'
                                          'buff 语义行 794，预分类晋级候选 96——实施逐行审核可再收缩）；'
                                          '只升「推断」档，G1–G8 门控（句唯一子串/buff 形状/主记录类型/'
                                          '属性全有规则/唯一载体形状匹配/競争句/样本域 CACHE/槽值方向）'
                                          '逐行审核；3005/3006 自身参数无规则不消费（派发证据只到 3000，'
                                          'occurrence 补证不可行）；值行 rule_key 只允许 skilllist|3000|*；'
                                          '非首段行按唯一载体＋形状匹配化解归属（批 6 裁决沿用）；'
                                          '不跨记录合并数值，归属为数据侧结构对应（引擎侧装载路径无原生核实）',
    'template_inference_b8_crit2012_enabled':True,
    'template_inference_b8_crit2012_scope':'暴击增益——bosspattern/denju/charainfo/dlb/heroic 行的 '
                                          'bossskill type13 中继→s_ability→skilllist ability2012 '
                                          '真实链载体解析：值行只消费 skilllist|2012|/param4'
                                          '（暴击率加算，pp）/param5（暴伤系数加算）；'
                                          '（b8_crit2012_scope.md 批 8：候选池 C∪批6/7hint 含 '
                                          'クリティカル 3,837 行，实测晋级候选全库 343 行/'
                                          'Y.G. 159 行——实施逐行审核可再收缩）；只升「推断」档，'
                                          'G1–G8 门控（句唯一子串/链可达/唯一载体＋type13 中继/'
                                          '属性形状/样本域 CACHE 406 条/对象相容/方向/跨 cid 守卫）'
                                          '逐行审核；普通 1110→1095 暴击段单列不进本批；D1 裁决：'
                                          '时长值行仍归批 6 t13 /skillparam3，b8 只在 note 登记载体 '
                                          'param0；APK 载体域外留 hint；不跨记录合并数值，归属为'
                                          '数据侧结构对应（引擎侧 s_ability 装载路径无原生核实）',
    'template_inference_b9_debuff_enabled':True,
    'template_inference_b9_debuff_scope':'敵デバフ家族（Top20 #6「攻撃した敵の⟨ATTR⟩が（一定時間）'
                                         '下がる。」及同形变体）——skilllist/supporterskill 容器行 '
                                         'own sub_effect 链→skilllist ability99 PowerDrain 载体解析：'
                                         '值行只消费 skilllist|99|/param0（时长，游戏秒）/param7'
                                         '（受击目标攻击倍率加算）/param8（移速因子加算，已核样本域仅 '
                                         '43023616 单条、逐行披露）/param9（受伤量倍率加算＝「防御』'
                                         '下降的表现层口径，不是固定防御减少）；'
                                         '（b9_debuff_scope.md 批 9：广筛敵デバフ句 973 行/451 cid'
                                         '（Y.G. 208/77），实测晋级候选全库 35 行/Y.G. 11 行——'
                                         '载体 2003 形状同构但无规则 431 行、方向冲突 77 行（B1 '
                                         '30338 防线）等 938 行留 hint）；只升「推断」档，P1–P6 门控'
                                         '（敵減益半句逐字对象/own sub99 链可达/唯一载体/形状双向/'
                                         '竞争句/方向按符号/跨 cid 守卫）＋B1 防线（pattern 行不经 '
                                         'sub_effect 伪影消费；我方增益句不挂敌方减益值）逐行审核；'
                                         'p7/p8 负值＝加算池下降贡献（非乘数<1、非独立 debuff 槽）；'
                                         '不跨记录合并数值，归属为数据侧结构对应（引擎侧装载路径无原生核实）',
    'message':'候选晋级及一般机制择句仍未实现；模板作用域推断层已启用八批（type1017 试点＋批 3 type8 '
              '严格子集＋批 4 条件扩展双记录映射＋批 5 跨表扩展＋批 6 必殺バフ bossskill 子记录解析＋'
              '批 7 共鳴 ability3000 载体解析＋批 8 暴击 2012 链载体解析＋批 9 敵デバフ ability99 载体解析），'
              '仅「推断」档，行级标注「推断（模板试点 type1017）」或「推断（模板批 3 type8）」或'
              '「推断（模板批 4 条件扩展）」或「推断（模板批 5 跨表 type1017）」或「推断（模板批 6 必殺バフ）」或'
              '「推断（模板批 7 共鳴）」或「推断（模板批 8 暴击 2012 链）」或「推断（模板批 9 敵デバフ）」，'
              '与「确认（类型外推）」不同、不进入整行确认',
    'zero_inference_meaning':'未晋级候选仍留 hint，不代表全库无hint',
    'B_zero_reason':'无经实现入页的新增机制；并非原数据不存在机制',
    'basic_mapping_note':'基础职业名称沿用名册的推断映射，与技能候选层分开标注',
}


def metrics(coverage):
    n=coverage['N_all'];num=coverage['N_num'];a=coverage['A']
    cross=coverage['evidence_cross'];confirmed=sum(r.get('确认',0) for r in cross.values())
    inferred=sum(r.get('推断',0) for r in cross.values())
    def item(count,denominator,label):return dict(count=count,denominator=denominator,rate=count/denominator if denominator else 0,label=label)
    return dict(A=item(a,num,'A率（数值/公式行率，不是已解释率）'),
                whole_row_confirmed=item(confirmed,n,'整行确认率'),
                original_A=item(coverage['original_A'],n,'原文A'),C=item(coverage['C'],n,'C仅未知'),
                A_whole_row_unknown=item(cross['A'].get('未知',0),a,'A中整行未知'),
                whole_row_inferred=item(inferred,n,'整行推断'),E=coverage['E'],N_all=n,N_num=num,
                whole_row_confirmed_scopes=self_split(coverage,n),
                implementation_status=INFERENCE_STATUS)


def self_split(coverage,n):
    """H-01（DeepSeek 20to39审查）：整行确认内部分两类口径，仅拆分呈现，不降级判定。
    记录级=REVIEWED_RECORD（如30236基线18行）；类型外推=BY_TYPE_EXTRAPOLATED（冻结P3B9/P3B10模板行）。
    campaign 聚合层若未带该字段则显示为不可用，不以零冒充。"""
    scopes=coverage.get('confirmed_rows_by_scope')
    if scopes is None:
        return dict(record=None,by_type_extrapolated=None,denominator=None,
                    label='整行确认口径拆分（记录级/类型外推）',status='NOT_AVAILABLE_IN_THIS_AGGREGATION')
    return dict(record=scopes.get('REVIEWED_RECORD',0),by_type_extrapolated=scopes.get('BY_TYPE_EXTRAPOLATED',0),
                mixed=scopes.get('MIXED',0),denominator=n,
                label='整行确认口径拆分（记录级REVIEWED_RECORD/类型外推BY_TYPE_EXTRAPOLATED）')


def summary_text(summary):
    return '；'.join(f"{summary[k]['label']} {summary[k]['count']}/{summary[k]['denominator']}（{summary[k]['rate']:.1%}）"
                    for k in ('A','whole_row_confirmed','original_A','C'))
