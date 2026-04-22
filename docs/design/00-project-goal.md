# 项目目标定义

> 任务编号: `T0-001`
> 状态: 已收口
> 最后更新: 2026-04-22

## 1. 项目定位

`akshare-data-service` 当前更接近“Cache-First 金融数据访问层”，目标是升级为“严肃数据工程数据服务”。

目标形态不是继续扩展接口数量，而是建设一条稳定的数据资产链路：

```text
Source -> Ingestion -> L0 Raw -> L1 Standardized -> Quality Gate -> L2 Served -> Service
```

### 1.1 当前系统的核心问题

- 数据落地语义仍然偏缓存，不是数据资产。
- 字段标准化主要靠代码里的 rename，不是字段字典和实体 schema。
- 在线服务仍可能直接回源，服务稳定性受上游波动影响。
- 质量检查更像离线评分，不是发布前门禁。
- 数据缺少批次、版本、血缘、回放等治理能力。

### 1.2 目标定位

升级后的系统必须满足：

- `资产化`：所有服务数据来自明确的数据层，而不是临时 DataFrame。
- `可追溯`：每条标准数据都能追溯到原始批次、源接口、参数和规则版本。
- `可重放`：给定批次或时间范围，可以从 Raw 重建 Standardized 并重新发布。
- `可阻断`：质量不过关的数据不能进入 Served。
- `可服务`：在线服务默认只读 Served，不直接依赖源站实时成功。

## 2. 单一事实来源

后续所有设计文档遵循以下优先级，低层文档不得与高层契约冲突：

1. `00-project-goal.md`：系统目标与总原则
2. `01-architecture-rfc.md`：总体架构、边界、依赖方向
3. `30-standard-entities.md`：标准实体、主键、时间语义、系统字段
4. `50-quality-rule-spec.md`：质量 DSL 与门禁规则
5. 其他实施文档：目录结构、映射、迁移、执行计划

如果下位文档与上位文档冲突，以上位文档为准。

## 3. 统一分层口径

### 3.1 数据层

数据层只有三层，后续不再扩展为 `L1-L7`：

| 层级 | 名称 | 职责 | 是否对外服务 |
|------|------|------|--------------|
| `L0` | `Raw` | 原始落地，保留源字段和抓取审计 | 否 |
| `L1` | `Standardized` | 标准字段、类型、主键、质量校验前后的标准资产 | 否 |
| `L2` | `Served` | 通过发布门禁、供服务读取的稳定版本 | 是 |

### 3.2 模块层

模块层不是数据层，不使用 `Lx` 编号：

- `ingestion`：接入、调度、抓取、限流、熔断、审计
- `raw`：L0 的写入、读取、manifest、schema fingerprint
- `standardized`：L1 的标准化、schema、merge、writer、reader
- `quality`：规则执行、报告、门禁、隔离区
- `served`：L2 的发布、版本、回滚、reader
- `governance`：元数据、血缘、schema registry、owner、变更管理
- `service`：HTTP/CLI/SDK，只读 Served
- `common`：跨层共享的错误、配置、日志、基础类型

## 4. 核心边界

### 4.1 Service 边界

在线服务默认：

- 只读 `Served`
- 可以返回“未发布/缺数/旧版本”状态
- 可以异步触发补数请求
- 不直接调用上游数据源
- 不直接写 Raw、Standardized、Served

### 4.2 Standardized 边界

`Standardized` 是字段标准化和业务契约中心：

- 标准字段名来自字段字典
- 主键、分区、时间语义由实体 schema 定义
- 质量规则只引用标准字段名
- 服务文档只引用标准字段名

### 4.3 Raw 边界

`Raw` 保留原始源语义：

- 不做 rename
- 不使用业务日期作为物理分区主语义
- 以 `extract_date + batch_id` 组织数据
- 原始记录可回放，不直接提供服务

## 5. 首批范围

首批只做 3 个核心数据集，先打通完整链路：

- `market_quote_daily`
- `financial_indicator`
- `macro_indicator`

扩展数据集必须复用相同架构，不允许再额外发明一套流程。

## 6. 成功标准

### 6.1 项目级验收

- `100% 可追溯`：标准层与服务层记录都能回溯到 Raw 批次
- `100% 可重放`：首批 3 个数据集支持按批次重建
- `100% 门禁前置`：Served 只接收通过质量门禁的数据
- `0 条服务直连源站主路径`：正式服务读取主路径不回源
- `1 套字段契约`：实体 schema、字段字典、质量规则名称一致

### 6.2 六个统一验收口径

- `可追溯`
- `可重放`
- `可阻断`
- `可观测`
- `可维护`
- `可服务`

## 7. 非目标

当前阶段明确不做：

- 实时行情推送
- 交易执行
- 因子研究与回测平台
- 大规模新增 69 张表之外的数据覆盖
- 多语言 SDK
- SaaS 托管版

## 8. 参考文档

- [01-architecture-rfc.md](01-architecture-rfc.md)
- [10-target-repo-layout.md](10-target-repo-layout.md)
- [20-raw-spec.md](20-raw-spec.md)
- [30-standard-entities.md](30-standard-entities.md)
- [50-quality-rule-spec.md](50-quality-rule-spec.md)
