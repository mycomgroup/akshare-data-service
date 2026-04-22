现在最需要的，不是继续补接口，而是把项目从“带缓存的数据访问层”重构成“有数据资产分层、有质量门禁、有字段标准、有可追溯血缘的严肃数据工程系统”。
- 下面这份是完整后续工作列表大全，按“必须先做 -> 核心建设 -> 服务稳定 -> 治理运维 -> 长期演进”来排。
- 如果严格执行，这套方案足够支撑你从 抓取数据 走到 稳定的数据服务 ，并把 字段标准化 变成系统能力，而不是零散函数。
北极星

- 目标 1 ：所有服务返回的数据，都来自可追溯、可重放、可校验的数据资产，而不是临时回源拼出来的 DataFrame。
- 目标 2 ：建立 raw -> standardized -> served 三层数据链路，任何字段都能追溯来源、变换规则、版本和质量状态。
- 目标 3 ：字段标准化成为中心能力，所有源接入都必须经过统一字段字典、统一实体模型和统一质量规则。
- 目标 4 ：在线服务从“抓数逻辑”中解耦，优先只读稳定层数据，缺数时走异步补数。
- 目标 5 ：形成工程规范、治理规范和发布规范，避免项目继续膨胀成不可维护的大杂烩。
总体分期

- Phase 0 ：定目标、定边界、冻结无序扩张。
- Phase 1 ：重建数据模型和分层架构。
- Phase 2 ：重建抓取与落地链路。
- Phase 3 ：重建字段标准化与质量体系。
- Phase 4 ：重建服务层与发布链路。
- Phase 5 ：补齐运维、治理、监控和测试。
- Phase 6 ：持续扩域、提性能、做团队化协作。
Phase 0：立项与止血

- 冻结新增接口 ：暂停大规模加新接口和新表，避免继续堆技术债。
- 定义系统边界 ：明确项目到底是 SDK、缓存层、离线数仓、还是正式数据服务平台。
- 定义优先域 ：先只聚焦 3 个最重要域，例如 A 股日线 、 财务指标 、 宏观指标 。
- 定义核心表 ：先锁定首批标准表，不要一开始就覆盖 69 张表。
- 定义成功标准 ：明确什么叫“稳定数据服务”，例如成功率、延迟、覆盖率、补数时效、质量通过率。
- 清理术语 ：统一 接口 、 源 、 原始表 、 标准表 、 服务表 、 资产表 、 缓存表 的概念。
- 冻结命名漂移 ：禁止继续出现接口名、表名、服务名三套不一致的命名体系。
- 形成 RFC 文档 ：先出一份架构 RFC，得到你自己或团队明确确认后再开工。
Phase 0 交付物

- 项目目标说明书
- 架构重构 RFC
- 首批业务域范围说明
- 首批标准表清单
- 命名与术语规范
- 重构期间变更冻结规则
Phase 0 验收标准

- 所有人对项目目标有统一理解。
- 未来 2 到 3 个月只围绕确定范围推进。
- 不再新增与目标无关的功能性扩张。
Phase 1：重建目标架构

- 定义三层架构 ： L0 Raw 、 L1 Standardized 、 L2 Served 。
- 明确职责隔离 ：抓取层只负责采集，标准化层只负责变换，服务层只负责读稳定数据。
- 拆在线与离线 ：在线服务不再承担主要抓取职责，离线链路负责生产资产。
- 建立生产链路 ：每个数据集都要经过 extract -> land raw -> normalize -> validate -> publish 。
- 建立发布链路 ：标准层通过质量门禁后，才能发布到服务层。
- 定义失败策略 ：抓取失败、标准化失败、质量失败、发布失败分别如何处理。
- 设计重放机制 ：给定批次号或日期范围，可以从原始层重新生成标准层。
- 设计回补机制 ：支持历史回填、增量补数、纠错重算。
- 设计幂等机制 ：同一任务重跑不会产生重复数据和口径漂移。
Phase 1 交付物

- 目标技术架构图
- 数据流架构图
- 批处理/发布流程图
- 模块边界设计
- 失败处理矩阵
- 重放与回补设计
Phase 1 验收标准

- 所有模块职责清楚。
- 在线链路和离线链路边界清晰。
- 新表接入必须知道落在哪一层，而不是直接写缓存。
Phase 2：重建抓取与落地链路

- 统一抓取任务模型 ：任务必须有 source_name 、 interface_name 、 params 、 batch_id 、 schedule_time 。
- 统一执行引擎 ：不要再有在线抓取一套、离线下载一套、脚本补数一套的实现。
- 接入 checkpoint ：每类任务都要支持断点续跑。
- 接入任务状态机 ：待执行、执行中、成功、失败、部分成功、待回补。
- 接入幂等键 ：同一抓取窗口、同一参数、同一版本生成同一幂等标识。
- 保留原始载荷 ：抓取后先落原始结果，不要直接只保留标准化后的表。
- 记录抓取审计 ：请求参数、抓取时间、返回行数、源响应 hash、错误信息都要保存。
- 接入源级熔断 ：不只是简单失败切换，要记录失败原因、降级原因和恢复时间。
- 接入速率控制 ：源级限流要统一，不要在线和离线重复造轮子。
- 接入任务编排 ：支持按数据域、按优先级、按日历、按分区调度。
L0 Raw 层必须有的字段

