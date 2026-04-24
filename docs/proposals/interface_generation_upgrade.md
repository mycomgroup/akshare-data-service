# 接口配置生成质量提升方案

## 问题总结

### 当前生成质量问题

| 问题类型 | 数量 | 占比 | 影响 |
|---------|------|------|------|
| TODO 标记 | 2,768 | 33% | 需人工审核 |
| 空 output_mapping | 664 | 7.9% | 无法使用 |
| 空 input | 493 | 5.9% | 参数不明 |
| 空 output | 227 | 2.7% | 返回不明 |
| 自动生成标记 | 847 | 10.1% | 可信度低 |

### 根本原因

1. **扫描器信息不足**：只提取函数名和参数名，未提取类型、默认值、文档
2. **缺少运行时探测**：未实际调用函数获取返回数据结构
3. **缺少语义推断**：字段名使用原始中文名，缺少业务语义映射
4. **配置分离**：generated 和手动配置未合并

---

## 改进方案

### 方案一：增强扫描器（提取完整签名）

**目标**：从 akshare 函数中提取完整信息

**改进点**：
```python
# 当前：只提取参数名
signature = ["symbol", "start_date", "end_date"]

# 改进后：提取类型、默认值、文档
signature = [
    {
        "name": "symbol",
        "type": "str",
        "required": true,
        "default": null,
        "doc": "股票代码，如 sh600000"
    },
    {
        "name": "start_date",
        "type": "str",
        "required": false,
        "default": "19700101",
        "doc": "开始日期，格式 YYYYMMDD"
    }
]
```

**实现方式**：
1. 使用 `inspect.signature()` 提取参数类型和默认值
2. 解析 docstring 提取参数说明（`:param symbol: xxx`）
3. 使用 `typing.get_type_hints()` 获取类型提示

**预期效果**：
- input 字段完整性：从 0% → 80%
- 类型推断准确率：从 30% → 70%

---

### 方案二：运行时探测（调用函数获取 schema）

**目标**：实际调用函数，获取返回数据结构

**策略**：
1. **安全探测**：只调用无参数或参数有默认值的函数
2. **采样探测**：对于需要参数的函数，使用示例参数（如 "000001"）
3. **批量探测**：并发调用，限速保护

**实现**：
```python
def probe_function(func_name: str, func: Callable) -> Dict:
    """探测函数返回结构"""
    try:
        # 1. 尝试无参数调用
        df = func()
        return extract_schema(df)
    except:
        # 2. 使用示例参数
        try:
            df = func(symbol="000001")
            return extract_schema(df)
        except:
            return None

def extract_schema(df: DataFrame) -> List[Dict]:
    """从 DataFrame 提取字段结构"""
    return [
        {
            "name": col,
            "type": infer_pandas_type(df[col]),
            "sample_values": df[col].head(3).tolist(),
            "null_rate": df[col].isna().sum() / len(df)
        }
        for col in df.columns
    ]
```

**预期效果**：
- output 字段完整性：从 0% → 60%
- output_mapping 准确率：从 20% → 80%

---

### 方案三：AI 语义推断（LLM 生成字段名）

**目标**：将中文列名转换为业务语义字段名

**策略**：
1. **规则匹配**：建立常用字段映射字典
   ```python
   FIELD_MAPPING = {
       "日期": "date",
       "开盘": "open",
       "收盘": "close",
       "成交量": "volume",
       "股票代码": "symbol",
       "转债代码": "bond_code",
   }
   ```

2. **LLM 推断**：对于未匹配的字段，使用 LLM 推断
   ```python
   prompt = f"""
   将以下中文字段名转换为英文业务字段名：
   - 原字段：{chinese_name}
   - 上下文：{function_description}
   - 数据类型：{dtype}
   - 示例值：{sample_values}

   要求：
   1. 使用 snake_case 命名
   2. 语义化，便于理解
   3. 符合金融数据惯例

   返回：字段名和说明
   """
   ```

**预期效果**：
- 字段名语义化率：从 0% → 90%
- 人工审核工作量：减少 70%

---

### 方案四：智能合并（升级手动配置）

**目标**：用生成的信息补充手动配置

**策略**：
1. **按函数名匹配**：找到手动配置中使用的 akshare 函数
2. **对比字段**：检查 input/output 是否完整
3. **补充缺失字段**：从 generated 中提取补充
4. **验证类型**：对比类型推断是否一致
5. **生成报告**：人工审核差异

