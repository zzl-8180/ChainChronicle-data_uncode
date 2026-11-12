# 角色技能阅读页：C19 独审整改 R01

当前入口：`output/character_skills/reader_full_20261106/index.html`，本机预览 `http://127.0.0.1:8768/reader_full_20261106/`。基础数据为已验收 C19 `99bee2a1-cf9451c6ff47fcfb`；不是旧 C18 冻结版。此目录名称为兼容旧入口保留，不代表数据周期。

初审裁决为 REQUEST_CHANGES，原独立报告保持不变。本轮修复与内部复验以 `docs/tasks/20261107-reader-c19-r01-fix.md`、`audit/c19_r01_fix_20261107/` 为准；新复审材料状态为 PREPARED_NOT_REVIEWED，不代表第三方通过。历史 C19 接入证据仍在 `audit/c19_closeout_20261107/`。

R01 修复完整竞争父接线（394/394）、已解析条件接线（883/883）、回复与解除异常的局部片段标签（118处/106行/55卡）。没有增加答案、改原数值或升级本轮颜色。此前474项升金包含15个旧基础答案的显示评估变化，清单单列于 `production/n06_existing_base_display_promotions.json`，与407个新增答案、9卡16处指纹分开。

## 当前范围与口径

- 2,236 卡、41,665 条原描述、35,811 条源答案。C19 新增133行407答案全部句内，保留45个同句未解效果。
- 原35,404答案的数值、文字、条件与可信度保留；仅主线已审9卡16处 `page_sha256` 来源指纹更新。中文复用经过139张变化卡的完整旧卡哈希逆向重建，不取消版本检查。
- 2,222项补充评估目前1,936项金色推断、286项紫色。本轮原760紫全部筛查，474项升金；不是主线新增474答案，也不是实机确认。
- 剩余286项：效果对应200、条件及对应5、逐人增长70、位置或形态条件7、卡面对应2、回复数值与本效果对应2。7项仅条件缺口为20811×3、30204×2、8371×2。具体依据逐项在本轮 inventory 和 condition_closeout_receipt。
- 主线的已解/待解/完整度统计与Web补充核查分开；页面版本说明明确这一点。颜色变化不会擅自改主线账本。

## 使用与后续更新

可以随主线更新，但只接收完成且一致的快照。当前交付的是受控更新流程与只读预检，**没有后台轮询或无人值守自动迁移**。

```powershell
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/sync_status.py --check --audit-dir audit/c19_r01_fix_20261107
```

预检分别报告 baseStatus、webIntegrity、sidecarStatus；base same 不等于完整语义一致。候选层保留真实C18来源戳，R01旁注适配证明核对1774条追加、563承载行、396卡及2249个运行文件；缺件或哈希不符不能返回完整可用状态。没有后台自动同步。

新版本流程：预检 → 差异审定 → 独立目录重建 → 旁注逐项验证 → 数据/页面验收 → 切换目录。原句/对象/条件/来源改变时重新审查受影响部分；禁止删除哈希检查、改版本标签或将旧旁注直接套给新答案。新周期若没有明确迁移规则，先生成差异并保留旧页面，不盲目升级。