- batch_id
- source_name
- interface_name
- request_params_json
- request_time
- ingest_time
- raw_record_hash
- extract_version
- source_schema_fingerprint
- payload 或原始列全量保留
Phase 2 交付物

- 统一抓取任务模型
- 统一任务执行器
- 任务状态表
- raw 层落地规范
- 抓取审计日志规范
- 任务调度配置
Phase 2 验收标准

- 任何一份标准数据都能回溯到原始抓取批次。
- 同一批次重跑结果可控。
- 离线下载器和在线抓取不再各写各的存储逻辑。
Phase 3：重建字段标准化

- 建立字段字典中心 ：每个标准字段都有正式定义，不再只是列名翻译。
- 先做实体建模 ：先定义实体，再定义字段，不要从 AkShare 返回列直接推字段。
- 定义业务主键 ：每张标准表都要有稳定主键和唯一性规则。
- 定义时间语义 ：区分 event_time 、 trade_date 、 report_date 、 publish_time 、 ingest_time 。
- 定义单位与币种 ：金额、比例、股数、估值必须显式有单位和币种语义。
- 定义枚举域 ：例如市场、复权类型、频率、报告类型等必须标准化。
- 定义缺失值策略 ：哪些字段允许空，空值代表什么，如何补默认值。
- 定义跨源映射 ：每个源字段如何映射到标准字段，要有配置和版本。
- 定义标准化版本 ：每次映射规则变更必须有 normalize_version 。
- 定义口径说明 ：例如 turnover_amount 、 volume 、 net_profit 的口径说明必须文档化。
首批建议标准实体

- security_master
- market_quote_daily
- market_quote_minute
- financial_indicator
- financial_statement_item
- shareholder_event
- capital_flow
- macro_indicator
字段标准化工作清单

- 梳理现有字段全集
- 按业务域分类
- 合并同义字段
- 拆分混合字段
- 建立标准命名规范
- 建立字段字典表
- 建立源字段映射表
- 建立字段废弃策略
- 建立字段版本升级策略
- 建立样例数据集
Phase 3 交付物

- 字段标准命名规范
- 字段字典
- 实体模型字典
- 源到标准映射规则
- 标准化规则版本表
- 首批标准表 schema
Phase 3 验收标准

- 新源接入时，不再直接手写 rename。
- 每个服务字段都能回答“它从哪来、怎么变、口径是什么”。
Phase 4：重建质量体系

- 建立质量分层 ：Raw 只做技术质量，Standardized 做业务质量，Served 做发布质量。
- 建立质量规则中心 ：规则不能散落在代码里，必须配置化、版本化。
- 建立核心规则类型 ：唯一性、非空性、完整性、时序连续性、范围合法性、跨表一致性、跨源偏差。
- 建立质量门禁 ：不过门禁不能发到服务层。
- 建立坏数据隔离区 ：异常数据进入 quarantine，不直接污染服务层。
- 建立数据评分体系 ：评分不能硬编码，要基于规则与权重自动生成。
- 建立质量报表 ：按表、按分区、按批次、按字段、按源输出质量结果。
- 建立对账机制 ：主备源数据差异超阈值要报警。
- 建立时效监控 ：数据新鲜度、延迟、缺失窗口必须可见。
- 建立发布回滚 ：某批质量异常时可以撤回最近发布。
Phase 4 必做质量规则

- 主键唯一
- 主键非空
- 时间字段合法
- 价格字段非负
- high >= low
- 成交量非负
- 日期覆盖率达标
- 跨源核心字段偏差在阈值内
- 财务字段单位一致
- 同一批次 schema 未漂移
Phase 4 交付物

- 质量规则库
- 质量执行框架
- 质量报告模板
- 坏数据隔离机制
- 质量告警机制
- 发布阻断策略
Phase 4 验收标准

- 服务层只发布质量合格批次。
- 质量问题可定位到具体批次、字段、源和规则。
Phase 5：重建存储层

- 重新定义存储语义 ：存储不是缓存目录，而是数据资产存储层。
- 按层分目录 ： raw/standardized/served/system ，不要混在 daily/meta/snapshot 的缓存语义里。
- 重新设计分区策略 ：按查询模式和更新模式定，不按临时实现习惯定。
- 引入数据集元数据 ：每张表有 schema version、owner、partition spec、quality profile。
- 统一写入协议 ：所有写入都走统一写入器，带校验、去重、审计字段补齐。
- 统一 compaction 策略 ：按数据量、分区和查询模式做合并。
- 统一 merge/upsert 策略 ：支持增量覆盖、快照替换、历史保留。
- 支持小文件治理 ：避免长期碎片化。
- 支持版本快照 ：服务读取某次发布版本，而不是读一个随时变化的目录。
- 支持清理与归档 ：raw、standardized、served 的保留周期不同。
存储层建议目录

