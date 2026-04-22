# 任务 06：实现质量引擎与门禁

## 目标

按新 DSL 落地质量执行与门禁，阻断不合格数据发布。

## 必读文档

- `docs/design/50-quality-rule-spec.md`
- `docs/design/30-standard-entities.md`
- `docs/design/01-architecture-rfc.md`

## 任务范围

- 新建 `src/akshare_data/quality/engine.py`
- 新建 `src/akshare_data/quality/gate.py`
- 新建 `src/akshare_data/quality/report.py`
- 新建 `src/akshare_data/quality/quarantine.py`
- 新建 `config/quality/market_quote_daily.yaml`
- 新建 `config/quality/financial_indicator.yaml`
- 新建 `config/quality/macro_indicator.yaml`

## 关键要求

- 规则文件按标准 dataset 命名
- 规则字段名必须和标准实体一致
- Raw 只做技术规则
- Standardized 执行业务规则
- 门禁输出可供 Served 发布前直接判断

## 验收标准

- 任意 `error + block` 失败时可以阻断发布
- 可以产出结构化质量结果和隔离记录
