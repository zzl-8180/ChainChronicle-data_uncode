# C20-P1：Y.G. pattern 行直接伤害

- 状态：**P1已完成**：9卡10行10效果10答案；真实Inputs/analyze_row检查22/22、Pro候选独审、恢复复核、正式终审及方向复核通过。
- 写域：`scripts/character_skills/card_page_inference_c20_direct_damage_common.py`、`card_page_inference_c20_p1_yg_direct_damage.py`、`output/character_skills/c20_p1_yg_direct_damage_20261108/`、本卡。
- scope：`C20_P1_YG_DIRECT_DAMAGE_20261108`；缺省、错误或空scope必须硬拒绝。

## 冻结范围

7250 pattern0 f1/f2；30105 pattern0 f2；30107 pattern0 f3；30220 pattern0 f1；30223 pattern0 f3；30225 pattern0 f1；30301 pattern0 f1；30329 pattern0 f1；30334 pattern0 f2。共9卡10行10个 `#e00` 伤害效果，最多10答案。

C14-P2已答的是同卡 `skilltext` 镜像行，本批是独立 `patternN` 来源行。只复用既有规则体与已审解析方法，逐行重新验证当前source，不复制旧答案对象。

## 逐行门

1. 当前row为special_move、reference_field与冻结一致；skill.table=bosspattern、record_id为正整数、layer=CACHE。
2. 同层charainfo[cid]唯一，实际patternN引用等于skill.record_id；row.source指向真实bosspattern下标及`/sinfo`。
3. context_text、skill.original_text与pattern.sinfo一致；行片段在父文有唯一字符span。多段句的N回与唯一type105/110且skillparam6=N匹配；大伤害与单发载体唯一。
4. 只用既有 `bossskill|3|22|55|74|105|110` 伤害规则及 `g1_b1_binding` 消费口；原值从选中bossskill字段重读，有限正数，保留raw与float32。
5. 已有非同规则答案原样保留；同规则已有答案只允许本批完全相同的幂等跳过，冲突则整行不追加。
6. 其它pattern、denju、句尾Chain强化、回复、状态与弹射不并入；未解效果继续可见。

候选目录须包含candidates、exclusions、check_result、run_record、README和真实Inputs/analyze_row检查脚本。独审有阻断时不接线。

## 当前实施回执

- 候选已实现并冻结：10行10答案，真实Inputs/analyze_row检查22/22通过，第二次新增0、未消费0、split_flags不新增。
- 首轮20/22为检查口径问题，失败件保留 `check_result_attempt1.json`；修正后22/22，不把失败历史改写成首轮通过。
- 当前会话未加载既定DeepSeek实施类型，确定性实现由主持完成并如实登记；R01定向复核B1 CLOSED、阻断0，README N1已同步。DeepSeek Pro GA正式候选审查提示词见 `20261108-c20-candidate-review-prompt.md`。后续已完成最小接线、经授权的一次纠正性全库构建、正式终审和方向复核；本批停止写入，不启动C21。
