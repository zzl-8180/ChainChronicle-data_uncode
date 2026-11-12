# 局部忽略规则候选

仅本包内候选，未创建正式目标或应用规则。`manifest.json` 为33个新叶目标到16份局部 `.gitignore` 的精确对应；全部使用锚定的单个子目录／文件名规则，不扩大到项目源码、配置、导航或全根。现有cache的v1/v2、history的single及reference-analysis上级规则保持不变。根 `.gitignore` 不改，不强制暂存被忽略的数据。

`candidate.patch` 对观测时live的 `git apply --check` 通过。最终合入前重读现有局部文件，若有并发新增就按行合并，不整文件覆盖。这些规则只防止搬离output后意外把大载荷纳入Git，不是迁移／删除／提交授权。
