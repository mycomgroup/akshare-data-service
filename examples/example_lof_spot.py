"""
get_lof_spot() 接口示例（增强稳健版）

演示如何使用 DataService.get_lof_spot() 获取LOF基金实时行情，并在无数据场景下通过
“可交易日回退 + 代码候选 + 字段兼容 + 降级输出”提高示例稳定性。
"""

<<<<<<< HEAD
import logging
import warnings
import pandas as pd

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("akshare_data").setLevel(logging.ERROR)

=======
from __future__ import annotations

from typing import Any

import pandas as pd

from _example_utils import recent_trade_days
>>>>>>> fbe6b24bca4744d99b8a20f07f01b84e23f4610d
from akshare_data import get_service

SPOT_CODE_CANDIDATES = ["162605", "163402", "161005", "160222", "161725", "501018", "501019"]
FIELD_ALIASES = {
    "code": ["代码", "基金代码", "symbol", "code"],
    "name": ["名称", "基金简称", "name", "基金名称"],
    "price": ["最新价", "现价", "最新", "price", "close", "收盘"],
    "change_pct": ["涨跌幅", "涨跌幅(%)", "pct_chg", "change_pct", "change"],
    "volume": ["成交量", "成交额", "volume", "vol", "amount"],
    "date": ["日期", "date", "trade_date"],
}


def _as_dataframe(data: Any, label: str) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame):
        print(f"{label}: 返回类型异常，期望 DataFrame，实际 {type(data).__name__}")
        return pd.DataFrame()
    return data


def _first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _col(df: pd.DataFrame, key: str) -> str | None:
    return _first_existing_col(df, FIELD_ALIASES.get(key, []))


def _prepare_display_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    renames: dict[str, str] = {}
    for canonical, alias_cols in FIELD_ALIASES.items():
        src = _first_existing_col(out, alias_cols)
        if src and src != canonical:
            renames[src] = canonical
    out = out.rename(columns=renames)
    for numeric_col in ("price", "change_pct", "volume"):
        if numeric_col in out.columns:
            out[numeric_col] = pd.to_numeric(out[numeric_col], errors="coerce")
    preferred = [c for c in ["code", "name", "price", "change_pct", "volume", "date"] if c in out.columns]
    others = [c for c in out.columns if c not in preferred]
    return out[preferred + others]


def _build_spot_like_from_daily(service) -> tuple[pd.DataFrame, str | None, str | None]:
    trade_days = recent_trade_days(service, max_backtrack=8)
    if not trade_days:
        return pd.DataFrame(), None, None

    for trade_day in trade_days:
        rows: list[pd.DataFrame] = []
        for code in SPOT_CODE_CANDIDATES:
            try:
                daily = _as_dataframe(
                    service.get_lof_daily(symbol=code, start_date=trade_day, end_date=trade_day),
                    f"daily-{code}-{trade_day}",
                )
            except Exception:
                continue
            if daily.empty:
                continue
            one = daily.tail(1).copy()
            if _col(one, "code") is None:
                one["code"] = code
            rows.append(one)
        if rows:
            merged = pd.concat(rows, ignore_index=True)
            return merged, trade_day, ",".join(SPOT_CODE_CANDIDATES)
    return pd.DataFrame(), trade_days[-1], ",".join(SPOT_CODE_CANDIDATES)


def fetch_lof_spot_stable() -> tuple[pd.DataFrame, dict[str, str | int]]:
    service = get_service()
    meta: dict[str, str | int] = {"source": "spot", "hit_trade_day": "", "candidate_codes": ""}
    try:
        spot_df = _as_dataframe(service.get_lof_spot(), "spot")
    except Exception:
        spot_df = pd.DataFrame()

    if not spot_df.empty:
        normalized = _prepare_display_df(spot_df)
        meta["rows"] = len(normalized)
        return normalized, meta

    fallback_df, hit_day, used_codes = _build_spot_like_from_daily(service)
    meta["source"] = "daily_fallback"
    meta["hit_trade_day"] = hit_day or ""
    meta["candidate_codes"] = used_codes or ""
    if not fallback_df.empty:
        normalized = _prepare_display_df(fallback_df)
        meta["rows"] = len(normalized)
        return normalized, meta

    meta["source"] = "degraded_empty"
    meta["rows"] = 0
    empty = pd.DataFrame(columns=["code", "name", "price", "change_pct", "volume", "date"])
    return empty, meta


def _print_degrade_hint(meta: dict[str, str | int]) -> None:
    source = str(meta.get("source", "unknown"))
    if source == "spot":
        return
    print(f"已触发回退链路: {source}")
    hit_day = str(meta.get("hit_trade_day", "")).strip()
    if hit_day:
        print(f"命中交易日: {hit_day}")
    candidate_codes = str(meta.get("candidate_codes", "")).strip()
    if candidate_codes:
        print(f"候选代码: {candidate_codes}")


# ============================================================
# 示例 1: 基本用法 - 获取全部LOF实时行情
# ============================================================
def example_basic():
    """基本用法: 获取全部LOF基金实时行情"""
    print("=" * 60)
    print("示例 1: 获取LOF基金实时行情")
    print("=" * 60)

    try:
        df, meta = fetch_lof_spot_stable()
        _print_degrade_hint(meta)

        if df.empty:
            print("示例1: 无可用数据（已输出降级空表）")
            return

        # 打印数据形状
        print(f"数据形状: {df.shape}")
        print(f"LOF基金数量: {len(df)}")
        print(f"字段列表: {list(df.columns)}")

        # 打印前10行
        print("\n前10行数据:")
        print(df.head(10).to_string(index=False))

        # 打印后5行
        print("\n后5行数据:")
        print(df.tail().to_string(index=False))

    except Exception as e:
        print(f"获取数据失败: {e}")


