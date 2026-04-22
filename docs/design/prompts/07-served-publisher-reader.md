# 任务 07：实现 Served 发布与读取

## 目标

建立 L2 Served 的发布、版本和读取基础能力。

## 必读文档

- `docs/design/01-architecture-rfc.md`
- `docs/design/30-standard-entities.md`
- `docs/design/50-quality-rule-spec.md`

## 任务范围

- 新建 `src/akshare_data/served/publisher.py`
- 新建 `src/akshare_data/served/manifest.py`
- 新建 `src/akshare_data/served/reader.py`
- 新建 `src/akshare_data/served/rollback.py`

## 关键要求

- Served 只接收通过质量门禁的 Standardized 数据
- 使用 `release_version` 组织已发布数据
- 生成发布 manifest
- reader 默认读取最新稳定版本

## 非目标

- 不让 Served 直接读取源站
- 不把旧 CacheManager 语义直接照搬

## 验收标准

- 可以发布一个标准化批次到 Served
- 可以按 dataset 读取最新稳定版本
- 可以回滚到前一版本
