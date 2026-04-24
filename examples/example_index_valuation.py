"""
get_index_valuation() 接口示例

演示如何使用 akshare_data.get_index_valuation() 获取指数估值数据。

接口说明:
  - get_index_valuation(index_code) -> pd.DataFrame
  - 返回指数的估值指标，如 PE-TTM、PB 等

数据来源:
  - Lixinger (需要配置 LIXINGER_TOKEN 环境变量)
  - AkShare CSIndex (stock_zh_index_value_csindex)

常用指数代码 (CSIndex格式):
  - "000300": 沪深300
  - "000905": 中证500
  - "000852": 中证1000
  - "000903": 中证A100
  - "000913": 300医药

常用估值指标:
  - pe: 指数市盈率
  - pe_2: 指数市盈率2
  - dividend_yield: 股息率
"""

import sys
import warnings

sys.warnoptions = ["ignore::DeprecationWarning"]
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging

logging.getLogger("akshare_data").setLevel(logging.ERROR)

try:
    from _example_utils import fetch_with_retry
except ImportError:
    from examples._example_utils import fetch_with_retry


CSINDEX_CODES = ["000300", "000905", "000852", "000903", "000913"]
CSINDEX_NAMES = {
    "000300": "沪深300",
    "000905": "中证500",
    "000852": "中证1000",
    "000903": "中证A100",
    "000913": "300医药",
}


def _try_direct_akshare_fetch(index_code: str):
    """直接尝试通过 AkShare 获取指数估值数据"""
    try:
        from akshare_data.sources.akshare.fetcher import fetch

        df = fetch("index_valuation", index_code=index_code)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    return None


# ============================================================
# 示例 1: 基本用法 - 获取沪深300估值
# ============================================================
def example_basic():
    """基本用法: 获取沪深300估值数据"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取沪深300估值")
    print("=" * 60)

    try:
        # 直接通过 AkShare fetcher 获取数据
        df = _try_direct_akshare_fetch("000300")

        if df is None or df.empty:
            print("无数据")
            print("提示: get_index_valuation 数据来源:")
            print("      1. Lixinger API (需要配置 LIXINGER_TOKEN 环境变量)")
            print("      2. AkShare CSIndex (stock_zh_index_value_csindex)")
            print("      请确保至少有一个数据源可用")
            return

        print(f"数据形状: {df.shape}")
        print(f"指数名称: {CSINDEX_NAMES.get('000300', '沪深300')}")
        print(f"字段列表: {list(df.columns)}")

        print("\n估值数据:")
        print(df.to_string(index=False))

    except Exception as e:
        print(f"获取估值数据失败: {e}")


# ============================================================
# 示例 2: 对比多个宽基指数估值
# ============================================================
def example_compare_indices():
    """对比多个宽基指数的估值水平"""
    print("\n" + "=" * 60)
    print("示例 2: 宽基指数估值对比")
    print("=" * 60)

    indices = {
        "000300": "沪深300",
        "000905": "中证500",
        "000852": "中证1000",
    }

    results = []
    for code, name in indices.items():
        try:
            df = _try_direct_akshare_fetch(code)
            if df is not None and not df.empty:
                row = {"指数代码": code, "指数名称": name}
                for col in ["pe", "pe_2", "dividend_yield", "dividend_yield_2"]:
                    if col in df.columns:
                        row[col] = df[col].iloc[0]
                results.append(row)
                print(f"{name}({code}): 获取成功")
            else:
                print(f"{name}({code}): 无数据")
        except Exception as e:
            print(f"{name}({code}): 获取失败 - {e}")

    if results:
        import pandas as pd

        compare_df = pd.DataFrame(results)
        print("\n指数估值对比表:")
        print(compare_df.to_string(index=False))
    else:
        print("\n提示: 所有指数均无数据，请检查数据源配置")


# ============================================================
# 示例 3: 获取中证500估值
# ============================================================
def example_csi500():
    """获取中证500估值数据"""
    print("\n" + "=" * 60)
    print("示例 3: 获取中证500估值")
    print("=" * 60)

    try:
        df = _try_direct_akshare_fetch("000905")

        if df is None or df.empty:
            print("无数据")
            return

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")
        print("\n估值数据:")
        print(df.to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 4: 估值水平分析
# ============================================================
def example_valuation_analysis():
    """演示获取指数估值后进行简单分析"""
    print("\n" + "=" * 60)
    print("示例 4: 估值水平分析")
    print("=" * 60)

    core_indices = {
        "000300": "沪深300",
        "000905": "中证500",
    }

    for code, name in core_indices.items():
        try:
            df = _try_direct_akshare_fetch(code)
            if df is None or df.empty:
                print(f"{name}({code}): 无数据")
                continue

            print(f"\n{name}({code}):")
            if "pe" in df.columns:
                pe = df["pe"].iloc[0]
                print(f"  市盈率(PE): {pe}")
                if pe < 12:
                    print("  估值判断: 偏低")
                elif pe < 20:
                    print("  估值判断: 适中")
                else:
                    print("  估值判断: 偏高")

            if "dividend_yield" in df.columns:
                dy = df["dividend_yield"].iloc[0]
                print(f"  股息率: {dy}%")

        except Exception as e:
            print(f"{name}({code}): 分析失败 - {e}")


# ============================================================
# 示例 5: 错误处理演示
# ============================================================
def example_error_handling():
    """演示错误处理 - 无效指数代码等"""
    print("\n" + "=" * 60)
    print("示例 5: 错误处理演示")
    print("=" * 60)

    print("\n测试 1: 正常获取")
    try:
        df = _try_direct_akshare_fetch("000300")
        if df is None or df.empty:
            print("  结果: 无数据 (空 DataFrame)")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")

    print("\n测试 2: 无效指数代码")
    try:
        df = _try_direct_akshare_fetch("999999")
        if df is None or df.empty:
            print("  结果: 无数据")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")

    print("\n测试 3: 数据源状态检查")
    import os

    lixinger_token = os.environ.get("LIXINGER_TOKEN", "")
    if lixinger_token:
        print(f"  LIXINGER_TOKEN: 已配置")
    else:
        print(f"  LIXINGER_TOKEN: 未配置")
    print("  AkShare CSIndex: 网络依赖 (stock_zh_index_value_csindex)")


if __name__ == "__main__":
    example_basic()
    example_compare_indices()
    example_csi500()
    example_valuation_analysis()
    example_error_handling()