# ============================================================
# 示例 2: LOF涨跌幅分析
# ============================================================
def example_price_change():
    """分析LOF基金的涨跌幅情况"""
    print("\n" + "=" * 60)
    print("示例 2: LOF涨跌幅分析")
    print("=" * 60)

    try:
        df, meta = fetch_lof_spot_stable()
        _print_degrade_hint(meta)

        if df.empty:
            print("示例2: 无可用数据（已输出降级空表）")
            return

        print(f"LOF基金总数: {len(df)}")

        # 查找涨跌幅列
        change_col = _col(df, "change_pct")

        if change_col and change_col in df.columns:
            # 转换为数值类型
            df[change_col] = pd.to_numeric(df[change_col], errors="coerce")

            print("\n涨跌幅统计:")
            print(f"  平均涨跌幅: {df[change_col].mean():.2f}%")
            print(f"  最大涨幅: {df[change_col].max():.2f}%")
            print(f"  最大跌幅: {df[change_col].min():.2f}%")

            # 涨幅前5
            top_gainers = df.nlargest(5, change_col)
            print("\n涨幅前5:")
            print(top_gainers[[col for col in df.columns if col in ["code", "name", "price", change_col]]].to_string(index=False))

            # 跌幅前5
            top_losers = df.nsmallest(5, change_col)
            print("\n跌幅前5:")
            print(top_losers[[col for col in df.columns if col in ["code", "name", "price", change_col]]].to_string(index=False))
        else:
            print("未找到涨跌幅字段")
            print(f"可用字段: {list(df.columns)}")

    except Exception as e:
        print(f"分析失败: {e}")


# ============================================================
# 示例 3: 查找特定LOF基金
# ============================================================
def example_find_lof():
    """在LOF列表中查找特定基金"""
    print("\n" + "=" * 60)
    print("示例 3: 查找特定LOF基金")
    print("=" * 60)

    # 常见LOF基金代码
    target_codes = ["162605", "163402", "161005"]

    try:
        df, meta = fetch_lof_spot_stable()
        _print_degrade_hint(meta)

        if df.empty:
            print("示例3: 无可用数据（已输出降级空表）")
            return

        print(f"LOF基金总数: {len(df)}")

        # 查找代码列
        code_col = _col(df, "code")

        if code_col:
            for code in target_codes:
                matched = df[df[code_col].astype(str).str.contains(code, na=False)]
                if not matched.empty:
                    print(f"\n找到基金代码 {code}:")
                    print(matched.to_string(index=False))
                else:
                    print(f"\n基金代码 {code}: 未找到")
        else:
            print("未找到代码字段")

    except Exception as e:
        print(f"查找失败: {e}")


# ============================================================
# 示例 4: LOF成交量分析
# ============================================================
def example_volume_analysis():
    """分析LOF基金的成交情况"""
    print("\n" + "=" * 60)
    print("示例 4: LOF成交量分析")
    print("=" * 60)

    try:
        df, meta = fetch_lof_spot_stable()
        _print_degrade_hint(meta)

        if df.empty:
            print("示例4: 无可用数据（已输出降级空表）")
            return

        print(f"LOF基金总数: {len(df)}")

        # 查找成交量列
        volume_col = _col(df, "volume")

        if volume_col and volume_col in df.columns:
            df[volume_col] = pd.to_numeric(df[volume_col], errors="coerce")

            print(f"\n{volume_col}统计:")
            print(f"  总成交量: {df[volume_col].sum():,.0f}")
            print(f"  平均成交量: {df[volume_col].mean():,.0f}")
            print(f"  最大成交量: {df[volume_col].max():,.0f}")

            # 成交量前10
            top_volume = df.nlargest(10, volume_col)
            print("\n成交量前10:")
            display_cols = [col for col in df.columns if col in ["code", "name", "price", volume_col]]
            print(top_volume[display_cols].to_string(index=False))
        else:
            print("未找到成交量字段")

    except Exception as e:
        print(f"分析失败: {e}")


# ============================================================
# 示例 5: LOF价格分布
# ============================================================
def example_price_distribution():
    """分析LOF基金的价格分布"""
    print("\n" + "=" * 60)
    print("示例 5: LOF价格分布")
    print("=" * 60)

    try:
        df, meta = fetch_lof_spot_stable()
        _print_degrade_hint(meta)

        if df.empty:
            print("示例5: 无可用数据（已输出降级空表）")
            return

        # 查找价格列
        price_col = _col(df, "price")

        if price_col and price_col in df.columns:
            df[price_col] = pd.to_numeric(df[price_col], errors="coerce")

            print(f"LOF基金价格分布 ({price_col}):")
            print(f"  平均价格: {df[price_col].mean():.3f}")
            print(f"  中位数: {df[price_col].median():.3f}")
            print(f"  最高价: {df[price_col].max():.3f}")
            print(f"  最低价: {df[price_col].min():.3f}")

            # 价格区间分布
            bins = [0, 1, 2, 5, 10, float("inf")]
            labels = ["<1", "1-2", "2-5", "5-10", ">10"]
            df["price_range"] = pd.cut(df[price_col], bins=bins, labels=labels)
            print("\n价格区间分布:")
            print(df["price_range"].value_counts().sort_index().to_string())
        else:
            print("未找到价格字段")
            print(f"可用字段: {list(df.columns)}")

    except Exception as e:
        print(f"分析失败: {e}")

if __name__ == "__main__":
    example_basic()
    example_price_change()
    example_find_lof()
    example_volume_analysis()
    example_price_distribution()