- data/raw/<domain>/<dataset>/dt=.../batch_id=...
- data/standardized/<domain>/<dataset>/partition=...
- data/served/<domain>/<dataset>/release_version=...
- data/system/metadata
- data/system/quality
- data/system/checkpoints
Phase 5 交付物

- 存储规范
- 表元数据规范
- 分区规范
- 统一写入协议
- 归档与清理策略
- 版本发布目录规范
Phase 5 验收标准

- 任何表的物理落地方式都有明确规范。
- 不再出现写入层名和系统定义层名不一致的问题。
Phase 6：重建服务层

- 服务层只读 served 层 ：不直接碰原始源站。
- 定义服务 SLA ：成功率、延迟、可用性、更新时间。
- 定义缺数策略 ：返回空、返回旧版本、异步补数、强制降级，要可配置。
- 定义版本选择策略 ：默认读最新稳定发布，不读进行中批次。
- 定义查询契约 ：分页、过滤、排序、时间范围、字段选择规范化。
- 定义缓存边界 ：服务缓存只是加速 served 层读取，不再承担资产语义。
- 定义回源开关 ：如保留在线回源，也必须为显式、异步、受控能力。
- 定义服务鉴权与限流 ：面向正式数据服务必须有租户或调用方边界。
- 定义错误码语义 ：区分无数据、数据未发布、数据质量不合格、源数据缺失。
- 定义服务文档生成 ：接口文档直接绑定标准字段字典。
Phase 6 交付物

- 服务层架构说明
- 查询契约规范
- 缺数与降级策略
- 服务 SLA
- 接口文档模板
- 版本读取策略
Phase 6 验收标准

- 服务响应不再依赖实时抓取成功。
- 服务返回的数据有清晰版本和质量状态。
Phase 7：重建元数据与治理体系

- 建立 metadata catalog ：记录每张表的定义、owner、版本、质量规则、分区、来源。
- 建立 schema registry 2.0 ：从“缓存表注册”升级为“数据契约注册”。
- 建立字段血缘 ：字段从哪个源字段映射而来，经过哪些变换。
- 建立变更管理 ：schema 变更必须评审、版本化、通知下游。
- 建立废弃策略 ：字段下线要有 deprecation window。
- 建立数据 owner ：每个域、每张表、每组规则必须有人负责。
- 建立发布审批 ：关键表变更需手动确认。
- 建立数据字典门户 ：至少先做静态文档版。
- 建立口径 FAQ ：对常见字段定义做集中说明。
- 建立依赖地图 ：知道哪些服务依赖哪些表。
Phase 7 交付物

- 元数据中心
- schema registry 2.0
- 字段血缘表
- 变更流程
- 字段废弃流程
- owner 制度
Phase 7 验收标准

- 任何 schema 改动不会再悄悄影响下游。
- 新人接手时可以快速理解表和字段。
Phase 8：重建测试体系

- 重建测试金字塔 ：单元测试、契约测试、集成测试、批次回放测试、端到端测试。
- 增加映射规则测试 ：字段映射变更必须自动校验。
- 增加样本快照测试 ：典型源返回样本固定后防 schema 漂移。
- 增加质量规则测试 ：每条关键质量规则都有正例和反例。
- 增加回放测试 ：历史批次能否从 raw 重建 standardized。
- 增加发布测试 ：质量不通过时，served 不得更新。
- 增加兼容性测试 ：schema 升级后旧查询是否兼容。
- 增加性能测试 ：典型查询、批处理、回补任务的时间基线。
- 增加容错测试 ：源站失败、字段漂移、空数据、重复数据场景。
- 增加数据对账测试 ：主备源偏差检测。
Phase 8 交付物

- 测试策略说明
- 样本数据仓
- 契约测试框架
- 回放测试框架
- 质量规则测试集
- 发布门禁测试
Phase 8 验收标准

- 每次变更都能自动知道是否破坏了资产契约。
- 核心域可稳定回归。
Phase 9：重建监控与运维

- 建立任务监控 ：任务成功率、失败率、重试次数、耗时。
- 建立数据监控 ：覆盖率、更新延迟、分区缺失、空值率、异常数。
- 建立服务监控 ：接口成功率、P95 延迟、命中率、热点表。
- 建立存储监控 ：文件数、小文件、分区倾斜、磁盘占用。
- 建立质量监控 ：规则通过率、异常批次、坏数据积压。
- 建立源监控 ：源可用性、失败原因分布、速率限制命中。
- 建立告警分级 ：P0 服务不可用、P1 数据未更新、P2 质量波动。
- 建立运行手册 ：故障处理、回补流程、回滚流程。
- 建立值班机制 ：至少先形成个人可执行的排障 SOP。
- 建立运营 dashboard ：统一看板。
Phase 9 交付物

- 监控指标清单
- 告警规则
- 运维手册
- 回补手册
- 回滚手册
- 统一 dashboard
Phase 9 验收标准

