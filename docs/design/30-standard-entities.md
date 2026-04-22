# 标准实体清单

> 任务编号: `T4-001`
> 最后更新: 2026-04-22

## 1. 使用规则

本文档是标准实体与标准字段命名的事实来源。

后续以下内容都必须引用这里的字段名和实体名：

- `config/standards/entities/*.yaml`
- `config/quality/*.yaml`
- `service` 输出字段文档
- `lineage` 和 `metadata catalog`

禁止在新文档和新代码中重新发明别名，例如：

- `stock_daily` 替代 `market_quote_daily`
- `date` 替代 `trade_date`
- `close` 替代 `close_price`
- `amount` 替代 `turnover_amount`

## 2. 统一系统字段

所有 Standardized 与 Served 数据集统一使用以下系统字段，不再使用 `_batch_id` 这类下划线前缀版本。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `batch_id` | string | 来源批次 |
| `source_name` | string | 来源数据源 |
| `interface_name` | string | 来源接口 |
| `ingest_time` | timestamp | 进入系统时间 |
| `normalize_version` | string | 标准化规则版本 |
| `schema_version` | string | 实体 schema 版本 |
| `quality_status` | string | 质量状态 |
| `publish_time` | timestamp | 发布到 Served 的时间，可空 |
| `release_version` | string | 发布版本，可空 |

## 3. 标准实体概览

| 实体名 | 优先级 | 说明 |
|--------|--------|------|
| `market_quote_daily` | P0 | 日线行情 |
| `financial_indicator` | P0 | 财务指标 |
| `macro_indicator` | P0 | 宏观指标 |
| `security_master` | P1 | 证券主数据 |
| `market_quote_minute` | P1 | 分钟行情 |
| `financial_statement_item` | P1 | 财报明细项 |

## 4. P0 实体定义

### 4.1 `market_quote_daily`

#### 主键与分区

| 类型 | 字段 |
|------|------|
| 主键 | `security_id`, `trade_date`, `adjust_type` |
| 分区 | `trade_date` |

#### 时间字段

| 字段 | 语义 |
|------|------|
| `trade_date` | 交易日期 |
| `ingest_time` | 入库时间 |
| `publish_time` | 发布到 Served 的时间 |

#### 核心字段

| 字段名 | 类型 | 单位 | 必填 |
|--------|------|------|------|
| `security_id` | string | - | 是 |
| `exchange` | string | - | 是 |
| `adjust_type` | string | - | 是 |
| `trade_date` | date | - | 是 |
| `open_price` | double | CNY | 是 |
| `high_price` | double | CNY | 是 |
| `low_price` | double | CNY | 是 |
| `close_price` | double | CNY | 是 |
| `volume` | double | share | 是 |
| `turnover_amount` | double | CNY | 是 |
| `change_pct` | double | pct | 否 |
| `turnover_rate` | double | pct | 否 |

#### 命名备注

- 用 `security_id`，不再新建 `symbol` 和 `code` 两套主名；如需兼容，可在映射层处理。
- 用 `adjust_type`，不再使用 `adjust`、`adjust_flag` 混用。
- 用 `turnover_amount`，不再使用 `turnover`、`amount` 混用。

### 4.2 `financial_indicator`

#### 主键与分区

| 类型 | 字段 |
|------|------|
| 主键 | `security_id`, `report_date`, `report_type` |
| 分区 | `report_date` |

#### 时间字段

| 字段 | 语义 |
|------|------|
| `report_date` | 报告期截止日 |
| `publish_date` | 公告发布日期 |
| `ingest_time` | 入库时间 |

#### 核心字段

| 字段名 | 类型 | 单位 | 必填 |
|--------|------|------|------|
| `security_id` | string | - | 是 |
| `report_date` | date | - | 是 |
| `report_type` | string | - | 是 |
| `publish_date` | date | - | 否 |
| `currency` | string | - | 否 |
| `pe_ratio_ttm` | double | ratio | 否 |
| `pb_ratio` | double | ratio | 否 |
| `ps_ratio_ttm` | double | ratio | 否 |
| `roe_pct` | double | pct | 否 |
| `roa_pct` | double | pct | 否 |
| `net_profit` | double | CNY | 否 |
| `revenue` | double | CNY | 否 |
| `total_assets` | double | CNY | 否 |
| `total_equity` | double | CNY | 否 |
| `debt_ratio_pct` | double | pct | 否 |
| `gross_margin_pct` | double | pct | 否 |
| `net_margin_pct` | double | pct | 否 |

### 4.3 `macro_indicator`

#### 主键与分区

| 类型 | 字段 |
|------|------|
| 主键 | `indicator_code`, `observation_date` |
| 分区 | `indicator_code`, `observation_date` |

#### 时间字段

| 字段 | 语义 |
|------|------|
| `observation_date` | 统计观测期 |
| `publish_date` | 官方发布时间 |
| `ingest_time` | 入库时间 |

#### 核心字段

| 字段名 | 类型 | 单位 | 必填 |
|--------|------|------|------|
| `indicator_code` | string | - | 是 |
| `indicator_name` | string | - | 是 |
| `frequency` | string | - | 是 |
| `region` | string | - | 否 |
| `observation_date` | date | - | 是 |
| `publish_date` | date | - | 否 |
| `value` | double | by indicator | 是 |
| `value_yoy_pct` | double | pct | 否 |
| `value_mom_pct` | double | pct | 否 |
| `unit` | string | - | 否 |
| `source_org` | string | - | 否 |

## 5. 质量规则引用约束

质量 DSL 中必须使用本文档字段名。

例如：

- 正确：`close_price`, `trade_date`, `turnover_amount`
- 错误：`close`, `date`, `amount`

## 6. 历史字段别名映射

| 历史名字 | 标准名字 |
|----------|----------|
| `symbol` | `security_id` |
| `date` | `trade_date` 或 `observation_date` |
| `adjust` / `adjust_flag` | `adjust_type` |
| `amount` / `turnover` | `turnover_amount` |
| `pe` | `pe_ratio_ttm` |
| `roe` | `roe_pct` |

## 7. 后续要求

- 字段字典必须扩展本文档中的每一个标准字段
- 质量规则必须按本文档字段名重写
- 服务文档必须按本文档字段名输出
