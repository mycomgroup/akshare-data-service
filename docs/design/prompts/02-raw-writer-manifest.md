# 任务 02：实现 Raw Writer 与 Manifest

## 目标

按 `docs/design/20-raw-spec.md` 实现 L0 Raw 写入基础设施。

## 必读文档

- `docs/design/01-architecture-rfc.md`
- `docs/design/20-raw-spec.md`
- `docs/design/10-target-repo-layout.md`

## 任务范围

- 新建 `src/akshare_data/raw/system_fields.py`
- 新建 `src/akshare_data/raw/writer.py`
- 新建 `src/akshare_data/raw/manifest.py`
- 新建 `src/akshare_data/raw/schema_fingerprint.py`
- 如有必要，新建 `src/akshare_data/raw/reader.py`

## 关键要求

- 路径使用 `extract_date=<date>/batch_id=<id>`
- Raw 只保留原字段名，不做 rename
- 支持 manifest 和 schema snapshot 输出
- 记录系统字段：`batch_id`、`source_name`、`interface_name`、`request_params_json`、`request_time`、`ingest_time`、`extract_date`、`extract_version`、`source_schema_fingerprint`、`raw_record_hash`
- 支持原子写入

## 非目标

- 不做 Standardized writer
- 不做服务层读取

## 验收标准

- 可将任意 DataFrame 以 Raw 规范写盘
- Manifest 表示“抽取行为”，不是业务日期快照
- 能按 `batch_id` 读回原始数据