- 出问题时先看监控就知道是源问题、质量问题还是发布问题。
- 关键故障可在可接受时间内恢复。
Phase 10：组织与协作机制

- 建立域负责人 ：行情域、财务域、宏观域分别有人负责。
- 建立代码评审规则 ：字段变更、schema 变更、质量规则变更要专项评审。
- 建立接口接入模板 ：新源接入必须走 checklist。
- 建立变更公告机制 ：重要字段变更对使用方可见。
- 建立 issue 分类 ：源问题、标准化问题、质量问题、服务问题分开管理。
- 建立开发规范 ：目录规范、命名规范、配置规范、异常规范。
- 建立数据发布节奏 ：日更、盘后、周更、月更要明确定义。
- 建立技术债清单 ：长期追踪，不让问题再沉底。
- 建立版本节奏 ：架构版本、schema 版本、服务版本不要混。
- 建立季度复盘机制 ：每季度复盘覆盖率、稳定性和质量指标。
第一批必须优先落地的核心数据集

- market_quote_daily
- financial_indicator
- financial_statement_item
- trade_calendar
- security_master
- macro_indicator
建议先不要做的事

- 不要继续大量补 69 张表之外的新表
- 不要继续扩充动态 __getattr__ 这种黑盒式 API
- 不要把字段标准化继续停留在中文转英文
- 不要让服务层继续默默回源补数据
- 不要让离线和在线各自维护一套抓取与写盘逻辑
- 不要把 schema registry 继续只当缓存配置
- 不要先优化查询性能，再补数据治理主线
建议的 90 天执行顺序

- 第 1-2 周 ：完成 Phase 0 和 Phase 1 设计确认。
- 第 3-4 周 ：完成统一抓取模型、raw 层落地、任务审计。
- 第 5-6 周 ：完成首批 3 张标准表和字段字典。
- 第 7-8 周 ：完成质量规则中心和质量门禁。
- 第 9-10 周 ：完成 served 层发布和服务层只读改造。
- 第 11-12 周 ：完成监控、回补、回滚、测试闭环。
最小可行版本范围

- 只做 3 个数据域
- 只做 3 层架构
- 只做 10-15 条关键质量规则
- 只做 1 套统一抓取执行链路
- 只做 1 套发布链路
- 只做 1 套元数据和字段字典
每阶段统一验收口径

- 可追溯 ：能查到这条数据来自哪个源、哪次任务、哪套规则。
- 可重放 ：给定批次可重新生成。
- 可阻断 ：质量不合格不能发布。
- 可观测 ：异常时有指标和告警。
- 可维护 ：新源接入不用在 5 个地方改代码。
- 可服务 ：在线接口不依赖临时抓取成功。

## 更具体的 Task 清单

这一部分不是原则，而是可以直接拆成 issue、任务卡、里程碑的执行清单。

建议每个 task 统一包含 4 个字段：

- task_id：唯一编号，例如 `T0-001`
- output：产出物放到哪里
- done_when：什么叫完成
- dependency：依赖哪个前置任务

建议状态统一使用：

- todo
- doing
- blocked
- review
- done

建议优先级统一使用：

- P0：不做后面都没法推进
- P1：核心链路必须做
- P2：重要但可后置
- P3：优化项

## Task Backlog V1

### Phase 0 立项与止血

- [ ] `T0-001` 明确项目目标定义
  - output：`docs/design/00-project-goal.md`
  - done_when：明确项目是“严肃数据工程数据服务”，而不是“缓存增强 SDK”
  - dependency：无
- [ ] `T0-002` 编写重构 RFC
  - output：`docs/design/01-architecture-rfc.md`
  - done_when：写清目标架构、分层、迁移范围、非目标
  - dependency：`T0-001`
- [ ] `T0-003` 定义术语表
  - output：`docs/design/02-glossary-v2.md`
  - done_when：统一 raw、standardized、served、dataset、batch、publish、quality gate 等术语
  - dependency：`T0-001`
- [ ] `T0-004` 冻结新增接口规则
  - output：`docs/design/03-change-freeze.md`
  - done_when：明确哪些类型的新增接口暂停，哪些修复允许继续
  - dependency：`T0-001`
- [ ] `T0-005` 选定首批试点数据域
  - output：`docs/design/04-pilot-scope.md`
  - done_when：至少确定 `market_quote_daily`、`financial_indicator`、`macro_indicator`
  - dependency：`T0-002`
- [ ] `T0-006` 盘点现有模块映射关系
  - output：`docs/design/05-current-to-target-mapping.md`
  - done_when：标出当前 `api`、`sources`、`store`、`offline` 在新架构中的归属
  - dependency：`T0-002`
- [ ] `T0-007` 建立技术债总表
  - output：`docs/design/06-tech-debt-register.md`
  - done_when：把已识别问题按严重度、模块、处理阶段登记
  - dependency：`T0-006`
- [ ] `T0-008` 制定 90 天里程碑
  - output：`docs/design/07-roadmap-90d.md`
  - done_when：分周列出目标、负责人、里程碑、验收口径
  - dependency：`T0-005`

### Phase 1 目标架构与目录重构

