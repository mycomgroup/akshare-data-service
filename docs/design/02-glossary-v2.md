# 术语表 (Glossary) v2

本文档定义 akshare-data-service 项目重构后的核心术语，统一命名规范，避免歧义。

> **适用范围**: 所有设计文档、代码命名、配置文件、Issue/PR 描述。

---

## 一、数据分层术语 (Data Layer)

| 术语 | 中文 | 定义 | 示例 | 注意事项 |
|------|------|------|------|----------|
| **L0 Raw Layer** | 原始层 | 数据源返回的原始数据，未经任何转换，保留完整 payload 和抓取元信息 | `data/raw/cn/market_quote_daily/dt=2024-01-15/batch_id=abc123/` | 1. 不可删除，用于回放和审计；<br>2. 保留原始字段名，不做 rename；<br>3. 必须包含系统字段：`batch_id`, `source_name`, `interface_name`, `request_time`, `ingest_time`, `raw_record_hash` |
| **L1 Standardized Layer** | 标准化层 | 经过字段映射、类型转换、单位统一的标准化数据，符合实体 Schema 定义 | `data/standardized/cn/market_quote_daily/` | 1. 字段名来自字段字典，不是源字段名；<br>2. 通过标准化器 (Normalizer) 从 Raw 层生成；<br>3. 未通过质量门禁的数据不能进入下一层 |
| **L2 Served Layer** | 服务层 | 发布给在线服务读取的稳定数据，通过质量门禁检查，带版本标记 | `data/served/cn/market_quote_daily/release_version=v2024.01.15/` | 1. 服务层只能读 Served 层，不能直接读 Raw 或 Standardized；<br>2. 发布后不可修改，只能发布新版本或回滚；<br>3. 每次发布有 `release_version` 和 Manifest 文件 |

---

## 二、数据实体术语 (Data Entity)

| 术语 | 中文 | 定义 | 示例 | 注意事项 |
|------|------|------|------|----------|
| **Dataset** | 数据集 | 某一业务域下的数据集合，按实体逻辑划分，有明确的 Schema 和质量规则 | `market_quote_daily`, `financial_indicator`, `macro_indicator` | 1. Dataset 是业务概念，不是物理存储目录；<br>2. 一个 Dataset 可能对应多张物理表（按时间、分区拆分）；<br>3. Dataset 有唯一 owner |
| **Table** | 表 | Dataset 的物理存储单元，Parquet 文件集合 | `data/standardized/cn/market_quote_daily/date=2024-01-15/*.parquet` | 1. Table 是物理概念，对应磁盘上的文件；<br>2. Table 有分区策略 (`partition_by`)；<br>3. Table 有 Schema version |
| **Entity** | 实体 | 业务语义上的数据对象，对应一个标准 Dataset，有主键、时间字段、业务边界 | `Security`, `MarketQuote`, `FinancialIndicator` | 1. Entity 先于 Dataset 定义；<br>2. Entity 定义主键、时间语义、单位；<br>3. Entity 是字段字典的组织单位 |
| **Field** | 字段 | Entity 的属性，有标准命名、类型、单位、允许空值等定义 | `close_price`, `turnover_amount`, `pe_ratio` | 1. 字段名使用 snake_case；<br>2. 每个字段有唯一标准定义（字段字典）；<br>3. 源字段映射到标准字段，映射规则版本化 |

---

## 三、任务执行术语 (Task Execution)

