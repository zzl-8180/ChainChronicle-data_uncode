# 项目状态

更新：2026-10-17（最终确认与审查基准）。接手入口：[HANDOFF.md](HANDOFF.md)；交付包：[output/share_bundle/20261016-delivery/README.md](output/share_bundle/20261016-delivery/README.md)。

## 当前交付：最终确认与审查基准（2026-10-17）

- **仓库确认**：124 个跟踪文件（107 脚本＋README/docs/规范/依赖锁/参考 ZIP）；全部解包管线与修复入库；第三方导入（unicorn/capstone/pyelftools/UnityPy/pillow/lz4/pyaxmlparser/asn1crypto）全部被 requirements-lock.txt 覆盖；无游戏资源、大产物、凭据入库（模式扫描为空）；winreg 仅见于 emulator_probe.py（研究探针，非解包链）；工作树干净。
- **版本绑定**：被测目录 `work/delivery_20261016/final/`（git archive ff664a7）与最终 HEAD 的全部脚本、README.md、requirements-lock.txt、.gitignore 经 `git diff` 确认完全相同（差异仅 HANDOFF/STATUS/审计文档与打包脚本新增），交付测试结论适用于最终版本。
- **错误输入处理（本轮补测，全在隔离目录）**：破坏 data5（位翻转）→ 该文件 FAILED_RETAINED（"Native envelope digest-size constant or payload boundary invalid"），其余文件正常，报告 PARTIAL_FAILURES_RETAINED；空输入目录 → ValueError("No data5 input")；libcompatible.so 改动 1 字节 → 版本断言拒绝（"Pinned build only"，已恢复原件 79b6ae19…）；缺恢复镜像 → FileNotFoundError 并给出缺失路径。
- **A/B/C 包核验**：A 1.4MB/129 项（git archive 最终 HEAD）；B 149.7MB/3366 项；C media_manifest.json（56 类统计＋重建命令＋分包方案＋版权边界，不复制 20GB）；zip 条目对账＋CRC 自检全过；B 包内 base_master 全量组件 JSON 与四个分表 JSON 存在同数据两种访问形式（项目既有产物结构，压缩后增量小，已在清单注明，不重构）。
- **审查基准**：以当前最新提交为冻结版本（哈希见本轮交付报告与 git log）；若审查期间修改交付版本，须重记提交哈希与受影响文件。
- **待推送差异**：origin/main..HEAD 共 4 个提交（8b91293、ff664a7、e2cc987、ac76029＋本确认提交），未推送；外部发布动作（push、Release 上传）待用户授权。
- **未验证（如实保留）**：全新机器从零安装 .venv、非 Windows 平台、bdl 全量 68655 在独立目录重跑（项目内既有 100% 验证，不重复）；verify_cache_snapshot/refresh 本快照专用；analyze/export_master 研究线。

更新：2026-10-16（第三阶段交付准备）。接手入口：[HANDOFF.md](HANDOFF.md)；交付包：[output/share_bundle/20261016-delivery/README.md](output/share_bundle/20261016-delivery/README.md)。

## 当前交付：源码仓库补齐＋交付版本验证＋分层成果包（2026-10-16）

- **Git 提交（未推送）**：`8b91293` 26 文件（根 README.md、docs/ 全部、full_unpack 五脚本、build_char_roster、scripts/release 两脚本、9 个修复脚本、AGENTS/HANDOFF/STATUS）；`ff664a7` full_unpack merge/finalize 容忍第三方最小清单（archive 等来源字段可选、finalize 加 --inventory）；`e2cc987` 分层交付打包脚本。提交前确认并行打包任务无新改动，未覆盖他人文件；工作树干净，无 output/work/raw 入库。
- **交付版本验证（任务二）**：`work/delivery_20261016/final/`＝`git archive ff664a7`＋APK＋4 样本 data5，全链实测：A1 apk_baseline 44 文件→A2 重定位 2855→A3 镜像 SHA256＝3fd354b5…钉住值；B1 decode_data5 2 文件、B2 四文件（charainfo/skilllist 偏移 6、bossinfo/helper 偏移 0 变体）16719 记录全部原生解码；**全部与既有参考逐字节一致**。bdl：2 样本 run→merge→verify→finalize，objects_index.json 与项目 full_unpack 逐字节一致。**chronicle**：A4 native_debug＋D1 decode_chronicle，ChronicleArchiveData.json/.bin 及四表与 output/base_master 逐字节一致（7800 角色/21008 技能唯一 ID）。
- **真实验证状态**：data5【已验证·独立目录·两包装格式】；BDL【已验证·独立目录小样本；全量 68655 为项目内既有验证】；chronicle【已验证·独立目录】。未验证：全新机器从零安装、非 Windows 平台。
- **分层交付包（任务三）**：`output/share_bundle/20261016-delivery/`——A 工具包 1.4MB/129 项（git archive e2cc987）；B 研究成果包 149.7MB/3366 项（v3 全部、base_master、card_comparison、ordinary_effects、boss_chain/boss_heal、sample、phase_d、validation、双审查报告、card_images、char_roster、structured、两个 latest 指针）；C `media_manifest.json`（20.24GiB/903402 文件逐类统计＋重建命令＋分包方案，**不复制媒体**）；统一 README＋package_manifest.json（git HEAD、SHA-256、排除项、用法、版权边界）；zip 条目对账＋CRC 自检全过。有意排除：export 旧构建（被 v3+base_master 覆盖）、field_guide 旧快照字典、可重建中间产物、历史版本。
- **README**：根 README.md 完成（版本硬边界、环境、安装、data5/bdl/chronicle 命令、采集、结果查看、已知限制、仓库结构）。
- **待授权**：git push origin main；GitHub Release 上传 A/B 包（及如需 C 媒体分包，先确认音频与版权范围）；均属外部发布动作，未执行。
- **不影响交付的限制**：verify_cache_snapshot/refresh 为本快照专用；analyze/export_master 研究线依赖历史证据；bdl 全量独立重跑未做（无必要重复）；pwsh 已切 7.6.6。