- [ ] `T1-001` 设计目标目录结构
  - output：`docs/design/10-target-repo-layout.md`
  - done_when：定义 `ingestion`、`raw`、`standardized`、`served`、`governance`、`quality`、`service` 模块边界
  - dependency：`T0-002`
- [ ] `T1-002` 设计三层数据架构
  - output：`docs/design/11-data-layer-model.md`
  - done_when：定义 `L0 Raw`、`L1 Standardized`、`L2 Served` 的职责和禁止事项
  - dependency：`T1-001`
- [ ] `T1-003` 设计任务流转架构
  - output：`docs/design/12-pipeline-lifecycle.md`
  - done_when：定义 `extract -> land -> normalize -> validate -> publish`
  - dependency：`T1-002`
- [ ] `T1-004` 设计失败处理矩阵
  - output：`docs/design/13-failure-matrix.md`
  - done_when：抓取失败、解析失败、质量失败、发布失败都有处理策略
  - dependency：`T1-003`
- [ ] `T1-005` 设计重放与回补策略
  - output：`docs/design/14-replay-backfill.md`
  - done_when：支持按批次、按日期、按分区重建
  - dependency：`T1-003`
- [ ] `T1-006` 设计版本模型
  - output：`docs/design/15-versioning-model.md`
  - done_when：明确 `extract_version`、`normalize_version`、`schema_version`、`release_version`
  - dependency：`T1-002`
- [ ] `T1-007` 设计模块迁移计划
  - output：`docs/design/16-migration-plan-v2.md`
  - done_when：写清哪些旧模块保留、拆分、废弃、兼容
  - dependency：`T1-001`
- [ ] `T1-008` 落地新目录骨架
  - output：代码目录
  - done_when：在 `src/akshare_data/` 下创建新分层目录但不破坏现有功能
  - dependency：`T1-007`

### Phase 2 统一抓取与任务系统

- [ ] `T2-001` 定义抓取任务数据类
  - output：`src/akshare_data/ingestion/models/task.py`
  - done_when：包含 `task_id`、`source_name`、`interface_name`、`params`、`window`、`batch_id`
  - dependency：`T1-003`
- [ ] `T2-002` 定义批次数据类
  - output：`src/akshare_data/ingestion/models/batch.py`
  - done_when：支持批次号、计划时间、开始时间、结束时间、状态、统计信息
  - dependency：`T2-001`
- [ ] `T2-003` 定义任务状态机
  - output：`src/akshare_data/ingestion/task_state.py`
  - done_when：支持 `pending/running/succeeded/failed/partial/retrying/published`
  - dependency：`T2-001`
- [ ] `T2-004` 统一执行器接口
  - output：`src/akshare_data/ingestion/executor/base.py`
  - done_when：在线、离线、补数都走同一执行抽象
  - dependency：`T2-001`
- [ ] `T2-005` 抽取现有离线下载逻辑
  - output：重构 `offline/downloader/*`
  - done_when：旧下载器不再直接写脏数据到旧缓存层
  - dependency：`T2-004`
- [ ] `T2-006` 增加幂等键计算器
  - output：`src/akshare_data/ingestion/idempotency.py`
  - done_when：同源同参数同窗口生成稳定幂等键
  - dependency：`T2-001`
- [ ] `T2-007` 增加 checkpoint 管理器
  - output：`src/akshare_data/ingestion/checkpoint.py`
  - done_when：任务支持断点续跑与恢复
  - dependency：`T2-003`
- [ ] `T2-008` 增加抓取审计记录
  - output：`src/akshare_data/ingestion/audit.py`
  - done_when：记录请求参数、源、耗时、行数、错误、schema 指纹
  - dependency：`T2-004`
- [ ] `T2-009` 增加源健康与降级记录
  - output：`src/akshare_data/ingestion/source_health.py`
  - done_when：不仅知道源失败，还知道失败原因和恢复时间
  - dependency：`T2-004`
- [ ] `T2-010` 增加调度入口
  - output：`src/akshare_data/ingestion/scheduler.py`
  - done_when：支持按日历、优先级、分区生成任务
  - dependency：`T2-002`

### Phase 3 Raw 层落地

- [ ] `T3-001` 设计 raw 数据集规范
  - output：`docs/design/20-raw-spec.md`
  - done_when：定义 raw 表结构、目录规范、保留字段、保留周期
  - dependency：`T1-002`
- [ ] `T3-002` 定义 raw 统一系统字段
  - output：`src/akshare_data/raw/system_fields.py`
  - done_when：包含 `batch_id/source_name/interface_name/request_time/ingest_time/raw_record_hash`
  - dependency：`T3-001`
- [ ] `T3-003` 实现 raw writer
  - output：`src/akshare_data/raw/writer.py`
  - done_when：所有抓取结果先进入 raw 层
  - dependency：`T3-002`
- [ ] `T3-004` 实现 raw manifest
  - output：`src/akshare_data/raw/manifest.py`
  - done_when：每批次都生成 manifest，记录文件、分区、条数、hash
  - dependency：`T3-003`