| 术语 | 中文 | 定义 | 示例 | 注意事项 |
|------|------|------|------|----------|
| **Batch** | 批次 | 一组任务的逻辑集合，共享同一个 `batch_id`，代表一次抓取或发布周期 | `batch_20240115_001` | 1. Batch 是可追溯的基本单位；<br>2. Batch 有状态：pending/running/succeeded/failed/partial；<br>3. 同一 Batch 可以回放、重算、回补 |
| **Task** | 任务 | 执行的最小单元，对应一次抓取或标准化操作 | `{interface: "stock_zh_a_hist", symbol: "600519", start_date: "2024-01-01"}` | 1. Task 有幂等键：source + interface + params + window；<br>2. Task 状态由 TaskExecutor 管理；<br>3. Task 失败可单独重试，不影响 Batch 其他 Task |
| **Job** | 作业 | 定时执行的批处理调度单元，包含多个 Batch | 每日盘后数据更新 Job | 1. Job 由 Scheduler 调度；<br>2. Job 有调度策略：日历、优先级、分区；<br>3. Job 与 Batch 是 1:N 关系 |
| **Pipeline** | 管道 | 数据流转的完整链路：Extract → Land → Normalize → Validate → Publish | Raw → Standardized → Served 管道 | 1. Pipeline 定义数据生命周期；<br>2. 每个 Dataset 有对应 Pipeline；<br>3. Pipeline 阶段不可跳过 |

---

## 四、数据操作术语 (Data Operation)

| 术语 | 中文 | 定义 | 示例 | 注意事项 |
|------|------|------|------|----------|
| **Extract** | 抽取 | 从数据源获取原始数据的操作 | `akshare.stock_zh_a_hist(symbol="600519")` | 1. Extract 只负责获取，不做转换；<br>2. Extract 结果直接写入 Raw 层；<br>3. Extract 有 `extract_version` |
| **Normalize** | 标准化 | 将 Raw 数据转换为 Standardized 数据，应用字段映射、类型转换、单位归一 | `Normalizer.transform(raw_df) → standard_df` | 1. Normalize 基于 Normalizer 类和字段映射配置；<br>2. Normalize 有 `normalize_version`；<br>3. Normalize 输出必须符合 Entity Schema |
| **Validate** | 校验 | 执行质量规则检查，生成质量报告 | `QualityEngine.validate(standardized_df)` | 1. Validate 在 Standardized 层执行；<br>2. Validate 结果决定是否可 Publish；<br>3. Validate 不修改数据，只产出报告 |
| **Publish** | 发布 | 将质量通过的 Standardized 数据发布到 Served 层 | `Publisher.publish(batch_id, dataset)` | 1. Publish 必须通过质量门禁；<br>2. Publish 生成新 `release_version`；<br>3. Publish 是幂等的，同批次重复发布不产生新版本 |

---

## 五、质量体系术语 (Quality System)

| 术语 | 中文 | 定义 | 示例 | 注意事项 |
|------|------|------|------|----------|
| **Quality Gate** | 质量门禁 | 决定数据是否可发布到下一层的规则组合，必须全部通过才能 Publish | `Gate.check(batch_report) → pass/fail` | 1. Gate 是阻断性检查，不可绕过；<br>2. Gate 规则可配置权重和阈值；<br>3. Gate 失败数据进入 Quarantine 区 |
| **Quality Rule** | 质量规则 | 单个校验规则，定义检查类型、字段、阈值、严重级别 | `non_null(primary_key)`, `unique(primary_key)`, `range(close_price, min=0)` | 1. Rule 配置化存储在 `config/quality/*.yaml`；<br>2. Rule 有类型：completeness/consistency/anomaly/schema；<br>3. Rule 有版本，变更需记录 |
| **Quality Report** | 质量报告 | Batch/表/分区的质量检查结果汇总 | `{batch_id, dataset, pass_rate, failed_rules, details}` | 1. Report 是发布决策依据；<br>2. Report 持久化存储，可回查历史；<br>3. Report 包含字段级、记录级失败明细 |
| **Quarantine** | 隔离区 | 存放质量不合格数据的临时区域，等待人工审查或修复 | `data/quarantine/cn/market_quote_daily/batch_id=...` | 1. Quarantine 数据不进入 Served 层；<br>2. Quarantine 数据有处理状态：pending/fixed/discarded；<br>3. Quarantine 数据定期清理或归档 |

