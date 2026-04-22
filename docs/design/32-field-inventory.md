# T4-003 字段全集盘点

> **文档目的**: 汇总现有所有 source 字段、旧 schema 字段、服务字段，为后续字段标准化提供依据。

---

## 1. 字段来源概述

| 来源 | 文件路径 | 字段数量 | 说明 |
|------|----------|---------|------|
| Schema Registry (YAML) | `config/schemas.yaml` | 69 表 x N 字段 | 缓存表结构定义 |
| Schema Registry (Python) | `src/akshare_data/core/schema.py` | 69 表 x N 字段 | Python 版表定义 (与 YAML 同步) |
| Field Mapping | `src/akshare_data/core/fields.py` | 53 条映射 | 中→英字段映射 |
| Interface Definitions | `config/interfaces/*.yaml` | 6 类接口 | 接口输入输出规范 |
| Lixinger Source | `src/akshare_data/sources/lixinger_source.py` | - | 数据源适配器 |
| AkShare Source | `src/akshare_data/sources/akshare_source.py` | - | 配置驱动分发器 |

---

## 2. Schema Registry 字段清单 (69 表)

### 2.1 Daily Layer (45 表)

#### 核心 OHLCV 字段 (高频)

| 字段名 | 数据类型 | 中文名 | 使用表数 | 备注 |
|--------|----------|--------|---------|------|
| `symbol` | string | 代码/股票代码 | 45+ | 所有表主键 |
| `date` | date | 日期/交易日期 | 45+ | 日线表分区键 |
| `open` | float64 | 开盘价 | 15+ | OHLCV 标准字段 |
| `high` | float64 | 最高价 | 15+ | OHLCV 标准字段 |
| `low` | float64 | 最低价 | 15+ | OHLCV 标准字段 |
| `close` | float64 | 收盘价 | 15+ | OHLCV 标准字段 |
| `volume` | float64 | 成交量 | 15+ | OHLCV 标准字段 |
| `amount` | float64 | 成交额 | 14+ | OHLCV 标准字段 |

#### 股票日线 (stock_daily)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `date` | date | 交易日期 |
| `open` | float64 | 开盘价 |
| `high` | float64 | 最高价 |
| `low` | float64 | 最低价 |
| `close` | float64 | 收盘价 |
| `volume` | float64 | 成交量 |
| `amount` | float64 | 成交额 |
| `adjust` | string | 复权类型 |

#### 期货日线 (futures_daily)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 期货代码 |
| `date` | date | 交易日期 |
| `open` | float64 | 开盘价 |
| `high` | float64 | 最高价 |
| `low` | float64 | 最低价 |
| `close` | float64 | 收盘价 |
| `volume` | float64 | 成交量 |
| `open_interest` | float64 | 持仓量 |

#### 资金流向 (money_flow)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `date` | date | 交易日期 |
| `main_net_inflow` | float64 | 主力净流入 |
| `super_large_net_inflow` | float64 | 超大单净流入 |
| `large_net_inflow` | float64 | 大单净流入 |
| `medium_net_inflow` | float64 | 中单净流入 |
| `small_net_inflow` | float64 | 小单净流入 |

#### 北向资金 (north_flow)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `date` | date | 日期 |
| `net_flow` | float64 | 净流入 |
| `buy_amount` | float64 | 买入金额 |
| `sell_amount` | float64 | 卖出金额 |

#### 财务指标 (finance_indicator)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `report_date` | date | 报告日期 |
| `pe` | float64 | 市盈率 |
| `pb` | float64 | 市净率 |
| `ps` | float64 | 市销率 |
| `roe` | float64 | ROE |
| `net_profit` | float64 | 净利润 |
| `revenue` | float64 | 营业收入 |

#### 估值数据 (valuation)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `date` | date | 日期 |
| `pe` | float64 | 市盈率 |
| `pb` | float64 | 市净率 |
| `ps` | float64 | 市销率 |
| `market_cap` | float64 | 总市值 |
| `circulating_cap` | float64 | 流通市值 |

#### 指数成份股 (index_components)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `index_code` | string | 指数代码 |
| `date` | date | 日期 |
| `symbol` | string | 成份股代码 |
| `weight` | float64 | 权重 |

#### 持仓变动 (holder)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `report_date` | date | 报告日期 |
| `holder_name` | string | 持有人名称 |
| `hold_count` | float64 | 持仓数量 |
| `hold_ratio` | float64 | 持仓比例 |
| `holder_type` | string | 持有人类型 |

