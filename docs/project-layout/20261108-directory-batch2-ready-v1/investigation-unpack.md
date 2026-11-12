# 第二批目录整理：解包候选只读调查

本批准备两个整目录scope：**single 3文件/4,131,868B + v2 95文件/118,170,246B，总98文件/122,302,114B**。single低耦合；v2的最小复用适配已在候选副本实现并通过7项夹具回归，5入口/写域交接与实际执行授权仍待明确。尚未移动、合入live代码或改联接。旧HOLD不是否决理由，本轮已补齐具体接口与候选修复。

|候选|当前文件/逻辑字节|既有映射目标|本轮判断|
|---|---:|---|---|
|output/single|3 / 4,131,868|projects/unpack/history/single|低耦合整目录候选，待一次主持使用状态确认及临前身份门|
|output/cache_full_20261015_v2|95 / 118,170,246|projects/unpack/data/cache/cache_full_20261015_v2|整目录准备范围；复用候选已验证，5入口/共享写域交接和执行授权仍为门槛|
|output/decoded|23 / 17,027,377|projects/unpack/history/decoded|现存默认读写链多，不纳本批低耦合scope|
|output/export|234 / 1,500,467,070|projects/unpack/data/export|latest、固定manifest、研究/验证链及5隔离入口仍在，不纳本批|

四个候选均仅在其本树无跟随计数，未发现内部reparse；四个拟目标均不存在。没有全盘扫描、重跑解码/导出/生成业务、搬移或修改代码。完整细目、少量实读SHA、精确联接fileID见[机器报告](investigation-unpack.json)。

## single：可独立保留整个样本

本树恰为`charainfo.data5.json`、`charainfo.data5.json.raw`、`report.json`，共3项，无子目录。report保留原输入`work/phone_candidates/charainfo.data5`及原生解码结果，没有必须回读`output/single`的自目录路径。旧静态5条命中包括已退役的`output/share_bundle/build_bundle.py:39`，其余为旧库存盘点/冻结说明。现有`decode_data5.py:145`默认写`output/decoded`，可通过显式`--output`写任何样本目录；未发现维护代码固定读single，但这不证明外部命令或别的对话无人使用。

保持三个原件不变，不因与decoded可能同内容而删重。执行前仅需核当前身份、目标/祖先真实且无碰撞、主持一次确认无动态使用者，再按另获授权同卷整目录rename；外部旧新路径回执供历史盘点定位，不修改冻结审计或样本report。

## v2：具体阻断是接口，不是“旧映射HOLD”

当前95文件含77份decoded、14份analysis和4个根视图/回执。latest和当前角色数据读取指v3，`card_page_data.py:493`与抽查reader侧证均证实；本轮不选v3。

两项真实接口仍在：

1. C14—C18五个`impl/isolation_input/output/cache_full_20261015_v2`仍是真实junction，精确指向旧v2根。这与已退役的share_bundle/previous不同，未获得这五cache入口已停用的证明。报告只lstat/readlink，没有通过联接递归扫描。
2. `decode_report.json`和`decode_progress.json`各77条`json_file`保留旧`output\cache_full_20261015_v2\decoded\…`路径。维护中的`decode_cache_snapshot.py:64–65`直接`Path(row['json_file'])`；仅把`--reuse-dir`改成新target仍不能读到已搬的JSON。`STATUS.md:209`保留v3复用v2的历史命令。`analyze_cache_snapshot.py --input`还可能重写这个快照的analysis。

因此v2按本批**有界接口闭合后整目录迁**准备：保留95文件原字节；读取端使用已测试候选：明确--reuse-dir/decoded/<filename>.json.raw定位，原SHA门不变；5cache入口按单次主持交接的接管人/窗口另列精确切换；不靠改冻结JSON或常驻旧output兼容联接掩盖问题。不要求重解码或重建v3。

## decoded/export为何暂不纳入

`decode_data5.py`默认写decoded；`decode_cache_snapshot.py`默认读其report，`export_master.py`固定读该report/raw。`verify_data5.py`、`sample_trace.py`、Chica比较和阶段D探针还存在具体旧数据读口。export有`analyze_cache_snapshot.py:51`、`build_field_guide.py:154`、`verify_export.py:27`读latest/载荷，`export_master.py:238`默认产出，`verify_export_pointer.py:37`把其作为正式目录守卫，另有固定旧manifest比较及冻结研究probe。删除旧打包脚本没有撤销这些真实代码边。

这些是当前代码能力与历史接口的证据，不是声称它们正在运行。将来整理须单独闭合接口/指针，不把本轮single的低耦合结论套到所有旧目录。

## 最多一次主持交互

把以下事项合在一次明确交接，不追加逐步骤往返：确认single当前读写者及显式`--output output/single`调用；确认执行对话维护相关解包导航的写域；同时确认v2动态`--reuse-dir/--input`使用者、五cache入口接管人/共同窗口及复用resolver写域。两根都准备到实际执行前；v2候选已完成，剩余5入口/写域/临前门不以概念性HOLD替代。主线研究无需停工。临前身份/冲突检查由执行对话完成，不把一次答复视为永久无人使用保证。

## 保留边界

新增本调查JSON/Markdown和候选脚本/patch/tests；live脚本未改。v3、profiles/pages/ledger、raw、vault、已迁5317和11原位材料均排除。旧冻结库存、审查、报告及原路径值不改；旧P/v7定向字面查询未找到single/v2路径，但这不等于全域无保护。`projects/unpack/README.md`仍有已过时的旧打包准备态文字，已告父整合者，本调查不接管修改。

## 复用候选与验证

已核v2全部77个DECODED行均位于固定`decoded/<filename>.json.raw`，无例外。候选只改`--reuse-dir`分支一处定位：验证filename为单个安全basename，按显式reuse根拼decoded路径；冻结`json_file`不再被当作搬后物理读口。source SHA匹配才复用，JSON raw SHA仍必须等原meta；缺新文件保留FAILED_RETAINED，绝不读旧root或悄悄native降级；无reuse prior-report行为和recovered_variants相对布局保持。

[candidate](candidate/scripts/decode_cache_snapshot.py) SHA `818e03e8c0ddf9ed46ef9ef6ce8f2b0f51670657b45ed6b25e30227e7cac4f78`；[patch](decoder-reuse.patch) SHA `19fb7d01140d2985c4156438afe0fc87fa2a73d8270da5912f2097dd45246ef7`。`git apply --check`通过，未apply；live SHA前后均`46043f8ebdb6922475f8e744b4859e86c6970284195a4f842a9b2153762ea6ec`。

测试真实调用candidate.main，仅新小夹具，NativeDecoder/variant计算以trap禁止。7/7通过：搬后路径成功；新缺件不回旧root；JSON SHA漂移拒绝；cipher SHA不匹配不误复用；不安全basename拒绝；无reuse prior行为；recovered_variants不变。每例核冻结夹具report字节不变。具体回执与SHA在机器报告candidate_adapter。未复制118MB、未用真实APK解码、未运行真实v2生产命令。
