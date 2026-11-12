# C21交付包旧数量字样勘误

- 日期：2026-11-12。
- 性质：说明／检查名勘误；不改变正式答案、页面、账本、实际断言集合或独立终审裁决。严重度由第三方方向审查独立判断，主持不替其预写通过。

## 事实

C21正式范围是**518卡、900行、900效果、900答案**，不是C20的16卡18行。固定隔离集是525卡1050文件，即518张目标卡加7张保护／反例等相关卡。

独立终审R22按真实全库前像重算：card.json变化集合为518张目标卡与额外漂移卡30220的并集；其余8张预登记漂移卡本就在目标集内。正式答案、账本增量及900个新answer_ref均与这一范围一致。

## 保留的原始字样

下列交付材料残留从C20复制的“16卡／18行”等说明或检查名：

- `output/character_skills/c21_delivery_20261111/run_formal.py`：文件头、复制范围、final_diff、隔离说明和limitations中的相关文字。
- `output/character_skills/c21_delivery_20261111/validate_formal.py`：检查2.2名称“16目标卡”。
- `output/character_skills/c21_delivery_20261111/run_record.json`、`build_report.md`：limitations中的“16目标卡”。
- `output/character_skills/c21_delivery_20261111/checks/final_diff.json`：C1检查名“16张／18目标行”和隔离note“全部16目标卡”。
- `output/character_skills/c21_delivery_20261111/checks/validate_formal.json`：检查2.2名称“16目标卡”。

这些字符串与对应详情中的实际518／900集合不一致。原始正式脚本和回执不追溯改写，不用重跑检查来消除历史文字；当前成果页、清单、收口记录及本勘误按真实数量承接。

## 不影响的已验证内容

- 唯一一次jobs4全库生成及campaign `5492e173e3fa7c918eb3a2a701d6471e4a84246927e9450cf1cd99d3bc74e010`不变。
- 900项来源、raw、父集合、条件镜像、答案身份、账本消费、保护卡和隔离文件比较不变。
- 正式独立终审23/23、阻断0；审查入口路径修复见`output/character_skills/review/c21_delivery_final_20261111_deepseek/REPAIR.md`。
- 本勘误不授权再次全库生成、resume、清理、Git、发布或C22。