#### 分红数据 (dividend)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `announce_date` | date | 公告日期 |
| `dividend_cash` | float64 | 现金分红 |
| `dividend_stock` | float64 | 股票分红 |
| `record_date` | date | 登记日 |
| `ex_date` | date | 除权日 |

#### 股权质押 (equity_pledge)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `pledge_date` | date | 质押日期 |
| `shareholder_name` | string | 股东名称 |
| `pledge_shares` | float64 | 质押股数 |
| `pledge_ratio` | float64 | 质押比例 |
| `pledgee` | string | 质权人 |
| `start_date` | date | 开始日期 |
| `end_date` | date | 结束日期 |

#### 限售股解禁 (restricted_release)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `release_date` | date | 解禁日期 |
| `release_shares` | float64 | 解禁股数 |
| `release_value` | float64 | 解禁市值 |
| `release_type` | string | 解禁类型 |
| `shareholder_name` | string | 股东名称 |

#### 商誉数据 (goodwill)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `report_date` | date | 报告日期 |
| `goodwill_balance` | float64 | 商誉余额 |
| `goodwill_impairment` | float64 | 商誉减值 |
| `net_assets` | float64 | 净资产 |
| `goodwill_ratio` | float64 | 商誉占比 |

#### 内部交易 (insider_trade)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `transaction_date` | date | 交易日期 |
| `name` | string | 姓名 |
| `title` | string | 职位 |
| `transaction_shares` | float64 | 交易股数 |
| `transaction_price` | float64 | 交易价格 |
| `transaction_value` | float64 | 交易金额 |
| `relationship` | string | 关系 |

#### ESG评级 (esg_rating)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `rating_date` | date | 评级日期 |
| `esg_score` | float64 | ESG得分 |
| `e_score` | float64 | E得分 |
| `s_score` | float64 | S得分 |
| `g_score` | float64 | G得分 |
| `rating_agency` | string | 评级机构 |

#### 业绩预告 (performance_forecast)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `report_date` | date | 报告日期 |
| `forecast_type` | string | 预告类型 |
| `net_profit_min` | float64 | 净利润下限 |
| `net_profit_max` | float64 | 净利润上限 |
| `change_pct_min` | float64 | 变幅下限 |
| `change_pct_max` | float64 | 变幅上限 |

#### 龙虎榜 (dragon_tiger_list)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `name` | string | 名称 |
| `date` | date | 日期 |
| `change_pct` | float64 | 涨跌幅 |
| `turnover` | float64 | 成交额 |
| `reason` | string | 上榜原因 |
| `net_buy` | float64 | 净买入 |
| `buy_amount` | float64 | 买入金额 |
| `sell_amount` | float64 | 卖出金额 |

#### 大宗交易 (block_deal)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `date` | date | 日期 |
| `deal_price` | float64 | 成交价 |
| `deal_volume` | float64 | 成交量 |
| `deal_amount` | float64 | 成交额 |
| `buyer` | string | 买方 |
| `seller` | string | 卖方 |
| `premium_ratio` | float64 | 溢价率 |

---

### 2.2 Snapshot Layer (7 表)

#### 实时快照 (spot_snapshot)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `date` | date | 日期 |
| `price` | float64 | 最新价 |
| `change_pct` | float64 | 涨跌幅 |
| `volume` | float64 | 成交量 |
| `amount` | float64 | 成交额 |
| `turnover_rate` | float64 | 换手率 |
| `pe` | float64 | 市盈率 |
| `pb` | float64 | 市净率 |
| `market_cap` | float64 | 市值 |

#### 板块资金流向快照 (sector_flow_snapshot)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `date` | date | 日期 |
| `sector_name` | string | 板块名称 |
| `sector_type` | string | 板块类型 |
| `change_pct` | float64 | 涨跌幅 |
| `net_inflow` | float64 | 净流入 |
| `stock_count` | int64 | 股票数 |

#### 热门排行 (hot_rank)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `rank` | int64 | 排名 |
| `symbol` | string | 股票代码 |
| `name` | string | 名称 |
| `price` | float64 | 价格 |
| `pct_change` | float64 | 涨跌幅 |
| `date` | date | 日期 |

---

### 2.3 Minute Layer (2 表)