- [ ] `T3-005` 实现 raw schema fingerprint
  - output：`src/akshare_data/raw/schema_fingerprint.py`
  - done_when：源字段变化可以被自动识别
  - dependency：`T3-003`
- [ ] `T3-006` 建 raw 样本存档
  - output：`data/system/raw_samples/`
  - done_when：核心接口的代表性样本被固化保存
  - dependency：`T3-003`
- [ ] `T3-007` 增加 raw 重放读取器
  - output：`src/akshare_data/raw/reader.py`
  - done_when：可按批次和分区读回原始数据
  - dependency：`T3-003`

### Phase 4 标准实体与字段标准化

- [ ] `T4-001` 定义标准实体清单
  - output：`docs/design/30-standard-entities.md`
  - done_when：首批实体、主键、时间字段、业务边界明确
  - dependency：`T0-005`
- [ ] `T4-002` 定义标准命名规范
  - output：`docs/design/31-field-naming-standard.md`
  - done_when：统一 snake_case、时间字段、金额字段、比例字段命名
  - dependency：`T4-001`
- [ ] `T4-003` 盘点现有字段全集
  - output：`docs/design/32-field-inventory.md`
  - done_when：把现有所有 source 字段、旧 schema 字段、服务字段汇总
  - dependency：`T4-001`
- [ ] `T4-004` 建字段字典主表
  - output：`config/standards/field_dictionary.yaml`
  - done_when：每个字段有定义、类型、单位、允许空值、说明
  - dependency：`T4-002`
- [ ] `T4-005` 建实体 schema 定义
  - output：`config/standards/entities/*.yaml`
  - done_when：每个实体的字段、主键、分区、版本明确
  - dependency：`T4-004`
- [ ] `T4-006` 建源字段映射表
  - output：`config/mappings/sources/*.yaml`
  - done_when：每个源字段都映射到标准字段或标记废弃
  - dependency：`T4-003`
- [ ] `T4-007` 建标准化规则版本表
  - output：`config/standards/normalize_versions.yaml`
  - done_when：映射调整可追踪版本
  - dependency：`T4-006`
- [ ] `T4-008` 实现标准化引擎基类
  - output：`src/akshare_data/standardized/normalizer/base.py`
  - done_when：支持字段映射、系统字段补齐、类型转换、枚举归一
  - dependency：`T4-005`
- [ ] `T4-009` 实现 `market_quote_daily` 标准化器
  - output：`src/akshare_data/standardized/normalizer/market_quote_daily.py`
  - done_when：首个核心标准表跑通
  - dependency：`T4-008`
- [ ] `T4-010` 实现 `financial_indicator` 标准化器
  - output：对应代码文件
  - done_when：财务指标标准化跑通
  - dependency：`T4-008`
- [ ] `T4-011` 实现 `macro_indicator` 标准化器
  - output：对应代码文件
  - done_when：宏观指标标准化跑通
  - dependency：`T4-008`
- [ ] `T4-012` 实现标准化样例数据集
  - output：`tests/fixtures/standardized_samples/`
  - done_when：每张标准表至少有 3 份样例
  - dependency：`T4-009`

### Phase 5 Standardized 层写入与读取

- [ ] `T5-001` 设计 standardized 存储规范
  - output：`docs/design/40-standardized-storage-spec.md`
  - done_when：目录、分区、版本、upsert 策略明确
  - dependency：`T1-002`
- [ ] `T5-002` 实现 standardized writer
  - output：`src/akshare_data/standardized/writer.py`
  - done_when：带 schema 校验、去重、系统字段补齐
  - dependency：`T5-001`
- [ ] `T5-003` 实现 standardized reader
  - output：`src/akshare_data/standardized/reader.py`
  - done_when：支持按实体、分区、时间范围查询
  - dependency：`T5-002`
- [ ] `T5-004` 实现 merge/upsert 规则
  - output：`src/akshare_data/standardized/merge.py`
  - done_when：明确增量覆盖、晚到数据、重复数据处理方式
  - dependency：`T5-002`
- [ ] `T5-005` 实现 compaction 作业
  - output：`src/akshare_data/standardized/compaction.py`
  - done_when：支持按分区合并小文件
  - dependency：`T5-002`
- [ ] `T5-006` 实现 standardized manifest
  - output：`src/akshare_data/standardized/manifest.py`
  - done_when：每次写入可追踪版本和文件清单
  - dependency：`T5-002`

### Phase 6 质量体系与门禁

- [ ] `T6-001` 设计质量规则 DSL
  - output：`docs/design/50-quality-rule-spec.md`
  - done_when：支持 non_null、unique、range、coverage、freshness、diff 等规则
  - dependency：`T1-003`
- [ ] `T6-002` 建质量规则配置目录
  - output：`config/quality/*.yaml`
  - done_when：每个标准表都可以单独配置质量规则
  - dependency：`T6-001`
- [ ] `T6-003` 实现质量执行引擎
  - output：`src/akshare_data/quality/engine.py`
  - done_when：可执行规则并生成结构化结果
  - dependency：`T6-002`
