"""
get_index_components() 接口示例

演示如何使用 akshare_data.get_index_components() 获取指数成分股数据。

接口说明:
  - get_index_components(index_code, include_weights=True) -> pd.DataFrame
  - 返回指数的成分股列表，可选是否包含权重信息

参数:
  - index_code: 指数代码，如 "000001" (上证指数)
  - include_weights: 是否包含权重信息，默认 True

常用指数代码:
  - "000001": 上证指数
  - "000016": 上证50
  - "000300": 沪深300
  - "000905": 中证500
  - "399001": 深证成指
  - "399006": 创业板指

返回字段 (可能包含):
  - code: 股票代码
  - name: 股票名称
  - weight: 权重 (当 include_weights=True 时)
"""

from datetime import datetime, timedelta
import inspect

import pandas as pd

from akshare_data import get_service
from _example_utils import fetch_with_retry, normalize_symbol_input, stable_df


def _safe_df(df):
    """Return None if df is None or empty."""
    if df is None or df.empty:
        return None
    return df


_INDEX_CODE_ALIASES = {
    "000300": ("000300", "399300"),
    "399300": ("399300", "000300"),
    "000016": ("000016",),
    "000905": ("000905",),
    "000852": ("000852",),
    "399001": ("399001",),
    "399006": ("399006",),
}


def _candidate_index_codes(index_code: str) -> list[str]:
    raw = str(index_code).strip()
    normalized = normalize_symbol_input(raw)
    base_candidates = list(_INDEX_CODE_ALIASES.get(normalized, (normalized,)))
    extras = [raw, normalized]

    if raw.endswith((".SH", ".SZ", ".XSHG", ".XSHE")):
        extras.append(raw.split(".")[0])
    if raw.startswith(("sh", "sz")):
        extras.append(raw[2:])

    candidates: list[str] = []
    for code in [*extras, *base_candidates]:
        clean = normalize_symbol_input(code)
        if clean and clean not in candidates:
            candidates.append(clean)
    return candidates


