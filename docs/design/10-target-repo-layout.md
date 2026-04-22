# 目标目录结构设计

> 任务编号: `T1-001`
> 最后更新: 2026-04-22

## 1. 设计原则

- `数据层语义优先`：目录要反映数据生命周期，而不是历史缓存实现
- `模块边界清晰`：采集、标准化、发布、服务解耦
- `向后兼容`：保留 `api.py` 和 `__init__.py` 外部入口
- `单一命名`：dataset、schema、质量配置、服务文档使用同一标准名

## 2. 顶层目录建议

```text
src/akshare_data/
├── __init__.py
├── api.py                    # 对外兼容 facade
├── common/                   # 公共能力
├── ingestion/                # 接入与任务执行
├── raw/                      # L0 原始层
├── standardized/             # L1 标准层
├── quality/                  # 质量规则与门禁
├── served/                   # L2 发布层
├── governance/               # 元数据与血缘
├── service/                  # HTTP/CLI/SDK 读取入口
└── legacy/                   # 可选，迁移过渡壳
```

## 3. 模块职责

### 3.1 `common/`

- 错误定义
- 配置加载
- 日志
- 基础类型与工具

### 3.2 `ingestion/`

- source adapters
- router
- rate limiter
- scheduler
- batch/task model
- audit
- checkpoint

说明：`ingestion` 负责“拿到原始数据”，不负责对外服务。

### 3.3 `raw/`

- writer
- reader
- manifest
- schema fingerprint
- replay reader

说明：Raw 只保留原始语义，不做业务字段 rename。

### 3.4 `standardized/`

- entity schema
- field mapping
- symbol normalization
- normalizers
- writer/reader
- merge/upsert

说明：Standardized 是字段标准和实体契约中心。

### 3.5 `quality/`

- rule loader
- engine
- checks
- report
- gate
- quarantine

说明：质量规则只引用标准字段，不引用源字段别名。

### 3.6 `served/`

- publisher
- rollback
- manifest
- reader
- release selector

说明：Served 只面向发布版本，不直接持有源适配器。

### 3.7 `governance/`

- metadata catalog
- schema registry
- lineage
- owner registry
- change log

### 3.8 `service/`

- facade/read API
- query contract
- version selection
- missing data policy
- CLI/HTTP entry

说明：`service` 默认只读 `served`，如果需要补数，只能发起异步任务请求，不得同步回源。

## 4. 推荐代码骨架

```text
src/akshare_data/
├── __init__.py
├── api.py
├── common/
│   ├── __init__.py
│   ├── config.py
│   ├── errors.py
│   ├── logging.py
│   └── types.py
├── ingestion/
│   ├── __init__.py
│   ├── base.py
│   ├── router.py
│   ├── audit.py
│   ├── checkpoint.py
│   ├── rate_limiter.py
│   ├── scheduler.py
│   ├── models/
│   │   ├── task.py
│   │   └── batch.py
│   └── adapters/
│       ├── akshare.py
│       ├── lixinger.py
│       ├── tushare.py
│       └── mock.py
├── raw/
│   ├── __init__.py
│   ├── system_fields.py
│   ├── writer.py
│   ├── reader.py
│   ├── manifest.py
│   └── schema_fingerprint.py
├── standardized/
│   ├── __init__.py
│   ├── fields.py
│   ├── symbols.py
│   ├── schema/
│   ├── normalizer/
│   ├── writer.py
│   ├── reader.py
│   └── merge.py
├── quality/
│   ├── __init__.py
│   ├── engine.py
│   ├── gate.py
│   ├── report.py
│   ├── quarantine.py
│   └── checks/
├── served/
│   ├── __init__.py
│   ├── publisher.py
│   ├── rollback.py
│   ├── manifest.py
│   └── reader.py
├── governance/
│   ├── __init__.py
│   ├── catalog.py
│   ├── schema_registry.py
│   ├── lineage.py
│   └── ownership.py
└── service/
    ├── __init__.py
    ├── data_service.py
    ├── reader.py
    ├── version_selector.py
    ├── missing_data_policy.py
    └── cli/
```

## 5. 配置目录建议

```text
config/
├── standards/
│   ├── field_dictionary.yaml
│   ├── normalize_versions.yaml
│   └── entities/
│       ├── market_quote_daily.yaml
│       ├── financial_indicator.yaml
│       └── macro_indicator.yaml
├── mappings/
│   └── sources/
│       ├── akshare/
│       ├── lixinger/
│       └── tushare/
├── quality/
│   ├── market_quote_daily.yaml
│   ├── financial_indicator.yaml
│   └── macro_indicator.yaml
└── ingestion/
    ├── sources.yaml
    ├── rate_limits.yaml
    └── schedules.yaml
```

## 6. 数据目录建议

```text
data/
├── raw/
├── standardized/
├── served/
├── quarantine/
└── system/
    ├── metadata/
    ├── quality/
    ├── checkpoints/
    └── lineage/
```

## 7. 迁移注意事项

- 不把 `source adapters` 放到 `service/`
- 不把 `fetcher` 继续当成服务主逻辑中心
- 不把 `cache` 当作数据层名称
- 不新建第二套 dataset 命名

## 8. 最小迁移顺序

1. 创建 `common/ingestion/raw/standardized/quality/served/governance/service`
2. 保留旧入口，先做 re-export
3. 建首批 3 个数据集的 schema 与质量配置
4. 打通 `Raw -> Standardized -> Served`
5. 最后把 `DataService` 改为只读 Served