更新：2026-10-16（审查整改）。接手入口：[HANDOFF.md](HANDOFF.md)；审计与整改全文：[docs/tasks/20261016-reproducibility-audit.md](docs/tasks/20261016-reproducibility-audit.md)；独立审查报告：[output/20261016-reproducibility-audit/review/review_20261016_independent/README.md](output/20261016-reproducibility-audit/review/review_20261016_independent/README.md)。

## 当前交付：可复现性审查整改（2026-10-16）

- **整改依据**：独立审查结论「带明确限制通过、无 P0」；2 项 P1（修复未提交、F3 隔离证据只覆盖 1/3 脚本）与 4 项 P2（--prior-report 不彻底、77 重放口径、同类缺 mkdir、--cert-hex 未实测）。
- **P2-1**：`decode_cache_snapshot.py` 复用分支改从 `json_file`／--prior-report 所在目录解析（原第 87 行硬编码 `output/decoded`）；默认路径行为不变。三模式复验 PASS：项目侧 77 文件重放 39047 记录归一化后 0 差异、隔离旧报告缺失、隔离自定义报告目录（隐藏 output/decoded 仍正确解析）。
- **P2-2**：77 重放口径写入审计文档（全部 REUSE_THIS_SNAPSHOT_VERIFIED_DECODE，比较对象 records.jsonl，归一化仅 snapshot_id，非 77 次原生解码）；原生解码抽样补 bossinfo（偏移 6）＋helper（偏移 0 变体），与 v3 逐字节一致。
- **P1-2**：jni_prefix_probe／metadata_decode_probe 修复版隔离各跑一次，产物（compatible_jni_prefix/conversion.bin、metadata_aei_decoded.bin）与项目既有文件 SHA256 逐字节一致；F3 三脚本至此全部有隔离实测。
- **P2-3**：protection_sample.py、callback_sample.py、callback_key_candidates.py 入口补 output/protection mkdir；隔离冒烟 PASS（PASS_PROTECTION_SAMPLE／PASS_OFFLINE_BLOCK_MODEL／distinct_keys=1, occurrences=43）。
- **P2-4**：`full_unpack_run.py --cert-hex` 端到端实测通过——2 个 bdl 迷你清单、运行期隐藏 APK，2/2 ok；objects_index.json 与项目 full_unpack 同名包逐字节一致，decoded_sha256 与 ledger 一致。
- **P1-1**：待提交清单已列（full_unpack_*.py、build_char_roster、scripts/release/ 两脚本、docs/、AGENTS.md、9 个修复脚本），**等用户授权后显式提交，一律不推送**。
- **本轮修改**：scripts/decode_cache_snapshot.py、protection_sample.py、callback_sample.py、callback_key_candidates.py 及审计文档、HANDOFF/STATUS；复验全写独立临时目录，未覆盖正式输出；未提交 git、未推送。
- **下一步**：用户授权后按清单提交（git 补缺）；根 README.md；chronicle（A4+D1）隔离补测；发布清单草案。

更新：2026-10-16（可复现性审计与规范）。接手入口：[HANDOFF.md](HANDOFF.md)；审计全文：[docs/tasks/20261016-reproducibility-audit.md](docs/tasks/20261016-reproducibility-audit.md)。

## 当前交付：可复现性审计与 GitHub 交付规范（2026-10-16）

- **可复现性结论**：data5 解包链第三方可独立复现——git HEAD 原始状态在 APK 原生库提取（apk_baseline 未提取 libcompatible.so）、旧解码报告硬依赖（decode_cache_snapshot 必读 output/decoded/report.json）、`work/protection` 建目录（signal_region_probe 等三脚本）三处必败；本轮均最小修复并在仅含仓库文件＋APK＋2 样本 data5 的隔离目录实测通过。恢复镜像 SHA256＝钉住值＝既有文件；charainfo/skilllist 解码字节一致；77 文件重放与 v3 规范化后 0 差异；bdl 管线脚本已参数化但未入 git（下一阶段最高优先）；export_master／analyze／verify_cache_snapshot 属研究线或本快照专用，第三方不适用已标注。
- **版本边界**：仅支持 com.sega.chainchronicle 5.6.2/56021；库、镜像、密钥派生均以哈希钉住，不匹配明确报错。
- **规范调整**：AGENTS.md §7 新增 GitHub 存储策略（≤1GB、遵守单文件限制、继续忽略 raw/work/output/.venv/tools、严禁全目录强制提交、Git LFS 非默认）；§8 重构为 8.1 独立可复现性、8.2 分层发布 A—C、8.3 工具可移植性、8.4 发布清单与发布前隔离验证。
- **实际修改**：scripts/apk_baseline.py、decode_cache_snapshot.py、signal_region_probe.py、jni_prefix_probe.py、metadata_decode_probe.py 五处最小修复；output/apk/baseline.json 重建（verify_phase_a PASS，44 文件）；AGENTS.md；新增 docs/tasks/20261016-reproducibility-audit.md。
- **实测**：隔离环境 11 项（3 项失败复现＋8 项通过）；项目侧 verify_phase_a PASS、v3 重放 PASS（0 差异，测试目录已删）。未验证：il2cpp 镜像、native_debug、chronicle、采集链、bdl 全量隔离、全新机器安装、非 Windows 平台。
- **文件盘点**：output 23.54GB/97.7 万文件（full_unpack 20.24GB 可重建媒体、export 1.40GB、field_guide 0.75GB 等，分类与存放建议见审计文档 §7）；work 4.30GB；raw 3.80GB；.git 仅 1MB。
- **边界**：未提交 git、未推送、未打包上传、未删除或覆盖既有成果；会话期间并行任务已为 NativeDecoder 补 cert_hex/protection 并新建 scripts/release/ 打包脚本（其范围，未接管）。下一阶段：git 补缺→根 README→cert_hex 实测→chronicle/bdl 隔离补测→发布清单草案。