---

## 六、数据源术语 (Data Source)

| 术语 | 中文 | 定义 | 示例 | 注意事项 |
|------|------|------|------|----------|
| **Source** | 数据源 | 数据提供方，有优先级和健康状态 | `lixinger` (primary), `akshare` (backup), `tushare` (optional) | 1. Source 有优先级排序；<br>2. Source 有健康监控和熔断机制；<br>3. Source 失败后自动切换备源 |
| **Interface** | 接口 | Source 提供的具体数据获取方法，有参数签名和字段映射 | `stock_zh_a_hist`, `stock_financial_analysis_indicator` | 1. Interface 配置化定义（`config/interfaces/*.yaml`）；<br>2. Interface 有 `rate_limit_key` 限速归属；<br>3. Interface 映射到 Dataset/Entity |
| **Endpoint** | 端点 | Interface 的 API 调用地址，用于限速分组 | `push2his.eastmoney.com`, `api.lixinger.com` | 1. Endpoint 决定域名级限速；<br>2. Endpoint 对应 `rate_limit_key`；<br>3. Endpoint 有健康状态跟踪 |

---

## 七、状态与版本术语 (State & Version)

| 术语 | 中文 | 定义 | 示例 | 注意事项 |
|------|------|------|------|----------|
| **Checkpoint** | 检查点 | 任务执行的断点记录，用于断点续跑 | `{interface, last_symbol, last_date, status}` | 1. Checkpoint 持久化存储；<br>2. Checkpoint 支持增量任务恢复；<br>3. Checkpoint 有 TTL，过期自动清理 |
| **Manifest** | 清单文件 | Batch 或 Release 的元数据文件，记录文件列表、条数、Hash、版本 | `data/served/.../manifest.json` | 1. Manifest 是数据集的身份证；<br>2. Manifest 支持版本追溯；<br>3. Manifest 与数据文件原子写入 |
| **Version** | 版本 | Schema、规则、发布等变更的唯一标识 | `extract_version=v1`, `normalize_version=v2`, `release_version=v2024.01.15` | 1. Version 有多种：extract/normalize/schema/release；<br>2. Version 变更必须有记录和原因；<br>3. Version 支持回滚到指定版本 |
| **Release** | 发布版本 | Served 层的一次发布，对应一个 `release_version` | `release_version=v2024.01.15.001` | 1. Release 只来自质量通过的 Batch；<br>2. Release 不可修改，只能发布新 Release 或回滚；<br>3. Release 是服务读取的版本单位 |

---

## 八、时间语义术语 (Time Semantics)

| 术语 | 中文 | 定义 | 示例 | 注意事项 |
|------|------|------|------|----------|
| **event_time** | 事件时间 | 业务事件发生的时间 | 股票交易日期 `trade_date` | 1. event_time 是业务主键的一部分；<br>2. event_time 用于时间序列排序；<br>3. event_time ≠ 抓取时间 |
| **trade_date** | 交易日期 | 股票/ETF 的交易日期，特定事件时间 | `2024-01-15` | 1. trade_date 是日线数据的主键字段；<br>2. trade_date 格式统一为 `YYYY-MM-DD`；<br>3. trade_date 必须存在于交易日历 |
| **report_date** | 报告日期 | 财务报告的报告期截止日 | 季报 `2024-03-31` | 1. report_date 区分报告期；<br>2. report_date ≠ publish_time；<br>3. 同一 report_date 可有多份报告 |
| **publish_time** | 发布时间 | 数据/报告对外发布的时间 | 财报发布日期 `2024-04-25` | 1. publish_time 决定数据可用性；<br>2. publish_time 用于数据新鲜度判断；<br>3. publish_time 可能晚于 event_time |
| **ingest_time** | 入库时间 | 数据写入系统的时间戳 | `2024-01-15T10:30:00Z` | 1. ingest_time 由系统自动生成；<br>2. ingest_time 用于审计和追溯；<br>3. ingest_time ≠ event_time |

