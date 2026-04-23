# 首批试点数据域范围说明

> 任务编号: `T0-005`
> 状态: 已定义
> 最后更新: 2026-04-23

## 1. 目标

本阶段只选择 3 个数据域做端到端试点，验证 `Raw -> Standardized -> Served` 全链路可追溯、可重放、可门禁发布。

## 2. 试点数据域

1. `market_quote_daily`
2. `financial_indicator`
3. `macro_indicator`

## 3. 入选原则

- 覆盖核心业务场景：行情、财务、宏观三类查询。
- 覆盖不同更新频率：交易日更新 + 财报更新 + 低频宏观更新。
- 覆盖不同字段复杂度：价格/成交量、财务口径、宏观统计口径。
- 可验证跨源映射：AkShare/Lixinger 字段差异可用于检验标准化规则。

## 4. 每个数据域的 MVP 范围

### 4.1 `market_quote_daily`

- 主键：`security_id + trade_date + adjust_type`
- 核心字段：`open/high/low/close/volume/turnover_amount`
- 最低质量门禁：主键唯一、主键非空、`high >= low`、价格非负、成交量非负
- 发布频率：交易日 T+0 盘后发布

### 4.2 `financial_indicator`

- 主键：`security_id + report_period + report_type`
- 核心字段：`roe/roa/gross_margin/net_profit_margin`
- 最低质量门禁：主键唯一、字段单位一致、报告期合法
- 发布频率：财报更新日批量发布

### 4.3 `macro_indicator`

- 主键：`indicator_code + period`
- 核心字段：`indicator_value/unit/frequency/publish_time`
- 最低质量门禁：时间合法、缺失率阈值、同指标频率一致
- 发布频率：按指标频率（周/月/季）发布

## 5. 非范围（当前阶段不做）

- 分钟级行情全覆盖
- 股东事件类复杂实体
- 高维度因子资产
- 全量 69 表迁移

## 6. 验收标准

- 三个数据域均可从 Raw 回放并重建 Standardized。
- 三个数据域均接入质量门禁并发布到 Served。
- 服务层默认仅读取 Served，不依赖实时回源成功。

## 7. 依赖关系

- 依赖 `T0-002` 架构 RFC 作为边界约束。
- 与 `T1-002 ~ T1-007` 并行推进实现层设计。
