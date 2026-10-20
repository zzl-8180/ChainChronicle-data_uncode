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
    'message':'候选晋级及一般机制择句仍未实现；模板作用域推断层已启用三批（type1017 试点＋批 3 type8 '
              '严格子集＋批 4 条件扩展双记录映射），仅「推断」档，行级标注「推断（模板试点 type1017）」'
              '或「推断（模板批 3 type8）」或「推断（模板批 4 条件扩展）」，与「确认（类型外推）」不同、'
              '不进入整行确认',
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