#### 分钟线 (stock_minute / etf_minute)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 代码 |
| `datetime` | timestamp | 时间戳 |
| `period` | string | 周期 |
| `adjust` | string | 复权类型 (仅股票) |
| `open` | float64 | 开盘价 |
| `high` | float64 | 最高价 |
| `low` | float64 | 最低价 |
| `close` | float64 | 收盘价 |
| `volume` | float64 | 成交量 |
| `amount` | float64 | 成交额 |

---

### 2.4 Meta Layer (15 表)

#### 证券列表 (securities)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 代码 |
| `name` | string | 名称 |
| `type` | string | 类型 |
| `list_date` | date | 上市日期 |
| `delist_date` | date | 退市日期 |
| `exchange` | string | 交易所 |

#### 交易日历 (trade_calendar)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `date` | date | 日期 |
| `is_trading_day` | bool | 是否交易日 |

#### 行业列表 (industry_list)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `industry_code` | string | 行业代码 |
| `industry_name` | string | 行业名称 |
| `source` | string | 数据来源 |

#### 概念列表 (concept_list)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `concept_code` | string | 概念代码 |
| `concept_name` | string | 概念名称 |
| `source` | string | 数据来源 |

#### 公司信息 (company_info)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `name` | string | 名称 |
| `industry` | string | 行业 |
| `area` | string | 地区 |
| `list_date` | date | 上市日期 |
| `market` | string | 市场 |

#### 公司管理层 (company_management)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `name` | string | 姓名 |
| `title` | string | 职位 |
| `age` | int64 | 年龄 |
| `education` | string | 学历 |
| `hold_shares` | float64 | 持股数 |

#### 历史名称 (name_history)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `symbol` | string | 股票代码 |
| `old_name` | string | 旧名称 |
| `new_name` | string | 新名称 |
| `change_date` | date | 变更日期 |

---

### 2.5 Macro Layer (8 表)

#### Shibor利率 (shibor_rate)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `date` | date | 日期 |
| `on` | float64 | 隔夜 |
| `1w` | float64 | 1周 |
| `2w` | float64 | 2周 |
| `1m` | float64 | 1月 |
| `3m` | float64 | 3月 |
| `6m` | float64 | 6月 |
| `9m` | float64 | 9月 |
| `1y` | float64 | 1年 |

#### GDP数据 (macro_gdp)

| 字段名 | 数据类型 | 中文名 |
|--------|----------|--------|
| `date` | date | 日期 |
| `gdp` | float64 | GDP |
| `gdp_yoy` | float64 | GDP同比 |
| `primary_industry` | float64 | 第一产业 |
| `secondary_industry` | float64 | 第二产业 |
| `tertiary_industry` | float64 | 第三产业 |

---

## 3. Field Mapping 映射表 (`core/fields.py`)

### 3.1 中文→英文标准映射 (CN_TO_EN)

| 中文原名 | 英文映射名 | 数据类型 |
|----------|-----------|----------|
| 日期 | datetime | date |
| 开盘 | open | float |
| 最高 | high | float |
| 最低 | low | float |
| 收盘 | close | float |
| 成交量 | volume | float |
| 成交额 | amount | float |
| 振幅 | amplitude | float |
| 涨跌幅 | pct_chg | float |
| 涨跌额 | change | float |
| 换手率 | turnover | float |
| 涨停价 | limit_up | float |
| 跌停价 | limit_down | float |
| 昨收 | pre_close | float |
| 今开 | open | float |
| 最高价 | high | float |
| 最低价 | low | float |
| 收盘价 | close | float |
| 名称 | name | string |
| 代码 | symbol | string |
| 股票代码 | symbol | string |
| 证券代码 | symbol | string |
| 品种代码 | symbol | string |
| 成分券代码 | symbol | string |
| 成分股代码 | symbol | string |
| 权重 | weight | float |
| 占比 | weight | float |
| 持仓量 | openinterest | float |
| 结算价 | settle | float |
| 时间 | datetime | string |
| trade_date | datetime | string |
| vol | volume | float |
| turn | turnover | float |
| pctChg | pct_chg | float |
| preclose | pre_close | float |
| adjustflag | adjust_flag | string |
| tradestatus | trade_status | string |

### 3.2 多源字段映射 (FIELD_MAPS)

#### Eastmoney 源

