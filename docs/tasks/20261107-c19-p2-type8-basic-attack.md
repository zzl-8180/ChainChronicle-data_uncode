# C19-P2 APK type8基础攻击任务卡

- 创建：2026-11-07；实施：`new-provider/deepseek-v4-1-flash-261017` high；独审：`new-provider/deepseek-v4-pro-ga-260813` high。
- 状态：**3项APK type8已交付；原第三方R01定向复核通过，R01 CLOSED，阻断0；C19清理已完成，Git提交／推送进行中，不启动C20或发布**。正式独立终审PASS_WITH_EXPLICIT_SCOPE_LIMITS、阻塞0、47/47（28项独立重算＋19项只读引用）；成果页详细验证21/21、坏链接0。
- 只允许写入`card_page_inference_c19_p2_type8_basic_attack.py`、`output/character_skills/c19_type8_basic_attack_20261107/`与`work/c19_type8_basic_attack_20261107/`；共享card_page_data由主持在独审通过后处理。

## 精确范围

| cid／effect | 局部预筛值 | 来源与句间分工 | 必须排除 |
|---|---|---|---|
| 1063 `1063-ability-ability-skillid_1_-lvorder0-f1#e00` | ×1.35／提高35% | APK父424 `/skilllist/272`自身type8；基础句局部贡献 | 三个type67条件记录及全部后文，不把旧B4整行hint改成晋级 |
| 1238 `1238-ability-ability-skillid_2_-lvorder1-f0#e00` | ×1.75／提高75% | 首句Always子记录30123804 `/skilllist/4083`；WAVE父type4、HighHP、WaveUp2、WaveSupport各有分工 | 不向WAVE句复制，不合并HP条件或其他字段 |
| 12220 `12220-ability-ability-skillid_1_-lvorder0-f0#e00` | ×1.1／提高10% | 第一段Always子记录31222001 `/skilllist/8227` | 第二段type96择槽未决、第三段97、第四段1019均不并入 |

## 验收门

1. APK原层`charainfo→父skilllist→适用type8记录`独立重导；不得从CACHE借值或只按同文匹配。
2. 使用整句／fragment／source span消歧，保留旧B3/B4/B11拒绝原因；新的逐效果局部作用域不等于全局放宽旧模板。技能末尾连携／地形强化句保留完整上下文，条件在技能级可见位置展示且数值可回指，不把pattern序号当游戏档位或把一个增幅套给全部效果。
3. `rules.answer_for('skilllist',8,'/param1',raw,record,source_layer='APK')`与真实`effect_ledger.analyze_row`消费；第二次新增0，未消费0，scope硬拒绝。
4. 默认中文可读、raw／单位／对象／条件／来源／证据档齐全；numeric=确认仅规则与原值，association=推断，runtime=false。
5. 候选独立审查无阻断后才允许主持接线；任何一项归属不成立，单独移除，不影响其他成熟候选。