更新：2026-10-16（完整解包）。本轮完成已取得本地资源完整解包：68655个bdl全部解码展开、834741个对象导出；前轮ability1008及前六类型有效，不重跑A—E/核心全量校验/手机，原始资源、v3/E和独立报告不改。

## 当前交付：本地资源完整解包（full_unpack）

- 入口：[阅读说明](output/full_unpack/README.md)、[输入账本68993行](output/full_unpack/ledger.jsonl)、[覆盖统计](output/full_unpack/coverage.json)、[4项验证PASS](output/full_unpack/validation.json)、[manifest](output/full_unpack/manifest.json)、[cid附加索引6233](output/full_unpack/cid_index.json)。
- 范围：composite_inventory全部68993文件。68655 bdl经DecodeXorData（每文件前256字节）转UnityFS后UnityPy展开，100%成功、0部分、0失败；77个data5沿用v3已验证解码（补采密文一致）；261个其他文件分类为il2cpp引擎文件4（复用）、UnityShaderCache 206、广告SDK 34、macOS垃圾17，理由逐条在账本。
- 产物20.24 GiB/903396导出文件：73490 PNG（原尺寸mip0含透明）、17389 WAV（Vorbis→PCM）、50051 OBJ、2845 TXT（BGMTable/Motion/Tips等UTF-8）、759621 JSON（622311个45类typetree+68655包清单+68655包索引）。每包objects_index.json记录对象类型/path_id/导出文件/纹理格式（ETC2_RGBA8 34335、ETC_RGB4 33784等）/音频参数；命名冲突（含大小写）加path_id后缀，全量逐包索引↔磁盘核对0失配。
- 字节/特殊值约定：typetree字节转__bytes_hex__（>256KB截断记SHA）、非有限浮点转__non_finite_float__；无静默补零。本轮0例typetree失败退存.bin。
- 已闭合问题：15包大小写命名覆盖+75个旧命名遗留文件清理；纹理格式名UNKNOWN元数据修正（全量重跑14.2分钟）。
- 实际命令：`full_unpack_run.py --workers 14`（分片续跑，中断自动跳过已完成）→ `full_unpack_merge.py` → `full_unpack_verify.py` → `full_unpack_finalize.py`；现有.venv（UnityPy 1.25.4/Pillow 12.3.0/unicorn），无新依赖，未连手机。
- 剩余：字段语义解释（另一任务线）、APK内置媒体批量导出（索引已有，可复用本管线）、cid_index仅命名规律非绑定证明、257个非游戏文件未展开（有理由）、全游戏索引不可信不声明100%。详见README剩余问题列表。

## 前轮交付：TargetStageAll地形条件全体攻防可查

- [原对照页](output/card_comparison_cid30236/index.html)含七个独立检索区，1095/1017/2012/3000/99/7/1008分别407/321/406/382/133/64/37条。1008相关逐效果行补param0和对象条件/依据；原101项、截图、33概览状态保留。
- [77条规则](output/card_comparison_cid30236/field_dictionary.json)：1008两旧攻防规则扩大、新增param0。来源/原值/类型/字节及JSON定位、中文解释、换算、单位/条件、三类确认状态另列；总2684来源记录/6613存在字段，普通子集1723/4947、60规则。未改v3历史字典。
- 玩家侧当前param是接受者，提供者候选来自_aChara_Player，非空且存活活动；实际类型/资格筛选执行。1008段无自身排除、接受者职业或距离筛选，可含自身/其他队友。非活动提供者转独立后备路径，未证明1008后备安装/转写，40526403后备原文保留；敌用同表记录不推定玩家侧实际装入。
- param0复用7相同IsTargetStage/当前背景flag证据，9种源编码；新3/607分别对99背景核实，607=7或6。param1乘接受者本项攻击，param3乘本项受伤量，均不在该段乘Chain。43023606沙漠下本项攻击/减伤各12.5%；102070攻击5%、防御原值1为中性。完整叠加/HP及其余字段不扩张。
- [1008限定依据](output/ordinary_effects/ability1008/README.md)、[trace](output/ordinary_effects/ability1008/trace.json)、[389项本轮原生检查](output/ordinary_effects/ability1008/native_checks.json)。只新增ordinary_1008_probe.py及相应证据，更新原字段模块/生成器/逐效果/查询/验证器；CSV/JSON/HTML和manifest同流程生成，未手改展示。
- 实际执行新1008探针389项、主生成器及验证器71项，全部通过；四个命令行样本含普通/Boss同号隔离通过。源字节/换算/背景匹配/CSVJSON/链接及前六类型、101项/五组政策回归通过；七段实际生成搜索脚本的V8 DOM夹具14项通过。浏览器file限制保留，未做视觉验收；旧原生证据只读，未重跑7的1390项。
- [查询脚本](scripts/query_effect_dictionary.py)示例：`.venv\Scripts\python.exe -B scripts/query_effect_dictionary.py --id 43023606`；102070看中性防御，42011507看607。target_conditions列param0，trigger_context列范围和来源边界。前轮[7规则](output/ordinary_effects/ability7/README.md)及102071森林/沙漠源内矛盾、2/250原值有效；[五组政策](output/card_comparison_cid30236/difference_sources/adoption_policy.json)不变，[旧审验](output/card_comparison_cid30236/completion_audit.json)仅绑定冻结旧载荷。

