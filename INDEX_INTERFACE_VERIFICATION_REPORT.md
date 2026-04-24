# 指数接口 Akshare 原始实现与配置文件映射对比报告

生成时间: 2026-04-24
检查范围: 13个指数相关接口

---

## 一、函数存在性检查

| 序号 | 函数名 | 中文名称 | 存在性 |
|------|--------|----------|--------|
| 1 | stock_zh_index_spot_em | A股指数实时 | ✓ 存在 |
| 2 | stock_zh_index_spot | A股指数-Sina | ✗ 不存在 |
| 3 | index_zh_a_hist | A股指数历史 | ✓ 存在 |
| 4 | index_stock_hist | 指数历史 | ✗ 不存在 |
| 5 | index_stock_cons_csindex | 中证指数成分 | ✓ 存在 |
| 6 | index_stock_cons_weight_csindex | 指数权重 | ✓ 存在 |
| 7 | stock_zh_index_value_csindex | 指数估值 | ✓ 存在 |
| 8 | sw_index_first_info | 申万行业指数 | ✓ 存在 |
| 9 | sw_index_third_cons | 申万成分股 | ✓ 存在 |
| 10 | index_global_hist_sina | 全球指数-Sina | ✓ 存在 |
| 11 | index_global_hist_em | 全球指数-EM | ✓ 存在 |
| 12 | index_global_spot_em | 全球指数实时 | ✓ 存在 |
| 13 | index_global_name_table | 全球指数列表 | ✓ 存在 |

**统计**: 存在 11个，不存在 2个

---

## 二、详细对比分析

### 1. stock_zh_index_spot_em (A股指数实时)

#### Akshare 实现
```python
函数签名: stock_zh_index_spot_em(symbol: str = '上证系列指数') -> DataFrame
参数:
  - symbol: str, 默认='上证系列指数'
返回列: 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 振幅, 最高, 最低, 今开, 昨收, 量比
```

#### 配置文件映射 (index_list)
**位置**: config/interfaces/index.yaml (line 81-112)

| 项目 | 配置值 | 状态 |
|------|--------|------|
| 映射函数 | stock_zh_index_spot_em | ✓ 正确 |
| 输入映射 | symbol → symbol | ✓ 正确 |
| 输出映射 | 代码→symbol, 名称→name, 最新价→close, 涨跌幅→change_pct, 涨跌额→change, 成交量→volume, 成交额→amount, 振幅→amplitude, 最高→high, 最低→low, 今开→open, 昨收→prev_close, 量比→volume_ratio | ✓ 正确 |

**结论**: ✅ 配置正确

---

### 2. stock_zh_index_spot (A股指数-Sina)

**Akshare 实现**: ✗ 函数不存在

**配置文件映射**: ✗ 未在配置文件中找到

**结论**: ❌ 函数不存在，无法配置

---

### 3. index_zh_a_hist (A股指数历史)

#### Akshare 实现
```python
函数签名: index_zh_a_hist(
    symbol: str = '000859', 
    period: str = 'daily', 
    start_date: str = '19700101', 
    end_date: str = '22220101'
) -> DataFrame

参数:
  - symbol: str, 默认='000859' (指数代码)
  - period: str, 默认='daily' (daily/weekly/monthly)
  - start_date: str, 默认='19700101' (格式: YYYYMMDD)
  - end_date: str, 默认='22220101' (格式: YYYYMMDD)

返回列: 日期, 开盘, 最高, 最低, 收盘, 成交量, 成交额
```

#### 配置文件映射 (index_daily)
**位置**: config/interfaces/index.yaml (line 4-53)

| 项目 | 配置值 | 状态 |
|------|--------|------|
| 映射函数 | index_zh_a_hist | ✓ 正确 |
| 输入参数 | symbol, period, start_date, end_date | ✓ 正确 |
| 输入映射 | symbol→symbol, period→period, start_date→start_date, end_date→end_date | ✓ 正确 |
| 参数转换 | start_date: YYYYMMDD, end_date: YYYYMMDD | ✓ 正确 |
| 输出映射 | 日期→date, 开盘→open, 最高→high, 最低→low, 收盘→close, 成交量→volume, 成交额→amount | ✓ 正确 |

**结论**: ✅ 配置正确

---

### 4. index_stock_hist (指数历史)

**Akshare 实现**: ✗ 函数不存在

**配置文件映射**: ✗ 未在配置文件中找到

**结论**: ❌ 函数不存在，无法配置

---

### 5. index_stock_cons_csindex (中证指数成分)

