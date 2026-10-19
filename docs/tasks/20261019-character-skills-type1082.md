# type1082 有界运行时取证

- 负责人：实施子智能体 `/root/type1082_implement`；主持 `/root`。
- 状态：任务−1余项与任务0完成，冻结待主持（2026-10-19）。任务卡原不存在；先执行了 git status，现有他人及旧 P3 改动均保留。
- 目标：任务 −1 余项依赖／源码漂移核对，然后只判定 extra_ability_info.skill_ids 消费路径上的 type1082.str0 是否运行时解引用并转发。
- 写入范围：本任务卡、`scripts/character_skills/type1082*.py`、`output/character_skills/type1082/`、`work/character_skills_type1082/`，以及 `work/character_skills_pivot/snapshots/` 的独立增量快照。
- 只读：旧 P3／profiles／公共规则和查询生成器／原始输入／旧审查／根交接。无 git add/commit/push，无依赖安装，无角色页、实机或完整引擎研究。
- 共享依赖：既有 `.venv`、`scripts/metadata_targets.py`、`scripts/il2cpp_sample_code.py`、`work/protection/{il2cpp_loader_seed1,metadata_aei_decoded}.bin`。
- 已沿用用户核验的旧快照 67 文件、六模块 6/6 hash、10 张任务卡，不重验这些验收项目。源码快照不等于 HEAD 可复现或干净环境复现通过。
- 任务−1余项：54项静态导入／代码目录JSON/JS配置依赖，旧已存源无漂移；发现两个遗漏定位模块，已补 `work/character_skills_pivot/snapshots/20261019-type1082-dependencies-20261019T105412Z/`。六模块／67文件／10卡直接沿用用户核验，不重新验收。
- 任务0结论：**FORWARD**。extra专用初始化先以子ID查包装，读取str0，实际Int32.TryParse写 `_skillId +0x14`，后续 active extra 消费器输出目标ID，BattleParam.SetSkillList 再查目标能力记录并加入能力列表。1082是metadata枚举ExtraAbility；包装在extra预处理中解引用，无须先走普通1082 switch。
- 结论入口：`output/character_skills/type1082/README.md`、`native_checks.json`。三项检查5/5、2/2、16/16；实际执行十进制解析循环，无离线解析结果替代。数据库／保护值解码／托管字典枚举等夹具边界与未执行路径明确登记。
- 限制：父limit_break索引与对象资格有门控；param0缺省／反射转换、账号队伍状态及逐句归属未恢复，不把4496关联范围算成4496个A；原文数字不重复归功于FORWARD，候选模板只作推断。
- 新源码：type1082_native.py、type1082_probe.py、type1082_snapshot.py；最终三脚本及本卡保存 `work/character_skills_pivot/snapshots/20261019-type1082-final/` 独立增量快照，旧快照保留。
- 实际命令：`& .\.venv\Scripts\python.exe -B scripts/character_skills/type1082_native.py`；只读定位命令见README。无全链回归、页面生成、实机或依赖变更。
- 下一步：成果冻结，等主持下一条任务；不自行继续渲染。
