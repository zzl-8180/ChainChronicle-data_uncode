# 角色技能选题与验收源码入口

2026-10-24 Git同步：将原来仅存在于被忽略work/output目录的5个必要脚本纳入源码仓库。原位置保留，不覆盖历史版本、产物或运行回执。三个选题脚本及README生成器初次按字节复制；A7只增加可指定报告路径的入口，29例语义不变。

在仓库根运行 `.venv/Scripts/python.exe -X utf8 -B scripts/character_skills_pipeline/<script>.py`。顺序为 `build_inventory.py → enrich_records.py → assign_candidates.py`；输出仍为 `work/character_skills_yg_priority/`，F03回执需引用实际运行的新路径。`regen_readme28.py`按正式metrics与campaign刷新pages/README §28。A7可用 `a7_regression.py --out <独立报告路径>`；默认仍写output/character_skills/effect_ledger/acceptance/a7_regression_results.json，覆盖前保留旧结果及版本。

依赖见方案§7.1：正式pages、profiles/records/rules/characters、effect_ledger及由前步生成的视图；build_inventory另读不可重建的coverage_refined.json冻结研究输入。原始游戏表、原生证据、规则数据和研究输入不因源码入库而自动随仓库分发。它们必须由声明的输入生成、由用户提供或随结构化成果包提供。本目录不是独立可复现发行已完成的声明。

历史来源：work/character_skills_yg_priority/三脚本、work/character_skills_goal_rectification/regen_readme28.py、output/character_skills/effect_ledger/acceptance/a7_regression.py。后续维护优先使用本受控入口，不并行维护两套实现；旧入口只用于按对应旧回执重放，不静默追改历史哈希。
