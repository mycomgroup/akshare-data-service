# 设计文档

本目录存放项目重构后的核心设计文档。当前以“严肃数据工程数据服务”为目标，优先建设统一的数据契约、分层架构和并行实施任务。

## 阅读顺序

建议按以下顺序阅读，越靠前越接近事实来源：

1. [00-project-goal.md](00-project-goal.md) - 项目目标、边界、单一事实来源
2. [01-architecture-rfc.md](01-architecture-rfc.md) - 总体架构决策与依赖规则
3. [10-target-repo-layout.md](10-target-repo-layout.md) - 目标目录与模块边界
4. [20-raw-spec.md](20-raw-spec.md) - Raw 层规范
5. [30-standard-entities.md](30-standard-entities.md) - 标准实体与字段契约
6. [50-quality-rule-spec.md](50-quality-rule-spec.md) - 质量 DSL 与门禁
7. [05-current-to-target-mapping.md](05-current-to-target-mapping.md) - 旧模块到新架构的迁移映射
8. [03-change-freeze.md](03-change-freeze.md) - 重构期间变更冻结规则

## 当前有效文档

| 文档 | 用途 | 状态 |
|------|------|------|
| [00-project-goal.md](00-project-goal.md) | 定义项目目标和北极星 | 有效 |
| [01-architecture-rfc.md](01-architecture-rfc.md) | 定义架构决策和边界 | 有效 |
| [03-change-freeze.md](03-change-freeze.md) | 约束重构期变更 | 有效 |
| [05-current-to-target-mapping.md](05-current-to-target-mapping.md) | 指导模块迁移 | 有效 |
| [10-target-repo-layout.md](10-target-repo-layout.md) | 指导目录重构 | 有效 |
| [20-raw-spec.md](20-raw-spec.md) | 指导 Raw 实现 | 有效 |
| [30-standard-entities.md](30-standard-entities.md) | 指导字段与实体实现 | 有效 |
| [50-quality-rule-spec.md](50-quality-rule-spec.md) | 指导质量规则和发布门禁 | 有效 |

## Prompt 文件

并行推进任务的提示词文件放在：

- [prompts/README.md](prompts/README.md)

每个提示词对应一个独立任务，默认面向并行执行，但都必须遵守：

- 不破坏外部兼容入口
- 不引入第二套命名体系
- 不让 service 重新直接回源
- 不跳过 Raw/Standardized/Served 主链路

## 历史文档

以下文档保留用于参考，但不作为当前重构事实来源：

- `DATA_SOURCE_REDESIGN.md`
- `DESIGN_non_akshare_sources.md`
- `DEVELOPMENT_PLAN.md`
- `MIGRATION_PLAN.md`
- `TESTING_PLAN.md`
- `implementation_plan.md`
- `11-cache-policy-config.md`
- `11-config-redesign.md`

使用这些历史文档时，若与当前有效文档冲突，以当前有效文档为准。
