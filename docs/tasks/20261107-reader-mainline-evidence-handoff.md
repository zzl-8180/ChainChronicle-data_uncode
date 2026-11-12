# Web 补证交给主线的接收提案

2026-11-07。单向研究交接；**尚未进入主线正式规则、答案或账本**。C19保持已收口，不因本文件自动启动新周期。主线可按有界任务自行接收、验证和选择正式消费者；不要让生产解析依赖 Web JS 或 audit 路径。

## 值得接收的事实

| 内容 | 证据入口 | 适用范围与不得外推之处 |
|---|---|---|
| HP/Chain条件 | reader_full_20261106/audit/player_conditions_20261107/native_conditions.* | HP先取整数百分比后闭区间比较；Chain计数映射0th/1st/2nd/3rd/Max。必要条件不等于完整选择 |
| 权重与完整分支选择 | audit/selection_order_20261107/native/ 与 audit/c19_closeout_20261107/condition_closeout_receipt.json | priority为权重，不是取最大；零总权重取首个符合项；必须保留charainfo全部真实父引用及顺序，不按名称过滤竞争者 |
| 使用次数/地形 | 同上及 audit/final5_evidence_20261107/sparse_receipt.json | 各控制器独立计数；仅当前同模式控制器生命周期，不保证跨波、复活或重建不重置；计数不等于成功命中或成功获珠 |
| 法珠与选档时点 | audit/selection_order_20261107/native/mana_timing_receipt.json | 普通UI预测选档后缓存ID，手动点击扣费后执行该ID；职业法珠范围按预测扣费后计数，废料按相应计数。自动无ID路径另论，不泛化为发动前固定门槛 |
| 稀疏字段装载 | audit/final5_evidence_20261107/native/sparse/、sparse_receipt.json | primary JSON逐记录new与缺键保留构造值；整记录缺失才回退AB，不逐字段合并。J/AB默认不可套给primary。12236原始hpend明确100，旧“缺上界”归因作废 |
| 结构关联推断 | scripts/skill_reader_preview/review_damage_structure.js；audit/remaining_evidence_20261107/ | 唯一伤害执行器、精确父引用及20332首次对敌范围等候选；自身受伤与后续type116另论。既有公式可复用，句面归属仍按推断审查 |
| 未解反例 | 最新condition_closeout_receipt的items/cohorts及final5/random_pool_receipt | 278普通池3项已证，动画→实际卡面未证；状态位消费不可按动画后缀命名。位置/形态、人数增长、重叠随机范围及效果歧义保留，不借选择证据越过绑定 |

所有相对 audit 路径均位于 output/character_skills/reader_full_20261106/。新条件回执含输入哈希、原760项完整身份、父记录、完整分支集合、准入/拒绝依据、枚举探针和反例。最新版评估 inventory 区分 numericKnown、bindingKnown、conditionKnown，不以颜色替代证据。

## 建议接收方式

1. 从原解码表及镜像独立核对所需事实，带上输入版本、调用路径与明确适用域；按当前正式数据重新判定，不直接导入 Web 的“金色”状态。
2. 文字绑定交由对应逐效果推断消费者；条件事实接到正式条件/来源结构。没有新数值公式证据时不为展示修改 rules.json。
3. 正式接收后输出来源可追踪的答案或条件元数据，Web再适配该新版本并撤销同一效果的重复补充，不把两套成果重复计数。
4. 布局、中文润色、颜色、额外等级合并与目录顺序由Web维护，不要求主线生成玩家页面格式。

完整逐项清单与本轮最终数量见 docs/tasks/20261107-reader-c19-closeout.md 及送审 manifest。本文件不表示已发送主持，不授予更新主线/启动新周期的指令。