- [ ] `T6-004` 实现完整性检查器
  - output：`src/akshare_data/quality/checks/completeness.py`
  - done_when：覆盖日期连续性、主键覆盖率、分区覆盖率
  - dependency：`T6-003`
- [ ] `T6-005` 实现一致性检查器
  - output：`src/akshare_data/quality/checks/consistency.py`
  - done_when：支持跨源、跨层、跨表对账
  - dependency：`T6-003`
- [ ] `T6-006` 实现异常检测器
  - output：`src/akshare_data/quality/checks/anomaly.py`
  - done_when：支持数值异常、价格异常、波动异常
  - dependency：`T6-003`
- [ ] `T6-007` 实现质量报告模型
  - output：`src/akshare_data/quality/report.py`
  - done_when：结果包含批次、规则、严重级别、失败明细
  - dependency：`T6-003`
- [ ] `T6-008` 实现质量门禁
  - output：`src/akshare_data/quality/gate.py`
  - done_when：质量不通过不得进入 served 层
  - dependency：`T6-007`
- [ ] `T6-009` 实现坏数据隔离区
  - output：`src/akshare_data/quality/quarantine.py`
  - done_when：失败数据和失败原因可留存和回查
  - dependency：`T6-008`
- [ ] `T6-010` 移除现有硬编码评分
  - output：重构旧质量代码
  - done_when：评分由规则权重自动生成，不再硬编码固定分值
  - dependency：`T6-007`

### Phase 7 Served 层与发布系统

- [ ] `T7-001` 设计 served 层规范
  - output：`docs/design/60-served-layer-spec.md`
  - done_when：明确 served 表只来自质量通过的 standardized 表
  - dependency：`T6-008`
- [ ] `T7-002` 定义发布版本模型
  - output：`docs/design/61-release-version-model.md`
  - done_when：定义每次发布的 release_version 和 manifest
  - dependency：`T7-001`
- [ ] `T7-003` 实现发布器
  - output：`src/akshare_data/served/publisher.py`
  - done_when：可将 standardized 数据发布到 served 层
  - dependency：`T7-002`
- [ ] `T7-004` 实现回滚器
  - output：`src/akshare_data/served/rollback.py`
  - done_when：可回滚到上一版本发布
  - dependency：`T7-003`
- [ ] `T7-005` 实现 served manifest
  - output：`src/akshare_data/served/manifest.py`
  - done_when：知道哪些分区由哪个批次发布
  - dependency：`T7-003`
- [ ] `T7-006` 实现服务读取适配层
  - output：`src/akshare_data/service/reader.py`
  - done_when：服务层优先读 served，不直接读 raw 和源站
  - dependency：`T7-003`

### Phase 8 在线服务改造

- [ ] `T8-001` 设计新服务职责
  - output：`docs/design/70-service-boundary.md`
  - done_when：服务层明确不承担主抓取职责
  - dependency：`T7-006`
- [ ] `T8-002` 抽离现有 `DataService` 抓取逻辑
  - output：重构 `src/akshare_data/api.py`
  - done_when：服务读取和抓取执行逻辑解耦
  - dependency：`T8-001`
- [ ] `T8-003` 增加数据版本选择器
  - output：`src/akshare_data/service/version_selector.py`
  - done_when：支持默认最新稳定版本、指定版本、指定发布日期
  - dependency：`T7-003`
- [ ] `T8-004` 增加缺数策略控制
  - output：`src/akshare_data/service/missing_data_policy.py`
  - done_when：支持返回空、返回旧版本、异步补数
  - dependency：`T8-002`
- [ ] `T8-005` 增加查询契约定义
  - output：`docs/design/71-query-contract.md`
  - done_when：统一分页、排序、过滤、字段裁剪、时间范围规则
  - dependency：`T8-001`
- [ ] `T8-006` 接口文档绑定字段字典
  - output：文档生成逻辑
  - done_when：每个接口字段描述来自标准字段字典而不是手写注释
  - dependency：`T4-004`
- [ ] `T8-007` 增加服务错误语义分层
  - output：错误码与异常重构
  - done_when：能区分无数据、未发布、质量阻断、源失败
  - dependency：`T8-002`

### Phase 9 元数据、血缘、治理

- [ ] `T9-001` 设计 metadata catalog
  - output：`docs/design/80-metadata-catalog.md`
  - done_when：表、字段、版本、owner、质量规则、依赖关系可登记
  - dependency：`T4-005`
- [ ] `T9-002` 实现 dataset 元数据注册
  - output：`src/akshare_data/governance/catalog.py`
  - done_when：每张表有正式注册信息
  - dependency：`T9-001`
- [ ] `T9-003` 实现字段血缘记录
  - output：`src/akshare_data/governance/lineage.py`
  - done_when：从 source field 到 standard field 到 served field 可追溯
  - dependency：`T4-006`
- [ ] `T9-004` 实现 schema 变更流程
  - output：`docs/design/81-schema-change-process.md`
  - done_when：新增字段、改字段、删字段有明确流程
  - dependency：`T9-001`
