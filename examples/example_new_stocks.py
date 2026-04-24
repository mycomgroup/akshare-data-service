"""
get_new_stocks() 接口示例

演示如何使用 akshare_data.get_new_stocks() 获取新股数据。

接口说明:
- 获取全市场新股申购/上市数据
- 无需参数
- 返回字段包含: 股票代码、股票名称、申购日期、上市日期、发行价格等

使用方式:
    from akshare_data import get_service
    service = get_service()
    df = service.get_new_stocks()
"""

import logging
import warnings
import pandas as pd

from akshare_data import get_service

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)


def _normalize_new_stock_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    aliases = {
        "symbol": ("symbol", "代码", "证券代码", "股票代码"),
        "name": ("name", "名称", "股票简称", "股票名称"),
        "subscribe_date": ("subscribe_date", "申购日期", "发行日期", "申购日", "apply_date"),
        "list_date": ("list_date", "上市日期", "上市日", "list_date"),
        "price": ("price", "发行价", "发行价格", "price"),
        "pe": ("pe", "市盈率", "发行市盈率", "pe_ratio"),
    }
    for target, names in aliases.items():
        for name in names:
            if name in df.columns:
                rename_map[name] = target
                break
    out = df.rename(columns=rename_map).copy()
    for col in ("subscribe_date", "list_date"):
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    if "price" in out.columns:
        out["price"] = pd.to_numeric(out["price"], errors="coerce")
    return out


def _as_dataframe(data, label: str) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame):
        print(f"{label}: 返回类型异常，期望 DataFrame，实际 {type(data).__name__}")
        return pd.DataFrame()
    if data.empty:
        print(f"{label}: 返回空数据")
    return data


def _fetch_new_stocks(service) -> pd.DataFrame:
    method_candidates = [
        "get_new_stocks",
        "get_stock_new",
        "get_new_stock",
        "get_stock_ipo",
    ]
    for method_name in method_candidates:
        fn = getattr(service, method_name, None)
        if not callable(fn):
            continue
        try:
            data = fn()
        except Exception as exc:  # pragma: no cover - example script best-effort
            print(f"  [失败] {method_name}() 调用异常: {exc}")
            continue
        df = _as_dataframe(data, f"{method_name}()")
        if not df.empty:
            print(f"  [命中] 使用 {method_name}()，rows={len(df)}")
            return _normalize_new_stock_columns(df)
    return pd.DataFrame()


# ============================================================
# 示例 1: 基本用法 - 获取新股数据
# ============================================================
def example_basic():
    """基本用法: 获取新股数据"""
    print("=" * 60)
    print("示例 1: 基本用法 - 获取新股数据")
    print("=" * 60)

    service = get_service()

    try:
        df = _fetch_new_stocks(service)
        if df.empty:
            return

        print(f"数据形状: {df.shape}")
        print(f"字段列表: {list(df.columns)}")

        print("\n前5行数据:")
        print(df.head())
        print("\n后5行数据:")
        print(df.tail())

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: 数据概览与统计
# ============================================================
def example_overview():
    """对新数据进行概览统计"""
    print("\n" + "=" * 60)
    print("示例 2: 新股数据概览")
    print("=" * 60)

    service = get_service()

    try:
        df = _fetch_new_stocks(service)
        if df.empty:
            return

        print(f"新股数据总数: {len(df)}")
        print(f"字段列表: {list(df.columns)}")

        # 数值列统计
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols:
            print("\n数值字段统计:")
            print(df[numeric_cols].describe())

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 3: 近期新股筛选
# ============================================================
def example_recent():
    """筛选近期上市的新股"""
    print("\n" + "=" * 60)
    print("示例 3: 近期新股筛选")
    print("=" * 60)

    service = get_service()

    try:
        df = _fetch_new_stocks(service)
        if df.empty:
            return

        date_col = "list_date" if "list_date" in df.columns else None
        if date_col is None:
            for col in df.columns:
                if "上市" in col or "日期" in col or "date" in col.lower():
                    date_col = col
                    break

        if date_col:
            sorted_df = df.sort_values(by=date_col, ascending=False, na_position="last")
            print("最新的10只新股:")
            print(sorted_df.head(10).to_string(index=False))
        else:
            print(f"字段列表: {list(df.columns)}")
            print("\n全部新股数据 (前20条):")
            print(df.head(20).to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 4: 发行价格分析
# ============================================================
def example_price_analysis():
    """分析新股发行价格"""
    print("\n" + "=" * 60)
    print("示例 4: 发行价格分析")
    print("=" * 60)

    service = get_service()

    try:
        df = _fetch_new_stocks(service)
        if df.empty:
            return

        price_col = "price" if "price" in df.columns else None
        if price_col is None:
            for col in df.columns:
                if "价格" in col or "发行价" in col or "price" in col.lower():
                    price_col = col
                    break

        if price_col:
            df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
            print(f"发行价格统计 ({price_col}):")
            print(df[price_col].describe())

            # 最贵的新股
            print("\n发行价格最高的5只新股:")
            top_price = df.nlargest(5, price_col)
            print(top_price.to_string(index=False))
        else:
            print(f"字段列表: {list(df.columns)}")
            print("无法识别发行价格字段")

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 5: 错误处理
# ============================================================
def example_error_handling():
    """演示错误处理"""
    print("\n" + "=" * 60)
    print("示例 5: 错误处理")
    print("=" * 60)

    service = get_service()

    try:
        print("\n测试 1: 正常调用")
        df = _fetch_new_stocks(service)
        if df.empty:
            print("  结果: 无数据")
        else:
            print(f"  结果: {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")

    try:
        print("\n测试 2: 再次调用（验证缓存）")
        df = _fetch_new_stocks(service)
        if df.empty:
            print("  结果: 无数据")
        else:
            print(f"  结果: {len(df)} 行数据")
    except Exception as e:
        print(f"  捕获异常: {type(e).__name__}: {e}")


if __name__ == "__main__":
    example_basic()
    example_overview()
    example_recent()
    example_price_analysis()
    example_error_handling()
