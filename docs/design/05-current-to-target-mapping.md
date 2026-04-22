# 现有模块到目标架构的映射关系

> 任务编号: `T0-006`
> 最后更新: 2026-04-22

## 1. 使用说明

本文档用于回答两个问题：

- 当前代码各模块在目标架构里应该归属哪里
- 哪些模块保留 facade，哪些模块迁移，哪些模块只作为兼容层

本文档不再把模块层写成 `L1-L7`。`L0/L1/L2` 只保留给数据层。

## 2. 目标架构视图

### 2.1 数据层

| 数据层 | 含义 |
|--------|------|
| `L0 Raw` | 原始落地与审计 |
| `L1 Standardized` | 标准实体与标准字段 |
| `L2 Served` | 已发布稳定数据 |

### 2.2 功能模块

- `ingestion`
- `raw`
- `standardized`
- `quality`
- `served`
- `governance`
- `service`
- `common`

## 3. 当前模块映射总览

| 当前模块 | 当前职责 | 目标归属 | 处理方式 |
|----------|----------|----------|----------|
| `api.py` | DataService、命名空间 API、缓存编排 | `service` facade + 部分 `served` 适配 | 拆分并保留 facade |
| `sources/` | 源适配器、多源路由、限流、熔断 | `ingestion` | 迁移 |
| `store/` | 缓存、Parquet、DuckDB、策略 | `raw` + `served` + 部分 `standardized` | 拆分 |
| `offline/` | 下载、探测、分析、CLI、调度 | `ingestion` + `quality` + `governance` + `service/cli` | 拆分 |
| `core/` | 配置、错误、schema、字段映射、normalize | `common` + `governance` + `standardized` | 拆分并保留兼容壳 |

## 4. 模块级映射

### 4.1 `api.py`

| 当前能力 | 目标模块 | 说明 |
|----------|----------|------|
| `DataService` facade | `service` | 对外兼容入口 |
| 命名空间 API | `service` | 面向 Served 的查询代理 |
| Cache-First 编排 | `served` | 只做稳定层读取与版本选择 |
| 直接源调用逻辑 | `ingestion` | 从服务主路径移出 |

结论：`api.py` 保留，但只能是薄 facade，不再承载抓取主逻辑。

### 4.2 `sources/`

| 当前文件 | 目标模块 | 处理 |
|----------|----------|------|
| `router.py` | `ingestion/router.py` | 保留与重构 |
| `akshare_source.py` | `ingestion/adapters/akshare.py` | 迁移 |
| `lixinger_source.py` | `ingestion/adapters/lixinger.py` | 迁移 |
| `tushare_source.py` | `ingestion/adapters/tushare.py` | 可选迁移 |
| `mock.py` | `ingestion/adapters/mock.py` | 保留 |

结论：源适配器属于 `ingestion`，不属于 `service`。

### 4.3 `store/`

| 当前文件 | 目标模块 | 说明 |
|----------|----------|------|
| `parquet.py` | `raw` + `standardized` + `served` 公共 writer 能力 | 按层拆开 |
| `manager.py` | `served` | 不再叫 CacheManager 中心资产层 |
| `fetcher.py` | `served` | 只负责已发布数据读取策略 |
| `duckdb.py` | `raw` 或 `standardized` 辅读取能力 | 不是服务层主语义 |
| `aggregator.py` | `standardized` | 属于标准层加工 |
| `validator.py` | `quality` | 进入规则体系 |
| `strategies/*` | `served` | 仅保留读取/补数策略语义 |

### 4.4 `offline/`

| 当前子模块 | 目标模块 | 说明 |
|------------|----------|------|
| `downloader/` | `ingestion` | 统一任务执行与批次编排 |
| `scheduler/` | `ingestion` 或 `service/cli` 驱动 | 调度属于控制面，不属于在线查询 |
| `prober/` | `governance` | 监测与发现 |
| `analyzer/cache_analysis/` | `quality` | 质量分析 |
| `registry/` | `governance` | 注册与元数据 |
| `scanner/` | `governance` | 接口发现 |
| `cli/` | `service/cli` | 用户入口 |

### 4.5 `core/`

| 当前文件 | 目标模块 | 说明 |
|----------|----------|------|
| `errors.py` | `common/errors.py` | 公共能力 |
| `config*.py` | `common/config.py` 等 | 公共能力 |
| `schema.py` | `governance` | 从缓存注册迁移到数据契约注册 |
| `fields.py` | `standardized` | 标准字段映射 |
| `normalize.py` | `standardized` | 类型与格式标准化 |
| `symbols.py` | `standardized` | 证券代码归一 |
| `base.py` | `ingestion/base.py` + 部分 mixin 清理 | 仅保留源接口定义 |

## 5. 必须保留的兼容 facade

以下外部入口在迁移中保持稳定：

- `from akshare_data import DataService`
- `src/akshare_data/api.py`
- 部分 `core/*` 导入路径
- 现有 CLI 主入口

兼容层职责：

- 仅转发
- 发出 deprecation 提示
- 不承载新逻辑

## 6. 迁移原则

- 先建立新目录和新契约，再迁移实现
- 先迁移低耦合模块，再拆 `api.py` 和 `store/manager.py`
- 先做首批 3 个数据集，不做全量平移
- 任何迁移都不能引入新的双命名体系

## 7. 风险点

- `api.py` 对下游兼容性影响最大
- `core/schema.py` 的旧缓存表定义与新标准实体之间有语义断层
- `store/manager.py` 拆分时最容易把“缓存语义”和“数据层语义”继续混在一起
- `offline/` 工具较多，必须区分控制面工具与数据层核心逻辑