| 原字段 | 映射字段 |
|--------|---------|
| 日期 | datetime |
| 开盘 | open |
| 最高 | high |
| 最低 | low |
| 收盘 | close |
| 成交量 | volume |
| 成交额 | amount |
| 振幅 | amplitude |
| 涨跌幅 | pct_chg |
| 涨跌额 | change |
| 换手率 | turnover |

#### Tushare 源

| 原字段 | 映射字段 |
|--------|---------|
| trade_date | datetime |
| ts_code | symbol |
| pre_close | pre_close |
| change | change |
| pct_chg | pct_chg |
| vol | volume |

#### Baostock 源

| 原字段 | 映射字段 |
|--------|---------|
| date | datetime |
| code | symbol |
| preclose | pre_close |
| adjustflag | adjust_flag |
| turn | turnover |
| tradestatus | trade_status |
| pctChg | pct_chg |

#### Options Chain 源

| 原字段 | 映射字段 |
|--------|---------|
| 期权代码 | option_code |
| 标的代码 | underlying_code |
| 到期日 | expiration_date |
| 行权价 | strike_price |
| 期权类型 | option_type |
| 昨持仓 | open_interest |
| 最新价 | close |
| 买价 | bid |
| 卖价 | ask |
| 内涵价值 | intrinsic_value |
| 时间价值 | time_value |

---

## 4. Interface Definitions 输出字段 (config/interfaces/*.yaml)

### 4.1 Equity 接口 (`equity.yaml`)

| 接口名 | 输出字段 |
|--------|---------|
| equity_daily | date, open, high, low, close, volume, amount |
| equity_minute | datetime, open, high, low, close, volume, amount |
| equity_realtime | symbol, name, price, change, pct_change, volume, amount, open, high, low, prev_close |
| securities_list | symbol, name |
| block_deal | datetime, symbol, name, price, volume, amount, direction, pct_change, change |
| suspended_stocks | symbol, name, suspend_date, resume_date, suspend_reason |
| st_stocks | symbol, name |
| security_info | symbol, name, industry, list_date |
| industry_stocks | symbol, name, sw_level1, sw_level2, sw_level3, price, pe, pe_ttm, pb, dividend_yield, market_cap |
| industry_list | industry_code, industry_name, count, pe_static, pe_ttm, pb, dividend_yield |
| finance_indicator | report_date, basic_eps, roe, net_profit_margin, gross_profit_margin, debt_ratio, total_revenue, net_profit |

### 4.2 Index 接口 (`index.yaml`)

| 接口名 | 输出字段 |
|--------|---------|
| index_daily | date, open, high, low, close, volume, amount |
| index_components | - (动态) |
| index_list | - (动态) |

### 4.3 Futures 接口 (`futures.yaml`)

| 接口名 | 输出字段 |
|--------|---------|
| futures_daily | date, open, high, low, close, volume, open_interest |
| futures_realtime | symbol, name, price, open, high, low, prev_close, volume, open_interest, change, pct_change |
| futures_main_contracts | symbol, name, exchange, variety |

### 4.4 Options 接口 (`options.yaml`)

| 接口名 | 输出字段 |
|--------|---------|
| options_realtime | symbol, underlying, option_type, strike, expiration, price, volume, open_interest |
| option_sse_daily_sina | date, open, high, low, close, volume |

### 4.5 Fund 接口 (`fund.yaml`)

| 接口名 | 输出字段 |
|--------|---------|
| etf_daily | date, open, high, low, close, volume, amount |
| fund_net_value | date, nav, acc_nav |
| fund_manager_info | seq, name, company, fund_code, fund_name, tenure_days, asset_scale, best_return |
| etf_list | symbol, name |
| lof_list | symbol, name |

### 4.6 Bond 接口 (`bond.yaml`)

| 接口名 | 输出字段 |
|--------|---------|
| convert_bond_premium | symbol, name, price, premium_rate |

### 4.7 Macro 接口 (`macro.yaml`)

| 接口名 | 输出字段 |
|--------|---------|
| macro_cpi | date, cpi |
| macro_gdp | date, gdp |
| macro_pmi | date, pmi |
| macro_lpr | date, one_year, five_year |
| macro_ppi | date, ppi |
| macro_m2 | date, m2 |

---

## 5. 同义/重复字段分析

### 5.1 同义字段组

