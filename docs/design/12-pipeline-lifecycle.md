# 任务流转架构（Pipeline Lifecycle）

> 任务编号: `T1-003`
> 状态: Draft-v1
> 最后更新: 2026-04-23

## 1. 生命周期总览

```text
plan -> schedule -> extract -> land_raw -> normalize -> validate -> publish -> serve
```

## 2. 阶段说明

1. `plan`：根据数据域、日历、分区生成待执行任务。
2. `schedule`：分配优先级并发执行窗口。
3. `extract`：调用源接口，记录请求参数与响应摘要。
4. `land_raw`：原始数据写入 L0，补齐系统字段。
5. `normalize`：按实体 schema 与映射规则生成 L1。
6. `validate`：执行质量规则、产出报告与评分。
7. `publish`：质量通过后生成 `release_version` 并发布到 L2。
8. `serve`：服务层读取 L2 稳定版本。

## 3. 状态机映射

- `pending`：任务创建待执行
- `running`：执行中
- `partial`：部分分区成功，需补数
- `failed`：执行失败
- `retrying`：重试中
- `succeeded`：任务成功（不等于已发布）
- `published`：质量通过并已发布

## 4. 幂等与回放

- 幂等键：`source + interface + window + params + extract_version`
- 回放入口：指定 `batch_id/date_range/partition` 重建
- 规则：重跑不产生重复记录，不覆盖非目标发布版本

## 5. 产物清单

- 任务日志（执行耗时、错误信息）
- 抓取审计（请求参数、行数、schema 指纹）
- 质量报告（规则结果、阻断原因）
- 发布清单（release_version、输入批次）
