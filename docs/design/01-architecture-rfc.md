# 架构 RFC

> 文档编号: `RFC-001`
> 状态: Draft
> 最后更新: 2026-04-22

## 1. 背景

当前项目同时承担 SDK、缓存、抓取、落地、服务、离线工具等多种职责，导致：

- 生产链路和服务链路耦合
- 数据层与缓存层语义混淆
- 字段标准化与质量治理缺少中心契约
- 模块命名和职责边界持续漂移

## 2. 决策

本 RFC 做出以下架构决策：

1. 数据层固定为 `L0 Raw / L1 Standardized / L2 Served`
2. 模块层不再使用 `Lx` 编号
3. 在线服务默认只读 `Served`
4. 源接入统一进入 `ingestion`，不得由 `service` 直接持有源适配器
5. 标准实体 schema 是标准字段、质量规则、服务文档的唯一事实源
6. Raw 的物理分区以抽取语义组织，不以业务日期组织
7. 发布必须经过质量门禁，Served 只保留发布版本

## 3. 目标架构

```text
Sources
  -> ingestion
  -> raw (L0)
  -> standardized (L1)
  -> quality gate
  -> served (L2)
  -> service
```

## 4. 模块职责

| 模块 | 责任 | 禁止事项 |
|------|------|----------|
| `ingestion` | 抓取、调度、限流、熔断、批次、审计 | 不直接对外服务 |
| `raw` | 原始落地、manifest、replay reader | 不做字段 rename |
| `standardized` | 字段映射、类型转换、schema 校验、merge | 不直接回源 |
| `quality` | 规则执行、报告、门禁、隔离区 | 不直接修改数据 |
| `served` | 发布版本、reader、rollback | 不直接接触上游源站 |
| `governance` | 元数据、schema registry、lineage、owner | 不直接持有业务数据 |
| `service` | API/CLI/SDK，对外查询与状态反馈 | 不直接读取 Raw 和源站 |
| `common` | 配置、错误、日志、基础类型 | 不包含业务编排 |

## 5. 依赖规则

允许的高层依赖：

- `service -> served, governance`
- `served -> standardized, governance`
- `standardized -> raw, governance`
- `quality -> standardized, raw, governance`
- `raw -> common`
- `ingestion -> common, governance`

禁止：

- `service -> ingestion`
- `service -> source adapters`
- `served -> ingestion`
- `standardized -> service`
- `quality -> service`

## 6. 数据集命名决策

数据集统一使用业务标准名，以下命名为 canonical：

- `market_quote_daily`
- `financial_indicator`
- `macro_indicator`
- `security_master`
- `financial_statement_item`

以下名称只允许作为历史映射出现，不再作为新配置名或新文件名：

- `stock_daily`
- `quote_daily`
- `indicator`
- `finance_indicator`

## 7. 时间语义决策

- `extract_date`：任务抽取日期，用于 Raw 物理分区
- `batch_id`：批次标识，用于追溯与重放
- `trade_date / report_date / observation_date`：业务时间，用于 Standardized/Served 分区
- `ingest_time`：系统写入时间
- `publish_time`：发布到 Served 的时间

## 8. 发布决策

一次标准链路的发布过程为：

```text
extract -> land raw -> normalize -> validate -> gate -> publish
```

门禁失败时：

- 阻断发布
- 生成质量报告
- 写入 quarantine
- 保留 Raw 与 Standardized 证据

## 9. 迁移策略

- 保留现有 `api.py` 作为 facade，内部逐步切换到新模块
- 保留 `core/` 作为兼容壳，逐步沉淀到 `common/`、`governance/`、`standardized/`
- 旧缓存概念逐步退化为加速层，不再承载数据资产语义

## 10. 验收条件

- 首批 3 个数据集跑通全链路
- Service 主读取路径只读 Served
- Quality 规则与实体 schema 字段完全一致
- Raw 支持批次重放
- Manifest、lineage、release version 可追踪
