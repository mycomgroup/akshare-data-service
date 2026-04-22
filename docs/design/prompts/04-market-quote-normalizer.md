# 任务 04：实现 `market_quote_daily` 标准化器

## 目标

打通首个核心标准数据集 `market_quote_daily` 的 `Raw -> Standardized` 转换。

## 必读文档

- `docs/design/20-raw-spec.md`
- `docs/design/30-standard-entities.md`
- `docs/design/50-quality-rule-spec.md`

## 任务范围

- 新建 `src/akshare_data/standardized/normalizer/base.py`
- 新建 `src/akshare_data/standardized/normalizer/market_quote_daily.py`
- 如需要，补充 `src/akshare_data/standardized/fields.py` 或 `symbols.py`

## 关键要求

- 输入来自 Raw，输出字段严格使用标准字段名
- 把旧字段映射到：`security_id`、`trade_date`、`open_price`、`high_price`、`low_price`、`close_price`、`volume`、`turnover_amount`、`adjust_type`
- 补齐系统字段：`batch_id`、`source_name`、`interface_name`、`ingest_time`、`normalize_version`、`schema_version`
- 不允许再输出 `symbol/date/close/amount`

## 非目标

- 不实现 Served 发布
- 不改 service 层查询接口

## 验收标准

- 标准化器能处理至少一个主数据源样例
- 生成字段与实体 schema 完全一致
