# 任务 05：实现 `financial_indicator` 与 `macro_indicator` 标准化器

## 目标

打通另外两个 P0 数据集的标准化能力。

## 必读文档

- `docs/design/30-standard-entities.md`
- `docs/design/50-quality-rule-spec.md`
- `docs/design/01-architecture-rfc.md`

## 任务范围

- 新建 `src/akshare_data/standardized/normalizer/financial_indicator.py`
- 新建 `src/akshare_data/standardized/normalizer/macro_indicator.py`
- 如需要，补充对应映射配置

## 关键要求

- `financial_indicator` 使用 `security_id/report_date/report_type`
- `macro_indicator` 使用 `indicator_code/observation_date`
- 比率字段统一带 `_pct` 或标准后缀
- 避免把 `date`、`symbol` 继续作为标准字段主名

## 验收标准

- 两个 normalizer 都能从 Raw 产生标准字段
- 字段命名和实体文档一致
- 为后续质量规则执行做好准备
