# 并行执行提示词

本目录包含 10 个可并行执行的提示词文件。每个提示词对应一个明确任务，默认给独立执行代理使用。

## 使用规则

- 每个代理只处理一个提示词文件
- 所有代理都必须先阅读以下文档：
  - `docs/design/00-project-goal.md`
  - `docs/design/01-architecture-rfc.md`
  - `docs/design/10-target-repo-layout.md`
  - `docs/design/30-standard-entities.md`
  - `docs/design/50-quality-rule-spec.md`
- 所有代理都必须遵守：
  - Service 默认只读 Served
  - Dataset 只使用标准名字
  - 质量规则只使用标准字段名
  - Raw 分区使用 `extract_date + batch_id`
- 如果任务之间发生文件冲突，优先保证架构契约，不为兼容旧实现继续扩散旧命名

## 提示词列表

1. `01-ingestion-task-model.md`
2. `02-raw-writer-manifest.md`
3. `03-standard-entity-config.md`
4. `04-market-quote-normalizer.md`
5. `05-financial-and-macro-normalizer.md`
6. `06-quality-engine-and-gate.md`
7. `07-served-publisher-reader.md`
8. `08-service-read-only-refactor.md`
9. `09-governance-catalog-lineage.md`
10. `10-tests-and-regression-guard.md`