#### Akshare 实现
```python
函数签名: index_stock_cons_csindex(symbol: str = '000300') -> DataFrame
参数:
  - symbol: str, 默认='000300' (指数代码)
返回列: 日期, 指数代码, 指数名称, 指数英文名称, 成分券代码, 成分券名称, 
        成分券英文名称, 交易所, 交易所英文名称
```

#### 配置文件映射 (index_components)
**位置**: config/interfaces/index.yaml (line 55-80)

| 项目 | 配置值 | 状态 |
|------|--------|------|
| 映射函数 | index_stock_cons_csindex | ✓ 正确 |
| 输入映射 | symbol → symbol | ✓ 正确 |
| 输出映射 | 日期→date, 指数代码→index_code, 指数名称→index_name, 成分券代码→symbol, 成分券名称→name, 交易所→exchange | ⚠️ 部分正确 |
| 缺失字段 | 指数英文名称, 成分券英文名称, 交易所英文名称 | ❌ 未映射 |

**结论**: ⚠️ 配置部分正确，缺少英文名称字段映射

---

### 6. index_stock_cons_weight_csindex (指数权重)

#### Akshare 实现
```python
函数签名: index_stock_cons_weight_csindex(symbol: str = '000300') -> DataFrame
参数:
  - symbol: str, 默认='000300' (指数代码)
返回列: 日期, 指数代码, 指数名称, 指数英文名称, 成分券代码, 成分券名称, 
        成分券英文名称, 交易所, 交易所英文名称, 权重
```

#### 配置文件映射
**状态**: ❌ 未在配置文件中找到独立配置

**问题**:
- 配置文件中 `index_weights` (line 141-166) 使用了 `index_stock_cons_csindex` 函数
- `index_stock_cons_csindex` 不返回权重字段
- 应该使用 `index_stock_cons_weight_csindex` 才能获取权重数据

**结论**: ❌ 配置错误，使用了错误的函数

**建议修复**:
```yaml
index_weights:
  sources:
    - name: "akshare_csindex"
      func: "index_stock_cons_weight_csindex"  # 修改为正确的函数
      enabled: true
      input_mapping:
        symbol: "symbol"
      output_mapping:
        日期: date
        指数代码: index_code
        成分券代码: symbol
        成分券名称: name
        权重: weight  # 添加权重字段
```

---

### 7. stock_zh_index_value_csindex (指数估值)

#### Akshare 实现
```python
函数签名: stock_zh_index_value_csindex(symbol: str = 'H30374') -> DataFrame
参数:
  - symbol: str, 默认='H30374' (指数代码)
返回列: 日期, 指数代码, 指数中文全称, 指数中文简称, 指数英文全称, 
        指数英文简称, 市盈率1, 市盈率2, 股息率1, 股息率2
```

#### 配置文件映射 (index_valuation)
**位置**: config/interfaces/index.yaml (line 114-139)

| 项目 | 配置值 | 状态 |
|------|--------|------|
| 映射函数 | stock_zh_index_value_csindex | ✓ 正确 |
| 输入参数定义 | index_code | ⚠️ 与akshare参数名不一致 |
| 输入映射 | index_code → symbol | ✓ 映射正确 |
| 输出映射 | 日期→date, 指数代码→index_code, 指数中文简称→index_name, 市盈率1→pe, 市盈率2→pe_2, 股息率1→dividend_yield, 股息率2→dividend_yield_2 | ⚠️ 部分正确 |
| 缺失字段 | 指数中文全称, 指数英文全称, 指数英文简称 | ❌ 未映射 |

**问题**:
1. 输入参数名不一致: 配置定义为 `index_code`，akshare使用 `symbol`
2. 输出映射不完整，缺少英文名称字段

**结论**: ⚠️ 配置部分正确，参数名不一致，缺少部分字段映射

---

### 8. sw_index_first_info (申万行业指数)

#### Akshare 实现
```python
函数签名: sw_index_first_info() -> DataFrame
参数: 无
返回列: 行业代码, 行业名称, 成份个数, 静态市盈率, TTM(滚动)市盈率, 市净率, 静态股息率
```

#### 配置文件映射
**状态**: ❌ 未在配置文件中找到

**结论**: ❌ 未配置

---

### 9. sw_index_third_cons (申万成分股)

#### Akshare 实现
```python
函数签名: sw_index_third_cons(symbol: str = '801120.SI') -> DataFrame
参数:
  - symbol: str, 默认='801120.SI' (三级申万行业代码)
返回列: 序号, 股票代码, 股票简称, 纳入时间, 申万1级, 申万2级, 申万3级, 
        价格, 市盈率, 市盈率ttm, 市净率, 股息率, 市值, 
        归母净利润同比增长(09-30), 归母净利润同比增长(06-30), 
        营业收入同比增长(09-30), 营业收入同比增长(06-30)
```

