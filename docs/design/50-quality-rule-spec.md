# 质量规则 DSL 规范

> 任务编号: `T6-001`
> 最后更新: 2026-04-22

## 1. 设计原则

- 规则引用 `标准实体字段`，不引用源字段别名
- 规则绑定 `dataset/entity`，不绑定历史 cache table 名
- Raw 规则只做技术质量
- Standardized/Served 规则做业务质量和发布门禁
- 门禁结果必须能阻断发布

## 2. 绑定对象

质量配置文件按标准数据集命名：

```text
config/quality/
├── market_quote_daily.yaml
├── financial_indicator.yaml
└── macro_indicator.yaml
```

不再新建：

- `stock_daily.yaml`
- `finance_indicator.yaml`
- 任何与标准实体名不一致的配置文件

## 3. 层级规则边界

### 3.1 Raw

Raw 只允许技术规则：

- `system_fields_complete`
- `request_params_parseable`
- `schema_fingerprint_valid`
- `request_before_ingest`
- `record_count_min`

Raw 不做：

- 主键唯一
- 行情高低价关系
- 财务比率口径一致性

### 3.2 Standardized

Standardized 执行业务规则：

- `non_null`
- `unique_key`
- `range`
- `enum`
- `continuity`
- `freshness`
- `business_rule`
- `cross_source_diff`

### 3.3 Served

Served 不重新定义业务真相，只做：

- 发布门禁
- 版本完整性
- manifest 完整性
- 发布范围一致性

## 4. DSL 通用结构

```yaml
version: '1.0'
dataset: market_quote_daily
entity: market_quote_daily
schema_version: v1
rules:
  - rule_id: mq_daily_pk_unique
    layer: standardized
    type: unique_key
    severity: error
    gate_action: block
    fields: [security_id, trade_date, adjust_type]
    description: 主键必须唯一
```

字段说明：

- `dataset`：标准数据集名
- `entity`：标准实体名，通常与 dataset 一致
- `layer`：`raw` / `standardized` / `served`
- `type`：规则类型
- `severity`：`error` / `warning` / `info`
- `gate_action`：`block` / `alert` / `ignore`

## 5. 规则类型

| 类型 | 说明 | 适用层 |
|------|------|--------|
| `system_fields_complete` | Raw 系统字段完整 | raw |
| `schema_fingerprint_valid` | Raw schema 指纹有效 | raw |
| `request_before_ingest` | `request_time <= ingest_time` | raw |
| `record_count_min` | 最低记录数 | raw |
| `non_null` | 必填字段非空 | standardized |
| `unique_key` | 业务主键唯一 | standardized |
| `range` | 数值范围 | standardized |
| `enum` | 枚举约束 | standardized |
| `continuity` | 时间连续性 | standardized |
| `freshness` | 数据新鲜度 | standardized/served |
| `business_rule` | 业务表达式 | standardized |
| `cross_source_diff` | 跨源偏差 | standardized |
| `release_manifest_complete` | 发布 manifest 完整 | served |

## 6. 标准字段引用示例

### 6.1 `market_quote_daily`

```yaml
version: '1.0'
dataset: market_quote_daily
entity: market_quote_daily
schema_version: v1
rules:
  - rule_id: mq_daily_pk_unique
    layer: standardized
    type: unique_key
    severity: error
    gate_action: block
    fields: [security_id, trade_date, adjust_type]

  - rule_id: mq_daily_price_positive
    layer: standardized
    type: range
    severity: error
    gate_action: block
    field: close_price
    min: 0

  - rule_id: mq_daily_high_ge_low
    layer: standardized
    type: business_rule
    severity: error
    gate_action: block
    expression: high_price >= low_price

  - rule_id: mq_daily_turnover_non_negative
    layer: standardized
    type: range
    severity: error
    gate_action: block
    field: turnover_amount
    min: 0
```

### 6.2 `financial_indicator`

```yaml
version: '1.0'
dataset: financial_indicator
entity: financial_indicator
schema_version: v1
rules:
  - rule_id: fin_indicator_pk_unique
    layer: standardized
    type: unique_key
    severity: error
    gate_action: block
    fields: [security_id, report_date, report_type]

  - rule_id: fin_indicator_roe_range
    layer: standardized
    type: range
    severity: warning
    gate_action: alert
    field: roe_pct
    min: -100
    max: 100

  - rule_id: fin_indicator_currency_enum
    layer: standardized
    type: enum
    severity: warning
    gate_action: alert
    field: currency
    values: [CNY, USD, HKD]
```

### 6.3 `macro_indicator`

```yaml
version: '1.0'
dataset: macro_indicator
entity: macro_indicator
schema_version: v1
rules:
  - rule_id: macro_pk_unique
    layer: standardized
    type: unique_key
    severity: error
    gate_action: block
    fields: [indicator_code, observation_date]

  - rule_id: macro_value_not_null
    layer: standardized
    type: non_null
    severity: error
    gate_action: block
    fields: [value]

  - rule_id: macro_frequency_enum
    layer: standardized
    type: enum
    severity: error
    gate_action: block
    field: frequency
    values: [D, W, M, Q, Y]
```

## 7. 门禁策略

### 7.1 全局规则

- 任意 `error + block` 失败时，不得发布到 Served
- `warning + alert` 可发布，但必须输出告警
- `info + ignore` 仅记录

### 7.2 发布前最小检查集

发布到 Served 前至少检查：

- Standardized 主键唯一
- Standardized 必填字段非空
- Standardized 关键业务规则通过
- Release manifest 完整

## 8. 质量结果结构

```yaml
result:
  dataset: market_quote_daily
  batch_id: '20260422_001'
  layer: standardized
  gate_passed: false
  failed_rules:
    - mq_daily_pk_unique
  warnings:
    - mq_daily_freshness
```

## 9. 与实体 schema 的关系

质量 DSL 不自行定义主键与字段主名，统一继承自：

- `30-standard-entities.md`
- `config/standards/entities/*.yaml`

如果字段名和实体 schema 不一致，视为文档错误或配置错误。

## 10. 验收标准

- 所有质量配置文件按标准数据集名命名
- 首批 3 个数据集的规则字段名与实体 schema 完全一致
- Raw 规则与 Standardized 规则严格分层
- 发布门禁能直接作为 Served 发布前置条件