下一最小动作：定向追40526403后备生效原文与1008活动提供者路径的关系，先查该卡后备安装/转写及独立Backup记录；不重新调查已核地形和攻防。15%剩余额度暂停线保留，最近可见剩16%。

## 前轮字段对照进展：type105（2026-10-16，后续以当前节为准）

- [チーカ cid30236 HTML](output/card_comparison_cid30236/index.html) 沿用原33项结构，新增一项局部规则对应：现在10项文本/局部规则已对应、14项原值待解释、5项差异、2项未对应、2项网站添加排除；不是完成率。[详细证据与重建命令](output/boss_chain/type105/README.md)。
- 普通pattern43023601→Boss43023600、沙漠43023600→43023605、超共鸣43023602→43023609；param1=3.5/3.75/4.25是**单次攻击技能基值系数**。整数伤害输入=floor/clamp(float32(getBasicSkillAttack(true)×param1))，Chain已在基值内参与，不重复乘。基值使用BattleParam._skillAtk及状态/技能等因子，不能直接当面板ATK倍率或最终扣血。
- param6=5为每目标尝试上限，有限正数向零截断；范围判定前计数。目标持续在范围内可产生5次Attack调用，范围外会消耗预算。对应页同时分列原值已找到、对应关系已确认、局部计算已确认/最终伤害未知。
- 同一生成器新增[2条type105字段规则](output/card_comparison_cid30236/field_dictionary.json)、[142记录/284存在字段CSV](output/card_comparison_cid30236/verified_parameter_views.csv)及JSON，保留原字段、值/类型、Boss命名空间、来源SHA、记录ID、字节和JSON定位、单位/条件/证据。未修改v3历史字典或其他类型解释。
- 实际执行现有.venv的 `scripts/boss_type105_trace.py`、`boss_type105_probe.py`、`build_chica_comparison.py`、`verify_chica_comparison.py`。11项受控片段检查及11项局部数据/结构检查通过；[验证结果](output/card_comparison_cid30236/validation.json)。54条证据一致、三档关联/6样本字段源字节一致、同类型284字段及三组CSV/JSON、HTML33项/链接/manifest核对通过。未重跑A—E、未连接手机、无新依赖。
- 受控夹具建模引擎/ParamS访问及能力提供值，Attack入口拦截；不证明实际HP变化、当前装载或玩家解锁。初版静态脚本的施法者类型名定位失败已按类型索引修正重跑，详情留在局部说明。浏览器安全策略拒绝file协议，视觉验收未完成；结构检查通过。
- 剩余具体缺口：type112单次陷阱伤害基值、九个位置及触发次数；下一步只从Boss43023602 param1=.75追到处理器/伤害输入，再核同卡档位。type105局部规则已从待办移除，完整战斗伤害和pattern选择仍未知。

最终验收依据：[阶段E独立交付复审报告](output/审查报告/阶段E独立交付复审报告_2026-10-15.md)。复审独立重跑五种指针、12项检查和4项受控原生结构场景均通过；新旧10个数据与样本载荷一致。未确认范围继续保留，不宣称全游戏覆盖、当前玩家生效配置、全部字段解释或最终战斗倍率。初审修正工作已结束，不重复执行。

## 已成立基线

- APK：com.sega.chainchronicle 5.6.2/56021，Unity2021.3.58f1。必要程序/配置已提取，未批量导出媒体。
- 原APK、14个采集件不改写。11个data5已解码并通过C阶段完整性/结构验证；chronicle.dat内置主表已解出。元数据和必要原生代码已恢复，不要求完整Android初始化或全部源码。
- D：cid2327「すこやかなるメイド エレミア」→40232705→40232706的原记录、安装/展开/资格/HighHPAll条件链已建立。25%/50%门槛看接受者，局部运算有代码与受控模型依据，不等于当前实机生效或最终倍率。
- D：daSkill逐ID先查JSON层，缺ID才回退APK，不逐字段合并。36000358分别保留APK300.0/缓存400；当前加载版本未知。外部数据库截图仅EXTERNAL_REFERENCE。

依据：[阶段D独立审查（只读）](output/审查报告/阶段D独立审查报告_2026-10-15.md)、[标准样本](output/sample/sample_trace.md)、[完整样本JSON](output/sample/sample.json)。

## 全量采集与新缓存交付（2026-10-15）

当前入口：[阅读说明](output/cache_full_20261015_v3/README.md)、[选定指针](output/cache_full_latest.json)、[来源/版本清单](output/cache_full_20261015_v3/manifest.json)。手机端工作已完成，可拔下手机。

