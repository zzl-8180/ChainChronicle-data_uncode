# C8-P1 B1 effect_ledger 回退哈希整改记录

- 日期：2026-10-30。范围：仅交付证据与文档，不改正式页面、账本、规则或生产代码。
- 原审查：`output/character_skills/review/c8_p1_final_20261030_deepseek/REPORT.md`，verdict=REQUEST_CHANGES；18条答案、账本、no-op、verify_full 17/17、A7 29/29、隔离40文件均通过，唯一阻断为回退哈希写错。

## 独立复核

主持实际执行：

```bash
sha256sum scripts/character_skills/effect_ledger.py \
  work/c8_p1_final_20261030_deepseek/ledger_reverse/scripts/character_skills/effect_ledger.py
git apply --check -R -p0 output/character_skills/c8_p1_20261030/code_snapshot/effect_ledger.patch
```

结果：当前文件=`833c4d12864c17b691d39d7790b477931319bbe38d582403a41ad3e7b0a7a506`；反向副本=`b09bb928f62d2594dd9ca4f3060df8561940fe32ec9cbf4e14b087ac701c7190`；patch可干净反向。故本批前基线为`b09bb928…`，与C7-P1/P2/P3回执一致。`a40a1694…`只是C7-P1早态，遗漏其后改动，不是本批前基线。

## 集中修复

- 改正 `output/character_skills/c8_p1_20261030/run_record.json`、`code_snapshot/README.md`、`build_report.md`。
- 同步改正 `docs/tasks/20261030-c8-p1-throughput-package.md`。
- 同步生成器 `work/c8_p1_20261030/tools/build_final_run_record.py`、`build_c8p1_run_record.py`，避免重新生成时回退。
- `run_record.json`通过`python -m json.tool`；`work/c8_p1_20261030/tools/complete_delivery_manifest.py`重建并自验`SHA256SUMS.txt`，69/69、0失配。
- 未重新生成正式页面，未改`effect_ledger.py`、两个C8模块、rules、ledger或campaign。

定向复审：`dwfrun-2970c985-6d0d-4e04-988f-938533e50002`。原REQUEST_CHANGES报告保留；复审结果以`output/character_skills/review/c8_p1_final_20261030_deepseek/RECHECK.md`为准。