---

## 九、核心动词规范 (Action Verbs)

| 动词 | 含义 | 使用场景 | 禁止用法 |
|------|------|----------|----------|
| **fetch** | 从源获取数据 | `fetcher.fetch()`, `FetchConfig` | 不要用于内部读取 |
| **read** | 从存储读取数据 | `reader.read()`, `RawReader`, `ServedReader` | 不要用于从源获取 |
| **write** | 写入存储 | `writer.write()`, `RawWriter` | 不要用于发布操作 |
| **extract** | 抽取原始数据 | `extractor.extract()` | 不要用于标准化后的数据 |
| **normalize** | 标准化数据 | `normalizer.normalize()` | 不要用于原始数据 |
| **validate** | 校验质量 | `validator.validate()` | 不要用于数据获取 |
| **publish** | 发布到服务层 | `publisher.publish()` | 不要用于写入 Raw/Standardized |
| **rollback** | 回滚发布版本 | `rollbacker.rollback()` | 不要用于删除数据 |
| **replay** | 从 Raw 重放生成 | `replayer.replay(batch_id)` | 不要用于增量更新 |

---

## 十、命名规范 (Naming Convention)

### 10.1 文件与目录命名

```
data/
├── raw/                    # L0 原始层
│   └── <domain>/           # 业务域 (cn/us/global)
│       └── <dataset>/      # 数据集名 (snake_case)
│           └── dt=<date>/  # 分区 (event_time)
│               └── batch_id=<id>/  # 批次分区
│                   └── *.parquet
├── standardized/           # L1 标准化层
│   └── <domain>/           # 业务域
│       └── <dataset>/      # 数据集名
│           └── <partition>=<value>/  # 分区
│               └── *.parquet
├── served/                 # L2 服务层
│   └── <domain>/           # 业务域
│       └── <dataset>/      # 数据集名
│           └── release_version=<version>/  # 发布版本分区
│               ├── *.parquet
│               └── manifest.json
├── quarantine/             # 质量隔离区
│   └── <domain>/           # 业务域
│       └── <dataset>/      # 数据集名
│           └── batch_id=<id>/
│               └── *.parquet
└── system/                 # 系统数据
    ├── metadata/           # 元数据
    ├── quality/            # 质量报告
    └── checkpoints/        # 检查点
```

### 10.2 类与模块命名

| 命名模式 | 示例 | 说明 |
|----------|------|------|
| `<Layer>Writer` | `RawWriter`, `StandardizedWriter` | 各层写入器 |
| `<Layer>Reader` | `RawReader`, `ServedReader` | 各层读取器 |
| `<Action>er` | `Extractor`, `Normalizer`, `Publisher` | 操作执行器 |
| `<Entity>Normalizer` | `MarketQuoteNormalizer`, `FinancialIndicatorNormalizer` | 实体标准化器 |
| `<Type>Engine` | `QualityEngine`, `ValidationEngine` | 执行引擎 |
| `<Type>Manager` | `CheckpointManager`, `ManifestManager` | 状态管理器 |
| `<Type>Builder` | `TaskBuilder`, `QueryBuilder` | 构建器 |

### 10.3 配置文件命名

```
config/
├── standards/              # 标准定义
│   ├── field_dictionary.yaml       # 字段字典
│   ├── normalize_versions.yaml     # 标准化版本
│   └── entities/                   # 实体定义
│       ├── market_quote_daily.yaml
│       └── financial_indicator.yaml
├── mappings/               # 源字段映射
│   └── sources/
│       ├── akshare/
│       │   └── market_quote.yaml
│       └── lixinger/
│       │   └── market_quote.yaml
├── quality/                # 质量规则
│   ├── market_quote_daily.yaml
│   └── financial_indicator.yaml
└──── interfaces/           # 接口定义
    ├── stock/
    ├── fund/
    └── macro/
```