- 原件`raw/phone_20261015_full_02/external_cache.tar`3948107776字节；工作副本`work/phone_20261015_full_02/`。68828个文件、内容3895475185字节，全部路径/大小与本次清单一致，无缺项或差异；OBB为空。首次中文路径ADB pull失败保留在full_01，随后只读tar流成功，无手机文件改动。
- 77个data5、68490个bdl、261个其他文件全部取得。77个data5全部通过原生解密、外层SHA1、gzip CRC/长度及严格JSON核对；bdl和其他混合文件的目标语义仍未穷尽。全量名称/大小校验不冒充原子采集或全量双端哈希。
- 新缓存角色1488、普通技能8634；Boss pattern2149、Boss技能3745。完整77份JSON在[decoded](output/cache_full_20261015_v3/decoded)，[records.jsonl](output/cache_full_20261015_v3/records.jsonl)共39047个记录/文档视图，[tables.csv](output/cache_full_20261015_v3/tables.csv)列134个数组/文档视图数量。原嵌套、缺失、空值、重复和包装字段保留；非数组包装字段仍在完整JSON，不把视图总数当角色实体数。
- 更新[字段字典CSV](output/cache_full_20261015_v3/analysis/field_dictionary.csv)/[JSON](output/cache_full_20261015_v3/analysis/field_dictionary.json)：4671项，仅本缓存，已确认1007/推断47/未知3617。与旧双来源11261项范围不同，不计算解释率；CSV长示例有显式预览标志与完整JSON定位。
- 新[覆盖审计CSV](output/cache_full_20261015_v3/analysis/coverage_audit.csv)/[JSON](output/cache_full_20261015_v3/analysis/coverage_audit.json)：资源取得缺口已补齐至本次可访问目录；结构、关联、语义范围继续分开。所有原始文件可离线再分析，尚无全游戏可信索引。
- cid2327已找到3个pattern及其6条Boss技能：[原记录与候选链](output/cache_full_20261015_v3/analysis/cid2327_patterns.json)、[原文/参数48行CSV](output/cache_full_20261015_v3/analysis/cid2327_pattern_fields.csv)。type116/27/13及原参数存在；Boss读取/安装、后续段执行条件、type27/13单位未知。Boss40232705与普通能力40232705严格分域。已有HighHPAll规则仍仅34条、143个存在字段，不推定实际开放或最终倍率。
- 旧9个缺候选技能ID均在本批找到。当前已列范围23491条引用：普通技能按既有逐ID条件回退，Boss只分别列缓存/APK候选，不套用优先级。仍有60次Extra技能候选引用（12个ID）和6次传授pattern缺候选，[未关联CSV](output/cache_full_20261015_v3/analysis/unresolved_references.csv)逐位置保留；不等于66个资源缺件。36000358仍为缓存400/APK300，未合并当前生效值。
- 适配两个已观察包装：helper/search的gzip从载荷偏移0开始，原主表偏移6。questdigest提高受控实例指令上限至120000000/60秒后成功，算法未变。只新增适配器，未改原E解码脚本。初次74成功/3失败记录及修正前中间输出保留供追溯。
- [13项检查PASS](output/cache_full_20261015_v3/analysis/checks.json)：文件对账、77文件哈希与校验、39047条字节/pointer、409个四槽/1079个八槽完整保留、偏移0/6重复解码、破坏/截断/错误文件名拒绝、样本和旧缺ID、冲突、CSV追溯及引用数量。未重跑无关A—D/E实验；不是实机或独立审查。

实际命令（先采集到新原件，再在工作副本分析）：

```powershell
& .\.venv\Scripts\python.exe -B scripts/collect_cache_archive.py --probe output/phone_full_20261015 --snapshot raw/phone_20261015_full_02
& .\.venv\Scripts\python.exe -B scripts/extract_cache_archive.py --snapshot raw/phone_20261015_full_02 --work work/phone_20261015_full_02 --output output/phone_full_20261015/extraction
& .\.venv\Scripts\python.exe -B scripts/decode_cache_snapshot.py --work work/phone_20261015_full_02 --output output/cache_full_20261015_v3 --reuse-dir output/cache_full_20261015_v2
& .\.venv\Scripts\python.exe -B scripts/analyze_cache_snapshot.py --input output/cache_full_20261015_v3
& .\.venv\Scripts\python.exe -B scripts/verify_cache_snapshot.py --input output/cache_full_20261015_v3
```

采集/提取/导出命令要求新目录；不要把以上已执行路径再用于覆盖历史。离线重跑范例、现有依赖和写入范围见新README；不需要连接手机或安装新包。下一步优先核对Boss pattern读取链及type27/13处理器，再解释必杀后续段；剩余候选缺引用先查命名空间和加载规则。当前没有追加手机操作的具体阻塞。

## 治疗上限与时间单位补充（2026-10-15）

- [最新阅读说明](output/boss_heal/README.md)、[合并字段字典CSV](output/boss_heal/field_dictionary.csv)、[54行样本对照CSV](output/boss_heal/cid2327_description_fields.csv)、[批量字段视图](output/boss_heal/verified_parameter_views.csv)（均有JSON）。8条局部规则覆盖772记录3084个存在字段；本轮新增53个type27标志字段解释。
- 追通skillflag0_1高32位装配、常量元数据数组、GetOverHealRate和Heal上限分支。40232701原值1024→bit42→HP上限1.6倍；40232704原值2048→bit43→1.8倍。仅原记录标志，能力可合入其他位，不能冒充最终实机结果。
- UpdateParameter→BattleManager.GetDeltaTime→Unity Time.fixedDeltaTime成立，结合2021.3官方API文档，type27间隔2、type13支持时间30确认为游戏秒，不是现实墙钟秒。15次回复首次update可触发，不把15×2直接当精确持续时间。
- 13项受控原生检查通过（7个标志档位/组合、6个HP上限边界），执行真实选择函数及Heal上限片段，ParamS访问/小正整数加法建模；未运行完整Heal或实机。初始夹具入口x0缺值已修正后重验，详情见README。
- 修正Boss样本CSV漏列skillflag前缀的6行；原JSON未丢失。build_boss_chain_guide.py已最小修正，样本48→54行，逐槽/逐字段及CSV复杂值核对通过。旧E/v3载荷及全部独立报告未改。
- 本轮命令：现有.venv Python -B运行scripts/boss_heal_trace.py、scripts/boss_heal_probe.py、scripts/build_boss_heal_guide.py。只写output/boss_heal；视图修正另写output/boss_chain。manifest保存输入与代码哈希，非独立审查结果。
- 仍需闭合pattern选择/超共鸣切换及逐段触发；技能基值、整数转换、完整Heal及支持聚合仍未知。下一步优先样本选择链，非必要不采手机。补下载165个bdl的覆盖与语义未知维持前节结论。

## 补下载缓存已核对并补采（2026-10-15 20:30）

