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
    'template_inference_b10_sa2003_enabled':True,
    'template_inference_b10_sa2003_scope':'SA_PowerDrain（ability2003）载体解析——批 9 C1 遗留 '
                                         '431 行闭合：bosspattern/denju/dlb/charainfo 行 own '
                                         'children→boss_skill.s_ability→skilllist ability2003 '
                                         '载体；rules.py 2003 注册处新登记五键 '
                                         'skilllist|2003|/param0|/param3|/param7|/param8|'
                                         '/param9（样本域＝当前 v3 CACHE 普通 ability2003 全部 '
                                         '265 条，occurrences 265/265/265/258/263）；'
                                         '（b10_sa2003_scope.md 批 10：431 行逐行门控——晋级 239、'
                                         'APK 148 域外载体 hint 192、multi-carrier 6；触发仅 '
                                         'Skill 型着弹、与 99 三路不同逐行披露）；只升「推断」档，'
                                         'P1 句面/P3 唯一/P2 样本域/P4 形状双向/P5 方向/P6 跨 cid '
                                         '守卫＋B1 防线（sub_effect 伪影不消费；s_ability 链含 99 '
                                         '归批 9）逐行审核；param9 用受伤量口径（不是固定防御'
                                         '减少）；param4/5/6 自身侧未登记换算不分配；'
                                         '不跨记录合并数值，归属为数据侧结构对应（引擎侧行→'
                                         '载体装载路径无原生核实）',
    'template_inference_b11_sa1095_enabled':True,
    'template_inference_b11_sa1095_scope':'普通自身增益 1095 链——普通 skilllist 父记录（1110 '
                                         'UniverseMana/26 ManaGet/1089 PirikaExtend 等）sub[]→'
                                         'skilllist ability1095（Always3）载体解析：值行只消费 '
                                         'skilllist|1095|/param1（攻击倍率）/param3（受伤量倍率'
                                         '＝防御上升口径，不是固定防御量）——两键 occurrences=407 '
                                         '存在数口径全域已确认；p2/p5/p6 规则已核 ID 仅 '
                                         '65000001/43023601（occurrences 1/1/2 已核 ID 数口径），'
                                         'tier B 94 行按 scope §5.3 保守案整行留 hint '
                                         'slot-rule-not-in-domain、不出部分值行；'
                                         '（b11_sa1095_scope.md 批 11：候选池 1,070 行（Y.G. 388）'
                                         '逐行门控——tier A 晋级 34（全 p1）、tier B hint 94、'
                                         'shape-mismatch 58、conditional 92、mixed 69、enemy-'
                                         'debuff 56、non-base 10、APK 域外 27；multi-1095-sub '
                                         '与方向冲突结构性为 0）；只升「推断」档，P1 基础句正则/'
                                         'P2 样本域/P3 唯一/P4 形状双向/P5 方向/P6 对象'
                                         '（rules target 装有者自身，句面省略主语逐行披露）/'
                                         'G1′ 句唯一逐行审核；父 ability==1095 相邻集 370 行与'
                                         '批 5 65000001 链不入本批（65000001 不被任何 '
                                         'skilllist.sub 引用）；不跨记录合并数值，归属为数据侧'
                                         '结构对应（引擎侧 sub[] 装载路径无原生核实）',
    'template_inference_b12_1095ext_enabled':True,
    'template_inference_b12_1095ext_scope':'ability1095 扩域（批 12，两步）——第一步（案 A）'
                                         '扩 rules.json 三键：p2/p5/p6 occurrences 由「已核 '
                                         'ID 数」（1/1/2：65000001；p6 加 43023601）改为'
                                         '「当前 v3 CACHE ability=1095 全部根记录字段存在数」'
                                         '（407/211/407，与 p1/p3 同域同义；受控检查 9 项边界'
                                         '记录×资格真假＋p2 407/p5 211/p6 407 全域公式核对，'
                                         'output/ordinary_effects/ability1095/native_checks.'
                                         'json 顶层 b12_extension；无新反汇编、未实机）；'
                                         '第二步 tier B 94 行整行晋级（批 11 保守案 hint '
                                         'slot-rule-not-in-domain 的行级替换）：门与批 11 '
                                         '完全同门（基础句正则/CACHE 407 域/唯一/形状双向/'
                                         '方向/对象=rules target 装有者自身/G1′ 句唯一），'
                                         '值行 rule_key 允许 skilllist|1095|/param1|param2|'
                                         'param3|param5|param6 五键（p2 移动乘数×原值；'
                                         'p5 暴击概率直接加算 pp 不套减 1.5；p6 暴伤 '
                                         'delta=p6−1.5 pp；p1/p3 口径不变）；p5/p6 中性'
                                         '（p6=1.5）如实不写值；行级键 inference_b12、'
                                         'evidence_scope=TEMPLATE_BATCH12_1095EXT；'
                                         '批 11 tier A 34 行零触碰（仍 inference_b11）、'
                                         'APK 52 域外 carrier-out-of-domain 27 行与各失败'
                                         '桶 hint 口径零变化；不跨记录合并数值，归属为数据侧'
                                         '结构对应（引擎侧 sub[] 装载路径无原生核实）',
    'template_inference_b13_apkext_enabled':True,
    'template_inference_b13_apkext_scope':'APK 域外扩域（批 13）——rules.json skilllist|99 四键＋'
                                         'skilllist|2003 五键样本域由「仅当前 v3 CACHE」扩为'
                                         '「CACHE＋APK 主表两域分源」（单键保留、新增伴生字段 '
                                         'occurrences_apk＝APK 存在数 196/157/82/162 与 '
                                         '148/148/114/75/140；occurrences 的 CACHE 口径不变；'
                                         '不拆双键；两域 5＋5 个同号记录中 7 组为真实参数值分歧、'
                                         '3 组仅缺省/float32 表示差（逐组明细见 rules.json 九键 '
                                         'conditions；批13修复轮 R02 措辞精确化）、命名空间不'
                                         '合并、行侧载体按载体所在层取值不得跨层；最小新增证据＝'
                                         '99 处理器 31020502 全路＋31221605 分数阈值 2 条 APK '
                                         '记录受控检查＋99×199×3 路、2003×148×Skill 路全域公式'
                                         '核对 0 失败，work/character_skills_b13_impl_apkext/，'
                                         '无新反汇编、未实机）；批 9 APK 域外 94 行（86 晋级＋8 '
                                         'multi-carrier 留 hint）与批 10 APK 域外 192 行（全'
                                         '晋级；跨层 63 行按载体层域归类）在 B9/B10 载体域门处'
                                         '委托 B13 逐行审核（P4 形状双向/P5 方向/P4b 竞争句/P6 '
                                         '守卫同批 9/10 门）；披露区分「规则本体已确认（样本域'
                                         '扩至 CACHE+APK）」与「本条归属推断」；行级键 '
                                         'inference_b13、evidence_scope=TEMPLATE_BATCH13_APKEXT、'
                                         'replaces_hint 溯源不双登记；只升「推断」档，不跨记录'
                                         '合并数值，归属为数据侧结构对应（引擎侧行→载体装载路径'
                                         '无原生核实）',
    'template_inference_b14_apkext_enabled':True,
    'template_inference_b14_apkext_scope':'APK 域外扩域第二批（批 14）——rules.json skilllist|2012 '
                                         '三键（/param0 /param4 /param5）＋skilllist|1095 五键'
                                         '（/param1 /param2 /param3 /param5 /param6）样本域由'
                                         '「仅当前 v3 CACHE」扩为「CACHE＋APK 主表两域分源」'
                                         '（单键保留、新增伴生字段 occurrences_apk＝APK 存在数 '
                                         '211/132/131 与 52/52/52/37/52；中性口径：存储 0.0＝'
                                         '中性不计、p2/p3=1.0 与 p6=1.5 中性同 CACHE 口径'
                                         '计入；occurrences 的 CACHE 口径不变；不拆双键；两域'
                                         '同号 15＋4 条记录参数值不同——分源不合并、行侧载体按'
                                         '载体所在层取值不得跨层读取、本批 113 载体与 CACHE 同号'
                                         ' 0 交集）；最小新增证据＝CheckJobFlag 非零分支体片段 '
                                         '0x13ab388–0x13ab458（升级项经主持授权，自既有恢复的'
                                         '原生镜像提取）＋2012×211×3 键、1095×52×5 键全域公式'
                                         '核对 0 违例＋边界/职业过滤受控检查（ability2012 证据落 '
                                         'output/ordinary_effects/ability2012/ b14_extension，'
                                         '1095 侧落 work/character_skills_b14_impl/；未实机）；'
                                         '批 8 APK 域外 196 行（195 晋级＋1 G6 句无对象词留守）'
                                         '与批 11/12 APK 域外 27 行（17 晋级＋10 P4 形状不符'
                                         '留守）在 B8 G5 域门/B11 P2 域门处委托 B14 按载体层域'
                                         '接管：行级键 inference_b14、evidence_scope='
                                         'TEMPLATE_BATCH14_APKEXT、replaces_hint 溯源不双登记；'
                                         'iParam0≠0 的 8 载体 27 行 condition_label 条件分组'
                                         '披露（句面职业位==解码位逐行断言，不并入基础值）；'
                                         '批 6 让渡注记 166 行随晋级行级替换（不残留 hint 键）；'
                                         '只升「推断」档，不跨记录合并数值，归属为数据侧结构对应'
                                         '（引擎侧行→载体装载路径无原生核实）',
    'template_inference_b15_union_enabled':True,
    'template_inference_b15_union_scope':'t13 槽∪2012 暴击链并集归属（批 15，20261023——批 6×批 8/14 '
                                        '跨批衔接断点修复；GOAL_ALIGNMENT.md G01、整改任务书 §三.3）：'
                                        '批 8/14 已出 crit 值行的行上，批 6 G4「句含クリティカル→整行 '
                                        'hint」一刀切在并集归属成立时解除——非 crit 属性/时长主张由'
                                        '同链 t13 载体活性槽（skillparam1/2/3/6，批 6 已确认规则、'
                                        'rules.json 现行 conversion）按属性分别归属出值，crit 值行'
                                        '维持批 8/14 既有答案零触碰；门 U1 crit 覆盖核对/U2 链一致'
                                        '（批 6 t13==批 8/14 中继）＋charainfo G5 同法/U3 并集形状'
                                        '双向（B6._gate_parent has_crit=False 承接残余门：G7 同文/'
                                        'fam 竞争/G6 竞争句）/U4 方向（非 crit 与时长槽原值>0）/'
                                        'U5 非 FAM1 句父记录无 fam 竞争；任一不过→inference_b15_hint '
                                        '登记具体缺口；行级键 inference_b15 行级替换 inference_b6_hint'
                                        '（让渡注记先例，不双登记），批 8/14 链 provenance 记入本键 '
                                        'crit_chain 子对象；每答案各注来源载体与层，不合并不乘积；'
                                        'D1 裁决口径：时长值行归 t13 /skillparam3，不消费 2012 param0；'
                                        '只升「推断」档，不跨记录合并数值',
    'template_inference_b17_p0finale_enabled':True,
    'template_inference_b17_p0finale_scope':'P0 断点收尾（批 17，20261023——批 16 审计三族规则'
                                        '改动一次落地）：①H1/P2 槽位分区——批 6 G6/批 15 U5 从'
                                        '「存在竞争句即 hint」升级：竞争句（FAM11/FAM13 家族句＋'
                                        'G6 扩展 ally-buff 短语）属性主张按 ATTR_PARAM 词表映射后'
                                        '与 t13 非 crit 活性槽不相交、且 t13 全字段复核无已分配槽外'
                                        '非零槽时，竞争句结构上不能持有该 t13 任何槽→本行获 t13 全'
                                        '活性槽＋/skillparam3 时长值行；竞争句「一定時間」随其自身'
                                        '载体走（逐字论证披露在行注记）；②H2 时长槽共享（主持 D1 '
                                        '级裁决 2026-10-23 方案①）：条件暴击行継続時間值行引同一 '
                                        't13 /skillparam3（「も」＝同 buff 追加语义；硬前提逐行复验：'
                                        '兄弟 FAM1 行已由批 6 以同一 t13 晋级＋2012 载体 param0 与 '
                                        't13 p3 原值一致，不一致留 hint 披露两值；槽共享／各注来源/'
                                        '不合并不乘积）；③多 t13 denju patternid 映射：patternidN→'
                                        'bosspattern sinfo 唯一命中→boss_skill_refs reference_field '
                                        '归属登记→唯一 t13（charainfo 行同法可解性未测不做）；'
                                        'P2 溢出（b6 hint fam 冲突 45＋同属性竞争句 30 行）同法逐行'
                                        '复验、不适用者留 hint；行级键 inference_b17 行级替换既有'
                                        '唯一 hint 键（不双登记），批 8/14 crit 值行零触碰、链 '
                                        'provenance 记入本键 crit_chain；只升「推断」档，不跨记录'
                                        '合并数值',
    'message':'候选晋级及一般机制择句仍未实现；模板作用域推断层已启用十七批（type1017 试点＋批 3 type8 '
              '严格子集＋批 4 条件扩展双记录映射＋批 5 跨表扩展＋批 6 必殺バフ bossskill 子记录解析＋'
              '批 7 共鳴 ability3000 载体解析＋批 8 暴击 2012 链载体解析＋批 9 敵デバフ ability99 载体'
              '解析＋批 10 SA_PowerDrain ability2003 载体解析＋批 11 普通自身增益 skilllist 父 '
              'sub[]→ability1095 Always3 载体解析＋批 12 ability1095 扩域（rules.json 三键 '
              'p2/p5/p6 occurrences 407/211/407 存在数口径后，批 11 tier B 94 行整行晋级）＋'
              '批 13 APK 扩域（rules.json 99 四键＋2003 五键两域分源＋occurrences_apk 后，'
              '批 9/10 APK 域外 286 行按载体层域晋级 278、multi-carrier 8 行留 hint）＋'
              '批 14 APK 扩域第二批（rules.json 2012 三键＋1095 五键两域分源＋occurrences_apk '
              '后，批 8 APK 域外 196 行与批 11/12 APK 域外 27 行按载体层域晋级 212、'
              'G6/P4 实际门 11 行留 hint、iParam0 职业过滤 27 行条件分组披露）），'
              '仅「推断」档，行级标注「推断（模板试点 type1017）」或「推断（模板批 3 type8）」或'
              '「推断（模板批 4 条件扩展）」或「推断（模板批 5 跨表 type1017）」或「推断（模板批 6 必殺バフ）」或'
              '「推断（模板批 7 共鳴）」或「推断（模板批 8 暴击 2012 链）」或「推断（模板批 9 敵デバフ）」或'
              '「推断（模板批 10 SA2003）」或「推断（模板批 11 自身增益 1095）」或「推断（模板批 12 1095 扩域）」或'
              '「推断（模板批 13 APK 扩域）」或「推断（模板批 14 APK 扩域）」或'
              '「推断（模板批 15 并集归属：t13 槽∪2012 暴击链）」或'
              '「推断（模板批 17 P0 收尾：槽位分区/时长槽共享/denju patternid 映射）」，'
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
