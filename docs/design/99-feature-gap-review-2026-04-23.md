# Feature Gap Review (2026-04-23)

基于 `docs/all.md` 的 `Task Backlog V1` 对当前仓库进行快速盘点，目标是识别「仍需实现」的核心功能。

## 盘点方法

- 逐条读取 `Task Backlog V1` 中 106 个任务。
- 对每个任务的 `output` 路径执行存在性检查（仅做“文件/目录是否存在”的静态核对）。
- 统计为三类：
  - `exists`：输出文件/目录已存在（不代表功能 100% 完成，只代表已有落地点）。
  - `missing`：输出路径不存在，属于明确缺口。
  - `unknown`：输出不是单一路径（如“重构某目录/模板/代码目录”），需人工进一步验证。

## 总体结论

- 总任务数：106
- 已有落地点（exists）：66
- 明确缺口（missing）：17
- 需人工核验（unknown）：23

> 结论：项目已完成大量基础骨架，但在「架构设计文档补齐、服务层发布规范、测试体系收口」上仍有明显缺口。

## 仍需实现（missing）

### Phase 0

1. `T0-005` 选定首批试点数据域  
   - 期望输出：`docs/design/04-pilot-scope.md`
2. `T0-008` 制定 90 天里程碑  
   - 期望输出：`docs/design/07-roadmap-90d.md`

### Phase 1

3. `T1-002` 设计三层数据架构  
   - 期望输出：`docs/design/11-data-layer-model.md`
4. `T1-003` 设计任务流转架构  
   - 期望输出：`docs/design/12-pipeline-lifecycle.md`
5. `T1-004` 设计失败处理矩阵  
   - 期望输出：`docs/design/13-failure-matrix.md`
6. `T1-005` 设计重放与回补策略  
   - 期望输出：`docs/design/14-replay-backfill.md`
7. `T1-006` 设计版本模型  
   - 期望输出：`docs/design/15-versioning-model.md`
8. `T1-007` 设计模块迁移计划  
   - 期望输出：`docs/design/16-migration-plan-v2.md`

### Phase 2

9. `T2-004` 统一执行器接口  
   - 期望输出：`src/akshare_data/ingestion/executor/base.py`

### Phase 4 / 6 / 7 / 8 / 9 / 10

10. `T4-002` 定义标准命名规范  
    - 期望输出：`docs/design/31-field-naming-standard.md`
11. `T6-010` 移除现有硬编码评分（文档落点）  
    - 期望输出：`docs/design/60-served-layer-spec.md`
12. `T7-001` 设计 served 层规范  
    - 期望输出：`docs/design/60-served-layer-spec.md`
13. `T7-002` 定义发布版本模型  
    - 期望输出：`docs/design/61-release-version-model.md`
14. `T8-001` 设计新服务职责  
    - 期望输出：`docs/design/70-service-boundary.md`
15. `T8-007` 增加服务错误语义分层（文档落点）  
    - 期望输出：`docs/design/80-metadata-catalog.md`
16. `T9-001` 设计 metadata catalog  
    - 期望输出：`docs/design/80-metadata-catalog.md`
17. `T10-001` 重写测试策略文档  
    - 期望输出：`docs/design/90-test-strategy-v2.md`
18. `T10-002` 增加字段映射测试  
    - 期望输出：`tests/contract/test_field_mappings.py`
19. `T10-005` 增加质量规则测试  
    - 期望输出：`tests/quality/`

## 优先级建议（接下来 2~4 周）

按“对主链路影响程度”建议优先顺序：

1. **先补 Phase 1 设计文档 6 件套（T1-002~T1-007）**
   - 不补齐会导致后续开发继续“有代码、无契约”。
2. **再补 T2-004 统一执行器接口**
   - 这是打通在线/离线/补数执行抽象的关键点。
3. **再补 served + release 规范（T7-001、T7-002）**
   - 决定服务层是否能真正“只读稳定发布版本”。
4. **最后补测试缺口（T10-001、T10-002、T10-005）**
   - 没有契约/质量测试，前述规范难以长期稳定。

## 注意事项

- 本文是**静态落点盘点**，不是功能正确性验收。
- 对 `unknown` 类任务（例如“重构 offline/downloader/*”）建议做一次人工评审或补充 `status` 字段落盘，避免“文件存在但目标未完成”的假阳性。