- 手机连接恢复。新清单68993文件，较前一份增加165个bdl，无删除；已有文件大小/mtime无变化。补采全部165新增包及77个data5，共242文件到raw/phone_20261015_refresh_02，旧原件不改。
- [本次交付说明](output/cache_refresh_20261015/README.md)、[新增文件CSV](output/cache_refresh_20261015/added_resources.csv)、[覆盖表](output/cache_refresh_20261015/coverage_audit.csv)、[4项核对PASS](output/cache_refresh_20261015/checks.json)、[新旧原件映射](output/cache_refresh_20261015/composite_inventory.jsonl)。242文件提取/归档内容核对通过。
- 77个data5重取密文与v3完全一致；核验完整JSON哈希后复用解码，重新导出39047记录视图，原值、类型、顺序、定位一致。角色1488、普通技能8634、Boss pattern2149、Boss技能3745；本次未新增主表记录。沿用v3字段/关联视图，不冒充新原生解码测试。
- 新清单范围77 data5 / 68655 bdl / 261其他，可由旧归档加补采映射定位。新增bdl尚未解码，未知目标语义保留；未重取媒体按路径/大小/mtime核对，不声称全量内容哈希或原子快照。
- 成功归档11169280字节；首次stdin清单尝试零输出已终止，保留refresh_01诊断。现无手机操作阻塞。旧E、v3及其指针不变，另设output/cache_refresh_latest.json。
- 下面Boss补充段的ADB阻塞为本次恢复前历史状态，已解决。下一步继续本地Boss flag/上限与时间链，以及有证据索引支持的bdl目标识别，不因新增包无目的重跑A—E。

## Boss后续段静态补充与新下载核对（2026-10-15）

- 新[补充说明](output/boss_chain/README.md)、[字段字典](output/boss_chain/field_dictionary.csv)、[cid2327描述/字段对照](output/boss_chain/cid2327_description_fields.csv)。7条type13/27局部规则，48行样本；推广至772条记录3031个存在字段，不覆盖旧E/v3输出。
- 静态追通Boss JSON/AB逐ID条件回退、按槽有序组装、SetExecSkill→initialize_ExAttack→type27/type13处理器。完整pattern选择/切换及当前运行版本仍未知。
- type27参数1为技能基值乘数、参数2为间隔输入、参数3为次数。type13参数1/2/6分别进入攻击/固定防御/移动增益，乘skillChainRate；参数3为支持时间。防御读取接受者_normalAtk，不能称为减伤百分比。时间到秒及整数转换规则仍待核实。
- 8项受控原生片段实验通过：首次update回复、间隔边界、15次停止、零次数、大delta仅一次、新设置覆盖、两组支持参数。Heal和SetSupport入口被拦截；不证明实际HP/最终倍率。3项样本结构检查通过。
- 强化治疗缓存param1=1.75，与截图2倍分别保留，不以截图改值。原始flag与缺失项保留。
- 用户告知又补下载缓存。本轮ADB两次无设备；Windows正常识别手机/MTP及ADB Interface，重启本机ADB后曾出现offline，已尝试reconnect offline。待恢复后核对新增范围，尚未宣称本次新下载已采集。旧全量采集发生北京时间19:19:14—19:23:33。
- 重跑：`.\.venv\Scripts\python.exe -B scripts/boss_chain_trace.py`、`scripts/boss_chain_probe.py`、`scripts/build_boss_chain_guide.py`（后两者同Python命令前缀）。只写output/boss_chain，依赖现有native/metadata/v3 records；无手机、无新依赖。下一步优先完成新下载对账及必要补采，再继续flag/上限与时间链。

## 前一离线字段与覆盖交付（保留旧快照，2026-10-15）

前一离线交付：`output/field_guide/guide_8753bb116c6e66b2/`。入口：[阅读说明](output/field_guide/guide_8753bb116c6e66b2/README.md)、[该系列指针](output/field_guide/latest.json)、[版本/输入/载荷清单](output/field_guide/guide_8753bb116c6e66b2/manifest.json)。以下数量及待采结论均绑定采集前旧快照；新进展以上节为准。

- [字段字典CSV](output/field_guide/guide_8753bb116c6e66b2/field_dictionary.csv) / [JSON](output/field_guide/guide_8753bb116c6e66b2/field_dictionary.json)：11261个来源/表/类型/路径条目；已确认2188、推断58、未知9015。此分组计数不是字段解释率；同名参数按效果分域，原值示例、缺字段计数、单位确认状态和定位分列。
- [实际样例CSV](output/field_guide/guide_8753bb116c6e66b2/record_comparisons_examples.csv) / [JSON](output/field_guide/guide_8753bb116c6e66b2/record_comparisons_examples.json)：30行，先做cid2327根/子HighHP、143001、必杀116入参、Extra五档、36000358两来源冲突；原文、片段、中文和数值解释分列。Extra仅关联同一嵌套对象的等级/描述/ID列表，不用文案百分比代替参数证据。
- [已验证规则扩展CSV](output/field_guide/guide_8753bb116c6e66b2/record_comparisons_highhp.csv) / [JSON](output/field_guide/guide_8753bb116c6e66b2/record_comparisons_highhp.json)：34条HighHPAll、143行存在字段；不解释param4、不补缺失，不推定玩家解锁或最终倍率。其他效果参数继续未知。
- 实际补充数据：原先完整JSON内的18296个辅助顶层记录/文档视图新增[JSONL](output/field_guide/guide_8753bb116c6e66b2/supplemental_records.jsonl)和[CSV索引](output/field_guide/guide_8753bb116c6e66b2/supplemental_record_index.csv)。覆盖APK Boss pattern/skill、传授、Class/Extra/Leader、羁绊/共鸣等；与E核心38849条合计57145个顶层视图。另2658个Extra/被动嵌套视图与父项重叠，不相加作为实体数。const根文档是分析视图，不是角色/技能实体。
- [覆盖审计CSV](output/field_guide/guide_8753bb116c6e66b2/coverage_audit.csv) / [JSON](output/field_guide/guide_8753bb116c6e66b2/coverage_audit.json)：按取得、解码、解析、导出、关联、解释分层。原E确认图不变，新增144967条辅助候选引用明确标推断。45次缺技能候选引用涉及Extra第491—493项的9个不同ID；1644次其他命名空间缺候选。全部保留，不证明记录失效，不默认删除或强行跨表按同号替代。
- 无E已验证入边的技能为缓存4828/APK9416；再计辅助候选仍无已知入边为缓存2859/APK6430。这是指定图内情况，不是废弃/无效数量。重复、历史、占位或未生效性质未确认时均原位置保存；str0数字串未自动当技能ID。
- 定向补查既有Unity头部19项错误：[原字节和分类](output/field_guide/guide_8753bb116c6e66b2/unity_header_gap_audit.json)。19项均32字节、脚本指针为空，共608字节已保存，不计成已解析游戏记录。已有9个按类名候选中6个完整可读、3个字段读取失败（2个ChroSkillParameterView、1个CharaDetailSkill），原二进制已保留；目标性质未证实，不把181783个对象元信息导出当所有目标字段已解析。
- [本轮核对](output/field_guide/guide_8753bb116c6e66b2/checks.json)：8项PASS，覆盖全部57145视图与原JSON字节/位置、APK四组件完整一致、原文片段、类型限定、CSV数量、辅助引用及19项错误原值保留；未重跑A—D或既有全部E原生实验，不冒充实机/独立审查。