#### 配置文件映射
**状态**: ❌ 未在配置文件中找到

**结论**: ❌ 未配置

---

### 10. index_global_hist_sina (全球指数-Sina)

#### Akshare 实现
```python
函数签名: index_global_hist_sina(symbol: str = 'OMX') -> DataFrame
参数:
  - symbol: str, 默认='OMX' (指数代码)
返回列: (无法验证，symbol格式不明确)
```

#### 配置文件映射
**状态**: ❌ 未在配置文件中找到

**结论**: ❌ 未配置

**注意**: 该接口的symbol参数格式需要进一步研究，测试中无法成功调用

---

### 11. index_global_hist_em (全球指数-EM)

#### Akshare 实现
```python
函数签名: index_global_hist_em(symbol: str = '美元指数') -> DataFrame
参数:
  - symbol: str, 默认='美元指数' (指数名称，非代码)
返回列: 日期, 代码, 名称, 今开, 最新价, 最高, 最低, 振幅
```

#### 配置文件映射
**状态**: ❌ 未在配置文件中找到

**结论**: ❌ 未配置

---

### 12. index_global_spot_em (全球指数实时)

#### Akshare 实现
```python
函数签名: index_global_spot_em() -> DataFrame
参数: 无
返回列: (网络问题无法获取)
```

#### 配置文件映射
**状态**: ❌ 未在配置文件中找到

**结论**: ❌ 未配置

---

### 13. index_global_name_table (全球指数列表)

#### Akshare 实现
```python
函数签名: index_global_name_table() -> DataFrame
参数: 无
返回列: 指数名称, 代码
```

#### 配置文件映射
**状态**: ❌ 未在配置文件中找到

**结论**: ❌ 未配置

---

## 三、配置文件中的问题汇总

### 问题1: index_weights 配置错误

**位置**: config/interfaces/index.yaml (line 141-166)

**问题描述**:
- 使用了 `index_stock_cons_csindex` 函数，但该函数**不返回权重字段**
- 应该使用 `index_stock_cons_weight_csindex` 函数

**影响**: 无法获取正确的权重数据

**修复建议**:
```yaml
index_weights:
  sources:
    - name: "akshare_csindex"
      func: "index_stock_cons_weight_csindex"  # 修改此处
      enabled: true
      input_mapping:
        symbol: "symbol"
      output_mapping:
        日期: date
        指数代码: index_code
        成分券代码: symbol
        成分券名称: name
        权重: weight  # 添加此字段
```

### 问题2: index_weights_history 配置错误

**位置**: config/interfaces/index.yaml (line 168-192)

**问题描述**:
- 同样使用了 `index_stock_cons_csindex` 函数
- `index_stock_cons_csindex` 只返回最新成分，不返回历史权重

**影响**: 无法获取正确的权重历史数据

**修复建议**: 同上，需要使用 `index_stock_cons_weight_csindex` 函数

### 问题3: index_components 缺少英文字段映射

**位置**: config/interfaces/index.yaml (line 55-80)

**问题描述**:
- `index_stock_cons_csindex` 返回9个字段
- 配置只映射了6个字段
- 缺少: 指数英文名称, 成分券英文名称, 交易所英文名称

**影响**: 英文名称数据丢失

### 问题4: index_valuation 参数名不一致

**位置**: config/interfaces/index.yaml (line 114-139)

**问题描述**:
- 配置定义的输入参数名为 `index_code`
- akshare函数参数名为 `symbol`
- 虽然映射正确，但参数定义不一致可能引起混淆

**修复建议**:
```yaml
input:
  - {name: "symbol", type: "str", required: true, desc: "指数代码，如 H30374"}
```

---

## 四、统计汇总

| 分类 | 数量 | 百分比 |
|------|------|--------|
| 总函数数 | 13 | 100% |
| 函数存在 | 11 | 84.6% |
| 函数不存在 | 2 | 15.4% |
| 已配置且正确 | 2 | 15.4% |
| 已配置但有问题 | 3 | 23.1% |
| 未配置 | 7 | 53.8% |

### 详细统计

- **✅ 配置正确**: 2个
  - stock_zh_index_spot_em
  - index_zh_a_hist

- **⚠️ 配置部分正确**: 2个
  - index_components (缺少英文字段映射)
  - index_valuation (参数名不一致，缺少英文字段映射)

- **❌ 配置错误**: 2个
  - index_weights (使用了错误的函数)
  - index_weights_history (使用了错误的函数)

