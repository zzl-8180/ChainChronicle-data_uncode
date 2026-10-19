"""Shared, explicitly separated presentation metrics and actual implementation state."""
INFERENCE_STATUS={
    'skill_candidate_promotion_enabled':False,
    'general_mechanism_layer_enabled':False,
    'message':'技能描述推断层暂不启用（候选晋级未实现；有意保守的实际边界）',
    'zero_inference_meaning':'本轮未将候选晋级入页，不代表全库无hint',
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
                implementation_status=INFERENCE_STATUS)


def summary_text(summary):
    return '；'.join(f"{summary[k]['label']} {summary[k]['count']}/{summary[k]['denominator']}（{summary[k]['rate']:.1%}）"
                    for k in ('A','whole_row_confirmed','original_A','C'))
