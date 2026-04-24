# 接口配置升级工具包

这个工具包用于提升 akshare-data-service 的接口配置质量。

## 工具列表

### 1. 增强扫描器 (`scanner_v2.py`)
提取 akshare 函数的完整信息：
- 参数类型和默认值
- docstring 参数说明
- 类型提示

### 2. 运行时探测器 (`runtime_prober.py`)
实际调用 akshare 函数，获取返回数据结构：
- DataFrame 列名和类型
- 示例数据值
- 字段统计信息

### 3. 语义推断器 (`semantic_inferrer.py`)
将中文字段名转换为英文业务字段名：
- 字段映射字典
- 拼音转换
- LLM 推断接口（可选）

### 4. 配置合并器 (`config_merger.py`)
用生成的信息升级手动配置：
- 补充缺失字段
- 验证类型一致性
- 改进 output_mapping
- 生成差异报告

### 5. 快速升级脚本 (`upgrade_manual_config.py`)
一键升级手动配置的脚本。

## 使用方法

### 快速升级（推荐）

```bash
# 升级手动配置
python docs/proposals/upgrade_manual_config.py \
  --manual-config config/interfaces \
  --output config/upgraded \
  --probe-limit 100

# 输出：
# - config/upgraded/scanned_enhanced.yaml  （扫描结果）
# - config/upgraded/probed_schemas.yaml    （探测结果）
# - config/upgraded/generated_enhanced.yaml（生成的骨架）
# - config/upgraded/upgraded_config.yaml   （升级后的配置）
# - config/upgraded/upgrade_report.md      （差异报告）
```

### 分步使用

#### Step 1: 增强扫描

```python
from scanner_v2 import EnhancedScanner

scanner = EnhancedScanner()
results = scanner.scan_all()

# 输出：包含完整签名的字典
```

#### Step 2: 运行时探测

```python
from runtime_prober import RuntimeProber

prober = RuntimeProber(max_workers=5, rate_limit=1.0)

# 探测单个函数
result = prober.probe_function("stock_zh_a_hist", {"symbol": "000001"})

# 批量探测
results = prober.probe_batch(["stock_zh_a_spot_em", "bond_zh_cov"])
```

#### Step 3: 语义推断

```python
from semantic_inferrer import SemanticInferrer

inferrer = SemanticInferrer()

# 推断字段名
field_name = inferrer.infer_field_name("成交量")  # -> "volume"

# 批量推断
field_names = inferrer.batch_infer(["日期", "开盘", "收盘"])
# -> {"日期": "date", "开盘": "open", "收盘": "close"}
```

#### Step 4: 配置合并

```python
from config_merger import ConfigMerger

merger = ConfigMerger()

upgraded, changes = merger.upgrade_manual_config(
    manual_config,
    generated_config,
)

# 生成报告
merger.generate_report(changes, Path("upgrade_report.md"))
```

## 预期效果

| 指标 | 当前 | 目标 | 提升 |
|-----|------|------|------|
| 配置覆盖率 | 10.2% | 80% | +70% |
| input 完整性 | 60% | 95% | +35% |
| output 完整性 | 50% | 90% | +40% |
| 字段语义化 | 30% | 85% | +55% |
| 人工审核工作量 | 100% | 20% | -80% |

## 实施步骤

1. **开发工具**（1周）：完善工具代码，添加更多功能
2. **数据收集**（2天）：扫描所有函数，探测关键函数
3. **配置升级**（3天）：运行合并器，人工审核
4. **验证优化**（2天）：测试验证，性能优化

## 注意事项

1. **运行时探测限流**：akshare 有 API 限制，控制并发和频率
2. **参数安全**：只探测安全函数，避免触发异常
3. **人工审核**：自动升级后需要人工审核关键差异
4. **备份配置**：升级前备份原有配置

## 下一步

1. 集成工具到 `src/akshare_data/offline/` 目录
2. 编写单元测试
3. 建立 CI/CD 验证流程
4. 优化字段映射字典