重跑只写`output/field_guide`，复用Python3.12.14及现有依赖，不改正式E输入/历史构建：

```powershell
Set-Location 'E:\代码项目\锁链战记数据解包'
$env:PYTHONIOENCODING='utf-8'
& .\.venv\Scripts\python.exe -B scripts/build_field_guide.py
# 仅重建19项头部证据时先执行（现有UnityPy1.25.4）：
& .\.venv\Scripts\python.exe -B scripts/audit_unity_headers.py
```

字段交付器使用标准库与现有export_master辅助函数，需正式E构建、既有手机清单/采集清单、组件JSON、必杀追踪和Unity扫描/定向证据。头部脚本另需原Unity容器。完整工作区前提及CSV显示限制见新README，不是独立可运行包或未来快照通用验收器。

## 采集前具体缺口（历史依据，现已补采）

- 2026-10-14外部清单共68789个文件：77个data5，电脑取得/解码11个，66个尚无采集件；68451个bdl未取得/识别；其余261个其他后缀/无后缀文件仅取2个技术文件。三组总数已核对，未凭名称全部排除其他文件；候选文件数不等于目标表/记录数。没有可信全游戏目标索引，不报全游戏百分比。
- cid2327 pattern0=40232700、pattern1=40232701及传授候选patternid0=40232702未在当前APK pattern表找到。旧手机清单确有`bossinfo.data5`134000字节但电脑未取得，是高价值缺件候选，不能用普通skilllist同号或旧APK数据替代。
- 用户随后连接并授权全量采集；本次已完成外部files/cache采集及77文件解码，见上节。旧14件/旧清单保持，私有目录未采，不自动Root、不清缓存、不更新/卸载。
- 电脑已取得范围的原值和辅助视图可查询；全部资源取得、全部效果解释、当前加载版本/玩家开放状态、完整治疗/增益、成长及最终战斗倍率仍不成立。只对实际缺资源/运行态问题安排最小操作。

## 阶段E实际交付

当前快照：`snapshot_223183400c1c62013338`；正式构建：`build_261ac189c316abba`。旧构建`build_d21ab77ae4cbcdf3`及其载荷保留不变。

[使用说明/输出索引](output/export/README.md) · [当前构建指针](output/export/latest.json) · [manifest](output/export/snapshot_223183400c1c62013338/build_261ac189c316abba/manifest.json) · [验证结果](output/export/snapshot_223183400c1c62013338/build_261ac189c316abba/validation.json)。

|来源|角色记录|技能记录|四槽/八槽角色|原始槽位/sub引用|
|---|---:|---:|---|---|
|缓存|1482|8559|406 / 1076|10232 / 3203|
|APK|7800|21008|1927 / 5873|54692 / 7863|

- 合计38849条主记录，分四份来源JSONL；15份完整JSON保留所有辅助表及包装字段。角色含NPC等，不等于可用卡数；未声明全游戏覆盖。
- 合计75990条原始引用，含11066条sub边。全部父记录、引用序号、顺序与重复保留；根/子图不递归执行。一层展开59134项场景结果，均非玩家实际安装声明。
- 缓存104条sub须回退APK。假定JSON快照与APK都装入时，11066条sub均可关联；APK单层有3条APK sub缺目标，保留MISSING_ID。八槽55592个槽位保留SLOT_ROLE_UNKNOWN，未套四槽角色。
- 119个角色、568个技能跨来源同ID差异逐字段保存；不合成当前唯一值。当前输入来源内重复ID、坏记录、解析异常为0；未来异常会保留可取得原字节及具体错误，受影响查询标异常。
- 仅ability1105的存在param0/1/2/3/5附已有局部语义。缓存34条HighHPAll按27/4/3三种参数存在组合核对；不补默认值、不解释param4、不统一求值。其余29533条技能的参数语义UNKNOWN，原值照样导出。
- CSV仅38849行可追溯筛选视图，不是完整交付或生效表。JSONL保留缺失/null/0、字段类型、嵌套、数组；来源JSON副本保留精确原字节。
- manifest记录APK版本、快照、解析器/解释规则版本及SHA、验证器/模型脚本SHA和依赖锁；构建内保存必要脚本及证据副本。更新生成新snapshot/build，不覆盖旧输出。