- **❌ 未配置**: 7个
  - index_stock_cons_weight_csindex
  - sw_index_first_info
  - sw_index_third_cons
  - index_global_hist_sina
  - index_global_hist_em
  - index_global_spot_em
  - index_global_name_table

- **❌ 函数不存在**: 2个
  - stock_zh_index_spot
  - index_stock_hist

---

## 五、建议配置补充

### 1. 新增: sw_index_first_info (申万行业指数)

```yaml
sw_index_first_level:
  name: "sw_index_first_level"
  category: "index"
  description: "申万一级行业指数信息"

  input: []

  output: []

  rate_limit_key: "default"

  sources:
    - name: "akshare_legulegu"
      func: "sw_index_first_info"
      enabled: true
      input_mapping: {}
      output_mapping:
        行业代码: industry_code
        行业名称: industry_name
        成份个数: component_count
        静态市盈率: pe
        TTM(滚动)市盈率: pe_ttm
        市净率: pb
        静态股息率: dividend_yield
```

### 2. 新增: sw_index_third_cons (申万成分股)

```yaml
sw_index_third_components:
  name: "sw_index_third_components"
  category: "index"
  description: "申万三级行业成分股"

  input:
    - {name: "symbol", type: "str", required: true, desc: "三级申万行业代码"}

  output: []

  rate_limit_key: "default"

  sources:
    - name: "akshare_legulegu"
      func: "sw_index_third_cons"
      enabled: true
      input_mapping:
        symbol: "symbol"
      output_mapping:
        序号: seq
        股票代码: symbol
        股票简称: name
        纳入时间: include_date
        申万1级: sw_level1
        申万2级: sw_level2
        申万3级: sw_level3
        价格: price
        市盈率: pe
        市盈率ttm: pe_ttm
        市净率: pb
        股息率: dividend_yield
        市值: market_cap
```

### 3. 新增: index_global_name_table (全球指数列表)

```yaml
index_global_list:
  name: "index_global_list"
  category: "index"
  description: "全球指数名称代码列表"

  input: []

  output: []

  rate_limit_key: "default"

  sources:
    - name: "akshare_sina"
      func: "index_global_name_table"
      enabled: true
      input_mapping: {}
      output_mapping:
        指数名称: name
        代码: symbol
```

### 4. 新增: index_global_hist_em (全球指数历史-EM)

```yaml
index_global_daily_em:
  name: "index_global_daily_em"
  category: "index"
  description: "全球指数历史数据(东方财富)"

  input:
    - {name: "symbol", type: "str", required: true, desc: "指数名称，如'道琼斯'"}

  output: []

  rate_limit_key: "default"

  sources:
    - name: "akshare_em"
      func: "index_global_hist_em"
      enabled: true
      input_mapping:
        symbol: "symbol"
      output_mapping:
        日期: date
        代码: symbol
        名称: name
        今开: open
        最新价: close
        最高: high
        最低: low
        振幅: amplitude
```

---

## 六、修复优先级建议

### 高优先级 (影响数据准确性)
1. **修复 index_weights 配置** - 使用错误的函数导致无法获取权重数据
2. **修复 index_weights_history 配置** - 同上

### 中优先级 (完善功能)
3. **补充 index_components 的英文字段映射** - 避免数据丢失
4. **统一 index_valuation 的参数命名** - 提高一致性
5. **新增 index_stock_cons_weight_csindex 配置** - 提供独立的权重查询接口

### 低优先级 (功能扩展)
6. **新增 sw_index_first_info 配置** - 申万行业指数
7. **新增 sw_index_third_cons 配置** - 申万成分股
8. **新增全球指数相关配置** - index_global_hist_em, index_global_spot_em, index_global_name_table

---

## 七、附录: Akshare函数签名汇总

```python
# A股指数
stock_zh_index_spot_em(symbol: str = '上证系列指数') -> DataFrame
index_zh_a_hist(symbol: str = '000859', period: str = 'daily', 
                start_date: str = '19700101', end_date: str = '22220101') -> DataFrame

# 指数成分
index_stock_cons_csindex(symbol: str = '000300') -> DataFrame
index_stock_cons_weight_csindex(symbol: str = '000300') -> DataFrame
stock_zh_index_value_csindex(symbol: str = 'H30374') -> DataFrame

# 申万指数
sw_index_first_info() -> DataFrame
sw_index_third_cons(symbol: str = '801120.SI') -> DataFrame

# 全球指数
index_global_hist_sina(symbol: str = 'OMX') -> DataFrame
index_global_hist_em(symbol: str = '美元指数') -> DataFrame
index_global_spot_em() -> DataFrame
index_global_name_table() -> DataFrame
```
