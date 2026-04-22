# 任务 10：补齐测试与回归保护

## 目标

为新架构关键链路建立最低限度但有效的回归保护。

## 必读文档

- `docs/design/20-raw-spec.md`
- `docs/design/30-standard-entities.md`
- `docs/design/50-quality-rule-spec.md`
- `docs/design/01-architecture-rfc.md`

## 任务范围

- 新建或补充 `tests/contract/`
- 新建或补充 `tests/replay/`
- 新建或补充 `tests/served/`
- 新建或补充 `tests/integration/`

## 关键要求

- 至少覆盖：实体 schema 契约、Raw manifest、quality gate、Served 发布、Service 只读 Served
- 使用首批 3 个数据集的样例数据
- 测试命名和字段名必须与标准实体一致

## 验收标准

- 关键契约漂移时测试会直接失败
- 可以验证 service 主路径不直接回源