- [ ] `T9-005` 实现字段废弃流程
  - output：`docs/design/82-field-deprecation.md`
  - done_when：存在下线窗口和兼容策略
  - dependency：`T9-004`
- [ ] `T9-006` 建立 owner 制度
  - output：`docs/design/83-owner-model.md`
  - done_when：每个域、每张核心表都有 owner
  - dependency：`T0-005`

### Phase 10 测试体系

- [ ] `T10-001` 重写测试策略文档
  - output：`docs/design/90-test-strategy-v2.md`
  - done_when：定义单测、契约、回放、质量、发布、E2E 测试边界
  - dependency：`T1-003`
- [ ] `T10-002` 增加字段映射测试
  - output：`tests/contract/test_field_mappings.py`
  - done_when：映射变更自动检查
  - dependency：`T4-006`
- [ ] `T10-003` 增加 schema 契约测试
  - output：`tests/contract/test_entity_schemas.py`
  - done_when：标准表 schema 漂移会失败
  - dependency：`T4-005`
- [ ] `T10-004` 增加 raw 回放测试
  - output：`tests/replay/test_raw_replay.py`
  - done_when：历史批次可重建标准层
  - dependency：`T3-007`
- [ ] `T10-005` 增加质量规则测试
  - output：`tests/quality/`
  - done_when：每条关键规则至少有正反例
  - dependency：`T6-003`
- [ ] `T10-006` 增加发布门禁测试
  - output：`tests/served/test_publish_gate.py`
  - done_when：质量失败时发布一定失败
  - dependency：`T7-003`
- [ ] `T10-007` 增加在线服务只读测试
  - output：`tests/integration/test_service_reads_served_only.py`
  - done_when：服务链路不直接触发实时抓取
  - dependency：`T8-002`

### Phase 11 监控与运维

- [ ] `T11-001` 设计监控指标表
  - output：`docs/design/100-observability-metrics.md`
  - done_when：任务、数据、质量、服务、存储指标全覆盖
  - dependency：`T2-008`
- [ ] `T11-002` 增加任务指标埋点
  - output：代码实现
  - done_when：可以看到任务成功率、耗时、失败原因
  - dependency：`T11-001`
- [ ] `T11-003` 增加质量指标埋点
  - output：代码实现
  - done_when：能看到规则通过率、异常批次数
  - dependency：`T6-007`
- [ ] `T11-004` 增加服务指标埋点
  - output：代码实现
  - done_when：能看到响应时间、错误码、命中率
  - dependency：`T8-002`
- [ ] `T11-005` 建立告警规则
  - output：`docs/design/101-alert-rules.md`
  - done_when：P0/P1/P2 告警分级清楚
  - dependency：`T11-001`
- [ ] `T11-006` 编写运行手册
  - output：`docs/runbooks/`
  - done_when：包括故障处理、补数、回滚、重放 SOP
  - dependency：`T11-005`
- [ ] `T11-007` 建立统一 dashboard
  - output：看板配置或文档
  - done_when：可以一眼看到系统健康情况
  - dependency：`T11-002`

## 首批 30 天建议直接开工的任务

这 12 个任务建议最先做，不要分散：

- [ ] `T0-001` 明确项目目标定义
- [ ] `T0-002` 编写重构 RFC
- [ ] `T0-005` 选定首批试点数据域
- [ ] `T1-001` 设计目标目录结构
- [ ] `T1-002` 设计三层数据架构
- [ ] `T2-001` 定义抓取任务数据类
- [ ] `T2-004` 统一执行器接口
- [ ] `T3-001` 设计 raw 数据集规范
- [ ] `T4-001` 定义标准实体清单
- [ ] `T4-004` 建字段字典主表
- [ ] `T6-001` 设计质量规则 DSL
- [ ] `T7-001` 设计 served 层规范

## 首批试点建议验收包

试点只做 3 张表，跑通完整链路：

- `market_quote_daily`
- `financial_indicator`
- `macro_indicator`

每张表必须完成以下 task：

- [ ] 有 raw 落地
- [ ] 有标准实体 schema
- [ ] 有字段字典
- [ ] 有源字段映射
- [ ] 有 standardized writer
- [ ] 有质量规则
- [ ] 有质量报告
- [ ] 有 served 发布
- [ ] 有服务读取
- [ ] 有回放测试

## issue 拆分建议

建议后续在 issue 系统中按以下标签拆：

- `arch`
- `ingestion`
- `raw`
- `standardized`
- `served`
- `quality`
- `governance`
- `service`
- `testing`
- `ops`

建议 issue 标题格式：

- `[arch] T1-002 设计三层数据架构`
- `[quality] T6-008 实现质量门禁`
- `[service] T8-002 抽离 DataService 抓取逻辑`

## 最后一句

从现在开始，所有新增工作都要先问 3 个问题：

- 它是落在 raw、standardized 还是 served？
- 它有没有字段标准和质量规则？
- 它是否可追溯、可重放、可发布？

如果这 3 个问题答不上来，就先不要做。