本次 C19 的精确迁移回执在 `audit/c19_closeout_20261107/semantic_migration.json`。可在项目根复现基础数据（指定新的输出目录）：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/build.py --output output/character_skills/reader_rebuild_check --semantic-migration output/character_skills/reader_full_20261106/audit/c19_closeout_20261107/semantic_migration.json --data-only
```

`--data-only`仅重建基础数据，不生成旁注、也不改历史审查。须保留或重新核验branch_candidates、branch_conditions、mana_costs及完整证据目录，再生成评估。不要把不含旁注的新目录当成完整交付。`migrate_c19.py`用于首次从已审C18生成回执，不能拿来批准未来任意周期。

对已齐备的独立读者目录重新核评估及前端：

```powershell
node scripts/skill_reader_preview/review_confidence.js --output <读者目录> --audit-dir audit/c19_closeout_20261107
& .\.venv\Scripts\python.exe -X utf8 -B scripts/skill_reader_preview/build.py --output <读者目录> --frontend-only
```

只改样式时用 `--frontend-only`，它不会同步主线或更新答案。R01切换先运行 `revalidate_sidecars.py`，完成全部验证及浏览器证据后用 `seal_reader.py` 封存全目录，再运行 `publish_reader.py`；三者指定 `--audit-dir audit/c19_r01_fix_20261107`。封存后不可再改stage，发布重新核对全目录哈希；成功切换后才写成功回执，失败回滚。R01前版本保留在 `reader_c19_before_r01_20261107`；更早C18备份亦不覆盖。完整命令见R01复审提示词。

## 展示约定

正文以技能描述和数值为主，说明/原文/来源折叠。绿色已确认、金色推断、紫色仍有条件或对应疑问、灰色对应待核、淡红未解；蓝色是原文明示等级数值。颜色统一图例，不逐值重复“推断/候选”。

- 已有且可定位数值必须进入对应句面；无法定位的保留展开入口及具体缺口，不写成未发现参数。
- 连携/地形强化句跟随原文顺序，作用范围链接到前面效果。条件、数值语义、效果绑定分别核验；`×C`只用于原答案本来包含的Chain乘项。
- 分支按真实层/父ID和已证条件排序，不按数组号或数值大小命名。随机池须标“随机选档”；概率仅为预测调用区间，不当实战施放频率。未被本模式常规选择的记录不称可切换档，也不凭零权重断言历史废弃。
- 额外能力同名相邻等级且中日文本仅数字变化时合并；条件/对象改变则分段。数列紧凑，和正文两侧等距；全部等级来源保留。
- 同文角色资料只和唯一匹配分支合并，不能叫共鸣/超共鸣共用描述。技能目录“必杀技→传授”。
- 反向遍历所有已解析父和selectionResolved答案，不能只从已生成的branchTable自检。完全相同执行槽的竞争父可复用已绑定值，必须保留各自真实条件和来源；不能凭数值相同、名称或pattern号合并。
- 回复标签按effect span/snippet所在的“回復”判断HP回复还是异常恢复，禁止因为整句同时含两者而批量改名。传授采用与必杀一致的条件顺序，只去重数值、颜色、条件都相同的项；596卡跨组同文保留两个记录类型并提示同文。
- 法珠小圆点表示配置消耗，0珠明示；不重复扣原文条件减少的消耗，不猜职业珠色。
- 全卡按游戏控件640×960显示2:3，头像1:1；512×512存储纹理不是游戏显示比例。

CID350的25/27.5和20332首次对敌系数现为金色静态推断；不是最终扣血。278仍缺动画→具体卡面的真实引用，5300限次以当前控制器生命周期解释。12236的hpend本来就是100，旧“缺上界”归因不得继续引用。

## 证据、验证与主线边界

正式主线 pages/profiles/effect_ledger 始终只读。Web将结构绑定/选择条件等证据单向交给主持决定是否正式接收；不让主线依赖Web脚本。见 `docs/tasks/20261107-reader-mainline-evidence-handoff.md`。

本轮验收：`verify_full.py --output ...`、`verify_c19.py --output ... --baseline ...`、`verify_confidence.js <目录> audit/c19_closeout_20261107/confidence_validation.json`、`verify_condition_closeout.py --output ...`。验证写回执时指定本轮/独立目录，不覆盖历史独审。浏览器测试与程序检查分别记录。

新复审入口：`docs/tasks/20261107-reader-c19-r01-recheck-prompt.md`；准备材料在 `output/character_skills/review/reader_c19_r01_prepared_20261107/`。初审及冻结输入不覆盖，本轮没有启动第三方复审或发送主线消息。

本机依赖含Python/Node、正式主线与原解码表、审定中文/reference_pairs、共享图片 `../pages/art/`、既有镜像/metadata及原生摘录。本次不是干净机器完整解包发行包。保留图片目录关系可离线浏览。

## 历史定位

旧各轮统计只反映当时版本。原README保存在本轮audit/previous_readme.md，不再用其中的“当前”数字作为现状。

- 句内/等级/去重：`docs/tasks/20261107-reader-release.md`。
- 中文全库审定：`docs/tasks/20261107-reader-semantic-review.md`。
- 原记录分母与无正文分支：`docs/tasks/20261107-reader-branch-candidates.md`。
- 绑定补证：`docs/tasks/20261107-reader-remaining-evidence.md`。
- 选择与时点：`docs/tasks/20261107-reader-selection-order-audit.md`。
- 最后五条及旧归因纠正：`docs/tasks/20261107-reader-final5-evidence.md`。
- 卡面比例和25/27.5复发经验：`docs/tasks/20261106-character-skills-reader-prototype.md`“接手必读”。