**实现**：
```python
def upgrade_manual_config(manual: Dict, generated: Dict) -> Tuple[Dict, List[str]]:
    """升级手动配置"""
    changes = []
    
    for interface_name, interface_config in manual.items():
        # 1. 找到对应的 generated 接口
        func_name = extract_akshare_func(interface_config)
        gen_interface = find_in_generated(func_name, generated)
        
        if not gen_interface:
            continue
        
        # 2. 补充缺失的 input 字段
        missing_inputs = find_missing_fields(
            interface_config.get("input", []),
            gen_interface.get("input", [])
        )
        if missing_inputs:
            interface_config["input"].extend(missing_inputs)
            changes.append(f"{interface_name}: added {len(missing_inputs)} input fields")
        
        # 3. 补充缺失的 output 字段
        missing_outputs = find_missing_fields(
            interface_config.get("output", []),
            gen_interface.get("output", [])
        )
        if missing_outputs:
            interface_config["output"].extend(missing_outputs)
            changes.append(f"{interface_name}: added {len(missing_outputs)} output fields")
        
        # 4. 验证类型一致性
        type_conflicts = check_type_conflicts(
            interface_config,
            gen_interface
        )
        if type_conflicts:
            changes.append(f"{interface_name}: type conflicts - {type_conflicts}")
    
    return manual, changes
```

**预期效果**：
- 手动配置完整性：从 60% → 95%
- 类型错误率：从 10% → 2%

---

## 实施步骤

### 阶段一：工具开发（1周）

1. **增强扫描器** (`scanner_v2.py`)
   - 提取完整签名信息
   - 解析 docstring 参数说明
   - 推断参数类型

2. **运行时探测器** (`runtime_prober.py`)
   - 安全调用策略
   - DataFrame schema 提取
   - 字段类型推断

3. **语义推断器** (`semantic_inferrer.py`)
   - 字段名映射字典
   - LLM 推断接口
   - 批量处理优化

4. **配置合并器** (`config_merger.py`)
   - 智能匹配策略
   - 字段补充逻辑
   - 冲突检测报告

### 阶段二：数据收集（2天）

1. 扫描所有 akshare 函数（8,365个）
2. 探测无参数函数（估计 500+）
3. 采样探测有参数函数（估计 1,000）
4. 生成高质量骨架

### 阶段三：配置升级（3天）

1. 运行合并器升级手动配置
2. 生成差异报告
3. 人工审核关键差异
4. 应用审核后的配置

### 阶段四：验证与优化（2天）

1. 单元测试验证配置正确性
2. 实际调用测试
3. 性能优化
4. 文档更新

---

## 预期成果

### 量化指标

| 指标 | 当前 | 目标 | 提升 |
|-----|------|------|------|
| 配置覆盖率 | 10.2% | 80% | +70% |
| input 完整性 | 60% | 95% | +35% |
| output 完整性 | 50% | 90% | +40% |
| 字段语义化 | 30% | 85% | +55% |
| 人工审核工作量 | 100% | 20% | -80% |

### 质量提升

1. **完整性**：所有接口都有完整的 input/output 定义
2. **准确性**：类型推断基于实际数据，准确率高
3. **语义化**：字段名符合业务惯例，易于理解
4. **可维护性**：统一命名规范，降低维护成本

---

## 工具使用示例

### 1. 增强扫描

```bash
# 扫描所有 akshare 函数
python -m akshare_data.offline.scanner_v2 scan-all

# 输出：config/registry/akshare_enhanced.yaml
```

### 2. 运行时探测

```bash
# 探测无参数函数
python -m akshare_data.offline.runtime_prober probe-safe

# 采样探测有参数函数
python -m akshare_data.offline.runtime_prober probe-sample --limit 1000

# 输出：config/registry/probed_schemas.yaml
```

### 3. 生成高质量骨架

```bash
# 合并扫描和探测结果
python -m akshare_data.offline.generator_v2 generate \
  --scanner config/registry/akshare_enhanced.yaml \
  --prober config/registry/probed_schemas.yaml \
  --output config/interfaces/generated_v2/
```

### 4. 升级手动配置

```bash
# 升级现有手动配置
python -m akshare_data.offline.config_merger upgrade \
  --manual config/interfaces/ \
  --generated config/interfaces/generated_v2/ \
  --output config/interfaces/upgraded/ \
  --report config/reports/upgrade_diff.md
```

### 5. 审核差异

```bash
# 查看差异报告
cat config/reports/upgrade_diff.md

# 示例：
# ## stock_daily
# - Added input fields: 0
# - Added output fields: 3 (amount, turnover_rate, amplitude)
# - Type conflicts: 1 (volume: float -> int)
```

---

## 风险与对策

### 风险1：运行时探测触发限流

**对策**：
- 使用代理池轮换
- 限制并发和频率
- 优先探测低风险接口

### 风险2：LLM 推断成本高

**对策**：
- 建立缓存机制
- 批量处理优化
- 规则匹配优先，LLM 兜底

### 风险3：合并冲突处理

**对策**：
- 保留人工配置优先级
- 生成详细的差异报告
- 提供交互式合并工具

---

## 后续优化

1. **持续学习**：建立字段映射知识库，持续优化
2. **社区贡献**：开放配置库，接受社区审核
3. **自动化测试**：建立 CI/CD 验证配置正确性
4. **文档生成**：自动生成接口文档