# 版本模型设计

> 任务编号: `T1-006`
> 状态: Draft-v1
> 最后更新: 2026-04-23

## 1. 版本类型

| 版本字段 | 作用域 | 含义 |
|---|---|---|
| `extract_version` | ingestion/raw | 抓取器或源适配逻辑版本 |
| `normalize_version` | standardized | 字段映射与标准化规则版本 |
| `schema_version` | standardized/served | 实体 schema 版本 |
| `quality_version` | quality | 质量规则集版本 |
| `release_version` | served | 对外可读稳定发布版本 |

## 2. 版本关系

一个 `release_version` 对应一个确定的版本组合：

```text
release_version
  -> dataset
  -> input_batches[]
  -> extract_version
  -> normalize_version
  -> schema_version
  -> quality_version
```

## 3. 命名建议

- `extract_version`: `ext-vYYYYMMDD-N`
- `normalize_version`: `norm-vYYYYMMDD-N`
- `schema_version`: `sch-vMAJOR.MINOR.PATCH`
- `release_version`: `rel-<dataset>-YYYYMMDD-HHMM-<seq>`

## 4. 兼容策略

- `schema` 发生不兼容变更时，`MAJOR +1`。
- `normalize` 规则变更必须显式升级版本。
- 服务默认读取最新 `quality_passed=true` 的 release。

## 5. 最小元数据字段

- `version_id`
- `dataset`
- `created_at`
- `created_by`
- `change_summary`
- `compatibility`
- `upstream_refs`