def _date_fallback_kwargs(fetcher) -> list[dict]:
    params = inspect.signature(fetcher).parameters
    supports_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    if not supports_var_kw and not {"date", "start_date", "end_date"}.intersection(params):
        return [{}]

    today = datetime.now().date()
    recent_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6)]
    kwargs_list = [{}]
    for day in recent_days:
        kwargs_list.append({"date": day})
        kwargs_list.append(
            {"start_date": (datetime.strptime(day, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d"), "end_date": day}
        )
    return kwargs_list


def _safe_index_components(service, index_code: str, include_weights: bool = True):
    for candidate in _candidate_index_codes(index_code):
        for date_kwargs in _date_fallback_kwargs(service.get_index_components):
            try:
                df = fetch_with_retry(
                    lambda c=candidate, kw=date_kwargs: service.get_index_components(
                        index_code=c,
                        include_weights=include_weights,
                        **kw,
                    ),
                    retries=1,
                )
                safe = _safe_df(stable_df(df))
                if safe is not None:
                    return safe
            except TypeError:
                continue
            except Exception:
                continue
    return None


def _safe_weight_sum(df: pd.DataFrame) -> str:
    if "weight" not in df.columns:
        return "N/A"
    weights = pd.to_numeric(df["weight"], errors="coerce").dropna()
    if weights.empty:
        return "N/A"
    return f"{weights.sum():.2f}%"


# ============================================================
# 示例 1: 基本用法 - 获取指数成分股
# ============================================================
def example_basic():
    """基本用法: 获取沪深300成分股"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取沪深300成分股")
    print("=" * 60)

    service = get_service()

    try:
        df = _safe_index_components(service, "000300", include_weights=True)
        if df is None:
            print("无数据")
            return

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10行数据:")
        print(df.head(10).to_string(index=False))

        print("\n后5行数据:")
        print(df.tail(5).to_string(index=False))

    except Exception as e:
        print(f"获取成分股数据失败: {e}")


# ============================================================
# 示例 2: 不含权重的成分股列表
# ============================================================
def example_without_weights():
    """获取不含权重的成分股列表"""
    print("\n" + "=" * 60)
    print("示例 2: 不含权重的成分股列表")
    print("=" * 60)

    service = get_service()

    try:
        df = _safe_index_components(service, "000300", include_weights=False)
        if df is None:
            print("无数据")
            return

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")
        print("\n前10行数据:")
        print(df.head(10).to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 3: 对比不同指数的成分股数量
# ============================================================
def example_compare_indices():
    """对比不同指数的成分股数量"""
    print("\n" + "=" * 60)
    print("示例 3: 不同指数成分股数量对比")
    print("=" * 60)

    service = get_service()

    indices = {
        "000016": "上证50",
        "000300": "沪深300",
        "000905": "中证500",
        "399006": "创业板指",
    }

    for code, name in indices.items():
        try:
            df = _safe_index_components(service, code, include_weights=True)
            if df is None:
                print(f"{name}({code}): 无数据")
            else:
                print(f"{name}({code}): {len(df)} 只成分股")
                print(f"  字段: {list(df.columns)}")
                print(f"  权重合计: {_safe_weight_sum(df)}")
        except Exception as e:
            print(f"{name}({code}): 获取失败 - {e}")


# ============================================================
# 示例 4: 分析权重分布
# ============================================================
def example_weight_analysis():
    """演示如何分析指数成分股权重分布"""
    print("\n" + "=" * 60)
    print("示例 4: 权重分布分析 (上证50)")
    print("=" * 60)

    service = get_service()

    try:
        df = _safe_index_components(service, "000016", include_weights=True)
        if df is None or "weight" not in df.columns:
            print("无权重数据")
            return

        weights = pd.to_numeric(df["weight"], errors="coerce").dropna()
        if weights.empty:
            print("无可用权重数据")
            return

        print(f"成分股数量: {len(df)}")
        print("\n权重统计:")
        print(weights.describe())

        if "name" in df.columns:
            top10 = (
                df.assign(weight_num=pd.to_numeric(df["weight"], errors="coerce"))
                .dropna(subset=["weight_num"])
                .nlargest(10, "weight_num")[["code", "name", "weight_num"]]
                .rename(columns={"weight_num": "weight"})
            )
        else:
            top10 = (
                df.assign(weight_num=pd.to_numeric(df["weight"], errors="coerce"))
                .dropna(subset=["weight_num"])
                .nlargest(10, "weight_num")
                .drop(columns=["weight"])
                .rename(columns={"weight_num": "weight"})
            )

        print("\n前10大权重股:")
        print(top10.to_string(index=False))

        print("\n权重分布:")
        ranges = [
            (0, 1),
            (1, 3),
            (3, 5),
            (5, 10),
            (10, 100),
        ]
        for low, high in ranges:
            count = len(weights[(weights >= low) & (weights < high)])
            print(f"  {low}% - {high}%: {count} 只")

    except Exception as e:
        print(f"分析失败: {e}")


# ============================================================
# 示例 5: 获取深证指数成分股
# ============================================================
def example_sz_index():
    """获取深证成指成分股"""
    print("\n" + "=" * 60)
    print("示例 5: 获取深证成指成分股")
    print("=" * 60)

    service = get_service()

    try:
        df = _safe_index_components(service, "399001", include_weights=True)
        if df is None:
            print("无数据")
            return

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前10行数据:")
        print(df.head(10).to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 6: 导出成分股代码列表
# ============================================================
def example_extract_codes():
    """演示如何提取成分股代码列表"""
    print("\n" + "=" * 60)
    print("示例 6: 提取成分股代码列表")
    print("=" * 60)

    service = get_service()

    try:
        df = _safe_index_components(service, "000300", include_weights=False)
        if df is None:
            print("无数据")
            return

        if "code" in df.columns:
            codes = df["code"].tolist()
            print(f"沪深300成分股代码列表 (共 {len(codes)} 只):")
            print(f"{codes}")
        elif "symbol" in df.columns:
            codes = df["symbol"].tolist()
            print(f"沪深300成分股代码列表 (共 {len(codes)} 只):")
            print(f"{codes}")
        else:
            print("未找到代码字段")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 7: 错误处理演示
# ============================================================
def example_error_handling():
    """演示错误处理 - 无效指数代码等"""
    print("\n" + "=" * 60)
    print("示例 7: 错误处理演示")
    print("=" * 60)

    service = get_service()

    # 测试 1: 正常获取
    print("\n测试 1: 正常获取")
    try:
        df = _safe_index_components(service, "000300")
        if df is None:
            print("  结果: 无数据")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")

    # 测试 2: 无效指数代码
    print("\n测试 2: 无效指数代码")
    try:
        df = _safe_index_components(service, "999999")
        if df is None:
            print("  结果: 无数据")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")

    # 测试 3: 不含权重
    print("\n测试 3: 不含权重")
    try:
        df = _safe_index_components(service, "000300", include_weights=False)
        if df is None:
            print("  结果: 无数据")
        else:
            print(f"  结果: 获取到 {len(df)} 行数据, 字段: {list(df.columns)}")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")


if __name__ == "__main__":
    example_basic()
    example_without_weights()
    example_compare_indices()
    example_weight_analysis()
    example_sz_index()
    example_extract_codes()
    example_error_handling()
