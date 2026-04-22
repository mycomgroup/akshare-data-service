# 任务 08：改造 Service 为只读 Served

## 目标

把对外服务主路径改造成“只读 Served”，停止把实时抓取作为默认响应路径。

## 必读文档

- `docs/design/00-project-goal.md`
- `docs/design/01-architecture-rfc.md`
- `docs/design/10-target-repo-layout.md`

## 任务范围

- 重构 `src/akshare_data/api.py`
- 新建或完善 `src/akshare_data/service/data_service.py`
- 新建 `src/akshare_data/service/reader.py`
- 新建 `src/akshare_data/service/version_selector.py`
- 新建 `src/akshare_data/service/missing_data_policy.py`

## 关键要求

- 保留外部 `DataService` 入口兼容
- 主查询路径只读 `served`
- 缺数时可返回状态或触发异步补数请求，但不可同步直连源站
- 避免把 source adapter 放回 `service`

## 验收标准

- 关键查询入口不再直接回源
- 兼容层仍可被现有调用方导入