---

## 十一、术语对照表 (Term Mapping)

### 旧术语 → 新术语

| 旧术语 (当前代码) | 新术语 (重构后) | 说明 |
|-------------------|-----------------|------|
| `CacheTable` | `Dataset` + `Table` | Cache 概念升级为数据资产概念 |
| `TableRegistry` | `MetadataCatalog` + `SchemaRegistry` | 注册表升级为元数据中心 |
| `storage_layer` (daily/meta/snapshot) | `L0/L1/L2` + `storage_layer` | 新增三层架构，原 storage_layer 作为分区策略保留 |
| `aggregated` (DuckDB) | `Standardized` + `Served` | DuckDB 概念与三层数据架构对齐 |
| `raw` (DuckDB fallback) | `Raw Layer` (L0) | 原 DuckDB raw fallback 概念与 L0 Raw 层对齐 |
| `BatchDownloader` | `BatchExecutor` + `TaskScheduler` | 下载器升级为批处理执行器 |
| `DownloadTask` | `ExtractTask` | 任务命名与操作动词对齐 |
| `CachedFetcher` | `ServedReader` + `MissingDataPolicy` | 缓存获取器升级为服务层读取器 |

---

## 十二、约束与禁止事项

### 12.1 数据层约束

| 层级 | 允许操作 | 禁止操作 |
|------|----------|----------|
| **L0 Raw** | Extract → Write, Read (replay), Delete (retention) | Normalize, Validate, Publish, 直接服务读取 |
| **L1 Standardized** | Normalize → Write, Read, Validate, Delete (retention) | Extract, Publish (未通过 Gate), 直接服务读取 |
| **L2 Served** | Publish → Write, Read, Rollback | Extract, Normalize, Validate, 修改已发布数据 |

### 12.2 命名禁止事项

1. **禁止**在代码中使用 `cache` 作为数据层名称（除非特指服务层缓存）
2. **禁止**混用 `fetch`/`read`（fetch=从源获取，read=从存储读取）
3. **禁止**在实体/字段命名中使用驼峰命名（统一 snake_case）
4. **禁止**使用 `update`、`modify` 描述发布操作（统一使用 `publish`）
5. **禁止**使用 `delete` 描述回滚操作（统一使用 `rollback`）

---

## 附录：术语索引

按字母顺序排列的术语索引，便于快速查阅：

| 术语 | 中文 | 章节 |
|------|------|------|
| Batch | 批次 | 三 |
| Checkpoint | 检查点 | 七 |
| Dataset | 数据集 | 二 |
| Endpoint | 端点 | 六 |
| Entity | 实体 | 二 |
| event_time | 事件时间 | 八 |
| Extract | 抽取 | 四 |
| Field | 字段 | 二 |
| ingest_time | 入库时间 | 八 |
| Interface | 接口 | 六 |
| Job | 作业 | 三 |
| L0 Raw Layer | 原始层 | 一 |
| L1 Standardized Layer | 标准化层 | 一 |
| L2 Served Layer | 服务层 | 一 |
| Manifest | 清单文件 | 七 |
| Normalize | 标准化 | 四 |
| Pipeline | 管道 | 三 |
| Publish | 发布 | 四 |
| Quality Gate | 质量门禁 | 五 |
| Quality Report | 质量报告 | 五 |
| Quality Rule | 质量规则 | 五 |
| Quarantine | 隔离区 | 五 |
| Release | 发布版本 | 七 |
| report_date | 报告日期 | 八 |
| Source | 数据源 | 六 |
| Table | 表 | 二 |
| Task | 任务 | 三 |
| trade_date | 交易日期 | 八 |
| Validate | 校验 | 四 |
| Version | 版本 | 七 |

---

> **维护说明**: 本术语表随架构演进持续更新。新增术语需在此注册，变更术语需更新对照表并标注变更日期。