| 标准字段名 | 同义字段列表 | 来源 |
|-----------|-------------|------|
| `symbol` | 代码, 股票代码, 证券代码, 品种代码, 成分券代码, 成分股代码, ts_code, code | 多源 |
| `date` | 日期, trade_date, datetime, day | 多源 |
| `datetime` | 时间, 日期, trade_date, day | 多源 |
| `open` | 开盘, 开盘价, 今开 | 多源 |
| `close` | 收盘, 收盘价, 最新价 | 多源 |
| `volume` | 成交量, vol, 成交量(手) | 多源 |
| `amount` | 成交额, 成交额(元) | 多源 |
| `pct_chg` | 涨跌幅, pct_change, changepercent, pctChg | 多源 |
| `pre_close` | 昨收, settlement, prev_close, preclose | 多源 |
| `turnover` | 换手率, turn | 多源 |
| `open_interest` | 持仓量, openinterest, 昨持仓 | 多源 |
| `weight` | 权重, 占比 | 多源 |
| `stock_name` | 成分券名称, 成分股名称, 品种名称, name | 多源 |

### 5.2 建议统一字段名

| 领域 | 推荐标准字段 | 舍弃别名 |
|------|-------------|---------|
| 标识 | `symbol` | code, ts_code, 股票代码 |
| 时间 | `date` (日线) / `datetime` (分钟) | trade_date, day, 日期 |
| OHLC | `open`, `high`, `low`, `close` | 开盘, 最高, 最低, 收盘 |
| 量价 | `volume`, `amount` | vol, 成交量(手), 成交额(元) |
| 变化 | `pct_chg` (涨跌幅) / `change` (涨跌额) | pct_change, 涨跌额, pctChg |
| 估值 | `pe`, `pb`, `ps` | PE, PB, PS |
| 市值 | `market_cap` | 市值, 总市值 |
| 持仓 | `open_interest` | 持仓量, openinterest |
| 权重 | `weight` | 占比, 权重比例 |

---

## 6. 字段类型统计

| 类型 | 字段数 | 典型字段 |
|------|--------|---------|
| string | 80+ | symbol, name, adjust, holder_name, reason, industry |
| float64 | 150+ | open, high, low, close, volume, amount, pe, pb, market_cap |
| date | 30+ | date, report_date, announce_date, list_date |
| timestamp | 5 | datetime (分钟线) |
| bool | 3 | is_trading_day |
| int64 | 10+ | rank, age, level, stock_count |

---

## 7. 高频字段使用频率

| 字段名 | 使用表数 | 使用接口数 | 优先级 |
|--------|---------|-----------|-------|
| `symbol` | 69 | 50+ | P0 |
| `date` | 45 | 30+ | P0 |
| `open` | 20+ | 15+ | P0 |
| `close` | 20+ | 15+ | P0 |
| `volume` | 20+ | 15+ | P0 |
| `amount` | 18+ | 12+ | P1 |
| `name` | 15+ | 20+ | P1 |
| `pe` | 8+ | 5+ | P1 |
| `pb` | 8+ | 5+ | P1 |
| `change_pct` / `pct_chg` | 10+ | 10+ | P1 |

---

## 8. 问题字段识别

### 8.1 命名不一致

| 问题 | 示例 | 建议 |
|------|------|------|
| 中英混杂 | `pct_chg` vs `change_pct` | 统一为 `pct_chg` |
| 同义词多 | `symbol` 有 10+ 别名 | 统一为 `symbol` |
| 大小写不一 | `PE` vs `pe` | 统一小写 |
| 后缀冗余 | `open_price` vs `open` | 移除 `_price` 后缀 |

### 8.2 类型不一致

| 字段 | YAML 类型 | Python 类型 | 建议 |
|------|----------|-------------|------|
| `volume` | float64 | int (部分源) | 统一 float64 |
| `amount` | float64 | int (部分源) | 统一 float64 |
| `rank` | int64 | int | 统一 int64 |

---

## 9. 后续建议

1. **字段标准化**: 参考 Section 5.2 统一所有字段名
2. **类型统一**: 所有数值字段使用 `float64`，避免精度问题
3. **映射表完善**: 补充 AkShare 原生字段 → 标准字段映射
4. **文档同步**: 更新 `schemas.yaml` 与 `schema.py` 保持一致

---

**文档生成日期**: 2026-04-22  
**扫描文件**: schemas.yaml, schema.py, fields.py, interfaces/*.yaml, lixinger_source.py, akshare_source.py  
**总表数**: 69  
**总字段数**: 约 300+  
**同义字段组**: 15+