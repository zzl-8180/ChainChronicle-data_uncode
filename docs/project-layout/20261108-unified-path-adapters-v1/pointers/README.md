# 四个selector的小文件候选

仅按原审定pointer-change-plan生成的候选，不是正式切换。四个source的字节SHA／JSON与原绑定相同；7个改值字段都为directory、manifest、base_directory一类定位字段，逐个符合31根＋2控制文件总映射。snapshot_id、build_id、manifest_sha256、raw_snapshot及其他非定位值不改。精确字段和SHA见 [verification.json](verification.json)。

`baseline/` 只保存四份当前小JSON原字节，`candidate/` 放拟新位置的新JSON。正式selector、冻结manifest和载荷都未写。未来临前如任一source漂移，停止对应步骤、重新审定，不把当前候选直接覆盖新版。新位置和消费者尚待真实迁移后验读；不同selector与多根整体不是一个原子事务。