## 阶段E交付修正（2026-10-15）

- 修复scripts/export_master.py已有构建分支：全部载荷校验成功后更新所选输出根的latest.json，缺失则创建；失败时不改指针或旧载荷。
- 新增scripts/verify_export_pointer.py。5种独立目录测试全部PASS：首次导出、同构建复用、缺指针恢复、指向其他真实构建后切回、损坏测试副本校验失败时指针不变。
- 原有12项当前快照验证及4项受控原生结构场景在独立目录重验PASS。主记录JSONL、引用、冲突、一层展开、异常、CSV和D样本等10个语义载荷与修正前字节一致；原输入、独立审查报告、旧正式载荷不变。
- 测试及日志只写work/phase_e_delivery_fix_20261015_4a244651af/；原验证器另在work/phase_e_fault_*创建/清理临时故障目录。测试完成前正式指针未变。
- 验证后生成正式新构建，manifest与独立已验构建字节一致、37个载荷SHA全部一致，再复制已绑定该manifest的validation.json；正式latest.json已明确选定新构建。
- 修正记录：[5种指针结果](work/phase_e_delivery_fix_20261015_4a244651af/pointer_tests/pointer_checks.json)、[语义与保护核对](work/phase_e_delivery_fix_20261015_4a244651af/delivery_fix_checks.json)、[正式选定依据](work/phase_e_delivery_fix_20261015_4a244651af/formal_selection.json)。损坏副本仅保留在独立测试目录供诊断。

## 验证与重跑

12项检查PASS：全量JSONL/完整JSON回读、类型与字节定位；记录/引用数量；四/八槽；cid2327；36000358冲突；循环/自环/共享子项；34条参数缺失组合；重复ID/坏JSON/null/0/缺引用；CSV追溯；输入与证据版本。

4项结构场景同时对照既有受控原生安装模型：42011300跨来源、602循环、36000376自环、40034712+40034714共享子项。新增故障注入导出也通过：坏缓存原字节及缺APK技能表错误保留，其余7800条APK角色、8559条缓存技能仍导出。临时测试件在work内运行后清理，未改真实输入。此前D的32项HP、11+1关联及4项来源实验复用锁定证据，不冒充本轮新测或实机观测。

```powershell
Set-Location 'E:\代码项目\锁链战记数据解包'
$env:PYTHONIOENCODING='utf-8'
& .\.venv\Scripts\python.exe -B scripts/export_master.py
& .\.venv\Scripts\python.exe -B scripts/verify_export.py
```

必须从项目根目录运行，复用Python3.12.14的现有.venv；导出器用标准库，验证器需要Unicorn2.1.4、work/protection/il2cpp_loader_seed1.bin、模型脚本及manifest所列原输入路径。构建目录可供数据消费，完整重跑依赖现有工作区，不能宣称独立运行包。完整逐项前提、独立输出命令及写入范围集中在README。

verify_export.py是当前快照回归工具，固定数量/样本不适用于任意新快照。当前更新是新输入重新全量导出并保留旧构建，未实现增量解析。新快照先核实变化与适用回归，再调整有依据的基准，不能只改断言获得PASS。依赖锁哈希目前不参与build ID，本轮未处理该可选改进；不承诺环境变化自动刷新构建。未新增依赖或验证干净环境安装。

## 仍未知与后续范围

- 补充只读核对：[cid2327截图字段覆盖](output/sample/cid2327_截图字段覆盖.md)。本轮已将相关辅助JSON补成逐记录/嵌套阅读视图并标注候选关联；截图LV60—80属性及全部细化倍率尚未还原。E完成及新字段对照都不代表整页数据库内容一一复刻；截图仍仅为外部参考。

- 玩家实际CardInfo.skillid、等级/突破/解锁条件、当前激活和接受的JSON版本；不能把主表定义当实例。
- 八槽角色、其他效果参数、完整必杀后续段与单位、全局叠加及最终战斗倍率。元数据枚举匹配不代表参数含义已确认。
- 外部数据库截图没有解锁条件或测试原始数据，不覆盖解包原值。
- 当前已完成本次可访问外部files/cache的全量采集和77个data5原值导出；bdl结构化目标、未列命名空间、私有/服务端范围仍未知。后续先利用本地原件静态核对，无需Root或模拟器，不把全部未知实机验证作为前置条件。

## 2026-10-16 截图对照与交接（本轮结束）

- 完成 [cid30236 チーカ HTML 对照页](output/card_comparison_cid30236/index.html)，附同目录 comparison.csv/json、evidence.json、reference.png 和 manifest.json；生成脚本 scripts/build_chica_comparison.py。
- 33项：9项文本或局部规则已对应、15项原值待解释、5项差异待核、2项未建立对应、2项网站添加排除；不是完成百分比。未把候选数字匹配写成最终倍率。
- 54条完整证据与v3源记录逐对象核对一致，全部引用和本地下载链接有效，HTML含33项；结果见 [validation.json](output/card_comparison_cid30236/validation.json)。内置浏览器本地服务连接超时，未完成视觉/交互验收；可直接在本地浏览器打开HTML。
- 完成 [HANDOFF.md](HANDOFF.md)，81行，文档链接已核对，包含当前有效数据入口、已确认规则、缺数据/缺解释、已解决事项及单一后续任务。
- 遵照用户限定，本轮未扩展新逆向、不连接手机、不重做历史验证；原始采集件、正式E构建和独立审查报告未修改。后续交由新对话。

- 2026-10-16用户补充：获得来源、登场日期为网站添加。已同步对照生成器、HTML/CSV/JSON及HANDOFF，不再计入游戏数据提取缺口；未扩展调查。
