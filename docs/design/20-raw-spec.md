# Raw 数据集规范

> 任务编号: `T3-001`
> 状态: 已收口
> 最后更新: 2026-04-22

## 1. 目标

Raw 是 `L0` 原始层，负责保留源站返回结果和抓取审计信息，支持：

- 回放
- 审计
- schema 漂移检测
- 批次重建

Raw 的核心原则：

- 不做字段 rename
- 不按业务日期定义物理主分区
- 不直接对外服务
- 一次抓取对应一个可追溯批次

## 2. 关键决策

### 2.1 Raw 分区语义

Raw 不使用 `trade_date`、`report_date`、`observation_date` 作为主物理分区。

Raw 的标准物理路径：

```text
data/raw/<domain>/<dataset>/extract_date=<YYYY-MM-DD>/batch_id=<batch_id>/
```

其中：

- `extract_date`：任务执行或计划抽取日期
- `batch_id`：本次抓取批次号

这样设计的原因：

- 一次接口调用可能返回一个时间区间的数据
- 一次财务接口可能返回多期数据
- 一次全量快照不一定对应单一业务日期
- Raw 需要按“抓取行为”组织，而不是按“业务事件”组织

业务时间只保存在记录字段中，不作为 Raw 主分区语义。

### 2.2 Dataset 命名

Raw 路径中的 `<dataset>` 使用标准数据集名，而不是历史别名。

正确示例：

- `market_quote_daily`
- `financial_indicator`
- `macro_indicator`

不再新增以下命名：

- `quote_daily`
- `stock_daily`
- `indicator`

## 3. 路径规范

### 3.1 标准目录

```text
data/raw/
├── cn/
│   ├── market_quote_daily/
│   │   └── extract_date=2026-04-22/
│   │       └── batch_id=20260422_001/
│   │           ├── part-000.parquet
│   │           ├── _manifest.json
│   │           └── _schema.json
│   ├── financial_indicator/
│   └── macro_indicator/
└── system/
```

### 3.2 业务时间在 Raw 中的表达

- 行情记录保留 `日期` 或源字段原名
- 财务记录保留 `报告期` 或源字段原名
- 宏观记录保留源端返回的时间列
- 是否再抽取出 `source_event_time` 可选，但不能替代源原字段

## 4. 系统字段

Raw 系统字段使用无前缀命名，后续 Standardized 和 Served 延续同一风格。

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `batch_id` | string | 是 | 批次标识 |
| `source_name` | string | 是 | 源名称 |
| `interface_name` | string | 是 | 源接口名 |
| `request_params_json` | string | 是 | 请求参数 |
| `request_time` | timestamp | 是 | 发起请求时间 |
| `ingest_time` | timestamp | 是 | 落入 Raw 时间 |
| `extract_date` | date | 是 | 抽取日期 |
| `extract_version` | string | 是 | 抓取版本 |
| `source_schema_fingerprint` | string | 是 | 源 schema 指纹 |
| `raw_record_hash` | string | 是 | 原始记录 hash |

说明：

- `ingest_time` 是系统时间，不等于业务时间
- `extract_date` 是物理分区列，不等于事件时间
- `raw_record_hash` 仅基于业务内容计算，不含系统字段

## 5. 存储模式

### 5.1 默认模式

Raw 默认使用“展开模式 + 保留原字段名”。

原因：

- 便于排查 schema 漂移
- 便于抽样分析
- 便于回放前验证

### 5.2 可选 payload 模式

仅在以下场景允许使用单列 payload：

- 新接入且 schema 明显不稳定
- 半结构化返回难以稳定展开
- 仅做原始归档暂不进入首批标准化

如果使用 payload 模式，仍必须补齐全部系统字段。

## 6. Manifest 规范

每个批次目录必须包含 `_manifest.json`，最少包含：

```json
{
  "manifest_version": "1.0",
  "dataset": "market_quote_daily",
  "domain": "cn",
  "batch_id": "20260422_001",
  "extract_date": "2026-04-22",
  "source_name": "akshare",
  "interface_name": "stock_zh_a_hist",
  "request_params": {"symbol": "600519", "start_date": "2026-04-01", "end_date": "2026-04-22"},
  "record_count": 15,
  "file_count": 1,
  "schema_fingerprint": "sha256:...",
  "extract_version": "v1.0",
  "status": "success"
}
```

Manifest 记录的是“这次抽取行为”，不是“某个业务日期快照”。

## 7. `_schema.json` 规范

`_schema.json` 记录该批次 Raw 文件的实际列结构，用于：

- schema 漂移检测
- 回放兼容性判断
- 调试与审计

字段变更策略：

- 新增字段：允许
- 删除字段：允许，但产生告警
- 重命名字段：视为删除 + 新增
- 类型剧烈变化：允许落 Raw，但产生高优先级告警

## 8. 重放语义

Raw 的 replay 是“按抽取批次重放”，不是“按业务日期回放”。

### 8.1 支持的重放模式

- 按 `batch_id` 重放
- 按 `extract_date` 范围重放
- 按 `dataset + source_name + interface_name` 重放

### 8.2 不建议的重放模式

- 仅按 `trade_date` 在 Raw 中直接定位
- 仅按 `report_date` 在 Raw 中直接定位

这些属于 Standardized/Served 的读取语义，不是 Raw 的主语义。

## 9. Raw 质量边界

Raw 只做技术质量，不做业务质量。

允许的 Raw 规则：

- 文件存在
- schema 可解析
- 系统字段完整
- 参数可反序列化
- `request_time <= ingest_time`
- `raw_record_hash` 可计算

不在 Raw 强制的内容：

- 主键唯一
- 业务字段范围
- 行情高低价关系
- 财务口径一致性

## 10. 与 Standardized 的接口

进入 Standardized 前，必须由 normalizer 明确：

- 使用哪份实体 schema
- 使用哪版字段映射
- 使用哪版 normalize 规则
- 是否允许该 source schema fingerprint

## 11. 验收标准

- Raw 路径不再使用业务日期作为统一分区主语义
- 首批 3 个数据集都能按批次落 Raw
- 每个批次都有 manifest 和 schema snapshot
- 给定 `batch_id` 可读回原始记录并进入标准化流程
