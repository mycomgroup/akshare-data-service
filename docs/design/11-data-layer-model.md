# 三层数据架构设计

> 任务编号: `T1-002`
> 状态: Draft-v1
> 最后更新: 2026-04-23

## 1. 架构目标

通过 `L0 Raw / L1 Standardized / L2 Served` 三层模型，建立从采集到服务的稳定数据资产链路。

## 2. 三层定义

| 层级 | 输入 | 输出 | 允许操作 | 禁止操作 |
|---|---|---|---|---|
| L0 Raw | 源接口返回 | 原始资产 + 审计信息 | 原样落地、去重 hash、记录 schema 指纹 | 业务字段重命名、对外服务 |
| L1 Standardized | L0 数据 | 标准实体表 | 字段映射、类型标准化、主键约束、单位统一 | 直接回源、绕过规则写服务层 |
| L2 Served | L1 合格批次 | 发布版本 | 版本冻结、读优化、服务消费 | 直接接受未门禁数据 |

## 3. 系统字段约束

- L0 必须具备：`batch_id/source_name/interface_name/request_time/ingest_time/raw_record_hash`。
- L1 必须具备：`normalize_version/schema_version/lineage_ref`。
- L2 必须具备：`release_version/published_at/quality_status`。

## 4. 数据流

```text
extract -> land_raw -> normalize -> validate -> publish -> serve
```

- `validate` 通过前，数据不得进入 L2。
- `publish` 必须显式写入发布元数据与版本清单。

## 5. 分层收益

- 可追溯：L2 任意记录可定位到 L0 批次。
- 可重放：按 `batch_id` 重建 L1/L2。
- 可阻断：质量失败自动阻断发布。
- 可维护：新增数据域仅扩展映射和实体，不改服务主路径。
